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
"""The Z-Matrix Editor toplevel widget

This tool can be used to manipulate coordinates
(both internal,cartesian and mixed).
"""
#
# a few more changes to make,
#
# arrow keys to move up and down
#
#

import exceptions 
import string
import chempy
import pickle
import copy
import sys
import re

import Pmw
from Tkinter import *
import tkFileDialog

from chempy.cpv import *
from objects.zmatrix import *

from viewer.initialisetk import initialiseTk
from viewer.paths import gui_path
import viewer.help
trans = string.maketrans('a','a')

class ZME(Pmw.MegaToplevel):
    """A toplevel window containing a z-matrix editor widget
    
    constructor options
    
    parent      n/a    root window Tk
    
    Functions to call to 
    reload_func               when a new structure is to be pulled in
    update_func               when a change made in the editor
                              needs to be propogated to the main window
    import_selection_func     when a selection ""
    export_selection_func ... when an atom is clicked to propogate selection
    handle_next_pick_func ... unused (will be for responding to pick events)
    in a more specific way
    on_exit=None
    v_key=0
    model=None
    list_final_coords=0
    """
    
    appname         = 'Coordinates'
    appversion      = '0.02'
    copyright       = 'CLRC Daresbury Laboratory'
    contactweb      = 'http://www.cse.clrc.ac.uk/qcg/ccp1gui'
    contactemail    = 'p.sherwood@dl.ac.uk'

    frameWidth       = 500
    frameHeight      = 630
    if sys.platform == 'mac':
       pass
    elif sys.platform[:3] == 'win':
       frameWidth       = 720
       frameHeight      = 500 
    elif sys.platform[:5] == 'linux':
       pass
    else:
       pass

    padx         = 1
    pady         = 1
    balloonhelp  = 1
    busyCursor = 'watch'

    def __init__(self, parent, 
                 reload_func=None,
                 update_func=None,
                 import_selection_func=None,
                 export_selection_func=None,
                 handle_next_pick_func=None,
                 on_exit=None,
                 v_key=0,
                 model=None,
                 list_final_coords=0,
                 **kw):

        optiondefs = (
            ('padx',         1,               Pmw.INITOPT),
            ('pady',         1,               Pmw.INITOPT))

        self.defineoptions(kw, optiondefs)

        initialiseTk(parent)

        # Initialise base class (after defining options).
        Pmw.MegaToplevel.__init__(self, parent)
        self.parent = parent
        self.title(self.appname)
        self.geometry('%dx%d+0+0' % (self.frameWidth, self.frameHeight))

        self.dialogresult = ""
        self.query = Pmw.MessageDialog(self.interior(),
                                       title = "Warning", iconpos='w', icon_bitmap='warning',
                                       buttons = ("Yes",),
                                       command = self._QueryResult)
        self.query.withdraw()

        self.pad = ' '
                                      
        # Optional molecule visualiser (see visualiser.py)
        #self.visualiser = visualiser

        self.reload_func  = reload_func
        self.update_func  = update_func
        self.on_exit      = on_exit

        # this function (if present) enables the selection in the widget
        # to be visible in the viewer
        self.export_selection_func = export_selection_func

        # this function (if present) enables the selection in the widget
        # to be visible in the viewer
        self.import_selection_func = import_selection_func

        # this function (if present) enables the zmatrix editor
        # to catch pick events
        # zme will call this when an atom ID is needed, passing a
        # handler for the pick

        # SO FAR UNUSED
        self.handle_next_pick_func = handle_next_pick_func

        # When window is closed object will survive
        ######obsolete
        ######self.userdeletefunc(lambda s=self: s.withdraw())

        self.varmenu = Menu(self.interior())
        self.varmenu.add_command(label="Remove Variable Reference",
                                 underline=0, command=self._editvar)
        self.varmenu['tearoff'] = 0

        self.v_key = v_key
        self.natoms=0
        self.atom_sel = []
        self.var_sel = []
        self.end_selected = 0
        self.end_var_selected = 0

        self.last_var = -1
      
        self.trash = []
        self.clipboard = []
        self.debug = 0
        self.recalc = 1
        # create variables like t5
        self.var_name_scheme = 0
        # create variables like t5432
        # self.var_name_scheme = 1
        self.list_final_coords = list_final_coords
      
        if kw.has_key("filename"):
            self.filename = kw["filename"]
        else:
            self.filename = "./"

        self.sel_height    = 15
        self.varsel_height = 8
        self.text_height   = 8

        if sys.platform == 'mac':
            pass
        elif sys.platform[:3] == 'win':
            self.sel_height = 10
            self.varsel_height = 5
            self.text_height   = 5
            pass
        elif sys.platform[:5] == 'linux':
            pass
        else:
            pass

        # create the interface
        self._createInterface()

        # these are used to check if any edit has happened
        self.old_sym = ' '
        self.old_r = ''
        self.old_i1 = ''
        self.old_theta = ''
        self.old_i2 = ''
        self.old_phi = ''
        self.old_i3 = ''
        self.old_conn = ''
        self.old_x = ''
        self.old_y = ''
        self.old_z = ''
        self.old_name = ''
        self.old_value = ''
        self.old_keys = ''

        self.model = model

        if not self.model:
            self.Reload()
        else:
            self._load_atom_sel()

        self._load_var_sel()

        # initialise the selection and editor
        self.active_atom = 0
        self.sel.select_set(0)
        self._store_atom_selection()
        self._update_atom_editor()
        self._update_atom_selection()
        self._export_atom_selection()
        self.build_help_dialog()

        #Associate widget with its helpfile
        viewer.help.sethelp(self,'Edit Coords')

    def get_mol(self):
        """ simply return a reference to the current coordinate
            object
        """
        return self.model

    def _StoreResult(self,option):
        """Store the name of the pressed button and destroy the 
           dialog box."""
        self.result.set(option)
        self.dialog.destroy()

    def _QueryResult(self,result):
        """Pmw silliness, need to get the result of a query. 
        Have to have a routine to store the result and remove the 
        window (sigh)."""
        print 'QueryResult',result
        self.dialogresult = result
        self.query.deactivate()

    def _createInterface(self):
        self._createBalloon()
        self._createAboutBox()
        self._createMenuBar()
        self.createMenuBar()
        self._build()

    def _createMenuBar(self):
        self.menuBar = self.createcomponent('menubar', (), None,
                                            Pmw.MenuBar,
                                            (self._hull,),
                                            # hull_relief=RAISED,
                                            # hull_borderwidth=0,
                                            balloon=self.balloon())

        self.menuBar.pack(fill=X)
        self.menuBar.addmenu('Help', 'About %s' % self.appname, side='right')
        self.menuBar.addmenu('File', 'File Input/Output')
        self.menuBar.addmenu('Edit', 'Atom and Variable')
        self.menuBar.addmenu('Convert', 'Z-matrix/cartesian conversion')
        self.menuBar.addmenu('Calculate', 'Generate Cartesians')

    def _createBalloon(self):
        # Create the balloon help manager for the frame.
        # Create the manager for the balloon help
        self._balloon = self.createcomponent('balloon', (), None,
                                              Pmw.Balloon, (self._hull,))
    def balloon(self):
        return self._balloon

    def _createAboutBox(self):
        Pmw.aboutversion(self.appversion)
        Pmw.aboutcopyright(self.copyright)
        Pmw.aboutcontact(
          'For more information, browse to: %s\n or send email to: %s' %\
                   (self.contactweb, self.contactemail))
        self.about = Pmw.AboutDialog(self._hull, 
                              applicationname=self.appname)
        self.about.withdraw()
        return None

    def showAbout(self):
        # Create the dialog to display about and contact information.
        self.about.activate(geometry='centerscreenfirst')
        # self.about.show()
        # self.about.focus_set()

    def createMenuBar(self):
        self.menuBar.addmenuitem('File', 'command',
                                 'Save coordinates to a file', 
                                 label=self.pad + 'Save Zmatrix', command = self.save_to_file)

        self.menuBar.addmenuitem('File', 'command',
                                 'Load coordinates from a file', 
                                 label=self.pad+'Load Zmatrix', command = self.load_from_file)

        self.menuBar.addmenuitem('File', 'command',
                                 'Finish Editing this Z-matrix', 
                                 label=self.pad+'Close', command = self.Quit)

        self.menuBar.addmenuitem('Help', 'command',
                                 'Get information on application', 
                                 label=self.pad+'About', command = self.showAbout)

        self.toggleBalloonVar = IntVar()
        self.toggleBalloonVar.set(1)
        #      self.setting = Setting()
        self.menuBar.addmenuitem('Help', 'separator', '')

        self.menuBar.addmenuitem('Help', 'checkbutton',
                                 'Toggle balloon help',
                                 label='Balloon help',
                                 variable = self.toggleBalloonVar,
                                 command=self.toggleBalloon)

        self.menuBar.addmenuitem('Help', 'command',
                                 'Z-matrix documentation',
                                 label='Documentation',
                                 command=self.doc)

