#
#    This file is part of the CCP1 Graphical User Interface (ccp1gui)
# 
#   (C) 2002-2007 CCLRC Daresbury Laboratory
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
import os
import sys
import getpass
import socket
import jobmanager
import traceback
from viewer.paths import paths

import objects.vector

# see also jobman.py
#BLANK     = " "
MODIFIED  = "Modified"
SUBMITTED = "Submitted"
RUNNING   = "Running"
KILLED    = "Killed"
DONE      = "Done"


# Global dictionary
calced_dict = {}

class Calc:
    """This is a storage class holding the data for a general calculation.

 A calculation is an operation that uses a program implementing a particular 
 theory to transform a set of input data to a set of output data. The theory 
 can be tuned through a set of parameters (e.g. convergence criteria, 
 accuracies, etc.)

 It is assumed that the input and output data sets have a meaning independent 
of any program using or generating them. The parameters however will be 
 program dependent.

 The calculation must specify:
 - the program used
 - the theory used
 - the task to be performed (defines what the outputs will be)
 - the parameter set
 - the input data set
 - the output data set
 - the calculation status
 - the job options
 In addition a calculation will have: 
 - a name
 - a title

 For calculations the following operations will be specified
 - A new operation
 - A save operation
 - A load operation
 - A run operation
 In addition there must be operations to access the various data attributes.

    """
    def __init__(self,program="Unknown",name="unnamed",title="untitled",mol=None):

        """Create a calculation object."""
        self.new()

        self.debug = None
        self.debug_slave = 0

        user = getpass.getuser()
        self.LOCALHOST = jobmanager.job.LOCALHOST

