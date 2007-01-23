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
"""A molecule representation including internal coordinates.

This is derived from the PyMOL chempy class Indexed with provision
for storage of the internal coordinates.
"""

#
# -999s show up as -998 when a better message would be
#   "reference to undefined or incorrectly defined atom"
#
#  fragments should perhaps incorporate variables, or at
#  least flag the independent variables for use in optimisations
#
#  perhaps the fragment lib is best kept as a bunch of files?
#  or held in strings and then processed on demand?
#  (these two could easily be combined)
#
import math
import copy
import exceptions
import string
import re
import symdet

# From Konrad Hinsens scientific python
from Scientific.Geometry.VectorModule import *

import Numeric,LinearAlgebra


from objects.periodic import rcov, sym2no, atomic_mass, name_to_element, get_bond_length
from chempy import cpv, atomic_number

pi_over_180 = math.atan(1.0) / 45.0
dtorad = pi_over_180
trans = string.maketrans('a','a')

SMALL = 1.0e-4

NO_CHECK=1
ORDER_CHECK=2
OK_CHECK=3

orig = [0.0, 0.0, 0.0]
xvec = [1.0, 0.0, 0.0]
zvec = [0.0, 0.0, 1.0]

fp0 = None

#
# define some exceptions
#
class ImportGeometryError(exceptions.Exception):
    def __init__(self,args=None):
        self.args = args

class Atom:
    def __init__(self):
        self.symbol             = 'X'
        self.name                = ''
        self.resn                = 'UNK'
        self.resn_code           = 'X'
        self.resi                = '1'
        self.resi_number         = 1
        self.b                   = 0.0
        self.q                   = 1.0
        self.vdw                 = 0.0
        self.alt                 = ''
        self.hetatm              = 1
        self.segi                = ''
        self.chain               = ''
        self.coord               = [9999.999,9999.999,9999.999]
        self.formal_charge       = 0.0
        self.partial_charge      = -9999.0
        # Flags
        self.flags               = 0
        # Force-fields
        self.numeric_type        = -9999
        self.text_type           = '??'
        # MDL Mol-files
        self.stereo              = 0
        # Macromodel files
        self.color_code          = 2
        # PAUL HACK
        self.seqno               = -1
        self.selected            = 0

    def get_mass(self):
        '''Given the chemical symbol the atomic mass is returned'''      
        return atomic_mass[self.symbol]

    def get_number(self):
        '''Given the chemical symbol the atomic number is returned'''
        try:
            return sym2no[self.symbol]
        except KeyError:
            return 0

    def get_index(self):
        '''Sequence number in molecule'''
        return self.seqno

    def get_index2(self):
        '''Sequence number in molecule'''
        return self.seqno2

    def get_name(self):
        if self.title:
            return self.title
        else:
            return "untitled zmat"

    def get_connected( self, root, visited=[], start=None ):
        """ Determine if an atom is a fragment by recursively finding all atoms connected
            to it, following all connections bar root, which is the parent atom that lies
            'above' this one in the connectivity tree. 'start' is the atom attached to the main
            molecule that the search was first started from. If we end up back at start then
            the atom is not part of a fragment.
            We return a list of the atoms that constitute this fragment, or None if the function
            loops back on itself
        """

        debug = None

        def remove_duplicates(AtomList):
            tmp = []

            for atom in AtomList:
                if atom not in tmp:
                    tmp.append( atom )
            return tmp
            
        
        # First call should remember the root - this is then passed down to all other invocations
        first_pass = None
        if not start:
            first_pass = 1
            start = root

        if not first_pass:
            if self == start:
                return None

        if len(self.conn) == 1:
            if debug: print "Found terminus: %s:%s" % (self.name,self.get_index()+1)
            return [self]

        all_visited = copy.copy(visited)
        for bonded in self.conn:
            if bonded != root:
                all_visited.append( bonded )

        if self in all_visited:
            if debug: print "Looped back to atom %s:%s" % (self.name,self.get_index()+1)
            return []
        elif start in all_visited:
            print "Fragment Loops back onto the start atom!"
            return None
        
        # Can now add self
        all_visited.append(self)

        if debug:
            print "Checking connectivity for %s:%s" % (self.name,self.get_index()+1)
            for bonded in self.conn:
                print "Links %s:%s" % (bonded.name,bonded.get_index()+1)
                
        # Get the lists of all atoms bonded to this one
        atomList = []
        for bonded in self.conn:
            if bonded != root and bonded not in visited:
                if debug: print "Following track down atom: %s:%s" % (bonded.name,bonded.get_index()+1)
                try:
                    this=all_visited.index(bonded)
                    del all_visited[this]
                    if debug: print "deleting %s:%s from all_visited" % (bonded.name,bonded.get_index()+1)
                    bondedList = bonded.get_connected( self, visited=all_visited, start=start )
                    # Need to check we haven't looped back via a ring - this check might be redundant
                    if self in bondedList: # we've looped back so don't follow this path again
                        if debug: print "found self in bondedList"
                        pass
                    else:
                        atomList.extend( bondedList )
                except TypeError:
                    # we've been returned a None indicating that the fragment connects
                    # back to the start
                    return None

        atomList.append( self )
        if debug: print "Atom %s:%s returning:" % (self.name, self.get_index()+1)
        atomList = remove_duplicates( atomList )
        return atomList
        
    def rotate(self, angle, axis, center = [0.0,0.0,0.0]):
        """Rotate the atom around center"""
        angle = angle *dtorad
        R = cpv.rotation_matrix(angle,axis)
        print 'R=',R
        print 'centre=',center
        rt = cpv.sub(self.coord,center)
        print 'initial coords',self.coord
        print 'rt',rt
        print 'trans rt',cpv.transform(R,rt)
        self.coord = cpv.add(cpv.transform(R,rt),center)
        print 'rotated atom coords',self.coord

class Bond:
    def __init__(self):
        pass


class Indexed:
    def __init__(self):
        self.atom = []

#####    def reset(self):
        self.index = None
##        self.molecule = chempy.Molecule()
        self.atom = []
        self.shell = []
        self.bond = []

    # also need to adapt connectivity data
    def delete_atom(self,index):

        self.delete_list([index])

    def delete_list(self,list):
        deadmen = []
        for a in self.atom:
            a.tempflag=0
        for i in list:
            deadmen.append(self.atom[i])
            self.atom[i].tempflag=1

        print 'sorting shells'
        # keep only attached shells
        oldshell = self.shell
        self.shell = []
        for s in oldshell:
            if not s.linked_core.tempflag:
                self.shell.append(s)

        # remove the atoms and clean connectivity
        for a in deadmen:
            self.delete_atom_obj(a)
        self.reindex()

    def delete_atom_obj(self,a):
        for c in a.conn:
            c.conn.remove(a)
        self.atom.remove(a)

    def reindex(self):
        k = 0
        kk = 0
        for a in self.atom:
            a.seqno = k
            k = k + 1
            if a.get_number() > 0:
                a.seqno2 = kk
                kk = kk + 1
            else:
                a.seqno2 = -1

        k = 0
        for a in self.shell:
            a.seqno = k
            k = k + 1

        self.nondum = kk 

    def get_nondum(self):
        """Returns the count of non-dummy atoms"""
        return self.nondum

    def list(self):
        for a in self.atom:
            txt = ''
            try:
                for b in a.conn:
                    txt = txt + '%d ' % (b.get_index() + 1) 
            except AttributeError:
                pass

            print a.get_index()+1, a.seqno+1, a.symbol, a.name, 
            for coor in a.coord:
                print "%10.5f" % (coor,),
            print txt

        if len(self.shell):
            print 'Shells:'
            for a in self.shell:
                print a.get_index(), a.seqno, a.symbol, a.name,  a.coord, a.linked_core.get_index()+1

        for a in self.bond:
            print a.index

    def get_mass(self):
        sm = 0.0
        for a in self.atom:
            sm = sm + a.get_mass()
        return sm

#------------------------------------------------------------------------------
    def get_nuclear_charges(self):
        '''Return the sum of nuclear charges of all atoms in a molecule.'''
        sm = 0
        for a in self.atom:
            sm = sm + a.get_number()
        return sm

class ConversionError(exceptions.Exception):
    def __init__(self,args=None):
        self.args = args

class VariableError(exceptions.Exception):
    def __init__(self,args=None):
        self.args = args

