"""dsa-0 第 4 节：哈希表与集合"""
from unitlib import *
from runlib import code

C_HASH = code('''
def my_hash(s, m):
    # 把字符串变成 0 ~ m-1 的桶编号：h = h*31 + 字符编码，每一步取余，防止数字越来越大
    h = 0
    for ch in s:
        h = (h * 31 + ord(ch)) % m
    return h

names = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Heidi"]
m = 8                                    # 8 个桶
for s in names:
    print(f"{s:<6} → 桶 {my_hash(s, m)}")
''')

C_CHAIN = code('''
import random

class ChainMap:
    # 链地址法 (separate chaining)：每个桶是一个小列表，哈希到同一桶的键都放进去
    def __init__(self, m=4):
        self.m = m
        self.buckets = [[] for _ in range(m)]
        self.n = 0
        self.resizes = 0

    def _idx(self, key):
        return hash(key) % self.m                    # 哈希值 → 桶编号

    def put(self, key, val):
        b = self.buckets[self._idx(key)]
        for i, (k, v) in enumerate(b):               # 先看键是否已存在，存在就覆盖
            if k == key:
                b[i] = (key, val)
                return
        b.append((key, val))
        self.n += 1
        if self.n / self.m > 0.75:                   # 装载因子 n/m 超过 0.75 就扩容
            self._resize()

    def get(self, key, default=None):
        for k, v in self.buckets[self._idx(key)]:    # 只需要在一个桶里找，不用全表扫描
            if k == key:
                return v
        return default

    def _resize(self):
        old = [kv for b in self.buckets for kv in b]
        self.m *= 2                                  # 桶数翻倍，所有元素重新分配（rehash）
        self.buckets = [[] for _ in range(self.m)]
        self.n = 0
        self.resizes += 1
        for k, v in old:
            self.put(k, v)

random.seed(0)
d = ChainMap()
keys = [random.randint(0, 10**6) for _ in range(1000)]
for k in keys:
    d.put(k, k * 2)
print("元素数", d.n, " 桶数", d.m, " 扩容次数", d.resizes)
print("装载因子", round(d.n / d.m, 2), " 最长的链", max(len(b) for b in d.buckets))
print("查找：", d.get(keys[0]) == keys[0] * 2, d.get(-1, "没有这个键"))
''')

C_PROBE = code('''
import random

def probe_insert(table, key):
    # 开放寻址 (open addressing) 的线性探测：位置被占了，就往后找下一个空位
    m = len(table)
    i = hash(key) % m
    steps = 1
    while table[i] is not None:
        i = (i + 1) % m
        steps += 1
    table[i] = key
    return steps

# 先看「聚集」：这些键本来想去同一个位置，结果越排越长
table = [None] * 10
print([probe_insert(table, k) for k in (5, 15, 25, 35, 6)])
print(table)

# 再看装载因子对速度的影响：表有 1000 个位置，填到不同的满度，平均每次插入要探测几次
random.seed(0)
for load in (0.5, 0.75, 0.9, 0.99):
    table = [None] * 1000
    total = 0
    for _ in range(int(1000 * load)):
        total += probe_insert(table, random.randrange(10**9))    # 随机整数键
    print(f"装载因子 {load}：平均探测 {total / int(1000 * load):.1f} 次")
''')

C_BAD = code('''
class Key:
    eq_calls = 0                                         # 统计「比较两个键是否相等」的次数
    def __init__(self, v, bad):
        self.v, self.bad = v, bad
    def __hash__(self):
        return 0 if self.bad else hash(self.v)           # bad=True：所有键的哈希值都一样
    def __eq__(self, other):
        Key.eq_calls += 1
        return self.v == other.v

for bad in (False, True):
    for n in (200, 400, 800):
        Key.eq_calls = 0
        d = {}
        for i in range(n):
            d[Key(i, bad)] = i                           # 插入 n 个键
        label = "哈希值全相同" if bad else "哈希值正常  "
        print(f"{label} n={n:<4} 比较次数 {Key.eq_calls}")
''')

C_HASHABLE = code('''
for key in [(1, 2), "abc", 3.5, frozenset({1, 2})]:
    d = {key: 1}                                         # 这些都可以当字典的键
    print(type(key).__name__, "可以")

for bad in ([1, 2], {1, 2}, {"a": 1}):
    try:
        {bad: 1}
    except TypeError as e:
        print(type(bad).__name__, "不行：", e)
''')

