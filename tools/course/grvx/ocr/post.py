"""OCR 结果后处理：①去掉题干里残留的操作说明句；②同一 section 里共用一篇文章的各题，把不同滚动位置的片段合并成完整原文。
用法：python post.py <txt.json 所在目录(含 txt-<套>.json 原始结果)> <输出目录>"""
import json,os,re,sys,difflib
RAW,OUT=sys.argv[1],sys.argv[2]
from spellchecker import SpellChecker
SP=SpellChecker()
def known(w):return w.lower() in SP
def fixw(m):
    w=m.group(0)
    if len(w)<4 or known(w) or (w[0].isupper() and w[1:].islower() and not w.startswith(('A','I'))):return w
    if w.isupper():return w
    for i in range(1,len(w)-2):
        a,b=w[:i],w[i:]
        if (a.lower() in ('a','i') or (len(a)>=2 and known(a))) and known(b) and len(b)>=3:return a+' '+b
    return w
def rep(t):return re.sub(r"[A-Za-z]+",fixw,t)
def blankfix(t):
    # 重复空 / 空旁边的乱码短词
    tk=t.split();out=[]
    for i,x in enumerate(tk):
        nb=(i+1<len(tk) and tk[i+1]=='____') or (out and out[-1]=='____')
        if nb and len(x)<=3 and x!='____' and (any(not c.isalnum() for c in x.strip('.,;:?!')) and any(c.isalnum() for c in x) or (len(x)<=2 and any(c.isalpha() for c in x) and x.lower() not in SP and x.lower() not in('a','i'))) and not re.fullmatch(r'\(?i{1,3}\)?[.,;:]?',x):
            continue
        out.append(x)
    t=' '.join(out)
    t=re.sub(r'____\s*_+','____ ',t)
    t=re.sub(r'\((i{1,3})\)([.,;:])\s+____',r'(\1) ____\2',t)
    return re.sub(r'\s+',' ',re.sub(r'(____\s*)+','____ ',t)).strip()
SHORT=set('a i of to in on as at by it or be is an no so up us we he me my if do go am ad'.split())
def junkpara(t):
    tk=[re.sub(r"[^A-Za-z']","",x).lower().replace('’',"'") for x in t.split()]
    tk=[w for w in tk if w]
    if not tk:return True
    return sum(1 for w in tk if w in SP or w in('a','i'))/len(tk)<(0.99 if len(t)<30 else 0.6)
def trim_lead(t):
    tk=t.split()
    def kn(x):
        w=re.sub(r"[^A-Za-z']","",x).lower().replace('’',"'")
        return x=='____' or re.fullmatch(r"[\d.,%$]+",x) is not None or (len(w)>=1 and (w in SP or w in ('a','i')))
    for i in range(0,max(1,len(tk)-3)):
        if all(kn(x) for x in tk[i:i+4]):
            return ' '.join(tk[i:]) if i else t
    return t
def trimjunk(o):
    tk=o.split()
    while len(tk)>1 and len(tk[-1])<=2 and tk[-1].lower() not in SHORT:tk.pop()
    while len(tk)>1 and len(tk[0])<=2 and tk[0].lower() not in SHORT:tk.pop(0)
    return ' '.join(tk)
def relabel(ps):
    # (i)(ii)(iii) 编号被 OCR 读坏时按出现顺序重新编号
    n=[0]
    def f(m):
        n[0]+=1;return ' ('+'i'*min(n[0],3)+') '
    return [re.sub(r'(?<=\s)(?:\(|G|C|\[)?(?:i{1,3}|il|li|Ii|ll|l)(?:\)|\])[.,;:]?(?=\s)',lambda m:f(m)[:-1]+(m.group(0)[-1] if m.group(0)[-1] in '.,;:' else '')+' ',p) for p in ps]
def unk(t):
    ws=[w for w in re.findall(r"[A-Za-z]+",t.replace('’',"'")) if len(w)>=4 and not w[0].isupper() and not w.isupper()]
    return sum(1 for w in ws if not known(w)),len(ws)
