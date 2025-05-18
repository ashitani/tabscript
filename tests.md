# テスト仕様（tests.md）

## テストファイル構成

- test_00_preprocessor.py … 前処理（Preprocessor）
- test_10_parser_section.py … セクションパース
- test_11_parser_bar.py … 小節パース・繰り返し
- test_12_parser_note.py … 音符パース
- test_20_validator.py … バリデーション
- test_30_builder_score.py … ScoreBuilder
- test_31_builder_bar.py … BarBuilder
- test_32_builder_note.py … NoteBuilder
- test_99_integration.py … 統合・最終確認

### renderer関連
- tests/renderer/ 配下に配置（現状維持）

## 命名規則
- 10の位でカテゴリ、1の位でバリエーション
- integrationは test_99_integration.py に統合

## テスト追加・修正時の指針
- 単体テストはカテゴリごとに追加
- 複合仕様や全体フローは test_99_integration.py に追加 