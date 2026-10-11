import json,re
pages=json.load(open('../quant_pages.json'))
SETS=[('ar',59,66),('al',79,86),('ge',98,105),('da',116,128),('m1',147,158),('m2',176,185),('m3',202,211)]
def keyof(a,b):
    txt='\n'.join(pages[str(p)] for p in range(a,b+1))
    i=txt.find('ANSWER KEY'); j=txt.find('Answers and Explanations',i)
    seg=txt[i+len('ANSWER KEY'):j]
    entries={};cur=None
    for ln in seg.splitlines():
        m=re.match(r'\s*(\d+)\.\s+(.*)$',ln)
        if m and (cur is None or int(m.group(1))==cur+1):
            cur=int(m.group(1)); entries[cur]=m.group(2).strip()
        elif ln.strip() and cur: entries[cur]+=' '+ln.strip()
    return entries
if __name__=='__main__':
    out={}
    for sid,a,b in SETS:
        k=keyof(a,b); out[sid]=k
        print('##',sid,len(k))
        for n,t in k.items(): print(n,t)
    json.dump(out,open('keys.json','w'),ensure_ascii=False,indent=1)
