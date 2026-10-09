# 改动日志 (Changelog)

每次改动都记在这里，**最新的写在最上面**。规则见 README「改动日志规则」。

格式：

```
## 日期 — 一句话标题（对应的 commit 说明）
- 改了什么（用户能看到的变化）
- 改了哪些文件 / 数据结构（给之后接手的人看）
- 需要注意的（迁移、要手动做的事、已知问题）
```

---

## 2026-10-09 — 新课 ba-0：BA 入门，一个项目从头到尾（10 节，选修）
- 新课 `ba-0`，选修（`tier: elective`，`order: 17`）：u01 BA 是做什么的、u02 项目启动、u03 干系人分析、u04 需求访谈、u05 As-Is 现状、u06 写需求、u07 数据与接口、u08 方案选择、u09 UAT 与上线、u10 上线后与面试；每节 40–45 分钟，5 道测验，`direct: true`，合计 420 分钟。每节有「会议卡」（找谁开会、准备什么、问什么）和「对照你的 SOC Automation」
- 对照案例只使用简历里的事实；没有视频
- 文件：`courses/ba-0/*.json`、`course.json`，脚本 `tools/course/ba01.py`–`ba10.py`、`balib.py`；`courses/index.json` 加了 ba-0
- 需要注意：参考链接（IIBA BABOK 页面、Wikipedia）需要单独核对；BABOK 只引用概念，没有转载原文

## 2026-10-07 — 新课 pl300-0：PL-300 Power BI 数据分析师认证备考（13 节，选修）
- 新课 `pl300-0`，选修（`tier: elective`，`order: 16`）：按微软官方 PL-300 Study Guide（2026-04-20 更新版）的四个技能域整理。u01 获取数据（Import / DirectQuery / Direct Lake、共享语义模型、隐私级别、参数）、u02 剖析与清洗、u03 转换与加载（合并、逆透视、事实表与维度表）、u04 数据模型设计（星型模型、关系、日期表）、u05 DAX 与 CALCULATE、u06 时间智能 / 半可加 / 计算组、u07 性能优化、u08 创建报表（含视觉计算）、u09 可用性与叙事（钻取、书签、无障碍）、u10 模式与趋势、u11 工作区与分发、u12 安全（RLS、敏感度标签）、u13 备考路线；每节 35–50 分钟，5 道测验，`direct: true`，合计约 560 分钟
- 代码块都是用 Python 对 DAX / Power Query 语义的**模拟**（网页里能直接运行，只用标准库），不是真的 DAX / M；输出由 `Notebook` 真实运行写入。例题和测验是自己写的，不是考试真题
- 文件：`courses/pl300-0/*.json`、`course.json`，脚本 `tools/course/pl01.py`–`pl13.py`、`pllib.py`；`courses/index.json` 加了 pl300-0
- 需要注意：**视频**（Guy in a Cube、Leila Gharani、Pragmatic Works、SQLBI、Curbal、Chandoo 等 9 个）用 `yt.py verify` 核实过存在且可嵌入，**内容没有看过**；官方大纲的域和权重、及格线 700、练习评估链接来自 Microsoft Learn Study Guide，**题量、时长、费用、题型、续期规则没有核实**（课程里已写明要去官方页面确认）；计划刷新次数、DirectQuery 100 万行等具体数字按官方文档记忆写成，已标注「以官方为准」；Copilot 相关功能只讲能做什么，未实操；OMRON 租户不能创建工作区，第 11–12 节无法在服务里实操
- 已知：`validate.py --online` 对全部课程联网时会偶尔超时；pl300-0 的参考链接单独用 urllib 核对过（51 条，2 条 404 已换成可打开的链接）；`tools/course/` 里留有 `pl03_head.py`、`pl03_body.py` 两个临时文件（没有删除权限），可以手动删掉，不影响课程

## 2026-10-07 — 新功能「城邦」：项目地图（3D 小游戏，map.html）
- 主页「🗺 城邦」进入。所有项目在同一张 3D 低多边形地图上：每个项目从中央首都往外长一条随机拐弯的路，每一步（约半天）是路上的一座城，做完就点亮，整张地图越做越亮；每个项目一辆小车，选中的那辆可以自己开（键盘 WASD/方向键，手机左下摇杆），也可以点「开过去」自动开到下一站；拖动旋转、滚轮 / 双指缩放、🌍 切换上帝视角
- 模板：第一首 demo（Logic Pro，10 步，4 个阶段）、写一篇文章、做一个小工具、空白项目；步骤标题 / 说明 / 参考 / 阶段都可以改，可上移下移、增删；同时进行的项目超过 3 个会提醒，可「停放」
- 积分：点亮一座城 +50（`mapstep-项目-步骤`），一个阶段全部点亮再 +100（只在项目有多个阶段时），项目全部完成 +200；都走 `awardOnce`，重复点只发一次；取消完成不扣已发的分
- 布局稳定：城的位置只由「项目 slot + 项目 id + 第几步」决定（`cityPositions`），重开、手机电脑之间都一样；在末尾加步骤不会挪动前面的城，**在中间删 / 换顺序会让后面的城挪位置**
- 数据：`users/{uid}/projects/{id}`（title、templateId、icon、slot、color、parked、createdAt、steps[{id,title,detail,refs,stage,doneAt}]）；安全规则不用改
- 文件：`map.html`、`css/map.css`、`js/map/main.js`（界面）、`js/map/scene.js`（three.js 场景）、`js/core/map.js`（布局 / 进度 / 积分 / 模板，纯函数）、`js/data/map.js`、`tests/map.test.js`；`js/firebase.js` 加 `projects` 集合；`js/core/constants.js` 加三个小标签
- 注意：three.js r160 从 jsDelivr CDN 加载，加载失败（离线 / 公司网络拦截）会自动退回列表模式；云端用软件渲染 + 假 Firebase 测过桌面和 375 宽手机画面，没有在真实手机上测过
- 已知：外观是朴素的低多边形；参考链接目前是文字提示，没有逐条核验过的教程视频

