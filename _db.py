# -*- coding: utf-8 -*-
"""Supabase 数据记录（通过 PostgREST REST API，零额外依赖）。

环境变量：
  SUPABASE_URL   形如 https://xxxx.supabase.co
  SUPABASE_KEY   service_role key（只放在服务器端，绝不暴露给浏览器）

未配置时所有函数静默 no-op —— 不影响主功能。
"""
import json
import os
import urllib.request

SUPABASE_URL = os.environ.get('SUPABASE_URL', '').rstrip('/')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')


def enabled():
    return bool(SUPABASE_URL and SUPABASE_KEY)


def _insert(table, row, return_row=False):
    if not enabled():
        return None
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': 'Bearer ' + SUPABASE_KEY,
        'Content-Type': 'application/json',
    }
    if return_row:
        headers['Prefer'] = 'return=representation'
    req = urllib.request.Request(
        SUPABASE_URL + '/rest/v1/' + table,
        data=json.dumps(row).encode('utf-8'),
        headers=headers, method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode('utf-8')
        if return_row and body:
            arr = json.loads(body)
            return arr[0] if isinstance(arr, list) and arr else None
        return None
    except Exception:  # noqa — 数据库出问题绝不能拖垮解读
        return None


def log_reading(client_id, chart, reading, model, palm_used, is_calibration):
    chart = chart or {}
    row = {
        'client_id': client_id,
        'solar_date': chart.get('solar_date'),
        'hour': chart.get('hour_index'),
        'gender': chart.get('gender'),
        'calendar': 'solar' if chart.get('solar_date') else 'lunar',
        'chinese_date': chart.get('chinese_date'),
        'five_elements': chart.get('five_elements'),
        'model': model,
        'palm_used': bool(palm_used),
        'is_calibration': bool(is_calibration),
        'chart': chart,
        'reading': reading,
    }
    r = _insert('readings', row, return_row=True)
    return r.get('id') if r else None


def log_feedback(client_id, reading_id, card_title, note):
    _insert('feedback', {
        'client_id': client_id,
        'reading_id': reading_id or None,
        'card_title': card_title,
        'note': note,
    })
