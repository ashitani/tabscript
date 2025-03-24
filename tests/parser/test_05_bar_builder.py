import pytest
from tabscript.parser.builder.bar import BarBuilder
from tabscript.models import Bar, Note, BarInfo
from tabscript.exceptions import ParseError
from fractions import Fraction

class TestBarBuilder:
    """BarBuilderのテスト"""
    
    def test_parse_bar_line(self):
        """小節行のパースをテスト"""
        builder = BarBuilder()
        bar = builder.parse_bar_line("1-1:4 2-2:4")
        
        assert len(bar.notes) == 2
        assert bar.notes[0].string == 1
        assert bar.notes[0].fret == "1"
        assert bar.notes[0].duration == "4"
        assert bar.notes[1].string == 2
        assert bar.notes[1].fret == "2"
        assert bar.notes[1].duration == "4"
    
    def test_parse_bar_with_chord(self):
        """コード名を含む小節のパースをテスト"""
        builder = BarBuilder()
        bar = builder.parse_bar_line("@Am 1-1:4 2-2:4")
        
        assert bar.chord == "Am"
        assert len(bar.notes) == 2
        assert bar.notes[0].chord == "Am"
        assert bar.notes[1].chord == "Am"
    
    def test_parse_bar_with_repeat_marks(self):
        """繰り返し記号を含む小節のパースをテスト"""
        builder = BarBuilder()
        
        # 繰り返し記号は { } で表現
        # 直接BarInfoオブジェクトをセットして渡す
        bar_info = BarInfo("1-1:4 2-2:4", repeat_start=True, repeat_end=True)
        bar = builder.parse_bar_line(bar_info)
        
        assert len(bar.notes) == 2
        assert bar.is_repeat_start
        assert bar.is_repeat_end
        assert bar.notes[0].string == 1
        assert bar.notes[0].fret == "1"
        assert bar.notes[1].string == 2
        assert bar.notes[1].fret == "2"
    
    def test_parse_bar_with_volta(self):
        """ボルタブラケットを含む小節のパースをテスト"""
        builder = BarBuilder()
        bar = builder.parse_bar_line("[1] 1-1:4 2-2:4")
        
        assert bar.volta_number == 1
        assert bar.volta_start
        assert len(bar.notes) == 2
    
    def test_parse_bar_with_chord_notation(self):
        """和音記法を含む小節のパースをテスト"""
        builder = BarBuilder()
        bar = builder.parse_bar_line("(1-1 2-2):4 3-3:4")
        
        # 修正: 和音1つと単音1つで計2音
        assert len(bar.notes) == 2
        
        # 和音の内部構造を検証
        assert bar.notes[0].is_chord
        assert bar.notes[0].is_chord_start
        assert len(bar.notes[0].chord_notes) == 1  # 主音以外に1音
        assert bar.notes[0].chord_notes[0].string == 2
        assert bar.notes[0].chord_notes[0].fret == "2"
    
    def test_parse_bar_with_rest(self):
        """休符を含む小節のパースをテスト"""
        builder = BarBuilder()
        
        # NoteBuilder の実装を直接見ずに、期待される結果のみをテスト
        bar = builder.parse_bar_line("1-1:4 r:4 2-2:4")
        
        assert len(bar.notes) == 3
        assert bar.notes[0].string == 1
        assert bar.notes[0].fret == "1"
        assert bar.notes[1].is_rest
        assert bar.notes[2].string == 2
        assert bar.notes[2].fret == "2"
    
    def test_parse_bar_with_string_movement(self):
        """弦移動を含む小節のパースをテスト"""
        builder = BarBuilder()
        
        # u/dは1弦分の上下移動、数値はフレット番号
        bar = builder.parse_bar_line("3-3:4 d5:4 u2:4")
        
        assert len(bar.notes) == 3
        assert bar.notes[0].string == 3
        assert bar.notes[0].fret == "3"
        
        assert bar.notes[1].is_down_move
        assert bar.notes[1].string == 4  # 3弦から1弦下の4弦
        assert bar.notes[1].fret == "5"  # フレット番号は5
        
        assert bar.notes[2].is_up_move
        assert bar.notes[2].string == 3  # 4弦から1弦上の3弦
        assert bar.notes[2].fret == "2"  # フレット番号は2
    
    def test_calculate_note_steps(self):
        """小節内の音符のステップ数計算をテスト"""
        builder = BarBuilder()
        bar = Bar()
        
        # 4分音符と8分音符を追加
        note1 = Note(string=1, fret="0", duration="4")
        note2 = Note(string=2, fret="0", duration="8")
        bar.notes.append(note1)
        bar.notes.append(note2)
        
        builder._calculate_note_steps(bar)
        
        assert note1.step == Fraction(1)
        assert note2.step == Fraction(1, 2)
    
    def test_parse_notes(self):
        """スペース区切りの音符をパースするテスト"""
        builder = BarBuilder()
        notes = builder._parse_notes("1-1:4 2-2:4 3-3:4")
        
        assert len(notes) == 3
        assert notes[0].string == 1
        assert notes[0].fret == "1"
        assert notes[0].duration == "4"
        assert notes[1].string == 2
        assert notes[1].fret == "2"
        assert notes[1].duration == "4"
        assert notes[2].string == 3
        assert notes[2].fret == "3"
        assert notes[2].duration == "4"
    
    def test_parse_notes_with_chord(self):
        """コード名を含む音符列のパースをテスト"""
        builder = BarBuilder()
        notes = builder._parse_notes("@Am 1-1:4 2-2:4")
        
        assert len(notes) == 2
        assert notes[0].chord == "Am"
        assert notes[1].chord == "Am"
    
    def test_parse_notes_with_chord_notation(self):
        """和音記法を含む音符列のパースをテスト"""
        builder = BarBuilder()
        notes = builder._parse_notes("(1-1 2-2):4 3-3:4")
        
        assert len(notes) == 2
        assert notes[0].is_chord
        assert notes[0].is_chord_start
        assert not notes[1].is_chord
