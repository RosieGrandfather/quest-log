"""pl300-0 第 4 节：数据模型设计"""
from pllib import *

nb = Notebook()

C_FILTER = nb.cell('''
dim_product = {1: {"Name": "Pen",  "Cat": "Stationery"},
               2: {"Name": "Desk", "Cat": "Furniture"},
               3: {"Name": "Lamp", "Cat": "Furniture"}}          # 一端：键唯一
fact_sales = [(101, 1, 10), (102, 2, 200), (103, 2, 150), (104, 1, 5)]   # 多端：(订单, ProductKey, 金额)

def total(filter_cat=None):
    rows = [f for f in fact_sales if filter_cat is None or dim_product[f[1]]["Cat"] == filter_cat]
    return sum(f[2] for f in rows)

print("全部:", total(), "  家具:", total("Furniture"), "  文具:", total("Stationery"))

# 单向筛选：维度 → 事实。只从事实表筛选时，维度表不会被筛掉：
visible_fact = [f for f in fact_sales if f[2] >= 100]
print("事实表筛选后，仍然可见的产品（单向）:", sorted(dim_product))
print("双向筛选时，可见的产品:", sorted({f[1] for f in visible_fact}))
''')

C_ROLE = nb.cell('''
import datetime as dt
orders = [("O1", dt.date(2026, 1, 28), dt.date(2026, 2, 3), 100),
          ("O2", dt.date(2026, 2, 5),  dt.date(2026, 2, 6), 40),
          ("O3", dt.date(2026, 2, 27), dt.date(2026, 3, 2), 60)]

def by_month(date_index):
    out = {}
    for o in orders:
        key = o[date_index].strftime("%Y-%m")
        out[key] = out.get(key, 0) + o[3]
    return dict(sorted(out.items()))

print("按下单日期（激活关系）:", by_month(1))
print("按发货日期（不激活，USERELATIONSHIP）:", by_month(2))
''')

C_DATE = nb.cell('''
import datetime as dt
start, end = dt.date(2026, 1, 1), dt.date(2026, 12, 31)       # 连续、覆盖所有事实日期
days = [start + dt.timedelta(d) for d in range((end - start).days + 1)]

def fiscal_year(d, first_month=4):                              # 财年从 4 月开始（示例）
    return d.year + 1 if d.month >= first_month else d.year

cal = [{"Date": d, "Year": d.year, "Month": d.month, "Quarter": (d.month - 1) // 3 + 1, "FY": fiscal_year(d)} for d in days]
print("行数:", len(cal), " 最早:", cal[0]["Date"], " 最晚:", cal[-1]["Date"])
print("连续没有缺口:", all((b["Date"] - a["Date"]).days == 1 for a, b in zip(cal, cal[1:])))
print("2026-03-31 的 FY:", cal[89]["FY"], " 2026-04-01 的 FY:", cal[90]["FY"])
''')

C_COL = nb.cell('''
rows = [{"Rev": 100, "Cost": 60}, {"Rev": 400, "Cost": 100}]
for r in rows: r["Margin"] = (r["Rev"] - r["Cost"]) / r["Rev"]     # 计算列：每行算好存起来

print("每行毛利率:", [round(r["Margin"], 3) for r in rows])
print("把毛利率列求和:", round(sum(r["Margin"] for r in rows), 3), " ← 没有意义")
print("平均毛利率（各行平均）:", round(sum(r["Margin"] for r in rows) / 2, 3))
rev, cost = sum(r["Rev"] for r in rows), sum(r["Cost"] for r in rows)
print("度量值的正确做法（总和之比）:", round((rev - cost) / rev, 3))
''')