##       self.menuBar.addmenuitem('File', 'command', 'Open structure file.',
##                         label=self.pad+'Open...',
##                         command=self.file_open)

        if self.reload_func:
            self.menuBar.addmenuitem('File', 'command',
                                     'Replace current coordinates with those in the molecular graphics program',
                                     label=self.pad+'Reload from Graphics Window',
                                     command=self.Reload)

        self.menuBar.addmenuitem('Edit', 'command', 'Select All Atoms',
                                 label=self.pad+'Select All Atoms',
                                 command=self._select_all_atoms)

        self.menuBar.addmenuitem('Edit', 'command', 'Insert a new atom before selection',
                                 label=self.pad+'Insert Atom',
                                 command=self._insert_atom)

        self.menuBar.addmenuitem('Edit', 'command', 'Copy selected Atoms to clipboard',
                                 label=self.pad+'Copy Atoms',
                                 command=self.atom_copy)

        self.menuBar.addmenuitem('Edit', 'command', 'Move selected Atoms to clipboard',
                                 label=self.pad+'Cut Atoms',
                                 command=self.atom_cut)

        self.menuBar.addmenuitem('Edit', 'command', 'Paste Atoms from clipboard',
                                 label=self.pad+'Paste Atoms',
                                 command=self.atom_paste)

        self.menuBar.addmenuitem('Edit', 'command', 'Move selected Atoms to clipboard',
                          label=self.pad+'Delete Atoms',
                          command=self.delete_atoms)

        self.menuBar.addmenuitem('Edit', 'command', 'Complete inversion of atom order',
                          label=self.pad+'Invert Order',
                          command=self.invert_order)


        self.menuBar.addmenuitem('Edit', 'command', 'Create variable for r/x coordinate',
                          label=self.pad+'r,x -> var',
                          command=self._create_var1)
        self.menuBar.addmenuitem('Edit', 'command', 'Create variable for theta/y coordinate',
                          label=self.pad+'theta,y -> var',
                          command=self._create_var2)
        self.menuBar.addmenuitem('Edit', 'command', 'Create variable for phi/z coordinate',
                          label=self.pad+'phi,z -> var',
                          command=self._create_var3)

        self.menuBar.addmenuitem('Edit', 'command', 'Create variable for all coordinates',
                          label=self.pad+'all -> var',
                          command=self._create_var123)

##        self.menuBar.addmenuitem('Edit', 'separator', '')

        self.menuBar.addmenuitem('Edit', 'command', 'Hybridise sp3',
                          label=self.pad+'=>sp3',
                          command=lambda s = self: s._hyb('sp3'))

        self.menuBar.addmenuitem('Edit', 'separator', '')

##        self.menuBar.addmenuitem('Edit', 'command', 'Add Methyl',
##                          label=self.pad+'Add Methyl',
##                          command=lambda s = self: s._add_frag('Me'))

##        self.menuBar.addmenuitem('Edit', 'command', 'Add Ethyl',
##                          label=self.pad+'Add Ethyl',
##                          command=lambda s = self: s._add_frag('Et'))

        self.menuBar.addmenuitem('Edit', 'separator', '')

        self.menuBar.addmenuitem('Edit', 'command', 'Select All Variables',
                                 label=self.pad+'Select All Variables',
                                 command=self._select_all_variables)

        self.menuBar.addmenuitem('Edit', 'command', 'Delete Variables',
                                 label=self.pad+'Delete Variables',
                                 command=self._delete_variables)

        self.menuBar.addmenuitem('Edit', 'command', 'Switch variables to constants and vice versa',
                                 label=self.pad+'Toggle Variable/Constant',
                                 command=self._toggle_constants)

