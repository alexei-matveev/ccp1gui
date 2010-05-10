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
"""Readers for GAMESS-UK input and output files
Provide an interface to the contents of the output file

still to do.....
sensible names and title
remove rotations/translations
  tool to step through vibrations?

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
import copy
import string
import unittest

# import internal modules
from fileio import FileIO
import objects.zmatrix
import objects.vibfreq
from objects.periodic import name_to_element

toAngstrom = 0.529177249

def _spliteformat(mobj):
    """Routine to take part of an e format output that overlaps and split it up
       string should containt X-Y, where X,Y are numbers
       we want to change it to X -Y
       mobj is the match object determined by a re.sub call"""
    string = mobj.group(0) 
    return string[0]+' '+string[1:2]
#end def


class GUKInputIO(FileIO):
    """
     A reader GAMESS-UK input files
    """

    def __init__(self, filepath=None,**kw):
        """ Set up the structures we need

        """

        # Initialise base class
        FileIO.__init__(self,filepath=filepath,**kw)

        # State we can read these files
        self.canRead = True


    def _ReadFile(self,**kw):
        """ Read a GAMESS-UK input file. Currently this only reads in the
        structure of the molecule and no calculation details. It parses
        the z-matrix into a list and then uses the ZMatrix method with the
        load from list method. If it encounters a geom field it assumes everything
        that follows is gamess cartesian format and reformats each string so that it
        can be handled by the list method.
        """
        print "Reading GAMESS-UK input file: %s" % self.filepath

        # root is the default filename, file is the filename, not the file handle
        file  = open(self.filepath,'r')        #The file descriptor

        # loop to find where the coordinate specification starts
        finished = 0
        while not finished:
            line = file.readline()
            if not line: # EOF so return 
                finished = 1
                return None
                break

            # Remove space and convert to lower case
            line=line.strip()
            line=line.lower()
            
            if line:
                #fields = string.split( line )
                fields = line.split()
            else:
                # ignore empty lines
                continue

            if len(fields) and len(fields[0])>=4:
                if ( fields[0][0:4] == "zmat" ):
                    mode = 'z'
                    finished = 1
                elif ( fields[0][0:4] == "cart" ):
                    mode = 'x'
                    finished = 1
                elif ( fields[0][0:4] == "geom"):
                    # Check for NWChem input style
                    if ( len(fields) == 3 and fields[2][0:4] == 'nwch'):
                        mode = 'n'
                    else:
                        mode = 'x'
                    finished = 1

        zmat_buffer = []

        # We should now be at the start of a line beginning with zmat or geom
        # Append the header line we just read:
        zmat_buffer.append( line )
        
#        if ( fields[0][0:4] == "zmat" ):# start
#            mode = 'z'
#        elif (fields[0][0:4] == "geom" ): # start but need to flag the mode
#            mode = 'x'
#             if ( len( fields ) > 1 ):
#                 if ( fields[1][0:4] == "angs" ):
#                     zmat_buffer.append( "coordinates angstrom" )
#                 elif ( fields[1][0:4] == 'bohr' or fields[1][0:4] == 'a.u.' or fields[1][0:4] == 'au' ):
#                     zmat_buffer.append( "coordinates bohr" )
#                 else:
#                     print "Unknown modifier for geometry directive!"
#                     print "Offending line is %s" % line
#                    zmat_buffer.append( "coordinates" )
#        else:
#            # shouldn't ever get here
#            print "Error reading GAMESS-UK input"
#           return 1

        # loop to read in the coordinates
        reading = 1
        while ( reading ):
            line = file.readline()

            if not line: # EOF so return 
                reading = 0
                print "ERROR! Encountered EOF while reading in coordinates from GAMESS-UK Input file!"
                return None
                break
        
            line=line.strip()
            line=line.lower()
            
            if line:
                # See if the line has commas in it, as GAMESS-UK supports this as a
                # separator as well as whitespace
                if re.compile(",").search( line ):
                    fields = line.split(',')
                    line = fields.join() # Rejoin split line using space as separator
                else:
                    fields = line.split()                    
            else:
                # ignore empty lines
                continue

            if ( fields[0][0] == "#" or fields[0][0] == "?" ): # ignore comments
                continue
            elif ( fields[0][0:3] == "end" ): # stop
                zmat_buffer.append( "end" )
                reading = 0
            else:
                if mode == 'z':
                    zmat_buffer.append( line )
                elif mode == 'x': # reformat the line
                    cart_string = fields[4] + "\t" + fields[0] + "\t" \
                                  + fields[1] + "\t" + fields[2]
                    zmat_buffer.append( cart_string )
                elif mode == 'n':
                    # Reformat the string from NWChem input format
                    cart_string = fields[0] + "\t" + fields[2] + "\t" \
                                  + fields[3] + "\t" + fields[4]
                    zmat_buffer.append( cart_string )
                    

        #self.debug = 1
        if ( self.debug == 1 ):
            print "viewer/main.py: rdgamin read zmat_buffer:"
            for line in zmat_buffer:
                print "zmat: ",line

        # Now we've got a buffer with the coordinates, create the model
        model = objects.zmatrix.Zmatrix( list = zmat_buffer )
        model.title = self.name
        model.name = self.name
        self.molecules.append( model )
        #self.objects.append( model )

    
class GUKOutputIO( FileIO ):
    """ Read an GAMESS-UK output file and store information"""
    
    def __init__(self,filepath=None,**kw):

        # Initialise base class
        FileIO.__init__(self,filepath=filepath,**kw)
        
        self.debug = 0
        self.title = None
        self.type = 'Gamess-UK output'
        self.date = ''
        self.time = ''
        self.nelec = 0
        self.nbasis = 0
        self.nshells = 0
        self.multiplicity = 0
        self.charge = 0.0
        self.basis = ''
        self.pointGroup = ''
        self.orderOfPrincipalAxis = 0
        self.nuclearEnergies = []
        self.XCEnergies = []
        self.electronicEnergies = []
        self.totalEnergies = []
        self.finalNuclearEnergy = 0.0
        self.finalElectronicEnergy = 0.0
        self.finalTotalEnergy = 0.0
        self.orbitalIrreps = []
        self.orbitalEnergies = []
        self.orbitalOccupancies = []
        self.mullikens  = []
        self.lowdins  = []
        self.scftypes  = []
        self.runtypes  = []
        self.maximumSteps = []
        self.nuclearDipole = [0.0, 0.0, 0.0]
        self.electronicDipole = []
        self.totalDipole = []
        self.converged = 0
        self.homo = 0
        self.lumo = 0
#         self.zmatrix_atoms = []
#         self.zmatrix_n1s = []
#         self.zmatrix_v1s = []
#         self.zmatrix_n2s = []
#         self.zmatrix_v2s = []
#         self.zmatrix_n3s = []
#         self.zmatrix_v3s = []
#         self.variables_type = {}
#         self.variables_value = {}
#         self.variables_units = {}
#         self.variables_hessian = {}

# Don't use vibrations list as we return a vibration set
#        self.vibrations = []
        self.vibration_sets = []
        self.TransitionFrequencies = []
        self.TransitionDipoles     = []
        self.TransitionStrengths   = []
        self.TransitionIntensities = []
        self.DRF_totalQMEnergy = 0.0
        self.DRF_qm_classical = 0.0
        self.DRF_polarisation = 0.0
        self.DRF_totalEnergy = 0.0
        self.DRF_totalArea = 0.0
        self.zmatrix = None # Flag to monitor if we are in cartesian or zmatrix mode
        self.zmatrix_auto = None
        self.readvar = None # flag to monitor calls to _read_variables
        self.molecules = []    # use to hold the list of coordinates as z-matrices


    def _ReadFile(self):
        """ Read a GAMESS-UK Output file"""
        self.manage  = {}      # Manage holds a tuple with a matching string, and function to handle
        # Define a phrase to search for and the routine to read the data
        self.manage['molsym'] = ( re.compile('^ *molecular point group'), self._read_molecular_symmetry)
        self.manage['nuclear_xyz'] = ( re.compile('^ *point.*nuclear coordinate') , self._read_nuclear_xyz )
#       The three methods below are redundant now
#        self.manage['nuclear_coords'] = ( re.compile('^ *nuclear coordinates') , self._read_nuclear_coordinates )
#        self.manage['atomic_coords'] = ( re.compile('^ *\* *atom  *atomic  *coord') , self._read_molecular_geometry )
        self.manage['input_zmatrix'] = ( re.compile(' >>>>> zmat',re.IGNORECASE) , self._read_input_zmatrix )
        self.manage['variables'] = ( re.compile('^ *variable *value *hessian') , self._read_variables )
        self.manage['zmatrix_auto'] = ( re.compile('^ *automatic z-matrix generation') , self._read_zmatrix_auto )
        self.manage['zmatrix2'] = ( re.compile('^ *z-matrix \(angstroms and degrees\)') , self._read_zmatrix2 )
        self.manage['symm_geom'] = ( re.compile('^ *\*     atom   atomic                coordinates') , self._read_orient_geom )
        self.manage['nuclear_energy'] = ( re.compile('^ *nuclear energy *=') , self._read_energies )
        self.manage['mo_irreps'] = ( re.compile('^ *m.o. irrep') , self._read_orbital_energies )
        self.manage['gross_pops'] = ( re.compile('^ *-.* total gross pop.*atoms') , self._read_total_populations )
        self.manage['run_type'] = ( re.compile('^ *\* RUN TYPE') , self._read_runtype )
        self.manage['scf_type'] = ( re.compile('^ *\* SCF TYPE') , self._read_scftype )
        self.manage['final_energy'] = ( re.compile('^ *final energies') , self._read_final_energies )
        self.manage['opt_converged'] = ( re.compile('^ *optimization converged') , self._read_optimization_converged )
        self.manage['dipole'] = ( re.compile('^ *dipole moments') , self._read_dipole )
        self.manage['date'] = ( re.compile('^  *date') , self._read_date )
        self.manage['time'] = ( re.compile('^  *time') , self._read_time )
        self.manage['charge'] = ( re.compile('^  *charge of molecule') , self._read_charge )
        self.manage['nelec'] = ( re.compile('^  *number of electrons') , self._read_nelec )
        self.manage['shells'] = ( re.compile('^  *total number of shells') , self._read_nshells )
        self.manage['nbasis'] = ( re.compile('^  *total number of basis') , self._read_nbasis )
        self.manage['multi'] = ( re.compile('^  *state multiplicity') , self._read_multiplicity )
        self.manage['basis'] = ( re.compile('^  *\* basis selected') , self._read_basis )
        self.manage['max_step'] = ( re.compile('^  *maximum step') , self._read_maximum_step )
        self.manage['normal_modes_hessian'] = ( re.compile('^  *cartesians to normal') , self._read_normal_modes_hessian )
        self.manage['normal_modes_force'] = ( re.compile('^  *eigenvectors of cartesian') , self._read_normal_modes_force )
        self.manage['freq_hessian'] = ( re.compile('^ =  *normal') , self._read_frequencies_hessian )
        self.manage['freq_force'] = ( re.compile('^  *harmonic frequencies ') , self._read_frequencies_force )
        self.manage['drf_area'] = ( re.compile('^  *contact area:') , self._read_DRF_area )
        self.manage['drf'] = ( re.compile('^  *--- quantum system ---') , self._read_DRF )
        
        # Attempt opening the file. Any exception should be trapped in the methods in the base
        # class that call this
        self.fd = open(self.filepath,'r')
        
        # Loop through the contents of the file a line at a time and parse the contents
        line = self.fd.readline()
        while line != '' :
            #jk print line
            for k in self.manage.keys():
                if self.manage[k][0].match(line):
                    if self.debug:
                        print 'Match found %s' % k
                    self.manage[k][1](line)
                    break
                #end if
            #end for
            line = self.fd.readline()
        #end while
        self.fd.close()
        return 
    #end def
    
    def _read_optimization_converged(self, line):
        converged = 1
        return
    #end def

    def _read_molecular_symmetry(self,line):
        self.pointGroup = line.split()[3]
        line = self.fd.readline()
        self.orderOfPrincipalAxis = int(line.split()[4])
        return
    #end def

    def _read_molecular_geometry(self, line):
        """ This reads in the molecular geometry printed at the start of the output
            file - regardless of the optimise runtype being undertaken.
        """

        # REM - THIS IS PROBABLY REDUNDANT NOW.
        
        # Create a new molecule
        # First skip 5 lines
        line = self.fd.readline()
        line = self.fd.readline()
        line = self.fd.readline()
        line = self.fd.readline()
        line = self.fd.readline()
        line = self.fd.readline()    # Start parsing this line
        zz = objects.zmatrix.Zmatrix()
        cnt = 0
        while not line.isspace():
            p = objects.zmatrix.ZAtom()
            s = line.split()
            x = float(s[3])*toAngstrom
            y = float(s[4])*toAngstrom
            z = float(s[5])*toAngstrom
            p.coord = [ x, y, z ]
            p.name = s[1]
            p.symbol = name_to_element( s[1] )
            p.index = cnt
            cnt += 1
            zz.add_atom(p)
            # skip to the first line which has simply ' *     * ' in it
            search = re.compile('^[\t ]*\*[\t ]*\*[\t ]*$')
            while not search.match(line):
                line = self.fd.readline()
            line = self.fd.readline()
            line = self.fd.readline()
        # end while not line.isspace()
        self.molecules.append(zz)        # Store the molecule in the list
    #end def

    def _read_nuclear_coordinates(self,line):
        """ This reads in the nuclear coodinates as printed at the outset of a gamess
            optimise run. This is not needed as, for runtype optimise, we pick up the
            coordinates from the _read_zmatrix method.
        """
        #REM - THIS PROBABLY REDUNDANT NOW

        # skip 3 lines
        line = self.fd.readline()
        line = self.fd.readline()
        line = self.fd.readline()
        line = self.fd.readline()    # this line will be the first to be parsed
        zz = objects.zmatrix.Zmatrix()
        cnt = 0
        search = re.compile('^.* ENTERING RHFCLM')
        while ( not line.isspace() and search.match(line) ) :
            p = objects.zmatrix.ZAtom()
            s = line.split()
            x = float(s[2]*toAngstrom)
            y = float(s[3]*toAngstrom)
            z = float(s[4]*toAngstrom)
            p.coord = [ x, y, z ]
            p.symbol = name_to_element( s[1] )
            p.index = cnt
            cnt += 1
            zz.add_atom(p)
        # end while
        self.molecules.append(zz)        # Store the molecule in the list
    #end def

    def _read_nuclear_xyz(self,line):
        """ This reads in instances of the cartesian coordinates printed by the optx
            optimiser and creates new molecules from them.
        """

        # This should now be done in _read_runtype
        # Find which point of the optimisation we are at
        #point = int(line.split()[1])
        #if point == 0:
        #    # First optimisation point so add a trajectory object
        #    # we then append all further molecules to this
        #    self.trajectories.append( objects.zmatrix.ZmatrixSequence() )
            
        # skip to start of coordinates
        while ( line and not line[3:5] == "==" ):
            line = self.fd.readline()
            
        line = self.fd.readline() # get first coordinates line

        zz = objects.zmatrix.Zmatrix()
        reading = 1
        count = 0 # to count in num of atoms
        while ( reading ):
            if ( not line ):
                reading = 0
                break
            else:
                line = line.strip()
                fields = line.split()

            if ( len( fields ) != 5 ):
                reading = 0
            else:
                a = objects.zmatrix.ZAtom()
                tag = fields[4]
                x = float(fields[0])*toAngstrom
                y = float(fields[1])*toAngstrom
                z = float(fields[2])*toAngstrom
                a.coord = [ x, y, z ]
                a.name = tag
                a.symbol = name_to_element( tag )
                a.index = count
 
                zz.add_atom(a)
                count += 1
                
            line = self.fd.readline() # bottom of reading loop

        # We should now have the structure - Really should check 
        # this but not sure of best way to do this.
        #self.molecules.append(zz)

        # Add this molecule to the latest trajectory object
        self.trajectories[-1].add_molecule( zz )

    def _read_variables(self, line):
        """This method reads in the updated variables for the z-matrix, deep copies
           the last molecule and updates the variable values of the copy to create
           the new molecule.
        """
        # Don't do this if we are running under geometry angstrom all
        if self.zmatrix_auto:
            return
        
        # Check if this is the first time here, as GAMESS-UK prints out the variables before
        # the first optimisation step
        if not self.readvar:
            self.readvar = 1
            return
        
        line = self.fd.readline()
        line = self.fd.readline()

        # Get the last model - there should prob only be one
        if ( len( self.molecules ) > 0 ):
            old_model = self.molecules[-1]
        
        new_var_dict = {}
        
        search = re.compile(' *===*')
        finished = 0
        
        while ( line and not finished ):
            if  search.match(line):
                finished = 1
                
            s = line.split()
            var_name = s[0]
            
            try:
                var_value= float( s[1] )
            except:
                finished = 1

            new_var_dict[var_name] = var_value
                
            line = self.fd.readline()
        #end of while
        
        # Now have a list of the variables & their new value so copy the last
        # molecule and update it with the new values
        new_model = copy.deepcopy( old_model )

        for var in new_model.variables:
            if ( var.name.lower() in new_var_dict.keys() ):
                var.value = new_var_dict[var.name.lower()]
            else:
                print "Error - _read_variables can't find : ",var.name
                pass

        # Update the molecule somehow...
        new_model.calculate_coordinates()

        # Add this molecule to the latest trajectory object
        self.trajectories[-1].add_molecule( new_model )


#  OLD CODE THAT JUST APPENDED THE VARIABLES
#         line = self.fd.readline()
#         line = self.fd.readline()
#         search = re.compile(' *===*')
#         while not search.match(line):
#             s = line.split()
#             name = s[0]
#             self.variables_value[name] = s[1]
#             self.variables_units[name] = s[2]
#             self.variables_hessian[name] = s[2]
#             line = self.fd.readline()
        #end of while



#     def _read_zmatrix(self, line):
#         # skip 2 lines
#         line = self.fd.readline()
#         line = self.fd.readline()
#         line = self.fd.readline()
#         nline = 0
#         while not line.isspace():
#             nline += 1
#             s = line.split()
#             self.zmatrix_atoms.append(s[0])
#             if nline == 1 :
#                 line = self.fd.readline()
#                 continue
#             self.zmatrix_n1s.append(s[1])
#             self.zmatrix_v1s.append(s[2])
#             if nline == 2 :
#                 line = self.fd.readline()
#                 continue
#             self.zmatrix_n2s.append(s[3])
#             self.zmatrix_v2s.append(s[4])
#             if nline == 3 :
#                 line = self.fd.readline()
#                 continue
#             self.zmatrix_n3s.append(s[5])
#             self.zmatrix_v3s.append(s[6])
#             line = self.fd.readline()
#         # end of while
#     #end def


    def _read_input_zmatrix(self, line):
        """ Read the zmatrix the user has input.
            For the time being, we assume that this zmatrix is o.k. as GAMESS-UK has accepted it,
            so we just parse it out and then use the load_from_list method of the zmatrix class to
            create the molecule
            We need to convert evrything to lower case as GUK prints variables as lower case
        """
        if self.debug: print "_read_input_zmatrix"
        self.zmatrix = 1
        zmat = []
        zmat.append( line[7:].lower() ) # always strip the ' >>>>> ' off
        inputre =  re.compile('^ >>>>> *end',re.IGNORECASE)
        while not inputre.match( line ):
            line = self.fd.readline()
            zmat.append( line[7:].lower() )

        model = objects.zmatrix.Zmatrix( list = zmat )
        self.molecules.append( model )
        
        
        

#     def _read_input_zmatrix2(self, line):
#         """ This reads the input z-matrix into a a text buffer and passed it to the
#             load_from_file method of the z-matrix class.
#             This is pretty messy and in retrospect, it is probably far easier just
#             to parse the z-matrix out of the echoed input. But I'd started so...
#         """
        
