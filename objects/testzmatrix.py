#
# unit tests for the zmatrix classes
#

if __name__ == "__main__":
    # Need to add the gui directory to the python path so 
    # that all the modules can be imported
    import os,sys
    gui_path = os.path.split(os.path.dirname( os.path.realpath( __file__ ) ))[0]
    sys.path.append(gui_path)
else:
    from viewer.paths import gui_path


import zmatrix
import interfaces.filepunch
import copy
import unittest

# some simple structures / zmatrices to be used in testing
z1="""
zmatrix angstrom
     C                                                  
     h    1     1.0000                                  
     H    1     1.0900    2   109.4000                  
     H    1     1.0900    2   109.4000    3   120.0000  
     H    1     1.0900    2   109.4000    3  -120.0000  
"""

z2="""
zmatrix angstrom
     C                                                  
     h    1     CH1                                  
     H    1     1.0900    2   109.4000                  
     H    1     1.0900    2   109.4000    3   120.0000  
     H    1     1.0900    2   109.4000    3  -120.0000  
variables
CH1 1.0
"""

z3="""
zmatrix angstrom
     C                                                  
     X    1     1.0000                                  
     H    1         r3    2         v1a                  
     H    1         r4    2         v1b    3   180.0000  
     H    1         r5    2         v2a    3    90.0000  
     H    1         r6    2         v2b    3   270.0000  
variables angstrom
      v1a     50.000000  
      v2a    130.000000  
      v1b     50.000000  
      v2b    130.000000  
      r3       1.000000  
      r4       1.000000  
      r5       1.000000  
      r6       1.000000
"""

c1="""
coordinates
C 0.0 0.0 0.0
h 2.31417154151e-016 0.0 1.88972687777
H 1.94285219728 0.0 -0.684186262154
H -0.971426098735 -1.68255935859 -0.684186262154
H -0.971426098735 1.68255935859 -0.684186262154
"""

class testReadFromFile(unittest.TestCase):
    """load a zmatrix from a file artesian """

    def testLoadFromFile1(self):
        """Check simple file reader 1"""
        model=zmatrix.Zmatrix(file=gui_path+"/examples/water.zmt")
        self.assertEqual( 3, len(model.atom) )

    def testLoadFromFile2(self):
        """Check simple file reader 2"""
        model=zmatrix.Zmatrix(file=gui_path+"/examples/feco5.zmt")
        self.assertEqual( 16, len(model.atom) )


class testAutoZ(unittest.TestCase):
    """test automatic z-matrix generation"""

    def testAutoZ1(self):
        """Check autoz function"""
        r = interfaces.filepunch.PunchIO()
        model = r.GetObjects(filepath=gui_path+'/examples/caffeine.pun')[0]
        model.autoz()

        # A couple of silly tests
        self.assertEqual(model.atom[4].name,'C06')
        self.assertEqual(model.atom[4].i1.name,'C05')

class testImportCart(unittest.TestCase):
    """import function using Cartesian """

    def testA(self):
        """check import cartesians for zmatrix with no variables"""

        model = zmatrix.Zmatrix(list=c1.split('\n'))
        model2 = zmatrix.Zmatrix(list=z1.split('\n'))
        model2.import_geometry(model)

    def testB(self):
        """check import cartesians for zmatrix with a variable"""
        model = zmatrix.Zmatrix(list=c1.split('\n'))
        model2 = zmatrix.Zmatrix(list=z2.split('\n'))
        model2.import_geometry(model)


    def testImportWithDummy(self):
        """import cartesians ->  zmat with a dummy"""
        # this generates warnings and the wrong answer with the current code
        # because it has a dummy at atom 2
        model = zmatrix.Zmatrix(list=c1.split('\n'))
        model2 = zmatrix.Zmatrix(list=z3.split('\n'))
        self.assertRaises(zmatrix.ImportGeometryError,model2.import_geometry,model)
 
    def testCartesianImport(self):
        # check import function for pure cartestian system
        r = interfaces.filepunch.PunchIO()
        model = r.GetObjects(filepath=gui_path+'/examples/metallo.c')[0]
        model2 = copy.deepcopy(model)
        model.import_geometry(model2)


if __name__ == "__main__":

    # Need to add the gui directory to the python path
    #guidir = os.path.dirname( os.path.realpath( __file__ ) )
    

    if 1:
        # Run all tests in this module automatically
        unittest.main()
    else:
        # Build a test suite with required cases and run it
        myTestSuite = unittest.TestSuite()
        myTestSuite.addTest(testImportCart("testCartesianImport"))
        runner = unittest.TextTestRunner()
        runner.run(myTestSuite)
    
