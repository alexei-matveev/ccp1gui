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
"""Code to read molden format files
May need further work...
"""

# Import Python modules
import math

# Import our modules
import objects.zmatrix
#from chempy.brick import Brick

class VibFreq:
   def __init__(self,index):
      self.index=index
      self.freq=0.0
      self.atoms=[]

class MoldenReader:

   def __init__(self):
      print "> molden.py __init__"
      self.test=1
      self.objects=[]
      self.normal = []
      self.coordinates = None
      self.basis = None
      self.title = None
      print "< molden.py __init__"

   def scan(self,file):
      print "> molden.py scan"
      f = open(file)
      punch = f.readlines()
      f.close()

      while len(punch):
         print '---'
         a = punch[0]
         if   a[0:15] == '[Molden Format]':
            punch.pop(0)
         elif a[0:7]  == '[Atoms]':
            if a.find('Angs',7) > 0:
               factor = 1.0/0.529177249
            elif a.find('AU',7) > 0:
               factor = 1.0
            else:
               factor = 1.0
            punch.pop(0)
            self.coordinates = self.read_fragment(punch,factor)
            self.coordinates.name = 'coordinates'
            self.objects.append(self.coordinates)
         elif a[0:5]  == '[GTO]':
            punch.pop(0)
            self.basis = self.read_basis(punch)
            #self.basis.name = 'gtos'
            #self.objects.append(self.basis)
         elif a[0:5]  == '[STO]':
            punch.pop(0)
            self.basis = self.read_basis(punch)
            #self.basis.name = 'stos'
            #self.objects.append(self.basis)
         elif a[0:4]  == '[MO]':
            punch.pop(0)
            self.read_skip(punch)
         elif a[0:9]  == '[SCFCONV]':
            punch.pop(0)
            self.read_skip(punch)
         elif a[0:9]  == '[GEOCONV]':
            punch.pop(0)
            self.read_skip(punch)
         elif a[0:12] == '[GEOMETRIES]':
            factor = 1.0/0.529177249
            if a.find('XYZ',12) > 0:
               punch.pop(0)
               self.read_geoms(punch,factor)
            elif a.find('ZMAT',12) > 0:
               punch.pop(0)
               self.read_skip(punch)
            else:
               punch.pop(0)
               self.read_skip(punch)
         elif a[0:6]  == '[FREQ]':
            punch.pop(0)
         elif a[0:10]  == '[FR-COORD]':
            punch.pop(0)
         elif a[0:15] == '[FR-NORM-COORD]':
            punch.pop(0)
         else:
            print 'stray:',a
            punch.pop(0)
      print "< molden.py scan"
            
   def read_fragment(self,list,fac):
      tt = Indexed()
      tt.atom = []
      cnt = 0
      while 1:
         subhead = list[0]
         if(len(list) == 0):
            return tt
         elif subhead[0] == '[':
            return tt
         list.pop(0)
         rr = subhead.split()
         p = objects.zmatrix.Atom()
         p.coord = [ float(rr[3])*fac , float(rr[4])*fac, float(rr[5])*fac ]
         p.symbol = rr[0].capitalize()
         p.name = p.symbol + str(cnt+1).zfill(c2)
         p.index = int(rr[1])
         cnt = cnt + 1
         tt.add_atom(p)

   def read_geoms(self,list,fac):
      numat = self.coordinates.nAtom
      while 1:
         if len(list) == 0:
            return 
         a = list[0]
         if a[0] == '[':
            return 
         assert int(a) == numat, "Number of atoms not the same [ATOMS] and [GEOMETRIES]"
         list.pop(0)
         list.pop(0)
         tt = Indexed()
         tt.atom = []
         for i in range(0,numat):
            q  = self.coordinates.atom[i]
            rr = list[0].split()
            p  = Atom()
            p.coord  = [ float(rr[1])*fac, float(rr[2])*fac, float(rr[3])*fac]
            p.symbol = rr[0].capitalize()
            p.name   = q.name
            p.index  = q.index
            tt.add_atom(p)
            list.pop(0)
         self.objects.append(tt)

   def read_basis(self,list):
      tt = []
      while 1:
         if (len(list) == 0):
            return tt
         elif list[0][0] == '[':
            return tt
         list.pop(0)

   def read_skip(self,list):
      tt = []
      while 1:
         if (len(list) == 0):
            return tt
         elif list[0][0] == '[':
            return tt
         list.pop(0)
            

   def read_grid(self,list):
      print 'reading brick'
      #brik = Brick()
      while 1:
         if(len(list) == 0):
            return brik
         subhead = list[0]
         self.parse_header(subhead)
         print self.name , self.records
         if self.name == 'grid_title':
            list.pop(0)
            brik.title = ''
            for i in range(0,self.records):
               r = list.pop(0)
               brik.title = brik.title + r.rstrip()
         elif self.name == 'grid_axes':
            list.pop(0)
            cnt = 0
            brik.dim = []
            for i in range(0,self.records):
               rr = list.pop(0).split()
               brik.dim.append(int(rr[0]))
            print 'dim', brik.dim
         elif self.name == 'grid_mapping':
            list.pop(0)
            brik.range = []
            fac = 0.529177
            for i in range(0,self.records):
               rr = list.pop(0).split()
               if i == 0:
                  brik.origin = [ float(rr[0])*fac, float(rr[1])*fac, float(rr[2])*fac ]
                  brik.range.append((float(rr[3])-float(rr[0]))*fac)
               if i == 1:
                  brik.range.append((float(rr[4])-float(rr[1]))*fac)
               if i == 2:
                  brik.range.append((float(rr[5])-float(rr[2]))*fac)
            print 'origin', brik.origin
            print 'range', brik.range
            brik.grid = [ brik.range[0] / float(brik.dim[0] - 1),
                          brik.range[1] / float(brik.dim[1] - 1),
                          brik.range[2] / float(brik.dim[2] - 1) ]
                          
         elif self.name == 'grid_data':
            list.pop(0)
            brik.lvl = zeros(brik.dim,Float)
            for z in range(brik.dim[2]):
               for y in range(brik.dim[1]):
                  for x in range(brik.dim[0]):
                     brik.lvl[x,y,z]=float(list.pop(0))
         else:
            print type(brik), str(brik)
            return brik

   def read_normal(self,list):
         print self.name , self.records, self.index
         cnt = 0
         v = VibFreq(self.index)
         for i in range(0,self.records):
               p = objects.zmatrix.Atom()
               rr = list.pop(0).split()
               p.coord = [ float(rr[1]) , float(rr[2]), float(rr[3]) ]
               p.symbol = rr[0].capitalize()
               p.name = p.symbol + str(i).zfill(2)
               p.index = cnt
               cnt = cnt + 1
               v.atoms.append(p)
         self.normal.append(v)
         return v

   def read_freq(self,list):
         print self.name , self.records, self.index
         cnt = 0
         tt = list.pop(0)
         for v in self.normal:
            if v.index == self.index:
               v.freq = float(tt)
         return None
