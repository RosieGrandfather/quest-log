"""ARENA 0.0 第 9 节：信息论（按 v3 格式重写，2026-10-04）"""
from unitlib import *
from a09c import C_SURP, C_ENT, C_CE, C_LM, C_FIT
from a09_quiz import QUIZ

unit = {
 "id": "u09",
 "title": "信息论：熵、交叉熵、KL 散度",
 "en": "Information Theory",
 "minutes": 90,
 "objectives": [
  "理解 **信息量 (information / surprisal)** $-\\log p$：越意外的事件信息量越大，独立事件的信息量相加；分清 **比特 (bit)** 和 **奈特 (nat)**",
  "理解 **熵 (entropy)** 是平均信息量，知道它什么时候最大（均匀分布，$\\log n$）、什么时候为 0，以及它与最优编码长度的关系",
  "理解 **交叉熵 (cross-entropy)** 和 **KL 散度 (KL divergence)** 的定义，会用 $H(P,Q)=H(P)+D_{KL}(P\\|Q)$ 推理，知道 KL 非负且不对称",
  "明白为什么语言模型的训练损失就是交叉熵：独热目标下损失 $=-\\ln Q(\\text{正确的词})$，会算「均匀猜测」时的损失，会把损失换算成 **困惑度 (perplexity)**",
  "知道交叉熵对 logit 的梯度是 $Q-P$，并能用 NumPy 验证",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

ARENA 说得很直接：信息、熵和 KL 散度「在解释损失函数时扮演关键角色」。语言模型每一步都在预测下一个词的概率分布，训练它用的**交叉熵损失 (cross-entropy loss)** 就来自信息论。分类、语言建模、强化学习里的策略优化（KL 惩罚）、扩散模型、蒸馏，用到的都是这一套语言。

**学完它你就能看懂这几件事：**

- 训练日志里那个 loss 数字意味着什么：训练刚开始为什么是 10.8 左右，降到 3 又意味着什么（困惑度）；
- PyTorch 里 `F.cross_entropy(logits, target)` 到底算了什么，为什么传进去的是 logit 不是概率；
- 为什么「最小化交叉熵」和「让模型分布靠近数据分布」是一回事；
- 后面强化学习（RLHF）里常见的「KL 惩罚」「KL 散度约束」是什么意思。

**本节安排（约 90 分钟）**：信息量与比特（12 分钟）→ 视频一（17 分钟）→ 熵与最优编码（15 分钟）→ 视频二（11 分钟）→ 交叉熵与 KL 散度（15 分钟）→ 语言模型的损失（12 分钟）→ 动手实验：用交叉熵拟合一个分布（8 分钟）→「想一想」。视频是英文的，可以打开 YouTube 的中文字幕。

### 从「惊讶程度」开始

> **标准定义 · 信息量 / 惊讶度 (information / surprisal)**
>
> 事件 $x$ 发生的概率是 $p(x)$，它带来的**信息量**（也叫**惊讶度**）定义为
>
> $$I(x)=-\log p(x)=\log\frac{1}{p(x)}$$
>
> 对数以 2 为底时，单位是**比特 (bit)**；以 $e$ 为底时，单位是**奈特 (nat)**。性质：$p=1$ 时 $I=0$；概率越小，信息量越大；两个**独立**事件同时发生，信息量**相加**（因为 $\log$ 把乘法变成加法）。
>
> *English: The information (surprisal) of an event with probability p is −log p. It is 0 for a certain event, grows as the event gets less likely, and is additive for independent events. Base 2 gives bits, base e gives nats.*

**白话版：「听到消息有多吃惊」。** 「明天太阳会升起」毫不意外，信息量是 0；「你中了彩票」非常意外，信息量很大。一个概率 $1/8$ 的事件，等价于「连续抛 3 枚公平硬币都猜对」，所以是 3 比特。

""" + C_SURP + r"""

读输出：$p=0.5$ 是 1 比特（一次抛硬币），$p=0.25$ 是 2 比特，$p=1/8$ 是 3 比特；$p=0.01$ 是 6.644 比特，也就是 4.605 奈特。「硬币正面 + 骰子 6」联合概率是 $1/12$，信息量 3.585 比特，正好等于 1 比特加 $\log_26=2.585$ 比特，验证了「独立事件信息量相加」。换算：1 奈特 = 1.4427 比特。**PyTorch 的所有损失函数用的是自然对数（奈特）**，而讲信息论时习惯用比特，读书时要留意底数。
"""),
  V("YtebGVx-Fxw", "视频一：Entropy (for data science) Clearly Explained（StatQuest）", 17),
  T(r"""
### 熵：平均信息量

> **标准定义 · 熵 (entropy)**
>
> 离散分布 $P$ 的**熵**是信息量的期望：
>
> $$H(P)=\mathbb{E}_{x\sim P}\big[-\log P(x)\big]=-\sum_xP(x)\log P(x)$$
>
> 约定 $0\log0=0$。性质：$H(P)\ge0$；当某个结果概率为 1 时 $H=0$；$n$ 个结果的分布里，**均匀分布的熵最大**，$H=\log n$。
>
> *English: The entropy of a distribution P is the expected surprisal, H(P) = −Σ P(x) log P(x). It is 0 for a deterministic outcome and is maximized by the uniform distribution, where it equals log n.*

**白话版：「平均每次要问几个是非题」。** 猜一个你脑子里的东西，每问一个「是 / 否」问题得到 1 比特。如果有 8 个等可能的答案，最少平均要问 3 个问题；如果某个答案几乎必然出现，问题就少得多。熵就是「用最聪明的问法，平均要问几个问题」，也是「用最优编码描述一个结果，平均需要多少比特」。

""" + C_ENT + r"""

读输出：

- 公平硬币 1 比特；正面概率 0.99 的硬币只有 0.0808 比特（几乎没有悬念）；完全确定的分布熵是 0。
- 均匀分布的熵就是 $\log_2n$：$n=8$ 是 3 比特，GPT-2 的 50257 个词若等可能，是 15.617 比特。
- 同样 4 个结果：确定分布 0，$(0.7,0.1,0.1,0.1)$ 是 1.3568，$(0.5,0.5,0,0)$ 是 1，均匀分布最大，是 2 比特。
- **编码的意义**：概率 $(1/2,1/4,1/8,1/8)$ 的四个结果，分配 1、2、3、3 位的码字（概率越大码字越短），平均码长是 1.75 位，**恰好等于熵 1.75 比特**。这里的概率都是 2 的负整数次幂，所以刚好取到；一般情况下，最优编码的平均长度不小于熵，且很接近它。
- 最后一行：1000 个随机分布的熵都落在 $[0,\log_25]$ 之内，这是「均匀分布熵最大」的随机对拍。

### 交叉熵与 KL 散度
"""),
  V("ErfnhcEV1O8", "视频二：A Short Introduction to Entropy, Cross-Entropy and KL-Divergence（Aurélien Géron）", 11),
  T(r"""
> **标准定义 · 交叉熵与 KL 散度 (cross-entropy & KL divergence)**
>
> 真实分布是 $P$，模型的预测是 $Q$。**交叉熵**
>
> $$H(P,Q)=-\sum_xP(x)\log Q(x)$$
>
> 是「用 $Q$ 去预测来自 $P$ 的结果，平均有多意外」。**KL 散度**是多付出的那一部分：
>
> $$D_{KL}(P\|Q)=\sum_xP(x)\log\frac{P(x)}{Q(x)}=H(P,Q)-H(P)$$
>
> 性质：$D_{KL}\ge0$，当且仅当 $P=Q$ 时为 0；**不对称**，$D_{KL}(P\|Q)\ne D_{KL}(Q\|P)$，所以它不是真正的「距离」。因此 $H(P,Q)\ge H(P)$，最小值在 $Q=P$ 时取到。
>
> *English: The cross-entropy H(P,Q) = −Σ P log Q is the expected surprisal when predicting data from P using Q. The KL divergence D_KL(P‖Q) = H(P,Q) − H(P) ≥ 0 is the extra cost of using Q instead of P; it is zero iff P = Q and is not symmetric.*

**白话版：「用错的地图导航，多绕的路」。** 真实情况是 $P$，你心里的模型是 $Q$。如果 $Q$ 就是 $P$，你的平均意外程度是最低的（也就是熵）；$Q$ 偏离得越多，平均意外越大，**多出来的那部分就是 KL 散度**。训练时数据分布 $P$ 是固定的，$H(P)$ 是个常数，所以**最小化交叉熵 = 最小化 KL 散度**，两者只差一个常数。

""" + C_CE + r"""

读输出：用公平硬币 $P=(0.5,0.5)$ 和一个错误的预测 $Q=(0.9,0.1)$：$H(P)=1$，$H(P,Q)=1.737$，两者之差就是 $D_{KL}(P\|Q)=0.737$，加回去 $1+0.737=1.737$，恒等式成立。换一个方向，$D_{KL}(Q\|P)=0.531$，**和 0.737 不一样**，说明 KL 不对称。后面两行是随机对拍：2000 组随机的 $P,Q$ 里，交叉熵都不小于熵、KL 都不小于 0、恒等式都成立；$Q=P$ 时 KL 恰好是 0.0。

**一个常见陷阱**：如果 $P(x)>0$ 而 $Q(x)=0$，$\log Q(x)=-\infty$，交叉熵和 KL 就是无穷大。这就是为什么模型输出要用 softmax：它保证每个词的概率都严格大于 0。

### 语言模型的损失：独热目标下的交叉熵

训练语料里，下一个词是确定的（比如是 "cat"），相当于 $P$ 是一个**独热 (one-hot)** 分布：正确词概率为 1，其余为 0。交叉熵里只剩一项：

$$H(P,Q)=-\log Q(\text{正确的词})$$

这就是语言模型的训练损失：**模型给正确答案的概率取负对数**。

**ARENA 的思考题**：词表大小为 $|V|$。如果模型**均匀地瞎猜**（每个词 $1/|V|$），损失就是 $-\log\frac1{|V|}=\log|V|$。GPT-2 的词表有 50,257 个词，所以随机初始化的模型损失约为 $\ln50257\approx10.82$；训练刚开始看到这个数，说明一切正常。如果模型的分布**完全等于**语言的真实分布（$Q=P$），交叉熵降到 $H(P)$，也就是自然语言本身的熵，这是任何模型都突破不了的下限。

下面用 NumPy 把 PyTorch 的 `F.cross_entropy` 重写一遍，并看看它为什么必须直接吃 logit：

""" + C_LM + r"""

读输出：

- 全 0 的 logit（= 均匀分布）在 50257 个词上的损失是 10.8249，恰好等于 $\ln50257$。
- 小例子：4 个词的 logit 是 $(1,0.5,2,-1)$，softmax 后 $(0.2242,0.136,0.6095,0.0303)$，和为 1；正确词是第 3 个（下标 2），概率 0.6095，损失 $-\ln0.6095=0.4952$。
- 概率到损失的对照：概率 1 对应损失 0，0.5 对应 0.693，0.25 对应 1.386，0.05 对应 2.996，0.01 对应 4.605。**损失每增加 $\ln2\approx0.693$，正确词的概率就减半。**
- **困惑度 (perplexity) $=e^{\text{loss}}$**：损失 10.8249 对应困惑度 50256.7，约等于词表大小（相当于在全部词里随机猜）；损失 4.0 对应 54.6；损失 3.0 对应 20.1，相当于模型的「平均犹豫程度」是在大约 20 个等可能的词里猜。
- 最后一行：当某个 logit 高达 1000，朴素写法 $-\ln\frac{e^{z_0}}{\sum e^{z}}$ 因为 $e^{1000}$ 溢出而得到 `nan`，**log-sum-exp 的稳定写法**给出正确的 0.0。这就是为什么应该把 logit 直接交给 `CrossEntropyLoss`，不要自己先 softmax 再取对数。

### 动手实验：用交叉熵「拟合」一个分布

最后做一个实验，把这一节和上一节（微积分）串起来。真实分布是 $P=(0.5,0.25,0.15,0.1)$，模型只有 4 个 logit，经 softmax 得到 $Q$，从均匀分布出发，用梯度下降最小化交叉熵。**交叉熵对 logit 的梯度恰好是 $Q-P$**（和上一节 BCE 的结论 $\sigma(z)-y$ 是同一个规律的推广），而且我们先用数值微分核对：

""" + C_FIT + r"""

读输出：$H(P)=1.208$ 奈特，是交叉熵能达到的下限。起点是均匀分布，交叉熵 $=\ln4=1.3863$，KL 为 0.17832。随着训练，交叉熵一路下降逼近 1.2080，**KL 同步降到 0**：第 5 步 0.04264，第 20 步 0.00185，第 50 步 0.00003；第 200 步 $Q=(0.5,0.25,0.15,0.1)$，和 $P$ 一模一样。最后一行的梯度检验也是 `True`。这就是「训练语言模型」最小的缩影：**降低交叉熵，就是让模型分布逼近数据分布**；真正的语言模型多了的，只是 $Q$ 由一个巨大的网络根据上下文算出来。

### 这一节你要带走的三句话

1. **信息量 $-\log p$ 衡量意外程度，熵是它的平均值**：均匀分布熵最大（$\log n$），确定分布熵为 0；底数是 2 时单位是比特，PyTorch 用自然对数（奈特）。
2. **交叉熵 $H(P,Q)=H(P)+D_{KL}(P\|Q)$**：KL 非负、不对称；数据分布固定时，最小化交叉熵就是最小化 KL。
3. **语言模型的损失 $=-\ln$（正确词的概率）**：随机初始化约 $\ln|V|$（GPT-2 是 10.82），$e^{\text{loss}}$ 是困惑度；对 logit 的梯度是 $Q-P$，所以直接把 logit 交给 `CrossEntropyLoss`。
"""),
  THINK("一个有 8 个等可能结果的分布，熵是多少比特？如果其中一个结果的概率变成 1 呢？再算：概率为 $(1/2,1/4,1/4)$ 的分布，熵是多少？", r"""
均匀分布：$H=\log_28=3$ 比特（正好需要 3 个比特来编码 8 种情况）。某个结果概率为 1：没有任何不确定性，$H=0$。

$(1/2,1/4,1/4)$：$H=\tfrac12\times1+\tfrac14\times2+\tfrac14\times2=1.5$ 比特。可以用上面代码里的 `entropy([0.5, 0.25, 0.25])` 核对。
"""),
  THINK("$P=(0.5,0.5)$，$Q=(0.9,0.1)$。算 $H(P,Q)$ 和 $D_{KL}(P\\|Q)$（以 2 为底）。为什么 $D_{KL}(Q\\|P)$ 是另一个数？", r"""
$$H(P,Q)=-\big(0.5\log_20.9+0.5\log_20.1\big)\approx-\big(0.5\times(-0.152)+0.5\times(-3.322)\big)\approx1.737$$

$H(P)=1$，所以 $D_{KL}(P\|Q)=1.737-1=0.737$ 比特：用 $Q$ 来猜公平硬币，每次平均多付出约 0.74 比特的「意外」。

KL 的定义里，**期望是对第一个分布取的**：$D_{KL}(P\|Q)$ 在 $P$ 认为重要的地方衡量 $Q$ 的差距，而 $D_{KL}(Q\|P)$ 在 $Q$ 认为重要的地方衡量。两者权重不同，所以结果不同（代码里是 0.531 对 0.737），KL 不是对称的「距离」。
"""),
  THINK("**联系机器学习**：训练一个语言模型，loss 从 10.8 降到 3.0。用「概率」来解释这个数字，并说说用这个 loss 能不能判断模型「理解」了语言。", r"""
损失是 $-\ln Q(\text{正确词})$ 的平均值。

- $10.8\approx\ln50257$：相当于在五万多个词里瞎猜（困惑度约 50000）。
- $3.0$：$e^{-3}\approx0.05$，粗略地说，模型给正确的下一个词的概率大约是 5%（几何平均意义下），相当于在大约 $e^3\approx20$ 个候选词里猜，这个量 $e^{\text{loss}}$ 叫**困惑度 (perplexity)**。

严格来说，$e^{-\text{平均 loss}}$ 是概率的几何平均，不是算术平均。另外，**loss 低不等于「理解」**：它只说明模型把训练分布的下一个词预测得准；评价语言模型，还要看在没见过的数据上的 loss（泛化）和各种任务上的表现。损失的下限是语言本身的熵 $H(P)$，不可能降到 0。
"""),
  KW(("信息量 / 惊讶度","information / surprisal","$-\\log p$，越意外越大"),
     ("比特 / 奈特","bit / nat","以 2 / 以 $e$ 为底的对数单位，1 奈特 ≈ 1.4427 比特"),
     ("熵","entropy $H(P)$","平均信息量，衡量不确定性"),
     ("均匀分布","uniform distribution","熵最大，$H=\\log n$"),
     ("最优编码","optimal code","概率大的结果用短码字，平均码长不小于熵"),
     ("交叉熵","cross-entropy $H(P,Q)$","用 $Q$ 预测 $P$ 的平均意外程度"),
     ("KL 散度","KL divergence","$H(P,Q) - H(P) \\ge 0$，不对称"),
     ("独热分布","one-hot","正确类为 1，其他为 0"),
     ("交叉熵损失","cross-entropy loss","$-\\log Q(\\text{正确答案})$"),
     ("困惑度","perplexity","$e^{\\text{loss}}$，相当于在多少个词里猜"),
     ("词表","vocabulary $V$","模型能输出的所有 token"),
     ("softmax","softmax","把 logit 变成严格为正、和为 1 的概率"),
     ("logit","logit","进 softmax 之前的原始输出，交叉熵对它的梯度是 $Q-P$"),
     ("log-sum-exp","log-sum-exp trick","先减最大值再算，避免 exp 溢出"),
  ),
 ],
 "references": [
  {"title": "ARENA [0.0] Prerequisites — Information theory 部分", "url": "https://github.com/ARENA-education/ARENA_materials/blob/main/chapter0_fundamentals/instructions/pages/00_%5B0.0%5D_Prerequisites.md", "note": "本节依据的原文大纲和「均匀猜测时的交叉熵」思考题（讲解为自写，未转载原文）"},
  {"title": "Six (and a half) intuitions for KL divergence（LessWrong）", "url": "https://www.lesswrong.com/posts/no5jDTut5Byjqb4j5/six-and-a-half-intuitions-for-kl-divergence", "note": "ARENA 推荐；先掌握熵再看"},
  {"title": "Elements of Information Theory（Cover & Thomas）", "url": "http://staff.ustc.edu.cn/~cgong821/Wiley.Interscience.Elements.of.Information.Theory.Jul.2006.eBook-DDU.pdf", "note": "ARENA 提到的经典教材，内容远超所需，不必优先"},
  {"title": "PyTorch 文档：torch.nn.CrossEntropyLoss", "url": "https://pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html", "note": "官方说明：输入是未归一化的 logit，用自然对数"},
 ],
 "quiz": {"questions": QUIZ},
}

if __name__ == '__main__':
    dump(unit, "arena-0.0", "u09-information-theory.json")
