#
# unit tests for the MOLDEN interface
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
import molden


out=gui_path+os.sep+'examples'+os.sep+'methanol_sample.out'

class MoldenTestCase(unittest.TestCase):
    """ using a sample output try and get a 3d density """

    def testDensity(self):
        if os.access('3dgridfile', os.R_OK):
            os.unlink('3dgridfile')
        t=molden.MoldenDriver(out)
        t.ComputePlot((1,2,3))
        check = os.access('3dgridfile', os.R_OK)
        self.assertEqual(check,1,"No 3dgridfile generated")

    def testOrbital(self):
        if os.access('3dgridfile', os.R_OK):
            os.unlink('3dgridfile')
        t=molden.MoldenDriver(out)
        t.ComputePlot((1,2,3),mo=5)
        check = os.access('3dgridfile', os.R_OK)
        self.assertEqual(check,1,"No 3dgridfile generated")

def suite():
    return unittest.TestLoader().loadTestsFromTestCase(MoldenTestCase)

if __name__ == "__main__":

    # Run all the tests
    unittest.main()    
