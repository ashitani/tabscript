# TabScriptパーサーのリファクタリング計画

## 目次

1. [現状の問題点](#現状の問題点)
2. [リファクタリング方針](#リファクタリング方針)
3. [モジュール分割](#モジュール分割)
4. [クラス設計](#クラス設計)
5. [段階的移行計画](#段階的移行計画)
6. [テスト戦略](#テスト戦略)

## 現状の問題点

1. **ファイルサイズが大きい**: 約1500行のコードが単一ファイルに詰め込まれています
2. **単一責任の原則に違反**: パース、検証、構造解析など複数の役割を1つのクラスが担っています
3. **保守性の低下**: コードの関連部分が離れており、修正や拡張が困難です
4. **テスト困難**: 責任が分離されていないため、単体テストが困難です

## リファクタリング方針

1. 単一責任の原則に従って、パーサーを複数の小さなクラスに分割
2. 各クラスは特定の責任領域に集中し、他の部分との依存関係を最小限に保つ
3. 段階的にリファクタリングを進め、各ステップでテストを実行して機能を確認
4. 既存のテストを維持しながら、新しいクラスの機能を徐々に追加

## モジュール分割

src/tabscript/parser/
├── init.py # パーサーのエントリーポイント
├── preprocessor.py # テキスト前処理を担当
├── analyzer.py # 構造解析を担当
├── validator.py # バリデーションを担当
├── builder.py # スコア構築を担当
└── utils.py # ユーティリティ関数

## クラス設計

| モジュール | クラス | 責任 |
|---------|------|-----|
| `preprocessor.py` | `TextPreprocessor` | コメント除去、正規化 |
| `analyzer.py` | `StructureAnalyzer` | セクション・小節の構造解析 |
| `validator.py` | `TabScriptValidator` | 音価、拍子、チューニングの検証 |
| `builder.py` | `ScoreBuilder` | 解析結果からScoreオブジェクトを構築 |

## 段階的移行計画

### フェーズ1: 並行開発フェーズ

1. **新クラスの作成と既存機能の段階的移行**
   ```python
   class Parser:
       def __init__(self, debug_mode=False):
           # 新クラスのインスタンスを作成
           self._preprocessor = TextPreprocessor(debug_mode)
           
           # 既存の処理はそのまま維持
           self.debug_mode = debug_mode
           self.score = None
   
       def _clean_text(self, text: str) -> str:
           # 段階的に新クラスへ移行
           # 1. まず新クラスの処理を呼び出し
           preprocessed = self._preprocessor.preprocess(text)
           
           # 2. 既存の処理も並行して実行
           old_result = self._old_clean_text(text)
           
           # 3. 結果を比較して検証（デバッグモード時）
           if self.debug_mode and preprocessed != old_result:
               print("Warning: New preprocessor result differs from old implementation")
               print(f"Old: {old_result}")
               print(f"New: {preprocessed}")
           
           # 4. テストが通れば新実装を返す
           return preprocessed
   ```

2. **テストの並行実行**
   ```python
   # tests/parser/test_01_preprocessor.py
   def test_preprocessor_removes_comments():
       preprocessor = TextPreprocessor()
       input_text = "# コメント\n実際の内容"
       assert preprocessor.preprocess(input_text) == "実際の内容"

   # tests/test_parser.py (既存)
   def test_parser_removes_comments():
       parser = Parser()
       input_text = "# コメント\n実際の内容"
       assert parser._clean_text(input_text) == "実際の内容"
   ```

3. **段階的な機能移行のチェックリスト**
   - [ ] コメント除去機能
   - [ ] 空行正規化
   - [ ] 繰り返し記号の正規化
   - [ ] n番カッコの正規化

### フェーズ2: 検証フェーズ

1. **新旧実装の並行運用**
   - 新クラスと旧実装の両方を維持
   - 両方のテストが通ることを確認
   - 出力結果の一致を検証

2. **差分の検出と修正**
   - 新旧実装の結果が異なる場合の原因特定
   - エッジケースの発見と対応
   - 仕様の明確化と文書化

3. **パフォーマンス比較**
   - 新実装と旧実装の処理速度比較
   - メモリ使用量の検証
   - 必要に応じた最適化

### フェーズ3: 完全移行フェーズ

1. **旧実装の段階的削除**
   - 新実装が安定していることを確認
   - 旧コードの削除
   - 関連する古いテストの整理

2. **新インターフェースの確立**
   - 新クラスのAPIの最終調整
   - ドキュメントの更新
   - 移行ガイドの作成

このアプローチの利点：

1. **安全性**
   - 既存の機能が常に維持される
   - 新旧両方のテストによる二重の検証
   - 問題発生時の早期発見

2. **段階的な移行**
   - 機能ごとの段階的な移行が可能
   - 各段階での検証が容易
   - リスクの分散

3. **品質保証**
   - 新旧実装の結果比較による検証
   - エッジケースの発見機会の増加
   - テストカバレッジの向上

4. **柔軟性**
   - 問題発生時の切り戻しが容易
   - 部分的な改善が可能
   - 開発速度の調整が可能

## テスト戦略

### 既存のテストの維持

1. 既存の`test_parser.py`はそのまま維持
2. 新クラスのテストを追加する際は、同等の機能をテストしていることを確認
3. 新旧両方のテストが通ることを確認しながら移行

### 新しいテストの追加

1. 各クラスの責任に応じたテストを作成
2. エッジケースや異常系のテストを追加
3. テストカバレッジを維持または向上

### 統合テスト

1. 新しいクラス間の連携をテスト
2. エンドツーエンドのテストを追加
3. パフォーマンステストの実施

このアプローチの利点：

1. **安全性**: 既存のテストが常に動作することを確認しながら移行できます
2. **段階的**: 一度に大きな変更を行わず、少しずつ移行できます
3. **可逆性**: 問題が発生した場合、簡単に元に戻せます
4. **並行開発**: 新旧の実装を並行して維持できます

このように段階的に移行することで、リファクタリングのリスクを最小限に抑えながら、コードの品質を向上させることができます。

### テストディレクトリ構造

tests/
├── parser_old/                     # 旧Parserクラスのテスト（一時的）
│   ├── test_01_preprocess.py      # 前処理関連
│   ├── test_02_structure.py       # 構造解析関連
│   ├── test_03_bar_content.py     # 小節内容解析関連
│   └── test_04_validation.py      # バリデーション関連
│
├── parser/                         # 新しいパーサー関連のテスト
│   ├── test_01_preprocessor.py    # TextPreprocessorのユニットテスト
│   ├── test_02_analyzer.py        # StructureAnalyzerのユニットテスト
│   ├── test_03_validator.py       # TabScriptValidatorのユニットテスト
│   ├── test_04_builder.py         # ScoreBuilderのユニットテスト
│   └── test_99_parser.py          # 新Parserクラスの統合テスト
│
├── renderer/                       # レンダラー関連のテスト（変更なし）
│   ├── test_01_layout.py
│   └── test_02_drawing.py
│
└── integration/                    # システム全体の統合テスト
    └── test_01_end_to_end.py      # パーサー＋レンダラーの結合テスト

## テスト移行計画

### 現在のテストの分類と移行先

現在のテストを機能ごとに分類し、新しいクラスのテストへと移行していきます。

#### 1. プリプロセッサ関連 (`TextPreprocessor`のテスト)
- コメント除去テスト (`test_comment_removal`, `test_multiline_comment`, `test_empty_line_removal`)
  - 行頭コメントの除去
  - 複数行コメントの除去
  - コメント除去後の空行の正規化
- 繰り返し記号の正規化テスト (`test_repeat_bracket_normalization`, `test_volta_bracket_normalization`, `test_normalize_repeat_brackets`, `test_normalize_volta_brackets`)
  - 基本的な繰り返し記号の正規化
  - n番カッコの正規化
  - 入れ子の繰り返し構造の検証
- エラーケーステスト (`test_empty_repeat_bracket`, `test_unclosed_repeat_bracket`, `test_unclosed_volta_bracket`, `test_mismatched_volta_numbers`)
  - 不正なコメント形式
  - 閉じられていない複数行コメント
  - 不正な繰り返し記号

#### 2. 構造解析関連 (`StructureAnalyzer`のテスト)
- メタデータ解析テスト (`test_metadata_extraction`, `test_invalid_metadata`, `test_parse_metadata_line`)
  - 基本的なメタデータの解析
  - 不正なメタデータ形式の検証
  - メタデータの継承と上書き
- セクション構造テスト (`test_section_structure`, `test_empty_section`, `test_parse_section_header`)
  - セクション名の解析
  - セクション内容の抽出
  - 空のセクションの処理
- 小節構造テスト (`test_bar_structure`, `test_volta_structure`, `test_repeat_basic`, `test_repeat_separate_brackets`, `test_volta_brackets`, `test_repeat_with_volta`, `test_complex_repeat_structure`, `test_repeat_end_only`, `test_multi_bar_volta`)
  - 基本的な小節構造の解析
  - 繰り返し記号を含む小節の解析
  - n番カッコを含む小節の解析

#### 3. バリデーション関連 (`TabScriptValidator`のテスト)
- 音価検証テスト (`test_duration_validation`, `test_bar_duration_validation`, `test_chord_notation_duration`)
  - 基本的な音価の検証
  - 付点音符の検証
  - 不正な音価の検出
- 拍子記号テスト (`test_beat_validation`, `test_bar_duration_skip_validation`)
  - 基本的な拍子記号の検証
  - 不正な拍子記号の検出
  - 小節の長さと拍子の整合性
- チューニングテスト (`test_tuning_validation`, `test_string_number_validation`, `test_fret_number_validation`)
  - 有効なチューニングの検証
  - 不正なチューニングの検出
  - チューニングに基づく弦番号の検証

#### 4. スコア構築関連 (`ScoreBuilder`のテスト)
- 基本構造テスト (`test_basic_note_parsing`, `test_rest_parsing`, `test_parse_notes`, `test_parse_bar_line`)
  - スコアオブジェクトの構築
  - セクションの構築
  - 小節の構築
- 音符解析テスト (`test_chord_parsing`, `test_chord_notation`, `test_muted_note`, `test_string_movement_notation`, `test_tie_slur_notation`)
  - 基本的な音符の解析
  - 和音の解析
  - 休符の解析
  - スラー/タイの解析
- 継承テスト (`test_duration_inheritance`, `test_inheritance`, `test_continued_string_movement`, `test_string_movement_duration_calculation`, `test_chord_duration_calculation`)
  - 弦番号の継承
  - 音価の継承
  - コード名の継承

#### 5. 統合テスト
- エンドツーエンドテスト (`test_complete_score`, `test_file_parsing`, `test_sample_tab`)
  - 基本的なタブ譜の解析
  - 複雑な繰り返し構造の解析
  - 全機能を含むタブ譜の解析
- エッジケーステスト (`test_error_cases`, `test_repeat_test`)
  - 最小限のタブ譜
  - 最大限の機能を使用したタブ譜
  - エラーケースの処理

### 移行手順

1. **準備フェーズ**
   - 既存のテストを`tests/parser_old/`に移動
   - 新しいテストディレクトリ構造を作成

2. **段階的移行**
   - 各機能を新しいクラスに移行する際に、対応するテストも移行
   - 移行中は両方のテストが並行して実行されることを確認
   - 新旧の出力結果を比較して正しさを検証

3. **検証フェーズ**
   - 全ての機能が移行された後、新旧のテストを並行実行
   - カバレッジを確認し、必要に応じてテストを追加
   - エッジケースのテストを強化

4. **完了フェーズ**
   - 新しいテストが十分な品質に達したことを確認
   - 古いテストを段階的に削除
   - 最終的なテストの整理とドキュメント更新

### テストの依存関係

新しいクラス構造では、以下のような依存関係を考慮してテストを設計します：

TextPreprocessor
↓
StructureAnalyzer
↓
TabScriptValidator
↓
ScoreBuilder


各クラスのテストは、可能な限り独立して実行できるように設計し、必要な場合はモックを使用して依存関係を分離します。

### 注意点

- 既存のテストの機能カバレッジを維持
- エッジケースや異常系のテストを確実に移行
- テスト名や構造を明確に保ち、メンテナンス性を向上
- 新旧のテストが並存する期間の管理を慎重に行う