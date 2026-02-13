# to comply with the standards of java and mysql regex engine
import traceback, regex as re
from functools import partial
from std import computed, clip, splice, binary_search
from std.parser.newline import NewLineParser
from std.parser.node import IndentedNode, clone, Closable, AbstractParser, case
from std.sets import Range

def add(arr, val):
    return [x + val for x in arr]

class XML(IndentedNode):
    is_XMLText = False
    is_XMLContainerTag = False
    is_XMLVoidTag = False
    is_XMLArgs = False
    is_XMLUnbalancedTag = False
    
    def has_recursive_error(self):
        try:
            str(self.root)
        except Exception as e:
            return True

    @computed
    def physicalText(self):
        caret = self
        s = ''
        while caret is not None:
            s += str(caret)
            caret = caret.parent
#         s += '\n'
        return s
    
    def push_special(self, token, **kwargs):
        new = XMLText(str(self) + token, start_idx=self.start_idx)
        self.parent.replace(self, new)
        return new

    def enumerate(self):
        assert False, type(self)
        
    def has(self, cls):
        return False
    
    @property
    def zeros(self):
        return []
    
    @computed
    def style(self):
        return {}

    def modify_style(self, tag):
        if self.text:
            set = Range(0, len(self.text))
            _style = self.style
            if tag in _style:
                _style[tag] = _style[tag].union_without_merging(set)
            else:
                _style[tag] = set

    @property
    def length(self):
        return self.end_idx - self.start_idx

    @computed
    def style_traits(self):
        style_traits = [''] * len(self.text)
        for i, s in enumerate(self.style_input):
            s = [*s]
            s.sort()
            s = '.'.join(s)
            style_traits[i] = s
        return style_traits
    
    @computed
    def style_input(self):
        style_input = [set() for _ in range(len(self.text))]
        for tag, s in self.style.items():
            if s.is_Range:
                for i in range(s.start_idx, s.end_idx):
                    style_input[i].add(tag)
            elif s.is_Union:
                for s in s.args:
                    for i in range(s.start_idx, s.end_idx):
                        style_input[i].add(tag)
        return style_input

    @case(' ')
    def case(self, **kwargs):
        return self.parent.insert_space(self, **kwargs)

    @case("\n")
    def case(self, **kwargs):
        return NewLineParser(self, **kwargs)

    @case('<')
    def case(self, **kwargs):
        return self.parent.insert_lt(self, **kwargs)

    @case('>')
    def case(self, **kwargs):
        return self.parent.insert_gt(self, **kwargs)

    @case('"')
    def case(self, **kwargs):
        return self.parent.insert_quotation(self, **kwargs)

    @case("'")
    def case(self, **kwargs):
        return self.parent.insert_apostrophe(self, **kwargs)
    
    @case('/')
    def case(self, **kwargs):
        return self.parent.insert_solidus(self, **kwargs)

    @case('=')
    def case(self, **kwargs):
        return self.parent.insert_eq(self, **kwargs)

    @case('!')
    def case(self, **kwargs):
        return self.parent.insert_exclamation(self, **kwargs)

    @case('&')
    def case(self, **kwargs):
        return self.parent.insert_ampersand(self, **kwargs)

    @case(';')
    def case(self, **kwargs):
        return self.parent.insert_semicolon(self, **kwargs)

    @case('`')
    def case(self, **kwargs):
        return self.parent.insert_backtick(self, **kwargs)

    @case(']')
    def case(self, **kwargs):
        return self.parent.insert_right_bracket(self, **kwargs)

    @case("\t")
    def case(self, **kwargs):
        return self.parent.insert_token(self, '    ', **kwargs)

    @case
    def case(self, **kwargs):
        return self.parent.insert_token(self, self.key, **kwargs)

    def has_newline(self):
        return False
    
    @property
    def html(self):
        return str(self)

class XMLCaret(XML):
    @property
    def end_idx(self):
        return self.start_idx

    def strFormat(self):
        return ''

    def append(self, new):
        self.parent.replace(self, new)
        return new

    def push_token(self, word, **kwargs):
        new = XMLText(word, **kwargs)
        self.parent.replace(self, new)
        return new

    @property
    def text(self):
        return ''

    @computed
    def physicalText(self):
        return ""
    
    @property
    def logicalLength(self):
        return 0
    
    @property
    def texts(self):
        return []
    
    def enumerate(self):
        yield

    def has(self, cls):
        return isinstance(self, cls)
    
    @property
    def length(self):
        return 0


