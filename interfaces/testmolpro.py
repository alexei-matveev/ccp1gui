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
        calc.endjob()
        print calc.results
        self.assertEqual(len(calc.results),2,"Failed to return Structure+Vibrations")

        #if os.access('3dgridfile', os.R_OK):
        #    os.unlink('3dgridfile')
        #t=MoldenDriver(out)
        #t.ComputePlot((1,2,3))
        #check = os.access('3dgridfile', os.R_OK)
        #self.assertEqual(check,1,"No 3dgridfile generated")

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

    
