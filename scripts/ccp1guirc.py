#
# This is a sample ccp1guirc file 


############################## User Defaults ######################
#
# The following are default values that you can modify here, or with
# the Edit -> Options dialogue. Any updated values will be saved back
# to the file.
#
# You can also set the locations of the scripts to run the various
# programmes here too.


# The background of the main CCP1GUI window
bg_rgb = (0, 0, 100)

# Change pick_tolerance to determine how close you need to click to
# an atom of it to be selected
pick_tolerance = 0.01

# Set show_selection_by_colour for an atom to change colour when
# it is selected (instead of just displaying a yellow dot).
show_selection_by_colour = 1

conn_scale = 1.0
conn_toler = 0.5
contact_scale = 1.0
contact_toler = 1.5

field_line_width = 1
field_point_size = 2

mol_line_width = 3
mol_point_size = 4

# Sphere rending options
mol_sphere_resolution = 8
mol_sphere_specular = 1.0
mol_sphere_diffuse = 1.0
mol_sphere_specular_power = 5
mol_sphere_ambient = 0.4

# Cylinder rending options
mol_cylinder_resolution = 8
mol_cylinder_specular = 0.7
mol_cylinder_diffuse = 0.7
mol_cylinder_specular_power = 10
mol_cylinder_ambient = 0.4


# Script locations
gamessuk_script = '/home/jmht/codes/GAMESS-UK-7.0/rungamess/rungamess'
#gamessuk_exe = '/home/jmht/test/GAMESS-UK-7.0/bin/gamess'
dalton_script = '/home/jmht/codes/dalton/dalton-2.0/bin/dalton'

###################### End User Defaults #####################

# An example of a new colour map
c = self.colourmap_func()
self.colourmaps.append(c)
c.set_title("Custom map")
c.set_range(-1.0,1.0)
c.set_colours([
    (0 , 255 , 255),
    (0 , 255 , 0),
    (255 , 255 , 0),
    (255 , 0 , 0) ])
c.build()

# Modifying the colouring scheme, this will make The X 
# atoms (Z=0) red and hydrogens (Z=1) green

from objects.periodic import colours

colours[0] = (0.9, 0.2, 0.2)
colours[1] = (0.2, 0.9, 0.2) 

# An example of adding a new menu
self.menuBar.addmenu('Custom', 'Example of a static custom menu')
mbutton = self.menuBar.component('Custom-button')
menu = Menu(mbutton, tearoff=0)
mbutton['menu'] = menu

#
# All code here will execute as part of the __init__ method of the
# main tk-based viewer widget, so any functions that are needed
# from Tk callbacks need to be declared global 
#
# It will often be helpful to pass in the main viewer widget
# instance to the new code, this will be "self" in the namespace
#
global listobjects
def listobjects(gui):
    txt = 'Objects:\n'
    for o in self.data_list:
        myclass = string.split(str(o.__class__),'.')[-1]
        try:
            name = o.name
        except AttributeError:
            name = "NoName"
        try:
            title = o.title
        except AttributeError:
            name = "NoTitle"
        txt = txt + myclass + ', name= ' + name + ', title=' + title + '\n'
    gui.info(txt)

menu.add_command(label='List Objects', underline=0,command=lambda s=self: listobjects(s) )

#
# tools for loading ChemShell hessian eigenmode information from
# the newopt optimiser
#
from interfaces.chemshell import chemshell_z_modes, chemshell_c_modes

global get_chemshell_z_modes
def get_chemshell_z_modes(gui):
    gui.data_list = gui.data_list + chemshell_z_modes()

global get_chemshell_c_modes
def get_chemshell_c_modes(gui):
    gui.data_list = gui.data_list + chemshell_c_modes()

menu.add_command(label='Load ChemShell Zopt Modes', underline=0,command=lambda s=self: get_chemshell_z_modes(s) )
menu.add_command(label='Load ChemShell Copt Modes', underline=0,command=lambda s=self: get_chemshell_c_modes(s) )


