"""sql-0 第 9 节：面试实战（上）经典题"""
from sqllib import *

nb = Notebook()
C_DB = nb.cell(SETUP_DATA)
C_Q = nb.cell(SETUP_Q)

C_OA = nb.cell('''
OA = """WITH oa AS (
    SELECT o.order_id, o.cust_id, o.order_date, SUM(ol.qty * ol.unit_price) AS amount
    FROM orders o JOIN order_lines ol ON ol.order_id = o.order_id
    GROUP BY o.order_id)"""
def nth_highest(n):
    q(OA + f"""
      SELECT MAX(amount) AS nth_highest FROM (
          SELECT amount, DENSE_RANK() OVER (ORDER BY amount DESC) AS r FROM oa) WHERE r = {n}""")
nth_highest(2)
nth_highest(10)
''')

C_TOPN = nb.cell('''
q("""SELECT category, sku, total_qty FROM (
         SELECT p.category, p.sku, SUM(ol.qty) AS total_qty,
                ROW_NUMBER() OVER (PARTITION BY p.category ORDER BY SUM(ol.qty) DESC) AS rn
         FROM order_lines ol JOIN products p ON p.sku = ol.sku
         GROUP BY p.category, p.sku)
     WHERE rn <= 2 ORDER BY category, rn""")
''')

C_BOTH = nb.cell('''
def bought_both(extra=""):
    q(f"""SELECT c.cust_id, c.name
          FROM orders o
          JOIN customers c    ON c.cust_id = o.cust_id
          JOIN order_lines ol ON ol.order_id = o.order_id
          WHERE ol.sku IN ('BP100', 'TH10') {extra}
          GROUP BY c.cust_id, c.name
          HAVING COUNT(DISTINCT ol.sku) = 2""")
print("含已取消订单：")
bought_both()
print("不含已取消订单：")
bought_both("AND o.status <> 'CANCELLED'")
''')

C_PARETO = nb.cell('''
q("""WITH r AS (SELECT sku, SUM(qty * unit_price) AS rev FROM order_lines GROUP BY sku),
     c AS (SELECT sku, rev,
                  SUM(rev) OVER (ORDER BY rev DESC ROWS UNBOUNDED PRECEDING) AS cum_rev,
                  SUM(rev) OVER () AS total_rev
           FROM r)
     SELECT sku, rev, ROUND(100.0 * cum_rev / total_rev, 1) AS cum_pct,
            CASE WHEN (cum_rev - rev) * 1.0 / total_rev < 0.8 THEN 'A' ELSE 'B' END AS cls
     FROM c ORDER BY rev DESC""")
''')

C_RATE = nb.cell('''
q("""SELECT COALESCE(c.country, '(unknown)') AS country,
            COUNT(*) AS n_orders,
            ROUND(100.0 * AVG(CASE WHEN o.status = 'CANCELLED' THEN 1.0 ELSE 0 END), 1) AS cancel_pct
     FROM orders o LEFT JOIN customers c ON c.cust_id = o.cust_id
     GROUP BY COALESCE(c.country, '(unknown)')
     ORDER BY country""")
''')

C_GAP = nb.cell('''
q("""SELECT cust_id, order_id, order_date, gap_days FROM (
         SELECT cust_id, order_id, order_date,
                CAST(julianday(order_date) - julianday(
                     LAG(order_date) OVER (PARTITION BY cust_id ORDER BY order_date)) AS INT) AS gap_days
         FROM orders)
     WHERE gap_days > 7""")
''')

C_DEL = nb.cell('''
db.execute("CREATE TABLE stg(order_id INT, sku TEXT, qty INT)")
db.executemany("INSERT INTO stg VALUES (?,?,?)", [(101,"BP100",10),(101,"BP100",10),(102,"BP200",20),(102,"BP200",20),(102,"BP200",20)])
cur = db.execute("""DELETE FROM stg WHERE rowid NOT IN (
                        SELECT MIN(rowid) FROM stg GROUP BY order_id, sku)""")
print("删除行数:", cur.rowcount)
q("SELECT * FROM stg ORDER BY order_id")
db.rollback()
''')

