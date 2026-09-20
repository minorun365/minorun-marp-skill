#!/usr/bin/env python3
"""流用元デッキと、見出しごとの画像の対応を突き合わせる。

過去のデッキから定番の枚を持ってきたとき、図の対応が入れ替わっていないかを機械で確かめる。
見出しは合っているのに図が別の枚のもの、という取り違えは縮小画像の目視では判別できない。

使い方:
  python3 tools/check-reuse-diff.py "<新デッキ>.md" "<流用元デッキ>.md" [<流用元2>.md ...]

同じ見出し（h1。<br> は無視）を持つ枚について、参照している images/ のファイル名を並べ、
違うものだけを出す。ファイル名が違うだけで中身が同じ（-dark 無し版など）ケースは人が見て
判断する。出力が0件でも「同じ」ではなく、見出しが違う枚は照合していない。
"""
import io, re, sys

def deck(path):
    blocks = io.open(path, encoding="utf-8").read().split("\n---\n")
    out = {}
    for b in blocks[1:]:
        m = re.search(r"^# (.+)$", b, re.M)
        if not m:
            continue
        title = re.sub(r"<br>", "", m.group(1)).strip()
        imgs = re.findall(r'(?:!\[[^\]]*\]\(|src=")\./images/([^")]+)', b)
        out.setdefault(title, imgs)
    return out

def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    new = deck(sys.argv[1])
    diffs = shared = 0
    for src_path in sys.argv[2:]:
        src = deck(src_path)
        name = src_path.rsplit("/", 1)[-1].removesuffix(".md")
        for title, imgs in new.items():
            if title not in src:
                continue
            shared += 1
            if (imgs or src[title]) and imgs != src[title]:
                diffs += 1
                print(f"[{name}] {title}\n   新={imgs}\n   元={src[title]}")
    print(f"照合した枚: {shared} / 画像が違う枚: {diffs}")

if __name__ == "__main__":
    main()
