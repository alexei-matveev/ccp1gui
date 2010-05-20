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
rungamess_dir='/c/ccg/share/software/gamess-uk/GAMESS-UK_dev_pgf/rungamess'
os.environ['PATH']=os.environ['PATH']+os.pathsep+rungamess_dir
#
# ChemShell
#
chemsh_script_dir='/c/ccg/share/software/ChemShell/ChemShell-3.4.dev/scripts'
viewer.defaults.defaults.set_value('chemsh_script_dir', chemsh_script_dir)

#
# Dalton
#
dalton_dir='/c/ccg/share/software/dalton/dalton-2.0_intel/bin/'
os.environ['PATH']+=os.pathsep+dalton_dir

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
import objects.am1
testsuite.addTests(objects.am1.testMe())

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
import interfaces.am1calc
testsuite.addTests(interfaces.am1calc.testMe())

import interfaces.charmm
testsuite.addTests(interfaces.charmm.testMe())

import interfaces.chemshell
testsuite.addTests(interfaces.chemshell.testMe())

#import interfaces.cubereader
#testsuite.addTests(interfaces.cubereader.testMe())

import interfaces.dalton
testsuite.addTests(interfaces.dalton.testMe())

import interfaces.fileio
testsuite.addTests(interfaces.fileio.testMe())

import interfaces.filepunch
testsuite.addTests(interfaces.filepunch.testMe())

import interfaces.gamessukio
testsuite.addTests(interfaces.gamessukio.testMe())

import interfaces.mndo
# Poke root Tk instance into mndo module
interfaces.mndo.tkroot=tkroot
testsuite.addTests(interfaces.mndo.testMe())

import interfaces.smeagolio
testsuite.addTests(interfaces.smeagolio.testMe())

import interfaces.testgamessuk
testsuite.addTests(interfaces.testgamessuk.testMe())

# Below still to do:
#interfaces/testmolpro.py
#interfaces/testmolden.py


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
