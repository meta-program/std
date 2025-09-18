# to comply with the standards of java and mysql regex engine
# https://latex.codecogs.com/svg.image?a^2+b^2=c^2\qquad\tag*{Pythagoras}
import regex as re, traceback
from std import computed, array_splice
from std.parser.node import AbstractParser, Node, Closable, case
from std.parser.command import CommandParser, starred_commands
from std.parser.newline import NewLineParser

paired_commands = (
    r'\lvert', r'\rvert',
    r'\lceil', r"\rceil",
    r'\lfloor', r'\rfloor',
    r"\langle", r'\rangle',
)
self_group_operators = r"\big", r"\Big", r"\bigg", r"\Bigg"
group_operators = {
    r"\right": r"\left",
    r"\bigr": r"\bigl",
    r"\Bigr": r"\Bigl",
    r"\biggr": r"\biggl",
    r"\Biggr": r"\Biggl",
}
left_operators = group_operators.values()
right_operators = group_operators.keys()

spaces = r"\ ", r"\:", r"\,", r"\;", r"\!", r"\enspace", r"\thinspace", r"\negthinspace", r"\quad", r"\qquad", r"\displaystyle"
minus = '−–－'
input_priority = {
    '＋': 65,
    '+': 65,
    '-': 65,
    '×': 70,
    '*': 70,
    '÷' : 70,
    '/' : 70,
    r'\%' : 70,
    '=' : 50,
    '&=' : 50,
    '=&' : 50,
    '&=&' : 50,
    '≡': 50,
    '≈': 50,
    '!=' : 50,
    '≠' : 50,
    '&≠' : 50,
    '≠&' : 50,
    '&≠&' : 50,
    '<' : 50,
    '&<' : 50,
    '<&' : 50,
    '&<&' : 50,
    '>': 50,
    '&>': 50,
    '>&': 50,
    '&>&': 50,
    '≤' : 50,
    '&≤' : 50,
    '≤&' : 50,
    '&≤&' : 50,
    '≥' : 50,
    '&≥' : 50,
    '≥&' : 50,
    '&≥&' : 50,
    '^' : 80,
    '_' : 80,
    '∈' : 50,
    '∋' : 50,
    # Set Theory & Relations
    r"\in" : 50,
    r"\ni" : 50,
    r"\subset" : 50,
    r"\subseteq" : 50,
    r"\supset" : 50,
    r"\supseteq" : 50,
    r"\notin" : 50,
    r"\ne" : 50,
    r"\neq" : 50,
    r"\approx" : 50,
    r'\lt' : 50,
    r'\gt' : 50,
    r"\leq" : 50,
    r"\le" : 50,
    r"\geq" : 50,
    r"\ge" : 50,
    
    r"\mid" : 50,
    r"\nmid" : 50,
    r"\parallel" : 50,
    r"\nparallel" : 50,
    r"\perp" : 50,
    r"\implies" : 25,
    r"\rightarrow" : 25, # →
    r"\Rightarrow" : 23,
    r"\leftarrow": 19, # ←
    r"\Leftarrow": 19,
    r"\iff" : 20,
    r"\leftrightarrow" : 20,
    r"\Leftrightarrow" : 20,
    r"\mapsto" : 50,
    r"\circ" : 90,
    r"\cdot" : 70,
    r"\times" : 70,
    r"\mod" : 70,
    r"\bmod" : 70,
    r"\pmod" : 70,
    r"\cup" : 65,
    r"\cap" : 70,
    r"\setminus" : 70,
    # Extended Operators
    r"\subsetneq" : 50,
    r"\supsetneq" : 50,
    r"\triangle" : 50,
    r"\simeq" : 50,
    r"\approxeq" : 50,
    r"\cong" : 50,
    r"\to" : 50,
    r"\hookrightarrow" : 50,
    r"\twoheadrightarrow" : 50,
    r"\equiv" : 50,
    r"\sim" : 50,
    r"\land" : 35,
    r"\wedge" : 35,
    r"\lor" : 30,
    r"\vee" : 30,
    r"\vdash" : 50,
    r"\vDash" : 50,
    r"\doteq" : 50,
    r"\triangleq" : 50,
    r"\ll" : 50,
    r"\gg" : 50,
    r"\prec" : 50,
    r"\succ" : 50,
    r"\preceq" : 50,
    r"\succeq" : 50,
    r"\asymp" : 50,
    r"\propto" : 50,
    r"\bowtie" : 50,
    r"\div" : 70,
    r"\oplus" : 70,
    r"\otimes" : 70,
    r"\odot" : 70,
    r"\oslash" : 50,
    r"\ast" : 70,
    r"\star" : 70,
    r"\dagger" : 50,
    r"\ddagger" : 50,
    r"\nsubset" : 50,
    r"\nsubseteq" : 50,
    r"\nsupset" : 50,
    r"\nsupseteq" : 50,
    "&": 25,
    r"\\": 5,
}
for o in minus:
    input_priority[o] = 65

right_associative_operators = (
    '^',
    '=', '≡', '≈', '≠'
    '<', '>', '≤', '≥',
    r'\implies',
    r'\rightarrow',
    r'\Rightarrow',
    r'\mapsto',
)

big_operator_priority = {
    r"\sum" : 67,
    r"\prod"  : 67,
    r"\coprod"  : 67,
    r"\int"  : 67,
    r"\oint"  : 67,
    r"\bigcap"  : 60,
    r"\bigcup"  : 60,
    r"\bigsqcup"  : 60,
    r"\bigvee"  : 50,
    r"\bigwedge"  : 50,
    r"\biguplus"  : 67,
    r"\iint" : 67,
    r"\iiint" : 67,
    r"\iiiint" : 67,
    r"\idotsint" : 67,
    r"\bigoplus" : 67,
    r"\bigotimes" : 67,
    r"\bigodot" : 67,
    r"\nabla": 67,
    r"\partial": 67,
}

unary_math_functions = (
    r"\arg",
    r"\sin", r"\sinh",
    r"\cos", r"\cosh",
    r"\tan", r"\tanh",
    r"\cot", r"\coth",
    r"\sec",
    r"\csc",
    r"\arcsin",
    r"\arccos",
    r"\arctan",
    r"\exp",
    r"\Re", r"\Im",
    r"\lnot",
    r"\surd",
)

frac = r'\frac', r'\dfrac', r'\tfrac'

