import Tkinter
import Pmw
import tkFileDialog
import viewer.initialisetk
import os,getpass

if __name__ != "__main__":
    from viewer.rc_vars import rc_vars


class EntryPair( Tkinter.Frame ):
    """ A widget with two Pmw entry frames that has a singled
        getvalue method returning a list
    """
    def __init__(self,root):
        Tkinter.Frame.__init__( self, root )
        self.LayoutWidgets()
        
    def LayoutWidgets(self):
        self.entry1 = Pmw.EntryField( self )
        self.entry1.pack(side='left')
        self.entry2 = Pmw.EntryField( self )
        self.entry2.pack(side='left')

    def get(self):
        """Alias for getvalue"""
        return self.getvalue()
        
    def getvalue(self):
        v1 = self.entry1.getvalue()
        v2 = self.entry2.getvalue()
        return [v1,v2]
    
    def setvalue(self, entry):
        etype = type(entry)
        print "pair widget setting value etype:%s entry:%s" % (etype,entry)
        if etype == list:
            if len(entry) != 2:
                print "ERROR! JobSubEditor EntryPaire setvalue len(list) != 2!"
                print "entry is: %s" % entry
            # Need to set Nones to an empty string or else tk doesn't get enough
            # arguments when it tries to display with widget
            if entry[0] == None:
                entry[0] = ''
            if entry[1] == None:
                entry[1] = ''
            v1 = self.entry1.setentry(entry[0])
            v2 = self.entry2.setentry(entry[1])
        elif etype == str or etype == float or etype == int :
            v1 = self.entry1.setentry(entry)
            v2 = self.entry2.setentry(entry)
        else:
            v1 = self.entry1.setentry('')
            v2 = self.entry2.setentry('')

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


    def __init__(self, root,job,**kw):


        self.debug = None
        self.onkill = None
        self.job = job
        #self.calc = None
        title = None

        # Check the keywords dictionary
        if kw.has_key('title'):
            title = kw['title']
        else:
            title = self.jobtype+ ' JobEditor'
            
        if kw.has_key('onkill'):
            self.onkill = kw['onkill']
        if kw.has_key('debug'):
            self.debug = kw['debug']
        #if kw.has_key('calc'):
        #    self.calc = kw['calc']

        viewer.initialisetk.initialiseTk(root)

        # Initialise base class (after defining options).
        Pmw.MegaToplevel.__init__( self, root, title=title )
        
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
                         # These need to be set to default values in the classes that inherit
                         # form this one

        # RSL parameters
        
        #self.rsl_operations = [ '=','<','>','>=','<=' ]
        #self.rsl_operations = ( '=' )

        # Dictionary mapping variable name to the type of the variable
        self.rslVariables = {}
        self.rslVariables['jobName']=str
        self.rslVariables['cpuTime']=str
        self.rslVariables['wallTime']=str
        self.rslVariables['gridTime']=str
        self.rslVariables['memory']=int
        self.rslVariables['disk']=int
        self.rslVariables['architechture']=str
        self.rslVariables['runTimeEnvironment']=str
        self.rslVariables['opSys']=str
        self.rslVariables['executable']=str
        self.rslVariables['arguments']=str
        self.rslVariables['environment']='entrypair'
        self.selected_RSL = {} # dict of name : ( op,value ) - value could be a list
        self.currentRSL = 'NoneSelected' # Bit of a hack so we know the last selected RSL
        self.chooseRSLWidget = None
        self.rslValueWidget = None
        self.rslActive = None # To indicate if the RSL widgets are being used


    def GetJob(self):
        """Return the job supplied to this editor"""
        if self.job:
            return self.job
        else:
            print "jobSubEd - no job to return!"
            return None

    def GetInitialValues(self):
        """ Set self.values and self.selected_RSL to those specified in any calculation
            object we may have been passed and then overwrite any with those that are
            set in the rc_vars dictionary.
        """

        if self.job:
            jobdict = self.job.job_parameters
            for key,value in jobdict.iteritems():
                if value:
                    if self.values.has_key( key ):
                        self.values[key] = value
                        if self.debug:
                            print "GetInitialValues job setting: %s : %s" % (key,value)
                    if self.rslActive:
                        if self.rslVariables.has_key( key ):
                            if key == 'environment':
                                self._AddDictAsPair( key, value)
                            else:
                                self.selected_RSL[key] = ('=',value) # Currently only assume = op

        # Now update any variables that are set in the rc_vars
        global rc_vars
        for key,value in rc_vars.iteritems():
            if self.debug:
                print "rc_vars: %s : %s" %(key,value)
            if value:
                if self.values.has_key( key ):
                    self.values[key] = value
                    if self.debug:
                        print "GetInitialValues rc_vars setting: %s : %s" % (key,value)
                if self.rslActive:
                    if self.rslVariables.has_key( key ):
                        if key == 'environment':
                            self._AddDictAsPair( key, value)
                        else:
                            self.selected_RSL[key] = ('=',value) # Currently only assume = op

    def _AddDictAsPair(self,key,value):
        """ Take a dictionary we have been given and split it up into separate variables
            suitable for displaying with an entrypair widget
        """
        i=0
        for var,val in value.iteritems():
            if i==0:
                self.selected_RSL[key] = ('=',[var,val])
            else:
                self.selected_RSL[key+str(i)] = ('=',[var,val])
            i+=1

    def UpdateWidgets(self):
        """Set all the widgets to the value in self.values
        """
        for key,value in self.values.iteritems():
            if self.debug:
                print "Setting values for %s : %s" % (key,value)
            try:
                # Need to convert any None's to empty strings
                if value == None:
                    value = ''
                self.setValue[key]( value )
            except KeyError:
                pass
            
        if self.rslActive:
            selected = self.selected_RSL.keys()[0]
            self._UpdateRSLWidgets( selected )
            

    def LayoutRSLWidget(self):
        """ Lay out the RSL widgets"""

        self.rslActive = 1
        
        # Create the widgets to edit the list of machines
        RSLFrame = Pmw.Group( self.interior(), tag_text='RSL parameters' )
        RSLFrame.pack(fill='both',expand=1)
        self.selectedRSLWidget = Pmw.OptionMenu(
            RSLFrame.interior(),
            #items=self.selected_RSL.keys(),
            items=['NoneSelected'],
            command=self._ChangeSelectedRSL
            )
        self.selectedRSLWidget.pack(side='left')