#         self.zmatrix = 1
        
#         zmat_buffer = []
#         zmat_buffer.append("zmatrix angstrom")
#         # skip 2 lines
#         line = self.fd.readline()
#         line = self.fd.readline()
#         line = self.fd.readline()
#         finished = 0

#         # Read in the first bit of the z-matrix
#         while ( line and not finished ):
#             if ( len( line ) > 1 ):
#                 if ( line[1] == "=" ):
#                     finished = 1
#                 if ( not finished ):
#                     words =  string.split( string.strip( line ) )
#                     if ( words[0] != "comment" ):
#                         zmat_buffer.append( string.strip( line ) )
#             line = self.fd.readline()

#         #Now read in the variables
#         zmat_buffer.append( "variables" )
#         finished = 0
#         gotvar = 0
#         gotconst = 0
#         while ( line and not finished ):
#             line = string.strip( line )
#             try:
#                 fields = string.split(line)
#                 var_value = float( fields[1] )
#                 varline = fields[0].lower() + "   " + fields[1] 
#                 zmat_buffer.append( varline )
#                 gotvar = 1
#             except:
#                 if ( gotvar ):
#                     if ( gotconst ):
#                         finished = 1
#                     else:
#                         # Check if we are reading in the constants or have finished
#                         line = self.fd.readline()
#                         try:
#                             if string.split( line )[0] == "constants":
#                                 self.fd.readline() # read in the ---- line
#                                 line = self.fd.readline()
#                                 zmat_buffer.append("constants")
#                                 gotconst = 1
#                                 continue
#                         except:
#                             finished = 1
#                 else:
#                     pass
                
