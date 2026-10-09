"""sql-0 第 10 节：面试实战（下）进阶题"""
from sqllib import *

nb = Notebook()
C_DB = nb.cell(SETUP_DATA)
C_Q = nb.cell(SETUP_Q)

C_LOGIN = nb.cell('''
db.execute("CREATE TABLE logins(user_id TEXT, d TEXT)")
db.executemany("INSERT INTO logins VALUES (?,?)", [
    ("u1","2026-09-01"),("u1","2026-09-02"),("u1","2026-09-03"),("u1","2026-09-05"),
    ("u2","2026-09-01"),("u2","2026-09-03"),("u2","2026-09-04"),("u2","2026-09-05"),("u2","2026-09-06"),
    ("u3","2026-09-02")])
q("""WITH x AS (SELECT DISTINCT user_id, d FROM logins),
         g AS (SELECT user_id, d,
                      date(d, '-' || ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY d) || ' day') AS grp
               FROM x)
     SELECT user_id, MIN(d) AS start_d, MAX(d) AS end_d, COUNT(*) AS days
     FROM g GROUP BY user_id, grp HAVING COUNT(*) >= 3 ORDER BY user_id""")
''')

C_BOM = nb.cell('''
db.execute("CREATE TABLE bom(parent TEXT, child TEXT, qty INT)")
db.executemany("INSERT INTO bom VALUES (?,?,?)", [
    ("KIT-A","UNIT-A",1),("KIT-A","CUFF-A",1),("KIT-A","BATT",4),
    ("CUFF-A","FABRIC",2),("CUFF-A","TUBE",1)])
q("""WITH RECURSIVE tree(item, qty_per_kit, lvl) AS (
         SELECT 'KIT-A', 1, 0
         UNION ALL
         SELECT b.child, t.qty_per_kit * b.qty, t.lvl + 1
         FROM tree t JOIN bom b ON b.parent = t.item)
     SELECT item, qty_per_kit * 10 AS need_for_10_kits, lvl
     FROM tree WHERE item NOT IN (SELECT parent FROM bom) ORDER BY item""")
''')

C_CAL = nb.cell('''
db.execute("CREATE TABLE daily_sales(d TEXT, amt REAL)")
db.executemany("INSERT INTO daily_sales VALUES (?,?)", [
    ("2026-09-01",100),("2026-09-02",120),("2026-09-04",90),("2026-09-07",150)])
CAL = """WITH RECURSIVE cal(d) AS (
    SELECT '2026-09-01' UNION ALL SELECT date(d, '+1 day') FROM cal WHERE d < '2026-09-07')"""
print("没有销售记录的日期：")
q(CAL + " SELECT cal.d FROM cal LEFT JOIN daily_sales s ON s.d = cal.d WHERE s.d IS NULL")
''')

C_MA = nb.cell('''
q(CAL + """, f AS (SELECT cal.d, COALESCE(s.amt, 0) AS amt
                  FROM cal LEFT JOIN daily_sales s ON s.d = cal.d)
     SELECT d, amt,
            ROUND(AVG(amt) OVER (ORDER BY d ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS ma3
     FROM f ORDER BY d""")
''')

C_MED = nb.cell('''
OA = """WITH oa AS (
    SELECT o.order_id, SUM(ol.qty * ol.unit_price) AS amount
    FROM orders o JOIN order_lines ol ON ol.order_id = o.order_id
    GROUP BY o.order_id)"""
q(OA + """
  SELECT AVG(amount) AS median_amount FROM (
      SELECT amount, ROW_NUMBER() OVER (ORDER BY amount) AS rn, COUNT(*) OVER () AS n FROM oa)
  WHERE rn IN ((n + 1) / 2, (n + 2) / 2)""")
''')

C_FIFO = nb.cell('''
db.execute("CREATE TABLE supply(batch TEXT, qty INT)")
db.execute("CREATE TABLE demand(doc TEXT, qty INT)")
db.executemany("INSERT INTO supply VALUES (?,?)", [("B1",50),("B2",30),("B3",40)])
db.executemany("INSERT INTO demand VALUES (?,?)", [("D1",40),("D2",50),("D3",20)])
q("""WITH s AS (SELECT batch, SUM(qty) OVER (ORDER BY batch) - qty AS s_start,
                      SUM(qty) OVER (ORDER BY batch) AS s_end FROM supply),
         d AS (SELECT doc,   SUM(qty) OVER (ORDER BY doc) - qty AS d_start,
                      SUM(qty) OVER (ORDER BY doc) AS d_end FROM demand)
     SELECT d.doc, s.batch, MIN(s_end, d_end) - MAX(s_start, d_start) AS alloc_qty
     FROM d JOIN s ON s.s_start < d.d_end AND d.d_start < s.s_end
     ORDER BY d.doc, s.batch""")
''')

