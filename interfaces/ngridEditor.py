import Tkinter
import Pmw
import tkFileDialog
import viewer.initialisetk
import os,getpass
from interfaces.jobsubEditor import JobSubEditor
from viewer.rc_vars import rc_vars

class NordugridEditor(JobSubEditor):

    """ A widget to edit Nordugrid Jobs
    """

    def __init__(self, root,**kw):

        # Initialse everything in the base class
        JobSubEditor.__init__(self,root,**kw)

        # Set up the defaults
        self.title = 'Nordugrid JobEditor'

        self.GetInitialValues()
        self.LayoutWidgets()
        self.UpdateWidgets()


    def LayoutWidgets(self):
        """ Create and lay out all of the widgets"""

        # These are found in the base class JobSubEditor (see jobsubEditor.py)
        #self.LayoutMachListWidget()
        self.LayoutNprocWidget()
        self.LayoutRSLWidget()
        self.LayoutQuitButtons()
            

if __name__ == "__main__":
    rc_vars[ 'machine_list'] = ['computers','are','evil']
    rc_vars[ 'count'] = '4'

    root=Tkinter.Tk()
    ed = NordugridEditor( root )
    print "ed is ",ed
    root.mainloop()