#             line = self.fd.readline()
#         zmat_buffer.append("end")
        
#         model = Zmatrix( list = zmat_buffer )
#         self.molecules.append( model )

    def _read_orient_geom(self, line):
        """
           This reads in the geometry printed by gamess after it has read in the user specified
           geometry and rotated this following the symetry detection routines have done their work.
           We don't read this in if we are using a zmatrix.
        """
        if self.zmatrix:
            return

        if self.debug:
            print "read_orient_geom"

        # The regexp that identifies lines with the coordinates on them
        # REM: \s=space, \d=digit
        # strings we are looking for
        #symbol = '[a-zA-Z]{1,2}'
        symbol = '[a-zA-Z]{1,2}[0-9]*'
        charge = '\d{1,3}\.\d{1}'
        coord  = '[-]{0,1}\d{0,4}\.\d{7}'
        coord_line = re.compile('^\s*\*\s*'+symbol+'\s*'+charge+'\s*'+coord+'\s*'+coord)
        endsec = re.compile('^\s*\*{50,}') # at least 50 stars

        gotc = 0 # need to skip the first line of stars
        done = 0
        
        molc = objects.zmatrix.Zmatrix()
        while not done:

            if not line:
                print "EOF encountered in gamessoutputreader in _read_orient_geom!"
                done = 1
                break

            if not line.isspace():
                if endsec.match( line ):
                    if gotc:
                        # We've read in all the coordinates
                        done = 1
                        break
                    else:
                        # need to skip the first line of stars
                        gotc = 1
                elif coord_line.match( line ):
                    line = string.strip( line )
                    fields = string.split( line )
                    tag = fields[1]
                    try:
                        charge = float(fields[2])
                        x = float(fields[3])*toAngstrom
                        y = float(fields[4])*toAngstrom
                        z = float(fields[5])*toAngstrom
                    except:
                        print "Error reading values in gamessoutputreader in _read_orient_geom!"
                        print "Offending line is: ",line
                        
                    #print "tag:%s q:%s x:%s y:%s z:%s" % ( tag,charge,x,y,z)
                    a = objects.zmatrix.ZAtom()
                    a.coord = [ x, y, z ]
                    a.name = tag
                    a.symbol = name_to_element( tag )
                    molc.add_atom(a)

            line = self.fd.readline()

        # Finished reading so add the molecule to the list    
        self.molecules.append(molc)
        return

        
    def _read_energies(self, line):
        s = line.split()
        self.finalNuclearEnergy = float(s[3])
        self.nuclearEnergies.append(self.finalNuclearEnergy)
        line = self.fd.readline(); s = line.split()
        self.finalElectronicEnergy = float(s[3])
        self.electronicEnergies.append(self.finalElectronicEnergy)
        line = self.fd.readline(); s = line.split()
        self.finalTotalEnergy = float(s[3])
        self.totalEnergies.append(self.finalTotalEnergy)
    #enddef

    def _read_zmatrix_auto(self, line):
        """ This indicates that we are using an automatically generated Z-matrix.
            In this case we will need to set the variable zmatrix_auto to indicate
            that we don't use the read_variables method to update the zmatrix, as
            GAMESS-UK doesn't print out the variables that it uses and the we can't
            just update the variables as we do otherwise.
        """
        self.zmatrix  = 1
        self.zmatrix_auto = 1
        return

    def _read_zmatrix2(self, line):
        """ This reads in a z-matrix headed by the line "z-matrix (angstroms and degrees)" line.
            We only read this in if we are using a zmatrix generated by GAMESS-UK when running
            under "geometry angstrom all"
        """
        if not self.zmatrix_auto:
            if self.debug: print "## not reading zmatrix2 as not zmatrix_auto##"
            return

        zmat_buffer = [] # Buffer to hold zmatrix
        zmat_buffer.append("zmatrix angstrom")
        
        
        # skip 2 lines
        line = self.fd.readline()
        line = self.fd.readline()
        line = self.fd.readline()
        
        # Assume that the first 3 atoms are dummy z-atoms
        fields = string.split( line )
        if ( len(fields) != 2 ):
            print "ERROR reading first zmatrix line in _read_zmatrix2!"
            return
        else:
            zmat_buffer.append( fields[1] )
            
        line = self.fd.readline()
        fields = string.split( line )
        if ( len(fields) != 6 ):
            print "ERROR reading second zmatrix line in _read_zmatrix2!"
            return
        else:
            line = fields[1] + " " + fields[2] + " " + fields[3]
            zmat_buffer.append( line )
        
        line = self.fd.readline()
        fields = string.split( line )
        if ( len(fields) != 10 ):
            print "ERROR reading third zmatrix line in _read_zmatrix2!"
            return
        else:
            line =  fields[1] + " " + fields[2] + " " + fields[3] \
                   + " " + fields[6] + " "  + fields[7]
            zmat_buffer.append( line )

        # Now loop over each line reading in each zmat line until we hit the ==== line
        
        line = string.strip( self.fd.readline() )
        read = 1
        while( read ):
            fields = string.split( line )
            if line[0] == "=":
                read = 0
                break
            elif len( fields ) != 16 :
                print "ERROR reading in zmatrix in _read_zmatrix2!"
                print "Line is: %s" % line
                read = 0
                break
            else:
                line =  fields[2] + " " + fields[3] + " " + fields[4] \
                       + " " + fields[7] + " "  + fields[8]  +  " " + fields[11] + " " + fields[12]
                zmat_buffer.append(line )
                line = string.strip( self.fd.readline() )
                
        # Finished reading variables
        zmat_buffer.append( "end" )
        model = Zmatrix( list = zmat_buffer )
        self.molecules.append( model )
        return

