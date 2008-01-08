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
"""Molecular graphics code based on VTK

The viewer framework that this runs in is provided by
a parent class TkMolView.

"""
import re

from chempy.cpv import *

from objects.periodic import colours,rcov,rvdw,rgb_min,rgb_max

from viewer.vtkTkRenderWidgetP import *

from viewer.main import *
from viewer.debug import deb,trb

from generic.graph import Graph
from generic.colourmap import ColourMap
from generic.visualiser import *

mol_select_key=1

# From Konrad Hinsens scientific python
from Scientific.Geometry.VectorModule import *

def truncate_vec(tup,lim):
    len = tup[0]*tup[0] + tup[1]*tup[1] + tup[2]*tup[2]
    if len > lim*lim:
        fac = lim/sqrt(len)
        tup[0] = tup[0] * fac
        tup[1] = tup[1] * fac
        tup[2] = tup[2] *fac
    return tup

class VtkGraph(TkMolView,Graph):

    def __init__(self, parent, title=''):

        Graph.__init__(self)

        self.vtkVersion = vtkVersion.GetVTKVersion()

        self.render_in_tk = 1

        # Set defaults for any attributes properties that may be 
        # superceded by values from ccp1guirc
        self.pick_tolerance = 0.01
        self.near = None
        self.far = None        
        
        # flags controlling how to draw molecules
        # sphere/line/stick type 1 will also work but is more expensive for
        # large molecules
        # At present a bit more work is needed to get option 1 working.
        self.sphere_type = 2
        self.line_type = 2
        self.label_type = 0
        self.stick_type = 2
        self.show_selection_by_dots = 1
        self.show_selection_by_colour = 1
        # Set stereo visualiser options.
        self.stereo = None

        # Define viewer capabilities and visualiser classes
        self.molecule_visualiser =  VtkMoleculeVisualiser
        self.trajectory_visualiser =  VtkTrajectoryVisualiser
        self.orbital_visualiser =  VtkOrbitalVisualiser
        self.density_visualiser =  VtkDensityVisualiser
        self.volume_density_visualiser =  VtkVolumeDensityVisualiser
        self.volume_orbital_visualiser =  VtkVolumeOrbitalVisualiser
        self.grid_visualiser =  VtkGridVisualiser
        self.colour_surface_visualiser =  VtkColourSurfaceVisualiser
        self.slice_visualiser =  VtkSliceVisualiser
        self.cut_slice_visualiser =  VtkCutSliceVisualiser
        self.vibration_visualiser = VtkVibrationVisualiser
        self.vibration_set_visualiser = VtkVibrationSetVisualiser
        self.vector_visualiser = VtkVectorVisualiser
        self.wavefunction_visualiser = VtkMoldenWfnVisualiser
        self.colourmap_func = VtkColourMap
        # experimental
        self.irregular_data_visualiser =  VtkIrVis

        self.capabilities['wire']=1
        self.capabilities['sticks']=1
        self.capabilities['spheres']=1
        self.capabilities['labels']=1
        self.capabilities['contacts']=1
        self.capabilities['hedgehog']=1
        self.capabilities['orientedglyphs']=1
        self.capabilities['streamlines']=1
        self.capabilities['streamarrows']=1
        self.capabilities['colourmap_actor']=1
        
        # We can only have (currently 2) of these as otherwise
        # there is nowhere to put them so the graph must keep
        # track of them
        self.colourmap_actors = [None,None] # len 2 list for l-r

        # Initialise Tk viewer window and menus etc
        # This will source the users ccp1guirc, maybe overwriting
        # settings made in the section above
        TkMolView.__init__(self, parent) 

        global sel
        sel = self.sel()
        #
        #sel.call_on_add(self.sel_show)
        sel.call_on_add(self.sel_upd)
        sel.call_on_rem(self.sel_upd)
        if self.show_selection_by_colour:
            sel.call_on_rem(self.sel_remove)
                
        self.title('CCP1 GUI'+25*' '+title)
        self.iconname('CCP1 GUI ')

        if self.render_in_tk == 1:
            # create vtkTkRenderWidget
            self.pane = vtkTkRenderWidget(self.interior(), stereo=self.stereo)
            renwin = self.pane.GetRenderWindow()
            self._set_stereo( renwin ) # See if we are using stereo
            self.ren = vtkRenderer()
            renwin.AddRenderer(self.ren)
            renwin.SetDesiredUpdateRate(0.2)
            
            self.pane.firstrenderer()
            self.pane.SetCamera(0.,0.,15.)
            self.pane.Reset()

        else:
            renwin = vtkRenderWindow()
            self.ren = vtkRenderer()
            renwin.AddRenderer(self.ren)
            # create an interactor
            self.iren = vtkRenderWindowInteractor()
            self.iren.SetRenderWindow(renwin)
            self.pane = vtkTkRenderWidget(self.interior())
            if self.stereo:
                renwin.SetStereoCapableWindow()
            self.renwin = renwin
            renwin.Render()


        # Bindings for the poor lonesome mac osx mouse button
        if sys.platform == 'darwin':
            self.pane.bind("<Shift-B1-Motion>",
                           lambda e,s=self.pane: s.Zoom(e.x,e.y))
            self.pane.bind("<Control-B1-Motion>",
                           lambda e,s=self.pane: s.Pan(e.x,e.y))
            

        self.pane.handlepick = self.mypick2
        self.picked_atomic_actor = 0
        self.picked_atom = None
        self.picked_mol = None
        # pack the pane into the tk root
        self.pane.pack(side = 'top', expand=1, fill = 'both',padx=3, pady=3)
        # maybe replace when animation is working
        #self.toolbar()


        # create vtkTkRenderWidget
        self.pane2d = vtkTkRenderWidget(self.window2d.interior())
        self.pane2d.pack(side = 'top', expand=1, fill = 'both',padx=3, pady=3)
        self.ren2d = vtkRenderer()
        renwin = self.pane2d.GetRenderWindow()
        renwin.AddRenderer(self.ren2d)
        renwin.SetDesiredUpdateRate(0.2)
        self.pane2d.firstrenderer()
        self.pane2d.SetCamera(0.,0.,2.)
        self.pane2d.Reset()

        # Apply default parameters to viewer
        self.set_bg_colour(self.bg_rgb)
        self.set_pick_tolerance()
        self.set_clipping_planes()

        # reposition window
        #m = re.match('(\d+)x(\d+)\+(\d+)\+(\d+)',self.master.geometry())
        # Above may not work as offset may contain a minus sign
        # See http://www.pythonware.com/library/tkinter/introduction/x9867-window-geometry-methods.htm
        m = re.match('(\d+)x(\d+)\+(-?\d+)\+(-?\d+)',self.master.geometry())
        sx,sy,px,py = int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4))
        #print sx,sy,px,py
        sx = 450
        sy = 500
        #self.master.geometry("%dx%d+%d+%d" % (sx,sy,20,20))
        self.restore_saved_jobs()
        
    def fit_to_window(self):
        self.pane.ResetToFit(0,0)

    def update(self):
        """Update the VTK images"""

        if self.render_in_tk == 1:
            self.pane.Render()
        else:
            self.renwin.Render()    
        self.pane2d.Render(trace=0)


    def save_image(self, renderWindow, file, format=None, quality=None  ):
        """
           Save an image from the renderwindow to file.
           Specify format as png to write as png else it defaults
           to jpeg with the optional quality argument specifying
           the quality ( default is 95 ).
        """
        self.master.update()
        w2i = vtkWindowToImageFilter()
        #w2i.SetInput(self.pane.GetRenderWindow())
        w2i.SetInput(renderWindow)

        if format == "png":
            writer = vtkPNGWriter()
            print "Saving png to file... %s" % file
        else:
            writer = vtkJPEGWriter()
            print "Saving jpeg to file... %s" % file
            if ( quality ):
                try:
                    quality = int( quality )
                except:
                    print "Error! Quality is not a number"
                    return 1
                writer.SetQuality( quality )
                print 'Resolution of jpeg is %d' % quality
            
        writer.SetInput(w2i.GetOutput())
        writer.SetFileName(file)
        writer.Write()

#    def save_image2d(self,file):
#        self.master.update()
#        w2i = vtkWindowToImageFilter()
#        w2i.SetInput(self.pane2d.GetRenderWindow())
#        j = vtkJPEGWriter()
#        j.SetInput(w2i.GetOutput())
#        j.SetFileName(file)
#        j.Write()

    def sel_show(self,mol,atoms):
        if self.debug:
            print 'graph.sel_show # atoms=',len(atoms)
        t = id(mol)
        try:
            visl = self.vis_dict[t]
            for vis in visl:
                if self.debug:
                    print 'vis call'
                vis.sel_show(mol)
        except KeyError:
            pass

    def sel_upd(self,mol,atoms):
        if self.debug:
            print 'graph.sel_upd # atoms=',len(atoms)
        t = id(mol)
        try:
            visl = self.vis_dict[t]
            for vis in visl:
                if self.debug:
                    print 'vis call'
                vis.sel_upd(mol)
        except KeyError:
            pass

    def sel_remove(self,mol,atoms):
        if self.debug:
            print 'graph.sel_remove # atoms=', len(atoms)
        t = id(mol)
        try:
            visl = self.vis_dict[t]
            for vis in visl:
                if self.debug:
                    print 'vis call'
                vis.sel_remove(atoms)
        except KeyError:
            pass

    def mypick(self,obj,atom,x,y):
        """Handle atomic pick
        Bound using AddObserver to the atom representation actors
        """
        if self.debug:
            deb('mypick called atom='+str(atom.get_index()))
        self.picked_mol = obj
        self.picked_atom = atom
        self.picked_atomic_actor = 1

    def mypick1(self,mol,obj,event):
        """Handle Wireframe pick
        Bound using AddObserver to the wireframe
        """
        # This is called from the event callback, and provides the molecule ID
        self.picked_mol = mol
        if self.debug:
            deb('mypick1 done')

    def mypick2(self,but):
        """Handle a pick event"""
        if self.debug:
            trb()
            deb('mypick2 entered, self.picked_atomic_actor =' + str(self.picked_atomic_actor))
            deb('                 self.picked_mol =' + str(self.picked_mol))

        global sel

        if not self.picked_mol:
            # we didn't hit anything, clear selection
            if but == 1:
                sel.clear()
                for d in self.data_list:
                    t = id(d)
                    try:
                        zme = self.zme_dict[t]
                        try:
                            zme.update_selection_from_graph()
                        except:
                            print 'mypick2 update zme sel failed'
                            
                    except KeyError:
                        pass
            return

        #print self.graph.pane.GetPicker()
        # This is called after the pick returns

        if self.picked_atomic_actor:
            # we hit a sphere label etc
            self.picked_atomic_actor = 0
            atom = self.picked_atom
        else:
            i = self.pane.GetPicker().GetPointId()
            atom = self.picked_mol.atom[i]

        print 'Picked atom',atom.get_index()+ 1,'in ',self.picked_mol.title
        if but == 1:
            sel.toggle(self.picked_mol,[atom])
            t = id(self.picked_mol)
            try:
                zme = self.zme_dict[t]
                try:
                    zme.update_selection_from_graph()
                except:
                    print 'mypick2 update zme sel failed'
            except KeyError:
                if self.debug:
                    print 'didnt find zme to upd'

            self.measure_selection()
                
        elif but == 3:
            self.atom_info(self.picked_mol, atom.get_index())
                          
        self.picked_mol = None
        self.picked_atom = None
	#print 'mypick2 done'
                           
    def update_zme_sel(self):
        zme_keys = self.zme_dict.keys()
        for t in zme_keys:
            zme = self.zme_dict[t]
            zme.update_selection_from_graph()

    def set_origin(self,point):
        """Set the rotation origin"""
        self.pane.SetOrigin(point[0],point[1],point[2])

    def set_bg_colour(self,col):
        """Set a new background colour"""
        r,g,b = col
        self.ren.SetBackground(float(r)/255.,float(g)/255.,float(b)/255.);

    def set_pick_tolerance(self):
        if self.debug:
            deb('set_pick_tolerance'+str(self.pick_tolerance))
        self.pane._Picker.SetTolerance(self.pick_tolerance)

    def set_clipping_planes(self):
        if self.debug:
            deb('set_clipping_planes'+str(self.near)+' '+str(self.far))
        self.pane.SetNearClippingPlane(self.near)
        self.pane.SetFarClippingPlane(self.far)

    def get_cmap_lut(self,name):
        #print 'Colourmap name =',name
        if name != 'Default':
            for c in self.colourmaps:
                if name == c.title:
                    return c.lut
            #print 'Colourmap name not found',name
        return None

    def _set_stereo( self, RenderWidget ):
        """ Set the stereo options for the widget
            We also activate stero here for the time being.
        """
        print "Setting Stereo type..."
        
        # StereoCapableOn is done already in vtkTkRenderWidget by specifying stereo
        #RenderWidget.StereoCapableWindowOn()

        if not self.stereo:
            return
        elif self.stereo == 'CrystalEyes':
            print "Setting Stereo to crystal eyes"
            RenderWidget.SetStereoTypeToCrystalEyes()
        elif self.stereo == 'RedBlue':
            print "Setting Stereo to RedBlue"
            RenderWidget.SetStereoTypeToRedBlue()
        else:
            print "Unknown stereo type: %s" % self.stereo
            print "Setting to RedBlue as default.."
            RenderWidget.SetStereoTypeToRedBlue()
            
        # Below activates stereo, but this should be set through a button
        # in the future
        RenderWidget.StereoRenderOn()
        
class VtkVis:

    """Base class to implement some methods that are common to
    the VTK visualisers
    """
    
    def _hide(self):
        if self.debug:
            deb('VtkVis._hide')
        for a in self.alist:
            try:
                if self.debug:
                    deb('VtkVis._hide removing actor...')
                self.graph.ren.RemoveActor(a)
                if self.debug:
                    deb('VtkVis._hide .. done')
            except:
                if self.debug:
                    deb('VtkVis._hide .. not done')
        for a in self.alist2d:
            try:
                if self.debug:
                    deb('VtkVis._hide removing 2D actor...')
                self.graph.ren2d.RemoveActor(a)
                if self.debug:
                    deb('VtkVis._hide .. done')
            except:
                if self.debug:
                    deb('VtkVis._hide .. not done')

    def _show(self):
        if self.debug:
            deb('VtkVis._show, calling hide first')
        self._hide()
        for a in self.alist:
            if self.debug:
                deb('VtkVis._show, adding actor')
            self.graph.ren.AddActor(a)
        for a in self.alist2d:
            if self.debug:
                deb('VtkVis._show, adding 2D actor')
            self.graph.ren2d.AddActor(a)
 
    def _delete(self):
        if self.debug:
            deb('VtkVis._delete')
        self._hide()
        self.alist = []
        self.alist2d = []