class XMLText(XML):
    is_XMLText = True
    def __init__(self, text, indent=0, start_idx=None, parent=None, **kwargs):
        assert isinstance(text, str) and isinstance(indent, int) and isinstance(start_idx, int)
        super().__init__(indent, parent, **kwargs)
        self.text = text
        self.start_idx = start_idx

    def append(self, new):
        if self.parent:
            return self.parent.insert(self, new)
        raise Exception(f'append is not defined {new}: {self.__class__.__name__}')

    def push_token(self, word, **kwargs):
        self.text += word
        return self

    def strFormat(self):
        return self.text

    @property
    def kwargs_list(self):
        return [self.text]

    @computed
    def physicalText(self):
        return self.text
    
    @property
    def logicalLength(self):
        return len(self.text)

    @computed
    def texts(self):
        return [self.text]
    
    def logical2physical(self, pos):
        return pos

    def physical2logical(self, pos):
        return pos
    
    def is_physically_valid(self, pos):
        return 0 <= pos < self.length

    def is_sibling(self, start_idx, end):
        return 0 <= start_idx < end <= self.length
        
    def getPhysicalIndices(self, start_idx, end_idx):
        return start_idx, end_idx
        
    def enumerate(self):
        yield (self.lexeme, False)

    def has(self, cls):
        return isinstance(self, cls)

