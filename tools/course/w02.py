"""wm-0 第 2 节：贝尔曼方程与动态规划求解（v3 格式，2026-10-04）"""
from unitlib import *
from w02c import C_EVAL, C_CONTRACT, C_VI, C_PI, C_HORIZON
from w02_quiz import QUIZ

unit = {
 "id": "u02",
 "title": "贝尔曼方程与动态规划求解",
 "en": "Bellman Equations & Dynamic Programming",
 "minutes": 100,
 "objectives": [
  "写出并推导 **贝尔曼期望方程 (Bellman expectation equation)**，理解它既是一个递推关系，也是一个线性方程组 $v_\\pi=r_\\pi+\\gamma P_\\pi v_\\pi$，会用 **策略评估 (policy evaluation)** 迭代求解",
  "理解 **收缩映射 (contraction mapping)**：为什么贝尔曼备份会收敛到唯一的 **不动点 (fixed point)**，误差如何按 $\\gamma^k$ 衰减，并能用数值验证",
  "写出 **贝尔曼最优方程 (Bellman optimality equation)** 和 **最优价值函数 (optimal value function)**，会用 **价值迭代 (value iteration)** 求 $v_*$ 并读出最优策略",
  "掌握 **策略改进定理 (policy improvement theorem)** 和 **策略迭代 (policy iteration)**，理解它与价值迭代的关系（**广义策略迭代**）",
  "说清 MDP 的动态规划与 dsa-0 第 11 节「动态规划」的联系和区别：最优子结构、状态转移方程、为什么 MDP 要迭代到不动点",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

上一节我们用蒙特卡洛「玩上万局再取平均」估计价值：慢，有噪声，而且每个状态都要单独估。这一节换一个思路：**如果环境的模型 $P,R$ 是已知的，价值可以不玩一局，直接算出来**。关键是一个等式：**贝尔曼方程 (Bellman equation)**，它把「一个状态的价值」和「后继状态的价值」联系起来，价值就变成一个方程组的解。再往前一步，把「取平均」换成「取最大」，就能求出**最优**价值，进而得到最优策略。这套办法叫**动态规划 (dynamic programming, DP)**，是强化学习里所有价值类算法的理论根基，Q-learning、DQN 都是在**模型未知**时对它的逼近。

**这一节和世界模型的关系。** 动态规划是「**已知世界模型时怎么规划**」的标准答案：给你 $P$ 和 $R$，就能在脑子里一层层推演出最优行动。而世界模型研究的是反面的问题：$P$ 和 $R$ 不知道，就从数据里学一个近似，然后把学到的模型当作 $P,R$ 拿来规划（第 7、8 节）。贝尔曼备份也是 Dreamer 里「想象中的回报怎么算」的数学基础（$\lambda$-回报就是多步贝尔曼备份的混合）。

**学完它你就能看懂这几件事：**

- 强化学习论文和代码里反复出现的 $r+\gamma\max_{a'}Q(s',a')$（DQN 的目标值）是怎么来的，为什么叫「自举 (bootstrapping)」；
- 为什么折扣因子 $\gamma$ 取 0.99 比 0.9 训练慢得多（收缩得更慢）；
- 「$Q$ 值迭代」「策略迭代」「actor-critic」都是同一张图（广义策略迭代）的不同画法；
- 为什么实际问题里不能直接用 DP（状态太多、模型未知），以及下一节、第 7 节分别怎么绕开。

**本节安排（约 100 分钟）**：贝尔曼期望方程（12 分钟）→ 视频一（9 分钟）→ 策略评估与实验（15 分钟）→ 收缩映射（12 分钟）→ 最优方程与价值迭代（12 分钟）→ 策略改进与策略迭代（10 分钟）→ 视频二（22 分钟）→ 和动态规划的联系（8 分钟）→「想一想」。视频是英文的，可以打开 YouTube 的中文字幕。

### 贝尔曼期望方程：价值的递推

> **标准定义 · 贝尔曼期望方程 (Bellman expectation equation)**
>
> 给定策略 $\pi$，它的价值函数满足
>
> $$v_\pi(s)=\sum_a\pi(a\mid s)\Big[R(s,a)+\gamma\sum_{s'}P(s'\mid s,a)\,v_\pi(s')\Big]$$
>
> $$q_\pi(s,a)=R(s,a)+\gamma\sum_{s'}P(s'\mid s,a)\sum_{a'}\pi(a'\mid s')\,q_\pi(s',a')$$
>
> 推导：由 $G_t=R_{t+1}+\gamma G_{t+1}$，取条件期望 $v_\pi(s)=\mathbb{E}_\pi[R_{t+1}+\gamma v_\pi(S_{t+1})\mid S_t=s]$，再把期望按「先选动作、再转移」展开。
>
> 矩阵形式：记 $P_\pi(s'\mid s)=\sum_a\pi(a\mid s)P(s'\mid s,a)$，$r_\pi(s)=\sum_a\pi(a\mid s)R(s,a)$，则 $v_\pi=r_\pi+\gamma P_\pi v_\pi$，即 $v_\pi=(I-\gamma P_\pi)^{-1}r_\pi$。
>
> *English: The value of a state equals the expected immediate reward plus the discounted value of the successor state, averaged over the policy and the dynamics. In matrix form it is the linear system v = r_π + γ P_π v.*

**白话版：「一步看远：我的价值 = 眼前一步 + 打折后的『下一步的价值』」。** 价值是回报的期望，回报 = 眼前奖励 + 折扣后的未来回报，所以价值 = 眼前奖励的期望 + 折扣后的下一状态价值的期望。**这个等式不需要看到整条轨迹**，只需要往前看一步，剩下的交给后继状态的价值去代表，这叫**自举 (bootstrapping)**：用估计值去更新估计值。每个状态写一个这样的方程，$|S|$ 个未知数、$|S|$ 个线性方程，就是上一节最后提到的「MDP + 策略 = 马尔可夫链」的矩阵写法。$(I-\gamma P_\pi)$ 总是可逆的，因为 $P_\pi$ 的每一行和为 1，$\gamma P_\pi$ 的所有特征值绝对值都不超过 $\gamma<1$。
"""),
  V("9JZID-h6ZJ0", "视频一：Bellman Equation - Explained!（CodeEmporium）", 9),
  T(r"""
### 策略评估：把方程当作更新规则

> **标准定义 · 策略评估 (iterative policy evaluation)**
>
> 要从方程 $v_\pi=r_\pi+\gamma P_\pi v_\pi$ 求 $v_\pi$，除了解线性方程组（代价约 $O(|S|^3)$），还可以把它当作**更新规则**反复套用：从任意 $v_0$ 出发，
>
> $$v_{k+1}(s)=\sum_a\pi(a\mid s)\Big[R(s,a)+\gamma\sum_{s'}P(s'\mid s,a)\,v_k(s')\Big]$$
>
> 每次**扫描 (sweep)** 更新所有状态；当 $\max_s|v_{k+1}(s)-v_k(s)|$ 足够小时停止。每次扫描代价约 $O(|S|^2|A|)$。
>
> *English: Iterative policy evaluation repeatedly applies the Bellman expectation equation as an update rule, starting from an arbitrary v_0, until the values stop changing.*

**白话版：「消息一层层往回传」。** 一开始所有状态价值都当作 0；第一次扫描，只有紧挨着终点和陷阱的格子「知道」有奖励；第二次扫描，再外面一圈的格子通过邻居得到消息……每扫描一次，信息向外传一步，最后传遍全图，数字不再变化。

下面把网格世界的 $P$ 和 $R$ 完整写成数组（和上一节同一个环境，$\gamma=0.9$），对**随机策略**做策略评估，再和直接解线性方程组对比，最后用 $v_\pi$ 算 $q_\pi$。

""" + C_EVAL + r"""

读输出：

- 第 1 次扫描最大变化 2.5：只有紧挨终点的格子拿到了 $0.25\times10=2.5$（四个动作里只有一个走进终点）；之后每次扫描变化越来越小：第 10 次 0.097463，第 50 次 0.000270，共 159 次扫描后变化小于 $10^{-10}$。
- 精确值 $v_\pi(\text{起点})=-0.8293$，第 50 次扫描时已经是 $-0.8275$。上一节蒙特卡洛玩 2 万局得到的是 $-0.822\pm0.012$，**吻合**，但这里一局都没有玩。
- 价值表：靠近陷阱的格子被拉低（陷阱正上方是 $-4.241$，左边是 $-3.704$，右边是 $-3.584$），靠近终点的格子为正（终点上方 1.664，左边 2.808）；两个终止状态本身价值为 0。
- 迭代结果与 `np.linalg.solve` 解线性方程组的结果一致（`True`）。小问题两种做法都行；状态数很大时，$O(|S|^3)$ 不可行，才必须用迭代。
- 起点的 $q_\pi$：上 $-0.746$、下 $-0.799$、左 $-0.746$、右 $-1.025$。「上」和「左」完全相等，因为两个动作都撞墙、留在起点，下一状态一样。这也解释了上一节蒙特卡洛估计里上和左的差别只是采样噪声。最后一行验证了 $v_\pi=\sum_a\pi(a\mid s)q_\pi(s,a)$ 对所有状态成立。

### 为什么会收敛：收缩映射

策略评估的更新一直做下去，真的会收敛吗？会收敛到哪里？这个问题的答案很干净，用到数学里的**收缩映射**。

> **标准定义 · 收缩映射与不动点 (contraction mapping & fixed point)**
>
> 记 $\|x\|_\infty=\max_s|x(s)|$（最大范数）。映射 $T$ 称为**$\gamma$-收缩映射**，若对任意 $v,w$ 有 $\|Tv-Tw\|_\infty\le\gamma\|v-w\|_\infty$，其中 $0\le\gamma<1$。**巴拿赫不动点定理 (Banach fixed-point theorem)**：这样的 $T$ 有**唯一**不动点 $v^\star=Tv^\star$，且从任意 $v_0$ 出发，$\|T^kv_0-v^\star\|_\infty\le\gamma^k\|v_0-v^\star\|_\infty$。
>
> 贝尔曼备份 $(T^\pi v)(s)=r_\pi(s)+\gamma\sum_{s'}P_\pi(s'\mid s)v(s')$ 就是 $\gamma$-收缩：$|(T^\pi v-T^\pi w)(s)|=\gamma\big|\sum_{s'}P_\pi(s'\mid s)(v-w)(s')\big|\le\gamma\|v-w\|_\infty$，因为 $P_\pi(\cdot\mid s)$ 是一组和为 1 的权重，加权平均不会超过最大值。
>
> *English: A γ-contraction shrinks the max-norm distance between any two points by a factor γ < 1. By Banach's theorem it has a unique fixed point and repeated application converges to it geometrically from any start. The Bellman backup is a γ-contraction in the max norm.*

**白话版：「两个人同时往中间靠拢」。** 想象两个人各自站在价值空间里的一个点上（两个不同的「价值向量」），每做一次贝尔曼备份，两人的距离至少缩到原来的 $\gamma$ 倍。距离每次缩小一截，最后只能重合：不动点只能有一个，而且不管从哪出发都会走到它。**$\gamma$ 就是收缩的速度**：$\gamma=0.9$ 每次缩小 10%，$\gamma=0.99$ 每次只缩小 1%，所以后者需要多得多的扫描。

一个实用的推论是**停止准则**：若 $\|v_{k+1}-v_k\|_\infty<\varepsilon$，则 $\|v_{k+1}-v^\star\|_\infty\le\frac{\gamma}{1-\gamma}\varepsilon$。（推导：$\|v_{k+1}-v^\star\|\le\gamma\|v_k-v^\star\|\le\gamma(\|v_k-v_{k+1}\|+\|v_{k+1}-v^\star\|)$，移项即得。）

下面用数字验证收缩性：随机取一万对价值向量，看备份一次后距离缩小的比例；再看误差是否真的低于 $\gamma^k\|v_0-v_\pi\|$。

""" + C_CONTRACT + r"""

读输出：

- 1 万对随机向量里，$\|Tv-Tw\|/\|v-w\|$ 的最大值是 0.9000，**没有超过 $\gamma=0.9$**。它恰好等于 $\gamma$，是因为终止状态有 $P_\pi(s\mid s)=1$（原地不动）：当两个向量差得最大的地方恰好在终止状态时，这一格的差距正好乘以 $\gamma$。下一行把 $w$ 取成 $v+5$（每格都多 5），比值就**精确**是 0.9，说明 $\gamma$ 这个界不能再改小了。
- 最优备份（带 $\max$）同样是收缩（最大比值 0.9000）。证明用到 $|\max_ax_a-\max_ay_a|\le\max_a|x_a-y_a|$。
- 从一个很差的初始值出发（初始误差 98.78），误差表：第 1 步 55.9106（上界 88.9027），第 10 步 21.4006（上界 34.4427），第 50 步 0.31632，第 100 步 0.00163024（上界 0.00262376）。**每一步都低于上界**（程序里的 `assert` 通过）。100 次扫描把误差压低了约 6 万倍。
"""),
  T(r"""
### 最优方程与价值迭代

> **标准定义 · 最优价值函数与贝尔曼最优方程 (optimal value function & Bellman optimality equation)**
>
> **最优状态价值** $v_*(s)=\max_\pi v_\pi(s)$，**最优动作价值** $q_*(s,a)=\max_\pi q_\pi(s,a)$。对有限 MDP（$\gamma<1$），存在一个对所有状态同时最优的**确定性**策略 $\pi_*$，并且 $v_*$ 满足
>
> $$v_*(s)=\max_a\Big[R(s,a)+\gamma\sum_{s'}P(s'\mid s,a)\,v_*(s')\Big]$$
>
> $$q_*(s,a)=R(s,a)+\gamma\sum_{s'}P(s'\mid s,a)\max_{a'}q_*(s',a')$$
>
> 最优策略由 $q_*$ 直接读出：$\pi_*(s)=\arg\max_aq_*(s,a)$。
>
> *English: The optimal value function satisfies the Bellman optimality equation, which replaces the policy-weighted average over actions by a max. An optimal deterministic policy is greedy with respect to q_*.*

**白话版：「每个岔路口都选最好的那条，并且相信后面也会选最好的」。** 这是**最优子结构**：一条最优路线，它的后半段也一定是（从那个点出发的）最优路线。所以最优价值 = 选最好的动作，之后继续最优。和期望方程相比，唯一的差别是「按策略取平均」变成了「取最大」。**这个 $\max$ 让方程变成非线性**，没法再用矩阵求逆，只能迭代。

> **标准定义 · 价值迭代 (value iteration)**
>
> 把最优方程当作更新规则：从任意 $v_0$（例如全 0）出发，
>
> $$v_{k+1}(s)=\max_a\Big[R(s,a)+\gamma\sum_{s'}P(s'\mid s,a)\,v_k(s')\Big]$$
>
> 最优备份 $T^*$ 同样是 $\gamma$-收缩，所以 $v_k\to v_*$，误差按 $\gamma^k$ 衰减。收敛后读出贪心策略 $\pi(s)=\arg\max_a\big[R(s,a)+\gamma\sum_{s'}P(s'\mid s,a)v_*(s')\big]$。
>
> *English: Value iteration repeatedly applies the Bellman optimality backup until the values converge to v_*, then extracts the greedy policy.*

**白话版：「每一轮都假设自己之后会走得最好」。** 它和策略评估的代码几乎一模一样，只把「对动作按策略加权」换成 `max`。

""" + C_VI + r"""

读输出：

- 只用 9 次扫描就收敛（变化小于 $10^{-10}$）。这是因为这个网格世界是**确定性**的：起点离终点 8 步，好消息每次扫描往回传一格，8 次扫描后起点就知道了，第 9 次确认没有变化。随机的环境里则是逐渐逼近，不会这么整齐。
- 最优价值 $v_*(s)=10\,\gamma^{d-1}$，其中 $d$ 是到终点的最少步数。起点 $d=8$，所以 $v_*(\text{起点})=10\times0.9^7=4.783$，输出中两个数一致。对比随机策略的 $-0.829$，最优策略让起点价值从负变成了正。
- 最优策略（并列的动作都列出）：大部分格子「向下」和「向右」都是最优（任何曼哈顿最短路径都行）；**陷阱周围的格子只剩一个选项**：陷阱上方那格只能向右（向下是陷阱），陷阱左边那格只能向下，右边那格也只能向下；终点正左、正上的两格直接走进终点；最后一行都是向右。策略自己学会了「绕开陷阱」。
- 贝尔曼最优方程残差是 0.0：把 $v_*$ 再备份一次，一点都不变，说明它确实是不动点。

### 策略改进与策略迭代

价值迭代每一步都在「评估 + 取最大」。另一种思路是把两件事分开做：先把某个策略**完整评估**，再用评估结果**改进**策略，反复交替。它的依据是一个定理。

> **标准定义 · 策略改进定理与策略迭代 (policy improvement theorem & policy iteration)**
>
> **策略改进定理**：设 $\pi,\pi'$ 是两个确定性策略。若对所有状态 $s$ 有 $q_\pi\big(s,\pi'(s)\big)\ge v_\pi(s)$，则对所有状态 $v_{\pi'}(s)\ge v_\pi(s)$。特别地，**贪心策略** $\pi'(s)=\arg\max_aq_\pi(s,a)$ 总是满足条件，因此不比 $\pi$ 差。
>
> **策略迭代**：交替做 (1) 策略评估：求 $v_\pi$；(2) 策略改进：$\pi\leftarrow\text{greedy}(q_\pi)$。若改进后策略不变，则 $v_\pi(s)=\max_aq_\pi(s,a)$，满足最优方程，$\pi$ 已是最优。确定性策略只有有限个（$|A|^{|S|}$）且每轮不变差，所以有限轮内必然停止。
>
> *English: If acting greedily with respect to q_π for one step is no worse than π everywhere, the greedy policy is at least as good as π. Policy iteration alternates full policy evaluation with greedy improvement and stops after finitely many rounds at an optimal policy.*

**白话版：「评估，再挑刺」。** 先把现在这套打法打分（评估），再在每个路口问「如果这一步换个走法，之后照旧，会不会更好」（改进）。有更好就换，直到挑不出毛病。价值迭代是这套做法的「懒人版」：评估只做一次扫描就立即改进。**两者合起来的统一视角叫广义策略迭代 (generalized policy iteration, GPI)**：评估让价值追上策略，改进让策略追着价值走，二者互相追赶，最终在最优处同时稳定。后面的 Q-learning、actor-critic 都是 GPI 的特例。

下面从一个很差的策略（处处向上，永远撞墙）出发做策略迭代，评估这一步用解线性方程组。并且用 20 个随机生成的 MDP 对拍：策略迭代和价值迭代必须得到相同的最优价值。

""" + C_PI + r"""

读输出：初始策略处处向上，谁也走不到终点，所以所有状态价值都是 0。第 1 轮的改进里只有几个格子能发现「直接走进终点有 10」或「向上会掉进陷阱」，改了 3 个；之后每一轮好消息往回传一层，改动的格子数是 3、3、5、4、3、2、1；起点的价值在前 8 轮都是 0（策略还没有一条从起点通往终点的路），到第 9 轮变成 4.7830，同时「本轮改变 0 个」，算法停止。这个 4.7830 与价值迭代的 $v_*(\text{起点})$ 完全一致，整张价值表也一致（`True`），20 个随机 MDP 上也全部一致（`True`）。

策略迭代轮数很少（9 轮），但每轮要做完整评估；价值迭代轮数多，但每轮便宜。哪个更快取决于问题，实践里两者都用，也常常折中成「评估只做几次扫描」。
"""),
  V("_j6pvGEchWU", "视频二：Bellman Equations, Dynamic Programming, Generalized Policy Iteration — Reinforcement Learning Part 2（Mutual Information）", 22),
  T(r"""
### 和 dsa-0 第 11 节「动态规划」的联系

dsa-0 第 11 节讲过动态规划的三件事：**最优子结构**（大问题的最优解包含子问题的最优解）、**重叠子问题**（同一个子问题被反复用到）、**状态与转移方程**（用子问题的值写出大问题的值）。贝尔曼方程正是它们在 MDP 上的体现：

- 状态 = MDP 的状态；**转移方程 = 贝尔曼最优方程**，$v_*(s)$ 由后继状态的 $v_*(s')$ 算出；
- **最优子结构**：最优策略从任何一个中间状态之后的部分，仍然是那个状态出发的最优策略（Bellman 称之为「最优性原理」）；
- **重叠子问题**：从不同的路径走到同一个状态，后面的价值是同一个数，算一次存起来，这就是用 $v$ 表而不是枚举轨迹的意义。轨迹的条数随步数指数增长，价值表只有 $|S|$ 个数。

**一个关键的区别**：dsa-0 里的动态规划（最长公共子序列、背包、编辑距离）的子问题依赖关系是**有向无环图**，按拓扑顺序一遍就能填完表。MDP 的状态图是**有环的**：撞墙留在原地、可以来回走，$v(s)$ 依赖 $v(s')$，$v(s')$ 又可能依赖 $v(s)$，没有「先算谁」。所以要**迭代**，靠收缩映射保证收敛到不动点，而不是一遍制表。

但只要把时间展开，环就消失了：定义 $V_k(s)$ 为「最多再走 $k$ 步」的最优折扣回报，则 $V_k$ 只依赖 $V_{k-1}$，依赖关系是无环的，可以自底向上制表，也可以自顶向下写带记忆化的递归。**价值迭代的第 $k$ 次扫描，恰好就是这张表的第 $k$ 行**。

""" + C_HORIZON + r"""

读输出：两种写法（制表 / 记忆化递归）在 $k=30$ 时逐状态一致。$V_k(\text{起点})$ 在 $k\le7$ 时是 0：「最多走 7 步」到不了终点，拿不到任何奖励；$k=8$ 时变成 4.7830，之后不再变化，并且 $k=100$ 时和 $v_*$ 的最大差距是 0.0。这就是「有限视野 DP 随视野增大逼近无限视野的最优价值」，也是价值迭代的另一种读法。

**动态规划的局限，正是这门课后面要解决的问题**：(1) 它需要**完整的模型** $P$ 和 $R$；(2) 每次扫描要遍历**全部**状态，状态数一大（比如像素图像）就不可能。下一节讲没有模型时怎么从交互样本学习价值（蒙特卡洛、TD、Q-learning）；第 7 节讲先学一个模型、再用模型规划。

### 这一节你要带走的三句话

1. **贝尔曼期望方程**：$v_\pi=r_\pi+\gamma P_\pi v_\pi$，价值 = 眼前奖励 + 折扣后的后继价值；可以解线性方程组，也可以当更新规则迭代（策略评估）。
2. **收缩映射保证收敛**：备份算子每次把任意两个价值向量的最大距离缩小到 $\gamma$ 倍，所以迭代收敛到唯一不动点，误差按 $\gamma^k$ 衰减，$\gamma$ 越接近 1 越慢。
3. **最优方程把「平均」换成「最大」**：价值迭代求 $v_*$，策略迭代交替「评估 + 贪心改进」，二者是广义策略迭代的两个极端；DP 需要已知模型，这也是世界模型要提供的东西。
"""),
  THINK("某个状态 A 有两个动作：「留下」奖励 1、仍留在 A；「离开」奖励 5、进入终止状态。$\\gamma=0.9$。(a) 求 $v_*(A)$；(b) 从 $v_0=0$ 做价值迭代，前四次扫描的值是多少？每一步贪心策略是什么？", r"""
(a) 最优方程：$v_*(A)=\max\{1+0.9\,v_*(A),\ 5\}$。若永远「留下」，$v=1/(1-0.9)=10$，满足 $10=1+0.9\times10$，且大于「离开」的 5，所以 $v_*(A)=10$，最优策略是**一直留下**。短视地一次拿 5 分是错的。

(b) $v_1=\max\{1+0,5\}=5$（此时贪心选「离开」）；$v_2=\max\{1+0.9\times5,5\}=5.5$（贪心已变成「留下」）；$v_3=\max\{1+0.9\times5.5,5\}=5.95$；$v_4=6.355$。数值一步步上升，逼近 10，每次的误差都不超过 $0.9^k\times10$。可以用 3 行代码核对。
"""),
  THINK("**概念辨析**：(1) 贝尔曼期望方程和最优方程差在哪一步？为什么前者是线性方程组而后者不是？(2) 当 $\\gamma$ 从 0.9 提高到 0.99，按收缩界 $\\gamma^k$，要把初始误差压到 $10^{-6}$ 倍以内，各需要多少次扫描？", r"""
(1) 差在「对动作怎么处理」：期望方程按策略概率**加权平均**，对 $v$ 是线性的；最优方程取 $\max$，$\max$ 是非线性的，没法写成 $v=r+\gamma Pv$ 这种矩阵形式，只能迭代（或用线性规划）。

(2) 需要 $\gamma^k\le10^{-6}$，即 $k\ge\ln(10^{-6})/\ln\gamma$。$\gamma=0.9$：$13.8155/0.10536\approx131.1$，至少 **132** 次；$\gamma=0.99$：$13.8155/0.01005\approx1374.6$，至少 **1375** 次，约多了 10 倍。长远规划（$\gamma$ 大）收敛慢，这也是实际训练里远期回报难学的数学原因之一。（这是上界，真实扫描次数可能少，如上面的网格世界。）
"""),
  THINK("**联系机器学习 / 世界模型**：Atari 游戏的状态是 $210\\times160$ 的彩色像素，动作 18 个。动态规划为什么直接用不了？下一节和世界模型各自去掉了 DP 的哪一个前提？", r"""
两个障碍：**(1) 状态数天文数字**，每次扫描要遍历所有状态，更不可能存一张 $v(s)$ 表（像素组合的数量远超宇宙里的原子数）；**(2) 模型未知**，没人给你 $P$ 和 $R$。

下一节（无模型学习）去掉的是前提 (2)：不需要模型，直接用交互得到的样本 $(s,a,r,s')$ 来更新价值（TD、Q-learning），而且只更新碰到的状态；解决 (1) 要靠函数近似（用神经网络代替表格，第 4 节起）。世界模型去掉的也是前提 (2)，但走另一条路：先从数据里学出一个 $P,R$ 的近似（最好是在压缩后的潜在空间里，这同时缓解了 (1)），再用它来规划或生成想象的数据。
"""),
  KW(("贝尔曼方程","Bellman equation","价值与后继状态价值之间的递推关系"),
     ("贝尔曼期望方程","Bellman expectation equation","对给定策略 $\\pi$ 的 $v_\\pi$ 的递推，线性"),
     ("贝尔曼最优方程","Bellman optimality equation","把按策略平均换成 $\\max$，非线性"),
     ("自举","bootstrapping","用估计值更新估计值"),
     ("策略评估","policy evaluation","给定策略，求 $v_\\pi$（预测）"),
     ("策略改进","policy improvement","对 $q_\\pi$ 取贪心得到不更差的新策略"),
     ("策略迭代","policy iteration","评估与改进交替，有限步收敛"),
     ("价值迭代","value iteration","反复做最优备份，收敛到 $v_*$"),
     ("广义策略迭代","generalized policy iteration (GPI)","评估和改进相互追赶的统一视角"),
     ("最优价值函数","optimal value function $v_*$","所有策略中最大的价值"),
     ("最优策略","optimal policy $\\pi_*$","对 $q_*$ 贪心得到的确定性策略"),
     ("收缩映射","contraction mapping","每次使距离缩小到 $\\gamma$ 倍的映射"),
     ("不动点","fixed point","$Tv=v$ 的点，价值迭代的收敛目标"),
     ("最大范数","max norm $\\|\\cdot\\|_\\infty$","向量分量绝对值的最大值，度量价值向量的距离"),
     ("动态规划","dynamic programming (DP)","利用最优子结构和重叠子问题求解，MDP 里需已知模型"),
  ),
 ],
 "references": [
  {"title": "Sutton & Barto《Reinforcement Learning: An Introduction》第二版（2018），第 4 章 Dynamic Programming（4.1 Policy Evaluation、4.2 Policy Improvement、4.3 Policy Iteration、4.4 Value Iteration、4.6 Generalized Policy Iteration）；贝尔曼方程见 3.5–3.6", "url": "http://incompleteideas.net/book/RLbook2020.pdf", "note": "本节依据的开放教材（作者免费公开）；讲解为自写，未转载原文"},
  {"title": "David Silver：RL Course, Lecture 3: Planning by Dynamic Programming（DeepMind / UCL，约 99 分钟）", "url": "https://www.youtube.com/watch?v=Nd1-UUMVfz4", "note": "选看：同一主题的大学课堂版本，含收缩映射的证明"},
  {"title": "Hugging Face Deep RL Course, Unit 2: The Bellman Equation", "url": "https://huggingface.co/learn/deep-rl-course/unit2/bellman-equation", "note": "免费课程里用很短的篇幅讲贝尔曼方程，可以当复习"},
  {"title": "OpenAI Spinning Up：Key Concepts in RL（含 Bellman Equations 一节）", "url": "https://spinningup.openai.com/en/latest/spinningup/rl_intro.html", "note": "简明的符号对照表，读论文时可以回头查"},
 ],
 "quiz": {"questions": QUIZ},
}

if __name__ == '__main__':
    dump(unit, "wm-0", "u02-bellman-dp.json")
