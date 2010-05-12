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
"""Manage debug output from the gui"""


import Tkinter
import traceback

widget=None
lines=0
max_lines=10

def deb(txt):
    """Output the debug text"""
    global widget
    global lines, max_lines

    txt=deb_format(txt)
    if widget:
        widget.insert(Tkinter.AtEnd(),txt+'\n')
        widget.see(Tkinter.AtEnd())
        if lines > max_lines:
            widget.delete(0)
        else:
            lines = lines + 1
    else:
        print txt

def trb():
    """Output the traceback"""
    global widget
    global lines, max_lines
    tback = traceback.extract_stack(limit=5)
    txt = ""
    for level in tback[:-1]:
        txt = txt + '>>'+ str(level[2])

    if widget:
        widget.insert(Tkinter.AtEnd(),txt)
        widget.see(Tkinter.AtEnd())
        if lines > max_lines:
            widget.delete(0)
        else:
            lines = lines + 1
    else:
        print txt

def deb_setwidget(mywidget):
    global widget
    widget=mywidget

def deb_format(itext):
    prefix="DEBUG>> "

    dtext=""
    if type(itext) is list:
        for t in itext:
            dtext=dtext+"\n"+prefix+t
    elif type(itext) is str:
        dtext=prefix+itext
    else:
        raise TypeError("deb_format: unsupported type!")

    return dtext

#if __name__=="__main__":
#    print deb_format(["hello there","I'm some text"])
