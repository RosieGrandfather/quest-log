"""Independent arithmetic/enumeration checks; never derives results from the answer key."""
import csv
import json
import math
from fractions import Fraction as F
from itertools import combinations, permutations, product
from pathlib import Path
from statistics import NormalDist, mean, median

HERE = Path(__file__).resolve().parent

def compute():
    prime = lambda n: n >= 2 and all(n % d for d in range(2, math.isqrt(n) + 1))
    out = {}
    def check(n, value, expected):
        assert value == expected, (n, value, expected)
        out[str(n)] = str(value)
    check(4, F(44, 24+44), F(11,17))
    check(5, (42/F(3)+45*F(2,9))/87, F(24,87))
    check(10, ''.join(c for c,n in zip('ABCDE',[1,3,4,6,7]) if not prime(4*n+3)), 'BD')
    check(12, round(100*35/69), 51)
    z=NormalDist().inv_cdf
    check(17, 650+200*(z(.75)-z(.6))/(z(.9)-z(.6)) < 750, True)
    check(28, F(math.comb(18,2), math.comb(20,2)), F(153,190))
    check(31, round(sum(x*f for x,f in zip([F(1,2),F(3,4),F(5,4),F(3,2),F(7,4)],[2,7,8,8,9]))/34,2), F(129,100))
    check(37, sum(len(set(str(n)))==2 for n in range(10,100)), 81)
    check(39, len({s*t for s in [1,4,7,10] for t in [2,3,5,8,13]}), 18)
    check(40, (10**32+2)%11, 3)
    check(43, {pow(824,n,10) for n in range(1,21)}, {4,6})
    check(45, sum({0:4,1:1,2:-3}[n%3] for n in range(150,155)), 7)
    check(49, round(100*(1.1/.95-1),1), 15.8)
    check(61, round(130/-z(.15)/5)*5, 125)
    check(62, [m for m in range(1,331) if all(m%p==0 for p in [10,15,25])], [150,300])
    check(63, ''.join(c for c,(x,y) in zip('ABCDE',[(2,18),(5,12),(10,7),(12,3),(15,2)]) if 4*x+3*y<60), 'BD')
    check(64, {(x,y) for x in range(1,70) for y in range(1,140) if 2*x+y==140 and x*y==2400}, {(30,80),(40,60)})
    check(73, (sum(all(int(d)%2==0 for d in str(n)) for n in range(100,1000)),sum(all(int(d)%2 for d in str(n)) for n in range(100,1000))), (100,125))
    check(76, {(a+b+x+y)/4 for a,b,x,y in product(range(1,14), repeat=4) if a+b==13 and x*y==13}, {6.75})
    check(78, 10**3*26**2+26**3*10**2, 2433600)
    check(79, sum(str(n)==str(n)[::-1] for n in range(1,1001)), 108)
    data=[10,9,1,3,7,7,8,3,4,3]
    check(81, (mean(data),median(data),(median(data)+3)/2), (5.5,5.5,4.25))
    check(86, sum(x for x in range(-100,101) if abs(x+4)**2-10*abs(x+4)==24), -8)
    check(87, [x for x in range(-100,101) if x+1>=0 and 2*x*x-x-9==(x+1)**2], [5])
    check(88, [(x,y) for x,y in product(range(-20,21),repeat=2) if x+abs(x)+y==7 and x+abs(y)-y==6], [(4,-1)])
    check(89, ''.join(c for c,k in zip('ABCDEFGH',[-15,-10,-5,0,5,10,15,20]) if 6*abs(F(4)-F(k,3))>12), 'ABCDEH')
    check(90, ''.join(c for c,(x,y) in zip('ABCDEFG',[(3,7),(-3,7),(-11,-9),(9,-6),(-20,-24),(12,9),(-2,16)]) if x+y!=0 and F(x*x-y*y-1,x+y)>F(-1,x+y)), 'DEF')
    check(92, [(x,(60-x)//3) for x in range(8,22) if (60-x)%3==0], [(9,17),(12,16),(15,15),(18,14),(21,13)])
    check(93, F(1,4)**3, F(1,8)**2)
    check(111, round(400*((76662.25/61293)**(1/20)-1),1), 4.5)
    check(114, F(sum(map(prime,[71,73,79,83,87])),5)*F(sum(map(prime,[57,59,61,67])),4), F(3,5))
    check(116, sum(15//3**k for k in range(1,4)), 6)
    check(118, len({''.join('3' if i in pos else '52115'[sum(j not in pos for j in range(i))] for i in range(7)) for pos in combinations(range(7),2)}), 21)
    check(119, sum(all(abs(p.index(g1)-p.index(g2))<=2 for g1,g2 in combinations('abc',2)) and all(abs(p.index(g1)-p.index(g2))<=2 for g1,g2 in combinations('ABC',2)) for p in permutations('abcABC')), 72)
    check(121, [k for k in range(9) if math.comb(8,k)==56], [3,5])
    check(122, sum(math.perm(6,k) for k in range(4,7)), 1800)
    check(124, 21+math.comb(21,2), 231)
    check(126, sum(math.prod(map(int,str(n)))==210 for n in range(1,10000)), 54)
    check(128, [f for f in range(1,200) if 49*f%100==0 and (200-f)%10==0], [100])
    check(133, ([n for n in range(51,60) if prime(n)],[n for n in range(81,90) if prime(n)]), ([53,59],[83,89]))
    check(136, [(x,y) for x,y in product(range(6,101),repeat=2) if x*y==100], [(10,10)])
    check(138, sum(16000%n==0 for n in range(1,16001)), 32)
    check(139, [(x,y) for x,y in product(range(2),repeat=2) if (x*x*y+x+3*y)%2==0], [(0,0)])
    check(142, [(r,b,g) for r,b,g in product(range(10),repeat=3) if b==g and 2**r*4**b*5**g==16000], [(1,3,3)])
    check(144, sum(sum(n%d==0 for d in range(1,n+1))==3 for n in range(1,901)), 10)
    check(145, [n for n in range(1,100) if n%13==2], [2,15,28,41,54,67,80,93])
    check(149, [n for n in range(1,21) if any(3 in [a]*(n-b)+[a+1]*b and a*n+b==20 for a in range(1,21) for b in range(n))], [6,7,8,9])
    check(156, [n for n in range(-20,21) if 99<n*n<200], [-14,-13,-12,-11,-10,10,11,12,13,14])
    check(157, F(sum(n%2==0 and n%8==0 for n in range(1,1001)),1000), F(1,8))
    check(158, F(6000+250,1)/F(8,100), 78125)
    check(160, sum(math.comb(4,k) for k in range(2,5)), 11)
    check(162, pow(3,283,5), 2)
    check(164, {64//m for m in range(1,65) if 64%m==0 and (64//m)%3==0}, set())
    check(166, min(abs(10*a+b-10*c-d) for a,b,c,d in permutations([2,4,6,9])), 13)
    check(167, F(3*math.comb(5,2),math.comb(15,2)), F(2,7))
    check(168, {p[2] for p in permutations('SMJKP') if p.index('S')<p.index('J')<p.index('M')<p.index('K') and p.index('P')<p.index('K')}, {'J','M','P'})
    check(169, [a for a in range(-100,101) if math.prod(range(a,a+7))==a+3], [-3])
    return out

def main():
    results=compute()
    reviews=list(csv.DictReader((HERE/'reviewed-answers.tsv').read_text(encoding='utf8').splitlines(),delimiter='\t'))
    qs=json.loads((HERE/'questions.json').read_text(encoding='utf8'))
    assert [int(r['question']) for r in reviews]==list(range(1,170))
    for r,q in zip(reviews,qs):
        assert r['candidate']==q['answer'], (r,q['answer'])
        assert len(r['reason'])>=10
    report={'date':'2026-10-16','method':'逐题独立解题后对照配套答案；有限计数、分数、边界与正态分位再用标准库复算。','reviewed':169,'retained':169,'corrected':0,'pending':0,'computerCheckedQuestions':sorted(map(int,results)), 'computedResults':results,'items':[{'question':int(r['question']),'sourceAnswer':q['sourceAnswer'],'independentAnswer':r['candidate'],'status':'retained','reason':r['reason']} for r,q in zip(reviews,qs)]}
    (HERE/'answer-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
    md=['# 张巍数学169题答案独立复核','',
        '2026-10-16：169道数学题逐题独立解题后与配套DOCX对照，169题保留原答案，0题更正，0题待定。原书第170项为词汇提醒。此次没有发现明确错误，不代表ETS官方认证或绝对无误。','',
        '计数、概率、分数、整除及边界等57题另用Python标准库复算，结果见 `tools/course/grzq170/answer-review.json`，运行 `verify_answers.py` 可复现。解析依据以原PDF为准，未依赖OCR对公式的转写。普通题仍只在提交后展示答案；此次没有需要增加争议说明的题。','',
        '同时修复第35题坐标图、第131题数轴等页底内容的截断，以及第121题原有7项却只显示5个作答选项的问题。课程与课节ID、`answerFormat`不变，原有答案和作答记录格式保留。','',
        '下表记录每题独立复核答案和依据；“程序”仅表示另有程序复算，未标记的题仍已人工独立求解。','',
        '|原题号|复核答案|程序|独立解题依据|','|---|---|---|---|']
    for r in reviews:
        md.append(f"|{r['question']}|{r['candidate']}|{'✓' if r['question'] in results else ''}|{r['reason'].replace('|','&#124;')}|")
    (HERE.parents[2]/'docs/GRE_ZQ170_ANSWER_REVIEW.md').write_text('\n'.join(md)+'\n',encoding='utf8')
    print(f'169 independent reviews agree with source; {len(results)} independent computational checks passed.')

if __name__=='__main__':main()
