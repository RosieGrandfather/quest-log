"""pl300-0 第 9 节：可用性与叙事"""
from pllib import *

nb = Notebook()

C_DRILL = nb.cell('''
orders = [
    {"Region": "North", "Product": "Pen",  "Order": "O1", "Amt": 20},
    {"Region": "North", "Product": "Desk", "Order": "O2", "Amt": 300},
    {"Region": "South", "Product": "Pen",  "Order": "O3", "Amt": 25},
    {"Region": "South", "Product": "Pen",  "Order": "O4", "Amt": 15},
]

def drillthrough(selected, keep_all_filters=False, page_filters=None):
    # 钻取：把你在源视觉对象里选中的值，作为筛选传给详情页（默认只传「钻取字段」）
    rows = [o for o in orders if all(o[k] == v for k, v in selected.items())]
    if keep_all_filters and page_filters:
        rows = [o for o in rows if all(o[k] == v for k, v in page_filters.items())]
    return rows

print("从产品 = Pen 钻取:", [o["Order"] for o in drillthrough({"Product": "Pen"})])
print("再保留页面上的地区 = South:", [o["Order"] for o in drillthrough({"Product": "Pen"}, True, {"Region": "South"})])
''')

C_INTER = nb.cell('''
# 编辑交互：点击视觉对象 A 里的「South」，视觉对象 B（按产品的柱）有三种反应
data = [("North", "Pen", 20), ("North", "Desk", 300), ("South", "Pen", 40), ("South", "Desk", 100)]
click = "South"

def by_product(rows):
    out = {}
    for _, p, a in rows: out[p] = out.get(p, 0) + a
    return out

filtered = by_product([r for r in data if r[0] == click])
total    = by_product(data)
highlight = {p: (filtered[p], total[p]) for p in total}      # 总柱高不变，其中一部分被高亮

print("筛选 (Filter):   ", filtered)
print("突出显示 (Highlight): 高亮 / 总", highlight)
print("无 (None):       ", total)
''')

C_BOOK = nb.cell('''
# 书签保存的是「状态快照」：数据（筛选、切片器）、显示（视觉对象的隐藏 / 聚焦）、当前页
state = {"page": "概览", "slicer_region": None, "hidden": set(), "spotlight": None}

def make_bookmark(st, data=True, display=True, current_page=True):
    snap = {}
    if data:         snap["slicer_region"] = st["slicer_region"]
    if display:      snap["hidden"] = set(st["hidden"]); snap["spotlight"] = st["spotlight"]
    if current_page: snap["page"] = st["page"]
    return snap

def apply(st, snap): st.update(snap); return st

state["slicer_region"] = "North"; state["hidden"] = {"明细表"}
bm = make_bookmark(state)                                   # 记下「North，隐藏明细」这个视图
state["slicer_region"] = None; state["hidden"] = set()      # 之后读者随便点了点
print("点书签后:", apply(state, bm))
bm_nodata = make_bookmark({"page": "概览", "slicer_region": "South", "hidden": set(), "spotlight": None}, data=False)
print("取消「数据」后，书签里有切片器状态吗？", "slicer_region" in bm_nodata)
''')

C_A11Y = nb.cell('''
def lum(hexc):                      # WCAG 的相对亮度
    c = [int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

for fg in ("#000000", "#767676", "#999999"):
    r = contrast(fg, "#FFFFFF")
    print(fg, "在白底上对比度", round(r, 2), "→", "达到 AA（4.5:1）" if r >= 4.5 else "未达到 AA")
''')

C_APR = nb.cell('''
# 自动页面刷新：固定间隔会让每个视觉对象按时重发查询。负载 = 视觉对象数 × 每小时刷新次数 × 同时在看的人
def queries_per_hour(visuals, interval_sec, viewers):
    return visuals * (3600 // interval_sec) * viewers

print("15 个视觉对象，每 5 秒，1 人看:", queries_per_hour(15, 5, 1))
print("同样设置，20 人同时看:", queries_per_hour(15, 5, 20))
print("改为每 60 秒:", queries_per_hour(15, 60, 20))
''')

