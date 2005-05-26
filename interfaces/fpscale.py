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
import Tkinter 
import Pmw
 
class FPScale(Pmw.MegaWidget):
    """ A Megawidget containing a scale and an entry, allowing
    direct entry or slider control
    """
 
    def __init__(self, parent = None, **kw):

        # Define the megawidget options.
        optiondefs = (
	    ('command',   None,   Pmw.INITOPT),
	    ('low',          0,   Pmw.INITOPT),
	    ('high',       100,   Pmw.INITOPT),
	    ('value',     None,   Pmw.INITOPT),
        )
        self.defineoptions(kw, optiondefs)

        # Initialise base class (after defining options).
        Pmw.MegaWidget.__init__(self, parent)
 
        # Create the components.
        interior = self.interior()
 
        # Create the label component.
        self.label = self.createcomponent('label',
                                          (), None,
                                          Tkinter.Label, interior,
                                          width = 8,
                                          borderwidth = 2,
                                          relief = 'sunken')

        self.label.pack(side='left')
        
        # Create the scale component.
        self.scale = self.createcomponent('scale',
                                          (), None,
                                          Tkinter.Scale, interior,
                                          command = self._doScale,
                                          resolution = 0.01,
                                          length = 200,
                                          from_ = self['low'],
                                          to = self['high'],
                                          orient = 'horizontal',
                                          showvalue = 0)
        self.scale.pack(side='left')

        # Create the entry component.
        self.entry = self.createcomponent('entry',
                                          (), None,
                                          Tkinter.Entry, interior,
                                          width = 8,
                                          borderwidth = 2,
                                          relief = 'sunken')

        self.entry.bind('<Return>', lambda e,s = self: s._doEntry(e) )

        self.entry.pack(side='left')
 
        value = self['value']
        if value is not None:
            self.scale.set(value)
 
        # Check keywords and initialise options.
        self.initialiseoptions()

    def disable(self):
        self.entry.configure(state='disabled')
        self.scale.configure(state='disabled')

    def enable(self):
        self.entry.configure(state='normal')
        self.scale.configure(state='enables')

    def set(self,value):
        ''' Set the value '''
        from_ = self.scale.cget('from')
        if value < float(from_):
            self.scale.configure(from_=value)
        to = self.scale.cget('to')
        if value > float(to):
            self.scale.configure(to=value)
	self.scale.set(value)
	self.entry.delete(0,Tkinter.AtEnd())
	self.entry.insert(0,str(value))
        pass

    def get(self):
        ''' Get the value from the widget'''
        return float(self.scale.get())

    def _doScale(self, valueStr):
	self.entry.delete(0,Tkinter.AtEnd())
	self.entry.insert(0,self.scale.get())
        if self['command']:
            self['command']()

    def _doEntry(self,event):
        valueStr = self.entry.get()
        value = float(valueStr)
        to    = self.scale.cget('to')
        from_ = self.scale.cget('from')
        if float(value) < float(from_):
            self.scale.configure(from_=value)
        if float(value) > float(to):
            self.scale.configure(to=value)

	self.scale.set(value)
        if self['command']:
            self['command']()
        
Pmw.forwardmethods(FPScale, Tkinter.Scale, 'scale')
