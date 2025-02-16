from typing import List, Tuple, Optional, Dict
import re
from .models import Score, Section, Bar, Note, Column
from .exceptions import ParseError, TabScriptError
from fractions import Fraction
from dataclasses import dataclass

@dataclass
class BarInfo:
    """小節の構造情報"""
    content: str
    repeat_start: bool = False
    repeat_end: bool = False
    volta_number: Optional[int] = None

@dataclass
class SectionStructure:
    """セクションの構造情報"""
    name: str
    content: List[str]  # 生のテキスト行

@dataclass
class ScoreStructure:
    """スコア全体の構造情報"""
    metadata: Dict[str, str]
    sections: List[SectionStructure]

class Parser:
    def __init__(self):
        self.score = None
        self.current_section = None
        self.current_line = 0
        self.last_string = 1      # デフォルトは1弦
        self.last_duration = "4"  # デフォルトは4分音符
        self.debug_mode = False  # デバッグモードのフラグ

    def debug_print(self, *args, **kwargs):
        """デバッグモードの時だけ出力"""
        if self.debug_mode:
            print(*args, **kwargs)

    def _preprocess_text(self, text: str) -> str:
        """コメントと空行を除去する前処理"""
        self.debug_print("\n=== _preprocess_text ===")
        processed_lines = []
        in_multiline_comment = False
        
        for line in text.split('\n'):
            line = line.strip()
            self.debug_print(f"Processing line: '{line}'")
            
            # 空行をスキップ
            if not line:
                self.debug_print("Skipping empty line")
                continue
            
            # 複数行コメントの処理
            if in_multiline_comment:
                self.debug_print("In multiline comment")
                if line.endswith("'''") or line.endswith('"""'):
                    self.debug_print("Found multiline comment end")
                    in_multiline_comment = False
                continue
            
            # 複数行コメントの開始
            if line.startswith("'''") or line.startswith('"""'):
                self.debug_print("Found multiline comment start")
                in_multiline_comment = True
                continue
            
            # 行頭#のコメントをスキップ（行頭のみ）
            if line.lstrip().startswith('#'):
                self.debug_print("Skipping line starting with #")
                continue
            
            # 有効な行を追加
            self.debug_print(f"Adding line: '{line}'")
            processed_lines.append(line)
        
        result = '\n'.join(processed_lines)
        self.debug_print(f"\nFinal result:\n{result}")
        return result

    def parse(self, source: str) -> Score:
        """TabScriptをパースしてScoreオブジェクトを返す"""
        self.debug_print("\n=== parse ===")
        self.debug_print(f"Parsing source: {source}")
        
        # ファイルかテキストかを判断
        text = self._load_source(source)
        self.debug_print(f"\nLoaded text:\n{text}")
        
        # 1. 基本的なテキストクリーニング
        cleaned_text = self._clean_text(text)
        self.debug_print(f"\nCleaned text:\n{cleaned_text}")
        
        # 2. メタデータとセクション構造の抽出
        structure = self._extract_structure(cleaned_text)
        self.debug_print(f"\nExtracted structure:")
        self.debug_print(f"Metadata: {structure.metadata}")
        self.debug_print(f"Sections: {[s.name for s in structure.sections]}")
        
        # 3. 小節構造の解析（繰り返し記号など）
        self.score = self._create_score(structure, cleaned_text)
        self.debug_print(f"\nCreated score object id: {id(self.score)}")
        
        return self.score
    
    def _load_source(self, source: str) -> str:
        """ファイルパスまたはテキストから入力を読み込む"""
        if '\n' in source:
            return source
        with open(source, 'r') as f:
            return f.read()
    
    def _clean_text(self, text: str) -> str:
        """コメントと空行の除去、括弧記号の正規化"""
        raw_lines = text.split('\n')
        processed_lines = []
        
        # 括弧記号の正規化
        i = 0
        in_volta = False  # n番カッコの中にいるかどうか
        while i < len(raw_lines):
            line = raw_lines[i].strip()
            
            # 空行スキップ
            if not line:
                i += 1
                continue
            
            # n番カッコの開始行を処理
            if line.startswith('{') and len(line) > 1:
                try:
                    # n番カッコの入れ子チェック
                    if in_volta:
                        raise ParseError("Nested volta brackets are not allowed", self.current_line)
                    
                    # 複数番号のパターン（例：1,2）をチェック
                    numbers_str = line[1:].strip()
                    if ',' in numbers_str:
                        numbers = [n.strip() for n in numbers_str.split(',')]
                        numbers_text = ','.join(numbers)
                        if i + 1 < len(raw_lines) and i + 2 < len(raw_lines):
                            next_line = raw_lines[i + 1].strip()
                            end_line = raw_lines[i + 2].strip()
                            if end_line == f"{numbers_text}}}":
                                # 複数番号のn番カッコを1行に正規化
                                processed_lines.append(f"{{{numbers_text} {next_line} }}{numbers_text}")
                                i += 3
                                continue
                    else:
                        # 単一番号の処理
                        number = int(numbers_str)
                        if i + 1 < len(raw_lines) and i + 2 < len(raw_lines):
                            next_line = raw_lines[i + 1].strip()
                            end_line = raw_lines[i + 2].strip()
                            if end_line == f"{number}}}":
                                # n番カッコを1行に正規化
                                processed_lines.append(f"{{{number} {next_line} }}{number}")
                                i += 3
                                continue
                    in_volta = True  # n番カッコの中に入る
                except ValueError:
                    pass
            
            # n番カッコの終了行を処理
            if line.endswith('}') and len(line) > 1:
                try:
                    number = int(line[:-1])
                    in_volta = False  # n番カッコから出る
                except ValueError:
                    pass
            
            # 通常の繰り返し記号を処理
            if line == '{':
                if i + 1 < len(raw_lines) and i + 2 < len(raw_lines):
                    next_line = raw_lines[i + 1].strip()
                    end_line = raw_lines[i + 2].strip()
                    if end_line == '}':
                        # 繰り返し記号を1行に正規化
                        processed_lines.append(f"{{ {next_line} }}")
                        i += 3
                        continue
            
            # その他の行はそのまま追加
            processed_lines.append(line)
            i += 1
        
        # コメント処理
        cleaned_lines = []
        in_multiline_comment = False
        
        for line in processed_lines:
            line = line.strip()
            
            # 複数行コメントの処理
            if in_multiline_comment:
                if "'''" in line or '"""' in line:
                    in_multiline_comment = False
                    # コメント終了後のテキストを処理
                    remaining = line[line.find("'''") + 3:] if "'''" in line else line[line.find('"""') + 3:]
                    if remaining.strip() and not remaining.strip().startswith('#'):
                        cleaned_lines.append(remaining.strip())
                continue
            
            # 行内の複数行コメントを処理
            while "'''" in line or '"""' in line:
                marker = "'''" if "'''" in line else '"""'
                before_comment = line[:line.find(marker)]
                after_comment = line[line.find(marker) + 3:]
                
                if marker in after_comment:
                    # 同じ行でコメントが終わる場合
                    after_comment = after_comment[after_comment.find(marker) + 3:]
                    if before_comment.strip():
                        cleaned_lines.append(before_comment.strip())
                    if after_comment.strip():
                        cleaned_lines.append(after_comment.strip())
                    line = ""
                    break
                else:
                    # コメントが次の行まで続く場合
                    if before_comment.strip():
                        cleaned_lines.append(before_comment.strip())
                    in_multiline_comment = True
                    line = ""
                    break
            
            # 行頭#のコメントをスキップ
            if line.lstrip().startswith('#'):
                continue
            
            # 行末コメントの除去
            if '#' in line:
                line = line[:line.find('#')].strip()
            
            if line:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _extract_structure(self, text: str) -> ScoreStructure:
        """メタデータとセクション構造の抽出"""
        metadata = {}
        sections = []
        current_section = None
        
        for line in text.split('\n'):
            line = line.strip()
            
            # 空行はスキップ
            if not line:
                continue
            
            # メタデータの処理
            if line.startswith('$'):
                match = re.match(r'\$(\w+)\s*=\s*"([^"]*)"', line)
                if not match:
                    raise ParseError("Invalid metadata format", self.current_line)
                key, value = match.group(1), match.group(2)
                metadata[key] = value
                continue
            
            # セクションヘッダーの処理
            if line.startswith('['):
                name = line[1:-1].strip()
                current_section = SectionStructure(name=name, content=[])
                sections.append(current_section)
                continue
            
            # セクション内容の追加
            if current_section is not None:
                current_section.content.append(line)
        
        return ScoreStructure(metadata=metadata, sections=sections)

    def _parse_lines(self, lines: List[str]):
        """Parse lines of TabScript"""
        current_bars = []  # 現在の行の小節リスト
        bars_per_line = 4  # デフォルト値
        
        for line in lines:
            self.current_line += 1
            line = line.strip()
            
            if not line:  # 空行のみスキップ（#のチェックを削除）
                continue
            
            if line.startswith('['):
                # 未処理の小節があれば追加
                if current_bars:
                    self.current_section.columns.append(Column(bars=current_bars.copy()))
                    current_bars = []
                
                # セクション開始
                section_name = line[1:-1].strip()
                self.current_section = Section(name=section_name)
                self.score.sections.append(self.current_section)
                continue
            
            if line.startswith('$'):
                # メタデータ
                key, value = self._parse_metadata_line(line)
                if key == "bars_per_line":
                    # 未処理の小節があれば追加
                    if current_bars:
                        self.current_section.columns.append(Column(bars=current_bars.copy()))
                        current_bars = []
                    bars_per_line = int(value)
                continue
            
            # セクションがない場合は自動的にデフォルトセクションを作成
            if not self.current_section:
                self.current_section = Section(name="")  # 空の名前でセクションを作成
                self.score.sections.append(self.current_section)
            
            # 小節をパース
            bar = self._parse_bar_line(line)
            current_bars.append(bar)
            
            # 指定された数の小節が集まったら新しい行を作成
            if len(current_bars) >= bars_per_line:
                self.current_section.columns.append(Column(bars=current_bars.copy()))
                current_bars = []
        
        # 最後の未処理の小節があれば追加
        if current_bars:
            self.current_section.columns.append(Column(bars=current_bars.copy()))

    def _parse_metadata_line(self, line: str) -> Tuple[str, str]:
        """Parse a metadata line ($key="value")"""
        match = re.match(r'\$(\w+)\s*=\s*"([^"]*)"', line)
        if not match:
            raise ParseError("Invalid metadata format", self.current_line)
        key, value = match.group(1), match.group(2)
        
        # タイトルが最初に来た時のScoreの初期化を修正
        if key == 'title' and not self.score:
            self.score = Score(
                title=value,
                tuning=metadata.get('tuning', 'guitar'),
                sections=[]  # bars_per_lineパラメータを削除
            )
        elif key != "bars_per_line":  # bars_per_line以外のメタデータを設定
            setattr(self.score, key, value)
        
        return key, value

    def _parse_section_header(self, line: str):
        """Parse a section header [name]"""
        match = re.match(r'\[(.*)\]', line)
        if not match:
            raise ParseError("Invalid section header", self.current_line)
        
        name = match.group(1)
        self.current_section = Section(name=name, columns=[])
        self.score.sections.append(self.current_section)

    def _parse_notes(self, notes_str: str) -> List[Note]:
        """Parse space-separated notes"""
        self.debug_print("\n=== _parse_notes ===")
        self.debug_print(f"Input string: {notes_str}")
        notes = []
        current_chord = None
        last_chord = None

        # トークンを抽出
        tokens = []
        current_token = ""
        in_chord = False
        in_chord_name = False  # コードネーム処理中かどうか
        skip_next = False

        # トークン抽出のデバッグ
        self.debug_print("\nTokenizing:")
        i = 0
        while i < len(notes_str):
            if skip_next:
                skip_next = False
                i += 1
                continue

            char = notes_str[i]

            # 行末コメントの開始を検出したら、そこで処理を終了
            # ただしコードネーム処理中は#を通常の文字として扱う
            if char == '#' and not in_chord_name:
                if current_token:  # 現在のトークンがあれば追加
                    tokens.append(current_token.strip())
                break  # 以降は全て無視

            if char == '@':
                # コードトークンの開始
                if current_token:
                    tokens.append(current_token.strip())
                current_token = char
                in_chord_name = True  # コードネーム処理開始
            elif in_chord_name and char.isspace():
                # コードネーム処理終了
                tokens.append(current_token.strip())
                current_token = ""
                in_chord_name = False
            elif char == '(':
                in_chord = True
                current_token += char
            elif char == ')':
                in_chord = False
                current_token += char
                # 音価が続くかチェック
                if i + 1 < len(notes_str) and notes_str[i + 1] == ':':
                    # 音価部分も含めて1つのトークンとする
                    while i + 1 < len(notes_str) and (notes_str[i + 1] == ':' or notes_str[i + 1].isdigit()):
                        i += 1
                        current_token += notes_str[i]
                tokens.append(current_token.strip())
                current_token = ""
            elif not in_chord and not in_chord_name and char.isspace():
                if current_token:
                    tokens.append(current_token.strip())
                    current_token = ""
            else:
                current_token += char
            i += 1
            self.debug_print(f"  char: '{notes_str[i-1]}', current_token: '{current_token}', in_chord: {in_chord}, in_chord_name: {in_chord_name}")

        if current_token:
            tokens.append(current_token.strip())

        self.debug_print(f"\nExtracted tokens: {tokens}")
        
        # トークンをパース
        for token in tokens:
            if token.startswith('@'):
                # コードトークン
                current_chord = token[1:]
                # 前と同じコードなら None に
                if current_chord == last_chord:
                    current_chord = None
                continue
            
            # 音符トークン
            note = self._parse_note(token)
            # 前と同じコードなら None を設定
            if current_chord == last_chord:
                note.chord = None
            else:
                note.chord = current_chord
                last_chord = current_chord  # 新しいコードを記憶
            notes.append(note)
        
        return notes

    def _parse_note(self, token: str) -> Optional[Note]:
        """音符トークンをパース"""
        self.debug_print(f"\n=== _parse_note ===")
        self.debug_print(f"Token: '{token}'")
        
        # 休符の処理
        if token.startswith('r'):
            duration = token[1:] or self.last_duration
            self.last_duration = duration.rstrip('.')
            # 音価のバリデーション
            if not duration.rstrip('.').isdigit():
                raise ParseError("Invalid duration", self.current_line)
            
            # stepを計算（4分音符=4ステップ）
            base_duration = int(duration.rstrip('.'))
            step = int(16 / base_duration)  # 16分音符=1ステップ
            if duration.endswith('.'):
                step += step // 2  # 付点の場合は1.5倍
            
            return Note(
                string=0,
                fret="0",
                duration=duration,
                is_rest=True,
                step=step,
                is_chord=False,
                is_chord_start=False
            )
        
        # 通常の音符
        parts = token.split(':')
        note_part = parts[0]
        duration = parts[1] if len(parts) > 1 else self.last_duration
        
        self.debug_print(f"Initial parse: note_part='{note_part}', duration='{duration}'")
        
        # 初期化
        connect_next = False
        is_up_move = False
        is_down_move = False
        
        # 移動記号の処理
        is_up_move = note_part.startswith('u')
        is_down_move = note_part.startswith('d')
        if is_up_move or is_down_move:
            self.debug_print(f"Found move mark: up={is_up_move}, down={is_down_move}")
            note_part = note_part[1:]  # 移動記号を除去
            self.debug_print(f"After removing move mark: note_part='{note_part}'")
        
        # 弦-フレット形式の場合
        if '-' in note_part:
            self.debug_print(f"Found string-fret format: '{note_part}'")
            string_part, fret_part = note_part.split('-')
            self.debug_print(f"After split: string_part='{string_part}', fret_part='{fret_part}'")
            
            # 弦番号をパース
            string = self.safe_int(string_part.strip(), "_parse_note/string")
            self.last_string = string
            self.debug_print(f"Parsed string number: {string}")
            
            # タイ・スラー記号を処理（strip前に行う）
            if fret_part.endswith('&'):
                self.debug_print(f"Found tie/slur mark in fret_part: '{fret_part}'")
                fret_part = fret_part[:-1]
                connect_next = True
                self.debug_print(f"After removing tie/slur: fret_part='{fret_part}'")
            else:
                self.debug_print(f"No tie/slur mark found in fret_part")
            
            # フレット番号をパース
            fret_part = fret_part.strip()  # stripはタイ・スラー処理の後
            self.debug_print(f"After strip: fret_part='{fret_part}'")
            
            # フレット番号をパース
            if fret_part.upper() == 'X':
                self.debug_print("Found muted note")
                fret = fret_part
            else:
                self.debug_print(f"Parsing fret number: '{fret_part}'")
                fret = str(self.safe_int(fret_part, "_parse_note/fret"))
                self.debug_print(f"Parsed fret number: {fret}")
        else:
            # フレット番号のみの場合
            self.debug_print("Processing fret-only note")
            if note_part.endswith('&'):
                self.debug_print(f"Found tie/slur mark in note_part: '{note_part}'")
                note_part = note_part[:-1]
                connect_next = True
                self.debug_print(f"After removing tie/slur: note_part='{note_part}'")
            
            string = self.last_string
            
            # note_partを一度だけstripする
            note_part = note_part.strip()
            self.debug_print(f"After strip: note_part='{note_part}'")
            
            # フレット番号をパース
            if note_part.upper() == 'X':
                self.debug_print("Found muted note")
                fret = note_part
            else:
                self.debug_print(f"Parsing fret number: '{note_part}'")
                fret = str(self.safe_int(note_part, "_parse_note/fret"))
                self.debug_print(f"Parsed fret number: {fret}")
        
        # 音価のタイ・スラー処理
        if duration.endswith('&'):
            duration = duration[:-1]
            connect_next = True
        
        # 音価のバリデーション
        if not duration.rstrip('.').isdigit():
            raise ParseError("Invalid duration", self.current_line)
        
        self.last_duration = duration.rstrip('.')
        
        # 弦番号の範囲チェック
        string_count = self._get_string_count()
        if string < 1 or string > string_count:
            raise ParseError("Invalid string number", self.current_line)
        
        # stepを計算（4分音符=4ステップ）
        base_duration = int(duration.rstrip('.'))
        step = int(16 / base_duration)  # 16分音符=1ステップ
        if duration.endswith('.'):
            step += step // 2  # 付点の場合は1.5倍
        
        return Note(
            string=string,
            fret=fret,
            duration=duration,
            is_rest=False,
            is_up_move=is_up_move,
            is_down_move=is_down_move,
            connect_next=connect_next,
            step=step,
            is_chord=False,
            is_chord_start=False
        )

    def render_score(self, output_path: str):
        """タブ譜をファイルとして出力"""
        if not self.score:
            raise TabScriptError("No score to render. Call parse() first.")
        
        from .renderer import Renderer
        renderer = Renderer(self.score, debug_mode=self.debug_mode)  # デバッグモードを渡す
        
        if output_path.endswith('.pdf'):
            renderer.render_pdf(output_path)
        else:
            renderer.render_text(output_path)

    def print_tab(self, output_path: str):
        """省略記法を展開した完全な形式のtabファイルを出力"""
        if not self.score:
            raise TabScriptError("No score to print. Call parse() first.")

        with open(output_path, 'w') as f:
            # メタデータを出力
            f.write(f'$title="{self.score.title}"\n')
            f.write(f'$tuning="{self.score.tuning}"\n')
            f.write(f'$beat="{self.score.beat}"\n\n')

            # 各セクションを出力
            for section in self.score.sections:
                f.write(f"[{section.name}]\n")
                
                # 各小節を出力
                for column in section.columns:
                    # コード名を出力（空の場合は空文字列）
                    chord = column.bars[0].chord if column.bars[0].chord else ""
                    f.write(f"{chord}, ")

                    # 音符を完全な形式で出力
                    notes = []
                    for bar in column.bars:
                        # 音符を完全な形式で出力
                        notes.append(f"{bar.notes[0].string}-{bar.notes[0].fret}:{bar.notes[0].duration}")
                    
                    f.write(" ".join(notes) + "\n")
                
                f.write("\n")  # セクション間に空行を挿入

    def _get_string_count(self) -> int:
        """チューニング設定から弦の数を取得"""
        tuning_map = {
            "guitar": 6,
            "guitar7": 7,
            "bass": 4,
            "bass5": 5,
            "ukulele": 4
        }
        return tuning_map.get(self.score.tuning, 6)  # デフォルトは6弦

    def safe_int(self, value: str, caller: str) -> int:
        """
        intのラッパー関数。呼び出し元と変換しようとした値をデバッグ出力する
        """
        self.debug_print(f"\n=== safe_int ===")
        self.debug_print(f"Called from: {caller}")
        self.debug_print(f"Converting value: '{value}'")
        try:
            result = int(value)
            self.debug_print(f"Result: {result}")
            return result
        except ValueError:
            self.debug_print(f"Error converting value: {value}")
            if caller.endswith("/fret"):
                raise ParseError("Invalid fret number", self.current_line)
            elif caller.endswith("/string"):
                raise ParseError("Invalid string number", self.current_line)
            else:
                raise ParseError(f"Invalid number: {value}", self.current_line)

    def _create_score(self, structure: ScoreStructure, cleaned_text: str) -> Score:
        """スコア全体の構築"""
        self.debug_print("\n=== _create_score ===")
        
        # メタデータからScoreを初期化（デフォルト値を使用）
        self.score = Score(
            title=structure.metadata.get('title', ''),
            tuning=structure.metadata.get('tuning', 'guitar'),
            beat=structure.metadata.get('beat', '4/4')
        )
        self.debug_print(f"Created score with metadata: title='{self.score.title}', tuning='{self.score.tuning}', beat='{self.score.beat}'")
        
        # セクションがない場合は空のセクションを作成
        if not structure.sections:
            self.debug_print("No sections found, creating default section")
            default_section = SectionStructure(name="", content=[cleaned_text])  # 渡されたcleaned_textを使用
            structure.sections.append(default_section)
        
        # 各セクションの処理
        for section_structure in structure.sections:  # 変数名を変更して明確に
            self.debug_print(f"\nProcessing section: {section_structure.name}")
            current_section = Section(name=section_structure.name)
            
            # セクション内の小節を解析
            bars = self._analyze_section_bars(section_structure.content)  # SectionStructureのcontentを使用
            self.debug_print(f"Found {len(bars)} bars")
            
            # 小節をColumnに分割して追加
            current_bars = []
            for bar in bars:
                parsed_bar = self._parse_bar_line(bar.content)
                parsed_bar.is_repeat_start = bar.repeat_start
                parsed_bar.is_repeat_end = bar.repeat_end
                parsed_bar.volta_number = bar.volta_number
                current_bars.append(parsed_bar)
                
                # 4小節ごとにColumnを作成
                if len(current_bars) >= 4:
                    current_section.columns.append(Column(bars=current_bars.copy()))
                    current_bars = []
            
            # 残りの小節があればColumnを作成
            if current_bars:
                current_section.columns.append(Column(bars=current_bars))
            
            self.score.sections.append(current_section)
        
        return self.score

    def _analyze_section_bars(self, lines: List[str]) -> List[BarInfo]:
        """セクション内の小節構造を解析"""
        bars = []
        in_repeat = False
        in_volta = False
        repeat_content = False
        current_volta_number = None
        
        for line in lines:
            line = line.strip()
            
            # 空行はスキップ
            if not line:
                continue
            
            # 1行形式の繰り返し記号を処理
            if line.startswith('{ ') and line.endswith(' }'):
                content = line[2:-2].strip()
                if not content:
                    raise ParseError("Empty repeat bracket", self.current_line)
                bars.append(BarInfo(
                    content=content,
                    repeat_start=True,
                    repeat_end=True
                ))
                continue
            
            # 1行形式のn番カッコを処理
            match = re.match(r'{\s*(\d+)\s+([^}]+)\s+}(\1)', line)
            if match:
                number = int(match.group(1))
                content = match.group(2).strip()
                bars.append(BarInfo(
                    content=content,
                    volta_number=number
                ))
                continue
            
            # 繰り返し記号の開始
            if line == '{':
                if in_repeat:
                    raise ParseError("Nested repeat brackets are not allowed", self.current_line)
                in_repeat = True
                continue
            
            # 繰り返し記号の終了
            if line == '}':
                if not in_repeat:
                    raise ParseError("Unmatched closing bracket", self.current_line)
                if not repeat_content:
                    raise ParseError("Empty repeat bracket", self.current_line)
                in_repeat = False
                continue
            
            # n番カッコの開始
            if line.startswith('{') and len(line) > 1:
                try:
                    number = int(line[1:])
                    if in_volta:
                        raise ParseError("Nested volta brackets are not allowed", self.current_line)
                    current_volta_number = number
                    in_volta = True
                except ValueError:
                    pass
                continue
            
            # n番カッコの終了
            if line.endswith('}') and len(line) > 1:
                try:
                    number = int(line[:-1])
                    if not in_volta:
                        raise ParseError("Unmatched closing volta bracket", self.current_line)
                    if number != current_volta_number:
                        raise ParseError("Mismatched volta bracket numbers", self.current_line)
                    in_volta = False
                    current_volta_number = None
                except ValueError:
                    pass
                continue
            
            # 通常の小節内容
            bar = BarInfo(content=line)
            bars.append(bar)
            
            # 小節の長さをチェックは、n番カッコの中でない場合のみ行う
            if not in_volta:
                parsed_bar = self._parse_bar_line(line)
                # 和音の場合は最大のstepを使用
                max_step = 0
                current_step = 0
                for note in parsed_bar.notes:
                    if note.is_chord_start:  # 和音の開始
                        current_step = 0
                    current_step = max(current_step, note.step)
                    if not note.is_chord:  # 和音でない場合は合計に加算
                        max_step += current_step
                        current_step = 0
                if max_step > 16:  # 4/4拍子の場合
                    raise ParseError("Bar duration exceeds time signature", self.current_line)
            
            if in_repeat:
                repeat_content = True
        
        # 閉じていない括弧のチェック
        if in_repeat:
            raise ParseError("Unclosed repeat bracket", self.current_line)
        if in_volta:
            raise ParseError("Unclosed volta bracket", self.current_line)
        
        return bars

    def _parse_bar_line(self, line: str) -> Bar:
        """1行の小節内容をパース"""
        bar = Bar()
        
        # 空行の場合は空の小節を返す
        if not line:
            return bar
        
        # トークンを抽出（和音を1つのトークンとして扱う）
        tokens = []
        i = 0
        while i < len(line):
            # 空白をスキップ
            while i < len(line) and line[i].isspace():
                i += 1
            if i >= len(line):
                break
            
            # トークンの開始
            if line[i] == '(':
                # 和音の終わりを探す
                start = i
                paren_count = 1
                i += 1
                while i < len(line) and paren_count > 0:
                    if line[i] == '(':
                        paren_count += 1
                    elif line[i] == ')':
                        paren_count -= 1
                    i += 1
                # 音価があれば含める
                if i < len(line) and line[i] == ':':
                    while i < len(line) and not line[i].isspace():
                        i += 1
                tokens.append(line[start:i])
            else:
                # 通常のトークン
                start = i
                while i < len(line) and not line[i].isspace():
                    i += 1
                token = line[start:i]
                self.debug_print(f"Found token: '{token}'")
                tokens.append(token)
        
        self.debug_print(f"\n=== Tokens ===")
        self.debug_print(f"Input line: '{line}'")
        self.debug_print(f"Extracted tokens: {tokens}")
        
        # トークンを処理
        i = 0
        while i < len(tokens):
            token = tokens[i]
            self.debug_print(f"\n=== Processing token ===")
            self.debug_print(f"Token {i}: '{token}'")
            
            if token.startswith('@'):
                bar.chord = token[1:]
                i += 1
                continue
            
            # 和音の処理
            if token.startswith('('):
                # 和音の終わりを探す
                chord_notes = []
                chord_duration = None
                
                # デバッグ出力を追加
                self.debug_print(f"\n=== Processing chord token ===")
                self.debug_print(f"Token: {token}")
                
                # 括弧内の音符を取得
                if ':' in token:
                    # 音価がある場合（例：(1-0 2-0 3-0):4）
                    chord_part, duration = token.split(':')
                    chord_duration = duration
                    # 括弧を除去して音符を取得
                    notes_str = chord_part[1:chord_part.rfind(')')].strip()
                else:
                    # 音価がない場合（例：(1-0 2-0 3-0)）
                    notes_str = token[1:token.rfind(')')].strip()
                
                self.debug_print(f"Notes string: '{notes_str}'")
                self.debug_print(f"Duration: {chord_duration}")
                
                # 和音内の各音符をパース
                first_note = True
                for note_str in notes_str.split():  # 空白で分割
                    self.debug_print(f"Processing note: '{note_str}'")
                    if not note_str:  # 空文字列をスキップ
                        continue
                    
                    # 音価を一時的に保存
                    saved_duration = self.last_duration
                    
                    # 音符をパース
                    note = self._parse_note(note_str)
                    
                    # 和音全体の音価を設定
                    if chord_duration:
                        note.duration = chord_duration
                    
                    # 和音の属性を設定
                    note.is_chord = True
                    note.is_chord_start = first_note
                    first_note = False
                    
                    # 音価を復元
                    self.last_duration = saved_duration
                    
                    chord_notes.append(note)
                
                bar.notes.extend(chord_notes)
                i += 1
                continue
            
            # 通常の音符の処理
            self.debug_print(f"Processing as normal note: '{token}'")
            note = self._parse_note(token)
            if note:
                self.debug_print(f"Created note: string={note.string}, fret={note.fret}, duration={note.duration}, connect_next={note.connect_next}")
                bar.notes.append(note)
            i += 1
        
        return bar 