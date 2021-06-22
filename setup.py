import setuptools

setuptools.setup(
    name="simplechinese", # 名称
    version="0.2.7", # 版本
    author="Chen, Mingxiang", # 作者
    author_email="chenmingxiang110@gmail.com", # 邮箱
    package_data={
        '': [
            '**/*.txt',
            '**/*.pickle',
            '**/*.npy',
            'LICENSE',
        ]},
    description="This package integrates many basic Chinese NLP functions, making Python-based Chinese word processing and information extraction simple and convenient.", # 简介
    long_description="", # 详细介绍
    long_description_content_type="text/markdown", # 详细介绍的文件类型
    url="https://github.com/chenmingxiang110/SimpleChinese2", # 包的链接
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    install_requires=[
        'numpy',
        'jieba',
        'Levenshtein',
        'pandas',
        'sklearn',
        'wordcloud',
        'matplotlib',
        'chinese-converter',
    ]
)
