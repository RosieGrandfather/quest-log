# GRE Verbal 2025 第一节答案复核

2026-10-16；范围：1月14日 Verbal 1，12 题。根据题干、选项和文章独立解题，并对部分题使用公开同题资料交叉核对。**这不是 ETS 官方答案表**；尚未取得原 PDF 答案页，无法确认原错误产生于哪一步。

原先 10 道实际计分题的答案键全部错误；Q4 此前待核对、不计分，Q5 为选句子、自评。这足以导致正确作答也显示全错；没有读取用户真实作答，因此不能据此推算她的实际分数。

多空题以下按每一列各自 A/B/C 编号，与当前页面一致；若使用跨列 A–I 编号，第 2 题为 BF，第 3 题为 CDG。

| 题号 | 原答案 | 复核答案 | 依据 |
|---|---|---|---|
| 1 | C | B：subjective | 艺术的主观性与物理学回避内心思想相对照。 |
| 2 | C / A | B / C：deviates from / caricature | 避免以往的讽刺刻画，因此偏离传统。 |
| 3 | A / A / A | C / A / A | 科学很少名誉受损；法律玷污科学；科学制衡法律的不稳定性。 |
| 4 | 待核对；更早为不存在的 D | A、B | 不受文化传统限制，强调个人经历；未要求必须写成文字。 |
| 5 | 待核对，自评 | 第 3 句，Ralph Ellison’s definition… | 此句具体提出基于个人经历的另一种蓝调定义。 |
| 6 | B、D | E、F：disdain for / scorn for | 广泛涉猎与专业化相对，lordly 提示轻视。 |
| 7 | C、D | C、F：insufficient / meager | 证据不足却仍作概括；indirect 不等于不足。 |
| 8 | C、F | B、D：untenable / indefensible | 一概免责的立场将难以成立。 |
| 9 | C、F | B、E：demarcation of / lines between | 保护原则要求不同时代分界清楚。 |
| 10 | B | C | 介绍 Jeffrey 的研究并对照已有观点。 |
| 11 | A | D | 先前 scholars 举的是散发请愿书。 |
| 12 | E | B | 募捐集市支持 Jeffrey 对妇女边缘化说的反驳。 |

## 交叉核对资料

以下是培训机构同题资料，不能视为官方答案出处。答案措辞按本地原题核对，未复制机构解析。

- [Q1 考满分](https://gre.kmf.com/explain/question/d2cb7j-0.html?isFav=0)、[Q2 考满分](https://grev2.kmf.com/explain/question/22cb8j-0.html?isFav=0)、[Q3 考满分](https://gre.kmf.com/explain/question/02cbbj-0.html?isFav=0)
- [Q5 考满分](https://gre.kmf.com/explain/question/a2bruj-0.html?isFav=0)、[Q6 考满分](https://gre.kmf.com/explain/question/62e24j-0.html?isFav=0)、[Q7 新东方](https://bj.xdf.cn/wenzhang/xinwen/18199.html)
- [Q9 考满分](https://gre.kmf.com/explain/question/12cbej-0.html?isFav=0)、[Q10 考满分](https://gre.kmf.com/explain/index/d1pf4j)
- Q4、Q8、Q11、Q12 的答案依据来自本地原题的直接推理；本次未取得可核实的官方答案。

## 实现与验证

- 修正本节答案及生成源，保留旧答案于 `answerReview.previous`，Q4 更早的错误记录仍在 `legacyAnswer`。每题附独立复核中文依据，交卷后显示。
- 本节作答版本更新；后续已改为直接恢复上次选择，使用当前答案展示复核成绩、错题和依据，不要求重做。文字 v2 与本次答案修订版的选项顺序一致，可直接复核；更早无法确定映射的题单独保留原记录待核对。查看时不修改真实 Firebase 成绩、不增加作答次数，也不改积分。
- Q4 恢复计分；Q5 保留句子点选与自评，当前分母为 11。用按单词和句意选择的正确作答回归验证为 11/11；相同作答对旧的十道计分题为 0/10。
- 仅本节答案经过此次复核，不能据此认定其他 49 节答案可靠。没有改整体架构，未发布线上。
- 验证：`npm test` 74 项通过；本地 Edge 验证提交正确作答显示 11/11、Q4 计分、Q5 参考句、12 条交卷后依据、恢复上次作答、旧答案版本保护。保存使用模拟存储，没有写入真实账号。