class LatexNode(Node):
    is_LatexCaret = False
    is_LatexText = False
    is_LatexBinary = False
    is_LatexArgs = False

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)

    @case(' ')
    def case(self, **kwargs):
        return self.parent.insert_space(self, **kwargs)

    @case("\n")
    def case(self, **kwargs):
        return NewLineParser(self, next=True, **kwargs)

    @case("\\")
    def case(self, **kwargs):
        return CommandParser(self, **kwargs)

    # infix operator
    @case(*input_priority.keys() - {'+', '＋', '-', '<', '>', '&', r'\\', *minus})
    def case(self, **kwargs):
        return self.parent.insert_infix(self, operator=self.key, **kwargs)

    # infix operators that can possibly be unary prefix operators
    @case('+', '＋', '-', *minus)
    def case(self, **kwargs):
        if isinstance(self, (LatexCaret, LatexLeft)) or isinstance(self, LatexCommand) and not isinstance(self.parent, (LatexArgsNullSeparated, LatexArgsSpaceSeparated)) and self.text in spaces:
            return self.parent.insert_unary(self, self.unary_operator[self.key], **kwargs)
        else:
            return self.parent.insert_infix(self, operator=self.key, **kwargs)

    @case('<')
    def case(self, **kwargs):
        return self.parent.insert_lt(self, **kwargs)

    @case('>')
    def case(self, **kwargs):
        return self.parent.insert_gt(self, **kwargs)

    @case('&')
    def case(self, **kwargs):
        return self.parent.insert_infix(self, operator='&', **kwargs)

    @case(r"\\")
    def case(self, **kwargs):
        return self.parent.insert_infix(self, operator=r"\\", **kwargs)

    @case(r"\tag", r"\tag*")
    def case(self, **kwargs):
        return self.parent.insert_tag(self, self.key, **kwargs)

    @case(
        r"\alpha", r"\beta", r"\gamma", r"\delta", r"\epsilon", r"\zeta", r"\eta", r"\theta", r"\iota", r"\kappa", r"\lambda", r"\mu", r"\nu", r"\xi", r"\omicron", r"\pi", r"\rho", r"\sigma", r"\tau", r"\upsilon", r"\phi", r"\chi", r"\psi", r"\omega",
        r"\Gamma", r"\Delta", r"\Theta", r"\Lambda", r"\Xi", r"\Pi", r"\Sigma", r"\Upsilon", r"\Phi", r"\Psi", r"\Omega",
        r"\aleph", r"\angle",
        r"\infty", r"\emptyset",
        r"\ldots", r"\cdots", r"\vdots", r"\ddots",
        *paired_commands,
        *spaces, r"\hline",
    )
    def case(self, **kwargs):
        return self.parent.insert_command(self, self.key, **kwargs)

    # unary operator
    @computed
    def unary_operator(cls):
        unary_operator = {
            r"\not" : LatexNot,
            r"\begin" : LatexBegin,
            r"\end" : LatexEnd,
            r"\mathop" : LatexMathOp,
            "-" : lambda arg : LatexUnaryOperator(LatexText('-'), arg),
            "+" : lambda arg : LatexUnaryOperator(LatexText('+'), arg),
            r"\pm": lambda arg : LatexUnaryOperator(LatexCommand(r"\pm"), arg),
            r"\mp": lambda arg : LatexUnaryOperator(LatexCommand(r"\mp"), arg),
        }
        for o in minus:
            unary_operator[o] = lambda arg : LatexUnaryOperator(LatexText(o), arg),
        return unary_operator

    @case(r"\not", r"\begin", r"\end", r"\mathop")
    def case(self, **kwargs):
        return self.parent.insert_unary(self, self.unary_operator[self.key], **kwargs)

    # group operator
    @computed
    def group_operator(cls):
        return {op : LatexLeft for op in left_operators} | {op : LatexRight for op in right_operators}

    @case(*left_operators, *right_operators)
    def case(self, **kwargs):
        key = self.key
        return self.parent.insert_unary(self, lambda caret : self.group_operator[key]([LatexCommand(key), caret]), **kwargs)

    @case(*self_group_operators)
    def case(self, **kwargs):
        key = self.key
        return self.parent.insert_unary(self, lambda caret : LatexLeft([LatexCommand(key), caret]), **kwargs)

    @case(r"\sqrt")
    def case(self, **kwargs):
        return self.parent.insert_optional_unary_function(self, r"\sqrt", **kwargs)

    @case(
        r"\boxed", 
        r"\text", r"\textbf",
        r"\overline", r"\underline", 
        r"\overbrace", r"\underbrace",
        r"\acute",
        r"\substack",
        r"\mathbf", r"\mathrm", r"\mathit", r"\mathcal", r"\mathsf", r"\mathtt", r"\mathbb", r"\mathfrak", r"\mathscr", 
        r"\boldsymbol", r"\pmb", 
        r"\dot", r"\ddot", r"\dddot", r"\ddddot", r"\vec", r"\breve", r"\bar", r"\tilde",
        r"\tiny", r"\small", r"\normalsize",
        r"\large", r"\Large", r"\LARGE",
        r"\huge", r"\Huge",
        r"\phantom", r"\hphantom", r"\vphantom",
        r"\mspace", r"\hspace",
        *unary_math_functions,
    )
    def case(self, **kwargs):
        return self.parent.insert_unary_function(self, self.key, **kwargs)

    # binary operator
    @case(
        *frac,
        r"\binom", 
        r"\stackrel", 
        r"\color", 
        r"\textcolor", 
        r"\overset", 
        r"\underset",
        r"\operatorname",
        r"\rule", # \rule{10em}{1pt}
    )
    def case(self, **kwargs):
        return self.parent.insert_binary(self, self.key, **kwargs)

    # big operator
    @case(*big_operator_priority.keys())
    def case(self, **kwargs):
        return self.parent.insert_big_operator(self, self.key, **kwargs)

    #  operators taking limits
    @case(
        r"\max", 
        r"\min", 
        r"\lim", 
        r"\sup", 
        r"\inf", 
        r"\limsup", 
        r"\liminf", 
        r"\det", 
        r"\Pr"
    )
    def case(self, **kwargs):
        return self.parent.insert_big_operator_via_command(self, self.key, **kwargs)

    # universal/existential quantifier operator
    @case(
        r"\forall", 
        r"\exists", 
        r"\nexists",
    )
    def case(self, **kwargs):
        return self.parent.insert_quantifier(self, self.key, **kwargs)

    # limited modifier
    @case(
        r"\limits", 
        r"\nolimits", 
    )
    def case(self, **kwargs):
        return self.parent.insert_limit_modifier(self, self.key, **kwargs)

    # delimiters for \left \right 
    @case('.', '|', '(', ')', '[', ']')
    def case(self, **kwargs):
        return self.parent.insert_delimiter(self, self.key, **kwargs)

    @case('{')
    def case(self, **kwargs):
        return self.parent.insert_left_brace(self, **kwargs)

    @case('}')
    def case(self, **kwargs):
        return self.push_right_brace(**kwargs)
    
    @case(',')
    def case(self, **kwargs):
        return self.parent.insert_comma(self, **kwargs)

    @case(';')
    def case(self, **kwargs):
        return self.parent.insert_semicolon(self, **kwargs)

    @case(*(str(d) for d in range(10)))
    def case(self, **kwargs):
        return self.parent.insert_digit(self, self.key, **kwargs)

    @case
    def case(self, **kwargs):
        return self.parent.insert_token(self, self.key, **kwargs)

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if isinstance(caret, LatexCaret):
            caret.start_idx = kwargs['start_idx'] + newline_count + indent
        return caret

    def insert_space(self, caret, **kwargs):
        if isinstance(caret, LatexCaret):
            caret.start_idx = kwargs['start_idx']
        return caret

    def insert_unary(self, this, func, **kwargs):
        if isinstance(this, LatexCaret):
            caret = this
            new = func(caret)
        else:
            caret = LatexCaret(**kwargs)
            new = func(caret)
            new = LatexArgsSpaceSeparated([this, new])
        self.replace(this, new)
        return caret

    def insert_left_brace(self, caret, **kwargs):
        if isinstance(self.parent, LatexExprWithLimits) and self is self.parent.args[0] and len(self.parent.args) == 1 and isinstance(caret, LatexBrace):
            caret = LatexCaret(**kwargs)
            self.parent.push(caret)
        return caret.push_left_brace(**kwargs)

    def push_right_brace(self, **kwargs):
        if self.parent:
            return self.parent.push_right_brace(**kwargs)

    def insert_comma(self, caret, **kwargs):
        if isinstance(caret, LatexNumber):
            return caret.push_token(',', **kwargs)
        if self.parent:
            return self.parent.insert_comma(self, **kwargs)

    def insert_semicolon(self, caret, **kwargs):
        if self.parent:
            return self.parent.insert_semicolon(self, **kwargs)

    def push_left_brace(self, **kwargs):
        caret = LatexCaret(**kwargs)
        self.parent.replace(self, LatexArgsNullSeparated([self, LatexBrace(caret)]))
        return caret

    def push_token(self, word, **kwargs):
        if word:
            new = LatexText(word, **kwargs)
            self.parent.replace(self, LatexArgsSpaceSeparated([self, new]))
            return new
        return self

    def push_big_operator_via_command(self, operator, **kwargs):
        return self.parent.push_big_operator_via_command(operator, **kwargs)

    def insert_big_operator_via_command(self, caret, operator, **kwargs):
        return caret.push_big_operator_via_command(operator, **kwargs)

    def push_quantifier(self, operator, **kwargs):
        return self.parent.push_quantifier(operator, **kwargs)

    def insert_quantifier(self, caret, operator, **kwargs):
        return caret.push_quantifier(operator, **kwargs)

    def push_big_operator(self, operator, **kwargs):
        if isinstance(self.parent, LatexBigOperator):
            return LatexLeft.push_big_operator(self, operator, **kwargs)
        return self.parent.push_big_operator(operator, **kwargs)

    def insert_big_operator(self, caret, operator, **kwargs):
        return caret.push_big_operator(operator, **kwargs)

