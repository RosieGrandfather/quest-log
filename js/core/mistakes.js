/* 练习课错题本（纯函数，可测试）：从每节「最近一次提交」里找出答错 / 没答的题，整理成可导出的列表和 Markdown。
   两种练习格式都支持：gre-qset（张巍机经、真题回忆、官方 Quant）和 gre-set（官方 Verbal 12 套）。
   不计分的题（选句子自评、答案待核对）不算错题。 */
import { restorePractice } from './qreview.js';
import { gradeItem, isAnswered, isGraded, answerText, pickedText, QKIND_LABEL } from './qgrade.js';
import { decodeSel, gradeItem as gradeSet, isAnswered as answeredSet, KIND_LABEL } from './practice.js';

const L = 'ABCDEFGH', BL = ['(i)', '(ii)', '(iii)'];
const paras = x => Array.isArray(x) ? x : x ? [x] : [];
const choiceList = (opts, zh) => opts.map((s, k)=> ({key:L[k], text:String(s), zh:zh?.[k] || ''}));

/* gre-qset 一节的错题。ctx = {courseId, courseTitle, unitTitle} */
export function qsetMistakes(ctx, unit, last){
  const b = unit?.blocks?.find(x=> x.type === 'gre-qset');
  if(!b || !last) return [];
  const {answers, gradedItems} = restorePractice(unit, last);
  return gradedItems.flatMap((it, i)=>{
    if(!isGraded(it) || gradeItem(it, answers[i])) return [];
    const t = it.txt || {};
    const p = it.passage && b.passages?.[it.passage];
    const passage = p ? {id:`${unit.id}:${it.passage}`, title:`Passage ${p.number}`, text:paras(p.paragraphs).join('\n\n')}
      : t.pass ? {id:`${unit.id}:q${it.n}`, title:'文章', text:paras(t.pass).join('\n\n')} : null;
    const options = t.cols ? t.cols.map((col, j)=> ({label:`空${BL[j]}`, choices:choiceList(col, t.colsZh?.[j])}))
      : t.opts ? [{label:'', choices:choiceList(t.opts, t.optsZh)}] : [];
    return [{...ctx, unitId:unit.id, n:it.n, kind:QKIND_LABEL[it.kind] || it.kind, passage,
      stem:paras(t.stem).join('\n'), options, picked:pickedText(it, answers[i]), correct:answerText(it),
      blank:!isAnswered(it, answers[i]), expl:it.explanation || '', imageOnly:!t.stem}];
  });
}

/* gre-set（官方 Verbal 12 套）一节的错题 */
export function setMistakes(ctx, unit, last){
  const b = unit?.blocks?.find(x=> x.type === 'gre-set');
  if(!b || !last) return [];
  return b.items.flatMap((it, i)=>{
    const sel = decodeSel(last.answers?.[i], it);
    if(gradeSet(it, sel)) return [];
    const multi = it.groups.length > 1;
    const lab = (g, j)=> g.label || `空${BL[j]}`;
    const fmt = arr => it.groups.map((g, j)=>{
      const s = (arr[j] || []).map(k=> L[k]).join('、') || '未作答';
      return multi ? `${lab(g, j)} ${s}` : s;
    }).join('　');
    const p = it.passage && b.passages?.[it.passage];
    const passage = p ? {id:`${unit.id}:${it.passage}`, title:'文章',
      text:typeof p === 'string' ? p : paras(p.paragraphs).join('\n\n')} : null;
    return [{...ctx, unitId:unit.id, n:i + 1, kind:KIND_LABEL[it.kind] || it.kind, passage, stem:it.stem || '',
      options:it.groups.map((g, j)=> ({label:multi ? lab(g, j) : '', choices:choiceList(g.options)})),
      picked:answeredSet(it, sel) ? fmt(sel) : '未作答', correct:fmt(it.groups.map(g=> g.correct)),
      blank:!answeredSet(it, sel), expl:it.expl || '', imageOnly:false}];
  });
}

export function unitMistakes(ctx, unit, last){
  return [...qsetMistakes(ctx, unit, last), ...setMistakes(ctx, unit, last)];
}

/* 按题型统计：[['多空填空', 5], ...]，多的在前 */
export function countByKind(rows){
  const m = new Map();
  rows.forEach(r=> m.set(r.kind, (m.get(r.kind) || 0) + 1));
  return [...m].sort((a, b)=> b[1] - a[1]);
}

const optLine = c => `${c.key}. ${c.text}${c.zh ? `（${c.zh}）` : ''}`;

export function toMarkdown(rows, {title = 'GRE 错题本', date = ''} = {}){
  const out = [`# ${title}`, ''];
  const nUnits = new Set(rows.map(r=> `${r.courseId}/${r.unitId}`)).size;
  out.push(`${date ? `导出时间：${date}；` : ''}共 ${rows.length} 道错题，来自 ${nUnits} 节（按每节最近一次提交统计）。`, '');
  if(rows.length) out.push(`按题型：${countByKind(rows).map(([k, n])=> `${k} ${n}`).join('，')}`, '');
  let unitHead = '', passages = new Set();
  rows.forEach(r=>{
    const head = `${r.courseTitle} · ${r.unitTitle}`;
    if(head !== unitHead){ unitHead = head; out.push(`## ${head}`, ''); }
    if(r.passage && !passages.has(r.passage.id)){
      passages.add(r.passage.id);
      out.push(`#### ${r.passage.title}`, '', ...r.passage.text.split('\n\n').flatMap(p=> [`> ${p}`, '>']).slice(0, -1), '');
    }
    out.push(`### 第 ${r.n} 题 · ${r.kind}`, '');
    if(r.imageOnly) out.push('（这题只有原图，请回课程里看题目）', '');
    else if(r.stem) out.push(r.stem, '');
    r.options.forEach(g=>{
      if(g.label) out.push(`${g.label}：${g.choices.map(optLine).join('｜')}`);
      else g.choices.forEach(c=> out.push(`- ${optLine(c)}`));
    });
    if(r.options.length) out.push('');
    out.push(`**你的答案**：${r.picked}　**正确答案**：${r.correct}`, '');
    if(r.expl) out.push(`解析：${r.expl.replace(/\n+/g, ' ')}`, '');
  });
  return out.join('\n');
}
