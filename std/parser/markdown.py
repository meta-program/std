# cd ../keras && bash run.sh std.parser.markdown.test_table &
# python std/parser/markdown.py
import sys, traceback, regex as re
from std.parser.node import AbstractParser, clone, IndentedNode, Closable, case
from std.parser.xml import XMLParser
from std.parser.newline import NewLineParser
from std import computed, binary_search

class Markdown(IndentedNode):
    is_MarkdownText = False
    is_MarkdownSPAN = False
    is_MarkdownLI = False

    is_Paragraph = False
    is_token = False

    @property
    def html(self):
        html = self.htmlFormat()
        if args := self.args:
            return html % tuple(arg.html for arg in args)
        return html

    def htmlFormat(self):
        return self.strFormat()

    def __str__(self):
        s = super().__str__()
        if self.is_indented():
            s = ' ' * self.indent + s
        return s

    @property
    def plainText(self):
        strFormat = self.strFormat()
        text = strFormat % tuple(arg.plainText for arg in self.args) if self.args else strFormat
        if self.is_indented():
            text = ' ' * self.indent + text
        return text

    def has_newline(self):
        return self.is_Paragraph

    def push_token(self, word, **kwargs):
        return self.append(MarkdownText(word, self.indent, **kwargs))
    
    def push_left_bracket(self, **kwargs):
        indent = self.indent
        caret = MarkdownCaret(indent, **kwargs)
        caret.start_idx += 1
        new = MarkdownBracket(caret, indent)
        if isinstance(self.parent, MarkdownSPAN) or isinstance(self.parent, MarkdownDocument) and not isinstance(self, MarkdownText):
            self.parent.push(new)
        else:
            self.parent.replace(self, MarkdownSPAN([self, new], indent))
        return caret

    def push_left_parenthesis(self, **kwargs):
        return self.push_token('(', **kwargs)

    def push_tilde(self, **kwargs):
        return self.push_token('~', **kwargs)
    
    @case(' ')
    def case(self, **kwargs):
        return self.parent.insert_space(self, **kwargs)

    @case("\n")
    def case(self, **kwargs):
        return NewLineParser(self, next=True, **kwargs)

    @case('*')
    def case(self, **kwargs):
        return self.parent.insert_asterisk(self, **kwargs)
    
    @case('_')
    def case(self, **kwargs):
        return self.parent.insert_underscore(self, **kwargs)
    
    @case('[')
    def case(self, **kwargs):
        return self.parent.insert_left_bracket(self, **kwargs)

    @case(']')
    def case(self, **kwargs):
        return self.parent.insert_right_bracket(self, **kwargs)

    @case('(')
    def case(self, **kwargs):
        return self.parent.insert_left_parenthesis(self, **kwargs)

    @case(')')
    def case(self, **kwargs):
        return self.parent.insert_right_parenthesis(self, **kwargs)
    
    @case('<')
    def case(self, **kwargs):
        return self.parent.insert_lt(self, **kwargs)

    @case('&')
    def case(self, **kwargs):
        return self.parent.insert_ampersand(self, **kwargs)
    
    @case('|')
    def case(self, **kwargs):
        return self.parent.insert_bar(self, **kwargs)

    @case('~')
    def case(self, **kwargs):
        return self.parent.insert_tilde(self, **kwargs)

    @case('"')
    def case(self, **kwargs):
        return self.parent.insert_quotation(self, **kwargs)

    @case("'")
    def case(self, **kwargs):
        return self.parent.insert_apostrophe(self, **kwargs)

    @case('`')
    def case(self, **kwargs):
        return self.parent.insert_backtick(self, **kwargs)
    
    @case('$')
    def case(self, **kwargs):
        return self.parent.insert_dollar(self, **kwargs)

    @case("\t")
    def case(self, **kwargs):
        return self.parent.insert_token(self, '    ', **kwargs)

    @case
    def case(self, **kwargs):
        return self.parent.insert_token(self, self.key, **kwargs)

    def isspace(self):
        return False

class MarkdownCaret(Markdown):
    @property
    def text(self):
        return ''
    
    def is_indented(self):
        return False

    def strFormat(self):
        return ''

    def append(self, new):
        self.parent.replace(self, new)
        return new

    def push_token(self, word, **kwargs):
        new = MarkdownText(word, self.indent, **kwargs)
        self.parent.replace(self, new)
        return new

    def push_left_bracket(self, **kwargs):
        indent = self.indent
        caret = self
        caret.start_idx += 1
        self.parent.replace(self, MarkdownBracket(caret, indent))
        return caret

    def isspace(self):
        return True

class MarkdownText(Markdown):
    is_MarkdownText = True
    is_token = True
    def __init__(self, text, indent=0, start_idx=None, parent=None):
        assert isinstance(text, str) and isinstance(indent, int) and isinstance(start_idx, int)
        super().__init__(indent, parent)
        self.text = text
        self.start_idx = start_idx

    def has_newline(self):
        return '\n' in self.text

    def append(self, new):
        if self.parent:
            return self.parent.insert(self, new)
        raise Exception(f'append is not defined {new}: {self.__class__.__name__}')

    def push_token(self, word, **kwargs):
        self.text += word
        return self

    def is_indented(self):
        return False

    def htmlFormat(self):
        return self.text.replace('<', '&lt;').replace('>', '&gt;')

    def strFormat(self):
        return self.text

    def push_patten(self, cls, stop=None):
        # First condition: check for pattern at end of text
        if not re.search(cls.regex_skip, self.text):
            if (m := re.search(cls.regex_text, self.text)) and m[1]:
                self.text = self.text[:-len(m[0])]
                new = MarkdownText(m[1], self.indent, start_idx=self.start_idx + m.start(1))
                new_pattern = cls(new, self.indent)
                if self.text:
                    if isinstance(self.parent, MarkdownSPAN):
                        self.parent.push(new_pattern)
                    else:
                        self.parent.replace(self, MarkdownSPAN([self, new_pattern], self.indent))
                else:
                    self.parent.replace(self, new_pattern)
                return new_pattern

            # Second condition: handle parent spans
            if isinstance(self.parent, (MarkdownSPAN, MarkdownLI)):
                if new := cls.try_pattern(self, stop):
                    return new

        # Default case: add char to text
        self.text += cls.char
        return self

    def push_asterisk(self, **kwargs):
        return self.push_patten(MarkdownI)

    def push_underscore(self, **kwargs):
        return self.push_patten(MarkdownIUnderscore)

    def push_tilde(self, **kwargs):
        return self.push_patten(MarkdownS, -1)

    def push_backtick(self, **kwargs):
        return self.push_patten(MarkdownCODE)

    def push_dollar(self, **kwargs):
        return self.push_patten(MarkdownLatex)

    def try_insert_latex(self, block, **kwargs):
        if re.search(r"(?<!\\)(\\\\)*\\$", self.text):
            return self.parent.insert_latex(self, block, **kwargs)

    def push_left_bracket(self, **kwargs):
        if new := self.try_insert_latex((r'\[', r'\]'), **kwargs):
            return new
        if self.text.endswith('\\'):
            self.text += '['
            return self
        return super().push_left_bracket(**kwargs)

    def push_left_parenthesis(self, **kwargs):
        return self.try_insert_latex((r'\(', r'\)'), **kwargs) or super().push_left_parenthesis(**kwargs)

    @property
    def kwargs_list(self):
        return [self.text, self.start_idx]

    def colgroup_css(self):
        if re.search(': *$', self.text):
            return 'center' if re.match(' *:', self.text) else 'right'
        else:
            return 'left' if re.match(' *:', self.text) else None

    def isspace(self):
        return self.text.isspace()