unit = {
 "id": "u09",
 "title": "SQL 面试实战（上）：七道常考题的解法、追问与边界",
 "en": "SQL Interview Practice I: Seven Classic Questions, Follow-ups & Edge Cases",
 "minutes": 50,
 "objectives": [
  "掌握面试答题的固定流程：**问清口径 → 举例子 → 选工具 → 写 → 查边界 → 讲复杂度和优化**",
  "做出七类经典题：**第 N 高、每组前 N 名、同时满足多个条件的人、帕累托 80/20、比率、相邻记录的间隔、保留一条的去重**",
  "对每道题能说出**至少一种别的写法**和**一个会让答案出错的边界**（并列、NULL、空表、取消的订单）",
  "知道每道题在 **Oracle 里要怎么改**",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

SQL 面试几乎都是在白板、共享文档或在线编辑器里**现场写查询**，题目往往短，但**追问很多**。面试官想看的不只是你会不会写，而是：你**问不问口径、会不会举例子验证、能不能想到边界、能不能解释为什么这样写**。这一节用同一个演示库做七道常考题。我说明一下：这些题型是 SQL 面试里的常见类型（来自我对常见面试题的整理，不是某家公司的真题，也没有查到新加坡公司具体考什么）；有的比基础题难，超出前面的内容也是有意的。

""" + C_DB + r"""
""" + C_Q + r"""

**本节安排（约 50 分钟）**：导读与答题流程（5 分钟）→ 七道题各约 6 分钟（42 分钟）→ 总结（3 分钟）。**建议做法：每道题先看题目，自己在练习里写一遍，再看我的解法。**

### 答题流程：六步

1. **问清口径**：「取消的订单算不算？并列怎么处理？没有数据时返回什么？」（这一步本身就是加分项。）
2. **举个小例子**：用 3 到 5 行数据手算期望结果，说给面试官听。
3. **选工具**：这是「分组汇总」「排名」「连接」「窗口」「集合」里的哪一类？
4. **边写边说**：先写骨架，再补细节，别一次写完才解释。
5. **查边界**：NULL、重复、并列、空表、边界值（`>` 还是 `>=`）。
6. **讲优化和替代**：可能的索引、有没有别的写法。

### 第 1 题：第 N 高的值

> **题目：** 订单金额第 2 高是多少？如果没有第 2 高，返回 NULL。

**追问：** 金额并列怎么办？N 是参数怎么办？

""" + C_OA + r"""

**读输出：** 先用 `DENSE_RANK` 给金额排名（并列不跳号），再取排名为 N 的值。第 2 高是 1000（订单 101）。**为什么外面套 `MAX`：** 子查询没有匹配行时返回的是「零行」，而面试要求返回 NULL；聚合函数在零行时返回 NULL，这是个小技巧（第 10 高就返回了 `NULL`）。**为什么用 `DENSE_RANK`：** 如果用 `RANK`，两个并列第 3 之后就没有「第 4」了；如果用 `ROW_NUMBER`，并列的值会被当成不同名次。**别的写法：** `SELECT DISTINCT amount FROM oa ORDER BY amount DESC LIMIT 1 OFFSET 1`（Oracle 用 `OFFSET 1 ROWS FETCH NEXT 1 ROWS ONLY`），但没有结果时返回零行而不是 NULL。

### 第 2 题：每组前 N 名

> **题目：** 每个产品类别里销量最高的 2 个 SKU。

""" + C_TOPN + r"""

**读输出：** 按类别分区，按销量倒序编号，取编号 <= 2。BP 类别两个都在（BP200 为 35，BP100 为 34），其他类别只有一个 SKU 有销量。**追问：并列怎么办？** `ROW_NUMBER` 会在并列时随便选一个，如果要保留所有并列的，改用 `RANK` 或 `DENSE_RANK` 并筛 `<= 2`。**边界：** 没有销量的 SKU（OLD9）不会出现，因为我们用的是 `JOIN`；如果题目要求「没有销量的也要显示」，要改成从产品表出发的 `LEFT JOIN`。

### 第 3 题：同时买过 A 和 B 的客户

> **题目：** 找出同时买过 BP100 和 TH10 的客户。

""" + C_BOTH + r"""

**读输出：** 做法是先筛出只含这两个 SKU 的行，按客户分组，用 `HAVING COUNT(DISTINCT sku) = 2` 保证两个都买过。**这道题的重点在口径：** 含已取消订单时有 Alpha 和 Gamma 两个客户；不含已取消订单时只剩 Alpha，因为 Gamma 的 TH10 在被取消的 105 号订单里。面试官问「取消的算不算」才是答对的关键。**别的写法：** 用 `INTERSECT`（两个 SKU 各查一次客户，再求交集），或者 `EXISTS` 写两次。

### 第 4 题：帕累托（80/20）分析

> **题目：** 按销售额从高到低列出 SKU，算出累计占比，并把累计占比达到 80% 之前的 SKU 标为 A 类。

""" + C_PARETO + r"""

**读输出：** `SUM(rev) OVER (ORDER BY rev DESC ROWS UNBOUNDED PRECEDING)` 得到累计销售额，除以总额得到累计占比。BP100 的累计 28.7%，TH10 累计 53.6%，BP200 累计 75.2%，NB50 累计 91.1%。**A 类的判断用的是「这一行之前的累计占比」**（`cum_rev - rev`）：NB50 开始前累计才 75.2%，没到 80%，所以 NB50 也算 A；如果用「含本行的累计占比」判断，NB50（91.1%）就被排除，会少一个。**这个边界是常见追问**，答案没有对错，要和面试官确认「A 类是包含跨过 80% 的那一个，还是不包含」。这类库存分类（ABC 分析）在供应链里很常用。

### 第 5 题：比率和百分比

> **题目：** 每个国家的订单取消率。

""" + C_RATE + r"""

**读输出：** `AVG(CASE WHEN … THEN 1.0 ELSE 0 END)` 是算比例的万能写法：满足条件记 1，否则记 0，平均数就是占比。MY 有 3 张订单、1 张取消，33.3%；SG 5 张，0%；订单 109 的客户不存在，国家是 NULL，用 `COALESCE` 单独标为 `(unknown)`。**边界：** `1.0` 不能写成 `1`，否则在有些数据库里整数相除会得到 0（SQLite 里 `1/3` 也是 0）；**分母为 0** 时要避免除零。

### 第 6 题：相邻记录的间隔

> **题目：** 找出同一个客户相邻两次下单间隔超过 7 天的订单。

""" + C_GAP + r"""

**读输出：** `LAG` 取同一客户上一张订单的日期，两个日期相减得到间隔天数。只有客户 2 的 108 号订单满足（9 月 3 日到 9 月 22 日，相隔 19 天）。**注意客户 3 的两张订单（9 月 5 日和 12 日）刚好相隔 7 天，因为题目是「超过 7 天」所以不算，如果改成 `>= 7` 就会包含它**，这正是面试官爱问的边界。**Oracle：** 日期直接相减就是天数，不需要 `julianday`：`order_date - LAG(order_date) OVER (...)`（日期类型的前提下）。

### 第 7 题：删除重复，只保留一条

> **题目：** 临时表里同一个订单和 SKU 有重复行，写出只保留一条的删除语句。

""" + C_DEL + r"""

**读输出：** 按业务键（订单号加 SKU）分组，每组只留 `MIN(rowid)` 那一条，其余删掉，共删除 3 行（5 行变 2 行）。最后 `rollback()` 撤销。**Oracle 对应：** `ROWID` 是行的物理地址，写法几乎一样：`DELETE FROM stg WHERE ROWID NOT IN (SELECT MIN(ROWID) FROM stg GROUP BY order_id, sku)`。**追问：** 如果这是生产表怎么办？答：先备份或在事务里，先用 `SELECT` 确认要删的行，让有权限的人执行；还要问「保留哪条才对」。

### 这一节你要带走的三句话

1. **答题流程：问口径、举例子、选工具、边写边说、查边界、讲替代和优化；很多题的「陷阱」其实是口径（取消的算不算、并列怎么办、> 还是 >=）。**
2. **常考题型对应的工具：第 N 高用 DENSE_RANK，每组前 N 用 ROW_NUMBER，「同时买过」用 HAVING COUNT(DISTINCT)，占比用 AVG(CASE)，相邻记录用 LAG，去重用 ROWID 或 ROW_NUMBER。**
3. **每道题都准备一个替代写法和一个会让答案出错的边界，面试官追问时就不会慌。**
"""),
  THINK("**（实践）** 不看解法，写出：「每个客户最近一张订单的金额」。再写出：「每个客户金额最高的订单」。两题的窗口函数有什么区别？", r"""
最近一张：`ROW_NUMBER() OVER (PARTITION BY cust_id ORDER BY order_date DESC)` 取 1；金额最高：`ROW_NUMBER() OVER (PARTITION BY cust_id ORDER BY amount DESC)` 取 1。区别只有 `ORDER BY` 的列。如果日期或金额并列要保留所有并列，就把 `ROW_NUMBER` 换成 `RANK`。
"""),
  THINK("**（概念辨析）** 为什么算比例时要写 `1.0` 而不是 `1`？", r"""
很多数据库里整数除以整数的结果仍然是整数（舍去小数），例如 `1/3` 得 0。把其中一个数写成小数（`1.0`、`100.0`）就会按小数计算。写 `AVG(CASE WHEN … THEN 1.0 ELSE 0 END)` 或 `100.0 * COUNT(…) / COUNT(*)` 都是为了避免这个问题。Oracle 的 `/` 本身会得到小数，但这个习惯在换库时依然安全。
"""),
  THINK("**（联系）** 面试官给了题目就问你：「有什么要问我的吗？」，你会问哪三个问题？拿第 3 题（同时买过 A 和 B）举例。", r"""
可以问：① 已取消和未发货的订单算不算？② 「同时买过」是指同一张订单里同时买，还是不同订单里分别买过？（我们的解法是后者，如果要求同一张订单，分组要改成按订单。）③ 结果要客户编号、客户名，还是数量？同时可以顺带问数据量，决定要不要考虑索引。这些问题本身就在展示你做 BA 的思维。
"""),
  KW(("第 N 高","Nth highest","按值排名取第 N 个"),
     ("每组前 N 名","top N per group","分区排名后筛选"),
     ("紧凑排名","DENSE_RANK","并列不跳号"),
     ("关系除法","relational division","买过全部指定项的人"),
     ("帕累托","Pareto / ABC analysis","按累计占比分类"),
     ("累计占比","cumulative share","累计值除以总值"),
     ("比率","ratio","用 AVG(CASE) 计算占比"),
     ("相邻记录","adjacent rows","用 LAG 比较前后行"),
     ("边界条件","edge case","并列、NULL、空表、等于"),
     ("业务键","business key","判断重复的列组合"),
     ("行标识","ROWID","Oracle 里行的物理地址"),
     ("口径","definition","统计范围的定义"),
  ),
 ],
 "references": [
  SQLITE_DOC,
  {"title": "SQLite 官方文档：窗口函数", "url": "https://www.sqlite.org/windowfunctions.html", "note": "第 1、2、4、6 题用到的窗口函数"},
  ORACLE_SQL_REF,
  {"title": "Wikipedia：Pareto principle", "url": "https://en.wikipedia.org/wiki/Pareto_principle", "note": "80/20 法则的背景（ABC 分析是它在库存管理里的应用）"},
 ],
 "quiz": {"questions": [
  Q("求「第 2 高的金额」，金额有并列时最稳妥的做法是：",
    ["DENSE_RANK 排名后取排名为 2 的值", "ROW_NUMBER 取第 2 行", "ORDER BY 后 LIMIT 2", "MAX 减 1"], 0,
    "DENSE_RANK 并列不跳号，保证「第 2 高」是第二个不同的值；ROW_NUMBER 会把并列的值当成不同名次。"),
  Q("找「同时买过 A 和 B 两个 SKU 的客户」，下面哪个条件配合 GROUP BY 客户最合适？",
    ["HAVING COUNT(DISTINCT sku) = 2（先筛出只含 A 和 B 的行）", "WHERE sku = 'A' AND sku = 'B'", "ORDER BY sku", "SELECT DISTINCT sku"], 0,
    "一行的 sku 不可能同时等于 A 和 B，所以要分组后数不同的 SKU 个数。"),
  Q("订单取消率用 `AVG(CASE WHEN status = 'CANCELLED' THEN 1.0 ELSE 0 END)` 计算，其中写 1.0 而不是 1 的主要原因是：",
    ["避免整数运算把小数截断", "1.0 运行更快", "1 会报错", "1.0 能排序"], 0,
    "在不少数据库里整数相除结果仍是整数，用小数能得到正确的比例。"),
  Q("题目要求相邻两次下单间隔「超过 7 天」，某客户的两张订单刚好相隔 7 天，应该：",
    ["不算，因为 7 不大于 7", "算，因为 7 接近 7", "报错", "取决于排序"], 0,
    "超过是严格大于；如果题目是「至少 7 天」才用 >= 7，面试里要确认边界。"),
  Q("面试时拿到题目，最应该先做的是：",
    ["问清口径并用小例子确认期望结果", "立刻开始写完整答案", "先背语法", "先写索引"], 0,
    "多数题的坑在口径和边界，先问清再写，既减少错误，也体现 BA 的思维。"),
 ]},
}
retarget(unit, [1, 2, 0, 3, 1])

if __name__ == '__main__':
    dump(unit, "sql-0", "u09-interview-1.json", n_questions=5)
