"""Reconcile independent OCR with existing transcription and image-reviewed overrides.

Prepare a candidate file without touching courses:
  python apply_review.py candidates.json final.json
Publish reviewed data and synchronize generator inputs:
  python apply_review.py candidates.json final.json --write
"""
import copy
from collections import Counter
import difflib
import json
import re
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]

def normalized(s):return re.sub(r'[^a-z0-9]+','',s.lower())
def clean(s):
    s=re.sub(r'\s+',' ',s).strip()
    s=re.sub(r'____(?:\s+____)+','____',s)
    s=re.sub(r"(\w)['’]\s+(s|t|re|ve|ll|d|m)\b",r'\1’\2',s)
    return s

def reconcile(previous,current):
    """Use coordinate-based new layout, preserving independently matching old spelling.

    Old instruction text and unmatched old fragments are never imported. Old blank
    markers survive only at aligned text boundaries.
    """
    if not previous:return clean(current)
    a=previous.split();b=current.split();out=[]
    for op,a0,a1,b0,b1 in difflib.SequenceMatcher(None,[normalized(x) if x!='____' else x for x in a],[normalized(x) if x!='____' else x for x in b],autojunk=False).get_opcodes():
        aa=a[a0:a1];bb=b[b0:b1]
        if op=='equal':out.extend(aa)
        elif op=='delete':
            if aa==['____']:out+=aa
        elif op=='replace' and len(aa)==len(bb):
            for old,new in zip(aa,bb):
                ratio=difflib.SequenceMatcher(None,normalized(old),normalized(new)).ratio()
                out.append(old if ratio>.67 and not re.search(r'[^A-Za-z0-9’“”\s.,;:!?()\-—–\"\'/]',old) else new)
        else:out.extend(bb)
    return clean(' '.join(out))

def format_blanks(s,n):
    s=re.sub(r'\bOil\)', '(iii)',s)
    s=re.sub(r'\bCli\)', '(ii)',s)
    s=re.sub(r'\((?:il|li|ll)\)', '(ii)',s)
    markers=list(re.finditer(r'\((?:i{1,3}|ili)\)',s,re.I))
    if len(markers)==n:
        s=re.sub(r'(?:____\s*)+','',s)
        num=iter(range(1,n+1))
        s=re.sub(r'\((?:i{1,3}|ili)\)',lambda m:'('+'i'*next(num)+') ____',s,flags=re.I)
    return clean(s)

