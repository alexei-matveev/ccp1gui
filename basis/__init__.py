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
"""Storage and Management of Gaussian basis sets

Still really a prototype implementation

We have one python module per library basis
not classes right now, just functions .. 
this way allows different basis sets to be
stored and implemented differently

for each basis set module must provide three functions
  valid_elements()
  get_basis(element)
  get_ecp(element)

no modules for code internal library basis sets (these
are handled by special cases .. search for keyword
currently there is a dummy module?? probably a mistake

Further developments:
types of expansions (currently we only have storage of
segmented basis sets ... need ANOs etc)

The storage of ECPs and basis sets is rather inconsistent
exponents first for basis sets, last for ECPs

"""

import basis.basismanager
import basis.sto3g
import basis.lanl2dz

import string

class AtomBasis:
    """Hold a single basis set
    A basis here means a list of shells associated
    with a z value, a basis set label, and descriptive text
    """

    def __init__(self,z=0,name='UNK',text="Unassigned Basis"):
        self.z=z
        self.text=text
        self.name=name
        self.shells=[]
        self.label='unassigned'

    def load_from_list(self,data):
        """load basis from a nested python list structure, e.g.
        [  ['S', [ 2.23100000, -0.49005890   ],
                 [ 0.47200000,  1.25426840  ] ],
           ['S', [ 0.16310000,  1.00000000  ] ],
           ['P', [ 6.29600000, -0.06356410  ],
                 [ 0.63330000,  1.01413550  ] ],
           ['P', [ 0.18190000,  1.00000000  ] ]  ]

        """
        for shell in data:
            s = BasisShell()
            self.shells.append(s)
            s.type = shell[0]
            for contr in shell[1:]:
                if len(contr) == 2:
                    s.expansion.append((float(contr[0]),float(contr[1])))
                else:
                    s.expansion.append((float(contr[0]),float(contr[1]),float(contr[2])))

    def load_from_file(self,file):
        """pull in a single atomic basis from a file
        file format:
        S 
        71.616837 0.15432897
        13.045096 0.53532814
        3.5305122 0.44463454
        L 
        2.9412494 -0.09996723 0.15591627
        0.6834831 0.39951283 0.60768372
        0.2222899 0.70011547 0.39195739
        """
        f = open(file)
        while 1:
            line = f.readline()
            if not line:
                break
            words = string.split(line)
            txt  = string.upper(words[0])
            if words[0] == 'S' or words[0] == 'P' or words[0] == 'L' \
                   or words[0] == 'D' or words[0] == 'F' or words[0] == 'G':
                s = BasisShell()
                s.type = words[0]
                self.shells.append(s)
            else:
                n = len(words)
                if n == 2:
                    s.expansion.append((float(words[0]),float(words[1])))
                else:
                    s.expansion.append((float(words[0]),float(words[1]),float(words[2])))
        f.close()

    def __str__(self):
        return self.label + ' Basis ' + self.name + ' for z= ' + str(self.z) + ', '+ str(len(self.shells)) + ' shells'
    def __repr__(self):
        return self.label + ' Basis ' + self.name + ' for z= ' + str(self.z) + ', '+ str(len(self.shells)) + ' shells'

    def list(self):
        """human readable output of the basis set"""
        print self.name, 'Z=',self.z
        for shell in self.shells:
            shell.list()

class KeywordAtomBasis(AtomBasis):
    """A Keyword basis holds metadata relating to a basis set
    which is to be taken from a code's internal library
    """
    def __str__(self):
        return self.label + ' Basis ' + self.name + ' for z= ' + str(self.z) + ', (Internal)'
    def __repr__(self):
        return self.__str__()
    def list(self):
        """human readable output of the basis set"""
        print self.label, self.name, 'Z=',self.z, '(Internal)'

