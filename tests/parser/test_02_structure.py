import pytest
from tabscript.parser import Parser
from tabscript.exceptions import ParseError
from tabscript.models import Score

def test_metadata_extraction(debug_level):
    """メタデータ抽出のテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    
    text = """
    $title="Test Score"
    $tuning="guitar"
    $beat="4/4"
    
    [Section1]
    1-1:4 2-2:4
    """
    
    structure = parser._extract_structure(text)
    
    assert structure.metadata["title"] == "Test Score"
    assert structure.metadata["tuning"] == "guitar"
    assert structure.metadata["beat"] == "4/4"

def test_invalid_metadata(debug_level):
    """無効なメタデータのテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    
    # 引用符なし
    text = """
    $title=Test Score
    [Section1]
    1-1:4 2-2:4
    """
    
    with pytest.raises(ParseError, match="Invalid metadata format"):
        parser._extract_structure(text)
    
    # 閉じ引用符なし
    text = """
    $title="Test Score
    [Section1]
    1-1:4 2-2:4
    """
    
    with pytest.raises(ParseError, match="Invalid metadata format"):
        parser._extract_structure(text)

def test_section_structure(debug_level):
    """セクション構造の解析をテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    
    text = """
    $title="Test Score"
    
    [Intro]
    1-1:4 2-2:4
    3-3:4 4-4:4
    
    [Verse]
    5-5:4 6-6:4
    """
    
    structure = parser._extract_structure(text)
    
    assert len(structure.sections) == 2
    
    # Introセクション
    assert structure.sections[0].name == "Intro"
    assert len(structure.sections[0].content) == 2
    assert "1-1:4 2-2:4" in structure.sections[0].content[0]
    assert "3-3:4 4-4:4" in structure.sections[0].content[1]
    
    # Verseセクション
    assert structure.sections[1].name == "Verse"
    assert len(structure.sections[1].content) == 1
    assert "5-5:4 6-6:4" in structure.sections[1].content[0]

def test_bar_structure(debug_level):
    """小節構造の解析をテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    
    lines = [
        '{ 3-3:4 4-4:4 }',  # より自然な形式に修正
        '1-1:4 2-2:4'
    ]
    # テストモードを有効にして呼び出し
    bars = parser._analyze_section_bars(lines)
    
    assert len(bars) == 2
    
    # 繰り返し記号付きの小節
    assert bars[0].content == "3-3:4 4-4:4"
    assert bars[0].repeat_start
    assert bars[0].repeat_end
    
    # 通常の小節
    assert bars[1].content == "1-1:4 2-2:4"
    assert not bars[1].repeat_start
    assert not bars[1].repeat_end

def test_volta_structure(debug_level):
    """n番カッコの構造解析をテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    lines = [
        "{ 1-1:4 2-2:4",  # 繰り返し開始と共通部分
        "{1 3-3:4 4-4:4 }1",  # 1番カッコ
        "{2 5-5:4 6-6:4 }2 }"  # 2番カッコと繰り返し終了
    ]
    # テストモードを有効にして呼び出し
    bars = parser._analyze_section_bars(lines)
    
    assert len(bars) == 3
    
    # 繰り返し開始と共通部分
    assert bars[0].content == "1-1:4 2-2:4"
    assert bars[0].repeat_start
    assert not bars[0].repeat_end
    
    # 1番カッコ
    assert bars[1].content == "3-3:4 4-4:4"
    assert bars[1].volta_number == 1
    assert bars[1].volta_start
    assert bars[1].volta_end
    
    # 2番カッコと繰り返し終了
    assert bars[2].content == "5-5:4 6-6:4"
    assert bars[2].volta_number == 2
    assert bars[2].volta_start
    assert bars[2].volta_end
    assert bars[2].repeat_end  # 繰り返し終了も含む

def test_empty_section(debug_level):
    """空のセクションのテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    
    text = """
    $title="Test Score"
    
    [Intro]
    
    [Verse]
    5-5:4 6-6:4
    """
    
    structure = parser._extract_structure(text)
    
    assert len(structure.sections) == 2
    
    # Introセクション（空）
    assert structure.sections[0].name == "Intro"
    assert len(structure.sections[0].content) == 0
    
    # Verseセクション
    assert structure.sections[1].name == "Verse"
    assert len(structure.sections[1].content) == 1
    assert "5-5:4 6-6:4" in structure.sections[1].content[0]