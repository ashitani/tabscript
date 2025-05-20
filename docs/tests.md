# テスト仕様

## テストの実行方法

テストは以下のコマンドで実行できます：

```bash
# 全てのテストを実行
pytest

# 特定のテストファイルを実行
pytest tests/renderer/test_01_layout_calculator.py

# 特定のテスト関数を実行
pytest tests/renderer/test_01_layout_calculator.py::test_calculate_section_layout

# 詳細な出力で実行
pytest -v

```

## テストの追加方法

新しいテストを追加する際は、以下の点に注意してください：

1. テストファイルの選択
   - 機能に応じて適切なテストファイルを選択
   - レンダリング処理は `tests/renderer/` に
   - パース処理は `tests/parser/` に

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

# テスト構成

## フォルダ構成
```
tests/
├── data/           # テストデータ
├── integration/    # 統合テスト
├── parser/         # パース処理のテスト
└── renderer/       # レンダリング処理のテスト
```

## レンダリング処理のテスト

- `test_01_layout_calculator.py`: レイアウト計算のテスト
- `test_02_note_renderer.py`: 音符の描画テスト
- `test_03_triplet_renderer.py`: 三連符の描画テスト
- `test_04_volta_renderer.py`: ボルタブラケットの描画テスト
- `test_05_repeat_renderer.py`: リピート記号の描画テスト
- `test_06_dummy_bar_renderer.py`: ダミー小節の描画テスト
- `test_07_bar_renderer.py`: 小節全体の描画テスト
- `test_08_renderer.py`: 全体のレンダリング処理のテスト

## パース処理のテスト

- `test_01_preprocessor.py`: テキスト前処理のテスト
- `test_02_analyzer.py`: 構造解析のテスト
- `test_03_repeat_analyzer.py`: リピート解析のテスト
- `test_04_section_analyzer.py`: セクション解析のテスト
- `test_05_validator.py`: バリデーションのテスト
- `test_06_note_builder.py`: 音符構築のテスト
- `test_07_bar_builder.py`: 小節構築のテスト
- `test_08_score_builder.py`: スコア構築のテスト
