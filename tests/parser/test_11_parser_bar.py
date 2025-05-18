import pytest
from tabscript.parser.analyzer import StructureAnalyzer
from tabscript.exceptions import ParseError

def test_basic_repeat():
    """基本的な繰り返し記号の解析をテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """1-0:4 2-0:4 3-0:4 4-0:4
{ 1-0:4 2-0:4 3-0:4 4-0:4 }
1-0:4 2-0:4 3-0:4 4-0:4"""
    
    metadata, sections = analyzer.analyze(text)
    assert len(sections) == 1
    bars = sections[0]["bars"]
    
    # 繰り返し記号の検証
    assert not bars[0].repeat_start
    assert not bars[0].repeat_end
    assert bars[1].repeat_start
    assert bars[1].repeat_end
    assert not bars[2].repeat_start
    assert not bars[2].repeat_end

def test_repeat_with_volta():
    """繰り返し記号とn番カッコの組み合わせをテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """1-0:4 2-0:4 3-0:4 4-0:4
{ 1-0:4 2-0:4 3-0:4 4-0:4
{1 5-5:4 6-6:4 }1
{2 1-1:4 2-2:4 }2 }"""
    
    metadata, sections = analyzer.analyze(text)
    assert len(sections) == 1
    bars = sections[0]["bars"]
    
    # 繰り返し記号とn番カッコの検証
    assert not bars[0].repeat_start
    assert not bars[0].repeat_end
    assert bars[1].repeat_start
    assert not bars[1].repeat_end
    assert not bars[1].volta_number
    assert bars[2].repeat_start
    assert bars[2].repeat_end
    assert bars[2].volta_number == 1
    assert bars[3].repeat_start
    assert bars[3].repeat_end
    assert bars[3].volta_number == 2

