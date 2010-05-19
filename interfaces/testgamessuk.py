#
# unit tests for the GAMESS-UK interface
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
import time
import gamessuk
import objects.zmatrix
import jobmanager

exdir=gui_path+os.sep+'examples'+os.sep

class GAMESSUKCalcTests(unittest.TestCase):

    def SetUp(self):
        """Need to wait as otherwise the tests run so quickly gamess-uk can't delete
        the files between runs and we hit all sorts of errors"""
        time.sleep(2)

    def testOptx(self):
        """Cartesian geometry optimisation"""
        calc = gamessuk.GAMESSUKCalc()
        #out=gui_path+os.sep+'examples'+os.sep+'water.zmt'
        m = objects.zmatrix.Zmatrix(file=gui_path+os.sep+'examples'+os.sep+'water.zmt')
        calc.set_input('mol_obj',m)
        calc.set_parameter('task','optimise')
        calc.set_parameter('default_basis','sto3g')
        job = calc.makejob()
        #job.debug = 1
        job.run()
        ret=job.run()
        self.assertEqual(0,ret,"Error running GAMESS-UK job:\n%s" % job.msg )

        # tidy loads the reults
        job.tidy(0)
        self.assertEqual(len(calc.results),4,"Failed to return Structure+2*List+File")
        

class GAMESSUKCalcEdTests(unittest.TestCase):
    
    """We just check we can fire up the calculation editor and run a calculation.
       We don't check for results, just that there are no exceptions raised"""

    def SetUp(self):
        """Need to wait as otherwise the tests run so quickly gamess-uk can't delete
        the files between runs and we hit all sorts of errors"""
        time.sleep(2)

    def testOptx(self):
        """Cartesian geometry optimisation run with editor"""

        # tkroot either created in this module if we run standalone, or passed in by the
        # testall script if run as part of all the tests
        global tkroot

        calc = gamessuk.GAMESSUKCalc()
        m = objects.zmatrix.Zmatrix(file=gui_path+os.sep+'examples'+os.sep+'water.zmt')
        calc.set_input('mol_obj',m)
        calc.set_parameter('task',gamessuk.MENU_OPT)
        calc.set_parameter('default_basis','sto3g')
        #job = calc.makejob()
        #job.debug = 1

        jm = jobmanager.JobManager()
        je = jobmanager.jobeditor.JobEditor(tkroot,jm)
        vt = gamessuk.GAMESSUKCalcEd(tkroot,calc,None,job_editor=je)
        vt.Run()


def testMe():
    """Return a unittest test suite with all the testcases that should be run by the main 
    gui testing framework."""

    suite = unittest.TestLoader().loadTestsFromTestCase(GAMESSUKCalcTests)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(GAMESSUKCalcEdTests))
    return suite

if __name__ == "__main__":

    # Make sure we can find the exectuable
    os.environ['GAMESS_EXE']='/c/ccg/share/software/gamess-uk/GAMESS-UK_dev_pgf/bin/gamess'

    import Tkinter
    tkroot = Tkinter.Tk()
    tkroot.withdraw()

    if 1:
        # Run all tests in this module automatically
        unittest.main()
    else:
        # Build a test suite with required cases and run it
        myTestSuite = unittest.TestSuite()
        #myTestSuite.addTest(GAMESSUKCalcTests("testOptx"))
        myTestSuite.addTest(GAMESSUKCalcEdTests("testOptx"))
        runner = unittest.TextTestRunner()
        runner.run(myTestSuite)

    
