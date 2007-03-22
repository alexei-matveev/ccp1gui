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
# Read a GAMESS-UK punchfile
# Revised version based on a recursive parser
# Revised again so as not to read in the whole file
#    at once - this was because list.pop(0) turned 
#    out to be too slow
#   
from Numeric import *
from objects.zme import *
from math  import *
from objects.zmatrix import *
from objects.field import *
from objects.matrix import *
from objects.vibfreq import *
from objects.list import *

###from tkmolview.vtkgraph import VtkColourMap

# From Konrad Hinsens scientific python
from Scientific.Geometry.VectorModule import *

import copy
import string
import os

End_of_Block = 1
End_of_Complex = 2
End_of_File = 3
Read_Error = 4
Bad_Position = 5

class PunchReader:
   """Load result objects from GAMESS-UK format punchfiles"""
   def __init__(self):

      global frame_count
      frame_count = 0
      self.debug=0
      self.skip_parse=0

      self.objects=[]
      self.normal=[]
      self.title=None
      self.filename = None
      self.readers = {}

      self.readers['fragment'] = None
      self.readers['fragment.sequence'] = None

      self.readers['coordinates'] = self.read_coordinates
      self.readers['update_coordinates'] = self.read_update_coordinates

      # so we can get the unit cell of periodic systems
      # the rest is to be implemented
      self.readers['fractional_coordinates'] =  self.skip_block
      self.readers['fractional_atom_charges'] =  self.skip_block
      self.readers['cell_constants'] = self.skip_block
      self.readers['space_group'] = self.skip_block
      self.readers['xtal_map'] = self.skip_block
      self.readers['charge'] = self.skip_block
      self.readers['shells'] = self.read_shells
      self.readers['fractional_shells'] = self.skip_block

      self.readers['cell_vectors'] = self.read_cell_vectors
      self.readers['connectivity'] = self.read_connectivity
      self.readers['point_charges'] = self.read_point_charges
      self.readers['atom_charges'] = self.read_atom_charges
      self.readers['title'] = self.read_title
      self.readers['normal_coordinates'] = self.read_normal
      self.readers['vibrational_frequency'] = self.read_freq
      #
      self.readers['data'] = None
      self.readers['grid_title'] = self.read_grid_title
      self.readers['grid_mapping'] = self.read_grid_mapping
      self.readers['grid_axes'] = self.read_grid_axes
      self.readers['grid_data'] = self.read_grid_data
      self.readers['grid_points'] = self.read_grid_points
      self.readers['grid_indices'] = self.read_grid_indices
      self.readers['grid_mask'] = self.read_grid_mask

      self.readers['field'] = None
      self.readers['field_title'] = self.read_grid_title
      self.readers['field_mapping'] = self.read_grid_mapping
      self.readers['field_axes'] = self.read_grid_axes
      self.readers['field_data'] = self.read_grid_data
      self.readers['field_grid'] = self.read_grid_points
      self.readers['field_indices'] = self.read_grid_indices
      self.readers['field_mask'] = self.read_grid_mask

      self.readers['zmatrix'] = None
      self.readers['zmatrix_title'] = self.read_zmatrix_title
      self.readers['zmatrix_zatoms'] = self.read_zmatrix_zatoms
      self.readers['zmatrix_constants'] = self.read_zmatrix_constants
      self.readers['zmatrix_variables'] = self.read_zmatrix_variables
      self.readers['zmatrix_charges'] = self.read_zmatrix_charges

      self.readers['matrix'] = None
      self.readers['matrix_title'] = self.read_matrix_title
      self.readers['dense_real_matrix'] = self.read_dense_real_matrix

      self.readers['potential_derived_charges'] = self.read_pdc
      self.readers['mulliken_atomic_charges'] = self.read_mulliken
      self.readers['lowdin_atomic_charges'] = self.read_lowdin

      self.subblocks = {}

      self.subblocks['fragment'] = [
         'coordinates', 'fractional_coordinates','space_group','cell_constants',
         'xtal_map','cell_vectors','fractional_atom_charges','charge','shells',
         'fractional_shells',
         'connectivity', 'title','atom_charges','point_charges']

      self.subblocks['fragment.sequence'] = ['coordinates', 'update_coordinates']

      self.subblocks['data'] = [
         'grid_title', 'grid_mapping', 'grid_axes', 'grid_data',
         'grid_indices','grid_points','grid_mask']

      self.subblocks['field'] = [
         'field_title', 'field_mapping', 'field_axes', 'field_data',
         'field_indices','field_grid','field_mask']

      self.subblocks['zmatrix'] = [
         'zmatrix_title','zmatrix_zatoms','zmatrix_constants',
         'zmatrix_variables','zmatrix_charges']

      self.subblocks['matrix'] = [
         'matrix_title','dense_real_matrix' ]

      self.iter = 0
      self.fragment = None

   def scan(self,file):
      print file
      if self.debug:
         print "> filepunch.py scan"

      # get the root of the filename
      self.filename = os.path.splitext( os.path.basename( file ) )[0]
      
      f = open(file)
      while self.read_object(f) != End_of_File:
         pass
      f.close()

   def rescan(self,file,object):
      if self.debug:
         print "> filepunch.py rescan"

      f = open(file)
      while self.read_object(f,object=object) != End_of_File:
         pass
      f.close()


   def read_object(self,f,object=None,subblocks=None):
      """Top level reading of a block and sub-blocks
      Will read the next header and all blocks it refers to
      """
      code = self.parse_header(f)
      if code:
         return End_of_File

      if self.name == "*******":
         return Bad_Position
      
      self.iter = self.iter + 1
      if self.iter > 10000:
         a=x
      
      if self.debug:
         print 'read_object Obj=',object,'Subbl=',subblocks
      
      if self.debug:
         print 'read_object header', self.name

      if subblocks:
         if self.name not in subblocks:
            if self.debug:
               print 'read_object returns, not a subblock'
            # We don't need to call parse_header again
            # next time as we have the info stored
            self.skip_parse = 1
            return End_of_Complex

      if self.readers.has_key(self.name):
         if self.readers[self.name]:
            if self.debug:
               print 'calling known reader for ', self.name
            #try:
            self.readers[self.name](f,object)
            #except Exception,e:
            if 0:
               print 'Problem reading ',self.name
               print "Error was: %s" % e

               #self.skip_rest_of_block(f)
               return Read_Error

            return End_of_Block

      else:
         print '...skipped (no reader)'
         self.skip_block(f)
         return End_of_Block
         
      # these are composite blocks that have no readers
      if self.name == 'fragment':
         if self.debug:
            print 'New frag'
         if object:
            tt = object
         else:
            #tt = Indexed()
            # We use the zmatrix derived-class here, so we can use zmatrix tools
            # to edit it 
            tt = Zmatrix()
            #tt.title='unknown'
            tt.title = self.filename
         # This is a hack so the VibFreq instances have a reference structure
         self.fragment = tt
         tt.tidy = self.tidy_frag
         
      elif self.name == 'fragment.sequence':
         if self.debug:
            print 'New frag (seq)'
         
         tt = ZmatrixSequence()
         tt.title = tt.title+ ' ' +self.filename
         #tt2 = Zmatrix()
         #tt2.title='seq 0 frame 0'
         #tt.frames.append(tt2)

         # This is a hack so the VibFreq instances have a reference structure
         #self.fragment = tt
         ####tt.tidy = self.tidy_seq

      elif self.name == 'zmatrix':
         if self.debug:
            print 'New zmatrix frag'
         tt = Zmatrix()
         #tt.title='unknown'
         tt.title=self.filename
         tt.variables = []
         tt.constants = []
         tt.tidy = self.tidy_z

      elif self.name == 'data' or self.name == 'field':
         if self.debug:
            print 'New Field'
         tt = Field()
         tt.title='unknown'
         # Start with an irregular grid 
         del tt.dim 

      elif self.name == 'matrix':
         if self.debug:
            print 'New Matrix'
         tt = Matrix()
         tt.title='unknown'

      subbl = self.subblocks[self.name]

      while self.read_object(f,object=tt,subblocks=subbl) == End_of_Block:
         pass

      try:
         tf = tt.tidy
      except AttributeError:
         tf = None
      if tf:
         tf(tt)

      self.objects.append(tt)
 
   def parse_header(self,f):
      """Parse the next header on the file"""

      if self.skip_parse:
         if self.debug:
            print 'parse_header skipped'
         self.skip_parse=0
         return

