from std.parser.node import AbstractParser, IndentedNode, Closable, case
from std.parser.newline_skipping_comment import NewLineSkippingCommentParser
from std.parser.token import TokenParser, Token
from std.parser.operator import OperatorParser
from std import getitem, binary_search
from copy import copy
import itertools, json, os, shlex, std, regex as re, traceback


token2classname = {
    '+': 'LeanAdd',
    '-': 'LeanSub',
    '*': 'LeanMul',
    '/': 'LeanDiv',
    '÷': 'LeanEDiv',  # euclidean division
    '//': 'LeanFDiv',  # floor division
    '%': 'LeanMod',
    '×': 'Lean_times',
    '•': 'Lean_bullet',
    '⬝': 'Lean_cdotp',
    '∘': 'Lean_circ',
    '▸': 'Lean_blacktriangleright',
    '⊙': 'Lean_odot',
    '⊕': 'Lean_oplus',
    '⊖': 'Lean_ominus',
    '⊗': 'Lean_otimes',
    '⊘': 'Lean_oslash',
    '⊚': 'Lean_circledcirc',
    '⊛': 'Lean_circledast',
    '⊜': 'Lean_circleeq',
    '⊝': 'Lean_circleddash',
    '⊞': 'Lean_boxplus',
    '⊟': 'Lean_boxminus',
    '⊠': 'Lean_boxtimes',
    '⊡': 'Lean_dotsquare',
    '∈': 'Lean_in',
    '∉': 'Lean_notin',
    '&': 'LeanBitAnd',
    '|': 'LeanBitOr',
    '^': 'LeanPow',
    '<<': 'Lean_ll',
    '>>': 'Lean_gg',
    '||': 'LeanLogicOr',
    '&&': 'LeanLogicAnd',
    '∨': 'Lean_lor',
    '∧': 'Lean_land',
    '∪': 'Lean_cup',
    '∩': 'Lean_cap',
    "\\": 'Lean_setminus',  # Requires escape character for backslash
    '|>.': 'LeanMethodChaining',
    '⊆': 'Lean_subseteq',
    '⊇': 'Lean_supseteq',
    '⊔': 'Lean_sqcup',
    '⊓': 'Lean_sqcap',
    '++': 'LeanAppend',
}

tactics = (
    'abel',
    'abel_nf',
    'aesop',
    'all_goals',
    'apply',
    'assumption',
    'by_cases',
    'by_contra',
    'case',
    'cases',
    "cases'",
    'classical',
    'congr',
    'constructor',
    'contradiction',
    'convert',
    'decide',
    'denote',
    'dsimp',
    'exact',
    'exfalso',
    'exists',
    'ext',
    'field_simp',
    'funext',
    'induction',
    'injection',
    'interval_cases',
    'intro',
    'intros',
    'left',
    'linarith',
    'mp',
    'mpr',
    'nlinarith',
    'norm_cast',
    'norm_num',
    'obtain',
    'omega',
    'pick_goal',
    'positivity',
    'push_cast',
    'push_neg',
    'rcases',
    'refine',
    'rename',
    'rfl',
    'right',
    'ring',
    'ring1',
    'ring_exp',
    'ring_nf',
    'rintro',
    'rw',
    'rwa',
    'simp',
    'simp_all',
    'simp_rw',
    'simpa',
    'sorry',
    'specialize',
    'split',
    'split_ifs',
    'subst',
    'suffices',
    'swap',
    'symm',
    'tauto',
    'trivial',
    'try',
    'unfold',
    'use',
    'zify',
)

class Lean(IndentedNode):
    def is_comment(self):
        return False

    def tokens_space_separated(self):
        return []

    def is_outsider(self):
        return False

    def getEcho(self):
        pass

    def strArgs(self):
        return self.args

    def toString(self):
        return self.strFormat() % tuple(self.strArgs())

    def __str__(self):
        prefix = ' ' * self.indent if self.is_indented() else ''
        return prefix + self.toString()

    def latexFormat(self):
        return self.strFormat()

    def latexArgs(self, syntax=None):
        return [arg.toLatex(syntax) for arg in self.args]

    def toLatex(self, syntax=None):
        return self.latexFormat() % tuple(self.latexArgs(syntax))

    def isProp(self, vars):
        return False

    def echo(self):
        return self

    def traverse(self):
        yield self

    def set_line(self, line):
        self.line = line
        return line

    def insert(self, caret, func, type):
        if self.parent:
            return self.parent.insert(caret, func, type)

    def insert_space(self, caret, **kwargs):
        if isinstance(caret, LeanCaret):
            caret.start_idx = kwargs['start_idx']
        return caret

    def insert_dot(self, caret, **kwargs):
        if isinstance(caret, LeanCaret) and isinstance(caret.parent, (LeanStatements, LeanSequentialTacticCombinator)):
            caret = caret.parent.insert_unary(caret, LeanTacticBlock, **kwargs)
        else:
            caret = caret.push_binary(LeanProperty, **kwargs)
        return caret

    def insert_token(self, caret, token, **kwargs):
        index = binary_search(tactics, token)
        fun = caret.parent.insert_tactic if index < len(tactics) and tactics[index] == token else caret.parent.insert_word
        caret = fun(caret, token, **kwargs)
        return caret

    def insert_keyword(self, caret, token, type, **kwargs):
        caret = caret.append(f"Lean_{token}", type)
        return caret

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.parent:
            return self.parent.insert_newline(caret, newline_count, indent, **kwargs)

    def insert_end(self, caret):
        if self.parent:
            return self.parent.insert_end(caret)

    def append(self, new, type):
        if self.parent:
            return self.parent.append(new, type)

    def push_accessibility(self, new, accessibility):
        if self.parent:
            return self.parent.push_accessibility(new, accessibility)

    def __copy__(self):
        new = type(self).__new__(type(self))
        new.__dict__.update(self.__dict__)
        new.parent = None
        return new

    def push_binary(self, type, **kwargs):
        if parent := self.parent:
            if type.input_priority > parent.stack_priority:
                new = LeanCaret(self.indent, **kwargs)
                parent.replace(self, type(self, new, self.indent))
                return new
            return parent.push_binary(type, **kwargs)

    def push_arithmetic(self, token, **kwargs):
        return self.push_binary(token2classname[token], **kwargs)

    def push_or(self):
        if not self.parent:
            return
        if Lean_lor.input_priority > self.parent.stack_priority:
            return self.push_multiple(Lean_lor, LeanCaret(self.indent))
        else:
            return self.parent.push_or()

    def push_multiple(self, Type, caret):
        if not self.parent:
            return
        parent = self.parent
        if isinstance(parent, Type):
            parent.push(caret)
        else:
            parent.replace(self, Type([self, caret], parent))
        return caret

    def push_token(self, word, **kwargs):
        return self.append(LeanToken(word, self.indent, **kwargs), "token")

    def insert_word(self, caret, word, **kwargs):
        return caret.push_token(word, **kwargs)

    def insert_comma(self, caret, **kwargs):
        if self.parent:
            return self.parent.insert_comma(self, **kwargs)

    def insert_semicolon(self, caret, **kwargs):
        if self.parent:
            return self.parent.insert_semicolon(self, **kwargs)

    def insert_colon(self, caret, **kwargs):
        return caret.push_binary(LeanColon, **kwargs)

    def insert_assign(self, caret, **kwargs):
        return caret.push_binary(LeanAssign, **kwargs)

    def insert_vconstruct(self, caret, **kwargs):
        return caret.push_binary(LeanVConstruct, **kwargs)

    def insert_construct(self, caret, **kwargs):
        return caret.push_binary(LeanConstruct, **kwargs)

    def insert_bar(self, caret, prev_token, next_token, **kwargs):
        if next_token == ' ':
            if prev_token == ' ':
                return caret.push_arithmetic('|')
            return self.push_right(LeanAbs)
        elif next_token == ')':
            return self.push_right(LeanAbs)
        else:
            if not next_token:
                return self.push_right(LeanAbs)
            return self.insert_unary(caret, LeanAbs, **kwargs)

    def insert_unary(self, this, func, **kwargs):
        parent = this.parent
        if isinstance(this, LeanCaret):
            caret = this
            new = func(caret, this.indent)
        else:
            caret = LeanCaret(this.indent)
            new = func(caret, this.indent)
            new = LeanArgsSpaceSeparated([this, new], this.indent)
        parent.replace(this, new)
        return caret

    def push_post_unary(self, func):
        if not self.parent:
            return
        parent = self.parent
        if func.input_priority > parent.stack_priority:
            new = func(self, self.indent)
            parent.replace(self, new)
            return new
        else:
            return parent.push_post_unary(func)

    def push_left(self, Type, prev_token):
        if Type in [
            'LeanParenthesis', 'LeanBracket', 'LeanBrace', 'LeanAngleBracket', 'LeanFloor', 'LeanCeil', 'LeanNorm', 'LeanDoubleAngleQuotation'
        ]:
            indent = self.indent
            caret = LeanCaret(indent)
            if Type == 'LeanBracket':
                if prev_token == ' ':
                    # consider the case: a ≡ b [MOD n]
                    current = self
                    parent = self.parent
                    while parent:
                        if isinstance(parent, (Lean_equiv, LeanNotEquiv)):
                            new = Type(caret, indent)
                            parent.replace(current, LeanArgsSpaceSeparated([current, new], indent))
                            return caret
                        current = parent
                        parent = parent.parent
                elif isinstance(self, (LeanToken, LeanProperty, LeanGetElemBase)) or isinstance(self, LeanPairedGroup) and self.is_Expr():
                    # consider the case: (f x)[n], f[m][n]
                    self.parent.replace(self, LeanGetElem(self, caret, indent))
                    return caret

            new = Type(caret, indent)
            if isinstance(self.parent, LeanArgsSpaceSeparated):
                self.parent.push(new)
            else:
                self.parent.replace(self, LeanArgsSpaceSeparated([self, new], indent))
            return caret
        else:
            raise Exception(f"{self.__class__.__name__}.push_left is unexpected for {Type}")

    def insert_left(self, caret, func, prev_token=''):
        return caret.push_left(func, prev_token)

    def push_right(self, func):
        if self.parent:
            return self.parent.push_right(func)

    def push_attr(self, caret):
        raise Exception(f"{type(self).__name__}.push_attr is unexpected for {type(self).__name__}")

    def push_minus(self):
        raise Exception(f"{type(self).__name__}.push_minus is unexpected for {type(self).__name__}")

    def push_quote(self, quote):
        raise Exception(f"{type(self).__name__}.push_quote is unexpected for {type(self).__name__}")

    @property
    def root(self):
        return self.parent.root

    @property
    def stack_priority(self):
        return type(self).input_priority

    def insert_sequential_tactic_combinator(self, caret):
        if self.parent:
            return self.parent.insert_sequential_tactic_combinator(self)

    def relocate_last_comment(self):
        pass

    def split(self, syntax=None):
        return [self]

    def regexp(self):
        return []

    def insert_then(self, caret):
        if self.parent:
            return self.parent.insert_then(self)

    def insert_else(self, caret):
        if self.parent:
            return self.parent.insert_else(self)

    def is_indented(self):
        parent = self.parent
        return isinstance(parent, (LeanArgsCommaNewLineSeparated, LeanArgsNewLineSeparated)) or \
               (isinstance(parent, LeanITE) and (self is parent.then or self is parent.Else))

    def is_space_separated(self):
        return False

    def insert_line_comment(self, caret, comment):
        return caret.push_line_comment(comment)

    @case(*Token.ascii)
    def case(self, **kwargs):
        return TokenParser(self, **kwargs).parse(self.key)

    @case('import', 'open', 'namespace', 'def', 'theorem', 'lemma')
    def case(self, **kwargs):
        return self.parent.insert_keyword(self, self.key, "delspec", **kwargs)
    
    @case('fun', 'match')
    def case(self, **kwargs):
        return self.parent.insert_keyword(self, self.key, "expr", **kwargs)

    @case('have', 'let', 'show')
    def case(self, **kwargs):
        return self.parent.insert_keyword(self, self.key, "tactic", **kwargs)

    # todo
    def insert_accessibility(self, caret, token, type, **kwargs):
        caret = caret.append(f"Lean_{token}", type)
        return caret
    
    @case('public', 'private', 'protected', 'noncomputable')
    def case(self, **kwargs):
        return self.parent.insert_keyword(self, self.key, "accessibility", **kwargs)

    @case("\t")
    def case(self, **kwargs):
        raise Exception("Tab is not allowed in Lean")

    @case("\r")
    def case(self, **kwargs):
        print("Carriage return is not allowed in Lean")
    
    @case('\n')
    def case(self, **kwargs):
        return NewLineSkippingCommentParser(self, **kwargs)

    def insert_is(self, caret, **kwargs):
        if isinstance(caret, LeanCaret) and isinstance(caret.parent, LeanProperty):
            caret = caret.parent.insert_word(caret, 'is', **kwargs)
        else:
            Type = Lean_is
            if i + 2 < count and tokens[i + 1] == ' ' and tokens[i + 2].lower() == 'not':
                i += 2
                Type += '_not'
            caret = caret.push_binary(Type, **kwargs)
        return caret

    @case('is')
    def case(self, **kwargs):
        return self.parent.insert_is(self, **kwargs)

    @case('(')
    def case(self, **kwargs):
        return self.parent.insert_left_parenthesis(self, **kwargs)

    def insert_left_parenthesis(self, caret, **kwargs):
        return self.insert_left(caret, 'LeanParenthesis')
    
    @case(')')
    def case(self, **kwargs):
        return self.parent.insert_right_parenthesis(self, **kwargs)

    def insert_right_parenthesis(self, caret, **kwargs):
        return self.push_right('LeanParenthesis')

    @case('[')
    def case(self, **kwargs):
        return self.parent.insert_left_bracket(self, **kwargs)

    def insert_left_bracket(self, caret, **kwargs):
        return self.insert_left(caret, 'LeanBracket', tokens[i - 1] if i else '')
    
    @case(']')
    def case(self, **kwargs):
        return self.parent.insert_right_bracket(self, **kwargs)

    def insert_right_bracket(self, caret, **kwargs):
        return self.push_right('LeanBracket')

    @case('{')
    def case(self, **kwargs):
        return self.parent.insert_left(self, LeanBrace, **kwargs)

    @case('}')
    def case(self, **kwargs):
        return self.push_right(LeanBrace, **kwargs)

    @case('⟨')
    def case(self, **kwargs):
        return self.parent.insert_left_angle_bracket(self, **kwargs)

    def insert_left_angle_bracket(self, caret, **kwargs):
        return self.insert_left(caret, 'LeanAngleBracket')
    
    @case('⟩')
    def case(self, **kwargs):
        return self.parent.insert_right_angle_bracket(self, **kwargs)

    def insert_right_angle_bracket(self, caret, **kwargs):
        return self.push_right('LeanAngleBracket')

    @case('⌈')
    def case(self, **kwargs):
        return self.parent.insert_left_ceil(self, **kwargs)

    def insert_left_ceil(self, caret, **kwargs):
        return self.insert_left(caret, 'LeanCeil')

    @case('⌉')
    def case(self, **kwargs):
        return self.parent.insert_right_ceil(self, **kwargs)

    def insert_right_ceil(self, caret, **kwargs):
        return self.push_right('LeanCeil')

    @case('⌊')
    def case(self, **kwargs):
        return self.parent.insert_left_floor(self, **kwargs)

    def insert_left_floor(self, caret, **kwargs):
        return self.insert_left(caret, 'LeanFloor')

    @case('⌋')
    def case(self, **kwargs):
        return self.parent.insert_right_floor(self, **kwargs)

    def insert_right_floor(self, caret, **kwargs):
        return self.push_right('LeanFloor')
    
    @case('«')
    def case(self, **kwargs):
        return self.parent.insert_left_double_angle_quotation(self, **kwargs)

    def insert_left_double_angle_quotation(self, caret, **kwargs):
        return self.insert_left(caret, 'LeanDoubleAngleQuotation')

    @case('»')
    def case(self, **kwargs):
        return self.parent.insert_right_double_angle_quotation(self, **kwargs)

    def insert_right_double_angle_quotation(self, caret, **kwargs):
        return self.push_right('LeanDoubleAngleQuotation')

    @case('?')
    def case(self, **kwargs):
        return self.parent.insert_question_mark(self, **kwargs)

    def insert_question_mark(self, caret, **kwargs):
        if isinstance(caret, LeanGetElem):
            parent = caret.parent
            lhs, rhs = caret.args
            new = LeanGetElemQue(lhs, rhs, caret.indent)
            parent.replace(caret, new)
            caret = new
        else:
            caret = caret.parent.insert_word(caret, '?', **kwargs)
        return caret

    @case('?_')
    def case(self, **kwargs):
        return self.parent.insert_question_hole(self, **kwargs)

    def insert_question_hole(self, caret, **kwargs):
        return self.insert_word(caret, '?_', **kwargs)

    @case('<', '>', '=', '!', ':', '+', '-', '/', '|', '&', '⁻', '.')
    def case(self, **kwargs):
        return OperatorParser(self, **kwargs)

        if token == '<':
            if tokens[i+1] == '=':
                i += 1
                caret = caret.push_binary('Lean_le', **kwargs)
            elif i + 2 < count and tokens[i + 1] == ';' and tokens[i + 2] == '>':
                i += 2
                caret = caret.parent.insert_sequential_tactic_combinator(caret)
            else:
                caret = caret.push_binary('Lean_lt', **kwargs)
        elif token == '>':
            if tokens[i + 1] == '=':
                i += 1
                caret = caret.push_binary('Lean_ge', **kwargs)
            else:
                caret = caret.push_binary('Lean_gt', **kwargs)
        elif token == '=':
            if tokens[i + 1] == '>':
                i += 1
                caret = caret.push_binary('LeanRightarrow', **kwargs)
            elif tokens[i + 1] == '=':
                i += 1
                caret = caret.push_binary('LeanBEq', **kwargs)
            else:
                caret = caret.push_binary('LeanEq', **kwargs)
        elif token == '!':
            if tokens[i + 1] == '=':
                i += 1
                caret = caret.push_binary('Lean_ne', **kwargs)
            else:
                caret = caret.parent.insert_unary(caret, 'LeanNot', **kwargs)
        if token == ':':
            if tokens[i + 1] == '=':
                i += 1
                caret = caret.parent.insert_assign(caret)
            elif tokens[i + 1] == ':':
                i += 1
                if tokens[i + 1] == 'ᵥ':
                    i += 1
                    caret = caret.parent.insert_vconstruct(caret)
                else:
                    caret = caret.parent.insert_construct(caret)
            else:
                caret = caret.parent.insert_colon(caret)
        elif token == ';':
            caret = caret.parent.insert_semicolon(caret)
        elif token == '-':
            if tokens[i + 1] == '-':
                i += 1
                comment = ""
                i += 1
                while tokens[i] != '\n':
                    comment += tokens[i]
                    i += 1
                caret = caret.parent.insert_line_comment(caret, comment.strip())
                i -= 1; # now $tokens[++$i] must be a new line;
            elif isinstance(caret, LeanCaret):
                caret = caret.parent.insert_unary(caret, 'LeanNeg', **kwargs)
            else:
                caret = caret.push_arithmetic(token)
        if token == '|':
            next_token = tokens[i + 1]
            if next_token == '|':
                i += 1
                caret = caret.push_arithmetic('||')
            elif next_token == '>':
                i += 1
                if tokens[i + 1] == '.':
                    i += 1
                    caret = caret.push_arithmetic('|>.')
                else:
                    caret = caret.push_post_unary('LeanPipeForward')
            else:
                caret = caret.parent.insert_bar(caret, tokens[i - 1] if i else '', next_token)
        elif token == '&':
            if tokens[i + 1] == '&':
                caret = caret.push_arithmetic('&&')
                i += 1
            else:
                caret = caret.parent.insert_bitand(caret)
        if token == '+':
            if isinstance(caret, LeanCaret):
                caret = caret.parent.insert_unary(caret, 'LeanPlus', **kwargs)
            else:
                if tokens[i + 1] == '+':
                    i += 1
                    token += '+'
                caret = caret.push_arithmetic(token)
        elif token == '⁻':
            if tokens[i + 1] == '¹':
                i += 1
                caret = caret.push_post_unary('LeanInv')
        elif token == '/':
            if tokens[i + 1] == '-':
                i += 1
                if tokens[i+1] == '-':
                    docstring = True
                    i += 1
                else:
                    docstring = False
                comment = ""
                while True:
                    i += 1
                    if tokens[i] == '-' and tokens[i + 1] == '/':
                        i += 1
                        break
                    comment += tokens[i]
                comment = re.sub(r'(?<=\n) +$', '', comment)
                comment = comment.strip('\n')
                caret = caret.push_block_comment(comment, docstring)
                if tokens[i + 1] == '\n':
                    i += 1
            elif tokens[i + 1] == '/':
                caret = caret.push_arithmetic('//')
                i += 1

    @case('≤')
    def case(self, **kwargs):
        return self.push_binary('Lean_le', **kwargs)
    
    @case('≥')
    def case(self, **kwargs):
        return self.push_binary('Lean_ge', **kwargs)

    @case('≠')
    def case(self, **kwargs):
        return self.push_binary('Lean_ne', **kwargs)

    @case('≡')
    def case(self, **kwargs):
        return self.push_binary('Lean_equiv', **kwargs)
    
    @case('≢')
    def case(self, **kwargs):
        return self.push_binary('LeanNotEquiv', **kwargs)
    
    @case(',')
    def case(self, **kwargs):
        return self.parent.insert_comma(self)

    @case('*')
    def case(self, **kwargs):
        if isinstance(self, LeanCaret):
            self = self.parent.insert_word(self, '*', **kwargs)
        elif isinstance(self, LeanToken) and self.is_TypeStar() and (not i or tokens[i - 1] != ' '):
            self.text += '*'
        else:
            self = self.push_arithmetic('*')
        return self

    @case('%', '^', '<<', '>>', '×', '⬝', '∘', '•', '⊙', '⊗', '⊕', '⊖', '⊘', '⊚', '⊛', '⊜', '⊝', '⊞', '⊟', '⊠', '⊡', '∈', '∉', '▸', '∪', '∩', '⊔', '⊓', "\\")
    def case(self, **kwargs):
        return self.push_arithmetic(self.key)
    
    @case('←')
    def case(self, **kwargs):
        return self.parent.insert_unary(self, 'Lean_leftarrow', **kwargs)

    @case('→')
    def case(self, **kwargs):
        return self.push_binary('Lean_rightarrow', **kwargs)

    @case('↦')
    def case(self, **kwargs):
        return self.push_binary('Lean_mapsto', **kwargs)

    @case('↔')
    def case(self, **kwargs):
        return self.push_binary('Lean_leftrightarrow', **kwargs)

    @case('∀')
    def case(self, **kwargs):
        return self.append('Lean_forall', 'operator', **kwargs)

    @case('∃')
    def case(self, **kwargs):
        return self.append('Lean_exists', 'operator', **kwargs)

    @case('∑')
    def case(self, **kwargs):
        return self.append('Lean_sum', 'operator')

    @case('∏')
    def case(self, **kwargs):
        return self.append('Lean_prod', 'operator')

    @case('∧')
    def case(self, **kwargs):
        return self.push_binary('Lean_land', **kwargs)

    @case('∨')
    def case(self, **kwargs):
        return self.push_binary('Lean_lor', **kwargs)

    @case('⊆')
    def case(self, **kwargs):
        return self.push_binary('Lean_subseteq', **kwargs)

    @case('⊇')
    def case(self, **kwargs):
        return self.push_binary('Lean_supseteq', **kwargs)

    @case('¬')
    def case(self, **kwargs):
        return self.parent.insert_unary(self, 'Lean_lnot', **kwargs)

    @case('√')
    def case(self, **kwargs):
        return self.parent.insert_unary(self, 'Lean_sqrt', **kwargs)

    @case('∛')
    def case(self, **kwargs):
        return self.parent.insert_unary(self, 'LeanCubicRoot', **kwargs)

    @case('∜')
    def case(self, **kwargs):
        return self.parent.insert_unary(self, 'LeanQuarticRoot', **kwargs)

    @case('↑')
    def case(self, **kwargs):
        return self.parent.insert_unary(self, 'Lean_uparrow', **kwargs)

    @case('²')
    def case(self, **kwargs):
        return self.push_post_unary('LeanSquare')

    @case('³')
    def case(self, **kwargs):
        return self.push_post_unary('LeanCube')

    @case('⁴')
    def case(self, **kwargs):
        return self.push_post_unary('LeanTesseract')

    @case('by', 'calc', 'using', 'at', 'with', 'in', 'generalizing', 'MOD', 'from')
    def case(self, **kwargs):
        if isinstance(self, LeanCaret) and isinstance(self.parent, LeanProperty):
            self = self.parent.insert_word(self, self.key, **kwargs)
        else:
            self = self.parent.insert(self, f"Lean_{self.key}", "modifier")
        return self

    @case('·')
    def case(self, **kwargs):
        if isinstance(self.parent, (LeanStatements, LeanSequentialTacticCombinator)):
            self = self.parent.insert_unary(self, 'LeanTacticBlock', **kwargs)
        else:
            # Middle Dot token
            self = self.parent.insert_word(self, self.key, **kwargs)
        return self

    @case('@')
    def case(self, **kwargs):
        if isinstance(self, LeanCaret):
            return self.parent.insert_unary(self, LeanAttribute, **kwargs)
        else:
            return self.push_binary(LeanMatMul)

    @case('end')
    def case(self, **kwargs):
        return self.parent.insert_end(self)

    @case('only')
    def case(self, **kwargs):
        return self.parent.insert_only(self)

    @case('if')
    def case(self, **kwargs):
        return self.parent.insert_if(self)

    @case('then')
    def case(self, **kwargs):
        return self.parent.insert_then(self)

    @case('else')
    def case(self, **kwargs):
        return self.parent.insert_else(self)

    @case('‖')
    def case(self, **kwargs):
        if isinstance(self, LeanCaret) or i and tokens[i - 1] == ' ':
            self = self.parent.insert_left(self, 'LeanNorm')
        else:
            self = self.parent.push_right('LeanNorm')
        return self

    @case(' ')
    def case(self, **kwargs):
        return self.parent.insert_space(self, **kwargs)

    @case('.')
    def case(self, **kwargs):
        return self.parent.insert_dot(self, **kwargs)

    @case
    def case(self, **kwargs):
        return self.parent.insert_token(self, self.key, **kwargs)

