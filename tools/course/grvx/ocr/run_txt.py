import sys,json,os,time,signal;
def _h(*a):raise TimeoutError('slow')
signal.signal(signal.SIGALRM,_h);sys.path.insert(0,os.path.expanduser('~/scratch/gv'))
import parse
D=os.path.expanduser('~/scratch/gv/pages')
d=json.load(open(os.path.expanduser('~/scratch/gv/data.json')))
ONLY=json.load(open(os.environ['ONLY'])) if os.environ.get('ONLY') else None
t0=time.time();lim=float(sys.argv[1]);ids=sys.argv[2:]
for s in d:
    if ids and s['id'] not in ids:continue
    f=f'{D}/{s["id"]}/'+os.environ.get('TXTNAME','txt.json')
    res=json.load(open(f)) if os.path.exists(f) else {}
    for sec in s['sections']:
        for it in sec['items']:
            k=f'{sec["sec"]}-{it["n"]}'
            if k in res:continue
            if ONLY is not None and k not in ONLY.get(s['id'],[]):continue
            if time.time()-t0>lim:json.dump(res,open(f,'w'));print('timeout',s['id'],len(res));sys.exit()
            signal.alarm(40)
            try:res[k]=parse.extract(it,f'{D}/{s["id"]}')
            except Exception as e:res[k]=dict(ok=False,err=str(e));print('ERR',s['id'],k,e,flush=True)
            signal.alarm(0);json.dump(res,open(f,'w'))
    json.dump(res,open(f,'w'));print('done',s['id'],len(res),sum(1 for v in res.values() if v.get('ok')),flush=True)