class LatexCaret(LatexNode):
    is_LatexCaret = True

    def push_token(self, word, **kwargs):
        new = LatexText(word, **kwargs)
        self.parent.replace(self, new)
        return new

    def strFormat(self):
        return ''

    def push_left_brace(self, **kwargs):
        self.parent.replace(self, LatexBrace(self))
        return self

    def push_big_operator_via_command(self, operator, **kwargs):
        caret = LatexCommand(operator, **kwargs)
        self.parent.replace(self, LatexBigOperatorViaCommand([caret]))
        return caret

    def push_big_operator(self, operator, **kwargs):
        caret = LatexCommand(operator, **kwargs)
        self.parent.replace(self, LatexBigOperator([caret]))
        return caret

    def push_quantifier(self, operator, **kwargs):
        caret = LatexCommand(operator, **kwargs)
        self.parent.replace(self, LatexQuantifier([caret]))
        return caret

    @property
    def text(self):
        return ''

class LatexText(LatexNode):
    is_LatexText = True
    def __init__(self, text, parent=None, **kwargs):
        super().__init__(text=text, parent=parent, **kwargs)

    def strFormat(self):
        return self.text

    def push_token(self, word, **kwargs):
        if kwargs['start_idx'] == self.end_idx:
            if word.isalpha() and self.text.isalpha():
                self.text += word
                return self
            new = LatexText(word, **kwargs)
            self.parent.replace(self, LatexArgsNullSeparated([self, new]))
            return new
        return super().push_token(word, **kwargs)

    @classmethod
    def match_left_parenthesis(cls, arg):
        return isinstance(arg, cls) and arg.text == '(' and not (isinstance(parent := arg.parent, LatexParenthesisGroup) and isinstance(right := parent.args[-1], LatexText) and right.text == ')')

    @classmethod
    def match_left_bracket(cls, arg):
        return isinstance(arg, cls) and arg.text == '[' and not (isinstance(parent := arg.parent, LatexBracketGroup) and isinstance(right := parent.args[-1], LatexText) and right.text == ']')

    def push_delimiter(self, delimiter, **kwargs):
        if delimiter == ')':
            left = self.search_tagBegin(LatexText.match_left_parenthesis, LatexParenthesisGroup)
            assert isinstance(left, LatexText) and left.text == '(', r"unmatch ) command detected!"
            assert left.parent is self.parent
            return self.parent.unwrapped()
        if delimiter == ']':
            left = self.search_tagBegin(LatexText.match_left_bracket, LatexBracketGroup)
            assert isinstance(left, LatexText) and left.text == '[', r"unmatch ] command detected!"
            assert left.parent is self.parent
            return self.parent.unwrapped()

class LatexCommand(LatexNode):
    is_LatexCommand = True
    def __init__(self, text, parent=None, **kwargs):
        super().__init__(text=text, parent=parent, **kwargs)

    def strFormat(self):
        return self.text

class LatexNumber(LatexNode):
    def __init__(self, text, parent=None, **kwargs):
        super().__init__(text=text, parent=parent, **kwargs)

    def strFormat(self):
        return self.text

    def push_token(self, word, **kwargs):
        if word.isdigit():
            self.text += word
            return self
        new = LatexText(word, **kwargs)
        if kwargs['start_idx'] == self.end_idx:
            if isinstance(parent := self.parent, LatexArgsNullSeparated):
                parent.push(new)
            else:
                parent.replace(self, LatexArgsNullSeparated([self, new]))
        else:
            if isinstance(parent := self.parent, LatexArgsSpaceSeparated):
                parent.push(new)
            else:
                parent.replace(self, LatexArgsSpaceSeparated([self, new]))
        return new

    def push_big_operator(self, operator, **kwargs):
        caret = LatexCommand(operator, **kwargs)
        self.parent.replace(self, LatexArgsSpaceSeparated([self, LatexBigOperator([caret])]))
        return caret

