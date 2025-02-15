from .parser import Parser
from .renderer import Renderer
from .exceptions import TabScriptError

def parser():
    """Create and return a new TabScript parser instance"""
    return Parser()

__all__ = ['parser', 'TabScriptError', 'Parser', 'Renderer'] 