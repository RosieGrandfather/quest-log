"""把「整节」课程 JSON 拆成若干个 ≤50 分钟的小节。

用法：python3 tools/course/split.py py-0            # 读 tools/course/whole/py-0/*.json，写 courses/py-0/ 并更新 course.json
规则：
  - 只在 `###` 小节边界切；视频跟在它前面的小节后面；
  - 第一个小节沿用原 id（进度不丢），后面的叫 u01b、u01c …；
  - 「想一想」「关键词」「测验」按内容相关度分到各小节；测验每个小节 3–5 题，正确答案位置打散；
  - 后面的小节如果用到前面小节定义的变量，自动在开头补一个「承接上一部分」的代码块。
"""
import ast, copy, itertools, json, math, os, re, sys, textwrap
sys.path.insert(0, os.path.dirname(__file__))
from runlib import Notebook
from unitlib import validate_unit, python_cells, COURSES

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_MIN = 50
LABEL = ['', 'b', 'c', 'd', 'e']
FENCE = re.compile(r'```.*?```', re.S)

def tokens(s):
    s = FENCE.sub(lambda m: m.group(0), s)
    return set(re.findall(r'[A-Za-z_][A-Za-z_0-9.]{2,}|[一-鿿]{2,4}', s))

# ---------- 把一节拆成「原子」 ----------
def paragraphs(md):
    """按空行分段，但围栏代码块里的空行不算"""
    out, cur, infence = [], [], False
    for line in md.split('\n'):
        if line.startswith('```'): infence = not infence
        if not line.strip() and not infence:
            if cur: out.append('\n'.join(cur)); cur = []
        else: cur.append(line)
    if cur: out.append('\n'.join(cur))
    return out

def groups_of(unit):
    """返回 groups：每个 dict(md, w, head, vids)。边界：每个 ### 小节开头，以及每个「**读输出/读代码…**」段落之后。视频跟在前一组后面。"""
    gs = []
    for b in unit['blocks']:
        if b['type'] == 'text':
            prev_read = False
            for p in paragraphs(b['md']):
                head = p.startswith('### ')
                if head or prev_read or not gs or gs[-1].get('vids') or p.startswith('**问题'):
                    gs.append(dict(md=p, w=len(p), head=head, vids=[], think=False))
                else:
                    gs[-1]['md'] += '\n\n' + p; gs[-1]['w'] += len(p)
                prev_read = bool(re.match(r'\*{0,2}读(输出|代码|混淆矩阵|结果)', p)) and not head
        elif b['type'] == 'video':
            gs[-1]['vids'].append(b)
    return gs

def split_unit(unit):
    M = unit['minutes']
    gs = groups_of(unit)
    thinks = [b for b in unit['blocks'] if b['type'] == 'think']
    kws = [b for b in unit['blocks'] if b['type'] == 'keywords']
    last = None
    for i in range(len(gs) - 1, -1, -1):
        if gs[i]['md'].startswith('### 这一节你要带走'): last = gs.pop(i); break
    body = gs
    vid_min = sum(v['minutes'] for g in gs for v in g['vids'])
    fixed = 4 * len(thinks) + 6
    text_min = max(M - vid_min - fixed, 10)
    tot_w = sum(g['w'] for g in body) or 1
    gm = [g['w'] / tot_w * text_min + sum(v['minutes'] for v in g['vids']) for g in body]
    K = max(1, math.ceil(M / MAX_MIN))
    while True:
        cuts = best_cuts(gm, K, [g['head'] for g in body])
        bs = list(zip([0] + cuts, cuts + [len(gm)]))
        loads = [sum(gm[i:j]) for i, j in bs]
        extra = 6 + 4 * math.ceil(len(thinks) / K)
        if max(loads) + extra <= MAX_MIN - 0.5 or K >= 6: break
        K += 1
    parts = [dict(groups=body[i:j], gm=gm[i:j], minutes=sum(gm[i:j])) for i, j in bs]
    return K, parts, thinks, kws, last, M

