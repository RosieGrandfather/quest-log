# 远征日志 — 项目说明（给未来的我 / 未来的 Claude 看）

一个纯前端的学习积分 / 奖励兑换小工具，帮 Yijia 把 AI 转型学习计划（ARENA、PL-300、Python 练习、自建项目、求职、规划复盘）游戏化：做一件事记一次积分，攒够积分兑换真实奖励。

**技术栈**：纯静态 HTML/CSS/JS（无构建步骤，无框架）+ Firebase（Auth 登录 + Firestore 数据库）+ GitHub Pages 托管。数据只存在 Yijia 自己的 Firebase 项目里，不经过 Claude 或任何第三方；手机和电脑用同一个 Google 账号登录，实时同步。

## ⚠️ 改动日志规则（每次都要遵守）

**每次改动（代码、课程内容、数据结构、配置）都要在 [`CHANGELOG.md`](CHANGELOG.md) 最上面记一笔**，写清楚：日期、一句话标题（和 commit 说明一致）、用户能看到的变化、改了哪些文件 / 数据结构、需要注意的事（迁移、要手动做的操作、已知问题）。没记日志的改动不算完成。

**出新课程 / 补章节 / 重写旧章节**：先读 [`docs/COURSE_AUTHORING.md`](docs/COURSE_AUTHORING.md) 第「〇」节（**现行的出课格式 v3**：每节怎么写、渲染规则、质量检查、脚本写法），再按后面的流程做，工具在 `tools/course/`。

## 学习顺序（五门课怎么排）

页面「我的课程」里每张卡片上的「第 N 步」就是这个顺序（读 `course.json` 的 `order` / `order_note`，小时数由各节 `minutes` 加总）。

| 步骤 | 课程 | 约多久 | 为什么排在这里 |
|---|---|---|---|
| 1 | `py-0` Python 软件基础（6 节） | 10 小时 | 其他三门课都要写代码；第 6 节是综合小项目 |
| 2 | `prob-0` 概率统计补漏（6 节） | 6 小时 | ARENA 的概率、信息论（含交叉熵）要用 |
| 3 | `arena-0.0` ARENA 前置知识（15 节） | 约 25 小时 | 主线技术课；第 10–15 节与 Python 基础有重叠，熟了可略读 |
| 4 | `dsa-0` 数据结构与算法（11 节） | 14 小时 | Master 课程的先修，可以在 ARENA 的学习之间穿插；想先准备申请就提到第 3 步 |
| 5 | `wm-0` 通往世界模型：强化学习与生成模型衔接课（8 节） | 14 小时 | 选修衔接课：想研究 world model 时，学完 ARENA 0.0 再开始（强化学习、VAE、状态空间模型、基于模型的强化学习、Dreamer / JEPA）；与第 4 步互不依赖 |

每周 12–15 小时的话，前两门大约 1–1.5 周，ARENA 约 2 周，数据结构约 1–1.5 周，衔接课约 1 周（只算看课时间，不含自己做练习）。这个顺序是建议，改动方法见 `docs/COURSE_AUTHORING.md` 第 0.6 节。

## 文件

- `index.html` — 主页面的 HTML 骨架（弹窗也在这里），不含样式和逻辑。左上角「📚 学习区」进入学习区
- `study.html` — **学习区**（独立页面），见下面「学习区」一节
- `css/study.css` — 学习区专用样式
- `courses/` — 学习区的课程内容（JSON），**推送即发布**
- `css/base.css` — 所有页面共用：颜色变量（含深色模式）、登录页、按钮、弹窗、提示、庆祝动画
- `css/app.css` — 主页面专用：顶部状态栏、Tab、任务 / 奖励卡片、记录列表
- `js/` — 全部逻辑，浏览器原生 ES 模块（`<script type="module">`），**没有构建步骤**，推上去就能用。结构见下面「代码结构」
- `tests/core.test.js` — `js/core/` 纯逻辑的测试，跑 `npm test`（只需要装了 Node.js，不需要 npm install）
- `package.json` — 只用来声明 ES 模块和 `npm test` / `npm run serve` 两个命令，没有依赖
- `firebase-config.js` — Yijia 自己 Firebase 项目的连接信息（apiKey 等，不是密钥，允许公开）
- `firestore.rules` — Firestore 安全规则的存档（**真正生效的是 Firebase 控制台里的那份**，改规则要去控制台发布，然后同步回这里）
- `README.md` — 这份文件
- `CHANGELOG.md` — **改动日志**，从第一版到现在每次改了什么（最新在上）
- `docs/COURSE_AUTHORING.md` — **出课流程与格式**：现行的 v3 格式、怎么选视频、写内容、出测验、检查、验收（下次出课先读它）
- `tools/course/` — 出课工具（Python，不参与网页运行）：`yt.py` 搜索 / 核实 YouTube 视频，`unitlib.py` 写章节的辅助函数和检查，`validate.py` 检查所有课程，`unit_template.py` 新章节模板