## 2026-10-08 — 城邦：每座城不一样 + 修键盘开车
- 每座城按「阶段」配一个地标：民居 / 工坊（烟囱）/ 塔楼 / 圆顶剧场 / 集市（摊位喷泉），同一阶段里相邻的城也不同；路上最后一座城是金顶大塔。没点亮时是暗色轮廓，点亮后变亮、窗户亮灯（`addLandmark`，`js/map/scene.js`）
- 修了：新建项目弹窗关掉后输入框还占着焦点，方向键被当成在打字而失效（`typing()` 现在只认可见的输入框）
- 光晕调弱，近看不再一片白
- 列表面板里每个项目多了「换成模板步骤」：选一个模板，把项目的步骤整个换掉（名字 / 颜色 / 位置不变；标题相同的已点亮城保留，其余重置；两次点击确认；已拿的分不扣，新步骤用新 id 所以新步骤点亮会重新计分）（`js/map/main.js`、`css/map.css`）
- 新模板「把 AI demo 变成自己的歌（Suno → Logic）」13 步：选定 Master Demo、写 producer notes、拆 stems、逐轨听、找 BPM/调/和弦、画 Arrangement Map、在 Logic 里重做副歌 8 小节（鼓 / bass / 和弦 / synth hook / 人声）、对比差距、换成自己的元素（`js/core/map.js` 的 `TEMPLATES`）；顺带修了「空白项目」第二步阶段名的乱码
- 城邦质感：天空渐变 + 星星、会起伏发光的海面、飘过地面的云影；整体随点亮的城越多从深蓝夜色渐变到暖色黄昏（天色 / 海色 / 星星都跟着变）；城名和编号的字调小（`js/map/scene.js`，纯 shader，没有新增文件）

## 2026-10-07 — 新课 gre-0：GRE 普通考试每个科目到底多难（7 节，选修）
- 新课 `gre-0`，选修（`tier: elective`，`order: 15`）：u01 全景与难度地图、u02/u03 数学推理上下、u04 填空与句子等价、u05 阅读理解、u06 分析性写作、u07 备考路线与摸底；每节 35–45 分钟，5 道测验，`direct: true`
- 考试结构（作文 30 分钟；Verbal 12+15 题 18+23 分钟；Quant 12+15 题 21+26 分钟；小节级自适应）来自 ETS 官方 GRE General Test Structure；百分位、均值、标准差来自 ETS Interpretive Data Table 1A（统计期 2022-07-01 至 2025-06-30）；各科题型与范围来自 ETS 官方各科页面；POWERPREP 免费两套与付费 44.95 美元来自 ETS POWERPREP 页面（2026-10 读取）
- 例题和示例短文都是自己写的，不是 ETS 真题；数学答案都用代码核对过
- 文件：`courses/gre-0/*.json`，脚本 `tools/course/gre01.py`–`gre07.py`、`gre01c.py`、`gre02c.py`、`gre03c.py`、`gre06c.py`、`gre07c.py`；`courses/index.json` 加了 gre-0
- 需要注意：5 个视频（Magoosh、GRE Ninja、GREBooster、YMGrad）用 `yt.py verify` 核实过存在且可嵌入，但**内容没有看过**，只是按标题、频道和时长选的；「Quant 的难度」「对你的初步判断」这类判断是本课程的推理，不是 ETS 的结论；费用、成绩有效期、各项目要求没有核实；`validate.py --online` 只报了 dl-0 里一条旧链接（deeplearning.ai，返回 308），与本次无关

## 2026-10-05 — 新增「日记」板块（和记录 / 学习区平行），每天写了就 +5 分
- 主页面右上角新增「📔 日记」入口 → `journal.html`：每天一页，当天再进来还是同一页，无固定格式，自动保存，输入框提示语固定为 "What's on your mind today?"；今天记录就自动 +5 分（每天只发一次，内容不能只有空白）；可以在月历里点任意一天翻看和修改以前的日记（有日记的日子有圆点，不加分）；页头显示连续写日记的天数；历史里的小标签是「日记」
- 日记一页分五块（身体 / 心情 / 学习 / 工作 / 想说的）；月历默认收起，点「🗓 历史记录」才展开，选了日期自动收起；老的整段日记归到「想说的」
- 连续写日记有隐藏的小惊喜（3/7/14/21/30/50/66/100/200/365 天，+5 到 +200，到了弹窗提示）
- 改了哪些文件：新增 `journal.html`、`css/journal.css`、`js/journal/main.js`、`js/data/journal.js`、`js/core/journal.js`、`tests/journal.test.js`；改了 `index.html`（入口）、`css/base.css`（`.entry-links`）、`js/firebase.js`（`journal` 集合）、`js/core/constants.js`（`CAT_SHORT.journal`）、README
- 数据：`users/{uid}/journal/{YYYY-MM-DD}`；积分记录 `log/journal-YYYY-MM-DD`（`awardOnce`）；不需要迁移，也不用改 Firestore 规则
- 数据：`journal` 文档新增 `sections`（五块），`text` 变成拼起来的一份；不需要迁移
- 需要注意的：「记录次数」会把日记的 +5 算一次；积分涨得更快，奖励价格和 `LEVEL_STEP` 之后还要一起重新平衡

