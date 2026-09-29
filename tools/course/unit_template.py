"""新章节模板。复制成 tools/course/uXX.py，改内容，运行：

  python tools/course/uXX.py

写作规范见 docs/COURSE_AUTHORING.md。下面每一部分都是必需的。
"""
from unitlib import *

unit = {
 "id": "u99",                       # 和 course.json 里的 id 一致
 "title": "中文标题",
 "en": "English Title",
 "minutes": 45,                     # 视频 + 阅读 ≈ 45 分钟
 # 3–4 条「学完这节你能……」，关键词写成 **中文 (English)**
 "objectives": [
  "理解 **某概念 (concept)** 是什么",
  "会用 …… 做 ……",
 ],
 "blocks": [
  # 1. 导读：为什么学这个（和 ARENA 原文 / 后面内容的联系）+ 本节时间安排
  T(r"""
### 为什么要学这个

（ARENA 在原文里怎么说、后面哪里会用到）

**本节安排（约 45 分钟）**：导读 → 视频一（N 分钟）→ 要点 → 视频二 → 要点和「想一想」。
"""),
  # 2. 视频：id 必须先用 yt.py verify 核实过；minutes 写四舍五入后的真实时长
  V("VIDEO_ID", "视频一：原标题（频道 / 系列 第几章）", 10),
  # 3. 要点：对照视频，用自己的话写；公式用 $...$；代码块里的输出必须是真跑出来的
  T(r"""
### 视频一要点

**1. ……**

$$公式$$
"""),
  # 4. 三个「想一想」：计算题 / 概念辨析 / 和深度学习的联系，各一个比较好
  THINK("问题？", r"""
参考答案。
"""),
  # 5. 关键词表：8–12 个
  KW(("中文", "English", "一句话说明"),),
 ],
 # 6. 参考资料：第一条放 ARENA 原文对应部分；链接都要能打开
 "references": [
  {"title": "ARENA [0.0] Prerequisites — 某部分", "url": ARENA_URL},
 ],
 # 7. 测验：正好 10 题、每题 4 个选项；正确答案分散在 0–3（每个位置最多 4 次）；
 #    讲解要说明为什么对、常见的错误选项错在哪
 "quiz": {"questions": [
  Q("题目？", ["选项 A", "选项 B", "选项 C", "选项 D"], 1, "讲解。"),
 ]},
}

if __name__ == '__main__':
    dump(unit, "arena-0.0", "u99-example.json")
