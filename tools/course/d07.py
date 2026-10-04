"""dsa-0 第 7 节：树与二叉搜索树"""
from unitlib import *
from runlib import code

C_TRAV = code('''
from collections import deque

class TreeNode:
    def __init__(self, val, left=None, right=None):
        self.val, self.left, self.right = val, left, right

#        1
#       / \\
#      2   3
#     / \\   \\
#    4   5   6
root = TreeNode(1, TreeNode(2, TreeNode(4), TreeNode(5)), TreeNode(3, None, TreeNode(6)))

def preorder(t):                         # 前序：根 → 左 → 右
    return [] if not t else [t.val] + preorder(t.left) + preorder(t.right)

def inorder(t):                          # 中序：左 → 根 → 右
    return [] if not t else inorder(t.left) + [t.val] + inorder(t.right)

def postorder(t):                        # 后序：左 → 右 → 根
    return [] if not t else postorder(t.left) + postorder(t.right) + [t.val]

def level_order(t):                      # 层序：一层一层地走，用队列
    out, q = [], deque([t] if t else [])
    while q:
        level = []
        for _ in range(len(q)):          # 这一层有多少个节点，就取多少次
            node = q.popleft()
            level.append(node.val)
            if node.left:
                q.append(node.left)
            if node.right:
                q.append(node.right)
        out.append(level)
    return out

def inorder_iter(t):                     # 用自己的栈改写中序遍历（避免递归太深）
    out, stack, cur = [], [], t
    while cur or stack:
        while cur:                       # 一路向左，沿途的节点都压栈
            stack.append(cur)
            cur = cur.left
        cur = stack.pop()                # 左边走到头了，访问它
        out.append(cur.val)
        cur = cur.right                  # 然后去它的右子树
    return out

def height(t):                           # 高度：从该节点到最远叶子的边数；空树记为 -1
    return -1 if not t else 1 + max(height(t.left), height(t.right))

def size(t):
    return 0 if not t else 1 + size(t.left) + size(t.right)

print("前序", preorder(root))
print("中序", inorder(root))
print("后序", postorder(root))
print("层序", level_order(root))
print("迭代版中序", inorder_iter(root) == inorder(root))
print("高度", height(root), " 节点数", size(root))
''')

C_BST = code('''
import random

class Node:
    def __init__(self, val):
        self.val, self.left, self.right = val, None, None

class BST:
    def __init__(self):
        self.root = None

    def insert(self, val):
        self.root = self._insert(self.root, val)
    def _insert(self, node, val):
        if node is None:
            return Node(val)             # 找到空位，新节点就放在这里
        if val < node.val:
            node.left = self._insert(node.left, val)
        elif val > node.val:
            node.right = self._insert(node.right, val)
        return node                      # 相等就不重复插入

    def search(self, val):
        node = self.root
        while node:                      # 每次比较，排除一整棵子树
            if val == node.val:
                return True
            node = node.left if val < node.val else node.right
        return False

    def delete(self, val):
        self.root = self._delete(self.root, val)
    def _delete(self, node, val):
        if node is None:
            return None
        if val < node.val:
            node.left = self._delete(node.left, val)
        elif val > node.val:
            node.right = self._delete(node.right, val)
        else:                            # 找到要删除的节点了，分三种情形
            if node.left is None:        # 情形 1、2：没有孩子，或者只有一个孩子，让孩子顶上来
                return node.right
            if node.right is None:
                return node.left
            succ = node.right            # 情形 3：有两个孩子。找「后继」：右子树里最小的
            while succ.left:
                succ = succ.left
            node.val = succ.val          # 用后继的值覆盖当前节点
            node.right = self._delete(node.right, succ.val)   # 再把后继删掉
        return node

    def inorder(self):
        out = []
        def go(n):
            if n:
                go(n.left); out.append(n.val); go(n.right)
        go(self.root)
        return out

t = BST()
for v in (50, 30, 70, 20, 40, 60, 80):
    t.insert(v)
print("中序（BST 的中序一定是升序）：", t.inorder())
t.delete(20); print("删除叶子 20：       ", t.inorder())
t.delete(30); print("删除只有一个孩子的 30：", t.inorder())
t.delete(50); print("删除有两个孩子的根 50：", t.inorder(), " 根现在是", t.root.val)

# 随机操作，和 Python 的 set 对照
random.seed(0)
ref, t = set(), BST()
for _ in range(3000):
    x = random.randint(0, 100)
    if random.random() < 0.6:
        t.insert(x); ref.add(x)
    else:
        t.delete(x); ref.discard(x)
print("随机插入 / 删除 3000 次，结果与 set 一致：", t.inorder() == sorted(ref))
''')

