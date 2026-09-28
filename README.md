# 远征日志 — 项目说明（给未来的我 / 未来的 Claude 看）

一个纯前端的学习积分 / 奖励兑换小工具，帮 Yijia 把 AI 转型学习计划（ARENA、PL-300、Python 练习、自建项目、求职、规划复盘）游戏化：做一件事记一次积分，攒够积分兑换真实奖励。

**技术栈**：纯静态 HTML/CSS/JS（无构建步骤，无框架）+ Firebase（Auth 登录 + Firestore 数据库）+ GitHub Pages 托管。数据只存在 Yijia 自己的 Firebase 项目里，不经过 Claude 或任何第三方；手机和电脑用同一个 Google 账号登录，实时同步。

## 文件

- `index.html` — 整个应用，界面 + 逻辑都在这一个文件里（一个 `<style>`、一段主体 HTML、一个 `<script>`）
- `firebase-config.js` — Yijia 自己 Firebase 项目的连接信息（apiKey 等，不是密钥，允许公开）
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
- **每日上线奖励**：每天第一次打开（登录状态下）自动 +5 分（`DAILY_LOGIN_POINTS`，`ensureDailyLoginBonus()`）。写进 `log` 集合，文档 ID 固定为 `daily-YYYY-MM-DD`，用事务保证多设备同时打开每天也只加一次；页面跨零点或从后台切回时会补发。`category:'daily'` 的记录只计积分，**不计入「记录次数」和连续打卡天数**。

### 2. 「记录」Tab —— 学习任务（像奖励商店一样的卡片式）
这是最新的交互方式，**已经不是**表单弹窗式记录了：
- 按类别分组显示任务卡片（`CATEGORIES` 数组的 7 个类别：arena/pl300/python/project/job/review/custom）
- 每张卡片：自动分配的小图标（`iconForTask()`，图标库是 `TASK_ICONS`，10 个通用学习/成就主题图标）+ 任务名 + 积分
- 卡片按钮：**编辑**（弹窗改名称/类别/积分）、**删除**（点一下变"确认删除？"，4 秒内再点才真删）、**完成 ✓**（点了弹二次确认 → 确认后写入一条 `log` 记录并弹庆祝弹窗+撒花动画，文案："你太棒了！完成了一次「XX」学习任务 🎉 已添加 X 积分！"）
- 底部「＋ 添加自定义学习任务」可以新增任务，**积分允许填 0**（比如"心安理得摸鱼"类的 0 分任务，用户明确要求过）
- 首次登录会自动把 `CATEGORIES` 里预设的 16 条里程碑写进 `tasks` 集合当默认任务（`ensureSeedTasks()`），之后改代码里的 `CATEGORIES` 不会覆盖用户已经建过的任务
- 下面还有「最近记录」列表（`renderRecent()`）

> 旧版本的「记录一次学习」表单弹窗（类别下拉+里程碑下拉+自定义标题+积分+备注+日期，`openLogModal`/`submitLogEntry`/`CATEGORIES.presets` 那套）**代码还留着但入口按钮已经删掉了**，属于死代码，不会被用户看到，以后如果要彻底清理或者要恢复"手动填表单记录"这种更灵活的记录方式，可以从这里改。

### 3. 「奖励商店」Tab
- 三档：小奖励 / 中奖励 / 大奖（`TIER_META`），默认种子奖励见 `DEFAULT_REWARDS`（奶茶、打游戏、摸鱼、买书、新加坡周边游、马来西亚租摩托、东南亚穷游、新加坡买摩托车）
- 每张卡片：自动分配的小图标（`iconForReward()`，图标库 `REWARD_ICONS`，10 个通用魔法/奇幻主题图标——魔杖、药水瓶、咒语书等，**同样是为了避开哈利波特商标图案而设计的通用款**）+ 名称 + 所需积分 + 攒够进度条
- 兑换：点"兑换"→ 二次确认弹窗 → 确认后从 `log` 里写一条 `spend` 记录 → 弹庆祝弹窗+撒花动画（"「XX」奖励已兑换 🎉 已扣除 X 积分。奖励商店欢迎下次光临！"）
- 编辑/删除跟学习任务同一套交互
- 「＋ 添加自定义奖励」可以新增奖励，**积分同样允许填 0**

### 4. 「历史」Tab
- 所有记录按日期分组显示（`renderHistory()`）

### 5. 等级系统
`LEVELS` 数组，**现在是 20 级**，按累计获得的总积分（不是可用积分，兑换奖励不扣这个数）从低到高：新手上路(0) → 打好地基(100) → 小试牛刀(250) → 渐入佳境(450) → 独当一面(700) → 融会贯通(1000) → 炉火纯青(1400) → 崭露头角(1900) → 步入正轨(2500) → 渐成气候(3200) → 游刃有余(4000) → 登堂入室(5000) → 自成一派(6200) → 声名鹊起(7600) → 独步一方(9200) → 名扬四海(11000) → 出类拔萃(13000) → 登峰造极(15200) → 一代宗师(17600) → 传奇远征者(20200)。超过最后一级后，`levelInfo()` 会自动按"每 +5000 分再升一级"继续延伸下去，不会封顶。

---

## 数据结构（Firestore）

所有数据都在 `users/{uid}/...` 下面，按 uid 隔离，安全规则只允许本人读写自己的数据（见文末规则原文）。三个子集合：

- `users/{uid}/log`：每条学习记录或兑换记录。字段：`kind`（'earn' 或 'spend'）、`category`、`label`、`amount`、`note`、`dateISO`、`ts`
- `users/{uid}/rewards`：奖励定义。字段：`name`、`tier`（small/medium/big）、`cost`、`active`、`ts`
- `users/{uid}/tasks`：学习任务定义。字段：`name`、`category`（对应 `CATEGORIES` 的 id）、`points`、`active`、`ts`

积分/等级/连续打卡都是前端根据 `log` 集合实时算出来的（`computeStats()` / `levelInfo()` / `computeStreak()`），不是存好的字段。

---

## 代码里关键的东西在哪（方便以后改）

- `CATEGORIES`（学习类别 + 预设里程碑，也是任务分组依据）
- `DEFAULT_REWARDS`（首次登录写入的默认奖励）
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
