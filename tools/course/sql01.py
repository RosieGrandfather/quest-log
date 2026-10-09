"""sql-0 第 1 节：SELECT 基础与 NULL"""
from sqllib import *

nb = Notebook()
C_DB = nb.cell(SETUP_DATA)
C_Q = nb.cell(SETUP_Q)

C_SEL = nb.cell('''
q("""SELECT order_id, cust_id, order_date
     FROM orders
     WHERE status = 'OPEN'
     ORDER BY order_date DESC""")
q("SELECT order_id, order_date FROM orders ORDER BY order_date DESC LIMIT 2")
''')

C_NULL = nb.cell('''
q("SELECT name, country FROM customers WHERE country <> 'SG'")
q("SELECT name FROM customers WHERE country IS NULL")
q("SELECT NULL = NULL AS eq, NULL IS NULL AS is_null")
q("SELECT COUNT(*) AS total_rows, COUNT(country) AS with_country FROM customers")
''')

C_FILTER = nb.cell('''
q("SELECT sku, name FROM products WHERE sku LIKE 'BP%'")
q("""SELECT order_id, order_date, status FROM orders
     WHERE order_date BETWEEN '2026-09-03' AND '2026-09-15'
       AND status IN ('OPEN', 'SHIPPED')""")
q("SELECT DISTINCT stock_status FROM inventory ORDER BY stock_status")
''')

C_CASE = nb.cell('''
q("""SELECT order_id, line_no, qty * unit_price AS amount,
            CASE WHEN qty * unit_price >= 800 THEN 'big'
                 WHEN qty * unit_price >= 400 THEN 'mid'
                 ELSE 'small' END AS size
     FROM order_lines
     WHERE order_id IN (101, 104, 105)
     ORDER BY order_id, line_no""")
''')

