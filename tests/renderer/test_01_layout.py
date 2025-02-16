import pytest
from tabscript.renderer import Renderer
from tabscript.models import Score, Section, Column, Bar, Note

def test_column_layout():
    """小節の配置計算をテスト"""
    score = Score(title="Test")
    section = Section(name="Test")
    column = Column(bars=[
        Bar(notes=[Note(string=1, fret="0", duration="4")]),
        Bar(notes=[Note(string=2, fret="0", duration="4")])
    ])
    section.columns.append(column)
    score.sections.append(section)
    
    renderer = Renderer(score)
    layout = renderer._calculate_layout()
    # レイアウトの検証 