#         Below if we need to support different operation types
#         self.RSLOpWidget = Pmw.OptionMenu(
#             RSLFrame.interior(),
#             items=self.rsl_operations,
#             initialitem = '='
#             #command = self._UpdateRSLOpWidget
#             )
#         self.RSLOpWidget.pack( side='left' )

        oplabel = Tkinter.Label( RSLFrame.interior(), text=' = ')
        oplabel.pack( side='left' )
        
        self.RSLValueFrame = Tkinter.Frame( RSLFrame.interior() )
        self.RSLValueFrame.pack( side = 'left' )
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
                value =0.0 # jens change
                )
        # See above for EntryPair class
        self.RSLPairSelect = EntryPair( self.RSLValueFrame )
        
        self.RSLTextSelect = Pmw.EntryField( self.RSLValueFrame,
                                             labelpos=None,
                                             entry_width=20 )
        #self.RSLTextSelect.pack(side='left')

        
        self.rslValueWidget =  self.RSLTextSelect
        
        delRSLButton = Tkinter.Button( RSLFrame.interior(),
                                       text = 'Delete',
                                       command = self._DelRSL)
        delRSLButton.pack(side='left')
        addRSLButton = Tkinter.Button( RSLFrame.interior(),
                                        text = 'Add',
                                        command = self._AddRSL)
        addRSLButton.pack(side='left')

    def _AddRSL(self):
        """Add an RSL to the list"""
        # Pop up widget with list of valid rsls and get the selection
        # Look up the selection in rslVariables and determine it's type
        # prepend the variable to selected_rsl
        # hide the previous value widget and update selected rsl with it's value
        # pack the new value widget depend on the type of rsl variable selected

        self._ChooseRSL()
        pass

    def _ChooseRSL(self):
        """ Pop up a list of RSLs that the user can select and get them to select one
        """

        if not self.chooseRSLWidget:
            # REM configure so window manager doesn't detroy!
            self.chooseRSLWidget = Pmw.SelectionDialog( self.interior(),
                                                        title = 'Add an RSL',
                                                        buttons = ('Ok','Cancel'),
                                                        defaultbutton = 'Ok',
                                                        scrolledlist_items = self.rslVariables.keys(),
                                                        command=self._selectRSL
                                                        )
            self.chooseRSLWidget.pack()
        else:
            self.chooseRSLWidget.show()
        
    def _selectRSL(self,button_press):
        """Command invoked when the user selects an RSL
           Make sure there is only one selection and pass this to add_rsl
           then destroy the widget.
        """
        selected = self.chooseRSLWidget.getcurselection()
        self.chooseRSLWidget.withdraw()

        if button_press == 'Ok':
            if len(selected) > 0:
                self._SaveCurrentRSL()
                self._AddSelectedRSL( selected[0] )


    def _AddSelectedRSL( self, selected):
        """ Add the selected RSL"""

        #print "AddSelectedRSL"

        vtype = self.rslVariables[selected]
        if vtype == str:
            value = ''
        elif vtype == int or vtype == float:
            value = 0
        elif vtype == 'entrypair':
            value = ['','']
        else:
            print "add_rsl - bad type"

        # Need to deal with multiple environment variables
        if selected == 'environment' and self.selected_RSL.has_key( selected ):
            for i in range(10):
                selected =  'environment'+str(i+1)
                if not self.selected_RSL.has_key( selected ):
                    break
            self.selected_RSL[selected] = ( None, value )
        else:
            self.selected_RSL[selected] = ( None, value )

        if 'NoneSelected' in self.selected_RSL.keys():
            del self.selected_RSL['NoneSelected']
            
        self._UpdateRSLWidgets( selected )
        

    def _ChangeSelectedRSL(self,value):
        """The user has changes the currently selected RSL"""

        self._SaveCurrentRSL()
        self._UpdateRSLWidgets( value )

