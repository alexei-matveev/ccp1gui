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
"""Generic classes used for user parameter input.

These objects serve as containers for the widgets (in this from
Tkinter) which are used to set the control parameters for the
calculations. In all case the name of parameter(s) to be set
are passed as arguments.

"""

import Pmw
import Tkinter
import tkFileDialog

class Tool:
    """base tool initialisation

    Store the editor as the editor attribute of the tool
    and add the tool to the list of tools managed by the editor
    """
    def __init__(self,editor,**kw):
        self.editor = editor
        self.parent = editor.interior()
        self.editor.tools.append(self)
        self.debug = 1

    def GetWidget(self):
        return self.widget


class IntegerTool(Tool):
    """Input of a single integer"""
    def __init__(self,editor,parameter,label_text,mini=None,maxi=None,**kw):
        apply(Tool.__init__, (self,editor), kw)
        self.parameter = parameter
        self.label_text = label_text
        value   = self.editor.calc.get_parameter(parameter)
        self.packparent = None

        # Will need a callback here to change the variable value
        if mini and maxi:
            v = {'validator' : 'integer' , 'min' : mini , 'max' : maxi}
        elif mini:
            v = {'validator' : 'integer' , 'min' : mini }
        elif maxi:
            v = {'validator' : 'integer' , 'max' : maxi }
        else:
            v = {'validator' : 'integer' }

        self.widget = Pmw.Counter(
            self.parent, 
            labelpos = 'w', label_text = self.label_text,
            increment = 1,
            entryfield_entry_width = 6,
            entryfield_value = value,
            entryfield_validate = v)

        self.UpdateWidget()

    def ReadWidget(self):
        value = self.widget.get()
        self.editor.calc.set_parameter(self.parameter,int(value))
        return value

    def UpdateWidget(self):
        value = self.editor.calc.get_parameter(self.parameter)
        self.widget.setentry(value)

    def SetParent(self,packparent):
        self.packparent = packparent

    def Pack(self,side=None):
        self.widget.pack(in_=self.packparent,side=side)

    def Forget(self):
        self.widget.forget()


class FloatTool(Tool):
    """Input a floating point number"""
    def __init__(self,editor,parameter,label_text,mini=None,maxi=None, **kw):
        apply(Tool.__init__, (self,editor), kw)
        self.parameter = parameter

        self.packparent=None
        
        if mini and maxi:
            v = {'validator' : 'real' , 'min' : mini , 'max' : maxi}
        elif mini:
            v = {'validator' : 'real' , 'min' : mini }        
        elif maxi:
            v = {'validator' : 'real' , 'max' : maxi }        
        else:
            v = {'validator' : 'real' }

        if(label_text):
            self.widget = Pmw.EntryField(
                self.parent,
                labelpos = 'w',
                label_text = label_text,
                validate = v,
                value = self.editor.calc.get_parameter(self.parameter))
        else:
            self.widget = Pmw.EntryField(
                self.parent,
                labelpos = 'w',
                validate = v,
                value = self.editor.calc.get_parameter(self.parameter))

    def ReadWidget(self):
        value = self.widget.get()
        self.editor.calc.set_parameter(self.parameter,float(value))
        return value

    def UpdateWidget(self):
        value = self.editor.calc.get_parameter(self.parameter)
        self.widget.setentry(value)

    def SetParent(self,packparent):
        self.packparent = packparent

    def Pack(self,side=None):
        self.widget.pack(in_=self.packparent,side=side)

    def Forget(self):
        self.widget.forget()