unit = {
 "id": "u04",
 "title": "数据模型设计：星型模型、关系与日期表",
 "en": "Model Design: Star Schema, Relationships & the Date Table",
 "minutes": 45,
 "objectives": [
  "说出**星型模型 (star schema)** 的结构，并解释为什么 Power BI 偏爱它",
  "区分**基数 (cardinality)**（一对多、一对一、多对多）和**交叉筛选方向 (cross-filter direction)**（单向、双向），并知道默认该怎么选",
  "解释**角色扮演维度 (role-playing dimension)**，以及激活 / 非激活关系和 `USERELATIONSHIP` 的关系",
  "为什么、怎样建立一张**通用日期表 (common date table)** 并**标记为日期表**",
  "区分**计算列、度量值、计算表**，并设置表和列的常用属性（排序依据、汇总方式、数据类别、隐藏）",
 ],
 "blocks": [
  T(r"""
### 先说这一小节要干什么

**Model the data（建模）** 同样占 25–30%，是整个考试里分量最重、也最容易被场景题绕的一块。你已经会拖拽建关系，这一节要补的是**为什么这样设计**：考试从不问「怎么拖」，只问「**这个模型有什么问题、应该改成什么样**」。

**学完它你就能看懂这几件事：**

- 为什么「销售表里直接放客户姓名、产品类别」会让模型又大又慢；
- 一张日期表怎么同时服务下单日期和发货日期；
- 为什么按月份排序时 `April` 会排在 `August` 前面（以及怎么修）；
- 为什么毛利率不该做成「可以求和的列」。

**本小节安排（约 45 分钟）**：导读（2 分钟）→ 星型模型与两个视频（20 分钟）→ 基数、方向、角色扮演（10 分钟）→ 日期表（5 分钟）→ 计算列 / 度量值 / 属性（5 分钟）→ 总结与「想一想」（3 分钟）。

### 星型模型

> **标准定义 · 星型模型 (star schema)**
>
> 一种建模方式：中间一张**事实表 (fact table)** 存可度量的事件，周围连接若干张**维度表 (dimension table)**，每个维度**一对多**地筛选事实表。维度表是「一」端，键唯一；事实表是「多」端，保存维度的外键。Power BI 的引擎（VertiPaq）和 DAX 的筛选传播都为这种形状优化：维度做筛选和分组，事实表做汇总。
>
> *English: A central fact table surrounded by dimension tables, each related one-to-many to the fact table; dimensions filter and group, facts are aggregated.*

**白话版：「流水账 + 通讯录」，不要把通讯录抄进流水账。** 几个设计结论：**事实表窄而长**（键 + 数值），**维度表宽而短**（属性）；维度之间不直接连接，而是都连到事实表；尽量**不要把一个维度再拆成几张**（雪花模型），除非有强理由；多个事实表共享同样的**一致维度**（如日期、产品）。
"""),
  V("vZndrBBPiQc", "Why Power BI loves a Star Schema", 8),
  V("mPnnygpy2lY", "Star Schema in 10 Minutes: The ONLY Explanation You Need!", 9),
  T(r"""
> 两个视频（Guy in a Cube 约 8 分钟；Pragmatic Works 约 9 分钟）都是讲星型模型的。**我只核实了它们存在且可嵌入，内容没有看过**，请带着一个问题去看：**为什么事实表里不放文本属性**。还有一个 Chandoo 的 22 分钟长视频放在参考资料里，选看。

### 基数与交叉筛选方向

> **标准定义 · 基数 (cardinality) 与交叉筛选方向 (cross-filter direction)**
>
> **基数**描述两端的键关系：**一对多 (1:\*)**——维度到事实，最常见、首选；**一对一 (1:1)**——两张表的键都唯一，通常应该合成一张；**多对多 (\*:\*)**——两端的键都不唯一，要谨慎。**交叉筛选方向**决定筛选沿关系传播的方向：**单向 (Single)**——只从「一」端筛选「多」端；**双向 (Both)**——两个方向都传播。
>
> *English: Cardinality is one-to-many, one-to-one or many-to-many; cross-filter direction is single or both, controlling which way filters propagate.*

**白话版：「箭头指向谁被筛」。** 单向意味着你在产品表里选「家具」，事实表只显示家具的订单；反过来你在事实表里筛选，产品表不会少几行。**默认和首选：一对多、单向。** 双向会带来歧义和性能代价，只在确有需要（比如要在维度切片器里「只显示有数据的值」）时才开，并且考虑用 DAX（`CROSSFILTER`）局部开。
""" + C_FILTER + r"""

**读输出：** 总金额 365；家具 $200+150=350$，文具 $10+5=15$。事实表筛成「金额 ≥ 100」之后，单向时产品表仍然有 3 个产品可见；**双向时**只剩产品 2（`Desk`）。这就是双向「让维度反过来被事实筛选」的意思。

### 角色扮演维度与日期表

> **标准定义 · 角色扮演维度 (role-playing dimension)**
>
> 同一张维度表在事实表里扮演**多个角色**。典型例子：事实表有 `OrderDate`、`ShipDate`，都连接到同一张 `Date` 表。Power BI 里**两张表之间同一时间只能有一条激活 (active) 关系**，其余是**非激活 (inactive)**（虚线）。要用非激活的那条，在度量值里写 `CALCULATE([Sales], USERELATIONSHIP(Sales[ShipDate], 'Date'[Date]))`；或者**复制一份 Date 表**，每个角色一张。
>
> *English: One dimension plays several roles for a fact table; only one relationship can be active at a time, and inactive ones are activated in a measure with USERELATIONSHIP, or the dimension is duplicated.*

**白话版：「一个日历，两种读法」。** 默认按下单日期看，需要时临时「切换」成发货日期。取舍：`USERELATIONSHIP` 不增加模型大小，但同一个视觉对象里没法同时并排放下单和发货两种视角；复制日期表则每个角色都能独立切片，代价是多一张表。
""" + C_ROLE + r"""

**读输出：** 按下单日期，一月 100、二月 100（`O2` 的 40 加 `O3` 的 60）；按发货日期，二月是 `O1` 的 100 加 `O2` 的 40 等于 140，三月是 `O3` 的 60。同样三笔订单，月份切法不同，结果不同——考试里「度量值要按发货日期统计」就是这个。

> **标准定义 · 通用日期表 (common date table)**
>
> 一张**每天一行、日期连续、覆盖事实表所有日期范围**的维度表，含年、季度、月、星期、财年等列；用 **Mark as date table（标记为日期表）** 指定它的日期列（必须是日期类型、无空值、无重复）。时间智能函数（`TOTALYTD`、`SAMEPERIODLASTYEAR` 等）依赖它。可以用 DAX 的 `CALENDAR` / `CALENDARAUTO` 建（计算表），也可以在 Power Query 里生成，或从数据源 / 数据流引入。
>
> *English: A contiguous, one-row-per-day dimension covering all fact dates, marked as the date table so time-intelligence functions work.*

**白话版：「一份统一的日历」。** 事实表的日期往往有缺口（周末没订单），**不能直接拿事实表的日期列做时间智能**；必须有一张连续的日历。另外建议**关闭「自动日期 / 时间 (Auto date/time)」**，否则每个日期列会悄悄生成一张隐藏的日期表，增加模型大小。
""" + C_DATE + r"""

**读输出：** 2026 年共 365 行、从 2026-01-01 到 2026-12-31、没有缺口；财年从 4 月开始时，3 月 31 日的 `FY` 是 2026，4 月 1 日变成 2027。**排序陷阱：** 月份名称列按字母排序会让 `April`、`August` 排在 `January` 前面，修法是**按列排序 (Sort by column)**：选中月份名列，让它按月份数字列排序。

### 计算列、度量值、计算表与属性

> **标准定义 · 计算列 (calculated column)、度量值 (measure)、计算表 (calculated table)**
>
> **计算列**：用 DAX 逐行计算，**在刷新时算好并存进模型**，占内存，可以用来做筛选、分组、排序。**度量值**：在**查询时**按当前**筛选上下文**计算，不占存储，用来做聚合。**计算表**：用 DAX 表达式生成一张新表（如日期表），在刷新时计算并存储。选择原则：**聚合用度量值；要拿来切片、分组、排序的才用列；能在 Power Query 里做的优先在 Power Query 里做**。
>
> *English: Calculated columns are computed row by row at refresh and stored; measures are computed at query time in the current filter context; calculated tables are DAX-generated tables stored at refresh.*

**白话版：「列是写在纸上的，度量值是现场算的」。** 一个经典陷阱：把毛利率做成列，再把列求和：
""" + C_COL + r"""

**读输出：** 两行的毛利率是 0.4 和 0.75，求和得 1.15——**百分比相加没有意义**；各行平均是 0.575；用总和之比 $(500-160)/500$ 才得 0.68。**比率永远用度量值：先聚合分子分母，再相除。**

**表和列的属性（常考）：** **数据类型与格式**；**默认汇总 (Default summarization)**（比如把 `ProductKey` 设成「不汇总」，避免被拖进值里求和）；**按列排序**；**数据类别 (Data category)**（城市、国家、网址、图片网址，让地图和链接行为正确）；**隐藏 (Hide in report view)**——**外键列和不应该被直接汇总的数值列**应该隐藏，只暴露度量值；**显示文件夹 (Display folders)** 和描述，帮助使用者。

### 这一小节你要带走的三句话

1. **星型模型**：窄长的事实表 + 宽短的维度表，一对多、单向，键唯一；双向和多对多要有理由。
2. **一个日历服务多个日期**：非激活关系加 `USERELATIONSHIP`，或复制日期表；日期表要连续并标记；月份名用「按列排序」。
3. **聚合用度量值，比率先聚合再相除**；列用来切片和排序；外键和裸数值列隐藏。
"""),
  THINK("**（场景判断）** 销售事实表里直接有 `CustomerName`、`CustomerCity`、`ProductCategory` 三个文本列，模型很大、很慢。应该怎么改？", r"""
把这些属性拆出去，建成 `Customer`、`Product` 维度表（键唯一），事实表只留 `CustomerKey`、`ProductKey` 和数值，再用一对多、单向关系连起来。文本列在事实表里重复数百万次，压缩效果差；放在维度表里只存一份。
"""),
  THINK("**（概念辨析）** 一个同事把 `Sales` 和 `Product` 之间的关系改成了「双向」，说这样切片器更好用。这样做有什么风险？有更好的替代办法吗？", r"""
风险：筛选会沿两个方向传播，可能产生**歧义路径**、让某些度量值结果不符合预期，并增加查询开销。替代办法：保持单向，需要时只在某个度量值里用 `CROSSFILTER` 局部启用双向；或者把「只显示有数据的值」的需求用视觉对象级筛选来实现。
"""),
  THINK("**（联系后续）** 下一节你会学 `CALCULATE` 和时间智能。如果日期表里 2026-02-28 的下一行是 2026-03-02（缺一天），`SAMEPERIODLASTYEAR` 这类函数会出什么问题？", r"""
时间智能函数要求日期列**连续、无缺口**，否则 Power BI 无法把日期表标记成日期表，函数也可能返回错误或不完整的结果。所以要建一张覆盖全范围、每天一行的日历（`CALENDAR` 生成），并标记为日期表。
"""),
  KW(("星型模型","star schema","事实表居中，维度表围绕，一对多筛选"),
     ("事实表","fact table","每行一个事件，键加数值"),
     ("维度表","dimension table","描述性属性，键唯一"),
     ("雪花模型","snowflake schema","维度又拆成多张表；通常尽量避免"),
     ("基数","cardinality","关系两端键的唯一性：一对多 / 一对一 / 多对多"),
     ("交叉筛选方向","cross-filter direction","筛选沿关系传播的方向：单向或双向"),
     ("激活关系","active relationship","两张表之间默认生效的那一条"),
     ("非激活关系","inactive relationship","虚线，需要 USERELATIONSHIP 才生效"),
     ("角色扮演维度","role-playing dimension","一个维度在事实表中扮演多个角色，如下单和发货日期"),
     ("日期表","date table","每天一行、日期连续的日历，需标记"),
     ("计算列","calculated column","刷新时逐行计算并存储"),
     ("度量值","measure","查询时按筛选上下文计算，不占存储"),
     ("计算表","calculated table","用 DAX 生成的表"),
     ("按列排序","Sort by column","让一列按另一列的顺序排，如月份名按月份数"),
     ("数据类别","data category","声明列的含义，如城市、网址"),
  ),
 ],
 "references": [
  PL_STUDY_GUIDE,
  {"title": "Microsoft Learn：Understand star schema and the importance for Power BI", "url": "https://learn.microsoft.com/en-us/power-bi/guidance/star-schema", "note": "星型模型的官方指南，包含维度与事实表的设计建议"},
  {"title": "Microsoft Learn：Set and use date tables in Power BI Desktop", "url": "https://learn.microsoft.com/en-us/power-bi/guidance/model-date-tables", "note": "日期表要求与标记方法"},
  {"title": "Microsoft Learn：Active vs inactive relationship guidance", "url": "https://learn.microsoft.com/en-us/power-bi/guidance/relationships-active-inactive", "note": "角色扮演维度与 USERELATIONSHIP"},
  {"title": "Chandoo：Learn Data Modelling & Star Schema for Power BI in 20 minutes（选看，22 分钟）", "url": "https://www.youtube.com/watch?v=4ePNrdxWtY0", "note": "我只核实过存在，内容没看过"},
 ],
 "quiz": {"questions": [
  Q("星型模型里，维度表和事实表之间最合适的关系是：",
    ["一对多，单向（维度筛选事实）", "多对多，双向", "一对一，双向", "维度表之间互相连接"], 0,
    "维度是「一」端、事实是「多」端，单向从维度筛选到事实。多对多和双向只在确有需要时用。"),
  Q("事实表有 OrderDate 和 ShipDate，共用一张 Date 表。要在一个度量值里按发货日期汇总，应该：",
    ["用 CALCULATE 加 USERELATIONSHIP 激活 ShipDate 的关系", "删除 OrderDate 的关系", "把两列都放进切片器", "把 Date 表改成事实表"], 0,
    "同一时间只有一条激活关系，其余非激活；度量值里用 USERELATIONSHIP 临时激活。也可以复制日期表，各用各的。"),
  Q("要使用 TOTALYTD 等时间智能函数，日期表必须满足：",
    ["日期连续、每天一行、无空值，并标记为日期表", "只包含事实表里出现过的日期", "必须由 Power Query 生成", "不能有年份列"], 0,
    "日期表要覆盖连续的日期范围并标记；事实表日期有缺口，不能直接作为日期表。DAX 或 Power Query 都可以生成。"),
  Q("图表的月份按 April、August、December…字母顺序显示，而不是 1 月到 12 月。正确的修法是：",
    ["让月份名称列按月份数字列排序（Sort by column）", "把月份名改成数字文本", "改成度量值", "删除月份列"], 0,
    "文本列默认按字母排序，设置 Sort by column 为月份编号即可，显示的仍是月份名称。"),
  Q("毛利率应该怎样建？",
    ["度量值：先分别求利润与收入的总和，再相除", "计算列：每行算毛利率，然后求和", "计算表", "在 Power Query 里逐行算后求平均"], 0,
    "比率不能求和，各行平均也不等于总体毛利率。度量值在当前筛选上下文下先聚合分子分母，再相除。"),
 ]},
}
retarget(unit, [1, 2, 3, 0, 2])

if __name__ == '__main__':
    dump(unit, "pl300-0", "u04-model-design.json", n_questions=5)
