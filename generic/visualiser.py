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
"""Visualisation base class

The derived classes store the data associated with visualisation
of a single data object and an interactive dialog widget which
controls the representation. e.g. MoleculeVisualiser
"""

import Pmw
import Tkinter
import re
import math
import copy
import viewer.help
import string
import time

# From Konrad Hinsens scientific python
import Scientific.Geometry.VectorModule

from SimpleDialog import SimpleDialog
import tkColorChooser
from tkFileDialog import *
from objects.field import Field
from objects.grideditor import GridEditorWidget
from interfaces.dl_poly import Dl_PolyHISTORYReader
from viewer.debug import deb

VDW_RADII = 10
COV_RADII = 11


NULL  = 0
BUILT = 1


class Colourer:
    """A class to hold information about how to colour an object
    Vaild schemes are:
    Uniform : a single colour
    +ve -ve : two colours for positive & negative values
    ????    : Any object that we can colour by
    """
    def __init__(self,graph):

        # Need the graph object
        self.graph = graph

        # The colouring scheme in opreation - this could be
        # Uniform, "+ve -ve", or the name of a scheme/object to colour by
        self.scheme = None
        
        # The name of the colouring scheme in operation
        self.cmap_name=None
        
        # For uniform colouring we use the plus_colour
        self.plus_colour   =  None
        self.plus_rgb = None

        # For orbital colouring need a -ve colour
        self.minus_colour=None
        self.minus_rgb=None

        # The lookup table we are using
        self.lut=None

        # An object that we want to colour by
        self.cmap_obj=None

        # The min and max values that the colouring will be
        # mapped between
        self.cmap_low = None
        self.cmap_high = None

        # Determine whether to display a scalar bar of the colourmap
        self.show_colourmap_actor = None


    def get_lut(self):
        """Return the lookuptable"""
        
        self.lut = self.graph.get_cmap_lut(self.cmap_name)
        return self.lut

    def get_value(self,value):
        """Return an attribute of the object if it exists"""
        if hasattr(self,value):
            return getattr(self,value)
        else:
            return None
        
    def set_value(self,vtype,value):
        """Set an attribute of the colourobject"""
        setattr(self,vtype,value)

    def cmap_by_object(self):
        """Convenience function - return True if colourmapping by
        an object (checks if the object can be found)"""

        # Can only check if not uniform or +ve-ve & that there is
        # an object
        if ( self.scheme != 'Uniform' and self.scheme != '+ve -ve' ):
            if self.cmap_obj:
                return True
        return False


class ColourChooser:
    """Implements widgets to colour an object.
    It acts on a colourer object that holds the various parameters
    requried for colouring the object.
    The colourchooser takes a list of colour schemes in the 'schemes'
    keyword argument to init that defines which capabilities the widget
    will have. They are:
    Uniform: colour a field uniformly
    +ve -ve: binary colour scheme (e.g. for orbitals)
    Anything else is currently considered to be some form of colourmap
    """
    def __init__(self,
                 parent,
                 colourer,
                 schemes,
                 graph=None,
                 choose_field=None,
                 title=None
                 ):


        self.debug=0
        self.parent = parent
        self.colourer = colourer # object to hold colour info
        self.schemes = schemes # which schemes this widget supports
        self.graph = graph # graph object - for getting field objects
        self.choose_field=choose_field # If we are query for fields
        if title:
            self.title=title # this is what the group will be called
        else:
            self.title = "Colours" # Default title of Colours

        # If we're choosing fields, Append them here
        if self.choose_field:
            fields = self.get_all_fields()
            self.schemes+=fields
        
        # Build the base widgets
        self.build_base()

        # Build the widgets for all schemes
        builtcmap=None # Don't build the cmap widgts more than once
        for scheme in self.schemes:
            if scheme == 'Uniform':
                self.build_uniform()
            elif scheme == '+ve -ve':
                self.build_plusminus()
            else:
                # Assume anything else is a colourmap
                if not builtcmap:
                    self.build_colourmap()
                    builtcmap=1


        # Now pack them - preference is uniform > +ve-ve > colourmap
        if 'Uniform' in self.schemes:
            self.pack_uniform()
        elif '+ve -ve' in self.schemes:
            self.pack_plusminus()
        else:
            self.pack_colourmap()

        # Need to initialise the scheme in use
        scheme = self.w_scheme_options.getvalue()
        self.colourer.set_value("scheme",scheme)


    ###############################################################
    ### get_colourmaps, get_all_fields and get_field_from_name
    ### are here as they are a little different in requiring the graph object
    ###
    def get_colourmaps(self):
        """Return a list of the available colourmaps that
        is stored in the graph object"""

        t = ['Default']
        if self.graph:
            for c in self.graph.colourmaps:
                t.append(c.title)
        return t

    def get_all_fields(self):
        """Return a list of the fields held by the CCP1GUI so that
        we can use their data values to colourmap other objects"""
        items = []
        #items=['foo','bar']
        #return items
        for o in self.graph.data_list:
            t1 = string.split(str(o.__class__),'.')
            myclass = t1[len(t1)-1]
            if myclass == 'Field':
                if o.ndd == 1:
                    items.append(o.name)

        return items

    def get_field_from_name(self,name):
        """Get the field object that the user has selected to colour
        things by"""
                    
        colour_obj = None
        for o in self.graph.data_list:
            t1 = string.split(str(o.__class__),'.')
            myclass = t1[len(t1)-1]
            if myclass == 'Field':
                if o.ndd == 1:
                    if o.name == name:
                        colour_obj = o
        return colour_obj

    ###############################################################

    def build_base(self):
        """Consists of two Pmw.Labelled Widgets side by side in topframe.
        The first is used to select the scheme to be used. The second is
        used to hold the tools to manipulate that scheme.
        """

        # Build the main group
        self.widget = Pmw.Group(
            self.parent,
            tag_text=self.title,
            #tag_foreground="blue"
            #tagindent=100 # default is 10
            )
        #self.widget.pack(fill = 'x', expand = 1)

        self.topframe = Tkinter.Frame(self.widget.interior())
        self.topframe.pack(side='top')

        # Scheme Chooser
        self.w_scheme = Pmw.LabeledWidget(
            self.topframe,
            labelpos = 'w',
            label_text='Scheme')
        self.w_scheme.pack(side='left')

        # Option menu to choose between the different schemes
        # calls change_scheme to update the widget with any
        # required changes
        self.w_scheme_options = Pmw.OptionMenu(
            self.w_scheme.interior(),
            labelpos = None,
            items=self.schemes,
            initialitem=self.colourer.get_value("scheme"),
            command=self.change_scheme
            )

        # Disable if only 1 option
        if len(self.schemes)==1:
            self.w_scheme_options.configure(menubutton_state='disabled')
        self.w_scheme_options.pack()

        # Labelled widget to configure the chosen scheme
        self.w_config = Pmw.LabeledWidget(
            self.topframe,
            labelpos = 'w',
            label_text='Colour')
        self.w_config.pack(side='left')


    def build_plus(self):
        """Build the widgets to configure the plus colour (also
        used for the uniform scheme
        label is used to change the text label)
        """
        label='+ve'
        colour = self.colourer.get_value('plus_colour')
        self.plus_button = Tkinter.Button(self.w_config.interior(),
                                       text = label,
                                       foreground = colour,
                                       command= self.choose_plus_colour)

    def pack_plus(self):
        """Pack the plus widget
        Need to change the text as this is also used by the uniform widget
        """
        self.plus_button.config(text='+ve')
        self.plus_button.pack(side='left')

    def choose_plus_colour(self):
        """Get the selected clour, set the colourer and then
        colour the button"""
        colour = self.colourer.get_value('plus_colour')
        plus_rgb, plus_colour = tkColorChooser.askcolor(initialcolor=colour)
        #print "plus_rgb ",plus_rgb
        #print "plus_colour ",plus_colour
        self.colourer.set_value('plus_colour',plus_colour)
        self.colourer.set_value('plus_rgb',plus_rgb)
        self.plus_button.configure(foreground = plus_colour)


    def build_minus(self):
        """Build the widgets to configure the negative colour
        """
        colour = self.colourer.get_value('minus_colour')
        self.minus_button = Tkinter.Button(self.w_config.interior(),
                                       text = '-ve',
                                       foreground = colour,
                                       command= self.choose_minus_colour)

    def pack_minus(self):
        """Pack the uniform widget"""
        self.minus_button.pack(side='left')

    def choose_minus_colour(self):
        """Get the selected clour, set the colourer and then
        colour the button"""
        colour = self.colourer.get_value('minus_colour')
        minus_rgb, minus_colour = tkColorChooser.askcolor(initialcolor=colour)
        self.colourer.set_value('minus_colour',minus_colour)
        self.colourer.set_value('minus_rgb',minus_rgb)
        self.minus_button.configure(foreground = minus_colour)

    def build_uniform(self):
        """Build the widgets for the uniform configuration (this
        just uses the plus widget)"""
        self.build_plus()

    def pack_uniform(self):
        """Pack the widgets for the uniform configuration
        Also need to change the label"""
        self.plus_button.config(text='oOo')
        self.plus_button.pack(side='left')
        
    def forget_uniform(self):
        """Pack the widgets for the uniform configuration
        Also need to change the label"""
        if hasattr(self,'plus_button'):
            self.plus_button.forget()
        
    def build_plusminus(self):
        """Build the widgets for the plusminus configuration"""
        self.build_plus()
        self.build_minus()

    def pack_plusminus(self):
        """Pack the widgets for the plusminus configuration"""
        self.pack_plus()
        self.pack_minus()
                           
    def forget_plusminus(self):
        """Hide the plusminus widgets
        Checks if they exist so we can just call this regardles
        of whether we have built them or not
        """
        if hasattr(self,'minus_button'):
            self.minus_button.forget()
        if hasattr(self,'plus_button'):
            self.plus_button.forget()

    def build_colourmap(self):
        """A Pmw.OptionMenu to choose the colourmapping to apply
        In addition a frame is created below the other widgets
        to hold the cmap high & low tools as well as the one to toggle
        if we show the colourmap_actor
        
        """


        # The menu to configure the colourmaps - packs in self.w_config
        # like the other configuration widgets
        cmaps = self.get_colourmaps()
        self.colourmap_options = Pmw.OptionMenu(
            self.w_config.interior(),
            labelpos = None,
            items=cmaps,
            initialitem=cmaps[0],
            command=self.change_colourmap
            )


        # Frame to hold the other widgets (sits below them)
        self.bottomframe = Tkinter.Frame(self.widget.interior())
        
        # Counter to configure the lower bound
        low=self.colourer.get_value("cmap_low")
        if not low:
            # Trap this here cos it's a bugger to work out why it's crashing otherwise...
            raise AttributeError,"visualiser.py:ColourChooser need a cmap_low value!"
        self.w_cmap_low = Pmw.Counter(
            self.bottomframe,
            labelpos = 'w',
            label_text = 'Lo',
            entryfield_value = low,
            entryfield_entry_width = 5,
            increment=1.0,
            datatype = {'counter' : 'real' },
            entryfield_validate = { 'validator' : 'real' },
            )

        self.w_cmap_low.pack(side='left')

        # Counter to configure the upper bound
        high=self.colourer.get_value("cmap_high")
        if not high:
            # Trap this here cos it's a bugger to work out why it's crashing otherwise...
            raise AttributeError,"visualiser.py:ColourChooser need a cmap_high value!"
        self.w_cmap_high = Pmw.Counter(
            self.bottomframe,
            labelpos = 'w',
            label_text = 'Hi',
            entryfield_value = high,
            entryfield_entry_width = 5,
            increment=1.0,
            datatype = {'counter' : 'real' },
            entryfield_validate = { 'validator' : 'real' })
        self.w_cmap_high.pack(side='left')


        # Checkbox to decide if to show the colourmap actor
        self.w_cmap_show_var = Tkinter.BooleanVar()
        self.w_cmap_show_var.set(0) # Turn it off by default
        self.w_cmap_show = Pmw.LabeledWidget(
            self.bottomframe,
            labelpos='w',
            label_text='Display'
            )
        self.w_cmap_show_button = Tkinter.Checkbutton(
            self.w_cmap_show.interior()
            )
        self.w_cmap_show_button.config(variable=self.w_cmap_show_var)
        self.w_cmap_show_button.config(
            command=lambda s=self: s.toggle_colourmap()
            )
        self.w_cmap_show_button.pack(side='left')
        self.w_cmap_show.pack(side='left')

    def toggle_colourmap(self):
        """Update the colourer to show or hide the scalarbar"""
        show = self.w_cmap_show_var.get()
        #print "setting show_colourmap_actor to ",show
        self.colourer.set_value("show_colourmap_actor",show)

