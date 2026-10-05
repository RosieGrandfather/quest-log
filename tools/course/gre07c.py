from runlib import Notebook

nb = Notebook()

C_DIAG = nb.cell('''
# ETS Table 1A（2022-07 至 2025-06）里列出的点；两点之间用直线插值，所以中间值只是近似
V = {135: 3, 140: 10, 145: 21, 150: 39, 155: 64, 157: 72, 160: 82, 162: 88, 165: 95, 168: 98, 170: 99}
Q = {135: 1, 140: 5, 145: 12, 150: 23, 155: 37, 157: 42, 160: 50, 162: 57, 165: 67, 168: 80, 170: 89}

def pct(table, s):
    pts = sorted(table.items())
    if s <= pts[0][0]: return pts[0][1]
    if s >= pts[-1][0]: return pts[-1][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= s <= x1:
            return y0 + (y1 - y0) * (s - x0) / (x1 - x0)

# 把下面的数字改成你自己模考的分数；现在是「示例数字」，不是你的成绩
mine   = {"V": 152, "Q": 162}
target = {"V": 155, "Q": 165}

for sec, table in (("V", V), ("Q", Q)):
    p_now, p_goal = pct(table, mine[sec]), pct(table, target[sec])
    print(f"{sec}: 现在 {mine[sec]}（约第 {p_now:.0f} 百分位）→ 目标 {target[sec]}（约第 {p_goal:.0f} 百分位），差 {target[sec] - mine[sec]} 分")
print("总分：", sum(mine.values()), "→", sum(target.values()))
''')