class LeanCaret(Lean):
    def __init__(self, indent, start_idx, parent=None):
        super().__init__(indent, parent)
        self.start_idx = start_idx

    @property
    def end_idx(self):
        return self.start_idx

    def is_indented(self):
        return isinstance(self.parent, LeanArgsNewLineSeparated)

    def strFormat(self):
        return ''

    def push_line_comment(self, comment):
        parent = self.parent
        new = LeanLineComment(comment, self.indent)
        parent.replace(self, new)
        return new

    def push_block_comment(self, comment, docstring):
        parent = self.parent
        func = LeanDocString if docstring else LeanBlockComment
        parent.replace(self, func(comment, self.indent))
        parent.push(self)
        return self

    def append(self, new, type):
        if isinstance(new, str):
            self.parent.replace(self, eval(new)(self, self.indent))
            return self
        else:
            self.parent.replace(self, new)
            return new

    def push_accessibility(self, new, accessibility):
        self.parent.replace(self, eval(new)(accessibility, self, self.indent))
        return self

    def toJson(self):
        return ""

    def push_left(self, Type, prev_token):
        self.parent.replace(self, Type(self, self.indent))
        return self

    def latexFormat(self):
        return ""

    def is_outsider(self):
        return True

class LeanToken(Lean):
    def __init__(self, text, indent, start_idx, parent=None):
        super().__init__(indent, start_idx=start_idx, parent=parent)
        self.text = text
        self.cache = None

    def push_quote(self, quote):
        self.text += quote
        return self

    def strFormat(self):
        return self.text

    subscript = {
        'ₐ': 'a',
        'ₑ': 'e',
        'ₕ': 'h',
        'ᵢ': 'i',
        'ⱼ': 'j',
        'ₖ': 'k',
        'ₗ': 'l',
        'ₘ': 'm',
        'ₙ': 'n',
        'ₒ': 'o',
        'ₚ': 'p',
        'ᵣ': 'r',
        'ₛ': 's',
        'ₜ': 't',
        'ᵤ': 'u',
        'ᵥ': 'v',
        'ₓ': 'x',
        '₀': '0',
        '₁': '1',
        '₂': '2',
        '₃': '3',
        '₄': '4',
        '₅': '5',
        '₆': '6',
        '₇': '7',
        '₈': '8',
        '₉': '9',
        'ᵦ': r'\beta',
        'ᵧ': r'\gamma',
        'ᵨ': r'\rho',
        'ᵩ': r'\phi',
        'ᵪ': r'\chi',
    }

    subscript_keys = None
    supscript = {
        '⁰': '0',
        '¹': '1',
        '²': '2',
        '³': '3',
        '⁴': '4',
        '⁵': '5',
        '⁶': '6',
        '⁷': '7',
        '⁸': '8',
        '⁹': '9',
        'ᵅ': 'alpha',
        'ᵝ': 'beta',
        'ᵞ': 'gamma',
        'ᵟ': 'delta',
        'ᵋ': 'epsilon',
        'ᵑ': 'eta',
        'ᶿ': 'theta',
        'ᶥ': 'iota',
        'ᶺ': 'lambda',
        'ᵚ': 'omega',
        'ᶹ': 'upsilon',
        'ᵠ': 'phi',
        'ᵡ': 'chi',
    }

    supscript_keys = None
    def latexFormat(self):
        text = escape_specials(self.text)
        if text == self.text:
            text = self.subscript_keys.sub(
                lambda m: '_{' + ''.join(self.subscript[c] for c in m.group(0)) + '}',
                text
            )
            text = self.supscript_keys.sub(
                lambda m: '^{' + ''.join(self.supscript[c] for c in m.group(0)) + '}',
                text
            )
            if text == '_':
                text = '\\_'
        return [text]

    def starts_with_2_letters(self):
        return bool(re.match(r"^[a-zA-Z]{2,}", self.text))

    def ends_with_2_letters(self):
        return bool(re.search(r"[a-zA-Z]{2,}$", self.text))

    def push_token(self, word, **kwargs):
        new = LeanToken(word, self.indent, **kwargs)
        self.parent.replace(self, LeanArgsSpaceSeparated([self, new], self.indent))
        return new

    def append(self, new, type):
        if self.parent:
            return self.parent.insert(self, new, type)

    def toJson(self):
        return self.text

    def is_variable(self):
        return re.fullmatch(r'[a-zA-Z_][a-zA-Z_0-9]*', self.text)

    def lower(self):
        self.text = self.text.lower()
        return self

    def regexp(self):
        return ["_"]

    def tokens_space_separated(self):
        return [self]

    def isProp(self, vars):
        return vars.get(self.text) == 'Prop'

    def operand_count(self):
        match = re.search(r"\?*$", self.text)
        return len(match.group(0)) if match else 0

    def is_parallel_operator(self):
        return re.search(r"_\?+$", self.text)

    def tactic_block_info(self):
        self.cache = {'size': 1}
        return {0: [self]}

    def is_TypeStar(self) -> bool:
        return self.text in [
            'Sort', 'Type'
        ]

LeanToken.subscript_keys = '[' + ''.join(LeanToken.subscript.keys()) + ']+'
LeanToken.supscript_keys = '[' + ''.join(LeanToken.supscript.keys()) + ']+'

class LeanLineComment(Lean):
    def __init__(self, text, indent, parent=None):
        super().__init__(indent, parent)
        self.text = text

    def is_outsider(self) -> bool:
        return re.match(r'(created|updated) on (\d{4}-\d{2}-\d{2})$', self.text)

    def is_indented(self) -> bool:
        if self.text == 'given':
            parent = self.parent
            if isinstance(parent, LeanArgsNewLineSeparated):
                parent = parent.parent
                if isinstance(parent, LeanArgsIndented):
                    parent = parent.parent
                    if isinstance(parent, LeanColon):
                        parent = parent.parent
                        if isinstance(parent, LeanAssign) and isinstance(parent.parent, Lean_lemma):
                            return False

        elif self.text == 'proof':
            parent = self.parent
            if isinstance(parent, LeanStatements):
                if isinstance(parent.parent, Lean_by):
                    parent = parent.parent
                if parent.parent:
                    parent = parent.parent
                    if isinstance(parent, LeanAssign) and isinstance(parent.parent, Lean_lemma):
                        return False
            elif isinstance(parent, LeanArgsNewLineSeparated):
                if parent.parent:
                    parent = parent.parent
                    if isinstance(parent, LeanAssign) and isinstance(parent.parent, Lean_lemma):
                        return False

        if self.text == 'proof':
            parent = self.parent
            if isinstance(parent, LeanStatements):
                parent = parent.parent
                if isinstance(parent, LeanColon):
                    parent = parent.parent
                    if isinstance(parent, LeanAssign) and isinstance(parent.parent, Lean_lemma):
                        return False
        return True

    def sep(self):
        return ' '

    def strFormat(self):
        sep = self.sep()
        return f"{self.operator}{sep}%s"

    def toJson(self):
        return {self.func : self.text}

    def latexFormat(self):
        sep = self.sep()
        return f"{self.command}{sep}%s"

    operator = '--'
    command = '%'
    
    @property
    def args(self):
        return [self.text]

    def latexArgs(self, syntax):
        return self.args

    def is_comment(self):
        return True

class LeanBlockComment(Lean):
    def __init__(self, text, indent, parent=None):
        super().__init__(indent, parent)
        self.text = text

    def is_indented(self):
        return True

    def sep(self):
        return ''

    def strFormat(self):
        return "/-%s-/"

    def toJson(self):
        return {self.func: self.text}

    @property
    def args(self):
        return [self.text]

    def latexArgs(self, syntax=None):
        return self.args

    def set_line(self, line):
        self.line = line
        line += self.text.count("\n")
        return line

    def is_comment(self):
        return True

class LeanDocString(LeanBlockComment):
    def __init__(self):
        super().__init__()
        self.text = None

    def strFormat(self):
        return "/--\n%s\n-/"

    def is_indented(self):
        return False

    def toJson(self):
        return {self.func: self.text}

    def set_line(self, line):
        self.line = line
        line += 1
        if self.text is not None:
            line += self.text.count('\n')
        line += 1
        return line

class LeanMultipleLine:
    def set_line(self, line):
        self.line = line
        for arg in self.args:
            line = arg.set_line(line) + 1
        return line - 1

class LeanArgs(Lean, LeanMultipleLine):
    input_priority = 47

    @property
    def command(self):
        return "\\" + self.func

    @property
    def func(self):
        cls_name = self.__class__.__name__
        for prefix in ['Lean_', 'Lean']:
            if cls_name.startswith(prefix):
                return cls_name[len(prefix):]
        return cls_name

    def __copy(self):
        this = super().__copy()
        this.args = [arg.__copy() for arg in self.args]
        for arg in this.args:
            arg.parent = this
        return this

    def __init__(self, args, indent, parent=None):
        super().__init__(indent, parent)
        self.args = args
        for arg in self.args:
            arg.parent = self

    def replace(self, old, new):
        try:
            i = self.args.index(old)
        except ValueError:
            raise Exception(f"{self.__class__.__name__}.replace is unexpected")

        if isinstance(new, list):
            self.args[i:i+1] = new
            for el in new:
                if el.parent is None:
                    el.parent = self
        else:
            self.args[i] = new
            if new.parent is None:
                new.parent = self

    def removeChild(self, node):
        try:
            i = self.args.index(node)
        except ValueError:
            raise Exception(f"{self.__class__.__name__}.remove_child is unexpected")
        del self.args[i]
        if len(self.args) == 1:
            arg = self.args[0]
            parent = self.parent
            parent.replace(self, arg)
            arg.parent = parent

    def toJson(self):
        return [arg.toJson() for arg in self.args]

    def push(self, arg):
        self.args.append(arg)
        arg.parent = self

    def unshift(self, arg):
        self.args.insert(0, arg)
        arg.parent = self

    def set_line(self, line):
        self.line = line
        for arg in self.args:
            line = arg.set_line(line)
        return line

    def traverse(self):
        yield self
        for arg in self.args:
            if arg is not None:
                yield from arg.traverse()

    def regexp(self):
        func = self.func.capitalize()
        all_patterns = []
        for arg in self.args:
            patterns = arg.regexp() 
            patterns.append("_")
            all_patterns.append(patterns)
        regexps = []
        for combo in itertools.product(*all_patterns):
            expr = "".join(combo)
            regexps.append(f"{func}{expr}")
        return regexps

    def strip_parenthesis(self):
        return [
            arg.arg if isinstance(arg, LeanParenthesis) and not isinstance(arg.arg, LeanMethodChaining) 
            else arg 
            for arg in self.args
        ]

    def insert_tactic(self, caret, type):
        if isinstance(caret, LeanCaret):
            tactic = LeanTactic(type, caret, self.indent)
            self.replace(caret, tactic)
            return caret
        raise Exception(f"{self.__class__.__name__}.insert_tactic is unexpected")

class LeanUnary(LeanArgs):
    input_priority = 47

    def __init__(self, arg, indent, parent=None):
        super().__init__([], indent, parent)
        self.args.append(None)
        self.arg = arg

    @property
    def arg(self):
        return self.args[0]

    @arg.setter
    def arg(self, value):
        self.args[0] = value
        value.parent = self

    def replace(self, old, new):
        assert self.arg is old, "assert failed: public function replace($old, $new)"
        self.arg = new

    def toJson(self):
        return self.arg.toJson()

    def insert_if(self, caret):
        if self.arg is caret:
            if isinstance(caret, LeanCaret):
                self.arg = LeanITE(caret, caret.indent)
                return caret
        raise Exception(f"{self.__class__.__name__}::insert_if is unexpected for {self.__class__.__name__}")

class LeanPairedGroup(LeanUnary, Closable):
    input_priority = 60

    def is_indented(self):
        parent = self.parent
        return not isinstance(parent, (
            LeanTactic, 
            LeanArgsCommaSeparated, 
            LeanAssign, 
            LeanArgsSpaceSeparated, 
            LeanRelational, 
            LeanRightarrow, 
            LeanUnaryArithmeticPre, 
            LeanArithmetic, 
            LeanProperty, 
            LeanColon, 
            LeanPairedGroup
        ))

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.indent <= indent:
            if isinstance(caret, LeanCaret):
                if indent == self.indent:
                    indent = self.indent + 2
                caret.indent = indent
                self.arg = LeanArgsCommaNewLineSeparated([caret], indent)
                return caret
            else:
                if indent == self.indent:
                    return caret
                raise Exception(f"{self.__class__.__name__}.insert_newline is unexpected for {self.__class__.__name__}")
        else:
            return super().insert_newline(caret, newline_count, indent, **kwargs)

    def insert_comma(self, caret):
        caret = LeanCaret(self.indent)
        if isinstance(self.arg, LeanArgsCommaSeparated):
            self.arg.push(caret)
        else:
            self.arg = LeanArgsCommaSeparated([self.arg, caret], self.indent)
        return caret

    def insert_tactic(self, caret, token, **kwargs):
        if isinstance(caret, LeanCaret):
            return self.insert_word(caret, token, **kwargs)
        raise Exception(f"{self.__class__.__name__}.insert_tactic is unexpected for {self.__class__.__name__}")

    def set_line(self, line):
        self.line = line
        has_newline = isinstance(self.arg, LeanArgsCommaNewLineSeparated)
        if has_newline:
            line += 1
        line = self.arg.set_line(line)
        if has_newline:
            line += 1
        return line

    def push_right(self, func):
        if self.__class__.__name__ == func.__name__:
            lt = self.arg
            if isinstance(lt, Lean_lt) and isinstance(lt.lhs, LeanToken):
                new = LeanStack(lt, self.indent)
                caret = LeanCaret(self.indent)
                new.scope = caret
                self.parent.replace(self, new)
                return caret
            self.is_closed = True
            return self
        return self.parent.push_right(func)

    def insert(self, caret, func, type):
        if self.arg is caret:
            if isinstance(caret, LeanCaret):
                self.arg = func(caret, self.indent)
                return caret
        raise Exception(f"{self.__class__.__name__}.insert is unexpected for {self.__class__.__name__}")

    def argFormat(self):
        return '%s'

    def strFormat(self):
        arg = self.argFormat()
        operator = self.operator
        format = f"{operator[0]}{arg}"
        if self.is_closed:
            format += operator[1]
        return format

    def is_Expr(self):
        return True

