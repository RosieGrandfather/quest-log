"""检查 courses/ 下所有课程。

  python tools/course/validate.py            # 格式、公式、测验、文件是否对得上
  python tools/course/validate.py --online   # 另外核实所有视频可嵌入、所有参考链接能打开（要联网，较慢）
"""
import json, os, sys, urllib.request, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(__file__))
from unitlib import COURSES, validate_unit, python_cells

# 这些课的代码块必须「一个知识点一段」：单个代码块（不含输出行）不超过 MAX_CELL 行，解释紧跟在后面
SPLIT_COURSES = {'py-0'}
MAX_CELL = 35
from yt import verify

def main(online):
    errors, videos, links = [], set(), set()
    long_cells = []
    index = json.load(open(os.path.join(COURSES, 'index.json'), encoding='utf-8'))
    for entry in index['courses']:
        cdir = os.path.join(COURSES, entry['path'])
        course = json.load(open(os.path.join(cdir, 'course.json'), encoding='utf-8'))
        if course['id'] != entry['id']: errors.append(f"index.json 的 id {entry['id']} ≠ course.json 的 {course['id']}")
        ids = [u['id'] for u in course['units']]
        if len(ids) != len(set(ids)): errors.append(f"{course['id']}: 章节 id 重复")
        done = 0
        for u in course['units']:
            if not u.get('file'): continue
            path = os.path.join(cdir, u['file'])
            if not os.path.exists(path): errors.append(f"{course['id']}/{u['id']}: 找不到文件 {u['file']}"); continue
            unit = json.load(open(path, encoding='utf-8'))
            if unit['id'] != u['id']: errors.append(f"{u['file']}: 文件里的 id {unit['id']} ≠ course.json 的 {u['id']}")
            if unit['title'] != u['title']: errors.append(f"{u['file']}: 标题和 course.json 不一致")
            nq = len(unit['quiz']['questions']) if u.get('whole') else 10     # 拆分出来的小节，每个 3–5 题
            if u.get('whole') and not 2 <= nq <= 5: errors.append(f"{u['id']}: 拆分小节的测验应有 2–5 题，现在 {nq} 题")
            if u['minutes'] > 50: errors.append(f"{course['id']}/{u['id']}: 一节 {u['minutes']} 分钟，超过 50 分钟（用 tools/course/split.py 拆开）")
            errors += validate_unit(unit, n_questions=nq)
            for j, lang, n, _ in python_cells(unit):
                if n > MAX_CELL:
                    msg = f"{course['id']}/{u['id']} 块{j}: 代码块 {n} 行，太长（拆成一个知识点一段，解释紧跟其后）"
                    if course['id'] in SPLIT_COURSES: errors.append(msg)
                    else: long_cells.append(msg)
            videos |= {b['id'] for b in unit['blocks'] if b['type'] == 'video' and b['provider'] == 'youtube'}
            links |= {r['url'] for r in unit.get('references', [])}
            done += 1
        print(f"{course['id']}：{done} / {len(course['units'])} 节有内容")
    if long_cells: print(f'提示：{len(long_cells)} 个代码块超过 {MAX_CELL} 行（非 py-0，不算错误，以后重写时拆开）')
    if online:
        print(f'核实 {len(videos)} 个 YouTube 视频、{len(links)} 个链接 …')
        with cf.ThreadPoolExecutor(8) as ex:
            for r in ex.map(verify, sorted(videos)):
                if r[1] == 'NOT EMBEDDABLE / MISSING': errors.append(f'视频 {r[0]} 不存在或不能嵌入')
            def ok(u):
                try:
                    req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 Chrome/126'})
                    with urllib.request.urlopen(req, timeout=25) as r: return u, r.status
                except Exception as e: return u, getattr(e, 'code', type(e).__name__)
            for u, s in ex.map(ok, sorted(links)):
                if s != 200: errors.append(f'链接打不开（{s}）：{u}')
    if errors:
        print('\n发现问题：'); [print('  -', x) for x in errors]; sys.exit(1)
    print('全部通过 ✓')

if __name__ == '__main__':
    main('--online' in sys.argv)
