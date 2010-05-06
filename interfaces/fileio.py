#
#    This file is part of the CCP1 Graphical User Interface (ccp1gui)
# 
#   (C) 2002-2007 STFC Daresbury Laboratory
# 
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
# 
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
# 
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
"""
     
"""
import os,sys
if __name__ == "__main__":
    # Need to add the gui directory to the python path so 
    # that all the modules can be imported
    gui_path = os.path.split(os.path.dirname( os.path.realpath( __file__ ) ))[0]
    sys.path.append(gui_path)
else:
    from viewer.paths import gui_path

# import python modules
import re
import unittest

# import internal modules
import objects.zmatrix
import objects.vector
from objects.periodic import z_to_el, sym2no, name_to_element
from objects.zmatrix import Zmatrix

openbabel=None

class FileIO:
    """
    Base class for all the file readers/writers

    All IO objects that inherit from this one are required to supply the following:

    1. Set self.canRead to a boolean indicating if the object can read files
    2. Set self.canWrite to be a list of the classes of any objects that this writer can write
    files for
    3. Provide a _ReadFile method that opens the file and parses through it to create the lists
    of the various object types supported (e.g. molecules, fields, trajectories etc)
    4. Provide e.g. a _WriteMolecule method if the object an write out a molecule
       - writing out other types of file isnt' currently supported

    Once this has been done, the file getfileio.py should be edited to update the
    self.format_info attribute of the GetFileIO object so that we know what
    the capabilities of the different readers/writers are.

    The base class provides a number of things that should be useful to all the writers,
    in including attributes of the file (full path, name, extension etc
    - see self._ParseFilepath

    At the moment the assumption for reading is that the entire file is read in one pass and
    all objects returned together. It should be relatively simple to change things
    so that individual attributes can be returned without parsing the whole file
    if this becomes necessary.

    """

    def __init__(self, filepath=None, debug=None,**kw):
        """ Handle setting any data structures

        """
        self.debug = None
        if debug:
            self.debug=1

        # File variables
        self.filepath  = None
        self.directory = None
        self.filename  = None
        self.name      = None
        self.ext       = None


        if filepath:
            # Set the above structures from the filepath
            self._ParseFilepath( filepath )
        
        self.read = None # Indicate whether the file has been read - only need
                         # to do this once


        # List of which objects can be read/written by fileIO objects
        self.objectTypes = ['molecules',
                            'trajectories',
                            'vibrations',
                            'vibration_sets',
                            'fields',
                            'objects',
                            'bricks',
                            'matrices',
                            'lists'
                            ]

        # Now set as attributes of self
        for obj in self.objectTypes:
            setattr( self, obj, [] )

        # These define the read/write capabilities of these objects
        self.canWrite = []
        self.canRead = True
        

    def _ParseFilepath( self, filepath ):
        """ The IO objects all assume that the following attributes
            are present so that they can query them so this method
            sets these up
        """

        self.filepath = filepath
        self.directory,self.filename = os.path.split( self.filepath )
        self.name,ext = os.path.splitext( self.filename )
        self.ext = ext.lower()

    def CanRead( self ):
        """Return whether we can read this type of file"""

        return self.canRead

    def CanWrite( self, dataobj ):
        """
        Determine if we can write a particular file type
        """

        myclass = self.GetClass( dataobj )
        if myclass in self.canWrite:
            return True
        else:
            return False


    def GetObjects(self,otype=None, filepath=None, debug=None,**kw):
        """ Return any objects suitable for viewing
            If the otype argument is set, return only the object of the specified type

        """

        if debug:
            self.debug=1

        if not self.read:
            self.ReadFile( filepath=filepath,**kw )
        
        if otype:
            if hasattr( self, otype ):
                if self.debug: print "GetObjects returning objects for ",otype
                olist = getattr( self, otype )
                if len( olist ):
                    if self.debug: print "GetObjects returning objects for ",otype,olist
                    return olist
                else:
                    return None
        else:
            objects = []
            for o in self.objectTypes:
                if hasattr( self, o ):
                    ol = getattr( self, o )
                    if len( ol ):
                        objects += ol
                        
            if self.debug: print "GetObjects returning all objects",objects
            return objects
        
    def ReadFile(self, filepath=None, **kw ):
        """
        """
        if not self.read:
            if filepath:
                self._ParseFilepath( filepath )
                
            self._ReadFile(**kw)
            self.read = 1
        else:
            print 'skipping ',filepath,' as data loaded already'

    def _ReadFile( self, **kw):
        """
           Method to parse through a file and get objects - shouol be overloaded
           in any class that inherit from this
        """
        
        assert 0!=0, "FileIO _readfile should have been overloaded."

    def WriteFile( self, dataobj, filepath=None, format=None,**kw ):
        """ Write out object to a file
            Select the correct writer for this type of object
            If the filepath argument is supplied, set up the correct
            path to the file
            format can be used to set the format of the file form those
            IO objects that support multiple ones
        """

        if filepath:
            # Set up file data structures needed by the IO ojbects
            self._ParseFilepath( filepath )

        # Set self.format
        if format:
            self.format = format
            
        myclass = self.GetClass( dataobj )

        if myclass == 'Indexed' or myclass == 'Zmatrix':
            self.WriteMolecule( dataobj, **kw )
            
        elif myclass == 'VibFreqSet' :
            pass
            
        elif myclass == 'VibFreq':
            pass
            
        elif myclass == 'ZmatrixSequence':
            pass
        
        elif myclass == 'Brick':
            pass
            
        elif myclass == 'Field':
            pass
            
        else:
            print "WriteFile unknown class ",myclass

    def WriteMolecule( self, molecule, **kw ):
        """
        Write out a molecule to file - currently just calls _WriteMolecule
        which should have been overloaded
        """
        self._WriteMolecule( molecule, **kw )

    def _WriteMolecule( self, molecule, **kw ):
        """
        Write out a molecule to file
        """
        assert 0!=0, "FileIO _WriteMolecule should have been overloaded."


    def GetClass(self,object):
        """ Return an object's class
             take the last field of the class specification
        """
        t1 = str(object.__class__).split('.')
        myclass = t1[len(t1)-1]
        return myclass


