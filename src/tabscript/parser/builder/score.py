from typing import Dict, List, Any, Tuple, Optional
from ...models import Score, Section, Column, Bar, Note, BarInfo
from ...exceptions import ParseError, TabScriptError
from .bar import BarBuilder
import re
from ..analyzer import StructureAnalyzer  # 循環インポートを避けるためにここでインポート
# from ..analyzer.note import NoteAnalyzer  # この行を削除または以下のようにコメントアウト
from fractions import Fraction

class ScoreBuilder:
    """スコアレベルの処理を担当するクラス"""
    
    def __init__(self, debug_mode: bool = False):
        """ScoreBuilderを初期化
        
        Args:
            debug_mode: デバッグモードの有効/無効
        """
        self.debug_mode = debug_mode
        self.current_line = 0
        self.bar_builder = BarBuilder(debug_mode)
        self.analyzer = StructureAnalyzer(debug_mode)
        # 後方互換性のための状態変数
        self.last_string = self.bar_builder.last_string
        self.last_duration = self.bar_builder.last_duration
    
    def debug_print(self, *args, **kwargs):
        """デバッグ出力を行う"""
        if self.debug_mode:
            print("DEBUG (ScoreBuilder):", *args, **kwargs)
    
    def build_score(self, settings, section_bar_infos):
        """BarInfoの配列からScoreを構築する
        
        Args:
            settings: スコアの設定（title, tuning, beatなど）
            section_bar_infos: 各セクションの情報と小節情報のリスト
                以下の形式が期待されます:
                - リスト形式: [{"name": "Section A", "bars": [BarInfo, BarInfo, ...]}]
                - 辞書形式: {"Section A": [BarInfo, BarInfo, ...]}
        """
        # スコアの基本設定を追加
        score = Score(
            title=settings.get('title', ''),
            tuning=settings.get('tuning', 'guitar'),
            beat=settings.get('beat', '4/4'),
            bars_per_line=int(settings.get('bars_per_line', 4))
        )
        self.debug_print(f"Initial bars_per_line: {score.bars_per_line}")
        
        # 各セクションのバーを作成
        current_beat = score.beat
        current_bars_per_line = score.bars_per_line
        
        # section_bar_infosの形式を検出して適切に処理
        if isinstance(section_bar_infos, list):
            # リスト形式 [{"name": "Section A", "bars": [...]}, ...]
            for section_info in section_bar_infos:
                section_name = section_info.get('name', '')
                bar_infos = section_info.get('bars', [])
                
                # セクションごとのbars_per_lineを取得
                section_bars_per_line = section_info.get('bars_per_line', current_bars_per_line)
                self.debug_print(f"Section {section_name} using bars_per_line: {section_bars_per_line}")
                
                section = Section(section_name)
                # page_breaks情報を引き継ぐ
                if 'page_breaks' in section_info:
                    section.page_breaks = section_info['page_breaks']
                score.sections.append(section)
                
                # 小節の作成
                bars = []
                for bar_info in bar_infos:
                    bar = self._build_bar(bar_info, current_beat)
                    bars.append(bar)
                    # 拍子が変わったら記録
                    if bar.beat != current_beat:
                        current_beat = bar.beat
                # 小節リストをbars_per_line単位でColumnに分割
                self.debug_print(f"Organizing bars for section {section_name} with bars_per_line={section_bars_per_line}")
                self._organize_bars_into_columns(section, bars, section_bars_per_line, current_beat)
                # 追加: Sectionの_bars属性に全小節をセット
                section._bars = bars
        else:
            # 辞書形式 {"Section A": [...], ...}
            for section_name, bar_infos in section_bar_infos.items():
                # セクションごとのbars_per_lineを取得
                section_bars_per_line = bar_infos.get('bars_per_line', current_bars_per_line)
                self.debug_print(f"Section {section_name} using bars_per_line: {section_bars_per_line}")
                
                section = Section(section_name)
                # page_breaks情報を引き継ぐ
                if 'page_breaks' in bar_infos:
                    section.page_breaks = bar_infos['page_breaks']
                score.sections.append(section)
                
                # 小節の作成
                bars = []
                for bar_info in bar_infos:
                    bar = self._build_bar(bar_info, current_beat)
                    bars.append(bar)
                    # 拍子が変わったら記録
                    if bar.beat != current_beat:
                        current_beat = bar.beat
                # 小節リストをbars_per_line単位でColumnに分割
                self.debug_print(f"Organizing bars for section {section_name} with bars_per_line={section_bars_per_line}")
                self._organize_bars_into_columns(section, bars, section_bars_per_line, current_beat)
                # 追加: Sectionの_bars属性に全小節をセット
                section._bars = bars
        
        return score
    
    def _organize_bars_into_columns(self, section, bars, bars_per_line, beat):
        """小節リストをColumnに整理する
        
        Args:
            section: 小節を追加するセクション
            bars: 小節のリスト
            bars_per_line: 1行あたりの小節数
            beat: 拍子
        """
        if not bars:
            return
        
        # 小節を bars_per_line ごとに分割
        for i in range(0, len(bars), bars_per_line):
            # bars_per_line 個または残りすべてを取得
            chunk = bars[i:i+bars_per_line]
            
            # 新しいカラムを作成して追加
            column = Column(bars=chunk, bars_per_line=bars_per_line, beat=beat)
            section.columns.append(column)
    
    def parse_metadata_line(self, line: str) -> Tuple[str, str]:
        """メタデータ行をパースする
        
        Args:
            line: パースするメタデータ行
            
        Returns:
            Tuple[str, str]: キーと値のペア
        """
        match = re.match(r'\$(\w+)\s*=\s*"([^"]*)"', line)
        if not match:
            raise ParseError("Invalid metadata format", self.current_line)
        return match.group(1), match.group(2)
    
    def parse_section_header(self, line: str) -> Section:
        """セクションヘッダーをパースする
        
        Args:
            line: パースするセクションヘッダー行
            
        Returns:
            Section: 作成されたセクションオブジェクト
        """
        match = re.match(r'\[(.*)\]', line)
        if not match:
            raise ParseError("Invalid section header", self.current_line)
        
        name = match.group(1)
        return Section(name=name)
    
    def parse_lines(self, lines):
        """行をパースしてScoreオブジェクトを返す
        
        Args:
            lines: パースする行のリスト
        
        Returns:
            Score: パースされたスコアオブジェクト
        """
        self.debug_print(f"Parsing {len(lines)} lines")
        score = Score()
        current_section = None
        current_column = None
        current_bars = []
        current_bars_per_line = 4  # デフォルト値
        current_beat = '4/4'

        for line in lines:
            self.debug_print(f"Parsing line: {line}")
            if not line.strip():
                continue
            if line.startswith('$'):
                key, value = self.parse_metadata_line(line)
                if key == 'title':
                    score.title = value
                elif key == 'tuning':
                    score.tuning = value
                elif key == 'beat':
                    score.beat = value
                    current_beat = value
                elif key == 'bars_per_line':
                    # bars_per_line切り替え時は強制的にカラムを区切る
                    if current_section and current_bars:
                        # 直前のbars_per_lineでカラム分割
                        self._organize_bars_into_columns(current_section, current_bars, current_bars_per_line, current_beat)
                        current_bars = []
                    current_bars_per_line = int(value)
                    score.bars_per_line = current_bars_per_line
                elif key == 'section':
                    if current_section and current_bars:
                        self._organize_bars_into_columns(current_section, current_bars, current_bars_per_line, current_beat)
                        current_bars = []
                    current_section = Section(value)
                    score.sections.append(current_section)
                    current_column = None
                continue
            if line.startswith('[') and line.endswith(']'):
                if current_section and current_bars:
                    self._organize_bars_into_columns(current_section, current_bars, current_bars_per_line, current_beat)
                    current_bars = []
                current_section = self.parse_section_header(line)
                score.sections.append(current_section)
                current_column = None
                continue
            if not current_section:
                current_section = Section("Default")
                score.sections.append(current_section)
                current_column = None
            if line.strip():
                bar = self.parse_bar_line(line)
                if bar:
                    current_bars.append(bar)
                    # bars_per_lineに達したらカラムを作成
                    if len(current_bars) == current_bars_per_line:
                        self._organize_bars_into_columns(current_section, current_bars, current_bars_per_line, current_beat)
                        current_bars = []
        # 残りの小節をカラムに
        if current_section and current_bars:
            self._organize_bars_into_columns(current_section, current_bars, current_bars_per_line, current_beat)
        return score
    
    # 後方互換性のためのメソッド
    def _parse_note(self, token: str, default_duration: str = "4", chord: Optional[str] = None) -> Note:
        """音符トークンをパースしてNoteオブジェクトを返す（互換性のため）"""
        # 状態をBarBuilderに設定
        self.bar_builder.last_string = self.last_string
        self.bar_builder.last_duration = self.last_duration
        self.bar_builder.current_line = self.current_line
        
        # BarBuilderを使用して音符をパース
        note = self.bar_builder._parse_note(token, default_duration, chord)
        
        # 状態を同期
        self.last_string = self.bar_builder.last_string
        self.last_duration = self.bar_builder.last_duration
        
        return note
    
    def _parse_notes(self, notes_str: str) -> List[Note]:
        """スペース区切りの音符をパースしてNoteのリストを返す（互換性のため）"""
        # 状態をBarBuilderに設定
        self.bar_builder.last_string = self.last_string
        self.bar_builder.last_duration = self.last_duration
        self.bar_builder.current_line = self.current_line
        
        # BarBuilderを使用して音符をパース
        notes = self.bar_builder._parse_notes(notes_str)
        
        # 状態を同期
        self.last_string = self.bar_builder.last_string
        self.last_duration = self.bar_builder.last_duration
        
        return notes
    
    def parse_bar_line(self, line: str) -> Optional[Bar]:
        """小節行をパースする
        
        Args:
            line: パースする小節行
            
        Returns:
            Optional[Bar]: パースされた小節オブジェクト、または無効な行の場合はNone
        """
        # 空行や無効な行はスキップ
        if not line.strip():
            return None
        
        # 小節をパース
        try:
            bar = self.bar_builder.parse_bar_line(line)
            return bar
        except ParseError as e:
            self.debug_print(f"Error parsing bar line: {e}")
            return None
    
    def _calculate_note_step(self, note: Note) -> None:
        """音符のステップ数を計算する（互換性のため）"""
        self.bar_builder._calculate_note_step(note)
    
    def _calculate_note_steps(self, bar: Bar) -> None:
        """小節内の全ての音符のステップ数を計算する（互換性のため）"""
        self.bar_builder._calculate_note_steps(bar)
    
    def _build_bar(self, bar_info, current_beat=None):
        """BarInfoからBarを構築する"""
        # 小節の基本設定
        bar = Bar(
            notes=[],  # 初期値は空のリスト
            beat=current_beat or getattr(bar_info, 'beat', '4/4')
        )
        # is_repeat_symbol, repeat_bars, is_dummyをコピー
        bar.is_repeat_symbol = getattr(bar_info, 'is_repeat_symbol', False)
        bar.repeat_bars = getattr(bar_info, 'repeat_bars', None)
        # 繰り返し記号の小節はis_dummyをTrueに設定
        bar.is_dummy = bar.is_repeat_symbol or getattr(bar_info, 'is_dummy', False)
        # コンテンツがある場合は解析
        if hasattr(bar_info, 'content') and bar_info.content:
            # BarBuilderを使用して音符を解析
            content = bar_info.content
            self.bar_builder.current_line = self.current_line
            parsed_bar = self.bar_builder.parse_bar_line(content)
            bar.notes = parsed_bar.notes
        # 繰り返し記号の設定
        bar.is_repeat_start = getattr(bar_info, 'repeat_start', False)
        bar.is_repeat_end = getattr(bar_info, 'repeat_end', False)
        # n番括弧の設定
        bar.volta_number = getattr(bar_info, 'volta_number', None)
        bar.volta_start = getattr(bar_info, 'volta_start', False)
        bar.volta_end = getattr(bar_info, 'volta_end', False)
        return bar 