class BooleanTool(Tool):
    """ Control of a boolean variable (stored as integer) using a Tkinter Checkbutton widget """
    def __init__(self,editor,parameter,label_text,command=None,**kw):
        apply(Tool.__init__, (self,editor), kw)
        value   = self.editor.calc.get_parameter(parameter)

        if self.debug:
            print 'Initial parameter',parameter,value


        self.packparent=None
        #self.widget = Tkinter.Checkbutton(self.parent)
        self.widget = Pmw.LabeledWidget(self.parent,
                                        labelpos='w',
                                        label_text=label_text)
        self.button =  Tkinter.Checkbutton(self.widget.interior())
        self.button.pack(side='left')
        self.variable = Tkinter.BooleanVar()
        self.button.config(variable=self.variable)
        self.parameter = parameter
        
        if command:
            self.button.configure(command=command)
        else:
            #self.button.configure(command=lambda opt,s=self: s.ReadWidget())
            self.button.configure(command=lambda s=self: s.ReadWidget())

        self.UpdateWidget()
        
    def ReadWidget(self):
        """The parameter is given an integer value"""
        if self.variable.get():
            value = 1
        else:
            value = 0        
        self.editor.calc.set_parameter(self.parameter,value)
        if self.debug:
            print 'BooleanTool.ReadWidget',self.parameter,value
        return value

    def UpdateWidget(self):
        value = self.editor.calc.get_parameter(self.parameter)
        if value:
            self.button.select()
        else:
            self.button.deselect()

    def SetParent(self,packparent):
        self.packparent = packparent

    def Pack(self,side=None):
        self.widget.pack(in_=self.packparent,side=side)

    def Forget(self):
        self.widget.forget()

class SelectOptionTool(Tool):
    """A tool for selecting one of several mutually exclusive options
    """
    def __init__(self,editor,parameter,label_text,items,command=None,**kw):
        apply(Tool.__init__, (self,editor), kw)
        self.label_text = label_text
        self.parameter = parameter
        self.packparent = None

        #Get the default value of the parameter
        self.default=self.editor.calc.get_parameter(self.parameter)
        if self.debug:
            print "default is: "+str(self.default)

        self.widget = Pmw.OptionMenu(
                    self.parent,
                    labelpos = 'w',
                    label_text = self.label_text,
                    items = items,
                    initialitem=self.default)
        if command:
            self.widget.configure(command=command)
        else:
            self.widget.configure(command=lambda opt,s=self: s.ReadWidget())

    def SetItems(self,items):
        self.widget.setitems(items)

    def ReadWidget(self):
        value = self.widget.getvalue()
        self.editor.calc.set_parameter(self.parameter,value)
        return value

    def UpdateWidget(self):
        value = self.editor.calc.get_parameter(self.parameter)
        self.widget.setvalue(value)
        
    def SetParent(self,packparent):
        self.packparent = packparent

    def Pack(self,side=None):
        self.widget.pack(in_=self.packparent,side=side)

    def Forget(self):
        self.widget.forget()


class TitleTool(Tool):
    """ Special text string control to set the calculation title """
    def __init__(self,editor,**kw):
        apply(Tool.__init__, (self,editor), kw)
        title = self.editor.calc.get_title()

        self.widget = Pmw.EntryField(
            self.parent,
            entry_width = 50,
            labelpos = 'w', label_text = 'Title',
            value = title)
    def ReadWidget(self):
        title = self.widget.get()
        self.editor.calc.set_title(title)
        return title
    
    def RefreshWidget(self):
        title = self.editor.calc.get_title()
        self.widget.setentry(title)

class TextFieldTool(Tool):
    """A tool for single line text entry
    """
    def __init__(self,editor,parameter,label_text,command=None,width=None,**kw):
        apply(Tool.__init__, (self,editor), kw)

        value = self.editor.calc.get_parameter(parameter)
        self.parameter=parameter
        self.packparent = None
        self.command = command

        self.widget = Pmw.EntryField(
            self.parent,
            labelpos = 'w',
            label_text = label_text,
            value = value)

        # change our width if necessary
        if width:
            self.widget.configure( entry_width = width )
        
        if self.command:
            self.widget.configure(command=self.command)
            self.widget.component('entry').bind("<Leave>",self.command)
        else:
#            self.widget.configure(command=lambda opt,s=self: s.ReadWidget())
            self.widget.configure(command=lambda s=self: s.ReadWidget())
            self.widget.component('entry').bind("<Leave>",self.ReadWidget)

    def ReadWidget(self,arg=None):
        value = self.widget.getvalue()
        self.editor.calc.set_parameter(self.parameter,value)
        return value

    def UpdateWidget(self):
        value = self.editor.calc.get_parameter(self.parameter)
        self.widget.setvalue(value)

    def SetParent(self,packparent):
        self.packparent = packparent

    def Pack(self,side=None):
        self.widget.pack(in_=self.packparent,side=side)

    def Forget(self):
        self.widget.forget()