**线上地址**：`https://rosiegrandfather.github.io/quest-log/`
**本地路径（Yijia 电脑上）**：`C:\projects\quest-log-project\quest-log-project\quest-log`（挂载后是 `$HOME/mnt/quest-log/`）

---

## 项目里有什么功能（现状）

### 1. 顶部状态栏
- 连续打卡天数（🔥 streak，`computeStreak()`）
- 等级名 + Lv.数字 + 经验条（`levelInfo()`，见下面「等级系统」）
- 经验条（纯进度条，之前的魔杖挥舞特效已按用户要求移除，不要再加回来）
- 三个统计数字：可用积分 / 累计获得 / 记录次数
- **每日上线奖励**：每天第一次打开（登录状态下）自动 +5 分（`DAILY_LOGIN_POINTS`，`ensureDailyLoginBonus()`）。写进 `log` 集合，文档 ID 固定为 `daily-YYYY-MM-DD`，用事务保证多设备同时打开每天也只加一次；页面跨零点或从后台切回时会补发。`category:'daily'` 的记录计入积分和连续打卡天数（每天上线就算连续），但**不计入「记录次数」**。

### 2. 「记录」Tab —— 任务（像奖励商店一样的卡片式）
- 按板块分组显示任务卡片。**板块全部存在数据库 `sections` 集合里**（代码里没有写死的板块了），按 `ts` 排序
- 每张卡片：自动分配的小图标（`iconForTask()`，图标库是 `TASK_ICONS`，10 个通用学习/成就主题图标）+ 任务名 + 积分
- 卡片按钮：**编辑**（弹窗改名称/类别/积分）、**删除**（点一下变"确认删除？"，4 秒内再点才真删）、**完成 ✓**（点了弹二次确认 → 确认后写入一条 `log` 记录并弹庆祝弹窗+撒花动画，文案："你太棒了！完成了一次「XX」任务 🎉 已添加 X 积分！"）
- **板块管理**：底部「＋ 添加自定义板块」新建板块；每个板块标题右侧有「改名」「删除板块」（删除同样要点两次；板块里还有任务时不让删）。空板块也会显示。万一有任务找不到所属板块，会显示在最后一个「未分类」组里（不可改名/删除）
- 底部「＋ 添加自定义任务」可以新增任务，**积分允许填 0**（比如"心安理得摸鱼"类的 0 分任务，用户明确要求过）
- 新用户首次登录：`ensureUserData()` → `seedNewUser()` 把 `SEED_SECTIONS` / `SEED_TASKS` / `SEED_REWARDS` 写进这个用户自己的数据库（3 个板块：精神食粮 / 身体 / 生活，每个 2 条任务；4 个通用奖励）。之后只读数据库，改代码里的模板不影响已有用户
- 下面还有「最近记录」列表（`renderRecent()`）

> 旧版本的「记录一次学习」表单弹窗（`openLogModal` / `submitLogEntry` 那套）已经彻底删除。要恢复"手动填表单记录"得重新写。

### 3. 「奖励商店」Tab
- 三档：小奖励 / 中奖励 / 大奖（`TIER_META`），新用户默认奖励见 `SEED_REWARDS`（奶茶/咖啡、看电影、买小东西、一次旅行）
- 每张卡片：自动分配的小图标（`iconForReward()`，图标库 `REWARD_ICONS`，10 个通用魔法/奇幻主题图标——魔杖、药水瓶、咒语书等，**同样是为了避开哈利波特商标图案而设计的通用款**）+ 名称 + 所需积分 + 攒够进度条
- 兑换：点"兑换"→ 二次确认弹窗 → 确认后从 `log` 里写一条 `spend` 记录 → 弹庆祝弹窗+撒花动画（"「XX」奖励已兑换 🎉 已扣除 X 积分。奖励商店欢迎下次光临！"）
- 编辑/删除跟任务同一套交互
- 「＋ 添加自定义奖励」可以新增奖励，**积分同样允许填 0**

### 4. 「历史」Tab
- 所有记录按日期分组显示（`renderHistory()`）