#     def _UpdateRSLOpWidget(self,value):
#         """ Do nowt, just save the current state
#         """
#         self._SaveCurrentRSL()

    def _SaveCurrentRSL(self, name=None):
        """ Save the current state of the RSL list"""

        #print "SaveCurrentValues: ",name
        #rsl_name = self.selectedRSLWidget.getvalue()
        rsl_name = self.currentRSL
            
        #rsl_op = self.RSLOpWidget.getvalue()
        rsl_op = '='
        try:
            rsl_value = self.rslValueWidget.entryfield.getvalue()
        except AttributeError,e:
                try:
                    rsl_value = self.rslValueWidget.get()
                except Exception,e:
                    print "save_old_rsl widget got unhandled exception ",e
                    
        if len(rsl_value) == 0:
            rsl_value = None

        #print "SaveCurrentValues got: %s %s %s" % ( rsl_name, rsl_op, rsl_value )
        self.selected_RSL[rsl_name] = ( rsl_op, rsl_value )
        

    def _UpdateRSLWidgets( self, selected ):
        """ Display the correct widgts for the selected rsl """


        #print "UpdateRSLWidgets: ",selected
        
        self.selectedRSLWidget.setitems( self.selected_RSL.keys() )
        self.selectedRSLWidget.setvalue(selected)
        self.currentRSL = selected
        
        if selected == 'NoneSelected':
            self.rslValueWidget.forget()
            return

        # Update the op widget
        #op = self.selected_RSL[selected][0]
        #if not op:
        #    op = '='
        #self.RSLOpWidget.setvalue(op)

        # update the value widget
        value = self.selected_RSL[selected][1]
        self.rslValueWidget.forget()

        # Need to deal with numbered variables - this might need more work...
        #rsl_type = self.rslVariables[selected]
        rsl_type = self.rslVariables[selected.rstrip('0123456789')]
        if rsl_type == str:
            self.rslValueWidget = self.RSLTextSelect
            if not value:
                self.rslValueWidget.setvalue( '' )
        elif rsl_type == int:
            self.rslValueWidget = self.RSLIntegerSelect
            if not value:
                self.rslValueWidget.setvalue( 0 )
        elif rsl_type == float:
            self.rslValueWidget = self.RSLFloatSelect
            if not value:
                self.rslValueWidget.setvalue( 0 )
        elif rsl_type == 'entrypair':
            self.rslValueWidget = self.RSLPairSelect
            if not value:
                self.rslValueWidget.setvalue( ['',''] )

        if value:
            self.rslValueWidget.setvalue( value )
            
        self.rslValueWidget.pack(side='left')

    def _DelRSL(self):
        """Delete the currently selected RSL from the list"""
        
        to_delete = self.selectedRSLWidget.getvalue()
        if len( self.selected_RSL ) == 0:
            selected = 'NoneSelected'
        elif len( self.selected_RSL ) == 1:
            #current = self.selected_RSL.keys()[0]
            #del self.selected_RSL[ current ]
            del self.selected_RSL[ to_delete ]
            selected = 'NoneSelected'
        else:
            del self.selected_RSL[ to_delete ]
            selected = self.selected_RSL.keys()[0]
            
        self._UpdateRSLWidgets( selected )

    def GetRSLValues(self):
        """Update self.values with all the values from the RSL widgets"""

        envdict = {}
        for key,vlist in self.selected_RSL.iteritems():
            value = vlist[1]
            tmp = key.rstrip('0123456789')
            if tmp == 'environment':
                #print "got environment"
                envdict[value[0]] = value[1]
            else:
                #key = 'rsl_'+key
                self.values[key] = value

        if len(envdict):
            #self.values['rsl_environment'] = envdict
            self.values['environment'] = envdict


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
            
        # RSL values need to be handled differently
        self.GetRSLValues()

        #print "self.values is ",self.values
        return self.values

    def LayoutQuitButtons(self):
        """ Layout the Buttons to quit"""
        # Buttons to save or quit
        quitAndSaveButton = Tkinter.Button(self.interior(),
                                text="Quit and Save",
                                command=self.QuitAndSave)
        quitAndSaveButton.pack(side='left')
        quitAndSaveAsDefaultButton = Tkinter.Button(self.interior(),
                                text="Quit and Save as Defaults",
                                command=lambda s=self: s.QuitAndSave(default=1) )
        quitAndSaveAsDefaultButton.pack(side='left')
        quitNoSaveButton = Tkinter.Button(self.interior(),
                                text="Quit do not save",
                                command=self.QuitNoSave)
        quitNoSaveButton.pack(side='left')

    def QuitNoSave(self):
        """It's all gone Pete Tong so we do the honourable thing..."""
        self.Quit()

    def QuitAndSave(self,default=None):
        """Update the rc_vars or the supplied calculation with the new values
           If default keyword is supplied update the rc_vars with the values we are saving
        """

        if self.rslActive:
            self._SaveCurrentRSL()

        if self.job:
            jobdict = self.GetValueDict()
            for key,value in jobdict.iteritems():
                if type(value) == str and len(value) == 0: # Need to convert empty strings to null
                    value = None

                if key in self.job.job_parameters.keys():
                    self.job.job_parameters[key] = value
                    if self.debug:
                        print "QuitAndSave setting: %s : %s" % (key,value)

        #if self.calc:
        #    self.calc.job = self.job

        if default:
            global rc_vars
            for key,value in self.GetValueDict().iteritems():
                rc_vars[key] = value
                if self.debug:
                    print "QuitAndSave updating rc_vars with %s : %s" % (key,rc_vars[key])
                
        self.Quit()

    def Quit(self):
        """Destroy the widget and run any cleanup code we may have been passed"""
        self.destroy()
        if self.onkill:
            self.onkill()

        if self.debug:
            if self.job:
                print "jobsubed parameters"
                print self.job.job_parameters
            
    def __str__(self):
       """The string to return when we are asked what we are"""
       if self.title:
           return self.title
       else:
           return 'JobSubmissionEditor'