class MarkdownArgs(Markdown):
    def __init__(self, args, indent, parent=None, **kwargs):
        super().__init__(indent, parent, **kwargs)
        self.args = args
        for arg in args:
            arg.parent = self

    @computed
    def start_idx(self):
        return self.args[0].start_idx

    @computed
    def end_idx(self):
        return self.args[-1].end_idx

    def clone(self):
        return self.__class__(clone(self.args), self.indent, *self.kwargs_list)

    def toJSON(self):
        return {self.func: [arg.toJSON() for arg in self.args]}

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.indent > indent:
            return self.parent.insert_newline(self, newline_count, indent, **kwargs)

        if self.indent < indent:
            raise ValueError(f"{self.__class__.__name__}::insert_newline is unexpected for {self.__class__.__name__}")
        caret = None
        start_idx = kwargs['start_idx']
        for i in range(newline_count):
            caret = MarkdownCaret(indent, start_idx=start_idx + i)
            self.push(caret)
        return caret

    def insert_space(self, caret, **kwargs):
        return self.parent.insert_space(self, **kwargs)
    
    def insert_asterisk(self, caret, **kwargs):
        return caret.push_token('*', **kwargs)

    def insert_underscore(self, caret, **kwargs):
        return caret.push_token('_', **kwargs)

    def insert_token(self, caret, word, **kwargs):
        return caret.push_token(word, **kwargs)

    def insert_right_bracket(self, caret, **kwargs):
        parent = self.parent
        while parent:
            if isinstance(parent, MarkdownBracket):
                parent.is_closed = True
                return parent
            parent = parent.parent
        return self.insert_token(caret, ']', **kwargs)

    def insert_right_parenthesis(self, caret, **kwargs):
        return self.insert_token(caret, ')', **kwargs)

    def insert_bar(self, caret, **kwargs):
        return self.insert_token(caret, '|', **kwargs)

    def insert_latex(self, caret, block, **kwargs):
        new = MarkdownCaret(self.indent, **kwargs)
        latex = MarkdownLatex(new, self.indent, block)
        if isinstance(caret, MarkdownText):
            caret.text = caret.text[:-1]
            if caret.text:
                latex = [caret, latex]
                if not isinstance(self, MarkdownSPAN):
                    latex = MarkdownSPAN(latex, self.indent)
            self.replace(caret, latex)
        else:
            raise Exception(f'insert_latex is not defined {caret}: {self.__class__.__name__}')
        return new

    def insert_h(self, caret, h_level, **kwargs):
        if self.parent:
            return self.parent.insert_h(self, h_level, **kwargs)
        raise Exception(f'insert_h is not defined {caret}: {self.__class__.__name__}')

    def insert_blockquote(self, caret, **kwargs):
        caret = MarkdownCaret(self.indent, **kwargs)
        self.push(MarkdownBLOCKQUOTE([caret], self.indent))
        return caret

    def insert_list(self, cls, caret, m, **kwargs):
        indent = len(m[1])
        warning = None
        if indent == self.indent + 1 and self.indent:
            warning = f'insert_list : indent adjusted from {indent} to {self.indent}'
            indent = self.indent
        caret.text = caret.text[:-len(m[0])]
        new = MarkdownCaret(len(m[0]) + 1, **kwargs)
        new_li = MarkdownLI([new], indent, text=m[2])
        new_list = cls([new_li], indent)
        if caret.text:
            self.push(new_list)
        else:
            self.replace(caret, new_list)
        new.warning = warning
        return new

    def insert_ul(self, caret, m, **kwargs):
        return self.insert_list(MarkdownUL, caret, m, **kwargs)

    def insert_ol(self, caret, m, **kwargs):
        return self.insert_list(MarkdownOL, caret, m, **kwargs)

    def insert_code(self, caret, m, indent, **kwargs):
        caret.text = caret.text[:-len(m[0])]
        lang = m[1]
        new = MarkdownText(' ' * indent, self.indent, **kwargs) if indent else MarkdownCaret(self.indent, **kwargs)
        new_code = MarkdownPreCode(new, self.indent, lang)
        if isinstance(self, MarkdownSPAN) and isinstance(self.parent, (MarkdownLI, MarkdownP, MarkdownDocument)):
            self.parent.push(new_code)
        else:
            self.push(new_code)
        if not caret.text:
            caret.remove()
        return new

    def insert_hr(self, caret, m, **kwargs):
        caret.text = caret.text[:-len(m[0])]
        new = MarkdownHR(self.indent, start_idx=caret.end_idx + 1)
        if caret.text:
            self.push(new)
        else:
            self.replace(caret, new)
        return new

    def insert_left_bracket(self, caret, **kwargs):
        return caret.push_left_bracket(**kwargs)

    def insert_left_parenthesis(self, caret, **kwargs):
        return caret.push_left_parenthesis(**kwargs)

    def insert_lt(self, caret, **kwargs):
        parser = XMLParser(**kwargs)
        if isinstance(caret, MarkdownCaret):
            self.replace(caret, parser)
        elif self.is_MarkdownSPAN:
            self.push(parser)
        else:
            self.replace(caret, MarkdownSPAN([caret, parser], self.indent))
        parser.parse('<')
        return parser

    def insert_ampersand(self, caret, **kwargs):
        parser = XMLParser(**kwargs)
        if isinstance(caret, MarkdownCaret):
            self.replace(caret, parser)
        elif self.is_MarkdownSPAN:
            self.push(parser)
        else:
            self.replace(caret, MarkdownSPAN([caret, parser], self.indent))
        parser.parse('&')
        return parser

    def insert_tilde(self, caret, **kwargs):
        if isinstance(caret, MarkdownText):
            return caret.push_tilde(**kwargs)
        return self.insert_token(caret, '~', **kwargs)

    def insert_apostrophe(self, caret, **kwargs):
        return self.insert_token(caret, "'", **kwargs)

    def insert_quotation(self, caret, **kwargs):
        return self.insert_token(caret, '"', **kwargs)

    def insert_backtick(self, caret, **kwargs):
        return self.insert_token(caret, '`', **kwargs)

    def insert_dollar(self, caret, **kwargs):
        return self.insert_token(caret, '$', **kwargs)

    def span(self, indices):
        index = binary_search(self.args, indices, self.__class__.compareTo)
        if index < len(self.args):
            if isinstance(node := self.args[index], MarkdownArgs) and node.start_idx < indices.end_idx:
                return node.span(indices)
            return node

    def process_inner_loop(self, i, **kwargs):
        args = self.args
        if args[i].has_newline():
            if isinstance(args[i], MarkdownText):
                text = args[i].text
                index = text.rfind("\n")
                former = text[:index]
                latter = text[index + 1:]
                if '`' in latter:
                    return args[-1].push_token('|', **kwargs)
                args[i].text = former
            elif i + 1 < len(args):
                latter = ' ' * args[i + 1].indent
            else:
                latter = ''
            rest = args[i + 1:]
            del args[i + 1:]
            m = re.match('( *)(.*)', latter)
            indent = len(m[1])
            if latter := m[2]:
                rest.insert(0, MarkdownText(latter, indent, **kwargs))
            if rest:
                if len(rest) == 1:
                    rest, = rest
                else:
                    rest = MarkdownSPAN(rest, indent) 
            else:
                rest = MarkdownCaret(indent, **kwargs)
            caret = MarkdownCaret(indent, **kwargs)
            while not isinstance(self, (
                MarkdownP, 
                MarkdownLI, 
                MarkdownListBase,
                MarkdownTABLE, 
                MarkdownDocument, 
                MarkdownH
            )):
                self = self.parent
            self.push(MarkdownArgsBarSeparated([rest, caret], indent))
            return caret

class MarkdownSPAN(MarkdownArgs):
    is_MarkdownSPAN = True

    def is_indented(self):
        return False

    def htmlFormat(self):
        return f'<span>{self.strFormat()}</span>'

    def strFormat(self):
        return '%s' * len(self.args)

    def insert_space(self, caret, **kwargs):
        assert not isinstance(caret, MarkdownCaret)
        assert caret is self.args[-1]
        
        if isinstance(caret, MarkdownText):
            previousElementSibling = caret.previousElementSibling
            if previousElementSibling is None and isinstance(caret.parent, MarkdownP) and len(caret.parent.args) == 1:
                previousElementSibling = caret.parent.previousElementSibling
            newline = '^' if previousElementSibling and previousElementSibling.is_Paragraph else r'(?<=\n)'
            # Handle headings
            if m := re.search(newline + MarkdownH.regex_text, caret.text):
                level = len(m[1])
                caret.text = caret.text[:-len(m[0])]
                if not caret.text:
                    caret.remove()
                return self.parent.insert_h(self, level, **kwargs)
            # Handle unordered lists
            if m := re.search(newline + '( *)([-*])$', caret.text):
                return self.insert_ul(caret, m, **kwargs)
            # Handle ordered lists
            if m := re.search(newline + r'( *)(\d+\.)$', caret.text):
                return self.insert_ol(caret, m, **kwargs)
            caret.text += ' '
        else:
            caret = MarkdownText(' ', self.indent, **kwargs)
            self.push(caret)
        
        return caret

    def insert_asterisk(self, caret, **kwargs):
        if isinstance(caret, MarkdownB):
            if new_i := caret.toMarkdownI():
                return new_i
        elif isinstance(caret, MarkdownText):
            if isinstance(self.parent, MarkdownLI):
                if new := self.parent.try_indent_li(caret, '*', **kwargs):
                    return new
            return caret.push_asterisk(**kwargs)
        elif caret.is_token:
            if isinstance(caret, MarkdownI):
                if new_b := caret.toMarkdownB():
                    return new_b
            if new := MarkdownI.try_pattern(caret):
                return new
        
        return self.insert_token(caret, '*', **kwargs)

    def insert_underscore(self, caret, **kwargs):
        if isinstance(caret, MarkdownB):
            if new_i := caret.toMarkdownI():
                return new_i
        elif isinstance(caret, MarkdownText):
            return caret.push_underscore(**kwargs)
        elif caret.is_token:
            if isinstance(caret, MarkdownI):
                if new_b := caret.toMarkdownB():
                    return new_b
            if new := MarkdownIUnderscore.try_pattern(caret):
                return new

        return self.insert_token(caret, '_', **kwargs)

    def insert_backtick(self, caret, **kwargs):
        if isinstance(caret, MarkdownText):
            if isinstance(new := caret.push_backtick(**kwargs), MarkdownCODE):
                new.arg = MarkdownText(new.arg.plainText, new.indent, start_idx=new.arg.start_idx)
            return new
        if caret.is_token:
            if new := MarkdownCODE.try_pattern(caret):
                new.arg = MarkdownText(new.arg.plainText, new.indent, start_idx=new.arg.start_idx)
                return new
        return self.insert_token(caret, '`', **kwargs)

    def insert_dollar(self, caret, **kwargs):
        if isinstance(caret, MarkdownText):
            if isinstance(new := caret.push_dollar(**kwargs), MarkdownLatex):
                new.arg = MarkdownText(new.arg.plainText, new.indent, start_idx=new.arg.start_idx)
            return new
        if caret.is_token:
            if new := MarkdownLatex.try_pattern(caret):
                new.arg = MarkdownText(new.arg.plainText, new.indent, start_idx=new.arg.start_idx)
                return new
        return self.insert_token(caret, '$', **kwargs)

    def try_pattern(self, cls, stop=None):
        nested_pattern = []
        for i in range(len(self.args) - 2, -1, -1):
            node = self.args[i]
            if isinstance(node, MarkdownText) and (m := re.search(cls.regex_span, node.text)):
                node.text = node.text[:-len(m[0])]
                new_pattern = cls(
                    MarkdownSPAN(
                        [
                            MarkdownText(
                                m[1], 
                                node.indent,
                                start_idx=node.start_idx + m.start(1)
                            ), 
                            *self.args[i + 1:stop]
                        ], 
                        node.indent
                    ), 
                    node.indent, 
                )
                new_pattern.parent = self
                del self.args[i + 1:]
                if node.text:
                    self.args.append(None)
                    i += 1
                self.args[i] = new_pattern
                new_pattern.warning = f'try_pattern : nested tag {cls} detected: {[*map(lambda arg : str(arg), nested_pattern)]}' if nested_pattern else None
                return new_pattern
            elif isinstance(node, cls.base):
                nested_pattern.append(node)

    def try_strike(self):
        if new := self.try_pattern(MarkdownS, -1):
            return new

    def try_backtick(self):
        if new := self.try_pattern(MarkdownCODE):
            return new

    def insert_newline(self, caret, newline_count, indent, next, **kwargs):
        if isinstance(self.parent, (MarkdownArgsBarSeparated, MarkdownH)):
            return self.parent.insert_newline(self, newline_count, indent, next=next, **kwargs)
        if isinstance(caret, MarkdownText):
            if m := re.search(MarkdownPreCode.code_start_regex, caret.text):
                return self.insert_code(caret, m, indent, **kwargs)
            if m := re.search(MarkdownHR.regex, caret.text):
                return self.insert_hr(caret, m, **kwargs)
        if newline_count == 1:
            return self.insert_token(caret, "\n" * newline_count + ' ' * indent, **kwargs)
        if isinstance(li := self.parent, MarkdownLI):
            if next in "-*" :
                return self.insert_token(caret, "\n" * newline_count + ' ' * indent, **kwargs)
            else:
                new = MarkdownText(' ' * indent, 0, **kwargs) if indent else MarkdownCaret(indent, **kwargs)
                new.start_idx += newline_count
                li.parent.parent.push(new)
                return new
        if isinstance(bracket := self.parent, MarkdownBracket):
            container = self.parent.parent
            self.unshift(MarkdownText('[', bracket.indent, start_idx=bracket.start_idx))
            if self.__class__ == container.__class__:
                self = self.args
            container.replace(bracket, self)
            if parent := container.parent:
                return parent.insert_newline(container, newline_count, indent, next=next, **kwargs)
            return container.insert_newline(container.args[-1], newline_count, indent, next=next, **kwargs)
        if newline_count > 1 and indent >= 4 and isinstance(self.parent, MarkdownDocument) and caret.is_token:
            new = MarkdownText(' ' * indent, self.indent, **kwargs)
            new.start_idx += newline_count
            self.parent.push(MarkdownPreCode(new, self.indent, None))
        else:
            new = MarkdownP(self.args, self.indent)
            parent = self.parent
            parent.replace(self, new)
            indent -= self.indent
            if indent > 0:
                new = MarkdownText(' ' * indent, self.indent, **kwargs)
                new.start_idx += newline_count
                parent.push(new)
        return new
    
    def insert(self, caret, new):
        assert caret == self.args[-1]
        assert isinstance(new, MarkdownText)
        assert not isinstance(caret, MarkdownText)
        self.push(new)
        return new
    
    def append(self, new):
        if isinstance(new, MarkdownText):
            self.push(new)
            return new
        return self.parent.append(new)

    def insert_list(self, cls, caret, m, **kwargs):
        indent = len(m[1])
        warning = None
        if indent == self.indent + 1 and self.indent:
            warning = f'insert_list : indent adjusted from {indent} to {self.indent}'
            indent = self.indent

        caret.text = caret.text[:-len(m[0])]
        node = self.parent
        if isinstance(node, MarkdownLI):
            new = node.insert_li(indent, m[2], len(m[0]) + 1, **kwargs)
        else:
            new = MarkdownCaret(indent, **kwargs)
            new_li = MarkdownLI([new], indent, text=m[2])
            new_list = cls([new_li], indent)

            if caret.text:
                self.push(new_list)
            elif caret.parent is self:
                self.replace(caret, new_list)
            else:
                caret.remove()
                self.push(new_list)
        new.warning = warning
        return new

    def insert_token(self, caret, word, **kwargs):
        if isinstance(caret, MarkdownText) and isinstance(self.parent, MarkdownLI):
            if new := self.parent.try_indent_li(caret, word, **kwargs):
                return new
        elif isinstance(caret, XMLParser):
            return MarkdownI.push_token(caret, word, **kwargs)
        return super().insert_token(caret, word, **kwargs)

    def insert_bar(self, caret, **kwargs):
        args = self.args
        for i in reversed(range(len(args))):
            if new := self.process_inner_loop(i, **kwargs):
                return new
        else:
            if isinstance(self.parent, MarkdownArgsBarSeparated):
                return self.parent.insert_bar(self, **kwargs)
            else:
                return caret.push_token('|', **kwargs)

    def removeChild(self, child):
        super(IndentedNode, self).removeChild(child)
        if not self.args:
            self.remove()

