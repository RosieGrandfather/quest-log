"""从 ETS《Official Guide》PDF 的文本层（pdftotext -layout 的输出）里抽出写作题：题目、官方思路提示、各分数样文和阅卷评语。
用法：python extract.py guide_raw.txt out.json   （guide_raw.txt = pdftotext -layout ETS.pdf 的输出）"""
import re, json, sys
L = open(sys.argv[1], encoding='utf-8').read().replace('\f', '').split('\n')
STOP = re.compile(r'^(Answers and Explanations|GRE Scoring Guide|\s*SECTION \d|Analyze an (Argument|Issue) Task|Analytical Writing Sample|\s*NO TEST MATERIAL)')
NOISE = re.compile(r'^\s*(NO TEST MATERIAL ON THIS PAGE|\d{1,3}|.*GRE.{0,20}Official Guide.*)\s*$')

def paras(lines):
    out, cur = [], []
    for ln in lines:
        if not ln.strip():
            if cur: out.append(' '.join(cur)); cur = []
            continue
        if NOISE.match(ln): continue
        if re.match(r'^\s{3,}\S', ln) and cur and not re.match(r'^\s{6,}\S', ln) is None and False: pass
        if re.match(r'^\s{3,5}\S', ln) and cur:      # 缩进 = 新段落
            out.append(' '.join(cur)); cur = []
        cur.append(re.sub(r'\s+', ' ', ln.strip()))
    if cur: out.append(' '.join(cur))
    return out

def responses(i):
    """i = 第一个 'Score 6 Response' 所在行；返回 [{score, essay:[段], commentary:[段]}]"""
    res, cur, mode = [], None, None
    while i < len(L):
        ln = L[i]
        m = re.match(r'^\s*Score (\d) Response', ln)
        if m:
            cur = {'score': int(m.group(1)), 'essay': [], 'commentary': []}; res.append(cur); mode = 'essay'; buf = []; i += 1; continue
        if cur is not None and STOP.match(ln) and not ln.startswith('Reader'): break
        if cur is not None and re.match(r'^Reader Commentary', ln):
            cur['essay'] = paras(buf); mode = 'com'; buf = []; i += 1; continue
        if cur is not None: buf.append(ln)
        if cur is not None and (i + 1 >= len(L) or STOP.match(L[i + 1])):
            pass
        i += 1
        if cur is not None and mode == 'com':
            cur['commentary'] = paras(buf)
    for r in res: pass
    return res

def finish(res_lines_start):
    res, cur, mode, buf = [], None, None, []
    i = res_lines_start
    def close():
        if cur is None: return
        if mode == 'essay': cur['essay'] = paras(buf)
        else: cur['commentary'] = paras(buf)
    while i < len(L):
        ln = L[i]
        m = re.match(r'^\s*Score (\d) Response', ln)
        if m:
            close(); cur = {'score': int(m.group(1)), 'essay': [], 'commentary': []}; res.append(cur); mode = 'essay'; buf = []
        elif cur is not None and re.match(r'^Reader Commentary', ln):
            close(); mode = 'com'; buf = []
        elif cur is not None and STOP.match(ln) and mode == 'com':
            break
        else: buf.append(ln)
        i += 1
    close()
    return res

def find(pat, start=0):
    return next(i for i in range(start, len(L)) if re.match(pat, L[i]))

def block(a, b):
    return paras(L[a:b])

tasks = []
# 官方示范题（正文讲解部分）
a = find(r'^Sample Issue Task'); s = find(r'^Strategies for This Topic', a); r = find(r'^Essay Responses and Reader Commentary', s)
tasks.append(dict(id='issue-sample', kind='issue', src='官方指南「Sample Issue Task」', prompt=block(a + 1, s), strategy=block(s + 1, r), responses=finish(find(r'^\s*Score 6 Response', r))))
a = find(r'^Sample Argument Task'); s = find(r'^Strategies for This Topic', a); r = find(r'^Essay Responses and Reader Commentary', s)
tasks.append(dict(id='arg-sample', kind='argument', src='官方指南「Sample Argument Task」', prompt=block(a + 1, s), strategy=block(s + 1, r), responses=finish(find(r'^\s*Score 6 Response', r))))
# 两套模考的作文题 + 样文
heads = [(i, L[i].strip()) for i in range(len(L)) if re.match(r'^\s*ANALYZE AN (ISSUE|ARGUMENT)\s*$', L[i])]
for n, (i, h) in enumerate(heads):
    nxt = next((j for j in range(i, len(L)) if re.match(r'^\s*Score 6 Response', L[j])), None)
    # 样文区的标题后面紧跟题目；只处理后面 60 行内出现 Score 6 Response 的
    if nxt is not None and nxt - i < 60:
        kind = 'issue' if 'ISSUE' in h else 'argument'
        k = sum(1 for t in tasks if t['id'].startswith(('issue-t', 'arg-t')) and t['kind'] == kind) + 1
        tasks.append(dict(id=f'{"issue" if kind == "issue" else "arg"}-t{k}', kind=kind, src=f'官方指南 Practice Test {k} 的作文题与样文', prompt=block(i + 1, nxt), strategy=[], responses=finish(nxt)))

def rubric(a, b):
    out, cur = [], None
    for ln in L[a:b]:
        m = re.match(r'^\s*Score (\d)\s*$', ln)
        if m: cur = {'score': int(m.group(1)), 'summary': '', 'bullets': []}; out.append(cur); stage = 0; buf = []; continue
        if cur is None or cur['score'] == 0: continue
        t = ln.strip()
        if not t or t == 'A typical response in this category':
            if t and buf: cur['summary'] = ' '.join(buf); buf = []
            continue
        if not ln.startswith('   '):
            buf.append(t)                                  # 顶格：该分数的一句话概括
        else:
            if buf: cur['summary'] = ' '.join(buf); buf = []
            cur['bullets'].append(t) if (not cur['bullets'] or len(cur['_last']) < 66 if cur.get('_last') else True) else cur['bullets'].__setitem__(-1, cur['bullets'][-1] + ' ' + t)
            cur['_last'] = t
    for c in out: c.pop('_last', None)
    return out
ia = find(r'^GRE Scoring Guide: Analyze an Issue', find(r'^Essay Responses and Reader Commentary'))
aa = find(r'^GRE Scoring Guide: Analyze an Argument', ia); ee = find(r'^Score Level Descriptions', aa)
rub = {'issue': rubric(ia, aa), 'argument': rubric(aa, ee)}
json.dump({'tasks': tasks, 'rubric': rub}, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for t in tasks:
    print(t['id'], t['kind'], len(t['prompt']), 'strategy', len(t['strategy']), [(r['score'], sum(len(p.split()) for p in r['essay']), len(r['commentary'])) for r in t['responses']])