###############################################################################
#
# Readers below here
#
###############################################################################

# Old readers
"""
 form == 'dlphist':
objs = self.rdhist(filename)
elif form == 'XYZ_seq':
    objs = self.rdxyz(fileh,root,sequence=1)
elif form == 'GAU':
    objs = self.rdgjf(fileh,root)
else:


"""

class CML_IO(FileIO):
    """
    Writer for CML
        
    """
    
    def __init__(self,**kw):
        """ Set up the structures we need
        """

        # Initialise base class
        FileIO.__init__(self,**kw)

        # capapbilties
        self.canRead = True
        self.canWrite = [ 'Zmatrix','Indexed' ]

    def _ReadFile(self,format=None):
        """ Read the file and return the molecule(s)"""
        model = Zmatrix()
        model.rdcml(self.filepath)
        self.molecules.append(model)

    def _WriteMolecule(self,molecule,**kw):
        """
        """

        if molecule.title:
            title = molecule.title
        else:
            title = self.name
            
        molecule.wrtcml( self.filepath, title=title )


class OpenBabelIO(FileIO):
    """
     A reader for all the filetypes supported by OpenBabel
    """

    def __init__(self, filepath=None,format=None,desc2OBfmt=None,**kw):
        """ Set up the structures we need

        """


        # Initialise base class
        FileIO.__init__(self,filepath,**kw)

        
        #if not format:
        #    raise AttributeError,"OpenBabelReader needs a format keyword!"
        #else:
        #    self.format = format
        
        self.format=None
        if format:
            self.format=format

        # Need to set these as global as we import them here
        #global openbabel,pybel
        global openbabel
        # Don't trap import errors as we should only get here if we've got OB
        #import openbabel,pybel
        import openbabel

        # Dictionary with mapping our format -> OBformat (see getfileio.py)
        self.desc2OBfmt = desc2OBfmt
        
