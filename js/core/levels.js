/* 等级按「累计获得」算（兑换奖励不扣）。
   每级之间相差 LEVEL_STEP 分：按每周大约 800 分的学习节奏，大约一周升一级。
   以后觉得太快 / 太慢，只改这一个数。超过最后一级后每 +LEVEL_STEP 分再升一级，不封顶。 */
export const LEVEL_STEP = 800;
const NAMES = ['新手上路','打好地基','小试牛刀','渐入佳境','独当一面','融会贯通','炉火纯青','崭露头角','步入正轨','渐成气候',
  '游刃有余','登堂入室','自成一派','声名鹊起','独步一方','名扬四海','出类拔萃','登峰造极','一代宗师','传奇远征者'];
export const LEVELS = NAMES.map((name, i)=> ({name, min: i*LEVEL_STEP}));

export function levelInfo(total){
  let idx=0;
  for(let i=0;i<LEVELS.length;i++){ if(total>=LEVELS[i].min) idx=i; }
  const cur = LEVELS[idx];
  const next = LEVELS[idx+1];
  if(next){
    return {name:cur.name, sub:`Lv.${idx+1}`, curMin:cur.min, nextMin:next.min};
  }
  const over = total - cur.min;
  const stage = Math.floor(over/LEVEL_STEP);
  const stageMin = cur.min + stage*LEVEL_STEP;
  return {name:cur.name, sub:`Lv.${LEVELS.length+stage}`, curMin:stageMin, nextMin:stageMin+LEVEL_STEP};
}
