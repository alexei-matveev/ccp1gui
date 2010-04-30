"""
Unit testing for the visualisers
"""
import os,sys
if __name__ == "__main__":
    # Need to add the gui directory to the python path so 
    # that all the modules can be imported
    gui_path = os.path.split(os.path.dirname( os.path.realpath( __file__ ) ))[0]
    sys.path.append(gui_path)


import unittest
import viewer.vtkgraph
import generic.visualiser

class testMoleculeVisualisers(unittest.TestCase):
    """Test the different visualisers for Molecules"""


    # These are all class variables - see setUp for details
    gui=None
    visualiser=None
    molecule=None


    def setUp(self):

        """
        When unittest runs the tests, a new class is created and then destroyed for each test.
        As a result a new gui instance would need to be created, molecule loaded etc for each one
        which is unecesssarily time-consuming. To prevent this, the gui, molecule and visualiser variables
        are saved as class as opposed to instance variables, allowing them to be created once but shared
        by all the test cases.

        """

        if not self.__class__.gui:
            
            # need to use global tkroot for all tests or else it is destroyed when 
            # the testsuite is destroyed
            global tkroot

            gui = viewer.vtkgraph.VtkGraph(tkroot)
            gui.load_from_file(gui_path+"/examples/feco5.zmt",display=0)

            # Set the molecule and molvis we will be using for all tests
            molecule = gui.loaded_mols()[0]
            visualiser = gui.molecule_visualiser(gui.master,gui,molecule)

            # Set to show nothing at first
            visualiser.show_labels = 0
            visualiser.show_spheres = 0
            visualiser.show_sticks = 0
            visualiser.show_wire = 0

            self.__class__.gui=gui
            self.__class__.visualiser=visualiser
            self.__class__.molecule=molecule


    def testLabels(self):
        """Test the labels visualiser"""
        
        self.visualiser.show_labels = 1
        self.gui.visualise(self.molecule,self.visualiser,open_widget=1)
        self.visualiser.show_labels = 0

    def testSpheres(self):
        """Test the spheres visualiser"""
        
        self.visualiser.show_spheres = 1
        self.gui.visualise(self.molecule,self.visualiser,open_widget=1)
        self.visualiser.show_spheres = 0

    def testSticks(self):
        """Test the sticks visualiser"""
        
        self.visualiser.show_sticks = 1
        self.gui.visualise(self.molecule,self.visualiser,open_widget=1)
        self.visualiser.show_sticks = 0

    def testWire(self):
        """Test the wire visualiser"""
        
        self.visualiser.show_wire = 1
        self.gui.visualise(self.molecule,self.visualiser,open_widget=1)
        self.visualiser.show_wire = 0



class testFieldVisualisers(unittest.TestCase):
    """Test the different visualisers for Fields"""

    gui=None

    def setUp(self):
        """Fire up the GUI, delete the molecule and vector objects leaving us with 
        just the field one to test.

        When unittest runs the tests, a new class is created and then destroyed for each test.
        As a result a new gui instance would need to be created, molecule loaded etc for each one
        which is unecesssarily time-consuming. To prevent this, the gui variable is saved as class 
        as opposed to an instance variable, allowing it to be created once but shared by all the 
        test cases.

        """

        if not self.__class__.gui:
            
            global tkroot
            gui = viewer.vtkgraph.VtkGraph(tkroot)
            gui.load_from_file(gui_path+"/examples/gamess_vect3d.pun",display=0)

            # Delete the molecule
            m = gui.loaded_mols()[0]
            gui.delete_obj(m)

            # Delete the Vector field
            f = gui.loaded_fields()[0]
            gui.delete_obj(f)

            self.__class__.gui=gui



    def testColourSurface(self):
        """Test the Colour Surface visualiser"""

        # Get the field object
        f = self.gui.loaded_fields()[0]

        # Create the visualiser
        visualiser=self.gui.colour_surface_visualiser(self.gui.master,self.gui,f)
        self.gui.visualise(f,visualiser,open_widget=1)

        # Destroy it
        visualiser.Delete()


    def testCutSlice(self):
        """Test the Cut Slice visualiser"""

        # Get the field object
        f = self.gui.loaded_fields()[0]

        # Create the visualiser
        visualiser=self.gui.cut_slice_visualiser(self.gui.master,self.gui,f)
        self.gui.visualise(f,visualiser,open_widget=1)

        # Destroy it
        visualiser.Delete()


    def testDensity(self):
        """Test the Density visualiser"""

        # Get the field object
        f = self.gui.loaded_fields()[0]

        # Create the visualiser
        visualiser=self.gui.density_visualiser(self.gui.master,self.gui,f)
        self.gui.visualise(f,visualiser,open_widget=1)

        #self.gui.mainloop()

        # Destroy it
        visualiser.Delete()


    def testDensityVolume(self):
        """Test the Density Volume visualiser"""


        # Get the field object
        f = self.gui.loaded_fields()[0]

        # Create the visualiser
        visualiser=self.gui.volume_density_visualiser(self.gui.master,self.gui,f)
        self.gui.visualise(f,visualiser,open_widget=1)

        # Destroy it
        visualiser.Delete()


    def testIrregularData(self):
        """Test the Irregular Data visualiser"""


        # Get the field object
        f = self.gui.loaded_fields()[0]

        # Create the visualiser
        visualiser=self.gui.irregular_data_visualiser(self.gui.master,self.gui,f)
        self.gui.visualise(f,visualiser,open_widget=1)

        # Destroy it
        visualiser.Delete()



    def testOrbital(self):
        """Test the Orbital visualiser"""

        # Get the field object
        f = self.gui.loaded_fields()[0]

        # Create the visualiser
        visualiser=self.gui.orbital_visualiser(self.gui.master,self.gui,f)
        self.gui.visualise(f,visualiser,open_widget=1)

        # Destroy it
        visualiser.Delete()


    def testOrbitalVolume(self):
        """Test the Orbital Volume visualiser"""


        # Get the field object
        f = self.gui.loaded_fields()[0]

        # Create the visualiser
        visualiser=self.gui.volume_orbital_visualiser(self.gui.master,self.gui,f)
        self.gui.visualise(f,visualiser,open_widget=1)

        # Destroy it
        visualiser.Delete()


