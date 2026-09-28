# 远征日志 — 项目说明（给未来的我 / 未来的 Claude 看）

一个纯前端的学习积分 / 奖励兑换小工具，帮 Yijia 把 AI 转型学习计划（ARENA、PL-300、Python 练习、自建项目、求职、规划复盘）游戏化：做一件事记一次积分，攒够积分兑换真实奖励。

**技术栈**：纯静态 HTML/CSS/JS（无构建步骤，无框架）+ Firebase（Auth 登录 + Firestore 数据库）+ GitHub Pages 托管。数据只存在 Yijia 自己的 Firebase 项目里，不经过 Claude 或任何第三方；手机和电脑用同一个 Google 账号登录，实时同步。

## 文件

- `index.html` — 整个应用，界面 + 逻辑都在这一个文件里（一个 `<style>`、一段主体 HTML、一个 `<script>`）
- `firebase-config.js` — Yijia 自己 Firebase 项目的连接信息（apiKey 等，不是密钥，允许公开）
- `firestore.rules` — Firestore 安全规则的存档（**真正生效的是 Firebase 控制台里的那份**，改规则要去控制台发布，然后同步回这里）
- `README.md` — 这份文件

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
`LEVELS` 数组，**现在是 20 级**，按累计获得的总积分（不是可用积分，兑换奖励不扣这个数）从低到高：新手上路(0) → 打好地基(100) → 小试牛刀(250) → 渐入佳境(450) → 独当一面(700) → 融会贯通(1000) → 炉火纯青(1400) → 崭露头角(1900) → 步入正轨(2500) → 渐成气候(3200) → 游刃有余(4000) → 登堂入室(5000) → 自成一派(6200) → 声名鹊起(7600) → 独步一方(9200) → 名扬四海(11000) → 出类拔萃(13000) → 登峰造极(15200) → 一代宗师(17600) → 传奇远征者(20200)。超过最后一级后，`levelInfo()` 会自动按"每 +5000 分再升一级"继续延伸下去，不会封顶。

---

## 数据结构（Firestore）

所有数据都在 `users/{uid}/...` 下面，按 uid 隔离，安全规则只允许本人读写自己的数据（规则原文见 `firestore.rules`，2026-09-28 用规则测试平台验证过：别的账号读取被拒绝）。子集合：

- `users/{uid}/log`：每条学习记录或兑换记录。字段：`kind`（'earn' 或 'spend'）、`category`、`label`、`amount`、`note`、`dateISO`、`ts`
- `users/{uid}/rewards`：奖励定义。字段：`name`、`tier`（small/medium/big）、`cost`、`active`、`ts`
- `users/{uid}/tasks`：任务定义。字段：`name`、`category`（= 所属板块在 `sections` 里的文档 ID）、`points`、`active`、`ts`
- `users/{uid}/sections`：板块。文档 ID 就是板块 id。字段：`label`、`ts`（排序）、`short`（可选，历史记录小标签用的简称；老板块迁移时带上，改名后删除，之后标签显示全名）
- `users/{uid}/meta/app`：`schemaVersion`（当前为 2）、`migratedAt`。`ensureUserData()` 看到版本已是最新就什么都不做

**2026-09 数据迁移（schemaVersion 1 → 2）**：老版本板块写死在代码里。老账号登录时 `migrateLegacySections()` 会：① 把原来 7 个板块（arena/pl300/python/project/job/review/custom，见 `LEGACY_SECTIONS`）用**原 id 当文档 ID** 写进 `sections`（已存在的不覆盖），所以老任务/老记录的 `category` 不用改；②把上一版自定义板块留下的 `'sec_'+文档ID` 格式的 `category`（任务和 log 里都有）统一去掉前缀。每一步都可以重复执行，完成后写 `meta/app`。`log` 里的 `category` 还可能是 `'reward'`（兑换）或 `'daily'`（签到），小标签见 `CAT_SHORT`。

积分/等级/连续打卡都是前端根据 `log` 集合实时算出来的（`computeStats()` / `levelInfo()` / `computeStreak()`），不是存好的字段。

---

## 代码里关键的东西在哪（方便以后改）