class XMLArgs(XML):
    is_XMLArgs = True
    
    def __init__(self, args, indent=0, parent=None):
        super().__init__(indent, parent)
        self.args = args
        for arg in args:
            arg.parent = self

    def clone(self):
        return self.__class__(clone(self.args), *self.kwargs_list)

    def strFormat(self):
        return '%s' * len(self.args)

    def insert_lt(self, caret, **kwargs):
        if isinstance(caret, XMLCaret):
            caret.start_idx += 1
            self.replace(caret, XMLTagBegin(caret))
        else:
            caret = XMLCaret(**kwargs)
            caret.start_idx += 1
            self.push(XMLTagBegin(caret))
        return caret

    def insert_gt(self, caret, **kwargs):
        return self.parent.insert_gt(self, **kwargs)

    def insert_ampersand(self, caret, **kwargs):
        if isinstance(caret, XMLCaret):
            caret.start_idx += 1
            self.replace(caret, XMLEntity(caret))
            return caret
        else:
            new = XMLCaret(**kwargs)
            new.start_idx += 1
            self.replace(caret, XMLArgsNullSeparated([caret, XMLEntity(new)]))
            return new

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        return self.insert_token(caret, '\n' * newline_count + ' ' * indent, **kwargs)

    def insert_semicolon(self, caret, **kwargs):
        return self.insert_token(caret, ';', **kwargs)

    def insert_space(self, caret, **kwargs):
        return self.insert_token(caret, ' ', **kwargs)
    
    def insert_backtick(self, caret, **kwargs):
        return self.insert_token(caret, '`', **kwargs)
    
    def insert_right_bracket(self, caret, **kwargs):
        return self.insert_token(caret, ']', **kwargs)

    def insert_apostrophe(self, caret, **kwargs):
        return self.insert_token(caret, "'", **kwargs)

    def insert_quotation(self, caret, **kwargs):
        return self.insert_token(caret, '"', **kwargs)

    def insert_solidus(self, caret, **kwargs):
        return self.insert_token(caret, '/', **kwargs)

    def insert_eq(self, caret, **kwargs):
        return self.insert_token(caret, '=', **kwargs)
    
    def insert_exclamation(self, caret, **kwargs):
        return self.insert_token(caret, '!', **kwargs)

    def push_token(self, token, **kwargs):
        text = XMLText(token, **kwargs)
        self.parent.push(text)
        return text

    @computed
    def physicalText(self):
        return ''.join(str(nd) for nd in self.args)

    @property
    def start_idx(self):
        return self.args[0].start_idx
    
    @property
    def end_idx(self):
        return self.args[-1].end_idx

    @computed
    def text(self):
        return ''.join(nd.text for nd in self.args)
    
    @property
    def logicalLength(self):
        return sum(el.logicalLength for el in self.args)

    @computed
    def texts(self):
        return [text for nd in self.args for text in nd.texts]
    
    @computed
    def zeros(self):
        zeros = []
        length = 0
        for arg in self.args:
            zeros += [zero + length for zero in arg.zeros]
            length += len(arg.text)
        return zeros

    @computed
    def style(self):
        for i, tagEnd in enumerate(self.args):
            if tagEnd.is_XMLUnbalancedTag:
                _self = tagEnd.ContainerTag
                assert _self.tagEnd is tagEnd, "_self.tagEnd is tagEnd"
                while True:
                    parent = _self.parent
                    if parent.is_XMLArgs:
                        index = parent.args.index(_self)
                        for j in range(index + 1, i if parent is self else len(parent.args)):
                            parent.args[j].modify_style(tagEnd.tag)
                    _self = parent
                    if parent is self:
                        break
        
        _style = {}
        length = 0
        for arg in self.args:
            for tag, set in arg.style.items():
                set += length
                if tag in _style:
                    _style[tag] = _style[tag].union_without_merging(set)
                else:
                    _style[tag] = set
            
            length += len(arg.text)
        
        return _style

    def enumerate(self):
        for node in self.args:
            yield from node.enumerate()

    def has(self, cls):
        if isinstance(self, cls):
            return True
        for e in self.args:
            if e.has(cls):
                return True
        return False

    @computed
    def logicalOffset(self):
        logicalOffset = []
        start_idx = 0
        for arg in self.args:
            end_idx = start_idx + arg.logicalLength
            logicalOffset.append((start_idx, end_idx))
            start_idx = end_idx
        
        return logicalOffset
    
    @computed
    def physicalOffset(self):
        physicalOffset = []
        start_idx = 0
        for arg in self.args:
            end_idx = start_idx + arg.length
            physicalOffset.append((start_idx, end_idx))
            start_idx = end_idx
            
        return physicalOffset
    
    @computed
    def offsets(self):
        offsets = []
        offset = 0
        for arg in self.args:
            offsets.append(offset)
            offset += arg.length - arg.logicalLength
        
        return offsets
        
    def logical2physical(self, pos):
        logicalOffset, offsets = self.logicalOffset, self.offsets
        assert logicalOffset, logicalOffset
        index = binary_search(logicalOffset, pos, lambda args, hit: -1 if hit >= args[1] else 1 if hit < args[0] else 0)

        prev_start = logicalOffset[index][0]
        return self.args[index].logical2physical(pos - prev_start) + prev_start + offsets[index]
    
    def physical2logical(self, pos):
        physicalOffset, offsets = self.physicalOffset, self.offsets
        assert physicalOffset, physicalOffset
        index = binary_search(physicalOffset, pos, lambda args, hit: -1 if hit >= args[1] else 1 if hit < args[0] else 0)

        prev_start = physicalOffset[index][0]
        return self.args[index].physical2logical(pos - prev_start) + prev_start - offsets[index]
    
    def is_physically_valid(self, pos):
        physicalOffset, offsets = self.physicalOffset, self.offsets
        assert physicalOffset, physicalOffset
        index = binary_search(physicalOffset, pos, lambda args, hit: -1 if hit >= args[1] else 1 if hit < args[0] else 0)
        if index < len(physicalOffset):
            prev_start = physicalOffset[index][0]
            pos -= prev_start
            if pos >= 0:
                return self.args[index].is_physically_valid(pos)
        
    def is_sibling(self, start_idx, end):
        if start_idx < end:
            physicalOffset, offsets = self.physicalOffset, self.offsets
            assert physicalOffset, physicalOffset
            index = binary_search(physicalOffset, start_idx, lambda args, hit: -1 if hit >= args[1] else 1 if hit < args[0] else 0)
            _index = binary_search(physicalOffset, end - 1, lambda args, hit: -1 if hit >= args[1] else 1 if hit < args[0] else 0)
            if _index == index < len(physicalOffset):
                prev_start = physicalOffset[index][0]
                start_idx -= prev_start
                end -= prev_start
                if start_idx >= 0:
                    return self.args[index].is_sibling(start_idx, end)
            if index < _index < len(physicalOffset):
                if self.args[index].is_XMLText:
                    if self.args[_index].is_XMLText:
                        return True
                    if self.args[_index].is_XMLContainerTag or self.args[_index].is_XMLVoidTag:
                        prev_start = physicalOffset[_index][0]
                        end -= prev_start
                        if end == self.args[_index].length:
                            return True

    def cmp(self, args, hit):
        return -1 if hit >= args[1] else 1 if hit < args[0] else 0
        
    def getPhysicalIndices(self, start_idx, end_idx):
        logicalOffset, offsets = self.logicalOffset, self.offsets
        index = binary_search(logicalOffset, start_idx, self.cmp)
        _index = binary_search(logicalOffset, end_idx - 1, self.cmp)
        
        if index == _index:
            prev_start = logicalOffset[index][0]
            return add(self.args[index].getPhysicalIndices(start_idx - prev_start, end_idx - prev_start), prev_start + offsets[index])
        else:
            [prev_start, prev_stop] = logicalOffset[index]
            _prev_start = logicalOffset[_index][0]
            start_idx = add(self.args[index].getPhysicalIndices(start_idx - prev_start, prev_stop - prev_start), prev_start + offsets[index])[0]
            end_idx = add(self.args[_index].getPhysicalIndices(0, end_idx - _prev_start), _prev_start + offsets[_index])[1]
            return [start_idx, end_idx]

    def insert_token(self, caret, token, **kwargs):
        return caret.push_token(token, **kwargs)

    def has_newline(self):
        return any(arg.has_newline() for arg in self.args)

class XMLArgsNullSeparated(XMLArgs):
    def insert_ampersand(self, caret, **kwargs):
        if isinstance(caret, XMLCaret):
            caret.start_idx += 1
            self.replace(caret, XMLEntity(caret))
            return caret
        new = XMLCaret(**kwargs)
        new.start_idx += 1
        self.push(XMLEntity(new))
        return new

    def insert_token(self, caret, token, **kwargs):
        if isinstance(caret, (XMLCaret, XMLText)):
            return super().insert_token(caret, token, **kwargs)
        caret = XMLText(token, **kwargs)
        self.push(caret)
        return caret

    @property
    def html(self):
        return ''.join(arg.html for arg in self.args)

