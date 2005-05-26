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
import pickle

class Graph:

    def __init__(self, **kw):
        self.mol = None
        self.capabilities = {}

    def get_names(self):
        pass

    def load_from_graph(self,name):
        pass

    def check_capability(self,key):
        ''' use the capabilities dictionary to indicate what
        options to provide on the visualiser menus '''

        try:
            return self.capabilities[key]
        except KeyError:
            return 0
