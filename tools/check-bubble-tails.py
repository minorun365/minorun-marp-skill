#!/usr/bin/env python3
"""吹き出しのしっぽ（::before / ::after の三角形）が、箱の縁で突き合わせになっていないかを検出する。

しっぽの底辺を箱の縁ぴったりで止めると、箱の縁としっぽの縁のぼかしが重なり、
継ぎ目に1pxの濃い線が出る。
しっぽは箱の「裏」へ4pxもぐらせて継ぎ目そのものを無くす。そのためには次の2つが要る。

- しっぽの擬似要素に z-index: -1（箱の背景より奥に描く。前面にかぶらない）
- 箱の側に isolation: isolate（無いと z-index: -1 がスライドの背景の裏へ回って消える）

長さは「見せたい長さ＋4px」を border に書き、位置の負値は見せたい長さのままにする
（例：border-left: 48px と right: -44px）。

使い方: python3 tools/check-bubble-tails.py "<deck>.md"
"""
import re, sys


def rules(md):
    for m in re.finditer(r'<style[^>]*>(.*?)</style>', md, re.S):
        css = re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S)
        line = md.count('\n', 0, m.start()) + 1
        page = md.count('\n---\n', 0, m.start())
        for sel, body in re.findall(r'([^{}]+)\{([^{}]*)\}', css):
            yield line, page, css, sel.strip(), body


def is_tail(body):
    # 透明でない色の太いボーダーを1辺だけ持つ絶対配置の擬似要素＝三角形のしっぽ
    solid = [m for m in re.finditer(r'border-(left|right|top|bottom)\s*:\s*(\d+)px\s+solid\s+([^;]+)', body)
             if 'transparent' not in m.group(3)]
    return 'position' in body and 'absolute' in body and solid


def main(path):
    md = open(path, encoding='utf-8').read()
    ng = n = 0
    for line, page, style, sel, body in rules(md):
        if '::before' not in sel and '::after' not in sel:
            continue
        if not is_tail(body):
            continue
        n += 1
        owner = sel.split('::')[0].strip()
        # 同じ <style> の中に、箱の側の isolation があるか
        iso = re.search(re.escape(owner) + r'\s*\{[^}]*isolation\s*:\s*isolate', style)
        miss = []
        if not re.search(r'z-index\s*:\s*-1', body):
            miss.append('しっぽに z-index: -1 が無い')
        if not iso:
            miss.append(f'{owner} に isolation: isolate が無い')
        if miss:
            ng += 1
            print(f'NG p{page}（{line}行目の<style>） {sel}: ' + '／'.join(miss))
    print(f'しっぽ {n} 個を走査、NG {ng} 個' + ('' if ng else '（継ぎ目の出ない書き方）'))
    return 1 if ng else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
