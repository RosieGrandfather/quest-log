import { awardOnce } from './awards.js';
import { localISO } from '../core/dates.js';
import { DAILY_LOGIN_POINTS } from '../core/constants.js';

/* 每日上线奖励：每天第一次打开就加 DAILY_LOGIN_POINTS 分，每天最多一次。
   页面一直开着跨过零点，或者从后台切回来时，也会补发当天的奖励（由调用方定时调用）。 */
let checkedISO = null;

export function resetDailyBonus(){ checkedISO = null; }

export async function ensureDailyLoginBonus(logCol, onAwarded){
  if(!logCol) return;
  const today = localISO(new Date());
  if(checkedISO===today) return;
  checkedISO = today;
  try{
    const created = await awardOnce(logCol, 'daily-'+today,
      {category:'daily', label:'每日上线', amount:DAILY_LOGIN_POINTS, dateISO:today});
    if(created && onAwarded) onAwarded(DAILY_LOGIN_POINTS);
  }catch(e){
    checkedISO = null;
    console.error('daily login bonus failed', e);
  }
}
