"""sql-0 第 3 节：JOIN"""
from sqllib import *

nb = Notebook()
C_DB = nb.cell(SETUP_DATA)
C_Q = nb.cell(SETUP_Q)

C_INNER = nb.cell('''
q("""SELECT o.order_id, c.name, ol.sku, ol.qty
     FROM orders o
     JOIN customers c   ON c.cust_id  = o.cust_id
     JOIN order_lines ol ON ol.order_id = o.order_id
     WHERE o.order_id IN (101, 109)
     ORDER BY o.order_id, ol.line_no""")
''')

C_LEFT = nb.cell('''
q("""SELECT o.order_id, c.name
     FROM orders o
     LEFT JOIN customers c ON c.cust_id = o.cust_id
     WHERE o.order_id IN (108, 109)
     ORDER BY o.order_id""")
''')

C_ANTI = nb.cell('''
print("没有订单的客户：")
q("""SELECT c.cust_id, c.name FROM customers c
     LEFT JOIN orders o ON o.cust_id = c.cust_id
     WHERE o.order_id IS NULL""")
print("客户不存在的订单：")
q("""SELECT o.order_id, o.cust_id FROM orders o
     LEFT JOIN customers c ON c.cust_id = o.cust_id
     WHERE c.cust_id IS NULL""")
print("产品主数据里没有的 SKU：")
q("""SELECT ol.order_id, ol.sku FROM order_lines ol
     LEFT JOIN products p ON p.sku = ol.sku
     WHERE p.sku IS NULL""")
''')

C_ONWHERE = nb.cell('''
print("条件写在 ON：保留所有客户")
q("""SELECT c.name, COUNT(o.order_id) AS shipped
     FROM customers c
     LEFT JOIN orders o ON o.cust_id = c.cust_id AND o.status = 'SHIPPED'
     GROUP BY c.cust_id ORDER BY c.cust_id""")
print("条件写在 WHERE：没有已发货订单的客户消失")
q("""SELECT c.name, COUNT(o.order_id) AS shipped
     FROM customers c
     LEFT JOIN orders o ON o.cust_id = c.cust_id
     WHERE o.status = 'SHIPPED'
     GROUP BY c.cust_id ORDER BY c.cust_id""")
''')

C_FAN = nb.cell('''
print("BP100 的销售数量（正确）：")
q("SELECT SUM(qty) AS qty FROM order_lines WHERE sku = 'BP100'")
print("先 JOIN 库存表（BP100 有 2 行库存）再求和：")
q("""SELECT SUM(ol.qty) AS qty
     FROM order_lines ol JOIN inventory i ON i.sku = ol.sku
     WHERE ol.sku = 'BP100'""")
print("先把库存汇总成每个 SKU 一行，再 JOIN：")
q("""SELECT SUM(ol.qty) AS qty
     FROM order_lines ol
     JOIN (SELECT sku, SUM(on_hand) AS on_hand FROM inventory GROUP BY sku) i
       ON i.sku = ol.sku
     WHERE ol.sku = 'BP100'""")
''')

