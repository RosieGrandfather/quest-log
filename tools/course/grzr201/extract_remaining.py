"""Extract only Passages 201–440 without overwriting the first course's cache."""
import json
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'grzr'))
from extract import extract,parse,DEFAULT

def parse_remaining(p):
    # Explicit source-layout repairs, not changes to the questions' wording.
    p=json.loads(json.dumps(p))
    if p['n']==240:
        # The line begins with the decimal 4.5, not a numbered question.
        for line in p['lines']:
            if line['text'].startswith('4.5 '):line['text']=' '+line['text']
        # parse() permits leading whitespace only after the initial digit.
    if p['n'] in (272,398):
        for line in p['lines']:
            if line['text'].startswith('The author introduces the subject') or (p['n']==398 and line['text'].startswith('Which of the following, if true, might help')):
                line['text']='1. '+line['text']
            elif line['text'].startswith('1. Which of the following best characterizes') or (p['n']==398 and line['text'].startswith('1. The author of the passage refers')):
                line['text']='2. '+line['text'][3:]
    parsed=parse(p)
    if p['n']==208:
        q=parsed['items'][1]
        if 'D' not in q['options']:
            c,d=q['options']['C'].split(' .D. ',1)
            q['options']={'A':q['options']['A'],'B':q['options']['B'],'C':c,'D':d,'E':q['options']['E']}
    if p['n']==440:
        q=parsed['items'][-1]
        q['options']['E']=q['options']['E'].split('答案获取方式:')[0].strip()
    return parsed

if __name__=='__main__':
    raw=extract(next(DEFAULT.glob('*440*.pdf')),201,440)
    parsed=[parse_remaining(p) for p in raw]
    assert [p['n'] for p in parsed]==list(range(201,441))
    for name,value in [('raw-lines',raw),('passages',parsed)]:
        (HERE/f'{name}.json').write_text(json.dumps(value,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
    print(len(parsed),'passages;',sum(len(p['items']) for p in parsed),'questions')
