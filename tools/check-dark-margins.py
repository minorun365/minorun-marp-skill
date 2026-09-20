#!/usr/bin/env python3
"""黒地テーマ（minorun-dark）のデッキで、各ページの中身が下端・右端にどれだけ迫っているかを画像から測る。

使い方: python3 tools/check-dark-margins.py <deck.pdf> [--bottom 60] [--right 60]
仕組み: 各ページを 1280x720 相当（100dpi 相当）に焼き、黒（背景）でないピクセルの最下行・最右列を取る。
       右下のページ番号（幅 140px・高さ 48px の隅）は除外する。全面画像の枚（bg cover）と、表紙のように下端まで帯を敷いた枚は対象外。
       必要なもの: pdftoppm（poppler）、Pillow
"""
import sys, subprocess, tempfile, os, glob
from PIL import Image

pdf = sys.argv[1]
def opt(name, default):
    return int(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default
MIN_B, MIN_R = opt('--bottom', 60), opt('--right', 60)
tmp = tempfile.mkdtemp()
subprocess.run(['pdftoppm', '-png', '-r', '96', pdf, os.path.join(tmp, 'p')], check=True, stderr=subprocess.DEVNULL)
ng = 0; n = 0
for f in sorted(glob.glob(os.path.join(tmp, 'p-*.png'))):
    n += 1
    im = Image.open(f).convert('L'); W, H = im.size
    sx = 1280 / W
    px = im.load()
    # 全面画像（黒でないピクセルが半分以上）は対象外
    dark = sum(1 for y in range(0, H, 6) for x in range(0, W, 6) if px[x, y] < 24)
    if dark < (W // 6) * (H // 6) * 0.5:
        continue
    maxy = -1; maxx = -1
    for y in range(H):
        for x in range(W):
            if px[x, y] >= 40:
                if x > W - 140 / sx and y > H - 48 / sx:  # ページ番号の隅
                    continue
                if y > maxy: maxy = y
                if x > maxx: maxx = x
    if maxy < 0: continue
    # 表紙の帯のように、最下行がほぼ全幅で塗られている枚は意図した全面の面なので対象外
    if maxy == H - 1 and sum(1 for x in range(0, W, 4) if px[x, H - 1] >= 40) > (W // 4) * 0.9:
        continue
    bottom = round((H - 1 - maxy) * sx); right = round((W - 1 - maxx) * sx)
    flags = []
    if bottom < MIN_B: flags.append(f'下端の空き {bottom}px（最低 {MIN_B}）')
    if right < MIN_R: flags.append(f'右端の空き {right}px（最低 {MIN_R}）')
    if flags:
        ng += 1; print(f'NG p{n} ' + ' / '.join(flags))
print(f'{n} ページ走査、NG {ng} 件')
sys.exit(1 if ng else 0)
