"""pl300-0 第 3 节：转换与加载"""
from pllib import *

nb = Notebook()

C_MERGE = nb.cell('''
orders = [("O1", "C1", 100), ("O2", "C2", 250), ("O3", "C9", 80), ("O4", "C1", 40)]
customers = [("C1", "Ann"), ("C2", "Bob"), ("C3", "Cy")]

def merge(left, right, kind):
    rkeys = {k for k, *_ in right}
    out = []
    for lrow in left:
        matches = [r for r in right if r[0] == lrow[1]]
        if matches:
            out += [(*lrow, m[1]) for m in matches]
        elif kind in ("left outer", "left anti"):
            out.append((*lrow, None))
    if kind == "inner":      out = [r for r in out if r[-1] is not None]
    if kind == "left anti":  out = [r for r in out if r[-1] is None]
    return out

for kind in ("left outer", "inner", "left anti"):
    res = merge(orders, customers, kind)
    print(f"{kind:10s} → {len(res)} 行", [r[0] + ":" + str(r[-1]) for r in res])
''')

C_DUPKEY = nb.cell('''
# 键重复会让行数"变多"：客户表里 C1 出现两次
customers_dup = customers + [("C1", "Ann (旧)")]
res = merge(orders, customers_dup, "left outer")
print("订单 4 行 → 合并后", len(res), "行；O1 的销售额被算了", sum(1 for r in res if r[0] == "O1"), "次")
''')

C_UNPIV = nb.cell('''
wide = {"Product": ["A", "B"], "Jan": [10, 5], "Feb": [12, 7], "Mar": [9, 6]}
months = ["Jan", "Feb", "Mar"]

# 逆透视（Unpivot）：把月份列变成「属性-值」两列
long = [(p, m, wide[m][i]) for i, p in enumerate(wide["Product"]) for m in months]
print(long[:4])
print("宽表单元格:", len(wide["Product"]) * len(months), "→ 长表行数:", len(long))

# 透视（Pivot）：再变回去，值列在重复时要聚合
from collections import defaultdict
agg = defaultdict(int)
for p, m, v in long: agg[(p, m)] += v
print({p: [agg[(p, m)] for m in months] for p in wide["Product"]})
''')

C_GROUP = nb.cell('''
sales = [("North","A",10),("North","B",5),("South","A",7),("North","A",3),("South","B",9)]
groups = {}
for region, prod, amt in sales:
    g = groups.setdefault(region, {"n": 0, "sum": 0})
    g["n"] += 1; g["sum"] += amt
for r, g in groups.items():
    print(r, "行数", g["n"], "合计", g["sum"])
''')

C_STAR = nb.cell('''
flat = [
    {"order": "O1", "cust": "Ann", "city": "SG", "amt": 100},
    {"order": "O2", "cust": "Bob", "city": "KL", "amt": 250},
    {"order": "O3", "cust": "Ann", "city": "SG", "amt": 40},
]
# 维度表：每个客户一行，加一个代理键；事实表：只留键和数值
dim = {}
for r in flat:
    dim.setdefault(r["cust"], {"CustKey": len(dim) + 1, "Customer": r["cust"], "City": r["city"]})
fact = [{"Order": r["order"], "CustKey": dim[r["cust"]]["CustKey"], "Amount": r["amt"]} for r in flat]
print("维度表:", list(dim.values()))
print("事实表:", fact)
''')

C_JSON = nb.cell('''
import json
raw = '{"orders":[{"id":"O1","lines":[{"sku":"A","qty":2},{"sku":"B","qty":1}]},{"id":"O2","lines":[{"sku":"A","qty":5}]}]}'
data = json.loads(raw)
rows = [(o["id"], l["sku"], l["qty"]) for o in data["orders"] for l in o["lines"]]   # 展开列表 + 展开记录
print(rows)
''')