class FileTool(Tool):
    """A tool for single line text entry of a file name
      including a browser.
    """
    def __init__(self,editor,parameter,label_text,command=None,
                 filetypes=None,action=None,**kw):
        apply(Tool.__init__, (self,editor), kw)

        self.value = self.editor.calc.get_parameter(parameter)
        self.parameter=parameter
        self.command = command
        self.filetypes = filetypes
        self.action = action
        self.browsevalue = None

        self.widget = Tkinter.Frame(self.parent,borderwidth=5)

        self.entry = Pmw.EntryField(
            self.widget,
            labelpos = 'w',
            label_text = label_text,
            entry_width = '10',
            value = self.value)

        if self.command:
            self.entry.configure(command=self.command)
            self.entry.component('entry').bind("<Leave>",self.command)
        else:
            self.entry.configure(command=lambda opt,s=self: s.ReadWidget())
            self.entry.component('entry').bind("<Leave>",self.ReadWidget)
        self.entry.pack(side="left")

        self.button = Tkinter.Button(self.widget,text="Browse...",command=self.FindFile)
        self.button.pack(side="left", padx=10)

    def FindFile(self):
        oldfile = self.value
        if self.action == "open":
            if self.filetypes:
                self.browsevalue=tkFileDialog.askopenfilename(initialfile=self.value,
                                                          filetypes=self.filetypes)
            else:
                self.browsevalue=tkFileDialog.askopenfilename(initialfile=self.value)
        else: # elif self.action == "save":
            if self.filetypes:
                self.browsevalue=tkFileDialog.asksaveasfilename(initialfile=self.value,
                                                                filetypes=self.filetypes)
            else:
                self.browsevalue=tkFileDialog.asksaveasfilename(initialfile=self.value)
        if len(self.browsevalue) == 0:
            self.browsevalue = oldfile
        if self.command:
            self.command()
        else:
            self.entry.setvalue(self.browsevalue)
            self.editor.calc.set_parameter(self.parameter,self.browsevalue)
        
    def ReadWidget(self,arg=None):
        self.value = self.entry.getvalue()
        self.editor.calc.set_parameter(self.parameter,self.value)
        return self.value

    def UpdateWidget(self):
        self.value = self.editor.calc.get_parameter(self.parameter)
        self.entry.setvalue(self.value)

    def SetParent(self,packparent):
        self.packparent = packparent

    def Pack(self,side=None):
        self.widget.pack(in_=self.packparent,side=side)

    def Forget(self):
        self.widget.forget()

class ChangeDirectoryTool(Tool):
    """A tool for changing the working directory of a calculation run under control of the gui
    """
    def __init__(self,editor,parameter,label_text,command=None,**kw):
        apply(Tool.__init__, (self,editor), kw)

        value = self.editor.calc.get_parameter(parameter)
        self.parameter=parameter
        self.command=command

        self.widget = Tkinter.Frame(self.parent,borderwidth=5)

        self.entry = Pmw.EntryField(
            self.widget,
            labelpos = 'w',
            label_text = label_text,
            value = value)

        self.entry.pack(side="left")

        self.button = Tkinter.Button(self.widget,text="Browse...",command=self.BrowseDirectory)
        self.button.pack(side="left", padx=10)
        if self.command:
            self.entry.configure(command=self.command)
            self.entry.component('entry').bind("<Leave>",self.command)
        else:
#            self.entry.configure(command=lambda opt,s=self: s.ReadWidget())
            self.entry.configure(command=lambda s=self: s.ReadWidget())
            self.entry.component('entry').bind("<Leave>",self.ReadWidget)

    def BrowseDirectory(self):
        # askdirectory() cant create new directories so use asksaveasfilename is used instead
        # and the filename  is discarded - also fixes problem with no askdirectory in Python2.1
        olddir = self.editor.calc.get_parameter(self.parameter)
        dummyfile=str(self.editor.calc.get_parameter("job_name"))+'.in'
        lendummy=(len(dummyfile)+1)
        path=tkFileDialog.asksaveasfilename(initialfile=dummyfile, initialdir=olddir)
        if len(path) == 0:
            self.entry.setvalue(olddir)
        else:
            value=path[0:-lendummy]
            self.entry.setvalue(value)
        if self.command:
            self.command()
        else:
            self.ReadWidget()
        
    def ReadWidget(self,arg=None):
        value = self.entry.getvalue()
        self.editor.calc.set_parameter(self.parameter,value)
        return value

    def UpdateWidget(self):
        value = self.editor.calc.get_parameter(self.parameter)
        self.entry.setvalue(value)

    def SetParent(self,packparent):
        self.packparent = packparent

    def Pack(self,side=None):
        self.widget.pack(in_=self.packparent,side=side)

    def Forget(self):
        self.widget.forget()


