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
import os,sys
if __name__ == "__main__":
    # Need to add the gui directory to the python path so 
    # that all the modules can be imported
    gui_path = os.path.split(os.path.dirname( os.path.realpath( __file__ ) ))[0]
    sys.path.append(gui_path)


import exceptions
import os
import re
import copy
import cPickle
import traceback
import threading

import Pmw
import Tkinter
import tkFileDialog

import interfaces.calc
import interfaces.tools
import interfaces.inputeditor
from interfaces.jobed import RMCSEditor,NordugridEditor,GlobusEditor,LocalJobEditor

import objects.zme
import objects.grideditor

import jobmanager
import jobmanager.job

from viewer.initialisetk import initialiseTk
 

Create = 0
Raise  = 1
Lower  = 2

Mol_Key = 100

class CalcEd(Pmw.MegaToplevel):

    """Check if calculation is already being edited,
    Build the basic calculation GUI,
    hide the GUI (to be shown if the show method is invoked).
    master denotes an editor object that will execute run, save etc
    arguments:
    root      parent tk instance 
    calc      the calculation to be edited
    graph     graph object for getting/displaying stucture
    master    calculation (of this is one component of a QM/MM or similar)
    mol_name  identifier to pass to reload_func
    """

    width = 450
    height = 500

    def __init__(self,root,calc,graph,
                 master=None,
                 mol_name=None,
                 vis=None,
                 job_editor=None,
                 reload_func=None,
                 update_func=None,
                 on_exit=None,
                 **kw):

        if calc.get_editor():
            raise interfaces.calc.EditError("Editor open already")
        else:
            calc.set_editor(self)

        initialiseTk(root)

        self.calc = calc

        # Define the megawidget optons.
        self.reload_func = reload_func
        self.update_func = update_func
        self.on_exit = on_exit

        optiondefs = (
           ('command',   None,   Pmw.INITOPT),
           )
        self.defineoptions(kw, optiondefs)

        # Initialise base class (after defining options).
        Pmw.MegaToplevel.__init__(self, root)

        title=self.calc.get_program()+" Calculation: "+self.calc.get_name()

        self.title(title)
        #self.geometry('%dx%d+0+0' % (self.frameWidth, self.frameHeight))

        self.debug = 0
        self.debug_slave = 0
        self.inputeditor = None
            
        self.jobsub_editor=None
                           
        # Class associated with job manager thread
        self.job_editor = job_editor
        self.job_thread = None
        
        self.root = root
        self.pages = {}

        self.lock  = threading.RLock()


        # store the graph object 
        # - used to get/put structures, and also to process results
        self.graph = graph

        #
        # Build the message dialogs
        #
        self.msg_dialog = Pmw.MessageDialog(self.root, 
                                            title = 'Information',
                                            iconpos='w',
                                            icon_bitmap='info',
                                            defaultbutton = 0)
        self.msg_dialog.withdraw()

        self.query_dialog =  Pmw.MessageDialog(self.root,
                                               title = "Query:",
                                               iconpos='w',
                                               icon_bitmap='question',
                                               buttons = ("Yes","No","Cancel"),
                                               command = self.__QueryResult)
        self.query_dialog.withdraw()
        
        self.dialogresult = ""

        #
        # Create the elements of the editor widget
        #
        #self.balloon = Pmw.Balloon(self.interior())
        if kw.has_key('balloon'):
            balloon = kw['balloon']
            self.balloon = balloon
        else:
            self.balloon = Pmw.Balloon(self.interior())
            
        if kw.has_key("filename"):
            self.filename = kw["filename"]
        else:
            self.filename = "./"

        self.menu    = self.__CreateMenuBar(self.interior(),self.balloon)

        self.master = master

        # For the rest of the widget construction, see
        # the code specific sections
        self.tasks = []

        ###self.statusframe = self.__CreateStatusFrame(self.interior())

        fixedFont = Pmw.logicalfont('Courier')
        self.textview = Pmw.TextDialog(
           self.interior(),
           text_width = 80)
        self.textview.configure(text_font = fixedFont)
        self.textview.withdraw()

        # Visualisation dictionary, provides mapping between
        # results of the calculation and their graphical
        # representations (currently a one-to-one mapping)

        self.vis_dict = {}

        # Set up the object for visualisation
        # Both name and object will be set to None
        # mol_name = self.calc.get_input("mol_name")

        mol_obj  = self.calc.get_input("mol_obj")

        if not mol_obj:

            if self.reload_func:
