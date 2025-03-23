from typing import Dict, List, Optional, Tuple, Any
from fractions import Fraction
from ..exceptions import ParseError

class TabScriptValidator:
    """TabScriptの検証を行うクラス"""
    
    def __init__(self):
        """バリデータを初期化"""
        self.tuning = "guitar"  # デフォルトはギター
        self.beat = "4/4"       # デフォルトは4/4拍子
        self.current_line = 0   # 現在処理中の行番号
    
    def validate_duration(self, duration: str) -> bool:
        """音価の検証
        
        Args:
            duration: 音価を表す文字列（例: "4", "8", "16", "4."）
            
        Returns:
            bool: 有効な音価の場合はTrue
            
        Raises:
            ParseError: 無効な音価の場合
        """
        # 付点の処理
        has_dot = duration.endswith('.')
        base_duration = duration[:-1] if has_dot else duration
        
        # 有効な音価のリスト
        valid_durations = ["1", "2", "4", "8", "16", "32", "64"]
        
        if base_duration not in valid_durations:
            raise ParseError(f"Invalid duration: {duration}", self.current_line)
        
        # 二重付点以上はエラー
        if duration.count('.') > 1:
            raise ParseError(f"Invalid duration: {duration}", self.current_line)
        
        return True
    
    def validate_bar_duration(self, beat: str, total_duration: float) -> bool:
        """小節の長さを検証
        
        Args:
            beat: 拍子記号（例: "4/4", "3/4"）
            total_duration: 小節内の音符の合計長さ
            
        Returns:
            bool: 小節の長さが正しい場合はTrue
            
        Raises:
            ParseError: 小節の長さが不正な場合
        """
        expected_duration = self._calculate_expected_duration(beat)
        
        # 許容誤差（浮動小数点の誤差を考慮）
        epsilon = 0.001
        
        if total_duration < expected_duration - epsilon:
            raise ParseError(f"Bar duration is too short: {total_duration} (expected {expected_duration})", self.current_line)
        
        if total_duration > expected_duration + epsilon:
            raise ParseError(f"Bar duration is too long: {total_duration} (expected {expected_duration})", self.current_line)
        
        return True
    
    def _calculate_expected_duration(self, beat: str) -> float:
        """拍子記号から期待される小節の長さを計算
        
        Args:
            beat: 拍子記号（例: "4/4", "3/4"）
            
        Returns:
            float: 期待される小節の長さ
        """
        try:
            numerator, denominator = map(int, beat.split('/'))
            # 4/4拍子なら4、3/4拍子なら3を返す
            return numerator
        except ValueError:
            raise ParseError(f"Invalid beat format: {beat}", self.current_line)
    
    def validate_chord_notation(self, chord_notation: str) -> bool:
        """和音表記の検証
        
        Args:
            chord_notation: 和音表記（例: "(1-0 2-0 3-0):4"）
            
        Returns:
            bool: 有効な和音表記の場合はTrue
            
        Raises:
            ParseError: 無効な和音表記の場合
        """
        # 基本的な形式チェック
        if not chord_notation.startswith('(') or '):' not in chord_notation:
            raise ParseError(f"Invalid chord notation: {chord_notation}", self.current_line)
        
        # 音価の検証
        try:
            duration = chord_notation.split('):')[1]
            self.validate_duration(duration)
        except IndexError:
            raise ParseError(f"Invalid chord notation: {chord_notation}", self.current_line)
        
        return True
    
    def validate_beat(self, beat: str) -> bool:
        """拍子記号の検証
        
        Args:
            beat: 拍子記号（例: "4/4", "3/4"）
            
        Returns:
            bool: 有効な拍子記号の場合はTrue
            
        Raises:
            ParseError: 無効な拍子記号の場合
        """
        # 形式チェック
        if '/' not in beat:
            raise ParseError(f"Invalid beat format: {beat}", self.current_line)
        
        try:
            numerator, denominator = map(int, beat.split('/'))
        except ValueError:
            raise ParseError(f"Invalid beat format: {beat}", self.current_line)
        
        # サポートされている拍子のチェック
        valid_beats = [
            "4/4", "3/4", "2/4", "6/8", "9/8", "12/8"
        ]
        
        if beat not in valid_beats:
            raise ParseError(f"Invalid beat: {beat}", self.current_line)
        
        return True
    
    def validate_tuning(self, tuning: str) -> bool:
        """チューニングの検証
        
        Args:
            tuning: チューニング（例: "guitar", "bass"）
            
        Returns:
            bool: 有効なチューニングの場合はTrue
            
        Raises:
            ParseError: 無効なチューニングの場合
        """
        valid_tunings = [
            "guitar", "guitar7", "bass", "bass5", "ukulele"
        ]
        
        if tuning not in valid_tunings:
            raise ParseError(f"Invalid tuning: {tuning}", self.current_line)
        
        return True
    
    def validate_string_number(self, string_number: int) -> bool:
        """弦番号の検証
        
        Args:
            string_number: 弦番号
            
        Returns:
            bool: 有効な弦番号の場合はTrue
            
        Raises:
            ParseError: 無効な弦番号の場合
        """
        # チューニングに基づく弦の数
        string_counts = {
            "guitar": 6,
            "guitar7": 7,
            "bass": 4,
            "bass5": 5,
            "ukulele": 4
        }
        
        max_string = string_counts.get(self.tuning, 6)
        
        if string_number < 1 or string_number > max_string:
            raise ParseError(f"Invalid string number: {string_number} (max: {max_string})", self.current_line)
        
        return True
    
    def validate_fret_number(self, fret: str) -> bool:
        """フレット番号の検証
        
        Args:
            fret: フレット番号（数字またはX）
            
        Returns:
            bool: 有効なフレット番号の場合はTrue
            
        Raises:
            ParseError: 無効なフレット番号の場合
        """
        # ミュート記号の場合
        if fret.upper() == 'X':
            return True
        
        try:
            fret_num = int(fret)
            if fret_num < 0:
                raise ParseError(f"Invalid fret number: {fret}", self.current_line)
        except ValueError:
            raise ParseError(f"Invalid fret number: {fret}", self.current_line)
        
        return True
    
    def validate(self, metadata: Dict[str, str], sections: List[Dict[str, Any]]) -> None:
        """メタデータとセクション構造を検証する
        
        Args:
            metadata: メタデータ辞書
            sections: セクション構造のリスト
            
        Raises:
            ParseError: 検証エラーが発生した場合
        """
        # メタデータの検証
        self._validate_metadata(metadata)
        
        # セクションの検証
        for section in sections:
            self._validate_section(section)
            
            # 小節の検証
            if "bars" in section:
                for bar in section["bars"]:
                    self._validate_bar(bar) 