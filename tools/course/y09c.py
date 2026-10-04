from runlib import Notebook
import os, subprocess, sys, tempfile, textwrap

nb = Notebook()


def shown(src):
    """把一段会报语法错误的代码写进文件真实运行，返回 ```text 块（源码 + 真实的错误信息）。
    语法错误发生在「读代码」阶段，整块代码都不会开始运行，所以不能放进网页里的运行块。"""
    src = textwrap.dedent(src).strip('\n')
    d = tempfile.mkdtemp()
    with open(os.path.join(d, 'demo.py'), 'w', encoding='utf-8') as f:
        f.write(src + '\n')
    r = subprocess.run([sys.executable, 'demo.py'], cwd=d, capture_output=True, text=True, timeout=60)
    if not r.stderr.strip():
        raise SystemExit('这段代码应该报错：\n' + src)
    import re
    err = re.sub(r'"[^"]*demo\.py"', '"demo.py"', r.stderr.strip())
    return '```text\n# demo.py\n' + src + '\n```\n\n运行 `python demo.py` 得到：\n\n```text\n' + err + '\n```'


# ───── 缩进是语法、if / elif / else ─────
C_IF_BASIC = nb.cell('''
stock = 12            # 仓库里还有 12 箱
need = 20             # 订单要 20 箱

if stock >= need:
    print("可以全部发货")
else:
    print("库存不够")
    print("缺", need - stock, "箱")
print("这一行没有缩进，属于 if 之外，永远会执行")
''')

C_IF_NOELSE = nb.cell('''
qty = 0
if qty > 0:
    print("发货")
    print("这一行也缩进了，也只在 qty > 0 时执行")
print("无论如何都会打印")
''')

C_IFELIF = nb.cell('''
stock = 35
if stock == 0:
    status = "缺货"
elif stock < 20:
    status = "低库存"
elif stock < 100:
    status = "正常"
else:
    status = "充足"
print(stock, "->", status)
''')

C_IFORDER = nb.cell('''
qty = 500
if qty >= 1:
    size = "小单"
elif qty >= 100:
    size = "大单"        # 永远走不到：500 在上一条就已经匹配了
print(qty, "->", size)
''')

C_COMPARE = nb.cell('''
qty = 12
print(qty == 12, qty != 12, qty > 10, qty <= 10)
print("ab" in "cabd", 3 in [1, 2, 3], "SKU-A" in {"SKU-A": 120})   # in：是否包含；对字典查的是键
print("SKU-Z" not in {"SKU-A": 120})
print(0 < qty <= 100)           # 比较链：0 < qty 并且 qty <= 100
print(0 < qty and qty <= 100)   # 和上一行等价
''')

C_OR_PITFALL = nb.cell('''
qty = 7
print(qty == 1 or 2)                  # 看起来像「qty 是 1 或 2」，实际结果是 2
print(bool(qty == 1 or 2))            # 当条件用，永远为真
print(qty == 1 or qty == 2, qty in (1, 2))    # 正确写法：两种都行
''')

C_TRUTHY = nb.cell('''
print("当作假：", bool(0), bool(0.0), bool(""), bool([]), bool({}), bool(None))
print("当作真：", bool(-1), bool("0"), bool(" "), bool([0]), bool("False"))
''')

C_TRUTHY_USE = nb.cell('''
orders = []
if orders:                       # 等价于 if len(orders) > 0:
    print("有订单要处理")
else:
    print("今天没有订单")

result = None
print(result is None, result == None)   # 判断是不是 None，习惯写 is None
''')

C_ANDOR = nb.cell('''
print(0 or 5, "" or "默认", "A" or "B")     # or：返回第一个为真的；全是假就返回最后一个
print(3 and 7, 0 and 7, [] and 7)           # and：返回第一个为假的；全是真就返回最后一个
print(not 0, not [1])
name = ""
print("名字：" + (name or "未填写"))          # 常见用法：给空值一个默认
''')

