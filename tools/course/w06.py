"""wm-0 第 6 节：序列与状态空间模型（v3 格式）"""
from unitlib import *
from w06c import C_RING, C_RING2, C_HMM, C_KF1, C_KF2, C_GRU, C_RES, C_LAT
from w06_quiz import QUIZ

unit = {
 "id": "u06",
 "title": "序列与状态空间模型",
 "en": "Sequence & State-space Models",
 "minutes": 100,
 "objectives": [
  "分清 **观测 (observation)** 与 **状态 (state)**，理解 **部分可观测 (partial observability)** 为什么让「只看当前观测」不够，会写出 **状态空间模型 (state-space model)** 的两个条件分布 $p(z_{t+1}\\mid z_t,a_t)$ 和 $p(o_t\\mid z_t)$",
  "理解 **信念 (belief)** $p(z_t\\mid o_{1:t},a_{1:t-1})$ 与 **贝叶斯滤波 (Bayes filter)** 的「预测 + 更新」两步，知道 POMDP 的信念是历史的充分统计量",
  "会写 **隐马尔可夫模型 (HMM)** 的 **前向算法 (forward algorithm)**，说清它为什么是 $O(TK^2)$、归一化之后就是滤波，并用 NumPy 对拍暴力枚举",
  "会推导并实现线性高斯情形的 **卡尔曼滤波 (Kalman filter)**：预测步方差增大、更新步按增益修正，理解卡尔曼增益是「相信观测的程度」",
  "能手算一步 **GRU**，理解 RNN 的隐状态是一种 **学出来的信念 (learned belief)**，并能说出 **潜在动力学模型 (latent dynamics model)** 与后面 Dreamer 的 RSSM 的关系",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

前面几节里，智能体看到的 $s_t$ 就是世界的真实状态：MDP 假设「当前状态包含做决定所需的全部信息」。现实里几乎没有这样的好事。摄像头只拍到一帧图像，看不到物体的速度；机械臂的传感器有噪声；游戏里敌人躲在墙后面。智能体拿到的是**观测 (observation)**，世界真正的状态藏在背后。

**这一节和世界模型的关系**：世界模型要做的事，就是从一串观测和动作里，学出一个紧凑的**潜在状态 (latent state)** $z_t$，再学出这个状态怎么随动作演化。这一节把「从历史推断隐藏状态」这件事讲清楚，用的是三个经典工具：HMM（离散状态）、卡尔曼滤波（连续线性高斯状态）、RNN/GRU（学出来的、不再有显式概率解释的状态）。后面的 PlaNet、Dreamer 里的 RSSM，本质上是把这三条线接在一起：一部分是 RNN 的确定性记忆，一部分是潜变量的随机性，训练目标是上一节的 ELBO。

**学完它你就能看懂这几件事：**

- 为什么 Atari 里的 DQN 要把最近 4 帧叠在一起当输入，而 Dreamer 这类方法要给模型加一个循环的隐状态；
- 论文里常见的「filtering」「belief state」「posterior $q(z_t\mid o_{\le t},a_{<t})$」各自指什么；
- 卡尔曼滤波里「预测 + 更新」和 GRU 里「门控保留 + 候选覆盖」为什么是同一类思想；
- Dreamer 论文里「representation model / transition model」的区别：前者是滤波（看了观测），后者是预测（没看观测）。

**本节安排（约 100 分钟）**：观测、状态与信念（15 分钟，含走廊实验）→ HMM 与前向算法（12 分钟 + 视频 11 分钟）→ 卡尔曼滤波（15 分钟 + 视频 11 分钟）→ RNN/GRU 的隐状态（12 分钟 + 视频 9 分钟）→ 潜在动力学模型（10 分钟）→「想一想」。视频是英文的，可以打开 YouTube 的中文字幕。

### 观测、状态与信念

> **标准定义 · 状态空间模型 (state-space model)**
>
> 一个**状态空间模型**由隐藏状态序列 $z_1,z_2,\dots$ 和观测序列 $o_1,o_2,\dots$ 组成，包含两个条件分布：
>
> $$z_{t+1}\sim p(z_{t+1}\mid z_t,a_t)\quad(\text{转移 / 动力学}),\qquad o_t\sim p(o_t\mid z_t)\quad(\text{观测 / 发射})$$
>
> 其中 $a_t$ 是智能体的动作（没有动作时就是普通的 HMM 或卡尔曼模型）。关键假设：$z_t$ 是**马尔可夫**的，也就是给定 $z_t$，未来与过去无关；而 $o_t$ 只依赖当前的 $z_t$。**状态是看不见的，我们只能看到观测。**
>
> *English: A state-space model has a hidden Markov state z_t evolving under p(z_{t+1} | z_t, a_t) and emitting observations o_t ~ p(o_t | z_t). The state is never observed directly.*

**白话版：「透过毛玻璃看一个人走路」。** 你看不清人在哪，只能看到模糊的影子（观测）；但如果你知道他走路的习惯（转移）和玻璃怎么模糊的（发射），连续看几秒钟，就能比只看一眼猜得准得多。

> **标准定义 · 信念与贝叶斯滤波 (belief & Bayes filter)**
>
> 智能体在时刻 $t$ 对隐藏状态的**信念**是给定全部历史后的后验分布：
>
> $$b_t(z)=p(z_t=z\mid o_{1:t},a_{1:t-1})$$
>
> 信念可以递推地更新，每一步分成两半。**预测 (predict)**：用动力学把信念往前推一步（还没看新观测）；**更新 (update)**：用新观测的似然修正（贝叶斯公式）：
>
> $$\bar b_{t+1}(z')=\sum_z p(z'\mid z,a_t)\,b_t(z),\qquad b_{t+1}(z')=\frac{p(o_{t+1}\mid z')\,\bar b_{t+1}(z')}{\sum_{z''}p(o_{t+1}\mid z'')\,\bar b_{t+1}(z'')}$$
>
> 在**部分可观测马尔可夫决策过程 (POMDP)** 里，信念 $b_t$ 是历史的**充分统计量**：最优决策只需要 $b_t$，不需要记住整段历史。把信念当作新的「状态」，POMDP 就变成了一个（连续状态的）MDP。
>
> *English: The belief b_t is the posterior over the hidden state given the history. The Bayes filter updates it recursively with a predict step (push through the dynamics) and an update step (reweight by the observation likelihood). In a POMDP the belief is a sufficient statistic of the history.*

**白话版：「侦探的脑子」。** 侦探不会每次破案都从头重读所有案卷，他心里始终有一个「目前嫌疑人的概率分布」，来了新线索就更新一下。信念就是这个不断更新的分布，它把任意长的历史压缩成固定大小的东西。

下面做一个小实验：一个环形走廊有 8 个格子，格子 0、3、5 有门，机器人只能看到当前格子是门还是墙（准确率 90%），动作永远是「向右走」，但会打滑。它看不见自己在哪格，只能靠滤波。

""" + C_RING + r"""

读输出：

- **只看一次观测是不够的**：最后一行显示，看到「门」之后，在三扇门的格子（0、3、5）各是 0.281，其余五个墙格各是 0.031。三扇门长得一样，所以单看一次观测，最好也只能在三个候选里猜（这叫**感知混淆**）。
- 第 0 步：均匀信念的熵是 3 比特，看到门之后降到 2.325 比特，但最大概率只有 0.281，因为有三扇门（最大格 0 只是并列时取了第一个）。
- 第 2 步：真实格子是 2（墙），传感器偶然读成了「门」，信念最大的格子跑到了 5，概率 0.491，**滤波也会被错误的观测带偏**；之后几步信念又慢慢回到真实位置附近（第 5 到第 7 步又都对上了）。
- 第 8 步：机器人在第 8 步滑动了 2 格，真实格子是 1，而信念还在 7 附近，说明动作的不确定性（打滑）会让熵重新上升（从 2.077 升到 2.705 比特）。**信念的熵不是一路下降的**，新的随机性（转移噪声、传感器噪声）会让它回升。

这一次运行只是一条轨迹。更可靠的做法是重复很多次，比较「用整段历史」和「只看最后一次观测」：

""" + C_RING2 + r"""

读输出：重复 2000 次、每次走 12 步，用贝叶斯滤波的信念猜格子，猜对的比例是 0.4855；只看最后一次观测，只有 0.2305。两者相差一倍多，这就是「记忆」的价值。而且这里的传感器已经有 90% 准确，打滑又让位置不断变化，所以即使是最优滤波，也只能猜对约一半，这是问题本身的不确定性，不是算法的缺陷。
"""),
  T(r"""
### 隐马尔可夫模型与前向算法

> **标准定义 · 隐马尔可夫模型与前向算法 (HMM & forward algorithm)**
>
> **隐马尔可夫模型 (HMM)** 是隐状态取有限个值（$K$ 个）、没有动作的状态空间模型，由三部分确定：初始分布 $\pi_i=P(z_1=i)$，转移矩阵 $A_{ij}=P(z_{t+1}=j\mid z_t=i)$，发射矩阵 $B_{ik}=P(o_t=k\mid z_t=i)$。**前向变量**定义为
>
> $$\alpha_t(j)=P(o_{1:t},\,z_t=j),\qquad \alpha_1(j)=\pi_jB_{j,o_1},\qquad \alpha_{t+1}(j)=\Big[\sum_i\alpha_t(i)A_{ij}\Big]B_{j,o_{t+1}}$$
>
> 整段观测的概率是 $P(o_{1:T})=\sum_j\alpha_T(j)$，时间复杂度 $O(TK^2)$；把每一步的 $\alpha_t$ 除以它的和，就得到**滤波分布** $P(z_t\mid o_{1:t})$。
>
> *English: The forward algorithm computes α_t(j) = P(o_1..t, z_t = j) by dynamic programming in O(T K^2); normalizing α_t gives the filtering distribution P(z_t | o_1..t).*

**白话版：「天气预报员记账」。** 路径有 $K^T$ 条，一条条枚举不现实。前向算法的窍门是：每天只记「到今天为止，各种天气的账面概率」，明天的账只依赖今天的账。其实它就是上一节的**预测（乘 $A$）+ 更新（乘发射概率）**，只不过没有归一化。归一化之后，每一步的结果就是信念。

""" + C_HMM + r"""

读输出：

- 6 天的观测序列概率是 0.010615，前向算法与 64 条路径暴力枚举完全一致，这是动态规划正确的随机对拍（枚举 64 条路径，前向每一步只做 $K^2=4$ 次乘加）。
- 滤波信念：第 1 天看到带伞，下雨的概率是 0.8182；第 2 天又带伞，升到 0.8912；第 3 天没带伞，一下掉到 0.2005；第 6 天连续没带伞，晴天的概率升到 0.9058。每一次信念都同时综合了「天气自己的惯性」和「观测的证据」。
- **数值陷阱**：序列长到 3000 步，不归一化的 $\alpha$ 连乘得到 0.0（浮点数下溢），但每步归一化、把缩放系数的对数累加，得到对数似然 $-2141.53$，完全可用。实际代码总是这样做（或者全程在对数空间里算）。
"""),
  V("9-sPm4CfcD0", "视频一：Forward Algorithm Clearly Explained | Hidden Markov Model Part 6（Normalized Nerd）", 11),
  T(r"""
### 卡尔曼滤波：连续状态下的贝叶斯滤波

> **标准定义 · 卡尔曼滤波 (Kalman filter)**
>
> 若转移和观测都是**线性**的、噪声都是**高斯**的：
>
> $$z_{t+1}=Az_t+Ba_t+w_t,\ w_t\sim\mathcal N(0,Q),\qquad o_t=Hz_t+v_t,\ v_t\sim\mathcal N(0,R)$$
>
> 那么信念永远是高斯 $b_t=\mathcal N(m_t,P_t)$，只需维护均值和协方差。**预测**：$m^-=Am+Ba,\ P^-=APA^\top+Q$。**更新**：新息 $y=o-Hm^-$，增益 $K=P^-H^\top(HP^-H^\top+R)^{-1}$，$m=m^-+Ky$，$P=(I-KH)P^-$。
>
> *English: For linear dynamics with Gaussian noise, the belief stays Gaussian. The Kalman filter alternates a predict step (propagate mean and covariance through the dynamics, adding process noise) and an update step (correct by the Kalman gain times the innovation).*

**白话版：「一边猜、一边被现实拉一下」。** 预测步：我根据运动规律猜你下一刻在哪，但猜得越远越没把握（方差变大）。更新步：新测量来了，我把「我的猜测」和「测量值」按各自的可信度加权平均：谁更不确定，谁的权重就小。**卡尔曼增益 $K$ 就是「相信新测量多少」**，介于 0 和 1 之间（标量情形）。

先看最简单的一维情形：隐藏状态做随机游走，只能看到带噪声的测量。

""" + C_KF1 + r"""

读输出：

- 误差：直接用观测当估计，RMSE 是 0.93（就是观测噪声的标准差附近，$\sqrt1=1$）；卡尔曼滤波降到 0.4164；窗口 5 的滑动平均是 0.4507，比卡尔曼差。**卡尔曼滤波知道动力学噪声 $q$ 和观测噪声 $r$ 的大小，所以能给出最优的加权**，滑动平均只是凭经验平均。
- 卡尔曼增益：第 1 步是 0.910（初始方差 10，几乎完全相信观测），第 2 步 0.490，第 50 步 0.200，第 300 步还是 0.200：增益很快收敛到一个稳态值。稳态后验方差 0.2，也和理论解（预测方差 0.25，增益 0.2，后验方差 0.2）一致。
- 最后两行是对拍：先验 $\mathcal N(2,4)$，观测 5，$r=1$，卡尔曼更新给出均值 4.4、方差 0.8，和「按精度（方差的倒数）加权的两个高斯相乘」完全一致。**卡尔曼更新就是贝叶斯公式在高斯下的闭式解。**

再看一个更像「世界模型」的例子：状态是**位置和速度**，我们能控制加速度，但只能观测到带很大噪声的位置，速度根本没人告诉我们。

""" + C_KF2 + r"""

读输出：位置的 RMSE 从观测的 1.905 降到 1.09；更惊人的是**速度**，从未被直接观测，用相邻观测做差分得到的估计 RMSE 是 2.686，卡尔曼滤波只有 0.301。原因是滤波器**知道位置和速度的联系**（$A$ 矩阵）和已知的动作（$B$ 矩阵），所以位置的一连串观测就带来了速度的信息。这就是「状态」的意义：它是比观测更本质的、被动力学连在一起的量，可以从观测里被推断出来。稳态后验协方差的对角线是（位置 1.513，速度 0.074）。
"""),
  V("IFeCIbljreY", "视频二：Visually Explained: Kalman Filters（Visually Explained）", 11),
  T(r"""
### RNN / GRU 的隐状态：学出来的信念

HMM 和卡尔曼滤波有一个共同的前提：你得**事先知道**模型（$A,B,Q,R$）。现实里这些通常未知，状态可能是一张图像背后的物体位置，没有任何公式。深度学习的做法是放弃显式的概率解释，用循环神经网络 (RNN) 把历史压进一个向量 $h_t$：

$$h_t=f_\theta(h_{t-1},x_t)$$

这和滤波的结构完全相同：「旧的信念 + 新的输入 → 新的信念」。普通 RNN 在长序列上有梯度消失的问题，**GRU** 用门控解决：

> **标准定义 · 门控循环单元 (GRU)**
>
> 输入 $x_t$、上一步隐状态 $h_{t-1}$，GRU 先算两个门（$\sigma$ 是 sigmoid），再算候选状态，最后加权混合（这里采用 PyTorch 的约定）：
>
> $$z_t=\sigma(W_zx_t+U_zh_{t-1}+b_z),\qquad r_t=\sigma(W_rx_t+U_rh_{t-1}+b_r)$$
>
> $$n_t=\tanh\big(W_nx_t+U_n(r_t\odot h_{t-1})+b_n\big),\qquad h_t=(1-z_t)\odot n_t+z_t\odot h_{t-1}$$
>
> **更新门** $z_t$ 越接近 1，越保留旧状态；**重置门** $r_t$ 决定计算候选状态时用多少旧状态。不同论文和实现对 $z_t$ 的约定可能相反（有的写成 $z_t\odot n_t+(1-z_t)\odot h_{t-1}$），读代码前要先确认。另外 PyTorch 的 `nn.GRU` 把重置门放在矩阵乘法之后：$n_t=\tanh(W_nx_t+b_{in}+r_t\odot(U_nh_{t-1}+b_{hn}))$，和上式的 $U_n(r_t\odot h_{t-1})$ 略有不同（我用 `nn.GRUCell` 做过数值核对，差别是真实存在的）。
>
> *English: A GRU keeps a hidden state h_t and updates it through an update gate z_t and a reset gate r_t: the new state is an element-wise blend of the old state and a candidate state. Conventions differ on whether z or 1−z multiplies the old state.*

**白话版：「会做笔记的人」。** 每读一句话（输入），他决定：这条新信息值不值得写进笔记（候选状态 $n_t$）？旧笔记要保留多少（更新门）？写新笔记前要不要先忘掉一部分旧内容（重置门）？笔记（隐状态）的长度是固定的，不管读了多少句。

先手算一步，确认每个公式的含义（用很小的维度：输入 2 维、隐状态 3 维）：

""" + C_GRU + r"""

读输出：给定输入 $x=(1,-1)$ 和旧状态 $h=(0.5,-0.5,0)$，三个更新门是 $(0.625,0.5024,0.4496)$，重置门是 $(0.255,0.3554,0.6153)$，候选状态是 $(-0.7473,-0.0663,-0.6433)$，新状态是 $(0.0323,-0.2842,-0.3541)$。例如第 0 维：$(1-0.625)\times(-0.7473)+0.625\times0.5\approx0.0323$，和代码一致，也和全部用标量乘加的手算一致。后两行展示了门的作用：把更新门偏置调到 $+8$（$z\approx1$）后喂入 5 个随机输入，状态几乎没变，仍是 $(0.5,-0.5,0.004)$（第三维从 0 开始，剩下的 0.004 是极小的泄漏）；调到 $-8$（$z\approx0$）则完全被新输入覆盖，变成了 $(0.317,-0.172,0.18)$。**门控让网络自己决定「记多久」。**

下面这个实验验证「隐状态里确实装着历史」。还是那个环形走廊，但这次**完全不做贝叶斯推断**：用一个随机初始化、一次都没训练过的 GRU 读观测序列，只用最小二乘训练最后一层线性读出，看能否猜出真实的格子，并与「只用当前观测」比较：

""" + C_RES + r"""

读输出：随机猜是 0.125；只用当前观测做特征，线性读出只能达到 0.207；而同一份观测序列经过 GRU 的隐状态后，线性读出达到 0.409，约为前者的两倍。**循环的隐状态把过去的观测压进了一个向量里**，使得线性读出就能利用历史。这个数字（0.409）低于上面贝叶斯滤波的 0.4855（那是另一组设置：12 步、从均匀信念开始），因为这里的 GRU 一次都没有被训练，真正训练过的网络会更接近最优信念。

**一个重要的区别**：卡尔曼滤波和 HMM 的信念有明确的概率意义，可以保证它是历史的充分统计量；GRU 的隐状态只是被训练目标塑造成「对预测有用」，**没有任何保证**它是精确的后验。能否装下足够多的信息，取决于网络容量、训练数据和目标。把 $h_t$ 称作「学出来的信念」是一个有用的类比，而不是严格的等式。

""" + "" ),
  V("hkJNjxlEO-s", "视频三：Gated Recurrent Unit (GRU) Equations Explained（DataMListic）", 9),
  T(r"""
### 潜在动力学模型：把它们接在一起

现在可以把上面三条线合并成世界模型真正要学的对象。

> **标准定义 · 潜在动力学模型 (latent dynamics model)**
>
> 在观测（比如图像）$o_t$ 之上引入低维的潜状态 $z_t$，用三个部分描述环境：
>
> $$\underbrace{p(z_{t+1}\mid z_t,a_t)}_{\text{转移（动力学）}},\qquad\underbrace{p(o_t\mid z_t)}_{\text{观测模型（解码器）}},\qquad\underbrace{q(z_t\mid o_{\le t},a_{<t})}_{\text{推断（编码器 / 滤波）}}$$
>
> 训练用序列版本的 **ELBO**，对每个时间步，既要重建观测，又要让推断出的后验与「只靠动力学的预测」靠近：
>
> $$\mathcal L=\sum_t\Big(\mathbb E_{q}\big[\log p(o_t\mid z_t)\big]-D_{KL}\big(q(z_t\mid o_{\le t},a_{<t})\,\big\|\,p(z_t\mid z_{t-1},a_{t-1})\big)\Big)$$
>
> *English: A latent dynamics model learns a transition p(z_{t+1} | z_t, a_t), an observation model p(o_t | z_t) and an inference network q(z_t | o_≤t, a_<t), trained with a sequential ELBO: reconstruct the observation while keeping the posterior close to the dynamics prior.*

**白话版：「在脑子里放电影」。** 转移模型是「剧本」：给定现在的场景和我的动作，下一幕可能是什么；观测模型是「放映机」：把潜状态渲染成图像；推断网络是「侦探」：看了真实画面后，判断此刻剧本演到哪儿了。训练时让侦探的结论和剧本的预测尽量一致（KL 项），同时画面要还原得像（重建项）。**上一节的 VAE 在这里被一帧接一帧地串起来了**，每一步的先验不再是固定的 $\mathcal N(0,I)$，而是由上一步的状态和动作算出来的。

这里的 $p(z_{t+1}\mid z_t,a_t)$ 是一个**分布**而不是确定的函数，下面的小例子里用一维非线性模型采样不同的未来：

""" + C_LAT + r"""

读输出：同一个起点、同样的噪声强度，动作序列 $(+0.3,+0.3,+0.3)$ 的 3 步后均值是 $+1.384$，$(-0.3,-0.3,-0.3)$ 是 $-1.381$，对称，标准差都是 0.26 左右；也就是说**动作改变了未来的分布，噪声给每种动作后的未来加上了散布**。这正是「规划」的前提：不同的动作序列在潜在动力学里对应不同的未来，我们可以比较它们。下面两行说明观测模型把潜变量变成观测样本（5 个 $z_3$ 对应 5 个 $o_3$，约为其 2 倍加噪声）。

**和 PlaNet / Dreamer 的关系（第 8 节会细讲）**：RSSM 把潜状态拆成两部分：一个确定性的循环部分 $h_t$（像 GRU，负责长期记忆，对应本节的「学出来的信念」）和一个随机部分 $z_t$（负责不确定性，对应卡尔曼/HMM 里的「噪声」）。推断网络 $q(z_t\mid h_t,o_t)$ 是滤波，转移 $p(z_t\mid h_t)$ 是预测。本节学过的所有东西都在里面。

### 这一节你要带走的三句话

1. **观测不等于状态**：只看当前观测会感知混淆；维护**信念** $p(z_t\mid o_{1:t},a_{1:t-1})$（预测 + 更新两步）才能在部分可观测下决策，POMDP 的信念是历史的充分统计量。
2. **HMM 的前向算法和卡尔曼滤波是同一件事的离散 / 连续版本**：预测（过动力学）、更新（乘观测似然）；前向算法 $O(TK^2)$，卡尔曼增益是「相信观测的程度」，更新步一定不增大方差。
3. **RNN / GRU 的隐状态是学出来的信念**：它把历史压成固定长度的向量，但没有精确后验的保证；**潜在动力学模型**把转移 $p(z_{t+1}\mid z_t,a_t)$、观测模型和推断网络合起来，用序列 ELBO 训练，是世界模型的核心。
"""),
  THINK("**计算**：HMM 里初始信念是（下雨, 晴天）$=(0.5,0.5)$，转移矩阵 $A=\\begin{pmatrix}0.7&0.3\\\\0.4&0.6\\end{pmatrix}$，发射矩阵 $B=\\begin{pmatrix}0.9&0.1\\\\0.2&0.8\\end{pmatrix}$（第二列是「没带伞」）。先预测一步，再看到一次「没带伞」，更新后下雨的概率是多少？", r"""
预测：$b^-=(0.5,0.5)A=(0.5\times0.7+0.5\times0.4,\ 0.5\times0.3+0.5\times0.6)=(0.55,\ 0.45)$。

更新：乘上「没带伞」的发射概率（下雨 0.1，晴天 0.8）：$(0.55\times0.1,\ 0.45\times0.8)=(0.055,\ 0.36)$，和是 $0.415$。

归一化：下雨的概率 $0.055/0.415\approx0.1325$，晴天 $\approx0.8675$。可以用上面代码里的 `(b @ A) * B[:, 1]` 再归一化来核对。注意先后顺序：预测在前（还没看新观测），更新在后。
"""),
  THINK("一维卡尔曼滤波里，若观测噪声方差 $r$ 趋近于 $0$（传感器几乎完美），卡尔曼增益 $K$ 和更新后的均值会怎样？若 $r$ 趋近于无穷大呢？分别说成「相信谁」。", r"""
$K=P^-/(P^-+r)$。

- $r\to0$：$K\to1$，$m=m^-+1\cdot(o-m^-)=o$，**完全相信观测**，更新后方差 $(1-K)P^-\to0$。
- $r\to\infty$：$K\to0$，$m\approx m^-$，**完全相信自己的预测**，观测被忽略，方差基本不变。

中间情形是按精度（方差的倒数）加权平均：谁更不确定，谁的权重小。这也是为什么调卡尔曼滤波的关键参数是噪声协方差 $Q$ 与 $R$ 的相对大小：$Q/R$ 越大，滤波器越相信观测、越灵敏；越小越平滑。
"""),
  THINK("**联系机器学习**：DQN 在 Atari 上把最近 4 帧叠起来作为输入，Dreamer 则用循环的隐状态。从「信念」的角度，各自在解决什么问题？各自的局限是什么？", r"""
单帧图像看不出球的运动方向和速度（速度是状态的一部分，但不在单个观测里），所以状态不是马尔可夫的。

- **叠 4 帧**：用一个固定长度的历史窗口当作信念的近似。简单，但窗口之外的信息全部丢掉，窗口内的帧数又靠人工指定；
- **循环隐状态（RNN / GRU / RSSM）**：让网络自己决定把哪些历史压进 $h_t$，理论上可以记住任意久以前的事，但没有精确后验的保证，训练也更难（梯度消失、需要序列数据）。

两者都是对「信念」这个充分统计量的近似。Dreamer 的 RSSM 更进一步：确定性部分负责长期记忆，随机部分负责不确定性，并且有明确的概率模型（ELBO）可以训练。
"""),
  KW(("观测","observation","智能体直接看到的传感器信号，通常只含状态的部分信息"),
     ("状态","state $z_t$","隐藏的、马尔可夫的变量；给定它，未来与过去无关"),
     ("部分可观测","partial observability","观测不足以确定状态，会出现感知混淆"),
     ("状态空间模型","state-space model","转移 $p(z_{t+1}|z_t,a_t)$ 加观测 $p(o_t|z_t)$ 的生成模型"),
     ("信念","belief","给定历史后隐藏状态的后验分布"),
     ("贝叶斯滤波","Bayes filter","预测（过动力学）+ 更新（乘观测似然并归一化）"),
     ("POMDP","partially observable MDP","部分可观测的 MDP，信念是历史的充分统计量"),
     ("隐马尔可夫模型","hidden Markov model (HMM)","离散隐状态 + 转移矩阵 $A$ + 发射矩阵 $B$"),
     ("前向算法","forward algorithm","动态规划计算 $P(o_{1:t},z_t)$，复杂度 $O(TK^2)$"),
     ("卡尔曼滤波","Kalman filter","线性高斯状态空间模型的精确滤波"),
     ("卡尔曼增益","Kalman gain $K$","更新时对新息的权重，反映相信观测的程度"),
     ("新息","innovation","观测减去预测的观测，$o-Hm^-$"),
     ("门控循环单元","gated recurrent unit (GRU)","用更新门、重置门控制隐状态的 RNN"),
     ("隐状态","hidden state $h_t$","RNN 里压缩历史的向量，可看作学出来的信念"),
     ("潜在动力学模型","latent dynamics model","在潜空间里学转移、观测和推断，世界模型的核心"),
  ),
 ],
 "references": [
  {"title": "Kaelbling, Littman & Cassandra《Planning and acting in partially observable stochastic domains》（Artificial Intelligence 101, 1998）", "url": "https://people.csail.mit.edu/lpk/papers/aij98-pomdp.pdf", "note": "本节「信念作为历史的充分统计量」的经典来源；篇幅较长，读前几节即可"},
  {"title": "Hafner 等《Learning Latent Dynamics for Planning from Pixels》（PlaNet，ICML 2019）", "url": "https://arxiv.org/abs/1811.04551", "note": "RSSM 的出处，第 8 节会细读；现在可以先看它的模型图"},
  {"title": "Cho 等《Learning Phrase Representations using RNN Encoder-Decoder for Statistical Machine Translation》（EMNLP 2014）", "url": "https://arxiv.org/abs/1406.1078", "note": "GRU 的出处"},
  {"title": "Rabiner《A tutorial on hidden Markov models and selected applications in speech recognition》（1989）", "url": "http://www.cs.ubc.ca/~murphyk/Bayes/rabiner.pdf", "note": "HMM 的经典教程（前向 / 后向 / Viterbi）；链接可打开，书目信息我没有逐项核实"},
 ],
 "quiz": {"questions": QUIZ},
}

TARGET = [1, 3, 0, 2, 1, 0, 3, 2, 0, 1]
for q, t in zip(unit["quiz"]["questions"], TARGET):
    q["options"][q["answer"]], q["options"][t] = q["options"][t], q["options"][q["answer"]]
    q["answer"] = t

if __name__ == '__main__':
    dump(unit, "wm-0", "u06-state-space.json")