unit = {
 "id": "u09",
 "title": "可用性与讲故事：钻取、书签、交互与无障碍",
 "en": "Usability & Storytelling: Drillthrough, Bookmarks, Interactions & Accessibility",
 "minutes": 50,
 "objectives": [
  "配置**钻取 (drillthrough)** 和**自定义工具提示页 (report page tooltip)**，并说出它们各自传递了什么上下文",
  "用**编辑交互 (edit interactions)** 控制视觉对象之间是**筛选、突出显示还是无**；用**同步切片器 (sync slicers)** 跨页共享筛选",
  "用**书签 (bookmarks)** 和**选择窗格 (Selection pane)** 做视图切换和导航，说出书签保存哪些状态",
  "知道**导航按钮、页面导航器、排序、导出设置、个性化视觉对象、移动布局**各自解决什么问题",
  "按**无障碍 (accessibility)** 要求设置替代文字、Tab 键顺序、颜色对比度，并解释**自动页面刷新 (automatic page refresh)** 的两种模式与限制",
 ],
 "blocks": [
  T(r"""
### 先说这一小节要干什么

这一节是考试域 3 的第二块 **Enhance reports for usability and storytelling（让报表更易用、更会讲故事）**。清单很长，但每一项都是「**一个功能解决一个问题**」，考试就是把问题和功能连起来。我们按问题组织：**怎么往下钻、怎么控制联动、怎么保存视图、怎么让别人也能用**。

**学完它你就能看懂这几件事：**

- 「从摘要点进明细」是钻取，「鼠标悬停显示小图」是工具提示页，它们是两个不同的功能；
- 点一个视觉对象，另一个视觉对象是该被「筛选」还是「突出显示」；
- 书签到底保存了什么，为什么有时恢复后切片器没变；
- 对比度 4.5:1 是怎么算出来的；自动刷新为什么会吃掉服务器。

**本小节安排（约 50 分钟）**：导读（2 分钟）→ 钻取与工具提示（12 分钟，含两个视频）→ 交互、同步切片器、书签（14 分钟）→ 导航与布局类功能（6 分钟）→ 无障碍（6 分钟）→ 自动页面刷新（5 分钟）→ 总结（5 分钟）。

### 钻取与工具提示页

> **标准定义 · 钻取 (drillthrough) 与报表页工具提示 (report page tooltip)**
>
> **钻取**：在**详情页**上把一个或多个字段设为**钻取字段**；读者在别的页面右键某个数据点，选择**钻取**，就进入该详情页，并带着被选中的值作为筛选。详情页上会自动出现**返回按钮**。**保留所有筛选器 (Keep all filters)** 决定源页面上的其他筛选是否一起传过去。**报表页工具提示**：把一页设置成**工具提示类型**的页面（小尺寸），再在某个视觉对象的**工具提示**里选这页，悬停时就显示一个迷你图表，并带着悬停的数据点作为上下文。
>
> *English: Drillthrough sends the selected value as a filter to a detail page (with an automatic back button and a Keep all filters option); a report-page tooltip is a small tooltip-type page shown on hover with the hovered point as context.*

**白话版：「钻取是点进去，工具提示是飘出来」。** 钻取离开当前页、看完还要返回；工具提示不离开，鼠标移开就消失。
""" + C_DRILL + r"""

**读输出：** 从「产品 = Pen」钻取，详情页只显示 `O1`、`O3`、`O4`；如果同时选择**保留所有筛选器**，并且源页面还有「地区 = South」，就只剩 `O3` 和 `O4`。
"""),
  V("BbplhqDCWOM", "How to use Drill Through in Power BI. ONE click from chart to details", 10),
  V("npaQ42K1sTs", "How to create Tooltip Pages in Power BI - Easy Tutorial", 5),
  T(r"""
> 两个视频（Leila Gharani 约 10 分钟讲钻取；Chandoo 约 5 分钟讲工具提示页）。**我只核实了它们存在且可嵌入，内容没有看过**；看的时候抓一个问题：**钻取字段放在哪一页？**（答案：放在详情页上）

### 编辑交互、同步切片器与书签

> **标准定义 · 编辑交互 (edit interactions)**
>
> 默认情况下，在一个视觉对象里点击数据点，同页的其他视觉对象会**交叉筛选**或**交叉突出显示**。用 **格式 → 编辑交互** 可以为每个目标视觉对象单独设置三种行为：**筛选 (Filter)**——只显示相关数据；**突出显示 (Highlight)**——总量不变，把相关的一部分高亮；**无 (None)**——不受影响。
>
> *English: Edit interactions sets, per target visual, whether a click filters, highlights or does nothing.*

**白话版：「点一下，别的图怎么反应，你说了算」。**
""" + C_INTER + r"""

**读输出：** 点击 South 之后：**筛选**时，产品柱变成 `Pen 40、Desk 100`；**突出显示**时总数仍是 `Pen 60、Desk 400`，其中被高亮的是 `40` 和 `100`；**无**时保持不变。

> **标准定义 · 同步切片器 (sync slicers)**
>
> **视图 → 同步切片器**窗格里，你可以让**同一个切片器**在多个页面上保持同步（两个复选框：**同步**与**可见**）；在一页选了值，其他页同步的切片器也跟着变，不必每页各设一个。
>
> *English: The Sync slicers pane lets one slicer's selection apply across pages, and control on which pages it is visible.*

> **标准定义 · 书签 (bookmark) 与选择窗格 (Selection pane)**
>
> **书签**保存报表页的一个**状态快照**：**数据**（筛选、切片器、排序和钻取状态）、**显示**（视觉对象的显示 / 隐藏、聚焦模式 / 突出显示）、**当前页**；并可选择应用到**所有视觉对象**还是**选中的视觉对象**。**选择窗格**列出页面上所有对象，可以显示 / 隐藏、重命名、调整图层顺序；它与书签配合就能做**视图切换**（比如用按钮在「图」和「表」之间切换）和**导航**。
>
> *English: A bookmark captures a snapshot of data state, display state and current page; the Selection pane shows, hides and orders objects; together they enable view toggles and navigation buttons.*

**白话版：「拍张照，需要时回到这张照」。** 你可以勾选「数据」、「显示」、「当前页」决定拍进去什么：
""" + C_BOOK + r"""

**读输出：** 书签记下了「North、隐藏明细表」；读者点乱之后点书签，状态恢复为 `slicer_region: North`、`hidden: {'明细表'}`。**如果取消勾选「数据」**，书签里就没有切片器状态（`False`）——这就是为什么「恢复了显示但切片器没变」：因为你没把「数据」拍进去。

**其他功能一句话对应：**

| 功能 | 解决的问题 |
|---|---|
| **按钮 / 页面导航器 (page navigator)** | 给读者明确的跳转路径，隐藏默认页签 |
| **排序 (sorting)** | 视觉对象右上角「更多选项」改变排序字段与方向；月份用「按列排序」 |
| **导出设置 (export settings)** | 在发布到服务的报表设置里，控制读者能导出汇总数据还是明细数据，或不能导出 |
| **个性化视觉对象 (personalization)** | 读者可以在不改作者版本的前提下，自己换图表类型、字段 |
| **移动布局 (mobile layout)** | 在视图里单独设计手机竖屏的排布，不影响桌面版 |
| **主题** | 统一视觉风格（上一节） |

### 无障碍

> **标准定义 · 无障碍设计 (accessible report design)**
>
> 让使用辅助技术（屏幕阅读器、键盘）和有视觉障碍的读者也能用报表：给视觉对象设置**替代文字 (alt text)**，设置合理的**Tab 键顺序**，装饰性对象标记为装饰，**标题 (title)** 清楚，颜色**对比度**要达标（WCAG AA 的正文要求至少 **4.5:1**），不要只靠颜色表达含义，并用**主题 / 高对比度**。
>
> *English: Accessible reports have alt text, a sensible tab order, clear titles, sufficient colour contrast (WCAG AA: at least 4.5:1 for text) and do not rely on colour alone.*

**白话版：「眼睛看不见、手不用鼠标，也能读懂」。** 对比度是可以算的：
""" + C_A11Y + r"""

**读输出：** 黑字在白底上的对比度是 21:1，非常高；`#767676` 是 4.54，刚好达标；`#999999` 只有 2.85，**不达标**。所以灰色的小字不适合做关键信息。

### 自动页面刷新

> **标准定义 · 自动页面刷新 (automatic page refresh)**
>
> 让**当前页**的视觉对象按设定间隔自动重新查询。两种类型：**固定间隔 (Fixed interval)**——每隔 N 秒、分、小时；**变化检测 (Change detection)**——定期检查一个度量值，**只有值变化才刷新**。它**只适用于 DirectQuery 数据源**（变化检测也有对应的限制），而且受**管理员设置的最小间隔**约束。
>
> *English: Automatic page refresh re-queries the page at a fixed interval or on change detection; it applies to DirectQuery sources and is bounded by the admin's minimum interval.*

**白话版：「自己定时刷新这一页」，但每次刷新都是真实的查询：**
""" + C_APR + r"""

**读输出：** 15 个视觉对象每 5 秒刷新，一个人看每小时就是 10,800 次查询；20 个人同时看，是 216,000 次；改为每 60 秒，降到 18,000 次。**这是课程的简化估算**，不是微软的计费，但它说明为什么要用变化检测、把间隔设得合理。

### 这一小节你要带走的三句话

1. **钻取（点进去，字段设在详情页）、工具提示页（悬停显示）、编辑交互（筛选 / 突出显示 / 无）、同步切片器（跨页共享）**：每一个功能对应一个场景。
2. **书签是状态快照**：数据 + 显示 + 当前页；配合选择窗格做视图切换。
3. **无障碍看四件事**：替代文字、Tab 顺序、对比度（≥ 4.5:1）、不靠颜色；自动页面刷新只适用于 DirectQuery，间隔太短会放大负载。
"""),
  THINK("**（场景判断）** 读者在摘要页看到「产品销售额」条形图，想点某个产品，跳到一个有订单明细的页面，并带着这个产品。要怎么配置？", r"""
建一个**详情页**，把「产品」字段拖到该页的**钻取字段**区；读者在摘要页右键条形图里的某个产品，选**钻取 → 详情页**，就带着该产品进入。详情页会自动有返回按钮。如果源页面还有切片器筛选并希望一起带过去，打开**保留所有筛选器**。
"""),
  THINK("**（概念辨析）** 一个书签应用后，视觉对象的显示 / 隐藏恢复了，但切片器仍是读者自己选的值。最可能是哪里设置的？", r"""
创建书签时**取消了「数据」**（只保存了「显示」）。「数据」选项决定书签是否保存筛选器、切片器和排序等状态。要连切片器一起恢复，需要勾选「数据」，并重新更新这个书签。
"""),
  THINK("**（联系后续）** 一份 DirectQuery 的运营看板，要每 5 秒自动刷新，部署后服务器很慢。结合上面的计算和第 7 节，你有哪几种改法？", r"""
①把间隔拉长（如 60 秒）；②改用**变化检测**，只在数据变化时才刷新；③减少该页的视觉对象数量；④用 Performance Analyzer 找出最慢的视觉对象，优化其 DAX 或数据源；⑤对热点表考虑聚合或导入。同时要知道管理员对最小间隔有限制。
"""),
  KW(("钻取","drillthrough","带着选中的值进入详情页"),
     ("钻取字段","drillthrough field","设在详情页上，决定能钻取什么"),
     ("工具提示页","report page tooltip","悬停时显示的迷你报表页"),
     ("编辑交互","edit interactions","设置视觉对象间的筛选 / 突出显示 / 无"),
     ("突出显示","highlight","保持总量，高亮相关部分"),
     ("同步切片器","sync slicers","让一个切片器跨页面保持一致"),
     ("书签","bookmark","报表状态的快照：数据、显示、当前页"),
     ("选择窗格","Selection pane","管理页面对象的显示、命名和图层"),
     ("页面导航器","page navigator","自动生成的页面跳转按钮组"),
     ("导出设置","export settings","控制读者能导出汇总还是明细数据"),
     ("个性化视觉对象","personalize visuals","读者自己调整图表类型和字段"),
     ("移动布局","mobile layout","手机竖屏的单独排布"),
     ("替代文字","alt text","给屏幕阅读器读的描述"),
     ("对比度","contrast ratio","WCAG AA 正文要求至少 4.5:1"),
     ("自动页面刷新","automatic page refresh","按间隔或变化检测刷新当前页，用于 DirectQuery"),
  ),
 ],
 "references": [
  PL_STUDY_GUIDE,
  {"title": "Microsoft Learn：Use drillthrough in Power BI Desktop", "url": "https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-drillthrough", "note": "钻取的设置与保留所有筛选器"},
  {"title": "Microsoft Learn：Use bookmarks to share insights and build stories", "url": "https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-bookmarks", "note": "书签保存的状态与选项"},
  {"title": "Microsoft Learn：Create accessible Power BI reports", "url": "https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-accessibility-creating-reports", "note": "无障碍报表的做法：替代文字、Tab 顺序、对比度等"},
  {"title": "Microsoft Learn：Automatic page refresh in Power BI", "url": "https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-automatic-page-refresh", "note": "固定间隔与变化检测，及限制"},
  {"title": "Microsoft Learn：Create tooltips based on report pages", "url": "https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-tooltips", "note": "报表页工具提示"},
 ],
 "quiz": {"questions": [
  Q("要让读者从摘要页右键某个产品，进入带着该产品的订单明细页。钻取字段应放在：",
    ["详情页上", "摘要页的切片器里", "每个视觉对象的工具提示里", "书签里"], 0,
    "钻取字段设置在**详情页**，读者在别的页的视觉对象里右键数据点，选钻取，就带着选中的值进入详情页。"),
  Q("点击一个视觉对象后，希望另一个柱形图保持总高度，只把相关的那部分高亮。应将交互设置为：",
    ["突出显示（Highlight）", "筛选（Filter）", "无（None）", "钻取"], 0,
    "突出显示保持总量，把相关部分高亮；筛选会只显示相关数据；无则不受影响。"),
  Q("书签应用后，视觉对象显示 / 隐藏恢复了，但切片器没变。最可能是因为创建书签时：",
    ["取消了「数据」选项", "取消了「当前页」选项", "使用了选择窗格", "页面用了移动布局"], 0,
    "「数据」选项决定是否保存筛选器和切片器状态。取消它，书签就只恢复显示状态。"),
  Q("按 WCAG AA 的要求，正文文字与背景的对比度至少应为：",
    ["4.5 : 1", "2 : 1", "10 : 1", "21 : 1"], 0,
    "AA 对正文要求至少 4.5:1；21:1 是黑白对比的最大值，不是要求。"),
  Q("关于自动页面刷新（automatic page refresh），哪项正确？",
    ["适用于 DirectQuery 数据源，有固定间隔和变化检测两种类型", "适用于所有导入数据源，且无限制", "只能手动触发", "会同时刷新整个工作区"], 0,
    "自动页面刷新针对当前页，只适用于 DirectQuery，有固定间隔和变化检测两种类型，间隔受管理员设置的最小值限制。"),
 ]},
}
retarget(unit, [1, 0, 2, 3, 1])

if __name__ == '__main__':
    dump(unit, "pl300-0", "u09-storytelling.json", n_questions=5)
