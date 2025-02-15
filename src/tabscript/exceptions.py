class TabScriptError(Exception):
    """Base exception for all TabScript related errors"""
    pass

class ParseError(TabScriptError):
    """Raised when parsing fails"""
    def __init__(self, message, line_number=None):
        self.line_number = line_number
        if line_number is not None:
            message = f"Line {line_number}: {message}"
        super().__init__(message) 