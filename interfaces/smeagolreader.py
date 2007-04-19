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
# Read a data file output by Smeagol

# import python modules
import re
import string
import os.path
import math

# import external modules
# From Konrad Hinsens scientific python
import Scientific.Geometry.VectorModule
import vtk # We create the VTK objects directly

# import internal modules
import objects.zmatrix
import objects.field
from viewer.rc_vars import rc_vars
from objects.periodic import name_to_element

class SmeagolReader:
   """
      Load objects from the files generated by Smeagol
   """
   def __init__( self ):

      print "instantiating smeagol reader"

      self.debug=0

      self.objects = [] # List to hold objects read from the files


   def read( self, smgfile, ftype=None):
       """ Main read method - this just works out which reader to call
           either by having been given a file type, otherwise it works
           it out from the file suffix.
       """


       # Get filename and directory
       directory,name = os.path.split( smgfile )
       name,ext = os.path.splitext( name )
       ext = ext[1:] # remove dot

       if not ftype:
          #Determine filetype from extension
          ftype = ext

       print "ftype is ",ftype
          
       if ( ftype == "RHO" ):
          self.read_RHO( smgfile )
       elif ( ftype == "fdf" ):
          self.read_FDF( smgfile,directory,name,ext )
       elif ( ftype == "ANI" ):
          self.read_ANI( smgfile,directory,name,ext )
       else:
          print "No SMEAGOL reader for filetype %s !" % ftype

   def get_objects(self):
      """ Return any objects we have or None if there aren't any"""

      if len(self.objects):
         return self.objects
      else:
         return None
           

   def read_RHO(self,smgfile):
       """ Read in the data from an RHO file.
       
           Format of the file is expected to be:
           
           1: Z lattice vector - float(x) float(y) float(z)
           2: Y lattice vector - float(x) float(y) float(z)
           3: X lattice vector - float(x) float(y) float(z)
           4: zdim ydim xdim nspin - number of mesh points in each direction
                                     plus the number of spins - if nspin=2 then
                                     we are creating 2 datasets
           5:data...               - list of data points as floats
       """
       
       print "smeagolreader: reading RHO file %s" % smgfile

       # Derive the title from the filename
       filename = os.path.basename( smgfile )
       filename = string.split( filename, "." )[0]

       # Open the file
       try:
          f = open( smgfile, 'r')
       except IOError,e:
          print "Error opening file in read_RHO in smeagolreader !"
          return 1
              
       # Read in the first 4 lines containing the grid definition
       # and the dimensions & spin
       try:
           zline = string.strip( f.readline() )
           yline = string.strip( f.readline() )
           xline = string.strip( f.readline() )
           dimline = string.strip( f.readline() )
       except:
           print "Error reading file %s in smeagolreader.read_grid_axis !" % f
           return 1

       # Set up the Z lattice vector
       zLatVec = self.__get_latvec( zline )
       if not zLatVec:
          print "No Z Lattice Vector!"
          return 1

       # Set up the Y lattice vector
       yLatVec = self.__get_latvec( yline )
       if not yLatVec:
          print "No Z Lattice Vector!"
          return 1

       # Set up the X lattice vector
       xLatVec = self.__get_latvec( xline )
       if not xLatVec:
          print "No X Lattice Vector!"
          return 1


       # Get the dimensions & the number of spins
       fields = string.split( dimline )
       if ( len( fields ) != 4 ):
          print "Problem with dimension line in smeagolreader read_grid_dimensions!"
          return
       else:
          try:
             xDim,yDim,zDim,nspin = fields[0:4]
             xDim,yDim,zDim,nspin = int(xDim), int(yDim), int(zDim), int(nspin)
          except  Exception,e:
             print "Problem reading dimensions in smeagolreader read_grid_dimensions!"
             print e
             return 1

       #Work out how many data points we've got
       npoints = xDim * yDim * zDim

       # Now loop over the spins & read in the data points.
       # We assume that the origin is at the centre of the grid and that the data has been written
       # out starting at the origin, going to the edge and then being translated back
       # by the unit cell vector and writing out the remaining points back to the origin
       
       # Need to allocate memory for the data
       #data = []
       #for i in range(npoints):
       #   data.append(0)

       scalars = vtk.vtkFloatArray()
       scalars.SetNumberOfValues( npoints )

       for spin in range(nspin):
          print "Reading data points from file..."
          for z in range(zDim):
             if ( z < (zDim/2) ):
                zt = z + (zDim/2)
             else:
                zt = z - (zDim/2)
             for y in range(yDim):
                if ( y < (yDim/2) ):
                   yt = y + (yDim/2)
                else:
                   yt = y - (yDim/2)
                for x in range(xDim):
                   if ( x < (xDim/2) ):
                      xt = x + (xDim/2)
                   else:
                      xt = x - (xDim/2)

                   #if not count % 10000:
                   #   print '...',
                      
                   line = f.readline()
                   if not line:
                      print "ERROR reading Data in smeagolreader!"
                      return None
                   
                   try:
                      dat = float(line)
                   except:
                      print "Bad Data in smeagol reader!: %s " % line
                      dat = float(-999999)
                      
                   offset = (zt * xDim * yDim) + (yt * xDim) + xt
                   #data[offset] = dat
                   scalars.SetValue( offset, dat )
                   
          #End of loop over z,x,y

          if ( nspin == 2):
             title = filename + str(spin)
          else:
             title = filename

          # Create the field object
          smgfield = self.create_vtkfield( title, scalars, zLatVec, yLatVec, xLatVec, \
                                      zDim, yDim, xDim )
          # Add the field to the list of objects
          if self.debug:
             print "smeagolreader appending field:"
             smgfield.list()
          self.objects.append( smgfield )
          

   def __get_latvec( self, line ):
      """ Take a line read in from the RHO file and return the
          relevant lattice vector as a list of floats
          REM: we need to convert from Bohrs -> Angstroms so we do
          this here.
      """

      bohr_2_angs = 0.529177
      
      try:
         x,y,z = string.split( line )
         x,y,z = float(x), float(y), float(z)
         x,y,z = x* bohr_2_angs, y* bohr_2_angs, z* bohr_2_angs
         LatVec = [ x, y, z ]

         return LatVec
      
      except Exception,e:
         print "Error reading Lattic Vector in smeagolreader !"
         print e
         return None

