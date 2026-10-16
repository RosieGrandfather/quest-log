# GRE Verbal 2025：第一节原图与 OCR 校对

日期：2026-10-16。范围：`u01-2025-01-14-v1` 的全部 12 题。

方法：Windows 英文 OCR 重新识别 `img/2025-01-14/2-01.webp` 至 `2-12.webp`，再逐张目视对照原图。统一换行和排版空格，以 `____` 表示填空；不凭词典猜词，不调整选项顺序，不据语义擅自改答案。

## 核对结果

| 题号 | 原有问题及处理 |
|---|---|
| 1 | B/C 合并，末尾操作提示误入 E，导致 C–E 错位；恢复 accessible / subjective / enigmatic / detached / conceptual。 |
| 2 | 第二个空前多出句点；恢复 `(ii) ____.`。 |
| 3 | 原来只有图片；补全题干和三个空的三列选项。 |
| 4 | 已识别并对图校验，但原图是 3 选项多选，数据是 4 选项且答案为下标 3（D）；保留图片模式，文字转录见下，不发布不匹配的选项。 |
| 5 | 原图是选句子，数据误设为 5 选项单选、答案 E；后续按用户要求改为直接点选文章中的 5 个句子，补入完整文字，保留原图对照。答案待核对，按自评题不计分。 |
| 6 | 补回题干开头 `Hilton discusses the well-developed`；选项 `curiosity about` 恢复原图小写。 |
| 7 | 补回 `Although Wynne`；去掉多余句点和末尾伪填空。 |
| 8 | 题干与选项吻合，补回填空后的句末句点。 |
| 9 | 第一项 `changes within` 错入题干，底部提示错入末项；恢复原图 6 个选项及顺序，移除题干中的操作说明。 |
| 10 | 补齐阅读文章末句 `more directly than did integrated abolitionist groups.`；题干、选项吻合。 |
| 11 | 同上补齐共用文章末句；题干、选项吻合。 |
| 12 | 同上补齐共用文章末句；去掉题干开头 `ill` 并修复引号。 |

首次校对修正 10 题文字；后续补入第 5 题，现有 11 题提供文字。网页章节 JSON、OCR 数据源及题型生成源均已同步，重新生成不会丢掉这些修正。第 4 题仍为原图模式，元数据冲突待处理。

## 第 4、5 题：已核对的文字转录

共用文章：

> Blues music speaks histories that, from the conventional perspective, originate in the experiences of African Americans. But invariably, the blues exceed rigid cultural boundaries. Ralph Ellison’s definition of the blues suggests an expansive vista, limited only by a speaker’s capacity to lyrically express an “autobiographical chronicle of personal catastrophe.” As an idiom, the blues record histories, yet Ellison’s definition privileges the personal and leaves uncertain the role of national histories, the stories that speak our collective experiences. Locating the collective histories in the personal has proved a pivotal problem for readers in the written use of the blues both in Ellison’s fiction and in works by Toni Morrison, Gayl Jones, and others.

第 4 题（多选）：

> The passage suggests that which of the following is an accurate characterization of the blues as defined by Ralph Ellison?

- A. They are not limited to a specific cultural tradition.
- B. They emphasize personal experience over collective history.
- C. They must appear in written works.

第 5 题（选句子，无 A–E 选项）：

> Select the sentence in the passage that describes a particular alternative to the conventional perspective on the blues.

## 判分数据仍需独立复核

本次校对不等于答案正确性认证。题目截图没有答案表，现有答案数据来自另一份人工录入，无法仅凭 OCR 核实。第 4、5 题已明确暴露出数据与截图不匹配；其他题也不能据此假定答案正确。例如第 1 题当前答案仍指向 C（enigmatic），并未随文字修正改为 B。

首次文字校对保留全部判分数据；后续第 5 题按截图纠正为 `ss`，移除不适用的五选项及答案 E，参考答案显示待核对，不计入分数。文章按目视确认的 5 句话点选，保存整句文本，旧 A–E 下标不会自动选中句子。其余题型、答案、题号、图片及课程 ID 不变。下一步需找到对应原 PDF 的答案页，核对题号、Section 和答案映射，再修复判分数据。历史作答未迁移；第 1、9 题恢复原始选项顺序后，旧作答记录中的选项下标需谨慎解读。

其余 49 个 Section 不在本次范围。尚未发布到线上，也未验证 Firebase 登录后的实际页面。

验证：本节 `validate_qset` 检查通过，全部图片引用有效，11 题文字与生成源一致；`npm test` 71 项通过。已用本地 Edge 无头浏览器验证点选、切换、键盘、模拟提交保存、重做、上次作答恢复、旧数据兼容及手机宽度。未连接真实 Firebase。以上验证不能证明原始答案表正确。
