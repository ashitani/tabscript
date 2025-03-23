import re
import logging
from tabscript.exceptions import ParseError  # 正しい例外クラスをインポート

class TextPreprocessor:
    """テキスト前処理を担当するクラス"""
    
    def __init__(self, debug_mode=False, debug_level=0):
        """前処理クラスの初期化
        
        Args:
            debug_mode: デバッグモードの有効/無効
            debug_level: デバッグレベル（0-3）
        """
        self.debug_mode = debug_mode
        self.debug_level = debug_level
        self.logger = logging.getLogger(__name__)
    
    def debug_print(self, *args, level: int = 1, **kwargs):
        """デバッグ出力を行う
        
        Args:
            *args: 出力する内容
            level: このメッセージのデバッグレベル（1: 基本情報、2: 詳細情報、3: 全情報）
            **kwargs: print関数に渡す追加の引数
        """
        if self.debug_mode and level <= self.debug_level:
            print(*args, **kwargs)
    
    def preprocess(self, text: str) -> str:
        """テキストの前処理を行う
        
        Args:
            text: 処理対象のテキスト
            
        Returns:
            前処理後のテキスト
        """
        self.debug_print("\n=== preprocess ===", level=1)
        
        # 1. コメント除去
        text = self._clean_text(text)
        self.debug_print(f"After comment removal: {len(text)} bytes", level=2)
        
        # 2. 空行の正規化
        text = self._normalize_empty_lines(text)
        self.debug_print(f"After normalizing empty lines: {len(text)} bytes", level=2)
        
        # ネストされた括弧の処理順序を修正
        # 3. 繰り返し記号と n番カッコを同時に処理
        text = self._normalize_all_brackets(text)
        self.debug_print(f"After normalizing all brackets: {len(text)} bytes", level=2)
        
        return text
    
    def _clean_text(self, text: str) -> str:
        """不要な空行とコメントを除去
        
        Args:
            text: 処理対象のテキスト
            
        Returns:
            コメント除去後のテキスト
        """
        self.debug_print("\n=== _clean_text ===", level=1)
        
        # 行末コメントの削除（直前の空白含む）
        text = re.sub(r'\s*#.*$', '', text, flags=re.MULTILINE)
        
        # 行頭コメントの削除
        text = re.sub(r'^#.*$', '', text, flags=re.MULTILINE)
        
        # 複数行コメントの削除（''' と """ の両方）
        # まず '''で囲まれた部分を削除
        text = re.sub(r"'''[\s\S]*?'''", '', text)
        # 次に """で囲まれた部分を削除
        text = re.sub(r'"""[\s\S]*?"""', '', text)
        
        # 閉じられていない複数行コメントの処理
        open_comment = re.search(r"('''|\"\"\")([\s\S]*)$", text)
        if open_comment:
            # コメント開始位置から末尾までを削除
            text = text[:open_comment.start()]
        
        # 空行を削除（連続する改行を一つに）
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # 先頭と末尾の空白を削除
        text = text.strip()
        
        return text
    
    def _normalize_empty_lines(self, text: str) -> str:
        """空行の正規化"""
        # 連続する空行を1行に
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # セクション区切り（[名前]）の前後に空行を2行ずつ
        text = re.sub(r'\n*(\[\w+\])\n*', r'\n\n\1\n\n', text)
        
        return text
    
    def _normalize_all_brackets(self, text: str) -> str:
        """繰り返し記号とn番カッコを同時に正規化
        
        複数行に分かれた各種括弧を一行に結合する。
        処理順序の問題を解決するため、一括で処理する。
        """
        if self.debug_mode:
            self.debug_print(f"\n=== _normalize_all_brackets ===")
            self.debug_print(f"Input text: {repr(text)}")
        
        # 段階1: 特殊パターンを一時置換（n番カッコの処理を優先）
        # "{n\n...\nn}" パターンを "{n ... }n" に変換
        def normalize_volta(match):
            n = match.group(1)
            content = match.group(2).strip()
            end_n = match.group(3)
            
            if n != end_n:
                # 番号が一致しない場合はエラー
                line_num = text[:match.start()].count('\n') + 3
                raise ValueError(f"Mismatched volta bracket number at line {line_num}")
            
            if not content:
                raise ValueError("Empty volta bracket")
                
            return f"{{{n} {content} }}{n}"
        
        # "{n\n...\nn}" パターンを検出
        text = re.sub(r'\{(\d+)\s*\n(.*?)\n\s*(\d+)\}', normalize_volta, text, flags=re.DOTALL)
        
        # 段階2: "{\n...\n}" パターンを "{ ... }" に変換
        def normalize_repeat(match):
            content = match.group(1).strip()
            if not content:
                raise ValueError("Empty repeat bracket")
            return f"{{ {content} }}"
        
        text = re.sub(r'\{\s*\n(.*?)\n\s*\}', normalize_repeat, text, flags=re.DOTALL)
        
        # 段階3: 特殊ケース - n}\n} パターンを n} } に変換
        text = re.sub(r'(\d+)\}\s*\n\s*\}', r'\1} }', text)
        
        # 段階4: 特殊ケース - }\n} パターンを } } に変換
        text = re.sub(r'\}\s*\n\s*\}', r'} }', text)
        
        # 段階5: 行単位での処理で残りのケースを処理
        lines = text.splitlines()
        result = []
        
        # カッコの処理状態を追跡
        in_repeat = False
        in_volta = False
        repeat_content = []
        volta_content = []
        volta_number = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # n番カッコの開始 {n を検出
            volta_start_match = re.match(r'^\{(\d+)$', line)
            if volta_start_match and not in_repeat and not in_volta:
                in_volta = True
                volta_number = volta_start_match.group(1)
                volta_content = []
                i += 1
                continue
            
            # n番カッコの終了 n} を検出
            volta_end_match = re.match(r'^(\d+)\}$', line)
            if volta_end_match and in_volta:
                end_number = volta_end_match.group(1)
                
                if volta_number != end_number:
                    # 番号が一致しない場合はエラー
                    raise ValueError(f"Mismatched volta bracket number at line {i+1}")
                
                in_volta = False
                if not volta_content:
                    raise ValueError(f"Empty volta bracket at line {i+1}")
                
                # n番カッコ内容を一行に結合
                content = '\n'.join(volta_content)
                result.append(f"{{{volta_number} {content} }}{volta_number}")
                volta_number = None
                i += 1
                continue
            
            # 繰り返し記号の開始 { を検出
            if line == '{' and not in_repeat and not in_volta:
                in_repeat = True
                repeat_content = []
                i += 1
                continue
            
            # 繰り返し記号の終了 } を検出
            if line == '}' and in_repeat:
                in_repeat = False
                if not repeat_content:
                    raise ValueError(f"Empty repeat bracket at line {i+1}")
                
                # 繰り返し内容を一行に結合
                content = '\n'.join(repeat_content)
                result.append(f"{{ {content} }}")
                i += 1
                continue
            
            # n番カッコと繰り返し記号が両方とも閉じられている場合
            if not in_volta and not in_repeat:
                # 既に正規化された括弧パターンをチェック
                if re.match(r'^\{\d+\s+.*\s+\}\d+$', line) or re.match(r'^\{\s+.*\s+\}$', line):
                    # 既に正規化された形式ならそのまま追加
                    result.append(line)
                elif re.match(r'^\d+\}\s+\}$', line):
                    # ネストされた括弧の終了パターンはそのまま保持
                    result.append(line)
                else:
                    # それ以外の通常の行
                    result.append(line)
                i += 1
                continue
            
            # 括弧内の行を蓄積
            if in_volta:
                volta_content.append(line)
            elif in_repeat:
                repeat_content.append(line)
            else:
                result.append(line)
            
            i += 1
        
        # 閉じられていない括弧があればエラー
        if in_volta:
            raise ValueError("Unclosed volta bracket")
        if in_repeat:
            raise ValueError("Unclosed repeat bracket")
        
        result_text = '\n'.join(result)
        
        if self.debug_mode:
            self.debug_print(f"Output text: {repr(result_text)}")
        
        return result_text
    
    # 以下の2つのメソッドは互換性のために残しておく
    def _normalize_repeat_brackets(self, text: str) -> str:
        """互換性のために残す（新メソッドを呼び出す）"""
        return self._normalize_all_brackets(text)
    
    def _normalize_volta_brackets(self, text: str) -> str:
        """互換性のために残す（新メソッドを呼び出す）"""
        return self._normalize_all_brackets(text) 