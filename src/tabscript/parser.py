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
    volta_start: bool = False
    volta_end: bool = False

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

        # 1. コメント除去フェーズ
        text = self._remove_comments(text)
        self.debug_print(f"\nAfter comment removal:\n{text}")

        # 2. 空行正規化フェーズ
        text = self._normalize_empty_lines(text)
        self.debug_print(f"\nAfter empty line normalization:\n{text}")

        # 3. 繰り返し記号の一行化フェーズ
        text = self._normalize_repeat_brackets(text)
        self.debug_print(f"\nAfter repeat bracket normalization:\n{text}")

        # 4. n番カッコの一行化フェーズ
        text = self._normalize_volta_brackets(text)
        self.debug_print(f"\nAfter volta bracket normalization:\n{text}")

        # 5. メタデータとセクション構造の抽出
        structure = self._extract_structure(text)
        self.debug_print(f"\nExtracted structure:")
        self.debug_print(f"Metadata: {structure.metadata}")
        self.debug_print(f"Sections: {[s.name for s in structure.sections]}")

        # 6. スコアの構築
        self.score = self._create_score(structure, text)

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
        """音符をパース"""
        # 休符の処理
        if token.startswith('r'):
            duration = token[1:] or self.last_duration
            step = self._duration_to_step(duration)
            return Note(
                string=0,
                fret="R",
                duration=duration,
                is_rest=True,
                step=step
            )

        # タイ・スラー記号の処理
        connect_next = False
        if token.endswith('&'):
            connect_next = True
        token = token.rstrip('&')
        
        # 音価の処理
        parts = token.split(":")
        note_part = parts[0]
        duration = parts[1] if len(parts) > 1 else self.last_duration
        
        # 移動記号の処理
        is_up_move = note_part.startswith('u')
        is_down_move = note_part.startswith('d')
        if is_up_move or is_down_move:
            note_part = note_part[1:]  # 移動記号を除去
        
        # 弦とフレットの処理
        string = self.last_string  # 前の音符から弦番号を継承
        if '-' in note_part:
            string, fret = note_part.split('-')
            try:
                string = int(string)
            except ValueError:
                raise ParseError(f"Invalid string number: {string}", self.current_line)
        else:
            fret = note_part
        
        # フレット番号の検証
        try:
            if fret.upper() != "X" and fret.upper() != "R":
                int(fret)
        except ValueError:
            raise ParseError(f"Invalid fret number: {fret}", self.current_line)
        
        # Noteオブジェクトを作成
        note = Note(
            string=string,
            fret=fret,
            duration=duration,
            is_rest=(fret.upper() == 'R'),
            connect_next=connect_next
        )
        
        # ステップ数を計算
        note.step = self._duration_to_step(duration)
        
        # 移動記号による弦番号の調整
        if is_up_move:
            note.string -= 1
        elif is_down_move:
            note.string += 1
        
        # 弦番号の範囲チェック
        if not note.is_rest:  # 休符以外の場合のみチェック
            if note.string < 1 or note.string > self._get_string_count():
                raise ParseError(f"Invalid string number: {note.string}", self.current_line)
        
        # 継承用に弦番号と音価を保存
        self.last_string = note.string  # 移動後の弦番号を保存
        self.last_duration = duration.rstrip('.')
        
        return note

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
            
            # 1行形式の繰り返し記号
            if line.startswith('{ ') and line.endswith(' }'):
                content = line[2:-2].strip()
                bar = BarInfo(
                    content=content,
                    repeat_start=True,
                    repeat_end=True
                )
                bars.append(bar)
                continue
            
            # 1行形式のn番カッコ
            match = re.match(r'{\s*(\d+)\s+([^}]+)\s+}\1', line)
            if match:
                number = int(match.group(1))
                content = match.group(2).strip()
                bar = BarInfo(
                    content=content,
                    volta_number=number,
                    volta_start=True,
                    volta_end=True
                )
                bars.append(bar)
                continue
            
            # 通常の小節内容
            bar = BarInfo(content=line)
            bars.append(bar)
        
        return bars

    def _parse_bar_line(self, line: str) -> Bar:
        """1行の小節内容をパース"""
        bar = Bar()
        current_chord = None  # 現在のコード名を保持
        
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
                current_chord = token[1:]
                i += 1
                continue
            
            # 和音の処理
            if token.startswith('('):
                # 和音の処理
                chord_parts = token.split(':')
                chord_content = chord_parts[0][1:-1].strip()  # 括弧の中身
                chord_duration = chord_parts[1] if len(chord_parts) > 1 else self.last_duration

                # 和音内の各音符をパース
                chord_notes = []
                for note_str in chord_content.split():
                    note = self._parse_note(note_str)
                    if note:
                        note.duration = chord_duration
                        note.step = self._duration_to_step(chord_duration)
                        note.is_chord = True
                        chord_notes.append(note)

                if chord_notes:
                    # 最初の音符をメインの音符として設定
                    main_note = chord_notes[0]
                    main_note.is_chord_start = True
                    main_note.chord = current_chord  # コードはメインの音符にのみ設定
                    main_note.chord_notes = chord_notes[1:]  # 2つ目以降の音符を和音ノートとして設定
                    bar.notes.append(main_note)

                self.last_duration = chord_duration.rstrip('.')
                current_chord = None  # コードをリセット
            else:
                # 通常の音符の処理
                note = self._parse_note(token)
                if note:
                    note.chord = current_chord  # コードを音符に設定
                    bar.notes.append(note)
                    current_chord = None  # コードをリセット
            i += 1
        
        # 小節の長さをチェック
        total_steps = 0
        i = 0
        while i < len(bar.notes):
            note = bar.notes[i]
            if note.is_chord:
                # 和音の場合は最初の音符のステップ数だけを加算
                chord_steps = note.step
                # 和音の残りの音符をスキップ
                while i + 1 < len(bar.notes) and bar.notes[i + 1].is_chord:
                    i += 1
                total_steps += chord_steps
            else:
                # 通常の音符
                total_steps += note.step
            i += 1

        # 拍子記号から期待されるステップ数を計算
        beat = self.score.beat
        numerator, denominator = map(int, beat.split('/'))
        expected_steps = numerator * (16 // denominator)

        self.debug_print(f"\n=== Bar duration check ===")
        self.debug_print(f"Total steps: {total_steps}")
        self.debug_print(f"Expected steps: {expected_steps}")

        if total_steps > expected_steps:
            raise ParseError("Bar duration exceeds time signature", self.current_line)

        return bar 

    def _remove_comments(self, text: str) -> str:
        """コメントを除去"""
        lines = []
        for line in text.splitlines():
            # コメント行をスキップ
            if line.strip().startswith('#'):
                continue
            # 行末コメントは処理しない（仕様外）
            lines.append(line)
        return '\n'.join(lines)

    def _normalize_empty_lines(self, text: str) -> str:
        """空行を正規化"""
        lines = text.splitlines()
        result = []
        prev_empty = False
        
        for line in lines:
            is_empty = not line.strip()
            # セクション区切りの空行は2行に
            if is_empty and not prev_empty:
                result.append('')
                result.append('')
            # 通常の空行はスキップ
            elif not is_empty:
                result.append(line)
            prev_empty = is_empty
        
        return '\n'.join(result)

    def _normalize_repeat_brackets(self, text: str) -> str:
        """繰り返し記号を一行形式に変換"""
        lines = text.splitlines()
        result = []
        content = []
        in_repeat = False
        
        for line in lines:
            line = line.strip()
            if line == '{':
                if in_repeat:
                    raise ParseError("Nested repeat brackets are not allowed", self.current_line)
                in_repeat = True
            elif line == '}' and in_repeat:
                if not content:
                    raise ParseError("Empty repeat bracket", self.current_line)
                result.append(f"{{ {' '.join(content)} }}")
                content = []
                in_repeat = False
            elif in_repeat and line:
                content.append(line)
            else:
                result.append(line)
        
        # 閉じていない繰り返しがある場合はエラー
        if in_repeat:
            raise ParseError("Unclosed repeat bracket", self.current_line)
        
        return '\n'.join(result)

    def _normalize_volta_brackets(self, text: str) -> str:
        """n番カッコを一行形式に変換"""
        lines = text.splitlines()
        result = []
        content = []
        current_volta = None
        
        self.debug_print("\n=== _normalize_volta_brackets ===")
        self.debug_print(f"Input text:\n{text}")
        
        for line in lines:
            line = line.strip()
            self.debug_print(f"Processing line: '{line}'")
            
            if line.startswith('{') and len(line) > 1:
                try:
                    # 入れ子のn番カッコをチェック
                    if current_volta is not None:
                        raise ParseError("Nested volta brackets are not allowed", self.current_line)
                    current_volta = int(line[1:])
                    content = []
                    self.debug_print(f"Found volta start: {current_volta}")
                except ValueError:
                    # 通常の繰り返し記号の場合
                    result.append(line)
            elif line.endswith('}'):
                try:
                    number = int(line[:-1])
                    if current_volta is None:
                        # n番カッコの外での終了括弧
                        result.append(line)
                    elif number == current_volta:
                        normalized = f"{{{current_volta} {' '.join(content)} }}{current_volta}"
                        self.debug_print(f"Normalized volta: {normalized}")
                        result.append(normalized)
                        current_volta = None
                    else:
                        # 番号が一致しない場合はエラー
                        raise ParseError("Mismatched volta bracket numbers", self.current_line)
                except ValueError:
                    # 通常の繰り返し記号の終了の場合
                    result.append(line)
            elif current_volta is not None and line:
                content.append(line)
                self.debug_print(f"Added content: {line}")
            else:
                result.append(line)
        
        # 閉じていないn番カッコがある場合はエラー
        if current_volta is not None:
            raise ParseError("Unclosed volta bracket", self.current_line)
        
        final_text = '\n'.join(result)
        self.debug_print(f"Output text:\n{final_text}")
        return final_text 

    def _duration_to_step(self, duration: str) -> int:
        """音価をステップ数に変換（4分音符=4ステップ）"""
        base_duration = int(duration.rstrip('.'))
        step = int(16 / base_duration)  # 16分音符=1ステップ
        if duration.endswith('.'):
            step += step // 2  # 付点の場合は1.5倍
        return step 