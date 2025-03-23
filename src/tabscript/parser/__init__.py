from typing import List, Tuple, Optional, Dict, Union
from pathlib import Path
import re
from ..models import Score, Section, Bar, Note, Column
from ..exceptions import ParseError, TabScriptError
from fractions import Fraction
from dataclasses import dataclass
import os
import sys

# TextPreprocessorクラスをインポート
# 相対インポートを修正
from .preprocessor import TextPreprocessor
from .analyzer import StructureAnalyzer
from .validator import TabScriptValidator

# 新しいbuilderクラスをインポート
from .builder.score import ScoreBuilder
from .builder.bar import BarBuilder

@dataclass
class BarInfo:
    """小節の構造情報"""
    content: str
    repeat_start: bool = False
    repeat_end: bool = False
    volta_number: Optional[int] = None
    volta_start: bool = False
    volta_end: bool = False

@dataclass
class SectionStructure:
    """セクションの構造情報"""
    name: str
    content: List[str]  # 生のテキスト行

@dataclass
class ScoreStructure:
    """スコア全体の構造情報"""
    metadata: Dict[str, str]
    sections: List[SectionStructure]

class Parser:
    def __init__(self, debug_mode: bool = False, debug_level: int = 0, skip_validation: bool = False):
        """パーサーを初期化
        
        Args:
            debug_mode: デバッグモードの有効/無効
            debug_level: デバッグレベル（旧テスト用に追加）
            skip_validation: バリデーションをスキップするかどうか（旧テスト用に追加）
        """
        self.debug_mode = debug_mode
        self.debug_level = debug_level  # 旧テスト用に追加
        self.skip_validation = skip_validation  # 旧テスト用に追加
        self.score = None
        self.current_line = 0
        
        # 各コンポーネントを初期化
        self._preprocessor = TextPreprocessor(debug_mode=debug_mode)
        self._analyzer = StructureAnalyzer(debug_mode)
        self._validator = TabScriptValidator()
        self._score_builder = ScoreBuilder(debug_mode)
        self._bar_builder = BarBuilder(debug_mode)
        
        # 後方互換性のための状態変数
        self.last_string = self._bar_builder.last_string
        self.last_duration = self._bar_builder.last_duration

        # 新しいanalyzerを設定
        self._score_builder.analyzer = self._analyzer

    def debug_print(self, *args, level: int = 1, **kwargs):
        """デバッグ出力を行う
        
        Args:
            *args: 出力する内容
            level: このメッセージのデバッグレベル（1: 基本情報、2: 詳細情報、3: 全情報）
            **kwargs: print関数に渡す追加の引数
        """
        if self.debug_mode and level <= self.debug_level:
            print(*args, **kwargs)

    def parse(self, text_or_file: str) -> Score:
        """TabScriptテキストまたはファイルをパースしてScoreオブジェクトを返す
        
        Args:
            text_or_file: パースするTabScriptテキストまたはファイルパス
            
        Returns:
            Score: パースされたスコアオブジェクト
        """
        # ファイルパスの場合はファイルを読み込む
        if os.path.isfile(text_or_file):
            with open(text_or_file, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            text = text_or_file
        
        self.debug_print(f"Parsing text: {len(text)} characters")
        
        # テキストの前処理
        preprocessed_text = self._preprocessor.preprocess(text)
        
        # 構造解析
        metadata, sections = self._analyzer.analyze(preprocessed_text)
        
        # バリデーション（一時的にスキップ）
        # if not self.skip_validation:
        #     self._validator.validate(metadata, sections)
        
        # スコア構築
        self.score = self._score_builder.build_score(metadata, sections)
        
        return self.score

    def _preprocess_text(self, text: str) -> str:
        """テキストの前処理を行う（互換性のため）"""
        return self._preprocessor.preprocess(text)

    def _load_source(self, source: Union[str, Path]) -> str:
        """ファイルパスまたはテキストから入力を読み込む"""
        if '\n' in source:
            return source
        with open(source, 'r') as f:
            return f.read()
    
    def _parse_lines(self, lines: List[str]):
        """Parse lines of TabScript（互換性のため）"""
        # 現在の状態をScoreBuilderに設定
        self._score_builder.last_string = self.last_string
        self._score_builder.last_duration = self.last_duration
        self._score_builder.current_line = self.current_line
        
        # ScoreBuilderを使用して行をパース
        self.score = self._score_builder.parse_lines(lines)
        
        # ScoreBuilderの状態を取得
        self.last_string = self._score_builder.last_string
        self.last_duration = self._score_builder.last_duration
        
        return self.score

    def _parse_metadata_line(self, line: str) -> Tuple[str, str]:
        """Parse a metadata line ($key="value")（互換性のため）"""
        # 現在の状態をScoreBuilderに設定
        self._score_builder.current_line = self.current_line
        
        # ScoreBuilderを使用してメタデータ行をパース
        key, value = self._score_builder.parse_metadata_line(line)
        
        return key, value

    def _parse_section_header(self, line: str):
        """Parse a section header [name]（互換性のため）"""
        # 現在の状態をScoreBuilderに設定
        self._score_builder.current_line = self.current_line
        
        # ScoreBuilderを使用してセクションヘッダーをパース
        section = self._score_builder.parse_section_header(line)
        
        # セクションを追加
        if not self.score:
            self.score = Score(sections=[])
        self.score.sections.append(section)

    def _parse_notes(self, notes_str: str) -> List[Note]:
        """Parse space-separated notes（互換性のため）"""
        # 現在の状態をScoreBuilderに設定
        self._score_builder.last_string = self.last_string
        self._score_builder.last_duration = self.last_duration
        self._score_builder.current_line = self.current_line
        
        # ScoreBuilderを使用して音符をパース
        notes = self._score_builder._parse_notes(notes_str)
        
        # ScoreBuilderの状態を取得
        self.last_string = self._score_builder.last_string
        self.last_duration = self._score_builder.last_duration
        
        return notes

    def _parse_bar_line(self, line: str) -> Bar:
        """小節行をパース（互換性のため）"""
        # 現在の状態をScoreBuilderに設定
        self._score_builder.last_string = self.last_string
        self._score_builder.last_duration = self.last_duration
        self._score_builder.current_line = self.current_line
        
        # ScoreBuilderを使用して小節をパース
        bar = self._score_builder.parse_bar_line(line)
        
        # ScoreBuilderの状態を取得
        self.last_string = self._score_builder.last_string
        self.last_duration = self._score_builder.last_duration
        
        return bar

    def _calculate_note_step(self, note: Note) -> None:
        """音符のステップ数を計算（互換性のため）"""
        # ScoreBuilderを使用してステップ数を計算
        self._score_builder._calculate_note_step(note)

    def _calculate_note_steps(self, bar: Bar) -> None:
        """小節内の音符のステップ数を計算（互換性のため）"""
        # ScoreBuilderを使用してステップ数を計算
        self._score_builder._calculate_note_steps(bar)

    def _parse_note(self, token: str, default_duration: str = "4", chord: Optional[str] = None) -> Note:
        """音符トークンをパース（互換性のため）"""
        # 現在の状態を一時的にScoreBuilderに設定
        self._score_builder.last_string = self.last_string
        self._score_builder.last_duration = self.last_duration
        self._score_builder.current_line = self.current_line
        
        # ScoreBuilderを使用して音符をパース
        note = self._score_builder._parse_note(token, default_duration, chord)
        
        # ScoreBuilderの状態を取得
        self.last_string = self._score_builder.last_string
        self.last_duration = self._score_builder.last_duration
        
        return note

    def render_score(self, output_path: str):
        """タブ譜をファイルとして出力"""
        if not self.score:
            raise TabScriptError("No score to render. Call parse() first.")
        
        from .renderer import Renderer
        renderer = Renderer(self.score, debug_mode=self.debug_mode)  # デバッグモードを渡す
        
        if output_path.endswith('.pdf'):
            renderer.render_pdf(output_path)
        else:
            renderer.render_text(output_path)

    def print_tab(self, output_path: str):
        """省略記法を展開した完全な形式のtabファイルを出力"""
        if not self.score:
            raise TabScriptError("No score to print. Call parse() first.")

        with open(output_path, 'w') as f:
            # メタデータを出力
            f.write(f'$title="{self.score.title}"\n')
            f.write(f'$tuning="{self.score.tuning}"\n')
            f.write(f'$beat="{self.score.beat}"\n\n')

            # 各セクションを出力
            for section in self.score.sections:
                f.write(f"[{section.name}]\n")
                
                # 各小節を出力
                for column in section.columns:
                    # コード名を出力（空の場合は空文字列）
                    chord = column.bars[0].chord if column.bars[0].chord else ""
                    f.write(f"{chord}, ")

                    # 音符を完全な形式で出力
                    notes = []
                    for bar in column.bars:
                        # 音符を完全な形式で出力
                        notes.append(f"{bar.notes[0].string}-{bar.notes[0].fret}:{bar.notes[0].duration}")
                    
                    f.write(" ".join(notes) + "\n")
                
                f.write("\n")  # セクション間に空行を挿入

    def _get_string_count(self) -> int:
        """チューニング設定から弦の数を取得"""
        tuning_map = {
            "guitar": 6,
            "guitar7": 7,
            "bass": 4,
            "bass5": 5,
            "ukulele": 4
        }
        return tuning_map.get(self.score.tuning, 6)  # デフォルトは6弦

    def safe_int(self, value: str, caller: str) -> int:
        """
        intのラッパー関数。呼び出し元と変換しようとした値をデバッグ出力する
        """
        self.debug_print(f"\n=== safe_int ===")
        self.debug_print(f"Called from: {caller}")
        self.debug_print(f"Converting value: '{value}'")
        try:
            result = int(value)
            self.debug_print(f"Result: {result}")
            return result
        except ValueError:
            self.debug_print(f"Error converting value: {value}")
            if caller.endswith("/fret"):
                raise ParseError("Invalid fret number", self.current_line)
            elif caller.endswith("/string"):
                raise ParseError("Invalid string number", self.current_line)
            else:
                raise ParseError(f"Invalid number: {value}", self.current_line)

    def _parse_metadata(self, line: str) -> None:
        """メタデータ行をパース
        
        Args:
            line: メタデータ行（$key="value"形式）
        """
        self.debug_print(f"Parsing metadata: {line}")
        
        # $key="value"形式のパース
        match = re.match(r'\$(\w+)\s*=\s*"([^"]*)"', line)
        if not match:
            raise ParseError(f"Invalid metadata format: {line}", self.current_line)
        
        key, value = match.group(1), match.group(2)
        
        # メタデータをスコアに設定
        if key == "title":
            self.score.title = value
        elif key == "tuning":
            self.score.tuning = value
            self._validator.validate_tuning(value)
        elif key == "beat":
            self.score.beat = value
            self._validator.validate_beat(value)
        elif key == "bars_per_line":
            try:
                bars_per_line = int(value)
                # 各セクションのカラムに設定するため、ここでは保存のみ
                self.bars_per_line = bars_per_line
            except ValueError:
                raise ParseError(f"Invalid bars_per_line value: {value}", self.current_line)
        else:
            # 未知のメタデータは無視（将来の拡張のため）
            self.debug_print(f"Unknown metadata key: {key}")

    def _normalize_volta_brackets(self, text: str) -> str:
        """n番カッコを一行形式に変換（互換性のため）"""
        try:
            # 繰り返し記号の正規化を先に行う
            text = self._normalize_repeat_brackets(text)
            return self._preprocessor._normalize_volta_brackets(text)
        except ValueError as e:
            # ValueErrorをParseErrorに変換
            raise ParseError(str(e), self.current_line)

    def _clean_text(self, text: str) -> str:
        """テキストからコメントと空行を除去（互換性のため）"""
        return self._preprocessor._clean_text(text)

    def _normalize_repeat_brackets(self, text: str) -> str:
        """繰り返し記号の正規化（互換性のため）"""
        return self._preprocessor._normalize_repeat_brackets(text)

    def _extract_structure(self, text: str) -> Tuple[Dict[str, str], List[SectionStructure]]:
        """テキストからメタデータとセクション構造を抽出（互換性のため）"""
        return self._analyzer._extract_structure(text)

    def _analyze_section_bars(self, section_content: List[str]) -> List[BarInfo]:
        """セクション内容から小節情報を抽出（互換性のため）"""
        return self._analyzer._analyze_section_bars(section_content)
