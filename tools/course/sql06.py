"""sql-0 第 6 节：修改数据、事务、约束与索引"""
from sqllib import *

nb = Notebook()
C_DB = nb.cell(SETUP_DATA)
C_Q = nb.cell(SETUP_Q)

C_DML = nb.cell('''
db.execute("CREATE TABLE inv_copy AS SELECT * FROM inventory")   # 在副本上练，不动原表
print("先 SELECT 确认要改的行：")
q("SELECT * FROM inv_copy WHERE sku = 'BP100' AND stock_status = 'QUAR'")
cur = db.execute("UPDATE inv_copy SET stock_status = 'AVAIL' WHERE sku = 'BP100' AND stock_status = 'QUAR'")
print("UPDATE 影响行数:", cur.rowcount)
db.rollback()
q("SELECT stock_status, on_hand FROM inv_copy WHERE sku = 'BP100' ORDER BY on_hand")
''')

C_NOWHERE = nb.cell('''
cur = db.execute("UPDATE inv_copy SET on_hand = 0")      # 忘了写 WHERE
print("忘了 WHERE，影响行数:", cur.rowcount)
db.rollback()                                             # 撤销
print("rollback 之后，库存合计:", db.execute("SELECT SUM(on_hand) FROM inv_copy").fetchone()[0])
''')

C_CONSTR = nb.cell('''
try:
    db.execute("INSERT INTO customers VALUES (1, 'Duplicate Co', 'SG')")
except Exception as e:
    print(type(e).__name__, "-", e)
db.execute("DELETE FROM inv_copy WHERE sku = 'OLD9'")
print("删除后行数:", db.execute("SELECT COUNT(*) FROM inv_copy").fetchone()[0])
db.rollback()
print("rollback 后行数:", db.execute("SELECT COUNT(*) FROM inv_copy").fetchone()[0])
''')

C_INDEX = nb.cell('''
def uses_index(sql):
    plan = db.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    return any("SEARCH" in row[-1] for row in plan)

sql1 = "SELECT * FROM order_lines WHERE sku = 'BP100'"
sql2 = "SELECT * FROM order_lines WHERE substr(sku, 1, 2) = 'BP'"
print("没有索引，用索引吗：", uses_index(sql1))
db.execute("CREATE INDEX idx_lines_sku ON order_lines(sku)")
print("建索引后，用索引吗：", uses_index(sql1))
print("对列套函数后，用索引吗：", uses_index(sql2))
''')

