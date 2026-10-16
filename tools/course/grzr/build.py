"""Build 40 text-only reading lessons from Passages 1–200 (five per lesson).
Run extract.py first if the source PDF changes, then run this script.
"""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from extract import HERE, DEFAULT, clean

REPO=HERE.parents[2]
OUT=REPO/'courses/gre-zr'
INSTRUCTION=re.compile(r'(?:For the following question,\s*)?Consider each of the choices separately and select all that apply\.?',re.I)
# The TXT identifies these sentence answers by position or opening words.
SENTENCE_KEYS={2:(1,0),18:'Often written',22:'Such a strategy',40:(0,0),
               41:'This compression has combined',55:'Yet McCormick',58:(0,1),
               148:'Early modern',172:'The problem, however',175:(0,3),191:(1,0)}


def text(s):
    return clean(INSTRUCTION.sub('',s))


def sentences(paragraph):
    # Protect abbreviation dots before splitting; do not drop any source text.
    protected=re.sub(r'\b(?:Ph\.D\.s?|Mr\.|Mrs\.|Dr\.|e\.g\.|i\.e\.)',lambda m:m[0].replace('.','\uE000'),paragraph)
    parts=re.split(r'(?<=[.!?])\s+(?=[“"\u2018]?[A-Z])',protected)
    result=[p.replace('\uE000','.') for p in parts]
    assert ' '.join(result)==paragraph
    return result


def answer_blocks(path):
    raw=path.read_text(encoding='utf-8-sig')
    # Source headings 92 and 177 are misspelled PASSAEG / PASASGE.
    parts=re.split(r'(?m)^\s*P[A-Z]{4,7}\s*(\d+)\s*$',raw)
    blocks={int(parts[i]):parts[i+1].strip() for i in range(1,len(parts),2)}
    assert set(blocks)==set(range(1,441))
    return blocks


def dump(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=1)+'\n',encoding='utf8')


