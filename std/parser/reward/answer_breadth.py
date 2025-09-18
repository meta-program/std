import regex as re
from std.parser.reward.answer_depth import preprocess
from std.parser.markdown import *
from std.parser.xml import XML
from std import __set__

def is_conclusion(text):
    return re.match('总结|结论|Conclusion', text)

@__set__(Markdown, XMLParser, XML)
@computed
def answer_breadth(self):
    return 1

@__set__(MarkdownOL, MarkdownUL)
@computed
def answer_breadth(self):
    li = [arg for arg in self.args if isinstance(arg, MarkdownLI)]
    return len(li)

@__set__(MarkdownH, MarkdownDocument)
@computed
def answer_breadth(self):
    ol = []
    ul = []
    h = []
    for i, child in enumerate(self.args):
        if isinstance(child, MarkdownOL):
            if len([child for child in child.args if isinstance(child, MarkdownLI)]) > 1:
                ol.append(child)
        elif isinstance(child, MarkdownUL):
            if len([child for child in child.args if isinstance(child, MarkdownLI)]) > 1:
                ul.append(child)
        elif isinstance(child, MarkdownH):
            h.append(child)
    if h:
        breadth = len(h)
    else:
        if ol:
            if len(ol) > 1:
                return len(ol) + len(ul)
            args = [child for child in ol[0].args if isinstance(child, MarkdownLI)]
            if ul:
                if any(child.answer_depth > 1 for child in args):
                    return len(args) + len(ul)
                return 1 + len(ul)
            else:
                return len(args)
        if ul:
            return len(ul) if len(ul) > 1 else len([child for child in ul[0].args if isinstance(child, MarkdownLI)])
        return 0
    if breadth == 1 and not ol and not ul:
        return h[0].answer_breadth
    header = h[-1].args[0]
    if is_conclusion(str(header)):
        breadth -= 1
    return breadth + len(ol) + len(ul)

def answer_breadth(prompt, answer):
    if isinstance(answer, str):
        answer = preprocess(answer)
        tree = MarkdownParser.instance.build(answer)
    else:
        tree = answer
    tree.answer_depth = 1
    max_answer_breadth = -1
    node = None
    for arg in tree.dfs():
        answer_breadth = arg.answer_breadth
        if answer_breadth > max_answer_breadth:
            max_answer_breadth = answer_breadth
            node = arg
    
    return {
        'score': max_answer_breadth,
        'start_idx': node.start_idx,
        'end_idx': node.end_idx,
    }


def test_table(id=None, Rank=None, offset=0):
    import json
    from std import MySQL
    kwargs = {
        'where' : "json_length(answer) > 0 and source regexp 'answer_breadth'",
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
    sum = 0 
    err = 0 
    for data in MySQL.instance.select('reward', **kwargs):
        id = data['id']
        offset += 1
        print('testing id =', id, 'offset =', offset)
        hit = False
        for i, (answer, source) in enumerate(zip(json.loads(data['answer']), json.loads(data['source']))):
            try:
                if Rank is not None:
                    if i != Rank - 1:
                        continue
                if isinstance(answer, str):
                    answer = [answer]
                    source = [source]
                for answer, source in zip(answer, source):
                    if 'answer_breadth' not in source:
                        continue
                    breadth = answer_breadth(None, answer)['max_answer_breadth']
                    sum += 1
                    if breadth != int(source['answer_breadth']):
                        err += 1
                        print(f"source['answer_breadth'] =", source['answer_breadth'])
                        print('answer_breadth =', breadth)
                        print(f'acc = {((sum - err) / sum) * 100:.2f}%')
                        print('Rank', i + 1)
                        print(f"http://192.168.18.133:8000/label/query.php?id={id}")
                        print(f"http://192.168.18.133:8000/label/query.php?select[0][json_extract][0]=answer&select[0][json_extract][1]=%24%5B{i}%5D&select[1][json_extract][0]=source&select[1][json_extract][1]=%24%5B{i}%5D&from[corpus]=reward&where[eq][0]=id&where[eq][1]={id}&limit=1")
                        hit = True
                        breadth = answer_breadth(None, answer)
            except Exception as e:
                print('Rank', i + 1)
                print(f"http://192.168.18.133:8000/label/query.php?id={id}")
                import traceback
                traceback.print_exc()
                print(e)
                return
        if hit:
            MySQL.instance().executemany("update corpus.reward set label = json_set(label, '$[2]', 'answer_breadth_error') where id = %s", [(id,)])

def test():
    from std.file import Text
    file = f"std/src/hash/test/test-27.txt"
    text = Text(file).read()
    res = answer_breadth(None, text)
    print(res)

if __name__ == '__main__':
    test()
    test_table(
        # id=273979, 
        # Rank=4
    )
