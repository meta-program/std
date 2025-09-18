from .node import AbstractParser, IndentedNode, case 

class NewLine(IndentedNode):
    @case("\n")
    def case(self, **_):
        self.indent = 0
        self.newline_count += 1
        return self

    @case(' ')
    def case(self, **_):
        self.indent += 1
        return self

    @case("\t")
    def case(self, **_):
        self.indent += 4
        return self

    @case
    def case(self, **kwargs):
        caret = self.parent
        self_kwargs = self.kwargs
        if self.next:
            self_kwargs['next'] = self.key
        return caret.parent.insert_newline(caret, self.newline_count, **self_kwargs).parse(self.key, **kwargs)

class NewLineParser(AbstractParser):
    def __init__(self, caret, next=None, **kwargs):
        super().__init__(caret := NewLine(parent=caret, **kwargs))
        caret.newline_count = 1
        caret.next = next