class MarkdownUnary(MarkdownArgs):
    def __init__(self, arg, indent, parent=None):
        super().__init__([], indent, parent)
        self.arg = arg  # Uses the arg setter

    def clone(self):
        return self.__class__(self.arg.clone(), self.indent, *self.kwargs_list)

    @property
    def arg(self):
        return self.args[0]

    @arg.setter
    def arg(self, arg):
        if not self.args:
            self.args.append(None)
        self.args[0] = arg
        arg.parent = self

    def toJSON(self):
        return self.arg.toJSON()

    def push(self, arg):
        raise Exception(f"push operation not allowed for {self.__class__.__name__}")

    def unshift(self, arg):
        raise Exception(f"unshift operation not allowed for {self.__class__.__name__}")

    def replace(self, old, new):
        if isinstance(new, list):
            new = MarkdownSPAN(new, self.indent)
        super().replace(old, new)

class MarkdownI(MarkdownUnary):
    char = '*'
    regex_skip = r'[ \n\t~\\]$|`'
    regex_text = regex_span = r'\*(?![ \n\t])([^*]*)$'
    is_token = True

    def __init__(self, arg, indent, char='*', parent=None):
        super().__init__(arg, indent, parent)
        self.kwargs['char'] = char

    def is_indented(self):
        return False

    def htmlFormat(self):
        return '<i>%s</i>'

    def strFormat(self):
        char = self.kwargs['char']
        return f'{char}%s{char}'

    def append(self, caret):
        if self.parent:
            return self.parent.insert(self, caret)
        raise Exception(f'append is not defined {caret}: {self.__class__.__name__}')

    def push_token(self, word, **kwargs):
        new = MarkdownText(word, self.indent, **kwargs)
        if isinstance(self.parent, (MarkdownSPAN, MarkdownLI)):
            self.parent.push(new)
        else:
            self.parent.replace(self, MarkdownSPAN([self, new], self.indent))
        return new

    def toMarkdownB(self):
        caret = self
        parent = self.parent
        previousElementSibling = caret.previousElementSibling
        if (isinstance(previousElementSibling, MarkdownText) and previousElementSibling.text.endswith('*')):
            previousElementSibling.text = previousElementSibling.text[:-1]
            arg = caret.arg.arg if isinstance(caret.arg, MarkdownB) else caret.arg
            new_b = MarkdownB(arg, caret.indent)
            
            parent.replace(caret, new_b)
            
            if not previousElementSibling.text:
                previousElementSibling.remove()
            
            return new_b

    def insert_asterisk(self, caret, **kwargs):
        if isinstance(caret, MarkdownText):
            return caret.push_asterisk(**kwargs)
        return self.insert_token(caret, '*', **kwargs)

    def insert_underscore(self, caret, **kwargs):
        if isinstance(caret, MarkdownText):
            return caret.push_underscore(**kwargs)
        return self.insert_token(caret, '_', **kwargs)

    @classmethod
    def try_pattern(cls, self, stop=None):
        self = self.parent
        if new := self.try_pattern(cls, stop):
            return new
        # Handle span parent being inside italic
        if isinstance(self.parent, MarkdownI):
            if new := self.parent.toMarkdownB():
                return new

class MarkdownIUnderscore(MarkdownI):
    base = MarkdownI
    char = '_'
    regex_text = regex_span = r'_(?![ \n\t])([^_]*)$'
    def __new__(cls, *args, **kwargs):
        return MarkdownI(*args, **kwargs, char='_')

class MarkdownB(MarkdownUnary):
    is_token = True

    def is_indented(self):
        return False

    def htmlFormat(self):
        return '<b>%s</b>'

    def strFormat(self):
        return '**%s**'

    def append(self, new):
        if self.parent:
            return self.parent.insert(self, new)
        raise Exception(f'append is not defined {new}: {self.__class__.__name__}')

    def toMarkdownI(self):
        caret = self
        parent = self.parent
        previousElementSibling = caret.previousElementSibling
        if (isinstance(previousElementSibling, MarkdownText) and previousElementSibling.text.endswith('*')):
            previousElementSibling.text = previousElementSibling.text[:-1]
            # Handle text that's both italic and bold
            new_i = MarkdownI(caret, indent=caret.indent)
            parent.replace(caret, new_i)
            
            if not previousElementSibling.text:
                previousElementSibling.remove()
            return new_i

    push_token = MarkdownI.push_token
    insert_asterisk = MarkdownI.insert_asterisk
    insert_underscore = MarkdownI.insert_underscore

class MarkdownS(MarkdownUnary):
    char = '~'
    regex_skip = r'[^~]$|[ \n\t\\]~$'
    regex_text = r'~~(?![ \n\t~])([^~]*)~$'
    regex_span = r'~~(?![ \n\t~])([^~]*)$'
    is_token = True

    def is_indented(self):
        return False

    def htmlFormat(self):
        return '<s>%s</s>'

    def strFormat(self):
        return '~~%s~~'

    def append(self, caret):
        if self.parent:
            return self.parent.insert(self, caret)
        raise Exception(f'append is not defined {caret}: {self.__class__.__name__}')

    @classmethod
    def try_pattern(cls, self, stop):
        if self.text == '~':
            return self.parent.try_pattern(cls, stop)

    push_token = MarkdownI.push_token
    insert_asterisk = MarkdownI.insert_asterisk
    insert_underscore = MarkdownI.insert_underscore

