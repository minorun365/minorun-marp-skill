#!/usr/bin/env python3
"""スライド原稿のうち、書き換えたスライドだけに「機械が書いた文」の型を当てる。

デッキ全体へ当てると、話し手が自分で書いた既存のスライドまで大量に引っかかり、検査が使われなくなる。
そこで git の HEAD 版と比べ、変わったスライドだけを見る。新しく書いた文に毎回当たるので、
「指摘された箇所は直したが、新しく書き足した文で同じ型が再発する」を止められる。

    python3 tools/check-ai-smell.py deck.md          # HEAD から変わったスライドだけ
    python3 tools/check-ai-smell.py deck.md --all    # 全スライド（新しいデッキ用）

NG が1件でもあれば終了コード1を返す。
"""
import re
import subprocess
import sys
from pathlib import Path

# (名前, 正規表現, 直し方)
PATTERNS = [
    ("キメ構文", r"のは、|のが、", "「〜のは◯◯です」。主語を先頭へ戻して普通の文にする"),
    ("決め台詞", r"これが[^。]{0,20}です|それが[^。]{0,20}です", "「これが〜です」。抽象名詞で包み直さず、具体のまま終える"),
    ("過大な効能", r"だけで[^。]{0,20}ます|やすくなります|やすくなる", "「これだけで〜できます」型。具体的な結果に置き換える"),
    ("終助詞", r"ですよね|ますよね|でしょうね", "地の文に終助詞を置かない"),
    ("見出しの読点タメ", r"^#+ .{1,18}は、", "見出しを「〜は、〜」でためない。読点を外すか普通の一文にする"),
    ("ダッシュ", r"—|──|―", "使わない。読点か文の分割にする"),
    ("定番の誇張語", r"一気に|驚くほど|劇的に|目に見えて|一撃で|腑に落ち", "平明な語に言い換える"),
    ("行頭の太字ラベル", r"^\s*[-*] \*\*", "箇条書きごと地の文へ戻す"),
]


def slides(text):
    return text.split("\n---\n")


def visible(block):
    """CSS・HTMLタグ・コメントを落として、画面に出る文字だけにする。"""
    b = re.sub(r"<style scoped>.*?</style>", "", block, flags=re.S)
    b = re.sub(r"<!--.*?-->", "", b, flags=re.S)
    b = re.sub(r"<[^>]+>", "", b)
    return [ln.rstrip() for ln in b.split("\n") if ln.strip()]


def bullet_monotony(lines):
    """箇条書きが3行以上続き、全部に読点が入っていたら型の反復とみなす。"""
    run = []
    for ln in lines:
        if re.match(r"^\s*[-*] ", ln):
            run.append(ln)
        else:
            if len(run) >= 3 and all("、" in x for x in run):
                return run
            run = []
    if len(run) >= 3 and all("、" in x for x in run):
        return run
    return None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check_all = "--all" in sys.argv
    if not args:
        print(__doc__)
        return 2
    path = Path(args[0])
    now = slides(path.read_text(encoding="utf-8"))

    targets = list(range(1, len(now)))
    if not check_all:
        repo = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                              text=True, cwd=path.resolve().parent).stdout.strip()
        old = None
        if repo:
            rel = path.resolve().relative_to(repo).as_posix()
            old = subprocess.run(["git", "show", f"HEAD:{rel}"], capture_output=True, text=True, cwd=repo)
        if old is not None and old.returncode == 0:
            before = set(slides(old.stdout))
            targets = [i for i in range(1, len(now)) if now[i] not in before]
            print(f"HEAD と比べて変わったスライド: {len(targets)}"
                  f"{'（' + ', '.join('p%d' % i for i in targets) + '）' if targets else ''}")
        else:
            print("git の HEAD に無いファイルなので、全スライドを見る")

    ng = 0
    for i in targets:
        lines = visible(now[i])
        for ln in lines:
            for name, pat, fix in PATTERNS:
                if re.search(pat, ln):
                    print(f"NG p{i} [{name}] {ln.strip()[:60]}\n      → {fix}")
                    ng += 1
        # 短く言い切って、次の文を指示語で受ける「タメ」
        for j in range(len(lines) - 1):
            cur, nxt = lines[j].strip(), lines[j + 1].strip()
            if re.search(r"[うくすつぬむるい]。$", cur) and len(cur) <= 26 \
               and re.match(r"^(そういう|こういう|そんな|こんな|これ|それ|その)", nxt):
                print(f"NG p{i} [言い切りのタメ] {cur} → {nxt[:24]}\n"
                      f"      → 1文につなげる。短く切って次の文を指示語で受けない")
                ng += 1
        cond = [ln for ln in lines if re.search(r"(と|ば|たら|なら|ので|ため|して)、", ln)]
        if len(cond) >= 3:
            print(f"NG p{i} [型の反復] 「条件＋読点＋帰結」の文が{len(cond)}つ\n"
                  f"      → 言い切り・体言止め・問いかけを混ぜる: " + " / ".join(x.strip()[:22] for x in cond[:3]))
            ng += 1
        run = bullet_monotony(lines)
        if run:
            print(f"NG p{i} [型の反復] 箇条書き{len(run)}行が全部「〜、〜」で同じ拍\n"
                  f"      → 1行は読点なしにするなど、形を混ぜる")
            ng += 1

    print(f"\n{len(targets)} スライド走査、NG {ng} 件" if ng else
          f"\nOK: {len(targets)} スライド走査、型は見つからなかった")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main())
