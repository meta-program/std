# std

a standard library for algorithms:  
pip install std.algorithm  

## multi-language segmenter 

```
from std.nlp.segment.cn import split  
split('结婚的和尚未结婚的确实在理念上将存在分歧。')  #['结婚', '的', '和', '尚未', '结婚', '的', '确实', '在', '理念上', '将', '存在', '分歧', '。']  

from std.nlp.segment.jp import split  
split('の出力と前記第3のゲート回路34-oの出力とを入力するアンドゲート回路35を備え、') #['の', '出力', 'と', '前記', '第', '3', 'の', 'ゲート', '回路', '34', '-', 'o', 'の', '出力', 'と', 'を', '入力', 'する', 'アンド', 'ゲート', '回路', '35', 'を', '備え', '、']  

from std.nlp.segment.en import split   
split('who are you?') #['who ', 'are ', 'you', '?']  
```


## rich text preprocessing

```
from std.xml import construct_rich_text
physicalText = "firstly,&nbsp;<div><b>this&nbsp;is&nbsp;<I>an&nbsp;<font color='red'><i>italic</i>&nbsp;<u>&lt;underline&gt;</u><mspace /></font>, simply put</b>,&nbsp;this&nbsp;is&nbsp;an&nbsp;italic&nbsp;text,&nbsp;</I>with&nbsp;something&emsp;<u>&lt;underlined&gt;</u>;</div>&ensp;<b>another&nbsp;bold&nbsp;text&nbsp;is&nbsp;followed.&nbsp;</b>At&nbsp;last,&nbsp;there&nbsp;a&nbsp;plain&nbsp;text."
richText = construct_rich_text(physicalText)
# print(richText)
richText.sanity_check()
print("physical text =", richText.physicalText)
print(" logical text =", richText.text)
print(" style_traits =", richText.style_traits)

start, stop = 20, 39
print("the logical text is :")
print(richText.text[start:stop])
print("its style trait is :")
print(richText.style_traits[start:stop])

start, stop = richText.getPhysicalIndices(start, stop)
print("its original physical text is:")
print(physicalText[start:stop])
print()
```

## balanced parenthese/brachets/braces matching
```
from std.regexp import balanced
for pairedGroup in balanced.finditer("()", '((1 + 2) * (3 * 4)) + (7 + 8) * [8 + 8]'):
    print(pairedGroup)

for pairedGroup in balanced.findall("[]", '[[1 + 2] * [3 * 4]] + (7 + 8) * [8 + 8]'):
    print(pairedGroup)

print(balanced.search("{}", '{{1 + 2} * {3 * 4}} + {7 + 8} * [8 + 8]'))

outputs:
<regex.Match object; span=(0, 19), match='((1 + 2) * (3 * 4))'>
<regex.Match object; span=(22, 29), match='(7 + 8)'>
[[1 + 2] * [3 * 4]]
[8 + 8]
<regex.Match object; span=(0, 19), match='{{1 + 2} * {3 * 4}}'>
```
### supported paired groups:
()[]{}

<>

（）【】｛｝《》〈〉〖〗〘〙〚〛｟｠

‘’“”〝〞

「」『』｢｣〔〕

## rule reward/penalty for NLP
### repetition-penalty
this is the efficient algorithm for detecting duplicate text detection written in C++
Definition of repeated fragments:  
1. The text fragment length is defined as scan_length, measured by the UTF-8 `strlen : len(text.encode())` of the text (regardless of Chinese or English).  
2. The fragment must repeat at least the user-specified number of times `min_coverage_area / scan_length if scan_length < min_scan_length else min_repetition_count`, where `min_repetition_count` and `min_coverage_area` are user-defined.
3. The spacing between repeated fragments must not exceed the user-specified multiple (`max_distance_multiple`), i.e., the distance between adjacent fragments satisfies:  
   `StartIndexᵢ₊₁ - StartIndexᵢ ≤ len(text.encode()) * (max_distance_multiple + 1)`.  
   Repetitions beyond this spacing are no longer considered redundant.
