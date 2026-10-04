"""py-0 第 6 节的小项目：写出项目文件，真实运行，收集输出（正文引用的都是真实输出）"""
import subprocess, sys, tempfile, re, json, textwrap
from pathlib import Path

FILES = {}

FILES["knn/__init__.py"] = '''"""一个只用标准库实现的 k 近邻分类器。"""
'''

FILES["knn/data.py"] = '''"""数据：样本、数据集（CSV 读取、划分训练 / 测试集）。"""
import csv
import random
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

    def split(self, test_ratio: float, seed: int) -> tuple["Dataset", "Dataset"]:
        """随机划分；同一个 seed 得到同样的划分（可复现）。"""
        if not 0 < test_ratio < 1:
            raise ValueError("test_ratio 必须在 0 和 1 之间")
        idx = list(range(len(self)))
        random.Random(seed).shuffle(idx)
        n_test = int(len(idx) * test_ratio)
        test = [self[i] for i in idx[:n_test]]
        train = [self[i] for i in idx[n_test:]]
        return Dataset(train), Dataset(test)
'''

FILES["knn/model.py"] = '''"""模型：k 近邻分类器。"""
import heapq
import math
from collections import Counter

from .data import Dataset


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
        votes = Counter(label for _, _, label in nearest)
        top = max(votes.values())
        for _, _, label in nearest:          # 平票时，选「得票最多的标签里最近的那个」
            if votes[label] == top:
                return label
        raise AssertionError("不可能到达这里")

    def predict(self, xs: list[tuple[float, ...]]) -> list[str]:
        return [self.predict_one(x) for x in xs]
'''

FILES["knn/metrics.py"] = '''"""评估指标。"""
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
'''

FILES["tests/__init__.py"] = ""

FILES["gen_data.py"] = '''"""生成三个高斯团的人工数据并存成 CSV（用固定种子，保证每次一样）。"""
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
'''

FILES["train.py"] = '''"""命令行入口：读数据 -> 划分 -> 训练 -> 评估 -> 保存结果。"""
import argparse
import json
import logging
from pathlib import Path

from knn.data import Dataset
from knn.metrics import accuracy, confusion
from knn.model import KNN

log = logging.getLogger("train")


def run(data: str, k: int, test_ratio: float, seed: int) -> dict:
    ds = Dataset.from_csv(data)
    train, test = ds.split(test_ratio, seed)
    log.info("样本总数 %d：训练 %d，测试 %d", len(ds), len(train), len(test))
    model = KNN(k).fit(train)
    feats = lambda d: [s.features for s in d.samples]
    labels = lambda d: [s.label for s in d.samples]
    result = {
        "k": k,
        "seed": seed,
        "train_accuracy": accuracy(labels(train), model.predict(feats(train))),
        "test_accuracy": accuracy(labels(test), model.predict(feats(test))),
    }
    pred = model.predict(feats(test))
    result["confusion"] = {f"{t}->{p}": n for (t, p), n in sorted(confusion(labels(test), pred).items())}
    return result


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
'''

FILES["tests/test_knn.py"] = '''import csv
import tempfile
import unittest
from pathlib import Path

from knn.data import Dataset, Sample
from knn.metrics import accuracy
from knn.model import KNN


def tiny():
    return Dataset([Sample((0.0, 0.0), "a"), Sample((0.1, 0.0), "a"),
                    Sample((5.0, 5.0), "b"), Sample((5.1, 5.0), "b")])


class TestKNN(unittest.TestCase):
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

    def test_invalid_k(self):
        with self.assertRaises(ValueError):
            KNN(k=0)

    def test_predict_before_fit(self):
        with self.assertRaises(RuntimeError):
            KNN().predict_one((0.0, 0.0))


class TestData(unittest.TestCase):
    def test_split_is_reproducible_and_disjoint(self):
        ds = Dataset([Sample((float(i),), "a") for i in range(20)])
        tr1, te1 = ds.split(0.25, seed=1)
        tr2, te2 = ds.split(0.25, seed=1)
        self.assertEqual(tr1.samples, tr2.samples)
        self.assertEqual((len(tr1), len(te1)), (15, 5))
        self.assertFalse(set(tr1.samples) & set(te1.samples))
        _, te3 = ds.split(0.25, seed=2)
        self.assertNotEqual(te1.samples, te3.samples)

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


class TestMetrics(unittest.TestCase):
    def test_accuracy(self):
        self.assertAlmostEqual(accuracy(["a", "b", "a", "a"], ["a", "b", "b", "a"]), 0.75)
        with self.assertRaises(ValueError):
            accuracy(["a"], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
'''

OUT = {}

def _run(root, *args):
    r = subprocess.run([sys.executable, *args], cwd=root, capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()

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
    sweep = []
    for k in (1, 3, 5, 9, 15, 31):
        res = json.loads(_run(root, "-c", f"import json; from train import run; print(json.dumps(run('blobs.csv', {k}, 0.3, 0)))"))
        sweep.append((k, res["train_accuracy"], res["test_accuracy"]))
    OUT["sweep"] = sweep
    seeds = []
    for sd in range(5):
        res = json.loads(_run(root, "-c", f"import json; from train import run; print(json.dumps(run('blobs.csv', 5, 0.3, {sd})))"))
        seeds.append(res["test_accuracy"])
    OUT["seeds"] = seeds
    OUT["bad_k"] = _run(root, "train.py", "blobs.csv", "--k", "abc").splitlines()[-1]
    (root / "broken.csv").write_text("x1,x2,label\n1,2,A\n3,oops,B\n", encoding="utf-8")
    OUT["bad_csv"] = _run(root, "train.py", "broken.csv").splitlines()[-1]
    t = _run(root, "-m", "unittest", "discover", "-s", "tests", "-t", ".", "-v")
    t = re.sub(r"Ran (\d+) tests? in [\d.]+s", r"Ran \1 tests", t)
    OUT["tests"] = t
    # 故意引入 bug 让测试失败：平票时不按最近排序，直接返回第一个标签
    broken = FILES["knn/model.py"].replace("for _, _, label in nearest:          # 平票时，选「得票最多的标签里最近的那个」\n            if votes[label] == top:\n                return label", "for label in sorted(votes, reverse=True):\n            if votes[label] == top:\n                return label")
    assert broken != FILES["knn/model.py"]
    (root / "knn/model.py").write_text(broken, encoding="utf-8")
    t2 = _run(root, "-m", "unittest", "discover", "-s", "tests", "-t", ".")
    t2 = re.sub(r"Ran (\d+) tests? in [\d.]+s", r"Ran \1 tests", t2)
    OUT["tests_bug"] = "\n".join(l for l in t2.splitlines() if l.startswith(("FAIL", "AssertionError", "Ran", "FAILED", "OK")))

if __name__ == "__main__":
    for k, v in OUT.items():
        print("=====", k); print(v)
