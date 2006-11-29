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

# From Konrad Hinsens scientific python
from Scientific.Geometry.VectorModule import *

from SimpleDialog import SimpleDialog
from tkColorChooser import *
from tkFileDialog import *
from objects.field import Field
from objects.grideditor import GridEditorWidget
from viewer.debug import deb

VDW_RADII = 10
COV_RADII = 11


NULL  = 0
BUILT = 1

class ColourMapChooser:
    """Implements widgets to select a colourmap and optionally
    a vector field to colour by
    """
    def __init__(self, parent, key, graph=None,choose_field=0,low=-1,high=1):
        self.parent = parent
        self.key = key
        self.graph = graph
        self.low = low
        self.high = high
        self.choose_field = choose_field

    def widget(self):
        """ add a colourmap selector, includes
        colour map choice,
        Scalar field for colouring
        Mapping range
        """

        self.cmap_frame = Pmw.Group(self.parent, tag_text=self.key + "Colour Mapping")
        self.cmap_name_var = Tkinter.StringVar()

        t = ['Default']

        if self.graph:
            for c in self.graph.colourmaps:
                t.append(c.title)

        f1 = Tkinter.Frame(self.cmap_frame.interior())
        f2 = Tkinter.Frame(self.cmap_frame.interior())
        f1.pack(side='top')
        f2.pack(side='top')
        self.w_cmap_name_menu = Pmw.OptionMenu(f1,
                                               labelpos = 'w',
                                               label_text = 'Scheme :',
                                               menubutton_textvariable = self.cmap_name_var,
                                               items = t,
                                               menubutton_width = 10)

        self.w_cmap_name_menu.setvalue('Default')

        self.w_cmap_low = Pmw.Counter(f2,
                                   labelpos = 'w', label_text = 'Lo',
                                   entryfield_value = self.low,
                                   entryfield_entry_width = 5,
                                   increment=1.0,
                                   datatype = {'counter' : 'real' },
                                   entryfield_validate = { 'validator' : 'real' })

        self.w_cmap_high = Pmw.Counter(f2,
                                   labelpos = 'w', label_text = 'Hi',
                                   entryfield_value = self.high,
                                   entryfield_entry_width = 5,
                                   increment=1.0,
                                   datatype = {'counter' : 'real' },
                                   entryfield_validate = { 'validator' : 'real' })

        self.w_cmap_name_menu.pack(side='left')
        self.w_cmap_low.pack(side='left')
        self.w_cmap_high.pack(side='left')

        if self.choose_field:
            self.colour_field_var = Tkinter.StringVar()
            self.w_colour_field_obj = Pmw.OptionMenu(f1,
                                                     labelpos = 'w',
                                                     label_text = 'Colour by',
                                                     menubutton_textvariable = self.colour_field_var,
                                                     items = ['dum'],
                                                     menubutton_width = 10)
            self.w_colour_field_obj.pack(side='top')
            self.update_colour_field_obj()

        return self.cmap_frame

    def update_colour_field_obj(self):
        items = []
        print 'update_colour_field'
        items.append('None')
        for o in self.graph.data_list:
            print o
            t1 = string.split(str(o.__class__),'.')
            print t1
            myclass = t1[len(t1)-1]
            if myclass == 'Field':
                if o.ndd == 1:
                    items.append(o.name)

        self.w_colour_field_obj.setitems(items)
        self.w_colour_field_obj.setvalue('None')

    def read_widgets(self):

        colour_obj = None
        if self.choose_field:
            field_name = self.colour_field_var.get()
            if field_name == 'None':
                pass
            else:
                for o in self.graph.data_list:
                    t1 = string.split(str(o.__class__),'.')
                    myclass = t1[len(t1)-1]
                    if myclass == 'Field':
                        if o.ndd == 1:
                            if o.name == field_name:
                                colour_obj = o

        return ( colour_obj,
                 self.cmap_name_var.get(),
                 float(self.w_cmap_low.get()),
                 float(self.w_cmap_high.get()) )

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


    def Open(self):
        """ Open the widget for editing/actions """
        print 'Open'
        if not self.dialog:
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

            # build specific elements
            self.make_dialog()

        print 'reposition'
        self.reposition()
        print 'disable'
        self.disable_dialog()
        self.dialog.show()
        self.dialog.update()
        print 'disable'
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

        print 'reposition'
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
        print 'master geom',    msx,msy,mpx,mpy
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