unit = {
 "id": "u06",
 "title": "改数据要小心：INSERT / UPDATE / DELETE、事务、约束与索引",
 "en": "Changing Data Safely: DML, Transactions, Constraints & Indexes",
 "minutes": 40,
 "objectives": [
  "写出 **INSERT、UPDATE、DELETE**，并养成**先 SELECT 确认、再改、再核对行数**的习惯",
  "说明**事务 (transaction)**、**COMMIT** 和 **ROLLBACK**，以及 Oracle 里 DML 和 DDL 提交方式的差别",
  "说出**主键、外键、唯一、非空、检查**这些约束各防什么错",
  "知道**索引**是什么，什么时候有用，以及哪些写法会让索引失效",
  "知道作为 BA / 支持人员，什么情况下**不要自己改生产数据**，应该怎么走流程",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

前面五节都是「读」数据，这一节讲「改」。BA 和 BAU 支持岗位**经常只有读权限**，改生产数据通常要走变更流程；但你要看得懂别人写的修复脚本、能写出准确的修复方案让 DBA 执行、也要理解为什么系统会拒绝某些数据（约束）。另外，查询慢时知道**索引**是什么，能和 IT 沟通。

""" + C_DB + r"""
""" + C_Q + r"""

**本节安排（约 40 分钟）**：导读（2 分钟）→ 增删改与事务（12 分钟）→ 忘记 WHERE 的后果（6 分钟）→ 约束（8 分钟）→ 索引（8 分钟）→ 总结（4 分钟）。

### INSERT、UPDATE、DELETE 与事务

> **标准定义 · 事务 (transaction)**
>
> 一组要么**全部成功、要么全部撤销**的数据修改。`COMMIT` 提交，让修改永久生效；`ROLLBACK` 撤销，回到事务开始之前的状态。
>
> *English: A group of changes that either all succeed or are all undone; COMMIT makes them permanent, ROLLBACK discards them.*

**白话版：「改了先别急着存盘，确认没问题再 COMMIT；有问题还能 ROLLBACK」。**

**安全习惯三步：** ① 先用同样的 WHERE 写一条 SELECT，看看会命中哪几行；② 执行 UPDATE / DELETE，检查**影响行数**是否等于预期；③ 确认后再 COMMIT。下面在库存副本上练（不动原表）：

""" + C_DML + r"""

**读输出：** 先 SELECT 看到命中 1 行（BP100 的隔离库存）；UPDATE 影响行数是 1，符合预期；`rollback()` 之后，BP100 的两行库存回到原样（隔离 30、可用 120）。**影响行数和预期不一样时立刻 ROLLBACK。**

**Oracle 的差别：** Oracle 里 DML（INSERT / UPDATE / DELETE）要显式 `COMMIT` 才永久生效；而 **DDL（CREATE / ALTER / DROP）会自动提交**，不能 ROLLBACK。所以 `DROP TABLE` 之前一定要想清楚。

### 忘记写 WHERE

""" + C_NOWHERE + r"""

**读输出：** 忘了 WHERE，8 行库存全被改成 0，影响行数 8 一眼就能看出不对。rollback 之后库存合计恢复为 930。**这是新手最常见、代价最大的错误**，所以先 SELECT 再改、看影响行数、有事务保护，缺一不可。生产环境没有「撤销」键，要靠备份和变更审批。

### 约束：数据库帮你守规矩

> **标准定义 · 约束 (constraint)**
>
> 数据库对表里数据设的规则：**主键 (PRIMARY KEY)** 唯一且非空，标识一行；**外键 (FOREIGN KEY)** 必须引用存在的主键；**唯一 (UNIQUE)** 不允许重复；**非空 (NOT NULL)**；**检查 (CHECK)** 值必须满足条件。违反约束的写入会被**拒绝并报错**。
>
> *English: Rules the database enforces on data; violating writes are rejected.*

**白话版：「系统拒绝写入，通常不是系统坏了，是数据撞到了规则」。**

""" + C_CONSTR + r"""

**读输出：** 往客户表插入已经存在的 `cust_id = 1`，数据库拒绝并报 `UNIQUE constraint failed`（主键重复）。在 Oracle 里对应的是 `ORA-00001: unique constraint violated`。**读报错信息能直接告诉你哪条规则被违反**，这对排查「为什么这张单导入失败」很有用。再看删除：删掉 OLD9 之后行数减 1，rollback 后恢复。注意我们的演示库**没有建外键**，所以订单 109 才能引用不存在的客户 9；有外键的库里这条订单会被拒绝。

### 索引：让查询更快的「目录」

> **标准定义 · 索引 (index)**
>
> 为某一列（或几列）建立的有序目录。按这一列查找时可以直接定位，不用扫描整张表。代价：占空间，写入时要多维护一份。
>
> *English: A sorted lookup structure on one or more columns that speeds up searches at the cost of extra storage and slower writes.*

**白话版：「书后面的索引页：想找某个词，不用从头翻」。**

""" + C_INDEX + r"""

**读输出：** 没有索引时按 `sku` 查要扫描整张表（`False`）；建了索引后查询走索引（`True`）。但对列套上函数（`substr(sku, 1, 2)`）后，索引**失效**（`False`），数据库要对每一行先算函数。**让索引失效的常见写法：对列套函数、`LIKE '%xxx'`（通配符在开头）、隐式类型转换（如文本列和数字比较）。** 这类写法叫非 **SARGable**，能改成「列保持原样、值去做计算」就改。

**你不需要自己建索引**，但你可以对 IT 说：「这个查询按 `sku` 过滤，数据量大了很慢，是不是可以给 `sku` 加索引？」

### 对照你的工作

如果你的角色是 BA / 业务支持：**发现数据错误时，写清楚「要改哪几行、改成什么、依据是什么、影响多少行」，交给有权限的人（DBA 或系统管理员）按流程执行**，并保留修改前后的对账记录。这比自己直接改更安全，也更容易被审计接受。

### 这一节你要带走的三句话

1. **改数据前先用同样的 WHERE 写 SELECT，改完核对影响行数；事务让你能 ROLLBACK；Oracle 里 DDL 自动提交、不能回滚。**
2. **约束是数据库的守门员：报错信息会告诉你哪条规则被违反（主键重复、外键不存在、不能为空）。**
3. **索引像目录，加速查找但有代价；对列套函数、开头通配符会让索引失效；生产数据的修改要走变更流程。**
"""),
  THINK("**（实践）** 在副本表上写一条语句，把 `MY-WH` 仓库的所有 `QUAR` 状态库存改成 `AVAIL`，并写出你执行前后各要做的检查。", r"""
`UPDATE inv_copy SET stock_status = 'AVAIL' WHERE warehouse = 'MY-WH' AND stock_status = 'QUAR'`。执行前：用同样的条件 SELECT，确认命中 1 行（BP200 的 25 件）；执行后：确认影响行数是 1，再 SELECT 看结果；没问题才 COMMIT。现实中「隔离库存放行」是业务动作，要有质量部门的批准，不是 SQL 能决定的。
"""),
  THINK("**（概念辨析）** 同事说「导入失败了，系统有 bug」。报错是 `unique constraint violated`。你怎么判断是系统问题还是数据问题？", r"""
这个报错说明导入的数据里有**和已有记录重复的唯一值**，更像数据问题（重复导入、编号重复）而不是系统缺陷。查法：从报错里找到是哪个约束，在目标表里查这个键是否已存在，再看导入文件里是否有重复。如果数据没问题而系统还报错，才往系统缺陷方向查。
"""),
  THINK("**（联系）** 你发现订单 109 引用了不存在的客户 9。你应该直接在生产库里插入客户 9 吗？", r"""
不应该。先弄清楚是哪种情况：客户 9 是真实客户但主数据没建（找主数据负责人建），还是订单上写错了客户号（找订单负责人改），不要凭猜测补数据。把查询结果（哪张单、什么问题）交给对应负责人，并记录处理结果。
"""),
  KW(("插入","INSERT","新增行"),
     ("更新","UPDATE","修改已有行"),
     ("删除","DELETE","删除行"),
     ("事务","transaction","要么全成功要么全撤销"),
     ("提交","COMMIT","让修改永久生效"),
     ("回滚","ROLLBACK","撤销未提交的修改"),
     ("约束","constraint","数据库强制的规则"),
     ("主键","PRIMARY KEY","唯一且非空"),
     ("外键","FOREIGN KEY","必须引用存在的行"),
     ("索引","index","加速查找的有序目录"),
     ("执行计划","execution plan","数据库打算怎么执行查询"),
     ("影响行数","rows affected","语句实际改了几行"),
  ),
 ],
 "references": [
  SQLITE_DOC,
  ORACLE_SQL_REF,
  {"title": "Wikipedia：Database transaction", "url": "https://en.wikipedia.org/wiki/Database_transaction", "note": "事务与 ACID 的概述"},
  {"title": "Wikipedia：Database index", "url": "https://en.wikipedia.org/wiki/Database_index", "note": "索引的原理与代价"},
 ],
 "quiz": {"questions": [
  Q("执行 UPDATE 前，最推荐的第一步是：",
    ["用同样的 WHERE 写 SELECT，确认会命中哪些行", "直接执行再说", "先 DROP 表", "先 COMMIT"], 0,
    "先 SELECT 确认命中范围，执行后再核对影响行数是否一致。"),
  Q("在 Oracle 里，下面哪个语句执行后**不能**用 ROLLBACK 撤销？",
    ["DROP TABLE（DDL，自动提交）", "UPDATE（未提交时）", "DELETE（未提交时）", "INSERT（未提交时）"], 0,
    "Oracle 的 DDL 会隐式提交，不能回滚；未提交的 DML 可以回滚。"),
  Q("插入一行时报 `unique constraint violated`，说明：",
    ["要插入的唯一值和已有记录重复", "磁盘满了", "SQL 语法错误", "没有权限登录"], 0,
    "唯一或主键约束被违反，意味着该键已经存在。"),
  Q("下面哪种写法最容易让列上的索引失效？",
    ["对列套函数，如 WHERE substr(sku,1,2) = 'BP'", "WHERE sku = 'BP100'", "ORDER BY sku", "SELECT sku"], 0,
    "对列做函数运算后，数据库无法直接用索引定位，只能逐行计算。"),
  Q("你发现生产数据里有错误但只有读权限，最合适的做法是：",
    ["写清要改的行、改成什么、依据和影响行数，交给有权限的人按流程处理", "想办法借别人账号改", "忽略它", "直接告诉所有人系统坏了"], 0,
    "清晰的修复方案加变更流程，既安全又方便审计。"),
 ]},
}
retarget(unit, [3, 1, 0, 2, 3])

if __name__ == '__main__':
    dump(unit, "sql-0", "u06-dml-index.json", n_questions=5)
