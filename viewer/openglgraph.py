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

from viewer.main import *
from viewer.selections import *
from generic.visualiser import *
from generic.colourmap import ColourMap
from chempy import cpv

from objects.periodic import colours,rcov,rvdw,rgb_min,rgb_max
from viewer.selections2 import *

#
# Extend the path to access GLUT - the main bit we will be missing 
# os the DLL/.so File  This works for windows, maybe also linux ...
# to check
#
os.environ['PATH'] = os.environ['PATH'] + gui_path + os.sep + 'glut-3.7.6-bin'
print os.environ['PATH']

try:
    from OpenGL.GLUT import *
    from OpenGL.GL import *
    from OpenGL.Tk import *
except:
    print '''
    ERROR: PyOpenGL + GLUT not installed properly.
    '''
    sys.exit()


class OpenGLGraph(TkMolView,Graph):

    def __init__(self, parent, title=''):

        Graph.__init__(self)
        

        self.molecule_visualiser =  OpenGLMoleculeVisualiser
        self.colourmap_func = OpenGLColourMap

        self.capabilities['wire']=1
        self.capabilities['stick']=0
        self.capabilities['sphere']=1
        self.capabilities['labels']=0

        # Set defaults for any attributes properties that may be 
        # superceded by values from ccp1guirc
        self.pick_tolerance = 0.01
        self.near = None
        self.far = None        

        self.capabilities['wire']=1
        self.capabilities['sticks']=0
        self.capabilities['spheres']=1
        self.capabilities['labels']=0
        self.capabilities['contacts']=0
        self.capabilities['hedgehog']=0
        self.capabilities['orientedglyphs']=0
        self.capabilities['streamlines']=0


        TkMolView.__init__(self, parent)
        
        self.gl=GLView(self.interior())
        self.gl.pack(side = 'top', expand=1, fill = 'both',padx=3, pady=3)

        #self.toolbar()
        
        self.gl.tkRedraw()


        self.title('GLMolView'+25*' '+title)
        self.iconname('GLMolView')



        #self.pack()

    def fit_to_window(self):
        pass

    def drawmol(self,obj):
        self.gl.drawmol(obj)

    def update(self):
        ''' Update the screen '''
        print 'redraw'
        self.gl.tkRedraw()


    def save_image(self):
        file=asksaveasfilename(defaultextension='.ps',
        filetypes=[('PostScript','.ps'), ('PPM', '.ppm')])
        if file:
            glSavePPM(file, 500,500)

class GLView(Opengl):
    def __init__(self, parent):
        Opengl.__init__(self, parent, width=500,height=500)

        self.sphere_list = None
        self.line_list = None

        self.cc=[0.0,0.0,0.0]
        self.redraw = self.display
        #self.config(depth=1, double = 1)

        self.bind_events()

        self.wframe=0
        self.cull=0
        self.smooth=0
        self.color=0
        self.bw_bg=0

        # can be controlled by visualiser controls
        self.show_sphere=1
        self.show_line=1

        self.GLinit()