class MoleculeVisualiser(Visualiser):

    def __init__(self, root, graph, obj, **kw):

        apply(Visualiser.__init__, (self, root, graph, obj), kw)

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
        self.label_scale = 0.2
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

        print 'Mol Title',self.title

    def make_dialog(self):

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
        self.label_rgb, self.label_colour = askcolor(initialcolor=self.label_colour)
        self.w_label_colour.configure(foreground = self.label_colour)

    def __choose_cyl_colour(self):
        self.cyl_rgb, self.cyl_colour = askcolor(initialcolor=self.cyl_colour)
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
        self.frame_delay = 20
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
        
    def make_dialog(self, **kw):
        print 'Dialog'
        apply(MoleculeVisualiser.make_dialog, (self,), kw)

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
                                   increment=10,
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

        apply(MoleculeVisualiser.read_widgets, (self, ) )

        if self.choose_mode:
            self.mode = self.w_mode.index(Pmw.SELECT)
            #print 'Mode',self.mode
            #self.mode =  int(self.w_mode.get())
        self.frames =  int(self.w_frames.get())
        self.scale  =  float(self.w_scale.get())
        self.frame_delay  =  int(self.w_delay.get())

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
        apply(Visualiser.hide, (self,), kw)


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
    def make_dialog(self, **kw):
        VibrationVisualiser.make_dialog(self, **kw)


class TrajectoryVisualiser(MoleculeVisualiser):
    """To update a single image with a sequence of sets coordinates
    without loading all the structures as molecule objects
    """
    def __init__(self, root, graph, obj, **kw):
        self.frame = 0
        self.molecule = obj
        
    def make_dialog(self, **kw):
        MoleculeVisualiser.make_dialog(self, **kw)

        self.ani_frame = Pmw.Group(self.dialog.topframe, tag_text="Play Trajectory")

        bar = Tkinter.Frame(self.ani_frame.interior(),relief=Tkinter.SUNKEN, borderwidth=2)
        bar.pack(side='bottom', fill=Tkinter.X)

        #b=Tkinter.Button(bar, text='Reset', command=self.reset)
        #b.pack(side='left')
        b=Tkinter.Button(bar, text='|<', command=self.rew)
        b.pack(side='left')
        b=Tkinter.Button(bar, text='<', command=self.bak)
        b.pack(side='left')
        b=Tkinter.Button(bar, text='Stop', command=self.stop)
        b.pack(side='left')
        b=Tkinter.Button(bar, text='Play', command=self.play)
        b.pack(side='left')
        b=Tkinter.Button(bar, text='>', command=self.fwd)
        b.pack(side='left')
        b=Tkinter.Button(bar, text='>|', command=self.end)
        b.pack(side='left')

        self.ani_frame.pack()

            
    def rew(self):
        """ Go to the first frame of the trajectory and display the image
        """
        self.frame_no = 0
        self.show_frame()
        
    def end(self):
        """ Go to the last frame of the animation and display the image.
        """
        self.frame_no = self.nframes
        self.show_frame()

    def bak(self):
        """ Step back a single frame in the animation
        """
        self.frame_no -= 1
        self.show_frame()

    def fwd(self):
        """ Step forward a single frame in the animation
        """
        self.frame_no += 1
        self.show_frame()
    
    def stop(self):
        """ Stop the animation
        """
        self.ani_stop = 1

    def play(self):
        """ Play through the sequence of images from self.frame_no to the end
        """
        # Need to initialise frame_no if the animation toolbar was
        # open when objects were read in

        self.ani_stop = 0
        while 1:
            print 'Trajectory Frame:',self.frame_no
            #self.interior().update()
            if self.ani_stop:
                return
            self.frame_no += 1
            self.show_frame()
            time.sleep(0.2)

    def show_frame(self):
        """Update the working molecule with 
        """
        # check if the user has changed the parameters
        self.read_widgets()

        if self.traj_type == STRUCTURE_SEQ:

            for i in range(len(self.molecule.atom)):
                frame = self.frames[self.frame_no]
                atom = frame.coords[i]
                a.coord[0] = atom[0]
                a.coord[1] = atom[1]
                a.coord[2] = atom[2]

        elif self.traj_type == MMTK:
            print "MMTK trajectory"

        # remake images
        self._delete()
        self._build()
        self._show()
        # update image
        self.graph.update()
        # schedule next frame
        #self.dialog.after(self.frame_delay, self.nextframe)

