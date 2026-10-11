import json,re
from crop import *
meta=json.load(open('meta.json'))
out={}
for sid,name,pa,pb,pe in SETS:
    blocks,figs,E,mk,N=build_exam(sid,name,pa,pb,pe)
    K={int(k):v for k,v in keys[sid].items()}
    qs=[]
    for n in range(1,N+1):
        (s,e,t)=blocks[n]
        els=[x for x in E if (x['p'],x['top'])>=s and (x['p'],x['bottom'])<=(e[0],e[1]+3) and (x['p'],x['top'])<=(e[0],e[1])]
        txt=' '.join(x.get('text','') for x in els if x['k']=='T')
        k=K[n]
        letters=re.findall(r'Choice ([A-H])',k)
        if t=='qc': typ='qc';no=4;ans=letters
        elif letters:
            no=sum(1 for x in els if x['k']=='I' and x['x0']<62 and (x['x1']-x['x0'])<100 and 0.6<(x['bottom']-x['top'])/max(1,x['x1']-x['x0'])<1.6)
            all_=bool(re.search(r'Indicate\s+all',txt)) or len(letters)>1
            typ='mcn' if all_ else 'mc1'; ans=letters
        else:
            typ='ne';ans=k.strip();no=0
        qs.append(dict(n=n,type=typ,nopt=no,ans=ans,txt=txt[:60]))
    out[sid]=qs
json.dump(out,open('qmeta.json','w'),ensure_ascii=False,indent=1)
for sid,qs in out.items():
    print(sid,[(q['n'],q['type'],q['nopt'],q['ans']) for q in qs if q['type']!='qc'])
