import sys,os,re,subprocess,json,statistics
from PIL import Image,ImageOps
import ocrt
def tsv_words(im,psm=4):
    f=f'/tmp/p_{os.getpid()}.png';im.save(f)
    t=subprocess.run(['tesseract',f,'-','--psm',str(psm),'-l','eng','tsv'],capture_output=True,text=True,env={**os.environ,'OMP_THREAD_LIMIT':'1'}).stdout
    W=[]
    for ln in t.split('\n')[1:]:
        c=ln.split('\t')
        if len(c)<12 or not c[11].strip():continue
        try:conf=float(c[10])
        except:continue
        W.append(dict(x=int(c[6]),y=int(c[7]),w=int(c[8]),h=int(c[9]),t=c[11].strip(),conf=conf,blk=int(c[2]),par=int(c[3]),ln=int(c[4])))
    return W
def add_blanks(W,hl):
    """把被去掉的下划线（填空处）补回成 '____' 词，插到对应文字行里"""
    if not hl or not W:return W
    d={}
    for w in W:d.setdefault((w['blk'],w['par'],w['ln']),[]).append(w)
    L=[]
    for k,ws in d.items():
        L.append((k,min(w['y'] for w in ws),max(w['y']+w['h'] for w in ws),statistics.median(w['h'] for w in ws)))
    out=list(W);used=set()
    for y,x0,x1 in hl:
        wd=x1-x0
        if not 120<=wd<=900:continue
        if sum(1 for y2,a,b in hl if (y2,a,b)!=(y,x0,x1) and abs(a-x0)<40 and abs(b-x1)<40)>=2:continue   # 表格横线（同宽成排）不是填空下划线
        best=None
        for k,ty,by,h in L:
            if ty-0.3*h<=y<=by+0.9*h and (best is None or abs(y-by)<abs(y-best[2])):best=(k,ty,by,h)
        if not best:continue
        k,ty,by,h=best
        # 表格线（同一 y 附近成排的线）不算：下划线下方紧贴文字、且至少有一个单词与其横向重叠或相邻
        near=[w for w in d[k] if w['x']<=x1+30 and w['x']+w['w']>=x0-30]
        if not near and not (x0>min(w['x'] for w in d[k])-30):continue
        out.append(dict(x=x0,y=ty,w=wd,h=int(h),t='____',conf=99.0,blk=k[0],par=k[1],ln=k[2]))
    return out
def lines_of(W,gapk=2.4):
    """group words into lines by (blk,par,ln), insert ____ for big gaps, return list of dict(x,y,h,text,x1)"""
    d={}
    for w in W:d.setdefault((w['blk'],w['par'],w['ln']),[]).append(w)
    out=[]
    for k,ws in d.items():
        ws.sort(key=lambda w:w['x'])
        hh=statistics.median(w['h'] for w in ws)
        gaps=[b['x']-(a['x']+a['w']) for a,b in zip(ws,ws[1:])]
        txt=ws[0]['t'];
        for g,w in zip(gaps,ws[1:]):
            if g>gapk*hh and g>40:txt+=' ____ '+w['t']
            else:txt+=' '+w['t']
        out.append(dict(x=ws[0]['x'],y=min(w['y'] for w in ws),y1=max(w['y']+w['h'] for w in ws),h=hh,x1=ws[-1]['x']+ws[-1]['w'],text=txt,words=ws))
    out.sort(key=lambda l:(l['y']))
    return out
def crop_scaled(path,box=None,scale=None):
    im=Image.open(path).convert('RGB');H=im.size[1]
    y=ocrt.hb(im)
    if not .03*H<=y<=.2*H:y=int(H*.095)
    im=im.crop((0,y,im.size[0],H))
    return im
