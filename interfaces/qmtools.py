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
#
import Pmw
import Tkinter
import re
from basis.basismanager import *
from tools import *

class BasisToolWidget(Pmw.MegaWidget):
    """PWM Megawidget implementation of the basis tool
    selector"""

    def __init__(self, parent, m, **kw):

        self.sel_height = 14
        self.sel_width =  35
        self.basis_manager = m

        # Define the megawidget options.
        optiondefs = (
            ('colors',    ('green', 'red'), None),
            ('value',     None,             Pmw.INITOPT),
            )
        self.defineoptions(kw, optiondefs)
        # Initialise base class (after defining options).
        Pmw.MegaWidget.__init__(self, parent)

        # Create the components.
        interior = self.interior()

        f1 = Tkinter.Frame(interior)
        fl = Tkinter.Frame(interior)
        fr = Tkinter.Frame(interior)
        
        # Main atom selection/display widet
        fixedFont = Pmw.logicalfont('Courier',size=12)
        self.atomdisplay_widget = self.createcomponent(
            'selector', (), None,
            Pmw.ScrolledListBox,
            (interior,),
            listbox_selectmode='extended',
            listbox_height=self.sel_height,
            listbox_width=self.sel_width,
            listbox_font=fixedFont,
            listbox_background='white',
            labelpos='nw',
            label_text='Current Basis Assignment',
            selectioncommand=self.__click_atom)

        all_avail = self.basis_manager.available_basis_sets([])

        self.assign_atom_group = self.createcomponent(
            'assignatomgroup', (), None,
            Pmw.Group,
            (interior),
            tag_text="Assign by atom")

        self.choose_default_widget = self.createcomponent(
            'default basis', (), None,
            Pmw.OptionMenu,
            (interior,),
            labelpos = 'w',
            label_text = 'Default Basis',
            command = self.__choose_default,
            items = all_avail, 
            initialitem = self.basis_manager.default_basis)

        all_avail.append("Custom")
        self.choose_assigned_widget = self.createcomponent(
            'assigned basis', (), None,
            Pmw.OptionMenu,
            (interior,),
            labelpos = 'w',
            label_text = 'Choose Basis',
            command = self.__choose_assigned,
            items = all_avail, 
            initialitem = all_avail[0])

        # Box to enter the custom basis set
        # Create the ScrolledText with headers.
        fixedFont = Pmw.logicalfont('Fixed')

        self.custom_widget = self.createcomponent(
            'custom', (), None,
             Pmw.ScrolledText,
            (interior,),
            borderframe = 1,
            labelpos = 'n',
            label_text='Custom Basis Specification',
            #columnheader = 1,
            #rowheader = 1,
            #rowcolumnheader = 1,
            usehullsize = 1,
            hull_width = 200,
            hull_height = 100,
            text_wrap='none',
            text_font = fixedFont,
            #Header_font = fixedFont,
            #Header_foreground = 'blue',
            #rowheader_width = 3,
            #rowcolumnheader_width = 3,
            text_padx = 4,
            text_pady = 4,
            #Header_padx = 4,
            #rowheader_pady = 4
            )

        self.assign_atom_widget = self.createcomponent(
            'assignatom', (), None,
            Tkinter.Button,
            (interior,),
            text = 'Assign\nAtom',
            command = self.__assign_basis_atom)

        self.assign_type_widget = self.createcomponent(
            'assigntype', (), None,
            Tkinter.Button,
            (interior,),
            text = 'Assign\nType',
            command = self.__assign_basis_type)

        self.unassign_atom_widget = self.createcomponent(
            'unassign', (), None,
            Tkinter.Button,
            (interior,),
            text = 'Clear\nAssignment',
            command = self.__unassign_basis)

        self.choose_default_widget.pack(in_=fl)

