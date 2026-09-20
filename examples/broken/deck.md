---
marp: true
paginate: true
theme: minorun-dark
---

<style>
.win { position:relative; border-radius:18px; margin:8px 0 28px; padding:22px 0 4px; overflow:hidden;
  background:linear-gradient(165deg, rgba(255,255,255,.10) 0%, rgba(255,255,255,.045) 100%);
  border:1px solid rgba(255,255,255,.14); box-shadow:0 18px 44px rgba(0,0,0,.45); }
.win::before { content:""; position:absolute; left:0; right:0; top:0; height:3px;
  background:linear-gradient(90deg, #00c4e4 0%, #7fe3f5 45%, rgba(127,227,245,0) 100%); }
.win pre { background:transparent !important; box-shadow:none; margin:0; padding:0 28px 16px; font-size:21.5pt; line-height:1.3; }
.win pre code { color:#f2f1f5; background:transparent; }
table { display:table !important; width:100%; border-collapse:collapse !important; background:transparent !important; border:none !important; font-size:22pt; }
table thead, table tbody, table tr { background:transparent !important; border:none !important; }
table th { background:transparent !important; color:#a09aa4 !important; font-weight:600; font-size:18pt;
  text-align:left; padding:0 .7em .55em; border:none !important; border-bottom:1px solid #3a3640 !important; }
table td { background:transparent !important; color:#b5b0ba !important; padding:.5em .7em; white-space:nowrap;
  border:none !important; border-bottom:1px solid #221f28 !important; }
table tr:last-child td { border-bottom:none !important; }
table td:first-child { color:#ffffff !important; font-weight:700; }
img { display:block; margin:0 auto; }
</style>

<!-- _class: top -->
<!-- _paginate: false -->

# AIに作らせたスライド、<br>なぜか薄くなる問題

<br><br>

サンプルデッキ

---

<!-- _class: crosshead -->

# AIにスライドを作らせたこと、<br>ありますか？

---

<!-- _class: crosshead -->

# そのまま登壇に使えましたか？

---

# こうなりがち

- 全ページが「見出し＋カード3枚」の同じ形
- 見出しが全部、同じ長さの体言止め
- 図の文字が小さくて、後ろの席から読めない

体裁は整っているのに、話が頭に残りません

---

<!-- _class: crosshead -->

# じゃあ、どこを直せばいいの？

---

# 直すのは3か所だけ

図のすぐ上に本文を置きます
![w:1000](./images/flow-bad.svg)

---

# 話の順番は、聞き手の疑問の順番

- 概念の定義から始めない
- 中扉には、聞き手の心の声を書く
- 答えは先に出さず、1スライドずつ開く

アジェンダも、まとめも作りません

---

# 見た目は目分量で決めない

| 測るもの | 下限 |
| --- | --- |
| 図の中の文字 | 16pt |
| 文字と箱の縁 | 14px |
| 図と本文の間隔 | 36px |
| 中身とスライド下端 | 60px |
| あ | 1 |
| い | 2 |
| う | 3 |
| え | 4 |
| お | 5 |

---

# 書き出したら、検査をまとめて通す

<div class="win">

```bash
marp --no-stdin deck.md --pdf --allow-local-files
python3 tools/check-dark-margins.py deck.pdf
python3 tools/check-dark-gaps.py deck.pdf
python3 tools/check-figure-text.py deck.pdf
```

</div>

---

# …検査が通れば完成！ではないんです

- 検査が測れるのは、描かれた要素だけ
- 矢印が消えた図は、全部OKで通ってしまう
- 最後は全ページを画像にして、<strong>自分の目で見る</strong>

---

<!-- _class: crosshead -->

# まずは手元の1本を、<br>測るところから始めてみませんか？