class Zmatrix(Indexed):

    def __init__(self, mol=None,file=None,list=None,title=None,debug=0):
        apply(Indexed.__init__, (self,))

        self.v_key = 0
        self.debug = debug
        self.debug_frag = debug
        self.is_frag = 0
        self.variables = []
        self.cell = []
        # for selection manager
        self.selix=0

        # for editor
        self.errors = []

        #
        # phi convention
        #
        self.phi_convention = 1

        self.charge_sets=[]
        if title:
            self.title = title
        else:
            self.title = "Untitled molecule"

        if mol:
            # Import from PyMol molecule object
            # copy attributes of the molecule
            self.atom = copy.deepcopy(mol.atom)
            ####self.bond = copy.deepcopy(mol.bond)
            ####self.variables = copy.deepcopy(mol.variables)
            
            for a in self.atom:
                a.zorc = 'c'
                a.r_var = None
                a.theta_var = None
                a.phi_var = None
                a.x_var = None
                a.y_var = None
                a.z_var = None
                a.i1 = None
                a.i2 = None
                a.i3 = None
                a.r = 1.0
                a.theta = 90.0
                a.phi = 0.0
                a.r_sign =1.0
                a.theta_sign = 1.0
                a.phi_sign = 1.0
                a.x_sign = 1.0
                a.y_sign = 1.0
                a.z_sign = 1.0
                a.ok  = 1

            self.reindex()
            self.update_conn()

        if file:
            self.load_from_file(file)
        elif list:
            self.load_from_list(list)

    def zlist(self,full=0):
        txt = self.output_zmat(full=full)
        for rec in txt:
            print rec
        apply(Indexed.list,(self,), {})

    def copy(self):
        self.update_bonds()

        if self.__dict__.has_key('tidy'):
            t=self.tidy
            self.tidy=None
        else:
            t=None
        new = copy.deepcopy(self)
        new.update_conn()
        if t:
            self.tidy=t
            new.tidy=t
        return new
    
    def load_from_file(self,file):

        f = open(file,'r')
        txt = f.readlines()
        f.close()
        return self.load_from_list(txt)

    def load_from_list(self,otxt):

        txt = copy.copy(otxt)
        self.variables = []
        mode = 'i'
        fac = 0.529177 
        while len(txt):

            a = txt[0]
            txt.pop(0)

            a = string.lstrip(a)
            fields = string.split(a)

            if not len(fields):
                continue

            f0 = string.lower(fields[0])

            if ( f0[0:4] == 'zmat' ) or ( f0[0:4] == 'inte' ):
                mode = 'z'
                # interpret unit specifier if present
                if len(fields) > 1:
                    fac = self.rescale( fields[1] )

            elif ( f0[0:4] == 'coor') or ( f0[0:4] == 'cart') or ( f0[0:4] == 'geom' ):
                mode = 'x'
                # interpret unit specifier if present
                if len(fields) > 1:
                    fac = self.rescale(fields[1])

            elif ( f0[0:4] == 'vari' ):
                mode = 'v'
                if len(fields) > 1:
                    fac = self.rescale(fields[1])
            elif f0[0:4] == 'cons':
                mode = 'c'
                if len(fields) > 1:
                    fac = self.rescale(fields[1])
            elif f0[0:3] == 'end':
                mode = 'i'
            else:
                if mode == 'i':
                    pass
                if mode == 'z' or mode == 'x':

                    # load in a new atom
                    a = ZAtom()
                    a.coord = [0.0,0.0,0.0]
                    self.atom.append(a)
                    a.name = fields[0]
                    a.symbol = name_to_element( a.name )

                    if mode == 'z':

                        a.zorc = 'z'
                        if(len(fields)) > 1:

                            try:
                                i1 = int(fields[1])
                                a.i1 = self.atom[i1-1]
                            except ValueError, e:
                                a.i1 = self.find_atom(fields[1])

                            try:
                                a.r = float(fields[2])*fac
                                a.r_var = None
                            except ValueError, e:
                                a.r_var, a.r_sign = self.find_var_or_create(fields[2],0.0,'d')

                        if(len(fields)) > 3:

                            try:
                                i2 = int(fields[3])
                                a.i2 = self.atom[i2-1]
                            except ValueError, e:
                                a.i2 = self.find_atom(fields[3])

                            try:
                                a.theta = float(fields[4])
                                a.theta_var = None
                            except ValueError, e:
                                a.theta_var, a.theta_sign = self.find_var_or_create(fields[4],0.0,'a')

                        if(len(fields)) > 5:

                            try:
                                i3 = int(fields[5])
                                a.i3 = self.atom[i3-1]
                            except ValueError, e:
                                a.i3 = self.find_atom(fields[5])
                            try:
                                a.phi = float(fields[6])
                                a.phi_var = None
                            except ValueError, e:
                                a.phi_var, a.phi_sign = self.find_var_or_create(fields[6],0.0,'a')

                        if(len(fields)) > 7:
                            if fields[7] == "charge":
                                a.partial_charge = float(fields[8])
                            else:
                                print 'TRAILING JUNK IGNORED', fields[7:]

                    if mode == 'x':

                        a.zorc = 'c'
                        try:
                            a.coord[0] = float(fields[1])*fac
                            a.r_var = None
                        except ValueError, e:
                            a.x_var, a.x_sign = self.find_var_or_create(fields[1],0.0,'d')

                        try:
                            a.coord[1] = float(fields[2])*fac
                            a.y_var = None
                        except ValueError, e:
                            a.y_var, a.y_sign = self.find_var_or_create(fields[2],0.0,'d')

                        try:
                            a.coord[2] = float(fields[3])*fac
                            a.z_var = None
                        except ValueError, e:
                            a.z_var, a.z_sign = self.find_var_or_create(fields[3],0.0,'d')

                        if(len(fields)) > 4:
                            if fields[4] == "charge":
                                a.partial_charge = float(fields[5])
                            else:
                                print 'TRAILING JUNK IGNORED', fields[4:]

                if mode == 'c' or mode == 'v':
                    # At this stage the variables should already exist
                    # so this call should just look it up
                    # and there should be no leading sign flag
                    v = self.find_var(fields[0])
                    if v:
                        v.value= float(fields[1])
                        # apply scaling to distance only
                        if v.metric == 'd':
                            v.value = v.value * fac
                        if mode == 'c':
                            v.constant = 1

                        # Append any keys (e.g. type 3 for GAMESS-UK use)
                        v.keys = ""
                        for k in fields[2:]:
                            v.keys = v.keys + " " + k
                            self.v_key = 1 

                    else:
                        # for now we ignore stray vars
                        pass

        # At this stage, there may be some variables with values of 0
        # i1,i2,i3 still none?

        # Fill in index array as we use it for
        # some pymol mapping operations
        # to be deleted in future
        self.reindex()
        # since we don't have any bonding info we can just guess
        # from the input connectivity
        # to be replaced later
        for a in self.atom:
            if a.i1:
                a.conn.append(a.i1)
                a.i1.conn.append(a)

        #      for a in self.atom:
        #         a.index = a.get_index() + 1
        #         a.id = a.get_index()

        self.calculate_coordinates()

    #
    #  Variable editing window
    #
    def find_var_or_create(self,txt,value,metric):
        """ Locate a variable and create one if it doesnt exist
        txt    - variable name
        value  - value to create with
        metric - 'd' for distance or 'a' for angles
                 'x' will generate an VariableError exception if the variable doesnt exist
        Returns a two-element tuple of (variable,sign)
        """
        if txt[0] == '-':
            sign = -1.0
            txt = txt[1:]
        else:
            sign = 1.0

        var = self.find_var(txt)

        if var == None:
            if metric == 'x':
                print 'Bad variable name: ' + txt
                raise VariableError
            # create a variable, initialised to the provided value 
            var = self.new_var(txt,value,metric)
            
        return (var,sign)

    def find_var(self,txt):
        """ Locates a variable from its name
        """
        # Look it up in the variable list
        var = None
        for v in self.variables:
            if txt == v.name:
                return v
        return None

    def new_var(self,name,value,metric):
        """Add a new variable"""
        v = ZVar()
        self.variables.append(v)
        v.name = name
        v.value = value
        v.metric = metric
        if self.v_key:
            v.keys = " "
        return v
    
    def find_atom(self,qname):
        """ Search for an atom name in a molecule and return the atom object.
        """
        found=0
        for a in self.atom:
            if a.name == qname:
                atom = a
                found = found+1
 
        if found == 0:
            print 'No matching atom name for z-matrix variable: '+str(qname)
            return None
             #raise and error
                
        if found > 1:
            print 'More than one atom in this z-matrix has the same name!'
            #raise AtomNameError
            return None

        return (atom)

    def rescale(self,key):
        """Change the scaling factor when reading in a z-matrix if we switch
        from Angstroms to Bohrs or v.v.
        """
        key = string.lower( key )
        if key[0:4] == 'angs':
            fac = 1.0
        elif key[0:4] == 'bohr' or key[0:4] == 'a.u.' or key[0:2] == 'au':
            fac = 0.529177
        else:
            print "ERROR reading in factor in rescale in zmatrix.py!!!"
            print "Errant key is: %s" % fac
            fac = 0.529177
        
        return fac
        
    def output_zmat(self,full=0,charges=1):
        """Return a text form of the z-matrix
        format is that used by the chemshell z_create module
        """
        out = []
        ozorc = 'q'
        ###self.update_conn()
        for a in self.atom:
            if a.zorc != ozorc:
                if a.zorc == 'z':         
                    out.append('zmatrix angstrom')
                elif a.zorc == 'c':
                    out.append('coordinates angstrom')
                ozorc = a.zorc

            if full:
                txt = self.output_atom_full(a,list_final_coords=full)
            else:
                txt = self.output_atom(a)        

            if charges:
                if abs( a.partial_charge - -9999.0) > 0.0001:
                    txt = txt + 'charge ' + str(a.partial_charge)

            out.append(txt)

        if len(self.shell):
            out.append('shells')
            for a in self.shell:
                txt = self._output_shell(a)
            out.append(txt)

        test=0
        for a in self.variables:
            if not a.constant:
                test=1

        if test:
            out.append('variables angstrom')
            for a in self.variables:
                if not a.constant:
                    txt = self.__output_var(a)
                    out.append(txt)
        test=0
        for a in self.variables:
            if a.constant:
                test=1

        if test:
            out.append('constants angstrom')
            for a in self.variables:
                if a.constant:
                    txt = self.__output_var(a)
                    out.append(txt)
        return out

    def __output_var(self,v):
        """output variable name and value (could be __str method of variable) """
        txt = '%8s %14.6f ' % (v.name, v.value)
        if self.v_key:
            txt = txt + v.keys
        return txt

    def __output_var_full(self,v):
        """as self.__output_var, except that constants are denoted"""
        txt = self.__output_var(v)
        if v.constant:
            txt = txt + '    [constant]'
        return txt

    def output_atom_full(self,a,list_final_coords=0):
        """Generate the selection box record for a single atom
        it includes (optionally) the final coords and also
        the connectivity data
        """

        v_con = ' '
        for b in a.conn:
            v_con = v_con + '%d ' % (b.get_index()+1)

        if list_final_coords:
            if a.ok:
                v_xx = '%12.4f' % (a.coord[0])
                v_yy = '%12.4f' % (a.coord[1])
                v_zz = '%12.4f' % (a.coord[2])

            else:
                v_xx = '************'
                v_yy = '************'
                v_zz = '************'

            txt = '%4d %52s %8s %8s %8s %s' % (a.get_index()+1,
                                            self.output_atom(a),
                                            v_xx, v_yy, v_zz,v_con)
        else:
            txt = '%4d %52s %s' % (a.get_index()+1,
                                            self.output_atom(a),v_con)

        return txt

    def output_atom(self,a):
        """this routine handles the coordinates/variable names part
        it is used by both output_atom_full and output_zmatrix
        """

        n = a.get_index()

        # Hack for fragments
        if self.is_frag:
            n = 4

        if a.zorc == 'z':

            if a.r_var == None:
                v_r = '%10.4f' % (a.r)
            else:
                txt = a.r_var.name
                if a.r_sign == -1.0:
                    txt = '-' + txt
                v_r = '%10s' % txt

            if a.theta_var == None:
                v_theta = '%10.4f' % (a.theta)
            else:
                txt = a.theta_var.name
                if a.theta_sign == -1.0:
                    txt = '-' + txt
                v_theta = '%10s' % txt

            if a.phi_var == None:
                v_phi = '%10.4f' % (a.phi)
            else:
                txt = a.phi_var.name
                if a.phi_sign == -1.0:
                    txt = '-' + txt
                v_phi = '%10s' % txt

            i1 = -1
            i2 = -1
            i3 = -1

            # The x fields are used when holding fragments
            # for the editor (see zfragment.py)
            if a.i1:
                i1 = a.i1.get_index()
            else:
                try:
                    i1 = a.i1x
                except AttributeError:
                    pass

            if a.i2:
                i2 = a.i2.get_index()
            else:
                try:
                    i2 = a.i2x
                except AttributeError:
                    pass

            if a.i3:
                i3 = a.i3.get_index()
            else:
                try:
                    i3 = a.i3x
                except AttributeError:
                    pass

            if n == 0:
                txt = '%6s                                                  ' % (
                   a.name)
                    #a.symbol)

            elif n == 1:
                txt = '%6s %4d %10s                                  ' % (
                   a.name,i1+1,v_r)
                    #a.symbol,i1+1,v_r)

            elif n == 2:
                txt = '%6s %4d %10s %4d %10s                  ' % (
                   a.name,i1+1,v_r,i2+1,v_theta)
                    #a.symbol,i1+1,v_r,i2+1,v_theta)

            else:
                txt = '%6s %4d %10s %4d %10s %4d %10s  ' % (
                   a.name,i1+1,v_r,i2+1,v_theta,i3+1,v_phi)
                    #a.symbol,i1+1,v_r,i2+1,v_theta,i3+1,v_phi)

        else:
            # This else clause for Cartesian atoms
            if a.x_var == None:
                v_x = '%14.6f' % (a.coord[0])
            else:
                txt = a.x_var.name
                if a.x_sign == -1.0:
                    txt = '-' + txt
                v_x = '%14s' % txt

            if a.y_var == None:
                v_y = '%14.6f' % (a.coord[1])
            else:
                txt = a.y_var.name
                if a.y_sign == -1.0:
                    txt = '-' + txt
                v_y = '%14s' % txt

            if a.z_var == None:
                v_z = '%14.6f' % (a.coord[2])
            else:
                txt = a.z_var.name
                if a.z_sign == -1.0:
                    txt = '-' + txt
                v_z = '%14s' % txt

            txt = '%6s  %12s  %12s  %12s  ' % (
               a.name,v_x, v_y, v_z)
                #a.symbol,v_x, v_y, v_z)

        return txt

    def get_element_from_tag(self,atom_type):
        """ Utility to extract the element symbol
            This is a copy of the routine sat in basis/basismanager.py, but
            I am finding it pretty useful here too...
        """
        # try a few possibilities
        el = string.split(atom_type,'_')[0]
        trans = string.maketrans('a','a')
        el = string.translate(el,trans,string.digits)
        # Jens change to make function usable in Dalton interface
        if len( el ) == 2:
            a = string.upper(el[0])
            b = string.lower(el[1])
            el = a + b
        elif len( el ) == 1:
            el = string.upper(el[0])
        
        return el


    def atom_list_novar(self,a):
        """ This returns a list of either the coordinates or the zmatrix line
            for an individual atom. The first item in the list indicates whether
            the atom is in zmatrix or cartesian format. If the atom is Cartesian,
            4 addional fields are returned - the x,y, & z coordinates ( or variables )
            and the charge. If it is zmatrix format, then the zmatrix list is the zmatrix
            fields followed by the charge. All variables are converted to their numeric values.
        """

        atomlist = []
        n = a.get_index()

        # Hack for fragments
        if self.is_frag:
            n = 4

        if a.zorc == 'z':
            atomlist.append( 'z' ) # First item always indicates atom type

            # distance value
            if a.r_var == None:
                v_r = a.r
            else:
                # Could I just use a.r_var.value?
                name = a.r_var.name
                var = self.find_var( name )
                if ( a.r_sign == -1.0 ):
                    v_r = ( var.value * -1 )
                else:
                    v_r = var.value

            # Angle value
            if a.theta_var == None:
                v_theta = a.theta
            else:
                name = a.theta_var.name
                var = self.find_var( name )
                if ( a.theta_sign == -1.0 ):
                    v_theta = ( var.value * -1 )
                else:
                    v_theta = var.value

            # dihedral value
            if a.phi_var == None:
                v_phi = a.phi
            else:
                name = a.phi_var.name
                var = self.find_var( name )
                if ( a.phi_sign == -1.0 ):
                    v_phi = ( var.value * -1 )
                else:
                    v_phi = var.value

            i1 = -1
            i2 = -1
            i3 = -1

            # The x fields are used when holding fragments
            # for the editor (see zfragment.py)
            if a.i1:
                i1 = a.i1.get_index()
            else:
                try:
                    i1 = a.i1x
                except AttributeError:
                    pass

            if a.i2:
                i2 = a.i2.get_index()
            else:
                try:
                    i2 = a.i2x
                except AttributeError:
                    pass

            if a.i3:
                i3 = a.i3.get_index()
            else:
                try:
                    i3 = a.i3x
                except AttributeError:
                    pass

            if n == 0: # Origin atom of z-matrix
                atomlist.append( a.name )

            elif n == 1: # 2nd zmatrix atom
                atomlist.append( a.name )
                atomlist.append( i1+1 )
                atomlist.append( v_r )

            elif n == 2: # 3rd zmatrix atom
                atomlist.append( a.name )
                atomlist.append( i1+1 )
                atomlist.append( v_r )
                atomlist.append( i2+1 )
                atomlist.append( v_theta )

            else: # All reamining atoms
                atomlist.append( a.name )
                atomlist.append( i1+1 )
                atomlist.append( v_r )
                atomlist.append( i2+1 )
                atomlist.append( v_theta )
                atomlist.append( i3+1 )
                atomlist.append( v_phi )

            # Now just append the charge
            element = self.get_element_from_tag( a.name )
            charge = float ( atomic_number[ element ] )
            atomlist.append( charge )

        else: # This else clause for Cartesian atoms
            atomlist.append( 'c' )
            if a.x_var == None:
                v_x = a.coord[0]
            else:
                name = a.x_var.name
                var = self.find_var( name )
                if ( a.x_sign == -1.0 ):
                    v_x = ( var.value * -1 )
                else:
                    v_x = var.value

            if a.y_var == None:
                v_y = a.coord[1]
            else:
                name = a.y_var.name
                var = self.find_var( name )
                if ( a.y_sign == -1.0 ):
                    v_y = ( var.value * -1 )
                else:
                    v_y = var.value

            if a.z_var == None:
                v_z = a.coord[2]
            else:
                name = a.z_var.name
                var = self.find_var( name )
                if ( a.z_sign == -1.0 ):
                    v_z = ( var.value * -1 )
                else:
                    v_z = var.value

            atomlist.append( a.name )
            atomlist.append( v_x )
            atomlist.append( v_y )
            atomlist.append( v_z )
            
            # Now just append the charge
            element = self.get_element_from_tag( a.name )
            charge = float ( atomic_number[ element ] )
            atomlist.append( charge )

        return atomlist

    def _output_shell(self,a):
        """ shell output (no z-matrix support) and no control of shell
        optimisation, as this is assumed to follow the respective cores
        """

        v_x = '%14.6f' % (a.coord[0])
        v_y = '%14.6f' % (a.coord[1])
        v_z = '%14.6f' % (a.coord[2])
        txt = '%6s %12s %12s %12s  %12.5f %d' % (
        a.name,v_x, v_y, v_z,a.partial_charge,a.linked_core.get_index())

        return txt

    def output_coords_block(self,write_connect=1,write_dummies=1,exclude_cell=0):
        """Output structure in punchfile format
        (simple cartesian coordinate representation)
        """
        out = []
        out.append('block = fragment records = 0')
        out.append('block = title records = 1')
        out.append(self.title)

        self.reindex()

        if write_dummies:
            n = len(self.atom)
        else:
            n = self.get_nondum()

        out.append('block = coordinates records = ' + str(n))

        for a in self.atom:
            #t = string.lower(a.symbol)[:2]
            #if t[1:2] == string.upper(t[1:2]):
            #t = t[:1]
            fac = 1.0 / 0.529177
            if write_dummies or (a.seqno2 > -1):
                out.append(
                   a.name + ' ' + 
                   str(fac*a.coord[0]) + ' ' +
                   str(fac*a.coord[1]) + ' ' +
                   str(fac*a.coord[2]))

        if len(self.cell) and not exclude_cell:
            ncell = len(self.cell)
            out.append('block = cell_vectors records = ' + str(ncell))
            fac = 1.0 / 0.529177
            for a in self.cell:
                out.append(str(fac*a[0]) + ' ' +str(fac*a[1]) + ' '+ str(fac*a[2]))

        out.append('block = atom_charges records = ' + str(n))
        for a in self.atom:
            if write_dummies or (a.seqno2 > -1):
                out.append(str(a.partial_charge))

        if len(self.shell):
            n = len(self.shell)
            out.append('block = shells records = ' + str(n))
            fac = 1.0 / 0.529177
            for a in self.shell:
                out.append(
                    a.name + ' ' + 
                    str(fac*a.coord[0]) + ' ' +
                    str(fac*a.coord[1]) + ' ' +
                    str(fac*a.coord[2]) + ' ' +
                    str(a.partial_charge) + ' ' +
                    str(a.linked_core.get_index()) )

        #count valid connections
        if write_connect:
            if write_dummies:
                count = 0
                for a in self.atom:
                    for b in a.conn:
                        if a.get_index() > b.get_index():
                            count = count+1
                out.append('block = connectivity records = ' + str(count))
                for a in self.atom:
                    for b in a.conn:
                        if a.get_index() > b.get_index():
                            out.append(str(1+a.get_index()) + ' ' + str(1+b.get_index()))
            else:
                count = 0
                for a in self.atom:
                    if a.seqno2 > -1:
                        for b in a.conn:
                            if b.seqno2 > -1:
                                if a.get_index2() > b.get_index2():
                                    count = count+1

                out.append('block = connectivity records = ' + str(count))
                for a in self.atom:
                    if a.seqno2 > -1:
                        for b in a.conn:
                            if b.seqno2 > -1:
                                if a.get_index2() > b.get_index2():
                                    out.append(str(1+a.get_index2()) + ' ' + str(1+b.get_index2()))
        return out
    
    def is_connected(self,a1,a2):
        """Test if two atoms are connected"""
        try:
            idum = a1.conn.index(a2)
            return 1
        except ValueError:
            return 0

    def get_distance(self,a1,a2):
        return cpv.distance(a1.coord,a2.coord)
    
    def get_angle(self,a1,a2,a3):
        """Return the angle a1---a2---a3"""
        p1 = a1.coord
        p2 = a2.coord
        p3 = a3.coord

        r1 = cpv.distance(p1,p2)
        r2 = cpv.distance(p2,p3)
        r3 = cpv.distance(p1,p3)

        small = 1.0e-10
        cnv   = 57.29577951
        if r1 + r2 - r3 < small:
            # printf("trig error %f\n",r3-r1-r2)
            # This seems to happen occasionally for 180 angles 
            theta = 180.0
        else:
            theta = cnv*math.acos( (r1*r1 + r2*r2  - r3*r3) / (2.0 * r1*r2) )
        return theta;


    def get_dihedral(self,a1,a2,a3,a4):

        p1 = a1.coord
        p2 = a2.coord
        p3 = a3.coord
        p4 = a4.coord

        cnv=57.29577951

        vec_ij = cpv.sub(p1, p2)
        vec_kj = cpv.sub(p3, p2)
        vec_kl = cpv.sub(p3, p4)

        # vec1 is the normal to the plane defined by atoms i, j, and k    
        vec1 = cpv.cross_product(vec_ij,vec_kj)
        magvec1 = cpv.dot_product(vec1,vec1)

        #  vec2 is the normal to the plane defined by atoms j, k, and l
        vec2 = cpv.cross_product(vec_kl,vec_kj)
        magvec2 = cpv.dot_product(vec2,vec2)

        # the definition of a dot product is used to find the angle between  
        # vec1 and vec2 and hence the angle between the planes defined by    
        # atoms i, j, k and j, k, l                                          
        #                                                                    
        # the factor of pi (180.0) is present since when we defined the      
        # vectors vec1 and vec2, one used the right hand rule while the      
        # other used the left hand rule                                      

        dotprod = cpv.dot_product(vec1,vec2)
        #print magvec1, magvec2
        #print type(magvec1), type(magvec2)
        fac = dotprod / math.sqrt(magvec1*magvec2)
        if(fac > 1.0):
            fac = 1.0
        if(fac < -1.0):
            fac = -1.0
        dihed = 180.0 - cnv * math.acos(fac )

        # the dot product between the bond between atoms i and j and the     
        # normal to the plane defined by atoms j, k, and l is used to        
        # determine whether or not the dihedral angle is clockwise or        
        # anti_clockwise                                                     
        #                                                                    
        # if the dot product is positive, the rotation is clockwise          

        sign_check = cpv.dot_product(vec_ij,vec2)
        if( sign_check > 0.0):
            dihed = dihed * -1.0

        return dihed


    def bonds_and_angles(self,unit='angstrom',all=0):
        """ Returns a printable list of bond lengths, angles and torsions"""
        if unit == 'angstroms' or unit == 'angstrom' or unit == 'angs':
            scale = 1.0
        elif unit == 'pm':
            scale = 100
        elif unit == 'au' or unit == 'bohr':
            scale = 1.0 / 0.52917706
        else:
            print 'Unrecognised unit',unit
            return

        # Connectivity analysis
        # Assumes conn entries and index array are to date

        res = []
        res.append("Bonds (" + unit + ")")
        for a in self.atom:
            for b in a.conn:
                tester = all or( a.get_index() < b.get_index())
                if tester:
                    r = self.get_distance(a,b)*scale
                    s1 = "%5d-%d (%s-%s) " % (a.get_index()+1,  b.get_index()+1, a.name, b.name)
                    res.append("%15s %10.4f" % (s1, r) )
                #res.append("%5d - %5d (%4s - %4s) %10.4f" % (a.get_index()+1, b.get_index()+1, a.name, b.name, r) )                

        res.append("Bond Angles")
        for a in self.atom:
            for b in a.conn:
                for c in a.conn:
                    tester = all or (b.get_index() < c.get_index())
                    if c != b and tester:
                        ang = self.get_angle(b,a,c)
                        s1 = "%d-%d-%d" % (c.get_index()+1, a.get_index()+1, b.get_index()+1)
                        s2 = "(%s-%s-%s)" % (c.name,  a.name,  b.name)
                        res.append("%10s %10s   %10.4f " % (s1, s2, ang))

                        #res.append("%5d (%4s) %5d (%4s) %5d (%4s)  %10.4f" %
                        #(b.get_index()+1, b.name, a.get_index()+1, a.name, c.get_index()+1, c.name, ang))

        res.append("Proper Torsions")
        for a in self.atom:
            for b in a.conn:
                tester = all or( a.get_index() < b.get_index())
                if tester:
                    for c in a.conn:
                        if c != b:
                            for d in b.conn:
                                if d != a:
                                    dih = self.get_dihedral(c,a,b,d)
                                    s1 = "%d-%d-%d-%d" % (c.get_index()+1, a.get_index()+1, b.get_index()+1, d.get_index()+1)
                                    s2 = "(%s-%s-%s-%s)" % (c.name,  a.name,  b.name,  d.name)
                                    res.append("%10s %10s   %10.4f " % (s1, s2, dih))
                                    #res.append("%5d (%4s) %5d (%4s) %5d (%4s) %5d (%4s) %10.4f " % (c.get_index()+1, c.name,  a.get_index()+1, a.name, b.get_index()+1, b.name, d.get_index()+1, d.name, dih))
        res.append("Improper Torsions")
        res.append("Measured i,j-[k]-l for k bonded to i,j and l")
        for c in self.atom:
            for b in c.conn:
                for a in c.conn:
                    if a != b:
                        for d in c.conn:
                            if d != a and d != b:
                                dih = self.get_dihedral(a,b,c,d)
                                s1 = "%d,%d-[%d]-%d" % (a.get_index()+1, b.get_index()+1, c.get_index()+1, d.get_index()+1)
                                s2 = "(%s,%s-[%s]-%s)" % (a.name,  b.name,  c.name,  d.name)
                                res.append("%10s %10s   %10.4f " % (s1, s2, dih))
                                #res.append("%5d (%4s) %5d (%4s) %5d (%4s) %5d (%4s) %10.4f " % (c.get_index()+1, c.name,  a.get_index()+1, a.name, b.get_index()+1, b.name, d.get_index()+1, d.name, dih))

        return res

    def load_coordinate_variables(self):
        """copy values from coordinate variables (a.x_var) -> a.coord"""
        for a in self.atom:
            if a.x_var != None:
                a.coord[0] = a.x_sign * a.x_var.value
            if a.y_var != None:
                a.coord[1] = a.y_sign * a.y_var.value
            if a.z_var != None:
                a.coord[2] = a.z_sign * a.z_var.value

    def calculate_one_coordinate(self,i):
        """Compute cartesian coordinates for a single atom """
        global fp0, fp1, fp2
        if not fp0:
            # these are for generating coords for fragments (in isolation)
            # taken from methane oriented so that missing group
            # is in the +z direction
            fp0 = ZAtom()
            fp0.coord = orig
            fp1 = ZAtom()
            fp1.coord = [0.943,  0.00, -0.342]
            fp2 = ZAtom()
            fp2.coord = [-0.47, -0.81, -0.342]

        a = self.atom[i]
        ok = 1

        if self.debug:
            print 'calc coord for ',self.output_atom_full(a)

        # fill in name field
        # a.name = a.symbol + string.zfill(i,2)
        if a.zorc == 'z':
            i1 = a.i1
            i1i = -999
            if i1 and i1.ok:
                i1i=i1.get_index()
            else:
                try:
                    i1i = a.i1x
                    if i1i == -1:
                        i1 = fp0
                    elif i1i == -2:
                        i1 = fp1
                    elif i1i == -3:
                        i1 = fp2
                except AttributeError:
                    pass

            i2 = a.i2
            i2i = -999
            if i2 and i2.ok:
                i2i=i2.get_index()
            else:
                try:
                    i2i = a.i2x
                    if i2i == -1:
                        i2 = fp0
                    elif i2i == -2:
                        i2 = fp1
                    elif i2i == -3:
                        i2 = fp2
                except AttributeError:
                    pass

            i3 = a.i3
            i3i = -999
            if i3 and i3.ok:
                i3i=i3.get_index()
            else:
                try:
                    i3i = a.i3x
                    if i3i == -1:
                        i3 = fp0
                    elif i3i == -2:
                        i3 = fp1
                    elif i3i == -3:
                        i3 = fp2
                except AttributeError:
                    pass

            if i == 0 and not self.is_frag:
                p1 = [ 0.0, 0.0, 0.0]
                p2 = [ 0.0, 0.0, 1.0]
                p3 = [ 1.0, 1.0, 1.0]
                r = 0.0
                theta = 0.0
                phi = 0.0

            elif i == 1 and not self.is_frag:
                if i1i > 0:
                    self.logerr('bad i1 atom index for atom 2: %d' % (i1i+1))
                    ok = 0 
                    a.ok = 0

                if(ok):
                    #.....assumption that i1 is set is not generally safe
                    p1 = i1.coord
                    p2 = cpv.add(i1.coord,zvec)
                    # arbritary vector 
                    p3 = cpv.add(i1.coord,xvec)

                    if a.r_var == None:
                        r = a.r
                    else:
                        r = a.r_sign * a.r_var.value
                    theta =  0.0
                    phi = 0.0

            elif i == 2 and not self.is_frag:

                if i1i == 0 and i2i == 1:
                    pass
                elif i1i == 1 and i2i == 0:
                    pass
                else:
                    if i1i > 1 or i1i == -999 or i2i > 1 or i2i == -999:
                        self.logerr('bad atom indices for atom 3: %d %d' % (i1i+1,i2i+1))
                        ok = 0
                        a.ok = 0

                if(ok):
                    p1 = i1.coord
                    p2 = i2.coord
                    p3 = cpv.add(i1.coord,xvec)
                    if a.r_var == None:
                        r = a.r
                    else:
                        r = a.r_sign * a.r_var.value
                    if a.theta_var == None:
                        theta = a.theta 
                    else:
                        theta = a.theta_sign * a.theta_var.value
                    phi = 0.0

            else:

                if i1i != -999 and i2i != -999 and i3i != -999 and \
                   i1i < i and i2i < i and i3i < i and \
                   i1i != i2i and i2i != i3i and i1i != i3i:

                    p1 = i1.coord
                    p2 = i2.coord
                    p3 = i3.coord
                    if a.r_var == None:
                        r = a.r
                    else:
                        r = a.r_sign * a.r_var.value
                    if a.theta_var == None:
                        theta = a.theta 
                    else:
                        theta = a.theta_sign * a.theta_var.value
                    if a.phi_var == None:
                        phi = a.phi 
                    else:
                        phi = a.phi_sign * a.phi_var.value

                else:
                    print 'bad atom indices for atom %d: %d %d %d' % (i+1,i1i+1,i2i+1,i3i+1)
                    self.logerr('bad atom indices for atom %d: %d %d %d' % (i+1,i1i+1,i2i+1,i3i+1))
                    ok = 0
                    a.ok = 0


            # Check for numerical problems with the dihedral
            if i > 2:
                if theta < SMALL:
                    print 'Small theta, torsion undefined'
                elif cpv.get_angle_formed_by(p3,p2,p1) < SMALL:
                    print 'WARNING: Small jkl angle, torsion undefined'
                elif abs(math.pi - cpv.get_angle_formed_by(p3,p2,p1)) < SMALL:
                    print 'WARNING: 180 jkl angle, torsion undefined'

            if(ok):
                # add exception handling here later
                if self.debug > 1:
                    print 'ziccd arg types',type(r),type(phi),type(dtorad),type(theta)

                a.coord = self.__ziccd(p3,p2,p1,r,theta*dtorad,phi*dtorad)

                if self.debug > 1:
                    print '================',r,theta,phi
                    print p3
                    print p2
                    print p1
                if self.debug:
                    print 'new coords for atom',i,
                    for coor in a.coord:
                        print "%10.5f" % (coor,),
                    print
                a.ok = 1
            else:
                print 'skip calc for',i+1
                a.ok = 0

        return not ok

    def calculate_coordinates(self):
        """Compute cartesian coordinates for all atoms"""

        self.errors = []
        self.reindex()
        self.load_coordinate_variables()

        # Loop over atoms computing cartesians
        ok = 1
        for i in range(len(self.atom)):
            ok = ok and not self.calculate_one_coordinate(i)

        if self.debug:
            if len(self.errors):
                print 'calculate_coordinates done, errors:',errors
            else:
                print 'calculate_coordinates done with no errors'
            if not ok:
                print 'problems with atoms:',
                for a in self.atom:
                    if not a.ok: print a.get_index()
                print

    def __ziccd(self,a,b,c,r,theta,phi):
        """compute coordinates of atom x from a,b,c
        r = r(c--x),
        theta = ang(x--c--b),
        phi = tor(x--c--b--a)
        """

        assert type(a) == type([]), 'bad type for a'+type(a)
        assert type(b) == type([]), 'bad type for b'+type(b)
        assert type(c) == type([]), 'bad type for c'+type(c)

        assert type(a[0]) == type(0.0), 'bad type for a[0]'+type(a[0])
        assert type(b[0]) == type(0.0), 'bad type for b[0]'+type(b[0])
        assert type(c[0]) == type(0.0), 'bad type for c[0]'+type(c[0])

        assert type(r) == type(0.0), 'bad type for r'+type(r)
        assert type(theta) == type(0.0), 'bad type for theta'+type(theta)
        assert type(phi) == type(0.0), 'bad type for phi'+type(phi)

        PI=3.14159265358979323846

        #compute normalised  bc vector, and two perpendicul
        #vectors, v1 (in the same plane as ab and bc) and

        vbc = cpv.normalize(cpv.sub(c,b))
        v1 = cpv.normalize(cpv.cross_product(vbc,cpv.sub(a,b)))
        v2 = cpv.cross_product(v1,vbc)

        # construct torsion angle vector 

        v3 = cpv.add(cpv.scale(v1,math.sin(phi)),cpv.scale(v2,math.cos(phi)))

        # take required combination of vbc and v3 

        # print 'trig types', type(math.cos(PI-theta)), type(math.sin(PI-theta))
        return cpv.add(c,cpv.add(cpv.scale(vbc,r*math.cos(PI-theta)),
               cpv.scale(v3,r*math.sin(PI-theta))))

    def __printinternals(self):
        print type(self), type(self.atom[0])
        for i in range(len(self.atom)):
            a = self.atom[i]
            i1i = 0
            if a.i1:
                i1i=a.i1.get_index()+1
            i2i = 0
            if a.i2:
                i2i=a.i2.get_index()+1
            i3i = 0
            if a.i3:
                i3i=a.i3.get_index()+1
            print a.name, i1i, a.r, i2i+1, a.theta, i3i+1, a.phi

    def counts(self):
        """Returns number of x atoms, z atoms, variables and constants"""
        z=0;x=0;c=0;v=0
        for a in self.atom:
            if a.zorc == 'z':
                z = z + 1
            else:
                x = x + 1

        for a in self.variables:
            if a.constant:
                c = c + 1
            else:
                v = v + 1
        return (x,z,v,c)

    #
    # some simple editing operations
    # used by tkmolview
    #

    def connect_old(self,scale=1.0,toler=0.5):
        """Old (brain-dead) connectivity routine"""
        model.bond = []
        model.reindex()

        for atomi in model.atom:
            atomi.rad = 0.529177*rcov[atomi.get_number()]
            #print atomi.get_number(), atomi.rad

        count=0
        for i in range(len(model.atom)):
            atomi = model.atom[i]
            #atomi.conn = []
            if not i % 10:
                print '....' + str(i)
            for j in range(i):
                atomj = model.atom[j]
                dist0 = scale*(atomi.rad+atomj.rad) + toler
                dist = cpv.distance(atomi.coord,atomj.coord)
                if dist <= dist0:
                    print i,j,dist,dist0
                    count = count + 1
                    # Add in 'Indexed' form
                    b = Bond()
                    b.index=[atomi.get_index(), atomj.get_index()]
                    model.bond.append(b)
                    # Add to conn array
                    #atomi.conn.append[atomj]
                    #atomj.conn.append[atomi]

        print 'connect: found ',count,' bonds'

    def connect(self,scale=1.0,toler=0.5):
        """ Compute connectivity
        Taken from John Kendricks Tcl routine
        Connectivity is stored in the bond array
        """

        self.bond = []
        self.reindex()
        count=0
        #
        #  Allocate the atoms in the molecule mol to boxes ready for calculation of bonds
        #
        Box1 = {}
        Box3 = {}
        boxSize=2

        print 'Pass 0'
        rmax = 0.0
        for i in range(len(self.atom)):
            atomi = self.atom[i]
            #print atomi.symbol, atomi.get_number()
            atomi.rad = 0.529177*rcov[atomi.get_number()]
            if atomi.rad > rmax:
                rmax = atomi.rad

        boxSize=2*rmax*scale+toler+0.1

        print 'Pass 0','box size=',boxSize

        for i in range(len(self.atom)):
            atomi = self.atom[i]
            # Calculate a box label holding the atom assuming boxes are boxSize Angs cubes
            a=int( math.floor( atomi.coord[0] / boxSize ) )
            b=int( math.floor( atomi.coord[1] / boxSize ) ) 
            c=int( math.floor( atomi.coord[2] / boxSize ) )
            key = (a,b,c)
            atomi.cell = key
            try:
                Box1[key].append(i)
            except KeyError:
                Box1[key] = [i]

        for key in Box1.keys():
            Box3[key] = self._permBox(key)

        print 'Pass 2'
        for i in range(len(self.atom)):
            if not i % 50:
                print '....' + str(i),
            atomi = self.atom[i]
            for tuple in Box3[atomi.cell]:
                try:
                    for j in Box1[tuple]:
                        if j < i:
                            atomj = self.atom[j]
                            dist0 = scale*(atomi.rad+atomj.rad) + toler
                            dist = cpv.distance(atomi.coord,atomj.coord)
                            #print dist, dist0
                            if dist <= dist0:
                                count = count + 1
                                b = Bond()
                                b.index=[atomi.get_index(), atomj.get_index()]
                                self.bond.append(b)
                except KeyError:
                    pass

        print 'connect: found ',count,' bonds'
        self.update_conn()

    def find_contacts(self,contact_scale=1.0,contact_toler=2.5,pr=0,list=None):

        """Search for nonbonded contacts
        Taken from John Kendricks Tcl routine
        """
        self.contacts = []
        self.reindex()
        count=0
        #
        #  Allocate the atoms in the molecule mol to boxes ready for calculation of bonds
        #
        #PS should be based on vdw radii, not covalent
        #   also should exclude bonds and perhaps 1,3

        Box1 = {}
        Box3 = {}

        print 'Pass 0'
        rmax = 0.0
        for i in range(len(self.atom)):
            atomi = self.atom[i]
            atomi.rad = 0.529177*rcov[atomi.get_number()]
            if atomi.rad > rmax:
                rmax = atomi.rad

        boxSize=2*rmax*contact_scale+contact_toler+0.1
        print 'Pass 1'

        for i in range(len(self.atom)):
            atomi = self.atom[i]
            # Calculate a box label holding the atom assuming boxes are boxSize Angs cubes
            a=int( math.floor( atomi.coord[0] / boxSize ) )
            b=int( math.floor( atomi.coord[1] / boxSize ) ) 
            c=int( math.floor( atomi.coord[2] / boxSize ) )
            key = (a,b,c)
            atomi.cell = key
            try:
                Box1[key].append(i)
            except KeyError:
                Box1[key] = [i]

        for key in Box1.keys():
            Box3[key] = self._permBox(key)

        if list is None:
            list = range(len(self.atom))

        newlist = []
        for i in list:
            newlist.append(i+1)
        print 'Pass 2', newlist

        exclusions = {}
        for a in self.atom:
            ia = a.get_index()
            exclusions[ia] = []
            for b in a.conn:
                exclusions[ia].append(b.get_index())
                for c in b.conn:
                    if a != c:
                        exclusions[ia].append(c.get_index())
                        for d in c.conn:
                            if d != b and d != a:
                                if not d.get_index() in exclusions[ia]:
                                    exclusions[ia].append(d.get_index())
            if self.debug:
                print 'Ex',ia,': ',exclusions[ia]

        for i in list:
            if not pr:
                if not i % 50:
                    print '....' + str(i),
            atomi = self.atom[i]
            for tuple in Box3[atomi.cell]:
                try:
                    for j in Box1[tuple]:
                        if i != j:
                            atomj = self.atom[j]
                            dist1 = contact_scale*(atomi.rad+atomj.rad) + contact_toler
                            dist = cpv.distance(atomi.coord,atomj.coord)
                            if dist <= dist1:
                                if not j in exclusions[i]:
                                    if pr:
                                        print i+1,self.atom[i].name,j+1,self.atom[j].name,dist
                                    count = count + 1
                                    b = Bond()
                                    b.index=[atomi.get_index(), atomj.get_index()]
                                    self.contacts.append(b)
                except KeyError:
                    pass

        if not pr:
            print ''

        print 'connect: found ',count,' contacts'

    def _permBox(self,ix):
        a,b,c = ix
        l = []
        for  i in [ 0, -1, +1 ]:
            for j in [ 0, -1, +1 ]:
                for k in [ 0, -1, +1 ]:
                    l.append((a+i, b+j, c+k))
        return l

    def apply_connect(self,new_bond):
        """apply a new bond table"""
        print 'applying new_bond',new_bond,len(new_bond)
        for b in new_bond:
            print b.index
        self.bond = new_bond
        self.list()

    def apply_atom_list(self,new_atom):
        """apply a new bond table"""
        print 'applying new_atom',new_atom,len(new_atom)
        self.atom = new_atom
        self.list()

    def extend(self,minx,maxx,miny,maxy,minz,maxz):

        try:
            prim = self.primitive_atom
            shellprim = self.primitive_shell
        except AttributeError:
            self.primitive_atom = self.atom
            prim = self.atom
            self.primitive_shell = self.shell
            shellprim = self.shell
        ##vx = Vector(self.cell[0])
        vx = self.cell[0]
        ##vy = Vector(self.cell[1])
        vy = self.cell[1]

        if  len(self.cell) == 3:
            ###vz = Vector(self.cell[2])
            vz = self.cell[2]
        else:
            vz = Vector(0., 0., 0.)
            minz=0
            maxz=0

        self.atom = []
        self.shell = []        
        offset=0
        nat = len(prim)
        for ix in range(minx,maxx+1):
            tranx = vx * ix
            for iy in range(miny,maxy+1):
                trany = vy * iy
                for iz in range(minz,maxz+1):
                    tranz = vz * iz

                    for atom in prim:
                        #old_conn = atom.conn
                        atom.conn = []
                        new = copy.deepcopy(atom)
                        self.atom.append(new)
                        pos = Vector(atom.coord) + tranx + trany + tranz
                        new.coord[0] = pos[0]
                        new.coord[1] = pos[1]
                        new.coord[2] = pos[2]

                    for atom in shellprim:
                        ixx = atom.linked_core.get_index()
                        atom.conn = []
                        # no need to copy the referenced atom
                        t= atom.linked_core
                        atom.linked_core=None
                        new = copy.deepcopy(atom)
                        atom.linked_core=t
                        self.shell.append(new)
                        pos = Vector(atom.coord) + tranx + trany + tranz
                        new.coord[0] = pos[0]
                        new.coord[1] = pos[1]
                        new.coord[2] = pos[2]
                        # link to parent atom
                        new.linked_core = self.atom[ixx+offset]

                    offset=offset+nat
                        

        print 'extend: generated ',len(self.atom),' atoms'
        if len(self.shell):
            print 'and ',len(self.shell),' shells'

    def hybridise(self,atom,hybridisation):
        """ Try and impose a given hybridisation on an atomic centre
        Add x atoms to make up the required number of connections
        """

        self.reindex()
        if self.debug:
            print 'HYBRIDISE',atom.get_index()
        self.list()

        for a in self.atom:
            print a.get_index(),len(a.conn),
            if a == atom:
                print 'X'
            else:
                print ''

        # Delete any unattached X atoms already present
        # This should move to a local delete function
        #for a in self.atom:
        #    a.conn = []
        #for b in self.bond:
        #    self.atom[b.index[0]].conn.append(self.atom[b.index[1]])
        #    self.atom[b.index[1]].conn.append(self.atom[b.index[0]])
        #self.reindex()

        print 'After rebuilding atom.conn'
        self.list()

        self.recycle = []
        for a in atom.conn:
            print a, a.get_number()
            if a.get_number() == 0 and len(a.conn) == 1:
                print 'del list'
                self.recycle.append(a)

        print 'list of Xs to be recycled',self.recycle
        ###self.delete_list(dels)

        # disconnect the recycle list
        for a in self.recycle:
            try:
                atom.conn.remove(a)
            except ValueError:
                print 'Internal error.. unexpected connectivity for atom-X'
            try:
                a.conn.remove(atom)
            except ValueError:
                print 'Internal error.. unexpected connectivity for X-atom'

        self.reindex()
        print 'After processing recycle'
        self.list()

        for a in self.atom:
            print a.get_index(),len(a.conn),
            if a == atom:
                print 'X'
            else:
                print ''

        print 'len of conn',len(atom.conn)
        print 'conn',atom.conn

        self.irecyc = 0

        if hybridisation == 'sp3':

            oldi3 = None
            if len(atom.conn) == 0:
                a1 = self._next_x()
                a1.name = 'x1'
                a1.r = 1.0
                a1.theta = 0.0
                a1.phi = 0.0
                a1.i1 = atom
                a1.i2 = None
                a1.i3 = None
                p1 = a1.i1.coord
                p2 = [0.0, 0.0, 1.0]
                p3 = [1.0, 0.0, 0.0]
                a1.coord = self.__ziccd(p3,p2,p1,a1.r,a1.theta*dtorad,a1.phi*dtorad)
                self.add_conn(atom,a1)

            if len(atom.conn) == 1:
                a2 = self._next_x()
                a2.name = 'x2'
                a2.r = 1.0
                a2.theta = 109.4
                a2.phi = 0.0
                a2.i1 = atom
                a2.i2 = atom.conn[0]
                p1 = a2.i1.coord
                p2 = a2.i2.coord
                a2.i3 = self._find_i3(a2, atom, a2.i2)
                if a2.i3 == None:
                    p3 = [ 1.0, 0.0, 0.0]
                else:
                    p3 = a2.i3.coord
                    oldi3 = a2.i3
                a2.coord = self.__ziccd(p3,p2,p1,a2.r,a2.theta*dtorad,a2.phi*dtorad)
                self.add_conn(atom,a2)
                
            if len(atom.conn) == 2:
                a3 = self._next_x()
                a3.name = 'x3'
                a3.r = 1.0
                a3.theta = 109.4
                a3.phi = 120.0
                a3.i1 = atom
                a3.i2 = atom.conn[0]
                if oldi3:
                    a3.i3 = oldi3
                else:
                    a3.i3 = self._find_i3(a3, atom, a3.i2)
                    oldi3 = a3.i3
                    if a3.i3 == None:
                        a3.i3 = atom.conn[1]
                p1 = a3.i1.coord
                p2 = a3.i2.coord
                p3 = a3.i3.coord
                a3.coord = self.__ziccd(p3,p2,p1,a3.r,a3.theta*dtorad,a3.phi*dtorad)
                self.add_conn(atom,a3)

            if len(atom.conn) == 3:
                a4 = self._next_x()
                a4.name = 'x4'
                a4.r = 1.0
                a4.theta = 109.4
                a4.phi = 240.0
                a4.i1 = atom
                a4.i2 = atom.conn[0]
                if oldi3:
                    a4.i3 = oldi3
                else:
                    a4.i3 = self._find_i3(a4, atom, a4.i2)
                    if a4.i3 == None:
                        a4.i3 = atom.conn[1]
                p1 = a4.i1.coord
                p2 = a4.i2.coord
                p3 = a4.i3.coord
                a4.coord = self.__ziccd(p3,p2,p1,a4.r,a4.theta*dtorad,a4.phi*dtorad)
                self.add_conn(atom,a4)

        elif hybridisation == 'sp2' or hybridisation == 'tpy' or hybridisation == 'tbpy':

            oldi3 = None
            if len(atom.conn) == 0:
                a1 = self._next_x()
                a1.name = 'x1'
                a1.r = 1.0
                a1.theta = 0.0
                a1.phi = 0.0
                a1.i1 = atom
                a1.i2 = None
                a1.i3 = None
                p1 = a1.i1.coord
                p2 = [ 0.0, 0.0, 1.0]
                p3 = [ 1.0, 1.0, 1.0]
                a1.coord = self.__ziccd(p3,p2,p1,a1.r,a1.theta*dtorad,a1.phi*dtorad)
                self.add_conn(atom,a1)

            if len(atom.conn) == 1:
                a2 = self._next_x()
                a2.name = 'x2'
                a2.r = 1.0
                a2.theta = 120.0
                a2.phi = 0.0
                a2.i1 = atom
                # only one candidate for i2
                a2.i2 = atom.conn[0]
                p1 = a2.i1.coord
                p2 = a2.i2.coord
                a2.i3 = self._find_i3(a2, atom, a2.i2)
                if a2.i3 == None:
                    p3 = [ 1.0, 0.0, 0.0]
                else:
                    p3 = a2.i3.coord
                    oldi3 = a2.i3
                a2.coord = self.__ziccd(p3,p2,p1,a2.r,a2.theta*dtorad,a2.phi*dtorad)
                self.add_conn(atom,a2)
                
            if len(atom.conn) == 2:
                a3 = self._next_x()
                a3.name = 'x3'
                a3.r = 1.0
                a3.theta = 120.0
                a3.phi = 180.0
                a3.i1 = atom
                # should pick i2 as a real atom - this will probably
                # happen anyway as conn is built up by appending Xs
                a3.i2 = atom.conn[0]
                if oldi3:
                    # if we choose the same i3 as in the previous case
                    # we can use an angle of 180
                    a3.i3 = oldi3
                else:
                    # pick the atom we just added
                    # (an improper torsion, also 180)
                    a3.i3 = atom.conn[1]
                p1 = a3.i1.coord
                p2 = a3.i2.coord
                p3 = a3.i3.coord
                a3.coord = self.__ziccd(p3,p2,p1,a3.r,a3.theta*dtorad,a3.phi*dtorad)
                self.add_conn(atom,a3)

            if len(atom.conn) == 3 and hybridisation != 'sp2':
                a4 = self._next_x()
                a4.name = 'x4'
                a4.r = 1.0
                a4.theta = 90.0
                a4.phi = 80.0
                a4.i1 = atom
                a4.i2 = atom.conn[0]
                a4.i3 = atom.conn[1]
                p1 = a4.i1.coord
                p2 = a4.i2.coord
                p3 = a4.i3.coord
                a4.coord = self.__ziccd(p3,p2,p1,a4.r,a4.theta*dtorad,a4.phi*dtorad)
                self.add_conn(atom,a4)

            if len(atom.conn) == 4 and hybridisation == 'tbpy':
                a5 = self._next_x()
                a5.name = 'x5'
                a5.r = 1.0
                a5.theta = 90.0
                a5.phi = 270.0
                a5.i1 = atom
                a5.i2 = atom.conn[0]
                a5.i3 = atom.conn[1]
                p1 = a5.i1.coord
                p2 = a5.i2.coord
                p3 = a5.i3.coord
                a5.coord = self.__ziccd(p3,p2,p1,a5.r,a5.theta*dtorad,a5.phi*dtorad)
                self.add_conn(atom,a5)

        elif hybridisation == 'oct' or hybridisation == 'sqpy' or \
                 hybridisation == 'sqpl' or hybridisation == 'sp':

            oldi3 = None
            if len(atom.conn) == 0:
                a1 = self._next_x()
                a1.name = 'x1'
                a1.r = 1.0
                a1.theta = 0.0
                a1.phi = 0.0
                a1.i1 = atom
                a1.i2 = None
                a1.i3 = None
                p1 = a1.i1.coord
                p2 = [ 0.0, 0.0, 1.0]
                p3 = [ 1.0, 1.0, 1.0]
                a1.coord = self.__ziccd(p3,p2,p1,a1.r,a1.theta*dtorad,a1.phi*dtorad)
                self.add_conn(atom,a1)

            if len(atom.conn) == 1:
                a2 = self._next_x()
                a2.name = 'x2'
                a2.r = 1.0
                a2.theta = 90.0
                a2.phi = 0.0
                a2.i1 = atom
                a2.i2 = atom.conn[0]
                p1 = a2.i1.coord
                p2 = a2.i2.coord
                a2.i3 = self._find_i3(a2,atom,a2.i2)
                if a2.i3 == None:
                    p3 = [ 1.0, 0.0, 0.0]
                else:
                    p3 = a2.i3.coord
                    oldi3 = a2.i3
                a2.coord = self.__ziccd(p3,p2,p1,a2.r,a2.theta*dtorad,a2.phi*dtorad)
                self.add_conn(atom,a2)
                
            if len(atom.conn) == 2:
                # Two cases here
                # preceding code will create give two bonds at 90,
                # but previous editing could bring in two trans atoms

                a3 = self._next_x()
                a3.name = 'x3'
                a3.i1 = atom

                tester = abs(90-self.get_angle(atom.conn[0],atom,atom.conn[1]))
                if tester < 45:
                    # add an atom trans to a1
                    a3.i2 = atom.conn[1]
                    a3.i3 = atom.conn[0]
                    a3.r = 1.0
                    a3.theta = 90.0
                    a3.phi = 180.0
                else:
                    # position here is possibly indeterminate
                    # sometimes positioning the new atom above the existing
                    # ones might work (this recreates the pattern obtained by
                    # building the sp group at the start)
                    a3.i2 = atom.conn[1]
                    a3.r = 1.0
                    a3.theta = 90.0
                    a3.phi = 180.0
                    a3.i3 = self._find_i3(a3,atom,a3.i2)

                p1 = a3.i1.coord
                p2 = a3.i2.coord
                if a3.i3 == None:
                    p3 = [ 1.0, 0.0, 0.0]
                else:
                    p3 = a3.i3.coord                        
                a3.coord = self.__ziccd(p3,p2,p1,a3.r,a3.theta*dtorad,a3.phi*dtorad)
                self.add_conn(atom,a3)

            if len(atom.conn) == 3 and hybridisation != 'sp':
                a4 = self._next_x()
                a4.name = 'x4'
                a4.r = 1.0
                a4.theta = 90.0
                a4.phi = 180.0
                a4.i1 = atom
                a4.i2 = atom.conn[0]
                a4.i3 = atom.conn[1]
                p1 = a4.i1.coord
                p2 = a4.i2.coord
                p3 = a4.i3.coord
                a4.coord = self.__ziccd(p3,p2,p1,a4.r,a4.theta*dtorad,a4.phi*dtorad)
                self.add_conn(atom,a4)

            if len(atom.conn) == 4 and (hybridisation != 'sqpl' and hybridisation != 'sp'):
                a5 = self._next_x()
                a5.name = 'x5'
                a5.r = 1.0
                a5.theta = 90.0
                a5.phi = 90.0
                a5.i1 = atom
                a5.i2 = atom.conn[0]
                a5.i3 = atom.conn[1]
                p1 = a5.i1.coord
                p2 = a5.i2.coord
                p3 = a5.i3.coord
                a5.coord = self.__ziccd(p3,p2,p1,a5.r,a5.theta*dtorad,a5.phi*dtorad)
                self.add_conn(atom,a5)

            if len(atom.conn) == 5 and hybridisation == 'oct':
                a6 = self._next_x()
                a6.name = 'x6'
                a6.r = 1.0
                a6.theta = 90.0
                a6.phi = 270.0
                a6.i1 = atom
                a6.i2 = atom.conn[0]
                a6.i3 = atom.conn[1]
                p1 = a6.i1.coord
                p2 = a6.i2.coord
                p3 = a6.i3.coord
                a6.coord = self.__ziccd(p3,p2,p1,a6.r,a6.theta*dtorad,a6.phi*dtorad)
                self.add_conn(atom,a6)
        else:
            return (-1,'Cannot hybridise '+hybridisation+' yet')

        self.update_bonds()
        self.list()

        # finally delete Xs that we dont need
        dels = []
        for a in self.recycle[self.irecyc:]:
            dels.append(a.get_index())
        self.delete_list(dels)

        return (0,'')

    def _next_x(self,ix=None):
        if self.irecyc < len(self.recycle):
            a1 = self.recycle[self.irecyc]
            self.irecyc = self.irecyc + 1
        else:
            a1 = ZAtom()
            if ix is None:
                ix = len(self.atom)
            self.insert_atom(ix,a1)
            self.reindex()
        a1.symbol = 'X'
        return a1

    def _find_i1(self,target):
        """Choose an atom to define a distance to """
        i1 = None
        if self.debug:
            print 'Find i1 conn=',target.conn
        best = None
        for test in target.conn:
            if test.get_index() > target.get_index():
                pass
            else:
                # seek an atom, we may need a second connection for i2
                if test.get_index() == 1 or len(test.conn) > 1:
                    if self._find_i2(target,test):
                        best = test
        return best
    
    def _find_i2(self,target,i1atom,check=ORDER_CHECK,check_i3=1,testang=85):

        """Choose an atom to define a angle from
        if checking = ORDER_CHECK, only atoms which are above the target in the
        atom list are valid candidates
        if checking == OK_CHECK, use the ok attribute
        if checking == NO_CHECK, all candidates will be possible (check_i3 should be 0)

        if an i3 search is performed, both proper and improper possibilities are considered

        """
        i2 = None
        bestang = testang
        if self.debug:
            print '_find_i2', 'target = ', target.get_index(),' and i1 = ', i1atom.get_index()
        for test in i1atom.conn:
            if self.debug:
                print 'checking',test.get_index(),
            if test == target:
                if self.debug:
                    print 'is target'
            elif (check == ORDER_CHECK) and (test.get_index() > target.get_index() ):
                if self.debug:
                    print 'out of order'
            elif (check == OK_CHECK) and (not test.ok ) :
                if self.debug:
                    print 'atom marked as undefined'
            else:
                print 'looking for valid i3'
                if (check_i3 == 0) or self._find_i3(target,i1atom,test,check=check,testang=testang) \
                       or self._find_i3(target,i1atom,test,check=check,improper=1,testang=testang):
                    ang = self.get_angle(test,i1atom,target)
                    tester = abs(ang - 90)
                    if self.debug:
                        print 'ok, i2 candidate tester=',tester,
                    if tester < bestang:
                        bestang = tester
                        i2 = test
                        if self.debug:
                            print ' - retain',i2.get_index()
                    else:
                        if self.debug:
                            print ' - reject'
                else:
                    if self.debug:
                        print 'no possible i3'

        return i2

    def _find_i3(self,target,i1atom,i2atom,check=ORDER_CHECK,improper=0,testang=85):
        """Choose an atom to define a dihedral from
        search is conducted by looking at connections to i2 ie proper dihedrals
        """
        i3 = None
        bestang = testang

        print 'i3 CHECK is',check

        if self.debug:
            print '   _find_i3',target.get_index(),'i1',i1atom.get_index(),'i2',i2atom.get_index(),
            if improper:
                ', proper'
            else:
                ', improper'                
        if improper:
            list = i1atom.conn
        else:
            list = i2atom.conn

        for test in list:
            if self.debug:
                print '     checking',test.get_index(),
            if (check == ORDER_CHECK) and (test.get_index() > target.get_index()):
                if self.debug:
                    print 'out of order'
            elif (check == OK_CHECK) and (not test.ok ) :
                if self.debug:
                    print 'atom marked as undefined'
            elif test == i1atom:
                if self.debug:
                    print '== i1 atom'
            elif test == i2atom:
                if self.debug:
                    print '== i2 atom'
            else:
                if improper:
                    ang = self.get_angle(test,i1atom,i2atom)
                else:
                    ang = self.get_angle(test,i2atom,i1atom)                    
                tester = abs(ang - 90)
                if self.debug:
                    print '      i3 candidate tester=',tester
                if tester < bestang:
                    bestang = tester
                    i3 = test
                    if self.debug:
                        print '     i3 candidate selected'
                else:
                    if self.debug:
                        print '      poor angle'

        return i3


    def convert_to_z(self,atom):
        """Try and work out an internal coordinate definition for an atom"""

        print 'Convert to Z',atom.get_index()
        atom.zorc = 'z'

        if atom.get_index() > 0:
            if not atom.i1:
                atom.i1 = self._find_i1(atom)
                if not atom.i1:
                    print 'Problem defining i1'
                    return -1
            atom.r = self.get_distance(atom,atom.i1)

        if atom.get_index() > 1:
            if not atom.i2:
                atom.i2 = self._find_i2(atom, atom.i1)
                if not atom.i2:
                    print 'Problem defining i2'
                    return -1
            atom.theta = self.get_angle(atom,atom.i1,atom.i2)

        if atom.get_index() > 2:
            if not atom.i3:
                atom.i3 = self._find_i3(atom, atom.i1, atom.i2)
                if not atom.i3:
                    print 'Problem defining i3'
                    return -1
            atom.phi = self.get_dihedral(atom,atom.i1,atom.i2,atom.i3)

        return 0
    
    def add_fragment(self,atom,fragment):
        """Add a fragment from the library to the molecule,
        guessing the required internal coordinates (they
        can be edited with the z-matrix editor
        """

        self.reindex()

        if self.debug_frag:
            print 'Fragment',atom.get_index(), fragment
            print 'replacing', atom.get_index()+1

        # establish the geometrical parameters for the coupling
        # dependent on local geometry
        # first atom is going to be a direct replacement

        # bond length change can be added later
        r_tmp = atom.r
        theta_tmp = atom.theta
        phi_tmp = atom.phi

        coord_tmp = copy.deepcopy(atom.coord)
        zorc_tmp = atom.zorc

        # i1,i2,i3 set  may be incomplete because the
        # atom is at the start, or because z-matrix defs havent
        # been set up yet
        # note that for atoms added as part of editor
        # zorc is c but there are definitions as well which we could use
        # so should test i1,i2,i3 individually

        iref = {}

        i1_tmp = atom.i1
        i2_tmp = atom.i2
        i3_tmp = atom.i3

        if self.debug:
            print 'Adding fragment',fragment, 'to atom',atom.get_index()
            self.zlist()

        print 'Connections',atom.conn
        if not i1_tmp:
            i1_tmp = atom.conn[0]

            print 'first atom i1=',i1_tmp

        print 'I2 LOOP'
        if not i2_tmp:
            i2_tmp = self._find_i2(atom,i1_tmp,check=NO_CHECK,check_i3=0)

            print 'first atom i2=',i2_tmp

        print 'I3 LOOP'
        if not i3_tmp:
            i3_tmp = self._find_i3(atom,i1_tmp,i2_tmp,check=NO_CHECK)

            print 'first atom i3=',i2_tmp


        iref[-1] = i1_tmp
        iref[-2] = i2_tmp
        ##### shouldnt need this one for most fragment definitions
        #####iref[-3] = atom.i3