- `SEED_SECTIONS` / `SEED_TASKS` / `SEED_REWARDS`（新用户模板）、`LEGACY_SECTIONS`（只给老账号迁移用）、`SCHEMA_VERSION`
- `ensureUserData()` / `seedNewUser()` / `migrateLegacySections()`（登录后先跑，完成后才开始订阅数据）
- `openSectionModal()` / `submitSection()` / `onDeleteSectionClick()`（板块增/改名/删）
- `TIER_META` / `TIER_ICON_COLORS`（奖励三档的标题/颜色）
- `LEVELS`（等级门槛，改这里就能调整等级数量/名字/分数线）
- `REWARD_ICONS` / `iconForReward()`（奖励图标库 + 按 doc id 哈希自动分配，同一个奖励永远同一个图标）
- `TASK_ICONS` / `iconForTask()`（任务图标库，逻辑同上）
- `hashStr()`（两个图标分配函数共用的字符串哈希）
- `renderRewards()` / `rewardCardHTML()`、`renderTasks()` / `taskCardHTML()`（两个 tab 的卡片渲染，结构几乎对称）
- `openRewardModal()` / `submitReward()`（奖励增/改共用一个表单，`editingRewardId` 判断是新增还是编辑）
- `openTaskModal()` / `submitTask()`（任务增/改，同理，`editingTaskId`）
- `openRedeemConfirm()` / `confirmRedeem()`（兑换二次确认）
- `openTaskConfirm()` / `confirmTaskLog()`（完成任务二次确认）
- `openCelebrate(kind, name, amount)`（庆祝弹窗+撒花动画，`kind` 传 `'reward'` 或 `'task'` 决定文案）

## ⚠️ IP / 版权注意事项

Yijia 喜欢哈利波特主题，多次要求"魔法/巫师"风格的视觉效果（图标、进度条动画等）。**已经明确讨论过并达成共识**：可以做同一氛围的通用奇幻/魔法元素（魔杖、药水瓶、星光、咒语书……），但**不能照抄哈利波特具体的商标视觉设计**（金色飞贼的球+翅膀造型、院徽、闪电疤痕、角色形象等）。以后再加类似的视觉元素，延续这个原则就行，不需要每次都重新问。

---

## 部署 / 怎么改代码立即上线

用的是 GitHub Desktop（不是命令行 git）。流程：
1. 在这台电脑上直接改 `index.html`（无论是 Yijia 自己改，还是让 Claude 通过设备连接直接改这个本地文件）
2. 打开 GitHub Desktop，仓库选 `quest-log`，能看到 `Changes` 里列出改动的文件和具体 diff
3. 左下角填一句 commit 说明 → 点 `Commit 1 file to main`
4. 点顶部的 `Push origin`，大概 30-60 秒后 GitHub Pages 自动重新部署
5. 浏览器刷新（必要时强制刷新清缓存）就是最新版本

## Firebase 项目信息

- Firebase 项目：`yaz-quest-log`（Firestore 数据库选的是新加坡 `asia-southeast1`，标准版）
- 登录方式：仅 Google 登录（`firebase.auth.GoogleAuthProvider`）
- Firestore 安全规则（**必须点右上角"发布"才生效**，之前踩过一次"粘贴了但没发布"导致 `Missing or insufficient permissions` 的坑）：

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{uid}/{document=**} {
      allow read, write: if request.auth != null && request.auth.uid == uid;
    }
  }
}
```

---

## 给下一次接手的 Claude 的话

如果 Yijia 下次把整个文件夹发过来（或者通过设备连接指到这个本地路径），直接读 `index.html` 全文 + 这份 README 就能完整了解现状。改代码时优先用"读现有文件 → 定位精确锚点文本 → 原子替换（全部匹配到才真正写入，否则整体放弃）"这种方式改这一个大文件，比整个重写更安全，避免动到用户已经积累的真实数据结构或引入语法错误。改完一定要跑一次 Node.js 的内联 `<script>` 语法检查（把文件里的 `<script>` 块整个提出来跑 `new Function(code)`），再让用户走 GitHub Desktop 的 commit → push 流程上线。
