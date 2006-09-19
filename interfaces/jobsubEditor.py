import Tkinter
import Pmw
import tkFileDialog
import viewer.initialisetk
import os,getpass

if __name__ != "__main__":
    from viewer.rc_vars import rc_vars

class JobSubEditor(Pmw.MegaToplevel):

    """ A baseclass widget to hold the Job Submission tools.
        The widget has a self.values dictionary that holds all of the
        parameters that are editable by this widget. The GetInitialValues
        method queries the rc_vars to get any initial values that have been
        set, otherwise, the init method is supposed to set any defaults.

        There are two dictionaries getValue and setValue. These are keyed by
        the job parameters and map them to functions that either return the current
        value of the widget or set it when given a single argument.

        The SetInitialValues and GetWidgets methods trundle though these to get or
        set all of the relevant values

        A number of the methods to layout tools that are expected to be used in other
        editors are found in this class. These include:
        
        LayoutMachListWidget
        LayoutNprocWidget
        
    """

    frameWidth       = 300
    frameHeight      = 200


    def __init__(self, root,**kw):


        self.debug = None
        self.title = None
        self.onkill = None

        # Check the keywords dictionary
        if kw.has_key('title'):
            self.title = kw['title']
        if kw.has_key('onkill'):
            self.onkill = kw['onkill']
        if kw.has_key('debug'):
            self.debug = 1

        viewer.initialisetk.initialiseTk(root)

        # Initialise base class (after defining options).
        Pmw.MegaToplevel.__init__( self, root, title=self.title )
        
        # Ensure that when the user kills us with the window manager we behave as expected
        self.userdeletefunc( lambda s=self: s.Quit() )
        #self.usermodaldeletefunc( func = self.withdraw )

        #try and get the thing to be a decent size
        #self.interior( height = self.frameWidth, width = self.frameWidth )
        #self.component('hull').configure( height = self.frameWidth, width = self.frameWidth )

        # Get the balloon help from the main widget
        if kw.has_key('balloon'):
            self.balloon = kw['balloon']
        else:
            self.balloon = Pmw.Balloon(self.interior())

        self.getValue = {} # maps the name of the variable to the function to call to query
                           # the widget and return its value
        self.setValue = {} # maps the name of a variable to a function that sets the widget
                           # to the desired value
        
        self.values = {} # Dictionary of the values held by this widget at any point
        self.values['machine_list'] = []
        self.values['count'] = 1

        # RSL parameters
        self.rsl_operations = [ '=','<','>','>=','<=' ]
        self.rsl_variables = []
        self.rsl_variables.append(['cpuTime',str])
        self.rsl_variables.append(['wallTime',str])
        self.rsl_variables.append(['architechture',str])
        self.rsl_variables.append(['opSys',str])

    def GetInitialValues(self):
        """Query the rc_vars dictionary to get the initial values to set self.values with
        """        
        global rc_vars
        for key,value in rc_vars.iteritems():
            #print "rc_vars: %s : %s" %(key,value)
            if self.values.has_key( key ):
                self.values[key] = value
                #print "GetInitialValues Setting %s to %s" %(key,value)

    def UpdateWidgets(self):
        """Set all the widgets to the value in self.values
        """
        for key,value in self.values.iteritems():
            #print "Setting values for %s : %s" % (key,value)
            self.setValue[key]( value )


    def LayoutResourceDefWidget(self):
         """ Layout the widget the allows the user to choose a bunch of resources"""
         pass

    def LayoutRSLWidget(self):
        """ Lay out the RSL widgets"""
        
        # Create the widgets to edit the list of machines
        RSLFrame = Pmw.Group( self.interior(), tag_text='RSL parameters' )
        RSLFrame.pack(fill='both',expand=1)
        self.selectedRSLList = Pmw.OptionMenu(
            RSLFrame.interior(),
            items=['machinetime']
            )
        #self.getValue[''] = lambda s=self: s.machList.get()
        #self.setValue['machine_list'] = self.machList.setlist
        self.selectedRSLList.pack(side='left')
        self.RSLOpList = Pmw.OptionMenu(
            RSLFrame.interior(),
            items=self.rsl_operations
            )
        self.RSLOpList.pack( side='left' )
        self.RSLValueFrame = Tkinter.Frame( RSLFrame.interior() )
        self.RSLValueFrame.pack( side = 'left' )
        self.RSLBoolSelect = Tkinter.Checkbutton( self.RSLValueFrame )
        self.RSLIntegerSelect = Pmw.Counter(
            self.RSLValueFrame, 
            labelpos = None,
            increment = 1,
            entryfield_entry_width = 4,
            entryfield_value = 0, # jens change
            )
        # entryfield_validate = v)
        self.RSLFloatSelect = Pmw.EntryField(
                self.RSLValueFrame,
                labelpos = None,
                value =0.34 # jens change
                )
        self.RSLTextSelect = Tkinter.Entry( self.RSLValueFrame,
                                            width=20 )
        self.RSLTextSelect.pack(side='left')
        
        addRSLButton = Tkinter.Button( RSLFrame.interior(),
                                        text = 'Add',
                                        command = self.AddRSL)
        addRSLButton.pack(side='left')
        delRSLButton = Tkinter.Button( RSLFrame.interior(),
                                       text = 'Delete',
                                       command = self.DelRSL)
        delRSLButton.pack(side='left')

    def AddRSL(self):
        """Add an RSL to the list"""
        pass

    def DelRSL(self):
        """Delete the currently selected RSL from the list"""
        sel = self.selectedRSLList.get()
        print "DelRSL got ",sel
        
        pass

    def LayoutMachListWidget(self):
        """ Lay out the machine list widget"""
        
        # Create the widgets to edit the list of machines
        machListFrame = Pmw.Group( self.interior(), tag_text='Machines' )
        machListFrame.pack(fill='both',expand=1)
        self.machList = Pmw.ScrolledListBox(
            machListFrame.interior(),
            items=self.values['machine_list']
            )
        self.getValue['machine_list'] = lambda s=self: s.machList.get()
        self.setValue['machine_list'] = self.machList.setlist
        self.machList.pack(side='left')
        buttonFrame=Tkinter.Frame( machListFrame.interior() )
        buttonFrame.pack(side='left')
        addMachButton = Tkinter.Button( buttonFrame,
                                        text = 'Add',
                                        command = self.AddMachine)
        addMachButton.pack(side='left')
        #self.balloon.bind( addMachButton, 'Add a machine to the list. )
        delMachButton = Tkinter.Button( buttonFrame,
                                        text = 'Del',
                                        command = self.DelMachine)
        delMachButton.pack(side='left')
        self.machEntry = Tkinter.Entry( machListFrame.interior(),
                                        width=20)
        self.machEntry.pack(side='left')


    def LayoutNprocWidget(self):
        """ Layout the widget to set the number of processors"""
        self.nProc = Pmw.Counter( self.interior(),
                                  labelpos = 'w',
                                  label_text = 'Number of Processors:',
                                  entryfield_entry_width = 4,
                                  entryfield_validate = {'validator' : 'integer' ,
                                              'min' : 1 },
                                  increment = 1
                                  )
        self.getValue['count'] = lambda s=self: s.nProc.getvalue()
        self.setValue['count'] = self.nProc.setentry
        self.nProc.pack(side='top')

    def AddMachine(self):
        """ Add a machine to the list and update the list widget"""
        
        mach = self.machEntry.get()
        all = self.machList.get()
        machines = []  # need to convert to a list
        for m in all:
            machines.append( m )
        machines.append( mach )
        self.machList.setlist( machines )
        self.machEntry.delete(0,'end')

    def DelMachine(self):
        """ Remove a machine from the list and update the list widget
            This gets a bit silly as we are returned a tuple and need to
            use a list.
        """
        
        toRemove = self.machList.getcurselection()

        all = self.machList.get()
        machines = []  # need to convert to a list
        for m in all:
            machines.append( m )
        for mach in toRemove:
            machines.remove( mach )
        self.machList.setlist( machines )

    def GetMachines(self):
        """Return a list of the machines"""
        all = self.machList.get()
        machines = []  # need to convert to a list
        for m in all:
            machines.append( m )
        return machines


    def GetValueDict(self):
        """Return a dictionary with all of the values in it"""

        for key,func in self.getValue.iteritems():
            self.values[key]= func()
        #print self.values
        return self.values

    def Quit(self):
        """Destroy the widget and run any cleanup code we may have been passed"""
        self.destroy()
        if self.onkill:
            self.onkill()
            
    def __str__(self):
       """The string to return when we are asked what we are"""
       if self.title:
           return self.title
       else:
           return 'JobSubmissionEditor'

if __name__ == "__main__":
    
    rc_vars = {} # Dictionary of the values held by this widget at any point
    rc_vars['machine_list'] = ['computers','are','evil']
    rc_vars['count'] = '4'
    root=Tkinter.Tk()
    ed = JobSubEditor( root )
    ed.GetInitialValues()
    ed.LayoutMachListWidget()
    ed.LayoutNprocWidget()
    ed.LayoutRSLWidget()
    ed.UpdateWidgets()
    root.mainloop()