class IntegerAndBooleanTool(Tool):

    """Combined Boolean/Integer input
    The Integer control is only presented if the checkbutton is selected.
    The boolean is stored in the parameter dictionary as 0,1

    """
    def __init__(self,editor,bool_parameter,int_parameter,bool_label_text,int_label_text,mini=None,maxi=None,**kw):
        apply(Tool.__init__, (self,editor), kw)

        self.bool_parameter = bool_parameter
        self.int_parameter = int_parameter
        value   = self.editor.calc.get_parameter(self.int_parameter)

        # Will need a callback here to change the variable value
        if mini and maxi:
            v = {'validator' : 'integer' , 'min' : mini , 'max' : maxi}
        elif mini:
            v = {'validator' : 'integer' , 'min' : mini }
        elif maxi:
            v = {'validator' : 'integer' , 'max' : maxi }
        else:
            v = {'validator' : 'integer' }

        self.frame = Tkinter.Frame(self.parent)

        self.widget = self.frame
        self.int_widget = Pmw.Counter(
            self.frame, 
            labelpos = 'w', label_text = int_label_text,
            increment = 1,
            entryfield_entry_width = 6,
            entryfield_value = value,
            entryfield_validate = v)

        self.bool_widget = Pmw.LabeledWidget(
            self.frame,
            labelpos='w',
            label_text=bool_label_text)

        self.button =  Tkinter.Checkbutton(self.bool_widget.interior())
        self.button.pack(side='left')
        self.variable = Tkinter.BooleanVar()
        self.button.config(variable=self.variable)
        self.button.configure(command=self.__display_int_widget)
        self.bool_widget.pack(side='left')
        if self.debug:
            print 'Done int/bool tool',self.int_parameter

    def __display_int_widget(self):
        value = self.variable.get()
        if value:
            self.int_widget.pack(side='left')
        else:
            self.int_widget.forget()

    def ReadWidget(self):
        value = self.int_widget.get()
        self.editor.calc.set_parameter(self.int_parameter,int(value))
        if self.variable.get():
            value2 = 1
        else:
            value2 = 0        
        self.editor.calc.set_parameter(self.bool_parameter,value2)
        if self.debug:
            print 'IntegerAndBooleanTool.ReadWidget',self.bool_parameter,value2, \
                  self.int_parameter,value,

    def UpdateWidget(self):
        value = self.editor.calc.get_parameter(self.int_parameter)
        self.int_widget.setentry(value)

        value = self.calc.get_parameter(self.bool_parameter)
        self.bool_widget.setentry(value)

        
