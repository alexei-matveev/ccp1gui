#!/usr/bin/python
#
#Script to run all the current CCP1GUI tests
#

import unittest

#
# The testsuite to hold the series of tests that we will run
#
testsuite = unittest.TestSuite()

###########################################################################
#
# Go through the various directories and add the test jobs from the files
#
##########################################################################

#
# objects
#
import objects.zmatrix
testsuite.addTests(objects.zmatrix.testMe())

#
# jobmanager
#
import jobmanager.job
testsuite.addTests(jobmanager.job.testMe())
import jobmanager.ccp1gui_subprocess
testsuite.addTests(jobmanager.ccp1gui_subprocess.testMe())

#
# interfaces
#
import interfaces.fileio
testsuite.addTests(interfaces.fileio.testMe())
import interfaces.smeagolio
testsuite.addTests(interfaces.smeagolio.testMe())
import interfaces.gamessukio
testsuite.addTests(interfaces.gamessukio.testMe())
import interfaces.charmm
testsuite.addTests(interfaces.charmm.testMe())
import interfaces.filepunch
testsuite.addTests(interfaces.filepunch.testMe())
import interfaces.cubereader
testsuite.addTests(interfaces.cubereader.testMe())
import interfaces.testgamessuk
testsuite.addTests(interfaces.testgamessuk.testMe())
import interfaces.am1calc
testsuite.addTests(interfaces.am1calc.testMe())

# Below still to do:
#interfaces/testmolpro.py:import unittest
#interfaces/testmolden.py:import unittest
#interfaces/testchemshell.py:import unittest


###############################################################
#
# Finally test the gui itself
#
###############################################################

# Just have one root instance to run all the tests
import Tkinter
tkroot=Tkinter.Tk()
tkroot.withdraw()
import viewer.testVisualisers
# Horrible, dirty hack - pass the tkroot instance to the testVisualisers module
viewer.testVisualisers.tkroot=tkroot
testsuite.addTests(viewer.testVisualisers.testMe())

###############################################################
#
# Now run 'em all
#
###############################################################

unittest.TextTestRunner(verbosity=2).run(testsuite)
