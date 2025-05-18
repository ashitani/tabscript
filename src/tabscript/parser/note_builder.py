from tabscript.models import Note
from tabscript.exceptions import ParseError

class NoteBuilder:
    """音符を構築するクラス"""
    
    def build_note(self, string, fret, duration):
        """音符を構築する"""
        note = Note(string=string, fret=fret, duration=duration)
        return note
    
    def build_rest(self, duration):
        """休符を構築する"""
        note = Note(string=None, fret="r", duration=duration)
        return note
    
    def build_muted(self, string, duration):
        """ミュート音符を構築する"""
        note = Note(string=string, fret="x", duration=duration)
        return note
    
    def build_triplet(self, notes, duration):
        """三連符グループを構築する"""
        if len(notes) != 3:
            raise ParseError("Invalid triplet: must contain exactly 3 notes")
        
        # 三連符グループの親音符を作成
        triplet = Note(string=notes[0].string, fret=notes[0].fret, duration=duration)
        triplet.is_triplet = True
        triplet.triplet_notes = []
        
        # 三連符内の各音符を処理
        for note in notes:
            # 音価を親音符と同じに設定
            note.duration = duration
            triplet.triplet_notes.append(note)
        
        return triplet
    
    def parse_triplet(self, content):
        """三連符グループをパースする"""
        # 括弧を除去
        content = content.strip("()")
        
        # 音符を分割
        note_strings = content.split()
        if len(note_strings) != 3:
            raise ParseError("Invalid triplet: must contain exactly 3 notes")
        
        # 各音符をパース
        notes = []
        for note_str in note_strings:
            if note_str == "r":
                # 休符
                notes.append(self.build_rest(None))
            elif "-x" in note_str or "-X" in note_str:
                # ミュート音符
                string = int(note_str.split("-")[0])
                notes.append(self.build_muted(string, None))
            else:
                # 通常の音符
                string, fret = note_str.split("-")
                notes.append(self.build_note(int(string), fret, None))
        
        return notes 