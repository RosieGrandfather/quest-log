"""Build the Zhang Wei text-completion courses, one per Test range in COURSES. Local sources only.
Run with bundled Python: build.py [--source-dir PATH] [--course ID ...]  (default: every course).
Each Section is one unit. Unit numbering only ever grows within a course, so saved progress stays valid.
"""
import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

import pdfplumber
from glossary import annotate_unit, annotate_course

REPO = Path(__file__).resolve().parents[3]
# course id -> Tests covered, audit file. Section n of the book is Test (n+1)//2.
COURSES = {
    'gre-zt': dict(tests=(1, 50), audit='audit.json'),
    'gre-zt-101': dict(tests=(51, 100), audit='audit-101.json'),
    'gre-zt-201': dict(tests=(101, 143), audit='audit-201.json'),  # Test 143 is the last in the book
}
LETTERS = 'ABCDEFGHI'
# Blanks the PDF itself prints without underscores
# PDF lines with a broken option label, fixed before parsing
LINE_FIXES = [('E shortage', 'E. shortage')]  # whole-line match
STEM_FIXES = [('as if it were a Gothic or', 'as if it were a ____ Gothic or'),
              # CO2 subscripts the PDF text layer drops onto a later line
              ('anthropogenic CO , thereby', 'anthropogenic CO₂, thereby'), ('However, the 2 (i)', 'However, the (i)'),
              ('net source of CO , thereby', 'net source of CO₂, thereby'), ('feedback loop. 2', 'feedback loop.')]
# Answer keys the review found unreliable: after submit the page shows "此题不计分" once plus this note as the reason; the source key is kept in sourceAnswer/ans.
# Notes name multi-blank answers per blank as shown on screen (空(ii) A), not with the PDF's D-I letters.
# See docs/GRE_ZT_ANSWER_REVIEW.md.
PENDING = {
    ('gre-zt-101', 'u96-test98-s2', 5): '配套答案为 C/F（logical / understandable）。冒号后说她打心底认定自己是在为更大的事业付出，说明她并不承认、也意识不到自己的权力欲，更合理的是 B/E（unacknowledged / subconscious）。',
    ('gre-zt-201', 'u08-test104-s2', 1): '配套答案为 C（anthropocentrism，人类中心主义）。把圣城耶路撒冷放在地图中心，反映的是当时以宗教为核心的世界观，与“以人为中心”无关，更合理的是 D（cosmology）。',
    ('gre-zt-201', 'u60-test130-s2', 4): '配套答案为 空(i) B continues to matter、空(ii) A links between、空(iii) A satisfactory。冒号后说某些参与的减少是恰当的、增加反而可能有害，对应“整体参与在青春期开始减少，但参与与学业结果之间的关系不再简单”，更合理的是 空(i) A begins to wane、空(ii) A links between、空(iii) C straightforward。',
    ('gre-zt-201', 'u62-test131-s2', 3): '配套答案为 空(i) C singular among、空(ii) C conjecture、空(iii) C venturing beyond，部分题库网站也这样给。但后一句举的例子是 Penrose 认为暴胀宇宙学“缺乏证据却被当成定论”，说明他是在批评别的理论物理学家超出数据作推测，空(i) 更合理的是 B critical of，其余两空不变。',
    ('gre-zt-201', 'u86-test143-s2', 3): '配套答案为 空(i) C mendacious、空(ii) B convincingly、空(iii) B champion。前半句说她闪烁其词甚至说谎，后面“不论是否认同她的观点”都应让选民有理由拒绝她，更合理的是 空(i) C mendacious、空(ii) A badly、空(iii) A reject。',
}


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
                for old,new in LINE_FIXES: text=new if text==old else text
                y = min(w['top'] for w in ws)
                if text.startswith('微信公众号') or re.match(r'^第\s*\d+\s*[页⻚]', text):
                    continue
                head = re.match(r'test\s*(\d+)\s*section\s*([12])\s*[(（]?\s*(easy|medium|hard)', text, re.I)  # from Test 130 on: no parentheses
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
                if not question['opts']:  # option A glued to the stem's last sentence: "reality.A. ubiquitous"
                    text=re.sub(r'(?<=[a-z][.?!])A\s*[.．]\s+',' A. ',text)
                opts=list(re.finditer(r'(?<!\S)([A-I])\s*[.．]\s*',text))
                if opts and not question['opts'] and opts[0][1]!='A':  # e.g. "vitamin" / "C." -- still the stem
                    opts=[]
                if opts:
                    pre=text[:opts[0].start()].strip()  # stem tail sharing a line with option A
                    if pre:
                        if not question['opts']: question['stem'].append(pre)
                        else:
                            last=next(reversed(question['opts']))
                            question['opts'][last]+=' '+pre
                    for oi,m in enumerate(opts):
                        value=text[m.end():opts[oi+1].start() if oi+1<len(opts) else len(text)].strip()
                        assert m[1] not in question['opts'], (current, text)
                        question['opts'][m[1]]=value
                elif not question['opts']:
                    question['stem'].append(text)
                else:
                    last=next(reversed(question['opts']))
                    question['opts'][last]+=' '+text
    if sections and sections[-1]['test']==tests[1]:  # the book ends with this Test
        if question: question['end']=[len(doc.pages)-1,780]
        return [s for s in sections if s['test']>=tests[0]]
    raise RuntimeError(f'Did not find end of Test {tests[1]}')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source-dir',type=Path,default=Path('C:/projects/learning/GRE prep/张巍GRE/verbal'))
    ap.add_argument('--course',nargs='*',choices=sorted(COURSES),default=sorted(COURSES))
    args=ap.parse_args()
    pdf=next(args.source_dir.glob('*2000*.pdf'))
    key=args.source_dir/'填空2000答案.txt'
    keys={}
    t=None
    for line in key.read_text(encoding='utf-8-sig').splitlines():
        if m:=re.match(r'test\s+(\d+)',line,re.I):t=int(m[1])
        elif m:=re.match(r'section\s+([12])\s+(.+)',line,re.I):
            keys[t,int(m[1])]=[x for x in m[2].strip().split('/') if x]
    for cid in args.course:
        build(cid,pdf,key,keys)


