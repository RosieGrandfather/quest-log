"""py-0 第 6 节：项目文件（一个文件一块，长文件拆成几块）+ 网页里可运行的小演示（Notebook）+ 真实运行整个项目并收集输出"""
import subprocess, sys, tempfile, re, json, textwrap
from pathlib import Path
from runlib import Notebook

# ───────────── 一、网页里可以运行的小演示（k-NN 的核心思想、划分）─────────────
nb = Notebook()

C_SYN = nb.cell('''
# 两个语法热身：嵌套解包、f-string 的格式说明
sample = ((0.0, 1.5), "A")                   # 一个元组：(特征, 标签)，特征本身又是一个元组
(a, b), tag = sample                         # 嵌套解包：左边的形状要和右边一样
print(a, b, tag)

pairs = [((0.0, 0.0), "A"), ((1.0, 0.0), "B")]
for i, (feat, lab) in enumerate(pairs):      # enumerate 给出 (下标, 元素)，元素又是 (特征, 标签)
    print(i, feat, lab)

v = 3.14159
print(f"{v:.3f}|{v:8.2f}|{7:<3}|{7:>3}|")    # .3f 三位小数；8.2f 占 8 格、两位小数；<3 左对齐占 3 格；>3 右对齐
''')

C_DIST = nb.cell('''
import heapq, math
from collections import Counter

# 5 个带标签的训练点 (特征, 标签)，和一个要分类的新点 x
train = [((0.0, 0.0), "A"), ((1.0, 0.0), "B"), ((1.2, 0.3), "B"), ((3.0, 3.0), "A"), ((3.5, 2.5), "C")]
x = (0.2, 0.0)

dists = [(math.dist(x, f), i, label) for i, (f, label) in enumerate(train)]   # (距离, 下标, 标签)
for d, i, label in sorted(dists):
    print(f"训练点 {i}  标签 {label}  距离 {d:.3f}")
''')

C_VOTE3 = nb.cell('''
nearest = heapq.nsmallest(3, dists)                  # 堆：取距离最小的 3 个，O(n log k)
print([(round(d, 3), i, label) for d, i, label in nearest])    # (距离, 下标, 标签)
votes = Counter(label for _, _, label in nearest)    # 哈希计数：统计每个标签的票数
print(votes)
print("k=3 的预测：", votes.most_common(1)[0][0])
''')

C_TIE = nb.cell('''
def predict(x, k, train):
    dists = [(math.dist(x, f), i, label) for i, (f, label) in enumerate(train)]
    nearest = heapq.nsmallest(k, dists)
    labels = [label for _, _, label in nearest]      # 按距离从近到远排好
    votes = Counter(labels)
    top = max(votes.values())
    for label in labels:                             # 平票时：得票最多的标签里，最近的那个
        if votes[label] == top:
            return label

for k in range(1, 6):
    print("k =", k, "->", predict(x, k, train))
''')

C_SELF = nb.cell('''
# 用训练集自己评估 1-NN：每个点自己就是自己最近的邻居（距离 0）
hits = [predict(f, 1, train) == label for f, label in train]
print(hits, "| 训练准确率 =", sum(hits) / len(hits))
''')

C_SPLIT = nb.cell('''
import random

def split(items, test_ratio, seed):
    idx = list(range(len(items)))
    random.Random(seed).shuffle(idx)                 # 固定种子的随机数发生器：同一个 seed 洗牌结果相同
    n_test = int(len(idx) * test_ratio)
    return [items[i] for i in idx[n_test:]], [items[i] for i in idx[:n_test]]

items = list(range(10))
tr1, te1 = split(items, 0.3, seed=1)
tr2, te2 = split(items, 0.3, seed=1)
_, te3 = split(items, 0.3, seed=2)
print(len(tr1), len(te1))
print("同一个种子，划分相同：", (tr1, te1) == (tr2, te2))
print("不同种子，测试集不同：", te1 != te3)
print("训练集与测试集没有交集：", not set(tr1) & set(te1))
''')

C_DICTCOMP = nb.cell('''
conf = {("A", "A"): 3, ("B", "C"): 1}        # 混淆矩阵的样子：(真实, 预测) -> 次数
print(sorted(conf.items()))                  # .items() 给出 (键, 值) 的配对，这里的键本身又是元组
print({f"{t}->{p}": n for (t, p), n in sorted(conf.items())})   # 字典推导式 + 嵌套解包
''')

# ───────────── 二、项目文件（每个键一个文件；值是「块」的列表，块之间拼起来就是完整文件）─────────────
PARTS = {}

PARTS["knn/__init__.py"] = ['''"""一个只用标准库实现的 k 近邻分类器。"""
''']

