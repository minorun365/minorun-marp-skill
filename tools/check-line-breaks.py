#!/usr/bin/env python3
"""Marpで書き出したPDFから、本文の改行の過不足を検出する。

使い方: python3 tools/check-line-breaks.py <deck.pdf> [--md <deck.md>] [--short 0.45] [--mean 0.36] [--run 3]
                                            [--room 1.5] [--tail 6] [--debug N]

検出するもの（1280x720換算のpx）:
  ① 改行しすぎ   : 本文幅の45%に届かない行が同じ段落で3行以上続き、その平均が本文幅の36%未満
                   （1行10字台を積み上げた形）。行の右に1.5字ぶんも空きが無いもの（スクショ横の
                   固定幅カラムで、カラムいっぱいまで使っている行）は対象外
  ② 改行の位置   : 段落の途中の行で、次のどれかに当たるもの
       - 読点の後ろの切れ端 : 行の最後の読点・句点の後ろに1〜6字だけ残して改行している
                              （「…図の文字を大きくして、すべて／16pt以上に…」→ 読点の直後で改行する）
       - 原稿に無い改行     : 原稿（同名の .md）には改行が無く、ブラウザの自動折り返しで切れている
                              （端まで伸びて改行していない）。句読点・閉じ括弧の直後で切れたものは対象外
       - 右端まで伸びている : 原稿が無いときの代わり。句読点以外で終わる行が版面の右端（本文の左端と
                              左右対称）まで1.2字ぶんも残さず、次の行へ続いている
       行の右端の近さだけでは判定しない。右揃えの表紙や、1行に2文を並べた行（規則で勧めている形）まで拾うため

仕組み: `pdftotext -bbox-layout` で行と語の座標を取り、次の場所で段落を分ける。
       行送りの開き（通常の1.3倍超）／行頭のずれ（0.5字超。中央揃えの図のラベルを外す）／
       行頭の左にある箇条書きの記号（画像で見る）／行と行の間の罫線や地色の切れ目（表の行・カードの境目）。
       語と語の間が2字以上空いた行は表の行として外す。見出し（上端70px以内）・フッター（下端40px）・
       デッキの標準の行送りの6割未満の小さい文字（図の注記・キャプション・表紙の注意書き）も対象外。
       同名の .md が無ければ「原稿に無い改行」の代わりに「右端まで伸びている」で見る（`--md` で別の原稿を渡せる）。
`--debug N` を付けると、N ページの段落ごとの測定値を出す（しきい値の調整用）。
"""
import _marp_pdf_guard  # noqa: F401  Speaker Deck 向けに拡大済みのPDFなら止める
import glob
import html
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path

from PIL import Image

W, H = 1280, 720
TOP, BOTTOM = 70, H - 40
PUNCT = set('、。，．,.！？!?）)」』】〕〉》"”’：:；;…')
SENT = set('、。，．！？!?')
TEXT_BULLET = re.compile(r'^\s*(?:[•・●○◦▪■□▶➤✓✔]|\d+[.)．）]\s|[①-⑳])')


def opt(name, default, cast=float):
    return cast(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def norm(s):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', s))


def parse(pdf):
    out = subprocess.run(['pdftotext', '-bbox-layout', pdf, '-'], capture_output=True, text=True, check=True).stdout
    num = r'"([\d.-]+)"'
    pages = []
    for pw, body in re.findall(r'<page width="([\d.]+)" height="[\d.]+">(.*?)</page>', out, re.S):
        s = W / float(pw)
        blocks = []
        for b in re.findall(r'<block [^>]*>(.*?)</block>', body, re.S):
            lines = []
            for m in re.finditer(rf'<line xMin={num} yMin={num} xMax={num} yMax={num}>(.*?)</line>', b, re.S):
                words = [(float(a) * s, float(c) * s, html.unescape(t)) for a, c, t in
                         re.findall(rf'<word xMin={num} yMin="[\d.-]+" xMax={num} yMax="[\d.-]+">(.*?)</word>', m.group(5), re.S)]
                x1, y1, x2, y2 = (float(v) * s for v in m.groups()[:4])
                lines.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'words': words,
                              'text': ' '.join(w[2] for w in words)})
            if lines:
                blocks.append(lines)
        pages.append(blocks)
    return pages


def md_code(md):
    """原稿のコードブロックの中身（空白を落とした平文）。"""
    t = md.read_text(encoding='utf-8')
    return norm(''.join(re.findall(r'```.*?\n(.*?)```', t, re.S)))


CODE_CHARS = re.compile(r'[{};=]|^\s*["\']|\)\s*;')