class VtkMoleculeVisualiser(MoleculeVisualiser):

    """Represent a molecule using Vtk

    see visualiser.py for the base class which defines the Tk widgets
    used for the user interactions.
    """

    def __init__(self, root, graph, obj, **kw):

        apply(MoleculeVisualiser.__init__, (self,root,graph,obj), kw)
        
        self.wire_actors = []
        self.sphere_actors = []
        self.stick_actors = []
        self.label_actors = []
        self.selection_actors = []
        self.contact_actors = []

        self.wire_visible = 0
        self.spheres_visible = 0
        self.sticks_visible = 0
        self.labels_visible = 0
        self.selection_visible = 0
        self.contacts_visible = 0
        
        self.debug = 0
        self.debug_selection = 0
        self.selection_key = None

        # dictionary to locate which actor highlights which atom
        self.atom_to_selection_actor = {}

    def draw_by_selection(self):
        if not self.selection_key:
            global mol_select_key
            mol_select_key = mol_select_key +1
            self.selection_key  = mol_select_key

        for atom in self.molecule.atom:
            try:
                ttt = atom.visible
            except AttributeError:
                atom.visible = {}
            atom.visible[self.selection_key]=0
            
        s = sel.get_by_mol(self.molecule)
        for atom in s:
            atom.visible[self.selection_key]=1
        self.Build()

    def draw_all(self):
        self.selection_key  = None
        self.Build()

    def _build(self,selected=None,object=None):
        """Create the molecular images"""
        if object:
            if self.debug:
                print 'mol build_ new obj'
            self.molecule = object

        self.molecule.reindex()

        t = vtkLookupTable()
        t.SetNumberOfColors(len(colours) + 1)
        t.Build()
        ix = 0
        for i in range(len(colours)):
            r,g,b = colours[i]
            t.SetTableValue(ix,r,g,b,1)
            ix = ix + 1
        self.colour_table = t

        #for a in self.molecule.atom:
        #    a.conn = []
        #for b in self.molecule.bond:
        #    self.molecule.atom[b.index[0]].conn.append(self.molecule.atom[b.index[1]])
        #    self.molecule.atom[b.index[1]].conn.append(self.molecule.atom[b.index[0]])

        if self.debug:
            self.molecule.list()

        # ---- Spheres ---------
        # 0  spheres with their own actors
        # 1  appendPolyData
        # 2  use glyph method (needs linetype=2)
        self.sphere_type = self.graph.sphere_type

        # ---- Lines ------
        # 0 individual linesource 
        # 1 linesources appended to a single actor
        # 2 celldata array
        self.line_type = self.graph.line_type

        # ---- Labels --------
        # individual actors
        # 0 = 3D
        # 1 = 2D
        self.label_type = self.graph.label_type

        # ---- Sticks ----------
        # 0 = individual vtkCylinderSource
        self.stick_type = self.graph.stick_type

        # ---- Contacts ----------
        # 2 = celldata array
        self.contact_type = 2
        
        if self.debug:
            print 'making sphere list of ', len(self.molecule.atom),' atoms'

        if self.show_spheres:
            if self.sphere_type == 0:

                for a in self.molecule.atom:

                    if self.selection_key:
                        draw = a.visible[self.selection_key]
                    else:
                        draw = 1

                    if draw:

                        try:
                            z = a.get_number()
                            r,g,b = colours[z]
                        except Exception:
                            z = 0
                            r,g,b = (1.,1.,1.)

                        # create the sphere
                        s = vtkSphereSource()

                        s.SetThetaResolution(self.graph.mol_sphere_resolution)
                        s.SetPhiResolution(self.graph.mol_sphere_resolution)
                        
                        if self.sphere_table == COV_RADII:
                            fac = 0.529177 * rcov[z] * self.sphere_scale
                        else:
                            fac = rvdw[z] * self.sphere_scale

                        #fac = rcov[z] / 2.0
                        # to show cylinders....
                        #fac = fac / 3.0
                        s.SetRadius(fac)

                        # create the mapper
                        m = vtkPolyDataMapper()
                        m.SetInput(s.GetOutput())

                        # create the actor
                        act = vtkActor()
                        self.sphere_actors.append(act)
                        act.SetMapper(m)
                        act.GetProperty().SetColor(r,g,b)

                        act.GetProperty().SetDiffuse(self.graph.mol_sphere_diffuse)
                        act.GetProperty().SetAmbient(self.graph.mol_sphere_ambient)
                        act.GetProperty().SetSpecular(self.graph.mol_sphere_specular)
                        act.GetProperty().SetSpecularPower(self.graph.mol_sphere_specular_power)

                        x = a.coord[0]
                        y = a.coord[1]
                        zz = a.coord[2]

                        act.SetPosition(x,y,zz)
                        # this seems to work
                        act.AddObserver(
                            'PickEvent', \
                            lambda x,y,s=self,obj=self.molecule,atom=a : s.graph.mypick(obj,atom,x,y) )

            elif self.sphere_type == 1:

                app = vtkAppendPolyData()
                for a in self.molecule.atom:
                    try:
                        z = a.get_number()
                    except Exception:
                        z = 0
                    r,g,b = colours[z]

                    # create the sphere
                    s = vtkSphereSource()
 
                    s.SetThetaResolution(self.graph.mol_sphere_resolution)
                    s.SetPhiResolution(self.graph.mol_sphere_resolution)

                    fac = rcov[z] * self.sphere_scale
                    # to show cylinders....
                    # fac = fac / 3.0
                    s.SetRadius(fac)

                    x = a.coord[0]
                    y = a.coord[1]
                    zz = a.coord[2]
                    s.SetCenter([x,y,zz])

                    app.AddInput(s.GetOutput())

                # create the mapper
                m = vtkPolyDataMapper()
                m.SetInput(app.GetOutput())

                # create the actor
                act = vtkLODActor()
                self.sphere_actors.append(act)
                act.SetMapper(m)
                act.GetProperty().SetDiffuse(self.graph.mol_sphere_diffuse)
                act.GetProperty().SetAmbient(self.graph.mol_sphere_ambient)
                act.GetProperty().SetSpecular(self.graph.mol_sphere_specular)
                act.GetProperty().SetSpecularPower(self.graph.mol_sphere_specular_power)


        # LABELS
        if self.show_labels:            
            for a in self.molecule.atom:
                if self.selection_key:
                    draw = a.visible[self.selection_key]
                else:
                    draw = 1
                if draw:
                    # Try and work out the label
                    try:
                        if self.label_with == 'symbol':
                            txt = a.symbol
                        elif self.label_with == 'name':
                            txt = a.name

                        elif self.label_with == 'mulliken charge':
                            val = self.molecule.get_atom_charge(a.get_index(),'Mulliken')
                            if val:
                                txt = "%f" % (val,)
                                while txt[-1:] == '0':
                                    txt = txt[:-1]
                            else:
                                txt = '---'

                        elif self.label_with == 'lowdin charge':
                            val = self.molecule.get_atom_charge(a.get_index(),'Lowdin')
                            if val:
                                txt = "%f" % (val,)
                                while txt[-1:] == '0':
                                    txt = txt[:-1]
                            else:
                                txt = '---'

                        elif self.label_with == 'potential derived charge':
                            val = self.molecule.get_atom_charge(a.get_index(),'PDC')
                            if val:
                                txt = "%f" % (val,)
                                while txt[-1:] == '0':
                                    txt = txt[:-1]
                            else:
                                txt = '---'

                        elif self.label_with == 'charge':
                            txt = "%f" % (a.partial_charge,)
                            while txt[-1:] == '0':
                                txt = txt[:-1]
                        elif self.label_with == 'atom no.':
                            txt = "%d" % (a.get_index()+1,)
                        else:
                            txt = a.name + '(' + str(a.get_index() + 1) + ')'
                    except AttributeError:
                        txt = '--'
                        
                    # Now got the label as txt
                    if self.label_type == 0:
                        # 3D Actors
                        s = vtkVectorText()
                        s.SetText(txt)

                        m = vtkPolyDataMapper()
                        m.SetInput(s.GetOutput())

                        act = vtkFollower()
                        self.label_actors.append(act)
                        act.SetMapper(m)

                        red = self.label_rgb[0] / 255.0
                        green = self.label_rgb[1] / 255.0
                        blue = self.label_rgb[2] / 255.0
                        act.GetProperty().SetColor(red,green,blue)
                        act.SetCamera(self.graph.pane._CurrentCamera)
                        act.SetScale(self.label_scale,self.label_scale,self.label_scale)
                        x = a.coord[0]
                        y = a.coord[1]
                        zz = a.coord[2]
                        act.PickableOn()
                        act.SetPosition(x,y,zz)
                        act.AddObserver(
                            'PickEvent', \
                            lambda x,y,s=self,obj=self.molecule,atom=a : s.graph.mypick(obj,atom,x,y) )
                    elif self.label_type == 1:
                        # 2D Actors
                        # create the mapper
                        m = vtkTextMapper()
                        m.SetInput(txt)
                        #print 'label scale',self.label_scale
                        #size = int(20.0*self.label_scale)
                        #m.SetFontSize(size)

                        # create the actor
                        #act = vtkScaledTextActor() # deprecated
                        act = vtkTextActor()
                        act.ScaledTextOn()
                        self.label_actors.append(act)
                        act.SetMapper(m)
                        act.GetPositionCoordinate().SetCoordinateSystemToWorld();

                        # Set the label size
                        h = self.label_scale/3
                        w = self.label_scale/3
                        act.SetHeight(h) #Defaults seems to be 0.5
                        act.SetWidth(w)#Defaults seems to be 0.5

                        # Try and centre the labels
                        #act.SetAlignmentPoint(2)
                        #x = a.coord[0] - w
                        #y = a.coord[1] - h
                        x = a.coord[0]
                        y = a.coord[1]
                        zz = a.coord[2]

                        act.GetPositionCoordinate().SetValue(x,y,zz);
                        #act.SetScale(self.label_scale,self.label_scale,self.label_scale)
                        act.PickableOff()
                        # act.AddObserver(
                        #    'PickEvent', \
                        #    lambda x,y,s=self,obj=self.molecule,atom=a : s.graph.mypick(obj,atom,x,y) )

                        red = self.label_rgb[0] / 255.0
                        green = self.label_rgb[1] / 255.0
                        blue = self.label_rgb[2] / 255.0
                        act.GetTextProperty().SetColor(red,green,blue)

        if self.show_wire:
            # Lines
            line_count = 0
            rad2deg = 180./Numeric.pi
            if self.line_type == 0:
                # 2 linesource objects per bond with their own actors
                orphans = []
                for a in self.molecule.atom:
                    try:
                        c = a.conn
                    except AttributeError:
                        c = []

                    if len(c) == 0:
                        orphans.append(a)

                    for t in c:

                        if self.selection_key:
                            draw = t.visible[self.selection_key] and a.visible[self.selection_key]
                        else:
                            draw = 1

                        if t.get_index() > a.get_index() and draw:

                            start = Vector(a.coord)
                            end = Vector(t.coord)
                            mid = 0.5*(start+end)

                            try:
                                z = a.get_number()
                            except Exception:
                                z = 0
                            r,g,b = colours[z]

                            s = vtkLineSource()
                            s.SetPoint1(start)
                            s.SetPoint2(mid)
                            m = vtkPolyDataMapper()

                            m.SetInput(s.GetOutput())
                            act = vtkActor()
                            act.SetMapper(m)
                            act.GetProperty().SetColor(r,g,b)
                            act.GetProperty().SetLineWidth(self.graph.mol_line_width)
                            act.AddObserver(
                                'PickEvent', \
                                lambda x,y,s=self,obj=self.molecule,atom=a : s.graph.mypick(obj,atom,x,y) )

                            self.wire_actors.append(act)

                            line_count = line_count + 1

                            try:
                                z = t.get_number()
                            except Exception:
                                z = 0
                            r,g,b = colours[z]

                            s = vtkLineSource()
                            s.SetPoint1(mid)
                            s.SetPoint2(end)
                            m = vtkPolyDataMapper()
                            m.SetInput(s.GetOutput())
                            act = vtkActor()
                            act.SetMapper(m)
                            act.GetProperty().SetColor(r,g,b)
                            act.GetProperty().SetLineWidth(self.graph.mol_line_width)
                            act.AddObserver(
                                'PickEvent', \
                                lambda x,y,s=self,obj=self.molecule,atom=t : s.graph.mypick(obj,atom,x,y) )
                            self.wire_actors.append(act)
                            line_count = line_count + 1

                if self.debug:
                    print 'orphans',len(orphans)

                for a in orphans:

                    if self.selection_key:
                        draw = a.visible[self.selection_key]
                    else:
                        draw = 1

                    if draw:

                        try:
                            z = a.get_number()
                        except Exception:
                            z = 0
                        r,g,b = colours[z]

                        s = vtkPointSource()
                        s.SetNumberOfPoints(1)
                        s.SetRadius(0.0)
                        s.SetCenter(a.coord)
                        m = vtkPolyDataMapper()
                        m.SetInput(s.GetOutput())
                        act = vtkActor()
                        act.SetMapper(m)
                        act.GetProperty().SetColor(r,g,b)
                        act.GetProperty().SetPointSize(self.graph.mol_point_size)
                        act.AddObserver(
                            'PickEvent', \
                            lambda x,y,s=self,obj=self.molecule,atom=a : s.graph.mypick(obj,atom,x,y) )
                        self.wire_actors.append(act)
                        line_count = line_count + 1


                for a in self.molecule.shell:

                    aa =  a.linked_core
                    if self.selection_key:
                        draw = aa.visible[self.selection_key]
                    else:
                        draw = 1

                    if draw:

                        r,g,b = (0.7,0.0,0.7)

                        s = vtkPointSource()
                        s.SetNumberOfPoints(1)
                        s.SetRadius(0.0)
                        s.SetCenter(a.coord)
                        m = vtkPolyDataMapper()
                        m.SetInput(s.GetOutput())
                        act = vtkActor()
                        act.SetMapper(m)
                        act.GetProperty().SetColor(r,g,b)
                        act.GetProperty().SetPointSize(self.graph.mol_point_size)
                        act.AddObserver(
                            'PickEvent', \
                            lambda x,y,s=self,obj=self.molecule,atom=aa : s.graph.mypick(obj,atom,x,y) )
                        self.wire_actors.append(act)
                        line_count = line_count + 1


            elif self.line_type == 1:
                # use linesource but append into a single polydata
                app = vtkAppendPolyData()
                for a in self.molecule.atom:
                    try:
                        c = a.conn
                    except AttributeError:
                        c = []
                    for t in c:
                        if t.get_index() > a.get_index():

                            start = Vector(a.coord)
                            end = Vector(t.coord)
                            mid = 0.5*(start+end)

                            try:
                                z = a.get_number()
                            except Exception:
                                z = 0
                            r,g,b = colours[z]

                            s = vtkLineSource()
                            s.SetPoint1(start)
                            s.SetPoint2(mid)

                            app.AddInput(s.GetOutput())

                            line_count = line_count + 1

                            try:
                                z = t.get_number() -1
                            except Exception:
                                z = 0
                            r,g,b = colours[z]

                            s = vtkLineSource()
                            s.SetPoint1(mid)
                            s.SetPoint2(end)

                            app.AddInput(s.GetOutput())

                            line_count = line_count + 1

                # create the mapper
                m = vtkPolyDataMapper()
                m.SetInput(app.GetOutput())

                # create the actor
                act = vtkActor()
                self.wire_actors.append(act)
                act.SetMapper(m)

                act.AddObserver(
                    'PickEvent', \
                    lambda x,y,s=self,obj=self.molecule,atom=a : s.graph.mypick(x,y) )


        if self.show_wire or (self.sphere_type == 2 and self.show_spheres ) :

            if self.line_type == 2:
                # construct points, cell data etc
                # includes spheres if sphere_type == 2
                # the best option for large molecules but so far colouring/scaling
                # balls is a problem

                np = 0
                mapper = []
                orphans = []
                for a in self.molecule.atom:
                    if self.selection_key:
                        draw = a.visible[self.selection_key]
                    else:
                        draw = 1
                    if draw:
                        mapper.append(np)
                        np = np + 1
                    else:
                        mapper.append(-1)
                for a in self.molecule.shell:
                    if self.selection_key:
                        aa =  a.linked_core
                        draw = aa.visible[self.selection_key]
                    else:
                        draw = 1
                    if draw:
                        np = np + 1

                #print 'points', np
                p = vtkPoints()

                zvals = vtkIntArray()
                zvals.SetName('z')
                zvals.SetNumberOfComponents(1)
                zvals.SetNumberOfTuples(np)

                hackrad = vtkFloatArray()
                hackrad.SetName('sizevecs')
                hackrad.SetNumberOfComponents(3)
                hackrad.SetNumberOfTuples(np)

                p.SetNumberOfPoints(np)
                bonds = []
                self.molecule.reindex()

                i=0
                np = 0
                for a in self.molecule.atom:
                    if self.selection_key:
                        draw = a.visible[self.selection_key]
                    else:
                        draw = 1
                    if draw:
                        p.SetPoint(np,a.coord[0], a.coord[1], a.coord[2])
                        try:
                            z = a.get_number()
                        except Exception:
                            z = 0
                        zvals.SetTuple1(np,z)

                        
                        if self.sphere_table == COV_RADII:
                            fac = 0.529177 * rcov[z] * self.sphere_scale
                        else:
                            fac = rvdw[z] * self.sphere_scale

                        # this 5 is empirical
			#   print 'setting size',z,rcov[z]
                        r = fac*5
                        hackrad.SetTuple3(np,r,r,r)
                        i=i+1

                        try:
                            c = a.conn
                        except AttributeError:
                            c = []

                        if len(c) == 0:
                            orphans.append(np)

                        for t in c:
                            if t.get_index() > a.get_index():
                                if self.selection_key:
                                    draw = t.visible[self.selection_key]
                                else:
                                    draw = 1
                                if draw:
                                    bonds.append([mapper[a.get_index()], mapper[t.get_index()]])
                        np = np + 1

                for a in self.molecule.shell:
                    if self.selection_key:
                        aa =  a.linked_core
                        draw = aa.visible[self.selection_key]
                    else:
                        draw = 1
                    if draw:
                        p.SetPoint(np,a.coord[0], a.coord[1], a.coord[2])
                        orphans.append(np)
                        zvals.SetTuple1(np,105)

                        # dummy radius for shells
                        fac = 0.529177 * 0.5 * self.sphere_scale
                        r = fac*5
                        hackrad.SetTuple3(np,r,r,r)

                        np = np + 1

                l = vtkCellArray()
                nb = len(bonds)
                l.Allocate(nb,nb)
                for b in bonds:
                    l.InsertNextCell(2)
                    l.InsertCellPoint(b[0])
                    l.InsertCellPoint(b[1])

                v = vtkCellArray()
                nv = len(orphans)
                v.Allocate(nv,nv)
                for o in orphans:
                    v.InsertNextCell(1)
                    v.InsertCellPoint(o)

                poly = vtkPolyData()
                poly.SetPoints(p)
                poly.SetLines(l)
                poly.SetVerts(v)

                # seems only one of these is needed, not sure which is best
                # SetScalars seems compatible with copying xyzmolreader code (at
                # least the colouring works for mode 2)
                #poly.GetPointData().AddArray(zvals)
                poly.GetPointData().SetScalars(zvals)
                poly.GetPointData().SetVectors(hackrad)

                self.zvals = zvals
                self.poly = poly

                m = vtkPolyDataMapper()
                self.map = m
                m.SetInput(poly)

                # the extra +1 is empirical so that
                # an integer index of 104 gets top colour in the list
                m.SetScalarRange(rgb_min, rgb_max+1)
                m.SetLookupTable(self.colour_table)
                m.SetScalarModeToUsePointFieldData()
                m.ColorByArrayComponent('z',0)

                act = vtkActor()
                act.SetMapper(m)
                act.GetProperty().SetLineWidth(self.graph.mol_line_width)
                act.GetProperty().SetPointSize(self.graph.mol_point_size)

                self.wire_actors.append(act)

                act.AddObserver(
                    'PickEvent', \
                    lambda x,y,s=self,obj=self.molecule : s.graph.mypick1(obj,x,y) )

                if self.sphere_type == 2:

                    s = vtkSphereSource()

                    s.SetThetaResolution(self.graph.mol_sphere_resolution)
                    s.SetPhiResolution(self.graph.mol_sphere_resolution)

                    g = vtkGlyph3D()
                    g.SetInput(poly)
                    g.SetSource(s.GetOutput())
                    g.SetScaleFactor(0.4)
                    #g.SetColorModeToColorByScalar()
                    #g.SetScaleModeToDataScalingOff()
                    #from xyz
                    g.SetColorMode(1)
                    g.SetScaleMode(2)

                    m = vtkPolyDataMapper()
                    m.SetInput(g.GetOutput())
                    m.SetLookupTable(self.colour_table)
                    m.SetScalarRange(rgb_min,rgb_max+1)
                    # from xyz
                    m.SetScalarVisibility(1)
                    m.UseLookupTableScalarRangeOff()
                    act = vtkActor()
                    act.SetMapper(m)
                    act.PickableOff()

                    act.GetProperty().SetDiffuse(self.graph.mol_sphere_diffuse)
                    act.GetProperty().SetAmbient(self.graph.mol_sphere_ambient)
                    act.GetProperty().SetSpecular(self.graph.mol_sphere_specular)
                    act.GetProperty().SetSpecularPower(self.graph.mol_sphere_specular_power)

                    tmp = 0.5
                    r = tmp
                    g = tmp
                    b = tmp
                    act.GetProperty().SetColor(r,g,b)
                    self.sphere_actors.append(act)

                #print 'made polydata with ', len(bonds), ' lines', len(orphans), 'vertices'

        if self.show_sticks:
            #print 'stick type', self.stick_type
            if self.stick_type == 0:
                # Cylinders
                line_count = 0
                rad2deg = 180./Numeric.pi
                for a in self.molecule.atom:
                    try:
                        c = a.conn
                    except AttributeError:
                        c = []

                    for t in c:

                        if self.selection_key:
                            draw = t.visible[self.selection_key] and a.visible[self.selection_key]
                        else:
                            draw = 1

                        if t.get_index() > a.get_index() and draw:
                            r1 = Vector(a.coord)
                            r2 = Vector(t.coord)
                            axis = r2-r1
                            center = 0.5*(r1+r2)
                            print 'center', center, t.get_index(), a.get_index()
                            print 'axis',axis

                            blength = axis.length()
                            # print 'blength ',blength
                            if blength > 0.0001:

                                axis = axis/blength
                                # Angles will be applied z, x, y in the cylinders local frame
                                # first move cylinder so that it overlap the target
                                # direction in the projection down Z

                                rot = Numeric.array([0.0,0.0,0.0])

                                # Assume we start with z 

                                if axis[1] == 0.0:
                                    if axis[0] < 0:
                                        angle = -90.0
                                    else:
                                        angle = 90.0                                        

                                else:
                                    ratio = axis[0] / axis[1]
                                    angle = Numeric.arctan(ratio)*rad2deg

                                print 'z angle',angle
                                # sign convention is empirical
                                rot[2] = -angle

                                # Get angle of target direction relative to yx plane
                                # and rotate about the local x axis
                                prj = sqrt(axis[0]*axis[0] + axis[1]*axis[1])
                                if prj ==  0.0:
                                    angle = 90.0
                                else:
                                    ratio = axis[2] / prj
                                    angle = Numeric.arctan(ratio)*rad2deg
                                    if axis[1] < 0:
                                        angle = -angle

                                if self.debug:
                                    print 'prj, axis[2], x angle',prj, axis[2], angle
                                rot[0] = angle

                                # we dont need a y rotation (cylinder axis)
                                rot[1] = 0.0

                                s = vtkCylinderSource()

                                # using radius values of less that 1 appear to
                                # produce very dark sided cylinders
                                # using 1.0 is OK, width is scaled using the SetScale method
                                # of the corresponding actor
                                s.SetRadius(1.0)
                                s.SetResolution(self.graph.mol_cylinder_resolution)
                                m = vtkPolyDataMapper()
                                m.SetInput(s.GetOutput())
                                act = vtkActor()
                                act.SetMapper(m)
                                red = self.cyl_rgb[0] / 255.0
                                green = self.cyl_rgb[1] / 255.0
                                blue = self.cyl_rgb[2] / 255.0
                                act.GetProperty().SetColor(red,green,blue)
                                act.GetProperty().SetDiffuse(self.graph.mol_cylinder_diffuse)
                                act.GetProperty().SetAmbient(self.graph.mol_cylinder_ambient)
                                act.GetProperty().SetSpecular(self.graph.mol_cylinder_specular)
                                act.GetProperty().SetSpecularPower(self.graph.mol_cylinder_specular_power)
                                act.SetPosition(center[0],center[1],center[2])
                                act.SetScale(self.cyl_width,blength,self.cyl_width)

                                act.SetOrientation(rot[0],rot[1],rot[2])

                                self.stick_actors.append(act)
                                line_count = line_count + 1

                if self.debug:
                    print 'made list of ', line_count, ' cylinders'


            elif self.stick_type == 2:

                Tube= vtkTubeFilter()
                ####Tube.SetInputConnection(readerGetOutputPort())
                Tube.SetInput(poly)
                Tube.SetNumberOfSides(16)
                Tube.SetCapping(0)

                fac = self.cyl_width
                Tube.SetRadius(fac)
                Tube.SetVaryRadius(0)
                Tube.SetRadiusFactor(10)

                m= vtkPolyDataMapper()
                ###m.SetInputConnection(TubeGetOutputPort())
                m.SetInput(Tube.GetOutput())

                # not sure what this does
                m.SetImmediateModeRendering(1)

                if self.colour_cyl:
                    m.UseLookupTableScalarRangeOff()
                    m.SetScalarModeToDefault()
                    m.SetLookupTable(self.colour_table)
                    m.SetScalarRange(rgb_min,rgb_max+1)
                    red = 1.0
                    green = 1.0
                    blue = 1.0
                else:
                    m.SetScalarVisibility(0)
                    red = self.cyl_rgb[0] / 255.0
                    green = self.cyl_rgb[1] / 255.0
                    blue = self.cyl_rgb[2] / 255.0

                act= vtkActor()
                act.SetMapper(m)
                act.GetProperty().SetRepresentationToSurface()
                act.GetProperty().SetInterpolationToGouraud()

                act.GetProperty().SetAmbient(self.graph.mol_cylinder_ambient)
                act.GetProperty().SetDiffuse(self.graph.mol_cylinder_diffuse)
                act.GetProperty().SetSpecular(self.graph.mol_cylinder_specular)
                act.GetProperty().SetSpecularPower(self.graph.mol_cylinder_specular_power)
                ##act.GetProperty().SetSpecularColor(1,1,1)
                act.GetProperty().SetColor(red,green,blue)
                act.PickableOff()

                self.stick_actors.append(act)

        if self.show_contacts:
            if self.contact_type == 2:

                self.molecule.find_contacts(self.graph.contact_scale,
                                            self.graph.contact_toler)

                p = vtkPoints()
                n = len(self.molecule.atom)
                p.SetNumberOfPoints(n)
                for a in self.molecule.atom:

                    if self.selection_key:
                        draw = a.visible[self.selection_key]
                    else:
                        draw = 1
                    if draw:
                        p.SetPoint(a.get_index(),a.coord[0], a.coord[1], a.coord[2])

                l = vtkCellArray()
                nb = len(self.molecule.contacts)
                l.Allocate(nb,nb)
                for c in self.molecule.contacts:
                    if self.debug:
                        print c.index
                    if c.index[0] > c.index[1]:
                        if self.selection_key:
                            draw = self.molecule.atom[c.index[0]].visible[self.selection_key] and  self.molecule.atom[c.index[1]].visible[self.selection_key] 
                        else:
                            draw = 1
                        if draw:
                            l.InsertNextCell(2)
                            l.InsertCellPoint(c.index[0])
                            l.InsertCellPoint(c.index[1])
                poly = vtkPolyData()
                poly.SetPoints(p)
                poly.SetLines(l)

                m = vtkPolyDataMapper()
                m.SetInput(poly)
                act = vtkActor()
                act.SetMapper(m)
                act.GetProperty().SetLineWidth(1)
                act.GetProperty().SetColor(1.0,1.0,1.0)
                self.contact_actors.append(act)
                print 'made contact polydata with ', len(self.molecule.contacts), ' lines'

        if self.show_wire and self.line_type == 2:
            # Apply selection highlighting by poking into zvals array
            #
            if self.graph.show_selection_by_colour:
                sels = sel.get_by_mol(self.molecule)
                for a in sels:
                    if a.get_index() >= 0:
                        self.zvals.SetTuple1(a.get_index(),106)
                self.zvals.Modified()

        # Selection highlighting
        # OLD CODE
