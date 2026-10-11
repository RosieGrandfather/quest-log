"""Quant 练习套题（block type = gre-qset）的格式检查：validate.py 和 build.py 都用它。返回错误列表。"""
import os

def validate_qset(unit, cdir):
    e = []
    uid = unit.get('id', '?')
    for k in ('id', 'title', 'en', 'minutes', 'objectives', 'blocks', 'references'):
        if k not in unit: e.append(f'{uid}: 缺少字段 {k}')
    if e: return e
    if unit['minutes'] > 50: e.append(f'{uid}: {unit["minutes"]} 分钟，超过 50')
    blocks = [b for b in unit['blocks'] if b.get('type') == 'gre-qset']
    if len(blocks) != 1: return e + [f'{uid}: 应当有且只有 1 个 gre-qset 块']
    b = blocks[0]
    base = b.get('base', '')
    items = b.get('items') or []
    if not items: e.append(f'{uid}: 没有题')
    def need(p, w):
        if not p or not os.path.exists(os.path.join(cdir, '..', '..', base + p)): e.append(f'{w}: 找不到图片 {p}')
    ns = [it.get('n') for it in items]
    if len(set(ns)) != len(ns): e.append(f'{uid}: 题号重复')
    for i, it in enumerate(items, 1):
        w = f'{uid} 第 {i} 题'
        kind = it.get('kind'); ans = it.get('ans')
        if kind not in ('qc', 'mc1', 'mcn', 'ne', 'se', 'tc', 'ss'): e.append(f'{w}: kind 不对'); continue
        for p in (it.get('imgs') or [it.get('img')]): need(p, w)
        if it.get('exp') is not None: need(it.get('exp'), w)
        if it.get('fig'): need(it['fig'], w)
        if kind == 'ss':
            if not str(it.get('ansText', '')).strip(): e.append(f'{w}: 选句子题没有 ansText')
        elif kind == 'tc':
            nb = it.get('blanks')
            if nb not in (2, 3): e.append(f'{w}: 填空数 blanks 应为 2 或 3')
            elif not isinstance(ans, list) or len(ans) != nb or any((not isinstance(x, int)) or not 0 <= x < 3 for x in ans): e.append(f'{w}: 多空填空答案应为 {nb} 个 0–2 的下标')
        elif kind == 'se':
            if it.get('nopt') != 6: e.append(f'{w}: 选两个应有 6 个选项')
            if not isinstance(ans, list) or len(ans) != 2 or len(set(ans)) != 2 or any((not isinstance(x, int)) or not 0 <= x < 6 for x in ans): e.append(f'{w}: 选两个答案应为 2 个 0–5 的下标')
        elif kind == 'ne':
            if not isinstance(ans, str) or not ans.strip(): e.append(f'{w}: 数值题没有答案')
            if it.get('frac') and '/' not in str(ans): e.append(f'{w}: 分数题答案应为 a/b')
        else:
            n = 4 if kind == 'qc' else it.get('nopt', 0)
            if kind != 'qc' and not 3 <= n <= 8: e.append(f'{w}: 选项数 {n} 不合理')
            if not isinstance(ans, list) or not ans or len(set(ans)) != len(ans) or any((not isinstance(x, int)) or not 0 <= x < n for x in ans): e.append(f'{w}: 正确答案下标不对')
            elif kind in ('qc', 'mc1') and len(ans) != 1: e.append(f'{w}: 单选题应只有 1 个正确答案')
    return e
