from fractions import Fraction
from typing import List, Optional, Dict, Tuple
from ...models import Bar, Note, BarInfo
from ...exceptions import ParseError
from .note import NoteBuilder
import re

class BarBuilder:
    """小節レベルの処理を担当するクラス"""
    
    def __init__(self, debug_mode: bool = False):
        """BarBuilderを初期化
        
        Args:
            debug_mode: デバッグモードの有効/無効
        """
        self.debug_mode = debug_mode
        self.current_line = 0
        self.note_builder = NoteBuilder(debug_mode)
    
    def debug_print(self, *args, **kwargs):
        """デバッグ出力を行う"""
        if self.debug_mode:
            print("DEBUG (BarBuilder):", *args, **kwargs)
    
    def set_tuning(self, tuning: str) -> None:
        """チューニング設定を変更
        
        Args:
            tuning: チューニング設定
        """
        self.note_builder.set_tuning(tuning)
    
    @property
    def last_string(self) -> int:
        """最後に使用した弦番号を取得"""
        return self.note_builder.last_string
    
    @last_string.setter
    def last_string(self, value: int) -> None:
        """最後に使用した弦番号を設定"""
        self.note_builder.last_string = value
    
    @property
    def last_duration(self) -> str:
        """最後に使用した音価を取得"""
        return self.note_builder.last_duration
    
    @last_duration.setter
    def last_duration(self, value: str) -> None:
        """最後に使用した音価を設定"""
        self.note_builder.last_duration = value
    
    def parse_bar_line(self, line) -> Bar:
        """小節行をパースしてBarオブジェクトを返す
        
        Args:
            line: パースする小節行（文字列またはBarInfoオブジェクト）
        
        Returns:
            Bar: パースされた小節オブジェクト
        """
        self.debug_print(f"Parsing bar line: {line}")
        
        # 小節オブジェクトを作成
        bar = Bar()
        
        # BarInfoオブジェクトの場合、内容を取り出す
        if isinstance(line, BarInfo) or (hasattr(line, 'content') and hasattr(line, 'repeat_start')):
            content = line.content
            
            # BarInfoから繰り返しと小節情報を取得
            if hasattr(line, 'repeat_start'):
                bar.is_repeat_start = line.repeat_start
            if hasattr(line, 'repeat_end'):
                bar.is_repeat_end = line.repeat_end
            if hasattr(line, 'volta_number'):
                bar.volta_number = line.volta_number
            if hasattr(line, 'volta_start'):
                bar.volta_start = line.volta_start
            if hasattr(line, 'volta_end'):
                bar.volta_end = line.volta_end
        else:
            content = line
        
        # n番カッコの処理
        if isinstance(content, str) and content.startswith('['):
            volta_match = re.match(r'\[(\d+)\](.*)', content)
            if volta_match:
                bar.volta_number = int(volta_match.group(1))
                bar.volta_start = True
                content = volta_match.group(2).strip()
        
        # コード名の検出
        if isinstance(content, str) and content.startswith('@'):
            # コード名を抽出
            chord_parts = content.split(' ', 1)
            chord_name = chord_parts[0][1:]  # @を除去
            bar.chord = chord_name
        
        # 音符をパース
        notes = self._parse_notes(content)
        
        # 音符にコード名が設定されていれば、バーにも設定
        if notes and notes[0].chord:
            bar.chord = notes[0].chord
        
        # 音符のステップ数を計算
        for note in notes:
            self._calculate_note_step(note)
        
        bar.notes = notes
        
        return bar
    
    def _parse_note(self, token: str, default_duration: str = "4", chord: Optional[str] = None) -> Note:
        """音符トークンをパースしてNoteオブジェクトを返す（互換性のため）
        
        Args:
            token: パースする音符トークン
            default_duration: デフォルトの音価
            chord: コード名
            
        Returns:
            Note: パースされた音符オブジェクト
        """
        # NoteBuilderに現在の状態を設定
        self.note_builder.current_line = self.current_line
        
        # 音符をパース
        return self.note_builder.parse_note(token, default_duration, chord)
    
    def _parse_notes(self, notes_str: str, chord: Optional[str] = None) -> List[Note]:
        """スペース区切りの音符をパースしてNoteのリストを返す
        
        Args:
            notes_str: パースする音符文字列
            chord: コード名
            
        Returns:
            List[Note]: パースされた音符オブジェクトのリスト
        """
        notes = []
        
        # コード名の処理
        if isinstance(notes_str, str) and notes_str.startswith('@'):
            chord_parts = notes_str.split(' ', 1)
            chord = chord_parts[0][1:]  # @を除去
            if len(chord_parts) > 1:
                notes_str = chord_parts[1]
            else:
                notes_str = ""  # コード名のみの場合は空文字列に
        
        # 和音記法の処理（括弧で囲まれた音符）
        if isinstance(notes_str, str) and '(' in notes_str and ')' in notes_str:
            # 括弧の位置を特定
            open_bracket_pos = notes_str.find('(')
            close_bracket_pos = notes_str.find(')', open_bracket_pos)
            
            # 括弧の前の部分を処理
            if open_bracket_pos > 0:
                prefix = notes_str[:open_bracket_pos].strip()
                if prefix:
                    prefix_notes = self._parse_notes(prefix, chord)
                    notes.extend(prefix_notes)
            
            # 和音部分を抽出
            chord_part = notes_str[open_bracket_pos:close_bracket_pos+1]
            
            # 音価を抽出
            if close_bracket_pos + 1 < len(notes_str) and notes_str[close_bracket_pos + 1] == ':':
                colon_pos = notes_str.find(':', close_bracket_pos)
                space_pos = notes_str.find(' ', colon_pos)
                if space_pos > 0:
                    chord_part += notes_str[close_bracket_pos+1:space_pos]
                    suffix = notes_str[space_pos+1:].strip()
                else:
                    chord_part += notes_str[close_bracket_pos+1:]
                    suffix = ""
            else:
                suffix = notes_str[close_bracket_pos+1:].strip()
            
            # 和音部分をパース
            self.note_builder.current_line = self.current_line
            chord_notes = self.note_builder.parse_chord_notation(chord_part, chord)
            
            # 和音の音符をリストに追加
            notes.extend(chord_notes)
            
            # 残りの部分を処理
            if suffix:
                suffix_notes = self._parse_notes(suffix, chord)
                notes.extend(suffix_notes)
            
            return notes
        
        # 文字列の場合のみトークン分割処理
        if isinstance(notes_str, str) and notes_str.strip():
            # 通常の音符（スペースで区切られた複数の音符）
            tokens = notes_str.split()
            for token in tokens:
                self.note_builder.current_line = self.current_line
                note = self.note_builder.parse_note(token, self.last_duration, chord)
                notes.append(note)
        
        # コード名だけを持つバーの場合
        if chord and not notes and not isinstance(notes_str, str):
            # 空のバーにコード名を設定
            bar = Bar()
            bar.chord = chord
        
        return notes
    
    def _calculate_note_step(self, note: Note) -> None:
        """音符のステップ数を計算する（互換性のため）
        
        Args:
            note: ステップ数を計算する音符オブジェクト
        """
        self.note_builder.calculate_note_step(note)
    
    def _calculate_note_steps(self, bar: Bar) -> None:
        """小節内の全ての音符のステップ数を計算する
        
        Args:
            bar: 計算対象の小節オブジェクト
        """
        for note in bar.notes:
            self.note_builder.calculate_note_step(note)
    
    def get_string_count(self) -> int:
        """チューニング設定から弦の数を取得（互換性のため）
        
        Returns:
            int: 弦の数
        """
        return self.note_builder.get_string_count() 