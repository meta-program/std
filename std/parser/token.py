from .node import AbstractParser, Node, case 
from .word import Word

class Token(Node):
    ascii = (*Word.ascii, "'", '?', '!')

    @case(*ascii)
    def case(self, **kwargs):
        self.text += self.key
        return self

    @case
    def case(self, **kwargs):
        return self.parent.parse(**self.kwargs).parse(self.key, **kwargs)
    
    def strFormat(self):
        return self.text

class TokenParser(AbstractParser):
    def __init__(self, caret, **kwargs):
        self.caret = Token(parent=caret, **kwargs)
        self.caret.text = ''

