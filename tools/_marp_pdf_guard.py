"""検査スクリプトに渡された PDF が、Speaker Deck 向けに拡大済みでないかを確かめる。

検査は Marp の書き出しそのまま（960×540pt）の座標を前提にしている。pdf-for-speakerdeck.py で
寸法を拡大した PDF を渡すと、エラーにならずに誤った結果を返すので、import した時点で止める。
"""

import re
import subprocess
import sys

MARP_WIDTH_PT = 960

for arg in sys.argv[1:]:
    if not arg.lower().endswith(".pdf"):
        continue
    info = subprocess.run(["pdfinfo", arg], capture_output=True, text=True).stdout
    m = re.search(r"Page size:\s+([\d.]+) x", info)
    if m and float(m.group(1)) > MARP_WIDTH_PT + 1:
        print(
            f"{arg} は Speaker Deck 向けに拡大済み（{float(m.group(1)):.0f}pt 幅）なので検査できません。\n"
            "marp で書き出し直してから検査し、最後に tools/pdf-for-speakerdeck.py を通してください。",
            file=sys.stderr,
        )
        sys.exit(2)