#     def set_cmap_low(self,low):
#         """Set the cmap_low variable"""
#         #low='foo'
#         print "setting cmap low ",low
#         self.colourer.set_value("cmap_low",low)

    def change_colourmap(self,colourmap):
        """The colourmap has been changed to update the colourer object"""
        #print "updating colourmap to ",colourmap
        self.colourer.set_value("cmap_name",colourmap)

    def pack_colourmap(self):
        """Pack the colourmap widgets"""
        self.colourmap_options.pack(side='left')
        self.bottomframe.pack(side='bottom',pady='5')
        
    def forget_colourmap(self):
        if hasattr(self,"colourmap_options"):
            self.colourmap_options.forget()
        if hasattr(self,"bottomframe"):
            self.bottomframe.forget()

        
    def change_scheme(self,scheme):
        """The user has changed the colourscheme so we forget/pack
        the relevant widgets."""
        
        # Forget all the widgets
        self.forget_uniform()
        self.forget_plusminus()
        self.forget_colourmap()
        
        if scheme == 'Uniform':
            self.pack_uniform()
        elif scheme == '+ve -ve':
            self.pack_plusminus()
        else:
            self.pack_colourmap()

        # Update the colourer object with the new scheme
        self.colourer.set_value("scheme",scheme)
        
        self.read_widgets()

    def read_widgets(self):
        """ Update the colourer with the widget options.
        """

        if self.debug:print "ColourChooser read_widgets"

        # This is required for the Pmw.Counters as I can't work out
        # how to get them to call a command whenever they are updated (they
        # can be configured with a command, but it's only invoked when "Enter"
        # is pressed).
        if hasattr(self,"w_cmap_low"):
            cmap_low=float(self.w_cmap_low.get())
            self.colourer.set_value("cmap_low",cmap_low)
        if hasattr(self,"w_cmap_high"):
            cmap_high=float(self.w_cmap_high.get())
            self.colourer.set_value("cmap_high",cmap_high)
            

        # Colourmap name is updated automatically

        # Scheme updated automatically but set again just to be sure
        #scheme = self.w_scheme_options.getvalue()
        #self.colourer.set_value("scheme",scheme)
        scheme = self.colourer.get_value("scheme")
        
        
        # Now get the field object if requried
        if self.choose_field:
            field = self.get_field_from_name(scheme)
            if field:
                self.colourer.set_value("cmap_obj",field)


class Visualiser:

    """ Base class for visualisation controls takes user input and
    creates and modifies images in the viewer

    The main access methods (Open, Build, Show, Hide, Delete) will not
    usually need to be overloaded but the internal methods with a
    leading underscore should be provided either by the generic
    classes in this file or more specific derived classes
    """

    initted = 0
    
    def __init__(self,root,graph,obj,allvis=None,**kw):
        
        # allvis is a flag to tag if the visualiser is being used to change all the images
        # or just a single one
        self.allvis = allvis

        if not self.allvis:
            if self.initted:
                print 'reinit skipped'
                return

        self.initted = 1
        self.root = root
        # the graph object we will be rendering to
        self.graph = graph
        # the result object to be visualised
        self.object = obj
        # This is now handled in the derived class
        self.status = NULL
        self.is_showing = 0
        self.dialog = None
        self.title = 'Untitled'
        self.show_2d = 0
        self.debug = 0


    def make_dialog(self):
        """Create the dialogs. The base dialog may have been created
        already if we are inheriting from the DataVisualiser class so
        we check this before calling _make_dialog"""
        if not self.dialog:
            self.make_base_dialog()
        if not self.dialog_contents:
            self._make_dialog()
            self.dialog_contents=1

    def _make_dialog(self):
        """This should be overloaded in any derived class"""
        print "generic/visualiser.py Visualiser._make_dialog should be overloaded"
        
    def make_base_dialog(self):
        """Build the base Widgets"""
        # delete final arg as we will use kw

        self.dialog = Pmw.MegaToplevel(self.root)
        #Associate widget with its help file
        viewer.help.sethelp(self.dialog,"AdjMolView")

        self.dialog.userdeletefunc(lambda s=self: s.dialog.withdraw())
        self.dialog.title(self.title)
        self.dialog.topframe = Tkinter.Frame(self.dialog.component('hull'))
        self.dialog.topframe.pack(side='top',fill='x')
        self.dialog.botframe = Tkinter.Frame(self.dialog.component('hull'))
        self.dialog.botframe.pack(side='top',fill='x')

        if self.allvis:
            self.dialog.b1 = Tkinter.Button(self.dialog.botframe,text='Update All',command=self.__view)
            self.dialog.b2 = Tkinter.Button(self.dialog.botframe,text='Show All',command=self.__show )
            self.dialog.b3 = Tkinter.Button(self.dialog.botframe,text='Hide All',command=self.__hide)
            self.dialog.b4 = Tkinter.Button(self.dialog.botframe,text='Destroy All',command=self.__delete)
            self.dialog.b5 = Tkinter.Button(self.dialog.botframe,text='Close',command=self.__close)
        else:
            self.dialog.b1 = Tkinter.Button(self.dialog.botframe,text='Update',command=self.__view)
            self.dialog.b2 = Tkinter.Button(self.dialog.botframe,text='Show',command=self.__show)
            self.dialog.b3 = Tkinter.Button(self.dialog.botframe,text='Hide',command=self.__hide)
            self.dialog.b4 = Tkinter.Button(self.dialog.botframe,text='Destroy',command=self.__delete)
            self.dialog.b5 = Tkinter.Button(self.dialog.botframe,text='Close',command=self.__close)

        self.dialog.b1.pack(side='left',fill='x')
        self.dialog.b2.pack(side='left',fill='x')
        self.dialog.b3.pack(side='left',fill='x')
        self.dialog.b4.pack(side='left',fill='x')
        self.dialog.b5.pack(side='left',fill='x')
        self.dialog_contents=0

    def Open(self):
        """ Open the widget for editing/actions """
        self.make_dialog()
        self.reposition()
        self.disable_dialog()
        self.dialog.show()
        self.dialog.update()
        self.enable_dialog()

    def disable_dialog(self):
        """This will be called before the tk events from the widget
        are handled for the first time
        Empirically we find that the command callback from the FPScale
        widget is being called once as soon as the widget is activated,
        this leads to unnecessary computation
        in such cases overload this function with code needed to bypass
        such computation
        """
        pass

    def enable_dialog(self):
        """Can (optionally) be defined to reverse the effects of disable_dialog
        """
        pass

    def reposition(self):

        if self.debug:deb('reposition')
        """ Try to translate the widget so it is in a convenient spot
        relative to the main window This needs to be executed after
        the widget is complete
        """

        #m = re.match('(\d+)x(\d+)\+(\d+)\+(\d+)',self.dialog.geometry())
        #sx,sy,px,py = int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4))
        #print 'visualiser geom',    sx,sy,px,py
        # Find position of master
        m = re.match('(\d+)x(\d+)\+(\d+)\+(\d+)',self.graph.master.geometry())
        msx,msy,mpx,mpy = int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4))
        if self.debug:deb('master geom: %f %f %f %f' % (msx,msy,mpx,mpy))
        self.dialog.geometry("+%d+%d" % (mpx+msx+4,mpy))
    
    def opacity_widget(self,frame=None):
        if frame:
            f = frame
        else:
            f = self.dialog.topframe

        self.w_opacity = Pmw.Counter(f,
                                     labelpos = 'w',
                                     label_text = 'Opacity',
                                     entryfield_value = self.opacity,
                                     increment=0.1,
                                     entryfield_entry_width=5,
                                     datatype = {'counter' : 'real' },
                                     entryfield_validate = { 'validator' : 'real',
                                                             'min'       : 0.0,
                                                             'max'       : 1.0})
        self.w_opacity.pack()

    def read_opacity_widgets(self):
        self.opacity = float(self.w_opacity.get())        

    def __view(self):
        self.View()

    def View(self):
        self.read_widgets()
        self.Build()
        if self.status == BUILT:
            self.dialog.b1.configure(text = 'Update')

    def __delete(self):
        """ Delete the graphical representation (and the widget) """
        self.Delete()

        # Need to miss this out if we are changing all molecules
        if not self.allvis:
            #
            # need to destory vis_dict and vis_list entries for as well
            # the modelling program as well
            #
            t = id(self.object)
            self.graph.vis_list.remove(self)
            try:
                visl = self.graph.vis_dict[t]
                visl.remove(self)
            except KeyError:
                print 'key error'

    def __show(self):
        self.Show()

    def __hide(self):
        self.Hide()

    def __close(self):
        self.dialog.withdraw()

    def Build(self,object=None):
        if self.dialog:
            self.read_widgets()
        if object:
            self.object = object
        self._delete()
        self._build(object=object)
        self._show()
        self.is_showing=1
        if self.show_2d:
            self.graph.window2d.show()
        self.graph.update()

    def Build2(self,object=None):
        self._delete()
        self._build()
        self._show()
        self.is_showing=1
        if self.show_2d:
            self.graph.window2d.show()
        self.graph.update()
        
    def Show(self,object=None,update=1):
        if self.status == NULL:
            self._build(object=object)
        self._show()
        self.is_showing=1
        if self.show_2d:
            self.graph.window2d.show()
        if update:
            self.graph.update()

    def Hide(self):
        if self.status == BUILT:
            self._hide()
        self.is_showing=0
        self.graph.update()

    def Delete(self):
        if self.status == BUILT:
            self._delete()
        if self.dialog:
            self.dialog.destroy()

    def read_widgets(self):
        print 'read_widgets method should be replaced in the derived class'

    def GetStatus(self):
        return self.status

    def IsShowing(self):
        return self.is_showing

    def GetTitle(self):
        """ Provide an identifying string"""
        try:
            txt = self.title
        except AttributeError:
            txt = 'No Title'
        return txt

##    def _delete(self):
##        print 'overload me _delete'
##    def _hide(self):
##        print 'overload me _hide'
##    def _show(self):
##        print 'overload me _show'
##    def _build(self,object=None):
##        print 'overload me _build'        


class DataVisualiser(Visualiser):
    """Generic class to hold stuff that is common to all the visualisers that visualise
    fields. Currently this just includes the widget that lists the min and max
    values"""

    def __init__(self, root, graph, obj, data_summary=None,**kw):
        
        Visualiser.__init__(self, root, graph, obj, **kw)

        #Make the base dialog that creates the widgets
        if not self.dialog:
            self.make_base_dialog()

        if data_summary:
            self.make_data_summary_dialog(obj)


    def make_data_summary_dialog(self,obj):
        # Frame to hold textwidget and button to show/hide it
        self.data_summary_group = Pmw.Group( self.dialog.topframe, tag_text="Data Summary" )

        # Button & control to show/hide summary
        self.data_summary_show_var = Tkinter.BooleanVar()
        self.data_summary_show_var.set(0) # Turn it off by default
        self.data_summary_show_widget = Pmw.LabeledWidget(
            self.data_summary_group.interior()
            ,labelpos='w',
            label_text='Show Summary')
        self.data_summary_show_button = Tkinter.Checkbutton(self.data_summary_show_widget.interior())
        self.data_summary_show_button.config(variable=self.data_summary_show_var)
        self.data_summary_show_button.config(command=lambda s=self: s.data_summary_show_toggle() )
        self.data_summary_show_button.pack(side='left')
        self.data_summary_show_widget.pack(side='top')
        self.data_summary_group.pack(side='top',fill='x')

        # Text widget to hold data field information
        #summary = obj.data_summary()
        summary = obj.summary()
        self.data_summary_text_widget = Pmw.ScrolledText(
            self.data_summary_group.interior(),
            hull_width = 400,
            hull_height = 150,
            usehullsize=1,
            borderframe=1
            
            )
        self.data_summary_text_widget.settext(summary)

    def data_summary_show_toggle(self):
        """Show or hide the data summary"""
        show = self.data_summary_show_var.get()
        if show:
            self.data_summary_text_widget.pack(side='top')
        else:
            self.data_summary_text_widget.forget()

