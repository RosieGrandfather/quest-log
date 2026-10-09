"""sql-0 第 2 节：聚合与分组"""
from sqllib import *

nb = Notebook()
C_DB = nb.cell(SETUP_DATA)
C_Q = nb.cell(SETUP_Q)

C_AGG = nb.cell('''
q("""SELECT COUNT(*) AS n_lines, SUM(qty) AS total_qty,
            MIN(unit_price) AS min_p, MAX(unit_price) AS max_p,
            ROUND(AVG(unit_price), 2) AS avg_p
     FROM order_lines""")
''')

C_GROUP = nb.cell('''
q("""SELECT sku, SUM(qty) AS total_qty, ROUND(SUM(qty * unit_price), 1) AS revenue
     FROM order_lines
     GROUP BY sku
     ORDER BY revenue DESC""")
q("SELECT status, COUNT(*) AS n FROM orders GROUP BY status ORDER BY status")
''')

C_HAVING = nb.cell('''
# WHERE 在分组前筛行；HAVING 在分组后筛组
q("""SELECT sku, SUM(qty) AS total_qty FROM order_lines
     GROUP BY sku HAVING SUM(qty) >= 50""")
q("""SELECT sku, SUM(qty) AS big_line_qty FROM order_lines
     WHERE qty >= 10
     GROUP BY sku ORDER BY sku""")
''')

C_NULLAGG = nb.cell('''
q("SELECT AVG(x) AS avg_x, COUNT(x) AS n_x, COUNT(*) AS n_all FROM (SELECT 10 AS x UNION ALL SELECT NULL UNION ALL SELECT 20)")
q("SELECT SUM(x) AS sum_x, COALESCE(SUM(x), 0) AS sum_or_zero FROM (SELECT NULL AS x)")
''')

C_COND = nb.cell('''
q("""SELECT sku,
            SUM(on_hand) AS total,
            SUM(CASE WHEN stock_status = 'AVAIL' THEN on_hand ELSE 0 END) AS avail,
            SUM(CASE WHEN stock_status = 'QUAR'  THEN on_hand ELSE 0 END) AS quarantine
     FROM inventory
     GROUP BY sku
     ORDER BY sku""")
''')

