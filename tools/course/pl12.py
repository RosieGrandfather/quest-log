"""pl300-0 第 12 节：保护与治理"""
from pllib import *

nb = Notebook()

C_ROLE = nb.cell('''
# 工作区角色的能力（课程的简化整理，真实权限更细，以官方「Roles in workspaces」为准）
ROLES = {
    "Admin":       {"view", "edit", "publish_app", "manage_access", "delete_workspace"},
    "Member":      {"view", "edit", "publish_app"},
    "Contributor": {"view", "edit"},
    "Viewer":      {"view"},
}
def can(role, action): return action in ROLES[role]

for action in ("view", "edit", "publish_app", "manage_access", "delete_workspace"):
    print(f"{action:17s}", {r: can(r, action) for r in ROLES})
''')

C_RLS = nb.cell('''
sales = [("North", "Pen", 20), ("North", "Desk", 300), ("South", "Pen", 40), ("East", "Desk", 120)]
security = {"ann@corp.com": ["North"], "bob@corp.com": ["South", "East"]}   # 动态 RLS 用的「用户-地区」表

def total(rows): return sum(a for _, _, a in rows)

def rls_filter(user, workspace_role):
    if workspace_role in ("Admin", "Member", "Contributor"):   # 有编辑权限的角色不受 RLS 限制
        return sales
    allowed = security.get(user, [])                            # 对应 DAX：[Email] = USERPRINCIPALNAME()
    return [r for r in sales if r[0] in allowed]

for user, role in (("ann@corp.com", "Viewer"), ("bob@corp.com", "Viewer"), ("ann@corp.com", "Member"), ("nobody@corp.com", "Viewer")):
    rows = rls_filter(user, role)
    print(f"{user:16s} {role:7s} 看到 {len(rows)} 行，合计 {total(rows)}")
''')

C_LABEL = nb.cell('''
# 敏感度标签：越往后越敏感。课程简化：从多个来源创建内容时，继承其中最敏感的一个
ORDER = ["Public", "General", "Confidential", "Highly Confidential"]

def inherited(*labels):
    return max(labels, key=ORDER.index)

print("来源 General + Confidential →", inherited("General", "Confidential"))
print("来源 Public + General →", inherited("Public", "General"))
print("来源 Confidential + Highly Confidential →", inherited("Confidential", "Highly Confidential"))
''')