def md_flat(md):
    """原稿から「改行の位置」だけを残した平文を作る。改行と <br> は ¶、そのほかの空白と記法は落とす。"""
    t = md.read_text(encoding='utf-8')
    t = re.sub(r'<style.*?</style>', '', t, flags=re.S)
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'<br\s*/?>', '\n', t)
    t = re.sub(r'</?(p|div|li|h\d|tr|td|th)[^>]*>', '\n', t)
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'!?\[[^\]]*\]\([^)]*\)', '', t)
    t = re.sub(r'(?m)^\s*(?:[-*+]|\d+\.|#+|>)\s+', '', t)
    t = re.sub(r'[*_`|]', '', t)
    t = unicodedata.normalize('NFKC', html.unescape(t))
    return re.sub(r'[ \t　]+', '', t).replace('\n', '¶')


def differs(a, b, th=12):
    return max(abs(x - y) for x, y in zip(a, b)) > th


def bullet_left(px, ln, em):
    """行頭の左（1.6字ぶん）に記号のインクがあれば箇条書きの行とみなす。"""
    yc = int((ln['y1'] + ln['y2']) / 2)
    x_end = int(ln['x1']) - 3
    if x_end < 5:
        return False
    bg = px[x_end, yc]
    return any(differs(px[x, y], bg, 60) for x in range(max(0, int(ln['x1'] - em * 1.6)), x_end)
               for y in range(yc - int(em * 0.25), yc + int(em * 0.25) + 1))


def ruled_between(px, a, b, em):
    """2行のあいだに、行幅の8割以上にわたって地色と違う横一列（罫線・地色の切れ目）があるか。"""
    ya = int((a['y1'] + a['y2']) / 2 + em * 0.6)
    yb = int((b['y1'] + b['y2']) / 2 - em * 0.6)
    x0, x1 = int(max(a['x1'], b['x1'])), int(min(a['x2'], b['x2']))
    if yb <= ya or x1 - x0 < em:
        return False
    bg = px[x0, int((a['y1'] + a['y2']) / 2)]
    xs = range(x0, x1, 3)
    return any(sum(differs(px[x, y], bg) for x in xs) >= len(xs) * 0.8 for y in range(ya, yb))


