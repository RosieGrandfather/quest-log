"""pl300-0 第 10 节：识别模式与趋势"""
from pllib import *

nb = Notebook()

C_BIN = nb.cell('''
ages = [19, 23, 24, 31, 33, 35, 38, 42, 44, 47, 51, 58, 62, 64]
size = 10                                              # 箱大小 (bin size)：Power BI 里在字段上右键「新建组」→ 选「箱」

bins = {}
for a in ages:
    start = (a // size) * size
    bins[f"{start}-{start + size - 1}"] = bins.get(f"{start}-{start + size - 1}", 0) + 1
print(dict(sorted(bins.items())))
''')

C_KM = nb.cell('''
# 聚类 (clustering)：把二维点分成 k 组。这里用最朴素的 k-means，初始中心固定，结果可复现
pts = [(1, 1), (1.5, 2), (2, 1.2), (8, 8), (9, 9), (8.5, 7.5), (1, 8), (2, 9)]
centers = [(1, 1), (8, 8), (1, 8)]

def d2(a, b): return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

for _ in range(5):
    groups = {i: [] for i in range(3)}
    for p in pts:
        groups[min(range(3), key=lambda i: d2(p, centers[i]))].append(p)
    centers = [(sum(x for x, _ in g) / len(g), sum(y for _, y in g) / len(g)) for g in groups.values()]
print({i: len(g) for i, g in groups.items()}, [tuple(round(c, 1) for c in ce) for ce in centers])
''')

C_ANOM = nb.cell('''
import statistics as st
sales = [100, 104, 98, 102, 101, 150, 99, 103, 97, 100]       # 第 6 个月有个尖峰

mean, sd = st.mean(sales), st.stdev(sales)
z = [round((x - mean) / sd, 2) for x in sales]
print("z 分数:", z)
for sens in (3.0, 2.0, 1.0):                                  # 灵敏度越高，阈值越小，被标为异常的越多
    print(f"阈值 {sens}σ → 异常月份:", [i + 1 for i, v in enumerate(z) if abs(v) >= sens])
''')

C_FORE = nb.cell('''
# 预测 (forecast)：这里用 Holt 线性指数平滑做教学演示；Power BI 官方文档提到的是指数平滑类算法
y = [100, 108, 115, 124, 130, 139, 146, 155]
alpha, beta = 0.5, 0.3
level, trend = y[0], y[1] - y[0]
for v in y[1:]:
    prev = level
    level = alpha * v + (1 - alpha) * (level + trend)
    trend = beta * (level - prev) + (1 - beta) * trend
print("下 3 期预测:", [round(level + (h + 1) * trend, 1) for h in range(3)])
''')

C_INFL = nb.cell('''
# 关键影响因素的直觉：某个取值让目标出现的概率比总体高多少（提升度 lift）
customers = [("月付", 1), ("月付", 1), ("月付", 0), ("月付", 1), ("年付", 0), ("年付", 0), ("年付", 1), ("年付", 0), ("年付", 0), ("年付", 0)]
overall = sum(c for _, c in customers) / len(customers)
for plan in ("月付", "年付"):
    rows = [c for p, c in customers if p == plan]
    rate = sum(rows) / len(rows)
    print(f"{plan}: 流失率 {rate:.0%}（总体 {overall:.0%}），提升度 {rate / overall:.2f}×")
''')