class OutlineVisualiser:
    """To add outline to the volume widgets"""

    def __init__(self):
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
        self.outline_rgb, self.outline_colour = askcolor(initialcolor=self.outline_colour)
        self.w_outline_colour.configure(foreground = self.outline_colour)

    def _outline_switch(self):
        self.show_outline = self.outline_var.get()


class IsoSurfaceVisualiser(Visualiser,OutlineVisualiser):
    """Base class for isosurfaces"""
    def __init__(self, root, graph, obj, **kw):
        apply(Visualiser.__init__, (self, root, graph, obj), kw)
        apply(OutlineVisualiser.__init__, (self,), kw)
        self.field=obj
        self.opacity = 1.0

class OrbitalVisualiser(IsoSurfaceVisualiser):

    def __init__(self, root, graph, obj, **kw):

        apply(IsoSurfaceVisualiser.__init__, (self, root, graph, obj), kw)
        #
        # Create the required controls (how many frames)
        #

        self.cmap_obj = None
        self.height = 0.05

        self.plus_colour   =  '#ff0000'
        self.minus_colour  =  '#0000ff'
        self.plus_rgb = [ 255, 0, 0]
        self.minus_rgb = [ 0, 0, 255]
        self.title='Orbital view: ' + self.field.title
        
    def make_dialog(self):

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

        self.cframe = Tkinter.Frame(f)

        self.w_colorlab = Tkinter.Label(self.cframe,text='Edit Colours:      ')

        self.w_pcolor = Tkinter.Button(self.cframe,
                               text = '+ve',
                               foreground = self.plus_colour,
                               command= self.__choose_plus_colour)

        self.w_mcolor = Tkinter.Button(self.cframe,
                               text = '-ve',
                               foreground = self.minus_colour,
                               command= self.__choose_minus_colour)

        self.w_colorlab.pack(side='left')
        self.w_pcolor.pack(side='left')
        self.w_mcolor.pack(side='left')

        self.cframe.pack(side='top',fill='x')
        self.w_height.pack(side='top')

        self.opacity_widget(frame=f)

        surface_group.pack(side='top',fill='x')

        self.add_outline_widget()
        
    def __choose_plus_colour(self):
        self.plus_rgb, self.plus_colour = askcolor(initialcolor=self.plus_colour)
        self.w_pcolor.configure(foreground = self.plus_colour)

    def __choose_minus_colour(self):
        self.minus_rgb, self.minus_colour = askcolor(initialcolor=self.minus_colour)
        self.w_mcolor.configure(foreground = self.minus_colour)

    def read_widgets(self):
        self.height =  float(self.w_height.get())
        self.opacity =  float(self.w_opacity.get())
        # convert color format
        r, g, b = self.dialog.winfo_rgb(self.plus_colour)
        self.plus_rgb = [r/256, g/256, b/256]
        r, g, b = self.dialog.winfo_rgb(self.minus_colour)
        self.minus_rgb = [r/256, g/256, b/256]