C_USE = code('''
from collections import Counter, defaultdict
import random

# 1. 数频率
words = "the cat and the hat and the bat".split()
print(Counter(words).most_common(2))

# 2. 两数之和（无序数组，O(n)）：字典记住「见过的数 → 下标」
def two_sum(a, target):
    seen = {}
    for i, x in enumerate(a):
        if target - x in seen:                           # 需要的那个数以前见过吗？O(1)
            return seen[target - x], i
        seen[x] = i

print(two_sum([2, 7, 11, 15], 9))

# 3. 字母异位词分组：排序后的字母一样，就是一组
groups = defaultdict(list)
for w in ["eat", "tea", "tan", "ate", "nat", "bat"]:
    groups["".join(sorted(w))].append(w)
print(list(groups.values()))

# 4. 和为 k 的连续子数组有几个？前缀和（上一节）+ 字典，O(n)
def subarray_sum(a, k):
    count, prefix, seen = 0, 0, {0: 1}                   # seen：每个前缀和出现过几次
    for x in a:
        prefix += x
        count += seen.get(prefix - k, 0)                 # 以当前位置结尾，需要的前缀和出现过几次
        seen[prefix] = seen.get(prefix, 0) + 1
    return count

def brute(a, k):                                         # 暴力法 O(n²)，用来对照
    return sum(1 for i in range(len(a)) for j in range(i, len(a)) if sum(a[i:j + 1]) == k)

print(subarray_sum([1, 2, 3, -3, 3], 3))
random.seed(0)
tests = ([random.randint(-3, 3) for _ in range(random.randint(0, 10))] for _ in range(1000))
print("1000 组随机数据，和暴力法一致：", all(subarray_sum(a, 3) == brute(a, 3) for a in tests))
''')

