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
"""Sample basis...STO3-G
This one has some parts (C, CL) in element specific files,
H basis is stored as a string.
"""
import basis

bas={}
def valid_elements():
    return ['h','c','cl']

def get_ecp(element):
    return None

def get_basis(element):
    if element == 'h':
        p = basis.AtomBasis(z=1,name='sto3g')
        p.load_from_list([['S' ,[3.42525091,0.15432897],[0.62391373, 0.53532814],[0.16885540,0.44463454]]])
        return p
    if element == 'c':
        p = basis.AtomBasis(z=6,name='sto3g')
        p.load_from_file('sto3g.c.txt')
        return p
    if element == 'cl':
        p = basis.AtomBasis(z=17,name='sto3g')
        p.load_from_file('sto3g.cl.txt')
        return p

    print 'sto3g get_basis failed',element,'Should be one of ',valid_elements()
