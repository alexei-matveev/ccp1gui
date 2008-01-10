"""
A widget to plot the progress of an energy calculation/geometry optimisation
"""
import Tkinter
import Pmw
from Scientific.TkWidgets import TkPlotCanvas
import Numeric
import viewer.initialisetk


class CalculationMonitor(Pmw.MegaToplevel):

    """ A widget to monitor a calculation
    """

    def __init__(self,root,
                 **kw):

        self.debug = 1

        viewer.initialisetk.initialiseTk(root)

        # Define the megawidget optons.
        optiondefs = (
           ('command',   None,   Pmw.INITOPT),
           )
        self.defineoptions(kw, optiondefs)

            
        # Initialise base class (after defining options).
        Pmw.MegaToplevel.__init__( self, root )

        # Set the title
        self.configure( title = 'Calculation Monitor' )
        
        # Ensure that when the user kills us with the window manager we behave as expected
        self.userdeletefunc( lambda s=self: s.hide() )
        #self.usermodaldeletefunc( func = self.withdraw )

        #try and get the thing to be a decent size
        #self.interior( height = self.frameWidth, width = self.frameWidth )
        #self.component('hull').configure( height = self.frameWidth, width = self.frameWidth )


        # Get the balloon help from the main widget
        if kw.has_key('balloon'):
            self.balloon = kw['balloon']
        else:
            self.balloon = Pmw.Balloon(self.interior())


        self.plotCanvas =  TkPlotCanvas.PlotCanvas( self.interior(),
                                                "300", "200",
                                                relief=Tkinter.SUNKEN,
                                                border=2,
                                                zoom = 1,
                                                #select=display
                                                )

        self.plotCanvas.pack(side='top', fill='both', expand='yes')

        buttonFrame = Tkinter.Frame(self.interior())
        buttonFrame.pack(fill='both',expand=1)

        updateButton = Tkinter.Button( buttonFrame, text='Update', command=self.update)
        updateButton.pack( side='left' )
        resizeButton = Tkinter.Button( buttonFrame, text='Resize', command=self.plotCanvas._autoScale)
        resizeButton.pack( side='left' )
        stopButton = Tkinter.Button( buttonFrame, text='Stop Calculation', command=self.stop)
        stopButton.pack( side='left' )
        hideButton = Tkinter.Button( buttonFrame, text='Quit', command=self.hide)
        hideButton.pack( side='left' )
        

    def draw(self,plotgraphics):
        """Draw the lines and markers onto the canvas"""

        self.plotCanvas.draw( plotgraphics,'automatic','automatic' )

    def clear(self):
        """Clear the canvas"""

        self.plotCanvas.clear()
        
    def update(self):
        """ Update the canvas with the latest objects """

        graphObj = self.getGraphObj()
        if not graphObj:
            return
        
        self.plotCanvas.clear()
        self.draw( graphObj )


    def getGraphObj(self):
        """Create the object that we are going to draw."""
        
        if self['command']:
            # will return None, None if there are no new values
            energies, optEnergies = self['command']('newValues',None)

            if not energies:
                # Can't do owt
                return

            if not optEnergies:
                # Need to zero this out if it's only an energy calculation
                optEnergies = []

            i=0
            energyPoints = []
            optPoints = []
            for point in energies:
                energyPoints.append( (i,point) )
                if point in optEnergies:
                    optPoints.append( (i,point) )
                i+=1

            energyLine =  TkPlotCanvas.PolyLine( energyPoints, color='red' )
            energyMarkers =  TkPlotCanvas.PolyMarker( energyPoints,marker='dot')

            toDraw = []
            toDraw.append( energyLine )
            toDraw.append( energyMarkers )

            if len(optPoints):
                optMarkers =  TkPlotCanvas.PolyMarker( optPoints,marker='triangle', color='blue')
                toDraw.append( optMarkers )

            graphObj = TkPlotCanvas.PlotGraphics( toDraw )
            return graphObj


    def stop(self):
        """stop the calculation"""
        print "stopping"
        if self['command']:
            self['command']('stop',None)


    def hide(self):
        """Hide the widget"""
        self.withdraw()


if __name__ == '__main__':

    count = 0
    energies = [-348.394983025,
                -348.43698948,
                -348.484016162,
                -348.492265832,
                -348.514626899,
                -348.516509211,
                -348.516509983,
                -348.51652592 ]

    optEnergies = [-348.394983025,
                   -348.514626899,
                   -348.51652592 ]
    
    def get_values(operation,arguments):
        global count
        if operation == 'newValues':
            count +=1
            return energies[:count],optEnergies
        
        elif operation == 'stop':
            print "stopping calc"

    root=Tkinter.Tk()
    calcmon = CalculationMonitor( root, command = get_values )
    root.mainloop()