#        # Have now read in all the lines, so skip ahead 4 lines to the variables
#        for i in range(4):
#            line = self.fd.readline()
#
#         # Read in the variables
#         zmat_buffer.append( "variables" )
#         read = 1
#         line = self.fd.readline()
#         line = string.strip( line )
#         while( read):
#             if ( len(line) == 0 or not line ):
#                 read = 0
#                 break
#             else:
#                 fields = string.split( line )
#                 if ( len( fields ) != 4 ):
#                     print "ERROR reading in variables in read_zmatrix2"
#                     read = 0
#                     break
#                 else:
#                     zmat_buffer.append( fields[0] + " " + fields[1] )
                    
#             line = self.fd.readline()
#             line = string.strip( line )
            
#         # Finished reading variables
#         zmat_buffer.append( "end" )
#         model = Zmatrix( list = zmat_buffer )
#         self.molecules.append( model )
#         return

    def _read_orbital_energies(self, line):
        line = self.fd.readline()
        line = self.fd.readline()
        line = self.fd.readline()
        norbs = 0
        while not line.isspace() and line[3:4] != '=':
            norbs += 1
            s = line.split()
            self.orbitalIrreps.append(s[1])
            self.orbitalEnergies.append(float(s[2]))
            self.orbitalOccupancies.append(float(s[3]))
            if float(s[3]) > 0.0 :
                self.homo = norbs
                self.lumo = norbs + 1
            # endif
            line = self.fd.readline()
        # end while
    #end def
    
    def _read_total_populations(self,line):
        """ This reads the mulliken and lowden population analyses following the:
            <quote> total gross population on atom </quote> line.
        """
        line = self.fd.readline()
        line = self.fd.readline()
        finished = 0
        while not finished:
            s = line.split()
            try:
                self.mullikens.append(float(s[3]))
                self.lowdins.append(float(s[4]))
            except:
                finished = 1
            line = self.fd.readline()
        #end while
    #end def

    def _read_runtype(self,line):
        """Read the runtype and do any preparations we might need for parsing this runtype."""

        runtype=line.split()[3]

        if self.debug: print "_read_runtype setting parameters for: %s " % runtype

        self.runtypes.append(runtype)
        
        #
        # Here we set certain things depending on the runtype
        if runtype == "optimize" or runtype == "optxyz":
            self.trajectories.append( objects.zmatrix.ZmatrixSequence() )
            
    #end def

    def _read_date(self,line):
        #print line.split()
        self.date = ' '.join(line.split()[1:])
    #end def

    def _read_basis(self,line):
        s = line.split()
        self.basis = s[4]+s[5]
    #enddef

    def _read_nbasis(self,line):
        self.nbasis = int(line.split()[5])
    #end def

    def _read_nshells(self,line):
        self.nshells = int(line.split()[4])
    #end def
  
    def _read_nelec(self,line):
        self.nelec = int(line.split()[3])
    #end def

    def _read_multiplicity(self,line):
        self.multiplicity = int(line.split()[2])
    #end def

    def _read_charge(self,line):
        self.charge = float(line.split()[3])
    #end def

    def _read_time(self,line):
        s = line.split()
        self.time = ''.join(s[1:])
    #end def

    def _read_scftype(self,line):
        self.scftypes.append(line.split()[3])
    #end def

    def _read_final_energies(self,line):
        """ Having found a final energies field, read in the Exchange Correlation, electronic
            nuclear and total energies and update the finalNuclearEnergy... etc fields with
            these new values. Various GAMESS-UK runs produce subtley different output so  this
            needs to be done in a fairly robust manner.
        """

        count = 0 # make sure we don't keep reading forever...
        finished = 0
        while ( not finished ):
            
            count += 1
            if ( count > 15 ):
                finished = 1
            elif( not line):
                finished = 1
                
            fields = string.split(line)
            
            if ( len( fields ) > 2 ):
                if fields[0] == "XC":
                    try:
                        self.XCEnergies.append(float(line.split()[2]))
                    except:
                        print "gamessoutputreader.py: - error reading XCEnergies in _read_final_energies!"
                        print "Offending line is %s" % line
                        
                if ( fields[0] == "electronic" ):
                    try:    
                        self.electronicEnergies.append(float(line.split()[2]))
                        self.finalElectronicEnergy = self.electronicEnergies[-1]
                    except:
                        print "gamessoutputreader.py: - error reading electronicEnergies in _read_final_energies!"
                        print "Offending line is %s" % line
                        
                if ( fields[0] == "nuclear" ):
                    try:
                        
                        self.nuclearEnergies.append(float(line.split()[2]))
                        self.finalNuclearEnergy = self.nuclearEnergies[-1]
                    except:
                        try:
                            self.nuclearEnergies.append(float(line.split()[3]))
                            self.finalNuclearEnergy = self.nuclearEnergies[-1]
                        except:
                            print "gamessoutputreader.py: - error reading nuclearEnergies in _read_final_energies!"
                            print "Offending line is %s" % line
                        
                if ( fields[0] == "total" ):
                    # Hack for qm energy
                    if ( fields[1] == "qm" ):
                        energy = fields[3]
                    else:
                        energy = fields[2]
                        
                    try:
                        self.totalEnergies.append( float(energy) )
                        self.finalTotalEnergy = self.totalEnergies[-1]
                        finished = 1
                    except:
                        print "gamessoutputreader.py: - error reading totalEnergies in _read_final_energies!"
                        print "Offending line is %s" % line

            else: # else for len(fields )>2
                pass

            line = self.fd.readline()

    #end def

    def _read_DRF_area(self,line):
        self.DRF_totalArea = float(line.split()[8])
    #def

    def _read_DRF(self,line):
        # skip 20 lines
        for i in range(0,20):
            line = self.fd.readline()
        #end for
        self.DRF_totalQMEnergy = float(line.split()[9])
        line = self.fd.readline()
        self.DRF_qm_classical = float(line.split()[9])
        line = self.fd.readline()
        self.DRF_polarisation = float(line.split()[7])
        line = self.fd.readline()
        self.DRF_qm_totalEnergy = float(line.split()[7])
    #end def


    def _read_normal_modes_force(self,line):
        """Read the normal modes of a force calculation"""


        mol = self.molecules[-1]

        # Create a vibfreqset object to hold all the vibrations
        vfs = objects.vibfreq.VibFreqSet()
        vfs.title = "Vibrations of: %s" % self.name
        vfs.reference = mol

        ncols = 9
        n = mol.get_nondum()
        maxroot = n*3

        vibrations=[]
        line = self.fd.readline()
        #Create a zero normal mode
        for root in range(1,maxroot+1):       
            v = objects.vibfreq.VibFreq(root)
            v.reference = mol
            v.disp = []
            for cnt in range(0,n):
                p = objects.zmatrix.ZAtom()
