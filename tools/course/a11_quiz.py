"""ARENA u11 的 10 道测验（沿用旧版题目；个别解释去掉了位置引用）"""
from unitlib import Q
QUIZ = [
  Q('和 NumPy 数组相比，`torch.Tensor` 多了哪两项关键能力？', ['可以存字符串、可以自动排序', '可以放在 GPU 上计算、可以记录计算过程用于自动求导', '可以无限大、可以自动去重', '没有区别'], 1, '张量本质是多维数组，额外支持 GPU 计算和 autograd，这正是深度学习需要的。'),
  Q("运行下面的代码，打印的 `w.grad` 是多少？\n\n```text\nimport torch as t\nw = t.tensor(2.0, requires_grad=True)\ny = w ** 3\ny.backward()\nprint(w.grad)\n```", ['12', '8', '6', '3'], 0, '$dy/dw = 3w^2 = 3 \\times 4 = 12$。'),
  Q('调用 `loss.backward()` 之后，梯度存在哪里？', ['存在 `loss.grad` 里', '作为 `backward()` 的返回值', '直接更新到参数的值里', '存在各个参数（叶子张量）的 `.grad` 属性里'], 3, '`backward()` 没有返回值，也不会修改参数本身，只是把梯度写进每个参数的 `.grad`。更新参数是优化器的事。'),
  Q('对同一个张量连续两次计算并调用 `.backward()`（中间不清零），`.grad` 会？', ['保留第二次的梯度', '保留第一次的梯度', '变成两次梯度之和', '变成 0'], 2, 'PyTorch 的梯度默认**累加**。所以训练循环每一步都要 `optimizer.zero_grad()`。'),
  Q('`nn.Parameter` 的作用是？', ['一种会被 `nn.Module` 自动登记为可训练参数的张量，默认 `requires_grad=True`', '设置学习率', '定义损失函数', '一种不能求导的常量'], 0, '把 `nn.Parameter` 赋给模块属性后，`model.parameters()` 就能找到它，优化器就会更新它。'),
  Q('自定义一个 `nn.Module` 时，前向计算写在哪个方法里？', ['`__init__`', '`backward`', '`step`', '`forward`'], 3, '`__init__` 里定义层和参数，`forward` 里写输入怎么变成输出。反向传播由 autograd 自动完成，不用自己写 `backward`。'),
  Q('`nn.Linear(4, 8)` 的 `weight` 形状是？', ['`(4, 8)`', '`(8, 4)`', '`(8,)`', '`(32,)`'], 1, 'PyTorch 的线性层权重是 (输出维度, 输入维度)，计算 $\\mathbf{y} = W\\mathbf{x} + \\mathbf{b}$。另外还有一个形状为 `(8,)` 的偏置。'),
  Q('损失函数一般返回什么？', ['和输入同形状的张量', '一个标量张量，衡量预测和目标的差距', '模型的参数', '梯度'], 1, '返回一个标量（`torch.Size([])`），这样才能对它调用 `.backward()`。'),
  Q('一个标准训练步骤的正确顺序是？', ['`backward` → 前向 → `zero_grad` → `step`', '`step` → 前向 → `backward` → `zero_grad`', '前向 → 算损失 → `zero_grad` → `backward` → `step`', '前向 → `step` → 算损失 → `backward`'], 2, '先前向算出损失；清空旧梯度；反向传播填好新梯度；最后优化器用梯度更新参数。`zero_grad` 只要在 `backward` 之前即可。'),
  Q('下面哪一个**不是**超参数？', ['学习率', '批量大小 (batch size)', '隐藏层的宽度', '第一层线性层的权重'], 3, '权重是训练学出来的**参数**；学习率、批量大小、层宽都是训练前人为设定的**超参数**。'),
]
