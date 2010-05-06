"""Reader for Gaussian Cube files
"""
import os,sys
if __name__ == "__main__":
    # Need to add the gui directory to the python path so 
    # that all the modules can be imported
    gui_path = os.path.split(os.path.dirname( os.path.realpath( __file__ ) ))[0]
    sys.path.append(gui_path)
else:
    from viewer.paths import gui_path

import unittest

###from interfaces.units import *
au_to_angstrom = 0.529177249

from objects.zmatrix import Zmatrix,ZAtom
from objects.field import Field
from objects.periodic import z_to_el
from fileio import FileIO
import objects.vector

class CubeIO(FileIO):

    def __init__(self, filepath=None,**kw):
        """ Set up the structures we need

        """

        # Initialise base class
        FileIO.__init__(self,filepath=filepath,**kw)

        # List which types of object we can read/write
        self.canRead = True
        self.canWrite = [ ]


    def _ReadFile(self,**kw):
        """Parse a cube file returning Field and Zmatrix objects
        We do not attempt to convert the units of the field,
        so they are probably in atomic units.


        Below from: http://www.ks.uiuc.edu/Research/vmd/plugins/molfile/cubeplugin.html

C     WRITE A FORMATTED CUBEFILE VERY SIMILAR TO THOSE CREATED BY 
C     THE GAUSSIAN PROGRAM OR THE CUBEGEN UTILITY.
C     THE FORMAT IS AS FOLLOWS (LAST CHECKED AGAINST GAUSSIAN 98):
C
C     LINE   FORMAT      CONTENTS
C     ===============================================================
C      1     A           TITLE
C      2     A           DESCRIPTION OF PROPERTY STORED IN CUBEFILE
C      3     I5,3F12.6   #ATOMS, X-,Y-,Z-COORDINATES OF ORIGIN
C      4-6   I5,3F12.6   #GRIDPOINTS, INCREMENT VECTOR
C      #ATOMS LINES OF ATOM COORDINATES:
C      ...   I5,4F12.6   ATOM NUMBER, CHARGE, X-,Y-,Z-COORDINATE
C      REST: 6E13.5      CUBE DATA (WITH Z INCREMENT MOVING FASTEST, THEN
C                        Y AND THEN X)
C
C     FOR ORBITAL CUBE FILES, #ATOMS WILL BE < 0 AND THERE WILL BE ONE
C     ADDITIONAL LINE AFTER THE FINAL ATOM GIVING THE NUMBER OF ORBITALS
C     AND THEIR RESPECTIVE NUMBERS. ALSO THE ORBITAL NUMBER WILL BE
C     THE FASTEST MOVING INCREMENT.
C
C     ALL COORDINATES ARE GIVEN IN ATOMIC UNITS.
        
        """


        mol = Zmatrix()
        field = Field(nd=3)

        fp = open( self.filepath ,"r" )


        title1 = fp.readline().strip()
        title2 = fp.readline().strip()

        # could load titles from here
        mol.title = title1
        field.title = title1 + title2
        
        # empirically axes and coordinates are in au
        fac = au_to_angstrom
        tmp = fp.readline().split()

        # -ve natoms indicates an orbital file (see comments above)
        orbitals = None
        natoms = int(tmp[0])
        if natoms < 0:
            orbitals=1
            natoms = abs(natoms)
            if self.debug: "CubeIO reading orbital file"
        
        field.origin = fac*objects.vector.Vector([float(tmp[1]),float(tmp[2]),float(tmp[3])])
        # note that the Field object follows the punchfile (Fortran-style)
        # ordering so we reorder the axes
        for i in [0,1,2]:
            tmp = fp.readline().split()
            field.dim[2-i] = int(tmp[0])
            field.axis[2-i] = fac*float(field.dim[2-i]-1)* \
                         objects.vector.Vector([float(tmp[1]),float(tmp[2]),float(tmp[3])])
        # move origin to centre of grid from corner
        for i in [0,1,2]:
            field.origin = field.origin + 0.5*field.axis[i]

        # geometry seems to be in au
        fac = au_to_angstrom
        cnt = 0
        for i in range(0,natoms):
            tmp = fp.readline().split()
            #print i,tmp
            p = ZAtom()
            try:
                p.coord = [ float(tmp[2])*fac , float(tmp[3])*fac, float(tmp[4])*fac ]
            except ValueError:
                print 'Bad Line in cube file:',tmp
            p.symbol = z_to_el[int(tmp[0])]
            p.name = p.symbol
            p.index = cnt
            cnt = cnt + 1
            mol.add_atom(p)
        mol.reindex()


        # Set up the base field object
        ndata = field.dim[0]*field.dim[1]*field.dim[2]
        field.data = ndata*[0.0]

        # If we're reading orbitals, there could be multiple datasets
        # we read in the number of datasets and then need to read in as
        # many integers as there are datasets
        nfields = 1
        if orbitals:
            orbital_description = []
            
            tmp = fp.readline().split()
            
            nfields = int( tmp[0] ) # First item is # datasets
            
            for d in tmp[1:]:
                # Add remaining fields to the descriptions
                orbital_description.append( d )

            # Now keep looping till we've read as many descriptions
            # as there are datasets
            while len( orbital_description ) < nfields:
                descs = fp.readline().split()
                for d in descs:
                    orbital_description.append( d )

        # Create a list of fields to cycle through - for non-orbital
        # files there is only one
        fields = [ field ]

        # We only do this loop if we are reading an orbital file
        if orbitals:
            # Rename first field
            title = field.title
            fields[0].title = title+'_orbital_'+str( orbital_description[0] )

            # Duplicate the field so we have a list of fields to work with
            for i in range(nfields-1):
                new = copy.deepcopy( field )
                new.title = title+'_orbital_'+str(orbital_description[i+1])
                fields.append( new )

        # Now pull records off the file until all done
        for field_obj in fields:
            i = 0
            while i < ndata:
                line = fp.readline()
                if line == "":
                    print "Warning Incomplete Cube Data"
                    break
                values = line.split()
                for v in values:
                    #print "i ",i
                    field_obj.data[i] = float(v)
                    i = i + 1
                
        #return (mol,field)
        self.molecules.append( mol )
        self.fields = self.fields + fields