# defaults
      self.records=0
      self.elements=1
      self.dimensions=[]
      self.name="*******"


# skip blanks
      words=[]
      while 1:
         line = f.readline()
         if len(line) == 0:
            return 1
         header=line
         if self.debug:
            print 'try parse header', line
         a = string.split(header)
         if len(a) > 0:
            self.cont = 0
            for w in a:
               if self.debug:
                  print 'word',w
               if w == '\\':
                  self.cont=1
               else:
                  words.append(w)
            # just allow a single continuation
            if self.cont:
               line = f.readline()
               a = string.split(line)
               for w in a:
                  if self.debug:
                     print 'word',w
                  words.append(w)
            break

      if self.debug:
         print 'now parse header', words

      self.header = words
      
      tmp = []
      header = ""
      for a in words:
         header = header + ' ' + a
         if string.count(a,'='):
            c = string.split(a,'=')
            t1 = c[0].strip()
            if len(t1):
               tmp.append(t1)
            tmp.append("=")
            t1 = c[1].strip()
            if len(t1):
               tmp.append(t1)
         else:
            tmp.append(a)

      print 'read>', header
      counter = 0
      if self.debug:
         print 'header words before loop',tmp

      while len(tmp):
         t1 = tmp.pop(0)
         junk = tmp.pop(0)
         t2 = []
         try:
            ix = tmp.index("=")
            # loop forward until next element
            for i in range(ix-1):
               tt = tmp.pop(0)
               t2.append(tt)
         except ValueError:
            # no next element, store all words
            t2 = t2 + tmp
            tmp = []

         if self.debug:
            print 'Parser',t1, t2

         if t1 == 'block':
            self.name = t2[0]
         elif t1 == 'records':
            self.records = int(t2[0])
         elif t1 == 'index':
            self.index = int(t2[0])
         elif t1 == 'elements':
            self.elements = int(t2[0])
         elif t1 == 'dimensions':
            self.dimensions = []
            for t3 in t2:
               self.dimensions.append(int(t3))

      return 0
   
   def read_coordinates(self,f,tt):

      if not tt:
         print '... skipped - coordinates without parent fragment or fragment.sequence block'
         self.skip_block(f)
         return

      cnt = 0
      fac = 0.529177
      tt.atom = []
      trans = string.maketrans('a','a')
      for i in range(0,self.records):
         #p = Atom()
         p = ZAtom()
         line = f.readline()
         rr = string.split(line)
         try:
            p.coord = [ float(rr[1])*fac , float(rr[2])*fac, float(rr[3])*fac ]
         except ValueError:
            print 'Bad Line:',rr

         p.symbol = string.translate(rr[0],trans,string.digits)
         # we are not trying to impose uniqueness here but
         # pymol gets a modified name
         p.symbol = string.capitalize(p.symbol)
         p.name = rr[0]
         p.index = cnt
         cnt = cnt + 1
         tt.add_atom(p)

      # for structure sequences, this is also the first frame
      t1 = string.split(str(tt.__class__),'.')
      myclass = t1[len(t1)-1]
      clone = tt.copy()
      if myclass == 'ZmatrixSequence':
         #jmht - need to connect here as otherwise all the child structures
         # that we add are not connected
         tt.connect()
         #tt.frames.append(clone)
         tt.add_molecule(clone)


   def read_shells(self,f,tt):
      if not tt:
         print '... skipped - shells without fragment block'
         self.skip_block(f)
         return
      cnt = 0
      fac = 0.529177
      tt.shell = []
      trans = string.maketrans('a','a')
      for i in range(0,self.records):
         #p = Atom()
         p = ZAtom()
         line = f.readline()
         rr = string.split(line)
         try:
            p.coord = [ float(rr[1])*fac , float(rr[2])*fac, float(rr[3])*fac ]
         except ValueError:
            print 'Bad Line:',rr

         p.symbol = string.translate(rr[0],trans,string.digits)
         # we are not trying to impose uniqueness here but
         # pymol gets a modified name
         p.symbol = string.capitalize(p.symbol)
         p.partial_charge =  float(rr[4])
         # link shell to core