### 5. 等级系统
`LEVELS` 数组，**现在是 20 级**，按累计获得的总积分（不是可用积分，兑换奖励不扣这个数）算，每级相差 `LEVEL_STEP = 800` 分（`js/core/levels.js`，按每周约 800 分的学习节奏，大约一周升一级）：新手上路(0) → 打好地基(800) → 小试牛刀(1600) → …… → 传奇远征者(15200)。超过最后一级后，`levelInfo()` 按「每 +800 分再升一级」继续延伸，不会封顶。觉得太快或太慢，只改 `LEVEL_STEP` 这一个数。

### 6. 学习区（`study.html`）
独立页面，只放学习内容。学完 / 测验达标 / 连续学习的积分自动写进同一个 `log`，回主页面积分、历史、🔥 连续打卡都会更新。
- 页面：课程列表 `#/` → 章节列表 `#/c/课程id` → 学习页 `#/c/课程id/u/章节id` → 测验 `…/quiz` → 回顾 `…/review`
- 章节不锁顺序；已学（绿色 + ✓）、未学（编号）、即将上线（半透明，`file` 为 null）一眼能分出来
- 学习页内容块：文字（Markdown + KaTeX 公式）、视频（YouTube / B站 嵌入 + 「在 XX 打开」备用链接）、图片、「想一想」折叠题、关键词表；底部「学完了 ✓」
- **积分规则**（`js/core/study.js`，有测试）：
  - 学完一节 +100，每节只一次（log 文档 ID `study-{课程}__{章节}`）
  - 测验可无限重做；**第一次**达到 80 分 +50（`quiz-{课程}__{章节}`），当时跳过、之后补做达标也算
  - 连续学习：只有「当天首次学完了一节新章节」才算有效学习日。每满 7 天 +100；第 30 天 +500（只一次）；第 100 / 200 / 300 天各 +500；第 365 天 +1000。每次都有庆祝弹窗（`studystreak-{日期}-{天数}-{分值}`）
  - 同一天学完 3 节新章节：额外 +100，每天只一次（`studyday-{日期}`，category `studyday`），第 3 节的庆祝弹窗里会显示；前两节会提示「今天已学完 N 节」
  - 学习记录（category `study` / `quiz` / `studystreak`）也算主页面的 🔥 连续打卡
- 笔记：每节一篇，点右下角「📝 笔记」弹出，停止输入 0.8 秒自动保存，只有本人可见
- 学习区打开时同样会发每日签到奖励

#### 课程内容怎么加 / 改
> 完整流程见 [`docs/COURSE_AUTHORING.md`](docs/COURSE_AUTHORING.md)；改完跑 `python tools/course/validate.py`。

课程是仓库里的 JSON，页面直接从网站读，**推送就上线**，不需要进 Firebase：
- `courses/index.json`：课程列表 `{"courses":[{"id","path"}]}`
- `courses/{path}/course.json`：`id`、`title`、`subtitle`、`source`（内容依据，链接）、`units`（`id`、`title`、`en`、`minutes`、`file`——还没写好的节 `file` 为 null）
- `courses/{path}/{file}`：一节的内容：`objectives`（学完能做到什么）、`blocks`、`references`、`quiz.questions`（`q`、4 个 `options`、`answer` 为正确选项下标、`explain`）
- block 类型：`text`（`md`）、`video`（`provider` 为 youtube / bilibili，`id`，可选 `start` / `end` 秒、`title`、`lang`、`minutes`）、`image`（`src`、`alt`、`caption`）、`think`（`q`、`a`）、`keywords`（`items`: [中文, English, 说明]）
- 公式用 `$...$` / `$$...$$`；JSON 里反斜杠要写两个（`\\sigma`）
- **ARENA 课程不放原文**（ARENA 仓库没有开源授权）：按他们的大纲和知识点、参考链接自编中文讲解，关键词标英文，每节附原文链接
- 视频链接加进课程前要核实存在、可嵌入（YouTube 可用 `https://www.youtube.com/oembed?url=…` 查，返回 200 即可嵌入）；公司网络会拦 B站，B站 编号请在手机上确认
- 已上线：**ARENA 0.0 全部 15 节**（2026-09-28）；**补基础三门课**（2026-10-03，`prob-0` 概率统计、`dsa-0` 数据结构与算法、`py-0` Python 软件基础）`prob-0` 全 6 节、`dsa-0` 全 11 节、`py-0` 全 6 节已写完（2026-10-03），大纲依据是大学公开课和开放教材，讲解自写。每节 = 学习目标 + 导读 + 1–3 个 YouTube 视频（均已用 oEmbed 核实可嵌入）+ 要点 + 3 个「想一想」+ 关键词表 + 10 道测验（正确答案分散在 A–D）+ 参考资料（链接已核实）
- 代码示例（第 10–15 节等）都在 Python 3.12 + numpy 2.5 + torch 2.14 + einops 0.8 上实际跑过，注释里的输出是真实输出；第 13–15 节的练习题是自编的，没有照搬 ARENA 的练习

