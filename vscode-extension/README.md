# TabScript PDF Preview for VSCode

TabScript（.tab）ファイルを保存するたびに自動でPDF化し、VSCode内でプレビュー表示する拡張です。

## インストール方法

1. このリポジトリの`vscode-extension/`ディレクトリで以下を実行：

```
npm install
npm run package
```

2. 生成された`.vsix`ファイルをVSCodeでインストール：

- コマンドパレット（Cmd+Shift+P）で「拡張機能: VSIXからインストール」を選択し、`.vsix`ファイルを指定

## 使い方

- `.tab`ファイルを保存すると自動でPDFが生成され、プレビューが表示されます。
- PythonのTabScript本体（tab2pdf）が実行できる環境が必要です。

## 注意
- Python・tab2pdfのパスが通っていることを確認してください。
- PDFのプレビューはVSCodeのバージョンや設定によっては制限される場合があります。 