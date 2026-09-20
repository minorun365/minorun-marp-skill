#!/usr/bin/env python3
"""図・箱の中の文字を全ページ実測する。①小さすぎる文字 ②箱の縁に詰まった文字。

    python3 tools/check-figure-text.py <deck.pdf> [--min-pt 16] [--min-pad 14] [--bg dark|light]

SVG のソースに 21px と書いてあっても、`![center w:820]` で縮めて貼ると 13pt になる。
書き出した PDF から実寸で測るのが唯一確実。

- ① pt は版面 1280x720 基準。ページ下端のページ番号・フッターは除外する
- ② 文字の左右の直近の画素がスライドの背景色でないとき「箱の中」とみなし、背景色になるまでの距離を測る。
  吹き出し・補足ボックス・SVG の箱すべてに効く。--bg で背景を指定する（既定は黒地の dark）
  文字が箱の外へはみ出しているケースは背景が隣接するので拾えない。そちらは check-svg-box-fit.mjs の担当
- 直し方: 文言を短くする → 箱を広げる → 図の幅を上げる → font-size を上げる、の順

必要なもの: mutool（mupdf-tools）、pdfinfo（poppler）、Pillow
"""
import html, io, re, subprocess, sys, unicodedata
from PIL import Image


def opt(name, default, cast=float):
    return cast(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("--"):
        print(__doc__); sys.exit(2)
    pdf = sys.argv[1]
    min_pt = opt("--min-pt", 16.0)
    min_pad = int(opt("--min-pad", 14))
    bg = opt("--bg", "dark", str)
    if bg == "dark":
        is_bg = lambda px: px[0] < 24 and px[1] < 24 and px[2] < 24
    else:
        is_bg = lambda px: px[0] > 235 and px[1] > 235 and px[2] > 235

    n = int(subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout.split("Pages:")[1].split()[0])
    ng = 0
    for p in range(1, n + 1):
        out = subprocess.run(["mutool", "draw", "-F", "stext", "-o", "-", pdf, str(p)],
                             capture_output=True, text=True).stdout
        lines = []
        for m in re.finditer(r'<line bbox="([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+)"(.*?)</line>', out, re.S):
            x0, y0, x1, y1 = (float(v) for v in m.groups()[:4]); body = m.group(5)
            if y0 > 480:          # ページ番号・フッター（PDF は 960x540 基準）
                continue
            sizes = [float(v) for v in re.findall(r'size="([\d.]+)"', body)]
            txt = unicodedata.normalize("NFKC", html.unescape("".join(re.findall(r'c="([^"]*)"', body)))).strip()
            if sizes and txt:
                lines.append((x0 / .75, y0 / .75, x1 / .75, y1 / .75, min(sizes), txt))
        small = [(round(s), t[:24]) for *_, s, t in lines if s < min_pt]
        if small:
            ng += 1; print(f"NG p{p:>2} 小さい文字（{min_pt:g}pt未満）:", sorted(set(small))[:8])

        png = subprocess.run(["mutool", "draw", "-r", "96", "-w", "1280", "-h", "720", "-o", "-", "-F", "png",
                              pdf, str(p)], capture_output=True).stdout
        im = Image.open(io.BytesIO(png)).convert("RGB")
        W, H = im.size
        for x0, y0, x1, y1, s, txt in lines:
            yc = min(H - 1, int((y0 + y1) / 2)); xr = int(x1) + 2; xl = int(x0) - 2
            if xr >= W or xl < 0 or is_bg(im.getpixel((xr, yc))) or is_bg(im.getpixel((xl, yc))):
                continue

            def run(x, step):
                d = 0
                while 0 <= x < W and not is_bg(im.getpixel((x, yc))):
                    x += step; d += 1
                return d

            r, l = run(xr, 1), run(xl, -1)
            if (r < min_pad or l < min_pad) and max(r, l) < 400:
                ng += 1
                print(f"NG p{p:>2} 箱の縁に詰まっている「{txt[:26]}」 左 {l}px / 右 {r}px（最低 {min_pad}px）")
    print(f"\n{n} ページ走査、NG {ng} 件")
    sys.exit(1 if ng else 0)


if __name__ == "__main__":
    main()
