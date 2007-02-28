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
import basis
#
# custom basis
# Basis sets are keyed by element
#
bas={}
ecp={}
valid_element_list=[]

def valid_elements():
    return valid_element_list

def get_ecp(element):
    try:
        return ecp[element]
    except KeyError:
        print 'No custom ECP for ',element
        return None

def get_basis(element):
    try:
        print 'get for custom',element, bas
        return bas[element]
    except KeyError:
        print 'No custom basis for ',element
        return None

def store_basis(element,basis,ecp=None):
    ''' Add an entry to the custom basis
    In this case, element need not be a real element by can be
    any unique string.
    '''

    bas[element] = basis
    if ecp:
        ecp[element] = ecp
    valid_element_list.append(element)