## 2026-10-06 — 课程分必修 / 选修 / 方向课；dl-0 第 1 节「卷积神经网络」上线
- 首页课程卡片按「必修 / 选修 / 方向课」分组并带标签；必修 8 门（py-0、prob-0、arena-0.0、ml-0、proj-a、dl-0、proj-b、rs-0）、选修 2 门（dsa-0、opt-0）、方向课 4 门（wm-0、proj-c 世界模型；llm-0；safety-0）
- 占位小节显示「要讲：…」（`covers`）
- dl-0 u01 卷积神经网络（50 分钟，1 个视频，5 道测验）；手写 conv2d 与 F.conv2d、手写 CNN 与 nn.Sequential 都核对一致
- 改了哪些文件：各 `course.json`（`tier`、`track`、`order`、`order_note`）、`js/study/views.js`、`css/study.css`、`courses/dl-0/`、`tools/course/dl01*.py`、`unitlib.py`（`dump` 支持 `n_questions`）、`validate.py`（`direct` 小节）、README
- 需要注意的：视频内容没看过，只核实了存在和可嵌入；「有效感受野比理论值小」「LeNet/VGG 参数规模」「ViT 切块」写自已有知识，没查文献；若有 `.git/index.lock` 先删掉再提交

## 2026-10-06 — 占位课 proj-c（从零搭一个世界模型），README 写入「下回怎么开始」
- 新增占位课 `proj-c`（9 个小节，放在 wm-0 之后）；llm-0 / safety-0 / opt-0 / rs-0 的步数顺延为 11–14
- README 新增「下回怎么开始」一节：当前状态、建议顺序、要先核实的东西、不要运行 git 等约定
- 改了哪些文件：`courses/proj-c/`、`courses/index.json`、几门课的 `order`、README

## 2026-10-06 — 新增 7 门占位课（只有大纲，没有内容）
- 新增占位课：`proj-a`（Karpathy 前半：micrograd 与 makemore）、`dl-0` 深度学习主干、`proj-b`（Karpathy 后半：GPT、分词器、复现 GPT-2）、`llm-0`、`safety-0`、`opt-0`（选修）、`rs-0` 研究技能；小节的 `file` 为 null，用新字段 `covers` 写这节要讲什么
- 学习顺序：py-0 → prob-0 → arena-0.0 → ml-0 → proj-a → dl-0 → proj-b → dsa-0 → wm-0 → llm-0 → safety-0 → opt-0 → rs-0（`order`、`order_note`、`courses/index.json` 已更新）
- `js/study/views.js` 课程页：小节有 `covers` 时显示「要讲：…」；`css/study.css` 加了 `.unit-covers`
- 注意：占位小节的分钟数是估计值；Karpathy 各集的标题和顺序是凭记忆写的，出课时要核实；占位课还没有「内容依据」来源链接

## 2026-10-06 — 测验题干里的代码改成完整代码块
- py-0 和 ARENA 0.0 里 34 道「考代码结果」的测验题，题干改成把完整代码单独放进代码块（带 `print`），不再用文字描述代码；py-0 u01「两次返回值打印出来」那题有歧义，改成两个分开的 `print`，正确答案相应改为 `[1]` 和 `[1, 2]`
- 改了哪些文件：`tools/course/whole/` 里对应整节、对应的 `y01/y07/y08_quiz/y09/a10…` 脚本，重新拆分后的各小节 JSON；规则写进 `docs/COURSE_AUTHORING.md` 0.9
- 注意：其他课程（prob-0、dsa-0、wm-0 和 ARENA 的数学部分）的测验我只扫了「题干里有代码」的题，没发现同类问题，但没有逐题细读

## 2026-10-06 — 新课「机器学习入门」(ml-0)
- 新增 `ml-0`，8 个整节、自动拆成 24 个 ≤50 分钟的小节（线性回归与梯度下降、逻辑回归与分类、偏差方差与正则化、决策树与集成、无监督学习、神经网络与训练实践、完整项目流程与误差分析等）；全部用 NumPy 从零实现，网页里可以运行
- 学习顺序：py-0 → prob-0 → arena-0.0 → ml-0 → dsa-0 → wm-0（`course.json` 的 `order` / `order_note` 与 `courses/index.json` 已更新；dsa-0 变第 5 步，wm-0 变第 6 步）
- 改了哪些文件：`courses/ml-0/`、`tools/course/m0N*.py`（整节脚本）、`tools/course/whole/ml-0/`；`tools/course/split.py` 修了「承接上一小节」代码块的几处问题（依赖多个前面代码块时按顺序补全，每个原代码块单独一段）
- 未验证：视频内容没看过（只核实了存在且可嵌入）；Pyodide (Python 3.13) 里个别数值输出的最后一位可能和设备上不同

