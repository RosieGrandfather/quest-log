"""GRE Verbal 2025 年真题回忆课程生成器（逐鹿整理的考场截图，25 套 × 2 个 Verbal section）。
数据：data.json（每个 section 的题号、题型、答案、对应截图页；答案来自各套 PDF 末页的答案表，目视录入）
输入：PAGES 目录（每套一个子目录 pNN.png，由 pdftoppm / pdfimages 从 PDF 逐页转出）
输出：courses/gre-vx/（img/<套>/<section>-<题号>[b].webp + course.json + uNN-*.json）
裁剪：去掉页眉（Section/Question 页码、计时器、按钮、水印二维码），转 WebP 缩小体积。
运行：python tools/course/grvx/build.py <PAGES 目录> [套 id ...]   （不给套 id 就全部生成；图片已存在则跳过）
"""
import json, os, sys, subprocess, re
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(HERE, '..', 'grq'))
from unitlib import REPO
from qset_check import validate_qset

MAXW = 1000
data = json.load(open(os.path.join(HERE, 'data.json'), encoding='utf-8'))
pages_dir = sys.argv[1]
only = set(sys.argv[2:])
OCR = os.path.join(HERE, 'ocr')
def load_txt(sid):
    f = os.path.join(OCR, f'txt-{sid}.json')
    return json.load(open(f, encoding='utf-8')) if os.path.exists(f) else {}
out = os.path.join(REPO, 'courses', 'gre-vx')

def header_bottom(im):
    """页眉（含 Section X | Question N 那一行）的下边缘 y；找不到就按比例猜。"""
    W, H = im.size
    band = im.crop((0, 0, int(W * .5), int(H * .2))).convert('L')
    sc = 2 if W < 1500 else 1
    if sc > 1: band = band.resize((band.size[0] * sc, band.size[1] * sc))
    f = f'/tmp/hb_{os.getpid()}.png'; band.save(f)
    t = subprocess.run(['tesseract', f, '-', '--psm', '6', 'tsv'], capture_output=True, text=True).stdout
    for ln in t.split('\n')[1:]:
        c = ln.split('\t')
        if len(c) >= 12 and c[11].strip().lower().startswith('section') and int(c[10] if c[10].lstrip('-').isdigit() else 0) > 30:
            return int((int(c[7]) + int(c[9])) / sc) + 6
    return int(H * .095)

def save(src, dst, hb_cache):
    if os.path.exists(dst): return
    im = Image.open(src).convert('RGB')
    y0 = header_bottom(im)
    H = im.size[1]
    if not .03 * H <= y0 <= .2 * H: y0 = hb_cache.get('y', int(H * .095)) if hb_cache.get('y') else int(H * .095)
    else: hb_cache['y'] = y0
    im = im.crop((0, y0, im.size[0], H))
    if im.size[0] > MAXW: im = im.resize((MAXW, round(im.size[1] * MAXW / im.size[0])), Image.LANCZOS)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im.save(dst, 'WEBP', quality=62, method=6)

units, errors = [], []
n_unit = 0
for s in data:
    for v, sec in enumerate(s['sections'], 1):
        n_unit += 1
        uid = f'u{n_unit:02d}-{s["id"]}-v{v}'
        if only and s['id'] not in only: continue
        M = sec['M']; items = []
        cache = {}
        txts = load_txt(s['id'])
        for it in sec['items']:
            names = []
            for j, pg in enumerate(it['pages']):
                nm = f'{s["id"]}/{sec["sec"]}-{it["n"]:02d}{"" if j == 0 else "b"}.webp'
                save(os.path.join(pages_dir, s['id'], pg), os.path.join(out, 'img', nm), cache)
                names.append(nm)
            o = {k: it[k] for k in ('n', 'kind', 'nopt', 'blanks', 'ans', 'ansText') if k in it}
            o['img'] = names[0]
            tx = txts.get(f'{sec["sec"]}-{it["n"]}')
            if tx and tx.get('ok'):
                o['txt'] = {k: tx[k] for k in ('pass', 'stem', 'opts', 'cols') if tx.get(k)}
            if len(names) > 1: o['imgs'] = names
            items.append(o)
        title = f'{s["zh"]} · Verbal {v}（{M} 题）'
        minutes = 18 if M == 12 else 23
        missing = [q for q in range(1, M + 1) if q not in {i['n'] for i in items}]
        objs = [f'按真实考试节奏做完 {M} 题（建议 {minutes} 分钟），**全部做完再点提交**（提交前不显示对错）',
                '提交后逐题看对错和正确答案；错题先回原文找依据，再决定是词汇问题还是逻辑问题',
                '这是考生考后回忆/拍屏整理的版本，没有官方解析；答案取自原整理者的答案表']
        if missing: objs.append(f'原 PDF 缺第 {"、".join(map(str, missing))} 题的截图，所以这一节只有 {len(items)} 题')
        if any(i['kind'] == 'ss' for i in items): objs.append('「选句子」题没法在网页里点选，请写下你选的句子（序号或开头几个词），交卷后对照答案自评，不计入分数')
        unit = {'id': uid, 'title': title, 'en': f'Verbal Reasoning — {s["id"]} section {v}', 'minutes': minutes, 'practice': True,
                'objectives': objs,
                'blocks': [{'type': 'gre-qset', 'base': 'courses/gre-vx/img/', 'source': f'2025 年 GRE 考场回忆真题（逐鹿留学整理）· {s["zh"]}', 'noteTail': '（考场截屏整理版，仅供个人学习；没有官方解析）', 'items': items}],
                'references': []}
        errors += validate_qset(unit, out)
        json.dump(unit, open(os.path.join(out, f'{uid}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(uid, len(items), flush=True)
# course.json（所有 section 的清单，不论本次生成哪几套）
allunits = []
n_unit = 0
for s in data:
    for v, sec in enumerate(s['sections'], 1):
        n_unit += 1
        uid = f'u{n_unit:02d}-{s["id"]}-v{v}'
        M = sec['M']
        allunits.append({'id': uid, 'title': f'{s["zh"]} · Verbal {v}（{M} 题）', 'en': f'Verbal Reasoning — {s["id"]} section {v}', 'minutes': 18 if M == 12 else 23, 'file': f'{uid}.json', 'practice': True, 'hasQuiz': False})
course = {'id': 'gre-vx', 'title': 'GRE Verbal 2025 年真题回忆：25 套 · 50 个 Section',
          'order': 16, 'order_note': '选修，申请准备：2025 年 1–4 月考场回忆真题的 Verbal 部分，每个 section 一节（12 题 / 15 题各一）',
          'tier': 'elective', 'tags': ['GRE'], 'units': allunits}
json.dump(course, open(os.path.join(out, 'course.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'{len(allunits)} 节')
if errors:
    print('\n'.join(errors)); sys.exit(1)