#### requirements
```bash
pip install pybind11
pip install --upgrade std.algorithm
```
#### [usage](std/cpp/__init__.py)
```python
from std.cpp import repetition_penalty
text='''这是一篇陈词滥调的文章[1]。This is a clichéd article [2]. C’est un article plein de clichés [3].
这是一篇陈词滥调的文章[4]。C’est un article plein de clichés [6]. This is a clichéd article [5].
C’est un article plein de clichés [9]. 这是一篇陈词滥调的文章[6]。This is a clichéd article [7].
C’est un article plein de clichés [8]. This is a clichéd article [0]. 这是一篇陈词滥调的文章[7]。
This is a clichéd article [1]. C’est un article plein de clichés [7]. 这是一篇陈词滥调的文章[8]。
This is a clichéd article [8]. 这是一篇陈词滥调的文章[9]。C’est un article plein de clichés [1].'''
# use min_repetition_count, min_scan_length, max_distance_multiple, min_coverage_area, ignore to filter result and gather scores:
print(repetition_penalty(None, text, min_repetition_count=3, min_scan_length=32, max_distance_multiple=14, min_coverage_area=428, ignores=["MarkdownTD", "MarkdownTH", "MarkdownTR", "MarkdownTABLE", "MarkdownCheckbox", "MarkdownHR", "MarkdownBR"]))
```
##### json-post API without post-processing
```bash
curl -H 'Content-Type: application/json' -d '{"text": "这是一篇陈词滥调的文章[1]。This is a clichéd article [2]. C’est un article plein de clichés [3].\n这是一篇陈词滥调的文章[4]。C’est un article plein de clichés [6]. This is a clichéd article [5].\nC’est un article plein de clichés [9]. 这是一篇陈词滥调的文章[6]。This is a clichéd article [7].\nC’est un article plein de clichés [8]. This is a clichéd article [0]. 这是一篇陈词滥调的文章[7]。\nThis is a clichéd article [1]. C’est un article plein de clichés [7]. 这是一篇陈词滥调的文章[8]。\nThis is a clichéd article [8]. 这是一篇陈词滥调的文章[9]。C’est un article plein de clichés [1]."}' -X POST 'http://192.168.18.102:5001/repetition_penalty'
```
##### json-post API for markdown post-processing
```bash
curl -H 'Content-Type: application/json' -d '{"text": "这是一篇陈词滥调的文章[1]。This is a clichéd article [2]. C’est un article plein de clichés [3].\n这是一篇陈词滥调的文章[4]。C’est un article plein de clichés [6]. This is a clichéd article [5].\nC’est un article plein de clichés [9]. 这是一篇陈词滥调的文章[6]。This is a clichéd article [7].\nC’est un article plein de clichés [8]. This is a clichéd article [0]. 这是一篇陈词滥调的文章[7]。\nThis is a clichéd article [1]. C’est un article plein de clichés [7]. 这是一篇陈词滥调的文章[8]。\nThis is a clichéd article [8]. 这是一篇陈词滥调的文章[9]。C’est un article plein de clichés [1].", "min_repetition_count": 3, "min_scan_length": 32, "max_distance_multiple": 14, "min_coverage_area": 428, "ignores": ["MarkdownTD", "MarkdownTH", "MarkdownTR", "MarkdownTABLE", "MarkdownCheckbox", "MarkdownHR", "MarkdownBR"]}' -X POST 'http://192.168.18.102:5001/repetition_penalty'
```
#### output
```json
{
    "error": [
        {
            "text": "这是一篇陈词滥调的文章[", 
            "scan_length": 34,
            "index": [0, 85, 209, 325, 411, 458],
            "tagName": [
                "MarkdownBracket",
                "MarkdownBracket",
                "MarkdownSPAN",
                "MarkdownBracket",
                "MarkdownSPAN",
                "MarkdownBracket"
            ]
        },
        {
            "text": "C’est un article plein de clichés [", 
            "scan_length": 38,
            "index": [46, 100, 170, 255, 372, 473],
            "tagName": [
                "MarkdownSPAN",
                "MarkdownBracket",
                "MarkdownSPAN",
                "MarkdownSPAN",
                "MarkdownSPAN",
                "MarkdownBracket"
            ]
        }
    ],
    "score": -432,
    "min_repetition_count": 3,
    "min_scan_length": 32,
    "max_distance_multiple": 14,
    "min_coverage_area" : 428
}
```
the `score` field in the output represents the total bytes length of all the erroneous pieces, irrespective of the language per se.

#### design principle
1. First, identify repeated segments with step lengths of 8, 16, 32, ..., 2ᵏ (where 2ᵏ ≤ n). The average complexity is O(n), and the worst-case is O(n * log₂n).  
2. For repeated segments with non-power-of-2 step lengths (e.g., a step length of 257, which is 2⁸ + 1), there must exist intermittent repeated segments with a step length of 2⁸. Thus, they can be detected by locally adjusting the results from step 1.  
3. Additionally, the step length and spacing of repeated segments must be considered. For example, in the text "But wait! wait! wait!" from DeepSeek, this should not be counted as repetition.  
4. Leverage the property that Mersenne primes have binary representations of 111111...111111 to simplify hash value calculations, using bitwise operations instead of large integer multiplication and modulo operations.  

