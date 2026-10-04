"""写课程章节用的辅助函数 + 自动检查。

用法：在 tools/course/ 下新建一个 uXX.py（复制 unit_template.py），
写好 unit 字典后调用 dump(unit, "arena-0.0", "u16-xxx.json")。
dump 会先跑 validate_unit，检查不通过就报错、不写文件。
"""
import json, os
from collections import Counter

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
COURSES = os.path.join(REPO, 'courses')

# ARENA 0.0 常用链接
ARENA_URL = 'https://github.com/ARENA-education/ARENA_materials/blob/main/chapter0_fundamentals/instructions/pages/00_%5B0.0%5D_Prerequisites.md'
ARENA_COLAB = 'https://colab.research.google.com/github/ARENA-education/ARENA_materials/blob/main/chapter0_fundamentals/exercises/part0_prereqs/0.0_Prerequisites_exercises.ipynb'

# ---------- 内容块 ----------
def T(md):
    """文字块（Markdown，公式用 $...$ / $$...$$）"""
    return {"type": "text", "md": md.strip('\n')}

def V(vid, title, minutes, lang="英文，可开中文字幕", provider="youtube", **kw):
    """视频块。provider: youtube / bilibili；可选 start / end（秒）"""
    return {"type": "video", "provider": provider, "id": vid, "title": title, "lang": lang, "minutes": minutes, **kw}

def IMG(src, alt, caption=''):
    return {"type": "image", "src": src, "alt": alt, "caption": caption}

def THINK(q, a):
    """「想一想」折叠题"""
    return {"type": "think", "q": q, "a": a.strip('\n')}

def KW(*items):
    """关键词表，每项 (中文, English, 一句话说明)"""
    return {"type": "keywords", "items": [list(i) for i in items]}

def Q(q, options, answer, explain):
    """测验题：4 个选项，answer 是正确选项的下标（0–3）"""
    return {"q": q, "options": options, "answer": answer, "explain": explain}

# ---------- 检查 ----------
def _check_math(s, where, errors):
    if s.replace('$$', '').count('$') % 2:
        errors.append(f'{where}: $ 没有成对出现：{s[:60]}')

import ast as _ast, re as _re
def python_cells(unit):
    """返回这一节所有 ```python / ```python-static 代码块：[(块序号, 语言, 代码行数(不含「# 输出：」行), 源码)]"""
    out = []
    for j, b in enumerate(unit['blocks']):
        for m in _re.finditer(r'```(python-static|python)\n(.*?)```', b.get('md', ''), _re.S):
            lines = [l for l in m.group(2).rstrip('\n').split('\n') if not l.startswith('# 输出：')]
            out.append((j + 1, m.group(1), len(lines), '\n'.join(lines)))
    return out

def validate_unit(unit, n_questions=10):
    """返回错误列表（空 = 通过）"""
    e = []
    uid = unit.get('id', '?')
    for k in ('id', 'title', 'en', 'minutes', 'objectives', 'blocks', 'references', 'quiz'):
        if k not in unit: e.append(f'{uid}: 缺少字段 {k}')
    if e: return e
    qs = unit['quiz']['questions']
    if len(qs) != n_questions: e.append(f'{uid}: 测验应有 {n_questions} 题，现在 {len(qs)} 题')
    for i, q in enumerate(qs):
        w = f'{uid} 第{i+1}题'
        if len(q['options']) != 4: e.append(f'{w}: 应有 4 个选项')
        if len(set(q['options'])) != len(q['options']): e.append(f'{w}: 选项重复')
        if not 0 <= q['answer'] < len(q['options']): e.append(f'{w}: answer 下标越界')
        if not q.get('explain'): e.append(f'{w}: 缺少讲解')
        for s in [q['q'], q['explain'], *q['options']]: _check_math(s, w, e)
    if qs:
        dist = Counter(q['answer'] for q in qs)
        if max(dist.values()) > (len(qs) * 0.4 if len(qs) >= 10 else (len(qs) + 1) // 2): e.append(f'{uid}: 正确答案太集中 {dict(dist)}')
        if len(dist) < min(3, len(qs)): e.append(f'{uid}: 正确答案只用了 {len(dist)} 个位置 {dict(dist)}')
    for j, b in enumerate(unit['blocks']):
        for k in ('md', 'q', 'a'):
            if k in b: _check_math(b[k], f'{uid} 块{j+1}', e)
        if b['type'] == 'video' and b.get('provider') not in ('youtube', 'bilibili'):
            e.append(f'{uid} 块{j+1}: 视频 provider 只能是 youtube / bilibili')
    for o in unit['objectives']: _check_math(o, f'{uid} 学习目标', e)
    for j, lang, n, src in python_cells(unit):          # 每个 Python 代码块必须语法正确（网页里可以直接运行）
        try: _ast.parse(src)
        except SyntaxError as x: e.append(f'{uid} 块{j}: Python 代码有语法错误（第 {x.lineno} 行）：{x.msg}')
    return e

def dump(unit, course_path, filename):
    errors = validate_unit(unit)
    if errors:
        raise SystemExit('检查没通过：\n  ' + '\n  '.join(errors))
    out = os.path.join(COURSES, course_path, filename)
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(unit, f, ensure_ascii=False, indent=1)
    vids = [b for b in unit['blocks'] if b['type'] == 'video']
    print(f"{unit['id']} 已写入 {os.path.relpath(out, REPO)}：答案 {[q['answer'] for q in unit['quiz']['questions']]}，"
          f"视频 {sum(v['minutes'] for v in vids)} 分钟，正文 {sum(len(b.get('md', '')) for b in unit['blocks'])} 字")
    print('记得：把 course.json 里这一节的 file 填上，并在 CHANGELOG.md 记一笔')
