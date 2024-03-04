from functools import wraps
from inspect import getfullargspec, signature
from copy import deepcopy


def type_check(func):
    """ 严格类型检查 """
    @wraps(func)
    def wapper(*args, **kwargs):
        argspec = getfullargspec(func)
        #print(argspec)
        # print(args, kwargs)
        paramdict = deepcopy(kwargs)
        for i in range(len(args)):
            paramdict[argspec.args[i]] = args[i]
        for param, value in paramdict.items():
            if not param in argspec.annotations:
                continue
            ptype = argspec.annotations[param]
            if not isinstance(value, ptype):
                raise TypeError(f'the value of `{param}` is {value}, which is not instance of {ptype}')
        return func(*args, **kwargs) #执行函数，也要返回其值
    return wapper


# @type_check
# def _test(n: int | float, x: float = 2, z: int = 1):
#     """ Test """
#     ...


# _test(1.1, x=2.1)
# _test(1, x=2.1)