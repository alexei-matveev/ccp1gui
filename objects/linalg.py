try:
    import LinearAlgebra as _LinearAlgebra
except ImportError:
    _LinearAlgebra=None

def isAvailable():
    """Return True or False depending on whether we have linear algebra functionality"""
    if _LinearAlgebra: return True
    return False
    
def eigenvectors(object,**kw):
    if _LinearAlgebra:
        return _LinearAlgebra.eigenvectors(object,**kw)
    else:
        raise AttributeError("No linear algebra functionality to deal with an eigenvectors.")

def Heigenvectors(object,**kw):
    if _LinearAlgebra:
        return _LinearAlgebra.Heigenvectors(object,**kw)
    else:
        raise AttributeError("No linear algebra functionality to deal with Heigenvectors.")
