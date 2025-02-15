import pytest
from tabscript.parser import Parser
from tabscript.exceptions import ParseError

def test_bar_duration():
    """小節の長さが正しいことをテスト"""
    parser = Parser()
    score = parser.parse("""
    [Test]
    @Cmaj7 3-3:8 r8 r8. 3:16 3:8 r8 r4
    """)
    
    bar = score.sections[0].columns[0].bars[0]
    total_steps = sum(note.step for note in bar.notes)
    assert total_steps == 16  # 4/4拍子なら16ステップ
    
    # 付点音符のステップ数を検証
    assert bar.notes[2].duration == "8."
    assert bar.notes[2].step == 3  # 付点8分音符は3ステップ

def test_duration_inheritance():
    """音価の継承が正しく機能することをテスト"""
    parser = Parser()
    score = parser.parse("""
    [Test]
    3-3:8 4 5 6  # 全て8分音符として解釈されるべき
    """)
    
    bar = score.sections[0].columns[0].bars[0]
    for note in bar.notes:
        assert note.duration == "8"
        assert note.step == 1 

def test_slur_duration():
    """スラー記号が音価の計算に影響を与えないことをテスト"""
    parser = Parser()
    
    # スラーなしの場合
    score1 = parser.parse("""
    [Test]
    3-3:8 4-4:8 5-5:8 6-6:8
    """)
    bar1 = score1.sections[0].columns[0].bars[0]
    total_steps1 = sum(note.step for note in bar1.notes)
    
    # スラーありの場合（同じ音価）
    score2 = parser.parse("""
    [Test]
    3-3:8& 4-4:8& 5-5:8& 6-6:8
    """)
    bar2 = score2.sections[0].columns[0].bars[0]
    total_steps2 = sum(note.step for note in bar2.notes)
    
    # スラーの有無で音価（ステップ数）は変わらないはず
    assert total_steps1 == total_steps2 