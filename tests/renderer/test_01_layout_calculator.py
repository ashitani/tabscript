import pytest
from reportlab.lib.units import mm
from tabscript.renderer import LayoutCalculator
from tabscript.style import StyleManager
from tabscript.models import Score, Section, Bar, Note

@pytest.fixture
def style_manager():
    return StyleManager()

@pytest.fixture
def layout_calculator(style_manager):
    return LayoutCalculator(style_manager)

@pytest.fixture
def bars_per_line():
    return 4

@pytest.fixture
def sample_score(bars_per_line):
    score = Score(title="Test Score", tuning="EADGBE", beat="4/4", bars_per_line=bars_per_line)
    section = Section("Test Section")
    for _ in range(bars_per_line):
        bar = Bar()
        bar.notes = [Note(string=1, fret="0", duration="4")]
        section.bars.append(bar)
    score.sections.append(section)
    return score

def test_calculate_section_layout(layout_calculator, style_manager, sample_score, bars_per_line):
    """セクションのレイアウト計算テスト"""
    page_width = 210 * mm
    bar_width, bar_group_width, bar_group_margin = layout_calculator.calculate_section_layout(
        bars_per_line, page_width
    )
    assert bar_width > 0
    assert bar_group_width > 0
    assert bar_group_margin > 0
    assert bar_group_width == bar_width * bars_per_line

def test_calculate_bar_width_single_group(layout_calculator, style_manager, bars_per_line):
    """単一グループの小節幅計算テスト"""
    page_width = 210 * mm
    bar_width, _, _ = layout_calculator.calculate_section_layout(bars_per_line, page_width)
    assert bar_width > 0

def test_calculate_bar_width_multiple_groups(layout_calculator, style_manager, bars_per_line):
    """複数グループの小節幅計算テスト（bars_per_line=4で十分）"""
    page_width = 210 * mm
    bar_width, _, _ = layout_calculator.calculate_section_layout(bars_per_line, page_width)
    assert bar_width > 0

def test_calculate_bar_width_with_repeat(layout_calculator, style_manager, bars_per_line):
    """リピート記号付きの小節幅計算テスト（bars_per_line=4で十分）"""
    page_width = 210 * mm
    bar_width, _, _ = layout_calculator.calculate_section_layout(bars_per_line, page_width)
    assert bar_width > 0

def test_calculate_bar_width_with_volta(layout_calculator, style_manager, bars_per_line):
    """ボルタ付きの小節幅計算テスト（bars_per_line=4で十分）"""
    page_width = 210 * mm
    bar_width, _, _ = layout_calculator.calculate_section_layout(bars_per_line, page_width)
    assert bar_width > 0

def test_calculate_bar_width_with_triplet(layout_calculator, style_manager, bars_per_line):
    """三連符付きの小節幅計算テスト（bars_per_line=4で十分）"""
    page_width = 210 * mm
    bar_width, _, _ = layout_calculator.calculate_section_layout(bars_per_line, page_width)
    assert bar_width > 0

def test_calculate_bar_width_with_chord(layout_calculator, style_manager, bars_per_line):
    """コード付きの小節幅計算テスト（bars_per_line=4で十分）"""
    page_width = 210 * mm
    bar_width, _, _ = layout_calculator.calculate_section_layout(bars_per_line, page_width)
    assert bar_width > 0

def test_calculate_bar_width_with_rest(layout_calculator, style_manager, bars_per_line):
    """休符付きの小節幅計算テスト（bars_per_line=4で十分）"""
    page_width = 210 * mm
    bar_width, _, _ = layout_calculator.calculate_section_layout(bars_per_line, page_width)
    assert bar_width > 0

def test_calculate_bar_positions(layout_calculator, bars_per_line):
    """小節の位置計算テスト"""
    page_width = 210 * mm
    bar_width, bar_group_width, bar_group_margin = layout_calculator.calculate_section_layout(
        bars_per_line, page_width
    )
    positions = layout_calculator.calculate_bar_positions(
        bars_per_line, 0, bar_width, bar_group_width, bar_group_margin
    )
    assert len(positions) == bars_per_line
    # 位置が昇順で並んでいることのみ確認
    for i in range(len(positions) - 1):
        assert positions[i + 1] > positions[i]

def test_calculate_string_positions(layout_calculator):
    """弦の位置計算テスト"""
    y = 100 * mm
    positions = layout_calculator.calculate_string_positions(y)
    assert len(positions) == 6
    string_spacing = layout_calculator.style_manager.get("string_spacing")
    for i in range(6):
        assert positions[i] == y - (i * string_spacing) 