## 2026-10-06 — Python 基础补三节 + 所有课程拆成 ≤50 分钟的小节
- py-0 新增三节基础（变量、数据类型与字符串；容器：列表、元组、字典与集合；条件、循环与读懂报错），放在最前面；原来的 6 节补了「开始之前你要会」、回指和补讲，「第 N 节」式引用改成小节名；u04 改成「回顾 + 进阶」，新增上下文管理器 `with`
- 所有课程（py-0、prob-0、arena-0.0、dsa-0、wm-0）每个整节拆成 2–4 个小节，每个 ≤50 分钟：现在共 134 个小节（原来 62 节），每个小节有自己的「想一想」和 2–5 道小测验；第一个小节沿用原 id，所以已有的学习记录不受影响（但原来标「完成」的整节只对应它的第一个小节）
- 新增 `tools/course/split.py`（自动拆分，见 `docs/COURSE_AUTHORING.md` 0.9）；整节 JSON 备份在 `tools/course/whole/`；`validate.py` 现在对超过 50 分钟的节报错，拆分小节的测验数按 2–5 题检查（`unitlib.validate_unit` 对少于 10 题放宽了「答案位置」的要求）
- `course.json` 里被拆的条目多了 `whole`、`part_of` 两个字段，页面不读它们
- 注意：积分按小节算（每个小节 +100），同样的学习时间能拿到的积分比以前多（以前约 90 分钟 100 分，现在约 45 分钟 100 分），等级门槛 `LEVEL_STEP` 和奖励价格可能需要跟着调；测验题少了（2–5 题），及格线仍是 80%，2–4 题的小测验要全对
- 未验证：新增 u07–u09 的浏览器 (Pyodide 3.13) 实测；视频内容没看过

## 2026-10-05 — 等级门槛调高：大约一周升一级
- 20 级的名字不变，门槛从「0 / 100 / 250 …… 20200」改成每级相差 800 分（0 / 800 / 1600 …… 15200），按每周约 800 分的学习节奏大约一周升一级；超过 Lv.20 后每 800 分再升一级（原来是 5000）
- 改了哪些文件：`js/core/levels.js`（新增 `LEVEL_STEP`）、`tests/core.test.js`、README「等级系统」
- 注意：等级是按累计积分实时算的，已有积分的账号打开后等级会变低（比如原来 Lv.5 的 700 分现在是 Lv.1），积分本身不变；觉得节奏不合适只改 `LEVEL_STEP`

---

