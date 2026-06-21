# -*- coding: utf-8 -*-
"""本地一键运行服务器（只依赖 Python 标准库 + iztro-py）。

用法：
    set ANTHROPIC_API_KEY=sk-ant-...   (Windows PowerShell: $env:ANTHROPIC_API_KEY="sk-ant-...")
    python server.py
然后浏览器打开 http://localhost:8000

/api/chart   POST {date, hour, gender, calendar, leap}      -> 排盘 JSON（不需要 API key）
/api/reading POST {chart, palm_image?, palm_media_type?}    -> Claude 解读 JSON（需要 API key）
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api'))
import _mingli_core as mingli_core

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public')
PORT = int(os.environ.get('PORT', '8000'))

CONTENT_TYPES = {'.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
                 '.js': 'application/javascript; charset=utf-8', '.svg': 'image/svg+xml',
                 '.ico': 'image/x-icon', '.png': 'image/png'}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype='application/json; charset=utf-8'):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode('utf-8')
        elif isinstance(body, str):
            body = body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        n = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(n).decode('utf-8')) if n else {}

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path == '/':
            path = '/index.html'
        fp = os.path.normpath(os.path.join(STATIC_DIR, path.lstrip('/')))
        if not fp.startswith(STATIC_DIR) or not os.path.isfile(fp):
            return self._send(404, {'error': 'not found'})
        ext = os.path.splitext(fp)[1]
        with open(fp, 'rb') as f:
            self._send(200, f.read(), CONTENT_TYPES.get(ext, 'application/octet-stream'))

    def do_POST(self):
        try:
            data = self._read_json()
            if self.path == '/api/chart':
                chart = mingli_core.build_chart(
                    data['date'], int(data['hour']), data['gender'],
                    is_lunar=(data.get('calendar') == 'lunar'),
                    is_leap=bool(data.get('leap', False)),
                )
                return self._send(200, chart)
            if self.path == '/api/reading':
                reading = mingli_core.call_anthropic(
                    data['chart'], data.get('palm_image'),
                    data.get('palm_media_type', 'image/jpeg'),
                    hand=data.get('hand'), calibration=data.get('calibration'),
                )
                return self._send(200, reading)
            return self._send(404, {'error': 'unknown endpoint'})
        except Exception as e:  # noqa
            return self._send(500, {'error': str(e)})

    def log_message(self, *a):
        pass


if __name__ == '__main__':
    print(f'命理 App 运行中 → http://localhost:{PORT}  (Ctrl+C 退出)')
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print('提示：未检测到 ANTHROPIC_API_KEY，排盘可用，但 AI 解读会报错。')
    ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