##        sels = sel.get_by_mol(self.molecule)
##        if self.debug_selection:
##            print '_build selection objects',sels
##        for a in sels:
##            act = self.create_selection_actor(a)
##            ix = a.get_index()
##            if ix != -1:
##                self.atom_to_selection_actor[ix] = act
##            else:
##                print 'INDEX IS -1'

        if self.graph.show_selection_by_dots:
            for a in self.molecule.atom:
                if a.selected:
                    act = self.create_selection_actor(a)
                    self.selection_actors.append(act)
                    self.graph.ren.AddActor(act)
            
        if self.debug_selection:
            print 'after build # sel acts=', len(self.selection_actors)

        # these are all zero as we start with no actors in the scene
        self.wire_visible    = 0
        self.sticks_visible  = 0
        self.spheres_visible = 0
        self.labels_visible  = 0
        self.selection_visible  = 0
        self.contacts_visible  = 0

        # set current visibility
        self.status = BUILT

####    def sel_show(self,atoms):


    def sel_upd(self,mol):
        """Display the listed atoms as selected"""

        #Old code.. set the scalar value to 104 

        if self.graph.show_selection_by_colour:
            for a in mol.atom:
                if a.selected:
                    if self.debug_selection:
                        print 'select',a.get_index()+1
                    if a.get_index() >= 0:
                        self.zvals.SetTuple1(a.get_index(),106)
            self.zvals.Modified()

        #OLD CODE
##        for a in atoms:
##            if self.debug_selection:
##                print 'select',a.get_index()+1
##            try:
##                act = self.atom_to_selection_actor[a.get_index()]
##                if self.debug_selection:
##                    print 'selection actor already present ... rebuilding'
##                act = self.create_selection_actor(a,actor=act)
##            except KeyError:
##                act = self.create_selection_actor(a)
##                self.atom_to_selection_actor[a.get_index()] = act
##            self.graph.ren.AddActor(act)

        #
        # need to try and ensure no stray dots
        #
        for act in self.selection_actors:
            self.graph.ren.RemoveActor(act)
        self.selection_actors = []
        
        if self.graph.show_selection_by_dots:
            for atom in mol.atom:
                if atom.selected:
                    if self.debug_selection:
                        print 'showing selected atom',atom.get_index()
                    act = self.create_selection_actor(atom)
                    self.selection_actors.append(act)
                    self.graph.ren.AddActor(act)

    def create_selection_actor(self,a,actor=None):
        """ Create the little yellow dots to show that an atom has been
        selected.
        """
                
        # Add a 2D text element
        if not actor:
            m = vtkTextMapper()
            m.SetInput('.')
            
            try:
                prop=m.GetTextProperty()
            except AttributeError:
                prop=m
                    
            prop = m.GetTextProperty()
            prop.SetBold(1)
            prop.SetFontSize(70)
            prop.SetJustificationToLeft()
            prop.SetColor(1.0,1.0,0.0)
            act = vtkActor2D()
            act.SetMapper(m)
                
            act.PickableOff()
            act.GetPositionCoordinate().SetCoordinateSystemToWorld();
            # Perform display-coordinate transformation
            # works but needs refreshing as molecule moves
            #x,y = c.GetComputedDisplayValue(self.graph.ren)
            #c.SetCoordinateSystemToDisplay();
            #c.SetValue(x-8,y-8)
            self.selection_actors.append(act)

        else:
            act = actor

        x = a.coord[0]
        y = a.coord[1]
        zz = a.coord[2]
        #act.GetPositionCoordinate().SetValue(x,y,zz);
        c = act.GetPositionCoordinate()
        c.SetValue(x,y,zz);

        return act

    def sel_remove(self,atoms):
        """Remove the selection highlighting from an atom"""

        # Restore the atomic color 
        # Reset the scalar values
        for a in atoms:
            if self.debug_selection:
                print 'deselect',a.get_index()+1
            try:
                z = a.get_number()
            except Exception:
                z = 0
            if a.get_index() >= 0:
                self.zvals.SetTuple1(a.get_index(),z)
        self.zvals.Modified()

        # OLD CODE
##        for a in atoms:
##            if self.debug_selection:
##                print 'deselect',a.get_index()+1
##            ix = a.get_index()
##            if ix != -1:
##                act = self.atom_to_selection_actor[ix]
##                try:
##                    self.selection_actors.remove(act)
##                    del self.atom_to_selection_actor[ix]
##                    if self.debug_selection:
##                        print 'sel_remove: remove sel actor',id(act)
##                    self.graph.ren.RemoveActor(act)
##                except ValueError:
##                    print 'sel remove act: value error exception'

##            else:
##                print 'Internal error .. atom index is -1'
    
    def _delete(self):
        """Remove all vtk components of the image"""

        if self.debug:
            print '_delete'
        
        for a in self.sphere_actors:
            self.graph.ren.RemoveActor(a)
        for a in self.stick_actors:
            self.graph.ren.RemoveActor(a)
        for a in self.wire_actors:
            self.graph.ren.RemoveActor(a)
        for a in self.label_actors:
            self.graph.ren.RemoveActor(a)
        for a in self.selection_actors:
            #print 'rem selection actor',id(a)
            self.graph.ren.RemoveActor(a)
        for a in self.contact_actors:
            #print 'rem selection actor',id(a)
            self.graph.ren.RemoveActor(a)

        # Reset dictionary for selection actors
        self.atom_to_selection_actors = {}

        self.sphere_actors = []
        self.stick_actors = []
        self.wire_actors = []
        self.label_actors = []
        self.selection_actors = []
        self.contact_actors = []
    
    def _hide(self):
        """remove all actors from the renderer"""
        if self.debug:
            print 'hide_', self.show_wire, self.show_spheres, self.show_sticks, \
                  self.wire_visible, self.spheres_visible, self.sticks_visible, self.contacts_visible

        if self.show_spheres and self.spheres_visible:
            for a in self.sphere_actors:
                self.graph.ren.RemoveActor(a)
                #print 'rem sph'
            self.spheres_visible = 0

        if self.show_sticks and self.sticks_visible:
            for a in self.stick_actors:
                self.graph.ren.RemoveActor(a)
                #print 'rem stick'
            self.sticks_visible = 0

        if self.show_wire and self.wire_visible:
            for a in self.wire_actors:
                self.graph.ren.RemoveActor(a)
                #print 'rem line'
            self.wire_visible = 0

        if self.show_labels and self.labels_visible:
            for a in self.label_actors:
                self.graph.ren.RemoveActor(a)
                #print 'rem label'
            self.labels_visible = 0

        if self.show_contacts and self.contacts_visible:
            for a in self.contact_actors:
                self.graph.ren.RemoveActor(a)
                print 'rem contact'
            self.contacts_visible = 0

        if self.selection_visible:
            for a in self.selection_actors:
                self.graph.ren.RemoveActor(a)
            self.selection_visible=0;

    def _show(self):
        """Ensure that all requested images are showing"""

        if self.debug:
            print 'show_', self.show_wire, self.show_spheres, self.show_sticks, \
                  self.wire_visible, self.spheres_visible, self.sticks_visible

        if self.show_spheres:
            if not self.spheres_visible:
                for a in self.sphere_actors:
                    self.graph.ren.AddActor(a)
                    #print 'add sph'
                self.spheres_visible=1
        else:
            if self.spheres_visible:
                for a in self.sphere_actors:
                    self.graph.ren.RemoveActor(a)
                    #print 'rem sph'
                self.spheres_visible = 0

        if self.show_wire:
            if not self.wire_visible:
                for a in self.wire_actors:
                    #print 'add wire'
                    self.graph.ren.AddActor(a)
                self.wire_visible = 1
        else:
            if self.wire_visible:
                for a in self.wire_actors:
                    self.graph.ren.RemoveActor(a)
                    #print 'rem wire'
                self.wire_visible = 0

        if self.show_sticks:
            if not self.sticks_visible:
                for a in self.stick_actors:
                    #print 'add stick'
                    self.graph.ren.AddActor(a)
                self.sticks_visible = 1
        else:
            if self.sticks_visible:
                for a in self.stick_actors:
                    self.graph.ren.RemoveActor(a)
                    #print 'rem stick'
                self.sticks_visible = 0

        if self.show_labels:
            if not self.labels_visible:
                for a in self.label_actors:
                    #print 'add stick'
                    self.graph.ren.AddActor(a)
                self.labels_visible = 1
        else:
            if self.labels_visible:
                for a in self.label_actors:
                    self.graph.ren.RemoveActor(a)
                    #print 'rem stick'
                self.labels_visible = 0

        if self.show_contacts:
            if not self.contacts_visible:
                for a in self.contact_actors:
                    #print 'add contact'
                    self.graph.ren.AddActor(a)
                self.contacts_visible = 1
        else:
            if self.contacts_visible:
                for a in self.contact_actors:
                    #print 'rem contact'
                    self.graph.ren.RemoveActor(a)
                self.contacts_visible = 0
                
        # Always show selection
        if not self.selection_visible:
            for a in self.selection_actors:
                #print 'add sel actor (show)', id(a)
                self.graph.ren.AddActor(a)
            self.selection_visible = 1

