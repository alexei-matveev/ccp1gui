#!/usr/bin/python
#
#Script to run all the current CCP1GUI tests
#
import os,sys

import viewer.defaults

# Set paths to code binaries/scripts below:
#
#
# GAMESS-UK
#
#os.environ['GAMESS_EXE']='/home/jmht/Documents/GAMESS-UK.gnu/bin/gamess'
rungamess_dir='/home/jmht/Documents/GAMESS-UK.gnu/rungamess'
os.environ['PATH']=os.environ['PATH']+os.pathsep+rungamess_dir
#
# ChemShell
#
chemsh_script_dir='/c/ccg/share/software/ChemShell/ChemShell-3.4.dev/scripts'
viewer.defaults.defaults.set_value('chemsh_script_dir', chemsh_script_dir)


#
import unittest
#
# The testsuite to hold the series of tests that we will run
#
testsuite = unittest.TestSuite()

#
# We have just one Tk root instance to run all the tests
# It's somewhat of a dirty hack, but we poke the tkroot instance into 
# the module namespace of the various modules that run graphical tests

#
import Tkinter
tkroot=Tkinter.Tk()
#tkroot.withdraw()


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
#import interfaces.cubereader
#testsuite.addTests(interfaces.cubereader.testMe())
import interfaces.am1calc
testsuite.addTests(interfaces.am1calc.testMe())

# interfaces with graphical tests
import interfaces.testgamessuk
interfaces.testgamessuk.tkroot=tkroot
testsuite.addTests(interfaces.testgamessuk.testMe())

#import interfaces.dalton
#interfaces.dalton.tkroot=tkroot
#testsuite.addTests(interfaces.dalton.testMe())

import interfaces.mndo
interfaces.mndo.tkroot=tkroot
testsuite.addTests(interfaces.mndo.testMe())

# Below still to do:
#interfaces/testmolpro.py
#interfaces/testmolden.py
#interfaces/testchemshell.py


###############################################################
#
# Finally test the gui itself
#
###############################################################

import viewer.testVisualisers
viewer.testVisualisers.tkroot=tkroot
testsuite.addTests(viewer.testVisualisers.testMe())

###############################################################
#
# Now run 'em all
#
###############################################################

unittest.TextTestRunner(verbosity=2).run(testsuite)