C_VALID = code('''
class Node:
    def __init__(self, val, left=None, right=None):
        self.val, self.left, self.right = val, left, right

def naive_valid(t):                      # 错误的检查：只看每个节点和它的直接孩子
    if not t:
        return True
    if t.left and t.left.val >= t.val:
        return False
    if t.right and t.right.val <= t.val:
        return False
    return naive_valid(t.left) and naive_valid(t.right)

def valid(t, lo=float('-inf'), hi=float('inf')):    # 正确的检查：每个节点必须落在祖先们规定的区间里
    if not t:
        return True
    if not lo < t.val < hi:
        return False
    return valid(t.left, lo, t.val) and valid(t.right, t.val, hi)

#      5
#       \\
#        7
#       /
#      4        ← 4 比它的父亲 7 小，没问题；但它在 5 的右子树里，必须比 5 大
bad = Node(5, None, Node(7, Node(4), None))
print("局部检查：", naive_valid(bad), "  正确检查：", valid(bad))
good = Node(5, Node(3, Node(2), Node(4)), Node(8, Node(6), Node(9)))
print("合法的 BST：", naive_valid(good), valid(good))
''')

C_HEIGHT = code('''
import random

class Node:
    def __init__(self, val):
        self.val, self.left, self.right = val, None, None

def insert(root, val):                   # 迭代版插入（避免递归太深）
    if root is None:
        return Node(val)
    cur = root
    while True:
        if val < cur.val:
            if cur.left is None:
                cur.left = Node(val); break
            cur = cur.left
        else:
            if cur.right is None:
                cur.right = Node(val); break
            cur = cur.right
    return root

def height(root):                        # 迭代版高度：一层层数
    h, level = -1, [root] if root else []
    while level:
        h += 1
        level = [c for n in level for c in (n.left, n.right) if c]
    return h

random.seed(0)
n = 1000
keys = list(range(n))
for name, order in (("随机顺序插入", random.sample(keys, n)), ("按升序插入", keys)):
    root = None
    for k in order:
        root = insert(root, k)
    print(f"{name}：n={n}，树高 {height(root)}")
''')

C_AVL = code('''
import random

class Node:
    def __init__(self, val):
        self.val, self.left, self.right, self.h = val, None, None, 0

def h(n):
    return -1 if n is None else n.h
def update(n):
    n.h = 1 + max(h(n.left), h(n.right))

def rot_right(y):                        # 右旋：把左孩子 x 提上来当根
    x = y.left
    y.left, x.right = x.right, y
    update(y); update(x)
    return x

def rot_left(x):                         # 左旋：把右孩子 y 提上来当根
    y = x.right
    x.right, y.left = y.left, x
    update(x); update(y)
    return y

def insert(n, val):                      # AVL 插入：先按 BST 插入，回溯时检查平衡并旋转
    if n is None:
        return Node(val)
    if val < n.val:
        n.left = insert(n.left, val)
    elif val > n.val:
        n.right = insert(n.right, val)
    else:
        return n
    update(n)
    bal = h(n.left) - h(n.right)         # 平衡因子 = 左高 − 右高
    if bal > 1:                          # 左边太高
        if h(n.left.left) < h(n.left.right):
            n.left = rot_left(n.left)    # 「左右」型：先把左孩子左旋，变成「左左」型
        return rot_right(n)
    if bal < -1:                         # 右边太高
        if h(n.right.right) < h(n.right.left):
            n.right = rot_right(n.right) # 「右左」型：先把右孩子右旋
        return rot_left(n)
    return n

def inorder(n):
    return [] if n is None else inorder(n.left) + [n.val] + inorder(n.right)

def balanced(n):                         # 检查每个节点的左右高度差都不超过 1
    return n is None or (abs(h(n.left) - h(n.right)) <= 1 and balanced(n.left) and balanced(n.right))

for name, order in (("升序插入", list(range(1000))), ("随机插入", random.sample(range(1000), 1000))):
    root = None
    for k in order:
        root = insert(root, k)
    print(f"{name} 1000 个键：树高 {h(root)}，保持平衡 {balanced(root)}，中序有序 {inorder(root) == sorted(order)}")
''')