def build(cid,pdf,key,keys):
    first,last=COURSES[cid]['tests']
    nsec=2*(last-first+1)
    lo,hi=2*first-1,2*last  # book-wide Section numbers
    out=REPO/'courses'/cid
    sections=extract(pdf,(first,last))
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
            for old,new in STEM_FIXES: stem=stem.replace(old,new)
            stem=re.sub(r'\((i{1,3})\)\)',r'(\1)',stem)  # "(i))_____" doubled bracket
            stem=re.sub(r'\((I{1,3})\)',lambda m:m[0].lower(),stem)
            stem=re.sub(r'\((i{1,3})\)(?!\s*_)',lambda m:m[0]+'____',stem)  # "(ii) across" -> "(ii)____ across"
            q['opts']={k:re.sub(r'\s*答案获取方式.*$','',clean(v)) for k,v in q['opts'].items()}  # book's closing note after the last option
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
            if note:=PENDING.get((cid,uid,q['n'])):
                it.update(answerPending=True,answerReviewReason='校对认为配套答案不可靠',explanation=note)
            items.append(it)
            audit.append({'unit':uid,'question':q['n'],'pages':[p0+1,p1+1],'sourceAnswer':a,'options':n})
        unit={'id':uid,'title':title,'en':f'Text Completion — Test {s["test"]}, Section {s["section"]}',
              'minutes':15,'practice':True,'answerFormat':'gre-zt-v1','objectives':[
                  '独立完成7道原题，整节完成后提交。','提交后核对答案；答案按配套《填空2000答案》记录，本课程暂不附讲解。'],
              'blocks':[{'type':'gre-qset','base':f'courses/{cid}/','source':f'张巍GRE填空机经2000题 · Test {s["test"]} Section {s["section"]}',
                         'noteTail':'（原题及配套答案，仅供个人学习；暂不附讲解）','items':items}],'references':[]}
        if cid=='gre-zt':annotate_unit(unit)
        (out/f'{uid}.json').write_text(json.dumps(unit,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
        units.append({k:unit[k] for k in ['id','title','en','minutes','practice']}|{'file':f'{uid}.json','hasQuiz':False,'difficulty':s['difficulty']})
    name=f'前{hi}个Section' if lo==1 else f'第{lo}–{hi}个Section'
    course={'id':cid,'title':f'张巍GRE填空机经：{name}','subtitle':f'Test {first}–{last}，每个Section一节，共{nsec}节{7*nsec}题。原题与配套答案，完成整节后提交查看对错，暂不附讲解。',
            'order':17,'order_note':'选修，GRE填空专项练习','tier':'elective','tags':['GRE'],'units':units}
    if cid=='gre-zt':annotate_course(course)
    (out/'course.json').write_text(json.dumps(course,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    report={'sourcePDF':pdf.name,'pdfSHA256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'answerSHA256':hashlib.sha256(key.read_bytes()).hexdigest(),'course':cid,'tests':[first,last],'sections':nsec,'questions':len(audit),'items':audit}
    (Path(__file__).parent/COURSES[cid]['audit']).write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    print(f'{cid}: {len(units)} sections, {len(audit)} questions')


if __name__=='__main__':main()
