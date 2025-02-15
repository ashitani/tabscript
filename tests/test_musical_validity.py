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