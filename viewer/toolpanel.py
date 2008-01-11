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
"""A Toplevel widget displaying the molecule editing tools"""

from Tkinter import *
import Pmw
import re
import viewer.help
from objects.periodic import PeriodicTable
from objects.zmatrix import fragment_lib

class EditingToolsWidget(Pmw.MegaToplevel):

    """A Toplevel displaying the molecule editing tools"""
 
    appname         = 'Editing Tool Panel'
    appversion      = '0.01'
    copyright       = 'CLRC Daresbury Laboratory'
    contactweb      = 'http://www.cse.clrc.ac.uk/Activity/CCP1GUI'
    contactemail    = 'p.sherwood@dl.ac.uk'

    # Size is not used at the moment (need to be able to grow
    # to accomodate the full periodic table)

    frameWidth       = 400
    frameHeight      = 150
    if sys.platform == 'mac':
        pass
    elif sys.platform[:3] == 'win':
        frameWidth       = 400
        frameHeight      = 150
    elif sys.platform[:5] == 'linux':
        pass
    else:
        pass

    def __init__(self, parent = None, **kw):

        # Define the megawidget options.
        optiondefs = (
	    ('command',   None,   Pmw.INITOPT),
        )
        self.defineoptions(kw, optiondefs)
        self.parent = parent

        # Initialise base class (after defining options).
        Pmw.MegaToplevel.__init__(self, parent)
 
        self.title(self.appname)
        #self.geometry('%dx%d+0+0' % (self.frameWidth, self.frameHeight))

        #Associate widget with its help file
        viewer.help.sethelp(self,"Editing Tools")
        # Create the components.
        i = self.interior()
        self.createcomponent('element-type-group',(), None,
                             Pmw.Group, i,tag_text = 'Change Element Type')
        tt =Frame(i)
        left =Frame(i)
        right =Frame(i)
        left_up =Frame(left)
        left_down =Frame(left)
        right_up =Frame(right)
        right_down =Frame(right)

        self.createcomponent('editing-group',(), None,
                             Pmw.Group, left_up,tag_text = 'Editing')
        self.createcomponent('misc2-group',(), None,
                             Pmw.Group, left_down,tag_text = 'Measure')
        self.createcomponent('hybridisation-group',(), None,
                             Pmw.Group, right_up,tag_text = 'Hybridisation')
        self.createcomponent('symmetry-group',(), None,
                             Pmw.Group,right_up,tag_text = 'Symmetry')
        self.createcomponent('fragment-group',(), None,
                             Pmw.Group,right_down,tag_text = 'Add Fragment')
        self.createcomponent('clean-group',(), None,
                             Pmw.Group,right_down,tag_text = 'Optimise ')        
        self.component('element-type-group').pack(side='top')
        tt.pack(side='top')
        left.pack(side='left')
        right.pack(side='left')

        left_up.pack(side='top')
        left_down.pack(side='top')
        right_up.pack(side='top')
        right_down.pack(side='top')
        
        self.component('editing-group').pack(side='left')
        self.component('misc2-group').pack(side='left')
        self.component('hybridisation-group').pack(side='left')
        self.component('fragment-group').pack(side='left')
        self.component('clean-group').pack(side='left')
        self.component('symmetry-group').pack(side='left')

        self.createcomponent('periodic-table',(), None,
                             PeriodicTable,
                             self.component('element-type-group').interior(),
                             command = self.setz)

        self.component('periodic-table').pack()

        # Editing tools
        self.createcomponent('editing-group-top-frame',(), None,
                             Frame,
                             self.component('editing-group').interior())
        self.component('editing-group-top-frame').pack(side='top')
        
        self.createcomponent('editing-group-bottom-frame',(), None,
                             Frame,
                             self.component('editing-group').interior())
        self.component('editing-group-bottom-frame').pack(side='top')
        
        for op in ['Del Atom','Del Bond','Add Bond','All X->H']:
            t = self.createcomponent('button-'+op,
                                     (), None,
                                     Button,
                                     self.component('editing-group-top-frame'),
                                     command = lambda s=self,z=op : s.miscop(z),
                                     text=op)
            t.pack(side='left')
            
        # Additional tools for editing bonds
        self.create_bond_tools()

        for op in ['Distance', 'Angle','Torsion']:
            t = self.createcomponent('button-'+op,
                                     (), None,
                                     Button,
                                     self.component('misc2-group').interior(),
                                     command = lambda s=self,z=op : s.measure(z),
                                     text=op)
            t.pack(side='left')


        lf = Frame(self.component('misc2-group').interior())
        t = self.createcomponent('measure-label0',
                                 (), None,
                                 Label,
                                 lf,
                                 width=14,
                                 borderwidth=0,
                                 font=("Helvetica", 9, "bold"),
                                 text=' ')
        t.pack(side='top')        
        t = self.createcomponent('measure-label',
                                 (), None,
                                 Label,
                                 lf,
                                 width=14,
                                 borderwidth=0,
                                 font=("Helvetica", 9, "bold"),
                                 text='0.00000')

        t.pack(side='top')        
        lf.pack(side='left')
        
        for hyb in ['sp','sp2','sp3','tpy','tbpy','sqpl','sqpy','oct']:
            t = self.createcomponent('button-'+hyb,
                                     (), None,
                                     Button,
                                     self.component('hybridisation-group').interior(),
                                     command = lambda s=self,z=hyb : s.sethyb(z),
                                     width=3,text=hyb)
            t.pack(side='left')

        t = self.createcomponent('fragment-button', (), None,
                                 Button,
                                 self.component('fragment-group').interior(),
                                 command=self.pickfrag,
                                 text = "Add:")
        t.pack(side='left')

        t = self.createcomponent('fragment-selector', (), None,
                                 Pmw.OptionMenu,
                                 self.component('fragment-group').interior(),
                                 items=fragment_lib.keys(),
                                 menubutton_width=10,
                                 initialitem="Me")                                 
        t.pack(side='left')

        t = self.createcomponent('clean-button', (), None,
                                 Button,
                                 self.component('clean-group').interior(),
                                 command=self.cleanfrag,
                                 text = "Optimise")
        t.pack(side='left')

        t = self.createcomponent('cleancode-selector', (), None,
                                 Pmw.OptionMenu,
                                 self.component('clean-group').interior(),
                                 items=["GAMESS-UK","MOPAC","MNDO", "UFF", "AM1 (built-in)"],
                                 menubutton_width=8,
                                 initialitem="GAMESS-UK")
