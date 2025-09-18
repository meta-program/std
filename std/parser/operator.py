from .node import AbstractParser, Node, case 

class OperatorParser(AbstractParser):
    def __init__(self, caret, **kwargs):
        self.caret = Operator(parent=caret, **kwargs)
        self.caret.text = ''

class Operator(Node):
    operators = {
        '<': 'LeanLt',
        '>': 'LeanGt',
        '!': 'LeanNot',
        '+': 'LeanAdd',
        '-': 'LeanSub',
        ':': 'LeanColon',
        '|': 'LeanBitOr',
        '&': 'LeanBitAnd',
        '⁻': None,
        '.': 'LeanProperty',

        '<=': 'LeanLe',
        '>=': 'LeanGe',
        '!=': 'LeanNe',
        '=>': 'LeanRightarrow',
        ':=': 'LeanAssign',
        '::': 'LeanConstruct',
        '--': 'LeanLineComment',
        '++': 'LeanAppend',
        '||': 'LeanLogicOr',
        '|>': 'LeanPipeForward',
        '&&': 'LeanLogicAnd',
        '/': 'LeanDiv',
        '//': 'LeanFDiv',
        '/-': 'LeanBlockComment',
        '-/': 'LeanBlockComment',
        '⁻¹': 'LeanInv',
        '>>': 'LeanMonadicThen',
        '<;': None,
        '..': 'LeanKwargs',

        '|>.': 'LeanMethodChaining',
        '>>=': 'LeanMonadicBind',
        '=<<': 'LeanFlippedBind',
        '<;>': 'LeanSequentialTacticCombinator',
        '::ᵥ':'LeanVConstruct',
        '/--': 'LeanDocString',
    }
    @case('<', '>', '=', '!', ':', '+', '-', '/', '|', '&', '⁻', '.')
    def case(self, **kwargs):
        self.text += self.key
        return self

    @case('>', '=', ';', ':', 'ᵥ', '+', '-', '/', '|', '&', '¹')
    def case(self, **kwargs):
        text = self.text + self.key
        if text in self.operators:
            self.text = text
            return self
        return self.parent.parse('&' + self.operators[self.text], **self.kwargs).parse(self.key, **kwargs)

    @case
    def case(self, **kwargs):
        return self.parent.parse('&' + self.operators[self.text], **self.kwargs).parse(self.key, **kwargs)
    
    def strFormat(self):
        return self.text