class MarkdownLink(MarkdownArgs, Closable):
    is_token = True
    @property
    def href(self):
        return self.args[1]

    @property
    def title(self):
        try:
            return self.args[2]
        except IndexError:
            ...

    @property
    def title_quote(self):
        return self.kwargs.get('title_quote')

    @title_quote.setter
    def title_quote(self, title_quote):
        self.kwargs['title_quote'] = title_quote

    def is_indented(self):
        return False

    @property
    def html(self):
        text, href, *title = self.args
        args = href, *title, text
        return self.htmlFormat() % tuple(arg.html for arg in args)

    def strFormat(self):
        if len(self.args) == 2:
            return '[%s](%s)'
        title_quote = self.title_quote[0]
        return f'[%s](%s {title_quote}%s{title_quote})'

    def insert_right_parenthesis(self, caret, **kwargs):
        paren_count = 0
        if isinstance(href := self.href, MarkdownText) and caret is href:
            for ch in href.text:
                if ch == '(':
                    paren_count += 1
                elif ch == ')':
                    paren_count -= 1
        if paren_count > 0:
            caret.text += ')'
            return caret
        self.is_closed = True
        return self

    def insert_space(self, caret, **kwargs):
        if caret is self.href:
            return caret.push_token(' ', **kwargs)
        return super().insert_space(caret, **kwargs)

    def insert_apostrophe(self, caret, **kwargs):
        if caret is self.href:
            caret = MarkdownCaret(self.indent, **kwargs)
            caret.start_idx += 1
            self.title_quote = "'"
            self.push(caret)
            return caret
        if caret is self.title:
            if self.title_quote == "'":
                self.title_quote += "'"
                return caret
        return super().insert_apostrophe(caret, **kwargs)

    def insert_quotation(self, caret, **kwargs):
        if caret is self.href:
            caret = MarkdownCaret(self.indent, **kwargs)
            caret.start_idx += 1
            self.title_quote = '"'
            self.push(caret)
            return caret
        if caret is self.title:
            if self.title_quote == '"':
                self.title_quote += '"'
                return caret
        return super().insert_quotation(caret, **kwargs)

    def insert_ampersand(self, caret, **kwargs):
        return self.insert_token(caret, '&', **kwargs)

    def insert_newline(self, caret, newline_count, indent, next, **kwargs):
        href = self.href
        args = [
            self.args[0], 
            MarkdownText("(", start_idx=href.start_idx - 1), 
            href
        ]
        if caret is self.title:
            args += [
                MarkdownText(")", start_idx=href.end_idx), 
                caret
            ]
        new = MarkdownText("\n" * newline_count + ' ' * indent, **kwargs)
        args.append(new)
        self.parent.replace(self, args)
        return new

    push_token = MarkdownI.push_token

class MarkdownA(MarkdownLink):
    @computed
    def start_idx(self):
        return self.args[0].start_idx - 1
    def htmlFormat(self):
        if len(self.args) == 2:
            return '<a href="%s">%s</a>'
        title_quote = self.title_quote[0]
        return f'<a href="%s" title={title_quote}%s{title_quote}>%s</a>'


class MarkdownIMG(MarkdownLink):
    @computed
    def start_idx(self):
        return self.args[0].start_idx - 2

    def htmlFormat(self):
        if len(self.args) == 2:
            return '<img src="%s" alt="%s" />'
        title_quote = self.title_quote[0]
        return f'<img src="%s" alt="%s"title={title_quote}%s{title_quote} />'

    def strFormat(self):
        return '!' + super().strFormat()

    def insert_left_bracket(self, caret, **kwargs):
        if caret is self.href:
            return self.insert_token(caret, '[', **kwargs)
        return super().insert_left_bracket(caret, **kwargs)

class MarkdownArgsBarSeparated(MarkdownArgs):
    is_Paragraph = True
    def strip_head_tail(self):
        args = self.args
        if not args:
            return
        if args[0].isspace():
            args = args[1:]
            if not args:
                return
        if args[-1].isspace():
            args = args[:-1]
            if not args:
                return
        return args

    def is_colgroup_setting(self):
        if (args := self.strip_head_tail()) and all(isinstance(cell, MarkdownText) and re.fullmatch(r' *:?-+:? *', cell.text) for cell in args):
            return args

    def has_newline(self):
        return True

    def strFormat(self):
        args_placeholders = '|'.join(['%s'] * len(self.args))
        return f"\n{args_placeholders}"

    def insert_space(self, caret, **kwargs):
        if isinstance(caret, (MarkdownCaret, MarkdownText)):
            return caret.push_token(' ', **kwargs)
        return self.parent.insert_space(self, **kwargs)

    def insert_bar(self, caret, **kwargs):
        caret = MarkdownCaret(self.indent, **kwargs)
        self.push(caret)
        return caret

    def insert_newline(self, caret, newline_count, indent, next, **kwargs):
        table_continued = newline_count == 1 and indent >= self.indent and indent < self.indent + 4
        caret = MarkdownText(' ' * indent, indent, **kwargs) if indent else MarkdownCaret(indent, **kwargs)
        caret.start_idx += newline_count
        indent = self.indent
        if isinstance(table := self.parent, MarkdownTABLE):
            if args := self.strip_head_tail():
                new_td = [MarkdownTD(arg, indent) for arg in args]
                for td, th in zip(new_td, table.args[0].args):
                    td.textAlign = th.textAlign
                table.replace(self, MarkdownTR(new_td, indent))
            parent = table
            if not table_continued:
                while parent := parent.parent:
                    if parent.is_Paragraph or isinstance(parent, MarkdownLI):
                        break
            parent.push(caret)
        elif isinstance(P := self.parent, MarkdownP) and isinstance(previousElementSibling := self.previousElementSibling, MarkdownArgsBarSeparated) and (colgroup := self.is_colgroup_setting()) and (args := previousElementSibling.strip_head_tail()):
            escape_li = False
            if isinstance(li := P.parent, MarkdownLI) and isinstance(li.parent, MarkdownListBase):
                indent_pivot = li.args[0].indent
                if indent < indent_pivot:
                    if indent > li.indent:
                        indent = li.indent
                    P.remove()
                    parent = li.parent.parent
                    escape_li = True
            new_th = [MarkdownTH(arg, indent) for arg in args]
            new_table = MarkdownTABLE(
                [
                    MarkdownTR(new_th, indent),
                    caret
                ],
                indent
            )
            if escape_li:
                parent.push(new_table)
            else:
                P.parent.replace(P, new_table)
            for align, th in zip(colgroup, new_th):
                th.textAlign = align.colgroup_css()
        elif isinstance(self.parent, MarkdownP):
            self.parent.push(caret)
        else:
            self.parent.replace(self, MarkdownP([self, caret], indent))
        return caret

    insert_asterisk = MarkdownI.insert_asterisk
    insert_underscore = MarkdownI.insert_underscore
    insert_backtick = MarkdownSPAN.insert_backtick

class MarkdownPreCode(MarkdownUnary, Closable):
    code_start_regex = r'(?<=(?:^|\n) *)```([a-zA-Z:]*\+*\d*)( *)$'
    is_Paragraph = True
    def __init__(self, caret, indent, lang, parent=None):
        super().__init__(caret, indent, parent)
        self.lang = lang
    
    @property
    def kwargs_list(self):
        return [self.lang]

    @property
    def lang(self):
        return self.kwargs['lang']
    
    @lang.setter
    def lang(self, lang):
        self.kwargs['lang'] = lang

    def is_indented(self):
        return False
    
    @property
    def html(self):
        args = tuple(arg.html.replace('<', '&lt;').replace('>', '&gt;') for arg in self.args)
        return self.htmlFormat() % args

    def htmlFormat(self):
        if (lang := self.lang) is None:
            return f'<pre><code>%s</code></pre>'
        else:
            return f'<pre class="language-{lang}"><code class="language-{lang}">%s</code></pre>'

    def strFormat(self):
        if (lang := self.lang) is None:
            return '\n%s\n'
        else:
            return f'```{lang}\n%s\n```'

    def insert_space(self, caret, **kwargs):
        return caret.push_token(' ', **kwargs)

    def insert_asterisk(self, caret, **kwargs):
        return caret.push_token('*', **kwargs)

    def insert_underscore(self, caret, **kwargs):
        return caret.push_token('_', **kwargs)

    def insert_left_bracket(self, caret, **kwargs):
        return caret.push_token('[', **kwargs)

    def insert_left_parenthesis(self, caret, **kwargs):
        return caret.push_token('(', **kwargs)
    
    def insert_right_bracket(self, caret, **kwargs):
        return caret.push_token(']', **kwargs)
    
    def insert_right_parenthesis(self, caret, **kwargs):
        return caret.push_token(')', **kwargs)

    def insert_newline(self, caret, newline_count, indent, next, **kwargs):
        if isinstance(caret, MarkdownText):
            if self.lang is None:
                if indent < 4:
                    self.is_closed = True
            elif m := re.search(r'\n* *``` *$', caret.text):
                caret.text = caret.text[:-len(m[0])]
                self.is_closed = True
        if self.is_closed:
            kwargs['start_idx'] += newline_count
            if not indent:
                if isinstance(li := self.parent, MarkdownLI):
                    li.replace(self, MarkdownP([self], self.indent))
                    caret = MarkdownCaret(indent, **kwargs)
                    hit = False
                    if newline_count > 1:
                        while isinstance(li, MarkdownLI) and indent <= li.indent:
                            li = li.parent.parent
                            hit = True
                    if hit:
                        li.push(caret)
                    else:
                        li.push(MarkdownP([caret], indent))
                    return caret
                return self
            newline_count = 0
            caret = self
            self = caret.parent
        return self.insert_token(caret, "\n" * newline_count + ' ' * indent, **kwargs)

    def insert_lt(self, caret, **kwargs):
        return caret.push_token('<', **kwargs)

    def insert_ampersand(self, caret, **kwargs):
        return caret.push_token('&', **kwargs)

    def insert_bar(self, caret, **kwargs):
        return caret.push_token('|', **kwargs)

    def insert_tilde(self, caret, **kwargs):
        return caret.push_token('~', **kwargs)

    def insert_apostrophe(self, caret, **kwargs):
        return self.insert_token(caret, "'", **kwargs)

    def insert_quotation(self, caret, **kwargs):
        return self.insert_token(caret, '"', **kwargs)

    def insert_backtick(self, caret, **kwargs):
        return self.insert_token(caret, '`', **kwargs)

    def insert_dollar(self, caret, **kwargs):
        return self.insert_token(caret, '$', **kwargs)

    def push_token(self, word, **kwargs):
        new = MarkdownText(word, self.indent, **kwargs)
        if isinstance(self.parent, (MarkdownP, MarkdownLI, MarkdownH, MarkdownDocument)):
            self.parent.push(new)
        else:
            self.parent.replace(self, MarkdownP([self, new], self.indent))
        return new


