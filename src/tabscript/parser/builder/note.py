from fractions import Fraction
from typing import List, Optional, Dict, Tuple
from ...models import Note, Bar
from ...exceptions import ParseError
import re

class NoteBuilder:
    """音符レベルの処理を担当するクラス"""
    
    def __init__(self, debug_mode: bool = False):
        """NoteBuilderを初期化
        
        Args:
            debug_mode: デバッグモードの有効/無効
        """
        self.debug_mode = debug_mode
        self.current_line = 0
        self.last_string = 1  # 初期値を1に設定
        self.last_duration = "4"  # デフォルトは4分音符
        self.tuning = "guitar"  # デフォルト値
    
    def debug_print(self, *args, **kwargs):
        """デバッグ出力を行う"""
        if self.debug_mode:
            print("DEBUG (NoteBuilder):", *args, **kwargs)
    
    def set_tuning(self, tuning: str) -> None:
        """チューニング設定を変更
        
        Args:
            tuning: チューニング設定
        """
        self.tuning = tuning
    
    def parse_note(self, token: str, default_duration: str = None, chord: Optional[str] = None) -> Note:
        """音符トークンをパースしてNoteオブジェクトを返す
        
        Args:
            token: パースする音符トークン（例：3-5:8）
            default_duration: デフォルトの音価
            chord: コード名
            
        Returns:
            Note: パースされた音符オブジェクト
        """
        self.debug_print(f"parse_note: token='{token}', default_duration='{default_duration}', chord='{chord}'")
        
        # 繰り返し記号や n番括弧の場合はエラー
        if token in ['{', '}'] or re.match(r'^\{\d+$', token) or re.match(r'^\d+\}$', token):
            raise ParseError(f"繰り返し記号や n番括弧（'{token}'）は音符として解析できません", self.current_line)
        
        # デフォルト音価が指定されていない場合は前回の音価を使用
        if default_duration is None:
            default_duration = self.last_duration
        
        # 休符の処理
        if token.startswith('r'):
            # 休符を直接ここで処理
            parts = token.split(':')
            duration = parts[1] if len(parts) > 1 else default_duration
            
            # 音符は次の音符と接続されるか？
            connect_next = False
            if duration.endswith('&'):
                connect_next = True
                duration = duration.rstrip('&')
            
            note = Note(
                string=self.last_string,  # 前回の弦番号を継承
                fret="0",
                duration=duration,
                is_rest=True,
                connect_next=connect_next
            )
            
            self.last_duration = duration
            return note
        
        # 和音の処理
        if token.startswith('('):
            return self.parse_chord_notation(token, default_duration, chord)
        
        # 弦移動の処理
        if token.startswith('u') or token.startswith('d'):
            # 弦移動を処理
            is_up = token.startswith('u')
            # フレット番号を抽出（u/dの後の数字はフレット番号）
            fret_str = token[1:].split(':')[0]
            
            # フレットからも &を削除（もし含まれていたら）
            connect_next = False
            if fret_str.endswith('&'):
                connect_next = True
                fret_str = fret_str[:-1]
            
            parts = token.split(':')
            duration = parts[1] if len(parts) > 1 else default_duration
            
            # 音価からも &を削除
            if duration.endswith('&'):
                connect_next = True
                duration = duration.rstrip('&')
            
            # 弦移動（常に1弦分のみ）
            new_string = self.last_string - 1 if is_up else self.last_string + 1
            
            # 弦番号が有効範囲内かチェック
            if new_string < 1:
                raise ParseError(f"cannot move above string 1", self.current_line)
            
            # チューニングに基づいて最大弦数を取得
            max_string = 6  # デフォルトは6弦ギター
            if self.tuning == "guitar7":
                max_string = 7
            elif self.tuning in ["bass", "ukulele"]:
                max_string = 4
            elif self.tuning == "bass5":
                max_string = 5
            
            if new_string > max_string:
                raise ParseError(f"cannot move beyond string {max_string}", self.current_line)
            
            note = Note(
                string=new_string,
                fret=fret_str,
                duration=duration,
                is_up_move=is_up,
                is_down_move=not is_up,
                connect_next=connect_next,
                chord=chord
            )
            
            self.last_string = new_string
            self.last_duration = duration
            
            return note
        
        # 通常の音符パース
        parts = token.split(':')
        string_fret = parts[0]
        
        # `string-fret` 部分を処理
        if '-' in string_fret:
            string_parts = string_fret.split('-')
            string_num = int(string_parts[0])
            fret_str = string_parts[1]
        else:
            # 弦番号が省略されている場合は前回の弦番号を使用
            string_num = self.last_string
            fret_str = string_fret
        
        # フレットからも &を削除（もし含まれていたら）
        connect_next = False
        if fret_str.endswith('&'):
            connect_next = True
            fret_str = fret_str[:-1]  # &を取り除く
        
        # 音価を抽出
        duration = parts[1] if len(parts) > 1 else default_duration
        
        # 音価からも &を削除
        if duration.endswith('&'):
            connect_next = True
            duration = duration.rstrip('&')
        
        # ミュート音符の処理（X または x）
        if fret_str.upper() == 'X':
            # ミュート音符も音価を省略可能
            is_muted = True
        else:
            is_muted = False
        
        # デバッグ出力を追加して、&が正しく除去されていることを確認
        self.debug_print(f"After parsing: string={string_num}, fret={fret_str}, duration={duration}, connect_next={connect_next}")
        
        note = Note(
            string=string_num,
            fret=fret_str,
            duration=duration,
            is_muted=is_muted,
            connect_next=connect_next,
            chord=chord
        )
        
        self.last_string = string_num
        self.last_duration = duration
        
        return note
    
    def parse_chord_notation(self, token: str, default_duration: str = None, chord: Optional[str] = None) -> Note:
        """和音表記（括弧で囲まれた複数の音符）をパースする"""
        self.debug_print(f"parse_chord_notation: token='{token}', default_duration='{default_duration}', chord='{chord}'")
        
        # 括弧と音価の分離
        if token.startswith('(') and ')' in token:
            # 右括弧の位置を見つける
            close_bracket_pos = token.find(')')
            
            # 括弧内のコンテンツを抽出
            content_part = token[1:close_bracket_pos]
            
            # 音価の取得（括弧の後に:区切りで音価が指定されている場合）
            duration = default_duration
            connect_next = False
            if close_bracket_pos < len(token) - 1 and ':' in token[close_bracket_pos:]:
                duration_part = token[close_bracket_pos:]
                try:
                    duration = duration_part.split(':')[1]
                    # &記号の処理
                    if duration.endswith('&'):
                        connect_next = True
                        duration = duration.rstrip('&')
                except IndexError:
                    pass
            
            # コンテンツを空白で分割して各音符を取得
            notes_tokens = content_part.split()
            if not notes_tokens:
                raise ValueError(f"Empty chord notation: {token}")
            
            self.debug_print(f"Chord content: {content_part}, notes_tokens: {notes_tokens}, duration: {duration}")
            
            # 最初の音符を主音として処理
            main_note = self.parse_note(notes_tokens[0], duration, chord)
            
            # 和音フラグと接続フラグの設定
            main_note.is_chord = True
            main_note.is_chord_start = True
            main_note.chord_notes = []  # 明示的に初期化
            
            if connect_next:
                main_note.connect_next = True
            
            # 残りの音符を和音の構成音として追加
            for note_token in notes_tokens[1:]:
                chord_note = self.parse_note(note_token, duration, chord)
                chord_note.is_chord = True
                if connect_next:
                    chord_note.connect_next = True
                main_note.chord_notes.append(chord_note)
            
            self.debug_print(f"Created chord with {len(main_note.chord_notes)} additional notes")
            return main_note
        else:
            raise ValueError(f"Invalid chord notation format: {token}")
    
    def calculate_note_step(self, note: Note) -> None:
        """音符のステップ数を計算する
        
        Args:
            note: ステップ数を計算する音符オブジェクト
        """
        # 音価を解析
        duration = note.duration
        
        # タイ/スラーの記号を除去
        if '~' in duration:
            duration = duration.replace('~', '')
        if '(' in duration:
            duration = duration.replace('(', '')
        if ')' in duration:
            duration = duration.replace(')', '')
        
        # 付点の処理
        if duration.endswith('.'):
            base = int(duration[:-1])
            # 付点音符は基本の音価の1.5倍
            note.step = Fraction(4, base) * Fraction(3, 2)
        else:
            base = int(duration)
            note.step = Fraction(4, base)
    
    def get_string_count(self) -> int:
        """チューニング設定から弦の数を取得
        
        Returns:
            int: 弦の数
        """
        tuning_map = {
            "guitar": 6,
            "guitar7": 7,
            "bass": 4,
            "bass5": 5,
            "ukulele": 4
        }
        return tuning_map.get(self.tuning, 6)  # デフォルトは6弦 

    def parse_bar_line(self, line):
        """小節行を解析してBarオブジェクトを返す"""
        bar = Bar(notes=[])
        
        # 小節行をトークンに分割
        tokens = re.findall(r'\S+', line)
        
        # コード名と音価の初期設定
        current_chord = None
        current_duration = "4"  # デフォルトは4分音符
        
        # 各トークンを解析
        for token in tokens:
            # コード名の処理
            if token.startswith('@'):
                current_chord = token[1:]  # @を除去してコード名を抽出
                continue
            
            try:
                # 和音表記の場合
                if token.startswith('(') and ')' in token:
                    chord_note = self.parse_chord_notation(token, current_duration, current_chord)
                    # 音価を更新（次の音符のデフォルト値として）
                    if chord_note.duration:
                        current_duration = chord_note.duration
                    
                    # 和音をバーに追加
                    bar.notes.append(chord_note)
                    continue
                
                # 通常の音符の処理
                note = self.parse_note(token, current_duration, current_chord)
                
                # 音価を更新（次の音符のデフォルト値として）
                if note.duration:
                    current_duration = note.duration
                
                # 音符をバーに追加
                bar.notes.append(note)
            except Exception as e:
                self.debug_print(f"Error parsing token '{token}': {str(e)}")
                raise e
        
        return bar 