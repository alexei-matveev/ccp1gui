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
"""MM specialisations for Calc and CalcEd classes
(these are mostly empty)
"""

from calc    import *
from calced  import *

class MMCalc(Calc):
    """Molecular mechanics specifics to Calc class"""

    def __init__(self,program="untitled",title="untitled"):
        Calc.__init__(self,program,title)

    def ReadOutput(self,file):
        output = file.readlines()
        self.set_output("log_file",output)

class MMCalcEd(CalcEd):
    """Molecular mechanics specifics to CalcEd class"""
    def __init__(self,root,calc,graph,**kw):
        """Initialise a MM calculation editor
        First initialise the base class and then do our own stuff.
        """
        apply(CalcEd.__init__, (self,root,calc,graph), kw)
        self.CreateViewMenu(self.menu)
