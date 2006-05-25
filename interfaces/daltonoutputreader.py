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
import re
import string
from objects import zmatrix

# Define bohrs 2 anstrom - this really needs to be stored globally
bohr_2_angs = 0.529177
angs_2_bohr = eval( "1 / 0.529177 " )


class DaltonOutputReader:
    """ Read a Dalton output file, list of strings read from an outputfile and store relevant information.
        A dictionary of tuples is defined, which is keyed by a string that just serves to
        identify the information that is being searched for. The first item in the tuple
        is the python regular expression for the string in the output file that identifies the
        data item of interest. The second item is a method that is called when the regular expression
        in the first item has been matched, and actually reads in the data item.
        The file is parsed line by line and each line is checked to see if any of the regexp's from
        the dictionary match.
    """
    
    def __init__(self, ofile=None, olist=None ):
        
        # To check if we are in file or list mode
        self.file = None
        self.list = None
        self.debug = 0

        self.molecules = []    # use to hold the list of molecules

        # List of data items we are looking for
        self.type = 'Dalton output'
        self.title = None
        self.name = ''
        self.date = ''
        self.charge = 0
        self.multiplicity = 0

        self.geomoptsteps = [] # list to hold information on the individual geom opt steps
        # Need to think more about how to set this up. Each item in the list will be a dictinoary
        # holding information on a particular optimisation step, the key specifying the type of info.
        self.finalNuclearEnergy = 0.0
        self.finalElectronicEnergy = 0.0
        self.finalTotalEnergy = 0.0

        self.manage  = {}      # Manage holds a tuple with a matching string, and function to handle

        # Define a regexp to search for and the routine to read the data
        self.manage['date'] = ( re.compile('^  *Date and time' ) , self._read_date )
        self.manage['spin'] = ( re.compile('^  *Spin multiplicity') , self._read_multiplicity )
        self.manage['charge'] = ( re.compile('^  *Total charge of the molecule') , self._read_charge )
        self.manage['diis_energies'] = ( re.compile('^  *Iter *Total energy *Error norm') , self._read_diisE )
        self.manage['sirius_final_energies'] = ( re.compile('^ *>>> FINAL RESULTS FROM SIRIUS <<<') , self._read_sirius_final_energies )
        self.manage['initial_geom'] = ( re.compile('^  *Cartesian Coordinates') , self._read_initialxyz )
        self.manage['geomopt_structure'] = ( re.compile('^  *Next geometry \(au\)') , self._read_optstepxyz )
        #self.manage['final_geom'] = ( re.compile('^  *Total charge of the molecule') , self._read_charge )


        # Check if we are reading a list or a file
        if ( ofile ):
            try:
                self.file = open( ofile, 'r' )
            except Exception, e:
                print "Error opening output file in Dalton output reader!: %s" % e
                return
            
        elif( olist ):
            self.list = olist
        else:
            print "Dalton output reader must be called with a file or a list as an argument!"
            return
        
        # Loop through the contents of the file a line at a time and parse the contents
        line = self.getline()
        while line:
            #print line
            for k in self.manage.keys():
                if self.manage[k][0].match(line):
                    #print 'Match found %s' % k
                    self.manage[k][1](line)
                    break
            line = self.getline()
            
        #end while
        if ( self.file ):
            self.file.close()
        return 
    #end def
    

    def getline( self ):
        """ Method to get a line that will work with either a file or a list of strings
        """

        if ( self.file ):
            line = self.file.readline()
        elif ( self.list ):
            line = self.list.pop(0)
        else:
            # If we have been called with a list, self.list is empty after the last pop
            # therefore, the only time self.file & self.list should be empty is after
            # the last pop.
            line = None

        return line

    def _read_date( self, line ):
        """ Get the first instance of the date printed by the program
        """
        if ( len( self.date ) == 0 ):
            # split the line at the :  take the latter part and remove spaces
            i = string.index( line,":" )
            date = line[i+1:]
            self.date = string.strip( date )
            return
        else:
            return
        

    def _read_multiplicity( self, line ):
        """ Get the spin multiplicity
        """

        try:
            line = string.strip( line )
            spin = int( string.split( line )[2] )
            return
        except Exception, e:
            print "Error reading spin multiplcity in dalton output!: %s" % e
        
    def _read_charge( self, line ):
        """ Get the charge from the:
            Total charge of the molecule
            line
        """
        try:
            line = string.strip( line )
            fields = string.split( line )
            self.charge = float( fields[5] )
        except Exception, e:
            print "Error reading charge in Dalton output!: %s" % e

        return

    def _read_diisE( self, line ):
        """ Read the per cycle information for an scf convergence cycle.
            This was just done for testing purposes and takes no account of
            diis failure etc.
        """

        # Lazy again - skip 5 lines to get to the cycles
        for i in range( 6 ):
            self.getline()
            #print "skipped line"

        # Add a dictionary for this step - this is done here as it is currently the
        # first item that we are looking for in a geometry optimisation.
        geominfo = {}
        geominfo['diisE'] = []


        line = self.getline()

        while( line[0:4] != "DIIS" ):
            fields = string.split( line )
            # All sort of crap gets printed, so we need to see if we can
            # convert the first field to an int and assume that's the cycle info line
            try:
                cycleno = int( fields[0] )
                E = float( fields[1] )
                geominfo['diisE'].append( E )
            except:
                pass
            
            line = self.getline()
            line = string.strip( line )

        # End of loop so append the  newly created list    
        self.geomoptsteps.append( geominfo )
        

    def _read_sirius_final_energies( self, line ):
        """ Get the final energies from the sirius module
        """

        # skip five lines - or would this be a better place to get the spin et al from?
        self.getline()
        self.getline()
        self.getline()
        self.getline()
        self.getline()

        line = self.getline()
        try:
            self.finalTotalEnergy = float( string.split( line )[3] )
        except Exception, e:
            print "Error reading finalTotalEnergy in dalton output!: %s",e
            
        line = self.getline()
        try:
            self.finalNuclearEnergy = float( string.split( line )[2] )
        except Exception, e:
            print "Error reading finalNuclearEnergy in dalton output!: %s",e

        line = self.getline()
        try:
            self.finalElectronicEnergy = float( string.split( line )[2] )
        except Exception, e:
            print "Error reading finalElectronicEnergy in dalton output!: %s",e

        return

    def _read_initialxyz( self, line ):
        """ Read in the initial structure starting at the line:
            Cartesian Coordinates

        """
        # Assume that there will always be 2 lines to ignore
        self.getline()
        self.getline()

        # Read in the number of coordinates
        line = string.strip( self.getline() )
        
        # The try/except bit here is just a quick hack to deal with the fact that I think
        # different versions of Dalton may print this differently
        try:
            fields = string.split( line )
            ncoords = int (fields[4] )
        except IndexError:
            try:
                fields = string.split( line, ':' )
                ncoords = int( fields[1] )
            except ValueError:
                print "Error reading coordinates in daltonoutputreader _read_initialxyz!"
        
        natoms = ncoords / 3

        # Create a molecule
        molecule = zmatrix.Zmatrix()

        # bin a line
        self.getline()

        # Loop over the number of atoms - at each iteration read in the
        # 3 coords followed by the blank line
        for i in range( natoms ):
            atom = zmatrix.ZAtom()
            
            line = string.strip( self.getline() )
            #print "line1 ",line
            fields = string.split( line )
            atom.name = fields[1]
            atom.symbol = molecule.get_element_from_tag( atom.name )
            
            if ( len ( fields )  == 5 ):
                x = float( fields[4] ) * bohr_2_angs
            elif ( len ( fields ) == 4 ):
                x = float ( fields[3] ) * bohr_2_angs

            line = string.strip( self.getline() )
            #print "line2 ",line
            fields = string.split( line )
            y = float( fields[2] ) * bohr_2_angs

            line = string.strip( self.getline() )
            #print "line3 ",line
            fields = string.split( line )
            z = float( fields[2] ) * bohr_2_angs

            atom.coord = [ x, y, z]
            atom.index = i - 1
            molecule.add_atom( atom )
            
            self.getline() # blank line
            
        self.molecules.append( molecule )
                

    def _read_optstepxyz( self, line ):
        """ Read in an intermediate structure from a geometry optimisation, starting at the
            Next geometry (au)
            line
        """
        # Be lazy and assume that there will always be 2 blank lines b4 the coordinates
        self.getline()
        self.getline()

        # Create the molecule
        molecule = zmatrix.Zmatrix()
            
        line = string.strip( self.getline() )
        index = 0
        while ( len( line ) != 0 ):
            fields = string.split( line )

            try:
                if ( len( fields ) == 4 ):
                    name = fields[0]
                    x = float( fields[1] ) * bohr_2_angs
                    y = float( fields[2] ) * bohr_2_angs
                    z = float( fields[3] ) * bohr_2_angs
                elif ( len ( fields ) == 5 ) :
                    name = fields[0]
                    x = float( fields[2] ) * bohr_2_angs
                    y = float( fields[3] ) * bohr_2_angs
                    z = float( fields[4] ) * bohr_2_angs
                else:
                    print "Unrecognised number of fields in _read_optstepxzy!"

                atom = zmatrix.ZAtom()
                atom.name = name
                atom.symbol = molecule.get_element_from_tag( name )
                atom.coord = [ x, y, z ]
                atom.index = index
                molecule.add_atom( atom )
                index += 1
                
            except Exception, e:
                print "Error reading in coordinates in _readoptstepxyz!: %s" % e


            line = string.strip( self.getline() )
            
        # end of while loop
        
        # Add the molecule
        self.molecules.append( molecule )


    # Here follows a list of methods that can be expected to be called by external functions
    # that are querying us for bits and bobs
    def get_molecules( self ):
        """ Return the list of molecules that we have read
        """
        if len( self.molecules ) > 0 :
            return self.molecules
        else:
            return None
    
    def list_summary( self ):
        """ Return a list of strings containing the summary.
        """

        slist = []
        slist.append( "Summary of a dalton output file generated by the CCP1GUI\n" )
        slist.append( "--------------------------------------------------------\n\n" )
        slist.append('Date = %s\n' % self.date)
        slist.append('Multiplicity = %s\n' % self.multiplicity)
        slist.append('Charge = %s\n' % self.charge)
        slist.append('Final nuclear energy = %s\n' % self.finalNuclearEnergy)
        slist.append('Final electronic energy = %s\n' % self.finalElectronicEnergy)
        slist.append('Final total energy = %s\n' % self.finalTotalEnergy)

        return slist

    def get_geomoptsteps( self ):
        """ Return the list with information about the geometry optimisations
        """
        if ( len( self.geomoptsteps ) > 0 ):
            return self.geomoptsteps
        else:
            return None