#### debug
if compiling fails, try to compile manually using
```sh
make -C $YourWorkingDirectory/std/std/cpp
```
and see what is happening.

### citation-penalty
this is the regex algorithm for detecting malformed citation in RAG answers.
#### demo
```python
from std.nlp.penalty import citation_penalty
print(citation_penalty('''
这是一篇陈词滥调的文章[1][2][3][4][5][6]。
'''))
# output: {'score': -1, 'error': ['[1][2][3][4][5][6] exceeds 5 citations']}
```

### [language consistency](https://arxiv.org/pdf/2501.12948#page=10)
despite the name, this is actually the algorithm for detecting language-inconsistencies within the answer.
#### usage
```python
from std.nlp.lang import language_consistency
text = '''这是一篇陈词滥调的文章。
C’est un article plein de clichés.'''
print(language_consistency(None, text, lang='en', min_scan_length=16, ignores=['MarkdownA', 'MarkdownB', 'MarkdownBracket', 'MarkdownLatex', 'MarkdownCODE', 'MarkdownPreCode', 'MarkdownTABLE']))
```
json-post API without post-processing
```bash
curl -H 'Content-Type: application/json' -d '{"text": "这是一篇陈词滥调的文章[1]。This is a clichéd article [2]. C’est un article plein de clichés [3].\n这是一篇陈词滥调的文章[4]。C’est un article plein de clichés [6]. This is a clichéd article [5].\nC’est un article plein de clichés [9]. 这是一篇陈词滥调的文章[6]。This is a clichéd article [7].\nC’est un article plein de clichés [8]. This is a clichéd article [0]. 这是一篇陈词滥调的文章[7]。\nThis is a clichéd article [1]. C’est un article plein de clichés [7]. 这是一篇陈词滥调的文章[8]。\nThis is a clichéd article [8]. 这是一篇陈词滥调的文章[9]。C’est un article plein de clichés [1].", "lang": "cn", "min_scan_length": 16, "ignores": ["MarkdownA", "MarkdownB", "MarkdownBracket", "MarkdownLatex", "MarkdownCODE", "MarkdownPreCode", "MarkdownTABLE"]}' -X POST 'http://192.168.18.102:5001/language_consistency'
```
#### output:
```json
{
 "error": [
        {
            "text": "。This is a clichéd article ",
            "index": 14,
            "tagName": "MarkdownSPAN"
        },
        {
            "text": ". C’est un article plein de clichés ",
            "index": 44,
            "tagName": "MarkdownSPAN"
        },
        {
            "text": "。C’est un article plein de clichés ",
            "index": 99,
            "tagName": "MarkdownSPAN"
        },
        {
            "text": ". This is a clichéd article ",
            "index": 137,
            "tagName": "MarkdownSPAN"
        },
        {
            "text": "C’est un article plein de clichés ",
            "index": 170,
            "tagName": "MarkdownSPAN"
        },
        {
            "text": "。This is a clichéd article ",
            "index": 223,
            "tagName": "MarkdownSPAN"
        },
        {
            "text": "C’est un article plein de clichés ",
            "index": 255,
            "tagName": "MarkdownSPAN"
        },
        {
            "text": ". This is a clichéd article ",
            "index": 292,
            "tagName": "MarkdownSPAN"
        },
        {
            "text": "。\nThis is a clichéd article ",
            "index": 339,
            "tagName": "MarkdownSPAN"
        },
        {
            "text": ". C’est un article plein de clichés ",
            "index": 370,
            "tagName": "MarkdownSPAN"
        },
        {
            "text": "。\nThis is a clichéd article ",
            "index": 425,
            "tagName": "MarkdownSPAN"
        },
        {
            "text": "。C’est un article plein de clichés ",
            "index": 472,
            "tagName": "MarkdownSPAN"
        }
    ],
    "score": -12
}
```
the `score` field in the output is defined similarly as `repetition_penalty`.

### syntax-penalty
this is the regex algorithm for detecting syntax errors within the answer.
#### demo
```python
from std.nlp.penalty import syntax_penalty
print(syntax_penalty('''
这是一篇陈词滥调的文章
''', 'cn'))
# {'score': -1, 'error': ['语句没有休止符']}
```


