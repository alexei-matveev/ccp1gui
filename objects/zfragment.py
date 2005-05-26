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
The zfragment module defines as class that holds a group of atoms
with internal coordinate definitions so that molecules can be built
up from pieces. A number of fragments are defined here also.

"""

from chempy.models import Indexed
from chempy.cpv import *
from zmatrix import *

class Zfragment(Zmatrix):
    """
    Class for holding bits of molecules with internal
    coordinate information
    """
    def __init__(self):
        apply(Zmatrix.__init__, (self,))

    def add(self,sym,i1,i2,i3,r,theta,phi):
        z = ZAtom()
        z.symbol = sym
        z.name=sym

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

        z.r = r/0.529177
        z.theta = theta
        z.phi = phi

fragment_lib = {}

methyl = Zfragment()
methyl.add('c',-1,-2,-3,1.4,120.0,90.0)
methyl.add('h', 1,-1,-2,1.0,109.4,0.0)
methyl.add('h', 1, 2,-2,1.0,109.4,120.0)
methyl.add('h', 1, 2, 3,1.0,109.4,240.0)
fragment_lib['Me'] = methyl

ethyl = Zfragment()
ethyl.add('c',-1,-2,-3,1.4,120.0, 90.0)
ethyl.add('c', 1,-1,-2,1.4,109.4, 60.0)
ethyl.add('h', 1,-1, 2,1.0,109.4,120.0)
ethyl.add('h', 1,-1, 2,1.0,109.4,240.0)
ethyl.add('h', 2, 1, 3,1.0,109.4, 60.0)
ethyl.add('h', 2, 1, 3,1.0,109.4,180.0)
ethyl.add('h', 2, 1, 3,1.0,109.4,240.0)
fragment_lib['Et'] = ethyl
