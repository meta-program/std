# cd ../keras && bash run.sh std.parser.reward.answer_depth.test_table &
# python std/parser/reward/answer_depth.py
from collections import defaultdict
from std.parser.markdown import *
from std import __set__

@__set__(MarkdownArgs)
def has_heading_elements(self):
    return any(
        isinstance(arg, MarkdownH)
        for arg in self.args
    )

@__set__(Markdown)
@property
def answer_depth(self):
    return self.kwargs['answer_depth']

@__set__(Markdown)
@answer_depth.setter
def answer_depth(self, depth):
    self.kwargs['answer_depth'] = depth


@__set__(MarkdownArgs)
@property
def answer_depth(self):
    return max(child.answer_depth for child in self.args)

@__set__(MarkdownArgs)
@answer_depth.setter
def answer_depth(self, depth):
    self.kwargs['answer_depth'] = depth
    args = self.args
    if self.has_heading_elements():
        level2children = defaultdict(list)
        for child in args:
            if isinstance(child, MarkdownH):
                level2children[child.level].append(child)

        min_level = min(level2children.keys())
        depth_heading = depth
        if len(level2children[min_level]) > 1:
            depth_heading += 1

        current_level = 0
        for child in args:
            if isinstance(child, MarkdownH):
                current_level = child.level
            depth_child = current_level - min_level
            depth_child += depth_heading if current_level else depth
            if depth_child < 0:
                depth_child = depth
            child.answer_depth = depth_child
    else:
        depth_list = depth
        if isinstance(self, (MarkdownUL, MarkdownOL)):
            if sum(isinstance(child, MarkdownLI) for child in args) > 1:
                depth_list += 1
            is_list = lambda self: isinstance(self, MarkdownLI)
        elif not isinstance(self, MarkdownLI):
            if sum(isinstance(child, (MarkdownUL, MarkdownOL, MarkdownTABLE)) for child in args) > 1:
                depth_list += 1
            is_list = lambda self: isinstance(self, (MarkdownUL, MarkdownOL))
        else:
            is_list = lambda _: False

        for child in args:
            child.answer_depth = depth_list if is_list(child) else depth

def preprocess(answer):
    answer = re.sub(r'(?<=[:：]|\*\*)\n+(?=[a-zA-Z\p{Han}])', lambda m : ' ' * len(m[0]), answer)
    answer = re.sub(r'\*\*(\d+\. )([^*]+)\*\*', r'\1**\2**', answer)
    answer = re.sub(r'(?<=\n)\((\d+)\) ', r' \1. ', answer)
    return answer

def answer_depth(prompt, answer, **kwargs):
    if isinstance(answer, str):
        if kwargs.get('preprocess'):
            answer = preprocess(answer)
        tree = MarkdownParser.instance.build(answer)
    else:
        tree = answer
    tree.answer_depth = 1
    return {
        'score' : tree.answer_depth
    }


def test_table(id=None, Rank=None, offset=0):
    import json
    from std import MySQL
    kwargs = {
        'where' : "json_length(answer) > 0 and source regexp 'answer_depth' and label regexp 'answer_depth_error'",
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
                    if 'answer_depth' not in source:
                        continue
                    depth = answer_depth(None, answer)
                    sum += 1
                    if depth != int(source['answer_depth']):
                        err += 1
                        print(f"source['answer_depth'] =", source['answer_depth'])
                        print('answer_depth =', depth)
                        print(f'acc = {((sum - err) / sum) * 100:.2f}%')
                        print('Rank', i + 1)
                        print(f"http://192.168.18.133:8000/label/query.php?id={id}")
                        print(f"http://192.168.18.133:8000/label/query.php?select[0][json_extract][0]=answer&select[0][json_extract][1]=%24%5B{i}%5D&select[1][json_extract][0]=source&select[1][json_extract][1]=%24%5B{i}%5D&from[corpus]=reward&where[eq][0]=id&where[eq][1]={id}&limit=1")
                        hit = True
                        depth = answer_depth(None, answer)
            except Exception as e:
                print('Rank', i + 1)
                print(f"http://192.168.18.133:8000/label/query.php?id={id}")
                import traceback
                traceback.print_exc()
                print(e)
                return
        if hit:
            MySQL.instance().executemany("update corpus.reward set label = json_set(label, '$[2]', 'answer_depth_error') where id = %s", [(id,)])

if __name__ == '__main__':
    # test()
    test_table(
        # id=273979, 
        # Rank=4
    )
