"""Read the PDF text layer, retaining page/line positions for source checks."""
import argparse
import json
import re
import unicodedata
from pathlib import Path

import pdfplumber

HERE=Path(__file__).resolve().parent
DEFAULT=Path('C:/projects/learning/GRE prep/张巍GRE/verbal')


def clean(s):
    s=unicodedata.normalize('NFKC',s)
    s=re.sub(r'【\s*微\s*信\s*公\s*众\s*号[^】]*】','',s)
    return re.sub(r'\s+',' ',s).strip()


def join(lines):
    text=''
    for l in lines:
        s=l['text']
        # Rejoin words split by a print line; preserve the printed hyphen.
        text+=('' if text.endswith('-') else ' ')+s
    return clean(text)


def paragraphs(lines):
    result=[];group=[];previous=None
    for l in lines:
        if group and previous['page']==l['page'] and l['top']-previous['top']>19:
            result.append(join(group));group=[]
        group.append(l);previous=l
    if group:result.append(join(group))
    return [p for p in result if p]


def extract(pdf, first=1, last=200):
    result=[];current=None
    with pdfplumber.open(pdf) as doc:
        for pn in range(21,len(doc.pages)):
            page=doc.pages[pn].filter(lambda o:o['object_type']!='char' or (abs(o['matrix'][1])<.01 and o['top']<780))
            words=page.extract_words(x_tolerance=2,y_tolerance=3,return_chars=True)
            lines=[]
            for w in sorted(words,key=lambda w:(round(w['top']/3),w['x0'])):
                if not lines or abs(lines[-1][0]['top']-w['top'])>3:lines.append([w])
                else:lines[-1].append(w)
            for ws in lines:
                ws.sort(key=lambda w:w['x0'])
                text=clean(' '.join(w['text'] for w in ws))
                if not text or text.startswith('微信公众号') or re.match(r'^第\s*\d+\s*[页⻚]',text):continue
                h=re.fullmatch(r'Passage\s*(\d+)',text,re.I)
                if h:
                    n=int(h[1])
                    if n>last:return result
                    if n<first:
                        current=None;continue
                    current={'n':n,'lines':[]};result.append(current)
                elif current:
                    current['lines'].append({'page':pn+1,'top':round(min(w['top'] for w in ws),2),'text':text,
                                             'words':[[w['text'],any('Bold' in c['fontname'] for c in w['chars'])] for w in ws]})
    return result


def parse(p):
    lines=p['lines']
    starts=[i for i,l in enumerate(lines) if re.match(r'^[1-9]\s*[.．]\s*\S',l['text'])]
    if not starts:
        ai=next(i for i,l in enumerate(lines) if re.match(r'^A\s*[.．]',l['text']))
        candidates=[i for i in range(ai) if re.match(r'^(?:Which |The (?:argument|passage|author|primary|purpose|function|two |reasoning|statement|bold|highlighted)|In (?:the |order)|It can |According |Select |If |An assumption|Each of |The .*?(?:following|above))',lines[i]['text'])]
        # A single unnumbered question is separated from the passage by extra leading.
        gap_candidates=[i for i in range(1,ai) if lines[i]['page']==lines[i-1]['page'] and lines[i]['top']-lines[i-1]['top']>19]
        if candidates: start=candidates[-1]
        elif gap_candidates:start=gap_candidates[-1]
        else:raise ValueError(f'Passage {p["n"]}: cannot locate unnumbered question')
        starts=[start]
    article=paragraphs(lines[:starts[0]])
    highlights=[];run=[]
    for line in lines[:starts[0]]:
        for word,bold in line.get('words',[]):
            if bold:run.append(word)
            elif run:
                highlights.append(clean(' '.join(run)));run=[]
    if run:highlights.append(clean(' '.join(run)))
    items=[]
    for qi,start in enumerate(starts):
        chunk=lines[start:starts[qi+1] if qi+1<len(starts) else len(lines)]
        chunk=[dict(x) for x in chunk]
        chunk[0]['text']=re.sub(r'^[1-9]\s*[.．]\s*','',chunk[0]['text'])
        opts={};stem=[];buf=[];last=None
        for l in chunk:
            m=re.match(r'^([A-E])\s*[.．]\s*(.*)',l['text'])
            if m:
                if last:opts[last]=join(buf)
                else:stem=list(buf)
                last=m[1];buf=[dict(l,text=m[2])]
            else:buf.append(l)
        if last:opts[last]=join(buf)
        else:stem=buf
        items.append({'n':qi+1,'stem':join(stem),'options':opts,'pages':sorted({l['page'] for l in chunk})})
    return {'n':p['n'],'paragraphs':article,'highlights':highlights,'items':items,'pages':sorted({l['page'] for l in lines})}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source-dir',type=Path,default=DEFAULT);args=ap.parse_args()
    raw=extract(next(args.source_dir.glob('*440*.pdf')))
    (HERE/'raw-lines.json').write_text(json.dumps(raw,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
    parsed=[]
    for p in raw:
        try:parsed.append(parse(p))
        except Exception as e:print(str(e))
    (HERE/'passages.json').write_text(json.dumps(parsed,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
    print(len(raw),'passages,',sum(len(p['items']) for p in parsed),'questions')