C_SHORT = nb.cell('''
items = []
if len(items) > 0 and items[0] > 5:      # 左边已经是 False，右边根本不会被执行
    print("第一个超过 5")
else:
    print("跳过，没有报错")
print(True or print("我不会被打印"))        # or：左边为真，右边整个跳过
''')

C_SHORT_ERR = nb.cell('''
items = []
if items[0] > 5 and len(items) > 0:      # 顺序反了：先执行 items[0]
    print("不会到这里")
''', err=True)

C_PREC = nb.cell('''
a, b, c = True, False, False
print(a or b and c)         # and 比 or 先算，等价于 a or (b and c)
print((a or b) and c)       # 括号改变计算顺序
''')

C_CONDEXPR = nb.cell('''
stock = 0
label = "有货" if stock > 0 else "缺货"     # 条件表达式：一行里二选一，值是 if 前面或 else 后面的那个
print(label)
''')

# ───── for 循环 ─────
C_FOR1 = nb.cell('''
orders = [12, 0, 35, 8]          # 四个订单的箱数
for qty in orders:
    print("qty 现在是", qty)
print("循环结束后 qty 还是", qty)   # 变量不会消失，停在最后一个值
''')

C_FOR_STR = nb.cell('''
for ch in "SKU-42":              # 字符串：一次一个字符
    print(ch, end="|")
print()
for sku in ("SKU-A", "SKU-B"):   # 元组也一样
    print(sku)
''')

C_RANGE = nb.cell('''
print(range(5))                  # range 对象只是「一个范围」的描述，本身不是列表
print(list(range(5)))            # range(stop)：从 0 数到 stop 的前一个
print(list(range(2, 6)))         # range(start, stop)
print(list(range(0, 10, 3)))     # range(start, stop, step)
print(list(range(5, 0, -1)))     # step 是负数就倒着数
print(len(range(2, 6)), list(range(3, 3)))   # 长度是 stop - start；start 等于 stop 时是空的
''')

C_RANGE_USE = nb.cell('''
for i in range(3):
    print("第", i + 1, "次盘点")
''')

C_ENUM = nb.cell('''
orders = [12, 0, 35, 8]
for i in range(len(orders)):                  # 能用，但绕：先造下标，再用下标取值
    print(i, orders[i])
for i, qty in enumerate(orders, start=1):     # 更直接：每轮同时拿到序号和值
    print("订单", i, ":", qty, "箱")
print(list(enumerate(["a", "b"], start=1)))   # enumerate 每轮给一对 (序号, 元素)
''')

C_DICT_ITER = nb.cell('''
stock = {"SKU-A": 120, "SKU-B": 0, "SKU-C": 35}
for sku in stock:                      # 直接遍历字典：只拿到键
    print(sku)
for sku, qty in stock.items():         # .items() 每轮给一对 (键, 值)，用解包拆开
    print(sku, "还有", qty, "箱")
print(list(stock.values()))            # 只要值
''')

C_ZIP = nb.cell('''
skus = ["SKU-A", "SKU-B", "SKU-C"]
qtys = [120, 0, 35]
for sku, qty in zip(skus, qtys):       # zip：把两个序列「拉链」式配对
    print(sku, qty)
print(list(zip([1, 2, 3], "ab")))      # 遇到最短的就停
''')

C_CONTINUE = nb.cell('''
orders = [12, 0, 35, 8]
for qty in orders:
    if qty == 0:
        continue                  # 跳过这一轮剩下的代码，直接进入下一轮
    print("处理", qty, "箱")
''')

C_BREAK = nb.cell('''
for qty in orders:
    if qty > 30:
        print("找到第一个超过 30 箱的订单：", qty)
        break                     # 整个循环到此结束
    print("检查过", qty)
print("循环之后")
''')

C_FORELSE = nb.cell('''
for qty in orders:
    if qty > 100:
        print("有大订单")
        break
else:                             # 循环「没有被 break 打断」才会执行
    print("没有任何订单超过 100 箱")
''')