class LeanParenthesis(LeanPairedGroup):
    def is_indented(self):
        parent = self.parent
        return isinstance(parent, LeanArgsNewLineSeparated) or isinstance(parent, LeanArgsCommaNewLineSeparated)

    def argFormat(self):
        arg = self.arg
        if (isinstance(arg, Lean_by) and 
            (stmt := arg.arg) and isinstance(stmt, LeanStatements) and 
            (end := stmt.args[-1]) and isinstance(end, LeanCaret)):
            indent = ' ' * self.indent
            return f"%s{indent}"
        return '%s'

    def latexFormat(self):
        arg = self.arg
        if isinstance(arg, LeanColon) and isinstance(arg.lhs, LeanBrace):
            return arg.lhs.latexFormat()
        return r'\left( {%s} \right)'

    def latexArgs(self, syntax=None):
        arg = self.arg
        if isinstance(arg, LeanColon) and isinstance(arg.lhs, LeanBrace):
            return arg.lhs.latexArgs(syntax)
        return super().latexArgs(syntax)

    stack_priority = 10
    operator = '()'

    def append(self, new, type):
        indent = self.indent
        caret = LeanCaret(indent)
        if isinstance(new, str):
            new_cls = globals()[new]
            new = new_cls(caret, indent)
            if isinstance(self.parent, LeanArgsSpaceSeparated):
                self.parent.push(new)
            else:
                self.arg = LeanArgsSpaceSeparated([self.arg, new], indent)
            return caret
        else:
            self.parent.replace(self, LeanArgsSpaceSeparated([self, new], indent))
            return new

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.indent <= indent:
            if caret is self.arg:
                if isinstance(caret, Lean_by) and self.indent == indent:
                    caret = LeanCaret(indent)
                    new = LeanArgsNewLineSeparated([self.arg, caret], indent)
                    caret = new.push_newlines(newline_count - 1)
                    self.arg = new
                else:
                    indent = indent if self.indent == indent else self.indent + 2
                    caret = LeanCaret(indent)
                    new = LeanArgsNewLineSeparated([caret], indent)
                    caret = new.push_newlines(newline_count - 1)
                    self.arg = LeanArgsIndented(self.arg, new, self.indent)
                return caret
        raise Exception(f"{self.insert_newline.__name__} is unexpected for {self.__class__.__name__}")

    def insert_unary(self, caret, func, **kwargs):
        if caret is self.arg:
            indent = self.indent
            if isinstance(caret, LeanCaret):
                new = func(caret, indent)
            else:
                caret = LeanCaret(indent)
                new = LeanArgsSpaceSeparated([self.arg, func(caret, indent)], indent)
            self.arg = new
            return caret
        raise Exception(f"{self.insert_unary.__name__} is unexpected for {self.__class__.__name__}")

    def regexp(self):
        return self.arg.regexp()

    def isProp(self, vars):
        return self.arg.isProp(vars)

class LeanAngleBracket(LeanPairedGroup):
    def strArgs(self):
        arg = self.arg
        if isinstance(arg, LeanArgsCommaNewLineSeparated):
            arg = f"\n{arg}\n{' ' * self.indent}"
        return [arg]

    stack_priority = 10
    operator = '⟨⟩'

    def latexFormat(self):
        return '\\langle {%s} \\rangle'

    def tokens_comma_separated(self):
        arg = self.arg
        if isinstance(arg, LeanArgsCommaSeparated):
            tokens = arg.tokens_comma_separated()
        else:
            tokens = [arg]
        return tokens
    
class LeanBracket(LeanPairedGroup):

    def is_Expr(self):
        return False

    def strArgs(self):
        arg = self.arg
        if isinstance(arg, LeanArgsCommaNewLineSeparated):
            arg = f"\n{arg}\n{' ' * self.indent}"
        return [arg]

    stack_priority = 17
    operator = '[]'

    def latexFormat(self):
        return r'\left[ {%s} \right]'

class LeanBrace(LeanPairedGroup):
    def is_Expr(self):
        return False

    def is_indented(self):
        parent = self.parent
        return not isinstance(parent, (LeanQuantifier, LeanBinaryBoolean, LeanColon, LeanSetOperator))

    stack_priority = 17
    operator = '{}'

    def latexFormat(self):
        return r'\left\{ {%s} \right\}'

class LeanAbs(LeanPairedGroup):
    # public static $input_priority = 60
    stack_priority = 17
    operator = '||'

    def latexFormat(self):
        return r'\left| {%s} \right|'

class LeanNorm(LeanPairedGroup):
    stack_priority = 17
    operator = '‖‖'

    def latexFormat(self):
        return r'\left\lVert {%s} \right\rVert'

class LeanCeil(LeanPairedGroup):
    input_priority = 72
    stack_priority = 22
    operator = '⌈⌉'

    def latexFormat(self):
        return r'\left\lceil {%s} \right\rceil'

class LeanFloor(LeanPairedGroup):
    input_priority = 72
    stack_priority = 22
    operator = '⌊⌋'

    def latexFormat(self):
        return r'\left\lfloor {%s} \right\rfloor'

class LeanDoubleAngleQuotation(LeanPairedGroup):
    def is_Expr(self):
        return False

    stack_priority = 22
    operator = '«»'
    def is_indented(self):
        return False
    
class LeanBinary(LeanArgs):
    input_priority = 47

    def __init__(self, lhs, rhs, indent, parent=None):
        super().__init__([lhs, rhs], indent, parent)

    @property
    def lhs(self):
        return self.args[0]

    @lhs.setter
    def lhs(self, val):
        self.args[0] = val
        val.parent = self

    @property
    def rhs(self):
        return self.args[1]

    @rhs.setter
    def rhs(self, val):
        self.args[1] = val
        val.parent = self

    def toJson(self):
        return {self.func: [self.lhs.toJson(), self.rhs.toJson()]}

    def set_line(self, line: int) -> int:
        self.line = line
        line = self.lhs.set_line(line)
        sep = self.sep()
        if sep and sep[0] == '\n':
            line += 1
        return self.rhs.set_line(line)

    def latexFormat(self) -> str:
        return "{%s} " + self.command + " {%s}"

    def insert_if(self, caret) -> object:
        if self.rhs == caret:
            if isinstance(caret, LeanCaret):
                self.rhs = LeanITE(caret, caret.indent)
                return caret
        raise Exception(f"{self.__class__.__name__}.insert_if is unexpected")

class LeanProperty(LeanBinary):
    input_priority = 81

    def push_attr(self, caret):
        return super().push_attr(caret)

    def sep(self):
        return ''

    def is_indented(self):
        parent = self.parent
        if isinstance(parent, (LeanArgsCommaNewLineSeparated, LeanArgsNewLineSeparated)):
            return True
        if isinstance(parent, LeanArgsIndented) and parent.rhs == self:
            return True
        if isinstance(parent, LeanITE):
            else_node = getattr(parent, 'else', None)
            if else_node is self:
                return True
        return False

    def strFormat(self):
        return f"%s{self.operator}%s"

    def is_space_separated(self):
        rhs = self.rhs
        if isinstance(rhs, LeanToken):
            command = rhs.text
            if command in [
                'cos', 'sin', 'tan', 'log'
            ]:
                return True
        return False

    def latexFormat(self):
        rhs = self.rhs
        if isinstance(rhs, LeanToken):
            command = rhs.text
            if command == 'exp':
                return r'{\color{RoyalBlue} e} ^ {%s}'
            if command in [
                'cos', 'sin', 'tan', 'log'
            ]:
                return f"\\{command} {{{{%s}}}}"
            if command == 'fmod':
                return r'{%s} \textcolor{red}{\%%}'
            if command == 'card':
                if not (isinstance(self.lhs, LeanToken) and 
                        isinstance(self.parent, LeanArgsSpaceSeparated) and 
                        self.parent.args[0] == self):
                    return r'\left|{%s}\right|'
        return "{%s}" + str(self.command) + "{%s}"

    def latexArgs(self, syntax):
        rhs = self.rhs
        if isinstance(rhs, LeanToken):
            command = rhs.text
            if command == 'exp':
                exponent = self.lhs
                if isinstance(exponent, LeanParenthesis):
                    exponent = exponent.arg
                return [exponent.toLatex(syntax)]
            if command in [
                'cos', 'sin', 'tan', 'log', 'fmod'
            ]:
                return [self.lhs.toLatex(syntax)]
            if command == 'card':
                if not (isinstance(self.lhs, LeanToken) and 
                        isinstance(self.parent, LeanArgsSpaceSeparated) and 
                        self.parent.args[0] == self):
                    return [self.lhs.toLatex(syntax)]
        return super().latexArgs(syntax)

    stack_priority = 87
    operator = command = '.'

    def insert_left(self, caret, func, prev_token=''):
        if func == 'LeanDoubleAngleQuotation':
            return caret.push_left(func, prev_token)
        if self.parent:
            return self.parent.insert_left(self, func, prev_token)

    def insert_word(self, caret, word, **kwargs):
        if isinstance(caret, LeanCaret):
            return super().insert_word(caret, word, **kwargs)
        if self.parent:
            return self.parent.insert_word(self, word, **kwargs)

    def push_token(self, word, **kwargs):
        new = LeanToken(word, self.indent)
        self.parent.replace(self, LeanArgsSpaceSeparated([self, new], self.indent))
        return new

    def insert_tactic(self, caret, token, **kwargs):
        return self.insert_word(caret, token, **kwargs)

    def regexp(self):
        func = str(self.rhs).capitalize()
        regexp_list = self.lhs.regexp()
        regexp_list = [func + expr for expr in regexp_list]
        regexp_list.append(func + '_')
        return regexp_list

    def insert_unary(self, caret, func, **kwargs):
        if self.parent:
            return self.parent.insert_unary(self, func, **kwargs)

    def insert(self, caret, func, type, **kwargs):
        if self.rhs == caret:
            if isinstance(caret, LeanCaret):
                if func.startswith('Lean_'):
                    return self.insert_word(caret, func[5:], **kwargs)
            elif type == 'modifier':
                return self.parent.insert(self, func, type)
            else:
                caret = LeanCaret(self.indent)
                new_args = LeanArgsSpaceSeparated(
                    [
                        self, 
                        eval(func)(caret, caret.indent)
                    ], 
                    self.indent
                )
                self.parent.replace(self, new_args)
                return caret
        raise Exception(f"{self.__class__.__name__}::insert is unexpected for {caret.__class__.__name__}")

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if isinstance(self.parent, LeanTactic) and indent > self.indent:
            caret = LeanCaret(indent)
            newline = LeanArgsNewLineSeparated([caret], indent)
            caret = newline.push_newlines(newline_count - 1)
            self.parent.replace(self, LeanArgsIndented(
                self,
                newline,
                self.indent
            ))
            return caret
        return self.parent.insert_newline(self, newline_count, indent, **kwargs)

class LeanColon(LeanBinary):
    input_priority = 20

    def sep(self):
        rhs = self.rhs
        if isinstance(rhs, LeanStatements):
            return "\n"
        elif isinstance(rhs, LeanCaret):
            return ''
        else:
            return ' '

    def is_indented(self):
        return False

    def strFormat(self):
        sep = self.sep()
        return f"%s {self.operator}{sep}%s"

    def strArgs(self):
        lhs, rhs = self.args
        if isinstance(lhs, LeanArgsNewLineSeparated):
            args = [f"{arg}" for arg in lhs.args[1:]]
            args.insert(0, f"{lhs.args[0]}")
            lhs = "\n".join(args)
        return [lhs, rhs]

    @property
    def operator(self):
        return ':'
    @property
    def command(self):
        return ':'

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.rhs is caret:
            if isinstance(caret, LeanCaret) and indent > self.indent:
                caret.indent = indent
                self.rhs = LeanStatements([caret], indent)
                return caret
            if isinstance(caret, LeanStatements) and indent == self.indent and isinstance(self.parent, LeanParenthesis):
                return caret
        return super().insert_newline(caret, newline_count, indent, **kwargs)

class LeanAssign(LeanBinary):
    input_priority = 19

    def sep(self):
        rhs = self.rhs
        if isinstance(rhs, LeanArgsNewLineSeparated):
            lines = rhs.args
            if (len(lines) > 2 or 
                not (isinstance(lines[1], LeanArgsNewLineSeparated) if len(lines) > 1 else False) or 
                (len(lines) > 0 and isinstance(lines[0], LeanLineComment))):
                return "\n"
        return ' '

    def is_indented(self):
        return isinstance(self.parent, LeanArgsNewLineSeparated)

    def strFormat(self):
        sep = self.sep()
        return f"%s {self.operator}{sep}%s"

    @property
    def operator(self):
        return ':='
    @property
    def command(self):
        return ':='

    def relocate_last_comment(self):
        self.rhs.relocate_last_comment()

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.indent < indent:
            if caret == self.rhs:
                if isinstance(caret, LeanCaret):
                    caret.indent = indent
                    self.rhs = LeanArgsNewLineSeparated([caret], indent)
                    caret = self.rhs.push_newlines(newline_count - 1)
                    return caret
                elif isinstance(caret, LeanArgsNewLineSeparated):
                    if self.parent:
                        return self.parent.insert_newline(self, newline_count, indent, **kwargs)
                else:
                    caret = LeanCaret(indent)
                    new = LeanArgsNewLineSeparated([caret], indent)
                    caret = new.push_newlines(newline_count - 1)
                    self.rhs = LeanArgsIndented(self.rhs, new, self.indent)
                    return caret
            raise Exception(f"{__name__} is unexpected for {self.__class__.__name__}")
        elif self.parent:
            return self.parent.insert_newline(self, newline_count, indent, **kwargs)

    def echo(self):
        self.rhs = self.rhs.echo()
        return self

    def insert(self, caret, func, type):
        if self.rhs == caret:
            if isinstance(caret, LeanCaret):
                self.replace(caret, func(caret, caret.indent))
                return caret
        raise Exception(f"{__name__} is unexpected for {self.__class__.__name__}")

class LeanProp:
    def isProp(self, vars):
        return True

class LeanBinaryBoolean(LeanBinary, LeanProp):
    def sep(self):
        return "\n" if isinstance(self.rhs, LeanStatements) else " "

    def is_indented(self):
        return isinstance(self.parent, LeanStatements)

    def strFormat(self):
        sep = self.sep()
        return f"%s {self.operator}{sep}%s"

    def append(self, new, type):
        indent = self.indent
        caret = LeanCaret(indent)

        if isinstance(new, str):
            new = globals()[new](caret, indent)
            self.rhs = LeanArgsSpaceSeparated([self.rhs, new], indent)
            return caret
        else:
            self.parent.replace(self, LeanArgsSpaceSeparated([self, new], indent))
            return new

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.rhs is caret and isinstance(caret, LeanCaret) and indent > self.indent:
            caret.indent = indent
            self.rhs = LeanStatements([caret], indent)
            return caret
        return super().insert_newline(caret, newline_count, indent, **kwargs)

class LeanRelational(LeanBinaryBoolean):
    input_priority = 51

    def latexArgs(self, syntax):
        lhs, rhs = self.strip_parenthesis()
        return [lhs.toLatex(syntax), rhs.toLatex(syntax)]

    def insert_tactic(self, caret, token, **kwargs):
        return self.insert_word(caret, token, **kwargs)

class Lean_gt(LeanRelational):
    @property
    def operator(self):
        return '>'

class Lean_ge(LeanRelational):
    @property
    def operator(self):
        return '≥'

class Lean_lt(LeanRelational):
    @property
    def operator(self):
        return '<'

class Lean_le(LeanRelational):
    @property
    def operator(self):
        return '≤'

class LeanEq(LeanRelational):
    @property
    def command(self):
        return '='

    @property
    def operator(self):
        return '='

class LeanBEq(LeanRelational):
    @property
    def command(self):
        return r'=\!\!='

    @property
    def operator(self):
        return '=='

class Lean_ne(LeanRelational):
    @property
    def operator(self):
        return '≠'

class Lean_equiv(LeanRelational):
    input_priority = 32

    @property
    def operator(self):
        return '≡'

class LeanNotEquiv(LeanRelational):
    input_priority = 32

    @property
    def command(self):
        return r'\not\equiv'

    @property
    def operator(self):
        return '≢'

class Lean_in(LeanBinaryBoolean):
    input_priority = 51

    @property
    def operator(self):
        return '∈'

    def latexArgs(self, syntax=None):
        lhs, rhs = self.args
        if isinstance(lhs, LeanParenthesis):
            lhs = lhs.arg
        lhs = lhs.toLatex(syntax)
        rhs = rhs.toLatex(syntax)
        return [lhs, rhs]

class Lean_notin(LeanBinaryBoolean):
    input_priority = 51

    @property
    def operator(self):
        return '∉'

    def latexArgs(self, syntax=None):
        lhs, rhs = self.args
        if isinstance(lhs, LeanParenthesis):
            lhs = lhs.arg
        lhs = lhs.toLatex(syntax)
        rhs = rhs.toLatex(syntax)
        return [lhs, rhs]

class Lean_leftrightarrow(LeanBinaryBoolean):
    input_priority = 21

    @property
    def operator(self):
        return '↔'

class LeanArithmetic(LeanBinary):
    input_priority = 67

    def sep(self):
        return ' '

    def strFormat(self):
        sep = self.sep()
        return f"%s {self.operator}{sep}%s"


class LeanAdd(LeanArithmetic):
    input_priority = 66

    @property
    def command(self):
        return '+'

    @property
    def operator(self):
        return '+'


class LeanSub(LeanArithmetic):
    input_priority = 66

    @property
    def command(self):
        return '-'

    @property
    def operator(self):
        return '-'


class LeanMul(LeanArithmetic):
    input_priority = 71

    @property
    def command(self):
        lhs, rhs = self.args

        if (isinstance(rhs, LeanParenthesis) and isinstance(rhs.arg, LeanDiv) or
            isinstance(rhs, LeanToken) and rhs.text.isdigit() or
            isinstance(rhs, LeanMul) and rhs.command or
            isinstance(lhs, LeanMul) and lhs.command or
            lhs.is_space_separated() or
            isinstance(lhs, LeanFDiv) or
            isinstance(rhs, LeanPow)):
            return r'\cdot'

        if (isinstance(lhs, LeanToken) and (rhs.is_space_separated() or 
            isinstance(rhs, LeanToken) and rhs.starts_with_2_letters()) or
            isinstance(lhs, LeanToken) and lhs.ends_with_2_letters() and 
            isinstance(rhs, LeanToken) or
            isinstance(lhs, LeanProperty) or 
            isinstance(rhs, LeanProperty)):
            return r'\ '

        return ''

    @property
    def operator(self):
        return '*'

    def latexFormat(self):
        return "%s {command} %s".format(command=self.command)

    def latexArgs(self, syntax=None):
        lhs, rhs = self.args
        syntax_ref = syntax

        if isinstance(rhs, LeanParenthesis) and isinstance(rhs.arg, LeanDiv):
            rhs = rhs.arg
        elif isinstance(rhs, LeanNeg):
            rhs = LeanParenthesis(rhs, self.indent)
        elif isinstance(lhs, LeanNeg):
            lhs = LeanParenthesis(lhs, self.indent)

        lhs = lhs.toLatex(syntax_ref)
        rhs = rhs.toLatex(syntax_ref)
        return [lhs, rhs]

class Lean_times(LeanArithmetic):
    input_priority = 72

    @property
    def operator(self):
        return '×'

class LeanMatMul(LeanArithmetic):
    input_priority = 70
    operator = '@'
    command = r'{\color{red}\times}'

class Lean_bullet(LeanArithmetic):
    input_priority = 73

    @property
    def operator(self):
        return '•'

class Lean_odot(LeanArithmetic):
    input_priority = 73

    @property
    def operator(self):
        return '⊙'

class Lean_otimes(LeanArithmetic):
    input_priority = 32

    @property
    def operator(self):
        return '⊗'

class Lean_oplus(LeanArithmetic):
    input_priority = 31

    @property
    def operator(self):
        return '⊕'

class LeanDiv(LeanArithmetic):
    input_priority = 71

    @property
    def operator(self):
        return '/'

    def latexFormat(self):
        if isinstance(self.lhs, LeanDiv):
            return r'\left. {%s} \right/ {%s}'
        else:
            return r'\frac {%s} {%s}'

    def latexArgs(self, syntax):
        lhs = self.lhs
        rhs = self.rhs

        if not isinstance(self.lhs, LeanDiv):
            if isinstance(lhs, LeanParenthesis):
                lhs = lhs.arg
            if isinstance(rhs, LeanParenthesis):
                rhs = rhs.arg

        lhs = lhs.toLatex(syntax)
        rhs = rhs.toLatex(syntax)
        return lhs, rhs

class LeanFDiv(LeanArithmetic):
    input_priority = 70

    @property
    def command(self):
        return r'/\!\!/'

    @property
    def operator(self):
        return '//'

class LeanBitAnd(LeanArithmetic):
    input_priority = 68

    @property
    def command(self):
        return '\\&'

    @property
    def operator(self):
        return '&'


