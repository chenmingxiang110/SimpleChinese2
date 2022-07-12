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

def num2chinese(x):
    num=['零','一','二','三','四','五','六','七','八','九']
    k=['零','十','百','千','万','十','百']

    def turn(x,y):
        if y>= 1:
            a=x//pow(10,y)
            b=x%pow(10,y)
            c=num[a]+k[y]
            if y>4 and b<pow(10,4):
                c+=k[4]
            if (len(str(x))-len(str(b))) >= 2 and b != 0:
                c+=k[0]
        else:
            a=x
            b=0
            c=num[a]
        return (c,b,)

    c=turn(x,(len(str(x))-1))
    a,b=c[0], c[1]
    while b != 0:
        a+=turn(b,(len(str(b))-1))[0]
        b=turn(b,(len(str(b))-1))[1]
    return a
