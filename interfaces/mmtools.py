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
from tools import *

class FFTool(Tool):
    """ A tool for defining the forcefield  """
    def __init__(self,editor,molecule=None,**kw):

        apply(Tool.__init__, (self,editor), kw)

        self.widget = Pmw.Group(self.parent,tag_text="Forcefield Selection")

        interior = self.widget.interior()

        if molecule:
            self.widget.set_molecule(molecule)

        #f1 = Tkinter.Frame(interior)
        self.f2 = Tkinter.Frame(interior)
        #fr = Tkinter.Frame(interior)

        self.from_quanta_tool = BooleanTool(self.editor,"from_quanta","Use files from Quanta")
        self.charmm_psf_file_tool = TextFieldTool(self.editor,"charmm_psf_file","charmm_psf_file",action='open')
        self.charmm_pdb_file_tool = TextFieldTool(self.editor,"charmm_pdb_file","charmm_pdb_file",action='open')
        self.charmm_parm_file_tool = TextFieldTool(self.editor,"charmm_parm_file","charmm_parm_file",action='open')
        self.charmm_mass_file_tool = TextFieldTool(self.editor,"charmm_mass_file","charmm_mass_file",action='open')

        self.mm_defs_file_tool = FileTool(self.editor,"mm_defs","Forcefield File ",action='open')

        all_avail = ["UFF", "Charmm DataFiles", "User FF file" ]

        self.select_ff = Pmw.OptionMenu(interior,
            labelpos = 'w',
            label_text = 'Select Forcefield',
            command = self.__choose_ff,
            items = all_avail, 
            initialitem = all_avail[0])

        self.select_ff.pack(side='top')
        self.f2.pack(side='top',expand=1,fill='x')

        self.__choose_ff(all_avail[0])
        
    def __choose_ff(self,choice):
        """Handler for the option menu"""
        
        if choice == "Charmm DataFiles":
            self.from_quanta_tool.widget.pack(expand='yes',anchor='w',padx=10,in_=self.f2)
            self.charmm_psf_file_tool.widget.pack(expand = 1, fill = 'x',in_=self.f2)
            self.charmm_pdb_file_tool.widget.pack(expand = 1, fill = 'x',in_=self.f2)
            self.charmm_parm_file_tool.widget.pack(expand = 1, fill = 'x',in_=self.f2)
            self.charmm_mass_file_tool.widget.pack(expand = 1, fill = 'x',in_=self.f2)
        else:
            self.from_quanta_tool.widget.forget()
            self.charmm_psf_file_tool.widget.forget()
            self.charmm_pdb_file_tool.widget.forget()
            self.charmm_parm_file_tool.widget.forget()
            self.charmm_mass_file_tool.widget.forget()

        if choice == "User FF file":
            self.mm_defs_file_tool.widget.pack(in_=self.f2)
        else:
            self.mm_defs_file_tool.widget.forget()

    def set_molecule(self,molecule):
        self.molecule = molecule

    def ReadWidget(self):
        # read any component tools
        for x in [self.charmm_psf_file_tool,
                  self.charmm_pdb_file_tool,
                  self.charmm_parm_file_tool,
                  self.charmm_mass_file_tool,
                  self.mm_defs_file_tool] :
            x.ReadWidget()

        choice = self.select_ff.getvalue()
        if choice == "Charmm DataFiles":
            self.editor.calc.set_parameter('use_charmm',1)
            self.editor.calc.set_parameter("forcefield","none")
        elif choice == "User FF file":
            self.editor.calc.set_parameter('use_charmm',0)
            self.editor.calc.set_parameter("forcefield","none")
        else:
            self.editor.calc.set_parameter('use_charmm',0)
            self.editor.calc.set_parameter("forcefield",choice)

    def UpdateWidget(self):
        pass


if __name__ == '__main__':

    from dlpoly import *
    from zmatrix import *

    root = Tkinter.Tk()

    model = Zmatrix()
    atom = ZAtom()
    atom.symbol = 'C'
    atom.name = 'C'
    model.insert_atom(0,atom)
    atom = ZAtom()
    atom.symbol = 'Cl'
    atom.name = 'Cl'
    atom.coord = [ 1.,0.,0. ]
    model.insert_atom(1,atom)
    atom = ZAtom()
    atom.symbol = 'H'
    atom.name = 'H'
    atom.coord = [ 1.,1.,0. ]
    model.insert_atom(1,atom)

    calc = DLPOLYCalc()
    calc.set_input('mol_obj',model)
    jm = JobManager()
    je = JobEditor(root,jm)
    vt = DLPOLYCalcEd(root,calc,None)
#    t = FFTool(vt)
#    vt.pack()
    root.mainloop()
