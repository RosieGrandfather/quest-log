/* 等级按「累计获得」算（兑换奖励不扣）。超过最后一级后每 +5000 分再升一级，不封顶。 */
export const LEVELS = [
  {name:'新手上路', min:0},
  {name:'打好地基', min:100},
  {name:'小试牛刀', min:250},
  {name:'渐入佳境', min:450},
  {name:'独当一面', min:700},
  {name:'融会贯通', min:1000},
  {name:'炉火纯青', min:1400},
  {name:'崭露头角', min:1900},
  {name:'步入正轨', min:2500},
  {name:'渐成气候', min:3200},
  {name:'游刃有余', min:4000},
  {name:'登堂入室', min:5000},
  {name:'自成一派', min:6200},
  {name:'声名鹊起', min:7600},
  {name:'独步一方', min:9200},
  {name:'名扬四海', min:11000},
  {name:'出类拔萃', min:13000},
  {name:'登峰造极', min:15200},
  {name:'一代宗师', min:17600},
  {name:'传奇远征者', min:20200},
];

export function levelInfo(total){
  let idx=0;
  for(let i=0;i<LEVELS.length;i++){ if(total>=LEVELS[i].min) idx=i; }
  const cur = LEVELS[idx];
  const next = LEVELS[idx+1];
  if(next){
    return {name:cur.name, sub:`Lv.${idx+1}`, curMin:cur.min, nextMin:next.min};
  }
  const over = total - cur.min;
  const stage = Math.floor(over/5000);
  const stageMin = cur.min + stage*5000;
  return {name:cur.name, sub:`Lv.${LEVELS.length+stage}`, curMin:stageMin, nextMin:stageMin+5000};
}