unit = {
 "id": "u10",
 "title": "SQL 面试实战（下）：连续登录、递归、补全日期、移动平均、中位数与先进先出",
 "en": "SQL Interview Practice II: Streaks, Recursion, Date Gaps, Moving Averages, Median & FIFO",
 "minutes": 50,
 "objectives": [
  "做出**连续登录 N 天（gaps and islands）**：用「日期减行号」把连续的日期变成同一个分组键",
  "用**递归 CTE**展开**物料清单 (BOM)**，并说出防止死循环的办法",
  "用**日历表**补全缺失的日期，再算**移动平均**，并区分「3 行」和「3 天」",
  "用窗口函数模拟**中位数**，并知道 Oracle 里直接用 `MEDIAN`",
  "用**累计区间重叠**做**先进先出 (FIFO) 分配**，把一批供应分配给多张需求",
  "面对**没见过的题**，说出自己的思考过程，而不是沉默",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

这一节的题比上一节难，**很多已经超出 BA 岗位通常要求的水平**，是高级数据分析、数据工程或技术咨询面试里才可能出现的。我选这些题的标准是：**要么是面试里反复出现的经典难题，要么贴近你的供应链背景**（物料清单展开、先进先出分配）。能全部做出来更好，做不出来也不意味着你不够格，重点是学会拆解的思路。

**说明：** 和上一节一样，这些题型来自我对常见面试题的整理，不是某家公司的真题；窗口函数和递归写法我在 SQLite 里运行验证过，Oracle 的写法按官方文档整理，没有在 Oracle 上逐条运行过。

""" + C_DB + r"""
""" + C_Q + r"""

**本节安排（约 50 分钟）**：导读（3 分钟）→ 六道题各约 7 分钟（42 分钟）→ 没见过的题怎么办与总结（5 分钟）。

### 第 1 题：连续登录至少 3 天（gaps and islands）

> **题目：** 找出连续登录至少 3 天的用户，并给出连续的起止日期。

**思路（这是整个类型的核心技巧）：** 把每个用户的登录日期按顺序编号 1、2、3……，再用「**日期减去编号**」。连续的日期会得到**同一个结果**，一旦断档，结果就变了。用这个结果当分组键，每一组就是一段连续的登录。

""" + C_LOGIN + r"""

**读输出：** u1 的 9 月 1、2、3 日连续 3 天；u2 的 9 月 3 日到 6 日连续 4 天（9 月 1 日单独一天，被 `HAVING` 筛掉了）；u3 只有一天，不满足。**为什么先 `DISTINCT`：** 同一天登录多次会让编号错位，先去重是这类题的必要步骤，也是常见追问。**Oracle：** 日期和数字可以直接相减，写成 `d - ROW_NUMBER() OVER (...)`，不需要 `date(…)` 函数。**变形：** 「连续缺货的天数」「连续达标的月份」「连续 3 次订单失败」都是同一个套路。

### 第 2 题：递归展开物料清单 (BOM)

> **题目：** 一套 KIT-A 由 UNIT-A、CUFF-A 和 4 个 BATT 组成，CUFF-A 又由 2 个 FABRIC 和 1 个 TUBE 组成。做 10 套 KIT-A，每种最底层的零件各需要多少？

**思路：** 这是树形结构，层数不固定，要用**递归 CTE**：先写起点（KIT-A，数量 1），再写「从上一层的结果，连到下一层」，数量逐层相乘。

""" + C_BOM + r"""

**读输出：** 底层零件（不再作为父件的）：BATT 需要 40，FABRIC 20，TUBE 10，UNIT-A 10。CUFF-A 是中间件，所以被 `WHERE item NOT IN (SELECT parent …)` 过滤掉了（这里 `parent` 列没有 NULL，所以 NOT IN 是安全的；第 4 节讲过它的陷阱）。**追问：如果数据里有循环引用（A 包含 B，B 又包含 A）会怎样？** 递归会无限进行。办法：加层数上限（`WHERE lvl < 10`）、记录已走过的路径、或在 Oracle 里用 `CYCLE` 子句。**Oracle：** 递归 `WITH` **不写 `RECURSIVE` 这个关键字**，列名写在 `WITH tree(item, qty_per_kit, lvl) AS (…)` 里；Oracle 还有传统的 `START WITH … CONNECT BY PRIOR …` 写法，在老代码里很常见。你可能在 JDE 或其他 ERP 里遇到物料清单，所以这一题值得熟悉。

### 第 3 题：补全缺失的日期

> **题目：** 9 月 1 日到 7 日里，哪几天没有任何销售记录？

**思路：** 缺失的日期在销售表里根本不存在，没法直接查出来。解决办法是**先造一张完整的日历**，再 `LEFT JOIN` 销售表，找右边是 NULL 的日子。

""" + C_CAL + r"""

**读输出：** 销售表里有 1、2、4、7 日，所以 3、5、6 日是缺失的。日历用递归 CTE 生成，每次加一天，直到 9 月 7 日。**Oracle：** 可以用 `SELECT DATE '2026-09-01' + LEVEL - 1 FROM DUAL CONNECT BY LEVEL <= 7` 生成日历。**这个技巧是很多题的基础**，比如下面的移动平均。

### 第 4 题：移动平均，并区分「3 行」和「3 天」

> **题目：** 计算每天的 3 日移动平均销售额，缺失的日期销售额按 0 算。

""" + C_MA + r"""

**读输出：** 先用日历补全日期，缺失日销售额记 0，再用 `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` 取「本行和前面 2 行」求平均。前两行因为前面不够 2 行，所以是用已有的行平均（第一天 100，第二天 110）。**关键区别：** 窗口框架算的是**行数**，不是天数。**如果没有先补全日期**，缺失的日子没有行，「前 2 行」就会跨过缺口，实际覆盖的天数不止 3 天，算出来的就不是真正的「3 日」平均。这是面试里很容易被抓住的错误。**追问：** `ROWS` 和 `RANGE` 的区别？`ROWS` 按物理行数，`RANGE` 按排序列的值（并列的值被一起算）。

### 第 5 题：中位数

> **题目：** 订单金额的中位数是多少？

""" + C_MED + r"""

**读输出：** 9 张订单金额从小到大排列，第 5 个就是中位数，800。写法：给每行编号，并数出总行数 n；如果 n 是奇数，`(n+1)/2` 和 `(n+2)/2`（整数除法）是同一个位置；如果 n 是偶数，就是中间两个位置，对这两个值取平均。**Oracle：** 直接有 `MEDIAN(amount)` 函数，也可以用 `PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY amount)`。**追问：为什么业务上常用中位数而不是平均值？** 因为中位数不受极端值影响，比如订单金额里有一两张特别大的单，平均值会被拉高。

### 第 6 题：先进先出 (FIFO) 分配

> **题目：** 三个批次的库存（B1 50、B2 30、B3 40）按顺序分配给三张需求（D1 40、D2 50、D3 20），每张需求分别从哪些批次拿多少？

**思路：** 把库存和需求各自排成一条**数轴**：库存批次占的区间是 [0,50)、[50,80)、[80,120)，需求占的区间是 [0,40)、[40,90)、[90,110)。**每一对需求和批次的「区间重叠长度」，就是这个批次分给这张需求的数量。** 区间起点用「累计和减本行数量」，终点用「累计和」，重叠长度 = 两个终点的较小值 减 两个起点的较大值。

""" + C_FIFO + r"""

**读输出：** D1 需要 40，全部来自 B1；D2 需要 50，先拿 B1 剩下的 10，再拿 B2 的 30，不够再拿 B3 的 10；D3 需要 20，来自 B3。总需求 110 小于总库存 120，所以都满足了。`JOIN` 的条件 `s_start < d_end AND d_start < s_end` 是「两个区间有重叠」的标准写法。**Oracle：** 求较小值和较大值用 `LEAST` 和 `GREATEST`，不是 `MIN` / `MAX`（后两个在 Oracle 里只能做聚合）。**这类题把供应链业务和 SQL 结合，如果面试官看到你的背景，这是一个很好的「我真的懂业务」的展示机会。** 如果需求大于总库存，最后一张需求会拿不满，答案里自然只显示能分配的部分。

### 遇到没见过的题怎么办

别沉默，把思考过程说出来：

1. **复述题目并确认口径**：「我理解为……，对吗？」
2. **拿小例子手算**：「如果数据是这 5 行，期望结果是……」
3. **说出你认识的相近题型**：「这有点像连续登录那类问题，核心是找分组键」。
4. **先给一个笨办法**：「最直接的是用自连接，但数据量大会慢，我再想想怎么用窗口函数」。
5. **主动讲边界和验证方法**。

**面试官评价的是你的思考过程和沟通，而不仅是最后的代码。** 写不出来时，说「我卡在这里，我的想法是……」比沉默强得多。

### 这一节你要带走的三句话

1. **「日期减行号」把连续的日期变成同一个分组键（gaps and islands）；先补全日历再做移动平均，否则「3 行」不等于「3 天」。**
2. **树形结构用递归 CTE（Oracle 里不写 RECURSIVE，或用 CONNECT BY），要想到循环引用；中位数在 Oracle 里直接用 MEDIAN。**
3. **先进先出分配 = 供应和需求各排成数轴，区间重叠长度就是分配量；没见过的题，把思考过程说出来。**
"""),
  THINK("**（实践）** 把第 1 题改成：找出每个用户**最长**的连续登录天数。提示：在分组结果上再做一次聚合。", r"""
把第 1 题里的 `HAVING COUNT(*) >= 3` 去掉，作为子查询，外层 `SELECT user_id, MAX(days) AS longest FROM (…) GROUP BY user_id`。结果 u1 是 3，u2 是 4，u3 是 1。这说明「先分组、再对分组结果聚合」是处理连续问题的通用结构。
"""),
  THINK("**（概念辨析）** 为什么没有先补全日期就算 3 日移动平均是错的？举个例子。", r"""
窗口框架 `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` 数的是行，不是日历上的天。如果 9 月 3 日没有数据，9 月 4 日这行的「前 2 行」就是 9 月 2 日和 9 月 1 日，覆盖了 4 天，却当成 3 天来平均。先用日历补全并把缺失日记成 0（或按业务决定是否记 0），每一行才对应一天。
"""),
  THINK("**（联系）** 某个零件在 BOM 里被多个父件共用，直接展开会重复出现很多次。如果要算「每种底层零件的总需求」，怎么改第 2 题？", r"""
在递归结果的外层对底层零件做 `GROUP BY item` 再 `SUM(qty_per_kit * 数量)`。例如 FABRIC 同时用在 CUFF-A 和另一个组件里，就把两条路径的需求加起来。要注意不同路径下的零件是否真的是同一个物料号。这是做物料需求计划 (MRP) 的核心计算，你在 OMRON 的供应链背景是很好的讲点。
"""),
  KW(("连续问题","gaps and islands","找连续的一段"),
     ("分组键","grouping key","用日期减行号得到"),
     ("递归 CTE","recursive CTE","自己引用自己"),
     ("物料清单","BOM","产品由哪些零件组成"),
     ("层次查询","hierarchical query","Oracle 的 CONNECT BY"),
     ("日历表","calendar table","完整的日期序列"),
     ("移动平均","moving average","滑动窗口内的平均"),
     ("窗口框架","window frame","ROWS / RANGE 指定的范围"),
     ("中位数","median","排在中间的值"),
     ("先进先出","FIFO","先入库的先出库"),
     ("区间重叠","interval overlap","两段的重叠长度"),
     ("最小 / 最大值函数","LEAST / GREATEST","Oracle 里取多个值的较小或较大者"),
  ),
 ],
 "references": [
  SQLITE_DOC,
  {"title": "SQLite 官方文档：WITH 子句（含递归）", "url": "https://www.sqlite.org/lang_with.html", "note": "递归 CTE 的语法和例子"},
  ORACLE_SQL_REF,
  {"title": "Wikipedia：Bill of materials", "url": "https://en.wikipedia.org/wiki/Bill_of_materials", "note": "物料清单的概念"},
 ],
 "quiz": {"questions": [
  Q("连续日期问题里，「日期减去按日期排序的行号」得到的值：",
    ["在连续的日期上是同一个值，断档后会变化", "总是不同", "总是 0", "只对周末有效"], 0,
    "连续日期每天加 1，行号也每行加 1，两者的差保持不变；断档后差值会变。"),
  Q("没有先补全日期，直接用 `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` 算「3 日」移动平均，问题是：",
    ["缺失的日期没有行，窗口会跨过缺口，覆盖的天数超过 3 天", "会报错", "结果永远是 0", "只能算周平均"], 0,
    "ROWS 按行数计算，不是按日历天数，缺口会让窗口实际覆盖更多天。"),
  Q("在 Oracle 里写递归 CTE，下面哪项正确？",
    ["WITH 后面不写 RECURSIVE 关键字，列名写在 CTE 名后面", "必须写 WITH RECURSIVE", "不支持递归，只能用存储过程", "只能用 UNION 不能用 UNION ALL"], 0,
    "Oracle 的递归 WITH 不使用 RECURSIVE 关键字；也可以用传统的 CONNECT BY。"),
  Q("先进先出分配中，用「区间重叠」计算某批次分给某需求的数量，公式是：",
    ["两个终点的较小值 减 两个起点的较大值（重叠为正才有分配）", "两个起点相加", "两个终点相乘", "供应量除以需求量"], 0,
    "重叠长度 = min(终点) − max(起点)；Oracle 里较小值用 LEAST，较大值用 GREATEST。"),
  Q("面试时遇到没见过的 SQL 题，最推荐的做法是：",
    ["复述并确认口径，拿小例子手算，说出思路再逐步写，并讲边界", "保持沉默直到想出完整答案", "直接说不会", "随便写一条查询"], 0,
    "面试官重视思考过程和沟通；说出卡在哪里和你的想法，比沉默强得多。"),
 ]},
}
retarget(unit, [3, 0, 2, 1, 3])

if __name__ == '__main__':
    dump(unit, "sql-0", "u10-interview-2.json", n_questions=5)