#         # Get the supported input & output formats and combine
#         # into a single dictionary
#         formats = pybel.informats
#         formats.update(pybel.outformats)
#         # Key the dictionary by the values
#         newd = [(v, k) for k, v in formats.items()]
#         self.format = dict( newd )
#         # A key error here indicates something has gone wrong in
#         # interfaces/getreader.py ( see __init__ of GetReader class )
#         self.babelID = newd[format]

        # get the OBConv object
        self.OBConv = openbabel.OBConversion()

        # State what we can read and write
        self.canRead = True
        self.canWrite = [ 'Zmatrix','Indexed' ]


    def _ReadFile(self,format=None):
        """ Read the file and return the molecule(s)"""

        if format:
            self.format=format
            
        if not self.format:
            raise Exception,"OpenBabel _ReadFile no format set!"

        format = self.desc2OBfmt[ self.format ]
        # Need to remove the dot
        format = format[1:]
        
        ok = self.OBConv.SetInFormat( format )
        if not ok:
            raise Exception,"OpenBabelReader could not set input format to: %s" % format
        elif self.debug:
            print "OpenBabel _ReadFile set input format to ",format
        OBmol = openbabel.OBMol()
        
        notatend = self.OBConv.ReadFile( OBmol, self.filepath )
        
        while notatend:

            # Check we've got a valid molecule back
            natom = OBmol.NumAtoms()
            if not natom:
                notatend = False
                break
            
            mol = objects.zmatrix.Zmatrix()
            mol.title = self.name 
            mol.name = OBmol.GetTitle()

            for i in range( natom ):
                
                OBatom = OBmol.GetAtom( i+1 )
                atom = objects.zmatrix.ZAtom()

                Z = OBatom.GetAtomicNum()
                #print "z is ",Z
                
                element = z_to_el[ Z ]
                atom.symbol = element
                atom.name = element
                #print OBatom.GetType()
                atom.coord = [ OBatom.x(), OBatom.y(),OBatom.z() ]
                #print "coords are ",atom.coord

                mol.atom.append( atom )

            #print "iterating over bonds"
            for bond in openbabel.OBMolBondIter( OBmol ):
                i1 = bond.GetBeginAtomIdx()
                i1=i1-1 # Decrement index
                i2 = bond.GetEndAtomIdx()
                i2=i2-1 # Decrement index
                #print bond.GetBondOrder()
                b = objects.zmatrix.Bond()
                b.index=[i1, i2]
                mol.bond.append( b )
                
            mol.update_conn()
            self.molecules.append( mol )
            
            OBmol = openbabel.OBMol()
            notatend = self.OBConv.Read( OBmol )


# Below is currently broken for NW-Chem and Gaussian readers
#         molecules = [ mol for mol in pybel.readfile( self.babelID, self.filepath ) ]

#         print "OpenBabel got molecules ",molecules

#         for PMol in molecules:

#             print "OpenBabel processsing molecule ",PMol

#             # NB pybel returns it's own wrapper version of OBMol (called PMol here),
#             # so standard methods do not work with it. The original OBMol can be
#             # accessed through the OBMol attribute of the returned molecule

#             # Create a CCP1GUI molecule
#             mol = objects.zmatrix.Zmatrix()
#             mol.name = self.name

#             for OBAtom in PMol.atoms:

#                 # Ignore the pybel convenience class Atom and get
#                 # the original OBAtom atom
#                 OBAtom = OBAtom.OBAtom

#                 #print "OpenBabel got atom ",OBAtom

#                 # Create a CCP1GUIAtom
#                 atom = objects.zmatrix.ZAtom()
            
#                 Z = OBAtom.GetAtomicNum()
#                 #print "z is ",Z
#                 element = z_to_el[ Z ]
#                 atom.symbol = element
#                 atom.name = element
#                 #print OBatom.GetType()
#                 atom.coord = [ OBAtom.x(), OBAtom.y(),OBAtom.z() ]
#                 #print "coords are ",atom.coord
#                 mol.atom.append( atom )

#             self.molecules.append( mol )

    def _WriteMolecule(self,molecule,format=None):
        """  Write out the molecule """

        if format:
            self.format=None
            
        if not self.format:
            raise Exception,"OpenBabel _WriteMolecule format not set!"
        
        format = self.desc2OBfmt[ self.format ]
        # Need to remove the dot
        format = format[1:]
        ok = self.OBConv.SetOutFormat( format )
        if not ok:
            raise Exception,"OpenBabel _Write Molecule could not set output format to: %s" % format

        # Create an OpenBabel molecule from the ZMatrix one
        OBmol = openbabel.OBMol()

        OBmol.SetTitle( molecule.name )

        for atom in molecule.atom:
            #idx = atom.get_index()
            OBAtom = OBmol.NewAtom()
            OBAtom.SetAtomicNum( sym2no[ atom.symbol ] )
            OBAtom.SetVector( atom.coord[0],atom.coord[1],atom.coord[2])


        # Now add bonds (we assume that the atoms come out in the order
        # they are indexed, which appears to be correct).
        for atom in molecule.atom:
            idx1 = atom.get_index() + 1
            for conn in atom.conn:
                 idx2 = conn.get_index() + 2
                 print idx1,idx2
                 # Assume bond order of 1
                 OBmol.AddBond( idx1, idx2, 1 )

        ok = self.OBConv.WriteFile( OBmol, self.filepath )
        if not ok:
            raise Exception,"OpenBabel _Write Molecule could not write file: %s" % format
        
