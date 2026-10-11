import re,json,os,sys
from PIL import Image
sys.path.insert(0,'.')
from seg import *
SC=2.0
def page_extent(p):
    d=data[p]; ys=[l['top'] for l in d['lines']]+[i[1] for i in d['images']]; ye=[l['bottom'] for l in d['lines']]+[i[3] for i in d['images']]
    return min(ys),max(ye)
def crop(start,end,out,pad=6):
    """start=(page,y) end=(page,y). Stitch pieces vertically."""
    pieces=[]
    for p in range(start[0],end[0]+1):
        ct,cb=page_extent(p)
        y0=start[1] if p==start[0] else ct-2
        y1=end[1] if p==end[0] else cb+2
        if y1-y0<3: continue
        # x extent from elements overlapping y range
        d=data[p]; xs=[];xe=[]
        for l in d['lines']:
            if l['bottom']>=y0 and l['top']<=y1: xs.append(l['x0']);xe.append(l['x1'])
        for (x0,t,x1,b) in d['images']:
            if b>=y0 and t<=y1: xs.append(x0);xe.append(x1)
        if not xs: continue
        pieces.append((p,y0,y1,min(xs),max(xe)))
    X0=max(0,min(p[3] for p in pieces)-pad); X1=min(612,max(p[4] for p in pieces)+pad)
    ims=[]
    for p,y0,y1,_,_ in pieces:
        im=Image.open(f'pg/p-{p:03d}.png').convert('RGB')
        ims.append(im.crop((int(X0*SC),int(max(0,y0)*SC),int(X1*SC),int(min(792,y1)*SC))))
    W=ims[0].width; H=sum(i.height for i in ims)
    canvas=Image.new('RGB',(W,H),'white'); y=0
    for i in ims: canvas.paste(i,(0,y)); y+=i.height
    # quantize to shrink
    q=canvas.quantize(colors=48,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    q.save(out,optimize=True)
    return canvas.size
def build_exam(sid,name,pa,pb,pe):
    E,mk,N=seg_exam(sid,pa,pb)
    key={int(k):v for k,v in keys[sid].items()}
    blocks={}; figs=[]
    qcr=set()
    figs_=[]
    for e in E:
        mm=re.match(r'^For Questions (\d+) to (\d+), compare Quantity A',e['text']) if e['k']=='T' else None
        if mm: qcr|=set(range(int(mm.group(1)),int(mm.group(2))+1))
    for e in E:
        mm=re.match(r'^Questions (\d+) (and|to) (\d+) are based',e['text']) if e['k']=='T' else None
        if mm: figs_.append(dict(a=int(mm.group(1))))
    # markers indexes
    idx=[mk[n] for n in range(1,N+1)]
    # DI statements
    stm=[(i,e) for i,e in enumerate(E) if e['k']=='T' and re.match(r'^Questions (\d+) (and|to) (\d+) are based',e['text'])]
    def isbound(i,n):
        e=E[i]
        if e['k']=='R' and (e['x1']-e['x0'])>400: return True
        if e['k']=='T' and HEAD.match(e['text']): return True
        if i in idx and i!=idx[n-1]: return True
        return False
    def lastb(m):
        bs=[x['bottom'] for x in E if x['p']==m['p'] and x['bottom']<=m['top'] and ((x['k']=='R' and (x['x1']-x['x0'])>400) or (x['k']=='T' and HEAD.match(x['text'])))]
        return (max(bs)-1) if bs else -1
    firsts={f['a'] for f in figs_}
    prev_end=None
    for n in range(1,N+1):
        i=idx[n-1]; m=E[i]
        # QC image containing marker
        qimg=None
        for j,e in enumerate(E):
            if e['k']=='I' and e['p']==m['p'] and e['x0']<70 and e['top']-3<=m['top']<=e['bottom']+3 and (e['bottom']-e['top'])>30:
                # only treat as QC row if key says quantity comparison
                if n in qcr: qimg=j
        if qimg is not None:
            e=E[qimg]
            if prev_end is None:
                pe_=[x for x in E if x['p']==m['p'] and x['k'] in 'TI' and x['top']>=lastb(m)]
                start=(m['p'],min(x['top'] for x in pe_)-1)
            else: start=(prev_end[0],prev_end[1]+1)
            end=(e['p'],max(e['bottom'],m['bottom'])+2)
            blocks[n]=(start,end,'qc')
            prev_end=end
        else:
            j=i+1; blk=[i]
            while j<len(E) and not isbound(j,n):
                blk.append(j); j+=1
            content=[k for k in blk if E[k]['k'] in 'TI']
            opts=[k for k in content if E[k]['k']=='I' and E[k]['x0']<62 and (E[k]['x1']-E[k]['x0'])<100 and 0.6<(E[k]['bottom']-E[k]['top'])/max(1,(E[k]['x1']-E[k]['x0']))<1.6 and k>i]
            if opts:
                lo=E[opts[-1]]
                rows=[k for k in content if E[k]['p']==lo['p'] and E[k]['k']=='T' and lo['top']-6<=E[k]['top']<=lo['bottom']+4]
                endel=[lo]+[E[k] for k in rows]
                eb=max(x['bottom'] for x in endel)
                ch=True
                while ch:
                    ch=False
                    for k in content:
                        x=E[k]
                        if x['p']==lo['p'] and x['top']<=eb+2 and x['bottom']>eb and k>opts[0]-1: eb=x['bottom'];ch=True
                nxt=[E[k]['top'] for k in range(blk[-1]+1,len(E)) if E[k]['p']==lo['p'] and E[k]['k'] in 'TI' and E[k]['top']>eb-3]
                lim=(min(nxt)-2) if nxt else eb+14
                end=(lo['p'],min(eb+14,max(lim,eb))+2)
            else:
                last=E[content[-1]]; end=(last['p'],last['bottom']+2)
            # premise elements before the marker (after the last boundary)
            start=(m['p'],m['top']-2)
            if prev_end is not None:
                # find elements between prev block end and marker
                pre=[k for k in range(i-1,-1,-1) if (E[k]['p'],E[k]['bottom'])>prev_end]
                # walk back until a boundary
                prem=[];bd=None
                for k in range(i-1,-1,-1):
                    if (E[k]['p'],E[k]['bottom'])<=(prev_end[0],prev_end[1]): break
                    if E[k]['k']=='R' or (E[k]['k']=='T' and HEAD.match(E[k]['text'])): bd=E[k]; break
                    if E[k]['k'] in 'TI': prem.append(E[k])
                if bd is not None: prem=[x for x in prem if (x['p'],x['top'])>=(bd['p'],bd['bottom']-1)]
                if n in firsts: prem=[]
                if prem:
                    f=min(prem,key=lambda x:(x['p'],x['top'])); start=(f['p'],f['top']-2)
            blocks[n]=(start,end,'x'); prev_end=end
    # figures
    for si,(i,e) in enumerate(stm):
        mm=re.match(r'^Questions (\d+) (and|to) (\d+)',e['text']); a,b=int(mm.group(1)),int(mm.group(3))
        # DI set statement may be repeated in explanation; here only exam
        fig_end=(E[idx[a-1]]['p'],E[idx[a-1]]['top']-2)
        figs.append(dict(a=a,b=b,start=(e['p'],e['top']-3),end=fig_end))
    return blocks,figs,E,mk,N
def build_expl(sid,pb,pe):
    pa=pb  # explanations start page
    E=elems(pa,pe)
    ex=[i for i,e in enumerate(E) if e['k']=='T' and e['text'].strip()=='Explanation']
    res=[]
    for k,i in enumerate(ex):
        lim=ex[k+1] if k+1<len(ex) else len(E)
        j=next((j for j in range(i+1,lim) if E[j]['k']=='T' and E[j]['text'].startswith('This explanation uses')),None)
        if j is None:
            res.append((E[i],None)); continue
        last=j; q=j+1
        while q<lim and (E[q]['k']=='T' and E[q]['text'].startswith('Strategy')): last=q; q+=1
        res.append((E[i],E[last]))
    return res
if __name__=='__main__':
    for sid,name,pa,pb,pe in SETS:
        blocks,figs,E,mk,N=build_exam(sid,name,pa,pb,pe)
        ex=build_expl(sid,pb,pe)
        miss=[k+1 for k,(a,b) in enumerate(ex) if b is None]
        print(sid,'N',N,'expl',len(ex),'no-strategy',miss,'figs',[(f['a'],f['b']) for f in figs],'qc',[n for n,b in blocks.items() if b[2]=='qc'])
