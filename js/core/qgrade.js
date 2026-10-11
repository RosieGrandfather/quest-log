/* Quant 练习题的判分（纯函数，可测试）。
   题型 kind：qc 数量比较（A–D 单选）/ mc1 单选 / mcn 多选（全选对才算对）/ ne 数值输入（含分数）。
   作答统一存成字符串：选择题 "1,3"（选项下标），数值题 "12" 或分数 "5/2"。没有部分分。 */
export const QKIND_LABEL = {qc:'数量比较', mc1:'单选题', mcn:'多选题', ne:'数值输入'};
export const QC_TEXT = ['Quantity A 更大', 'Quantity B 更大', '两者相等', '无法确定'];

const num = s => {
  const t = String(s ?? '').trim().replace(/[,\s%$]/g, '');
  if(!/^[-+]?(\d+\.?\d*|\.\d+)$/.test(t)) return NaN;
  return Number(t);
};
/* 数值答案 → 数；分数 "a/b" → a/b；其余 NaN */
export function parseNum(s){
  const t = String(s ?? '').trim();
  if(t.includes('/')){
    const [a, b] = t.split('/');
    const x = num(a), y = num(b);
    return Number.isFinite(x) && Number.isFinite(y) && y !== 0 ? x / y : NaN;
  }
  return num(t);
}
const idx = s => String(s || '').split(',').filter(x=> x !== '').map(Number).sort((a, b)=> a - b);

export const isAnswered = (item, a)=> item.kind === 'ne'
  ? (item.frac ? /^\s*\S+\s*\/\s*\S+\s*$/.test(a || '') : String(a || '').trim() !== '')
  : idx(a).length > 0;

export function gradeItem(item, a){
  if(!isAnswered(item, a)) return false;
  if(item.kind === 'ne'){
    const x = parseNum(a), y = parseNum(String(item.ans));
    return Number.isFinite(x) && Number.isFinite(y) && Math.abs(x - y) < 1e-9;
  }
  const got = idx(a), want = [...item.ans].sort((p, q)=> p - q);
  return got.length === want.length && got.every((v, i)=> v === want[i]);
}

export function summarize(items, answers){
  const byKind = {}, wrong = [];
  let correct = 0, blank = 0;
  items.forEach((it, i)=>{
    const a = answers[i] || '';
    const ok = gradeItem(it, a);
    const k = byKind[it.kind] || (byKind[it.kind] = {total:0, correct:0});
    k.total++;
    if(ok){ correct++; k.correct++; } else wrong.push(i);
    if(!isAnswered(it, a)) blank++;
  });
  const total = items.length;
  return {total, correct, blank, wrong, byKind, pct: total ? Math.round(correct / total * 100) : 0};
}

export const answerText = item => item.kind === 'ne' ? String(item.ans)
  : item.ans.map(k=> 'ABCDEFGH'[k]).join('、');
export const pickedText = (item, a)=> !isAnswered(item, a) ? '未作答'
  : item.kind === 'ne' ? String(a).trim() : idx(a).map(k=> 'ABCDEFGH'[k]).join('、');
