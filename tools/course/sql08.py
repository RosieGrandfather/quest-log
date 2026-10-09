"""sql-0 第 8 节：Oracle 方言、JDE 常见写法、证书与水平自测"""
from sqllib import *

nb = Notebook()

C_JDE = nb.cell('''
import datetime
def jde_to_date(j):               # CYYDDD：C 是世纪（1 代表 20xx），YY 是年，DDD 是一年中的第几天
    c, yy, ddd = j // 100000, (j // 1000) % 100, j % 1000
    return datetime.date(1900 + c * 100 + yy, 1, 1) + datetime.timedelta(days=ddd - 1)

def date_to_jde(d):
    return (d.year - 1900) * 1000 + d.timetuple().tm_yday

print(jde_to_date(126246))
print(date_to_jde(datetime.date(2026, 9, 3)))
''')

unit = {
 "id": "u08",
 "title": "换成 Oracle：方言对照、常见报错、证书路线与水平自测",
 "en": "Switching to Oracle: Dialect Map, Common Errors, Certification & Self-Assessment",
 "minutes": 45,
 "objectives": [
  "把前七节的 SQLite 写法**翻译成 Oracle**：取前几行、空值函数、日期、字符串、集合运算",
  "记住 Oracle 的几个**特有行为**：空字符串等于 NULL、`ROWNUM` 先于排序、表别名不能写 AS、NULL 的排序位置",
  "读懂**常见 ORA 报错**，知道各自大概是什么问题",
  "了解 **JDE（企业资源系统）里常见的日期格式**，会做转换（先在自己的库里验证）",
  "对照 **Oracle 官方 SQL 证书 (1Z0-071)** 的考试范围，知道本课程覆盖了什么、还缺什么，并给自己做一次水平自测",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

前七节在浏览器里用 SQLite 练，好处是随时能跑；你在 OMRON 面对的是 **Oracle**（JDE 背后的数据库），写法有一些差别。这一节是「翻译表」：同一个意图在 Oracle 里怎么写。最后回答你一开始问的两个问题：**证书考哪个**，以及**你现在到底是什么水平**。

> **说明：** 浏览器里不能运行 Oracle，这一节的 Oracle 写法是按官方文档和常见用法整理的，**我没有在 Oracle 数据库里逐条运行过**。你在公司的库里（只读环境）试之前，对照官方 SQL 语言参考确认，并先用小数据验证。

**本节安排（约 45 分钟）**：导读（2 分钟）→ 写法对照表（12 分钟）→ Oracle 特有行为（8 分钟）→ 常见报错（5 分钟）→ JDE 日期（5 分钟）→ 证书与范围（8 分钟）→ 水平自测（5 分钟）。

### 写法对照表

| 想做的事 | SQLite（本课程里） | Oracle |
|---|---|---|
| 取前 3 行 | `LIMIT 3` | 12c 及以上：`FETCH FIRST 3 ROWS ONLY`；老写法：`WHERE ROWNUM <= 3`（见下） |
| 空值换默认值 | `COALESCE(x, 0)` / `IFNULL` | `NVL(x, 0)` 或 `COALESCE(x, 0)` |
| 字符串拼接 | `a \|\| b` | `a \|\| b`（相同） |
| 截取字符串 | `substr(s, 1, 2)` | `SUBSTR(s, 1, 2)` |
| 当前日期 | `date('now')` | `SYSDATE`（带时间）；`TRUNC(SYSDATE)`（只要日期） |
| 文本转日期 | 日期直接存成文本 | `TO_DATE('2026-09-03', 'YYYY-MM-DD')` 或 `DATE '2026-09-03'` |
| 日期转文本、按月分组 | `substr(order_date, 1, 7)` | `TO_CHAR(order_date, 'YYYY-MM')` |
| 日期加减 | `date(d, '+7 day')` | `d + 7`（加 7 天）；`ADD_MONTHS(d, 1)` |
| 两个日期相差几天 | `julianday(a) - julianday(b)` | `a - b`（直接相减得天数） |
| 左边有右边没有 | `EXCEPT` | `MINUS`（较新版本也支持 EXCEPT，以你们版本为准） |
| 没有表的查询 | `SELECT 1` | `SELECT 1 FROM DUAL`（较新版本可省略 FROM） |
| 分支判断 | `CASE WHEN` | `CASE WHEN`，也有老的 `DECODE(x, a, b, c)` |
| 文本类型 | `TEXT` | `VARCHAR2(n)` |
| 数字类型 | `INTEGER / REAL` | `NUMBER` |
| 绑定参数 | `?` | `:name`（如 `WHERE sku = :sku`） |

### Oracle 的几个特有行为（容易踩坑）

1. **空字符串就是 NULL。** 在 Oracle 里 `''` 等于 NULL，所以 `WHERE name = ''` 永远查不到东西，要写 `IS NULL`。字符串长度为 0 的情况不存在。
2. **ROWNUM 在排序之前生效。** `SELECT * FROM t WHERE ROWNUM <= 3 ORDER BY amount DESC` 取的是「随便 3 行再排序」，不是金额最大的 3 行。正确写法是先排序再套一层：`SELECT * FROM (SELECT * FROM t ORDER BY amount DESC) WHERE ROWNUM <= 3`，或直接用 `FETCH FIRST`。
3. **表别名不能写 AS。** 写 `FROM orders o` 可以，`FROM orders AS o` 在 Oracle 里会报错（列别名可以写 AS）。
4. **NULL 的排序位置。** Oracle 里升序时 NULL 排最后、降序时排最前（SQLite 正好相反）。要控制就写 `ORDER BY x NULLS LAST`。
5. **文本比较区分大小写**，对象名默认大写。`WHERE status = 'open'` 查不到 `'OPEN'`；要忽略大小写用 `UPPER(status) = 'OPEN'`。
6. **别依赖隐式日期转换。** `WHERE order_date > '2026-09-03'` 能不能工作取决于数据库的日期格式设置，用 `DATE '2026-09-03'` 或 `TO_DATE` 才可靠。
7. **看到 `(+)` 不要慌。** 老代码里 `WHERE a.id = b.id(+)` 是左连接（`(+)` 在哪边，哪边可以缺行）。新代码用标准 `LEFT JOIN`。

### 常见 ORA 报错速查

| 报错 | 大概意思 | 常见原因 |
|---|---|---|
| ORA-00942 | 表或视图不存在 | 表名写错、没有权限、少写了所属用户（schema） |
| ORA-00904 | 标识符无效 | 列名写错、别名用在了不该用的地方 |
| ORA-00979 | 不是 GROUP BY 表达式 | SELECT 里的非聚合列没有写进 GROUP BY（第 2 节） |
| ORA-00001 | 违反唯一约束 | 主键或唯一值重复（第 6 节） |
| ORA-01400 | 不能插入 NULL | 非空列没给值 |
| ORA-02291 | 违反完整性约束，找不到父键 | 外键引用的主数据不存在 |
| ORA-02292 | 违反完整性约束，发现子记录 | 要删的主数据还被别的表引用 |
| ORA-01722 | 无效数字 | 文本和数字比较或转换失败（如把 `'N/A'` 当数字） |
| ORA-01843 / ORA-01861 | 月份无效 / 文本和格式不匹配 | 日期文本和格式模板对不上 |

**读报错的办法：先看 ORA 编号，再看报错指向的行和列。** 这些含义按 Oracle 官方文档的常见解释整理，遇到具体报错以官方错误信息文档为准。

### JDE 里的日期（先验证再用）

很多 JDE 的表把日期存成一个整数，格式是 **CYYDDD**：C 是世纪（1 代表 20xx），YY 是年份后两位，DDD 是这一年的第几天。例如 `126246` 表示 2026 年的第 246 天，也就是 2026-09-03。用 Python 演示规则：

""" + C_JDE + r"""

**读输出：** `126246` 转成 `2026-09-03`；反过来 2026-09-03 就是 `126246`。在 Oracle 里常见的转换写法是 `TO_DATE(TO_CHAR(1900000 + 日期字段), 'YYYYDDD')`（把 126246 加上 1900000 得 2026246，再按「年 + 天数」解析）。**这是常见写法，不同表、不同版本的字段可能不同，你要先在自己的库里拿一个已知日期的记录验证。** 另外，JDE 的表名和列名通常带表前缀（例如销售订单明细表的列都以相同的两个字母开头），具体以你们系统里的数据字典为准。

### 证书：你问的第一个问题

**我的查询结果（来自公开网页，不是 Oracle 官方页面，价格和细节请以官方为准）：**

| 证书 | 说明 | 适合你吗 |
|---|---|---|
| **Oracle Database SQL Certified Associate（考试代码 1Z0-071）** | Oracle 官方 SQL 认证。多个备考网站写的是：单选题约 63 题、120 分钟、及格线 63%，每次约 245 美元，没有免费重考 | **和你的工作环境（Oracle / JDE）最对口**；是证书里「证明 SQL 水平」最直接的一个 |
| **DataCamp SQL Associate** | DataCamp 的 SQL 技能认证，不绑定某个数据库，订阅制 | 便宜、灵活；但行业认可度我没查到数据 |
| **Microsoft DP-900 / PL-300** | DP-900 是云数据基础，不是专门考 SQL；PL-300 是 Power BI 分析师，你已经在备考 | SQL 只是其中一部分，不能代替 SQL 证书 |

**我的判断（请你自己权衡）：**

- 如果你想在简历上放一个**能直接证明 SQL** 的证书，**1Z0-071 是最对口的选择**，因为你的实际工作环境就是 Oracle。
- 但**我没有查到新加坡雇主对这类证书重视到什么程度的数据**。BA / IT BA 岗位更看重你能不能讲清楚做过什么，所以证书是加分项，不是门票；先把本课程练熟、在 Oracle 里实际写一遍，比先交考试费更重要。
- 考试内容的官方页面我这次没能打开，所以**题量、费用、范围、是否有新版（有备考网站提到较新的 1Z0-171 版本）请在报名前去 Oracle 官方网站确认**。备考网站列出的 16 个考试范围，对照本课程大致是：

| 考试范围（备考网站转述 Oracle 的目录） | 本课程覆盖 |
|---|---|
| 关系型数据库概念、SELECT、筛选与排序 | 第 1 节 |
| 单行函数、类型转换与条件表达式 | 第 1、8 节（函数只讲了一小部分，需要另外补） |
| 分组函数 | 第 2 节 |
| 多表连接 | 第 3 节 |
| 子查询、集合运算 | 第 4 节 |
| DML（增删改）、DDL（建表） | 第 6 节（DDL 只讲了索引和约束，建表细节需补） |
| 索引、同义词、序列 | 第 6 节只讲了索引，**同义词和序列没讲** |
| 视图 | **没讲** |
| 用户权限 (GRANT / REVOKE) | **没讲** |
| 数据字典视图 | **没讲** |
| 时区与日期时间类型 | **没讲**（只讲了日期基础） |

所以如果要考，大约还要**补 1 周左右**：单行函数、视图、同义词和序列、权限、数据字典、时区。窗口函数（第 5 节）在这份考试范围的转述里没有出现，但对工作和面试很有用。

### 水平自测：你心里没底的那件事

不看答案，在 Oracle 或本课程的练习库里，**每项 10 分钟内写得出来、并能解释结果**，就算过：

| 档次 | 任务 | 对应章节 |
|---|---|---|
| **A 能读懂别人的 SQL** | ① 读一条三表 JOIN 加 GROUP BY 的查询，说出每一行结果代表什么；② 说出 `NOT IN` 遇到 NULL 的问题 | 第 1–4 节 |
| **B 能独立做 BAU 支持** | ③ 找出没有主数据的孤儿记录；④ 找出重复记录并说明保留哪条要问谁；⑤ 把两边数字对账找出差异；⑥ 把「总数、可用、隔离」放进同一条查询 | 第 3、5、7 节 |
| **C 面试和高级支持** | ⑦ 用窗口函数取每组最新一条；⑧ 解释一个查询为什么慢、该怎么改；⑨ 把 SQLite 写法改成 Oracle 写法 | 第 5、6、8 节 |

**怎么用这张表：** 你的简历说你有 2 年 Oracle 和 SQL 经验，做过 JDE 排查。A 档你大概率已经过，B 档里的任务你工作中应该做过一部分，**用这张表把没把握的挑出来重点练**，比泛泛地学更快。如果 B 档你都能写出来，面对 BAU 支持类岗位的 SQL 要求就比较稳了；面试时要能讲出你实际写过的查询，而不仅仅是知道概念。

### 这一节你要带走的三句话

1. **Oracle 和 SQLite 基础相同，差别集中在取前几行、日期、空字符串即 NULL、ROWNUM 先于排序、表别名不能写 AS、MINUS。**
2. **读 ORA 报错先看编号；JDE 日期常见格式是 CYYDDD，用之前先在自己的库里拿已知日期验证。**
3. **证书和水平是两回事：1Z0-071 最对口，但先用自测表找出薄弱项；费用、范围、版本以 Oracle 官方页面为准。**
"""),
  THINK("**（实践）** 把这条 SQLite 查询改成 Oracle 写法：`SELECT order_id, order_date FROM orders ORDER BY order_date DESC LIMIT 2`。再把 `substr(order_date,1,7)` 的月份分组改成 Oracle 写法（假设 order_date 是日期类型）。", r"""
第一条：`SELECT order_id, order_date FROM orders ORDER BY order_date DESC FETCH FIRST 2 ROWS ONLY`；老版本用 `SELECT * FROM (SELECT order_id, order_date FROM orders ORDER BY order_date DESC) WHERE ROWNUM <= 2`。月份分组：`TO_CHAR(order_date, 'YYYY-MM')`，`GROUP BY` 里也要写同样的表达式。
"""),
  THINK("**（概念辨析）** 为什么 `SELECT * FROM t WHERE ROWNUM <= 3 ORDER BY amount DESC` 不是「金额最大的 3 行」？", r"""
因为 ROWNUM 是在取出行的时候就编号的，**先于 ORDER BY**。数据库先随便取 3 行，再对这 3 行排序。要得到最大的 3 行，必须先在子查询里排序，外层再用 ROWNUM 限制，或者直接使用 FETCH FIRST。
"""),
  THINK("**（联系）** 同事让你查「所有姓名为空的客户」，你写了 `WHERE name = ''`，在 Oracle 里查不到任何行。为什么？该怎么写？", r"""
Oracle 里空字符串被当成 NULL，`name = ''` 等价于 `name = NULL`，结果是未知，永远不为真。要写 `WHERE name IS NULL`。这也说明为什么要先搞清楚「空」在这个系统里是 NULL 还是空格或其他占位符，可以用 `LENGTH` 和 `TRIM` 去验证。
"""),
  KW(("取前几行","FETCH FIRST","Oracle 12c 及以上的限制行数写法"),
     ("行号","ROWNUM","先于排序生效的伪列"),
     ("空值函数","NVL","把 NULL 换成默认值"),
     ("虚拟表","DUAL","没有真实表时用来选常量"),
     ("日期转换","TO_DATE / TO_CHAR","日期和文本互转"),
     ("当前时间","SYSDATE","数据库服务器当前日期时间"),
     ("差集","MINUS","Oracle 里的 EXCEPT"),
     ("旧式左连接","(+)","老代码里的外连接写法"),
     ("报错编号","ORA-nnnnn","Oracle 错误编号"),
     ("JDE 日期","CYYDDD","世纪、年、一年中的第几天"),
     ("SQL 认证","1Z0-071","Oracle Database SQL Certified Associate"),
     ("数据字典","data dictionary","描述表和列本身的系统视图"),
  ),
 ],
 "references": [
  ORACLE_SQL_REF,
  {"title": "Oracle MyLearn：Exam 1Z0-071（Oracle Database SQL）", "url": "https://mylearn.oracle.com/ou/exam/oracle-database-sql-1z0-071/105037/110647/170369", "note": "官方考试页面（我这次没能读到页面里的考试细节，请你自己打开确认题量、费用、范围、是否有新版）"},
  {"title": "OpenExamPrep：Oracle SQL 1Z0-071 指南（2026）", "url": "https://open-exam-prep.com/blog/oracle-sql-exam-guide-2026", "note": "第三方备考网站，本节转述的题量、时长、及格线和 16 个范围来自这里，不是官方页面"},
  {"title": "DataCamp：Best SQL certifications", "url": "https://www.datacamp.com/blog/best-sql-certifications", "note": "对几种 SQL 相关证书的横向介绍，同样是第三方（DataCamp 自己也卖认证）"},
 ],
 "quiz": {"questions": [
  Q("在 Oracle 里，`WHERE name = ''` 通常查不到任何行，因为：",
    ["空字符串被当作 NULL，比较结果未知", "name 不能为空", "引号写错了", "Oracle 不支持 WHERE"], 0,
    "Oracle 把长度为 0 的字符串当作 NULL，要用 IS NULL 判断。"),
  Q("想取金额最大的 3 行，Oracle 里正确的做法是：",
    ["先在子查询里排序，外层用 ROWNUM 限制，或用 FETCH FIRST 3 ROWS ONLY", "WHERE ROWNUM <= 3 ORDER BY amount DESC", "LIMIT 3", "TOP 3 加 GROUP BY"], 0,
    "ROWNUM 先于排序生效，直接和 ORDER BY 写在同一层结果不对。"),
  Q("下面哪个报错最可能表示「SELECT 里有非聚合列没写进 GROUP BY」？",
    ["ORA-00979", "ORA-00942", "ORA-00001", "ORA-01400"], 0,
    "ORA-00979 是「不是 GROUP BY 表达式」；ORA-00942 是表或视图不存在。"),
  Q("JDE 日期 `126246` 按 CYYDDD 规则表示：",
    ["2026 年的第 246 天（2026-09-03）", "1926 年的第 246 天", "2012 年 6 月 246 日", "2026 年 12 月 6 日"], 0,
    "C = 1 表示 20xx 世纪，YY = 26，DDD = 246。使用前要在自己的库里用已知日期验证。"),
  Q("关于 SQL 证书，下面哪个判断最稳妥？",
    ["1Z0-071 和 Oracle 环境最对口，但费用、范围、版本以 Oracle 官方页面为准，证书是加分项而不是门票", "有证书就一定能拿到 offer", "所有 SQL 证书价值相同", "不需要看官方页面，备考网站的信息就够"], 0,
    "备考网站是第三方信息，报名前要核对官方；招聘更看重你能讲清楚实际做过什么。"),
 ]},
}
retarget(unit, [3, 0, 1, 2, 0])

if __name__ == '__main__':
    dump(unit, "sql-0", "u08-oracle-cert.json", n_questions=5)
