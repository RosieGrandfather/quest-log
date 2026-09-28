/* 学习区共享状态 */
export const T = {
  uid: null,
  cols: null,
  courses: [],          // courses/index.json
  courseCache: {},      // courseId -> course.json
  unitCache: {},        // unitKey -> unit json
  progress: {},         // unitKey -> studyProgress 文档（测验成绩、上次答题）
  completed: {},        // unitKey -> 首次学完的日期（来自 log 里的 study 记录）
  studyDates: [],       // 有效学习日
};