class XMLTagBase(XMLArgs):

    @property
    def start_idx(self):
        return self.tagName.start_idx - 1

    @property
    def end_idx(self):
        return super().end_idx + 1

    @start_idx.setter
    def start_idx(self, start_idx):
        self.tagName.start_idx = start_idx + 1

    @property
    def tagName(self):
        return self.args[0]
    
    @property
    def attributes(self):
        return self.args[1:]
    
    def insert_space(self, caret, **kwargs):
        if caret is self.tagName and isinstance(caret, XMLCaret):
            return self.push_special(' ', **kwargs)
        caret = XMLCaret(**kwargs)
        self.push(caret)
        return caret

    def insert_token(self, caret, token, **kwargs):
        # if caret is self.tagName:
        if isinstance(caret, XMLCaret) and (token.isdigit() or token in "`~@#$%^&()_=+[{]}\\|,./?-") or \
            isinstance(caret, XMLText) and token in "`~@#$%^&()=+[{]}\\|,/?" or \
            isinstance(caret, XMLEq):
            return self.push_special(token, **kwargs)
        return caret.push_token(token, **kwargs)

    def insert_eq(self, caret, **kwargs):
        if caret is self.tagName and isinstance(caret, XMLCaret):
            return self.push_special('=', **kwargs)
        new = XMLCaret(**kwargs)
        new.start_idx += 1
        self.replace(caret, XMLEq(caret, new))
        return new

    def insert_lt(self, caret, **kwargs):
        if isinstance(caret, XMLCaret) and caret is self.tagName:
            text = str(self)
            if (prev := self.previousElementSibling) and isinstance(prev, XMLText):
                prev.text += text
            else:
                self.parent.replace(self, [XMLText(text, start_idx=self.start_idx), self])
                self.start_idx = kwargs['start_idx']
            return caret
        return super().insert_lt(caret, **kwargs)

    def insert_gt(self, caret, **kwargs):
        self.is_closed = True
        return self

    def insert_exclamation(self, caret, **kwargs):
        if caret is self.tagName and isinstance(caret, XMLCaret):
            return self.insert_token(caret, '!', **kwargs)
        return self.push_special('!', **kwargs)
        
    def insert_apostrophe(self, caret, **kwargs):
        return self.push_special("'", **kwargs)

    def insert_quotation(self, caret, **kwargs):
        return self.push_special('"', **kwargs)

class XMLTagBegin(XMLTagBase, Closable):
    def __init__(self, arg, indent=0, parent=None, **kwargs):
        super().__init__([arg], indent, parent, **kwargs)

    def __str__(self):
        s = f"<{self.tagName}"
        if attributes := ' '.join(str(attr) for attr in self.attributes):
            s += ' ' + attributes
        if self.is_closed:
            s += '>'
        return s

    def insert_solidus(self, caret, **kwargs):
        if caret is self.tagName:
            if isinstance(caret, XMLCaret):
                caret.start_idx += 1
                self.parent.replace(self, XMLTagEnd(caret))
                return caret
            return self.push_special('/', **kwargs)
        self.parent.replace(self, XMLTagVoid(self.args))
        return caret
    

class XMLTagVoid(XMLTagBase, Closable):
    is_XMLTagVoid = True
    
    def __str__(self):
        s = f"<{self.tagName}"
        if attributes := ' '.join(str(attr) for attr in self.attributes):
            s += ' ' + attributes
        s += ' /'
        if self.is_closed:
            s += '>'
        return s
        # text = tag.lower()
        # if tag == 'img':
        #     text = '★'
        # elif tag == 'mspace':
        #     text = ' '
        # elif tag == 'br':
        #     text = '\n'
        # else:
        #     text = '?'
            
        # self.text = text
    def insert_solidus(self, caret, **kwargs):
        return self.push_special('/', **kwargs)

class XMLUnary(XMLArgs):
    def __init__(self, arg, indent=0, parent=None):
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

    def strFormat(self):
        return '%s'

    def insert_token(self, caret, token, **kwargs):
        return caret.push_token(token, **kwargs)

    def replace(self, old, new):
        if isinstance(new, list):
            new = XMLArgsNullSeparated(new)
        super().replace(old, new)

class XMLPairedGroup(XMLUnary, Closable):
    def insert_space(self, caret, **kwargs):
        return self.insert_token(caret, ' ', **kwargs)

    def insert_solidus(self, caret, **kwargs):
        return self.insert_token(caret, '/', **kwargs)
    
    def insert_eq(self, caret, **kwargs):
        return self.insert_token(caret, '=', **kwargs)

    def insert_exclamation(self, caret, **kwargs):
        return self.insert_token(caret, '!', **kwargs)

    def insert_lt(self, caret, **kwargs):
        return self.insert_token(caret, '<', **kwargs)

    def insert_gt(self, caret, **kwargs):
        return self.insert_token(caret, '>', **kwargs)

    def insert_ampersand(self, caret, **kwargs):
        return self.insert_token(caret, '&', **kwargs)

    def insert_semicolon(self, caret, **kwargs):
        return self.insert_token(caret, ';', **kwargs)

    def insert_backtick(self, caret, **kwargs):
        return self.insert_token(caret, '`', **kwargs)

