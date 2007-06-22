#
#    This file is part of the CCP1 Graphical User Interface (ccp1gui)
# 
#   (C) 2002-2005 CCLRC Daresbury Laboratory
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

# import python modules
import re
import os
import copy
import traceback

# import internal modules
from charmm import CRDReader
from daltonio import DaltonIO
from dl_poly import DLPOLY_CONFIG_IO, Dl_PolyHISTORYReader
from gamessukio import GUKOutputIO,GUKInputIO
from fileio import CML_IO
from cubereader import CubeIO
from fileio import OpenBabelIO
from fileio import MDL_IO
from fileio import MSICeriusII_IO
from fileio import PDB_IO
from filepunch import PunchIO
from smeagolio import SmeagolIO
from fileio import SHELXTL_IO
from fileio import SpartanInputIO
from fileio import XYZ_IO
from fileio import VTK_IO
from fileio import ZmatrixIO

class GetFileIO:
    """
    Class for determining the correct object to read or write a particular filetype

    """

    def __init__(self,debug=None):
        """ Set up the supported Readers """


        self.debug=None
        if debug:
            self.debug = 1
        
        # For using openBabel
        global openbabel,pybel
        openbabel = None
        pybel = None

        # Hacks...
        self.desc2OBfmt = None # Used for coping with the Tkinter
                               # bug with long menus
        self.agentx = None # So know if we are using AgentX and can
                           # preferentially use this for all xml files
        
        try:
            import openbabel
            import pybel
        except ImportError:
            if self.debug: print "filereader - cannot import openbabel"
            pass


        # Dictionary mapping filetype string to a list
        #
        # NB - the filetype string should be the same as the decription of the
        # format supported by openbabel - these can be listed with the command:
        # import pybel;print pybel.informats; print pybel.outformats
        #
        # The contents of the list are:
        # 1. the reader for that filetype
        # 2. a list of the extensions valid for this filetype
        # 3. a regular expression that can be used to identify these sorts of files
        #    (see FormatFromFile )
        # 4. A logical flag indicating if we can read this type of file
        # 5. a list of the types of objects this IO Object can write

        self.format_info = {
            'Chemical Markup Language'  : [ CML_IO, ['.cml'], None,False, ['Zmatrix','Indexed']  ],
            'ChemShell punchfile'  : [ PunchIO, ['.c'], None, True, None ],
            'Dalton output' : [ DaltonIO, ['.out','.log'],
                                re.compile('\s*\*{11}  DALTON - An electronic structure program  \*{11}'), True, None ],                                
            'CHARMM crd' : [ CRDReader, ['.crd'], None, True, ['Zmatrix','Indexed']  ],
            'DL-POLY CONFIG' : [ DLPOLY_CONFIG_IO, ['CONFIG'], None, True, None ],
            'DL-POLY HISTORY' : [ Dl_PolyHISTORYReader, ['HISTORY'], None, True, None ],
            'GAMESS-UK input' : [ GUKInputIO, ['.in'], None, True, None ],
            'GAMESS-UK output' : [ GUKOutputIO, ['.out'],
                                   re.compile('\s*\*\s*===  G A M E S S - U K    ===\s*\*'), True, None ],
            'GAMESS-UK punchfile'  : [ PunchIO, ['.pun'], re.compile('\s*block =.*=.*'), True, None ],
            'Gaussian cubefile'  : [ CubeIO, ['.cube'], None, True, None ],
            'MDL MOL format' : [ MDL_IO, ['.mol','.mdl'], None, True, None ],
            'MSI Cerius II' : [ MSICeriusII_IO, ['.car'], None, False, ['Zmatrix','Indexed'] ],
            'Protein Data Bank format'  : [ PDB_IO, ['.pdb'], re.compile('^COMPND .*'), True, None],
            'SHELXTL res format' : [ SHELXTL_IO,['.res'],None,False,['Zmatrix','Indexed']], 
            'Spartan input' : [ SpartanInputIO,['.spinput'],None,True, None], 
            'Smeagol output' : [ SmeagolIO,['.rho'],None,True, None], 
            'XYZ cartesian coordinates format' : [ XYZ_IO,['.xyz'],None,True,['Zmatrix','Indexed']], 
            'VTK data'      : [ VTK_IO, ['.vtk'], None,True,None],
            'Zmatrix'      : [ ZmatrixIO, ['.zmt'], None, True, ['Zmatrix','Indexed']]
            }


        # See if we can use AGENTX
        try:
            from filexml import XML_IO
            self.format_info['XML (AgentX)'] = [ XML_IO, ['.owl','.rdf','.xml'],None,True,None ]
            self.agentx=1
        except ImportError:
            if self.debug: print "Cannot Import AgentX"

            
        # Using OpenBabel
        if openbabel:
            self.SetupOpenbabel()

        ### End __init__ ###



    def SetupOpenbabel(self):
        """ Populate the self.format_info data structure with the formats
            supported by openbabel.
            
            We highlighted a bug in the dynamic population of the list of
            different filetypes supported by openbabel, so this function
            is only available in particular versions. Therefore we see if
            we can use the informats feature of pybel (indicating the list
            works) and use a static dictionary if it isn't available - this
            obviously has the potential problem that we may claim to support
            a filetype not supported by the OB version in use.

        """
            
        if hasattr(pybel,'informats'):
            # Can dynamically populate the formats dictionary...

            # Get dictionary of BabelID(the extension) -> description
            # for all supported
            # Babel input and output formats
            informats = pybel.informats
            #formats.update(pybel.outformats)
            outformats = pybel.outformats
            #print outformats

        else:
            # Use a static dictionary of formats we know OB supports
            informats = {'res': 'ShelX format', 'pqs': 'Parallel Quantum Solutions format', 'mdl': 'MDL MOL format', 'c3d2': 'Chem3D Cartesian 2 format', 'pcm': 'PCModel Format', 'xyz': 'XYZ cartesian coordinates format', 'c3d1': 'Chem3D Cartesian 1 format', 'gpr': 'Ghemical format', 'alc': 'Alchemy format', 'outmol': 'DMol3 coordinates format', 'ins': 'ShelX format', 'gamout': 'GAMESS Output', 'arc': 'Accelrys/MSI Biosym/Insight II CAR format', 'therm': 'Thermo format', 'mpqc': 'MPQC output format', 'cdx': 'ChemDraw binary format', 'ct': 'ChemDraw Connection Table format', 'unixyz': 'UniChem XYZ format', 'jout': 'Jaguar output format', 'nwo': 'NWChem output format', 'pc': 'PubChem format', 'feat': 'Feature format', 'mol': 'MDL MOL format', 'dmol': 'DMol3 coordinates format', 'yob': 'YASARA.org YOB format', 'ml2': 'Sybyl Mol2 format', 'fract': 'Free Form Fractional format', 'mmod': 'MacroModel format', 'ent': 'Protein Data Bank format', 'crk3d': 'Chemical Resource Kit 3D format', 'mopout': 'MOPAC Output format', 'mopin': 'MOPAC Internal', 'cdxml': 'ChemDraw CDXML format', 'mopcrt': 'MOPAC Cartesian format', 'xml': 'General XML format', 'prep': 'Amber Prep format', 'fchk': 'Gaussian formatted checkpoint file format', 'crk2d': 'Chemical Resource Kit diagram format (2D)', 'smiles': 'SMILES format', 'mop': 'MOPAC Cartesian format', 'fs': 'FastSearching', 'mpc': 'MOPAC Cartesian format', 'sy2': 'Sybyl Mol2 format', 'inp': 'GAMESS Input', 'mol2': 'Sybyl Mol2 format', 'gamin': 'GAMESS Input', 'txt': 'Title format', 'tdd': 'Thermo format', 'inchi': 'InChI format', 'gam': 'GAMESS Output', 'g94': 'Gaussian98/03 Output', 'moo': 'MOPAC Output format', 'g92': 'Gaussian98/03 Output', 'cmlr': 'CML Reaction format', 'bs': 'Ball and Stick format', 'fch': 'Gaussian formatted checkpoint file format', 'mmd': 'MacroModel format', 'fck': 'Gaussian formatted checkpoint file format', 'tmol': 'TurboMole Coordinate format', 'hin': 'HyperChem HIN format', 'g98': 'Gaussian98/03 Output', 'box': 'Dock 3.5 Box format', 'cml': 'Chemical Markup Language', 'cif': 'Crystallographic Information File', 'bgf': 'MSI BGF format', 'rxn': 'MDL RXN format', 'car': 'Accelrys/MSI Biosym/Insight II CAR format', 'sdf': 'MDL MOL format', 'vmol': 'ViewMol format', 'smi': 'SMILES format', 'acr': 'ACR format', 'gal': 'Gaussian98/03 Output', 'caccrt': 'Cacao Cartesian format', 'qcout': 'Q-Chem output format', 'g03': 'Gaussian98/03 Output', 'pdb': 'Protein Data Bank format', 'ccc': 'CCC format', 'sd': 'MDL MOL format'}

            outformats = {'xed': 'XED format', 'cssr': 'CSD CSSR format', 'zin': 'ZINDO input format', 'pqs': 'Parallel Quantum Solutions format', 'mdl': 'MDL MOL format', 'qcin': 'Q-Chem input format', 'c3d2': 'Chem3D Cartesian 2 format', 'gjf': 'Gaussian 98/03 Input', 'xyz': 'XYZ cartesian coordinates format', 'c3d1': 'Chem3D Cartesian 1 format', 'inp': 'GAMESS Input', 'alc': 'Alchemy format', 'outmol': 'DMol3 coordinates format', 'ent': 'Protein Data Bank format', 'inchi': 'InChI format', 'fasta': 'FASTA format', 'txt': 'Title format', 'feat': 'Feature format', 'ct': 'ChemDraw Connection Table format', 'test': 'Test format', 'therm': 'Thermo format', 'unixyz': 'UniChem XYZ format', 'fract': 'Free Form Fractional format', 'jin': 'Jaguar input format', 'mpqcin': 'MPQC simplified input format', 'fix': 'SMILES FIX format', 'cache': 'CAChe MolStruct format', 'dmol': 'DMol3 coordinates format', 'yob': 'YASARA.org YOB format', 'ml2': 'Sybyl Mol2 format', 'fpt': 'Fingerprint format', 'pov': 'POV-Ray input format', 'crk2d': 'Chemical Resource Kit diagram format (2D)', 'cht': 'Chemtool format', 'crk3d': 'Chemical Resource Kit 3D format', 'pcm': 'PCModel Format', 'mopin': 'MOPAC Internal', 'cdxml': 'ChemDraw CDXML format', 'txyz': 'Tinker MM2 format', 'mopcrt': 'MOPAC Cartesian format', 'mol2': 'Sybyl Mol2 format', 'gpr': 'Ghemical format', 'csr': 'Accelrys/MSI Quanta CSR format', 'cacint': 'Cacao Internal format', 'smiles': 'SMILES format', 'mpd': 'Sybyl descriptor format', 'fs': 'FastSearching', 'mpc': 'MOPAC Cartesian format', 'mol': 'MDL MOL format', 'gau': 'Gaussian 98/03 Input', 'mop': 'MOPAC Cartesian format', 'smi': 'SMILES format', 'report': 'Open Babel report format', 'tdd': 'Thermo format', 'fa': 'FASTA format', 'sdf': 'MDL MOL format', 'mmod': 'MacroModel format', 'cmlr': 'CML Reaction format', 'bs': 'Ball and Stick format', 'fh': 'Fenske-Hall Z-Matrix format', 'mmd': 'MacroModel format', 'copy': 'Copies raw text', 'tmol': 'TurboMole Coordinate format', 'sy2': 'Sybyl Mol2 format', 'hin': 'HyperChem HIN format', 'gamin': 'GAMESS Input', 'box': 'Dock 3.5 Box format', 'fsa': 'FASTA format', 'cml': 'Chemical Markup Language', 'cif': 'Crystallographic Information File', 'bgf': 'MSI BGF format', 'rxn': 'MDL RXN format', 'k': 'Compares first molecule with others using InChI', 'vmol': 'ViewMol format', 'pdb': 'Protein Data Bank format', 'molreport': 'Open Babel molecule report', 'can': 'Canonical SMILES format.', 'gr96': 'GROMOS96 format', 'cac': 'CAChe MolStruct format', 'nw': 'NWChem input format', 'com': 'Gaussian 98/03 Input', 'gjc': 'Gaussian 98/03 Input', 'caccrt': 'Cacao Cartesian format', 'sd': 'MDL MOL format'}


        # Dictionaries keyed by extension, but we need description
        # We also need to add a dot to the extension
        newd = [(v, '.'+k) for k, v in informats.items()]
        informats = dict( newd )
        newd = [(v, '.'+k) for k, v in outformats.items()]
        outformats = dict( newd )

        # desc2OBfmt Maps our description to the OB supported ones
        self.desc2OBfmt = copy.copy( informats )
        self.desc2OBfmt.update( outformats )

        # Now add these formats to self.format_info - we just
        # add these to any existing entries instead of overwriting
        # the entries as otherwise we would lose the regular expression
        # string, which isn't supported by openbabel - in addition we add
        # regular expressions to some of the OB suported formats for convenience

        # First readers
        for format,ext in informats.iteritems():
            #print "Adding %s from OpenBabel to self.format_keys",format

            if self.format_info.has_key( format ):
                # We have an existing IO object so we need to overwrite it
                self.format_info[format][0] = OpenBabelIO

                # Set read flag to true
                self.format_info[format][3] = True # Can read

            else:
                # No existing IO object
                # We add regular expressions for those files we know about
                if format == 'Gaussian98/03 Output':
                    filere = re.compile('\s*This is the Gaussian\(R\) 03 program.')
                else:
                    filere = None

                # Add the entry
                self.format_info[format] = [ OpenBabelIO,[ext],filere,True,None ]


        # Now Writers
        for format,ext in outformats.iteritems():
            #print "Adding %s from OpenBabel to self.format_keys",format

            if self.format_info.has_key( format ):
                # We have an existing IO object so we need to overwrite it
                self.format_info[format][0] = OpenBabelIO

                # Set write flag to indiate we can deal with molecules
                self.format_info[format][4] = ['Zmatrix','Indexed']

    def GetReader( self, filepath=None, format=None, debug=None ):
        """Return an IO object that can read this type of file"""

        if debug:
            self.debug=1
            
        fio = self.GetIO( filepath=filepath, format=format, read=1 )

        if not fio:
            if self.debug: print "GetReader did not get a reader"
            return None

        if self.debug:
            print "getfileIO GetReader got reader ",fio

        # This check is probably redundant now as this information
        # specified in format_info
        if fio.CanRead():
            if self.debug: print "getfileIO reader can read"
            return fio
        else:
            if self.debug:print "getfileIO reader cannot read"
            return None

    def GetWriter( self, dataobj=None, filepath=None, format=None, debug=None):
        """Return an IO object that can write this type of file"""
    
        if debug:
            self.debug=1
            
        fio = self.GetIO( filepath=filepath, format=format, write=1 )
        if not fio:
            return None

        if dataobj:
            if fio.CanWrite( dataobj ):
                print "GetWriter can write "
                return fio
            else:
                print "GetWriter no write "
                return None
        else:
            # Have to assume that we can write
            return fio
    
    def GetIO( self, filepath=None, format=None, read=None, write=None ):
        """
         Return an IO object for file located at filepath or of the type specificed by format
         if filetype is not None, we return an IO object for the specified filetype
         else we try and determine the format (FormatFromFile)
         Return None if we can't find an IO object (i.e. file is unsupported)
        
        """

        if not format:
            format = self.FormatFromFile( filepath )
            
        # Can't work out what sort of file this is
        if not format:
            print "GetIO cannot determine an IO object for the file: %s" % filepath
            return
        
        if self.debug:
            print "GetIO using format ",format

        # Return the correct IO object for this format
        if format in self.format_info.keys():

            # Check if it supports reading or writing
            if read:
                if not self.format_info[ format ][3]:
                    if self.debug:print "GetIO cannot read files for: %s" % format
                    return None

            if write:
                if not len(self.format_info[ format ][4]):
                    if self.debug:print "GetIO cannot write files for: %s" % format
                    return None
                
            # IO object is first item in the list
            fileio = self.format_info[ format ][0]

            if self.debug:
                print "GetIO got key ",format
                print "io object is ",fileio,id(fileio)

            # Instantiate and return the IO object
            # we instatitate it with the file as an argument
            
            # HACK - Open babel uses the extension to identify files
            # (whereas we can't as we support different files with the
            # same extension) so when using openbabel
            # we need to pass a dictionary to the OB object so it
            # can lookup the OB format from the description
            return fileio( filepath=filepath,format=format,desc2OBfmt=self.desc2OBfmt )
        else:
            print "Could not find an io object for:\nformat: %s\nfile: %s" % (format,filepath)
            return None

    def FormatFromFile(self,filepath):
        """
        Try and work out the type of file

        We first try going through our dictionary of regular expressions and if that fails
        we then try and guess from the file extension
        """

        format = None
        
        if os.access( filepath, os.R_OK):
            # Only do this if we can read the file - we don't want to use
            # this if we are aiming to write a file as it won't exist yet
            format = self.FormatFromRegxp( filepath )
            
        if not format:
            format = self.FormatFromExt( filepath )

        # Hack - we always want to use agentx for xml where
        # it's available
        if self.agentx:
            if format == 'General XML format':
                format = 'XML (AgentX)'
            

        if self.debug:
            if not format:
                print "FormatFromFile could not determine format for file: %s" % filepath
            else:
                print "FormatFromFile returning format ",format
                
        return format


    def FormatFromExt(self,filepath):
        """ Guess the format from the extension

        """

        format = None
        # First see if we can use OpenBabel for this
        if openbabel:
            OBConv = openbabel.OBConversion()
            OBFormat = OBConv.FormatFromExt( filepath )
            if OBFormat:
                # Assume the first line of the description is what we need
                desc = OBFormat.Description()
                format = desc.split("\n")[0].strip()
                print "FormatFromExt got format from openbabel ",format

        if not format:
            # Either no openbabel or the filetype isn't supported by it
            directory,filename = os.path.split( filepath )
            path,ext = os.path.splitext( filename )
            name = os.path.basename( path )

            # If there's no extension, we use the filename instead
            if not len(ext):
                ext = name
            
            # See if it's in the list of files we know about
            # the second item in the list
            for ftype,ilist in self.format_info.iteritems():
                if ilist[1]:
                    if ext in ilist[1]:
                        format = ftype
                        break

        if self.debug:
            print "FormatFromExt returning: %s" % format
            
        return format

        
    def FormatFromRegxp(self,filepath):
        """
        Try and work out the type of file by parsing through it until we can work out what we have
        Return the filetype or None if we can't determine it
        
        We compare each line against a list of regular expressions that
        are considered indicative of a particular programmes output and then
        break out as soon as we hit a match.

        """

        f = open( filepath, 'r' )

        maxlines = 500 # Need to ensure we don't read too many lines
        done = None
        ret = None

        read = 0
        while not done:

            if read > maxlines:
                if self.debug:
                    print "FormatFromRegxp reader > maxlines ",maxlines
                done = 1

            line = f.readline()

            if not line:
                print "No line in file in scan_output!"
                done = 1
                break
            
            for format in self.format_info.keys():
                # Third item should be a regular experssion
                myre = self.format_info[format][2]
                if not myre:
                    # No regular expression for this object
                    continue
                else:
                    if myre.match( line ):
                        done = 1
                        ret = format
                        break
                
            read += 1

        f.close()

        if self.debug:
            print "FormatFromRegxp returning; %s" % ret
        return ret


    def GetInputFiletypesAsTuple(self):
        """
        Return a list of tuples mapping filetypes -> extensions
        this is for use by tkFileDialog.askopenfilename
        
        """

        ftypes = []
        for format in self.format_info.keys():
            
            # Check can read
            if not self.format_info[ format ][ 3 ]:
                continue
            
            # Fix for bug in Tkinter for long menus
            # Only display supported formats
            if self.desc2OBfmt:
                if format in self.desc2OBfmt.keys():
                    # self.format_info[format][1] is extension list - there will
                    # only be one for each OpenBabel supported format
                    ext = self.format_info[ format ][1][0]
                    ftypes.append(('OpenBabel Supported Format',ext))
                    continue
            
            if self.format_info[ format ][1]: # We have a list of extensions
                for ext in self.format_info[ format ][1]:
                    #ftypes.append( (format, "."+ext ) )
                    ftypes.append( (format, ext ) )
            else:
                # List all files for unknown extensions
                ftypes.append( (format, "*.*") )

        # Get them into alphabetical order
        ftypes.sort()

        # Need to add the option to open any file type
        ftypes.append(('All','*'))

        # So that we have a separate heading for molecule types
        moltypes=[('Molecules','.xyz'),
                  ('Molecules','.pdb'),
                  ('Molecules','.pun'),
                  ('Molecules','.c'),
                  ('Molecules','.crd'),
                  ('Molecules','.z'),
                  ('Molecules','.cml'),
                  ('Molecules','.xml'),
                  ('Molecules','.zmt'),
                  ('Molecules','.gjf'),
                  ('Molecules','.mol')]
        
        # put it at the top of the list
        ftypes = moltypes+ftypes
        
        return ftypes
    
    def GetOutputFiletypesAsTuple(self):
        """
        Return a list of tuples mapping filetypes -> extensions
        this is for use by tkFileDialog.asksaveasfilename
        """

        ftypes = []
        for format in self.format_info.keys():
            # list of supported object types is the 5th item in format_info
            if self.format_info[format][4] and len(self.format_info[format][4]):
                # list of extension is 2nd item
                for ext in self.format_info[format][1]:
                    ftypes.append( (format,ext) )

        return ftypes
                

    def GetOutputFiletypesAsString(self):
        ftypes = self.GetOutputFiletypesAsTuple()
        names = []
        for name,ext in ftypes:
            names.append('%s [%s]' % (name,ext) )
        return names

    def GetOpenBabelIO(self,format=None):
        """ If Openbabel is available, return the IO object
        """

        if openbabel:
            return OpenBabelIO( format=format, desc2OBfmt=self.desc2OBfmt )
        else:
            return None

if __name__ == "__main__":

    root = "/Users/jmht/work/codes/CCP1GUI/sources/ccp1gui/interfaces/"
    # Testcases = dict mapping filenames to filetypes
    toTest = {
#        root+"c2032_g.out" : None,
        '/Users/jmht/work/codes/openbabel-2.0.2/scripts/python/jens/CChol_HF_631Gd_opt.log': None
        }

    print "teating..."
    getReader = GetFileIO()
    print "reader is ",getReader

    for filepath,format in toTest.iteritems():
        print "checking file ",filepath
        reader = getReader.GetReader( filepath,format=format )
        #reader = GetFileReader( filepath )
        print "reader ",reader
        if reader:
            objs = reader.GetViewObjects()
            print "objs ",objs
        else:
            print "No reader!!!"

    
    