class DensityVisualiser(IsoSurfaceVisualiser):

    def __init__(self, root, graph, obj, **kw):

        apply(IsoSurfaceVisualiser.__init__, (self, root, graph, obj), kw)

        self.cmap_obj = None

        # Default settings
        self.height = 0.05

        self.plus_colour   =  '#00ff00'
        self.plus_rgb = [0, 255, 0]
        self.opacity = 1.0
        self.field = obj
        self.title = 'Density Isosurface: ' + self.field.title

    def make_dialog(self):

        surface_group  = Pmw.Group(self.dialog.topframe, tag_text="Surfaces")
        f = surface_group.interior()

        labs = []

        self.w_colour_lab = Pmw.LabeledWidget(f,labelpos='w',label_text='Colour')
        self.w_pcolor = Tkinter.Button(self.w_colour_lab.interior(),
                                       text = 'oOo',
                                       foreground = self.plus_colour,
                                       command= self.__choose_plus_colour)

        self.w_pcolor.pack(side='left')
        self.w_colour_lab.pack(side='top')

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

        labs.append(self.w_colour_lab)

        self.opacity_widget(frame=f)
        labs.append(self.w_opacity)

        surface_group.pack(side='top',fill='x')

        Pmw.alignlabels(labs)

        self.add_outline_widget()


    def __choose_plus_colour(self):
        self.plus_rgb, self.plus_colour = askcolor(initialcolor=self.plus_colour)
        self.w_pcolor.configure(foreground = self.plus_colour)

    def read_widgets(self):
        self.height =  float(self.w_height.get())
        # convert color format
        r, g, b = self.dialog.winfo_rgb(self.plus_colour)
        self.plus_rgb = [r/256, g/256, b/256]
        self.opacity =  float(self.w_opacity.get())

class VolumeVisualiser(Visualiser,OutlineVisualiser):

    def __init__(self, root, graph, obj, **kw):

        apply(Visualiser.__init__, (self, root, graph, obj), kw)
        apply(OutlineVisualiser.__init__, (self,), kw)        
        self.colour_obj = None

        # Default settings
        #self.height = 0.05
        #self.plus_colour   =  '#00ff00'
        self.plus_rgb = [0, 255, 0]
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

    def make_dialog(self):

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
        self.rgb[ix], self.colour[ix] = askcolor(initialcolor=self.colour[ix])
        self.w_color[ix].configure(foreground = self.colour[ix])

    def __choose_outline_colour(self):
        self.outline_rgb, self.outline_colour = askcolor(initialcolor=self.outline_colour)
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

        apply(VolumeVisualiser.__init__, (self, root, graph, obj), kw)
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

        apply(VolumeVisualiser.__init__, (self, root, graph, obj), kw)
        self.title = 'Density Orbital Visualisation: ' + self.field.title
        self.setvalues()

    def setvalues(self):
        self.tfv = [ -0.1, -0.05, 0.0, 0.05, 0.1 ]
        self.rgb = [ [ 0,0,255],[0,0,255],[255,255,255],[255,0,0],[255,0,0]]
        self.colour = ['#0000ff',  '#0000ff',  '#ffffff', '#ff0000', '#ff0000' ]
        self.opacity = [0.8, 0.4, 0.0, 0.4, 0.8 ]
        #self.sfac = 10.0

