import { localISO } from './dates.js';

/* 积分 / 连续打卡都是根据 log 实时算的，不是存好的字段 */
export function computeStats(logEntries, now = new Date()){
  let totalEarned=0, totalSpent=0, entriesCount=0;
  const earnDates = new Set();
  logEntries.forEach(e=>{
    if(e.kind==='earn'){
      totalEarned += Number(e.amount)||0;
      if(e.dateISO) earnDates.add(e.dateISO);
      // 每日上线奖励算积分和连续打卡，但不算"记录次数"
      if(e.category!=='daily') entriesCount++;
    }
    else if(e.kind==='spend'){ totalSpent += Number(e.amount)||0; }
  });
  return {totalEarned, totalSpent, balance: totalEarned-totalSpent, entriesCount, streak: computeStreak(earnDates, now)};
}

/* 今天还没记录时从昨天往前数，不会一早起来就断签 */
export function computeStreak(datesSet, now = new Date()){
  const cursor = new Date(now);
  if(!datesSet.has(localISO(cursor))){
    cursor.setDate(cursor.getDate()-1);
    if(!datesSet.has(localISO(cursor))) return 0;
  }
  let streak=0;
  while(datesSet.has(localISO(cursor))){
    streak++;
    cursor.setDate(cursor.getDate()-1);
  }
  return streak;
}