#   def create_vtkfield( self, title, data, zLatVec, yLatVec, xLatVec, zDim, yDim, xDim ):
   def create_vtkfield( self, title, scalars, zLatVec, yLatVec, xLatVec, zDim, yDim, xDim ):
      """ Create a field object that holds the data in a vtkImageData object
      """

      vtkdata = vtk.vtkImageData()
      vtkdata.SetDimensions( xDim, yDim, zDim )

      # work out the spacing
      # asume the grid origin is always at 0.0, 0.0, 0.0
      origin = [ 0.0, 0.0, 0.0 ]
      xlen = math.sqrt( math.pow( (origin[0] - xLatVec[0]), 2) + \
                        math.pow( (origin[1] - xLatVec[1]), 2) + \
                        math.pow( (origin[2] - xLatVec[2]), 2) )    
      xspacing = float( xlen/xDim )
      ylen = math.sqrt( math.pow( (origin[0] - yLatVec[0]), 2) + \
                        math.pow( (origin[1] - yLatVec[1]), 2) + \
                        math.pow( (origin[2] - yLatVec[2]), 2) )     
      yspacing = float( ylen/yDim )
      zlen = math.sqrt( math.pow( (origin[0] - zLatVec[0]), 2) + \
                        math.pow( (origin[1] - zLatVec[1]), 2) + \
                        math.pow( (origin[2] - zLatVec[2]), 2) )
      zspacing = float( zlen/zDim )
      vtkdata.SetSpacing( xspacing, yspacing, zspacing )

      #scalars = vtk.vtkFloatArray()
      #npoints = zDim * yDim * xDim
      #scalars.SetNumberOfValues( npoints )
      #for i in range( npoints ):
         # What on earth is the vtkIdType??? (1st arg)
         #scalars.SetValue( i, data[i] )
      #   scalars.InsertNextValue( data[i] )
         
      vtkdata.GetPointData().SetScalars(scalars)
      vtkdata.SetScalarTypeToFloat()

      # Work out the origin (assume it's at the centre of the grid)
      origin = [ -xlen / 2, -ylen / 2 , -zlen / 2 ]
      vtkdata.SetOrigin( origin )

      # Instantiate the field object
      field = objects.field.Field()
      field.title = title
      field.vtkdata = vtkdata

      # Need to add axis, dimensions & origin as these are required by the CutSlice visulaliser
      # NB: May need to use Scientific Vector? as currently these are only lists
      field.dim = [ xDim, yDim, zDim ]
      field.x = Scientific.Geometry.VectorModule.Vector( xLatVec )
      #field.axis.append( field.x )
      field.axis[0] = field.x 
      field.y = Scientific.Geometry.VectorModule.Vector( yLatVec )
      #field.axis.append( field.y )
      field.axis[1] = field.y
      field.z = Scientific.Geometry.VectorModule.Vector( zLatVec )
      #field.axis.append( field.z )
      field.axis[2] = field.z 
      #field.origin =Scientific.Geometry.VectorModule.Vector( origin )
      #jmht HACK - need to think about this
      field.origin =Scientific.Geometry.VectorModule.Vector( [0.,0.,0.] )

      

      return field


   def read_FDF( self, fdffile,directory,name,ext ):
      """ Dirty hack to read in an fdf file """

      fd = open( fdffile, 'r' )

      line = fd.readline()
      startCoordRe = re.compile("^%block AtomicCoordinatesAndAtomicSpecies")
      endCoordRe = re.compile("^%endblock AtomicCoordinatesAndAtomicSpecies")
      while line:
         #print "read line ",line
         line = line.strip()
         if startCoordRe.match( line ):
            mol = objects.zmatrix.Zmatrix()
            mol.title = name
            mol.name = name

            #print "got start coord"
            line = fd.readline().strip()
            while not endCoordRe.match( line ):
               atom = objects.zmatrix.ZAtom()
               fields = line.split()
               #print "fields ",fields
               x = float( fields[0] )
               y = float( fields[1] )
               z = float( fields[2] )
               atom.coord = [ x, y, z ]
               atom.name = fields[5]
               atom.symbol = name_to_element( atom.name )
               mol.atom.append( atom )
               
               # Read in the next line for the coordinate loop
               line = fd.readline().strip()

            # Get here when finished reading coords
            fd.close()
            mol.connect()
            #self.update_from_object(mol)
            #self.quick_mol_view([mol])
            #self.append_data(mol)
            self.objects.append( mol )
            # hack set rc_vars
            rc_vars['smeagol_input'] = fdffile
            return

         # read in the next line for the first while loop
         line = fd.readline()