class LatexArgs(LatexNode):
    is_LatexArgs = True
    def __init__(self, args, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.args = args
        for arg in args:
            arg.parent = self

    def insert_token(self, caret, word, **kwargs):
        return caret.push_token(word, **kwargs)

    def strFormat(self):
        return ''.join(['%s'] * len(self.args))

    def insert_digit(self, caret, digit, **kwargs):
        if isinstance(caret, LatexCaret):
            new = LatexNumber(digit, **kwargs)
            self.replace(caret, new)
        elif isinstance(caret, LatexNumber):
            caret.text += digit
            return caret
        else:
            new = LatexNumber(digit, **kwargs)
            if isinstance(self, (LatexArgsNullSeparated, LatexArgsSpaceSeparated)):
                self.push(new)
            else:
                self.replace(
                    caret, 
                    (LatexArgsSpaceSeparated if isinstance(caret, LatexCommand) else LatexArgsNullSeparated)([caret, new])
                )
        return new

    def insert_infix(self, caret, operator, **kwargs):
        if input_priority[operator] >= self.input_priority if operator in right_associative_operators else input_priority[operator] > self.input_priority:
            op = LatexCommand(operator, **kwargs)
            new = LatexCaret(**kwargs)
            self.replace(caret, LatexInfix(caret, op, new))
            return new
        return self.parent.insert_infix(self, operator, **kwargs)

    def insert_tag(self, caret, operator, **kwargs):
        return self.parent.insert_tag(self, operator, **kwargs)

    def insert_unary_function(self, this, func, **kwargs):
        if isinstance(this, LatexCaret):
            caret = this
            new = LatexUnaryFunction(LatexCommand(func, **kwargs), this)
        else:
            caret = LatexCaret(**kwargs)
            new = LatexArgsSpaceSeparated([this, LatexUnaryFunction(LatexCommand(func, **kwargs), caret)])
        self.replace(this, new)
        return caret

    def insert_optional_unary_function(self, this, func, **kwargs):
        if isinstance(this, LatexCaret):
            caret = this
            new = LatexOptionalUnaryFunction(LatexCommand(func, **kwargs), this)
        else:
            caret = LatexCaret(**kwargs)
            new = LatexArgsSpaceSeparated([this, LatexOptionalUnaryFunction(LatexCommand(func, **kwargs), caret)])
        self.replace(this, new)
        return caret

    def insert_binary(self, this, operator, **kwargs):
        operator = LatexCommand(operator, **kwargs)
        if isinstance(this, LatexCaret):
            caret = this
            new = LatexBinary([operator, caret])
        else:
            caret = LatexCaret(**kwargs)
            new = LatexBinary([operator, caret])
            new = LatexArgsSpaceSeparated([this, new])
        self.replace(this, new)
        return caret

    def insert_command(self, caret, command, **kwargs):
        new = LatexCommand(command, **kwargs)
        if isinstance(caret, LatexCaret):
            self.replace(caret, new)
        elif isinstance(caret, LatexArgsNullSeparated):
            caret.push(new)
        else:
            self.replace(caret, LatexArgsNullSeparated([caret, new]))
        return new

    def insert_lt(self, caret, **kwargs):
        return self.insert_infix(caret, '<', **kwargs)

    def insert_gt(self, caret, **kwargs):
        return self.insert_infix(caret, '>', **kwargs)

    def insert_dot(self, caret, delimiter, **kwargs):
        if delimiter == '.' and isinstance(caret, LatexNumber) and kwargs['start_idx'] == caret.end_idx:
            new = LatexCaret(**kwargs)
            self.replace(caret, LatexFloat(caret, LatexText(delimiter, **kwargs), new))
            return new

    def push_expr_with_limits(self, cls, operator, **kwargs):
        caret = LatexCommand(operator, **kwargs)
        if isinstance(self.parent, LatexArgsNullSeparated):
            self.parent.push(caret)
        else:
            self.parent.replace(self, LatexArgsNullSeparated([self, cls([caret])]))
        return caret

class LatexFloat(LatexArgs):
    def __init__(self, integer, dot, fraction, parent=None, **kwargs):
        super().__init__(args=[integer, dot, fraction], parent=parent, **kwargs)

    def strFormat(self):
        return "%s%s%s"

    @property
    def integer(self):
        return self.args[0]
    
    @integer.setter
    def integer(self, val):
        self.args[0] = val

    def dot(self):
        return self.args[1]
    
    @property
    def fraction(self):
        return self.args[2]
    
    @fraction.setter
    def fraction(self, val):
        self.args[2] = val
        val.parent = self

    def insert_token(self, caret, word, **kwargs):
        if word.isdigit():
            if isinstance(caret, LatexCaret):
                caret = LatexNumber(word, **kwargs)
                self.fraction = caret
            elif isinstance(caret, LatexNumber):
                caret.text += word
            else:
                print(f"Unexpected caret type: {type(caret)}")
            return caret
        return self.parent.insert_token(self, word, **kwargs)

    push_big_operator = LatexNumber.push_big_operator

class LatexUnary(LatexArgs):
    is_LatexUnary = True
    def __init__(self, arg, parent=None):
        super().__init__([arg], parent)

    @property
    def arg(self):
        return self.args[0]

    @arg.setter
    def arg(self, arg):
        self.args[0] = arg
        arg.parent = self

class LatexPairedGroup(LatexUnary, Closable):
    input_priority = 0

class LatexBrace(LatexPairedGroup):
    def strFormat(self):
        if self.is_closed:
            return r"{%s}"
        return r"{%s"

    def push_right_brace(self, **kwargs):
        if self.is_closed:
            return self.parent.push_right_brace(**kwargs)
        self.is_closed = True
        if isinstance(self.parent, LatexEnd):
            return self.parent.close()
        return self

    def insert_comma(self, caret, **kwargs):
        comma = LatexText(',', **kwargs)
        new = LatexCaret(**kwargs)
        if isinstance(caret, LatexArgsNullSeparated):
            self.arg.push(comma)
            self.arg.push(new)
        else:
            self.arg = LatexArgsNullSeparated([caret, comma, new])
        return new

    def insert_semicolon(self, caret, **kwargs):
        comma = LatexText(';', **kwargs)
        new = LatexCaret(**kwargs)
        if isinstance(caret, LatexArgsNullSeparated):
            self.arg.push(comma)
            self.arg.push(new)
        else:
            self.arg = LatexArgsNullSeparated([caret, comma, new])
        return new

    def insert_delimiter(self, caret, delimiter, **kwargs):
        if new := self.insert_dot(caret, delimiter, **kwargs):
            return new
        new = LatexText(delimiter, **kwargs)
        if isinstance(self.arg, LatexArgsNullSeparated):
            self.arg.push(new)
        elif isinstance(caret, LatexCaret):
            self.replace(caret, new)
        else:
            self.replace(caret, LatexArgsNullSeparated([caret, new]))
        return new

    def insert_big_operator(self, caret, operator, **kwargs):
        if isinstance(caret, LatexCaret):
            return caret.push_big_operator(operator, **kwargs)
        caret = LatexCommand(operator, **kwargs)
        new = LatexBigOperator([caret])
        if isinstance(self.arg, LatexArgsNullSeparated):
            self.arg.push(new)
        else:
            self.arg = LatexArgsNullSeparated([self.arg, new])
        return caret

    def insert_quantifier(self, caret, operator, **kwargs):
        if isinstance(caret, LatexCaret):
            return caret.push_quantifier(operator, **kwargs)
        caret = LatexCommand(operator, **kwargs)
        new = LatexQuantifier([caret])
        if isinstance(self.arg, LatexArgsNullSeparated):
            self.arg.push(new)
        else:
            self.arg = LatexArgsNullSeparated([self.arg, new])
        return caret

    def insert_big_operator_via_command(self, caret, operator, **kwargs):
        if isinstance(caret, LatexCaret):
            return caret.push_big_operator_via_command(operator, **kwargs)
        caret = LatexCommand(operator, **kwargs)
        new = LatexBigOperatorViaCommand([caret])
        if isinstance(self.arg, LatexArgsNullSeparated):
            self.arg.push(new)
        else:
            self.arg = LatexArgsNullSeparated([self.arg, new])
        return caret

    def insert_infix(self, caret, operator, **kwargs):
        if operator == '*' and isinstance(caret, LatexText) and caret.text in starred_commands and kwargs['start_idx'] == caret.end_idx and isinstance(self.parent, LatexBeginEnd):
            caret.text += '*'
            return caret
        return super().insert_infix(caret, operator, **kwargs)

class LatexBracketGroup(LatexArgs):
    @property
    def left(self):
        return self.args[0]
    
    @property
    def right(self):
        return self.args[-1]
    
    @property
    def children(self):
        return self.args[1:-1]

    def unwrapped(self):
        if isinstance(ancestor := self.parent, (LatexArgsNullSeparated, LatexArgsSpaceSeparated)) and len(ancestor.args) == 1:
            ancestor.parent.replace(ancestor, ancestor.args[0])
        return self

    def insert_delimiter(self, caret, delimiter, **kwargs):
        if delimiter == ']' and not (isinstance(punct := self.args[-1], LatexText) and punct.text == ']'):
            self.push(LatexText(']', **kwargs))
            return self
        return self.parent.insert_delimiter(self, delimiter, **kwargs)

class LatexLeftRight(LatexArgs):
    paired_delimiters = (
        '<', '>',
        '(', ')',
        '[', ']',
        r'\{', r'\}',
        *paired_commands
    )
    single_delimiters = (
        '.',
        '|',
        r'\|',
        r'\\',
        '/',
        r'\uparrow',
        r'\Uparrow',
        r'\downarrow',
        r'\Downarrow',
        r'\updownarrow',
        r"\Updownarrow",
    )

    @computed
    def delimiters(cls):
        return cls.paired_delimiters + cls.single_delimiters

    @computed
    def left_delimiters(cls):
        return cls.paired_delimiters[::2]
    
    @computed
    def right_delimiters(cls):
        return cls.paired_delimiters[1::2]

    @property
    def operator(self):
        return self.args[0]

    def insert_unary(self, this, func, **kwargs):
        this = self
        self = self.parent
        parent = this.parent
        caret = LatexCaret(**kwargs)
        new = func(caret)
        new = LatexArgsNullSeparated([this, new])
        parent.replace(this, new)
        return caret

    def insert_delimiter(self, caret, delimiter, **kwargs):
        assert isinstance(caret, LatexCaret)
        assert delimiter in self.delimiters
        new = LatexText(delimiter, **kwargs)
        self.replace(caret, new)
        return self

    def insert_lt(self, caret, **kwargs):
        assert isinstance(caret, LatexCaret)
        new = LatexText('<', **kwargs)
        self.replace(caret, new)
        return self

    def insert_gt(self, caret, **kwargs):
        assert isinstance(caret, LatexCaret)
        new = LatexText('>', **kwargs)
        self.replace(caret, new)
        return self

    def insert_command(self, caret, command, **kwargs):
        assert isinstance(caret, LatexCaret)
        assert command in self.delimiters
        new = LatexCommand(command, **kwargs)
        self.replace(caret, new)
        return self

    def insert_left_brace(self, caret, **kwargs):
        if isinstance(self.parent, LatexArgsNullSeparated):
            caret = LatexCaret(**kwargs)
            self.parent.push(LatexBrace(caret))
            return caret
        return caret.push_left_brace(**kwargs)

class LatexLeft(LatexLeftRight):
    is_LatexLeft = True

    def push_big_operator(self, operator, **kwargs):
        return self.push_expr_with_limits(LatexBigOperator, operator, **kwargs)

    def push_big_operator_via_command(self, operator, **kwargs):
        return self.push_expr_with_limits(LatexBigOperatorViaCommand, operator, **kwargs)

    def push_quantifier(self, operator, **kwargs):
        return self.push_expr_with_limits(LatexQuantifier, operator, **kwargs)

    def insert_delimiter(self, caret, delimiter, **kwargs):
        if delimiter in self.right_delimiters:
            right = LatexRight(self.args)
            self.parent.replace(self, right)
            return right.insert_delimiter(caret, delimiter, **kwargs)
        return super().insert_delimiter(caret, delimiter, **kwargs)

class LatexRight(LatexLeftRight):
    is_LatexRight = True

    @property
    def reversed_operator(self):
        op = self.operator.text
        return group_operators.get(op, op)

    @property
    def match_LatexLeft(self):
        reversed_operator = self.reversed_operator
        return lambda arg: isinstance(arg, LatexLeft) and arg.operator.text == reversed_operator and not (isinstance(parent := arg.parent, LatexSizingGroup) and isinstance(parent.args[-1], LatexRight))

    def insert_delimiter(self, caret, delimiter, **kwargs):
        super().insert_delimiter(caret, delimiter, **kwargs)
        left = self.search_tagBegin(self.match_LatexLeft, LatexSizingGroup)
        assert isinstance(left, LatexLeft), fr"unmatch {self.operator} command detected!"
        assert left.parent is self.parent
        return self.parent.unwrapped()

    def insert_lt(self, caret, **kwargs):
        super().insert_lt(caret, **kwargs)
        left = self.search_tagBegin(self.match_LatexLeft, LatexSizingGroup)
        assert isinstance(left, LatexLeft), fr"unmatch {self.operator} command detected!"
        assert left.parent is self.parent
        return self.parent

    def insert_gt(self, caret, **kwargs):
        super().insert_gt(caret, **kwargs)
        left = self.search_tagBegin(self.match_LatexLeft, LatexSizingGroup)
        assert isinstance(left, LatexLeft), fr"unmatch {self.operator} command detected!"
        assert left.parent is self.parent
        return self.parent

    def insert_command(self, caret, command, **kwargs):
        super().insert_command(caret, command, **kwargs)
        left = self.search_tagBegin(self.match_LatexLeft, LatexSizingGroup)
        assert isinstance(left, LatexLeft), fr"unmatch {self.operator} command detected!"
        assert left.parent is self.parent
        return self.parent.unwrapped()

class LatexBeginEnd(LatexUnary):
    environments = (
        # Basic document structure
        "document", "titlepage", "abstract",
        # Math environments (amsmath)
        "equation", "align", "gather", "multline", "flalign", "alignat", "cases", "matrix", "pmatrix", "bmatrix", "Bmatrix", "vmatrix", "Vmatrix",
        # Lists
        "itemize", "enumerate", "description",
        # Theorem-like environments (amsthm)
        "theorem", "lemma", "proposition", "corollary", "definition", "remark", "example", "proof",
        # Tables and arrays
        "tabular", "tabbing", "array",
        # Figures and captions
        "figure", "table",
        # Code and text
        "verbatim", "lstlisting", "alltt",
        # Formatting
        "center", "flushleft", "flushright", "minipage", "quote", "quotation",
        # Beamer/presentation
        "frame", "columns", "column",
        # Graphics
        "tikzpicture", "picture",
        # Misc
        "appendix", "scriptsize", "footnotesize",
        # Poetic or structured text
        'verse',         # For poems or structured stanzas
        # Math environments (some from amsmath, some deprecated)
        'split',         # Used inside equation for multi-line alignment
        'aligned',       # Inline version of align, used inside math mode
        'gathered',      # Inline version of gather
        'eqnarray',      # Obsolete math alignment (use align instead)
        'displaymath',   # Equivalent to \[ ... \], displays math (deprecated)
        # List-related
        'list',          # Low-level list environment
        'trivlist',      # Base list environment used internally
        # Document structures
        'letter',        # Letter document format
        'thebibliography', # Bibliography formatting
        'theindex',      # Index formatting
    )
    def insert_unary(self, this, func, **kwargs):
        this = self
        self = self.parent
        parent = this.parent
        caret = LatexCaret(**kwargs)
        new = func(caret)
        new = LatexArgsNullSeparated([this, new])
        parent.replace(this, new)
        return caret

    def insert_command(self, caret, command, **kwargs):
        assert isinstance(caret, LatexCaret)
        assert command in self.delimiters
        new = LatexCommand(command, **kwargs)
        self.replace(caret, new)
        return self

class LatexBegin(LatexBeginEnd):
    def strFormat(self):
        return r"\begin%s"

    @classmethod
    def match_LatexBegin(cls, arg):
        return isinstance(arg, cls) and not (isinstance(parent := arg.parent, LatexEnvironment) and isinstance(parent.args[-1], LatexEnd))

    def insert_left_brace(self, caret, **kwargs):
        if isinstance(caret, LatexCaret):
            self.replace(caret, LatexBrace(caret))
            return caret
        return self.parent.insert_left_brace(self, **kwargs)

    def insert_digit(self, caret, digit, **kwargs):
        if isinstance(caret, (LatexCaret, LatexNumber)):
            return super().insert_digit(caret, digit, **kwargs)
        return self.parent.insert_digit(self, digit, **kwargs)

    def insert_unary_function(self, this, func, **kwargs):
        return self.parent.insert_unary_function(self, func, **kwargs)

    def insert_infix(self, caret, operator, **kwargs):
        caret = LatexCaret(**kwargs)
        op = LatexCommand(operator, **kwargs)
        new = LatexCaret(**kwargs)
        self.parent.replace(self, LatexArgsSpaceSeparated([self, LatexInfix(caret, op, new)]))
        return new

class LatexEnd(LatexBeginEnd):
    def strFormat(self):
        return r"\end%s"

    def close(self, **kwargs):
        begin = self.search_tagBegin(LatexBegin.match_LatexBegin, LatexEnvironment)
        assert isinstance(begin, LatexBegin), r"unmatch \begin command detected!"
        assert begin.parent is self.parent
        return self.parent.unwrapped()

class LatexMathOp(LatexUnary):
    def strFormat(self):
        return r"\mathop%s"

class LatexSizingGroup(LatexArgs):
    @property
    def left(self):
        return self.args[0]
    
    @property
    def right(self):
        return self.args[-1]
    
    @property
    def children(self):
        return self.args[1:-1]

    def unwrapped(self):
        if isinstance(ancestor := self.parent, (LatexArgsNullSeparated, LatexArgsSpaceSeparated)) and len(ancestor.args) == 1:
            ancestor.parent.replace(ancestor, ancestor.args[0])
        return self

    push_big_operator = LatexLeft.push_big_operator
    push_big_operator_via_command = LatexLeft.push_big_operator_via_command

class LatexEnvironment(LatexArgs):
    @property
    def begin(self):
        return self.args[0]
    
    @property
    def end(self):
        return self.args[-1]
    
    @property
    def children(self):
        return self.args[1:-1]

    unwrapped = LatexSizingGroup.unwrapped

class LatexParenthesisGroup(LatexArgs):
    @property
    def left(self):
        return self.args[0]
    
    @property
    def right(self):
        return self.args[-1]
    
    @property
    def children(self):
        return self.args[1:-1]

    def unwrapped(self):
        if isinstance(ancestor := self.parent, (LatexArgsNullSeparated, LatexArgsSpaceSeparated)) and len(ancestor.args) == 1:
            ancestor.parent.replace(ancestor, ancestor.args[0])
        return self

    push_big_operator = LatexLeft.push_big_operator
    push_big_operator_via_command = LatexLeft.push_big_operator_via_command

class LatexNot(LatexUnary):
    input_priority = 40
    def strFormat(self):
        return r"\not%s"

    def insert_infix(self, caret, operator, **kwargs):
        assert isinstance(caret, LatexCaret)
        operator = LatexCommand(operator, **kwargs)
        self.replace(caret, operator)
        self = self.parent
        lhs, op = array_splice(self.args, -2, 2, [])
        new = LatexCaret(**kwargs)
        self.push(LatexInfix(lhs, op, new))
        if len(self.args) == 1:
            self.parent.replace(self, self.args[0])
        return new

class LatexUnaryFunction(LatexArgs):
    def __init__(self, operator, arg, parent=None, **kwargs):
        super().__init__([operator, arg], parent=parent, **kwargs)

    @property
    def input_priority(self):
        return 72

    @property
    def operator(self):
        return self.args[0]
    
    @property
    def arg(self):
        return self.args[1]

    def insert_delimiter(self, caret, delimiter, **kwargs):
        return self.parent.insert_delimiter(self, delimiter, **kwargs)

class LatexOptionalUnaryFunction(LatexArgs):
    def __init__(self, operator, arg, parent=None, **kwargs):
        super().__init__([operator, arg], parent=parent, **kwargs)

    @property
    def input_priority(self):
        return 72

    @property
    def operator(self):
        return self.args[0]
    
    @property
    def optional_arg(self):
        if len(self.args) == 3:
            return self.args[1]

    @property
    def arg(self):
        return self.args[-1]

    def insert_delimiter(self, caret, delimiter, **kwargs):
        if isinstance(caret, LatexCaret) and len(self.args) == 2 and delimiter == '[':
            self.replace(caret, LatexBracketGroup([LatexText('[', **kwargs), caret]))
            return caret
        return self.parent.insert_delimiter(self, delimiter, **kwargs)

    def insert_left_brace(self, caret, **kwargs):
        if len(self.args) == 2:
            if isinstance(caret, LatexBracketGroup):
                caret = LatexCaret(**kwargs)
                self.push(LatexBrace(caret))
                return caret
            if isinstance(caret, LatexCaret):
                return caret.push_left_brace(**kwargs)
        return self.parent.insert_left_brace(self, **kwargs)

class LatexUnaryOperator(LatexArgs):
    input_priority = 75

    def __init__(self, operator, arg, parent=None, **kwargs):
        super().__init__([operator, arg], parent=parent, **kwargs)

    @property
    def operator(self):
        return self.args[0]
    
    @property
    def arg(self):
        return self.args[1]

    def insert_delimiter(self, caret, delimiter, **kwargs):
        if isinstance(caret, LatexCaret):
            new = LatexText(delimiter, **kwargs)
            self.replace(caret, new)
            return new
        return self.parent.insert_delimiter(self, delimiter, **kwargs)

class LatexArgsNullSeparated(LatexArgs):
    @property
    def input_priority(self):
        if isinstance(arg := self.args[0], LatexBegin):
            return 0
        if isinstance(arg, LatexText) and arg.text.isalpha() or \
            isinstance(arg, LatexNumber) or \
            isinstance(arg, LatexCommand) and arg.text in spaces or \
            isinstance(arg, (LatexParenthesisGroup, LatexSizingGroup, LatexBrace)):
            return 72
        return 5

    def strFormat(self):
        return "".join(['%s'] * len(self.args))

    def insert_token(self, caret, word, **kwargs):
        if isinstance(caret, LatexText) and caret.end_idx and kwargs['start_idx'] and caret.text.isalpha() and word.isalpha():
            caret.text += word
            return caret
        new = LatexText(word, **kwargs)
        if isinstance(caret, LatexCaret):
            self.replace(caret, new)
        else:
            self.push(new)
        return new

    def insert_delimiter(self, caret, delimiter, **kwargs):
        new = LatexText(delimiter, **kwargs)
        self.push(new)
        if caret := new.push_delimiter(delimiter):
            return caret
        return new

    def insert_comma(self, caret, **kwargs):
        comma = LatexText(',', **kwargs)
        new = LatexCaret(**kwargs)
        self.push(comma)
        self.push(new)
        return new

    def insert_semicolon(self, caret, **kwargs):
        comma = LatexText(';', **kwargs)
        new = LatexCaret(**kwargs)
        self.push(comma)
        self.push(new)
        return new

    def insert_command(self, caret, command, **kwargs):
        new = LatexCommand(command, **kwargs)
        if isinstance(caret, LatexCaret):
            self.replace(caret, new)
        else:
            self.push(new)
        return new

    def insert_infix(self, caret, operator, **kwargs):
        if input_priority[operator] > self.input_priority and len(self.args) > 2:
            offset = 0
            if operator == r"\\":
                offset += 1
                if isinstance(array := self.args[0], LatexBegin) and isinstance(array := array.arg, LatexBrace) and isinstance(array := array.arg, LatexText) and array.text == 'array' and \
                    isinstance(rcl := self.args[1], LatexBrace) and isinstance(rcl := rcl.arg, LatexText) and re.fullmatch("[rcl]+", rcl.text):
                    offset += 1
            elif isinstance(arg := self.args[0], LatexLeft) or isinstance(arg, LatexText) and arg.text in ('(', ']'):
                offset += 1
            if offset:
                caret = LatexArgsNullSeparated(self.args[offset:])
                del self.args[offset:]
                self.push(caret)
        return super().insert_infix(caret, operator, **kwargs)

    def insert_big_operator(self, caret, operator, **kwargs):
        caret = LatexCommand(operator, **kwargs)
        self.push(LatexBigOperator([caret]))
        return caret

    def insert_digit(self, caret, digit, **kwargs):
        if isinstance(caret, LatexCaret):
            new = LatexNumber(digit, **kwargs)
            self.replace(caret, new)
            if len(self.args) > 2 and \
            isinstance(comma := self.args[-2], LatexText) and comma.text == ',' and \
            isinstance(infix := self.args[-3], LatexInfix) and isinstance(left := infix.right, LatexNumber):
                infix.replace(left, LatexArgsNullSeparated([left, comma, new]))
                del self.args[-2:]
            return new
        return super().insert_digit(caret, digit, **kwargs)

    def adjustment(self, index, node=None):
        if len(self.args) == 1 :
            first = self.args[0]
            self.parent.replace(self, first)
            if isinstance(first, LatexInfix):
                first.adjustment(index)

class LatexArgsSpaceSeparated(LatexArgs):
    @property
    def input_priority(self):
        if any(isinstance(arg, LatexLeft) for arg in self.args):
            return 51
        return 72

    def strFormat(self):
        return " ".join(['%s'] * len(self.args))

    def insert_left_brace(self, caret, **kwargs):
        if isinstance(caret, LatexInfix):
            caret = LatexCaret(**kwargs)
            self.push(LatexBrace(caret))
            return caret
        return super().insert_left_brace(caret, **kwargs)

    def insert_infix(self, caret, operator, **kwargs):
        if isinstance(self.args[0], LatexBegin):
            op = LatexCommand(operator, **kwargs)
            new = LatexCaret(**kwargs)
            self.replace(caret, LatexInfix(caret, op, new))
            return new
        return super().insert_infix(caret, operator, **kwargs)

    insert_token = LatexArgsNullSeparated.insert_token
    insert_delimiter = LatexArgsNullSeparated.insert_delimiter
    insert_comma = LatexArgsNullSeparated.insert_comma
    insert_big_operator = LatexArgsNullSeparated.insert_big_operator

class LatexInfix(LatexArgs):
    def __init__(self, left, operator, right, parent=None, **kwargs):
        assert isinstance(operator, (LatexCommand, LatexNot))
        super().__init__([left, operator, right], parent=parent, **kwargs)

    @property
    def input_priority(self):
        op = self.operator
        if isinstance(op, LatexNot):
            op = op.arg
        return input_priority[op.text]

    @property
    def left(self):
        return self.args[0]

    @property
    def operator(self):
        return self.args[1]

    @property
    def right(self):
        if len(self.args) > 2:
            return self.args[2]

    def is_operator(self, *ch):
        return isinstance(op := self.operator, LatexCommand) and op.text in ch

    @property
    def is_subscript(self):
        return self.is_operator('_')

    @property
    def is_ampersand(self):
        return self.is_operator('&')

    @property
    def is_supscript(self):
        return self.is_operator('^')

    def strFormat(self):
        op = '' if self.is_subscript else ' '
        return op.join(['%s'] * len(self.args))

    def insert_token(self, caret, word, **kwargs):
        if (self.is_subscript or self.is_supscript) and isinstance(self.parent, LatexOperatorWithLimits) and len(self.parent.parent.args) == 1:
            caret = LatexCaret(**kwargs)
            self.parent.parent.push(caret)
        return caret.push_token(word, **kwargs)

    def insert_unary(self, this, func, **kwargs):
        if isinstance(self.parent, LatexBigOperator) and len(self.parent.args) == 1 and self.parent.args[0] is self:
            caret = LatexCaret(**kwargs)
            self.parent.push(caret)
            return caret.parent.insert_unary(caret, func, **kwargs)
        if isinstance(self.parent, LatexInfix) and isinstance(self.parent.parent, LatexOperatorWithLimits) or isinstance(self.parent, LatexOperatorWithLimits):
            return self.parent.insert_unary(self, func, **kwargs)
        return super().insert_unary(this, func, **kwargs)

    def insert_delimiter(self, caret, delimiter, **kwargs):
        if new := self.insert_dot(caret, delimiter, **kwargs):
            return new
        if isinstance(caret, LatexCaret):
            new = LatexText(delimiter, **kwargs)
            self.replace(caret, new)
            return new
        if delimiter in '()[]':
            new = LatexText(delimiter, **kwargs)
            if isinstance(caret, (LatexArgsNullSeparated, LatexArgsSpaceSeparated)):
                caret.push(new)
                return new
            self.replace(caret, LatexArgsNullSeparated([caret, new]))
            if caret := new.push_delimiter(delimiter):
                return caret
            return new
        return self.parent.insert_delimiter(self, delimiter, **kwargs)

    def insert_big_operator(self, caret, operator, **kwargs):
        if isinstance(self.parent, LatexOperatorWithLimits) and isinstance(caret, LatexBrace) or isinstance(self.parent, (LatexArgsNullSeparated, LatexArgsSpaceSeparated)):
            return self.parent.insert_big_operator(self, operator, **kwargs)
        if self.is_subscript and isinstance(caret, LatexBrace) and isinstance(self.parent, LatexBrace):
            caret = LatexCommand(operator, **kwargs)
            self.parent.replace(self, LatexArgsSpaceSeparated([self, LatexBigOperator([caret])]))
            return caret
        return caret.push_big_operator(operator, **kwargs)

    def insert_left_brace(self, caret, **kwargs):
        if not isinstance(caret, LatexCaret):
            if isinstance(self.parent, LatexBrace) and self.is_subscript:
                caret = LatexCaret(**kwargs)
                self.parent.replace(self, LatexArgsSpaceSeparated([self, LatexBrace(caret)]))
                return caret
            if isinstance(self.parent, (LatexArgsSpaceSeparated, LatexOperatorWithLimits)):
                return self.parent.insert_left_brace(self, **kwargs)
        return super().insert_left_brace(caret, **kwargs)

    def insert_infix(self, caret, operator, **kwargs):
        if isinstance(caret, LatexCaret) and (operator in ('=', '≠', '<', '>', '≤', '≥') and self.is_ampersand or operator == '&' and self.is_operator('=', '≠', '<', '>', '≤', '≥', '&=', '&≠', '&<', '&>', '&≤', '&≥')):
            self.operator.text += operator
            return caret
        return super().insert_infix(caret, operator, **kwargs)

    def merge_infix(self, index):
        while len(self.args) >= 5 and isinstance(cmd := self.args[index + 2], LatexCommand) and cmd.text in input_priority:
            infixNode = LatexInfix(*self.args[index + 1: index + 4])
            array_splice(self.args, index + 1, 3, [infixNode])
            infixNode.parent = self

    def adjustment(self, index, node=None):
        if len(self.args) == 1:
            arg = self.args[0]
            self.parent.replace(self, arg)
            if isinstance(arg, (LatexArgsNullSeparated, LatexArgsSpaceSeparated)):
                LatexInfix.merge_infix(arg, index)
            elif isinstance(arg, LatexInfix):
                arg.adjustment(index)
            if node and isinstance(node, (LatexArgsNullSeparated, LatexArgsSpaceSeparated)):
                LatexInfix.merge_infix(node, index)
                while isinstance(node := node.parent, LatexInfix):
                    node.adjustment(index)
        else:
            self.merge_infix(index)

class LatexTag(LatexArgs):
    def __init__(self, equation, operator, tagName, parent=None, **kwargs):
        super().__init__([equation, operator, tagName], parent=parent, **kwargs)

    @property
    def equation(self):
        return self.args[0]

    @property
    def operator(self):
        return self.args[1]

    @property
    def tagName(self):
        return self.args[2]

    def strFormat(self):
        return "%s %s%s"

class LatexBinary(LatexArgs):
    @property
    def input_priority(self):
        return 70

    def insert_token(self, caret, word, **kwargs):
        if isinstance(caret, LatexCaret):
            return super().insert_token(caret, word, **kwargs)
        if len(self.args) == 3:
            caret = LatexText(caret, **kwargs)
            new = LatexArgsSpaceSeparated([self, caret])
            self.parent.replace(self, new)
        else:
            caret = LatexText(word, **kwargs)
            self.push(caret)
        return caret

    def insert_left_brace(self, caret, **kwargs):
        if len(self.args) == 2:
            assert caret is self.args[-1]
            if isinstance(caret, LatexCaret):
                return caret.push_left_brace(**kwargs)
            caret = LatexCaret(**kwargs)
            self.push(LatexBrace(caret))
            return caret
        return self.parent.insert_left_brace(self, caret, **kwargs)

    def insert_delimiter(self, caret, delimiter, **kwargs):
        if len(self.args) == 3:
            return self.parent.insert_delimiter(self, delimiter, **kwargs)
        new = LatexText(delimiter, **kwargs)
        self.push(new)
        return new

class LatexExprWithLimits(LatexArgs):
    def strFormat(self):
        return ' '.join(['%s'] * len(self.args))

    @property
    def operator(self):
        return self.args[0]

    @property
    def expr(self):
        return self.args[1]

# latex command: \max \min that take limits
class LatexBigOperatorViaCommand(LatexExprWithLimits):
    @property
    def input_priority(self):
        return 52
    
    def insert_limit_modifier(self, caret, operator, **kwargs):
        assert isinstance(caret, LatexCommand)
        assert len(self.args) == 1
        new = LatexCommand(operator, **kwargs)
        self.replace(caret, LatexOperatorWithLimits([caret, new]))
        return new

# latex big operator: \sum \prod \int
class LatexBigOperator(LatexExprWithLimits):
    @property
    def input_priority(self):
        op = self.operator
        if isinstance(op, LatexCommand) or \
            isinstance(op, LatexOperatorWithLimits) and isinstance(op := op.args[0], LatexCommand) or \
            isinstance(op, LatexInfix) and op.is_subscript and isinstance(op:= op.left, LatexCommand):
            return big_operator_priority[op.text]
        return 52

    def insert_limit_modifier(self, caret, operator, **kwargs):
        assert isinstance(caret, LatexCommand)
        assert len(self.args) == 1
        new = LatexCommand(operator, **kwargs)
        self.replace(caret, LatexOperatorWithLimits([caret, new]))
        return new

    def insert_big_operator(self, caret, operator, **kwargs):
        caret = LatexCommand(operator, **kwargs)
        self.push(LatexBigOperator([caret]))
        return caret

# latex quantifier: \exists \forall 
class LatexQuantifier(LatexExprWithLimits):
    @property
    def input_priority(self):
        return 24

# limit modifier: \sum\limits_{...}
class LatexOperatorWithLimits(LatexArgs):
    @property
    def input_priority(self):
        return 24

    def insert_big_operator(self, caret, operator, **kwargs):
        return self.parent.insert_big_operator(self, operator, **kwargs)

    def insert_left_brace(self, caret, **kwargs):
        return self.insert_unary(caret, LatexBrace, **kwargs)

    def insert_unary(self, caret, func, **kwargs):
        assert isinstance(self.parent, (LatexBigOperator, LatexBigOperatorViaCommand)) and len(self.parent.args) == 1
        caret = LatexCaret(**kwargs)
        self.parent.push(func(caret))
        return caret

class LatexDocument(LatexArgs):
    input_priority = 0

    def strFormat(self):
        return "\n".join(['%s'] * len(self.args))

    @property
    def root(self):
        return self

    def insert_comma(self, caret, **kwargs):
        comma = LatexText(',', **kwargs)
        new = LatexCaret(**kwargs)
        self.replace(caret, LatexArgsNullSeparated([caret, comma, new]))
        return new

    def insert_semicolon(self, caret, **kwargs):
        comma = LatexText(';', **kwargs)
        new = LatexCaret(**kwargs)
        self.replace(caret, LatexArgsNullSeparated([caret, comma, new]))
        return new

    def insert_tag(self, caret, operator, **kwargs):
        op = LatexCommand(operator, **kwargs)
        new = LatexCaret(**kwargs)
        self.replace(caret, LatexTag(caret, op, new))
        return new

    def insert_delimiter(self, caret, delimiter, **kwargs):
        if new := self.insert_dot(caret, delimiter, **kwargs):
            return new
        new = LatexText(delimiter, **kwargs)
        if isinstance(caret, LatexCaret):
            self.replace(caret, new)
        elif len(self.args) == 1:
            self.replace(caret, LatexArgsNullSeparated([caret, new]))
        else:
            self.push(new)
        return new

class LatexParser(AbstractParser):
    def __init__(self):
        ...

    def init(self):
        caret = LatexCaret(start_idx=0)
        self.caret = caret
        self.root = LatexDocument([caret])

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
                # if token in ';':
                    # print(history)
                # if history.endswith(r"{\begin{cases} {\left[\begin{array}{cc}{["):
                    # print(history)
                self.parse(token, start_idx=start_idx)
                assert self.caret is not None
            except Exception as e: 
                print(e)
                traceback.print_exc()
                print(history)
                raise e
            history += token
            try:
                assert re.sub(r'\s', '', str(self)) in re.sub(r'\s', '', history), history
            except Exception as e:
                print(history[:-1])
                raise e
        self.parse('', start_idx=len(text))
        return self.root

    def build(self, text):
        self.init()
        for start_idx, token in enumerate(text):
            self.parse(token, start_idx=start_idx)
        self.parse('', start_idx=len(text))
        return self.root

def test():
    from std import listdir
    import json
    for txt in listdir('std/parser/test/'):
        if not txt.endswith('case-2.txt'):
            continue
        with open(txt, 'r', encoding='utf-8') as file:
            latex = file.read()
            try:
                tree = LatexParser().build_debug(latex)
            except Exception as e:
                traceback.print_exc()
                print(e)
                exit()
            print(tree)

def test_table(module=None, Rank=None, offset=0, limit=None):
    import re
    from std import MySQL
    kwargs = {
        'dictionary' : True,
    }
    if module:
        kwargs['axiom'] = module
    else:
        kwargs |= {
            'offset' : offset,
            'fetch_size' : 1024
        }
        if limit:
            kwargs['limit'] = limit
            if kwargs['fetch_size'] > limit:
                kwargs['fetch_size'] = limit
        else:
            kwargs['limit'] = 100000
    for data in MySQL.instance.select('axiom.axiom', **kwargs):
        offset += 1
        print('testing axiom =', data['axiom'], 'offset =', offset)
        latex = data['latex']
        latex = latex.decode()
        latex = latex.split("\n")
        for latex in latex:
            for latex in latex.split("\t"):
                for latex in re.findall(r'\\\[.+?\\\]', latex):
                    latex = latex[2:-2]
                    try:
                        tree = LatexParser().build_debug(latex)
                        try:
                            if re.sub(r'\s', '', str(tree)) != re.sub(r'\s', '', latex):
                                print('difference detected:')
                                print(tree)
                                print(latex)
                        except Exception as e:
                            print(f"error in printing:\n{latex}")
                            raise e

                        if module is not None:
                            print(tree)
                    except Exception as e:
                        print(f"http://192.168.18.131:8000/py/?module={data['axiom']}")
                        import traceback
                        traceback.print_exc()
                        print(e)
                        return

digits_subscript = '[₀₁₂₃₄₅₆₇₈₉]'
digits_superscript = '⁻?[¹²³⁴⁵⁶⁷⁸⁹]'

non_digits_subscript = '[ₐₑᵢⱼₒₓᵣᵤᵥₓ]'
non_digits_superscript = '[ʰᵏᵐⁿ⁺⁻]'

greek_lowercase_letters = '[αβγδεϵζηθϑικϰλμνξοπρσςτυφχψω]'
greek_uppercase_letters = '[ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ]'
unicode_operators = '[⋅⋆⋇⋈⋉⋊⋋⋌⋍⋎⋏⋐⋑⋒⋓⋔⋕⋖⋗⋘⋙⋚⋛⋜⋝⋞⋟⋠⋡⋢⋣⋤⋥⋦⋧⋨⋩⋪⋫⋬⋭⋮⋯⋰⋱⋲⋳⋴⋵⋶⋷⋸⋹⋺⋻⋼⋽⋾⋿≤≥≠≈≡∼∝±∓×÷∑∏√∛∜∫∬∭∮∯∰∇∂∀∃∄∅∆∇∈∉∋∌∩∪⊂⊃⊆⊇⊕⊖⊗⊘⊙⊚⊛⊜⊝⊞⊟⊠⊡⊢⊣⊤⊥⋀⋁⋂⋃]'
latex_functions = [
    'acotangent', 'acsc', 'amalg', 'And', 'arccosecant', 'arccosine', 'arcotangent', 'arcsecant', 'arcsine', 'arctangent',
    'det', 'dim', 'deg', 
    'frac',
    'gcd',
    'hom',
    'inf', 'ker',
    'ln', 'log', 'liminf', 'limsup', 'lg', 'left', 
    'Pr', 'phi', 'pi', 'psi',
]

if __name__ == '__main__':
    # test_table(offset=247, limit=1)
    test()
    test_table(offset=0, limit=247)