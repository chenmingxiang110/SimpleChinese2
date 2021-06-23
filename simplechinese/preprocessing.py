import re
import unicodedata
import numpy as np
import pandas as pd

table = {ord(f):ord(t) for f,t in zip(
    u'，。！？【】（）％＃＠＆１２３４５６７８９０',
    u',.!?[]()%#@&1234567890')}

def _parse(func, x):
    if isinstance(x, str):
        return func(x)
    elif isinstance(x, pd.DataFrame):
        return x.applymap(func)
    else:
        raise ValueError("The type of the input variable should be string or pandas.DataFrame.")

def only_digits(x):
    """
    Only keeps the digits in a string or a pandas.DataFrame.

    Args:
        x: The content to be parsed. Either a string or a pandas.DataFrame.

    Returns:
        A new string or a pandas.DataFrame only includes digits.
    |
    """

    def func(_s):
        return "".join([x for x in re.findall(r'[0-9]', _s)])
    return _parse(func, x)

def only_zh(x):
    """
    Only keeps Chinese characters in a string or a pandas.DataFrame.

    Args:
        x: The content to be parsed. Either a string or a pandas.DataFrame.

    Returns:
        A new string or a pandas.DataFrame only includes Chinese characters.
    |
    """

    def func(_s):
        return "".join([x for x in re.findall(r'[\u4e00-\u9fff]+', _s)])
    return _parse(func, x)

def only_en(x):
    """
    Only keeps English alphabets in a string or a pandas.DataFrame.

    Args:
        x: The content to be parsed. Either a string or a pandas.DataFrame.

    Returns:
        A new string or a pandas.DataFrame only includes English alphabets.
    |
    """

    def func(_s):
        return re.sub(r'[^\x41-\x5A\x61-\x7A ]', '', _s)
    return _parse(func, x)

def remove_space(x):
    """
    Remove all the spaces in a string or a pandas.DataFrame.

    Args:
        x: The content to be parsed. Either a string or a pandas.DataFrame.

    Returns:
        A new string or a pandas.DataFrame without spaces.
    |
    """

    def func(_s):
        return "".join(_s.split())
    return _parse(func, x)

def remove_digits(x):
    """
    Remove all the digits in a string or a pandas.DataFrame.

    Args:
        x: The content to be parsed. Either a string or a pandas.DataFrame.

    Returns:
        A new string or a pandas.DataFrame without digits.
    |
    """

    def func(_s):
        return re.sub('[0-9]', '', _s)
    return _parse(func, x)

def remove_zh(x):
    """
    Remove all the Chinese characters in a string or a pandas.DataFrame.

    Args:
        x: The content to be parsed. Either a string or a pandas.DataFrame.

    Returns:
        A new string or a pandas.DataFrame without Chinese characters.
    |
    """

    def func(_s):
        return re.sub(r'[\u4e00-\u9fff]+', '', _s)
    return _parse(func, x)

def remove_en(x):
    """
    Remove all the English alphabets in a string or a pandas.DataFrame.

    Args:
        x: The content to be parsed. Either a string or a pandas.DataFrame.

    Returns:
        A new string or a pandas.DataFrame without English alphabets.
    |
    """

    def func(_s):
        return re.sub(r'[\x41-\x5A\x61-\x7A]', '', _s)
    return _parse(func, x)

def remove_punctuations(x):
    """
    Remove all the punctuations in a string or a pandas.DataFrame.

    Args:
        x: The content to be parsed. Either a string or a pandas.DataFrame.

    Returns:
        A new string or a pandas.DataFrame without punctuations.
    |
    """

    def func(_s):
        return re.sub(r'[^\w\s]','',_s)
    return _parse(func, x)

def fillna(x):
    """
    Fill the N/As in a pandas.DataFrame with an empty string.

    Args:
        x: A pandas.DataFrame content to be parsed.

    Returns:
        A pandas.DataFrame without N/As, which are substituted with empty strings.
    |
    """

    return x.fillna("")
#     return x.applymap(lambda a: a if pd.notnull(a) else "")

def toLower(x):
    """
    Transform alphabets to their lowercases.

    Args:
        x: The content to be parsed. Either a string or a pandas.DataFrame.

    Returns:
        A new string or a pandas.DataFrame where the alphabets are in lowercases.
    |
    """

    def func(_s):
        return _s.lower()
    return _parse(func, x)

def toUpper(x):
    """
    Transform alphabets to their uppercases.

    Args:
        x: The content to be parsed. Either a string or a pandas.DataFrame.

    Returns:
        A new string or a pandas.DataFrame where the alphabets are in uppercases.
    |
    """

    def func(_s):
        return _s.upper()
    return _parse(func, x)

def punc_norm(x):
    """
    Normalize chinese punctuations and special characters
    """
    h = unicodedata.normalize('NFKC', x)
    h = h.translate(table)
    return h

def clean(x):
    """
    This function does the following:

    1. fillna(): Fill the N/As in a pandas.DataFrame with an empty string.

    2. toLower(): Transform alphabets to their lowercases.

    3. remove_punctuations(): Remove all the punctuations in a string or a pandas.DataFrame.

    4. remove_space(): Remove all the spaces in a string or a pandas.DataFrame.

    |
    """
    y = fillna(x)
    y = toLower(y)
    y = remove_punctuations(y)
    y = remove_space(y)
    return y