class MenuAndBooleanTool(Tool):
    """Combined Boolean/Menu input
    The menu is only displayed if the checkbutton is selected.
    The boolean is stored in the parameter dictionary as 0,1
    """
    def __init__(self,editor,bool_parameter,menu_parameter,
                 bool_label_text,menu_label_text,
                 menu_items,bool_command=None,menu_command=None,**kw):
        apply(Tool.__init__, (self,editor), kw)

        self.bool_parameter = bool_parameter
        self.menu_parameter = menu_parameter
        self.bool_label_text = bool_label_text
        self.menu_label_text = menu_label_text
        self.menu_items = menu_items
        self.bool_command = bool_command
        self.menu_command = menu_command
        
        self.menu_default=self.editor.calc.get_parameter(self.menu_parameter)
        #value = self.editor.calc.get_parameter(self.int_parameter)
        
        self.widget = Tkinter.Frame(self.parent)

        self.bool_widget = Pmw.LabeledWidget(self.widget,
                                             labelpos='w',
                                             label_text=self.bool_label_text)
        
        self.button =  Tkinter.Checkbutton(self.bool_widget.interior())
        self.button.pack(side='left')
        self.bool_variable = Tkinter.BooleanVar()
        self.button.config(variable=self.bool_variable)
        self.button.configure(command=self.__display_menu_widget)
        self.bool_widget.pack(side='left')

        self.menu_widget = Pmw.OptionMenu(self.widget,
                                          labelpos = 'w',
                                          label_text = self.menu_label_text,
                                          items = self.menu_items,
                                          initialitem=self.menu_default)

        if self.bool_command:
            self.button.configure(command=self.bool_command)
        else:
            self.button.configure(command=self.ReadWidget)

        if self.menu_command:
            self.menu_widget.configure(command=self.menu_command)
        else:
            self.menu_widget.configure(command = self.ReadWidget)


    def __display_menu_widget(self):
        value = self.bool_variable.get()
        if value:
            self.menu_widget.pack(side='left')
        else:
            self.menu_widget.forget()
        
    def ReadWidget(self):
        """The parameter is given an integer value"""
        if self.bool_variable.get():
            value = 1
        else:
            value = 0        
        self.editor.calc.set_parameter(self.bool_parameter,value)

        value2 = self.menu_widget.getvalue()
        self.editor.calc.set_parameter(self.menu_parameter,value2)

    def UpdateWidget(self):
        value = self.editor.calc.get_parameter(self.boolean_parameter)
        if not value:
            self.button.deselect()
        else:
            self.button.select()
            value2 = self.editor.calc.get_parameter(self.menu_parameter)
            self.menu_widget.setvalue(value2)

    def SetParent(self,packparent):
        self.packparent = packparent

    def Pack(self,side=None):
        self.widget.pack(in_=self.packparent,side=side)

    def Forget(self):
        self.widget.forget()


class MenuCounterTool(Tool):
    """A menu that brings up a counter if the selected menu item is changeable
    with a counter.
    """
    
    def __init__(self,editor,parameter1,label_text1,items,
                 parameter2,label_text2,command,mini=None,maxi=None,**kw):
        apply(Tool.__init__, (self,editor), kw)

        self.parameter1 = parameter1
        self.label_text1 = label_text1
        self.items = items
        self.parameter2 = parameter2
        self.label_text2 = label_text2

        if mini and maxi:
            v = {'validator' : 'integer' , 'min' : mini , 'max' : maxi}
        elif mini:
            v = {'validator' : 'integer' , 'min' : mini }
        elif max:
            v = {'validator' : 'integer' , 'max' : maxi }
        else:
            v = {'validator' : 'integer' }
        
        self.widget = Pmw.LabeledWidget(self.parent,
                                        labelpos='w',
                                        label_text = self.label_text1)
        self.widget.pack(side='left')
        
        self.firstmenu = Pmw.OptionMenu(self.widget.interior(),
                                        items = self.items,
                                        command = command
                                        )
        
        self.firstmenu.pack(side='left',padx=10)

        self.menucounter = Pmw.Counter(self.widget.interior(),
                                      labelpos='w',
                                      label_text = self.label_text2,
                                      increment = 1,
                                      entryfield_entry_width = 20,
                                      entryfield_validate = v,
                                      entryfield_value = self.editor.calc.get_parameter(self.parameter2)
                                      )

    def ShowCounter(self):
        self.menucounter.pack(side='left',padx=10)

    def HideCounter(self):
        self.menucounter.forget()
             
    def ReadWidget(self):
        value1 = self.firstmenu.getvalue()
        self.editor.calc.set_parameter(self.parameter1,value1)
        value2 = self.menucounter.getvalue()
        self.editor.calc.set_parameter(self.parameter2,value2)

#Haven't been able to check the UpdateWidget method yet so carfeul if you use it!
    def UpdateWidget(self):
        value1 = self.editor.calc.get_parameter(self.parameter1)
        self.firstmenu.setvalue(value1)
        value2 = self.editor.calc.get_parameter(self.parameter2)
        self.menucounter.setvalue(value2)
        
