"""sql-0 第 4 节：子查询、CTE、集合运算"""
from sqllib import *

nb = Notebook()
C_DB = nb.cell(SETUP_DATA)
C_Q = nb.cell(SETUP_Q)

C_SUB = nb.cell('''
print("买过 BP100 的客户（IN 子查询）：")
q("""SELECT name FROM customers
     WHERE cust_id IN (SELECT o.cust_id FROM orders o
                       JOIN order_lines ol ON ol.order_id = o.order_id
                       WHERE ol.sku = 'BP100')
     ORDER BY name""")
print("单价高于平均单价的订单行数：")
q("SELECT COUNT(*) AS n FROM order_lines WHERE unit_price > (SELECT AVG(unit_price) FROM order_lines)")
''')

C_NOTIN = nb.cell('''
db.execute("INSERT INTO orders VALUES (110, NULL, '2026-09-28', 'OPEN')")   # 一张客户为空的订单
print("NOT IN（子查询结果里有 NULL）：")
q("SELECT cust_id, name FROM customers WHERE cust_id NOT IN (SELECT cust_id FROM orders)")
print("NOT EXISTS：")
q("""SELECT c.cust_id, c.name FROM customers c
     WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.cust_id = c.cust_id)""")
db.rollback()    # 撤销刚才插入的那一行
''')

C_CTE = nb.cell('''
q("""WITH order_amt AS (
         SELECT order_id, SUM(qty * unit_price) AS amount
         FROM order_lines GROUP BY order_id
     )
     SELECT o.order_id, o.status, a.amount
     FROM orders o JOIN order_amt a ON a.order_id = o.order_id
     WHERE a.amount >= 1000
     ORDER BY a.amount DESC""")
''')

C_SET = nb.cell('''
q("""SELECT COUNT(*) AS rows_all FROM
     (SELECT sku FROM order_lines UNION ALL SELECT sku FROM inventory)""")
q("""SELECT COUNT(*) AS rows_distinct FROM
     (SELECT sku FROM order_lines UNION SELECT sku FROM inventory)""")
print("卖过但产品表里没有（Oracle 里 EXCEPT 叫 MINUS）：")
q("SELECT sku FROM order_lines EXCEPT SELECT sku FROM products")
print("产品表里有但从没卖过：")
q("SELECT sku FROM products EXCEPT SELECT sku FROM order_lines")
''')

