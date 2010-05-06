"""
Try and use the Scientific Vector class, otherwise fall back on our own.

The vector code originally resided in the objects/symdet.py supplied
by Ulf Ekstrom from Patrick Norman's group, and has been extended by Jens.
"""
import copy
import math

def isVector(x):
   return hasattr(x,'is_vector')

class CCP1GUI_Vector:

   is_vector=1

   def __init__(self, x = [0,0,0], y = None, z = None):
      if y != None:
         self.r = [x,y,z]
      else:
         self.r = copy.copy(x)

   def __abs__(self):
      return math.sqrt(self.abs2())

   def __add__(self,v):
      return CCP1GUI_Vector(self[0]+v[0],self[1]+v[1],self[2]+v[2])

   def __copy__(self, memo = None):
      return self
   __deepcopy__ = __copy__
   
   def __div__(self, c):
      if isVector(c):
         raise TypeError("Can't divide by a vector")
      else:
         c=float(c)
         return CCP1GUI_Vector(self[0]/c,self[1]/c,self[2]/c)
            
   def __rdiv__(self, c):
      raise TypeError("Can't divide by a vector")

   def __getitem__(self, i):
      return self.r[i]

   def __getstate__(self):
      return self.r

   def __len__(self):
      return 3

   def __mul__(self,c):
      if isVector(c):
         return self.dot(c)
      else:
         return self.scaled(c)

   def __rmul__(self,c):
      return self.scaled(c)

   def __neg__(self):
      return -1*self

   def __repr__(self):
      return "(%.6f, %.6f, %.6f)" % (self.r[0],self.r[1],self.r[2])

   def __str__(self):
      return "CCP1GUI_Vector: (%.6f, %.6f, %.6f)" % (self.r[0],self.r[1],self.r[2])

   def __sub__(self,v):
      return CCP1GUI_Vector(self[0]-v[0],self[1]-v[1],self[2]-v[2])



   def abs2(self):
      return self[0]*self[0] + self[1]*self[1] + self[2]*self[2]

   def cross(self,v):
      return CCP1GUI_Vector(self[1]*v[2] - self[2]*v[1],
                    self[2]*v[0] - self[0]*v[2],
                    self[0]*v[1] - self[1]*v[0])

   def dist(self,p):
      return abs(self-p)

   def dist2(self,p):
      return (self-p).abs2()

   def dot(self,v):
      return self[0]*v[0] + self[1]*v[1] + self[2]*v[2]

   def length(self):
      return math.sqrt(self.abs2())

   def normal(self):
      return self.scaled(1.0/math.sqrt(self.abs2()))

   def scaled(self,c):
      c=float(c)
      return CCP1GUI_Vector(c*self[0],c*self[1],c*self[2])


try:
   from  Scientific.Geometry.VectorModule import Vector
except ImportError:
   Vector = CCP1GUI_Vector
   