class PDB_IO(FileIO):
    """
     A reader for a PDB files
    """

    def __init__(self, filepath=None,**kw):
        """ Set up the structures we need

        """

        from Scientific.IO import PDB

        # Initialise base class
        FileIO.__init__(self,filepath=filepath,**kw)

        # List which types of object we can read/write
        self.canRead = True
        self.canWrite = [ 'Indexed', 'Zmatrix' ]



    def _ReadFile(self):
        """ Read the file and return the molecule(s)"""


        model = objects.zmatrix.Zmatrix()
        model.title = self.name
        model.name = self.name


        conf = PDB.Structure(self.filepath)
        #print conf
        i=0
        import string
        trans = string.maketrans('a','a')
        for residue in conf.residues:
            for atom in residue:
                #print atom
                atsym = atom.name

                x = atom.position[0]
                y = atom.position[1]
                z = atom.position[2]
                # atno = Element.sym2no[atsym]
                a = objects.zmatrix.ZAtom()
                a.coord = [x,y,z]

                #print atsym

                try:
                    # for newer versions of Scientific
                    a.symbol = atom['element']
                except KeyError:
                    try:
                        txt_type = string.strip(atsym)
                        txt_type = string.upper(txt_type)
                        #print 'trying to map',atsym
                        a.symbol = map[txt_type]
                        #print 'done',a.symbol
                        #a.name = a.symbol + string.zfill(i+1,2)
                    except KeyError:
                        a.symbol = string.translate(atsym,trans,string.digits)
                        a.symbol = string.capitalize(a.symbol)

                if 0:
                    a.name = atsym
                else:
                    a.name = a.symbol + string.zfill(i+1,2)
                model.atom.append(a)
                #print 'get number', a.symbol, a.get_number()
                i=i+1

        self.molecules.append( model )

    def _WriteMolecule(self,molecule):
        """PDB reader, based on Konrad Hinsens Scientific Python"""

        pdbf = PDB.PDBFile(self.filepath,mode='w')
        for atom in molecule.atom:
            d = { 'position': atom.coord, 'name' : atom.name }
            pdbf.writeLine('ATOM',d)


class MDL_IO(FileIO):
    """ IO object for an MDL mol file - see:
         http://www.eyesopen.com/docs/html/smack/node13.html
    """
    
    def __init__(self,**kw):
        """ Set up the structures we need
        """

        # Initialise base class
        FileIO.__init__(self,**kw)

        # capapbilties
        self.canRead = True
        #self.canWrite = [ 'Zmatrix','Indexed' ]


    def _ReadFile(self):
        """Read in a small molecule from a file in MDL .mol file format. This reader
        has been constructed from the information found at:
        http://www.eyesopen.com/docs/html/smack/node13.html
        If this reader doesnt work it is almost certainly THEIR problem not MINE...
        """


        f = open( self.filepath, 'r' )

        #Header block contains 3 lines: name, info & a comment - only need the name if present
        molname = self.name
        line = f.readline().strip()
        if line:
            #molname = string.split(line)[0]
            molname = line.split(line)[0]

        # set up the model
        model = objects.zmatrix.Zmatrix()
        model.title = molname
        model.name = molname

        # Skip the other two header lines
        f.readline()
        f.readline()

        # Now read in # of molecules and bonds
        line = f.readline()
        try:
            natoms = int( line[0:3] )
            nbonds = int( line[4:6] )
        except:
            print "Error reading in # of atoms and bonds in MOL_IO!"
            return

        # Now cycle over the atom block reading in the coordinates
        atom_count = 0
        while ( atom_count < natoms ):
            line = f.readline()
            if ( not line or ( len(line) < 39 )  ):
                print "Error reading in atoms in MOL_IO!"
                return
            try:
                x = float( line[0:9] )
                y = float( line[10:19] )
                z = float( line[20:29] )
                #jmht hack
                #symbol = string.strip( line[31:33] )
                #symbol = string.strip( line[31:34] )
                symbol = line[31:34].strip()
                charge = int( line[35:37] )
            except:
                print "Error reading atom line in MOL_IO!"

            a = objects.zmatrix.ZAtom()
            a.coord = [ x, y, z ]
            #a.symbol = string.capitalize(symbol)
            a.symbol = symbol.capitalize()
            #a.name = a.symbol + string.zfill(atom_count+1,2)
            a.name = a.symbol + str(atom_count+1).zfill(2)
            model.atom.append(a)
            atom_count += 1

        # Index the model or adding bonds wont work
        model.reindex()

        # Now read in the bond block
        bond_count = 0
        while ( bond_count < nbonds ):
            line = f.readline()
            if ( not line or ( len(line) < 9 )  ):
                print "Error reading in bonds in MOL_IO!"
                return
            try:
                i1 = int( line[0:3] )
                i2 = int( line[4:6] )
                bond_order = int( line[7:9] )
            except:
                print "Error reading bond line in MOL_IO!"

            atom1 = model.atom[i1-1] # Rem we index from 0 , they start at 1
            atom2 = model.atom[i2-1]
            model.add_bond( atom1, atom2 )
            bond_count += 1

        f.close()
        
        self.molecules.append( model )

