try:
    import simplepinyin as sp
    lm = sp.Languagle_Model()
except ImportError:
    import warnings
    warnings.warn("Did not found module simplepinyin.")
    lm = None

def str2pinyin(words, hasTone=False):
    if lm is not None:
        return lm.translate_c2p(words, hasTone=hasTone)
    else:
        return None

def pinyin2str(pinyins):
    if lm is not None:
        return lm.translate_p2c(pinyins.strip().split())
    else:
        return None