class VtkCmapVis_:
    """Base class for widets that support a colourmap actor. This one
    has an underscore in the name because it is the base class that implements
    the functionality required in the cmap visualisers. VtkCmapVis inherits
    from this one but provides the _show/_hide/_remove support.
    However, we keep this class separate as we need the underlying methods in the
    vector visualiers, which implement their own _show etc.
    """

    # For keeping track of the scalarbar (for removing/refreshing)
    colourmap_actor=None
    
    # We need to determine the default lookuptable
    # so we get this from the mapper when we create the actor
    default_lut=None


    def __init__(self,graph):
        """Optional init method - just sets self.graph for those cases
        where multiple inheritance doesn't give us a graph"""
        print "VtkCmapVis_ __init__"
        self.graph=graph

    def add_colourmap_actor(self,colourer,title=None):
        """Add a colourmap widget
        Keywords:
        title: an optional title for the widget (else one will be
               constructed from the map object and colourmap name)
        """

        #print "add_colourmap_actor self.colourmap_actor is ",self.colourmap_actor

        # Just a quick hack - use a list of length 2 for left and right
        if (self.graph.colourmap_actors[0] and self.graph.colourmap_actors[1]):
            print "\n\nCANNOT ADD ANOTHER COLOURMAP_ACTOR-PLEASE REMOVE ONE FIRST!\n"
            return

        self.colourer = colourer

        # Get a title
        if not title:
            name = None
            cmap_obj = colourer.get_value('cmap_obj')
            cmap_name = colourer.get_value('cmap_name')
            if not cmap_name:
                cmap_name = 'Default'
            if cmap_obj:
                name = cmap_obj.get_name()
            if name:
                title = name + ':\n' + cmap_name
            else:
                title = cmap_name

        # Set up the scalarbar
        if not self.colourmap_actor:
            print "add colourmap widget create new actor"
            self.colourmap_actor = vtkScalarBarActor()
        else:
            print "add colourmap widget reusing actor"
            
            
        # Get a lookuptable - the default should have been
        # saved from the mapper
        lut = self.colourer.get_lut()
        if not lut:
            lut = self.get_default_lut()
        if not lut:
            raise AttributeError,"No lut!!!"
        
        self.colourmap_actor.SetLookupTable(lut)
        self.colourmap_actor.SetTitle(title)
        
        self.colourmap_actor.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()

        def add_left(cmap_actor,height=80,width=10,indent=0.01 ):
            """Position the bar to the left - height & width in viewport"""
            
            h=float(height/100.0)
            w=float(width/100.0)
            up = (1-h)/2
            cmap_actor.GetPositionCoordinate().SetValue(indent,up)
            cmap_actor.SetOrientationToVertical()
            cmap_actor.SetHeight(h)
            cmap_actor.SetWidth(w)
            return cmap_actor

        def add_right(cmap_actor,height=80,width=10,indent=0.01):
            """Position the bar to the right - height & width in viewport"""
            
            h=float(height/100.0)
            w=float(width/100.0)
            up = (1-h)/2
            right=1-(w+indent)
            cmap_actor.GetPositionCoordinate().SetValue(right,up)
            cmap_actor.SetOrientationToVertical()
            cmap_actor.SetHeight(h)
            cmap_actor.SetWidth(w)
            return cmap_actor


        # Add to the left or right of the window
        if not self.graph.colourmap_actors[0]:
            #print "setting left"
            self.graph.colourmap_actors[0]=self.colourmap_actor
            self.colourmap_actor = add_left(self.colourmap_actor)
        elif not self.graph.colourmap_actors[1]:
            #print "setting right"
            self.graph.colourmap_actors[1]=self.colourmap_actor
            self.colourmap_actor = add_right(self.colourmap_actor)
        else:
            print "colourmap_actor I SHOULD NOT BE HERE!"
           
        #print "Added colourmap actor",self.colourmap_actor
        #print "list now ",self.graph.colourmap_actors
        
        #Bottom
        #self.colourmap_actor.GetPositionCoordinate().SetValue(0.1,0.01)
        #self.colourmap_actor.SetOrientationToHorizontal()
        #self.colourmap_actor.SetHeight(0.17)
        #self.colourmap_actor.SetWidth(0.8)

        #Top
        #self.colourmap_actor.GetPositionCoordinate().SetValue(0.1,0.82)
        #self.colourmap_actor.SetOrientationToHorizontal()
        #self.colourmap_actor.SetHeight(0.17)
        #self.colourmap_actor.SetWidth(0.8)

        # Would be great if we could use this but as we
        # use vtkTkRenderWidget as our base widget there is no
        # interactor we can use for the widget. *#*#*!! Tkinter...
        # Create the scalarwidget
        #scalarWidget = vtkScalarBarWidget()
        #scalarWidget.SetScalarBarActor( colourmap_actor )
        #scalarWidget.EnabledOn()        
        #scalarWidget.AddObserver("RightButtonPressEvent",None)
        #scalarWidget.SetInteractor(self.graph.iren)
        
        #self.graph.ren.AddActor(self.colourmap_actor)

    def show_colourmap_actor(self):
        """Show the colourmap actor if we have one"""

        #print "show_colourmap_actor ",
        if (self.colourmap_actor and self.colourer.get_value(
            "show_colourmap_actor")):
            #print "got actor"
            # Need to set the range for the default lut
            if not self.colourer.get_lut():
                lut = self.get_default_lut()
                lut.SetTableRange( self.colourer.get_value("cmap_low"),
                                   self.colourer.get_value("cmap_high"))
                
            self.graph.ren.AddActor(self.colourmap_actor)
            
    def hide_colourmap_actor(self):
        """Hide the colourmap actor"""

        #print "hide_colourmap_actor ",
        if self.colourmap_actor:
            #print "got actor"
            self.graph.ren.RemoveActor(self.colourmap_actor)
            
    def delete_colourmap_actor(self):
        """Delete the colourmap_actor"""

        # Make sure we remove it from the renderer first
        self.hide_colourmap_actor()
        
        if self.colourmap_actor:
            # Remove this actor from the graph
            if self.graph.colourmap_actors[0] == self.colourmap_actor:
                self.graph.colourmap_actors[0]=None
            elif self.graph.colourmap_actors[1]==self.colourmap_actor: 
                self.graph.colourmap_actors[1]=None
            else:
                print "delete colourmap actor no self in list!"
            self.colourmap_actor=None

    def get_default_lut(self):
        """Return the default lookup table """
        if self.default_lut:
            return self.default_lut
        else:
            print "!!!!!!!!! get_default_lut no lookuptable!!!"

    def set_default_lut(self,lut):
        """Set the default lookup table """
        self.default_lut = lut

class VtkCmapVis(VtkCmapVis_,VtkVis):
    """Implement the show/hiding of the scalar bar with VtkVis"""

    def _hide(self):
        VtkVis._hide(self)
        #print "calling hide_colourmap_actor"
        self.hide_colourmap_actor()
        
    def _show(self):
        VtkVis._show(self)
        #print "calling show_colourmap_actor"

        # See if we are displaying a scalar bar to show the
        # colourmap we are using
        if ( self.colourer.get_value('show_colourmap_actor') and \
             self.colourer.cmap_by_object() ):
            self.add_colourmap_actor(self.colourer)
            #print "added colourmap_actor in _show"
        
        self.show_colourmap_actor()
        
    def _delete(self):
        VtkVis._delete(self)
        #print "calling delete_colourmap_actor"
        self.delete_colourmap_actor()
        
class VtkIsoSurf(VtkCmapVis):

    """A base class for the 3D surface visualisers, supporting
    conversion of field objects to vtk format and the drawing of
    isosurfaces and drawing a bounding box.

    """

    def __init__(self, **kw):
        self.alist = []
        self.alist2d = []
        self.convert_data()

    def convert_data(self):
        """ Set up vtk data structures depending on whether data strucutures
            held in python or vtk data structures.
        """
        if self.field.vtkdata:
            self.convert_data_vtk()
        else:
            self.convert_data_python()


    def convert_data_vtk(self):
        """ Use the vtkImageData directly - assumes axes are algined for the time being
        """
        self.data = self.field.vtkdata

    def convert_data_python(self):

        # Policy here should depend on whether data is axis aligned
        axis_aligned = 0

        if axis_aligned:
            #
            # Use structured points (alias vtkImageData) if data is 
            # on the grid assumed by vtk
            #
            self.data = vtkStructuredPoints()
            data = self.data
            npts = Vector(self.field.dim[0],self.field.dim[1],self.field.dim[2])

            xspacing = self.field.grid[0]
            yspacing = self.field.grid[1]
            zspacing = self.field.grid[2]

            data.SetDimensions(npts[0],npts[1],npts[2])
            data.SetOrigin(self.field.origin[0],self.field.origin[1],self.field.origin[2])
            data.SetSpacing(xspacing,yspacing,zspacing)

            bigsize = npts[0]*npts[1]*npts[2]

            data_array = vtkFloatArray()
            data_array.SetNumberOfValues(bigsize)

            # The mess with the offsets is to correct for the fact that, although
            # Jaguar creates the output in the zyx ordering, the vtk libraries
            # want it in the xyz ordering.
            offset=0
            for i in range(npts[0]):
                for j in range(npts[1]):
                    for k in range(npts[2]):
                        data_array.SetValue(offset,self.field.lvl[k,j,i])
                    offset = offset+1

            #print self.field.lvl
            #tmp = Numeric.reshape(Numeric.transpose(self.field.lvl,[2,1,0]),(-1,))
            #print tmp
            #tmp = self.field.lvl
            #tmp = Numeric.reshape(self.field.lvl,(-1,))
            #data_array.SetFloatArray(tmp,bigsize,1)

            data.GetPointData().SetScalars(data_array)

        #del data_array  # clean up some of the memory

        else:
            # General case:
            # use the Field get_grid method to generate an explicit
            # representation of the point array, render as vtkStructuredGrid
            #
            nx = self.field.dim[0]
            if len(self.field.dim) > 1:
                ny = self.field.dim[1]
            else:
                ny = 1

            ny = self.field.dim[1]
            if len(self.field.dim) > 2:
                nz = self.field.dim[2]
            else:
                nz = 1

            npts = Vector(nx,ny,nz)

            print 'dim',self.field.dim,'vec',npts

            self.data = vtkStructuredGrid()
            self.data.SetDimensions(npts[0],npts[1],npts[2])
            #
            # Pack the data into a float arrat
            #
            bigsize = npts[0]*npts[1]*npts[2]

            # Not clear if this test is right!!

            if self.field.data:
                data_array = vtkFloatArray()
                data_array.SetNumberOfValues(bigsize)
                offset = 0
                for k in range(npts[2]):
                    for j in range(npts[1]):
                        for i in range(npts[0]):
                            data_array.SetValue(offset,self.field.data[offset])
                            offset = offset+1

                print 'set scalars'
                self.data.GetPointData().SetScalars(data_array)

            bigsize = npts[0]*npts[1]*npts[2]
            points = vtkPoints()
            points.SetNumberOfPoints(bigsize)
            offset = 0
            print 'getting grid'
            grid = self.field.get_grid()
            print 'grid done'

            for k in range(npts[2]):
                for j in range(npts[1]):
                    for i in range(npts[0]):
                        points.SetPoint(offset,grid[offset])
                        offset = offset+1

            print 'setPoints'
            self.data.SetPoints(points)

    def add_outline(self):
        #jmht
        #outline = vtkStructuredGridOutlineFilter()
        # outline filter will work with both Structured Grids & vtkImageData
        outline = vtkOutlineFilter()
        outline.SetInput(self.data)
        outlineMapper = vtkPolyDataMapper()
        outlineMapper.SetInput(outline.GetOutput())
        outlineActor = vtkActor()

        red = self.outline_rgb[0] / 255.0
        green = self.outline_rgb[1] / 255.0
        blue = self.outline_rgb[2] / 255.0
        outlineActor.GetProperty().SetColor(red,green,blue)
        outlineActor.SetMapper(outlineMapper)
        self.alist.append(outlineActor)

    def add_surface(self, contour, rgb, opacity):
#    def add_surface(self, contour, opacity, rgb=None):

        #if not rgb:
        #    rgb = self.colourer.get_value("plus_rgb")
        r = float(rgb[0])/256
        g = float(rgb[1])/256
        b = float(rgb[2])/256

        if self.colourer.cmap_by_object():
            cmap_obj = self.colourer.get_value('cmap_obj')
            # There is an additional field to colour by
            data_array2 = vtkFloatArray()
            npts = Vector(cmap_obj.dim[0],cmap_obj.dim[1],cmap_obj.dim[2])
            bigsize = npts[0]*npts[1]*npts[2]
            data_array2.SetNumberOfValues(bigsize)
            offset=0
            for i in range(npts[0]):
                for j in range(npts[1]):
                    for k in range(npts[2]):
                        data_array2.SetValue(offset,cmap_obj.data[offset])
                        offset = offset+1
            data_array2.SetName("MapScalar");
            self.data.GetPointData().AddArray(data_array2)

        s = vtkContourFilter()
        s.SetInput(self.data)
        s.SetValue(0,contour)
        s.SetComputeNormals(1)

        n = vtkPolyDataNormals()
        n.SetInput(s.GetOutput())
        n.SetFeatureAngle(89)

        m = vtkPolyDataMapper()
        # Need to determine the default lut before it gets changed
        self.default_lut = m.GetLookupTable()
        m.SetInput(n.GetOutput())

        if self.colourer.cmap_by_object():
            m.ScalarVisibilityOn()
            m.ColorByArrayComponent("MapScalar",0);
            m.SetScalarModeToUsePointFieldData()
            lut = self.colourer.get_lut()
            if lut:
                m.SetLookupTable(lut)
            m.SetScalarRange(self.colourer.get_value('cmap_low'),
                             self.colourer.get_value('cmap_high'))
        else:
            m.ScalarVisibilityOff()

        act = vtkActor()
        act.SetMapper(m)
        if not self.colourer.cmap_by_object():
            act.GetProperty().SetColor(r,g,b)
        act.GetProperty().SetOpacity(opacity)
                    
        self.alist.append(act)


