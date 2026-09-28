/* 课程内容从网站上的 courses/ 目录读（仓库里的 JSON，推送即发布） */
import { T } from './state.js';
import { unitKey } from '../core/study.js';

async function getJSON(path){
  const res = await fetch(path, {cache:'no-cache'});
  if(!res.ok) throw new Error(`读取 ${path} 失败（${res.status}）`);
  return res.json();
}

export async function loadCourses(){
  if(!T.courses.length) T.courses = (await getJSON('courses/index.json')).courses;
  return T.courses;
}

export async function loadCourse(courseId){
  if(!T.courseCache[courseId]){
    const entry = (await loadCourses()).find(c=>c.id===courseId);
    if(!entry) throw new Error('找不到这门课');
    T.courseCache[courseId] = {...await getJSON(`courses/${entry.path}/course.json`), path:entry.path};
  }
  return T.courseCache[courseId];
}

/* 返回 {course, unit}；unit.file 为空表示这一节还没写好 */
export async function loadUnit(courseId, unitId){
  const course = await loadCourse(courseId);
  const meta = course.units.find(u=>u.id===unitId);
  if(!meta) throw new Error('找不到这一节');
  if(!meta.file) return {course, unit:null, meta};
  const key = unitKey(courseId, unitId);
  if(!T.unitCache[key]) T.unitCache[key] = {...meta, ...await getJSON(`courses/${course.path}/${meta.file}`)};
  return {course, unit:T.unitCache[key], meta};
}
