/* 把课程 JSON 里的内容块渲染成 HTML。
   Markdown 用 marked，公式用 KaTeX（都由 study.html 从 CDN 引入，全局变量 marked / renderMathInElement）。
   课程内容来自我们自己仓库里的 JSON，属于可信内容。 */
/* global marked, renderMathInElement */
import { escapeHTML } from '../core/html.js';

/* marked 会把公式里的 _ 和 * 当成斜体，所以先把 $...$ / $$...$$ 换成占位符，排版完再换回来 */
export function mdToHTML(md){
  const math = [];
  const protectedMd = md.replace(/\$\$[\s\S]+?\$\$|\$[^$\n]+?\$/g, m=>{ math.push(m); return `@@MATH${math.length-1}@@`; });
  const html = marked.parse(protectedMd);
  return html.replace(/@@MATH(\d+)@@/g, (_, i)=> escapeHTML(math[Number(i)]));
}

export function renderMath(el){
  if(typeof renderMathInElement !== 'function') return;
  renderMathInElement(el, {
    delimiters:[{left:'$$', right:'$$', display:true}, {left:'$', right:'$', display:false}],
    throwOnError:false,
  });
}

const fmtTime = s => `${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;

function videoHTML(b){
  let embed, open, site;
  if(b.provider === 'bilibili'){
    embed = `https://player.bilibili.com/player.html?bvid=${encodeURIComponent(b.id)}&page=1&autoplay=0&high_quality=1${b.start?`&t=${b.start}`:''}`;
    open = `https://www.bilibili.com/video/${encodeURIComponent(b.id)}/${b.start?`?t=${b.start}`:''}`;
    site = 'B站';
  } else {
    const q = new URLSearchParams({rel:'0'});
    if(b.start) q.set('start', b.start);
    if(b.end) q.set('end', b.end);
    embed = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(b.id)}?${q}`;
    open = `https://www.youtube.com/watch?v=${encodeURIComponent(b.id)}${b.start?`&t=${b.start}s`:''}`;
    site = 'YouTube';
  }
  const range = b.start || b.end ? ` · 建议看 ${fmtTime(b.start||0)}${b.end?`–${fmtTime(b.end)}`:' 起'}` : '';
  const meta = [b.lang, b.minutes ? `约 ${b.minutes} 分钟` : ''].filter(Boolean).join(' · ') + range;
  return `<figure class="blk-video">
    <div class="video-frame"><iframe src="${embed}" title="${escapeHTML(b.title||'视频')}" loading="lazy"
      allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen" allowfullscreen
      referrerpolicy="strict-origin-when-cross-origin"></iframe></div>
    <figcaption>
      <div class="video-title">🎬 ${escapeHTML(b.title||'')}</div>
      <div class="video-meta">${escapeHTML(meta)}</div>
      <a class="video-open" href="${open}" target="_blank" rel="noopener">在 ${site} 打开 ↗</a>
    </figcaption>
  </figure>`;
}

function blockHTML(b){
  switch(b.type){
    case 'text': return `<div class="blk-text">${mdToHTML(b.md)}</div>`;
    case 'video': return videoHTML(b);
    case 'image': return `<figure class="blk-image"><img src="${escapeHTML(b.src)}" alt="${escapeHTML(b.alt||'')}" loading="lazy">${b.caption?`<figcaption>${mdToHTML(b.caption)}</figcaption>`:''}</figure>`;
    case 'think': return `<details class="blk-think"><summary><span class="think-tag">想一想</span>${mdToHTML(b.q)}</summary><div class="think-answer">${mdToHTML(b.a)}</div></details>`;
    case 'keywords': return `<div class="blk-keywords"><div class="kw-title">本节关键词</div><table>${b.items.map(([zh,en,desc])=>
      `<tr><td class="kw-zh">${escapeHTML(zh)}</td><td class="kw-en">${escapeHTML(en)}</td><td class="kw-desc">${mdToHTML(desc||'')}</td></tr>`).join('')}</table></div>`;
    default: return '';
  }
}

export function unitBodyHTML(unit){
  const obj = unit.objectives && unit.objectives.length
    ? `<div class="blk-objectives"><div class="kw-title">学完这节你能</div><ul>${unit.objectives.map(o=>`<li>${mdToHTML(o).replace(/^<p>|<\/p>\s*$/g,'')}</li>`).join('')}</ul></div>` : '';
  const refs = unit.references && unit.references.length
    ? `<div class="blk-refs"><div class="kw-title">参考资料</div><ul>${unit.references.map(r=>`<li><a href="${escapeHTML(r.url)}" target="_blank" rel="noopener">${escapeHTML(r.title)}</a>${r.note?` <span class="ref-note">${escapeHTML(r.note)}</span>`:''}</li>`).join('')}</ul></div>` : '';
  return obj + unit.blocks.map(blockHTML).join('') + refs;
}
