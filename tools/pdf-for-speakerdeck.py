#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["pikepdf", "pillow"]
# ///
"""Marp の PDF を、Speaker Deck 向けの寸法（ページ寸法2倍）にその場で置き換える。

Speaker Deck は PDF を 1920×1080 の JPEG に焼き直して配信するが、そのとき埋め込み画像
（スクショ・写真）だけが文字より粗くなる。Marp の PDF は 960×540pt なので、ページ寸法を
引き伸ばして画像に割り当てられる解像度を増やす。2倍で改善を確認した
（完全には直らない）。

拡大は、元のページを丸ごと部品（Form XObject）にして2倍で貼る方式で行う。描画命令に
拡大を足すだけの方式（pypdf の scale_by）は、グラデーション（SVG・CSS の gradient）の
座標が元の寸法のまま残り、色の位置がずれる。

置き換える前に、元と変換後を同じ画素数で画像にして全ページを比べ、見た目が変わった
ページが1枚でもあれば置き換えずに止める。

書き出しの最後の工程として、検査（check-*.py）を通したあとに打つ。検査は 960×540pt の
座標を前提にしているので、置き換え後の PDF は検査できない（各検査が止まる）。

    uv run tools/pdf-for-speakerdeck.py deck.pdf
    uv run tools/pdf-for-speakerdeck.py deck.pdf --scale 3

すでに拡大済みの PDF を渡したときは何もしない。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import pikepdf
from PIL import Image, ImageChops

MARP_WIDTH_PT = 960
COMPARE_WIDTH_PX = 640   # 見比べるときの画像の幅
MAX_DIFF = 12            # 0〜255 の色差。これを超える画素が出たページは「変わった」とみなす
MAX_DIFF_RATIO = 0.002   # ページの画素のうち、色差の大きい画素がこの割合を超えたら止める


def scale_pdf(src: Path, dst: Path, scale: float) -> int:
    with pikepdf.open(src) as pdf:
        out = pikepdf.new()
        for page in pdf.pages:
            box = page.mediabox
            w, h = float(box[2]) - float(box[0]), float(box[3]) - float(box[1])
            form = out.copy_foreign(page.as_form_xobject())
            new = out.add_blank_page(page_size=(w * scale, h * scale))
            new.add_overlay(form, pikepdf.Rectangle(0, 0, w * scale, h * scale))
        out.save(dst)
        return len(out.pages)


def render(pdf: Path, outdir: Path, prefix: str) -> list[Path]:
    subprocess.run(
        ["pdftoppm", "-png", "-scale-to", str(COMPARE_WIDTH_PX), str(pdf), str(outdir / prefix)],
        check=True,
    )
    return sorted(outdir.glob(f"{prefix}-*.png"))


def changed_pages(src: Path, dst: Path) -> list[tuple[int, float]]:
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        before, after = render(src, d, "a"), render(dst, d, "b")
        if len(before) != len(after):
            return [(0, 1.0)]
        bad = []
        for i, (a, b) in enumerate(zip(before, after), start=1):
            ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
            if ia.size != ib.size:
                ib = ib.resize(ia.size)
            diff = ImageChops.difference(ia, ib).convert("L")
            hist = diff.histogram()
            ratio = sum(hist[MAX_DIFF + 1:]) / (ia.width * ia.height)
            if ratio > MAX_DIFF_RATIO:
                bad.append((i, ratio))
        return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--scale", type=float, default=2.0)
    args = ap.parse_args()

    src = args.pdf.resolve()
    if not src.is_file():
        print(f"PDF が見つかりません: {src}", file=sys.stderr)
        return 1

    with pikepdf.open(src) as pdf:
        box = pdf.pages[0].mediabox
        width = float(box[2]) - float(box[0])
        height = float(box[3]) - float(box[1])
        n_src = len(pdf.pages)
    if width > MARP_WIDTH_PT + 1:
        print(f"{src}\n  すでに {width:.0f}pt 幅に拡大済みなので、そのままにしました")
        return 0

    with tempfile.NamedTemporaryFile(dir=src.parent, suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    n_out = scale_pdf(src, tmp_path, args.scale)
    if n_out != n_src:
        tmp_path.unlink()
        print("ページ数が元と一致しないので、置き換えずに止めました", file=sys.stderr)
        return 1

    bad = changed_pages(src, tmp_path)
    if bad:
        tmp_path.unlink()
        pages = "、".join(f"{p}枚目（{r:.1%}）" for p, r in bad[:10])
        print(f"変換の前後で見た目が変わったページがあるので、置き換えずに止めました: {pages}", file=sys.stderr)
        return 1

    tmp_path.replace(src)
    print(f"{src}\n  {n_out}ページ / {width * args.scale:.0f}×{height * args.scale:.0f}pt（{args.scale:g}倍）に置き換えました。全ページの見た目が元と一致することを確認済み")
    return 0


if __name__ == "__main__":
    sys.exit(main())
