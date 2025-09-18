import regex as re

dot_lookbehind = [
    r'\b([a-z]+|[A-Z][a-z]*)\s+\d+',
    r'\b[a-z]+',
    r'((\b[A-Z]?[a-z]+)*| +[A-Z]+\.) +[A-Z][a-z]+', # The famous person is Martin Luther K.jr, JPR. Hendrikson
    r'\b[A-Z]?[a-z]+\s+[A-Z]+', # Washington DC
    r'\w+ +([A-Z]\.)+[A-Z]', # U.S.A.
    r'[;!?；！？…。"\'’”\da-zA-Z][)\]}）】｝]', # even includes motivational expressions ("Three times the money, three times the fun!"). Today is a nice day
]
dot_lookbehind = '|'.join(dot_lookbehind)

dot_negative_lookbehind = [
    r' vs', # vs. versus
    r' v',  # v. versus
    r's.t', # subject to
    r'etc', # etc. et cetera
]
dot_negative_lookbehind = '|'.join(dot_negative_lookbehind)

first_token = '|'.join([
    "[A-Z][a-z]*®?",
    "[A-Z][A-Z]+s?",
    r"[A-Z]\d+",
])

second_token = '|'.join([
    r"[ _-]\w+\b",
    ",",
    ''' ?[“‘"'`(]''',
])

dot_lookahead = [
    fr'''(?:{first_token})(?:{second_token})''',
    r'''[“‘"'`\d]''',
    r" *\|(?:\s|$)", # consider the case: | **Microstructure**     | Alternating layers of ferrite and cementite[1].      | Plate-like or acicular ferrite with dispersed carbides[10].          |
]
dot_lookahead = '|'.join(dot_lookahead)

def merge_next_line(texts, nextLine):
    if texts:
        prevLine = texts[-1]
        if m := re.search(r'(?<=\n)[ \t]+$', prevLine):
            index = m.start()
            texts[-1] = prevLine[:index]
            return prevLine[index:] + nextLine
        elif re.search(r'\b[a-z\d]! *$', prevLine) and re.match(' *[*-*/()]', nextLine):
            # deal with mathematical factorial expression n! / r!
            texts[-1] += nextLine
            return ''

englishSentenceRegex = fr'''(?<={dot_lookbehind})(?<!{dot_negative_lookbehind})[.．]\s+(?={dot_lookahead})'''

def sbd(text):
    m = re.match(r'[;!?；！？…。\s]+', text)
    if m:
        leadingDelimiters = m.group()
        text = text[len(leadingDelimiters):]
    else:
        leadingDelimiters = ''
    
    regex = r"[^;!?；！？…。\r\n]+[;!?；！？…。\s]*"
    texts = []
    hasContext = False
    for m in re.finditer(regex, text):
        line = m.group()
        # if the current sentence is correct, skipping processing!
        if not re.match('[’”]', line):
            # considering the following case:
            # ("Going once, going twice, gone!") and even includes motivational expressions
            if (end := m.end()) < len(text) and text[end] in '")]}）】｝’”':
                if hasContext:
                    texts[-1] += line
                else:
                    newLine = merge_next_line(texts, line)
                    if newLine:
                        texts.append(newLine)
                    elif newLine is None:
                        texts.append(line)
                    hasContext = True
                continue
            # sentence boundary detected!
            start = 0
            # consider the following case: 1. firstly...  2. secondly... 3. thirdly...
            # the best answer is answer 1. Answer 2 is not correct.
            englishSentences = []
            for englishSentenceMatch in re.finditer(englishSentenceRegex, line):
                end = englishSentenceMatch.end()
                englishSentences.append(line[start:end])
                start = end
            
            englishSentences.append(line[start:] if start else line)
            if hasContext:
                texts[-1] += englishSentences[0]
                englishSentences = englishSentences[1:]
                hasContext = False
            if texts and englishSentences:
                if line := merge_next_line(texts, englishSentences[0]):
                    englishSentences[0] = line
                elif line == '':
                    englishSentences = englishSentences[1:]
            texts += englishSentences
            continue

        hasContext = False
        boundaryIndex = 0
        if re.match(r'.[,)\]}，）】｝》、的]', line):
            # for the following '的 ' case, this sentence should belong to be previous one:
            # ”的文字，以及选项“是”和“否”。
            if line[1:3] == '的确':
                # for the following special case:
                # ”的确， GPS和其它基于卫星的定位系统为了商业、公共安全和国家安全的用 途而快速地发展。
                boundaryIndex = 1
            else:
                # for the following comma case:
                # ”,IEEE Jounalon Selected Areas in Communications,Vol.31,No.2,Feburary2013所述。
                if texts:
                    texts[-1] += line
                else:
                    texts = [line]
        else:
            m = re.match(r'.[;.!?:；。！？：…\r\n]+', line)
            boundaryIndex = m.end() if m else 1
            # considering the following complex case:
            # ”!!!然后可以通过家长控制功能禁止观看。

        if boundaryIndex:
            if not texts:
                texts.append('')
            texts[-1] += line[:boundaryIndex]  # sentence boundary detected! insert end of line here
            if boundaryIndex < len(line):
                latter = line[boundaryIndex:]
                if m := re.match(r'\s+', latter):
                    texts[-1] += m.group()
                    latter = latter[m.end():]
                    if not latter:
                        continue
                texts.append(latter)

    if leadingDelimiters:
        if texts:
            texts[0] = leadingDelimiters + texts[0]
        else:
            texts.append(leadingDelimiters)
    assert ''.join(texts) == leadingDelimiters + text
    return texts