C_MODIFY = nb.cell('''
nums = [1, 2, 2, 3]
for n in nums:
    if n == 2:
        nums.remove(n)            # 一边遍历一边删
print(nums)                       # 想删掉所有 2，结果还剩一个

nums = [1, 2, 2, 3]
kept = []                         # 正确做法：造一个新列表，只放要留下的
for n in nums:
    if n != 2:
        kept.append(n)
print(kept)
''')

C_NESTED = nb.cell('''
shipments = [[2, 3], [5], []]       # 三张发货单，每张里是各箱的件数
for i, boxes in enumerate(shipments, start=1):
    total = 0
    for pieces in boxes:            # 内层循环：外层每来一轮，内层从头跑一遍
        total += pieces             # total += x 就是 total = total + x
    print("发货单", i, "共", total, "件")
''')

# ───── while ─────
C_WHILE1 = nb.cell('''
stock = 100
while stock > 30:                    # 条件为真就继续；每一轮开头都重新检查
    stock = stock - 40
    print("发走 40 箱，剩", stock)
print("停止：stock 已经不大于 30")
''')

C_WHILE_BREAK = nb.cell('''
attempts = 0
while True:                          # 看起来永远为真，靠 break 退出
    attempts += 1
    if attempts ** 2 >= 50:
        break
print("第", attempts, "次尝试后停止")
''')

C_WHILE_SAFE = nb.cell('''
tries = 0
stock = 5
while stock < 20 and tries < 10:     # 加一道保险：最多 10 轮，万一逻辑写错也不会无限转
    stock += 3
    tries += 1
print(stock, tries)
''')

TEXT_INFINITE = '''```text
n = 10
while n > 0:
    print(n)
    n = n + 1        # 写反了：n 越来越大，n > 0 永远为真，永远不停
```'''

# ───── 常见循环模式 ─────
C_PAT_DATA = nb.cell('''
orders = [
    {"id": "A101", "qty": 12, "status": "shipped"},
    {"id": "A102", "qty": 0, "status": "cancelled"},
    {"id": "A103", "qty": 35, "status": "shipped"},
    {"id": "A104", "qty": 8, "status": "pending"},
    {"id": "A105", "qty": 20, "status": "pending"},
]
print(len(orders), orders[0]["id"], orders[0]["qty"])
''')

C_PAT_SUM = nb.cell('''
total = 0                          # 累加器：先放一个「空值」0
for order in orders:
    total += order["qty"]
print("总箱数", total)
print("平均每单", total / len(orders))
''')

C_PAT_RESET = nb.cell('''
for order in orders:
    total = 0                      # 错：每一轮都把累加器清零
    total += order["qty"]
print(total)
''')

C_PAT_COUNT = nb.cell('''
pending = 0
for order in orders:
    if order["status"] == "pending":
        pending += 1
print("待处理订单数", pending)
''')

C_PAT_FILTER = nb.cell('''
big = []                           # 先造一个空盒子
for order in orders:
    if order["qty"] >= 10:
        big.append(order["id"])
print(big)
''')

C_PAT_MAX = nb.cell('''
best = orders[0]                   # 先假设第一个最大
for order in orders[1:]:           # 从第二个开始比
    if order["qty"] > best["qty"]:
        best = order
print(best["id"], best["qty"])
''')

C_PAT_COUNTDICT = nb.cell('''
by_status = {}
for order in orders:
    s = order["status"]
    by_status[s] = by_status.get(s, 0) + 1     # 没见过的状态按 0 算，再加 1
print(by_status)
''')

C_PAT_GROUP = nb.cell('''
ids_by_status = {}
for order in orders:
    ids_by_status.setdefault(order["status"], []).append(order["id"])   # 没有这个键就先放一个空列表
print(ids_by_status)
''')

# ───── 读报错 ─────
C_ERR_ZERO = nb.cell('''
total = 75
count = 0
average = total / count
print(average)
''', err=True)

C_TRACE_CHAIN = nb.cell('''
def load_qty(text):
    return int(text)

def read_order(row):
    sku, text = row
    return sku, load_qty(text)

print(read_order(("SKU-A", "12")))
print(read_order(("SKU-B", "12箱")))
''', err=True)

SYNTAX_COLON = shown('''
qty = 12
if qty > 10
    print("大单")
''')

