_Numeric=None
_numpy=None
try:
    import Numeric as _Numeric
except ImportError:
    try:
        import numpy as _numpy
    except ImportError:
        pass

# Test numpy
#_Numeric=None
#import numpy as _numpy

def usingNumeric():
    """Return True if we are using Numeric"""
    global _Numeric
    if _Numeric: return True
    return False

def usingNumpy():
    """Return True if we are using numpy"""
    global  _numpy
    if _numpy: return True
    return False

def isAvailable():
    """Return True or False depending on whether we have linear algebra functionality"""
    if usingNumeric or usingNumpy: return True
    return False

def array(object,**kw):
    global _Numeric, _numpy
    if _Numeric:
        return _Numeric.array(object,**kw)
    elif _numpy:
        return _numpy.array(object,**kw)
    else:
        raise AttributeError("No numeric functionality to deal with an array.")

def matrixmultiply(array1,array2,**kw):
    global _Numeric, _numpy
    if _Numeric: 
        return _Numeric.matrixmultiply(array1,array2,**kw)
    elif _numpy:
        return _numpy.dot(array1,array2,**kw)
    else:
        raise AttributeError("No numeric functionality to deal with matrixmultiply.")

def reshape(array,newshape,**kw):
    global _Numeric, _numpy
    if _Numeric:
        return _Numeric.reshape(array,newshape,**kw)
    elif _numpy:
        return _numpy.reshape(array,newshape,**kw)
    else:
        raise AttributeError("No numeric functionality to deal with reshape.")

def transpose(array,**kw):
    global _Numeric, _numpy
    if _Numeric:
        return _Numeric.transpose(array,**kw)
    elif _numpy:
        return _numpy.transpose(array,**kw)
    else:
        raise AttributeError("No numeric functionality to deal with transpose.")

def zeros(array,**kw):
    global _Numeric, _numpy
    if _Numeric:
        return _Numeric.zeros(array,**kw)
    elif _numpy:
        return _numpy.zeros(array,**kw)
    else:
        raise AttributeError("No numeric functionality to zero an array.")



if __name__=="__main__":

    import Numeric
    import numpy

    a = [
        [ -121.41295785, -3.39655004,  -1.22443129,   0.,         -35.94746644, -21.23132728 ],
        [ -3.39655004,   -96.82243358, -0.38162982,   0.,         -25.73131733, -13.03766446 ],
        [ -1.22443129,   -0.38162982,  -95.95695143,  0.,          0.,          -13.03766446 ],
        [  0.,            0.,           0.,          -95.5753216,  0.,           0.,         ],
        [ -35.94746644,  -25.73131733,  0.,           0.,         -70.19263086, -13.62411618 ],
        [ -21.23132728,  -13.03766446, -13.03766446,  0.,         -13.62411618, -63.98948192 ],
        ]

    num_a = Numeric.array(a)
    npy_a = numpy.array(a)


    num_t = Numeric.transpose(num_a)
    npy_t = numpy.transpose(npy_a)
