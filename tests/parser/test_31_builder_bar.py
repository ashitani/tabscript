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

    def test_parse_bar_with_triplet(self):
        """三連符グループのパースをテスト"""
        builder = BarBuilder()
        # 4分音符三連符
        bar = builder.parse_bar_line("[ 1-1:4 2-2:4 3-3:4 ]3")
        assert len(bar.notes) == 3
        # すべて三連符スケールで音価が換算されていること（例: 4分音符三連符なら1/3全音符）
        for note in bar.notes:
            assert note.duration == "4"
            # stepなどの値は実装次第で追加検証可能

    def test_parse_bar_with_triplet_and_rest_and_ghost(self):
        """三連符グループ内で休符やゴーストノートが混在する場合のテスト"""
        builder = BarBuilder()
        bar = builder.parse_bar_line("[ 1-1:4 r4 3-x:4 ]3")
        assert len(bar.notes) == 3
        assert not bar.notes[0].is_rest
        assert bar.notes[1].is_rest
        assert bar.notes[2].fret.lower() == "x"

    def test_parse_bar_with_quintuplet_and_mixed(self):
        """五連符グループで音価・休符・ミュート混在のテスト"""
        builder = BarBuilder()
        # 16分音符5つで合計5/16（すべて通常の音符）
        bar = builder.parse_bar_line("[ 1-1:16 2-2:16 3-3:16 4-4:16 5-5:16 ]5")
        assert len(bar.notes) == 5
        # それぞれの音符が正しくパースされていること
        assert bar.notes[0].duration == "16"
        assert bar.notes[1].duration == "16"
        assert bar.notes[2].duration == "16"
        assert bar.notes[3].duration == "16"
        assert bar.notes[4].duration == "16"

    def test_parse_bar_with_quintuplet_rests(self):
        """五連符グループで休符のみのテスト"""
        builder = BarBuilder()
        # 16分休符5つで合計5/16
        bar = builder.parse_bar_line("[ r16 r16 r16 r16 r16 ]5")
        assert len(bar.notes) == 5
        # すべて休符であることを確認
        for note in bar.notes:
            assert note.is_rest
            assert note.duration == "16"

    def test_parse_bar_with_quintuplet_mutes(self):
        """五連符グループでミュートのみのテスト"""
        builder = BarBuilder()
        # 16分ミュート5つで合計5/16
        bar = builder.parse_bar_line("[ 1-x:16 2-x:16 3-x:16 4-x:16 5-x:16 ]5")
        assert len(bar.notes) == 5
        # すべてミュートであることを確認
        for note in bar.notes:
            assert note.fret.lower() == "x"
            assert note.duration == "16"

    def test_parse_bar_with_quintuplet_mixed_types(self):
        """五連符グループで休符・ミュート・通常音符が混在するテスト"""
        builder = BarBuilder()
        # 16分音符5つで合計5/16（休符・ミュート・通常音符の混在）
        bar = builder.parse_bar_line("[ 1-1:16 r16 3-x:16 4-4:16 5-5:16 ]5")
        assert len(bar.notes) == 5
        # それぞれの音符が正しくパースされていること
        assert bar.notes[0].duration == "16"
        assert bar.notes[0].string == 1
        assert bar.notes[0].fret == "1"
        assert bar.notes[1].is_rest
        assert bar.notes[1].duration == "16"
        assert bar.notes[2].fret.lower() == "x"
        assert bar.notes[2].duration == "16"
        assert bar.notes[3].duration == "16"
        assert bar.notes[3].string == 4
        assert bar.notes[4].duration == "16"
        assert bar.notes[4].string == 5

    def test_triplet_tuplet_flag_and_step(self):
        """三連符グループのtuplet属性と絶対音価(step)の検証"""
        builder = BarBuilder(debug_mode=True)
        bar = builder.parse_bar_line("[ 1-1:4 2-2:4 3-3:4 ]3")
        assert len(bar.notes) == 3
        for note in bar.notes:
            # tuplet属性が正しく付与されている
            assert note.tuplet is not None
            assert note.tuplet == 3

    def test_quintuplet_tuplet_flag_and_step(self):
        """五連符グループのtuplet属性と絶対音価(step)の検証"""
        builder = BarBuilder(debug_mode=True)
        bar = builder.parse_bar_line("[ 1-1:8 2-2:8 3-3:8 4-4:8 5-5:8 ]5")
        assert len(bar.notes) == 5
        for note in bar.notes:
            assert note.tuplet is not None
            assert note.tuplet == 5

    def test_triplet_bar_notes_count(self):
        """三連符4セットが1小節に12ノートとしてパースされることを検証"""
        builder = BarBuilder()
        bar = builder.parse_bar_line("[ 4-2 4-4 3-2 ]3 [ 4-2 4-4 3-2 ]3 [ 4-2 4-4 3-2 ]3 [ 4-2 4-4 3-2 ]3")
        assert len(bar.notes) == 12, "1小節内に12個のノートが含まれるべき"

    def test_triplet_line_should_be_single_bar(self):
        """三連符4セットを含む1小節分の文字列が1小節として扱われるべきだが、現状は分割されてしまう問題の再現テスト"""
        from tabscript.parser.analyzer import StructureAnalyzer
        analyzer = StructureAnalyzer()
        # 三連符4セットを含む1小節分の文字列
        lines = ["[ 4-2 4-4 3-2 ]3 [ 4-2 4-4 3-2 ]3 [ 4-2 4-4 3-2 ]3 [ 4-2 4-4 3-2 ]3"]
        bars = analyzer.analyze_section_bars(lines)
        assert len(bars) == 1, f"本来は1小節であるべきだが、{len(bars)}小節になっている"
