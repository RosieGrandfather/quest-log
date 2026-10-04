from runlib import Notebook

nb = Notebook()

def synerr(src):
    """语法错误的整块代码根本不会运行，网页里也没法放「运行」按钮：用 ```text 展示，报错信息是真的编译出来的。"""
    import textwrap
    src = textwrap.dedent(src).strip('\n')
    try:
        compile(src, '<cell>', 'exec')
    except SyntaxError as e:
        return '```text\n' + src + '\n\n# Python 报错：' + type(e).__name__ + ': ' + e.msg + '\n```'
    raise SystemExit('这段代码本应有语法错误：' + src)


# ───── 一、语句、表达式、print、注释、缩进 ─────
C_HELLO = nb.cell('''
print("Hello, 仓库")            # 调用 print：把括号里的东西显示出来
print(7 * 6)                   # 括号里可以是一个要先算的式子
print("箱数：", 7, "每箱", 6)   # 多个东西用逗号隔开，显示时中间自动加一个空格
''')

C_ECHO = nb.cell('''
print("OMRON Healthcare")      # print 显示的是内容本身
"OMRON Healthcare"             # 最后一行的值：网页会替你显示，带引号 = 这是字符串
''')

C_COMMENT = nb.cell('''
# 这一行是注释：Python 完全忽略它，写给人看的
print(12.5 * 4)    # 行尾也能写注释：单价 × 数量
# print(999)       # 在一行前面加 # ，这行就「暂时不运行」了
''')

C_INDENT = synerr('''
print("第一行")
    print("第二行")    # 这一行凭空多了 4 个空格
''')

# ───── 二、变量 ─────
C_ASSIGN = nb.cell('''
qty = 24          # 把名字 qty 贴到整数 24 上
print(qty)
qty = 30          # 把标签撕下来，贴到另一个值 30 上
print(qty)
qty = qty + 6     # 先算右边 30 + 6，再把 qty 贴到结果 36 上
print(qty)
''')

C_ALIAS = nb.cell('''
a = 5
b = a          # b 贴到「a 此刻指着的值」5 上，不是「b 永远等于 a」
a = 10         # 只把 a 挪走了，b 不受影响
print(a, b)
''')

C_AUG = nb.cell('''
stock = 100
stock += 20       # 等价于 stock = stock + 20
stock -= 5        # 等价于 stock = stock - 5
stock *= 2        # 等价于 stock = stock * 2
print(stock)
''')

C_NAMEERR = nb.cell('''
print(price_per_box)      # 这个名字还没有被赋过值
''', err=True)

C_DEFINE = nb.cell('''
price_per_box = 18.5      # 第一次赋值，名字才算「定义」了
print(price_per_box * 4)
''')

C_MULTI = nb.cell('''
lo, hi = 3, 9        # 左边两个变量 lo 和 hi，右边两个值，按位置一一对应
print(lo)
print(hi)
''')

C_SWAP = nb.cell('''
lo, hi = hi, lo      # 右边先整体算好 (9, 3)，再按位置贴回去：交换
print(lo, hi)
''')

C_TUPLE = nb.cell('''
pair = 24, 6                 # 右边用逗号隔开的一串，本身就是一个整体
print(pair, type(pair))
box_qty, per_box = pair      # 再按位置拆给两个变量
print(box_qty, per_box)
''')

C_UNPACKERR = nb.cell('''
a, b = 1, 2, 3     # 左边 2 个名字，右边 3 个值：对不上
''', err=True)

# ───── 三、命名规则 ─────
C_NAMES_OK = nb.cell('''
total_qty = 120        # 约定的写法：小写字母 + 下划线（snake_case）
Total_qty = 7          # 合法，但和上一行是两个不同的名字（区分大小写）
box2 = 5               # 数字可以出现在中间或末尾
_tmp = 0               # 下划线可以开头
数量 = 8               # 汉字也是「字母」，合法（但不建议用）
print(total_qty, Total_qty, box2, _tmp, 数量)
''')

C_BADSPACE = synerr('''
my qty = 3         # 名字里有空格
''')

C_BADDIGIT = synerr('''
2nd_box = 5        # 以数字开头
''')

C_BADKW = synerr('''
class = 1          # class 是 Python 的关键字
''')

