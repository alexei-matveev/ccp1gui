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

from interfaces.calc import *
from viewer.initialisetk import initialiseTk

class Editor(Pmw.MegaToplevel):

   """A simple editor class for editing text data.
   """

#   def __init__(self,parent,title=None,data=None,**kw):
   def __init__(self,parent,title=None,data=None,directory=None,**kw):


       self.parent = parent
       self.data = data
       self.inputtitle = title
       self.user_directory=directory

       Pmw.MegaToplevel.__init__(self, parent, title="Calculation Input Editor" )
       initialiseTk(parent)
       
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
                                          label_text=self.inputtitle)
       self.text.pack(fill='both',expand=1)
       
       self.__settext()

        
   def __settext(self):
       """ Fill the widget with the input text
       """
       if self.data == None:
           self.Quit()
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
           initialdir = self.user_directory,
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
   
   """

   def __init__(self,parent,calc,calced,**kw):

       self.parent = parent
       self.calc = calc
       self.calced = calced

       # Use the job_name if one set, else the calc name
       try:
          self.edtitle = self.calc.get_parameter("job_name")
       except KeyError, e:
          self.edtitle= self.calc.get_name()

       #Get the data 
       self.input = self.calc.get_input('input_file')

       #Initialise the base editor class
       Editor.__init__(self,self.parent,self.edtitle,self.input)
                               
       #self.__settext()

        
               
   def Quit(self,**kw):
       """Close this window"""
       self.calced.inputeditor = None
       apply(Pmw.MegaToplevel.destroy,(self,), **kw)
       
   def Save(self):
       """Make this the input
       """
       input = self.text.get()
       self.calc.set_input('input_file',input)
       
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