class MSICeriusII_IO(FileIO):
    """
    MSI CERIUS2 DataModel File Version 4 0
        
    """
    
    def __init__(self,**kw):
        """ Set up the structures we need
        """

        # Initialise base class
        FileIO.__init__(self,**kw)

        # capapbilties
        self.canRead = False
        self.canWrite = [ 'Zmatrix','Indexed' ]


    def _WriteMolecule(self,molecule,**kw):
        """
        """

        molecule.wrtmsi( self.filepath )
        

class SHELXTL_IO(FileIO):
    """
    Write a SHELXTL .res  file

    """

    def __init__(self, filepath=None,**kw):
        """ Set up the structures we need

        """

        # Initialise base class
        FileIO.__init__(self,filepath=filepath,**kw)

        # List which types of object we can read/write
        self.canRead = False
        self.canWrite = [ 'Zmatrix','Indexed' ]

    def _WriteMolecule( self, molecule, **kw ):

        if molecule.title:
            title = molecule.title
        else:
            title = self.name
            
        molecule.wrtres( self.filepath, title=title )


class SpartanInputIO(FileIO):
    """
    Class for Spartan input files

    """
    def __init__(self, filepath=None,**kw):
        """ Set up the structures we need

        """

        # Initialise base class
        FileIO.__init__(self,filepath=filepath,**kw)

        # List which types of object we can read/write
        self.canRead = True
        self.canWrite = [  ]

    def _ReadFile(self):
        """ V. basic reader for spartan input files written only having seen 2 files
            Assumes that the format of the files is:
            3 or 4 (for us) uniteresting lines followed by a line with the charge & spin then a
            sequence of lines each of which is charge, x, y, z terminated by a line
            with ENDCAR
            There may then be an optional block starting with the line "ATOMLABELS"
            that contains a list of the names for the previously read in atoms with one
            label per atom
        """
        
        f = open(self.filepath,'r')

        #Read 1st 3 lines
        for i in range(3):
            line = f.readline()

        # Check if this is the charge/spin line 
        fields = line.split()
        if len(fields) != 2:
            # line is not charge/spin so skip to next
            line = f.readline()

        # read in initial coordinates
        natom = 0
        atoms_read = [] # list - each item is list [ tag, charge, x, y, z ]
        while 1:
            line = f.readline()
            if not len(line):
                # EOF
                print "rdsptn: EOF before ENDCART label!"
                break
            
            line = line.strip()
            if len(line) >= 7 and line[0:7] == 'ENDCART':
                # End of coordinates
                break

            fields = line.split()
            # Each line should be charge, x, y, z
            if len(fields) >= 4:
                try:
                    atoms_read.append( [ None,
                                       int(fields[0]),
                                       float(fields[1]),
                                       float(fields[2]),
                                       float(fields[3]) ])
                except Exception,e:
                    print "rdsptn: error reading coords!\nLine was: %s\nError:%s" % (line,e)
                    break
                natom+=1 # incrememt atom counter
            else:
                print "rdsptn: invalid coord line?: %s" % line


        # Now check for labels
        labels = None
        while 1:
            line = f.readline()
            if not len(line):
                # EOF
                print "rdsptn: EOF before got labels"
                break
            
            line = line.strip()

            if len(line) >= 10 and line[0:10] == 'ATOMLABELS':
                labels = 1
                # found labelsblock
                break

        # Loop over labels
        if labels:
            for i in range( natom ):
                line = f.readline()
                if not len(line):
                    # EOF
                    print "rdsptn: EOF before all atom labels read in"
                    break
            
                line = line.strip()

                if len(line) >= 13 and line[0:13] == 'ENDATOMLABELS':
                    print "rdsptn: got end labels early!"
                    # End of coordinates
                    break

                line = line.strip('"') # Remove quotes around label
                atoms_read[i][0] = line

        # Now loop over the read in atoms and create the atom objects
        mol = objects.zmatrix.Zmatrix()
        mol.name = self.name
        mol.title = self.name

        for a in atoms_read:
            atom = objects.zmatrix.ZAtom()
            charge = a[1]
            if a[0]:
                # Read in label
                tag = a[0]
            else:
                # Determine label from charge
                tag = z_to_el[charge]

            atom.name = tag
            atom.symbol = z_to_el[charge]
            atom.formal_charge = charge
            atom.coord = [a[2],a[3],a[4] ]
            mol.atom.append( atom )

        self.molecules.append( mol )



