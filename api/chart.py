# -*- coding: utf-8 -*-
"""Vercel serverless function: 排盘（不需要 API key）。POST /api/chart"""
import os
import sys
import json
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mingli_core


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            n = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(n).decode('utf-8')) if n else {}
            chart = mingli_core.build_chart(
                data['date'], int(data['hour']), data['gender'],
                is_lunar=(data.get('calendar') == 'lunar'),
                is_leap=bool(data.get('leap', False)),
            )
            self._json(200, chart)
        except Exception as e:  # noqa
            self._json(500, {'error': str(e)})

    def _json(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)