##########################################################
#
#
# Unittesting stuff goes here
#
#
##########################################################

# new file from: http://www.stolaf.edu/academics/chemapps/jmol/docs/examples-11/data/dxy.cube

class testCube_IO(unittest.TestCase):
    """Test whether we can read a Gau$$ian cube file"""

    reader = CubeIO()

    def testRead1(self):
        """ """
        
        fields = self.reader.GetObjects(
            filepath='/c/qcg/jmht/Documents/codes/OpenBabel/fileformats/cube/dxy.cube',
            otype = 'fields'
            )

        molecules = self.reader.GetObjects( 'molecules' )

        self.assertEqual( len(molecules[0].atom),7)
        self.assertEqual( len(fields[0].data),68921)

    def testRead2(self):
        """ """
        
        fields = self.reader.GetObjects(
            filepath='/c/qcg/jmht/Documents/codes/OpenBabel/fileformats/cube/phoh.cube',
            otype = 'fields'
            )

        molecules = self.reader.GetObjects( 'molecules' )

        self.assertEqual( len(molecules[0].atom),7)
        self.assertEqual( len(fields[0].data),68921)


#     def testReadOrbitals(self):
#         """ """
        
#         fields = self.reader.GetObjects(
#             filepath='/c/qcg/jmht/Documents/codes/OpenBabel/fileformats/cube/phoh.cube',
#             otype = 'fields'
#             )

#         molecules = self.reader.GetObjects( 'molecules' )

#         self.assertEqual( len(molecules[0].atom),13)
#         self.assertEqual( len(fields),25)

def testMe():
    """Return a unittest test suite with all the testcases that should be run by the main 
    gui testing framework."""

    return  unittest.TestLoader().loadTestsFromTestCase(testCube_IO)

        
if __name__ == "__main__":
    unittest.main()