##                p.coord = [ 0.0, 0.0, 0.0 ]
##                p.name  = mol.atom[cnt].name
##                p.index = mol.atom[cnt].index
##                p.name  = mol.atom[cnt].name
##                p.symbol = mol.atom[cnt].symbol
##                v.atoms.append(p)
                vec = [0.0, 0.0, 0.0]
                v.disp.append(vec)
            #end for cnt
            vibrations.append(v)
        #end for root
        root = 0
        for root1 in range(1, maxroot+1, ncols): #Step through in columns of 8
            root7 = root1 + ncols -1              # root7 is the last column
            root7 = min(maxroot,root7)
            line = self.fd.readline()
            line = self.fd.readline()
            line = self.fd.readline()
            line = self.fd.readline()
            line = self.fd.readline()
            line = self.fd.readline()
            line = re.sub('[0-9]-[0-9]',_spliteformat,line)
            for f in line.split():         # split the frequencies up and store in the
                vibrations[root].freq = float(f)
                root += 1
            #end for f
            line = self.fd.readline()
            line = self.fd.readline()
            for i in range(1,maxroot+1):     # loop over the number of rows
                line = self.fd.readline()
                k = 0                      # if the start of an atom, skip more entries
                if i%3 == 1 :
                    k = 2
                #end if mod
                iat = int((i-1)/3)+1           # this is the atom seq. in the list
                ixyz = (i-1)%3                 # this is 0,1,2 for x,y,z
                sl = line.split()
                for j in range(root1, root7+1):
                    k += 1
                    ###self.vibrations[j-1].atoms[iat-1].coord[ixyz] = float(sl[k])
                    vibrations[j-1].disp[iat-1][ixyz] = float(sl[k])
                #end for j
            #end for i
        # end for root

        for v in vibrations:
            v.displacement = []
            for d in v.disp:
                v.displacement.append(objects.vector.Vector(d))
            del v.disp
            vfs.add_vib(v)

        # now add to vibfreqset
        self.vibration_sets.append(vfs)

    #end def
        
    def _read_normal_modes_hessian(self,line):
        """Read the normal modes of a hessian calculation"""

        if self.debug: print "_read_normal_modes_hessian: %s" % line

        # The reference molecule: optimsed structure
        mol = self.molecules[-1]

        # Create a vibfreqset object to hold all the vibrations
        vfs = objects.vibfreq.VibFreqSet()
        vfs.title = "Vibrations of: %s" % self.name
        vfs.reference = mol
        
        ncols = 8
        natoms = mol.get_nondum()
        maxroot = natoms*3


        vibrations=[]
        #Create a zero normal mode
        for root in range(1,maxroot+1):
            v = objects.vibfreq.VibFreq(root)
            v.reference = mol
            v.disp = []
            for cnt in range(0,natoms):
                p = objects.zmatrix.ZAtom()
                vec = [0.0, 0.0, 0.0]
                v.disp.append(vec)
            #end for
            vibrations.append(v)
        #endif

        
        line = self.fd.readline() # skip "===============" line
        root = 0
        for root1 in range(1, maxroot+1, ncols):
            root7 = root1 + ncols - 1
            root7 = min(maxroot,root7)

            # Skip 6 lines to col header with frequencies
            for i in range(6):
                line = self.fd.readline()

            for f in line.split():
                #self.vibrations[root].freq = float(f)
                vibrations[root].freq = float(f)
                root += 1
            #end for f
            
            # Skip 2 lines to where data matrix starts
            line = self.fd.readline()
            line = self.fd.readline()

            for i in range(1,maxroot+1):
                line = self.fd.readline()
                k = 0
                if i%3 == 1 :
                    k = 2
                #end if mod
                iat = int((i-1)/3)+1
                ixyz = (i-1)%3
                sl = line.split()
                for j in range(root1, root7+1):
                    k += 1
                    ###self.vibrations[j-1].atoms[iat-1].coord[ixyz] = float(sl[k])
                    #print "self.vibrations[%d-1].disp[%d-1].coord[%d] = float(sl[%d])" %(j,iat,ixyz,k)
                    vibrations[j-1].disp[iat-1][ixyz] = float(sl[k])
                #end for j
            #end for i
        # end for root


        for v in vibrations:
            v.displacement = []
            for d in v.disp:
                v.displacement.append(objects.vector.Vector(d))
            del v.disp
            vfs.add_vib(v)

        # now add to vibfreqset
        self.vibration_sets.append(vfs)


    def _read_frequencies_hessian(self,line):
        """Read the frequencies from a hessian calculation"""
        if self.debug: print "_read_frequencies_hessian"
        
        line = self.fd.readline()
        line = self.fd.readline()
        line = self.fd.readline()
        line = self.fd.readline()
        self.transitionFrequencies = []
        self.transitionDipoles = []
        self.transitionStrengths = []
        self.transitionIntensities = []
        search = re.compile('^ *====*')
        while not search.match(line):
            s = line.split()
            self.transitionFrequencies.append(float(s[1]))
            self.transitionDipoles.append([float(s[2]),float(s[3]),float(s[4])])
            self.transitionStrengths.append(float(s[5]))
            self.transitionIntensities.append(float(s[6]))
            line = self.fd.readline()
        #end while
    #end def


    def _read_frequencies_force(self,line):
        """Read the frequencies from a force calculation"""

        if self.debug: print "_read_frequencies_force: %s " % line
        self.transitionFrequencies = []
        self.transitionDipoles = []
        self.transitionStrengths = []
        self.transitionIntensities = []
        thisMol = self.molecules[-1]
        natoms = len( thisMol.atom )
        ncoords = natoms*3
        nfreq = ncoords - 6    #there will be a problem here if we have a large linear molecule
        nf = 0
        freq_re = re.compile(' frequencies ----')
        freq_end =  re.compile(' ={50}')

        while nf<nfreq:
            #print "line is ",line
            if freq_end.match( line ):
                if self.debug: 
                    print "Error in gamessoutputreader._read_frequencies_force"
                    print "End of frequencies section before all frequencies have been read!"
                return
            elif freq_re.match( line ):
                line = re.sub('[0-9]-[0-9]',_spliteformat,line)                
                for f in line.split()[2:]:
                    try:
                        self.transitionFrequencies.append(float(f))
                    except ValueError:
                        print "Error in gamessoutputreader._read_frequencies_force"
                        print "Offending line is: %s\n" % line
                
                nf = len(self.transitionFrequencies)                
                if nf>=nfreq:
                    break
                
            line = self.fd.readline()
        #end while
    #end def

    def _read_maximum_step(self,line):
        """add to the list of tuples containing the convergence information"""

        # Make sure this isnt the summary printed at the start
        fields = string.split(line) 
        if ( len( fields ) > 3 ):
            if ( fields[2] == "length" ):
                return
        
        words1 = string.split( line  )# max step
        words2 = string.split( self.fd.readline() ) # average step
        words3 = string.split( self.fd.readline() ) # max gradient
        words4 = string.split( self.fd.readline() ) # max gradient

        try:
            av_step  = float( words1[2] )
            max_step = float( words2[2] )
            max_grad = float( words3[2] )
            av_grad  = float( words4[2] )
            self.maximumSteps.append( ( av_step, max_step, max_grad, av_grad) )
        except:
            print "Error reading output in _read_maximum_step!"
    #enddef

    def _read_dipole(self,line):
        line = self.fd.readline()
        line = self.fd.readline()
        line = self.fd.readline()
        line = self.fd.readline()
        line = self.fd.readline()
        self.nuclearDipole = []
        self.nuclearDipole.append(float(line.split()[1]))
        self.electronicDipole.append(float(line.split()[3]))
        self.totalDipole.append(float(line.split()[3]))
        line = self.fd.readline()
        self.nuclearDipole.append(float(line.split()[1]))
        self.electronicDipole.append(float(line.split()[3]))
        self.totalDipole.append(float(line.split()[3]))
        line = self.fd.readline()
        self.nuclearDipole.append(float(line.split()[1]))
        self.electronicDipole.append(float(line.split()[3]))
        self.totalDipole.append(float(line.split()[3]))
        line = self.fd.readline()
        line = self.fd.readline()
    #end def
    
    def printAll():
        """Print all the information contained in this object"""


    #end def

