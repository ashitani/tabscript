from dataclasses import dataclass, field
from typing import List, Optional
from fractions import Fraction

@dataclass
class Note:
    """音符"""
    string: int  # 弦番号（1〜6）
    fret: str    # フレット番号（0〜24、またはX）
    duration: str  # 音価（4, 8, 16など）
    step: Fraction = field(default_factory=lambda: Fraction(1, 1))  # 音符の長さ（拍数）
    chord: Optional[str] = None  # コード名
    is_rest: bool = False  # 休符かどうか
    is_muted: bool = False  # ミュート音かどうか
    is_up_move: bool = False  # 上方向への弦移動かどうか
    is_down_move: bool = False  # 下方向への弦移動かどうか
    connect_next: bool = False  # 次の音符と接続するかどうか
    is_chord: bool = False  # コードの一部かどうか
    is_chord_start: bool = False  # コードの最初の音符かどうか
    chord_notes: List['Note'] = field(default_factory=list)  # コード内の他の音符への参照
    is_triplet: bool = False  # 三連符グループかどうか
    triplet_notes: List['Note'] = field(default_factory=list)  # 三連符グループ内の音符リスト
    tuplet: Optional[int] = None  # 連符の種類（3=三連符, 5=五連符など）

    def __post_init__(self):
        if self.chord_notes is None:
            self.chord_notes = []
        if self.triplet_notes is None:
            self.triplet_notes = []
        # フレット番号の正規化
        if isinstance(self.fret, str) and self.fret.upper() == 'X':
            self.fret = 'x'  # 小文字で統一
            self.is_muted = True

@dataclass
class Bar:
    """小節"""
    notes: List[Note] = field(default_factory=list)  # 音符のリスト
    beat: str = "4/4"  # 拍子
    resolution: int = 16  # 分解能
    is_repeat_start: bool = False  # 繰り返し開始かどうか
    is_repeat_end: bool = False  # 繰り返し終了かどうか
    repeat_number: Optional[int] = None  # 反復番号（1, 2など）
    volta_number: Optional[int] = None  # n番カッコの番号
    volta_start: bool = False  # n番カッコの開始かどうか
    volta_end: bool = False  # n番カッコの終了かどうか
    chord: Optional[str] = None  # コード名
    is_repeat_symbol: bool = False  # ...記号かどうか
    repeat_bars: Optional[int] = None  # リピートする小節数
    is_dummy: bool = False  # ...記号小節用のダミーフラグ

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
    """楽譜のセクション"""
    
    def __init__(self, name: str = ""):
        self.name = name
        self.columns = []
        self._bars = []  # 内部用の属性
        self.is_default = name == ""  # 名前が空文字列の場合はデフォルトセクション
        self.bar_group_size = 4  # デフォルトの小節グループサイズ
    
    def get_all_bars(self) -> List[Bar]:
        """全ての小節を取得"""
        return self._bars
    
    @property
    def bars(self) -> List[Bar]:
        """互換性のためのプロパティ"""
        if self._bars:
            return self._bars
        return self.get_all_bars()
    
    @bars.setter
    def bars(self, value: List[Bar]):
        """互換性のためのセッター"""
        self._bars = value

@dataclass
class Score:
    title: str = ""
    tuning: str = "guitar"
    beat: str = "4/4"  # デフォルトは4/4拍子
    bars_per_line: int = 4  # デフォルトは1行あたり4小節
    sections: List[Section] = None
    is_valid: bool = True  # パースが成功したかどうか

    def __post_init__(self):
        if self.sections is None:
            self.sections = []
    
    @property
    def bars(self) -> List[Bar]:
        """全ての小節を返す"""
        return [bar for section in self.sections for bar in section.bars]

class BarInfo(dict):
    """小節の構造情報"""
    def __init__(self, content, repeat_start=False, repeat_end=False, 
                 volta_number=None, volta_start=False, volta_end=False):
        super().__init__({
            'content': content,
            'repeat_start': repeat_start,
            'repeat_end': repeat_end,
            'volta_number': volta_number,
            'volta_start': volta_start,
            'volta_end': volta_end
        })
        
    @property
    def content(self):
        return self['content']
        
    @property
    def repeat_start(self):
        return self['repeat_start']
        
    @repeat_start.setter
    def repeat_start(self, value):
        self['repeat_start'] = value
        
    @property
    def repeat_end(self):
        return self['repeat_end']
        
    @repeat_end.setter
    def repeat_end(self, value):
        self['repeat_end'] = value
        
    @property
    def volta_number(self):
        return self['volta_number']
        
    @volta_number.setter
    def volta_number(self, value):
        self['volta_number'] = value
        
    @property
    def volta_start(self):
        return self['volta_start']
        
    @volta_start.setter
    def volta_start(self, value):
        self['volta_start'] = value
        
    @property
    def volta_end(self):
        return self['volta_end']
        
    @volta_end.setter
    def volta_end(self, value):
        self['volta_end'] = value 