class ColourSurfaceVisualiser(IsoSurfaceVisualiser):

    def __init__(self, root, graph, obj, colour_obj=None, **kw):

        apply(IsoSurfaceVisualiser.__init__, (self, root, graph, obj), kw)
        # Default settings
        self.height = 0.05
        self.plus_colour   =  '#00ff00'
        self.plus_rgb = [0, 255, 0]

        self.opacity = 1.0

        self.field = obj
        self.cmap_obj = colour_obj
        self.cmap_obj = None
        self.cmap_low = -50
        self.cmap_high = 50
        self.title = 'Coloured Isosurface of ' + self.field.title

    def make_dialog(self):

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

        self.cframe = Tkinter.Frame(f)

        self.w_colorlab = Tkinter.Label(self.cframe,text='Edit Colours:    ')

        self.w_pcolor = Tkinter.Button(self.cframe,
                                       text = 'oOo',
                                       foreground = self.plus_colour,
                                       command= self.__choose_plus_colour)

        self.w_colorlab.pack(side='left')
        self.w_pcolor.pack(side='left')
        self.cframe.pack(side='top',fill='x')
        self.w_height.pack(side='top')

        self.opacity_widget(frame=f)

        surface_group.pack(side='top',fill='x')

        self.cmap_chooser = ColourMapChooser(self.dialog.topframe,"",
                                             self.graph,
                                             choose_field=1,
                                             low=self.cmap_low,
                                             high=self.cmap_high)

        self.cmap_chooser.widget().pack(side='top',fill='x')

        self.add_outline_widget()

        Pmw.alignlabels([ self.w_height, self.w_opacity ] )

    def __choose_plus_colour(self):
        self.plus_rgb, self.plus_colour = askcolor(initialcolor=self.plus_colour)
        self.w_pcolor.configure(foreground = self.plus_colour)

    def read_widgets(self):
        self.height =  float(self.w_height.get())

        # convert color format
        r, g, b = self.dialog.winfo_rgb(self.plus_colour)
        self.plus_rgb = [r/256, g/256, b/256]

        self.cmap_obj, self.cmap_name, \
                       self.cmap_low, self.cmap_high = \
                       self.cmap_chooser.read_widgets()

        self.read_opacity_widgets()
        
class GridVisualiser(Visualiser):
    def __init__(self, root, graph, obj, **kw):
        apply(Visualiser.__init__, (self, root, graph, obj), kw)
        self.field = obj


STREAM_LINES=1
STREAM_TUBES=2
STREAM_SURFACE=3
STREAM_FORWARD=11
STREAM_BACKWARD=12
STREAM_BOTH=13
VECTOR_SAMPLE_ALL = 10