class VTK_IO(FileIO):
    """ IO object for VTK data files
    """
    
    def __init__(self,**kw):
        """ Set up the structures we need
        """

        global vtk
        import vtk
        
        # Initialise base class
        FileIO.__init__(self,**kw)

        # capapbilties
        self.canRead = True
        #self.canWrite = [ 'Zmatrix','Indexed' ]


    def _ReadFile(self,**kw):
        """Read in a VTK data structure from a vtk data file
        """


        fd = open( self.filepath, 'r' )
        
        # Instantiate the field object
        field = objects.field.Field()
        
        reader = vtk.vtkDataSetReader()
        reader.SetFileName(self.filepath)
        #field.vtkdata = reader.GetStructuredPointsOutput()

        data = reader.GetOutput()
        if not data:
            raise Exception,"VTK_IO no data found while reading file: %s" % self.filepath

        if not data.GetClassName() == 'vtkStructuredPoints':
            raise Exception,"VTK_IO someone needs to tell me how to read something other than Stuctured Points!"


        field.dim = data.GetDimensions()
        #print data.GetDataDimension()
        origin =  data.GetOrigin()
        field.origin = objects.vector.Vector( origin )
        
        field.vtkdata = data
        field.title = self.name
        field.name = self.name
        self.fields.append(field)


class XYZ_IO(FileIO):
    """
    Class for MDL xyz format

    """
    def __init__(self,**kw):
        """ Set up the structures we need

        """

        # Initialise base class
        FileIO.__init__(self,**kw)

        # capapbilties
        self.canRead = True
        self.canWrite = [ 'Zmatrix','Indexed' ]


    def _ReadFile(self,sequence=None):
        """ Read in cartesian coordinates in XMOL .xyz file format.
            The xyz format can contain multiple frames so we need to
            check if we have come to the end of one frame and need to
            start another
            The optional sequence flag indicates if we should create a
            ZmatrixSequence of the molecules in the file
        """

        fd = open( self.filepath, 'r' )
        
        if sequence:
            ZmatSeq = objects.zmatrix.ZmatrixSequence()

        finished = 0
        line = fd.readline()
        while( not finished ): # loop to cycle over all the frames
            words = line.split()

            # First word specifies the number of atoms
            try:
                natoms = int(words[0])
            except:
                finished = 1
                break

            model = objects.zmatrix.Zmatrix()
            #model.title = self.
            model.name = self.name

            line = fd.readline() # First line is a comment so ignore it
            for i in range(natoms):
                line = fd.readline()

                # Make sure we got something to read...
                if not line:
                    print "Error reading coordinates in rdxyz!"
                    finished = 1
                    break
                    
                # Check we are not at the end of the current frame
                words = line.split()
                if ( len( words ) != 4 ):
                    print "Error reading coordinates in rdxyz!"
                    print "Offending line is: %s" % line
                    break # jump out of for loop and start next cycle
                
                atsym = words[0]
                try:
                    x = float(words[1])
                    y = float(words[2])
                    z = float(words[3])
                    a = objects.zmatrix.ZAtom()
                    a.coord = [x,y,z]
                    a.symbol = name_to_element( words[0] )
                    #a.name = a.symbol + string.zfill(i+1,2)
                    a.name = a.symbol + str(i+1).zfill(2)
                    model.atom.append(a)
                except:
                    print "Error reading coordinates in rdxyz!"
                    print "Offending line is: %s" % line
                    break # jump out of for loop and start next cycle

            if sequence:
                ZmatSeq.add_molecule(model)
            else:
                self.molecules.append( model )
                
            # Go back to top of while loop with next line
            line = fd.readline()

        if sequence:
            ZmatSeq.connect()
            # Name the sequence after the first molecule
            ZmatSeq.name = ZmatSeq.frames[0].name
            self.trajectories.append( ZmatSeq )

    def _WriteMolecule( self, molecule ):
        """ Write out the molecule as an xyz file """

        fd = open( self.filepath, 'w' )
        natoms = len(molecule.atom)

        # Get a title
        title = molecule.title
        if not title:
            title = molecule.name
        if not title:
            title = self.name

        # First line is natoms
        fd.write("%s\n" % natoms )
        # then title
        fd.write("%s\n" % title )

        # Loop over atoms writing symbol & coordinates
        for atom in molecule.atom:
            s = atom.symbol
            x = atom.coord[0]
            y = atom.coord[1]
            z = atom.coord[2]
            fd.write("%s    %s    %s    %s\n" % (s,x,y,z) )
        
        fd.close()
            
        
