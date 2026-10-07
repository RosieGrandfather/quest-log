"""pl300-0 第 2 节：数据剖析与清洗"""
from pllib import *

nb = Notebook()

C_ROWS = nb.cell('''
# 一份故意弄脏的小订单表（全是文本，和刚从 CSV 读进来时一样）
rows = [
    {"OrderID": "1001", "Region": " North ", "Qty": "5",   "Price": "12.5"},
    {"OrderID": "1002", "Region": "north",   "Qty": "N/A", "Price": "9.0"},
    {"OrderID": "1003", "Region": "South",   "Qty": "",    "Price": "7.25"},
    {"OrderID": "1003", "Region": "South",   "Qty": "",    "Price": "7.25"},
    {"OrderID": "1004", "Region": None,      "Qty": "2",   "Price": "abc"},
    {"OrderID": "1005", "Region": "NORTH",   "Qty": "8",   "Price": "11"},
]

def to_num(s):
    try: return float(s)
    except (TypeError, ValueError): return "ERROR" if s not in ("", None) else None

def profile(col):
    vals = [r[col] for r in rows]
    n = len(vals)
    empty = sum(v is None or v == "" for v in vals)
    distinct = len(set(vals))
    unique = sum(vals.count(v) == 1 for v in set(vals))
    print(f"{col:8s} 行数 {n}  空 {empty}  不同值 {distinct}  只出现一次 {unique}")

for c in ("OrderID", "Region", "Qty"):
    profile(c)
''')

C_QUAL = nb.cell('''
# 数值列：能转成数字的算 Valid，转不了的算 Error，空的算 Empty
for col in ("Qty", "Price"):
    conv = [to_num(r[col]) for r in rows]
    err = conv.count("ERROR"); emp = conv.count(None); ok = len(conv) - err - emp
    print(f"{col}: Valid {ok/len(conv):.0%}  Error {err/len(conv):.0%}  Empty {emp/len(conv):.0%}")
''')

C_CLEAN = nb.cell('''
# 清洗：trim → 统一大小写 → 去重 → 处理空值 / 错误
def clean_region(v): return None if v is None else v.strip().title()

step1 = [{**r, "Region": clean_region(r["Region"])} for r in rows]
print("清洗后的 Region:", [r["Region"] for r in step1])

seen, step2 = set(), []
for r in step1:
    key = tuple(r.values())
    if key not in seen:
        seen.add(key); step2.append(r)
print("去重后行数:", len(step2))

# 先把 N/A 之类变成 null，再转数字；剩下的 Error 行单独看
for r in step2:
    r["Qty"] = None if r["Qty"] in ("", "N/A") else to_num(r["Qty"])
    r["Price"] = to_num(r["Price"])
print([(r["OrderID"], r["Qty"], r["Price"]) for r in step2])
''')

C_DUP = nb.cell('''
# 重要陷阱：去重区分大小写。没统一大小写就去重，" North " / "north" / "NORTH" 全被当成不同的值
raw = [" North ", "north", "NORTH", "South", "South"]
print("直接去重:", len(set(raw)))
print("先 trim+lower 再去重:", len({v.strip().lower() for v in raw}))
''')

