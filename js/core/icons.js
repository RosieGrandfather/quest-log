/* 按文档 id 哈希自动分配图标，同一个任务 / 奖励永远是同一个图标 */
/* 通用奇幻/魔法学院风格的小图标(魔杖、药水瓶、咒语书……)，
   不使用任何特定作品的商标图案(比如院徽、闪电疤痕、金色飞贼这类) */
export const REWARD_ICONS = [
  '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 19L17 7"/><path d="M15 3l1 2 2 1-2 1-1 2-1-2-2-1 2-1z"/></svg>',
  '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M10 3h4"/><path d="M10 3v5l-4.5 8A2 2 0 0 0 7.2 19h9.6a2 2 0 0 0 1.7-3l-4.5-8V3"/><path d="M8 14h8"/></svg>',
  '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5.5C4 4.7 4.7 4 5.5 4H12v16H5.5A1.5 1.5 0 0 1 4 18.5v-13z"/><path d="M20 5.5c0-.8-.7-1.5-1.5-1.5H12v16h6.5a1.5 1.5 0 0 0 1.5-1.5v-13z"/></svg>',
  '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10h16l-1.5 7a2 2 0 0 1-2 1.6H7.5a2 2 0 0 1-2-1.6L4 10z"/><path d="M2 10h20"/><path d="M9 6.5c0-1 1-2 3-2s3 1 3 2"/></svg>',
  '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="7"/><circle cx="9.3" cy="11" r="1.6"/><circle cx="14.7" cy="11" r="1.6"/><path d="M12 13.5l-1 2h2l-1-2z"/><path d="M5 8l2.5 1.5M19 8l-2.5 1.5"/></svg>',
  '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 4L9 15"/><path d="M4 20l3-6 4 4-6 3z"/><path d="M9 15l1.5-3M11 17l1.5-3"/></svg>',
  '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3z"/></svg>',
  '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21h6"/><rect x="9" y="9" width="6" height="12" rx="1"/><path d="M12 9V5"/><path d="M12 5c-1 0-1.5-1-1-2 .3.6 1 .6 1 0 0 .6.7.6 1 0 .5 1 0 2-1 2z"/></svg>',
  '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="7" cy="14" r="3.2"/><path d="M9.3 11.7L18 3M15 6l2 2M17 4l2 2"/></svg>',
  '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h12M6 21h12"/><path d="M7 3c0 4 4 6 5 8-1 2-5 4-5 8M17 3c0 4-4 6-5 8 1 2 5 4 5 8"/></svg>',
];
function hashStr(s){
  let h = 0;
  for(let i=0;i<s.length;i++){ h = (h*31 + s.charCodeAt(i)) | 0; }
  return Math.abs(h);
}
export function iconForReward(r){
  const key = String(r.id || r.name || 'x');
  return REWARD_ICONS[hashStr(key) % REWARD_ICONS.length];
}

export const TASK_ICONS = [
  '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5.5C4 4.7 4.7 4 5.5 4H14v16H5.5c-.8 0-1.5-.7-1.5-1.5v-13z"/><path d="M14 4h4.5c.8 0 1.5.7 1.5 1.5v13c0 .8-.7 1.5-1.5 1.5H14"/><path d="M7 8h4M7 11h4"/></svg>',
  '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M15.5 4.5l4 4L8 20l-4.5 1L4.5 16.5 15.5 4.5z"/><path d="M13 7l4 4"/></svg>',
  '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="0.6" fill="currentColor"/></svg>',
  '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.8 4.6L18 9l-4.2 1.4L12 15l-1.8-4.6L6 9l4.2-1.4L12 3z"/><path d="M12 15v6M9 21h6"/></svg>',
  '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l-3.5-3.5a7 7 0 1 1 10 0L12 18"/><path d="M9 18v2.5h6V18"/></svg>',
  '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 15l4-4 3 3 5-6 4 4"/><path d="M4 20h16"/></svg>',
  '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="12" rx="1.5"/><path d="M8 21h8M12 17v4"/></svg>',
  '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 21V8l7-5 7 5v13"/><path d="M9 21v-6h6v6"/></svg>',
  '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>',
  '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>',
];
export function iconForTask(t){
  const key = (t.id || t.name || '') + '';
  return TASK_ICONS[hashStr(key) % TASK_ICONS.length];
}