class ZmatrixIO(FileIO):
    """
     A reader for a zmatrix file
    """

    def __init__(self,**kw):
        """ Set up the structures we need

        """

        # Initialise base class
        FileIO.__init__(self,**kw)

        # capapbilties
        self.canRead = True
        self.canWrite = [ 'Zmatrix','Indexed' ]


    def _ReadFile(self):
        """ Read the file and return the molecule(s)"""

        mol = objects.zmatrix.Zmatrix(file=self.filepath)
        mol.title = self.name
        mol.name = self.name
        self.molecules.append( mol )

    def _WriteMolecule( self, molecule ):
        """ Write out the molecule as a zmatrix """

        txt = molecule.output_zmat()
        fobj = open(self.filepath,'w')
        for rec in txt:
            fobj.write(rec + '\n')
        fobj.close()


##########################################################
#
#
# Unittesting stuff goes here
#
#
##########################################################


class IOTestCase(unittest.TestCase):
    """Base class - might come in useful later and save lots of typing..."""

    # So that all tests can find the examples directory
    egdir = egdir=gui_path+os.sep+'examples'+os.sep
    
    def getMolecule(self):
        """ Return a molecule suitable for testing the writers - could
            just read one in, but this way we have more control over
            exactly what the molecule contains
        """

        molecule = objects.zmatrix.Zmatrix()
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
            atom = objects.zmatrix.ZAtom()
            x = float( d[0] )
            y = float( d[1] )
            z = float( d[2] )
            atom.coord = [ x,y,z ]
            atom.name = d[3]
            atom.symbol = d[4]
            molecule.add_atom( atom )
            
        return molecule
        

class testCML(IOTestCase):

    """Test whether we deal with a CML file"""

    def setUp(self):
        """Set the reader for all these filetypes"""
        self.reader = self.writer = CML_IO()

    def testRead(self):
        """CML Reader Test"""
        fil=self.egdir+'caffeine.cml'
        molecules = self.reader.GetObjects(filepath=fil,otype = 'molecules')
        self.assertEqual( len(molecules[0].atom),14)

    def testWrite(self):
        """CML Writer Test"""
        mol = self.getMolecule()
        filepath = os.getcwd()+'/test.cml'
        self.writer.WriteFile( mol, filepath=filepath )
        statinfo = os.stat( filepath )
        self.assertEqual( statinfo.st_size,1141)
        os.remove( filepath )


class testMDL_IO(IOTestCase):
    """Test whether we deal with MDL mol file"""

    def setUp(self):
        """Set the reader for all these filetypes"""        
        self.reader = MDL_IO()

    def testRead(self):
        """ """

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
        self.writer = MSICeriusII_IO()

    def testWrite(self):
        """ """
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
        self.IO = PDB_IO()

    def testRead(self):
        """ """

        molecules = self.IO.GetObjects(
            filepath='/c/qcg/jmht/Documents/codes/OpenBabel/fileformats/pg_kaptein1.pdb',
            otype = 'molecules'
            )

        # Should return 1929 atoms
        self.assertEqual( len(molecules[0].atom),1929)

    def testWrite(self):
        """ """

        mol = self.getMolecule()

        filepath = os.getcwd()+'/test.pdb'
        self.IO.WriteFile( mol, filepath=filepath )

        statinfo = os.stat( filepath )
        self.assertEqual( statinfo.st_size,1009)
        os.remove( filepath )

