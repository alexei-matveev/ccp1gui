#
# unit tests for the MOLPRO interface
#
import os,sys
if __name__ == "__main__":
    # Need to add the gui directory to the python path so 
    # that all the modules can be imported
    gui_path = os.path.split(os.path.dirname( os.path.realpath( __file__ ) ))[0]
    sys.path.append(gui_path)
else:
    from viewer.paths import gui_path

import unittest
import molpro
import objects.zmatrix


class MolproTestCase(unittest.TestCase):

    def testHessian(self):
        calc = molpro.MOLPROCalc()
        calc.set_parameter('ana_hessian',1)
        infile=gui_path+os.sep+'examples'+os.sep+'water.zmt'
        calc.set_input('mol_obj',objects.zmatrix.Zmatrix(file=infile))

        job = calc.makejob()
        #job.debug = 1
        ret=job.run()
        self.assertEqual(0,ret,"Error running job!")

        calc.endjob(0)
        #print calc.results
        self.assertEqual(len(calc.results),3,"Failed to return Structure+Vibrations+MoldenFile")


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(MolproTestCase)

if __name__ == "__main__":

    # Make sure we can find the exectuable
    molpro_dir='/c/ccg/share/software/molpro/molpro2006.1/bin'
    os.environ['PATH']=os.environ['PATH']+os.pathsep+molpro_dir

    if 0:
        # Run all tests in this module automatically
        unittest.main()
    else:
        # Build a test suite with required cases and run it
        myTestSuite = unittest.TestSuite()
        myTestSuite.addTest(MolproTestCase("testHessian"))
        runner = unittest.TextTestRunner()
        runner.run(myTestSuite)

    