SYNTAX_PAREN = shown('''
print("总数：", (3 + 4)
print("下一行")
''')

INDENT_EXPECT = shown('''
qty = 12
if qty > 10:
print("大单")
''')

INDENT_UNMATCH = shown('''
qty = 12
if qty > 10:
        print("大单")
    print("要发货")
''')

C_E_NAME = nb.cell('''
stock = 12
print(stok)                  # 拼错了
''', err=True)

C_E_TYPE = nb.cell('''
qty = 12
print("箱数：" + qty)
''', err=True)

C_E_VALUE = nb.cell('''
qty = int("12箱")
''', err=True)

C_E_UNPACK = nb.cell('''
sku, qty = ["SKU-A", 12, "pending"]
''', err=True)

C_E_KEY = nb.cell('''
stock = {"SKU-A": 120, "SKU-C": 35}
print(stock["SKU-B"])
''', err=True)

C_E_INDEX = nb.cell('''
orders = [12, 0, 35, 8]
print(orders[4])
''', err=True)

C_E_ATTR = nb.cell('''
nums = [3, 1, 2]
result = nums.sort()         # sort 是原地排序，返回值是 None
print(result)
result.append(9)
''', err=True)

C_E_ATTR2 = nb.cell('''
"SKU".append("-A")           # 字符串没有 append：append 属于列表
''', err=True)

C_FIXES = nb.cell('''
stock = {"SKU-A": 120, "SKU-C": 35}
qty = 12
print("箱数：" + str(qty))                        # TypeError：把数字转成字符串（或 print("箱数：", qty)）
print(int("12"), int("12箱".replace("箱", "")))    # ValueError：先清洗，再转换
print(stock.get("SKU-B", 0))                      # KeyError：用 get 给一个默认值
sku, qty, status = ["SKU-A", 12, "pending"]       # 解包：左边的个数要和右边一致
orders = [12, 0, 35, 8]
print(orders[len(orders) - 1], orders[-1])        # IndexError：最大下标是 len - 1
nums = [3, 1, 2]
nums.sort()                                       # 原地排序，不要接收它的返回值
print(nums, sorted([3, 1, 2]))                    # 想要「排好序的新列表」用 sorted
total, count = 75, 0
print(total / count if count else 0)              # ZeroDivisionError：先判断
''')

# ───── try / except ─────
C_TRY1 = nb.cell('''
text = "12箱"
try:
    qty = int(text)
    print("转换成功：", qty)
except ValueError:
    qty = 0
    print("不是纯数字，按 0 处理")
print("程序继续往下走，qty =", qty)
''')

C_TRY_FLOW = nb.cell('''
try:
    print("1. 开始")
    x = 1 / 0
    print("2. 这一行不会执行")
except ZeroDivisionError:
    print("3. 进入 except")
print("4. 回到正常流程")
''')

C_TRY_AS = nb.cell('''
try:
    int("abc")
except ValueError as e:
    print(type(e).__name__)
    print(e)
    print(repr(e))
''')

C_TRY_MULTI = nb.cell('''
for raw in ["12", "abc", "0", None]:
    try:
        per_box = 100 // int(raw)
        print(repr(raw), "->", per_box)
    except ValueError:
        print(repr(raw), "-> 不是整数")
    except ZeroDivisionError:
        print(repr(raw), "-> 不能为 0")
    except TypeError:
        print(repr(raw), "-> 类型不对")
''')

C_TRY_TUPLE = nb.cell('''
for raw in ["abc", None, "5"]:
    try:
        print(100 // int(raw))
    except (ValueError, TypeError) as e:       # 圆括号里是一个元组：这几种错误一起处理
        print("输入有问题：", type(e).__name__)
''')

C_MRO = nb.cell('''
for cls in (KeyError, ZeroDivisionError, ValueError):
    names = []
    for c in cls.__mro__:                      # __mro__：这个类的「家谱」，从自己一路往上
        names.append(c.__name__)
    print(" -> ".join(names))
''')

