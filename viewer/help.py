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
##Binding now done in main with:
# Associate helpfile with widget
#tkmolview.help.sethelp(self.master,'Introduction','tkmolview.intro.txt')
## Bind F1 to open a help menu
#self.master.bind_all('<F1>', lambda event : tkmolview.help.helpall(event))

import Pmw
import sys,os
import string
import webbrowser
from viewer.paths import gui_path


tkmolobject=None #see get_tkmolview
helpdialog=None #see help_set_widget

global nametofile # maps names to files and urls
nametofile = {"Introduction":["index.html","viewer.intro.txt"],
"File Menu":["menus.html#FileMenu","viewer.filemenu.txt"],            
"Edit Menu":["menus.html#EditMenu","viewer.editmenu.txt"],            
"View Menu":["menus.html#ViewMenu","viewer.viewsmenu.txt"],            
"Compute Menu":["menus.html#ComputeMenu","viewer.computemenu.txt"],            
"Shell Menu":["menus.html#ShellMenu"," viewer.shellmenu.txt"],            
"Key Bindings":["menus.html#KeyBindings","viewer.keybindings.txt"],            
"Edit Coords":["menus.html#EditCoords","ccp1gui.zme.txt"],
"AdjMolView":["menus.html#AdjMolView","viewer.adjmolview.txt"],
"Debug Window":["index.html","viewer.debugwindow.txt"],
"Edit Options":["menus.html#EditOptions","viewer.editoptions.txt"],
"Python Shell":["menus.html#IdleShell","viewer.pythonshell.txt"],
"Editing Tools":["menus.html#EditTools","viewer.edittools.txt"],
 "MoleculeTab":["gamessuk_menus.html#MolTab","gamessuk.moltab.txt"],
"Theory Tab":["gamessuk_menus.html#TheoryTab","gamessuk.theorytab.txt"],
"DFT Tab":["gamessuk_menus.html#DFTTab","gamessuk.dfttab.txt"],
"Properties Tab":["gamessuk_menus.html#PropTab","gamessuk.proptab.txt"],
"Optimisation Tab":["gamessuk_menus.html#GeomoptTab","gamessuk.opttab.txt"],
"Job Tab":["gamessuk_menus.html#JobTab","gamessuk.jobtab.txt"],
"Grid Editor":["gamessuk_menus.html#editgrid","grideditor.txt"]}

global idtoname # maps widget ids to the names for lookup in nametofile
idtoname = {}

def get_tkmolview(tkmolview):
    """ Pass in the tkmolview widget so we can use its methods that manipulate
        the text dialog widget.
    """
    global tkmolobject
    global helpdialog
    tkmolobject = tkmolview
    helpdialog = tkmolobject.help_dialog

def sethelp(widget,name):
    """Associate a widget with a helpfile.
    """
    idtoname[str(widget)]=name


def helpall(event):
    """Open a browser or text file depending on the widget.
    """
    htmlfile,txtfile, helpname = widgettofiles(event)
    displayhelp(htmlfile,txtfile,helpname)

def displayhelp(htmlfile,txtfile, helpname=None):
    """Open a browser with the html help file, failing that bring up
       a dialog with the help as a text file, or as a last resort direct
       the user to the online documentation.
    """

    #This holds the title for the widget
    if not helpname:
        helpname="CCP1GUI help"
        
    if sys.platform[:3] == 'win':
        txtpath = gui_path + '\\doc\\'
        htmlpath = gui_path+ '\\doc\\html\\'
    elif  sys.platform[:3] == 'mac':
        pass
    else:
        txtpath = gui_path + '/doc/'
        htmlpath =  gui_path + '/doc/html/'

    htmlfound = None
    browserr = None

    if validpath(htmlpath+htmlfile):
        #Check for file as no way of checking with webrowser
        htmlfound = 1
        try:
            url = "file://"+htmlpath+htmlfile
            webbrowser.open_new(url)
        except webbrowser.Error, (errno,msg):
            print "Browser Error: %s (%d)\n" % (msg,errno)
            print "Using widget instead."
            browserr = 1
            
    if not htmlfound or browserr:
        print "Could not find html file: "+htmlpath+htmlfile+"\n"
        print "Trying to open text file: "+txtpath+txtfile+"\n"
        try:
            fp = open(txtpath+txtfile)
            txt = fp.read()
            fp.close()
            tkmolobject.open_help_dialog(helpname,txt)
        except Exception,args:
            print args
            msg="Sorry - help not available\n" + \
                "Check online at: http://www.cse.clrc.ac.uk/qcg/ccp1gui/index.shtml"
            print msg
            errordialog(msg)

def getfiles(helpname):
    global nametofile # maps names to files and urls
    htmlfile = nametofile[helpname][0]
    txtfile = nametofile[helpname][1]

    return htmlfile,txtfile

def widgettofiles(event):
    """Check to see if widget id matches a known widget and return the
       corresponding file. Otherwise return the default helpfile.
    """
    global idtoname
    global nametofile
    widget_id = str(event.widget)

    #Check to see if widget id matches a known widget. Otherwise
    #keep lopping off the end of the widget id until a match 
    while widget_id is not None and not idtoname.has_key(widget_id):
        widget_id = rmlast(widget_id)

    if widget_id: #ie we can identify the widget
        helpname = idtoname[widget_id]
        htmlfile = nametofile[helpname][0]
        txtfile = nametofile[helpname][1]
        
    else: #Cant identify widget
        htmlfile = "index.html"
        txtfile = "viewer.intro.txt"

    return htmlfile, txtfile, helpname

def rmlast(s):
    """Trim the last object id from a string representation of a widget
    """
    c=' '
    l = len(s)
    if l < 1:
        return None
    while c != '.':
        l=l-1
        c = s[l]
    return s[:l]

def validpath(link):
    """Get the filename from an html link and return true if we can find it
    """
    file = string.split(link,'#')[0]
    if os.path.exists(file):
        return 1
    else:
        return None

def errordialog(txt):
    global tkmolobject
    tkmolobject.error(txt)
