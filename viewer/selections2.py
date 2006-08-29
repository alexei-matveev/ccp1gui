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
# this implementation is only designed to hold a single
# selection at a time
#
debug=0
class SelectionManager:

    def __init__(self):
        self.selected_mols = []
        self.add_funcs = []
        self.rem_funcs = []

    def add(self,mol,atoms):
        for atom in atoms:
            mol.selix = mol.selix + 1
            atom.selected=mol.selix
        if debug: print 'len sel mols',len(self.selected_mols)
        try:
            t = self.selected_mols.index(mol)
            print 't=',t
        except ValueError:
            self.selected_mols.append(mol)
        if debug: print 'after... len sel mols',len(self.selected_mols)
        # perform all tasks dependent on the selection
        for f in self.add_funcs:
            f(mol,atoms)

    def append(self,mol,atoms):
        """add but without checking"""
        self.add(mol,atoms)

    def rem(self,mol,atoms):
        for atom in atoms:
            atom.selected=0
        for f in self.rem_funcs:
            f(mol,atoms)

    def clear(self):
        if debug: print 'clear selection',len(self.selected_mols)
        ra = []
        for mol in self.selected_mols:
            for a in mol.atom:
                if a.selected:
                    ra.append(a)
                a.selected=0
            for f in self.rem_funcs:
                f(mol,ra)
            mol.selix = 0
        self.selected_mols = []


    def toggle(self,mol,atoms):
        if debug: print 'toggle', 'len sel mols',len(self.selected_mols)
        aa = []
        ra = []
        for atom in atoms:
            if atom.selected:
                ra.append(atom)
                atom.selected = 0
            else:
                aa.append(atom)
                mol.selix = mol.selix + 1
                atom.selected = mol.selix

        if len(ra):
            for f in self.rem_funcs:
                f(mol,ra)
        if len(aa):
            for f in self.add_funcs:
                f(mol,aa)
            try:
                t = self.selected_mols.index(mol)
            except ValueError:
                self.selected_mols.append(mol)
            if debug: print 'after... len sel mols',len(self.selected_mols)
        
    def call_on_add(self,f):
        self.add_funcs.append(f)

    def call_on_rem(self,f):
        self.rem_funcs.append(f)

    def clean_deleted(self,mol):
        """Remove atoms from the selection if the atoms
        are no longer part of the molecule"""
        pass

    def get(self):
        res = []
        for mol in self.selected_mols:
            for a in mol.atom:
                if a.selected:
                    res.append((mol,a))
        return res


    def get_ordered(self):
        """The sorting is by the order the atoms were selected"""
        res = []
        ttt = []
        for mol in self.selected_mols:
            for a in mol.atom:
                if a.selected:
                    ttt.append((a.selected,mol,a))
            ttt.sort()
            for xxx in ttt:
                (ix,mol,a) = xxx
                res.append((mol,a))

        return res

    def get_centroid(self):

        sel = self.selected_mols
        if not len(sel):
            return
        x=0.0;y=0.0;z=0.0;n=0
        for mol in self.selected_mols:
            for a in mol.atom:
                if a.selected:
                    x = x + a.coord[0]
                    y = y + a.coord[1]
                    z = z + a.coord[2]
                    n=n+1
        x = x / float(n)
        y = y / float(n)
        z = z / float(n)
        return [x,y,z]

    def printsel(self):
        mols  = []
        for mol in self.selected_mols:
            print mol.title
            for a in mol.atom:
                if a.selected:
                    print a.get_index(),
        print ""

    def get_by_mol(self,mol):
        result = []
        for a in mol.atom:
            if a.selected:
                result.append(a)
        if debug:
            print 'get_by_mol returned',len(result),'atoms'
        return result

    def get_mols(self):
        return self.selected_mols