# apostrophe
class XMLApostrophe(XMLPairedGroup):
    def strFormat(self):
        s = "'%s"
        if self.is_closed:
            s += "'"
        return s

    def insert_apostrophe(self, caret, **kwargs):
        self.is_closed = True
        return self

    def insert_quotation(self, caret, **kwargs):
        return self.insert_token(caret, '"', **kwargs)


# quotation mark
class XMLQuotation(XMLPairedGroup):
    def strFormat(self):
        s = '"%s'
        if self.is_closed:
            s += '"'
        return s

    def insert_quotation(self, caret, **kwargs):
        self.is_closed = True
        return self

    def insert_apostrophe(self, caret, **kwargs):
        return self.insert_token(caret, "'", **kwargs)


class XMLTagEnd(XMLUnary, Closable):
    is_XMLTagEnd = True
    
    @property
    def tagName(self):
        return self.arg

    def __str__(self):
        s = f"</{self.tagName}"
        if self.is_closed:
            s += '>'
        return s

    def insert_gt(self, caret, **kwargs):
        self.is_closed = True
        if not isinstance(parent := self.parent, XMLUnary):
            tagName = self.tagName.text.lower()
            args = parent.args
            if len(args) == 1:
                parent = self.parent
                if isinstance(parent, XMLDocument) and isinstance(parent := parent.parent, XMLParser) and (parent := parent.parent) and parent.is_MarkdownSPAN:
                    if tagBegin := self.parent.parent.search_tagBegin(partial(XMLParser.match_XMLTagBegin, tagName=tagName), XMLContainerTag):
                        document = tagBegin.parent.parent
                        containerTag = tagBegin.parent
                        containerTag[0] = containerTag.tagBegin.root.args[0]
                        containerTag[-1] = containerTag.tagEnd.root.args[0]
                        assert all(arg.parent is containerTag for arg in containerTag.args)
                        tagBegin.root[0] = containerTag
                        document.args[-1] is containerTag
                        document[-1] = tagBegin
                        tagBegin.caret = tagBegin.root.args[0]
                        assert all(arg.parent is document for arg in document.args)
                        return tagBegin
            else:
                for i in range(len(args) - 2, -1, -1):
                    if isinstance(args[i], XMLTagBegin) and args[i].tagName.text.lower() == tagName:
                        tag = XMLContainerTag(args[i:])
                        del args[i:]
                        parent.push(tag)
                        return tag
        return self

    def insert_lt(self, caret, **kwargs):
        caret = XMLCaret(**kwargs)
        caret.start_idx += 1
        self.parent.replace(self, [XMLText(str(self), start_idx=self.start_idx), XMLTagBegin(caret)])
        return caret

    def insert_apostrophe(self, caret, **kwargs):
        return self.push_special("'", **kwargs)
    
    def insert_quotation(self, caret, **kwargs):
        return self.push_special('"', **kwargs)

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        return self.push_special('\n' * newline_count + ' ' * indent, **kwargs)

    def insert_solidus(self, caret, **kwargs):
        return self.push_special('/', **kwargs)

    def insert_exclamation(self, caret, **kwargs):
        return self.push_special('!', **kwargs)

    def insert_eq(self, caret, **kwargs):
        return self.push_special('=', **kwargs)

class XMLBinary(XMLArgs):
    def __init__(self, lhs, rhs, indent=0, parent=None):
        super().__init__([lhs, rhs], indent, parent)

    @property
    def lhs(self):
        return self.args[0]

    @lhs.setter
    def lhs(self, value):
        self.args[0] = value
        value.parent = self

    @property
    def rhs(self):
        return self.args[1]

    @rhs.setter
    def rhs(self, value):
        self.args[1] = value
        value.parent = self

    def toJSON(self):
        return {
            self.func: [
                self.lhs.toJSON(),
                self.rhs.toJSON()
            ]
        }

    def push(self, arg):
        raise Exception(f"push operation not allowed for {self.__class__.__name__}")

class XMLEq(XMLBinary):
    def strFormat(self):
        return '%s=%s'

    def insert_apostrophe(self, caret, **kwargs):
        if caret is self.rhs and isinstance(caret, XMLCaret):
            self.rhs = XMLApostrophe(caret)
        return caret

    def insert_quotation(self, caret, **kwargs):
        if caret is self.rhs and isinstance(caret, XMLCaret):
            self.rhs = XMLQuotation(caret)
        return caret

    def insert_space(self, caret, **kwargs):
        caret = XMLCaret(**kwargs)
        self.parent.push(caret)
        return caret

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if isinstance(this := self.parent, XMLTagBegin):
            return this.push_special('\n' * newline_count + ' ' * indent, **kwargs)
        return super().insert_newline(caret, newline_count, indent, **kwargs)

    def insert_solidus(self, caret, **kwargs):
        return self.parent.insert_solidus(self, **kwargs)

    def insert_ampersand(self, caret, **kwargs):
        return self.push_special('&', **kwargs)

    def insert_lt(self, caret, **kwargs):
        return self.push_special('<', **kwargs)

    def insert_eq(self, caret, **kwargs):
        return self.push_special('=', **kwargs)

    def insert_exclamation(self, caret, **kwargs):
        return self.push_special('!', **kwargs)

    def insert_token(self, caret, token, **kwargs):
        return self.parent.insert_token(self, token, **kwargs)

