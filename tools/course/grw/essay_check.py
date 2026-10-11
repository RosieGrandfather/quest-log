"""写作练习（block type = gre-essay）的格式检查：validate.py 和 build.py 都用它。返回错误列表。"""

def validate_essay(unit):
    e = []
    uid = unit.get('id', '?')
    for k in ('id', 'title', 'en', 'minutes', 'objectives', 'blocks', 'references'):
        if k not in unit: e.append(f'{uid}: 缺少字段 {k}')
    if e: return e
    if unit['minutes'] > 50: e.append(f'{uid}: {unit["minutes"]} 分钟，超过 50')
    blocks = [b for b in unit['blocks'] if b.get('type') == 'gre-essay']
    if len(blocks) != 1: return e + [f'{uid}: 应当有且只有 1 个 gre-essay 块']
    b = blocks[0]
    if b.get('kind') not in ('issue', 'argument'): e.append(f'{uid}: kind 不对')
    if not b.get('prompt') or any(not p.strip() for p in b['prompt']): e.append(f'{uid}: 题目为空')
    if not 2 <= len(b.get('prompt', [])) <= 4: e.append(f'{uid}: 题目段数不对（应含题干/引文 + 任务指令）')
    rub = b.get('rubric') or []
    if [r['score'] for r in rub] != [6, 5, 4, 3, 2, 1]: e.append(f'{uid}: 评分标准应含 6–1 分')
    for r in rub:
        if not r.get('summary') or not r.get('bullets'): e.append(f'{uid}: 评分标准 {r.get("score")} 分内容不全')
    rs = b.get('responses') or []
    if [r['score'] for r in rs] != [6, 5, 4, 3, 2, 1]: e.append(f'{uid}: 样文应含 6–1 分各一篇，现在 {[r["score"] for r in rs]}')
    for r in rs:
        if not r.get('essay') or not r.get('commentary'): e.append(f'{uid}: {r.get("score")} 分样文或评语为空')
        words = sum(len(p.split()) for p in r.get('essay', []))
        if r.get('score') in (6, 5, 4) and words < 150: e.append(f'{uid}: {r["score"]} 分样文只有 {words} 词，可能截断')
    return e