class MenuCounterMenuTool(Tool):
    """A menu that brings up an additional counter or menu tools if the selected menu item
    requires it.
    """
    def __init__(self,editor,parameter1,label_text1,items,
                 parameter2,label_text2,
                 parameter3,label_text3,items3,
                 command,mini=None,maxi=None,**kw):
        apply(Tool.__init__, (self,editor), kw)

        self.parameter1 = parameter1
        self.label_text1 = label_text1
        self.items = items
        self.parameter2 = parameter2
        self.label_text2 = label_text2
        self.parameter3= parameter3
        self.label_text3=label_text3
        self.items3=items3

        if mini and maxi:
            v = {'validator' : 'integer' , 'min' : mini , 'max' : maxi}
        elif mini:
            v = {'validator' : 'integer' , 'min' : mini }
        elif max:
            v = {'validator' : 'integer' , 'max' : maxi }
        else:
            v = {'validator' : 'integer' }
        
        self.widget = Pmw.LabeledWidget(self.parent,
                                        labelpos='w',
                                        label_text = self.label_text1)
        self.widget.pack(side='left')
        
        self.firstmenu = Pmw.OptionMenu(self.widget.interior(),
                                        items = self.items,
                                        command = command)
        
        self.firstmenu.pack(side='left',padx=10)

        self.menucounter = Pmw.Counter(self.widget.interior(),
                                      labelpos='w',
                                      label_text = self.label_text2,
                                      increment = 1,
                                      entryfield_entry_width = 20,
                                      entryfield_validate = v,
                                      entryfield_value = self.editor.calc.get_parameter(self.parameter2))
        
        self.secondmenu = Pmw.OptionMenu(self.widget.interior(),
                                        items = self.items3)

    def ShowCounter(self):
        self.menucounter.pack(side='left',padx=10)

    def HideCounter(self):
        self.menucounter.forget()

    def ShowMenu(self):
        self.secondmenu.pack(side='left',padx=10)

    def HideMenu(self):
        self.secondmenu.forget()
             
    def ReadWidget(self):
        value1 = self.firstmenu.getvalue()
        self.editor.calc.set_parameter(self.parameter1,value1)
        value2 = self.menucounter.getvalue()
        self.editor.calc.set_parameter(self.parameter2,value2)
        value3= self.secondmenu.getvalue()
        self.editor.calc.set_parameter(self.parameter3,value3)


#The following tools still need work

class CommmentTool(Tool):
    """ Tool to input a number of lines of comments - defaults to 1, but could be many
    """
    def __init__(self,editor,lines=None,**kw):
        apply(Tool.__init__, (self,editor), kw)

        # Set the height of the box
        if lines:
            self.lines = lines
        else:
            self.lines = 1

        self.width = 50
            
        comment = self.editor.calc.get_comment()

        self.widget = Tkinter.Frame(self.parent)
        self.label = Tkinter.Label(self.widget,text="Comment: ")
        self.label.pack(side="left")
        self.text = Tkinter.Text(self.widget,height=self.lines, width=self.width )
        self.text.pack(side="left")

        self.text.insert('0.0',comment)

    def ReadWidget(self):
        end = str(self.lines)+"."+str(self.width)
        comment = self.text.get('0.0',end)
        self.editor.calc.set_comment(comment)
        
    def RefreshWidget(self):
        title = self.editor.calc.get_comment()
        end = str(self.lines)+"."+str(self.width)
        self.text.insert('0.0',end,comment)

class TextTool(Tool):
    """ A tool for multi-line text input
    """
    def __init__(self,editor,parameter,label_text,**kw):

        apply(Tool.__init__, (self,editor), kw)
        text = self.editor.calc.get_parameter(parameter)

        self.parameter = parameter
        
        self.widget = Pmw.ScrolledText(
            self.parent,
            labelpos = 'w',
            label_text = label_text,
            borderframe = 1)
        self.widget.settext(text)
 
    def ReadWidget(self):
        txt = self.widget.get()
        length = len(txt)
        if length == 1:
            txt = ""
        elif txt[length-2] == '\n':
            txt = txt[:length-1]
        self.editor.calc.set_parameter(self.parameter,txt)

    def RefreshWidget(self):
        self.widget.settext(self.editor.calc.get_parameter(self.parameter))

