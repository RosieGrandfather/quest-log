/* ============ 新用户模板（首次登录时写进这个用户自己的数据库，之后只读数据库） ============
   文档 ID 固定，这样即使手机和电脑同时首次登录，重复写入也只是覆盖成同样的内容。 */
export const SEED_SECTIONS = [
  {id:'mind', label:'精神食粮', ts:1},
  {id:'body', label:'身体', ts:2},
  {id:'life', label:'生活', ts:3},
];
export const SEED_TASKS = [
  {id:'seed-t1', name:'读 10 页书', category:'mind', points:10, ts:1},
  {id:'seed-t2', name:'学会一个新知识点', category:'mind', points:15, ts:2},
  {id:'seed-t3', name:'运动 30 分钟', category:'body', points:15, ts:3},
  {id:'seed-t4', name:'23:00 前睡觉', category:'body', points:10, ts:4},
  {id:'seed-t5', name:'整理房间 15 分钟', category:'life', points:10, ts:5},
  {id:'seed-t6', name:'自己做一顿饭', category:'life', points:10, ts:6},
];
export const SEED_REWARDS = [
  {id:'seed-r1', name:'一杯奶茶 / 咖啡', tier:'small', cost:50, ts:1},
  {id:'seed-r2', name:'看一场电影', tier:'small', cost:100, ts:2},
  {id:'seed-r3', name:'买一件想要的小东西', tier:'medium', cost:300, ts:3},
  {id:'seed-r4', name:'一次旅行', tier:'big', cost:1000, ts:4},
];

/* 老版本写死在代码里的 7 个板块。只在老账号迁移（schemaVersion < 2）时用一次：
   用原来的 id 当文档 ID 写进 sections，所以老任务 / 老记录的 category 不用改。 */
export const LEGACY_SECTIONS = [
  {id:'arena', label:'ARENA / AI 研究学习', short:'ARENA'},
  {id:'pl300', label:'PL-300 备考', short:'PL-300'},
  {id:'python', label:'Python 练习', short:'Python'},
  {id:'project', label:'自建项目', short:'项目'},
  {id:'job', label:'求职 / 转型', short:'求职'},
  {id:'review', label:'规划 / 复盘', short:'复盘'},
  {id:'custom', label:'其他（自定义）', short:'其他'},
];
export const SCHEMA_VERSION = 2;

/* 不属于任何板块的记录类型的小标签 */
export const CAT_SHORT = {reward:'奖励', daily:'签到', study:'学习', quiz:'测验', studystreak:'连续学习'};
export const DAILY_LOGIN_POINTS = 5;

export const TIER_META = {
  small:{title:'日常小奖励', cls:'small'},
  medium:{title:'中型奖励', cls:'medium'},
  big:{title:'终极大奖', cls:'big'},
};
export const TIER_ICON_COLORS = {
  small:['var(--teal-soft)','var(--teal)'],
  medium:['var(--accent-soft)','var(--accent)'],
  big:['var(--burgundy-soft)','var(--burgundy)'],
};
