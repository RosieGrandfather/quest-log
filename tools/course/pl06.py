"""pl300-0 第 6 节：时间智能、半可加度量值与计算组"""
from pllib import *

nb = Notebook()

C_TI = nb.cell('''
# 每月销售额：2025 与 2026（示例数字）
m25 = [100, 110, 120, 90, 95, 105, 130, 125, 115, 100, 140, 160]
m26 = [112, 118, 130, 100, 104, 112, 0, 0, 0, 0, 0, 0]     # 到 6 月为止
month = 6                                                  # 当前上下文：2026 年 6 月

ytd = sum(m26[:month])                                     # TOTALYTD / DATESYTD
ly_same_month = m25[month - 1]                             # SAMEPERIODLASTYEAR（单月）
ly_ytd = sum(m25[:month])                                  # 去年同期 YTD
mov3 = sum(m26[month - 3:month]) / 3                       # 3 个月移动平均（DATESINPERIOD）
print("2026 YTD:", ytd, "  去年同期 YTD:", ly_ytd, "  同比:", f"{(ytd - ly_ytd) / ly_ytd:.1%}")
print("6 月:", m26[month - 1], "  去年 6 月:", ly_same_month)
print("3 个月移动平均（4–6 月）:", round(mov3, 1))
''')

C_SEMI = nb.cell('''
# 库存是「半可加」：跨产品可以加，跨时间不能加；跨时间要取期末（最后一个有数据的日期）
stock = {                       # {日期: {产品: 库存}}
    "2026-01-31": {"A": 50, "B": 20},
    "2026-02-28": {"A": 40, "B": 25},
    "2026-03-31": {"A": 45, "B": 30},
}
dates = sorted(stock)
print("跨产品相加（可加）:", {d: sum(stock[d].values()) for d in dates})
print("跨时间直接相加（错）:", sum(sum(stock[d].values()) for d in dates))
last = dates[-1]                                            # LASTNONBLANK / LASTDATE
print("期末库存（对）:", sum(stock[last].values()), "，日期", last)
''')

C_CG = nb.cell('''
# 计算组：把「时间变换」写一次，对任何基础度量值都适用（SELECTEDMEASURE() 就是那个基础度量值）
measures = {"Sales": lambda m: m26[m - 1], "Orders": lambda m: [20, 22, 25, 18, 19, 21][m - 1]}
items = {
    "Current": lambda f, m: f(m),
    "YTD":     lambda f, m: sum(f(i) for i in range(1, m + 1)),
    "Prior month": lambda f, m: f(m - 1),
}
for iname, item in items.items():
    print(iname.ljust(12), {mname: item(f, 6) for mname, f in measures.items()})
n, k = 10, 4
print(f"{n} 个度量值 × {k} 种时间变换：手写 {n * k} 个，用计算组只写 {n + k} 个")
''')

C_STAT = nb.cell('''
import statistics as st
amt = {"Ann": 120, "Bob": 80, "Cy": 200, "Di": 80, "Ed": 200}

print("平均:", st.mean(amt.values()), " 中位数:", st.median(amt.values()))
print("样本标准差 STDEV.S:", round(st.stdev(amt.values()), 2), " 总体标准差 STDEV.P:", round(st.pstdev(amt.values()), 2))

def rank(values, dense):                                    # RANKX 的并列处理：默认 Skip（并列后跳号），Dense 不跳号
    ordered = sorted(set(values.values()), reverse=True)
    if dense: return {k: ordered.index(v) + 1 for k, v in values.items()}
    return {k: 1 + sum(1 for o in values.values() if o > v) for k, v in values.items()}

print("RANKX（Skip）:", rank(amt, False))
print("RANKX（Dense）:", rank(amt, True))
print("TOPN(3) 的名字:", sorted(amt, key=lambda k: (-amt[k], k))[:3])
''')

