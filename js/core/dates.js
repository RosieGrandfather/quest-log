/* 日期一律用本地时区的 YYYY-MM-DD 字符串 */
export function localISO(d){
  const y=d.getFullYear(), m=String(d.getMonth()+1).padStart(2,'0'), day=String(d.getDate()).padStart(2,'0');
  return `${y}-${m}-${day}`;
}

export function fmtDateLabel(iso, now = new Date()){
  const today = localISO(now);
  const y = new Date(now); y.setDate(y.getDate()-1);
  const yesterday = localISO(y);
  if(iso===today) return '今天';
  if(iso===yesterday) return '昨天';
  return iso;
}