unit = {
 "id": "u03",
 "title": "把表连起来：JOIN、孤儿记录与重复放大",
 "en": "Joining Tables: JOIN, Orphan Records & Row Fan-out",
 "minutes": 45,
 "objectives": [
  "区分 **INNER JOIN 和 LEFT JOIN**，并说出各自会丢掉或保留哪些行",
  "用 **LEFT JOIN … IS NULL** 找出「孤儿记录」：没有对应主数据的行",
  "知道 LEFT JOIN 里条件写在 **ON 还是 WHERE** 的区别",
  "识别 **一对多 JOIN 造成的重复放大 (fan-out)**，并用先汇总再 JOIN 来避免",
  "能读懂多表 JOIN 的结果行数，并核对「连接前后行数是否合理」",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

真实系统里数据分散在很多表：订单头在一张表，订单行在另一张，客户和产品是主数据。**JOIN 就是用一个共同的列（键）把它们对上。**排查问题时，大部分「对不上」就出在 JOIN：少了行、多了行、数字翻倍。这一节练三件事：连起来、找孤儿、防止重复放大。

""" + C_DB + r"""
""" + C_Q + r"""

**本节安排（约 45 分钟）**：导读（2 分钟）→ INNER 与 LEFT（12 分钟）→ 孤儿记录（10 分钟）→ ON 与 WHERE（7 分钟）→ 重复放大（10 分钟）→ 总结（4 分钟）。

### INNER JOIN 与 LEFT JOIN

> **标准定义 · 连接 (JOIN)**
>
> **INNER JOIN** 只保留**两边都能对上**的行；**LEFT JOIN** 保留**左表所有行**，右表对不上的列显示 NULL。键就是 `ON` 里写的相等条件，例如 `c.cust_id = o.cust_id`。
>
> *English: INNER JOIN keeps only matching rows from both tables; LEFT JOIN keeps every row from the left table and fills unmatched right-side columns with NULL.*

**白话版：「INNER 是两边都要有才留；LEFT 是以左边为准，右边没有就留空」。**

""" + C_INNER + r"""

**读输出：** 101 号订单有 2 行明细，所以 JOIN 后出现 **2 行**（行数由「多的一边」决定）。109 号订单**完全没出现**：它的客户编号是 9，客户表里没有 9，INNER JOIN 把它悄悄丢掉了。如果你拿这个结果去汇总，总数就比订单表少。

""" + C_LEFT + r"""

**读输出：** 改成 LEFT JOIN，订单 109 保留了，客户名显示 `NULL`。**排查时用 LEFT JOIN 能看见「对不上的」，INNER JOIN 看不见。**

### 找孤儿记录：LEFT JOIN … IS NULL

> **标准定义 · 孤儿记录 (orphan record)**
>
> 在一张表里引用了另一张表的键（外键），但被引用的行**不存在**。例如订单引用了不存在的客户，订单行引用了不在产品主数据里的 SKU。
>
> *English: A row whose foreign key refers to a parent row that does not exist.*

**白话版：「单据上写了编号，但主数据里查无此人」。**这是数据质量排查里最常用的一类查询：**以子表为左表 LEFT JOIN 主数据，再筛主数据那边是 NULL 的行**。

""" + C_ANTI + r"""

**读输出：** 客户 6（Foxtrot Store）没有任何订单；订单 109 引用了不存在的客户 9；订单 108 里有一个 SKU `XX99` 不在产品表里。这三类问题在真实系统里分别意味着：客户建了没人下单（可能正常）、单据上的客户没建主数据、SKU 没维护或被写错。**先判断是数据问题还是操作问题，再决定谁去修。**

### ON 与 WHERE：LEFT JOIN 里条件写哪里

""" + C_ONWHERE + r"""

**读输出：** 条件写在 `ON`，6 个客户都在，没有已发货订单的客户显示 0（Delta Retail、Foxtrot Store）。条件写在 `WHERE`，结果只剩 4 个客户：因为没匹配上的行右边是 NULL，`o.status = 'SHIPPED'` 对 NULL 不成立，被 WHERE 筛掉了，**LEFT JOIN 实际上退化成了 INNER JOIN**。规则：**想保留左表所有行，右表的筛选条件写在 ON 里。**

### 重复放大 (fan-out)：数字突然翻倍

当你 JOIN 的那张表在键上**有多行**（一对多），左表的行会被复制，之后再 SUM 就会重复计算。

""" + C_FAN + r"""

**读输出：** BP100 实际销售数量是 34。库存表里 BP100 有 2 行（可用和隔离各一行），直接 JOIN 后每个销售行被复制了 2 次，求和变成 **68**。先把库存按 SKU 汇总成一行再 JOIN，结果回到 34。**核对办法：JOIN 前后对比行数和合计，数字异常变大先想 fan-out。**

### 对照你的工作

你做对账、做 Power BI 数据模型时，每次连接两张表都要问：**键在这两边各自是不是唯一？** 一边唯一、另一边多行（一对多）是正常的；两边都多行（多对多）就会放大。这和 Power BI 里关系的「一对多」「多对多」是同一件事。

### 这一节你要带走的三句话

1. **INNER 只留两边都有的，LEFT 以左表为准；排查「对不上」用 LEFT JOIN 加 IS NULL。**
2. **LEFT JOIN 里右表的筛选条件写在 ON，写在 WHERE 会把 LEFT 变成 INNER。**
3. **JOIN 一对多会复制行导致合计翻倍；先汇总成每个键一行再 JOIN，并对比 JOIN 前后的行数和合计。**
"""),
  THINK("**（实践）** 写一条查询，列出每张订单的订单号、客户名和订单总金额（`qty * unit_price` 之和），客户不存在的订单也要显示。", r"""
`SELECT o.order_id, c.name, SUM(ol.qty * ol.unit_price) AS amount FROM orders o LEFT JOIN customers c ON c.cust_id = o.cust_id JOIN order_lines ol ON ol.order_id = o.order_id GROUP BY o.order_id, c.name ORDER BY o.order_id`。客户用 LEFT JOIN 保留 109（名字为 NULL）。核对：9 张订单，9 行。
"""),
  THINK("**（概念辨析）** 一张表 100 行，JOIN 一张 5 行的表之后变成 300 行。可能是什么原因？", r"""
最可能是 **fan-out**：连接键在 5 行的那张表里不唯一，有些键对应多行，左边的行被复制。要查那张小表的键是否重复（`GROUP BY 键 HAVING COUNT(*) > 1`）。也可能是 ON 条件漏写，变成了交叉连接（100 × 5 = 500 是交叉连接的行数）。
"""),
  THINK("**（联系）** 同事说「订单总数和汇总报表对不上，少了 1 张」，你怎么用本节的方法排查？", r"""
先数订单表行数（9），再数报表用的 JOIN 结果行数。如果报表用了 INNER JOIN 客户表，那 109 号订单（客户不存在）就被丢了。用 `LEFT JOIN … IS NULL` 找出「订单没有客户」的行，把它交给负责主数据的人，同时和同事确认这类订单该不该进报表。
"""),
  KW(("连接","JOIN","用共同的键把表连起来"),
     ("内连接","INNER JOIN","只保留两边都能匹配的行"),
     ("左连接","LEFT JOIN","保留左表所有行"),
     ("键","key","用来匹配的列"),
     ("主键","primary key","唯一标识一行的列"),
     ("外键","foreign key","引用另一张表主键的列"),
     ("孤儿记录","orphan record","引用的主数据不存在"),
     ("重复放大","fan-out","一对多连接造成行被复制"),
     ("一对多","one-to-many","一边唯一、另一边多行"),
     ("多对多","many-to-many","两边都有重复的键"),
     ("交叉连接","CROSS JOIN","两边所有行两两组合"),
     ("自连接","self join","表和自己连接"),
  ),
 ],
 "references": [
  SQLITE_DOC,
  {"title": "Wikipedia：Join (SQL)", "url": "https://en.wikipedia.org/wiki/Join_(SQL)", "note": "各种 JOIN 的定义和示例"},
  {"title": "Wikipedia：Foreign key", "url": "https://en.wikipedia.org/wiki/Foreign_key", "note": "外键与引用完整性"},
 ],
 "quiz": {"questions": [
  Q("订单表里有一张订单的客户编号在客户表中不存在。`orders INNER JOIN customers` 的结果里，这张订单会：",
    ["消失", "保留，客户名为 NULL", "保留，客户名为空字符串", "导致报错"], 0,
    "INNER JOIN 只保留两边都匹配的行，不匹配的订单被丢掉；LEFT JOIN 才会保留并显示 NULL。"),
  Q("找出「在产品主数据里不存在的 SKU」，应该用：",
    ["订单行 LEFT JOIN 产品，再筛产品键 IS NULL", "产品 INNER JOIN 订单行", "SELECT DISTINCT 产品", "订单行 GROUP BY 产品"], 0,
    "以子表（订单行）为左表，LEFT JOIN 主数据，主数据那边是 NULL 的就是孤儿。"),
  Q("`customers LEFT JOIN orders ... WHERE o.status = 'SHIPPED'` 的问题是：",
    ["没有已发货订单的客户会消失，LEFT 退化成 INNER", "会报错", "会让所有客户重复", "会把状态改成 SHIPPED"], 0,
    "没匹配上的行右边是 NULL，条件对 NULL 不成立，被 WHERE 筛掉。保留左表所有行时要把条件写在 ON。"),
  Q("销售表合计 34，JOIN 库存表后合计变成 68，最可能的原因是：",
    ["库存表在该键上有 2 行，销售行被复制了两次", "库存表有 NULL", "SUM 写错了", "ORDER BY 写错了"], 0,
    "一对多 JOIN 复制左边的行，再求和就重复计算。先把库存汇总成每个键一行。"),
  Q("101 号订单有 2 行明细，`orders JOIN order_lines` 后 101 号订单出现几行？",
    ["2 行", "1 行", "0 行", "4 行"], 0,
    "JOIN 后的行数由匹配的行决定，一个订单头匹配 2 个明细行，就出现 2 行。"),
 ]},
}
retarget(unit, [1, 3, 0, 2, 0])

if __name__ == '__main__':
    dump(unit, "sql-0", "u03-joins.json", n_questions=5)
