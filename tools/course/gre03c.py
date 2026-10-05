from runlib import Notebook

nb = Notebook()

C_GEO = nb.cell('''
import math
# 勾股定理：直角三角形两条直角边 6 和 8，斜边是多少？面积是多少？
print("斜边：", math.hypot(6, 8), " 面积：", 6 * 8 / 2)

# 圆：周长 C = 10π，求面积。由 C = 2πr 得 r = 5，面积 = πr^2
r = 10 * math.pi / (2 * math.pi)
print("半径：", r, " 面积 / π =", r ** 2)
''')

C_DATA = nb.cell('''
from math import comb
from statistics import mean, median

data = [3, 5, 5, 7, 10]
print("均值", mean(data), " 中位数", median(data))
print("加入一个极端值 100 后：均值", round(mean(data + [100]), 2), " 中位数", median(data + [100]))

# 概率：掷两颗骰子，点数和为 7 的概率
hits = sum(1 for a in range(1, 7) for b in range(1, 7) if a + b == 7)
print("点数和为 7：", hits, "/ 36 =", round(hits / 36, 4))

# 组合：6 个人里选 2 人组成委员会（顺序无关）
print("C(6,2) =", comb(6, 2))
# 排列：3 位数，各位数字互不相同，百位不能是 0
print("三位数各位互不相同：", 9 * 9 * 8)
''')

C_QC = nb.cell('''
# 数量比较：已知 x > 0，比较 A = x^2 与 B = x。用代入法试几个有代表性的值
def relation(a, b):
    return "A>B" if a > b else ("A<B" if a < b else "A=B")

for x in [0.5, 1, 2, 10]:
    print(f"x = {x:>4}:  A = {x**2:<6} B = {x:<4} ->", relation(x**2, x))
print("结论：关系取决于 x，选「无法确定」")

# 再看第二题：已知 x > 1，比较 A = x^2 与 B = x
print([relation(x**2, x) for x in [1.1, 2, 10]])
print("结论：关系始终是 A>B，选「A 大」")
''')