unit = {
 "id": "u02",
 "title": "数据剖析与清洗：先看清再动手",
 "en": "Profile & Clean: Look Before You Transform",
 "minutes": 40,
 "objectives": [
  "用 **列质量 (column quality)**、**列分布 (column distribution)** 和 **列剖析 (column profile)** 读出一张表的健康状况，并知道它默认只看前 1000 行",
  "区分 **空值 (null)**、**空字符串 (empty string)** 和 **错误 (error)**，并对每一类选对处理办法",
  "解决数据不一致：**修剪 (Trim)、清除 (Clean)、统一大小写、替换值、删除重复项**（以及它区分大小写这个陷阱）",
  "读懂常见的导入错误：**DataFormat.Error、Expression.Error（找不到列）、DataSource.Error**，并知道从哪一步修",
  "说出清洗应该排在**改数据类型之前还是之后**，以及为什么",
 ],
 "blocks": [
  T(r"""
### 先说这一小节要干什么

你做过报表，一定遇到过「某一列突然全是 Error」「合计和对方的数对不上」。这一节对应考试域 1 的 **Profile, clean, and transform data（剖析、清洗和转换数据）** 的前半部分：怎么**先看清**数据有什么问题，再用对应的步骤去处理。后半部分（合并、透视、事实表和维度表）放在下一节。

**学完它你就能看懂这几件事：**

- Power Query 编辑器里那几条绿色 / 灰色 / 红色小条分别在说什么；
- 为什么列里的「north / North / NORTH」去重之后还剩三行；
- 为什么改了数据类型之后冒出一堆 Error，该先改什么；
- 刷新失败写着 `Expression.Error: The column 'xxx' of the table wasn't found` 时，问题出在哪里。

**本小节安排（约 40 分钟）**：导读（2 分钟）→ 剖析工具（10 分钟）→ 空值、错误与不一致（15 分钟）→ 导入错误（8 分钟）→ 总结与「想一想」（5 分钟）。

### 数据剖析：三个工具

> **标准定义 · 数据剖析工具 (data profiling tools)**
>
> Power Query 编辑器的 **View（视图）** 选项卡里有三个开关。**列质量 (Column quality)**：每列显示 **有效 (Valid)**、**错误 (Error)**、**空 (Empty)** 三个百分比。**列分布 (Column distribution)**：每列显示 **不同值 (Distinct)** 和 **唯一值 (Unique)** 的数量，并画出分布柱形。**列剖析 (Column profile)**：选中一列后，在下方显示该列的统计（计数、错误、空、不同值、最小 / 最大 / 平均等）和值分布。**默认只基于前 1000 行**，需要时在编辑器底部状态栏切换为**基于整个数据集**。
>
> *English: Column quality shows valid / error / empty percentages; column distribution shows distinct and unique counts; column profile shows detailed statistics for one column. By default profiling is based on the first 1,000 rows unless switched to the entire data set.*

**白话版：「体检报告」。** 质量条告诉你哪一列有病，分布告诉你它重复得有多厉害，剖析给你详细化验单。**关键陷阱：默认只化验前 1000 行**，如果脏数据在第 5 万行，体检报告会显示一切正常。

注意两个容易混的词：**不同值 (distinct)** 是出现过的不同取值有多少种；**唯一值 (unique)** 是只出现过一次的值有多少个。下面用一张小表把它们算出来：
""" + C_ROWS + r"""

**读输出：** `OrderID` 有 6 行，不同值 5 个，其中只出现一次的有 4 个——因为 `1003` 出现了两次。`Region` 有 1 个空（`None`），5 个不同值（`" North "`、`north`、`South`、`None`、`NORTH`），也就是说「看起来只有两三个地区」的列，其实因为空格和大小写分裂成了 5 种。`Qty` 的 2 个空是两个空字符串。

再看**列质量**：把能转成数字的算 Valid，转不了的算 Error，空的算 Empty：
""" + C_QUAL + r"""

**读输出：** `Qty` 有 50% 有效（5、2、8）、17% 错误（`N/A` 转不成数字）、33% 空；`Price` 有 83% 有效、17% 错误（`abc`）。这就是编辑器列头下那一条绿 / 红 / 灰的由来。

### 空值、错误与不一致

> **标准定义 · 空值与错误 (null, empty and error)**
>
> **空值 (null)** 表示「没有值」；**空字符串 (empty string)** 是长度为 0 的文本，不等于 null，需要先**替换值**才会变成 null。**错误 (error)** 是某个单元格里的值在某一步计算失败了（如把 `N/A` 转成数字）；它**只影响那个单元格**，但会让汇总出错。处理办法：**替换值 (Replace values)**、**向下 / 向上填充 (Fill down / up)**、**删除空行 (Remove blank rows)**、**删除错误 (Remove errors)**、**替换错误 (Replace errors)**，或**保留错误 (Keep errors)**以便检查。
>
> *English: Null means no value; an empty string is text of length zero; an error means a step failed for that cell. Use Replace values, Fill down/up, Remove blank rows, or Remove / Replace / Keep errors.*

**白话版：「缺失、空白、算错了」是三种病，药不一样。** 缺失可以补（用上一行填充、用 0 或平均值替换）或删；空白文本要先转成 null；算错的要先弄明白**为什么错**——是 `N/A`、是千分位逗号，还是日期格式。**不要一上来就 Remove errors**：那等于悄悄把问题行从报表里删掉，合计会少，却没人发现。

**不一致**主要靠 **转换 → 格式 (Format)** 里的几个步骤：**修剪 (Trim)** 去掉两端空格；**清除 (Clean)** 去掉不可打印字符；**大写 / 小写 / 每个单词首字母大写**；再用 **替换值** 统一写法。最后才 **删除重复项 (Remove duplicates)**。

下面把这些步骤连起来：
""" + C_CLEAN + r"""

**读输出：** Trim 加首字母大写之后，`Region` 变成 `North, North, South, South, None, North`，空仍然是 `None`；`1003` 那两条完全相同的行去重后，行数从 6 变成 5。再看数值：`Qty` 里的 `N/A` 和空字符串先变成 null，再转数字，`1002` 和 `1003` 的 `Qty` 就是 `None`；`1004` 的 `Price` 因为是 `abc` 转不了，剩下一个 `ERROR`，**要单独去看，而不是直接删掉**。

一个考试常见的陷阱——**删除重复项区分大小写**：
""" + C_DUP + r"""

**读输出：** 直接去重，`" North "`、`north`、`NORTH`、`South` 是 4 个不同值；先 Trim 再统一小写，只剩 2 个。**所以顺序是：先统一写法，再去重。**

**清洗和改类型谁先？** 先清洗（把 `N/A`、空白、千分位符号处理掉），再改数据类型；否则类型转换会把这些值变成 Error。日期、小数点和千分位依赖区域设置，必要时用 **使用区域设置更改类型 (Change type using locale)**，比如把文本 `12/03/2026` 按英国（日/月/年）还是美国（月/日/年）解析，结果不同。
"""),
  T(r"""
### 导入错误：看错误信息的第一行

> **标准定义 · 常见的导入与刷新错误 (import and refresh errors)**
>
> **`DataSource.Error`**：连不上源，常见原因是文件被移动或重命名、没有权限、凭据过期。**`Expression.Error: The column 'X' of the table wasn't found`**：某一步引用了列 `X`，但源里的列名变了或没有了（例如有人改了表头）。**`DataFormat.Error`**：某个值不能按指定格式解析，如把 `abc` 转成数字。**`Formula.Firewall`**：合并多个数据源时被隐私级别拦下（见上一节）。
>
> *English: DataSource.Error means the source cannot be reached; Expression.Error "column wasn't found" means a step references a column that no longer exists; DataFormat.Error means a value cannot be parsed; Formula.Firewall means privacy levels blocked a combine.*

**白话版：「看第一行就知道该去哪一步」。** 编辑器右侧的 **应用的步骤 (Applied steps)** 会在出错的那一步旁边留下提示：点一下该步骤，就能看到它依赖的上一步。**错误的根源往往在更早的一步**，比如列被重命名，后面所有引用旧列名的步骤都会炸。

**预防办法：** 源里的表头可能会变，就尽量在 Power Query 里**最早的一步**就重命名成稳定的名字；把「提升标题」「更改类型」这类自动生成的步骤留在一个可预测的位置；需要时用参数管理文件路径（上一节）。

### 这一小节你要带走的三句话

1. **先剖析再动手**：列质量看 Valid / Error / Empty，列分布看 Distinct / Unique，列剖析给详细统计；**默认只看前 1000 行**。
2. **清洗的顺序**：Trim / Clean / 统一大小写 / 替换值 → 删除重复项 → 处理空值和错误 → 改数据类型；去重区分大小写，不要先 Remove errors 掩盖问题。
3. **错误信息第一行指路**：DataSource（连不上）、Expression（找不到列）、DataFormat（解析失败）、Formula.Firewall（隐私级别）。
"""),
  THINK("**（计算）** 一列有 1,000 行，其中 120 行是空，30 行转数字时出错，其余有效。按列质量的方式，三个百分比各是多少？如果你对这列直接 Remove errors，会对汇总有什么影响？", r"""
空 $120/1000=12\%$，错误 $30/1000=3\%$，有效 $850/1000=85\%$。直接删除错误行，这 30 行会从所有后续汇总里消失，合计偏小，却没有任何提示；应先找出出错原因（格式？特殊文本？），能修就修，不能修再决定删、置空或替换，并在报告里说明。
"""),
  THINK("**（概念辨析）** 同事说：「Region 列看起来只有 North 和 South 两个值，我去重一下就行。」但列分布显示 Distinct 是 5。可能是什么原因？正确的处理顺序是什么？", r"""
常见原因是**空格、大小写不统一**（` North `、`north`、`NORTH`）或有 null；删除重复项区分大小写，所以不会合并它们。顺序：Trim → 统一大小写（或用替换值统一写法）→ 再删除重复项 → 检查 null。
"""),
  THINK("**（联系后续）** 下一节你会用 Merge 把订单表和客户表按 `CustomerID` 合并。如果订单表里的 `CustomerID` 是文本、客户表里是整数，或者前者带有多余空格，合并会发生什么？现在清洗阶段该做什么？", r"""
两侧类型不同或有不可见的空格，匹配不上，合并后新增的列大部分是 null，看起来像「客户缺失」。清洗阶段就要把两侧的键都 Trim、统一类型（以及大小写，如果键是字母数字混合），并用列剖析确认没有 null 和重复（客户表里的键应当唯一）。
"""),
  KW(("数据剖析","data profiling","在转换前检查数据的质量和分布"),
     ("列质量","column quality","有效 / 错误 / 空 三个百分比"),
     ("列分布","column distribution","不同值与唯一值的数量及分布"),
     ("列剖析","column profile","选中列的详细统计与值分布"),
     ("不同值","distinct","出现过的不同取值有多少种"),
     ("唯一值","unique","只出现过一次的值的数量"),
     ("空值","null","没有值"),
     ("空字符串","empty string","长度为 0 的文本，不等于 null"),
     ("修剪","Trim","去掉文本两端的空格"),
     ("清除","Clean","去掉不可打印字符"),
     ("删除重复项","Remove duplicates","区分大小写"),
     ("向下填充","Fill down","用上一个非空值填充空白"),
     ("替换错误","Replace errors","把错误单元格换成指定值"),
     ("应用的步骤","Applied steps","编辑器里一步一步记录的转换序列"),
     ("区域设置","locale","决定日期、小数点和千分位的解析规则"),
  ),
 ],
 "references": [
  PL_STUDY_GUIDE,
  {"title": "Microsoft Learn：Using the data profiling tools", "url": "https://learn.microsoft.com/en-us/power-query/data-profiling-tools", "note": "三个剖析工具与「前 1000 行」默认值的官方说明"},
  {"title": "Microsoft Learn：Data types in Power Query", "url": "https://learn.microsoft.com/en-us/power-query/data-types", "note": "数据类型与「使用区域设置更改类型」；删除重复项区分大小写这一点请自己在 Desktop 里试一次验证"},
  {"title": "Microsoft Learn：Dealing with errors in Power Query", "url": "https://learn.microsoft.com/en-us/power-query/dealing-with-errors", "note": "步骤级与单元格级错误、删除 / 替换 / 保留错误"},
 ],
 "quiz": {"questions": [
  Q("Power Query 的列剖析（Column profile）默认基于多少数据？",
    ["前 1000 行", "整个数据集", "随机抽样 10%", "只看可见的行"], 0,
    "默认只基于前 1000 行，所以第 1000 行之后的脏数据可能看不到；需要时在状态栏切换为基于整个数据集。"),
  Q("一列里有 `North`、` North `、`north`，直接删除重复项，会得到什么？",
    ["三个值都保留，因为它们不完全相同", "只剩一个", "只剩两个", "报错"], 0,
    "删除重复项区分大小写，也不会忽略空格，所以三个值都被保留。应先 Trim、统一大小写，再去重。"),
  Q("一列文本里混有 `N/A`，你要把它转成整数列。更合适的做法是：",
    ["先把 `N/A` 替换成 null，再改数据类型", "直接改类型，然后删除错误行", "把整个列删掉", "保持文本，在 DAX 里转换"], 0,
    "先清洗、再改类型，避免类型转换把 `N/A` 变成 Error。直接删除错误行会悄悄丢数据，改用 DAX 转换则把本该在 Power Query 里解决的问题推后。"),
  Q("刷新报错：`The column 'Customer ID' of the table wasn't found`。最可能的原因是：",
    ["源里的列被重命名或删除，后面某一步仍引用旧列名", "没有刷新权限", "数据类型是文本", "使用了 DirectQuery"], 0,
    "这是 Expression.Error，表示某一步引用的列在上一步结果里不存在，常见于源表头改名。到出错的步骤，改成正确的列名或调整更早的步骤。"),
  Q("「列分布」里，Distinct 与 Unique 的区别是：",
    ["Distinct 是不同取值的种类数，Unique 是只出现一次的值的个数", "两者相同", "Distinct 是空值个数，Unique 是错误个数", "Unique 是不同取值的种类数，Distinct 是只出现一次的值的个数"], 0,
    "Distinct：有多少种不同的取值；Unique：只出现过一次的值有多少个。键列如果应当唯一，应该满足 Distinct 等于行数、Unique 等于行数。"),
 ]},
}
retarget(unit, [1, 3, 0, 2, 3])

if __name__ == '__main__':
    dump(unit, "pl300-0", "u02-profile-clean.json", n_questions=5)
