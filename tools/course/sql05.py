"""sql-0 第 5 节：窗口函数"""
from sqllib import *

nb = Notebook()
C_DB = nb.cell(SETUP_DATA)
C_Q = nb.cell(SETUP_Q)

C_OA = nb.cell('''
# 先把「每张订单的金额」做成一段可复用的 CTE 文本，后面几个块都拼在它前面用
OA = """WITH oa AS (
    SELECT o.order_id, o.cust_id, o.order_date,
           SUM(ol.qty * ol.unit_price) AS amount
    FROM orders o JOIN order_lines ol ON ol.order_id = o.order_id
    GROUP BY o.order_id)"""
q(OA + " SELECT COUNT(*) AS n_orders, SUM(amount) AS total FROM oa")
''')

C_RANK = nb.cell('''
q(OA + """
  SELECT order_id, amount,
         RANK()       OVER (ORDER BY amount DESC)               AS rnk,
         DENSE_RANK() OVER (ORDER BY amount DESC)               AS dense,
         ROW_NUMBER() OVER (ORDER BY amount DESC, order_id)     AS rn
  FROM oa ORDER BY amount DESC, order_id LIMIT 6""")
''')

C_LATEST = nb.cell('''
q(OA + """, ranked AS (
      SELECT oa.*, ROW_NUMBER() OVER (PARTITION BY cust_id ORDER BY order_date DESC) AS rn
      FROM oa)
  SELECT cust_id, order_id, order_date, amount FROM ranked WHERE rn = 1 ORDER BY cust_id""")
''')

C_RUN = nb.cell('''
q(OA + """
  SELECT order_id, order_date, amount,
         SUM(amount) OVER (ORDER BY order_date, order_id) AS running_total
  FROM oa ORDER BY order_date, order_id LIMIT 5""")
q(OA + """
  SELECT cust_id, order_date, amount,
         LAG(amount) OVER (PARTITION BY cust_id ORDER BY order_date) AS prev_amount
  FROM oa WHERE cust_id IN (1, 2, 3) ORDER BY cust_id, order_date""")
''')

C_DEDUP = nb.cell('''
db.execute("CREATE TABLE stg(order_id INT, sku TEXT, qty INT, loaded_at TEXT)")
db.executemany("INSERT INTO stg VALUES (?,?,?,?)", [
    (101, "BP100", 10, "09-01 08:00"), (101, "BP100", 12, "09-02 08:00"),
    (102, "BP200", 20, "09-01 08:00")])
print("同一个订单和 SKU 被加载了两次：")
q("SELECT * FROM stg ORDER BY order_id, loaded_at")
print("每组只保留最新加载的一条：")
q("""SELECT order_id, sku, qty, loaded_at FROM (
         SELECT stg.*, ROW_NUMBER() OVER (PARTITION BY order_id, sku ORDER BY loaded_at DESC) AS rn
         FROM stg) WHERE rn = 1 ORDER BY order_id""")
''')

