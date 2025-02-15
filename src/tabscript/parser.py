from typing import List, Tuple
import re
from .models import Score, Section, Bar, Note, Column
from .exceptions import ParseError, TabScriptError
from fractions import Fraction

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

    def parse(self, source: str) -> Score:
        """Parse a TabScript file or string and return a Score object"""
        self.score = Score(title="", beat="4/4")
        self.current_section = None
        self.current_line = 0
        self.last_string = 1
        self.last_duration = "4"

        if '\n' in source:  # 文字列として直接パース
            lines = source.splitlines()
        else:  # ファイルパスとして扱う
            with open(source, 'r') as f:
                lines = f.readlines()

        self._parse_lines(lines)
        
        # スコアの構造を詳細にダンプ
        self.debug_print("\nDEBUG: Score structure:")
        for section in self.score.sections:
            self.debug_print(f"\nSection: {section.name}")
            for i, column in enumerate(section.columns):
                self.debug_print(f"  Column {i}: bars_per_line={column.bars_per_line}, {len(column.bars)} bars")
                for j, bar in enumerate(column.bars):
                    self.debug_print(f"    Bar {j}: resolution={bar.resolution}, {len(bar.notes)} notes")
                    for k, note in enumerate(bar.notes):
                        chord_info = f", chord={note.chord}" if note.chord else ""
                        step_info = f", step={note.step}"
                        if note.is_chord:
                            self.debug_print(f"      Note {k}: string={note.string}, fret={note.fret}, duration={note.duration}{step_info}, is_chord=True{chord_info}")
                            for l, chord_note in enumerate(note.chord_notes):
                                self.debug_print(f"        Chord note {l}: string={chord_note.string}, fret={chord_note.fret}")
                        else:
                            rest_info = ", is_rest=True" if note.is_rest else ""
                            move_info = ""
                            if note.is_up_move:
                                move_info = ", up_move"
                            elif note.is_down_move:
                                move_info = ", down_move"
                            self.debug_print(f"      Note {k}: string={note.string}, fret={note.fret}, duration={note.duration}{step_info}{chord_info}{rest_info}{move_info}")
        
        return self.score

    def _parse_lines(self, lines: List[str]):
        """Parse lines of TabScript"""
        current_bars = []  # 現在の行の小節リスト
        bars_per_line = 4  # デフォルト値
        
        for line in lines:
            self.current_line += 1
            line = line.strip()
            
            if not line or line.startswith('#'):  # 空行と行頭#のコメント行をスキップ
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
            
            if not self.current_section:
                raise ParseError("Bar must be inside a section", self.current_line)
            
            # 小節をパース
            bar = self._parse_bar(line)
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

    def _parse_bar(self, line: str) -> Bar:
        """Parse a bar line"""
        bar = Bar()
        
        # 分解能を計算（その小節内の最小の音価で決定）
        min_duration = int(self.last_duration.rstrip('.'))  # デフォルトは直前の音価
        for token in line.split():
            if token.startswith('@'):
                continue
            if ':' in token:
                duration_str = token.split(':')[1]
                try:
                    base = self.safe_int(duration_str.rstrip('.'), "_parse_bar/duration")
                    # 不正な音価をチェック
                    if base not in [1, 2, 4, 8, 16]:
                        raise ParseError(f"Invalid note duration: {base}", self.current_line)
                    min_duration = max(min_duration, base)
                    self.debug_print(f"DEBUG: min_duration={min_duration}, base={base}")
                except ValueError:
                    raise ParseError(f"Invalid duration: {duration_str}", self.current_line)
        bar.resolution = min_duration
        self.debug_print(f"DEBUG: final resolution={bar.resolution}")
        
        # 音符をパース
        notes = self._parse_notes(line)
        total_steps = 0
        for note in notes:
            # ステップ数を計算
            duration_str = note.duration
            base = self.safe_int(duration_str.rstrip('.'), "_parse_bar/step")
            steps = bar.resolution // base
            if duration_str.endswith('.'):
                steps = (steps * 3) // 2  # 付点の場合は1.5倍
            note.step = steps
            total_steps += steps
            bar.notes.append(note)
            
            self.debug_print(f"DEBUG: note={note.string}-{note.fret}:{note.duration}, steps={steps}, total_steps={total_steps}")
        
        # 小節の長さをチェック
        bar_length = Fraction(total_steps, bar.resolution)
        # 拍子記号から分数を取得（例: "4/4" -> Fraction(4, 4), "3/4" -> Fraction(3, 4)）
        numerator, denominator = map(int, self.score.beat.split('/'))
        max_length = Fraction(numerator, denominator)
        
        if bar_length > max_length:
            raise ParseError("Bar duration exceeds time signature", self.current_line)
        
        return bar

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
            
            if char == '@':
                # コードトークンの開始
                if current_token:
                    tokens.append(current_token.strip())
                current_token = char
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
            elif not in_chord and char.isspace():
                if current_token:
                    tokens.append(current_token.strip())
                    current_token = ""
            else:
                current_token += char
            i += 1
            self.debug_print(f"  char: '{notes_str[i-1]}', current_token: '{current_token}', in_chord: {in_chord}")
        
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

    def _parse_note(self, token: str) -> Note:
        """Parse a single note token"""
        self.debug_print(f"\nParsing note token: {token}")
        self.debug_print(f"Current last_duration: {self.last_duration}")
        
        # 和音の場合
        if token.startswith('(') and ':' in token:
            self.debug_print(f"Detected chord token")
            # まず括弧を除去してから:で分割
            content = token[1:]  # 先頭の(を除去
            self.debug_print(f"After removing opening bracket: {content}")
            
            parts = content.split(':')
            self.debug_print(f"Parts after split by ':': {parts}")
            
            chord_token = parts[0][:-1]  # 末尾の)を除去
            self.debug_print(f"Chord token after removing closing bracket: {chord_token}")
            
            duration = parts[1] if len(parts) > 1 else self.last_duration
            self.debug_print(f"Duration: {duration}")
            
            # 音符をパース
            note_tokens = chord_token.split(None)
            self.debug_print(f"Individual note tokens: {note_tokens}")
            
            # 最初の音符を主音として扱う
            self.debug_print(f"Parsing main note: {note_tokens[0]}")
            main_note = self._parse_single_note(note_tokens[0])
            main_note.is_chord = True
            main_note.duration = duration
            
            # 残りの音符を和音の構成音として追加
            for note_token in note_tokens[1:]:
                self.debug_print(f"Parsing chord note: {note_token}")
                chord_note = self._parse_single_note(note_token)
                chord_note.duration = duration
                main_note.chord_notes.append(chord_note)
            
            return main_note
        
        # 通常の音符の場合
        self.debug_print(f"Parsing as single note")
        note = self._parse_single_note(token)
        
        # 次の音符のためにデフォルト値を更新
        if not note.is_rest:
            self.last_string = note.string
        
        return note

    def _validate_duration(self, duration: str) -> None:
        """音価の妥当性をチェック"""
        base = duration.rstrip('.')  # 付点を除去
        try:
            value = int(base)
            if value not in [1, 2, 4, 8, 16]:
                raise ParseError(f"Invalid note duration: {base}", self.current_line)
        except ValueError:
            raise ParseError(f"Invalid duration: {duration}", self.current_line)

    def _parse_single_note(self, token: str) -> Note:
        """Parse a single note (not a chord)"""
        self.debug_print(f"\n=== _parse_single_note ===")
        self.debug_print(f"Input token: {token}")
        
        # 休符の場合
        if token.startswith('r'):
            duration_part = token[1:]
            self.debug_print(f"Rest note: duration_part='{duration_part}'")
            if not duration_part:
                duration_part = self.last_duration
            self.last_duration = duration_part.rstrip('.')
            return Note(
                string=0,
                fret="0",
                duration=duration_part,
                is_rest=True
            )

        # 弦-フレット:音価 の形式をパース
        parts = token.split(':')
        note_part = parts[0]
        duration = parts[1] if len(parts) > 1 else self.last_duration
        self.debug_print(f"note_part: '{note_part}', duration: '{duration}'")
        
        # 音価のバリデーション
        self._validate_duration(duration)
        self.last_duration = duration.rstrip('.')  # 付点を除去して保存（これを戻す）
        
        # 弦移動の指定（和音の音符の場合はスキップ）
        is_up = note_part.startswith('u')
        is_down = note_part.startswith('d')
        if is_up or is_down:
            note_part = note_part[1:]
            # 弦番号を計算
            if is_up:
                string = self.last_string - 1
            else:
                string = self.last_string + 1
            
            # 弦番号の範囲チェック
            string_count = self._get_string_count()
            if string < 1 or string > string_count:
                raise ParseError(f"Invalid string number {string} after movement", self.current_line)
            
            # フレット番号を処理（付点音符の場合は.を除去）
            try:
                fret = str(self.safe_int(note_part.rstrip('.'), "_parse_single_note/fret"))
            except ValueError:
                raise ParseError(f"Invalid fret number: {note_part}", self.current_line)
        else:
            # 和音の音符または通常の音符
            if '-' in note_part:
                string_part, fret_part = note_part.split('-')
                string = self.safe_int(string_part, "_parse_single_note/string")
                # フレット部分がxまたはXの場合はそのまま、それ以外は数値として解釈
                if fret_part.upper() == 'X':
                    fret = 'X'
                else:
                    try:
                        fret = str(self.safe_int(fret_part.rstrip('.'), "_parse_single_note/fret"))
                    except ValueError:
                        raise ParseError(f"Invalid fret number: {fret_part}", self.current_line)
            else:
                string = self.last_string
                # フレット部分の処理
                if note_part.upper() == 'X':
                    fret = 'X'
                else:
                    try:
                        fret = str(self.safe_int(note_part.rstrip('.'), "_parse_single_note/fret"))
                    except ValueError:
                        raise ParseError(f"Invalid fret number: {note_part}", self.current_line)
        
        self.last_string = string  # 弦番号を記憶
        return Note(
            string=string,
            fret=fret,
            duration=duration,
            is_up_move=is_up,
            is_down_move=is_down
        )

    def render_score(self, output_path: str):
        """タブ譜をファイルとして出力"""
        if not self.score:
            raise TabScriptError("No score to render. Call parse() first.")
        
        from .renderer import Renderer
        renderer = Renderer(self.score)
        
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
        except ValueError as e:
            self.debug_print(f"Error converting value: {str(e)}")
            raise 