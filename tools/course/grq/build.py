"""GRE Quant 官方练习套题课程生成器。
数据：sets.json（7 套：算术 / 代数 / 几何 / 数据分析 + 3 套混合，共 150 题；答案来自 ETS 官方 Quantitative Reasoning 练习册的答案表）
图片：courses/gre-q/img/<套>/ 里的题目、解析、图表截图（由 extract/ 里的脚本从 PDF 切出，仅供个人学习）
输出：courses/gre-q/course.json 和 uNN-*.json
运行：python tools/course/grq/build.py
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from unitlib import REPO
from qset_check import validate_qset

sets = json.load(open(os.path.join(HERE, 'sets.json'), encoding='utf-8'))
out = os.path.join(REPO, 'courses', 'gre-q')
os.makedirs(out, exist_ok=True)
units, errors = [], []
for i, s in enumerate(sets, 1):
    n = len(s['items'])
    mixed = s['id'].startswith('m')
    title = f'{s["zh"]}（{n} 题）' if mixed else f'{s["zh"]}专题（{n} 题）'
    minutes = min(50, max(10, -(-int(n * 1.75 * 10) // 50) * 5))      # 约每题 1.75 分钟，向上取整到 5 分钟
    uid = f'u{i:02d}-{s["id"]}'
    unit = {
        'id': uid, 'title': title, 'en': f'Quantitative Reasoning — {s["en"]}', 'minutes': minutes, 'practice': True,
        'objectives': [f'独立做完 {n} 道 ETS 官方 Quant 真题，**全部做完再点提交**（提交前不显示对错）',
                       '提交后逐题看对错、正确答案和官方解析；错题先自己重算一遍，再看解析',
                       '页面底部有本套对错总结：总分、正确率、各题型表现和错题清单'],
        'blocks': [{'type': 'gre-qset', 'base': 'courses/gre-q/img/', 'source': f'ETS《Official GRE Quantitative Reasoning Practice Questions》· {s["zh"]}', 'items': s['items']}],
        'references': [],
    }
    errors += validate_qset(unit, out)
    json.dump(unit, open(os.path.join(out, f'{uid}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    units.append({'id': uid, 'title': title, 'en': unit['en'], 'minutes': minutes, 'file': f'{uid}.json', 'practice': True, 'hasQuiz': False})
course = {
    'id': 'gre-q', 'title': 'GRE Quant 官方练习题：7 套 Practice Set',
    'order': 17, 'order_note': '选修，申请准备：官方 Quant 真题 150 道，算术 / 代数 / 几何 / 数据分析各一套，另有 3 套混合',
    'tier': 'elective', 'tags': ['GRE'], 'units': units,
}
json.dump(course, open(os.path.join(out, 'course.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'{len(units)} 节，{sum(len(s["items"]) for s in sets)} 题')
if errors:
    print('\n'.join(errors)); sys.exit(1)