#        self.assign_atom_widget.pack(in_=f1,side='left')
        self.assign_type_widget.pack(in_=f1,side='left')
        self.unassign_atom_widget.pack(in_=f1,side='left')

        self.choose_assigned_widget.pack(in_=self.assign_atom_group.interior())
        f1.pack(in_=self.assign_atom_group.interior())
        self.assign_atom_group.pack(in_=fl)
        self.custom_widget.pack(in_=fl)

        self.atomdisplay_widget.pack(in_=fr)
        fl.pack(side='left')
        fr.pack(side='left')
        self.__refresh()
        
    def __choose_default(self,txt):
        ''' Assign default basis
        '''
        self.__refresh()

    def __choose_assigned(self,txt):
        ''' Set Assign  basis
        '''
        print '__choose_assigned', txt
        self.assigned_basis = txt
        #self.__refresh()

    def __assign_basis_type(self):
        self.__assign_basis(0)
    def __assign_basis_atom(self):
        self.__assign_basis(1)
    def __assign_basis(self,how):
        ''' Assign the chosen basis to the selected atoms
        how = 0 by type
        how = 1 by atom
        '''

        self.assigned_basis = self.choose_assigned_widget.getcurselection()
        print 'ass',self.assigned_basis

        sel = self.atomdisplay_widget.curselection()
        print 'sel',sel

        m = self.basis_manager
        if self.assigned_basis == "Custom":

            p = basis.AtomBasis(name='custom')
            # Parse the context of the text box into the required
            # list structure

            txt = self.custom_widget.get()
            #print 'raw', txt
            txt = string.strip(txt)
            txt  = string.split(txt,'\n')
            #print 'text', txt
            lst = []
            for record in txt:
                record = string.strip(record)
                # Split according to whitespace or separators
                words  = re.split(r'[\s,:;]+',record)
                if len(words) == 0 or len(record) == 0:
                    # skip blank
                    pass
                elif words[0][:1] == '#':
                    # skip comment
                    pass
                else:
                    print 'words',words
                    if words[0] == 's' or words[0] == 'S' or \
                       words[0] == 'p' or words[0] == 'P' or \
                       words[0] == 'l' or words[0] == 'L' or \
                       words[0] == 'd' or words[0] == 'D' or \
                       words[0] == 'f' or words[0] == 'F' or \
                       words[0] == 'g' or words[0] == 'G':
                           current = [words[0]]
                           lst.append(current)
                    else:
                        # Check for problems with the 
                        numerical=1
                        for each in words:
                            try:
                                junk = float(each)
                            except ValueError:
                                numerical=0
                        if numerical:
                            # Append to existing definition
                            current.append(words)
                        else:
                            # Need to replace with warning box
                            print 'Unrecognised basis entry!!: %s' % record
                            return

            print 'final list', lst
            p.load_from_list(lst)
            p.list()
            if how == 1:
                for s in sel:
                    index = int(s)
                    m.assign_basis_to_atom(index,self.assigned_basis,custom=p)
            elif how == 0:
                for s in sel:
                    index = int(s)
                    lab = self.basis_manager.molecule.atom[index].name
                    m.assign_basis_to_label(lab,self.assigned_basis,custom=p)

        else:
            if how == 1:
                for s in sel:
                    index = int(s)
                    m.assign_basis_to_atom(index,self.assigned_basis,custom=None)
            elif how == 0:
                for s in sel:
                    index = int(s)
                    lab = self.basis_manager.molecule.atom[index].name
                    m.assign_basis_to_label(lab,self.assigned_basis,custom=None)

        self.__refresh()

    def __unassign_basis(self):
        """Remove the atom assignments for those atoms selected in
        the listbox
        """
        sel = self.atomdisplay_widget.curselection()
        for s in sel:
            index = int(s)
            self.basis_manager.clear_atom_assignment(index)
        self.__refresh()

    def __click_atom(self):
        """unused, but could display more detail about the
        basis for a selected atom in another dialog
        """
        pass

    def Refresh(self):
        self.__refresh()
        
    def __refresh(self):
        """Update the listing of assigned basis sets"""
        
        self.default_basis = self.choose_default_widget.getcurselection()
        self.basis_manager.assign_default_basis(self.default_basis)
        self.basis_manager.apply_default_assignment()

        # Fill in the selection box
        self.atomdisplay_widget.delete(0,'end')
        list = self.basis_manager.basis_summary_by_atom()
        for t in list:
            self.atomdisplay_widget.insert(Tkinter.AtEnd(),t)

class BasisTool(Tool):
    """ A tool for choosing basis sets
    """
    def __init__(self,editor,basis_parameter,ecp_parameter,default_parameter,molecule=None,basis_manager=None,**kw):

        apply(Tool.__init__, (self,editor), kw)

        self.basis_parameter = basis_parameter
        self.ecp_parameter = ecp_parameter
        self.default_parameter = default_parameter

        if basis_manager:
            self.basis_manager=basis_manager
        else:
            self.basis_manager=BasisManager()

        self.initial_default = self.editor.calc.get_parameter(default_parameter)
        self.basis_manager.assign_default_basis(self.initial_default)

        if molecule:
            self.basis_manager.set_molecule(molecule)
        self.widget = BasisToolWidget(self.parent,self.basis_manager)

    def ReadWidget(self):
        bas = self.basis_manager.output()
        self.editor.calc.set_parameter(self.basis_parameter,bas)
        ecp = self.basis_manager.output_ecp()
        self.editor.calc.set_parameter(self.ecp_parameter,ecp)
        if self.debug:
            print 'readwidget',bas,ecp

    def UpdateWidget(self):
        """Update the contents of the widget based on changes
        normally would be to the value of the parameter?
        here it is changes to the molecule?
        can we incorporate both?

        We will assume that the basismanager is the accurate
        representation of the selection (in fact probably the basis
        manager should perhaps be the value of the basis parameter?)

        the job then is to refresh the widget
        """
        self.widget.Refresh()

if __name__ == '__main__':
    root = Tkinter.Tk()

    from ccp1gui.zmatrix import *
    model = Zmatrix()
    atom = ZAtom()
    atom.symbol = 'c'
    atom.name = 'C0'
    model.insert_atom(0,atom)
    atom = ZAtom()
    atom.symbol = 'h'
    atom.name = 'H1'
    model.insert_atom(0,atom)
    atom = ZAtom()
    atom.symbol = 'F'
    atom.name = 'F2'
    model.insert_atom(0,atom)
    model.reindex()

    # maybe a problem if there is a basis set which has ecps for
    # some but not all atoms
    #
    m = BasisManager()
    m.define_keyword_basis('dzp',['h','he','li','b','c','n'],ecp=0)
    m.define_keyword_basis('3-21G',['h','he','li','b','c','n'],ecp=0)
    m.define_keyword_basis('rlc',['cl','br','i'],ecp=1)

    m.set_molecule(model)
    t = BasisToolWidget(root,m)
    t.pack()
    root.mainloop()
