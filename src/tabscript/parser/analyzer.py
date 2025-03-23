from typing import List, Optional, Tuple, Dict, Any, Union
from dataclasses import dataclass
from tabscript.exceptions import ParseError
from tabscript.models import BarInfo
import re

@dataclass
class Structure:
    """スコアの構造情報"""
    metadata: Dict[str, str]  # メタデータ（title, tuning, beatなど）
    sections: List['SectionInfo']  # セクション情報のリスト

    @property
    def title(self) -> str:
        """タイトルを取得"""
        return self.metadata.get('title', '')

    @property
    def tuning(self) -> str:
        """チューニングを取得"""
        return self.metadata.get('tuning', 'guitar')

    @property
    def beat(self) -> str:
        """拍子を取得"""
        return self.metadata.get('beat', '4/4')

@dataclass
class SectionInfo:
    """セクション情報"""
    name: str
    content: List[str]

@dataclass
class BarInfo:
    """小節の構造情報"""
    content: str
    repeat_start: bool = False
    repeat_end: bool = False
    volta_number: Optional[int] = None
    volta_start: bool = False
    volta_end: bool = False

class StructureAnalyzer:
    def __init__(self, debug_mode=False, debug_level=0):
        self.debug_mode = debug_mode
        self.debug_level = debug_level
        self.current_line = 0
        self.current_volta_number = None  # n番カッコの番号を保持
    
    def debug_print(self, *args, level: int = 1, **kwargs):
        """デバッグ出力を行う"""
        if self.debug_mode and level <= self.debug_level:
            print(*args, **kwargs)

    def extract_structure(self, text: str) -> Structure:
        """テキストから構造を抽出"""
        lines = text.split('\n')
        metadata = {}
        sections = []
        current_section = None
        current_content = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('$'):
                # メタデータ行
                key, value = self._parse_metadata_line(line)
                metadata[key] = value
            elif line.startswith('['):
                # セクション開始
                if current_section is not None:
                    sections.append(SectionInfo(name=current_section, content=current_content))
                current_section = line[1:-1].strip()
                current_content = []
            else:
                # セクションの内容
                if current_section is not None:
                    current_content.append(line)

        # 最後のセクションを追加
        if current_section is not None:
            sections.append(SectionInfo(name=current_section, content=current_content))

        return Structure(metadata=metadata, sections=sections)

    def _parse_metadata_line(self, line: str) -> Tuple[str, str]:
        """メタデータ行を解析"""
        if '=' not in line:
            raise ParseError("Invalid metadata format", self.current_line)

        key, value = line[1:].split('=', 1)
        key = key.strip()
        value = value.strip()

        # 値が引用符で囲まれているか確認
        if not (value.startswith('"') and value.endswith('"')):
            raise ParseError("Invalid metadata format", self.current_line)  # エラーメッセージを変更

        # 引用符を除去
        value = value[1:-1]
        return key, value

    def analyze_section_bars(self, lines: List[str]) -> List[BarInfo]:
        """セクション内の小節構造を解析
        
        Args:
            lines: セクションのテキスト行
            
        Returns:
            小節情報のリスト
        """
        if self.debug_mode:
            print("\n=== analyze_section_bars ===")
            print(f"Input lines: {lines}")
        
        bars = []
        # まずn番括弧を検出するパターン
        repeat_start_pattern = re.compile(r'^{(\s.*)?$')
        repeat_end_pattern = re.compile(r'^(.*\s)?}$')
        volta_start_pattern = re.compile(r'^{(\d+)(\s.*)?$')
        volta_end_pattern = re.compile(r'^(.*\s)?}(\d+)(\s.*)?$')  # 右側にさらにコンテンツがある可能性
        
        # 処理中の繰り返し情報を追跡
        current_volta_number = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # ケース1: n番括弧が1行にある場合（{n content }n）
            volta_bracket_pattern = re.compile(r'^\{(\d+)\s+(.*?)\s+\}\1(\s*\})?$')
            match = volta_bracket_pattern.match(line)
            if match:
                number = int(match.group(1))
                content = match.group(2)
                has_repeat_end = match.group(3) is not None
                
                # n番括弧の情報を設定
                bar = BarInfo(
                    content=content,
                    volta_number=number,
                    volta_start=True,
                    volta_end=True,
                    repeat_end=has_repeat_end
                )
                bars.append(bar)
                continue
            
            # ケース2: 繰り返し括弧が1行にある場合（{ content }）
            repeat_bracket_pattern = re.compile(r'^\{\s+(.*?)\s+\}$')
            match = repeat_bracket_pattern.match(line)
            if match:
                content = match.group(1)
                bars.append(BarInfo(
                    content=content,
                    repeat_start=True,
                    repeat_end=True
                ))
                continue
            
            # 以降の処理は複数行にまたがるケース
            # n番括弧開始（{n または {n + コンテンツの行）
            volta_start_match = volta_start_pattern.match(line)
            if volta_start_match:
                number = int(volta_start_match.group(1))
                current_volta_number = number
                
                # コンテンツ部分を抽出（{n を除去）
                prefix = f"{{{number}"
                content = line[len(prefix):].strip()
                
                bars.append(BarInfo(
                    content=content,
                    volta_number=number,
                    volta_start=True
                ))
                continue
            
            # n番括弧終了（}n または コンテンツ + }n の行）
            if '}' in line and re.search(r'\}\d+', line):
                volta_end_match = re.search(r'\}(\d+)(\s*\})?', line)
                if volta_end_match and current_volta_number is not None:
                    number = int(volta_end_match.group(1))
                    has_repeat_end = volta_end_match.group(2) is not None
                    
                    if number != current_volta_number:
                        raise ValueError(f"n番カッコの番号が一致しません: 開始={current_volta_number}, 終了={number}")
                    
                    # コンテンツ部分を抽出（}n を除去）
                    suffix = f"}}{number}"
                    suffix_idx = line.rfind(suffix)
                    content = line[:suffix_idx].strip()
                    
                    bars.append(BarInfo(
                        content=content,
                        volta_number=number,
                        volta_end=True,
                        repeat_end=has_repeat_end
                    ))
                    
                    # n番カッコ終了時に番号をリセット
                    current_volta_number = None
                    continue
            
            # 繰り返し開始の行（{ または { + コンテンツの行）
            if line.startswith('{'):
                if len(line) == 1:  # { だけの行
                    content = ""
                else:
                    content = line[1:].strip()  # { を除去
                
                bars.append(BarInfo(content, repeat_start=True))
                continue
            
            # 繰り返し終了の行（} または コンテンツ + } の行）
            if line.endswith('}'):
                if len(line) == 1:  # } だけの行
                    content = ""
                else:
                    content = line[:-1].strip()  # } を除去
                
                bars.append(BarInfo(content, repeat_end=True))
                continue
            
            # 通常の小節内容
            if current_volta_number is not None:
                # n番カッコ内の小節
                bars.append(BarInfo(line, volta_number=current_volta_number))
            else:
                # 通常の小節
                bars.append(BarInfo(line))
        
        if self.debug_mode:
            print(f"Output bars:")
            for i, bar in enumerate(bars):
                print(f"  Bar {i}:")
                print(f"    content: '{bar.content}'")
                print(f"    repeat_start: {bar.repeat_start}")
                print(f"    repeat_end: {bar.repeat_end}")
                print(f"    volta_number: {bar.volta_number}")
                print(f"    volta_start: {bar.volta_start}")
                print(f"    volta_end: {bar.volta_end}")
        
        return bars

    def _parse_section_header(self, line: str) -> str:
        """セクションヘッダー行を解析してセクション名を返す
        
        Args:
            line: セクションヘッダー行（例：'[Section Name]'）
            
        Returns:
            str: セクション名（例：'Section Name'）
            
        Raises:
            ParseError: セクションヘッダーの形式が不正な場合
        """
        if not (line.startswith('[') and line.endswith(']')):
            raise ParseError("Invalid section header format", self.current_line)
        
        # 角括弧を除去してセクション名を取得
        name = line[1:-1].strip()
        if not name:
            raise ParseError("Empty section name", self.current_line)
            
        return name 

    def analyze(self, text: str) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
        """テキストからメタデータとセクション構造を抽出
        
        Args:
            text: 前処理済みのテキスト
            
        Returns:
            Tuple[Dict[str, str], List[Dict[str, Any]]]: メタデータとセクション構造のタプル
        """
        structure = self.extract_structure(text)
        sections_data = []
        
        for section in structure.sections:
            # 各セクションの小節情報を解析
            bars = self.analyze_section_bars(section.content)
            
            sections_data.append({
                'name': section.name,
                'content': section.content,
                'bars': bars  # BarInfoオブジェクトのリストをそのまま使用
            })
        
        return structure.metadata, sections_data

    def _extract_structure(self, text: str) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
        """extract_structureのエイリアス（後方互換性のため）"""
        return self.extract_structure(text) 