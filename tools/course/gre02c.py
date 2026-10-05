from runlib import Notebook

nb = Notebook()

C_ARITH = nb.cell('''
# 1. 倍数计数（容斥）：1 到 99 里，能被 3 或 5 整除的整数有多少个？
a = 99 // 3                        # 3 的倍数
b = 99 // 5                        # 5 的倍数
c = 99 // 15                       # 同时是 3 和 5 的倍数（15 的倍数），被数了两次
print("公式：", a + b - c)
print("暴力枚举：", sum(1 for n in range(1, 100) if n % 3 == 0 or n % 5 == 0))

# 2. 百分数：先涨 20% 再跌 20%，相对原价变化多少？
print("最终价格是原价的", round(1.2 * 0.8, 2), "倍")

# 3. 平均速度：去程 60 km/h、回程 40 km/h，路程相同。平均速度不是 50
d = 120                            # 任取一个路程，答案与它无关
t = d / 60 + d / 40
print("平均速度：", round(2 * d / t, 2), "km/h")
''')

C_ALG = nb.cell('''
# 方程组：2x + 3y = 12，x - y = 1。用代入消元法
# 由第二式 x = y + 1，代入第一式：2(y+1) + 3y = 12  =>  5y = 10
y = (12 - 2) / 5
x = y + 1
print("x =", x, " y =", y)
print("检验：", 2 * x + 3 * y == 12, x - y == 1)

# 一元二次方程 x^2 - 5x + 6 = 0：求根公式
import math
a, b, c = 1, -5, 6
disc = b * b - 4 * a * c
r1 = (-b + math.sqrt(disc)) / (2 * a)
r2 = (-b - math.sqrt(disc)) / (2 * a)
print("判别式：", disc, " 两个根：", r1, r2)
''')
