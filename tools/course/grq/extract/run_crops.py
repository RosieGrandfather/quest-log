import os,json
from crop import *
meta={}
for sid,name,pa,pb,pe in SETS:
    os.makedirs(f'img/{sid}',exist_ok=True)
    blocks,figs,E,mk,N=build_exam(sid,name,pa,pb,pe)
    ex=build_expl(sid,pb,pe)
    EE=elems(pb,pe)
    m={'q':{},'e':{},'f':[]}
    for n,(s,e,t) in blocks.items():
        sz=crop(s,e,f'img/{sid}/q{n}.png'); m['q'][n]=dict(type=t,size=sz)
    for k,f in enumerate(figs):
        sz=crop(f['start'],f['end'],f'img/{sid}/f{k+1}.png'); m['f'].append(dict(a=f['a'],b=f['b'],size=sz))
    for k,(a,b) in enumerate(ex):
        n=k+1
        if b is None:
            # fallback: up to before next restated question marker
            i0=EE.index(a)
            nxt=next((j for j in range(i0+1,len(EE)) if ismarker(EE[j],n+1)),None)
            last=max(j for j in range(i0+1,nxt) if EE[j]['k'] in 'TI') if nxt else len(EE)-1
            b=EE[last]
        sz=crop((a['p'],a['top']-3),(b['p'],b['bottom']+3),f'img/{sid}/e{n}.png'); m['e'][n]=dict(size=sz)
    meta[sid]=m
    print(sid,'done',len(m['q']),len(m['e']),len(m['f']))
json.dump(meta,open('meta.json','w'),indent=1)
