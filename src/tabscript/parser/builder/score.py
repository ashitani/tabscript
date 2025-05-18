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
        
        # 各セクションのバーを作成
        current_beat = score.beat  # 現在の拍子を追跡（スコアのデフォルト値で初期化）
        
        # section_bar_infosの形式を検出して適切に処理
        if isinstance(section_bar_infos, list):
            # リスト形式 [{"name": "Section A", "bars": [...]}, ...]
            for section_info in section_bar_infos:
                section_name = section_info.get('name', '')
                bar_infos = section_info.get('bars', [])
                
                section = Section(section_name)
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
                self._organize_bars_into_columns(section, bars, score.bars_per_line, current_beat)
                # 追加: Sectionの_bars属性に全小節をセット
                section._bars = bars
        else:
            # 辞書形式 {"Section A": [...], ...}
            for section_name, bar_infos in section_bar_infos.items():
                section = Section(section_name)
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
                self._organize_bars_into_columns(section, bars, score.bars_per_line, current_beat)
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
    
    def parse_lines(self, lines: List[str]) -> Score:
        """TabScriptの複数行をパースしてスコアを構築する
        
        Args:
            lines: パースする行のリスト
            
        Returns:
            Score: 構築されたスコアオブジェクト
        """
        # スコアの初期化
        score = Score()
        current_section = None
        
        # 行ごとに処理
        for line_num, line in enumerate(lines, 1):
            self.current_line = line_num
            line = line.strip()
            
            # 空行のスキップ
            if not line:
                continue
            
            # メタデータの処理
            if line.startswith('$'):
                key, value = self.parse_metadata_line(line)
                if key == "title":
                    score.title = value
                elif key == "tuning":
                    score.tuning = value
                    self.bar_builder.set_tuning(value)
                elif key == "beat":
                    score.beat = value
                # その他のメタデータは無視
                continue
            
            # セクションヘッダーの処理
            if line.startswith('['):
                section = self.parse_section_header(line)
                score.sections.append(section)
                current_section = section
                continue
            
            # セクションがない場合は自動的にデフォルトセクションを作成
            if not current_section:
                current_section = Section(name="")
                score.sections.append(current_section)
            
            # 小節行の処理
            self.bar_builder.current_line = self.current_line
            bar = self.bar_builder.parse_bar_line(line)
            
            # 小節をセクションに追加
            if not current_section.columns:
                current_section.columns.append(Column(bars=[]))
            current_section.columns[-1].bars.append(bar)
        
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
    
    def parse_bar_line(self, line: str) -> Bar:
        """小節行をパースしてBarオブジェクトを返す（互換性のため）"""
        # 状態をBarBuilderに設定
        self.bar_builder.last_string = self.last_string
        self.bar_builder.last_duration = self.last_duration
        self.bar_builder.current_line = self.current_line
        
        # BarBuilderを使用して小節をパース
        bar = self.bar_builder.parse_bar_line(line)
        
        # 状態を同期
        self.last_string = self.bar_builder.last_string
        self.last_duration = self.bar_builder.last_duration
        
        return bar
    
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