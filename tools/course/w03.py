"""wm-0 第 3 节：无模型学习（v3 格式，2026-10-04）"""
from unitlib import *
from w03c import C_EPS, C_PRED, C_BIASVAR, C_CLIFF, C_DECAY
from w03_quiz import QUIZ

unit = {
 "id": "u03",
 "title": "无模型学习：蒙特卡洛、TD 与 Q-learning",
 "en": "Model-free RL: Monte Carlo, TD & Q-learning",
 "minutes": 105,
 "objectives": [
  "区分 **预测 (prediction)** 与 **控制 (control)**，理解为什么 **无模型 (model-free)** 学习只靠交互样本、不需要知道 $P$ 和 $R$",
  "掌握 **蒙特卡洛 (Monte Carlo)** 预测与 **TD(0)** 的更新式，理解 **自举 (bootstrapping)** 和 **TD 误差 (TD error)**，并用实验比较两者",
  "说清蒙特卡洛与 TD 的 **偏差-方差权衡 (bias–variance trade-off)**，并用采样数据验证",
  "理解 **探索与利用 (exploration vs exploitation)** 与 **$\\varepsilon$-贪心 ($\\varepsilon$-greedy)**，写出 **SARSA** 和 **Q-learning** 的更新式",
  "分清 **同策略 (on-policy)** 与 **异策略 (off-policy)**，能解释悬崖行走里 SARSA 与 Q-learning 为什么学出不同的路径",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

上一节的动态规划有两个前提：知道环境模型 $P,R$，并且能扫描所有状态。现实里这两条几乎都不成立：没人告诉你机器人关节动一下世界会怎样变，也没人给你列出所有的游戏画面。这一节去掉第一个前提：**不要模型，只靠「做一步、看结果」的样本学习价值**。这类方法统称**无模型 (model-free)** 强化学习，包括**蒙特卡洛**、**时序差分 (temporal-difference, TD)** 和它的控制版本 **SARSA**、**Q-learning**。其中的 Q-learning 是 DQN 的前身，也是整个强化学习里最重要的算法之一。

**这一节和世界模型的关系。** 无模型方法有一个代价：**样本效率低**。每次更新都要真的去环境里走一步，要走几十万、几百万步才学得会。世界模型要解决的正是这件事：先学一个环境的副本，之后很多更新就可以在「想象」里做，少打扰真实环境。同时，这一节的**自举目标**（用「奖励 + 下一状态的价值估计」去训练价值函数）也是世界模型类方法（如 Dreamer 的 critic）训练价值网络的基本思路。

**学完它你就能看懂这几件事：**

- DQN 论文里那个损失 $\big(r+\gamma\max_{a'}Q_{\text{target}}(s',a')-Q(s,a)\big)^2$ 的每一项是什么，为什么要「目标网络」（第 4 节会用到）；
- 为什么强化学习里到处是 $\varepsilon$（$\varepsilon$-贪心）、「熵正则」，它们都在解决同一个问题：不能只利用已知的好动作；
- 「同策略 (on-policy)」与「异策略 (off-policy)」：PPO 为什么是前者、DQN 和经验回放为什么是后者；
- 为什么有人说「Q-learning 学的是最优价值，SARSA 学的是实际会怎么做的价值」。

**本节安排（约 105 分钟）**：无模型预测与蒙特卡洛（10 分钟）→ TD(0)（10 分钟）→ 动手实验：MC 对 TD（10 分钟）→ 偏差与方差（10 分钟）→ 探索与 $\varepsilon$-贪心（10 分钟）→ SARSA 与 Q-learning（12 分钟）→ 视频（29 分钟）→ 悬崖行走实验（12 分钟）→「想一想」。视频是英文的，可以打开 YouTube 的中文字幕。

### 预测与控制，无模型预测的第一种办法：蒙特卡洛

强化学习有两类基本问题。**预测 (prediction)**：给定一个策略 $\pi$，估计它的价值函数 $v_\pi$（上一节的策略评估）。**控制 (control)**：找到最优策略。无模型的时候，先看预测。

> **标准定义 · 蒙特卡洛预测 (Monte Carlo prediction)**
>
> 让策略 $\pi$ 玩很多个回合，对每个状态 $s$，把「$s$ 出现之后得到的回报」记下来取平均，作为 $v_\pi(s)$ 的估计。**首次访问 (first-visit)** 只取每个回合里第一次到达 $s$ 之后的回报，**每次访问 (every-visit)** 取每次到达之后的回报。写成增量形式（$\alpha$ 是**步长 (step size)**）：
>
> $$V(S_t)\leftarrow V(S_t)+\alpha\big[G_t-V(S_t)\big]$$
>
> 由大数定律，估计收敛到 $v_\pi(s)$。目标 $G_t$ 是真实回报的无偏样本，但必须等**回合结束**才能算出，且只适用于回合制任务。
>
> *English: Monte Carlo prediction estimates v_π(s) by averaging the returns observed after visits to s. The update V ← V + α(G − V) uses the full sampled return as target, so it is unbiased but must wait until the episode ends.*

**白话版：「打完整局再复盘」。** 下完一盘棋，赢了，就把这一局里出现过的每个局面都「加一分」；输了就「减一分」。局面的价值就是它平均「带来多少分」。简单、直观，不需要任何环境知识。上一节的蒙特卡洛估计价值就是这个做法。问题是：必须等一整局结束才能学；一局里所有随机的事情（每一步的运气）都混进了这个分数，所以**方差大**。

### 第二种办法：TD(0)，每走一步就学一步

> **标准定义 · 时序差分预测 TD(0) (temporal-difference prediction)**
>
> 观察到一步转移 $(S_t,R_{t+1},S_{t+1})$ 之后立刻更新：
>
> $$V(S_t)\leftarrow V(S_t)+\alpha\big[R_{t+1}+\gamma V(S_{t+1})-V(S_t)\big]$$
>
> 方括号里的量叫 **TD 误差 (TD error)**：$\delta_t=R_{t+1}+\gamma V(S_{t+1})-V(S_t)$；$R_{t+1}+\gamma V(S_{t+1})$ 叫 **TD 目标**。它用「下一状态的当前估计」代替「真实的未来回报」，这种做法叫**自举 (bootstrapping)**。
>
> *English: TD(0) updates after every step using the target R + γV(S'), which bootstraps from the current estimate of the next state. The bracketed difference is the TD error.*

**白话版：「边走边校正：用下一步的猜测去修正这一步的猜测」。** 你从 A 走到 B，得到奖励 $r$。你本来认为 A 值 $V(A)$，现在发现「奖励 $r$ + B 的价值」是 $r+\gamma V(B)$，两者对不上，差多少就按比例 $\alpha$ 修正。**TD 误差为正，说明比预期更好；为负说明比预期更差**（后面你会在 actor-critic 和 Dreamer 里反复看到这个量）。

把三类方法并排看，就能看到它们和上一节的关系：

| 方法 | 需要模型 $P,R$ 吗 | 更新用「期望」还是「样本」 | 是否自举 |
|---|---|---|---|
| 动态规划 (DP) | 需要 | 对所有后继状态取期望 | 是 |
| 蒙特卡洛 (MC) | 不需要 | 用一整条轨迹的样本 | 否 |
| TD(0) | 不需要 | 用一步的样本 | 是 |

**TD(0) 就是把贝尔曼期望方程里的「对所有后继求期望」换成「用实际走到的那一个后继」**：保留了 DP 的自举（可以每步更新），又像 MC 一样不需要模型。

### 动手实验：MC 对 TD(0)

经典的测试环境是 5 状态随机游走（A B C D E，从中间的 C 出发，每步等概率向左右走，走出右端得 1、走出左端得 0，$\gamma=1$，Sutton & Barto 第 6 章的 Example 6.2）。真实价值是 $(1/6,2/6,3/6,4/6,5/6)$，我们把所有状态的初始估计设成 0.5，看两种方法的估计误差（RMS 误差，对 5 个状态取均方根）随回合数怎么下降。每个设置独立重复 200 次取平均。

""" + C_PRED + r"""

读输出：初始估计全是 0.5，起点的 RMS 误差约为 0.236。

- **TD(0)** 在 $\alpha=0.05$ 时，第 10 局 0.175、第 30 局 0.095、第 100 局 0.037，一路下降；$\alpha=0.15$ 前期更快（第 10 局 0.093），但第 30 局之后反而回升（0.062，再到 0.071）：**步长越大，学得越快，但最后稳定下来的噪声也越大**，这是步长的取舍。
- **蒙特卡洛**在 $\alpha=0.01$ 时，第 100 局还有 0.129；$\alpha=0.04$ 第 100 局 0.061。同样比较各自较好的步长，100 局时 TD 的最好成绩（0.037）比 MC 的（0.061）更低，前几十局差距更明显。
- 这是教材里的一个经验观察：在随机任务里，TD 通常比常数步长的 MC 学得快；教材也特别说明，目前还没有一般性的数学证明说谁一定更快。**读这一段不要得出「TD 永远更好」的结论。**

### 偏差与方差：为什么 TD 通常更快

两种目标的差别可以用统计语言精确说出来。

> **标准定义 · 偏差与方差 (bias and variance of the targets)**
>
> 估计 $v_\pi(s)$ 时，**蒙特卡洛目标** $G_t$ 满足 $\mathbb{E}[G_t\mid S_t=s]=v_\pi(s)$，是**无偏 (unbiased)** 的，但 $G_t$ 累积了此后所有步的随机性，**方差 (variance)** 大。**TD 目标** $R_{t+1}+\gamma V(S_{t+1})$ 只含**一步**的随机性，方差小；但它用到当前的估计 $V(S_{t+1})$，若 $V$ 不准则目标**有偏**，只有当 $V=v_\pi$ 时才无偏。
>
> *English: The MC target is an unbiased sample of v_π but has high variance because it sums many random steps. The TD target has lower variance since it contains one random step, but is biased whenever the current estimate V is inaccurate.*

**白话版：「老老实实的但嘈杂，对比省事的但可能带偏见」。** MC 像是等到全部结果出来才打分：公正，但一局之中的运气全混进来，打分忽高忽低；TD 像是只看一步，再请一位「顾问」（当前的 $V$）估计之后的结果：打分稳，但如果顾问本人不靠谱，打分就会被他带偏。随着学习进行，顾问越来越准，偏差会消失。

用同一个随机游走，对 B、C、D、E 每个状态各采样 5 万次，直接看两种目标的均值和方差。TD 目标分两种情形：$V$ 完全准确，和 $V$ 处处等于 0.5（一个不准的估计）。

""" + C_BIASVAR + r"""

读输出：

- **MC 目标**的均值等于真实价值（B 是 0.335 对 0.333，C 是 0.498 对 0.500，D 是 0.669 对 0.667，E 是 0.832 对 0.833），无偏；方差很大：目标只取 0 或 1，方差是 $v(1-v)$，C 是 0.250，B、D 约 0.22，E 是 0.139。
- **TD 目标（$V$ 准确）**均值同样等于真实价值，而方差只有 0.028（B、C、D、E 都一样）：只剩一步的随机性，比 MC 小近一个数量级。
- **TD 目标（$V$ 处处 0.5）**：B 的均值是 0.500，而真实价值是 0.333，偏差 $+0.167$；D 的均值 0.500 对真实 0.667，偏差 $-0.167$；E 是 0.748 对 0.833。方差几乎为 0（B、C、D 的两个后继状态的估计都是 0.5，目标几乎不随机），但**被不准的 $V$ 带偏了**。这就是自举的代价：快而稳，但学习初期会把估计的错误一层层传播。

**常见的折中**是 **$n$ 步 TD** 与 **TD($\lambda$)**：用 $n$ 步的真实奖励加上第 $n$ 步之后的估计做目标，$n=1$ 是 TD(0)，$n=\infty$ 是 MC。Dreamer 里用的 **$\lambda$-回报**就是这一类。

### 探索与利用：为什么需要 $\varepsilon$-贪心

从预测转到控制，要面对一个新的矛盾。你只能从自己尝试过的动作里学：如果总选当前估计最好的动作（**利用 exploitation**），一旦初始估计有偏，就永远不会发现更好的动作；如果总是乱试（**探索 exploration**），又浪费机会。

> **标准定义 · $\varepsilon$-贪心策略 ($\varepsilon$-greedy policy)**
>
> 给定动作价值估计 $Q(s,\cdot)$，以概率 $1-\varepsilon$ 选当前最好的动作 $\arg\max_aQ(s,a)$，以概率 $\varepsilon$ 在所有 $|A|$ 个动作里均匀随机选。所以最优动作被选中的概率是 $1-\varepsilon+\varepsilon/|A|$，其他动作各是 $\varepsilon/|A|$。
>
> *English: With probability 1 − ε pick the greedy action, with probability ε pick uniformly at random. It keeps every action's probability positive, so all actions continue to be tried.*

**白话版：「大多数时候去老馆子，偶尔试一家新店」。** 这里先用最简单的场景来感受：10 臂老虎机（每个臂的平均奖励不同，智能体不知道，每次拉一个臂拿一个有噪声的奖励；教材第 2 章的 10-armed testbed）。看不同 $\varepsilon$ 的表现，每个设置重复 500 次、每次 1000 步。

""" + C_EPS + r"""

读输出：前两行是概率：4 个动作、$\varepsilon=0.1$ 时，最优动作 0.925（$=0.9+0.1/4$），其余各 0.025；$\varepsilon=0.4$ 时 0.7 和 0.1。

老虎机的结果（每个 $\varepsilon$ 下最优臂均值约 1.5）：**$\varepsilon=0$（纯贪心）**最后 500 步平均奖励只有 1.024，离最优臂的 1.5 左右还差很远：它早早锁定了一个看上去还行的臂，再也不试别的；**$\varepsilon=0.1$** 最后 500 步达到 1.373，是四个里最高的；$\varepsilon=0.01$ 是 1.234，探索太少，发现好臂很慢；$\varepsilon=0.3$ 是 1.091，探索太多，一直在浪费。这次实验只有 1000 步，所以「最好的 $\varepsilon$」依赖于时间长度：时间越长，越应该减少探索。**$\varepsilon$ 没有放之四海的最优值，通常需要随训练衰减。**

### 无模型控制：SARSA 与 Q-learning

控制需要选动作，所以学的是**动作价值** $Q(s,a)$（有了 $Q$ 不需要模型就能选动作：直接取 $\arg\max_aQ(s,a)$）。TD 的思想原封不动搬过来，把 $V(s)$ 换成 $Q(s,a)$，就有两种经典写法，区别只在「下一状态的价值怎么取」。

> **标准定义 · SARSA 与 Q-learning (on-policy and off-policy TD control)**
>
> **SARSA**（同策略）：观察到五元组 $(S_t,A_t,R_{t+1},S_{t+1},A_{t+1})$ 后，
>
> $$Q(S_t,A_t)\leftarrow Q(S_t,A_t)+\alpha\big[R_{t+1}+\gamma Q(S_{t+1},A_{t+1})-Q(S_t,A_t)\big]$$
>
> 其中 $A_{t+1}$ 是智能体**实际要执行**的下一个动作（按 $\varepsilon$-贪心选出的）。**Q-learning**（异策略）：
>
> $$Q(S_t,A_t)\leftarrow Q(S_t,A_t)+\alpha\big[R_{t+1}+\gamma\max_{a'}Q(S_{t+1},a')-Q(S_t,A_t)\big]$$
>
> 下一状态里直接取**最好**的动作，不管实际会不会执行。
>
> *English: SARSA bootstraps from the action actually taken next, so it evaluates the behavior (ε-greedy) policy itself. Q-learning bootstraps from the maximum over next actions, so it learns the greedy policy's values regardless of what the behavior policy does.*

**白话版：「SARSA 是『我会怎么走』的评估，Q-learning 是『如果我走到最好』的评估」。** SARSA 估计的是「**包括我探索时会犯的随机错误**，从这里出发能拿多少分」；Q-learning 估计的是「假设我之后每一步都选最好的，从这里出发能拿多少分」。教材里它们的名字：SARSA 来自五元组 $(S,A,R,S',A')$，由 Rummery 与 Niranjan 在 1994 年提出；Q-learning 由 Watkins 在 1989 年提出。

> **标准定义 · 同策略与异策略 (on-policy vs off-policy)**
>
> 产生数据的策略叫**行为策略 (behavior policy)** $b$，正在学习价值的策略叫**目标策略 (target policy)** $\pi$。**同策略**：$b=\pi$，评估和改进的是自己正在用的策略（SARSA）。**异策略**：$b\ne\pi$，可以用别人（或以前）的数据学习另一个策略（Q-learning：$b$ 是 $\varepsilon$-贪心，$\pi$ 是贪心）。
>
> *English: The behavior policy generates the data; the target policy is the one being evaluated or improved. On-policy methods have them equal; off-policy methods learn about one policy from data generated by another.*

**白话版：「边做边学」对「看别人做也能学」。** 异策略的好处很大：可以用旧数据（经验回放）、人类示范、别的智能体的经验来学习；代价是估计的稳定性更差（用函数近似时「异策略 + 自举 + 函数近似」被称为「致命三元组 (deadly triad)」，第 4 节再讲）。

**和上一节的关系**：Q-learning 就是用一个**样本**去逼近**贝尔曼最优备份**，是价值迭代的无模型版本；SARSA 则是在评估自己的 $\varepsilon$-贪心策略的同时让它逐步变好，是策略迭代（广义策略迭代）的样本版。两者在所有状态-动作对都被反复访问、步长按常见条件衰减的前提下，在表格情形下都有收敛保证（Q-learning 收敛到 $q_*$，SARSA 在探索逐渐减少的条件下收敛到最优策略）。
"""),
  V("AJiG3ykOxmY", "视频：Temporal Difference Learning (including Q-Learning) — Reinforcement Learning Part 4（Mutual Information）", 29),
  T(r"""
### 动手实验：悬崖行走，SARSA 与 Q-learning 的对比

这是教材里（Example 6.6）专门用来展示同策略与异策略差别的例子。一个 4 行 12 列的网格：起点 S 在左下角，终点 G 在右下角，**最下面一行中间的 10 格是悬崖**。每走一步奖励 $-1$；踩进悬崖奖励 $-100$，并被送回起点（回合不结束）；不打折（$\gamma=1$）。**最短路径是沿着悬崖边缘走，共 13 步，回报 $-13$**；但只要探索时一个随机动作选了「向下」，就会掉下去。

两种算法用完全相同的设置（$\alpha=0.5$，$\varepsilon=0.1$，500 局），各重复 30 次。除了在线回报（带 $\varepsilon$ 探索），也看「去掉探索」之后的贪心路径：把 30 次运行学到的 $Q$ 取平均再看路径，以及每次运行的贪心策略各自能不能走到终点。

""" + C_CLIFF + r"""

读输出：

- **前 50 局**两者都很差（$-110.48$ 对 $-112.80$）：刚开始都在乱撞，掉崖很多次。
- **最后 100 局的在线回报**：SARSA 是 $-27.23$，Q-learning 只有 $-51.15$；平均每局掉崖次数 0.051 对 0.344。**Q-learning 的在线表现反而更差。**
- 贪心路径（把 30 次的 $Q$ 取平均）：**SARSA 走的是 17 步的远路**：先一路向上到最上面一行，横着走过去，再向下到终点，**离悬崖最远**；**Q-learning 走的是 13 步的最短路径**：紧贴悬崖边。
- 单次运行里，Q-learning 的贪心策略 30 次全部走到了终点，每次回报都是 $-13$；SARSA 的贪心策略 30 次里有 24 次走到终点（回报 $-17$ 共 22 次、$-15$ 和 $-19$ 各 1 次），另外 6 次在 100 步内没走到终点（多半是一些很少被访问的格子上 $Q$ 值还没学好，贪心路径在里面转圈）。

**这就是同策略与异策略的区别在行为上的体现**：Q-learning 学到了「完全贪心时」的最优路径，于是**价值本身是对的**，可是训练时还在以 $\varepsilon=0.1$ 探索，贴着悬崖边每一步都有概率失足，在线回报很差；SARSA 学的是「带着探索去走」的价值，它「知道」自己会偶尔走错，所以绕远路，在线回报更好，但**没有学到真正的最优路径**。哪个更好取决于你想要什么：训练过程中的表现，还是训练完成后「部署」的表现。

最后一个问题：如果让探索逐渐消失呢？两个算法的在线回报差距会缩小吗？

""" + C_DECAY + r"""

读输出：$\varepsilon$ 从第 0 局的 0.5 衰减到第 100 局的 0.083，再降到 0.01。训练 2000 局，固定 $\varepsilon=0.1$ 时最后 100 局的在线回报：SARSA $-28.80$，Q-learning $-49.07$，和 500 局的结果相近；**探索衰减之后，两者的在线回报几乎一样好**（SARSA $-17.81$，Q-learning $-16.53$）：在线回报的差距，几乎全来自探索。Q-learning 的 $-16.53$ 仍比 $-13$ 差：贴悬崖边的约 10 步里，每步有 $\varepsilon/4=0.25\%$ 的概率恰好选到「向下」，掉崖概率约 2.5%，每次损失约 100 多分，算下来多损失约 3，量级吻合。

最后一列是衰减训练后的**贪心路径**回报：Q-learning 20 次全是 $-13$（均值 $-13.00$）；SARSA 的均值是 $-21.35$，这是因为 20 次里有 17 次回报 $-17$、2 次 $-19$、1 次是没走到终点（按 100 步封顶算 $-100$）。注意，即使 $\varepsilon$ 衰减到 0.01，SARSA 的贪心路径依然是 17 步的远路，不是 13 步：它的 $Q$ 值是在早期高探索率时学的，贴悬崖边的格子很少再被访问，所以旧的悲观估计没有机会被修正。理论上，探索逐渐消失并且每个状态-动作对被无限访问时，SARSA 也收敛到最优策略，但**有限的训练里它不一定走到那一步**。

### 这一节你要带走的三句话

1. **无模型 = 只用样本**：蒙特卡洛用整局回报（无偏、方差大、要等回合结束），TD(0) 用 $r+\gamma V(s')$（方差小、有偏、每步更新）；TD 误差 $\delta=r+\gamma V(s')-V(s)$ 是后面所有算法的学习信号。
2. **SARSA 与 Q-learning 只差一个下一状态的取法**：实际要走的动作 vs 取最大；前者同策略，评估带探索的自己，后者异策略，直接学贪心策略的最优价值。
3. **探索不可省**：$\varepsilon$-贪心保证每个动作继续被试；探索会影响在线表现（悬崖行走里 Q-learning 的在线回报更差），所以通常让 $\varepsilon$ 衰减。无模型方法样本效率低，这是引入世界模型的动机之一。
"""),
  THINK("**计算**：某个状态-动作对当前 $Q(s,a)=1$。执行后得到奖励 $r=2$，下一状态 $s'$ 的三个动作价值是 $Q(s',\\cdot)=(0,4,1)$，智能体实际要执行的下一个动作是第三个（价值 1）。$\\gamma=0.9$，$\\alpha=0.5$。分别算 SARSA 和 Q-learning 更新后的 $Q(s,a)$。", r"""
**SARSA**：目标 $=2+0.9\times1=2.9$，TD 误差 $=2.9-1=1.9$，新值 $=1+0.5\times1.9=1.95$。

**Q-learning**：目标 $=2+0.9\times\max(0,4,1)=2+3.6=5.6$，TD 误差 $=4.6$，新值 $=1+0.5\times4.6=3.3$。

差别正好在「下一状态的价值怎么取」：SARSA 用实际执行的那个动作（价值 1），Q-learning 用最好的动作（价值 4）。所以只要探索让智能体偶尔选了较差的动作，SARSA 的估计就会比 Q-learning 保守。
"""),
  THINK("**概念辨析**：蒙特卡洛目标和 TD 目标，哪个方差大、哪个有偏？为什么 TD 能「在线」更新而 MC 不能？一个会无限持续、没有回合的任务，哪一种能用？", r"""
MC 目标 $G_t$ 是真实回报的无偏样本，但累积了此后所有步的随机性，**方差大**；TD 目标只含一步随机，**方差小**，但因为用了估计 $V(S_{t+1})$ 而**有偏**（估计越不准偏差越大，随学习而消失）。

TD 只需要 $(S_t,R_{t+1},S_{t+1})$ 这一步就能构造目标，所以每走一步就能更新；MC 的目标是整局回报，必须等回合结束才知道，无法「在线」更新。

持续任务没有终点，MC 永远等不到回合结束，无法使用（除非人为截断）；**TD 可以使用**，这是它的重要优势。
"""),
  THINK("**联系世界模型**：无模型方法要用大量真实交互：DQN 论文（Mnih 等，2015，*Nature*）的 Atari 实验训练了 5000 万帧画面，约相当于 38 天的游戏时间。如果有一个学得不错的环境模型，能怎样用「想象的经验」去减少真实交互？这样做的主要风险是什么？", r"""
有了模型就可以**让智能体在模型里自己玩**：从真实经验里出发，用模型生成「想象的」$(s,a,r,s')$，再喂给同一个 Q-learning 更新（Sutton 的 Dyna 架构就是这样做的，第 7 节会实现）。真实交互只用来更新模型，大量的价值更新在想象中完成，样本效率可以提升很多。

风险是**模型误差**：模型不完美，想象的经验里的错误会被价值更新当成真的学进去，而且滚动预测的步数越多，误差累积得越多。所以基于模型的方法要么只做短期的想象，要么显式考虑模型的不确定性。这是第 7、8 节的主题。
"""),
  KW(("预测 / 控制","prediction / control","估计给定策略的价值 / 找最优策略"),
     ("无模型","model-free","不使用 $P,R$，只用交互样本学习"),
     ("蒙特卡洛","Monte Carlo (MC)","用整局回报的平均估计价值，无偏、方差大"),
     ("首次访问 / 每次访问","first-visit / every-visit","每个回合只取第一次 / 每次访问某状态后的回报"),
     ("时序差分","temporal difference (TD)","每步用 $r+\\gamma V(s')$ 更新，方差小、有偏"),
     ("TD 误差","TD error $\\delta_t$","$R_{t+1}+\\gamma V(S_{t+1})-V(S_t)$，比预期好或坏的程度"),
     ("自举","bootstrapping","用自己的估计更新自己"),
     ("步长","step size $\\alpha$","每次更新朝目标走多远"),
     ("偏差-方差权衡","bias–variance trade-off","MC 无偏高方差，TD 有偏低方差"),
     ("探索 / 利用","exploration / exploitation","尝试新动作 / 选已知最好的动作"),
     ("$\\varepsilon$-贪心","$\\varepsilon$-greedy","以概率 $\\varepsilon$ 随机选动作，其余选最好的"),
     ("SARSA","SARSA","同策略 TD 控制，目标用实际选的下一个动作"),
     ("Q-learning","Q-learning","异策略 TD 控制，目标用下一状态的最大 $Q$"),
     ("同策略 / 异策略","on-policy / off-policy","学习的策略与产生数据的策略相同 / 不同"),
     ("行为策略 / 目标策略","behavior / target policy","产生数据的策略 / 正在学习的策略"),
  ),
 ],
 "references": [
  {"title": "Sutton & Barto《Reinforcement Learning: An Introduction》第二版（2018），第 5 章 Monte Carlo Methods（5.1）与第 6 章 Temporal-Difference Learning（6.1–6.5，Example 6.2 随机游走、Example 6.6 悬崖行走）；第 2 章 2.3 10-armed Testbed", "url": "http://incompleteideas.net/book/RLbook2020.pdf", "note": "本节内容依据的开放教材（作者免费公开）；讲解和实验代码为自写，未转载原文"},
  {"title": "David Silver：RL Course, Lecture 4: Model-Free Prediction 与 Lecture 5: Model-Free Control（DeepMind / UCL，各约 97 分钟）", "url": "https://www.youtube.com/watch?v=PnHCvfgC_ZA", "note": "选看：同一主题的大学课堂版本；Lecture 5 的链接为 youtube.com/watch?v=0g4j2k_Ggc4"},
  {"title": "Mutual Information：Monte Carlo And Off-Policy Methods — Reinforcement Learning Part 3（约 27 分钟）", "url": "https://www.youtube.com/watch?v=bpUszPiWM7o", "note": "选看：本节视频的前一集，按标题讲蒙特卡洛与异策略方法（没有逐个看过）"},
  {"title": "Hugging Face Deep RL Course, Unit 2: Introduction to Q-Learning", "url": "https://huggingface.co/learn/deep-rl-course/unit2/introduction", "note": "免费课程，带动手练习"},
 ],
 "quiz": {"questions": QUIZ},
}

if __name__ == '__main__':
    dump(unit, "wm-0", "u03-model-free.json")
