# TabScript

[![Tests](https://github.com/ashitani/tabscript/actions/workflows/tests.yml/badge.svg)](https://github.com/yourusername/tabscript/actions/workflows/tests.yml)

TabScriptは、ギターやベースのタブ譜を記述するためのシンプルなテキスト形式の言語です。

このレポジトリはTabscript言語の仕様と、処理系としてtabscriptという名称のPythonパッケージを提供します。

## インストール

```bash
# PyPIからインストール
pip install tabscript

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

# テキストとして出力
tab2txt score.tab
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

## 記法の詳細

TabScript言語の記法の詳細については[docs/format.md](docs/format.md)を参照してください。

## 開発者向け情報

開発への参加方法、テスト方法、コーディング規約などについては[docs/development.md](docs/development.md)を参照してください。

## Todo
- スラー・タイ
- 繰り返し、DS、Coda
- 三連符
- 改ページ
- VSCode plugin

## ライセンス

MIT License
