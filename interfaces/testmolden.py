#
# unit tests for the MOLDEN interface
#
import unittest
import os
from molden import *

from viewer.paths import gui_path
out=gui_path+os.sep+'examples'+os.sep+'methanol_sample.out'

class MoldenTestCase(unittest.TestCase):
    """ using a sample output try and get a 3d density """

    def testDensity(self):
        if os.access('3dgridfile', os.R_OK):
            os.unlink('3dgridfile')
        t=MoldenDriver(out)
        t.ComputePlot((1,2,3))
        check = os.access('3dgridfile', os.R_OK)
        self.assertEqual(check,1,"No 3dgridfile generated")

    def testOrbital(self):
        if os.access('3dgridfile', os.R_OK):
            os.unlink('3dgridfile')
        t=MoldenDriver(out)
        t.ComputePlot((1,2,3),mo=5)
        check = os.access('3dgridfile', os.R_OK)
        self.assertEqual(check,1,"No 3dgridfile generated")


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(MoldenTestCase)


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
    
