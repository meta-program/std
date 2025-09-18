from .node import AbstractParser, IndentedNode, case 

class NewLineSkippingComment(IndentedNode):
    @case("\n")
    def case(self, **_):
        self.indent = 0
        if self.hyphen_count:
            assert self.hyphen_count >= 2, "Hyphen count must be at least 2 to insert newline"
            self.line_comment.append("\n")
            self.hyphen_count = 0  # Reset hyphen count after newline
        else:
            self.newline_count += 1
        return self

    @case(' ')
    def case(self, **_):
        self.indent += 1
        return self

    @case
    def case(self, **kwargs):
        key = self.key
        caret = self.parent
        self_kwargs = self.kwargs
        if self.next:
            self_kwargs['next'] = key
        if self.hyphen_count:
            if self.hyphen_count >= 2:
                self.line_comment.append(key)
                return self
            else:
                new_caret = caret.parent.insert_newline(
                    caret,
                    self.newline_count,
                    **self_kwargs
                )
                return new_caret.parse(key, *kwargs)
        else:
            caret = caret.parent.insert_newline(
                caret,
                self.newline_count,
                **self_kwargs
            )

            if self.line_comment:
                ctx = kwargs[0]  # First positional arg in kwargs
                ctx.caret = caret
                ctx.start_idx -= self.indent + len(self.line_comment)

                length = len(ctx.tokens)
                while ctx.start_idx < length:
                    current_idx = ctx.start_idx
                    ctx.parse(ctx.tokens[current_idx], ctx)
                    if not ctx.caret:
                        break
                    ctx.start_idx = current_idx + 1
                return ctx.caret

            return caret.parse(key, **kwargs)

class NewLineSkippingCommentParser(AbstractParser):
    def __init__(self, caret, next=True, **kwargs):
        caret = NewLineSkippingComment(parent=caret, **kwargs)
        self.caret = caret
        caret.newline_count = 1
        caret.hyphen_count = 0
        caret.next = next
        caret.line_comment = []