##         icore = int(rr[5]) - 1
         icore = int(rr[5]) 
         ##print icore, tt.atom
         p.linked_core = tt.atom[icore]
         p.name = rr[0]
         p.index = cnt
         cnt = cnt + 1
         tt.add_shell(p)


   def read_update_coordinates(self,f,oldtt):

      if not oldtt:
         print '.. skipped - update_coordinates without fragment.sequence block'
         self.skip_block(f)
         return
      
      global frame_count
      frame_count = frame_count + 1
      tt = Zmatrix()
      try:
         tt.title = oldtt.title + ' frame ' + str(frame_count)
      except AttributeError:
         tt.title = 'Frame ' + str(frame_count)         

      oldtt.frames.append(tt)

      cnt = 0
      fac = 0.529177
      tt.atom = []
      trans = string.maketrans('a','a')
      for i in range(0,self.records):
         #p = Atom()
         p = ZAtom()
         line = f.readline()
         rr = string.split(line)
         try:
            p.coord = [ float(rr[1])*fac , float(rr[2])*fac, float(rr[3])*fac ]
         except ValueError:
            print 'Bad Line:',rr

         p.symbol = string.translate(rr[0],trans,string.digits)
         # we are not trying to impose uniqueness here but
         # pymol gets a modified name
         p.symbol = string.capitalize(p.symbol)
         p.name = rr[0]
         p.index = cnt
         cnt = cnt + 1
         tt.add_atom(p)

      # We don't need to connect the additional structures for sequences
      # as this is done when we read in the first one
      t1 = string.split(str(tt.__class__),'.')
      myclass = t1[len(t1)-1]
      if myclass != 'ZmatrixSequence':
         tt.connect()
      
   def read_connectivity(self,f,tt):

      for i in range(0,self.records):
         line = f.readline()
         rr = string.split(line)
         a1 = tt.atom[int(rr[0])-1]
         a2 = tt.atom[int(rr[1])-1]
         tt.add_conn(a1,a2)

   def read_cell_vectors(self,f,tt):
      tt.cell = []
      fac = 0.529177
      for i in range(0,self.records):
         line = f.readline()
         rr = string.split(line)
         tt.cell.append(Vector([ float(rr[0])*fac, float(rr[1])*fac, float(rr[2])*fac ]))

   def read_title(self,f,tt):
      if tt:
         tt.title=None
      for i in range(0,self.records):
         r = string.strip(f.readline())
         # this title is not a lot of use at the moment
         if( not self.title):
            self.title =  r
         else:
            self.title =  self.title + r
         if tt:
            if( not tt.title):
               tt.title =  r
            else:
               tt.title =  tt.title + r

   def read_atom_charges(self,f,tt):
      for i in range(0,self.records):
         r = f.readline()
         tt.atom[i].partial_charge = float(r)

   def read_point_charges(self,f,tt):
      cnt = len(tt.atom)
      fac = 0.529177
      #####tt.atom = []
      trans = string.maketrans('a','a')
      for i in range(0,self.records):
         #p = Atom()
         p = ZAtom()
         rr = string.split(f.readline())
         p.coord = [ float(rr[1])*fac , float(rr[2])*fac, float(rr[3])*fac ]
         p.name = rr[0]
         p.symbol = 'bq'
         p.partial_charge=float(rr[4])
         p.index = cnt
         cnt = cnt + 1
         tt.add_atom(p)

   def read_grid_title(self,f,brik):
      if not brik:
         print '... skipped - grid_title without data block'
         self.skip_block(f)
         return

      brik.title = ''
      for i in range(0,self.records):
         r = f.readline()
         brik.title = brik.title + string.rstrip(r)

   def read_grid_axes(self,f,brik):
      if not brik:
         print '... skipped - grid_axes without data block'
         self.skip_block(f)
         return
      cnt = 0
      brik.dim = []
      # only take the no. of points
      for i in range(0,self.records):
         rr = string.split(f.readline())
         brik.dim.append(int(rr[0]))
      if self.debug:
         print 'dim', brik.dim

   def read_grid_mapping(self,f,brik):
      if not brik:
         print '... skipped - grid_mapping without data block'
         self.skip_block(f)
         return
      #brik.range = []
      brik.mapping = []
      fac = 0.529177
      for i in range(0,self.records):
         txt = f.readline()
         rr = string.split(txt)
         if len(rr) == 6:
            # correctly split
            pass
         else:
            rr = []
            rr.append(txt[0:10])
            rr.append(txt[10:20])
            rr.append(txt[20:30])
            rr.append(txt[30:40])
            rr.append(txt[40:50])
            rr.append(txt[50:60])
            print rr

         if i == 0:
            brik.origin_corner = Vector([ float(rr[0])*fac, float(rr[1])*fac, float(rr[2])*fac ])
            brik.mapping.append(Vector([ float(rr[3])*fac, float(rr[4])*fac, float(rr[5])*fac ]))
         if i == 1:
            brik.mapping.append(Vector([ float(rr[3])*fac, float(rr[4])*fac, float(rr[5])*fac ]))
         if i == 2:
            brik.mapping.append(Vector([ float(rr[3])*fac, float(rr[4])*fac, float(rr[5])*fac ]))

      #if self.debug:
      print 'origin', brik.origin
      print 'mapping', brik.mapping

      #if len(brik.dim) == 1:
      #   brik.grid = [ brik.range[0] / float(brik.dim[0] - 1) ]
      #elif len(brik.dim) == 2:
      #   brik.grid = [ brik.range[0] / float(brik.dim[0] - 1),
      #              brik.range[1] / float(brik.dim[1] - 1) ]
      #elif len(brik.dim) == 3:
      #   brik.grid = [ brik.range[0] / float(brik.dim[0] - 1),
      #              brik.range[1] / float(brik.dim[1] - 1),
      #              brik.range[2] / float(brik.dim[2] - 1) ]
      #
      # compute origin and corners
      #
      brik.axis = []
      if len(brik.dim) == 1:
         vx = brik.mapping[0] - brik.origin_corner
         brik.origin = brik.origin_corner + 0.5*vx
         brik.axis.append(vx)

      if len(brik.dim) == 2:
         vx = brik.mapping[0] - brik.origin_corner
         vy = brik.mapping[1] - brik.origin_corner
         brik.origin = brik.origin_corner + 0.5*vx + 0.5*vy
         brik.axis.append(vx)
         brik.axis.append(vy)

      if len(brik.dim) == 3:
         vx = brik.mapping[0] - brik.origin_corner
         vy = brik.mapping[1] - brik.origin_corner
         vz = brik.mapping[2] - brik.origin_corner
         brik.origin = brik.origin_corner + 0.5*vx + 0.5*vy + 0.5*vz
         brik.axis.append(vx)
         brik.axis.append(vy)
         brik.axis.append(vz)

   def read_grid_data(self,f,brik):
      if not brik:
         print '... skipped - grid_data without data block'
         self.skip_block(f)
         return
      
      brik.data = []

      brik.ndd = self.elements

      try:
         # Temporary simple implementation avoiding numerical python
         # pending resolution of the conflict in ordering conventions
         # Store data in punchfile ordering (first index varying
         # fastest)

         # this  may throw an exception
         dummy = brik.dim

         print 'Dim array',brik.dim
         print 'Recs',self.records
         print 'Elements',self.elements


         if self.records == 0:
            brik.data = None

         elif len(brik.dim) == 1:
            for x in range(brik.dim[0]):
               line = f.readline()
               line = line.split()
               for e in range(self.elements):
                  try:
                     brik.data.append(float(line[e]))
                  except ValueError:
                     print 'Warning ... Bad numeric data in punchfile, replaced with 999'
                     brik.data.append(999.0)

         elif len(brik.dim) == 2:
            for y in range(brik.dim[1]):
               if not y % 10:
                  print '....' + str(y),
               for x in range(brik.dim[0]):
                  line = f.readline()
                  line = line.split()
                  for e in range(self.elements):
                     try:
                        brik.data.append(float(line[e]))
                     except ValueError:
                        print 'Warning ... Bad numeric data in punchfile, replaced with 999'
                        brik.data.append(999.0)
            print ' '

         elif len(brik.dim) == 3:
            for z in range(brik.dim[2]):
               if not z % 10:
                  print '....' + str(z),
               for y in range(brik.dim[1]):
                  for x in range(brik.dim[0]):
                     line = f.readline()
                     line = line.split()
                     for e in range(self.elements):
                        try:
                           brik.data.append(float(line[e]))
                        except ValueError:
                           print 'Warning ... Bad numeric data in punchfile, replaced with 999'
                           brik.data.append(999.0)

            print ' '

