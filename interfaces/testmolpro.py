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
import Tkinter
import jobmanager

class MolproCalcTestCases(unittest.TestCase):

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

class MolproCalcEdTestCases(unittest.TestCase):

    """We just check we can fire up the calculation editor and run a calculation.
       We don't check for results, just that there are no exceptions raised"""    

    def testScf(self):
        root = Tkinter.Tk()
        calc = molpro.MOLPROCalc()
        infile=gui_path+os.sep+'examples'+os.sep+'water.zmt'
        calc.set_input('mol_obj',objects.zmatrix.Zmatrix(file=infile))
        jm = jobmanager.JobManager()
        je = jobmanager.jobeditor.JobEditor(root,jm)
        vt = molpro.MOLPROCalcEd(root,calc,None,job_editor=je)
        # invoke via calculation editor
        vt.Run()
        #root.mainloop()


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(MolproTestCase)

if __name__ == "__main__":

    # Make sure we can find the exectuable
    molpro_dir='/c/ccg/share/software/molpro/molpro2008.2/bin'
    os.environ['PATH']=os.environ['PATH']+os.pathsep+molpro_dir

    if 1:
        # Run all tests in this module automatically
        unittest.main()
    else:
        # Build a test suite with required cases and run it
        myTestSuite = unittest.TestSuite()
        #myTestSuite.addTest(MolproCalcTestCases("testHessian"))
        myTestSuite.addTest(MolproCalcEdTestCases("testScf"))
        runner = unittest.TextTestRunner()
        runner.run(myTestSuite)

    
