/* Firebase 初始化。页面先用 <script> 引入 compat SDK 和 firebase-config.js，
   这里从全局的 firebase / firebaseConfig 拿，其他模块只从这个文件 import。 */
/* global firebase, firebaseConfig */
firebase.initializeApp(firebaseConfig);

export const auth = firebase.auth();
export const fs = firebase.firestore();
export const FieldValue = firebase.firestore.FieldValue;

export function signInWithGoogle(){
  return auth.signInWithPopup(new firebase.auth.GoogleAuthProvider());
}

/* 一个用户名下的所有集合，全部在 users/{uid}/ 下面（安全规则只允许本人读写） */
export function userCols(uid){
  const u = fs.collection('users').doc(uid);
  return {
    log: u.collection('log'),
    rewards: u.collection('rewards'),
    tasks: u.collection('tasks'),
    sections: u.collection('sections'),
    meta: u.collection('meta').doc('app'),
    studyProgress: u.collection('studyProgress'),   // 文档 ID = unitKey(courseId, unitId)
    readPos: u.collection('readPos'),               // 每节课读到哪儿（跨设备同步），文档 ID 同上
    studyNotes: u.collection('studyNotes'),         // 同上，每节一篇笔记
    journal: u.collection('journal'),               // 日记，文档 ID = 日期 YYYY-MM-DD
    projects: u.collection('projects'),             // 城邦地图的项目，每个项目一篇文档，步骤放在文档里的 steps 数组
  };
}
