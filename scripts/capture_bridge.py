"""One-shot loopback handoff of a visible research report; no remote service."""
from __future__ import annotations
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import secrets
import time
from urllib.parse import parse_qs


def receive(destination, timeout=180):
    target = Path(destination).expanduser().resolve()
    if target.exists():
        raise ValueError('destination_exists')
    if not 1 <= timeout <= 600:
        raise ValueError('timeout_out_of_range')
    token = secrets.token_urlsafe(24)
    saved = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def answer(self, code, body):
            payload = body.encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Security-Policy', "default-src 'none'; form-action 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            if self.path != '/' + token:
                return self.answer(404, 'Unavailable')
            self.answer(200, '<!doctype html><meta charset="utf-8"><title>FS local report handoff</title>'
                        '<h1>FS local report handoff</h1><p>Loopback only. This form saves one report locally.</p>'
                        '<form method="post"><label>Report capture JSON<textarea name="capture"></textarea></label>'
                        '<button type="submit">Save locally</button></form>')

        def do_POST(self):
            self.connection.settimeout(5)
            expected_host = f'127.0.0.1:{self.server.server_port}'
            origin = self.headers.get('Origin')
            if self.path != '/' + token or self.headers.get('Host') != expected_host or (origin and origin != 'http://' + expected_host):
                return self.answer(403, 'Unavailable')
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 1 <= length <= 2 * 1024 * 1024:
                    raise ValueError('capture_size_limit')
                form = parse_qs(self.rfile.read(length).decode('utf-8'), strict_parsing=True)
                capture = json.loads(form['capture'][0])
                if not isinstance(capture, dict) or not isinstance(capture.get('html'), str) or not isinstance(capture.get('sources'), list):
                    raise ValueError('invalid_capture')
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('x', encoding='utf-8') as handle:
                    json.dump(capture, handle, ensure_ascii=False)
                saved.append(True)
                self.answer(200, '<!doctype html><meta charset="utf-8"><h1>Saved locally</h1><p>The report was saved. No report body is displayed here.</p>')
            except (ValueError, KeyError, OSError, UnicodeError):
                self.answer(400, 'Capture invalid or destination unavailable')

    server = HTTPServer(('127.0.0.1', 0), Handler)
    server.timeout = 1
    deadline = time.monotonic() + timeout
    print(json.dumps({'status': 'waiting', 'url': f'http://127.0.0.1:{server.server_port}/{token}',
                      'expires_seconds': timeout, 'destination': str(target)}), flush=True)
    try:
        while not saved and time.monotonic() < deadline:
            server.handle_request()
    finally:
        server.server_close()
    value = {'status': 'saved' if saved else 'timeout', 'destination': str(target)}
    print(json.dumps(value), flush=True)
    return 0 if saved else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args(argv)
    try:
        return receive(args.out, args.timeout)
    except (OSError, ValueError) as exc:
        print(json.dumps({'status': 'error', 'reason': str(exc)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