##         self.jobopt    = { "hostname"  : "localhost",
##                            "directory" : ".",
##                            "submission": "Interactive",
##                            "username"  : user}

        #mol_name is kept for compatibility with pymol
        if mol:
            self.set_input("mol_obj" ,mol)
            self.set_input("mol_name",mol.name)
        else:
            self.set_input("mol_obj" ,None)
            self.set_input("mol_name",None)

        self.set_input("input_file",None)
        self.set_output("log_file",None)

        # were inputs, now parameters
        #self.set_parameter("hostname", "localhost")
        self.set_parameter("submission", self.LOCALHOST)
        self.set_parameter("directory", paths['user'])
        self.set_parameter("username", user)
        self.set_parameter("task", "Energy")
        self.set_parameter("charge"  ,0)
        self.set_parameter("spin"    ,1)


        #self.tasks = ["energy", 
        #              "optimise internal coord."] 

        # Optimisation page
        self.set_parameter('optimiser','Z-Matrix')
        self.set_parameter('optimiser_method','BFGS')
        self.set_parameter('max_opt_step',60)
        self.set_parameter('max_opt_line',60)
        self.set_parameter('max_opt_step_len',0.2)
        self.set_parameter('opt_conv_thsld',0.003)
        self.set_parameter('opt_value',0.6)
        self.set_parameter('find_ts',0)
        self.set_parameter('ts_mode',1)
        self.set_parameter("inp_file",None)

        self.set_name(name)

        if self.debug: print 'NEW CALC',program, name

        self.set_title(title)
        self.set_job(None)
        self.job_dict = {} # Keeps track of the parameters for jobs we have edited
                           # this session maps jobtype -> dictionary of parameters
                           # for that job


    def get_editor_class(self):
        """overload to return the editor class"""
        return None

    def ReadInput(self,file):
        input = file.readlines()
        self.set_input("input_file",input)

    def ReadOutput(self,file):
        output = file.readlines()
        self.set_output("log_file",output)

    def new(self,program="untitled",name="untitled",title="untitled"):
        """Reset the object to the empty state."""
        self.program   = program
        self.task      = None
        self.input     = {}
        self.output    = {}
        self.parameter = {}
        # self.jobopt    = {}
        self.name      = name
        self.title     = title
        self.note      = ""
        self.jobstatus = MODIFIED
        self.results   = []
        # no longer stored (cant be pickled)
        #self.graph     = None
        self.editing   = 0

    def list(self):
        """Print the contents of the object."""
        print self.__str__()

    def run(self):
        """To run the calculation (should be overloaded)"""
        assert 0!=0, "Calc.run should have been overloaded."

    def write_inputs(self):
        """This method will be called from within the job manager to generate
            all the required input data sets."""
        assert 0!=0, "Calc.write_inputs should have been overloaded."

    def read_outputs(self):
        """This method will be called from within the job manager to load
            all the available output data sets."""
        assert 0!=0, "Calc.read_outputs should have been overloaded."

    def scan(self,file):
        """To scan results from punchfile or similar (should be overloaded)"""
        assert 0!=0, "Calc.scan should have been overloaded."

    def WriteInput(self,filename=None):
        """Writes an output file to disk - should return path of the file as a string"""
        assert 0!=0, "Calc.WriteInput overloaded."

    # title methods

    def set_title(self,title):
        """Sets the title for the calculation."""
        self.title = title

    def get_title(self):
        """Returns the title of the calculation."""
        return self.title

    # name methods
    def set_name(self,name):
        """Sets the name for the calculation."""
        if self.jobstatus == SUBMITTED or self.jobstatus == RUNNING:
            pass
        else:
            self.name = name

    def get_name(self):
        """Returns the name of the calculation."""
        if self.name:
            return self.name
        else:
            return "unnamed"

    # input data sets things
    
    def set_input(self,name,reference):
        """Specify the source of an input data set."""
        if self.jobstatus == SUBMITTED or self.jobstatus == RUNNING:
            #print 'warning - job is already running'
            # return
            pass
        if not self.input.has_key(name):
            self.jobstatus = MODIFIED
        elif not self.input[name] == reference:
            self.jobstatus = MODIFIED
        self.input[name] = reference

    def has_input(self,name):
        """Returns true if a input data set is specified."""
        self.input.has_key(name)

    def get_input(self,name):
        """Returns the reference to the input data set."""

        if self.input.has_key( name ):
            return self.input[name]
        else:
            return None

    # output data sets things

    def set_output(self,name,reference):
        """Specify the target of an output data set."""
        self.output[name] = reference

    def has_output(self,name):
        """Returns true if a output data set is specified."""
        return self.output.has_key(name)

    def get_output(self,name):
        """Returns the reference to the output data set."""

        if ( self.output.has_key( name ) ):
            return self.output[name]
        else:
            return None

    # program specification things
    def set_program(self,name):
        """Sets the program name."""
        self.program = name

    def get_program(self):
        """Returns the program name."""
        if self.program:
            return self.program
        else:
            return None

    # program parameter things
    def set_parameter(self,name,reference):
        """Specify a parameter."""
        #if self.jobstatus == SUBMITTED or self.jobstatus == RUNNING:
        #return

        if not self.parameter.has_key(name):
            self.jobstatus = MODIFIED
        elif not self.parameter[name] == reference:
            self.jobstatus = MODIFIED
        self.parameter[name] = reference

    def has_parameter(self,name):
        """Returns true if a parameter is specified."""
        return self.parameter.has_key(name)

    def get_parameter(self,name):
        """Returns the reference to the parameter."""
        if self.parameter.has_key(name):
            return self.parameter[name]

    # notes things

    def set_notes(self,notes):
        """Specify a the notes """
        self.note = notes
    def get_notes(self):
        """Returns the reference to the parameter."""
        return self.note

    # job status things
    def set_jobstatus(self,status):
        """Set the current job status."""
        self.jobstatus = status

    def get_jobstatus(self):
        """Return the current job status."""
        return self.jobstatus

    def set_job(self,job):
        """
        Set the job for this calculation - this is expected to be called
        by the calculation editor to set the job before running it
        """
        self.job = job

    def get_job(self):
        """If the job editor has a job that is being edited return that job
        """

        if self.debug:
            print "calc get_job ",self.job

        if self.job:
            # Check that the jobtype matches the submission parameter
            jobtype = self.job.jobtype
            if not jobtype == self.get_parameter("submission"):
                print "calc get_job jobtype does not match submission parameter"
                return None
        return self.job


    def create_job( self, jobtype=None ):
        """Create a job of the specified type
        """

        if self.debug:
            print "calc create_job called with: %s" % jobtype
            
        if jobtype:
            # Set the submission type to this sort of job
            jobtype = self.set_parameter( "submission", jobtype )
        else:
            jobtype = self.get_parameter("submission")

        if self.debug: print "jobtype is ",jobtype

            
        if jobtype == self.LOCALHOST:
            job =  jobmanager.job.LocalJob()            
        elif jobtype == 'SSH':
            host = 'login.hpcx.ac.uk'
            user = 'psh'
            job =  jobmanager.job.RemoteJob(host,user)
        elif jobtype == 'RMCS':
            job =  jobmanager.job.RMCSJob()
        elif jobtype == 'Nordugrid':
            job =  jobmanager.job.NordugridJob()
        elif jobtype == 'Globus':
            job =  jobmanager.job.GlobusJob()
        else:
            raise AttributeError,"create_job: unknown jobtype: %s" % jobtype

        # Need to set the program/calc type so we know what sort of
        # job this is
        program = self.get_program()
        job.set_parameter('calctype',program)

        # See if the user has any default settings for this type of job
        job.update_parameters_from_defaults()

        # Then update any that haven't been set already - this assumes we pass
        # a pointer to the job so that this updates the job directly
        self.set_job_defaults( job )

        # If we've run a previous calculation this session, update the dictionary
        # with those parameters
        if self.job_dict.has_key( job.jobtype ):
            job.update_parameters( self.job_dict[ job.jobtype ] )
        

        # Set this as the job for the calculation so that the editor can get at it
        self.set_job( job )
        
        return self.job

    def set_job_defaults(self,job):
        """
        Set any default parameters for calculations with this type of job

        This is expected to be called after the job parameters for the job
        have been updated from the users' defaults dictionary, so it should
        only overwrite those parameters that are unset.
        """
        if self.debug:
            print "calc set_job_defaults"

        # Always set the working directory to the directory parameter of the calc
        if job.jobtype == self.LOCALHOST:
            if not job.get_parameter( 'local_directory' ):
                job.set_parameter( 'local_directory', self.get_parameter('directory') )
                return

    def OpenInit(self):
        """When loading the calculation from a file we need to send
        the geometry to the viewer."""
        mol_obj = self.get_input('mol_obj')
        mol_name = self.get_input('mol_name')
        if self.get_editor():
            self.get_editor().load_to_graph(mol_name)

    def GetModel(self):
        """Pull the structure from the GUI
        (if we are editing the coordinates we assume that
        the modified ones are already in the gui,but
        will take internal coordinates from the editor as
        Pymol will have lost them
        """
        # Task of updating model is performed at present by the
        # calculation editor
        ed = self.get_editor()
        if ed:
            self.get_editor().Reload()

    def CheckSpin(self, show=None):
        """Check the molecule, charge, and multiplicity for consistency"""

        self.show = show
        self.GetModel()
        mol_obj = self.get_input('mol_obj')
        spin   = self.get_parameter("spin")
        charge   = self.get_parameter("charge")
        mxcharge = int(mol_obj.get_nuclear_charges())
        nelec = mxcharge - charge
        mnspin = nelec - 2*int(nelec/2) + 1
        spineven = (mnspin - 2*int(mnspin/2) == 0)
        mxspin = max(nelec + 1,mnspin)
        badspin = None

        ##print 'check spin:', spin, charge, mxspin, mnspin, spineven

        if spin > mxspin:
            message_text = \
            "Currently selected spin "+str(spin)+" exceeds\nmaximum "+\
            "spin multiplicity of "+str(mxspin)+" for\nthe currently "+\
            "selected molecule."
            badspin = 1
        elif spineven != (spin - 2*int(spin/2) == 0):
            if spineven:
                message_text = \
                "The currently selected spin "+str(spin)+" is "+\
                "inconsistent with\nthe number of electrons in the "+\
                "molecule.\nThe spin should have an even value."
                badspin = 1
            else:
                message_text = \
                "The currently selected spin "+str(spin)+" is "+\
                "inconsistent with\nthe number of electrons in the "+\
                "molecule.\nThe spin should have an odd value."
                badspin = 1

        else:
            message_text = "Current Spin OK"
            badspin = 0

        # If we have an editor running use a dialog to announce this
        ed = self.get_editor()
        if ed:
            if self.show == None:
                ed.Info(message_text)
            else:
                if badspin == 1:
                    ed.Info(message_text)
        else:
            print message_text
            
        return badspin

    def get_editor(self):
        """Return the calculation editor object which is editing this object"""
        t = id(self)
        try:
            return calced_dict[t]
        except KeyError:
            return None

    def set_editor(self,editor):
        """Define the an editor for the current object"""
        t = id(self)
        if editor:
            calced_dict[t] = editor
        else:
            try:
                del calced_dict[t]
            except KeyError:
                pass

    def edit(self,root,graph,editor=None,**kw):
        """return a calculation editor to edit the data"""

        if editor:
            editor.calc = self
            return editor
        else:
            if self.get_editor_class():
                try:
                    e = apply(self.get_editor_class(),(root,self,graph),kw)
                    return e
                except EditError:
                    pass
            else:
                print 'Internal Error - No editor class defined'

        return None

    def warn(self,txt):
        ed = self.get_editor()
        if ed:
            ed.Info(txt)
        else:
            print "Warning: ",txt
        
    def error(self,txt):
        """ handler for problems encountered by the calc clasees"""
        # strange core dump from this
        #      if self.editor:
        #         self.editor.error(txt)
        #      else:

        print 'Error: ' + txt
        ed = self.get_editor()
        if ed:
            ed.Error(txt)
        raise Exception, txt

    def fit_grid_to_mol(self,field,mol,border=1.0):
        """ utility function to fit a grid around a molecule"""
        big=100000
        minx = big;   miny = big;   minz = big
        maxx = -big;  maxy = -big;  maxz = -big
        for a in mol.atom:
            minx = min(minx,a.coord[0])
            maxx = max(maxx,a.coord[0])
            miny = min(miny,a.coord[1])
            maxy = max(maxy,a.coord[1])
            minz = min(minz,a.coord[2])
            maxz = max(maxz,a.coord[2])
        minx = minx  - border
        maxx = maxx  + border
        miny = miny  - border
        maxy = maxy  + border
        minz = minz  - border
        maxz = maxz  + border

        field.origin = 0.5*objects.vector.Vector(minx+maxx,miny+maxy,minz+maxz)
        field.axis[0] = objects.vector.Vector(maxx-minx,0.,0.)
        field.axis[1] = objects.vector.Vector(0.,maxy-miny,0.)
        field.axis[2] = objects.vector.Vector(0.,0.,maxz-minz)
        
    def store_results_to_gui(self):
        """This procedure scans the results of the calculation,
        assumed kept in self.results, where possible loads them up
        into GUI and also replaces the molecule
        from self.get_input("mol_obj") with the LAST structure
        in the sequence.
        Lists are assumed to be charges and are added to the molecule
        Returns 0 if the structure was updated,
        1 if the structure was found to me missing
        """

        # construct the results list for visualisation
        warn=0
        mols = []
        loadables = []
        for o in self.results:

            # take the last field of the class specification
            t1 = str(o.__class__).split('.')
            myclass = t1[len(t1)-1]

            if myclass == 'VibFreq' or \
                   myclass == 'VibFreqSet' or \
                   myclass == 'Brick' or \
                   myclass == 'Field' or \
                   myclass == 'File' :
                loadables.append(o)

            elif myclass == 'Indexed' or myclass == 'Zmatrix':
                # will need to organise together with other results
                # assume overwrite using last structure for now
                mols.append(o)

            elif myclass == 'ZmatrixSequence':
                o.connect()
                loadables.append(o)

            # list class is just used for atomic charge data at present
            elif myclass == 'List':
                mol_obj  = self.get_input("mol_obj")
                mol_obj.charge_sets.append((o.type,o.data))

        upd = 0
        if len(mols):

            # Take the last structure and over-write the current structure
            # with it
            # use import_geometry to try and keep all elements of old structure
            # including internal coordinates

            # Dont try and update structure sequences here, instead
            # we return all structures for use
            
            oldo = self.get_input("mol_obj")

            for o in mols[:-1]:
                self.results.append(o)
            o = mols[-1]

            if self.debug:
                print 'NEW GEOMETRY'
                o.connect()
                print o.bonds_and_angles()
            try:
                oldo.import_geometry(o,update_constants=0)
            except objects.zmatrix.ImportGeometryError:
                warn=1
                copycontents(oldo,o)

            if self.debug:
                print 'UPDATED GEOMETRY'
                oldo.zlist()
                print oldo.bonds_and_angles()

            if warn:
                print ' Warning: could not retain old zmatrix, so imported as cartesians'
            upd = 1

        ed = self.get_editor()
        if ed:
            if ed.graph:
                # Import
                ed.graph.import_objects(loadables)
                # Dialog
                txt = "Objects loaded from punchfile:"
                if upd:
                    txt = txt  + "Structure update" + '\n'
                else:
                    txt = txt  + '\n'
                
                for r in loadables:
                    txt = txt + r.title + '\n'
                ed.Info(txt)

            # Update anything dependent on the new structure, e.g. coordinate editors
            if ed.update_func and upd:
                o = self.get_input("mol_obj")
                if self.debug:
                    print 'calling update_func on new structure'
                ed.update_func(o)

        return not upd

def copycontents(to,fro):
    """Used to update an object by copying in the contents from another"""
    c = to.__class__
    d1 = c.__dict__
    try:
        d2 = fro.__dict__
    except AttributeError:
        d2 = {}
    for k in d2.keys():
        to.__dict__[k] = fro.__dict__[k]

class CalcError(RuntimeError):
    def __init__(self,message):
        
       #self.args = args
       # Make sure that message is a string
       if type(message) == list:
           message = "\n".join(message)
       if type(message) != str:
           message = str(message)
       
       self.args = message
       self.msg = message
       
    def __str__(self):
        return self.msg

class EditError(RuntimeError):
    def __init__(self,args=None):
        self.args = args

