import pickle,re,json,sys
data=pickle.load(open('../qdata.pkl','rb'))
keys=json.load(open('keys.json'))
SETS=[('ar','算术 Arithmetic',59,66,77),('al','代数 Algebra',79,86,97),('ge','几何 Geometry',98,105,115),('da','数据分析 Data Analysis',116,128,146),
      ('m1','混合 Practice Set 1',147,158,175),('m2','混合 Practice Set 2',176,185,201),('m3','混合 Practice Set 3',202,211,230)]
HEAD=re.compile(r'^(Multiple-choice Questions|Numeric Entry Questions|Data Interpretation|Quantitative Comparison Questions|For Questions? \d+|For these questions|Questions \d+ (and|to) \d+ are based|PRACTICE SET|ANSWER KEY|Answers and Explanations)')
def elems(pa,pb):
    out=[]
    for p in range(pa,pb+1):
        d=data[p]
        for l in d['lines']: out.append(dict(p=p,top=l['top'],bottom=l['bottom'],x0=l['x0'],x1=l['x1'],k='T',text=l['text']))
        for (x0,t,x1,b) in d['images']: out.append(dict(p=p,top=t,bottom=b,x0=x0,x1=x1,k='I',text=''))
        for (x0,t,x1,b) in d['rects']: out.append(dict(p=p,top=t,bottom=b,x0=x0,x1=x1,k='R',text=''))
    out.sort(key=lambda e:(e['p'],e['top'],e['x0']))
    return out
def ismarker(e,n=None):
    if e['k']!='T' or e['x0']>=30: return False
    m=re.match(r'(\d+)\.(\s|$)',e['text'])
    return bool(m) and (n is None or int(m.group(1))==n)
def seg_exam(sid,pa,pb):
    E=[e for e in elems(pa,pb)]
    # cut at ANSWER KEY
    kidx=next(i for i,e in enumerate(E) if e['k']=='T' and e['text'].strip().startswith('ANSWER KEY'))
    E=E[:kidx]
    N=len(keys[sid]); 
    # markers sequential
    mk={}; pos=0
    for n in range(1,N+1):
        i=next((i for i in range(pos,len(E)) if ismarker(E[i],n)),None)
        if i is None: mk[n]=None; continue
        mk[n]=i; pos=i+1
    return E,mk,N
if __name__=='__main__':
    for sid,name,pa,pb,pe in SETS:
        E,mk,N=seg_exam(sid,pa,pb)
        print(sid,N,[n for n,i in mk.items() if i is None] or 'all markers found')