def test_invalid_volta_pair():
    """無効なn番カッコのペアをテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    
    # 1番カッコのみの場合
    text1 = """1-0:4 2-0:4 3-0:4 4-0:4
{ 1-0:4 2-0:4 3-0:4 4-0:4
{1 5-5:4 6-6:4 }1"""
    
    with pytest.raises(ParseError):
        analyzer.analyze(text1)
    
    # 2番カッコのみの場合
    text2 = """1-0:4 2-0:4 3-0:4 4-0:4
{ 1-0:4 2-0:4 3-0:4 4-0:4
{2 1-1:4 2-2:4 }2"""
    
    with pytest.raises(ParseError):
        analyzer.analyze(text2)

def test_invalid_volta_order():
    """無効なn番カッコの順序をテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    
    # 2番カッコが1番カッコより先にある場合
    text = """1-0:4 2-0:4 3-0:4 4-0:4
{ 1-0:4 2-0:4 3-0:4 4-0:4
{2 1-1:4 2-2:4 }2
{1 5-5:4 6-6:4 }1"""
    
    with pytest.raises(ParseError):
        analyzer.analyze(text)

def test_invalid_volta_duplicate():
    """重複したn番カッコをテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    
    # 同じ番号のn番カッコが複数ある場合
    text = """1-0:4 2-0:4 3-0:4 4-0:4
{ 1-0:4 2-0:4 3-0:4 4-0:4
{1 5-5:4 6-6:4 }1
{1 1-1:4 2-2:4 }1
{2 1-1:4 2-2:4 }2"""
    
    with pytest.raises(ParseError):
        analyzer.analyze(text)

def test_invalid_volta_nesting():
    """無効なn番カッコの入れ子をテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    
    # n番カッコが入れ子になっている場合
    text = """1-0:4 2-0:4 3-0:4 4-0:4
{ 1-0:4 2-0:4 3-0:4 4-0:4
{1 5-5:4 6-6:4
{2 1-1:4 2-2:4 }2 }1"""
    
    with pytest.raises(ParseError):
        analyzer.analyze(text)

def test_invalid_volta_outside():
    """無印カッコの外にn番カッコがある場合をテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    
    text = """1-0:4 2-0:4 3-0:4 4-0:4
{ 1-0:4 2-0:4 3-0:4 4-0:4 }
{1 5-5:4 6-6:4 }1
{2 1-1:4 2-2:4 }2"""
    
    with pytest.raises(ParseError):
        analyzer.analyze(text)

def test_complex_repeat_structure():
    """複雑な繰り返し構造の解析をテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """1-0:4 2-0:4 3-0:4 4-0:4
{ 1-0:4 2-0:4 3-0:4 4-0:4
{1 5-5:4 6-6:4 }1
{2 1-1:4 2-2:4 }2 }
1-0:4 2-0:4 3-0:4 4-0:4 """
    
    metadata, sections = analyzer.analyze(text)
    assert len(sections) == 1
    bars = sections[0]["bars"]
    
    # 複雑な繰り返し構造の検証
    assert not bars[0].repeat_start
    assert not bars[0].repeat_end
    assert bars[1].repeat_start
    assert not bars[1].repeat_end
    assert not bars[1].volta_number
    assert bars[2].repeat_start
    assert bars[2].repeat_end
    assert bars[2].volta_number == 1
    assert bars[3].repeat_start
    assert bars[3].repeat_end
    assert bars[3].volta_number == 2
    assert not bars[4].repeat_start
    assert not bars[4].repeat_end
    assert not bars[4].volta_number


def test_repeat_basic():
    """基本的な繰り返し記号の解析をテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """1-0:4 2-0:4 3-0:4 4-0:4
{ 1-0:4 2-0:4 3-0:4 4-0:4 }
1-0:4 2-0:4 3-0:4 4-0:4"""
    
    metadata, sections = analyzer.analyze(text)
    assert len(sections) == 1
    bars = sections[0]["bars"]
    
    # 基本的な繰り返し記号の検証
    assert not bars[0].repeat_start
    assert not bars[0].repeat_end
    assert bars[1].repeat_start
    assert bars[1].repeat_end
    assert not bars[2].repeat_start
    assert not bars[2].repeat_end

def test_repeat_separate_brackets():
    """別々の繰り返し記号の解析をテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """1-0:4 2-0:4 3-0:4 4-0:4
{ 1-0:4 2-0:4 3-0:4 4-0:4
1-0:4 2-0:4 3-0:4 4-0:4 }"""
    
    metadata, sections = analyzer.analyze(text)
    assert len(sections) == 1
    bars = sections[0]["bars"]
    
    # 別々の繰り返し記号の検証
    assert not bars[0].repeat_start
    assert not bars[0].repeat_end
    assert bars[1].repeat_start
    assert not bars[1].repeat_end
    assert not bars[2].repeat_start
    assert bars[2].repeat_end


def test_multi_bar_volta():
    """複数小節を含むn番カッコの解析をテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """1-0:4 2-0:4 3-0:4 4-0:4
{ 1-0:4 2-0:4 3-0:4 4-0:4 
{1 5-5:4 6-6:4 }1
{2 1-0:4 2-0:4 3-0:4 4-0:4 }2 }"""
    
    metadata, sections = analyzer.analyze(text)
    assert len(sections) == 1
    bars = sections[0]["bars"]
    
    # 複数小節を含むn番カッコの検証
    assert not bars[0].repeat_start
    assert not bars[0].repeat_end
    assert bars[1].repeat_start
    assert not bars[1].repeat_end
    assert not bars[1].volta_number
    assert bars[2].repeat_start
    assert bars[2].repeat_end
    assert bars[2].volta_number == 1
    assert bars[3].repeat_start
    assert bars[3].repeat_end
    assert bars[3].volta_number == 2

def test_analyze_section_bars_with_repeat_marks():
    """繰り返し記号を含む小節の解析をテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """1-0:4 2-0:4 3-0:4 4-0:4
{ 1-0:4 2-0:4 3-0:4 4-0:4 }
1-0:4 2-0:4 3-0:4 4-0:4"""
    
    metadata, sections = analyzer.analyze(text)
    assert len(sections) == 1
    bars = sections[0]["bars"]
    
    # 繰り返し記号を含む小節の検証
    assert not bars[0].repeat_start
    assert not bars[0].repeat_end
    assert bars[1].repeat_start
    assert bars[1].repeat_end
    assert not bars[2].repeat_start
    assert not bars[2].repeat_end


def test_analyze_section_with_multiline_repeat():
    """複数行にまたがる繰り返しの解析をテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """1-0:4 2-0:4 3-0:4 4-0:4
{ 1-0:4 2-0:4 3-0:4 4-0:4 }
{ 1-0:4 2-0:4 3-0:4 4-0:4 }"""
    
    metadata, sections = analyzer.analyze(text)
    assert len(sections) == 1
    bars = sections[0]["bars"]
    
    # 複数行にまたがる繰り返しの検証
    assert not bars[0].repeat_start
    assert not bars[0].repeat_end
    assert bars[1].repeat_start
    assert bars[1].repeat_end
    assert bars[2].repeat_start
    assert bars[2].repeat_end 