class BasisShell:
    """Storage for a basis shell
    Each shell has a type (S,L,P,....G) and an expansion
    The expansion is a list structure of the form
    [ [ exp coef ] [ exp coef ] .... ]
    or for L shells
    [ [ exp coef_s coef_p ] [ exp coef_s coef_p] .... ]
    """
    def __init__(self):
        self.type='S'
        self.expansion=[]

    def __repr__(self):
        txt = ''
        for p in self.expansion:
            txt = txt + str(p) + '\n'
        return self.type + ':' + txt

    def __str__(self):
        return 'Shell type ' + self.type + ', ' + str(len(self.expansion)) + ' primitives'

    def list(self):
        print self.type
        for p in self.expansion:
            if len(p) == 2:
                print '%12.8f %8.4f' % (p[0],p[1])
            elif len(p) == 3:
                print '%12.8f %8.4f %8.4f' % (p[0],p[1],p[2])
        

class AtomECP:
    """Storage of ECP data for one element"""
    def __init__(self,z=-1,name='UNK',ncore=-1,lmax=-1):
        self.z = z
        self.lmax = lmax
        self.ncore = ncore
        self.expansion=[]
        self.name=name
        self.shells=[]
        self.label='unassigned'

    def __str__(self):
        return self.label + ' ECP ' + self.name + ' for z= ' + str(self.z) + ', '+ str(len(self.shells)) + ' terms'
    def __repr__(self):
        return self.label + ' ECP ' + self.name + ' for z= ' + str(self.z) + ', '+ str(len(self.shells)) + ' terms'
        
    def load_from_list(self,data):
        """load ecp from a nested python list structure
        structure required:

        [ [2, 10],                                   !   L_max, N_core
        [3, "f potential",                           !   L ,  Label 
        [1 ,     -10.00000000,     94.81300000 ] ,   !   rexp , coeff , exp
        [2 ,      66.27291700,    165.64400000 ] ,
        [2 ,     -28.96859500,     30.83170000 ] ,
        [2 ,     -12.86633700,     10.58410000 ] ,
        [2 ,      -1.71021700,      3.77040000 ] ] ,
        [0, "s-f potential",
        [0 ,       3.00000000,    128.83910000 ] ,
        [1 ,      12.85285100,    120.37860000 ] ,
        [2 ,     275.67239800,     63.56220000 ] ,
        [2 ,     115.67771200,     18.06950000 ] ,
        [2 ,      35.06060900,      3.81420000 ] ] ,
        [1, "p-f potential",
        [0 ,       5.00000000,    216.52630000 ] ,
        [1 ,       7.47948600,     46.57230000 ] ,
        [2 ,     613.03200000,    147.46850000 ] ,
        [2 ,     280.80068500,     48.98690000 ] ,
        [2 ,     107.87882400,     13.20960000 ] ,
        [2 ,      15.34395600,      3.18310000 ] ] ]

        """
        self.lmax = data[0][0]
        self.ncore = data[0][1]
        shells = data[1:]
        for shell in shells:
            s = EcpShell()
            s.type = shell[0]
            s.desc = shell[1]
            self.shells.append(s)
            for c in shell[2:]:
                s.expansion.append((float(c[0]),float(c[1]),float(c[2])))

    def list(self):
        """human readable output of the basis set"""
        print self.name, 'Z=',self.z,' ncore=',self.ncore,' lmax= ',self.lmax
        for shell in self.shells:
            shell.list()

class KeywordAtomECP(AtomECP):
    """Storage for ECPs to be taken from internal code libraries"""
    def __str__(self):
        return self.label + ' ECP ' + self.name + ' for z= ' + str(self.z) + ', (Internal)'
    def __repr__(self):
        return self.__str__()
    def list(self):
        """human readable output of the basis set"""
        print self.label, self.name, 'Z=',self.z, '(Internal)'

class EcpShell:
    """Storage for a component of an ECP
    Each shell has a type (l) (0,1,2), a description,  and an expansion
    The expansion is a list structure of the form
    [ [ rexp coef exp ] [ rexp coef exp ] .... ]
    rexp is the integer power of r.
    """

    def __init__(self):
        self.type='0'
        self.desc='unk'
        self.expansion=[]

    def __repr__(self):
        txt = ''
        for p in self.expansion:
            txt = txt + str(p) + '\n'
        return self.type + ':' + txt

    def __str__(self):
        return 'ECP Shell L=' + self.type + ', ' + str(len(self.expansion)) + ' primitives'

    def list(self):
        print self.type,self.desc
        for p in self.expansion:
            print '%d %12.8f %8.4f' % (p[0],p[1],p[2])
