#
# unit tests for the ChemShell interface
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
import shutil
import interfaces.chemshell
import objects.zmatrix
import jobmanager

exdir=gui_path+os.sep+'examples'+os.sep

class ChemShellCalcTestCase(unittest.TestCase):
    """ Batch tests of the ChemShell interface """

    def testMolproOptim(self):
        calc = interfaces.chemshell.ChemShellCalc()        
        #calc.debug=1
        f = exdir + os.sep + 'water.zmt'
        m = objects.zmatrix.Zmatrix(file=f)
        calc.set_input('mol_obj',m)
        #for t in  m.bonds_and_angles():
        #    print t
        calc.set_parameter('task','optimise')
        calc.set_qm_code('molpro')
        calc.create_qm_calc()
        calc.qmcalc.set_parameter('default_basis','sto3g')
        job = calc.makejob()
        ret = job.run()
        
        # Check the job ran
        self.assertEqual(ret,0,"Failed to run job!")

        job.tidy(0)

        # Check the results
        dist=m.get_distance(m.atom[0],m.atom[1])
        ref=0.9892
        self.assertEqual(abs(dist-ref)<0.0001,1,"Molpro opt Failed to give O-H dist: "+str(dist))


    def testGAMESSUKOptim(self):
        calc = interfaces.chemshell.ChemShellCalc()
        #calc.debug=1
        f = exdir + os.sep + 'water.zmt'
        m = objects.zmatrix.Zmatrix(file=f)
        calc.set_input('mol_obj',m)
        #for t in  m.bonds_and_angles():
        #    print t
        calc.set_parameter('task','optimise')
        calc.set_qm_code('gamess')
        calc.create_qm_calc()
        calc.qmcalc.set_parameter('default_basis','sto3g')
        job = calc.makejob()
        ret=job.run()

        # Check we ran o.k. first
        self.assertEqual(ret,0,"Failed to run job!")
        job.tidy(0)

        # Check the results
        dist=m.get_distance(m.atom[0],m.atom[1])
        ref=0.9892
        self.assertEqual(abs(dist-ref)<0.0001,1,"GAMESS-UK opt Failed to give O-H dist: "+str(dist))

    def XtestGAMESS(self):
        if os.access('3dgridfile', os.R_OK):
            os.unlink('3dgridfile')
        t=MoldenDriver(out)
        t.ComputePlot((1,2,3),mo=5)
        check = os.access('3dgridfile', os.R_OK)
        self.assertEqual(check,1,"No 3dgridfile generated")


class ChemShellCalcEdTestCases(unittest.TestCase):
    
    """We just check we can fire up the calculation editor and run a calculation.
       We don't check for results, just that there are no exceptions raised"""

    def testGAMESSUKOptim(self):
        """GAMESSUK Optimisation"""

        # tkroot either created in this module if we run standalone, or passed in by the
        # testall script if run as part of all the tests
        global tkroot


        calc = interfaces.chemshell.ChemShellCalc()        
        f = exdir + os.sep + 'water.zmt'
        m = objects.zmatrix.Zmatrix(file=f)
        calc.set_input('mol_obj',m)
        #for t in  m.bonds_and_angles():
        #    print t
        calc.set_parameter('task','optimise')
        calc.set_qm_code('gamess')
        calc.create_qm_calc()
        calc.qmcalc.set_parameter('default_basis','sto3g')

        jm = jobmanager.JobManager()
        je = jobmanager.jobeditor.JobEditor(tkroot,jm)
        vt = interfaces.chemshell.ChemShellCalcEd(tkroot,calc,None,job_editor=je)
        vt.Run()


class ChemShellModeVis(unittest.TestCase):
    """ Batch tests of the ChemShell Mode visualiser (reader part  not the actual visualistion)"""

    cdir=exdir+os.sep+'chemsh_mode_visualisation'

    def testZOpt(self):

        shutil.copyfile(self.cdir+os.sep+'zopt.z_vis.keep',self.cdir+os.sep+'zopt.z_vis')
        shutil.copyfile(self.cdir+os.sep+'zopt.hessian',self.cdir+os.sep+'newopt.h_vis')

        vfs=interfaces.chemshell.chemshell_z_modes(directory=self.cdir)[0]

        self.assertAlmostEqual(1.069801728,vfs.vibs[2].freq)
        
        os.remove(self.cdir+os.sep+'zopt.z_vis')
        os.remove(self.cdir+os.sep+'newopt.h_vis')
        
    def testCOpt(self):

        shutil.copyfile(self.cdir+os.sep+'copt.c_vis.keep',self.cdir+os.sep+'copt.c_vis')
        shutil.copyfile(self.cdir+os.sep+'copt.hessian',self.cdir+os.sep+'newopt.h_vis')

        vfs=interfaces.chemshell.chemshell_c_modes(directory=self.cdir)[0]

        self.assertAlmostEqual(-0.0008933,vfs.vibs[2].freq)
        
        os.remove(self.cdir+os.sep+'copt.c_vis')
        os.remove(self.cdir+os.sep+'newopt.h_vis')


def testMe():
        suite = unittest.TestSuite()
        suite.addTest(ChemShellTestCase("testGAMESSUKOptim"))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(ChemShellModeVis))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(ChemShellCalcEdTestCases))
        return suite

if __name__ == "__main__":

    #
    # Set the paths to scripts/executables here:
    #
    chemsh_script_dir='/c/ccg/share/software/ChemShell/ChemShell-3.4.dev/scripts'
    rungamess_dir='/c/ccg/share/software/gamess-uk/GAMESS-UK_dev/rungamess'

    #
    # Set up to run
    #
    import viewer.defaults
    viewer.defaults.defaults.set_value('chemsh_script_dir', chemsh_script_dir)
    os.environ['PATH']=os.environ['PATH']+os.pathsep+rungamess_dir

    import Tkinter
    tkroot=Tkinter.Tk()
    tkroot.withdraw()

    if 0:
        # Run all tests in this module automatically
        unittest.main()
    else:
        # Build a test suite with required cases and run it
        myTestSuite = unittest.TestSuite()
        myTestSuite.addTest(ChemShellCalcTestCase("testGAMESSUKOptim"))
        #myTestSuite.addTest(ChemShellCalcTestCase("testMolproOptim"))
        myTestSuite.addTests(unittest.TestLoader().loadTestsFromTestCase(ChemShellModeVis))
        myTestSuite.addTests(unittest.TestLoader().loadTestsFromTestCase(ChemShellCalcEdTestCases))
        runner = unittest.TextTestRunner()
        runner.run(myTestSuite)