#        self.menuBar.addmenuitem('Convert', 'command', 'Re-order based on connectivity',
#                                 label='Reorder Atoms',
#                                 command = self.reorder)      

        self.menuBar.addmenuitem('Convert', 'command', 'Autogenerate a full Z-matrix',
                                 label='Autoz',
                                 command = self.autoz)

        self.menuBar.addmenuitem('Convert', 'command', 'Convert selected atoms to Z-matrix',
                                 label='Convert Selection to Z-matrix',
                                 command = self._convert_to_zmatrix)

        self.menuBar.addmenuitem('Convert', 'command', 'Convert selected atoms to Cartesian',
                                 label='Convert Selection to Cartesian',
                                 command = self._convert_to_cartesian)

        self.toggleReCalcVar = IntVar()
        self.toggleReCalcVar.set(1)

        self.menuBar.addmenuitem('Calculate', 'checkbutton',
                                 'Recompute coordinates while editing ',
                                 label=self.pad+'Auto Recalc',
                                 variable = self.toggleReCalcVar,
                                 command = self.toggleReCalc)

        self.menuBar.addmenuitem('Calculate', 'command', 'Recompute Coordinates',
                                 label='Recompute Now',
                                 command = self.recalculate)

        #self.menuBar.addmenuitem('Calculate', 'command', 'Recompute Only Selected Atoms',
        #label='Recompute Selected',
        #command = self._computeCoordinates)

    def destroy(self):
        self.Quit()
    
    def Quit(self,**kw):
        """Close this window"""
        if self.on_exit:
            self.on_exit()
        apply(Pmw.MegaToplevel.destroy,(self,), **kw)

    def doc(self):

        dialog = self.help_dialog
        dialog.configure(text_state = 'normal')
        dialog.delete('1.0','end')
        fp = open(gui_path+'/doc/ccp1gui.zme.txt')
        txt = fp.readlines()
        fp.close()
        for l in txt:
            dialog.insert('end',l)
        dialog.configure(label_text = 'ZME Help')
        dialog.configure(text_state = 'disabled')
        dialog.show()

    def build_help_dialog(self):
        dialog = Pmw.TextDialog(self.parent.master,
                                scrolledtext_labelpos = 'n',
                                title = 'Help',
                                defaultbutton = 0,
                                label_text = '')
        dialog.withdraw()
        self.help_dialog  = dialog


    def file_open(self):
        pass
   
    def toggleBalloon(self):
        # from abstractapp
        if self.toggleBalloonVar.get():
            self._balloon.configure(state = 'both')
        else:
            self._balloon.configure(state = 'status')

    def toggleReCalc(self):
        if self.toggleReCalcVar.get():
            self.recalc = 1
        else:
            self.recalc = 0

    def _build(self):
        """This builds the main body of the widget, by splitting it into a number
        of frames and laying the various tools out in those frames.

        """
      
        interior = self.interior()
        #Create the 'upper' frame to hold the coordinate data
        self.coordframe = self.createcomponent('coordframe', (), None, Frame,
                                              (interior,), height=12, width=500)

        #Create the 'lower' frame to hold information on the variables and display
        #error messages relating to the z-matrix
        self.varframe = self.createcomponent('varframe', (), None, Frame,
                                             (interior,), height=7, width=500)
        
        self.coordframe.pack(side='top',fill='both',expand=1)
        self.varframe.pack(side='top',fill='x',expand=0)
        self.topframe = self.createcomponent('topframe', (), None, Frame,
                                           (self.coordframe,),)
        if self.list_final_coords:
            t = 'Coordinate Input                         |            Results\n' + \
               '   i      Sym   i1      x/r    i2    y/theta  i3     z/phi           x            y            z   connections'
        else:
            t = '   i      Sym   i1      x/r    i2    y/theta  i3     z/phi   connections'
         
        self.topframe.label =  self.createcomponent('topCoordLabel', (), None,
                                                    Label,
                                                    (self.topframe,),
                                                    font='Courier 10',
                                                    text=t)

        self.topframe.label.pack(side='left',expand=0,fill='none')
        self.topframe.pack(side='top',expand=0,fill='x')

        # Main atom selection/display widet
        self.sel = self.createcomponent('selector', (), None,
                                        Pmw.ScrolledListBox,
                                        (self.coordframe,),
                                        listbox_selectmode='extended',
                                        listbox_font='Courier 10',
                                        listbox_height=self.sel_height,
                                        selectioncommand=self._click_atom)
                                        

        self.line =         self.createcomponent('frame', (), None,Frame,(self.coordframe,), height=10, width=300 )



        self.no_line = self.createcomponent('nolineframe', (), None, Pmw.Group,
                                           (self.line),
                                           tag_text='No ' ) 

        self.mix_line = self.createcomponent('mixlineframe', (), None, Pmw.Group,
        (self.line),
                                           tag_text='No ' ) 

        self.no_line.pad =   self.createcomponent('nopad', (), None, Label,(self.no_line.interior(),),width=6)
        self.mix_line.pad =   self.createcomponent('mixpad', (), None, Label,(self.mix_line.interior(),),width=6)
        self.no_line.pad.pack()
        self.mix_line.pad.pack()

        #self.z_line =       self.createcomponent('zlineframe', (), None,Frame,(self.line,), )

        self.z_line = self.createcomponent('zlineframe', (), None, Pmw.Group,
                                           (self.line),
                                           tag_text='Enter Z-Matrix values' ) #Change to Pmw.Group

        self.z_line.pad =   self.createcomponent('zpad', (), None, Label,(self.z_line.interior(),),width=6)
        self.z_line.sym =   self.createcomponent('zname', (), None, Entry,(self.z_line.interior(),), justify='right',width=6)
        self.z_line.i1 =    self.createcomponent('i1', (), None, Entry,(self.z_line.interior(),),width=4)
        self.z_line.r =     self.createcomponent('r', (), None, Entry,(self.z_line.interior(),),width=10)
        self.z_line.i2 =    self.createcomponent('i2', (), None, Entry, (self.z_line.interior(),), width=4)
        self.z_line.theta = self.createcomponent('theta', (), None,Entry,(self.z_line.interior(),),width=10)
        self.z_line.i3 =    self.createcomponent('i3', (), None,Entry,(self.z_line.interior(),),width=4)
        self.z_line.phi =   self.createcomponent('phi', (), None, Entry,(self.z_line.interior(),), width=10)
        self.z_line.conn =  self.createcomponent('zconn', (), None, Entry, (self.z_line.interior(),),width=20)

        self.z_line.pad.pack(side='left')
        self.z_line.sym.pack(side='left')
        self.z_line.i1.pack(side='left')
        self.z_line.r.pack(side='left')
        self.z_line.i2.pack(side='left')
        self.z_line.theta.pack(side='left')
        self.z_line.i3.pack(side='left')
        self.z_line.phi.pack(side='left')
        self.z_line.conn.pack(side='left')

        self.z_line.sym.bind('<Return>',self._copy_atom_to_sel2)
        self.z_line.i1.bind('<Return>',self._copy_atom_to_sel2)
        self.z_line.r.bind('<Return>',self._copy_atom_to_sel2)
        self.z_line.r.bind('<Button-3>',self._rvarmenu)
        self.z_line.i2.bind('<Return>',self._copy_atom_to_sel2)
        self.z_line.theta.bind('<Return>',self._copy_atom_to_sel2)
        self.z_line.theta.bind('<Button-3>',self._thetavarmenu)
        self.z_line.i3.bind('<Return>',self._copy_atom_to_sel2)
        self.z_line.phi.bind('<Return>',self._copy_atom_to_sel2)
        self.z_line.conn.bind('<Return>',self._copy_atom_to_sel2)

        self.z_line.i1.bind('<Button-2>', lambda event, s=self, i=1 : s._get_graph_selection(i))
        self.z_line.i2.bind('<Button-2>', lambda event, s=self, i=2 : s._get_graph_selection(i))
        self.z_line.i3.bind('<Button-2>', lambda event, s=self, i=3 : s._get_graph_selection(i))

        self.z_line.phi.bind('<Button-3>',self._phivarmenu)

        #self.z_line.to_c.configure(command=self._to_c)

        self.c_line = self.createcomponent('clineframe', (), None, Pmw.Group,
                                           (self.line),
                                           tag_text='Enter coordinate values' )

        self.c_line.pad = self.createcomponent('cpad', (), None,
                                               Label,
                                               (self.c_line.interior()),
                                               width=6)

        self.c_line.sym = self.createcomponent('cname', (), None,
                                               Entry,
                                               (self.c_line.interior(),),
                                               justify='right',width=6)

        self.c_line.x = self.createcomponent('cx', (), None,
                                             Entry,
                                             (self.c_line.interior(),),
                                             width=15)

        self.c_line.y = self.createcomponent('cy', (), None,
                                             Entry,
                                             (self.c_line.interior(),),
                                             width=15)
        self.c_line.z = self.createcomponent('cz', (), None,
                                             Entry,
                                             (self.c_line.interior(),),
                                             width=15)

        self.c_line.conn = self.createcomponent('cconn', (), None,
                                                Entry,
                                                (self.c_line.interior(),),
                                                width=20)
        self.c_line.pad.pack(side='left', pady = 5)
        self.c_line.sym.pack(side='left', pady = 5)
        self.c_line.x.pack(side='left', pady = 5)
        self.c_line.y.pack(side='left', pady = 5)
        self.c_line.z.pack(side='left', pady = 5)
        self.c_line.conn.pack(side='left', pady = 5)

        self.c_line.sym.bind('<Return>',self._copy_atom_to_sel2)
        self.c_line.x.bind('<Return>',self._copy_atom_to_sel2)
        self.c_line.y.bind('<Return>',self._copy_atom_to_sel2)
        self.c_line.z.bind('<Return>',self._copy_atom_to_sel2)
        self.c_line.conn.bind('<Return>',self._copy_atom_to_sel2)

        #divide the lower region into two halfs (variable editor on left, diagnostic window on right)
        self.llframe = self.createcomponent('llframe', (), None, Frame,(self.varframe,))
        self.lrframe = self.createcomponent('lrframe', (), None, Frame, (self.varframe,))

        self.llframe.pack(side='left',expand=0,fill='x')
        self.lrframe.pack(side='right',expand=0,fill='x')

        #Create label for the error field
        self.lrmidframe = self.createcomponent('lrmidframe', (), None, Frame,(self.lrframe,))
        self.lrmidframe.label =  self.createcomponent('lrmidCoordLabel', (), None,Label,
                                                   (self.lrmidframe,),
                                                   text='Error output')
        #Create text widget for errror output
        self.errbox = self.createcomponent('text', (), None, Pmw.ScrolledText,(self.lrframe,),
                                           text_height=self.text_height)
 
        #Create label for Variables box
        self.midframe = self.createcomponent('midframe', (), None, Frame,(self.llframe,))
        self.midframe.label =  self.createcomponent('midCoordLabel', (), None,Label,
                                                   (self.midframe,),
                                                   text='Variables')

        # Variable selection/display widget
        self.varsel = self.createcomponent('varselector', (), None,
                                           Pmw.ScrolledListBox,
                                           (self.llframe,),
                                           listbox_selectmode='extended',
                                           listbox_width=40,
                                           listbox_height=self.varsel_height,
                                           selectioncommand=self._click_var)

        self.v_line = self.createcomponent('vlineframe', (), None, Frame,(self.llframe,), height=10, width=300 )

        self.v_line.name = self.createcomponent('name', (), None,
                                                Entry,
                                                (self.v_line,),
                                                width=8)

        self.v_line.value = self.createcomponent('value', (), None,
                                                 Entry,
                                                 (self.v_line,),
                                                 width=18)
        if self.v_key:
            self.v_line.keywords = self.createcomponent('keywords', (), None,
                                                        Entry,
                                                        (self.v_line,),
                                                        width=18)
        self.v_line.name.pack(side='left')
        self.v_line.value.pack(side='left')
        if self.v_key:
            self.v_line.keywords.pack(side='left')

        self.v_line.name.bind('<Return>',self._copy_var_to_sel2)
        self.v_line.value.bind('<Return>',self._copy_var_to_sel2)
        if self.v_key:
            self.v_line.keywords.bind('<Return>',self._copy_var_to_sel2)

        self.sel.pack(fill='both',expand=1,padx = 5, pady = 5)

        self.c_line.pack(side='left',expand=0,fill='none')
        self.line.pack(fill='x',expand=0)

        self.midframe.pack(side='top',expand=0,fill='x')
        self.midframe.label.pack(side='left',expand=0,fill='none')

        self.lrmidframe.pack(side='top',expand=0,fill='x')
        self.lrmidframe.label.pack(side='left',expand=0,fill='none')

        self.errbox.pack(fill='x',expand=0, padx = 5, pady = 5)
        self.varsel.pack(fill='x',expand=0,padx = 5, pady = 5)
        self.v_line.pack(expand=0,fill='x')

        #
        # Code associated with Atom selection and editing
        #     

    def _printselection(self):
        """ Print the current atom selection
        """   
        print 'selection is ', self.sel.curselection()
        sels = self.sel.getcurselection()
        atom = int(self.sel.curselection()[0])
        print 'picked record', atom, 'sels is ',sels, type(sels), len(sels)

    def _load_atom_sel(self):
        """ Load the atom selection box from the structure
        This involves a complete reload (overkill really)
        It should leave the selection unchanged
        """
        cursel = self.sel.curselection()
        if self.debug:
            print '_load_atom_sel (selection is', cursel,')'

        self.sel.delete(0,'end')
        i = 0
        for i in range(len(self.model.atom)):
            txt = self.model.output_atom_full(self.model.atom[i])
            self.sel.insert(i, txt)
        self.sel.insert(i+1, '[End]')

        # selats = []
        # for t in cursel:
        #     self.sel.select_set(t)
        #     try:
        #         i = int(t)
        #         selats.append(self.model.atom[i])
        #     except:
        #         pass
        # this is a bit pointless
        # Actually it is dangerous as the export may not
        # be valid yet (e.g. update_core has not been run)
        #if self.export_selection_func:
        #   self.export_selection_func(self.model, selats)

    def update_selection_from_graph(self):
        """ Set the selection of atoms in the z-matrix editor to match
        the GUI window
        """
        if self.import_selection_func:
            sel = self.import_selection_func(self.model)
            if self.debug:
                print 'import_selection_func returns',sel
            self.sel.select_clear(0,AtEnd())
            for a in sel:
                i = a.get_index()
                self.sel.select_set(i,i)

        self._store_atom_selection()
        self._update_atom_editor()

    def _get_graph_selection(self,box):
        """ Get the selection atom from the GUI window"""
        if self.import_selection_func:
            sel = self.import_selection_func(self.model)
            if box == 1:
                self.z_line.i1.insert(0,str(sel[0].get_index()+1))
            elif box == 2:
                self.z_line.i2.insert(0,str(sel[0].get_index()+1))
            if box == 3:
                self.z_line.i3.insert(0,str(sel[0].get_index()+1))
        return 'break'

    def _copy_atom_to_sel(self,atom):
        """Output an single atom to the selection widget
        Note that this deletes the selection
        """
        if self.debug:
            print '_copy_atom_to_sel ', atom

        if atom == -1:
            print 'warning _copy_atom_to_sel called incorrectly!!!'
            return

        txt = self.model.output_atom_full(self.model.atom[atom])
        self.sel.delete(atom,atom)
        self.sel.insert(atom, txt)

    def _copy_atom_to_sel2(self,junk):
        """Save edits when return is hit in a widget
        """
        if self.debug:
            print '_copy_atom_to_sel2'
        if self._save_edits():
            print 'running update'
            self._update()

    def _update_atom_editor(self):
        """ When a single atom record is selected, update the editing
        widgets with the relevant fields
        when multiple atoms of the same type are selected, leave the
        boxes blank
        for mixed z-matrix and cartesian selections no widgets are shown
        """
        if self.debug:
            print '_update_atom_editor atom_sel=', self.atom_sel

        self.z_line.forget()
        self.c_line.forget()
        self.no_line.forget()
        self.mix_line.forget()

        type = ' '
        mix=0
        for i in self.atom_sel:
            a = self.model.atom[i]
            if type == ' ':
                type = a.zorc
            if type != a.zorc:
                mix=1

        if mix:
            self.mix_line.pack()
            return

        self.active_atom = None        
        if len(self.atom_sel) == 0:
            self.no_line.pack()
            return
        elif len(self.atom_sel) == 1:
            a = self.model.atom[self.atom_sel[0]]
            self.active_atom = self.atom_sel[0]
        else:
            a = None

            
        if type == 'z':
            self.z_line.sym.delete(0,'end')

            txt = 'Edit Z-matrix coords for :'
            for ii in self.atom_sel:
                txt = txt + ' ' + str(ii+1)
            self.z_line.configure(tag_text="%s" % txt)

            if a:
                #self.z_line.pad.configure(text="%d" % (a.get_index()+1))
                #txt = str(a.symbol)
                txt = str(a.name)
            else:
                self.z_line.pad.configure(text="")
                txt=''

            self.old_sym = txt
            self.z_line.sym.insert(0,txt)

            self.z_line.i1.delete(0,'end')
            self.z_line.r.delete(0,'end')
            self.old_r = ''
            self.old_i1 = ''
            if a and i > 0 :
                if a.i1:
                    txt = str(a.i1.get_index()+1)
                    self.z_line.i1.insert(0,txt)
                    self.old_i1 = txt

                if a.r_var == None:
                    txt = str(a.r)
                else:
                    txt = a.r_var.name
                self.z_line.r.insert(0,txt)
                self.old_r = txt

            self.z_line.i2.delete(0,'end')
            self.z_line.theta.delete(0,'end')

            self.old_i2 = ''
            self.old_theta = ''
            if a and i > 1 :
                if a.i2:
                    txt = str(a.i2.get_index()+1)
                    self.z_line.i2.insert(0,txt)
                    self.old_i2 = txt

                if a.theta_var == None:
                    txt = str(a.theta)
                else:
                    txt = a.theta_var.name            
                self.z_line.theta.insert(0,txt)
                self.old_theta = txt

            self.z_line.i3.delete(0,'end')
            self.z_line.phi.delete(0,'end')

            self.old_i3 = ''
            self.old_phi = ''
            if a and i > 2 :
                if a.i3:
                    txt = str(a.i3.get_index()+1)
                    self.z_line.i3.insert(0,txt)
                    self.old_i3 = txt

                if a.phi_var == None:
                    txt = str(a.phi)
                else:
                    txt = a.phi_var.name
                self.z_line.phi.insert(0,txt)
                self.old_phi = txt

            self.z_line.conn.delete(0,'end')
            self.old_conn = ''
            if a:
                txt = ''
                for b in a.conn:
                    txt = txt + '%d ' % (b.get_index() + 1) 
                self.z_line.conn.insert(0,txt)
                self.old_conn = txt

            self.z_line.pack(side='left',expand=0,fill='none')

        else:

            self.c_line.sym.delete(0,'end')
            self.c_line.x.delete(0,'end')
            self.c_line.y.delete(0,'end')
            self.c_line.z.delete(0,'end')
            self.c_line.conn.delete(0,'end')
            self.c_line.pad.configure(text="")
            self.old_sym = ''
            self.old_x = ''
            self.old_y = ''
            self.old_z = ''
            self.old_conn = ''

            txt = 'Edit Cartesian coords for :'
            for ii in self.atom_sel:
                txt = txt + ' ' + str(ii+1)
            self.c_line.configure(tag_text="%s" % txt)

            if a:
                self.c_line.pad.configure(text="%d" % (a.get_index()+1 ))
                #txt = str(a.symbol)
                txt = str(a.name)
                self.c_line.sym.insert(0,txt)
                self.old_sym = txt

                if a.x_var == None:
                    txt = str(a.coord[0])
                else:
                    txt = a.x_var.name         
                self.c_line.x.insert(0,txt)
                self.old_x = txt

                if a.y_var == None:
                    txt = str(a.coord[1])
                else:
                    txt = a.y_var.name
                self.c_line.y.insert(0,txt)
                self.old_y = txt

                if a.z_var == None:
                    txt = str(a.coord[2])
                else:
                    txt = a.z_var.name
                self.c_line.z.insert(0,txt)
                self.old_z = txt

                txt = ''
                for b in a.conn:
                    txt = txt + '%d ' % (b.get_index() + 1) 
                self.c_line.conn.insert(0,txt)
                self.old_conn = txt

            self.c_line.pack(side='left',expand=0,fill='none')

    def _save_edits(self):
        """ Copy data from the editing widgets to the molecule object
        Does not include any calculation yet
        All selected atoms are modified but blank widgets are
        ignored (this should be the case for multiple selections)
        """

        self.logerr('')
        #####self._store_atom_selection()

        if self.debug:
            print 'ZME._save_edits selection=',self.atom_sel

        type=' '
        for i in self.atom_sel:
            a = self.model.atom[i]
            if type == ' ':
                type = a.zorc
            if type != a.zorc:
                self.warn("Internal Error _save_edits: mixed Z-matrix and cartesian atoms selected")
                return

        targets=self.atom_sel
        #
        #  ???? Not sure about this
        #  should be at least one atom chosen here from last _click_atom
        #if len(targets) == 0:
        #    if self.active_atom is not None:
        #        targets = [self.active_atom]

        change = 0
        try:
            update_editor = 0
            for i in targets:
                a = self.model.atom[i]

                if a.zorc == 'z':

                    recomp_r     = 0
                    recomp_theta = 0
                    recomp_phi   = 0

                    txt = self.z_line.sym.get()
                    if txt != self.old_sym:
                        if self.debug:
                            print '  sym changed from',self.old_sym,'to', txt
                        change = 1
                        if len(string.split(txt)) != 0:
                            a.name = txt
                            #a.symbol = txt
                            a.symbol = string.translate(a.name,trans,string.digits)
                            a.symbol = string.capitalize(a.symbol)

                    if i > 0:
                        txt = self.z_line.i1.get()
                        if txt != self.old_i1:
                            if self.debug:
                                print '  i1 changed from',self.old_i1,'to',txt
                            change = 1
                            if len(string.split(txt)) != 0:
                                try:
                                    i1 = int(txt)
                                except ValueError, e:
                                    print 'raising non int'
                                    raise BadInput, "non integer for i1"
                                if i == 0:
                                    a.i1 = None
                                else:
                                    try:
                                        a.i1 = self.model.atom[i1 - 1]
                                    except IndexError, e:
                                        raise BadInput, "invalid value for i1"
                                    #
                                    # replace variable if not symbolic
                                    # -- this is tricky as it is hard to make sure that variables
                                    # are set to sensible values, plus the result will
                                    # be over-ridden by the theta field if we are not careful
                                    # for now it is assumed that it can be blanked out
                                    #
                                    
                                    #  !!!!! Paul test
                                    if a.r_var == None or 1:
                                        recomp_r = 1
                                        if i > 1:
                                            recomp_theta = 1
                                        if i > 2:
                                            recomp_phi = 1

                        txt = self.z_line.r.get()
                        if txt != self.old_r:
                            change=1
                            if self.debug:
                                print '  r changed'
                            recomp_r = 0
                            if len(string.split(txt)) != 0:
                                try:
                                    a.r = float(txt)
                                    a.r_var = None
                                except ValueError, e:
                                    a.r_var, a.r_sign = self.model.find_var_or_create(txt,a.r,'d')
                                    a.r = a.r_var.value

                    if i > 1:
                        txt = self.z_line.i2.get()
                        if txt != self.old_i2:
                            change=1
                            if self.debug:
                                print '  i2 changed from',self.old_i2,'to',txt

                            if len(string.split(txt)) != 0:
                                try:
                                    i2 = int(txt)
                                except ValueError, e:
                                    raise BadInput, "non integer for i2"

                                if i == 0:
                                    a.i2 = None
                                else:
                                    try:
                                        a.i2 = self.model.atom[i2 - 1]
                                    except IndexError, e:
                                        raise BadInput, "invalid value for i2"
                                    # replace variable if not symbolic

                                    #  !!!!! Paul test
                                    if a.theta_var == None or 1:
                                        recomp_theta = 1
                                        if i > 2:
                                            recomp_phi = 1

                        txt = self.z_line.theta.get()
                        if txt != self.old_theta:
                            change=1
                            if self.debug:
                                print '  theta changed'

                            recomp_theta = 0
                            if len(string.split(txt)) != 0:
                                try:
                                    a.theta = float(txt)
                                    a.theta_var = None
                                except ValueError, e:
                                    a.theta_var,  a.theta_sign = self.model.find_var_or_create(txt,a.theta,'a')
                                    a.theta = a.theta_var.value

                    if i > 2:
                        txt = self.z_line.i3.get()
                        if txt != self.old_i3:
                            change=1
                            if self.debug:
                                print '  i3 changed'

                            if len(string.split(txt)) != 0:
                                try:
                                    i3 = int(txt)
                                except ValueError, e:
                                    raise BadInput, "non integer for i3"
                                if i == 0:
                                    a.i3 = None
                                else:
                                    try:
                                        a.i3 = self.model.atom[i3 - 1]
                                    except IndexError, e:
                                        raise BadInput, "invalid value for i3"
                                    # replace variable if not symbolic

                                    #  !!!!! Paul test
                                    if a.phi_var == None or 1:
                                        recomp_phi = 1

                        txt = self.z_line.phi.get()
                        if txt != self.old_phi:
                            if self.debug:
                                print '  phi changed'

                            change=1
                            recomp_phi = 0
                            if len(string.split(txt)) != 0:
                                try:
                                    a.phi = float(txt)
                                    a.phi_var = None
                                except ValueError, e:
                                    a.phi_var, a.phi_sign = self.model.find_var_or_create(txt,a.phi,'a')
                                    if  a.phi_var == None:
                                        raise BadInput, "bad variable name"
                                    a.phi = a.phi_var.value


                    if recomp_r and a.i1:
                        if self.debug:
                            print '   recompute r'
                        a.r = distance(a.coord,a.i1.coord)

                        # !!!!! paul need to check if the variable is shared

                        if a.r_var:
                            a.r_var.value = a.r*a.r_sign
                    if recomp_theta and a.i1 and a.i2:
                        if self.debug:
                            print '   recompute theta'
                        a.theta = self.model.get_angle(a,a.i1,a.i2)

                        # !!!!! paul need to check if the variable is shared

                        if a.theta_var:
                            a.theta_var.value = a.theta*a.theta_sign
                    if recomp_phi and a.i1 and a.i2 and a.i3:
                        if self.debug:
                            print '   recompute phi'
                        try:
                            a.phi = self.model.get_dihedral(a,a.i1,a.i2,a.i3)
                        except ZeroDivisionError:
                            self.logerr('arithmetic error in dihedral on atom: %d' % (i+1))

                        # !!!!! paul need to check if the variable is shared

                        if a.phi_var:
                            a.phi_var.value = a.phi*a.phi_sign

                    # if the path has changed, update the widgets
                    if recomp_phi:
                        update_editor = 1

                else:
                    txt = self.c_line.sym.get()
                    if txt != self.old_sym:
                        change = 1
                        if len(string.split(txt)) != 0:
                            a.name = txt
                            #a.symbol = txt
                            a.symbol = string.translate(a.name,trans,string.digits)
                            a.symbol = string.capitalize(a.symbol)


                    txt = self.c_line.x.get()
                    if txt != self.old_x:
                        change=1
                        if len(string.split(txt)) != 0:
                            try:
                                a.coord[0] = float(txt)
                                a.x_var = None
                            except ValueError, e:
                                a.x_var, a.x_sign = self.model.find_var_or_create(txt,a.coord[0],'d')
                                a.coord[0] = a.x_var.value

                    txt = self.c_line.y.get()
                    if txt != self.old_y:  
                        change=1
                        if len(string.split(txt)) != 0:
                            try:
                                a.coord[1] = float(txt)
                                a.y_var = None
                            except ValueError, e:
                                a.y_var, a.y_sign = self.model.find_var_or_create(txt,a.coord[1],'d')
                                a.coord[1] = a.y_var.value

                    txt = self.c_line.z.get()
                    if txt != self.old_z:
                        change=1
                        if len(string.split(txt)) != 0:
                            try:
                                a.coord[2] = float(txt)
                                a.z_var = None
                            except ValueError, e:
                                a.z_var, a.z_sign = self.model.find_var_or_create(txt,a.coord[2],'d')
                                a.coord[2] = a.z_var.value

                if a.zorc == 'z':
                    txt = self.z_line.conn.get()
                else:
                    txt = self.c_line.conn.get()

                if txt != self.old_conn:
                    change = 1
                    if self.debug:
                        print '  conn changed'

                    # clear all connections to this atom
                    for b in a.conn:
                        t = []
                        for c in b.conn:
                            if c != a:
                                t.append(c)
                        b.conn = t
                    a.conn = []

                    for t in string.split(txt):
                        i = int(t) 
                        if i < 1 or i > len(self.model.atom):
                            self.warn("connection index out of range: " + str(i))
                        else:
                            a.conn.append(self.model.atom[i-1])
                            self.model.atom[i-1].conn.append(a)

        except BadInput, e:
            self.logerr("input invalid: " + str(e.args))
            return 0

        if update_editor or change:
            # in the change case this stores the revised "old" values
            self._update_atom_editor()

        if self.debug:
            print 'ZME._save_edits done, change=',change
        self._update_atom_selection()
        return change

    def _click_atom(self):
        """ The user has clicked on an item in the listbox
        Update any text from the editing widgets and replace
        with the data for the currently selected atom
        Also stores the atom selection for later use.
        """
        self._store_atom_selection()
        if self.debug:
            print 'ZME._click_atom: selection=',self.atom_sel,'active_atom =',self.active_atom

        self._export_atom_selection()

        # Update the editing widgets
        self._update_atom_editor()

    def _deselect_all_atoms(self):
        self.sel.select_clear(0,AtEnd())
        self._export_atom_selection()
        self._update_atom_editor()
        self.active_atom = None

    def _select_all_atoms(self):
        self.sel.select_set(0,AtEnd())
        if self.export_selection_func:
            self.export_selection_func(self.model, self.model.atom)
        self.sel.select_clear(AtEnd())

    def _store_atom_selection(self):
        """Save the indices of the selected atoms"""
        self.atom_sel = []
        for s in self.sel.curselection():
            if int(s) < len(self.model.atom):
                self.atom_sel.append(int(s))
            else:
                self.end_selected = 1

    def _export_atom_selection(self):
        if self.export_selection_func:
            selats = []
            for i in self.atom_sel:
                selats.append(self.model.atom[i])
            self.export_selection_func(self.model, selats)


    def _store_var_selection(self):
        """Save the indices of the selected variables"""
        self.var_sel = []
        for s in self.varsel.curselection():
            if int(s) < len(self.model.variables):
                self.var_sel.append(int(s))
            else:
                self.end_var_selected = 1

    def _create_var1(self):
        self._store_atom_selection()
        if len(self.atom_sel):
            self.create_var1(self.atom_sel)
            self._update(selection=self.atom_sel)

    def _create_var2(self):
        self._store_atom_selection()
        if len(self.atom_sel):
            self.create_var2(self.atom_sel)
            self._update(selection=self.atom_sel)

    def _create_var3(self):
        self._store_atom_selection()
        if len(self.atom_sel):
            self.create_var3(self.atom_sel)
            self._update(selection=self.atom_sel)

    def _create_var123(self):
        self._store_atom_selection()
        if len(self.atom_sel):
            self.create_var1(self.atom_sel)
            self.create_var2(self.atom_sel)
            self.create_var3(self.atom_sel) 
            self._update(selection=self.atom_sel)

    def create_var1(self,ix):
        """ create a new variable r or x """
        for i in ix:
            a = self.model.atom[i]
            if a.zorc == 'z':
                if a.i1:
                    if self.var_name_scheme == 1:
                        txt = 'r' + str(i+1) + str(a.i1.get_index()+1)
                    else:
                        txt = 'r' + str(i+1)
                    a.r_var, a.r_sign = self.model.find_var_or_create(txt,a.r,'d')
            else:
                txt = 'x' + str(i+1)
                a.x_var, a.x_sign = self.model.find_var_or_create(txt,a.coord[0],'d')

    def create_var2(self,ix):
        for i in ix:
            a = self.model.atom[i]
            if a.zorc == 'z':
                if a.i2:
                    if self.var_name_scheme == 1:
                        txt = 'a' + str(i+1) + str(a.i1.get_index()+1)  + str(a.i2.get_index()+1)
                    else:
                        txt = 'a' + str(i+1)
                    a.theta_var, a.theta_sign = self.model.find_var_or_create(txt,a.theta,'a')
            else:
                txt = 'y' + str(i+1)
                a.y_var, a.y_sign = self.model.find_var_or_create(txt,a.coord[1],'d')

    def create_var3(self,ix):
        for i in ix:
            a = self.model.atom[i]
            if a.zorc == 'z':
                if a.i3:
                    if self.var_name_scheme == 1:
                        txt = 't' + str(i+1) + str(a.i1.get_index()+1) + \
                              str(a.i2.get_index()+1) + str(a.i3.get_index()+1)
                    else:
                        txt = 't' + str(i+1)
                    a.phi_var, a.phi_sign = self.model.find_var_or_create(txt,a.phi,'a')
            else:
                txt = 'z' + str(i+1)
                a.z_var, a.z_sign = self.model.find_var_or_create(txt,a.coord[2],'d')

    def _deselect_all_variables(self):
        self.varsel.select_clear(0,AtEnd())
        self.last_var = -1

    def _select_all_variables(self):
        self.varsel.select_set(0,AtEnd())
        self.varsel.select_clear(AtEnd())

    def _hyb(self,hyb):
        self._store_atom_selection()
        for i in self.atom_sel:
            self.model.hybridise(self.model.atom[i],hyb)

        self._update()

    def atom_cut(self):
        """ remove selected atoms and place on the clipboard"""
        self.delete_atoms(1)

    def recalculate(self):
        """Manual force of recalculation"""
        self._update(force=1)

    def atom_paste(self):
        sel = self.sel.curselection()
        if len(sel) != 1:
            self.warn('Select a single atom to define insertion point')
            return
        else:
            pt = int(sel[0])

        for a in self.model.atom:
            a.clone = None

        # Take a copy of all the atoms on the clipboard
        #
        tt = []
        for a in self.clipboard:
            t = self._copy_one_atom(a)
            tt.append(t)
            a.clone = t

        # Now update connectivity and i1,i2,i3 data to 
        # try and resolve references within the copy
        #
        # references to atoms on clipboard are not corrected yet

        for a in tt:
            if a.i1 != None and a.i1.clone != None:
                a.i1 = a.i1.clone
            if a.i2 != None and a.i2.clone != None:
                a.i2 = a.i2.clone
            if a.i3 != None and a.i3.clone != None:
                a.i3 = a.i3.clone
            t = []
            for c in a.conn:
                if c.clone == None:
                    t.append(c)
                else:
                    t.append(c.clone)
            a.conn = t

        # Produce extended lists
        self.model.atom = self.model.atom[:pt] + tt + self.model.atom[pt:]

        # to flag up any that are now invalid
        self._update()

    def _update(self,force=0,selection=None):
        """ Routine for changes involving multiple atoms
        At present all atoms are updated
        """
        if self.debug:
            print '_update recalc=',self.recalc,'force=',force

        calc = self.recalc or force
        if calc:
            self.model.reindex()
            self.model.calculate_coordinates()
            # log any errors
            txt = ""
            for er in self.model.errors:
                txt = txt + er + '\n'
            self.logerr(txt)
        
        self._load_atom_sel()
        self._load_var_sel()
        self._update_atom_editor()
        self._update_var_editor()

        if calc:
            self._update_core()

        self._update_atom_selection()
        self._export_atom_selection()

    def _update_atom_selection(self,selection=None):
        """ Select atoms in the listbox according to the atom_sel attribute
        most useful when we have reloaded the selection box and lost
        the old selection, or where we have (maybe inadvertenly)
        selected something else in the widget
        """
        for i in self.atom_sel:
            self.sel.select_set(i)

        if self.active_atom is not None:
            self.sel.see(self.active_atom)
        elif len(self.atom_sel):
            self.sel.see(self.atom_sel[0])

    def _editvar(self):
        print '_editvar unimplemented'
        pass

    def delete_atoms(self,save_to_clipboard=0):
        """ Delete the selected atoms"""
        list = []
        for s in self.sel.curselection():
            i = int(s)
            if i < len(self.model.atom):
                list.append(i)

        lrev = copy.deepcopy(list)
        lrev.sort()
        lrev.reverse()
        if self.debug:
            print 'deletion list',lrev,' save=',save_to_clipboard

        if save_to_clipboard:
            self.clear_clipboard()

        n = len(self.model.atom)
        for i in lrev:

            self.model.atom[i].seqno = -1
            if save_to_clipboard:
                self.clipboard.insert(0,self.model.atom[i])
            else:
                self.trash.append(self.model.atom[i])

            # construct revised atom list
            if i == n-1:
                self.model.atom = self.model.atom[:i]
            elif i == 0:
                self.model.atom = self.model.atom[1:]
            else:
                self.model.atom = self.model.atom[:i] + self.model.atom[i+1:]
            n = n - 1
        self.active_atom = None

        if self.debug:
            print 'trash:',self.trash
            print 'clip :',self.clipboard
        
        self._store_atom_selection()
        self._update_atom_editor()
        self._update()

    def clear_clipboard(self):
        self.trash = self.trash + self.clipboard
        self.clipboard = []
      
    def atom_copy(self):
        """Move a copy of the relevant atoms onto the clipboard"""
        list = []
        for s in self.sel.curselection():
            i = int(s)
            list.append(i)

        if self.debug:
            print 'atom_copy: ',list

        self.clear_clipboard()

        n = len(self.model.atom)

        for i in list:
            self.clipboard.append(self.model.atom[i])

    def _copy_one_atom(self,a):

        # we want to avoid creating lots of additional atoms
        # we may vary this for multiple atom copies in future

        i1 = a.i1
        i2 = a.i2
        i3 = a.i3
        conn = a.conn
        r_var = a.r_var
        theta_var = a.theta_var
        phi_var = a.phi_var

        a.i1 = None
        a.i2 = None
        a.i3 = None
        a.conn = None
        a.theta_var = None
        a.phi_var = None

        b = copy.deepcopy(a)

        a.i1 = i1
        b.i1 = i1

        a.i2 = i2
        b.i2 = i2

        a.i3 = i3
        b.i3 = i3

        a.conn = conn
        b.conn = conn

        a.r_var = r_var
        b.r_var = r_var

        a.theta_var = theta_var
        b.theta_var = theta_var

        a.phi_var = phi_var
        b.phi_var = phi_var

        return b

    def _insert_atom(self):
        """ Insert a new atom record before the most recently selected line
        and make it the current (single-atom) selection
        """

        self._store_atom_selection()

        if self.debug:
            print 'ZME._insert_atom: active_atom is  ', self.active_atom, 'selection is ',self.atom_sel
        if self.end_selected:
            pt = len(self.model.atom)
        elif len(self.atom_sel) != 1:
            self.warn('Select a single atom to define insertion point')
            return
        else:
            pt = self.atom_sel[0]
            
        ########self._save_edits()
            
        # Try and augment the model as well
        new = ZAtom()
        #
        # Problem here, when the structure is edited
        # does the name change as well ?
        #
        new.name     = 'C'
        new.symbol   = 'C'
        new.coord = [0.0, 0.0, 0.0] 
        self.model.insert_atom(pt,new)
        # start life as cartesian
        new.zorc = 'c'
        self.active_atom = pt
        self._store_atom_selection()
        self._update_atom_editor()
        self._update()

    def reorder(self):
        print 'reorder'
        pass

    def invert_order(self):

        # save anything pending in the widgets #!! paul should just be a check and warn
        self._save_edits()

        #self._store_atom_selection()

        self.model.atom.reverse()
        self.model.reindex()
        self._update()


    def _convert_to_cartesian(self):
        self._store_atom_selection()
        if len(self.atom_sel):
            self.convert_to_cartesian(self.atom_sel)
        for i in self.atom_sel:
            self._copy_atom_to_sel(i)
        self._update_atom_selection()
        self._update_atom_editor()
        
    def _convert_to_zmatrix(self):
        self._store_atom_selection()
        if len(self.atom_sel):
            self.convert_to_zmatrix(self.atom_sel)
        for i in self.atom_sel:
            self._copy_atom_to_sel(i)
            self.sel.select_set(i)
        self._update_atom_selection()
        self._update_atom_editor()

    def convert_to_cartesian(self,indices):
        """ Convert the selected atoms to Cartestan form"""
        for i in indices:
            self.model.atom[i].zorc = 'c'

    def convert_to_zmatrix(self,indices):
        """ Convert the selected atoms to z-matrix form
        BUGS.... first 3 atoms may be unsuitable to convert
            .... need to guess i1,i2,i3
        """
        self.model.reindex()
        for i in indices:
            atom = self.model.atom[i]
            print atom.i1,atom.i2,atom.i3
            if atom.i1:
                if atom.i1.get_index() > atom.get_index():
                    atom.i1 = None
            if atom.i2:
                if atom.i2.get_index() > atom.get_index():
                    atom.i2 = None
            if atom.i3:
                if atom.i3.get_index() > atom.get_index():
                    atom.i3 = None
            self.model.convert_to_z(self.model.atom[i])
            #self.model.atom[i].zorc = 'z'

    def autoz(self):
        """ Flag all atoms as z-matrix, includes re-ordering
        creates all additional data structures
        (at the moment)
        """

        # anything pending in widgets #!! paul should just be a check and warn
        self._save_edits()
        self.model.calculate_coordinates()

        try:
            self.model.autoz(testang=89)
            self._update_atom_editor()
            self._update()
        except ConversionError, e:
            self.logerr(e.args)

    def _update_var_editor(self):
        """ When a variable record is selected, update the editing widgets with 
        the relevant fields.
        It should only be called for a single atom selection
        The line to be edited is assumed to have been stored in last_var
        """
        targets = self.var_sel

        if len(targets) == 1:
            a = self.model.variables[targets[0]]
        else:
            a = None

        model = self.model

        for i in targets:
            v = model.variables[i]

            self.v_line.name.delete(0,'end')
            txt = ''
            if a:
                txt = v.name

            self.v_line.name.insert(0,txt)
            self.old_name = txt

            self.v_line.value.delete(0,'end')
            txt = ''
            if a:
                txt = str(v.value)
            self.v_line.value.insert(0,txt)
            self.old_value = txt

            if self.v_key:
                self.v_line.keywords.delete(0,'end')
                txt = ''
                if a:
                    txt = v.keys
                self.v_line.keywords.insert(0,txt)
                self.old_keys = txt

    def _click_var(self):
        """ The user has clicked on an item in the variable listbox"""
        self._store_var_selection()
        self._update_var_editor()
        # self.varsel.see(var)

    def _save_var_edits(self,targets=None):

        """ Copy data from the variable editing widgets to the
        molecule object. Does not include any calculation yet. All
        selected atoms are modified but blank widgets are ignored
        (this should be the case for multiple selections) """

        change = 0
        try:
            update_editor = 0
            for i in self.var_sel:
                txt =  self.v_line.name.get()
                if txt != self.old_name:
                    change = 1
                    self.model.variables[i].name = self.v_line.name.get()

                txt = self.v_line.value.get()
                if txt != self.old_value:
                    change = 1
                    self.model.variables[i].value = float(txt)

                if self.v_key:
                    txt = self.v_line.keywords.get()
                    if txt != self.old_keys:
                        change = 1
                        self.model.variables[i].keys = txt

        except BadInput, e:
            self.logerr("input invalid: " + e.args)
            self.last_var = -1

        if change:
            # in the change case this stores the revised "old" values
            self._update_var_editor()

        if self.debug:
            print '_save_var_edits change=',change

        return change

    def _output_var(self,v):
        """ output variable name and value (could be _str method of variable) """
        txt = '%8s %14.6f ' % (v.name, v.value)
        if self.v_key:
            txt = txt + v.keys
        return txt

    def _output_var_full(self,v):
        """ as self.output_var, except that constants are denoted"""
        txt = self._output_var(v)
        if v.constant:
            txt = txt + '    [constant]'
        return txt

    def _new_var(self,name,value,metric):
        """ Add a new variable"""
        v = self.model.new_var(name,value,metric)
        self._load_var_sel()
        return v

    def _delete_variables(self):
        list = []
        for s in self.varsel.curselection():
            i = int(s)
            if i < len(self.model.variables):
                list.append(i)

        lrev = copy.deepcopy(list)
        lrev.sort()
        lrev.reverse()
        if self.debug:
            print 'deletion list',lrev

        n = len(self.model.variables)
        for i in lrev:
            v = self.model.variables[i]
            # Remove variable references 
            for a in self.model.atom:
                if a.r_var is v:
                    a.r_var = None
                    a.r = v.value * a.r_sign
                if a.theta_var is v:
                    a.theta_var = None
                    a.theta = v.value * a.theta_sign
                if a.phi_var is v:
                    a.phi_var = None
                    a.phi = v.value * a.phi_sign
                if a.x_var is v:
                    a.x_var = None
                    a.x = v.value * a.x_sign
                if a.y_var is v:
                    a.y_var = None
                    a.y = v.value * a.y_sign
                if a.z_var is v:
                    a.z_var = None
                    a.z = v.value * a.z_sign

            if i == n-1:
                self.model.variables = self.model.variables[:i]
            elif i == 0:
                self.model.variables = self.model.variables[1:]
            else:
                self.model.variables = self.model.variables[:i] + self.model.variables[i+1:]
            n = n - 1

        self.last_var = -1
        self._deselect_all_variables()
        self._update()

    def _load_var_sel(self):
        """ load the variable selection box"""
        if self.debug:
            print '_load_var_sel'
        self.varsel.delete(0,'end')
        if not self.model:
            return
        if len(self.model.variables):
            for i in range(len(self.model.variables)):
                txt = self._output_var_full(self.model.variables[i])
                self.varsel.insert(i, txt)
        else:
            i=-1
        self.varsel.insert(i+1, '[End]')

        # !! paul should replace this will code based on var_sel setting
        if self.last_var != -1:
            self.varsel.select_set(self.last_var)
            self.varsel.see(i)
            self._update_var_editor()
      
    def _copy_var_to_sel2(self,junk):
        # Save edits
        if self._save_var_edits():
            self._update()

    # currently we are not using menus yet ... but we will need this some day
    def _rvarmenu(self,event):
        # print 'r varmenu',self, event
        sizex, sizey, x, y = getgeometry(self.root)
        #print "root geom", sizex, sizey, x, y
        #print "event x,y", event.x, event.y
        #sizex, sizey, x, y = getgeometry(event.widget)
        #print "winfo", event.widget.winfo_x(), event.widget.winfo_y()
        #print "winfo", event.widget.winfo_rootx(), event.widget.winfo_rooty()
        self.active_var = 'r'
        self.varmenu.tk_popup(event.widget.winfo_rootx()+event.x,
                              event.widget.winfo_rooty()+event.y)

    def _thetavarmenu(self,event):
        #print 'theta varmenu',self, event      
        self.active_var = 'theta'
        self.varmenu.tk_popup(event.widget.winfo_rootx()+event.x,
                              event.widget.winfo_rooty()+event.y)

    def _phivarmenu(self,event):
        #print 'phi varmenu',self, event
        self.active_var = 'theta'
        self.varmenu.tk_popup(event.widget.winfo_rootx()+event.x,
                              event.widget.winfo_rooty()+event.y)

    def _toggle_constants(self):
        """ convert all selected variables to constant (or vice versa)"""
        for s in self.varsel.curselection():
            i = int(s)
            v = self.model.variables[i]
            v.constant = not v.constant
        self._load_var_sel()

    def logerr(self,msg):
        """ Write the messages into the error box
        """
        self.errbox.delete('1.0','end')
        self.errbox.insert(AtEnd(),msg+'\n')            
        self.errbox.see('1.0')
        ###AtEnd())

    #
    #
    #  Generic stuff .......
    #
    #
    def counts(self):
        """Returns number of x atoms, z atoms, variables and constants"""
        z=0;x=0;c=0;v=0
        for a in self.model.atom:
            if a.zorc == 'z':
                z = z + 1
            else:
                x = x + 1

        for a in self.model.variables:
            if a.constant:
                c = c + 1
            else:
                v = v + 1
        return (x,z,v,c)

    def read_zmat_file(self, f):
        """ Load in a zmatrix from a file, GAMESS-UK format
        This replaces the current one, and retains the name
        """
        # This is needed by the visualiser
        try:
            title = self.model.title
        except AttributeError:
            title = 'untitled'

        self.model = Zmatrix(file=f)
        self.model.title = title
        self.model.list()
        self._update()

    def get_zmat_ordering(self):
        lst = []
        for z in self.model.my_get_internal_tuples():
            lst.append(z[0])
        return lst

    def get_zmat_ordering_back(self):
        lst = []
        for z in self.model.my_get_internal_tuples():
            lst.append(0)
        i=0
        print 'map tuples', self.model.my_get_internal_tuples()
        for z in self.model.my_get_internal_tuples():