## 2026-10-05 — 学习页的 Python 代码块可以直接运行；py-0 的代码块按知识点拆开
- **可运行**：学习页里每个 ```python 块都有「▶ 运行」，能改代码、Shift+Enter 运行，同一节里变量共用（像 Jupyter），支持 numpy；报错会显示 traceback，死循环可「停止」。块末尾真实输出显示为「预期输出」。浏览器里的 Python 是 Pyodide（Python 3.13），第一次要下载约 10 MB（cdn.jsdelivr.net，公司网络可能拦截，会有提示）
- **py-0 六节重写代码块**：原来每块 35–84 行、好几个知识点、解释攒在后面；现在一个知识点一块（最长 35 行），格式是「问题引入 → 代码 → 紧跟着读输出」。块数：u01 5→22、u02 4→25、u03 4→22、u04 5→23、u05 4→17、u06 11→18；讲解、视频、测验保留。u06 的项目文件块大多是 static（网页里没法把多个文件当项目运行），可运行的是 5 个算法块
- **出课工具**：`runlib.Notebook`（块之间共用变量，规则和网页一致）；`validate.py` 现在检查每个 Python 块的语法，py-0 的单块超过 35 行报错，其他课只提示（共 63 块，以后重写时拆）；`docs/COURSE_AUTHORING.md` 新增 0.8
- 改了哪些文件：新增 `js/study/runner.js`、`js/study/pyworker.js`；改 `js/study/views.js`、`css/study.css`、`tools/course/runlib.py`、`unitlib.py`、`validate.py`、`y01…y06*.py`（旧版备份 `*_old.py`）、`courses/py-0/u01…u06`、dsa-0 第 5 节里一处伪代码的代码块语言（python→text）、README、文档
- 注意：我在浏览器里用真实 Pyodide 把 py-0 全部可运行块跑了一遍：无意外报错；少数输出措辞和预期输出略有差异（Python 版本不同，如报错措辞）。手机上的实际体验、公司网络下能否下载 Pyodide 没测过
- **修了一个 bug**：点「清空变量」（或者先看完一节再进入另一节）之后再运行，会报 `py.globals.get(...) is not a function`——清空变量时把运行用的辅助函数也一起删掉了。已改为清空时保留辅助函数（`js/study/pyworker.js`），并在浏览器里测过「运行 → 清空 → 再运行」
- 其他课（ARENA、prob-0、dsa-0、wm-0）的代码块也有「▶ 运行」，但很多块偏长、且 ARENA/wm-0 里用 torch 的块在网页里跑不了（只有 numpy），还没按新规则拆

---

## 2026-10-05 — 学习积分：同一天学完 3 节再奖励 100 分
- 同一天首次学完 3 节新章节，额外 +100，每天只发一次（再多学不重复发）；第 3 节的庆祝弹窗里会显示奖励，前两节的弹窗会提示「今天已学完 N 节，学满 3 节再得 100 分」
- 改了哪些文件：`js/core/study.js`（`dayUnitsBonus`）、`js/data/study.js`（`completeUnit` 多返回 `todayCount` 并发放，log 文档 ID `studyday-{日期}`、category `studyday`）、`js/study/views.js`、`js/core/constants.js`（标签「当日三连」）、`tests/study.test.js`、README
- 注意：只数「首次学完」的章节，重复点同一节不算；跨零点以学完那一刻的本地日期为准；不需要改 Firestore 安全规则
- 以前已经学完的章节不会被补发（只在学完新章节的那一刻判断）

---

## 2026-10-05 — ARENA 第 2–15 节全部改成新格式，新增衔接课 wm-0（通往世界模型）
- **ARENA 第 2–15 节按 v3 重写**：每节加「标准定义 + 白话版」、真实运行的 NumPy / PyTorch 代码和小实验（梯度检验、梯度消失、PCA 与 LoRA 参数量、权重初始化、交叉熵拟合、广播与 einsum 对拍等）；视频、10 道测验沿用旧版（只改了解释里的「选项 A」式位置引用）；旧版备份在 `tools/course/aNN_old_uNN.json`。每节 45 分钟 → 85–115 分钟，整门课约 25 小时
- **新增课程 `wm-0` 通往世界模型**（8 节，约 14 小时）：MDP、贝尔曼方程与动态规划、无模型学习（MC/TD/Q-learning）、策略梯度与深度 RL、潜变量与 VAE、序列与状态空间模型（HMM、卡尔曼、GRU）、基于模型的 RL、世界模型（Ha & Schmidhuber、Dreamer、JEPA、读论文指南与进一步学习资源）。学习顺序第 5 步，选修
- 改了哪些文件：`courses/arena-0.0/u02…u15-*.json`、`course.json`（minutes）；新增 `courses/wm-0/`、`courses/index.json`、`tools/course/a02…a15*.py`、`w01…w08*.py`、`.gitignore`（忽略 `__pycache__`）；`README.md`、`docs/COURSE_AUTHORING.md`（顺序）
- 需要注意：所有视频只按标题/频道选择，没逐个看过；新课里有少数事实标了「未核实」；手机上的渲染没看过。**提交前如果有 `.git/index.lock` 要自己删**（我从不运行 git）

---

## 2026-10-04 — 出课格式写进文档、四门课排出学习顺序、ARENA 第 1 节改成新格式
- **出课格式**：把 v3 格式（每节结构、渲染规则、脚本写法、质量检查、对 ARENA 旧节的重写方法）写进 `docs/COURSE_AUTHORING.md` 的新增第「〇」节；README 的「出新课程」一条改为先读这一节。下次出课直接读它
- **学习顺序**：新增 README「学习顺序」一节；`courses/index.json` 改成 py-0 → prob-0 → arena-0.0 → dsa-0；每门课的 `course.json` 加了 `order`、`order_note`；「我的课程」页的卡片和课程页上显示「第 N 步 · 说明 · 约 X 小时」，页面顶部加了一行顺序提示
- **ARENA 第 1 节按 v3 重写**（`u01-neural-networks.json`，45 → 85 分钟）：加了「标准定义 + 白话版」（神经元、全连接层与前向传播、非线性、代价函数、梯度下降），用 NumPy 真实运行了单个神经元、784→16→16→10 的形状与参数个数（13,002）、批量前向传播、「去掉激活函数 = 一个线性变换」的验证、代价函数、五种学习率的梯度下降、XOR 小实验（10 个随机种子，9 个学会、1 个卡住）；视频、10 道测验沿用旧版，旧版备份在 `tools/course/a01_old_u01.json`
- 改了哪些文件：`docs/COURSE_AUTHORING.md`、`README.md`、`courses/index.json`、四个 `course.json`、`courses/arena-0.0/u01-neural-networks.json`、`js/study/views.js`、`css/study.css`；新增 `tools/course/a01.py`、`a01c.py`、`a01_quiz.py`、`a01_old_u01.json`
- 检查：`validate.py` 通过（`--online` 两次都因网络超时中断，新增的 4 个链接和 2 个视频单独核实过可用）；`npm test` 17 项通过；`views.js` 语法检查通过；本节 69 处公式 KaTeX 试渲染 0 个出错
- 需要注意的：①「第 N 步」的显示我没有在浏览器里看过，请你打开页面确认排版；②ARENA 的 u02–u15 还是旧格式；③顺序是我的建议，不合适可以按文档 0.6 改；④`tools/course/__pycache__/` 不要提交

## 2026-10-03 — dsa-0 全 11 节、py-0 全 6 节写完（含第 1 节按新格式重写）
- 按 Yijia 的要求「深浅由我判断够不够给 master 打基础」，不再压缩深度：覆盖 NUS IT5003 / MIT 6.006 的核心内容，py-0 补上读 ML 代码需要的部分
- **dsa-0 扩成 11 节**（共约 855 分钟）：u01 复杂度（重写：加了 Big-O/Ω/Θ 的形式定义、均摊分析、空间复杂度）、u02 数组与链表、u03 栈队列、u04 哈希表、u05 分治与回溯（含主定理）、u06 排序与二分、u07 树与 BST（含 AVL）、u08 堆、u09 图（BFS/DFS/拓扑排序）、u10 最短路径、最小生成树与并查集（新增）、u11 动态规划（新增，单独成节）
- **py-0 扩成 6 节**（共约 600 分钟）：u01 函数、作用域与递归（重写：加了 `*args/**kwargs`、传参机制、闭包、装饰器）、u02 推导式、迭代器与生成器、u03 类与对象（特殊方法、继承、property、dataclass）、u04 异常、调试、测试与类型注解（含 logging）、u05 文件、模块与环境（新增：pathlib、json/csv、模块与包、argparse、venv/uv）、u06 综合小项目（从零实现 k-NN，含测试）
- 格式沿用 prob-0 的定稿格式：中英文标准定义 → 白话版 → 带真实输出的注释代码 → 三句话 → 3 个「想一想」→ 关键词 → 参考资料 → 10 题测验
- 所有「# 输出：」都由 `runlib.code()` 运行后写入；多数算法都用随机输入与暴力解法 / 标准库做了对拍（如 Dijkstra 对 Floyd-Warshall、Kruskal 对暴力枚举生成树、背包对子集枚举）；py-0 u06 的项目文件由 `y06c.py` 写出并真实运行，正文里的终端输出、测试结果都是那次运行的结果
- 改了哪些文件：新增 `courses/dsa-0/u02…u11-*.json`、`courses/py-0/u02…u06-*.json`；重写 `u01-complexity.json`、`u01-functions-recursion.json`；`dsa-0/course.json`、`py-0/course.json`（节数、标题、时长、简介）；`tools/course/` 下新增 `d02…d11.py`、`y02…y06.py` 及配套的 `*c.py`（代码块），`runlib.py` 的 `code()` 增加 `err=True`（把标准错误并入输出，用来展示 traceback 与日志）；`d01_old.py`、`y01_old.py` 是旧版备份，可删
- 检查：`validate.py --online` 通过（99 个 YouTube 视频、95 个链接可用）；`npm test` 17 项通过；1538 处公式用 KaTeX 试渲染，0 个出错；各节测验正确答案分散；讲义里没有写作提示类文字
- 需要注意的：①视频都是按标题与时长选的，我没有看过全部内容，建议抽看；②没有在手机上看过排版；③各节「分钟数」是估算（视频时长 + 阅读与动手时间）；④输出里涉及计时的地方（如 `lru_cache` 对比、并查集速度对比）只写了量级，具体倍数因机器而异；⑤`tools/course/__pycache__/` 里有编译缓存，不要提交（仓库里没有 .gitignore）

## 2026-10-03 — prob-0 补全第 2–6 节（按第 1 节定稿的格式）
- 新增 5 节：u02 随机变量、期望与方差（60 分钟）；u03 常见分布：二项、泊松、正态（70 分钟）；u04 大数定律与中心极限定理（60 分钟）；u05 最大似然估计与交叉熵（65 分钟）；u06 置信区间与假设检验（70 分钟）。至此 prob-0 共 6 节，每节正文约 6500–7800 字
- 统一格式：每个概念先放中英文**标准定义**（引用块），再放**白话版**（例子、类比，面向高中生）；重点概念带英文；代码逐行中文注释；每节 3 道「想一想」、关键词表（带英文）、10 题测验（正确答案分布在 4 个位置）
- 所有代码块的「# 输出：」行都由 `tools/course/runlib.py` 的 `code()` 运行后自动写入，保证和真实输出一致
- 同时删掉 u01 里那段「本节的讲法」说明（它是给 Claude 的写作提示，不应该出现在讲义里）；u02–u06 的讲义里没有此类文字
- 改了哪些文件：新增 `courses/prob-0/u02-random-variables.json`、`u03-distributions.json`、`u04-lln-clt.json`、`u05-mle-cross-entropy.json`、`u06-ci-hypothesis-tests.json`；修改 `courses/prob-0/course.json`（5 节的 `file` 和 `minutes`）、`courses/prob-0/u01-conditional-bayes.json`；新增 `tools/course/runlib.py`、`p02.py`–`p06.py`，修改 `p01.py`
- 检查：`validate.py --online` 通过（52 个 YouTube 视频、54 个链接可用）；`npm test` 17 项通过；583 处公式用 KaTeX 试渲染，0 个出错
- 需要注意的：①视频都是按标题与时长选的，我没有看过全部内容，建议你看一眼是否合适；②这五节还没在手机上看过排版；③u05、u06 的参考资料较少（MIT OCW 6.041 主页 + StatQuest），想要更深的内容再补；④需要推送才会上线

## 2026-10-03 — prob-0 第 1 节再改：先给中英文标准定义，再给白话版；面向高中生；代码加注释
- 按 Yijia 的反馈：① 每个新概念先放**标准定义**（引用块，中文 + 英文各一行），再放**白话版**（例子和类比）；共 9 个概念：概率、条件概率、独立、乘法法则、互斥、全概率公式、先验与后验、贝叶斯定理、基础概率谬误；② 正文里的重点概念都带英文，符号速查表也加了英文；③ 语气从「给初中生讲」调整为「给高中生讲」，措辞更紧凑，例子保留；④ 三段代码都加了逐行中文注释，输出行统一用「# 输出：」标出
- 新增了「样本空间 / 事件」的定义，条件概率的「想一想」第 1 题多给了一个用定义验证的算法
- 篇幅：正文约 9000 字，本节时长改为 55 分钟（`course.json` 同步）；视频、测验 10 题和参考资料不变
- 改了哪些文件：`courses/prob-0/u01-conditional-bayes.json`、`courses/prob-0/course.json`、`tools/course/p01.py`
- 检查：`validate.py --online` 通过；三段代码都实际运行，输出和「# 输出：」行逐行一致；130 处公式用 KaTeX 试渲染，0 个出错；用 marked 试排版，定义引用块、表格、代码块都正常，没有残留的占位符或没渲染的星号
- 需要注意的：需要重新推送才会覆盖线上的旧版本；这一版比上一版长，如果觉得太长，可以把「基础概念」和「互斥」两小节压缩

## 2026-10-03 — 重写 prob-0 第 1 节，概念讲得更细（初中生也能听懂）
- 按 Yijia 的反馈重写「条件概率与贝叶斯」：每个新概念先用生活例子或类比引入，再给公式。加了符号速查表；用「40 人班级戴眼镜」讲条件概率和独立；用「下雨带伞」对比不独立；用「掷骰子」讲互斥不等于独立；用「玩具厂两条生产线」讲全概率；用「烟雾报警器」类比和「10000 人数人头」表讲贝叶斯；新增「连续测几次阳性」的更新代码；结尾加了三句话总结
- 3 个「想一想」的答案也改成同样的讲法；关键词表的解释改成白话；测验 10 题和参考资料不变（答案位置不变）
- 篇幅：正文约 6200 字，视频不变（25 分钟），本节时长从 45 改为 50 分钟（`course.json` 同步）
- 改了哪些文件：`courses/prob-0/u01-conditional-bayes.json`、`courses/prob-0/course.json`、`tools/course/p01.py`
- 检查：`validate.py --online` 通过；本节两段代码都实际运行过，输出与注释一致；公式逐个用 KaTeX 试渲染，0 个出错
- 需要注意的：已经推送过的旧版本会被这次改动覆盖，需要重新推送

## 2026-10-03 — 新增三门补基础课程的大纲和样板课（概率统计、数据结构与算法、Python 软件基础）
- 学习区多了三门课，各有完整大纲（章节列表）和 **1 节样板课**，其余章节显示「即将上线」：
  - `prob-0` 概率统计补漏（6 节）：样板 u01「条件概率与贝叶斯（含诊断测验）」，兼作对「概率够用」这个假设的检验
  - `dsa-0` 数据结构与算法（10 节，对应 NUS IT5003 的核心内容）：样板 u01「复杂度：Big-O 怎么看」
  - `py-0` Python 软件基础（5 节，对应 NUS IT5001 的核心内容）：样板 u01「函数与递归」
- 每个样板课：学习目标、导读、2 个 YouTube 视频、要点、3 个「想一想」、关键词表、10 道测验、参考资料，格式和 ARENA 0.0 一致
- 内容依据：大学公开课程（MIT OCW 6.041 / 6.006、Harvard Stat 110 / CS50P）和开放教材（Runestone pythonds、Think Python 3e）当**大纲和参考阅读**，讲解是自己用中文写的，没有转载原文。Runestone 和 Think Python 都是 CC BY-NC-SA 4.0，每节参考资料里已标明出处和链接；OpenStax Introductory Statistics 的条款禁止把内容输入 AI 模型，所以没有使用
- 改了哪些文件：新增 `courses/prob-0/`、`courses/dsa-0/`、`courses/py-0/`（各含 `course.json` 和一节样板 JSON）；`courses/index.json` 加了三项（顺便把格式从单行改成缩进）；新增 `tools/course/p01.py`、`d01.py`、`y01.py`（三节的源脚本，放在这里方便以后改）
- 检查：`validate.py --online` 全部通过（38 个视频可嵌入、46 个链接可打开）；`npm test` 17 个测试通过；三节里所有代码块都实际运行过，注释里的输出和真实输出一致；235 处公式用 KaTeX 逐个试渲染，0 个出错
- 需要注意的：① 没有在浏览器里用假 Firebase 做过整页验收，请在手机上打开三节确认排版、测验里的代码块和视频能播放；② 新加的视频中，除 StatQuest 外都只按标题和频道挑选，没有逐个看完；③ Harvard Stat 110 的课程主页（projects.iq.harvard.edu）会拦截脚本访问，所以参考资料里放的是它的 YouTube 视频链接；④ 没有改任何 JS 代码和 Firestore 数据结构

## 2026-09-29 — 加改动日志和出课流程文档
- 新增本文件 `CHANGELOG.md`，把从第一版到现在的改动补记下来
- 新增 `docs/COURSE_AUTHORING.md`：记录 ARENA 0.0 这 15 节课是怎么出的（选题 → 找视频并核实 → 写内容 → 跑代码 → 出题 → 检查 → 浏览器验收），以后出新课照这个流程
- 新增 `tools/course/`：出课用的小工具
  - `yt.py`：搜索 YouTube 视频，核实能否嵌入、拿到时长
  - `unitlib.py`：写章节用的辅助函数和自动检查
  - `validate.py`：检查 `courses/` 里所有课程 JSON 的格式、公式、测验答案分布
  - `unit_template.py`：新章节的模板
- README 加了「改动日志规则」，并链接到上面两个文件
- 没有改任何页面代码和用户数据

## 2026-09-28 — 完善了第一个完整的课程（`8933fe3`）
- 学习区的「ARENA 0.0 前置知识」写完全部 15 节：反向传播、线性变换、矩阵性质、基与基变换、特征值与 SVD、概率统计、微积分、信息论、Python/NumPy、PyTorch、开发工具、einops、广播、einsum 与索引
- 每节：学习目标、导读、1–3 个 YouTube 视频、要点、3 个「想一想」、关键词表、10 道测验、参考资料
- 29 个视频都用 YouTube oEmbed 核实过可嵌入；35 个参考链接都核实过能打开；代码示例都在 torch 2.14 / numpy 2.5 / einops 0.8 上实际跑过
- 文件：`courses/arena-0.0/u02 … u15-*.json`，`course.json` 里每节的 `file` 都填上了

## 2026-09-28 — 样板课程内容（`d6d75de`）
- 新增**学习区** `study.html`（独立页面，主页面左上角「📚 学习区」进入）
  - 课程列表 → 章节列表（已学 / 未学 / 即将上线 分开显示）→ 学习页 → 测验 → 答题回顾
  - 学习页支持文字（Markdown + KaTeX 公式）、YouTube / B站 视频嵌入（带「在 XX 打开」备用链接）、图片、「想一想」折叠题、关键词表
  - 每节一篇笔记，点「📝 笔记」弹出，自动保存
- 积分规则（`js/core/study.js`）：学完一节 +100（只一次）；测验第一次达到 80 分 +50（补做也算）；连续学习每满 7 天 +100、第 30 天 +500、第 100/200/300 天各 +500、第 365 天 +1000，都有庆祝弹窗。只有学完**新章节**才算当天有效学习；学习记录也算主页面的 🔥 连续打卡
- 新增数据：`users/{uid}/studyProgress`（测验成绩）、`users/{uid}/studyNotes`（笔记）；log 新增 category `study` / `quiz` / `studystreak`。现有安全规则已覆盖，不用改
- 课程内容放在仓库 `courses/` 里的 JSON，推送即发布（方案 A）
- ARENA 0.0 课程大纲 15 节，先写好第 1 节「神经网络是什么」作样板
- 新增文件：`study.html`、`css/study.css`、`js/study/*`、`js/core/study.js`、`js/data/study.js`、`courses/`、`tests/study.test.js`

## 2026-09-28 — 改整体架构（`ed07247`）
- 把原来 1200 行的单文件 `index.html` 拆成 `css/`（base / app）和 `js/`（core 纯逻辑 / data 读写 Firebase / ui 共用组件 / app 主页面），浏览器原生 ES 模块，不需要构建步骤。功能不变
- 新增 `package.json`（`npm test`、`npm run serve`）和 `tests/core.test.js`（积分、连续天数、等级等 12 个测试）
- 新增 `js/data/awards.js` 的 `awardOnce()`：「只加一次分」的通用函数
- 修复：「＋ 添加自定义奖励」按钮会把点击事件当成要编辑的奖励，导致标题显示「编辑奖励」、名称框显示 undefined、保存后档位为空不显示。空档位的老奖励现在会显示在「日常小奖励」里，编辑一次就能改对
- 修复：编辑任务 / 奖励后提示错写成「已添加」，改为「已保存修改」
- 注意：之后不能再双击 `index.html` 本地打开，要用 `npm run serve`

## 2026-09-28 — 顶部标题去掉个人名字（`153a1da`）
- 顶部「远征日志 · Yijia 的 AI 转型任务」改为「远征日志」，其他用户不会再看到你的名字

## 2026-09-28 — 数据迁移（`8ae1097`）
- 新用户的默认内容换成通用版：3 个板块（精神食粮 / 身体 / 生活）× 2 条任务，4 个奖励（奶茶、电影、小东西、旅行）
- 所有板块都存进数据库 `users/{uid}/sections`，预设板块也能改名 / 删除
- 老账号登录时自动迁移一次：原来写死的 7 个板块用原 id 写进数据库（任务和历史记录不用改），上一版自定义板块的 `sec_` 前缀统一去掉；完成后写 `meta/app.schemaVersion = 2`
- 删除旧版「记录一次学习」表单的死代码
- 新增 `firestore.rules`（安全规则存档）。已在控制台用规则测试平台验证：别的账号读取被拒绝
- 注意：推送后要等 1–2 分钟再登录，否则浏览器缓存的旧版会给新账号写入旧模板（当天踩过一次，手动删了测试账号的数据重来）

## 2026-09-28 — 任务板块自定义（`0011a26`）
- 记录页底部新增「＋ 添加自定义板块」，自定义板块可改名、删除（里面有任务时不让删）
- 「添加自定义学习任务」改为「添加自定义任务」，确认 / 庆祝弹窗里的「学习任务」也改成「任务」

## 2026-09-28 — 上线打卡就算连续（`f5281b7`）
- 每日签到的日子也算进 🔥 连续打卡天数（签到仍然不算「记录次数」）

## 2026-09-28 — 添加每日上线打卡功能，拿掉魔法棒特效（`20a740d`）
- 去掉经验条上挥舞的魔杖图标和动画
- 新增每日上线奖励：每天第一次打开 +5 分，每天最多一次（log 文档 ID `daily-YYYY-MM-DD` + 事务，多设备同时打开也只记一次；页面跨零点 / 从后台切回会补发）

## 2026-09-26 — 第一版（`4b370f1` … `23c0323`）
以下由 git 历史整理（当时的 commit 说明只写了 Update index.html）：
- `d02e478` 第一版：Google 登录 + Firestore，记录学习、奖励商店、历史三个 Tab；README 写了部署步骤（建 Firebase 项目、安全规则、GitHub Pages）
- `9ce20a6` 兑换奖励加二次确认弹窗、庆祝弹窗和撒花动画
- `2ed72bb` 奖励卡片加自动分配的小图标（`REWARD_ICONS`，按 id 哈希）
- `9f29823` 奖励可编辑
- `543a300` 「记录」Tab 改成像奖励商店一样的任务卡片（完成 / 编辑 / 删除），预设 16 条任务
- `9e311fb`、`4390007` 经验条上加挥舞的魔杖图标（09-28 已移除）
- `23c0323` README 重写成「项目说明（给未来的我 / 未来的 Claude 看）」