PARTS["knn/data.py"] = ['''"""数据：样本与数据集（从 CSV 读取）。"""
import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Sample:
    features: tuple[float, ...]
    label: str


class Dataset:
    def __init__(self, samples: list[Sample]) -> None:
        self.samples = list(samples)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, i: int) -> Sample:
        return self.samples[i]

    @classmethod
    def from_csv(cls, path: str | Path) -> "Dataset":
        """读取 CSV：最后一列叫 label，其余列都是数值特征。"""
        samples = []
        with open(path, encoding="utf-8", newline="") as f:
            for lineno, row in enumerate(csv.DictReader(f), start=2):
                label = row.pop("label")
                try:
                    features = tuple(float(v) for v in row.values())
                except ValueError as e:
                    raise ValueError(f"第 {lineno} 行含有非数字的特征：{row}") from e
                samples.append(Sample(features, label))
        return cls(samples)
''']

PARTS["knn/split.py"] = ['''"""划分训练集与测试集。"""
import random

from .data import Dataset


def train_test_split(ds: Dataset, test_ratio: float, seed: int) -> tuple[Dataset, Dataset]:
    """随机划分；同一个 seed 得到同样的划分（可复现）。"""
    if not 0 < test_ratio < 1:
        raise ValueError("test_ratio 必须在 0 和 1 之间")
    idx = list(range(len(ds)))
    random.Random(seed).shuffle(idx)
    n_test = int(len(idx) * test_ratio)
    test = [ds[i] for i in idx[:n_test]]
    train = [ds[i] for i in idx[n_test:]]
    return Dataset(train), Dataset(test)
''']

PARTS["knn/vote.py"] = ['''"""投票规则（单独成一个模块，方便单独检验）。"""
from collections import Counter


def majority_vote(labels: list[str]) -> str:
    """labels 按距离从近到远排列；返回得票最多的标签，平票时取其中最近的那个。"""
    votes = Counter(labels)
    top = max(votes.values())
    for label in labels:          # 平票时，选「得票最多的标签里最近的那个」
        if votes[label] == top:
            return label
    raise AssertionError("不可能到达这里")
''']

PARTS["knn/model.py"] = ['''"""模型：k 近邻分类器。"""
import heapq
import math

from .data import Dataset
from .vote import majority_vote


class KNN:
    def __init__(self, k: int = 3) -> None:
        if k < 1:
            raise ValueError("k 必须 >= 1")
        self.k = k
        self._train: Dataset | None = None

    def fit(self, dataset: Dataset) -> "KNN":
        if len(dataset) == 0:
            raise ValueError("训练集是空的")
        self._train = dataset
        return self

    def predict_one(self, x: tuple[float, ...]) -> str:
        if self._train is None:
            raise RuntimeError("请先调用 fit")
        # 取距离最小的 k 个：堆（heapq.nsmallest）是 O(n log k)；下标 i 用来在距离相同时稳定排序
        nearest = heapq.nsmallest(
            self.k,
            ((math.dist(x, s.features), i, s.label) for i, s in enumerate(self._train.samples)),
        )
        return majority_vote([label for _, _, label in nearest])

    def predict(self, xs: list[tuple[float, ...]]) -> list[str]:
        return [self.predict_one(x) for x in xs]
''']

PARTS["knn/metrics.py"] = ['''"""评估指标。"""
from collections import Counter


def accuracy(y_true: list[str], y_pred: list[str]) -> float:
    if len(y_true) != len(y_pred):
        raise ValueError(f"长度不一致：{len(y_true)} vs {len(y_pred)}")
    if not y_true:
        raise ValueError("没有样本")
    return sum(t == p for t, p in zip(y_true, y_pred)) / len(y_true)


def confusion(y_true: list[str], y_pred: list[str]) -> dict[tuple[str, str], int]:
    """(真实标签, 预测标签) -> 次数"""
    return dict(Counter(zip(y_true, y_pred)))
''']

PARTS["tests/__init__.py"] = [""]

PARTS["gen_data.py"] = ['''"""生成三个高斯团的人工数据并存成 CSV（用固定种子，保证每次一样）。"""
import csv
import random
import sys

CENTERS = {"A": (0.0, 0.0), "B": (3.0, 0.0), "C": (1.5, 2.5)}


def main(path: str, n_per_class: int = 100, seed: int = 0) -> None:
    rng = random.Random(seed)
    rows = []
    for label, (cx, cy) in CENTERS.items():
        for _ in range(n_per_class):
            rows.append((round(rng.gauss(cx, 1.0), 3), round(rng.gauss(cy, 1.0), 3), label))
    rng.shuffle(rows)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["x1", "x2", "label"])
        w.writerows(rows)


if __name__ == "__main__":
    main(sys.argv[1])
''']