def prep_new(im,scale):
    import cv2,numpy as np
    im=im.resize((im.size[0]*scale,im.size[1]*scale),Image.LANCZOS).convert('L')
    a=np.array(im);b=(a<150).astype('uint8')
    h=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(110,1)))
    v=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(1,70)))
    global LASTHL
    n,lab,st,_=cv2.connectedComponentsWithStats(cv2.dilate(h,np.ones((3,3),'uint8')))
    LASTHL=[(int(y+hh/2),int(x),int(x+w)) for x,y,w,hh,area in st[1:] if w>=150 and hh<=30]
    blocks=[(x,y,w,hh) for x,y,w,hh,area in st[1:] if w>=150 and 60<=hh<=170 and w<a.shape[1]*.5]
    hh_=h.copy()
    for x,y,w,hh in blocks:hh_[max(0,y-3):y+hh+3,max(0,x-3):x+w+3]=0
    m=cv2.dilate(((hh_|v)>0).astype('uint8'),np.ones((5,5),'uint8'))
    a=a.copy();a[m>0]=255
    for x,y,w,hh in blocks:
        a[y+3:y+hh-3,x+3:x+w-3]=255-a[y+3:y+hh-3,x+3:x+w-3]
        a[y:y+3,x:x+w]=255;a[y+hh-3:y+hh,x:x+w]=255
    return ImageOps.autocontrast(Image.fromarray(a),cutoff=1)
def prep_old(im,scale):
    import cv2,numpy as np
    global LASTHL
    im=im.resize((im.size[0]*scale,im.size[1]*scale),Image.LANCZOS).convert('L')
    a=np.array(im);b=(a<150).astype('uint8')
    h=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(110,1)))
    v=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(1,70)))
    n,lab,st,_=cv2.connectedComponentsWithStats(cv2.dilate(h,np.ones((3,3),'uint8')))
    LASTHL=[(int(y+hh/2),int(x),int(x+w)) for x,y,w,hh,area in st[1:] if w>=150 and hh<=14]
    m=cv2.dilate(((h|v)>0).astype('uint8'),np.ones((5,5),'uint8'))
    a=a.copy();a[m>0]=255
    return ImageOps.autocontrast(Image.fromarray(a),cutoff=1)
def prep(im,scale):
    return prep_new(im,scale) if os.environ.get('INV') else prep_old(im,scale)
def divider(im):
    """x of vertical pane divider (original px) or None"""
    g=im.convert('L');W,H=g.size
    px=g.load();best=(0,None)
    y0,y1=int(H*.12),int(H*.88)
    for x in range(int(W*.38),int(W*.62)):
        dark=sum(1 for y in range(y0,y1,3) if px[x,y]<215)
        r=dark/((y1-y0)/3)
        if r>best[0]:best=(r,x)
    return best

SC=3
INSTR=re.compile(r'^(for each blank|select one entry|consider each of the choices|select the two|select one or more|select one answer|select all|select two|questions? \d+|click on|select the sentence|choose the two|fill (the|all)|each blank|answer choices that|best completes|completes the text|apply\.?$)',re.I)
FOOT=re.compile(r'^(select one|select two|select all|select the|click on|select one or more|select one entry)',re.I)
def clean(ls):
    out=[]
    for l in ls:
        t=l['text'].strip()
        alpha=sum(c.isalnum() for c in t)
        if alpha<2:continue
        avgc=statistics.mean(w['conf'] for w in l['words'])
        if avgc<25 and alpha<8:continue
        out.append(l)
    return out
def groups(ls,k=.55):
    g=[]
    for l in ls:
        if g and l['y']-g[-1][-1]['y1']<=k*l['h']:g[-1].append(l)
        else:g.append([l])
    return g
