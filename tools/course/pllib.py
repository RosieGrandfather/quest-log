"""pl300-0 共用：导入 unitlib / runlib，并提供调整答案位置的函数"""
from unitlib import *
from runlib import Notebook

PL_STUDY_GUIDE = {"title": "Microsoft Learn：PL-300 Study Guide（官方考试大纲）", "url": "https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/pl-300", "note": "本课程的大纲依据（2026-04-20 更新版）；只引用，没有转载"}

def retarget(unit, target):
    for q, t in zip(unit["quiz"]["questions"], target):
        q["options"][q["answer"]], q["options"][t] = q["options"][t], q["options"][q["answer"]]
        q["answer"] = t