unit = {
 "id": "u06",
 "title": "时间智能、半可加度量值与计算组",
 "en": "Time Intelligence, Semi-Additive Measures & Calculation Groups",
 "minutes": 45,
 "objectives": [
  "用 **`TOTALYTD`、`SAMEPERIODLASTYEAR`、`DATEADD`、`DATESINPERIOD`** 写出 YTD、同比和移动平均，并解释它们为什么依赖日期表",
  "识别**半可加度量值 (semi-additive measure)**（如库存、余额），用 **`LASTDATE` / `LASTNONBLANK`** 取期末值",
  "用 **`MEDIAN`、`STDEV.S`、`RANKX`、`TOPN`** 做基础统计，并知道 `RANKX` 的并列处理",
  "说明**计算组 (calculation group)** 解决了什么问题，能读懂 `SELECTEDMEASURE()`",
  "知道**快速度量值 (quick measure)** 是怎么生成 DAX 的，以及计算列、计算表在什么场景用",
 ],
 "blocks": [
  T(r"""
### 先说这一小节要干什么

上一节你有了「筛选上下文」这个模型。**时间智能就是 `CALCULATE` 的一个特殊用法：把日期筛选换成另一批日期**。这一节把考试大纲里 Model 域 DAX 部分的剩余内容一起收了：时间智能、**半可加**度量值、基础统计、**计算组**、快速度量值、计算列与计算表。

**学完它你就能看懂这几件事：**

- `TOTALYTD`、`SAMEPERIODLASTYEAR` 到底把筛选改成了什么；
- 为什么「月末库存」跨三个月加起来是错的，该怎么取；
- 为什么 10 个度量值 × 4 种时间对比，不需要写 40 个度量值；
- Quick measure 生成的 DAX 能不能直接信。

**本小节安排（约 45 分钟）**：导读（2 分钟）→ 时间智能（10 分钟）→ 视频（8 分钟）→ 半可加（6 分钟）→ 统计（6 分钟）→ 计算组与快速度量值（10 分钟）→ 总结（3 分钟）。

### 时间智能：把日期换一批

> **标准定义 · 时间智能函数 (time intelligence functions)**
>
> 一组在**日期列**上修改筛选上下文的 DAX 函数，需要一张**连续、已标记**的日期表。**累计到今天**：`TOTALYTD / TOTALQTD / TOTALMTD`（或表函数 `DATESYTD` 等，配合 `CALCULATE`）。**去年同期**：`SAMEPERIODLASTYEAR`，或更通用的 `DATEADD ( 'Date'[Date], -1, YEAR )`。**一段时间**：`DATESBETWEEN`、`DATESINPERIOD ( 日期列, 起点, 数量, 单位 )`（常用于**移动平均**）。财年不是 12 月底结束时，`TOTALYTD` 可以加第三个参数写年结日（如 `"3/31"`）。
>
> *English: Time-intelligence functions change the date filter in context (YTD, same period last year, windows); they need a contiguous, marked date table, and TOTALYTD accepts a fiscal year-end date.*

**白话版：「CALCULATE 加上一个时间旅行」。** 比如同比：
""" + C_TI + r"""

**读输出：** 2026 年 1–6 月累计 676，去年同期累计 620，同比 $(676-620)/620\approx9.0\%$；6 月当月 112 对比去年 6 月的 105；4–6 月三个月的平均是 $(100+104+112)/3\approx105.3$。对应的 DAX：

```text
Sales YTD   = TOTALYTD ( [Total Sales], 'Date'[Date] )
Sales LY    = CALCULATE ( [Total Sales], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )
Sales YoY % = DIVIDE ( [Total Sales] - [Sales LY], [Sales LY] )
Sales 3M Avg =
    AVERAGEX ( DATESINPERIOD ( 'Date'[Date], MAX ( 'Date'[Date] ), -3, MONTH ),
               CALCULATE ( [Total Sales] ) )
```

**几个考点：** 这些函数必须作用在**日期表的日期列**上，而不是事实表的日期列；日期表没标记或不连续，结果会出错；`DATESYTD`、`DATESINPERIOD` 是**返回日期表的函数**，要放进 `CALCULATE` 当筛选，而 `TOTALYTD` 是直接返回值的简写。较新的版本还有基于自定义日历的写法，本课程不展开，需要时看官方文档。
"""),
  V("-li7sxUxEqA", "Creating a simple date table in Power BI", 8),
  T(r"""
> 视频（SQLBI，约 8 分钟）讲怎样建一张简单的日期表。**我只核实了它存在且可嵌入，内容没有看过**；上一节已经讲过日期表的要求，看视频时对照一下：日期连续、标记为日期表。

### 半可加度量值：库存、余额

> **标准定义 · 半可加度量值 (semi-additive measure)**
>
> 跨**某些维度可以相加、跨另一些维度（通常是时间）不能相加**的度量值，典型是**库存数量**和**账户余额**。跨产品、仓库可以求和，跨时间应取**期末值**（或期初、平均）。常用函数：`LASTDATE`（上下文里最后一个日期）、`LASTNONBLANK`（最后一个**有数据**的日期）、`CLOSINGBALANCEMONTH / QUARTER / YEAR`。
>
> *English: A measure that adds across some dimensions but not across time (stock, balances); across time use the closing value, with LASTDATE, LASTNONBLANK or CLOSINGBALANCE.*

**白话版：「每个月的库存是一张照片，不是一股流」。** 1 月底有 70 件，2 月底有 65 件，把它们加起来说「有 210 件」毫无意义：
""" + C_SEMI + r"""

**读输出：** 同一天里 A、B 两个产品可以相加（70、65、75）；把三个月底的库存直接相加得到 210，**是错的**；期末库存是最后一个日期 2026-03-31 的 75。DAX：

```text
Closing Stock =
CALCULATE ( SUM ( Inventory[Qty] ),
            LASTNONBLANK ( 'Date'[Date], CALCULATE ( COUNTROWS ( Inventory ) ) ) )
```

用 `LASTNONBLANK` 比 `LASTDATE` 稳：期末那天没有记录时，`LASTDATE` 会得到空，`LASTNONBLANK` 会退回到**最近一个有数据的日期**。

### 基础统计与排名

> **标准定义 · 统计与排名函数**
>
> 聚合：`AVERAGE`、`MEDIAN`、`MIN`、`MAX`、`COUNT`、`DISTINCTCOUNT`；离散程度：`STDEV.S`（样本）、`STDEV.P`（总体）、`VAR.S`、`VAR.P`；排名与取前几名：`RANKX ( 表, 表达式, [值], [升降序], [并列处理] )`——并列默认 **Skip**（并列之后跳号），也可选 **Dense**（不跳号）；`TOPN ( n, 表, 表达式 )` 返回前 n 行。
>
> *English: AVERAGE, MEDIAN, STDEV.S / STDEV.P, RANKX (ties Skip by default, Dense optional) and TOPN.*

**白话版：「中位数不怕离群点，样本标准差用 n−1」。**
""" + C_STAT + r"""

**读输出：** 平均 136，中位数 120——**有一两个大值时，均值被拉高，中位数更稳**；样本标准差 60.66 比总体标准差 54.26 大，因为分母是 $n-1$ 而不是 $n$。`Cy` 和 `Ed` 并列第一时，**Skip** 把下一名排到 3（`Ann`），**Dense** 排成 2。

### 计算组与快速度量值

> **标准定义 · 计算组 (calculation group)**
>
> 一种特殊的表，里面是若干个**计算项 (calculation item)**；每个计算项用 DAX 写「如何变换**当前的度量值**」，其中 `SELECTEDMEASURE()` 指代**此刻被计算的那个度量值**。典型用途：**时间智能变换**（Current、YTD、Prior year）、币种转换、单位转换。放到矩阵的列里或切片器里，同一套计算项可以作用于**所有**度量值，不必为每个度量值各写一份。在 Desktop 里创建计算组时，通常要求启用**不鼓励隐式度量值 (Discourage implicit measures)**。
>
> *English: A calculation group is a table of calculation items; each item transforms the currently selected measure via SELECTEDMEASURE(), so one set of time-intelligence items serves every measure.*

**白话版：「一个滤镜，套在所有度量值上」。**
""" + C_CG + r"""

**读输出：** 同样的 `Current`、`YTD`、`Prior month` 三个计算项，对 `Sales` 和 `Orders` 都适用：6 月的 Sales 是 112，YTD 是 676，上月是 104；Orders 是 21、125、19。**计算组的价值是规模**：10 个度量值乘 4 种时间变换，手写 40 个，计算组只写 14 个。一个计算项在 DAX 里就是：

```text
YTD item:  CALCULATE ( SELECTEDMEASURE (), DATESYTD ( 'Date'[Date] ) )
```

**快速度量值 (Quick measure)**：在 **Home / Modeling → Quick measure** 里选一个类别（聚合、筛选器、时间智能、总计如运行总计、数学运算、文本），按提示选字段，它会**生成一个度量值**。考试的要点是：它**生成的就是普通的 DAX**，你可以读懂、修改；复杂需求仍要自己写。

**计算列与计算表的位置：** 计算列用来做**要被切片、分组、排序**的东西，也可以用 `RELATED` 取「一」端表的列；计算表常用来建日期表（`CALENDAR`）或断开的切片器表（比如「选择指标」的参数表）。**能在 Power Query 里做，就不要在 DAX 里做**：Power Query 的结果压缩得更好。

### 这一小节你要带走的三句话

1. **时间智能 = 在日期表的日期列上换一批日期**；`TOTALYTD`、`SAMEPERIODLASTYEAR`、`DATESINPERIOD`；日期表要连续并标记。
2. **库存、余额是半可加**：跨时间取期末（`LASTNONBLANK`），不能直接加。
3. **计算组用一套 `SELECTEDMEASURE()` 变换所有度量值**；Quick measure 只是 DAX 生成器；`RANKX` 并列默认 Skip。
"""),
  THINK("**（计算）** 已知 2025 年 1–6 月累计 620，2026 年同期累计 676。同比增长率是多少？如果日期表里 2025 年 3 月缺了一整个月的行，用 `SAMEPERIODLASTYEAR` 会发生什么？", r"""
$(676-620)/620\approx9.0\%$。日期表缺了行会让日期不连续，Power BI 无法把它标记成日期表，时间智能函数可能返回错误或不完整的结果，同比也就不可信。要先修日期表。
"""),
  THINK("**（概念辨析）** 一个仓库每天记录库存。报表上月份汇总该显示什么？如果用 `SUM(Inventory[Qty])`，一个月显示的值会是什么意思？", r"""
月汇总应该显示**月末（期末）库存**，比如用 `LASTNONBLANK` 或 `CLOSINGBALANCEMONTH` 取这个月最后一个有记录的日期的库存。`SUM` 会把这个月每天的库存相加，得到的数没有业务含义（「库存天数的累计」），而且月份越长越大。
"""),
  THINK("**（联系后续）** 下一节讲优化。计算组和「为每个度量值各写一组时间度量值」相比，对**模型大小**和**维护成本**各有什么影响？", r"""
度量值不占存储，所以对**模型大小**影响都不大，计算组主要的价值在**维护成本**：时间变换逻辑只写一次，改一处就对所有度量值生效，度量值的数量不会成倍膨胀，报表里的字段列表也更干净。
"""),
  KW(("时间智能","time intelligence","在日期表上改变日期筛选的 DAX 函数"),
     ("TOTALYTD","TOTALYTD","年初至今的累计，可加年结日参数"),
     ("去年同期","SAMEPERIODLASTYEAR","把日期筛选移到去年同一时段"),
     ("DATEADD","DATEADD","把日期筛选平移若干个年 / 季 / 月 / 日"),
     ("DATESINPERIOD","DATESINPERIOD","从某日起向前或向后的一段日期，用于移动平均"),
     ("半可加","semi-additive","跨时间不能直接相加，如库存、余额"),
     ("LASTNONBLANK","LASTNONBLANK","最后一个有数据的日期"),
     ("中位数","MEDIAN","排序后居中的值，不怕离群点"),
     ("样本标准差","STDEV.S","分母为 n−1"),
     ("RANKX","RANKX","排名，并列默认 Skip"),
     ("TOPN","TOPN","返回前 n 行"),
     ("计算组","calculation group","由计算项组成的表，可变换任意度量值"),
     ("SELECTEDMEASURE","SELECTEDMEASURE()","计算项里指代当前被计算的度量值"),
     ("快速度量值","quick measure","向导，帮你生成常见的 DAX 度量值"),
     ("RELATED","RELATED","在计算列里取「一」端表的列"),
  ),
 ],
 "references": [
  PL_STUDY_GUIDE,
  {"title": "Microsoft Learn：Time intelligence functions (DAX)", "url": "https://learn.microsoft.com/en-us/dax/time-intelligence-functions-dax", "note": "时间智能函数清单与说明"},
  {"title": "Microsoft Learn：Calculation groups", "url": "https://learn.microsoft.com/en-us/power-bi/transform-model/calculation-groups", "note": "计算组的官方说明与示例"},
  {"title": "Microsoft Learn：Use quick measures for common calculations", "url": "https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-quick-measures", "note": "快速度量值的类别与用法"},
  {"title": "Microsoft Learn：RANKX function (DAX)", "url": "https://learn.microsoft.com/en-us/dax/rankx-function-dax", "note": "并列处理的参数说明"},
 ],
 "quiz": {"questions": [
  Q("要算「截至当前月份的年初至今销售额」，而财年在 3 月 31 日结束，应该：",
    ["TOTALYTD ( [Sales], 'Date'[Date], \"3/31\" )", "TOTALYTD ( [Sales], Sales[OrderDate] )", "SUM ( Sales[Amount] ) 再手动筛 3 月", "SAMEPERIODLASTYEAR ( 'Date'[Date] )"], 0,
    "TOTALYTD 的第三个参数可以指定年结日。时间智能函数要作用在日期表的日期列上，而不是事实表的日期列。"),
  Q("每天记录一次仓库库存。月度报表要显示的合适度量值是：",
    ["期末库存，如用 LASTNONBLANK 取最后一个有数据的日期", "整个月每天库存的 SUM", "整个月库存的 COUNT", "月初库存的 SUM"], 0,
    "库存是半可加度量值，跨时间取期末（或期初、平均），跨产品可以相加。把每天的库存加起来没有业务含义。"),
  Q("用一个计算组为 20 个度量值同时提供 Current / YTD / Prior year 三种视图，关键写法是：",
    ["在计算项里用 SELECTEDMEASURE() 指代当前度量值", "为每个度量值各写三个度量值", "把度量值改成计算列", "用切片器筛选日期表"], 0,
    "SELECTEDMEASURE() 代表此刻被计算的度量值，所以一套计算项能作用于所有度量值，而不是 60 个手写的度量值。"),
  Q("某数据集中 Cy 和 Ed 并列第一。RANKX 默认并列处理下，下一名（Ann）的名次是：",
    ["3", "2", "1", "空"], 0,
    "默认的并列处理是 Skip：并列之后跳号，所以下一名是 3。选 Dense 才是 2。"),
  Q("关于快速度量值（Quick measure），哪项正确？",
    ["它会生成一个普通的 DAX 度量值，你可以查看并修改", "它生成的是不可修改的隐藏对象", "它只能用于计算列", "它总是比手写的 DAX 更快"], 0,
    "快速度量值是向导，产出就是 DAX 度量值，可以读、改。它不保证性能最优，复杂需求仍需要自己写。"),
 ]},
}
retarget(unit, [1, 3, 0, 2, 3])

if __name__ == '__main__':
    dump(unit, "pl300-0", "u06-time-intel.json", n_questions=5)
