import pytest
from tabscript.parser.analyzer import StructureAnalyzer
from tabscript.exceptions import ParseError
from tabscript.models import BarInfo

def test_analyze_section_bars_basic():
    """基本的な小節解析のテスト"""
    analyzer = StructureAnalyzer()
    lines = [
        "1-1:4 2-2:4 3-3:4 4-4:4",
        "5-5:4 6-6:4 6-0:4 1-0:4"
    ]
    bars = analyzer.analyze_section_bars(lines)
    
    assert len(bars) == 2
    assert bars[0].content == "1-1:4 2-2:4 3-3:4 4-4:4"
    assert bars[1].content == "5-5:4 6-6:4 6-0:4 1-0:4"
    
    # すべての小節にフラグが設定されていないことを確認
    for bar in bars:
        assert not bar.repeat_start
        assert not bar.repeat_end
        assert not bar.volta_start
        assert not bar.volta_end
        assert bar.volta_number is None

def test_standalone_repeat_brackets():
    """単体の繰り返し括弧のテスト - 前処理後の形式に修正"""
    analyzer = StructureAnalyzer()
    # 前処理後の形式（繰り返し記号が一行化されている）
    lines = [
        "{ 1-0:8 2-0:8 }",
        "{ 3-0:8 4-0:8 }"
    ]
    bars = analyzer.analyze_section_bars(lines)
    
    assert len(bars) == 2
    # 各小節の内容とフラグを確認
    assert bars[0].content == "1-0:8 2-0:8"
    assert bars[0].repeat_start
    assert bars[0].repeat_end
    
    assert bars[1].content == "3-0:8 4-0:8"
    assert bars[1].repeat_start
    assert bars[1].repeat_end

def test_repeat_with_volta():
    """n番括弧を含む繰り返し構造のテスト - 前処理後の形式に修正"""
    analyzer = StructureAnalyzer()
    # 前処理後の形式（n番括弧が一行化されている）
    lines = [
        "{ 1-1:4 2-2:4 }",
        "{1 3-3:4 4-4:4 }1",
        "{2 5-5:4 6-6:4 }2"
    ]
    bars = analyzer.analyze_section_bars(lines)
    
    assert len(bars) == 3
    
    # 最初の小節（繰り返し開始＋終了）
    assert bars[0].content == "1-1:4 2-2:4"
    assert bars[0].repeat_start
    assert bars[0].repeat_end
    assert bars[0].volta_number is None
    
    # 1番括弧
    assert bars[1].content == "3-3:4 4-4:4"
    assert bars[1].volta_number == 1
    assert bars[1].volta_start
    assert bars[1].volta_end
    
    # 2番括弧
    assert bars[2].content == "5-5:4 6-6:4"
    assert bars[2].volta_number == 2
    assert bars[2].volta_start
    assert bars[2].volta_end


def test_analyze_nested_repeat():
    """入れ子の繰り返し構造のテスト - 前処理後の形式に修正"""
    analyzer = StructureAnalyzer()
    # 前処理後の形式（入れ子の繰り返しが一行化されている）
    lines = [
        "{ 1-1:4 2-2:4 }",
        "{ { 3-3:4 4-4:4 } }"
    ]
    bars = analyzer.analyze_section_bars(lines)
    
    assert len(bars) == 2
    
    # 最初の繰り返し
    assert bars[0].content == "1-1:4 2-2:4"
    assert bars[0].repeat_start
    assert bars[0].repeat_end
    
    # 入れ子の繰り返し（外側と内側の繰り返しフラグが両方設定）
    assert bars[1].content == "{ 3-3:4 4-4:4 }"
    assert bars[1].repeat_start
    assert bars[1].repeat_end

def test_complex_repeat_structure():
    """複雑な繰り返し構造のテスト - 前処理後の形式に修正"""
    analyzer = StructureAnalyzer()
    # 前処理後の形式
    lines = [
        "{ 1-1:4 2-2:4 ",
        "{1 3-3:4 4-4:4 }1",
        "{2 5-5:4 6-6:4 }2}"
    ]
    bars = analyzer.analyze_section_bars(lines)
    
    assert len(bars) == 3
    
    # 最初の繰り返し
    assert bars[0].content == "1-1:4 2-2:4"
    assert bars[0].repeat_start
    
    # 1番括弧（内部に繰り返しを含む）
    assert bars[1].content == "3-3:4 4-4:4"
    assert bars[1].volta_number == 1
    assert bars[1].volta_start
    assert bars[1].volta_end
    
    # 2番括弧
    assert bars[2].content == "5-5:4 6-6:4"
    assert bars[2].volta_number == 2
    assert bars[2].volta_start
    assert bars[2].volta_end
    assert bars[2].repeat_end

