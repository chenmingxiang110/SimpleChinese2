import re
import pickle
import warnings
import os
import sys

import numpy as np
import pandas as pd

import Levenshtein
from difflib import SequenceMatcher

from sklearn.neighbors import KDTree
from scipy.spatial import distance

from collections import OrderedDict
from collections.abc import MutableMapping

import jieba
jieba.setLogLevel(60)

class LimitedSizeDict(MutableMapping):
    def __init__(self, maxlen, items=None):
        self._maxlen = maxlen
        self.d = OrderedDict()
        if items:
            for k, v in items:
                self[k] = v

    @property
    def maxlen(self):
        return self._maxlen

    def __getitem__(self, key):
        self.d.move_to_end(key)
        return self.d[key]

    def __setitem__(self, key, value):
        if key in self.d:
            self.d.move_to_end(key)
        elif len(self.d) == self.maxlen:
            self.d.popitem(last=False)
        self.d[key] = value

    def __delitem__(self, key):
        del self.d[key]

    def __iter__(self):
        return self.d.__iter__()

    def __len__(self):
        return len(self.d)

curdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curdir)
with open(os.path.join(curdir, 'data', 'names.pickle'), 'rb') as handle:
    names = pickle.load(handle)
_nr = names['nr'] | names['nrt'] | names['nrfg']
_ns = names['nrt'] | names['ns'] | names['nt']
_n = set([])
for k in names.keys(): _n = _n | names[k]

with open(os.path.join(curdir, 'data', 'all_words.pickle'), 'rb') as handle:
    all_words = pickle.load(handle)
word_indices = {}
for i,w in enumerate(all_words):
    word_indices[w] = i
all_weights = np.load(os.path.join(curdir, 'data', 'all_weights_64.npy'))
kdt = KDTree(all_weights, leaf_size=10, metric = "euclidean")
all_weights_normed = all_weights/np.sqrt(np.sum(all_weights**2, 1, keepdims=True))
kdt = KDTree(all_weights_normed, leaf_size=10, metric = "euclidean")

cache=LimitedSizeDict(10000) # 缓存一万条最近的记录

def extract_nums(x, isList=False, dtype=float):
    """
    Extract the numbers from a string, a pandas.Series, or a pandas.DataFrame.

    Args:
        x: The content to be parsed. Either a string, a pandas.Series, or a pandas.DataFrame.

        isList: A boolean. If it is True, the returned value would be a list/lists of floats, or it would be a string/strings of numbers seperated by spaces.

    Returns:
        The numbers in the input data.

    |
    """

    def get_nums(x):
        def get_float(element):
            try:
                return float(element)
            except ValueError:
                return None
        nums = [get_float(n) for n in re.sub('[^0-9.]',' ', x).split()]
        nums = np.array([n for n in nums if n is not None]).astype(dtype)
        return list(nums)

    def func(x):
        nums = get_nums(x)
        if isList: return nums
        return " ".join([str(n) for n in nums])

    if isinstance(x, str):
        return get_nums(x)
    elif isinstance(x, pd.DataFrame):
        return x.applymap(func)
    elif isinstance(x, pd.Series):
        return x.apply(func)
    else:
        raise ValueError("The type of the input variable should be string, pd.Series, pandas.DataFrame.")