class VectorVisualiser(Visualiser):
    """visualise a vector field
    Display a slice through a 3D dataset
    Relies on SliceVisualiser for most of the code, uses
    a GridEditor widget to position the slice
    """

    def __init__(self, root, graph, obj, colour_obj_choice=None, colour_obj_list=None, **kw):
        apply(Visualiser.__init__, (self, root, graph, obj), kw)
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
        self.cmap_name = 'Default'
        self.cmap_low = -1
        self.cmap_high = 1

        self.hedgehog_scale=1.0
        self.orientedglyph_scale=1.0
        self.streamline_propagation_time=5.0
        self.streamline_integration_step_length=0.2
        self.streamline_step_length=0.05
        self.streamline_display = STREAM_LINES
        self.streamline_integration_direction = STREAM_FORWARD

        self.show_hedgehog = 1
        self.show_orientedglyphs = 0
        self.show_streamlines = 0

        if self.regular3:
            self.sample_grid = self.cut_plane
        else:
            self.sample_grid = VECTOR_SAMPLE_ALL

        self.cmap_obj = None

    def make_dialog(self, **kw):

        print 'vectorvis.make_dialog'

        labels = []
        # selector for whether the 

        self.hedgehog_var = Tkinter.BooleanVar()
        self.hedgehog_var.set(self.show_hedgehog)

        if self.graph.check_capability('hedgehog'):

            self.hedgehog_group = Pmw.Group(
                self.dialog.topframe ,tag_text='Hedgehog')

            f = self.hedgehog_group.interior()

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
            labels.append(self.w_hedgehog_scale)            

            self.hedgehog_group.pack(side='top',fill='x')

        self.orientedglyphs_var = Tkinter.BooleanVar()
        self.orientedglyphs_var.set(self.show_orientedglyphs)

        if self.graph.check_capability('orientedglyphs'):

            self.orientedglyphs_group = Pmw.Group(
                self.dialog.topframe ,tag_text='Oriented Glyphs')
            f = self.orientedglyphs_group.interior()

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
            labels.append(self.w_orientedglyph_scale)

            self.orientedglyphs_group.pack(side='top',fill='x')

        self.streamlines_var = Tkinter.BooleanVar()
        self.streamlines_var.set(self.show_streamlines)

        if self.regular3:

            if self.graph.check_capability('streamlines'):

                self.streamlines_group = Pmw.Group(
                    self.dialog.topframe ,tag_text='Streamlines')
                f = self.streamlines_group.interior()
                f1 = Tkinter.Frame(f)
                f2 = Tkinter.Frame(f)
                f3 = Tkinter.Frame(f)

                self.w_streamlines_lab = Pmw.LabeledWidget(
                    f1,labelpos='w',label_text='Display')
                self.w_streamlines = Tkinter.Checkbutton(self.w_streamlines_lab.interior())
                self.w_streamlines.config(variable=self.streamlines_var)
                self.w_streamlines.config(command=lambda s=self: s.__read_buttons() )
                self.w_streamlines.pack(side='top')

                self.w_streamlines_lab.pack(side='left')

                self.w_streamline_propagation_time = Pmw.Counter(
                    f1,
                    labelpos = 'w', label_text = 'Propagation Time',
                    entryfield_value = self.streamline_propagation_time,
                    entryfield_entry_width = 5,
                    increment=0.1,
                    datatype = {'counter' : 'real' },
                    entryfield_validate = { 'validator' : 'real' })

                self.w_streamline_propagation_time.pack(side='left')
                labels.append(self.w_streamline_propagation_time)

                self.w_streamline_integration_step_length = Pmw.Counter(
                    f2,
                    labelpos = 'w', label_text = 'Integ Step Length',
                    entryfield_value = self.streamline_integration_step_length,
                    entryfield_entry_width = 5,
                    increment=0.1,
                    datatype = {'counter' : 'real' },
                    entryfield_validate = { 'validator' : 'real' })

                self.w_streamline_integration_step_length.pack(side='left')
                labels.append(self.w_streamline_integration_step_length)

                self.w_streamline_step_length = Pmw.Counter(
                    f2,
                    labelpos = 'w', label_text = 'Step Length',
                    entryfield_value = self.streamline_step_length,
                    entryfield_entry_width = 5,
                    increment=0.1,
                    datatype = {'counter' : 'real' },
                    entryfield_validate = { 'validator' : 'real' })

                self.w_streamline_step_length.pack(side='left')
                labels.append(self.w_streamline_step_length)

                self.streamline_display_mode_var = Tkinter.StringVar()
                self.w_streamline_display_mode = Pmw.OptionMenu(
                    f3,
                    labelpos = 'w',
                    label_text = 'Display:',
                    menubutton_textvariable = self.streamline_display_mode_var,
                    items = ['lines','tubes','surfaces'],
                    initialitem='lines',
                    menubutton_width = 8)

                self.w_streamline_display_mode.pack(side='left')
    #            labels.append(self.w_streamline_display_mode)

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
    #           labels.append(self.w_streamline_integration_direction)

                f1.pack(side='top')
                f2.pack(side='top')
                f3.pack(side='top')
                self.streamlines_group.pack(side='top',fill='x')
            
##            Pmw.alignlabels(labels)

        # Colourmaps
        self.cmap_chooser = ColourMapChooser(self.dialog.topframe,"",
                                             self.graph,
                                             choose_field=1,
                                             low=self.cmap_low,
                                             high=self.cmap_high)

        self.cmap_chooser.widget().pack(side='top',fill='x')

        self.sample_var = Tkinter.StringVar()

        if self.regular3:
            # Specification of the sampling grid

            self.sample_group = Pmw.Group(self.dialog.topframe ,tag_text='Sampling Grid')

            self.sample_var = Tkinter.StringVar()
            self.sample_grid_menu = Pmw.OptionMenu(self.sample_group.interior(),
                                                   labelpos = 'w',
                                                   label_text = 'Sample at:',
                                                   menubutton_textvariable = self.sample_var,
                                                   items = ['dum'],
                                                   menubutton_width = 10)

            self.sample_grid_menu.pack(side='top')
            self.update_sample_grid_choice()

            print ' creating grid editor'
            self.grid_editor = GridEditorWidget(self.sample_group.interior(), self.cut_plane, command = self.__reslice,close_ok=0)
            print ' packing grid editor'
            self.grid_editor.pack(side='top')
            self.sample_group.pack(side='top')
            print ' grid editor make_dialog done'
        else:
            self.sample_var.set('All Field Points')

    def enable_dialog(self):
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
        self.show_hedgehog = self.hedgehog_var.get()
        self.show_orientedglyphs = self.orientedglyphs_var.get()
        self.show_streamlines = self.streamlines_var.get()
        if self.is_showing:
            self._show()

    def read_widgets(self):

        ####apply(SliceVisualiser.read_widgets, (self,))

        self.hedgehog_scale = float(self.w_hedgehog_scale.get())
        self.orientedglyph_scale = float(self.w_orientedglyph_scale.get())

        if self.regular3:
            self.streamline_propagation_time=float(self.w_streamline_propagation_time.get())
            self.streamline_integration_step_length=float(self.w_streamline_integration_step_length.get())
            self.streamline_step_length=float(self.w_streamline_step_length.get())

        #print 'READW'
        self.cmap_obj, self.cmap_name, self.cmap_low, self.cmap_high = \
                        self.cmap_chooser.read_widgets()

