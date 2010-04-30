"""CHARMM interface routines.
At present this is limited to support for reading in .crd format files.
"""
import os,sys
if __name__ == "__main__":
    # Need to add the gui directory to the python path so 
    # that all the modules can be imported
    gui_path = os.path.split(os.path.dirname( os.path.realpath( __file__ ) ))[0]
    sys.path.append(gui_path)

import unittest
import string
import objects.zmatrix

from interfaces.fileio import FileIO
from objects.periodic import sym2no

charmm_map = {}

charmm_map['N'] = 'N'
charmm_map['NE'] = 'N'
charmm_map['ND1'] = 'N'
charmm_map['ND2'] = 'N'
charmm_map['NH1'] = 'N'
charmm_map['NH2'] = 'N'
charmm_map['NE'] = 'N'
charmm_map['NE1'] = 'N'
charmm_map['NE2'] = 'N'
charmm_map['NZ'] = 'N'

charmm_map['O'] = 'O'
charmm_map['O1'] = 'O'
charmm_map['O2'] = 'O'
charmm_map['O3'] = 'O'
charmm_map['O4'] = 'O'
charmm_map['O5'] = 'O'
charmm_map['O6'] = 'O'
charmm_map['OD1'] = 'O'
charmm_map['OD2'] = 'O'
charmm_map['OG'] = 'O'
charmm_map['OG1'] = 'O'
charmm_map['OE'] = 'O'
charmm_map['OE1'] = 'O'
charmm_map['OE2'] = 'O'
charmm_map['OH'] = 'O'
charmm_map['OH1'] = 'O'
charmm_map['OH2'] = 'O'

charmm_map['OCT1'] = 'O'        
charmm_map['OCT2'] = 'O'        
charmm_map['OT1'] = 'O'        
charmm_map['OT2'] = 'O'        

charmm_map['C'] = 'C'
charmm_map['C1'] = 'C'
charmm_map['C2'] = 'C'
charmm_map['C3'] = 'C'
charmm_map['CA'] = 'C'
charmm_map['CB'] = 'C'
charmm_map['CD'] = 'C' 
charmm_map['CD'] = 'C' 
charmm_map['CD1'] = 'C' 
charmm_map['CD2'] = 'C' 

charmm_map['CE'] = 'C' 
charmm_map['CE1'] = 'C' 
charmm_map['CE2'] = 'C' 
charmm_map['CE3'] = 'C' 

charmm_map['CG'] = 'C'
charmm_map['CG1'] = 'C'
charmm_map['CG2'] = 'C'

charmm_map['CH'] = 'C'
charmm_map['CH1'] = 'C'
charmm_map['CH2'] = 'C'

charmm_map['CZ'] = 'C'
charmm_map['CZ1'] = 'C'
charmm_map['CZ2'] = 'C'
charmm_map['CZ3'] = 'C'

charmm_map['H'] = 'H'

charmm_map['H1'] = 'H'
charmm_map['H2'] = 'H'
charmm_map['H3'] = 'H'
charmm_map['H4'] = 'H'
charmm_map['H5'] = 'H'
charmm_map['HA'] = 'H'
charmm_map['HA1'] = 'H'
charmm_map['HA2'] = 'H'
charmm_map['HB'] = 'H'
charmm_map['HB1'] = 'H'
charmm_map['HB2'] = 'H'
charmm_map['HB3'] = 'H'
charmm_map['HD1'] = 'H'
charmm_map['HD11'] = 'H'
charmm_map['HD2'] = 'H'
charmm_map['HD3'] = 'H'
charmm_map['HD12'] = 'H'
charmm_map['HD13'] = 'H'
charmm_map['HD21'] = 'H'
charmm_map['HD22'] = 'H'
charmm_map['HD23'] = 'H'

charmm_map['HE'] = 'H'
charmm_map['HE1'] = 'H'
charmm_map['HE2'] = 'H'
charmm_map['HE3'] = 'H'
charmm_map['HE21'] = 'H'
charmm_map['HE22'] = 'H'

