from runlib import Notebook

nb = Notebook()

C_PLAN = nb.cell('''
# 30 分钟的一个作文任务：本课程建议的分配（不是 ETS 的要求）
plan = [("审题与立场", 3), ("列提纲：理由与例子", 4), ("写作", 20), ("通读与改错（没有拼写检查）", 3)]
print("总计：", sum(m for _, m in plan), "分钟")
for name, m in plan:
    print(f"  {name:<14s} {m:>2d} 分钟")

# 写 450 个词需要的速度（450 只是示例，官方页面没有给出字数要求）
words = 450
for typing_minutes in (20, 18, 15):
    print(f"{words} 词用 {typing_minutes} 分钟写完：每分钟 {words / typing_minutes:.0f} 词")
''')

C_PCT = nb.cell('''
# ETS Table 1A（2022-07 至 2025-06）Analytical Writing 的百分位
aw = {6.0: 99, 5.0: 93, 4.0: 63, 3.5: 40, 3.0: 16}
for score, p in aw.items():
    print(f"AW {score}  ->  第 {p} 百分位")
print("均值 3.46，标准差 0.85；NUS MComp 页面曾列出 AW 3.5 的要求，对应第", aw[3.5], "百分位")
''')
