"""GRE 高频核心词（S 级）课程生成器。
数据：words_shuffled.json（顺序已打乱，固定随机种子）、entries_NN.txt（每词一行：词|英文释义|近义词|反义词|中文覆盖）、passages_NN.txt（每 5 词一段例句：组号|短文）
输出：courses/gre-v/course.json 和 uNN-set.json
运行：python tools/course/grev/build.py
"""
import json, os, re, random, glob, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from unitlib import validate_unit, REPO

PER_UNIT, PER_PASSAGE = 20, 5
words = json.load(open(os.path.join(HERE, 'words_shuffled.json'), encoding='utf-8'))
entries = {}
for f in sorted(glob.glob(os.path.join(HERE, 'entries_*.txt'))):
    for ln in open(f, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if not ln.strip(): continue
        p = ln.split('|')
        assert len(p) == 5, f'{f}: 字段数不对：{ln}'
        w, en, syn, ant, zh = [x.strip() for x in p]
        entries[w] = dict(en=en, syn=[x.strip() for x in syn.split(',') if x.strip() and x.strip() != '—'],
                          ant=[x.strip() for x in ant.split(',') if x.strip() and x.strip() != '—'], zh=zh)
passages = {}
for f in sorted(glob.glob(os.path.join(HERE, 'passages_*.txt'))):
    for ln in open(f, encoding='utf-8'):
        if ln.strip():
            k, t = ln.rstrip('\n').split('|', 1); passages[int(k)] = t
n_done = 0
while n_done < len(words) and (n_done // PER_PASSAGE) in passages and words[n_done]['w'] in entries: n_done += 1
if n_done < len(words): n_done = (n_done // PER_PASSAGE) * PER_PASSAGE
n_units_total = -(-len(words) // PER_UNIT)
print(f'已写好 {n_done} / {len(words)} 个词，共 {n_units_total} 组')
errors = []
POS_FIX = {'parsimonious':'adj.', 'arrogance':'n.', 'metaphor':'n.', 'seemly':'adj.', 'deadpan':'adj.', 'invective':'n.'}
def item(i):
    w = words[i]; e = entries[w['w']]
    return dict(w=w['w'], ipa=w['ipa'], pos=POS_FIX.get(w['w'], w['pos']), zh=e['zh'] or w['zh'].replace('\n', ' '), en=e['en'], syn=e['syn'], ant=e['ant'])
MARK = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')
def lemmas(text): return [(m.group(2) or m.group(1)).strip() for m in MARK.finditer(text)]

def make_quiz(uid, its, pas, rng):
    """5 题：词→中文 ×2、中文→词、近义词匹配、例句填空。选项干扰项取自同一小节或全表。"""
    allzh = [x['zh'] for x in (item(i) for i in range(n_done)) ]
    qs = []
    def pk(x): return (x['pos'] or '?')[0]
    def ranked(w):
        pool = [x for x in its if x['w'] != w['w'] and x['zh'] != w['zh']]
        rng.shuffle(pool); pool.sort(key=lambda x: pk(x) != pk(w))     # 同词性的优先当干扰项
        seen, out = set(), []
        for x in pool:                                               # 干扰项的中文不能重复
            if x['zh'] not in seen: seen.add(x['zh']); out.append(x)
        return out
    def distract_zh(w): return [x['zh'] for x in ranked(w)][:3]
    def distract_words(w): return [x['w'] for x in ranked(w)][:3]
    pick = its[:]; rng.shuffle(pick)
    a, b, c, d, e = pick[:5]
    for w in (a, b):
        qs.append(dict(q=f'**{w["w"]}** 的意思最接近：', correct=w['zh'], wrong=distract_zh(w),
                       explain=f'{w["w"]}：{w["zh"]}（{w["en"]}）。近义词：{", ".join(w["syn"]) or "—"}。'))
    qs.append(dict(q=f'哪个词的意思是「{c["zh"]}」？', correct=c['w'], wrong=distract_words(c),
                   explain=f'{c["w"]}：{c["zh"]}（{c["en"]}）。'))
    dw = [x for x in its if x['syn']] 
    w = d if d['syn'] else dw[0]
    s = rng.choice(w['syn'])
    qs.append(dict(q=f'哪个词和 **{s}** 的意思最接近？', correct=w['w'], wrong=distract_words(w),
                   explain=f'{w["w"]} 与 {s} 近义：{w["en"]}。'))
    # 例句填空：从短文里挖掉一个目标词
    pi = rng.randrange(len(pas)); ptxt = pas[pi][0]; plist = pas[pi][1]
    tw = rng.choice(plist)
    def blank(m):
        return '____' if (m.group(2) or m.group(1)).strip() == tw['w'] else m.group(1)
    sentence = MARK.sub(blank, ptxt)
    others = distract_words(tw)
    qs.append(dict(q='选最适合填入空格的词：\n\n> ' + sentence, correct=tw['w'], wrong=others,
                   explain=f'{tw["w"]}：{tw["zh"]}（{tw["en"]}）。'))
    # 选项排列：正确答案位置打散
    pos = [0, 1, 2, 3, rng.randrange(4)]; rng.shuffle(pos)
    while len(set(pos)) < 3 or max(pos.count(x) for x in pos) > 2: rng.shuffle(pos); pos[4] = rng.randrange(4)
    out = []
    for q, p in zip(qs, pos):
        opts = q['wrong'][:3]; opts.insert(p, q['correct'])
        out.append(dict(q=q['q'], options=opts, answer=p, explain=q['explain']))
    return out

def wrap(text): return text
units, meta = [], []
for u in range(n_done // PER_UNIT + (1 if n_done % PER_UNIT else 0)):
    lo, hi = u * PER_UNIT, min(n_done, (u + 1) * PER_UNIT)
    its = [item(i) for i in range(lo, hi)]
    blocks, pas = [], []
    for g in range(lo // PER_PASSAGE, -(-hi // PER_PASSAGE)):
        gi = [item(i) for i in range(g * PER_PASSAGE, min(hi, (g + 1) * PER_PASSAGE))]
        text = passages[g]
        found = sorted(lemmas(text)); want = sorted(x['w'] for x in gi)
        if found != want: errors.append(f'第 {g} 段例句里标出的词 {found} ≠ 应有的词 {want}')
        gloss = {x['w']: re.split(r'[；;]', x['zh'])[0][:24] for x in gi}
        blocks.append({"type": "vocab", "items": gi})
        blocks.append({"type": "passage", "text": text, "gloss": gloss})
        pas.append((text, gi))
    uid = f'u{u+1:02d}'
    rng = random.Random(1000 + u)
    unit = dict(id=uid, title=f'S 级核心词 · 第 {u+1} 组', en=f'GRE Core Vocabulary · Set {u+1}', minutes=35,
                objectives=[f'认识并会读这 {len(its)} 个高频词：点 🔊 音标听发音，跟读一遍',
                            '记住每个词的**中文意思**和**英文释义**，并用近义词、反义词把意思连成一片',
                            '在例句短文里认出这些词，体会它们在句子里的语气（褒、贬、中性）'],
                blocks=blocks, references=[], quiz=dict(questions=make_quiz(uid, its, pas, rng)))
    errors += validate_unit(unit, n_questions=5)
    units.append(unit)
if errors: raise SystemExit('检查没通过：\n  ' + '\n  '.join(errors))
cdir = os.path.join(REPO, 'courses', 'gre-v'); os.makedirs(cdir, exist_ok=True)
cu = []
for unit in units:
    fn = f'{unit["id"]}-set.json'
    json.dump(unit, open(os.path.join(cdir, fn), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    cu.append(dict(id=unit['id'], title=unit['title'], en=unit['en'], minutes=unit['minutes'], file=fn, direct=True))
for u in range(len(units), n_units_total):      # 还没写好的组先占位
    cu.append(dict(id=f'u{u+1:02d}', title=f'S 级核心词 · 第 {u+1} 组', en=f'GRE Core Vocabulary · Set {u+1}', minutes=35, file=None,
                   covers='待写'))
course = dict(id='gre-v', title='GRE 核心词汇 S 级：机经里出现过的再要你命 3000',
              subtitle=f'把「再要你命 3000」里同时出现在机经（霍 V6）里的 {len(words)} 个词，按乱序拆成每组 {PER_UNIT} 个词的小节：中英释义、近义词、反义词、点音标发音、每 {PER_PASSAGE} 个词一段例句短文，最后 5 道小测验。',
              order=16, order_note='选修，申请准备：背 GRE 词汇，可以和别的课穿插着学', tier='elective', units=cu)
json.dump(course, open(os.path.join(cdir, 'course.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(f'写入 courses/gre-v：{len(units)} 个小节（{n_done} 词），占位 {n_units_total-len(units)} 个')