C_KEYWORDS = nb.cell('''
import keyword                 # 先照抄：把标准库里的「keyword 工具箱」拿来用
print(keyword.kwlist)          # 全部关键字（方括号里的一串值叫列表，「容器」那一节讲）
''')

C_SHADOW = nb.cell('''
print(max(3, 9))      # 内置函数 max：取最大值
max = 5               # 合法！但 max 这个名字现在贴到了整数 5 上
print(max)
del max               # del：把名字撕掉，内置的 max 又回来了
print(max(3, 9))
''')

# ───── 四、类型 ─────
C_TYPES = nb.cell('''
print(type(24))
print(type(3.5))
print(type("box"))
print(type(True))
print(type(None))
''')

C_NUMBERS = nb.cell('''
print(2 ** 100)            # int 没有大小上限
print(1_000_000)           # 数字里可以用下划线分组，方便人读，值不变
print(3.0, 1e3, 2.5e-3)    # float：带小数点，或科学计数法（1e3 就是 1×10³）
print(type(3.0), type(3))  # 3.0 和 3 是不同的类型
''')

C_VARTYPE = nb.cell('''
x = 5
print(type(x))
x = "five"
print(type(x))     # 同一个名字，后来贴到了另一种类型的值上
''')

C_ISINST = nb.cell('''
print(isinstance(24, int), isinstance(24, float))
print(isinstance(24, (int, float)))    # 第二个参数写成 (类型, 类型)：是其中任何一种吗
print(isinstance(True, int))           # bool 其实算 int 的一种
print(True + True)
''')

C_TRUTHY = nb.cell('''
print(bool(0), bool(0.0), bool(""), bool(None))     # 这四个是「假」
print(bool(1), bool(-3), bool("0"), bool("a"))      # 其余基本都是「真」
''')

# ───── 五、运算符 ─────
C_ARITH = nb.cell('''
a, b = 17, 5
print(a + b, a - b, a * b)
print(a / b)       # 真除法：结果永远是 float
print(a // b)      # 整除：只要商的整数部分
print(a % b)       # 取余：除完剩下的
print(a ** 2)      # 乘方：17 的平方
print(10 / 2)      # 注意：能整除时，/ 的结果也是 float
''')

C_BOXES = nb.cell('''
qty, per_box = 110, 24
print(qty // per_box, qty % per_box)       # 整箱数、零散数
boxes, leftover = divmod(qty, per_box)     # divmod 一次给出 (商, 余数)，正好拆给两个变量
print(boxes, leftover)
print(-7 // 2, -7 % 2)                     # 负数：// 向「更小」的方向取整
''')

C_PREC = nb.cell('''
print(2 + 3 * 4, (2 + 3) * 4)    # 先乘除后加减，括号优先
print(2 ** 3 ** 2)               # ** 从右往左算：2 ** (3 ** 2)
print(-3 ** 2)                   # 先乘方、再取负
''')

C_CMP = nb.cell('''
x = 5                  # 一个 =：赋值，把 x 贴到 5 上
print(x == 5)          # 两个 =：比较，x 等于 5 吗？结果是 bool
print(x != 5, x < 3, x >= 5)
print(1 < x < 10)      # 连着比：1 < x 并且 x < 10
print(3 == 3.0, "a" == "A", "3" == 3)
''')

C_LOGIC = nb.cell('''
stock, on_hold = 120, False
print(stock > 100 and not on_hold)    # 库存充足 并且 没有被冻结
print(stock < 50 or on_hold)          # 库存不足 或者 被冻结
print(not True)
''')

C_NONE = nb.cell('''
result = None
print(result is None, result is not None)
print(result == 0, result == "")      # None 不等于 0，也不等于空字符串
''')

C_FLOAT = nb.cell('''
print(0.1 + 0.2)
print(0.1 + 0.2 == 0.3)
print(abs((0.1 + 0.2) - 0.3) < 1e-9)    # 比较小数：看「差」是否小到可以忽略
print(round(0.1 + 0.2, 2) == 0.3)       # 或者先四舍五入再比
print(0.5 + 0.25)                       # 0.5、0.25 恰好能精确表示
''')

