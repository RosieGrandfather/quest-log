/* 「接着上次读」的纯规则（不碰浏览器，可以测试）。
   位置不存像素，而是存「读到第几个内容块、该块顶边离屏幕顶多远」：
   页面里有图片 / 代码输出 / 展开的「想一想」时，像素会变，内容块的序号不会。 */

/* rects：每个内容块当前的 {top, bottom}（相对屏幕）。返回屏幕顶边处的第一个块 */
export function pickAnchor(rects){
  for(let i = 0; i < rects.length; i++){
    if(rects[i].bottom > 8) return { i, off: Math.round(rects[i].top) };
  }
  return null;
}

/* 还在最开头就不用跳了 */
export function worthResuming(a){
  return !!a && Number.isInteger(a.i) && Number.isFinite(a.off) && (a.i > 0 || a.off < -200);
}
