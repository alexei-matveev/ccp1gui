#
# unit tests for the MOLPRO interface
#
import unittest
import os
from molpro import *

from viewer.paths import gui_path

class MolproTestCase(unittest.TestCase):

    def testHessian(self):
        calc = MOLPROCalc()
        calc.set_parameter('ana_hessian',1)
        out=gui_path+os.sep+'examples'+os.sep+'water.zmt'
        calc.set_input('mol_obj',Zmatrix(file='../examples/water.zmt'))
        job = calc.makejob()
        #job.debug = 1
        job.run()
        calc.endjob(0)
        print calc.results
        self.assertEqual(len(calc.results),3,"Failed to return Structure+Vibrations+MoldenFile")


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(MolproTestCase)

if __name__ == "__main__":

    if 0:
        # Run all tests in this module automatically
        unittest.main()
    else:
        # Build a test suite with required cases and run it
        myTestSuite = unittest.TestSuite()
        myTestSuite.addTest(MolproTestCase("testHessian"))
        runner = unittest.TextTestRunner()
        runner.run(myTestSuite)

    
