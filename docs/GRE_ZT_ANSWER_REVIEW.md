# 张巍填空前50节答案校对

日期：2026-10-16。范围：`gre-zt`，Test 1–25，每个Test两个Section，共350题。

## 结论

本轮没有找到明确应改成另一组字母的答案，因此没有修改350题答案键。349题有明确的词义与上下文支持；1题存在选项版本问题，只能低把握保留，不能把它视为已完全确认。

逐题推理候选均与配套TXT一致，不等于350题获得ETS官方认证。第14节Q5的版本问题和若干原题措辞问题仍需保留说明。课程仍只有原题和答案，没有新增讲解或截图，其他课程截图保持原样。

## 方法与边界

- 逐题读完350题的题干和全部选项，单空看上下文，多空看逻辑及每列词义，六选二要求两项代入后句意相近。记录每题候选字母和一句理由。这不是遮住答案进行的盲审。
- 再从本地PDF重新提取这350题，核对课程中的题干、选项及顺序；逐项核对配套TXT及课程的零基下标。多空的D/E/F和G/H/I分别映射为第二、第三列的A/B/C。
- 对措辞不顺的疑难题回看原PDF页面，对部分题查询公开同题版本。没有获得ETS官方答案表，也没有把其他题库的答案当作官方认证。
- 全部PDF文字与课程相符，说明本轮未发现提取错位；这不能证明PDF原文自身无印刷或编写错误。未对350题逐字逐标点进行完整的页面视觉验收。
- 程序检查证明来源映射和记录完整，不证明英语题答案本身正确。语言判断依据在逐题记录中。

## 第14节Q5：须保留的版本疑问

位置：Test 7 · Section 2 · Q5。题意是保育项目报告近半来自同一州，样本地理范围缺少多样性。本地选项为rudimentary / interdependent / interrelated / complex / heterogeneous / dissimilar，配套答案BC。

本地六项中，BC是唯一能组成“相互关联”词对的选择，但interdependent比interrelated强，不能仅由同州报告充分推出“互相依赖”。按句意更自然的词是“范围受限”。

[考满分的相同题干](https://gre.kmf.com/explain/index/81w0ok)使用另一套选项，含circumscribed和restricted；[GRE Prep Club](https://gre.myprepclub.com/forum/the-book-brings-together-many-valuable-reports-on-conservation-project-30502.html)则使用与本地相同选项并给BC。因此不能直接把另一版DF答案搬过来，也不能宣称本地BC已确定无疑。本轮保留BC及原选项，单独标记低把握，不擅自替换成另一版原题。

课程目前仍按BC计分；本轮没有把这题标成“明确答案错误”，也没有关闭计分。若以后取得可靠原始版本，需整题核对后再决定是否替换选项与答案。

## 原PDF本身的措辞问题

以下均已回看相关PDF原页，课程不是在这些位置读错了文字。它们与“答案字母错误”分开处理；没有擅自改写题目。

| 课节 / 题号 | 问题 | 答案判断 |
|---|---|---|
| 第25节Q4 | appearing scientific investigation、great experiment’s mentoring等表达明显不顺 | commonsense empiricism与推测式思考对照，BD仍有支持 |
| 第32节Q3 | artifacts into objective importance的连接不自然 | 小物件从trivial变importance，BD仍可判断 |
| 第42节Q4 | deeply…conference连接不顺；enlivened by pleasantries与后面的sensory deprivation、only respite相冲突 | BEI由奢华场地、苦行议程与感官缓解的整体对照支持，但原文需要可靠版本校订 |
| 第46节Q4 | high level of mathematical theory与后文经验计算标准之间的连接不清楚 | BEH与题干所述“仅观测计算、排除强理论假说”的局部逻辑一致 |
| 第47节Q1 | to create them absent句尾不通顺 | D indispensable to是唯一与成功必需相符的选项；[同题页](https://gre.kmf.com/explain/index/0cw89k)也给D |

第42节的[新东方同题页](https://cc.xdf.cn/gre/201708/298360750.html)也包含上述不顺措辞。网络重复不能证明文字正确，因此不根据猜测自动补成unenlivened。

## 可复查记录

- `tools/course/grzt/reviewed-sections.tsv`：50节的350个推理候选及逐题理由。字母沿用PDF的A–I全局编号，不使用网页填空列的局部A/B/C。
- `docs/GRE_ZT_ANSWER_AUDIT.json`：350题的位置、来源答案、候选、状态、理由、PDF页码及来源哈希。
- `tools/course/grzt/review_answers.py`：重新核对以上记录、本地TXT、PDF文字和课程JSON；不会更改答案或向课程添加讲解。

本轮保持原来的无截图课程形式，回查页面只用于校对，不进入课程资源。
