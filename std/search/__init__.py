import std


# https://www.inf.fh-flensburg.de/lang/algorithmen/pattern/sundayen.htm
# https://en.wikipedia.org/wiki/Boyer%E2%80%93Moore_string-search_algorithm
# https://www.jianshu.com/p/2594d312cefd
def sunday(haystack, needle, haystackLength=None):
    
    needelLength = len(needle)
    
    if haystackLength:
        haystackLength = min(len(haystack), haystackLength)
    else:
        haystackLength = len(haystack)
    
    # If the needle contains duplicate characters, the dictionary will only store the last occurrence of each character. When a duplicate key is encountered, the previous value for that key is overwritten.
    dic = {v: needelLength - k for k, v in enumerate(needle)}
    
    end = needelLength
    
    while end <= haystackLength:
        begin = end - needelLength
        if haystack[begin: end] == needle:
            return begin

        if end >= haystackLength:
            return -1

        offset = dic.get(haystack[end])
        if not offset:
            offset = needelLength + 1
        
        end += offset

    return -1


std.compile_cpp(__file__)

from std.search.rabin_karp import repetition_penalty

if __name__ == '__main__':
    print(repetition_penalty('''
这是一篇陈词滥调的文章[1]。This is a clichéd article [2]. C’est un article plein de clichés [3].
这是一篇陈词滥调的文章[4]。C’est un article plein de clichés [6]. This is a clichéd article [5].
C’est un article plein de clichés [9]. 这是一篇陈词滥调的文章[7]。This is a clichéd article [8].
C’est un article plein de clichés [9]. This is a clichéd article [8]. 这是一篇陈词滥调的文章[7]。
This is a clichéd article [8]. C’est un article plein de clichés [9]. 这是一篇陈词滥调的文章[7]。
This is a clichéd article [8]. 这是一篇陈词滥调的文章[7]。C’est un article plein de clichés [9].
'''))