#####            if mol_name:
                self.calc.set_input("mol_name",mol_name)
                self.Reload()
                if self.calc.get_name() == "untitled":
                    self.calc.set_name(mol_name)
            else:
                # choose a structure name from the GUI and load it
                self.SelectMolecule()

        # We expect there to be a visualiser for the active
        # molecule already made

        if vis:
            # hack - this is now a list
            self.mol_vis = vis[0]
        elif graph:
            #PS this code is now too simple
            #   it draws the structure OK
            #   needs to add data_list, vis_dict etc stuff
            #   To simplify we should handle all this before the editor
            #   is invoked (see main.py)
            #####self.mol_vis = self.graph.molecule_visualiser(self.root,self.graph,
            #####self.calc.get_input("mol_obj"))
            #####self.mol_vis.Build()
            print 'Warning graph passed to calced but vis=None'
            self.mol_vis = None
        else:
            self.mol_vis = None

        self.vis_dict[Mol_Key] = self.mol_vis

        if calc.editing:
            # needed to avoid "already editied" condition
            self.calc.editing = 0
            # structure contains internal coordinates
            self.EditCoordinates(model=mol_obj)

        # This method can be found one of the derived classes
        self.CreateCalcMenu(self.menu)
        


        # Add some generic tools
        # This must come before any tool widget creation...

        # List of parameter tools (see tools.py)
        self.tools = []
        
        self.CreateNotebook()
        
        self.title_tool = interfaces.tools.TitleTool(self)
        #self.charge_tool = interfaces.tools.IntegerTool(self,'charge','Charge')
        #self.spin_tool = interfaces.tools.IntegerTool(self,'spin','Spin Multiplity',mini=0)



        # defer until 
        #print 'layout'
        #self.LayoutToolsTk()

    def LayoutToolsTk(self):
        """ Place the widgets belonging to the tools (ChargeTool etc)
        This will generally be replaced by a more specific function
        for a particular code interface.
        """
        page = self.notebook.add('Molecule',tab_text='Molecule')
        self.title_tool.widget.pack(in_=page)
        self.charge_tool.widget.pack(in_=page)
        self.spin_tool.widget.pack(in_=page)
        Pmw.alignlabels([self.title_tool.widget, self.charge_tool.widget, self.spin_tool.widget ])

    def __QueryResult(self,result):
        """Pmw silliness, need to get the result of a query. 
            Have to have a routine to store the result and remove the 
            window (sigh)."""
        self.dialogresult = result
        self.query_dialog.deactivate()

    def edit_grid(self):
        """Allow adjustment of the grid parameters """
        field=self.calc.get_parameter('grid')
        if not self.calc.field_sized:
            m = self.calc.get_input("mol_obj")
            self.calc.fit_grid_to_mol(field,m)
            self.calc.field_sized = 1

        self.grid_vis = None
        window=objects.grideditor.GridEditor(self.root, field, command=self.view_grid, exitcommand=self.done_view_grid)
        window.show()
        self.root.update()
        window.reposition()
        
    def view_grid(self, field):
        """ callback for the grid editor to enable the grid to be visualised
        as it is being edited
        """
        # Create the image if not already active
        if not self.grid_vis:
            t = id(field)
            self.grid_vis = self.graph.grid_visualiser(self.root,self.graph,field)
            self.vis_dict[t] = self.grid_vis
            self.grid_vis.Show()
        self.grid_vis.Build()

    def done_view_grid(self, field):
        """ remove the image of the grid"""
        t = id(field)
        vis = self.vis_dict[t]
        vis.Hide()

    def reposition(self):
        """ place window relative to main graphics window"""
        parent = self.graph.master
        m = re.match('(\d+)x(\d+)\+(-?\d+)\+(-?\d+)',parent.geometry())
        msx,msy,mpx,mpy = int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4))
        #print 'master geom',    msx,msy,mpx,mpy
        self.geometry("+%d+%d" % (mpx+msx+4,mpy+1))

    def __del__(self):
        self.Withdraw()
        self.destroy()

    def __CreateMenuBar(self,parent,balloon):
        """Create the basic calculation menu bar."""
        menu = Pmw.MenuBar(parent,
                           hull_relief = 'raised',
                           hull_borderwidth = 1,
                           balloon = balloon)
        menu.pack(fill='x')
        return menu

    def Show(self):
        """Make the GUI visible."""
        self.show()
        self.reposition()

    def Withdraw(self):
        """Withdraw the GUI from the screen."""
        self.withdraw()

    def WriteInput(self):

        self.ReadWidgets()
        try:
            filename = self.calc.WriteInput()
        except Exception,e:
            self.Error("Error writing input file!\n%s" % e)
            return None

        self.Info("Wrote input file to disk:\n%s" % filename)
        return
    
    def ReadWidgets(self):
        for tool in self.tools:
            tool.ReadWidget()
        
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

        if self.job_thread == None:
            pass
        elif self.job_thread.isAlive():
            self.Error( "This calculation is running already!" )
            return
            
        # build job
        # .. this includes making up the input deck and
        #    scheduling the job steps
        # the graph object is needed so that the job can include
        # the final load of results back into the GUI
        self.ReadWidgets()

        try:
            job = self.calc.makejob(writeinput=writeinput,graph=self.graph)
        except Exception,e:
            traceback.print_exc()
            self.Error( "Error creating job: %s" % (e,) )
            return

        if not job:
            self.Error( "No job returned by the makejob routine!" )
            return

        try:
            self.start_job( job )
        except Exception,e:
            traceback.print_exc()
            self.Error( "Error starting job: %s!\n%s" % (job.name,e) )
            return

        # Job has been started so remove this job from the calculation object
        # but save the old job dictionary so that we can resuse it

        # Update the job_dict with the parameters from this job
        jobtype = job.jobtype
        parameters = job.get_parameters()
        self.calc.job_dict[ jobtype ] = copy.copy(parameters)
        self.set_job( None )

    def start_job(self,job):
        """Start a job running under control of the job manager"""
        self.job_editor.start_job( job )
        self.job_thread = job.thread

    def Reload(self):
        """Reload the model
        This is only executed if the calling object provided
        a function for the purpose
        """
        if self.reload_func:
            mol_obj = self.reload_func()
            self.calc.set_input("mol_obj",mol_obj)
            # this field is used by the visualisers
            mol_name = self.calc.get_input("mol_name")
            mol_obj.title = mol_name


    def Scan(self):
        """Load results from an earlier run"""
        #self.LowerPage(self.notebook.getcurselection())
        try:
            #self.CheckData()
            self.calc.scan()
        except RuntimeError,e:
            self.Error(str(e))

    def Close(self):
        """Close this calculation and destroy the associated data structures.
            1) Lower the current page
            2) Popup "are you sure" dialog
            3) Check whether a save is needed and save if yes
            4) Destroy current editor."""
        #self.LowerPage(self.notebook.getcurselection())
        self.Query("Are you sure you want to close this calculation\n"+
                  "and lose all unsaved changes?")
        if self.dialogresult == 'Yes':
            if self.on_exit:
                self.on_exit()
            self.withdraw()
            self.destroy()

    def EndEdit(self):
        """Close this calculation edit"""
        #self.LowerPage(self.notebook.getcurselection())
        self.calc.set_editor(None)
        try:
            self.withdraw()
        except:
            pass
        try:
            self.destroy()
        except:
            pass


    def CreateViewMenu(self,menu):
        """Create the view menu:
            Output."""
        menu.addmenu('View','View calculation data-structures: Input/Output')
        menu.addmenuitem('View','command',
                     'View the calculation input file',
                     command = lambda s=self: s.ViewInput(),
                     label = 'Input')
        menu.addmenuitem('View','command',
                     'View the calculation output file',
                     command = lambda s=self: s.ViewOutput(),
                     label = 'Output')

    def CreateEditMenu(self,menu):
        """Create the view menu:
            Output."""
        menu.addmenu('Edit','Edit data files: Input')
        menu.addmenuitem('Edit','command',
                     'Edit the calculation input file',
                     command = lambda s=self: s.EditInput(),
                     label = 'Input')

    def CreateNotebook(self):
        """Create a basic notebook frame."""

        self.notebook = Pmw.NoteBook(
           self.interior(),
           hull_width = self.width,
           hull_height = self.height,
           createcommand=self.CreatePage,
           raisecommand=self.RaisePage,
           lowercommand=self.LowerPage)
        self.notebook.pack(expand=1, fill='both')

    def CreatePage(self,pagename):
        """The function self.CreatePage will be attached to the createcommand
            option of the note book, and will be issued after the page
            has been created, allowing the contents to be added to the page
            the call looks like
            self.TaskPage(page,Create)
            where self. is the Calculation editor object
            """
        fnc = "self."+pagename
        fnc = fnc+"(self.notebook.page(pagename),Create)"
        #self.lock.acquire()
        #exec(fnc)
        #self.notebook.setnaturalpagesize()
        #self.lock.release()

    def LowerPage(self,pagename):
        """The function self.LowerPage will be attached to the lowercommand
            option of the note book. As we don't know about all the pages
            that the complete GUI will have this method needs to be overloaded
            by the top level class. Its function is to sample entry-fields where
            necessary."""
        fnc = "self."+pagename
        fnc = fnc+"(self.notebook.page(pagename),Lower)"
        #self.lock.acquire()
        #exec(fnc)
        #self.lock.release()

    def RaisePage(self,pagename):
        """The function self.RaisePage will be attached to the raisecommand
            option of the note book. As we don't know about all the pages
            that the complete GUI will have this method needs to be overloaded
            by the top level class. Its function is to update entry-fields where
            necessary."""
        fnc = "self."+pagename
        fnc = fnc+"(self.notebook.page(pagename),Raise)"
        #self.lock.acquire()
        #exec(fnc)
        #self.lock.release()

    def Resize(self):
        """Resize the notebook, and hence the whole widget"""