# This is nicked from main - just a quick hack until the file readers
# have been updated
   def read_ANI(self,anifile,directory,name,ext):
      """ Read in cartesian coordinates in XMOL .xyz file format.
      The xyz format can contain multiple frames so we need to
      check if we have come to the end of one frame and need to
      start another
      The optional sequence flag indicates if we should create a
      ZmatrixSequence of the molecules in the file
      """
      
      print "reading ANI file"
      if 1:
         ZmatSeq = objects.zmatrix.ZmatrixSequence()
      else:
         models = []

      file = open( anifile,'r' )
            
      finished = 0
      line = file.readline()
      while( not finished ): # loop to cycle over all the frames
         words = string.split(line)

         # First word specifies the number of atoms
         try:
            natoms = int(words[0])
         except:
            finished = 1
            break

         model = objects.zmatrix.Zmatrix()
         model.title = name
         model.name = None

         line = file.readline() # First line is a comment so ignore it
         for i in range(natoms):
            line = file.readline()
            
            # Make sure we got something to read...
            if not line:
               print "Error reading coordinates in rdxyz!"
               finished = 1
               break
                    
            # Check we are not at the end of the current frame
            words = string.split(line)
            if ( len( words ) != 4 ):
               print "Error reading coordinates in rdxyz!"
               print "Offending line is: %s" % line
               break # jump out of for loop and start next cycle
            
            atsym = words[0]
            try:
               x = float(words[1])
               y = float(words[2])
               z = float(words[3])
               a = objects.zmatrix.ZAtom()
               a.coord = [x,y,z]
               a.symbol = name_to_element( words[0] )
               a.name = a.symbol + string.zfill(i+1,2)
               model.atom.append(a)
            except:
               print "Error reading coordinates in rdxyz!"
               print "Offending line is: %s" % line
               break # jump out of for loop and start next cycle

         if 1:
            ZmatSeq.add_molecule(model)
         else:
            #self.connect_model(model)
            #self.quick_mol_view([model])
            #self.append_data(model)
            #models.append( model )
            pass
                
         # Go back to top of while loop with next line
         line = file.readline()

      if 1:
         ZmatSeq.connect()
         # Name the sequence after the first molecule
         ZmatSeq.name = ZmatSeq.frames[0].name
         self.objects.append(ZmatSeq)
         return
      else:
         pass
         #if len( models ) == 0:
         #   return None
         #else:
         #   return models




if ( __name__ == "__main__" ):
   #fname = "/c/qcg/jmht/share/codes/ccp1gui/smeagol/Benz_shift.RHO.vtk"
   fname = "/c/qcg/jmht/share/codes/ccp1gui/smeagol/Benz.RHO.short"
   fttype = 'RHO'
   s = SmeagolReader()
   s.read( fname,ftype=fttype )
    
