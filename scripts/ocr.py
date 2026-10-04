"""Page OCR with original images/coordinates; optional CPU runtime, offline reuse."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import material
import report
import runtime_config


def _pages(value):
    pages = set()
    for part in value.split(','):
        ends = part.split('-')
        if len(ends) == 1:
            start = stop = int(ends[0])
        elif len(ends) == 2:
            start, stop = map(int, ends)
        else:
            raise ValueError('invalid_pages')
        if not 1 <= start <= stop <= 10000 or stop - start >= 10:
            raise ValueError('page_limit')
        pages.update(range(start, stop + 1))
        if len(pages) > 10:
            raise ValueError('page_limit')
    return sorted(pages)


def extract(args):
    source = Path(args.input).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() not in {'.pdf', '.png', '.jpg', '.jpeg', '.tif', '.tiff', '.webp'}:
        raise ValueError('input_missing_or_unsupported')
    if not 36 <= args.dpi <= 240 or not 1 <= args.timeout <= 180:
        raise ValueError('budget_out_of_range')
    pages = _pages(args.pages)
    region = [float(v) for v in args.region.split(',')] if args.region else [0, 0, 1, 1]
    if len(region) != 4 or not (0 <= region[0] < region[2] <= 1 and 0 <= region[1] < region[3] <= 1):
        raise ValueError('invalid_region')
    digest, size = material._sha256_path(source)
    url = report._validate_source_url(args.source_url)
    key = hashlib.sha256(json.dumps([digest, pages, args.dpi, region, url, 'rapidocr-3.9.2'], ensure_ascii=False).encode()).hexdigest()
    target = Path(args.out).expanduser().resolve()
    if target.exists():
        if not target.is_dir():
            raise ValueError('destination_conflict')
        meta = json.loads((target / 'ocr.json').read_text(encoding='utf-8'))
        if meta['request_key'] != key:
            raise ValueError('destination_conflict')
        summary(target, meta, 'reused')  # validate the receipt before following its image names
        report._resolve_report(str(target))
        for page in meta['pages']:
            image = target / page['image']
            if image.parent != target or hashlib.sha256(image.read_bytes()).hexdigest() != page['image_sha256']:
                raise ValueError('ocr_image_damaged')
        return summary(target, meta, 'reused')
    python = args.python_path or runtime_config.runtime_path(runtime_config.load_config(args.config).get('data') or {}, 'ocr')
    if not python or not Path(python).is_file():
        raise ValueError('ocr_runtime_not_configured')
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='fs-ocr-', dir=target.parent))
    started = time.monotonic()
    try:
        images = stage / 'images'
        images.mkdir()
        req = {'input': str(source), 'out': str(images), 'pages': pages, 'dpi': args.dpi, 'region': region}
        try:
            run = subprocess.run([python, '-X', 'utf8', '-I', '-B', str(Path(__file__).with_name('ocr_worker.py'))],
                                 input=json.dumps(req).encode(), capture_output=True,
                                 timeout=args.timeout, env=material._safe_environment())
        except subprocess.TimeoutExpired:
            raise ValueError('ocr_timeout') from None
        if len(run.stdout) > 16 * 1024 * 1024:
            raise ValueError('ocr_output_limit')
        parsed = json.loads(run.stdout.decode('utf-8'))
        if run.returncode or parsed.get('status') != 'ok':
            raise ValueError(parsed.get('reason', 'ocr_failed'))
        if not any(page['lines'] for page in parsed['pages']):
            raise ValueError('no_recognized_text')
        parts = ['# Page OCR\n\nRecognized text is unverified. OCR line order may interleave columns. Read original page images for numbers, tables and formulas; use a region for a specific column.\n']
        for page in parsed['pages']:
            parts.append(f"\n## Page {page['page']}\n\n![Original page]({page['image']})\n")
            parts.extend(f"\n[{line['line']}] {line['text']}\n" for line in page['lines'])
        input_md = stage / 'input.md'
        input_md.write_text(''.join(parts), encoding='utf-8')
        artifact = stage / 'artifact'
        report.import_report(str(input_md), str(artifact), url, 'rapidocr_local_pages', 0)
        for image in images.iterdir():
            shutil.move(str(image), str(artifact / image.name))
        meta = {'schema_version': 1, 'request_key': key, 'input_sha256': digest, 'input_bytes': size,
                'source_url': url, 'created_at': datetime.now(timezone.utc).isoformat(),
                'pages': parsed['pages'], 'tool': 'rapidocr', 'tool_version': parsed['tool_version'],
                'dpi': args.dpi, 'region': region, 'seconds': round(time.monotonic() - started, 3),
                'fidelity': 'unverified_ocr_lines_with_page_coordinates', 'network_used': False,
                'table_or_formula_reconstruction': False}
        (artifact / 'ocr.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
        # Bind page/line receipts to the report hash so offline readers can check it.
        metadata_path = artifact / 'metadata.json'
        metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
        metadata['ocr_receipt_sha256'] = hashlib.sha256((artifact / 'ocr.json').read_bytes()).hexdigest()
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(artifact, target)
        return summary(target, meta, 'saved')
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def summary(target, meta, status):
    recorded = json.loads((target / 'metadata.json').read_text(encoding='utf-8'))
    if recorded.get('ocr_receipt_sha256') != hashlib.sha256((target / 'ocr.json').read_bytes()).hexdigest():
        raise ValueError('ocr_receipt_damaged')
    return {'status': status, 'report_dir': str(target), 'source_url': meta['source_url'],
            'pages': [{'page': p['page'], 'image': str(target / p['image']), 'line_count': len(p['lines'])} for p in meta['pages']],
            'seconds': meta['seconds'], 'fidelity': meta['fidelity'], 'network_used': False,
            'next': 'Use report find/open, then inspect page image and ocr.json coordinates.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    parser.add_argument('--out', required=True)
    parser.add_argument('--pages', default='1', help='One-based pages, e.g. 1,3-4; maximum 10.')
    parser.add_argument('--dpi', type=int, default=150)
    parser.add_argument('--region', help='Normalized x0,y0,x1,y1 page region (0..1); original page retained.')
    parser.add_argument('--timeout', type=float, default=90)
    parser.add_argument('--python-path')
    parser.add_argument('--config')
    parser.add_argument('--source-url')
    args = parser.parse_args(argv)
    try:
        value = extract(args)
    except (ValueError, OSError, KeyError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
        value = {'status': 'error', 'reason': str(exc) if isinstance(exc, ValueError) else 'ocr_artifact_or_runtime_invalid'}
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return 1 if value['status'] == 'error' else 0


if __name__ == '__main__':
    raise SystemExit(main())
