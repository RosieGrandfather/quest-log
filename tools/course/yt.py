"""YouTube 小工具：搜索视频、核实能否嵌入、拿到时长。

  python tools/course/yt.py search "3blue1brown eigenvectors" "statquest entropy"
  python tools/course/yt.py verify PFDu9oVAE-g YtebGVx-Fxw

verify 用的是 YouTube 官方 oEmbed 接口：能返回标题 = 视频存在且允许嵌入；
报错 = 视频不存在或作者关闭了嵌入，这种视频不要放进课程。
（Windows 上中文输出乱码时，先 set PYTHONIOENCODING=utf-8）
"""
import json, re, sys, urllib.parse, urllib.request

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Accept-Language': 'en-US,en;q=0.9'}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode('utf-8', 'replace')

def search(q, n=6):
    """返回 [(id, 标题, 频道, 时长)]。解析的是搜索结果页，YouTube 改版后可能需要调整"""
    html = get('https://www.youtube.com/results?search_query=' + urllib.parse.quote(q))
    m = re.search(r'var ytInitialData = (\{.*?\});</script>', html)
    if not m: return []
    out = []
    def walk(o):
        if isinstance(o, dict):
            if 'videoRenderer' in o:
                v = o['videoRenderer']
                title = ''.join(r.get('text', '') for r in v.get('title', {}).get('runs', []))
                ch = ''.join(r.get('text', '') for r in v.get('ownerText', {}).get('runs', []))
                out.append((v['videoId'], title, ch, v.get('lengthText', {}).get('simpleText', '')))
            for x in o.values(): walk(x)
        elif isinstance(o, list):
            for x in o: walk(x)
    walk(json.loads(m.group(1)))
    return out[:n]

def verify(vid):
    """返回 (id, 标题, 频道, 时长) 或 (id, 'NOT EMBEDDABLE / MISSING', 错误)"""
    try:
        o = json.loads(get(f'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json'))
    except Exception as e:
        return (vid, 'NOT EMBEDDABLE / MISSING', str(e)[:60])
    m = re.search(r'"lengthSeconds":"(\d+)"', get(f'https://www.youtube.com/watch?v={vid}'))
    secs = int(m.group(1)) if m else 0
    return (vid, o['title'], o['author_name'], f'{secs // 60}:{secs % 60:02d}')

if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] not in ('search', 'verify'):
        print(__doc__); sys.exit(1)
    if sys.argv[1] == 'search':
        for q in sys.argv[2:]:
            print('##', q)
            for r in search(q): print('  ', ' | '.join(r))
    else:
        for vid in sys.argv[2:]:
            print(' | '.join(verify(vid)))
