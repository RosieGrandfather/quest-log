"""pl300-0 第 1 节：获取数据：连接、存储模式与参数"""
from pllib import *

nb = Notebook()

C_MODE = nb.cell('''
# 课程的简化选择器：不是微软的算法，只是把「场景 → 存储模式」的推理写成代码
def choose_mode(source_supports_dq, need_near_realtime, data_fits_in_model, in_fabric_lakehouse=False, transform_needed=True):
    if in_fabric_lakehouse and data_fits_in_model is False:
        return "Direct Lake"                    # 数据在 Fabric 的 OneLake 里，又大到不想复制
    if need_near_realtime and source_supports_dq:
        return "DirectQuery"                    # 要最新数据、数据源又能接 DirectQuery
    if not data_fits_in_model and source_supports_dq:
        return "DirectQuery"                    # 太大，装不进模型
    return "Import"                              # 默认：最快、功能最全

cases = {
    "每天早上刷新的销售报表":        dict(source_supports_dq=True,  need_near_realtime=False, data_fits_in_model=True),
    "要看仓库此刻库存，源是 SQL":    dict(source_supports_dq=True,  need_near_realtime=True,  data_fits_in_model=True),
    "几十亿行事件表，数据在 Lakehouse": dict(source_supports_dq=True, need_near_realtime=False, data_fits_in_model=False, in_fabric_lakehouse=True),
    "手工维护的 Excel 价格表":       dict(source_supports_dq=False, need_near_realtime=False, data_fits_in_model=True),
}
for name, kw in cases.items():
    print(f"{name} → {choose_mode(**kw)}")
''')

C_PARAM = nb.cell('''
# 用「参数」把环境差异抽出来：同一份查询逻辑，换参数就换数据源
params = {
    "dev":  {"Server": "sql-dev.contoso.local",  "Database": "Sales_Dev",  "StartDate": "2026-01-01"},
    "prod": {"Server": "sql-prod.contoso.local", "Database": "Sales_Prod", "StartDate": "2024-01-01"},
}

def build_query(p):
    return f"SELECT * FROM {p['Database']}.dbo.Orders WHERE OrderDate >= '{p['StartDate']}'  -- @ {p['Server']}"

for env, p in params.items():
    print(env, "→", build_query(p))
''')

C_PRIV = nb.cell('''
# 隐私级别的课程简化模型：数据能不能被「发送」到另一个数据源（比如查询折叠时把一个源的值塞进另一个源的查询）
LEVELS = {"Private": 0, "Organizational": 1, "Public": 2}

def may_send(src, dst):
    if src == "Public": return True                       # 公开数据可以送给任何源
    if src == "Organizational": return dst in ("Organizational",)   # 组织数据只能送给组织级的源
    return False                                           # 私有数据不送给任何其他源

for a in LEVELS:
    for b in LEVELS:
        if a != b:
            print(f"{a:15s} → {b:15s}: {'允许' if may_send(a, b) else '拒绝'}")
''')

