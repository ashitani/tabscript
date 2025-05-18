# TabScript Syntax

TabScriptのシンタックスハイライトを提供するVSCode拡張機能です。

## 機能

- TabScriptファイル（.tab）のシンタックスハイライト
- コメント、メタデータ、セクションの色分け

## テーマの設定

シンタックスハイライトを有効にするには、以下の手順でテーマを設定してください：

1. VSCodeのコマンドパレットを開く（Mac: `Cmd+Shift+P`、Windows: `Ctrl+Shift+P`）
2. `Preferences: Color Theme`を選択
3. 以下のいずれかのテーマを選択：
   - `TabScript Light`（ライトテーマ用）
   - `TabScript Dark`（ダークテーマ用）

## 色の設定

- コメント：緑色（ライト）/ 薄緑色（ダーク）
- メタデータ行：紫色（両テーマ）
- セクション行：青緑色（両テーマ）

## 開発

### 必要条件

- Node.js
- npm

### セットアップ

```bash
npm install
```

### ビルド

```bash
npm run compile
```

### デバッグ

1. 拡張機能をパッケージング
```bash
npm run package
```

2. 生成された`.vsix`ファイルをVSCodeにインストール
   - VSCodeの拡張機能ビューを開く
   - 「...」メニューから「VSIXからのインストール...」を選択
   - 生成された`.vsix`ファイルを選択

3. VSCodeを再起動して拡張機能を有効化

## ライセンス

MIT 