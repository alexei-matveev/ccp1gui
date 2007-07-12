#
# unit tests for the GAMESS-UK interface
#
import unittest
import os
from gamessuk import *
from viewer.paths import gui_path

exdir=gui_path+os.sep+'examples'+os.sep

class GAMESSUKTestCase(unittest.TestCase):

    def testOptx(self):
        """Cartesian heometry optimisation"""
        calc = GAMESSUKCalc()
        out=gui_path+os.sep+'examples'+os.sep+'water.zmt'
        m = Zmatrix(file='../examples/water.zmt')
        calc.set_input('mol_obj',m)
        calc.set_parameter('task','optimise')

        #
        # hard work setting the basis set
        #
#         calc.basis_manager.set_molecule(m)
#         calc.basis_manager.assign_default_basis('sto3g')
#         calc.basis_manager.apply_default_assignment()
#         print calc.basis_manager.basis_summary_by_atom()
## we need to generate the output from the manager and store it
## this would be done by the ReadWidgets 
#         bas = calc.basis_manager.output()
#         calc.set_parameter('basis',bas)
        calc.set_parameter('default_basis','sto3g')

        job = calc.makejob()
        #job.debug = 1
        job.run()
        job.tidy(0)
        print calc.results
        self.assertEqual(len(calc.results),4,"Failed to return Structure+2*List+File")

def suite():
    return unittest.TestLoader().loadTestsFromTestCase(GANESSUKTestCase)

if __name__ == "__main__":

    if 0:
        # Run all tests in this module automatically
        unittest.main()
    else:
        # Build a test suite with required cases and run it
        myTestSuite = unittest.TestSuite()
        myTestSuite.addTest(GAMESSUKTestCase("testOptx"))
        runner = unittest.TextTestRunner()
        runner.run(myTestSuite)

    
