from typing import List, Tuple, Optional, Dict, Union
from pathlib import Path
import re
from .models import Score, Section, Bar, Note, Column
from .exceptions import ParseError, TabScriptError
from fractions import Fraction
from dataclasses import dataclass
import os
import sys

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
    def __init__(self, debug_mode=False, debug_level=0, skip_validation=False):
        """パーサーの初期化
        
        Args:
            debug_mode: デバッグモードの有効/無効
            debug_level: デバッグレベル（0-3）
            skip_validation: 検証をスキップするかどうか
        """
        self.debug_mode = debug_mode
        self.debug_level = debug_level
        self.skip_validation = skip_validation
        self.score = None
        self.current_section = None
        self.current_line = 0
        self.last_string = 0
        self.last_duration = "4"  # デフォルトは4分音符
        self.bars_per_line = 4  # デフォルトは1行あたり4小節

    def debug_print(self, *args, level: int = 1, **kwargs):
        """デバッグ出力を行う
        
        Args:
            *args: 出力する内容
            level: このメッセージのデバッグレベル（1: 基本情報、2: 詳細情報、3: 全情報）
            **kwargs: print関数に渡す追加の引数
        """
        if self.debug_mode and level <= self.debug_level:
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
                if line.endswith("'''") or line.startswith('"""'):
                    self.debug_print("Found multiline comment end")
                    in_multiline_comment = False
                continue
            
            # 行コメントをスキップ
            if line.startswith('#'):
                self.debug_print("Skipping line starting with #")
                continue
            
            # 複数行コメントの開始
            if line.startswith("'''") or line.startswith('"""'):
                self.debug_print("Found multiline comment start")
                in_multiline_comment = True
                continue
            
            # 行末コメントを除去
            if '#' in line:
                comment_pos = line.find('#')
                # シャープ記号がクォート内にある場合はコメントとみなさない
                in_quote = False
                for i in range(comment_pos):
                    if line[i] == '"' and (i == 0 or line[i-1] != '\\'):
                        in_quote = not in_quote
                
                if not in_quote:  # クォート外のシャープ記号はコメント
                    self.debug_print(f"Removing end-of-line comment at position {comment_pos}")
                    line = line[:comment_pos].strip()
                    if not line:  # コメント除去後に空行になった場合はスキップ
                        self.debug_print("Line is empty after comment removal, skipping")
                        continue
            
            self.debug_print(f"Adding line: '{line}'")
            processed_lines.append(line)
        
        result = '\n'.join(processed_lines)
        self.debug_print(f"\nFinal result:\n{result}")
        return result

    def parse(self, input_data: str) -> Score:
        """タブ譜テキストをパースしてScoreオブジェクトを返す"""
        self.debug_print("\n=== parse ===", level=1)
        self.debug_print(f"Input data: {input_data[:100]}{'...' if len(input_data) > 100 else ''}", level=2)
        
        # ファイルパスが渡された場合はファイルを読み込む
        if not input_data.startswith('$') and not input_data.startswith('[') and '\n' not in input_data:
            try:
                self.debug_print(f"Loading file: {input_data}", level=1)
                with open(input_data, 'r', encoding='utf-8') as f:
                    text = f.read()
                self.debug_print(f"File loaded, size: {len(text)} bytes", level=2)
            except FileNotFoundError:
                raise ParseError(f"File not found: {input_data}", 0)
        else:
            text = input_data
        
        # 前処理
        self.debug_print("Starting text preprocessing", level=1)
        text = self._clean_text(text)
        self.debug_print(f"After cleaning: {len(text)} bytes", level=2)
        text = self._normalize_volta_brackets(text)
        self.debug_print(f"After normalizing volta brackets: {len(text)} bytes", level=2)
        
        # 構造解析
        self.debug_print("Starting structure extraction", level=1)
        structure = self._extract_structure(text)
        self.debug_print(f"Structure extracted: {len(structure.sections)} sections", level=1)
        for i, section in enumerate(structure.sections):
            self.debug_print(f"Section {i}: {section.name}, {len(section.content)} lines", level=2)
            if self.debug_level >= 3:
                for j, line in enumerate(section.content):
                    self.debug_print(f"  Line {j}: {line}", level=3)
        
        # スコア構築
        self.debug_print("Starting score construction", level=1)
        self.score = self._create_score(structure, text)
        self.debug_print(f"Score constructed: {len(self.score.sections)} sections", level=1)
        for i, section in enumerate(self.score.sections):
            self.debug_print(f"Section {i}: {section.name}, {len(section.columns)} columns", level=2)
            for j, column in enumerate(section.columns):
                self.debug_print(f"  Column {j}: {len(column.bars)} bars", level=2)
                for k, bar in enumerate(column.bars):
                    self.debug_print(f"    Bar {k}: {len(bar.notes)} notes", level=3)
                    for l, note in enumerate(bar.notes):
                        self.debug_print(f"      Note {l}: string={note.string}, fret={note.fret}, duration={note.duration}, step={note.step}", level=3)
        
        return self.score

    def _load_source(self, source: Union[str, Path]) -> str:
        """ファイルパスまたはテキストから入力を読み込む"""
        if '\n' in source:
            return source
        with open(source, 'r') as f:
            return f.read()
    
    def _clean_text(self, text: str) -> str:
        """
        不要な空行とコメントを除去
        """
        # 複数行コメントを除去（未終了のものも含む）
        text = re.sub(r"'''.*?'''|'''.*$", "", text, flags=re.DOTALL)
        text = re.sub(r'""".*?"""|""".*$', "", text, flags=re.DOTALL)
        
        lines = text.splitlines()
        # 行コメントと空行を除去
        lines = [re.sub(r'#.*', '', line).strip() for line in lines]
        lines = [line for line in lines if line]

        return '\n'.join(lines)
    
    def _extract_structure(self, text: str) -> ScoreStructure:
        """メタデータとセクション構造の抽出"""
        metadata = {}
        sections = []
        current_section = None
        
        lines = text.split('\n')
        i = 0
        
        # メタデータの処理
        while i < len(lines):
            line = lines[i].strip()
            
            # 空行はスキップ
            if not line:
                i += 1
                continue
            
            # メタデータの処理
            if line.startswith('$'):
                match = re.match(r'\$(\w+)\s*=\s*"([^"]*)"', line)
                if not match:
                    raise ParseError("Invalid metadata format", self.current_line)
                key, value = match.group(1), match.group(2)
                metadata[key] = value
                i += 1
                continue
            
            # メタデータでなければループを抜ける
            break
        
        # セクションの処理
        while i < len(lines):
            line = lines[i].strip()
            
            # 空行はスキップ
            if not line:
                i += 1
                continue
            
            # セクションヘッダーの処理
            if line.startswith('['):
                name = line[1:-1].strip()
                current_section = SectionStructure(name=name, content=[])
                sections.append(current_section)
                i += 1
                continue
            
            # セクションヘッダーがない場合、デフォルトセクションを作成
            if current_section is None:
                self.debug_print("Creating default section", level=1)
                current_section = SectionStructure(name="", content=[])
                sections.append(current_section)
            
            # セクション内容の追加
            current_section.content.append(line)
            i += 1
        
        # セクションがない場合でも、内容があればデフォルトセクションを作成
        if len(sections) == 0 and i < len(lines):
            self.debug_print("Creating default section for remaining content", level=1)
            current_section = SectionStructure(name="", content=[])
            
            # 残りの行をすべてデフォルトセクションに追加
            while i < len(lines):
                line = lines[i].strip()
                if line:  # 空行でなければ追加
                    current_section.content.append(line)
                i += 1
            
            sections.append(current_section)
        
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
                in_chord_name = True
                i += 1
                continue

            if char == '(':
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
            note = self._parse_note(token, self.last_duration, current_chord if not in_chord else None)
            # 前と同じコードなら None を設定
            if current_chord == last_chord:
                note.chord = None
            else:
                note.chord = current_chord
                last_chord = current_chord  # 新しいコードを記憶
            notes.append(note)
        
        return notes

    def _parse_bar_line(self, line: str) -> Bar:
        """小節行をパース"""
        self.debug_print(f"\n=== _parse_bar_line ===", level=1)
        self.debug_print(f"Input: {line}", level=2)
        
        # 小節の初期化
        bar = Bar()
        
        # コード名の抽出
        chord = None
        
        # 括弧内の空白を一時的に置換して、トークン分割を正しく行う
        # 例: (1-0 2-0 3-0):4 → (1-0_2-0_3-0):4
        def replace_spaces_in_brackets(text):
            result = ""
            in_bracket = False
            for char in text:
                if char == '(':
                    in_bracket = True
                    result += char
                elif char == ')':
                    in_bracket = False
                    result += char
                elif char == ' ' and in_bracket:
                    result += '_'  # 括弧内の空白を_に置換
                else:
                    result += char
            return result
        
        # 括弧内の空白を置換
        processed_line = replace_spaces_in_brackets(line)
        tokens = processed_line.split()
        
        # 置換した_を元の空白に戻す
        tokens = [token.replace('_', ' ') for token in tokens]
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            self.debug_print(f"Processing token: {token}", level=2)
            
            # コード名の処理
            if token.startswith('@'):
                chord = token[1:]  # @を除去
                bar.chord = chord
                self.debug_print(f"Found chord: {chord}", level=2)
                i += 1
                continue
            
            # 小節線の処理
            if token == '|':
                self.debug_print("Found bar line", level=2)
                i += 1
                continue
            
            # リピート開始の処理
            if token == '|:':
                bar.repeat_start = True
                self.debug_print("Found repeat start", level=2)
                i += 1
                continue
            
            # リピート終了の処理
            if token == ':|':
                bar.repeat_end = True
                self.debug_print("Found repeat end", level=2)
                i += 1
                continue
            
            # ボルタブラケットの処理
            if token.startswith('[') and token.endswith(']'):
                try:
                    volta_number = int(token[1:-1])
                    bar.volta_number = volta_number
                    bar.volta_start = True
                    self.debug_print(f"Found volta bracket: {volta_number}", level=2)
                except ValueError:
                    raise ParseError(f"Invalid volta bracket: {token}", self.current_line)
                i += 1
                continue
            
            # 和音記法の処理（括弧で囲まれた音符）
            if token.startswith('(') and ')' in token:
                self.debug_print("Processing chord notation", level=2)
                
                # 括弧内の音符と音価を分離
                chord_part, *rest = token.split(')')
                chord_notes_str = chord_part[1:]  # 先頭の'('を除去
                
                # 音価の取得
                duration = self.last_duration
                if rest and ':' in rest[0]:
                    duration = rest[0].split(':')[1]
                    
                    # タイ・スラーの処理
                    if duration.endswith('&'):
                        connect_next = True
                        duration = duration[:-1]
                    else:
                        connect_next = False
                    
                    self._validate_duration(duration)
                    self.last_duration = duration
                
                # 括弧内の音符をパース
                chord_notes = []
                for note_str in chord_notes_str.split():
                    # 弦-フレット形式の解析
                    if '-' in note_str:
                        string_fret = note_str.split('-')
                        string = int(string_fret[0])
                        fret = string_fret[1].upper()  # フレット番号を大文字に統一
                        
                        # ミュート音の処理
                        is_muted = (fret == "X")
                        
                        # フレット番号の検証（ミュート音以外）
                        if not is_muted:
                            self._validate_fret_number(fret)
                        
                        # 弦番号を更新
                        self.last_string = string
                        
                        note = Note(
                            string=string,
                            fret=fret,
                            duration=duration,
                            chord=chord,
                            is_muted=is_muted,
                            is_chord=True,
                            is_chord_start=(len(chord_notes) == 0),
                            connect_next=connect_next if len(chord_notes) == 0 else False
                        )
                        chord_notes.append(note)
                
                # 和音の音符をバーに追加
                for note in chord_notes:
                    bar.notes.append(note)
                
                i += 1
                continue
            
            # 休符の処理
            if token.lower() == 'r':
                # 音価が指定されていない休符の場合、直前の音価を継承
                duration = self.last_duration
                
                # 休符を表す音符を作成
                note = Note(
                    string=0,
                    fret="0",
                    duration=duration,
                    chord=chord,
                    is_rest=True
                )
                
                # 音符のステップ数を計算
                self._calculate_note_step(note)
                
                bar.notes.append(note)
                i += 1
                continue
            elif token.lower().startswith('r') and len(token) > 1:
                # 音価が指定されている休符の処理
                duration = token[1:]  # 'r'を除去
                self._validate_duration(duration)
                
                # 休符を表す音符を作成
                note = Note(
                    string=0,
                    fret="0",
                    duration=duration,
                    chord=chord,
                    is_rest=True
                )
                
                # 音符のステップ数を計算
                self._calculate_note_step(note)
                
                bar.notes.append(note)
                self.last_duration = duration
                i += 1
                continue
            
            # 通常の音符
            parts = token.split(':')
            note_part = parts[0]
            duration = parts[1] if len(parts) > 1 else self.last_duration
            
            # タイ・スラーの処理
            connect_next = False
            if duration.endswith('&'):
                connect_next = True
                duration = duration[:-1]
            
            self._validate_duration(duration)
            
            # 弦-フレット形式の解析
            if '-' in note_part:
                string_fret = note_part.split('-')
                string = int(string_fret[0])
                fret = string_fret[1].upper()  # フレット番号を大文字に統一
                
                # タイ・スラーの処理（フレット番号の後にある場合）
                if fret.endswith('&'):
                    connect_next = True
                    fret = fret[:-1]  # &を除去
                
                # 0-0は休符として扱う
                is_rest = (string == 0 and fret == "0")
                
                # ミュート音の処理
                is_muted = (fret == "X")
                
                # フレット番号の検証（ミュート音以外）
                if not is_muted and not is_rest:
                    self._validate_fret_number(fret)
                
                # 弦番号を更新
                if not is_rest:  # 休符の場合は弦番号を更新しない
                    self.last_string = string
                
                note = Note(
                    string=string,
                    fret=fret,
                    duration=duration,
                    chord=chord,
                    is_rest=is_rest,
                    is_muted=is_muted,
                    connect_next=connect_next
                )
                bar.notes.append(note)
            
            # 弦移動の処理
            elif note_part.startswith('u') or note_part.startswith('d'):
                direction = note_part[0]
                try:
                    fret = note_part[1:]  # 移動後のフレット番号
                    
                    # タイ・スラーの処理
                    if fret.endswith('&'):
                        connect_next = True
                        fret = fret[:-1]  # &を除去
                    
                    # 弦番号の計算
                    if direction == 'u':
                        string = self.last_string - 1  # 1弦上に移動
                    else:  # direction == 'd'
                        string = self.last_string + 1  # 1弦下に移動
                        
                    # 弦番号の範囲チェック
                    if string < 1:
                        raise ParseError(f"Invalid string movement: {note_part} (results in string {string})", self.current_line)
                    
                    # チューニングに基づいて弦の数を決定
                    if self.score.tuning == "guitar":
                        max_strings = 6
                    elif self.score.tuning == "bass":
                        max_strings = 4
                    elif self.score.tuning == "ukulele":
                        max_strings = 4
                    elif self.score.tuning == "guitar7":
                        max_strings = 7
                    elif self.score.tuning == "bass5":
                        max_strings = 5
                    else:
                        max_strings = 6  # デフォルト
                    
                    # 弦番号の範囲チェック（下限）
                    if string > max_strings:
                        raise ParseError(f"Invalid string movement: {note_part} (results in string {string})", self.current_line)
                    
                    # 弦番号を更新
                    self.last_string = string
                    
                    note = Note(
                        string=string,
                        fret=fret,
                        duration=duration,
                        chord=chord,
                        is_up_move=(direction == 'u'),
                        is_down_move=(direction == 'd'),
                        connect_next=connect_next
                    )
                    bar.notes.append(note)
                except ValueError:
                    raise ParseError(f"Invalid string movement: {note_part}", self.current_line)
            
            # フレット番号のみの場合（前の弦番号を継承）
            else:
                fret = note_part.upper()
                
                # タイ・スラーの処理
                if fret.endswith('&'):
                    connect_next = True
                    fret = fret[:-1]  # &を除去
                
                # ミュート音の処理
                is_muted = (fret == "X")
                
                # フレット番号の検証（ミュート音以外）
                if not is_muted:
                    self._validate_fret_number(fret)
                
                note = Note(
                    string=self.last_string,
                    fret=fret,
                    duration=duration,
                    chord=chord,
                    is_muted=is_muted,
                    connect_next=connect_next
                )
                bar.notes.append(note)
            
            # 音価を更新
            self.last_duration = duration
            
            i += 1
        
        # 音符のステップ数を計算
        self._calculate_note_steps(bar)
        
        # 小節の長さを検証
        if not self.skip_validation:
            self._validate_bar_duration(bar)
        
        return bar

    def _parse_note(self, token: str, default_duration: str = "4", chord: Optional[str] = None) -> Note:
        """音符トークンをパース"""
        self.debug_print(f"Processing token: {token}", level=3)
        
        # コード形式の音符（括弧で囲まれた複数の音符）
        if token.startswith('(') and ')' in token:
            self.debug_print("Processing as chord notation", level=3)
            
            # 括弧内の音符と音価を分離
            chord_part, *rest = token.split(')')
            chord_notes_str = chord_part[1:]  # 先頭の'('を除去
            
            # 音価の取得
            duration = default_duration
            if rest and ':' in rest[0]:
                duration = rest[0].split(':')[1]
                self.debug_print(f"Chord duration: {duration}", level=3)
            
            # 括弧内の音符をパース
            chord_notes = []
            for note_str in chord_notes_str.split():
                # コード内の音符は音価を持たない（コード全体の音価を使用）
                if ':' in note_str:
                    note_str = note_str.split(':')[0]
                
                # 個々の音符をパース
                note = self._parse_note(note_str, duration, chord)
                note.duration = duration  # コード全体の音価を設定
                note.is_chord = True  # コードの一部であることを明示
                chord_notes.append(note)
            
            # コードの先頭音符を返す（他の音符はchord_notesに格納）
            if chord_notes:
                main_note = chord_notes[0]
                main_note.is_chord_start = True  # コードの先頭音符であることを明示
                main_note.chord_notes = chord_notes[1:]  # 先頭以外の音符
                self.debug_print(f"Created chord with {len(chord_notes)} notes, duration={main_note.duration}", level=3)
                return main_note
            else:
                raise ParseError(f"Empty chord notation: {token}", self.current_line)
        
        # 休符の処理
        if token.lower() == 'r':
            self.debug_print("Processing as rest with inherited duration", level=3)
            return Note(
                string=0,
                fret="0",
                duration=default_duration,
                chord=chord,
                is_rest=True
            )
        elif token.lower().startswith('r'):
            self.debug_print("Processing as rest with specified duration", level=3)
            duration = token[1:] if len(token) > 1 else default_duration
            self._validate_duration(duration)
            return Note(
                string=0,
                fret="0",
                duration=duration,
                chord=chord,
                is_rest=True
            )
        
        # 弦移動の処理
        if token.startswith('u') or token.startswith('d'):
            direction = token[0]
            try:
                fret = token[1:].split(':')[0]  # 移動後のフレット番号
                
                # 弦番号の計算
                if direction == 'u':
                    string = self.last_string - 1  # 1弦上に移動
                else:  # direction == 'd'
                    string = self.last_string + 1  # 1弦下に移動
                    
                # 弦番号の範囲チェック
                if string < 1:
                    raise ParseError(f"Invalid string movement: {token} (results in string {string})", self.current_line)
                
                # チューニングに基づいて弦の数を決定
                if self.score.tuning == "guitar":
                    max_strings = 6
                elif self.score.tuning == "bass":
                    max_strings = 4
                elif self.score.tuning == "ukulele":
                    max_strings = 4
                elif self.score.tuning == "guitar7":
                    max_strings = 7
                elif self.score.tuning == "bass5":
                    max_strings = 5
                else:
                    max_strings = 6  # デフォルト
                
                # 弦番号の範囲チェック（下限）
                if string > max_strings:
                    raise ParseError(f"Invalid string movement: {token} (results in string {string})", self.current_line)
                
                # 弦番号を更新
                self.last_string = string
                
                # 音価の取得
                if ':' in token:
                    duration = token.split(':')[1]
                else:
                    duration = default_duration
                
                # 新しい音符を作成して返す
                return Note(
                    string=string,
                    fret=fret,
                    duration=duration,
                    chord=chord,
                    is_up_move=(direction == 'u'),
                    is_down_move=(direction == 'd')
                )
            except ValueError:
                raise ParseError(f"Invalid string movement: {token}", self.current_line)
        
        # 弦-フレット形式の解析
        if '-' in token:
            string_fret = token.split('-')
            string = int(string_fret[0])
            fret = string_fret[1].upper()  # フレット番号を大文字に統一
            
            # 0-0は休符として扱う
            is_rest = (string == 0 and fret == "0")
            
            # ミュート音の処理
            is_muted = (fret == "X")
            
            # フレット番号の検証（ミュート音以外）
            if not is_muted and not is_rest:
                self._validate_fret_number(fret)
            
            # 弦番号を更新
            if not is_rest:  # 休符の場合は弦番号を更新しない
                self.last_string = string
            
            return Note(
                string=string,
                fret=fret,
                duration=default_duration,  # default_durationではなくdurationを使用
                chord=chord,
                is_rest=is_rest,
                is_muted=is_muted
            )
        
        # フレット番号のみの場合（前の弦番号を継承）
        else:
            fret = token.upper()
            
            # ミュート音の処理
            is_muted = (fret == "X")
            
            # フレット番号の検証（ミュート音以外）
            if not is_muted:
                self._validate_fret_number(fret)
            
            return Note(
                string=self.last_string,
                fret=fret,
                duration=default_duration,
                chord=chord,
                is_muted=is_muted
            )

    def _validate_string_number(self, string: int) -> bool:
        """弦番号の妥当性を検証
        
        Args:
            string: 検証する弦番号
            
        Returns:
            検証結果（True: 有効、False: 無効）
            
        Raises:
            ParseError: 無効な弦番号の場合
        """
        self.debug_print(f"Validating string number: {string}", level=3)
        
        # 検証をスキップする場合
        if self.skip_validation:
            return True
        
        # 休符の場合は弦番号0も有効
        if string == 0:
            return True
        
        # チューニングに基づいて弦の数を決定
        if self.score.tuning == "guitar":
            max_strings = 6
        elif self.score.tuning == "bass":
            max_strings = 4
        elif self.score.tuning == "ukulele":
            max_strings = 4
        elif self.score.tuning == "guitar7":
            max_strings = 7
        elif self.score.tuning == "bass5":
            max_strings = 5
        else:
            max_strings = 6  # デフォルト
        
        # 弦番号の範囲チェック
        if string < 1 or string > max_strings:
            raise ParseError(f"Invalid string number: {string} (must be between 1 and {max_strings})", self.current_line)
        
        return True

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

    def _create_score(self, structure: ScoreStructure, text: str) -> Score:
        """構造情報からScoreオブジェクトを構築"""
        self.debug_print("\n=== _create_score ===", level=1)
        
        # メタデータからスコアを初期化
        score = Score()
        # 現在のスコアとして設定（_parse_bar_lineなどで使用）
        self.score = score
        
        for key, value in structure.metadata.items():
            self.debug_print(f"Setting metadata: {key}={value}", level=2)
            if key == "title":
                score.title = value
            elif key == "tuning":
                score.tuning = value
                self._validate_tuning(value)
            elif key == "beat":
                score.beat = value
                self._validate_beat(value)
        
        self.debug_print(f"Score initialized: title='{score.title}', tuning='{score.tuning}', beat='{score.beat}'", level=1)
        
        # セクションを処理
        for section_structure in structure.sections:
            self.debug_print(f"Processing section: {section_structure.name}", level=1)
            section = Section(name=section_structure.name)
            score.sections.append(section)
            
            # 小節を解析
            bar_infos = self._analyze_section_bars(section_structure.content)
            self.debug_print(f"Found {len(bar_infos)} bars", level=2)
            
            # BarInfoからBarオブジェクトを作成
            bars = []
            for bar_info in bar_infos:
                # 小節の内容をパース
                bar = self._parse_bar_line(bar_info.content)
                
                # 繰り返しと番号括弧の情報を設定
                bar.is_repeat_start = bar_info.repeat_start
                bar.is_repeat_end = bar_info.repeat_end
                bar.volta_number = bar_info.volta_number
                bar.volta_start = bar_info.volta_start
                bar.volta_end = bar_info.volta_end
                
                # 小節の長さを検証（skip_validationがFalseの場合のみ）
                if not self.skip_validation:
                    self._validate_bar_duration(bar)
                
                bars.append(bar)
            
            self.debug_print(f"Analyzed {len(bars)} bars in section", level=2)
            
            # 小節をカラムに分割
            bars_per_line = getattr(self, 'bars_per_line', 4)  # デフォルトは4小節/行
            self.debug_print(f"Bars per line: {bars_per_line}", level=2)
            
            for i in range(0, len(bars), bars_per_line):
                column_bars = bars[i:i+bars_per_line]
                column = Column(bars=column_bars, bars_per_line=bars_per_line, beat=score.beat)
                section.columns.append(column)
                self.debug_print(f"Added column with {len(column_bars)} bars", level=2)
        
        self.debug_print(f"Score construction complete: {len(score.sections)} sections", level=1)
        return score

    def _analyze_section_bars(self, content: List[str]) -> List[BarInfo]:
        """セクション内容から小節情報を抽出
        
        Args:
            content: セクションの内容（行のリスト）
            
        Returns:
            小節情報のリスト
        """
        self.debug_print("\n=== _analyze_section_bars ===")
        self.debug_print(f"Content: {content}")
        
        bar_infos = []
        
        # 各行を処理
        i = 0
        in_volta = False
        volta_number = None
        
        while i < len(content):
            line = content[i].strip()
            self.debug_print(f"Processing line: {line}")
            
            # n番カッコの開始を検出（単独行の場合）
            if line.startswith('{') and line[1:].strip().isdigit():
                volta_number = int(line[1:].strip())
                self.debug_print(f"Found volta start: {volta_number}")
                in_volta = True
                i += 1
                continue
            
            # n番カッコの終了を検出（単独行の場合）
            if line.endswith('}') and line[:-1].strip().isdigit():
                end_volta_number = int(line[:-1].strip())
                if end_volta_number == volta_number:
                    self.debug_print(f"Found volta end: {volta_number}")
                    in_volta = False
                    volta_number = None
                    i += 1
                    continue
            
            # n番カッコ内の行を処理
            if in_volta:
                self.debug_print(f"Processing volta content: {line}")
                
                # 最後の行かどうかを確認
                is_last_volta_line = False
                if i + 1 < len(content):
                    next_line = content[i + 1].strip()
                    if next_line.endswith('}') and next_line[:-1].strip().isdigit():
                        is_last_volta_line = True
                else:
                    is_last_volta_line = True
                
                bar_info = BarInfo(
                    content=line,
                    volta_number=volta_number,
                    volta_start=(i == 1 or content[i-1].strip().startswith('{')),
                    volta_end=is_last_volta_line,
                    repeat_end=(is_last_volta_line and i + 2 < len(content) and content[i + 2].strip() == '}')
                )
                bar_infos.append(bar_info)
                i += 1
                continue
            
            # 繰り返し開始と共通部分（"{ 1-1:4 2-2:4" 形式）
            if line.startswith('{ ') and not line.endswith(' }'):
                bar_content = line[2:].strip()
                self.debug_print(f"Found repeat start: {bar_content}")
                
                bar_info = BarInfo(
                    content=bar_content,
                    repeat_start=True,
                    repeat_end=False
                )
                bar_infos.append(bar_info)
                i += 1
                continue
            
            # 繰り返し記号付きの小節（"{ 1-1:4 2-2:4 }" 形式）
            if line.startswith('{ ') and line.endswith(' }'):
                bar_content = line[2:-2].strip()
                self.debug_print(f"Found repeat bar: {bar_content}")
                
                bar_info = BarInfo(
                    content=bar_content,
                    repeat_start=True,
                    repeat_end=True
                )
                bar_infos.append(bar_info)
                i += 1
                continue
            
            # 繰り返し終了のみの小節（"3-3:4 4-4:4 }" 形式）
            if not line.startswith('{') and line.endswith(' }'):
                bar_content = line[:-2].strip()
                self.debug_print(f"Found repeat end only: {bar_content}")
                
                bar_info = BarInfo(
                    content=bar_content,
                    repeat_start=False,
                    repeat_end=True
                )
                bar_infos.append(bar_info)
                i += 1
                continue
            
            # n番カッコ付きの小節（"{1 3-3:4 4-4:4 }1" 形式）
            volta_match = re.match(r'\{(\d+) (.*) \}\d+', line)
            if volta_match:
                volta_number = int(volta_match.group(1))
                bar_content = volta_match.group(2).strip()
                self.debug_print(f"Found volta bar: {volta_number}, {bar_content}")
                
                # 繰り返し終了も含むかチェック
                is_repeat_end = False
                if i == len(content) - 1 or (i + 1 < len(content) and content[i + 1].strip() == '}'):
                    is_repeat_end = True
                
                # 連続するn番カッコを検出
                is_volta_start = True
                is_volta_end = True
                
                # 前の小節がn番カッコかチェック
                if i > 0 and len(bar_infos) > 0:
                    prev_bar = bar_infos[-1]
                    if prev_bar.volta_number == volta_number:
                        # 同じ番号のn番カッコが続いている場合
                        is_volta_start = False
                
                # 次の小節がn番カッコかチェック
                if i + 1 < len(content):
                    next_line = content[i + 1].strip()
                    next_volta_match = re.match(r'\{(\d+) (.*) \}\d+', next_line)
                    if next_volta_match and int(next_volta_match.group(1)) == volta_number:
                        # 同じ番号のn番カッコが続く場合
                        is_volta_end = False
                
                bar_info = BarInfo(
                    content=bar_content,
                    volta_number=volta_number,
                    volta_start=is_volta_start,
                    volta_end=is_volta_end,
                    repeat_end=is_repeat_end
                )
                bar_infos.append(bar_info)
                i += 1
                continue
            
            # 通常の小節
            bar_info = BarInfo(content=line)
            bar_infos.append(bar_info)
            i += 1
        
        self.debug_print(f"Found {len(bar_infos)} bars")
        return bar_infos

    def _normalize_repeat_brackets(self, text: str) -> str:
        """繰り返し記号の正規化"""
        self.debug_print("\n=== _normalize_repeat_brackets ===")
        lines = text.splitlines()
        result = []
        in_repeat = False
        repeat_content = []
        repeat_start_line = 0
        
        for i, line in enumerate(lines):
            self.debug_print(f"Processing line {i+1}: '{line}'")
            
            # 空の繰り返し記号を検出 ({ })
            if line.strip() == '{ }':
                self.debug_print(f"Empty repeat bracket detected at line {i+1}")
                raise ParseError("Empty repeat bracket", i + 1)
            
            # 繰り返し開始
            if line.strip() == '{':
                self.debug_print(f"Found repeat start at line {i+1}")
                if in_repeat:
                    raise ParseError("Nested repeat brackets are not allowed", i + 1)
                in_repeat = True
                repeat_start_line = i + 1
                repeat_content = []
                continue
            
            # 繰り返し終了
            if line.strip() == '}':
                self.debug_print(f"Found repeat end at line {i+1}")
                if not in_repeat:
                    raise ParseError("Unmatched closing repeat bracket", i + 1)
                
                # 空の繰り返しをチェック
                if not repeat_content:
                    self.debug_print(f"Empty repeat bracket detected at line {i+1}")
                    raise ParseError("Empty repeat bracket", i + 1)
                
                # 繰り返し内容を正規化
                normalized = "{ " + " ".join(repeat_content) + " }"
                self.debug_print(f"Normalized repeat: '{normalized}'")
                result.append(normalized)
                in_repeat = False
                continue
            
            # 繰り返し内の行
            if in_repeat:
                self.debug_print(f"Adding content to repeat: '{line.strip()}'")
                repeat_content.append(line.strip())
            else:
                result.append(line)
        
        # 閉じられていない繰り返し
        if in_repeat:
            raise ParseError("Unclosed repeat bracket", repeat_start_line)
        
        return '\n'.join(result)

    def _normalize_volta_brackets(self, text: str) -> str:
        """n番カッコを一行形式に変換"""
        self.debug_print("\n=== _normalize_volta_brackets ===")
        lines = text.splitlines()
        result = []
        content = []
        current_volta = None
        volta_stack = []  # n番カッコのスタック
        in_repeat = False
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            self.debug_print(f"Processing line {i+1}: '{line}'")
            
            # 繰り返し開始を検出
            if line == '{':
                self.debug_print(f"Found repeat start at line {i+1}")
                in_repeat = True
                
                # 次の行があるか確認
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    
                    # 次の行が閉じ括弧の場合は空の繰り返し
                    if next_line == '}':
                        self.debug_print(f"Empty repeat bracket detected at lines {i+1}-{i+2}")
                        raise ParseError("Empty repeat bracket", i + 1)
                    
                    # n番カッコでない場合は内容と結合
                    if not (next_line.startswith('{') and len(next_line) > 1 and next_line[1].isdigit()):
                        result.append(f"{{ {next_line}")
                        i += 2
                        continue
                    else:
                        result.append("{ ")
                        i += 1
                        continue
                else:
                    # 次の行がない場合は閉じられていない繰り返し
                    raise ParseError("Unclosed repeat bracket", i + 1)
            
            # 繰り返し終了を処理
            if line == '}':
                self.debug_print(f"Found repeat end at line {i+1}")
                in_repeat = False
                # 最後の行の場合、前の行に追加
                if result:
                    result[-1] = result[-1] + " }"
                i += 1
                continue
            
            # n番カッコの開始を検出
            if line.startswith('{') and len(line) > 1 and line[1].isdigit():
                try:
                    volta_number = int(line[1])
                    self.debug_print(f"Found volta start: {volta_number}")
                    
                    # n番カッコの入れ子をチェック
                    if current_volta is not None:
                        # 既にn番カッコ内にいる場合は入れ子のn番カッコとなるためエラー
                        raise ParseError("Nested volta brackets are not allowed", i + 1)
                    
                    current_volta = volta_number
                    volta_stack.append(volta_number)  # スタックに追加
                    
                    # 複数行にまたがるn番カッコを処理
                    j = i + 1
                    volta_content = []
                    found_end = False
                    
                    while j < len(lines):
                        volta_line = lines[j].strip()
                        
                        # n番カッコの終了を検出（1}形式）
                        if volta_line.startswith(f"{volta_number}}}") or volta_line == f"{volta_number}":
                            found_end = True
                            break
                        
                        # n番カッコの終了を検出（}1形式）
                        if volta_line.startswith(f"}}") and len(volta_line) > 1 and volta_line[1].isdigit():
                            end_number = int(volta_line[1])
                            if end_number != volta_number:
                                # 番号不一致エラー
                                raise ParseError("Mismatched volta bracket numbers", j + 1)
                            found_end = True
                            break
                        
                        # 他の形式のn番カッコ終了を検出
                        if len(volta_line) > 0 and volta_line[0].isdigit() and volta_line[1:] == "}":
                            end_number = int(volta_line[0])
                            if end_number != volta_number:
                                # 番号不一致エラー
                                raise ParseError("Mismatched volta bracket numbers", j + 1)
                            found_end = True
                            break
                        
                        volta_content.append(volta_line)
                        j += 1
                    
                    # 閉じられていないn番カッコをチェック
                    if not found_end:
                        raise ParseError("Unclosed volta bracket", i + 1)
                    
                    # 各行を個別のn番カッコとして処理
                    for k, content_line in enumerate(volta_content):
                        result.append(f"{{{volta_number} {content_line} }}{volta_number}")
                    
                    # n番カッコの終了行をスキップ
                    i = j + 1
                    current_volta = None
                    volta_stack.pop()  # スタックから削除
                    continue
                except ValueError:
                    result.append(line)
                    i += 1
                    continue
            
            # n番カッコの終了を検出 (1} 形式 - 生データ形式)
            if len(line) > 0 and line[0].isdigit() and (line[1:] == "}" or line == f"{line[0]}"):
                try:
                    number = int(line[0])
                    self.debug_print(f"Found volta end (original format): {number}")
                    if number != current_volta:
                        raise ParseError("Mismatched volta bracket numbers", i + 1)
                    if not content:
                        raise ParseError("Empty volta bracket", i + 1)
                    
                    # 正規化された形式に変換
                    normalized = f"{{{current_volta} {' '.join(content)} }}{current_volta}"
                    result.append(normalized)
                    current_volta = None
                    volta_stack.pop()  # スタックから削除
                    i += 1
                    continue
                except ValueError:
                    result.append(line)
                    i += 1
                    continue
            
            # n番カッコの終了を検出 (}1 形式 - 正規化済み形式)
            if line.startswith('}') and len(line) > 1 and line[1].isdigit():
                try:
                    number = int(line[1])
                    self.debug_print(f"Found volta end (normalized format): {number}")
                    if number != current_volta:
                        raise ParseError("Mismatched volta bracket numbers", i + 1)
                    if not content:
                        raise ParseError("Empty volta bracket", i + 1)
                    
                    normalized = f"{{{current_volta} {' '.join(content)} }}{current_volta}"
                    result.append(normalized)
                    current_volta = None
                    volta_stack.pop()  # スタックから削除
                    i += 1
                    continue
                except ValueError:
                    result.append(line)
                    i += 1
                    continue
            
            # 内容の収集
            if current_volta is not None:
                content.append(line)
            else:
                result.append(line)
            i += 1
        
        # 閉じられていないn番カッコをチェック
        if current_volta is not None:
            raise ParseError("Unclosed volta bracket", len(lines))
        
        # 閉じられていない繰り返し記号をチェック
        if in_repeat:
            raise ParseError("Unclosed repeat bracket", len(lines))
        
        return '\n'.join(result)

    def _calculate_note_steps(self, bar: Bar) -> None:
        """小節内の音符のステップ数を計算
        
        Args:
            bar: ステップ数を計算する小節
        """
        self.debug_print(f"Calculating note steps", level=2)
        
        for note in bar.notes:
            # stepが設定されていない場合は、durationから計算
            if not hasattr(note, 'step') or note.step == 0:
                self._calculate_note_step(note)
        
    def _calculate_note_step(self, note: Note) -> None:
        """音符のステップ数を計算
        
        Args:
            note: ステップ数を計算する音符
        """
        duration = note.duration
        
        # 付点の処理
        has_dot = duration.endswith('.')
        if has_dot:
            base_duration = duration[:-1]
        else:
            base_duration = duration
        
        # 基本ステップ数の計算（4分音符を1とする）
        base_steps = {
            "1": Fraction(4),   # 全音符
            "2": Fraction(2),   # 2分音符
            "4": Fraction(1),   # 4分音符
            "8": Fraction(1, 2),   # 8分音符
            "16": Fraction(1, 4),   # 16分音符
            "32": Fraction(1, 8),   # 32分音符
            "64": Fraction(1, 16)   # 64分音符
        }
        
        step = base_steps.get(base_duration, 0)
        
        # 付点の場合は1.5倍
        if has_dot:
            step *= Fraction(3, 2)
        
        note.step = step

    def _validate_bar_duration(self, bar: Bar) -> bool:
        """小節の長さが拍子記号に合っているかを検証
        
        Args:
            bar: 検証する小節
        
        Returns:
            bool: 検証結果（True: OK, False: NG）
        """
        if self.skip_validation:
            return True
        
        # 拍子記号から期待される小節の長さを計算
        beat_parts = self.score.beat.split('/')
        if len(beat_parts) != 2:
            return False
        
        numerator = int(beat_parts[0])  # 分子（1小節の拍数）
        denominator = int(beat_parts[1])  # 分母（音価の単位）
        
        # 期待される小節の長さ（ステップ数）を計算
        # 例：4/4拍子 → 4拍 × (4/4) = 4ステップ
        expected_steps = Fraction(numerator, denominator) * 4
        
        # 小節内の音符のステップ数の合計を計算
        total_steps = Fraction(0)
        for note in bar.notes:
            # 和音の場合は最初の音符のみカウント
            if not note.is_chord or note.is_chord_start:
                total_steps += note.step
        
        # 許容誤差を設定（浮動小数点の誤差を考慮）
        tolerance = Fraction(1, 1000)
        
        # 期待値と実際の値の差が許容誤差以内かを確認
        diff = abs(expected_steps - total_steps)
        
        if diff > tolerance:
            self.debug_print(f"Bar duration validation failed: expected {expected_steps}, got {total_steps}")
            return False
        
        return True

    def _validate_fret_number(self, fret: str) -> bool:
        """フレット番号の検証
        
        Args:
            fret: 検証するフレット番号
            
        Returns:
            検証結果（True: 有効、False: 無効）
            
        Raises:
            ParseError: 無効なフレット番号の場合
        """
        self.debug_print(f"Validating fret number: {fret}", level=3)
        
        # 検証をスキップする場合
        if self.skip_validation:
            return True
        
        # ミュート記号は有効
        if fret == "x":
            return True
        
        try:
            fret_num = int(fret)
            if fret_num < 0 or fret_num > 24:
                raise ParseError(f"Invalid fret number: {fret} (must be between 0-24 or 'x')", self.current_line)
            return True
        except ValueError:
            raise ParseError(f"Invalid fret number: {fret} (must be a number, 'x', or empty)", self.current_line)

    def _validate_duration(self, duration: str) -> bool:
        """音価の検証
        
        Args:
            duration: 検証する音価
            
        Returns:
            検証結果（True: 有効、False: 無効）
            
        Raises:
            ParseError: 無効な音価の場合
        """
        self.debug_print(f"Validating duration: {duration}", level=3)
        
        # 検証をスキップする場合
        if self.skip_validation:
            return True
        
        # 付点の処理
        has_dot = duration.endswith('.')
        if has_dot:
            base_duration = duration[:-1]
        else:
            base_duration = duration
        
        # 有効な音価のリスト
        valid_durations = ["1", "2", "4", "8", "16", "32", "64"]
        
        if base_duration not in valid_durations:
            raise ParseError(f"Invalid duration: {duration}", self.current_line)
        
        return True

    def _validate_beat(self, beat: str) -> bool:
        """拍子記号の検証
        
        Args:
            beat: 検証する拍子記号
            
        Returns:
            検証結果（True: 有効、False: 無効）
            
        Raises:
            ParseError: 無効な拍子記号の場合
        """
        self.debug_print(f"Validating beat: {beat}", level=3)
        
        # 検証をスキップする場合
        if self.skip_validation:
            return True
        
        # 拍子記号の形式チェック
        if '/' not in beat:
            raise ParseError(f"Invalid beat: {beat} (must be in format 'n/m')", self.current_line)
        
        try:
            numerator, denominator = beat.split('/')
            num = int(numerator)
            denom = int(denominator)
            
            if num <= 0 or denom <= 0:
                raise ParseError(f"Invalid beat: {beat} (numerator and denominator must be positive)", self.current_line)
            
            # 分母は2のべき乗であるべき
            valid_denominators = [1, 2, 4, 8, 16, 32, 64]
            if denom not in valid_denominators:
                raise ParseError(f"Invalid beat: {beat} (denominator must be a power of 2)", self.current_line)
            
            return True
        except ValueError:
            raise ParseError(f"Invalid beat: {beat} (must contain valid numbers)", self.current_line)

    def _validate_tuning(self, tuning: str) -> bool:
        """チューニングの検証
        
        Args:
            tuning: 検証するチューニング
            
        Returns:
            検証結果（True: 有効、False: 無効）
            
        Raises:
            ParseError: 無効なチューニングの場合
        """
        self.debug_print(f"Validating tuning: {tuning}", level=3)
        
        # 検証をスキップする場合
        if self.skip_validation:
            return True
        
        # 有効なチューニングのリスト
        valid_tunings = [
            "guitar", "bass", "ukulele",  # 標準チューニング
            "guitar7", "bass5"  # 拡張チューニング
        ]
        
        if tuning not in valid_tunings:
            raise ParseError(f"Invalid tuning: {tuning}", self.current_line)
        
        return True

    def _parse_metadata(self, line: str) -> None:
        """メタデータ行をパース
        
        Args:
            line: メタデータ行（$key="value"形式）
        """
        self.debug_print(f"Parsing metadata: {line}")
        
        # $key="value"形式のパース
        match = re.match(r'\$(\w+)\s*=\s*"([^"]*)"', line)
        if not match:
            raise ParseError(f"Invalid metadata format: {line}", self.current_line)
        
        key, value = match.group(1), match.group(2)
        
        # メタデータをスコアに設定
        if key == "title":
            self.score.title = value
        elif key == "tuning":
            self.score.tuning = value
            self._validate_tuning(value)
        elif key == "beat":
            self.score.beat = value
            self._validate_beat(value)
        elif key == "bars_per_line":
            try:
                bars_per_line = int(value)
                # 各セクションのカラムに設定するため、ここでは保存のみ
                self.bars_per_line = bars_per_line
            except ValueError:
                raise ParseError(f"Invalid bars_per_line value: {value}", self.current_line)
        else:
            # 未知のメタデータは無視（将来の拡張のため）
            self.debug_print(f"Unknown metadata key: {key}")