# TabScript

[![Tests](https://github.com/ashitani/tabscript/actions/workflows/tests.yml/badge.svg)](https://github.com/ashitani/tabscript/actions/workflows/tests.yml)
![Python Versions](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)

TabScriptは、ギターやベースのタブ譜を記述するためのシンプルなテキスト形式の言語です。

このレポジトリはTabscript言語の仕様と、処理系としてtabscriptという名称のPythonパッケージを提供します。

## TabScriptサンプル

```
5-1 4-2 3-3 2-4
```
という文字列を下記のようなpdfに変換できます。

![images/hello_world.png](images/hello_world.png)

TabScript言語の記法の詳細については[docs/format.md](docs/format.md)を参照してください。

## インストール

```bash
# PyPIからインストール (未実装)
# pip install tabscript

# ソースからインストール
git clone https://github.com/ashtiani/tabscript.git
cd tabscript
pip install .
```

## 使い方

### コマンドラインツール

```bash
# PDFとして出力
tab2pdf score.tab
tab2pdf tabs/*.tab   # 複数ファイルの一括処理

# オプション
tab2pdf --debug score.tab  # デバッグ出力を有効化
tab2pdf --debug-level 2 score.tab  # デバッグレベルを指定（1: basic, 2: detailed, 3: verbose）
tab2pdf --show-length score.tab  # 音価（三連符を含む）を表示
```

### Pythonコードでの使用

```python
import tabscript as ts

# TabScriptファイルのパース
parser = ts.parser()
parser.parse("path/to/your/score.tab")

# PDFとして出力
parser.render_score("output.pdf")
```


## 開発者向け情報

開発への参加方法、テスト方法、コーディング規約などについては[docs/development.md](docs/development.md)を参照してください。

## Todo
- ✅繰り返し
- DS、Coda
- ✅行末コメント対応
- ✅三連符
- 音価の表記（--show-lengthオプションで制御可能）
- 各種奏法（ハンマリング、プリング、スライド、チョーキング）
- ✅改ページ
- ✅VSCode extention(とりあえずpdfプレビューと簡単なシンタックスハイライトのみ)
- HTML5+JS
- pypi

## ライセンス

MIT License