#      self.notebook.setnaturalpagesize()

    def CreateCalcMenu(self,menu):
        """Create the file menu:
            New, Open, Save, Close.
        chemshell - need to leave off most of these for masters"""

        menu.addmenu('Calc','Operations on Calculations: Open / Save / Run')

        #menu.addmenuitem('Calc','command',
        #             'Setup a new calculation',
        #             command = lambda s=self: s.reset(),
        #             label = 'New')

##         menu.addmenuitem('Calc','command',
##                      'Get a calculation from file',
##                      command = lambda s=self: s.OpenCalc(),
##                      label = 'Open...')

        menu.addmenuitem('Calc','command',
                     'Save the calculation to file',
                     command = lambda s=self: s.SaveCalc(),
                     label = 'Save...')

        if self.master == None:
            menu.addmenuitem('Calc','command',
                             'Run the calculation',
                             command = lambda s=self: s.Run(writeinput=1),
                             label = 'Run')

        # original idea to Copy stuff by a copy command does not work because
        # it leads to circular dependencies in the import phase.
        #menu.addmenuitem('Calc','command',
        #             'Copy the current calculation to a new one',
        #             command = lambda s=self: s.Copy(),
        #             label = 'Copy')

        menu.addmenuitem('Calc', 'command',
                      'Write input file',
                      label='Write Inputfile',
                      command = lambda s=self: s.WriteInput() )