#        self.read_opacity_widgets()

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

        if self.regular3:
            v = self.streamline_integration_direction_var.get()
            if v == 'forward':
                self.streamline_integration_direction = STREAM_FORWARD
            elif v == 'backward':
                self.streamline_integration_direction = STREAM_BACKWARD
            elif v == 'both directions':
                self.streamline_integration_direction = STREAM_BOTH

            v = self.streamline_display_mode_var.get()
            if v == 'lines':
                self.streamline_display = STREAM_LINES
            if v == 'tubes':
                self.streamline_display = STREAM_TUBES
            if v == 'surfaces':
                self.streamline_display = STREAM_SURFACE

        if self.grid_editor is not None:
            # transform the grid, but do not trigger the the build that
            # normally results
            self.grid_editor.transform(callback=0)

class SliceVisualiser(Visualiser):
    """Represent a regular 2D grid using contour and colourmap
    representations and an outline. Can optionally render to the 2D
    window for preparation of printed plots.
    """
    def __init__(self, root, graph, obj, colour_obj_choice=None, colour_obj_list=None, **kw):

        apply(Visualiser.__init__, (self, root, graph, obj), kw)

        # Default settings
        self.min = -50
        self.max =  50
        self.ncont = 21
        self.opacity = 1.0

        self.contour_cmap_name = 'Default'
        self.contour_cmap_low = -50
        self.contour_cmap_high = 50

        self.pcmap_cmap_name = 'Default'
        self.pcmap_cmap_low = -50
        self.pcmap_cmap_high = 50

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
        
    def make_dialog(self):

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

        self.contour_cmap_chooser = ColourMapChooser(self.dialog.topframe,
                                                     "Contour ", self.graph,
                                                     low=self.contour_cmap_low,
                                                     high=self.contour_cmap_high)

        self.contour_cmap_chooser.widget().pack(side='top',fill='x')

        self.pcmap_cmap_chooser = ColourMapChooser(self.dialog.topframe, "ColourMap ", self.graph,
                                                     low=self.pcmap_cmap_low,high=self.pcmap_cmap_high)
        self.pcmap_cmap_chooser.widget().pack(side='top',fill='x')
        
        self.w_min.pack(side='top')
        self.w_max.pack(side='top')
        self.w_ncont.pack(side='top')

    def __choose_outline_colour(self):
        self.outline_rgb, self.outline_colour = askcolor(initialcolor=self.outline_colour)
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
        self.contour_cmap_obj, self.contour_cmap_name, \
                               self.contour_cmap_low, self.contour_cmap_high = \
                               self.contour_cmap_chooser.read_widgets()
        self.pcmap_cmap_obj, self.pcmap_cmap_name, \
                             self.pcmap_cmap_low, self.pcmap_cmap_high = \
                             self.pcmap_cmap_chooser.read_widgets()

        self.read_opacity_widgets()

