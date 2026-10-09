"""ba-0 共用：导入 unitlib，并提供调整答案位置的函数和常用参考资料"""
from unitlib import *

BABOK_REF = {"title": "IIBA：BABOK Guide（业务分析知识体系）", "url": "https://www.iiba.org/career-resources/a-business-analysis-professionals-foundation-for-success/babok/", "note": "BA 行业最通行的知识体系（六个知识领域）；本课程只引用概念，没有转载原文，完整内容需向 IIBA 获取"}

def retarget(unit, target):
    for q, t in zip(unit["quiz"]["questions"], target):
        q["options"][q["answer"]], q["options"][t] = q["options"][t], q["options"][q["answer"]]
        q["answer"] = t
