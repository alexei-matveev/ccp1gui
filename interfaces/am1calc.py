#
#    This file is part of the CCP1 Graphical User Interface (ccp1gui)
# 
#   (C) 2002-2005 CCLRC Daresbury Laboratory
# 
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
# 
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
# 
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
"""Implements the interface to the AM1 code from Linkoping
"""
import os,sys
if __name__ == "__main__":
    # Need to add the gui directory to the python path so 
    # that all the modules can be imported
    gui_path = os.path.split(os.path.dirname( os.path.realpath( __file__ ) ))[0]
    sys.path.append(gui_path)
else:
    from viewer.paths import gui_path

import unittest

import viewer.help
import jobmanager.job
from objects import zmatrix
from qm import QMCalc,QMCalcEd
from objects import am1

# If this fails, then we don't have Scientific Python installed
# and can't use the calculation monitor
try:
    from interfaces.calcmon import CalculationMonitor
except ImportError:
    CalculationMonitor=None

#import Tkinter
#import Pmw
#import tkFileDialog

MENU_OPT   = "Geometry Optimisation"

class AM1Calc(QMCalc):
    """Calculation object for the AM1 calculation
    """
    def __init__(self, **kw):

        #print QMCalc
        #print AM1Calc

        QMCalc.__init__(self,**kw)

        self.debug = 0
        self.generator = None
        self.optstep = 0 # to count optimisation steps

        self.molecules = []
        self.AM1Energies = []
        self.KillFlag = None
        self.AM1Mol = None

        
    def set_defaults( self ):
        """ Set up the default values for the calculation """
        #print 'set def'

        # these to reset for new opt
        self.molecules = []
        self.AM1Energies = []
        self.AM1Mol = None
        self.KillFlag = None

        self.set_program('AM1')
        self.set_title('x')
        self.set_parameter('task',MENU_OPT)
        self.set_parameter('max_iter', 100)
        self.set_parameter('energy_threshold', 1e-6)
        self.set_parameter('gradient_threshold', 1e-3)
        self.set_parameter('opt_method','Conjugate-gradient')
        self.set_name('am1 cleanup')
        
    def check_avail_parameters(self):
        """Check if we have parameters for all the atoms."""

        failed = []
        mol = self.get_input('mol_obj')
        for atom in mol.atom:
            if not atom.symbol in am1.AM1atoms:
                print "symbol %s not in list" % atom.symbol
                failed.append(atom.symbol)
                
        if len(failed) >= 1:
            return failed
        else:
            return None

    #def makejob(self,writeinput=1,graph=None):
    def makejob(self):
        """Prepare a job which will perform AM1 optimisation of a molecule
        """

        if self.debug: print "building AM1 job"

        #Get an editor instance to pop up tk-error widgets
        ed = self.get_editor()

        self.set_defaults()

        # note that the sub-processes (pipe, spawn etc) are not used
        # in this case
        job = jobmanager.job.LocalJob()

        # Check we have parameters for this atom
        failed = self.check_avail_parameters()
        if failed:
            txt = ''
            for element in failed:
                txt = txt+element+' '
            if ed:
                ed.Error("Sorry, cannot run am1 optimisation as there are no parameters for the elements: %s" % txt)
            else:
                print "Sorry, cannot run am1 optimisationas there are no parameters for the elements: %s" % txt
            return None

        self.GetModel()
        mol_name = self.get_input("mol_name")
        job_name = self.get_name()

        # connect up the monitor to load structure back
        if ed:
            job.add_monitor(ed.monitor)

        job.add_step(jobmanager.job.PYTHON_CMD,'am1 optimisation',proc=self.runAM1,kill_cmd=self.killAM1)
        job.add_tidy(self.tidy)
        
        return job

    def killAM1(self):
        self.KillFlag = jobmanager.job.JOBCMD_KILL
        
    def endjob(self,graph):
        """This is executed in the slave thread when the job completes
        successfully.
        There should be no output from slaves unless activated from
        using the debug_slave flag.
        """
        return 0,""

    def tidy(self,code):
        """ This is run by the job editor when the job completes. Code
        is 0 if the job succeeded and 1 if it failed.
        
        This updates the calculation monitor so that it displays the last point
        calculated - this wasn't happening before as the monitor code is only
        run by the job editor when the calculation is running (see
        jobmanager/jobeditor.py)

        It also uses the editor dialog to inform the user that the optimisation
        has finished.
        """

        if self.debug: print "AM1 tidy executing with code ",code
        
        ed = self.get_editor()
        if ed.calcMon:
            ed.calcMon.update()
        ed.Info("Optimisation finished")
        

    def get_generator( self ):
        """Return a generator object that can be used to cycle through the
           geometry optimisation steps and return geometries.
        """

        mol=self.get_input('mol_obj')
        Am1Mol = am1.Molecule()
        # Create the molecule
        for atom in mol.atom:
            Am1Mol.add( atom.name, atom.symbol,atom.coord[0], atom.coord[1], atom.coord[2] )
        if self.get_parameter( 'opt_method' ) == 'Newton':
            if self.debug: print "Running quasi-newton optimization"
            self.generator = Am1Mol.newton( self.get_parameter('fixed'),
                                       self.get_parameter('frozen_density') )
        elif self.get_parameter( 'opt_method' ) == 'Conjugate-gradient':
            if self.debug: print "Running conjugate-gradient optimization"
            self.generator = Am1Mol.conjugategradient( self.get_parameter('max_iter'),
                                                       self.get_parameter('gradient_threshold'),
                                                       self.get_parameter('energy_threshold'))
        else:
            print "No calculation"

        return None

    def get_opt_step( self ):
        """Return a molecule and it's energy from an optimisation step"""

        if not self.generator:
            self.get_generator()

        try:
            junk = self.generator.next()
            if self.debug:print 'TEST',junk
            atoms, energy = junk
            
            tmp = zmatrix.Zmatrix()
            for new in atoms:
                atom = zmatrix.ZAtom()
                atom.name = new.name
                atom.symbol = new.symbol
                atom.coord = [ new.x, new.y, new.z ]
                tmp.atom.append( atom )

            self.AM1Mol = tmp
            self.molecules.append(tmp)

            # Make the new energy available to the calcmon
            self.AM1Energies.append(energy)

        except StopIteration:
            # Optimisation has completed
            return None, None
            
        self.optstep += 1

        if self.debug: print "get_opt_step returning: %s" % energy
        return tmp,energy


    def runAM1(self):
        """ Run the AM1 Optimiser. This loops over each optimisation point updating the
            main window with the latest structure.
        """
        if self.debug: print "Optimisation running"
        finished = None
        i=0
        while not finished:

            if self.debug: print "Optimisation step: %d" % i

            if self.KillFlag == jobmanager.job.JOBCMD_KILL:
                # Kill the job 
                print 'kill'
                return 1,"Killed"
            elif self.KillFlag == jobmanager.job.JOBCMD_CANCEL:
                # Kill the job and revert.
                print 'cancel'
            else:
                newmol, energy = self.get_opt_step()
                if newmol == None:
                    # We've finished so clean up and break out of the loop
                    if self.debug: print "runAM1 finished optimisation."
                    finished=1
                    self.generator = None
                    break
                i+=1 
        return 0,""

    def get_editor_class(self):
        return AM1CalcEd