if __name__ == '__main__':
    text = [
        'Some of the best genealogy sites also offer best DNA testing kits, which offer a new avenue for finding relatives [2]. You can access some of the best DNA testing kits via these websites, which can reveal information about your ancient ancestors [2]. These specialized platforms hold digitized versions of things like census records, marriage certificates, and ship passenger information [1]. For example, some of these services also offer some the best family tree makers, which allows you to keep a visual record of your findings [1].' ,
        "Sites like Ancestry track your ancestors by using advanced genetic technology and sophisticated algorithms to analyze your DNA. Here's a general overview of how the process works:",
        "    The famous people is Martin Luther K.jr, JPR. Hendrikson. They are from U.S.A.", 
        "    Martin Luther K. Jr. delivered one of his powerful speeches in Washington D.C. I want to go there.",          #bad case
        "Martin Luther K. Jr. delivered one of his powerful speeches in Washington DC. I want to go there.",          #bad case
        "The famous people is Martin Luther K.jr. I want to visit him.",
        "Martin Luther K.jr. JPR. Hendrikson J.P.R. Hendrikson. U.S.A.",
        "My Father lived in U.S.A. He is a great man",
        "My Father lived in USA. He is a great man",
        "The new technology became broadly available in 2023. This innovation marked a turning point for many industries worldwide.",  #Sentence ends with word and digit.The next sentence starts with Word.
        "U.S.S.R. is a country. It is a big country. It is a powerful country. It is a country that no longer exists.", #Sentence ends with word.The next sentence starts with Word.
        "Many companies seek to establish headquarters in the UK. Each location offers unique advantages and challenges.", #Sentence ends with WORD.The next sentence starts with word.
        "There are some steps you can take to protect yourself from the flu. 1. make sure to wash your hands regularly. 2. avoid close contact with people who are sick. 3. get a flu shot every year.", #Sentence ends with word.The next sentence starts with digit.
        "？？ ！P.R.C. is a country is a powerful country. It is a country that still exists.", #Sentence ends with word.The next sentence starts with word.
        "The global pandemic drastically changed the way we interact and communicate with each other in 2020. 2021 brought new challenges and some hope as vaccines became widely available.", #Sentence ends with digit.The next sentence starts with digit.
        "The pandemic broke out in December 2020. Many people died from this disease. The world was not prepared for this crisis at that moment.", #Sentence ends with digit.The next sentence starts with Word.
        "China is a happy country. 'I am very proud of my country,' said the president of China. ", #Sentence ends with word.The next sentence starts with Chinese single quotation.
        'China is a happy country. "I am very proud of my country," said the president of China. ', #Sentence ends with word.The next sentence starts with Chinese double quotation.
        "？？？。。。China is a happy country. ‘I am very proud of my country,’ said the president of China. ", #Sentence ends with word.The next sentence starts with English single quotation.
        'China is a happy country. “I am very proud of my country,” said the president of China. ', #Sentence ends with word.The next sentence starts with English double quotation.
        '    The number of foreign people learning Chinese increased significantly in 2023. "Chinese language may become the most popular language in the future." said the specialist', #Sentence ends with word and digit.The next sentence starts with English double quotation.
        "    The number of foreign people learning Chinese increased significantly in 2023. 'Chinese language may become the most popular language in the future.' said the specialist", #Sentence ends with word and digit.The next sentence starts with English single quotation.
        'The number of foreign people learning Chinese increased significantly in 2023. “Chinese language may become the most popular language in the future.” said the specialist', #Sentence ends with word and digit.The next sentence starts with Chinese double quotation.
        "The number of foreign people learning Chinese increased significantly in 2023. ‘Chinese language may become the most popular language in the future.’ said the specialist", #Sentence ends with word and digit.The next sentence starts with Chinese single quotation.
        'The British Museum is a great place in the UK. "If you have the chance to visit the UK, you must go to the British Museum." a British person would say.', #Sentence ends with WORD.The next sentence starts with English double quotation.
        "The British Museum is a great place in the UK. 'If you have the chance to visit the UK, you must go to the British Museum.' a British person would say.", #Sentence ends with WORD.The next sentence starts with English single quotation.
        'The British Museum is a great place in the UK. “If you have the chance to visit the UK, you must go to the British Museum.” a British person would say.', #Sentence ends with WORD.The next sentence starts with Chinese double quotation.
        "The British Museum is a great place in the UK. ‘If you have the chance to visit the UK, you must go to the British Museum.’ a British person would say.", #Sentence ends with WORD.The next sentence starts with Chinese single quotation.
        "\nOne of the eight wonders of the world, the Great Wall, is in China. 'I must go and see it one day,' said a foreigner.", #Sentence ends with Word.The next sentence starts with English single quotation.
        'One of the eight wonders of the world, the Great Wall, is in China. "I must go and see it one day," said a foreigner.', #Sentence ends with Word.The next sentence starts with English double quotation.
        'One of the eight wonders of the world, the Great Wall, is in China. “I must go and see it one day,” said a foreigner.', #Sentence ends with Word.The next sentence starts with Chinese double quotation.
        "\n\nOne of the eight wonders of the world, the Great Wall, is in China. ‘I must go and see it one day,’ said a foreigner.", #Sentence ends with Word.The next sentence starts with Chinese single quotation.
        "The journey took us across various states, all the way to the bustling city where our adventures reached their peak in  America. Next, we planned to visit the historic monuments and experience the rich culture firsthand.",   #Sentence ends with Word.The next sentence starts with word.
        "The journey took us across various states, all the way to the bustling city where our adventures reached their peak in america. Next, we planned to visit the historic monuments and experience the rich culture firsthand.",   #Sentence ends with word.The next sentence starts with word.
        "The journey took us across various states, all the way to the bustling city where our adventures reached their peak in America. Next we planned to visit the historic monuments and experience the rich culture firsthand.",   #Sentence ends with Word.The next sentence starts with word(without comma).
        "However, Answer 1 provides a slightly more detailed response by also mentioning time differences, data accuracy, user-specific settings, and how to ensure the accuracy of currency values in Google Finance. Therefore, Answer 1 is slightly better than Answer 2.", #Sentence ends with two Word.The next sentence starts with Word.
        '我觉得你说得对ai在某些地方确实能替代人类\n但是ai不可能完全能够替代人类',        
        "However, Answer 1 provides a slightly more detailed response by also mentioning time differences, data accuracy, user-specific settings, and how to ensure the accuracy of currency values in Google Finance. Therefore, Answer 1 is slightly better than Answer 2.",  # Sentence ends with two Words.The next sentence starts with Word.
        "This response accurately lists popular game development engines like Unity, Unreal Engine, Godot, and GameMaker Studio. It correctly identifies the programming languages associated with each engine and mentions their capabilities in terms of supporting different platforms.",    # Sentence ends with many Words.The next sentence starts with Word.
        '\n\n??The difference lies slightly in the phrasing of urgency ("immediately" vs. "immediate") which effectively does not change the meaning or the urgency significantly. Both answers are equally clear and concise.',
        '我已经把五笔输入法给下载好了。要不要来看看',
        'Answer 1 provides a more complete explanation by listing out typical phrases one might hear from an auctioneer ("Going once, going twice, gone!") and even includes motivational expressions ("Three times the money, three times the fun!"). Today is a nice day',
        '根据问题的字面意思——‘行用卡借1####一年还，每个月还多少呢？’ —— 答案1更加符合问题的需求，因为它直接处理了如何计算基于不同还款方式的每月还款金额，而且提供了适用于大多数信用卡用户的普遍信息。虽然问题中存在一些模糊或语法上的错误，使得其真正的意图不太清晰，但从信用卡还款的角度考虑，答案1提供了更多相关且实用的信息。',
        '根据问题的字面意思——"行用卡借1####一年还，每个月还多少呢？"。 答案1更加符合问题的需求，因为它直接处理了如何计算基于不同还款方式的每月还款金额，而且提供了适用于大多数信用卡用户的普遍信息。虽然问题中存在一些模糊或语法上的错误，使得其真正的意图不太清晰，但从信用卡还款的角度考虑，答案1提供了更多相关且实用的信息。',
        '根据问题的字面意思——“行用卡借1####一年还，每个月还多少呢？”。 答案1更加符合问题的需求，因为它直接处理了如何计算基于不同还款方式的每月还款金额，而且提供了适用于大多数信用卡用户的普遍信息。虽然问题中存在一些模糊或语法上的错误，使得其真正的意图不太清晰，但从信用卡还款的角度考虑，答案1提供了更多相关且实用的信息。',
        '根据问题的字面意思——“行用卡借1####一年还，每个月还多少呢？”； 答案1更加符合问题的需求，因为它直接处理了如何计算基于不同还款方式的每月还款金额，而且提供了适用于大多数信用卡用户的普遍信息。虽然问题中存在一些模糊或语法上的错误，使得其真正的意图不太清晰，但从信用卡还款的角度考虑，答案1提供了更多相关且实用的信息。',
        '根据问题的字面意思——“行用卡借1####一年还，每个月还多少呢？”！ 答案1更加符合问题的需求，因为它直接处理了如何计算基于不同还款方式的每月还款金额，而且提供了适用于大多数信用卡用户的普遍信息。虽然问题中存在一些模糊或语法上的错误，使得其真正的意图不太清晰，但从信用卡还款的角度考虑，答案1提供了更多相关且实用的信息。',
        '明天又要下大雨了。‘又要下一周的雨’',
        '‘明天又要下大雨了’。‘又要下一周的雨’',
        '“明天又要下大雨了”。‘又要下一周的雨’',
        '“明天又要下大雨了”。“又要下一周的雨”',
        '“明天又要下大雨了”；“又要下一周的雨”',
        '“明天又要下大雨了”、“又要下一周的雨”',
        '“明天又要下大雨了”“又要下一周的雨”',
        '“明天又要下大雨了”!“又要下一周的雨”',
        '这是他说：“明天又要下大雨了”的话',
        '这是他说：“明天又要下大雨了！”的话',
        '''
作为一个聊天机器人，我背后实现的核心原理是基于人工智能（AI）和自然语言处理（NLP）技术。以下是一些关键概念和技术：

1. **自然语言处理（NLP）**：
   - **词法分析**：将输入的文本分解为单词或词组。
   - **语法分析**：确定单词之间的语法关系。
   - **语义理解**：理解文本的意义和意图。
   - **情感分析**：识别文本中的情感和态度。

2. **机器学习**：
   - **监督学习**：通过标注好的数据集来训练模型，使模型能够预测和分类新的输入。
   - **无监督学习**：对未标注的数据进行分析和聚类。
   - **强化学习**：通过与环境的互动来学习最佳策略。

3. **深度学习**：
   - **神经网络**：特别是深度神经网络（DNN），用于复杂的模式识别和特征提取。
   - **递归神经网络（RNN）**和**长短期记忆网络（LSTM）**：用于处理序列数据，如文本。
   - **转换器（Transformer）模型**：如BERT（Bidirectional Encoder Representations from Transformers）、GPT（Generative Pre-trained Transformer）等，这些模型在语言理解和生成方面表现出色。

4. **对话管理**：
   - **意图识别**：确定用户意图。
   - **实体识别**：从文本中提取有用的信息，如日期、地点、人物等。
   - **上下文管理**：保持对话的上下文，确保对话的连贯性。

5. **响应生成**：
   - **模板化回复**：使用预定义的回复模板。
   - **基于检索的回复**：从预定义的对话库中查找最相关的回复。
   - **生成式回复**：使用自然语言生成技术，根据输入内容生成合适的回复。

6. **多模态融合**：
   - **语音识别**：将语音转换为文本。
   - **文本到语音**：将文本转换为语音。
   - **视觉理解**：处理图像和视频内容，结合文本输入进行更全面的对话。

这些技术协同工作，使我能够理解用户的输入，进行合理的对话管理和生成自然的回复。当然，实际的实现还包括许多其他细节和优化，例如处理多语言、应对模糊输入、提高响应速度和准确性等。'''
    ]

    for text in text:
        for t in sbd(text):
            print(t)