class LeanBitOr(LeanArithmetic):
    #  used in the syntax:
    #  rcases lt_trichotomy 0 a with ha | h_0 | ha
    def is_indented(self):
        return False

    def insert_bar(self, caret, prev_token, next_token):
        if isinstance(caret, LeanToken):
            new = LeanCaret(self.indent)
            self.replace(caret, LeanBitOr(caret, new, self.indent))
            return new
        raise Exception(f"{self.__class__.__name__}.insert_bar is unexpected for {type(caret).__name__}")

    @property
    def operator(self):
        return '|'

    @property
    def command(self):
        return '|'

    def tokens_bar_separated(self):
        tokens = []
        for arg in self.args:
            if isinstance(arg, LeanBitOr):
                tokens.extend(arg.tokens_bar_separated())
            elif isinstance(arg, LeanAngleBracket):
                tokens.append(arg.tokens_comma_separated())
            else:
                tokens.append(arg)
        return tokens

    def unique_token(self, indent):
        tokens = self.tokens_bar_separated()
        processed_tokens = []
        for token in tokens:
            if isinstance(token, list):
                token = [t for t in token if t.text != 'rfl']
            processed_tokens.append(token)

        def create_key(t):
            if isinstance(t, LeanToken):
                return t.text
            return ','.join(sub.arg for sub in t)

        keys = [create_key(t) for t in processed_tokens]
        if len(set(keys)) == 1:
            token = processed_tokens[0]
            if isinstance(token, list) and len(token) == 1:
                token = token[0]
            if isinstance(token, list):
                cloned = [copy(t) for t in token]
                for t in cloned:
                    t.indent = indent
                return LeanArgsCommaSeparated(cloned, indent)
            else:
                cloned = copy(token)
                cloned.indent = indent
                return cloned

    def latexArgs(self, syntax=None):
        if syntax is None:
            syntax = {}
        if isinstance(self.parent, LeanQuantifier):
            syntax['setOf'] = True
        return super().latexArgs(syntax)

class LeanPow(LeanArithmetic):
    input_priority = 80

    operator = command = '^'
    stack_priority = 79

    def latexArgs(self, syntax=None):
        lhs, rhs = self.args
        if isinstance(lhs, LeanParenthesis):
            if (isinstance(lhs.arg, Lean_sqrt) or 
                isinstance(lhs.arg, LeanPairedGroup) or 
                (isinstance(lhs.arg, LeanArgsSpaceSeparated) and 
                 (lhs.arg.is_Abs() or lhs.arg.is_Bool()))):
                lhs = lhs.arg

        if isinstance(rhs, LeanParenthesis):
            rhs = rhs.arg

        return lhs.toLatex(syntax), rhs.toLatex(syntax)

class Lean_ll(LeanArithmetic):
    operator = '<<'

class Lean_gg(LeanArithmetic):
    operator = '>>'

class LeanMod(LeanArithmetic):
    input_priority = 71

    command = '\\%%'
    operator = '%%'

class LeanConstruct(LeanArithmetic):
    input_priority = 68

    command = operator = '::'

class LeanVConstruct(LeanArithmetic):
    input_priority = 68

    command = '::_v'
    operator = '::ᵥ'

class LeanAppend(LeanArithmetic):
    input_priority = 66

    command = r'+\!\!+'
    operator = '++'

class Lean_sqcup(LeanArithmetic):
    input_priority = 68

    @property
    def operator(self):
        return '⊔'

class Lean_sqcap(LeanArithmetic):
    input_priority = 69

    @property
    def operator(self):
        return '⊓'

class Lean_cdotp(LeanArithmetic):
    input_priority = 71

    @property
    def operator(self):
        return '⬝'

    @property
    def command(self):
        return '{\\color{red}\\cdotp}'

class Lean_circ(LeanArithmetic):
    input_priority = 91

    @property
    def operator(self):
        return '∘'

class Lean_blacktriangleright(LeanArithmetic):
    operator = '▸'
    def is_indented(self):
        return isinstance(self.parent, LeanArgsNewLineSeparated)

class LeanUnaryArithmetic(LeanUnary):
    pass

class LeanUnaryArithmeticPost(LeanUnaryArithmetic):
    input_priority = 58

    stack_priority = 60

class LeanUnaryArithmeticPre(LeanUnaryArithmetic):
    stack_priority = 67

class LeanNeg(LeanUnaryArithmeticPre):
    input_priority = 68

    def sep(self):
        if isinstance(self.arg, LeanNeg):
            return ' '
        return ''

    def strFormat(self):
        sep = self.sep()
        return f"{self.operator}{sep}%s"

    def latexFormat(self):
        return f"{self.command}{{%s}}"

    def latexArgs(self, syntax=None):
        arg = self.arg
        if isinstance(arg, LeanParenthesis):
            sub_arg = arg.arg
            if isinstance(sub_arg, LeanDiv) or (isinstance(sub_arg, LeanMul) and not sub_arg.command):
                arg = sub_arg
        arg = arg.toLatex(syntax)
        return [arg]

    stack_priority = 70
    operator = command = '-'

class LeanPlus(LeanUnaryArithmeticPre):
    def strFormat(self):
        return f"{self.operator}%s"

    def latexFormat(self):
        return f"{self.command}{{%s}}"

    operator = command = '+'

class LeanInv(LeanUnaryArithmeticPost):
    input_priority = 71

    def strFormat(self):
        return f"%s{self.operator}"

    def latexFormat(self):
        return f"{{%s}}{self.command}"

    @property
    def operator(self):
        return '⁻¹'

    @property
    def command(self):
        return '^{-1}'

class Lean_sqrt(LeanUnaryArithmeticPre):
    input_priority = 72

    def strFormat(self):
        return f"{self.operator}%s"

    def latexFormat(self):
        return f"{self.command}{{%s}}"

    def latexArgs(self, syntax=None):
        arg = self.arg
        if isinstance(arg, LeanParenthesis):
            arg = arg.arg
        arg = arg.toLatex(syntax)
        return [arg]

    @property
    def stack_priority(self):
        return 71

    @property
    def operator(self):
        return '√'

class LeanSquare(LeanUnaryArithmeticPost):
    def strFormat(self):
        return f"%s{self.operator}"

    def latexFormat(self):
        return f"{{%s}}{self.command}"

    def latexArgs(self, syntax=None):
        arg = self.arg
        if isinstance(arg, LeanParenthesis):
            if isinstance(arg.arg, (Lean_sqrt, LeanPairedGroup)) or (isinstance(arg.arg, LeanArgsSpaceSeparated) and (arg.arg.is_Abs() or arg.arg.is_Bool())):
                arg = arg.arg
        if syntax is not None:
            syntax['²'] = True
        arg = arg.toLatex(syntax)
        return [arg]

    @property
    def operator(self):
        return '²'

    @property
    def command(self):
        return '^2'

class LeanCubicRoot(LeanUnaryArithmeticPre):
    def strFormat(self):
        return f"{self.operator}%s"

    def latexFormat(self):
        return f"{self.command}{{%s}}"

    @property
    def stack_priority(self):
        return 71

    @property
    def operator(self):
        return '∛'

    @property
    def command(self):
        return r'\sqrt[3]'

class Lean_uparrow(LeanUnaryArithmeticPre):
    input_priority = 72

    def strFormat(self):
        return f"{self.operator}%s"

    def latexFormat(self):
        return f"{self.command} %s"

    def latexArgs(self, syntax=None):
        arg = self.arg
        if isinstance(arg, LeanParenthesis) and isinstance(arg.arg, LeanArgsSpaceSeparated) and arg.arg.is_Abs():
            arg = arg.arg
        return [arg.toLatex(syntax)]

    @property
    def stack_priority(self):
        return 70

    @property
    def operator(self):
        return '↑'

class LeanUparrow(LeanUnaryArithmeticPre):
    input_priority = 72

    def strFormat(self):
        return f"{self.operator}%s"

    def latexFormat(self):
        return f"{self.command} %s"

    @property
    def stack_priority(self):
        return 71

    @property
    def operator(self):
        return '⇑'

class LeanCube(LeanUnaryArithmeticPost):
    def strFormat(self):
        return f"%s{self.operator}"

    def latexFormat(self):
        return f"{{%s}}{self.command}"

    @property
    def operator(self):
        return '³'

    @property
    def command(self):
        return '^3'

class LeanQuarticRoot(LeanUnaryArithmeticPre):
    def strFormat(self):
        return f"{self.operator}%s"

    def latexFormat(self):
        return f"{self.command}{{%s}}"

    @property
    def stack_priority(self):
        return 71

    @property
    def operator(self):
        return '∜'

    @property
    def command(self):
        return r'\sqrt[4]'

class LeanTesseract(LeanUnaryArithmeticPost):
    def strFormat(self):
        return f"%s{self.operator}"

    def latexFormat(self):
        return f"{{%s}}{self.command}"

    @property
    def operator(self):
        return '⁴'

    @property
    def command(self):
        return '^4'

class LeanPipeForward(LeanUnaryArithmeticPost):
    def strFormat(self):
        return "%s " + self.operator

    def latexFormat(self):
        return "{%s} " + self.command

    @property
    def operator(self):
        return '|>'

    @property
    def command(self):
        return r'\text{ |> }'

class LeanMethodChaining(LeanBinary):
    input_priority = 67

    def sep(self):
        return ''

    @property
    def stack_priority(self):
        return 59

    def strFormat(self):
        return '%s |>.%s'

    def latexFormat(self):
        return r'%s\ \texttt{|>.}%s'

class LeanGetElemBase(LeanBinary):
    input_priority = 67

    def sep(self):
        return ''

    stack_priority = 19

    def push_right(self, func):
        if func == 'LeanBracket':
            return self
        return super().push_right(func)

    def insert_comma(self, caret):
        new = LeanCaret(self.indent)
        self.rhs = LeanArgsCommaSeparated([caret, new], self.indent)
        return new

class LeanGetElem(LeanGetElemBase):
    def strFormat(self):
        return '%s[%s]'

    def latexFormat(self):
        return '{%s}_{%s}'

class LeanGetElemQue(LeanGetElemBase):
    def strFormat(self):
        return '%s[%s]?'

    def latexFormat(self):
        return '{%s}_{%s?}'

class Lean_is(LeanBinary):
    input_priority = 62

    def sep(self):
        return ' '

    def is_indented(self):
        return isinstance(self.parent, LeanStatements)

    def strFormat(self):
        return f"%s {self.operator} %s"

    def latexFormat(self):
        return "{%s}\\ " + self.command + "\\ {%s}"

    @property
    def operator(self):
        return 'is'

    @property
    def command(self):
        return '{\\color{blue}\\text{is}}'

    def isProp(self, vars):
        return True


class L_is_not(LeanBinary):
    input_priority = 62

    def sep(self):
        return ' '

    def is_indented(self):
        return isinstance(self.parent, LeanStatements)

    def strFormat(self):
        return f"%s {self.operator} %s"

    @property
    def command(self):
        return '{\\color{blue}\\text{is not}}'

    @property
    def operator(self):
        return 'is not'

    def isProp(self, vars):
        return True

class LeanSetOperator(LeanBinary):
    def sep(self):
        return ' '

    def strFormat(self):
        return "%s " + self.operator + " %s"

class Lean_setminus(LeanSetOperator):
    input_priority = 71
    operator = "\\"

class Lean_cup(LeanSetOperator):
    input_priority = 66
    operator = '∪'

class Lean_cap(LeanSetOperator):
    input_priority = 71
    operator = '∩'

class LeanLogic(LeanBinaryBoolean):
    def __init__(self, lhs, rhs, indent, parent=None):
        super().__init__(lhs, rhs, indent, parent)
        self.hanging_indentation = None

    def sep(self):
        if self.hanging_indentation:
            return '\n' + (' ' * self.rhs.indent)
        else:
            return ' '

    def is_indented(self) -> bool:
        return isinstance(self.parent, LeanStatements)

    def strFormat(self) -> str:
        sep = self.sep()
        return f"%s {self.operator}{sep}%s"

class LeanLogicAnd(LeanLogic):
    input_priority = 37

    def strFormat(self) -> str:
        return f"%s {self.operator} %s"

    @property
    def stack_priority(self):
        return 50

    @property
    def command(self) -> str:
        return r'\&\&'

    @property
    def operator(self) -> str:
        return '&&'

    def toJson(self):
        lhs = self.lhs.toJson()
        rhs = self.rhs.toJson()
        if isinstance(self.lhs, Lean_land):
            return {self.func: [*lhs[self.func], rhs]}
        else:
            return {self.func: [lhs, rhs]}

class LeanLogicOr(LeanLogic):
    input_priority = 37

    def strFormat(self) -> str:
        return f"%s {self.operator} %s"

    @property
    def stack_priority(self) -> int:
        return 36

    command = operator = '||'

    def toJson(self):
        lhs = self.lhs.toJson()
        rhs = self.rhs.toJson()
        if isinstance(self.lhs, Lean_lor):
            return {self.func: [*lhs[self.func], rhs]}
        else:
            return {self.func: [lhs, rhs]}

class Lean_lor(LeanLogic):
    input_priority = 30

    @property
    def stack_priority(self):
        return 29

    @property
    def operator(self):
        return '∨'

    def toJson(self):
        lhs = self.lhs.toJson()
        rhs = self.rhs.toJson()
        return {self.func: [lhs, rhs]}

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if caret is self.rhs and isinstance(caret, LeanCaret):
            if indent >= self.indent:
                if indent == self.indent:
                    indent = self.indent + 2
                self.hanging_indentation = True
                caret.indent = indent
                return caret
        return super().insert_newline(caret, newline_count, indent, **kwargs)

class Lean_land(LeanLogic):
    input_priority = 35

    @property
    def stack_priority(self):
        return 34

    @property
    def operator(self):
        return '∧'

    def toJson(self):
        lhs = self.lhs.toJson()
        rhs = self.rhs.toJson()
        return {self.func: [lhs, rhs]}
    
class Lean_subseteq(LeanBinaryBoolean):
    input_priority = 51

    @property
    def operator(self):
        return '⊆'

class Lean_supseteq(LeanLogic):
    input_priority = 51

    @property
    def operator(self):
        return '⊇'

class LeanStatements(LeanArgs, LeanMultipleLine):

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.indent > indent:
            return super().insert_newline(caret, newline_count, indent, **kwargs)

        if self.indent < indent:
            raise Exception(f"{__name__} is unexpected for {self.__class__.__name__}")

        start_idx = kwargs['start_idx']
        for i in range(newline_count):
            caret = LeanCaret(indent, start_idx + i)
            self.push(caret)
        caret.start_idx += indent
        return caret

    def insert_if(self, caret):
        if self.args and self.args[-1] is caret:
            if isinstance(caret, LeanCaret):
                self.replace(caret, LeanITE(caret, caret.indent))
                return caret
        raise Exception(f"{__name__} is unexpected for {self.__class__.__name__}")

    @property
    def stack_priority(self):
        return LeanColon.input_priority
    def is_indented(self):
        return False

    def strFormat(self):
        return "\n".join(['%s'] * len(self.args))

    def latexFormat(self):
        return "\n".join(['{%s}'] * len(self.args))

    def toJson(self):
        args = super().toJson()
        if self.args and isinstance(self.args[-1], LeanCaret):
            args = args[:-1]
        if len(args) == 1:
            args = args[0]
        return args

    def relocate_last_comment(self):
        index = len(self.args) - 1
        while index >= 0:
            end = self.args[index]
            if end.is_outsider():
                current = self
                parent = None
                while current:
                    parent = current.parent
                    if isinstance(parent, LeanStatements):
                        break
                    current = parent
                if parent:
                    last = self.args.pop()
                    parent.args.insert(parent.args.index(self) + 1, last)
                    last.parent = parent
                    parent.relocate_last_comment()
                    break
            else:
                if end.is_comment():
                    lemma = None
                    j = index - 1
                    while j >= 0:
                        stmt = self.args[j]
                        if isinstance(stmt, Lean_lemma):
                            lemma = stmt
                            break
                        if stmt.is_comment():
                            j -= 1
                        else:
                            break
                    if lemma:
                        assignment = lemma.assignment
                        if isinstance(assignment, LeanAssign):
                            proof = assignment.rhs
                            if isinstance(proof, (Lean_by, Lean_calc)):
                                proof = proof.arg
                                if isinstance(proof, LeanStatements):
                                    for i in range(j + 1, index + 1):
                                        proof.push(self.args[i])
                                    self.args = self.args[:j + 1] + self.args[index + 1:]
                                    break
                            elif isinstance(proof, LeanArgsNewLineSeparated):
                                for i in range(j + 1, index + 1):
                                    proof.push(self.args[i])
                                self.args = self.args[:j + 1] + self.args[index + 1:]
                                break
                end.relocate_last_comment()
                break
            index -= 1

    def echo(self):
        index = 0
        while index < len(self.args) - 1:
            result = self.args[index].echo()
            if isinstance(result, list):
                length = result[0]
                for echo_item in result[1:]:
                    echo_item.parent = self
                insertion_index = result.index(self.args[index])
                self.args = self.args[:index] + result[1:] + self.args[index + length:]
                index += insertion_index - 1
            index += 1

        if not self.args:
            return self

        tactic = self.args[-1]
        if isinstance(tactic, (LeanTactic, Lean_match)):
            if tactic.With:
                if tactic.With.sep() == "\n":
                    for case in tactic.With.args:
                        case.echo()
                elif hasattr(tactic, 'sequential_tactic_combinator') and tactic.sequential_tactic_combinator:
                    block = tactic.sequential_tactic_combinator.arg
                    if isinstance(block, LeanTacticBlock):
                        block.echo()
                    else:
                        tactic.sequential_tactic_combinator.echo()
            elif hasattr(tactic, 'sequential_tactic_combinator') and tactic.sequential_tactic_combinator:
                tactic.sequential_tactic_combinator.echo()
        elif isinstance(tactic, LeanTacticBlock):
            tactic.echo()
        return self

    def isProp(self, vars):
        if len(self.args) == 1:
            return self.args[0].isProp(vars)