###################################################################################################
###################################################################################################

    def LayoutMachListWidget(self):
        """ Lay out the machine list widget"""

        # Create the widgets to edit the list of machines
        self.values['machine_list'] = [] # set default value here
        self.values['hosts'] = [] # set default value here
        machListFrame = Pmw.Group( self.interior(), tag_text='Machines' )
        machListFrame.pack(fill='both',expand=1)
        self.machList = Pmw.ScrolledListBox(
            machListFrame.interior(),
            listbox_selectmode='extended',
            items=self.values['machine_list']
            )
        self.getValue['hosts'] = lambda s=self: s.machList.getvalue()
        self.setValue['hosts'] = self.machList.setvalue
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
        self.values['count'] = 1 # set default value here
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

    def LayoutExecutableWidget(self):
        """ Lay out the widget to select the executable"""
        print "Laid out executable"
        self.executableWidget = Pmw.EntryField( self.interior(),
                                            labelpos = 'w',
                                            label_text = 'Executable Name:',
                                            validate = None
                                            )
        self.executableWidget.pack(side='top')
        self.values['executable'] = None
        self.getValue['executable'] = lambda s=self: s.executableWidget.getvalue()
        self.setValue['executable'] = self.executableWidget.setentry

        
    def LayoutDirectoryWidget(self):
        """ Lay out the widget to select the directory on the remote machine"""
        print "Laid out directory"
        self.remoteDirWidget = Pmw.EntryField( self.interior(),
                                            labelpos = 'w',
                                            label_text = 'Remote Directory:',
                                            entry_width = '30',
                                            validate = None
                                            )
        self.remoteDirWidget.pack(side='top')
        self.values['directory'] = None
        self.getValue['directory'] = lambda s=self: s.remoteDirWidget.getvalue()
        self.setValue['directory'] = self.remoteDirWidget.setentry
       
    def LayoutJobmanagerWidget(self):
        """ Lay out the widget to select the directory on the remote machine"""
        print "Laid out jobmanager"
        self.jobmanagerWidget = Pmw.EntryField( self.interior(),
                                            labelpos = 'w',
                                            label_text = 'Globus Jobmanager:',
                                            entry_width = '30',
                                            validate = None
                                            )
        self.jobmanagerWidget.pack(side='top')
        self.values['jobmanager'] = None
        self.getValue['jobmanager'] = lambda s=self: s.jobmanagerWidget.getvalue()
        self.setValue['jobmanager'] = self.jobmanagerWidget.setentry