##         brik.data = zeros(brik.dim,Float)

##         if len(brik.dim) == 1:
##            for x in range(brik.dim[0]):
##               brik.data[x]=float(f.readline())

##         elif len(brik.dim) == 2:
##            print 'dim',brik.dim
##            print 'reading ',brik.dim[1],':' 
##            for y in range(brik.dim[1]):
##               if not y % 10:
##                  print '....' + str(y),
##               for x in range(brik.dim[0]):
##                  brik.data[x,y]=float(f.readline())
##            print ' '

##         elif len(brik.dim) == 3:
##            print 'reading ',brik.dim[2],':' 
##            for z in range(brik.dim[2]):
##               if not z % 10:
##                  print '....' + str(z),
##               for y in range(brik.dim[1]):
##                  for x in range(brik.dim[0]):
##                     brik.data[x,y,z]=float(f.readline())
##            print ' '

      except AttributeError:

         # Irregular grid (it has no dim array)
         print 'No Dim'
         print 'Recs',self.records
         dim = [self.records]

         if self.records:
            for z in range(0,self.records):
               line = f.readline()
               line = line.split()
               for e in range(self.elements):
                  try:
                     brik.data.append(float(line[e]))
                  except ValueError:
                     print 'Warning ... Bad numeric data in punchfile, replaced with 999'
                     brik.data.append(999.0)
         else:
            brik.data = None

   def read_grid_points(self,f,brik):

      if not brik:
         print '... skipped - grid_points without data block'
         self.skip_block(f)
         return
      
      brik.points = []
      fac = 0.529177
      for i in range(0,self.records):
         txt = string.split(f.readline())
         t = []
         for j in range(0,self.elements):
            v = float(txt[j])
            v = v * fac
            t.append(v)
         brik.points.append(Vector(t))

