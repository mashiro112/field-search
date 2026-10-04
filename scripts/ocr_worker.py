"""Local bounded page OCR using RapidOCR's bundled CPU models and PyMuPDF."""
from __future__ import annotations
import contextlib
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys


def run(req):
    import fitz
    import numpy as np
    from PIL import Image
    from rapidocr import RapidOCR
    if importlib.metadata.version('rapidocr') != '3.9.2':
        raise ValueError('ocr_version_mismatch')
    engine = RapidOCR(params={'EngineConfig.onnxruntime.intra_op_num_threads': 2,
                              'EngineConfig.onnxruntime.inter_op_num_threads': 1})
    source, out = Path(req['input']), Path(req['out'])
    selected, dpi = req['pages'], req['dpi']
    records = []
    pdf = fitz.open(source) if source.suffix.lower() == '.pdf' else None
    try:
        for page in selected:
            if pdf:
                if pdf.is_encrypted or page > len(pdf):
                    raise ValueError('page_unavailable')
                rect = pdf[page - 1].rect
                if rect.width * rect.height * (dpi / 72) ** 2 > 24_000_000:
                    raise ValueError('page_pixel_limit')
                pix = pdf[page - 1].get_pixmap(dpi=dpi, colorspace=fitz.csRGB, alpha=False)
                image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
                path = out / f'page-{page}.png'
                pix.save(path)
            else:
                if page != 1:
                    raise ValueError('page_unavailable')
                with Image.open(source) as img:
                    if img.width * img.height > 24_000_000:
                        raise ValueError('page_pixel_limit')
                    image = np.asarray(img.convert('RGB'))
                    path = out / 'page-1.png'
                    Image.fromarray(image).save(path)
            height, width = image.shape[:2]
            region = req.get('region') or [0, 0, 1, 1]
            x0, y0, x1, y1 = [round(v * size) for v, size in zip(region, [width, height, width, height])]
            if x1 <= x0 or y1 <= y0:
                raise ValueError('region_too_small')
            result = engine(image[y0:y1, x0:x1])
            lines = []
            if result.txts is not None:
                for i, (text, score, box) in enumerate(zip(result.txts, result.scores, result.boxes), 1):
                    lines.append({'line': i, 'text': str(text), 'confidence': round(float(score), 5),
                                  'box_pixels': [[round(float(point[0]) + x0, 1), round(float(point[1]) + y0, 1)] for point in box]})
            records.append({'page': page, 'image': path.name,
                            'image_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                            'width': image.shape[1], 'height': image.shape[0], 'region': region, 'lines': lines})
    finally:
        if pdf:
            pdf.close()
    return {'status': 'ok', 'pages': records, 'tool_version': '3.9.2'}


if __name__ == '__main__':
    try:
        req = json.load(sys.stdin)
        with contextlib.redirect_stdout(sys.stderr):
            value = run(req)
        print(json.dumps(value, ensure_ascii=False))
    except Exception as exc:
        reason = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        print(json.dumps({'status': 'error', 'reason': reason}))
        sys.exit(1)
