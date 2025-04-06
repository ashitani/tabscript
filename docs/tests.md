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
│   ├── test_07_analyzer.py      # 追加の解析テスト
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
   - `test_07_analyzer.py`: 追加の解析テスト
     - 対応する実装: `src/tabscript/parser/analyzer/`配下の各モジュール
     - 特殊なケースの解析
     - エッジケースの処理
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