class MoleculeVisualiser(Visualiser):

    def __init__(self, root, graph, obj, **kw):

        Visualiser.__init__(self, root, graph, obj, **kw)

        self.show_wire =      self.graph.check_capability('wire')

        if obj and len(obj.atom) > 100:
            print 'Ball+Stick view is suppressed for initial view with natoms > 100'
            self.show_spheres = 0
            self.show_sticks = 0
        else:
            self.show_spheres = self.graph.check_capability('spheres')
            self.show_sticks = self.graph.check_capability('sticks')
        self.show_labels = 0
        self.show_contacts = 0
        self.sphere_scale = 0.5
        self.sphere_table = COV_RADII
        self.label_scale = 0.5
        self.cyl_width = 0.1
        self.label_colour = '#ffffff'
        self.label_rgb = [255,255,255]
        self.cyl_colour = '#808080'
        self.cyl_rgb = [ 128,128,128 ]
        self.colour_cyl = 0

        self.molecule=obj

        if not self.allvis:
            try:
                if  self.molecule.title:
                    self.title='Molecule view: ' + self.molecule.title
                else:
                    self.title='Molecule view: (None title)'
            except AttributeError:
                self.title='Molecule view: (untitled)'
        else:
            self.title='View Changer for All Molecules'

        #print 'Mol Title',self.title

    def _make_dialog(self):

        labels=[]
        labels2=[]

        self.wire_var = Tkinter.BooleanVar()
        self.wire_var.set(0)
        self.contact_var = Tkinter.BooleanVar()
        self.contact_var.set(0)

        if self.graph.check_capability('wire'):
            self.wire_var.set(self.show_wire)

            wire_group  = Pmw.Group(self.dialog.topframe, tag_text="Wireframe")
            f = wire_group.interior()

            self.wire_frame = Pmw.LabeledWidget(f,labelpos='w',label_text='Show Bonds')

            self.wire = Tkinter.Checkbutton(self.wire_frame.interior())
            self.wire.config(variable=self.wire_var)
            self.wire.config(command=lambda s=self: s.__read_buttons() )
            self.wire.pack(side='top')
            self.wire_frame.pack(side='left')

            labels.append(self.wire_frame)

            if self.graph.check_capability('contacts'):
                self.contact_var.set(self.show_contacts)
                self.contact_frame = Pmw.LabeledWidget(f,labelpos='w',label_text='Contacts')
                self.contact = Tkinter.Checkbutton(self.contact_frame.interior())
                self.contact.config(variable=self.contact_var)
                self.contact.config(command=lambda s=self: s.__read_buttons() )
                self.contact.pack(side='top')
                self.contact_frame.pack(side='left')
                labels.append(self.contact_frame)

            wire_group.pack(side='top',fill='x')

        self.sphere_var              = Tkinter.BooleanVar()
        self.sphere_var.set(self.show_spheres)
        if self.graph.check_capability('spheres'):

            sphere_group  = Pmw.Group(self.dialog.topframe, tag_text="Spheres")
            f = sphere_group.interior()

            self.sphere_frame = Pmw.LabeledWidget(f,labelpos='w',label_text='Show')

            self.sphere = Tkinter.Checkbutton(self.sphere_frame.interior())
            self.sphere.config(variable=self.sphere_var)
            self.sphere.config(command=lambda s=self: s.__read_buttons() )
            self.sphere.pack(side='top')
            self.sphere_frame.pack(side='left')
            labels.append(self.sphere_frame)

            self.sphere_size = Pmw.Counter(
                f,
                labelpos = 'w', label_text = 'Scale',
                entryfield_value = self.sphere_scale,
                entryfield_entry_width = 5,
                increment=0.1,
                datatype = {'counter' : 'real' },
                entryfield_validate = { 'validator' : 'real' })
            self.sphere_size.pack(side='left')

            labels2.append(self.sphere_size)

            self.radii_var  = Tkinter.StringVar()
            self.radii_menu = Pmw.OptionMenu(
                f,
                labelpos = 'w',
                label_text = 'Radii ',
                menubutton_textvariable = self.radii_var,
                items = ['Covalent','v.d.W.'],
                initialitem='Covalent',
                command=lambda val, s=self: s.__read_buttons(), 
                menubutton_width = 8)

            self.radii_menu.pack(side='left')
            sphere_group.pack(side='top',fill='x')

        self.stick_var              = Tkinter.BooleanVar()
        self.stick_var.set(self.show_sticks)

        self.stick_col_byat_var              = Tkinter.BooleanVar()
        self.stick_col_byat_var.set(self.colour_cyl)

        if self.graph.check_capability('sticks'):

            stick_group  = Pmw.Group(self.dialog.topframe, tag_text="Sticks")
            f = stick_group.interior()

            self.stick_frame = Pmw.LabeledWidget(f,
                labelpos='w',label_text='Show')
            self.stick = Tkinter.Checkbutton(self.stick_frame.interior())
            self.stick.config(variable=self.stick_var)
            self.stick.config(command=lambda s=self: s.__read_buttons() )
            self.stick.pack(side='top')
            self.stick_frame.pack(side='left')
            labels.append(self.stick_frame)

            #f = Tkinter.Frame(self.dialog.topframe)
            #self.w_cyl_colour_lab = Tkinter.Label(f,text='Cylinder Colour:      ')

            self.w_cyl_width = Pmw.Counter(
                f,
                labelpos = 'w', label_text = 'Radius',
                entryfield_value = self.cyl_width,
                entryfield_entry_width = 5,
                increment=0.01,
                datatype = {'counter' : 'real' },
                entryfield_validate = { 'validator' : 'real' })

            self.w_cyl_width.pack(side='left')

            self.w_cyl_colour = Tkinter.Button(f,
                                                 text = 'Colour',
                                                 foreground = self.cyl_colour,
                                                 command= self.__choose_cyl_colour)

            #self.w_cyl_colour_lab.pack(side='left')
            self.w_cyl_colour.pack(side='left',padx=5)

            labels2.append(self.w_cyl_width)

            self.stick_col_byat_frame = Pmw.LabeledWidget(f,
                labelpos='w',label_text='By Type')
            self.stick_col_byat = Tkinter.Checkbutton(self.stick_col_byat_frame.interior())
            self.stick_col_byat.config(variable=self.stick_col_byat_var)
            self.stick_col_byat.config(command=lambda s=self: s.__read_buttons() )
            self.stick_col_byat.pack(side='top')
            self.stick_col_byat_frame.pack(side='left')
            labels.append(self.stick_col_byat_frame)

            stick_group.pack(side='top',fill='x')

        self.labels_var               = Tkinter.BooleanVar()
        self.labels_var.set(self.show_labels)

        if self.graph.check_capability('labels'):

            labels_group  = Pmw.Group(self.dialog.topframe, tag_text="Labels")
            f = labels_group.interior()

            f1 = Tkinter.Frame(f)
            f2 = Tkinter.Frame(f)
            self.label_frame = Pmw.LabeledWidget(f1,labelpos='w',label_text='Show')
            self.labels = Tkinter.Checkbutton(self.label_frame.interior())
            self.labels.config(variable=self.labels_var)
            self.labels.config(command=lambda s=self: s.__read_buttons() )
            self.labels.pack(side='top')
            self.label_frame.pack(side='left')
            labels.append(self.label_frame)

            self.label_size = Pmw.Counter(
                f1,
                labelpos = 'w', label_text = 'Size',
                entryfield_value = self.label_scale,
                entryfield_entry_width = 5,
                increment=0.01,
                datatype = {'counter' : 'real' },
                entryfield_validate = { 'validator' : 'real' })
            self.label_size.pack(side='left')
            labels2.append(self.label_size)            

            #f = Tkinter.Frame(self.dialog.topframe)
            #self.w_label_colour_lab = Tkinter.Label(f,text='Edit Label Colour:      ')
            self.w_label_colour = Tkinter.Button(f1,
                                                 text = 'Colour',
                                                 foreground = self.label_colour,
                                                 command= self.__choose_label_colour)

            #self.w_label_colour_lab.pack(side='left')
            self.w_label_colour.pack(side='left',padx=5)
            #f.pack(side='top')


            self.label_with_var  = Tkinter.StringVar()
            self.w_label_with = Pmw.OptionMenu(
                f2,
                labelpos = 'w',
                label_text = 'Label With ',
                menubutton_textvariable = self.label_with_var,
                items = ['name','symbol','charge','atom no.','name(no.)',
                         'mulliken charge','lowdin charge','potential derived charge'
                         ],
                initialitem='name',
                menubutton_width = 10)
            self.w_label_with.pack(side='left')

            f1.pack(side='top',fill='x')
            f2.pack(side='top',fill='x')
            labels_group.pack(side='top',fill='x')

        Pmw.alignlabels(labels2)


        if not self.allvis:
            # Draw selected atoms not applicable to the all visualiser
            f = Tkinter.Frame(self.dialog.topframe)
            self.select_button = Tkinter.Button(f,command = self.draw_by_selection,text="Draw Selected Atoms Only")
            self.all_button = Tkinter.Button(f,command = self.draw_all,text="Draw All Atoms")        
            self.select_button.pack(side='left')
            self.all_button.pack(side='left')
            f.pack(side='top')

    def draw_by_selection(self):
        pass
    def draw_all(self):
        pass
    
    def __read_buttons(self):
        self.show_wire = self.wire_var.get()
        self.show_spheres = self.sphere_var.get()
        self.show_labels = self.labels_var.get()
        self.show_sticks = self.stick_var.get()
        self.show_contacts = self.contact_var.get()
        self.colour_cyl = self.stick_col_byat_var.get()

        txt = self.radii_var.get()
        if txt == "Covalent":
            self.sphere_table = COV_RADII
        else:
            self.sphere_table = VDW_RADII

        if self.is_showing:
            self._show()

    def __choose_label_colour(self):
        self.label_rgb, self.label_colour = tkColorChooser.askcolor(initialcolor=self.label_colour)
        self.w_label_colour.configure(foreground = self.label_colour)

    def __choose_cyl_colour(self):
        self.cyl_rgb, self.cyl_colour = tkColorChooser.askcolor(initialcolor=self.cyl_colour)
        self.w_cyl_colour.configure(foreground = self.cyl_colour)

    def read_widgets(self):
        self.sphere_scale = float(self.sphere_size.get())
        self.label_scale = float(self.label_size.get())
        self.cyl_width = float(self.w_cyl_width.get())
        self.label_with = self.label_with_var.get()

    def highlight_atom(self,list):
        """ Change the appearance of a group of atoms """
        print "no highlight implemented", list


class VibrationVisualiser(MoleculeVisualiser):
    """ A visualiser for normal coordinates
    based on the molecule visualiser
    """
    def __init__(self, root, graph, obj, **kw):

        self.frames = 36
        self.scale =  0.3
        self.vib = obj
        self.frame_delay = 10
        self.choose_mode = 0
        
        if kw.has_key("mol"):
            mol = kw["mol"]
        else:
            #print type(obj), obj.__class__
            if not obj.reference:
                raise AttributeError, 'Vibration visualiser requires a reference structure'
                return
            else:
                mol = obj.reference

        # take 2 copies of reference mol
        mol = copy.deepcopy(mol)
        self.molecule = mol
        self.mol2 = copy.deepcopy(mol)
        try:
            scale=graph.conn_scale
            toler=graph.conn_toler
            mol.connect(scale=scale, toler=toler)
            self.mol2.connect(scale=scale, toler=toler)
        except AttributeError:
            mol.connect()
            self.mol2.connect()

        # derived classes will run their moleculevisualiser methods
        # after this 
        

    def _make_dialog(self, **kw):
        #print 'Dialog'
        MoleculeVisualiser._make_dialog(self, **kw)

        self.ani_frame = Pmw.Group(self.dialog.topframe, tag_text="Animation")

        tf = Tkinter.Frame(self.ani_frame.interior())
        tf.pack()

        self.start_button = Tkinter.Button(tf,
                                           text = 'start',
                                           width = 12,
                                           command = self.start_ani)

        self.stop_button = Tkinter.Button(tf,
                                          text = 'stop',
                                          width = 12,
                                          command = self.stop_ani)
        labels = []
        if self.choose_mode:
            list = []
            for v in self.vs.vibs:
                list.append(v.title)
            self.w_mode = Pmw.OptionMenu(
                self.ani_frame.interior(),
                labelpos = 'w',
                label_text = 'Mode:',
                items = list,
                initialitem=0,
                menubutton_width = 8)
            labels.append(self.w_mode)

        self.w_frames = Pmw.Counter(self.ani_frame.interior(),
                                    labelpos = 'w', label_text = 'Number of frames',
                                    entryfield_value = self.frames,
                                    entryfield_entry_width = 5,
                                    increment=1,
                                    datatype = {'counter' : 'integer' },
                                    entryfield_validate = { 'validator' : 'integer' })

        labels.append(self.w_frames)

        self.w_scale = Pmw.Counter(self.ani_frame.interior(),
                                   labelpos = 'w', label_text = 'Amplitude',
                                   entryfield_value = self.scale,
                                   entryfield_entry_width = 5,
                                   increment=0.01,
                                   datatype = {'counter' : 'real' },
                                   entryfield_validate = { 'validator' : 'real' })

        labels.append(self.w_scale)

        self.w_delay = Pmw.Counter(self.ani_frame.interior(),
                                   labelpos = 'w', label_text = 'Frame delay',
                                   entryfield_value = self.frame_delay,
                                   entryfield_entry_width = 5,
                                   increment=1,
                                   datatype = {'counter' : 'integer' },
                                   entryfield_validate = { 'validator' : 'integer',
                                                           'min'       : 1 })
        labels.append(self.w_delay)

        if self.choose_mode:
            self.w_mode.pack(side='top')
        self.w_frames.pack(side='top')
        self.w_scale.pack(side='top')
        self.w_delay.pack(side='top')

        Pmw.alignlabels(labels)

        self.start_button.pack(side='left')
        self.stop_button.pack(side='left')

        self.ani_frame.pack(side='top')

        Pmw.alignlabels([self.wire_frame,
                         self.sphere_frame,
                         self.stick_frame,
                         self.label_frame])
        
    def read_widgets(self):

        MoleculeVisualiser.read_widgets(self)

        if self.choose_mode:
            self.mode = self.w_mode.index(Pmw.SELECT)
            #print 'Mode',self.mode
            #self.mode =  int(self.w_mode.get())

        # since this is in the diplay loop, it is better to keep
        # the current value in case of failure
        old = self.frames
        try:
            self.frames =  int(self.w_frames.get())
        except:
            self.frames = old

        old = self.scale
        try:
            self.scale  =  float(self.w_scale.get())
        except:
            self.scale = old

        old = self.frame_delay
        try:
            self.frame_delay  =  int(self.w_delay.get())
        except:
            self.frame_delay = old

    def start_ani(self):
        self.animate=1
        self.angle = 0.0
        self.nextframe()

    def stop_ani(self):
        self.animate=0

    def nextframe(self):
        """Update the structure and draw the next frame"""
        if self.animate == 0:
            return
        # check if the user has changed the parameters
        self.read_widgets()

        if self.choose_mode:
            self.vib = self.vs.vibs[self.mode]

        self.angle_increment = 2.0*math.pi / self.frames
        self.angle = self.angle +  self.angle_increment
        fac = self.scale * math.sin(self.angle)
        #print 'Displacement angle,scale = ',self.angle,fac
        for i in range(len(self.molecule.atom)):
            a = self.molecule.atom[i]
            r = self.mol2.atom[i]
            d = self.vib.displacement[i]
            a.coord[0] = r.coord[0] + fac*d[0]
            a.coord[1] = r.coord[1] + fac*d[1]
            a.coord[2] = r.coord[2] + fac*d[2]

        # remake images
        self._delete()
        self._build()
        self._show()
        # update image
        self.graph.update()
        # schedule next frame
        self.dialog.after(self.frame_delay, self.nextframe)

    def hide(self,**kw):
        """Overload to avoid reappearance """
        self.animate=0
        Visualiser.hide(self,**kw)