class LeanModule(LeanStatements, LeanMultipleLine):
    @property
    def root(self):
        return self
    
    stack_priority = -3

    @staticmethod
    def merge_proof(proof, echo, syntax=None):
        proof = proof.args
        if isinstance(proof[0], LeanLineComment) and proof[0].text == 'proof':
            proof = proof[1:]

        proof = [stmt for stmt in proof if not isinstance(stmt, LeanCaret)]
        code = []
        last = []
        statements = []
        for s in proof:
            statements.extend(s.split(syntax))

        if echo:
            for stmt in statements:
                echo_obj = stmt.getEcho()
                if echo_obj:
                    code.append([last, echo_obj.line if isinstance(echo_obj.line, int) else None])
                    last = []
                else:
                    last.append(stmt)
        else:
            for stmt in statements:
                if isinstance(stmt, (Lean_have, LeanTactic)):
                    last.append(stmt)
                    code.append([last, None])
                    last = []
                else:
                    last.append(stmt)

        if last:
            code.append([last, None])

        formatted = []
        for item in code:
            lean_str = "\n".join([
                re.sub(r"^  ", "", str(stmt).rstrip("\n")) 
                for stmt in item[0]
            ])
            formatted.append({
                'lean': lean_str,
                'latex': item[1]
            })

        return formatted

    def insert(self, caret, func, type):
        if self.args and self.args[-1] is caret:
            if isinstance(caret, LeanCaret):
                self.args.append(func(caret, self.indent))
                return caret
        return caret

    def decode(self, json_data, latex):
        if json_data:
            key, latexFormat = next(iter(json_data.items()))
            try:
                line = int(key)
            except ValueError:
                line = key

            if line in latex:
                if not isinstance(latex[line], list):
                    latex[line] = [latex[line]]
                latex[line].append(latexFormat)
            else:
                latex[line] = latexFormat

    def echo2vue(self, leanFile):
        leanCode = self.echo()
        leanEchoFile = re.sub(r'\.lean$', '.echo.lean', leanFile)

        if not Path(leanEchoFile).exists():
            Path(leanEchoFile).touch()

        with open(leanEchoFile, 'w') as f:
            f.write(str(leanCode))

        os.chdir(str(Path(__file__).parents[2]))

        imports = [
            imp for imp in leanCode.args
            if isinstance(imp, Lean_import) and 
            imp.arg.startswith('Lemma.') and 
            self.is_olean_outdated(imp.arg)
        ]

        lakePath = self.get_lake_path()
        if imports:
            import_str = " ".join(str(imp) for imp in imports)
            cmd = f'{lakePath} setup-file "{leanEchoFile}" Init {import_str}'
            if os.name == 'posix':
                subprocess.run(cmd, shell=True)
            else:
                self.exec_with_env(cmd)

        cmd = (
            f'{lakePath} env lean -D"linter.unusedTactic=false" '
            f'-D"linter.dupNamespace=false" -D"diagnostics.threshold=1000" '
            f'"{leanEchoFile}"'
        )
        output_array = self.run_cmd(cmd)

        latex = {}
        errors = []
        leanCode.set_line(1)

        end = leanCode.args[-1]
        if end.line != str(leanCode).count('\n') + 1:
            errors.append({
                'code': '',
                'line': end.line,
                'type': 'error',
                'info': 'the line count of *.echo.lean file is not correct'
            })

        echo_codes = None
        for line in output_array:
            try:
                json_data = json.loads(line)
                if json_data:
                    self.decode(json_data, latex)
                    continue
            except json.JSONDecodeError:
                pass

            match = re.match(
                r'([\w/]+)\.lean:(\d+):(\d+): (\w+): (.+)$',
                line
            )
            if match:
                if echo_codes is None:
                    with open(leanEchoFile, 'rb') as f:
                        encoding = chardet.detect(f.read())['encoding']
                    with open(leanEchoFile, 'r', encoding=encoding) as f:
                        echo_codes = f.readlines()

                file, line, col, err_type, info = match.groups()
                line = int(line)
                code = echo_codes[line-1].rstrip()
                errors.append({
                    'code': code,
                    'line': line,
                    'col': int(col) - 2,
                    'type': err_type,
                    'info': info
                })
            elif errors:
                errors[-1]['info'] += "\n" + line

        for node in leanCode.traverse():
            if (isinstance(node, LeanTactic) and 
                node.func == 'echo' and 
                isinstance(node.line, int)):
                node.line = latex.get(node.line)

        line_keys = sorted(int(k) for k in latex.keys() if str(k).isdigit())
        indices_to_delete = []
        for i, err in enumerate(errors):
            code = err['code']
            offset = 0
            if re.match(r" +echo ", code):
                if (err['type'] == 'error' and err['info'] == "no goals to be solved"):
                    offset = 1
                else:
                    indices_to_delete.append(i)
                    continue
            else:
                offset = -1
            err['line'] -= sum(1 for k in line_keys if k < err['line']) + offset

        for i in sorted(indices_to_delete, reverse=True):
            del errors[i]

        leanCode.args.pop(0)
        result = leanCode.render2vue(True)
        result['error'].extend(errors)
        return result

    def array_push(self, vars, lhs, rhs):
        if isinstance(lhs, LeanToken):
            args = [lhs, rhs]
            while isinstance(args[-1], Lean_rightarrow):
                last = args.pop()
                args.extend([last.lhs, last.rhs])
            vars.append(args)
        elif isinstance(lhs, LeanArgsSpaceSeparated):
            for item in lhs.args:
                self.array_push(vars, item, rhs)

    def parse_vars(self, implicit):
        vars = []
        for brace in implicit:
            if isinstance(brace, LeanBrace) and isinstance(brace.arg, LeanColon):
                self.array_push(vars, brace.arg.lhs, brace.arg.rhs)
        return {str(v[0]): str(v[1]) for v in vars}

    def parse_vars_default(self, default):
        vars = []
        for paren in default:
            if (isinstance(paren, LeanParenthesis) and 
                isinstance(paren.arg, LeanColon)):
                self.array_push(vars, paren.arg.lhs, paren.arg.rhs)
        return vars

    def render2vue(self, echo, modify=None, syntax=None):
        self.relocate_last_comment()
        imports = []
        opens = []
        defs = []
        lemmas = []
        dates = {}
        errors = []
        comment = None

        for stmt in self.args:
            if isinstance(stmt, Lean_import):
                imports.append(str(stmt.arg))
            elif isinstance(stmt, Lean_lemma) and isinstance(stmt.assignment, LeanAssign):
                declspec = stmt.assignment.lhs
                if isinstance(declspec, LeanColon):
                    # Process lemma attributes
                    attribute = None
                    if stmt.attribute:
                        attr_arg = stmt.attribute.arg
                        if isinstance(attr_arg, LeanBracket):
                            attr_arg = attr_arg.arg
                            if isinstance(attr_arg, LeanArgsCommaSeparated):
                                attribute = [str(arg) for arg in attr_arg.args]
                            else:
                                attribute = [str(attr_arg)]

                    # Process implications
                    imply = declspec.rhs.args
                    if isinstance(imply[0], LeanLineComment) and imply[0].text == 'imply':
                        imply = imply[1:]

                    # Format Lean and LaTeX outputs
                    imply_lean = "\n".join(
                        re.sub(r"^  ", "", str(s).rstrip("\n")) 
                        for s in imply
                    )
                    by_type = ''
                    if isinstance(stmt.assignment.rhs, Lean_by):
                        by_type = 'by'
                    elif isinstance(stmt.assignment.rhs, Lean_calc):
                        by_type = 'calc'

                    assignment = f" :={f' {by_type}' if by_type else ''}"
                    imply_lean += assignment

                    if len(imply) > 1 and isinstance(imply[0], Lean_let):
                        imply_latex = "\\\\\n".join(
                            f"&{s.toLatex(syntax)}&&" for s in imply
                        )
                        imply_latex = f"\\begin{{align}}\n{imply_latex}\n\\end{{align}}{assignment}"
                    else:
                        imply_latex = "\n".join(
                            s.toLatex(syntax) for s in imply
                        ) + f"\\tag*{{{assignment}}}"

                    imply_data = {
                        'lean': imply_lean,
                        'latex': imply_latex
                    }

                    # Process declaration spec
                    if isinstance(declspec.lhs, LeanToken):
                        name = declspec.lhs
                        declspec_args = []
                    else:
                        name, ds = declspec.lhs.args
                        declspec_args = ds.args

                    # Extract implicit/instance arguments
                    inst_implicit = []
                    implicit = []
                    decidables = []
                    given_idx = None

                    for i, arg in enumerate(declspec_args):
                        if isinstance(arg, LeanBracket):
                            inst_implicit.append(str(arg))
                            if (isinstance(arg.arg, LeanArgsSpaceSeparated) and 
                                len(arg.arg.args) == 2):
                                lhs, rhs = arg.arg.args
                                if (isinstance(lhs, LeanToken) and lhs.text == 'Decidable' and isinstance(rhs, LeanToken)):
                                    decidables.append(str(rhs))
                        elif isinstance(arg, LeanBrace):
                            arg.toLatex(syntax)
                            implicit.append(arg)
                        elif (isinstance(arg, LeanArgsSpaceSeparated) and 
                              arg.args):
                            if isinstance(arg.args[0], LeanBracket):
                                inst_implicit.append(str(arg))
                            elif isinstance(arg.args[0], LeanBrace):
                                implicit.append(arg)
                            else:
                                errors.append({
                                    'code': str(arg),
                                    'line': 0,
                                    'info': f"lemma {name} is not well-defined",
                                    'type': 'linter'
                                })
                        elif isinstance(arg, LeanLineComment):
                            if arg.text == 'given':
                                given_idx = i + 1
                                break
                        elif isinstance(arg, LeanParenthesis):
                            declspec_args.insert(i, LeanLineComment('given', arg.indent, arg.parent))
                            given_idx = i
                            if modify is not None:
                                modify = True
                            break

                    # Process 'given' section
                    given = []
                    explicit = []
                    if given_idx is not None:
                        given_data = declspec_args[given_idx:]
                        latex_list = []
                        vars_data = None

                        for item in given_data:
                            if isinstance(item, LeanParenthesis) and isinstance(item.arg, LeanColon):
                                if vars_data is None:
                                    vars_data = self.parse_vars(implicit)
                                    for p in decidables:
                                        vars_data[p] = "Prop"
                                if item.arg.rhs.isProp(vars_data):
                                    latex_list.append((
                                        item.arg.rhs.toLatex(syntax),
                                        f"{item.arg.lhs}"
                                    ))
                                else:
                                    break
                            elif isinstance(item, LeanLineComment):
                                latex_list.append(None)
                            else:
                                break

                        explicit = [
                            s + ' :' for s in map(str, given_data[len(latex_list):])
                        ]
                        given_data = given_data[:len(latex_list)]

                        if latex_list:
                            latex_list[-1] = (latex_list[-1][0], latex_list[-1][1] + ':')

                        given = []
                        for lean, latex in zip(given_data, latex_list):
                            data = {'lean' : str(lean)}
                            if latex:
                                data['latex'] = latex
                            else:
                                data['insert'] = True
                            given.append(data)
                    # Process proof
                    proof_data = {}
                    if by_type:
                        proof_data[by_type] = self.merge_proof(
                            stmt.assignment.rhs.arg, echo, syntax
                        )
                    else:
                        proof_data = self.merge_proof(
                            stmt.assignment.rhs, echo, syntax
                        )

                    lemmas.append({
                        'comment': comment,
                        'accessibility': str(stmt.accessibility),
                        'attribute': attribute,
                        'name': str(name),
                        'instImplicit': "\n".join(inst_implicit),
                        'implicit': "\n".join(map(str, implicit)),
                        'given': given,
                        'explicit': "\n".join(explicit),
                        'imply': imply_data,
                        'proof': proof_data
                    })
                    comment = None
                else:
                    errors.append({
                        'code': str(declspec),
                        'line': 0,
                        'info': "declspec of lemma must be of LeanColon Type",
                        'type': 'linter'
                    })
            elif isinstance(stmt, Lean_def):
                defs.append(str(stmt))
            elif isinstance(stmt, Lean_open):
                arg = stmt.arg
                if isinstance(arg, LeanArgsSpaceSeparated):
                    if len(arg.args) == 2 and isinstance(arg.args[1], LeanParenthesis):
                        open_item = {
                            str(arg.args[0]): (
                                [str(a) for a in arg.args[1].arg.args] 
                                if isinstance(arg.args[1].arg, LeanArgsSpaceSeparated) 
                                else [str(arg.args[1].arg.arg)]
                            )
                        }
                    else:
                        open_item = [str(a) for a in arg.args]
                else:
                    open_item = [str(arg)]
                opens.append(open_item)
            elif isinstance(stmt, LeanLineComment):
                match = re.match(r'^(created|updated) on (\d{4}-\d{2}-\d{2})$', stmt.text)
                if match:
                    dates[match.group(1)] = match.group(2)
                else:
                    comment = stmt.text
            elif isinstance(stmt, LeanBlockComment):
                comment = stmt.text

        return {
            'imports': imports,
            'open': opens,
            'def': defs,
            'lemma': lemmas,
            'date': dates,
            'error': errors,
        }

    def import_module(self, module):
        parts = module.split('.')
        module_obj = None
        for token in parts:
            token_obj = LeanToken(token, 0)
            if module_obj:
                module_obj = LeanProperty(module_obj, token_obj, 0)
            else:
                module_obj = token_obj
        self.args.insert(0, Lean_import(module_obj, 0))

    def echo(self):
        self.import_module('sympy.Basic')
        for i in range(len(self.args)):
            if isinstance(self.args[i], Lean_import):
                continue
            self.args[i] = self.args[i].echo()
        return self

class LeanCommand(LeanUnary):
    def is_indented(self):
        return False

    def strFormat(self):
        return f"{self.operator} %s"

    def latexFormat(self):
        return f"{self.command} %s"

    def toJson(self):
        return {
            self.func: self.arg.toJson()
        }

class Lean_import(LeanCommand):
    def push_attr(self, caret):
        if caret is self.arg:
            new = LeanCaret(self.indent)
            self.arg = LeanProperty(self.arg, new, self.indent)
            return new
        raise Exception(f"{__name__} is unexpected for {self.__class__.__name__}")

    stack_priority = 27
    operator = command = 'import'

    def append(self, func, type_):
        if isinstance(func, str):
            new = LeanCaret(self.indent)
            self.sql = eval(func)(new)
            self.sql.parent = self
            return new
        raise Exception(f"{__name__} is unexpected for {self.__class__.__name__}")

class Lean_open(LeanCommand):
    def push_attr(self, caret):
        if caret == self.arg:
            new = LeanCaret(self.indent)
            self.arg = LeanProperty(self.arg, new, self.indent)
            return new
        raise Exception(f"{__name__} is unexpected for {self.__class__.__name__}")

    stack_priority = 27
    operator = command = 'open'

    def append(self, func, type_):
        if isinstance(func, str):
            new = LeanCaret(self.indent)
            cls = globals().get(func)  # Get class by name from global scope
            if not cls:
                raise ValueError(f"Class {func} not found")
            self.sql = cls(new)
            self.sql.parent = self
            return new
        raise Exception(f"{__name__} is unexpected for {self.__class__.__name__}")

class Lean_namespace(LeanCommand):
    operator = command = 'namespace'

class LeanBar(LeanUnary):
    def is_indented(self):
        return True

    def strFormat(self):
        return f"{self.operator} %s"

    def latexFormat(self):
        return f"{self.command} %s"

    @property
    def stack_priority(self):
        # must be >= LeanAssign::$input_priority
        return LeanAssign.input_priority

    @property
    def operator(self):
        return '|'

    @property
    def command(self):
        return '|'

    def echo(self):
        self.arg.echo()
        return self

    def split(self, syntax=None):
        arrow = self.arg
        if isinstance(arrow, LeanRightarrow):
            this = copy(self)
            statements = [this]
            arrow = this.arg
            stmts = arrow.rhs
            if isinstance(stmts, LeanStatements):
                arrow.rhs = LeanCaret(arrow.indent)
                for stmt in stmts.args:
                    statements.extend(stmt.split(syntax))
            return statements
        return [self]

    def insert_comma(self, caret):
        if self.args and caret is self.args[-1]:
            new = LeanCaret(self.indent)
            self.replace(caret, LeanArgsCommaSeparated([caret, new], self.indent))
            return new
        raise Exception(f"{self.__class__.__name__}.insert_comma is unexpected for {caret}")

class LeanRightarrow(LeanBinary):
    input_priority = 20  # same as LeanColon.input_priority

    def sep(self):
        if isinstance(self.rhs, LeanStatements):
            return "\n"
        elif isinstance(self.rhs, LeanCaret):
            return ''
        else:
            return ' '

    def is_indented(self):
        return False

    def strFormat(self):
        sep = self.sep()
        lhs_format = "%s"
        if not isinstance(self.lhs, LeanCaret):
            lhs_format += ' '
        return f"{lhs_format}{self.operator}{sep}%s"

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.indent <= indent and isinstance(caret, LeanCaret) and caret == self.rhs:
            new_indent = self.indent + 2 if indent == self.indent else indent
            caret.indent = new_indent
            self.rhs = LeanStatements([caret], new_indent)
            for i in range(1, newline_count):
                caret = LeanCaret(new_indent)
                self.rhs.push(caret)
            return caret
        return super().insert_newline(caret, newline_count, indent, **kwargs)

    @property
    def operator(self):
        return '=>'

    def relocate_last_comment(self):
        self.rhs.relocate_last_comment()

    def echo(self):
        token = []
        parent = self.parent
        if isinstance(parent, LeanBar):
            parent = parent.parent
            if isinstance(parent, Lean_with):
                parent = parent.parent
                if isinstance(parent, (Lean_match, LeanTactic)) and (isinstance(parent, LeanTactic) and parent.func == 'induction'):
                    token.append(LeanToken('⊢', self.rhs.indent))
                    subject = parent.args[0]
                    if isinstance(subject, LeanArgsCommaSeparated):
                        for sujet in subject.args:
                            if isinstance(sujet, LeanColon):
                                token.append(sujet.lhs)
                    elif isinstance(subject, LeanColon):
                        token.append(subject.lhs)

        expr = self.lhs
        if isinstance(expr, LeanArgsSpaceSeparated):
            first_arg = expr.args[0]
            if isinstance(first_arg, LeanToken):
                func = first_arg.text
            elif isinstance(first_arg, LeanProperty) and isinstance(first_arg.lhs, LeanCaret) and isinstance(first_arg.rhs, LeanToken):
                func = first_arg.rhs.text
            else:
                func = None

            if func in [
                'succ', 'ofNat', 'negSucc'
            ]:
                start = 2
            elif func == 'cons':
                start = 3
            else:
                start = 1
            token.extend(expr.args[start:])
        elif isinstance(expr, LeanAngleBracket) and isinstance(expr.arg, LeanArgsCommaSeparated):
            token.extend(expr.arg.args[1:])
        elif isinstance(expr, LeanArgsCommaSeparated):
            for arg in expr.args:
                if isinstance(arg, LeanAngleBracket) and isinstance(arg.arg, LeanArgsCommaSeparated):
                    token.append(arg.arg.args[1])

        stmt = self.rhs
        stmt.echo()
        if token and isinstance(stmt, LeanStatements):
            indent = stmt.args[0].indent
            if len(token) > 1:
                adjusted_tokens = [LeanToken(tok.arg, indent) if isinstance(tok, LeanToken) else tok.clone() for tok in token]
                for tok in adjusted_tokens:
                    tok.indent = indent
                token_obj = LeanArgsCommaSeparated(adjusted_tokens, indent)
            else:
                token_obj = token[0].clone() if hasattr(token[0], 'clone') else token[0]
                token_obj.indent = indent

            stmt.unshift(LeanTactic('echo', token_obj, indent))
        return self

    def insert(self, caret, func, token_type):
        if self.rhs is caret and isinstance(caret, LeanCaret):
            new = func(caret, caret.indent)
            self.replace(caret, new)
            return caret
        if self.parent:
            return self.parent.insert(self, func, token_type)

class Lean_rightarrow(LeanBinary):
    input_priority = 25  # right associative operator

    def sep(self):
        return "\n" if isinstance(self.rhs, LeanStatements) else ' '

    def is_indented(self):
        return isinstance(self.parent, LeanStatements)

    def strFormat(self):
        sep = self.sep()
        return f"%s {self.operator}{sep}%s"

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.indent <= indent and isinstance(caret, LeanCaret) and caret is self.rhs:
            if indent == self.indent:
                indent = self.indent + 2
            caret.indent = indent
            self.rhs = LeanStatements([caret], indent)
            for i in range(1, newline_count):
                caret = LeanCaret(indent)
                self.rhs.push(caret)
            return caret

        return super().insert_newline(caret, newline_count, indent, **kwargs)

    stack_priority = 24
    operator = '→'

    def isProp(self, vars):
        lhs, rhs = self.args
        # Process LHS
        if isinstance(lhs, LeanToken):
            if vars.get(str(lhs), 'Prop') == 'Prop':
                lhs_ok = True
            else:
                lhs_ok = lhs.isProp(vars)
        else:
            lhs_ok = lhs.isProp(vars)
        # Process RHS
        if isinstance(rhs, LeanToken):
            if vars.get(str(rhs), 'Prop') == 'Prop':
                rhs_ok = True
            else:
                rhs_ok = rhs.isProp(vars)
        else:
            rhs_ok = rhs.isProp(vars)

        return lhs_ok and rhs_ok

class Lean_mapsto(LeanBinary):
    def sep(self):
        return "\n" if isinstance(self.rhs, LeanStatements) else ' '

    def is_indented(self):
        return False

    def strFormat(self):
        sep = self.sep()
        return f"%s {self.operator}{sep}%s"

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.indent <= indent and isinstance(caret, LeanCaret) and caret is self.rhs:
            if indent == self.indent:
                indent = self.indent + 2
            caret.indent = indent
            self.rhs = LeanStatements([caret], indent)
            for i in range(1, newline_count):
                caret = LeanCaret(indent)
                self.rhs.push(caret)
            return caret
        return super().insert_newline(caret, newline_count, indent, **kwargs)

    @property
    def stack_priority(self):
        return 23

    @property
    def operator(self):
        return '↦'

class Lean_leftarrow(LeanUnary):
    def strFormat(self):
        return f"{self.operator} %s"

    def latexFormat(self):
        return f"{self.command} %s"

    @property
    def operator(self):
        return '←'

class Lean_lnot(LeanUnary, LeanProp):
    input_priority = 50

    def is_indented(self):
        return isinstance(self.parent, LeanStatements)

    def strFormat(self):
        return f"{self.operator}%s"

    def latexFormat(self):
        return f"{self.command} %s"

    operator = '¬'

class LeanNot(LeanUnary, LeanProp):
    input_priority = 50

    def is_indented(self):
        return isinstance(self.parent, LeanStatements)

    def strFormat(self):
        return f"{self.operator}%s"

    def latexFormat(self):
        return f"{self.command} %s"

    operator = '!'
    command = r'\text{!}'

class Lean_match(LeanArgs):
    def __init__(self, subject, indent, parent=None):
        super().__init__([subject], indent, parent)

    def insert(self, caret, func, type):
        if not self.With and func == 'Lean_with':
            caret = LeanCaret(self.indent)
            with_obj = eval(func)(caret, self.indent)
            self.With = with_obj
            return caret
        raise Exception(f"{self.insert.__name__} is unexpected for {self.__class__.__name__}")

    def is_indented(self):
        return True

    def strFormat(self):
        if self.With:
            return f"{self.operator} %s %s"
        return f"{self.operator} %s"

    def latexFormat(self):
        if self.With:
            cases = self.With.args
            cases_str = " \\\\ ".join(["%s"] * len(cases))
            return f"\\begin{{cases}} {cases_str} \\end{{cases}}"
        return "match\\ %s"

    def latexArgs(self, syntax=None):
        subject = self.subject.toLatex(syntax)
        if self.With:
            cases = self.With.args
            return [
                f"{{{value.toLatex(syntax)}}} & {{\\color{{blue}}\\text{{if}}}}\\ \\: {subject}\\ =\\ {arg.lhs.toLatex(syntax)}"
                for arg in cases
                for value in [arg.rhs]
            ]
        return [subject]

    @property
    def stack_priority(self):
        return LeanColon.input_priority - 1
    @property
    def subject(self):
        return self.args[0]
    @property
    def With(self):
        if len(self.args) > 1:
            return self.args[1]
    @property
    def operator(self):
        return 'match'

    @subject.setter
    def subject(self, value):
        self.args[0] = value
        value.parent = self
    @With.setter
    def With(self, value):
        self.args[1] = value
        value.parent = self

    def insert_comma(self, caret):
        if caret == self.subject:
            caret = LeanCaret(self.indent)
            self.subject = LeanArgsCommaSeparated([self.subject, caret], self.indent)
            return caret
        if self.parent:
            return self.parent.insert_comma(self)

    def relocate_last_comment(self):
        if isinstance(self.With, Lean_with):
            self.With.relocate_last_comment()

    def insert_tactic(self, caret, token, **kwargs):
        if isinstance(caret, LeanCaret):
            return self.insert_word(caret, token, **kwargs)
        return super().insert_tactic(caret, token, **kwargs)

    def split(self, syntax=None):
        if With := self.With:
            stored_args = With.args
            this = copy(self)
            with_clone = copy(self.With)
            with_clone.args = []
            this.With = with_clone
            statements = [this]
            for stmt in stored_args:
                statements.extend(stmt.split(syntax))
            return statements
        return [self]

    def isProp(self, vars):
        cases = self.With.args
        case = cases[0] if cases else None
        if isinstance(case, LeanBar):
            arrow = case.arg
            if isinstance(arrow, LeanRightarrow):
                return arrow.rhs.isProp(vars)