unit = {
 "id": "u01",
 "title": "获取数据：连接、存储模式与参数",
 "en": "Get Data: Connections, Storage Modes & Parameters",
 "minutes": 40,
 "objectives": [
  "说出 Power BI 里 **导入 (Import)**、**DirectQuery**、**Direct Lake**、**实时连接 (Live connection)** 和 **复合模型 (Composite model)** 各自的含义，并能按场景选择",
  "知道怎样连接到**共享语义模型 (shared semantic model)**，以及它和自己导入一份数据有什么不同",
  "说明 **数据源凭据 (credentials)** 和 **隐私级别 (privacy levels)** 在哪里改、为什么会出现「防火墙」类错误",
  "会用 **参数 (parameters)** 把服务器、数据库、日期这类会变的值抽出来",
  "能解释每种选择的代价：刷新、性能、功能限制",
 ],
 "blocks": [
  T(r"""
### 先说这一小节要干什么

PL-300 的第一个考试域是 **Prepare the data（准备数据）**，占 25–30%，而它的第一步永远是**连上数据**。你已经用 Desktop 做过报表，所以「点 Get data」这个动作不用教；这一节要补的是**考试爱考的决策**：什么时候用 Import、什么时候用 DirectQuery 或 Direct Lake，连到别人发布好的语义模型意味着什么，凭据和隐私级别为什么会卡住刷新。

**学完它你就能看懂这几件事：**

- 一道场景题里「要接近实时」「数据量太大」「数据在 Fabric」分别指向哪种存储模式；
- 为什么连到共享语义模型之后，你**不能随意改它的表和关系**；
- 刷新报错提到 **privacy level（隐私级别）** 或 **credentials（凭据）** 时该去哪里改；
- 为什么公司里的 Dev / Prod 切换要用参数，而不是改查询。

**本小节安排（约 40 分钟）**：导读（2 分钟）→ 存储模式（10 分钟）→ 视频（8 分钟）→ 共享语义模型与数据源（6 分钟）→ 凭据与隐私级别（6 分钟）→ 参数（5 分钟）→ 总结与「想一想」（3 分钟）。

### 导入、DirectQuery、Direct Lake：数据放在哪里

> **标准定义 · 存储模式 (storage mode)**
>
> 存储模式决定表里的数据是**保存在 Power BI 的模型里**还是**留在数据源里按需查询**。**导入 (Import)**：数据被载入并压缩到内存里的列式引擎（VertiPaq），查询在模型内完成，数据新鲜度取决于刷新。**DirectQuery**：模型只保存元数据，每次打开或操作视觉对象时把查询发送给数据源，数据永远是源里当前的样子。**Direct Lake**：用于 Microsoft Fabric，语义模型直接读取 OneLake 里的 Delta 表，不需要「导入」一份拷贝。**双重 (Dual)** 表可以按查询情况表现为导入或 DirectQuery。同一个模型里混用多种模式称为 **复合模型 (composite model)**。
>
> *English: Import copies data into the in-memory engine; DirectQuery sends queries to the source at run time; Direct Lake reads Delta tables in OneLake directly; Dual tables behave as either; a model mixing modes is a composite model.*

**白话版：「搬回家」还是「每次去店里看」。** 导入是把货搬回自己家的仓库（最快，但要定期补货，也就是刷新）；DirectQuery 是每次都打电话问店里（永远最新，但店里慢你就慢）；Direct Lake 是店和你家在同一栋楼里，你直接从它的货架上拿（Fabric 的专属便利）。

下面的代码把这个推理写成一个小函数。**它不是微软的算法**，只是帮你把「条件 → 选择」固定成习惯：
""" + C_MODE + r"""

**读输出：** 第一个场景每天刷新就够，所以是 `Import`；第二个要看「此刻」库存且源是 SQL，所以是 `DirectQuery`；第三个数据在 Lakehouse 且太大，是 `Direct Lake`；第四个 Excel 不支持 DirectQuery，只能 `Import`。考试里的真实场景会多几个条件，但你要做的就是这一件事：**找出题目里决定性的那个词**。

**每种模式要记住的代价（考点）：**

| | 好处 | 代价 |
|---|---|---|
| Import | 最快；DAX 和 Power Query 功能最全 | 数据只和上次刷新一样新；受模型大小限制 |
| DirectQuery | 数据实时；不占模型空间 | 速度取决于数据源；部分转换和 DAX 受限；每个视觉对象都会给源发查询 |
| Direct Lake | 大数据量、接近 Import 的速度，且不用复制 | 只在 Fabric 里；有自己的限制与回退行为 |
| Live connection | 复用一个已有的模型，不重复建 | 不能改模型本身（表、关系、列），只能加报表级度量值 |

官方文档提到过的一个具体限制：DirectQuery 每个查询默认**最多返回 100 万行**。考试不会让你背数字，但「DirectQuery 的视觉对象慢、先看数据源有没有优化」这个因果链要知道。
"""),
  V("-ip7mKUdwRg", "Power BI Get Data: Choosing Import, DirectQuery, or Live Connections Explained", 8),
  T(r"""
> 视频（Guy in a Cube，8 分钟）是一个常用的 Power BI 频道，讲的是 Get Data 时怎样在导入、DirectQuery 和实时连接之间选择。**我只用工具核实了它存在且可嵌入，内容没有看过**；看的时候对照上面的表，留意他怎么描述「实时连接」，这是最容易和 DirectQuery 混淆的一个。

### 共享语义模型与其他数据源

> **标准定义 · 共享语义模型 (shared semantic model)**
>
> 一个已经发布到 Power BI 服务的语义模型（以前叫「数据集」 dataset），可以被多个报表复用。在 Desktop 里选 **OneLake catalog → Power BI semantic models** 之类的入口（不同版本菜单名略有差异）即可连接。连接后报表只负责**可视化层**：不能新增表、不能改关系；可以加**报表级度量值 (report-level measures)**。如果要在它的基础上再混入别的数据，要使用**复合模型**（对 Power BI 语义模型使用 DirectQuery）。
>
> *English: A published semantic model reused by many reports. A report connected to it owns only the visuals and report-level measures; adding other sources requires a composite model.*

**白话版：「一个口径，多份报表」。** 财务部发布一个模型，销售、运营、管理层的报表都连到它，这样「销售额」只有一个定义。代价是：**你不能擅自改它**，需要改就找模型的所有者，或者在复合模型里叠加自己的表。

**其他常见数据源（识别即可）：** 文件（Excel / CSV / JSON）、数据库（SQL Server、Azure SQL 等）、**数据流 (dataflow)**（在服务里集中做好 Power Query 的结果，供多个模型复用）、Fabric 的 Lakehouse 和 Warehouse、Web 与 SharePoint。考试里的关键词是「**多个报表需要同一份清洗好的数据**」，答案通常指向**数据流**或**共享语义模型**，而不是每个人各清洗一遍。

### 凭据与隐私级别：为什么刷新会失败

> **标准定义 · 凭据 (credentials) 与隐私级别 (privacy levels)**
>
> **凭据**是连接数据源时使用的身份（如 Windows、基本账号、组织账号、匿名）。**隐私级别**有三档：**私有 (Private)**、**组织 (Organizational)**、**公共 (Public)**，由 Power Query 用来判断：合并多个数据源时，**一个源的数据能不能被发送到另一个源**（例如查询折叠时把值嵌入给另一个源的查询），目的是防止泄露。两者都在 **数据源设置 (Data source settings)** 里改，并区分「当前文件」和「全局」权限。
>
> *English: Credentials define who connects; privacy levels (Private / Organizational / Public) control whether data from one source may be sent to another when queries combine sources.*

**白话版：「谁来开门」和「能不能把这个源的东西递给那个源」。** 凭据管开门，隐私级别管递东西。下面的代码用课程的简化规则模拟递东西的方向：
""" + C_PRIV + r"""

**读输出：** `Private` 对谁都是拒绝；`Organizational` 只允许送给同为组织级的源；`Public` 可以送给任何一方。真实的 Power Query 防火墙比这复杂，**这只是帮你记方向**：越私密，越不能往外递。

典型报错是合并一个私有的 Excel 和一个组织级的 SQL 表时，出现 `Formula.Firewall`（防火墙）错误。**修法有两类**：把各源的隐私级别设为合适的值，或者（明确知道风险、公司允许时）选择忽略隐私级别。考试给的场景一般是「合并来自不同源的数据后刷新报隐私相关的错」，答案是去 **Data source settings → Edit permissions** 设置隐私级别。

### 参数：把会变的值抽出来

> **标准定义 · 参数 (query parameter)**
>
> Power Query 里的参数是一个有名字、类型和**当前值 (current value)** 的值，可以在任何查询里引用。常用于**服务器 / 数据库名、文件路径、筛选起止日期**。参数在 **Home → Manage parameters** 里创建；发布后，可以在服务里的语义模型设置中修改参数值，而不必重新发布文件。
>
> *English: A named, typed value usable inside queries—commonly server, database, path or date cutoffs—editable later in the service without republishing.*

**白话版：「查询里的变量」。** 你不会在 20 个查询里各写一遍服务器名，而是写一个叫 `Server` 的参数，所有查询都引用它。换环境时只改一个地方：
""" + C_PARAM + r"""

**读输出：** 两个环境用的是同一个 `build_query`，唯一不同的是参数的值：服务器、数据库和起始日期。这正是「**用参数在开发 / 测试 / 生产之间切换，也用参数缩小开发时拉取的数据量**」的做法。

### 这一小节你要带走的三句话

1. **模式看代价**：Import 最快最全；DirectQuery 实时但依赖源；Direct Lake 在 Fabric 里读 Delta 表；多种混用是复合模型。
2. **共享语义模型 = 一个口径多份报表**，连上之后不改模型本身；多个人要同一份清洗结果时想到数据流或共享模型。
3. **刷新失败看两样**：凭据（谁开门）和隐私级别（能不能递数据）；会变的值放进参数。
"""),
  THINK("**（场景判断）** 零售公司要一张报表显示门店 POS 系统里「这一分钟」的交易，POS 数据库支持 DirectQuery，数据只有几百万行。选哪种存储模式？理由和代价是什么？", r"""
选 **DirectQuery**：需求是接近实时，而 Import 只能和最近一次刷新一样新（服务里的计划刷新有频率限制）。代价是每个视觉对象都要给 POS 数据库发查询，报表速度取决于数据库；部分 DAX 和 Power Query 转换在 DirectQuery 下受限，还要留意每个查询的行数上限。
"""),
  THINK("**（概念辨析）** 同事说「我连到了公司的共享语义模型，想给 Date 表加一列财年」。能直接加吗？应该怎么办？", r"""
通常**不能**：实时连接 / 连接到共享语义模型时，报表只拥有可视化层，不能改模型里的表、列和关系，只能新增**报表级度量值**。办法是：请模型所有者在源模型里加；或者建立**复合模型**，叠加自己的表来做扩展。
"""),
  THINK("**（联系后续）** 在第 8 节你会学 Performance Analyzer。如果一个 DirectQuery 报表很慢，Performance Analyzer 里「DAX 查询」这一段耗时很长，说明问题大概率在哪里？先动哪个层？", r"""
DirectQuery 下，DAX 查询时间里包含了**发送到数据源并等待返回**的时间，所以问题大概率在数据源或查询效率，而不是画图。先在数据源侧排查（索引、视图、聚合），或者考虑对重要表改用导入、做聚合表。
"""),
  KW(("存储模式","storage mode","数据放在模型里还是留在源里"),
     ("导入","Import","数据载入内存列式引擎，靠刷新更新"),
     ("DirectQuery","DirectQuery","每次交互都向数据源发查询"),
     ("Direct Lake","Direct Lake","Fabric 里直接读取 OneLake 的 Delta 表"),
     ("双重","Dual","可按查询情况表现为导入或 DirectQuery"),
     ("复合模型","composite model","一个模型里混用多种存储模式"),
     ("实时连接","live connection","连接到已有的模型，不能改模型本身"),
     ("共享语义模型","shared semantic model","发布后被多个报表复用的模型"),
     ("数据流","dataflow","服务里集中做好的 Power Query 结果，可复用"),
     ("凭据","credentials","连接数据源使用的身份"),
     ("隐私级别","privacy level","私有 / 组织 / 公共，控制数据能否被送到另一个源"),
     ("数据源设置","data source settings","修改凭据与隐私级别的地方"),
     ("参数","parameter","有名字、类型和当前值的变量，可在查询里引用"),
     ("报表级度量值","report-level measure","连到共享模型后只能新增的度量值"),
  ),
 ],
 "references": [
  PL_STUDY_GUIDE,
  {"title": "Microsoft Learn：Storage mode in Power BI Desktop", "url": "https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-storage-mode", "note": "导入 / DirectQuery / 双重 / 复合模型的官方说明"},
  {"title": "Microsoft Learn：Direct Lake overview", "url": "https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-overview", "note": "Direct Lake 的官方概述，包括它读取 OneLake 的方式"},
  {"title": "Microsoft Learn：Power BI Desktop privacy levels", "url": "https://learn.microsoft.com/en-us/power-bi/enterprise/desktop-privacy-levels", "note": "三种隐私级别的官方说明"},
  {"title": "Microsoft Learn：Power Query parameters", "url": "https://learn.microsoft.com/en-us/power-query/power-query-query-parameters", "note": "参数的创建与用法"},
 ],
 "quiz": {"questions": [
  Q("一份报表必须显示源数据库里**当前这一刻**的数据，且数据库支持 DirectQuery。最合适的存储模式是：",
    ["DirectQuery", "导入，并设置每天刷新一次", "导入，并手动刷新", "把数据导出成 Excel 再导入"], 0,
    "要求是接近实时，导入模式的数据只和最近一次刷新一样新。DirectQuery 每次交互都去查源，所以是最新的；代价是性能依赖数据源。"),
  Q("你连接到了一个已发布的共享语义模型，在报表里**还可以**做哪件事？",
    ["新增报表级度量值", "新增一张计算表", "修改表之间的关系", "删除模型里的一列"], 0,
    "连接到共享语义模型后，报表只拥有可视化层，可以新增报表级度量值，但不能改模型里的表、列和关系。想扩展需要复合模型或联系模型所有者。"),
  Q("合并一个私有的 Excel 和一个组织级的 SQL 表后，刷新报隐私相关的错误。应该首先去：",
    ["数据源设置里检查并设置隐私级别", "把 Excel 转成 CSV", "把报表改成 DirectQuery", "增加刷新频率"], 0,
    "隐私级别决定一个源的数据能否被发送到另一个源。错误提示涉及隐私时，先在 Data source settings 里设置合适的级别（或在明确风险后选择忽略）。"),
  Q("同一份 Power Query 逻辑要在开发库和生产库之间切换，最好用什么实现？",
    ["参数（服务器 / 数据库名）", "复制整个查询并手改", "改用计算列", "用书签"], 0,
    "把服务器和数据库名定义成参数，所有查询引用它，换环境时只改参数值；发布后还可以在服务里改参数，不必重新发布。"),
  Q("数据存放在 Fabric 的 Lakehouse（OneLake 的 Delta 表）里，体量很大，不想复制一份到模型。应优先考虑：",
    ["Direct Lake", "导入，每小时刷新", "实时连接到 SSAS", "把表拆成多个 Excel"], 0,
    "Direct Lake 让语义模型直接读取 OneLake 里的 Delta 表，避免导入拷贝，适合 Fabric 里的大数据量。它只适用于 Fabric 里的数据。"),
 ]},
}
retarget(unit, [2, 0, 3, 1, 2])

if __name__ == '__main__':
    dump(unit, "pl300-0", "u01-get-data.json", n_questions=5)
