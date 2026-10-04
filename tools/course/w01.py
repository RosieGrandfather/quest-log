"""wm-0 第 1 节：马尔可夫决策过程（v3 格式，2026-10-04）"""
from unitlib import *
from w01c import C_LOOP, C_MDP, C_RET, C_MC, C_POMDP
from w01_quiz import QUIZ

unit = {
 "id": "u01",
 "title": "马尔可夫决策过程：智能体与环境",
 "en": "Markov Decision Processes",
 "minutes": 90,
 "objectives": [
  "理解 **智能体-环境循环 (agent–environment interaction)**：状态、动作、奖励如何一步步产生一条 **轨迹 (trajectory)**，并能用代码写出一个最小的环境（`reset` / `step`）",
  "掌握 **马尔可夫决策过程 (MDP)** 的五元组 $(S,A,P,R,\\gamma)$ 和 **马尔可夫性 (Markov property)**，会把转移概率存成 `P[s, a, s']` 数组并检查合法性",
  "会算 **回报 (return)** $G_t=\\sum_k\\gamma^kR_{t+k+1}$，理解 **折扣因子 (discount factor)** 的作用与「有效视野」$1/(1-\\gamma)$，写出递推式 $G_t=R_{t+1}+\\gamma G_{t+1}$",
  "给出 **策略 (policy)**、**状态价值 (state value)** $v_\\pi$、**动作价值 (action value)** $q_\\pi$ 的定义和它们的关系，并用蒙特卡洛采样在网格世界里估计它们",
  "分清 **回合制任务 (episodic)** 与 **持续任务 (continuing)**，知道 **部分可观测 MDP (POMDP)** 和 **信念 (belief)**，明白它们为什么是通往世界模型的第一站",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

强化学习 (reinforcement learning, RL) 研究的问题只有一句话：**一个会行动的程序，怎样通过和环境反复交互，学会拿到更多的长期奖励**。这门课要走到的终点是「世界模型 (world model)」：让智能体学出一个环境的内部副本，在脑子里预演未来，再据此决定怎么做。要理解这个终点，得先把「环境」「行动」「奖励」「未来」这几个词说成数学语言，这就是 **马尔可夫决策过程 (Markov Decision Process, MDP)**。它是整个强化学习的地基：后面所有算法（动态规划、Q-learning、策略梯度、Dreamer）都是在回答「在一个 MDP 里怎么找到好的行动方式」。

**这一节和世界模型的关系。** MDP 的五个部分里，$P$（状态怎么转移）和 $R$（给多少奖励）合起来就是**环境的动力学**。「基于模型的强化学习」和「世界模型」要学的，正是这两样东西的近似：一个能回答「如果我在这里做这个动作，接下来会发生什么」的函数。另外，真实世界里智能体几乎从来看不到完整的状态，只能看到带噪声的观测（一帧画面、一段传感器读数），这就是 **POMDP**（本节最后讲）。世界模型里的「潜在状态 (latent state)」就是为了从观测的历史里恢复出一个够用的状态。

**学完它你就能看懂这几件事：**

- Gymnasium 里 `obs, reward, terminated, truncated, info = env.step(action)` 这一行每个返回值是什么，为什么要区分 `terminated` 和 `truncated`；
- 论文里一上来就写的「Consider an MDP $(S,A,P,R,\gamma)$」到底在说什么，为什么折扣因子几乎总是取 0.99 附近；
- 为什么 DQN 要把最近 4 帧画面叠在一起当输入（观测不是状态），为什么 Dreamer 这类方法要在循环网络里维护一个潜在状态；
- 后面几节反复出现的 $v_\pi(s)$、$q_\pi(s,a)$、$G_t$ 的含义。

**本节安排（约 90 分钟）**：智能体与环境（10 分钟）→ MDP 的五元组（15 分钟）→ 视频一（18 分钟）→ 回报与折扣（15 分钟）→ 策略与价值函数（10 分钟）→ 动手实验：网格世界里的蒙特卡洛（12 分钟）→ 部分可观测 (POMDP)（5 分钟）→ 视频二（4 分钟）→「想一想」。视频是英文的，可以打开 YouTube 的中文字幕。

### 智能体与环境：一个循环

> **标准定义 · 智能体-环境交互 (agent–environment interface)**
>
> 时间离散为 $t=0,1,2,\dots$。在每个时刻 $t$，**智能体 (agent)** 观察到状态 $S_t$，选择一个**动作 (action)** $A_t$；**环境 (environment)** 随后返回一个标量**奖励 (reward)** $R_{t+1}$ 和新的状态 $S_{t+1}$。这样产生的序列
>
> $$S_0,A_0,R_1,S_1,A_1,R_2,S_2,A_2,R_3,\dots$$
>
> 叫做一条**轨迹 (trajectory)**，也叫一次 **rollout**。智能体的目标是最大化未来奖励的累积（见后文「回报」）。
>
> *English: At each step the agent observes a state, picks an action, and the environment responds with a scalar reward and a next state. The resulting sequence is a trajectory. The agent's goal is to maximize the cumulative future reward.*

**白话版：「玩游戏：看屏幕、按按钮、得分」。** 状态是屏幕上此刻的局面，动作是你按的键，奖励是分数的变化。重点是它是一个**循环**，不是一次预测：你的动作会改变之后看到的东西，所以「现在得 1 分但把自己送进死路」和「现在不得分但铺好后路」是两回事。这和监督学习（给输入、预测标签、标签不受你的预测影响）有本质区别。

把循环写成代码，就是一个有 `reset()` 和 `step(a)` 两个方法的环境类。下面是一个 5×5 的**网格世界 (gridworld)**：起点在左上角，终点在右下角（奖励 $+10$），中间有一个陷阱（奖励 $-10$），其余每步奖励为 0，撞墙则留在原地。这个环境会贯穿整门课的前三节。

""" + C_LOOP + r"""

读输出：这是一个**随机策略**（四个方向等概率）走出来的轨迹。第 0 步从状态 0 向右到状态 1；接下来**四次**向上，但状态 1 已经在最上面一行，撞墙留在原地，所以「下一状态」还是 1，奖励依然是 0；之后在状态 2、3 之间来回，最后向下走到 7、12。12 步里没有走到终点或陷阱，所以没有出现「终止」。一条轨迹的长度是随机的；每一步的 `(状态, 动作, 奖励, 下一状态)` 就是后面所有算法的原材料。

### MDP：把环境写成五个对象

> **标准定义 · 马尔可夫决策过程 (Markov Decision Process, MDP)**
>
> 一个**有限 MDP** 是五元组 $(S,A,P,R,\gamma)$：
>
> - $S$ 是**状态 (state)** 的有限集合，$A$ 是**动作 (action)** 的有限集合；
> - $P(s'\mid s,a)=\Pr(S_{t+1}=s'\mid S_t=s,A_t=a)$ 是**转移概率 (transition probability)**，对每个 $(s,a)$ 有 $\sum_{s'}P(s'\mid s,a)=1$；
> - $R(s,a)=\mathbb{E}[R_{t+1}\mid S_t=s,A_t=a]$ 是**奖励函数 (reward function)**，即在 $(s,a)$ 之后的期望即时奖励；
> - $\gamma\in[0,1]$ 是**折扣因子 (discount factor)**。
>
> 并且满足**马尔可夫性 (Markov property)**：给定当前状态和动作，未来与过去无关，$\Pr(S_{t+1}=s'\mid S_t,A_t,S_{t-1},A_{t-1},\dots)=\Pr(S_{t+1}=s'\mid S_t,A_t)$。
>
> *English: A finite MDP is a tuple (S, A, P, R, γ) of states, actions, transition probabilities, expected rewards and a discount factor, where the next state depends only on the current state and action (the Markov property).*

**白话版：「状态是一张够用的存档」。** 马尔可夫性不是说世界没有历史，而是说**状态已经把历史里有用的部分都存进去了**。象棋的状态是当前棋盘，不需要知道棋是怎么走到这一步的；但如果状态只是「球的位置」而不含「球的速度」，历史就变得有用，这个「状态」就不满足马尔可夫性。**判断一个东西能不能当状态，就看它是否足以预测下一步。** 另外注意：转移可以是随机的（$P$ 是概率），随机性不违反马尔可夫性。

Sutton & Barto 的教材把动力学写成更一般的 $p(s',r\mid s,a)$（下一状态和奖励的联合分布）；上面这种 $P$ 加 $R$ 的写法和它等价，是后面动态规划里更方便的形式。

把 MDP 写成数组：转移概率是一个三维数组 `P[s, a, s']`，奖励是二维数组 `R[s, a]`。下面是一个只有 3 个状态的小 MDP（状态 2 是终止状态，进去就出不来，叫**吸收态 (absorbing state)**）。同时验证两件事：概率行和为 1；采样得到的经验频率和 `P` 一致。最后把一个策略「合」进 MDP，得到只含状态的马尔可夫链 $P_\pi$，它会在第 2 节里反复出现。

""" + C_MDP + r"""

读输出：六个 $(s,a)$ 组合的转移概率行和都是 1，合法。在 $(s=1,a=1)$ 上采样 10 万次，到达状态 0、1、2 的频率是 $(0,0.201,0.799)$，非常接近真实的 $(0,0.2,0.8)$。最后两行：策略取「两个动作各一半」时，状态 0 的下一状态分布是 $0.5\times(0.7,0.3,0)+0.5\times(0.1,0.9,0)=(0.4,0.6,0)$，状态 1 是 $(0.25,0.35,0.4)$，状态 2 吸收；对应的平均即时奖励 $r_\pi=(-0.5,2.5,0)$。「MDP + 策略 = 马尔可夫链」这个观察，让后面可以用线性代数来求价值。
"""),
  V("NFo9v_yKQXA", "视频一：Reinforcement Learning, by the Book（Mutual Information）", 18),
  T(r"""
### 回报与折扣：「未来」有多重要

> **标准定义 · 回报与折扣 (return & discounting)**
>
> 时刻 $t$ 之后的**折扣回报 (discounted return)** 是未来奖励的加权和：
>
> $$G_t=R_{t+1}+\gamma R_{t+2}+\gamma^2R_{t+3}+\cdots=\sum_{k=0}^{\infty}\gamma^kR_{t+k+1}$$
>
> 它满足**递推关系**
>
> $$G_t=R_{t+1}+\gamma\,G_{t+1}$$
>
> 若奖励有界 $|R|\le R_{\max}$ 且 $\gamma<1$，则 $|G_t|\le R_{\max}/(1-\gamma)$，回报一定有限。
>
> *English: The discounted return is G_t = Σ_k γ^k R_{t+k+1}. It obeys the recursion G_t = R_{t+1} + γ G_{t+1}, and is finite whenever rewards are bounded and γ < 1.*

**白话版：「明天的一块钱不如今天的一块钱」。** $\gamma$ 决定未来的奖励值多少钱：$\gamma=0$ 时只看眼前（完全短视），$\gamma$ 越接近 1 越有远见。$k$ 步之后的奖励要乘 $\gamma^k$，所以大约 $1/(1-\gamma)$ 步之外的奖励基本可以忽略，这个数叫**有效视野 (effective horizon)**：$\gamma=0.9$ 约 10 步，$\gamma=0.99$ 约 100 步。折扣有两个用处：一是让无限长的持续任务回报变成有限数；二是表达「越早拿到越好」的偏好。

递推式 $G_t=R_{t+1}+\gamma G_{t+1}$ 的推导只有一行：把 $\gamma R_{t+2}+\gamma^2R_{t+3}+\cdots$ 提出一个 $\gamma$，括号里恰好是 $G_{t+1}$。**这一行是整门课最重要的等式之一**：它说「现在的回报 = 眼前的奖励 + 折扣后的未来回报」，贝尔曼方程、时序差分学习、Q-learning 全是它的变形。

""" + C_RET + r"""

读输出：奖励序列 $(0,0,0,10)$（第 4 步才拿到 10）：$\gamma=1$ 时回报是 10；$\gamma=0.9$ 时是 $0.9^3\times10=7.29$；$\gamma=0.5$ 时是 1.25；$\gamma=0$ 时是 0，因为眼前什么都没有。从前往后按定义算，和从后往前用递推式算，数字完全相同，500 条随机奖励序列上的对拍也是 `True`。

下面是持续任务：每步奖励恒为 1，永不结束。$\gamma=0.5,0.9,0.99$ 时回报分别是 2、10、100，恰好是 $1/(1-\gamma)$（几何级数求和），有效视野也是 2、10、100 步。而 $\gamma=1$ 时，前 100 步的和是 100，前 5000 步的和是 5000，一直涨、没有极限，回报没有定义。这就是持续任务必须 $\gamma<1$ 的原因。

### 回合制任务与持续任务

> **标准定义 · 回合制与持续任务 (episodic vs continuing tasks)**
>
> **回合制任务**：交互自然地分成一个个有限长的**回合 (episode)**，每个回合在某个**终止状态 (terminal state)** 结束，之后重新从起点开始（棋局、迷宫、一局游戏）。**持续任务**：交互永不终止（长期运行的控制器、库存管理）。统一写法：把终止状态看成一个**吸收态**——进去之后永远留在原地、奖励恒为 0，这样两类任务都可以写成 $G_t=\sum_{k\ge0}\gamma^kR_{t+k+1}$，回合制任务里 $\gamma=1$ 也合法。
>
> *English: Episodic tasks end in a terminal state and restart; continuing tasks never end. Both can be written with the same return formula by treating the terminal state as an absorbing state with zero reward.*

**白话版：「一盘棋」对「一辈子」。** 下棋有输赢结束的时候，运营一家商店没有。实践中还有第三种情形：任务本来没有终点，但训练时为了方便被**截断 (truncation)** 成固定长度，比如「最多 1000 步」。这时回合是因为**时间到了**结束，而不是因为**走到了终点**。Gymnasium 把这两种结束分成 `terminated`（真正的终止状态）和 `truncated`（超时被截断）：前者之后的价值确实是 0，后者之后世界还在继续，价值不该当成 0。后面 Q-learning 做「自举」的时候就要用到这个区分。

### 策略与价值函数

> **标准定义 · 策略与价值函数 (policy, state value, action value)**
>
> **策略** $\pi(a\mid s)=\Pr(A_t=a\mid S_t=s)$ 是智能体的行为规则：在每个状态下选各个动作的概率（确定性策略是它的特例）。给定策略 $\pi$，**状态价值函数**是从 $s$ 出发、之后一直按 $\pi$ 行动所得回报的期望：
>
> $$v_\pi(s)=\mathbb{E}_\pi\big[G_t\mid S_t=s\big]$$
>
> **动作价值函数**是在 $s$ 先做动作 $a$、之后再按 $\pi$ 行动的期望回报：
>
> $$q_\pi(s,a)=\mathbb{E}_\pi\big[G_t\mid S_t=s,A_t=a\big]$$
>
> 两者的关系：$v_\pi(s)=\sum_a\pi(a\mid s)\,q_\pi(s,a)$。
>
> *English: A policy maps states to action probabilities. The state value v_π(s) is the expected return starting from s and following π; the action value q_π(s,a) is the expected return after taking a in s and then following π. v_π(s) is the π-weighted average of q_π(s,a).*

**白话版：「这个位置值多少钱」。** 下围棋时，一个局面是不是好，取决于「接下来你怎么下」，所以价值总是**相对于一个策略**的。$v_\pi(s)$ 是「从这里开始照 $\pi$ 玩，平均能拿多少分」，$q_\pi(s,a)$ 多问了一步：「如果我这一步偏要走 $a$，之后再照 $\pi$ 玩，平均能拿多少分」。选动作的时候看 $q$ 更方便，因为它直接告诉你每个动作值多少；这就是 Q-learning 学 $q$ 而不学 $v$ 的原因（第 3 节）。

价值函数的定义里有一个期望，期望可以用**平均**来近似：让策略真的玩很多局，把每局的回报平均。这就是**蒙特卡洛 (Monte Carlo)** 的思想，也是下面实验的做法。

### 动手实验：网格世界里估计价值，看 $\gamma$ 的影响

用随机策略从起点出发玩 20000 局，把每一局的回报按不同的 $\gamma$ 算出来再取平均，得到 $v_\pi(\text{起点})$ 的估计；然后强制第一步做某个动作，之后继续随机，得到起点的 $q_\pi$。注意同一批轨迹可以同时算多个 $\gamma$ 的回报，因为 $\gamma$ 只出现在「怎么把奖励加起来」里，不影响环境本身。

""" + C_MC + r"""

读输出：

- 20000 局全部在 500 步内结束，平均长度 41.3 步，最长 316 步（随机走路有时会绕很久），所以「500 步截断」几乎没有影响。
- $\gamma=0.5$：$v\approx-0.013$。起点离终点和陷阱都至少 6 步，$0.5^6\approx0.016$，远处的奖励被折扣得几乎看不见，价值接近 0。
- $\gamma$ 从 0.5 增大到 0.9、0.99、1.0，估计值依次是 $-0.822$、$-4.323$、$-5.959$：折扣越小，未来的 $\pm10$ 越不重要。$\gamma=1$ 时回报就是 $10\times(\text{先到终点的概率}-\text{先掉进陷阱的概率})$，$-5.959$ 说明随机走路大约 80% 先掉进陷阱、20% 先到终点（因为全部回合都结束了），所以越在乎远处，价值越负。标准误最大约 0.06，这些差别远大于采样噪声。
- 起点的动作价值（$\gamma=0.9$）：上 $-0.695$、下 $-0.808$、左 $-0.747$、右 $-1.017$。每个动作 5000 局，标准误大约 0.02 到 0.03，所以「向右」明显最差，上、左、下之间的差距要小心解读（下一节会精确算出来：上和左都是撞墙、留在起点，真实的 $q$ 值其实完全相等，这里的差别只是采样噪声）。四个值的平均是 $-0.817$，与上面直接估计的 $v=-0.822$ 相差在误差之内，印证了 $v_\pi(s)=\sum_a\pi(a\mid s)q_\pi(s,a)$（这里 $\pi$ 是均匀的，所以就是算术平均）。

**自己试试**：把陷阱挪到别处（改 `TRAP`），或者给每步加 $-0.1$ 的奖励，看 $v$ 怎么变；把 `gammas` 改成 `[0.8, 0.95]`。这个实验的缺点是：每个状态都要玩上万局，状态多了根本算不过来。**下一节会看到，用贝尔曼方程可以不玩一局就精确算出同样的数字**。

### 部分可观测：智能体看到的不一定是状态

前面默认智能体**看到的就是状态**。真实世界里往往不是：摄像头只给出一帧画面，看不出球的速度；对话里用户的真实意图藏在话后面。这时智能体拿到的是**观测 (observation)** $O_t$，状态 $S_t$ 藏在背后。

> **标准定义 · 部分可观测马尔可夫决策过程 (POMDP)**
>
> POMDP 在 MDP 的基础上增加**观测集合** $\Omega$ 和**观测概率** $O(o\mid s',a)$：智能体看不到状态，只看到观测。因为观测通常不满足马尔可夫性，智能体需要维护一个**信念状态 (belief state)** $b_t(s)=\Pr(S_t=s\mid O_{1:t},A_{0:t-1})$，即「根据到目前为止所有观测和动作，状态是各个 $s$ 的概率」，并按贝叶斯规则更新：
>
> $$b'(s')\;\propto\;O(o\mid s',a)\sum_sP(s'\mid s,a)\,b(s)$$
>
> 信念本身满足马尔可夫性，所以「POMDP 是以信念为状态的（连续状态）MDP」。
>
> *English: A POMDP adds observations and an observation model. The agent maintains a belief, a posterior over hidden states given the history, updated by Bayes' rule; the belief itself is a Markov state.*

**白话版：「侦探的脑内嫌疑人名单」。** 侦探看不到真相，只有一条条线索（观测）。他不断更新「每个嫌疑人是真凶的概率」，这张名单就是信念。看更多线索，名单越来越集中。

下面的实验是最简单的情形：宝藏在左或右房间（真实状态固定），传感器 80% 准确。每看到一个观测，就按贝叶斯规则更新一次信念。

""" + C_POMDP + r"""

读输出：真实状态是「左」，起初信念是 0.5 对 0.5。前两次观测碰巧都是「右」（20% 的错误读数），信念 $P(\text{左})$ 降到 0.200、0.059，**智能体被误导了**；之后连续看到「左」，信念经过 0.200、0.500、0.800 一路升到 0.941、0.985、0.996。**单个观测可能骗人，历史累积起来的信念却越来越可靠**，这就是为什么部分可观测的问题里要**记住历史**，而不是只盯着当前这一帧。

**这和世界模型有什么关系？** 现代的世界模型（本课第 6、8 节）做的正是用神经网络来近似「观测历史 → 潜在状态」这一步：循环网络或状态空间模型把历史压缩成一个向量，充当学出来的信念。DQN 把最近 4 帧叠在一起当输入，是同一件事最朴素的做法。
"""),
  V("4Fqt2Nk2lhY", "视频二：Markov Decision Process (MDP) - 5 Minutes with Cyrill（Cyrill Stachniss）", 4),
  T(r"""
### 这一节你要带走的三句话

1. **MDP $=(S,A,P,R,\gamma)$ 加上马尔可夫性**：状态是够用的存档，$P$ 和 $R$ 是环境的动力学，世界模型要学的正是这两样。
2. **回报 $G_t=R_{t+1}+\gamma G_{t+1}$**：折扣因子 $\gamma$ 让持续任务的回报有限，有效视野约 $1/(1-\gamma)$ 步；这个递推式是后面所有算法的出发点。
3. **价值是回报的期望**：$v_\pi(s)=\sum_a\pi(a\mid s)q_\pi(s,a)$；可以用蒙特卡洛平均来估计，但计算量大，下一节用贝尔曼方程精确求解；看不到完整状态时是 POMDP，要靠信念或潜在状态。
"""),
  THINK("奖励序列是 $R_1=0,R_2=0,R_3=5,R_4=0,R_5=10$（之后回合结束），$\\gamma=0.9$。分别用定义和递推式 $G_t=R_{t+1}+\\gamma G_{t+1}$ 算 $G_0$。", r"""
按定义：$G_0=\gamma^2\times5+\gamma^4\times10=0.81\times5+0.6561\times10=4.05+6.561=10.611$。

按递推式从后往前：$G_5=0$（回合结束）；$G_4=R_5+\gamma G_5=10$；$G_3=R_4+\gamma G_4=0+9=9$；$G_2=R_3+\gamma G_3=5+8.1=13.1$；$G_1=R_2+\gamma G_2=11.79$；$G_0=R_1+\gamma G_1=10.611$。两种算法一致。可以用上面的 `discounted_return([0, 0, 5, 0, 10], 0.9)` 核对。递推式的好处是**一遍扫描就把所有 $G_t$ 算出来了**，这正是训练时处理一整局数据的做法。
"""),
  THINK("**概念辨析**：奖励 $R_{t+1}$、回报 $G_t$、价值 $v_\\pi(s)$ 三者有什么区别？为什么智能体应该最大化「价值」而不是「奖励」？", r"""
- **奖励**是环境在一步之后给的一个数，是单步的、实际发生的。
- **回报**是一条具体轨迹上从 $t$ 起所有（折扣后）奖励的和，是一个随机变量：同一个状态出发，不同的运气会有不同的回报。
- **价值**是回报的**期望**，是一个确定的数，对每个状态（或状态-动作对）而言，且依赖于策略。

如果只追求单步奖励，会「吃了糖果但摔进坑里」：眼前的奖励高，后续回报很差。价值把整个未来都考虑进来，所以选动作应当比较价值（准确地说是 $q$）。回报的随机性也是第 3 节「蒙特卡洛方差大」的来源。
"""),
  THINK("**联系世界模型**：下面哪些情形满足马尔可夫性，哪些不满足？(a) 象棋，状态是当前棋盘；(b) 乒乓球游戏，状态只是单帧画面；(c) 同一个游戏，状态是最近 4 帧画面。若不满足，你会怎么补救？", r"""
(a) 满足（忽略「三次重复局面判和」之类需要历史的规则的话），当前棋盘足够预测下一步的可能结果。

(b) 不满足：单帧画面里看不出球往哪个方向、多快飞，历史对预测有用，这是 POMDP。

(c) 近似满足：4 帧可以估计出速度和方向，这是 DQN 的做法。更一般的补救是**让模型自己记住历史**：用循环网络或状态空间模型维护一个潜在状态（信念的神经网络版本），这正是世界模型（第 6 节开始）做的事。
"""),
  KW(("马尔可夫决策过程","Markov decision process (MDP)","五元组 $(S,A,P,R,\\gamma)$ 加马尔可夫性，描述环境"),
     ("智能体","agent","选择动作的决策者"),
     ("环境","environment","根据动作返回奖励和新状态的一方"),
     ("状态 / 动作","state / action","$S_t$、$A_t$：局面与可做的选择"),
     ("奖励","reward","环境每步给出的标量 $R_{t+1}$"),
     ("转移概率","transition probability $P(s'\\mid s,a)$","做动作后下一状态的分布"),
     ("马尔可夫性","Markov property","下一状态只依赖当前状态和动作"),
     ("轨迹 / 回合","trajectory / episode","$S_0,A_0,R_1,S_1,\\dots$ 一条交互序列 / 一局"),
     ("回报","return $G_t$","未来折扣奖励之和，$G_t=R_{t+1}+\\gamma G_{t+1}$"),
     ("折扣因子","discount factor $\\gamma$","未来奖励的折扣；有效视野约 $1/(1-\\gamma)$"),
     ("策略","policy $\\pi(a\\mid s)$","每个状态下选各动作的概率"),
     ("状态价值 / 动作价值","$v_\\pi(s)$ / $q_\\pi(s,a)$","按策略行动的期望回报"),
     ("回合制 / 持续任务","episodic / continuing task","有终点 / 没有终点；终止 vs 截断要区分"),
     ("蒙特卡洛","Monte Carlo","用大量采样的平均来近似期望"),
     ("部分可观测 MDP","POMDP","智能体只看到观测；维护信念或潜在状态"),
  ),
 ],
 "references": [
  {"title": "Sutton & Barto《Reinforcement Learning: An Introduction》第二版（2018），第 3 章 Finite Markov Decision Processes（3.1–3.6）；17.3 Observations and State", "url": "http://incompleteideas.net/book/RLbook2020.pdf", "note": "本节内容依据的开放教材（作者免费公开）；讲解为自写，未转载原文"},
  {"title": "David Silver：RL Course, Lecture 2: Markov Decision Process（DeepMind / UCL，约 102 分钟）", "url": "https://www.youtube.com/watch?v=lfHX2hHRMVQ", "note": "选看：同一主题的大学课堂版本，想系统听一遍时用；课程主页见 davidsilver.uk/teaching"},
  {"title": "David Silver 的强化学习课程主页（讲义 PDF 与视频）", "url": "https://www.davidsilver.uk/teaching/", "note": "整套 10 讲课程的讲义"},
  {"title": "Hugging Face Deep RL Course, Unit 1: Introduction to Deep Reinforcement Learning", "url": "https://huggingface.co/learn/deep-rl-course/unit1/introduction", "note": "免费课程，带可运行的练习，适合在手机之外动手"},
 ],
 "quiz": {"questions": QUIZ},
}

if __name__ == '__main__':
    dump(unit, "wm-0", "u01-mdp.json")