##      d = [ dim[0]*3 ]
##      brik.points = zeros(d,Float)
      
##      for i in range(0,self.records):
##         txt = string.split(f.readline())
##         p = []
##         for j in range(0,self.elements):
##            self.points[i,j] = float(txt[j])

      #print 'grid points read',len(brik.points)

   def read_grid_indices(self,f,brik):
      if not brik:
         print '... skipped - grid_indices without data block'
         self.skip_block(f)
         return
      
      brik.indices = []
      for i in range(0,self.records):
         txt = string.split(f.readline())
         p = []
         brik.indices.append(p)
         for j in range(0,self.elements):
            p.append(int(txt[j]))

   def read_grid_mask(self,f,brik):
      if not brik:
         print '... skipped - grid_mask without data block'
         self.skip_block(f)
         return
      
      brik.mask = []
      for i in range(0,self.records):
         txt = string.split(f.readline())
         txt0 = txt[0] 
         brik.mask.append(int(txt0))

   def read_normal(self,f,obj):
      if self.debug:
         print self.name , self.records, self.index
      cnt = 0
      v = VibFreq(self.index)
      v.reference = self.fragment
      v.displacement = []
      for i in range(0,self.records):
         rr = string.split(f.readline())
         vec = Vector([ float(rr[1]) , float(rr[2]), float(rr[3]) ])
         v.displacement.append(vec)

      if len(self.normal) == 0:
         vs = VibFreqSet()
         if not self.fragment:
            raise AttributeError,"Error in read_normal: No molecular fragment to serve as a reference!"
            
         #vs.title = "vibrations of " + self.fragment.title
         vs.title = "vibrations of " + self.name
         vs.reference = self.fragment
         self.vfs = vs
         self.objects.append(vs)

      self.vfs.vibs.append(v)

      self.normal.append(v)
      #self.objects.append(v)
      return v

   def read_freq(self,f,obj):
      if self.debug:
         print self.name , self.records, self.index
      tt = f.readline()
      used = {}

      for v in self.normal:
         if v.index == self.index:
            v.freq = float(tt)
            t='v%-10.0f' % v.freq
            v.title = t
      return None

   def read_zmatrix_title(self,f,tt):
      if tt:
         tt.title=None
      for i in range(0,self.records):
         r = f.readline()
         r = string.strip(r)
         if tt:
            if( not tt.title):
               tt.title =  r
            else:
               tt.title =  tt.title + r

   def read_zmatrix_zatoms(self,f,tt):
      if not tt:
         print '.. skipped - zatoms  without zmatrix block'
         self.skip_block(tt)
         return
      
      cnt = 0
      fac = 0.529177
      tt.atom = []
      trans = string.maketrans('a','a')

      for i in range(0,self.records):

         print 'read i',i
         a = ZAtom()
         rr = string.split(f.readline())

         a.symbol = string.translate(rr[0],trans,string.digits)
         # we are not trying to impose uniqueness here but
         # pymol gets a modified name
         a.symbol = string.capitalize(a.symbol)
         a.name = rr[0]

         a.i1 = int(rr[1])
         a.i2 = int(rr[3])
         a.i3 = int(rr[5])

         a.conn = []
         a.ok = 1

         v1 = rr[2]
         v2 = rr[4]
         v3 = rr[6]
         
         a.coord = [0.,0.,0.]

         if a.i1 != -1:
            a.zorc = 'z'

            a.x_var = None
            a.y_var = None
            a.z_var = None

            if v1[:2] == '-#':
               a.r = 0.0
               a.r_var = v1[1:]
               a.r_sign = -1.0
            elif v1[:1] == '#':
               a.r = 0.0
               a.r_var = v1
               a.r_sign = 1.0
            else:
               a.r = float(v1)*fac
               a.r_var = None
               a.r_sign = 1.0

            if v2[:2] == '-#':
               a.theta = 0.0
               a.theta_var = v2[1:]
               a.theta_sign = -1.0
            elif v2[:1] == '#':
               a.theta = 0.0
               a.theta_var = v2
               a.theta_sign = 1.0
            else:
               a.theta = float(v2)
               a.theta_var = None
               a.theta_sign = 1.0
            
            if v3[:2] == '-#':
               a.phi = 0.0
               a.phi_var = v3[1:]
               a.phi_sign = -1.0
            elif v3[:1] == '#':
               a.phi = 0.0
               a.phi_var = v3
               a.phi_sign = 1.0
            else:
               a.phi = float(v3)
               a.phi_var = None
               a.phi_sign = 1.0

         else:
            a.zorc = 'c'

            if v2[:2] == '-#':
               a.coord[0] = 0.0
               a.x_var = v2[1:]
               a.x_sign = -1.0
            elif v2[:1] == '#':
               a.coord[0] = 0.0
               a.x_var = v2
               a.x_sign = 1.0
            else:
               a.coord[0] = float(v2)*fac
               a.x_var = None
               a.x_sign = 1.0

            if v3[:2] == '-#':
               a.coord[1] = 0.0
               a.y_var = v3[1:]
               a.y_sign = -1.0
            elif v3[:1] == '#':
               a.coord[1] = 0.0
               a.y_var = v3
               a.y_sign = 1.0
            else:
               a.coord[1] = float(v3)*fac
               a.y_var = None
               a.y_sign = 1.0

            if v1[:2] == '-#':
               a.coord[2] = 0.0
               a.z_var = v1[1:]
               a.z_sign = -1.0
            elif v1[:1] == '#':
               a.coord[2] = 0.0
               a.z_var = v1
               a.z_sign = 1.0
            else:
               a.coord[2] = float(v1)*fac
               a.z_var = None
               a.z_sign = 1.0

            #print v1,v2,v3,a.coord

         a.index = cnt
         cnt = cnt + 1
         tt.add_atom(a)

   def read_zmatrix_constants(self,f,tt):
      for i in range(self.records):
         v = ZVar()
         tt.constants.append(v)
         rr = string.split(f.readline())
         v.name = rr[0]
         v.value = float(rr[1])
         v.keys = " "
         v.constant = 1

   def read_zmatrix_variables(self,f,tt):
      for i in range(self.records):
         v = ZVar()
         tt.variables.append(v)
         rr = string.split(f.readline())
         v.name = rr[0]
         v.value = float(rr[1])
         v.keys = " "
         v.constant = 0

   def read_zmatrix_charges(self,f,tt):
      for i in range(0,self.records):
         r = f.readline()
         tt.atom[i].partial_charge = float(r)

   def read_matrix_title(self,f,tt):
      if self.debug:
         print 'read tit',self.records
      if tt:
         tt.title=None
      for i in range(0,self.records):
         r = f.readline()
         r = string.strip(r)
         if tt:
            if( not tt.title):
               tt.title =  r
            else:
               tt.title =  tt.title + r

   def read_dense_real_matrix(self,f,tt):

      if self.debug:
         print "records",self.records
         print "len of dim",len(self.dimensions)
         print "tt is ",tt
      tt.dimensions = self.dimensions
      tt.data = []
      for i in range(0,self.records):
         r = f.readline()
         tt.data.append(float(r))

   def read_pdc(self,f,obj):
      print 'read_pdc',obj
      tt = []
      for i in range(0,self.records):
         r = f.readline()
         tt.append(float(r))
      #obj.charge_sets.append(('PDC',tt))
      l = List('PDC')
      l.data = tt
      self.objects.append(l)

   def read_mulliken(self,f,obj):
      print 'read_mulliken',obj
      tt = []
      for i in range(0,self.records):
         r = f.readline()
         tt.append(float(r))
      l = List('Mulliken')
      l.data = tt
      self.objects.append(l)
      
   def read_lowdin(self,f,obj):
      print 'read_lowdin',obj
      tt = []
      for i in range(0,self.records):
         r = f.readline()
         tt.append(float(r))
      #obj.charge_sets.append(('Lowdin',tt))
      l = List('Lowdin')
      l.data = tt
      self.objects.append(l)


   def tidy_frag(self,tt):
      """Complete processing of fragment  after reading, define atom numbers
      """
      tt.reindex()

      # Remove function reference
      # It seems to limit our ability to copy the object using copy.deepcopy
      tt.tidy = None

   def tidy_z(self,tt):
      """Complete processing of Z-matrix after reading
      - Add constants to end of variables
      - Replace i1,i2,i3 and variable references with
        object pointers
      - Scale distance variables into angstroms
      """

      tt.variables = tt.variables + tt.constants
      tt.reindex()
      for a in tt.atom:

         if a.i1:
            a.i1 = tt.atom[a.i1-1]
         if a.i2:
            a.i2 = tt.atom[a.i2-1]
         if a.i3:
            a.i3 = tt.atom[a.i3-1]

         if a.zorc == 'z':
            if a.r_var:
               print a.r_var
               a.r_var = self.lookup_var(tt,a.r_var)
               a.r = a.r_var.value
               a.r_var.metric = 'd'

            if a.theta_var:
               a.theta_var = self.lookup_var(tt,a.theta_var)
               a.theta = a.theta_var.value
               a.theta_var.metric = 'a'

            if a.phi_var:
               a.phi_var = self.lookup_var(tt,a.phi_var)
               a.phi = a.phi_var.value
               a.phi_var.metric = 'a'

         else:
            if a.x_var:
               a.x_var = self.lookup_var(tt,a.x_var)
               a.coord[0] = a.x_var.value
               a.x_var.metric = 'd'

            if a.y_var:
               a.y_var = self.lookup_var(tt,a.y_var)
               a.coord[1] = a.y_var.value
               a.y_var.metric = 'd'

            if a.z_var:
               a.z_var = self.lookup_var(tt,a.z_var)
               a.coord[2] = a.z_var.value
               a.z_var.metric = 'd'

      # convert distances to angstroms
      fac = 0.529177
      for v in tt.variables:
         if v.metric == 'd':
            v.value = v.value * fac

      tt.calculate_coordinates()
      # Remove function reference
      # It seems to limit our ability to copy the object using copy.deepcopy
      tt.tidy = None

   def lookup_var(self,tt,var):
      ix = int(var[1:])
      print 'ix is',ix,len(tt.variables)

      return tt.variables[ix-1]

   def skip_block(self,f,obj=None):
      for i in range(0,self.records):
         junk = f.readline()

   def skip_rest_of_block(self,f):
      while 1:
         junk = f.readline()


if __name__ == "__main__":

   p = PunchReader()
   p.scan("../viewer/seq.pun")

   sys.exit(0)
   m = p.objects[0]
   #m.reindex()
   m.list()
   from Numeric import array
   m.array = array([m.data[0:3],m.data[3:6],m.data[6:]])
   print m.array
   from LinearAlgebra import inverse, eigenvectors
   #print inverse(m.array)
   eval,evec = eigenvectors(m.array)
   print eval
   print evec