charmm_map['HG'] = 'H'
charmm_map['HG1'] = 'H'
charmm_map['HG2'] = 'H'
charmm_map['HG3'] = 'H'

charmm_map['HG11'] = 'H'
charmm_map['HG12'] = 'H'
charmm_map['HG13'] = 'H'
charmm_map['HG21'] = 'H'
charmm_map['HG22'] = 'H'
charmm_map['HG23'] = 'H'

charmm_map['HH'] = 'H'
charmm_map['HH1'] = 'H'
charmm_map['HH2'] = 'H'

charmm_map['HG'] = 'H'

charmm_map['HO1'] = 'H'
charmm_map['HO2'] = 'H'
charmm_map['HO3'] = 'H'
charmm_map['HO4'] = 'H'
charmm_map['HO5'] = 'H'
charmm_map['HO6'] = 'H'

charmm_map['HZ'] = 'H'
charmm_map['HZ1'] = 'H'
charmm_map['HZ2'] = 'H'
charmm_map['HZ3'] = 'H'

charmm_map['HT1'] = 'H'
charmm_map['HT2'] = 'H'
charmm_map['HT3'] = 'H'

charmm_map['HH11'] = 'H'
charmm_map['HH12'] = 'H'
charmm_map['HH21'] = 'H'
charmm_map['HH22'] = 'H'

charmm_map['HN'] = 'H'

charmm_map['P'] = 'P'
charmm_map['SG'] = 'S'
charmm_map['SD'] = 'S'
charmm_map['ZN'] = 'ZN'
charmm_map['CU'] = 'CU'


class CRDReader(FileIO):

    """Reader for CHARMM .CRD files

        The CARD file format is the standard means in CHARMM for
        providing a human readable and write able coordinate file. The
        format is as follows:

        TITLE (a line starting with "*")
        NATOM (I5)
        ATOMNO RESNO   RES  TYPE  X     Y     Z   SEGID RESID Weighting
        I5    I5  1X A4 1X A4 F10.5 F10.5 F10.5 1X A4 1X A4 F10.5

        The TITLE is a title for the coordinates, Next comes the
        number of coordinates. If this number is zero or too large,
        the entire file will be read.

        Finally, there is one line for each coordinate. ATOMNO gives
        the number of the atom in the file. It is ignored on
        reading. RESNO gives the residue number of the atom. It must
        be specified relative to the first residue in the PSF. The
        OFFSet option should be specified if one wishes to read
        coordinates into other positions. It should also be remembered
        that for card images, residues are identified by RESIDUE
        NUMBER. This number can be modified by using the OFFSet
        feature, which allows coordinates to be read from a different
        PSF. Both positive and negative values are allowed. The RESId
        option will cause the residue number field to be ignored and
        map atoms from SEGID and RESID labels instead.

        RES gives the residue type of the atom. RES is checked against
        the residue type in the PSF for consistency. TYPE gives the
        IUPAC name of the atom. The coordinates of an atom within a
        residue need not be specified in any particular order. A
        search is made within each residue in the PSF for an atom
        whose IUPAC name is given in the coordinate file.  The RESId
        option overrides the residue number and fills coordinates
        based on the SEGID and RESID identifiers in the coordinate
        file

        If the title contains the string replica, a separate molecule
        will be generated for each of the unique segids

        """


    def __init__(self,**kw):

        # Initialise base class
        FileIO.__init__(self,**kw)
        
        self.debug = 0
        
        # capabilties
        self.canRead = True
        self.canWrite = [ 'Zmatrix','Indexed' ]