unit = {
 "id": "u04",
 "title": "查询里套查询：子查询、CTE 与集合运算",
 "en": "Queries Inside Queries: Subqueries, CTEs & Set Operators",
 "minutes": 40,
 "objectives": [
  "写出**标量子查询、IN 子查询、EXISTS**，并说出它们适合解决什么问题",
  "识别 **NOT IN 遇到 NULL 的陷阱**，改用 **NOT EXISTS** 或 LEFT JOIN",
  "用 **CTE（WITH 子句）** 把复杂查询拆成一步一步的小块",
  "区分 **UNION 与 UNION ALL**，会用 **EXCEPT / MINUS、INTERSECT** 做两个结果的比较",
  "对一个多层嵌套的旧查询，能逐层读懂它在做什么",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

真实工作里你很少写一条简单的查询，更多是**读别人留下的长 SQL**，里面一层套一层。这一节教你读和写这些结构：子查询、CTE，以及把两个结果相减、相加的集合运算。接手 BAU 工作时，看懂旧查询比写新查询更常见。

""" + C_DB + r"""
""" + C_Q + r"""

**本节安排（约 40 分钟）**：导读（2 分钟）→ 子查询（10 分钟）→ NOT IN 陷阱（8 分钟）→ CTE（8 分钟）→ 集合运算（8 分钟）→ 总结（4 分钟）。

### 子查询

> **标准定义 · 子查询 (subquery)**
>
> 写在括号里、嵌在另一条查询中的查询。**标量子查询**返回单个值；**IN 子查询**返回一列值；**EXISTS** 只判断「有没有至少一行」。
>
> *English: A query nested inside another query, returning a single value, a list of values, or an existence test.*

**白话版：「先问一个小问题，把答案交给大问题用」。**

""" + C_SUB + r"""

**读输出：** 买过 BP100 的客户是 Alpha Pharmacy、Echo Health、Gamma Trading（客户 9 不在客户表里，所以名字查不到）。第二条：括号里先算出平均单价（39.25），外层再数单价高于它的行，共 8 行。**读嵌套查询的办法：从最里面的括号开始，一层层往外读。**

### NOT IN 遇到 NULL：最危险的陷阱

""" + C_NOTIN + r"""

**读输出：** 我们临时插入了一张 `cust_id` 为 NULL 的订单。`NOT IN` 版本**一行都没返回**，应该返回的客户 6 不见了；`NOT EXISTS` 版本正确返回了客户 6。原因：`x NOT IN (1,2,NULL)` 展开后包含 `x <> NULL`，结果是未知，整条判断永远不为真。**规则：子查询的列可能有 NULL 时，不要用 NOT IN，用 NOT EXISTS 或 LEFT JOIN … IS NULL。** 最后的 `rollback()` 撤销了临时插入，数据库回到原样（第 6 节讲事务）。

### CTE：把长查询拆成步骤

> **标准定义 · 公共表表达式 (CTE, Common Table Expression)**
>
> 用 `WITH 名字 AS (查询)` 给一个中间结果起名字，后面的查询可以像表一样使用它。可以写多个，逗号分隔。
>
> *English: WITH name AS (query) defines a named temporary result that the main query can reference like a table.*

**白话版：「给中间步骤起名字，让长查询像读文章一样一步一步读」。**

""" + C_CTE + r"""

**读输出：** 第一步 `order_amt` 算出每张订单的金额；第二步把订单表和它连起来，只保留金额 >= 1000 的：107 号（1350）和 101 号（1000）。同样的事用子查询也能写，但 CTE 把「先算什么、后算什么」摊开了，**调试时可以单独运行 CTE 里的那一段看中间结果。**

### 集合运算：两个结果相加、相减

""" + C_SET + r"""

**读输出：**

- `UNION ALL` 直接拼接，不去重：订单明细的 14 行加库存的 8 行，共 **22** 行。`UNION` 会去重，只剩 **7** 个不同的 SKU。**能用 UNION ALL 就用 UNION ALL**，去重要排序，更慢，而且会悄悄吃掉你想保留的重复行。
- `EXCEPT`（Oracle 叫 `MINUS`）是「左边有、右边没有」：卖过但产品表里没有的是 `XX99`；产品表里有但从没卖过的是 `OLD9`。第 3 节的孤儿查询也可以这样写，**用来做两边对比很方便。**
- 另有 `INTERSECT`（两边都有）。使用集合运算时，两边的列数和类型要一致。

### 对照你的工作

接手别人的 SQL 或 Power BI 的数据源查询时：**先看有没有 NOT IN；看 JOIN 是不是会放大；看有没有 UNION（是否该用 UNION ALL）**。这三个是最常见的隐藏问题。

### 这一节你要带走的三句话

1. **子查询从最里面一层读起；CTE 用名字把步骤摊开，更好读、更好调试。**
2. **NOT IN 遇到 NULL 会一行都不返回，改用 NOT EXISTS 或 LEFT JOIN … IS NULL。**
3. **UNION 去重、UNION ALL 不去重（优先用后者）；EXCEPT / MINUS 用来找「左边有右边没有」的差异。**
"""),
  THINK("**（实践）** 用 `NOT EXISTS` 写一条查询：找出订单明细里 SKU 不在产品表里的订单号。", r"""
`SELECT DISTINCT ol.order_id FROM order_lines ol WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.sku = ol.sku)`。结果是 108 号订单。和第 3 节用 LEFT JOIN 的写法结果相同，选哪种看哪种更好读。
"""),
  THINK("**（概念辨析）** `UNION` 和 `UNION ALL` 什么时候结果行数不同？为什么要优先用 UNION ALL？", r"""
当两边结果有重复行，或同一边内部有重复行时，UNION 会去重，行数更少。UNION ALL 不去重也不排序，更快，并且保留所有行。只有确实需要去重时才用 UNION，否则可能把应该保留的重复数据悄悄去掉。
"""),
  THINK("**（联系）** 你接手一个旧查询，里面写着 `WHERE cust_id NOT IN (SELECT cust_id FROM orders)`，用来找「没下过单的客户」，一直没出问题。你要不要改？", r"""
要改，或至少要验证。现在没问题只是因为 `orders.cust_id` 目前没有 NULL，哪天有一张客户为空的订单进来，查询就会静默返回空，没人报错。改成 NOT EXISTS 成本很低，还能避免将来难排查的问题。
"""),
  KW(("子查询","subquery","括号里的查询"),
     ("标量子查询","scalar subquery","返回单个值"),
     ("存在判断","EXISTS","子查询有没有结果行"),
     ("不在其中","NOT IN","遇到 NULL 会出问题"),
     ("公共表表达式","CTE / WITH","给中间结果起名字"),
     ("联合","UNION","合并并去重"),
     ("联合全部","UNION ALL","合并不去重"),
     ("差集","EXCEPT / MINUS","左边有右边没有"),
     ("交集","INTERSECT","两边都有"),
     ("相关子查询","correlated subquery","引用外层查询的列"),
     ("内联视图","inline view","FROM 里的子查询"),
     ("嵌套","nesting","查询里套查询"),
  ),
 ],
 "references": [
  SQLITE_DOC,
  {"title": "Wikipedia：Set operations (SQL)", "url": "https://en.wikipedia.org/wiki/Set_operations_(SQL)", "note": "UNION、INTERSECT、EXCEPT 的概述"},
  {"title": "Wikipedia：Hierarchical and recursive queries in SQL", "url": "https://en.wikipedia.org/wiki/Hierarchical_and_recursive_queries_in_SQL", "note": "CTE（WITH 子句）的背景，含递归用法"},
 ],
 "quiz": {"questions": [
  Q("子查询的结果列里有 NULL 时，`x NOT IN (子查询)` 会：",
    ["一行都不返回", "只返回 NULL 的行", "返回所有行", "报错"], 0,
    "NOT IN 里包含与 NULL 的比较，结果是未知，条件永远不为真，所以静默返回空。"),
  Q("找「没有任何订单的客户」，下面哪种写法对 NULL 最安全？",
    ["NOT EXISTS (SELECT 1 FROM orders o WHERE o.cust_id = c.cust_id)", "NOT IN (SELECT cust_id FROM orders)", "WHERE cust_id <> orders.cust_id", "SELECT DISTINCT cust_id"], 0,
    "NOT EXISTS 只判断有没有匹配行，不受 NULL 影响。"),
  Q("两张表各有 14 行和 8 行，其中有重复值。`UNION ALL` 的行数是：",
    ["22", "7", "14", "8"], 0,
    "UNION ALL 不去重，行数是两边相加：14 + 8 = 22。"),
  Q("Oracle 里等价于 SQLite 的 `EXCEPT` 的关键字是：",
    ["MINUS", "SUBTRACT", "DIFF", "NOT"], 0,
    "Oracle 用 MINUS，表示左边有右边没有。较新版本的 Oracle 也支持 EXCEPT，具体以你们的版本为准。"),
  Q("使用 CTE 的主要好处是：",
    ["把复杂查询拆成命名的步骤，更好读、更好调试", "一定让查询更快", "可以修改表数据", "代替索引"], 0,
    "CTE 主要提升可读性和可调试性，不保证更快。"),
 ]},
}
retarget(unit, [2, 0, 3, 1, 2])

if __name__ == '__main__':
    dump(unit, "sql-0", "u04-subquery-cte.json", n_questions=5)
