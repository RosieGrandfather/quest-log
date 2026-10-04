"""wm-0 第 4 节：策略梯度与深度强化学习（v3 格式，2026-10-04）"""
from unitlib import *
from w04c import (C_FA, C_BAIRD, C_DQN, C_TDQN, C_SCORE, C_VAR, C_BANDIT,
                   C_REINFORCE, C_GRID, C_PPO, C_RLHF, C_TPG)
from w04_quiz import QUIZ

unit = {
 "id": "u04",
 "title": "策略梯度与深度强化学习",
 "en": "Policy Gradient & Deep RL",
 "minutes": 120,
 "objectives": [
  "说清为什么要用 **函数逼近 (function approximation)**：状态太多或连续时查表不可行，而且查表不能泛化；知道 **致命三角 (deadly triad)** 为什么会让价值学习发散",
  "理解 **DQN** 的两个稳定化技巧——**经验回放 (experience replay)** 与 **目标网络 (target network)**——各自解决什么问题，并能读懂一段 PyTorch 的 DQN 更新",
  "能推导 **策略梯度定理 (policy gradient theorem)**：对数导数技巧、为什么环境的转移概率会消失、为什么可以用「未来回报」代替整条轨迹的回报；会写 **REINFORCE**",
  "理解 **基线 (baseline)** 为什么不改变梯度的期望却能大幅降低方差，以及 **优势函数 (advantage)** 与 **actor-critic** 的偏差—方差取舍",
  "知道 **PPO** 的裁剪目标在做什么，并能说出它与 **RLHF** 的联系：语言模型是策略，KL 惩罚把策略拴在参考模型附近",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

前三节的方法有一个共同点：状态可以一个一个数出来，价值存在表里。真实的问题（图像、连续的机器人状态、一整段文字）没法这样做。这一节回答两个问题：**价值函数换成神经网络之后会出什么事？**（DQN 的故事）以及 **不通过价值、直接对策略求梯度行不行？**（策略梯度的故事）。后者是现代强化学习的主干：PPO 用它训练机器人和游戏智能体，RLHF 用它训练对话模型，世界模型里在「想象」中训练智能体用的也是 actor-critic 一族。

**这一节和世界模型的关系：** 世界模型本身是一个学出来的环境模型，但模型建好之后还要有人来「用」它，也就是一个策略。Ha 和 Schmidhuber 的 World Models 里有一个很小的控制器 C，Dreamer 一类方法在模型想象出的轨迹里训练 actor-critic。你需要把这一节当成「怎样训练一个策略」的工具箱；后面第 7、8 节会把它装到学出来的模型上。另外，策略梯度里的对数导数技巧会在下一节（VAE）里再次出现，是同一个数学工具。

**学完它你就能看懂这几件事：**

- DQN 论文里「经验回放」「目标网络」为什么是必须的，而不是工程上的小优化；
- 一段 `loss = -(log_prob * advantage).mean()` 的 PyTorch 代码为什么这么写，为什么优势要 `.detach()`；
- PPO 的 `torch.clamp(ratio, 1 - eps, 1 + eps)` 在限制什么，InstructGPT 里「奖励 = 奖励模型的分数 − KL 惩罚」是怎么回事；
- 读强化学习论文时，那一页「$\nabla_\theta J(\theta)=\mathbb{E}[\cdots]$」是怎么来的。

**本节安排（约 120 分钟）**：函数逼近与致命三角（16 分钟）→ DQN（14 分钟）→ 视频一（11 分钟）→ 策略梯度定理（14 分钟）→ 视频二（20 分钟）→ REINFORCE 与基线（18 分钟）→ actor-critic（6 分钟）→ PPO（6 分钟）→ 与 RLHF 的联系（8 分钟）→「想一想」（7 分钟）。视频是英文的，可以打开 YouTube 的中文字幕；代码里 NumPy 部分直接运行，PyTorch 部分需要先 `pip install torch`。

### 为什么需要函数逼近

> **标准定义 · 函数逼近 (function approximation)**
>
> 用一族带参数的函数 $\hat v(s;\mathbf w)$（或 $\hat q(s,a;\mathbf w)$）去近似价值函数，参数个数 $d$ 远小于状态数。学习变成调整 $\mathbf w$ 使误差变小。以**梯度蒙特卡洛**为例，回报 $G_t$ 当作目标：
>
> $$\mathbf w\leftarrow\mathbf w+\alpha\,\big(G_t-\hat v(S_t;\mathbf w)\big)\,\nabla_{\mathbf w}\hat v(S_t;\mathbf w)$$
>
> 如果目标是自举得到的，如 $R_{t+1}+\gamma\hat v(S_{t+1};\mathbf w)$，把它当成常数、不对它求梯度，就得到**半梯度 (semi-gradient)** TD 方法。
>
> *English: Function approximation represents the value function with a parametric family whose number of parameters is much smaller than the number of states, so that experience in one state generalizes to others. Bootstrapped targets treated as constants give semi-gradient methods.*

**白话版：「用有限的笔记本记无限的路」。** 查表就像给城里每个门牌号各记一页笔记，页数无限，而且去过 1 号楼的经验帮不了 2 号楼。函数逼近让相邻的状态共用同一条笔记：学 50 号状态时，附近状态的估计也被带着动。代价是「带着动」带来的偏差，以及后面要说的稳定性问题。

下面做一个很小的实验。100 个状态排成一排，从 50 出发，每步随机跳到左右 10 格以内；从右边出界得 $+1$，从左边出界得 $-1$。用同一个蒙特卡洛学习规则，对比**查表**（100 个参数）和**状态聚合**（10 个相邻状态共用一个参数，共 10 个参数），看它们离真实价值有多远：

""" + C_FA + r"""

读输出：真实价值从 $v(1)=-0.913$ 光滑地变到 $v(100)=0.913$，$v(50)=-0.009$，接近 0。误差是对 100 个状态的均方根误差，数字是 10 个随机种子的平均。

- **前期**：学 10 个回合后，查表的误差还有 0.529，聚合是 0.458；50 个回合后 0.489 对 0.281，**聚合明显更快**，因为一个回合里经过的每个状态都在帮同一组的其他状态更新；
- **后期**：1000 个回合后查表降到 0.163，聚合是 0.148，两者接近。聚合有一个下限（同一组里的状态价值其实不同，它们只能共用一个数），查表没有，但需要更多数据去追。

这就是函数逼近的核心交易：**用偏差换泛化**。神经网络是更强、更灵活的函数族，但这个交易的另一面——不稳定——也更严重。

### 致命三角

> **标准定义 · 致命三角 (deadly triad)**
>
> 当下面三个要素**同时**出现时，价值学习可能发散（价值估计趋向无穷大）：①**函数逼近**（参数共享、泛化）；②**自举 (bootstrapping)**（用估计值更新估计值，如 TD、Q-learning）；③**离策略 (off-policy)**（用别的策略产生的数据学习）。三者缺一，发散的风险就大大减小。
>
> *English: Divergence of value learning can occur when function approximation, bootstrapping, and off-policy training are combined; this is known as the deadly triad (Sutton & Barto, Sec. 11.3).*

**白话版：「三个都用，就像用自己的草稿给自己改作业」。** 自举是用自己的估计当答案，函数逼近让一个状态的修改影响别的状态，离策略让数据的分布和真正要评价的策略对不上。三件事互相放大，错误会沿着循环越滚越大。Baird 的反例把它做得很干净：所有奖励都是 0，真实价值处处为 0，权重 $\mathbf w=\mathbf 0$ 就能精确表示它，也就是说「正确答案就在函数族里」；算法依然会发散：

""" + C_BAIRD + r"""

读输出：权重一开始最大是 10（初值）。前 100 步几乎没变化（9.98），到第 1000 步增长到 344.7，第 5000 步是 $9.049\times10^{6}$，第 10000 步是 $7.536\times10^{11}$，**指数级爆炸**。注意这里没有噪声，奖励恒为 0，纯粹是更新规则本身不稳定。

DQN 用的正是 Q-learning（自举 + 离策略）加神经网络（函数逼近），三要素齐全，所以下面两个技巧不是装饰。

### DQN：两个让它稳定下来的技巧

> **标准定义 · DQN 与它的两个技巧 (Deep Q-Network)**
>
> 用神经网络 $Q(s,a;\mathbf w)$ 逼近最优动作价值。每次从**经验回放缓冲区 (replay buffer)** 里随机抽一小批历史转移 $(s,a,r,s',\text{done})$，用 **TD 目标**
>
> $$y=r+\gamma\,(1-\text{done})\max_{a'}Q(s',a';\mathbf w^-)$$
>
> 做监督式回归，最小化 $\big(y-Q(s,a;\mathbf w)\big)^2$（常换成 Huber 损失）。其中 $\mathbf w^-$ 是**目标网络 (target network)** 的参数，每隔若干步才从在线网络 $\mathbf w$ 复制一次，其余时间保持不变。
>
> *English: DQN fits a neural Q-function by regression toward a TD target, using experience replay to sample past transitions at random and a periodically-updated target network to compute the bootstrapped target (Mnih et al., 2015).*

**白话版：「抽卡复习 + 冻结的标准答案」。** 经验回放像把所有做过的题放进一个盒子随机抽着复习：连续几步的数据高度相关（都是同一个房间里的画面），如果按顺序学，网络会被最近的一小段经验带偏；随机抽能打散相关性，而且每条经验可以反复用，更省数据。目标网络像一份冻结的标准答案：如果答案 $y$ 和正在训练的网络用同一份参数，每改一步参数，答案也跟着动，网络是在追着自己的影子跑；每隔 100~10000 步才更新一次答案，回归问题在这段时间里是稳定的。

先用 NumPy 和一个很小的环境把整套流程跑通。环境是 0 到 1 的连续数轴，从 0.5 出发，向右走到 1 得 $+1$、每步罚 $0.01$。Q 函数用 11 个径向基特征加线性权重（没有隐藏层，但流程和神经网络版本完全一样），同时对比「两个技巧都关掉」的版本：

""" + C_DQN + r"""

读输出：最优做法是一路向右 10 步，回报是 $9\times(-0.01)+1=0.91$，加上噪声，平均约 0.905。第 500 步时，两种设置的贪心策略平均回报都是 $-0.6$（60 步没走出去，$60\times(-0.01)$）；到第 1000 步就都是 0.905，并一直保持到第 6000 步。**这个玩具问题里，技巧关掉也一样学得会，这是诚实的结果**：环境只有一维、特征是线性的，数据的相关性和目标漂移都不严重。这两个技巧是为「高维图像输入、深层非线性网络、长时间的相关数据流」准备的（Atari 上的 DQN 就是这种情况，S&B 第 16.5 节有介绍）；上面的 Baird 反例才是不加保护时真实会出的事。

最后一行是训练后 $Q(x,\text{右})-Q(x,\text{左})$：在 $x=0.3,0.5,0.7,0.9$ 都是正的（0.067、0.257、0.094、0.087），说明「向右」更好；在 $x=0.1$ 是 $-0.002$，因为从 0.5 出发的智能体几乎不去那里，数据少，估计不可靠。这也是函数逼近的常见现象：**没访问过的地方估计是不可信的**。

同一个环境的 PyTorch 版本，把线性函数换成两层隐藏层的网络，并写出 DQN 更新中最关键的几行：

""" + C_TDQN + r"""

读输出：和 NumPy 版一致，第 500 步还没学会（$-0.6$），第 1000 步以后贪心策略的平均回报稳定在 0.904~0.906。三处值得记住的写法：`target(...)` 放在 `torch.no_grad()` 里，因为 TD 目标要当常数；`gather` 取出「实际做过的那个动作」的 Q 值；每 200 步 `load_state_dict` 同步一次目标网络。
"""),
  V("x83WmvbRa2I", "视频一：Deep Q-Networks Explained!（CodeEmporium）", 11),
  T(r"""
### 策略梯度：直接对策略求导

DQN 是「先学价值，再取 $\arg\max$ 得到策略」。这条路有局限：动作连续时 $\max_a$ 本身就是个优化问题；$\arg\max$ 给出的是确定性策略，没法自然地表达「在这个状态下 70% 向左 30% 向右」。**策略梯度**换了一条路：把策略本身参数化成 $\pi_\theta(a\mid s)$（例如神经网络输出的 softmax），直接对「期望回报」做梯度上升。

> **标准定义 · 策略梯度定理 (policy gradient theorem)**
>
> 设策略 $\pi_\theta$ 产生轨迹 $\tau=(s_0,a_0,r_0,s_1,\dots)$，目标是期望回报 $J(\theta)=\mathbb E_{\tau\sim\pi_\theta}[R(\tau)]$。则
>
> $$\nabla_\theta J(\theta)=\mathbb E_{\tau\sim\pi_\theta}\Big[\sum_{t}\nabla_\theta\log\pi_\theta(a_t\mid s_t)\,G_t\Big],\qquad G_t=\sum_{k\ge t}\gamma^{k-t}r_k$$
>
> 其中 $\nabla_\theta\log\pi_\theta(a\mid s)$ 叫**评分函数 (score function)**。右边只含策略的对数梯度和采到的回报，**不含环境的转移概率 $P(s'\mid s,a)$**。（严格推导里每一项还有一个 $\gamma^t$ 因子；实践中绝大多数实现把它省掉。）
>
> *English: The gradient of the expected return equals the expectation, over trajectories sampled from the policy, of the score function ∇log π(a_t|s_t) weighted by the return from time t onward. It does not involve the environment's transition probabilities.*

**白话版：「奖励高的动作，下次多做一点」。** 评分函数 $\nabla_\theta\log\pi(a\mid s)$ 指向「让动作 $a$ 在状态 $s$ 下更可能」的方向；乘上回报 $G_t$ 就是：回报高的，朝这个方向走得多；回报为负的，反方向走。定理保证这个「凭感觉的做法」恰好就是 $J$ 的真实梯度（期望意义下）。

**推导的思路**（五步，每一步只用一个想法）：

1. 一条轨迹的概率是 $p_\theta(\tau)=p(s_0)\prod_t\pi_\theta(a_t\mid s_t)\,P(s_{t+1}\mid s_t,a_t)$，策略和环境交替出现；
2. $J(\theta)=\sum_\tau p_\theta(\tau)R(\tau)$，对 $\theta$ 求导只有 $p_\theta$ 依赖 $\theta$，所以 $\nabla J=\sum_\tau\nabla p_\theta(\tau)\,R(\tau)$；
3. **对数导数技巧 (log-derivative trick)**：$\nabla p=p\,\nabla\log p$，于是 $\nabla J=\sum_\tau p_\theta(\tau)\,\nabla\log p_\theta(\tau)\,R(\tau)=\mathbb E_\tau[\nabla\log p_\theta(\tau)\,R(\tau)]$，**把求和重新变成了可以靠采样估计的期望**；
4. 取对数后乘积变求和：$\log p_\theta(\tau)=\log p(s_0)+\sum_t\log\pi_\theta(a_t\mid s_t)+\sum_t\log P(s_{t+1}\mid s_t,a_t)$，只有中间一项依赖 $\theta$，其余两项的梯度是 0，**环境的转移概率就这样消失了**，这是「无模型」的数学根源；
5. **因果性**：时刻 $k$ 的奖励 $r_k$ 不会被之后的动作 $a_t\,(t>k)$ 影响，而 $\mathbb E[\nabla\log\pi(a_t\mid s_t)\mid\text{过去}]=0$（见下面基线一节的证明），所以乘 $r_k$ 的那些项期望为 0，可以去掉，整条轨迹的回报 $R(\tau)$ 被换成「从 $t$ 开始的未来回报」$G_t$，方差更小。

下面在最简单的情形（一个状态、三个动作的老虎机）上把定理验证一遍：策略是 $\pi=\text{softmax}(\theta)$，此时 $\nabla_\theta\log\pi(a)=\mathbf e_a-\pi$（$\mathbf e_a$ 是独热向量），而 $J=\sum_i\pi_i\mu_i$ 的精确梯度是 $\pi_i(\mu_i-J)$，可以用三种办法算，互相对拍：

""" + C_SCORE + r"""

读输出：$\pi=(0.5065,0.3072,0.1863)$，$J=10.3399$。**精确梯度**是 $(-0.1722,0.0492,0.123)$：平均奖励 10.5、11.0 的两个臂比 $J$ 高，梯度为正，鼓励它们；10.0 的臂比 $J$ 低，被压低。**有限差分**给出完全相同的四位数，说明精确公式写对了。**评分函数的蒙特卡洛估计**（20 万个样本）是 $(-0.1534,0.0531,0.1003)$，和精确值的差在 1~2.5 个标准误（0.0116、0.0108、0.0094）之内，没有系统性偏差，只是有采样噪声。最后一行 $\mathbb E[\text{score}]\approx(0.0018,0.0003,-0.0021)$，接近 0，下一节的基线就靠它。
"""),
  V("5P7I-xPq8u8", "视频二：An introduction to Policy Gradient methods - Deep Reinforcement Learning（Arxiv Insights）", 20),
  T(r"""
### REINFORCE：最朴素的策略梯度算法

> **标准定义 · REINFORCE（蒙特卡洛策略梯度）**
>
> 重复：①用当前策略采样一个完整回合；②对回合中每个时刻 $t$ 计算未来回报 $G_t$；③沿梯度估计的方向更新：
>
> $$\theta\leftarrow\theta+\alpha\sum_t G_t\,\nabla_\theta\log\pi_\theta(a_t\mid s_t)$$
>
> 这是对策略梯度定理右边的单样本蒙特卡洛估计，无偏，但方差大（算法来自 Williams 1987、1992 年的工作；也见 Sutton & Barto 第 13.3 节）。
>
> *English: REINFORCE samples an episode, computes the return-to-go G_t at each step, and moves θ along G_t ∇log π(a_t|s_t). It is an unbiased but high-variance estimate of the policy gradient.*

**白话版：「打完一局，复盘每一步」。** 一局结束之后，对每一步问：这步之后我总共拿到多少分？分高，就把当时选的动作调大概率；分低，调小。没有价值函数，也没有环境模型。

用一个 4×4 的网格世界：从左上角出发，每走一步奖励 $-1$，右下角是终点，撞墙原地不动，最多 40 步。**策略是表格式的 softmax**：每个状态 4 个 logit（上下左右）。最短路径是 6 步：

""" + C_REINFORCE + r"""

读输出：10 个种子的平均回合长度，开头的 50 个回合是 20.6（一边学一边走，随机策略大约会拖到 30 步左右，所以这里已经有进步），第 100~149 个回合是 8.6，第 250~299 个回合是 6.7，第 550~599 个回合是 6.3，接近最优的 6 步。种子 0 的贪心策略打印出来：沿着 $(0,0)\to(0,1)\to(1,1)\to(2,1)\to(3,1)\to(3,2)\to(3,3)$ 刚好 6 步，是一条最短路径。图上其他状态（比如第 2 行第 1 列的 ↑）几乎没被访问过，动作是随机残留，不用在意。

### 基线：不改变期望，却能大幅降低方差

REINFORCE 有个明显的毛病：这个网格里每一步的奖励都是 $-1$，$G_t$ **永远是负数**，所以每个被采样到的动作都被「压低」，只是差的压得多一点；一个回报全是正数的任务里则是每个被采到的动作都被「鼓励」。梯度的方向主要靠相对大小，而这种「整体偏移」只增加噪声。解法：减去一个**基线**。

> **标准定义 · 基线 (baseline)**
>
> 把 $G_t$ 换成 $G_t-b(s_t)$，其中 $b$ 只依赖状态、**不依赖动作**。梯度估计的期望不变：
>
> $$\mathbb E_{a\sim\pi}\big[\nabla_\theta\log\pi_\theta(a\mid s)\,b(s)\big]=b(s)\sum_a\nabla_\theta\pi_\theta(a\mid s)=b(s)\,\nabla_\theta\!\sum_a\pi_\theta(a\mid s)=b(s)\,\nabla_\theta 1=0$$
>
> 但方差可以大幅下降。常用基线是状态价值 $V^\pi(s)$，此时 $G_t-V^\pi(s_t)$ 估计的是**优势 (advantage)** $A(s_t,a_t)=Q(s_t,a_t)-V(s_t)$：这个动作比这个状态下的平均水平好多少。
>
> *English: Subtracting any action-independent baseline b(s) leaves the expected policy gradient unchanged (because E[∇log π] = 0) but can greatly reduce its variance. With b = V(s) the weight becomes an estimate of the advantage.*

**白话版：「和平均水平比，而不是和 0 比」。** 考试得 85 分，如果全班平均是 90，这是坏消息；如果平均是 60，是好消息。只看 85 这个绝对数字会误导你，应该看它和平均的差。基线就是那个「平均」。

先在老虎机上量化方差。三个臂的平均奖励 $10,10.5,11$（刻意取成都很大、彼此差得很少的正数，这是方差问题最严重的情形），对比三种基线：

""" + C_VAR + r"""

读输出：三种基线的**均值**都收敛到同一个梯度：$b=0$ 的 $(-0.153,0.053,0.1)$ 有一点采样噪声，$b=J$ 和 $b^*$ 的 $(-0.172,0.05,0.122)$ 与精确梯度 $(-0.172,0.049,0.123)$ 一致，**期望没变**。但**总方差**从 68.247 降到 0.677，降低约 100 倍；最优常数基线 $b^*=10.498$（正好在平均奖励附近）只比 $b=J$ 再低一点点，是 0.662。工程上不用算 $b^*$，用平均回报或 $V(s)$ 就够好。

方差小有什么实际用处？用同样的老虎机（四个臂 $10,10.5,11,12$），让策略真的学起来：

""" + C_BANDIT + r"""

读输出：30 个种子，每个训练 2000 步。**无基线**：最优臂的概率平均到第 500 步是 0.652，第 2000 步是 0.854，而且有 4 个种子到 2000 步仍低于 0.5，学偏或学得很慢；**有基线**（用奖励的滑动平均）第 500 步就是 0.88，第 2000 步是 0.984，没有一个种子低于 0.5。注意第 100 步两者几乎一样（0.427 对 0.429），差别在于之后的噪声累积，无基线的轨迹被噪声推着走。

PyTorch 里同一个算法只有几行，**写法和上面的公式一一对应**：

""" + C_TPG + r"""

读输出：4 个臂最初几乎等概率（0.243~0.259），第 100 步最优臂是 0.402，第 500 步是 0.89，第 2000 步是 0.983。三个细节：`adv` 要 `.detach()`，因为优势是权重，不是要求导的量；`loss` 前面有个负号，因为优化器做最小化；`dist.sample` 本身不产生梯度，梯度全部来自 `log_prob`，这正是 REINFORCE「采样不可导，所以用评分函数」的体现。

### Actor-critic：把「回报」也换成估计

REINFORCE 要等一个回合结束才更新，而且 $G_t$ 是很多个随机奖励的累加，噪声大。**Actor-critic** 同时学两个东西：**actor（演员）**是策略 $\pi_\theta$，**critic（评论家）**是价值函数 $V_w$。用 critic 的估计给每一步打分：

> **标准定义 · TD 优势与 actor-critic**
>
> 用 **TD 误差**当作优势的估计：
>
> $$\delta_t=r_t+\gamma V_w(s_{t+1})-V_w(s_t)$$
>
> actor 沿 $\delta_t\,\nabla_\theta\log\pi_\theta(a_t\mid s_t)$ 更新，critic 把 $V_w(s_t)$ 往 $r_t+\gamma V_w(s_{t+1})$ 推。若 $V_w$ 恰好等于真实的 $V^\pi$，则 $\mathbb E[\delta_t\mid s_t,a_t]=A^\pi(s_t,a_t)$；实际中 $V_w$ 不准，估计有**偏差**，换来**更低的方差**，并且每一步都能更新。广义优势估计 **GAE** 用参数 $\lambda\in[0,1]$ 把 $\delta_t$ 按 $(\gamma\lambda)^l$ 加权相加，在两端（$\lambda=0$ 是单步 TD，$\lambda=1$ 是蒙特卡洛回报减去价值）之间平滑过渡（Schulman 等，2015）。
>
> *English: Actor-critic uses a learned value function to form low-variance advantage estimates such as the TD error. This trades some bias for lower variance and allows per-step updates; GAE interpolates between TD and Monte-Carlo estimates.*

**白话版：「不等期末考，每次小测就打分」。** REINFORCE 等整局结束才知道好坏；actor-critic 让 critic 在每一步给出「这一步比预期好还是差」，actor 立刻调整。

下面在同一个网格上，把 REINFORCE、带基线（用学出来的 $V(s)$）的 REINFORCE、单步 actor-critic 放在一起，并且对比三个学习率（每格是最后 50 个回合的平均回合长度，10 个种子，6 为最优）：

""" + C_GRID + r"""

读输出，诚实地看：学习率 0.01 和 0.02 时，三种方法都能学到接近最优（6.3~7.1），**在这个小问题上基线和 critic 没有带来决定性的好处**。差别出现在 0.05：REINFORCE 卡在 23.2，带基线的 16.3，而 actor-critic 仍是 6.2。一个合理的解释是，更新的步长正比于「权重」的大小：REINFORCE 的权重是 $G_t$，绝对值可达几十，学习率一大，一次更新就把某些状态的策略推到接近确定，之后几乎不再探索，被困在差的路线上；基线把权重缩小了一部分，所以好一些；TD 误差 $\delta_t$ 的量级通常在 1 左右，更新温和得多。**方差小的价值，往往体现为对学习率更不敏感、更稳定**，这是深度强化学习里它们被默认使用的原因。

### PPO：不要一步迈太大

策略梯度有一个麻烦：每次更新用的数据是「当前策略」采出来的，更新一次就得重新采样，非常浪费。想用同一批数据多做几步梯度，就得处理「策略已经变了」。**重要性比率** $r_t(\theta)=\pi_\theta(a_t\mid s_t)/\pi_{\theta_\text{old}}(a_t\mid s_t)$ 可以修正数据来源的差异，但如果策略变化太大，修正就不再可靠。PPO 的办法很简单：把比率限制在 $1$ 附近。

> **标准定义 · PPO 的裁剪目标 (clipped surrogate objective)**
>
> $$L^{\text{CLIP}}(\theta)=\mathbb E_t\Big[\min\big(r_t(\theta)\hat A_t,\ \text{clip}(r_t(\theta),1-\epsilon,1+\epsilon)\,\hat A_t\big)\Big]$$
>
> $\epsilon$ 是超参数，原论文里取 $\epsilon=0.2$。当 $\hat A_t>0$ 时，比率超过 $1+\epsilon$ 后目标不再增加，梯度为 0；当 $\hat A_t<0$ 时，比率低于 $1-\epsilon$ 后目标不再下降。实际实现里还会加上价值函数的损失和熵奖励，并对同一批数据做几轮小批量更新（Schulman 等，2017）。
>
> *English: PPO maximizes a surrogate in which the probability ratio is clipped to [1−ε, 1+ε], removing the incentive to move the policy far from the one that collected the data, so the same batch can be reused for several gradient steps.*

**白话版：「改进可以，但别一次改太多」。** 一个动作被证明很好（$\hat A>0$），就提高它的概率，但提到旧概率的 1.2 倍就够了，再提也不再给奖励；一个动作被证明很差，就降低它，降到旧概率的 0.8 倍就够了。

""" + C_PPO + r"""

读输出，先看表格：$A=+1$ 时目标是 $\min(r,\text{clip}(r))$，$r$ 从 1 涨到 1.2 目标跟着涨，涨到 1.5、2.0 时**目标停在 1.200**，不再有动力继续提高概率；$A=-1$ 时 $r$ 降到 0.8 以下目标停在 $-0.800$，而 $r=1.5,2.0$ 时目标继续下降到 $-1.5,-2.0$：最小值里的 `min` 保证了「错得离谱时仍然受惩罚」，只对**乐观的方向**裁剪。再看后面的实验：同一批 64 个样本，反复做梯度上升。**无裁剪**：第 10 步 $\max|r-1|=0.119$，第 50 步 0.645，第 300 步 1.79，KL（旧到新）涨到 1.1907，新策略变成 $(0.025,0.045,0.93)$，几乎把所有概率押在一个动作上，这是在一批只有 64 个带噪样本的数据上过拟合。**有裁剪**：第 50 步 0.206，第 300 步 0.204，KL 稳定在 0.0141，新策略 $(0.266,0.333,0.401)$，只是小步调整。注意 0.204 略大于 0.2：裁剪**不是硬约束**，只是让越界样本不再贡献梯度，所以 PPO 的「信任区域」是近似的。

### 与 RLHF 的联系

**RLHF（基于人类反馈的强化学习）** 把上面这一套原封不动地用在语言模型上。以 InstructGPT（Ouyang 等，2022）的做法为例：①用人写的示范做监督微调得到 SFT 模型；②用人对多个回答的偏好排序训练一个**奖励模型**；③把「生成一个回答」看成一个只有一步的老虎机环境：策略就是语言模型，动作是整个回答，奖励来自奖励模型，用 **PPO** 优化。论文里还加了**每个 token 相对于 SFT 模型的 KL 惩罚**，用来缓解对奖励模型的过度优化，价值函数用奖励模型初始化。

> **标准定义 · KL 正则化的 RLHF 目标**
>
> $$\max_\pi\ \mathbb E_{a\sim\pi}\big[r(a)\big]-\beta\,D_{KL}\big(\pi\,\|\,\pi_{\text{ref}}\big)$$
>
> $\pi_{\text{ref}}$ 是参考策略（SFT 模型），$\beta>0$ 控制「拴得多紧」。在一步（老虎机）情形下，最优策略有闭式解 $\pi^*(a)\propto\pi_{\text{ref}}(a)\exp\big(r(a)/\beta\big)$：参考策略按奖励做指数倾斜。
>
> *English: KL-regularized reward maximization keeps the policy close to a reference model. In the one-step case, the optimum is the reference distribution re-weighted by exp(r/β).*

**白话版：「可以朝高分走，但要拴着一根绳子」。** 奖励模型本身只是一个会犯错的打分器；如果完全追着它的分数跑，策略会学会钻它的空子。KL 项就是这根绳子，$\beta$ 越小绳子越松。这里的 KL 正是 ARENA 信息论一节里的 KL 散度。把四种回答的老虎机当作语言模型的玩具版，验证闭式解，并看 $\beta$ 的作用（参考策略下的平均奖励是 $0.5\times0+0.3\times1+0.15\times2+0.05\times3=0.75$）：

""" + C_RLHF + r"""

读输出：每一行里，用**梯度上升**得到的策略和**闭式解**一致（三位小数内基本相同，$\beta=0.3$ 时最小的两项只差 0.001）。看 $\beta$ 的作用：$\beta=10$ 时绳子很紧，策略几乎没动，$\mathbb E[r]=0.832$（参考是 0.75），KL 只有 0.004；$\beta=1$ 时 $\mathbb E[r]=1.763$，KL=0.531；$\beta=0.3$ 时 $\mathbb E[r]=2.888$，KL 涨到 2.514；$\beta=0.05$ 时策略几乎把全部概率放在奖励最高的回答上，$\mathbb E[r]=2.999$，KL=2.988。**奖励越高，付出的 KL 越大**，要选一个平衡点，这就是 RLHF 里 $\beta$ 的意义。

### 这一节你要带走的三句话

1. **函数逼近 + 自举 + 离策略可能发散（致命三角）**：DQN 用经验回放（打散相关性、复用数据）和目标网络（让回归目标暂时不动）把它稳住；
2. **策略梯度定理：$\nabla J=\mathbb E[\sum_t\nabla\log\pi(a_t\mid s_t)\,G_t]$**，来自对数导数技巧，环境的转移概率在求导时消失；减去与动作无关的基线不改变期望，却能大幅降低方差；actor-critic 用 TD 误差当优势，以一点偏差换更低方差；
3. **PPO 把概率比率裁剪在 $[1-\epsilon,1+\epsilon]$ 里，让同一批数据能安全地多用几步；RLHF 就是「策略 = 语言模型，奖励 = 奖励模型分数 − $\beta\cdot$KL」的 PPO**。
"""),
  THINK(r"一个 3 臂老虎机的策略是 $\pi=(0.5,0.3,0.2)$（softmax 的输出）。采样到第 3 个臂，奖励 $r=4$，基线 $b=1$。写出这一步的梯度估计 $g=(r-b)(\mathbf e_a-\pi)$，并说明更新后三个臂的概率各自往哪个方向变。如果 $r=0.5$ 会怎样？", r"""
$\mathbf e_a-\pi=(0,0,1)-(0.5,0.3,0.2)=(-0.5,-0.3,0.8)$，$r-b=3$，所以 $g=3\times(-0.5,-0.3,0.8)=(-1.5,-0.9,2.4)$。沿 $g$ 更新 logit：第 3 个臂的 logit 上升，前两个下降，第 3 个臂的概率变大，另外两个变小。三个分量加起来是 0，因为 softmax 对三个 logit 同时加同一个常数是不变的。

如果 $r=0.5$，$r-b=-0.5<0$，$g=-0.5\times(-0.5,-0.3,0.8)=(0.25,0.15,-0.4)$，方向反了：第 3 个臂的概率被压低。同一个动作，同一个策略，只因为它的回报比基线低，就从「鼓励」变成「抑制」。这就是基线的作用：决定的是**相对好坏**。
"""),
  THINK(r"为什么基线 $b(s)$ 不能依赖当前动作 $a_t$？请用 $\sum_a\nabla\pi(a\mid s)=0$ 解释，并说出如果让基线等于 $G_t$ 本身会发生什么。", r"""
基线不改变期望，靠的是 $b(s)$ 可以**提到求和号外面**：$\sum_a\pi(a\mid s)\,\nabla\log\pi(a\mid s)\,b(s)=b(s)\sum_a\nabla\pi(a\mid s)=b(s)\,\nabla\!\sum_a\pi(a\mid s)=0$。如果基线依赖动作，写成 $b(s,a)$，它就留在求和号里面，$\sum_a b(s,a)\nabla\pi(a\mid s)$ 一般不为 0，梯度估计就有了偏差。

若取 $b=G_t$，$G_t-b\equiv0$，整个梯度估计恒为 0，什么也学不到；它不是「不改变期望」，而是把真正的信号整个减掉了。要用依赖动作的量（例如 $Q(s,a)$）做控制变量，需要像某些方法那样再把它的期望加回来，才能保持无偏。
"""),
  THINK(r"**联系世界模型和 RLHF**：Dreamer 一类方法在学出来的世界模型想象出的轨迹里训练 actor-critic；RLHF 里的策略则是对着一个学出来的奖励模型优化。两种情形里，「被学出来的那个东西」有误差时，策略优化可能出现什么共同的问题？各自有什么缓解办法？", r"""
共同的问题是**策略会利用学出来的模型的漏洞**。策略优化就是在寻找「模型认为最好」的行为，而模型只在训练数据覆盖的地方可靠；策略很容易走到模型没见过的地方，那里的预测偏乐观、实际并不好，于是在模型里分数很高、在真实环境（或真实的人类偏好）下表现很差，也就是过度优化 (over-optimization)。

缓解办法各有侧重。RLHF：KL 惩罚把策略拴在参考模型附近（上面的 $\beta$），早停，或更新奖励模型。世界模型：只在较短的想象时间范围内用模型，用真实数据持续更新模型，用模型集成估计不确定性，别让策略走到模型不确定的地方。两边的思路都是：**限制策略离「模型可信的区域」有多远**，这也是第 7 节基于模型的强化学习要处理的核心问题。
"""),
  KW(("函数逼近","function approximation","用参数个数远少于状态数的函数近似价值，换取泛化"),
     ("致命三角","deadly triad","函数逼近 + 自举 + 离策略，三者同时出现可能发散"),
     ("DQN","Deep Q-Network","用神经网络做 Q-learning，配经验回放和目标网络"),
     ("经验回放","experience replay","把转移存进缓冲区随机抽样训练，打散相关性并复用数据"),
     ("目标网络","target network","周期性才同步的冻结参数副本，用来计算 TD 目标"),
     ("策略梯度定理","policy gradient theorem","$\\nabla J=\\mathbb E[\\nabla\\log\\pi\\cdot G]$，环境转移概率不出现"),
     ("评分函数","score function","$\\nabla_\\theta\\log\\pi_\\theta(a|s)$，让动作更可能的方向"),
     ("对数导数技巧","log-derivative trick","$\\nabla p=p\\nabla\\log p$，把求和变成可采样的期望"),
     ("REINFORCE","REINFORCE","蒙特卡洛策略梯度，无偏但方差大"),
     ("基线","baseline","与动作无关的量，减掉它不改变期望，能降方差"),
     ("优势函数","advantage function","$A=Q-V$，这个动作比平均水平好多少"),
     ("行动者-评论者","actor-critic","actor 是策略，critic 是价值函数，用 TD 误差做优势"),
     ("广义优势估计","GAE (Generalized Advantage Estimation)","用 $\\lambda$ 在 TD 与蒙特卡洛优势之间折中"),
     ("近端策略优化","PPO (Proximal Policy Optimization)","把概率比率裁剪在 $[1-\\epsilon,1+\\epsilon]$ 内的策略梯度方法"),
     ("基于人类反馈的强化学习","RLHF","策略是语言模型，奖励来自奖励模型，并用 KL 惩罚拴住参考模型"),
  ),
 ],
 "references": [
  {"title": "Sutton & Barto《Reinforcement Learning: An Introduction》（第 2 版，MIT Press，2018）— 第 9 章、第 11.3 节、第 13 章", "url": "http://incompleteideas.net/book/the-book-2nd.html", "note": "本节依据的开放教材（作者免费公开 PDF）：第 9 章函数逼近、第 11.3 节致命三角、第 13.1~13.5 节策略逼近 / 策略梯度定理 / REINFORCE / 基线 / actor-critic、第 16.5 节 DQN 案例（讲解为自写，未转载原文）"},
  {"title": "Mnih 等《Human-level control through deep reinforcement learning》（Nature 518, 529–533, 2015）", "url": "https://www.nature.com/articles/nature14236", "note": "DQN 的正式论文；经验回放与目标网络的出处"},
  {"title": "Schulman 等《Proximal Policy Optimization Algorithms》（arXiv:1707.06347，2017）", "url": "https://arxiv.org/abs/1707.06347", "note": "PPO 原论文，裁剪目标在第 3 节；GAE 见 arXiv:1506.02438"},
  {"title": "OpenAI Spinning Up：Intro to Policy Optimization", "url": "https://spinningup.openai.com/en/latest/spinningup/rl_intro3.html", "note": "策略梯度的另一份推导，含「奖励到达 (reward-to-go)」与基线两节，可对照本节的推导"},
  {"title": "Ouyang 等《Training language models to follow instructions with human feedback》（arXiv:2203.02155，2022）", "url": "https://arxiv.org/abs/2203.02155", "note": "InstructGPT：RLHF 的三步流程，PPO 与逐 token 的 KL 惩罚，选看"},
 ],
 "quiz": {"questions": QUIZ},
}

TARGET = [1, 3, 0, 2, 3, 1, 0, 2, 1, 0]
for q, t in zip(unit["quiz"]["questions"], TARGET):
    q["options"][q["answer"]], q["options"][t] = q["options"][t], q["options"][q["answer"]]
    q["answer"] = t

if __name__ == '__main__':
    dump(unit, "wm-0", "u04-policy-gradient.json")
