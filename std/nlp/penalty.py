import sys
import regex as re
from std.parser.markdown import MarkdownParser


def citation_penalty(answer, context=None, max_reference=5):
    '''
    args:
        answer: str
        context: information from database
        max_reference: maximum allowable consecutive references
    return:
        {"score": int, "error": str}
    '''
    max_num = sys.maxsize if context is None else len(context)
    penalty = 0
    error = []
    for m in re.finditer(r'(?:\[\d+\][,，、]? *)+', answer):
        indices = re.findall(r'\[(\d+)\]', m[0])
        score = max(0, len(indices) - max_reference)
        if score:
            error.append(f'{m[0]} exceeds {max_reference} consecutive citations')
            penalty += score
        for index in indices:
            if int(index) > max_num:
                error.append(f'out of range at {m[0]}, index {index} > {max_num}')
                penalty += 1

    for m in re.finditer(r'\[\d+(, *\d+)+\]', answer):
        error.append(f'comma separated citation: {m[0]}')
        penalty += 1

    # malformed_reference
    # lookahead = [
    #     '[。；]',
    #     '([.．] *)?(\n|$)',
    #     '([:：] *)?\n',
    #     f'[.．] +({dot_lookahead})',
    #     '\[\d+\]',
    # ]
    # lookahead = '|'.join(lookahead)
    # for m in re.finditer(f'((\[\d+\])+|\[\d+(?:, *\d+)+\])(?!{lookahead})', answer):
    #     info = answer[max(0, m.start() - 8): m.end() + 8]
    #     error.append(f"citation isn't at the end: {info}")
    #     penalty += 0.2

    # for m in re.finditer(r'文献\[\d+\]', answer):
    #     error.append(f"malformed citation: {m[0]} ")
    #     penalty += 0.5

    prefix = [
        r"(\*\*)?(\d+\. *)?",
        r" *\* +",
        " +- *",
        r" *\* +",
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
    warning = []
    MarkdownParser.instance.build(answer, warning)
    result = {}
    if error:
        result['error'] = error
    if warning:
        result['warning'] = warning
        score -= len(warning)
    result["score"] = score
    return result

if __name__ == '__main__':
    text = """1. 创新性分析：** * **核心概念：** 在洗碗机门把手上加入电容检测传感器，门关闭时检测到触摸信号自动开门一个小角度。门已打开时，电容检测不起作用。 * **现有技术对比：** * **专利[1][37]:** 提到洗碗机自动开门机制，但通过加热器改变长度的执行器实现，并非电容传感器。 * **专利[2][4]:** 涉及障碍物检测和感应器停止工作，但目的是防止夹伤或烫伤，而非自动开门。 * **专利[3][16]:** 提到肢体感应区和自动开门控制，但使用图像采集或距离传感器，而非电容。 * **专利[31][33]:** 提到电容式传感器用于开门，但通过肢体动作或压力检测触发，而非门关闭时的触摸检测。 * **专利[20][10]:** 涉及手势和视觉传感器，但非电容触摸。 * **专利[34]:** 门结构有传感器控制把手伸缩，但未提电容。 * **专利[35][36]:** 自动开门装置，通过驱动机构实现，但无电容传感器。 * **专利[5][6][7][8][9][11][12][13][14][15][17][18][19][21][22][23][24][25][26][27][28][29][30][32][38][39][40]:** 未涉及电容传感器与自动开门结合。 * **创新性体现：** * **传感器类型：** 使用电容传感器检测触摸，这在现有专利中未见明确记载。 * **触发条件：** 门关闭时检测到触摸信号自动开门，这一特定应用场景具有新颖性。 * **安全机制：** 门已打开时电容检测不起作用，这是对系统安全性的考虑，增加了创新点。 **2. 可能的争议点：** * **电容传感器的应用：** 虽然电容传感器本身不是新技术，但将其应用于洗碗机门的自动开门，并结合特定的触发条件（门关闭时），需要考虑其实际效果和可靠性。例如，专利[31]提到电容式传感器可把电容量变化转换为电信号输出，通过特定肢体动作实现开门动作，但未明确门关闭时的触发。"""
    result = citation_penalty(text)
    print(result)