unit = {
 "id": "u05",
 "title": "窗口函数：排名、取最新一条、累计与上一行",
 "en": "Window Functions: Ranking, Latest Row, Running Totals & LAG",
 "minutes": 45,
 "objectives": [
  "说出**窗口函数和 GROUP BY 的区别**：窗口函数**不压缩行**，每行都保留",
  "读懂 `函数() OVER (PARTITION BY … ORDER BY …)` 的结构",
  "分清 **ROW_NUMBER、RANK、DENSE_RANK** 遇到并列时的区别",
  "用 **ROW_NUMBER 去重 / 取每组最新一条**，这是 BAU 里最常用的写法",
  "用 **SUM OVER 做累计、用 LAG 取上一行**，做环比和对比",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

GROUP BY 会把一组行压成一行。但很多业务问题要的是「**保留每一行，同时看到它在组里的位置或组的合计**」：每个客户最新的一张订单、金额排名第几、累计到今天一共多少、和上一次相比涨了多少。这些就是窗口函数。你做 Power BI 的 DAX（如 `RANKX`、时间智能）时思路是一样的。面试和 BA / 数据岗位的 SQL 题几乎必考。

""" + C_DB + r"""
""" + C_Q + r"""

**本节安排（约 45 分钟）**：导读（2 分钟）→ OVER 的结构与排名（10 分钟）→ 取每组最新一条（10 分钟）→ 累计和上一行（10 分钟）→ 去重实战（8 分钟）→ 总结（5 分钟）。

### OVER：窗口的结构

> **标准定义 · 窗口函数 (window function)**
>
> 在**每一行**上，对「和它相关的一组行（窗口）」做计算，**结果附在这一行旁边，不合并行**。写法：`函数() OVER (PARTITION BY 分组列 ORDER BY 排序列)`。`PARTITION BY` 决定窗口分成哪几组（可省略，则全表一组），`ORDER BY` 决定组内顺序。
>
> *English: A window function computes a value for each row over a set of related rows without collapsing them; OVER(PARTITION BY … ORDER BY …) defines the window.*

**白话版：「GROUP BY 是『每组只留一行』，窗口函数是『每行都留着，还告诉你它在组里是第几、组里合计多少』」。**

""" + C_OA + r"""

**读输出：** 这是后面共用的「订单金额」CTE：9 张订单，总金额 6554。

### 排名：RANK、DENSE_RANK、ROW_NUMBER

""" + C_RANK + r"""

**读输出：** 订单 105 和 106 金额都是 900，并列。**`RANK`** 并列后跳号：1、2、3、3、5、6；**`DENSE_RANK`** 并列后不跳号：1、2、3、3、4、5；**`ROW_NUMBER`** 不管并列，永远是 1、2、3、4、5、6（并列的谁在前由额外的排序决定，这里加了 `order_id`）。**要「每组只取一行」就用 ROW_NUMBER，因为它保证唯一。**

### 取每组最新一条

""" + C_LATEST + r"""

**读输出：** 每个客户最新的一张订单：客户 1 是 102（09-03），客户 2 是 108，客户 3 是 105 ……写法是固定套路：**内层用 `ROW_NUMBER() OVER (PARTITION BY 分组列 ORDER BY 日期 DESC)` 编号，外层筛 `rn = 1`。** 窗口函数的结果不能直接写在同一层的 WHERE 里（WHERE 比 SELECT 先执行），所以要套一层。

### 累计和上一行

""" + C_RUN + r"""

**读输出：** 第一条累计：1000 → 1800 → 2150 → 2948 → 3848，每行是「截止这一行的合计」。第二条 `LAG(amount)` 取**同一客户上一张订单**的金额，客户 1 的第一张订单没有上一张，所以是 `NULL`；第二张订单（800）旁边是上一张的 1000，可以直接算差值。`LEAD` 则取下一行。

### 实战：去重，保留最新加载的一条

BAU 里很常见：数据重复加载，同一个订单和 SKU 有两条，只有最新的是对的。

""" + C_DEDUP + r"""

**读输出：** 订单 101 的 BP100 被加载了两次（数量 10 和 12），按加载时间倒序编号，保留 `rn = 1`，也就是更新的那条（12）。**注意：这个查询只是「选出」要保留的行，没有删除任何数据。** 真要清理数据前，要先和负责人确认「哪一条才是对的」。

### 对照你的工作

你排查「系统数字和 Excel 对不上」时，经常会遇到重复行、多个版本。看到「每个 X 的最新一条」「每个 X 的前 N 个」「和上一期比」，第一反应应该是窗口函数。

### 这一节你要带走的三句话

1. **窗口函数不合并行；`OVER (PARTITION BY 分组 ORDER BY 顺序)` 里，PARTITION 是分组，ORDER BY 是组内顺序。**
2. **RANK 并列跳号，DENSE_RANK 并列不跳号，ROW_NUMBER 永远唯一；取每组最新一条用 ROW_NUMBER 加 `rn = 1`。**
3. **窗口函数的结果要套一层才能在 WHERE 里筛选；SUM OVER 做累计，LAG 取上一行。**
"""),
  THINK("**（实践）** 写一条查询：每个 SKU 在订单明细里数量最大的那一行（订单号、SKU、数量）。提示：ROW_NUMBER。", r"""
`SELECT order_id, sku, qty FROM (SELECT order_id, sku, qty, ROW_NUMBER() OVER (PARTITION BY sku ORDER BY qty DESC, order_id) AS rn FROM order_lines) WHERE rn = 1`。每个 SKU 一行（共 6 个 SKU）。如果数量并列时想全部保留，改用 RANK 并筛 `= 1`。
"""),
  THINK("**（概念辨析）** 为什么不能写 `WHERE ROW_NUMBER() OVER (...) = 1`？", r"""
因为 WHERE 在逻辑上先于 SELECT 执行，窗口函数的结果在 SELECT 阶段才产生，WHERE 里还不存在。解决办法是把窗口函数放进子查询或 CTE，外层再筛。Oracle 和 SQLite 都是这个规则。
"""),
  THINK("**（联系）** 同事说「同一个订单在报表里出现了两次」。你怎么先判断是不是重复加载，再决定保留哪一条？", r"""
先用 `GROUP BY 订单号, SKU HAVING COUNT(*) > 1` 确认是否有重复，再看这些行有没有不同的字段（数量、加载时间）。如果有加载时间，保留最新一条是常见做法，但一定要向数据负责人确认：有时最新一条是错的，要保留的是被审批过的那条。确认之前只查询，不删除。
"""),
  KW(("窗口函数","window function","每行保留，附加组内计算"),
     ("分区","PARTITION BY","把行分成若干组"),
     ("窗口排序","ORDER BY in OVER","组内的顺序"),
     ("行号","ROW_NUMBER","每行唯一编号"),
     ("排名","RANK","并列后跳号"),
     ("紧凑排名","DENSE_RANK","并列后不跳号"),
     ("累计","running total","截止当前行的合计"),
     ("上一行","LAG","取前一行的值"),
     ("下一行","LEAD","取后一行的值"),
     ("取最新一条","latest per group","ROW_NUMBER 加 rn = 1"),
     ("去重","deduplication","保留每组一条"),
     ("环比","period over period","和上一期对比"),
  ),
 ],
 "references": [
  SQLITE_DOC,
  {"title": "SQLite 官方文档：窗口函数", "url": "https://www.sqlite.org/windowfunctions.html", "note": "窗口函数的语法和内置函数列表"},
  {"title": "Wikipedia：Window function (SQL)", "url": "https://en.wikipedia.org/wiki/Window_function_(SQL)", "note": "窗口函数的概述"},
 ],
 "quiz": {"questions": [
  Q("两行金额并列第 3，`RANK()` 给下一行的排名是：",
    ["5", "4", "3", "6"], 0,
    "RANK 并列后跳号：1、2、3、3、5；DENSE_RANK 才是 1、2、3、3、4。"),
  Q("要取「每个客户最新的一张订单」，最合适的写法是：",
    ["ROW_NUMBER() OVER (PARTITION BY 客户 ORDER BY 日期 DESC)，外层筛 rn = 1", "GROUP BY 客户 再 SELECT 订单号", "ORDER BY 日期 LIMIT 1", "DISTINCT 客户"], 0,
    "按客户分区、按日期倒序编号，每组第 1 条就是最新的。"),
  Q("窗口函数和 GROUP BY 的主要区别是：",
    ["窗口函数不压缩行，每行都保留", "窗口函数只能用于文本", "窗口函数不能排序", "窗口函数会删除重复行"], 0,
    "GROUP BY 每组只留一行，窗口函数保留所有行并附加组内计算结果。"),
  Q("某客户的第一张订单，`LAG(amount)` 的结果是：",
    ["NULL", "0", "该订单自己的金额", "报错"], 0,
    "第一行前面没有上一行，LAG 返回 NULL（也可以用第二个参数指定默认值）。"),
  Q("为什么 `WHERE ROW_NUMBER() OVER (...) = 1` 会报错？",
    ["WHERE 先于 SELECT 执行，窗口函数结果还不存在", "ROW_NUMBER 不存在", "OVER 不能带括号", "= 1 不允许"], 0,
    "要把窗口函数放进子查询或 CTE，外层再用 WHERE 筛选。"),
 ]},
}
retarget(unit, [1, 0, 3, 2, 0])

if __name__ == '__main__':
    dump(unit, "sql-0", "u05-window.json", n_questions=5)