class LeanITE(LeanArgs):
    input_priority = 60

    def __init__(self, If, indent, parent=None):
        super().__init__([If], indent, parent)

    def insert_then(self, caret):
        if self.then is None:
            caret = LeanCaret(self.indent + 2)
            self.then = caret
            return caret
        raise Exception(f"{self.__class__.__name__}.insert_then is unexpected")

    def insert_else(self, caret):
        if self.Else is None:
            caret = LeanCaret(self.indent + 2)
            self.Else = caret
            return caret
        if self.parent:
            return self.parent.insert_else(self)

    def insert_if(self, caret):
        if isinstance(caret, LeanCaret):
            if caret == self.Else:
                self.Else = LeanITE(caret, self.indent)
                return caret
            if caret == self.then:
                self.then = LeanITE(caret, self.indent + 2)
                return caret
        raise Exception(f"{self.__class__.__name__}.insert_if is unexpected")

    def insert_colon(self, caret, **kwargs):
        if caret == self.If:
            new = LeanCaret(caret.indent)
            self.replace(caret, LeanColon(caret, new, caret.indent))
            return new
        return caret.push_binary('LeanColon', **kwargs)

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if (caret == self.then or caret == self.Else) and isinstance(caret, LeanCaret):
            return caret
        if self.parent:
            return self.parent.insert_newline(self, newline_count, indent, **kwargs)

    def is_indented(self):
        parent = self.parent
        return isinstance(parent, LeanStatements) or \
               (isinstance(parent, LeanITE) and self == parent.then)

    def strFormat(self):
        indent_else = ' ' * self.indent
        sep = '\n' if isinstance(self.Else, LeanITE) else ' '
        then = '%s' if self.then is not None else ''
        Else = '%s' if self.Else is not None else ''
        return f"if %s then\n{then}\n{indent_else}else{sep}{Else}"

    def latexFormat(self):
        cases = 0
        Else = self
        while True:
            If, then, Else = Else.strip_parenthesis()
            cases += 1
            if not isinstance(Else, LeanITE):
                break
        placeholders = " \\\\ ".join(["%s"] * cases)
        return f"\\begin{{cases}} {placeholders} \\\\ {{%s}} & {{\\color{{blue}}\\text{{else}}}} \\end{{cases}}"

    def latexArgs(self, syntax=None):
        cases = []
        Else = self
        while True:
            If, then, Else = Else.strip_parenthesis()
            if_latex = If.toLatex(syntax)
            then_latex = then.toLatex(syntax)
            cases.append(f"{{{{{then_latex}}}}} & {{\\color{{blue}}\\text{{if}}}}\\ {if_latex}")
            if not isinstance(Else, LeanITE):
                break
        else_latex = Else.toLatex(syntax)
        return cases + [else_latex]

    @property
    def stack_priority(self):
        return 23

    @property
    def If(self):
        return self.args[0]

    @If.setter
    def If(self, value):
        self.args[0] = value
        value.parent = self

    @property
    def then(self):
        return self.args[1] if len(self.args) > 1 else None

    @then.setter
    def then(self, value):
        self.args[1] = value
        value.parent = self

    @property
    def Else(self):
        return self.args[2] if len(self.args) > 2 else None

    @Else.setter
    def Else(self, value):
        self.args[2] = value
        value.parent = self

    def set_line(self, line):
        self.line = line
        If = self.If
        then = self.then
        Else = self.Else
        line = If.set_line(line)
        line += 1
        line = then.set_line(line)
        line += 1
        if not isinstance(Else, LeanITE):
            line += 1
        return Else.set_line(line)

class LeanArgsSpaceSeparated(LeanArgs):
    input_priority = 72

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}

    def is_space_separated(self):
        return True

    def operand_count(self):
        return self.args[0].operand_count()

    def construct_prefix_tree(self):
        tokens = self.tokens_space_separated()
        tree = eval_prefix(tokens, lambda arg: arg.operand_count())
        return tree

    def tactic_block_info(self):
        if 'tactic_block_info' in self.cache:
            return self.cache['tactic_block_info']

        nodes = self.construct_prefix_tree()
        physic_index = [0]
        logic_index = [0]

        def visitor(n):
            if n.parent:
                args = n.parent.args
            else:
                args = nodes

            if i := args.index(n):
                for j in range(i - 1, -1, -1):
                    size = args[j].size()
                    if args[j].cache['physic_index'] + size == physic_index[0]:
                        logic_index[0] = max(logic_index[0], args[j].func.cache['index'] + size)
            elif n.parent and n.parent.func.is_parallel_operator():
                logic_index[0] += 1

            n.func.cache['index'] = logic_index[0]
            n.func.cache['size'] = n.size()
            n.cache['physic_index'] = physic_index[0]
            physic_index[0] += 1

        for node in nodes:
            node.traverse(visitor)

        tokens = self.tokens_space_separated()
        mapping = {}
        for token in reversed(tokens):
            if token.is_parallel_operator():
                token.cache['size'] = token.cache.get('size', 0) - 1
            idx = token.cache['index']
            if idx not in mapping:
                mapping[idx] = []
            mapping[idx].append(token)

        self.cache['tactic_block_info'] = mapping
        return mapping

    def tokens_space_separated(self):
        if 'tokens_space_separated' in self.cache:
            return self.cache['tokens_space_separated']

        tokens = []
        for arg in self.args:
            if isinstance(arg, LeanToken):
                tokens.append(arg)
            elif isinstance(arg, LeanAngleBracket):
                comma_tokens = arg.tokens_comma_separated()
                tokens.extend(comma_tokens)
            else:
                return []

        self.cache['tokens_space_separated'] = tokens
        return tokens

    def unique_token(self, indent):
        tokens = self.tokens_space_separated()
        if tokens:
            token_args = [token.text for token in tokens]
            if len(set(token_args)) == 1:
                token = copy(tokens[0])
                token.indent = indent
                return token

    def is_indented(self):
        parent = self.parent
        return (isinstance(parent, LeanStatements) or
                isinstance(parent, LeanArgsCommaNewLineSeparated) or
                isinstance(parent, LeanArgsNewLineSeparated) or
                (isinstance(parent, LeanITE) and
                 (self is parent.then or self is parent.else_)))

    def strFormat(self):
        return ' '.join(['%s'] * len(self.args))

    def latexFormat(self):
        args = self.args
        func = args[0]

        if self.is_Abs():
            return r'\left|{%s}\right|'
        if self.is_Bool():
            return r'\left|{%s}\right|'

        if isinstance(func, LeanToken):
            arg_count = len(args)
            token_value = func.text
            if arg_count == 2:
                if token_value in [
                    'exp', 'cexp'
                ]:
                    return r'{\color{RoyalBlue} e} ^ {%s}'
                elif token_value in [
                    'arcsin', 'arccos', 'arctan', 'sin', 'cos', 'tan', 'arg'
                ]:
                    return f"\\{token_value} {{{{%s}}}}"
                elif token_value in [
                    'arcsec', 'arccsc', 'arccot', 'arcsinh', 'arccosh', 'arctanh', 'arccoth'
                ]:
                    return f"{token_value}\\ {{{{%s}}}}"
                elif token_value == 'Ici':
                    return r'\left[%s, \infty\right)'
                elif token_value == 'Iic':
                    return r'\left(-\infty, %s\right]'
                elif token_value == 'Ioi':
                    return r'\left(%s, \infty\right)'
                elif token_value == 'Iio':
                    return r'\left(-\infty, %s\right)'
                elif token_value == 'Zeros':
                    return r'\mathbf{0}_{%s}'
                elif token_value == 'Ones':
                    return r'\mathbf{1}_{%s}'
            elif arg_count == 3:
                if token_value == 'Ioc':
                    return r'\left(%s, %s\right]'
                elif token_value == 'Ioo':
                    return r'\left(%s, %s\right)'
                elif token_value == 'Icc':
                    return r'\left[%s, %s\right]'
                elif token_value == 'Ico':
                    return r'\left[%s, %s\right)'
                elif token_value == 'KroneckerDelta':
                    return r'\delta_{%s %s}'

        if isinstance(func, LeanProperty):
            if (isinstance(func.rhs, LeanToken) and func.rhs.text == 'fmod' and len(args) == 2):
                return r'{%s}{%s}'

        return r"\\ ".join(['{%s}'] * len(self.args))

    def is_Abs(self):
        args = self.args
        if len(args) != 2:
            return False
        func = args[0]
        return isinstance(func, LeanToken) and func.text == 'abs'

    def is_Bool(self):
        args = self.args
        if len(args) != 2:
            return False
        func = args[0]
        return (isinstance(func, LeanProperty) and 
                isinstance(func.rhs, LeanToken) and 
                func.rhs.text == 'toNat' and 
                isinstance(func.lhs, LeanToken) and 
                func.lhs.text == 'Bool')

    def latexArgs(self, syntax=None):
        if syntax is None:
            syntax = {}

        args = self.args
        func = args[0]

        if self.is_Abs():
            stripped_args = self.strip_parenthesis()
            arg_latex = stripped_args[1].toLatex(syntax)
            return [arg_latex]

        if self.is_Bool():
            stripped_args = self.strip_parenthesis()
            arg_latex = stripped_args[1].toLatex(syntax)
            return [arg_latex]

        if isinstance(func, LeanToken):
            func_value = func.text
            syntax[func_value] = True
            arg_count = len(args)
            if arg_count == 2:
                if func_value in [
                    'exp', 'cexp'
                ]:
                    stripped_args = self.strip_parenthesis()
                    arg_latex = stripped_args[1].toLatex(syntax)
                    return [arg_latex]
                elif func_value in [
                    'arcsin', 'arccos', 'arctan', 'sin', 'cos', 'tan', 'arg', 'arcsec', 'arccsc', 'arccot', 'arcsinh', 'arccosh', 'arctanh', 'arccoth'
                ]:
                    arg = args[1]
                    if (isinstance(arg, LeanParenthesis) and 
                        isinstance(arg.arg, LeanDiv)):
                        arg = arg.arg
                    arg_latex = arg.toLatex(syntax)
                    return [arg_latex]
                elif func_value in [
                    'Ici', 'Iic', 'Ioi', 'Iio', 'Zeros', 'Ones'
                ]:
                    stripped_args = self.strip_parenthesis()
                    arg_latex = stripped_args[1].toLatex(syntax)
                    return [arg_latex]
            elif arg_count == 3:
                if func_value in [
                    'Ioc', 'Ioo', 'Icc', 'Ico'
                ]:
                    stripped_args = self.strip_parenthesis()
                    lhs_latex = stripped_args[1].toLatex(syntax)
                    rhs_latex = stripped_args[2].toLatex(syntax)
                    return [lhs_latex, rhs_latex]
                elif func_value == 'KroneckerDelta':
                    lhs_latex = args[1].toLatex(syntax)
                    rhs_latex = args[2].toLatex(syntax)
                    return [lhs_latex, rhs_latex]

        return super().latexArgs(syntax)

    def insert_word(self, caret, word, **kwargs):
        new = LeanToken(word, self.indent, **kwargs)
        self.push(new)
        return new

    stack_priority = 72

    def insert_unary(self, caret, func_class, **kwargs):
        if caret is self.args[-1] if self.args else False:
            indent = self.indent
            if isinstance(caret, LeanCaret):
                new = func_class(caret, indent)
                self.replace(caret, new)
            else:
                caret = LeanCaret(indent)
                new = func_class(caret, indent)
                self.push(new)
                caret = caret
            return caret
        else:
            raise Exception(f"{self.__class__.__name__}.insert_unary is unexpected for {caret.__class__.__name__}")

    def get_type(self, vars_dict, arg):
        if isinstance(arg, LeanToken):
            return vars_dict.get(arg.arg, '')
        elif isinstance(arg, LeanArgsSpaceSeparated):
            arg_types = [self.get_type(vars_dict, a) for a in arg.args]
            return getitem(vars_dict, *arg_types)
        else:
            return ''

    def isProp(self, vars_dict):
        arg_types = [self.get_type(vars_dict, arg) for arg in self.args]
        first_type = arg_types[0]
        if isinstance(first_type, dict) or hasattr(first_type, '__getitem__'):
            t = getitem(first_type, *arg_types[1:])
            return t == 'Prop'
        else:
            first_arg = self.args[0]
            if isinstance(first_arg, LeanToken) and first_arg.text == 'HEq':
                return True
            return False

    def insert(self, caret, func_class, type):
        if caret is (self.args[-1] if self.args else None) and not isinstance(caret, LeanCaret) and type != 'modifier':
            caret = LeanCaret(self.indent)
            new = func_class(caret, caret.indent)
            self.push(new)
            return caret
        elif self.parent:
            return self.parent.insert(self, func_class, type)

class LeanArgsNewLineSeparated(LeanArgs, LeanMultipleLine):
    def is_indented(self):
        return False

    def strFormat(self):
        return "\n".join(['%s'] * len(self.args))

    def latexFormat(self):
        return "\n".join(['{%s}'] * len(self.args))

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.indent > indent:
            return super().insert_newline(caret, newline_count, indent, **kwargs)

        if self.indent < indent:
            end = self.args[-1]
            if isinstance(end, (LeanToken, LeanProperty)):
                # function call
                caret = LeanCaret(indent)
                new = LeanArgsNewLineSeparated([caret], indent)
                caret = new.push_newlines(newline_count - 1)
                self.replace(end, LeanArgsIndented(end, new, self.indent))
                return caret
            raise Exception(f"insert_newline is unexpected for {type(self).__name__}")

        elif isinstance(self.parent, LeanAssign) and not isinstance(caret, LeanLineComment):
            return super().insert_newline(caret, newline_count, indent, **kwargs)
        else:
            if self.args[-1] == caret:
                for i in range(newline_count):
                    caret = LeanCaret(indent)
                    self.args.append(caret)
                return caret
            raise Exception(f"insert_newline is unexpected for {type(self).__name__}")

    @property
    def stack_priority(self):
        if isinstance(self.parent, Lean_calc):
            return 17
        return 47
    def relocate_last_comment(self):
        for index in range(len(self.args) - 1, -1, -1):
            end = self.args[index]
            if isinstance(end, LeanCaret) or end.is_comment():
                obj = self
                parent = None
                while obj:
                    parent = obj.parent
                    if isinstance(parent, LeanStatements):
                        break
                    obj = parent
                if parent:
                    last = self.args.pop()
                    idx = parent.args.index(obj) + 1
                    parent.args.insert(idx, last)
                    last.parent = parent
                    return parent.relocate_last_comment()
            else:
                return end.relocate_last_comment()

    def push_newlines(self, newline_count):
        for i in range(newline_count):
            self.args.append(LeanCaret(self.indent))
        return self.args[-1]

class LeanArgsIndented(LeanBinary):
    def sep(self):
        return "\n"

    def is_indented(self):
        return False

    def strFormat(self):
        sep = self.sep()
        return f"%s{sep}%s"

    def latexFormat(self):
        sep = self.sep()
        return f"%s{sep}%s"

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.indent > indent:
            return super().insert_newline(caret, newline_count, indent, **kwargs)

        if self.indent < indent:
            end = self.args[-1]
            if isinstance(end, (LeanToken, LeanProperty)):
                # function call
                caret = LeanCaret(indent)
                new = LeanArgsNewLineSeparated([caret], indent)
                caret = new.push_newlines(newline_count - 1)
                self.replace(end, LeanArgsIndented(end, new, self.indent))
                return caret
            raise Exception(f"insert_newline is unexpected for {self.__class__.__name__}")

        elif isinstance(self.parent, LeanAssign):
            return super().insert_newline(caret, newline_count, indent, **kwargs)
        else:
            if self.args[-1] is caret:
                for i in range(newline_count):
                    caret = LeanCaret(indent)
                    self.push(caret)
                return caret
            raise Exception(f"insert_newline is unexpected for {self.__class__.__name__}")

    @property
    def stack_priority(self):
        if isinstance(self.parent, Lean_calc):
            return 17
        return 47

    def relocate_last_comment(self):
        for i in range(len(self.args) - 1, -1, -1):
            end = self.args[i]
            if isinstance(end, LeanCaret) or end.is_comment():
                current = self
                parent = None
                while current:
                    parent = current.parent
                    if isinstance(parent, LeanStatements):
                        break
                    current = parent
                if parent:
                    last = self.args.pop()
                    index = parent.args.index(self)
                    parent.args.insert(index + 1, last)
                    last.parent = parent
                    return parent.relocate_last_comment()
            else:
                return end.relocate_last_comment()

class LeanArgsCommaSeparated(LeanArgs):

    def is_indented(self):
        return False

    def strFormat(self):
        return ", ".join(['%s'] * len(self.args))

    def latexFormat(self):
        return ", ".join(['{%s}'] * len(self.args))

    @property
    def stack_priority(self):
        if isinstance(self.parent, LeanBar):
            return LeanColon.input_priority
        return LeanColon.input_priority - 1

    def insert_comma(self, caret):
        caret = LeanCaret(self.indent)
        self.push(caret)
        return caret

    def insert_tactic(self, caret, token, **kwargs):
        if isinstance(caret, LeanCaret):
            return self.insert_word(caret, token, **kwargs)
        raise Exception(f"{self.__class__.__name__}.insert_tactic is unexpected for {caret.__class__.__name__}")

    def insert(self, caret, func, type):
        if self.args and self.args[-1] is caret:
            if isinstance(caret, LeanCaret):
                new = func(caret, caret.indent)
                self.replace(caret, new)
                return caret
        elif self.parent:
            return self.parent.insert(self, func, type)

    def tokens_comma_separated(self):
        tokens = []
        for arg in self.args:
            if isinstance(arg, LeanToken):
                tokens.append(arg)
            elif isinstance(arg, LeanAngleBracket):
                tokens.extend(arg.tokens_comma_separated())
        return tokens

class LeanArgsSemicolonSeparated(LeanArgs):
    def is_indented(self):
        return False

    def strFormat(self):
        return "; ".join(["%s"] * len(self.args))

    def latexFormat(self):
        return "; ".join(["{%s}"] * len(self.args))

    @property
    def stack_priority(self):
        return LeanColon.input_priority - 1

    def insert_semicolon(self, caret):
        caret = LeanCaret(self.indent)
        self.push(caret)
        return caret

    def insert_tactic(self, caret, token, **kwargs):
        if isinstance(caret, LeanCaret):
            return self.insert_word(caret, token, **kwargs)
        raise Exception(f"{self.__class__.__name__}.insert_tactic is unexpected for {caret.__class__.__name__}")

    def insert(self, caret, func, type):
        if self.args and self.args[-1] is caret:
            if isinstance(caret, LeanCaret):
                self.replace(caret, func(caret, caret.indent))
                return caret
            elif self.parent:
                return self.parent.insert(self, func, type)

class LeanArgsCommaNewLineSeparated(LeanArgs, LeanMultipleLine):
    def is_indented(self):
        return False

    def strFormat(self):
        return ",\n".join(['%s'] * len(self.args))

    def latexFormat(self):
        return ",\n".join(['{%s}'] * len(self.args))

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.indent > indent:
            return super().insert_newline(caret, newline_count, indent, **kwargs)

        if self.indent < indent:
            raise Exception(f"{self.__class__.__name__}.insert_newline is unexpected for {self.__class__.__name__}")
        else:
            if self.args[-1] == caret:
                for i in range(newline_count - 1):
                    caret = LeanCaret(indent)
                    self.push(caret)
                return caret
            raise Exception(f"{self.__class__.__name__}.insert_newline is unexpected for {self.__class__.__name__}")

    stack_priority = 17

    def insert_comma(self, caret):
        caret = LeanCaret(self.indent)
        self.push(caret)
        return caret

    def insert(self, caret, func, type):
        if self.args[-1] is caret:
            if isinstance(caret, LeanCaret):
                self.replace(caret, func(caret, caret.indent))
                return caret
        raise Exception(f"{self.__class__.__name__}.insert is unexpected for {self.__class__.__name__}")