##        print 'its reference atoms',
##        if atom.i1:
##            print atom.i1.get_index()+1,
##        else:
##            print ' - ',
##        if atom.i2:
##            print ', ',atom.i2.get_index()+1,
##        else:
##            print ', - ',
##        if atom.i3:
##            print ', ',atom.i3.get_index()+1
##        else:
##            print ', - '

        # distance depends on atom type of connection
        # theta,phi  depends on hybridisation, easy if we point 
        # the atom along the vector of the replaced atom

        # replace the target atom
        f = fragment_lib[fragment].copy()

        f.calculate_coordinates()
        f.connect()
        f.update_conn()

        print 'chosen frag is ',f.title
        f.list()

        # Check if the atom is a terminus - if it is, and it is of type x, we
        # change the bond length.
        if len(atom.conn) == 1 and atom.symbol[0].lower() == 'x':
            root = atom.conn[0]
            # Use the symbol of the atom this one is connected to as we
            # will be replacing this one
            new_length = get_bond_length( root.symbol, f.atom[0].symbol )
            # For zmatrix, can just change r, otherwise need to calculate the
            # coordinates
            if atom.zorc == 'z':
                tmp_r = new_length
            else:
                diff = self.get_bond_coord_diff( atom, root, new_length )
                coord_tmp = cpv.add( atom.coord, diff )

        # First atom inherits definitions from the atom its replacing
        f.atom[0].r = r_tmp
        f.atom[0].theta = theta_tmp
        f.atom[0].phi = phi_tmp

        # these are incorrect if we have guessed them, unless we compute
        # r,theta,phi
        f.atom[0].i1 = i1_tmp
        f.atom[0].i2 = i2_tmp
        f.atom[0].i3 = i3_tmp
        f.atom[0].coord = coord_tmp
        f.atom[0].zorc = zorc_tmp

        # first atom is a replacment
        self.replace_atom(atom, f.atom[0])

        # Add all the atoms of the fragment to the molecule
        # to ensure only backward zmatrix references
        # they are added to the end

        for a in f.atom[1:]:
            ix = len(self.atom)
            self.insert_atom(ix,a)
            # Replace references to negative atom numbers to point to
            # the defining atoms
            if a.i1 is None:
                a.i1 = iref[a.i1x]
            if a.i2 is None:
                a.i2 = iref[a.i2x]
            if a.i3 is None:
                a.i3 = iref[a.i3x]
                
        self.reindex()
        self.update_bonds()
        self.calculate_coordinates()

        return (0,'')

    def replace_atom(self,old,new):
        """ atom replace, retaining both old and new conn tables"""
        new.conn = new.conn + old.conn
        for i in range(len(self.atom)):
            a = self.atom[i]
            if a == old:
                self.atom[i] = new
            else:
                for i in range(len(a.conn)):
                    if a.conn[i] == old:
                        a.conn[i] = new
                        

    def remove_fragment(self,iatom,oldatom,natom):
        """Undo utility command for add_fragment
        """
        print 'remove_fragment',iatom,natom
        self.atom[iatom] = oldatom
        n = len(self.atom)
        list = []
        for i in range(1,natom+1):
            list.append(n - i)
        self.delete_list(list)
        self.reindex()
        #self.update_bonds()
        #self.calculate_coordinates()


    def insert_atom(self,pos,atom):
        """Insert an atom at the specified position"""
