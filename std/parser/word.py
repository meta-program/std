from .node import AbstractParser, Node, case 

class Word(Node):
    ascii = (*(str(d) for d in range(10)), '_', *(chr(d) for d in range(ord('a'), ord('z') + 1)), *(chr(d) for d in range(ord('A'), ord('Z') + 1)))

    @case(*ascii)
    def case(self, **kwargs):
        self.text += self.key
        return self

    @case
    def case(self, **kwargs):
        return self.parent.parse(**self.kwargs).parse(self.key, **kwargs)
    
    def strFormat(self):
        return self.text

class WordParser(AbstractParser):
    def __init__(self, caret, **kwargs):
        self.caret = Word(parent=caret, **kwargs)
        self.caret.text = ''