class CutSliceVisualiser(SliceVisualiser):
    """Display a slice through a 3D dataset
    Relies on SliceVisualiser for most of the code, uses
    a GridEditor widget to position the slice
    """
    def __init__(self, root, graph, obj, colour_obj_choice=None, colour_obj_list=None, **kw):
        apply(SliceVisualiser.__init__, (self, root, graph, obj), kw)
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

    def make_dialog(self, **kw):
        apply(SliceVisualiser.make_dialog, (self,), kw)
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
        apply(SliceVisualiser.read_widgets, (self,))
        if self.grid_editor is not None:
            # transform the grid, but do not trigger the the build that
            # normally results
            self.grid_editor.transform(callback=0)

class IrregularDataVisualiser(Visualiser):
    """Viewer for unstructured grid of data points
    currently only offers coloured dots.
    """
    def __init__(self, root, graph, obj, **kw):
        apply(Visualiser.__init__, (self, root, graph, obj), kw)
        self.field = obj

        # Seem to need this (no read_widgets before first build?)
        self.cmap_name = 'Default'
        self.cmap_low = -50
        self.cmap_high = 50
        self.point_size = graph.field_point_size
        self.opacity = 1.0
        self.title = "Grid View: " + obj.title

    def make_dialog(self):
        self.w_point_size = Pmw.Counter(
            self.dialog.topframe,
            labelpos = 'w', label_text = 'Point Size',
            entryfield_value = self.point_size,
            entryfield_entry_width = 5,
            increment=1,
            datatype = {'counter' : 'integer' },
            entryfield_validate = { 'validator' : 'integer' })
        self.w_point_size.pack(side='top')

        self.cmap_chooser = ColourMapChooser(self.dialog.topframe,"",
                                             self.graph,
                                             low=self.cmap_low,
                                             high=self.cmap_high)

        self.cmap_chooser.widget().pack(side='top',fill='x')
        self.opacity_widget()
        
    def read_widgets(self):
        self.point_size = int(self.w_point_size.get())

        self.cmap_obj, self.cmap_name, self.cmap_low, self.cmap_high = \
                        self.cmap_chooser.read_widgets()

        self.read_opacity_widgets()

        #self.cmap_low = float(self.w_cmap_low.get())
        #self.cmap_high = float(self.w_cmap_high.get())
        #self.opacity =  float(self.w_opacity.get())

class AllMoleculeVisualiser( MoleculeVisualiser ):

#    def __init__(self, root, graph, **kw):
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
        apply( Visualiser.__init__, ( self, root, graph, obj ), kw_dict )
        apply( MoleculeVisualiser.__init__, (self, root, graph, obj), kw_dict )


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
                print "visl is ",visl
                for vis in self.vis_list:
                    print "deleting vis: ",vis
                    vis._delete()
                    self.vis_list.remove( vis )
                # Remove the object from the vis dict?
                del self.vis_dict[t]
                        
            except KeyError,e:
                pass
            
        self.graph.update()


class MoldenWfnVisualiser(OrbitalVisualiser,Visualiser):

    def __init__(self, root, graph, obj, **kw):
        apply(Visualiser.__init__, (self, root, graph, obj), kw)
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

    def make_dialog(self, **kw):

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

        apply(OrbitalVisualiser.make_dialog, (self, ), kw)

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
    p = PunchReader()
    p.scan("c:\ccp1gui\ccp1gui\untitled.pun")
    print p.objects
    mol = p.objects[0]
    obj1 = p.objects[1]

#    obj = p.objects[2]
#    for o in p.objects:
#        o.name = o.title
#        vt.data_list.append(o)
    #vis = VtkColourSurfaceVisualiser(root,vt,obj1)
    #vis = VtkDensityVisualiser(root,vt,obj1)
    #vis = VtkVectorVisualiser(root,vt,obj)
    #vis2 = VtkMoldenWfnVisualiser(root,vt,"/home/psh/molden4.4_hvd/ex1/cyclopropaan.out")
    #vis = VtkTrajectoryVisualiser(root,vt,mol)
    vis = VtkVibrationSetVisualiser(root,vt,obj1)
    print 'build'
    vis.Build()
    #vis2.Build()
    print 'open'
    vis.Open()
    #vis2.Open()
    print 'loop'
    vt.mainloop()