class MarkdownCODE(MarkdownUnary):
    char = '`'
    regex_skip = r'(?<![`\\])`[^`]*\n\n'
    regex_text = regex_span = r'(?<![`\\])`([^`]*)$'
    is_token = True
    def is_indented(self):
        return False
    
    def htmlFormat(self):
        return '<code>%s</code>'

    def strFormat(self):
        return '`%s`'

    def insert_space(self, caret, **kwargs):
        return caret.push_token(' ', **kwargs)

    def insert_asterisk(self, caret, **kwargs):
        return caret.push_token('*', **kwargs)

    def insert_underscore(self, caret, **kwargs):
        return caret.push_token('_', **kwargs)

    def insert_left_bracket(self, caret, **kwargs):
        return caret.push_token('[', **kwargs)

    def insert_left_parenthesis(self, caret, **kwargs):
        return caret.push_token('(', **kwargs)

    def insert_right_bracket(self, caret, **kwargs):
        return caret.push_token(']', **kwargs)

    def insert_right_parenthesis(self, caret, **kwargs):
        return caret.push_token(')', **kwargs)

    def insert_newline(self, caret, newline_count, indent, next, **kwargs):
        return self.insert_token(caret, "\n" * newline_count + ' ' * indent, **kwargs)

    def insert_lt(self, caret, **kwargs):
        return caret.push_token('<', **kwargs)

    def insert_ampersand(self, caret, **kwargs):
        return caret.push_token('&', **kwargs)

    def insert_bar(self, caret, **kwargs):
        return caret.push_token('|', **kwargs)

    def insert_tilde(self, caret, **kwargs):
        return caret.push_token('~', **kwargs)

    def insert_apostrophe(self, caret, **kwargs):
        return self.insert_token(caret, "'", **kwargs)

    def insert_quotation(self, caret, **kwargs):
        return self.insert_token(caret, '"', **kwargs)

    def insert_backtick(self, caret, **kwargs):
        return self

    @classmethod
    def try_pattern(cls, self, stop=None):
        return self.parent.try_pattern(cls, stop)

    push_token = MarkdownI.push_token
    html = MarkdownPreCode.html

class MarkdownH(MarkdownArgs):
    regex_text = ' {0,3}(#+)$'
    def __init__(self, caret, indent, level, parent=None):
        super().__init__([caret], indent, parent)
        self.kwargs['level'] = level

    @property
    def kwargs_list(self):
        return [self.level]

    @property
    def level(self):
        return self.kwargs['level']

    def is_indented(self):
        return False

    def htmlFormat(self):
        level = self.level
        hanging = "\n".join(["%s"] * (len(self.args) - 1))
        return f"<h{level}>%s</h{level}>\n" + hanging

    def strFormat(self):
        level = self.level
        hanging = "\n".join(["%s"] * (len(self.args) - 1))
        hash = '#' * level
        return f"{hash} %s\n" + hanging

    @property
    def header(self):
        return self.args[0]

    @property
    def hanging(self):
        return self.args[1:]

    def insert_right(self, caret, **kwargs):
        if isinstance(caret, MarkdownText):
            if m := re.search(r'\(([^)]+)', caret.text):
                caret.text = caret.text[:-len(m[0])]
        if self.parent:
            return self.parent.insert_right(self, caret, **kwargs)
        raise Exception(f'insert_right is not defined {caret}: {self.__class__.__name__}')

    def insert_space(self, caret, **kwargs):
        if isinstance(caret, MarkdownText):
            if caret is not self.header:
                if m := re.search(r'(?<=^|\n)' + MarkdownH.regex_text, caret.text):
                    level = len(m[1])
                    caret.text = caret.text[:-len(m[0])]
                    new = self.insert_h(caret, level, **kwargs)
                    if not caret.text:
                        caret.remove()
                    return new
                if m := re.search(r'(?<=^|\n)( *)([-*])$', caret.text):
                    return self.insert_ul(caret, m, **kwargs)
                if m := re.search(r'(?<=^|\n)( *)(\d+\.)$', caret.text):
                    return self.insert_ol(caret, m, **kwargs)
            caret.text += ' '
        return caret

    def insert_backtick(self, caret, **kwargs):
        if isinstance(caret, MarkdownText):
            return caret.push_backtick(**kwargs)
        return self.insert_token(caret, '`', **kwargs)

    def insert_dollar(self, caret, **kwargs):
        if isinstance(caret, MarkdownText):
            return caret.push_dollar(**kwargs)
        return self.insert_token(caret, '$', **kwargs)

    def insert_newline(self, caret, newline_count, indent, next, **kwargs):
        if self.indent > indent:
            return super().insert_newline(caret, newline_count, indent, next=next, **kwargs)
        # now that indent ≥ this.indent
        if caret is self.header:
            caret = MarkdownText(' ' * indent, self.indent, **kwargs) if indent else MarkdownCaret(indent, **kwargs)
            caret.start_idx += newline_count
            self.push(caret)
            return caret

        if isinstance(caret, MarkdownText):
            if m := re.search(MarkdownPreCode.code_start_regex, caret.text):
                return self.insert_code(caret, m, indent, **kwargs)
            if m := re.search(MarkdownHR.regex, caret.text):
                return self.insert_hr(caret, m, **kwargs)
            if newline_count == 1:
                return self.insert_token(caret, "\n" * newline_count + ' ' * indent, **kwargs)

        if caret.is_Paragraph:
            return caret
        new = MarkdownP(caret.args if isinstance(caret, MarkdownSPAN) else [caret], self.indent)
        self.replace(caret, new)
        indent -= self.indent
        if indent:
            new = MarkdownText(' ' * indent, self.indent, **kwargs)
            new.start_idx += newline_count
            self.push(new)
        return new

    def insert_token(self, caret, char, **kwargs):
        if isinstance(caret, (MarkdownText, MarkdownCaret)):
            return caret.push_token(char, **kwargs)
        text = MarkdownText(char, self.indent, **kwargs)
        if caret.is_Paragraph:
            self.push(text)
        elif isinstance(caret, MarkdownSPAN):
            caret.push(text)
        else:
            self.replace(caret, MarkdownSPAN([caret, text], self.indent))
        return text

    def toJSON(self):
        data = super().toJSON()
        data['level'] = self.level
        return data

    def insert(self, caret, new):
        assert caret == self.args[-1], "Caret must be last argument"
        if isinstance(new, MarkdownText):
            if isinstance(caret, MarkdownSPAN):
                caret.push(new)
            else:
                texts = MarkdownSPAN([caret, new], self.indent)
                self.replace(caret, texts)
            return new
        else:
            raise ValueError(f"Invalid element type for insert: {type(new)}")

    def insert_h(self, caret, level, **kwargs):
        caret = MarkdownCaret(self.indent, **kwargs)
        new_h = MarkdownH(caret, self.indent, level)
        if level > self.level:
            self.push(new_h)
        else:
            node = self
            while isinstance(node.parent, MarkdownH) and level <= node.parent.level:
                node = node.parent
            node.parent.push(new_h)
        return caret

    def process_inner_loop(self, i, **kwargs):
        if not i:
            args = self.args
            rest = args[i + 1:]
            del args[i + 1:]
            indent = self.indent
            if rest:
                if len(rest) == 1:
                    rest, = rest
                else:
                    rest = MarkdownSPAN(rest, indent) 
            else:
                rest = MarkdownCaret(indent, **kwargs)
            caret = MarkdownCaret(indent, **kwargs)
            self.push(MarkdownArgsBarSeparated([rest, caret], indent))
            return caret
        else:
            return super().process_inner_loop(i, **kwargs)

    def insert_bar(self, caret, **kwargs):
        if caret is self.header:
            return self.insert_token(caret, '|', **kwargs)
        return MarkdownSPAN.insert_bar(self, caret, **kwargs)

    insert_asterisk = MarkdownI.insert_asterisk
    insert_underscore = MarkdownI.insert_underscore

class MarkdownPairedGroup(MarkdownUnary, Closable):
    def is_indented(self):
        return False

    def insert(self, caret, func):
        if self.arg is caret:
            if isinstance(caret, MarkdownCaret):
                self.arg = func(caret, self.indent)
                return caret
        raise ValueError(f"insert is unexpected for {self.__class__.__name__}")