class testVectorVisualisers(unittest.TestCase):
    """Test the different visualisers for Fields"""

    gui=None

    def setUp(self):
        """Fire up the GUI, delete the molecule and vector objects leaving us with 
        just the field one to test.

        When unittest runs the tests, a new class is created and then destroyed for each test.
        As a result a new gui instance would need to be created, molecule loaded etc for each one
        which is unecesssarily time-consuming. To prevent this, the gui variable is saved as class 
        as opposed to an instance variable, allowing it to be created once but shared by all the 
        test cases.

        """

        if not self.__class__.gui:
            
            global tkroot
            gui = viewer.vtkgraph.VtkGraph(tkroot)
            gui.load_from_file(gui_path+"/examples/gamess_vect3d.pun",display=0)

            # Delete the molecule
            m = gui.loaded_mols()[0]
            gui.delete_obj(m)

            # Delete the point field
            f = gui.loaded_fields()[1]
            gui.delete_obj(f)

            self.__class__.gui=gui



    def testHedgehog(self):
        """Test the Hedgehog vector plot"""

        # Get the field object
        f = self.gui.loaded_fields()[0]

        # Create the visualiser
        visualiser=self.gui.vector_visualiser(self.gui.master,self.gui,f)
        
        visualiser.show_hedgehog=1
        self.gui.visualise(f,visualiser,open_widget=1)

        # Destroy it
        visualiser.Delete()


    def testOrientedGlyphs(self):
        """Test the Oriented Glyphs vector plot"""

        # Get the field object
        f = self.gui.loaded_fields()[0]

        # Create the visualiser
        visualiser=self.gui.vector_visualiser(self.gui.master,self.gui,f)
        
        visualiser.show_orientedglyphs = 1
        self.gui.visualise(f,visualiser,open_widget=1)

        # Destroy it
        visualiser.Delete()


    def testStreamlines(self):
        """Test the default streamlines plot"""

        # Get the field object
        f = self.gui.loaded_fields()[0]

        # Create the visualiser
        visualiser=self.gui.vector_visualiser(self.gui.master,self.gui,f)
        
        visualiser.show_streamlines = 1
        self.gui.visualise(f,visualiser,open_widget=1)

        # Destroy it
        visualiser.Delete()


    def FOOtestStreamtubes(self):
        """Test the streamlines plot displayed as tubes.
        Don't run this as it fails to allocate the required memory & then seg-faults
        Need to look into this...

        """

        # Get the field object
        f = self.gui.loaded_fields()[0]

        # Create the visualiser
        visualiser=self.gui.vector_visualiser(self.gui.master,self.gui,f)
        
        visualiser.show_streamlines = 1
        visualiser.streamline_display=generic.visualiser.STREAM_TUBES
        # Don't open widget or else the 
        self.gui.visualise(f,visualiser,open_widget=1)

        # Destroy it
        visualiser.Delete()


    def testStreamarrows(self):

        # Get the field object
        f = self.gui.loaded_fields()[0]

        # Create the visualiser
        visualiser=self.gui.vector_visualiser(self.gui.master,self.gui,f)
        
        visualiser.show_streamarrows = 1
        self.gui.visualise(f,visualiser,open_widget=1)

        # Destroy it
        visualiser.Delete()



def testMolecules():
    """Routine to test just the molecule visualisers"""

    suite = unittest.TestLoader().loadTestsFromTestCase(testMoleculeVisualisers)
    unittest.TextTestRunner().run(suite)

def testFields():
    """Routine to test just the field visualisers"""

    suite = unittest.TestLoader().loadTestsFromTestCase(testFieldVisualisers)
    unittest.TextTestRunner().run(suite)

def testVectors():
    """Routine to test just the field visualisers"""

    suite = unittest.TestLoader().loadTestsFromTestCase(testVectorVisualisers)
    unittest.TextTestRunner().run(suite)

def testMe():
    """Return a test suite with all the tests that should be run by the main testing script"""

    m = unittest.TestLoader().loadTestsFromTestCase(testMoleculeVisualisers)
    f = unittest.TestLoader().loadTestsFromTestCase(testFieldVisualisers)
    v = unittest.TestLoader().loadTestsFromTestCase(testVectorVisualisers)
    
    return unittest.TestSuite([m, f, v])

if __name__ == "__main__":

    import Tkinter
    tkroot = Tkinter.Tk()
    tkroot.withdraw()

    #testMolecules()
    #testFields()
    #testVectors() 
    
    m = unittest.TestLoader().loadTestsFromTestCase(testMoleculeVisualisers)
    f = unittest.TestLoader().loadTestsFromTestCase(testFieldVisualisers)
    v = unittest.TestLoader().loadTestsFromTestCase(testVectorVisualisers)
    alltests = unittest.TestSuite([m, f, v])
    unittest.TextTestRunner().run(alltests)
