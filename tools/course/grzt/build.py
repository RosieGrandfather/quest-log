"""Build Zhang Wei text-completion sections, one course per Test range. Local sources only.
Run with bundled Python: build.py [--source-dir PATH] [--batch 1|2].
batch 1 = gre-zt (Test 1-25), batch 2 = gre-zt2 (Test 26-50).
"""
import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

import pdfplumber

REPO = Path(__file__).resolve().parents[3]
BATCHES = {
    1: dict(course='gre-zt', tests=(1, 25), name='前50个Section', audit='audit.json'),
    2: dict(course='gre-zt2', tests=(26, 50), name='第51–100个Section', audit='audit-2.json'),
}
LETTERS = 'ABCDEFGHI'


def clean(t):
    t = unicodedata.normalize('NFKC', t)
    t = re.sub(r'【\s*微\s*信[^】]*】', '', t)
    return re.sub(r'\s+', ' ', t).strip()


def extract(pdf, tests=(1, 25)):
    sections, current, question = [], None, None
    with pdfplumber.open(pdf) as doc:
        for pi in range(13, len(doc.pages)):
            page = doc.pages[pi].filter(lambda o: o['object_type'] != 'char' or (
                abs(o['matrix'][1]) < .01 and o['top'] < 780))
            words = page.extract_words(x_tolerance=2, y_tolerance=3)
            lines = []
            for w in sorted(words, key=lambda w: (round(w['top']/3), w['x0'])):
                if not lines or abs(lines[-1][0]['top']-w['top']) > 3:
                    lines.append([w])
                else:
                    lines[-1].append(w)
            for ws in lines:
                ws.sort(key=lambda w:w['x0'])
                text = clean(' '.join(w['text'] for w in ws))
                y = min(w['top'] for w in ws)
                if text.startswith('微信公众号') or re.match(r'^第\s*\d+\s*[页⻚]', text):
                    continue
                head = re.match(r'test\s*(\d+)\s*section\s*([12])\s*[(（]\s*(easy|medium|hard)', text, re.I)
                if head:
                    if question: question['end']=[pi,y-3]
                    if int(head[1])>tests[1]:
                        return [s for s in sections if s['test']>=tests[0]]
                    current={'test':int(head[1]),'section':int(head[2]),'difficulty':head[3].lower(),'items':[]}
                    sections.append(current)
                    question=None
                    continue
                q = re.match(r'^([1-7])[.．]\s*(.*)',text)
                if q and ws[0]['x0'] < 75:
                    if question: question['end']=[pi,y-3]
                    question={'n':int(q[1]),'stem':[q[2]],'opts':{},'start':[pi,y-3], 'end':None}
                    current['items'].append(question)
                    continue
                if not question: continue
                opts=list(re.finditer(r'(?<!\S)([A-I])\s*[.．]\s*',text))
                if opts:
                    for oi,m in enumerate(opts):
                        value=text[m.end():opts[oi+1].start() if oi+1<len(opts) else len(text)].strip()
                        assert m[1] not in question['opts'], (current, text)
                        question['opts'][m[1]]=value
                elif not question['opts']:
                    question['stem'].append(text)
                else:
                    last=next(reversed(question['opts']))
                    question['opts'][last]+=' '+text
    raise RuntimeError(f'Did not find end of Test {tests[1]}')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source-dir',type=Path,default=Path('C:/projects/learning/GRE prep/张巍GRE/verbal'))
    ap.add_argument('--batch',type=int,choices=sorted(BATCHES),default=1)
    args=ap.parse_args()
    b=BATCHES[args.batch]
    cid=b['course']
    out=REPO/'courses'/cid
    first,last=b['tests']
    nsec=2*(last-first+1)
    pdf=next(args.source_dir.glob('*2000*.pdf'))
    key=args.source_dir/'填空2000答案.txt'
    keys={}
    t=None
    for line in key.read_text(encoding='utf-8-sig').splitlines():
        if m:=re.match(r'test\s+(\d+)',line,re.I):t=int(m[1])
        elif m:=re.match(r'section\s+([12])\s+(.+)',line,re.I):
            keys[t,int(m[1])]=[x for x in m[2].strip().split('/') if x]
    sections=extract(pdf,b['tests'])
    assert len(sections)==nsec,(len(sections),nsec)
    out.mkdir(parents=True,exist_ok=True)
    units=[]
    audit=[]
    for si,s in enumerate(sections,1):
        answers=keys[s['test'],s['section']]
        assert len(s['items'])==len(answers)==7, (si,len(s['items']),answers)
        uid=f'u{si:02d}-test{s["test"]:02d}-s{s["section"]}'
        title=f'Test {s["test"]} · Section {s["section"]}（{s["difficulty"]} · 7题）'
        items=[]
        for q,a in zip(s['items'],answers):
            n=len(q['opts'])
            assert sorted(q['opts'])==list(LETTERS[:n]),(si,q)
            assert n in (5,6,9),(si,q)
            stem=clean(' '.join(q['stem']))
            kind='tc' if n==9 or (n==6 and '(ii)' in stem) else 'se' if n==6 else 'mc1'
            it={'n':q['n'],'kind':kind,'sourceAnswer':a,'txt':{'stem':[re.sub(r'_{3,}','____',stem)]}}
            if kind=='tc':
                blanks=n//3
                assert len(a)==blanks and all(3*j<=LETTERS.index(c)<3*j+3 for j,c in enumerate(a)),(si,q,a)
                it.update(blanks=blanks,ans=[LETTERS.index(c)%3 for c in a])
                it['txt']['cols']=[[q['opts'][c] for c in LETTERS[j*3:j*3+3]] for j in range(blanks)]
            else:
                assert len(a)==(2 if kind=='se' else 1),(si,q,a)
                it.update(nopt=n,ans=[LETTERS.index(c) for c in a])
                it['txt']['opts']=[q['opts'][c] for c in LETTERS[:n]]
            p0,_=q['start'];p1,_=q['end']
            items.append(it)
            audit.append({'unit':uid,'question':q['n'],'pages':[p0+1,p1+1],'sourceAnswer':a,'options':n})
        unit={'id':uid,'title':title,'en':f'Text Completion — Test {s["test"]}, Section {s["section"]}',
              'minutes':15,'practice':True,'answerFormat':'gre-zt-v1','objectives':[
                  '独立完成7道原题，整节完成后提交。','提交后核对答案；答案按配套《填空2000答案》记录，本课程暂不附讲解。'],
              'blocks':[{'type':'gre-qset','base':f'courses/{cid}/','source':f'张巍GRE填空机经2000题 · Test {s["test"]} Section {s["section"]}',
                         'noteTail':'（原题及配套答案，仅供个人学习；暂不附讲解）','items':items}],'references':[]}
        (out/f'{uid}.json').write_text(json.dumps(unit,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
        units.append({k:unit[k] for k in ['id','title','en','minutes','practice']}|{'file':f'{uid}.json','hasQuiz':False,'difficulty':s['difficulty']})
    course={'id':cid,'title':f'张巍GRE填空机经：{b["name"]}','subtitle':f'Test {first}–{last}，每个Section一节，共{nsec}节{7*nsec}题。原题与配套答案，完成整节后提交查看对错，暂不附讲解。',
            'order':17,'order_note':'选修，GRE填空专项练习','tier':'elective','tags':['GRE'],'units':units}
    (out/'course.json').write_text(json.dumps(course,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    report={'sourcePDF':pdf.name,'pdfSHA256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'answerSHA256':hashlib.sha256(key.read_bytes()).hexdigest(),'course':cid,'tests':[first,last],'sections':nsec,'questions':len(audit),'items':audit}
    (Path(__file__).parent/b['audit']).write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    print(f'{len(units)} sections, {len(audit)} questions')


if __name__=='__main__':main()