class MarkdownLatex(MarkdownPairedGroup):
    char = '$'
    regex_skip = r'(?<![$\\])\$[^$]*\n'
    regex_text = regex_span = r'(?<![$\\])\$([^$]*)$'
    is_token = True
    def __init__(self, caret, indent, block='$$', parent=None):
        super().__init__(caret, indent, parent)
        self.block = block

    @property
    def kwargs_list(self):
        return [self.block]

    @property
    def block(self):
        return self.kwargs['block']

    @block.setter
    def block(self, block):
        self.kwargs['block'] = block

    @property
    def is_Paragraph(self):
        return self.block[0] in ('\\[', '$$')

    def is_indented(self):
        return False

    def strFormat(self):
        block = self.block
        s = f"{block[0]}%s"
        if self.is_closed:
            s += block[1]
        return s

    def insert_space(self, caret, **kwargs):
        return caret.push_token(' ', **kwargs)

    def insert_asterisk(self, caret, **kwargs):
        return caret.push_token('*', **kwargs)

    def insert_underscore(self, caret, **kwargs):
        return caret.push_token('_', **kwargs)

    def insert_left_bracket(self, caret, **kwargs):
        return caret.push_token('[', **kwargs)

    def insert_left_parenthesis(self, caret, **kwargs):
        return caret.push_token('(', **kwargs)

    def insert_right_bracket(self, caret, **kwargs):
        if self.block[1] == r'\]' and isinstance(caret, MarkdownText) and re.search(r'(?<!\\)(\\\\)*\\$', caret.text):
            caret.text = caret.text[:-1]
            self.is_closed = True
            return self
        return caret.push_token(']', **kwargs)

    def insert_right_parenthesis(self, caret, **kwargs):
        if self.block[1] == r'\)' and isinstance(caret, MarkdownText) and re.search(r'(?<!\\)(\\\\)*\\$', caret.text):
            caret.text = caret.text[:-1]
            self.is_closed = True
            return self
        return caret.push_token(')', **kwargs)

    def insert_newline(self, caret, newline_count, indent, next, **kwargs):
        return self.insert_token(caret, "\n" * newline_count + ' ' * indent, **kwargs)

    def insert_lt(self, caret, **kwargs):
        return caret.push_token('<', **kwargs)

    def insert_ampersand(self, caret, **kwargs):
        return caret.push_token('&', **kwargs)
    
    def insert_bar(self, caret, **kwargs):
        return caret.push_token('|', **kwargs)

    def insert_tilde(self, caret, **kwargs):
        return caret.push_token('~', **kwargs)

    def insert_quote(self, caret, quote, **kwargs):
        if isinstance(caret, MarkdownCaret) and \
            isinstance(self.parent, MarkdownSPAN) and \
            isinstance(previousElementSibling := self.previousElementSibling, MarkdownText) and \
            re.search(fr"(?<!\\){quote}[^{quote}]*$", previousElementSibling.text):
            previousElementSibling.text += str(self) + quote
            self.remove()
            return previousElementSibling
        return self.insert_token(caret, quote, **kwargs)

    def insert_apostrophe(self, caret, **kwargs):
        return self.insert_quote(caret, "'", **kwargs)

    def insert_quotation(self, caret, **kwargs):
        return self.insert_quote(caret, '"', **kwargs)

    def insert_backtick(self, caret, **kwargs):
        return self.insert_token(caret, '`', **kwargs)

    def insert_dollar(self, caret, **kwargs):
        if self.block[1] == '$':
            return self
        return caret.push_token('$', **kwargs)
    
    try_pattern = MarkdownCODE.try_pattern

class MarkdownLI(MarkdownArgs):
    is_MarkdownLI = True
    def is_indented(self):
        return True

    @computed
    def start_idx(self):
        return self.args[0].start_idx - len(self.text) - 1

    def htmlFormat(self):
        return f"<li>{'%s' * len(self.args)}</li>"

    def strFormat(self):
        return self.text + ' ' + '%s' * len(self.args)

    def insert_newline(self, caret, newline_count, indent, next, **kwargs):
        if isinstance(caret, MarkdownText):
            if m := re.search(MarkdownPreCode.code_start_regex, caret.text):
                return self.insert_code(caret, m, indent, **kwargs)
            if isinstance(self.parent, MarkdownUL) and (m := re.match(fr'(?: *[{self.text}]){{2,}} *$', caret.text)):
                new = MarkdownHR(self.indent, start_idx=self.start_idx)
                if len(self.args) == 1:
                    self.parent.parent.push(new)
                    self.remove()
                else:
                    self.replace(caret, new)
                return new
            if m := re.search(MarkdownHR.regex, caret.text):
                return self.insert_hr(caret, m, **kwargs)
            if newline_count > 1 and not re.search('[-*0-9]', next):
                caret = MarkdownText(' ' * indent, 0, **kwargs) if indent else MarkdownCaret(indent, **kwargs)
                caret.start_idx += newline_count
                hit = False
                while isinstance(self, MarkdownLI) and indent <= self.indent:
                    self = self.parent.parent
                    hit = True
                if hit:
                    self.push(caret)
                else:
                    self.push(MarkdownP([caret], indent))
            else:
                caret.text += "\n" * newline_count + ' ' * indent
        else:
            caret = MarkdownText("\n" * newline_count + ' ' * indent, indent, **kwargs)
            self.push(caret)
        return caret
    
    def insert_li(self, indent, text, child_indent, **kwargs):
        new = MarkdownCaret(child_indent, **kwargs)
        new_li = MarkdownLI([new], indent, text=text)
        cls = MarkdownOL if text[-1] == '.' else MarkdownUL
        warning = None
        if indent < self.indent:
            node = self
            while indent < node.indent:
                node = node.parent.parent
                if not isinstance(node, MarkdownLI):
                    node.push(cls([new_li], indent))
                    break
            else:
                # normal end of while loop
                if not isinstance(node.parent, cls):
                    node = node.parent
                    new_li = cls([new_li], indent)
                elif indent > node.indent:
                    warning = f'insert_li : indent adjusted from {new_li.indent} to {node.indent}'
                    new_li.indent = node.indent
                node.parent.push(new_li)
        elif not isinstance(self.parent, cls):
            if indent == self.indent:
                self = self.parent.parent
            self.push(cls([new_li], indent))
        elif indent == self.indent:
            self.parent.push(new_li)
        elif self.indent and indent < self.indent + 2:
            warning = f'insert_li : indent adjusted from {new_li.indent} to {self.indent}'
            new_li.indent = self.indent
            self.parent.push(new_li)
        else:
            self.push(cls([new_li], indent))
        new.warning = warning
        return new

    def insert_space(self, caret, **kwargs):
        if isinstance(caret, MarkdownText):
            previousElementSibling = caret.previousElementSibling
            newline = '(?<=^|\n)' if isinstance(previousElementSibling, (MarkdownPreCode, MarkdownTABLE, MarkdownP, MarkdownH, MarkdownDocument, MarkdownHR, MarkdownBR, MarkdownListBase)) else '\n'
            if m := re.search(newline + '( *)([-*])$', caret.text):
                indent = len(m[1])
                warning = None
                if indent == self.indent + 1 and self.indent:
                    warning = f'indent adjusted from {indent} to {self.indent}'
                    indent = self.indent
                caret.text = caret.text[:-len(m[0])]
                child_indent = len(m[0])
                if newline != '\n':
                    child_indent += 1
                new = self.insert_li(indent, m[2], child_indent, **kwargs)
                new.warning = warning
                return new

            if m := re.search(newline + r'( *)(\d+\.)$', caret.text):
                caret.text = caret.text[:-len(m[0])]
                indent = len(m[1])
                child_indent = len(m[0]) + 1
                if not indent and (newline != '\n' and not caret.text.endswith('\n') or not caret.text):
                    indent = caret.indent
                    child_indent += indent
                if isinstance(self.parent, MarkdownOL) and self.indent < indent <= self.indent + 2:
                    indent = self.indent
                new = self.insert_li(indent, m[2], child_indent, **kwargs)
                if not caret.text:
                    caret.remove()
                return new
            if caret.indent < 4 and (m := re.search(newline + MarkdownH.regex_text, caret.text)):
                level = len(m[1])
                caret.text = caret.text[:-len(m[0])]
                return self.insert_h(caret, level, **kwargs)
            if m := re.search(newline + MarkdownBLOCKQUOTE.regex_text, caret.text):
                caret.text = caret.text[:-len(m[0])]
                new = self.insert_blockquote(caret, **kwargs)
                if not caret.text:
                    caret.remove()
                return new
        if caret is self.args[0] and isinstance(caret, MarkdownCaret):
            caret.indent += 1
            return caret
        return caret.push_token(' ', **kwargs)

    def insert_asterisk(self, caret, **kwargs):
        if isinstance(caret, MarkdownText):
            if new := self.try_indent_li(caret, '*', **kwargs):
                return new
            return caret.push_asterisk(**kwargs)
        return self.insert_token(caret, '*', **kwargs)
    
    def insert_underscore(self, caret, **kwargs):
        if isinstance(caret, MarkdownText):
            return caret.push_underscore(**kwargs)
        return self.insert_token(caret, '_', **kwargs)

    def try_indent_li(self, caret, word, **kwargs):
        node = self
        text = caret.text
        if re.search(r'\n\n$', text):
            ol_match = re.match(r' *\d+\.?', word)
            ul_match = re.match(r' *[-*]', word)
            preprocess = lambda _: word
            count = sys.maxsize
        elif m := re.search(r'\n\n( *)[-*]$', text):
            if m[1] and len(m[1]) >= self.indent:
                return
            ol_match = False
            ul_match = re.match(r' +', word)
            def preprocess(caret):
                caret.text = caret.text[:-len(m[0])]
                return m[0] + word
            count = sys.maxsize
        elif m := re.search(r'(.*)\n( +)$', text, re.S):
            # possibly the beginning of a new list
            if word in '-*':
                return
            elif isinstance(self.parent, MarkdownOL):
                if len(m[2]) in range(self.indent, self.indent + 4) and word.isdigit():
                    return
                if len(m[2]) >= self.args[0].indent and word in '-*':
                    return
            if not m[1].endswith("\n") and isinstance(self.parent, MarkdownListBase):
                indent = len(m[2])
                caret.text = text[:-(indent + 1)]
                self.push(MarkdownBR(indent, start_idx=caret.end_idx))
                new = MarkdownText(word, indent, **kwargs)
                self.push(new)
                return new
            if m[2] and len(m[2]) in range(self.indent, self.args[0].indent):
                ol_match = False
                ul_match = False
                def preprocess(caret):
                    caret.text = caret.text[:-len(m[2])]
                    return m[2] + word
                count = 1
            else:
                return
        else:
            return

        i = 0
        while node and node.parent:
            i += 1
            if i < count and isinstance(node.parent.parent, MarkdownLI):
                node = node.parent.parent
            else:
                if isinstance(node.parent, MarkdownOL) and not ol_match or isinstance(node.parent, MarkdownUL) and not ul_match:
                    if node.parent.parent:
                        return node.parent.parent.insert_token(node.parent, preprocess(caret), **kwargs)
                    raise Exception(f'try_indent_li is not defined {caret.__class__.__name__}: {self.__class__.__name__}')
                break

    def insert_token(self, caret, word, **kwargs):
        if isinstance(caret, MarkdownText):
            if new := self.try_indent_li(caret, word, **kwargs):
                return new
        return super().insert_token(caret, word, **kwargs)

    append = MarkdownSPAN.append
    insert_bar = MarkdownSPAN.insert_bar
    insert_backtick = MarkdownSPAN.insert_backtick
    try_pattern = MarkdownSPAN.try_pattern
    insert_dollar = MarkdownH.insert_dollar

