import os
import re
import sys
import time
import pickle
import numpy as np
from tqdm import trange
from pypinyin import pinyin, lazy_pinyin, Style

curdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curdir)
with open(os.path.join(curdir, 'input_dict_nt_max.pickle'), 'rb') as handle:
    input_dict_nt_max = pickle.load(handle)

def remove_digits(x):
    return re.sub('[0-9]', '', x)

def pinyin_augment(_pinyin_list, hasTone):

    def iterate(prior, remains):
        if len(remains)==0:
            return [prior]
        else:
            result = []
            for name in remains[0]:
                new_prior = tuple([x for x in prior]+[name])
                result+=iterate(new_prior, remains[1:])
            return result

    def add_tones(r):
        if len(r)==0:
            return []
        if len(r)==1:
            result = []
            for tone in range(1,6):
                result.append(tuple([r[0]+str(tone)]))
            return result
        result = []
        for l in add_tones(r[1:]):
            for tone in range(1,6):
                result.append(tuple([r[0]+str(tone)]+list(l)))
        return list(set(result))

    pinyin_list = remove_digits(" ".join(_pinyin_list)).split()
    pys = []
    for py in pinyin_list:
        aug = [py]
        if py[:2]=='le' and len(py)==2:
            aug.append('re')
        if py[:1]=='n' and len(py)>1:
            aug.append('l'+py[1:])
        if py[:1]=='l' and len(py)>1:
            aug.append('n'+py[1:])
        if py[:1]=='c' and len(py)>1 and py[1:2]!='h':
            aug.append('ch'+py[1:])
        if py[:1]=='z' and len(py)>1 and py[1:2]!='h':
            aug.append('zh'+py[1:])
        if py[:1]=='s' and len(py)>1 and py[1:2]!='h':
            aug.append('sh'+py[1:])
        if py[:2]=='ch' and len(py)>2:
            aug.append('c'+py[2:])
        if py[:2]=='zh' and len(py)>2:
            aug.append('z'+py[2:])
        if py[:2]=='sh' and len(py)>2:
            aug.append('s'+py[2:])
        if py[-2:] in ['in', 'en', 'on'] and len(py)>1:
            aug.append(py[:-1]+"ng")
        if py[-3:] in ['ing', 'eng', 'ong'] and len(py)>2:
            aug.append(py[:-2]+"n")
        pys.append(aug)

    result_tmp = iterate((""), pys)
    result = []
    for item in result_tmp:
        result.append(item)
    result = list(set(result))
    if hasTone:
        result_ = []
        for r in result:
            result_ = result_+add_tones(list(r))
        return list(set(result_))
    else:
        return result

class Languagle_Model:

    def __init__(self):
        self.longest = 0
        self.pinyin_nt_set = set([])
        self.longest = max([len(x) for x in input_dict_nt_max])
        for key in input_dict_nt_max:
            if len(key)==1: self.pinyin_nt_set.add(key[0])

    def add_words(self, words, vague_add=False):
        for word in words:
            _py_nt = tuple([remove_digits(x) for x in self.translate_c2p(word)])
            input_dict_nt_max[_py_nt] = (word, 1)

    def translate_c2p(self, _str, hasTone=True):
        if hasTone:
            return lazy_pinyin(_str, style=Style.TONE3)
        return lazy_pinyin(_str)

    def translate_p2c(self, _pinyin, max_length=10, stride=1):

        def helper(_pinyin, _dict):
            if len(_pinyin) == 0:
                return ["", 0]

            rs = [(" ".join(_pinyin), 0)]
            for l in range(1,min(self.longest,len(_pinyin))+1):
                if l<len(_pinyin):
                    if tuple(_pinyin[:l]) in _dict:
                        r_prev = _dict[tuple(_pinyin[:l])]
                        r_late = helper(_pinyin[l:], _dict)
                        r = (r_prev[0]+r_late[0], r_prev[1]*r_late[1])
                        rs.append(r)
                elif l==len(_pinyin):
                    if tuple(_pinyin) in _dict:
                        r = _dict[tuple(_pinyin)]
                        rs.append(r)
            return sorted(rs, key=lambda kv: kv[1], reverse=True)[0]

        _pinyin = remove_digits(" ".join(_pinyin)).split()
        _input = [x for x in _pinyin if x in self.pinyin_nt_set]

        if len(_input)<(max_length+1):
            return helper(_input, input_dict_nt_max)[0]
        fixed = []
        last = "",-1,stride
        for start in range(0, len(_input)-max_length+stride, stride):
            text, prob = helper(_input[start:start+max_length], input_dict_nt_max)
            if prob>last[1] or start>=(len(fixed)+(len(last[0])-last[2])//stride*stride):
                fixed.append(text[:stride])
                last = text,prob,stride
            else:
                fixed.append(last[0][last[2]:last[2]+stride])
                last = last[0],last[1],last[2]+stride
        fixed.append(text[stride:])
        return "".join(fixed)

if __name__=="__main__":
    lm = Languagle_Model()

    print(lm.translate_c2p("我们都有光明的未来", hasTone=True))
    print(lm.translate_c2p("我们都有光明的未来", hasTone=False))
    print("----------------------------------------")

    print(lm.translate_p2c("jin1 tian1 de tian1 qi4 zhen1 bu4 cuo4".split()))
    print(lm.translate_p2c("shuang ye hong yu er yue hua".split()))
    print(lm.translate_p2c("yu shi wo ti chu le xin de jie jue fang an".split()))
