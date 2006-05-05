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
"""Field - a data field class

A python object to represent numerical data at points in 3D space.

This is a simple implementation for molecular graphics.
To get started we have not yet used numerical python, although that
is the long-term plan.

Axis ordering conventions:
GAMESS-UK punchfile ordering has the first index varying fastest
VTK                 ordering has the first index varying fastest
Numeric has         the opposite convention!

It is not yet clear what is the best way to resolve this
   - later versions of vtk provide conversion functions but
     these do not reorder
   - it would be a shame to use Numeric and not be able to 
     to use it to manipulate the fields, which implies a
     fairly intuitive mapping
   - we can choose the orientation of axes in the gamess input
     such that the data (for 3D orthogonal grids) is in the
     required order
"""

# From Konrad Hinsens scientific python
from Scientific.Geometry.VectorModule import *
from math import *
from viewer.debug import deb
# import Numeric

#Note that it is not possible to add Scientific vectors and 3 element
#Numeric arrays using +, but they can be easily interconverted and can be
#used as arguments to dot, add

class Field:

    def __init__(self,nd=3):
        self.data = None
        # this field now obsolete?
        self.grid = None
        self.points = None
        self.debug = 0

        ######self.mapping = []
        self.axis = []
        # just for convenience
        self.x = Vector(1., 0., 0.)
        self.y = Vector(0., 1., 0.)
        self.z = Vector(0., 0., 1.)

        # default axis
        self.origin = Vector([0., 0., 0.])
        self.axis.append(self.x)
        self.axis.append(self.y)
        if nd == 3:
            self.axis.append(self.z)
            # brick had this, it seems sensible to hold it separately
            # a tuple would be more consistent with the shape() function
            self.dim = [ 5,5,5 ]
        else:
            self.dim = [ 5,5 ]

        # maybe should be 0
        self.ndd = 1

        self.title = "untitled"

        #jmht
        self.vtkdata=None

    def dimensions(self):
        try:
            return len(self.dim)
        except AttributeError:
            return 0
        
    def shape(self):
        try:
            return self.dim
        except:
            return "Irregular"
        #return self.data.shape()
    
    def get_axis(self,index):
        return self.axis[index] 

    def get_name(self):
        if self.title:
            return self.title
        else:
            return "untitled field"

    def get_mapping(self,index):
        """Return one of the mapping vectors as per GAMESS-UK punchfile """

        if self.debug:
            print "Field: get_mapping"
            
        if index == 0:
            if len(self.dim) == 1:
                return self.origin + 0.5*self.axis[0]
            if len(self.dim) == 2:
                return self.origin + 0.5*self.axis[0] - 0.5*self.axis[1]
            if len(self.dim) == 3:
                return self.origin + 0.5*self.axis[0] - 0.5*self.axis[1] - 0.5*self.axis[2]

        if index == 1:
            if len(self.dim) == 2:
                return self.origin - 0.5*self.axis[0] + 0.5*self.axis[1]
            if len(self.dim) == 3:
                return self.origin -0.5*self.axis[0] - 0.5*self.axis[2] + 0.5*self.axis[1]        

        if index == 2:
            return self.origin - 0.5*self.axis[0] - 0.5*self.axis[1] + 0.5*self.axis[2]

    def get_origin_corner(self):
        """Return origin vector as per GAMESS-UK punchfile"""
        if self.debug:
            print "Field: get_origin_corner"
            
        if len(self.dim) == 1:
            return self.origin - 0.5* self.axis[0]
        if len(self.dim) == 2:
            return self.origin - 0.5* self.axis[0]  - 0.5* self.axis[1] 
        if len(self.dim) == 3:
            return self.origin - 0.5* self.axis[0]  - 0.5* self.axis[1] - 0.5* self.axis[2] 

    def wrt_mapnet(self):
        # make sure all changes are reflected in the object
        scale = 1.0 / 0.529177
        if len(self.dim) == 2:
            x = self.axis[0]
            y = self.axis[1]
            orig = self.origin

            a=orig-0.5*x-0.5*y
            b=orig+0.5*x-0.5*y
            c=orig+0.5*x+0.5*y
            a = a * scale
            b = b * scale
            c = c * scale
            #use these coordinates to calculate 2D ESP using CRYSTAL
            print "CRYSTAL MAPNET Input A,B,C (BOHR):"
            print "COORDINA"
            print "%f %f %f" % (a[0],a[1],a[2])
            print "%f %f %f" % (b[0],b[1],b[2])
            print "%f %f %f" % (c[0],c[1],c[2])
            print "BOHR"
        else:
            print 'MAPNET format only available for 2D grids'

    def wrt_gamessuk(self):
        for a in self.output_gamessuk():
            print a

    def output_gamessuk(self):
        #
        # GAMESS-UK representation, this code is copied from
        # the gamess-uk interface
        #
        scale = 1.0 / 0.529177
        result=[]
        if len(self.dim) == 3:
            result.append( 'type 3d')
            result.append( 'points %d %d %d' % (self.dim[0],self.dim[1],self.dim[2]))
            result.append( 'size %f %f %f' % (scale*self.axis[0].length(),
                                              scale*self.axis[1].length(),
                                              scale*self.axis[2].length()))
            result.append( 'orig %f %f %f' % (scale*self.origin[0],
                                              scale*self.origin[1],
                                              scale*self.origin[2]))
            v = self.axis[0]
            result.append( 'x %f %f %f' % (scale*v[0],scale*v[1],scale*v[2]))
            v = self.axis[1]
            result.append( 'y %f %f %f'% (scale*v[0], scale*v[1], scale*v[2]))

        elif len(self.dim) == 2:
            result.append( 'type 2d')
            result.append( 'points %d %d' % (self.dim[0],self.dim[1]))
            result.append( 'size %f %f ' % (scale*self.axis[0].length(),
                                            scale*self.axis[1].length()))
            result.append( 'orig %f %f %f' % (scale*self.origin[0],
                                              scale*self.origin[1],
                                              scale*self.origin[2]))
            v = self.axis[0]
            result.append( 'x %f %f %f' % (scale*v[0],scale*v[1],scale*v[2]))
            v = self.axis[1]
            result.append( 'y %f %f %f' % (scale*v[0],scale*v[1],scale*v[2]))

        else:
            result.append( 'type 1d')
            result.append( 'points %d' % (self.dim[0],))
            result.append( 'size %f ' % (scale*self.axis[0].length()))
            result.append( 'size %f %f %f' % (self.dim[0],self.dim[1],self.dim[2]))
            result.append( 'orig %f %f %f' % (scale*self.origin[0],
                                              scale*self.origin[1],
                                              scale*self.origin[2]))
            v = self.axis[0]
            result.append( 'x %f %f %f' % (scale*v[0],scale*v[1],scale*v[2]))

        return result

    def wrt_punch(self):
        for a in self.output_punch():
            print a

    def output_punch(self):
        """Punchfile format (bohr)"""
        result = []
        scale = 1.0 / 0.529177
        o = self.get_origin_corner()
        o = o * scale
        result.append( "block = field records = 0")
        result.append( "block = field_title records = 1")
        result.append( "grid specification")
        result.append( "block = field_axes records = %d" %  (len(self.dim)))
        nx = self.dim[0]
        sx = scale*self.axis[0].length()
        result.append( "%d %f %f %d au axis_0" % (nx, 0.0, sx, 0))
        if len(self.dim) > 1:
            sy = scale*self.axis[1].length()
            ny = self.dim[1]
            result.append( "%d %f %f %d au axis_1" % (ny, 0.0, sy, 0))
        if len(self.dim) > 2:
            sz = scale*self.axis[2].length()
            nz = self.dim[2]
            result.append( "%d %f %f %d au axis_2" % (nz, 0.0, sz, 0))

        result.append( "block = field_mapping records = %d" % (len(self.dim)))
        m1 = self.get_mapping(0) * scale 
        result.append( "%f %f %f   %f %f %f" % (o[0],o[1],o[2],m1[0],m1[1],m1[2]))

        if len(self.dim) > 1:
            m2 = self.get_mapping(1) * scale
            result.append( "%f %f %f   %f %f %f" % (o[0],o[1],o[2],m2[0],m2[1],m2[2]))

        if len(self.dim) > 2:
            m3 = self.get_mapping(2) * scale
            result.append( "%f %f %f   %f %f %f" % (o[0],o[1],o[2],m3[0],m3[1],m3[2]))

        if self.data is None:
            result.append( "block = field_data records = 0 elements = 1"  )
        else:
            l = len(self.data) / self.ndd
            result.append( "block = field_data records = %d elements = %d" % (l, self.ndd)  )
            for i in range (l):
                tmp = ""
                for j in range(self.ndd):
                    tmp = tmp + str(self.data[i*self.ndd + j]) + " "
                result.append(tmp)

        return result

    def list(self):
        print 'Field Object ' + self.title
        if self.data:
            print 'Data shape', self.shape()
            print 'Axis aligned:', self.axis_aligned()

        if self.vtkdata:
            print "vtkdata is true"


        #if self.grid:
        #    print 'Grid shape',shape(self.grid)


        try:
            ddd = len(self.dim)
            print 'self.dim = ',ddd

            print 'Origin:', self.origin
            print 'Axis vectors:'
            for k in self.axis:
                print k

        except AttributeError:
            print 'Irregular grid'


        print '------------------------------------------------------------'

    def axis_aligned(self):
        """ establish if the axis vectors point along the x,y,z axes """

        try:
            dummy = self.dim
        except AttributeError:
            return 0

        if self.axis[0]*self.y > 0.0001 or self.axis[0]*self.z > 0.0001:
            return 0
        if len(self.dim) == 1:
            return 1
        if self.axis[1]*self.x > 0.0001 or self.axis[1]*self.y > 0.0001:
            return 0
        if len(self.dim) == 2:
            return 1
        if self.axis[2]*self.x > 0.0001 or self.axis[2]*self.z > 0.0001:
            return 0
        return 1
    
    def get_grid(self):
        """ Generate a grid array containing the positions of
        all the points. This version does not attempt to use Numeric Python.
        It is stored as a list of vectors, one per point
        """
        if self.points:
            return self.points

        self.tgrid = []
        if len(self.dim) == 1: 
            fac = 1.0 / (self.dim[0] - 1)
            #jmht
            #o = self.origin - 0.5*self.axis[0]
            o = self.get_origin_corner()
            for i in range(self.dim[0]):
                p = o + i*fac*self.axis[0]
                self.tgrid.append(p)

        if len(self.dim) == 2: 
            xfac = 1.0 / (self.dim[0] - 1)
            yfac = 1.0 / (self.dim[1] - 1)
            #jmht
            #o = self.origin - 0.5*self.axis[0] - 0.5*self.axis[1]
            o = self.get_origin_corner()
            for j in range(self.dim[1]):
                t = o + j*yfac*self.axis[1]
                for i in range(self.dim[0]):
                    p = t + i*xfac*self.axis[0] 
                    self.tgrid.append(p)

        if len(self.dim) == 3: 
            xfac = 1.0 / (self.dim[0] - 1)
            yfac = 1.0 / (self.dim[1] - 1)
            zfac = 1.0 / (self.dim[2] - 1)
            #jmht
            #o = self.origin - 0.5*self.axis[0] - 0.5*self.axis[1] - 0.5*self.axis[2]
            o = self.get_origin_corner()
            xvec = self.axis[0]
            yvec = self.axis[1]
            zvec = self.axis[2]
            for k in range(self.dim[2]):
                t1 = o + k*zfac*zvec
                for j in range(self.dim[1]):
                    t2 = t1 + j*yfac*yvec
                    for i in range(self.dim[0]):
                        p = t2 + i*xfac*xvec
                        self.tgrid.append(p)

        return self.tgrid
        
    def get_grid0(self):
        """ Generate a grid array containing the positions of
        all the points
        .... not in use as we are not using numerical python yet
        .... also needs recoding !!!!!!!!!!
        """
        if self.grid:
            return self.grid

        # ---------- Numeric based code -----------------------
        # [x1, x2, x3....] [y1, y2, y3.... ][z1 etc , where point 1
        # indices (x1,y1,z1)
        i = indices(self.dim,Float)        
        #    [x1,y1,z1]
        #    [x1,y2,z2] etc
        c = reshape(Numeric.transpose(i),(-1,len(self.dim)))
        # normalise to get axis multipliers
        norm = 1.0 / array(self.dim-array([1]))
        c = c * norm
        print c
        # m are the axis vectors
        m = array(self.axis) - array(self.origin)
        print m
        # convert normalised indices to coordinates
        p = matrixmultiply(c,m)
        
        # shift by origin setting
        p = p + array(self.origin)
        print p
        return p

    def transform(self, field,
                  scale=(1.,1.,1.),
                  rotate=(0.,0.,0.),
                  translate=(0.,0.,0.)):
        """Transform using scale/rotate/translate

        self - the grid to be transformed (which might be a lower
              dimensionality than the reference)
        field - reference to measure changes from
        scale, rotate, translate .. 3tuples
        """

        if self.debug:
            deb('Field.transform')
            deb('Scale:'+str(scale))
            deb('Rot  :'+str(rotate))
            deb('Tran :'+str(translate))

        (x_grid,  y_grid, z_grid) = scale
        (rx_grid, ry_grid, rz_grid) = rotate
        (tx_grid, ty_grid, tz_grid) = translate

        tol=0.001
        o = field.origin
        # edge vectors of origin grid 
        vx = field.axis[0]
        vxn = vx.normal()

        # generate full orthogonormal vector set for rotation
        if len(self.dim) == 1:
            # vx along Z, choose Y
            # otherwise, choose Z
            if vx[0] < tol and vx[1] < tol:
                tmp = Vector(0.,1.,0.)
            else:
                tmp = Vector(0.,0.,1.)
            vyn = vx.cross(tmp).normal()
            vzn = vx.cross(vyn).normal()
        else:
            vy = field.axis[1]
            if self.debug:
                deb('vx,vy'+str(vx)+str(vy))
            # NB not necessarily orthogonal to x axis 
            vyn = vy.normal()
            if len(field.dim) == 3:
                vz = field.axis[2]
            else:
                vz = vx.cross(vy)
            vzn = vz.normal();
                

        # calculate new translated origin 
        o = o + vxn*tx_grid + vyn*ty_grid + vzn*tz_grid

        # new edge vectors 
        if self.debug:
            deb("Before Rot")
            deb("vx "+str(vx))
            if len(self.dim) > 1:
                deb("vy "+str(vy))
            if len(self.dim) > 2:
                deb("vz "+str(vz))

        vx = self.vrot2(vx, rx_grid, ry_grid, rz_grid, vxn, vyn, vzn)
        if len(self.dim) > 1:
            vy = self.vrot2(vy, rx_grid, ry_grid, rz_grid,vxn,vyn,vzn)
        if len(self.dim) > 2:
            vz = self.vrot2(vz, rx_grid, ry_grid, rz_grid,vxn,vyn,vzn)

        if self.debug:
            deb("After Rot")
            deb("vx "+str(vx))
            if len(self.dim) > 1:
                deb("vy "+str(vy))
            if len(self.dim) > 2:
                deb("vz "+str(vz))

        # as a test - check the vectors are still orthogonal 
        if self.debug and len(self.dim) > 1:
            deb("dot product of x,y edge vectors = "+str(vx*vy))
            if len(self.dim) > 2:
                deb("dot product of x,z edge vectors ="+str(vx*vz))
                deb("dot product of y,z edge vectors ="+str(vy*vz))

        vx = vx * x_grid
        if len(self.dim) > 1:
            vy = vy*y_grid
        if len(self.dim) > 2:
            vz = vz*z_grid

        if self.debug:
            deb("After Scale")
            deb("vx "+str(vx))
            if len(self.dim) > 1:
                deb("vy "+str(vy))
            if len(self.dim) > 2:
                deb("vz "+str(vz))

        # compute new corners 
        #self.origin = o + vx*-0.5
        self.origin = o
        self.axis[0] = vx
        if len(self.dim) > 1:
            self.axis[1] = vy
        if len(self.dim) > 2:
            self.axis[2] = vz

    def vrot2(self, ifrom, rx,ry,rz, s1,s2,s3):
        """Rotate a vector

        rx,ry,rz    Magnitudes of rotation 
        s1, s2, s3  vectors for first rotation 
        """

        local = Vector(ifrom*s1, ifrom*s2, ifrom*s3)
        s = sin(rx *   0.00174532925199)
        c = cos(rx *   0.00174532925199)

        to = [ 0.,0.,0.]
        to[0] = local[0]
        to[1] = local[1] * c + local[2] * -s
        to[2] = local[2] * c + local[1] * s

        s = sin(ry * 0.00174532925199)
        c = cos(ry * 0.00174532925199)

        t = to[0]
        to[0] = to[0] * c + to[2] * -s
        to[2] = to[2] * c + t * s

        s = sin(rz * 0.00174532925199)
        c = cos(rz * 0.00174532925199)

        t = to[0]
        to[0] = to[0] * c + to[1] * s
        to[1] = to[1] * c + t * -s

        return s1*to[0] + s2*to[1] + s3*to[2]

    def minmax(self):
        maxi = -1.0e10
        mini = 1.0e10
        for i in range(len(self.data)):
            maxi = max(maxi,self.data[i])
            mini = min(mini,self.data[i])
        return (mini,maxi)

    def integral(self,fac=1.0):
        """ Sum up the data on a grid as an approximate integral
        if provided, fac is the scale factor needed to convert
        distances expressed in angstroms into the intrinsic length
        unit of the data on the grid.
        e.g., if the grid holds densities in electrons per cubic bohr,
        fac should be 0.529177, as this will convert bohrs to angstroms
        """
        if len(self.dim) != 3:
            return 0.0

        v =  self.axis[0].cross(self.axis[1]) * self.axis[2]
        nx = self.dim[0]-1
        ny = self.dim[1]-1
        nz = self.dim[2]-1
        vel = v / (nx*ny*nz)
        fac3 = 1.0 / ( fac*fac*fac)

        tot = 0
        for i in range(len(self.data)):
            tot = tot + self.data[i]
        tot = tot * fac3
        print 'volume', v, ' cubic angstroms'
        print 'volume element', vel, ' cubic angstroms'
        print 'number of points',len(self.data)
        print 'approximate integral',tot * vel
        return tot * vel

    def read_molden(self,file):
        """Load in the grid from a molden plot
        to start with, assumes 3D (ascii version from a hacked molden)
        (ignores the structural part)
        """

        fp = open(file,"r")
        line = fp.readline()
        natoms = int(line.split()[0])
        nat = []
        i = 0
        while i < natoms:
            line = fp.readline()
            for atom in line.split():
                i = i + 1
                nat.append(int(atom))

        line = fp.readline()
        adjus = float(line.split()[0])
        x = []; y = []; z = []
        for atom in range(0,natoms):
            line = fp.readline()
            coords = line.split()
            x.append(float(coords[0]))
            y.append(float(coords[1]))
            z.append(float(coords[2]))

        line = fp.readline()
        coords = line.split() 
        px = float(coords[1])
        py = float(coords[2])
        pz = float(coords[3])

        line = fp.readline()
        coords = line.split() 
        cx = -float(coords[1])
        cy = -float(coords[2])
        cz = -float(coords[3])

        line = fp.readline()
        coords = line.split() 
        v1x = float(coords[1])
        v1y = float(coords[2])
        v1z = float(coords[3])

        line = fp.readline()
        coords = line.split() 
        v2x = float(coords[1])
        v2y = float(coords[2])
        v2z = float(coords[3])

        # Edge Lengths 
        line = fp.readline()
        coords = line.split() 
        rx = float(coords[1])
        ry = float(coords[2])
        rz = float(coords[3])

        line = fp.readline()
        coords = line.split() 
        nx = int(coords[0])
        ny = int(coords[1])
        nz = int(coords[2])
        iplat = int(coords[3])

        fac = 0.529177249
        self.dim = [ nx, ny, nz ]
        self.origin = fac * Vector(px, py, pz)
        self.axis = []

        # note swap of v1 and v2, this is empirical

        self.axis.append(fac * ry * Vector(v2x,v2y,v2z))
        self.axis.append(fac * rx * Vector(v1x,v1y,v1z))
        self.axis.append(fac * rz * Vector(cx,cy,cz).normal())
        self.data = nx*ny*nz*[0.0]
        # Now pull records off the file until all done
        i = 0
        while i < nx*ny*nz:
            line = fp.readline()
            if line == "":
                print "Warning Incomplete Molden Data"
                return
            values = line.split()
            for v in values:
                self.data[i] = float(v)
                i = i + 1
    
        print 'molden data loaded'
        self.list()

if __name__ == "__main__":
    f = Field(nd=3)
    #f.wrt_punch()
    #.wrt_gamessuk()
    #.wrt_mapnet()
    f.read_molden('/home/psh/ccp1gui_bundle/ccp1gui/interfaces/3dgridfile')
    f.list()
    