class MarkdownListBase(MarkdownArgs):
    is_Paragraph = True

    def is_indented(self):
        return False

    def strFormat(self):
        return "\n".join([f"{' ' * self.indent}%s"] * len(self.args))

    def push_token(self, word, **kwargs):
        new = MarkdownText(word, self.indent, **kwargs)
        if isinstance(self.parent, (MarkdownLI, MarkdownP, MarkdownH, MarkdownDocument)):
            self.parent.push(new)
        else:
            self.parent.replace(self, MarkdownP([self, new], self.indent))
        return new

    removeChild = MarkdownSPAN.removeChild

# unordered list
class MarkdownUL(MarkdownListBase):
    def htmlFormat(self):
        return "<ul>\n%s\n</ul>" % "\n".join(["%s"] * len(self.args))

# ordered list
class MarkdownOL(MarkdownListBase):
    def __init__(self, args, indent, parent=None):
        super().__init__(args, indent, parent)
        li = args[0]
        start = None
        if isinstance(li, MarkdownLI):
            start = int(li.text[:-1])
            if start == 1:
                start = None
        self.start = start

    @property
    def start(self):
        return self.kwargs['start']

    @start.setter
    def start(self, start):
        self.kwargs['start'] = start

    def htmlFormat(self):
        ol = f"<ol start={self.start}>" if self.start else "<ol>"
        return f"{ol}\n%s\n</ol>" % "\n".join(["%s"] * len(self.args))

class MarkdownTD(MarkdownUnary):
    def is_indented(self):
        return False
    
    @property
    def textAlign(self):
        return self.kwargs.get('textAlign')
    
    @textAlign.setter
    def textAlign(self, value):
        self.kwargs['textAlign'] = value
    
    def htmlFormat(self):
        if self.textAlign:
            return f'<td style="text-align: {self.textAlign}">%s</td>'
        return '<td>%s</td>'

    def strFormat(self):
        return '%s'

class MarkdownTH(MarkdownUnary):
    def is_indented(self):
        return False
    
    @property
    def textAlign(self):
        return self.kwargs.get('textAlign')
    
    @textAlign.setter
    def textAlign(self, value):
        self.kwargs['textAlign'] = value
    
    def htmlFormat(self):
        if self.textAlign:
            return f'<th style="text-align: {self.textAlign}">%s</th>'
        return '<th>%s</th>'

    def strFormat(self):
        return '%s'

class MarkdownTR(MarkdownArgs):
    def is_indented(self):
        return False

    def htmlFormat(self):
        return f'<tr>{"".join(["%s" for _ in self.args])}</tr>'

    def strFormat(self):
        return " | ".join(["%s" for _ in self.args])

class MarkdownTABLE(MarkdownArgs):
    is_Paragraph = True
    
    def is_indented(self):
        return False
    
    def htmlFormat(self):
        placeholders = "\n".join(["%s"] * len(self.args))
        return f'<table border=1>{placeholders}</table>'

    def strFormat(self):
        colgroup = ['']
        for th in self.args[0].args:
            match th.textAlign:
                case 'center':
                    colgroup.append(":---:")
                case 'left':
                    colgroup.append(":---")
                case 'right':
                    colgroup.append("---:")
                case _:
                    colgroup.append("---")
        colgroup.append('')
        colgroup = ' | '.join(colgroup)
        args = ["%s"] * len(self.args)
        args.insert(1, colgroup)
        return "\n".join(args)

    def insert_space(self, caret, **kwargs):
        if isinstance(caret, MarkdownText):
            caret.text += ' '
        else:
            caret.push_token(' ', **kwargs)
        return caret

    def insert_newline(self, caret, newline_count, indent, next, **kwargs):
        return self.insert_token(caret, '\n' * newline_count + ' ' * indent, **kwargs)

    def insert_bar(self, caret, **kwargs):
        indent = caret.indent
        new = MarkdownCaret(indent, **kwargs)
        self.replace(caret, MarkdownArgsBarSeparated([caret, new], indent))
        return new

    insert_asterisk = MarkdownI.insert_asterisk
    insert_underscore = MarkdownI.insert_underscore

class MarkdownP(MarkdownSPAN):
    is_Paragraph = True

    def htmlFormat(self):
        return '<p>%s</p>' % ('%s' * len(self.args))

    def strFormat(self):
        return '%s' * len(self.args) + '\n\n'

    def insert_newline(self, caret, newline_count, indent, next, **kwargs):
        if isinstance(self.parent, MarkdownArgsBarSeparated):
            return self.parent.insert_newline(self, newline_count, indent, next=next, **kwargs)
        if isinstance(caret, MarkdownText):
            if m := re.search(MarkdownPreCode.code_start_regex, caret.text):
                return self.insert_code(caret, m, indent, **kwargs)
            if m := re.search(MarkdownHR.regex, caret.text):
                return self.insert_hr(caret, m, **kwargs)
        if newline_count == 1 or isinstance(self.parent, MarkdownLI):
            return self.insert_token(caret, "\n" * newline_count + ' ' * indent, **kwargs)
        new = MarkdownText(' ' * indent, indent, **kwargs) if indent > 0 else MarkdownCaret(indent, **kwargs)
        new.start_idx += newline_count
        self.parent.push(new)
        return new

    def insert_list(self, cls, caret, m, **kwargs):
        if isinstance(self.parent, MarkdownSPAN):
            return self.parent.insert_list(cls, caret, m, **kwargs)
        return super().insert_list(cls, caret, m, **kwargs)

class MarkdownBracket(MarkdownPairedGroup):
    is_token = True

    @property
    def start_idx(self):
        return self.arg.start_idx - 1

    def strFormat(self):
        if self.is_closed:
            return '[%s]'
        return '[%s'

    def push_left_bracket(self, **kwargs):
        indent = self.indent
        caret = MarkdownCaret(indent, **kwargs)
        caret.start_idx += 1
        new = MarkdownBracket(caret, indent)
        if isinstance(self.parent, MarkdownSPAN):
            self.parent.push(new)
        else:
            self.parent.replace(self, MarkdownSPAN([self, new], indent))
        return caret

    def push_left_parenthesis(self, **kwargs):
        indent = self.indent
        caret = MarkdownCaret(indent, **kwargs)
        caret.start_idx += 1
        if isinstance(textNode := self.previousElementSibling, MarkdownText) and textNode.text.endswith('!'):
            textNode.text = textNode.text[:-1]
            # if not textNode.text:
                # textNode.remove()
            cls = MarkdownIMG
        else:
            cls = MarkdownA
        new = cls([self.arg, caret], indent)
        self.parent.replace(self, new)
        return caret

    def insert_left_bracket(self, caret, **kwargs):
        warning = f'nested brackets detected: {caret}'
        if isinstance(parent := self.parent, MarkdownBracket) or isinstance(parent := parent.parent, MarkdownBracket):
            bracket = MarkdownText("[", self.indent, start_idx=self.start_idx)
            new = MarkdownText("[", self.indent, **kwargs)
            arg = self.arg
            span = [bracket, *arg.args, new] if isinstance(arg, MarkdownSPAN) else [bracket, arg, new]
            if not isinstance(self.parent, MarkdownSPAN):
                span = MarkdownSPAN(span, self.indent)
            self.parent.replace(self, span)
            return new
        new = super().insert_left_bracket(caret, **kwargs)
        new.warning = warning
        return new

    def insert_space(self, caret, **kwargs):
        return self.insert_token(caret, ' ', **kwargs)

    def insert_right_bracket(self, caret, **kwargs):
        if isinstance(caret, MarkdownText) and isinstance(self.parent, MarkdownLI) and self.previousElementSibling is None:
            match caret.text:
                case ' ':
                    checked = False
                case '*':
                    checked = True
                case _:
                    checked = None
            if checked is not None:
                checkbox = MarkdownCheckbox(self.indent, checked, start_idx=self.start_idx)
                self.parent.replace(self, checkbox)
                return checkbox
        if isinstance(caret, MarkdownCaret):
            new = MarkdownText("[]", self.indent, start_idx=self.start_idx)
            self.parent.replace(self, new)
            return new
        self.is_closed = True
        return self

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        # shrink to normal markdown text
        assert caret is self.arg
        new = MarkdownText('[', self.indent, start_idx=self.start_idx)
        caret = MarkdownSPAN([new, *caret.args] if isinstance(caret, MarkdownSPAN) else [new, caret], self.indent)
        if isinstance(parent := self.parent, MarkdownSPAN):
            parent.replace(self, caret.args)
            caret = caret.args[-1]
        else:
            parent.replace(self, caret)
        return parent.insert_newline(caret, newline_count, indent, **kwargs)

    def insert_backtick(self, caret, **kwargs):
        if isinstance(caret, MarkdownCaret):
            if isinstance(new := self.push_backtick(**kwargs), MarkdownCODE):
                new.arg = MarkdownText(new.arg.plainText, new.indent, start_idx=new.arg.start_idx)
                return new
        return MarkdownH.insert_backtick(self, caret, **kwargs)

    def push_backtick(self, **kwargs):
        return self.push_patten(MarkdownCODE)

    def push_patten(self, cls, stop=None):
        if isinstance(self.parent, (MarkdownSPAN, MarkdownLI)):
            if new := cls.try_pattern(self, stop):
                return new

    insert_asterisk = MarkdownI.insert_asterisk
    insert_underscore = MarkdownI.insert_underscore
    push_token = MarkdownI.push_token

