# cd ../keras && bash run.sh std.cpp.test_table &
from std import Object, compile_cpp, delete_indices
from std.debug import default_on_error
compile_cpp(__file__, 'rabin_karp')

from std.cpp.rabin_karp import repetition_penalty as cpp_repetition_penalty
from std.parser.markdown import MarkdownParser

def repetition_penalty_with_markdown_tags(answer):
    info = cpp_repetition_penalty(answer)
    tree = MarkdownParser.instance.build(answer)
    for res in info:
        length = len(res['text'])
        index = res['index']
        res['tagName'] = [span.parent.func if (span := tree.span(Object(start_idx=start_idx, end_idx=start_idx + length))) else None for start_idx in index]
    return info

@default_on_error({'score' : -30})
def repetition_penalty(
    prompt, 
    answer, 
    min_repetition_count=3, 
    min_scan_length=64, 
    max_distance_multiple=14, 
    min_coverage_area=428,
    ignores=(
        # html tags: <td></td>
        'MarkdownTD', 
        # html tags: <th></th>
        'MarkdownTH', 
        # html tags: <tr></tr>
        'MarkdownTR', 
        # html tags: <table></table>
        'MarkdownTABLE', 
        # html tags: <pre><code></code></pre>
        # 'MarkdownPreCode', 
        # (block/unblock) latex tags: \[\] \(\)
        # 'MarkdownLatex', 
        # html tags: <input type="checkbox" disabled checked>
        'MarkdownCheckbox',
        # html tags: <hr>
        'MarkdownHR',
        # html tags: <br>
        'MarkdownBR',
        # html tags: <code></code>
        # 'MarkdownCODE',
    ),
    **_
):
    # add prompt logic if necessary?
    score = 0
    error = repetition_penalty_with_markdown_tags(answer)
    indicesToDelete = set()
    for error_i, res in enumerate(error):
        text = res['text']
        # remove markdown syntax
        # if not re.sub(r'[\s*-:|]+', '', error):
            # continue
        index = []
        names = []
        for i, tagName in zip(res['index'], res['tagName']):
            if tagName in ignores:
                continue
            index.append(i)
            names.append(tagName)
            assert answer[i:i+ len(text)] == text
        hit = False
        scan_length = res['scan_length']
        # scan_length is the utf8-bytes of the text returned from C++, it must be equal to length of bytes representation of the text
        assert scan_length == len(text.encode())
        repetition_count = int(min_coverage_area / scan_length) if scan_length < min_scan_length else min_repetition_count
        max_distance = (max_distance_multiple + 1) * scan_length
        start = 0
        for i in range(len(index)):
            stop = i + 1
            if stop >= len(index) or index[stop] - index[i] > max_distance:
                if (size := stop - start) >= repetition_count:
                    hit = True
                    score += scan_length * size # use the total utf8-bytes it covers as the score
                start = stop
        if not hit:
            indicesToDelete.add(error_i)
    error = delete_indices(error, indicesToDelete)
    return {
        'score': -score / min_scan_length,
        'error': error,
        'min_repetition_count': min_repetition_count,
        'min_scan_length': min_scan_length,
        'max_distance_multiple': max_distance_multiple,
        'min_coverage_area': min_coverage_area,
        'ignores': ignores,
    }

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
                    res = repetition_penalty(None, answer)
                    if Rank is not None:
                        print(res)
            except Exception as e:
                print('Rank', i + 1)
                print(f"http://192.168.18.133:8000/label/query.php?id={id}")
                import traceback
                traceback.print_exc()
                print(e)
                return

def test():
    text = '''
这是一篇陈词滥调的文章[1]。This is a clichéd article [2]. C’est un article plein de clichés [3].
这是一篇陈词滥调的文章[4]。C’est un article plein de clichés [6]. This is a clichéd article [5].
C’est un article plein de clichés [9]. 这是一篇陈词滥调的文章[7]。This is a clichéd article [8].
C’est un article plein de clichés [9]. This is a clichéd article [8]. 这是一篇陈词滥调的文章[7]。
This is a clichéd article [8]. C’est un article plein de clichés [9]. 这是一篇陈词滥调的文章[7]。
This is a clichéd article [8]. 这是一篇陈词滥调的文章[7]。C’est un article plein de clichés [9].
'''
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
```
'''
    print(repetition_penalty(None, text))

if __name__ == '__main__':
    test_table(
        id=2163312,
        Rank=1
    )
