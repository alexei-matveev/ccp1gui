#
# unit tests for the zmatrix classes
#
import zmatrix
import interfaces.filepunch
import unittest
from viewer.paths import gui_path
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
        # check simple file reader
        model=zmatrix.Zmatrix(file=gui_path+"/examples/feco5.zmt")
        model.zlist()

class testAutoZ(unittest.TestCase):
    """test automatic z-matrix generation"""

    def testAutoZ1(self):
        # check autoz function
        p = interfaces.filepunch.PunchReader()
        p.scan(gui_path+'/examples/caffeine.pun')
        model = p.objects[0]
        model.list()
        print model.is_fully_connected()
        model.autoz()
        model.zlist()

class testImportCart(unittest.TestCase):
    """import function using Cartesian """

    def testA(self):
        """check import cartesians for zmatrix with no variables"""
        # import cartesians ->  zmat without variables

        model = zmatrix.Zmatrix(list=c1.split('\n'))
        model2 = zmatrix.Zmatrix(list=z1.split('\n'))
        print 'INITIAL CART MODEL'
        model.zlist()
        print 'INITIAL Z MODEL'
        model2.zlist()
        print 'IMPORT'
        model2.import_geometry(model)
        print 'AFTER IMPORT'
        model2.zlist()

    def testB(self):
        """check import cartesians for zmatrix with a variable"""
        model = zmatrix.Zmatrix(list=c1.split('\n'))
        model2 = zmatrix.Zmatrix(list=z2.split('\n'))
        print 'INITIAL CART MODEL'
        model.zlist()
        print 'INITIAL Z MODEL'
        model2.zlist()
        print 'IMPORT'
        model2.import_geometry(model)
        print 'AFTER IMPORT'
        model2.zlist()


    def testImportWithDummy(self):
        # import cartesians ->  zmat with a dummy
        # this generates warnings and the wrong answer with the current code
        # because it has a dummy at atom 2
        model = zmatrix.Zmatrix(list=c1.split('\n'))
        model2 = zmatrix.Zmatrix(list=z3.split('\n'))
        print 'INITIAL CART MODEL'
        model.zlist()
        print 'INITIAL Z MODEL'
        model2.zlist()
        print 'IMPORT'
        model2.import_geometry(model)
        print 'AFTER IMPORT'
        model2.zlist()

    def testCartesianImport(self):
        # check import function for pure cartestian system
        p = interfaces.filepunch.PunchReader()
        p.scan("../examples/metallo.c")
        model = p.objects[0]
        p.objects = []
        p.scan("../examples/metallo.c")
        model2 = p.objects[0]
        print 'BEFORE IMPORT'
        model.list()
        print 'IMPORT'
        model.import_geometry(model2)
        print 'AFTER IMPORT'
        model.list()


if __name__ == "__main__":

    if 1:
        # Run all tests in this module automatically
        unittest.main()
    else:
        # Build a test suite with required cases and run it

        #myTestSuite = unittest.TestSuite()

        #myTestSuite.addTest(testSpawn("testA"))
        #myTestSuite.addTest(testSpawnRemoteProcess("testA"))
        #myTestSuite.addTest(testSpawnRemoteProcess("testB"))
        #myTestSuite.addTest(testPipeRemoteCmd("testA"))
        #myTestSuite.addTest(testPipeRemoteCmd("testB"))

        #runner = unittest.TextTestRunner()
        #runner.run(myTestSuite)
        pass
    