if __name__ == "__main__":

    import sys
    if ( len( sys.argv ) != 2 ):
        print "%s needs a file to test!" % sys.argv[0]
        sys.exit(0)
        
    test = sys.argv[1]
    f = open( test, 'r' )
    d = DaltonOutputReader( ofile=test )
    print "file is %s" % test
    print "date is %s" % d.date
    print "charge is %f" % d.charge
    print "finalNuclearEnergy = %f" % d.finalNuclearEnergy
    print "finalElectronicEnergy = %f" % d.finalElectronicEnergy
    print "finalTotalEnergy = %f" % d.finalTotalEnergy
    molecules = d.get_molecules()
    print "molecules ",molecules
    for mol in molecules:
        print "mol is ",mol
        #print "mol.title is ",mol.title
        #if not mol.title:
        for atom in mol.atom:
            print "atom.coord are ",atom.coord
        #mol.name = ed.graph.make_unique_name( mol.name )
        #ed.graph.quick_mol_view( mol )
        #ed.graph.append_data( mol )
        #ed.graph.connect_model( mol )
        #index += 1
    l = d.get_geomoptsteps()
    for step in range( len( l ) ):
        print "step ",step

    i = 0
    for step in l:
        print "step"
        cycle = 0
        for e in step['diisE']:
            print "step %d cycle %d e is %E" % ( i, cycle, e )
            cycle += 1
        i += 1
    
    
    
