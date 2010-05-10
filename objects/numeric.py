try:
    import Numeric as _Numeric
except ImportError:
    _Numeric=None

def isAvailable():
    """Return True or False depending on whether we have numeric functionality"""
    if _Numeric: return True
    return False

# arctan?

def array(object,**kw):
    if _Numeric:
        return _Numeric.array(object,**kw)
    else:
        raise AttributeError("No numeric functionality to deal with an array.")

def matrixmultiply(array1,array2,**kw):
    if _Numeric:
        return _Numeric.matrixmultiply(array1,array2,**kw)
    else:
        raise AttributeError("No numeric functionality to deal with matrixmultiply.")

def reshape(array,newshape,**kw):
    if _Numeric:
        return _Numeric.reshape(array,newshape,**kw)
    else:
        raise AttributeError("No numeric functionality to deal with reshape.")

def transpose(array,**kw):
    if _Numeric:
        return _Numeric.transpose(array,**kw)
    else:
        raise AttributeError("No numeric functionality to deal with transpose.")

def zeros(array,**kw):
    if _Numeric:
        return _Numeric.zeros(array,**kw)
    else:
        raise AttributeError("No numeric functionality to deal with zeros.")

