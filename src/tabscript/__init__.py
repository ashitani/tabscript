from .renderer import Renderer
from .exceptions import TabScriptError
from .parser import Parser  # 明示的にParserをインポート

# TextPreprocessorのインポートを削除（まだ公開APIに含めない）
# from .preprocessor import TextPreprocessor

def parser():
    """Create and return a new TabScript parser instance"""
    return Parser()

__all__ = ['parser', 'TabScriptError', 'Parser', 'Renderer'] 