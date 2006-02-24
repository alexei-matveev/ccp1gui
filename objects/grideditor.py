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
"""A set of Tk widgets to edit the grid axes of Field object"""

import Pmw
import Tkinter
import copy
from interfaces.fpscale import *
from math import sqrt
import re
import viewer.help
from objects.field import Field
from viewer.debug import deb

class GridEditor(Pmw.MegaToplevel):

   """Toplevel widget to hold the grid editor

   initialisation args:
   command       a command to run for each update
   exitcommand   what to do on exit
   """

   def __init__(self, root, field, command=None,exitcommand=None):
      self.debug = 0
      self.root = root
      self.exitcommand = exitcommand
      Pmw.MegaToplevel.__init__(self, root, title="Grid Editor")
      w = GridEditorWidget(self.interior(),
                           field,
                           command=command,
                           exitcommand=self._close)
      w.pack(expand='yes',fill='both')
      root.update()
      self.reposition()
      
      #Associate widget with its help file
      viewer.help.sethelp(self,"Grid Editor")
      
   def _close(self,field):
      if self.exitcommand:
         self.exitcommand(field)
      self.destroy()
      
   def reposition(self):
      if self.debug:
         print 'GE self',self
         print 'GE self.root',self.root
         print 'Grideditor Geom',self.geometry()
      m = re.match('(\d+)x(\d+)\+(\d+)\+(\d+)',self.geometry())
      sx,sy,px,py = int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4))

      # Find position of master
      parent = self.root
      m = re.match('(\d+)x(\d+)\+(\d+)\+(\d+)',parent.geometry())
      msx,msy,mpx,mpy = int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4))
      self.geometry("%dx%d+%d+%d" % (sx,sy,mpx+msx+4,mpy+1))
      if self.debug:
         print 'master geom',    msx,msy,mpx,mpy
         print 'After',self.geometry()

class GridEditorWidget(Pmw.MegaWidget):

   """ Tk editor for changing the definition of a field"""
   def __init__(self, root, field, command=None,exitcommand=None,close_ok=1):
      #
      # nx, ny, nz
      # tx, ty, tz
      # rx, ry, rz
      # sx, sy, sz
      #
      self.root = root

      Pmw.MegaWidget.__init__(self, root)

      self.debug = 0

      self.command = command
      self.exitcommand = exitcommand
      self.field = field
      if self.debug:
         self.field.list()
      self.ref = copy.deepcopy(field)
      self.dynamic_update=0
      self.__createWidgets(close_ok)
      self.root = root
      self.dynamic_update=1
      self.transform()

      self.interior().bind("<ButtonPress-3>",
                  lambda e,s=self: s.RightMouseMenu(e))

      self.right_mouse_menu=Tkinter.Menu(root, tearoff=0)
      self.right_mouse_menu.add_command(label="MAPNET", command=self.wrt_mapnet)
      self.right_mouse_menu.add_command(label="GAMESS-UK", command=self.wrt_gamessuk)
      self.right_mouse_menu.add_command(label="Punch", command=self.wrt_punch)

   def RightMouseMenu(self,event):
      self.right_mouse_menu.post(event.x_root, event.y_root)

   def __createWidgets(self,close_ok):

      hull = self.component('hull')
      self.xtran_widget = FPScale(hull,
                                  command=self.update,
                                  low=-10,high=10,label_text='X Tran')
      self.xtran_widget.pack(side='top')
      self.ytran_widget = FPScale(hull,
                                  command=self.update,
                                  low=-10,high=10,label_text='Y Tran')
      self.ytran_widget.pack(side='top')

      self.ztran_widget = FPScale(hull,
                                  command=self.update,
                                  low=-10,high=10,label_text='Z Tran')
      self.ztran_widget.pack(side='top')

      self.xrot_widget = FPScale(hull,
                                 command=self.update,
                                 low=-90,high=90,label_text='X Rot')
      self.xrot_widget.pack(side='top')

      self.yrot_widget = FPScale(hull,
                                 command=self.update,
                                 low=-90,high=90,label_text='Y Rot')
      self.yrot_widget.pack(side='top')

      self.zrot_widget = FPScale(hull,
                                 command=self.update,
                                 low=-90,high=90,label_text='Z Rot')
      self.zrot_widget.pack(side='top')

      self.xscale_widget = FPScale(hull,
                                   command=self.update,
                                   low=0.1,high=10,value=1.0,
                                   label_text='X Scale')
      self.xscale_widget.pack(side='top')

      self.yscale_widget = FPScale(hull,
                                   command=self.update,
                                   low=0.1,high=10,value=1.0,
                                   label_text='Y Scale')
      self.yscale_widget.pack(side='top')

      self.zscale_widget = FPScale(hull,
                                   command=self.update,
                                   low=0.1,high=10,value=1.0,
                                   label_text='Z Scale')
      self.zscale_widget.pack(side='top')

      self.nptframe =  Tkinter.Frame(hull)

      #increment = 5,
