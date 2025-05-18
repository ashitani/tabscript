# テスト仕様

## テストファイル構成

テストは以下のファイルに分割されています：

1. `test_01_preprocessor.py`
   - テキスト前処理のテスト
   - コメント除去
   - 空行処理
   - インデント処理

2. `test_02_analyzer.py`
   - 基本的な解析機能のテスト
   - メタデータ解析
   - セクション構造解析
   - 基本的な小節解析

3. `test_03_repeat_analyzer.py`
   - 繰り返し構造の解析テスト
   - 基本的な繰り返し
   - n番カッコ
   - 複雑な繰り返し構造
   - 複数行にまたがる繰り返し

4. `test_04_section_analyzer.py`
   - セクション構造の詳細なテスト
   - デフォルトセクション
   - 名前付きセクション
   - 複数セクション
   - 空のセクション

5. `test_05_validator.py`
   - バリデーションのテスト
   - メタデータの検証
   - セクション構造の検証
   - 小節構造の検証

6. `test_06_note_builder.py`
   - 音符構築のテスト
   - 基本的な音符
   - 和音
   - 休符
   - 特殊な音符（ミュート、スライド等）

7. `test_07_bar_builder.py`
   - 小節構築のテスト
   - 基本的な小節
   - 繰り返しを含む小節
   - n番カッコを含む小節

8. `test_08_score_builder.py`
   - スコア構築のテスト
   - 基本的なスコア
   - 複数セクションを含むスコア
   - メタデータを含むスコア

9. `test_99_parser.py`
   - 統合テスト
   - 実際の楽譜データを使用したテスト
   - エラーケースのテスト
   - エッジケースのテスト

## テストの実行方法

テストは以下のコマンドで実行できます：

```bash
# 全てのテストを実行
pytest

# 特定のテストファイルを実行
pytest tests/parser/test_01_preprocessor.py

# 特定のテスト関数を実行
pytest tests/parser/test_01_preprocessor.py::test_remove_comments

# デバッグモードで実行
pytest -v --pdb
```

## テストの追加方法

新しいテストを追加する際は、以下の点に注意してください：

1. テストファイルの選択
   - 機能に応じて適切なテストファイルを選択
   - 新しい機能の場合は新しいテストファイルを作成

2. テストケースの設計
   - 正常系と異常系の両方をテスト
   - エッジケースも考慮
   - テストケースは独立していること

3. テストの実装
   - テスト関数名は`test_`で始める
   - テストの説明をドキュメント文字列で記述
   - アサーションは具体的な値を指定

4. テストの実行と確認
   - 全てのテストが通ることを確認
   - カバレッジを確認
   - パフォーマンスを確認

## テスト構成

```
tests/
├── conftest.py      # テスト共通設定
├── data/           # テストデータ
├── integration/    # 統合テスト
├── parser/         # パース処理のテスト
│   ├── test_01_preprocessor.py  # 前処理のテスト
│   ├── test_02_analyzer.py      # 構造解析のテスト
│   ├── test_03_validator.py     # バリデーションのテスト
│   ├── test_04_note_builder.py  # 音符構築のテスト
│   ├── test_05_bar_builder.py   # 小節構築のテスト
│   ├── test_06_score_builder.py # スコア構築のテスト
│   └── test_99_parser.py        # パーサーの統合テスト
└── renderer/       # レンダリング処理のテスト
```

### テストの種類と目的

1. パース処理テスト (`tests/parser/`)
   - `test_01_preprocessor.py`: 前処理フェーズのテスト
     - 対応する実装: `src/tabscript/parser/preprocessor.py`
     - コメント除去
     - 空行正規化
     - 括弧の正規化
   - `test_02_analyzer.py`: 構造解析フェーズのテスト
     - 対応する実装: `src/tabscript/parser/analyzer.py`
     - メタデータ解析
     - セクション解析
     - 音符解析
     - コード解析
   - `test_03_validator.py`: バリデーションフェーズのテスト
     - 対応する実装: `src/tabscript/parser/validator.py`
     - メタデータ検証
     - セクション構造検証
     - 小節の長さ検証
     - 音符の整合性検証
     - コードの整合性検証
   - `test_04_note_builder.py`: 音符構築のテスト
     - 対応する実装: `src/tabscript/parser/builder/note_builder.py`
     - 基本音符の構築
     - 休符の構築
     - 和音の構築
   - `test_05_bar_builder.py`: 小節構築のテスト
     - 対応する実装: `src/tabscript/parser/builder/bar_builder.py`
     - 小節の基本構造
     - 繰り返し記号の処理
     - n番カッコの処理
   - `test_06_score_builder.py`: スコア構築のテスト
     - 対応する実装: `src/tabscript/parser/builder/score_builder.py`
     - スコア全体の構造
     - セクションの構築
     - メタデータの構築
   - `test_99_parser.py`: パーサーの統合テスト
     - 対応する実装: `src/tabscript/parser/parser.py`
     - パース処理全体の動作確認
     - エラー処理の確認

2. レンダリングテスト (`tests/renderer/`)
   - 対応する実装: `src/tabscript/renderer.py`
   - レンダリング処理のテスト
   - 出力形式の検証
   - レイアウト計算の検証

3. 統合テスト (`tests/integration/`)
   - 対応する実装: `src/tabscript/`全体
   - パースからレンダリングまでの一連の処理のテスト
   - エンドツーエンドの動作確認

### テストの実行
- pytestを使用
- デバッグレベルオプション: `--debug-level` (0=無効, 1=基本, 2=詳細, 3=全情報)
- テスト失敗時のデバッグ出力機能あり

### テストデータ
- `tests/data/` にテスト用のtabファイルを配置
- テストケースごとに適切なテストデータを用意 