global gradient_from_field
def gradient_from_field(dens):
    """Crude finite difference gradient code, OK for pictures but not
    recommended for anything else"""

    ogdens = None
    gdens = Field()
    gdens.dim = copy.deepcopy(dens.dim)
    gdens.origin = copy.deepcopy(dens.origin)
    gdens.axis = copy.deepcopy(dens.axis)

    gdens.ndd = 3
    n = dens.dim[0]
    nn = dens.dim[0]*dens.dim[1]
    axisi = gdens.axis[0] 
    axisj = gdens.axis[1]
    axisk = gdens.axis[2]
    #print axisi
    sx = len(axisi)
    #print len(axisi), axisi*axisi

    si = 0.529177*0.5 * (gdens.dim[0] - 1) / sqrt(axisi*axisi)
    sj = 0.529177*0.5 * (gdens.dim[1] - 1) / sqrt(axisj*axisj)
    sk = 0.529177*0.5 * (gdens.dim[2] - 1) / sqrt(axisk*axisk)
    print 'scale facs',si, sj, sk

    print 'axes'
    print gdens.axis[0]
    print gdens.axis[1]
    print gdens.axis[2]

    # Normalise axis vectors
    axisi = axisi / sqrt(axisi*axisi)
    axisj = axisj / sqrt(axisj*axisj)
    axisk = axisk / sqrt(axisk*axisk)

    gdens.data = []
    gdens.ndd = 3
    gdens.title = 'Gradient of' + dens.title
    gdens.name = gdens.title
    
    for k in range(dens.dim[2]):
        for j in range(dens.dim[1]):
            for i in range(dens.dim[0]):
                vx = 0; vy = 0; vz = 0;
                if i == 0 or i == dens.dim[0]-1:
                    pass
                elif j == 0 or j == dens.dim[1]-1:
                    pass
                elif k == 0 or k == dens.dim[2]-1:
                    pass
                else:
                    # construct gradients along the 3 axis directions
                    vi = (dens.data[ (i+1) + (j  )*n + (k  )*nn ] - \
                          dens.data[ (i-1) + (j  )*n + (k  )*nn ]) * si
                    vi1 = (dens.data[ (i) + (j  )*n + (k  )*nn ] - \
                          dens.data[ (i-1) + (j  )*n + (k  )*nn ]) * si
                    vi2 = (dens.data[ (i+1) + (j  )*n + (k  )*nn ] - \
                          dens.data[ (i) + (j  )*n + (k  )*nn ]) * si
                    vj = (dens.data[ (i  ) + (j+1)*n + (k  )*nn ] - \
                          dens.data[ (i  ) + (j-1)*n + (k  )*nn ]) * sj
                    vj1 = (dens.data[ (i  ) + (j)*n + (k  )*nn ] - \
                          dens.data[ (i  ) + (j-1)*n + (k  )*nn ]) * sj
                    vj2 = (dens.data[ (i  ) + (j+1)*n + (k  )*nn ] - \
                          dens.data[ (i  ) + (j)*n + (k  )*nn ]) * sj
                    vk = (dens.data[ (i  ) + (j  )*n + (k+1)*nn ] - \
                          dens.data[ (i  ) + (j  )*n + (k-1)*nn ]) * sk
                    vk1 = (dens.data[ (i  ) + (j  )*n + (k)*nn ] - \
                          dens.data[ (i  ) + (j  )*n + (k-1)*nn ]) * sk
                    vk2 = (dens.data[ (i  ) + (j  )*n + (k+1)*nn ] - \
                          dens.data[ (i  ) + (j  )*n + (k)*nn ]) * sk

    #                print 'finite diffs i',vi, vi1, vi2
    #                print 'finite diffs j',vj, vj1, vj2
    #                print 'finite diffs k',vk, vk1, vk2

                    # sum components along axis directions (assumes orthogonal axes)
                    vx = vi * axisi[0] + vj * axisj[0] + vk * axisk[0]
                    vy = vi * axisi[1] + vj * axisj[1] + vk * axisk[1]
                    vz = vi * axisi[2] + vj * axisj[2] + vk * axisk[2]
                    d = dens.data[ 1*((i  ) + (j  )*n + (k  )*nn)   ] 
                    if ogdens:
                        vxo = ogdens.data[ 3*((i  ) + (j  )*n + (k  )*nn)    ]
                        vyo = ogdens.data[ 3*((i  ) + (j  )*n + (k  )*nn) + 1]
                        vzo = ogdens.data[ 3*((i  ) + (j  )*n + (k  )*nn) + 2]
                        rx = vi / vxo
                        ry = vj / vyo
                        rz = vk / vzo
                        #print " %16.8e   %12.4e %12.4e %12.4e   %12.4e %12.4e %12.4e %4.2f %4.2f %4.2f" % (d, vx, vy, vz, vxo, vyo, vzo, rx,ry,rz)
                    else:
                        #print " %16.8e    %12.4f %12.4f %12.4f    " % (d, vx, vy, vz)
                        pass

                gdens.data.append(vx)
                gdens.data.append(vy)
                gdens.data.append(vz)

    #print gdens.output_punch()
    return gdens


global vecfield
def vecfield(self):
    print 'executing vecfield'
    print self.data_list
    for o in self.data_list:
        myclass = string.split(str(o.__class__),'.')[-1]
        if myclass == 'Field':
            print 'field',o
            if o.ndd == 1:
                gdens = gradient_from_field(o)
                self.data_list.append(gdens)
                self.info('built vector field ' + gdens.title)

menu.add_command(label='Generate Vector Field ', underline=0,command=lambda s=self: vecfield(s) )

# An example of adding a new dynamic meny
self.menuBar.addmenu('Custom2', 'Example of a dynamic custom menu')

global lister
def lister(obj):
    print 'lister',obj
    obj.list()

global postit
global dynamic_menu
def postit(self):
    print 'postit', self.data_list
    menu = dynamic_menu
    print 'menu', menu

    menu.delete(0,Tkinter.AtEnd())

    if len(self.data_list) == 0:
        menu.add_command(label="No Objects Loaded", state="disabled")
    else:
        for obj in self.data_list:
            # one submenu for each object
            cascade = Menu(menu,tearoff=0)
            txt = obj.name
            cascade.add_command(label="List", underline=0,command=lambda o = obj: lister(o) )
            menu.add_cascade(label=txt, menu=cascade)

    print 'postit done'
    return menu
    
mbutton = self.menuBar.component('Custom2-button')
menu = Menu(mbutton, tearoff=0, postcommand=lambda s=self : postit(s))
print 'dynamic menu is',menu
mbutton['menu'] = menu
dynamic_menu = menu

print 'rc finished'

