from .note import NoteBuilder
from .bar import BarBuilder
from .score import ScoreBuilder

# 後方互換性のために単一のScoreBuilderクラスもエクスポート
class ScoreBuilderLegacy:
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.bar_builder = BarBuilder(debug_mode)
        self.score_builder = ScoreBuilder(debug_mode)
        self.current_line = 0
        self.last_string = self.bar_builder.last_string
        self.last_duration = self.bar_builder.last_duration

    # レガシーコードとの互換性のためのメソッド
    def build_score(self, *args, **kwargs):
        return self.score_builder.build_score(*args, **kwargs)

    def parse_bar_line(self, *args, **kwargs):
        result = self.bar_builder.parse_bar_line(*args, **kwargs)
        # 状態の同期
        self.last_string = self.bar_builder.last_string
        self.last_duration = self.bar_builder.last_duration
        return result

    def _calculate_note_step(self, *args, **kwargs):
        return self.bar_builder._calculate_note_step(*args, **kwargs)

    def _calculate_note_steps(self, *args, **kwargs):
        return self.bar_builder._calculate_note_steps(*args, **kwargs)

    def _parse_note(self, *args, **kwargs):
        # 状態をバーバルダーに設定
        self.bar_builder.last_string = self.last_string
        self.bar_builder.last_duration = self.last_duration
        
        result = self.bar_builder._parse_note(*args, **kwargs)
        
        # 状態を同期
        self.last_string = self.bar_builder.last_string
        self.last_duration = self.bar_builder.last_duration
        
        return result

# エクスポート
__all__ = ['NoteBuilder', 'BarBuilder', 'ScoreBuilder', 'ScoreBuilderLegacy'] 