unit = {
 "id": "u04",
 "title": "哈希表与集合",
 "en": "Hash Tables & Sets",
 "minutes": 75,
 "objectives": [
  "说出 **哈希函数 (hash function)**、**哈希表 (hash table)**、**碰撞 (collision)**、**装载因子 (load factor)** 的定义",
  "理解 **链地址法 (chaining)** 与 **开放寻址 (open addressing)** 两种解决碰撞的方法，并会手写前者",
  "解释为什么哈希表的查找「平均 $O(1)$、最坏 $O(n)$」，以及为什么要在装满之前扩容",
  "知道 Python 里哪些对象可以当字典的键（**可哈希 hashable**），为什么 list 不行",
  "会用 `dict` / `set` / `Counter` 把常见问题降到 $O(n)$：词频、两数之和、分组、前缀和 + 字典",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

前面的数据结构里，「按位置找」很快（数组 $O(1)$），但「按内容找」很慢（$O(n)$ 挨个比）。哈希表解决的是后者：**给我一个键 (key)，直接告诉我它在哪里**，平均只要 $O(1)$。Python 的 `dict` 和 `set` 都是哈希表，它们可能是你写 Python 时用得最多的两个数据结构。

**学完它你就能看懂这几件事：**

- 为什么 `x in set` 比 `x in list` 快几个数量级（前面第 1 节反复提到的那条）；
- 为什么 `dict` 的键必须是**不可变**的，为什么 list 不能做键；
- 面试和数据处理里「用字典记录见过的东西」这一大类技巧；
- 机器学习里的 **词表 (vocabulary)**（词到编号的映射）、**特征哈希 (feature hashing)**（把高维稀疏特征哈希到固定长度）和 **嵌入表 (embedding table)** 的查表思想。

**本节安排（约 75 分钟）**：导读与哈希函数（12 分钟）→ 视频一（14 分钟）→ 碰撞与链地址法（15 分钟）→ 视频二（8 分钟）→ 开放寻址（10 分钟）→ 视频三（11 分钟，选看）→ 最坏情况与可哈希（7 分钟）→ 应用（8 分钟）→「想一想」。

### 哈希函数与哈希表

> **标准定义 · 哈希函数 (hash function) 与哈希表 (hash table)**
>
> **哈希函数** $h$ 把任意一个键映射成一个整数（哈希值）。**哈希表**用一个长度为 $m$ 的数组，把键 $k$ 存放在位置 $h(k)\bmod m$（该位置称为一个 **桶 (bucket)**），这样查找、插入、删除只需先算出位置，再去那里找。
>
> 好的哈希函数应当：**确定性**（同一个键永远得到同一个值）、**计算快**、**分布均匀**（不同的键尽量落在不同的桶里）。并且，若 $a=b$（相等），则必须 $h(a)=h(b)$。
>
> *English: A hash function maps a key to an integer; a hash table stores each key in the bucket h(k) mod m, giving direct access to the likely location of the key.*

**白话版：像图书馆的索引卡。** 你想找一本叫《数据结构》的书，不用把整个图书馆走一遍，而是先用某个固定的规则（比如书名的第一个字的笔画数）算出它在第几号书架，直接去那个书架找。这个「规则」就是哈希函数，书架就是桶。

看一个字符串哈希的例子，规则是：每一步把当前结果乘以 31，再加上下一个字符的编码，最后取余，得到桶编号。

""" + C_HASH + r"""

注意输出里有没有两个名字落到了同一个桶：只有 8 个桶却有 8 个名字，**不同的键完全可能被映射到同一个桶**，这叫碰撞。

> **标准定义 · 碰撞 (collision) 与装载因子 (load factor)**
>
> 两个不同的键 $a\ne b$ 满足 $h(a)\bmod m=h(b)\bmod m$，称发生**碰撞**。碰撞不可避免（键的个数可以比桶多得多，这是**鸽巢原理**），哈希表的设计就是要处理好它。**装载因子** $\alpha=n/m$ 是元素个数与桶数之比，衡量表有多满。
>
> *English: A collision occurs when two distinct keys map to the same bucket. The load factor α = n/m is the ratio of stored elements to buckets.*

**白话版：「撞车」不可怕，关键是怎么处理。** 两种主流做法，下面分别看。
"""),
  V("KyUTuwz_b7Q", "视频一：Hash Tables and Hash Functions（Computer Science Lessons）", 14),
  T(r"""
### 解决碰撞一：链地址法

> **标准定义 · 链地址法 (separate chaining)**
>
> 每个桶存放一个**链表（或小列表）**，所有哈希到该桶的键值对都放在这个链里。查找时先算出桶，再在链里线性查找。若装载因子为 $\alpha$，哈希函数分布均匀，则一次查找平均需要检查约 $1+\alpha$ 个元素。
>
> *English: In separate chaining, each bucket holds a list of all entries that hash to it.*

**白话版：同一个书架上，再叠着放。** 书架（桶）上的书太多，就叠成一摞，找的时候在这一摞里翻。只要书架数量够多、书分得够匀，每一摞都很短，几乎一步就能找到。

下面是一个完整的实现，包括**扩容 (resizing)**：装载因子超过 0.75 就把桶数翻倍，并把所有元素重新分配到新桶里（这叫 **重新哈希 rehash**）。

""" + C_CHAIN + r"""

1000 个随机整数键（有少量重复，实际存入 998 个不同的键）一路扩容了 9 次，桶数变成 2048，装载因子 0.49，最长的链只有 4 个元素，说明元素分布很均匀。**扩容的意义**：不扩容的话，$m$ 固定，元素越来越多，$\alpha$ 越来越大，每个桶的链越来越长，最后退化成 $O(n)$ 的线性查找。每次扩容代价是 $O(n)$，但因为桶数翻倍，两次扩容之间能插入的元素越来越多，**摊还下来每次插入仍然是 $O(1)$**，这和上一节动态数组完全是同一个论证。
"""),
  V("T9gct6Dx-jo", "视频二：Hash table separate chaining（WilliamFiset）", 8),
  T(r"""
### 解决碰撞二：开放寻址

> **标准定义 · 开放寻址 (open addressing) 与线性探测 (linear probing)**
>
> 所有元素都直接存放在数组里（不用链表）。若 $h(k)\bmod m$ 位置被占用，就按某种规则**探测 (probe)** 下一个位置。**线性探测**依次尝试 $i,i+1,i+2,\dots$（取余绕圈），直到找到空位。查找时沿着同样的探测序列走，遇到空位说明键不存在。删除时不能直接清空，要放一个**墓碑标记 (tombstone)**，否则会截断后面元素的探测链。
>
> *English: In open addressing, all entries live in the array itself; a collision is resolved by probing other slots in a fixed sequence.*

**白话版：位置被占了就往后找空位。** 像电影院坐座位：你订的座位被人坐了，就往右顺延到第一个空位。好处是不用额外的链表，内存紧凑、缓存友好（Python 的 `dict` 底层就是开放寻址的一种变体）。坏处是**聚集 (clustering)**：连成一片的被占位置越来越长，新来的键一撞上就要穿过整片。

""" + C_PROBE + r"""

第一行：键 5、15、25、35 的桶编号都是 5，所以需要的探测次数依次是 1、2、3、4，它们在表里占了连续的位置 5、6、7、8；然后键 6 本来该去位置 6，却要一路探测到位置 9。**碰撞会「传染」。**

第二行是核心结论：装载因子 0.5 时平均探测约 1.5 次，0.75 时约 2.8 次，0.9 时约 5 次，**到 0.99 时升到约 18 次**（这是整个填表过程的平均值，快填满时单次插入要探测的次数还要多得多）。所以开放寻址的表绝对不能装得太满，一般在装载因子到 $2/3$ 左右就扩容。

| | 链地址法 | 开放寻址（线性探测） |
|---|---|---|
| 存储 | 每桶一个链表，有额外指针 | 全在数组里，紧凑 |
| 装载因子可以超过 1 吗 | 可以（链变长） | **不行**（最多填满） |
| 对哈希函数的敏感度 | 较低 | 较高（容易聚集） |
| 删除 | 直接从链里删 | 需要墓碑标记 |
| 缓存友好 | 一般 | 好 |
"""),
  V("xIejolxzZS8", "视频三（选看）：Hash table open addressing（WilliamFiset）", 11),
  T(r"""
### 最坏情况：为什么是「平均 $O(1)$」

哈希表的 $O(1)$ 是**平均情况**，前提是哈希函数把键分布得比较均匀。如果有人故意（或碰巧）让大量键有相同的哈希值，所有键都挤在同一个桶（或同一条探测链）里，查找就退化成 $O(n)$。用 Python 自己的 `dict` 验证，数「比较两个键是否相等」的次数（不同 Python 版本的具体数字可能略有差别，但量级一致）：

""" + C_BAD + r"""

哈希值正常时，插入 $n$ 个键几乎不需要比较键是否相等；哈希值全相同时，比较次数约是 $n^2/2$：$n$ 翻倍，次数变成 4 倍，这就是 $O(n^2)$ 的总代价。这件事也是一类真实的安全问题（**哈希碰撞攻击**）：攻击者构造一批哈希值相同的键发给服务器，让它的哈希表退化。所以 Python 对字符串的哈希值每次运行都会加一个随机的「盐」（salt），你每次运行程序打印 `hash("abc")` 会得到不同的值。

### 什么样的对象可以当键：可哈希

> **标准定义 · 可哈希 (hashable)**
>
> 一个对象是**可哈希的**，如果它的哈希值在生命周期内**永不改变**，并且可以和别的对象比较相等。在 Python 里，不可变对象（`int`、`float`、`str`、`tuple`（元素也要可哈希）、`frozenset`）是可哈希的；可变容器（`list`、`set`、`dict`）不可哈希。
>
> *English: A hashable object has a hash value that never changes during its lifetime and can be compared for equality.*

**白话版：键不能「变脸」。** 如果允许 list 做键：你把 `[1,2]` 放进字典，位置是根据它的哈希值算出来的；之后你把这个 list 改成 `[1,3]`，它的哈希值变了，但字典里它还待在老位置，再也找不到了。所以只允许不可变的对象做键。

""" + C_HASHABLE + r"""

### 用字典 / 集合解决问题

哈希表在算法里的作用一句话概括：**用 $O(1)$ 的查找，换掉一层循环**。

""" + C_USE + r"""

最后一个例子把上一节的前缀和和这一节的字典结合起来：以当前位置结尾、和为 $k$ 的子数组个数，等于「之前有多少个前缀和等于 $\text{prefix}-k$」。每个位置只需要一次字典查询，整体 $O(n)$，而暴力法是 $O(n^2)$ 或更差。

### 集合 `set`

`set` 就是**只有键、没有值**的哈希表：不重复、无序、`in` 判断 $O(1)$。常用的集合运算也都是线性时间：`a & b`（交集）、`a | b`（并集）、`a - b`（差集），做「去重」「求共同元素」特别方便。

### 这一节你要带走的三句话

1. **哈希表 = 数组 + 哈希函数**：用键算出位置，查找、插入、删除平均 $O(1)$；最坏情况（大量碰撞）退化成 $O(n)$。
2. **碰撞不可避免**：链地址法（桶里挂列表）和开放寻址（往后找空位）；装载因子太大要**扩容 + 重新哈希**，摊还仍是 $O(1)$。
3. **键必须不可变（可哈希）**；用字典记住「见过的东西」，是把 $O(n^2)$ 降到 $O(n)$ 最常用的手法。
"""),
  THINK("为什么扩容时要把所有元素**重新计算位置**，而不能直接把旧数组原样复制到新的更大的数组里？", r"""
因为元素的位置是 $h(k)\bmod m$，**依赖桶数 $m$**。$m$ 变了，同一个键 $k$ 对应的位置也变了，旧位置不再是它「应该在」的位置。如果只是把旧数组原样复制，查找时会按新的 $m$ 算出一个位置，却发现那里没有它。

所以必须对每个元素重新取余、重新放置（rehash），代价是 $O(n)$；但像动态数组一样，扩容是按倍数发生的，总代价摊还下来每次插入仍是 $O(1)$。
"""),
  THINK("如果你让自己定义的类的对象当字典的键，实现了 `__eq__` 但是没有实现 `__hash__`，会发生什么？为什么 Python 要这样设计？", r"""
Python 会把这个类的 `__hash__` 自动设为 `None`，也就是**这个类的对象变成不可哈希的**，当键时会抛出 `TypeError: unhashable type`。

原因是哈希表有一条基本约定：**相等的对象必须有相同的哈希值**（`a == b` 则 `hash(a) == hash(b)`）。你改写了「什么叫相等」，Python 就无法再保证默认的哈希值（基于对象身份）仍然满足这条约定，所以保守地禁止哈希。要让它可哈希，需要你**同时**实现 `__hash__`，并保证用于比较相等的那些字段，也被用来计算哈希值，并且这些字段在对象的生命周期内不变。
"""),
  THINK("你要在一个 100 万条记录的列表里，反复判断某个 ID 是否存在。方案 A：每次用 `x in list`；方案 B：先转成 `set`。查询次数在什么范围内，方案 B 才值得？", r"""
转成集合的一次性代价是 $O(n)$（约 100 万步）；之后每次查询 $O(1)$。方案 A 每次查询 $O(n)$。

只查一次的话，方案 A 是 $O(n)$，方案 B 也是 $O(n)$（建集合）加 $O(1)$，两者差不多，B 反而多用了内存。**只要查询两次以上，B 就开始占优**；查询次数 $q$ 很大时，A 总共是 $O(nq)$，B 是 $O(n+q)$，差别巨大。而且 $n$ 越大、$q$ 越多，B 越划算。代价是 $O(n)$ 的额外内存，以及元素必须可哈希。这是「预处理 + 多次查询」模式的典型例子，和前缀和一样。
"""),
  KW(("哈希函数","hash function","把键映射成整数；确定性、快、分布均匀"),
     ("哈希表","hash table","用 $h(k)\\bmod m$ 定位的数组；查找平均 $O(1)$"),
     ("桶","bucket","哈希表中的一个位置"),
     ("碰撞","collision","两个不同的键落进同一个桶"),
     ("装载因子","load factor","$\\alpha=n/m$，元素数 / 桶数"),
     ("链地址法","separate chaining","每个桶挂一个列表，碰撞的键都放进去"),
     ("开放寻址","open addressing","所有元素都在数组里，位置被占了就按规则找下一个"),
     ("线性探测","linear probing","依次尝试 $i,i+1,i+2,\\dots$"),
     ("聚集","clustering","连续被占的位置越来越长，探测变慢"),
     ("墓碑标记","tombstone","开放寻址里删除元素时留下的标记，避免截断探测链"),
     ("重新哈希","rehash","扩容后按新的桶数重新计算每个元素的位置"),
     ("可哈希","hashable","哈希值不变且可比较相等；不可变对象才可哈希"),
     ("集合","set","只有键的哈希表，去重、无序、`in` 是 $O(1)$"),
     ("哈希碰撞攻击","hash collision attack","构造大量同哈希值的键，让哈希表退化成 $O(n)$"),
  ),
 ],
 "references": [
  {"title": "Runestone：Sorting and Searching — Hashing", "url": "https://runestone.academy/ns/books/published/pythonds/SortSearch/Hashing.html", "note": "本节的大纲依据，含余数哈希、折叠、线性探测与再散列（CC BY-NC-SA 4.0）"},
  {"title": "MIT 6.006 Lecture 8：Hashing with Chaining（课程原视频，约 51 分钟，选看）", "url": "https://www.youtube.com/watch?v=0M_kIqhwbFo", "note": "含全域哈希与链地址法平均复杂度的严格推导"},
  {"title": "Python 文档：Mapping Types — dict", "url": "https://docs.python.org/3/library/stdtypes.html#mapping-types-dict", "note": "dict 的全部方法；注意 3.7 起 dict 保持插入顺序"},
 ],
 "quiz": {"questions": [
  Q("哈希表的查找（在哈希函数分布均匀的前提下）的复杂度是？",
    ["$O(n)$", "$O(\\log n)$", "$O(n\\log n)$", "平均 $O(1)$，最坏 $O(n)$"], 3,
    "平均情况下一次计算位置就能找到，$O(1)$；如果大量键碰撞到同一个位置，会退化成 $O(n)$。"),
  Q("哈希表里的「碰撞」指的是什么？",
    ["两个键的值相同", "两个不同的键被映射到了同一个桶（位置）", "哈希函数计算出错", "表被装满了"], 1,
    "碰撞是不同的键得到相同位置。由于键的个数可以远多于桶，碰撞不可避免，所以必须有处理办法。"),
  Q("Python 的 `list` 不能做字典的键，主要是因为？",
    ["list 太长", "list 的比较速度太慢", "list 是可变的，内容改变后哈希值会变，会导致在表里找不到它", "list 没有 `__len__` 方法"], 2,
    "键的位置由它的哈希值决定。如果键可变，改了内容后哈希值变化，但它仍然待在旧位置，再也找不到了。所以只有不可变（可哈希）的对象能做键。"),
  Q("哈希表的「装载因子」是指？",
    ["元素个数 / 桶的数量", "桶的数量 / 元素个数", "最长的那条链的长度", "发生碰撞的次数"], 0,
    "$\\alpha=n/m$。它越大，说明表越满，碰撞越多，所以要在超过某个阈值时扩容。"),
  Q("链地址法中，装载因子为 $\\alpha$、哈希函数分布均匀时，每个桶的链平均长度大约是？",
    ["1", "$\\log\\alpha$", "$\\alpha$", "$\\alpha^2$"], 2,
    "$n$ 个元素均匀分到 $m$ 个桶，每个桶平均 $n/m=\\alpha$ 个元素。所以一次查找平均看 $1+\\alpha$ 个元素，只要 $\\alpha$ 保持为常数，就是 $O(1)$。"),
  Q("开放寻址（线性探测）的表装载因子接近 1 时会怎样？",
    ["性能不变", "探测次数急剧增大，所以要在装满之前就扩容", "查找变成 $O(\\log n)$", "元素会被自动删除"], 1,
    "表快满时，几乎每个位置都被占，每次插入、查找都要探测很多次。上面的实验里装载因子 0.99 时平均要探测约 18 次，而 0.5 时只要 1.5 次。"),
  Q("哈希表扩容时每次把桶数翻倍，整体的插入为什么仍然是摊还 $O(1)$？",
    ["扩容不需要复制元素", "扩容永远不会发生", "每次只增加一个桶", "各次扩容的代价是一个等比数列，加起来是 $O(n)$，平摊到每次插入是常数"], 3,
    "扩容一次的代价与当前元素数成正比，但扩容越来越少见，总和 $1+2+4+\\dots+n/2<n$，平摊到 $n$ 次插入是 $O(1)$，和动态数组是同一个论证。"),
  Q("如果所有键的哈希值都相同，往哈希表里插入 $n$ 个键的总代价是？",
    ["$O(n^2)$", "$O(n)$", "$O(1)$", "$O(n\\log n)$"], 0,
    "所有键挤在同一条链（或探测序列）上，第 $k$ 个键要和前面 $k-1$ 个比较，总共 $n(n-1)/2$ 次，$O(n^2)$。上面的实验里 $n$ 翻倍，比较次数变成约 4 倍。"),
  Q("给一个**无序**数组，要在 $O(n)$ 时间内找到两个数之和等于 target，最合适的做法是？",
    ["双指针（直接用）", "先排序，再二分", "用字典记录已经见过的数，每一步查 `target - x` 是否出现过", "三层循环"], 2,
    "字典查找是 $O(1)$，一次遍历 $O(n)$。双指针需要数组有序；先排序是 $O(n\\log n)$。"),
  Q("对哈希表来说，若两个对象 `a == b` 为真，对它们的哈希值有什么要求？",
    ["`hash(a)` 和 `hash(b)` 可以不同", "必须有 `hash(a) == hash(b)`", "没有任何要求", "两者的哈希值必须都是 0"], 1,
    "这是哈希表正确工作的基本约定：相等的键必须落在同一个位置，否则会出现「明明放进去了却找不到」。所以自定义 `__eq__` 时也必须相应地定义 `__hash__`。"),
 ]},
}

if __name__ == '__main__':
    dump(unit, "dsa-0", "u04-hash-tables.json")