##      self.nx_widget = Pmw.Counter(
##         self.nptframe,
##         labelpos = 'w', label_text = 'nx',
##         orient = 'horizontal',
##         entryfield_entry_width = 6,
##         entryfield_validate = { 'validator' : 'integer',
##                                 'min'       : 1,
##                                 'max'       : 1001},
##         entryfield_value = self.field.dim[0])
##      self.ny_widget = Pmw.Counter(
##         self.nptframe,
##         labelpos = 'w', label_text = 'ny',
##         increment = 5, orient = 'horizontal',
##         entryfield_entry_width = 6,
##         entryfield_validate = { 'validator' : 'integer',
##                                 'min'       : 1,
##                                 'max'       : 1001},
##         entryfield_value = ny)

##      self.nz_widget = Pmw.Counter(
##         self.nptframe,
##         labelpos = 'w', label_text = 'nz',
##         increment = 5, orient = 'horizontal',
##         entryfield_entry_width = 6,
##         entryfield_validate = { 'validator' : 'integer',
##                                 'min'       : 1,
##                                 'max'       : 1001},
##         entryfield_value = nz )



      if len(self.field.dim) > 1:
         ny = self.field.dim[1]
      else:
         ny = 1

      if len(self.field.dim) > 2:
         nz = self.field.dim[2]
      else:
         nz = 1

      v = { 'validator' : 'integer', 'min'       : 1, 'max'       : 1001}
      self.nx_widget = Pmw.EntryField(
         self.nptframe,
         labelpos = 'w', label_text = 'nx',
         entry_width = 6,
         validate = v, 
         value = self.field.dim[0])
      self.ny_widget = Pmw.EntryField(
         self.nptframe,
         labelpos = 'w', label_text = 'ny',
         entry_width = 6,
         validate = v, 
         value = ny)
      self.nz_widget = Pmw.EntryField(
         self.nptframe,
         labelpos = 'w', label_text = 'nz',
         entry_width = 6,
         validate = v, 
         value = nz)

      self.nx_widget.pack(expand='yes',fill='x',side='left')
      self.ny_widget.pack(expand='yes',fill='x',side='left')
      self.nz_widget.pack(expand='yes',fill='x',side='left')

      self.nx_widget.component('entry').bind('<Return>',self.transform)
      self.ny_widget.component('entry').bind('<Return>',self.transform)
      self.nz_widget.component('entry').bind('<Return>',self.transform)

      self.nptframe.pack(side='top')
      
      if close_ok:
         self.buttonframe =  Tkinter.Frame(hull)
         self.buttonframe.pack(side='top')
         f = self.buttonframe
      else:
         f = self.nptframe


      self.transform_button = Tkinter.Button(f,
                                command = lambda s=self:s.transform(),
                                text = 'Transform')
      self.transform_button.pack(side='left')

      if close_ok:
         self.ok_button = Tkinter.Button(self.buttonframe,
                                         command = lambda s=self:s.__close(),
                                         text = 'Close and Save')

         self.ok_button.pack(side='left')      

      self.reset_button = Tkinter.Button(f,
                                         command = lambda s=self:s.__reset(),
                                         text = 'Reset')

      self.reset_button.pack(side='left')      
      if close_ok:
         self.cancel_button = Tkinter.Button(self.buttonframe,
                                             command = lambda s=self:s.__cancel(),
                                             text = 'Close and Cancel')
         self.cancel_button.pack(side='left')

   def update(self):
      if self.debug:
         deb('update: flag='+str(self.dynamic_update))
      if self.dynamic_update:
         self.transform()
         
   def wrt_gamessuk(self):
      self.transform()
      self.field.wrt_gamessuk()

   def wrt_mapnet(self):
      self.transform()
      self.field.wrt_mapnet()

   def wrt_punch(self):
      self.transform()
      self.field.wrt_punch()

   def __close(self):
      # make sure all changes are reflected in the object
      self.transform()
      # release reference to the reference object
      self.ref = None
      if self.exitcommand:
         self.exitcommand(self.field)
      self.destroy()

   def __cancel(self):
      self.__reset()
      self.__close()
      
   def __reset(self):

      # restore old data
      self.field.origin = self.ref.origin
      self.field.axis = self.ref.axis
      self.field.dim = self.ref.dim

      # reset the widgets

      self.xtran_widget.set(0.0)
      self.ytran_widget.set(0.0)
      self.ztran_widget.set(0.0)

      self.xscale_widget.set(1.0)
      self.yscale_widget.set(1.0)
      self.zscale_widget.set(1.0)

      self.xrot_widget.set(0.0)
      self.yrot_widget.set(0.0)
      self.zrot_widget.set(0.0)

      self.nx_widget.setentry(self.field.dim[0])

      if len(self.field.dim) > 1:
         ny = self.field.dim[1]
      else:
         ny = 1
      self.ny_widget.setentry(ny)

      if len(self.field.dim) > 2:
         nz = self.field.dim[2]
      else:
         nz = 1
      self.nz_widget.setentry(nz)

      self.transform()
      
   def transform(self,callback=1):

       xtran = self.xtran_widget.get()
       ytran = self.ytran_widget.get()
       ztran = self.ztran_widget.get()

       xscale = self.xscale_widget.get()
       yscale = self.yscale_widget.get()
       zscale = self.zscale_widget.get()

       xrot = self.xrot_widget.get()
       yrot = self.yrot_widget.get()
       zrot = self.zrot_widget.get()

       nx = int(self.nx_widget.get())
       ny = int(self.ny_widget.get())
       nz = int(self.nz_widget.get())

       if self.debug:
           txt =     'Parameters: tran '+str([xtran, ytran, ztran])+'\n'
           txt = txt+'           scale'+str([xscale, yscale, zscale])+'\n'
           txt = txt+'             rot'+str([xrot, yrot, zrot])+'\n'
           txt = txt+'            dims'+str([nx,ny,nz])
           deb(txt)
       #
       # Add new dimensions if required
       # - initially unit length vectors
       # probably should also shift origin by half of the length
       #

       self.field.dim[0] = nx

       # create a new Y axis 
       vx = self.field.axis[0]
       if ny > 1 and len(self.field.dim) == 1:
          if self.debug:
             print 'add y dim'
          self.field.dim.append(ny)
          #print vx
          #print self.field.x*(vx),self.field.y*(vx)
          #print self.field.x.cross(vx),self.field.y.cross(vx)
          if abs(self.field.x*(vx)) > 0.99:
             newaxis = self.field.y.cross(vx)
          else:
             newaxis = self.field.x.cross(vx)
          self.field.axis.append(newaxis.normal())
          #print 'new axis',self.field.axis
          #self.zscale_widget.enable()

       elif len(self.field.dim) > 2:
          self.field.dim[2] = nz

       # create a new Z axis 
       if nz > 1 and len(self.field.dim) == 2:
          if self.debug:
             print 'add z dim'
          vy = self.field.axis[1]
          self.field.dim.append(nz)
          newaxis = vy.cross(vx)
          self.field.axis.append(newaxis.normal())
          #self.yscale_widget.enable()
       elif len(self.field.dim) > 1:
          self.field.dim[1] = ny

       # Reduce dimensionality...
       if len(self.field.dim) == 3 and nz == 1:
          if self.debug:
             print 'lose z dim'
          # remove z axis
          self.field.axis = self.field.axis[0:2]
          self.field.dim = self.field.dim[0:2]
          
       if len(self.field.dim) == 2 and ny == 1:
          # remove y axis
          if self.debug:
             print 'lose y dim'
          self.field.axis = self.field.axis[0:1]
          self.field.dim = self.field.dim[0:1]

       self.field.transform(self.ref,
                            translate=(xtran,ytran,ztran),
                            scale=(xscale,yscale,zscale),
                            rotate=(10.0*xrot,10.0*yrot,10.0*zrot))

       if len(self.field.dim) <3:
          #self.zscale_widget.disable()
          pass
       if len(self.field.dim) <2:
          #self.yscale_widget.disable()
          pass

       # the callback e.g. to enable the result to be displayed
       if self.command and callback:
          if self.debug:
             deb('   calling transform callback')
          self.command(self.field)


if __name__ == "__main__":

    root=Tkinter.Tk()
    f = Field(nd=2)
    print f
    w = GridEditorWidget(root,f)
    w.pack()
    root.mainloop()
