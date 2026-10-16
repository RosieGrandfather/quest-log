"""Prepare source pages and DOCX answer paragraphs; no OCR text is published."""
from pathlib import Path
import re,json,zipfile,xml.etree.ElementTree as E
import pypdfium2 as pdfium
import pdfplumber
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCE=Path('C:/projects/learning/GRE prep/张巍GRE/quant')
PDF=next(SOURCE.glob('*170*.pdf'))
TMP=ROOT/'tmp/grzq170/pages'
if __name__=='__main__':
    TMP.mkdir(parents=True,exist_ok=True)
    doc=pdfium.PdfDocument(str(PDF))
    for i in range(4,len(doc)):
        dest=TMP/f'p{i+1:02d}.png'
        if not dest.exists():doc[i].render(scale=2).to_pil().save(dest)
    # Native text headings supplement OCR on pages with formula images.
    if not (HERE/'headings.json').exists():
        heads=[]
        with pdfplumber.open(PDF)as native:
            for i in range(4,len(native.pages)):
                p=native.pages[i].filter(lambda o:o['object_type']!='char' or(abs(o['matrix'][1])<.01 and 65<o['top']<780))
                for m in p.search(r'(?m)^\s*(\d{1,3})\.\s',regex=True):
                    if m['x0']<95:heads.append({'n':int(m['groups'][0]),'page':i+1,'top':m['top'],'x0':m['x0']})
        (HERE/'headings.json').write_text(json.dumps(heads,indent=1),encoding='utf8')
    with zipfile.ZipFile(SOURCE/'难题170答案.docx')as z:
        ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        root=E.fromstring(z.read('word/document.xml'))
        paragraphs=[''.join(t.text or '' for t in e.findall('.//w:t',ns)) for e in root.findall('.//w:p',ns)]
    text='\n'.join(paragraphs)
    (HERE/'answers-source.txt').write_text(text,encoding='utf8')
    starts=[];expected=1
    for m in re.finditer(r'(?m)^(\d{1,3})\.\s*',text):
        if int(m[1])==expected:starts.append((expected,m.start(),m.end()));expected+=1
    assert expected==171
    answers=[]
    for i,(n,start,end)in enumerate(starts):
        block=text[end:starts[i+1][1] if i+1<len(starts)else len(text)].strip()
        m=re.search(r'答案[：:]\s*([^\n]+)',block);assert m,n
        answers.append({'n':n,'answer':m[1].strip(),'explanation':block})
    (HERE/'source-answers.json').write_text(json.dumps(answers,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
    print('42 question pages rendered; 170 answer entries extracted')