# https://spec.commonmark.org/0.31.2/#thematic-break
class MarkdownHR(Markdown):
    is_Paragraph = True
    regex = r'(?:^|\n) {0,3}([-*_])(?: *\1){2,} *$'
    @computed
    def end_idx(self):
        return self.start_idx + self.indent + 3
    @property
    def text(self):
        return '---'
    def htmlFormat(self):
        return '<hr>'

    def strFormat(self):
        return self.text + '\n'

    def insert_space(self, caret, **kwargs):
        return self.insert_token(caret, ' ', **kwargs)

    def insert_asterisk(self, caret, **kwargs):
        return self.insert_token(caret, '*', **kwargs)

    def insert_underscore(self, caret, **kwargs):
        return self.insert_token(caret, '_', **kwargs)

class MarkdownBR(Markdown):
    @computed
    def end_idx(self):
        return self.start_idx + self.indent + 1
    @property
    def text(self):
        return '\n'
    def htmlFormat(self):
        return '<br>'

    def strFormat(self):
        return '\n\n'

    def insert_space(self, caret, **kwargs):
        return self.insert_token(caret, ' ', **kwargs)

    def insert_asterisk(self, caret, **kwargs):
        return self.insert_token(caret, '*', **kwargs)

    def insert_underscore(self, caret, **kwargs):
        return self.insert_token(caret, '_', **kwargs)

class MarkdownCheckbox(Markdown):
    def __init__(self, indent, checked, parent=None, **kwargs):
        super().__init__(indent, parent, **kwargs)
        self.checked = checked

    @property
    def text(self):
        x = 'x' if self.checked else ' '
        return f'[{x}]'

    @property
    def kwargs_list(self):
        return [self.checked]

    @property
    def checked(self):
        return self.kwargs['checked']

    @checked.setter
    def checked(self, value):
        self.kwargs['checked'] = value

    def htmlFormat(self):
        checked = ' checked' if self.checked else ''
        return f'<input type="checkbox" disabled{checked}>'

    def strFormat(self):
        return self.text

class MarkdownBLOCKQUOTE(MarkdownSPAN):
    regex_text = ' *>$'
    @property
    def start_idx(self):
        return self.args[0].start_idx - 2

    def is_indented(self):
        return False

    def htmlFormat(self):
        return f'<blockquote>{super().strFormat()}</blockquote>'

    def strFormat(self):
        return '> ' + '%s' * len(self.args)

class MarkdownDocument(MarkdownArgs):
    is_Paragraph = True
    is_MarkdownDocument = True
    def is_indented(self):
        return False

    def strFormat(self):
        return "\n".join(['%s'] * len(self.args))

    def insert_space(self, caret, **kwargs):
        if isinstance(caret, MarkdownText):
            text = caret.text
            if m := re.search(r'(?<=^|\n)' + MarkdownH.regex_text, text):
                level = len(m[1])
                caret.text = text[:-len(m[0])]
                new = self.insert_h(caret, level, **kwargs)
                if not caret.text:
                    caret.remove()
                return new

            if m := re.search(r'(?<=^|\n)( *)([-*])$', text):
                return self.insert_ul(caret, m, **kwargs)

            if m := re.search(r'(?<=^|\n)( *)(\d+\.)$', text):
                return self.insert_ol(caret, m, **kwargs)

            caret.text += ' '
            return caret
        else:
            new = MarkdownText(' ', self.indent, **kwargs)
            if isinstance(caret, MarkdownCaret):
                self.replace(caret, new)
            else:
                self.replace(caret, MarkdownSPAN([caret, new], caret.indent))
            return new

    @property
    def root(self):
        return self

    def insert_newline(self, caret, newline_count, indent, next, **kwargs):
        if isinstance(caret, MarkdownText):
            if m := re.search(MarkdownPreCode.code_start_regex, caret.text):
                return self.insert_code(caret, m, indent, **kwargs)
            if m := re.search(MarkdownHR.regex, caret.text):
                return self.insert_hr(caret, m, **kwargs)

        if newline_count > 1:
            if caret.is_token:
                if indent >= 4:
                    caret = MarkdownText(' ' * indent, self.indent, **kwargs)
                    caret.start_idx += newline_count
                    self.push(MarkdownPreCode(caret, self.indent, None))
                    return caret
                self.replace(caret, MarkdownP([caret], caret.indent))
            caret = MarkdownText("\n" * (newline_count - 1) + ' ' * indent, self.indent, **kwargs)
            caret.start_idx += 1
            self.push(caret)
            return caret

        return self.insert_token(caret, "\n" * newline_count + ' ' * indent, **kwargs)

    def insert_h(self, caret, level, **kwargs):
        caret = MarkdownCaret(self.indent, **kwargs)
        self.push(MarkdownH(caret, self.indent, level))
        return caret

    def insert_token(self, caret, char, **kwargs):
        is_token = caret.is_token
        if not is_token and not caret.is_Paragraph or isinstance(caret, MarkdownText):
            return super().insert_token(caret, char, **kwargs)
        new = MarkdownText(char, self.indent, **kwargs)
        if is_token:
            self.replace(caret, MarkdownSPAN([caret, new], self.indent))
        else:
            self.push(new)
        return new

    def append(self, new):
        self.push(new)
        return new

    insert_asterisk = MarkdownI.insert_asterisk
    insert_underscore = MarkdownI.insert_underscore
    insert_bar = MarkdownSPAN.insert_bar
    insert_backtick = MarkdownH.insert_backtick
    insert_dollar = MarkdownH.insert_dollar

Markdown.MarkdownCODE = MarkdownCODE
Markdown.MarkdownText = MarkdownText
Markdown.MarkdownSPAN = MarkdownSPAN
Markdown.MarkdownBracket = MarkdownBracket

class MarkdownParser(AbstractParser):
    def __init__(self):
        ...

    def init(self):
        caret = MarkdownCaret(start_idx=0)
        self.caret = caret
        self.root = MarkdownDocument([caret], 0)

    def __str__(self):
        return str(self.root)

    @property
    def html(self):
        return self.root.html

    def build_debug(self, text):
        self.init()
        history = ''  # for debug purposes
        for start_idx, token in enumerate(text):
            try:
                if history.endswith(r'''```
2.'''): 
                    print(history)
                self.parse(token, start_idx=start_idx)
            except Exception as e:
                print(e)
                traceback.print_exc()
                print(history)
                raise e
            history += token
        start_idx = len(text)
        self.parse("\n", start_idx=start_idx)
        self.parse('', start_idx=start_idx + 1)
        return self.root

    def build(self, text, warning=[]):
        self.init()
        for start_idx, token in enumerate(text):
            caret = self.parse(token, start_idx=start_idx)
            if w := caret.warning:
                warning.append(w)
        start_idx = len(text)
        self.parse("\n", start_idx=start_idx)
        self.parse('', start_idx=start_idx + 1)
        return self.root

def test():
    text = '''\
#### **在制药工业中的潜在应用**
this is ~~some [strikethrough](http://www.baidu.com '百度网址')~~ link
this isn't ~~a [strikethrough](http://www.baidu.com "百度网址") ~~ link
this is ~~a piece of `strikethrough [not a valid link](http://www.baidu.com)`~~ code
this is ~~a piece of strikethrough http://www.baidu.com~~ code
1. **质子交换膜的应用**  
   通过采用碱金属离子型全氟磺酸树脂制备的复合质子交换膜，具有很好的气密性和质子传导能力，可用于制药设备中的化学反应或分离过程[8]。
    | 参考 | 具体形式 |  应用领域|
    | -------- | --------: | :---- |
    | 质子交换膜 | 复合质子交换膜 | [9] |
    | 酸催化剂 | [3] |  强固体酸催化剂 |

2. **酸催化剂的应用**  
   含氟磺酸树脂因其强固体酸性，被认为是优质的酸催化剂。相比液体酸催化剂，它们具有催化活性好、选择性高、易于分离和重复使用等优势[3]。
    | 具体形式 | 应用领域 | 参考 |
    | -------- | -------- | ---- |
    | 质子交换膜 | 复合质子交换膜 | [7] |
    | 酸催化剂 | 强固体酸 | [3] 催化剂 |

  | 应用领域 | 具体形式 | 参考 |
  | -------- | :-------- | :---- |
  | 质子交换膜 | 复合质子交换膜 | [8] |
  | 酸催化剂 | 强固体酸催化剂 | [3] |
```C++
if (this.args && this.args.length > 0) {
}  
'''
    self = MarkdownParser()
    try:
        self.build_debug(text)
    except Exception as e:
        traceback.print_exc()
        print(e)
    print(self)
    exit()

def test_table(id=None, Rank=None, offset=0):
    import json
    from std import MySQL
    kwargs = {
        'where' : 'json_length(answer) > 0',
        'dictionary' : True,
    }
    if id:
        kwargs |= {
            'id' : id,
        }
    else:
        kwargs |= {
            'offset' : offset,
            'limit' : 10000000,
            'fetch_size' : 1024
        }
    for data in MySQL.instance.select('reward', **kwargs):
        id = data['id']
        offset += 1
        print('testing id =', id, 'offset =', offset)
        for i, answer in enumerate(json.loads(data['answer'])):
            try:
                if Rank is not None:
                    if i != Rank - 1:
                        continue
                if isinstance(answer, str):
                    answer = [answer]
                for answer in answer:
                    self = MarkdownParser()
                    self.build_debug(answer)
                    if Rank is not None:
                        print(self.html)
            except Exception as e:
                print('Rank', i + 1)
                print(f"http://192.168.18.133:8000/label/query.php?id={id}")
                import traceback
                traceback.print_exc()
                print(e)
                return

# convert $$...$$ block latex to \[...\] block latex to facilitate parsing
def convert_block_latex(latex):
    return re.sub(r'\$\$([\s\S]+?)\$\$', r'\[\1\]', latex)

if __name__ == '__main__':
    test()
    test_table(
        # id = 104341 # badcase
        id=3644122, 
        Rank=1
    )
