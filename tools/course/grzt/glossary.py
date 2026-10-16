"""Curated Chinese option meanings for all Zhang Wei completion Sections.

Data is checked into option-meanings.json; rebuilding needs no translation service.
English choices, answer indices, and answerFormat are deliberately untouched.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
COURSES=('gre-zt','gre-zt-101','gre-zt-201')

@lru_cache(maxsize=1)
def meanings():
    return json.loads((HERE/'option-meanings.json').read_text(encoding='utf8'))

def add_meanings(item):
    txt=item['txt']; lookup=meanings()
    if item['kind']=='tc':
        txt['colsZh']=[[lookup[o] for o in col] for col in txt['cols']]
    else:
        txt['optsZh']=[lookup[o] for o in txt['opts']]
    values=sum(txt['colsZh'],[]) if item['kind']=='tc' else txt['optsZh']
    assert all(isinstance(s,str) and re.search('[\u4e00-\u9fff]',s) for s in values)

def annotate_unit(unit):
    for block in unit['blocks']:
        if block['type']=='gre-qset':
            for item in block['items']:add_meanings(item)

def annotate_course(course):
    if '选项中文释义' not in course['subtitle']:
        course['subtitle']+='提交后显示所有选项中文释义。'

def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--course',nargs='+',choices=COURSES,default=COURSES)
    for cid in parser.parse_args().course:
        directory=ROOT/'courses'/cid
        course=json.loads((directory/'course.json').read_text(encoding='utf8'))
        count=questions=0
        for entry in course['units']:
            path=directory/entry['file'];unit=json.loads(path.read_text(encoding='utf8'))
            annotate_unit(unit)
            path.write_text(json.dumps(unit,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
            for q in unit['blocks'][0]['items']:
                questions+=1
                count+=sum(map(len,q['txt']['colsZh'])) if q['kind']=='tc' else len(q['txt']['optsZh'])
        annotate_course(course)
        (directory/'course.json').write_text(json.dumps(course,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
        print(f'{cid}: {len(course["units"])} Sections, {questions} questions, {count} translated options')

if __name__=='__main__':main()
