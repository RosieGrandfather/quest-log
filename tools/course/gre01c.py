from runlib import Notebook

nb = Notebook()

C_TIME = nb.cell('''
# ETS 官方：每个科目的两个小节（题数, 分钟）
sections = {
    "Verbal":       [(12, 18), (15, 23)],
    "Quantitative": [(12, 21), (15, 26)],
}
total = 30                                          # 作文 1 题，30 分钟
for name, parts in sections.items():
    n = sum(p[0] for p in parts)
    m = sum(p[1] for p in parts)
    total += m
    print(f"{name:13s} {n} 题 {m} 分钟 平均每题 {m / n:.2f} 分钟")
print("三个科目合计（不含休息、不含可能出现的不计分小节）：", total, "分钟")
''')

C_PCT = nb.cell('''
# ETS Table 1A（2022-07-01 至 2025-06-30）里的百分位：分数 -> 低于该分数的考生占比（%）
V = {170: 99, 168: 98, 165: 95, 162: 88, 160: 82, 157: 72, 155: 64, 150: 39, 145: 21, 140: 10, 135: 3}
Q = {170: 89, 168: 80, 165: 67, 162: 57, 160: 50, 157: 42, 155: 37, 150: 23, 145: 12, 140: 5, 135: 1}

combos = [(155, 165), (160, 160), (150, 170), (165, 155), (170, 150)]
for v, q in combos:
    pv = V.get(v, "—")
    pq = Q.get(q, "—")
    print(f"V{v} + Q{q} = {v + q}   Verbal 百分位 {pv}   Quant 百分位 {pq}")

# 同样是 +10 分，在两个科目上的「含金量」差多少？
print("Verbal 160 -> 170：百分位", V[160], "->", V[170], "，增加", V[170] - V[160])
print("Quant  160 -> 170：百分位", Q[160], "->", Q[170], "，增加", Q[170] - Q[160])
''')