####        apply(Indexed.insert_atom, (self,pos,atom))
        self.atom = self.atom[:pos] + [atom] + self.atom[pos:]
        self.reindex()

    def add_atom(self,atom):
        #      if chempy.feedback['atoms']:
        #         print " "+str(self.__class__)+': adding atom "%s".' % atom.name
        self.atom.append(atom)
        #      index = self.nAtom - 1
        #      if self.index:
        #         self.index[id(atom)] = index
        index = len(self.atom) - 1
        return index

    def add_shell(self,atom):
        #if chempy.feedback['shells']:
        #print " "+str(self.__class__)+': adding shell "%s".' % atom.name
        self.shell.append(atom)
        #      index = self.nAtom - 1
        #      if self.index:
        #         self.index[id(atom)] = index
        return len(self.shell) - 1

    def add_conn(self,a1,a2):
        """Add update atom connectivity lists"""
        a1.conn.append(a2)
        a2.conn.append(a1)

    def update_bonds(self):
        """Update bond table from conn entries"""
        self.reindex()
        self.bond = []
        for a1 in self.atom:
            for a2 in a1.conn:
                if a1.get_index() < a2.get_index():
                    b = Bond()
                    self.bond.append(b)
                    b.index=[a1.get_index(), a2.get_index()]

    def update_conn(self):
        """Update conn entries from bond table"""
        self.reindex()
        # connectivity pointers
        for a in self.atom:
            a.conn = []

        print 'len of bond',len(self.bond)

        for b in self.bond:
            self.atom[b.index[0]].conn.append(self.atom[b.index[1]])
            self.atom[b.index[1]].conn.append(self.atom[b.index[0]])

    def add_bond(self,a1,a2):
        """Add a bond by updating atom connectivity lists
        This no longer adds a bond object
        """
        a1.conn.append(a2)
        a2.conn.append(a1)
