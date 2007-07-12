#
# unit tests for the ChemShell interface
#
import unittest
import os
from interfaces.chemshell import *
from viewer.paths import gui_path

exdir=gui_path+os.sep+'examples'+os.sep

class ChemShellTestCase(unittest.TestCase):
    """ Batch tests of the ChemShell interface """

    def testMolproOptim(self):
        calc = ChemShellCalc()
        f = exdir + os.sep + 'water.zmt'
        m = Zmatrix(file=f)
        calc.set_input('mol_obj',m)
        #for t in  m.bonds_and_angles():
        #    print t
        calc.set_parameter('task','optimise')
        calc.set_parameter('qmcode','molpro')
        calc.set_qm_code('gamess')
        calc.create_qm_calc()
        calc.qmcalc.set_parameter('default_basis','sto3g')
        job = calc.makejob()
        job.run()
        job.tidy(0)
        dist=m.get_distance(m.atom[0],m.atom[1])
        ref=0.9892
        self.assertEqual(abs(dist-ref)<0.0001,1,"Molpro opt Failed to give O-H dist: "+str(dist))


    def testGAMESSUKOptim(self):
        calc = ChemShellCalc()
        f = exdir + os.sep + 'water.zmt'
        m = Zmatrix(file=f)
        calc.set_input('mol_obj',m)
        #for t in  m.bonds_and_angles():
        #    print t
        calc.set_parameter('task','optimise')
        calc.set_qm_code('gamess')
        calc.create_qm_calc()
        calc.qmcalc.set_parameter('default_basis','sto3g')
        job = calc.makejob()
        job.run()
        job.tidy(0)
        dist=m.get_distance(m.atom[0],m.atom[1])
        ref=0.9892
        self.assertEqual(abs(dist-ref)<0.0001,1,"Molpro opt Failed to give O-H dist: "+str(dist))

    def XtestGAMESS(self):
        if os.access('3dgridfile', os.R_OK):
            os.unlink('3dgridfile')
        t=MoldenDriver(out)
        t.ComputePlot((1,2,3),mo=5)
        check = os.access('3dgridfile', os.R_OK)
        self.assertEqual(check,1,"No 3dgridfile generated")

def suite():
    return unittest.TestLoader().loadTestsFromTestCase(MoldenTestCase)

if __name__ == "__main__":

    from viewer.rc_vars import rc_vars
    rc_vars['chemsh_script_dir']='/c/qcg/psh/ChemShell-3.2/chemsh/scripts'

    if 0:
        # Run all tests in this module automatically
        unittest.main()
    else:
        # Build a test suite with required cases and run it
        myTestSuite = unittest.TestSuite()
        myTestSuite.addTest(ChemShellTestCase("testGAMESSUKOptim"))
        myTestSuite.addTest(ChemShellTestCase("testMolproOptim"))
        runner = unittest.TextTestRunner()
        runner.run(myTestSuite)
        pass