unit = {
 "id": "u02",
 "title": "汇总数字：聚合函数、GROUP BY 与 HAVING",
 "en": "Summarising: Aggregates, GROUP BY & HAVING",
 "minutes": 40,
 "objectives": [
  "使用 **COUNT、SUM、AVG、MIN、MAX**，并分清 `COUNT(*)`、`COUNT(列)`、`COUNT(DISTINCT 列)`",
  "用 **GROUP BY** 按一列或多列分组汇总，说出「SELECT 里的非聚合列必须出现在 GROUP BY」的原因",
  "分清 **WHERE 和 HAVING**：一个在分组前筛行，一个在分组后筛组",
  "知道聚合函数怎么对待 **NULL**（忽略它），并用 **COALESCE** 处理",
  "用 **CASE WHEN 加 SUM（条件聚合）** 把一列拆成几列，做简单的透视",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

业务上大部分问题是汇总：每个产品卖了多少、每个状态有多少订单、可用库存有多少。你做 Power BI 报表时 DAX 的 `SUM`、`COUNT` 背后就是这些。这一节练的是：**先决定「按什么维度分组」，再决定「汇总什么数字」**，并且学会核对汇总结果。

""" + C_DB + r"""
""" + C_Q + r"""

**本节安排（约 40 分钟）**：导读（2 分钟）→ 聚合函数（8 分钟）→ GROUP BY（10 分钟）→ HAVING（6 分钟）→ NULL 与条件聚合（10 分钟）→ 总结（4 分钟）。

### 聚合函数

> **标准定义 · 聚合函数 (aggregate function)**
>
> 把**多行**压缩成**一个值**的函数：`COUNT`（个数）、`SUM`（求和）、`AVG`（平均）、`MIN`、`MAX`。除 `COUNT(*)` 外，聚合函数都**忽略 NULL**。
>
> *English: Aggregate functions collapse many rows into one value. Except COUNT(*), they ignore NULLs.*

**白话版：「一堆行进去，一个数出来」。**

""" + C_AGG + r"""

**读输出：** 订单明细共 14 行，总数量 `SUM(qty)` 是 282（可以自己把 14 行加一遍核对，**汇总结果要用别的办法抽查**），单价最低 9、最高 70，平均 39.25。三种 COUNT：`COUNT(*)` 数所有行；`COUNT(列)` 数该列非空的行；`COUNT(DISTINCT 列)` 数不重复的非空值。

### GROUP BY：先分组，再汇总

> **标准定义 · 分组 (GROUP BY)**
>
> 把行按指定列的值分成若干组，**每组产生一行结果**，聚合函数在每组内部计算。`SELECT` 里出现的**非聚合列必须出现在 GROUP BY 里**，否则这一列在每组里有多个值，数据库不知道该显示哪个。
>
> *English: GROUP BY splits rows into groups by the listed columns and returns one row per group; non-aggregated columns in SELECT must appear in GROUP BY.*

**白话版：「GROUP BY 后面写什么，结果就是一行一个什么」。**

""" + C_GROUP + r"""

**读输出：** 第一条按 SKU 一行，BP100 数量 34、收入 1878（四行加起来），收入最高；TH10 数量 180，数量最多但单价低，收入排第二。最后一行 `XX99` 不在产品表里，第 3 节会专门查这种「孤儿」。第二条按订单状态：CANCELLED 1 张、OPEN 3 张、SHIPPED 5 张，合计 9 张，和订单表总行数一致——**分组后的合计应该等于总数，这是最基本的核对**。可以按多列分组：`GROUP BY sku, stock_status`。

### WHERE 与 HAVING

""" + C_HAVING + r"""

**读输出：** 第一条先按 SKU 分组求和，再用 `HAVING` 保留合计 >= 50 的组，只剩 TH10（180）。第二条用 `WHERE qty >= 10` **先**去掉小行再分组，所以每个 SKU 的合计是「只算单行 >= 10 的」，数字和不筛选时不同。**区别：WHERE 看的是单行的值，HAVING 看的是分组后的汇总值。** 能用 WHERE 筛掉的尽量用 WHERE（先减少数据，更快）。

### NULL 与条件聚合

""" + C_NULLAGG + r"""

**读输出：** `AVG(x)` 是 15，不是 10：因为 NULL 被**忽略**，只用 10 和 20 算（平均 = 30 / 2）。`COUNT(x)` 是 2，`COUNT(*)` 是 3。全部是 NULL 时 `SUM` 返回 NULL 而不是 0，要显示 0 就用 `COALESCE(SUM(x), 0)`（Oracle 里也可以用 `NVL`）。

**条件聚合**是最实用的技巧之一：把 `CASE WHEN` 放进 `SUM`，一次查询把一列拆成几列。比如把库存按状态拆开，看总数、可用、隔离：

""" + C_COND + r"""

**读输出：** BP100 总共 150，其中可用 120、隔离 30；BP200 总共 225，可用 200、隔离 25。如果只看「可用」那一行，就不会发现隔离的 30 和 25；**把总数、可用、隔离放在一起，才看得见库存「存在但不能卖」的部分。**

### 对照你的工作

同事问：「系统里 BP100 到底有多少库存？」你要先问「哪个口径」：含不含隔离库存、含不含各个仓库。上面的条件聚合一次就能给出三个数。这和你在 SOC 项目里发现「隔离库存在系统里看不见」是同一类问题：**同一个词（库存）不同口径数字不同，要写清楚。**

### 这一节你要带走的三句话

1. **GROUP BY 后面写什么，结果就一行一个什么；SELECT 里的非聚合列都要在 GROUP BY 里。**
2. **WHERE 在分组前筛行，HAVING 在分组后筛组；聚合函数忽略 NULL，要 0 用 COALESCE。**
3. **汇总后一定要核对：分组合计等于总数、抽几行手算；条件聚合可以把一列变成几列。**
"""),
  THINK("**（实践）** 写一条查询：每个客户（cust_id）有多少张订单、其中多少张是 SHIPPED。提示：条件聚合。", r"""
`SELECT cust_id, COUNT(*) AS n_orders, SUM(CASE WHEN status = 'SHIPPED' THEN 1 ELSE 0 END) AS n_shipped FROM orders GROUP BY cust_id`。注意是 `THEN 1 ELSE 0`，再 SUM，相当于数个数。核对：每个客户的 n_orders 加起来应该等于 9。
"""),
  THINK("**（概念辨析）** 「找出订单数超过 1 张的客户」应该用 WHERE 还是 HAVING？为什么？", r"""
用 **HAVING**：`GROUP BY cust_id HAVING COUNT(*) > 1`。「订单数」是分组后才算出来的汇总值，WHERE 执行时还没分组，不能用聚合函数。
"""),
  THINK("**（联系）** 同事给你一张 Excel 报表，说 BP100 库存 150，你的查询「可用」是 120。你怎么向他解释？", r"""
先确认他的 150 是不是含隔离库存：总数 150 = 可用 120 + 隔离 30。给他看三列（总数、可用、隔离）说明口径差异，再问他的业务用途：做销售承诺应该看可用，做盘点对账应该看总数。
"""),
  KW(("聚合函数","aggregate function","多行压成一个值"),
     ("分组","GROUP BY","按列值分成若干组"),
     ("分组后筛选","HAVING","对汇总结果筛选"),
     ("计数","COUNT","数行或数非空值"),
     ("求和","SUM","忽略 NULL 的合计"),
     ("平均","AVG","忽略 NULL 的平均"),
     ("最小 / 最大","MIN / MAX","取极值"),
     ("去重计数","COUNT(DISTINCT)","数不重复的值"),
     ("空值替换","COALESCE","返回第一个非空值"),
     ("条件聚合","conditional aggregation","CASE WHEN 放进 SUM"),
     ("口径","definition / basis","同一个词不同的统计范围"),
     ("核对","reconciliation","用另一个办法验证结果"),
  ),
 ],
 "references": [
  SQLITE_DOC,
  {"title": "SQLite 官方文档：聚合函数", "url": "https://www.sqlite.org/lang_aggfunc.html", "note": "COUNT、SUM、AVG 等聚合函数的说明"},
  {"title": "Wikipedia：Group by (SQL)", "url": "https://en.wikipedia.org/wiki/Group_by_(SQL)", "note": "GROUP BY 与 HAVING 的概述"},
 ],
 "quiz": {"questions": [
  Q("`SELECT sku, qty FROM order_lines GROUP BY sku` 在 Oracle 里会报错，原因是：",
    ["qty 是非聚合列，没有出现在 GROUP BY 里", "sku 不能分组", "GROUP BY 必须写在 SELECT 前", "order_lines 不能被分组"], 0,
    "非聚合列必须出现在 GROUP BY 中，否则同一组有多个 qty，数据库不知道显示哪个（SQLite 会放行但结果不可靠）。"),
  Q("一列的值是 10、NULL、20。`AVG(x)` 的结果是：",
    ["15", "10", "30", "NULL"], 0,
    "AVG 忽略 NULL，只用 10 和 20，所以是 15，不是 30 / 3。"),
  Q("要筛出「合计数量 >= 50 的 SKU」，应当用：",
    ["HAVING SUM(qty) >= 50", "WHERE SUM(qty) >= 50", "ORDER BY SUM(qty) >= 50", "DISTINCT SUM(qty) >= 50"], 0,
    "合计是分组后才有的值，只能在 HAVING 里筛。"),
  Q("一列全是 NULL，`SUM(x)` 返回：",
    ["NULL", "0", "报错", "空字符串"], 0,
    "没有可求和的值时 SUM 返回 NULL；要显示 0 用 COALESCE(SUM(x), 0)。"),
  Q("`SUM(CASE WHEN stock_status = 'QUAR' THEN on_hand ELSE 0 END)` 的作用是：",
    ["只汇总隔离状态的库存", "删除隔离库存", "把所有库存改成 0", "按状态排序"], 0,
    "条件聚合：只有满足条件的行才贡献数量，其余算 0。"),
 ]},
}
retarget(unit, [0, 3, 1, 2, 3])

if __name__ == '__main__':
    dump(unit, "sql-0", "u02-aggregate.json", n_questions=5)