##        b = Bond()
##        self.bond.append(b)
##        b.index=[a1.get_index(), a2.get_index()]

    def replace_fragment(self,atom,zfrag,atom1=None,atom2=None,atom3=None):
        """Substitute the target atom with the specified fragment
        atom1,2,3 used to set up the zmatrix path
        eventually these can be guessed
        """

    def set_variable(self,varname,value):
        """Set a variable value"""
        v = self.find_var(varname)
        if v is None:
            print 'Attempt to set nonexistent variable'
        else:
            v.value = value

    def import_geometry_orig(self,newgeom,update_constants=1):

        """Import a geometry while trying to retain as much as possible of
        the object contents.

        issues
        .. possible change to orientation, store as a z-matrix,
        export, and re-import if completely Z this is OK, otherwise we
        may need to apply some translation and rotation

        ... dummies, they will probably be missing, can the
        coordinates be back-calculated? Should be easy to see we need
        to do this from the incoming symbols

        ... zmatrix conversion convention
        gamess-uk essentially produces a mirror image relative
        to the internal conventions

        .... question of what to with connectivity

        ... August 05 need to get a working solution for Erika Palin project

        assume all atoms defined by zmatrix
        assume no shared variables
        assume X atoms have already been added such that when their
              coordinates are computed they will be what are expected

        """

        # first check for the simple cases
        somez = 0
        somec = 0
        for a in self.atom:
            if a.zorc == 'z':
                somez = 1
            if a.zorc == 'c':
                somec = 1

        if somez and somec:
            ####raise ImportGeometryError, 
            print "cant re-import mixed coordinate systems yet"
            print " --------------->> importing as cartesian"
            somez=0
            for a in self.atom:
                if a.zorc == 'z':
                    a.zorc= 'c'
                    
        if somec and not somez:

            # pure cartesian import
            # there could potentially be a re-ordering transformation
            # here, but no way to perform it yet

            if len(self.atom) != len(newgeom.atom):
                print 'number of atoms has changed'
                raise ImportGeometryError

            for i in range(len(self.atom)):
                self.atom[i].coord = copy.deepcopy(newgeom.atom[i].coord)

        elif somec == 0:

            # purely Z

            print 'import pure z-matrix format'
            self.imported_vars = {}

            # first atom do nothing
            # could check if it is at the origin, as would define a translation
            # to apply to other atoms

            # second atom
            # could check it it is along z and compute a rotation angle?
            # this would be necessary of we are to process mixed x-z
            # coord systems...

            if len(self.atom) > 1:
                rnew = self.get_distance(newgeom.atom[0],newgeom.atom[1])
                v = self.atom[1].r_var
                if v and not v.constant:
                    self.update_variable(v,rnew)
                else:
                    if not update_constants:
                        if v:
                            tester = abs(v.value - rnew)
                        else:
                            tester = abs(self.atom[1].r - rnew)
                            print 'atom 1 r diff=',tester
                            if  tester > SMALL:
                                print 'could not import, constant parameter has changed'
                                raise ImportGeometryError, "constant value changed"
                    else:
                        if v:
                            self.update_variable(v,rnew)
                        else:
                            self.atom[1].r = rnew

            # third atom
            # could check if it is in xz plane and compute a second rotation

            if len(self.atom) > 2:
                # third atom
                i1 = self.atom[2].i1.get_index()
                i2 = self.atom[2].i2.get_index()
                rnew = self.get_distance(newgeom.atom[2], newgeom.atom[i1])
                anew = self.get_angle(newgeom.atom[2], newgeom.atom[i1], newgeom.atom[i2])
                v = self.atom[2].r_var
                if v and not v.constant:
                    self.update_variable(v,rnew)
                else:
                    if not update_constants:
                        if v:
                            tester = abs(v.value - rnew)
                        else:
                            tester = abs(self.atom[2].r - rnew)
                        print 'atom 2 r diff=',tester
                        if tester > SMALL:
                            print 'could not import, constant parameter has changed'
                            raise ImportGeometryError
                    else:
                        if v:
                            self.update_variable(v,rnew)
                        else:
                            self.atom[2].r = rnew

                v = self.atom[2].theta_var
                if v and not v.constant:
                    self.update_variable(v,anew)
                else:
                    if not update_constants:
                        if v:
                            tester = abs(v.value - anew)
                        else:
                            tester = abs(self.atom[2].theta - anew)
                        print 'atom 2 theta diff=',tester
                        if tester > SMALL:
                            print 'could not import, constant parameter has changed'
                            raise ImportGeometryError
                    else:
                        if v:
                            self.update_variable(v,anew)
                        else:
                            self.atom[2].theta = anew

            for a in self.atom[3:]:

                i = a.get_index()
                i1 = a.i1.get_index()
                i2 = a.i2.get_index()
                i3 = a.i3.get_index()

                rnew = self.get_distance(newgeom.atom[i], newgeom.atom[i1])
                anew = self.get_angle(newgeom.atom[i], newgeom.atom[i1],newgeom.atom[i2])
                tnew = self.get_dihedral(newgeom.atom[i], newgeom.atom[i1],newgeom.atom[i2],newgeom.atom[i3])

                print i,'measured values',rnew,anew,tnew

                print 'upd r'

                v = a.r_var
                if v and not v.constant:
                    self.update_variable(v,rnew)
                else:
                    if not update_constants:
                        if v:
                            tester = abs(v,value - rnew)
                        else:
                            tester = abs(a.r - rnew)
                        print 'atom '+str(i)+' r diff=',tester
                        if tester > SMALL:
                            print 'could not import, constant parameter has changed'
                            raise ImportGeometryError
                    else:
                        if v:
                            self.update_variable(v,rnew)
                        else:
                            a.r = rnew

                print 'upd theta'

                v = a.theta_var
                if v and not v.constant:
                    self.update_variable(v,anew)
                else:
                    if not update_constants:
                        if v:
                            tester = abs(v,value - anew)
                        else:
                            tester = abs(a.theta - anew)
                        print 'atom '+str(i)+' theta diff=',tester
                        if tester > SMALL:
                            print 'could not import, constant parameter has changed'
                            raise ImportGeometryError
                    else:
                        if v:
                            self.update_variable(v,anew)
                        else:
                            a.theta = anew

                print 'upd phi'

                v = a.phi_var
                if v and not v.constant:
                    self.update_variable(v,tnew,torsion=1)
                else:
                    tnew = self._adjust_dihedral(tnew, a.phi)
                    if self.debug:
                        print 'using adjusted dihedral',tnew
                    if not update_constants:
                        if v:
                            tester = abs(v,value - tnew)
                        else:
                            tester = abs(a.phi - tnew)

                        print a.get_index(),'phi',a.phi,tnew
                        tester = abs(a.phi - tnew)
                        print 'atom '+str(i)+' phi diff=',tester
                        if tester > SMALL:
                            print 'could not import, constant parameter has changed'
                            raise ImportGeometryError
                    else:
                        if v:
                            self.update_variable(v,tnew)
                        else:
                            a.phi = tnew

                print 'done'

            # Compute new coords
            self.calculate_coordinates()

    def import_geometry(self,newgeom,update_constants=1):

        """Import a geometry while trying to retain as much as possible of
        the object contents.
        """

        # first check for the simple cases
        somez = 0
        somec = 0
        for a in self.atom:
            if a.zorc == 'z':
                somez = 1
            if a.zorc == 'c':
                somec = 1

        if somez == 0 and len(self.variables) == 0:

            # pure cartesian import with no variables, allow everything to change
            update_constants=1

        if 0:

            # pure cartesian import
            # there could potentially be a re-ordering transformation
            # here, but no way to perform it yet

            if len(self.atom) != len(newgeom.atom):
                print 'number of atoms has changed'
                raise ImportGeometryError

            for i in range(len(self.atom)):
                self.atom[i].coord = copy.deepcopy(newgeom.atom[i].coord)