PARTS["train.py"] = ['''"""命令行入口：读数据 -> 划分 -> 训练 -> 评估 -> 保存结果。"""
import argparse
import json
import logging
from pathlib import Path

from knn.data import Dataset
from knn.metrics import accuracy, confusion
from knn.model import KNN
from knn.split import train_test_split

log = logging.getLogger("train")


def run(data: str, k: int, test_ratio: float, seed: int) -> dict:
    ds = Dataset.from_csv(data)
    train, test = train_test_split(ds, test_ratio, seed)
    log.info("样本总数 %d：训练 %d，测试 %d", len(ds), len(train), len(test))
    model = KNN(k).fit(train)
    feats = lambda d: [s.features for s in d.samples]
    labels = lambda d: [s.label for s in d.samples]
    pred = model.predict(feats(test))
    return {
        "k": k,
        "seed": seed,
        "train_accuracy": accuracy(labels(train), model.predict(feats(train))),
        "test_accuracy": accuracy(labels(test), pred),
        "confusion": {f"{t}->{p}": n for (t, p), n in sorted(confusion(labels(test), pred).items())},
    }
''', '''

def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="train.py", description="k 近邻分类")
    p.add_argument("data", help="CSV 文件路径（最后一列 label）")
    p.add_argument("--k", type=int, default=5)
    p.add_argument("--test-ratio", type=float, default=0.3)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", default=None, help="把结果写成 JSON 文件")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = run(args.data, args.k, args.test_ratio, args.seed)
    log.info("训练准确率 %.3f，测试准确率 %.3f", result["train_accuracy"], result["test_accuracy"])
    if args.out:
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("结果已保存到 %s", args.out)


if __name__ == "__main__":
    main()
''']

PARTS["tests/test_knn.py"] = ['''import tempfile
import unittest
from pathlib import Path

from knn.data import Dataset, Sample
from knn.metrics import accuracy
from knn.model import KNN
from knn.split import train_test_split


def tiny():
    return Dataset([Sample((0.0, 0.0), "a"), Sample((0.1, 0.0), "a"),
                    Sample((5.0, 5.0), "b"), Sample((5.1, 5.0), "b")])


class TestPredict(unittest.TestCase):
    def test_predicts_nearest_class(self):
        m = KNN(k=1).fit(tiny())
        self.assertEqual(m.predict_one((0.2, 0.1)), "a")
        self.assertEqual(m.predict_one((4.0, 4.0)), "b")

    def test_majority_vote(self):
        ds = Dataset([Sample((0.0,), "a"), Sample((1.0,), "b"), Sample((1.1,), "b")])
        self.assertEqual(KNN(k=3).fit(ds).predict_one((0.0,)), "b")   # 3 个邻居里 b 占多数
        self.assertEqual(KNN(k=1).fit(ds).predict_one((0.0,)), "a")

    def test_tie_breaks_by_nearest(self):
        ds = Dataset([Sample((0.0,), "a"), Sample((1.0,), "b")])
        self.assertEqual(KNN(k=2).fit(ds).predict_one((0.4,)), "a")   # 平票：选更近的
''', '''

class TestErrors(unittest.TestCase):
    def test_invalid_k(self):
        with self.assertRaises(ValueError):
            KNN(k=0)

    def test_predict_before_fit(self):
        with self.assertRaises(RuntimeError):
            KNN().predict_one((0.0, 0.0))


class TestSplit(unittest.TestCase):
    def test_split_is_reproducible_and_disjoint(self):
        ds = Dataset([Sample((float(i),), "a") for i in range(20)])
        tr1, te1 = train_test_split(ds, 0.25, seed=1)
        tr2, te2 = train_test_split(ds, 0.25, seed=1)
        self.assertEqual(tr1.samples, tr2.samples)
        self.assertEqual((len(tr1), len(te1)), (15, 5))
        self.assertFalse(set(tr1.samples) & set(te1.samples))
        _, te3 = train_test_split(ds, 0.25, seed=2)
        self.assertNotEqual(te1.samples, te3.samples)
''', '''

class TestCsvAndMetrics(unittest.TestCase):
    def test_from_csv_and_bad_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good.csv"
            good.write_text("x1,x2,label\\n1,2,a\\n3,4,b\\n", encoding="utf-8")
            ds = Dataset.from_csv(good)
            self.assertEqual(len(ds), 2)
            self.assertEqual(ds[1], Sample((3.0, 4.0), "b"))
            bad = Path(tmp) / "bad.csv"
            bad.write_text("x1,x2,label\\n1,oops,a\\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                Dataset.from_csv(bad)

    def test_accuracy(self):
        self.assertAlmostEqual(accuracy(["a", "b", "a", "a"], ["a", "b", "b", "a"]), 0.75)
        with self.assertRaises(ValueError):
            accuracy(["a"], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
''']

