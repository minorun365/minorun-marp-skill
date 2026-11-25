# minorun-marp-skill

登壇スライドを Marp で作るときのストーリー・図・デザインバランスの型をまとめたものです。Claude Code などのAIエージェントに読ませるスキルの形にしてあり、人が読んでもそのまま使えます。

AIにスライドを書かせると、体裁は整うのに話が薄くなりがちです。作者の [@minorun365](https://x.com/minorun365) が自分の登壇資料を作るなかでエージェントへ繰り返し伝えてきた直し方を、規則と検査スクリプトにしました。

<picture>
  <source media="(max-width: 767px)" srcset="examples/sample/preview-sp.png">
  <img src="examples/sample/preview.png" alt="見本デッキ">
</picture>

## 中身

| 場所 | 内容 |
|---|---|
| `skills/slide-story` | つかみ、中扉、段階的な開示、見出しの文体、締め方、尺の見積り |
| `skills/slide-figures` | 図の情報量の絞り方、SVGの描き方、文字サイズの下限、挿絵の置き方 |
| `skills/slide-design-dark` | 余白の測り方、縦のバランス、黒地の配色、表とコードのデザイン、Marpの罠 |
| `theme/minorun-dark.css` | 黒地にシアンの Marp テーマ |
| `tools/` | 書き出したPDFとSVGを実測する検査スクリプト |
| `examples/sample` | 見本デッキ。図は `images/build-figs.py` で部品から描く。README の一覧画像は `build-preview.py` で作る。`examples/broken` は検査が反応することを確かめるために、わざと崩した版 |

## 入れ方

Claude デスクトップアプリの「Code」タブか Claude Code で、このURLを渡して頼むだけです。

> https://github.com/minorun365/minorun-marp-skill のスキルを入れて

入れ終わったら新しいセッションを始め、「黒地のテーマで、勉強会の20分のスライドを作って」のように頼めば使えます。新しい版が出たときは「minorun-marp-skill を最新にして」で更新できます。

## インストールを頼まれた Claude へ

この節は Claude が読むための手順です。自分で入れる場合も、この順に進められます。

1. リポジトリを `~/.claude/skill-repos/minorun-marp-skill` へ置く。無ければ `git clone` し、あれば `git pull` する
2. `skills/` にある `slide-story`、`slide-figures`、`slide-design-dark` の3つを `~/.claude/skills/` へコピーする。同じ名前があれば上書きする
3. 書き出しと検査に使うツールが入っているか確かめ、無いものを入れる。必要なのは [Marp CLI](https://github.com/marp-team/marp-cli)、Google Chrome、poppler、mupdf-tools、Python 3、Pillow で、Marp CLI は `npm i -g @marp-team/marp-cli`、poppler と mupdf-tools は macOS なら `brew install poppler mupdf-tools` で入れられる。`check-svg-box-fit.mjs`・`check-svg-spacing.mjs`・`check-svg-contrast.mjs` は Marp CLI 同梱の puppeteer-core を使うので、場所が違う環境では `MARP_NODE_MODULES` と `CHROME_PATH` で指定する
4. 結果は、コマンドを見せずに、何が使えるようになったかと頼み方の例を平易な言葉で伝える

スライドを作るときは、`~/.claude/skill-repos/minorun-marp-skill` から `theme/` と `tools/` を作業フォルダへコピーして使う。

```bash
marp --no-stdin deck.md --pdf --theme theme/minorun-dark.css --allow-local-files

python3 tools/check-dark-margins.py deck.pdf    # 中身の下端と右端の空き
python3 tools/check-dark-gaps.py deck.pdf       # 図や箱と、隣の本文の間隔
python3 tools/check-figure-text.py deck.pdf     # 図の中の小さい文字、箱の縁に詰まった文字
python3 tools/check-line-breaks.py deck.pdf     # 改行のしすぎと、読点の後ろの切れ端
python3 tools/check-bubble-tails.py deck.md     # 吹き出しのしっぽの継ぎ目に線が出る書き方
node tools/check-svg-box-fit.mjs images/*.svg   # SVGの文字が箱に収まっているか
node tools/check-svg-spacing.mjs images/*.svg  # SVGの箱や行、線と文字の間隔が詰まっていないか
node tools/check-svg-contrast.mjs images/*.svg  # SVGの図形が下の面と同じ色で沈んでいないか
python3 tools/check-reuse-diff.py new.md old.md # 流用したスライドの、見出しと図の対応
python3 tools/check-ai-smell.py deck.md         # 書き換えたスライドの文の型の反復
```

検査を通したら、Speaker Deck の変換でスクリーンショットや写真だけが文字より粗くなるのを和らげるため、最後に PDF のページ寸法を2倍にしたものへ置き換える。置き換える前に元と変換後の全ページを画像で見比べ、見た目が変わったページがあれば置き換えずに中断する。検査は置き換え前の寸法を前提にしているので、置き換えた PDF を渡すと止まる。

```bash
uv run tools/pdf-for-speakerdeck.py deck.pdf
```

## フォント

テーマは丸ゴシック系を想定しています。第一候補の Zen Maru Gothic を入れておくと揃い、入っていない macOS ではヒラギノ丸ゴで表示されます。作者の手元では有償の丸ゴシック書体を使っているので、公開されている登壇資料とは字形が少し違います。

## 挿絵について

作者のスライドには「いらすとや」の挿絵がよく登場します。画像はこのリポジトリに同梱していないため、見本デッキを書き出す前に取得する必要があります。利用条件は各自で確かめてください。

```bash
sh examples/sample/fetch-illustrations.sh
```

## License

Apache License 2.0. Copyright 2026 Minoru Onda

見本デッキの一覧画像に写っている挿絵は「いらすとや」の著作物で、このライセンスの対象外です。