###        elif somec == 0:

        else:

            # Z-matrix import including some cartesians

            if self.debug:
                print 'import pure z-matrix format'

            self.imported_vars = {}

            # phi convention
            self.phi_convention = 1

            # Make a temporary copy of the starting point
            # This will hold the new cartesians and internals
            # computed from them

            # It also contains dummy coordinates reconstituted from
            # the internals (ie dummy coordinates in the incoming frame)
            # however workz will not be a valid z-matrix - it will not
            # in general obey z-matrix conventions

            # there should be a clever way to compute dummy coordinates for one of the
            # first 3 atoms (ie not z-matrix conventions) but we do not have that yet
            
            workz = copy.copy(self)

            # Load up new cartesians where we can
            i2 = 0
            for i1 in range(len(workz.atom)):

                if self.debug:
                    print
                    print 'import cart loop i1',i1,'workz name',workz.atom[i1].name[0]

                #jmht - need to check that the names match up, otherwise we are foobar
                if string.upper(workz.atom[i1].name) != string.upper(newgeom.atom[i1].name):
                    print "Error importing geometry! Atom tags do not match up."
                    raise ImportGeometryError,"Error importing geometry! Atom tags do not match up."

                if string.upper(workz.atom[i1].name[0]) == 'X' and \
                       string.upper(newgeom.atom[i2].name[0]) != 'X':
                    # We have a dummy but the incoming geometry is missing it
                    # We can try and compute its coordinates using the internals
                    # we currently have
                    #   this assumes they were constants, also for the first few atoms
                    #   things may break down because of zmatrix convention and
                    #   orientation differences
                    workz.calculate_one_coordinate(i1)

                else:
                    # Take over the new coordinates into the temporary structure
                    workz.atom[i1].coord = newgeom.atom[i2].coord
                    workz.atom[i1].ok = 1
                    i2 = i2 + 1

                    a = self.atom[i1]
                    w = workz.atom[i1]

                    if a.zorc == 'z':
                        # now attempt to find internal coordinates for workz and check whether
                        # constants are being violated
                        workz.update_internals_from_cartesians(i1,update_constants=update_constants)
                    else:
                        # move cartesians as input into variables if present, and check for
                        # violations

                        workz.update_cartesians_from_cartesians(i1,a,update_constants=update_constants)


            for i1 in range(len(workz.atom)):

                if self.debug:
                    print
                    print 'update self loop',i1,'workz name',workz.atom[i1].name[0]
                    
                    # finally update of our own internals and variables

                    if a.zorc == 'z':

                        if i1 > 1:
                            v = a.r_var
                            if not update_constants and (not v or v.constant):
                                pass # constant value cannot be updated
                            elif v:
                                v.value = w.r_var.value
                            else:
                                a.r = w.r

                        if i1 > 2:
                            v = a.theta_var
                            if not update_constants and (not v or v.constant):
                                pass # constant value cannot be updated
                            elif v:
                                v.value = w.theta_var.value
                            else:
                                a.theta = w.theta

                        if i1 > 3:
                            v = a.phi_var
                            if not update_constants and (not v or v.constant):
                                pass # constant value cannot be updated
                            elif v:
                                v.value = w.phi_var.value
                            else:
                                a.phi = w.phi
                    else:

                        if 1:
                            v = a.x_var
                            if not update_constants and (not v or v.constant):
                                pass # constant value cannot be updated
                            elif v:
                                v.value = w.x_var.value
                            else:
                                a.coord[0] = w.coord[0]

                            v = a.y_var
                            if not update_constants and (not v or v.constant):
                                pass # constant value cannot be updated

                            elif v:
                                v.value = w.y_var.value
                            else:
                                a.coord[1] = w.coord[1]

                            v = a.z_var
                            if not update_constants and (not v or v.constant):
                                pass # constant value cannot be updated

                            elif v:
                                v.value = w.z_var.value
                            else:
                                a.coord[0] = w.coord[0]


            # Compute new coords, this may involve a change back
            # to the z-matrix orientation
            self.calculate_coordinates()

    def update_internals_from_cartesians(self,index,update_constants=0):

        a = self.atom[index]
        if self.debug:
            print 'update_internals_from_cartesians: Current atom ',index,' coords',
            for coor in a.coord:
                print "%10.5f" % (coor,),
            print

        if index > 0:
            i1 = a.i1.get_index()
            rnew = self.get_distance(a,self.atom[i1])
            if self.debug:
                print 'new r (',index+1,i1+1,') = ',rnew
            v = a.r_var
            if v and not v.constant:
                self.update_variable(v,rnew)
            else:
                if not update_constants:
                    if v:
                        tester = abs(v.value - rnew)
                    else:
                        tester = abs(a.r - rnew)
                        print '    atom ',index+1,' r diff=',tester
                        if  tester > SMALL:
                            print 'could not import, constant parameter has changed'
                            raise ImportGeometryError, "constant value changed"
                else:
                    if v:
                        self.update_variable(v,rnew)
                    else:
                        a.r = rnew

        if index > 1:
            i2 = a.i2.get_index()
            anew = self.get_angle(a, self.atom[i1], self.atom[i2])

            if self.debug:
                print 'new theta (',index+1,i1+1,i2+1,') = ',anew

            v = a.theta_var
            if v and not v.constant:
                self.update_variable(v,anew)
            else:
                if not update_constants:
                    if v:
                        tester = abs(v.value - anew)
                    else:
                        tester = abs(a.theta - anew)
                    print '   atom ',index,'theta diff=',tester
                    if tester > SMALL:
                        print 'could not import, constant parameter has changed'
                        raise ImportGeometryError
                else:
                    if v:
                        self.update_variable(v,anew)
                    else:
                        a.theta = anew

        if index > 2:
            i3 = a.i3.get_index()

            tnew = self.get_dihedral(a, self.atom[i1],self.atom[i2],self.atom[i3])
            if self.debug:
                print 'new phi (',index+1,i1+1,i2+1,i3+1,') =',tnew

            v = a.phi_var
            if v and not v.constant:
                self.update_variable(v,tnew,torsion=1)
            else:
                tnew = self._adjust_dihedral(tnew, a.phi)
                print '    using adjusted dihedral',tnew
                if not update_constants:
                    if v:
                        tester = abs(v,value - tnew)
                    else:
                        tester = abs(a.phi - tnew)

                    print a.get_index(),'phi',a.phi,tnew
                    tester = abs(a.phi - tnew)
                    print '    atom '+str(index)+' phi diff=',tester
                    if tester > SMALL:
                        print 'could not import, constant parameter has changed'
                        raise ImportGeometryError
                else:
                    if v:
                        self.update_variable(v,tnew)
                    else:
                        a.phi = tnew


    def update_cartesians_from_cartesians(self,index,aref,update_constants=0):
        """ From the name you might expect this code does very little,
        however there is a job to do when a new set of cartesians is
        generated; any variable definitions need to be check and an exception
        thrown if constant values have changed.
        
        """

        a = self.atom[index]
        if self.debug:
            print 'update_cartesians_from_cartesians: Current atom ',index,' coords',
            for coor in a.coord:
                print "%10.5f" % (coor,),
            print

        if 1:
            xnew = a.coord[0]
            v = a.x_var
            if v and not v.constant:
                self.update_variable(v,xnew)
            else:
                if not update_constants:
                    if v:
                        tester = abs(v.value - xnew)
                    else:
                        tester = abs(aref.coord[0] - xnew)
                        print '    atom ',index+1,' x diff=',tester
                        if  tester > SMALL:
                            print 'could not import, constant parameter has changed'
                            raise ImportGeometryError, "constant value changed"
                else:
                    if v:
                        self.update_variable(v,xnew)
                    else:
                        # All done
                        pass

        if 1:
            ynew = a.coord[1]
            v = a.y_var
            if v and not v.constant:
                self.update_variable(v,ynew)
            else:
                if not update_constants:
                    if v:
                        tester = abs(v.value - ynew)
                    else:
                        tester = abs(aref.coord[1] - ynew)
                        print '    atom ',index+1,' y diff=',tester
                        if  tester > SMALL:
                            print 'could not import, constant parameter has changed'
                            raise ImportGeometryError, "constant value changed"
                else:
                    if v:
                        self.update_variable(v,ynew)
                    else:
                        # All done
                        pass

        if 1:
            znew = a.coord[2]
            v = a.z_var
            if v and not v.constant:
                self.update_variable(v,znew)
            else:
                if not update_constants:
                    if v:
                        tester = abs(v.value - znew)
                    else:
                        tester = abs(aref.coord[2] - znew)
                        print '    atom ',index+1,' z diff=',tester
                        if tester > SMALL:
                            print 'could not import, constant parameter has changed'
                            raise ImportGeometryError, "constant value changed"
                else:
                    if v:
                        self.update_variable(v,znew)
                    else:
                        # All done
                        pass

    def update_variable(self,var,val,torsion=0):

        # need to code up the sign
        if self.debug:
            print 'update v',var.name, val 

        if self.imported_vars.has_key(var.name):
            # could average here
            oldval = self.imported_vars[var.name][0]
            if torsion:
                val = self._adjust_dihedral(val,oldval)
                if self.debug:
                    print 'using adjusted dihedral1',val

            self.imported_vars[var.name].append(val)

            tester = abs(val-oldval)

            if self.debug:
                print 'var val check var=',var.name,' diff=',tester
            if tester > SMALL:
                print 'could not import, mismatched variable values'
                print oldval, val
                raise ImportGeometryError, "mismatched variable values"
        else:
            # the first update of this variable
            if torsion:
                val = self._adjust_dihedral(val, var.value)
                print 'using adjusted dihedral2',val
            self.imported_vars[var.name] = [ val ]

        # assign the current value of the variable
        # may need to average here
        var.value = val

    def _adjust_dihedral(self, val, oldval):

        if self.debug:
            print '_adjust_dihedral',val,oldval
        # apply any adjustment of measuring convention
        val = val*self.phi_convention
        # apply rotational periodicity
        more = 1
        while more:
            tester = oldval - val
            if self.debug:
                print 'tester',tester
            if tester < -180:
                if self.debug:
                    print 'shift -360'
                val = val - 360
            elif tester > 180:
                if self.debug:
                    print 'shift +360'
                val = val + 360
            else:
                more = 0
        return val

    def autoz(self,testang=45):

        """ Devise a completely new zmatrix from the
        structure. This will involve reordering the atoms

        at the moment no existing z-matrix definitions are used

        testang : abs(ang-90) cannot exceed this for a bond angle
                 or an angle involved in the declaration of a dihedral

        """

        if self.debug:
            print 'zmatrix.autoz'

        if not self.is_fully_connected():
            self.warn("system must be fully connected")
            raise ConversionError, "system must be fully connected"

        # use the atoms OK flag to denote whether we have a valid definition 
        # for the atom
        for a in self.atom:
            a.ok = 0

        if self.debug > 2:
            self.list()

        # this controls the code from pymol which implements a proper
        # torsion loop using the table of bonds
        # we have changed the algorithm to allow specification by improper
        # torsions 
        use_bond_list=0

        if use_bond_list:
            for a in self.atom:
                print a.conn

            # Reindex the table of bonds reflecting our edits
            # this is needed by the loop over bonds as the basis for dihedral search
            # we can skip this if the alternative strategy works OK

            print 'on entry len bond', len(self.bond)
            self.update_bonds()
            print 'new len bond', len(self.bond)
        
            if self.debug > 2:
                print 'revised bonding:'
                self.list()

            ang_tol=160
        

        # generates raw atom sets needed to construct an internal coordinate
        # description of the molecule

        self.list()
        
        center = [0.0,0.0,0.0]
        nAtom = len(self.atom)
        to_go = nAtom

        if to_go < 2:
            z_set = [(self.atom[0],)]
        elif to_go < 3:
            z_set = [(self.atom[0],),(self.atom[1],self.atom[0])]
        else:
            # get center of molecule
            for a in self.atom:
                center = cpv.add(center,a.coord)
            center = cpv.scale(center,1.0/nAtom)
            # find most central multivalent atom
            min_a = None
            c = 0
            for a in self.atom:
                if len(a.conn)>1: # must have at least two neighbors
                    d = cpv.distance(a.coord,center)
                    if min_a < 0:
                        min_d = d
                        min_a = a
                    elif d<min_d:
                        min_d=d
                        min_a=a
                c = c + 1

            max_c = 0
            for a in self.atom:
                if len(a.conn) > max_c:
                    max_c = len(a.conn)
                    min_a = a

            # make this our first atom
            if min_a:
                fst = min_a
            else:
                fst = self.atom[0]
            print 'fst',fst.get_index()
            z_set = [( fst,) ]
            fst.ok = 1
            to_go = to_go - 1

            # for the second atom, try to choose different multivalent neighbor
            nxt = None
            for b in fst.conn:
                if len(b.conn)>1:
                    nxt = b
                    break
            # safety, choose any neighbor
            if nxt is None:
                nxt = fst.conn[0]

            z_set.append((nxt,fst))
            nxt.ok = 1
            to_go = to_go - 1

            print '2nd',nxt.get_index()

            # for the third atom, choose a different multivalent neighbor
            trd = None
            for b in fst.conn:
                #testang = self.get_angle(self.atom[nbr],self.atom[fst],self.atom[nxt])
                #print 'testang 1',testang
                #if testang < 170:
                if len(b.conn) > 1:
                    if not b.ok:
                        trd = b
                        break
            if trd:
                print 'trd 1',trd.get_index()
            else:
                print 'safety code for trd'

            # safety, choose any unchosen neighbor
            if not trd:
                for b in fst.conn:
                    if not b.ok:
                        trd = b
                        break
            z_set.append((trd,fst,nxt))
            trd.ok = 1
            to_go = to_go - 1
            print 'trd 2',trd.get_index()
            print 'to_go',to_go

            # this is the original pymol algorithm
            # the alternative is an attempt to optimise choice of
            # paths and to include impropers as well

            if to_go and use_bond_list:
                # now find all proper torsions in the molecule that can be used
                # to define atoms at one or other end
                tors = []
                for b in self.bond: # use bond as center of torsion
                    print 'bond indices',b.index[0],b.index[1]
                    a1 = self.atom[b.index[0]]
                    a2 = self.atom[b.index[1]]
                    for c in a1.conn:
                        if c != a2:
                            ang1 = self.get_angle(c,a1,a2)
                            print '   checking c=',c.get_index(), 'angle=',ang1,
                            if ang1 >= ang_tol:
                                print 'Rejected'                              
                            else:
                                print ""
                                for d in a2.conn:
                                    if d != a1 and d != c:
                                        ang2  = self.get_angle(a1,a2,d)
                                        print '   checking d=',d.get_index(), 'angle=',ang2,
                                        if ang2 < ang_tol:                                        
                                            if c.get_index() < d.get_index():
                                                to = (c,a1,a2,d)
                                            else:
                                                to = (d,a2,a1,c)
                                            tors.append(to)
                                            print 'Keep',to
                                        else:
                                            print 'Rejected'

                print 'List of proper Torsions',tors
                if len(tors):
                    # assign atoms where possible using torsions
                    oldcnt = -1
                    while 1:
                        print 'Loop to_go=',to_go
                        if oldcnt == to_go:
                            print 'tors loop finished with ',to_go,' unassigned atoms'
                            break
                        oldcnt = to_go
                        for tor in tors:
                            a0 = tor[0]
                            a1 = tor[1]
                            a2 = tor[2]
                            a3 = tor[3]
                            if ( (not a0.ok) and a1.ok and a2.ok and a3.ok ):
                                z_set.append((a0,a1,a2,a3))
                                a0.ok = 1
                                print 'select ',(a0,a1,a2,a3)
                                to_go = to_go - 1
                            elif ( a0.ok and a1.ok and a2.ok and (not a3.ok) ):
                                z_set.append((a3,a2,a1,a0))
                                a3.ok = 1
                                print 'select ',(a3,a2,a1,a0)
                                to_go = to_go - 1

            if to_go:
                # some atoms could not be assigned using proper torsions
                # try using cominations impropers and propers

                oldcnt = -1
                while 1:
                    print 'Loop to_go=',to_go
                    if oldcnt == to_go:
                        print 'impropers loop finished with ',to_go,' unassigned atoms'
                        break
                    oldcnt = to_go

                    unass = []
                    for a in self.atom:
                        if not a.ok:
                            unass.append(a)
                    print 'unassigned: ',unass

                    for orphan in unass:
                        for con in orphan.conn:
                            if con.ok:
                                print 'XXXXX'
                                i2 = self._find_i2(orphan,con,check=OK_CHECK,testang=testang)
                                print 'XXXXX returned',i2
                                if i2:
                                    print 'YYYYY search i3 proper'
                                    i3 = self._find_i3(orphan,con,i2,check=OK_CHECK,testang=testang)
                                    print 'YYYYY proper returned',i3
                                    if i3:
                                        print 'found possible definition',i3.get_index(),i2.get_index(),con.get_index(),orphan.get_index()
                                        z_set.append((orphan,con,i2,i3))
                                        orphan.ok = 1
                                        to_go = to_go - 1
                                    else:
                                        print 'YYYYY search i3 improper'
                                        i3 = self._find_i3(orphan,con,i2,check=OK_CHECK,improper=1,testang=testang)
                                        print 'YYYYY improper returned',i3
                                        if i3:
                                            print 'found possible definition',i3.get_index(),i2.get_index(),con.get_index(),orphan.get_index()
                                            to_go = to_go - 1
                                            orphan.ok = 1                                                
                                            z_set.append((orphan,con,i2,i3))
                            if orphan.ok:
                                break

        if len(z_set) != len(self.atom):
            self.warn("Autoz failed - probably linear angles, you may need to add some dummy atoms")
            raise ConversionError, "Autoz failed - probably linear angles, you may need to add some dummy atoms"

        print 'autoz: Building new zmatrix'
        
        if self.debug > 2:
            print 'internal tuples',z_set


        # retain the old list to reference into
        old_atoms = copy.copy(self.atom)
        i=0
        warn = 0
        self.atom = []

        for z in z_set:
            print 'z',z
            print 'z[0]',z[0]
            indices = z
            a = z[0]

            a.zorc = 'z'

            a.r = 0.0
            a.theta = 0.0
            a.phi = 0.0
            a.r_var = None
            a.theta_var = None
            a.phi_var = None

            if len(indices) > 1:
                a.i1 = indices[1]
                a.r = cpv.distance(a.coord,a.i1.coord)
                if a.r < 0.01:
                    warn = 1
                    a.r = 0.01
            else:
                a.i1 = None

            if len(indices) > 2:
                a.i2 = indices[2]
                try:
                    a.theta = self.get_angle(a,a.i1,a.i2)
                except ZeroDivisionError, e:
                    self.logerr('zero division')
                    a.theta = 0.0
                    warn = 1
            else:
                a.i2 = None

            if len(indices) > 3:
                a.i3 = indices[3]
                try:
                    a.phi = self.get_dihedral(a,a.i1,a.i2,a.i3)
                except ZeroDivisionError, e:
                    self.logerr('zero division')
                    a.phi = 0.0
                    warn = 1
            else:
                a.i3 = None

            self.atom.append(a)
            i=i+1

        if warn:
            print "Some distances 0 or internal coordinates undefined"

        self.zlist()

    def is_fully_connected(self):
        set = [self.atom[0]]
        more=1
        while more:
            more=0
            for a in set:
                for b in a.conn:
                    if b in set:
                        pass
                    else:
                        set.append(b)
                        more=1
        print 'connection check',len(set),len(self.atom)
        if len(set) == len(self.atom):
            return 1
        else:
            return 0

    def logerr(self,txt):
        """log txt as an error message"""
        print txt
        self.errors.append(txt)

    def warn(self,txt):
        """log txt as an error message"""
        print "warning:",txt

    def wrtmsi(self,file):
        """Write the MSI format file"""
        from objects.periodic import z_to_el
        mol = self
        object_ids = []
        fp = open(file,"w")
        ix=1
        fp.write("# MSI CERIUS2 DataModel File Version 4 0\n")
        fp.write("(%d Model\n" % ix)
        ix = ix + 1
        fp.write("  (A C Label molecule)\n")

        # Output atom objects 
        i=0
        for a in mol.atom:
            object_ids.append(ix)
            fp.write(" (%d Atom\n" % ix)
            ix = ix + 1
            ###if frag->atoms[i].set_charge:
            fp.write(" (A D QuasiCharge %f)\n" % a.partial_charge)
            fp.write(" (A I ACL \"%d %s\")\n" % (a.get_number(), z_to_el[a.get_number()]))
            fp.write(" (A D XYZ (%f %f %f))\n" % (a.coord[0],a.coord[1],a.coord[2]))
            fp.write(" (A C Label %s)\n" % a.name )
            fp.write(")\n")

        for b in mol.bond:
            i = b.index[0]
            k = b.index[1]

            if i > k:
                fp.write(" (%d Bond\n" % ix)
                ix=ix+1
                fp.write(" (A O Atom1 %d)\n" % object_ids[i])
                fp.write(" (A O Atom2 %d)\n" % object_ids[k])
                fprintf(fp," )\n");

        fp.write(")\n")


    def wrtcrd(self,file,chain='CHAI',residues=None,write_dummies=1,unique_label=1):
        """Write a CHARMM CRD file"""
        from periodic import z_to_el
        mol = self
        object_ids = []
        fp = open(file,"w")
        fp.write("* coords from ccp1gui\n")
        fp.write("* \n")

        if write_dummies:
            n = len(self.atom)
        else:
            n = self.get_nondum()

        fp.write("%d\n" % n)
        # Output atom objects 
        ix=1
        i=0