##         self.cmap=self.make_cmap()
##         self.len_cmap=len(self.cmap)
##         if grid:
##             self.griddens=(self.max-self.min)/(self.len_cmap-1)
##             self.coordsys=1
##             self.surf=1
##             self.mksurf()
##             self.mkcoord()
##         else:	
        self.coordsys=0
        self.surf=0


    def bind_events(self):
        self.bind('<Shift-Button-1>',  self.tkRecordMouse)
        self.bind('<Shift-B1-Motion>', self.xRotate)
        self.bind('<Shift-Button-2>',  self.tkRecordMouse)
        self.bind('<Shift-B2-Motion>', self.yRotate)
        self.bind('<q>', self.quit)

    def GLinit(self):
        glClearColor(0.0, 0.0, 0.0, 0)
        glShadeModel(GL_SMOOTH)
        glPolygonMode(GL_BACK, GL_LINE)

        glLightfv(GL_LIGHT0, GL_POSITION, (0.0, 0.0, 5.0, 0.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.6, 0.6, 0.6))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, (0.0, 1.0, 1.0))

        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_COLOR_MATERIAL)

    def display(self, gl):
        glClearColor(self.cc[0], self.cc[1], self.cc[2], 0)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

        glLightfv(GL_LIGHT0, GL_POSITION, (0.0, 0.0, 5.0, 0.0))
        if self.sphere_list and self.show_sphere:
            glCallList(gl.sphere_list)
        if self.line_list and self.show_line:
            glCallList(gl.line_list)

    def toggle_wire(self):
        if self.wframe:
            self.wframe=0
        else:
            self.wframe=1
        if self.wframe:
            self.setwire(1)
        else:
            self.setwire(0)

    def setscale(self, scale):
        self.grid.scale=scale
        self.min=self.grid.min*scale
        self.max=self.grid.max*scale
        self.griddens=(self.max-self.min)/(self.len_cmap-1)
        self.mksurf()
        if self.show_coord:
            self.mkcoord()

    def setwire(self, opt):
        if opt:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        self.tkRedraw()

    def xRotate(self, event):
        print 'xrot'
        self.activate()
        glRotateScene(0.5, self.xcenter, self.ycenter, 
                self.zcenter, event.x, 0.0, self.xmouse, 0.0)
        self.tkRedraw()
        self.tkRecordMouse(event)

    def yRotate(self, event):
        self.activate()
        glRotateScene(0.5, self.xcenter, self.ycenter, 
                self.zcenter, 0.0, event.y, 0.0, self.ymouse)
        self.tkRedraw()
        self.tkRecordMouse(event)

    def toggle_smooth(self):
        if self.smooth:
            self.smooth=0
        else:
            self.smooth=1

        if self.smooth:
            glShadeModel(GL_SMOOTH)
        else:
            glShadeModel(GL_FLAT)
        self.tkRedraw()

    def toggle_cull(self):
        if self.cull:
            self.cull=0
        else:
            self.cull=1

        if self.cull:
            glEnable(GL_CULL_FACE)
            glCullFace(GL_BACK)
        else:
            glDisable(GL_CULL_FACE)
        self.tkRedraw()

    def toggle_color(self):
        if self.color:
            self.color=0
        else:
            self.color=1

        if self.color:
            glEnable(GL_COLOR_MATERIAL)
            glLightfv(GL_LIGHT0, GL_AMBIENT, (0.6, 0.6, 0.6))
        else:
            glDisable(GL_COLOR_MATERIAL)
            glLightfv(GL_LIGHT0, GL_AMBIENT, (0.8, 0.8, 0.8))
        self.tkRedraw()

    def setbgcolor(self, color):
        self.cc[0]=color[0]/256.0
        self.cc[1]=color[1]/256.0
        self.cc[2]=color[2]/256.0
        self.display(self)


    def setfgcolor(self, color):
        c=[0.0,0.0,0.0]
        c[0]=color[0]/256.0
        c[1]=color[1]/256.0
        c[2]=color[2]/256.0
        glDisable(GL_COLOR_MATERIAL)
        glLightfv(GL_LIGHT0, GL_AMBIENT, (c[0], c[1], c[2]))
        self.display(self)

    def setheightcolor(self):
        if self.color:
            glEnable(GL_COLOR_MATERIAL)
            glLightfv(GL_LIGHT0, GL_AMBIENT, (0.6, 0.6, 0.6))
        self.tkRedraw()

    def drawmol(self,model):
        print 'drawmol'
        self.sphere_list= glGenLists(1)
        glNewList(self.sphere_list, GL_COMPILE)
        print 'making sphere list of ', len(model.atom),' atoms'
        for a in model.atom:
            try:
                z = a.get_number()
            except Exception:
                z = 0
            r,g,b = colours[z]

            glColor3f(r,g,b)
            glPushMatrix()
            x = a.coord[0]
            y = a.coord[1]
            zz = a.coord[2]
            glTranslatef (x, y, zz)
            fac = rcov[z] / 2.0
            glScale(fac,fac,fac)
            glutSolidSphere(0.4, 16, 16)
            glPopMatrix()
        glEndList()

        self.line_list= glGenLists(1)
        glNewList(self.line_list, GL_COMPILE)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        line_count = 0
        for a in model.atom:
            try:
                c = a.conn
            except AttributeError:
                c = []
            for t in c:
                if t.get_index() > a.get_index():

                    line_count = line_count + 1
                    vec = cpv.sub(t.coord, a.coord)
                    mid = cpv.add(a.coord,cpv.scale(vec,0.5))

                    try:
                        z = a.get_number()
                    except Exception:
                        z = 0

                    r,g,b = colours[z]
                    glColor3f(r, g, b)
                    glVertex3f(a.coord[0],a.coord[1],a.coord[2])
                    glVertex3f(mid[0],mid[1],mid[2])

                    try:
                        z = t.get_number()
                    except Exception:
                        z = 0

                    r,g,b = colours[z]
                    glColor3f(r, g, b)
                    glVertex3f(mid[0],mid[1],mid[2])
                    glVertex3f(t.coord[0],t.coord[1],t.coord[2])

        glEnd()
        glEndList()
        print 'made line list of ', line_count, ' lines'


class OpenGLMoleculeVisualiser(MoleculeVisualiser):
    '''Represent a molecule using PyOpenGL
       see visualiser.py for the base class which defines
       the user interactions
    '''

    def __init__(self, root, graph, obj, **kw):
        apply(MoleculeVisualiser.__init__, (self,root,graph,obj), kw)

    def _build(self,selected=None,object=None):
        ''' Create the molecular images'''

        if object:
            if self.debug:
                print 'mol build_ new obj'
            self.molecule = object

        mol=self.molecule
        mol.reindex()
        for a in mol.atom:
            a.conn = []

        for b in mol.bond:
            self.molecule.update_bonds()
            mol.atom[b.index[0]].conn.append(mol.atom[b.index[1]])
            mol.atom[b.index[1]].conn.append(mol.atom[b.index[0]])

        # create line and sphere images
        self.graph.gl.drawmol(mol)

        # set current visibility
        self.graph.gl.show_sphere = self.show_spheres
        self.graph.gl.show_line = self.show_wire
        self.status = BUILT

        self.graph.update()


    def _delete(self):
        self.graph.gl.sphere_list = None
        self.graph.gl.line_list = None
    
    def _hide(self):
        self.graph.gl.show_sphere = 0;
        self.graph.gl.show_lines = 0;

    def _show(self):
        self.graph.gl.show_sphere = self.show_spheres
        self.graph.gl.show_line = self.show_wire


class OpenGLColourMap(ColourMap):
    def _build(self):
        pass

if __name__ == "__main__":

    # For help on why we don't create a new root instance see
    #http://tech.groups.yahoo.com/group/pyopengl/message/121

    Tkinter._default_root.withdraw()
    OpenGLGraph(None).mainloop()
    