class VtkVolVis:
    """A base class for the 3D volume visualisers, supporting
    conversion of field objects to vtk format, the volume
    rendering and drawing of a bounding box.
    """
    
    def __init__(self, **kw):
        self.alist = []
        self.alist2d = []
        # need to convert every time as we are scaling
        # to fit into unsigned byte array
        if self.field.vtkdata:
            self.data = self.field.vtkdata
            #print "self.data is ",self.data
        else:
            self.convert_data()

    def convert_data(self):
        """
           Convert the data into a form suitable for VTK
        """

        if self.field.vtkdata:
            self.convert_data_vtk()
        else:
            self.convert_data_python()

    def convert_data_python(self):
        """
           Convert the data held in a Python field structure
        """

        field = self.field

        #
        # Use structured points (alias vtkImageData) if data is 
        # on the grid assumed by vtk
        #
        self.data = vtkStructuredPoints()
        data = self.data
        npts = Vector(field.dim[0],field.dim[1],field.dim[2])

        # jmht - noticed that cube reader didn't have a mapping
        # and so this failed
        if field.mapping:
            vx = field.mapping[0] - field.origin_corner
            vy = field.mapping[1] - field.origin_corner
            vz = field.mapping[2] - field.origin_corner

            if not field.axis_aligned():
                print "Field has non-aligned axes"

            #xspacing = vx*xxx / (npts[0] - 1)
            #yspacing = vy*yyy / (npts[1] - 1)
            #zspacing = vz*zzz / (npts[2] - 1)
            #xspacing = vx / (npts[0] - 1)
            #yspacing = vy / (npts[1] - 1)
            #zspacing = vz / (npts[2] - 1)
            xspacing = vx.length() / (npts[0] - 1)
            yspacing = vy.length() / (npts[1] - 1)
            zspacing = vz.length() / (npts[2] - 1)
        else:
            xspacing = field.axis[0].length() / (npts[0] - 1)
            yspacing = field.axis[1].length() / (npts[1] - 1)
            zspacing = field.axis[2].length() / (npts[2] - 1)


        data.SetDimensions(npts[0],npts[1],npts[2])
        
        #jmht
        if field.mapping:
            data.SetOrigin(field.origin_corner[0],field.origin_corner[1],field.origin_corner[2])
        else:
            data.SetOrigin(field.origin[0],field.origin[1],field.origin[2])

        data.SetSpacing(xspacing,yspacing,zspacing)

        bigsize = npts[0]*npts[1]*npts[2]

        data_array = vtkUnsignedShortArray()
        data_array.SetNumberOfValues(bigsize)

        #This now in a separate routine as also required by vtk
        self.volvis_set_mapping()

        ioff=0
        for i in range(npts[2]):
            for j in range(npts[1]):
                for k in range(npts[0]):
                    try:
                        value = self.offset + self.sfac*field.data[ioff]
                        if value < 0.0:
                            value = 0.0
                        if value > 32767.0:
                            value = 32767.0 
                        data_array.SetValue(ioff,int(value))
                    except OverflowError:
                        print 'overflow', self.offset + self.sfac*field.data[ioff]
                        data_array.SetValue(ioff,int(255.0))
                    ioff=ioff+1

        #print field.lvl
        #tmp = Numeric.reshape(Numeric.transpose(field.lvl,[2,1,0]),(-1,))
        #print tmp
        #tmp = field.lvl
        #tmp = Numeric.reshape(field.lvl,(-1,))
        #data_array.SetFloatArray(tmp,bigsize,1)

        data.GetPointData().SetScalars(data_array)

    def convert_data_vtk(self):
        """
           Convert the data held in a vtk field structure (floats) into a format suitable
           for rendering with the volume visualiser (unsigned short)
           
        """

        # Set self.sfac & self.offest for scaling
        self.volvis_set_mapping()
        
        # We need to cast the data to unsigned shorts for the volumeMapper, so we
        # are required to scale & shift the data, as we are converting from floats
        datacast = vtkImageShiftScale()
        datacast.SetInput(self.data)
        datacast.SetScale( self.sfac )
        datacast.SetShift( self.offset )
        datacast.SetOutputScalarTypeToUnsignedShort()
        self.data = datacast.GetOutput()
        
    def volvis_set_mapping(self):
        """
           Set the scaling factors for the volume visualiser
        """
        ltf = len(self.tfv)
        self.range = self.tfv[ltf-1] - self.tfv[0]
        self.sfac = 32768 / self.range
        self.offset = -self.tfv[0] * self.sfac

    def add_outline(self):

        outline=vtkOutlineFilter()
        outline.SetInput(self.data)
        outlineMapper=vtkPolyDataMapper()
        outlineMapper.SetInput(outline.GetOutput())
        outlineActor=vtkActor()
        red = self.outline_rgb[0] / 255.0
        green = self.outline_rgb[1] / 255.0
        blue = self.outline_rgb[2] / 255.0
        print 'outline colour',red,green,blue
        outlineActor.GetProperty().SetColor(red,green,blue)
        outlineActor.SetMapper(outlineMapper)
        self.alist.append(outlineActor)

    def mapvol(self):

        # Create transfer mapping scalar value to opacity

        opacityTransferFunction=vtkPiecewiseFunction()
        colorTransferFunction=vtkColorTransferFunction ()
        for i in range(5):
            opacityTransferFunction.AddPoint(self.offset + self.sfac*self.tfv[i],self.opacity[i])
            red,green,blue = self.rgb[i]
            red = red / 255.0
            green = green / 255.0
            blue = blue / 255.0
            colorTransferFunction.AddRGBPoint(self.offset + self.sfac*self.tfv[i], red, green, blue)
            print i,self.tfv[i],self.offset + self.sfac*self.tfv[i],self.opacity[i],'(',red,green,blue,')'

        # The property describes how the data will look
        volumeProperty=vtkVolumeProperty()
        volumeProperty.SetColor(colorTransferFunction)
        volumeProperty.SetScalarOpacity(opacityTransferFunction)

        if 0:
            # The mapper / ray cast function know how to render the data
            compositeFunction=vtkVolumeRayCastCompositeFunction()
            volumeMapper=vtkVolumeRayCastMapper()
            volumeMapper.SetVolumeRayCastFunction(compositeFunction)
        else:
            # The mapper knows how to render the data
            volumeMapper=vtkVolumeTextureMapper2D()

        volumeMapper.SetInput(self.data)

        # The volume holds the mapper and the property and
        # can be used to position/orient the volume
        volume=vtkVolume()
        volume.SetMapper(volumeMapper)
        volume.SetProperty(volumeProperty)
        self.alist.append(volume)

    def _build(self,object=None):
        self.convert_data()
        self.mapvol()
        if self.show_outline:
            self.add_outline()
        self.status = BUILT

class VtkVolumeDensityVisualiser(VolumeDensityVisualiser,VtkVolVis,VtkVis):
    """Represent an density using VTK
    see visualiser.py for the base class (VolumeVisualiser) which defines
    the user interactions
    """
    def __init__(self, root, graph, obj, **kw):
        apply(VolumeVisualiser.__init__, (self,root,graph,obj), kw)
        apply(VtkVolVis.__init__, (self,) , kw)

class VtkVolumeOrbitalVisualiser(VolumeOrbitalVisualiser,VtkVolVis,VtkVis):
    """Represent an Orbital using VTK volume rendering
    see visualiser.py for the base class (VolumeVisualiser) which defines
    the user interactions
    """
    def __init__(self, root, graph, obj, **kw):
        apply(VolumeVisualiser.__init__, (self,root,graph,obj), kw)
        apply(VtkVolVis.__init__, (self,) , kw)

class VtkGridVisualiser(GridVisualiser,VtkVis):

    """Represent an empty grid using VTK
    See visualiser.py for the base class which defines the user
    interactions. Since there is no data, in this case build will
    refresh the grid instead.
    Note ... this could be done using an outline view ...
    """

    def __init__(self, root, graph, obj, **kw):
        apply(GridVisualiser.__init__, (self,root,graph,obj), kw)
        self.alist = []
        self.alist2d = []
        self.points = [ (-1,-1,-1),(-1,-1, 1),(-1, 1,-1),(-1, 1, 1),
                        ( 1,-1,-1),( 1,-1, 1),( 1, 1,-1),( 1, 1, 1) ]
        self.lines = [ (1,2), (1,3), (1,5), (2,4),
                       (2,6), (3,4), (3,7), (4,8),
                       (5,6), (5,7), (6,8), (7,8) ] 

    def _build(self,object=None):
        """re-build the vtk elements"""
        nx = self.field.dim[0]
        o  = self.field.origin
        ax1 = self.field.axis[0]
        if len(self.field.dim) > 1:
            ny = self.field.dim[1]
            ax2 = self.field.axis[1]
        else:
            ny = 1
            ax2 = Vector(0.,0.,0.)
            
        ny = self.field.dim[1]
        if len(self.field.dim) > 2:
            nz = self.field.dim[2]
            ax3 = self.field.axis[2]
        else:
            nz = 1
            ax3 = Vector(0.,0.,0.)

        app = vtkAppendPolyData()
        for i,j in self.lines:
            x,y,z = self.points[i-1]
            start = o + 0.5*(x*ax1+y*ax2+z*ax3)
            x,y,z = self.points[j-1]
            end = o + 0.5*(x*ax1+y*ax2+z*ax3)

            s = vtkLineSource()
            s.SetPoint1(start)
            s.SetPoint2(end)
            app.AddInput(s.GetOutput())

            # create the mapper
            m = vtkPolyDataMapper()
            m.SetInput(app.GetOutput())

            # create the actor
            act = vtkActor()
            act.SetMapper(m)
            self.alist.append(act)

        self.showing = 0
        self.status = BUILT



class VtkDensityVisualiser(DensityVisualiser,VtkIsoSurf,VtkVis):
    """Represent an density using VTK
    see visualiser.py for the base class which defines
    the user interactions
    """
    def __init__(self, root, graph, obj, **kw):
        
        apply(DensityVisualiser.__init__, (self,root,graph,obj), kw)
        apply(VtkIsoSurf.__init__, (self,) , kw)

    def _build(self,object=None):
        plus_rgb = self.colourer.get_value("plus_rgb")
        #self.add_surface(self.height,self.plus_rgb,self.opacity)
        self.add_surface(self.height,plus_rgb,self.opacity)
        if self.show_outline:
            self.add_outline()
        self.status = BUILT



class VtkOrbitalVisualiser(OrbitalVisualiser,VtkIsoSurf,VtkVis):
    """Represent an orbital using VTK
    see visualiser.py for the base class which defines
    the user interactions
    """

    def __init__(self, root, graph, obj, **kw):
        OrbitalVisualiser.__init__(self,root,graph,obj,**kw)
        VtkIsoSurf.__init__(self,**kw)

    def _build(self,object=None):


        # Get values from the colourer
        minus_rgb = self.colourer.get_value("minus_rgb")
        plus_rgb = self.colourer.get_value("plus_rgb")

        self.add_surface(-self.height,minus_rgb,self.opacity)
        self.add_surface( self.height,plus_rgb,self.opacity)
#        self.add_surface(-self.height,self.minus_rgb,self.opacity)
#        self.add_surface( self.height,self.plus_rgb,self.opacity)
        if self.show_outline:
            self.add_outline()                                 
        self.status = BUILT

class VtkColourSurfaceVisualiser(ColourSurfaceVisualiser,VtkIsoSurf,VtkVis):
    """Viewer for surfaces, coloured using another data field
    """

    def __init__(self, root, graph, obj, **kw):
        apply(ColourSurfaceVisualiser.__init__, (self,root,graph,obj), kw)
        apply(VtkIsoSurf.__init__, (self,), kw)

    def _build(self,object=None):

        plus_rgb = self.colourer.get_value("plus_rgb")
        self.add_surface(self.height,plus_rgb,self.opacity)
        if self.show_outline:
            self.add_outline()
        self.status = BUILT

class VtkIrVis(IrregularDataVisualiser,VtkVis):
    """ Viewer for Irregular Data
    """

    def __init__(self, root, graph, obj, **kw):
        IrregularDataVisualiser.__init__(self,root,graph,obj,**kw)
        self.alist = []
        self.alist2d = []

    def _build(self,object=None):

        if self.field.vtkdata:
            im2poly = vtkImageDataGeometryFilter()
            im2poly.SetInput( self.field.vtkdata )
            poly = im2poly.GetOutput()
            
        else:
            # Here we are building up the grid from data stored in python data
            # structures held in the Field object
            # Build up the grid
            gridpts = self.field.get_grid()
            p = vtkPoints()
            n = len(gridpts)
            p.SetNumberOfPoints(n)
            i = 0
            for pt in gridpts:
                p.SetPoint(i,pt[0],pt[1],pt[2])
                i = i + 1

            v = vtkCellArray()
            v.Allocate(n,n)

            i = 0
            for pt in gridpts:
                v.InsertNextCell(1)
                v.InsertCellPoint(i)
                i = i + 1

            poly = vtkPolyData()
            poly.SetPoints(p)
            poly.SetVerts(v)

            if self.field.data != None:
                data_array = vtkFloatArray()
                data_array.SetNumberOfValues(n)
                for i in range(n):
                    data_array.SetValue(i,self.field.data[i])
                poly.GetPointData().SetScalars(data_array)

        m = vtkPolyDataMapper()
        self.map = m            

        m.SetInput(poly)

        m.SetScalarRange(self.colourer.get_value("cmap_low"),
                         self.colourer.get_value("cmap_high"))
        lut = self.colourer.get_lut()
        if lut:
            m.SetLookupTable(lut)

        #m.SetScalarModeToUsePointFieldData()
        #m.ColorByArrayComponent('z',0)

        act = vtkActor()
        act.SetMapper(m)
        act.GetProperty().SetLineWidth(self.graph.field_line_width)
        act.GetProperty().SetPointSize(self.point_size)
        act.GetProperty().SetOpacity(self.opacity)
        self.alist.append(act)
        self.status = BUILT

class VtkSlice(VtkCmapVis_):
    """Base class for viewers of 2D data fields

    this version assumes storage as lists of floats
    rather than numeric python objects
    The grid is generated as an explicit set of points
    """

    def __init__(self, root, graph, obj, **kw):
        self.alist = []
        self.alist2d = []
        self.debug = 1

        self.contour_colourmap_actor=None
        self.pcmap_colourmap_actor=None

    def convert_data(self,field):

        """Convert the input field object (class Field) into a
        vtkStructuredGrid object. If a 2D representation is required a
        second object, with modified points values so the contours
        are in the xy plane is also generated.
        """

        if self.debug: deb('convert slice data')
        npts = Vector(field.dim[0],field.dim[1],1)
        self.vtkgrid = vtkStructuredGrid()
        self.vtkgrid.SetDimensions(npts[0],npts[1],1)

        # Pack the data into a float array
        bigsize = npts[0]*npts[1]
        data_array = vtkFloatArray()
        data_array.SetNumberOfValues(bigsize)
        offset = 0
        if field.data:
            for j in range(npts[1]):
                for i in range(npts[0]):
                    data_array.SetValue(offset,field.data[offset])
                    offset = offset+1
        self.vtkgrid.GetPointData().SetScalars(data_array)
        bigsize = npts[0]*npts[1]
        points = vtkPoints()
        points.SetNumberOfPoints(bigsize)
        offset = 0
        grid = field.get_grid()
        for j in range(npts[1]):
            for i in range(npts[0]):
                points.SetPoint(offset,grid[offset])
                offset = offset+1
        self.vtkgrid.SetPoints(points)

        # projected version for 2D window.
        # this is a vtkStructuredPoints (ie image) dataset

        self.proj_vtkpoints = vtkStructuredPoints()
        self.proj_vtkpoints.SetDimensions(npts[0],npts[1],1)

        lenx = sqrt(field.axis[0]*field.axis[0])
        leny = sqrt(field.axis[1]*field.axis[1])
        lenmax = max(lenx,leny)
        spacex = lenx / (lenmax *float(npts[0]))
        spacey = leny / (lenmax *float(npts[1]))
        self.proj_vtkpoints.SetSpacing(spacex,spacey,1.)

        ox = -spacex*float(npts[0])/2.0
        oy = -spacey*float(npts[1])/2.0
        self.proj_vtkpoints.SetOrigin(ox,oy,0.)
        if self.debug:
            deb('spacings'+str([spacex,spacey]))
            deb('origin  '+str([ox,oy]))

        # second version
        # we can plot the image twice with different
        # spacial position .. note the origin shift on z
        # that way contours appear in front of the colourmap
        #
        self.proj_vtkpoints2 = vtkStructuredPoints()
        self.proj_vtkpoints2.SetDimensions(npts[0],npts[1],1)
        self.proj_vtkpoints2.SetSpacing(spacex,spacey,1.)
        self.proj_vtkpoints2.SetOrigin(ox,oy,0.001)
        self.proj_vtkpoints2.GetPointData().SetScalars(data_array)

##  - no need for this code as all projection is done with
##           vtkStructuredPoints (aka image) data
##        self.proj_vtkgrid = vtkStructuredGrid()
##        self.proj_vtkgrid.SetDimensions(npts[0],npts[1],1)
##        self.proj_vtkgrid.GetPointData().SetScalars(data_array)
##        points = vtkPoints()
##        points.SetNumberOfPoints(bigsize)
##        offset = 0
##        grid = field.get_grid()
##        for j in range(npts[1]):
##            for i in range(npts[0]):
##                points.SetPoint(offset,grid[offset])
##                offset = offset+1
##        self.proj_vtkgrid.SetPoints(points)
##        self.proj_vtkpoints.GetPointData().SetScalars(data_array)

    def make_2d_contour_map(self,vtkgrid):
        if self.debug: deb('make contour map')
        s = vtkContourFilter()
        s.SetInput(vtkgrid)
        s.GenerateValues(self.ncont,self.min,self.max)
        m = vtkPolyDataMapper()
        m.SetInput(s.GetOutput())

        m.SetScalarRange(self.contour_colourer.get_value("cmap_low"),
                         self.contour_colourer.get_value("cmap_high"))
        
        default_lut = m.GetLookupTable()
        lut = self.contour_colourer.get_lut()
        if lut:
            m.SetLookupTable(lut)

        # Display colourmap bar
        if self.contour_colourer.get_value("show_colourmap_actor"):
            if not self.contour_colourmap_actor:
                self.contour_colourmap_actor = VtkCmapVis_(self.graph)
                # Set the default lookuptable
                self.contour_colourmap_actor.set_default_lut(default_lut)
                
            # Add the actor
            self.contour_colourmap_actor.add_colourmap_actor(
                self.contour_colourer)

        a = vtkActor()
        a.SetMapper(m)
        a.GetProperty().SetLineWidth(self.graph.field_line_width)
        self.alist.append(a)

    def make_proj_2d_contour_map(self,vtkpoints):

        if self.debug: deb('make projected contour map')
        s = vtkContourFilter()
        s.SetInput(vtkpoints)
        s.GenerateValues(self.ncont,self.min,self.max)
        m = vtkPolyDataMapper()
        m.SetInput(s.GetOutput())
        