def paras(ls):
    """reflow passage lines -> paragraphs list"""
    if not ls:return []
    xs=sorted(l['x'] for l in ls);mx=xs[len(xs)//5];hh=statistics.median(l['h'] for l in ls)
    ps=[];cur=[]
    for i,l in enumerate(ls):
        newp=cur and (l['x']>mx+1.3*hh or l['y']-ls[i-1]['y1']>.8*hh)
        if newp:ps.append(' '.join(cur));cur=[]
        cur.append(l['text'].strip())
    if cur:ps.append(' '.join(cur))
    return [fixtxt(p) for p in ps]
def strip_glyph(l):
    ws=l['words']
    out=[w for w in ws if w['t'] not in ('|','||','!')]
    ws=out
    if len(ws)>=2:
        a,b=ws[0],ws[1]
        gap=b['x']-(a['x']+a['w'])
        t=a['t']
        nonal=any(not c.isalnum() for c in t)
        if (nonal and len(t)<=4 and not re.fullmatch(r'["“‘\'(]\w*',t)) or (len(t)<=3 and gap>1.0*l['h'] and t not in ('A','I','a')) or (t in ('O','o','C','c','Q','©') and gap>.6*l['h']):
            ws=ws[1:]
    return ' '.join(w['t'] for w in ws)
def parse_page(path):
    im=crop_scaled(path);W,H=im.size
    r,x=divider(im)
    if r>.8:
        left=im.crop((0,0,x-3,H));right=im.crop((x+4,0,W,H))
        L=clean(lines_of(tsv_words(prep(left,SC))));R=clean(lines_of(tsv_words(prep(right,SC))))
        # coordinates remain in scaled space
        L=[l for l in L if not re.match(r'^questions? \d+',l['text'],re.I)]
        return dict(two=True,left=L,right=R)
    pp=prep(im,SC);hl=list(LASTHL)
    return dict(two=False,left=[],right=clean(lines_of(add_blanks(tsv_words(pp),hl))),hl=hl)
def stem_opts(R,n):
    R=[l for l in R if not FOOT.match(l['text'].strip()) or len(l['text'])>60]
    g=groups(R)
    # drop leading instruction group
    while g and INSTR.match(' '.join(x['text'] for x in g[0]).strip()) and len(g)>1:g=g[1:]
    cands=[]
    st=[i for i,l in enumerate(R) if strip_glyph(l)!=' '.join(w['t'] for w in l['words']) and sum(c.isalnum() for c in l['text'])>2]
    if len(st)==n:
        seg=[R[a:b] for a,b in zip(st,st[1:]+[len(R)])]
        pre=[l for l in R[:st[0]]]
        cands.append(([ [l] for l in pre ] if False else groups(pre),seg))
    if len(g)>n:cands.append((g[:-n],g[-n:]))
    lines=[[l] for l in R]
    if len(lines)>n:
        # each line one option
        cands.append((lines[:-n],lines[-n:]))
    best=None
    for stem,op in cands:
        if len(op)==n:best=(stem,op);break
    if not best:return None
    stem,op=best
    stxt=paras([l for gg in stem for l in gg])
    opts=[opt_text(gg) for gg in op]
    return stxt,opts

def fixtxt(t):
    t=re.sub(r"([A-Za-z])’ (s|t|re|ve|ll|d|m)\b",r"\1’\2",t)
    t=re.sub(r"\s+(____\s*)?[}\]\)|]+\s*$","",t)
    t=re.sub(r"(?<=[A-Za-z,;:.’])\s+\|\s+(?=[a-z])",' I ',t)
    t=re.sub(r"\s*\|\s*",' ',t)
    t=re.sub(r"\((il|Ii|li|I1|ii|i|iii|ili|lii)\)(?!\s*____)(\s)",lambda m:'('+{'il':'ii','Ii':'ii','li':'ii','I1':'ii','ili':'iii','lii':'iii'}.get(m.group(1),m.group(1))+') ____'+m.group(2),t)
    t=re.sub(r"(____\s*)+","____ ",t)
    tk=t.split()
    if '____' in tk:
        li=max(i for i,x in enumerate(tk) if x=='____')
        tail=tk[li+1:]
        if tail and all(len(x)<=3 and re.fullmatch(r'[_\w]+',x) for x in tail) and len(tail)<=4 and li>=len(tk)-5:tk=tk[:li+1]
    t=' '.join(tk)
    t=re.sub(r"\s+",' ',t).strip()
    t=re.sub(r"^[\s\-—–|\[\]]+|[\s\-—–|\[\]]+$","",t)
    tk=t.split()
    while len(tk)>1 and sum(c.isalnum() for c in tk[-1])<3 and any(not c.isalnum() for c in tk[-1]) and tk[-1] not in ('____',) and not re.search(r'[.,;:!?)]',tk[-1]):tk.pop()
    t=' '.join(tk)
    return t
def opt_text(gg):
    parts=[strip_glyph(gg[0])]+[l['text'] for l in gg[1:]]
    return fixtxt(' '.join(parts))

import difflib
def passage_paras(L,H):
    L=[l for l in L if l['y']>85 and not re.match(r'^questions? ',l['text'],re.I)]
    # drop bottom cut line
    if L and (L[-1]['y1']>H-12 or statistics.mean(w['conf'] for w in L[-1]['words'])<60):
        L=L[:-1] if L[-1]['y1']>H-12 else L
    L=[l for l in L if statistics.mean(w['conf'] for w in l['words'])>=35]
    return paras(L)
def merge_pass(p1,p2):
    if not p1:return p2
    if not p2:return p1
    tok=lambda ps:[w for i,p in enumerate(ps) for w in ((['¶'] if i else [])+p.split())]
    a,b=tok(p1),tok(p2)
    na=[x.lower() for x in a];nb=[x.lower() for x in b]
    sm=difflib.SequenceMatcher(None,na,nb,autojunk=False)
    m=max(sm.get_matching_blocks(),key=lambda x:x.size)
    if m.size<8:return None
    i,j,k=m
    if j>3:  # p2 starts earlier than p1? then prefer p2 head
        mer=b[:j]+a[i:]  # unlikely
    else:mer=a[:i]+b[j:]
    ps=[];cur=[]
    for w in mer:
        if w=='¶':ps.append(' '.join(cur));cur=[]
        else:cur.append(w)
    ps.append(' '.join(cur));return [fixtxt(p) for p in ps if p.strip()]
def tc_lines(R,hl,blanks):
    if not hl:return None
    cols=[]
    for y,x0,x1 in sorted(hl,key=lambda t:(t[1],t[0])):
        for c in cols:
            if abs(c['x0']-x0)<40 and abs(c['x1']-x1)<40:c['ys'].append(y);break
        else:cols.append(dict(x0=x0,x1=x1,ys=[y]))
    cols=[c for c in cols if len(c['ys'])>=3]
    cols.sort(key=lambda c:c['x0'])
    if len(cols)!=blanks:return None
    out=[];top=None
    for c in cols:
        ys=sorted(set(c['ys']))
        # merge near-duplicate lines
        z=[ys[0]]
        for y in ys[1:]:
            if y-z[-1]>12:z.append(y)
        ys=z
        if len(ys)==3:
            g1,g2=ys[1]-ys[0],ys[2]-ys[1]
            if max(g1,g2)>=1.6*min(g1,g2):
                ys=sorted(ys+[(ys[0]+ys[1])/2 if g1>g2 else (ys[1]+ys[2])/2])
        if len(ys)<4:return None
        if len(ys)>4:ys=ys[-4:]
        top=ys[0] if top is None else min(top,ys[0])
        band=[[],[],[]]
        for l in R:
            for w in l['words']:
                cxw=w['x']+w['w']/2
                if not(c['x0']-15<=cxw<=c['x1']+15):continue
                cy=w['y']+w['h']/2
                for b in range(3):
                    if ys[b]<=cy<ys[b+1]:band[b].append((l['y'],w['x'],w['t']))
        out.append([fixtxt(' '.join(t for _,_,t in sorted(b))) for b in band])
    if any(not o for col in out for o in col):return None
    stemL=[l for l in R if l['y1']<top-5 and not re.match(r'^\s*Blank\b',l['text'])]
    g=groups(stemL)
    while g and INSTR.match(' '.join(x['text'] for x in g[0]).strip()) and len(g)>1:g=g[1:]
    return paras([l for gg in g for l in gg]),out
def tc_parse(R,blanks):
    labs=[l for l in R if re.match(r'^Blank\\b',l['text'].strip(),re.I) or l['text'].count('Blank')>=1]
    if not labs:return None
    lab=labs[0];ly=lab['y']
    cx=[]
    ws=lab['words'];i=0
    # label centers: each 'Blank' word starts a label '(i)'
    for k,w in enumerate(ws):
        if w['t'].lower().startswith('blank'):
            nxt=ws[k+1] if k+1<len(ws) else None
            x1=(nxt['x']+nxt['w']) if nxt else w['x']+w['w']
            cx.append((w['x']+x1)/2)
    if len(cx)!=blanks:return None
    rows=[l for l in R if l['y']>ly+10 and not FOOT.match(l['text'].strip())]
    cols=[[] for _ in cx]
    for l in rows:
        for w in l['words']:
            if not any(c.isalnum() for c in w['t']):continue
            mid=w['x']+w['w']/2
            j=min(range(len(cx)),key=lambda k:abs(cx[k]-mid))
            cols[j].append((l['y'],l['y1'],w['x'],w['h'],w['t']))
    outc=[]
    for c in cols:
        lines={}
        for y,y1,x,h,t in c:lines.setdefault(y,[]).append((x,h,t,y1))
        rowsj=[]
        for y in sorted(lines):
            ws=sorted(lines[y]);rowsj.append([y,max(w[3] for w in ws),' '.join(w[2] for w in ws),statistics.median(w[1] for w in ws)])
        g=[]
        for y,y1,t,h in rowsj:
            if g and y-g[-1][1]<0.5*h:g[-1][1]=y1;g[-1][2]+=' '+t
            else:g.append([y,y1,t])
        outc.append([fixtxt(x[2]) for x in g])
    cols=outc
    stemL=[l for l in R if l['y']<ly-5 and not re.match(r'^\s*Blank\b',l['text'])]
    g=groups(stemL)
    while g and INSTR.match(' '.join(x['text'] for x in g[0]).strip()) and len(g)>1:g=g[1:]
    return paras([l for gg in g for l in gg]),cols
def extract(it,path_dir):
    kind=it['kind'];pages=[os.path.join(path_dir,p) for p in it['pages']]
    res=dict(ok=False)
    P=[parse_page(p) for p in pages]
    H=lambda r:(max([l['y1'] for l in r['left']+r['right']] or [0]))
    first=P[0]
    if kind=='tc':
        r=tc_lines(first['right'],first.get('hl'),it['blanks']) or tc_parse(first['right'],it['blanks']);
        if r and all(len(c)==3 for c in r[1]):
            res.update(ok=True,stem=r[0],cols=r[1])
        else:res['raw']=[l['text'] for l in first['right']]
        if first['two']:res['pass']=passage_paras(first['left'],3000)
        return res
    n={'mc1':5,'se':6,'mcn':it.get('nopt',3)}.get(kind)
    # passage
    ps=None
    for r in P:
        if r['two']:
            pp=passage_paras(r['left'],max(l['y1'] for l in r['left']) if r['left'] else 0)
            ps=pp if ps is None else (merge_pass(ps,pp) or ps)
    if kind=='ss':
        res.update(ok=True,stem=paras(first['right']))
        if ps:res['pass']=ps
        return res
    so=stem_opts(first['right'],n)
    if not so and len(P)>1:so=stem_opts(P[1]['right'],n)
    if so:res.update(ok=True,stem=so[0],opts=so[1])
    else:res['raw']=[l['text'] for l in first['right']]
    if ps:res['pass']=ps
    return res
