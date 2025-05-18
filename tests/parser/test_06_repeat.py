import pytest
from tabscript.parser.analyzer import StructureAnalyzer
from tabscript.exceptions import ParseError
from tabscript.parser import Parser

def test_single_bar_repeat():
    """1小節リピートのテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """
    # テスト
    3-3:4 4-4:4 5-5:4 6-6:4
    ...
    """
    metadata, sections = analyzer.analyze(text)
    assert len(sections) == 1
    bars = sections[0]["bars"]
    assert len(bars) == 2
    assert bars[1].is_repeat_symbol
    assert bars[1].repeat_bars == 1

def test_double_bar_repeat():
    """2小節リピートのテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """
    # テスト
    3-3:4 4-4:4 5-5:4 6-6:4
    1-1:4 2-2:4 3-3:4 4-4:4
    ...2
    """
    metadata, sections = analyzer.analyze(text)
    assert len(sections) == 1
    bars = sections[0]["bars"]
    assert len(bars) == 3  # 2小節 + リピート記号
    assert bars[2].is_repeat_symbol
    assert bars[2].repeat_bars == 2

def test_quadruple_bar_repeat():
    """4小節リピートのテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """
    # テスト
    3-3:4 4-4:4 5-5:4 6-6:4
    1-1:4 2-2:4 3-3:4 4-4:4
    5-5:4 6-6:4 1-1:4 2-2:4
    3-3:4 4-4:4 5-5:4 6-6:4
    ...4
    """
    metadata, sections = analyzer.analyze(text)
    assert len(sections) == 1
    bars = sections[0]["bars"]
    assert len(bars) == 5  # 4小節 + リピート記号
    assert bars[4].is_repeat_symbol
    assert bars[4].repeat_bars == 4

def test_multiple_repeats():
    """複数のリピートの組み合わせテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """
    # テスト
    3-3:4 4-4:4 5-5:4 6-6:4
    ...
    1-1:4 2-2:4 3-3:4 4-4:4
    ...2
    5-5:4 6-6:4 1-1:4 2-2:4
    ...4
    """
    metadata, sections = analyzer.analyze(text)
    assert len(sections) == 1
    bars = sections[0]["bars"]
    assert len(bars) == 6  # 3小節 + 3つのリピート記号
    assert bars[1].is_repeat_symbol and bars[1].repeat_bars == 1
    assert bars[3].is_repeat_symbol and bars[3].repeat_bars == 2
    assert bars[5].is_repeat_symbol and bars[5].repeat_bars == 4

def test_invalid_repeat_count():
    """無効なリピート回数のテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """
    # テスト
    3-3:4 4-4:4 5-5:4 6-6:4
    ...3
    """
    with pytest.raises(ParseError):
        analyzer.analyze(text)

def test_invalid_repeat_position():
    """不正な位置のリピート記号のテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """
    # テスト
    3-3:4 4-4:4 ... 5-5:4 6-6:4
    """
    with pytest.raises(ParseError):
        analyzer.analyze(text)

def test_insufficient_bars_for_repeat():
    """リピートに必要な小節数が不足している場合のテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """
    # テスト
    3-3:4 4-4:4 5-5:4 6-6:4
    ...2
    """
    with pytest.raises(ParseError):
        analyzer.analyze(text)

# パーサーのテスト
def test_parser_single_bar_repeat():
    """パーサーでの1小節リピートのテスト"""
    parser = Parser()
    text = """
    # テスト
    3-3:4 4-4:4 5-5:4 6-6:4
    ...
    """
    result = parser.parse(text)
    assert result.is_valid
    assert len(result.sections[0].bars) == 2
    assert result.sections[0].bars[1].is_repeat_symbol
    assert result.sections[0].bars[1].repeat_bars == 1
    assert result.sections[0].bars[1].is_dummy

def test_parser_double_bar_repeat():
    """パーサーでの2小節リピートのテスト"""
    parser = Parser()
    text = """
    # テスト
    3-3:4 4-4:4 5-5:4 6-6:4
    1-1:4 2-2:4 3-3:4 4-4:4
    ...2
    """
    result = parser.parse(text)
    assert result.is_valid
    assert len(result.sections[0].bars) == 3  # 2小節 + リピート記号
    assert result.sections[0].bars[2].is_repeat_symbol
    assert result.sections[0].bars[2].repeat_bars == 2

def test_parser_quadruple_bar_repeat():
    """パーサーでの4小節リピートのテスト"""
    parser = Parser()
    text = """
    # テスト
    3-3:4 4-4:4 5-5:4 6-6:4
    1-1:4 2-2:4 3-3:4 4-4:4
    5-5:4 6-6:4 1-1:4 2-2:4
    3-3:4 4-4:4 5-5:4 6-6:4
    ...4
    """
    result = parser.parse(text)
    assert result.is_valid
    assert len(result.sections[0].bars) == 5  # 4小節 + リピート記号
    assert result.sections[0].bars[4].is_repeat_symbol
    assert result.sections[0].bars[4].repeat_bars == 4

def test_parser_repeat_with_notes():
    """リピート記号を含む小節に音符が含まれている場合のテスト"""
    parser = Parser()
    text = """
    # テスト
    3-3:4 4-4:4 5-5:4 6-6:4
    ... 2-1:4 2-2:4  # リピート記号の後に音符がある
    """
    with pytest.raises(ParseError):
        parser.parse(text)

def test_parser_repeat_with_chord():
    """リピート記号を含む小節にコードが含まれている場合のテスト"""
    parser = Parser()
    text = """
    # テスト
    3-3:4 4-4:4 5-5:4 6-6:4
    @Am ...  # リピート記号の前にコードがある
    """
    with pytest.raises(ParseError):
        parser.parse(text) 