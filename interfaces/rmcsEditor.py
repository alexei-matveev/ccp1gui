import Tkinter
import Pmw
import tkFileDialog
import viewer.initialisetk
import os,getpass
from interfaces.jobsubEditor import JobSubEditor
from viewer.rc_vars import rc_vars

class RMCSEditor(JobSubEditor):

    """ A widget to hold all the symmetry tools.
    """

    def __init__(self, root,**kw):

        # Initialse everything in the base class
        JobSubEditor.__init__(self,root,**kw)

        # Set up the defaults
        self.title = 'RMCS JobEditor'
        
        self.values['srb_config_file'] = os.path.expanduser('~/srb.cfg')
        self.values['srb_input_dir'] = 'SET ME'
        self.values['srb_executable_dir'] = 'SET ME'
        self.values['srb_executable'] = 'SET ME'
        self.values['srb_output_dir'] = 'SET ME'
        self.values['rmcs_user'] = getpass.getuser()
        self.values['rmcs_password'] = ''
        self.values['myproxy_user'] = getpass.getuser()
        self.values['myproxy_password'] = ''

        self.GetInitialValues()
        self.LayoutWidgets()
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
    rc_vars[ 'machine_list'] = ['computers','are','evil']
    rc_vars[ 'count'] = '4'

    root=Tkinter.Tk()
    ed = RMCSEditor( root )
    print "ed is ",ed
    root.mainloop()