class VibrationSetVisualiser(VibrationVisualiser):
    """ Adaption of VibrationVisualiser to handle a whole set of
    vibrations
    """
    def __init__(self, root, graph, obj, **kw):
        VibrationVisualiser.__init__(self, root, graph, obj, **kw)
        self.choose_mode = 1
        self.max_mode = len(obj.vibs)
        self.mode = 0
        self.vs = obj
        self.vib = obj.vibs[0]
    def _make_dialog(self, **kw):
        VibrationVisualiser._make_dialog(self, **kw)


STRUCTURE_SEQ = 1
DLPOLY_HISTORY = 2

class TrajectoryVisualiser(MoleculeVisualiser):
    """To update a single image with a sequence of sets coordinates
    without loading all the structures as molecule objects
    """
    def __init__(self, root, graph, obj, type='SEQ',**kw):
        # the visualisation will start with a copy of the first frame

        self.type = type
        debug=None

        if type == 'SEQ':
            self.traj_type = STRUCTURE_SEQ
            self.sequence = obj
            self.molecule = obj
            self.nframes = len(obj.frames)

        elif type == 'DLPOLYHISTORY':
            self.traj_type = DLPOLY_HISTORY
            self.sequence = None
            self.traj_file = obj
            # have to parse out the first frame
            self.reader = Dl_PolyHISTORYReader()
            self.reader.open(obj.filename)
            self.reader.scan1()
            #####self.reader.close()
            self.molecule = self.reader.lastframe
            self.molecule.connect()
            self.nframes = 9999

        self.current_frame = 0

        #copy.deepcopy(obj.frames[0])
        #VtkMoleculeVisualiser is run next from vtkgraph

        if debug:
            print 'TRAJECTORY INIT',self.sequence, self.sequence.frames
            for f in self.sequence.frames:
                f.zlist()

    def _make_dialog(self, **kw):

        self.title='Trajectory Viewer'

        MoleculeVisualiser._make_dialog(self, **kw)

        self.ani_frame = Pmw.Group(self.dialog.topframe, tag_text="Play Trajectory")

        f = Tkinter.Frame(self.ani_frame.interior(),relief=Tkinter.SUNKEN, borderwidth=2)
        f.pack(side='bottom', fill=Tkinter.X)

        bar = Tkinter.Frame(f,relief=Tkinter.SUNKEN, borderwidth=2)
        bar.pack(side='left', fill=Tkinter.X)

        #b=Tkinter.Button(bar, text='Reset', command=self.reset)
        #b.pack(side='left')
        b=Tkinter.Button(bar, text='  |<  ', command=self.rew)
        b.pack(side='left')
        b=Tkinter.Button(bar, text='   <  ', command=self.bak)
        b.pack(side='left')
        b=Tkinter.Button(bar, text=' Stop ', command=self.stop)
        b.pack(side='left')
        b=Tkinter.Button(bar, text=' Play ', command=self.play)
        b.pack(side='left')
        b=Tkinter.Button(bar, text='  >   ', command=self.fwd)
        b.pack(side='left')
        b=Tkinter.Button(bar, text='  >|  ', command=self.end)
        b.pack(side='left')

        f.pack()
        bar2 = Tkinter.Frame(f, borderwidth=1)
        bar2.pack(side='left', fill=Tkinter.X)

        self.frame_label=Tkinter.Label(bar2)
        self.frame_label.configure(text="Frame %d of %d" % (self.current_frame+1,self.nframes))
        self.frame_label.pack(side='left')

        self.ani_frame.pack(side='top',fill='x')

    def rew(self):
        """ Go to the first frame of the trajectory and display the image
        """
        self.current_frame = 0
        if self.traj_type == DLPOLY_HISTORY:
            self.reader.close()
            self.reader.open(self.traj_file.filename)

        self.show_frame()
        
    def end(self):
        """ Go to the last frame of the animation and display the image.
        """
        self.current_frame = self.nframes - 1
        self.show_frame()

    def bak(self):
        """ Step back a single frame in the animation
        """
        self.current_frame -= 1
        if self.current_frame == -1:
            self.current_frame = 0
        self.show_frame()

    def fwd(self):
        """ Step forward a single frame in the animation
        """
        self.current_frame += 1
        if self.current_frame >= self.nframes:
            print 'END OF SEQUENCE'
            self.current_frame = self.nframes - 1
        self.show_frame()

    def stop(self):
        """ Stop the animation
        """
        self.ani_stop = 1

    def play(self):
        """ Play through the sequence of images from self.current_frame to the end
        """
        # Need to initialise frame_no if the animation toolbar was
        # open when objects were read in

        # Rewind if at end
        if self.current_frame >= self.nframes - 1:
            self.current_frame = 0

        self.ani_stop = 0
        self.ani_stop = 0

        while 1:
            print 'Trajectory Frame:',self.current_frame
            #self.interior().update()
            if self.ani_stop:
                return
            self.show_frame()

            self.current_frame += 1
            if self.ani_stop:
                return
            time.sleep(0.3)
            if self.ani_stop:
                return

            # the end?
            if self.current_frame == self.nframes:
                return

    def show_frame(self):
        """Update the working molecule with a set of coordinates and display
        """
        # check if the user has changed the parameters
        self.read_widgets()

        if self.traj_type == STRUCTURE_SEQ:

            print 'SHOWING FRAME #',self.current_frame
            frame = self.sequence.frames[self.current_frame]
            for i in range(len(self.molecule.atom)):
                a = self.molecule.atom[i]
                atom = frame.atom[i]
                a.coord[0] = atom.coord[0]
                a.coord[1] = atom.coord[1]
                a.coord[2] = atom.coord[2]

        elif self.traj_type == DLPOLY_HISTORY:
            
            print 'SHOWING FRAME #',self.current_frame

            iret = self.reader.scan1()

            if iret == -1:
                self.nframes = self.current_frame
                self.ani_stop = 1

            else:
                frame = self.reader.lastframe

                for i in range(len(self.molecule.atom)):
                    a = self.molecule.atom[i]
                    atom = frame.atom[i]
                    a.coord[0] = atom.coord[0]
                    a.coord[1] = atom.coord[1]
                    a.coord[2] = atom.coord[2]

        elif self.traj_type == MMTK:
            print "MMTK trajectory"

        #self.molecule.list()
        # remake images
        self._delete()
        self._build()
        self._show()
        self.frame_label.configure(text="Frame %d of %d" % (self.current_frame+1,self.nframes))
        self.dialog.update()
        # update image
        self.graph.update()

        # schedule next frame
        #self.dialog.after(self.frame_delay, self.nextframe)

class OutlineVisualiser:
    """To add outline to the volume widgets"""

    def __init__(self,**kw):
        self.outline_colour   =  '#00ff00'
        self.outline_rgb = [0, 255, 0]
        self.show_outline = 0

    def add_outline_widget(self):
        self.outline_var = Tkinter.BooleanVar()
        self.outline_var.set(self.show_outline)

        self.surface_outline_group = Pmw.Group(self.dialog.topframe ,tag_text='Outline')
        f = self.surface_outline_group.interior()
        self.outline_frame = Pmw.LabeledWidget(f ,labelpos='w',label_text='Display')
        self.w_outline = Tkinter.Checkbutton(self.outline_frame.interior())
        self.w_outline.config(variable=self.outline_var)
        self.w_outline.config(command=self._outline_switch)
        self.outline_frame.pack(side='left')
        self.w_outline.pack(side='top')

        self.w_outline_colour_lab = Tkinter.Label(f,text='Edit Colour: ')
        self.w_outline_colour = Tkinter.Button(f,
                                               text = 'oOo',
                                               foreground = self.outline_colour,
                                               command= self._choose_outline_colour)

        self.w_outline_colour_lab.pack(side='left')
        self.w_outline_colour.pack(side='left')
    
        self.surface_outline_group.pack(side='top',fill='x')

    def _choose_outline_colour(self):
        self.outline_rgb, self.outline_colour = tkColorChooser.askcolor(initialcolor=self.outline_colour)
        self.w_outline_colour.configure(foreground = self.outline_colour)

    def _outline_switch(self):
        self.show_outline = self.outline_var.get()


class IsoSurfaceVisualiser(DataVisualiser,OutlineVisualiser):
    """Base class for isosurfaces"""
    def __init__(self, root, graph, obj, **kw):
        DataVisualiser.__init__(self, root, graph, obj, **kw)
        OutlineVisualiser.__init__(self, **kw)
        self.field=obj
        self.opacity = 1.0
        self.colourer = Colourer(graph)
        

class OrbitalVisualiser(IsoSurfaceVisualiser):

    def __init__(self, root, graph, obj, **kw):

        IsoSurfaceVisualiser.__init__(self, root, graph, obj,data_summary=1,**kw)
        #
        # Create the required controls (how many frames)
        #

        self.title='Orbital view: ' + self.field.title
        self.height = 0.05

        # Set the default colours
        self.colourer.set_value("plus_colour",'#ff0000')
        self.colourer.set_value("minus_colour",'#0000ff')
        self.colourer.set_value("plus_rgb",[ 255, 0, 0])
        self.colourer.set_value("minus_rgb",[ 0, 0, 255])
        
        
    def _make_dialog(self):

        surface_group  = Pmw.Group(self.dialog.topframe, tag_text="Surfaces")
        f = surface_group.interior()

        self.w_height = Pmw.Counter(f,
                                    labelpos = 'w',
                                    label_text = 'Contour Height',
                                    entryfield_value = self.height,
                                    entryfield_entry_width = 5,
                                    increment=0.01,
                                    datatype = {'counter' : 'real' },
                                    entryfield_validate = { 'validator' : 'real' })

        self.w_height.pack(side='top')
        self.opacity_widget(frame=f)

        # Pack the colour chooser frame
        self.colourchooser = ColourChooser(
            f,
            self.colourer,
            schemes=['+ve -ve'],
            graph=self.graph,
            choose_field=0
            )
        self.colourchooser.widget.pack(side='top',fill='x',expand=1)
        
        surface_group.pack(side='top',fill='x')
        
        self.add_outline_widget()
        

    def read_widgets(self):
        self.height =  float(self.w_height.get())
        self.opacity =  float(self.w_opacity.get())
        self.colourchooser.read_widgets()


class DensityVisualiser(IsoSurfaceVisualiser):

    def __init__(self, root, graph, obj, **kw):

        IsoSurfaceVisualiser.__init__(self, root, graph, obj,data_summary=1,**kw)

        # Default settings
        self.height = 0.05
        self.opacity = 1.0
        self.field = obj
        self.title = 'Density Isosurface: ' + self.field.title
        # Colours
        self.colourer.set_value("plus_colour",'#00ff00')
        self.colourer.set_value("plus_rgb",[0, 255, 0])

    def _make_dialog(self):

        surface_group  = Pmw.Group(self.dialog.topframe, tag_text="Surfaces")
        f = surface_group.interior()

        labs = []

        self.w_height = Pmw.Counter(f,
                                    labelpos = 'w',
                                    label_text = 'Contour Height',
                                    entryfield_value = self.height,
                                    entryfield_entry_width = 5,
                                    increment=0.005,
                                    datatype = {'counter' : 'real' },
                                    entryfield_validate = { 'validator' : 'real' })
        labs.append(self.w_height)
        self.w_height.pack(side='top')

        #labs.append(self.w_colour_lab)

        self.opacity_widget(frame=f)
        labs.append(self.w_opacity)

        self.colourchooser = ColourChooser(
            f,
            self.colourer,
            schemes=['Uniform'],
            graph=self.graph,
            choose_field=0
            )
        self.colourchooser.widget.pack(side='top',fill='x',expand=1)
        

        surface_group.pack(side='top',fill='x')
        Pmw.alignlabels(labs)

        self.add_outline_widget()


    def __choose_plus_colour(self):
        self.plus_rgb, self.plus_colour = tkColorChooser.askcolor(initialcolor=self.plus_colour)
        self.w_pcolor.configure(foreground = self.plus_colour)

    def read_widgets(self):
        self.height =  float(self.w_height.get())
        self.opacity =  float(self.w_opacity.get())

