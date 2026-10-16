"""Locate numbered questions from PDF and local OCR; publish crops, not OCR formulas."""
import json,re
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def read(n):return json.loads((HERE/n).read_text(encoding='utf8'))
def dump(n,v):(HERE/n).write_text(json.dumps(v,ensure_ascii=False,indent=1)+'\n',encoding='utf8')

def main():
    raw=read('ocr.json');ocr_heads=[]
    for key,lines in raw.items():
        for line in lines:
            x=min(w['x']for w in line['words']);y=min(w['y']for w in line['words'])
            match=re.match(r'^(\d{1,3})[.,]\s*',line['text'])
            if match and x<180 and 110<y<1580:
                ocr_heads.append({'n':int(match[1]),'page':int(key[1:]),'top':y/2})
    candidates=read('headings.json')+ocr_heads+[{'n':1,'page':5,'top':59}]
    heads=[];last=(0,0)
    for n in range(1,171):
        found=sorted((x for x in candidates if x['n']==n and (x['page'],x['top'])>last),key=lambda x:(x['page'],x['top']))
        assert found,n
        x=found[0];heads.append({'n':n,'page':x['page'],'top':x['top']});last=(x['page'],x['top'])
    raw=read('ocr.json');answers=read('source-answers.json');records=[]
    out=ROOT/'courses/gre-zq170/img';out.mkdir(parents=True,exist_ok=True)
    # Shared source chart precedes the Q53 heading, below Q52's last option.
    with Image.open(ROOT/'tmp/grzq170/pages/p19.png')as im:
        im.crop((100,810,1100,1300)).save(out/'greeting-cards.webp',quality=88)
    for i,start in enumerate(heads[:-1]):
        n=start['n'];end=heads[i+1];pieces=[];lines=[];used_pages=[]
        for pg in range(start['page'],end['page']+1):
            y0=start['top']-4 if pg==start['page']else 55
            y1=end['top']-1 if pg==end['page']else 842
            if n==52 and pg==19:y1=400
            if y1<=y0:continue
            if n==53 and pg==19:y0=start['top']-4
            with Image.open(ROOT/f'tmp/grzq170/pages/p{pg:02}.png')as im:
                crop=im.crop((100,round(y0*2),1100,round(y1*2)))
                # Do not display an empty next-page strip as a continuation.
                if sum(crop.convert('L').histogram()[:120])<8:continue
                name=f'q{n:03}-{len(pieces)+1}.webp';crop.save(out/name,quality=88);pieces.append(name)
                used_pages.append(pg)
            for l in raw[f'p{pg:02}']:
                y=min(w['y']for w in l['words'])/2
                if y0<=y<y1:lines.append(l['text'])
        text='\n'.join(lines);answer=answers[n-1]['answer'];assert answers[n-1]['n']==n
        if not re.fullmatch(r'[A-H ]+',answer):
            kind='ne';numeric=re.match(r'-?\d+(?:\.\d+)?(?:/\d+)?',answer)[0];opts=None
        else:
            numeric=None
            if re.search(r'Quantity|two quantities|relationship cannot',text,re.I):kind='qc';opts=4
            else:
                multi=len(answer.replace(' ',''))>1 or bool(re.search(r'Indicate\s+all|select\s+all',text,re.I))
                kind='mcn' if multi else 'mc1'
                letters=re.findall(r'(?mi)^\s*([A-H])\s*[.．:]',text)
                opts=max([ord(c.upper())-64 for c in letters]+[ord(c)-64 for c in answer if c!=' '])
                opts=max(3,opts)
        # Printed option counts reconciled with OCR and visual checks of missing formula-only options.
        if kind=='mc1':opts=5
        if kind=='mcn':
            opts={1:3,2:4,6:3,10:5,24:5,25:5,27:3,33:5,50:3,53:8,60:3,
                  62:5,63:5,64:5,65:5,66:5,67:5,68:3,69:5,75:5,80:6,81:4,
                  82:5,89:8,90:7,101:5,107:5,121:7,139:4,146:4,168:5}[n]
        # The right-hand graph for Q93 extends beside Q94 in the source layout.
        if n in (93,94):
            with Image.open(ROOT/'tmp/grzq170/pages/p28.png')as im:
                if n==93:
                    im.crop((100,1058,1100,1120)).save(out/'q093-text.webp',quality=88)
                    im.crop((100,1135,620,1195)).save(out/'q093-rounding.webp',quality=88)
                    im.crop((610,1110,1100,1410)).save(out/'q093-graph.webp',quality=88)
                    pieces=['q093-text.webp','q093-rounding.webp','q093-graph.webp']
                else:
                    im.crop((100,1290,600,1560)).save(out/'q094-diagram.webp',quality=88)
                    pieces=['q094-diagram.webp']+pieces[1:]
        if 53<=n<=56:
            pieces=['greeting-cards.webp']+pieces
            used_pages=sorted(set([19]+used_pages))
        records.append({'n':n,'kind':kind,'nopt':opts,'answer':numeric if kind=='ne'else answer.replace(' ',''),
                        'sourceAnswer':answer,'imgs':pieces,'sourcePages':used_pages,
                        'ocrText':text,'cropStart':start,'cropEnd':end})
    dump('questions.json',records);dump('question-boundaries.json',heads)
    print('questions',len(records));print([(r['n'],r['kind'],r['nopt'])for r in records])

if __name__=='__main__':main()