def main():
    candidates=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    overrides=json.loads((HERE/'reviewed-overrides.json').read_text(encoding='utf-8'))
    libraries=json.loads((HERE/'reviewed-passages.json').read_text(encoding='utf-8'))
    ss={k:v for v in libraries.values() for k in v['questions']}
    old_sources={p.stem.removeprefix('txt-'):json.loads(p.read_text(encoding='utf-8')) for p in HERE.glob('txt-*.json')}
    units={p.stem:json.loads(p.read_text(encoding='utf-8')) for p in sorted((ROOT/'courses/gre-vx').glob('u*.json'))}
    final={};issues=[]
    for uid,u in units.items():
        for old in u['blocks'][0]['items']:
            key=uid+'/'+str(old['n']);c=candidates[key];it=copy.deepcopy(old)
            sid,image=old['img'].split('/')
            section=image.split('-')[0]
            tx=copy.deepcopy(c['txt']);prev=old.get('txt') or old_sources.get(sid,{}).get(str(int(section))+'-'+str(old['n']),{})
            # Keep the already visually reviewed pilot intact.
            if uid=='u01-2025-01-14-v1' and old['n']!=4:tx=copy.deepcopy(prev)
            else:
                for field in ('stem','pass'):
                    if tx.get(field):tx[field]=[reconcile(' '.join(prev.get(field,[])),' '.join(tx[field]))]
                if tx.get('opts'):
                    tx['opts']=[reconcile(prev.get('opts',[])[j] if j<len(prev.get('opts',[])) and len(prev['opts'][j].split())==len(s.split()) else '',s) for j,s in enumerate(tx['opts'])]
                if tx.get('cols') and prev.get('cols') and len(tx['cols'])==len(prev['cols']):
                    tx['cols']=[[reconcile(prev['cols'][j][i] if i<len(prev['cols'][j]) else '',s) for i,s in enumerate(col)] for j,col in enumerate(tx['cols'])]
            if key in overrides:tx.update(copy.deepcopy(overrides[key]))
            for field in ('opts','cols'):
                if field=='opts' and field in tx:tx[field]=[clean(s.replace('____','')) for s in tx[field]]
                if field=='cols' and field in tx:tx[field]=[[clean(s.replace('____','')) for s in col] for col in tx[field]]
            if key in ss:
                v=ss[key];tx={'stem':[v['stem']],'pass':[' '.join(v['sentences'])],'sentences':v['sentences']}
                c={**c,'kind':'ss'}
            kind=c['kind']
            if kind=='tc' and tx.get('cols'):
                tx['stem']=[format_blanks(' '.join(tx.get('stem',[])),len(tx['cols']))]
            # A missing field cannot silently masquerade as a complete transcription.
            flags=[]
            if not tx.get('stem') or not tx['stem'][0]:flags.append('missing_stem')
            if kind=='tc':
                if not tx.get('cols') or any(len(col)!=3 for col in tx['cols']):flags.append('missing_columns')
                elif ' '.join(tx['stem']).count('____')!=len(tx['cols']):flags.append('blank_count')
            elif kind=='ss':
                if not tx.get('sentences'):flags.append('missing_sentences')
            else:
                expected=6 if kind=='se' else 3 if kind=='mcn' else 5
                if len(tx.get('opts',[]))!=expected:flags.append('option_count')
                if kind=='se' and ' '.join(tx['stem']).count('____')!=1:flags.append('blank_count')
                if any(re.search(r'^(?:Select\b|[\[(]?[OCQ]\b|[\[(]3\b)',s,re.I) for s in tx.get('opts',[])):flags.append('option_junk')
            if re.search(r'[%=©�]|\b(?:oocp|___LQhan)\b',json.dumps(tx,ensure_ascii=False)):flags.append('ocr_symbols')
            it['txt']=tx;it['kind']=kind
            changed=kind!=old['kind']
            if kind=='ss':
                it.pop('nopt',None);it.pop('ans',None)
                it.setdefault('ansText','待核对（原答案表未提供，请按题意自评）')
            elif kind=='tc' and tx.get('cols'):
                it['blanks']=len(tx['cols']);changed|=it['blanks']!=old.get('blanks')
            elif tx.get('opts'):
                it['nopt']=len(tx['opts']);changed|=it['nopt']!=old.get('nopt')
            if changed and kind!='ss':
                it['legacyAnswer']={k:old[k] for k in ('kind','nopt','blanks','ans','ansText') if k in old}
                it['answerPending']=True;it['answerReviewReason']='题型或选项数已按原图修正，原答案映射需另行核对'
                it['ans']=[]
            if flags:issues.append(dict(key=key,flags=flags,image=it['img'],stem=tx.get('stem')))
            final[key]=it
    # Reuse the fullest available view of a shared passage, including scrolling
    # screenshots. A shorter question screenshot must not truncate its neighbors.
    shared={}
    for key,it in final.items():
        if it['txt'].get('pass'):
            prefix=normalized(' '.join(it['txt']['pass']))[:65]
            shared.setdefault(prefix,[]).append(key)
    for keys in shared.values():
        reviewed=next((key for key in keys if key in ss or 'pass' in overrides.get(key,{})),None)
        best=reviewed or max(keys,key=lambda key:len(' '.join(final[key]['txt']['pass'])))
        passage=final[best]['txt']['pass']
        for key in keys:
            if key not in ss:final[key]['txt']['pass']=copy.deepcopy(passage)
    # The first OCR line can be clipped under a scrolling pane header. Match
    # overlapping text within each section rather than relying only on prefixes.
    for uid,u in units.items():
        keys=[uid+'/'+str(it['n']) for it in u['blocks'][0]['items'] if final[uid+'/'+str(it['n'])]['txt'].get('pass')]
        remaining=set(keys)
        while remaining:
            first=min(remaining);a=' '.join(final[first]['txt']['pass'])
            tokens=lambda s:[normalized(w) for w in s.split()]
            related=[key for key in sorted(remaining) if difflib.SequenceMatcher(None,tokens(a),tokens(' '.join(final[key]['txt']['pass'])),autojunk=False).find_longest_match().size>=min(20,len(a.split()))]
            remaining.difference_update(related)
            counts=Counter(tuple(tokens(' '.join(final[key]['txt']['pass']))[:12]) for key in related)
            reviewed=next((key for key in related if key in ss or 'pass' in overrides.get(key,{})),None)
            anchor=reviewed or max(related,key=lambda key:counts[tuple(tokens(' '.join(final[key]['txt']['pass']))[:12])])
            aa=' '.join(final[anchor]['txt']['pass']).split()
            for key in related:
                if reviewed:break
                bb=' '.join(final[key]['txt']['pass']).split()
                match=max(difflib.SequenceMatcher(None,list(map(normalized,aa)),list(map(normalized,bb)),autojunk=False).get_matching_blocks(),key=lambda x:x.size)
                i,j,n=match
                right=aa[i+n:] if len(aa)-i-n>=len(bb)-j-n else bb[j+n:]
                aa=aa[:i]+aa[i:i+n]+right
            for key in related:
                if key not in ss:final[key]['txt']['pass']=[' '.join(aa)]
    for it in final.values():
        if it['txt'].get('pass') and re.search(r'completes? (?:the |this )?argument', ' '.join(it['txt']['stem']),re.I):
            last=it['txt']['pass'][-1]
            if not re.search(r'[.!?]$',last) and '____' not in last:
                it['txt']['pass'][-1]=last+' ____.'
    Path(sys.argv[2]).write_text(json.dumps({'items':final,'issues':issues},ensure_ascii=False,indent=1),encoding='utf-8')
    print('Prepared',len(final),'questions;',len(issues),'issues')
    print(json.dumps(issues,ensure_ascii=True))
    if '--write' not in sys.argv:return
    if issues:raise SystemExit('Resolve flagged issues before publishing.')
    source=json.loads((HERE.parent/'data.json').read_text(encoding='utf-8'))
    texts={}
    for uid,u in units.items():
        u['answerFormat']='gre-vx-text-v2'
        u['blocks'][0]['items']=[final[uid+'/'+str(i['n'])] for i in u['blocks'][0]['items']]
        if any(i['kind']=='ss' for i in u['blocks'][0]['items']):
            u['objectives']=[s for s in u['objectives'] if '选句子' not in s and '第 5 题点击' not in s]+['选句子题直接点击文章中的句子作答；交卷后对照答案自评，不计入分数。']
        (ROOT/'courses/gre-vx'/f'{uid}.json').write_text(json.dumps(u,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
        for it in u['blocks'][0]['items']:
            sid,image=it['img'].split('/');sec,n=image.removesuffix('.webp').split('-')
            texts.setdefault(sid,{})[str(int(sec))+'-'+str(it['n'])]={'ok':True,**it['txt']}
    for sid,tx in texts.items():
        (HERE/f'txt-{sid}.json').write_text(json.dumps(tx,ensure_ascii=False)+'\n',encoding='utf-8')
    for s in source:
        for sec in s['sections']:
            for it in sec['items']:
                image=f'{s["id"]}/{sec["sec"]}-{it["n"]:02d}.webp'
                reviewed=next(v for v in final.values() if v['img']==image)
                for k in ('kind','nopt','blanks','ans','ansText','answerPending','answerReviewReason','legacyAnswer'):
                    if k in reviewed:it[k]=reviewed[k]
                    else:it.pop(k,None)
    (HERE.parent/'data.json').write_text(json.dumps(source,ensure_ascii=False,indent=0)+'\n',encoding='utf-8')
    print('Published and synchronized all generator inputs.')

if __name__=='__main__':main()
