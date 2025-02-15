# TabScript 開発者ガイド

## 開発環境のセットアップ

```bash
# リポジトリのクローン
git clone https://github.com/ashitani/tabscript.git
cd tabscript

# 仮想環境の作成と有効化（推奨）
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# 開発用依存パッケージのインストール
pip install -e ".[dev]"
```

## システム要件

### macOS
```bash
brew install libjpeg
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get install libjpeg-dev
```

## テスト

### テストの構成

テストは以下の3つの主要なカテゴリーに分かれています：

1. **構造的なテスト** (`test_parser.py`)
   - 基本的なパース機能
   - メタデータの処理
   - セクション・小節の構造
   - コードの解析

2. **音楽的な正当性** (`test_musical_validity.py`)
   - 小節の長さ
   - 音価の継承
   - 付点音符の処理
   - 拍子記号との整合性

3. **エッジケース** (`test_edge_cases.py`)
   - 不正な入力の処理
   - 小節内でのコード変更
   - 特殊な記法の処理

### テストの実行

```bash
# 基本的なテスト実行
『

# 詳細な出力を表示
python -m pytest -v

# 失敗したテストのデバッグ情報を表示
python -m pytest --debug

# 特定のカテゴリーのみテスト
python -m pytest tests/test_parser.py
```

### デバッグ出力

`--debug`オプションを使用すると、テスト失敗時に以下の情報が表示されます：
- セクション構造
- 小節の内容
- 音符の詳細（弦、フレット、音価、ステップ数、コード）

## CI/CD

（近日実装予定）
- GitHub Actionsによる自動テスト
- 複数のPythonバージョンでのテスト
- コードカバレッジレポート
- リリース自動化

## コーディング規約

- PEP 8に準拠
- 型ヒントの使用を推奨
- docstringはGoogle形式
- コミットメッセージは日本語で具体的に

## プルリクエスト

1. 新しいブランチを作成
2. テストを追加
3. 変更を実装
4. テストが全て通ることを確認
5. プルリクエストを作成 