"""去掉课件开头的套话（Yijia 2026-10-09 的要求）。

删掉：
  - 「**本节安排…**」「**本小节安排…**」「**怎么学这一节/这一小节…**」「**这一节分成 N 个小节…**」
  - 拆分时自动生成的「这是「…」分成的第 k 个小节…」那一段
  - 「### 先说这一节要干什么」「### 先说这一小节要干什么」标题；手写的这一段里只留代码、表格、引用块，说明文字和「学完它你就能…」清单全删
  - 「**承接上一小节：** …」那段说明（代码块留着，在第一个代码块前加一行注释）
dump() 和 split.py 写文件前都会调用，所以以后新出的课件不会再带上这些套话。
命令行：python3 tools/course/cleanintro.py [--check]   （--check 只报告，不写文件）
"""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))

INTRO_HEAD = re.compile(r'^### 先说这一(小)?节要干什么\s*$')
DROP_START = ('**本节安排', '**本小节安排', '**怎么学这一节', '**怎么学这一小节', '**这一节分成')
GEN_INTRO = re.compile(r'^这是「.*」分成的第 \d+ 个小节')
CARRY = '**承接上一小节：**'
CARRY_COMMENT = '# 承接上一小节：先运行，重新定义前面用到的变量'

def _blocks(md):
    blocks, cur, fence = [], [], False
    for line in md.split('\n'):
        if line.lstrip().startswith('```'): fence = not fence
        if not fence and line.strip() == '' and not line.lstrip().startswith('```'):
            if cur: blocks.append('\n'.join(cur)); cur = []
        else:
            cur.append(line)
    if cur: blocks.append('\n'.join(cur))
    return blocks

def _keep_in_intro(b):
    return b.startswith('```') or b.startswith('>') or b.startswith('|') or b.startswith('$$')

def clean_md(md):
    blocks = _blocks(md)
    out, in_intro, hand, first = [], False, False, False
    carry_pending = False
    for b in blocks:
        if b.startswith('### '):
            in_intro = bool(INTRO_HEAD.match(b.split('\n')[0]))
            if in_intro: hand, first = True, True; continue      # 标题本身不要
            out.append(b); continue
        if in_intro and first:
            first = False
            if GEN_INTRO.match(b): hand = False                    # 自动生成的开头：只删套话，后面的内容保留
        if b.startswith(DROP_START) or GEN_INTRO.match(b):
            continue
        if b.startswith(CARRY):
            carry_pending = True; continue
        if in_intro and hand and not _keep_in_intro(b):
            continue
        if carry_pending and b.startswith('```python'):
            carry_pending = False
            if CARRY_COMMENT not in b:
                b = b.replace('```python\n', '```python\n' + CARRY_COMMENT + '\n', 1)
        out.append(b)
    return '\n\n'.join(out)

def clean_unit(unit):
    n = 0
    for blk in unit.get('blocks', []):
        if blk.get('type') == 'text' and 'md' in blk:
            new = clean_md(blk['md'])
            if new != blk['md']: blk['md'] = new; n += 1
    unit['blocks'] = [b for b in unit.get('blocks', []) if not (b.get('type') == 'text' and not b['md'].strip())]
    return n

def main(check=False):
    files = [f for f in glob.glob(os.path.join(REPO, 'courses', '*', 'u*.json'))]
    files += glob.glob(os.path.join(HERE, 'whole', '*', '*.json'))
    changed = {}
    for f in sorted(files):
        try: d = json.load(open(f, encoding='utf-8'))
        except Exception: continue
        if 'blocks' not in d: continue
        if clean_unit(d):
            key = os.path.relpath(os.path.dirname(f), REPO)
            changed[key] = changed.get(key, 0) + 1
            if not check:
                json.dump(d, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    for k, v in changed.items(): print(f'{k}: {v} 个文件{"需要清理" if check else "已清理"}')
    if not changed: print('没有需要清理的文件')

if __name__ == '__main__':
    main(check='--check' in sys.argv)