class testSHELXTL_IO(IOTestCase):
    """Test whether we deal with a shelxtl .res file"""

    def setUp(self):
        """Set the reader for all these filetypes"""
        self.writer = SHELXTL_IO()

    def testWrite(self):
        """ """

        mol = self.getMolecule()

        filepath = os.getcwd()+'/test.res'
        self.writer.WriteFile( mol, filepath=filepath )

        statinfo = os.stat( filepath )
        self.assertEqual( statinfo.st_size,840)
        os.remove( filepath )


class testSpartanInputIO(IOTestCase):
    """Test whether we deal with Spartan input data"""

    def setUp(self):
        """Set the reader for all these filetypes"""
        self.reader = SpartanInputIO()

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
        self.reader = VTK_IO()

    def testScalarRead(self):
        """ read in scalar data
        """

        fields = self.reader.GetObjects(
            filepath='/home/jmht/VTK/VTKData/Data/ironProt.vtk',
            otype = 'fields'
            )

        self.assertEqual( fields[0].dim[0] , 68)

class testXYZ_IO(IOTestCase):
    """Test whether we deal with VTK data"""

    def setUp(self):
        """Set the reader for all these filetypes"""
        self.reader = XYZ_IO()

    def testRead(self):
        """ read in scalar data
        """

        molecules = self.reader.GetObjects(
            filepath='/c/qcg/jmht/Documents/codes/OpenBabel/fileformats/toluene.xyz',
            otype = 'molecules'
            )

        self.assertEqual( len(molecules[0].atom) , 15)


class testZmatrixIO(IOTestCase):
    """Test whether we deal with Zmatrix data"""

    def setUp(self):
        """Set the reader for all these filetypes"""
        self.reader = ZmatrixIO()

    def testRead(self):
        """ read in a zmatrix
        """

        molecules = self.reader.GetObjects(
            filepath=self.egdir+'feco5.zmt',
            otype = 'molecules'
            )

        self.assertEqual( len(molecules[0].atom) , 16)


if openbabel:
    class testOpenBabel_IO(IOTestCase):
        """Test whether we deal with the openbabel interface
           If it is some of the other tests will fail as the file
           sizes written out by different readers for (e.g. pdb) vary
           This is on the list of things to sort out...
        """

        def setUp(self):
            """Set the reader for all these filetypes"""

            getIO = GetFileIO()
            self.IO = getIO.GetOpenBabelIO( )

        def testReadPDB(self):
            """ read in a PDB  FIle
            """

            molecules = self.IO.GetObjects(
                format='Protein Data Bank format',
                filepath=self.egdir+'caffeine.pdb',
                otype = 'molecules'
                )

            self.assertEqual( len(molecules[0].atom) , 24)

def testMe():
    """Return a unittest test suite with all the testcases that should be run by the main 
    gui testing framework."""

    suite =  unittest.TestLoader().loadTestsFromTestCase(testMDL_IO)
    suite.addTests( unittest.TestLoader().loadTestsFromTestCase(testMSICeriussII_IO) )
    suite.addTests( unittest.TestLoader().loadTestsFromTestCase(testPDB_IO) )
    suite.addTests( unittest.TestLoader().loadTestsFromTestCase(testSHELXTL_IO) )
    suite.addTests( unittest.TestLoader().loadTestsFromTestCase(testSpartanInputIO) )
    #suite.addTests( unittest.TestLoader().loadTestsFromTestCase(testVTK_IO) )
    suite.addTests( unittest.TestLoader().loadTestsFromTestCase(testXYZ_IO) )
    suite.addTests( unittest.TestLoader().loadTestsFromTestCase(testZmatrixIO) )
    return suite


if __name__ == "__main__":


    unittest.main()

    #root = "/home/jmht/Documents/codes/OpenBabel/fileformats/"
    #testcases = [
    #    root+'pg_kaptein1.pdb',
    #    root+'optim_c6h6.nwo',
    #    root+'Samples.sdf',
    #    root+'CChol_HF_631Gd_freq.log',
    #    root+'gamessuk.out',
    #    
    #    ]