C_CENTS = nb.cell('''
price_cents = 1999                 # 金额用整数（分）来算，不会有误差
total_cents = price_cents * 3
print(total_cents, total_cents / 100)
print(0.1 * 3)                     # 小数直接乘，又出现了误差
''')

# ───── 六、类型转换与报错 ─────
C_CONVERT = nb.cell('''
print(int("42") + 1)          # 字符串 → 整数
print(int(3.9), int(-3.9))    # 小数 → 整数：直接砍掉小数部分，不是四舍五入
print(float("3.5") * 2)
print(str(24) + " pcs")       # 整数 → 字符串
print(bool("False"))          # 非空字符串都是真，哪怕内容写着 False
''')

C_STRARITH = nb.cell('''
print("5" + "3")      # 字符串相加：拼接
print("5" * 3)        # 字符串乘整数：重复
print(5 + 3)          # 整数相加：算术
print("-" * 20)       # 画分隔线
''')

C_TYPEERR = nb.cell('''
print("箱数：" + qty)       # 字符串 + 整数，Python 不会替你猜
''', err=True)

C_VALERR = nb.cell('''
print(int("abc"))           # 类型对（字符串可以交给 int），内容不行
''', err=True)

C_VALERR2 = nb.cell('''
print(int("3.5"))           # "3.5" 不是整数的写法
''', err=True)

C_FIXCONV = nb.cell('''
print(int(float("3.5")))    # 先转 float，再转 int
''')

# ───── 七、字符串 ─────
C_QUOTES = nb.cell('''
a = 'single'
b = "double"
print(a, b, a == 'single')    # 单引号双引号完全等价
c = "It's fine"               # 内容里有单引号，就用双引号包起来
d = 'say "hi"'
print(c, d)
''')

C_ESCAPE = nb.cell('''
print("line1\\nline2")       # \\n：换行
print("a\\tb")               # \\t：制表符（Tab）
print("C:\\\\data")          # \\\\：一个真正的反斜杠
print("""多行字符串
可以直接换行""")           # 三个引号：里面可以直接换行
''')

C_INDEX = nb.cell('''
sku = "OMRON-0042"
print(sku[0], sku[1], sku[-1], sku[-2])    # 下标从 0 开始；负数从末尾倒着数
print(len(sku))                            # len：字符个数
''')

C_SLICE = nb.cell('''
print(sku[0:5])       # 下标 0,1,2,3,4：含头不含尾
print(sku[:5])        # 省略开头 = 从头开始
print(sku[6:])        # 省略结尾 = 一直到最后
print(sku[-4:])       # 最后 4 个字符
print(sku[::2])       # 步长 2：隔一个取一个
print(sku[::-1])      # 步长 -1：倒过来
print(sku[3:99])      # 切片越界不报错，取到哪算哪
''')

C_INDEXERR = nb.cell('''
print(sku[99])        # 单个下标越界，会报错
''', err=True)

C_IMMUT = nb.cell('''
sku[0] = "X"          # 想直接改第 0 个字符
''', err=True)

C_NEWSTR = nb.cell('''
new_sku = "X" + sku[1:]     # 用切片拼出一个新字符串
print(new_sku, sku)         # 原来的 sku 没有变
sku = "OMRON-0043"          # 想「改」，就是把名字贴到新字符串上
print(sku)
''')

C_LENIN = nb.cell('''
print(len("OMRON"), len(""), len("仓库"))
print("RON" in sku, "ron" in sku, "XYZ" not in sku)    # in：是不是它的一部分
''')

# ───── 八、点号与方法 ─────
C_METHOD1 = nb.cell('''
name = "  omron healthcare  "
print(name.upper())
print(name.strip())               # strip：去掉两头的空白
print(name)                       # 原字符串没变（字符串不可变）
clean = name.strip().upper()      # 方法可以连着用，从左往右一步步算
print(clean)
print("SG-DC".lower())
''')

C_STRUPPER = nb.cell('''
print("abc".upper())
print(str.upper("abc"))      # 同一件事的完整写法：类型名.方法名(对象)
''')

C_ATTRERR = nb.cell('''
n = 5
print(n.upper())      # 整数没有 upper 方法
''', err=True)

C_DIR = nb.cell('''
print(dir("abc")[-10:])      # 字符串类型的方法名，最后 10 个（按字母排序）
print(dir(dict)[-11:])       # dict 是字典类型的名字（「容器」那一节讲），它的方法里有 get
''')