#jmht
#        if self.master == None:
#            menu.addmenuitem('Calc', 'command',
#                             'Run input file',
#                             label='Run Inputfile',
#                             command = lambda s=self: s.Run(writeinput=0) )

        #menu.addmenuitem('Calc', 'command',
        #              'load Punchfile',
        #              label='Load Punchfile',
        #              command = lambda s=self: s.Scan() )

        menu.addmenuitem('Calc','command',
                     'Close the calculation editor',
                     command = lambda s=self: s.Close(),
                     label = 'Close')

        #menu.addmenuitem('Calc','command',
        #             'Update structure from GUI',
        #             command = lambda s=self: s.Reload(),
        #             label = 'Reload Model')

    
    def reload_for_zme(self):
        """A utility for coordinate editor, extractes the current
        structure from the graphics
        this should be the working structure for any
        calculation to be run

        probably a no-op in our GUI because the mol object is common
        """
        if self.graph:
            mol = self.calc.get_input("mol_obj")
            mol_name = str(id(mol))
            tt = self.graph.load_from_graph(mol_name)
            tt.title = mol_name
            return tt
        else:
            # Dummy code 
            return self.calc.get_input('mol_obj')

    def update_for_zme(self,obj):
        """Deal with a new update to the edited structure
        """
        if self.graph:
            mol_name = self.calc.get_input('mol_name')
            self.graph.update_model(mol_name,obj)

    def ViewInput(self):
        """Drag out the input file and show in a text widget."""
        input = self.calc.get_input('input_file')
        if input == None:
            self.Info("No input file available currently")
        else:
            textview = self.textview
            textview.configure(text_state="normal",title="Input Listing")
            textview.clear()
            for a in input:
                textview.insert('end',a)
            textview.configure(text_state="disabled")
            textview.show()

    def EditInput(self):
        """Check if there is an input, if there is make sure we are
           not editing it before firing up an editor.
        """
        data = self.calc.get_input('input_file')
        if not data:
            try:
                # Need to impelement the createInput methods in other calc editors...
                data = self.calc.createInput()
            except AttributeError:
                self.Info("No input file available currently")
                return None
                
        if self.inputeditor:
            self.inputeditor.withdraw()
            self.inputeditor.show()
            return
        else:
            self.inputeditor = interfaces.inputeditor.InputEd(self.interior(),self.calc,self,data=data)
            return 
       

    def ViewOutput(self):
        """Drag out the output file and show in a text widget."""
        output = self.calc.get_output('log_file')
        if output == None:
            self.Info("No output file available currently")
        else:
            textview = self.textview
            textview.configure(text_state="normal",title="Job Listing")
            textview.clear()
            for a in output:
                textview.insert('end',a)
            textview.configure(text_state="disabled")
            textview.show()

    def load_to_graph(self):
        """ Output the current structure to the GUI
        Not used any more
        """

        if self.update_func:
            mol_obj  = self.calc.get_input("mol_obj")

            # this is needed in tkmolview
            mol_name  = self.calc.get_input("mol_name")
            mol_obj.name = mol_name

            self.update_func(mol_obj)

    def update_graph(self):
        """ Update the graph
        this wont be needed when using a graphics systems
        running in its own thread
        """
        if self.graph:
            self.graph.update()

    def Copy(self):
        """Copy the contents of this calculation to a new one and launch
        the appropriate calculation editor.
        
        This is no longer useful as all the editor callbacks
        are missing, need to invoke the copy from the tkmolview.main
        """

        newcalc = copy.deepcopy(self.calc)
        newcalc.set_jobstatus(MODIFIED)
        newcalc.edit()

    def prdict(self,obj,name,depth):
        """Cycle through a calculation object and try and pickle the various
           objects - used for debugging pickling errors (see SaveCalc )
        """
        try:
            myclass = obj.__class__
        except:
            myclass = ""

        try:
            fobj = open('junk.pkl','w')
            p = cPickle.Pickler(fobj)
            p.dump(obj)
            fobj.close()
            pkl='pickled ok'
        except:
            pkl='NOT PICKLABLE'
            

        for i in range(depth):
            print "   ",
        print name, pkl, obj, myclass

        try:
            dicts = obj.__dict__.keys()
        except AttributeError:
            dicts = []

        for y in dicts:
            o = obj.__dict__[y]
            self.prdict(o,y,depth+1)
        
    def SaveCalc(self):
        """Pickle the current calculation: 
            1) Lower the current page (for data consistency)
            2) Popup a file browser
            3) Call the calculations write method"""
        #self.LowerPage(self.notebook.getcurselection())
        calcdir = self.calc.get_parameter("directory")
        if self.calc.has_parameter("job_name"):
            name = self.calc.get_parameter("job_name")+".clc"
        else:
            name = self.calc.get_name()+".clc"
        sfile = tkFileDialog.asksaveasfilename(initialfile = name,
                                               initialdir = calcdir,
                                               filetypes=[("Calc File","*.clc"),])
        self.ReadWidgets()
        if len(sfile):
            self.filename = sfile
            # store the internal coordinates as part of the calculation object
            ###if self.calc.editing:
            ###    self.calc.set_input("mol_obj",self.zme.get_mol())
            calc = self.calc
            
            # Below used for debugging pickling errors
            #self.prdict(calc,'TOP',0)
            fobj = open(sfile,'w')
            p = cPickle.Pickler(fobj)
            p.dump(self.calc)
            fobj.close()

    def OpenCalc(self):
        """Unpickle a calculation: 
            1) Popup a file browser
            2) Open the file
            3) Call the calculations read method
            4) Close the file
            5) Raise the currently selected page
            chemshell - should update other calculation widgets?

            This will overwrites the existing calculation
            It is not currently in use (see qmapp.py)
        """
        calcdir = self.calc.get_parameter("directory")
        if self.calc.has_parameter("job_name"):
            name = self.calc.get_parameter("job_name")
        else:
            name = self.calc.get_name()
        ofile = tkFileDialog.askopenfilename(initialfile = name+".clc",
                                             initialdir = calcdir,
                                             filetypes=[("Calc File","*.clc")] )
        if len(ofile):
            self.filename = ofile
            fobj = open(ofile,'r')
            u = cPickle.Unpickler(fobj)
            self.calc = u.load()
            fobj.close()
            
            self.calc.edit(self.root, self.graph,editor=self)

    def SelectMolecule(self):

        """ Make a selection for the molecule to be used in the
        calculation. The main purpose of this routine is to force any
        user to explicitly select a molecule through a dialog box. 
        If no molecule is present in the viewer an error condition is
        raised."""

        if self.graph:
            if mol_name == None or mol_name == "":

                mol_list = self.graph.get_names()

                if len(mol_list) == 0:
                    #
                    # No molecules present ??? 
                    #
                    self.Error("No molecules to choose from present in viewer.\n" +
                               "Please load a structure and retry.")
                    raise interfaces.calc.EditError("No molecular structures present!")
                elif len(mol_list) == 1:
                    #
                    # Select the 1 molecule present...
                    #
                    mol_name = mol_list[0]
                else:
                    #
                    # Bring up a selection widget
                    #
                    self.result = Tkinter.StringVar()
                    self.dialog = Pmw.Dialog(self.interior(),
                                             buttons = ('OK','Cancel'),
                                             title = 'Select Molecule',
                                             command = self.__StoreResult)
                    self.var = Tkinter.StringVar()
                    self.dialog.mol = Pmw.OptionMenu(self.dialog.interior(),
                                                     labelpos = 'n', 
                                                     label_text="Please select a molecular\nstructure "+
                                                     "from the list",
                                                     menubutton_textvariable = self.var,
                                                     items = mol_list,
                                                     initialitem = mol_list[0])
                    self.dialog.mol.pack(fill='both')
                    self.dialog.activate()
                    if self.result.get() == 'OK':
                        mol_name = self.var.get()
                    else:
                        raise interfaces.calc.EditError("No molecular structure selected!")

            self.calc.set_input("mol_name",mol_name)
            #print 'reload called from selectmolecule'
            self.Reload()
            if self.calc.get_name() == "untitled":
                self.calc.set_name(mol_name)

    def __StoreResult(self,option):
        """Store the name of the pressed button and destroy the 
        dialog box."""
        self.result.set(option)
        self.dialog.destroy()

    def set_jobstatus(self,status):
        self.calc.set_jobstatus(status)
        # Now handled by job manager
        # self.statusframe.l1.configure(text='Job '+status)

    def get_job(self):
        """
        Return the job if this editor is already editing one
        and it matches the submission type

        """

        if self.debug:
            print "calced get_job"

        # The selected submission policy
        jobtype = self.calc.get_parameter("submission")
        job = self.calc.get_job()
        if job:
            print "calced get_job already has job: %s : %s " % (job,job.jobtype)
            if job.jobtype == jobtype:
                # Returning an old job:
                # Sort of a hack - need to null out the home directory parameter if one
                # exists as otherwise trying to run the same job on another machine causes
                # the home directory for the previous machine to be lost (see GlobusJob get_homedir)
                # same for self.host
                #if job.job_parameters:
                #    if job.job_parameters.has_key('remote_home'):
                #        job.job_parameters['remote_home'] = None
                return job
            else:
                print "calced get_job we have a job but it is of the wrong type!"
                return None
        else:
            print "calc get_job no existing job"
            return None
    
    def set_job(self,job):
        """
        Set the job that is currently being edited by this calcualtion
        and also set it for the calcultion

        """
        self.calc.set_job( job )

    def create_job(self):
        """
        Create a job - we use the create_job method of the calc class
        to create the job and then update it with any defaults

        """

        job = self.calc.create_job()
        if not job:
            print "calced create_job no job!"
            return

        return job


    def open_jobsub_editor(self):
        """Fire up the appropriate widget to configure the job depending on
           whether we are using RMCS, Globus, Nordugrid..."""

        job = self.get_job()
        if not job:
            print "open_jobsub_editor got no job"
            try:
                job = self.create_job()
            except Exception,e:
                self.Error("Job submission editor - error creating job!\n%s" % e )
                return

        if not job:
            self.Error("Job submission editor - error creating job: no job returned!\n%s")
            return

        # Determine which editor we are using
        jobtype = job.jobtype

        if self.jobsub_editor:
            edtype = self.jobsub_editor.jobtype
            if edtype == jobtype:
                print "using old job editor"
                self.jobsub_editor.show()
                return
            else:
                # Should we ask here first?
                self.jobsub_editor.destroy()

        # Creating a new editor
        #print "creating new editor"

        # See if we have a hostlist from this session
        if self.calc.job_dict.has_key('hostlist'):
            hostlist = self.calc.job_dict['hostlist']
        else:
            hostlist=[]
            
        if jobtype == jobmanager.job.LOCALHOST:
            self.jobsub_editor = LocalJobEditor(
                                            self.interior(),
                                            job,
                                            onkill=self.kill_jobsub_editor,
                                            update_cmd=self.update_job_dict,
                                            )
        elif jobtype == 'RMCS':
            self.jobsub_editor = RMCSEditor(
                                        self.interior(),
                                        job,
                                        onkill=self.kill_jobsub_editor,
                                        update_cmd=self.update_job_dict,
                                        )
        elif jobtype == 'Nordugrid':
            self.jobsub_editor = NordugridEditor(
                                             self.interior(),
                                             job,
                                             onkill=self.kill_jobsub_editor,
                                             update_cmd=self.update_job_dict,
                                             hostlist=hostlist,
                                             )
        elif jobtype == 'Globus':
            self.jobsub_editor = GlobusEditor(
                                         self.interior(),
                                         job,
                                         onkill=self.kill_jobsub_editor,
                                         update_cmd=self.update_job_dict,
                                         hostlist=hostlist,
                                         debug=None,
                                         )
        else:
            self.Error("calced - unrecognised job editor: %s" % jobtype)
            return None

        self.jobsub_editor.show()

    def kill_jobsub_editor(self):
        """Set the job_editoritor variable to None"""
        self.jobsub_editor = None
        
        
