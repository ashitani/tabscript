from tabscript.parser.note_builder import NoteBuilder
from tabscript.parser.validator import TabScriptValidator
from tabscript.models import Score, Section, Column, Bar, Note
from tabscript.exceptions import ParseError

class Parser:
    """TabScriptをパースするクラス"""
    
    def __init__(self, skip_validation=False):
        self.validator = TabScriptValidator()
        self.note_builder = NoteBuilder()
        self.skip_validation = skip_validation
    
    def parse(self, content):
        """TabScriptをパースする"""
        # メタデータとセクションを解析
        metadata, sections = self.analyze_structure(content)
        
        # スコアを構築
        score = self.build_score(metadata, sections)
        
        return score
    
    def parse_note(self, note_str):
        """音符をパースする"""
        # 三連符の処理
        if note_str.startswith("(") and note_str.endswith("):3"):
            # 三連符グループをパース
            content = note_str[:-3]  # ":3"を除去
            notes = self.note_builder.parse_triplet(content)
            return self.note_builder.build_triplet(notes, "3")
        
        # 通常の音符の処理
        if note_str == "r":
            return self.note_builder.build_rest(None)
        
        if "-x" in note_str or "-X" in note_str:
            string = int(note_str.split("-")[0])
            return self.note_builder.build_muted(string, None)
        
        string, fret = note_str.split("-")
        return self.note_builder.build_note(int(string), fret, None)
    
    def parse_bar(self, bar_str):
        """小節をパースする"""
        # 音符を分割
        note_strings = bar_str.split()
        
        # 各音符をパース
        notes = []
        for note_str in note_strings:
            note = self.parse_note(note_str)
            notes.append(note)
        
        return Bar(notes=notes)
    
    def analyze_structure(self, content):
        """TabScriptの構造を解析する"""
        # メタデータとセクションを解析する処理
        # （既存の実装を維持）
        pass
    
    def build_score(self, metadata, sections):
        """スコアを構築する"""
        # スコアを構築する処理
        # （既存の実装を維持）
        pass 