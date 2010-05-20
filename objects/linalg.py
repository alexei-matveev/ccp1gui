"""
Modules to support linear algebra operations within the CCP1GUI.
This module just provides wrappers for either the LinearAlgebra module
(from Numeric) or the numpy.linalg module.
Currently if both NUmeric and numpy are installed, we go with Numeric, as this
is what is supported by Scientific Python, which we use for the CalculationMonitor
widget.
However, as both Numeric and Scientific are deprecated, we should aim to make numpy and scipy
the defaults.
"""

import os,sys
if __name__ == "__main__":
    # Need to add the gui directory to the python path so 
    # that all the modules can be imported
    gui_path = os.path.split(os.path.dirname( os.path.realpath( __file__ ) ))[0]
    sys.path.append(gui_path)

import unittest
import objects.numeric

#
# Import the modules - we import both if both are present for the unittesting stuff
#
_LinearAlgebra=None
_numpy_linalg=None
try:
    import LinearAlgebra as _LinearAlgebra
except ImportError:
    try:
        import numpy.linalg as _numpy_linalg
    except ImportError:
        pass

# Test numpy    
#_LinearAlgebra=None    
#import numpy.linalg as _numpy_linalg


def usingNumeric():
    """Return True if we are using Numeric"""
    global _LinearAlgebra
    if _LinearAlgebra: return True
    return False

def usingNumpy():
    """Return True if we are using numpy"""
    global  _numpy_linalg
    if _numpy_linalg: return True
    return False

def isAvailable():
    """Return True or False depending on whether we have linear algebra functionality"""
    if usingNumeric or usingNumpy: return True
    return False

    
def eig(object,**kw):
    """We try to adhere to the numpy way of doing things, so we need to do a transpose on the results
    that we get back from Numeric"""
    global _LinearAlgebra, _numpy_linalg
    if _LinearAlgebra:
        eigval,eigvec =  _LinearAlgebra.eigenvectors(object,**kw)
        eigvec = objects.numeric.transpose(eigvec)
        return eigval,eigvec
    elif _numpy_linalg:
        return _numpy_linalg.eig(object,**kw)
    else:
        raise AttributeError("No linear algebra functionality to deal with an eigenvectors.")

def eigh(object,**kw):
    """We try to adhere to the numpy way of doing things, so we need to do a transpose on the results
    that we get back from Numeric"""
    global _LinearAlgebra, _numpy_linalg
    if _LinearAlgebra:
        eigval,eigvec =  _LinearAlgebra.Heigenvectors(object,**kw)
        eigvec = objects.numeric.transpose(eigvec)
        return eigval,eigvec
    elif _numpy_linalg:
        return _numpy_linalg.eigh(object,**kw)
    else:
        raise AttributeError("No linear algebra functionality to deal with Heigenvectors.")


##########################################
#
# Unittesting stuff
# 
##########################################

class LinalgTestCases(unittest.TestCase):
    """Test cases to check that both our Numeric and numpy wrappers give the same result
    These will only work if both Numeric and numpy are installed"""

    try:
        import Numeric, numpy
    except ImportError:
        Numeric=None
        numpy=None

    # Symmetric matrix for testing
    symmat = [
        [ -121.41295785, -3.39655004,  -1.22443129,   0.,         -35.94746644, -21.23132728 ],
        [ -3.39655004,   -96.82243358, -0.38162982,   0.,         -25.73131733, -13.03766446 ],
        [ -1.22443129,   -0.38162982,  -95.95695143,  0.,          0.,          -13.03766446 ],
        [  0.,            0.,           0.,          -95.5753216,  0.,           0.,         ],
        [ -35.94746644,  -25.73131733,  0.,           0.,         -70.19263086, -13.62411618 ],
        [ -21.23132728,  -13.03766446, -13.03766446,  0.,         -13.62411618, -63.98948192 ],
        ]


    if Numeric:
        numeric_symmat = Numeric.array(symmat)
        numpy_symmat = numpy.array(symmat)


    def testEigh(self):
        """Test the eigenvalues and eigenvectors of a symmetric matrix"""

        global _LinearAlgebra, _numpy_linalg

        # Default is to run with LinearAlgebra
        numeric_vals,numeric_vecs = eigh(self.numeric_symmat)
        
        # Set to none to use numpy wrapper
        tmp=_LinearAlgebra
        _LinearAlgebra=None

        numpy_vals,numpy_vecs = eigh(self.numpy_symmat)

        # Convert eigenvalues and eigenvectors to python arrays so we can compare
        numeric_vals = numeric_vals.tolist()
        numpy_vals = numpy_vals.tolist()

        numeric_vecs = numeric_vecs.tolist()
        numpy_vecs = numpy_vecs.tolist()

        self.assertEqual(numpy_vals,numeric_vals)
        self.assertEqual(numpy_vecs,numeric_vecs)

        # Restore module to namespace so other tests will use it
        _LinearAlgebra=tmp


    def testEig(self):
        """Test the eigenvalues and eigenvectors of a symmetric matrix"""

        global _LinearAlgebra, _numpy_linalg

        # Default is to run with LinearAlgebra
        numeric_vals,numeric_vecs = eig(self.numeric_symmat)
        
        # Set to none to use numpy wrapper
        # Set to none to use numpy wrapper
        tmp=_LinearAlgebra
        _LinearAlgebra=None

        numpy_vals,numpy_vecs = eig(self.numpy_symmat)

        # Convert eigenvalues and eigenvectors to python arrays so we can compare
        numeric_vals = numeric_vals.tolist()
        numpy_vals = numpy_vals.tolist()

        numeric_vecs = numeric_vecs.tolist()
        numpy_vecs = numpy_vecs.tolist()

        self.assertEqual(numpy_vals,numeric_vals)
        self.assertEqual(numpy_vecs,numeric_vecs)

        # Restore module to namespace so other tests will use it
        _LinearAlgebra=tmp
        

if __name__ == "__main__":

    # Need to import here as it wouldn't have been pulled in if both present
    import numpy.linalg as _numpy_linalg
    unittest.main()
