from .node import AbstractParser, Node, case 

starred_commands = (
    'part', 'chapter', 'section', 'subsection', 'subsubsection', 'paragraph', 'subparagraph',
    'tag', 
    'equation', 'align', 'gather', 'multline', 'flalign', 'alignat', 'displaymath',
    'figure', 'table', 'eqnarray',
    'caption', 'tabular', 'frame', 'sideset',
    'proof', 'theorem', 'lemma', 'corollary',
    'verbatim', 'newcommand',
    'filecontents', 'cite', 'footnote', 'thanks', 'footnotemark', 'linebreak', 'nolinebreak', 'pagebreak', 'nopagebreak',
    'operatorname',
)

starred_command_match = {"\\" + cmd for cmd in starred_commands}

class Command(Node):
    ascii = (*(chr(d) for d in range(ord('a'), ord('z') + 1)), *(chr(d) for d in range(ord('A'), ord('Z') + 1)))

    @case(*ascii)
    def case(self, **kwargs):
        self.text += self.key
        return self

    @case(' ')
    def case(self, **kwargs):
        if self.text == "\\":
            self.text += ' '
        elif self.text[-1] != ' ':
            return self.case_default(' ', **kwargs)
        return self

    @case('*')
    def case(self, **kwargs):
        if self.text in starred_command_match:
            self.text += '*'
            return self
        return self.case_default('*', **kwargs)

    @case(':', '%', '_', '{', '}', "\\", '#', ',', ';', '!')
    def case(self, **kwargs):
        if self.text == "\\":
            self.text += self.key
            return self
        return self.case_default(self.key, **kwargs)

    @case
    def case(self, **kwargs):
        return self.case_default(self.key, **kwargs)

    def case_default(self, token, **kwargs):
        return self.parent.parse(**self.kwargs).parse(token, **kwargs)

    def strFormat(self):
        return self.text

class CommandParser(AbstractParser):
    def __init__(self, caret, **kwargs):
        caret = Command(parent=caret, **kwargs)
        self.caret = caret
        caret.text = "\\"