def best_cuts(gm, K, heads):
    n = len(gm)
    if K == 1: return []
    best, bc = None, None
    for cuts in itertools.combinations(range(1, n), K - 1):
        bs = list(zip((0,) + cuts, cuts + (n,)))
        m = max(sum(gm[i:j]) for i, j in bs)
        ls = [sum(gm[i:j]) for i, j in bs]
        key = (round(m / 3), sum(1 for c in cuts if not heads[c]), round(sum(x * x for x in ls)), m)
        if best is None or key < best: best, bc = key, list(cuts)
    return bc

def assign(items_tokens, parts_tokens, lo, hi):
    """items 分到 parts，每个 part 个数在 [lo, hi]，最大化相关度；并列时偏向顺序一致。"""
    n, K = len(items_tokens), len(parts_tokens)
    sc = [[len(it & pt) / (len(it) ** 0.5 + 1) for pt in parts_tokens] for it in items_tokens]
    best, ba = -1e9, None
    for a in itertools.product(range(K), repeat=n):
        cnt = [a.count(p) for p in range(K)]
        if min(cnt) < lo or max(cnt) > hi: continue
        s = sum(sc[i][a[i]] for i in range(n))
        s -= 0.01 * sum(1 for i in range(n - 1) if a[i] > a[i + 1])
        if s > best: best, ba = s, a
    return ba

BAD_OPT = re.compile(r'以上|都对|都不对|上述|前两|后两|选项|^[ABCD][、。]')

def spread_answers(qs, seed):
    n = len(qs)
    order = [2, 0, 3, 1]
    targets = [order[(i + seed) % 4] for i in range(n)]
    out = []
    for q, t in zip(qs, targets):
        q = copy.deepcopy(q)
        if not any(BAD_OPT.search(o) for o in q['options']) and q['answer'] != t:
            o = q['options']; a = q['answer']
            o[a], o[t] = o[t], o[a]; q['answer'] = t
        out.append(q)
    return out

def sec_title(md):
    m = re.match(r'### (.*)', md)
    return m.group(1) if m else ''

def r5(x): return int(5 * round(x / 5)) if x >= 5 else 5

NOTE_LEARN = ('**怎么学这一小节：** 每个知识点都是「一小段代码 → 紧跟着读它的输出」。每个代码块都可以点「▶ 运行」，也可以改一改再跑；'
              '同一小节里，前面的块定义的变量和函数，后面的块可以直接用，所以请**按顺序**往下跑。')

def strip_intro(md):
    paras = paragraphs(md)
    keep = [p for p in paras if not p.startswith('**本节安排') and not p.startswith('**怎么学这一节')]
    return '\n\n'.join(keep)