##########################################################
#
#
# Unittesting stuff goes here
#
#
##########################################################

class testGAMESSUK_IO(unittest.TestCase):
    """Test whether we can read a GAMESS-UK Output file"""

    egdir=gui_path+os.sep+'examples'+os.sep

    def testOutputOptimize(self):
        """ """
        
        reader = GUKOutputIO()
        trajectories = reader.GetObjects(
            filepath=self.egdir+'UHF_opt.pyridine.8x4.out',
            otype = 'trajectories'
            )

        # Should return one trajectory object
        self.assertEqual( len(trajectories),1)



    def testOutputOptimizeHessian(self):
        """ """
        
        reader = GUKOutputIO()
        objects = reader.GetObjects(
            filepath=self.egdir+'SECD_opt.pyridine.6-31G-dp.8x4.out'
            )

        self.assertEqual( len(objects), 3 )
        self.assertEqual( reader.GetClass( objects[0] ), 'Zmatrix' )
        self.assertEqual( reader.GetClass( objects[1] ), 'ZmatrixSequence' )
        vfs=objects[2]
        self.assertEqual( reader.GetClass( vfs ), 'VibFreqSet' )
        self.assertEqual( vfs.vibs[9].freq, 719.94 )


    def testOutputSurf(self):
        """ """
        
        reader = GUKOutputIO()
        objects = reader.GetObjects(
            filepath=self.egdir+'gamess_surf.out'
            )

        self.assertEqual( reader.GetClass( objects[0] ), 'Zmatrix' )

    def testOutputVect(self):
        """ """
        
        reader = GUKOutputIO()
        objects = reader.GetObjects(
            filepath=self.egdir+'gamess_vect.out'
            )

        self.assertEqual( reader.GetClass( objects[0] ), 'Zmatrix' )

    def testOutputVect3D(self):
        """ """
        
        reader = GUKOutputIO()
        objects = reader.GetObjects(
            filepath=self.egdir+'gamess_vect3d.out'
            )

        self.assertEqual( reader.GetClass( objects[0] ), 'Zmatrix' )



def testMe():
    """Return a unittest test suite with all the testcases that should be run by the main 
    gui testing framework."""

    return  unittest.TestLoader().loadTestsFromTestCase(testGAMESSUK_IO)

if __name__ == "__main__":
    unittest.main()