unit = {
 "id": "u07",
 "title": "树与二叉搜索树",
 "en": "Trees & Binary Search Trees",
 "minutes": 80,
 "objectives": [
  "说出 **树 (tree)** 的术语（根、叶、深度、高度、子树）和 **二叉树 (binary tree)** 的定义，知道 $n$ 个节点的树有 $n-1$ 条边",
  "会写四种遍历：**前序、中序、后序 (DFS)** 和 **层序 (BFS)**，并知道各自用什么结构实现",
  "说出 **二叉搜索树 (BST)** 的性质，会写查找、插入、**删除（三种情形）**，知道中序遍历得到升序",
  "理解 BST 的复杂度是 $O(h)$，为什么顺序插入会退化成链，以及 **AVL 树 (AVL tree)** 如何用旋转保证 $h=O(\\log n)$",
  "会用递归解决树问题：高度、节点数、**验证 BST**（常见错误）",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

数组和链表都是「一条线」；**树**是「会分叉的线」。现实里很多东西本来就是树：公司的组织架构、文件夹结构、网页的 HTML、决策的过程。它还能给我们一个新本事：把查找从 $O(n)$ 降到 $O(\log n)$，同时又比数组更方便插入和删除，这就是 **二叉搜索树**。

**学完它你就能看懂这几件事：**

- **决策树 (decision tree)**、**随机森林 (random forest)**、**XGBoost / LightGBM** 这些机器学习模型的基本单位就是树；
- 数据库的索引（B 树 / B+ 树）、Python 之外的很多有序容器（C++ 的 `std::map`、Java 的 `TreeMap`）都是**平衡搜索树**；
- 神经网络里的**计算图 (computational graph)** 虽是有向无环图，但反向传播的递归结构和树的后序遍历非常像；
- 面试里最高频的「遍历」「验证 BST」「最近公共祖先」。

**本节安排（约 80 分钟）**：树的术语与递归结构（12 分钟）→ 视频一（10 分钟）→ 四种遍历与代码（15 分钟）→ 视频二（4 分钟）→ BST 与代码（20 分钟）→ 视频三（6 分钟）→ 平衡与 AVL（13 分钟）→ 视频四（4 分钟）→「想一想」。

### 树的术语

> **标准定义 · 树 (tree)、二叉树 (binary tree)**
>
> **树**是由**节点 (node)** 和连接节点的**边 (edge)** 组成的、没有环的连通结构；指定一个节点为**根 (root)**。除根外每个节点有唯一的**父节点 (parent)**，可以有若干**子节点 (children)**；没有子节点的叫**叶子 (leaf)**。**二叉树**的每个节点至多有两个子节点，分别称为**左孩子**和**右孩子**。一棵有 $n$ 个节点的树恰有 $n-1$ 条边。
>
> *English: A tree is an acyclic connected structure of nodes and edges with a designated root; in a binary tree every node has at most two children, left and right.*

**白话版：倒着长的树。** 根在最上面，往下分叉，叶子在最底下。每个节点只有一个「上级」（父节点），但可以有好几个「下属」（子节点）。因为每个节点除根外都有一条通向父节点的边，所以 $n$ 个节点就有 $n-1$ 条边。

> **标准定义 · 深度、高度、子树**
>
> 节点的 **深度 (depth)**：从根到它的路径上的边数（根的深度是 0）。节点的 **高度 (height)**：从它到最远的叶子的路径上的边数（叶子高度是 0）；**树的高度**就是根的高度。以某个节点为根、包含它所有后代的部分称为它的 **子树 (subtree)**。高度为 $h$ 的二叉树最多有 $2^{h+1}-1$ 个节点。
>
> *English: Depth counts edges from the root; height counts edges down to the deepest leaf; a subtree is a node together with all its descendants.*

**白话版：「深度」往上数，「高度」往下数。** 深度是「离根多远」，高度是「离最底下的叶子多远」。关键事实：**树是递归的**，每个节点的左孩子和右孩子，又各自是一棵更小的树。所以对树的绝大多数问题，都可以写成「先处理根，再递归处理左子树和右子树」。
"""),
  V("1-l_UOFi1Xw", "视频一：Introduction to Trees（CS Dojo）", 10),
  T(r"""
### 四种遍历

> **标准定义 · 树的遍历 (tree traversal)**
>
> 按某种顺序**恰好访问每个节点一次**。深度优先 (DFS) 的三种，区别只在「根」什么时候访问：**前序 (preorder)**：根 → 左 → 右；**中序 (inorder)**：左 → 根 → 右；**后序 (postorder)**：左 → 右 → 根。**层序 (level-order)** 是广度优先 (BFS)：从上到下、从左到右一层一层访问，用**队列**实现。每种遍历都是 $O(n)$。
>
> *English: Preorder visits root–left–right, inorder left–root–right, postorder left–right–root; level-order visits nodes layer by layer using a queue.*

**白话版：同一棵树，不同的「走法」。** 前序是「先打招呼再往下」：用来**复制一棵树**；后序是「先处理完所有下属再轮到自己」：用来**删除一棵树**、**计算占用空间**（先算完子文件夹才知道本文件夹多大）；中序在 BST 里特别重要，下面会看到；层序用来**一层一层**地处理（比如打印每一层）。

""" + C_TRAV + r"""

注意几个细节：**前序的第一个一定是根，后序的最后一个一定是根**；`level_order` 里 `for _ in range(len(q))` 这一句，每次**固定取出当前这一层的所有节点**，这是按层分组的关键；迭代版中序使用自己的栈，原理和上一节「把递归改成显式栈」一样，避免树很深时递归爆栈。
"""),
  V("b_NjndniOqY", "视频二：Learn Tree traversal in 3 minutes（Bro Code）", 4),
  T(r"""
### 二叉搜索树

> **标准定义 · 二叉搜索树 (binary search tree, BST)**
>
> 一棵二叉树，对**每一个**节点 $x$ 都满足：$x$ 的**整个左子树**中的所有键都**小于** $x$ 的键，$x$ 的**整个右子树**中的所有键都**大于** $x$ 的键。查找、插入、删除的时间都是 $O(h)$，$h$ 为树的高度。**对 BST 做中序遍历，得到的是升序序列。**
>
> *English: In a BST, for every node all keys in the left subtree are smaller and all keys in the right subtree are larger; an inorder traversal yields the keys in sorted order.*

**白话版：每个节点都是一个「小于往左、大于往右」的路牌。** 找一个数时，从根出发：比根小就去左边，比根大就去右边，**每一步都能直接排除掉一整棵子树**。这和二分查找是同一个思想，只不过「中间的数」换成了树的根。

- **查找：** 沿着路牌走，$O(h)$。
- **插入：** 按查找的路径走到一个空位，把新节点放在那里。
- **删除：** 找到节点后分三种情形：**没有孩子**，直接删；**只有一个孩子**，让孩子顶上来；**有两个孩子**，用它的**后继 (successor)**（右子树里最小的节点）的值覆盖它，再把后继删掉（后继最多只有右孩子，属于前两种情形）。

""" + C_BST + r"""

最后一行用 3000 次随机插入、删除，和 Python 的 `set` 对照，结果一致。**第三种删除情形**为什么用后继？因为后继是「比当前节点大的最小的数」，用它顶替这个位置，左边所有数仍然小于它、右边所有数仍然大于它，BST 的性质不被破坏。用左子树里最大的数（**前驱**）顶替也可以。

**一个常见的错误：验证一棵树是不是 BST。** 很多人只检查「每个节点大于左孩子、小于右孩子」，这是不够的：

""" + C_VALID + r"""

那棵坏树里，4 比它的父节点 7 小，局部看没问题；但它在根 5 的**右**子树里，必须比 5 大。BST 的约束来自**所有祖先**，不只是父亲。正确的写法是递归时传下一个区间 `(lo, hi)`：进入左子树时上界收紧成当前值，进入右子树时下界收紧成当前值。也可以用中序遍历检查是否严格升序。
"""),
  V("mtvbVLK5xDQ", "视频三：Binary Search Trees (BST) Explained in Animated Demo（Programming and Math Tutorials）", 6),
  T(r"""
### BST 的问题：会长歪

BST 的复杂度是 $O(h)$，而不是 $O(\log n)$。如果插入的顺序很糟，树会变成一条**链**：

""" + C_HEIGHT + r"""

随机顺序插入 1000 个键，树高约 20（接近 $2\log_2n$，量级是 $\log n$）；而按升序插入，每个新键都比前面所有的大，一路往右挂，树高是 999，退化成一个**链表**，所有操作都变成 $O(n)$。现实里数据常常是「已经有序」或者「接近有序」的，所以朴素 BST 不能直接用。

### 平衡树与 AVL 树

> **标准定义 · AVL 树 (AVL tree)**
>
> **AVL 树**是**自平衡**的 BST：对每个节点，**左右子树的高度之差（平衡因子）的绝对值至多为 1**。每次插入或删除后，若某个节点失衡，就通过**旋转 (rotation)** 恢复平衡。旋转只改变常数个指针，$O(1)$，并且保持 BST 的性质。这保证了树高 $h=O(\log n)$，所以查找、插入、删除都是 $O(\log n)$。
>
> *English: An AVL tree is a self-balancing BST in which the heights of the two subtrees of every node differ by at most one; rotations restore balance after updates, guaranteeing O(log n) height.*

**白话版：长歪了就「扳」一下。** 旋转就像把一根太长的树枝折一下：右边太长，就把右孩子提上来当新的根（**左旋**），原来的根变成它的左孩子；左边太长则相反（**右旋**）。有两种「弯着长」的情形（左右型、右左型）需要旋转两次：先把里面那一层扳直，再扳外面。

""" + C_AVL + r"""

同样是顺序插入 1000 个键，AVL 树高只有 9（理论上最多约 $1.44\log_2n\approx14$），始终平衡；BST 的性质（中序有序）也保持了。实际使用中你不需要自己写 AVL：Python 标准库没有平衡树，但有 `bisect`（有序列表）和第三方的 `sortedcontainers`；C++/Java 里有现成的**红黑树 (red-black tree)**（比 AVL 更省旋转，用在 `std::map` / `TreeMap`）。你需要懂的是**为什么需要平衡，以及旋转保持了什么**。

> **常见的树结构一览**
>
> - **BST / AVL / 红黑树**：内存里的有序集合，$O(\log n)$ 查找、插入、删除。
> - **B 树 / B+ 树**：每个节点有很多孩子，用于数据库索引和文件系统，减少磁盘读取。
> - **堆 (heap)**：用来快速取最大 / 最小，下一节。
> - **字典树 (trie)**：按前缀组织字符串，用于自动补全、拼写检查。
> - **线段树、树状数组**：区间查询（竞赛里常见）。

### 这一节你要带走的三句话

1. **树是递归结构**，$n$ 个节点有 $n-1$ 条边；遍历有前序、中序、后序（DFS，栈 / 递归）和层序（BFS，队列），都是 $O(n)$。
2. **BST：左小右大，中序遍历是升序**；查找、插入、删除是 $O(h)$；删除有两个孩子的节点用后继顶替；验证 BST 要传区间。
3. **朴素 BST 顺序插入会退化成链（$h=n$）**；AVL / 红黑树用旋转保证 $h=O(\log n)$。
"""),
  V("1tp_ohWPWSs", "视频四：Understanding AVL Tree Rotations Visually（CodeAltus）", 4),
  THINK("一棵二叉树的前序遍历是 `[1, 2, 4, 5, 3]`，中序遍历是 `[4, 2, 5, 1, 3]`。能唯一确定这棵树吗？它长什么样？", r"""
**能。** 前序的第一个是根，所以根是 1。在中序里找到 1，它左边的 `[4, 2, 5]` 是左子树，右边的 `[3]` 是右子树。左子树的前序是 `[2, 4, 5]`（前序里 1 后面接着的 3 个），根是 2；在中序 `[4, 2, 5]` 里，2 的左边是 4、右边是 5。所以树是：根 1，左孩子 2（它的左孩子 4、右孩子 5），右孩子 3。

一般结论：**前序 + 中序**（或**后序 + 中序**）可以唯一确定一棵二叉树，原因就是前序（后序）告诉你根，中序告诉你左右子树的边界，然后递归。但**只有前序和后序不能唯一确定**（比如只有一个孩子时，不知道是左还是右）。
"""),
  THINK("一个 BST 里要找「第 $k$ 小的元素」，怎样利用中序遍历？如果这个查询要做很多次，应该怎样改进数据结构？", r"""
中序遍历得到升序序列，所以只要做中序遍历，数到第 $k$ 个就停下，时间 $O(h+k)$。（用迭代版中序，数到 $k$ 个就提前 `return`，不必走完整棵树。）

如果要做很多次，可以在每个节点额外存一个字段：**以它为根的子树的节点数 `size`**。查找第 $k$ 小时：设左子树大小为 $L$，若 $k\le L$ 就去左子树找第 $k$ 小；若 $k=L+1$ 就是当前节点；否则去右子树找第 $k-L-1$ 小。每一步排除一棵子树，$O(h)$，AVL 下就是 $O(\log n)$。这叫**顺序统计树 (order statistic tree)**。
"""),
  THINK("为什么说「BST 的中序遍历是升序」？这件事能用来快速验证一棵树是不是 BST 吗？", r"""
中序是「左、根、右」：先访问整个左子树（所有键都小于根），再访问根，再访问整个右子树（所有键都大于根），递归地对每个子树成立，所以得到的整个序列必然是升序。

反过来也成立：一棵二叉树，如果中序遍历得到的序列是**严格升序**的，那它就是 BST。所以验证 BST 还有一种写法：中序遍历时记住「上一个访问的值」，每访问一个新节点，都检查它是否严格大于上一个。比传区间的写法更简单，同样是 $O(n)$ 时间。
"""),
  THINK("AVL 树要求左右高度差不超过 1。这个条件为什么能推出树高是 $O(\\log n)$？", r"""
设 $N(h)$ 表示高度为 $h$ 的 AVL 树**最少**有多少个节点。要让节点尽量少，根的两棵子树高度要尽量悬殊：一棵高 $h-1$、另一棵高 $h-2$（差 1 是允许的上限），所以 $N(h)=1+N(h-1)+N(h-2)$，这是斐波那契型的递推，$N(h)$ 随 $h$ **指数增长**（约 $1.618^h$）。

反过来：$n$ 个节点的 AVL 树，$n\ge N(h)\approx1.618^h$，所以 $h\le\log_{1.618}n\approx1.44\log_2n$。树高是对数级的，这就是上面实验里 1000 个键只有 9 层的原因。
"""),
  KW(("树","tree","无环连通的结构；$n$ 个节点有 $n-1$ 条边"),
     ("根 / 叶子","root / leaf","没有父节点的节点 / 没有子节点的节点"),
     ("父节点 / 子节点","parent / child","相邻的上一层 / 下一层的节点"),
     ("深度","depth","从根到该节点的边数"),
     ("高度","height","从该节点到最远叶子的边数；树的高度 = 根的高度"),
     ("子树","subtree","一个节点连同它所有后代构成的树"),
     ("二叉树","binary tree","每个节点至多两个孩子：左孩子、右孩子"),
     ("前序 / 中序 / 后序","preorder / inorder / postorder","根左右 / 左根右 / 左右根，深度优先"),
     ("层序遍历","level-order traversal","一层层访问，用队列，广度优先"),
     ("二叉搜索树","binary search tree (BST)","左子树 < 根 < 右子树；中序遍历升序"),
     ("后继","successor","比当前键大的最小键，删除双孩子节点时用它顶替"),
     ("平衡因子","balance factor","左子树高度 − 右子树高度"),
     ("AVL 树","AVL tree","平衡因子绝对值不超过 1 的自平衡 BST，树高 $O(\\log n)$"),
     ("旋转","rotation","$O(1)$ 地改变几个指针来恢复平衡，保持 BST 性质"),
     ("红黑树","red-black tree","另一种自平衡 BST，$O(\\log n)$，用于 C++ `map`、Java `TreeMap`"),
  ),
 ],
 "references": [
  {"title": "Runestone：Trees（章节目录）", "url": "https://runestone.academy/ns/books/published/pythonds/Trees/index.html", "note": "本节的大纲依据，含树的术语、二叉树遍历、二叉搜索树与 AVL 树的 Python 实现（CC BY-NC-SA 4.0）"},
  {"title": "MIT OCW 6.006 Introduction to Algorithms（课程主页）", "url": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/", "note": "大学课程原版，含 BST 与 AVL 的严格分析，难度更高"},
  {"title": "Python 包 sortedcontainers 文档", "url": "https://grantjenks.com/docs/sortedcontainers/", "note": "Python 里实际常用的有序容器（SortedList / SortedDict），了解即可"},
 ],
 "quiz": {"questions": [
  Q("一棵有 $n$ 个节点的树，有多少条边？",
    ["$n$", "$n-1$", "$n+1$", "$2n$"], 1,
    "除根节点外，每个节点恰好有一条通向父节点的边，所以是 $n-1$ 条。"),
  Q("对一棵二叉搜索树做**中序遍历**，得到的是？",
    ["随机顺序", "从大到小", "一层一层的顺序", "从小到大（升序）"], 3,
    "中序「左、根、右」：先访问所有更小的，再根，再所有更大的，递归下去得到整体升序。"),
  Q("朴素 BST 的查找复杂度是？",
    ["$O(h)$：随机插入时 $h\\approx\\log n$，按顺序插入时 $h=n$", "永远是 $O(\\log n)$", "永远是 $O(n)$", "永远是 $O(1)$"], 0,
    "复杂度取决于树高。随机插入树高是对数级；顺序插入退化成链，树高是 $n$。AVL 树保证树高对数级。"),
  Q("删除一个有**两个孩子**的 BST 节点，标准做法是？",
    ["直接删除，让两个孩子都挂到它的父亲上", "删除它的父节点", "用它的后继（右子树的最小值）或前驱（左子树的最大值）的值替换它，再删除那个后继 / 前驱节点", "把整棵树重新建一遍"], 2,
    "后继是比当前键大的最小键，用它顶替后，左边仍然都小于它，右边仍然都大于它。后继最多有一个孩子，可以按简单情形删掉。"),
  Q("二叉树的**前序遍历**的访问顺序是？",
    ["左、根、右", "根、左、右", "左、右、根", "一层一层"], 1,
    "前序就是「根在前」：先根，再左子树，再右子树。左根右是中序，左右根是后序。"),
  Q("二叉树的**层序遍历**通常用什么结构实现？",
    ["队列", "栈", "堆", "哈希表"], 0,
    "一层一层地展开，先入队的先处理，用队列（先进先出）。DFS 的三种遍历才是用栈或递归。"),
  Q("高度（边数）为 $h$ 的二叉树，最多有多少个节点？",
    ["$2h$", "$h^2$", "$2^h$", "$2^{h+1}-1$"], 3,
    "第 0 层 1 个，第 1 层 2 个，……，第 $h$ 层 $2^h$ 个，总共 $1+2+\\dots+2^h=2^{h+1}-1$。这也说明 $n$ 个节点的树高至少是 $\\log_2n$ 的量级。"),
  Q("验证 BST 时，只检查「每个节点大于它的左孩子、小于它的右孩子」为什么不够？",
    ["因为太慢了", "因为孩子可能为空", "因为一个节点必须大于整个左子树、小于整个右子树，约束来自所有祖先，而不只是父亲", "因为 BST 允许有重复的键"], 2,
    "例如 5 的右子树里有 `7 → 4`，4 小于它的父亲 7，局部合法，但它在 5 的右子树里，必须大于 5。正确做法是递归时向下传一个 `(lo, hi)` 区间。"),
  Q("AVL 树的平衡条件是？",
    ["所有叶子在同一层", "每个节点的左右子树高度之差的绝对值至多为 1", "左子树的节点数等于右子树的节点数", "整棵树是满二叉树"], 1,
    "这是一个「局部」的、比满二叉树宽松得多的条件，但足以推出整棵树的高度是 $O(\\log n)$。"),
  Q("在 AVL 树里，查找、插入、删除的最坏时间复杂度是？",
    ["都是 $O(\\log n)$", "查找 $O(1)$，其他 $O(n)$", "插入 $O(n)$", "删除 $O(n\\log n)$"], 0,
    "树高始终是 $O(\\log n)$，每次操作沿着一条根到叶子的路径走，旋转本身是 $O(1)$，所以三者都是 $O(\\log n)$。"),
 ]},
}

if __name__ == '__main__':
    dump(unit, "dsa-0", "u07-trees-bst.json")
