import pytest
from tabscript import parser
from tabscript.exceptions import ParseError
from tabscript.parser import Parser

def test_basic_parsing():
    p = parser()
    score = p.parse("tests/data/sample.tab")
    
    assert score.title == "Test song"
    assert score.tuning == "guitar"
    assert score.beat == "4/4"
    assert len(score.sections) == 2
    
    # Introセクションのチェック
    intro = score.sections[0]
    assert intro.name == "Intro"
    assert len(intro.bars) == 2
    assert intro.bars[0].notes[0].chord == "B"  # 小節ではなく音符のコードをチェック
    
    # Aセクションのチェック
    section_a = score.sections[1]
    assert section_a.name == "A"
    assert len(section_a.bars) == 4

def test_invalid_metadata():
    p = parser()
    with pytest.raises(ParseError) as exc_info:
        p.parse("tests/data/invalid_metadata.tab")
    assert "Invalid metadata format" in str(exc_info.value)

def test_parse_basic_structure():
    """基本的な構造のパースをテスト"""
    p = Parser()
    score = p.parse("""
    $title="Test Score"
    $tuning="guitar"
    $beat="4/4"
    
    [A]
    @Cmaj7 3-3:4 @Dm7 4-5:4
    """)
    
    assert score.title == "Test Score"
    assert len(score.sections) == 1
    assert score.sections[0].name == "A"
    assert len(score.sections[0].columns[0].bars) == 1
    
    # 最初の小節の検証
    bar = score.sections[0].columns[0].bars[0]
    assert len(bar.notes) == 2
    assert bar.notes[0].string == 3
    assert bar.notes[0].fret == "3"
    assert bar.notes[0].duration == "4"
    assert bar.notes[0].chord == "Cmaj7" 

def test_no_section_name():
    """セクション名なしでも動作することをテスト"""
    parser = Parser()
    score = parser.parse("""
    3-3:4 4-4 5-5
    """)
    
    assert len(score.sections) == 1
    assert score.sections[0].name == ""
    assert len(score.sections[0].columns) == 1
    assert len(score.sections[0].columns[0].bars) == 1
    assert len(score.sections[0].columns[0].bars[0].notes) == 3
    