def page_bg(px):
    """ページの地色（四隅の近くで最も多い色）。"""
    pts = [px[x, y] for x in (20, W // 2, W - 20) for y in (H // 3, H // 2)]
    return Counter(pts).most_common(1)[0][0]


def free_right(px, ln, right_margin, pg):
    """行末から右へ、行の地（箱の地を含む）とページの地以外のインクに当たるまでの位置。"""
    yc = int((ln['y1'] + ln['y2']) / 2)
    x0 = int(ln['x2']) + 4
    if x0 >= right_margin:
        return ln['x2']
    local = px[x0, yc]
    run = 0
    for x in range(x0, int(right_margin)):
        hit = any(differs(px[x, y], local, 40) and differs(px[x, y], pg, 40) for y in (yc - 4, yc, yc + 4))
        run = run + 1 if hit else 0
        if run >= 4:
            return x - 3
    return right_margin


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    pdf = Path(sys.argv[1])
    short_ratio, min_run, max_tail = opt('--short', 0.45), opt('--run', 3, int), opt('--tail', 6, int)
    mean_ratio, min_room = opt('--mean', 0.36), opt('--room', 1.5)
    debug = opt('--debug', 0, int)
    md = Path(sys.argv[sys.argv.index('--md') + 1]) if '--md' in sys.argv else pdf.with_suffix('.md')
    flat = md_flat(md) if md.exists() else None
    code = md_code(md) if md.exists() else ''

    pages = parse(str(pdf))
    body = [ln for blocks in pages for b in blocks for ln in b if TOP < ln['y1'] < BOTTOM]
    left = Counter(round(ln['x1'] / 4) * 4 for ln in body).most_common(1)[0][0] if body else 64
    right_margin = W - left
    body_w = right_margin - left
    pitches = [b['y1'] - a['y1'] for blocks in pages for bl in blocks for a, b in zip(bl, bl[1:])
               if TOP < a['y1'] < BOTTOM and 0 < b['y1'] - a['y1'] < 120]
    std_pitch = sorted(pitches)[len(pitches) // 2] if pitches else 50
    min_pitch = std_pitch * 0.6

    tmp = tempfile.mkdtemp()
    subprocess.run(['pdftoppm', '-png', '-scale-to-x', str(W), '-scale-to-y', str(H), str(pdf), os.path.join(tmp, 'p')],
                   check=True, stderr=subprocess.DEVNULL)
    imgs = sorted(glob.glob(os.path.join(tmp, 'p-*.png')))
    ng = 0; scanned = 0; md_checked = 0
    for no, blocks in enumerate(pages, 1):
        px = Image.open(imgs[no - 1]).convert('RGB').load()
        pg = page_bg(px)
        flags = []
        for block in blocks:
            lines = [ln for ln in block if TOP < ln['y1'] < BOTTOM]
            if len(lines) < 2:
                continue
            ps = sorted(b['y1'] - a['y1'] for a, b in zip(lines, lines[1:]) if b['y1'] > a['y1'])
            pitch = ps[len(ps) // 2] if ps else 0
            if pitch < min_pitch:
                continue  # 図の注記・キャプションなどの小さい文字
            em = pitch * 0.62
            # 語と語の間が2字以上空いた行は、表の行が1行に連結されたもの
            lines = [ln for ln in lines if not any(b[0] - a[1] > em * 2 for a, b in zip(ln['words'], ln['words'][1:]))]
            # コードの行（原稿のコードブロックにある行、記号の多い行）
            lines = [ln for ln in lines if not ((code and len(norm(ln['text'])) >= 4 and norm(ln['text']) in code)
                                                or CODE_CHARS.search(ln['text']))]
            paras, cur = [], []
            for ln in lines:
                if cur:
                    a = cur[-1]
                    p = ln['y1'] - a['y1']
                    if (p <= 0 or p > pitch * 1.3 or abs(ln['x1'] - a['x1']) > em * 0.5 or TEXT_BULLET.match(ln['text'])
                            or bullet_left(px, ln, em) or ruled_between(px, a, ln, em)):
                        paras.append(cur); cur = []
                cur.append(ln)
            if cur:
                paras.append(cur)
            for para in paras:
                scanned += len(para)
                if debug == no:
                    print(f"  段落 行送り{pitch:.0f}px: " + ' / '.join(
                        f"{round((l['x2'] - l['x1']) / body_w * 100)}%「{l['text'][:12]}」" for l in para))
                # ① 改行しすぎ
                run = []
                for ln in para + [None]:
                    if ln is not None and ln['x2'] - ln['x1'] < body_w * short_ratio:
                        run.append(ln); continue
                    if len(run) >= min_run:
                        mean = sum(r['x2'] - r['x1'] for r in run) / len(run) / body_w
                        room = (min(free_right(px, r, right_margin, pg) for r in run) - min(r['x1'] for r in run)
                                - max(r['x2'] - r['x1'] for r in run))
                        if debug == no:
                            print(f"    短い行{len(run)}行 平均{mean * 100:.0f}% 右の空き{room / em:.1f}字")
                        if mean < mean_ratio and room >= em * min_room:
                            widths = '/'.join(f"{round((r['x2'] - r['x1']) / body_w * 100)}%" for r in run)
                            flags.append(f"改行しすぎ：本文幅の{round(short_ratio * 100)}%に届かない行が{len(run)}行続く"
                                         f"（{widths}・平均{mean * 100:.0f}%）「{run[0]['text'][:16]}…」")
                    run = []
                # ② 改行の位置（段落の途中の行だけ）
                for ln, nxt in zip(para, para[1:]):
                    t, n = norm(ln['text']), norm(nxt['text'])
                    if not t or not n:
                        continue
                    cut = max((i for i, c in enumerate(t) if c in SENT), default=-1)
                    tail = t[cut + 1:] if cut >= 0 else ''
                    if 0 < len(tail) <= max_tail and t[-1] not in PUNCT:
                        flags.append(f"読点の後ろの切れ端：「…{t[max(0, cut - 8):]}」の「{tail}」だけ残して改行。"
                                     f"読点の直後で改行する（次の行「{n[:10]}…」）")
                        continue
                    if flat is not None and t[-1] not in PUNCT:
                        a, b = t[-6:], n[:4]
                        if a + '¶' + b in flat or a + b in flat:
                            md_checked += 1
                        if a + b in flat and a + '¶' + b not in flat:
                            flags.append(f"原稿に無い改行：「…{t[-12:]}／{n[:8]}…」はブラウザの自動折り返しで切れている。"
                                         f"意味の切れ目で改行を入れる")
                            continue
                # ② 右端まで伸びている（原稿が無いときの代わり。段落の途中で、句読点以外で切れた行）
                if flat is None:
                    for ln, nxt in zip(para, para[1:]):
                        t = norm(ln['text'])
                        if not t or t[-1] in PUNCT or any(t[-6:] in f for f in flags):
                            continue
                        cw = (ln['x2'] - ln['x1']) / max(1, sum(0.55 if ord(c) < 0x2000 else 1 for c in t))
                        gap = right_margin - ln['x2']
                        if gap < cw * 1.2:
                            flags.append(f"右端まで伸びている：「…{t[-12:]}」が版面の右端まで{max(gap, 0):.0f}px（1字ぶん未満）で"
                                         f"次の行「{norm(nxt['text'])[:8]}…」へ続く。意味の切れ目で改行する")
        if flags:
            ng += 1
            print(f'NG p{no}')
            for f in flags:
                print(f'   {f}')
    src = f'原稿 {md.name} と照合' if flat is not None else '原稿なし（自動折り返しは右端の近さで代用）'
    print(f'{len(pages)} ページ・本文 {scanned} 行を走査、NG {ng} ページ'
          f'（本文の左端 {left}px・本文幅 {body_w}px・標準の行送り {std_pitch:.0f}px・{src}・改行を原稿で照合 {md_checked} 件）')
    sys.exit(1 if ng else 0)


if __name__ == '__main__':
    main()
