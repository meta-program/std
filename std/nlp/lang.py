# cd ../keras && bash run.sh std.nlp.lang.test_batch &
import regex as re
from std.nlp.segment import sbd
from std.parser.markdown import *
from std.debug import default_on_error
from std import __set__

Han = re.compile(r'\p{Han}')
Han2 = re.compile(r'\p{Han}{2,}')

Hiragana = re.compile(r'\p{Hiragana}')
Katakana = re.compile(r'\p{Katakana}')

Francais = re.compile('[éèàùçœæ]')
German = re.compile('[äöüß]')

Arabic = re.compile(r'\p{Arabic}')

Hangul = re.compile(r'\p{Hangul}')

Russian = re.compile(r'[А-Яа-я]+')
Ukrainian = re.compile(r'[А-Яа-яҐґІіЇїЄє]+')

def detect_language(text, fast=True):
    if fast:
        if Hiragana.search(text):
            return 'jp'

        if len(text) <= 2:
            if Han.search(text):
                return 'cn'
        else:
            if Han2.search(text):
                return 'cn'

        if Francais.search(text):
            return 'fr'

        if German.search(text):
            return 'de'

        if Arabic.search(text):
            return 'ar'

        if Hangul.search(text):
            return 'kr'
        
        # match mathematical formula:
        if m := re.match(r'\s*([^\n]*) = ([^\n]*)\s*$', text):
            if re.fullmatch(r'\w+', m[1]) or re.search('[^*/+-]', m[1]):
                if re.search('[^*/+-]', m[2]):
                    return 'math'
        if m := re.match(r'\s*([^\n]*) [≤≥] ([^\n]*)\s*$', text):
            return 'math'

        if Russian.search(text) or Ukrainian.search(text):
            return 'ru'

        if re.search('[a-zA-Z]', text):
            if Han.search(text):
                return
            return 'en'
        return

    if Han2.match(text):
        return 'cn'

    cn = 0
    en = 0

    mid = len(text) / 2
    for i, ch in enumerate(text):
        position_weight = (i - mid + 0.01) / mid
        position_weight = position_weight ** 2
        if re.compile(r'\p{Letter}').match(ch):
            if Han.match(ch):
                cn += 8 * position_weight
            else:
                en += position_weight

        elif re.compile(r'\p{Number}').match(ch):
            if ord(ch) > 256:
                cn += 2 * position_weight
            else:
                en += position_weight

        elif re.compile(r'\p{Punctuation}').match(ch):
            if ord(ch) > 256:
                cn += 2 * position_weight
            else:
                en += position_weight

        elif re.compile(r'\p{Symbol}').match(ch):
            ...
        elif re.compile(r'\p{Separator}').match(ch):
            ...
        elif re.compile(r'\p{Mark}').match(ch):
            ...
        else:
            ...
            
    if cn > en:
        return 'cn'

    if en > cn:
        return 'en'
    
    return 'en'


@__set__(Markdown, XMLParser)
def language_consistency(self, *_):
    yield from []

@__set__(MarkdownArgs)
def language_consistency(self, lang, min_scan_length, ignores):
    for arg in self.args:
        if type(arg) in ignores:
            continue
        yield from arg.language_consistency(lang, min_scan_length, ignores)

@__set__(MarkdownText)
def language_consistency(self, lang, min_scan_length, _):
    start_idx = self.start_idx
    end_idx = start_idx
    for ans in sbd(self.text):
        end_idx = start_idx + len(ans)
        hit = False
        if '\ufffd' in ans:
            # '�', Unicode Replacement Character, causing gibberish 
            scan_length = len(ans.encode())
            hit = True
        elif re.search(r'\w+', ans):
            if lang_ := detect_language(ans):
                if lang_ != 'math' and lang != lang_:
                    if lang not in ('en', 'de', 'fr') or lang_ not in ('en', 'de', 'fr'):
                        scan_length = len(ans.encode())
                        hit = scan_length >= min_scan_length
        if hit:
            yield {'text': ans, 'index': start_idx, 'tagName': self.parent.func, 'scan_length': scan_length}
        start_idx = end_idx

@default_on_error({'score' : -30})
def language_consistency(text, answer, lang=None, min_scan_length=32, ignores=["MarkdownA", "MarkdownB", "MarkdownBracket", "MarkdownLatex", "MarkdownCODE", "MarkdownPreCode", "MarkdownTABLE"], **_):
    '''
    Validate and score answer content based on language consistency, ignoring code blocks and tables.

    Processes text to check language consistency line-by-line, excluding markdown code blocks and tables.
    Returns a score based on invalid language lines and details about ignored content.

    Args:
        answer (str): The text content to validate (may contain markdown formatting).
        text (str, optional): Reference text used for language detection if lang isn't provided.
        lang (str, optional): Target language code (e.g., 'en', 'de'). If None, detected from `text`.
        min_scan_length (int, optional): minimum length of the inconsistent text piece

    Returns:
        dict: Result dictionary containing:
            - score (int): Penalty score (-number of lines with invalid language)
            - error (list, optional): Lines with language mismatches (excluded if no errors)
            - ignore (list, optional): Code blocks/tables removed from analysis (excluded if none)

    Processing Details:
    1. Removes markdown code blocks (```code```) and table headers from analysis
    2. Compares each text line's language against target language
    3. Allows mixing between 'en'/'de'/'fr' if target is one of these
    4. Empty/non-text lines are skipped in validation
    '''
    if lang is None:
        lang = detect_language(text)
        if lang is None or lang == 'math':
            lang = 'en'
    else:
        lang = lang.lower()
    answer = convert_block_latex(answer)
    tree = MarkdownParser.instance.build(answer)
    error = []
    score = 0
    for obj in tree.language_consistency(
        lang, 
        min_scan_length=min_scan_length, 
        ignores=
            [eval(cls) for cls in ignores] if ignores and isinstance(ignores[0], str) 
            else ignores
    ):
        score += obj['scan_length']
        error.append(obj)
    return {'error': error, 'score': -score / min_scan_length, 'min_scan_length': min_scan_length, 'ignores': ignores}

def test_batch(id=None, Rank=None, offset=0):
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
                    res = language_consistency(None, answer, lang=data['lang'])
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
    result = language_consistency(None, text, lang='cn')
    print('result =', result)

if __name__ == '__main__':
    # test()
    test_batch(
        id=2163312,
        Rank=1
    )

