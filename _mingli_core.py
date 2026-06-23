# -*- coding: utf-8 -*-
"""紫微斗数 App 核心：排盘计算 + Claude 解读。

被 server.py（本地）和 api/*.py（Vercel）共用。
排盘逻辑改编自 mingli-master skill 的 calculate_chart.py（已验证）。
"""
import json
import os
import re
import urllib.request
import urllib.error

# ---------- 排盘 ----------

BRANCH_CN = {
    'ziEarthly': '子', 'chouEarthly': '丑', 'yinEarthly': '寅', 'maoEarthly': '卯',
    'chenEarthly': '辰', 'siEarthly': '巳', 'wuEarthly': '午', 'weiEarthly': '未',
    'shenEarthly': '申', 'youEarthly': '酉', 'xuEarthly': '戌', 'haiEarthly': '亥',
}
STEM_CN = {
    'jiaHeavenly': '甲', 'yiHeavenly': '乙', 'bingHeavenly': '丙', 'dingHeavenly': '丁',
    'wuHeavenly': '戊', 'jiHeavenly': '己', 'gengHeavenly': '庚', 'xinHeavenly': '辛',
    'renHeavenly': '壬', 'guiHeavenly': '癸',
}
FIVE_ELEMENTS_CN = {
    'water2': '水二局', 'wood3': '木三局', 'metal4': '金四局',
    'earth5': '土五局', 'fire6': '火六局',
}
MUTAGEN_CN = {'禄': '化禄', '权': '化权', '科': '化科', '忌': '化忌'}

HOUR_NAMES = {
    0: '早子时 (23-01)', 1: '丑时 (01-03)', 2: '寅时 (03-05)', 3: '卯时 (05-07)',
    4: '辰时 (07-09)', 5: '巳时 (09-11)', 6: '午时 (11-13)', 7: '未时 (13-15)',
    8: '申时 (15-17)', 9: '酉时 (17-19)', 10: '戌时 (19-21)', 11: '亥时 (21-23)',
    12: '晚子时 (23-01)',
}


def _tn(obj):
    if hasattr(obj, 'translate_name'):
        return obj.translate_name()
    return str(obj)


def build_chart(date_str, hour_index, gender, is_lunar=False, is_leap=False, language='zh-CN'):
    from iztro_py import astro

    if is_lunar:
        chart = astro.by_lunar(date_str, hour_index, gender, is_leap, True, language)
    else:
        chart = astro.by_solar(date_str, hour_index, gender, language)

    soul_idx = chart.get_soul_palace().index
    body_idx = chart.get_body_palace().index
    five = FIVE_ELEMENTS_CN.get(chart.five_elements_class, chart.five_elements_class)

    year_mutagens = []
    for p in chart.palaces:
        for s in list(p.major_stars) + list(p.minor_stars):
            if getattr(s, 'mutagen', None):
                year_mutagens.append({
                    'star': _tn(s), 'mutagen': MUTAGEN_CN.get(s.mutagen, s.mutagen),
                    'palace': _tn(p), 'branch': BRANCH_CN.get(p.earthly_branch, p.earthly_branch),
                })

    palaces = []
    for p in chart.palaces:
        major = [_tn(s) for s in p.major_stars]
        minor = [_tn(s) for s in p.minor_stars]
        adj = [_tn(s) for s in p.adjective_stars] if hasattr(p, 'adjective_stars') else []
        star_mut = []
        for s in list(p.major_stars) + list(p.minor_stars):
            if getattr(s, 'mutagen', None):
                star_mut.append({'star': _tn(s), 'mutagen': s.mutagen})
        dec = p.decadal
        drange = [dec.range[0], dec.range[1]] if dec else None
        tags = []
        if p.index == soul_idx:
            tags.append('命宫')
        if p.index == body_idx:
            tags.append('身宫')
        palaces.append({
            'name': _tn(p),
            'heavenly_stem': STEM_CN.get(p.heavenly_stem, p.heavenly_stem),
            'earthly_branch': BRANCH_CN.get(p.earthly_branch, p.earthly_branch),
            'major_stars': major, 'minor_stars': minor, 'adjective_stars': adj[:5],
            'mutagens': star_mut, 'is_empty': not major,
            'decadal_range': drange, 'tags': tags, 'index': p.index,
        })

    return {
        'solar_date': None if is_lunar else date_str,
        'lunar_date': date_str if is_lunar else chart.lunar_date,
        'chinese_date': chart.chinese_date,
        'gender': gender, 'hour_index': hour_index,
        'hour_name': HOUR_NAMES.get(hour_index, ''),
        'five_elements': five,
        'soul_palace_branch': BRANCH_CN.get(chart.earthly_branch_of_soul_palace, chart.earthly_branch_of_soul_palace),
        'body_palace_branch': BRANCH_CN.get(chart.earthly_branch_of_body_palace, chart.earthly_branch_of_body_palace),
        'year_mutagens': year_mutagens, 'palaces': palaces,
    }


# ---------- Claude 解读 ----------