class XMLEntity(XMLUnary, Closable):
    is_XMLEntity = True
    
    @property
    def start_idx(self):
        return self.arg.start_idx - 1

    @property
    def end_idx(self):
        return self.arg.end_idx

    def unescape(self):
        import html
        return html.unescape(f'&{self.arg};')

    def strFormat(self):
        s = '&%s'
        if self.is_closed:
            s += ';'
        return s
    
    def insert_semicolon(self, caret, **kwargs):
        self.is_closed = True
        return self

    def insert_token(self, caret, token, **kwargs):
        if isinstance(caret, XMLText) and len(caret.text) >= 32:
            # &(#[0-9]+|#x[0-9a-f]+|[^\t\n\f <&#;]{1,32});
            return self.push_special(token, **kwargs)
        return super().insert_token(caret, token, **kwargs)

    # token in {"\t", "\n", "\f", ' ', '<', '&', '='}:
    def insert_ampersand(self, caret, **kwargs):
        return self.push_special('&', **kwargs)

    def insert_lt(self, caret, **kwargs):
        return self.push_special('<', **kwargs)

    def insert_space(self, caret, **kwargs):
        return self.push_special(' ', **kwargs)

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        return self.push_special("\n" * newline_count + ' ' * indent, **kwargs)
    
    def insert_eq(self, caret, **kwargs):
        return self.push_special('=', **kwargs)

    def insert_exclamation(self, caret, **kwargs):
        return self.push_special('!', **kwargs)

    def insert_solidus(self, caret, **kwargs):
        return self.push_special('/', **kwargs)

    def insert_apostrophe(self, caret, **kwargs):
        return self.push_special("'", **kwargs)

    def insert_quotation(self, caret, **kwargs):
        return self.push_special('"', **kwargs)

    def insert_backtick(self, caret, **kwargs):
        if isinstance(doc := self.parent, XMLDocument) and isinstance(parser := doc.parent, XMLParser) and (md := parser.parent):
            new = self.push_special('', start_idx=kwargs['start_idx'] - 1)
            new = md.MarkdownText(new.text, md.indent, start_idx=new.start_idx)
            md.replace(parser, new)
            return new.parse('`', **kwargs)
        return self.push_special('`', **kwargs)

class XMLUnbalancedTag(XML):
    is_XMLUnbalancedTag = True

    def __init__(self, tagEnd, ContainerTag, indent=0, parent=None):
        super().__init__(indent, parent)
        self.tagEnd = tagEnd
        self.ContainerTag = ContainerTag
        ContainerTag.tagEnd = self

    @property
    def tag(self):
        return self.tagEnd.tag
    
    @property
    def start_idx(self):
        return self.tagEnd.start_idx
    
    @property
    def end_idx(self):
        return self.tagEnd.end_idx
    
    @computed
    def physicalText(self):
        return str(self.tagEnd)

    @computed
    def text(self):
        return ''

    @property
    def logicalLength(self):
        return 0

    @computed
    def texts(self):
        return []
    
    @computed
    def zeros(self):
        return [0]
    