#        m.SetScalarRange(self.contour_cmap_low,self.contour_cmap_high)
#        lut = self.graph.get_cmap_lut(self.contour_cmap_name)
        m.SetScalarRange(self.contour_colourer.get_value("cmap_low"),
                         self.contour_colourer.get_value("cmap_high"))
        lut = self.contour_colourer.get_lut()
        if lut:
            m.SetLookupTable(lut)

        a = vtkActor()
        a.SetMapper(m)
        a.GetProperty().SetLineWidth(self.graph.field_line_width)
        self.alist2d.append(a)

    def make_2d_pseudocolour_map(self,vtkgrid,field):
        """ build the pseudocolour plane
        field here is a Field object, used only as a source
        of the dimensions for setting extent
        """
        if self.debug: deb('make plane')
        ex = vtkStructuredGridGeometryFilter()
        ex.SetInput(vtkgrid)
        ex.SetExtent(0,field.dim[0]-1,0,field.dim[1]-1,0,0)
        m= vtkPolyDataMapper()
        m.SetInput(ex.GetOutput())

        default_lut = m.GetLookupTable()
        m.SetScalarRange(self.pcmap_colourer.get_value("cmap_low"),
                         self.pcmap_colourer.get_value("cmap_high"))
        lut = self.pcmap_colourer.get_lut()
        if lut:
            m.SetLookupTable(lut)

        # Display colourmap bar
        if self.pcmap_colourer.get_value("show_colourmap_actor"):
            if not self.pcmap_colourmap_actor:
                self.pcmap_colourmap_actor = VtkCmapVis_(self.graph)
                # Set the default lookuptable
                self.pcmap_colourmap_actor.set_default_lut(default_lut)
            # Add the actor
            self.pcmap_colourmap_actor.add_colourmap_actor(
                self.pcmap_colourer)


        a = vtkActor()
        a.GetProperty().SetOpacity(self.opacity)
        a.SetMapper(m)
        self.alist.append(a)

    def make_proj_2d_pseudocolour_map(self,vtkgrid,field):
        """ build the pseudocolour plane
        field here is a Field object, used only as a source
        of the dimensions for setting extent
        """
        if self.debug: deb('make proj plane')
        ex = vtkGeometryFilter()
        ex.SetInput(vtkgrid)
        ex.SetExtent(0,field.dim[0]-1,0,field.dim[1]-1,0,0)
        m= vtkPolyDataMapper()
        m.SetInput(ex.GetOutput())

#        m.SetScalarRange(self.pcmap_cmap_low,self.pcmap_cmap_high)
#        lut = self.graph.get_cmap_lut(self.pcmap_cmap_name)
        m.SetScalarRange(self.pcmap_colourer.get_value("cmap_low"),
                         self.pcmap_colourer.get_value("cmap_high"))
        lut = self.pcmap_colourer.get_lut()
        if lut:
            m.SetLookupTable(lut)

        a = vtkActor()
        a.GetProperty().SetOpacity(self.opacity)
        a.SetMapper(m)
        self.alist2d.append(a)

    def make_2d_outline(self,vtkgrid):
        if self.debug: deb('make outline')
        outline = vtkStructuredGridOutlineFilter()
        outline.SetInput(vtkgrid)
        m = vtkPolyDataMapper()
        m.SetInput(outline.GetOutput())
        a = vtkActor()
        a.SetMapper(m)
        red = self.outline_rgb[0] / 255.0
        green = self.outline_rgb[1] / 255.0
        blue = self.outline_rgb[2] / 255.0
        a.GetProperty().SetColor(red,green,blue)
        self.alist.append(a)

    def make_proj_2d_outline(self,vtkgrid):
        if self.debug: deb('make proj outline')
        outline = vtkOutlineFilter()
        outline.SetInput(vtkgrid)
        m = vtkPolyDataMapper()
        m.SetInput(outline.GetOutput())
        a = vtkActor()
        a.SetMapper(m)
        red = self.outline_rgb[0] / 255.0
        green = self.outline_rgb[1] / 255.0
        blue = self.outline_rgb[2] / 255.0
        a.GetProperty().SetColor(red,green,blue)
        self.alist2d.append(a)

    # jmht need to override vtkvis _show/_hide/_delete methods
    # as we've two possible colourmap actors

    def _hide(self):
        VtkVis._hide(self)
        if self.contour_colourmap_actor:
            self.contour_colourmap_actor.hide_colourmap_actor()
        if self.pcmap_colourmap_actor:
            self.pcmap_colourmap_actor.hide_colourmap_actor()
        
    def _show(self):
        VtkVis._show(self)

        # See if we are displaying a scalar bar to show the
        # colourmap we are using
        if self.contour_colourmap_actor:
            if ( self.contour_colourmap_actor.colourer.get_value(
                'show_colourmap_actor')):
                 self.contour_colourmap_actor.show_colourmap_actor()
        if self.pcmap_colourmap_actor:
            if ( self.pcmap_colourmap_actor.colourer.get_value(
                'show_colourmap_actor')):
                 self.pcmap_colourmap_actor.show_colourmap_actor()
            #print "added colourmap_actor in _show"
        
        self.show_colourmap_actor()
        
    def _delete(self):
        VtkVis._delete(self)
        if self.contour_colourmap_actor:
            self.contour_colourmap_actor.delete_colourmap_actor()
        if self.pcmap_colourmap_actor:
            self.pcmap_colourmap_actor.delete_colourmap_actor()


    

class VtkSliceVisualiser(SliceVisualiser,VtkSlice,VtkVis):
#class VtkSliceVisualiser(SliceVisualiser,VtkSlice,VtkCmapVis_):

    """Viewer for 2D data fields"""

    def __init__(self, root, graph, obj, **kw):
        SliceVisualiser.__init__(self,root,graph,obj,**kw)
        VtkSlice.__init__(self,root,graph,obj,**kw)
        self.convert_data(self.field)

    def _build(self,object=None):
        if self.show_cont:
            self.make_2d_contour_map(self.vtkgrid)
            if self.show_2d:
                self.make_proj_2d_contour_map(self.proj_vtkpoints2)
        if self.show_plane:
            self.make_2d_pseudocolour_map(self.vtkgrid, self.field)
            if self.show_2d:
                self.make_proj_2d_pseudocolour_map(self.proj_vtkpoints, self.field)
        if self.show_outline:
            self.make_2d_outline(self.vtkgrid)
            if self.show_2d:
                self.make_proj_2d_outline(self.proj_vtkpoints)

        self.status = BUILT

class VtkCutSliceVisualiser(CutSliceVisualiser,VtkSlice,VtkVis):

    """Viewer for slicing 3D data fields"""

    def __init__(self, root, graph, obj, **kw):
        CutSliceVisualiser.__init__(self,root,graph,obj,**kw)
        VtkSlice.__init__(self,root,graph,obj, **kw)
        self.convert_3d_data()


    def convert_3d_data(self):
        """ Call the correct converter depending on whether we are using Python or VTGK data
            structures.
        """

        if self.field.vtkdata:
            self.convert_3d_data_vtk()
        else:
            self.convert_3d_data_python()


    def convert_3d_data_vtk(self):
        """
           Don't need to perform any manipulations - just use the vtkImageData directly
           we are currently ignoring the fact that, in future, data might not be aligned
           along the axes as the Smeagol data will be for the time being.
        """
        self.vtkgrid3d = self.field.vtkdata


    def convert_3d_data_python(self):
        """
            Create the relevant VTK structures from data stored in Pyton data structures
        """
        # Policy here should depend on whether data is axis aligned
        axis_aligned = 0

        if axis_aligned:
            #
            # Use structured points (alias vtkImageData) if data is 
            # on the grid assumed by vtk
            #
            self.vtkgrid3d = vtkStructuredPoints()
            data = self.vtkgrid3d
            npts = Vector(self.field.dim[0],self.field.dim[1],self.field.dim[2])

            xspacing = self.field.grid[0]
            yspacing = self.field.grid[1]
            zspacing = self.field.grid[2]

            data.SetDimensions(npts[0],npts[1],npts[2])
            data.SetOrigin(self.field.origin[0],self.field.origin[1],self.field.origin[2])
            data.SetSpacing(xspacing,yspacing,zspacing)

            bigsize = npts[0]*npts[1]*npts[2]

            data_array = vtkFloatArray()
            data_array.SetNumberOfValues(bigsize)

            # The mess with the offsets is to correct for the fact that, although
            # Jaguar creates the output in the zyx ordering, the vtk libraries
            # want it in the xyz ordering.
            offset=0
            for i in range(npts[0]):
                for j in range(npts[1]):
                    for k in range(npts[2]):
                        data_array.SetValue(offset,self.field.lvl[k,j,i])
                    offset = offset+1

            #print self.field.lvl
            #tmp = Numeric.reshape(Numeric.transpose(self.field.lvl,[2,1,0]),(-1,))
            #print tmp
            #tmp = self.field.lvl
            #tmp = Numeric.reshape(self.field.lvl,(-1,))
            #data_array.SetFloatArray(tmp,bigsize,1)

            data.GetPointData().SetScalars(data_array)

            #del data_array  # clean up some of the memory

        else:
            # General case:
            # use the Field get_grid method to generate an explicit
            # representation of the point array, render as vtkStructuredGrid
            #
            print 'isov vis init'

            nx = self.field.dim[0]
            if len(self.field.dim) > 1:
                ny = self.field.dim[1]
            else:
                ny = 1

            ny = self.field.dim[1]
            if len(self.field.dim) > 2:
                nz = self.field.dim[2]
            else:
                nz = 1

            npts = Vector(nx,ny,nz)

            print 'dim',self.field.dim,'vec',npts

            self.vtkgrid3d = vtkStructuredGrid()
            self.vtkgrid3d.SetDimensions(npts[0],npts[1],npts[2])
            #
            # Pack the data into a float arrat
            bigsize = npts[0]*npts[1]*npts[2]
            # Not clear if this test is right!!
            if self.field.data:
                data_array = vtkFloatArray()
                data_array.SetNumberOfValues(bigsize)
                offset = 0
                for k in range(npts[2]):
                    for j in range(npts[1]):
                        for i in range(npts[0]):
                            data_array.SetValue(offset,self.field.data[offset])
                            offset = offset+1

                print 'set scalars'
                self.vtkgrid3d.GetPointData().SetScalars(data_array)

            bigsize = npts[0]*npts[1]*npts[2]
            points = vtkPoints()
            points.SetNumberOfPoints(bigsize)
            offset = 0
            print 'getting grid'
            grid = self.field.get_grid()
            print 'grid done'

            for k in range(npts[2]):
                for j in range(npts[1]):
                    for i in range(npts[0]):
                        points.SetPoint(offset,grid[offset])
                        offset = offset+1

            print 'setPoints'
            self.vtkgrid3d.SetPoints(points)


    def _build(self,object=None):

        # This will set up self.vtkgrid
        self.convert_data(self.cut_plane)

        if 0:
            # cutter code
            # seems that vtkcutter generates polydata, not dataset
            # so we can't contour it
            # plane = vtkPlane()
            # plane.SetOrigin(self.vtkgrid3d.GetCenter())
            # plane.SetNormal(1.,0,0)
            # planeCut = vtkCutter()
            # planeCut.SetInput(data)
            # planeCut.SetCutFunction(plane)
            # cutMapper = vtkDataSetMapper()
            # self planeCut.GetOutput())
            # cutMapper.SetInput(..)
            # cutActor = vtkActor()
            # cutActor.SetMapper(cutMapper)
            pass
        else:
            probe = vtkProbeFilter()
            probe.SetSource(self.vtkgrid3d)
            probe.SetInput(self.vtkgrid)

            # Generate a normalised XY representation
            # twice, to support overlay of contours and pseudocolourmaps
            self.proj_interp = vtkStructuredPoints()
            self.proj_interp.SetDimensions(self.cut_plane.dim[0],self.cut_plane.dim[1],1)
            lenx = sqrt(self.cut_plane.axis[0]*self.cut_plane.axis[0])
            leny = sqrt(self.cut_plane.axis[1]*self.cut_plane.axis[1])
            lenmax = max(lenx,leny)
            spacex = lenx / (lenmax *float(self.cut_plane.dim[0]-1))
            spacey = leny / (lenmax *float(self.cut_plane.dim[1]-1))
            self.proj_interp.SetSpacing(spacex,spacey,1.)
            ox = -spacex*float(self.cut_plane.dim[0]-1)/2.0
            oy = -spacey*float(self.cut_plane.dim[1]-1)/2.0
            self.proj_interp.SetOrigin(ox,oy,0.)
            if self.debug:
                deb('spacings'+str([spacex,spacey]))
                deb('origin  '+str([ox,oy]))
            # the second one to place contours above the plane
            self.proj_interp2 = vtkStructuredPoints()
            self.proj_interp2.SetDimensions(self.cut_plane.dim[0],self.cut_plane.dim[1],1)
            self.proj_interp2.SetSpacing(spacex,spacey,1.)
            self.proj_interp2.SetOrigin(ox,oy,0.01)

            # interpolate
            interp = vtkStructuredGrid()
            probe.SetOutput(interp)
            # since the interp object is not actually feeding through
            # to the pipeline, run an update so there is some data
            # there for us to copy 
            interp.Update()
            data_array = interp.GetPointData().GetScalars()
            self.proj_interp.GetPointData().SetScalars(data_array)
            self.proj_interp2.GetPointData().SetScalars(data_array)

        if self.show_cont:
            self.make_2d_contour_map(interp)
            if self.show_2d:
                self.make_proj_2d_contour_map(self.proj_interp2)
        if self.show_plane:
            self.make_2d_pseudocolour_map(interp,self.cut_plane)
            if self.show_2d:
                self.make_proj_2d_pseudocolour_map(self.proj_interp,self.cut_plane)
        if self.show_outline:
            self.make_2d_outline(interp)
            if self.show_2d:
                self.make_proj_2d_outline(self.proj_interp)

        self.status = BUILT


class VtkVectorVisualiser(VectorVisualiser,VtkSlice,VtkVis):

    """Viewer for visualising vector fields
    Includes ability to sample using internal 2D slice or a
    general grid
    """

    def __init__(self, root, graph, obj, **kw):

        VectorVisualiser.__init__(self,root,graph,obj,**kw)

        #jmht don't call this here - only call when needed
        self.vtkgrid3d=None
        self.convert_3d_data()

        self.hedgehog_visible = 0
        self.orientedglyphs_visible = 0
        self.streamlines_visible = 0
        self.streamarrows_visible = 0

        self.hedgehog_grid=None
        self.orientedglyphs_grid=None
        self.streamlines_grid=None
        self.streamarrows_grid=None

        self.hedgehog_actors = []
        self.orientedglyphs_actors = []
        self.streamlines_actors = []
        self.streamarrow_actors = []

        self.hedgehog_colourmap_actor=None
        self.orientedglyphs_colourmap_actor=None
        self.streamlines_colourmap_actor=None
        self.streamarrows_colourmap_actor=None

        
        self.debug = 0

    def convert_3d_data(self):
        """Take the field stored in Python and create the VTK grid from it.
        This is then stored as vtkgrid3d.
        
        """

        # Policy here should depend on whether data is axis aligned or not
        axis_aligned = 0

        #print "convert_3d_data vector "
        #print self.field
        if axis_aligned:
            #
            # Use structured points (alias vtkImageData) if data is 
            # on the grid assumed by vtk
            #
            self.vtkgrid3d = vtkStructuredPoints()
            data = self.vtkgrid3d
            npts = Vector(self.field.dim[0],self.field.dim[1],self.field.dim[2])

            xspacing = self.field.grid[0]
            yspacing = self.field.grid[1]
            zspacing = self.field.grid[2]

            data.SetDimensions(npts[0],npts[1],npts[2])
            data.SetOrigin(self.field.origin[0],self.field.origin[1],self.field.origin[2])
            data.SetSpacing(xspacing,yspacing,zspacing)

            bigsize = npts[0]*npts[1]*npts[2]

            data_array = vtkFloatArray()
            data_array.SetNumberOfValues(bigsize)

            # The mess with the offsets is to correct for the fact that, although
            # Jaguar creates the output in the zyx ordering, the vtk libraries
            # want it in the xyz ordering.
            offset=0
            for i in range(npts[0]):
                for j in range(npts[1]):
                    for k in range(npts[2]):
                        data_array.SetValue(offset,self.field.lvl[k,j,i])
                    offset = offset+1

            #print self.field.lvl
            #tmp = Numeric.reshape(Numeric.transpose(self.field.lvl,[2,1,0]),(-1,))
            #print tmp
            #tmp = self.field.lvl
            #tmp = Numeric.reshape(self.field.lvl,(-1,))
            #data_array.SetFloatArray(tmp,bigsize,1)

            data.GetPointData().SetScalars(data_array)

            #del data_array  # clean up some of the memory

        else:
            #
            # General case:
            # use the Field get_grid method to generate an explicit
            # representation of the point array, render as vtkStructuredGrid
            #
            field = self.field
            #print 'convert field'

            try:

                # Regular Case

                nx = field.dim[0]
                if len(field.dim) > 1:
                    ny = field.dim[1]
                else:
                    ny = 1

                ny = field.dim[1]
                if len(field.dim) > 2:
                    nz = field.dim[2]
                else:
                    nz = 1

                npts = Vector(nx,ny,nz)
                print 'dim',field.dim,'vec',npts
                data = vtkStructuredGrid()
                data.SetDimensions(npts[0],npts[1],npts[2])
                #
                # Pack the data into a float arrat
                #
                bigsize = npts[0]*npts[1]*npts[2]
                # Not clear if this test is right!!
                #print 'DATA', len(field.data), field.ndd


                # Build points array
                bigsize = npts[0]*npts[1]*npts[2]
                points = vtkPoints()
                points.SetNumberOfPoints(bigsize)
                offset = 0
                #print 'getting grid', field
                grid = field.get_grid()
                #    print 'grid done'

                for k in range(npts[2]):
                    for j in range(npts[1]):
                        for i in range(npts[0]):
                            points.SetPoint(offset,grid[offset])
                            offset = offset+1

                #print 'setPoints'
                data.SetPoints(points)

            except AttributeError:

                # Iregular Case

                data  = vtkPolyData()

                #print "getting grid",self.field
                self.field.list()

                gridpts = self.field.get_grid()
                points = vtkPoints()
                n = len(gridpts)
                points.SetNumberOfPoints(n)
                i = 0
                for pt in gridpts:
                    points.SetPoint(i,pt[0],pt[1],pt[2])
                    i = i + 1

                data.SetPoints(points)
                bigsize = len(gridpts)

