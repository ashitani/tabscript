from fractions import Fraction
from typing import List, Optional, Dict, Tuple
from ...models import Note
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
            
            parts = token.split(':')
            duration = parts[1] if len(parts) > 1 else default_duration
            
            # 音符は次の音符と接続されるか？
            connect_next = False
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
        
        # 音価を抽出
        duration = parts[1] if len(parts) > 1 else default_duration
        
        # ミュート音符の処理（X または x）
        if fret_str.upper() == 'X':
            # ミュート音符も音価を省略可能
            is_muted = True
        else:
            is_muted = False
        
        # 音符は次の音符と接続されるか？
        connect_next = False
        if duration.endswith('&'):
            connect_next = True
            duration = duration.rstrip('&')
        
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
    
    def parse_chord_notation(self, chord_token: str, chord: Optional[str] = None) -> List[Note]:
        """コード記法をパースする
        
        Args:
            chord_token: コード記法トークン（例: "(1-0 2-2 3-2):4"）
            chord: コード名
            
        Returns:
            List[Note]: 解析された音符のリスト
        """
        # 音価の抽出
        parts = chord_token.split(':')
        chord_part = parts[0]
        duration = parts[1] if len(parts) > 1 else self.last_duration
        
        # 括弧を削除
        if chord_part.startswith('(') and chord_part.endswith(')'):
            chord_content = chord_part[1:-1]  # ()を削除
        else:
            # 括弧が閉じられていない場合は、先頭の括弧だけ削除
            if chord_part.startswith('('):
                chord_content = chord_part[1:]
                # 閉じ括弧を探して削除
                if ')' in chord_content:
                    chord_content = chord_content.split(')')[0]
            else:
                chord_content = chord_part
        
        # コードの各音符を解析
        notes = []
        chord_note_tokens = chord_content.split()
        
        # コード名が指定されていない場合は"chord"を使用
        if chord is None:
            chord = "chord"
        
        for i, note_token in enumerate(chord_note_tokens):
            # 音符トークンが弦-フレット形式かチェック
            if '-' not in note_token:
                continue
            
            note = self.parse_note(note_token, duration, chord)
            
            # コード属性を設定
            note.is_chord = True
            if i == 0:
                note.is_chord_start = True
            
            notes.append(note)
        
        # 音価を更新
        self.last_duration = duration
        
        return notes
    
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