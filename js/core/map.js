/* 城邦地图的纯逻辑（不碰 Firebase、不碰 DOM，可以直接在 node 里测试）：
   项目 = 一条从首都往外蛇形延伸的路，每一步 = 路上的一座城。
   城的位置只由「项目的 slot + 项目 id + 第几步」算出来，所以每次打开都一样，
   后面再加步骤只会往外长，不会让前面的城挪位置。 */

export const STEP_POINTS = 50;       // 点亮一座城
export const STAGE_BONUS = 100;      // 一个阶段的城全部点亮
export const PROJECT_BONUS = 200;    // 整个项目全部点亮
export const MAX_ACTIVE_PROJECTS = 3;  // 同时进行的项目超过这个数，页面提醒一句

export const PROJECT_COLORS = ['#e4572e', '#29a8e0', '#f2b134', '#6cc04a', '#b57bff', '#ff7fa8', '#22b8a6', '#ff9f43'];

/* ---------- 稳定的随机数 ---------- */
export function hash32(str){
  let h = 2166136261 >>> 0;
  for(let i = 0; i < str.length; i++){ h ^= str.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
  return h >>> 0;
}
export function rng(seed){          // mulberry32
  let a = seed >>> 0;
  return function(){
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/* ---------- 布局 ---------- */
export const HUB_RADIUS = 16;        // 首都的半径
export const SPACING = 12;           // 相邻两座城的路程

/* 每个项目有自己的 slot（创建时分配，之后不变），按黄金角分开，项目再多也不会朝同一个方向 */
export function slotAngle(slot){ return slot * 2.399963229728653; }

/* 第 i 座城（从 0 开始）只依赖 slot / seedStr / i，所以 n 变了前面的城不动 */
const LIM = 0.28;
export function cityPositions(slot, seedStr, n){
  const base = slotAngle(slot);
  const out = [];
  let x = Math.cos(base) * HUB_RADIUS, z = Math.sin(base) * HUB_RADIUS;
  let h = base, lat = 0;
  for(let i = 0; i < n; i++){
    const r = rng(hash32(seedStr + ':' + i));
    /* 随机游走：每一步随机转向，偶尔来一个大拐弯；向「往外」的方向有一点点回拉，保证整体往外扩而不是绕圈 */
    let turn = (r() - 0.5) * 1.1;
    if(r() < 0.22) turn += (r() < 0.5 ? -1 : 1) * (0.7 + r() * 0.5);
    let d = h - base; d = Math.atan2(Math.sin(d), Math.cos(d));
    h += turn - 0.22 * d;
    d = h - base; d = Math.atan2(Math.sin(d), Math.cos(d));
    if(Math.abs(d) > LIM) h = base + Math.sign(d) * LIM;   // 偏离「往外」方向有上限，不会掉头，也不会撞进别的项目的扇区
    x += Math.cos(h) * SPACING; z += Math.sin(h) * SPACING;
    /* 再叠一层垂直于「往外」方向的随机摆动，让路看起来是随手拐出去的，而不是一条直线 */
    lat += (r() - 0.5) * 6; lat *= 0.8; if(lat > 4) lat = 4; if(lat < -4) lat = -4;
    out.push({x: x - Math.sin(base) * lat, z: z + Math.cos(base) * lat});
  }
  return out;
}

/* 路的控制点：从首都边缘出发，依次经过每座城 */
export function roadPoints(slot, seedStr, n){
  const base = slotAngle(slot);
  const start = {x: Math.cos(base) * (HUB_RADIUS - 2), z: Math.sin(base) * (HUB_RADIUS - 2)};
  return [start, ...cityPositions(slot, seedStr, n)];
}

/* Catmull-Rom 采样：scene 画路、算「陆地」都用同一份，保证车能开的地方就是画出来的地 */
export function sampleRoad(points, perSegment = 8){
  if(points.length < 2) return points.slice();
  const out = [];
  const P = i => points[Math.max(0, Math.min(points.length - 1, i))];
  for(let i = 0; i < points.length - 1; i++){
    const p0 = P(i - 1), p1 = P(i), p2 = P(i + 1), p3 = P(i + 2);
    for(let s = 0; s < perSegment; s++){
      const t = s / perSegment, t2 = t * t, t3 = t2 * t;
      const f = (a, b, c, d) => 0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3);
      out.push({x: f(p0.x, p1.x, p2.x, p3.x), z: f(p0.z, p1.z, p2.z, p3.z)});
    }
  }
  out.push(points[points.length - 1]);
  return out;
}

export const LAND_RADIUS = 15;
/* 陆地 = 首都的大圆 + 沿路每隔几格一个小圆；返回 [{x,z,r}] */
export function landDisks(roads){
  const disks = [{x: 0, z: 0, r: HUB_RADIUS + 12}];
  for(const pts of roads){
    const s = sampleRoad(pts, 3);
    for(let i = 0; i < s.length; i += 2) disks.push({x: s[i].x, z: s[i].z, r: LAND_RADIUS});
  }
  return disks;
}
export function onLand(disks, x, z){
  for(const d of disks){ const dx = x - d.x, dz = z - d.z; if(dx * dx + dz * dz <= d.r * d.r) return true; }
  return false;
}

/* ---------- 项目与步骤 ---------- */
export function stagesOf(steps){
  const out = [];
  steps.forEach((s, i) => {
    const name = (s.stage || '').trim() || '主线';
    const last = out[out.length - 1];
    if(last && last.name === name) last.idx.push(i);
    else out.push({name, idx: [i]});
  });
  out.forEach(g => { g.done = g.idx.every(i => !!steps[i].doneAt); g.key = String(hash32(g.name)); });
  return out;
}

export function progressOf(project){
  const steps = project.steps || [];
  const done = steps.filter(s => s.doneAt).length;
  const next = steps.findIndex(s => !s.doneAt);
  return {done, total: steps.length, nextIndex: next, finished: steps.length > 0 && done === steps.length};
}

/* 整张地图亮了多少，0–1；scene 用它调环境光 */
export function overallProgress(projects){
  let d = 0, t = 0;
  for(const p of projects){ const g = progressOf(p); d += g.done; t += g.total; }
  return t ? d / t : 0;
}

export function nextStepId(project){
  let max = 0;
  for(const s of project.steps || []){ const m = /^s(\d+)$/.exec(s.id); if(m) max = Math.max(max, +m[1]); }
  return 's' + (max + 1);
}

/* 刚把 stepId 标记完成后，应该发哪些分。每条都有固定 id，所以重复调用也只会发一次（由 awardOnce 保证） */
export function dueAwards(project, stepIdDone){
  const steps = project.steps || [];
  const idx = steps.findIndex(s => s.id === stepIdDone);
  if(idx < 0 || !steps[idx].doneAt) return [];
  const out = [{id: `mapstep-${project.id}-${stepIdDone}`, category: 'mapstep', label: `点亮「${steps[idx].title}」`, amount: STEP_POINTS}];
  const stages = stagesOf(steps);
  const g = stages.find(g => g.idx.includes(idx));
  if(g && g.done && stages.length > 1) out.push({id: `mapstage-${project.id}-${g.key}`, category: 'mapstage', label: `阶段完成：${g.name}`, amount: STAGE_BONUS});
  if(progressOf(project).finished) out.push({id: `mapdone-${project.id}`, category: 'mapproject', label: `项目完成：${project.title}`, amount: PROJECT_BONUS});
  return out;
}

/* 引用资料：编辑框里一行一条，「标题 | 链接」或只写一个链接 / 一段文字 */
export function parseRefs(text){
  return String(text || '').split('\n').map(l => l.trim()).filter(Boolean).map(l => {
    const m = /^(.*?)\s*\|\s*(https?:\/\/\S+)$/.exec(l);
    if(m) return {title: m[1] || m[2], url: m[2]};
    if(/^https?:\/\/\S+$/.test(l)) return {title: l, url: l};
    return {title: l};
  });
}
export function refsToText(refs){ return (refs || []).map(r => r.url && r.title !== r.url ? `${r.title} | ${r.url}` : (r.url || r.title)).join('\n'); }

/* ---------- 模板（预设，创建项目时复制一份，之后随便改） ---------- */
const S = (stage, title, detail, refs = []) => ({stage, title, detail, refs});
export const TEMPLATES = [
  {
    id: 'music-demo', icon: '🎵', name: '第一首 demo（Logic Pro）',
    intro: '从零做出一首 60–90 秒的完整 demo，不求好听，先求做完。每步约半天。',
    steps: [
      S('先听懂一首歌', '拆解参考曲', '选一首参考曲（比如 James Blake《Say What You Will》），听三遍。每遍只盯一类声音，在纸上写下：钢琴/和弦、人声、bass、鼓、混响/空间，各自什么时候进来、什么时候退出。'),
      S('先听懂一首歌', '在 Logic 里搭好空工程', '新建工程，设好速度（先用 70–90 BPM）和调，建好空轨道：钢琴、bass、鼓、人声。不用做任何音乐，只要能一键播放、能录音。'),
      S('搭骨架', '写一段 4 小节和弦', '用钢琴音色，找一个偏忧郁的四和弦循环，录下来。最多重录三次，第三次就是最终版。'),
      S('搭骨架', '哼出一句 sad 的主旋律', '跟着和弦哼，录下来（手机录音也行）。挑最喜欢的一句，再用 MIDI 或人声录进工程里。'),
      S('搭骨架', '叠一条 bass', '跟着和弦根音录一条 bass，节奏越简单越好。能听出和弦在「往下沉」就够了。'),
      S('搭骨架', '极简鼓', '只放底鼓和一点点 snap 或 hi-hat。留很多空白，James Blake 的味道很大一部分来自「没有的东西」。'),
      S('加空间', '给人声和钢琴加混响与延迟', '用发送（send）加一个共用的 reverb 和一个 delay，只调两个旋钮：混响长度、混响湿度。听「空间」是怎么长出来的。'),
      S('加空间', '排出 60–90 秒的结构', '把循环排成：前奏 → 主歌 → 副歌（加一层声音）→ 尾声。每一段只靠「加一层」或「减一层」来区分。'),
      S('出成品', '粗混一遍', '只做三件事：把每轨音量调平衡、把 bass 和钢琴的低频错开（EQ）、人声稍微压一压（compression）。不用求专业。'),
      S('出成品', '导出 v0.1 并写三句话', '导出 mp3，听三遍，写下：哪里好、哪里烂、下一版只改一件什么事。烂也要导出，这是第一首。'),
    ],
  },
  {
    id: 'write-post', icon: '✍️', name: '写一篇文章',
    intro: '从选题到发布的最小路线，每步约半天。',
    steps: [
      S('想清楚', '定题目和读者', '用两句话写：这篇文章要对谁说什么。写不出来就换题。'),
      S('想清楚', '列提纲', '列 3–5 个小标题，每个下面写一句话的论点。'),
      S('写', '写出烂草稿', '不回头、不修改，只往前写完。'),
      S('写', '改第二稿', '删掉三分之一，把每段第一句改成论点。'),
      S('发出去', '最后通读并发布', '大声读一遍，改掉绕口的地方，发出去。'),
    ],
  },
  {
    id: 'build-tool', icon: '🛠️', name: '做一个小工具',
    intro: '从想法到能用的小工具，每步约半天。',
    steps: [
      S('想清楚', '写下这个工具解决什么', '一句话写清：谁在什么时候用它做什么。再写三条「一定不做」的功能。'),
      S('想清楚', '画出界面草图', '纸上画出最主要的一个界面，标出点哪里会发生什么。'),
      S('做出来', '做出能跑的最小版本', '只实现最核心的一个动作，先不管好不好看。'),
      S('做出来', '加上第二个功能并自己用一天', '自己真实用一天，记下卡顿和不顺手的地方。'),
      S('发出去', '修最影响使用的三个问题并发布', '只修最影响使用的三个。发布并写一段说明。'),
    ],
  },
  {
    id: 'blank', icon: '🗺️', name: '空白项目',
    intro: '三步占位，自己改成你要的。',
    steps: [
      S('主线', '第一步：写下目标', '用一句话写清这个项目要做出什么。'),
      S('主线', '第二步：做出最小的一块', '只做半天能做完的量。'),
      S('主线', '第三步：看看做出来的东西', '回头看，决定下一步。'),
    ],
  },
];

export function templateById(id){ return TEMPLATES.find(t => t.id === id) || TEMPLATES[TEMPLATES.length - 1]; }

/* 新项目：slot 取目前没被占用的最小编号，所以删掉一个项目后新项目会占它的位置 */
export function freeSlot(projects){
  const used = new Set(projects.map(p => p.slot));
  let s = 0; while(used.has(s)) s++; return s;
}
export function newProject({id, title, templateId, slot, color, now}){
  const t = templateById(templateId);
  return {
    id, title: title || t.name, templateId: t.id, icon: t.icon, slot,
    color: color || PROJECT_COLORS[slot % PROJECT_COLORS.length],
    parked: false, createdAt: now,
    steps: t.steps.map((s, i) => ({id: 's' + (i + 1), title: s.title, detail: s.detail, refs: s.refs, stage: s.stage, doneAt: null})),
  };
}

/* 从数据库读出来的文档，补齐缺的字段，防止旧数据或手改数据让页面报错 */
export function normalizeProject(id, data){
  const d = data || {};
  return {
    id, title: d.title || '未命名项目', templateId: d.templateId || 'blank', icon: d.icon || '🗺️',
    slot: Number.isInteger(d.slot) ? d.slot : 0,
    color: d.color || PROJECT_COLORS[0],
    parked: !!d.parked, createdAt: d.createdAt || 0,
    steps: (Array.isArray(d.steps) ? d.steps : []).map((s, i) => ({
      id: s.id || 's' + (i + 1), title: s.title || '未命名步骤', detail: s.detail || '',
      refs: Array.isArray(s.refs) ? s.refs : [], stage: s.stage || '主线', doneAt: s.doneAt || null,
    })),
  };
}

/* 同时进行的（没停放、没做完）项目数 */
export function activeCount(projects){
  return projects.filter(p => !p.parked && !progressOf(p).finished).length;
}
