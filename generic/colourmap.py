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
"""Implementation of colourmap. 
Most code will be associated with the particular graphics implementations
"""

class ColourMap:

    def __init__(self):
        self.title = "untitled"
        self.colours = [ (1.0, 0.0, 0.0), (0.0, 0.0, 1.0) ]
        self.low = -1
        self.high = 1
        pass

    def set_colours(self,colours):
        """ Load a list of colours into the colourmap
        """
        self.colours = colours
        pass

    def set_range(self,low,high):
        """Define the range of values"""
        self.low = low
        self.high = high
        pass

    def set_title(self,title):
        """ Define the title"""
        self.title = title

    def _build(self):
        print "_build must be overloaded"

    def build(self):
        self._build()


    def list(self):
        print 'Colourmap',self.title
        v = self.low
        n = len(self.colours)
        inc = (self.high - self.low)/(n-1)
        for i in range(n):
            print v, self.colour[i]
            v = v + inc
            