class LeanSyntax(LeanArgs):

    @property
    def arg(self):
        return self.args[0]

    @arg.setter
    def arg(self, val):
        self.args[0] = val
        val.parent = self

    def insert(self, caret, func, type):
        if caret is self.args[-1]:
            caret = LeanCaret(self.indent)
            self.push(func(caret, self.indent))
            return caret
        raise Exception(f"LeanSyntax::insert is unexpected for {self.__class__.__name__}")

class LeanTactic(LeanSyntax):
    def __init__(self, func, arg, indent, parent=None):
        super().__init__([arg], indent, parent)
        self.func = func
        self.only = False

    def insert_line_comment(self, caret, comment):
        return self.push_line_comment(comment)

    def push_line_comment(self, comment):
        new = LeanLineComment(comment, self.indent)
        self.push(new)
        return new

    def getEcho(self):
        if self.func == 'echo':
            return self
        if self.func == 'try' and isinstance(self.arg, LeanTactic) and self.arg.func == 'echo':
            return self.arg

    @property
    def stack_priority(self):
        if isinstance(self.parent, Lean_by):
            return LeanColon.input_priority
        if self.func == 'obtain':
            return LeanAssign.input_priority - 1
        return LeanAssign.input_priority

    @property
    def arg(self):
        return self.args[0]

    @property
    def modifiers(self):
        return self.args[1:]

    @property
    def at(self):
        for arg in reversed(self.args):
            if isinstance(arg, Lean_at):
                return arg

    @property
    def with_(self):
        for arg in reversed(self.args):
            if isinstance(arg, Lean_with):
                return arg

    @property
    def sequential_tactic_combinator(self):
        for arg in reversed(self.args):
            if isinstance(arg, LeanSequentialTacticCombinator):
                return arg

    def is_indented(self) -> bool:
        parent = self.parent
        return not parent or isinstance(parent, LeanStatements) or isinstance(parent, LeanSequentialTacticCombinator) and self.indent >= parent.indent

    def strFormat(self):
        func = self.func
        if self.only:
            func += " only"
        if not isinstance(self.arg, LeanCaret):
            func += ' '
        return func + ' '.join(['%s'] * len(self.args))

    def latexFormat(self) -> str:
        return self.strFormat()

    def toJson(self):
        return {
            self.func: self.arg.toJson(),
            'only': self.only,
            'modifiers': [modifier.toJson() for modifier in self.modifiers]
        }

    def relocate_last_comment(self) -> None:
        arg = self.args[-1]
        if isinstance(arg, (LeanRightarrow, Lean_with)):
            arg.relocate_last_comment()

    def insert_only(self, caret):
        if caret is self.args[-1]:
            self.only = True
            return caret
        raise Exception(f"{self.insert_only.__name__} is unexpected for {self.__class__.__name__}")

    def has_tactic_block_followed(self) -> bool:
        # check the next statement:
        # if the next statement is a tactic block, skipping echoing ⊢ since it will be done in the next tactic block
        # if the next statement isn't a tactic block, echo ⊢ as usual
        if isinstance(self.parent, LeanStatements):
            stmts = self.parent.args
            for index in range(stmts.index(self) + 1, len(stmts)):
                stmt = stmts[index]
                if isinstance(stmt, LeanTacticBlock):
                    return True
                if not stmt.is_comment():
                    break

    def get_echo_token(self):
        if self.at:
            token = self.at.arg
            if isinstance(token, LeanArgsSpaceSeparated):
                token = LeanArgsCommaSeparated(
                    [copy(a) for a in token.args], 
                    self.indent
                )
        else:
            token = []
            goal = "⊢"
            if self.func in ('intro', 'by_contra'):
                arg = self.arg
                if isinstance(arg, LeanToken):
                    token.append(copy(arg))
                elif isinstance(arg, LeanArgsSpaceSeparated):
                    for arg in arg.tokens_space_separated():
                        if isinstance(arg, LeanToken):
                            token.append(copy(arg))
                        elif isinstance(arg, list):
                            token.extend(copy(a) for a in arg)
                elif isinstance(arg, LeanAngleBracket):
                    arg = arg.arg
                    if isinstance(arg, LeanToken):
                        token.append(copy(arg.arg))
                    elif isinstance(arg, LeanArgsCommaSeparated):
                        token = [copy(a) for a in arg.args]
            elif self.func in ('denote', "denote'"):
                if isinstance(self.arg, LeanColon):
                    var = self.arg.lhs
                    if isinstance(var, LeanToken):
                        token.append(copy(var))
                goal = None
            elif self.func == 'by_cases':
                if isinstance(self.arg, LeanColon):
                    var = self.arg.lhs
                    if isinstance(var, LeanToken):
                        if self.has_tactic_block_followed():
                            return
                        token.append(copy(var))
            elif self.func == 'split_ifs':
                if (with_ := self.with_) and with_.sep() == ' ':
                    if self.has_tactic_block_followed():
                        return
                    var = with_.args[0]
                    if var := var.tokens_space_separated():
                        token.append(copy(var[0]))
            elif self.func == "cases'":
                if (with_ := self.with_) and with_.sep() == ' ':
                    if self.sequential_tactic_combinator:
                        var = with_.args[0]
                        if var := var.unique_token(self.indent):
                            token.append(var)
            elif self.func == 'rcases':
                if (with_ := self.with_) and (tokens := with_.tokens_bar_separated()):
                    if self.has_tactic_block_followed():
                        return
                    arg = tokens[0]
                    if isinstance(arg, list):
                        token.extend(t for t in arg if t.text != 'rfl')
                    elif isinstance(arg, LeanToken) and arg.text != 'rfl':
                        token.append(arg)
            elif self.func == 'obtain':
                arg = arg.lhs
                if isinstance(arg, LeanAngleBracket):
                    for t in arg.tokens_comma_separated():
                        if t.text != 'rfl':
                            token.append(t)
                elif isinstance(arg, LeanBitOr):
                    tokens = arg.tokens_bar_separated()
                    if self.has_tactic_block_followed():
                        return
                    if tokens:
                        arg = tokens[0]
                        if isinstance(arg, list):
                            token.extend(t for t in arg if t.text != 'rfl')
                        elif arg.text != 'rfl':
                            token.append(arg)
            elif self.func == 'specialize':
                arg = self.arg
                if isinstance(arg, LeanArgsSpaceSeparated) and isinstance(arg := arg.args[0], LeanToken):
                    token.append(copy.copy(arg))
                goal = None 
            elif self.func in ('sorry', 'echo'):
                return

            if self.has_tactic_block_followed() or isinstance(self.parent, LeanSequentialTacticCombinator):
                ...
            elif goal:
                token.append(LeanToken(goal, self.indent))

            if not token:
                ...
            elif len(tokens) == 1:
                token = tokens[0]
            else:
                token = LeanArgsCommaSeparated(
                    token, 
                    self.indent
                )
        return token

    def echo(self):
        token = self.get_echo_token()
        if token:
            return [
                1, 
                self, 
                LeanTactic('echo', token, self.indent)
            ]
        if (sequential_tactic_combinator := self.sequential_tactic_combinator) and sequential_tactic_combinator.arg.indent:
            sequential_tactic_combinator.echo()
        return self

    def split(self, syntax=None):
        syntax[self.func] = True

        if (with_ := self.with_) and self.with_.sep() == "\n":
            this = copy(self)
            this.with_ = copy(self.with_)
            this.with_.args = []
            statements = [this]
            for stmt in with_.args:
                statements += stmt.split(syntax)
            return statements

        if (sequential_tactic_combinator := self.sequential_tactic_combinator):
            block = sequential_tactic_combinator.arg
            if isinstance(block, LeanTacticBlock):
                if isinstance(block.arg, LeanStatements):
                    this = copy(self)
                    block = this.sequential_tactic_combinator.arg
                    statements = block.arg.args
                    block.arg = LeanCaret(0)
                    array = [this]
                    for stmt in statements:
                        array += stmt.split(syntax)
                    return array
            elif isinstance(block, LeanTactic) and block.indent >= self.indent:
                this = copy(self)
                block = this.sequential_tactic_combinator.arg
                this.sequential_tactic_combinator.arg = LeanCaret(0)
                array = [this]
                array.extend(block.split(syntax))
                return array
        return [self]

    def insert_sequential_tactic_combinator(self, caret):
        if caret is self.args[-1]:
            caret = LeanCaret(0) # use 0 as the temporary indentation
            self.push(LeanSequentialTacticCombinator(caret, self.indent))
            return caret
        raise Exception(f"{self.insert_sequential_tactic_combinator.__name__} is unexpected for {self.__class__.__name__}")

    def insert_tactic(self, caret, type, **kwargs):
        if self.args and caret is self.args[-1] and isinstance(caret, LeanCaret):
            if self.func == 'try':
                caret.parent.replace(caret, LeanTactic(type, caret, self.indent))
                return caret
            else:
                return self.insert_word(caret, type, **kwargs)
        raise Exception(f"{self.insert_tactic.__name__} is unexpected for {self.__class__.__name__}")

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.indent < indent:
            if caret is self.arg and isinstance(caret, LeanArgsSpaceSeparated):
                new = LeanCaret(self.indent)
                caret.push(new)
                return new
        return super().insert_newline(caret, newline_count, indent, **kwargs)

    def insert_comma(self, caret):
        if caret is self.arg:
            if isinstance(caret, (LeanToken, LeanArithmetic, LeanPairedGroup)):
                new = LeanCaret(self.indent)
                self.replace(caret, LeanArgsCommaSeparated([caret, new], self.indent))
                return new
            if isinstance(caret, LeanArgsCommaSeparated):
                new = LeanCaret(self.indent)
                caret.push(new)
                return new
        return super().insert_comma(caret)

class Lean_by(LeanUnary):
    def is_indented(self):
        return isinstance(self.parent, LeanArgsCommaNewLineSeparated)

    def sep(self):
        return "\n" if isinstance(self.arg, LeanStatements) else ' '

    def strFormat(self):
        sep = self.sep()
        return f"{self.operator}{sep}%s"

    def latexFormat(self):
        sep = self.sep()
        return f"{self.command}\\ %s"

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.indent <= indent and isinstance(caret, LeanCaret) and caret == self.arg:
            if indent == self.indent:
                indent = self.indent + 2
            caret.indent = indent
            self.arg = LeanStatements([caret], indent)
            for i in range(1, newline_count):
                caret = LeanCaret(indent)
                self.arg.push(caret)
            return caret

        return super().insert_newline(caret, newline_count, indent, **kwargs)

    def relocate_last_comment(self):
        self.arg.relocate_last_comment()

    def echo(self):
        self.arg = self.arg.echo()
        return self

    def set_line(self, line):
        self.line = line
        if isinstance(self.arg, LeanStatements):
            line += 1
        return self.arg.set_line(line)

    operator = command = 'by'

    def insert_semicolon(self, caret):
        if caret is self.arg:
            caret = LeanCaret(self.indent)
            self.arg = LeanArgsSemicolonSeparated([self.arg, caret], self.indent)
            return caret
        return self.parent.insert_semicolon(self)

class Lean_from(LeanUnary):
    def is_indented(self):
        return isinstance(self.parent, LeanArgsCommaNewLineSeparated)

    def sep(self):
        return "\n" if isinstance(self.arg, LeanStatements) else ' '

    def strFormat(self):
        sep = self.sep()
        return f"{self.operator}{sep}%s"

    def latexFormat(self):
        sep = self.sep()
        return f"{self.command}{sep}%s"

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.indent <= indent and isinstance(caret, LeanCaret) and caret is self.arg:
            if indent == self.indent:
                indent = self.indent + 2
            caret.indent = indent
            self.arg = LeanStatements([caret], indent)
            for i in range(1, newline_count):
                caret = LeanCaret(indent)
                self.arg.push(caret)
            return caret

        return super().insert_newline(caret, newline_count, indent, **kwargs)

    def relocate_last_comment(self):
        self.arg.relocate_last_comment()

    def echo(self):
        self.arg = self.arg.echo()
        return self

    def set_line(self, line):
        self.line = line
        if isinstance(self.arg, LeanStatements):
            line += 1
        return self.arg.set_line(line)

    operator = command = 'from'

class Lean_calc(LeanUnary):
    def is_indented(self):
        return False

    def sep(self):
        return "\n" if isinstance(self.arg, LeanArgsNewLineSeparated) else ' '

    def strFormat(self):
        sep = self.sep()
        return f"{self.operator}{sep}%s"

    def latexFormat(self):
        sep = self.sep()
        return f"{self.command}{sep}%s"

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.indent <= indent and isinstance(caret, LeanCaret) and caret is self.arg:
            if indent == self.indent:
                indent = self.indent + 2
            caret.indent = indent
            self.arg = LeanArgsNewLineSeparated([caret], indent)
            return self.arg.push_newlines(newline_count - 1)
        return super().insert_newline(caret, newline_count, indent, **kwargs)

    def relocate_last_comment(self):
        self.arg.relocate_last_comment()

    operator= command = 'calc'

    def set_line(self, line):
        self.line = line
        if isinstance(self.arg, LeanArgsNewLineSeparated):
            line += 1
        return self.arg.set_line(line)

class Lean_MOD(LeanUnary):
    def is_indented(self):
        return False

    def sep(self):
        return ' '

    def strFormat(self):
        sep = self.sep()
        return f"{self.operator}{sep}%s"

    def latexFormat(self):
        sep = self.sep()
        return f"{self.command}\\{sep}%s"

    operator = 'MOD'
    command = '\\operatorname{MOD}'

class Lean_using(LeanUnary):
    def is_indented(self):
        return False

    def strFormat(self):
        return f"{self.operator} %s"

    def latexFormat(self):
        return f"{self.command} %s"

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.indent <= indent and isinstance(caret, LeanCaret) and caret is self.arg:
            if indent == self.indent:
                indent = self.indent + 2
            caret.indent = indent
            self.arg = LeanStatements([caret], indent)
            for i in range(1, newline_count):
                caret = LeanCaret(indent)
                self.arg.push(caret)
            return caret

        return super().insert_newline(caret, newline_count, indent, **kwargs)

    operator = command = 'using'

class Lean_at(LeanUnary):
    def is_indented(self):
        return False

    def strFormat(self):
        return f"{self.operator} %s"

    def latexFormat(self):
        return f"{self.command} %s"

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.indent <= indent and isinstance(caret, LeanCaret) and caret == self.arg:
            if indent == self.indent:
                indent = self.indent + 2
            caret.indent = indent
            self.arg = LeanStatements([caret], indent)
            for i in range(1, newline_count):
                caret = LeanCaret(indent)
                self.arg.push(caret)
            return caret

        return super().insert_newline(caret, newline_count, indent, **kwargs)

    @property
    def operator(self):
        return 'at'

    @property
    def command(self):
        return 'at'

class LeanIn(LeanUnary):
    def is_indented(self):
        return False

    def strFormat(self):
        return f"{self.operator} %s"

    def latexFormat(self):
        return f"{self.command} %s"

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.indent <= indent and isinstance(caret, LeanCaret) and caret is self.arg:
            if indent == self.indent:
                indent = self.indent + 2
            caret.indent = indent
            self.arg = LeanStatements([caret], indent)
            for i in range(1, newline_count):
                caret = LeanCaret(indent)
                self.arg.push(caret)
            return caret

        return super().insert_newline(caret, newline_count, indent, **kwargs)

    operator = command = 'in'

class Lean_generalizing(LeanUnary):

    def is_indented(self):
        return False

    def strFormat(self):
        return f"{self.operator} %s"

    def latexFormat(self):
        return f"{self.command} %s"

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if (
            self.indent <= indent and 
            isinstance(caret, LeanCaret) and 
            caret is self.arg
        ):
            adjusted_indent = indent
            if indent == self.indent:
                adjusted_indent = self.indent + 2
            caret.indent = adjusted_indent
            self.arg = LeanStatements([caret], adjusted_indent)
            for i in range(1, newline_count):
                caret = LeanCaret(adjusted_indent)
                self.arg.push(caret)
            return caret
        return super().insert_newline(caret, newline_count, indent, **kwargs)

    @property
    def operator(self):
        return 'generalizing'

    @property
    def command(self):
        return 'generalizing'

class LeanSequentialTacticCombinator(LeanUnary):
    def is_indented(self):
        return False

    def sep(self):
        return "\n" if isinstance(self.arg, LeanTacticBlock) or self.arg.indent > 0 else " "

    def strFormat(self):
        sep = self.sep()
        return f"{self.operator}{sep}%s"

    def latexFormat(self):
        return f"{self.command} %s"

    operator = command = '<;>'

    def insert_tactic(self, caret, type):
        if isinstance(caret, LeanCaret):
            self.arg = LeanTactic(type, caret, caret.indent)
            return caret
        raise Exception(f"{self.__class__.__name__}.insert_tactic is unexpected for {caret.__class__.__name__}")

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if isinstance(caret, LeanCaret) and caret == self.arg:
            if next_token in ('·', '.'):
                if indent == self.indent:
                    caret.indent = indent
                    return caret
            else:
                if indent > self.indent:
                    indent = self.indent + 2
                else:
                    indent = self.indent
                caret.indent = indent
                return caret
        return super().insert_newline(caret, newline_count, indent, **kwargs)

    def echo(self):
        if isinstance(self.arg, LeanTacticBlock):
            self.arg = self.arg.echo()
        elif self.arg.indent > 0:
            arg = self.arg
            indent = arg.indent
            echo = LeanTactic('echo', LeanToken('⊢', indent), indent)
            echo.push(LeanSequentialTacticCombinator(arg, indent))
            self.arg = echo
            arg.echo()
        return self

    def set_line(self, line):
        self.line = line
        if isinstance(self.arg, LeanTacticBlock) or self.arg.indent >= self.indent:
            line += 1
        return self.arg.set_line(line)

