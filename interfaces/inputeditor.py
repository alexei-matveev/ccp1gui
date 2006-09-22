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
import Pmw
import Tkinter
import tkFileDialog
import os

from interfaces.calc import *
from viewer.initialisetk import initialiseTk

class Editor(Pmw.MegaToplevel):

   """A simple editor class for editing text data.
   """

#   def __init__(self,parent,title=None,data=None,directory=None,**kw):
   def __init__(self,parent,**kw):

       self.parent = parent

       if kw.has_key('title'):
          self.edtitle = kw['title']
       else:
          self.edtitle = 'No Title'
       if kw.has_key('directory'):
          self.directory = kw['directory']
       else:
          self.directory = os.getcwd()
       if kw.has_key('data'):
          self.data = kw['data']
       else:
          self.data = None

       Pmw.MegaToplevel.__init__(self, self.parent, title=self.edtitle )
       initialiseTk(self.parent)
       
       # Ensure that when the user kills us with the window manager we behave as expected
       self.userdeletefunc( func = self.Quit )
       #self.usermodaldeletefunc( func = self.Quit )
                            
       #Add the menu bar
       # Create the Balloon.
#       self.balloon = Pmw.Balloon(self.interior())
       self.balloon = Pmw.Balloon(self.parent)

       # Create and pack the MenuBar.
       menuBar = Pmw.MenuBar(self.interior(),
                             hull_relief = 'raised',
                             hull_borderwidth = 1,
                             balloon = self.balloon)
       menuBar.pack(fill = 'x')
       self.menuBar = menuBar
       
       # Add some buttons to the MenuBar.
       menuBar.addmenu('File', 'Save this file or exit')
#       menuBar.addmenuitem('File', 'command', balloonHelp='Save this file',
       menuBar.addmenuitem('File', 'command', 'Save this file',
                           command = self.Save,
                           label = 'Save')
       menuBar.addmenuitem('File', 'command', 'Save this file as...',
                           command = self.SaveAs,
                           label = 'Save As')
       menuBar.addmenuitem('File', 'separator')
       menuBar.addmenuitem('File', 'command', 'Quit the editor',
                           command = self.Quit,
                           label = 'Exit')
       
       self.text = Pmw.ScrolledText(self.interior(),
                                          labelpos = 'n',
                                          label_text=self.edtitle)
       self.text.pack(fill='both',expand=1)
       
       self.settext()

        
   def settext(self):
       """ Fill the widget with the input text
       """
       if self.data == None:
           pass
       else:
           self.text.clear()
           for a in self.data:
               self.text.insert('end',a)
               self.text.configure(text_state = 'normal')

   def Save(self):
      """
         Need to overwrite this method
      """
      self.SaveAs()
      return

   def SaveAs(self):
       """Save this version  as a named file.
       """
       savefilename = tkFileDialog.asksaveasfilename(
           initialdir = self.directory,
           filetypes=[("All Files","*.*")])
       if len(savefilename) == 0:
           return
       else:
           savefile = open(savefilename,"w")
           text = self.text.get()
           savefile.write(text)
           savefile.close()
           return
               
   def Quit(self,**kw):
       """Close this window"""
       #self.calced.inputeditor = None
       apply(Pmw.MegaToplevel.destroy,(self,), **kw)
       


class InputEd(Editor):

   """A simple text editor to edit the inputs to calculations.
   
      We can be passed a keyword "onsave" that is a command to run when the
      user hits "save" - this should set anything up requried by the calculation
      editor and reutrn the filname that we are to write out.
   """

   def __init__(self,parent,calc,calced,**kw):

       
       Editor.__init__( self, parent, **kw )
       
       self.parent = parent
       self.calc = calc
       self.calced = calced

       if kw.has_key('onsave'):
          self.onsave = kw['onsave']
       else:
          self.onsave = None
          
       #Get the data
       if not self.data:
          self.data = self.calc.get_input('input_file')

       # Use the job_name if one set, else the calc name
       try:
          self.edtitle = self.calc.get_parameter("job_name")
       except KeyError, e:
          self.edtitle= self.calc.get_name()

       self.settext()

        
               
   def Quit(self,**kw):
       """Close this window"""
       self.calced.inputeditor = None
       apply(Pmw.MegaToplevel.destroy,(self,), **kw)
       
   def Save(self):
       """Make this the input
       """

       input = self.text.get()
       self.calc.set_input('input_file',input)
       
       # Check if there is any command we should run on saving
       if self.onsave:
          try:
             filename = self.onsave()
          except Exception,e:
             self.calced.Error("Error running onsave commmand in InputEditor!\n%s" % e )
             return

       if not filename:
          try:
             filename = str(self.calc.get_parameter("job_name"))+".in"
          except KeyError, e:
             filename = str(self.calc.get_name())+".in"
          
       inputfile = open(filename,"w")
       inputfile.write(input)
       inputfile.close()
       return



if __name__ == "__main__":
   root=Tk()
   editor=Editor(root)
   root.mainloop()
