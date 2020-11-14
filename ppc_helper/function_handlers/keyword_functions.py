import pymorphy2
from operator import itemgetter

morph = pymorphy2.MorphAnalyzer(lang='ru')

def kf_fixate_keywords(data, strict_pronoun=True):
    """
    Fixates words keyform in keywords with operators
    :param keywords: string; comma separated keywords
    :param strict_pronoun: boolean; If true fixates pronouns (Я, себе e t.c.)
    :param args: -
    :param kwargs: -
    :return: list of rows with header
    """
    keywords = data['data']
    sep = '\n' if '\n' in keywords else ','
    keywords = keywords.split(sep)

    def fixate_word_forms(keyword, strict_pronoun=strict_pronoun):
        keyword = keyword.split(' ')
        i = 0
        for k in keyword:
            tag = morph.parse(k)[0].tag
            w_type = str(tag.POS)
            if w_type in {'PREP', 'CONJ', 'PRCL', 'NPRO'}:
                if strict_pronoun and w_type == 'NPRO':
                    keyword[i] = f'!{k}'
                else:
                    keyword[i] = f'+{k}'
            i += 1
        return ' '.join(keyword)

    kws = [[w, fixate_word_forms(w)] for w in keywords]
    output = [['keyword', 'fixed']] + kws
    return output


def kf_group_duplicates(data):
    """
    :return: list of rows with header
    """
    keywords = data['data']
    sep = '\n' if '\n' in keywords else ','
    keywords = keywords.split(sep)
    keywords = [k.split(' ') for k in keywords]
    groups = {}
    for phrase in keywords:
        normalized_phrase = []
        for word in phrase:
            word = morph.parse(word)[0]
            w_type = str(word.tag.POS)
            if w_type in {'PREP', 'CONJ', 'PRCL', 'NPRO'}:
                continue
            normalized = word.normal_form
            normalized_phrase.append(normalized)
        phrase = ' '.join(phrase)
        normalized_phrase = ' '.join(normalized_phrase)
        groups[phrase] = normalized_phrase

    groups = [[v, k] for k, v in groups.items()]
    groups = sorted(groups, key=itemgetter(0))
    output = [['keyword_group', 'keywords']] + groups
    return output



