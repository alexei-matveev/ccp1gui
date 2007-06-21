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
from objects.file import File
from interfaces.fileio import FileIO


class Dl_PolyHISTORYFile(File):
    pass

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



#class Dl_PolyCONFIGReader:
class DLPOLY_CONFIG_IO(FileIO):
    """Reader for DL_POLY config files
    """
    def __init__(self,**kw):

        # Initialise base class
        FileIO.__init__(self,**kw)
        
        self.debug = 0
        
        # capapbilties
        self.canRead = True
        #self.canWrite = [ 'Zmatrix','Indexed' ]

#    def scan(self,file):
    def _ReadFile(self,**kw):
        """ Parse CONFIG
        """

        #print file
        if self.debug:
            print "> config reader scannig file"
        #f = open(file)
        f = open(self.filepath)

        #self.title = f.readline()
        title = f.readline()

        tt = f.readline().split()
        #print 'Line 2 integers',tt[0],tt[1]

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
                #print tt
                self.cell.append([ float(tt[0]), float(tt[1]), float(tt[2]) ] )

        #self.model = Zmatrix()
        model = Zmatrix()

        model.title = title
        model.name = model.title

        more=1
        while more:
            line = f.readline()
            #print line
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
                model.add_atom(p)
                for i in range(0,nskip):
                    junk = f.readline()
                    #print 'skip',junk
            else:
                more=0
        
        f.close()
        #print 'reindex'
        model.reindex()
        #print 'returning', self.model
        #return self.model
        self.molecules.append( model )
        return None

#class Dl_PolyHISTORYReader:
class Dl_PolyHISTORYReader(FileIO):
    """Reader for DL_POLY history files

       This is rather different to the other readers as it parses the file
       on demand for individual frames and doesn't read in the whole file
       therefore we overwrite the public methods ReadFile and GetObjects
    """
    def __init__(self,**kw):
        
        # Initialise base class
        FileIO.__init__(self,**kw)
        
        self.debug = 0
        
        # capapbilties
        self.canRead = True
        #self.canWrite = [ 'Zmatrix','Indexed' ]

    def ReadFile(self,filepath=None,**kw):
        """Overload to not do anything - just set filepath"""
        
        if filepath:
            self._ParseFilepath( filepath )

    def GetObjects(self,filepath=None,**kw):
        """Overload to just return self"""

        if filepath:
            self._ParseFilepath( filepath )


        return [Dl_PolyHISTORYFile(self.filepath)]


    def scan(self,file):
        """ Parse HISTORY
        """

        if self.debug:
            print "> history reader scanning file ",file

        self.results = []

        self.open(file)
        
        while 1:
            iret = self.scan1()
            print 'ret=',iret
            if iret == -1:
                break
            else:
                self.results.append(self.lastframe)

        self.close()

        print 'returning', self.results
        return self.results

    def open(self,file):
        """ open file pointer to HISTORY file
        """
        self.fp = open(file)
        self.frame_count = 0

    def scan1(self):
        """ Parse opened HISTORY file for the next frame
        """

        if self.debug:
            print "> config reader scanning file for one configuration"

        if self.frame_count == 0:
            self.title = self.fp.readline()
            tt = self.fp.readline().split()
            if self.debug:
                print 'Line 3 integers',tt[0],tt[1],tt[2]
            self.atom_count = int(tt[2])

        self.frame_count = self.frame_count + 1

        atom_no = -1

        more=1
        model = None
        while more:
            line = self.fp.readline()

            #print 'line in loop',line
            #print line
            if line != "":
                ###print 'CHECK',atom_no, atom_count
                if atom_no == -1 :
                    if self.debug:
                        print 'timestep line',line
                    line = self.fp.readline()

                t = line.split()
                atom_no = int(t[1])
                mass = float(t[2])
                value = float(t[3])

                if atom_no == 1 :
                    model = Zmatrix()
                    model.title = self.title
                    model.name = model.title
                    self.lastframe = model

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
                line = self.fp.readline()
                t = line.split()
                p.coord[0] = float(t[0])
                p.coord[1] = float(t[1])
                p.coord[2] = float(t[2])
                model.add_atom(p)

            else:
                return -1
                
            #print 'atom_no atom_count',atom_no,self.atom_count
            if atom_no == self.atom_count:
                break;
        
        self.lastframe.reindex()

        return 0

    def close(self):
        """ close HISTORY file
        """
        self.fp.close()

if __name__ == "__main__":

    reader = Dl_PolyHISTORYReader()

    reader.scan("c:\\Documents and Settings\ps96\My Documents\Edinburgh MSc 2007\HISTORY.short")

    #reader.open("c:\\Documents and Settings\ps96\My Documents\Edinburgh MSc 2007\HISTORY.short")
    #for i in range(0,100):
    #    if reader.scan1() == -1:
    #        break
    #print 'FRAMES:',reader.frame_count
    #reader.close()

    print reader.results

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