def extract_words(x, isList=False, mode=0, token="/"):
    """
    Extract the words from a string, a pandas.Series, or a pandas.DataFrame.

    Args:
        x: The content to be parsed. Either a string, a pandas.Series, or a pandas.DataFrame.

        isList: A boolean. If it is True, the returned value would be a list/lists, or it would be a string/strings of words seperated by the token.

        token: The token to seperate words if isList is False.

        mode: 0: No single character words. The words may be overlapped.
              1: Have single character words. The words may be overlapped.
              2: No single character words. The words are not overlapped.
              3: Have single character words. The words are not overlapped.
              4: Only single characters.

    Returns:
        The seperated words in the input data.

    |
    """

    if mode not in [0,1,2,3,4]:
        raise ValueError("The mode should be chosen from 0-4.")

    def get_words(_s):
        if mode in [0,1]:
            words = jieba.cut_for_search(_s)
        elif mode in [2,3]:
            words = jieba.cut(_s, cut_all=False)
        else:
            words = [n for n in _s]
        if mode in [1,3,4]:
            result = list(words)
        else:
            result = [n for n in words if len(n)>1]
        return result

    def func(x):
        words = get_words(x)
        if isList: return words
        return token.join([str(n) for n in words])

    if isinstance(x, str):
        return get_words(x)
    elif isinstance(x, pd.DataFrame):
        return x.applymap(func)
    elif isinstance(x, pd.Series):
        return x.apply(func)
    else:
        raise ValueError("The type of the input variable should be string, pd.Series, pandas.DataFrame.")

def extract_nouns(x, isList=False, split_mode=0, extract_mode="all", token="/"):
    """
    Extract the nouns from a string, a pandas.Series, or a pandas.DataFrame. This function is still under developing.

    Args:
        x: The content to be parsed. Either a string, a pandas.Series, or a pandas.DataFrame.

        isList: A boolean. If it is True, the returned value would be a list/lists, or it would be a string/strings of nouns seperated by the token.

        token: The token to seperate words if isList is False.

        mode: 0: No single character words. The words may be overlapped.
              1: Have single character words. The words may be overlapped.
              2: No single character words. The words are not overlapped.
              3: Have single character words. The words are not overlapped.
              4: Only single characters.

    Returns:
        The seperated nouns in the input data.

    |
    """

    if split_mode not in [0,1,2,3,4]:
        raise ValueError("The mode should be chosen from 0-4.")
    if extract_mode.lower() not in ["all", "person", "place"]:
        raise ValueError("The mode should be chosen from \"all\", \"person\", and \"place\".")
    if extract_mode in ["person", "place"]:
        warnings.warn("The function of extracting people or locations` names is still under developing...")

    def get_words(_s):
        if split_mode in [0,1]:
            words = jieba.cut_for_search(_s)
        elif split_mode in [2,3]:
            words = jieba.cut(_s, cut_all=False)
        else:
            words = [n for n in _s]
        if split_mode in [1,3,4]:
            result = list(words)
        else:
            result = [n for n in words if len(n)>1]

        if extract_mode=="person":
            result = [n for n in result if n in _nr]
        elif extract_mode=="place":
            result = [n for n in result if n in _ns]
        else:
            result = [n for n in result if n in _n]
        return result

    def func(x):
        words = get_words(x)
        if isList: return words
        return token.join([str(n) for n in words])

    if isinstance(x, str):
        return get_words(x)
    elif isinstance(x, pd.DataFrame):
        return x.applymap(func)
    elif isinstance(x, pd.Series):
        return x.apply(func)
    else:
        raise ValueError("The type of the input variable should be string, pd.Series, pandas.DataFrame.")

def string_distance(a,b,mode="Levenshtein"):
    if mode=="SequenceMatcher":
        return SequenceMatcher(None, a, b).ratio()
    elif mode=="Levenshtein":
        return Levenshtein.ratio(a, b)
    # elif mode=="Synonym":
    #     return synonyms.compare(a, b, seg=True)
    else:
        raise ValueError("Invalid Mode.")

def find_synonyms(a, n=10):
    res = []
    if a not in word_indices:
        return res
    if (a,n) in cache:
        return cache[(a,n)]
    index = word_indices[a]
    v = all_weights_normed[index]
    [distances], [points] = kdt.query(np.array([v]), k=n, return_distance=True)
    for point, d in zip(points, distances):
        score_cos = 1-distance.cosine(
            all_weights_normed[index],
            all_weights_normed[point]
        )
        res.append((all_words[point], score_cos))
    cache[(a,n)] = res
    return res