unit = {
 "id": "u12",
 "title": "保护与治理：角色、行级安全与敏感度标签",
 "en": "Secure & Govern: Roles, Row-Level Security & Sensitivity Labels",
 "minutes": 40,
 "objectives": [
  "说出**工作区四个角色**（管理员、成员、参与者、查看者）各能做什么，并能为场景选角色",
  "区分**工作区角色、项目级访问 (item-level access) 与语义模型权限**（读取、**生成 Build**、再共享）",
  "写出**行级安全 (RLS)** 的**静态**与**动态**角色，并知道在 Desktop 里怎么测试、在服务里怎么分配成员",
  "说出 RLS 的关键限制：只约束**查看者**，不约束有编辑权限的角色",
  "说明**敏感度标签 (sensitivity labels)** 来自哪里、怎么继承，以及它们在导出时的作用",
 ],
 "blocks": [
  T(r"""
### 先说这一小节要干什么

安全这一块的考法非常「场景化」：给你一个需求（「销售只看自己区域」「合作伙伴只能读不能改」「导出的 Excel 也要带保密标记」），问你**用哪一层的哪个功能**。要答对，要先知道 Power BI 里**有四层不同的控制**，它们管的是不同的事：

1. **工作区角色**：你能在这个工作区里**做什么**；
2. **项目级 / 语义模型权限**：你能**访问哪个对象**、能不能基于它**生成 (Build)** 新内容；
3. **行级安全 (RLS)**：你能看到数据里的**哪些行**；
4. **敏感度标签**：这份内容有多**敏感**，以及它被导出后要怎样被**保护**。

**学完它你就能看懂这几件事：**

- 为什么「把销售放进工作区的 Viewer 角色」还不能让他们只看自己的区域；
- 为什么一个 Member 看到的数据比同一个 RLS 角色下的 Viewer 多；
- 动态 RLS 里 `USERPRINCIPALNAME()` 是干什么的；
- 敏感度标签到底影响内容，还是影响数据。

**本小节安排（约 40 分钟）**：导读（2 分钟）→ 工作区角色（6 分钟）→ 项目级与语义模型访问（5 分钟）→ RLS（17 分钟，含视频）→ 敏感度标签（6 分钟）→ 总结（4 分钟）。

### 工作区角色

> **标准定义 · 工作区角色 (workspace roles)**
>
> 工作区有四个角色，从高到低：**管理员 (Admin)**——管理整个工作区，包括添加或移除人员、删除工作区；**成员 (Member)**——可编辑和发布内容，可以添加权限不高于自己的人；**参与者 (Contributor)**——可以创建和编辑内容，但**不能发布或更新应用**；**查看者 (Viewer)**——只能**查看**内容。角色是给**一起制作和管理**内容的人用的。
>
> *English: Admin manages the whole workspace; Member can edit and publish and add people with equal or lower roles; Contributor can create and edit but not publish apps; Viewer can only view.*

**白话版：「查看者只读，参与者能做不能发，成员能发，管理员能管人」。** 下面是课程整理的简化表（**真实权限更细，以官方「Roles in workspaces」为准**）：
""" + C_ROLE + r"""

**读输出：** 只有 Viewer 不能编辑；`Admin` 和 `Member` 都能发布应用；只有 `Admin` 能管理访问和删除工作区。**场景题常见：** 「需要让一个人只看报表」→ Viewer（或更好的是给应用）；「需要他制作报表但不要发布应用」→ Contributor。

### 项目级访问与语义模型权限

**项目级访问 (item-level access)：** 不用把人加进工作区，也能给他访问**某一个报表或语义模型**的权限：通过**共享**，或在项目的**管理权限 (Manage permissions)** 里添加。对**语义模型**还有几个权限要分清：**读取 (Read)**——能看到基于它的报表里的数据；**生成 (Build)**——能基于这个语义模型**创建新内容**（新报表、在 Excel 里分析）；**再共享 (Reshare)**——能把访问权再给别人；**写入 (Write)**——能修改它。**一个考点：** 只被授予报表的访问，**不等于**可以基于它的语义模型做新报表，要单独给 **Build**。

### 行级安全 (RLS)

> **标准定义 · 行级安全 (row-level security, RLS)**
>
> RLS 用**角色 (role)** 里的 **DAX 表筛选表达式**限制用户能看到的**行**。流程：在 **Desktop** 里 **建模 → 管理角色**，为某张表写筛选，例如 `[Region] = "North"`（**静态 RLS**），或用 `[Email] = USERPRINCIPALNAME()` 配合一张**用户-区域映射表**（**动态 RLS**，一个角色服务所有人）；用 **以角色身份查看 (View as)** 测试；**发布**后，在服务里的语义模型 **安全性 (Security)** 页面把**用户或安全组**加到角色里。筛选沿着**关系**从维度表传播到事实表。**RLS 只限制工作区里的「查看者」**，**管理员、成员、参与者**可以访问语义模型的全部数据，不受 RLS 限制。
>
> *English: RLS uses DAX filter expressions in roles to limit visible rows; static roles hard-code values, dynamic roles use USERPRINCIPALNAME() with a mapping table; test with View as, assign members in the service; it restricts Viewers only, not users with edit roles.*

**白话版：「同一份报表，不同的人看到不同的行」。**
""" + C_RLS + r"""

**读输出：** 同一份 4 行的数据：`ann` 作为 Viewer，只看到 North 的 2 行，合计 320；`bob` 看到 South 和 East 的 2 行，合计 160；**同一个 `ann` 如果是 Member，就看到全部 4 行 480**，因为 RLS 不约束有编辑权限的角色；一个**不在映射表里**的用户，看到 0 行，不是报错。对应的动态 RLS DAX 是：

```text
-- 在「用户地区映射」表上定义角色筛选
[Email] = USERPRINCIPALNAME ()
```
"""),
  V("MxU_FYSSnYU", "How to Setup Row-Level Security (RLS) in Power BI", 5),
  T(r"""
> 视频（Guy in a Cube，约 5 分钟）演示在 Desktop 里建立 RLS 角色。**我只核实了它存在且可嵌入，内容没有看过**；看的时候对照上面的流程：管理角色 → 写筛选 → View as → 发布 → 在服务里分配成员。

**RLS 的几个考点：**

- 筛选默认**沿关系的方向**传播（维度到事实）；在维度表上设的 RLS，会筛选与它相关的事实表；**反方向**（从事实表影响维度表）需要在关系上勾选**双向安全筛选**，要谨慎；
- 一个用户属于**多个角色**时，看到的是各角色允许行的**并集**；
- **DirectQuery** 下 RLS 可以在源端实现，也可以在 Power BI 里定义，要看场景；
- 如果需要限制某一**列**或**表**（让人完全看不到它），那是**对象级安全 (object-level security, OLS)**，不是 RLS。

### 敏感度标签

> **标准定义 · 敏感度标签 (sensitivity labels)**
>
> 来自 **Microsoft Purview 信息保护**的标签（如 Public、General、Confidential、Highly Confidential），可以应用在 Power BI 的**语义模型、报表、仪表板、数据流**以及 `.pbix` 文件上。标签是**对内容的分类**，与 RLS 管**行**不同；它可以**继承**（从数据源或上游内容继承到下游），并且在内容被**导出到 Excel、PowerPoint、PDF 或 .pbix 文件**时，**标签和它配置的保护设置会跟着带出去**（比如加密、水印，以组织的策略为准）。可以在 Desktop 里设置，也可以在服务里设置；管理员可以要求**强制打标签**。
>
> *English: Sensitivity labels from Microsoft Purview Information Protection classify content (semantic models, reports, dashboards, dataflows, .pbix), can be inherited downstream, and travel with exported files along with their protection settings.*

**白话版：「给内容贴一张保密标签，标签跟着内容走」。** 课程用一个简化的「继承最敏感的」来帮你记方向：
""" + C_LABEL + r"""

**读输出：** 来源是 General 和 Confidential 时，新内容取 Confidential；来源是 Public 和 General 时取 General；来源是 Confidential 和 Highly Confidential 时取 Highly Confidential。**这是课程的简化，真实的继承规则（包括谁可以降低标签、是否强制）受组织策略影响，以官方文档为准。**

### 这一小节你要带走的三句话

1. **四层控制各管一件事**：工作区角色管「能做什么」，项目级 / 语义模型权限管「访问哪个对象、能不能 Build」，RLS 管「看到哪些行」，敏感度标签管「内容有多敏感、导出后怎么保护」。
2. **RLS：在 Desktop 定义角色 → View as 测试 → 发布 → 在服务里分配成员**；动态 RLS 用 `USERPRINCIPALNAME()`；**只限制查看者**，管理员、成员、参与者不受限制。
3. **敏感度标签是内容分类，可继承，导出时跟着走**；它不筛选行，也不替代 RLS。
"""),
  THINK("**（场景判断）** 全球销售团队要看同一份报表，但每个销售只能看自己所在国家的行。应怎么实现？你会把销售们放进什么工作区角色？", r"""
用**动态 RLS**：做一张「用户 - 国家」映射表，角色筛选写 `[Email] = USERPRINCIPALNAME()`，发布后在语义模型的安全性里把销售（或销售所在的安全组）加到这个角色。通过**应用**或共享给他们，工作区里应是 **Viewer** 或不加入工作区——因为 Admin、Member、Contributor 不受 RLS 约束。
"""),
  THINK("**（概念辨析）** 一个同事被加为工作区的 Contributor，也被加入了一个 RLS 角色，却能看到所有行。这是 bug 吗？", r"""
**不是**：RLS 只约束 Viewer。有编辑权限的角色（管理员、成员、参与者）在这个工作区里对语义模型有写权限，不受 RLS 限制。需要限制他，就把他降为 Viewer，或者不要让他有编辑角色。
"""),
  THINK("**（联系后续）** 下一节是考试策略。想一想：本课程前 12 节里，哪几个功能你在 OMRON 的租户里**没法实际操作**？你打算怎样补？", r"""
创建工作区、发布应用、订阅、数据警报、网关、RLS 的服务端分配成员、敏感度标签的设置，基本都涉及服务端权限，可能没法动手。补法：用官方**免费练习评估**检验这些概念，读官方文档里的**步骤说明**，并在自己注册的试用租户里练（不用公司数据）；把这几块当作**「场景识别」题**来背：「谁能做什么、用哪个功能」。
"""),
  KW(("工作区角色","workspace roles","管理员、成员、参与者、查看者"),
     ("项目级访问","item-level access","对单个报表或语义模型授权"),
     ("读取","Read","能看到语义模型里的数据"),
     ("生成","Build","能基于语义模型创建新内容"),
     ("再共享","Reshare","能把访问权再给别人"),
     ("行级安全","row-level security (RLS)","按角色限制能看到的行"),
     ("静态 RLS","static RLS","角色筛选里写死值，如 Region = North"),
     ("动态 RLS","dynamic RLS","用 USERPRINCIPALNAME() 配映射表，一个角色服务所有人"),
     ("USERPRINCIPALNAME","USERPRINCIPALNAME()","返回当前用户的登录名（邮箱）"),
     ("以角色身份查看","View as","在 Desktop 里测试 RLS"),
     ("对象级安全","object-level security (OLS)","隐藏整张表或某一列"),
     ("敏感度标签","sensitivity label","Purview 的内容分类标签"),
     ("标签继承","label inheritance","标签从上游传到下游内容"),
     ("Microsoft Purview 信息保护","Microsoft Purview Information Protection","敏感度标签所在的服务"),
  ),
 ],
 "references": [
  PL_STUDY_GUIDE,
  {"title": "Microsoft Learn：Row-level security (RLS) with Power BI", "url": "https://learn.microsoft.com/en-us/fabric/security/service-admin-row-level-security", "note": "RLS 的流程、动态 RLS、与工作区角色的关系"},
  {"title": "Microsoft Learn：Roles in workspaces", "url": "https://learn.microsoft.com/en-us/fabric/fundamentals/roles-workspaces", "note": "工作区角色的权限表"},
  {"title": "Microsoft Learn：Sensitivity labels in Power BI", "url": "https://learn.microsoft.com/en-us/power-bi/enterprise/service-security-sensitivity-label-overview", "note": "敏感度标签、继承与导出"},
  {"title": "Microsoft Learn：Build permission for shared semantic models", "url": "https://learn.microsoft.com/en-us/power-bi/connect-data/service-datasets-build-permissions", "note": "Build 权限与语义模型访问"},
 ],
 "quiz": {"questions": [
  Q("一个团队里每位销售只能看自己区域的行，且人员经常变动。最易维护的做法是：",
    ["动态 RLS：映射表加 USERPRINCIPALNAME()", "为每个销售各建一个静态角色", "为每个区域各复制一份报表", "把销售加为工作区成员"], 0,
    "动态 RLS 用一张用户-区域映射表，一个角色服务所有人，人员变动只需更新映射表。成员不受 RLS 限制。"),
  Q("RLS 对下列哪个工作区角色**不起**限制作用？",
    ["Member", "Viewer", "没有加入工作区、只通过应用访问的读者", "通过共享链接查看报表的读者"], 0,
    "RLS 只约束 Viewer 以及通过应用、共享访问的读者；管理员、成员、参与者有编辑权限，看到全部数据。"),
  Q("同事只被授予了某份报表的访问，却想基于它的语义模型在 Excel 里做分析。需要额外授予：",
    ["语义模型的 Build 权限", "工作区的管理员角色", "敏感度标签", "RLS 角色"], 0,
    "基于语义模型创建新内容需要 Build 权限，只给报表访问不等于有 Build。"),
  Q("敏感度标签和 RLS 的区别是：",
    ["标签是对内容的分类并随导出带走；RLS 限制能看到的行", "两者都限制能看到的行", "标签只能用在 Excel 里", "RLS 会在导出时加密文件"], 0,
    "敏感度标签是内容的分类标记，导出到 Excel、PowerPoint、PDF 时标签和保护设置会跟着走；RLS 限制用户在报表里能看到哪些行。"),
  Q("在 Desktop 里定义好 RLS 角色并发布后，还必须做的一步是：",
    ["在服务里的语义模型安全性页面把用户或安全组加到角色", "把所有读者设为工作区管理员", "关闭自动页面刷新", "启用 DirectQuery"], 0,
    "角色定义随语义模型发布，但成员要在服务里分配；没有被分配进任何角色的查看者，看不到受 RLS 保护的数据。"),
 ]},
}
retarget(unit, [1, 0, 2, 3, 1])

if __name__ == '__main__':
    dump(unit, "pl300-0", "u12-security.json", n_questions=5)
