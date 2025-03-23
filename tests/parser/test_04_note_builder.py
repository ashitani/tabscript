import pytest
from tabscript.parser.builder.note import NoteBuilder
from tabscript.models import Note
from tabscript.exceptions import ParseError
from fractions import Fraction

class TestNoteBuilder:
    """NoteBuilderのテスト"""
    
    def test_parse_basic_note(self):
        """基本的な音符のパースをテスト"""
        builder = NoteBuilder()
        note = builder.parse_note("3-5:8")
        
        assert note.string == 3
        assert note.fret == "5"
        assert note.duration == "8"
        assert not note.is_rest
        assert not note.is_chord
    
    def test_parse_note_with_inheritance(self):
        """弦番号と音価の継承をテスト"""
        builder = NoteBuilder()
        builder.last_string = 3
        builder.last_duration = "8"
        
        note = builder.parse_note("7", builder.last_duration)  # 明示的にデフォルト音価を渡す
        
        assert note.string == 3  # 前の弦番号を継承
        assert note.fret == "7"
        assert note.duration == "8"  # 前の音価を継承
    
    def test_parse_rest(self):
        """休符のパースをテスト"""
        builder = NoteBuilder()
        note = builder.parse_note("r:4")
        
        assert note.is_rest
        assert note.duration == "4"
    
    def test_parse_muted_note(self):
        """ミュート音符のパースをテスト"""
        builder = NoteBuilder()
        note = builder.parse_note("2-X:4")
        
        assert note.string == 2
        assert note.fret == "X"
        assert note.is_muted
        assert note.duration == "4"
    
    def test_parse_tie_slur(self):
        """タイ/スラー記法のパースをテスト"""
        builder = NoteBuilder()
        note = builder.parse_note("3-5:4&")
        
        assert note.string == 3
        assert note.fret == "5"
        assert note.duration == "4"
        assert note.connect_next
    
    def test_parse_string_movement(self):
        """弦移動表記のパースをテスト"""
        builder = NoteBuilder()
        builder.last_string = 3  # 3弦から開始
        
        # 上方向への移動（1弦上へ）
        note_up = builder.parse_note("u1:4")  # 3弦から1弦上の2弦へ移動し、1フレット
        
        assert note_up.is_up_move
        assert note_up.string == 2  # 3弦 → 2弦（1弦上）
        assert note_up.fret == "1"  # フレット番号は1
        assert note_up.duration == "4"
        
        # 下方向への移動（1弦下へ）
        builder.last_string = 2  # 2弦から開始
        note_down = builder.parse_note("d2:4")  # 2弦から1弦下の3弦へ移動し、2フレット
        
        assert note_down.is_down_move
        assert note_down.string == 3  # 2弦 → 3弦（1弦下）
        assert note_down.fret == "2"  # フレット番号は2
        assert note_down.duration == "4"
        
        # 1弦より上には移動できない
        builder.last_string = 1
        with pytest.raises(ParseError, match="cannot move above string 1"):
            builder.parse_note("u1:4")  # 1弦から上へは移動できない
        
        # 6弦より下には移動できない（標準ギターの場合）
        builder.last_string = 6
        with pytest.raises(ParseError, match="cannot move beyond string 6"):
            builder.parse_note("d1:4")  # 6弦から下へは移動できない
    
    def test_parse_chord_notation(self):
        """和音記法のパースをテスト"""
        builder = NoteBuilder()
        chord_notes = builder.parse_chord_notation("(1-1 2-2 3-3):4", None)
        
        # リストが返されることを確認
        assert isinstance(chord_notes, list)
        assert len(chord_notes) == 3
        
        # 各音符の確認
        assert chord_notes[0].string == 1
        assert chord_notes[0].fret == "1"
        assert chord_notes[0].duration == "4"
        assert chord_notes[0].chord == "chord"
        
        assert chord_notes[1].string == 2
        assert chord_notes[1].fret == "2"
        
        assert chord_notes[2].string == 3
        assert chord_notes[2].fret == "3"
    
    def test_calculate_note_step(self):
        """音符のステップ数計算をテスト"""
        builder = NoteBuilder()
        
        # 4分音符
        note1 = Note(string=1, fret="0", duration="4")
        builder.calculate_note_step(note1)
        assert note1.step == Fraction(1)
        
        # 8分音符
        note2 = Note(string=1, fret="0", duration="8")
        builder.calculate_note_step(note2)
        assert note2.step == Fraction(1, 2)
        
        # 付点4分音符
        note3 = Note(string=1, fret="0", duration="4.")
        builder.calculate_note_step(note3)
        assert note3.step == Fraction(3, 2)
    