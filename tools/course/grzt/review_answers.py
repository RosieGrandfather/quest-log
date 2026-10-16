"""Check the authored semantic review against the course, source TXT and PDF.
Does not change answer keys or add explanations to the lessons.
"""
import hashlib
import json
import re
from pathlib import Path

from build import REPO, extract, clean

HERE = Path(__file__).resolve().parent
SOURCE = Path('C:/projects/learning/GRE prep/张巍GRE/verbal')
PDF = next(SOURCE.glob('*2000*.pdf'))
KEY = SOURCE / '填空2000答案.txt'
LETTERS = 'ABCDEFGHI'
ROWS = HERE.joinpath('reviewed-sections.tsv').read_text(encoding='utf-8').splitlines()[1:]
course = json.loads((REPO/'courses/gre-zt/course.json').read_text(encoding='utf-8'))
pdf_sections = extract(PDF)
keys = {}
for line in KEY.read_text(encoding='utf-8-sig').splitlines():
    if m := re.match(r'test\s+(\d+)',line,re.I): test = int(m[1])
    elif m := re.match(r'section\s+([12])\s+(.+)',line,re.I):
        keys[test,int(m[1])] = [a for a in m[2].split('/') if a]
assert len(ROWS) == len(course['units']) == 50
audit = []
for i, (row, entry, pdf_section) in enumerate(zip(ROWS,course['units'],pdf_sections),1):
    number, candidate_keys, reasons = row.split('\t')
    candidates, reasons = candidate_keys.split('/'), reasons.split('|')
    assert int(number)==i and len(candidates)==len(reasons)==7
    unit = json.loads((REPO/'courses/gre-zt'/entry['file']).read_text(encoding='utf-8'))
    for q, pq, candidate, reason, source in zip(unit['blocks'][0]['items'],pdf_section['items'],candidates,reasons,keys[(i+1)//2, (i-1)%2+1]):
        assert q['sourceAnswer']==source
        expected=[LETTERS.index(c)-(3*j if q['kind']=='tc' else 0) for j,c in enumerate(source)]
        assert q['ans']==expected
        assert q['txt']['stem']==[re.sub(r'_{3,}','____',clean(' '.join(pq['stem'])))]
        options=q['txt'].get('opts') or sum(q['txt']['cols'],[])
        assert options==[pq['opts'][c] for c in LETTERS[:len(pq['opts'])]]
        audit.append({'unit':unit['id'],'lesson':i,'test':(i+1)//2,'section':(i-1)%2+1,
                      'question':q['n'],'sourceAnswer':source,'reviewCandidate':candidate,
                      'matchesSource':source==candidate,
                      'status':'version-dependent-low-confidence' if (i,q['n'])==(14,5) else 'supported',
                      'basis':reason,'sourcePDFPages':list(range(pq['start'][0]+1,pq['end'][0]+2))})
assert len(audit)==350
report={'date':'2026-10-16','course':'gre-zt','questions':350,'supported':349,
        'versionDependent':1,'differentCandidateCount':sum(not q['matchesSource'] for q in audit),
        'answerKeysChanged':0,'method':'逐题阅读题干及全部选项后推理；非盲审、非ETS官方答案认证。另核对本地TXT映射、PDF文字及选项顺序；疑难题回看原页并查询公开同题版本。',
        'sourcePDFSHA256':hashlib.sha256(PDF.read_bytes()).hexdigest(),
        'answerTXTSHA256':hashlib.sha256(KEY.read_bytes()).hexdigest(),
        'externalChecks':[
            {'lesson':14,'question':5,'url':'https://gre.kmf.com/explain/index/81w0ok','observation':'相同题干、不同选项版本；该页选项包含circumscribed/restricted。不能把该版本字母搬入本地版本。'},
            {'lesson':14,'question':5,'url':'https://gre.myprepclub.com/forum/the-book-brings-together-many-valuable-reports-on-conservation-project-30502.html','observation':'与本地相同的选项版本给BC；论坛标注Official Answer不等于ETS认证。'},
            {'lesson':42,'question':4,'url':'https://cc.xdf.cn/gre/201708/298360750.html','observation':'公开同题也出现enlivened等不顺措辞，不能据此擅自补写否定。'},
            {'lesson':47,'question':1,'url':'https://gre.kmf.com/explain/index/0cw89k','observation':'同题句尾同样不顺，页面答案D。'},
            {'lesson':2,'question':5,'url':'https://www.sohu.com/a/291241431_479533','observation':'相同题文与选项，作者给CD，与本轮brook/tolerate推理相符。'}],
        'items':audit}
(REPO/'docs/GRE_ZT_ANSWER_AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert report['differentCandidateCount']==0
print('350 reviewed: 349 supported, 1 version-dependent; 0 answer keys changed. PDF/TXT/course mappings agree.')