#     def chdir_cmd(self,event):
#         """
#         Command that is passed to the jobeditor and is invoked each time the directory
#         is changed with the change directory tool  
#         """

#         # This is a bit mucky because the FileTool can call this method
#         # either as one of the events that has been bound to the Tkinter.Entry
#         # field (in which case we get a Tkinter.Event) or when the 'Browse' tool
#         # was used (in which case we get a string).
#         print "event is ",event
#         print "type(event) ",type(event)
#         etype = type(event)
#         if etype is InstanceType:
#             print "got instance"
#             directory = event.widget.get()
#         else:
#             print "got string"
#             directory = event

#         self.calc.set_parameter('directory',directory)
#         print "chrdir_cmd set directory to ",directory


    def update_job_dict( self, job=None, hostlist=None ):
        """
        Job editor has saved changes to the job parameters so we
        update the dictionary 
        """

        print "calced updating job dict ..."
        if job:
            jobtype = job.jobtype
            parameters = job.get_parameters()
            # Need to use a copy or else any changes when running the job
            # come back to haunt us
            self.calc.job_dict[jobtype] = copy.copy(parameters)

        if hostlist:
            self.calc.job_dict['hostlist'] = hostlist
        
    #------------- messages -----------------------------

    def Info(self,txt):
        dialog = self.msg_dialog
        dialog.configure(message_text=txt)
        dialog.component('icon').configure(bitmap='info')
        dialog.configure(title="Calculation Information")
        dialog.activate()

    def Error(self,txt):
        dialog = self.msg_dialog
        dialog.configure(message_text=txt)
        dialog.configure(title='Calculation Error')
        dialog.component('icon').configure(bitmap='error')
        dialog.activate()
        
    def Query(self,txt):
        dialog = self.query_dialog
        dialog.configure(message_text=txt)
        dialog.configure(title='Calculation Query')
        dialog.activate( geometry='centerscreenalways' )
        # see __QueryResult for self.dialogresult
        return self.dialogresult
        

