# to comply with the standards of java and mysql regex engine
import regex as re
from functools import singledispatch
from std import cpp
import math
from std.cpp import instance, VectorS, String, MatrixS

# instance.ahocorasick_jws_segment[String] = VectorS
instance.ahocorasick_jws_split[String] = VectorS
instance.ahocorasick_jws_split_digits[String] = VectorS
instance.ahocorasick_jws_split_s[VectorS] = MatrixS
instance.ahocorasick_jws_split_s_digits[VectorS] = MatrixS
# instance.ahocorasick_jws_split_s_debug[VectorS] = MatrixS

    
@singledispatch
def normalize(text):
    return normalize_n(text)


@normalize.register(list)
def _(text):
    return [normalize(word) for word in text]


def normalize_n(word):
    word = re.compile('\n').sub(r'\\n', word)
    word = word.strip()
    word = word.lower()
    return word


def normalize_d(word):
    word = re.compile('\n').sub(r'\\n', word)
    word = re.compile('\d').sub(r'\d', word)
    word = word.strip()
    word = word.lower()
    return word


def split(text):
    return cpp.instance.ahocorasick_jws_split(text)

    
def test_split(limit=None):
    from std import MySQL
    err = 0
    sgm = 0
        
    sql = 'select text from tbl_segment_jp '
    if limit:
        sql += 'limit %s' % limit
        
    text = [text for text, *_ in MySQL.instance.select(sql)]
    
    array = split(text)
    for array, text in zip(array, text):
        if ''.join(array) != text:
            print(text)
            print(''.join(array))
            err += 1
        sgm += 1
        
    print('err =', err)
    print('sgm =', sgm)
    print('acc =', (sgm - err) / sgm)


sPunctuation = ",.:;!?()\\[\\]{}'\"=<>，。：；！？（）「」『』【】～‘’′”“《》、…．·"


def convertFromSegmentation(arr):
    s = ""
    for i in range(len(arr) - 1):
        s += arr[i]

        if arr[i][-1] in sPunctuation or arr[i + 1][0] in sPunctuation:
            continue
        s += " "

    s += arr[-1]
    return s


def convertToSegmentation(s):
    s = re.compile("([" + sPunctuation + "])").sub(' \\1 ', s)

    s = re.compile('(?<=[\\d])( +([\\.．：:]) +)(?=[\\d]+)').sub('\\2', s)

    while True:
        s, n = re.compile("([" + sPunctuation + "]) +\\1").subn('\\1\\1', s)
        if not n:
            break

    return s.strip().split()


def isEnglish(ch):
    return 'a' <= ch <= 'z' or 'A' <= ch <= 'Z' or 'ａ' <= ch <= 'ｚ' or 'Ａ' <= ch <= 'Ｚ'\
        or '0' <= ch <= '9' or '０' <= ch <= '９'
#     return re.compile('[a-zA-Zａ-ｚＡ-Ｚ\d]').match(ch)


def convertToOriginal(arr):
    s = ""
    for i in range(len(arr) - 1):
        s += arr[i]

        if isEnglish(arr[i][-1]) and isEnglish(arr[i + 1][0]):
            s += " "

    s += arr[-1]
    return s


def establish_vocabFile(weightsDirectory):
    from std import MySQL
    instance = MySQL.instance
    deletes = []
    updates = []

    def initialize(dic):
        for text, segement in instance.select("select text, seg from tbl_segment_jp"):
            seg = convertToSegmentation(segement)
            _text = convertToOriginal(seg)
            if text != _text:
#                 print(text)
#                 print(_text)
#                 print(' '.join(seg))
                deletes.append((text,))
                updates.append((_text, segement))
            for seg in seg:
                if len(seg) == 1:
                    continue
                
                if seg in dic:
                    dic[seg] += 1
                else:
                    dic[seg] = 1
            
        for key in dic:
            dic[key] = math.sqrt(dic[key] * len(key))
            
        utility.normalize(dic)

    vocabFile = weightsDirectory + "jp/segment/vocab.csv"
    
    from std.file import Text
    olddic = {}
    for line in Text(vocabFile):
        text, weight = line.split('\t')
        olddic[text] = float(weight)
    
#     normalize(olddic)
    
    newdic = {}
    initialize(newdic)
    
    print('olddic.keys() - newdic.keys()', olddic.keys() - newdic.keys())
    for key in olddic.keys() - newdic.keys():
        del olddic[key]

    print('newdic.keys() - olddic.keys()', newdic.keys() - olddic.keys())
    for key in newdic.keys() - olddic.keys():
        olddic[key] = newdic[key]

    std.normalize(olddic)

    with open(vocabFile, 'w', encoding='utf8') as file:
        for text, cnt in olddic.items():
            print(text + '\t' + str(cnt), file=file)

    from std.file import eol_convert
    eol_convert(vocabFile)

    if updates:
        instance.load_data('tbl_segment_jp', updates, replace=True)

    if deletes:
        sql = 'delete from tbl_segment_jp where text = %s'
        print(sql)
        instance.executemany(sql, deletes)


if __name__ == '__main__':
    print(split('-(o-1)</sub>の出力と前記第3のゲート回路34<sub>-o</sub>の出力とを入力するアンドゲート回路35を備え、'))