def test_volta_with_multiple_bars():
    """複数小節を含むn番括弧のテスト - 前処理後の形式に修正"""
    analyzer = StructureAnalyzer()
    # 前処理後の形式（volta内の複数小節が一行化されている）
    lines = [
        "{1 1-1:4 2-2:4 | 3-3:4 4-4:4 }1",
        "{2 5-5:4 6-6:4 | 1-1:4 2-2:4 }2"
    ]
    bars = analyzer.analyze_section_bars(lines)
    
    assert len(bars) == 2
    
    # 1番括弧（複数小節が｜で区切られている）
    assert bars[0].content == "1-1:4 2-2:4 | 3-3:4 4-4:4"
    assert bars[0].volta_number == 1
    assert bars[0].volta_start
    assert bars[0].volta_end
    
    # 2番括弧（複数小節が｜で区切られている）
    assert bars[1].content == "5-5:4 6-6:4 | 1-1:4 2-2:4"
    assert bars[1].volta_number == 2
    assert bars[1].volta_start
    assert bars[1].volta_end

# メタデータ解析テスト
def test_metadata_extraction():
    """メタデータが正しく抽出されるかテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """$title="Test Song"
$tuning="guitar"
$beat="4/4"

[Section1]
1-1:4 2-2:4
"""
    structure = analyzer.extract_structure(text)
    assert structure.metadata["title"] == "Test Song"
    assert structure.metadata["tuning"] == "guitar"
    assert structure.metadata["beat"] == "4/4"

def test_invalid_metadata():
    """不正なメタデータ形式でエラーが発生するかテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """$title=Test Song
[Section1]
1-1:4 2-2:4
"""
    with pytest.raises(ParseError):
        analyzer.extract_structure(text)

def test_parse_metadata_line():
    """メタデータ行の解析が正しく行われるかテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    line = '$title="Test Song"'
    key, value = analyzer._parse_metadata_line(line)
    assert key == "title"
    assert value == "Test Song"

# セクション構造テスト
def test_section_structure():
    """セクション構造が正しく抽出されるかテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """[Section1]
1-1:4 2-2:4

[Section2]
3-3:4 4-4:4
"""
    structure = analyzer.extract_structure(text)
    assert len(structure.sections) == 2
    assert structure.sections[0].name == "Section1"
    assert structure.sections[1].name == "Section2"
    assert len(structure.sections[0].content) == 1
    assert len(structure.sections[1].content) == 1

def test_empty_section():
    """空のセクションが正しく処理されるかテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """[Section1]

[Section2]
3-3:4 4-4:4
"""
    structure = analyzer.extract_structure(text)
    assert len(structure.sections) == 2
    assert structure.sections[0].name == "Section1"
    assert len(structure.sections[0].content) == 0

def test_parse_section_header():
    """セクションヘッダーの解析が正しく行われるかテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    line = '[Section Name]'
    name = analyzer._parse_section_header(line)
    assert name == "Section Name"

# 小節構造テスト
def test_bar_structure():
    """基本的な小節構造が正しく解析されるかテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    content = ["1-1:4 2-2:4", "3-3:4 4-4:4"]
    bars = analyzer.analyze_section_bars(content)
    assert len(bars) == 2
    assert bars[0].content == "1-1:4 2-2:4"
    assert bars[1].content == "3-3:4 4-4:4"

def test_volta_structure():
    """n番カッコの構造が正しく解析されるかテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    content = [
        "1-1:4 2-2:4",
        "{1 3-3:4 4-4:4 }1",
        "{2 5-5:4 6-6:4 }2"
    ]
    bars = analyzer.analyze_section_bars(content)
    assert len(bars) == 3
    assert bars[0].content == "1-1:4 2-2:4"
    assert bars[1].content == "3-3:4 4-4:4"
    assert bars[1].volta_number == 1
    assert bars[2].content == "5-5:4 6-6:4"
    assert bars[2].volta_number == 2

