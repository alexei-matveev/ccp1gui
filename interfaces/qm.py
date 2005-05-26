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
#######################################################################
#
# QM specialisations for Calc and CalcEd classes 
#
########################################################################

from calc    import *
from calced  import *

class QMCalc(Calc):
    '''Quantum chemistry specifics.'''
    def __init__(self,**kw):
        apply(Calc.__init__,(self,),kw)

class QMCalcEd(CalcEd):

    def __init__(self,root,calc,graph,**kw):
        '''Initialise a QM calculation editor. First initialise the base 
           class and then do our own stuff.'''
        apply(CalcEd.__init__, (self,root,calc,graph), kw)
        #Jens' addition of calc menu
        self.CreateCalcMenu(self.menu)
        self.CreateEditMenu(self.menu)
        self.CreateViewMenu(self.menu)
        self.tasks = []
        self.theories = {}
        self.basissets = []


    def __CreateStatusFrame(self,parent):
        '''Create a small frame to present status unformation '''
        frame = Tkinter.Frame(parent)
        frame.pack(expand=1, fill='x')
        frame.l1 = Tkinter.Label(frame,text='No job status to report')
        frame.l2 = Tkinter.Label(frame,text='')
        frame.l1.pack(side='left',expand=1, fill='x')
        frame.l2.pack(side='left',expand=1, fill='x')
        return frame

    def Reload(self,**kw):
        """Reload the structure, same as base class except basis
        manager is updated"""
        apply(CalcEd.Reload, (self,), kw)        
        try:
            self.basis_manager.new_molecule()
            self.basis_tool.RefreshWidget()
        except AttributeError:
            pass

    def StoreEditButton(self,button):
        self.texteditbutton = button
        self.textedit.deactivate()
        print 'texteditbutton pressed ',self.texteditbutton

    def AddPage(self,pagename,pagelabel=""):
        '''Add entries for all the pages you require. The actual creation of
            the pages is handled by the CreatePage method and the methods it
            calls.'''
        if pagelabel=="":
            pagelabel=pagename
        self.notebook.add(pagename,tab_text=pagelabel)


    def TaskPage(self,page,action):
        pass

    def TaskPage2(self,page,action):
        '''The task page aims to specify the objective of the calculation 
        In the QM case we overload to include basis set and theory on this page
        '''
        labels = []

        # Sort out RUNTYPE

#        runtype = self.calc.get_task()
        runtype = self.calc.get_parameter("task")        
        if action == Create:
           page.goal = Pmw.OptionMenu(page,
                      labelpos = 'w', label_text = 'Runtype',
                      command = self.LowerTaskPage,
                      items = self.tasks, 
                      initialitem = runtype)
           page.goal.pack(expand='yes',fill='x')
           labels = labels + [page.goal]
        elif action == Lower:
#           self.calc.set_task(page.goal.getcurselection())
           self.calc.set_parameter("task",page.goal.getcurselection())

        # Sort out THEORY
 
        if action == Create:
           page.theory = Pmw.OptionMenu(page,
                        labelpos = 'w', label_text = 'Theory',
                        items = self.theories[runtype],
                        initialitem = self.calc.get_theory())
           page.theory.pack(expand='yes',fill='x')
           labels = labels + [page.theory]
        elif action == Lower:
           self.calc.set_theory(page.theory.getcurselection())
        # action == Create or Lower or Raise
        page.theory.setitems(self.theories[self.calc.get_parameter("task")])

        # Sort out BASIS

        if action == Create:
           page.basis = Pmw.OptionMenu(page,
                       labelpos = 'w', label_text = 'Basis',
                       items = self.basissets,
                       initialitem = self.calc.get_input("basis"))
           page.basis.pack(expand='yes',fill='x')
           labels = labels + [page.basis]
        elif action == Lower:
           self.calc.set_input("basis",page.basis.getcurselection())

        Pmw.alignlabels(labels)

