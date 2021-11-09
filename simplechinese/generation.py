import os
import sys
import pickle
import numpy as np

class Generator:

    def __init__(self, folder):
        with open(os.path.join(folder, 'chinese_names.pickle'), 'rb') as handle:
            self.males_zh, self.females_zh, self.surnames_zh = pickle.load(handle)
        with open(os.path.join(folder, 'english_names_mini.pickle'), 'rb') as handle:
            self.males_en, self.females_en, self.surnames_en = pickle.load(handle)
        self.surnames_zh = [(k,self.surnames_zh[k]) for k in self.surnames_zh.keys()]
        self.surnames_zh_weights = [x[1] for x in self.surnames_zh]
        self.surnames_zh_weights = np.array(self.surnames_zh_weights) / np.sum(self.surnames_zh_weights)
        self.surnames_zh = [x[0] for x in self.surnames_zh]
        self.surnames_en_weights = np.ones(len(self.surnames_en))
        self.surnames_en_weights[:8000] = 2
        self.surnames_en_weights[:4000] = 4
        self.surnames_en_weights[:2000] = 8
        self.surnames_en_weights[:1000] = 16
        self.surnames_en_weights = np.array(self.surnames_en_weights) / np.sum(self.surnames_en_weights)

    def generate(self, language=None, sex=None):
        if language is None:
            language = np.random.choice(["en", "zh"])
        if language is None:
            sex = np.random.choice(["male", "female"])

        if language=="zh":
            if sex=="male":
                given_name = np.random.choice(self.males_zh)
            else:
                given_name = np.random.choice(self.females_zh)
        else:
            if sex=="male":
                given_name = np.random.choice(self.males_en)
            else:
                given_name = np.random.choice(self.females_en)

        if language=="zh":
            i = np.random.choice(len(self.surnames_zh_weights), 1, p=self.surnames_zh_weights)[0]
            surname = self.surnames_zh[i]
            return surname+given_name
        else:
            i = np.random.choice(len(self.surnames_en_weights), 1, p=self.surnames_en_weights)[0]
            surname = self.surnames_en[i]
            return given_name+" "+surname

curdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curdir)
generator = Generator(os.path.join(curdir, 'data'))

def generate_name(language=None, sex=None):
    return generator.generate(language=language, sex=sex)