class AM1CalcEd(QMCalcEd):
    """ This is not meant to provide input option editing, but provides
    access to the Run method which is used to control job execution and
    links to the job editor - and perhaps also calculation monitor
    """
    
    def __init__(self,root,calc,graph,**kw):
        QMCalcEd.__init__(self,root,calc,graph,**kw)

        # there will eventually be just one of these
        self.calcMon = None

    def Run(self,writeinput=1):
        """Run the calculation, via the following steps
        - ensure all widget data has been stored
        - invoke the makejob method of the calculation itself
          this will incorporate any
              * file staging
              * execution
              * postprocessing (eg python command)
              * tidy function (to execute once the job has finished or died).
        - register the job with the Job manager so its status is visible in the
          job editor
        - show the job editor
        - create a new thread and start execution
        """
        if self.master != None:
            print 'cant run slave calculation'
            return

        # self.ReadWidgets()

        # build job
        # .. this includes making up the input deck and
        #    scheduling the job steps
        # the graph object is needed so that the job can include
        # the final load of results back into the GUI
        job = self.calc.makejob()

        if not job:
            print 'could not create am1 job'
            return

        # create a calculation monitor window
        if CalculationMonitor:
            if not self.calcMon:
                self.calcMon = CalculationMonitor(self.root,command=self.calcmon_ops)
            self.calcMon.clear()
            self.calcMon.show()
            
        #self.AM1Lock = thread.allocate_lock()

        # register with the job manager
        if job:
            self.job_editor.manager.RegisterJob(job)
            self.job_editor.show()
        else:
            self.Error("Problem preparing Job - not submitted")
            return

        if self.job_thread == None:
            pass
        elif self.job_thread.isAlive():
            self.Error("This calculation is running already!")
            return

        self.job_thread = jobmanager.jobthread.JobThread(job)

        try:
            #self.CheckData()
            self.job_thread.start()
        except RuntimeError,e:
            #self.message["title"] = "Error"
            #self.message["message_text"] = str(e)
            #self.message["iconpos"] = 'w'
            #self.message["icon_bitmap"] = 'error'
            #self.message["buttons"] = ("Dismiss")
            print 'exception'
            self.Error(str(e))


    def monitor(self):
        """Transfer partially completed structure to GUI and update the graph widget
        """
        #print 'monitor'
        # Update displayed structure if a new geomtry has arrived
    
        if self.calc.AM1Mol:
            mol = self.calc.get_input('mol_obj')
            print 'UPDATE GEOM',self.calc.AM1Mol.atom[0].coord
            mol.import_geometry( self.calc.AM1Mol )
            if self.graph:
                print 'UPDATE GRAPH',self.calc.AM1Mol.atom[0].coord
                self.graph.update_from_object(mol)
            self.calc.AM1Mol = None

            # Update graph widget
            if CalculationMonitor:
                self.calcMon.update()
                self.calcMon.show()

    def calcmon_ops(self,operation,arguments):
        """ The operations that are passed to the calculation monitor.
        """
        if operation == 'newValues':
            print "refreshing calc from calcmon"
            # Probably don't need to lock here, as in the worst case we just get slightly
            # out of date values
            return self.calc.AM1Energies,None
        
        elif operation == 'stop':
            print "Stopping calc from calcmon"
            self.calc.killAM1()


