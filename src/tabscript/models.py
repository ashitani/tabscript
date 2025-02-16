from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Note:
    string: int
    fret: str  # intからstrに変更（数値またはX）
    duration: str
    chord: Optional[str] = None  # コード名を追加
    is_rest: bool = False
    is_up_move: bool = False
    is_down_move: bool = False
    is_chord: bool = False
    is_chord_start: bool = False  # 追加
    chord_notes: List['Note'] = None
    is_muted: bool = False
    step: int = 0  # resolution単位での長さ
    connect_next: bool = False  # スラー/タイ用のフラグ

    def __post_init__(self):
        if self.chord_notes is None:
            self.chord_notes = []
        # フレット番号の正規化
        if isinstance(self.fret, str) and self.fret.upper() == 'X':
            self.fret = 'X'
            self.is_muted = True

@dataclass
class Bar:
    notes: List[Note] = None
    chord: Optional[str] = None
    resolution: int = 16
    # 繰り返し関連のフィールドを追加
    is_repeat_start: bool = False
    is_repeat_end: bool = False
    volta_number: Optional[int] = None

    def __post_init__(self):
        if self.notes is None:
            self.notes = []

@dataclass
class Column:
    bars: List[Bar]
    bars_per_line: int = 4  # この行の小節数
    beat: str = "4/4"       # この行の拍子

@dataclass
class Section:
    name: str
    columns: List[Column] = None  # 行のリスト

    def __post_init__(self):
        if self.columns is None:
            self.columns = []
    
    @property
    def bars(self) -> List[Bar]:
        """このセクションの全ての小節を返す"""
        return [bar for column in self.columns for bar in column.bars]

@dataclass
class Score:
    title: str = ""
    tuning: str = "guitar"
    beat: str = "4/4"  # デフォルトは4/4拍子
    sections: List[Section] = None

    def __post_init__(self):
        if self.sections is None:
            self.sections = []
    
    @property
    def bars(self) -> List[Bar]:
        """全ての小節を返す"""
        return [bar for section in self.sections for bar in section.bars]

@dataclass
class BarInfo:
    """小節の構造情報"""
    content: str
    repeat_start: bool = False
    repeat_end: bool = False
    volta_number: Optional[int] = None
    volta_start: bool = False  # n番カッコの開始
    volta_end: bool = False    # n番カッコの終了 