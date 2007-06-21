#
# unit tests for the subprocess classes
#
import unittest
import os

from getfileio import GetFileIO

from objects.zmatrix import Zmatrix, ZAtom


class IOTestCase(unittest.TestCase):
    """Base class - might come in useful later and save lots of typing..."""

    
    def getMolecule(self):
        """ Return a molecule suitable for testing the writers - could
            just read one in, but this way we have more control over
            exactly what the molecule contains
        """

        molecule = Zmatrix()
        molecule.title = "Test Molecule"
        molecule.name = "Test1"
        data = [
            ['1.58890', '-1.44870', '-0.47000', 'C1', 'C', 6],
            ['1.54300', '-2.25990', '0.77910', 'C2', 'C', 6],
            ['2.21440', '-3.47410', '0.88040', 'C3', 'C', 6],
            ['2.16940', '-4.22350', '2.03080', 'C4', 'C', 6],
            ['1.45120', '-3.77740', '3.11890', 'C5', 'C', 6],
            ['0.77320', '-2.58240', '3.03840', 'C6', 'C', 6],
            ['0.82440', '-1.82660', '1.89060', 'C7', 'C', 6],
            ['2.40210', '-1.69480', '-0.94010', 'H8', 'H', 1],
            ['0.81370', '-1.61080', '-1.10630', 'H9', 'H', 1],
            ['1.55340', '-0.51550', '-0.20780', 'H10', 'H', 1],
            ['2.79760', '-3.75410', '0.13240', 'H11', 'H', 1],
            ['2.62530', '-5.03180', '2.07500', 'H12', 'H', 1],
            ['1.44160', '-4.26200', '3.93440', 'H13', 'H', 1],
            ['0.18740', '-2.32460', '3.76300', 'H14', 'H', 1],
            ['0.34860', '-0.96230', '1.79710', 'H15', 'H', 1]

            ]

        for d in data:
            atom = ZAtom()
            x = float( d[0] )
            y = float( d[1] )
            z = float( d[2] )
            atom.coord = [ x,y,z ]
            atom.name = d[3]
            atom.symbol = d[4]
            molecule.add_atom( atom )
        
            
        return molecule
            
            
        
class testCHARMM_CRD(IOTestCase):
    """Test whether we deal with CHARMM crd files"""

    def setUp(self):
        """Set the reader for all these filetypes"""
        
        getIO = GetFileIO()
        self.reader = getIO.GetReader( format='CHARMM crd' )
        self.writer = getIO.GetWriter( format='CHARMM crd' )

    def testRead(self):
        """"""

        molecules = self.reader.GetObjects(
            filepath='/c/qcg/jmht/Documents/codes/OpenBabel/fileformats/original-linear-path.crd',
            otype = 'molecules'
            )

        self.assertEqual( len(molecules[0].atom),24876)

    def testWrite(self):
        """"""

        mol = self.getMolecule()

        filepath = os.getcwd()+'/test.crd'
        self.writer.WriteFile( mol, filepath=filepath )

        statinfo = os.stat( filepath )
        self.assertEqual( statinfo.st_size,1099)
        os.remove( filepath )

class testCML(IOTestCase):
    """Test whether we deal with a CML file"""

    def setUp(self):
        """Set the reader for all these filetypes"""
        
        getIO = GetFileIO()
        self.writer = getIO.GetWriter( format='Chemical Markup Language' )

    def testWrite(self):
        """"""

        mol = self.getMolecule()

        filepath = os.getcwd()+'/test.cml'
        self.writer.WriteFile( mol, filepath=filepath )

        statinfo = os.stat( filepath )
        self.assertEqual( statinfo.st_size,1141)
        os.remove( filepath )


class testDLPOLY_CONFIG_IO(IOTestCase):
    """Test whether we deal with MDL mol file"""

    def setUp(self):
        """Set the reader for all these filetypes"""
        
        getIO = GetFileIO()
        self.reader = getIO.GetReader( format='DL-POLY CONFIG' )

    def testRead(self):
        """"""

        molecules = self.reader.GetObjects(
            filepath='/c/qcg/jmht/Documents/codes/OpenBabel/fileformats/DLPOLY_TEST1.cfg',
            otype = 'molecules'
            )

        self.assertEqual( len(molecules[0].atom),1080)