class VolumeVisualiser(DataVisualiser,OutlineVisualiser):

    def __init__(self, root, graph, obj, **kw):

        DataVisualiser.__init__(self, root, graph, obj, data_summary=1, **kw)
        OutlineVisualiser.__init__(self, **kw)        
        self.colour_obj = None

        # Default settings
        #self.height = 0.05
        #self.plus_colour   =  '#00ff00'
        #self.plus_rgb = [0, 255, 0]
        #self.opacity = 1.0

        # Need editor for this
        self.outline_colour   =  '#00ff00'
        self.outline_rgb = [0, 255, 0]

        self.field = obj
        self.title = 'Volume Visualisation: ' + self.field.title
        self.setvalues()

    def setvalues(self):

        self.tfv = [ 0.0, 0.1, 0.5, 2.0, 10.0 ]
        self.rgb = [ [ 0,255,0],[0,0,255],[255,0,0],[255,255,0],[0,255,255]]
        self.colour = ['#00ff00',  '#0000ff',  '#ff0000', '#ffff00', '#00ffff' ]
        self.opacity = [0.1, 0.3, 0.5, 0.7, 0.9 ]
        self.sfac = 100.0

    def _make_dialog(self):

        transfer_group  = Pmw.Group(self.dialog.topframe, tag_text="Transfer Function")
        f = transfer_group.interior()

        self.w_sfac = Pmw.Counter(f,
                                    labelpos = 'w',
                                    label_text = 'Scale Factor',
                                    entryfield_value = self.sfac,
                                    entryfield_entry_width = 5,
                                    increment=1.0,
                                    datatype = {'counter' : 'real' },
                                    entryfield_validate = { 'validator' : 'real' })

        self.cframe = Tkinter.Frame(f)

        self.w_tfv = []
        self.w_colorlab = []
        self.w_color = []
        self.w_opacity = []

        frame = Tkinter.Frame(self.cframe)
        lab = Tkinter.Label(frame,text='Value')
        lab.pack(side='left',expand='yes',fill='x')
        lab = Tkinter.Label(frame,text='Colour')        
        lab.pack(side='left',expand='yes',fill='x')
        lab = Tkinter.Label(frame,text='Opacity')        
        lab.pack(side='left',expand='yes',fill='x')
        frame.pack(side='top',fill='x')

        for i in range(5):
            frame = Tkinter.Frame(self.cframe)

            val = Pmw.Counter(frame,
                                labelpos = 'w',
                                label_text = None,
                                entryfield_value = self.tfv[i],
                                entryfield_entry_width = 5,
                                increment=1.0,
                                datatype = {'counter' : 'real' },
                                entryfield_validate = { 'validator' : 'real' })

            #lab = Tkinter.Label(frame,text='Colour'+str(i))

            but = Tkinter.Button(frame,
                                 text = 'Colour',
                                 foreground = self.colour[i],
                                 command= lambda s = self, ix=i: s.__choose_colour(ix))

            count = Pmw.Counter(frame,
                                labelpos = 'w',
                                label_text = None,
                                entryfield_value = self.opacity[i],
                                entryfield_entry_width = 5,
                                increment=0.1,
                                datatype = {'counter' : 'real' },
                                entryfield_validate = { 'validator' : 'real' })

            self.w_tfv.append(val)
            #self.w_colorlab.append(lab)
            self.w_color.append(but)
            self.w_opacity.append(count)

            self.w_tfv[i].pack(side='left',expand='yes',fill='x')
            #self.w_colorlab[i].pack(side='left')
            self.w_color[i].pack(side='left',expand='yes',fill='x')
            self.w_opacity[i].pack(side='left',expand='yes',fill='x')
            frame.pack(side='top',fill='x')

        #self.w_sfac.pack(side='top',fill='x')
        self.cframe.pack(side='top',fill='x')

        transfer_group.pack(side='top',fill='x')

        self.add_outline_widget()

    def __choose_colour(self, ix):
        self.rgb[ix], self.colour[ix] = tkColorChooser.askcolor(initialcolor=self.colour[ix])
        self.w_color[ix].configure(foreground = self.colour[ix])

    def __choose_outline_colour(self):
        self.outline_rgb, self.outline_colour = tkColorChooser.askcolor(initialcolor=self.outline_colour)
        self.w_outline_colour.configure(foreground = self.outline_colour)

    def read_widgets(self):
        #self.sfac =  float(self.w_sfac.get())
        for i in range(5):
            self.tfv[i] =  float(self.w_tfv[i].get())
            # convert color format
            r, g, b = self.dialog.winfo_rgb(self.colour[i])
            self.rgb[i] = [r/256, g/256, b/256]
            self.opacity[i] =  float(self.w_opacity[i].get())


class VolumeDensityVisualiser(VolumeVisualiser):

    def __init__(self, root, graph, obj, **kw):

        VolumeVisualiser.__init__(self, root, graph, obj, **kw)
        self.title = 'Density Volume Visualisation: ' + self.field.title
        self.setvalues()

    def setvalues(self):
        self.tfv = [ 0.0, 0.1, 0.5, 2.0, 10.0 ]
        self.rgb = [ [ 0,255,0],[0,0,255],[255,0,0],[255,255,0],[0,255,255]]
        self.colour = ['#00ff00',  '#0000ff',  '#ff0000', '#ffff00', '#00ffff' ]
        self.opacity = [0.1, 0.3, 0.5, 0.7, 0.9 ]
        self.sfac = 100.0

class VolumeOrbitalVisualiser(VolumeVisualiser):

    def __init__(self, root, graph, obj, **kw):

        VolumeVisualiser.__init__(self, root, graph, obj, **kw)
        self.title = 'Density Orbital Visualisation: ' + self.field.title
        self.setvalues()

    def setvalues(self):
        self.tfv = [ -0.1, -0.05, 0.0, 0.05, 0.1 ]
        self.rgb = [ [ 0,0,255],[0,0,255],[255,255,255],[255,0,0],[255,0,0]]
        self.colour = ['#0000ff',  '#0000ff',  '#ffffff', '#ff0000', '#ff0000' ]
        self.opacity = [0.8, 0.4, 0.0, 0.4, 0.8 ]
        #self.sfac = 10.0

class ColourSurfaceVisualiser(IsoSurfaceVisualiser):

    def __init__(self, root, graph, obj, colour_obj=None,**kw):

        IsoSurfaceVisualiser.__init__(self, root, graph, obj, data_summary=1,**kw)
        # Default settings
        self.height = 0.05
        self.opacity = 1.0
        self.field = obj
        
        self.colourer.set_value('plus_colour','#00ff00')
        self.colourer.set_value('plus_rgb',[0, 255, 0])
        self.colourer.set_value('cmap_obj',None)
        self.colourer.set_value('cmap_low',-50)
        self.colourer.set_value('cmap_high',50)
        self.title = 'Coloured Isosurface of ' + self.field.title

    def _make_dialog(self):

        surface_group  = Pmw.Group(self.dialog.topframe, tag_text="Surfaces")
        f = surface_group.interior()

        self.w_height = Pmw.Counter(f,
                                    labelpos = 'w',
                                    label_text = 'Contour Height',
                                    entryfield_value = self.height,
                                    entryfield_entry_width = 5,
                                    increment=0.005,
                                    datatype = {'counter' : 'real' },
                                    entryfield_validate = { 'validator' : 'real' })

        self.w_height.pack(side='top')

        self.opacity_widget(frame=f)
        surface_group.pack(side='top',fill='x')

        self.colourchooser = ColourChooser(
            f,
            self.colourer,
            schemes=['Uniform'],
            graph=self.graph,
            choose_field=1
            )
        self.colourchooser.widget.pack(side='top',fill='x',expand=1)

        self.add_outline_widget()

        Pmw.alignlabels([ self.w_height, self.w_opacity ] )

    def read_widgets(self):
        self.height =  float(self.w_height.get())

        self.colourchooser.read_widgets()
        
        self.read_opacity_widgets()
        
class GridVisualiser(Visualiser):
    def __init__(self, root, graph, obj, **kw):
        aVisualiser.__init__(self, root, graph, obj, **kw)
        self.field = obj


STREAM_LINES='lines'
STREAM_TUBES='tubes'
STREAM_SURFACE='surface'
STREAM_FORWARD=11
STREAM_BACKWARD=12
STREAM_BOTH=13
VECTOR_SAMPLE_ALL = 10

class VectorVisualiser(DataVisualiser):
    """visualise a vector field
    Display a slice through a 3D dataset
    Relies on SliceVisualiser for most of the code, uses
    a GridEditor widget to position the slice
    """

    def __init__(self, root, graph, obj, colour_obj_choice=None, colour_obj_list=None, **kw):
        DataVisualiser.__init__(self, root, graph, obj, data_summary=1,**kw)
        self.grid_editor=None

        #jmht - hack
        self.cut_plane=Field(nd=2)
        #self.cut_plane.dim = [21,21]
        # In increase the number of points
        self.cut_plane.dim = [51,51]
        # Shift the axis of the sampling grid to match the data
        self.cut_plane.origin += obj.origin
        # Set the x & y axes to be the same
        self.cut_plane.axis[0] = obj.axis[0] 
        #self.cut_plane.axis[1] = obj.axis[2]
        self.cut_plane.axis[1] = obj.axis[1]
        
        self.field = obj
        self.title = 'Vector View: ' + self.field.title

        try:
            dummy = obj.dim
            if len(obj.dim) == 3:
                self.regular3 = 1
            else:
                self.regular3 = 0
        except AttributeError:
            self.regular3 = 0            

        # Seem to need this (no read_widgets before first build?)

        # Heddgehog
        self.hedgehog_scale=1.0
        self.show_hedgehog = 0
        self.hedgehog_colourer = Colourer(graph)
        self.hedgehog_colourer.set_value("plus_colour", '#ffffff' )
        self.hedgehog_colourer.set_value("plus_rgb", [255,255,255] )
        self.hedgehog_colourer.set_value("cmap_low", -1 )
        self.hedgehog_colourer.set_value("cmap_high", 1 )

        
        # Oriented glyphs
        self.orientedglyph_scale=1.0
        self.show_orientedglyphs = 0
        self.orientedglyphs_colourer = Colourer(graph)
        self.orientedglyphs_colourer.set_value("plus_colour", '#646464' )
        self.orientedglyphs_colourer.set_value("plus_rgb", [100,100,100] )
        self.orientedglyphs_colourer.set_value("cmap_low", -1 )
        self.orientedglyphs_colourer.set_value("cmap_high", 1 )

        # Streamlines
        self.show_streamlines = 0
        
        self.streamlines_colourer = Colourer(graph)
        self.streamlines_colourer.set_value("cmap_low", -1 )
        self.streamlines_colourer.set_value("cmap_high", 1 )
        self.streamlines_colourer.set_value("plus_colour", '#ffffff' )
        self.streamlines_colourer.set_value("plus_rgb", [255,255,255] )
        
        self.streamline_propagation_time=5.0
        self.streamline_integration_step_length=0.2
        self.streamline_step_length=0.05
        self.streamline_display = STREAM_LINES
        self.streamline_integration_direction = STREAM_FORWARD
        self.streamline_thin_points=1

        # Streamarrows
        self.show_streamarrows = 0
        
        self.streamarrows_colourer = Colourer(graph)
        self.streamarrows_colourer.set_value("cmap_low", -1 )
        self.streamarrows_colourer.set_value("cmap_high", 1 )
        self.streamarrows_colourer.set_value("plus_colour", '#646464' )
        self.streamarrows_colourer.set_value("plus_rgb", [100,100,100] )
        
        self.streamarrow_propagation_time=5.0
        self.streamarrow_integration_step_length=0.2
        self.streamarrow_time_increment=10
        self.streamarrow_integration_direction = STREAM_FORWARD
        self.streamarrow_size=0.3
        self.streamarrow_thin_points=1
        self.streamarrow_scale=0
        self.streamarrow_type="Arrow"

        if self.regular3:
            self.sample_grid = self.cut_plane
        else:
            self.sample_grid = VECTOR_SAMPLE_ALL


    def _make_dialog(self, **kw):

        #print 'vectorvis.make_dialog'
        #labels = []

        # Hedgehog widget group
        if self.graph.check_capability('hedgehog'):
            self._make_hedgehog_dialog()
            
        # Oriented glyph widget group
        if self.graph.check_capability('orientedglyphs'):
            self._make_orientedglyphs_dialog()

        # Streamlines
        if self.graph.check_capability('streamlines'):
            self._make_streamlines_dialog()

        # Streamarrows
        if self.graph.check_capability('streamarrows'):
            self._make_streamarrows_dialog()
            
##            Pmw.alignlabels(labels)

        self.sample_var = Tkinter.StringVar()
        if self.regular3:
            # Specification of the sampling grid

            self.sample_group = Pmw.Group(self.dialog.topframe ,tag_text='Sampling Grid')

            # Checkbox to decide whether we display the grid editor
            self.grideditor_show_var = Tkinter.BooleanVar()
            self.grideditor_show_var.set(0) # Hide by default - only show if requested
            self.w_grid_lab = Pmw.LabeledWidget(self.sample_group.interior(),labelpos='w',label_text='Display')
            self.w_grid = Tkinter.Checkbutton(self.w_grid_lab.interior())
            self.w_grid.config(variable=self.grideditor_show_var)
            self.w_grid.config(command=lambda s=self: s.grideditor_show() )
            self.w_grid.pack(side='top')
            self.w_grid_lab.pack(side='top')

            # The Frame that hold the grid editor widgets
            self.grideditor_frame=Tkinter.Frame(
                self.sample_group.interior())
            
            self.sample_var = Tkinter.StringVar()
            #self.sample_grid_menu = Pmw.OptionMenu(self.sample_group.interior(),
            self.sample_grid_menu = Pmw.OptionMenu(self.grideditor_frame,
                                                   labelpos = 'w',
                                                   label_text = 'Sample at:',
                                                   menubutton_textvariable = self.sample_var,
                                                   items = ['dum'],
                                                   menubutton_width = 10)

            self.sample_grid_menu.pack(side='top')
            self.update_sample_grid_choice()

            #print ' creating grid editor'