#         print 'map',z[0], i
            lst[z[0]] = i
            i = i + 1
        return lst

    def _autoz(self):
        """ Use chempy code to define an automatic zmatrix from the
        structure, Will involve reordering the atoms
        """

        model = self.model

        if self.debug:
            print '_autoz'

        if self.debug > 2:
            model.list()
            for a in model.atom:
                print a.conn

        # Reindex the table of bonds reflecting our edits
        model.update_bonds()

        if self.debug > 2:
            print 'revised bonding:'
            model.list()

        tmpmol = copy.deepcopy(model)

        zmat = self.model.my_get_internal_tuples()

        print zmat
        
        if not zmat:
            self.warn("Autoz failed - probably linear angles or bad connectitivity")
            raise ConversionError, "autoz failure"

        if len(zmat) != len(model.atom):
            self.warn("system must be fully connected")
            raise ConversionError, "system must be fully connected"

        if self.debug > 2:
            print 'internal tuples',zmat

        i = 0
        # re-index bond table
        mapper = self.get_zmat_ordering_back()

        if len(mapper) != len(model.atom):
            print 'Problem with mapper', mapper
            self.warn("system must be fully connected")
            raise ConversionError, "system must be fully connected"

        if self.debug > 2:
            print 'mapper', mapper

        #no variables yet
        #self._load_coordinate_variables()

        # first  reordering
        for z in self.get_zmat_ordering():
            model.atom[i] = tmpmol.atom[z]
            i = i + 1

        #model.bond = []
        #tmpmol.list()
        #print len(tmpmol.bond)
        #for a in tmpmol.bond:
        #    bnd = chempy.Bond()
        #    model.bond.append(bnd)
        #    bnd.index = [mapper[a.index[0]],mapper[a.index[1]]]

        model.reindex()
        if self.debug > 2:
            print 'reordered'
            model.list()

        i=0
        warn = 0
        for a in model.atom:

            a.zorc = 'z'

            a.r = 0.0
            a.theta = 0.0
            a.phi = 0.0
            a.r_var = None
            a.theta_var = None
            a.phi_var = None

            indices = zmat[i]

            if self.debug > 2:
                print 'mapped indices'
                for jj in indices:
                    print mapper[int(jj)]

            if len(indices) > 1:
                a.i1 = model.atom[mapper[int(indices[1])]]
                a.r = distance(a.coord,a.i1.coord)
                if a.r < 0.01:
                    warn = 1
                    a.r = 0.01
            else:
                a.i1 = None

            if len(indices) > 2:
                a.i2 = model.atom[mapper[int(indices[2])]]
                try:
                    a.theta = self.model.get_angle(a,a.i1,a.i2)
                except ZeroDivisionError, e:
                    self.logerr('zero division')
                    a.theta = 0.0
                    warn = 1
            else:
                a.i2 = None

            if len(indices) > 3:
                a.i3 = model.atom[mapper[int(indices[3])]]
                try:
                    a.phi = self.model.get_dihedral(a,a.i1,a.i2,a.i3)
                except ZeroDivisionError, e:
                    self.logerr('zero division')
                    a.phi = 0.0
                    warn = 1
            else:
                a.i3 = None

            if self.debug:
                print '_autoz types', i, type(a.r), type(a.theta), type(a.phi)

            i=i+1

        if warn:
            self.warn("Some distances 0 or internal coordinates undefined")

        model.zlist()

    def warn(self,msg):
        self.query.configure(message_text = msg)
        self.query.activate()
        #self.query.show()
        if self.dialogresult == 'OK':
            self.query.withdraw()
            self.query.destroy()

    def _update_core(self):
        """Pass the newly edited structure back to the graphics viewer"""

        if self.debug:
            print '_update_core'

        # Reindex the table of bonds reflecting our edits
        # removed feb 2004 on assumption that conn entries 
        #self.model.bond = []
        #self.model.reindex()
        #for a in self.model.atom:
        #    i = a.get_index()
        #    for b in a.conn:
        #        j = b.get_index()
        #        # excludes bonds to atoms on the clipboard or trash (-ve j)
        #        if i < j:
        #            new = chempy.Bond()
        #            new.index = [ i, j ]
        #            self.model.bond.append(new)

        if self.debug > 2:
            self.model.list()

        # Update the graphics if present
        if self.update_func:
            self.update_func(self.model)

    def Reload(self):
        """ reload the structure from the graphics window.
        This is not really necessary in the tkmolview case as
        our case as the object is common to both modules??
        """

        if self.debug:
            print 'Reload'

        if not self.reload_func:
            print 'a reload_func must be provided'
            return

        self.model = self.reload_func()

        if len(self.model.atom):
            try:
                ttt = self.model.atom[0].zorc
                print 'input is already a zmatrix'

            except AttributeError:
                # Fill in the missing internal coordinate info
                print 'filling z data'
                self.model.variables = []
                for a in self.model.atom:
                    a.zorc = 'c'
                    a.r_var = None
                    a.theta_var = None
                    a.phi_var = None
                    a.x_var = None
                    a.y_var = None
                    a.z_var = None
                    a.i1 = None
                    a.i2 = None
                    a.i3 = None
                    a.r = 1.0
                    a.theta = 90.0
                    a.phi = 0.0
                    a.r_sign =1.0
                    a.theta_sign = 1.0
                    a.phi_sign = 1.0
                    a.x_sign = 1.0
                    a.y_sign = 1.0
                    a.z_sign = 1.0
                    a.ok  = 1

            self.model.reindex()

        if self.debug > 2:
            self.model.list()

        # connectivity pointers
        # now assume conn is set properly
        #for a in self.model.atom:
        #    a.conn = []
        #for b in self.model.bond:
        #    self.model.atom[b.index[0]].conn.append(self.model.atom[b.index[1]])
        #    self.model.atom[b.index[1]].conn.append(self.model.atom[b.index[0]])

        self.last_var = -1

