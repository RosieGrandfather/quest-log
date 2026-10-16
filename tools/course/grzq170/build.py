"""Build the hard-quant course in alternating official 12/21 and 15/26 sections."""
import json,hashlib,re
from pathlib import Path
from collections import Counter
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/'courses/gre-zq170'
SOURCE=Path('C:/projects/learning/GRE prep/张巍GRE/quant')
ETS='https://www.ets.org/gre/test-takers/general-test/prepare/test-structure.html'
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
def main():
    qs=json.loads((HERE/'questions.json').read_text(encoding='utf8'))
    review=json.loads((HERE/'answer-review.json').read_text(encoding='utf8'))
    assert review['reviewed']==169 and review['retained']==169
    assert [r['independentAnswer'] for r in review['items']]==[q['answer'] for q in qs]
    assert [q['n']for q in qs]==list(range(1,170))
    OUT.mkdir(parents=True,exist_ok=True);units=[];audit=[];offset=0
    for section in range(1,14):
        size,minutes=((12,21)if section%2 else(15,26))if section<13 else(7,13)
        batch=qs[offset:offset+size];assert len(batch)==size
        first,last=batch[0]['n'],batch[-1]['n'];uid=f'u{section:02d}-q{first:03d}-q{last:03d}'
        items=[]
        for j,q in enumerate(batch,1):
            it={'n':j,'sourceQuestion':q['n'],'kind':q['kind'],'sourceAnswer':q['sourceAnswer'],
                'img':q['imgs'][0],'imgs':q['imgs']}
            if q['kind']=='ne':
                it['ans']=q['answer']
                if '/'in q['answer']:it['frac']=True
            else:
                it['ans']=[ord(c)-65 for c in q['answer']]
                if q['kind']!='qc':it['nopt']=q['nopt']
            assert all((OUT/'img'/f).exists()for f in q['imgs'])
            items.append(it);audit.append({'section':section,'unit':uid,'question':q['n'],'kind':q['kind'],
                                           'sourceAnswer':q['sourceAnswer'],'answer':it['ans'],
                                           'reviewStatus':review['items'][q['n']-1]['status'],
                                           'independentAnswer':review['items'][q['n']-1]['independentAnswer'],
                                           'PDFPages':q['sourcePages'],'images':q['imgs']})
        supplement=section==13
        label='补充练习'if supplement else f'第{(section+1)//2}组 · Quant {1 if section%2 else 2}'
        title=f'{label}（{size}题 · {minutes}分钟）'
        objectives=[f'原书第{first}–{last}题，共{size}题，限时{minutes}分钟；做完整节再提交。',
                    '正式GRE数学第一节12题21分钟、第二节15题26分钟；本课按题数和时间配组。',
                    '比较题选一项，多选题须全选正确；数值题按原题要求输入数字、分数或四舍五入结果。',
                    '题目保留原式和图表，169题答案已逐题独立验算并与配套DOCX核对；提交前不显示答案。']
        if supplement:objectives.append('本节为最后7道数学题，13分钟按正式单题节奏折算，不是完整正式Section。原书第170项为“所有GRE数学单词都背好了吗”的复习提醒，不计作数学题或分数。')
        u={'id':uid,'title':title,'en':f'Hard Quant — Questions {first}–{last}',
           'minutes':minutes,'practice':True,'answerFormat':'gre-zq170-v1',
           'objectives':objectives,'blocks':[{'type':'gre-qset','base':'courses/gre-zq170/img/',
           'source':f'巍哥GRE数学170难题4.0（2026年）· 原书第{first}–{last}题',
           'noteTail':'（保留原题公式与图表；配套答案已逐题独立验算，非ETS官方认证）',
           'items':items}], 'references':[{'label':'ETS官方GRE考试结构：数学12题21分钟、15题26分钟','url':ETS}]}
        dump(OUT/f'{uid}.json',u)
        units.append({k:u[k]for k in ['id','title','en','minutes','practice']}|{'file':f'{uid}.json','hasQuiz':False})
        offset+=size
    assert offset==169
    dump(OUT/'course.json',{'id':'gre-zq170','title':'张巍GRE数学170难题：13节限时训练',
        'subtitle':'169道数学题；6组12题21分钟＋15题26分钟，另加7题13分钟补充练习。第170项为词汇复习提醒。',
        'order':19,'order_note':'选修，按现行GRE数学题数与时长编排；难题专项训练',
        'tier':'elective','tags':['GRE'],'units':units})
    pdf=next(SOURCE.glob('*170*.pdf'));doc=SOURCE/'难题170答案.docx'
    dump(HERE/'audit.json',{'sourcePDF':pdf.name,'pdfSHA256':hashlib.sha256(pdf.read_bytes()).hexdigest(),
        'answerDOCX':doc.name,'answerSHA256':hashlib.sha256(doc.read_bytes()).hexdigest(),
        'officialTimingSource':ETS,'officialTimingChecked':'2026-10-16',
        'questions':169,'units':13,'minutes':sum(u['minutes']for u in units),
        'kinds':dict(Counter(q['kind']for q in qs)),
        'answerPolicy':'169题逐题独立解题后对照配套DOCX，全部一致；57题另有程序复算，未发现需更正或待定答案；非ETS认证。',
        'answerReview':{'file':'answer-review.json','reviewed':169,'retained':169,'corrected':0,'pending':0,'computerChecked':57},
        'sourceItem170':'所有的GRE数学单词都背好了吗？（复习提醒，不计分）','items':audit})
    print('13 sections; 169 math questions; 295 minutes;',dict(Counter(q['kind']for q in qs)))
if __name__=='__main__':main()
