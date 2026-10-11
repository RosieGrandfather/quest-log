"""练习套题（kind=practice）的格式检查：validate.py 和 build.py 都用它。返回错误列表。"""

def validate_practice(unit):
    e = []
    uid = unit.get('id', '?')
    for k in ('id', 'title', 'en', 'minutes', 'objectives', 'blocks', 'references'):
        if k not in unit: e.append(f'{uid}: 缺少字段 {k}')
    if e: return e
    if unit['minutes'] > 50: e.append(f'{uid}: {unit["minutes"]} 分钟，超过 50')
    blocks = [b for b in unit['blocks'] if b.get('type') == 'gre-set']
    if len(blocks) != 1: return e + [f'{uid}: 应当有且只有 1 个 gre-set 块，现在 {len(blocks)} 个']
    b = blocks[0]
    items, passages = b.get('items') or [], b.get('passages') or {}
    if not items: e.append(f'{uid}: 没有题')
    seen = set()
    for i, it in enumerate(items, 1):
        w = f'{uid} 第 {i} 题'
        if it.get('kind') not in ('rc', 'tc', 'se'): e.append(f'{w}: kind 不对')
        if not (it.get('stem') or '').strip(): e.append(f'{w}: 题干为空')
        if not (it.get('expl') or '').strip(): e.append(f'{w}: 没有解析')
        if it.get('id') in seen: e.append(f'{w}: id 重复')
        seen.add(it.get('id'))
        if it.get('kind') == 'rc':
            if it.get('passage') not in passages: e.append(f'{w}: 阅读题找不到文章 {it.get("passage")}')
        elif it.get('passage'): e.append(f'{w}: 非阅读题不该有文章')
        groups = it.get('groups') or []
        if not groups: e.append(f'{w}: 没有选项组')
        if it.get('kind') == 'tc' and it['stem'].count('______') != len(groups): e.append(f'{w}: 题干空格数 ≠ 选项组数')
        if it.get('kind') == 'se' and it['stem'].count('______') != 1: e.append(f'{w}: 句子等价题应有 1 个空格')
        for j, g in enumerate(groups):
            opts, corr, pick = g.get('options') or [], g.get('correct') or [], g.get('pick')
            if len(opts) < 3 or len(set(opts)) != len(opts) or any(not o.strip() for o in opts): e.append(f'{w} 组{j+1}: 选项数量或内容不对')
            if not corr or any((not isinstance(x, int)) or not 0 <= x < len(opts) for x in corr) or len(set(corr)) != len(corr): e.append(f'{w} 组{j+1}: 正确答案下标不对')
            if pick == 1 and len(corr) != 1: e.append(f'{w} 组{j+1}: 单选题正确答案应为 1 个')
            if pick == 2 and len(corr) != 2: e.append(f'{w} 组{j+1}: 选两项的题正确答案应为 2 个')
            if pick not in (1, 2, 'any'): e.append(f'{w} 组{j+1}: pick 不对')
    for pid, t in passages.items():
        if not t.strip(): e.append(f'{uid}: 文章 {pid} 为空')
        if not any(it.get('passage') == pid for it in items): e.append(f'{uid}: 文章 {pid} 没有题用到')
    return e