#             self.grid_editor = GridEditorWidget(
#                 self.sample_group.interior(),
#                 self.cut_plane,
#                 command = self.__reslice,close_ok=0)
            self.grid_editor = GridEditorWidget(
                self.grideditor_frame,
                self.cut_plane,
                command = self.__reslice,close_ok=0)
            #print ' packing grid editor'
            self.grid_editor.pack(side='top')
            self.sample_group.pack(side='top',fill='x')
            #print ' grid editor make_dialog done'
            self.grideditor_show()
        else:
            self.sample_var.set('All Field Points')


    def _make_hedgehog_dialog(self):
        """ Create the dialog to display a hedgehog plot"""
        
        self.hedgehog_var = Tkinter.BooleanVar()
        self.hedgehog_var.set(self.show_hedgehog)

        self.hedgehog_group = Pmw.Group(
            self.dialog.topframe ,tag_text='Hedgehog')

        
        f = Tkinter.Frame(self.hedgehog_group.interior())
        f.pack(side='top')

        self.w_hedgehog_lab = Pmw.LabeledWidget(f,labelpos='w',label_text='Display')
        self.w_hedgehog = Tkinter.Checkbutton(self.w_hedgehog_lab.interior())
        self.w_hedgehog.config(variable=self.hedgehog_var)
        self.w_hedgehog.config(command=lambda s=self: s.__read_buttons() )
        self.w_hedgehog.pack(side='top')
        self.w_hedgehog_lab.pack(side='left')

        self.w_hedgehog_scale = Pmw.Counter(
            f, labelpos = 'w',
            label_text = 'Scale vectors by',
            entryfield_value = self.hedgehog_scale,
            entryfield_entry_width = 5,
            increment=0.1,
            datatype = {'counter' : 'real' },
            entryfield_validate = { 'validator' : 'real' })

        self.w_hedgehog_scale.pack(side='left')
        #labels.append(self.w_hedgehog_scale)
        
        self.hedgehog_colourchooser = ColourChooser(
            self.hedgehog_group.interior(),
            self.hedgehog_colourer,
            schemes=['Uniform'],
            graph=self.graph,
            choose_field=1
            )
        self.hedgehog_colourchooser.widget.pack(side='bottom',fill='x',expand=1)        

        self.hedgehog_group.pack(side='top',fill='x')

    def _make_orientedglyphs_dialog(self):
        """Create the dialog to display oriented glyphs"""
    
        self.orientedglyphs_var = Tkinter.BooleanVar()
        self.orientedglyphs_var.set(self.show_orientedglyphs)

        self.orientedglyphs_group = Pmw.Group(
            self.dialog.topframe ,tag_text='Oriented Glyphs')
        
        f = Tkinter.Frame(self.orientedglyphs_group.interior())
        f.pack(side='top')

        self.w_orientedglyphs_lab = Pmw.LabeledWidget(
            f,labelpos='w',label_text='Display')

        self.w_orientedglyphs = Tkinter.Checkbutton(self.w_orientedglyphs_lab.interior())
        self.w_orientedglyphs.config(variable=self.orientedglyphs_var)
        self.w_orientedglyphs.config(command=lambda s=self: s.__read_buttons() )
        self.w_orientedglyphs.pack(side='left')

        self.w_orientedglyphs_lab.pack(side='left')

        self.w_orientedglyph_scale = Pmw.Counter(
            f,
            labelpos = 'w', label_text = 'Scale glyphs by',
            entryfield_value = self.orientedglyph_scale,
            entryfield_entry_width = 5,
            increment=0.1,
            datatype = {'counter' : 'real' },
            entryfield_validate = { 'validator' : 'real' })
        self.w_orientedglyph_scale.pack(side='left')
        #labels.append(self.w_orientedglyph_scale)

        self.orientedglyphs_colourchooser = ColourChooser(
            self.orientedglyphs_group.interior(),
            self.orientedglyphs_colourer,
            schemes=['Uniform'],
            graph=self.graph,
            choose_field=1
            )
        self.orientedglyphs_colourchooser.widget.pack(side='bottom',fill='x',expand=1)        

        self.orientedglyphs_group.pack(side='top',fill='x')


    def _make_streamlines_dialog(self):
        """Layout the dialog to display streamlines"""

        self.streamlines_var = Tkinter.BooleanVar()
        self.streamlines_var.set(self.show_streamlines)

        self.streamlines_group = Pmw.Group(
            self.dialog.topframe ,tag_text='Streamlines')

        # Create a widget to show/hide the rest of the tools in this group
        # The rest of the tools are all packed in self.streamlines_frame
        # so that we can just show or hide that one frame
        self.w_streamlines_show = Pmw.LabeledWidget(
            self.streamlines_group.interior(),labelpos='w',label_text='Display')
        self.w_streamlines = Tkinter.Checkbutton(self.w_streamlines_show.interior())
        self.w_streamlines.config(variable=self.streamlines_var)
        self.w_streamlines.config(command=lambda s=self: s.show_streamline_widgets() )
        self.w_streamlines.pack(side='top')
        self.w_streamlines_show.pack(side='top')


        self.streamlines_frame = Tkinter.Frame( self.streamlines_group.interior() )
        f1 = Tkinter.Frame(self.streamlines_frame)
        f2 = Tkinter.Frame(self.streamlines_frame)
        f3 = Tkinter.Frame(self.streamlines_frame)
        f4 = Tkinter.Frame(self.streamlines_frame)

        self.w_streamline_propagation_time = Pmw.Counter(
            f1,
            labelpos = 'w', label_text = 'Propagation Time',
            entryfield_value = self.streamline_propagation_time,
            entryfield_entry_width = 5,
            increment=0.1,
            datatype = {'counter' : 'real' },
            entryfield_validate = { 'validator' : 'real' })

        self.w_streamline_propagation_time.pack(side='left')
        #labels.append(self.w_streamline_propagation_time)

        # Thin the number of starting points
        self.w_streamline_thin_points = Pmw.Counter(
            f1,
            labelpos = 'w', label_text = 'Thin Points',
            entryfield_value = self.streamline_thin_points,
            entryfield_entry_width = 2,
            increment=1,
            datatype = {'counter' : 'integer' },
            entryfield_validate = { 'validator' : 'integer',
                                    'min' : '1',
                                    })
        self.w_streamline_thin_points.pack(side='left')
        #labels.append(self.w_streamline_thin_points)


        self.w_streamline_integration_step_length = Pmw.Counter(
            f2,
            labelpos = 'w', label_text = 'Integ Step Length',
            entryfield_value = self.streamline_integration_step_length,
            entryfield_entry_width = 5,
            increment=0.1,
            datatype = {'counter' : 'real' },
            entryfield_validate = { 'validator' : 'real' })

        self.w_streamline_integration_step_length.pack(side='left')
        #labels.append(self.w_streamline_integration_step_length)

        self.w_streamline_step_length = Pmw.Counter(
            f2,
            labelpos = 'w', label_text = 'Step Length',
            entryfield_value = self.streamline_step_length,
            entryfield_entry_width = 5,
            increment=0.1,
            datatype = {'counter' : 'real' },
            entryfield_validate = { 'validator' : 'real' })

        self.w_streamline_step_length.pack(side='left')
        #labels.append(self.w_streamline_step_length)

        self.streamline_display_mode_var = Tkinter.StringVar()
        self.w_streamline_display_mode = Pmw.OptionMenu(
            f3,
            labelpos = 'w',
            label_text = 'Display:',
            menubutton_textvariable = self.streamline_display_mode_var,
            items = [STREAM_LINES,STREAM_TUBES,STREAM_SURFACE],
            initialitem=self.streamline_display,
            menubutton_width = 8)

        self.w_streamline_display_mode.pack(side='left')
        #labels.append(self.w_streamline_display_mode)

        self.streamline_integration_direction_var = Tkinter.StringVar()
        self.w_streamline_integration_direction = Pmw.OptionMenu(
            f3,
            labelpos = 'w',
            label_text = 'Integrate ',
            menubutton_textvariable = self.streamline_integration_direction_var,
            items = ['forward','backward','both directions'],
            initialitem='both directions',
            menubutton_width = 10)

        self.w_streamline_integration_direction.pack(side='left')
        #labels.append(self.w_streamline_integration_direction)

        self.streamlines_colourchooser = ColourChooser(
            f4,
            self.streamlines_colourer,
            schemes=['Uniform','Speed'],
            graph=self.graph,
            choose_field=1
            )
        self.streamlines_colourchooser.widget.pack(side='bottom',fill='x',expand=1)        

        f1.pack(side='top')
        f2.pack(side='top')
        f3.pack(side='top')
        f4.pack(side='top')
        self.streamlines_group.pack(side='top',fill='x')

        # Decide whether we need to be packed or not
        self.show_streamline_widgets()

    def _make_streamarrows_dialog(self):
        """Create the dialog to display streamarrows"""

        self.streamarrows_var = Tkinter.BooleanVar()
        self.streamarrows_var.set(self.show_streamarrows)
        self.streamarrows_group = Pmw.Group(
            self.dialog.topframe ,tag_text='StreamArrows')

        self.w_streamarrows_lab = Pmw.LabeledWidget(
            self.streamarrows_group.interior(),labelpos='w',label_text='Display')
        self.w_streamarrows = Tkinter.Checkbutton(self.w_streamarrows_lab.interior())
        self.w_streamarrows.config(variable=self.streamarrows_var)
        self.w_streamarrows.config(command=lambda s=self: s.show_streamarrow_widgets() )
        self.w_streamarrows.pack(side='top')
        self.w_streamarrows_lab.pack(side='top')

        self.streamarrows_frame = Tkinter.Frame( self.streamarrows_group.interior() )
        f1 = Tkinter.Frame(self.streamarrows_frame)
        f2 = Tkinter.Frame(self.streamarrows_frame)
        f3 = Tkinter.Frame(self.streamarrows_frame)
        f4 = Tkinter.Frame(self.streamarrows_frame)

        self.w_streamarrow_propagation_time = Pmw.Counter(
            f1,
            labelpos = 'w', label_text = 'Propagation Time',
            entryfield_value = self.streamarrow_propagation_time,
            entryfield_entry_width = 5,
            increment=0.1,
            datatype = {'counter' : 'real' },
            entryfield_validate = { 'validator' : 'real' })
        self.w_streamarrow_propagation_time.pack(side='left')
        #labels.append(self.w_streamarrow_propagation_time)

        self.w_streamarrow_integration_step_length = Pmw.Counter(
            f1,
            labelpos = 'w', label_text = 'Integ Step Length',
            entryfield_value = self.streamarrow_integration_step_length,
            entryfield_entry_width = 5,
            increment=0.1,
            datatype = {'counter' : 'real' },
            entryfield_validate = { 'validator' : 'real' })
        self.w_streamarrow_integration_step_length.pack(side='left')
        #labels.append(self.w_streamarrow_integration_step_length)

        self.streamarrow_integration_direction_var = Tkinter.StringVar()
        self.w_streamarrow_integration_direction = Pmw.OptionMenu(
            f2,
            labelpos = 'w',
            label_text = 'Integrate ',
            menubutton_textvariable = self.streamarrow_integration_direction_var,
            items = ['forward','backward','both directions'],
            initialitem='both directions',
            menubutton_width = 10)
        self.w_streamarrow_integration_direction.pack(side='left')
        #labels.append(self.w_streamarrow_integration_direction)

        self.w_streamarrow_time_increment = Pmw.Counter(
            f2,
            labelpos = 'w', label_text = 'Time Increment',
            entryfield_value = self.streamarrow_time_increment,
            entryfield_entry_width = 5,
            increment=0.1,
            datatype = {'counter' : 'real' },
            entryfield_validate = { 'validator' : 'real' })
        self.w_streamarrow_time_increment.pack(side='left')
        #labels.append(self.w_streamarrow_time_increment)

        # Widget for selecting whether to reduce the number of points
        # that the streamarrow integration starts from
        self.w_streamarrow_thin_points = Pmw.Counter(
            f3,
            labelpos = 'w', label_text = 'Thin Points',
            entryfield_value = self.streamarrow_thin_points,
            entryfield_entry_width = 2,
            increment=1,
            datatype = {'counter' : 'integer' },
            entryfield_validate = { 'validator' : 'integer',
                                    'min' : '1',
                                    })
        self.w_streamarrow_thin_points.pack(side='left')
        #labels.append(self.w_streamarrow_thin_points)

        # Size of the arrows
        self.w_streamarrow_size = Pmw.Counter(
            f3,
            labelpos = 'w', label_text = 'Size',
            entryfield_value = self.streamarrow_size,
            entryfield_entry_width = 5,
            increment=0.1,
            datatype = {'counter' : 'real' },
            entryfield_validate = { 'validator' : 'real',
                                    'min' : '0.0',
                                    })
        self.w_streamarrow_size.pack(side='left')
        #labels.append(self.w_streamarrow_size)

        # Select whether to scale the arrows by the vector
        self.streamarrows_scale_var = Tkinter.BooleanVar()
        self.w_streamarrows_scalel = Pmw.LabeledWidget(
            f3,labelpos='w',label_text='Scale')
        self.w_streamarrows_scale = Tkinter.Checkbutton(self.w_streamarrows_scalel.interior())
        self.w_streamarrows_scale.config(variable=self.streamarrows_scale_var)
        self.w_streamarrows_scale.config(command=lambda s=self: s.__read_buttons() )
        self.w_streamarrows_scale.pack(side='top')
        self.w_streamarrows_scalel.pack(side='left')

        # Select what sort of glyph to use
        self.streamarrows_type_var = Tkinter.StringVar()
        self.w_streamarrow_type = Pmw.OptionMenu(
            f4,
            labelpos = 'w',
            label_text = 'Glyph Type ',
            menubutton_textvariable = self.streamarrows_type_var,
            items = ['Arrow','Cone'],
            initialitem=self.streamarrow_type,
            menubutton_width = 10)
        self.w_streamarrow_type.pack(side='left')

        self.streamarrows_colourchooser = ColourChooser(
            self.streamarrows_frame,
            self.streamarrows_colourer,
            schemes=['Uniform','Vector'],
            graph=self.graph,
            choose_field=1
            )

        f1.pack(side='top')
        f2.pack(side='top')
        f3.pack(side='top')
        f4.pack(side='top')
        self.streamarrows_colourchooser.widget.pack(side='top',fill='x',expand=1)
        self.streamarrows_group.pack(side='top',fill='x')
        
        #Decide whether to pack the frame or no
        self.show_streamarrow_widgets()

    def show_streamline_widgets(self):
        s = self.streamlines_var.get()
        if s:
            self.streamlines_frame.pack(side='top') 
        else:
            self.streamlines_frame.forget()

    def show_streamarrow_widgets(self):
        s = self.streamarrows_var.get()
        if s:
            self.streamarrows_frame.pack(side='top') 
        else:
            self.streamarrows_frame.forget()

    def grideditor_show(self):
        s = self.grideditor_show_var.get()
        if s:
            self.grideditor_frame.pack()
        else:
            self.grideditor_frame.forget()


    def enable_dialog(self):
        #jmht
        if self.regular3:
            self.grid_editor.dynamic_update = 1

    def disable_dialog(self):
        if self.regular3:
            self.grid_editor.dynamic_update = 0

    def update_sample_grid_choice(self):

        items = []
        items.append('All Field Points')
        items.append('Internal 2D')

        for o in self.graph.data_list:
            t1 = string.split(str(o.__class__),'.')
            myclass = t1[len(t1)-1]
            if myclass == 'Field':
                items.append(o.name)

        self.sample_grid_menu.setitems(items)
        self.sample_grid_menu.setvalue('Internal 2D')