FILES = {k: "".join(v) for k, v in PARTS.items()}

OUT = {}

def _run(root, *args):
    r = subprocess.run([sys.executable, *args], cwd=root, capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()

def _static(root, src, name="_cell.py"):
    """在项目目录里真实运行一小段代码，返回 ```python-static 块（只展示，网页里不运行；输出是真实输出）"""
    src = textwrap.dedent(src).strip("\n")
    (root / name).write_text(src + "\n", encoding="utf-8")
    out = _run(root, name)
    (root / name).unlink()
    return "```python-static\n" + src + "\n" + "".join(f"# 输出：{l}\n" for l in out.splitlines()) + "```"

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    for rel, src in FILES.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(src, encoding="utf-8")
    OUT["gen"] = _run(root, "gen_data.py", "blobs.csv")
    OUT["head"] = "\n".join((root / "blobs.csv").read_text().splitlines()[:4])
    OUT["nrows"] = len((root / "blobs.csv").read_text().splitlines()) - 1
    OUT["k5"] = _run(root, "train.py", "blobs.csv", "--k", "5", "--out", "result.json")
    OUT["json"] = (root / "result.json").read_text()
    OUT["k1"] = _run(root, "train.py", "blobs.csv", "--k", "1")
    OUT["k5_res"] = json.loads(OUT["json"])
    OUT["k1_res"] = json.loads(_run(root, "-c", "import json; from train import run; print(json.dumps(run('blobs.csv', 1, 0.3, 0)))"))
    S_SWEEP = _static(root, '''
        from train import run

        for k in (1, 3, 5, 9, 15, 31):
            r = run("blobs.csv", k, test_ratio=0.3, seed=0)      # 同一份划分，只改 k
            print(f"k={k:<3} 训练 {r['train_accuracy']:.3f}  测试 {r['test_accuracy']:.3f}")
    ''')
    S_SEEDS = _static(root, '''
        from train import run

        accs = [run("blobs.csv", k=5, test_ratio=0.3, seed=s)["test_accuracy"] for s in range(5)]
        print([round(a, 3) for a in accs])                      # 同一个模型，只换划分的种子
    ''')
    OUT["sweep"] = []
    for k in (1, 3, 5, 9, 15, 31):
        res = json.loads(_run(root, "-c", f"import json; from train import run; print(json.dumps(run('blobs.csv', {k}, 0.3, 0)))"))
        OUT["sweep"].append((k, res["train_accuracy"], res["test_accuracy"]))
    OUT["bad_k"] = _run(root, "train.py", "blobs.csv", "--k", "abc").splitlines()[-1]
    (root / "broken.csv").write_text("x1,x2,label\n1,2,A\n3,oops,B\n", encoding="utf-8")
    OUT["bad_csv"] = _run(root, "train.py", "broken.csv").splitlines()[-1]
    t = _run(root, "-m", "unittest", "discover", "-s", "tests", "-t", ".", "-v")
    t = re.sub(r"Ran (\d+) tests? in [\d.]+s", r"Ran \1 tests", t)
    OUT["tests"] = t
    # 故意引入 bug 让测试失败：平票时不按最近排序，按标签字母倒序选
    old = "    for label in labels:          # 平票时，选「得票最多的标签里最近的那个」\n"
    assert old in FILES["knn/vote.py"]
    broken = FILES["knn/vote.py"].replace(old, "    for label in sorted(votes, reverse=True):\n")
    (root / "knn/vote.py").write_text(broken, encoding="utf-8")
    t2 = _run(root, "-m", "unittest", "discover", "-s", "tests", "-t", ".")
    t2 = re.sub(r"Ran (\d+) tests? in [\d.]+s", r"Ran \1 tests", t2)
    OUT["tests_bug"] = "\n".join(l for l in t2.splitlines() if l.startswith(("FAIL", "AssertionError", "Ran", "FAILED", "OK")))

if __name__ == "__main__":
    for k, v in OUT.items():
        print("=====", k); print(v)
    for n in ("C_DIST","C_VOTE3","C_TIE","C_SELF","C_SPLIT","S_SWEEP","S_SEEDS"):
        print("#####", n); print(globals()[n])
    for k, v in PARTS.items():
        print(k, [len(c.strip("\n").split("\n")) for c in v])
