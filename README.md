# SimpleChinese2

SimpleChinese2 集成了许多基本的中文NLP功能，使基于 Python 的中文文字处理和信息提取变得简单方便。

## 声明

本项目是为方便个人工作所创建的，仅有部分代码原创。包括分词、词云在内的诸多功能来自于其他项目，并非本人所写，如遇问题，请至原项目链接下提问，谢谢！

## 安装

```
pip install simplechinese==0.2.7
```

如直接从git上clone，那么需要从以下地址下载词向量文件：

```
https://drive.google.com/file/d/1ltyiTHZk8kIBYQGbZS9GoO_DwDOEWnL9/view?usp=sharing
```

并拷贝至"./simplechinese/data/"文件夹下

## 使用方法

```
import simplechinese as sc
```

### 1. 文字预处理

```
>>> import simplechinese as sc
>>> x = "测试测试，TestING    ;￥%& 01234测试测试"

>>> print(sc.only_digits(x))         # 仅保留数字
01234

>>> print(sc.only_zh(x))             # 仅保留中文
测试测试测试测试

>>> print(sc.only_en(x))             # 仅保留英文
TestING

>>> print(sc.remove_space(x))        # 去除空格
测试测试，TestING;￥%&01234测试测试

>>> print(sc.remove_digits(x))       # 去除数字
测试测试，TestING    ;￥%& 测试测试

>>> print(sc.remove_zh(x))           # 去除中文
，TestING    ;￥%& 01234

>>> print(sc.remove_en(x))           # 去除英文
测试测试，    ;￥%& 01234测试测试

>>> print(sc.remove_punctuations(x)) # 去除标点符号
测试测试TestING     01234测试测试

>>> print(sc.toLower(x))             # 修改为全小写字母
测试测试，testing    ;￥%& 01234测试测试

>>> print(sc.toUpper(x))             # 修改为全大写字母
测试测试，TESTING    ;￥%& 01234测试测试

>>> # y = fillna(df) # 将pandas.DataFrame中的N/A单元格填充为长度为0的str
```

### 2. 基础NLP信息提取功能

该部分中，分词功能使用 jieba 实现，源码请参考：https://github.com/fxsjy/jieba

同/近义词查找功能复用了 synonyms 中的词向量数据文件，源码请参考：https://github.com/chatopera/Synonyms 但有所改动，改动如下

1. 由于 pip 上传文件限制，synonyms 需要用户在完成 pip 安装后再下载词向量文件，国内下载需要设置镜像地址或使用特殊手段，有所不便。因此此处将词向量用 float16 表示，并使用 pca 降维至 64 维。总体效果差别不大，如果在意，请直接安装 synonyms 处理同/近义词查找任务。

2. 原项目通过构建 KDTree 实现快速查找，但比较相似度是使用 cosine similarity，而 KDTree (sklearn) 本身不支持通过 cosine similarity 构建。因此原项目使用欧式距离构建树，导致输出结果有部分顺序混乱。为修复该问题，本项目将词向量归一化后再构建 KDTree，改动虽小，但使得向量间的 cosine similarity 与欧式距离的顺序保持一致。具体推导可参考下文：https://stackoverflow.com/questions/34144632/using-cosine-distance-with-scikit-learn-kneighborsclassifier

3. 原项目中未设置缓存上限，本项目中仅保留最近10000次查找记录。

```
x = "今天是我参加工作的第1天，我花了23.33元买了写零食犒劳一下自己。"
print(sc.extract_nums(x))              # 提取数字信息
[1.0, 23.33]

# mode: 0: No single character words. The words may be overlapped.
#       1: Have single character words. The words may be overlapped.
#       2: No single character words. The words are not overlapped.
#       3: Have single character words. The words are not overlapped.
#       4: Only single characters.
print(sc.extract_words(x, mode=0))      # 分词
['今天', '参加', '工作', '我花', '23.33', '零食', '犒劳', '一下', '自己']

a = "做人真的好难"
b = "做人实在太难了"
print(sc.string_distance(a,b))  # 编辑距离
0.46153846153846156

x = "种族歧视"
print(sc.find_synonyms(x, n=3))  # 同/近义词
[('种族歧视', 1.0), ('种族主义', 0.84619140625), ('歧视', 0.76416015625)]
```

### 3. 繁体简体转换

该部分使用 chinese_converter 实现，源码请参考：https://github.com/zachary822/chinese-converter

```
>>> x = "乌龟测试123"
>>> print(sc.to_traditional(x))  # 转换为繁体
烏龜測試123

>>> x = "烏龜測試123"
>>> print(sc.to_simplified(x))   # 转换为简体
乌龟测试123
```

### 4. 特征提取和向量化

### 5. 词云和可视化
