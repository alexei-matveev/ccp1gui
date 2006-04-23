"""Reader for Gaussian Cube files
"""

###from interfaces.units import *
au_to_angstrom = 0.529177249

from objects.zmatrix import *
from objects.field import *
from objects.periodic import z_to_el

class CubeReader:

    def __init__(self):
        pass

    def ParseFile(self,file):
        """Parse a cube file returning Field and Zmatrix objects
        We do not attempt to convert the units of the field,
        so they are probably in atomic units.
        """


        mol = Zmatrix()
        field = Field(nd=3)

        fp = open(file,"r")

        self.title1 = fp.readline()
        self.title2 = fp.readline()

        # could load titles from here
        mol.title = self.title1
        field.title = self.title1 + self.title2
        
        # empirically axes and coordinates are in au
        fac = au_to_angstrom
        tmp = fp.readline().split()
        self.natoms = int(tmp[0])
        field.origin = fac*Vector([float(tmp[1]),float(tmp[2]),float(tmp[3])])
        # note that the Field object follows the punchfile (Fortran-style)
        # ordering so we reorder the axes
        for i in [0,1,2]:
            tmp = fp.readline().split()
            field.dim[2-i] = int(tmp[0])
            field.axis[2-i] = fac*float(field.dim[2-i]-1)* \
                         Vector([float(tmp[1]),float(tmp[2]),float(tmp[3])])
        # move origin to centre of grid from corner
        for i in [0,1,2]:
            field.origin = field.origin + 0.5*field.axis[i]

        # geometry seems to be in au
        fac = au_to_angstrom
        cnt = 0
        for i in range(0,self.natoms):
            tmp = fp.readline().split()
            print i,tmp
            p = ZAtom()
            try:
                p.coord = [ float(tmp[2])*fac , float(tmp[3])*fac, float(tmp[4])*fac ]
            except ValueError:
                print 'Bad Line in cube file:',tmp
            p.symbol = z_to_el[int(tmp[0])]
            p.name = p.symbol
            p.index = cnt
            cnt = cnt + 1
            mol.add_atom(p)
        mol.reindex()

        # Now pull records off the file until all done
        ndata = field.dim[0]*field.dim[1]*field.dim[2]
        field.data = ndata*[0.0]
        i = 0
        while i < ndata:
            line = fp.readline()
            if line == "":
                print "Warning Incomplete Cube Data"
                return
            values = line.split()
            for v in values:
                field.data[i] = float(v)
                i = i + 1

        return (mol,field)

if __name__ == "__main__":
    r = CubeReader()
    mol,field = r.ParseFile("c:\Documents and Settings\ps96\My Documents\CECAM2006\CubeFiles/acrolein1_gs.cube")
    mol.list()
    field.list()
    print field.data
