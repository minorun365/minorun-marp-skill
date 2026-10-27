#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["pypdf"]
# ///
"""Marp の PDF を、Speaker Deck 向けの寸法（ページ寸法2倍）にその場で置き換える。

Speaker Deck は PDF を 1920×1080 の JPEG に焼き直して配信するが、そのとき埋め込み画像
（スクショ・写真）だけが文字より粗くなる。Marp の PDF は 960×540pt なので、ページ寸法を
引き伸ばして画像に割り当てられる解像度を増やす。中身（文字のベクター・画像のピクセル）は
一切変えない。2倍で改善するが、完全には元の画質に戻らない。

書き出しの最後の工程として、検査（check-*.py）を通したあとに打つ。検査は 960×540pt の
座標を前提にしているので、置き換え後の PDF は検査できない（各検査が止まる）。

    uv run tools/pdf-for-speakerdeck.py deck.pdf
    uv run tools/pdf-for-speakerdeck.py deck.pdf --scale 3

すでに拡大済みの PDF を渡したときは何もしない。
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter

MARP_WIDTH_PT = 960


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--scale", type=float, default=2.0)
    args = ap.parse_args()

    src = args.pdf.resolve()
    if not src.is_file():
        print(f"PDF が見つかりません: {src}", file=sys.stderr)
        return 1

    reader = PdfReader(src)
    width = float(reader.pages[0].mediabox.width)
    if width > MARP_WIDTH_PT + 1:
        print(f"{src}\n  すでに {width:.0f}pt 幅に拡大済みなので、そのままにしました")
        return 0

    writer = PdfWriter()
    for page in reader.pages:
        page.scale_by(args.scale)
        writer.add_page(page)
    with tempfile.NamedTemporaryFile(dir=src.parent, suffix=".pdf", delete=False) as tmp:
        writer.write(tmp)
    tmp_path = Path(tmp.name)

    out = PdfReader(tmp_path)
    if len(out.pages) != len(reader.pages):
        tmp_path.unlink()
        print("ページ数が元と一致しないので、置き換えずに止めました", file=sys.stderr)
        return 1
    tmp_path.replace(src)
    box = out.pages[0].mediabox
    print(f"{src}\n  {len(out.pages)}ページ / {float(box.width):.0f}×{float(box.height):.0f}pt（{args.scale:g}倍）に置き換えました")
    return 0


if __name__ == "__main__":
    sys.exit(main())
