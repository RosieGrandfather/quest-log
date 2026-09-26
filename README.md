# 远征日志 — 部署与使用说明

一个纯前端的学习积分 / 奖励兑换小工具。代码就是这个文件夹里的三个文件，没有服务器、没有构建步骤。数据存在你自己的 Firebase 项目里，不经过 Claude、不经过任何第三方。手机和电脑用同一个 Google 账号登录，就能看到同一份数据。

## 文件说明
- `index.html` — 整个应用，界面 + 逻辑都在这一个文件里
- `firebase-config.js` — 你自己 Firebase 项目的连接信息，需要你手动填
- `README.md` — 就是这份说明

---

## 第一步：创建你自己的 Firebase 项目（免费）

1. 打开 https://console.firebase.google.com ，用你自己的 Google 账号登录
2. 点"添加项目"，起个名字（比如 `yijia-quest-log`），一路默认下一步，不需要开 Google Analytics
3. 项目建好后，左侧菜单点 **Firestore Database** → "创建数据库" → 选**生产模式** → 选一个离你近的区域（`asia-southeast1`，新加坡）
4. 左侧菜单点 **Authentication** → "开始使用" → "Sign-in method" → 启用 **Google** 这个登录方式
5. 左侧菜单点 **项目设置**（齿轮图标）→ 往下翻到"你的应用" → 点网页图标 `</>` → 注册一个网页应用（随便起个名字，不用勾 Hosting）→ 注册后会看到一段 `const firebaseConfig = {...}` 代码，先别关这个页面，等下要用

## 第二步：设置安全规则（很重要，别跳过）

在 Firestore Database → **规则 (Rules)** 标签页，把内容整个换成：

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

点右上角"发布"。这条规则的意思是：**只有登录后的你自己，能读写自己名下的数据**，别人一个字节都读不到、写不了。

## 第三步：填入你的配置

打开 `firebase-config.js`，把第一步复制的那段配置粘贴进去，替换掉里面的占位符文字。

## 第四步：放到 GitHub 上，开启免费托管

1. 去 github.com 建一个新仓库（比如 `quest-log`），Public 就行（代码本身没有隐私问题，你的数据不在这个仓库里，在 Firebase 里）
2. 把这个文件夹里的三个文件上传 / 推送进去
3. 仓库 **Settings → Pages** → Source 选 "Deploy from a branch" → 选 `main` 分支、根目录 `/ (root)` → Save
4. 等 1-2 分钟，页面顶部会出现一个网址，形如：
   `https://<你的GitHub用户名>.github.io/quest-log/`
5. 打开这个网址，点"用 Google 账号登录"，登录后第一次会自动帮你把默认的 8 个奖励写进去

---

## 以后怎么改代码、怎么立即上线

在你电脑上装一个 Git（Mac/Linux 通常自带，Windows 装 [Git for Windows](https://git-scm.com/download/win)），第一次把仓库克隆下来：

```bash
git clone https://github.com/<你的用户名>/quest-log.git
cd quest-log
```

以后每次想改（比如调整积分数值、加新类别），直接编辑 `index.html`，改完运行：

```bash
git add -A
git commit -m "说明这次改了什么"
git push
```

`git push` 之后，GitHub Pages 会在大概 **30-60 秒内自动重新部署**——不需要额外的"发布"按钮，push 本身就是部署。刷新网页（可能要强制刷新 / 清一下缓存）就是最新版本。

如果暂时不想装 Git，也可以在 GitHub 网页上直接点开 `index.html` → 铅笔图标编辑 → 改完点 "Commit changes"，效果一样，只是没有本地版本历史。

## 手机怎么用

手机浏览器打开同一个 `https://xxx.github.io/quest-log/`，用**同一个** Google 账号登录，看到的就是电脑上同一份数据，实时同步。可以在浏览器菜单里选"添加到主屏幕"，图标就跟个 App 一样。

## 想加功能怎么办

代码结构很直接：`CATEGORIES`（学习类别和默认分值）、`LEVELS`（等级门槛）、`DEFAULT_REWARDS`（默认奖励，只在你第一次登录、且奖励是空的时候写入一次，之后改代码不会覆盖你已经加过的奖励）都在 `index.html` 顶部的 `<script>` 里，改这几个数组最省事。也可以把这份代码带回来找我改，直接告诉我这个仓库的内容或者贴 `index.html` 就行。