class LeanTacticBlock(LeanUnary):
    def is_indented(self):
        return True

    def strFormat(self):
        return f"{self.operator}\n%s"

    def latexFormat(self):
        return f"{self.command}\n%s"

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if caret == self.arg:
            if isinstance(caret, LeanCaret):
                if self.indent <= indent:
                    if indent == self.indent:
                        indent = self.indent + 2
                    caret.indent = indent
                    self.arg = LeanStatements([caret], indent)
                    for i in range(1, newline_count):
                        caret = LeanCaret(indent)
                        self.arg.push(caret)
                    return caret
            elif isinstance(caret, LeanStatements):
                block = caret
                if indent >= block.indent:
                    for i in range(newline_count):
                        caret = LeanCaret(block.indent)
                        block.push(caret)
                    return caret
            elif self.indent < indent:
                caret = LeanCaret(indent)
                self.arg.indent = indent
                self.arg = LeanStatements([self.arg, caret], indent)
                return caret

        return super().insert_newline(caret, newline_count, indent, **kwargs)

    def insert_line_comment(self, caret, comment):
        if isinstance(caret, LeanCaret):
            indent = self.indent + 2
            new = LeanLineComment(comment, indent)
            self.arg = LeanStatements([new], indent)
            return new
        raise Exception(f"insert_line_comment is unexpected for {type(self).__name__}")

    @property
    def operator(self):
        return '·'

    @property
    def command(self):
        return r'\cdot'

    def echo(self):
        statements = self.arg
        self.arg = statements.echo()
        if isinstance(statements, LeanStatements):
            if isinstance(self.parent, LeanSequentialTacticCombinator):
                if (isinstance(self.parent.parent, LeanTactic) and 
                    (with_ := self.parent.parent.with_) and 
                    (token := with_.unique_token(statements.indent))):
                    pass
                else:
                    token = LeanToken('⊢', statements.indent)
                statements.unshift(LeanTactic('echo', token, statements.indent))
            elif isinstance(self.parent, LeanStatements):
                index = self.parent.args.index(self)
                tacticBlockCount = 0
                for i in range(index - 1, -1, -1):
                    stmt = self.parent.args[i]
                    if stmt.is_comment():
                        continue
                    if isinstance(stmt, LeanTacticBlock):
                        tacticBlockCount += 1
                        continue
                    if isinstance(stmt, LeanTactic):
                        if stmt.func == 'echo':
                            continue
                        if stmt.func == 'rcases':
                            if (isinstance(with_ := stmt.with_, Lean_with) and (tokens := with_.tokens_bar_separated())):
                                token = tokens[tacticBlockCount]
                                indent = statements.indent
                                if isinstance(token, list):
                                    token = [t for t in token if t.arg != 'rfl']
                                    token = [t.clone() for t in token]
                                    for t in token:
                                        t.indent = indent
                                    if len(token) == 1:
                                        token = token[0]
                                    else:
                                        token = LeanArgsCommaSeparated(token, indent)
                                else:
                                    token = token.clone()
                                    token.indent = indent
                                statements.unshift(LeanTactic(
                                    'echo', 
                                    token, 
                                    statements.indent
                                ))
                        elif stmt.func == "cases'":
                            if (isinstance(with_ := stmt.with_, Lean_with) and 
                                (tokens := with_.tokens_space_separated())):
                                token = tokens[tacticBlockCount].clone()
                                token.indent = statements.indent
                                statements.unshift(LeanTactic(
                                    'echo', 
                                    token, 
                                    statements.indent
                                ))
                        elif stmt.func == 'split_ifs':
                            if (isinstance(with_ := stmt.with_, Lean_with) and len(with_.args) == 1 and isinstance(tokens := with_.args[0], (LeanArgsSpaceSeparated, LeanToken))):
                                statements.unshift(LeanTactic(
                                    'echo', 
                                    LeanToken(
                                        '⊢', 
                                        statements.indent
                                    ), 
                                    statements.indent
                                ))
                                tactic_block_info = tokens.tactic_block_info()
                                if tacticBlockCount < len(tactic_block_info):
                                    tokens_list = tactic_block_info[tacticBlockCount]
                                    span = [t.cache['size'] for t in tokens_list]
                                    args = self.parent.args[index:]
                                    length = len(args)
                                    for i, token in enumerate(tokens_list):
                                        token = token.clone()
                                        token.indent = self.indent
                                        echo_tactic = LeanTactic(
                                            'echo', 
                                            token, 
                                            self.indent
                                        )
                                        stop = self.tactic_block(args, span[i])
                                        new_list = [echo_tactic]
                                        new_list.extend(args[:stop])
                                        new_list.append(echo_tactic.clone())
                                        args = new_list + args[stop:]
                                    return (length, *args)
                        elif stmt.func == 'by_cases':
                            if (isinstance(colon := stmt.arg, LeanColon) and isinstance(token := colon.lhs, LeanToken)):
                                tokens = token.tokens_space_separated()
                                if tacticBlockCount < len(tokens):
                                    token = tokens[tacticBlockCount].clone()
                                    token.indent = self.indent
                                    echo_tactic = LeanTactic(
                                        'echo', 
                                        token, 
                                        self.indent
                                    )
                                    return (1, echo_tactic, self, echo_tactic.clone())
                        else:
                            token = LeanToken('⊢', statements.indent)
                            if sequential_tactic_combinator := stmt.sequential_tactic_combinator:
                                tactic = sequential_tactic_combinator.arg
                                if tactic_token := tactic.get_echo_token():
                                    if isinstance(tactic_token, LeanArgsCommaSeparated):
                                        tactic_token.push(token)
                                        token = tactic_token
                                    else:
                                        token = LeanArgsCommaSeparated([tactic_token, token], statements.indent)
                            statements.unshift(LeanTactic(
                                'echo', 
                                token, 
                                statements.indent
                            ))
                    break
        return self

    # return the stop (right open) index of the range [0, stop) that contains $span elements of LeanTacticBlock
    def tactic_block(self, args, span):
        count = 0
        j = 0
        while j < len(args) and count < span:
            if isinstance(args[j], LeanTacticBlock):
                count += 1
            j += 1
        return j

    def set_line(self, line):
        self.line = line
        line += 1
        return self.arg.set_line(line)

    def split(self, syntax=None):
        if isinstance(self.arg, LeanStatements):
            statements = self.arg.args
            this = self.clone()
            this.arg = LeanCaret(self.indent)
            result = [this]
            for stmt in statements:
                result.extend(stmt.split(syntax))
            return result
        return [self]


class Lean_with(LeanArgs):
    def __init__(self, arg, indent, parent=None):
        super().__init__([arg], indent, parent)

    def is_indented(self):
        return False

    def sep(self):
        if len(self.args) > 1:
            return "\n"
        if not self.args:
            return ""
        caret = self.args[0]
        if isinstance(caret, LeanCaret) or caret.tokens_space_separated() or isinstance(caret, LeanBitOr):
            return ' '
        return "\n"

    def strFormat(self):
        sep = self.sep()
        return f"{self.func}{sep}" + "\n".join(['%s'] * len(self.args))

    def latexFormat(self):
        return self.strFormat()

    def relocate_last_comment(self):
        if self.args:
            self.args[-1].relocate_last_comment()

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.indent > indent:
            return super().insert_newline(caret, newline_count, indent, **kwargs)

        if self.args:
            last_arg = self.args[-1]
            if isinstance(last_arg, LeanCaret):
                return last_arg
            if next_token == '|':
                if isinstance(last_arg, LeanBar) or last_arg.is_comment():
                    new = LeanCaret(self.indent)
                    self.push(new)
                    return new
        return super().insert_newline(caret, newline_count, indent, **kwargs)

    def insert_bar(self, caret, prev_token, next_token):
        if self.args and self.args[-1] is caret:
            if isinstance(caret, LeanCaret):
                self.replace(caret, LeanBar(caret, self.indent))
                return caret
            else:
                new = LeanCaret(self.indent)
                self.replace(caret, LeanBitOr(caret, new, self.indent))
                return new
        raise Exception(f"{self.__class__.__name__}::insert_bar is unexpected for {type(self).__name__}")

    def insert_tactic(self, caret, token, **kwargs):
        if isinstance(caret, LeanCaret):
            return self.insert_word(caret, token, **kwargs)
        return super().insert_tactic(caret, token, **kwargs)

    @property
    def stack_priority(self, vname):
        if isinstance(self.parent, Lean_match):
            return 23
        return 17

    def insert_comma(self, caret):
        if self.args and caret is self.args[-1]:
            new = LeanCaret(self.indent)
            self.replace(caret, LeanArgsCommaSeparated([caret, new], self.indent))
            return new
        raise Exception(f"{self.__class__.__name__}::insert_comma is unexpected for {type(self).__name__}")

    def set_line(self, line):
        self.line = line
        if self.sep() == "\n":
            line += 1
        for arg in self.args:
            line = arg.set_line(line) + 1
        return line - 1

    def tokens_bar_separated(self):
        if len(self.args) == 1 and isinstance(self.args[0], LeanBitOr):
            return self.args[0].tokens_bar_separated()
        return []

    def unique_token(self, indent):
        if len(self.args) == 1:
            stmt = self.args[0]
            if isinstance(stmt, LeanBitOr) or isinstance(stmt, LeanArgsSpaceSeparated):
                return stmt.unique_token(indent)

    def tokens_space_separated(self):
        if len(self.args) == 1 and isinstance(self.args[0], LeanArgsSpaceSeparated):
            return self.args[0].tokens_space_separated()
        return []

class LeanAttribute(LeanUnary):
    def is_indented(self):
        return False

    def sep(self):
        return ''

    def strFormat(self):
        sep = self.sep()
        return f"{self.operator}{sep}%s"

    def latexFormat(self):
        return f"{self.command} %s"

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        return caret

    def append(self, new, type):
        return self.push_accessibility(new, "public")

    def push_accessibility(self, new, accessibility):
        if new in ['Lean_theorem', 'Lean_lemma', 'Lean_def']:
            caret = LeanCaret(self.indent)
            cls = globals()[new]
            new = cls(accessibility, caret, self.indent)
            self.parent.replace(self, new)
            new.attribute = self
            return caret
        else:
            raise Exception(f"{self.__class__.__name__}::{__name__} is unexpected for {self.__class__.__name__}")

    operator = command = '@'

class Lean_def(LeanArgs):
    def __init__(self, accessibility, name, indent=None, parent=None):
        if indent is None:
            indent = name
            name = accessibility
            accessibility = 'public'
        super().__init__([name], indent, parent)
        self.args.insert(0, None)
        self.accessibility = accessibility

    def is_indented(self):
        return False

    def strFormat(self):
        accessibilityString = '' if self.accessibility == 'public' else f"{self.accessibility} "
        def_str = f"{accessibilityString}{self.func} %s"
        if self.attribute:
            def_str = f"%s\n{def_str}"
        return def_str

    def latexFormat(self):
        return self.strFormat()

    def strArgs(self):
        attribute, assignment = self.args[0], self.args[1]
        if attribute is None:
            return [assignment]
        return self.args

    def toJson(self):
        json_data = {
            self.func: super().toJson(),
            "accessibility": self.accessibility
        }
        if self.attribute:
            json_data['attribute'] = self.attribute.toJson()
        return json_data

    def insert_newline(self, caret, newline_count, indent, **kwargs):
        if self.indent < indent:
            if caret == self.assignment:
                if isinstance(caret, (LeanToken, LeanProperty)):
                    caret = LeanCaret(indent)
                    new = LeanArgsNewLineSeparated([caret], indent)
                    caret = new.push_newlines(newline_count - 1)
                    self.assignment = LeanArgsIndented(
                        self.assignment,
                        new,
                        self.indent
                    )
                    return caret

                if isinstance(caret, LeanColon):
                    if isinstance(caret.rhs, LeanCaret):
                        caret = caret.rhs
                        caret.indent = indent
                        self.assignment.rhs = LeanStatements([caret], indent)
                        return caret

                elif isinstance(caret, LeanAssign):
                    caret = self.assignment.rhs
                    if isinstance(caret, LeanCaret):
                        caret.indent = indent
                        self.assignment.rhs = LeanStatements([caret], indent)
                        return caret
                    else:
                        return super().insert_newline(caret, newline_count, self.indent, **kwargs)

            raise Exception(f"{self.__class__.__name__}.insert_newline is unexpected for {self.__class__.__name__}")

        return super().insert_newline(caret, newline_count, indent, **kwargs)

    @property
    def stack_priority(self):
        return 7

    @property
    def attribute(self):
        return self.args[0] if len(self.args) > 0 else None

    @attribute.setter
    def attribute(self, val):
        if len(self.args) < 1:
            self.args = [val] + self.args[1:]
        else:
            self.args[0] = val
        val.parent = self

    @property
    def assignment(self):
        return self.args[1] if len(self.args) > 1 else None

    @assignment.setter
    def assignment(self, val):
        if len(self.args) < 2:
            if len(self.args) < 1:
                self.args.append(None)
            self.args.append(val)
        else:
            self.args[1] = val
        val.parent = self

    def relocate_last_comment(self):
        if isinstance(self.assignment, LeanAssign):
            self.assignment.relocate_last_comment()

    def set_line(self, line):
        self.line = line
        attribute = self.attribute
        if attribute:
            line = attribute.set_line(line) + 1
        return self.assignment.set_line(line)

    def insert_tactic(self, caret, token, **kwargs):
        return self.insert_word(caret, token, **kwargs)

class Lean_theorem(Lean_def):
    pass

class Lean_lemma(Lean_def):
    def echo(self):
        self.assignment = self.assignment.echo()
        if isinstance(self.assignment, LeanAssign) and isinstance(self.assignment.rhs, Lean_by):
            statement = self.assignment.rhs.arg
            if isinstance(statement, LeanStatements):
                statements = statement.args
                for i in range(len(statements) - 1, -1, -1):
                    stmt = statements[i]
                    if stmt.is_comment():
                        continue
                    if isinstance(stmt, (LeanTactic, Lean_have, Lean_let)):
                        token = stmt.get_echo_token()
                        # try echo ⊢
                        if token:
                            indent = statement.indent
                            statement.push(LeanTactic(
                                'try',
                                LeanTactic('echo', token, indent),
                                indent
                            ))
                        break
        return self

class Lean_have(LeanUnary):
    def is_indented(self):
        return True

    def sep(self):
        assign = self.arg
        if isinstance(assign, LeanAssign):
            lhs = assign.lhs
            if isinstance(lhs, LeanCaret) or (isinstance(lhs, LeanColon) and isinstance(lhs.lhs, LeanCaret)):
                return ''
        return ' '

    def strFormat(self):
        sep = self.sep()
        return f"{self.operator}{sep}%s"

    def latexFormat(self):
        return f"{self.command} %s"

    def toJson(self):
        return {
            self.func: self.arg.toJson()
        }

    stack_priority = 7

    operator = command = 'have'

    def get_echo_token(self):
        assign = self.arg
        if isinstance(assign, LeanAssign):
            token = assign.lhs
            if isinstance(token, LeanColon):
                token = token.lhs
            if isinstance(token, LeanCaret):
                token = LeanToken('this', self.indent)
            if (isinstance(token, LeanAngleBracket) and 
                isinstance(token.arg, LeanArgsCommaSeparated) and 
                all(isinstance(arg, LeanToken) for arg in token.arg.args)):
                token = token.arg
            if isinstance(token, (LeanToken, LeanArgsCommaSeparated)):
                return token

    def echo(self):
        token = self.get_echo_token()
        if token:
            by = self.arg.rhs
            if isinstance(by, Lean_by):
                stmt = by.arg
                if isinstance(stmt, LeanStatements):
                    stmt.echo()
            return [
                1, 
                self, 
                LeanTactic('echo', token, self.indent)
            ]
        return self

    def split(self, syntax=None):
        assign = self.arg
        if (isinstance(assign, LeanAssign) and isinstance(by := assign.rhs, Lean_by) and isinstance(stmts := by.arg, LeanStatements)):
            this = copy(self)
            this.arg.rhs = LeanCaret(by.indent)
            statements = [this]

            for stmt in stmts.args:
                statements.extend(stmt.split(syntax))

            return statements
        return [self]

class Lean_let(LeanUnary):
    
    def is_indented(self):
        return True
    
    def strFormat(self):
        return f"{self.operator} %s"
    
    def latexFormat(self):
        return r"\textcolor{#770088}{\textbf{let}}\ %s"
    
    def toJson(self):
        return {
            self.func: self.arg.toJson()
        }
    
    stack_priority = 7
    operator = command = 'let'
    
    def get_echo_token(self):
        assign = self.arg
        if isinstance(assign, LeanAssign):
            angleBracket = assign.lhs
            if isinstance(angleBracket, LeanAngleBracket):
                token = angleBracket.tokens_comma_separated()
                if len(token) == 1:
                    return token[0]
                return LeanArgsCommaSeparated(token, self.indent)
        return None
    
    def echo(self):
        token = self.get_echo_token()
        if token:
            return (
                1,
                self,
                LeanTactic('echo', token, self.indent)
            )
        return self

class Lean_show(LeanSyntax):
    def __init__(self, arg, indent, parent=None):
        super().__init__([arg], indent, parent)
    
    def is_indented(self):
        parent = self.parent
        return isinstance(parent, (LeanStatements, LeanArgsNewLineSeparated))
    
    def strFormat(self):
        return f"{self.func} " + " ".join(["%s"] * len(self.args))
    
    def latexFormat(self):
        return self.strFormat()
    
    def toJson(self):
        return {
            self.func: super().toJson()
        }
    
    stack_priority = 7

class Lean_fun(LeanUnary):
    input_priority = 19

    def is_indented(self):
        parent = self.parent
        return isinstance(parent, (LeanArgsNewLineSeparated, LeanStatements))
    
    def strFormat(self):
        return f"{self.operator} %s"
    
    def latexFormat(self):
        return f"{self.command}\\ %s"
    
    def toJson(self):
        return {self.func: self.arg.toJson()}
    
    operator = 'fun'
    command = r'\lambda'

class LBigOperator(LeanArgs):
    def __init__(self, bound, indent, parent=None):
        super().__init__([bound], indent, parent)
    
    @property
    def bound(self):
        return self.args[0]
    
    @bound.setter
    def bound(self, val):
        self.args[0] = val
        val.parent = self
    
    @property
    def scope(self):
        return self.args[1] if len(self.args) > 1 else None
    
    @scope.setter
    def scope(self, val):
        self.args[1] = val
        val.parent = self
    
    def is_indented(self):
        return isinstance(self.parent, LeanStatements)
    
    def strFormat(self):
        if len(self.args) == 1:
            return f"{self.operator} %s,"
        return f"{self.operator} %s, %s"
    
    def latexFormat(self):
        return fr"{self.command}\limits_{{\substack{{%s}}}} {{%s}}"
    
    def toJson(self):
        return {
            self.func: super().toJson()
        }
    
    def insert_comma(self, caret):
        if caret == self.bound:
            caret = LeanCaret(self.indent)
            self.scope = caret
            return caret
        raise Exception(f"insert_comma is unexpected for {self.__class__.__name__}")

class LeanQuantifier(LBigOperator, LeanProp):
    input_priority = 24

    def latexFormat(self):
        if len(self.args) == 1:
            return f"{self.command}\\\\ {{%s}},"
        return f"{self.command}\\\\ {{%s}}, {{%s}}"

    @property
    def stack_priority(self):
        return LeanColon.input_priority - 1

# universal quantifier
class Lean_forall(LeanQuantifier):
    @property
    def operator(self):
        return '∀'

# existential quantifier
class Lean_exists(LeanQuantifier):
    @property
    def operator(self):
        return '∃'

class Lean_sum(LBigOperator):
    input_priority = 52

    @property
    def operator(self):
        return '∑'

    @property
    def stack_priority(self):
        return 28

class Lean_prod(LBigOperator):
    input_priority = 52

    @property
    def operator(self):
        return '∏'

    @property
    def stack_priority(self):
        return 28
    
class LeanStack(LBigOperator):
    input_priority = 52

    operator = 'Stack'
    command = 'Stack'
    stack_priority = 28

    def strFormat(self):
        return "[%s] %s"

    def latexFormat(self):
        return r"\left[{%s}\\right]{%s}"

    def latexArgs(self, syntax=None):
        syntax[type(self).__name__] = True
        return super().latexArgs(syntax)

class LeanParser(AbstractParser):
    def __init__(self):
        ...

    def init(self):
        caret = LeanCaret(0, start_idx=0)
        self.caret = caret
        self.root = LeanModule([caret], 0)

    def __str__(self):
        return str(self.root)

    def build_debug(self, text):
        self.init()
        history = ''  # for debug purposes
        for start_idx, token in enumerate(text):
            try:
                # print("start_idx =", start_idx)
                # if i == 1530:
                    # print(history)
                # if history.endswith('@'):
                    # print(history)
                if token == '@':
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

    def build(self, text):
        self.init()
        for start_idx, token in enumerate(text):
            self.parse(token, start_idx=start_idx)
        start_idx = len(text)
        self.parse("\n", start_idx=start_idx)
        self.parse('', start_idx=start_idx + 1)
        return self.root

def compile(code):
    global tactics
    caret = LeanCaret(0)
    root = LeanModule([caret], 0)
    assert code.endswith('\n')
    tokens = re.findall(r'\w+|\W', code)
    i = 0
    count = len(tokens)
    tokens.append('') # prevent out of bounds error
    return root

def escape_specials(token):
    def replace(match):
        head = match.group(1)
        tail = re.sub(r'[{}_]', lambda x: '\\' + x.group(0), match.group(2))
        if len(head) == 1:
            return f"{head}_{{{tail}}}"
        else:
            return f"{head}\\_{tail}"

    return re.sub(r'^(\w+?)_(.+)', replace, token, count=1)

def latex_tag(tag):
    return '.'.join(escape_specials(part) for part in tag.split('.'))

def get_lake_path():
    return "~/.elan/bin/lake" if std.is_Linux() else shlex.quote(os.path.join(os.getenv('USERPROFILE'), ".elan", "bin", "lake.exe"))

def get_lean_env():
    # add to the file D:\wamp64\bin\apache\apache2.4.54.2\conf\extra\httpd-vhosts.conf
    # SetEnv USERPROFILE "C:\Users\admin"
    # Configure Git environment variables to trust the directory
    cwd = os.getcwd()
    packages_dir = os.path.join(cwd, ".lake", "packages")
    repository = os.listdir(packages_dir) if os.path.exists(packages_dir) else []
    env = {
        'GIT_CONFIG_COUNT': len(repository),
        # Preserve other important environment variables
        'PATH': os.getenv('PATH'),
        'SystemRoot': os.getenv('SystemRoot'),
        'HOME': os.getenv('HOME')
    }
    cwd = cwd.replace("\\", "/")
    for index, directory in enumerate(repository):
        env[f"GIT_CONFIG_KEY_{index}"] = "safe.directory"
        env[f"GIT_CONFIG_VALUE_{index}"] = f"{cwd}/.lake/packages/{directory}"

    return env

def test_files():
    from std.file import Text
    for file in std.listdir('../lean/Lemma', ext='.lean', recursive=True):
        if file.endswith('/Basic.lean'):
            continue
        print(file)
        text = Text(file).read()
        try:
            tree = LeanParser.instance.build_debug(text)
            print(tree)
        except Exception as e:
            print(f"http://192.168.18.131:8000/lean/?module={file}")
            import traceback
            traceback.print_exc()
            print(e)
            return

if __name__ == '__main__':
    test_files()
