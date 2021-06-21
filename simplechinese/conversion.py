import chinese_converter

def to_simplified(s):
    res = list(chinese_converter.to_simplified(s))
    for i in range(len(s)):
        if s[i]=='泡' and res[i]!='泡':
            res[i]='泡'
    res = "".join(res)
    return res

def to_traditional(s):
    res = list(chinese_converter.to_traditional(s))
    res = "".join(res)
    return res