C_HELP = nb.cell('''
help(str.strip)
''')

C_STRMETH = nb.cell('''
print("sg-dc-01".replace("-", "_"))                       # 把每个 "-" 换成 "_"
print("sg-dc-01".startswith("sg"), "sg-dc-01".endswith("02"))
print("sg-dc-01".find("dc"), "sg-dc-01".find("xx"))       # 找到返回位置；找不到返回 -1
print("sg-dc-01".count("-"))                              # 数出现几次
''')

C_SPLITJOIN = nb.cell('''
line = "SKU-001,24,Singapore"
parts = line.split(",")          # 按逗号切开，得到一串字符串（列表，「容器」那一节细讲）
print(parts)
print(" | ".join(parts))         # join：用左边这个字符串，把它们连起来
print("a  b   c".split())        # 不给参数：按任意空白切，多余空格自动忽略
''')

C_FORGET = nb.cell('''
title = " hello "
title.strip()              # 算出了新字符串，但没有人接住它
print(repr(title))         # repr：连引号一起显示，能看出空格还在
title = title.strip()      # 想保留结果，要把它赋值回去
print(repr(title))
''')

# ───── 九、f-string ─────
C_FSTR1 = nb.cell('''
name, qty, price = "BP monitor", 24, 18.5
print(f"{name}: {qty} pcs")
print(f"总价 = {qty * price}")       # 大括号里可以是任何表达式
print(f"{name.upper()[:2]}")         # 可以调用方法、切片
print(f"{qty=}")                      # 调试好用：同时显示名字和值
print(f"{{qty}} 双大括号显示成一个字面的大括号")
''')

C_FSTR2 = nb.cell('''
price, qty = 1234.5, 7
print(f"{price:.2f}")        # 冒号后面是格式：保留 2 位小数
print(f"{price:,.2f}")       # 加千分位逗号
print(f"{1234567:,}")
print(f"[{qty:>6}]")         # 右对齐，总宽 6
print(f"[{qty:<6}]")         # 左对齐
print(f"[{qty:^6}]")         # 居中
print(f"{qty:03d}")          # 整数，补零到 3 位
print(f"{0.075:.1%}")        # 百分数，1 位小数
''')

C_TABLE = nb.cell('''
print(f"{'item':<10}{'qty':>5}{'price':>10}")
print(f"{'Monitor':<10}{24:>5}{18.5:>10.2f}")
print(f"{'Cuff':<10}{150:>5}{3.2:>10.2f}")
''')

# ───── 十、内置函数与 eval ─────
C_BUILTIN1 = nb.cell('''
print(abs(-7), abs(-2.5))
print(round(3.14159, 2), round(2.5), round(3.5))    # round(2.5) 是 2，不是 3
print(min(3, 9, 5), max(3, 9, 5))
print(pow(2, 10), 2 ** 10)
print(type(len))
''')

C_BUILTIN2 = nb.cell('''
print(list(range(5)))                 # range(5)：0,1,2,3,4；list 把它们摆成一串
print(list(range(2, 10, 3)))          # range(起点, 终点, 步长)，同样含头不含尾
print(sum(range(1, 101)))             # 1 + 2 + ... + 100
print(sorted("banana"))               # 排序，返回列表
print(sorted("banana", reverse=True)) # name=value 的参数：关键字参数
''')

C_BUILTINS_CHECK = nb.cell('''
import builtins
print("max" in dir(builtins), "TypeError" in dir(builtins), "upper" in dir(builtins))
''')

C_EVAL = nb.cell('''
print(eval("2 + 3 * 4"))          # eval：把字符串当成 Python 表达式去算
price = 18.5
print(eval("price * 2"))          # 它能看到当前的变量
print(eval("len('abc') + 1"))
''')

C_EVALERR = nb.cell('''
print(eval("1 + 'a'"))            # 字符串里的代码，一样会报错
''', err=True)

# ───── 十一、读一行代码 ─────
C_READLINE = nb.cell('''
sku, qty, rate = "omron-hem", 8, "0.075"
label = f"{sku.upper()}-{qty:05d}"
tax = round(qty * float(rate), 2)
print(label, tax)
''')