class XMLContainerTag(XMLArgs):
    is_XMLContainerTag = True
    @property
    def tagBegin(self):
        return self.args[0]
    
    @property
    def tagEnd(self):
        return self.args[-1]
    
    @tagEnd.setter
    def tagEnd(self, tagEnd):
        self.args[-1] = tagEnd
    
    @property
    def children(self):
        return self.args[1:-1]

    def set_tagEnd(self, tagEnd):
        self.tagEnd = tagEnd
        if 'physicalText' in self.__dict__:
            del self.__dict__['physicalText']
        
    @property
    def tag(self):
        return self.tagBegin.tag
    
    @property
    def start_idx(self):
        return self.tagBegin.start_idx
    
    @property
    def end_idx(self):
        if self.is_unbalanced:
            if len(self.args) == 1 and isinstance(self.args[0], XMLCaret):
                return self.tagBegin.end_idx
            return self.args[-1].end_idx
        return self.tagEnd.end_idx

    @computed
    def physicalText(self):
        s = str(self.tagBegin) + ''.join(str(arg) for arg in self.args[1:-1])
        if self.is_unbalanced:
            return s
        return s + str(self.tagEnd)

    @computed
    def text(self):
        return ''.join(arg.text for arg in self.args)

    @property
    def logicalLength(self):
        return sum(el.logicalLength for el in self.args)

    @computed
    def texts(self):
        return [text for nd in self.args for text in nd.texts]
    
    @computed
    def zeros(self):
        if not self.text:
            return [0]
        zeros = []
        length = 0
        for arg in self.args:
            zeros += [zero + length for zero in arg.zeros]
            length += len(arg.text)
        return zeros
        
    @computed
    def style(self):
        _style = {}
        if self.text:
            if self.arg.is_XMLArgs:
                args = self.arg.args
                if self.tag in ("msub", "munder"):
                    if len(args) == 2:
                        args[1].modify_style('sub')
                            
                elif self.tag in ("msup", "mover"):
                    if len(args) == 2:
                        args[1].modify_style('sup')
                            
                elif self.tag in ("msubsup", "munderover"):
                    if len(args) == 3:
                        args[1].modify_style('sub')
                        args[2].modify_style('sup')
            
            _style[self.tag] = Range(0, len(self.text))
            for tag, set in self.arg.style.items():
                if tag in _style:
                    _style[tag] = _style[tag].union_without_merging(set)
                else:
                    _style[tag] = set
            
        return _style

    @property
    def is_unbalanced(self):
        return not self.tagEnd or isinstance(self.tagEnd, XMLUnbalancedTag)
    
    def logical2physical(self, pos):
        return self.arg.logical2physical(pos) + self.tagBegin.length

    def physical2logical(self, pos):
        return clip(self.arg.physical2logical(pos - self.tagBegin.length), 0, len(self.text) - 1)
    
    def is_physically_valid(self, pos):
        if self.tagBegin.length <= pos < self.length - self.tagEnd.length:
            return self.arg.is_physically_valid(pos - self.tagBegin.length)
    
    def is_sibling(self, start_idx, end):
        if self.tagBegin.length <= start_idx < end <= self.length - self.tagEnd.length:
            start_idx -= self.tagBegin.length
            end -= self.tagBegin.length
            return self.arg.is_sibling(start_idx, end)

    def getPhysicalIndices(self, start_idx, end_idx):
        start_idx, end_idx = self.arg.getPhysicalIndices(start_idx, end_idx)
        
        physicalText = str(self.arg)
        _stop = end_idx
        #ignore white spaces to the end;
        while _stop < len(physicalText) and physicalText[_stop].isspace():
            _stop += 1
        
        if _stop == len(physicalText):
            if not start_idx:
                end_idx = _stop + self.tagEnd.length

        end_idx += self.tagBegin.length
        
        if start_idx:
            start_idx += self.tagBegin.length
            
        return start_idx, end_idx

    def enumerate(self):
        yield from self.ptr.enumerate()

    def has(self, cls):
        if isinstance(self, cls):
            return True
        return self.ptr.has(cls)

    def reduceToText(self):
        arg, tagBegin, tagEnd, parent = self.arg, self.tagBegin, self.tagEnd, self.parent
        assert tagEnd is None, "tagEnd == null"
        if parent.is_XMLArgs:
            index = parent.args.index(self)
            count = 1
            
            if arg.is_XMLArgs:
                args = arg.args
                for arg in args:
                    arg.parent = parent
                
                if args[0].is_XMLText:
                    args[0].start_idx = tagBegin.start_idx
                else:
                    args.insert(0, XMLText(tagBegin.reduceToText(), start_idx=tagBegin.start_idx, parent=parent))
                    
                if index and parent.args[index - 1].is_XMLText:
                    index -= 1
                    count += 1
                    args[0].start_idx = parent.args[index].start_idx
                    
            elif isinstance(arg, XMLCaret):
                arg = XMLText(tagBegin.reduceToText(), start_idx=tagBegin.start_idx, parent=parent)
                if index + 1 < len(parent.args) and parent.args[index + 1].is_XMLText:
                    count += 1
                    arg.end_idx = parent.args[index + 1].end_idx
                
                if index and parent.args[index - 1].is_XMLText:
                    index -= 1
                    count += 1
                    arg.start_idx = parent.args[index].start_idx
                
                args = [arg]
            else:
                arg.parent = parent
                if arg.is_XMLText:
                    if index + 1 > len(parent.args) and parent.args[index + 1].is_XMLText:
                        count += 1
                        arg.end_idx = parent.args[index + 1].end_idx
                    
                    if index and parent.args[index - 1].is_XMLText:
                        index -= 1
                        count += 1
                        arg.start_idx = parent.args[index].start_idx
                    else:
                        arg.start_idx = tagBegin.start_idx
                    args = [arg]
                else:
                    args = [XMLText(tagBegin.reduceToText(), start_idx=tagBegin.start_idx, parent=parent), arg]
                    if index and parent.args[index - 1].is_XMLText:
                        index -= 1
                        count += 1
                        args[0].start_idx = parent.args[index].start_idx
            splice(parent.args, index, count, *args)
        else:
            assert parent.is_XMLContainerTag
            if arg.is_XMLArgs:
                args = arg.args
                if args[0].is_XMLText:
                    args[0].start_idx = tagBegin.start_idx
                else:
                    args.insert(0, XMLText(tagBegin.reduceToText(), start_idx=tagBegin.start_idx, parent=arg))
            elif arg.is_XMLText:
                arg.start_idx = tagBegin.start_idx
            elif isinstance(arg, XMLCaret):
                arg = XMLText(tagBegin.reduceToText(), start_idx=tagBegin.start_idx)
            else:
                arg = XMLArgs([XMLText(tagBegin.reduceToText(), start_idx=tagBegin.start_idx), arg])
                
            arg.parent = parent
            parent.replace(self, arg)

    @property
    def html(self):
        return ''.join(arg.html for arg in self.args)