###        self._deselect_all_atoms()
        self._load_atom_sel()
        self.update_selection_from_graph()

    def load_from_file(self):
        """ Load a zmatrix from a file"""
        calcdir = re.sub(r"[^\/\\:]*$","",self.filename)
        name    = re.split(r"[\/\\:]",self.filename)
        name    = name[len(name)-1]
        if name == "":
            #name = self.calc.get_name()+".zmt"
            name = "temp.zmt"
        ofile = tkFileDialog.askopenfilename(initialfile = name,
                                             initialdir = calcdir,
                                             filetypes=[("Zmatrix File","*.zmt"),
                                                        ("All Files","*.*")])
        if len(ofile):
            self.filename = ofile
            self.read_zmat_file(ofile)

    def save_to_file(self):
       """ Save to file, GAMESS-UK zmatrix format"""
       calcdir = re.sub(r"[^\/\\:]*$","",self.filename)
       name    = re.split(r"[\/\\:]",self.filename)
       name    = name[len(name)-1]
       if name == "":
          #name = self.calc.get_name()+".zmt"
          name = "temp.zmt"
       ofile = tkFileDialog.asksaveasfilename(initialfile = name,
                                            initialdir = calcdir,
                                            filetypes=[("Zmatrix File","*.zmt"),("All Files","*.*")])
       if len(ofile):
          self.filename = ofile
          txt = self.model.output_zmat()
          fobj = open(ofile,'w')
          for rec in txt:
             fobj.write(rec + '\n')
          fobj.close()         

#
# define some exceptions
#
class BadInput(exceptions.Exception):
    def __init__(self,args=None):
        self.args = args

# not used at present
def getgeometry(something):
    s = something.geometry()
    return map(int, re.split(s, "[x+]"))
 
if __name__ == '__main__':
    model = Zmatrix(file="../examples/feco5.zmt")
    #atom = ZAtom()
    #atom.symbol = 'C'
    #atom.name = 'C0'
    #model.insert_atom(0,atom)
    root = Tk()
    #root.withdraw()
    t = ZME(root,model=model,list_final_coords=1)
    #t.withdraw()
    #Button(command = lambda: t.show(), text = 'show').pack()
    root.mainloop()