##    def update_colour_choices(self):

##        items = []
##        items.append('None')
##        ######still need to figure out how to generate this
##        ######items.append('Vector Magnitude')
##        for o in self.graph.data_list:
##            t1 = string.split(str(o.__class__),'.')
##            myclass = t1[len(t1)-1]
##            if myclass == 'Field' and o.ndd == 1:
##                items.append(o.name)

##        self.colour_obj_menu.setitems(items)
##        self.colour_obj_menu.setvalue('None')

    def __reslice(self,cut_field):
        """ Recompute the slice and re-visualise"""
        # free up old objects?
        self.Build()

    def __read_buttons(self):
        if self.debug:
            deb("__read_buttons")

    def read_widgets(self):

        # Hedgehog
        if self.graph.check_capability('hedgehog'):
            self.show_hedgehog = self.hedgehog_var.get()
            self.hedgehog_scale = float(self.w_hedgehog_scale.get())
            self.hedgehog_colourchooser.read_widgets()

        # Oriented Glyphs
        if self.graph.check_capability('orientedglyphs'):
            self.show_orientedglyphs = self.orientedglyphs_var.get()
            self.orientedglyph_scale = float(self.w_orientedglyph_scale.get())
            self.orientedglyphs_colourchooser.read_widgets()

        # Streamlines
        if self.graph.check_capability('streamlines'):
            self.show_streamlines = self.streamlines_var.get()
            #self.streamline_colourmap = self.streamlines_cmap_var.get()
            self.streamlines_colourchooser.read_widgets()
            self.streamline_propagation_time=float(
                self.w_streamline_propagation_time.get())
            self.streamline_integration_step_length=float(
                self.w_streamline_integration_step_length.get())
            self.streamline_step_length=float(self.w_streamline_step_length.get())
            self.streamline_thin_points=int(self.w_streamline_thin_points.get())
            
            v = self.streamline_integration_direction_var.get()
            if v == 'forward':
                self.streamline_integration_direction = STREAM_FORWARD
            elif v == 'backward':
                self.streamline_integration_direction = STREAM_BACKWARD
            elif v == 'both directions':
                self.streamline_integration_direction = STREAM_BOTH

            self.streamline_display = self.streamline_display_mode_var.get()

        # Streamarrows
        if self.graph.check_capability('streamarrows'):
            self.show_streamarrows = self.streamarrows_var.get()
            #self.streamarrow_colourmap = self.streamarrows_cmap_var.get()
            self.streamarrows_colourchooser.read_widgets()
            self.streamarrow_type = self.streamarrows_type_var.get()
            self.streamarrow_scale = self.streamarrows_scale_var.get()
            self.streamarrow_propagation_time=float(
                self.w_streamarrow_propagation_time.get())
            self.streamarrow_time_increment=float(
                self.w_streamarrow_time_increment.get())
            self.streamarrow_integration_step_length=float(
                self.w_streamarrow_integration_step_length.get())
            self.streamarrow_size=float(self.w_streamarrow_size.get())
            self.streamarrow_thin_points=int(
                self.w_streamarrow_thin_points.get())
            
            v = self.streamarrow_integration_direction_var.get()
            if v == 'forward':
                self.streamarrow_integration_direction = STREAM_FORWARD
            elif v == 'backward':
                self.streamarrow_integration_direction = STREAM_BACKWARD
            elif v == 'both directions':
                self.streamlarrow_integration_direction = STREAM_BOTH


        #print 'READW'

        v = self.sample_var.get()
        if v == 'All Field Points':
            self.sample_grid = VECTOR_SAMPLE_ALL
        elif v == 'Internal 2D':
            self.sample_grid = self.cut_plane
        else:
            self.sample_grid = None
            for o in self.graph.data_list:
                t1 = string.split(str(o.__class__),'.')
                myclass = t1[len(t1)-1]
                if myclass == 'Field':
                    if o.name == v:
                        self.sample_grid = o
            if self.sample_grid is None:
                print 'Problem locating sampling grid'

        if self.grid_editor is not None:
            # transform the grid, but do not trigger the the build that
            # normally results
            self.grid_editor.transform(callback=0)

class SliceVisualiser(DataVisualiser):
    """Represent a regular 2D grid using contour and colourmap
    representations and an outline. Can optionally render to the 2D
    window for preparation of printed plots.
    """
    def __init__(self, root, graph, obj, colour_obj_choice=None, colour_obj_list=None, **kw):

        DataVisualiser.__init__(self, root, graph, obj,data_summary=0,**kw)

        
        # Try and work out sensible starting values
        mymin = -50
        mymax =  50
                
        # Get max and min from the field
        #mymin,mymax = obj.minmax()

        # Default settings
        self.min = mymin
        self.max = mymax
        self.ncont = 21
        self.opacity = 1.0

        # Setup the two colourers for contours and pcmap
        self.contour_colourer = Colourer(graph)
        self.pcmap_colourer = Colourer(graph)
        
        #self.contour_cmap_name = 'Default'
        #self.contour_cmap_low = mymin
        #self.contour_cmap_high = mymax
        self.contour_colourer.set_value("cmap_low",mymin)
        self.contour_colourer.set_value("cmap_high",mymax)

        #self.pcmap_cmap_name = 'Default'
        #self.pcmap_cmap_low = mymin
        #self.pcmap_cmap_high = mymax
        self.pcmap_colourer.set_value("cmap_low",mymin)
        self.pcmap_colourer.set_value("cmap_high",mymax)

        # switches for parts of image
        self.show_cont = 1
        self.show_plane = 0
        self.show_outline = 1

        #self.plus_colour   =  '#00ff00'
        #self.plus_rgb = [0, 255, 0]

        self.outline_colour = '#ffffff'
        self.outline_rgb = [255,255,255]

        self.field = obj
        self.title = '2D View: ' + self.field.title
        
    def _make_dialog(self):

        self.cont_var                = Tkinter.BooleanVar()
        self.plane_var               = Tkinter.BooleanVar()
        self.outline_var             = Tkinter.BooleanVar()
        self.var2d                   = Tkinter.BooleanVar()

        self.cont_var.set(self.show_cont)
        self.plane_var.set(self.show_plane)
        self.outline_var.set(self.show_outline)
        self.var2d.set(self.show_2d)


        self.w_min = Pmw.Counter(self.dialog.topframe,
                                 labelpos = 'w',
                                 label_text = 'Min Contour Height',
                                 entryfield_value = self.min,
                                 entryfield_entry_width = 5,
                                 increment=0.005,
                                 datatype = {'counter' : 'real' },
                                 entryfield_validate = { 'validator' : 'real' })

        self.w_max = Pmw.Counter(self.dialog.topframe,
                                 labelpos = 'w',
                                 label_text = 'Max Contour Height',
                                 entryfield_value = self.max,
                                 entryfield_entry_width = 5,
                                 increment=0.005,
                                 datatype = {'counter' : 'real' },
                                 entryfield_validate = { 'validator' : 'real' })

        self.w_ncont = Pmw.Counter(self.dialog.topframe,
                                   labelpos = 'w',
                                   label_text = 'Number of Contours',
                                   entryfield_value = self.ncont,
                                   increment=5,
                                   entryfield_entry_width = 5,
                                   datatype = {'counter' : 'integer' },
                                   entryfield_validate = { 'validator' : 'integer' })

        self.opacity_widget()

        self.repframe = Pmw.Group(self.dialog.topframe, tag_text="Representations")

        labs = []
        self.cont_frame = Pmw.LabeledWidget(
            self.repframe.interior() ,labelpos='w',label_text='Contours')
        self.cont = Tkinter.Checkbutton(self.cont_frame.interior())
        self.cont.config(variable=self.cont_var)
        self.cont.config(command=lambda s=self: s.__read_buttons() )
        self.cont_frame.pack(side='top')
        self.cont.pack(side='top')
        labs.append(self.cont_frame)

        self.plane_frame = Pmw.LabeledWidget(
            self.repframe.interior() ,labelpos='w',label_text='Colourmap')
        self.plane = Tkinter.Checkbutton(self.plane_frame.interior())
        self.plane.config(variable=self.plane_var)
        self.plane.config(command=lambda s=self: s.__read_buttons() )
        self.plane_frame.pack(side='top')
        self.plane.pack(side='top')
        labs.append(self.plane_frame)
        
        self.outline_frame = Pmw.LabeledWidget(
            self.repframe.interior() ,labelpos='w',label_text='Border')
        self.outline = Tkinter.Checkbutton(self.outline_frame.interior())
        self.outline.config(variable=self.outline_var)
        self.outline.config(command=lambda s=self: s.__read_buttons() )
        self.outline_frame.pack(side='top')
        self.outline.pack(side='top')
        labs.append(self.outline_frame)

        self.frame2d = Pmw.LabeledWidget(
            self.repframe.interior() ,labelpos='w',label_text='2D Representation')
        self.widget2d = Tkinter.Checkbutton(self.frame2d.interior())
        self.widget2d.config(variable=self.var2d)
        self.widget2d.config(command=lambda s=self: s.__read_buttons() )
        self.frame2d.pack(side='top')
        self.widget2d.pack(side='top')
        labs.append(self.frame2d)

        Pmw.alignlabels(labs)
                        
        f = Tkinter.Frame(self.dialog.topframe)
        self.w_outline_colour_lab = Tkinter.Label(f,text='Edit Outline Colour:      ')
        self.w_outline_colour = Tkinter.Button(f,
                                             text = 'oOo',
                                             foreground = self.outline_colour,
                                             command= self.__choose_outline_colour)

        self.w_outline_colour_lab.pack(side='left')
        self.w_outline_colour.pack(side='left')
        f.pack(side='top')

        self.repframe.pack(side='top',fill='x')

        self.contour_colourchooser = ColourChooser(
            self.dialog.topframe,
            self.contour_colourer,
            schemes=[],
            graph=self.graph,
            choose_field=1,
            title="Contour Colouring"
            )
        self.contour_colourchooser.widget.pack(side='top',fill='x',expand=1)        

        self.pcmap_colourchooser = ColourChooser(
            self.dialog.topframe,
            self.pcmap_colourer,
            schemes=[],
            graph=self.graph,
            choose_field=1,
            title="ColourSurface Colouring"
            )
        self.pcmap_colourchooser.widget.pack(side='top',fill='x',expand=1)        

        
        self.w_min.pack(side='top')
        self.w_max.pack(side='top')
        self.w_ncont.pack(side='top')

    def __choose_outline_colour(self):
        self.outline_rgb, self.outline_colour = tkColorChooser.askcolor(initialcolor=self.outline_colour)
        self.w_outline_colour.configure(foreground = self.outline_colour)

    def __read_buttons(self):
        self.show_cont = self.cont_var.get()
        self.show_plane = self.plane_var.get()
        self.show_outline = self.outline_var.get()
        self.show_2d  = self.var2d.get()
        if self.debug:
            deb('settings'+str(self.show_cont)+str(self.show_plane)+ 
                str(self.show_outline)+str(self.show_2d))

    def read_widgets(self):
        self.min = float(self.w_min.get())
        self.max = float(self.w_max.get())
        self.ncont = int(self.w_ncont.get())
        self.read_opacity_widgets()
        self.contour_colourchooser.read_widgets()
        self.pcmap_colourchooser.read_widgets()