---

## 数据结构（Firestore）

所有数据都在 `users/{uid}/...` 下面，按 uid 隔离，安全规则只允许本人读写自己的数据（规则原文见 `firestore.rules`，2026-09-28 用规则测试平台验证过：别的账号读取被拒绝）。子集合：

- `users/{uid}/log`：每条学习记录或兑换记录。字段：`kind`（'earn' 或 'spend'）、`category`、`label`、`amount`、`note`、`dateISO`、`ts`
- `users/{uid}/rewards`：奖励定义。字段：`name`、`tier`（small/medium/big）、`cost`、`active`、`ts`
- `users/{uid}/tasks`：任务定义。字段：`name`、`category`（= 所属板块在 `sections` 里的文档 ID）、`points`、`active`、`ts`
- `users/{uid}/sections`：板块。文档 ID 就是板块 id。字段：`label`、`ts`（排序）、`short`（可选，历史记录小标签用的简称；老板块迁移时带上，改名后删除，之后标签显示全名）
- `users/{uid}/studyProgress/{课程}__{章节}`：测验成绩。`quizAttempts`、`quizBest`、`quizPassed`、`lastAttempt`（`answers` 数组、`score`、`ts`）、首次学完时的 `completedISO`。**「是否学完」以 log 里有没有 `study-…` 记录为准**
- `users/{uid}/studyNotes/{课程}__{章节}`：笔记 `text`、`updatedAt`
- `users/{uid}/meta/app`：`schemaVersion`（当前为 2）、`migratedAt`。`ensureUserData()` 看到版本已是最新就什么都不做

**2026-09 数据迁移（schemaVersion 1 → 2）**：老版本板块写死在代码里。老账号登录时 `migrateLegacySections()` 会：① 把原来 7 个板块（arena/pl300/python/project/job/review/custom，见 `LEGACY_SECTIONS`）用**原 id 当文档 ID** 写进 `sections`（已存在的不覆盖），所以老任务/老记录的 `category` 不用改；②把上一版自定义板块留下的 `'sec_'+文档ID` 格式的 `category`（任务和 log 里都有）统一去掉前缀。每一步都可以重复执行，完成后写 `meta/app`。`log` 里的 `category` 还可能是 `'reward'`（兑换）或 `'daily'`（签到），小标签见 `CAT_SHORT`。

积分/等级/连续打卡都是前端根据 `log` 集合实时算出来的（`computeStats()` / `levelInfo()` / `computeStreak()`），不是存好的字段。

---

## 代码结构

依赖方向：`core`（纯逻辑，不碰浏览器和 Firebase，可以测试） ← `data`（读写 Firebase） ← `ui` / `app`（界面）。以后的学习区页面（`study.html`）可以复用 `core` / `data` / `ui`。

```
js/
├─ firebase.js          初始化；auth、fs、FieldValue；userCols(uid) 返回 users/{uid}/ 下所有集合
├─ core/                纯逻辑
│  ├─ constants.js      SEED_*（新用户模板）、LEGACY_SECTIONS（老账号迁移）、SCHEMA_VERSION、
│  │                    CAT_SHORT、DAILY_LOGIN_POINTS、TIER_META、TIER_ICON_COLORS
│  ├─ levels.js         LEVELS 等级表 + levelInfo()
│  ├─ stats.js          computeStats() / computeStreak()（都接受可选的 now，方便测试）
│  ├─ dates.js          localISO() / fmtDateLabel()
│  ├─ icons.js          REWARD_ICONS / TASK_ICONS + 按 id 哈希分配图标
│  └─ html.js           escapeHTML()
├─ data/
│  ├─ userData.js       ensureUserData()：新用户写模板 / 老账号迁移，写 meta/app
│  ├─ awards.js         awardOnce(logCol, docId, entry)：固定文档 ID + 事务，保证只加一次分
│  └─ dailyBonus.js     每日签到（用 awardOnce）
├─ ui/
│  └─ common.js         showToast、openCelebrate(html)、closeOnBackdrop、makeConfirmDelete（点两次才删）
└─ app/                 主页面
   ├─ main.js           入口：登录 → ensureUserData → 实时订阅 → render；签到定时检查
   ├─ state.js          共享状态 S（uid、cols、logEntries、tasks、sections、rewards）
   ├─ render.js         render()：状态栏、最近记录、历史，再调各 Tab 的渲染
   ├─ tasks.js          记录 Tab：任务卡片、完成确认、任务增改删
   ├─ sections.js       板块增 / 改名 / 删
   └─ rewards.js        奖励商店 Tab：卡片、兑换确认、奖励增改删
js/core/study.js        学习区规则：积分常量、scoreQuiz、studyStreak、streakBonuses
js/data/study.js        completeUnit / submitQuiz（都用 awardOnce）、笔记读写
js/study/               学习区页面
   ├─ main.js           入口：登录 → 订阅 study 记录和测验进度 → 按 # 路由渲染
   ├─ views.js          各界面（课程 / 章节列表 / 学习页 / 测验 / 回顾）；进度变化时只刷新学习页底部，不打断阅读和视频
   ├─ content.js        读 courses/ 下的 JSON（带缓存）
   ├─ render-content.js 内容块 → HTML；Markdown 用 marked，公式用 KaTeX（study.html 从 jsDelivr 引入）
   ├─ notes.js          笔记抽屉 + 自动保存
   └─ state.js          学习区共享状态 T
```

