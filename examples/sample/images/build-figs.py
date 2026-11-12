"""見本デッキの図を、黒地テーマの部品で描く。新しいデッキでは、このファイルを写して図の中身だけ書き換える。

    python3 images/build-figs.py   （デッキのフォルダで実行）

図の部品:
  - 主役の箱   テーマ色を暗く落とした面（#00849c）に白の太字。1枚の図で1か所か、同じ重さの工程の並び
  - 脇役の箱   濃い灰色の面（#1f1f27）に白の文字。縁取りの線は引かない
  - 方向の面   矢印や広がりを表す大きな面は、黒よりわずかに明るい灰色（#2a2a33）で塗る
  - 線・矢印   明るいテーマ色（#7fe3f5）。矢じりは実寸 18px
  - ラベル     箱が何であるかの名前は、箱の外の上に灰色の小さい文字で置く
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONT = "'Zen Maru Gothic','Hiragino Maru Gothic ProN',sans-serif"
MAIN, TILE, SOFT, LINE, GRAY = "#00849c", "#1f1f27", "#2a2a33", "#7fe3f5", "#a09aa4"


def svg(viewbox, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" font-family="{FONT}">
<defs>
  <marker id="arw" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" refX="16" refY="9" orient="auto">
    <path d="M0 0L18 9L0 18z" fill="{LINE}"/>
  </marker>
</defs>
{body}
</svg>
"""


def box(x, y, w, h, fill, rx=18):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"/>'


def text(x, y, s, size, fill="#ffffff", bold=False, anchor="middle"):
    b = ' font-weight="700"' if bold else ""
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" fill="{fill}"{b}>{s}</text>'


def line(x1, y1, x2, y2):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{LINE}" stroke-width="4" marker-end="url(#arw)"/>'


def write(name, content):
    (HERE / f"{name}.svg").write_text(content, encoding="utf-8")
    print("wrote", name)


# 1. 3つの工程。最後の「測って、見る」だけを主役の色にする。箱の下に、その工程で何をするかを灰色で添える
steps = [("話を決める", "疑問の順に並べる"), ("書き出す", "テーマの部品で組む"), ("測って、見る", "測ってから目で見る")]
BW, BH, GAP, Y = 250, 110, 105, 20
parts = []
for i, (s, sub) in enumerate(steps):
    x = 20 + i * (BW + GAP)
    last = i == len(steps) - 1
    parts.append(box(x, Y, BW, BH, MAIN if last else TILE))
    parts.append(text(x + BW / 2, Y + BH / 2 + 11, s, 32, bold=last))
    parts.append(text(x + BW / 2, Y + BH + 52, sub, 22, fill=GRAY))
    if not last:
        parts.append(line(x + BW + 16, Y + BH / 2, x + BW + GAP - 16, Y + BH / 2))
write("flow", svg("0 0 1000 210", "\n".join(parts)))

# 2. 直す前と直したあと。左は脇役の箱、右は主役の色。あいだの大きな矢印は方向の面
before = ["概念の定義から始まる", "全ページが同じ形", "図の文字が小さい"]
after = ["聞き手の疑問の順に開く", "1枚に1つのメッセージ", "図の文字は16pt以上"]
W, CW, RH, RG, TOP = 1000, 380, 72, 22, 60
parts = [text(20 + CW / 2, 34, "AIに任せたまま", 28, fill=GRAY),
         text(W - 20 - CW / 2, 34, "直したあと", 28, fill=LINE, bold=True)]
for i, (b, a) in enumerate(zip(before, after)):
    y = TOP + i * (RH + RG)
    parts += [box(20, y, CW, RH, TILE), text(20 + CW / 2, y + RH / 2 + 9, b, 26),
              box(W - 20 - CW, y, CW, RH, MAIN), text(W - 20 - CW / 2, y + RH / 2 + 9, a, 26, bold=True)]
cy, ax0, ax1 = TOP + (3 * RH + 2 * RG) / 2, 20 + CW + 28, W - 20 - CW - 28
parts.append(f'<path d="M{ax0} {cy-34} H{ax1-46} V{cy-58} L{ax1} {cy} L{ax1-46} {cy+58} V{cy+34} H{ax0} Z" fill="{SOFT}"/>')
write("before-after", svg(f"0 0 {W} {TOP + 3 * RH + 2 * RG + 20}", "\n".join(parts)))
