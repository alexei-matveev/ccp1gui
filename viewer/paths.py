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
"""helper module to manage pathnames
"""

# see http://www.pythonmac.org/wiki/FAQ#head-c88c53edb2f911e57c92adf2625ca2b73aa6fc6d
import os
import sys
import __main__


version=sys.version_info #The version of python we are using

try:
    # Below accpeted way of doing things for Python > 2.2
    mainscriptdir=os.path.dirname(os.path.abspath(__main__.__file__))
except AttributeError:
    import debug
    x=os.path.abspath(debug.__file__) # Get the full path to the debug file
    mainscriptdir=os.path.dirname(x)

gui_path = os.path.split(mainscriptdir)[0]
root_path = os.path.split(gui_path)[0]
python_path = os.path.split(os.__file__)[0]

if __name__ == "__main__":
    print 'Python',python_path
    print 'GUI   ',gui_path
    print 'Root  ',root_path
    