**本地预览**：ES 模块不能双击 `index.html` 用 `file://` 打开（浏览器会拦），要在项目目录跑 `npm run serve`（即 `python -m http.server 8000`），再打开 `http://localhost:8000`。注意 Google 登录要求域名在 Firebase 控制台 → Authentication → 设置 → 已授权网域 里，`localhost` 默认就在。

## ⚠️ IP / 版权注意事项

Yijia 喜欢哈利波特主题，多次要求"魔法/巫师"风格的视觉效果（图标、进度条动画等）。**已经明确讨论过并达成共识**：可以做同一氛围的通用奇幻/魔法元素（魔杖、药水瓶、星光、咒语书……），但**不能照抄哈利波特具体的商标视觉设计**（金色飞贼的球+翅膀造型、院徽、闪电疤痕、角色形象等）。以后再加类似的视觉元素，延续这个原则就行，不需要每次都重新问。

---

## 部署 / 怎么改代码立即上线

用的是 GitHub Desktop（不是命令行 git）。流程：
1. 在这台电脑上改代码（`index.html` / `css/` / `js/`，无论是 Yijia 自己改，还是让 Claude 直接改本地文件）
2. 打开 GitHub Desktop，仓库选 `quest-log`，能看到 `Changes` 里列出改动的文件和具体 diff
3. 左下角填一句 commit 说明 → 点 `Commit to main`
4. 点顶部的 `Push origin`，大概 30-60 秒后 GitHub Pages 自动重新部署
5. 浏览器强制刷新（Ctrl+Shift+R）就是最新版本。**推送后别马上登录测试**：GitHub Pages 部署要 1-2 分钟，浏览器还会缓存旧文件约 10 分钟，这段时间打开的可能还是旧版（2026-09-28 踩过：用旧版登录的新账号被写进了旧模板）

## Firebase 项目信息

- Firebase 项目：`yaz-quest-log`（Firestore 数据库选的是新加坡 `asia-southeast1`，标准版）
- 登录方式：仅 Google 登录（`firebase.auth.GoogleAuthProvider`）
- Firestore 安全规则：原文见仓库里的 `firestore.rules`。**改规则要去控制台粘贴并点"发布"才生效**（之前踩过一次"粘贴了但没发布"导致 `Missing or insufficient permissions` 的坑），发布后同步更新 `firestore.rules`

---

## 给下一次接手的 Claude 的话

先读这份 README，再按「代码结构」找到要改的模块。改完：
1. `node --check` 检查改过的 JS 文件，`npm test` 跑核心逻辑测试
2. 涉及界面或数据读写的改动，用假的 Firebase（内存实现 compat SDK 用到的那部分接口）在浏览器里实际跑一遍——Yijia 的真实 Firebase 我们连不上，也不该在真实数据上试
3. 涉及数据结构变化的，要考虑老账号迁移（参考 `ensureUserData()` + `SCHEMA_VERSION` 的做法，每一步都要能安全重复执行）
4. **在 `CHANGELOG.md` 最上面记一笔**（见上面「改动日志规则」）
5. 让 Yijia 自己 commit → push（她用 GitHub Desktop / 网页，不需要 Claude 推送）

已知历史 bug：2026-09-28 之前「＋ 添加自定义奖励」会把点击事件当成要编辑的奖励传进弹窗，导致新奖励存成空档位（`tier:''`）、页面上不显示。已修复；`renderRewards()` 会把空档位的奖励放进小奖励里显示，编辑一次就能改成正确档位。