unit = {
 "id": "u01",
 "title": "读懂一张表：SELECT、WHERE、排序与 NULL",
 "en": "Reading a Table: SELECT, WHERE, Sorting & NULL",
 "minutes": 40,
 "objectives": [
  "说出一条查询**从哪里取数、怎么筛选、怎么排序**，并知道 SQL 的**逻辑执行顺序**",
  "熟练使用 **WHERE、AND / OR、IN、BETWEEN、LIKE、DISTINCT、ORDER BY、LIMIT**",
  "理解 **NULL（空值）** 的三值逻辑：为什么 `= NULL` 查不到东西、为什么 `<>` 会漏掉空值行",
  "用 **CASE WHEN** 和**别名**生成新的列",
  "把同事一句口头需求，翻译成一条查询之前要问清的几个问题",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

整门课用同一个练习数据库：一家卖血压计、体温计的小公司，有**客户、产品、订单、订单明细、库存**五张表，都是自己编的演示数据。你要练的不是背语法，而是培养一个习惯：**看到一个业务问题，能想到「该查哪几张表、怎么筛、结果该是什么样」，并能验证结果对不对。**

浏览器里的 SQL 是 **SQLite**，和 Oracle 大部分基础语法一样，少数写法不同（如日期函数、取前几行），第 8 节专门对照。每一节开头会重新建库：

""" + C_DB + r"""

再放一个小工具函数 `q()`：传一条 SQL，打印结果表。后面所有查询都用它：

""" + C_Q + r"""

**本节安排（约 40 分钟）**：导读（2 分钟）→ SELECT 与执行顺序（10 分钟）→ NULL（12 分钟）→ 常用筛选（8 分钟）→ CASE（4 分钟）→ 对照工作与总结（4 分钟）。

### 一条查询的骨架

> **标准定义 · 查询 (query)**
>
> `SELECT` 指定要看的**列**；`FROM` 指定数据来自哪张**表**；`WHERE` 筛选**行**；`ORDER BY` 排序；`LIMIT`（Oracle 里是 `FETCH FIRST n ROWS ONLY`）限制返回的行数。
>
> *English: SELECT picks columns, FROM names the table, WHERE filters rows, ORDER BY sorts, LIMIT caps the number of rows returned.*

**白话版：「从哪张表，挑哪几行，看哪几列，怎么排」。**

""" + C_SEL + r"""

**读输出：** 第一条查出 3 张 OPEN 订单，按日期从新到旧排（109、106、103）。第二条不筛选，只取日期最新的 2 张订单。

**逻辑执行顺序**（写的顺序和执行的顺序不一样）：`FROM` → `WHERE` → `GROUP BY` → `HAVING` → `SELECT` → `ORDER BY` → `LIMIT`。这解释了很多「为什么报错」：比如 **WHERE 里不能直接用 SELECT 里起的别名**（Oracle 会报错，因为执行 WHERE 时别名还没产生；SQLite 比较宽松会放行，但别养成依赖它的习惯）。

### NULL：最容易出错的地方

> **标准定义 · 空值 (NULL)**
>
> NULL 表示**未知或不存在**，不是 0，也不是空字符串。任何值和 NULL 做比较（`=`、`<>`、`>`）结果都是**未知 (UNKNOWN)**，`WHERE` 只保留结果为**真**的行，所以这些行都会被筛掉。判断空值只能用 `IS NULL` / `IS NOT NULL`。
>
> *English: NULL means unknown or missing. Any comparison with NULL yields UNKNOWN, and WHERE keeps only rows that evaluate to TRUE; use IS NULL / IS NOT NULL.*

**白话版：「NULL 是『不知道』，不知道和任何东西比，答案都是『不知道』，不是『对』。」**

""" + C_NULL + r"""

**读输出：**

- `country <> 'SG'` 只返回 2 行（MY 的两个客户），`Foxtrot Store`（国家是 NULL）**悄悄消失了**：因为 `NULL <> 'SG'` 是未知，不是真。想要「不是 SG 的，包括没填的」要写 `country <> 'SG' OR country IS NULL`。
- `NULL = NULL` 的结果是 NULL（显示为 `NULL`），而 `NULL IS NULL` 是 1（真）。
- `COUNT(*)` 数所有行（6），`COUNT(country)` 只数**不是 NULL** 的行（5）。第 2 节会再用到。

**排查时的第一反应：** 数据对不上，先想「是不是有 NULL」。**Oracle 额外的坑**：Oracle 把**空字符串 `''` 当成 NULL**，SQLite 和多数数据库不是。

### 常用筛选：IN、BETWEEN、LIKE、DISTINCT

""" + C_FILTER + r"""

**读输出：**

- `LIKE 'BP%'`：`%` 代表任意多个字符，查出 BP100、BP200 两个产品。`_` 代表恰好一个字符。
- `BETWEEN '2026-09-03' AND '2026-09-15'` **包含两端**，所以 09-03 和 09-15 的订单都在；再加 `status IN ('OPEN','SHIPPED')` 去掉 CANCELLED，剩 4 张（102、103、104、106）。**注意：** 这里日期是文本 `YYYY-MM-DD`，字母顺序刚好等于时间顺序；Oracle 里日期是真正的日期类型，要用 `DATE '2026-09-03'` 或 `TO_DATE`，第 8 节讲。
- `DISTINCT` 去掉重复，库存状态只有 AVAIL 和 QUAR（隔离）两种。

### 用 CASE 生成新列

""" + C_CASE + r"""

**读输出：** 先算出每行金额 `qty * unit_price`，再用 `CASE WHEN` 按金额分档：900 元那行是 `big`，350 元是 `small`，其余 `mid`。`AS amount`、`AS size` 是**别名**，只是给结果列起的名字。`CASE` 按顺序判断，**第一个成立的分支生效**，所以大的条件要放前面。

### 对照你的工作：口头需求变成查询

同事说：「帮我拉一下马来西亚客户的未完成订单。」**写 SQL 之前要问清：**

| 要问清 | 为什么 |
|---|---|
| 「马来西亚客户」是客户主数据里的国家，还是收货地址的国家？ | 两张表的字段可能对不上 |
| 「未完成」包括哪些状态？OPEN 和 CANCELLED 算不算？ | 同一个词不同人理解不同 |
| 要哪些列？多久范围？排序？ | 避免对方拿到后又来要第二遍 |
| 客户国家为空的算不算？ | 就是上面的 NULL 陷阱 |

这就是第 9 节 BA 课里「把需求问清」在 SQL 上的样子。

### 这一节你要带走的三句话

1. **查询骨架是 SELECT 挑列、FROM 选表、WHERE 筛行、ORDER BY 排序；逻辑执行顺序是 FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY。**
2. **NULL 是「不知道」：比较只能用 IS NULL；`<>` 和 `NOT IN` 会漏掉 NULL 行；COUNT(列) 不数 NULL；Oracle 把空字符串当 NULL。**
3. **动手之前先问清口径：哪张表、什么状态、什么范围、空值怎么算。**
"""),
  THINK("**（实践）** 写一条查询：列出订单明细中 `qty >= 10` 的行，显示订单号、SKU、数量，按数量从大到小排序。再改一下，只要前 3 行。", r"""
参考：`SELECT order_id, sku, qty FROM order_lines WHERE qty >= 10 ORDER BY qty DESC LIMIT 3`。前 3 行是数量 100、50、30 的明细。注意 `ORDER BY ... DESC` 是从大到小，不写默认从小到大（ASC）。Oracle 里把 `LIMIT 3` 换成 `FETCH FIRST 3 ROWS ONLY`。
"""),
  THINK("**（概念辨析）** 为什么 `WHERE country = NULL` 一行都查不出来？应该怎么写？", r"""
因为任何值和 NULL 做 `=` 比较的结果都是未知，不是真，WHERE 只保留真，所以一行都不返回，也**不会报错**，这让它特别隐蔽。要写 `WHERE country IS NULL`。
"""),
  THINK("**（联系）** 同事说「SG 以外的客户」，你用 `country <> 'SG'` 查出 2 个客户。你怎么确认有没有漏掉？", r"""
先查有没有 NULL：`SELECT COUNT(*), COUNT(country) FROM customers`，两个数不同说明有空值；再问同事国家为空的客户算不算。漏掉的是 Foxtrot Store。**核对总数**（SG 的 + 非 SG 的 + 空的 = 全部）是最简单的验证办法。
"""),
  KW(("查询","query","向数据库提问的一条 SQL"),
     ("表 / 行 / 列","table / row / column","数据的基本结构"),
     ("筛选","WHERE","只保留满足条件的行"),
     ("排序","ORDER BY","按某列升序或降序"),
     ("去重","DISTINCT","去掉重复的结果行"),
     ("模糊匹配","LIKE","用 % 和 _ 匹配文本模式"),
     ("别名","alias","给列或表起的临时名字"),
     ("空值","NULL","未知或不存在，不等于 0 或空字符串"),
     ("三值逻辑","three-valued logic","真、假、未知"),
     ("条件表达式","CASE WHEN","按条件分支生成值"),
     ("逻辑执行顺序","logical processing order","FROM 到 ORDER BY 的真实顺序"),
     ("限制行数","LIMIT / FETCH FIRST","只返回前几行"),
  ),
 ],
 "references": [
  SQLITE_DOC,
  {"title": "Wikipedia：SQL", "url": "https://en.wikipedia.org/wiki/SQL", "note": "SQL 语言的概述和历史"},
  {"title": "Wikipedia：Null (SQL)", "url": "https://en.wikipedia.org/wiki/Null_(SQL)", "note": "NULL 与三值逻辑的详细说明"},
 ],
 "quiz": {"questions": [
  Q("客户表有一行 country 是 NULL。执行 `WHERE country <> 'SG'`，这一行会：",
    ["不出现在结果里", "出现在结果里", "导致报错", "被自动改成 SG"], 0,
    "NULL 和任何值比较的结果都是未知，WHERE 只保留真，所以这行被筛掉了。"),
  Q("表里有 6 行，其中 5 行 country 非空。`COUNT(country)` 的结果是：",
    ["5", "6", "1", "0"], 0,
    "COUNT(列) 只统计该列不是 NULL 的行；COUNT(*) 才统计所有行。"),
  Q("下面哪个子句在逻辑上**最先**执行？",
    ["FROM", "SELECT", "ORDER BY", "WHERE 之后的 LIMIT"], 0,
    "逻辑顺序是 FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT。"),
  Q("`order_date BETWEEN '2026-09-03' AND '2026-09-15'` 的范围是：",
    ["包含两端的日期", "不包含两端的日期", "只包含起始日期", "只包含结束日期"], 0,
    "BETWEEN 是闭区间，两端都包含。"),
  Q("在 Oracle 里，WHERE 子句通常不能直接使用 SELECT 里定义的别名，原因是：",
    ["WHERE 在逻辑上先于 SELECT 执行，别名还没产生", "别名只能用中文", "别名必须大写", "WHERE 不支持任何计算"], 0,
    "执行 WHERE 时 SELECT 还没执行，所以别名不存在。可以把计算写在 WHERE 里，或用子查询。"),
 ]},
}
retarget(unit, [1, 0, 2, 3, 1])

if __name__ == '__main__':
    dump(unit, "sql-0", "u01-select-null.json", n_questions=5)