class testGUKOutputIO(IOTestCase):
    """Test whether we can read a GAMESS-UK Output file"""

    def setUp(self):
        """Set the reader for all these filetypes"""
        
        getIO = GetFileIO()
        self.reader = getIO.GetReader( format='GAMESS-UK output' )

    def testOPTXY(self):
        """"""

        trajectories = self.reader.GetObjects(
            filepath='/c/qcg/jmht/Documents/codes/OpenBabel/fileformats/gamessuk/DFT_opt.exti4a1.3-21G.8x4.out',
            otype = 'trajectories'
            )

        # Should return one trajectory object
        self.assertEqual( len(trajectories),1)

class testCube_IO(IOTestCase):
    """Test whether we can read a Gau$$ian cube file"""

    def setUp(self):
        """Set the reader for all these filetypes"""
        
        getIO = GetFileIO()
        self.reader = getIO.GetReader( format='Gaussian cubefile' )

    def testRead(self):
        """"""
        
        fields = self.reader.GetObjects(
            filepath='/c/qcg/jmht/Documents/codes/OpenBabel/fileformats/cube/dxy.cube',
            otype = 'fields'
            )

        molecules = self.reader.GetObjects( 'molecules' )

        self.assertEqual( len(molecules[0].atom),7)
        self.assertEqual( len(fields[0].data),68921)

#     def testReadOrbitals(self):
#         """"""
        
#         fields = self.reader.GetObjects(
#             filepath='/c/qcg/jmht/Documents/codes/OpenBabel/fileformats/cube/phoh.cube',
#             otype = 'fields'
#             )

#         molecules = self.reader.GetObjects( 'molecules' )

#         self.assertEqual( len(molecules[0].atom),13)
#         self.assertEqual( len(fields),25)


class testMDL_IO(IOTestCase):
    """Test whether we deal with MDL mol file"""

    def setUp(self):
        """Set the reader for all these filetypes"""
        
        getIO = GetFileIO()
        self.reader = getIO.GetReader( format='MDL MOL format' )

    def testRead(self):
        """"""

        molecules = self.reader.GetObjects(
            filepath='/c/qcg/jmht/Documents/codes/OpenBabel/fileformats/nsc2dmol.mol',
            otype = 'molecules'
            )

        # Should return 13 atoms
        self.assertEqual( len(molecules[0].atom),13)

class testMSICeriussII_IO(IOTestCase):
    """Test whether we deal with an MSI Cerius II file"""

    def setUp(self):
        """Set the reader for all these filetypes"""
        
        getIO = GetFileIO()
        self.writer = getIO.GetWriter( format='MSI Cerius II' )

    def testWrite(self):
        """"""

        mol = self.getMolecule()

        filepath = os.getcwd()+'/test.car'
        self.writer.WriteFile( mol, filepath=filepath )

        statinfo = os.stat( filepath )
        self.assertEqual( statinfo.st_size,1847)
        os.remove( filepath )

        
class testPDB_IO(IOTestCase):
    """Test whether we deal with PDB files"""

    def setUp(self):
        """Set the reader for all these filetypes"""
        
        getIO = GetFileIO()
        self.IO = getIO.GetReader( format='Protein Data Bank format' )

    def testRead(self):
        """"""

        molecules = self.IO.GetObjects(
            filepath='/c/qcg/jmht/Documents/codes/OpenBabel/fileformats/pg_kaptein1.pdb',
            otype = 'molecules'
            )

        # Should return 1929 atoms
        self.assertEqual( len(molecules[0].atom),1929)

    def testWrite(self):
        """"""

        mol = self.getMolecule()

        filepath = os.getcwd()+'/test.pdb'
        self.IO.WriteFile( mol, filepath=filepath )

        statinfo = os.stat( filepath )
        self.assertEqual( statinfo.st_size,1009)
        os.remove( filepath )


class testPunch_IO(IOTestCase):
    """Test whether we deal with GAMESS-UK punchfiles"""

    def setUp(self):
        """Set the reader for all these filetypes"""
        
        getIO = GetFileIO()
        self.reader = getIO.GetReader( format='GAMESS-UK punchfile' )

    def test3DVectorRead(self):
        """ Read in a punch file that has a molecule, scalar and vector data
        """

        molecules = self.reader.GetObjects(
            filepath='/home/jmht/ccp1gui/examples/gamess_vect3d.pun',
            otype = 'molecules'
            )
        self.assertEqual( len(molecules[0].atom) , 4)


        fields = self.reader.GetObjects(
            filepath='/home/jmht/ccp1gui/examples/gamess_vect3d.pun',
            otype = 'fields'
            )
         
        # First field is vector (ndd=3) with 89373 points
        self.assertEqual( fields[0].ndd , 3)
        self.assertEqual( len(fields[0].data),89373)

        # Second field is scalar field with 29791 points
        self.assertEqual( fields[1].ndd , 1)
        self.assertEqual( len(fields[1].data),29791)

