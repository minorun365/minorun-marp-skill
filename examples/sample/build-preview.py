# /// script
# dependencies = ["pillow"]
# ///
"""見本デッキのPDFから、README に載せる一覧画像を作る。

PC用（preview.png）は横4列、スマホ用（preview-sp.png）は1列。
README は <picture> で画面幅に応じてどちらかを出す。

    uv run examples/sample/build-preview.py
"""
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
BG = (42, 42, 49)

# (出力名, 列数, 1枚の幅, 外周の余白, 間隔)
LAYOUTS = [
    ("preview.png", 4, 480, 5, 10),
    ("preview-sp.png", 1, 960, 16, 24),
]


def render_pages(pdf: Path, width: int, outdir: Path) -> list[Path]:
    height = width * 9 // 16
    prefix = outdir / f"w{width}"
    subprocess.run(
        ["pdftoppm", "-png", "-scale-to-x", str(width), "-scale-to-y", str(height),
         str(pdf), str(prefix)],
        check=True,
    )
    return sorted(outdir.glob(f"w{width}-*.png"))


def main() -> None:
    pdf = HERE / "deck.pdf"
    with tempfile.TemporaryDirectory() as tmp:
        for name, cols, tile_w, margin, gap in LAYOUTS:
            pages = render_pages(pdf, tile_w, Path(tmp))
            tile_h = tile_w * 9 // 16
            rows = -(-len(pages) // cols)
            w = margin * 2 + cols * tile_w + (cols - 1) * gap
            h = margin * 2 + rows * tile_h + (rows - 1) * gap
            sheet = Image.new("RGB", (w, h), BG)
            for i, page in enumerate(pages):
                r, c = divmod(i, cols)
                with Image.open(page) as im:
                    sheet.paste(im.convert("RGB"),
                                (margin + c * (tile_w + gap), margin + r * (tile_h + gap)))
            out = HERE / name
            sheet.save(out, optimize=True)
            print(f"{out.name}: {w}x{h}, {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