##                 v = vtkCellArray()
##                 v.Allocate(n,n)

##                 i = 0
##                 for pt in gridpts:
##                     v.InsertNextCell(1)
##                     v.InsertCellPoint(i)
##                     i = i + 1

##                 poly = vtkPolyData()
##                 poly.SetPoints(p)
##                 poly.SetVerts(v)
                    
            data_array = vtkFloatArray()
            data_array.SetNumberOfComponents(3)
            data_array.SetNumberOfTuples(bigsize)

            for offset in range(bigsize):
                tup = [ field.data[3*offset],field.data[3*offset+1], field.data[3*offset+2]]
                tup = truncate_vec(tup,1.0)
                data_array.SetTuple3(offset,tup[0],tup[1],tup[2])

            data.GetPointData().SetVectors(data_array)
            #data.GetPointData().SetVectors(data_array)

            self.vtkgrid3d = data
            #print "self.vtkgrid3d = ",self.vtkgrid3d
            return self.vtkgrid3d


    def thin_grid(self,refGrid,factor=2):
        """Thin a vtkgrid by sampling a subset of it's points
        return a new vtkgrid
        Currently rather crude
        """

        #print "thin_grid"

        gridType = refGrid.GetClassName()
        if gridType == 'vtkStructuredGrid':
            print "reducing resolution for vtkStructuredGrid by %d" % factor
            dim = refGrid.GetDimensions()
            eg = vtkExtractGrid()
            eg.SetSampleRate(factor,factor,factor)
            eg.SetInput(refGrid)
            newGrid = eg.GetOutput()
        elif gridType == 'vtkUnstructuredGrid':
            print "reducing resolution for vtkUnstructuredGrid by %d" % factor

            # This feels like taking a sledgehammer to a nut, but while I don't know
            # any better, for unstructured grids, we manually go through the points and
            # data and pull out every 'factor' value

            # Is also a bit cludgy as we use the InsertNext method to add data/points
            # instead of working out the size and them setting the values
            # no idea if this has much of an impact on performance
            newGrid = vtkUnstructuredGrid()

            # Thin the points
            newpoints = vtkPoints()
            oldpoints = refGrid.GetPoints()
            npoints = oldpoints.GetNumberOfPoints()
            for i in range( 0, npoints, factor ):
                point = oldpoints.GetPoint( i )
                newpoints.InsertNextPoint( point )
            newGrid.SetPoints( newpoints )

            # Thin the Data
            pointData = refGrid.GetPointData()
            #Scalar data
            oldScalars = pointData.GetScalars()
            if oldScalars:
                #print "copying scalars"
                dtype =  oldScalars.GetDataType()
                if dtype == VTK_FLOAT:
                    newScalars = vtkFloatArray()
                else:
                    raise Exception,"NEED TO ADD MORE DATA TYPES"
                newScalars.SetNumberOfComponents(1)
                for i in range(0,npoints,factor):
                    newScalars.InsertNextValue(oldScalars.GetValue(i))
                newGrid.GetPointData().SetScalars( newScalars )

            # Vector data
            oldVectors = pointData.GetVectors()
            if oldVectors:
                #print "copying vectors ",oldVectors
                dtype =  oldVectors.GetDataType()
                if dtype == VTK_FLOAT:
                    newVectors = vtkFloatArray()
                else:
                    raise Exception,"NEED TO ADD MORE DATA TYPES"
                
                newVectors.SetNumberOfComponents(3)
                #print "set components"
                for i in range(0,npoints,factor):
                    v =  oldVectors.GetTuple3(i)
                    newVectors.InsertNextTuple3( v[0],v[1],v[2] )
                #print "setting vectors"
                newGrid.GetPointData().SetVectors( newVectors )
        else:
            raise Exception,"thin_grid unknown gridType: %s" % gridType

        newGrid.Update() # This appears to be needed in some cases
        #print "returning newGrid ",newGrid
        return newGrid


    def get_sample_grid(self,source=None):
        """Convert the input field object (class Field) into a
        vtkStructuredGrid object. If a 2D representation is required a
        second object, with modified points values so the contours
        are in the xy plane is also generated.

        """

        if source:
            mygrid=source
        else:
            # Get a copy of the grid
            mygrid = self.get_grid()

        # If we're sampling at all points just return it
        if self.sample_grid == VECTOR_SAMPLE_ALL:
            return mygrid

        # sample the grid.
        print "vtkgraph.py vector get_sample_grid"
        field = self.sample_grid
        #print "grid is ",field.list()
        #if self.debug: deb('convert sample data')
        self.vtk_sample_grid = vtkUnstructuredGrid()
        # Pack the data into a float array
        #bigsize = sample_grid.npts[0]*npts[1]

        grid = self.sample_grid.get_grid()

        #####print 'sample grid',grid
        bigsize = len(grid)
        offset = 0
        if field.data:
            data_array = vtkFloatArray()
            data_array.SetNumberOfValues(bigsize)
            for i in range(bigsize):
                data_array.SetValue(i,field.data[i])

            self.vtk_sample_grid.GetPointData().SetScalars(data_array)

        points = vtkPoints()
        points.SetNumberOfPoints(bigsize)

        for i in range(bigsize):
            points.SetPoint(i,grid[i])

        if self.debug:
            print 'points'
            print points

        self.vtk_sample_grid.SetPoints(points)

        if self.debug:
            print self.vtk_sample_grid

        # The grid is being sampled
        probe = vtkProbeFilter()
        #probe.SetSource(self.vtkgrid3d)
        probe.SetSource(mygrid)
        probe.SetInput(self.vtk_sample_grid)
        interp = probe.GetUnstructuredGridOutput()

        # since the interp object is not actually feeding through
        # to the pipeline, run an update so there is some data
        # there for us to copy 

        interp.Update()
        ###data_array = interp.GetPointData().GetScalars()
        ###self.proj_interp.GetPointData().SetScalars(data_array)
        return interp

    def get_grid(self):
        """Return the grid that the data is to be plotted from
        We return a copy of the original grid as each visualiser
        needs it's own copy as it will change the scalar values
        depending on how it is colouring it.
        """

        
        if self.vtkgrid3d:
            source = self.vtkgrid3d
        else:
            source = self.convert_3d_data()
        
        # Need to copy the grid as each visualiser has it's own
        # copy
        gridType = source.GetClassName()
        if gridType == 'vtkStructuredGrid':
            newGrid=vtkStructuredGrid()
        elif gridType == 'vtkUnstructuredGrid':
            newGrid=vtkUnstucturedGrid()
        else:
            raise Exception,"get_grid unknown gridType: %s" % gridType
        
        # Can't copy as DeepCopying the grid causes a seg fault
        newGrid.ShallowCopy(source)
        #newGrid.DeepCopy(source)

        return newGrid
        

    def set_grid_scalars(self,grid,obj):
        """Set the scalars on the grid from a source object. This
        is done so that the grid can be coloured by the scalars.
        obj can be None in which case the scalars are set to None
        """

        #print "set_grid_scalars"
        if obj:
            #bigsize = self.vtkgrid3d.GetPoints().GetNumberOfPoints()
            bigsize = grid.GetPoints().GetNumberOfPoints()
            data_array = vtkFloatArray()
            data_array.SetNumberOfValues(bigsize)
            for offset in range(bigsize):
                data_array.SetValue(offset,obj.data[offset])
            grid.GetPointData().SetScalars(data_array)
            #grid.Update()
            #self.vtkgrid3d.GetPointData().SetScalars(data_array)
            #self.vtkgrid3d.GetPointData().AddArray(data_array)
            #self.vtkgrid3d.GetPointData().SetActiveScalars("MapScalarj")
        else:
            grid.GetPointData().SetScalars(None)
        
    
    def _build(self,object=None):

        if self.debug:
            print 'show_hedgehog',self.show_hedgehog
            print 'show_orientedglyphs',self.show_orientedglyphs
            print 'show_streamlines',self.show_streamlines
            print 'show_streamarrows',self.show_streamarrows
            print 'sample_grid',self.sample_grid
            print 'hedgehog_scale',self.hedgehog_scale
            print 'orientedglyph_scale',self.orientedglyph_scale
            print 'streamline_propagation_time',self.streamline_propagation_time
            print 'streamline_integration_step_length',self.streamline_integration_step_length
            print 'streamline_step_length',self.streamline_step_length
            print 'streamline_display',self.streamline_display


        # Now display the vector fields using a variety of methods
        if self.show_hedgehog:
            self._build_hedgehog()
            
        if self.show_orientedglyphs:
            self._build_orientedglyphs()
            
        if self.show_streamlines:
            self._build_streamlines()

        if self.show_streamarrows:
            self._build_streamarrows()
            
        self.status = BUILT

    def _build_hedgehog(self):
        """Display the hedgeghog representation"""
        

        # If we dont' have the data get it
        #if not self.hedgehog_grid:
        source = self.get_sample_grid()

        # We create a simple pipeline to display the data.
        # we could do with applying the truncation at some stage
        hedgehog = vtkHedgeHog()
        if self.debug:
            print 'Source'
            print source
        hedgehog.SetInput(source)
        hedgehog.SetScaleFactor(self.hedgehog_scale)
        #hedgehog.SetLineWidth(2.0)
        if self.debug:
            print hedgehog
        m = vtkPolyDataMapper()
        m.SetInput(hedgehog.GetOutput())
        hedgehogActor = vtkActor()
        hedgehogActor.SetMapper(m)

        # Get the default lookup table as we need to pass this to the
        # scalarbar actor
        default_lut = m.GetLookupTable()
        lut = self.hedgehog_colourer.get_lut()
        if lut:
            m.SetLookupTable(lut)

        # Set scalar range according to the colourer
        cmap_low = self.hedgehog_colourer.get_value("cmap_low")
        cmap_high = self.hedgehog_colourer.get_value("cmap_high")
        m.SetScalarRange(cmap_low,cmap_high)

        if self.hedgehog_colourer.cmap_by_object():
            #m.ScalarVisibilityOn()
            cmap_obj=self.hedgehog_colourer.get_value("cmap_obj")
            self.set_grid_scalars(source,cmap_obj)
            
            # See if we are displaying a scalar bar to show the
            # colourmap we are using
            if ( self.hedgehog_colourer.get_value('show_colourmap_actor') ):
                if not self.hedgehog_colourmap_actor:
                    self.hedgehog_colourmap_actor = VtkCmapVis(self.graph)
                    
                # Set the default lookuptable
                self.hedgehog_colourmap_actor.set_default_lut(default_lut)
                
                self.hedgehog_colourmap_actor.add_colourmap_actor(
                    self.hedgehog_colourer)
                #self.add_colourmap_actor(self.hedgehog_colourer)
                #print "added colourmap_actor in _show"
        else:
            #m.ScalarVisibilityOff()
            self.set_grid_scalars(source,None)
            # Convert from 0-255 to 0-1
            colour = map(lambda x: float(x)/255.,
                         self.hedgehog_colourer.get_value("plus_rgb") )
            hedgehogActor.GetProperty().SetColor(colour)
            #print dir(m)
            #print "scalarmode is ",m.GetScalarModeAsString()


        #m.ColorByArrayComponent("MapScalar",0);
        #m.SetScalarModeToUsePointFieldData()
        self.hedgehog_actors.append(hedgehogActor)

    def _build_orientedglyphs(self):
        """Show the oriented glyphs"""

        # If we dont' have the data get it
        #if not self.orientedglyphs_grid:
        source = self.get_sample_grid()

        cone = vtkConeSource()
        cone.SetResolution(10)

        arrow = vtkGlyph3D()
        arrow.SetInput(source)
        arrow.SetSource(cone.GetOutput())
        arrow.SetScaleFactor(self.orientedglyph_scale)
        ###arrow.ScalingOff()
        arrow.SetScaleModeToScaleByVector()
        #make range current 
        arrow.Update() 

        m=vtkPolyDataMapper()
        m.SetInput(arrow.GetOutput())
        vectorActor = vtkActor()
        vectorActor.SetMapper(m)

        # Get the default lookup table as we need to pass this to the
        # scalarbar actor
        default_lut = m.GetLookupTable()
        lut = self.orientedglyphs_colourer.get_lut()
        if lut:
            m.SetLookupTable(lut)

        # Determine how to colour the glyphs
        if self.orientedglyphs_colourer.cmap_by_object():
            m.ScalarVisibilityOn()
            cmap_obj=self.orientedglyphs_colourer.get_value("cmap_obj")
            self.set_grid_scalars(source,cmap_obj)

            # See if we are displaying a scalar bar to show the
            # colourmap we are using
            if ( self.orientedglyphs_colourer.get_value(
                'show_colourmap_actor') ):
                if not self.orientedglyphs_colourmap_actor:
                    self.orientedglyphs_colourmap_actor=VtkCmapVis(self.graph)
                # Set the default lookuptable
                self.orientedglyphs_colourmap_actor.set_default_lut(
                    default_lut)
                self.orientedglyphs_colourmap_actor.add_colourmap_actor(
                    self.orientedglyphs_colourer)
            
        else:
            m.ScalarVisibilityOff()
            self.set_grid_scalars(source,None)
            # Convert from 0-255 to 0-1
            colour = map(lambda x: float(x)/255.,
                         self.orientedglyphs_colourer.get_value("plus_rgb") )
            vectorActor.GetProperty().SetColor(colour)

        self.orientedglyphs_actors.append(vectorActor)

            
    def _build_streamlines(self):
        """ Show the streamlines"""
    
        # If we dont' have the data get it
        #if not self.streamlines_grid:
        #self.streamlines_grid = self.get_grid()

        #writer=vtkUnstructuredGridWriter()
        #writer.SetInput( self.streamlines_grid )
        #writer.SetFileName('/home/jmht/segf.vtk')
        #writer.Write()


        # We use a rake to generate a series of streamline starting points
        # scattered along a line. Each point will generate a streamline.
        if 0:
            rake=vtkLineSource()
            rake.SetPoint1(-1,-1,-2)
            rake.SetPoint2(1,1,2)
            rake.SetResolution(41)
            rakeMapper=vtkPolyDataMapper()
            rakeMapper.SetInput(rake.GetOutput())
            rakeActor=vtkActor()
            rakeActor.SetMapper(rakeMapper)        

        sl=vtkStreamLine()

        # Get the grid with all the data
        source=self.get_grid()
        
        # Get the grid we are sampling the data on
        sample = self.get_sample_grid(source=source)

        # Thin the sample grid if requested
        if self.streamline_thin_points > 1:
            sample = self.thin_grid(sample,
                                    factor=self.streamline_thin_points)        

        # Set input and source
        sl.SetInput(source)
        sl.SetSource(sample)
        #sl.SetSource(rake.GetOutput())
        
        #integ=vtkRungeKutta45()
        integ=vtkRungeKutta4()
        #integ=vtkRungeKutta2()
        sl.SetIntegrator(integ)

        
        sl.SetMaximumPropagationTime(self.streamline_propagation_time)
        sl.SetIntegrationStepLength(self.streamline_integration_step_length)
        sl.SetStepLength(self.streamline_step_length)

        if self.streamline_integration_direction == STREAM_BOTH:
            sl.SetIntegrationDirectionToIntegrateBothDirections()
        elif self.streamline_integration_direction == STREAM_FORWARD:
            sl.SetIntegrationDirectionToForward()
        elif self.streamline_integration_direction == STREAM_BACKWARD:
            sl.SetIntegrationDirectionToBackward()


        streamlineMapper=vtkPolyDataMapper()
        # Get the default lookup table for the scalarbar actor
        default_lut = streamlineMapper.GetLookupTable()

        # Determine how to colour the streamwotsits
        cscheme = self.streamlines_colourer.get_value("scheme")
        if cscheme == "Uniform":
            streamlineMapper.ScalarVisibilityOff()
        elif cscheme == "Speed":
            sl.SpeedScalarsOn()
        else:
            # Colourmapping by another object
            cmap_obj=self.streamlines_colourer.get_value("cmap_obj")
            self.set_grid_scalars(source,cmap_obj)

        # Set the colour lookuptable & mapping values for
        # all streamlines/tubes/surfaces
        lut = self.streamlines_colourer.get_lut()
        cmap_high = self.streamlines_colourer.get_value("cmap_high")
        cmap_low  = self.streamlines_colourer.get_value("cmap_low")

        # Check to display a scalar bar
        if cscheme == "Speed" or self.streamlines_colourer.cmap_by_object():
            if ( self.streamlines_colourer.get_value(
                'show_colourmap_actor') ):
                if not self.streamlines_colourmap_actor:
                    self.streamlines_colourmap_actor = VtkCmapVis(self.graph)
                # Set the default lookuptable
                self.streamlines_colourmap_actor.set_default_lut(default_lut)
                self.streamlines_colourmap_actor.add_colourmap_actor(
                    self.streamlines_colourer)

        streamlineMapper.SetScalarRange(cmap_low,cmap_high)

        if lut:
            streamlineMapper.SetLookupTable(lut)
            
        if self.streamline_display == STREAM_LINES:

            streamlineMapper.SetInput(sl.GetOutput())

            streamlineActor=vtkActor()

            # Colour if using uniform
            if cscheme == 'Uniform':
                # Convert from 0-255 to 0-1
                colour = map(lambda x: float(x)/255.,
                             self.streamlines_colourer.get_value("plus_rgb") )
                streamlineActor.GetProperty().SetColor(colour)
            
            streamlineActor.SetMapper(streamlineMapper)

        elif self.streamline_display == STREAM_TUBES:

            # The tube is wrapped around the generated streamline. By varying the
            # radius by the inverse of vector magnitude, we are creating a tube
            # whose radius is proportional to mass flux (in incompressible flow).
            streamTube = vtkTubeFilter()
            streamTube.SetInput(sl.GetOutput())
            streamTube.SetRadius(0.02)
            streamTube.SetNumberOfSides(12)
            #streamTube.SetVaryRadiusToVaryRadiusByVector()
            streamlineMapper.SetInput(streamTube.GetOutput())

            streamlineActor = vtkActor()
            streamlineActor.SetMapper(streamlineMapper)
            streamlineActor.GetProperty().BackfaceCullingOn()

        elif self.streamline_display == STREAM_SURFACE:            

            # These streamlines are then fed to the vtkRuledSurfaceFilter
            # which stitches  the lines together to form a surface.
            # Note the SetOnRation method. It turns on every other strip that
            # the filter generates (only when multiple lines are input).

            scalarSurface=vtkRuledSurfaceFilter()
            scalarSurface.SetInput(sl.GetOutput())
            scalarSurface.SetOffset(0)
            scalarSurface.SetOnRatio(2)
            scalarSurface.PassLinesOn()
            scalarSurface.SetRuledModeToPointWalk()
            scalarSurface.SetDistanceFactor(30)

            streamlineMapper.SetInput(scalarSurface.GetOutput())
            streamlineActor=vtkActor()
            streamlineActor.SetMapper(streamlineMapper)
        else:
            print 'BAD DISPLAY FLAG'


        self.streamlines_actors.append(streamlineActor)
        ##  eval mapper SetScalarRange [[pl3d GetOutput] GetScalarRange]

    def _build_streamarrows(self):
        """Display the streamarrows"""


        # Get the source and sample grid
        source = self.get_grid()
        sample = self.get_sample_grid(source=source)

        # Thin the grid
        if self.streamarrow_thin_points > 1:
            sample = self.thin_grid(sample,factor=self.streamarrow_thin_points)
            
        sa=vtkStreamPoints()
        sa.SetInput(source)
        sa.SetSource(sample)

        integ=vtkRungeKutta4()
        sa.SetIntegrator(integ)
        sa.SetMaximumPropagationTime(self.streamarrow_propagation_time)
        sa.SetIntegrationStepLength(self.streamarrow_integration_step_length)
        sa.SetTimeIncrement(self.streamarrow_time_increment)
        if self.streamarrow_integration_direction == STREAM_BOTH:
            sa.SetIntegrationDirectionToIntegrateBothDirections()
        elif self.streamarrow_integration_direction == STREAM_FORWARD:
            sa.SetIntegrationDirectionToForward()
        elif self.streamarrow_integration_direction == STREAM_BACKWARD:
            sa.SetIntegrationDirectionToBackward()

        # Display arrows or cones
        if self.streamarrow_type=='Arrow':
            arrow = vtkArrowSource()
            arrow.SetTipResolution(30)
            arrow.SetShaftResolution(30)
            arrow.SetTipRadius(0.2) #0.1
            arrow.SetTipLength(0.7) #0.35
            arrow.SetShaftRadius(0.06) #0.03
        elif self.streamarrow_type=='Cone':
            arrow = vtkConeSource()
            arrow.SetResolution(30)
        else:
            print "STREAMARROW_TYPE UNKNOWN TYPE!: ",self.streamarrow_type

        glyph = vtkGlyph3D()
        glyph.SetInput(sa.GetOutput())
        glyph.SetSource(arrow.GetOutput())

        # Determine how to scale the arrows
        #glyph.SetVectorModeToUseNormal()
        glyph.SetVectorModeToUseVector()
        if self.streamarrow_scale:
            glyph.SetScaleModeToScaleByVector()
        else:
            glyph.SetScaleModeToDataScalingOff()
        glyph.SetScaleFactor(self.streamarrow_size)

        # Sort out the colouring
        m=vtkPolyDataMapper()
        
        # Get the default lookup table as we need to pass this to the
        # scalarbar actor
        default_lut = m.GetLookupTable()
        
        cscheme = self.streamarrows_colourer.get_value("scheme")
        if cscheme == "Uniform":
            m.ScalarVisibilityOff()
        elif cscheme == "Vector":
            # If we are colouring by the vector values alone
            glyph.SetColorModeToColorByVector()
        else:
            # Colourmapping by another object so set the scalar values
            m.ScalarVisibilityOn()
            cmap_obj=self.streamarrows_colourer.get_value("cmap_obj")
            self.set_grid_scalars(source,cmap_obj)
            
        m.SetInput(glyph.GetOutput())
        
        lut = self.streamarrows_colourer.get_lut()
        if lut:
            m.SetLookupTable(lut)
        cmap_high = self.streamarrows_colourer.get_value("cmap_high")
        cmap_low  = self.streamarrows_colourer.get_value("cmap_low")
        m.SetScalarRange(cmap_low,cmap_high)


        # Decide whether to display a scalar bar
        if cscheme == "Vector" or self.streamarrows_colourer.cmap_by_object():
            if ( self.streamarrows_colourer.get_value('show_colourmap_actor') ):
                if not self.streamarrows_colourmap_actor:
                    self.streamarrows_colourmap_actor = VtkCmapVis(self.graph)
                    
                # Set the default lookuptable
                self.streamarrows_colourmap_actor.set_default_lut(default_lut)
                
                self.streamarrows_colourmap_actor.add_colourmap_actor(
                    self.streamarrows_colourer)

        streamArrowActor=vtkActor()
        # Colour if using uniform
        if cscheme == 'Uniform':
            # Convert from 0-255 to 0-1
            colour = map(lambda x: float(x)/100.,
                         self.streamarrows_colourer.get_value("plus_rgb") )
            streamArrowActor.GetProperty().SetColor(colour)
        
        streamArrowActor.SetMapper(m) 
        self.streamarrow_actors.append(streamArrowActor)
            

    def _delete(self):
        """Remove all vtk components of the image"""

        if self.debug:
            print '_delete'

        # Hedgehog
        for a in self.hedgehog_actors:
            self.graph.ren.RemoveActor(a)
        if self.hedgehog_colourmap_actor:
            self.hedgehog_colourmap_actor.delete_colourmap_actor()
            self.hedgehog_colourmap_actor=None

        # Oriented Glyphs
        for a in self.orientedglyphs_actors:
            self.graph.ren.RemoveActor(a)
        if self.orientedglyphs_colourmap_actor:
            self.orientedglyphs_colourmap_actor.delete_colourmap_actor()
            self.orientedglyphs_colourmap_actor=None

        # Streamlines
        for a in self.streamlines_actors:
            self.graph.ren.RemoveActor(a)
        if self.streamlines_colourmap_actor:
            self.streamlines_colourmap_actor.delete_colourmap_actor()
            self.streamlines_colourmap_actor=None

        # Streamarrows
        for a in self.streamarrow_actors:
            self.graph.ren.RemoveActor(a)
        if self.streamarrows_colourmap_actor:
            self.streamarrows_colourmap_actor.delete_colourmap_actor()
            self.streamarrows_colourmap_actor=None

        # Reset dictionary for selection actors
        self.atom_to_selection_actors = {}

        self.hedgehog_actors = []
        self.orientedglyphs_actors = []
        self.streamlines_actors = []
        self.streamarrow_actors = []

        self.hedgehog_visible = 0
        self.orientedglyphs_visible = 0
        self.streamlines_visible = 0
        self.streamarrows_visible = 0
    
    def _hide(self):
        """remove all actors from the renderer"""
        if self.debug:
            print 'hide_', self.show_hedgehog, self.show_orientedglyphs, self.show_streamlines
            print '  visi', self.hedgehog_visible, self.orientedglyphs_visible, self.streamlines_visible

        if self.show_hedgehog and self.hedgehog_visible:
            for a in self.hedgehog_actors:
                self.graph.ren.RemoveActor(a)
            if self.hedgehog_colourmap_actor:
                self.hedgehog_colourmap_actor.hide_colourmap_actor()
            self.hedgehog_visible = 0

        if self.show_orientedglyphs and self.orientedglyphs_visible:
            for a in self.orientedglyphs_actors:
                self.graph.ren.RemoveActor(a)
            if self.orientedglyphs_colourmap_actor:
                self.orientedglyphs_colourmap_actor.hide_colourmap_actor()
            self.orientedglyphs_visible = 0

        if self.show_streamlines and self.streamlines_visible:
            for a in self.streamlines_actors:
                self.graph.ren.RemoveActor(a)
            if self.streamlines_colourmap_actor:
                self.streamlines_colourmap_actor.hide_colourmap_actor()
            self.streamlines_visible = 0

        if self.show_streamarrows and self.streamarrows_visible:
            for a in self.streamarrow_actors:
                self.graph.ren.RemoveActor(a)
            if self.streamarrows_colourmap_actor:
                self.streamarrows_colourmap_actor.hide_colourmap_actor()
            self.streamarrows_visible = 0


    def _show(self):
        """Ensure that all requested images are showing"""
        if self.debug:
            print 'show_', self.show_hedgehog, self.show_orientedglyphs, self.show_streamlines
            print '  visi', self.hedgehog_visible, self.orientedglyphs_visible, self.streamlines_visible

        # Hedgehog
        if self.show_hedgehog:
            if not self.hedgehog_visible:
                for a in self.hedgehog_actors:
                    self.graph.ren.AddActor(a)
                    #print 'add hedgehog'
                if self.hedgehog_colourmap_actor:
                    self.hedgehog_colourmap_actor.show_colourmap_actor()
                self.hedgehog_visible=1
        else:
            if self.hedgehog_visible:
                for a in self.hedgehog_actors:
                    self.graph.ren.RemoveActor(a)
                    #print 'rem hedgehog'
                self.hedgehog_visible = 0

        # Orientedglyphs
        if self.show_orientedglyphs:
            if not self.orientedglyphs_visible:
                for a in self.orientedglyphs_actors:
                    #print 'add glyphs'
                    self.graph.ren.AddActor(a)
                if self.orientedglyphs_colourmap_actor:
                    self.orientedglyphs_colourmap_actor.show_colourmap_actor()
                self.orientedglyphs_visible = 1
        else:
            if self.orientedglyphs_visible:
                for a in self.orientedglyphs_actors:
                    self.graph.ren.RemoveActor(a)
                    #print 'rem glyphs'
                self.orientedglyphs_visible = 0

        # Streamlines
        if self.show_streamlines:
            if not self.streamlines_visible:
                for a in self.streamlines_actors:
                    #print 'add stream'
                    self.graph.ren.AddActor(a)
                if self.streamlines_colourmap_actor:
                    self.streamlines_colourmap_actor.show_colourmap_actor()
                self.streamlines_visible = 1
        else:
            if self.streamlines_visible:
                for a in self.streamlines_actors:
                    self.graph.ren.RemoveActor(a)
                    #print 'rem stream'
                self.streamlines_visible = 0

        # Streamarrows
        if self.show_streamarrows:
            if not self.streamarrows_visible:
                for a in self.streamarrow_actors:
                    #print 'add stream'
                    self.graph.ren.AddActor(a)
                if self.streamarrows_colourmap_actor:
                    self.streamarrows_colourmap_actor.show_colourmap_actor()
                self.streamarrows_visible = 1
        else:
            if self.streamarrows_visible:
                for a in self.streamarrow_actors:
                    self.graph.ren.RemoveActor(a)
                    #print 'rem stream'
                self.streamarrows_visible = 0


