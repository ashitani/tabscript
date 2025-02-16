import pytest
from tabscript.parser import Parser
from tabscript.exceptions import ParseError
from tabscript.models import Score

def test_metadata_extraction():
    """メタデータの抽出をテスト"""
    parser = Parser()
    text = """
    $title="Test Score"
    $tuning="guitar"
    $beat="4/4"
    $bars_per_line="3"
    """
    structure = parser._extract_structure(text)
    
    assert structure.metadata['title'] == 'Test Score'
    assert structure.metadata['tuning'] == 'guitar'
    assert structure.metadata['beat'] == '4/4'
    assert structure.metadata['bars_per_line'] == '3'

def test_invalid_metadata():
    """不正なメタデータをテスト"""
    parser = Parser()
    with pytest.raises(ParseError, match="Invalid metadata format"):
        parser._extract_structure('$title=Test')  # クォートなし
    
    with pytest.raises(ParseError, match="Invalid metadata format"):
        parser._extract_structure('$title="Test')  # 終端クォートなし

def test_section_structure():
    """セクション構造の解析をテスト"""
    parser = Parser()
    text = """
    [Intro]
    3-3:4 4-4:4
    5-5:4 6-6:4
    
    [A]
    1-1:4 2-2:4
    """
    structure = parser._extract_structure(text)
    
    assert len(structure.sections) == 2
    assert structure.sections[0].name == 'Intro'
    assert len(structure.sections[0].content) == 2
    assert structure.sections[1].name == 'A'
    assert len(structure.sections[1].content) == 1

def test_bar_structure():
    """小節構造の解析をテスト"""
    parser = Parser()
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    
    lines = [
        '{ 3-3:4 4-4:4 }',  # より自然な形式に修正
        '1-1:4 2-2:4'
    ]
    bars = parser._analyze_section_bars(lines)
    
    assert len(bars) == 2
    assert bars[0].repeat_start
    assert bars[0].repeat_end
    assert bars[0].content == '3-3:4 4-4:4'
    assert not bars[1].repeat_start
    assert not bars[1].repeat_end

def test_volta_structure():
    """n番カッコの構造解析をテスト"""
    parser = Parser()
    parser.debug_mode = True
    lines = [
        '{1 3-3:4 4-4:4 }1',  # {1 content }1 形式に修正
        '{2 5-5:4 6-6:4 }2'   # {1 content }1 形式に修正
    ]
    bars = parser._analyze_section_bars(lines)
    
    assert len(bars) == 2
    assert bars[0].volta_number == 1
    assert bars[1].volta_number == 2

def test_empty_section():
    """空のセクションの処理をテスト"""
    parser = Parser()
    text = """
    [Empty]
    
    [Next]
    1-1:4
    """
    structure = parser._extract_structure(text)
    
    assert len(structure.sections) == 2
    assert structure.sections[0].name == 'Empty'
    assert len(structure.sections[0].content) == 0
    assert structure.sections[1].name == 'Next'
    assert len(structure.sections[1].content) == 1 