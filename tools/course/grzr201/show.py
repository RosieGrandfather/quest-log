"""Print a bounded passage batch for manual semantic review (keys hidden by default)."""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ps=json.loads((HERE/'passages.json').read_text(encoding='utf8'))
first,last=map(int,sys.argv[1:3])
for p in ps:
    if not first<=p['n']<=last:continue
    print('\nP'+str(p['n']), ' '.join(p['paragraphs']))
    if p['highlights']:print('HIGHLIGHT:',p['highlights'])
    for q in p['items']:
        print(str(q['n'])+'.',q['stem'],' '.join(k+':'+v for k,v in q['options'].items()))