class GlobusEditor(JobSubEditor):

    """ A widget to edit Growl Jobs
    """

    def __init__(self, root,job,**kw):

        # Set up the defaults
        self.jobtype = 'Globus'
        self.debug=1
        
        # Initialse everything in the base class
        JobSubEditor.__init__(self,root,job,**kw)

        self.LayoutWidgets()
        self.GetInitialValues()
        self.UpdateWidgets()

    def LayoutWidgets(self):
        """ Create and lay out all of the widgets"""

        # These are found in the base class JobSubEditor (see jobsubEditor.py)
        self.LayoutMachListWidget()
        self.LayoutNprocWidget()
        self.LayoutExecutableWidget()
        self.LayoutDirectoryWidget()
        self.LayoutJobmanagerWidget()
        self.LayoutQuitButtons()

        #Pmw.alignlabels( [self.executableWidget, self.directoryWidget] )

class NordugridEditor(JobSubEditor):

    """ A widget to edit Nordugrid Jobs
    """

    def __init__(self, root,job,**kw):

        # Set up the defaults
        self.jobtype = 'Nordugrid'
        if not kw.has_key('title'):
            kw['title'] = self.jobtype+ ' JobEditor'

        # Initialse everything in the base class
        JobSubEditor.__init__(self,root,job,**kw)

        self.LayoutWidgets()
        self.GetInitialValues()
        self.UpdateWidgets()

    def LayoutWidgets(self):
        """ Create and lay out all of the widgets"""

        # These are found in the base class JobSubEditor (see jobsubEditor.py)
        #self.LayoutMachListWidget()
        self.LayoutNprocWidget()
        self.LayoutRSLWidget()
        self.LayoutQuitButtons()


