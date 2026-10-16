"""Produce review candidates from Windows OCR coordinates; never edits published courses.

Usage: python review_windows.py <ocr.json> <candidate.json>
Requires Pillow and NumPy. Coordinates refer to images resized to 2000 px wide.
"""
import json
import re
import sys
import statistics
import difflib
from pathlib import Path
from PIL import Image
import numpy as np
import parse as old

ROOT = Path(__file__).resolve().parents[4]
IMAGE_ROOT = ROOT / 'courses/gre-vx/img'
LEGACY=False

def fix(s):
    s = re.sub(r"([A-Za-z])['’]\s+(s|t|re|ve|ll|d|m)\b", r'\1’\2', s)
    s = re.sub(r'\s+([,.;:!?])', r'\1', s)
    return re.sub(r'\s+', ' ', s).strip()

def words_of(raw):
    return [dict(x=w['x'], y=w['y'], w=w['w'], h=w['h'], t=w['text'], conf=99, blk=0, par=0, ln=i)
            for i,l in enumerate(raw) for w in l['words']]

def lines(words):
    # Retain the engine's line membership on tilted photos, then join fragments
    # of the same physical row (for example text on both sides of a blank).
    if LEGACY:
        rows=[]
        for w in sorted(words,key=lambda w:(w['y']+w['h']/2,w['x'])):
            cy=w['y']+w['h']/2
            near=next((g for g in reversed(rows[-3:]) if abs(cy-statistics.median(a['y']+a['h']/2 for a in g))<.55*max(w['h'],statistics.median(a['h'] for a in g))),None)
            if near is None:rows.append([w])
            else:near.append(w)
        out=[]
        for i,g in enumerate(rows):
            for w in g:w['ln']=i
            out.extend(old.lines_of(g))
        return sorted(out,key=lambda l:l['y'])
    buckets={}
    for w in words:buckets.setdefault(w['ln'],[]).append(w)
    center=lambda g:statistics.median(a['y']+a['h']/2 for a in g)
    rows=[]
    for group in sorted(buckets.values(),key=center):
        near=next((g for g in reversed(rows[-3:]) if abs(center(group)-center(g))<.4*statistics.median(a['h'] for a in group+g)),None)
        if near is None:rows.append(group)
        else:near.extend(group)
    out=[]
    for i,g in enumerate(rows):
        for w in g: w['ln']=i
        out.extend(old.lines_of(g))
    return sorted(out,key=lambda l:l['y'])