unit = {
 "id": "u10",
 "title": "识别模式与趋势：分组、聚类、AI 视觉对象、预测与异常",
 "en": "Identify Patterns & Trends: Grouping, Clustering, AI Visuals, Forecasting & Anomalies",
 "minutes": 40,
 "objectives": [
  "用**分组 (grouping)** 和**分箱 (binning)** 把连续值或类别整理成可分析的组，知道**箱大小**的含义",
  "说出**聚类 (clustering)** 在散点图里做什么，并区分**关键影响因素 (Key influencers)**、**分解树 (Decomposition tree)** 和**问答 (Q&A)** 视觉对象各解决什么问题",
  "用**分析窗格 (Analytics pane)** 添加**参考线、误差线和预测**，并知道预测依赖时间轴字段、会给出置信区间",
  "解释**异常检测 (anomaly detection)** 的灵敏度，以及为什么要看解释而不是只看红点",
  "知道右键的 **Analyze（分析）→ 解释增长 / 下降** 和 Copilot 的**总结语义模型**能做什么",
 ],
 "blocks": [
  T(r"""
### 先说这一小节要干什么

考试域 3 的第三块是 **Identify patterns and trends（识别模式和趋势）**：不是画图，而是**让工具帮你发现图后面的故事**。这一节的所有功能都在报表里「点一下」就能用，所以考试只问两件事：**这个功能是做什么的**，以及**在什么场景用哪一个**。

**学完它你就能看懂这几件事：**

- 「年龄」这种连续值怎么变成「20–29、30–39」这样的组；
- 「为什么这个月销量掉了」这类问题，用哪个视觉对象来问；
- 预测线灰色的那一片是什么；
- 异常检测为什么有时一个红点也没有。

**本小节安排（约 40 分钟）**：导读（2 分钟）→ 分组、分箱、聚类（9 分钟）→ AI 视觉对象与 Analyze（9 分钟）→ 分析窗格：参考线与预测（10 分钟）→ 异常检测（7 分钟）→ 总结（3 分钟）。

### 分组、分箱与聚类

> **标准定义 · 分组 (grouping)、分箱 (binning) 与聚类 (clustering)**
>
> **分组**：把类别字段里的若干取值合并成一个组（如把几个城市合成「东区」）；**分箱**：把**数值或日期字段**按**箱大小 (bin size)** 切成等宽的区间，用来做**直方图**；两者都在字段上**右键 → 新建组**。**聚类**：在**散点图**上，由 Power BI **自动**把相似的点分成若干**簇**（可指定簇的数量），并把结果作为一个新字段用作图例或筛选。
>
> *English: Grouping combines category values; binning splits numeric or date fields into equal-width intervals (bin size); clustering automatically finds groups of similar points on a scatter chart.*

**白话版：「分组靠你定规矩，聚类靠算法找规律」。** 分箱就是画直方图的前一步：
""" + C_BIN + r"""

**读输出：** 14 个年龄按 10 岁一个箱，`10-19` 有 1 个，`30-39` 最多（4 个），其余依次。箱大小一变，直方图的形状就变，所以**箱大小是要试几个的参数**。

聚类的直觉（用最朴素的 k-means）：
""" + C_KM + r"""

**读输出：** 8 个点被分成 3 个簇，大小是 3、3、2，簇中心稳定在大约 `(1.5, 1.4)`、`(8.5, 8.2)`、`(1.5, 8.5)`。这只是原理演示；在 Power BI 里是**在散点图上直接生成**，你不用写代码，但要知道**聚类是无监督的**，簇没有现成的名字，需要你自己解释。

### AI 视觉对象与 Analyze

> **标准定义 · 关键影响因素、分解树与问答视觉对象**
>
> **关键影响因素 (Key influencers)**：选一个**目标**（如「流失」），它分析哪些字段的哪些取值最能**提高或降低**目标出现的可能性，并给出影响的大小。**分解树 (Decomposition tree)**：从一个度量值出发，**按你选的（或 AI 建议的）维度逐层拆解**，看贡献来自哪里。**问答 (Q&A)**：用自然语言提问，直接生成视觉对象。**智能叙述 (smart narrative)**：自动生成要点文字。**Analyze（分析）**：右键图表上的数据点，选择**分析 → 解释增长 / 解释下降**（Explain the increase / decrease），Power BI 会给出可能的原因视觉对象。
>
> *English: Key influencers find what drives a target; the decomposition tree breaks a measure down interactively; Q&A turns questions into visuals; Analyze → Explain the increase/decrease proposes drivers for a change at a data point.*

**白话版：「会提问的图」。** 关键影响因素的直觉是**提升度 (lift)**：某个取值下目标发生的概率，比总体高了多少倍：
""" + C_INFL + r"""

**读输出：** 总体流失率 40%；「月付」客户流失率 75%，提升度 1.88 倍，是**推高**流失的因素；「年付」只有 17%，提升度 0.42 倍，是**拉低**流失的因素。关键影响因素视觉对象就是帮你把这样的结果按显著性排好。**考试要点：** 需要找「什么导致了 X」用关键影响因素；需要「逐层往下拆、看谁贡献最大」用分解树；注意它们都只表示**相关**，不是因果。
"""),
  T(r"""
### 分析窗格：参考线、误差线与预测

> **标准定义 · 分析窗格 (Analytics pane)**
>
> 选中图表后，**分析窗格**可以添加：**常量线 (Constant line)**、**最小值 / 最大值 / 平均值 / 中位数 / 百分位线**、**趋势线 (Trend line)**、**误差线 (Error bars)**（显示数据的不确定范围），以及**预测 (Forecast)**：给**以日期或数字为 X 轴的折线图**预测未来若干期，可设置**预测长度、置信区间、季节性**；预测会带一个**置信区间**（灰色带）。
>
> *English: The Analytics pane adds constant, min, max, average, median and percentile lines, trend lines, error bars and forecasts with a confidence interval, seasonality and length settings.*

**白话版：「在图上加辅助线，再让图往后画一段」。** 预测的原理在这里用 Holt 指数平滑演示（Power BI 官方文档提到它用的是指数平滑一类的算法，细节以文档为准）：
""" + C_FORE + r"""

**读输出：** 从 8 期的数据看，增长越来越稳定，下 3 期预测是 `162.3、170.2、178.0`，差不多每期加 8 左右。**使用要点：** 预测适合**有规律的时间序列**，要有足够多的历史点；数据里有明显的季节性时要设置季节性；要告诉读者预测区间，而不是只给一条线。

### 异常检测

> **标准定义 · 异常检测 (anomaly detection)**
>
> 在**折线图**（X 轴是日期）上启用，Power BI 自动找出**偏离预期的点**并标出，还可以显示**解释**（可能的原因字段）。有一个**灵敏度 (Sensitivity)** 设置：灵敏度越高，被标为异常的点越多；期望范围用一个带状区域表示。
>
> *English: Anomaly detection flags points outside the expected range on a date-based line chart, with a sensitivity setting and optional explanations.*

**白话版：「平时波动范围以外的点」。** 下面用 z 分数演示灵敏度的含义：
""" + C_ANOM + r"""

**读输出：** 第 6 个月的 z 分数是 2.82，其他月份都在 ±0.6 内。阈值设成 3σ 时**一个异常也找不到**（小样本里单个尖峰的 z 分数有上限，10 个点最多约 2.85），阈值 2σ 或 1σ 才会把第 6 个月标出来。**这说明：灵敏度和样本量都会影响结果；红点只是「值得看」，要结合解释和业务判断。**

### 这一小节你要带走的三句话

1. **分组整理类别，分箱整理数值做直方图，聚类在散点图上自动分簇**；聚类的簇需要自己解释。
2. **关键影响因素找驱动因素，分解树逐层拆解，Q&A 用语言提问，Analyze 解释某个点的增减**；都不等于因果。
3. **分析窗格加参考线和预测（带置信区间），异常检测靠灵敏度**；红点和预测线都要配合业务判断。
"""),
  THINK("**（场景判断）** 经理问「为什么 7 月销售额比 6 月下降了」。你在折线图上想快速得到线索，应该怎么操作？", r"""
右键图上 7 月的数据点，选择**分析 → 解释下降**（Explain the decrease）。Power BI 会列出可能的驱动因素（如某地区、某产品类别）的视觉对象。要更系统地看贡献来源，可以再用**分解树**，从销售额出发按地区、产品逐层拆开。
"""),
  THINK("**（概念辨析）** 同事把关键影响因素的结果说成「月付客户**导致**流失」。这个结论哪里需要小心？", r"""
关键影响因素显示的是**统计上的关联**：月付客户流失率更高。它不能证明月付**导致**流失，可能有混杂因素（比如月付客户更多是新用户或价格敏感）。应说「月付与更高的流失率相关」，再用实验或更多分析去验证因果。
"""),
  THINK("**（联系后续）** 下一节开始是第 4 个域：管理和保护 Power BI。如果一个异常检测的报表被发布到服务，要让同事收到「数据出现异常」的提醒，你会用什么功能？", r"""
用**数据警报 (data alert)**：在服务里对**仪表板上的卡片 / 仪表 / KPI 磁贴**设置阈值，超过时发邮件或通知。注意数据警报是设在**仪表板磁贴**上的，不是设在报表的视觉对象上。这个会在下一节展开。
"""),
  KW(("分组","grouping","把类别取值合成一个组"),
     ("分箱","binning","把数值或日期按箱大小切成等宽区间"),
     ("箱大小","bin size","每个区间的宽度，决定直方图形状"),
     ("聚类","clustering","在散点图上自动把相似点分簇"),
     ("关键影响因素","Key influencers","找出提高或降低目标的因素"),
     ("分解树","Decomposition tree","从度量值逐层拆解贡献来源"),
     ("问答视觉对象","Q&A visual","用自然语言提问生成视觉对象"),
     ("智能叙述","smart narrative","自动生成要点文字"),
     ("解释增长 / 下降","Explain the increase / decrease","Analyze 功能，给出变化的可能原因"),
     ("分析窗格","Analytics pane","添加参考线、误差线、预测"),
     ("参考线","reference line","常量、平均值、中位数、百分位线"),
     ("误差线","error bars","显示数据的不确定范围"),
     ("预测","forecast","带置信区间和季节性设置的未来趋势"),
     ("异常检测","anomaly detection","在折线图上标出偏离预期的点"),
     ("灵敏度","sensitivity","异常检测的阈值，越高标的点越多"),
  ),
 ],
 "references": [
  PL_STUDY_GUIDE,
  {"title": "Microsoft Learn：Use the Analytics pane in Power BI Desktop", "url": "https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-analytics-pane", "note": "参考线、误差线、趋势线与预测的设置"},
  {"title": "Microsoft Learn：Key influencers visualization", "url": "https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-influencers", "note": "关键影响因素的用法与解读"},
  {"title": "Microsoft Learn：Anomaly detection in Power BI", "url": "https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-anomaly-detection", "note": "灵敏度与解释"},
  {"title": "Microsoft Learn：Use the Analyze feature", "url": "https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-insights", "note": "解释增长 / 下降"},
 ],
 "quiz": {"questions": [
  Q("你想找出「哪些因素最能提高客户流失的概率」。最合适的视觉对象是：",
    ["关键影响因素（Key influencers）", "漏斗图", "瀑布图", "卡片"], 0,
    "关键影响因素选一个目标，分析哪些字段取值最能提高或降低它。"),
  Q("要把「年龄」做成直方图，需要先对字段做什么？",
    ["新建组并选择分箱，设置箱大小", "转置", "把它改成度量值", "创建关系"], 0,
    "分箱把数值切成等宽区间，箱大小决定每个区间的宽度，再用它做直方图。"),
  Q("给折线图添加预测，下列哪项正确？",
    ["可设置预测长度、置信区间和季节性", "预测只能用于饼图", "预测不显示置信区间", "预测不需要日期或数字 X 轴"], 0,
    "预测用于以日期或数字为 X 轴的折线图，可设置长度、置信区间和季节性，并显示置信区间的灰色带。"),
  Q("异常检测的「灵敏度」调高后，通常会：",
    ["标出更多的点为异常", "标出更少的点为异常", "改变折线图的颜色", "删除预测线"], 0,
    "灵敏度越高，对偏离的容忍度越低，被标为异常的点越多。"),
  Q("在折线图上，想让 Power BI 给出「7 月为什么比 6 月下降」的线索，应：",
    ["右键数据点，选分析 → 解释下降", "新建计算组", "添加书签", "用 RANKX"], 0,
    "Analyze 功能在数据点上提供「解释增长 / 下降」，给出可能的原因视觉对象。"),
 ]},
}
retarget(unit, [2, 3, 1, 0, 3])

if __name__ == '__main__':
    dump(unit, "pl300-0", "u10-patterns.json", n_questions=5)
