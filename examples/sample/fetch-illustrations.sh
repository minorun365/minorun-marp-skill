#!/bin/sh
# 見本デッキの挿絵を「いらすとや」から取得する。画像はこのリポジトリに同梱していない。
# 利用条件は https://www.irasutoya.com/p/terms.html を確かめてください。
set -e
cd "$(dirname "$0")/images"
B=https://blogger.googleusercontent.com/img/b/R29vZ2xl
# 複雑なプレゼンのスライドのイラスト https://www.irasutoya.com/2018/06/blog-post_268.html
curl -sL -o irasutoya-complex-slide.png "$B/AVvXsEgUwzKFVlD9tqKIbFZnu0yIr62hGUEy_OdRUBNVAhAymJbvxmdguqefWb02FWVUUnuQbyfUp_T6ZX7i0uLXoghLSXuL_INF6yYVIZlM6eofPb-MzKh_uQvNyCzGmYV3_CcrFbdCeybRkPpw/s800/presentation_slide_fukuzatsu.png"
# 説明会・セミナーのイラスト（女性） https://www.irasutoya.com/2016/04/blog-post_37.html
curl -sL -o irasutoya-seminar.png "$B/AVvXsEiba1yRJ5eRxl8YVvAOLkGLVoIh0jZkp0xmJtSYT6jszzblzaaTsjuskCZieKBYeww-g-SUtK7kJFptaI_eS39PQtBiLWvtjpkjL0CSh6VRLA3XG1p1C6ZMesZhJbE1ouqlDzv9JVofNK7Y/s800/seminor_woman.png"
# 虫眼鏡を持つ女性会社員のイラスト https://www.irasutoya.com/2015/03/blog-post_87.html
curl -sL -o irasutoya-magnifier.png "$B/AVvXsEjWjiCYQzco9g91IMDbyUM4LYAOmYcdVTeQASBDrAPoT7ZYTfvIaOjIWNF8qv36sCm0EbcKyIk4WmpxA45asqEkeqXP1HCz0xCqv3WUy5vxsNZS_WfdpU65GohhvdqZWbgRqfle8ym-nJ7O/s800/magnifier4_woman.png"
ls -l irasutoya-*.png
