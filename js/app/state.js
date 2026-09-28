/* 主页面的共享状态。数据由 main.js 里的实时订阅写进来，各个界面模块只读。 */
export const S = {
  uid: null,
  cols: null,        // userCols(uid)
  logEntries: [],
  rewards: [],
  tasks: [],
  sections: [],
};
