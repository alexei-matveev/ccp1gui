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

import os
import string
import sys

import Tkinter
import Pmw
import tkFileDialog
import viewer.help
from objects import zmatrix

from qm import *

from objects import am1


from interfaces.calcmon import *

MENU_ENER  = "Energy"
MENU_GRAD  = "Gradient"
MENU_OPT   = "Geometry Optimisation"

class AM1Calc(QMCalc):
    """Calculation object for the AM1 calculation
    """
    def __init__(self, **kw):

        print QMCalc
        print AM1Calc

        QMCalc.__init__(self,**kw)

        self.debug = 1
        self.generator = None
        self.optstep = 0 # to count optimisation steps

        self.molecules = []
        self.AM1Energies = []
        self.KillFlag = None
        self.AM1Mol = None

        
    def set_defaults( self ):
        """ Set up the default values for the calculation """
        print 'set def'

        # these to reset for new opt
        self.molecules = []
        self.AM1Energies = []
        self.AM1Mol = None
        self.KillFlag = None

        self.set_program('AM1')
        self.set_title('x')
        self.set_parameter('task',MENU_OPT)
        self.set_parameter('frozen_density', 1)
        self.set_parameter('fixed', -1)
        self.set_parameter('opt_method','Newton')
        self.set_parameter('job_name','am1 cleanup')
        
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

    def makejob(self,writeinput=1,graph=None):
        """Prepare a job which will perform AM1 optimisation of a molecule
        """

        if self.debug:
            print "building AM1 job"

        #Get an editor instance to pop up tk-error widgets
        ed = self.get_editor()

        self.set_defaults()

        job = jobmanager.ForegroundJob()

        # Check we have parameters for this atom
        failed = self.check_avail_parameters()
        if failed:
            txt = ''
            for element in failed:
                txt = txt+element+' '
            if ed:
                ed.error("Sorry, cannot run am1 optimisationas there are no parameters for the elements: %s" % txt)
            else:
                print "Sorry, cannot run am1 optimisationas there are no parameters for the elements: %s" % txt
            return

        self.GetModel()
        mol_name = self.get_input("mol_name")
        job_name = self.get_parameter("job_name")

        # connect up the monitor to load structure back
        if ed:
            job.add_monitor(ed.monitor)

        job.add_step(PYTHON_CMD,'am1 optimisation',proc=self.runAM1,kill_cmd=self.killAM1)
        #job.add_tidy(self.endjob2)
        
        return job

    def killAM1(self):
        self.KillFlag = JOBCMD_KILL
        
    def endjob(self,graph):
        """This is executed in the slave thread when the job completes
        successfully.
        There should be no output from slaves unless activated from
        using the debug_slave flag.
        """
        return 0,""

    def endjob2(self,code=0):
        """This function is executed in the main thread"""

        if self.debug:
            print 'running endjob2 code=',code

        # load contents of listing for viewing
        if self.debug_slave:
            print 'endjob....'
        job_name = self.get_parameter("job_name")
        directory = self.get_parameter("directory")
        file = open(directory+'/'+job_name+'.out','r')
        self.ReadOutput(file)
        file.close()

        print 'scan output'


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
            print "Running Newton calculation"
            self.generator = Am1Mol.newton( self.get_parameter('fixed'),
                                       self.get_parameter('frozen_density') )
        else:
            print "No calculation"

        return None

    def get_opt_step( self ):
        """Return a molecule and it's energy from an optimisation step"""

        if not self.generator:
            self.get_generator()

        try:
            junk = self.generator.next()
            print 'TEST',junk
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

        print "get_opt_step returning:"
        print energy
        #print newmol
        return tmp,energy


    def runAM1(self):
        """ Run the AM1 Optimiser. This loops over each optimisation point updating the
            main window with the latest structure.
        """
        print "Optimisation running"
        finished = None
        i=0
        while not finished:
            print "Optimisation step: %d" % i

            if self.KillFlag == JOBCMD_KILL:
                # Kill the job 
                print 'kill'
                return 1,"Killed"
            elif self.KillFlag == JOBCMD_CANCEL:
                # Kill the job and revert.
                print 'cancel'
            else:
                newmol, energy = self.get_opt_step()
                if newmol == None:
                    # We've finished so clean up and break out of the loop
                    print "runAM1 finished optimisation."
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
        apply(QMCalcEd.__init__, (self,root,calc,graph), kw)

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
        job = self.calc.makejob(writeinput=writeinput,graph=self.graph)


        # create a calculation monitor window
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

        self.job_thread = JobThread(job)

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
        print 'job done'


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
            self.stopAM1Opt()


if __name__ == "__main__":

    #mystery error if the following statement is included
    #from interfaces.gamessuk import *
    from objects.zmatrix import *
    from jobmanager import *
    model = Zmatrix()
    atom = ZAtom()
    atom.symbol = 'C'
    atom.name = 'C'
    model.insert_atom(0,atom)
    atom = ZAtom()
    atom.symbol = 'H'
    atom.name = 'H'
    atom.coord = [ 1.,0.,0. ]
    model.insert_atom(1,atom)
    atom = ZAtom()
    atom.symbol = 'H'
    atom.name = 'H'
    atom.coord = [ 1.,1.,0. ]
    model.insert_atom(1,atom)

    print 'x'
    calc = AM1Calc()
    calc.set_input('mol_obj',model)
    #calc.set_defaults()
    #calc.runAM1()

    root=Tk()
    if 1:
        calc.set_input('mol_obj',model)
        jm = JobManager()
        je = JobEditor(root,jm)
        calc2 = copy.deepcopy(calc)
        vt = AM1CalcEd(root,calc,None,job_editor=je)
        vt.Run()
    root.mainloop()
