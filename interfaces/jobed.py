"""
Role: takes a job as an argument and updates various parameters

"""

import Tkinter
import Pmw
import tkFileDialog
import viewer.initialisetk
import os,getpass
from viewer.paths import paths

from viewer.defaults import defaults

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
        #print "pair widget setting value etype:%s entry:%s" % (etype,entry)
        if etype == list:
            if len(entry) != 2:
                print "ERROR! JobEditor EntryPaire setvalue len(list) != 2!"
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

class JobEditor(Pmw.MegaToplevel):

    """ A baseclass widget to hold the Job Submission tools.
        The widget has a self.values dictionary that holds all of the
        parameters that are editable by this widget. The GetInitialValues
        method queries the defaults to get any initial values that have been
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


        self.root = root
        self.job = job

        # Check the keywords dictionary
        if kw.has_key('title'):
            title = kw['title']
        else:
            title = self.jobtype+ ' JobEditor'
            
        self.onkill = None
        if kw.has_key('onkill'):
            self.onkill = kw['onkill']
            
        self.debug = None
        if kw.has_key('debug'):
            self.debug = kw['debug']
            
        # Commands that may be passed in and invoked when particular widgets are used
        self.dir_cmd = None
        if kw.has_key('dir_cmd'): # see LayoutDirectoryWidget
            self.dir_cmd = kw['dir_cmd']
            
        self.exe_cmd = None
        if kw.has_key('exe_cmd'): # see LayoutExecutableWidget
            self.exe_cmd = kw['exe_cmd']

        self.update_cmd = None
        if kw.has_key('update_cmd'): # see LayoutExecutableWidget
            self.update_cmd = kw['update_cmd']

        self.hostlist = [] # To hold the list of hosts - this is different as it is not a
                           # job parameter but applies to all jobs of a particular class
        if kw.has_key('hostlist'):
            self.hostlist = kw['hostlist']

        viewer.initialisetk.initialiseTk(self.root)

        # Initialise base class (after defining options).
        Pmw.MegaToplevel.__init__( self, self.root, title=title )
        
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
                         # from this one


        #
        # Build the message dialogs
        #
        self.msg_dialog = Pmw.MessageDialog(self.root, 
                                            title = 'Information',
                                            iconpos='w',
                                            icon_bitmap='info',
                                            defaultbutton = 0)
        self.msg_dialog.withdraw()



    def GetInitialValues(self):
        """ Set self.values and self.RSLValues to those specified in any
            calculation object we may have been passed
        """
        
        if self.debug:
            print "GetIntialValues norsl"
            
        self.GetInitialParameters()

    def GetInitialParameters(self):
        """ Set self.values from the job we were given

        """

        if self.debug:
            print "_getInitialJobParameters"

        self.SetHostlistFromDefaults()
        
        jobdict = self.job.get_parameters()
        self.UpdateValues( jobdict )


    def UpdateValues(self,job_dict):
        """ We just call _UpdateValues here as we are overridden in the RSL
            class, but the latter is needed thre
        """

        self._UpdateValues(job_dict)
        
    def _UpdateValues(self,job_dict):
        """ Update self.values with the values from the supplied dictionary
            of parametesrs
        """
        
        for key,value in job_dict.iteritems():
            if self.values.has_key( key ):
                self.values[key] = value
                if self.debug:
                    print "_UpdateValues setting: %s : %s" % (key,value)

        #hostlist is different as this applies to all jobs of a given class
        self.UpdateHostlistWidget()
        
            
    def UpdateWidgets(self):
        """Set all the widgets to the value in self.values
           we just call _UpdateWidgets as this is used in other
           classes too
        """
        self._UpdateWidgets()
        
        
    def _UpdateWidgets(self):
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

    def UpdateParametersFromHost(self):
        """ Update the job parameters for the machine selected
            from the defaults dictionary
        """

        host = self.machList.getvalue()
        if len(host) != 1:
            print "UpdateParametersFromHost an only update vlaues for a single host!"
            return

        host = host[0]
        if self.debug:
            print "UpdateParametersFromHost: %s" % host
                
        #self.job.update_parameters( host=host )
        job_dict = self.job.get_parameters_from_defaults( host=host )
        if not job_dict:
            print "UpdateParmetersFromHost host no job_dict for host ",host
            return

        self.job.update_parameters( job_dict )
        job_dict = self.job.get_parameters()

        self.UpdateValues( job_dict )
        self.UpdateWidgets()
        
        
    def AddMachine(self):
        """ Add a machine to the list and update the list widget"""
        
        toadd = self.machEntry.get()
        self.hostlist.append( toadd )
        self.UpdateHostlistWidget()
        self.machEntry.delete(0,'end')

    def DelMachine(self):
        """ Remove a machine from the list and update the list widget
            This gets a bit silly as we are returned a tuple and need to
            use a list.
        """
        toRemove = self.machList.getcurselection()
        for mach in toRemove:
            self.hostlist.remove( mach )
        self.UpdateHostlistWidget()

    def SetHostlistFromDefaults(self):
        global defaults
        
        if self.debug:
            print "SetHostlistFromDefaults"

        # Get the values we use to key the dictionaries
        calctype = self.job.get_parameter('calctype')
        jobtype = self.job.jobtype

        maind = defaults.get_value('job_dict')
        if not maind:
            if self.debug: print "#### SetHostlistFromDefaults NO JOB DICT!"
            return

        if not maind.has_key( calctype ):
            if self.debug:
                print "#### SetHostListFromDefaults No ctype dictionary!"
            return
        
        calcd = maind[calctype]
        if not calcd.has_key( jobtype ):
            if self.debug: print "#### SetHostListFromDefaults no jtype dictionary!"
            return
        
        job_dict = calcd[jobtype]        
        if job_dict.has_key('hostlist'):
            hostlist = job_dict['hostlist']
        else:
            if self.debug: print "#### SetHostlistFromDefaults no hostlist!"

        # Now add any that may have been passed in when the job editor was created
        # (from the calculation editor - this for remembering individual jobs in a session
        if len(self.hostlist):
            hostlist = hostlist + self.hostlist
        self.hostlist = hostlist

    def UpdateHostlistWidget(self):
        """ Update the list of hosts from self.hostlist
        """
        #self.setValue['hostlist'] = self.machList.setlist
        # Need to check if we are using the hostlist widget
        if hasattr( self, 'machList' ):
            self.machList.setlist( self.hostlist )

    def SaveHostlistToDefaults(self):
        """
        Save the current hostlist to the rc_vars keyed by the calc/jobtype
        """

        global defaults
        # Get the values we use to key the dictionaries
        calctype = self.job.get_parameter('calctype')
        jobtype = self.job.jobtype

        # Make sure we have the structure we need - this all relies
        # on the job_dict being a pointer to the dictinoary
        job_dict = defaults.get_value( 'job_dict' )
        if not job_dict:
            job_dict = {}
            defaults.set_value( 'job_dict', job_dict )

        if not job_dict.has_key( calctype ):
            job_dict[calctype] = {}

        if not job_dict[calctype].has_key( jobtype ):
            job_dict[calctype][jobtype] = {}

        # Don't think we need to explcitity set this?
        job_dict[calctype][jobtype]['hostlist'] = self.hostlist

    def GetValues(self):
        """
            We just call _GetValues as we can be overloaded, but this
            latter method is needed in the RSL widget
        """

        return self._GetValues()
        
    def _GetValues(self):
        """ Query the widgets to get their current values and
             return a dictionary with all of the values in it suitable
            for passing to a job.

        """

        for key,func in self.getValue.iteritems():
            val = func()
            # Need to convert empty strings to null
            if type(val) == str and len(val) == 0:
                value = None
            self.values[key]= val

            
            if self.debug:
                print "_GetValues setting: %s to: %s" % ( key,val )
                
        #print "self.values is ",self.values
        return self.values

    def SaveParameters(self,default=None):
        """ Save the job parameters from this widget into the job.job_parameters dictionary
            If the default flag is set we also save the values to the rc_vars dictionary
        """

        jobdict = self.GetValues()

        #for key,value in jobdict.iteritems():
        #    # Should save the values even if they are none.
        #    #if key in self.job.job_parameters.keys() and value:
        #    if key in self.job.get_parameters().keys():
        #        self.job.set_parameter( key, value )
        #        if self.debug:
        #            print "SaveParameters setting: %s : %s" % (key,value)

        self.job.update_parameters( jobdict )

        # Update command 
        if self.update_cmd:
            print "save Parameters  running update command"
            self.update_cmd( job=self.job, hostlist=self.hostlist )
                    
        if default:
            self.SaveHostlistToDefaults()
            self.job.save_parameters_as_default()

    def LayoutQuitButtons(self):
        """ Layout the Buttons to quit"""
        # Buttons to save or quit
        acceptButton = Tkinter.Button(self.interior(),
                                text="Accept",
                                command=lambda s=self: s.Quit(save=1))
        acceptButton.pack(side='left')
        saveAsDefaultButton = Tkinter.Button(self.interior(),
                                text="Save as Defaults",
                                command=lambda s=self: s.SaveParameters(default=1) )
        saveAsDefaultButton.pack(side='left')
        cancelButton = Tkinter.Button(self.interior(),
                                text="Cancel",
                                command=lambda s=self: s.Quit(save=None))
        cancelButton.pack(side='left')

    def Quit(self,save=None,default=None):
        """ call _quit ( which may be overloaded to implement any calc-specific stuff)
            and then destroy the editor
            _quit can generate an error code to state not to quit
        """
        
        error = self._quit(save=save,default=default)
        if error:
            return
        self._destroy()

    def _quit(self,save=None,default=None):
        """ Default quit - should be overwritten"""

        if save:
            self.SaveParameters( default=default )


    def _destroy(self):
        """Destroy the widget and run any cleanup code we may have been passed"""
        self.destroy()
        if self.onkill:
            self.onkill()

        if self.debug:
            if self.job:
                print self.job.get_parameters()
            
    def __str__(self):
       """The string to return when we are asked what we are"""
       if self.title:
           return self.title
       else:
           return 'JobEditor'

    # Messages - display a dialog with an information or error message

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
       

###################################################################################################
###################################################################################################

    def LayoutMachListWidget(self):
        """ Lay out the machine list widget"""

        # Create the widgets to edit the list of machines
        #self.values['hostlist'] = [] # set default value here
        self.values['host'] = [] # set default value here
        machListFrame = Pmw.Group( self.interior(), tag_text='Machines' )
        machListFrame.pack(fill='both',expand=1)

        # The rest of this is managed with the grid geometry manager
        self.machList = Pmw.ScrolledListBox(
            machListFrame.interior(),
            listbox_selectmode='extended',
            items=self.hostlist
#            items=self.values['hostlist']
            )
        #self.getValue['hostlist'] = lambda s=self: s.machList.get()
        #self.setValue['hostlist'] = self.machList.setlist
        
        # For the host we only want one so take the first item in the list
        #self.getValue['host'] = lambda s=self: s.machList.getvalue()[0]
        # Use all values but query the user in the _quit routine
        self.getValue['host'] = lambda s=self: s.machList.getvalue()
        
        # Can't guarantee the list of hosts will have been set up before we
        # try and set the value of the desired host
        #self.setValue['host'] = self.machList.setvalue

        self.machList.pack( side='left' )
        frameR = Tkinter.Frame( machListFrame.interior() )
        frameR.pack(side='left', fill='x', expand='1')
        
        self.machEntry = Tkinter.Entry( frameR,
                                        width=20)
        self.machEntry.pack( side='top', fill='x', expand='1' )
        bframe = Tkinter.Frame( frameR )
        bframe.pack( side='top' )
        addMachButton = Tkinter.Button( bframe,
                                         text = 'Add',
                                         command = self.AddMachine)
        addMachButton.pack( side='left' )
        #self.balloon.bind( addMachButton, 'Add a machine to the list. )
        delMachButton = Tkinter.Button( bframe,
                                        text = 'Del',
                                        command = self.DelMachine)
        delMachButton.pack( side='left' )
        
        updateButton = Tkinter.Button( frameR,
                                        text = 'Update parameters from host',
                                        command = self.UpdateParametersFromHost)
        updateButton.pack( side='top' )
        

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

    def LayoutExecutableWidget(self,browse=None):
        """ Lay out the widget to select the executable"""


        if browse:
            exeFrame = Tkinter.Frame( self.interior() )
            packParent = exeFrame
            labelText = 'Executable:'
        else:
            packParent = self.interior()
            labelText = 'Executable Name:'
        
        self.executableWidget = Pmw.EntryField( packParent,
                                            labelpos = 'w',
                                            label_text = labelText,
                                            validate = None
                                            )        
        
        if browse:
            def __findFile():
                oldfile = None
                olddir = None
                if self.values.has_key('executable'):
                    exe = self.values['executable']
                    if exe and len(exe):
                        olddir,oldfile = os.path.split( exe )

                exepath = tkFileDialog.askopenfilename(initialfile=oldfile,
                                                      initialdir=olddir)
                if len(exepath) == 0:
                    exepath = oldfile

                self.values['executable'] = exepath
                self.executableWidget.setentry( exepath )

            button = Tkinter.Button(exeFrame,text="Browse...",command=__findFile)
            self.executableWidget.pack(side='left')
            exeFrame.pack(side='top')
            button.pack(side="left", padx=10)
        else:
            self.executableWidget.pack(side='top')

        self.values['executable'] = None
        self.getValue['executable'] = lambda s=self: s.executableWidget.getvalue()
        self.setValue['executable'] = self.executableWidget.setentry


    def LayoutLocalDirectoryWidget( self ):
        """ Lay out the widget to select the directory"""


        # Add this attribute to the values dictionary
        self.values['local_directory'] = None
        
        dirFrame = Tkinter.Frame( self.interior() )
        packParent = dirFrame
        labelText = 'Local Directory:'
        
        self.localDirectoryWidget = Pmw.EntryField( packParent,
                                               labelpos = 'w',
                                               label_text = labelText,
                                               validate = None
                                               )
        if self.dir_cmd:
            self.localDirectoryWidget.configure(command=self.dir_cmd)
            #self.directoryWidget.component('entry').bind("<Leave>",self.dir_cmd)
        
        def __findDirectory():

            # Get a sensible default
            directory = self.values['local_directory']
            #if not directory:
            #    # Get the user paths from the dict in viewer.paths
            #    directory = paths['user']

            path=tkFileDialog.askdirectory( initialdir=directory )
            if len(path):
                self.values['local_directory'] = path
                self.localDirectoryWidget.setentry( path )
                # Run any command we may have been passed
                if self.dir_cmd:
                    self.dir_cmd( directory )

        button = Tkinter.Button(dirFrame,text="Browse...",command=__findDirectory)
        self.localDirectoryWidget.pack(side='left')
        dirFrame.pack(side='top')
        button.pack(side="left", padx=10)

        self.getValue['local_directory'] = lambda s=self: s.localDirectoryWidget.getvalue()
        self.setValue['local_directory'] = self.localDirectoryWidget.setentry
        
    def LayoutRemoteDirectoryWidget( self ):
        """ Lay out the widget to select the remote directory"""


        # Add this attribute to the values dictionary
        self.values['remote_directory'] = None
        
        packParent = self.interior()
        labelText = 'Remote Directory:'
        
        self.remoteDirectoryWidget = Pmw.EntryField( packParent,
                                               labelpos = 'w',
                                               label_text = labelText,
                                               validate = None
                                               )
        if self.dir_cmd:
            self.remoteDirectoryWidget.configure(command=self.dir_cmd)
            #self.directoryWidget.component('entry').bind("<Leave>",self.dir_cmd)
        
        self.remoteDirectoryWidget.pack(side='top')

        self.getValue['remote_directory'] = lambda s=self: s.remoteDirectoryWidget.getvalue()
        self.setValue['remote_directory'] = self.remoteDirectoryWidget.setentry


    def LayoutJobmanagerWidget(self):
        """ Lay out the widget to select the directory on the remote machine"""
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


class LocalJobEditor(JobEditor):

    """ A widget to edit jobs submitted to the local machine
    """

    def __init__(self, root,job,**kw):

        # Set up the defaults
        self.jobtype = 'LocalJobEditor'
        
        # Initialse everything in the base class
        JobEditor.__init__(self,root,job,**kw)

        self.LayoutWidgets()
        self.GetInitialValues()
        self.UpdateWidgets()


    def LayoutWidgets(self):
        self.LayoutExecutableWidget(browse=1)
        self.LayoutLocalDirectoryWidget()
        self.LayoutQuitButtons()


class RSLEditor(JobEditor):
    """ Base class editor for editors that support RSL
    """
    RSLNONE = 'None Selected'
    
    def __init__(self, root,job,**kw):

        self.jobtype = 'RSLEditor'

        # Initialse everything in the base class
        JobEditor.__init__(self,root,job,**kw)

        # RSL parameters
        
        #self.rsl_operations = [ '=','<','>','>=','<=' ]
        #self.rsl_operations = ( '=' )

        # Dictionary mapping variable name to the type of the variable
        # We list both rsl and xrsl (Nordugrid) parameters and then remove
        # those that aren't valid
        self.rslVariables = {}
        self.rslVariables['architechture']=str
        self.rslVariables['arguments']=str
        self.rslVariables['cpuTime']=str
        self.rslVariables['disk']=int
        self.rslVariables['environment']='entrypair'
#        self.rslVariables['executable']=str
        self.rslVariables['gridTime']=str
        self.rslVariables['jobName']=str
        self.rslVariables['maxCpuTime']=str
        self.rslVariables['maxTime']=str
        self.rslVariables['maxWallTime']=str
        self.rslVariables['memory']=int
        self.rslVariables['opSys']=str
        self.rslVariables['project']=str
        self.rslVariables['queue']=str
        self.rslVariables['runTimeEnvironment']=str
        self.rslVariables['wallTime']=str

        # Check the job and remove any that aren't valid
        if hasattr( self.job, 'rsl_parameters' ):
            # Cant change size of dict during iteration
            # so build up a list and then remove
            to_remove = []
            for parameter in self.rslVariables:
                if not parameter in self.job.rsl_parameters :
                    to_remove.append( parameter )
            for parameter in to_remove:
                del self.rslVariables[ parameter ]

        self.currentRSL = self.RSLNONE # Bit of a hack so we know the last selected RSL
        self.RSLValues = { self.currentRSL : ('=',None) } # dict of name : ( op,value ) - value could be a list
        self.chooseRSLWidget = None
        self.rslValueWidget = None
        self.rslActive = None # To indicate if the RSL widgets are being used

    def _AddDictAsPair(self,key,value):
        """ Take a dictionary we have been given and split it up into separate variables
            suitable for displaying with an entrypair widget
        """
        i=0
        for var,val in value.iteritems():
            if i==0:
                self.RSLValues[key] = ('=',[var,val])
            else:
                self.RSLValues[key+str(i)] = ('=',[var,val])
            i+=1
        
    def LayoutRSLWidget(self):
        """ Lay out the RSL widgets"""

        self.rslActive = 1
        
        # Create the widgets to edit the list of machines
        RSLFrame = Pmw.Group( self.interior(), tag_text='RSL parameters' )
        RSLFrame.pack(fill='both',expand=1)
        self.selectedRSLWidget = Pmw.OptionMenu(
            RSLFrame.interior(),
            #items=self.RSLValues.keys(),
            items=[self.RSLValues.keys()],
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
        """ Add the selected RSL to self.RSLValues and
           Then update the widgets
        """

        #print "AddSelectedRSL"

        # Select a suitable empty value 
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
        if selected == 'environment' and self.RSLValues.has_key( selected ):
            for i in range(10):
                selected =  'environment'+str(i+1)
                if not self.RSLValues.has_key( selected ):
                    break
            self.RSLValues[selected] = ( None, value )
        else:
            self.RSLValues[selected] = ( None, value )

        # Make sure we remove the null value
        if self.RSLNONE in self.RSLValues.keys():
            del self.RSLValues[self.RSLNONE]
            
        self.RSLUpdateWidgets( selected=selected )
        

    def _ChangeSelectedRSL(self,value):
        """The user has changes the currently selected RSL"""

        self._SaveCurrentRSL()
        self.RSLUpdateWidgets( selected=value )


    def _SaveCurrentRSL(self):
        """ Save the current state of the RSL list"""

        #print "_SaveCurrentRSL: ",name
        #rsl_name = self.selectedRSLWidget.getvalue()
        rsl_name = self.currentRSL

        # None were selected so skip anything else
        if rsl_name == self.RSLNONE:
            return None
            
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
        self.RSLValues[rsl_name] = ( rsl_op, rsl_value )
        

    def RSLUpdateWidgets( self, selected=None ):
        """ Display the correct widgets for the selected rsl]
            We only need to consider 2 widgets here:
            self.selectedRSLWidget - a Pmw Option Menu that holds the
            list of RSLValues keys
            self.rslValueWidget that holds a widget for the variable of the
            type of the currently selected RSL (self.currentRSL)
        """


        RSL_list = self.RSLValues.keys()

        # Determine which one we are showing
        if not selected:
            selected = RSL_list[0]
        self.currentRSL = selected
        
        # deal with the first widget
        self.selectedRSLWidget.setitems( RSL_list )
        self.selectedRSLWidget.setvalue(selected)

        # Forget the value widget - we recreate if needed
        self.rslValueWidget.forget()

        # No widgets selected
        if selected == self.RSLNONE:
            return

        # Now determine what sort of widget the value widget is
        value = self.RSLValues[selected][1]

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

        if to_delete == self.RSLNONE:
            return
        
        if len( self.RSLValues ) == 0:
            selected = self.RSLNONE
        elif len( self.RSLValues ) == 1:
            del self.RSLValues[ to_delete ]
            self.values[ to_delete ] = None
            selected = self.RSLNONE
        else:
            del self.RSLValues[ to_delete ]
            self.values[ to_delete ] = None
            selected = self.RSLValues.keys()[0]
            
        self.RSLUpdateWidgets( selected=selected )

    def GetValues(self):
        """ Return a dictionary with all of the values in it
        """

        self.GetValuesRSL()
        return self._GetValues()
        
    def GetValuesRSL(self):
        """ Update self.values with the values from the widgets
            We also deal with the environment variable here as it is
            a paired value
        """

        envdict = {}
        for key,vlist in self.RSLValues.iteritems():
            #print "RSL key: %s value: %s" % ( key,vlist)
            if key == self.RSLNONE:
                continue
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

    def GetInitialRSL(self):
        """ Set self.RSLValues from the job we were given
            If the rcUpdate flag is set then overwrite any with those that are
            set in the rc_vars dictionary.
        """
        
        jobdict = self.job.get_parameters()
        self.SetRSL( jobdict )


    def SetRSL(self,job_dict):
        """ Set self.RSLValues from a dictionary of job parameters
        """

        # Clear out the old values and set a null one
        self.RSLValues = {}
        self.RSLValues[self.RSLNONE] = ('=',None)
        
        for key,value in job_dict.iteritems():
            if value:
                if self.rslVariables.has_key( key ):
                    if key == 'environment':
                        self._AddDictAsPair( key, value)
                    else:
                        self.RSLValues[key] = ('=',value) # Currently only assume = op

    def GetInitialValues(self):
        """ Set self.values and self.RSLValues to those specified in
            job we've been given
        """

        if self.debug:
            print "GetIntialValues RSL"
            
        self.GetInitialParameters()
        self.GetInitialRSL()

    def UpdateValues(self,job_dict):
        """ Update self.values and self.RSLValues with the supplied
            dictionary of job paramters
        """

        self._UpdateValues( job_dict )
        self.SetRSL( job_dict )
        
        
    def UpdateWidgets(self):
        """Set all the widgets to the value in self.values
        """

        self._UpdateWidgets()

        # This is a definite hack - need to sort out the logic of adding/removing variables
        # and put it in one place
        if len(self.RSLValues) > 1 and self.RSLNONE in self.RSLValues.keys():
            del self.RSLValues[self.RSLNONE]
                
        selected = self.RSLValues.keys()[0]
        self.RSLUpdateWidgets( selected=selected )


    def _quit(self,save=None,default=None):
        """ Default quit - should be overwritten"""

        if save:
            #Make sure we get the latest rsl variable if that was the last thing to be updated
            self._SaveCurrentRSL()
            self.SaveParameters( default=default )


class GlobusEditor(RSLEditor):

    """ A widget to edit Growl Jobs
    """

    def __init__(self, root,job,**kw):


        # Initialse everything in the base class
        RSLEditor.__init__(self,root,job,**kw)

        # Set up the defaults
        self.jobtype = 'Globus'
        self.debug=None
        
        self.LayoutWidgets()
        self.GetInitialValues()
        self.UpdateWidgets()

        
    def LayoutWidgets(self):
        """ Create and lay out all of the widgets"""

        # These are found in the base class JobEditor (see jobed.py)
        self.LayoutMachListWidget()
        self.LayoutNprocWidget()
        self.LayoutExecutableWidget(browse=0)
        self.LayoutLocalDirectoryWidget()
        self.LayoutRemoteDirectoryWidget()
        self.LayoutJobmanagerWidget()
        self.LayoutRSLWidget()
        self.LayoutQuitButtons()

        #Pmw.alignlabels( [self.executableWidget, self.directoryWidget] )

    def _quit(self,save=None,default=None):
        """ Need to make sure that the user has selected a single host"""

        if save:
            hosts = self.getValue['host']()
            if not len(hosts) == 1:
                self.Error("Please select a single host for the job to run on")
                return 1

            #Make sure we get the latest rsl variable if that was the last thing to be updated
            self._SaveCurrentRSL()
            self.SaveParameters( default=default )


class NordugridEditor(RSLEditor):

    """ A widget to edit Nordugrid Jobs
    """

    def __init__(self, root,job,**kw):

        # Set up the defaults
        self.jobtype = 'Nordugrid'
        if not kw.has_key('title'):
            kw['title'] = self.jobtype+ ' JobEditor'

        # Initialse everything in the base class
        RSLEditor.__init__(self,root,job,**kw)

    def LayoutWidgets(self):
        """ Create and lay out all of the widgets"""

        # These are found in the base class JobEditor (see jobed.py)
        #self.LayoutMachListWidget()
        self.LayoutNprocWidget()
        self.LayoutRSLWidget()
        self.LayoutQuitButtons()


class RMCSEditor(JobEditor):

    """ A widget to hold all the symmetry tools.
    """

    def __init__(self, root,job,**kw):

        # Set up the defaults
        self.jobtype = 'RMCS'
        title = self.jobtype+ ' JobEditor'
        
        # Initialse everything in the base class
        JobEditor.__init__(self,root,job,**kw)

        
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
        
        # These are found in the base class JobEditor (see jobed.py)
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
    import jobmanager

    class Junk:
        def __init__(self):
            self.job_parameters =  {}
            #self.job_parameters =  {'memory' : '1234',
            #                    'environment' :
            #                    {'ed3':'file.ed3','ed2':'file.ed2'},
            #                    'gridTime':'444'}
        
        def has_parameter(self,par):
            return True
        def set_parameter(self,par,val):
            return True
        def get_parameter(self,par):
            return self.job_parameters
    #job = Junk()
    
    root=Tkinter.Tk()
    def test_cmd():
        print "ran test command"
    #ed = LocalJobEditor( root, job, dir_cmd=test_cmd )
    job = jobmanager.job.GlobusJob()
    job.set_parameter('calctype','GAMESS-UK')
    ed = GlobusEditor( root, job )
    test = Tkinter.Button( ed.interior(),
                           text = 'Test',
                           command = ed.GetValues)
    test.pack()
    root.mainloop()
