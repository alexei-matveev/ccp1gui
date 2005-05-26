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
# manage selections
#
# Rather inefficient, as it will probably 
# re-image for each atom added/deleted
#
debug=0
class SelectionManager:
    def __init__(self):
        self.selected = []
        self.add_funcs = []
        self.rem_funcs = []

    def add(self,mol,atoms):
        for atom in atoms:
            x = (mol,atom)
            try:
                t = self.selected.index(x)
            except ValueError:
                self.selected.append((mol,atom))
        # perform all tasks dependent on the selection
        for f in self.add_funcs:
            f(mol,atoms)

    def append(self,mol,atoms):
        ''' add but without checking'''
        for atom in atoms:
            self.selected.append((mol,atom))
        # perform all tasks dependent on the selection
        for f in self.add_funcs:
            f(mol,atoms)

    def rem(self,mol,atoms):
        ra = []
        for atom in atoms:
            x = (mol,atom)
            try:
                self.selected.remove(x)
                ra.append(atom)
            except ValueError:
                pass
        for f in self.rem_funcs:
            f(mol,ra)

    def clear(self):
        if debug: print 'clear selection'
        for s in self.selected:
            mol,atom = s
            for f in self.rem_funcs:
                f(mol,[atom])
        self.selected = []

    def toggle(self,mol,atoms):
        if debug: print 'toggle'
        aa = []
        ra = []
        for atom in atoms:
            if debug: print 'tog',atom.get_index()
            x = (mol,atom)
            try:
                self.selected.remove(x)
                if debug: print 'rem'
                ra.append(atom)
            except ValueError:
                self.selected.append(x)
                if debug: print 'add'
                aa.append(atom)

        for f in self.rem_funcs:
            f(mol,ra)

        for f in self.add_funcs:
            f(mol,aa)
        
    def call_on_add(self,f):
        self.add_funcs.append(f)

    def call_on_rem(self,f):
        self.rem_funcs.append(f)

    def clean_deleted(self,mol):
        ''' Remove atoms from the selection if the atoms
            are no longer part of the molecule'''

        dead  = []
        for s in self.selected:
            mol1,atom = s
            if mol == mol1:
                try:
                    test = mol.atom.index(atom)
                except ValueError:
                    dead.append(s)
        for d in dead:
            self.selected.remove(d)

    def get(self):
        return self.selected

    def get_centroid(self):
        sel = self.selected
        if not len(sel):
            return
        x=0.0;y=0.0;z=0.0;n=0
        for mol,atom in sel:
            x = x + atom.coord[0]
            y = y + atom.coord[1]
            z = z + atom.coord[2]
            n=n+1
        x = x / float(n)
        y = y / float(n)
        z = z / float(n)
        return [x,y,z]

    def printsel(self):
        mols  = []
        for s in self.selected:
            mol,atom = s
            try:
                test = mols.index(mol)
            except ValueError:
                mols.append(mol)

        for mol in mols:
            print mol.title
            for a in self.get_by_mol(mol):
                print a.get_index(),

        print ""

    def get_by_mol(self,mol):
        result = []
        for s in self.selected:
            tmol,atom = s

            if debug: print 'check',tmol.title, atom
            if tmol == mol:
                result.append(atom)

        if debug:
            print 'get_by_mol returned',len(result),'atoms'

        return result

    def get_mols(self):
        mols = []
        for s in self.selected:
            tmol,atom = s
            try:
                t = mols.index(tmol)
            except ValueError:
                mols.append(tmol)
        if debug:
            print 'get_molsa returned',len(mols),mols

        return mols