SYSTEM_PROMPT = """你是一位有主见、有温度的紫微斗数命理咨询师，融合三合派、中州派与手相互证的方法论。

风格要求：
- 像朋友聊天，不像教科书。有判断力，敢说「这个格局倾向于X」，不说「可能是X也可能是Y」。
- 用类比和日常语言翻译术语。先看到积极面，再温和指出需要注意的地方。
- 不预言死亡、不制造恐惧、不替代决策。不说「你一定会」，只说「这个格局倾向于」。

我会给你一份排盘 JSON（十二宫星曜、四化、大限）。请按以下结构解读，并【只输出一个合法 JSON 对象】，不要任何解释文字或 markdown 代码块标记：

{
  "current_decadal_branch": "当前大限宫位地支（按虚岁判断，如'亥'）",
  "current_decadal_display": "当前大限展示文字（如'亥宫 · 武曲 · 破军（15-24岁）'）",
  "cards": [
    {"title":"命盘底色 · 先天禀赋","badge":"主星名","full":true,"highlight":true,
     "body":"解读正文，可用 HTML 标签：<strong>白色强调</strong> <em>金色强调</em> <span class='warn'>橙色提醒</span> <span class='good'>绿色利好</span> <br>换行",
     "probabilities":[{"label":"纯命盘推算置信度","pct":70},{"label":"校准问答后可达","pct":88}]},
    {"title":"事业 · 官禄宫","badge":"星名","body":"..."},
    {"title":"财运 · 财帛宫","badge":"星名","body":"..."},
    {"title":"感情 · 夫妻宫","badge":"星名","body":"..."},
    {"title":"当前大限","badge":"星名","full":true,"teal":true,"body":"..."},
    {"title":"近三年流年提示","badge":"年份","body":"..."}
  ],
  "hand_reading": {"items":[{"title":"生命线","body":"...","status":"match","status_text":"与XX共振 ✓"}]},
  "calibration_questions":[{"text":"问题","hint":"用途说明"}]
}

要点：命宫空宫则借对宫。cards 里命盘底色最重要，给 3-5 个性格关键词。当前大限要说清「这十年的核心课题」。只有用户提供了手相照片时才输出 hand_reading（识别生命线/智慧线/感情线/掌型并与命盘交叉印证，status 用 match 或 conflict），否则省略 hand_reading 字段。calibration_questions 给 3-5 个最关键的追问。今年是公历 %d 年，请据此推算流年与当前大限。"""


def _today_year():
    import datetime
    return datetime.date.today().year


HAND_CN = {'left': '左手', 'right': '右手'}


def build_user_content(chart, palm_image_b64=None, palm_media_type='image/jpeg', hand=None, calibration=None):
    text = "排盘数据如下，请解读：\n\n" + json.dumps(chart, ensure_ascii=False, indent=2)

    if calibration:
        qa = "\n".join(
            f"- 问：{c.get('question', '')}\n  答：{c.get('answer', '')}"
            for c in calibration if c.get('answer')
        )
        text += (
            "\n\n【校准回流】用户已回答下列校准问题，请输出**修正后的**解读 JSON"
            "（结构与首次完全一致：cards / hand_reading / calibration_questions / current_decadal_*）：\n"
            + qa +
            "\n\n修正要求：\n"
            "1. 把 probabilities 的置信度提到 85% 以上；\n"
            "2. 在相关 card 的 body 里明确标注哪些推断被『<span class=\\'good\\'>印证 ✓</span>』、"
            "哪些需要『<span class=\\'warn\\'>修正</span>』并给出新判断；\n"
            "3. 针对用户透露的真实处境给出更具体、更有主见的解读，不要泛泛而谈；\n"
            "4. calibration_questions 换成 2-3 个更深入的新追问。"
        )

    hand_label = HAND_CN.get(hand, '')
    if palm_image_b64:
        note = (f"用户提供了下面这张{hand_label}照片" if hand_label
                else "用户提供了下面这张手相照片")
        note += "，请加入 hand_reading 手相互证。" + (
            "（传统男左女右：左手主先天禀赋、右手主后天现状，请据此说明。）" if hand_label else ""
        )
        return [
            {"type": "image", "source": {"type": "base64", "media_type": palm_media_type, "data": palm_image_b64}},
            {"type": "text", "text": text + "\n\n" + note},
        ]
    return [{"type": "text", "text": text}]


def call_anthropic(chart, palm_image_b64=None, palm_media_type='image/jpeg',
                   api_key=None, model=None, hand=None, calibration=None):
    api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise RuntimeError('缺少 ANTHROPIC_API_KEY 环境变量')
    model = model or os.environ.get('ANTHROPIC_MODEL', 'claude-opus-4-8')

    body = {
        'model': model,
        'max_tokens': 8192,
        'system': SYSTEM_PROMPT % _today_year(),
        'messages': [{'role': 'user', 'content': build_user_content(
            chart, palm_image_b64, palm_media_type, hand, calibration)}],
    }
    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=json.dumps(body).encode('utf-8'),
        headers={
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        },
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    text = ''.join(b.get('text', '') for b in data.get('content', []) if b.get('type') == 'text')
    return _extract_json(text)


def _extract_json(text):
    text = text.strip()
    if text.startswith('```'):
        text = text.split('```', 2)[1]
        if text.startswith('json'):
            text = text[4:]
        text = text.strip().rstrip('`').strip()
    start, end = text.find('{'), text.rfind('}')
    if start >= 0 and end > start:
        text = text[start:end + 1]
    text = re.sub(r',(\s*[}\]])', r'\1', text)  # 容忍模型偶发的尾逗号
    return json.loads(text)
