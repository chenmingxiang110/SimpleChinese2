import codecs
import jieba
import kenlm
import numpy as np
import operator
import os
import time
from pypinyin import lazy_pinyin

from .utils.logger import logger
from .utils.text_utils import *


class ErrorType(object):
    confusion = 'confusion'
    word = 'word'
    char = 'char'


class Corrector(object):

    def __init__(self, config):
        self.confusion_path = config.confusion_path
        self.word_dict_path = config.word_dict_path
        self.same_pinyin_path = config.same_pinyin_path
        self.same_stroke_path = config.same_stroke_path
        self.char_set_path = config.char_set_path
        self.lm_model_path = config.lm_model_path
        self.pinyin2word_path = config.pinyin2word_path

        self.confusion_dict = self._load_confusion_dict(self.confusion_path)
        self.word_dict = self._load_word_dict(self.word_dict_path)
        self.same_pinyin_dict = self._load_same_pinyin_dict(self.same_pinyin_path)
        self.same_stroke_dict = self._load_same_stroke_dict(self.same_stroke_path)
        self.pinyin2word = self._load_pinyin_2_word(self.pinyin2word_path)
        self.char_set = self._load_char_set(self.char_set_path)
        self.tokenizer = jieba
        self.lm = kenlm.Model(self.lm_model_path)

    def _load_confusion_dict(self, path):
        confusion = {}
        if not os.path.exists(path):
            logger.warning('File not found: %s' % path)
            return confusion
        with codecs.open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    continue
                info = line.split()
                if len(info) < 2:
                    continue
                variant = info[0]
                origin = info[1]
                confusion[variant] = origin
        self.confusion_path = path
        return confusion

    def _load_word_dict(self, path):
        word_freq = {}
        if not os.path.exists(path):
            logger.warning('file not found: %s' % path)
            return word_freq
        with codecs.open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    continue
                info = line.split()
                if len(info) < 1:
                    continue
                word = info[0]
                # ??????????????????1
                freq = int(info[1]) if len(info) > 1 else 1
                word_freq[word] = freq
        self.word_dict_path = path
        return word_freq

    def _load_same_pinyin_dict(self, path, sep='\t'):
        result = dict()
        if not os.path.exists(path):
            logger.warn("file not exists: %s" % path)
            return result
        with codecs.open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    continue
                parts = line.split(sep)
                if parts and len(parts) > 2:
                    key_char = parts[0]
                    same_pron_same_tone = set(list(parts[1]))
                    same_pron_diff_tone = set(list(parts[2]))
                    value = same_pron_same_tone.union(same_pron_diff_tone)
                    if key_char and value:
                        result[key_char] = value
        self.same_pinyin_path = path
        return result

    def _load_same_stroke_dict(self, path,  sep='\t'):
        result = dict()
        if not os.path.exists(path):
            logger.warn("file not exists: %s" % path)
            return result
        with codecs.open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    continue
                parts = line.split(sep)
                if parts and len(parts) > 1:
                    for i, c in enumerate(parts):
                        result[c] = set(list(parts[:i] + parts[i + 1:]))
        self.same_stroke_path = path
        return result

    def _load_pinyin_2_word(self, path):
        result = dict()
        if not os.path.exists(path):
            logger.warn("file not exists: %s" % path)
            return result
        with codecs.open(path, 'r', encoding='utf-8') as f:
            a = f.read()
            result = eval(a)
        return result

    def _load_char_set(self, path):
        words = set()
        with codecs.open(path, 'r', encoding='utf-8') as f:
            for w in f:
                w = w.strip()
                if w.startswith('#'):
                    continue
                if w:
                    words.add(w)
        return words

    def _check_state(self):
        res = True
        res &= self.confusion_dict is not None
        res &= self.word_dict is not None
        res &= self.same_pinyin_dict is not None
        res &= self.same_stroke_dict is not None
        return res

    def _process_text(self, text):
        # ???????????????utf-8 to unicode
        text = convert_to_unicode(text)
        # text = uniform(text)
        return text

    def _check_in_errors(self, maybe_errors, maybe_err):
        error_word_idx = 0
        begin_idx = 1
        end_idx = 2
        for err in maybe_errors:
            if maybe_err[error_word_idx] in err[error_word_idx] and maybe_err[begin_idx] >= err[begin_idx] and \
                    maybe_err[end_idx] <= err[end_idx]:
                return True
        return False

    def _get_max_len(self, d):
        return max(map(len, [w for w in d]))

    def FMM(self, word_dict, token, window_size=5):
        idxs = []
        result = []
        index = 0
        text_size = len(token)
        while text_size > index:
            for size in range(1,window_size):
                piece = token[index:index+size]
                if piece in word_dict:
                    idxs.append(index)
                    result.append(piece)
                    index = index+size
                    break
            index = index + 1
        return idxs, result

    def _is_filter_token(self, token):
        # ???
        if not token.strip():
            return True
        # ????????????
        if is_alphabet_string(token):
            return True
        # ????????????
        if token.isdigit():
            return True
        # ?????????????????????
        if is_alp_diag_string(token):
            return True
        # ??????????????????
        if re_poun.match(token):
            return True

        return False

    def _get_maybe_error_index(self, scores, ratio=0.6745, threshold=2):
        """
        ??????????????????????????????????????????????????????MAD???
        :param scores: np.array
        :param ratio: ?????????????????????
        :param threshold: ??????????????????????????????????????????
        :return: ????????????????????????index: list
        """
        result = []
        scores = np.array(scores)
        if len(scores.shape) == 1:
            scores = scores[:, None]
        median = np.median(scores, axis=0)  # get median of all scores
        margin_median = np.abs(scores - median).flatten()  # deviation from the median
        # ?????????????????????
        med_abs_deviation = np.median(margin_median)
        if med_abs_deviation == 0:
            return result
        y_score = ratio * margin_median / med_abs_deviation
        # ??????
        scores = scores.flatten()
        maybe_error_indices = np.where((y_score > threshold) & (scores < median))
        # ???????????????????????????index
        result = list(maybe_error_indices[0])
        return result

    def _detect_by_confusion(self, maybe_errors, sentence, start_idx):
        """
        ???????????????????????????????????????
        :param maybe_errors: ???????????????
        :param sentence: ????????????
        :param start_idx: ????????????????????????
        """
        # ????????????-??????????????????????????? : ???????????? 0.0002701282501220703 s
        # stat_time = time.time()
        # for confuse in self.confusion_dict:
        #     idx = sentence.find(confuse)
        #     if idx > -1:
        #         maybe_err = [confuse, idx + start_idx, idx + len(confuse) + start_idx, ErrorType.confusion]
        #         if maybe_err not in maybe_errors and not self._check_in_errors(maybe_errors, maybe_err):
        #             maybe_errors.append(maybe_err)
        # ??????????????????-???????????????????????????
        max_len = self._get_max_len(self.confusion_dict.keys())
        idxs, confuses = self.FMM(self.confusion_dict, sentence, max_len)
        if len(idxs) > 0:
            for idx, confuse in zip(idxs, confuses):
                maybe_err = [confuse, idx + start_idx, idx + len(confuse) + start_idx, ErrorType.confusion]
                if maybe_err not in maybe_errors and not self._check_in_errors(maybe_errors, maybe_err):
                    maybe_errors.append(maybe_err)
        # print('detect_by_confusion ????????? {}'.format(time.time()-stat_time))

    def _detect_by_token(self, maybe_errors, sentence, start_idx):
        """
        ???????????????????????????????????????????????????
        :param maybe_errors: ???????????????
        :param sentence: ????????????
        :param start_idx: ????????????????????????
        """
        # ??????
        tokens = self.tokenizer.tokenize(sentence, mode='search')
        # ????????????????????????????????????
        for token, begin_idx, end_idx in tokens:
            # pass filter word
            if self._is_filter_token(token):
                continue
            # pass in dict
            if token in self.word_dict:
                continue
            maybe_err = [token, begin_idx + start_idx, end_idx + start_idx, ErrorType.word]
            if maybe_err not in maybe_errors and not self._check_in_errors(maybe_errors, maybe_err):
                maybe_errors.append(maybe_err)

    def _detect_by_word_ngrm(self, maybe_errors, sentence, start_idx):
        try:
            ngram_avg_scores = []
            tokens = [x for x in self.tokenizer.cut(sentence)]
            for n in [1, 2, 3]:
                scores = []
                for i in range(len(tokens) - n + 1):
                    word = tokens[i:i + n]
                    score = self.lm.score(' '.join(list(word)), bos=False, eos=False)
                    scores.append(score)
                if not scores:
                    continue
                # ????????????????????????
                for _ in range(n - 1):
                    scores.insert(0, scores[0])
                    scores.append(scores[-1])
                    # scores.append(sum(scores)/len(scores))
                avg_scores = [sum(scores[i:i + n]) / len(scores[i:i + n]) for i in range(len(tokens))]
                ngram_avg_scores.append(avg_scores)

            if ngram_avg_scores:
                # ???????????????n-gram????????????
                sent_scores = list(np.average(np.array(ngram_avg_scores), axis=0))
                # ?????????????????????
                for i in self._get_maybe_error_index(sent_scores, threshold=1):
                    token = tokens[i]
                    i = sentence.find(token)
                    if len(token) == 1:
                        type = ErrorType.char
                    else:
                        type = ErrorType.word
                    maybe_err = [token, i+start_idx, i+len(token)+start_idx, type]
                    if maybe_err not in maybe_errors and not self._check_in_errors(maybe_errors, maybe_err):
                        maybe_errors.append(maybe_err)

        except IndexError as ie:
            logger.warn("index error, sentence:" + sentence + str(ie))
        except Exception as e:
            logger.warn("detect error, sentence:" + sentence + str(e))

    def _detect_by_char_ngrm(self, maybe_errors, sentence, start_idx):
        try:
            ngram_avg_scores = []
            for n in [1, 2, 3, 4]:
                scores = []
                for i in range(len(sentence) - n + 1):
                    word = sentence[i:i + n]
                    score = self.lm.score(' '.join(list(word)), bos=False, eos=False)
                    scores.append(score)
                if not scores:
                    continue
                # ????????????????????????
                for _ in range(n - 1):
                    scores.insert(0, scores[0])
                    scores.append(scores[-1])
                    # scores.append(sum(scores) / len(scores))
                avg_scores = [sum(scores[i:i + n]) / len(scores[i:i + n]) for i in range(len(sentence))]
                ngram_avg_scores.append(avg_scores)

            if ngram_avg_scores:
                # ???????????????n-gram????????????
                sent_scores = list(np.average(np.array(ngram_avg_scores), axis=0))
                # ?????????????????????
                for i in self._get_maybe_error_index(sent_scores):
                    token = sentence[i]
                    maybe_err = [token, i+start_idx, i+len(token)+start_idx, ErrorType.char]
                    if maybe_err not in maybe_errors and not self._check_in_errors(maybe_errors, maybe_err):
                        maybe_errors.append(maybe_err)

        except IndexError as ie:
            logger.warn("index error, sentence:" + sentence + str(ie))
        except Exception as e:
            logger.warn("detect error, sentence:" + sentence + str(e))

    def _detect_short(self, sentence, start_idx, is_confusion, is_token, is_wordgram, is_ngram):
        maybe_errors = []
        if not sentence.strip():
            return maybe_errors
        if is_confusion:
            self._detect_by_confusion(maybe_errors, sentence, start_idx)
        if is_token:
            self._detect_by_token(maybe_errors, sentence, start_idx)
        if is_wordgram:
            self._detect_by_word_ngrm(maybe_errors, sentence, start_idx)
        if is_ngram:
            self._detect_by_char_ngrm(maybe_errors, sentence, start_idx)
        return sorted(maybe_errors, key=lambda x: x[1], reverse=False)

    def _candidates(self, word, fregment=1):
        candidates = []
        if len(word) > 1:
            candidates += self._candidates_by_edit(word)
        candidates += self._candidates_by_pinyin(word)
        candidates += self._candidates_by_stroke(word)
        return set(candidates)

    def known(self, words):
        """The subset of `words` that appear in the dictionary of WORDS."""
        return set(w for w in words if w in self.word_dict)

    def edits1(self, word):
        """All edits that are one edit away from `word`."""
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
        replaces = [L + c + R[1:] for L, R in splits if R for c in self.char_set]
        return set(transposes + replaces)

    def _candidates_by_edit(self, word):
        return [w for w in self.known(self.edits1(word)) or [word] if lazy_pinyin(word) == lazy_pinyin(w)]

    def _candidates_by_pinyin(self, word):
        l = []
        r = list(self.pinyin2word.get(','.join(lazy_pinyin(word)), {word:''}).keys())
        for i, w in enumerate(word):
            before = word[:i]
            after = word[i+1:]
            a = list(self.same_pinyin_dict.get(w, w))
            l += [before+x+after for x in a]

        return set(l + r)

    def _candidates_by_stroke(self, word):
        l = []
        for i, w in enumerate(word):
            before = word[:i]
            after = word[i + 1:]
            a = list(self.same_stroke_dict.get(w, w))
            l += [before + x + after for x in a]

        return set(l)

    def _calibration(self, maybe_errors):
        res = []
        pre_item = None
        for cur_item, begin_idx, end_idx, err_type in maybe_errors:

            if pre_item is None:
                pre_item = [cur_item, begin_idx, end_idx, err_type]
                res.append(pre_item)
                continue
            if ErrorType.char == err_type and err_type == pre_item[3] and begin_idx == pre_item[2]:
                pre_item = [pre_item[0]+cur_item, pre_item[1], end_idx, ErrorType.word]
                res.pop()
            else:
                pre_item = [cur_item, begin_idx, end_idx, err_type]
            res.append(pre_item)
        return res

    def get_lm_correct_item(self, cur_item, candidates, before_sent, after_sent, threshold=57):
        """
        ????????????????????????????????????
        :param cur_item: ?????????
        :param candidates: ?????????
        :param before_sent: ??????????????????
        :param after_sent: ??????????????????
        :param threshold: ppl??????, ???????????????????????????ppl????????????
        :return: str, correct item, ???????????????
        """
        result = cur_item
        if cur_item not in candidates:
            candidates.append(cur_item)
        ppl_scores = {i: self.lm.perplexity(' '.join(list(before_sent + i + after_sent))) for i in candidates}
        sorted_ppl_scores = sorted(ppl_scores.items(), key=lambda d: d[1])
        # ????????????????????????????????????????????????
        top_items = []
        top_score = 0.0
        for i, v in enumerate(sorted_ppl_scores):
            v_word = v[0]
            v_score = v[1]
            if i == 0:
                top_score = v_score
                top_items.append(v_word)
            # ????????????????????????
            elif v_score < top_score + threshold:
                top_items.append(v_word)
            else:
                break
        if cur_item not in top_items:
            result = top_items[0]
        return result

    def correct(self, text, is_confusion=True, is_token=True, is_wordgram=True, is_ngram=True):
        if text is None or not text.strip():
            # logger.warn("Input text is error.")
            return text,[]

        if not self._check_state():
            # logger.warn("Corrector not init.")
            return text,[]

        text_new = ''
        details = []
        text = self._process_text(text)
        blocks = split_long_text(text, include_symbol=True)
        for blk, idx in blocks:
            maybe_errors = self._detect_short(blk, idx, is_confusion, is_token, is_wordgram, is_ngram)
            maybe_errors = self._calibration(maybe_errors)
            for cur_item, begin_idx, end_idx, err_type in maybe_errors:
                # ?????????????????????
                before_sent = blk[:(begin_idx - idx)]
                after_sent = blk[(end_idx - idx):]

                # ??????????????????????????????????????????
                if err_type == ErrorType.confusion:
                    corrected_item = self.confusion_dict[cur_item]
                else:
                    # ??????????????????????????????
                    candidates = self._candidates(cur_item)
                    if not candidates:
                        continue
                    corrected_item = self.get_lm_correct_item(cur_item, candidates, before_sent, after_sent)
                if corrected_item != cur_item:
                    blk = before_sent + corrected_item + after_sent
                    detail_word = [cur_item, corrected_item, begin_idx, end_idx]
                    details.append(detail_word)
            text_new += blk
        details = sorted(details, key=operator.itemgetter(2))
        return text_new, details