def test_repeat_basic():
    """基本的な繰り返し構造が正しく解析されるかテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    content = ["{ 1-1:4 2-2:4 }"]
    bars = analyzer.analyze_section_bars(content)
    assert len(bars) == 1
    assert bars[0].content == "1-1:4 2-2:4"
    assert bars[0].repeat_start == True
    assert bars[0].repeat_end == True

def test_repeat_separate_brackets():
    """分離した繰り返し括弧が正しく解析されるかテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    content = ["{ 1-1:4 2-2:4", "3-3:4 4-4:4 }"]
    bars = analyzer.analyze_section_bars(content)
    assert len(bars) == 2
    assert bars[0].content == "1-1:4 2-2:4"
    assert bars[0].repeat_start == True
    assert bars[0].repeat_end == False
    assert bars[1].content == "3-3:4 4-4:4"
    assert bars[1].repeat_start == False
    assert bars[1].repeat_end == True

def test_volta_brackets():
    """n番カッコが正しく解析されるかテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    content = ["{1 1-1:4 2-2:4 }1", "{2 3-3:4 4-4:4 }2"]
    bars = analyzer.analyze_section_bars(content)
    assert len(bars) == 2
    assert bars[0].volta_number == 1
    assert bars[0].volta_start == True
    assert bars[0].volta_end == True
    assert bars[1].volta_number == 2
    assert bars[1].volta_start == True
    assert bars[1].volta_end == True

def test_repeat_with_volta():
    """繰り返しとn番カッコの組み合わせが正しく解析されるかテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    content = [
        "{ 1-1:4 2-2:4",
        "{1 3-3:4 4-4:4 }1",
        "{2 5-5:4 6-6:4 }2 }"
    ]
    bars = analyzer.analyze_section_bars(content)
    assert len(bars) == 3
    assert bars[0].repeat_start == True
    assert bars[1].volta_number == 1
    assert bars[2].volta_number == 2
    assert bars[2].repeat_end == True

def test_complex_repeat_structure():
    """複雑な繰り返し構造が正しく解析されるかテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    content = [
        "{ 1-1:4 2-2:4",
        "{ 3-3:4 4-4:4 }",
        "{1 5-5:4 6-6:4 }1",
        "{2 1-1:4 2-2:4 }2 }"
    ]
    bars = analyzer.analyze_section_bars(content)
    assert len(bars) == 4
    assert bars[0].repeat_start == True
    assert bars[1].repeat_start == True
    assert bars[1].repeat_end == True
    assert bars[2].volta_number == 1
    assert bars[3].volta_number == 2
    assert bars[3].repeat_end == True

def test_repeat_end_only():
    """繰り返し終了のみの構造が正しく解析されるかテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    content = ["1-1:4 2-2:4 }"]
    bars = analyzer.analyze_section_bars(content)
    assert len(bars) == 1
    assert bars[0].repeat_start == False
    assert bars[0].repeat_end == True

def test_multi_bar_volta():
    """複数小節にまたがるn番カッコが正しく解析されるかテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    content = [
        "{1 1-1:4 2-2:4",
        "3-3:4 4-4:4 }1",
        "{2 5-5:4 6-6:4",
        "1-1:4 2-2:4 }2"
    ]
    bars = analyzer.analyze_section_bars(content)
    assert len(bars) == 4
    assert bars[0].volta_number == 1
    assert bars[0].volta_start == True
    assert bars[1].volta_number == 1
    assert bars[1].volta_end == True
    assert bars[2].volta_number == 2
    assert bars[2].volta_start == True
    assert bars[3].volta_number == 2
    assert bars[3].volta_end == True

def test_standalone_repeat_brackets():
    """単独の繰り返し括弧（{と}）を含む場合のテスト"""
    content = [
        "{ 1-0:8 1-2:8 1-3:8 1-5:8",
        "3-0:8 3-2:8 3-3:8 3-5:8 }"
    ]
    
    analyzer = StructureAnalyzer()
    bars = analyzer.analyze_section_bars(content)
    
    # 複数行のコンテンツが複数の小節として処理されることを検証
    assert len(bars) == 2
    
    # 1小節目の検証
    assert bars[0].content == "1-0:8 1-2:8 1-3:8 1-5:8"
    assert bars[0].repeat_start
    assert not bars[0].repeat_end
    
    # 2小節目の検証
    assert bars[1].content == "3-0:8 3-2:8 3-3:8 3-5:8"
    assert not bars[1].repeat_start
    assert bars[1].repeat_end