#  (2I5,2(1X,A4),3A10,1X,A4,1X,A4,A10)
#    1    1 WAT1 OH2    0.00000   0.00000   0.00000 WATR 1      0.00000
#    2    1 WAT1 H1     0.00000  -0.75184   0.56820 WATR 1      0.00000
#    3    1 WAT1 H2    -0.00000   0.75184   0.56820 WATR 1      0.00000
#    4    2 WAT2 OH2   -8.66025   0.00000  -5.00000 WATR 2      0.00000
#    5    2 WAT2 H1    -7.74843   0.00000  -4.76189 WATR 2      0.00000
#    6    2 WAT2 H2    -8.68007   0.00000  -5.94219 WATR 2      0.00000

        nresids = 0
        resids = {}
        for a in mol.atom:
            if write_dummies or (a.seqno2 > -1):            
               i = a.get_index()+1
               if residues:
                   r = residues[i]
                   try:
                       rid = resids[r]
                   except KeyError:
                       nresids=nresids+1
                       resids[r]=nresids
                       rid = nresids
               else:
                   r = 'RESI'
                   rid = 1
               name = string.upper(a.name)
               if unique_label:
                   name=name+str(ix)
               fp.write("%5d%5d %-4s %-4s%10.5f%10.5f%10.5f %4s %-4s%10.5f\n" %(
                   ix,rid,r,name,a.coord[0],a.coord[1],a.coord[2],
                        chain,'1',0.0))
               ix = ix + 1
        fp.close()
        
    def wrtcml(self,file,title="untitled"):
        """Write a CML file
        this is CML 1 I think
        """
        from objects.periodic import z_to_el
        mol = self
        object_ids = []
        fp = open(file,"w")

        fp.write("<!DOCTYPE molecule SYSTEM \"cml.dtd\">\n")
        fp.write("<molecule xmlns=\"http://www.xmlcml.org/dtd/cml1_0_1\"  convention=\"XYZ\" title=\"%s\">\n" % title)
        fp.write("<atomArray>\n")
        ##fp.write("<integerArray builtin=\"nonHydrogenCount\">0 0 0 0 0 0 0 1 0 3 0 3 0 3 </integerArray>")
        fp.write("<floatArray builtin=\"x3\">")
        for a in self.atom:
            fp.write("%f " % a.coord[0])
        fp.write("</floatArray>\n")
        ##fp.write("<floatArray builtin="x2">-30.0 -15.000000000000016 14.999999999999982 30.466666666666658 13.133333333333326 -12.866666666666674 63.133333333333326 62.48028192004379 35.133333333333326 85.13333333333333 27.799999999999994 -30.00000000000004 -60.0 -29.99999999999998 </floatArray>")
        fp.write("<stringArray builtin=\"elementType\">")
        for a in self.atom:
            fp.write("%s " % z_to_el[a.get_number()])
        fp.write("</stringArray>\n")
        fp.write("<floatArray builtin=\"y3\">")
        for a in self.atom:
            fp.write("%f " % a.coord[1])
        fp.write("</floatArray>\n")
        ##fp.write("<floatArray builtin="y2">5.450297236842311E-15 -25.980762113533153 -25.980762113533174 0.10514243960031422 26.771809106266982 22.105142439600314 3.4384757729336477 36.07300758558097 43.43847577293365 -16.561524227066354 -51.894857560399686 -51.961524227066306 1.693600333362316E-14 51.961524227066334 </floatArray>")

        fp.write("<floatArray builtin=\"z3\">")
        for a in self.atom:
            fp.write("%f " % a.coord[2])
        fp.write("</floatArray>\n")
        
        fp.write("<stringArray builtin=\"atomId\">")
        for a in self.atom:
            fp.write("a%d " % (a.get_index()+1))
        fp.write("</stringArray>\n")
        fp.write("</atomArray>\n")
        fp.write("<bondArray>\n")
        fp.write("<stringArray builtin=\"order\">")
        for b in self.bond:
            fp.write("A ")
        fp.write("</stringArray>\n")
        fp.write("<stringArray builtin=\"stereo\">")
        for b in self.bond:
            fp.write("null ")
        fp.write("</stringArray>\n")

        fp.write("<stringArray builtin=\"atomRef\">")
        for b in self.bond:
            fp.write("a%d " % (b.index[0]+1))
        fp.write("</stringArray>\n")

        fp.write("<stringArray builtin=\"atomRef\">")
        for b in self.bond:
            fp.write("a%d " % (b.index[1]+1))
        fp.write("</stringArray>\n")

        fp.write("<stringArray builtin=\"id\">               </stringArray>\n")
        fp.write("</bondArray>\n")
        fp.write("</molecule>\n")


    def wrtres(self,file,title="untitled"):
        """Write a SHELXTL .res  file
        """
        from objects.periodic import z_to_el
        mol = self
        object_ids = []
        fp = open(file,"w")
        fp.write("TITL %s\n" % title)
        fp.write("CELL  0.71073   10.0 10.0 10.0 90.0 90.0 90.0\n")
        fp.write("SYMM   X, Y, Z\n")
        zs = []
        counts = {}
        for a in self.atom:
            z = a.get_number()
            if z not in zs:
                zs.append(z)
                counts[z]=0
            counts[z] = counts[z]+1
        fp.write("SFAC ")
        for z in zs:
            fp.write("%s " % (z_to_el[z],))
        fp.write("\n")

        fp.write("UNIT ")
        for z in zs:
            fp.write("%d " % (counts[z],))
        fp.write("\n")

        for a in self.atom:
            z = a.get_number()
            sfac = zs.index(z)+1
            fp.write("%4s %-3d %9.5f %9.5f %9.5f %9.5f\n" %
                     (a.name, sfac,
                      a.coord[0]/10.0,a.coord[1]/10.0,a.coord[2]/10.0,
                      11.00000))
        fp.write("END \n")


    def update_bond_distances( self, atom, newElement):
        """ Scale the bond for atom so that the bond distance between it
            and the atom it is connected to (root) is set to be that as defined
            in the table of bond distances in periodic. Currently this is only 
            supposed to be used for x-atoms.
            If we have changed any atoms, we return a function that can be used by undo
            to undo this change, otherwise we return None
        """

        debug=1
        if debug: print "updating bond distances"
        # Find out if we are connected to more than one x-atom
        # if so we don't do anything - an alternative would be to create a zmatrix
        # and change things that way
        #
        i=0
        for bonded in atom.conn:
            if not bonded.symbol[0].lower() == 'x':
                root = bonded
                i+=1

        if i != 1:
            print "Cannot change bond length as x-atom connected to > 1 non-x atom"
            return None

        # The new bond length
        newLength = get_bond_length( newElement, root.symbol )
        oldLength = cpv.distance( atom.coord, root.coord )

        # See if all atoms have a zmatrix definition
        connected = atom.get_connected( root )
        if debug: print "connected is ",connected
        if not connected:
            print "Fragment is circular! - cannot change bond length!"
            return
        
        zmat = 1
        for c in connected:
            if c.zorc != 'z':
                zmat = None

        if zmat:
            # We have a z-matrix definition for all atoms so update the definition
            # See if this atom and root have a definition defining their distance
            if debug: print "updating bond distances using zmatrix"
            if ( atom.i1 == root or root.i1 == atom ):
                if atom.i1 == root:
                    defAtom = atom
                else:
                    defAtom = root

                if defAtom.r_var:
                    defAtom.r_var.value = newLength
                    def undo_move( defAtom, oldLength):
                        defAtom.r_var.value = oldLength
                else:
                    defAtom.r = newLength
                    def undo_move( defAtom, oldLength):
                        defAtom.r = oldLength
                return lambda d=defAtom : undo_move(d, oldLength)
            
        # Shift the atoms by directly updating the Cartesian coordinates
        # Might need to think about what to do if some atoms had zmatrix definitions
        # as these won't be updated to reflect the change
        if debug: print "updating bond distances using cartesians"
        diff = self.get_bond_coord_diff( atom, root, newLength )
        for c in connected:
            c.coord = cpv.add( c.coord, diff )

        def undo_move( connected, diff ):
            for c in connected:
                c.coord = cpv.sub( c.coord, diff )

        return lambda c = connected: undo_move( c, diff )

    def get_bond_coord_diff( self, atom, root, newLength ):
        """ Get the change in coordinates that can be applied to all atoms in a fragment
            to shift them all along the axis of the bond between atom and root so that
            the new bond length is newLength
        """

        if newLength <= 0.0:
            print "Cannot make a bond length 0 or have a negative bond length!"
            
        # get translation vector
        oldLength = cpv.distance( atom.coord, root.coord )
        oldVec = [ atom.coord[0] - root.coord[0],
                   atom.coord[1] - root.coord[1],
                   atom.coord[2] - root.coord[2] ]
        scale = newLength / oldLength
        newVec = cpv.scale( oldVec, scale )
        diff = cpv.sub( newVec, oldVec )
        return diff

    def rotate_about_bond(self, atom1, atom2, angle):
        """ Rotate a fragement about an axis defined by two atoms
            by angle in degrees - this still needs work. Sigh..."""

        debug = 1
        
        if atom1 not in atom2.conn:
            print "Atom %s not connected to atom %s" % ( atom1, atom1)
            return

        if debug: print "got two selected and connected atoms: %s and %s" % ( atom1,atom2)

        # Find out if at least one of the atoms is part of a fragment that is not
        # connected back to the rest of the molecule with > 1 bond, and then return
        # the smallest fragment so that we can rotate it
        
        connected1 = atom1.get_connected( atom2 )
        ok = 0
        if not connected1:
            connected1=[]
        else:
            ok = 1

        connected2 = atom2.get_connected( atom1 )
        if not connected2:
            if not ok:
                print "Both fragments are not viable - cannot rotate!"
                return
            connected2 = []
        else:
            pass

        if len(connected1) < len(connected2):
            smallest = connected1
            center = atom1
            root = atom2
        else:
            smallest = connected2
            center = atom2
            root = atom1

        if 0:
            # See if there is a zmatrix definition for the dihedral angle we want to
            # rotate about
            if center.zorc == 'z' and root.zorc == 'z':
                dihedral=None
                for clink in center.conn:
                    if clink.zorc == 'z' and clink.i1 == center and clink.i3 in root.conn:
                        dihedral = clink

                if not dihedral:
                    for clink in root.conn:
                        if clink.zorc == 'z' and clink.i1 == root and clink.i3 in center.conn:
                            dihedral = clink
                if dihedral:
                    if debug:
                        print "Got dihedral definition for atom %s" % dihedral
                        print "def is: i1:%s i2:%s i3:%s" % (dihedral.i1,dihedral.i2,dihedral.i3)

                # Now check if all atoms is the fragement we are going to rotate have a zmatrix
                # definition so that we ensure that we rotate the lot if we rotate using a z-matrix
                zmat = 1
                for atom in smallest:
                    if atom.zorc == 'c':
                        zmat = None

                if zmat:
                    print "Rotating fragment using a zmatrix by angle %s"
                    # Change the dihedral definition
                    if dihedral.phi_var:
                        dihedral.phi_var.value += (angle * dihedral.phi_sign)
                    else:
                        dihedral.phi += angle
                    self.calculate_coordinates()
                    return

        # Failed to rotate using a zmatrix, so use Cartesians
        # Again - need to think what happens to mixed definitions here
        if debug: print "XRotating fragment using Cartesians by angle %s" % angle
        axis = cpv.sub( atom1.coord, atom2.coord )
        print "center is ",center

        for atom in self.atom:
            atom.flag = 0
        for atom in smallest:
            print "rotating atom ",atom
            atom.rotate( angle, axis, center=center.coord )
            atom.flag=1

        print 'updating internals'
        # Still a problem here in that shared variables could
        # might need to be "unshared"

        self.imported_vars = {}
        for atom in self.atom:
            if atom.flag:
                i1 = atom.get_index()
                self.update_internals_from_cartesians(i1,update_constants=1)

        self.calculate_coordinates()

    def translate(self, dr):
        """Translate all atoms by a vector dr"""
        for a in self.atom:
            a.coord = cpv.add(a.coord,dr)

    def rotate(self, angle, axis, center = [0.0,0.0,0.0]):
        """Rotate all atoms around center"""
        R = cpv.rotation_matrix(angle,axis)
        for a in self.atom:
            rt = cpv.sub(a.coord,center)
            a.coord = cpv.add(cpv.transform(R,rt),center)
            
    def centerOfCharge(self):
        r = [0.0,0.0,0.0]
        mtot = 0
        for a in self.atom:
            r = cpv.add(cpv.scale(a.coord,a.formal_charge),r)
            mtot += a.formal_charge
        if mtot > 0:
            return cpv.scale(r,1.0/mtot)
        else:
            return r

    def centerOfMass(self):
        r = [0.0,0.0,0.0]
        mtot = 0
        for a in self.atom:
            try:
                m = a.get_mass()
            except Exception:
                m = 1.0
            r = cpv.add(cpv.scale(a.coord,m),r)
            mtot += m
        if mtot > 0:
            return cpv.scale(r,1.0/mtot)
        else:
            return r

    def inertialTensor(self, origin = [0.0,0.0,0.0]):
        I = Numeric.reshape(Numeric.array((0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0)),(3,3))
        for a in self.atom:
            try:
                m = a.get_mass()
            except Exception:
                m = 1.0
            r = cpv.sub(a.coord, origin)
            I[0,0] += m*r[0]**2
            I[0,1] += m*r[0]*r[1]
            I[0,2] += m*r[0]*r[2]
            I[1,1] += m*r[1]**2
            I[1,2] += m*r[1]*r[2]
            I[2,2] += m*r[2]**2
        I[1,0] = I[0,1]
        I[2,0] = I[0,2]
        I[2,1] = I[1,2]
        return I

    def mainAxis(self, origin = [0.0,0.0,0.0]):
        """Return a matrix with the eigenvectors of the
        inertial tensor, calculated with the given origin."""
        I = self.inertialTensor( origin )
        valvec = LinearAlgebra.Heigenvectors(I)
        res = []
        for i in range(3):
            res.append([valvec[0][i],[valvec[1][i][0],
                                      valvec[1][i][1],
                                      valvec[1][i][2]]])
        res.sort()
        return [res[0][1],res[1][1],res[2][1]]


    def toStandardOrientation(self):
        cm = self.centerOfMass()
        self.translate(cpv.negate(cm))
        A = self.mainAxis()
        for a in self.atom:
            a.coord = cpv.transform(A,a.coord)


    def getMomentsOfInertia(self):
        """ Get the eigenvalues of the axes. """
        I = self.inertialTensor()
        valvec = LinearAlgebra.eigenvectors(I)
        res = []
        for i in range(3):
            res.append(valvec[0][i])
        res.sort()
        return res

    def createSymMol(self):
        """ Create a molecule for the symmetry module."""
        
        symmol = symdet.Molecule()
        
        for atom in self.atom:
            symmol.addAtom( atom.name, atom.coord, atom.seqno ) # check seqno

        return symmol

    def updateMolFromSym(self, symmol):
        """ Update the ccp1gui coordinate definitions from a symmetry adapted
            molecule. We use the import_geometry method of the Zmatrix class to
            preserve the Zmatrix definitions, which requries us to copy the molecule
            update the coordinates of the copy and then call the import_geometry function
            using the copy.
        """

        atomlist = symmol.export()
        atomlist.sort()

        # Use try/except to trap the fact that import_geometry doesn't work for mixed
        # Zmatrix/Cartesian yet
        try:
            copymol = copy.deepcopy( self )
            for atom in copymol.atom:
                index = atom.get_index()
                atom.coord = atomlist[ index ][1]
                atom.zorc = 'c' 
                self.import_geometry( copymol )
                
        except ImportGeometryError:
            # Can't import so just update the coordinates and ignore the Zmatrix definitions
            for atom in self.atom:
                index = atom.get_index()
                atom.coord = atomlist[ index ][1]
                atom.zorc = 'c'

    def getSymmetry( self , thresh = None ):
        """ Return a string with the symmetry of the molecule. """

        if not len( self.atom ) > 1:
            print "Error in getSymmetry! Molecule has no atoms"
            return None

        if thresh:
            symdet.thresh = thresh

        self.toStandardOrientation()
        eigval = self.getMomentsOfInertia()
        symmol = self.createSymMol()
        group = symmol.getGroup( symdet.tightCartesian, eigval )
        generators = group.generators()
        label = group.label( gen=generators)
        return label, generators

        
    def Symmetrise( self, thresh = None ):
        """  Update the molecule to the closest symmetry. """

        if thresh:
            symdet.thresh = thresh

        self.toStandardOrientation()
        eigval = self.getMomentsOfInertia()
        symmol = self.createSymMol()
        symmol.symmetrize( symdet.tightCartesian, eigval )
        self.updateMolFromSym( symmol )
        #self.toStandardOrientation()

    def get_atom_charge(self,index,tag):
        for (t,values) in self.charge_sets:
            print 't,tag',t,tag
            if t == tag:
                return values[index]
        return None