class RMCSEditor(JobSubEditor):

    """ A widget to hold all the symmetry tools.
    """

    def __init__(self, root,job,**kw):

        # Set up the defaults
        self.jobtype = 'RMCS'
        title = self.jobtype+ ' JobEditor'
        
        # Initialse everything in the base class
        JobSubEditor.__init__(self,root,job,**kw)

        
        self.values['srb_config_file'] = os.path.expanduser('~/srb.cfg')
        self.values['srb_input_dir'] = 'SET ME'
        self.values['srb_executable_dir'] = 'SET ME'
        self.values['srb_executable'] = 'SET ME'
        self.values['srb_output_dir'] = 'SET ME'
        self.values['rmcs_user'] = getpass.getuser()
        self.values['rmcs_password'] = ''
        self.values['myproxy_user'] = getpass.getuser()
        self.values['myproxy_password'] = ''

        self.LayoutWidgets()
        self.GetInitialValues()
        self.UpdateWidgets()

    def LayoutWidgets(self):
        """ Create and lay out all of the widgets"""
        
        # These are found in the base class JobSubEditor (see jobsubEditor.py)
        self.LayoutMachListWidget()
        self.LayoutNprocWidget()

        # The SRB options
        srbFrame = Pmw.Group( self.interior(), tag_text='SRB Options' )
        srbFrame.pack(fill='both',expand=1)

        srbFileFrame = Tkinter.Frame( srbFrame.interior() )
        srbFileFrame.pack( side='top' )
        self.srbConfigFile = Pmw.EntryField( srbFileFrame,
                                        labelpos = 'w',
                                        label_text = 'SRB config file'
                                        )
        self.getValue['srb_config_file'] = lambda s=self: s.srbConfigFile.getvalue()
        self.setValue['srb_config_file'] = self.srbConfigFile.setentry
        self.srbConfigFile.pack(side="left")

        srbConfFileBrowseButton = Tkinter.Button(srbFileFrame,
                                           text="Browse...",
                                           command=self.SrbBrowseDir)
        srbConfFileBrowseButton.pack(side="left", padx=10)

        self.srbInputDir = Pmw.EntryField( srbFrame.interior(),
                                            labelpos = 'w',
                                            label_text = 'SRB Input Directory:',
                                            validate = None
                                            )
        self.getValue['srb_input_dir'] = lambda s=self: s.srbInputDir.getvalue()
        self.setValue['srb_input_dir'] = self.srbInputDir.setentry
        self.srbInputDir.pack(side='top')
        self.srbOutputDir = Pmw.EntryField( srbFrame.interior(),
                                            labelpos = 'w',
                                            label_text = 'SRB Output Directory:',
                                            validate = None
                                            )
        self.getValue['srb_output_dir'] = lambda s=self: s.srbOutputDir.getvalue()
        self.setValue['srb_output_dir'] = self.srbOutputDir.setentry
        self.srbOutputDir.pack(side='top')
        self.srbExecutableDir = Pmw.EntryField( srbFrame.interior(),
                                            labelpos = 'w',
                                            label_text = 'SRB Executable Directory:',
                                            validate = None
                                            )
        self.getValue['srb_executable_dir'] = lambda s=self: s.srbExecutableDir.getvalue()
        self.setValue['srb_executable_dir'] = self.srbExecutableDir.setentry
        self.srbExecutableDir.pack(side='top')
        self.srbExecutable = Pmw.EntryField( srbFrame.interior(),
                                            labelpos = 'w',
                                            label_text = 'SRB Executable:',
                                            validate = None
                                            )
        self.srbExecutable.pack(side='top')
        self.getValue['srb_executable'] = lambda s=self: s.srbExecutable.getvalue()
        self.setValue['srb_executable'] = self.srbExecutable.setentry
        Pmw.alignlabels( [self.srbInputDir, self.srbOutputDir,
                          self.srbExecutableDir,self.srbExecutable] )


        # The RMCS options
        rmcsFrame = Pmw.Group( self.interior(), tag_text='RMCS Options' )
        rmcsFrame.pack(fill='both',expand=1)
        self.rmcsUser = Pmw.EntryField( rmcsFrame.interior(),
                                            labelpos = 'w',
                                            label_text = 'RMCS User',
                                            validate = None
                                            )
        self.getValue['rmcs_user'] = lambda s=self: s.rmcsUser.getvalue()
        self.setValue['rmcs_user'] = self.rmcsUser.setentry
        self.rmcsUser.pack(side='top')
        self.rmcsPassword = Pmw.EntryField( rmcsFrame.interior(),
                                            labelpos = 'w',
                                            label_text = 'RMCS Password',
                                            validate = None
                                            )
        self.getValue['rmcs_password'] = lambda s=self: s.rmcsPassword.getvalue()
        self.setValue['rmcs_password'] = self.rmcsPassword.setentry
        self.rmcsPassword.configure( entry_show = '*')
        self.rmcsPassword.pack(side='top')
        Pmw.alignlabels( [self.rmcsUser, self.rmcsPassword] )

        # The myProxy Options
        myProxyFrame = Pmw.Group( self.interior(), tag_text='myProxy Options' )
        myProxyFrame.pack(fill='both',expand=1)
        self.myProxyUser = Pmw.EntryField( myProxyFrame.interior(),
                                            labelpos = 'w',
                                            label_text = 'myProxy User',
                                            validate = None
                                            )
        self.getValue['myproxy_user'] = lambda s=self: s.myProxyUser.getvalue()
        self.setValue['myproxy_user'] = self.myProxyUser.setentry
        self.myProxyUser.pack(side='top')
        self.myProxyPassword = Pmw.EntryField( myProxyFrame.interior(),
                                            labelpos = 'w',
                                            label_text = 'myProxy Password',
                                            validate = None
                                            )
        self.myProxyPassword.configure( entry_show = '*')
        self.getValue['myproxy_password'] = lambda s=self: s.myProxyPassword.getvalue()
        self.setValue['myproxy_password'] = self.myProxyPassword.setentry
        self.myProxyPassword.pack(side='top')
        Pmw.alignlabels( [self.myProxyUser, self.myProxyPassword] )

        self.LayoutQuitButtons()


    def SrbBrowseDir(self):
        # askdirectory() cant create new directories so use asksaveasfilename is used instead
        # and the filename  is discarded - also fixes problem with no askdirectory in Python2.1
        oldFile = self.srbConfigFile.get()
        dummyfile='srb.cfg'
        #path=tkFileDialog.asksaveasfilename(initialfile=dummyfile, initialdir=olddir)
        path=tkFileDialog.asksaveasfilename(initialfile=dummyfile)
        if len(path) == 0: #
            self.srbConfigFile.setvalue(oldFile)
        else:
            self.srbConfigFile.setvalue(path)

       
if __name__ == "__main__":
    rc_vars = {} # Dictionary of the values held by this widget at any point
    rc_vars['machine_list'] = ['computers','are','evil']
    rc_vars['count'] = '4'

    class Junk:
        def has_parameter(self,par):
            return True
        def set_parameter(self,par,val):
            return True
        def get_parameter(self,par):
            return {'memory' : '1234',
                    'environment' : {'ed3':'file.ed3','ed2':'file.ed2'},
                    'gridTime':'444'}
    job = Junk()
    
    root=Tkinter.Tk()
    ed = JobSubEditor( root, job )
    ed.GetInitialValues()
    ed.LayoutMachListWidget()
    ed.LayoutNprocWidget()
    ed.LayoutRSLWidget()
    ed.LayoutQuitButtons()
    ed.UpdateWidgets()
    test = Tkinter.Button( ed.interior(),
                           text = 'Test',
                           command = ed.GetValueDict)
    test.pack()
    root.mainloop()