class CutSliceVisualiser(SliceVisualiser):
    """Display a slice through a 3D dataset
    Relies on SliceVisualiser for most of the code, uses
    a GridEditor widget to position the slice
    """
    def __init__(self, root, graph, obj, colour_obj_choice=None, colour_obj_list=None, **kw):
        SliceVisualiser.__init__(self, root, graph, obj,**kw)
        self.grid_editor=None

        # Set up a sensible default for the slice plane
        # Try inheriting the origin and x and y axes
        self.cut_plane=Field(nd=2)
        
        # jmht
        if obj.vtkdata:
            # Need to check the order here to make sure we are using the correct dims
            self.cut_plane.dim = [ obj.dim[0], obj.dim[1] ]
        else:
            self.cut_plane.dim = [21,21]
            
        self.cut_plane.origin = obj.origin

        len = math.sqrt(obj.axis[1]*obj.axis[1])
        self.cut_plane.axis = [ obj.axis[0], len*obj.axis[0].cross(obj.axis[2]).normal() ]

        self.title = 'Cut Slice View: ' + self.field.title

    def _make_dialog(self, **kw):
        SliceVisualiser._make_dialog(self,**kw)
        self.grid_editor = GridEditorWidget(self.dialog.topframe, self.cut_plane, command = self.__reslice, close_ok=0)
        self.grid_editor.pack(side='top')

    def enable_dialog(self):
        self.grid_editor.dynamic_update = 1

    def disable_dialog(self):
        self.grid_editor.dynamic_update = 0

    def __reslice(self,cut_field):
        """ Recompute the slice and re-visualise"""
        # free up old objects?
        self.Build()

    def read_widgets(self):
        SliceVisualiser.read_widgets(self)
        if self.grid_editor is not None:
            # transform the grid, but do not trigger the the build that
            # normally results
            self.grid_editor.transform(callback=0)

class IrregularDataVisualiser(DataVisualiser):
    """Viewer for unstructured grid of data points
    currently only offers coloured dots.
    """
    def __init__(self, root, graph, obj, **kw):
        DataVisualiser.__init__(self, root, graph, obj,**kw)
        self.field = obj

        self.colourer = Colourer(graph)
        # Seem to need this (no read_widgets before first build?)
        self.colourer.set_value("cmap_low",-50)
        self.colourer.set_value("cmap_high",-50)

        self.point_size = graph.field_point_size
        self.opacity = 1.0
        self.title = "Grid View: " + obj.title

    def _make_dialog(self):
        self.w_point_size = Pmw.Counter(
            self.dialog.topframe,
            labelpos = 'w', label_text = 'Point Size',
            entryfield_value = self.point_size,
            entryfield_entry_width = 5,
            increment=1,
            datatype = {'counter' : 'integer' },
            entryfield_validate = { 'validator' : 'integer' })
        self.w_point_size.pack(side='top')

        self.opacity_widget()
        
        self.colourchooser = ColourChooser(
            self.dialog.topframe,
            self.colourer,
            schemes=[],
            graph=self.graph,
            choose_field=1
            )
        self.colourchooser.widget.pack(side='top',fill='x',expand=1)        
        
        
    def read_widgets(self):
        self.point_size = int(self.w_point_size.get())

        self.read_opacity_widgets()

class AllMoleculeVisualiser( MoleculeVisualiser ):

    def __init__( self, root, graph ):

        # Pass an empty object to the base classes as we operate on multiple objects
        obj = None

        # Set up the data structures we'll need to change things
        self.graph = graph
        self.data_list = graph.data_list
        self.vis_list = graph.vis_list
        self.vis_dict = graph.vis_dict  # dict mapping structures to image;
                                        #one->many, each entry is a list
        self.query = graph.query # For popping up questions
                                        
        #apply(Visualiser.__init__, (self, root, graph, obj), kw)
        #apply( MoleculeVisualiser.__init__, (self, root, graph, obj), kw )
        # Weve got stuff to display so carry on
        kw_dict = {'allvis': '1'}
        Visualiser.__init__( self, root, graph, obj , **kw_dict )
        MoleculeVisualiser.__init__(self, root, graph, obj, **kw_dict )


    def update_mol_list(self):
        """ Update the list of molecules that we know about:
            objects with a class of Indexed or Zmatrix are molecules so
            these are the only ones we are interested in.
            This methods returns None if no molecules are present, so this
            method can be used to query whether we have any molecules.
        """
        #Build up a list of all the molecules
        self.molecule_list = []
        for obj in self.data_list:
            t = id(obj)
            # for each object see if it is a molecule
            t1 = string.split(str(obj.__class__),'.')
            myclass = t1[len(t1)-1]
            if myclass == 'Indexed' or myclass == 'Zmatrix':
                self.molecule_list.append( obj )

        # Return 0 if we've no molecules to display - call this to see if we are needed or not
        if ( len( self.molecule_list ) == 0 ):
            return None
        else:
            return 1

    # Now set about overloading the definitions that are specific
    # to single instances of molecules

    def set_vis_variables(self,vis):
        """ This takes the a vis - i.e. an image and sets all of the variables
            that define how it will be visualised from the values that have been
            set in the widget
        """    
        vis.show_wire = self.show_wire

        vis.show_spheres = self.show_spheres
        vis.sphere_table = self.sphere_table
        vis.sphere_scale = self.sphere_scale
        
        vis.show_labels = self.show_labels
        vis.label_scale = self.label_scale
        vis.label_with = self.label_with
        vis.label_rgb = self.label_rgb
        vis.label_colour = self.label_colour
        
        vis.show_sticks = self.show_sticks
        vis.cyl_rgb = self.cyl_rgb
        vis.cyl_colour = self.cyl_colour
        vis.cyl_width = self.cyl_width
        
        vis.show_contacts = self.show_contacts
        

    def View(self):
        """ Method invoked with the 'Update All' button is clicked. """
        
        self.update_mol_list()
        self.read_widgets()
        
        for molc in self.molecule_list:
            t = id(molc)
            try:
                visl = self.vis_dict[t]
                for vis in visl:
                    # set the variables
                    self.set_vis_variables( vis )
                    # Delete the old image and create a new one
                    vis._delete()
                    vis._build(object=None)
                    vis._show()
                    vis.is_showing=1
            except KeyError:
                pass
        self.graph.update()

            
    def Show(self):
        """ Method invoked with the 'Show All' button is clicked. """
            
        self.update_mol_list()
        # Loop across all molecules and display the images
        for molc in self.molecule_list:
            t = id(molc)
            try:
                visl = self.vis_dict[t]
                for vis in visl:
                    #if vis.IsShowing():
                    vis.Show()
            except KeyError:
                pass
            

    def Hide(self):
        """ Method invoked with the 'Hide All' button is clicked. """

        self.update_mol_list()
        # Loop across all molecules and hide the images
        for molc in self.molecule_list:
            t = id(molc)
            try:
                visl = self.vis_dict[t]
                for vis in visl:
                    #if vis.IsShowing():
                    vis.Hide()
            except KeyError:
                pass


    def Delete(self):
        """ Method invoked with the 'Destroy All' button is clicked.
        """

        if not self.query("Are you really sure you want to trash all those images?"):
            return
        
        self.update_mol_list()
        # Loop across all molecules and delete all the images
        for molc in self.molecule_list:
            t = id(molc)
            try:
                # Each molecule could have a number of images
                # so for each id cycle through the list of possible images
                visl = self.vis_dict[t]
                #print "visl is ",visl
                for vis in self.vis_list:
                    #print "deleting vis: ",vis
                    vis._delete()
                    self.vis_list.remove( vis )
                # Remove the object from the vis dict?
                del self.vis_dict[t]
                        
            except KeyError,e:
                pass
            
        self.graph.update()


class MoldenWfnVisualiser(OrbitalVisualiser,Visualiser):

    def __init__(self, root, graph, obj, **kw):
        Visualiser.__init__(self, root, graph, obj, **kw)
        self.field = Field()
        OrbitalVisualiser.__init__(self, root, graph, self.field, **kw)

        self.title = "MolDen Visualiser for " + obj.name
        #self.height = 0.05

        # MOLDEN control object
        from interfaces.molden import MoldenDriver
        self.driver=MoldenDriver(obj.filename)

        # default molden settings
        self.mo = 0
        self.npts = 21
        self.edge = 0.0
        #
        self.last_mo = -1
        self.last_edge = -1.0
        self.last_npts = -1

    def _make_dialog(self, **kw):

        f = self.dialog.topframe
        #
        #  Selection of which orbital
        #
        value = self.mo
        mini = 0
        maxi = 100
        # Will need a callback here to change the variable value
        if mini and maxi:
            v = {'validator' : 'integer' , 'min' : mini , 'max' : maxi}
        elif mini:
            v = {'validator' : 'integer' , 'min' : mini }
        elif maxi:
            v = {'validator' : 'integer' , 'max' : maxi }
        else:
            v = {'validator' : 'integer' }

        self.w_pickmo = Pmw.Counter(f,
            labelpos = 'w', label_text = "select MO (0=density): ",
            increment = 1,
            entryfield_entry_width = 6,
            entryfield_value = value,
            entryfield_validate = v)

        self.w_pickmo.pack(side='top')

        #
        #  Selection of point density
        #
        value = self.npts
        mini = 2
        maxi = 201
        # Will need a callback here to change the variable value
        if mini and maxi:
            v = {'validator' : 'integer' , 'min' : mini , 'max' : maxi}
        elif mini:
            v = {'validator' : 'integer' , 'min' : mini }
        elif maxi:
            v = {'validator' : 'integer' , 'max' : maxi }
        else:
            v = {'validator' : 'integer' }

        self.w_npts = Pmw.Counter(f,
            labelpos = 'w', label_text = "Grid points/edge",
            increment = 5,
            entryfield_entry_width = 6,
            entryfield_value = value,
            entryfield_validate = v)

        self.w_npts.pack(side='top')

        #
        #  Selection of edge length
        #
        self.w_edge = Pmw.Counter(f,
                                   labelpos = 'w', label_text = 'Edge (0.0=auto)',
                                   entryfield_value = self.edge,
                                   entryfield_entry_width = 6,
                                   increment=1.0,
                                   datatype = {'counter' : 'real' },
                                   entryfield_validate = { 'validator' : 'real' })

        self.w_edge.pack(side='top')

        OrbitalVisualiser._make_dialog(self, **kw)

    def compute_grid(self):
        """ Compute the data via a call to Molden """
        retcode=0
        if self.mo != self.last_mo or self.edge != self.last_edge or self.npts != self.last_npts:
            self.driver.ComputePlot((1,2,3),mo=self.mo,npts=self.npts,edge=self.edge)
            self.field = self.driver.field
            retcode=1
        self.last_mo = self.mo
        self.last_edge = self.edge
        self.last_npts = self.npts
        # for the rest of the construction, see graph-specific
        # code (VtkMoldenWfnVisualise._build)
        return retcode

    def read_widgets(self):
        self.mo = int(self.w_pickmo.get())
        self.npts = int(self.w_npts.get())
        self.edge = float(self.w_edge.get())
        OrbitalVisualiser.read_widgets(self)

if __name__ == "__main__":

    import sys
    from Tkinter import *
    from viewer.vtkgraph import *
    from interfaces.filepunch import *

    root=Tk()
    root.withdraw()
    vt = VtkGraph(root)
    #p = PunchReader()
    #p.scan("c:\ccp1gui\seq4.pun")
    #print p.objects
    #obj = p.objects[0]
#    obj = p.objects[2]
#    for o in p.objects:
#        o.name = o.title
#        vt.data_list.append(o)
    #vis = VtkColourSurfaceVisualiser(root,vt,obj1)
    #vis = VtkDensityVisualiser(root,vt,obj1)
    #vis = VtkVectorVisualiser(root,vt,obj)
    #vis2 = VtkMoldenWfnVisualiser(root,vt,"/home/psh/molden4.4_hvd/ex1/cyclopropaan.out")
    #vis = VtkTrajectoryVisualiser(root,vt,mol)
    #vis = VtkVibrationSetVisualiser(root,vt,obj1)

    obj=Dl_PolyHISTORYFile("c:\\Documents and Settings\ps96\My Documents\Edinburgh MSc 2007\HISTORY.short")
    vis = VtkTrajectoryVisualiser(root,vt,obj,type='DLPOLYHISTORY')
    print 'build'
    vis.Build()
    #vis2.Build()
    print 'open'
    vis.Open()
    #vis2.Open()
    print 'loop'
    vt.mainloop()
