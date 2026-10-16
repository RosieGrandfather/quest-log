"""Apply the independently reviewed answer key for 2025-01-14 Verbal 1.

This is a content migration, not an ETS answer-sheet transcription. Running it
again preserves the original key recorded on the first run.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FORMAT = 'gre-vx-text-v2-answers-20261016'
# TC choices are indices within EACH column, not flattened A-I letters.
KEYS = [[1], [1, 2], [2, 0, 0], [0, 1], None, [4, 5], [2, 5],
        [1, 3], [1, 4], [2], [3], [1]]
REASONS = [
    '艺术被看作主观的（subjective），与物理学回避内心思想形成对照。enigmatic（难以理解的）不能表达这里的主客观区别。',
    '以往作品 lampooned（讽刺、丑化）这些历史人物；Mendez 避免 caricature（夸张讽刺式刻画），所以她 deviates from（偏离）这一传统。依次选 deviates from、caricature。',
    'Yet 转折后说科学家很少声誉受损（suffer reputational losses）。负面描绘归咎于法律过程玷污（tainted）科学；正面描绘把科学看作制衡（a counterweight to）法律不稳定性的力量。',
    '文章说蓝调超越严格的文化边界，Ellison 的定义只受个人表达能力限制，支持“不限于特定文化传统”；又明确说其定义 privileges the personal，支持“强调个人而非集体历史”。结尾讨论文学作品，并未要求蓝调必须写成文字。',
    '选第 3 句（Ralph Ellison’s definition…）。第 1 句给出常规看法；第 2 句只是概括指出文化边界可被超越；第 3 句才具体给出 Ellison 以个人经历为核心的另一种定义。',
    '能跨许多领域写作，与局限单一领域的 specialization 相对；lordly 又提示高傲态度。disdain for 与 scorn for 都表示轻视，填入后句意一致。',
    'Although…nonetheless 表示让步：承认证据不足，却仍作确定性结论和大范围概括。insufficient 与 meager 都表示证据不足，indirect 只表示间接，并非等义。',
    '计算机进入汽车和医疗设备后，软件商一概免除后果责任的立场将难以成立、难以辩护。untenable 与 indefensible 构成等义答案。',
    '无缝扩建恰好违背文物保护原则：不同时期的界线应清楚可辨。demarcation of 与 lines between 都表达时期之间的分界。',
    '全文介绍 Jeffrey 对妇女参与废奴运动的研究，并与既有学者的叙述作对照；两处 disputes 展开这种对照。没有介绍对她写作的影响，也没有指出她著作内部自相矛盾。',
    '题目问先前 scholars 所举的例子。第 2 句明确提到持续散发反奴隶制请愿书（circulation of petitions）；募捐集市则是后文 Jeffrey 用来反驳边缘化说的例子。',
    '1840 年代的募捐集市说明，即使运动在 1830 年代末分裂，妇女仍有效参与；这个例子支持 Jeffrey 对“妇女从此被边缘化”的反驳。',
]
SOURCES = {
    1: 'https://gre.kmf.com/explain/question/d2cb7j-0.html?isFav=0',
    2: 'https://grev2.kmf.com/explain/question/22cb8j-0.html?isFav=0',
    3: 'https://gre.kmf.com/explain/question/02cbbj-0.html?isFav=0',
    5: 'https://gre.kmf.com/explain/question/a2bruj-0.html?isFav=0',
    6: 'https://gre.kmf.com/explain/question/62e24j-0.html?isFav=0',
    7: 'https://bj.xdf.cn/wenzhang/xinwen/18199.html',
    9: 'https://gre.kmf.com/explain/question/12cbej-0.html?isFav=0',
    10: 'https://gre.kmf.com/explain/index/d1pf4j',
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value, indent=1):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=indent) + '\n', encoding='utf-8')


def main():
    data_path = HERE / 'data.json'
    data = read(data_path)
    section = data[0]['sections'][0]
    assert data[0]['id'] == '2025-01-14' and section['M'] == 12
    unit = read(ROOT / 'courses/gre-vx/u01-2025-01-14-v1.json')
    section['answerFormat'] = FORMAT
    for item in section['items']:
        n = item['n']
        if 'answerReview' not in item:
            item['answerReview'] = {
                'date': '2026-10-16', 'status': 'independently-reviewed',
                'basis': '题意与原文逐题推理；非 ETS 官方答案表',
                'previous': {k: item[k] for k in ('ans', 'ansText', 'answerPending') if k in item},
            }
        if n in SOURCES:
            item['answerReview']['corroboratingSource'] = SOURCES[n]
        if KEYS[n - 1] is not None:
            item['ans'] = KEYS[n - 1]
        else:
            item['ansText'] = unit['blocks'][0]['items'][4]['txt']['sentences'][2]
        item.pop('answerPending', None)
        item.pop('answerReviewReason', None)
        item['explanation'] = REASONS[n - 1]
    write(data_path, data, indent=0)


if __name__ == '__main__':
    main()