### answer-depth
this is the algorithm for determining the depth of the answer, return -1 if answer-breadth > 6.
#### demo
```python
from std.md import answer_depth
print(answer_depth('''
核桃被誉为“万岁子”、“长寿果”，其营养成分确实非常丰富，包括蛋白质、脂肪酸、维生素E、维生素B以及多种矿物质，如镁和锌。

### 核桃的营养成分

#### 维生素B
核桃还含有维生素B群，尤其是维生素B6和叶酸，这些维生素对神经系统的正常功能和红细胞的生成具有重要作用。

#### 矿物质
- **镁**：核桃中含有丰富的镁，每100克约含3.0毫克，镁对心脑血管健康和骨骼功能有重要作用。
- **锌**：核桃中锌的含量也较高，锌是脑细胞生长的关键元素，有助于提升免疫力和促进伤口愈合。

### 核桃对健康的益处

#### 心血管健康
核桃中的不饱和脂肪酸、纤维和维生素E有助于维护心血管系统健康。研究表明，食用核桃可以降低血压、胆固醇和三酰甘油水平，从而降低心血管疾病的风险。

#### 抗炎和抗氧化
核桃中的Omega-3脂肪酸和多酚类化合物具有显著的抗炎和抗氧化作用，可以减少体内的氧化应激反应，延缓衰老，减轻慢性炎症相关疾病的风险。
'''))
# output: 4
```


### answer-breadth
this is the algorithm for determining the depth of the answer, return -1 if answer-breadth > 10.
#### demo
```python
from std.md import answer_breadth
print(answer_breadth('''
核桃被誉为“万岁子”、“长寿果”，其营养成分确实非常丰富，包括蛋白质、脂肪酸、维生素E、维生素B以及多种矿物质，如镁和锌。

### 核桃的营养成分

#### 维生素B
核桃还含有维生素B群，尤其是维生素B6和叶酸，这些维生素对神经系统的正常功能和红细胞的生成具有重要作用。

#### 矿物质
- **镁**：核桃中含有丰富的镁，每100克约含3.0毫克，镁对心脑血管健康和骨骼功能有重要作用。
- **锌**：核桃中锌的含量也较高，锌是脑细胞生长的关键元素，有助于提升免疫力和促进伤口愈合。

### 核桃对健康的益处

#### 心血管健康
核桃中的不饱和脂肪酸、纤维和维生素E有助于维护心血管系统健康。研究表明，食用核桃可以降低血压、胆固醇和三酰甘油水平，从而降低心血管疾病的风险。

#### 抗炎和抗氧化
核桃中的Omega-3脂肪酸和多酚类化合物具有显著的抗炎和抗氧化作用，可以减少体内的氧化应激反应，延缓衰老，减轻慢性炎症相关疾病的风险。
'''))
# output: 2
```


### writing-style-detection
this is the algorithm for determining the long narrow list within the answer, return a list of texts and its average length.

#### demo
```bash
pip install --upgrade std.algorithm
```
```python
from std.parser.writing_style import min_length_of_paragraphs_in_sliding_window
print(min_length_of_paragraphs_in_sliding_window('''
核桃被誉为“万岁子”、“长寿果”，其营养成分确实非常丰富，包括蛋白质、脂肪酸、维生素E、维生素B以及多种矿物质，如镁和锌。

### 核桃的营养成分

#### 维生素B
核桃还含有维生素B群，尤其是维生素B6和叶酸，这些维生素对神经系统的正常功能和红细胞的生成具有重要作用。

#### 矿物质
- **镁**：核桃中含有丰富的镁
- **锌**：锌是脑细胞生长的关键元素
- **镁**：每100克约含3.0毫克
- **锌**：锌是脑细胞生长的关键元素
- **镁**：每100克约含3.0毫克

### 核桃对健康的益处

#### 心血管健康
核桃中的不饱和脂肪酸、纤维和维生素E有助于维护心血管系统健康。研究表明，食用核桃可以降低血压、胆固醇和三酰甘油水平，从而降低心血管疾病的风险。

#### 抗炎和抗氧化
核桃中的Omega-3脂肪酸和多酚类化合物具有显著的抗炎和抗氧化作用，可以减少体内的氧化应激反应，延缓衰老，减轻慢性炎症相关疾病的风险。
'''))
# json output:
```json
{
    "min_avg_length": 27,
    "texts": [
        "- **镁**：核桃中含有丰富的镁",
        "- **锌**：锌是脑细胞生长的关键元素",
        "- **镁**：每100克约含3.0毫克",
        "- **锌**：锌是脑细胞生长的关键元素",
        "- **镁**：每100克约含3.0毫克",
    ]
}
```
