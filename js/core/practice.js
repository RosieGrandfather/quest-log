/* 练习套题的判分逻辑（纯函数，可测试）。
   一道题 = {kind, groups:[{options, pick, correct:[下标…]}]}；
   作答 sel = 每组选了哪些下标：[[2], [0]]。整题对错只有「全对 / 不全对」，没有部分分（和 GRE 一样）。 */
export const KIND_LABEL = {rc:'阅读理解', tc:'文本补全', se:'句子等价'};
export const DIFF_LABEL = {easy:'低', medium:'中', hard:'高', mixed:'官方未标难度'};

const sortedNums = a => [...a].sort((x, y)=> x - y);
const sameSet = (a, b)=> a.length === b.length && sortedNums(a).every((v, i)=> v === sortedNums(b)[i]);

export const isAnswered = (item, sel)=> item.groups.every((_, j)=> (sel[j] || []).length > 0);
export const gradeItem = (item, sel)=> item.groups.every((g, j)=> sameSet(sel[j] || [], g.correct));

/* Firestore 不能存「数组里套数组」，所以每题存成字符串："1,3|0"（| 隔开各组，逗号隔开同组多选） */
export const encodeSel = sel => sel.map(a=> sortedNums(a).join(',')).join('|');
export function decodeSel(str, item){
  const parts = String(str || '').split('|');
  return item.groups.map((_, j)=> (parts[j] || '').split(',').filter(s=> s !== '').map(Number));
}

export function summarize(items, sels){
  const byKind = {};
  const wrong = [];
  let correct = 0, blank = 0;
  items.forEach((it, i)=>{
    const sel = sels[i] || [];
    const ok = gradeItem(it, sel);
    const k = byKind[it.kind] || (byKind[it.kind] = {total:0, correct:0});
    k.total++;
    if(ok){ correct++; k.correct++; } else wrong.push(i);
    if(!isAnswered(it, sel)) blank++;
  });
  const total = items.length;
  return {total, correct, blank, wrong, byKind, pct: total ? Math.round(correct / total * 100) : 0};
}
