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
    
    def _parse_notes(self, content: str) -> List[Note]:
        """小節内容から音符のリストを生成する
        
        Args:
            content: 小節の内容
            
        Returns:
            List[Note]: 音符のリスト
        """
        notes = []
        
        # 和音トークンを正しく抽出するための正規表現パターン
        # 括弧内のすべてを1つのトークンとして扱う
        tokens = []
        current_pos = 0
        content_length = len(content)
        
        while current_pos < content_length:
            # 空白をスキップ
            while current_pos < content_length and content[current_pos].isspace():
                current_pos += 1
            
            if current_pos >= content_length:
                break
            
            # 和音（括弧で囲まれたもの）を処理
            if content[current_pos] == '(':
                bracket_depth = 1
                start_pos = current_pos
                current_pos += 1
                
                # 括弧が閉じられるまで読み進める
                while current_pos < content_length and bracket_depth > 0:
                    if content[current_pos] == '(':
                        bracket_depth += 1
                    elif content[current_pos] == ')':
                        bracket_depth -= 1
                    current_pos += 1
                
                # 和音の後に音価指定がある場合（例: (1-1 2-2):4）
                if current_pos < content_length and content[current_pos] == ':':
                    while current_pos < content_length and not content[current_pos].isspace():
                        current_pos += 1
                
                # 和音全体をトークンとして追加
                tokens.append(content[start_pos:current_pos])
            else:
                # 通常のトークン（和音以外）
                start_pos = current_pos
                
                # スペースまたは括弧が出現するまで読み進める
                while current_pos < content_length and not content[current_pos].isspace() and content[current_pos] != '(':
                    current_pos += 1
                
                tokens.append(content[start_pos:current_pos])
        
        self.debug_print(f"Tokenized content: {tokens}")
        
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
                    chord_note = self.note_builder.parse_chord_notation(token, current_duration, current_chord)
                    
                    # 音価を更新（次の音符のデフォルト値として）
                    if hasattr(chord_note, 'duration') and chord_note.duration:
                        current_duration = chord_note.duration
                    
                    # 和音は単一のNoteオブジェクトとして追加
                    notes.append(chord_note)
                else:
                    # 通常の音符の処理
                    note = self.note_builder.parse_note(token, current_duration, current_chord)
                    
                    # 音価を更新（次の音符のデフォルト値として）
                    if hasattr(note, 'duration') and note.duration:
                        current_duration = note.duration
                    
                    # 音符をリストに追加
                    notes.append(note)
            except Exception as e:
                self.debug_print(f"Error parsing token '{token}': {str(e)}")
                raise e
        
        # 音符ごとにステップ数を計算
        for note in notes:
            self.note_builder.calculate_note_step(note)
        
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