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
def sample_score():
    score = Score(title="Test Score", tuning="EADGBE", beat="4/4", bars_per_line=4)
    section = Section()
    section.bar_group_size = 4
    for _ in range(8):
        section.bars.append(Bar())
    score.sections.append(section)
    return score

def calc_expected_bar_width(section, page_width, style_manager):
    bar_count = len(section.bars)
    group_size = getattr(section, 'bar_group_size', 4)
    num_groups = (bar_count + group_size - 1) // group_size
    bar_group_margin = style_manager.get("bar_group_margin")
    available_width = page_width - (bar_group_margin * (num_groups - 1))
    return available_width / (num_groups * group_size)

def test_calculate_section_layout(layout_calculator, style_manager, sample_score):
    page_width = 210 * mm
    section = sample_score.sections[0]
    bar_width, bar_group_width, bar_group_margin = layout_calculator.calculate_section_layout(
        section, page_width
    )
    assert bar_group_width == bar_width * 4
    assert bar_group_margin == 5 * mm
    expected_bar_width = calc_expected_bar_width(section, page_width, style_manager)
    assert abs(bar_width - expected_bar_width) < 0.1 * mm

def test_calculate_bar_width_single_group(layout_calculator, style_manager):
    section = Section("Single Group")
    section.bar_group_size = 4
    for _ in range(4):
        bar = Bar()
        bar.notes = [Note(string=1, fret="0", duration="4")]
        section.bars.append(bar)
    page_width = 210 * mm
    bar_width = layout_calculator._calculate_bar_width(section, page_width)
    expected_bar_width = calc_expected_bar_width(section, page_width, style_manager)
    assert abs(bar_width - expected_bar_width) < 0.1 * mm

def test_calculate_bar_width_multiple_groups(layout_calculator, style_manager):
    section = Section("Multiple Groups")
    section.bar_group_size = 4
    for _ in range(8):
        bar = Bar()
        bar.notes = [Note(string=1, fret="0", duration="4")]
        section.bars.append(bar)
    page_width = 210 * mm
    bar_width = layout_calculator._calculate_bar_width(section, page_width)
    expected_bar_width = calc_expected_bar_width(section, page_width, style_manager)
    assert abs(bar_width - expected_bar_width) < 0.1 * mm

def test_calculate_bar_width_with_repeat(layout_calculator, style_manager):
    section = Section("With Repeat")
    section.bar_group_size = 4
    for i in range(4):
        bar = Bar()
        bar.notes = [Note(string=1, fret="0", duration="4")]
        if i == 0:
            bar.repeat_start = True
        if i == 3:
            bar.repeat_end = True
        section.bars.append(bar)
    page_width = 210 * mm
    bar_width = layout_calculator._calculate_bar_width(section, page_width)
    expected_bar_width = calc_expected_bar_width(section, page_width, style_manager)
    assert abs(bar_width - expected_bar_width) < 0.1 * mm

def test_calculate_bar_width_with_volta(layout_calculator, style_manager):
    section = Section("With Volta")
    section.bar_group_size = 4
    for i in range(4):
        bar = Bar()
        bar.notes = [Note(string=1, fret="0", duration="4")]
        if i == 0:
            bar.volta_start = True
            bar.volta_number = 1
        if i == 3:
            bar.volta_end = True
        section.bars.append(bar)
    page_width = 210 * mm
    bar_width = layout_calculator._calculate_bar_width(section, page_width)
    expected_bar_width = calc_expected_bar_width(section, page_width, style_manager)
    assert abs(bar_width - expected_bar_width) < 0.1 * mm

def test_calculate_bar_width_with_triplet(layout_calculator, style_manager):
    section = Section("With Triplet")
    section.bar_group_size = 4
    for i in range(4):
        bar = Bar()
        if i == 0:
            for j in range(3):
                note = Note(string=1, fret=str(j), duration="8")
                note.tuplet = 3
                bar.notes.append(note)
        else:
            bar.notes = [Note(string=1, fret="0", duration="4")]
        section.bars.append(bar)
    page_width = 210 * mm
    bar_width = layout_calculator._calculate_bar_width(section, page_width)
    expected_bar_width = calc_expected_bar_width(section, page_width, style_manager)
    assert abs(bar_width - expected_bar_width) < 0.1 * mm

def test_calculate_bar_width_with_chord(layout_calculator, style_manager):
    section = Section("With Chord")
    section.bar_group_size = 4
    for i in range(4):
        bar = Bar()
        if i == 0:
            note = Note(string=1, fret="5", duration="4", is_chord=True, is_chord_start=True)
            note.chord_notes = [
                Note(string=2, fret="5", duration="4"),
                Note(string=3, fret="5", duration="4")
            ]
            bar.notes.append(note)
        else:
            bar.notes = [Note(string=1, fret="0", duration="4")]
        section.bars.append(bar)
    page_width = 210 * mm
    bar_width = layout_calculator._calculate_bar_width(section, page_width)
    expected_bar_width = calc_expected_bar_width(section, page_width, style_manager)
    assert abs(bar_width - expected_bar_width) < 0.1 * mm

def test_calculate_bar_width_with_rest(layout_calculator, style_manager):
    section = Section("With Rest")
    section.bar_group_size = 4
    for i in range(4):
        bar = Bar()
        if i == 0:
            note = Note(string=1, fret="0", duration="4", is_rest=True)
            bar.notes.append(note)
        else:
            bar.notes = [Note(string=1, fret="0", duration="4")]
        section.bars.append(bar)
    page_width = 210 * mm
    bar_width = layout_calculator._calculate_bar_width(section, page_width)
    expected_bar_width = calc_expected_bar_width(section, page_width, style_manager)
    assert abs(bar_width - expected_bar_width) < 0.1 * mm

def test_calculate_bar_positions(layout_calculator, sample_score):
    """小節の位置計算テスト"""
    section = sample_score.sections[0]
    page_width = 210 * mm
    bar_width, bar_group_width, bar_group_margin = layout_calculator.calculate_section_layout(
        section, page_width
    )
    x = 20 * mm  # 左マージン
    positions = layout_calculator.calculate_bar_positions(
        section, x, bar_width, bar_group_width, bar_group_margin
    )
    # 8小節分の位置が計算されていることを確認
    assert len(positions) == 8
    # 最初の小節の位置
    assert positions[0] == x
    # 4小節目の位置（最初のグループの最後）
    assert positions[3] == x + (3 * bar_width)
    # 5小節目の位置（2番目のグループの最初）
    assert positions[4] == x + bar_group_width + bar_group_margin
    # 最後の小節の位置
    assert positions[7] == x + bar_group_width + bar_group_margin + (3 * bar_width)

def test_calculate_string_positions(layout_calculator):
    """弦の位置計算テスト"""
    y = 100 * mm
    positions = layout_calculator.calculate_string_positions(y)
    
    # 6弦分の位置が計算されていることを確認
    assert len(positions) == 6
    
    # 各弦の間隔が正しいことを確認
    string_spacing = 3 * mm
    for i in range(6):
        assert positions[i] == y + (i * string_spacing) 