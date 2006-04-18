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
"""This file implements the DLPOLY specific calculation and
calculation editor classes
"""

import os
import string
import tkFileDialog

from mm        import *
from interfaces.mmtools   import *
from interfaces.tools   import *
from objects.periodic import z_to_el

class DLPOLYCalc(MMCalc):
    """DLPOLY specifics."""
    def __init__(self,title="untitled"):
        print self
        MMCalc.__init__(self,"DLPOLY",title)

        self.set_parameter("task","energy")
        self.set_parameter("forcefield","UFF")
        self.set_parameter('mm_defs','dlpoly.ff')
        self.set_parameter('from_quanta',0)
        self.set_parameter('use_charmm',0)
        self.set_parameter('use_exact_srf',0)
        self.set_parameter('use_pairlist',1)
        self.set_parameter('use_cutoff',1)
        self.set_parameter('pairlist_cutoff',99.00)

        self.set_parameter('scale1',1.0)
        self.set_parameter('scale4',1.0)

        self.set_parameter('charmm_pdb_file','charmm.pdb' )
        self.set_parameter('charmm_psf_file','charmm.psf' )
        self.set_parameter('charmm_parm_file','charmm.parm' )
        self.set_parameter('charmm_mass_file','charmm.mass' )

    def get_editor_class(self):    
        return DLPOLYCalcEd

    def run(self):
        raise RuntimeError,"DLPOLY calculation not available"

    def scan(self):
        raise RuntimeError,"DLPOLY output not available"

class DLPOLYCalcEd(MMCalcEd):

    def __init__(self,root,calc,graph,**kw):
        apply(MMCalcEd.__init__, (self,root,calc,graph), kw)

        self.tasks = ["energy"]

        self.use_cutoff_tool = BooleanTool(self,"use_cutoff","use_cutoff")
        self.pairlist_cutoff_tool = FloatTool(self,"pairlist_cutoff","pairlist_cutoff")
        self.use_pairlist_tool = BooleanTool(self,"use_pairlist","use_pairlist")

        self.ff_tool = FFTool(self)

        self.LayoutToolsTk()
        
    def LayoutToolsTk(self):

        page = self.notebook.add('MM Parameters',tab_text='MM Parameters')

        self.nbgroup = Pmw.Group(page,tag_text="Nonbond Options")
        self.nbgroup.pack(expand='yes',fill='x')

        self.use_cutoff_tool.widget.pack(in_=self.nbgroup.interior())
        self.pairlist_cutoff_tool.widget.pack(in_=self.nbgroup.interior())
        self.use_pairlist_tool.widget.pack(in_=self.nbgroup.interior())

        self.ffgroup = Pmw.Group(page,tag_text="Forcefield Options")
        self.ffgroup.pack(expand='yes',fill='x')

        self.ff_tool.widget.pack(in_=self.ffgroup.interior())

    def LaunchCalcEd(self,calc):
        """Create a new calculation editor."""
        a = DLPOLYCalcEd(calc)
        a.Show()



class Dl_PolyCONFIGReader:
    """Reader for DL_POLY config files
    """
    def __init__(self):
        self.debug = 0


    def scan(self,file):
        """ Parse CONFIG
        """

        print file
        if self.debug:
            print "> config reader scannig file"
        f = open(file)

        self.title = f.readline()

        tt = f.readline().split()
        print 'Line 2 integers',tt[0],tt[1]

        nskip = int(tt[0])
        icell = int(tt[1])

        if icell == 0:
            ncell = 0
        elif icell == 6:
            ncell = 2
        else:
            ncell = 3

        self.cell = []
        if ncell:
            for i in range(0,ncell):
                tt = f.readline().split()
                print tt
                self.cell.append([ float(tt[0]), float(tt[1]), float(tt[2]) ] )

        self.model = Zmatrix()

        self.model.title = self.title
        self.model.name = self.model.title

        more=1
        while more:
            line = f.readline()
            print line
            if line != "":
                p = ZAtom()
                t = line.split()
                p.name = t[0]
                atom_no = int(t[1])
                if len(t) > 2:
                    z_num = int(t[2])
                    p.symbol = z_to_el[z_num]
                    #print p.symbol,z_num
                else:

                    # Determine the symbol from the first 2 chars of the name
                    if ( len( p.name ) == 1 ):
                        p.symbol = p.name
                    else:
                        # See if 2nd char is a character - if so use 1st 2 chars as symbol
                        if re.match( '[a-zA-Z]', p.name[1] ):
                            p.symbol = p.name[0:2]
                        else:
                            p.symbol = p.name[0]
                    p.symbol = string.capitalize(p.symbol)

                line = f.readline()
                t = line.split()
                p.coord[0] = float(t[0])
                p.coord[1] = float(t[1])
                p.coord[2] = float(t[2])
                self.model.add_atom(p)
                for i in range(0,nskip):
                    junk = f.readline()
                    print 'skip',junk
            else:
                more=0
        
        f.close()
        print 'reindex'
        self.model.reindex()
        print 'returning', self.model
        return self.model


class Dl_PolyHISTORYReader:
    """Reader for DL_POLY history files
    """
    def __init__(self):
        self.debug = 0


    def scan(self,file):
        """ Parse HISTORY
        """

        print file
        if self.debug:
            print "> config reader scannig file"
        f = open(file)

        self.title = f.readline()

        tt = f.readline().split()
        ###print 'Line 3 integers',tt[0],tt[1],tt[2]

        atom_count = int(tt[2])
        atom_no = atom_count

        more=1
        self.results = []
        
        model = None
        while more:
            line = f.readline()
            #print 'line in loop',line
            #print line
            if line != "":

                ###print 'CHECK',atom_no, atom_count
                if atom_no == atom_count :
                    print 'timestep line',line
                    line = f.readline()

                t = line.split()
                atom_no = int(t[1])
                mass = float(t[2])
                value = float(t[3])

                if atom_no == 1 :
                    if model:
                        model.reindex()
                    model = Zmatrix()
                    model.title = self.title
                    model.name = model.title
                    self.results.append(model)

                p = ZAtom()
                p.name = t[0]

                # Determine the symbol from the first 2 chars of the name
                if ( len( p.name ) == 1 ):
                    p.symbol = p.name
                else:
                    # See if 2nd char is a character - if so use 1st 2 chars as symbol
                    if re.match( '[a-zA-Z]', p.name[1] ):
                        p.symbol = p.name[0:2]
                    else:
                        p.symbol = p.name[0]
                    p.symbol = string.capitalize(p.symbol)

                ##p.symbol = z_to_el[z_num]
                #print p.symbol,z_num
                line = f.readline()
                t = line.split()
                p.coord[0] = float(t[0])
                p.coord[1] = float(t[1])
                p.coord[2] = float(t[2])
                model.add_atom(p)

            else:
                more=0
        
        f.close()
        print 'reindex'

        print 'returning', self.results
        return self.results

if __name__ == "__main__":


    reader = Dl_PolyHISTORYReader()
    reader.scan("/c/qcg/psh/ParChemCourse/DL_POLY/NanoSwitch/PAUL/HISTORY")
    reader.model.list()
    sys.exit(0)


    from gamessuk import *
    from objects.zmatrix import *
    from jobmanager import *
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

    root=Tk()
    calc = DLPOLYCalc()
    calc.set_input('mol_obj',model)
    jm = JobManager()
    je = JobEditor(root,jm)
    vt = DLPOLYCalcEd(root,calc,None,job_editor=je)
    root.mainloop()