class ZAtom(Atom):
    """Storage of internal and cartesian coordinates for a single atom
    zorc  - is this z(internal) or c(cartesian)
    {r,theta,phi,x,y,z}_var - references to variables
    {r,theta,phi,x,y,z}_sign - sign multipliers
    """
    def __init__(self):
        apply(Atom.__init__, (self,))
        self.i1 = None
        self.i2 = None
        self.i3 = None

# not sure at the moment which is correct
        self.conn = []
#        self.conn = None

        self.r = 0.0
        self.theta = 0.0
        self.phi = 0.0

        self.r_sign =1.0
        self.theta_sign = 1.0
        self.phi_sign = 1.0

        self.x_sign = 1.0
        self.y_sign = 1.0
        self.z_sign = 1.0
        self.ok  = 1

        self.r_var = None
        self.theta_var = None
        self.phi_var = None
        self.x_var = None
        self.y_var = None
        self.z_var = None
        self.seq_no = 999
        self.zorc = 'c'
        self.coord = [0.0,0.0,0.0]


    def __repr__(self):
        return 'zatom ' + str(self.get_index()) + ' '+self.name + str(self.coord)
    def __str__(self):
        return 'zatom ' + str(self.get_index()) + ' '+self.name
        
    def set_symbol(self,symbol):
        self.symbol = symbol
        
    def set_name(self,name):
        self.name = name

class ZmatrixSequence(Zmatrix):
    def __init__(self,**kw):
        Zmatrix.__init__(self,**kw)
        self.frames=[]
        self.title="Sequence of Structures"
        self.current_frame=0

class Zfragment(Zmatrix):
    """Class for holding bits of molecules with internal coordinate information
    """
    def __init__(self, **kw):
        apply(Zmatrix.__init__, (self,), kw)
        self.is_frag = 1

    def add(self,sym,i1,i2,i3,r,theta,phi):
        z = ZAtom()
        z.zorc = 'z'
        z.name=sym
        z.symbol = string.capitalize(z.name)

        self.atom.append(z)
        if i1 > 0:
            z.i1=self.atom[i1-1]
        else:
            z.i1 = None
            z.i1x = i1

        if i2 > 0:
            z.i2=self.atom[i2-1]
        else:
            z.i2 = None
            z.i2x = i2

        if i3 > 0:
            z.i3=self.atom[i3-1]
        else:
            z.i3 = None
            z.i3x = i3

        z.r = r
        z.theta = theta
        z.phi = phi

class ZVar:
    """Holds a single z-matrix variable or constant"""
    def __init__(self):
        self.name = 'xxx'
        self.value = '0.0'
        self.type = 'distance'
        self.constant=0

    def __str__(self):
        if self.constant:
            return 'const '+str(self.name)+' '+str(self.value)
        else:
            return 'var '+str(self.name)+' '+str(self.value)

#
# -1         The attaching atom
# -2 and -3  Two other atoms, both connected to -1
# distance, angle and torsion will all depend on attachment,
# defaults are for attaching to an sp3 centre in a staggered conf
#

###from zmatrix import Zfragment

fragment_lib = {}

f = Zfragment(title="methyl group")
f.add('C',-1,-2,-3,1.4,109.4,120.0)
f.add('H', 1,-1,-2,1.0,109.4, 60.0)
f.add('H', 1,-1, 2,1.0,109.4,120.0)
f.add('H', 1,-1, 2,1.0,109.4,240.0)
fragment_lib['Me'] = f

f = Zfragment(title="ethyl group")
f.add('C',-1,-2,-3,1.4,109.4,120.0)
f.add('C', 1,-1,-2,1.4,109.4, 60.0)
f.add('H', 1,-1, 2,1.0,109.4,120.0)
f.add('H', 1,-1, 2,1.0,109.4,240.0)
f.add('H', 2, 1, 3,1.0,109.4, 60.0)
f.add('H', 2, 1, 3,1.0,109.4,180.0)
f.add('H', 2, 1, 3,1.0,109.4,300.0)
fragment_lib['Et'] = f

f = Zfragment(title="propyl group")
f.add('C',-1,-2,-3,1.4,109.4,120.0)
f.add('C', 1,-1,-2,1.4,109.4, 60.0)
f.add('C', 2, 1,-1,1.4,109.4,180.0)
f.add('H', 1,-1, 2,1.0,109.4,120.0)
f.add('H', 1,-1, 2,1.0,109.4,240.0)
f.add('H', 2, 1, 3,1.0,109.4,120.0)
f.add('H', 2, 1, 3,1.0,109.4,240.0)
f.add('H', 3, 2, 1,1.0,109.4, 60.0)
f.add('H', 3, 2, 1,1.0,109.4,180.0)
f.add('H', 3, 2, 1,1.0,109.4,300.0)
fragment_lib['Pr'] = f


f = Zfragment(title="iso-propyl group")
f.add('C',-1,-2,-3,1.4,109.4,120.0)
f.add('C', 1,-1,-2,1.4,109.4, 60.0)
f.add('C', 1,-1, 2,1.4,109.4,120.0)
f.add('H', 1,-1, 2,1.0,109.4,240.0)
f.add('H', 2, 1, 3,1.0,109.4, 60.0)
f.add('H', 2, 1, 3,1.0,109.4,180.0)
f.add('H', 2, 1, 3,1.0,109.4,300.0)
f.add('H', 3, 1, 2,1.0,109.4, 60.0)
f.add('H', 3, 1, 2,1.0,109.4,180.0)
f.add('H', 3, 1, 2,1.0,109.4,300.0)
fragment_lib['i-Pr'] = f


f = Zfragment(title="n-butyl group")
f.add('C',-1,-2,-3,1.4,109.4,120.0)
f.add('C', 1,-1,-2,1.4,109.4, 60.0)
f.add('C', 2, 1,-1,1.4,109.4,180.0)
f.add('C', 3, 2, 1,1.4,109.4,180.0)
f.add('H', 1,-1, 2,1.0,109.4,120.0)
f.add('H', 1,-1, 2,1.0,109.4,240.0)
f.add('H', 2, 1, 3,1.0,109.4,120.0)
f.add('H', 2, 1, 3,1.0,109.4,240.0)
f.add('H', 3, 2, 1,1.0,109.4, 60.0)
f.add('H', 3, 2, 1,1.0,109.4,300.0)
f.add('H', 4, 3, 2,1.0,109.4, 60.0)
f.add('H', 4, 3, 2,1.0,109.4,300.0)
f.add('H', 4, 3, 2,1.0,109.4,180.0)
fragment_lib['Bu'] = f

f = Zfragment(title="iso-butyl group")
f.add('C',-1,-2,-3,1.4,109.4,120.0)
f.add('C', 1,-1,-2,1.4,109.4, 60.0)
f.add('C', 1,-1, 2,1.4,109.4,120.0)
f.add('C', 2, 1, 3,1.4,109.4,180.0)
f.add('H', 1,-1, 2,1.0,109.4,240.0)
f.add('H', 2, 1, 3,1.0,109.4, 60.0)
f.add('H', 2, 1, 3,1.0,109.4,300.0)
f.add('H', 3, 1, 2,1.0,109.4, 60.0)
f.add('H', 3, 1, 2,1.0,109.4,180.0)
f.add('H', 3, 1, 2,1.0,109.4,300.0)
f.add('H', 4, 2, 1,1.0,109.4, 60.0)
f.add('H', 4, 2, 1,1.0,109.4,180.0)
f.add('H', 4, 2, 1,1.0,109.4,300.0)
fragment_lib['i-Bu'] = f

f = Zfragment(title="t-but group")
f.add('C',-1,-2,-3,1.4,109.4,120.0)
f.add('C', 1,-1,-2,1.4,109.4, 60.0)
f.add('C', 1,-1, 2,1.4,109.4,120.0)
f.add('C', 1,-1, 2,1.4,109.4,240.0)
f.add('H', 2, 1, 3,1.0,109.4, 60.0)
f.add('H', 2, 1, 3,1.0,109.4,180.0)
f.add('H', 2, 1, 3,1.0,109.4,300.0)
f.add('H', 3, 1, 2,1.0,109.4, 60.0)
f.add('H', 3, 1, 2,1.0,109.4,180.0)
f.add('H', 3, 1, 2,1.0,109.4,300.0)
f.add('H', 4, 1, 2,1.0,109.4, 60.0)
f.add('H', 4, 1, 2,1.0,109.4,180.0)
f.add('H', 4, 1, 2,1.0,109.4,300.0)
fragment_lib['t-Bu'] = f

f = Zfragment(title="carbonyl group")
f.add('C',-1,-2,-3,1.4,109.4,120.0)
f.add('x', 1,-1,-2,1.0, 90.0,  0.0)
f.add('o', 1, 2,-1,1.2, 90.0,180.0)
fragment_lib['CO'] = f

f = Zfragment(title="phenyl group")
f.add('C',-1,-2,-3,1.4,120.0,120.0)
f.add('C', 1,-1,-2,1.4,120.0,  0.0)
f.add('C', 1,-1,-2,1.4,120.0,180.0)
f.add('C', 2, 1,-1,1.4,120.0,180.0)
f.add('C', 3, 1,-1,1.4,120.0,180.0)
f.add('C', 4, 2, 1,1.4,120.0,  0.0)
f.add('H', 2, 1, 3,1.0,120.0,180.0)
f.add('H', 3, 1, 2,1.0,120.0,180.0)
f.add('H', 4, 2, 1,1.0,120.0,180.0)
f.add('H', 5, 3, 1,1.0,120.0,180.0)
f.add('H', 6, 4, 2,1.0,120.0,180.0)
fragment_lib['Ph'] = f

f = Zfragment(title="eta Cp")
f.add('x',-1,-2,-3,1.5,120.0,120.0)
f.add('C', 1,-1,-2,1.3, 90.0,  0.0)
f.add('C', 1,-1, 2,1.3, 90.0, 72.0)
f.add('C', 1,-1, 2,1.3, 90.0,144.0)
f.add('C', 1,-1, 2,1.3, 90.0,216.0)
f.add('C', 1,-1, 2,1.3, 90.0,288.0)
f.add('x', 2, 1,-1,1.0, 90.0,180.0)
f.add('x', 3, 1,-1,1.0, 90.0,180.0)
f.add('x', 4, 1,-1,1.0, 90.0,180.0)
f.add('x', 5, 1,-1,1.0, 90.0,180.0)
f.add('x', 6, 1,-1,1.0, 90.0,180.0)
f.add('H', 2, 7, 1,1.0, 90.0,180.0)
f.add('H', 3, 8, 1,1.0, 90.0,180.0)
f.add('H', 4, 9, 1,1.0, 90.0,180.0)
f.add('H', 5,10, 1,1.0, 90.0,180.0)
f.add('H', 6,11, 1,1.0, 90.0,180.0)
fragment_lib['eta Cp'] = f

f = Zfragment(title="eta Bz")
f.add('x',-1,-2,-3,1.5,120.0,120.0)
f.add('C', 1,-1,-2,1.3, 90.0,  0.0)
f.add('C', 1,-1, 2,1.3, 90.0, 60.0)
f.add('C', 1,-1, 2,1.3, 90.0,120.0)
f.add('C', 1,-1, 2,1.3, 90.0,180.0)
f.add('C', 1,-1, 2,1.3, 90.0,240.0)
f.add('C', 1,-1, 2,1.3, 90.0,300.0)
f.add('x', 2, 1,-1,1.0, 90.0,180.0)
f.add('x', 3, 1,-1,1.0, 90.0,180.0)
f.add('x', 4, 1,-1,1.0, 90.0,180.0)
f.add('x', 5, 1,-1,1.0, 90.0,180.0)
f.add('x', 6, 1,-1,1.0, 90.0,180.0)
f.add('x', 7, 1,-1,1.0, 90.0,180.0)
f.add('H', 2, 8, 1,1.0, 90.0,180.0)
f.add('H', 3, 9, 1,1.0, 90.0,180.0)
f.add('H', 4,10, 1,1.0, 90.0,180.0)
f.add('H', 5,11, 1,1.0, 90.0,180.0)
f.add('H', 6,12, 1,1.0, 90.0,180.0)
f.add('H', 7,13, 1,1.0, 90.0,180.0)
fragment_lib['eta Bz'] = f

f = Zfragment(title="eta Ethylene")
f.add('x',-1,-2,-3,1.5,120.0,120.0)
f.add('C', 1,-1,-2,0.65, 90.0,  0.0)
f.add('C', 1,-1, 2,0.65, 90.0,180.0)
f.add('x', 2, 1,-1,1.0, 90.0,180.0)
f.add('x', 3, 1,-1,1.0, 90.0,180.0)
f.add('H', 2, 3,-1,1.0,120.0, 90.0)
f.add('H', 2, 3,-1,1.0,120.0,270.0)
f.add('H', 3, 2,-1,1.0,120.0, 90.0)
f.add('H', 3, 2,-1,1.0,120.0,270.0)
fragment_lib['eta Ethylene'] = f


init_x="""
        coordinates angstrom
     C        0.000000        0.000000        0.000000  
    x1        0.000000        0.000000        1.000000  
    x2        0.943223        0.000000       -0.332161  
    x3       -0.471611       -0.816855       -0.332161  
    x4       -0.471611        0.816855       -0.332161
"""



if __name__ == "__main__":

    from interfaces.filepunch import PunchReader
    from viewer.paths import gui_path

    if 0:
        model=Zmatrix(file=gui_path+"/examples/feco5.zmt")
        model.list()
    
    if 0:
        # test fragment addition
        model2 = Zmatrix(list=init_x.split('\n'),debug=1)
        model2.connect()
        model2.add_fragment(model2.atom[1],'Me')
        
    if 1:
        # debug import geometry
        model1=Zmatrix(file=gui_path+"/old.zmt",debug=0)
        print "###### LIST1 #########"
        model1.list()
        
        model2 = Zmatrix(file=gui_path+"/new.zmt",debug=0)
        print "###### LIST2 #########"
        model2.list()

        model1.import_geometry(model2,update_constants=0)
        print "###### LIST1 #########"
        model1.list()
        
