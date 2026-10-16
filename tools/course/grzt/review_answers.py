"""Check the authored semantic review against the course, source TXT and PDF.
Round 1 covers lessons 1-50 (Test 1-25); round 2 covers lessons 51-100 (Test 26-50).
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
pdf_sections = extract(PDF, (1, 50))
keys = {}
for line in KEY.read_text(encoding='utf-8-sig').splitlines():
    if m := re.match(r'test\s+(\d+)',line,re.I): test = int(m[1])
    elif m := re.match(r'section\s+([12])\s+(.+)',line,re.I):
        keys[test,int(m[1])] = [a for a in m[2].split('/') if a]
assert len(ROWS) == len(course['units']) == 100
# Round 2 was blind (answer keys hidden from reviewers); these are the only blind answers that differed.
# Each was re-read and the source key kept; see docs/GRE_ZT_ANSWER_REVIEW.md.
BLIND_DIFF = {(64,6):'AD',(72,2):'BF',(79,3):'CDI',(83,5):'CF',(86,2):'AF',(86,3):'AF',(99,3):'ADI'}
LOW_CONFIDENCE = {(14,5):'version-dependent-low-confidence',(79,3):'low-confidence',(83,5):'low-confidence',(99,3):'low-confidence'}
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
                      'round':1 if i<=50 else 2,
                      'blindCandidate':(BLIND_DIFF.get((i,q['n']),source) if i>50 else None),
                      'status':LOW_CONFIDENCE.get((i,q['n']),'supported'),
                      'basis':reason,'sourcePDFPages':list(range(pq['start'][0]+1,pq['end'][0]+2))})
assert len(audit)==700
low=sum(q['status']!='supported' for q in audit)
report={'date':'2026-10-16','course':'gre-zt','questions':700,'supported':700-low,
        'lowConfidence':low,'blindDisagreements':len(BLIND_DIFF),'differentCandidateCount':sum(not q['matchesSource'] for q in audit),
        'answerKeysChanged':0,'method':{'round1':'第1–50节：逐题阅读题干及全部选项后推理；非盲审、非ETS官方答案认证。另核对本地TXT映射、PDF文字及选项顺序；疑难题回看原页并查询公开同题版本。',
                 'round2':'第51–100节：遮住答案键盲做全部350题，再与配套答案比对；7处不一致逐题复读并查询公开同题版本，均保留原答案。非ETS官方答案认证。'},
        'sourcePDFSHA256':hashlib.sha256(PDF.read_bytes()).hexdigest(),
        'answerTXTSHA256':hashlib.sha256(KEY.read_bytes()).hexdigest(),
        'externalChecks':[
            {'lesson':14,'question':5,'url':'https://gre.kmf.com/explain/index/81w0ok','observation':'相同题干、不同选项版本；该页选项包含circumscribed/restricted。不能把该版本字母搬入本地版本。'},
            {'lesson':14,'question':5,'url':'https://gre.myprepclub.com/forum/the-book-brings-together-many-valuable-reports-on-conservation-project-30502.html','observation':'与本地相同的选项版本给BC；论坛标注Official Answer不等于ETS认证。'},
            {'lesson':42,'question':4,'url':'https://cc.xdf.cn/gre/201708/298360750.html','observation':'公开同题也出现enlivened等不顺措辞，不能据此擅自补写否定。'},
            {'lesson':47,'question':1,'url':'https://gre.kmf.com/explain/index/0cw89k','observation':'同题句尾同样不顺，页面答案D。'},
            {'lesson':2,'question':5,'url':'https://www.sohu.com/a/291241431_479533','observation':'相同题文与选项，作者给CD，与本轮brook/tolerate推理相符。'},
            {'lesson':64,'question':6,'url':'https://gre.kmf.com/explain/index/01vtjk','observation':'同题同选项，多家题库给DE；原论文措辞为spatial homogeneity。'},
            {'lesson':83,'question':5,'url':'https://gre-sanqian.kmf.com/explain/question/81pmzj-0.html?isFav=0','observation':'同题同选项，页面答案AC；recipe亦接近，低把握保留。'},
            {'lesson':86,'question':2,'url':'https://gre.kmf.com/explain/index/baw8uk','observation':'同题同选项，答案CF；新东方解析指出carefully assembled限定细节，exhaustive为陷阱。'},
            {'lesson':86,'question':3,'url':'https://gre.kmf.com/explain/index/32w93k','observation':'同题同选项，答案AD；竞争方案更站不住脚，故淡化失败。'}],
        'items':audit}
(REPO/'docs/GRE_ZT_ANSWER_AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert report['differentCandidateCount']==0
print(f'700 reviewed: {700-low} supported, {low} low-confidence; {len(BLIND_DIFF)} blind disagreements in round 2 re-checked; 0 answer keys changed. PDF/TXT/course mappings agree.')
