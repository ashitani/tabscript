# 実装仕様

## プロジェクト構造

```
src/tabscript/
├── __init__.py      # パブリックAPIの定義
├── models.py        # データモデル定義
├── parser/          # パース処理関連
│   ├── __init__.py
│   ├── parser.py    # メインのパーサー
│   ├── preprocessor.py  # テキスト前処理
│   ├── analyzer.py  # 構造解析
│   ├── validator.py # バリデーション
│   ├── analyzer/    # 詳細な解析処理
│   └── builder/     # スコア構築処理
├── renderer.py      # レンダリング処理
├── style.py         # スタイル定義
├── exceptions.py    # 例外定義
└── cli.py          # コマンドラインインターフェース
```

## パース処理の流れ

TabScriptのパース処理は以下の順序で実行されます：

1. パース処理の全体フロー
   ```python
   # Parser.parse()内での処理順序
   preprocessor.preprocess()  # テキストの前処理
   analyzer.analyze()        # 構造解析
   validator.validate()      # バリデーション
   score_builder.build_score()  # スコア構築
   ```

2. 前処理フェーズ (`preprocessor.py`)
   - `_clean_text()`: コメントの除去
     - 行頭コメント（`#`または`//`で始まる行）
     - 行末コメント（`//`以降）
     - 複数行コメント（`'''`または`"""`で囲まれた部分）
   - `_normalize_empty_lines()`: 空行の正規化
     - 連続する空行を1行に
     - セクション区切りの空行は2行に
   - `_normalize_all_brackets()`: 括弧の正規化
     - 繰り返し記号（`{`と`}`）の一行化
     - n番カッコ（`{n`と`n}`）の一行化
     - 括弧と内容の間にスペースを挿入

3. 構造解析フェーズ (`analyzer.py`)
   - `analyze()`: メインの解析処理
     - `_parse_metadata()`: メタデータの解析
       - `$title`、`$tuning`、`$beat`などの設定
     - `_parse_sections()`: セクションの解析
       - セクション名の抽出
       - 小節の構造解析
     - `_parse_bars()`: 小節の解析
       - 基本音符（`弦-フレット:音価`）
       - 休符（`r音価`）
       - 和音（`(音符1 音符2):音価`）
       - コード（`[コード名]`）

4. バリデーションフェーズ (`validator.py`)
   - `validate()`: メインの検証処理
     - `_validate_metadata()`: メタデータの検証
     - `_validate_sections()`: セクション構造の検証
     - `_validate_bars()`: 小節の長さ検証
     - `_validate_notes()`: 音符の整合性検証
     - `_validate_chords()`: コードの整合性検証

5. スコア構築フェーズ (`builder/score.py`)
   - `build_score()`: メインの構築処理
     - `_build_sections()`: セクションの構築
       - デフォルトセクションの処理
       - 名前付きセクションの処理
     - `_build_bars()`: 小節の構築
       - 音符の構築
       - コードの構築
     - `_organize_bars_into_columns()`: レイアウトの構築
       - 行あたりの小節数に基づくカラム分割

## データモデル

### スコア構造
- `Score`: スコア全体を表す
  - `metadata`: メタデータ（タイトル、チューニング、拍子など）
  - `sections`: セクションのリスト

### セクション構造

#### セクションの解析

1. デフォルトセクションの処理
   - セクション名が指定されていない場合、デフォルトセクションとして扱う
   - `name`を空文字列（`""`）に設定
   - `is_default`を`True`に設定
   - 次のセクション名が指定されるまで、すべての小節をこのセクションに追加

2. 明示的なセクションの処理
   - `[セクション名]`の形式で指定された場合、新しいセクションを作成
   - `name`に指定されたセクション名を設定
   - `is_default`を`False`に設定
   - 前のセクションが空のデフォルトセクションの場合、そのセクションを破棄

3. セクションの保存
   - セクションは`Section`クラスのインスタンスとして管理
   - 各セクションは以下の属性を持つ：
     - `name`: セクション名（デフォルトセクションの場合は空文字列）
     - `is_default`: デフォルトセクションかどうか
     - `bars`: 小節のリスト
     - `columns`: カラムのリスト（レイアウト用）

#### セクションの構築

1. デフォルトセクションの作成
   ```python
   section = Section(
       name="",  # 空文字列でデフォルトセクションを表現
       is_default=True,
       bars=[],
       columns=[]
   )
   ```

2. 明示的なセクションの作成
   ```python
   section = Section(
       name="セクション名",
       is_default=False,
       bars=[],
       columns=[]
   )
   ```

3. 空のデフォルトセクションの処理
   ```python
   if current_section.is_default and not current_section.bars:
       # 空のデフォルトセクションを破棄
       sections.pop()
   ```

#### セクションのレンダリング

1. デフォルトセクション
   - セクション名を表示しない
   - 小節のみを表示

2. 明示的なセクション
   - セクション名を表示
   - その下に小節を表示

3. レイアウト
   - 各セクションは独立したブロックとして表示
   - セクション間は空行で区切る

### 小節構造
- `Bar`: 小節を表す
  - `notes`: 音符のリスト
  - `chords`: コードのリスト
  - `repeat_start`: 繰り返し開始フラグ
  - `repeat_end`: 繰り返し終了フラグ
  - `volta_start`: n番カッコ開始フラグ
  - `volta_end`: n番カッコ終了フラグ
  - `volta_number`: n番カッコの番号

### 音符構造
- `Note`: 音符を表す
  - `string`: 弦番号
  - `fret`: フレット番号
  - `duration`: 音価（`Fraction`型）
  - `is_rest`: 休符フラグ
  - `is_muted`: ミュートフラグ

### コード構造
- `Chord`: コードを表す
  - `name`: コード名
  - `position`: 小節内での位置

## 音符のステップ数計算

音符の長さ（ステップ数）は、`Fraction`クラスを使用して有理数で表現します。これにより、三連符などの特殊な音符も正確に表現できます。

### 基本的な考え方
- 4分音符を基本単位として`Fraction(1)`とする
- 全音符は`Fraction(4)`（4分音符4つ分）
- 2分音符は`Fraction(2)`（4分音符2つ分）
- 8分音符は`Fraction(1, 2)`（4分音符の半分）
- 16分音符は`Fraction(1, 4)`（8分音符の半分）
- 32分音符は`Fraction(1, 8)`（16分音符の半分）
- 64分音符は`Fraction(1, 16)`（32分音符の半分）

### 付点音符
付点音符は基本の音符の長さの1.5倍になります：
- 付点4分音符: `Fraction(1) * Fraction(3, 2) = Fraction(3, 2)`
- 付点8分音符: `Fraction(1, 2) * Fraction(3, 2) = Fraction(3, 4)`

### 小節の長さ検証
小節の長さは拍子記号に基づいて計算されます：
- 4/4拍子の場合: `Fraction(4, 4) * 4 = Fraction(4)` (4分音符4つ分)
- 3/4拍子の場合: `Fraction(3, 4) * 4 = Fraction(3)` (4分音符3つ分)
- 6/8拍子の場合: `Fraction(6, 8) * 4 = Fraction(3)` (4分音符3つ分)

小節内の全ての音符のステップ数の合計が、期待される小節の長さと一致するかを検証します。