class VtkVibrationVisualiser(VibrationVisualiser,VtkMoleculeVisualiser):

    """Visualiser for molecular vibrations.
    Uses all low-level methods of the vtk molvis, for vibration
    specific code see VibrationVisualiser implementation (graph/visualiser.py)
    """
    def __init__(self, root, graph, obj, **kw):

        # this will assign self.vib & self.object to the visualisation object
        # and self.molecule to a copy to be visualised 
        apply(VibrationVisualiser.__init__, (self,root,graph,obj), kw)
        apply(VtkMoleculeVisualiser.__init__, (self,root,graph,self.molecule), kw)

        # This hack is needed to restore data overwritten
        self.title = 'Animate ' + self.vib.title

class VtkVibrationSetVisualiser(VibrationSetVisualiser,VtkMoleculeVisualiser):

    """Visualiser for a set of molecular vibrations.
    Uses all low-level methods of the vtk molvis, for vibration
    specific code see VibrationSetVisualiser implementation (graph/visualiser.py)
    """
    def __init__(self, root, graph, obj, **kw):

        # this will assign self.vib & self.object to the visualisation object
        # and self.molecule to a copy to be visualised 
        apply(VibrationSetVisualiser.__init__, (self,root,graph,obj), kw)
        apply(VtkMoleculeVisualiser.__init__, (self,root,graph,self.molecule), kw)

        # This hack is needed to restore data overwritten
        self.title = 'Animate ' + self.vib.title

class VtkTrajectoryVisualiser(TrajectoryVisualiser,VtkMoleculeVisualiser):
    """Visualiser for trajectorues
    Uses all low-level methods of the vtk molvis, for trajectory
    specific code see TrajectoryVisualiser implementation (graph/visualiser.py)
    """
    def __init__(self, root, graph, obj, **kw):
        TrajectoryVisualiser.__init__(self,root,graph,obj, **kw)
        VtkMoleculeVisualiser.__init__(self,root,graph,self.molecule, **kw)
        self.title = 'trajectory view'

class VtkMoldenWfnVisualiser(MoldenWfnVisualiser,VtkOrbitalVisualiser):

    """Visualiser for wavefunction (held as a molden-compatible
    output file, obj is just a string holding the name of the file)
    """
    def __init__(self, root, graph, obj, **kw):

        self.alist = []
        self.alist2d = []
        apply(MoldenWfnVisualiser.__init__, (self,root,graph,obj), kw)


    def _build(self,**kw):
        if object:
            print 'passed in object',object

        # execute MolDen call to build and convert grids if needed
        if self.compute_grid():
            self.convert_data()

        print 'plot height', self.height
        VtkOrbitalVisualiser._build(self)

    # this group of methods can act on the particular embedded visualiser
    # that we are using eg orbiral visualiser


class VtkColourMap(ColourMap):

    def _build(self):
        t = vtkLookupTable()
        t.SetNumberOfTableValues(len(self.colours))
        ix = 0
        for i in range(len(self.colours)):
            r,g,b = self.colours[i]
            r = float(r) / 255.0
            g = float(g) / 255.0
            b = float(b) / 255.0
            t.SetTableValue(ix,r,g,b,1)
            ix = ix + 1
        self.lut = t

if __name__ == "__main__":
    import sys
    root=Tk()
    root.withdraw()
    vt = VtkGraph(root)
    for file in sys.argv[1:]:
        print 'loading',file
        vt.load_from_file(file)
    vt.mainloop()