class AM1CalcTests(unittest.TestCase):

    def makeCH2(self):
        model = zmatrix.Zmatrix()
        atom = zmatrix.ZAtom()
        atom.symbol = 'C'
        atom.name = 'C'
        model.insert_atom(0,atom)
        atom = zmatrix.ZAtom()
        atom.symbol = 'H'
        atom.name = 'H'
        atom.coord = [ 1.,0.,0. ]
        model.insert_atom(1,atom)
        atom = zmatrix.ZAtom()
        atom.symbol = 'H'
        atom.name = 'H'
        atom.coord = [ 1.,1.,0. ]
        model.insert_atom(1,atom)
        return model


    def testCH2(self):
        model = self.makeCH2()
        calc = AM1Calc()
        calc.set_input('mol_obj',model)
        calc.set_defaults()
        calc.runAM1()
        finalE = calc.AM1Energies[-1]
        self.assertAlmostEqual(-150.7306579594173,finalE)
        
    def testH20(self):
        model = zmatrix.Zmatrix()
        model.load_from_file(gui_path+os.sep+"examples"+os.sep+"water.zmt")
        calc = AM1Calc()
        calc.set_input('mol_obj',model)
        calc.set_defaults()
        calc.runAM1()
        finalE = calc.AM1Energies[-1]
        self.assertAlmostEqual(-348.51618349542707,finalE)

def testMe():
    """Return a unittest test suite with all the testcases that should be run by the main 
    gui testing framework."""

    return  unittest.TestLoader().loadTestsFromTestCase(AM1CalcTests)


if __name__ == "__main__":

    if 1:
        unittest.main()
    else:
        model = zmatrix.Zmatrix()
        model.load_from_file(gui_path+os.sep+"examples"+os.sep+"water.zmt")
        calc = AM1Calc()
        calc.set_input('mol_obj',model)
        calc.set_defaults()

        import Tkinter
        root=Tkinter.Tk()
        calc.set_input('mol_obj',model)
        jm = jobmanager.JobManager()
        je = jobmanager.jobeditor.JobEditor(root,jm)
        vt = AM1CalcEd(root,calc,None,job_editor=je)
        #vt.Run()
        root.mainloop()
