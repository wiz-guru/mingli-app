# -*- coding: utf-8 -*-
"""紫微斗数 App —— 单一 Flask 入口（Vercel 的 Python 运行时识别 app.py 里的 `app`）。

路由：
  GET  /                          -> public/index.html
  GET  /<file>                    -> public/<file>（styles.css / app.js / wechat-qr.jpg）
  POST /api/chart                 -> 排盘（不需要 API key）
  POST /api/reading               -> Claude 解读（需要 ANTHROPIC_API_KEY）
"""
import os

from flask import Flask, request, jsonify, send_from_directory

import _mingli_core

HERE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(HERE, 'public')

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


@app.post('/api/chart')
def api_chart():
    try:
        d = request.get_json(force=True) or {}
        chart = _mingli_core.build_chart(
            d['date'], int(d['hour']), d['gender'],
            is_lunar=(d.get('calendar') == 'lunar'),
            is_leap=bool(d.get('leap', False)),
        )
        return jsonify(chart)
    except Exception as e:  # noqa
        return jsonify({'error': str(e)}), 500


@app.post('/api/reading')
def api_reading():
    try:
        d = request.get_json(force=True) or {}
        reading = _mingli_core.call_anthropic(
            d['chart'], d.get('palm_image'), d.get('palm_media_type', 'image/jpeg'),
            hand=d.get('hand'), calibration=d.get('calibration'),
        )
        return jsonify(reading)
    except Exception as e:  # noqa
        return jsonify({'error': str(e)}), 500


@app.get('/')
def index():
    return send_from_directory(PUBLIC, 'index.html')


@app.get('/<path:filename>')
def static_files(filename):
    return send_from_directory(PUBLIC, filename)
