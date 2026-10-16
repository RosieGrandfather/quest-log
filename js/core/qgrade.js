/* Quant 练习题的判分（纯函数，可测试）。
   题型 kind：qc 数量比较（A–D 单选）/ mc1 单选 / mcn 多选（全选对才算对）/ ne 数值输入（含分数）。
   Verbal 回忆真题另有：se 选两个（同 mcn，必须刚好选对两个）/ tc 多空填空（每个空各选一项，按空的顺序全对才算对，
   作答存成 "2,0,1"）/ ss 句子选择（只能对照答案自评：不计入总分，单独列出）。
   作答统一存成字符串：选择题 "1,3"（选项下标），数值题 "12" 或分数 "5/2"。没有部分分。 */
export const QKIND_LABEL = {qc:'数量比较', mc1:'单选题', mcn:'多选题', ne:'数值输入', se:'选两个', tc:'多空填空', ss:'选句子（自评）'};
export const isMulti = it => it.kind === 'mcn' || it.kind === 'se';
export const isGraded = it => it.kind !== 'ss';
export const QC_TEXT = ['Quantity A 更大', 'Quantity B 更大', '两者相等', '无法确定'];

/* 句子边界由校对过的课程数据提供，避免缩写、引号被自动断句拆错。 */
export function sentenceChoices(item){
  const sentences = item.kind === 'ss' && item.txt && item.txt.sentences;
  return Array.isArray(sentences) && sentences.length > 0 && sentences.every(s=> typeof s === 'string' && s.trim()) ? sentences : [];
}

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

const blanks = (item, a)=> { const p = String(a || '').split(','); return Array.from({length: item.blanks}, (_, i)=> p[i] ?? ''); };
export const isAnswered = (item, a)=> item.kind === 'ne'
  ? (item.frac ? /^\s*\S+\s*\/\s*\S+\s*$/.test(a || '') : String(a || '').trim() !== '')
  : item.kind === 'ss' ? (sentenceChoices(item).length ? sentenceChoices(item).includes(String(a || '')) : String(a || '').trim() !== '')
  : item.kind === 'tc' ? blanks(item, a).every(x=> x !== '')
  : idx(a).length > 0;

export function gradeItem(item, a){
  if(!isAnswered(item, a) || item.kind === 'ss') return false;
  if(item.kind === 'tc') return blanks(item, a).every((x, i)=> Number(x) === item.ans[i]);
  if(item.kind === 'ne'){
    const x = parseNum(a), y = parseNum(String(item.ans));
    return Number.isFinite(x) && Number.isFinite(y) && Math.abs(x - y) < 1e-9;
  }
  const got = idx(a), want = [...item.ans].sort((p, q)=> p - q);
  return got.length === want.length && got.every((v, i)=> v === want[i]);
}

export function summarize(items, answers){
  const byKind = {}, wrong = [], selfCheck = [];
  let correct = 0, blank = 0, total = 0;
  items.forEach((it, i)=>{
    const a = answers[i] || '';
    if(!isGraded(it)){ selfCheck.push(i); return; }
    total++;
    const ok = gradeItem(it, a);
    const k = byKind[it.kind] || (byKind[it.kind] = {total:0, correct:0});
    k.total++;
    if(ok){ correct++; k.correct++; } else wrong.push(i);
    if(!isAnswered(it, a)) blank++;
  });
  return {total, correct, blank, wrong, selfCheck, byKind, pct: total ? Math.round(correct / total * 100) : 0};
}

const BL = ['(i)', '(ii)', '(iii)'];
export const answerText = item => item.kind === 'ne' ? String(item.ans)
  : item.kind === 'ss' ? String(item.ansText || '')
  : item.kind === 'tc' ? item.ans.map((k, i)=> `空${BL[i]} ${'ABCDEFGH'[k]}`).join('　')
  : item.ans.map(k=> 'ABCDEFGH'[k]).join('、');
export const pickedText = (item, a)=> !isAnswered(item, a) ? '未作答'
  : item.kind === 'ne' || item.kind === 'ss' ? String(a).trim()
  : item.kind === 'tc' ? blanks(item, a).map((k, i)=> `空${BL[i]} ${'ABCDEFGH'[Number(k)]}`).join('　')
  : idx(a).map(k=> 'ABCDEFGH'[k]).join('、');