if __name__ == "__main__":

    import Tkinter
    from gamessuk import GAMESSUKCalc,GAMESSUKCalcEd
    from objects.zmatrix import Zmatrix,ZAtom
    import jobmanager
    model = Zmatrix()
    atom = ZAtom()
    atom.symbol = 'C'
    atom.name = 'C0'
    model.insert_atom(0,atom)
    atom = ZAtom()
    atom.symbol = 'P'
    atom.name = 'P'
    atom.coord = [ 1.,0.,0. ]
    model.insert_atom(1,atom)

    root=Tkinter.Tk()
    calc = GAMESSUKCalc()

    for x in calc.__dict__.keys():
        print x
        try:
            dicts = calc.__dict__[x].keys()
        except AttributeError:
            dicts = []
        for y in dicts:
            print '>>',y
            try:
                dicts2 = x.__dict__[y].keys()
            except AttributeError:
                dicts2 = []
            for z in dicts2:
                print '>>',z

                try:
                    dicts3 = y.__dict__[z].keys()
                except AttributeError:
                    dicts3 = []
                for zz in dicts3:
                    print '>>',zz

    fobj = open("tmp.x",'w')
    p = cPickle.Pickler(fobj)
    p.dump(calc)
    fobj.close()

    calc.set_input('mol_obj',model)
    jm = jobmanager.JobManager()
    je = jobmanager.jobeditor.JobEditor(root,jm)
    vt = GAMESSUKCalcEd(root,calc,None,job_editor=je)
    root.mainloop()