########                                 command=self.change_clean_code)                                 
        t.pack(side='left')

        t = self.createcomponent('clean-opts-button', (), None,
                                 Button,
                                 self.component('clean-group').interior(),
                                 command=self.cleanopts,
                                 text = "Opts..",
                                 state = 'normal')

        t.pack(side='left')


        t = self.createcomponent('symmetry-button', (), None,
                                 Button,
                                 self.component('symmetry-group').interior(),
                                 command=self.symmetry,
                                 text = "Symm. Ops ")
        t.pack(side='left')



    def show(self,**kw):
        self.reposition(self.parent)
        apply(Pmw.MegaToplevel.show,(self,),kw)

    def reposition(self,parent):
        """Place the widget
        Try to translate the widget so it is in a convenient spot
        relative to the main window This needs to be executed after
        the widget is complete
        """

        if not parent:
            return

        #print 'TP self',self
        #print 'TP parent',parent
        # Find position of master
        #print 'toolpanel parent geom',parent.geometry()
        m = re.match('(\d+)x(\d+)\+(\d+)\+(\d+)',parent.geometry())
        try:
            msx,msy,mpx,mpy = int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4))
            print 'master geom',    msx,msy,mpx,mpy
            self.geometry("+%d+%d" % (mpx,mpy+msy+24))
        except AttributeError:
            print 'toolpanel parent geom',parent.geometry()
            print 'failed to reposition'
            

    def setz(self,value):
        """Pass the element selection to the widget command"""
        print 'Periodic Table z=',value
        if self['command']:
            self['command']('element',value)

    def sethyb(self,value):
        """Pass the hybridisation selection to the widget command"""
        print 'Hybridisation =',value
        if self['command']:
            self['command']('hybridisation',value)

    def miscop(self,value):
        """Misc Options..."""
        print 'Operation =',value
        if self['command']:
            self['command'](value,None)

    def measure(self,value):
        """Measurements"""
        print 'Measure, Operation =',value
        if self['command']:
            r = self['command'](value,None)
            if r is not None:
                (lab,result) = r
                self.component('measure-label').configure(text= ("%11.6f" %  result))
                self.component('measure-label0').configure(text=lab)

    def pickfrag(self):
        """Pass the fragment selection to the widget command"""
        sel = self.component('fragment-selector')
        frag = sel.getcurselection()
        if self['command']:
            self['command']('fragment',frag)

    def cleanfrag(self):
        sel = self.component('cleancode-selector')
        code = sel.getcurselection()
        if self['command']:
            self['command']('clean',code)

    def stopclean(self):
        if self['command']:
            self['command']('stop',None)

    def cleanopts(self):
        sel = self.component('cleancode-selector')
        code = sel.getcurselection()
        #if code == 'AM1':
        #    return None
        if self['command']:
            self['command']('cleanopts',code)

    def symmetry(self):
        print "Displaying Symmetry Widget..."
        sel = self.component('symmetry-button')
        if self['command']:
            self['command']('symmetry',None)

    def create_bond_tools(self):
        """Create the tools for editing bonds"""

        self.createcomponent('bond-tools-choose', (), None,
                             Pmw.OptionMenu,
                             self.component('editing-group-bottom-frame'),
                             labelpos='w',
                             label_text='Edit Bond:',
                             items=('Length','Rotate'),
                             command=self.__change_bedit_increment
                             )
        self.component('bond-tools-choose').pack(side='left')
        
        self.createcomponent('bond-tools-edit', (), None,
                             Pmw.Counter,
                             self.component('editing-group-bottom-frame'),
                             datatype='real',
                             increment=0.1,
                             entryfield_value=0.0,
                             entry_width=6,
                             entryfield_command=self.handle_bond_edit,
                             )
        self.component('bond-tools-edit').pack(side='left')

        self.createcomponent('bond-tools-apply', (), None,
                             Button,
                             self.component('editing-group-bottom-frame'),
                             text='Apply',
                             command=self.handle_bond_edit
                             )
        self.component('bond-tools-apply').pack(side='left')

    def __change_bedit_increment(self,select):
        """Change how we increment the bond editor depending on the whether
        we are changing the length or rotating
        """
        if select=="Length":
            self.component('bond-tools-edit').configure( increment=0.1 )
        elif select=="Rotate":
            self.component('bond-tools-edit').configure( increment=1 )
        else:
            raise AttributeError,"toolpanel.py:__change_bedit_increment, unknown option: %s" % select
        
    def handle_bond_edit(self):
        """Read the bond editing tools and call the appropriate command"""
        action=self.component('bond-tools-choose').getvalue()
        value=float(self.component('bond-tools-edit').component('entryfield').getvalue())

        if action=='Length':
            command='change_bond_length'
        elif action=='Rotate':
            command='rotate_about_bond'
        else:
            raise AttributeError,"toolpanel.py:handle_bond_edit, unknown option: %s" % action
        
        if self['command']:
            self['command'](command,value)

if __name__ == "__main__":
    root=Tk()
    vt = EditingToolsWidget(root,title='Editing Widget')
    vt.userdeletefunc(lambda: vt.withdraw())
    vt.withdraw()
    Entry().pack()
    #Button(command = lambda: vt.activate(globalMode='nograb'), text = 'show').pack()
    Button(command = lambda: vt.show(), text = 'show').pack()
    root.mainloop()
