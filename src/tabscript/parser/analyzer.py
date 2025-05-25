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
    is_repeat_symbol: bool = False  # ...記号かどうか
    repeat_bars: Optional[int] = None  # リピートする小節数

class StructureAnalyzer:
    def __init__(self, debug_mode=False, debug_level=0):
        self.debug_mode = debug_mode
        self.debug_level = debug_level
        self.current_line = 0
        self.current_volta_number = None  # n番カッコの番号を保持
        self.section_bar_count = 0  # セクション内の小節数を追跡
    
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
                # セクション名の切り替え
                if key == 'section':
                    if current_section is not None:
                        sections.append(SectionInfo(name=current_section, content=current_content))
                    current_section = value
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
        """メタデータ行を解析
        
        Args:
            line: 解析するメタデータ行
            
        Returns:
            Tuple[str, str]: メタデータのキーと値のタプル
            
        Raises:
            ParseError: メタデータの形式が不正な場合
        """
        # $で始まるメタデータ行の処理
        if line.startswith('$'):
            # $を除去してキーと値を分離
            parts = line[1:].split('=', 1)
            if self.debug_mode:
                print(f"[DEBUG] _parse_metadata_line: line='{line}' parts={parts}")
            
            # $newpageコマンドの特別処理
            if len(parts) == 1 and parts[0] == 'newpage':
                return 'newpage', ''
                
            if len(parts) != 2:
                if self.debug_mode:
                    print(f"[DEBUG] Invalid metadata format: line='{line}' parts={parts}")
                raise ParseError("Invalid metadata format", self.current_line)
            key = parts[0].strip()
            value = parts[1].strip()
            
            # 値が引用符で囲まれていることを確認
            if not (value.startswith('"') and value.endswith('"')):
                if self.debug_mode:
                    print(f"[DEBUG] Metadata value not quoted: value='{value}' line='{line}'")
                raise ParseError("Metadata value must be enclosed in quotes", self.current_line)
                
            value = value[1:-1]  # 引用符を除去
            return key, value
        
        # @で始まるメタデータ行の処理
        if line.startswith('@'):
            parts = line[1:].split('=', 1)
            if self.debug_mode:
                print(f"[DEBUG] _parse_metadata_line: line='{line}' parts={parts}")
            if len(parts) != 2:
                if self.debug_mode:
                    print(f"[DEBUG] Invalid metadata format: line='{line}' parts={parts}")
                raise ParseError("Invalid metadata format", self.current_line)
            key = parts[0].strip()
            value = parts[1].strip()
            
            # 値が引用符で囲まれていることを確認
            if not (value.startswith('"') and value.endswith('"')):
                if self.debug_mode:
                    print(f"[DEBUG] Metadata value not quoted: value='{value}' line='{line}'")
                raise ParseError("Metadata value must be enclosed in quotes", self.current_line)
                
            value = value[1:-1]  # 引用符を除去
            return key, value
        
        if self.debug_mode:
            print(f"[DEBUG] Invalid metadata format (not $ or @): line='{line}'")
        raise ParseError("Invalid metadata format", self.current_line)

    def analyze(self, text: str) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
        """テキストを解析してメタデータとセクション構造を返す
        
        Args:
            text: 解析するテキスト
            
        Returns:
            Tuple[Dict[str, str], List[Dict[str, Any]]]: メタデータとセクション構造のリスト
        """
        # メタデータとセクション構造を初期化
        metadata = {}
        sections = []
        current_section = None
        current_content = []
        current_bars_per_line = 4  # デフォルト値
        self.section_bar_count = 0  # セクション内の小節数をリセット
        
        # 行ごとに処理
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # メタデータ行の処理（$で始まる行）
            if line.startswith('$'):
                key, value = self._parse_metadata_line(line)
                metadata[key] = value
                # セクション名の切り替え
                if key == 'section':
                    # 前のセクションを保存
                    if current_section is not None and current_content:
                        current_section["bars"] = self.analyze_section_bars(current_content)
                        sections.append(current_section)
                        current_content = []
                    # 新しいセクションを開始
                    current_section = {"name": value, "bars": [], "bars_per_line": current_bars_per_line}
                    self.section_bar_count = 0  # セクション内の小節数をリセット
                # bars_per_lineの更新
                elif key == 'bars_per_line':
                    current_bars_per_line = int(value)
                    if current_section is not None:
                        current_section["bars_per_line"] = current_bars_per_line
                # $newpageコマンドの処理
                elif key == 'newpage':
                    if current_section is not None:
                        if "page_breaks" not in current_section:
                            current_section["page_breaks"] = []
                        current_section["page_breaks"].append(self.section_bar_count)
                continue
                
            # 通常の行（小節）の処理
            if current_section is None:
                # $section=が現れる前の小節はデフォルトセクションとして扱う
                current_section = {"name": "", "bars": [], "bars_per_line": current_bars_per_line}
            
            # 分割せず、そのままcurrent_contentに追加
            current_content.append(line)
            self.section_bar_count += 1  # セクション内の小節数をインクリメント
        
        # 最後のセクションを保存
        if current_section is not None and current_content:
            filtered_content = [l for l in current_content if not (l.startswith('[') and l.endswith(']')) and not l.startswith('#')]
            current_section["bars"] = self.analyze_section_bars(filtered_content)
            sections.append(current_section)
        
        return metadata, sections

    def analyze_section_bars(self, lines: List[str]) -> List[BarInfo]:
        """小節の解析を行う

        Args:
            lines (List[str]): 解析対象の行リスト

        Returns:
            List[BarInfo]: 解析結果の小節情報リスト
        """
        if self.debug_mode:
            print("\n=== analyze_section_bars ===")
            print(f"Input lines: {lines}")

        bars = []
        current_volta_number = None
        current_volta_start = False
        current_volta_end = False
        current_repeat_start = False
        current_repeat_end = False
        in_repeat = False
        repeat_stack = []  # 繰り返しのネストを管理するスタック
        volta_numbers = set()  # 使用済みのn番カッコの番号を管理
        volta_pairs = {}  # n番カッコのペアを管理 {番号: [開始位置, 終了位置]}
        bracket_count = 0  # 括弧のネストレベルを管理
        in_normal_repeat = False  # 通常の繰り返しの中にいるかどうか

        if self.debug_mode:
            print("\nInitial state:")
            print(f"  current_volta_number: {current_volta_number}")
            print(f"  volta_numbers: {volta_numbers}")
            print(f"  repeat_stack: {repeat_stack}")
            print(f"  bracket_count: {bracket_count}")
            print(f"  in_normal_repeat: {in_normal_repeat}")

        for i, line in enumerate(lines):
            # 空行をスキップ
            if not line.strip():
                continue
            
            line = line.strip()
            next_volta_number = None
            next_volta_start = False
            next_volta_end = False
            next_repeat_start = False
            next_repeat_end = False

            # --- 追加: フラグ伝播用 ---
            propagate_repeat_start = False
            propagate_volta_start = False
            propagate_volta_number = None

            # ...記号の処理
            if line.startswith('...'):
                # ...の後ろに数字がある場合
                rest = line[3:].strip()
                if rest == '':
                    repeat_bars = 1
                elif rest.isdigit():
                    repeat_bars = int(rest)
                else:
                    # ...の後ろに数字以外があればエラー（音符やコード混在）
                    raise ParseError("リピート記号の行に音符やコードを含めることはできません")
                # リピート記号の前に小節が存在することを確認
                if not bars:
                    raise ParseError("リピート記号の前に小節が必要です")
                # リピートする小節数が実際の小節数と一致することを確認
                if repeat_bars > len(bars):
                    raise ParseError(f"リピートする小節数({repeat_bars})が実際の小節数({len(bars)})を超えています")
                # 無効なリピート回数（1未満）はエラー
                if repeat_bars < 1:
                    raise ParseError("リピート回数は1以上である必要があります")
                # リピート記号の小節を追加
                bar_info = BarInfo(
                    content='',
                    is_repeat_symbol=True,
                    repeat_bars=repeat_bars
                )
                bars.append(bar_info)
                continue

            # 繰り返し開始を検出
            if '{' in line:
                volta_start_match = re.search(r'\{(\d+)', line)
                if volta_start_match:
                    if not in_normal_repeat:
                        raise ParseError(f"n番カッコ {volta_start_match.group(1)} が通常の繰り返しの外にあります")
                    next_volta_number = int(volta_start_match.group(1))
                    next_volta_start = True
                    next_repeat_start = True
                    volta_numbers.add(next_volta_number)
                    repeat_stack.append(next_volta_number)
                    volta_pairs[next_volta_number] = [len(bars), None]
                    current_volta_number = next_volta_number
                    propagate_volta_start = True
                    propagate_volta_number = next_volta_number
                else:
                    next_repeat_start = True
                    in_repeat = True
                    in_normal_repeat = True
                    repeat_stack.append(None)
                bracket_count += line.count('{')

            volta_end_match = re.search(r'}(\d+)', line)
            if volta_end_match:
                next_volta_number = int(volta_end_match.group(1))
                next_volta_end = True
                next_repeat_end = True
                bracket_count -= line.count('}')
                if next_volta_number in volta_pairs:
                    volta_pairs[next_volta_number][1] = len(bars)
                if repeat_stack:
                    repeat_stack.pop()
                if repeat_stack:
                    current_volta_number = repeat_stack[-1] if repeat_stack[-1] is not None else None
                else:
                    current_volta_number = None
            elif '}' in line:
                next_repeat_end = True
                bracket_count -= line.count('}')
                if repeat_stack:
                    if repeat_stack[-1] is None:
                        in_normal_repeat = False
                    repeat_stack.pop()
                if not repeat_stack:
                    in_repeat = False
                    in_normal_repeat = False
                    current_volta_number = None
                else:
                    current_volta_number = repeat_stack[-1] if repeat_stack[-1] is not None else None

            # ...記号の不正な位置や混在のエラー判定
            if '...' in line and not line.startswith('...'):
                raise ParseError("リピート記号は行頭にのみ記述できます")
            if line.startswith('@') and '...' in line:
                raise ParseError("リピート記号とコードを同時に記述することはできません")

            # --- ここから小節内容の処理 ---
            content = line
            if next_volta_start:
                content = re.sub(r'\{(\d+)\s*', '', content)
            if next_volta_end:
                content = re.sub(r'\s*}(\d+)', '', content)
            if next_repeat_start and not next_volta_start:
                content = re.sub(r'{\s*', '', content)
            if next_repeat_end and not next_volta_end:
                content = re.sub(r'\s*}', '', content)
            content = re.sub(r'[{}]', '', content)
            content = content.strip()

            # --- propagateフラグの伝播 ---
            if not content:
                # 記号行自体は小節として追加しない
                continue
            # propagateフラグが立っている場合は、次の小節にフラグを伝播
            repeat_start_flag = next_repeat_start or propagate_repeat_start or (len(bars) == 0 and in_repeat)
            volta_start_flag = next_volta_start or propagate_volta_start
            volta_number_val = None
            if next_volta_start or propagate_volta_start:
                volta_number_val = next_volta_number if next_volta_start else propagate_volta_number
            elif next_volta_end:
                volta_number_val = next_volta_number
            elif current_volta_number is not None and in_normal_repeat:
                volta_number_val = current_volta_number

            bar_info = BarInfo(
                content=content,
                repeat_start=repeat_start_flag,
                repeat_end=next_repeat_end,
                volta_number=volta_number_val,
                volta_start=volta_start_flag,
                volta_end=next_volta_end
            )
            bars.append(bar_info)

            # 状態の更新
            if next_volta_number is not None:
                current_volta_number = next_volta_number
            current_volta_start = next_volta_start
            current_volta_end = next_volta_end
            current_repeat_start = next_repeat_start
            current_repeat_end = next_repeat_end

            # 括弧の更新
            if next_repeat_end:
                if bracket_count == 0:
                    in_normal_repeat = False

        # n番カッコのペアチェック（最後に未完了のペアがないか確認）
        if self.debug_mode:
            print("\n=== Debug Info ===")
            print(f"volta_numbers: {volta_numbers}")
            print(f"volta_pairs: {volta_pairs}")
            print(f"len(volta_numbers): {len(volta_numbers)}")
            print(f"len(volta_pairs): {len(volta_pairs)}")
            print(f"final bracket_count: {bracket_count}")

        # 全てのn番カッコが正しく閉じられているか確認
        for number, positions in volta_pairs.items():
            if positions[1] is None:
                positions[1] = len(bars)  # 終了位置が設定されていない場合は最後の小節を使用

        # 括弧のネストレベルが0でない場合はエラー
        if bracket_count != 0:
            raise ParseError("括弧のネストが正しく閉じられていません")

        if self.debug_mode:
            print("Output bars:")
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

    def _extract_structure(self, text: str) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
        """extract_structureのエイリアス（後方互換性のため）"""
        return self.extract_structure(text) 
        return self.extract_structure(text) 