import sys
import regex as re
from std.nlp.segment import dot_lookahead


def citation_penalty(answer, context=None):
    '''
    args:
        answer: str
        context: information from database
    return:
        {"score": int, "error": str}
    '''
    max_num = sys.maxsize if context is None else len(context)
    penalty = 0
    error = []
    for m in re.finditer(r'(?:\[\d+\])+', answer):
        indices = re.findall(r'\[(\d+)\]', m[0])
        score = max(0, len(indices) - 5)
        if score:
            error.append(f'{m[0]} exceeds 5 citations')
            penalty += score
        for index in indices:
            if int(index) > max_num:
                error.append(f'out of range at {m[0]}, index {index} > {max_num}')
                penalty += 1

    for m in re.finditer(r'\[\d+(, *\d+)+\]', answer):
        error.append(f'comma separated citation: {m[0]}')
        penalty += 1

    # malformed_reference
    lookahead = [
        '[。；]',
        '([.．] *)?(\n|$)',
        '([:：] *)?\n',
        f'[.．] +({dot_lookahead})',
        '\[\d+\]',
    ]
    lookahead = '|'.join(lookahead)
    for m in re.finditer(f'((\[\d+\])+|\[\d+(?:, *\d+)+\])(?!{lookahead})', answer):
        info = answer[max(0, m.start() - 8): m.end() + 8]
        error.append(f"citation isn't at the end: {info}")
        penalty += 0.2

    for m in re.finditer(r'文献\[\d+\]', answer):
        error.append(f"malformed citation: {m[0]} ")
        penalty += 0.5

    prefix = [
        "(\*\*)?(\d+\. *)?",
        " *\* +",
        " +- *",
        " *\* +",
    ]
    prefix = "(?:%s)" % '|'.join(prefix)
    regexp = [
        fr"\n{prefix}(\*\*)?参考文献(\*\*)?：",
        "（未找到参考文献）",
        r"\n#+ 参考文献"
    ]
    for m in re.finditer("(?:%s)" % '|'.join(regexp), answer):
        error.append(f'improper citation: {m[0]}')
        penalty += 1

    result = {"score": -penalty}
    if error:
        result['error'] = error
    return result


def syntax_penalty(answer, lang):
    """Calculate a syntax penalty based on ending punctuation validity.
    
    Checks if the given answer ends with an appropriate punctuation mark followed
    by optional newlines. Different punctuation rules apply for Chinese vs other languages.
    
    Args:
        answer (str): The input text to be checked for ending punctuation validity.
        lang (str): Language code specifying punctuation rules ('cn' for Chinese,
            any other value for non-Chinese languages).
    
    Returns:
        int: 0 if the answer ends with a valid punctuation mark (followed by optional
            newlines), -1 otherwise.
    
    Examples:
        >>> syntax_penalty("Hello world!\n", 'en')
        0
        >>> syntax_penalty("你好世界。", 'cn')
        0
        >>> syntax_penalty("No punctuation", 'en')
        -1
        >>> syntax_penalty("Ends with comma,\n", 'cn')
        -1
    """

    error = []
    score = 0
    if lang == 'cn':
        if not re.search('[。！？]\n*$', answer):
            score -= 1
            error.append('语句没有休止符')
    else:
        if not re.search('[.!?]\n*$', answer):
            score -= 1
            error.append('sentence does not end with a full stop')
    result = {"score": score}
    if error:
        result['error'] = error
    return result
