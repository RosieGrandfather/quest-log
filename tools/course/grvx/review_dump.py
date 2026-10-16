"""Print a bounded, deduplicated slice for independent answer review."""
import json, re, sys
from pathlib import Path
root=Path(__file__).resolve().parents[3]
lo,hi=map(int,sys.argv[1:3])
seen={}; passages={}
for idx,p in enumerate(sorted((root/'courses/gre-vx').glob('u*.json')),1):
    u=json.loads(p.read_text(encoding='utf8'))
    if lo<=idx<=hi: print('\nSECTION',idx,u['id'])
    for q in u['blocks'][0]['items']:
        t=q['txt']; key=re.sub(r'[^a-z0-9]','',json.dumps(t,sort_keys=True).lower())
        previous=seen.get(key); seen[key]=f'{idx:02d}/{q["n"]}'
        pas=' '.join(t.get('pass',[]))
        oldpass=passages.get(pas)
        if pas:passages[pas]=f'{idx:02d}/{q["n"]}'
        if not lo<=idx<=hi:continue
        if previous:
            print(q['n'],'SAME',previous);continue
        if pas: print('PASS SAME '+oldpass if oldpass else 'PASS '+pas)
        print(q['n'],q['kind'],q['img'],' '.join(t['stem']))
        if 'cols'in t:print(' | '.join(' / '.join(chr(65+i)+'='+v for i,v in enumerate(c)) for c in t['cols']))
        elif 'opts'in t:print(' | '.join(chr(65+i)+'='+v for i,v in enumerate(t['opts'])))
        else: print('SENTENCES',t['sentences'])