def main():
    ps=json.loads((HERE/'passages.json').read_text(encoding='utf8'))
    assert [p['n'] for p in ps]==list(range(1,201))
    answer_path=DEFAULT/'阅读440答案.txt'
    keys=answer_blocks(answer_path)
    decisions=json.loads((HERE/'review-decisions.json').read_text(encoding='utf8'))
    review_rows={}
    for line in (HERE/'reviewed-answers.tsv').read_text(encoding='utf8').splitlines()[1:]:
        pn,candidates,reasons=line.split('\t')
        review_rows[int(pn)]=(candidates.split('/'),reasons.split('|'))
    reviews=[]
    OUT.mkdir(parents=True,exist_ok=True)
    units=[];audit=[];counts=Counter()
    for lesson in range(1,41):
        batch=ps[(lesson-1)*5:lesson*5]
        passages={};items=[]
        uid=f'u{lesson:02d}-p{batch[0]["n"]:03d}-p{batch[-1]["n"]:03d}'
        for p in batch:
            pn=p['n'];pid=f'p{pn}'
            paras=[text(a) for a in p['paragraphs'] if text(a)]
            highlights=[]
            for h in p['highlights']:
                h=text(re.sub(r'【.*$','',h))
                if not h:continue
                # Source line breaks can bisect a printed hyphenated word.
                if not any(h in a for a in paras):h=re.sub(r'(?<=\w)-\s+(?=\w)','-',h)
                assert any(h in a for a in paras),(pn,'highlight not found',h)
                highlights.append(h)
            passages[pid]={'number':pn,'paragraphs':paras,'highlights':highlights}
            raw=keys[pn]
            stripped=re.sub(r'【[^】]*】|[（(]新题[）)]','',raw)
            tokens=re.findall(r'(?<![A-Za-z])[A-E]+(?![A-Za-z])',stripped)
            assert len(tokens)==sum(bool(q['options']) for q in p['items']),(pn,raw)
            token_index=0
            for q in p['items']:
                stem=text(q['stem']);opts=q['options']
                it={'n':len(items)+1,'passage':pid,'sourceQuestion':q['n'],'txt':{'stem':[stem]}}
                if opts:
                    assert list(opts)==list('ABCDE'[:len(opts)]),(pn,q['n'],opts)
                    kind='mcn' if len(opts)==3 else 'mc1'
                    assert len(opts) in (3,5)
                    source=tokens[token_index];token_index+=1
                    assert kind=='mcn' or len(source)==1,(pn,q['n'],source)
                    it.update(kind=kind,nopt=len(opts),ans=[ord(c)-65 for c in source],sourceAnswer=source)
                    assert all(0<=v<len(opts) for v in it['ans'])
                    it['txt']['opts']=[text(opts[c]) for c in opts]
                else:
                    assert 'sentence' in stem.lower() and pn in SENTENCE_KEYS
                    ss=[s for a in paras for s in sentences(a)]
                    key=SENTENCE_KEYS[pn]
                    if isinstance(key,tuple):target=sentences(paras[key[0]])[key[1]]
                    else:
                        matches=[s for s in ss if s.lower().startswith(key.lower())]
                        assert len(matches)==1,(pn,key,matches)
                        target=matches[0]
                    it.update(kind='ss',ansText=target,sourceAnswer=raw)
                    it['txt'].update({'pass':paras,'sentences':ss,'highlights':highlights,
                                      'sentenceParagraphLengths':[len(sentences(a)) for a in paras]})
                if re.search(r'highlight|boldface|underlin',stem,re.I):
                    assert highlights,(pn,q['n'],'missing source emphasis')
                counts[it['kind']]+=1
                key=f'{pn}-{q["n"]}'
                candidates,reasons=review_rows[pn]
                assert len(candidates)==len(reasons)==len(p['items'])
                decision=decisions.get(key)
                review={'passage':pn,'question':q['n'],'lesson':lesson,'unit':uid,
                        'sourceAnswer':it['sourceAnswer'],'candidate':candidates[q['n']-1],
                        'reason':reasons[q['n']-1],'status':'agrees',
                        'finalAnswer':it.get('ans',it.get('ansText'))}
                if decision:
                    review.update(decision)
                    if decision['status']=='corrected':
                        it['ans']=[ord(c)-65 for c in decision['answer']]
                        it['explanation']=decision['reason']
                    elif decision['status']=='pending':
                        it['answerPending']=True
                        it['answerReviewReason']=decision['reason']
                        it['explanation']='本题答案有争议，尚无可靠定论。争议理由：'+decision['reason']
                    it['answerReview']={'date':'2026-10-16','status':decision['status']}
                    review['finalAnswer']=None if it.get('answerPending') else it.get('ans',it.get('ansText'))
                reviews.append(review)
                items.append(it)
                audit.append({'lesson':lesson,'unit':uid,'passage':pn,'question':q['n'],
                              'lessonQuestion':it['n'],'kind':it['kind'],'sourceAnswer':it['sourceAnswer'],
                              'answer':it.get('ans',it.get('ansText')),'answerPending':it.get('answerPending',False),'PDFPages':q['pages']})
        total=len(items)
        title=f'阅读 {lesson:02d} · Passage {batch[0]["n"]}–{batch[-1]["n"]}（5篇 · {total}题）'
        unit={'id':uid,'title':title,'en':f'Reading Comprehension — Passages {batch[0]["n"]}–{batch[-1]["n"]}',
              'minutes':20,'practice':True,'answerFormat':'gre-zr-text-v1','objectives':[
                  '独立阅读5篇文章并完成全部题目，建议用时约20分钟；完成整节后提交。',
                  '提交后核对答案；已做独立复核，争议题暂不计分，仅更正或争议题附核对说明。',
                  '选句题直接点击文章中的句子，提交后对照参考句自评，不计入自动评分。'],
              'blocks':[{'type':'gre-qset','base':'courses/gre-zr/','source':f'张巍GRE阅读机经440篇 · Passage {batch[0]["n"]}–{batch[-1]["n"]}',
                         'noteTail':'（纯阅读练习，建议约20分钟；配套答案经独立复核，争议题暂不计分）',
                         'passages':passages,'items':items}],'references':[]}
        dump(OUT/f'{uid}.json',unit)
        units.append({k:unit[k] for k in ['id','title','en','minutes','practice']}|{'file':f'{uid}.json','hasQuiz':False})
    course={'id':'gre-zr','title':'张巍GRE阅读机经：前200篇 · 40节',
            'subtitle':'每节5篇，建议约20分钟。纯文字原题，整节提交后看答案；选句题点击原文后自评，暂不附讲解。',
            'order':18,'order_note':'选修，GRE阅读专项训练；时长为训练建议，并非官方独立阅读Section',
            'tier':'elective','tags':['GRE'],'units':units}
    dump(OUT/'course.json',course)
    pdf=next(DEFAULT.glob('*440*.pdf'))
    dump(HERE/'audit.json',{'sourcePDF':pdf.name,'pdfSHA256':hashlib.sha256(pdf.read_bytes()).hexdigest(),
                           'answerTXT':answer_path.name,'answerSHA256':hashlib.sha256(answer_path.read_bytes()).hexdigest(),
                           'lessons':40,'passages':200,'questions':len(audit),
                           'kinds':dict(counts),'answerPolicy':'413题已逐题独立复核；1题更正、9题待核对不计分，11道选句题仍自评；不是ETS官方认证。',
                           'items':audit})
    dump(HERE/'answer-review.json',{'date':'2026-10-16','scope':'Passages 1–200; independent review, not ETS certification',
                                   'counts':dict(Counter(r['status'] for r in reviews)),'items':reviews})
    print('40 lessons, 200 passages,',len(audit),'questions;',dict(counts))


if __name__=='__main__':main()
