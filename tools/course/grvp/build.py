"""GRE Verbal 官方练习套题课程生成器。
数据：sets.json（12 套题：阅读 / 文本补全 / 句子等价各「低·中·高」三套，加混合 3 套；题目、选项、答案、解析取自 ETS 官方 Verbal Reasoning 练习册，仅供个人学习）
输出：courses/gre-vr/course.json 和 uNN-*.json
运行：python tools/course/grvp/build.py
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from unitlib import REPO
from practice_check import validate_practice

SEC = {'rc': ('阅读理解', 'Reading Comprehension'), 'tc': ('文本补全', 'Text Completion'), 'se': ('句子等价', 'Sentence Equivalence'), 'mix': ('混合', 'Mixed')}
DIFF = {'easy': '低', 'medium': '中', 'hard': '高', 'mixed': '官方未标难度'}
sets = json.load(open(os.path.join(HERE, 'sets.json'), encoding='utf-8'))
out = os.path.join(REPO, 'courses', 'gre-vr')
os.makedirs(out, exist_ok=True)
units, errors = [], []
for i, s in enumerate(sets, 1):
    zh, en = SEC[s['section']]
    n = len(s['items'])
    mix_no = s['id'].split('-')[1] if s['section'] == 'mix' else ''
    title = f'混合练习 · 第 {mix_no} 套（{n} 题）' if s['section'] == 'mix' else f'{zh} · 难度{DIFF[s["difficulty"]]}（{n} 题）'
    minutes = min(50, max(10, -(-int(n * 1.75 * 10) // 50) * 5))      # 约每题 1.75 分钟，向上取整到 5 分钟
    uid = f'u{i:02d}-{s["id"]}'
    blocks_items = []
    for it in s['items']:
        blocks_items.append({'id': f'q{it["n"]}', 'kind': it['kind'], 'passage': it['passage'], 'stem': it['stem'], 'groups': it['groups'], 'expl': it['expl']})
    unit = {
        'id': uid, 'title': title, 'en': f'{en} — {s["source"].split("· ")[-1]}',
        'minutes': minutes, 'practice': True,
        'objectives': [f'独立做完 {n} 道 ETS 官方真题，**全部做完再点提交**（提交前不显示对错，和真考一样）',
                       '提交后逐题看对错、正确答案和官方解析；错题先自己想一遍为什么错，再看解析',
                       '页面底部有本套对错总结：总分、正确率、各题型表现和错题清单'],
        'blocks': [{'type': 'gre-set', 'section': s['section'], 'difficulty': s['difficulty'], 'source': 'ETS《Official GRE Verbal Reasoning Practice Questions》· ' + s['source'],
                    'passages': s['passages'], 'items': blocks_items}],
        'references': [],
    }
    errors += validate_practice(unit)
    json.dump(unit, open(os.path.join(out, f'{uid}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    units.append({'id': uid, 'title': title, 'en': unit['en'], 'minutes': minutes, 'file': f'{uid}.json', 'practice': True, 'hasQuiz': False,
                  'difficulty': s['difficulty']})
course = {
    'id': 'gre-vr', 'title': 'GRE Verbal 官方练习题：12 套 Practice Set',
    'subtitle': 'ETS 官方 Verbal Reasoning 练习册里的真题，按原书分成 12 套：阅读理解、文本补全、句子等价各「低 / 中 / 高」难度三套，另有 3 套混合。每套做完再提交，才显示对错、官方解析和本套总结。',
    'order': 16, 'order_note': '选修，申请准备：Verbal 是弱项，词汇课背一段时间后穿插着做', 'tier': 'elective', 'tags': ['GRE'],
    'units': units,
}
json.dump(course, open(os.path.join(out, 'course.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'{len(units)} 节，{sum(len(s["items"]) for s in sets)} 题')
if errors:
    print('\n'.join(errors)); sys.exit(1)
