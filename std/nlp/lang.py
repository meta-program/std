# -*- coding: UTF-8 -*-
import regex as re
from std.nlp.segment import sbd

Han = re.compile('\p{Han}')
Han2 = re.compile('\p{Han}{2,}')

Hiragana = re.compile('\p{Hiragana}')
Katakana = re.compile('\p{Katakana}')

Francais = re.compile('[éèàùçœæ]')
German = re.compile('[äöüß]')

Arabic = re.compile('\p{Arabic}')

Hangul = re.compile('\p{Hangul}')

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
        return 'en'

    if Han2.match(text):
        return 'cn'

    cn = 0
    en = 0

    mid = len(text) / 2
    for i, ch in enumerate(text):
        position_weight = (i - mid + 0.01) / mid
        position_weight = position_weight ** 2
        if re.compile('\p{Letter}').match(ch):
            if Han.match(ch):
                cn += 8 * position_weight
            else:
                en += position_weight

        elif re.compile('\p{Number}').match(ch):
            if ord(ch) > 256:
                cn += 2 * position_weight
            else:
                en += position_weight

        elif re.compile('\p{Punctuation}').match(ch):
            if ord(ch) > 256:
                cn += 2 * position_weight
            else:
                en += position_weight

        elif re.compile('\p{Symbol}').match(ch):
            ...
        elif re.compile('\p{Separator}').match(ch):
            ...
        elif re.compile('\p{Mark}').match(ch):
            ...
        else:
            ...
            
    if cn > en:
        return 'cn'

    if en > cn:
        return 'en'
    
    return 'en'


def language_switch(answer, text=None, lang=None):
    '''
    Validate and score answer content based on language consistency, ignoring code blocks and tables.

    Processes text to check language consistency line-by-line, excluding markdown code blocks and tables.
    Returns a score based on invalid language lines and details about ignored content.

    Args:
        answer (str): The text content to validate (may contain markdown formatting).
        text (str, optional): Reference text used for language detection if lang isn't provided.
        lang (str, optional): Target language code (e.g., 'en', 'de'). If None, detected from `text`.

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
    # remove any code block
    ignore = []
    if m := re.search(r'(?<=\n|^)```[a-zA-Z]+\d?\n.*?\n```(?=\n|$)', answer):
        ignore.append({'code': m[0]})
        answer = answer[:m.start()] + answer[m.end():]

    # match markdown table
    if m := re.search(r'(?<=\n|^)( *\|([^|\n]*\|)+ *(\n|$))+', answer):
        table = m[0].split('\n')
        if len(table) > 1:
            # remove table header
            ignore.append({'th': table[0]})
            answer = answer[:m.start()] + '\n'.join(table[1:]) + answer[m.end():]
    error = []
    for ans in sbd(answer):
        if not re.search(r'\w+', ans):
            continue
        lang_ = detect_language(ans)
        if lang == lang_:
            continue
        if lang in ('en', 'de', 'fr') and lang_ in ('en', 'de', 'fr'):
            continue

        error.append(ans)
    result = {"score": -len(error)}
    if error:
        result['error'] = error
    if ignore:
        result['ignore'] = ignore
    return result

if __name__ == '__main__':
    text = '*   **湿度过低:** 湿度过低会导致墨水快速干燥，容易在喷头表面结块，造成堵塞。Given low print utilizations of the ink printing apparatus, not all nozzles of the ink print heads are activated in the printing process. Many nozzles still have downtimes (printing pauses), with the result that the ink in the ink channel of these nozzles is not moved. Due to the effect of evaporation from the nozzle opening, the danger exists from this that the viscosity of the ink then changes[7].'
    result = language_switch(text, lang='cn')
    print('result =', result)

