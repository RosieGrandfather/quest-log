"""GRE 写作练习课程生成器（gre-aw）。
数据：essays.json（extract.py 从 ETS《Official Guide》的文本层抽出：3 道 Issue + 3 道 Argument，每题含 6–1 分各一篇官方样文和阅卷评语；评分标准）
输出：courses/gre-aw/course.json 和 uNN-*.json
运行：python tools/course/grw/build.py
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from unitlib import REPO
from essay_check import validate_essay

data = json.load(open(os.path.join(HERE, 'essays.json'), encoding='utf-8'))
tasks, rubric = data['tasks'], data['rubric']

def clean(t):
    return re.sub(r'(\w)- ([a-z])', r'\1-\2', t)          # 行尾断词留下的 "well- articulated"

SPLIT = [' conveys ideas', ' develops the position with relevant', ' contains occasional', ' is poorly focused', ' demonstrates sufficient control',
         ' is limited in the logical', ' has serious problems', ' has problems in language']
def split_bullets(bullets):
    out = []
    for b in bullets:
        parts = [b]
        for s in SPLIT:
            parts = [q for p in parts for q in re.split(f'(?={re.escape(s)})', p)]
        out += [clean(p.strip()) for p in parts if p.strip()]
    return out

def split_strategy(ps):
    out = []
    for p in ps:
        for q in re.split(r'(?<=[.)”"])\s+(?=The assumption that |That (?:the|it|use|a|an|state|city|there|residents|people) )|(?<=include:)\s+|(?<=are:)\s+', clean(p)):
            if q.strip(): out.append(q.strip())
    return out

TITLES = {
    'issue-sample': ('Issue 1 · 技术依赖与独立思考', 'Analyze an Issue — Technology and thinking for oneself'),
    'issue-t1': ('Issue 2 · 表扬好行为、忽略坏行为', 'Analyze an Issue — Praise positive actions, ignore negative ones'),
    'issue-t2': ('Issue 3 · 企业的社会责任与利润', 'Analyze an Issue — Corporate responsibility'),
    'arg-sample': ('Argument 1 · Mason 河与河滨设施预算', 'Analyze an Argument — Mason River'),
    'arg-t1': ('Argument 2 · Tertia 岛的育儿研究', 'Analyze an Argument — Tertia island'),
    'arg-t2': ('Argument 3 · Movies Galore 缩减营业开支', 'Analyze an Argument — Movies Galore'),
}
order = ['issue-sample', 'issue-t1', 'issue-t2', 'arg-sample', 'arg-t1', 'arg-t2']
by = {t['id']: t for t in tasks}
out = os.path.join(REPO, 'courses', 'gre-aw')
os.makedirs(out, exist_ok=True)
units, errors = [], []
for i, tid in enumerate(order, 1):
    t = by[tid]
    title, en = TITLES[tid]
    uid = f'u{i:02d}-{tid}'
    kind_zh = 'Issue（议论文）' if t['kind'] == 'issue' else 'Argument（论证分析）'
    unit = {
        'id': uid, 'title': title, 'en': en, 'minutes': 45, 'practice': True,
        'objectives': [f'限时 30 分钟，在页面里写一篇 {kind_zh}（打字，自动保存；不想计时也可以先不点计时）',
                       '写完再看官方评分标准、6–1 分各一篇官方样文和阅卷评语，对照自己的文章找差距',
                       '重点对照：有没有紧扣任务指令、有没有具体的理由或例子、结构是否清楚；语言错误留到最后再改'],
        'blocks': [{
            'type': 'gre-essay', 'kind': t['kind'], 'source': 'ETS《The Official Guide to the GRE General Test》· ' + t['src'],
            'prompt': [clean(p) for p in t['prompt']], 'strategy': split_strategy(t['strategy']),
            'rubric': [{'score': r['score'], 'summary': clean(r['summary']), 'bullets': split_bullets(r['bullets'])} for r in rubric[t['kind']] if r['score'] > 0],
            'responses': [{'score': r['score'], 'essay': [clean(p) for p in r['essay']], 'commentary': [clean(p) for p in r['commentary']]} for r in t['responses']],
        }],
        'references': [],
    }
    errors += validate_essay(unit)
    json.dump(unit, open(os.path.join(out, f'{uid}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    units.append({'id': uid, 'title': title, 'en': en, 'minutes': 45, 'file': f'{uid}.json', 'practice': True, 'hasQuiz': False})
course = {
    'id': 'gre-aw', 'title': 'GRE 写作官方练习：Issue 与 Argument 各 3 题',
    'order': 18, 'order_note': '选修，申请准备：每题限时 30 分钟，写完对照官方评分标准、6–1 分样文和阅卷评语',
    'tier': 'elective', 'tags': ['GRE'], 'units': units,
}
json.dump(course, open(os.path.join(out, 'course.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'{len(units)} 节')
if errors:
    print('\n'.join(errors)); sys.exit(1)
