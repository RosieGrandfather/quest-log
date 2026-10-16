"""Publish the recorded independent review, preserving original answers/choices.

Review input: reviewed-answers.tsv (letters are per-column for TC).
No web-answer scraping or generation is performed by this script.
"""
import copy
import json
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
FORMAT='gre-vx-text-v2-answers-all-20261016'

def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,value,indent=1):p.write_text(json.dumps(value,ensure_ascii=False,indent=indent)+'\n',encoding='utf8')

def main():
    files=sorted((ROOT/'courses/gre-vx').glob('u*.json'))
    units=[read(p)for p in files]
    lookup={f'{idx:02d}/{q["n"]}':q for idx,u in enumerate(units,1)for q in u['blocks'][0]['items']}
    baseline=copy.deepcopy(lookup)
    source=read(HERE/'data.json')
    metadata={f'{idx:02d}/{it["n"]}':it for idx,sec in enumerate([sec for s in source for sec in s['sections']],1)for it in sec['items']}
    sources=read(HERE/'review-answer-sources.json')
    fixes=read(HERE/'answer-text-fixes.json')
    overrides=read(HERE/'ocr/reviewed-overrides.json')
    # Apply transcriptions only where the review exposed missing/shifted choices.
    for key,fix in fixes.items():
        q=lookup[key];tx=q['txt']
        if 'copy'in fix:tx.update(copy.deepcopy(baseline[fix['copy']]['txt']))
        elif 'passFrom'in fix:tx['pass']=copy.deepcopy(baseline[fix['passFrom']]['txt']['pass'])
        else:tx.update(fix)
        if key.startswith('07/'):
            tx['pass']=["The large amount of methane in the atmosphere of Saturn’s giant moon Titan puzzles astronomers. Because methane is converted into heavier hydrocarbons by the Sun’s ultraviolet light, all the methane in Titan’s atmosphere should, at the present conversion rate, have disappeared in a few million years, long ago in Titan’s 4.5 billion years of existence. Something must be continuously feeding methane into Titan’s atmosphere. One possibility is that the methane comes from volcanic eruptions, but unless the supply rate were somehow precisely calibrated at a moderate level, either the methane would have run out by now or excess methane would have started to accumulate as a liquid ocean on the surface. However, data indicate that the atmosphere just above the surface is not humid, as would be expected above a pure methane ocean. A possible explanation was suggested by Lunine: when sunlight breaks down methane, the main product is ethane. Lunine noted that at Titan’s surface temperature, ethane is also a liquid. A liquid mixture of methane and ethane would produce low humidity. Such an ocean would slowly become richer in ethane while keeping the atmosphere supplied with methane."]
        uid=units[int(key[:2])-1]['id']
        overrides[uid+'/'+str(q['n'])]=copy.deepcopy(tx)
    rows={}
    for line in (HERE/'reviewed-answers.tsv').read_text(encoding='utf8').splitlines():
        if not line or line.startswith('#'):continue
        key,answer,reason=line.split('|',2)
        assert key not in rows,key
        rows[key]=(answer,reason)
    assert set(rows)=={k for k in lookup if not k.startswith('01/')},'Review must cover every remaining question'
    audit=[]
    for key,(answer,reason)in rows.items():
        q=lookup[key];old=baseline[key]
        reviewed=q.setdefault('answerReview',{
            'date':'2026-10-16','status':'independently-reviewed',
            'basis':'根据题干、选项及原文独立解题；非 ETS 官方答案表',
            'previous':{k:copy.deepcopy(old[k])for k in ('ans','ansText','answerPending')if k in old}})
        if key in sources:reviewed['corroboratingSource']=sources[key]
        reviewed['status']='pending-verification' if answer=='?' else 'independently-reviewed'
        if old['txt'].get('opts')!=q['txt'].get('opts'):
            reviewed.setdefault('previousChoices',copy.deepcopy(old['txt'].get('opts',[])))
        if q['kind']=='ss':
            q['ansText']=q['txt']['sentences'][int(answer)-1]
        elif answer=='?':
            q['answerPending']=True;q['answerReviewReason']=reason;q['ans']=[]
        else:
            q['ans']=[ord(c)-65 for c in answer]
            q.pop('answerPending',None);q.pop('answerReviewReason',None)
            if q['kind']=='tc':assert len(q['ans'])==q['blanks']
            elif q['kind']=='se':assert len(q['ans'])==2
            elif q['kind']=='mc1':assert len(q['ans'])==1
            assert all(0<=k<(3 if q['kind']=='tc' else q['nopt'])for k in q['ans']),key
        q['explanation']=reason
        meta=metadata[key]
        for k in ('ans','ansText','answerPending','answerReviewReason','answerReview','explanation'):
            if k in q:meta[k]=copy.deepcopy(q[k])
            else:meta.pop(k,None)
        audit.append({'question':units[int(key[:2])-1]['id']+'/'+str(q['n']),
                      'previous':reviewed['previous'],
                      'answer':q.get('ansText')if q['kind']=='ss' else q['ans'],
                      'key_changed':reviewed['previous'].get('ansText')!=q['ansText']if q['kind']=='ss' else reviewed['previous'].get('ans')!=q['ans'],
                      'choice_text_repaired':bool(reviewed.get('previousChoices')),
                      'basis':reason,'source':sources.get(key),'status':reviewed['status']})
    sections=[sec for s in source for sec in s['sections']]
    ocr={s['id']:read(HERE/'ocr'/f'txt-{s["id"]}.json')for s in source}
    for idx,(p,u,sec)in enumerate(zip(files,units,sections),1):
        if idx>1:
            u['answerFormat']=sec['answerFormat']=FORMAT
            u['objectives'][2]='这是考生考后回忆/拍屏整理的版本，没有官方解析；本节答案已按题意独立复核，交卷后附中文依据，不代表 ETS 官方答案'
        for q in u['blocks'][0]['items']:
            date=q['img'].split('/')[0]
            ocr[date][f'{sec["sec"]}-{q["n"]}']={'ok':True,**q['txt']}
        write(p,u)
    write(HERE/'data.json',source,0)
    write(HERE/'ocr/reviewed-overrides.json',overrides)
    for date,value in ocr.items():write(HERE/'ocr'/f'txt-{date}.json',value)
    write(ROOT/'docs/GRE_VX_ANSWER_AUDIT.json',audit)
    print(json.dumps({'reviewed_remaining':len(audit),'changed_keys':sum(r['key_changed']for r in audit),
                      'repaired_choices':sum(r['choice_text_repaired']for r in audit),
                      'pending':sum(q.get('answerPending',False)for q in lookup.values())}))

if __name__=='__main__':main()