def gate(v):
    st=' '.join(v.get('stem') or [])
    if v.get('cols') and st.count('____')<len(v['cols']):return False
    if v.get('opts'):
        wl=[len(o.split()) for o in v['opts']];
        if max(wl)<=4 and '____' not in st:return False
        sw=sorted(wl)
        if sw[-1]>12 and sw[-2]<=4:return False
        if sw[-1]>=4*max(sw[len(sw)//2],1)+4 and sw[-1]>10:return False
    return gate0(v)
def gate0(v):
    for o in (v.get('opts') or [])+[c for col in (v.get('cols') or []) for c in col]:
        if unk(o)[0]:return False
    for key in ('stem','pass'):
        n,m=unk(' '.join(v.get(key) or []))
        if n>=3 and m and n/m>.03:return False
        if n>=1 and key=='stem' and m<8:return False
    return True
INS=[r'select one entry for the blank\.?',r'for each blank,? select one entry from the corresponding column[^.]*\.?',r'fill (the|all) blanks? in the way that best completes the text\.?',
 r'best completes the text\.?',r'select the two answer choices[^.]*\.?',r'that are alike in meaning\.?',r'consider each of the choices separately and select all that apply\.?',
 r'select one answer choice\.?',r'select one or more answer choices\.?',r'questions? \d+ (to|and) \d+ are based on this passage\.?',r'select the sentence[^.?]*\.?']
def strip_instr(ps):
    out=[]
    for i,p in enumerate(ps):
        if i<4:
            for _ in range(4):
                n=p
                for r in INS:p=re.sub(r'^\s*'+r+r'\s*','',p,flags=re.I)
                if p==n:break
        if p.strip():out.append(p)
    return out
def toks(ps):return [w for i,p in enumerate(ps) for w in ((['¶'] if i else [])+p.split())]
def untok(ws):
    ps=[];cur=[]
    for w in ws:
        if w=='¶':ps.append(' '.join(cur));cur=[]
        else:cur.append(w)
    ps.append(' '.join(cur));return [p for p in ps if p.strip()]
def merge(a,b):
    ta,tb=toks(a),toks(b)
    na=[x.lower() for x in ta];nb=[x.lower() for x in tb]
    m=max(difflib.SequenceMatcher(None,na,nb,autojunk=False).get_matching_blocks(),key=lambda x:x.size)
    if m.size<8:return None
    i,j,k=m
    left=ta[:i] if i>=j else tb[:j]
    right=ta[i+k:] if len(ta)-i-k>=len(tb)-j-k else tb[j+k:]
    return untok(left+ta[i:i+k]+right)
for f in sorted(os.listdir(RAW)):
    if not f.startswith('txt-'):continue
    d=json.load(open(os.path.join(RAW,f),encoding='utf-8'))
    groups={}
    for key in sorted(d,key=lambda k:tuple(map(int,k.split('-')))):
        v=d[key]
        if not v.get('ok'):continue
        if v.get('stem'):
            v['stem']=[trim_lead(x) if j==0 else x for j,x in enumerate(v['stem'])]
            v['stem']=[re.sub(r'\s*Blank\s*\(?i{1,3}\)?(\s*(____\s*)?Blank\s*\(?i{1,3}\)?)*(\s*____)?\s*$','',x) for x in v['stem']]
            v['stem']=[re.sub(r'^\s*(____\s*)*Blank\s*\(?i{1,3}\)?(\s*(____\s*)?Blank\s*\(?i{1,3}\)?)*\s*(____\s*)*$','',x) for x in v['stem']]
            v['stem']=[x for x in v['stem'] if x.strip()]
        if v.get('stem') and len(v['stem'])>1:v['stem']=[x for x in v['stem'] if not junkpara(x)] or v['stem']
        if v.get('stem'):v['stem']=[trim_lead(x) if j==0 else x for j,x in enumerate(strip_instr(v['stem']) or v['stem'])]
        if v.get('pass'):v['pass']=[trim_lead(x) if j==0 else x for j,x in enumerate(v['pass'])]
        GL=re.compile(r'^(?:[©Q®]|[\(\[\{][^\s\w]?\w?[\]\)\}]?|[CL]J|[CLO]\))\s+')
        def cg(o):
            for _ in range(2):
                if not re.match(r'^\(i{1,3}\)',o):o=GL.sub('',o)
            return o
        if v.get('stem') and len(v['stem'])>1:
            v['stem']=[p for i,p in enumerate(v['stem']) if i==len(v['stem'])-1 or len(p)>=45 or re.search(r'[.?:!]$',p)] or v['stem']
        cg0=cg
        def cg(o):
            o=cg0(o);return re.sub(r'^[A-Z]{2}\s+(?=[a-z])','',o)
        if v.get('opts'):v['opts']=[cg(o) for o in v['opts']]
        if v.get('cols'):v['cols']=[[cg(o) for o in c] for c in v['cols']]
        _o=(v.get('opts') or [])+[c for col in (v.get('cols') or []) for c in col]
        if any(re.match(r'^[©Q\(\[]',o) and not re.match(r'^\(i+\)',o) for o in _o) or any(re.match(r'^[©Oo0Q\(\[\{]\s?[a-z“"]',p) for p in (v.get('stem') or [])[1:]):
            v['ok']=False;continue
        for fld in ('stem','pass','opts'):
            if v.get(fld):v[fld]=[rep(x) for x in v[fld]]
        if v.get('stem'):
            v['stem']=[blankfix(x) for x in v['stem']]
            if v.get('cols'):v['stem']=relabel(v['stem']);v['stem']=[re.sub(r'\s+',' ',re.sub(r'\s+([.,;:])',r'\1',x)).strip() for x in v['stem']]
        if v.get('cols'):v['cols']=[[trimjunk(rep(x)) for x in c] for c in v['cols']]
        if v.get('opts'):v['opts']=[trimjunk(x) for x in v['opts']]
        if v.get('opts'):v['opts']=[re.sub(r'\s*____\s*',' ',x).strip() for x in v['opts']]
        if v.get('cols'):v['cols']=[[re.sub(r'\s*____\s*',' ',x).strip() for x in c] for c in v['cols']]
        if not gate(v):
            v['ok']=False;continue
        if v.get('pass'):
            sec=key.split('-')[0];G=groups.setdefault(sec,[])
            for g in G:
                m=merge(g['p'],v['pass'])
                if m:g['p']=m;g['keys'].append(key);break
            else:G.append(dict(p=v['pass'],keys=[key]))
    for G in groups.values():
        for g in G:
            for k in g['keys']:d[k]['pass']=g['p']
    json.dump(d,open(os.path.join(OUT,f),'w',encoding='utf-8'),ensure_ascii=False)
print('ok')
