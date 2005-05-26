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
import sys
import string
import objects.periodic

def rmlast(s,x):
    c=' '
    if s == None:
        return ''
    print s
    l = len(s)
    while c != x:
        l=l-1
        if l == 0:
            return None
        c = s[l]
    return s[:l]

if sys.platform[:3] == 'win':
    t = rmlast(objects.periodic.__file__,'\\')
    gui_path=rmlast(t,'\\')
    root_path=rmlast(gui_path,'\\')
    t = rmlast(string.__file__,'\\')
    python_path=rmlast(t,'\\')
elif  sys.platform[:3] == 'mac':
    gui_path=rmlast(objects.periodic.__file__,'/')
    python_path=rmlast(string.__file__,'/')
    root_path=rmlast(gui_path,'/')
else:
    t = rmlast(objects.periodic.__file__,'/')
    gui_path=rmlast(t,'/')
    root_path=rmlast(gui_path,'/')
    python_path=rmlast(string.__file__,'/')

if __name__ == "__main__":
    print 'Python',python_path
    print 'GUI   ',gui_path
    print 'Root  ',root_path
    
