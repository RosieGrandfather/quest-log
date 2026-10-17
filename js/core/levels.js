/* 按累计获得计算；首次升级 1600 XP，此后每次多需 800 XP，不封顶。 */
export const LEVEL_FIRST_STEP = 1600;
export const LEVEL_STEP_GROWTH = 800;
const NAMES = ['新手上路','打好地基','小试牛刀','渐入佳境','独当一面','融会贯通','炉火纯青','崭露头角','步入正轨','渐成气候',
  '游刃有余','登堂入室','自成一派','声名鹊起','独步一方','名扬四海','出类拔萃','登峰造极','一代宗师','传奇远征者'];
function levelMin(index){
  return index*LEVEL_FIRST_STEP + index*(index-1)/2*LEVEL_STEP_GROWTH;
}
export const LEVELS = NAMES.map((name, i)=> ({name, min:levelMin(i)}));
export function levelInfo(total){
  const xp = Math.max(0, Number.isFinite(total) ? total : 0);
  const b = LEVEL_FIRST_STEP - LEVEL_STEP_GROWTH/2;
  const idx = Math.floor(2*xp/(b + Math.sqrt(b*b + 2*LEVEL_STEP_GROWTH*xp)));
  return {name:NAMES[Math.min(idx, NAMES.length-1)], sub:`Lv.${idx+1}`,
    curMin:levelMin(idx), nextMin:levelMin(idx+1)};
}
