import Tkinter
import Pmw
import tkFileDialog
import viewer.initialisetk
import os,getpass

if __name__ != "__main__":
    from viewer.rc_vars import rc_vars

class RMCSEditor(Pmw.MegaToplevel):

    """ A widget to hold all the symmetry tools.
    """

    frameWidth       = 300
    frameHeight      = 200


    def __init__(self, root, onkill = None,**kw):

        self.debug = 1
        self.onkill = onkill

        viewer.initialisetk.initialiseTk(root)

        # Initialise base class (after defining options).
        Pmw.MegaToplevel.__init__( self, root, title='RMCS Editor' )
        
        # Ensure that when the user kills us with the window manager we behave as expected
        self.userdeletefunc( lambda s=self: s.QuitNoSave() )
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
        self.values[ 'machine_list'] = ['hpcx.ac.uk']
        self.values[ 'nproc'] = '1'
        self.values['srb_config_file'] = os.path.expanduser('~/srb.cfg')
        self.values['srb_input_dir'] = 'SET ME'
        self.values['srb_executable_dir'] = 'SET ME'
        self.values['srb_executable'] = 'SET ME'
        self.values['srb_output_dir'] = 'SET ME'
        self.values['rmcs_user'] = getpass.getuser()
        self.values['rmcs_password'] = 'SET ME'
        self.values['myproxy_user'] = getpass.getuser()
        self.values['myproxy_password'] = 'SET ME'

        self.LayoutWidgets()
        self.GetInitialValues()
        self.UpdateWidgets()


    def GetInitialValues(self):
        """Query the rc_vars dictionary to get the initial values to set self.values with
        """
        
        global rc_vars
        for key,value in rc_vars.iteritems():
            #print "rc_vars: %s : %s" %(key,value)
            if self.values.has_key( key ):
                self.values[key] = value
                #print "Setting %s to %s" %(key,value)

    def UpdateWidgets(self):
        """Set all the widgets to the value in self.values
        """
        for key,value in self.values.iteritems():
            #print "Setting values for %s : %s" % (key,value)
            self.setValue[key]( value )

    def LayoutWidgets(self):
        """ Create and lay out all of the widgets"""
        
        # Create the widgets to edit the list of machines
        machListFrame = Pmw.Group( self.interior(), tag_text='Machines' )
        machListFrame.pack(fill='both',expand=1)
        self.machList = Pmw.ScrolledListBox(
            machListFrame.interior(),
            items=['hpcx.ac.uk', 'scarf.rl.ac.uk', 'ccp1.dl.ac.uk']
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

        self.nProc = Pmw.Counter( self.interior(),
                                  labelpos = 'w',
                                  label_text = 'Number of Processors:',
                                  entryfield_entry_width = 4,
                                  entryfield_validate = {'validator' : 'integer' ,
                                              'min' : 1 },
                                  increment = 1
                                  )
        self.getValue['nproc'] = lambda s=self: s.nProc.getvalue()
        self.setValue['nproc'] = self.nProc.setentry
        self.nProc.pack(side='top')

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

        # Buttons to save or quit
        quitAndSaveButton = Tkinter.Button(self.interior(),
                                text="Quit and Save",
                                command=self.QuitAndSave)
        quitAndSaveButton.pack(side='left')
        quitNoSaveButton = Tkinter.Button(self.interior(),
                                text="Quit do not save",
                                command=self.QuitNoSave)
        quitNoSaveButton.pack(side='left')

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

        
    def GetValueDict(self):
        """Return a dirctionary with all of the values in it"""

        for key,func in self.getValue.iteritems():
            self.values[key]= func()
        #print self.values
        return self.values

    def QuitNoSave(self):
        """It's all gone Pete Tong so we do the honourable thing..."""
        self.destroy()
        if self.onkill:
            self.onkill()
        #self.GetValueDict()

    def QuitAndSave(self):
        """Update the rc_vars with the new values"""
        
        global rc_vars
        for key,func in self.getValue.iteritems():
            rc_vars[key] = func()
            #print "Updating rc_vars with %s : %s" % (key,rc_vars[key])
        
        self.destroy()
        if self.onkill:
            self.onkill()
            
    def __str__(self):
       """The string to return when we are asked what we are"""
       return 'RMCS JobEditor'

if __name__ == "__main__":
    
    rc_vars = {} # Dictionary of the values held by this widget at any point
    rc_vars[ 'machine_list'] = ['computers','are','evil']
    rc_vars[ 'nproc'] = '4'
    rc_vars['srb_input_dir'] = 'foo',
    rc_vars['srb_executable_dir'] = 'woo',
    rc_vars['srb_executable'] = 'bar',
    rc_vars['srb_output_dir'] = 'out',
    rc_vars['rmcs_user'] = 'das',
    rc_vars['rmcs_password'] = 'adsda',
    rc_vars['myproxy_user'] = 'adsads',
    rc_vars['srb_config_file'] = 'adsada',
    rc_vars['myproxy_password'] = 'twdde'

    root=Tkinter.Tk()
    ed = RMCSEditor( root )
    root.mainloop()
