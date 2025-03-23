import pytest
from tabscript.parser.analyzer import StructureAnalyzer
from tabscript.models import BarInfo

class TestStructureAnalyzer:
    def test_analyze_section_bars_with_newlines(self):
        """改行で区切られた小節が別々の小節として扱われることをテスト"""
        analyzer = StructureAnalyzer()
        
        # 複数行を含む小節内容
        content = [
            "1-0:8 1-2:8 1-3:8 1-5:8",
            "3-0:8 3-2:8 3-3:8 3-5:8"
        ]
        
        # 小節構造を解析
        bars = analyzer.analyze_section_bars(content)
        
        # 検証：2つの別々の小節として扱われるべき
        assert len(bars) == 2
        assert bars[0].content == "1-0:8 1-2:8 1-3:8 1-5:8"
        assert bars[1].content == "3-0:8 3-2:8 3-3:8 3-5:8"
    
    def test_analyze_section_bars_with_repeat_marks(self):
        """繰り返し記号を含む小節構造の解析をテスト"""
        analyzer = StructureAnalyzer()
        
        # 繰り返し記号を含む小節内容
        content = [
            "{ 1-0:4 1-2:4 2-0:4 2-2:4 }"
        ]
        
        # 小節構造を解析
        bars = analyzer.analyze_section_bars(content)
        
        # 検証：1つの小節、繰り返し開始と終了
        assert len(bars) == 1
        assert bars[0].content == "1-0:4 1-2:4 2-0:4 2-2:4"
        assert bars[0].repeat_start
        assert bars[0].repeat_end
    
    def test_analyze_section_bars_with_volta_brackets(self):
        """n番カッコを含む小節構造の解析をテスト"""
        analyzer = StructureAnalyzer()
        
        # n番カッコを含む小節内容
        content = [
            "{1 1-0:4 1-2:4 }1"
        ]
        
        # 小節構造を解析
        bars = analyzer.analyze_section_bars(content)
        
        # 検証：1つの小節、volta_numberが1
        assert len(bars) == 1
        assert bars[0].content == "1-0:4 1-2:4"
        assert bars[0].volta_number == 1
        assert bars[0].volta_start
        assert bars[0].volta_end 

    def test_analyze_section_with_multiline_repeat(self):
        """複数行にまたがるリピート構造をテスト"""
        content = [
            "{ 1-0:8 1-2:8 1-3:8 1-5:8",
            "3-0:8 3-2:8 3-3:8 3-5:8 }"
        ]
        
        analyzer = StructureAnalyzer()
        bars = analyzer.analyze_section_bars(content)
        
        assert len(bars) == 2
        assert bars[0].content == "1-0:8 1-2:8 1-3:8 1-5:8"
        assert bars[0].repeat_start
        assert not bars[0].repeat_end
        assert bars[1].content == "3-0:8 3-2:8 3-3:8 3-5:8"
        assert not bars[1].repeat_start
        assert bars[1].repeat_end 