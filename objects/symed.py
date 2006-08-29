import Tkinter
import Pmw
import viewer.initialisetk 

class SymmetryWidget(Pmw.MegaToplevel):

    """ A widget to hold all the symmetry tools.
    """

    frameWidth       = 300
    frameHeight      = 200


    def __init__(self,root, **kw):

        self.debug = 1

        viewer.initialisetk.initialiseTk(root)

        # Define the megawidget optons.
        optiondefs = (
           ('command',   None,   Pmw.INITOPT),
           )
        self.defineoptions(kw, optiondefs)

        self.defaultThresh = 0.1
                            
        # Initialise base class (after defining options).
        Pmw.MegaToplevel.__init__( self, root, title='Symmetry Operations' )
        
        # Ensure that when the user kills us with the window manager we behave as expected
        self.userdeletefunc( lambda s=self: s.withdraw() )
        #self.usermodaldeletefunc( func = self.withdraw )

        #try and get the thing to be a decent size
        #self.interior( height = self.frameWidth, width = self.frameWidth )
        #self.component('hull').configure( height = self.frameWidth, width = self.frameWidth )

        # Get the balloon help from the main widget
        if kw.has_key('balloon'):
            self.balloon = kw['balloon']
        else:
            self.balloon = Pmw.Balloon(self.interior())


        controlFrame = Pmw.Group( self.interior(), tag_text='Operations' )
        controlFrame.pack(fill='both',expand=1)

        getSymButton = Tkinter.Button( controlFrame.interior(), text='Get Symmetry', command=self.getSymmetry )
        self.balloon.bind( getSymButton, 'Get the point group for the molecule.' )

        getSymButton.pack( side = 'left' )

        symmetriseButton = Tkinter.Button( controlFrame.interior(), text='Symmetrise', command=self.symmetrise )
        self.balloon.bind( symmetriseButton, 'Change the molecule to conform to the symmetry group.' )
        symmetriseButton.pack( side = 'left' )

        self.symThresh = Pmw.EntryField(
            controlFrame.interior(),
            labelpos = 'w',
            label_text = 'Threshold:',
            entry_justify = 'right',
            entry_width = 10,
            validate = { 'validator' : 'real',
                         'min' : 0.000001,
                         'max' : 1 },
            value = self.defaultThresh
            )
        
        self.balloon.bind( self.symThresh, 'How close 2 points should be before they are considered the same.' )
        self.symThresh.pack( side = 'left' )

        # Frame to display the Group
        groupFrame = Pmw.Group( self.interior(), tag_text='Group:' )
        groupFrame.pack(fill='both',expand=1)
        self.groupDisplay = Tkinter.Label( groupFrame.interior(), text = 'Symmetry not determined yet.' )
        self.groupDisplay.pack()

        # Frame to display the generators
        generatorFrame = Pmw.Group( self.interior(), tag_text='Generators:' )
        generatorFrame.pack(fill='both',expand=1)
        self.generatorDisplay = Pmw.ScrolledListBox( generatorFrame.interior(),
                                                     items = ('No generators found yet',)
                                                     )
        self.generatorDisplay.pack(fill='both',expand=1)

    def getThresh(self):
        """ Get the threshold from the symTresh widget"""
        return float( self.symThresh.getvalue() )


    def getSymmetry(self):
        """Get the threshold for the symmetriser and then invoke the symmetry command we have
           been passed with that threshold.
        """
            
        thresh = self.getThresh()
        if self['command']:
            label,generators = self['command']('getSymmetry',thresh)

            self.groupDisplay.configure( text = label )
            self.generatorDisplay.setlist(generators)
                    
            
    def symmetrise(self):
        """Get the threshold for the symmetriser and then symmetrise the molecule using this value.
        """
        thresh = self.getThresh()
        
        if self.debug:
            print "Invoking symmetrise with thresh: %f" % thresh
            
        if self['command']:
            self['command']('symmetrise',thresh)



if __name__ == "__main__":

    root=Tkinter.Tk()
    symEd = SymmetryWidget( root, command = None )
    root.mainloop()