class AtomSelectionTool(Tool):

    """A text widget for entry of a list of atom numbers

    Also allows import/export from the atom selection from the graph
    widget.

    """

    def __init__(self,editor,parameter,label_text,**kw):

        apply(Tool.__init__, (self,editor), kw)

        self.parameter = parameter
        
        self.group = Pmw.Group(self.parent,tag_text=label_text)
        self.widget = self.group
        self.text_widget = Pmw.ScrolledText(
            self.group.interior(),
            labelpos = 'nw', 
            usehullsize = 1,
            hull_width  = 400,
            hull_height = 100,
            borderframe = 1)

        atom_nos = self.editor.calc.get_parameter(self.parameter)

        if self.debug:
            print 'Atom nos',atom_nos, type(atom_nos)
            
        if self.editor.graph:
            atom_labs = self.editor.graph.atom_names(atom_nos)
        else:
            atom_labs=""
            for a in atom_nos:
                atom_labs = atom_labs + " " + str(a)

        self.text_widget.settext(atom_labs)

        self.text_widget.pack(expand=1,fill='x')

        self.import_button = Tkinter.Button(self.group.interior())
        self.import_button.config(command=self.__import)
        self.import_button.config(text='Import from Selection')
        self.import_button.pack(expand='yes',anchor='w',padx=10,side='left')

        self.export_button = Tkinter.Button(self.group.interior())
        self.export_button.config(command=self.__export)
        self.export_button.config(text='Export to Selection')
        self.export_button.pack(expand='yes',anchor='w',padx=10,side='left')

    def __import(self):
        """Transfer the atom selection from the molecular graphics code
        to the text window
        """
        # Get the selection as a list of atoms
        mol_name = self.editor.calc.get_input('mol_name')
        atoms = self.editor.graph.get_selection(mol_name)
        if self.debug:
            print 'atoms', atoms
        # Store it
        self.editor.calc.set_parameter(self.parameter,atoms)
        # Present a list of atom numbers
        txt = self.editor.graph.atom_names(atoms,exclude_dummies=1)
        if self.debug:
            print 'txt', txt
        self.text_widget.settext(txt)      

    def __export(self):
        """ inverse of above"""
        self.ReadWidget()
        atoms = self.editor.calc.get_parameter(self.parameter)
        mol_name = self.editor.calc.get_input('mol_name')
        self.editor.graph.set_selection(mol_name,atoms)

    def ReadWidget(self):
        txt = self.text_widget.get()
        length = len(txt)
        if self.debug:
            print length, txt
        if length == 1:
            txt = ""
        elif txt[length-2] == '\n':
            txt = txt[:length-1]

        # This will check that the qm region (stored as a character
        # string) is valid, if so it is stored
        #try:
        mol = self.editor.calc.get_input('mol_obj')
        if self.editor.graph:
            a = self.editor.graph.map_names(mol,txt)
        else:
            a = []
            for t in txt:
                a.append(int(t))
        self.editor.calc.set_parameter(self.parameter,a)
        #except:
        #   self.gui.error.configure(message_text = "Bad Atom Name in QM Region input")
        #   self.gui.error.activate()

    def UpdateWidget(self):
        txt = self.editor.graph.atom_names(editor.calc.get_parameter(self.parameter))
        if self.debug:
            print 'update atom selection tool',txt
        self.text_widget.settext(txt)
        
#This button isn't used in the GUI yet so make sure it works as expected.

class RadioSelectTool(Tool):
    
    def __init__(self,editor,parameter,label_text,items,**kw):
        apply(Tool.__init__, (self,editor), kw)
        self.label_text = label_text
        self.parameter = parameter
        self.items = items # not sure if this good or no.

        self.widget = Pmw.RadioSelect(
                    self.parent,
                    buttontype = 'radiobutton',
                    orient = 'vertical',
                    labelpos = 'w',
                    label_text = self.label_text,
                    command = self.ReadWidget
                    )
        self.widget.pack(padx = 10, pady = 10) # might have to add side & expand?

        #add the individual buttons here
        for button in self.items.keys(): 
            self.widget.add(button)
        self.widget.invoke(0)# slight problem here as makes a call but as is default should be o.k.

    def ReadWidget(self,tag): #REM tag is name(key) of particular radiobutton
        value = self.items[tag]
        print "key and value are: " + str(tag) + " " + str(value)
#        self.editor.calc.set_parameter(self.parameter,value)

#    def UpdateWidget(self): #- not done yet as this widget isn't needed yet.
#        value = self.calc.get_parameter(self.parameter)
#        self.widget.setvalue(value)