def geometry(path):
    im=Image.open(path).convert('L'); a=np.asarray(im); h,w=a.shape
    dark=a<170
    # Find a long divider by local contrast, allowing tilted photographs. Absolute
    # darkness mistakes a dim photograph's whole background for a divider.
    yy=np.arange(int(h*.06),int(h*.89),4)
    xx=np.arange(int(w*.39),int(w*.62))
    best=(0,w//2)
    for slope in np.arange(-.12,.121,.01):
        xgrid=np.clip(np.rint(xx[None,:]+slope*(yy[:,None]-h/2)).astype(int),10,w-11)
        mid=np.minimum.reduce([a[yy[:,None],xgrid+j] for j in (-1,0,1)]).astype(float)
        sides=(a[yy[:,None],xgrid-8].astype(float)+a[yy[:,None],xgrid+8].astype(float))/2
        score=((mid<sides-20)&(mid<190)).mean(axis=0)
        j=int(np.argmax(score))
        if score[j]>best[0]:best=(float(score[j]),int(xx[j]))
    two,dx=best[0]>.42,best[1]
    # Repeated long horizontal edges identify option-table cells and fill blanks.
    edges=[]
    for y in range(int(h*.08),int(h*.92)):
        row=dark[y]; z=np.flatnonzero(np.diff(np.r_[False,row,False].astype(np.int8)))
        for x0,x1 in zip(z[::2],z[1::2]):
            if x1-x0>80 and x1-x0<w*.75: edges.append((y*2,x0*2000/w,x1*2000/w))
    unique=[]
    for y,x0,x1 in edges:
        if any(abs(y-yy)<7 and abs(x0-a)<10 and abs(x1-b)<10 for yy,a,b in unique[-20:]): continue
        unique.append((y,x0,x1))
    return two,dx*2000/w,unique,h*2,2000

def page(image, raw, force_single=False):
    two,dx,edges,h,w=geometry(IMAGE_ROOT/image)
    if force_single:two=False
    words=words_of(raw)
    slopes=[]
    for line in raw:
        ws=line['words']
        if len(ws)>=5 and max(v['x']+v['w'] for v in ws)-min(v['x'] for v in ws)>450:
            slope=float(np.polyfit([v['x']+v['w']/2 for v in ws],[v['y']+v['h']/2 for v in ws],1)[0])
            if abs(slope)<.1:slopes.append(slope)
    skew=statistics.median(slopes) if slopes else 0
    if abs(skew)>.004:
        for v in words:v['y']-=skew*(v['x']+v['w']/2-w/2)
        edges=[(y-skew*((x0+x1)/2-w/2),x0,x1) for y,x0,x1 in edges]
    lines(words)  # Assign row IDs before inserting blanks at their actual baseline.
    def keep(a):
        return [l for l in lines(a) if sum(c.isalpha() for c in l['text'])>=2 and not re.match(r'^[^A-Za-z]*[Qq]uestions?\s+\d',l['text'])]
    left=keep([a for a in words if a['x']+a['w']/2<dx-5]) if two else []
    right=keep([a for a in words if a['x']+a['w']/2>dx+5]) if two else keep(old.add_blanks(words,edges))
    # Remove footer buttons but not question stems that start with "Select the sentence".
    right=[l for l in right if not (l['y']>h*.8 and re.match(r'^[^A-Za-z]*Select\b',l['text'],re.I))]
    if not two:right=[l for l in right if l['y']>h*.14]
    return dict(two=two,left=left,right=right,edges=edges,h=h,w=w)

def text(ls):
    return fix(' '.join(l['text'] for l in ls))

def merge_passages(a,b):
    if not a:return b
    aa=' '.join(a).split();bb=' '.join(b).split()
    norm=lambda w:re.sub(r'[^a-z0-9]','',w.lower())
    m=max(difflib.SequenceMatcher(None,list(map(norm,aa)),list(map(norm,bb)),autojunk=False).get_matching_blocks(),key=lambda x:x.size)
    if m.size<12:return a
    i,j,n=m
    left=aa[:i] if i>=j else bb[:j]
    right=aa[i+n:] if len(aa)-i-n>=len(bb)-j-n else bb[j+n:]
    return [' '.join(left+aa[i:i+n]+right)]

def strip_instructions(ls):
    ls=list(ls)
    while ls and (old.INSTR.match(ls[0]['text']) and not re.match(r'^Select (?:the |a )?sentence',ls[0]['text'],re.I)):
        # Instruction spans several close lines.
        first=old.groups(ls)[0]
        ls=ls[len(first):]
    return ls

def table_parse(p):
    groups=[]
    for y,x0,x1 in p['edges']:
        if x1-x0>p['w']*.6: continue
        g=next((c for c in groups if abs(c['x0']-x0)<20 and abs(c['x1']-x1)<20),None)
        if g is None: groups.append(dict(x0=x0,x1=x1,ys=[y]))
        else:g['ys'].append(y)
    cols=[g for g in groups if len(g['ys'])>=4 and max(g['ys'])-min(g['ys'])>80]
    cols=sorted(cols,key=lambda c:c['x0'])
    if len(cols) not in (1,2,3):return None
    out=[]
    for c in cols:
        ys=sorted(c['ys'])
        # A four-line table has exactly three option rows. Dense compression may duplicate borders.
        z=[ys[0]]
        for y in ys[1:]:
            if y-z[-1]>12:z.append(y)
        if len(z)!=4:return None
        opts=[]
        for y0,y1 in zip(z,z[1:]):
            ws=[w for l in p['right'] for w in l['words'] if c['x0']-8<w['x']+w['w']/2<c['x1']+8 and y0<=w['y']+w['h']/2<y1]
            opts.append(text(lines(ws)))
        if any(not x for x in opts):return None
        out.append(opts)
    top=min(min(c['ys']) for c in cols)
    stem=strip_instructions([l for l in p['right'] if l['y1']<top-4 and not re.search(r'\bBlank\b',l['text'],re.I)])
    return {'stem':[text(stem)],'cols':out} if len(cols)>1 else None

def labelled_table(p, blanks):
    ws=[w for l in p['right'] for w in l['words']]
    labs=[w for w in ws if re.match(r'^Blank\b',w['t'],re.I) and w['y']>p['h']*.2]
    if len(labs)!=blanks:return None
    labs.sort(key=lambda w:w['x'])
    cx=[w['x']+w['w']*.8 for w in labs]
    top=min(w['y'] for w in labs)
    columns=[[] for _ in cx]
    for w in ws:
        if w['y']<top+35 or w['y']>p['h']*.85:continue
        j=min(range(blanks),key=lambda j:abs(w['x']+w['w']/2-cx[j]))
        columns[j].append(w)
    cols=[]
    for col in columns:
        gs=old.groups(lines(col),k=.15)
        if len(gs)!=3:return None
        cols.append([text(g) for g in gs])
    stem=strip_instructions([l for l in p['right'] if l['y1']<top-3])
    return {'stem':[text(stem)],'cols':cols}

def extract(item,pages):
    p=pages[0]; r=strip_instructions(p['right']); content=text(r)
    kind=item['kind']; flags=[]
    if re.match(r'^Select the sentence\b',content,re.I):kind='ss'
    elif table_parse(p):kind='tc'
    elif any(re.search(r'select (?:the )?two',l['text'],re.I) for l in p['right'][:3]):kind='se'
    elif any(re.search(r'Consider each of the choices',l['text'],re.I) for l in p['right'][:3]):kind='mcn'
    tx={}
    if kind=='ss':tx={'stem':[content]}
    elif kind=='tc':
        labelled=labelled_table(p,item.get('blanks',2))
        table=table_parse(p)
        tx=labelled or (table if table and len(table['cols'])==item.get('blanks') else None) or {}
        if not tx: flags.append('table_unresolved')
    else:
        n=6 if kind=='se' else 3 if kind=='mcn' else 5
        # Widely spaced groups delineate choices; glyph detection is a fallback.
        if not p['two']:
            # Short vocabulary choices have one row each, even when table borders
            # or font metrics make adjacent rows look like a paragraph.
            so=([text(r[:-n])],[old.strip_glyph(l) for l in r[-n:]]) if len(r)>n else None
        else:so=old.stem_opts(r,n)
        if so:tx={'stem':[fix(' '.join(so[0]))],'opts':[fix(re.sub(r'^(?:Ü|[\[(]3|[\[(]?[CO0DE][\])]?|CJ|Cl|17)\s+','',x)) for x in so[1]]}
        else:flags.append('options_unresolved')
    passages=[]
    for pg in pages:
        if pg['two']:
            ls=[l for l in pg['left'] if l['y']>35 and not re.match(r'^(?:Questions? |Select )',l['text'],re.I)]
            passage=[text(ls)]
            if not passages:passages=passage
            else:passages=merge_passages(passages,passage)
    if passages:tx['pass']=passages
    if kind!=item['kind']:flags.append('kind_changed')
    if not tx.get('stem') or not tx['stem'][0]:flags.append('empty_stem')
    if any('\ufffd' in s for key in ('stem','opts','pass') for s in tx.get(key,[])):flags.append('unrecognized_char')
    return dict(kind=kind,txt=tx,flags=flags)

def main():
    global LEGACY
    raw=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    out=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8')) if '--retry' in sys.argv or '--merge' in sys.argv else {}
    for f in sorted((ROOT/'courses/gre-vx').glob('u*.json')):
        u=json.loads(f.read_text(encoding='utf-8'))
        for it in u['blocks'][0]['items']:
            k=u['id']+'/'+str(it['n'])
            if '--retry' in sys.argv and k in out and 'table_unresolved' not in out[k]['flags']:continue
            if '--merge' in sys.argv and not it.get('imgs'):continue
            pp=[]
            for image in it.get('imgs',[it['img']]):
                sid,nm=image.split('/'); key=sid+'__'+Path(nm).stem
                pp.append(page(image,raw[key],force_single=it['kind'] in ('se','tc')))
            out[k]=extract(it,pp)
            if 'table_unresolved' in out[k]['flags']:
                LEGACY=True
                pages=[]
                for image in it.get('imgs',[it['img']]):
                    sid,nm=image.split('/'); key=sid+'__'+Path(nm).stem
                    pages.append(page(image,raw[key],force_single=True))
                alternate=extract(it,pages)
                if 'table_unresolved' not in alternate['flags']:out[k]=alternate
                LEGACY=False
    Path(sys.argv[2]).write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding='utf-8')
    print('Candidates',len(out))
    from collections import Counter
    print('Flags',Counter(f for v in out.values() for f in v['flags']))

if __name__=='__main__':main()