def build(unit):
    K, parts, thinks, kws, last, M = split_unit(unit)
    if K == 1:
        return [unit]
    uid, title, en = unit['id'], unit['title'], unit['en']
    ptxt = []
    for k, p in enumerate(parts):
        t = '\n'.join(g['md'] for g in p['groups'])
        if k == K - 1 and last: t += '\n' + last['md']
        ptxt.append(tokens(t))
    qs = unit['quiz']['questions']
    qa = assign([tokens(q['q'] + ' ' + q['explain'] + ' ' + ' '.join(q['options'])) for q in qs], ptxt,
                min(3, len(qs) // K), math.ceil(len(qs) / K))
    ta = assign([tokens(t['q'] + ' ' + t['a']) for t in thinks], ptxt, 1 if len(thinks) >= K else 0, len(thinks))
    kitems = [it for a in kws for it in a['items']]
    ka = []
    for it in kitems:
        txts = [' '.join(sorted(pt)).lower() for pt in ptxt]
        ka.append(max(range(K), key=lambda p: (any(w and w.lower() in txts[p] for w in (it[0], it[1])), -p)))
    n_obj = len(unit['objectives'])
    obj_part = [min(K - 1, i * K // n_obj) for i in range(n_obj)]
    result = []
    cur_head = ''
    for k, p in enumerate(parts):
        mins = r5(p['minutes'] + 6 + 4 * sum(1 for x in ta if x == k))
        titles = []
        for g, gmi in zip(p['groups'], p['gm']):
            if g['head']: cur_head = sec_title(g['md'])
            if g['md'].startswith('### 先说这一节'): continue
            lab = cur_head if (g['head'] or not titles) else None
            if lab is None: titles[-1][1] += gmi
            else: titles.append([lab + ('' if g['head'] else '（续）'), gmi])
        if last and k == K - 1: titles.append(['总结', 1])
        sched = ' → '.join(f"{t}（约 {max(5, r5(m))} 分钟）" for t, m in titles) + f' → 「想一想」与小测验'
        head = f"**本小节安排（约 {mins} 分钟）**：{sched}"
        blocks = []
        texts = []     # 合并相邻文字块
        def flush():
            if texts: blocks.append({'type': 'text', 'md': '\n\n'.join(texts)}); texts.clear()
        if k == 0:
            g0 = p['groups'][0]
            first = strip_intro(g0['md']) if g0['md'].startswith('### 先说这一节') else g0['md']
            # 先说这一节 可能被切成几组：把头几组里属于「先说这一节」的合起来（它们没有视频）
            texts.append(first)
            rest = p['groups'][1:]
            flush_idx = 0
            texts[-1] = texts[-1].rstrip()
            texts.append(f"**这一节分成 {K} 个小节（每个不超过 50 分钟，各有自己的「想一想」和测验），这是第 1 个。**")
            texts.append(head); texts.append(NOTE_LEARN)
            groups = rest
        else:
            texts.append(f"### 先说这一小节要干什么\n\n这是「{title}」分成的第 {k+1} 个小节（共 {K} 个），接着上一个小节往下学。"
                         f"这里的代码块如果用到了前面小节定义的变量或函数，会在开头用「承接上一小节」的代码块重新定义一遍，所以你可以直接从这里开始。")
            texts.append(head); texts.append(NOTE_LEARN)
            groups = p['groups']
        for g in groups:
            if g['md'].startswith('### 先说这一节'):
                texts.append(strip_intro(g['md']))      # 切到后面的「先说」部分（极少见）
            else: texts.append(g['md'])
            if g['vids']:
                flush()
                blocks.extend(g['vids'])
        if k == K - 1 and last:
            texts.append(last['md'])
        flush()
        for t, ai in zip(thinks, ta):
            if ai == k: blocks.append(t)
        ki = [it for it, ai in zip(kitems, ka) if ai == k]
        if ki: blocks.append({'type': 'keywords', 'items': ki})
        qsk = [q for q, ai in zip(qs, qa) if ai == k]
        part = {
            'id': uid + LABEL[k], 'title': f'{title}（{k+1}/{K}）', 'en': f'{en} ({k+1}/{K})', 'minutes': mins,
            'objectives': [o for o, ai in zip(unit['objectives'], obj_part) if ai == k] or unit['objectives'][-1:],
            'blocks': blocks,
            'references': unit['references'] if k == K - 1 else [],
            'quiz': {'questions': spread_answers(qsk, k)},
        }
        result.append(part)
    return result

# ---------- 承接上一小节：补前面小节定义的变量 ----------
def top_defs(src):
    names = set()
    try: tree = ast.parse(src)
    except SyntaxError: return names
    for st in tree.body:
        for n in ast.walk(st):
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)): names.add(n.name)
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                for a in n.names: names.add((a.asname or a.name).split('.')[0])
            elif isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store): names.add(n.id)
    return names

def cells_of(unit, with_static=False):
    out = []
    for b in unit['blocks']:
        for m in re.finditer(r'```(python-static|python)\n(.*?)```', b.get('md', ''), re.S):
            if m.group(1) == 'python-static' and not with_static: continue
            lines = m.group(2).rstrip('\n').split('\n')
            src = '\n'.join(l for l in lines if not l.startswith('# 输出：'))
            exp = [l[len('# 输出：'):] for l in lines if l.startswith('# 输出：')]
            out.append((src, exp))
    return out

def add_setup(parts, whole):
    """parts 按顺序；对每个后续小节尝试运行，缺名字就从前面的块里补。返回 (parts, 报告)"""
    allcells = []                      # 原始顺序所有 python 块 (part_idx, src, exp)
    for k, p in enumerate(parts):
        for src, exp in cells_of(p): allcells.append((k, src, exp))
    report = []
    for k in range(1, len(parts)):
        mine = [(s, e) for kk, s, e in allcells if kk == k]
        prior = [(s, e) for kk, s, e in allcells if kk < k]
        need = []
        for _ in range(12):
            nb = Notebook()
            for s, _e in need:
                out, fail = nb._run(s, False)
            missing = None
            for s, e in mine:
                out, fail = nb._run(s, False)
                if fail:
                    m = re.search(r"NameError: name '(\w+)' is not defined", fail)
                    if m and not _expects_err(e):
                        missing = m.group(1); break
            if not missing: break
            cand = [i for i, (s, _e) in enumerate(prior) if missing in top_defs(s)]
            if not cand:
                report.append(f'{parts[k]["id"]}: 找不到 {missing} 的定义'); break
            idx = cand[-1] if True else cand[0]
            # 需要的是「最先定义」的那一段（变量可能被后面段修改），取全部定义段里第一个
            idx = cand[0]
            if prior[idx] in need: idx = next((c for c in cand if prior[c] not in need), idx)
            if prior[idx] in need: report.append(f'{parts[k]["id"]}: {missing} 循环依赖'); break
            need.append(prior[idx])
            need.sort(key=lambda x: prior.index(x))
        if need:
            src = '\n'.join(s for s, _e in need)
            md = ('**承接上一小节：** 下面的代码用到了前面小节里定义的东西。先点一下「▶ 运行」把它们重新定义出来（不用细看，前面已经讲过）：\n\n'
                  '```python\n' + src + '\n```')
            blocks = parts[k]['blocks']
            # 插到开头介绍的末尾（「怎么学这一小节」之后）
            b0 = blocks[0]['md']
            i = b0.index(NOTE_LEARN) + len(NOTE_LEARN)
            blocks[0]['md'] = b0[:i] + '\n\n' + md + b0[i:]
            report.append(f'{parts[k]["id"]}: 补了承接块（{len(need)} 段，{src.count(chr(10))+1} 行）')
    return parts, report

def _expects_err(exp): return any('Error' in l or 'Exception' in l for l in exp)

def check_run(part):
    """按顺序运行这一小节的 python 块；报告没预期却出错的块，以及输出和注释对不上的块"""
    nb = Notebook()
    probs = []
    for src, exp in cells_of(part):
        out, fail = nb._run(src, False)
        if fail and not _expects_err(exp): probs.append(('ERR', src.split('\n')[0][:50], fail.strip().split('\n')[-1][:100]))
        elif not fail and exp and out.rstrip('\n').split('\n') != exp and not _expects_err(exp):
            probs.append(('DIFF', src.split('\n')[0][:50], f'{out.strip()[:60]!r} ≠ {exp[0][:60]!r}'))
    return probs

def main(course, only=None):
    wdir = os.path.join(HERE, 'whole', course)
    cdir = os.path.join(COURSES, course)
    cj = json.load(open(os.path.join(cdir, 'course.json'), encoding='utf-8'))
    new_units = []
    for u in cj['units']:
        if only and (u.get('part_of') or u['id']) not in only:
            new_units.append(u); continue
        if u['id'] and re.search(r'[a-z]$', u['id']) and u.get('part_of'): continue
        wf = os.path.join(wdir, u.get('whole') or u['file'] or '')
        if not os.path.exists(wf):
            new_units.append(u); continue
        unit = json.load(open(wf, encoding='utf-8'))
        parts = build(unit)
        parts, rep = add_setup(parts, unit) if len(parts) > 1 else (parts, [])
        base = u.get('whole') or u['file']
        for k, p in enumerate(parts):
            errs = validate_unit(p, n_questions=len(p['quiz']['questions']))
            probs = check_run(p)
            fname = base if k == 0 else base.replace('.json', '').replace(unit['id'] + '-', unit['id'] + LABEL[k] + '-', 1) + '.json'
            if k == 0 and len(parts) > 1: fname = base
            json.dump(p, open(os.path.join(cdir, fname), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
            print(f"{p['id']} {p['minutes']}分 题{[q['answer'] for q in p['quiz']['questions']]} 块{len(p['blocks'])}", errs or '', probs or '')
            e = dict(u); e.update(id=p['id'], title=p['title'], en=p['en'], minutes=p['minutes'], file=fname)
            e['whole'] = base
            if k: e['part_of'] = unit['id']
            new_units.append(e)
        for r in rep: print('   ', r)
    cj['units'] = new_units
    json.dump(cj, open(os.path.join(cdir, 'course.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:] or None)
