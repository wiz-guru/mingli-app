# -*- coding: utf-8 -*-
"""本地启动器：跑 Flask 开发服务器（本地和 Vercel 用同一套 app.py）。

用法：
    pip install flask iztro-py
    set ANTHROPIC_API_KEY=...      (PowerShell: $env:ANTHROPIC_API_KEY="...")
    python server.py
然后浏览器打开 http://localhost:8000
"""
import os

from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8000'))
    print(f'命理 App 运行中 -> http://localhost:{port}  (Ctrl+C 退出)')
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print('提示：未检测到 ANTHROPIC_API_KEY，排盘可用，但 AI 解读会报错。')
    app.run(host='0.0.0.0', port=port, debug=False)