#    def __init__(self,filename,filepointer=None,root="Untitled",map=charmm_map):
    def _ReadFile(self,**kw):

        old_segid='X99'
        #self.objects = []
        replica = 0
        
        trans = string.maketrans('a','a')

        #if filepointer:
        #    file=filepointer
        #else:
        #    file=open(filename,"r")
        #    words = string.split(filename,'.')
        #    root = words[0]
        file = open( self.filepath, 'r' )

        while 1:
            model = None
            line = file.readline()
            if line == "":
                break
            while 1:
                #print line
                if line[0] == '*':
                    if (line.find("replica") != -1 or \
                        line.find("REPLICA") != -1):
                        replica = 1
                    line = file.readline()                
                else:
                    break

            words = string.split(line)
            nat = eval(words[0])
            #print 'NAT', nat
            rdnat = 0

            for i in range(0,nat):

                line = file.readline()
                if not line: break

                #ATOMNO RESNO   RES  TYPE  X     Y     Z   SEGID RESID Weighting
                #I5    I5  1X A4 1X A4 F10.5 F10.5 F10.5 1X A4 1X A4 F10.5

                rdnat = rdnat + 1

                txt_n     = line[0:5]
                txt_resno = line[5:10]
                txt_res   = line[11:15]
                txt_type  = line[16:20]
                txt_x     = line[20:30]
                txt_y     = line[30:40]
                txt_z     = line[40:50]
                txt_segid = line[51:55]
                txt_resid = line[56:60]
                txt_weight = line[60:70]

                if not model or (replica and txt_segid != old_segid):
                    model = objects.zmatrix.Zmatrix()
                    #model.title = root
                    model.title = self.name
                    #self.objects.append(model)
                    self.molecules.append( model )
                    old_segid = txt_segid

                #print txt_n, txt_resno, txt_res, txt_type, txt_x, txt_y, txt_z, txt_segid, txt_resid
                txt_type = string.strip(txt_type)
                #print '--'+txt_type+'--'

                x = float(txt_x)
                y = float(txt_y)
                z = float(txt_z)

                a = objects.zmatrix.ZAtom()
                a.coord = [x,y,z]

                trans = string.maketrans('a','a')

                a.name = txt_type
                try:
                    #a.symbol = map[txt_type]
                    a.symbol = charmm_map[txt_type]
                    #a.name = a.symbol + string.zfill(i+1,2)
                except KeyError:
                    # strip off any numbers and punctuation
                    a.symbol = string.translate(txt_type,trans,string.digits)
                    a.symbol = string.translate(a.symbol,trans,string.punctuation)
                    a.symbol = string.upper(a.symbol)[:1] + string.lower(a.symbol)[1:2]
                    try:
                        testz = sym2no[a.symbol]
                    except KeyError:
                        print 'unrecognised atom type',txt_type
                        a.symbol = 'X'

                #a.symbol = string.translate(words[0],trans,string.digits)
                #a.symbol = string.capitalize(a.symbol)
                #a.name = a.symbol + string.zfill(i+1,2)

                a.resno = int(txt_resno)
                #a.resno = int(txt_resid)

                model.atom.append(a)

            #print 'Counts', rdnat, nat
            if rdnat != nat:
                msg = "Problem reading CHARMM .CRD file\n"+\
                "Number of atoms found doesn't match the entry\n at the start of the file\n"+\
                str(rdnat)+" atoms were read"
                #self.warn(msg)
                print msg

    def _WriteMolecule(self,molecule,**kw):

        """The write method sits in the Zmatrix class"""
        
        molecule.wrtcrd( self.filepath )


class testCHARMM_IO(unittest.TestCase):
    """Test CHARMM reader and writer"""

    reader = writer = CRDReader()

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


    def testCRDRead(self):
        """ """

        molecules = self.reader.GetObjects(
            filepath='/c/qcg/jmht/Documents/codes/OpenBabel/fileformats/original-linear-path.crd',
            otype = 'molecules'
            )

        self.assertEqual( len(molecules[0].atom),24876)

    def testCRDWrite(self):

        """CHARMM CRD Write"""

        mol = self.getMolecule()

        filepath = os.getcwd()+'/test.crd'
        self.writer.WriteFile( mol, filepath=filepath )

        statinfo = os.stat( filepath )
        self.assertEqual( statinfo.st_size,1099)
        os.remove( filepath )


if __name__ == "__main__":
    unittest.main()
    