class testSHELXTL_IO(IOTestCase):
    """Test whether we deal with a shelxtl .res file"""

    def setUp(self):
        """Set the reader for all these filetypes"""
        
        getIO = GetFileIO()
        self.writer = getIO.GetWriter( format='SHELXTL res format' )

    def testWrite(self):
        """"""

        mol = self.getMolecule()

        filepath = os.getcwd()+'/test.res'
        self.writer.WriteFile( mol, filepath=filepath )

        statinfo = os.stat( filepath )
        self.assertEqual( statinfo.st_size,840)
        os.remove( filepath )


class testSmeagol_IO(IOTestCase):
    """Test whether we deal with Smeagol data"""

    def setUp(self):
        """Set the reader for all these filetypes"""
        
        getIO = GetFileIO()
        self.reader = getIO.GetReader( format='Smeagol output' )

    def testRead(self):
        """ read in scalar data
        """

        fields = self.reader.GetObjects(
            filepath='/c/qcg/jmht/share/codes/ccp1gui/smeagol/Benz.short.rho',
            otype = 'fields'
            )

        self.assertEqual( fields[0].dim[0] , 90)


class testSpartanInputIO(IOTestCase):
    """Test whether we deal with Spartan input data"""

    def setUp(self):
        """Set the reader for all these filetypes"""
        
        getIO = GetFileIO()
        self.reader = getIO.GetReader( format='Spartan input' )

    def testRead(self):
        """ read in a molecule
        """

        molecules = self.reader.GetObjects(
            filepath='/c/qcg/jmht/Documents/codes/OpenBabel/fileformats/infile.spinput',
            otype = 'molecules'
            )
        self.assertEqual( len(molecules[0].atom) , 68)


class testVTK_IO(IOTestCase):
    """Test whether we deal with VTK data"""

    def setUp(self):
        """Set the reader for all these filetypes"""
        
        getIO = GetFileIO()
        self.reader = getIO.GetReader( format='VTK data' )

    def testScalarRead(self):
        """ read in scalar data
        """

        fields = self.reader.GetObjects(
            filepath='/home/jmht/VTK/VTKData/Data/ironProt.vtk',
#            filepath='/home/jmht/VTK/VTKData/Data/plate.vtk',
            otype = 'fields'
            )

        self.assertEqual( fields[0].dim[0] , 68)

class testXYZ_IO(IOTestCase):
    """Test whether we deal with VTK data"""

    def setUp(self):
        """Set the reader for all these filetypes"""
        
        getIO = GetFileIO()
        self.reader = getIO.GetReader( format='XYZ cartesian coordinates format' )

    def testRead(self):
        """ read in scalar data
        """

        molecules = self.reader.GetObjects(
            filepath='/c/qcg/jmht/Documents/codes/OpenBabel/fileformats/toluene.xyz',
            otype = 'molecules'
            )

        self.assertEqual( len(molecules[0].atom) , 15)


class testZmatrix_IO(IOTestCase):
    """Test whether we deal with Zmatrix data"""

    def setUp(self):
        """Set the reader for all these filetypes"""
        
        getIO = GetFileIO()
        self.reader = getIO.GetReader( format='Zmatrix' )

    def testRead(self):
        """ read in a zmatrix
        """

        molecules = self.reader.GetObjects(
            filepath='/home/jmht/ccp1gui/examples/feco5.zmt',
            otype = 'molecules'
            )

        self.assertEqual( len(molecules[0].atom) , 16)


if __name__ == "__main__":

    if 1:
        # Run all tests automatically
        unittest.main()
    else:
        # Build a test suite with required cases and run it

        myTestSuite = unittest.TestSuite()

        myTestSuite.addTest(testCube_IO("testRead"))

        runner = unittest.TextTestRunner()
        runner.run(myTestSuite)
    
