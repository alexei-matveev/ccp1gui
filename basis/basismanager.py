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
"""Basis Manager - store basis choices
"""
import string
import basis

#python_basis_list=["sto3g","lanl2dz"]
#python_basis_list=["lanl2dz"]
python_basis_list=[]

PYTHON_LIB=0
CODE_KEYWORD=1
CUSTOM=2

DEFAULT=0
REQUESTED=1

basis_module={}

t = python_basis_list
t.append("custom")
for p in t:
    name = 'basis.'+p
    mod = __import__(name)
    components = string.split(name, '.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
        basis_module[p] = mod

class BasisManager:
    """Store information relating to basis set selections

    The BasisManager provides various utilites
        - loading basis sets from sources
        - providing data for construction of GUI elements 
        - exporting basis information for use by the code interfaces

    Implementation Notes:
    the element names as held in the basis libraries are all kept
    in lower case
    """
    def __init__(self):
        #
        # build an index of the internally available basis sets
        #
        self.debug = 0
        self.known_basis_sets=[]
        self.valid_elements={}
        self.known_keyword_basis_sets=[]
        self.keyword_valid_elements={}
        self.keyword_ecp={}
        self.default_basis=None
        self.assigned_types={}
        self.assigned_atoms={}

        # import one module per basis
        # the import statement only imports the leading component
        # so see __init__

        t = python_basis_list
        for p in t:
            self.known_basis_sets.append(p)
            self.valid_elements[p] = basis_module[p].valid_elements()

    def define_keyword_basis(self,keyword,elements,ecp=0):
        """indicate which keyword basis sets are available in the code

        keyword  the code keyword in question
        elements if provided, only basis sets that can be applied
                 to these elements will be offered
        ecp=1    a keyword to request the ECP should be provided
        """
        self.known_keyword_basis_sets.append(keyword)
        self.keyword_ecp[keyword]=ecp
        #Convert all element names to lower case
        for el in elements:
            el = string.lower(el)
        self.keyword_valid_elements[keyword]=elements

        # Import the keyword module
        name = 'basis.keyword'
        mod = __import__(name)
        basis_module[keyword] = mod

    def is_supported(self,element,basisname):
        """check if an element is supported by a given basis

        only non-keyword basis sets are searched
        returns 1 if so, 0 if not
        """
        element = string.lower(element)
        if self.debug:
            print '>> is_supported',element, basisname
        try:
            return element in self.valid_elements[basisname]
        except KeyError:
            if self.debug:
                print '>> is_supported failed with keyerror'
            return 0

    def is_keyword_supported(self,element,basisname):
        """check if an element is supported by a given keyword basis
        returns 1 if so, 0 if not
        """
        element = string.lower(element)
        if self.debug:
            print '>> is_keyword_supported',element, basisname

        try:
            itest = element in self.keyword_valid_elements[basisname]
            if self.debug:
                print '>> is_keyword_supported returns ',itest
            return itest
        except KeyError:
            if self.debug:
                print '>> is_keyword_supported failed with KeyError'
            return 0        

    def available_basis_sets(self,elements):
        """check for basis sets compatible with a given list of elements
        lists modules first, then keywords, but not custom basis sets
        ? perhaps custom is ok for those basis sets that have been entered?
        """
        if self.debug:
            print '>> available_basis_sets called:', elements

        avail=[]
        for bas in self.known_keyword_basis_sets:
            discard=0
            for el in elements:
                el = string.lower(el)
                if not el in self.keyword_valid_elements[bas]:
                    discard=1
                    break
            if not discard:
                avail.append(bas)

        for bas in self.known_basis_sets:
            # Need a more efficient implementation here!!!

            if bas == "custom":
                break
            if bas in self.known_keyword_basis_sets:
                break
            discard=0
            for el in elements:
                el = string.lower(el)
                if not el in self.valid_elements[bas]:
                    discard=1
                    break
            if not discard:
                avail.append(bas)

        if self.debug:
            print '>> available_basis_sets returns', avail

        return avail

    def get_basis(self,el,basis_name):
        """Return the basis set (class AtomBasis or KeywordAtomBasis)
        for the provided element and basis_name
        """
        el = string.lower(el)
        if self.debug:
            print '>> get_basis:',el,basis_name

        if self.is_keyword_supported(el,basis_name):
            b = basis.KeywordAtomBasis(el,name=basis_name)
            if self.debug:
                if b:
                    print '>> get_basis: found keyword basis'
                else:
                    print '>> get_basis: returning None (keyword)'
            return b
        else:
            if self.is_supported(el,basis_name):
                b = basis_module[basis_name].get_basis(el)
                if self.debug:
                    if b:
                        print '>> get_basis: found explicit basis'
                    else:
                        print '>> get_basis: returning None (explicit)'
                return b
            else:
                print '>> get_basis: failed to find basis'
                return None

    def get_ecp(self,el,basis_name):
        """Return the ECP object (class AtomECP or KeywordAtomECP)
        for the provided element and basis_name
        """
        el = string.lower(el)
        if self.is_keyword_supported(el,basis_name) and self.keyword_ecp[basis_name]:
            b = basis.KeywordAtomECP(el,name=basis_name)
            if self.debug:
                if b:
                    print '>> get_basis: found keyword ecp'
                else:
                    print '>> get_basis: returning None (keyword ecp)'
            return b
        else:
            if self.is_supported(el,basis_name):
                b = basis_module[basis_name].get_ecp(el)
                if self.debug:
                    if b:
                        print '>> get_basis: found explicit ecp'
                    else:
                        print '>> get_basis: returning None (explicit ecp)'
                return b
            else:
                return None

    def clear_assignment(self):
        """remove internal storage and restore the default assignment"""
        if self.debug:
            print '>> clear_assignment'
        self.assigned_types={}
        self.assigned_atoms={}
        self.apply_default_assignment()

    def clear_atom_assignment(self,index):
        """Remove any non-default assignment of basis sets to an atom
        (both assignments to the atom, and to the type of the atom).
        ? not clear if both should be cleared here
        """
        if self.debug:
            print '>> clear_atom_assignment'

        atom = self.molecule.atom[index]
        t = id(atom)
        try:
            del self.assigned_atoms[t]
        except KeyError:
            pass

        # Also remove any assignment that has been made by atom type
        try:
            del self.assigned_types[string.lower(atom.name)]
        except KeyError:
            pass

    def assign_default_basis(self,basisname):
        """Set the default basis.
        basisname must be a valid basis (keyword or otherwise)
        """
        if self.debug:
            print '>> assign_default_basis'

        if basis_module.has_key(basisname):
            self.default_basis=basisname
            return 0
        else:
            print 'Bad choice for default basis',basisname
            return -1            

    def assign_basis_to_label(self,atom_type,basisname,custom=None):
        """use the basisname provided to make an internal assignment
        this is a mapping between atom labels and basis strings
        """
        atom_type = string.lower(atom_type)
        
        if self.debug:
            print '>> assign_basis_to_label'

        # check that it is a valid choice 
        el = string.lower(self.get_element_from_tag(atom_type))

        if custom:
            # Apply a custom basis
            basisname = 'custom'
            # Store this, using the atom_type as the key
            basis_module['custom'].store_basis(atom_type,custom)
            keyw = CUSTOM
        else:
            # First try the internal code basis sets
            if self.is_keyword_supported(el,basisname):
                keyw=1
            else:
                if not self.is_supported(el,basisname):
                    print 'Basis '+basisname+' does not support element '+el
                    return -1
                keyw=0

        self.assigned_types[atom_type]=(el,basisname,keyw,REQUESTED)
        return 0

    def assign_basis_to_atom(self,index,basisname,custom=None):
        """make assignment to an individual atom """

        if self.debug:
            print '>> assign_basis_to_atom'

        if not self.molecule:        
            print 'need a molecule for this!'
            return

        a = self.molecule.atom[index]
        atom_type = string.lower(a.symbol)
        el = string.lower(self.get_element_from_tag(atom_type))

        print 'ix,type,el', atom_type, el

        t = id(self.molecule.atom[index])

        if custom:
            # Apply a custom basis
            basisname = 'custom'
            # Store this, using the atom id  as the key
            atype='Id' + str(t)
            basis_module['custom'].store_basis(atype,custom)
            keyw = CUSTOM
        else:
            # First try the internal code basis sets
            # hopefully id is the most robust way of assigning
            # the atoms
            if self.is_keyword_supported(el,basisname):
                keyw = CODE_KEYWORD
            else:
                if not self.is_supported(el,basisname):
                    print 'Basis '+basisname+' does not support element '+el
                    return -1
                keyw = PYTHON_LIB

        self.assigned_atoms[t]=(el,basisname,keyw,REQUESTED)

    def check_assigned_atoms(self,id):
        """Return 1 if the atom id provided has an explicit basis assignment """
        try:
            el,basisname,keyw,req = self.assigned_atoms[id]
            if self.debug:
                print '>> check_assigned_atoms returns',req
            return req
        except KeyError:
            if self.debug:
                print '>> check_assigned_atoms returns 0 (KeyError)'
            return 0

    def check_assigned_types(self,type):
        """Return 1 if the atom type name provided has an explicit basis assignment"""
        type=string.lower(type)
        try:
            el,basisname,keyw,req = self.assigned_types[type]
            if self.debug:
                print '>> check_assigned_types returns',req
            return req
        except KeyError:
            if self.debug:
                print '>> check_assigned_types returns 0 (KeyError)'
            return 0

    def apply_default_assignment(self):
        """Try and use the default basisname to make type-wise assignments
        for all types in the molecule.
        Exclude cases where atom or type assignments have already been made
        """
        if self.debug:
            print '>>apply_default_assignment', self.default_basis

        for a in self.molecule.atom:
            # obtain the corresponding element symbol
            name = string.lower(a.name)
            el = string.lower(self.get_element_from_tag(name))
            if self.debug:
                print 'Def',name, a.get_index(), el
            # check assignment by atom and name first
            t = id(a)
            if self.check_assigned_atoms(t):
                if self.debug:
                    print 'Skip assigned atom'
            elif self.check_assigned_types(name):
                if self.debug:
                    print 'Skip assigned type'
            else:
                if self.debug:
                    print 'Applying def for atom', a.get_index(), name
                # First try the internal code basis sets
                if self.is_keyword_supported(el,self.default_basis):
                    self.assigned_types[name]=(el,self.default_basis,CODE_KEYWORD,DEFAULT)
                else:
                    if not self.is_supported(el,self.default_basis):
                        if self.debug:
                            print 'Basis '+self.default_basis+' does not support element '+el
                        try:
                            del self.assigned_atoms[t]
                        except KeyError:
                            pass
                        try:
                            del self.assigned_types[name]
                        except KeyError:
                            pass
                    else:
                        self.assigned_types[name]=(el,self.default_basis,PYTHON_LIB,DEFAULT)

    def get_element_from_tag(self,atom_type):
        """Utility to extract the element symbol """
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

    def assigned_basis_sets(self):
        """ Return the a list of basis objects currently assigned by atom type
        ?? why not those assigned by atoms ??
        ?? this overlaps with output method ??
        """
        basis = []
        for type in self.assigned_types.keys():
            (el,str,keyw,isreq) = self.assigned_types[type]
            el=string.lower(el)
            b = self.get_basis(el,str)
            #         ?? may append None??
            basis.append(b)
        return basis

    def assigned_ecps(self):
        """Return a list of ecp objects
        ?? compare with previous function
        """
        basis = []
        for type in self.assigned_types.keys():
            (el,str,key,req) = self.assigned_types[type]
            el=string.lower(el)
            if str:
                b = self.get_ecp(el,str)
            else:
                b = self.get_ecp(el,self.default_basis)
            if b:
                #b.label = type
                basis.append(b)
        return basis

    def set_molecule(self,molecule):
        """Set up the structure to refer assignments to"""
        self.molecule = molecule


    def new_molecule(self):
        """The molecule has been changed, try and reflect this in the
        internal storage
         - remove definitions that are no longer relevant
         - reassign defaults
        """
        new_types = []
        for atom in self.molecule.atom:
            if not string.lower(atom.name) in new_types:
                new_types.append(string.lower(atom.name))
        for type in self.assigned_types.keys():
            type = string.lower(type)
            if not type in new_types:
                del self.assigned_types[type]
        self.apply_default_assignment()

    def basis_summary_by_atom(self):
        """Give a human readable summary of the current basis assignment"""
        if not self.molecule:
            print 'summarise_basis_by_atom: No molecule loaded'
            return ['Molecule Info Not Available']

        # convert defaults
        self.apply_default_assignment()

        summary = []
        self.molecule.reindex()
        for a in self.molecule.atom:
            #
            # First see if a specific atom assignment has been made
            #
            t = id(a)
            try:
                el,bas,keyw,req = self.assigned_atoms[t]
                key0='A,'
            except KeyError:
                bas = None

            # Now perform a look up based on the atom name
            if not bas:
                try:
                    el,bas,keyw,req = self.assigned_types[string.lower(a.name)]
                    if self.debug:
                        print 'assigned_types bas is',bas
                    key0='T,'
                except KeyError:
                    bas = None

            if bas:
                if keyw == CODE_KEYWORD:
                    key1 = 'C,'
                elif keyw == PYTHON_LIB:
                    key1 = 'P,'
                elif keyw == CUSTOM:
                    key1 = 'U,'

                if req == DEFAULT:
                    key2 = 'D'
                elif req == REQUESTED:
                    key2 = 'R'
                if self.debug:
                    summary.append( "%-3d %-4s %-8s %s%s%s" % (a.get_index()+1, a.name, bas, key0, key1, key2))
                else:
                    summary.append( "%-3d %-4s %-8s" % (a.get_index()+1, a.name, bas))
            else:
                summary.append("%-3d %-4s           Unassigned" % (a.get_index(), a.name ))

        return summary

    def summarise_basis_by_atom(self):
        print 'Summary by Atom'
        txt = self.basis_summary_by_atom()
        for t in txt:
            print t

    def output(self):
        """Output the basis set as assigned
        first the assignments by type, then by atom
        """
        result = []
        if self.debug:
            print 'output',self.assigned_types.keys()
        for type in self.assigned_types.keys():
            (el,str,keyw,isreq) = self.assigned_types[type]
            b = self.get_basis(el,str)
            print 'b',b
            if b is None:
                print 'NULL BAS'
            elif keyw == CODE_KEYWORD:
                result.append(['TYPE.KEY', type, b.name ])
            elif keyw == PYTHON_LIB or keyw == CUSTOM:
                result.append(['TYPE.EXPL', type, b ])

#        for type in self.assigned_atoms.keys():
#            (el,str,keyw,isreq) = self.assigned_atoms[type]
#            b = self.get_basis(el,str)
#            result.append(['ATOM', type, b ])

        return result
    
    def keybasis_from_type(self,type):
        """ Return the name of the keyword basis as assigned to a particular atom type
            or return none if there isn't a keyword basis assigned.
        """
        result = None
        type = string.lower( type )
        (el,str,keyw,isreq) = self.assigned_types[type]
        b = self.get_basis(el,str)
        if b is None:
            print 'No basis found for atom type: ',str(type)
            result = None
        elif keyw == CODE_KEYWORD:
            result = b.name
        elif keyw == PYTHON_LIB or keyw == CUSTOM:
            result = None

        return result

    def output_ecp(self):
        """Output the ECPs as assigned
        first the assignments by type, then by atom
        """
        result = []

        if self.debug:
            print 'output_ecp',self.assigned_types.keys()

        for type in self.assigned_types.keys():
            (el,str,keyw,isreq) = self.assigned_types[type]
            b = self.get_ecp(el,str)
            if b is None:
                if self.debug:
                    print 'output_ecp: NULL ECP'
            elif keyw == CODE_KEYWORD:
                result.append(['TYPE.KEY', type, b.name ])
            elif keyw == PYTHON_LIB or keyw == CUSTOM:
                result.append(['TYPE.EXPL', type, b ])

        if self.debug:
            print 'output_ecp keys:',self.assigned_types.keys()
            print 'output_ecp result:',result

#        for type in self.assigned_atoms.keys():
#            (el,str,keyw,isreq) = self.assigned_atoms[type]
#            b = self.get_basis(el,str)
#            result.append(['ATOM', type, b ])

        return result

        
    def list(self):
        """ diagnostic listing"""

        print 'Code Keyword Basis sets'
        for known in self.known_keyword_basis_sets:
            for e in self.keyword_valid_elements[known]:
                b = self.get_basis(e,known)
                b.list()
                if self.keyword_ecp[known]:
                    print 'ECP is included'

        print 'Python Library Basis sets'
        for known in self.known_basis_sets:
            for e in self.valid_elements[known]:
                b = self.get_basis(e,known)
                if b:
                    b.list()

if __name__ == "__main__":
    m = BasisManager()
    #
    # maybe a problem if there is a basis set which has ecps for
    # some but not all atoms
    #
    m.define_keyword_basis('sto3g',['h','he','li','b','c','n'],ecp=0)
    m.define_keyword_basis('dzp',['h','he','li','b','c','n'],ecp=0)
    m.define_keyword_basis('3-21G',['h','he','li','b','c','n'],ecp=0)
    m.define_keyword_basis('rlc',['cl','br','i'],ecp=1)
    m.list()
    print m.available_basis_sets(['h'])
    print m.available_basis_sets(['cl'])
#    m.assign_basis_to_label('h1','sto3g')
#    m.assign_basis_to_label('h2','3-21G')
#    m.assign_basis_to_label('h2','3-21G')
#    m.assign_basis_to_label('h1','rlc')
#    m.assign_basis_to_label('cl1','lanl2dz')
#    print m.assigned_basis_sets(), m.assigned_ecps()

    from ccp1gui.zmatrix import *
    model = Zmatrix()
    atom = ZAtom()
    atom.symbol = 'c'
    atom.name = 'C0'
    model.insert_atom(0,atom)
    atom = ZAtom()
    atom.symbol = 'h'
    atom.name = 'H1'
    model.insert_atom(0,atom)
    atom = ZAtom()
    atom.symbol = 'Cl'
    atom.name = 'Cl2'
    model.insert_atom(0,atom)
    model.reindex()

    model.list()
    for a in model.atom:
        print a.get_index(), a.symbol, a.name

    m.assign_default_basis('sto3g')
    m.set_molecule(model)
    m.assign_basis_to_label('h','dzp')
    m.assign_basis_to_label('cl','lanl2dz')

    #p = basis.AtomBasis(name='mybas')
    #p.load_from_list([['S' ,[3.42525091,0.15432897],[0.62391373, 0.53532814],[0.16885540,0.44463454]]])
    #m.assign_basis_to_atom(0,'mybas',custom=p)
    #m.summarise_basis_by_atom()

    print ''
    m.summarise_basis_by_atom()
    print 'OUTPUT'
    out = m.output()
    for entry in out:
        (ass_type, tag, b) = entry
        print 'entry', ass_type, tag, b
        if ass_type == 'TYPE.KEY':
            print tag, b
        if ass_type == 'TYPE.EXPL':
            print tag, b.list()

    print 'OUTPUT ECP'
    out = m.output_ecp()
    for entry in out:
        (ass_type, tag, b) = entry
        print 'entry', ass_type, tag, b
        if ass_type == 'TYPE.KEY':
            print tag, b
        if ass_type == 'TYPE.EXPL':
            print tag, b.list()
