# -*- coding: utf-8 -*-
"""Vercel serverless function: Claude 解读（需要 ANTHROPIC_API_KEY）。POST /api/reading"""
import os
import sys
import json
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _mingli_core as mingli_core


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            n = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(n).decode('utf-8')) if n else {}
            reading = mingli_core.call_anthropic(
                data['chart'], data.get('palm_image'),
                data.get('palm_media_type', 'image/jpeg'),
                hand=data.get('hand'), calibration=data.get('calibration'),
            )
            self._json(200, reading)
        except Exception as e:  # noqa
            self._json(500, {'error': str(e)})

    def _json(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)