C_TRY_ORDER = nb.cell('''
stock = {"SKU-A": 120}
try:
    print(stock["SKU-B"])
except LookupError:                            # 范围大的写在前面
    print("被 LookupError 接住了（KeyError 是它的子类）")
except KeyError:
    print("永远走不到这里")
''')

C_TRY_EXC = nb.cell('''
for raw in ["12", "abc", "0", None]:
    try:
        print(100 // int(raw))
    except Exception as e:                     # 不管是什么错，一律报告类型和信息
        print(type(e).__name__ + ":", e)
''')

C_TRY_ABUSE = nb.cell('''
total = 0
for qty in [12, 0, 35]:
    try:
        total = toal + qty         # 手误：total 拼成了 toal
    except Exception:
        pass                       # 吞掉所有错误，什么也不说
print("总数", total)
''')

C_TRY_ELSE = nb.cell('''
for raw in ["12", "abc"]:
    print("--- 处理", repr(raw))
    try:
        qty = int(raw)
    except ValueError:
        print("except：转换失败")
    else:
        print("else：没出错，qty =", qty)
    finally:
        print("finally：无论如何都会执行")
''')

C_RAISE = nb.cell('''
qty = -3
try:
    if qty < 0:
        raise ValueError("箱数不能为负：" + str(qty))     # 自己抛出一个错误
    print("箱数合法")
except ValueError as e:
    print("接住了：", e)
''')

C_RAISE_ERR = nb.cell('''
qty = -3
if qty < 0:
    raise ValueError("箱数不能为负：" + str(qty))
''', err=True)

C_ASSERT = nb.cell('''
stock = 35
assert stock >= 0, "库存不应为负"      # 条件为真：什么都不发生
print("断言通过")
''')

C_ASSERT_ERR = nb.cell('''
stock = -5
assert stock >= 0, "库存不应为负"
''', err=True)

# ───── eval ─────
C_EVAL1 = nb.cell('''
print(eval("1 + 2 * 3"))
x = 10
print(eval("x * 2"))               # eval 能看到你程序里的变量
print(eval("[1, 2, 3][1]"))
''')

C_EVAL_LOOP = nb.cell('''
bad_snippets = ("1 + 'a'", "int('x')", "[1, 2][5]", "{}['k']")
for bad in bad_snippets:                   # bad 依次是这四个字符串
    try:
        eval(bad)                          # 把字符串当 Python 表达式运行
    except Exception as e:                 # 出了错就接住，循环继续
        print(repr(bad), "->", type(e).__name__ + ":", e)
''')

C_EVAL_DANGER = nb.cell('''
secret = "仓库门禁码 1234"
user_text = "secret"            # 假设这是别人在表单里填的一段文字
print(eval(user_text))          # 别人写的字符串，读到了你程序里的变量
''')

C_LITERAL = nb.cell('''
import ast
print(ast.literal_eval("[1, 2, {'a': 3}]"))      # 只认字面量：数字、字符串、列表、字典……
try:
    ast.literal_eval("secret")
except ValueError as e:
    print("literal_eval 拒绝了：", type(e).__name__)
''')

# ───── 调试 ─────
C_DBG_BUG = nb.cell('''
qtys = [12, 0, 35, 8]
total = 0
for q in qtys:
    total = q                       # 想累加，却写成了赋值
print("平均", total / len(qtys))    # 期望 13.75
''')

C_DBG_PRINT = nb.cell('''
total = 0
for q in qtys:
    total = q
    print("q =", q, " total =", total)    # 在循环里打印中间值
''')

C_DBG_FIX = nb.cell('''
total = 0
for q in qtys:
    total += q
print("平均", total / len(qtys))
''')

C_DBG_REPR = nb.cell('''
qty = "12 "                          # 从表格里复制来的，末尾带了一个空格
print(qty, qty == "12")
print(repr(qty), type(qty).__name__, len(qty))
print(f"{qty=}")                     # 快捷写法：同时打印变量名和 repr
''')

SYNTAX_ASSIGN = shown('''
qty = 12
if qty = 12:
    print("正好 12 箱")
''')