class XMLDocument(XMLArgs):
    def insert_backtick(self, caret, **kwargs):
        this = self.parent
        if (md := this.parent) and (md.is_MarkdownSPAN or md.is_MarkdownLI) and not self.has_newline() and (mdText := this.previousElementSibling) and mdText.is_MarkdownText and (m := re.search('(?<!`)`([^`]*)$', mdText.text)):
            MarkdownCODE = md.MarkdownCODE
            MarkdownText = mdText.__class__
            latter = mdText.text[-len(m[1]):] if m[1] else ''
            mdText.text = mdText.text[:-len(m[0])]
            if not mdText.text:
                mdText.remove()
            code = MarkdownCODE(
                MarkdownText(
                    latter + str(self), 
                    md.indent,
                    start_idx=self.start_idx - len(latter)
                ), 
                md.indent
            )
            this.parent.replace(this, code)
            return code
        else:
            return self.insert_token(caret, '`', **kwargs)

    def insert_gt(self, caret, **kwargs):
        return self.insert_token(caret, '>', **kwargs)

    def insert_token(self, caret, token, **kwargs):
        if isinstance(caret, XMLText):
            this = self.parent
            if md := this.parent:
                MarkdownText = md.MarkdownText
                new = MarkdownText(caret.text, md.indent, start_idx=caret.start_idx)
                new.text += token
                caret = new
                if len(self.args) > 1:
                    del self.args[-1]
                    new = [this, new]
                elif isinstance(md, md.MarkdownSPAN) and len(md.args) > 1 and isinstance(md.args[-2], MarkdownText):
                    del md.args[-1]
                    caret = md.args[-1]
                    caret.text += new.text
                    return caret
                md.replace(this, new)
                return caret
        return caret.push_token(token, **kwargs)

    def insert_right_bracket(self, caret, **kwargs):
        this = self.parent
        if (md := this.parent) and isinstance(md, md.MarkdownBracket):
            md.is_closed = True
            return md
        return self.insert_token(caret, ']', **kwargs)
    
    @property
    def html(self):
        return '\n'.join(arg.html for arg in self.args)

class XMLParser(AbstractParser):
    is_Paragraph = False
    is_token = True
    def __init__(self, parent=None, **kwargs):
        super().__init__(XMLCaret(**kwargs, start_idx=0))
        self.root = XMLDocument([self.caret], 0, self)
        self.parent = parent
        self.indent = 0

    @property
    def previousElementSibling(self):
        if i := self.parent.args.index(self) :
            return self.parent.args[i - 1]

    @property
    def start_idx(self):
        return self.root.start_idx

    @property
    def end_idx(self):
        return self.root.end_idx

    @property
    def html(self):
        return self.root.html

    def has_newline(self):
        return self.root.has_newline()

    @property
    def plainText(self):
        return str(self)
        
    def __str__(self):
        return str(self.root)

    def build(self, text):
        history = ''  # for debug purposes
        for start_idx, token in enumerate(text):
            try:
                self.parse(token, start_idx=start_idx)
            except Exception as e:
                print(e)
                traceback.print_exc()
                print(history)
            history += token
        start_idx = len(text)
        # self.parse("\n", start_idx=start_idx)
        self.parse('', start_idx=start_idx + 1)
        return self.root

    @classmethod
    def match_XMLTagBegin(cls, arg, tagName):
        return isinstance(arg, cls) and len(args := arg.root.args) == 1 and isinstance(tagBegin := args[0], XMLTagBegin) and tagBegin.tagName.text.lower() == tagName

    def find_path(self, *args):
        ...
    search_tagBegin = IndentedNode.search_tagBegin

def test():
    physicalText = "firstly,&nbsp;<div><b>this&nbsp;is&nbsp;<I>an&nbsp;<font color='red'><i>italic</i>&nbsp;<u>&lt;underline&gt;</u><mspace /></font>, simply put</b>,&nbsp;this&nbsp;is&nbsp;an&nbsp;italic&nbsp;text,&nbsp;</I>with&nbsp;something&emsp;<u>&lt;underlined&gt;</u>;</div>&ensp;<b>another&nbsp;bold&nbsp;text&nbsp;is&nbsp;followed.&nbsp;</b>At&nbsp;last,&nbsp;there&nbsp;a&nbsp;plain&nbsp;text."
    tree = XMLParser.instance.build(physicalText)
    print(tree)


if __name__ == '__main__':
    test()