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
"""A molecule viewer and editor built with Tkinter
 
The TkMolView class defined here does not actually include the code to
render the molecule into the main window, for this see the derived
classes in files (e.g. vtkgraph.py and openglgraph.py)
"""

if __name__ == "__main__":
    
    # Before we do owt else, make sure we can import the modules that we need
    # and give the user a helpful messsage if we can't (apparently some people
    # don't like reading tracebacks...)
    # If that all works, set the PYTHONPATH variable to include the main GUI
    # directory so that we can find all of our modules
    
    import sys

    # Append the gui directory to the PYTHONPATH
    from paths import gui_path
    sys.path.append(gui_path)

    
    header="""
######################################################################
#                                                                    #
#                  MODULE IMPORT ERROR!                              #
#                                                                    #
######################################################################"""
    
    whereget="""
Alternatively, for information on all of the dependancies for the GUI and
instructions for their installation proceedures, please visit:

http://www.cse.clrc.ac.uk/qcg/ccp1gui/install.shtml

Distributions of the CCP1GUI that contain the relevant Python modules
and pre-compiled vtk libraries are available for download for some
platforms from:

ftp ftp.dl.ac.uk/qcg/ccp1gui
"""

    # Tkinter
    try:
        import Tkinter
    except ImportError:
        print header
        print """
We are sorry but the CCP1GUI cannot run on your system as
you do not appear to have Tkinter installed. For more information
on installing Tkinter, please visit:

http://tkinter.unpythonic.net/wiki/How_20to_20install_20Tkinter"""
        print whereget
        sys.exit(-1)

    # Numeric
    try:
        import Numeric
    except ImportError:
        print header
        print """
We are sorry but the CCP1GUI cannot run on your system as
you do not appear to have Numeric Python installed. For more
information on installing Numeric Python, please visit:

http://sourceforge.net/project/showfiles.php?group_id=1369&package_id=1351"""
        print whereget
        sys.exit(-1)

    # Scientific
    try:
        import Scientific
    except ImportError:
        print header
        print """
We are sorry but the CCP1GUI cannot run on your system as
you do not appear to have Scientific Python installed. For more
information on installing Scientific Python, please visit:

http://starship.python.net/~hinsen/ScientificPython/"""
        print whereget
        sys.exit(-1)

    # Pmw
    try:
        import Pmw
    except ImportError:
        print header
        print """
We are sorry but the CCP1GUI cannot run on your system as
you do not appear to have Python MegaWidgets installed. For more
information on installing Python Megawidgets, please visit:

http://pmw.sourceforge.net/"""
        print whereget
        sys.exit(-1)
        
    # VTK
    try:
        import vtk
    except ImportError:
        print header
        print """
We are sorry but the CCP1GUI cannot run on your system as
you do not appear to have VTK installed. For more
information on installing VTK, please visit:

http://public.kitware.com/VTK/get-software.php"""
        print whereget
        sys.exit(-1)

    print
    print 'Module paths:'
    print '============='
    print 'VTK version',vtk.vtkVersion.GetVTKVersion(),' from ',vtk.__file__ 
    print Numeric.__file__
    print Scientific.__file__
    #print Pmw.__file__
    print

import sys,os,stat
from math import fabs, cos, sin, pi, sqrt, floor
from string import strip, split, atof
from tkFileDialog import *
from tkSimpleDialog import *
from tkColorChooser import *
from SimpleDialog import SimpleDialog

import time
from generic.graph import *
import copy
import chempy
from chempy import cpv, Atom, Bond

import viewer.help
from viewer.debug import deb_setwidget,deb
from viewer.initialisetk import initialiseTk
from viewer.shell import env, mypyshell
from viewer.paths import gui_path, python_path, user_path
from viewer.paths import paths

from interfaces.calc import *
from interfaces.calced import *
from interfaces.gamessuk import *
from interfaces.molpro import *
from interfaces.chemshell import *
from interfaces.dl_poly import *
from interfaces.mopac import *
from interfaces.mndo import *
from interfaces.dalton import *
from interfaces.charmm import *

from interfaces.gamessoutputreader import *
from interfaces.cubereader import *
from interfaces.filepunch import *

import objects
from objects.zme            import *
from objects.periodic       import sym2no, z_to_el, name_to_element


from slavethread import *
from jobmanager.jobeditor import *
from toolpanel import *

# dictionary to hold the variables that can be set in the ccp1guirc file
global rc_vars 
rc_vars = {}
rc_vars['conn_scale'] = 1.0
rc_vars['conn_toler']   = 0.5
rc_vars['contact_scale'] = 1.0
rc_vars['contact_toler']   = 1.5
rc_vars['bg_rgb'] = (0,0,0)
rc_vars['pick_tolerance'] = 0.01
rc_vars['show_selection_by_colour'] = 1
rc_vars['field_line_width']  =  1
rc_vars['field_point_size']  =  2
# Molecule variables
rc_vars['mol_line_width']  =  3
rc_vars['mol_point_size']  =  4
rc_vars['mol_sphere_resolution'] = 8
rc_vars['mol_sphere_specular'] = 1.0
rc_vars['mol_sphere_diffuse'] = 1.0
rc_vars['mol_sphere_ambient'] = 0.4
rc_vars['mol_sphere_specular_power'] = 5
rc_vars['mol_cylinder_resolution'] = 8
rc_vars['mol_cylinder_specular'] = 0.7
rc_vars['mol_cylinder_diffuse'] = 0.7
rc_vars['mol_cylinder_ambient'] = 0.4
rc_vars['mol_cylinder_specular_power'] = 10
# Script locations
rc_vars['gamessuk_exe'] = None
rc_vars['gamessuk_script'] = None
rc_vars['molden_exe'] = None
rc_vars['dalton_script'] = None

def set_rc_var( name, value ):
    """
       Set an rc_variable.
       name: the name of the variable in the rc_vars dictionary
       value: what the variable should be set to

       We return 1 if name is not in the dictionary
    """
    global rc_vars
    
    if rc_vars.has_key( name ):
        rc_vars[name] = value
        return None
    else:
        print "Error in set_rc_var! rc_vars has no key %s" % name
        return 1


class TkMolView(Pmw.MegaToplevel):
    """The Tk-based Widget"""

    def __init__(self, parent, title=''):

        Pmw.MegaToplevel.__init__(self) 

        self.title('CCP1GUI'+25*' '+title)
        self.iconname('CCP1GUI')

        # This is to provide a handle for the shell window to access
        # variables from this class
        env.tkmol = self
        
        initialiseTk(parent)
        self.parent = parent

        # TEMP HACK
        self.master = self.interior()
        
        #Bind F1 to open a help menu and pass in error widget
        self.master.bind_all('<F1>', lambda event : viewer.help.helpall(event))
        # Associate helpfile with widget
        viewer.help.sethelp(self.master,'Introduction')
        
        # We only want one instance of the allmoleculevisualiser 
        self.allmolecule_visualiser = None
        # We only want one scene visualiser
        self.ani_image_widget = None

        self.__createBalloon()
        
        # create the menubar
        self.menuBar = self.createcomponent('menubar', (), None,
                                            Pmw.MenuBar,
                                            (self._hull,),
                                            # hull_relief=RAISED,
                                            # hull_borderwidth=0,
                                            #balloon=self.__balloon)
                                            balloon=self.balloon)

        self.menuBar.pack(fill=X)
        self.menuBar.addmenu('Help', 'Documentation', side='right')
        self.menuBar.addmenu('File', 'File Input/Output')
        self.menuBar.addmenu('Edit', 'Editing molecules and other tools')
        self.menuBar.addmenu('Views', 'Create and modify graphical representation')
        self.menuBar.addmenu('Info', 'Information listings for the loaded objects')
        self.menuBar.addmenu('Compute', 'Call computational chemistry codes')
        #self.menuBar.addmenu('Debug', 'Switch various debug options on/off')
        self.menuBar.addmenu('Shell', 'Access Python Shell \n(see info and debug output, \nand enter python commands)')

        #self.menuBar.addmenu('Edit', 'Atom and Variable')
        #self.menuBar.addmenu('Convert', 'Z-matrix/cartesian conversion')
        #self.menuBar.addmenu('Calculate', 'Generate Cartesians')

        # Build Menus
        #self.mBar = Frame(self.interior(),relief=RAISED, borderwidth=2)
        #self.mBar.pack(side='top', fill=X)
        self.FileMenu()
        self.EditMenu()
        self.InfoMenu()
        self.ViewMenu()
        #self.VisualiseMenu()
        self.ComputeMenu()
        #self.DebugMenu()
        self.ShellMenu()
        self.HelpMenu()

        # Build Dialogs
        self.build_msg_dialog()
        self.build_query_dialog()
        self.build_vis_dialog()
        self.build_data_dialog()
        self.build_help_dialog()
        self.build_watch_dialog()
        self.build_extend_dialog()
        self.build_distance_dialog()
        self.build_distance_dialog(include_xyz=1)
        self.build_command_window()
        #self.build_save_image_dialog()
        self.build_save_movie_dialog()

        #Pass viewer object to the help.py module
        viewer.help.get_tkmolview(self)
        
        self.vis_list = []
        self.data_list = []

        # dictionary for mapping structures to images
        # one->many, each entry is a list
        self.vis_dict = {}

        # dictionary for working out which structures are being
        # actively edited (see vtkgraph.py)
        # one->one , each entry is a zme instance
        self.zme_dict = {}
        
        # dictionary for load/save
        self.file_dict = {}
        
        # dictionary for mapping structures to CalcEd instances
        # one->many, each entry is a list
        self.calced_dict = {}
        
        # default colourmaps
        self.define_colourmaps()

        self.undo_stack = []
        #
        # This group of options can be set by the user from the 
        # Options tool
        #

        self.conn_scale = 1.0
        self.conn_toler   = 0.5
        self.contact_scale = 1.0
        self.contact_toler   = 1.5
        self.bg_rgb      =  (0,0,0)

        ## this may have a different meaning in the derived class
        try:
            itest = self.pick_tolerance
        except AttributeError:
            self.pick_tolerance = -999

        self.field_line_width  =  1
        self.field_point_size  =  2

        self.mol_line_width  =  3
        self.mol_point_size  =  4

        self.mol_sphere_resolution = 8
        self.mol_sphere_specular = 1.0
        self.mol_sphere_ambient = 0.4
        self.mol_sphere_diffuse = 1.0       
        self.mol_sphere_specular_power = 5

        self.mol_cylinder_resolution = 8
        self.mol_cylinder_ambient = 0.4
        self.mol_cylinder_specular = 0.7
        self.mol_cylinder_diffuse = 0.7
        self.mol_cylinder_specular_power = 10

        self.debug = 0
        self.debug_callbacks = 0
        self.debug_selection = 0
        self.enable_undo = 1
        
        self.user_directory = None

        # animation controls
        self.build_ani_toolbar()
        self.pack_ani_toolbar()
        
        # list of images from last animation frame
        #self.oldvisl = []

        # Set any defaults form the ccp1guirc file & any user-defined functions
        self.read_ccp1guirc()
        
        self.build_options_dialog()
        self.toolwidget = EditingToolsWidget(self.master,
                                             command=self.handle_edits)
        self.toolwidget.userdeletefunc(lambda s=self: s.toolwidget.withdraw())
        self.toolwidget.withdraw()

        # Create a text widget for the debug output
        self.debug_window = Pmw.MegaToplevel(parent)
        self.debug_window.title('CCP1 GUI Debug Output')
        fixedFont = Pmw.logicalfont('Courier',size=10)
        txt = Pmw.ScrolledText(
            self.debug_window.interior(),
            borderframe = 1)
        txt.pack()
        txt.configure(text_font = fixedFont)
        self.debug_window.text = txt

        #Associated widget with its help file
        viewer.help.sethelp(self.debug_window,'Debug Window')
        
        self.debug_window.withdraw()
        self.debug_window.userdeletefunc(lambda s=self: s.debug_window.withdraw())

        self.job_manager = JobManager()
        self.job_editor = JobEditor(parent,self.job_manager)
        self.job_editor.userdeletefunc(lambda s=self: s.job_editor.withdraw())
        self.job_editor.withdraw()

        # these are used for on-the-fly minimisations
        self.clean_calced = {}
        ##self.start_clean_calceds()

        self.window2d = Pmw.MegaToplevel(parent)
        self.window2d.title('CCP1 GUI 2D')
        self.window2d.userdeletefunc(lambda s=self: s.window2d.withdraw())
        self.window2d.withdraw()

        self.mBar2d = Frame(self.window2d.interior(),relief=RAISED, borderwidth=2)
        self.mBar2d.pack(side='top', fill=X)
        self.FileMenu2d()

        # Paul debug
        self.job_editor.mainobj = self

        #print 'Parent Geom', parent.geometry()
        #print 'Master Geom', self.master.geometry()

        self.new_molecule_index = 0
        # A list of functions to be called whenever editing operations
        # are performed in the

        # Structure is a dictionary keyed on the ID of the object
        # that has changed. Each element is a list of tuples
        # each tuple is a character string to identify the callback and
        # a function to call when that object has been changed

        # If function is a method of another object, that object must
        # remove the callback on deletion
        #   - by convention this is handled by the on_exit= argument
        self.editing_callbacks = {}

    def read_ccp1guirc(self):
        """Process the ccp1guirc file:
           Execute the file to execute any of the users python code, and then
           check for any variables that are set in the file. These are stored
           in the rc_vars dictionary. Any variables that are attributes of self
           are set.
        """
        global rc_vars

        # Need to append all variables that we are going to change to locals
        # in order for them to be in scope when execfile executes
        #for var_name in rc_vars.keys():
        #    locals()[var_name] = rc_vars[var_name]

        # Load user Defaults if present
        if sys.platform[:3] == 'win':
            rcfile = os.path.expandvars('$USERPROFILE\ccp1guirc.py')
        else:
            rcfile = os.path.expandvars('$HOME/ccp1guirc.py')
            
        if not os.path.isfile( rcfile ):
            # No ccp1guirc file so we can return
            print "No user preferences file: %s found" % rcfile
            return
        
        print "Executing ccp1guirc file %s" % rcfile
        try:
            execfile( rcfile )
        except Exception,e:
                print "Error reading cco1guirc file: %s" % rcfile
                print e
                
        # Now trundle through the variables in rc_vars, seeing if any of them are in scope
        # as local variables. If they are we place the value in rc_vars and try and set the
        # variable value if they are attributes of self
        
        for var_name in rc_vars.keys():
            gotvar = None
            exeline = 'tmp = '+var_name
            print 
            try:
                exec(exeline)
                #print "%s from ccp1guirc is: %s" % (var_name, tmp)
                # Need to check if this is a string. Under windows a path could contain the
                # \b character (backspace). If the string is interpreted as a normal string
                # this causes the \b and the preceding character to be deleted. We therefore
                # need to convert the variable to a raw string.
                if type(tmp) is str:
                    tmp = self.raw( tmp )
                    
                rc_vars[var_name] = tmp
                gotvar = 1
            except NameError:
                #print "%s is not in ccp1guirc file" % var_name
                pass
            
            if gotvar:
                # Now try and set this if it is an attribute of main
                # and set it if it is
                try:
                    exeline3 = "self."+var_name+" = "+str(rc_vars[var_name])
                    exec(exeline3)
                    #print "Set self."+var_name+" to "+str(rc_vars[var_name])
                except:
                    pass
                    #print "%s is not a self var" % var_name

        # write out
        #print "rc_vars are:"
        #for key in rc_vars.keys():
        #    print "%s : %s" % (key,rc_vars[key])
                    

    def raw(self, text):
        """Returns a raw string representation of text
           Credit where it's due: this function was written by Brett Cannon and was
           found on the Python Cookbook website:
           http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/65211

        """

        escape_dict={'\a':r'\a',
               '\b':r'\b',
               '\c':r'\c',
               '\f':r'\f',
               '\n':r'\n',
               '\r':r'\r',
               '\t':r'\t',
               '\v':r'\v',
               '\'':r'\'',
               '\"':r'\"',
               '\0':r'\0',
               '\1':r'\1',
               '\2':r'\2',
               '\3':r'\3',
               '\4':r'\4',
               '\5':r'\5',
               '\6':r'\6',
               '\7':r'\7',
               '\8':r'\8',
               '\9':r'\9'}

        new_string=''
        for char in text:
            try: new_string+=escape_dict[char]
            except KeyError: new_string+=char
        return new_string

    def write_ccp1guirc(self):
        """ Write out the current state of the rc_vars to file
        """

        print "writing ccp1guirc file"
        global rc_vars
        
        # find the ccp1guirc file
        if sys.platform[:3] == 'win':
            rc_filename = os.path.expandvars('$USERPROFILE\ccp1guirc.py')
        else:
            rc_filename = os.path.expandvars('$HOME/ccp1guirc.py')

        if not os.path.isfile( rc_filename ):
            # No ccp1guirc file found, so just dump out the dictionary to a new ccp1guirc file
            try:
                rc_file = open( rc_filename, 'w' ) # Open File in write mode
            except IOError,e:
                print "Cant create user rc file. I give up..."

            rc_file.write("# This ccp1guirc file has been created by the CCP1GUI as no\n")
            rc_file.write("# user file could be found\n#\n#\n")
            for name in rc_vars.keys():
                rc_file.write( "%s = %s\n" % (name,str(rc_vars[name])) )

            # Have dumped dictionary so quit here
            return

        # Read the file into a buffer
        try:
            rc_file = open( rc_filename, 'r' )
            rc_buff = rc_file.readlines()
            rc_file.close()
        except Error,e:
            print "Error reading ccp1guirc file!"
            print e
            return

        # For each line of the file, if a variable appears at the start of the line
        # we replace the old value with the one from the rc_vars dictionary
        count = 0
        for line in rc_buff:
            for var_name in rc_vars.keys():
                re_str = '^'+var_name+' *='
                if re.compile( re_str ).match( line ):
                    # replace that line in the buffer with the new value
                    if type(rc_vars[var_name]) is str:
                        rc_buff[ count ] = "%s = \'%s\'\n" % (var_name, str(rc_vars[var_name]) )
                    else:
                        rc_buff[ count ] = "%s = %s\n" % (var_name, str(rc_vars[var_name]) )
            count += 1

        # Write out the ammended file
        try:
            rc_file = open( rc_filename, 'w')
            for line in rc_buff:
                rc_file.write( line )
        except Error,e:
            print "Can't write rc_file %s " % rc_filename
            print "Error is:"
            print e

    def __createBalloon(self):
        # Create the balloon help manager for the frame.
        # Create the manager for the balloon help
        #self.__balloon = self.createcomponent('balloon', (), None,
        #                                      Pmw.Balloon, (self._hull,))
        self.balloon = self.createcomponent('balloon', (), None,
                                              Pmw.Balloon, (self._hull,))

    def update(self):
        """Update the screen """
        print 'render should be overloaded'

#    def reset(self):
#        print 'reset'

    def build_ani_toolbar(self):

        bar = Frame(self.interior(),relief=SUNKEN, borderwidth=2)
        #bar.pack(side='bottom', fill=X)
        self.ani_toolbar = bar
        #b=Button(bar, text='Reset', command=self.reset)
        b=Button(bar, text='Reset', command=self.ani_reset)
        b.pack(side='left')
        b=Button(bar, text='|<', command=self.ani_rew)
        b.pack(side='left')
        b=Button(bar, text='<', command=self.ani_bak)
        b.pack(side='left')
        b=Button(bar, text='Stop', command=self.ani_stop)
        b.pack(side='left')
        b=Button(bar, text='Play', command=self.ani_play)
        b.pack(side='left')
        b=Button(bar, text='>', command=self.ani_fwd)
        b.pack(side='left')
        b=Button(bar, text='>|', command=self.ani_end)
        b.pack(side='left')
        #b=Button(bar, text='Hide', command=self.hide_ani_toolbar)
        #b.pack(side='left')
        b=Button(bar, text='Select', command=self.select_ani_images )
        b.pack(side='left')
        b=Button(bar, text='Save Images', command=self.ask_save_movie )
        b.pack(side='left')

    def pack_ani_toolbar(self):
        """ Pack the toolbar and reset it
        """
        self.ani_toolbar.pack(side='bottom')
        self.ani_reset()
        
    def hide_ani_toolbar(self):
        self.ani_toolbar.forget()

    def FileMenu(self):
        mbutton = self.menuBar.component('File-button')
        ##Menubutton(self.mBar, text='File', underline=0)
        ##mbutton.pack(side=LEFT, padx="2m")
        menu = Menu(mbutton, tearoff=0)

        menu.add_command(label='Open ', underline=0, 
                command=self.ask_load_from_file)

        menu.add_command(label='Save As', underline=0, 
               command=self.ask_save_to_file)

        menu.add_command(label='New Molecule', underline=0, 
                         command = lambda s=self: s.new_coords() )

        menu.add_separator()

        menu.add_command(label='Save Image', underline=0, 
               command=self.ask_save_image3d)
        
        # menu.add_separator()
        # menu.add_command(label='Watch ', underline=0, 
        #        command=self.ask_watch_file)

        menu.add_separator()
        menu.add_command(label='Open Calc',underline=0,
                         command = lambda s=self: s.open_calc() )

        # menu.add_command(label='Hardcopy', underline=0, 
        # command=self.hardcopy)

        menu.add_separator()
        menu.add_command(label='Quit', underline=0, 
                command=self.myquit)

        mbutton['menu'] = menu
        return mbutton

    def OldFileMenu(self):
        mbutton = Menubutton(self.mBar, text='File', underline=0)
        mbutton.pack(side=LEFT, padx="2m")
        menu = Menu(mbutton, tearoff=0)

        menu.add_command(label='Open ', underline=0, 
                command=self.ask_load_from_file)

        menu.add_command(label='Save As', underline=0, 
               command=self.save_to_file)

        menu.add_command(label='New Molecule', underline=0, 
                         command = lambda s=self: s.new_coords() )

        menu.add_separator()

        menu.add_command(label='Save Image', underline=0, 
               command=self.save_image)
        
        # menu.add_separator()
        # menu.add_command(label='Watch ', underline=0, 
        #        command=self.ask_watch_file)

        menu.add_separator()
        menu.add_command(label='Open Calc',underline=0,
                         command = lambda s=self: s.open_calc() )

        # menu.add_command(label='Hardcopy', underline=0, 
        # command=self.hardcopy)

        menu.add_separator()
        menu.add_command(label='Quit', underline=0, 
                command=self.myquit)

        mbutton['menu'] = menu
        return mbutton


    def FileMenu2d(self):
        mbutton = Menubutton(self.mBar2d, text='File', underline=0)
        mbutton.pack(side=LEFT, padx="2m")
        menu = Menu(mbutton, tearoff=0)
        menu.add_command(label='Save Image(2d)', underline=0, 
               command=self.ask_save_image2d)
        mbutton['menu'] = menu
        return mbutton

    def destroy(self):
        """invoked when window is closed by windowmanager"""
        self.myquit()
        
    def myquit(self):
        """Called on user-requested exit
            This is overloaded in VTK case to destroy VTK parts first
        """
        self.quit()

    def EditMenu(self):
        #mbutton = Menubutton(self.mBar, text='Edit', underline=0)
        #mbutton.pack(side=LEFT, padx="2m")
        mbutton = self.menuBar.component('Edit-button')
        menu = Menu(mbutton, tearoff=0, postcommand=self.post_edit)
        self.edit_menu=menu
        mbutton['menu'] = menu
        return mbutton

    def InfoMenu(self):
        mbutton = self.menuBar.component('Info-button')
        menu = Menu(mbutton, tearoff=0, postcommand=self.post_info)
        self.info_menu=menu
        mbutton['menu'] = menu
        return mbutton



    def build_save_image_dialog(self):
        """Build up the widgets that consitute the save image dialog box with the
           slider to specify the quality of the jpeg.
        """

        from FileDialog import SaveFileDialog
        self.save_image_dialog=SaveFileDialog(self.master)
        myframe=Frame(self.save_image_dialog.top,background='blue')
        self.save_image_dialog.midframe.forget()
        self.save_image_dialog.botframe.forget()
        self.save_image_dialog.selection.forget()
        myframe.pack(side='bottom',fill='x',expand='yes')
        self.save_image_dialog.midframe.pack(expand=YES, fill=BOTH)
        self.save_image_dialog.botframe.pack(side=BOTTOM, fill=X)
        self.save_image_dialog.selection.pack(side=BOTTOM, fill=X)

        self.image_format = Tkinter.StringVar( )
        self.image_format.set("jpg")

        format_frame = Tkinter.Frame( myframe )
        
        jpegradio = Tkinter.Radiobutton( format_frame,
                                        text = "jpg", variable = self.image_format, value = "jpg",
                                              command = self.select_image_format )
        pngradio = Tkinter.Radiobutton( format_frame,
                                        text = "png", variable = self.image_format, value = "png",
                                        command = self.select_image_format )

        self.jpeg_res_frame = Tkinter.Frame( myframe )
        
#        self.jpeg_res_widget = Tkinter.Scale( self.jpeg_res_frame ,
#                                           label = 'Jpeg quality',
#                                           orient = 'horizontal',
#                                           tickinterval = '10',
#                                           length = '400',
#                                           from_ = 0, to_ = 100 )
        format_frame.pack()
        jpegradio.select()
        jpegradio.pack( side = 'left' )
        pngradio.pack( side = 'left' )
#        self.jpeg_res_frame.pack()
#        self.jpeg_res_widget.set( '95' ) # This seems to be the default (see: VTK/IO/vtkJPEGWriter.cxx )
#        self.jpeg_res_widget.pack()


    def build_save_image_dialog_jens(self):
        """Build up the widgets that consitute the save image dialog box with the
           slider to specify the quality of the jpeg.
        """

        self.image_filename = None
        self.save_image_dialog = Pmw.Dialog( self.master,
                                             buttons = ( 'Save', 'Close', 'Browse...' ),
                                             title = 'Save window as image',
                                             command = self.save_image3d )
        format_frame = Tkinter.Frame( self.save_image_dialog.interior() )

        self.image_format = Tkinter.StringVar( )
        self.image_format.set("jpg")
        jpegradio = Tkinter.Radiobutton( format_frame,
                                        text = "jpg", variable = self.image_format, value = "jpg",
                                              command = self.select_image_format )
        pngradio = Tkinter.Radiobutton( format_frame,
                                        text = "png", variable = self.image_format, value = "png",
                                        command = self.select_image_format )

        self.jpeg_res_frame = Tkinter.Frame( self.save_image_dialog.interior() )
        
        self.jpeg_res_widget = Tkinter.Scale( self.jpeg_res_frame ,
                                           label = 'Jpeg quality',
                                           orient = 'horizontal',
                                           tickinterval = '10',
                                           length = '400',
                                           from_ = 0, to_ = 100 )
        
        format_frame.pack()
        jpegradio.select()
        jpegradio.pack( side = 'left' )
        pngradio.pack( side = 'left' )
        self.jpeg_res_frame.pack()
        self.jpeg_res_widget.set( '95' ) # This seems to be the default (see: VTK/IO/vtkJPEGWriter.cxx )
        self.jpeg_res_widget.pack()
        self.save_image_dialog.withdraw()

    def select_image_format( self ):
        """ Select between jpeg and png image formats - if jpg
            is selected display the widget to specify the quality
        """
        format = self.image_format.get()
        if format == "jpg":
            self.jpeg_res_frame.pack()
        elif format == "png":
            self.jpeg_res_frame.forget()
        else:
            print "no image string :%s" % format
            
    def build_save_movie_dialog(self):
        """Build up the widgets that consitute the save image dialog box with the
           slider to specify the quality of the jpeg.
        """

        from viewer.paths import gui_path
        self.movie_directory = gui_path
        
        self.save_movie_dialog = Pmw.Dialog( self.master,
                                             buttons = ( 'Save', 'Close', 'Browse...' ),
                                             title = 'Save Movie',
                                             command = self.save_movie_buttonclick )
        format_frame = Tkinter.Frame( self.save_movie_dialog.interior() )

        self.movie_format = Tkinter.StringVar( )
        self.movie_format.set("jpg")
        jpegradio = Tkinter.Radiobutton( format_frame,
                                        text = "jpg", variable = self.movie_format, value = "jpg",
                                              command = self.select_movie_format )
        pngradio = Tkinter.Radiobutton( format_frame,
                                        text = "png", variable = self.movie_format, value = "png",
                                        command = self.select_movie_format )

        self.movie_jpeg_res_frame = Tkinter.Frame( self.save_movie_dialog.interior() )
        
        self.movie_jpeg_res_widget = Tkinter.Scale( self.movie_jpeg_res_frame ,
                                           label = 'Jpeg quality',
                                           orient = 'horizontal',
                                           tickinterval = '10',
                                           length = '400',
                                           from_ = 0, to_ = 100 )
        
        format_frame.pack()
        jpegradio.select()
        jpegradio.pack( side = 'left' )
        pngradio.pack( side = 'left' )
        self.movie_jpeg_res_frame.pack()
        self.movie_jpeg_res_widget.set( '95' ) # This seems to be the default (see: VTK/IO/vtkJPEGWriter.cxx )
        self.movie_jpeg_res_widget.pack()
        self.save_movie_dialog.withdraw()

    def select_movie_format( self ):
        """ Select between jpeg and png image formats - if jpg
            is selected display the widget to specify the quality
        """
        format = self.movie_format.get()
        if format == "jpg":
            self.movie_jpeg_res_frame.pack()
        elif format == "png":
            self.movie_jpeg_res_frame.forget()
        else:
            print "no image string :%s" % format

    def save_movie_buttonclick(self, result ):
        """ Process the result of clicking one of the buttons in the save_movie_dialog
        """
        print "save_movie_buttonclick ", result

        if result == "Close":
            self.save_movie_dialog.withdraw()
        elif result == "Browse...":
            self.browse_movie_directory()
        elif result == "Save":
            format = self.movie_format.get()
            self.save_movie( format )
            self.save_movie_dialog.withdraw()
        else:
            self.save_movie_dialog.withdraw()
        
    def browse_movie_directory(self):
        # askdirectory() cant create new directories so use asksaveasfilename is used instead
        # and the filename  is discarded - also fixes problem with no askdirectory in Python2.1
        olddir = self.movie_directory
        dummyfile="use_this_directory"
        path=tkFileDialog.asksaveasfilename(initialfile=dummyfile, initialdir=olddir)
        #path=tkFileDialog.askdirectory(initialdir=olddir)
        if len(path) == 0:
            # User didn't select anything
            pass
        else:
            self.movie_directory = os.path.dirname( path )

    def save_movie(self, format ):
        """
        """
        print "format is ",format
        directory = self.movie_directory
        print "directory is ",directory

        # or should we ask?
        if len( self.ani_list ) == 0 :
            self.ani_reset()

        # hide everything
        self.showall(0)

        # Loop over the images, creating a unique name and then show the image,
        # take a snapshot and save this as a jpeg with the unique name and
        # then hide the image
        image_file_list = []
        i = 0
        for vis in self.ani_list:
            title = vis.title
            # Need to remove ":" from title & replace spaces with underscores
            title = string.replace( title, ":", "")
            title_list = string.split( title )
            title = string.join( title_list, "_" )
            myfile = directory + os.sep + title + "." + str( i ) + "." + format
            image_file_list.append( myfile )
            vis.Show()
            if format == "jpg":
                quality = self.movie_jpeg_res_widget.get()
                self.save_image(myfile, format=format, quality=quality )
            elif format == "png":
                self.save_image(myfile, format=format )
            else:
                print "Unrecognised image format in save_movie"
            vis.Hide()
            i += 1
            
        return
        
    def ask_save_image3d(self):
        #need code here to choose a sensible initial file
        self.build_save_image_dialog()
        self.image_filename = self.save_image_dialog.go(".","*.*","out.jpg")
        format = self.image_format.get()
        print 'filename',self.image_filename
        if format == "png":
            self.save_image( self.image_filename, format = format )
        elif format == "jpg":
#            quality = self.jpeg_res_widget.get()
            quality = 95
            self.save_image( self.image_filename, format = format, quality=quality )
        else:
            print "ERROR getting format in save_image3d"
        self.image_filename = None

    def save_image3d( self, result ):
        """Save image from main window to a JPEG file"""

        format = self.image_format.get()
        
        if ( result == 'Save' ):
            if self.image_filename == None:
                name = 'out.'+format
                self.image_filename = paths['user'] + os.sep + name

            print 'filename',self.image_filename
            if format == "png":
                self.save_image( self.image_filename, format = format )
            elif format == "jpg":
                quality = self.jpeg_res_widget.get()
                self.save_image( self.image_filename, format = format, quality=quality )
            else:
                print "ERROR getting format in save_image3d"

            self.image_filename = None
            self.save_image_dialog.withdraw()
            
        elif ( result == 'Close' ):
            self.save_image_dialog.withdraw()

        elif( result == 'Browse...' ):
            if format == "png":
                self.image_filename = tkFileDialog.asksaveasfilename(
                    initialfile = paths['user'] + self.image_filename,
                    filetypes=[("PNG","*.png")])
                print "png self.image_filename ",self.image_filename
            else:
                self.image_filename = tkFileDialog.asksaveasfilename(
                    initialfile = self.image_filename,
                    filetypes=[("JPEG","*.jpg")])
                print "jpeg self.image_filename ",self.image_filename
            

    def ask_save_image2d(self):
        """Save image from main window to a JPEG file"""
        name = 'out2d.jpg'
        ofile = tkFileDialog.asksaveasfilename(
            initialfile = name,
            filetypes=[("JPEG","*.jpg")])
        if len(ofile):
            self.save_image2d(ofile)

    def loaded_mols(self):
        """Return a list of all molecules currently loaded"""
        mols = []
        for o in self.data_list:
            t1 = string.split(str(o.__class__),'.')
            myclass = t1[len(t1)-1]
            if myclass == 'Indexed' or myclass == 'Zmatrix':
                mols.append(o)
        return mols

    def loaded_fields(self):
        """Return a list of all field objects currently loaded"""
        fields = []
        for o in self.data_list:
            t1 = string.split(str(o.__class__),'.')
            myclass = t1[len(t1)-1]
            if myclass == 'Field':
                fields.append(o)
        return fields
        
    def post_edit(self):
        menu = self.edit_menu
        menu.delete(0,Tkinter.AtEnd())
        mols=self.loaded_mols()
        fields=self.loaded_fields()
        if self.enable_undo:
            if len(self.undo_stack):
                menu.add_command(label="Undo", underline=0,command=self.undo)
            else:
                menu.add_command(label="Undo", underline=0,command=self.undo,state="disabled")
            menu.add_separator()
        self.add_mol_cmd(menu,mols,"Edit Coords",self.edit_coords)
        self.add_field_cmd(menu,fields,"Edit Grid",self.edit_grid)
        self.add_mol_cmd(menu,mols,"Connect",self.connect_model,all=1)
        self.add_mol_cmd(menu,mols,"Extend",self.extend_model)

        menu.add_separator()
        self.add_mol_cmd(menu,self.data_list,"Delete",self.delete_obj,all=1)
        menu.add_separator()

        # Simple molecular editing functions
        #self.add_mol_cmd(menu,mols,"Rename Molecule",self.rename_mol)

        menu.add_command(label='Editing Tools', underline=0, 
                command=lambda x=self: x.toolwidget.show())

        menu.add_separator()

        menu.add_command(label='Select All', underline=0, 
                command=lambda x=self: x.select_all())

        menu.add_command(label="Select connected",command=self.select_connected)

        menu.add_command(label="Select by bonds",command=self.select_by_bonds)

        menu.add_command(label="Select (dist to sel) ",command=self.select_by_distance_to_selected)

        menu.add_command(label="Select (dist to point)",command=self.select_by_distance_to_point)

        menu.add_command(label="Select (dist to point) + trim models",command=self.select_by_distance_to_point_and_trim)

        menu.add_separator()

        menu.add_command(label="Delete Selected Atoms",command=self.delete_atom)
        menu.add_command(label="Delete Unselected Atoms",command=self.delete_unselected)

        menu.add_separator()

        menu.add_command(label='Options', underline=0, 
                command=lambda x=self: x.open_options_dialog())

    def post_info(self):
        mols=self.loaded_mols()
        menu = self.info_menu
        menu.delete(0,Tkinter.AtEnd())

        self.add_mol_cmd(menu,mols,"Coordinate List",self.list_model)
        self.add_mol_cmd(menu,mols,"Bond Lengths and Angles",self.list_geom)
        self.add_mol_cmd(menu,mols,"Contacts to Selected Atoms",self.list_contacts)

    def handle_edits(self,operation,argument):
        """Handler for operations requested e.g. from the Editing Tools
        panel
        """
        if operation == 'Del Atom':
            self.delete_atom()
        elif operation == 'Del Bond':
            self.delete_bond()
        elif operation == 'Add Bond':
            self.add_bond()
        elif operation == 'All X->H':
            self.xtoh()
        elif operation == 'element':
            self.setz(argument)
        elif operation == 'hybridisation':
            self.sethyb(argument)
        elif operation == 'clean':
            self.clean(argument)
        elif operation == 'cleanopts':
            self.clean_opts(argument)
        elif operation == 'fragment':
            self.addfrag(argument)
        elif operation == 'Distance':
            return self.measure_dist()
        elif operation == 'Angle':
            return self.measure_angle()
        elif operation == 'Torsion':
            return self.measure_torsion()
        else:
            self.error('Unimplemented Edit: '+operation+' '+argument)


    def delete_atom(self):
        sel = self.sel()
        dsel = sel.get()
        if self.debug:
            deb('delete_atom'+str(dsel))
        edited = []
        undo = []
        # Undo: need to restructure into loops by molecule
        # and have a single set of undos per mol
        mols = sel.get_mols()
        for mol in mols:
            # Undo code
            # convert connectivity table to bond list to simplify storage
            mol.update_bonds()
            old_list = copy.copy(mol.atom)
            old_bond = copy.deepcopy(mol.bond)
            print 'check bonds saved'
            for b in old_bond:
                print b.index
            undo.append(lambda m = mol, oa = old_list: m.apply_atom_list(oa))
            undo.append(lambda m = mol, ob = old_bond: m.apply_connect(ob))
            undo.append(lambda m = mol: m.reindex())
            undo.append(lambda m = mol: m.update_conn())
            # End of undo code

            list = []
            for a in sel.get_by_mol(mol):
                list.append(a.get_index())
            mol.delete_list(list)
            sel.clean_deleted(mol)

            self.update_from_object(mol)
            undo.append(lambda m = mol, s = self: s.update_from_object(m))

        self.undo_stack.append(undo)

    def delete_unselected(self):
        print 'phase 1'
        sel = self.sel()
        dsel = sel.get()
        if self.debug:
            deb('delete_unselected'+str(dsel))
        edited = []
        selats = {}
        selected_mols = []
        for mol,atom in dsel:
            k = id(mol)
            if mol in selected_mols:
                selats[k].append(atom)
            else:
                selected_mols.append(mol)
                selats[k] = [atom]

        print 'phase 2'
        sel.clear()
        for mol in selected_mols:
            k = id(mol)            
            
            oldatom = mol.atom
            for atom in mol.atom:
                atom.tempflag=0
            mol.atom = []

            print 'building new atom list'
            #print 'Selats',selats[k]
            for atom in selats[k]:
                mol.atom.append(atom)
                atom.tempflag=1
            mol.reindex()

            print 'sorting shells'
            # keep only attached shells
            oldshell = mol.shell
            mol.shell = []
            for s in oldshell:
                if s.linked_core.tempflag:
                    mol.shell.append(s)

            print 'clean'
            sel.clean_deleted(mol)
            print 'update'
            self.update_from_object(mol)

    def add_bond(self):
        sel = self.sel()
        dsel = sel.get()
        if len(dsel) != 2:
            self.error('Select 2 atoms only')
            return
        m1,a1 = dsel[0]
        m2,a2 = dsel[1]
        if m1 != m2:
            self.error('Select 2 atoms in the same molecule')
            return
        m1.add_bond(a1,a2)
        self.update_from_object(m1)

    def delete_bond(self):
        sel = self.sel()
        sel.printsel()
        dsel = sel.get()
        if len(dsel) != 2:
            self.error('Select 2 atoms only')
            return

        m1,a1 = dsel[0]
        m2,a2 = dsel[1]

        if m1 != m2:
            self.error('Select 2 atoms in the same molecule')
            return
        
        a1.conn.remove(a2)
        a2.conn.remove(a1)

        bhit = None
        for b in m1.bond:
            if ( b.index[0] == a1.get_index() and b.index[1] == a2.get_index() ) or \
                   ( b.index[0] == a2.get_index() and b.index[1] == a1.get_index() ) :
                bhit = b

        print 'bhit',bhit
        m1.bond.remove(bhit)
        self.update_from_object(m1)

    def xtoh(self):
        sel = self.sel()
        dsel = sel.get()
        mols = []
        if len(dsel) == 0:
            # no selection
            mols.append(self.choose_mol())
        else:
            for mol,atom in dsel:
                mols.append(mol)

        undo = []
        for mol in mols:
            for atom in mol.atom:
                if atom.symbol == 'X':
                    undo.append(lambda a = atom, oldsym = atom.symbol: a.set_symbol(oldsym))
                    undo.append(lambda a = atom, oldname = atom.name: a.set_name(oldname))
                    atom.symbol = 'H'
                    atom.name = 'H'
            self.update_from_object(mol)
            undo.append(lambda m = mol, s = self: s.update_from_object(m))
        self.undo_stack.append(undo)            

    def setz(self,z):
        undo = []
        sel = self.sel()
        mols = sel.get_mols()
        for mol in mols:
            atoms = sel.get_by_mol(mol)
            for atom in atoms:
                undo.append(lambda a = atom, oldsym = atom.symbol: a.set_symbol(oldsym))
                undo.append(lambda a = atom, oldname = atom.name: a.set_name(oldname))
                atom.symbol = z_to_el[z]
                atom.name = z_to_el[z]
            self.update_from_object(mol)
            undo.append(lambda m = mol, s = self: s.update_from_object(m))
        self.undo_stack.append(undo)

    def sethyb(self,hyb):
        """Set hybridisation for the selected atoms
        Uses methods of the Zmatrix object
        """
        undo = []
        sel = self.sel()
        mols = sel.get_mols()
        for mol in mols:
            atoms = sel.get_by_mol(mol)
            old_list = copy.copy(mol.atom)
            old_bond = copy.deepcopy(mol.bond)
            #print 'check bonds saved'
            #for b in old_bond:
            #    print b.index
            undo.append(lambda m = mol, oa = old_list: m.apply_atom_list(oa))
            undo.append(lambda m = mol, ob = old_bond: m.apply_connect(ob))
            undo.append(lambda m = mol: m.reindex())
            undo.append(lambda m = mol: m.update_conn())
            # End of undo code

            for atom in atoms:
                (code,msg) = mol.hybridise(atom,hyb)
                if code:
                    self.error(msg)
                    break

            self.update_from_object(mol)
            undo.append(lambda m = mol, s = self: s.update_from_object(m))

        self.undo_stack.append(undo)

    def measure_dist(self):

        sel = self.sel()
        sel.printsel()
        dsel = sel.get()
        if len(dsel) != 2:
            self.error('Select 2 atoms for a bond')
            return

        m1,a1 = dsel[0]
        m2,a2 = dsel[1]

        if m1 != m2:
            self.error('Select 2 atoms in the same molecule')
            return

        val = m1.get_distance(a1,a2)
        tag = str(a1.get_index()+1) + ' - ' + str(a2.get_index()+1)
        return (tag,val)

    def measure_angle(self):

        sel = self.sel()
        sel.printsel()
        dsel = sel.get_ordered()
        if len(dsel) != 3:
            self.error('Select 3 atoms for an angle')
            return

        m1,a1 = dsel[0]
        m2,a2 = dsel[1]
        m3,a3 = dsel[2]

        val = m1.get_angle(a1,a2,a3)
        tag = str(a1.get_index()+1) + ' - ' + str(a2.get_index()+1) + ' - ' + str(a3.get_index()+1)
        return (tag,val)

    def measure_torsion(self):

        sel = self.sel()
        sel.printsel()
        dsel = sel.get_ordered()
        if len(dsel) != 4:
            self.error('Select 4 atoms for a torsion')
            return

        m1,a1 = dsel[0]
        m2,a2 = dsel[1]
        m3,a3 = dsel[2]
        m4,a4 = dsel[3]

        if m1 != m2 or m1 != m3 or m1 != m4:
            self.error('Select 4 atoms in the same molecule')
            return

        val = m1.get_dihedral(a1,a2,a3,a4)
        tag = str(a1.get_index()+1) + ' - ' + str(a2.get_index()+1) + ' - ' + str(a3.get_index()+1) + ' - ' + str(a4.get_index()+1)
        return (tag,val)

    def clean(self,clean_code):

        # see how many structures are loaded
        print len(self.data_list)
        mol = self.data_list[0]

        self.start_clean_calced(mol,clean_code)

        calced  = self.clean_calced[clean_code]
        calc  = calced.calc
        calc.set_input('mol_obj',mol)
        calced.update_func = lambda o,s=self,t=str(id(mol)) : s.update_model(t,o)
        calced.Run()


    def clean_opts(self,clean_code):

        # see how many structures are loaded
        print len(self.data_list)
        mol = self.data_list[0]

        self.start_clean_calced(mol,clean_code)

        # these  are simplified invocations, no callbacks, reload_func etc
        # we pass None as the graph argument which means there is no dialog box
        # when the calculation finishes (or fails....)
        # would be better to trap errors really...

        calced  = self.clean_calced[clean_code]
        calced.show()

    def start_clean_calced(self,mol,clean_code):

        # these  are simplified invocations, no callbacks, reload_func etc
        # we pass None as the graph argument which means there is no dialog box
        # when the calculation finishes (or fails....)
        # would be better to trap errors really...

        root = self.master

        if not self.clean_calced.has_key(clean_code):

            if clean_code == 'MNDO':

                calc = MNDOCalc()
                calc.set_input('mol_obj',mol)
                calc.set_parameter('task',MENU_OPT)
                ed = MNDOCalcEd(root,calc,None,job_editor=self.job_editor)

            elif clean_code == 'MOPAC':

                calc = MopacCalc()
                calc.set_input('mol_obj',mol)
                calc.set_parameter('task',"optimise")
                ed = MopacCalcEd(root,calc,None,job_editor=self.job_editor)

            elif clean_code == 'GAMESS-UK':

                calc = GAMESSUKCalc()
                calc.set_input('mol_obj',mol)
                calc.set_parameter('task',MENU_OPT)
                calc.set_parameter('symmetry',0)
                ed = GAMESSUKCalcEd(root,calc,None,job_editor=self.job_editor)

            elif clean_code == 'UFF':

                calc = ChemShellCalc()
                calc.set_input('mol_obj',mol)
                calc.set_parameter('calctype','MM')
                calc.set_parameter('task','optimise')
                ed = ChemShellCalcEd(root,calc,None,job_editor=self.job_editor)

            # when the window is closed, we want to keep the editor alive
            # to save options between runs
            ed.userdeletefunc(lambda: ed.withdraw())
            ed.withdraw()
            self.clean_calced[clean_code] = ed


    def addfrag(self,frag):
        """Add a fragment to the selected molecule

        non-trivial, because the process deletes (and replaces at the
        end) the selected atom, which may be referred to by other atoms
        ... multiple additions particularly troublesome.
        perhaps a replace_atom function could cover this?

        we need to do a deepcopy to make sure that each time we use a fragment
        we dont corrupt the template

        some atoms (e.g. the 1st 3) don't have the required internal coordinates
        anyway, so we will need to make them up, which may imply atom reordering

        lots of -998's (means i1,i2,i3 unexpectedly None) showing up

        also see zmatrix.py: 
        #.....assumption that i1 is set is not generally safe

        if replacement atom has a known cartesian position, it shouldn't
        actually be necessary to generate one (maybe update a distance?)

        we need to resolve question of which connectivity representation
        is up-to-date at any point in time
        ... perhaps best strategy is to define API

        also suggests value of saving the internals for all atoms to a file,
        even if they are not being used - quite a big change!
        
        should change interface to menubutton + a button to activate.
        could usefully have a selection window that takes wild cards,
        and also equivalencies (z=12, symbol=c*) etc, parse to regex
        module on an atom-by atom basis,
        perhaps one window, with and/or relationships between them.
        could use some exceptions (e.g. atom is not in molecule..)

        """
        sel = self.sel()
        undo = []
        for mol in sel.get_mols():
            atoms = sel.get_by_mol(mol)
            for atom in atoms:
                l1 = len(mol.atom)
                oa = atom
                ia = atom.get_index()
                (code,msg) = mol.add_fragment(atom,frag)
                if code:
                    self.error(msg)
                    break
                
                l2 = len(mol.atom)
                undo.append(lambda m = mol, i = ia, na = l2-l1: mol.remove_fragment(ia,oa,na))
            self.update_from_object(mol)
            undo.append(lambda m = mol, s = self: s.update_from_object(m))
        self.undo_stack.append(undo)

    def select_all(self):
        # First build a list of structures
        mols = self.loaded_mols()
        self.sel().clear()
        for m in mols:
            self.sel().append(m,m.atom)

    def select_by_distance_to_selected(self):
        """Uses distance to any selected atom"""
        sel = self.sel()
        dsel = sel.get()
        print 'dsel', dsel
            
        if not len(dsel):
            return

        res = self.distance_dialog.activate()

        if res == 'OK':
            val = float(self.distance_dialog.w_val.get())
        else:
            return

        mol,atom = dsel[0]
        r2test = val*val
        print  r2test, dsel
        set = []
        print 'Selected Atoms'
        reslist = []

        for a in mol.atom:
            for mol2,atom2 in dsel:
                if mol2 == mol:
                    ori = atom2.coord
                    r2 = ( (ori[0]-a.coord[0])*(ori[0]-a.coord[0]) + \
                           (ori[1]-a.coord[1])*(ori[1]-a.coord[1]) + \
                           (ori[2]-a.coord[2])*(ori[2]-a.coord[2]) )
                    if r2 < r2test:
                        set.append(a)
                        try:
                            resno = a.resno
                            try:
                                ix = reslist.index(resno)
                            except ValueError:
                                reslist.append(resno)
                            print a.get_index(), "      ", a.resno, a.symbol, sqrt(r2)
                        except AttributeError:
                            print a.get_index(), "      ", a.symbol, sqrt(r2)
                        break

                else:
                    print 'CANT PROCESS MULTIPLE MOLECULES'
                    return


        sel.clear()
        print 'residues selected',reslist
        print 'Total number of atoms selected',len(set)
        #print 'set',set
        sel.append(mol,set)
        self.update_zme_sel()
        self.update()
        

    def select_by_distance_to_point(self):
        """Uses distance to a point (by default it is at
        the centroid of the selection)"""
        sel = self.sel()
        dsel = sel.get()
        print 'dsel', dsel
            
        if len(dsel):
            ori = sel.get_centroid()
            self.distance_dialog2.x.setentry(ori[0])
            self.distance_dialog2.y.setentry(ori[1])
            self.distance_dialog2.z.setentry(ori[2])
            mol,atom = dsel[0]            
        else:
            # no selection
            mol = self.choose_mol()
            self.distance_dialog2.x.setentry(0.0)
            self.distance_dialog2.y.setentry(0.0)
            self.distance_dialog2.z.setentry(0.0)
            
        res = self.distance_dialog2.activate()

        if res == 'OK':
            val = float(self.distance_dialog2.w_val.get())
            ori = [ float(self.distance_dialog2.x.get()),
                    float(self.distance_dialog2.y.get()),
                    float(self.distance_dialog2.z.get())]
        else:
            return


        r2test = val*val
        print ori, r2test, dsel
        set = []
        print 'Selected Atoms'
        reslist = []
        for a in mol.atom:
            r2 = ( (ori[0]-a.coord[0])*(ori[0]-a.coord[0]) + \
                   (ori[1]-a.coord[1])*(ori[1]-a.coord[1]) + \
                   (ori[2]-a.coord[2])*(ori[2]-a.coord[2]) )
            if r2 < r2test:
                set.append(a)
                try:
                    resno = a.resno
                    try:
                        ix = reslist.index(resno)
                    except ValueError:
                        reslist.append(resno)
                    print a.get_index(), "      ", a.resno, a.symbol, sqrt(r2)
                except AttributeError:
                    print a.get_index(), "      ", a.symbol, sqrt(r2)

        sel.clear()
        print 'residues selected',reslist
        print 'Total number of atoms selected',len(set)
        #print 'set',set
        sel.append(mol,set)
        self.update_zme_sel()
        self.update()


    def select_by_distance_to_point_and_trim(self):
        """Uses distance to a point (by default it is at
        the centroid of the selection)"""
        sel = self.sel()
        dsel = sel.get()
        print 'dsel', dsel
            
        if len(dsel):
            ori = sel.get_centroid()
            self.distance_dialog2.x.setentry(ori[0])
            self.distance_dialog2.y.setentry(ori[1])
            self.distance_dialog2.z.setentry(ori[2])
            mol,atom = dsel[0]            
        else:
            # no selection
            mol = self.choose_mol()
            self.distance_dialog2.x.setentry(0.0)
            self.distance_dialog2.y.setentry(0.0)
            self.distance_dialog2.z.setentry(0.0)
            
        res = self.distance_dialog2.activate()

        if res == 'OK':
            val = float(self.distance_dialog2.w_val.get())
            ori = [ float(self.distance_dialog2.x.get()),
                    float(self.distance_dialog2.y.get()),
                    float(self.distance_dialog2.z.get())]
        else:
            return


        r2test = val*val
        print ori, r2test, dsel
        set = []
        print 'Selected Atoms'
        reslist = []

        mols = self.loaded_mols()

        for mol in mols:
            for a in mol.atom:
                r2 = ( (ori[0]-a.coord[0])*(ori[0]-a.coord[0]) + \
                       (ori[1]-a.coord[1])*(ori[1]-a.coord[1]) + \
                       (ori[2]-a.coord[2])*(ori[2]-a.coord[2]) )
                if r2 < r2test:
                    set.append(a)
                    try:
                        resno = a.resno
                        try:
                            ix = reslist.index(resno)
                        except ValueError:
                            reslist.append(resno)
                        print a.get_index(), "      ", a.resno, a.symbol, sqrt(r2)
                    except AttributeError:
                        print a.get_index(), "      ", a.symbol, sqrt(r2)

            sel.clear()
            print 'residues selected',reslist
            print 'Total number of atoms selected',len(set)
            #print 'set',set
            sel.append(mol,set)

        self.update_zme_sel()

        # Now update all images based on the new selections

        for v in self.vis_list:
            try:
                v.draw_by_selection()
            except AttributeError:
                pass

        self.update()

    def select_connected(self):
        # First build a list of structures
        sel = self.sel()
        dsel = sel.get()
        print 'dsel', dsel
        edited = []
        for mol in sel.get_mols():
            set = sel.get_by_mol(mol)
            set2 = copy.copy(set)
            for a in set2:
                for b in a.conn:
                    if b in set:
                        pass
                    else:
                        set.append(b)
            sel.append(mol,set)

    def select_by_bonds(self):
        # First build a list of structures
        sel = self.sel()
        dsel = sel.get()
        print 'dsel', dsel
        edited = []
        for mol in sel.get_mols():

            for a in mol.atom:
                a.tmp = 0

            set = sel.get_by_mol(mol)
            for a in set:
                a.tmp = 1

            more = 1
            while more:
                more = 0
                for a in mol.atom:
                    if a.tmp == 1:
                        a.tmp = 2
                        for b in a.conn:
                            if b.tmp == 0:
                                b.tmp = 1
                                more=1
            set = []
            for a in mol.atom:
                if a.tmp:
                    set.append(a)

            #sel.clear()
            sel.append(mol,set)

    def ViewMenu(self):
        mbutton = self.menuBar.component('Views-button')
        #mbutton = Menubutton(self.mBar, text="Views", underline=0)
        #mbutton.pack(side=LEFT, padx="2m")
        menu = Menu(mbutton, tearoff=0, postcommand=self.post_view)
        self.view_menu=menu
        mbutton['menu'] = menu
        return mbutton

    def post_view(self):

        print 'POST VIEW'
        menu = self.view_menu
        menu.delete(0,Tkinter.AtEnd())

        for obj in self.data_list:
            # one submenu for each object
            cascade = Menu(menu,tearoff=0)
            t = id(obj)
            show=0
            built=0
            try:
                visl = self.vis_dict[t]
                built=1
                for vis in visl:
                    if vis.IsShowing():
                        show=1
            except KeyError:
                pass

            if show:
                myfont=("Helvetica", 9, "bold")
            else:
                myfont=("Helvetica", 9, "normal")

            if obj.name is not None:
                name = obj.name
            else:
                name = obj.title

            menu.add_cascade(label=name, font=myfont,menu=cascade)
            t = id(obj)
            if built:
                for vis in visl:
                    if vis.IsShowing():
                        txt = "Hide " + vis.GetTitle()
                        cascade.add_command(label=txt, underline=0,command=lambda x=vis: x.Hide())
                    else:
                        txt = "Show " + vis.GetTitle()
                        cascade.add_command(label=txt, underline=0,command=lambda x=vis: x.Show())
                    txt = "Adjust " + vis.GetTitle()
                    cascade.add_command(label=txt, command= lambda x=vis : x.Open())
                    cascade.add_separator()

            #
            # build menu of options, note double lambda form....
            # inner lambda wraps up the call to the visualiser with any arguments
            #    that are needed (these are visualiser-specific)
            # outer lambda passes this function to self.visualise, which
            #    creates the visualiser, and also registers it in self.vis_dict
            # 

            t1 = string.split(str(obj.__class__),'.')
            myclass = t1[len(t1)-1]

            print 'myclass',myclass
            if myclass == 'Indexed' or myclass == 'Zmatrix':
                if self.molecule_visualiser:
                    cascade.add_command(
                        label="New Molecule View",command=\
                           lambda s=self,obj=obj: s.visualise(obj,visualiser=\
                              lambda r=s.master,g=s,func=s.molecule_visualiser,obj=obj: func(r,g,obj)))

            if myclass == 'Field' :
                if obj.dimensions() == 3:
                    if 1:
                        if obj.ndd == 1:
                            # scalar visualiser tools
                            cascade.add_command(
                                label="New Orbital View",command=\
                                   lambda s=self,obj=obj: s.visualise(obj,visualiser=\
                                      lambda r=s.master,g=s,func=s.orbital_visualiser,obj=obj: func(r,g,obj),open_widget=1))
                            cascade.add_command(
                                label="New Density View",command=\
                                   lambda s=self,obj=obj: s.visualise(obj,visualiser=\
                                      lambda r=s.master,g=s,func=s.density_visualiser,obj=obj: func(r,g,obj)))
                            cascade.add_command(
                                label="Density Volume Visualisation View",command=\
                                   lambda s=self,obj=obj: s.visualise(obj,visualiser=\
                                      lambda r=s.master,g=s,func=s.volume_density_visualiser,obj=obj: func(r,g,obj)))
                            cascade.add_command(
                                label="Orbital Volume Visualisation View",command=\
                                   lambda s=self,obj=obj: s.visualise(obj,visualiser=\
                                      lambda r=s.master,g=s,func=s.volume_orbital_visualiser,obj=obj: func(r,g,obj)))
                            cascade.add_command(
                                label="New Cut Slice View",command=\
                                   lambda s=self,obj=obj: s.visualise(obj,visualiser=\
                                      lambda r=s.master,g=s,func=s.cut_slice_visualiser,obj=obj: func(r,g,obj),open_widget=1))

                            cascade.add_command(
                                label="New Colour Surface View",command=\
                                   lambda s=self,obj=obj: s.visualise(obj,visualiser=\
                                      lambda r=s.master,g=s,func=s.colour_surface_visualiser,obj=obj : func(
                                r,g,obj,colour_obj=None)))

                if obj.dimensions() == 2:
                    if self.slice_visualiser:
                        cascade.add_command(
                            label="New 2D View",command=\
                               lambda s=self,obj=obj: s.visualise(obj,visualiser=\
                                  lambda r=s.master,g=s,func=s.slice_visualiser,obj=obj: func(r,g,obj)))

                print 'ndd',obj.ndd
                if obj.ndd == 3:
                    if self.vector_visualiser:
                        cascade.add_command(
                            label="Vector Visualisation View",command=\
                               lambda s=self,obj=obj: s.visualise(obj,visualiser=\
                                  lambda r=s.master,g=s,func=s.vector_visualiser,obj=obj: func(r,g,obj)))
                else:
                    if self.irregular_data_visualiser:
                        cascade.add_command(
                            label="New Grid View",command=\
                                   lambda s=self,obj=obj: s.visualise(obj,visualiser=\
                                      lambda r=s.master,g=s,func=s.irregular_data_visualiser,obj=obj: func(r,g,obj)))



            if myclass == 'VibFreq' :
                if self.vibration_visualiser:
                    cascade.add_command(
                        label="Animate Vibration",command=\
                               lambda s=self,obj=obj: s.visualise(obj,visualiser=\
                                  lambda r=s.master,g=s,func=s.vibration_visualiser,obj=obj: func(r,g,obj),
                                                                  open_widget=1))

            print 'myclass',myclass
            if myclass == 'File' and obj.MoldenReadable() :
                if self.wavefunction_visualiser:  
                    cascade.add_command(
                        label="Run Molden",command=\
                               lambda s=self,obj=obj: s.visualise(obj,visualiser=\
                                  lambda r=s.master,g=s,func=s.wavefunction_visualiser,obj=obj: func(r,g,obj),
                                                                  open_widget=1))


        menu.add_separator()

        greyedfont = ("Helvetica", 9, "normal")
        showfont = ("Helvetica", 9, "bold")
        
        # Create the Menu Item to Alter all molecules
        # First instantiate the visualiser if it doesn't exist
        if not self.allmolecule_visualiser:
            # Need to import this here because the others are set up in vtkgraph.py but we are different
            # because we are not tied to a single image and so have no vtk-specific code
            from generic.visualiser import AllMoleculeVisualiser
            self.allmolecule_visualiser = AllMoleculeVisualiser( self.master, self )
            
        # update_mol_list returns None if no molecules to display
        if self.allmolecule_visualiser.update_mol_list(): 
            menu.add_command(label="Adust All Molecules", underline=0, font=showfont,
                             command = lambda s=self : s.adjust_allmolc(1) )
        else:
            menu.add_command(label="Adust All Molecules", underline=0, font=greyedfont,
                             command = lambda s=self : s.adjust_allmolc(0) )
        
        if ( len( self.vis_list ) >= 1 ):
            myfont = showfont
        else:
            myfont = greyedfont
                
        menu.add_command(label="Show All", underline=0, font=myfont,
                         command=lambda x=self : x.showall(1))
        menu.add_command(label="Hide All", underline=0, font=myfont,
                         command=lambda x=self : x.showall(0))
        menu.add_separator()

#        menu.add_command(label="Animation...", underline=0, font=myfont,
#                         command=lambda x=self : x.pack_ani_toolbar())
        menu.add_separator()

        menu.add_command(label="Centre on Selected", underline=0, 
                         command=lambda x=self : x.centre_on_selected())

    def add_vis_menu(self,menu,txt,fnc,objects):
        """ make a list of objects that can be visualised in a particular way
        """
        if len(objects) == 0:
            menu.add_command(label=txt, underline=0,state="disabled")
        elif len(objects) == 1:
            menu.add_command(label=txt, underline=0, 
                             command=lambda f=fnc,s=self,o=objects[0]: s.visualise(o,visualiser=f))
        else:
            cascade = Menu(menu,tearoff=0)
            menu.add_cascade(label=txt, menu=cascade)
            for obj in objects:
                if obj.name is not None:
                    name = obj.name
                else:
                    name = obj.title
                cascade.add_command(label=obj.name,
                                    command=lambda f=fnc,s=self,o=obj: s.visualise(o,visualiser=f))


    def add_obj_cmd(self,menu,txt,fnc):
        """Loop over all objects and build a submenu
        """
        mols = self.data_list
        if len(mols) == 0:
            menu.add_command(label=txt, underline=0,state="disabled")
        elif len(mols) == 1:
            menu.add_command(label=txt, underline=0, 
                                 command=lambda f=fnc,o=mols[0] : f(o))
        else:
            cascade = Menu(menu,tearoff=0)
            menu.add_cascade(label=txt, menu=cascade)
            for obj in mols:
                cascade.add_command(label=obj.name,
                                    command= lambda f=fnc,o=obj : f(o))

    def adjust_allmolc(self, show):
        """Display the widget to adjust all the molecule representations together
           if we have any molecules to adjust
        """

        if ( show == 1 ):
            self.allmolecule_visualiser.Open()
        else:
            if self.allmolecule_visualiser.dialog:
                self.allmolecule_visualiser.dialog.withdraw()
            else:
                pass

    def showall(self,show):
        for o in self.vis_list:
            if show:
                o.Show()
            else:
                o.Hide()

    def centre_on_selected(self):
        if len(self.sel().get()):
            self.set_origin(self.sel().get_centroid())

##    def VisualiseMenu(self):
##        mbutton = Menubutton(self.mBar, text='Visualise', underline=0)
##        mbutton.pack(side=LEFT, padx="2m")
##        menu = Menu(mbutton, tearoff=0, postcommand=self.post_vis)
##        self.visualiser_menu=menu
##        mbutton['menu'] = menu
##        return mbutton

    def ComputeMenu(self):
        #mbutton = Menubutton(self.mBar, text='Compute', underline=0)
        #mbutton.pack(side=LEFT, padx="2m")
        mbutton = self.menuBar.component('Compute-button')
        self.compute_menu=Menu(mbutton, tearoff=0, postcommand=self.post_compute_menu)
        mbutton['menu'] = self.compute_menu
        return mbutton

    def post_compute_menu(self):

        menu = self.compute_menu
        menu.delete(0,Tkinter.AtEnd())
        # First build a list of structures
        mols = self.loaded_mols()
        ###menu.add_command(label="Test", underline=0, command=self.testcmd2)
        self.add_mol_cmd(menu,mols,"GAMESS-UK",self.gamessuk_calced)
        self.add_mol_cmd(menu,mols,"MOLPRO",self.molpro_calced)
        self.add_mol_cmd(menu,mols,"MNDO",self.mndo_calced)
        self.add_mol_cmd(menu,mols,"Dalton",self.dalton_calced)
        self.add_mol_cmd(menu,mols,"Mopac",self.mopac_calced)
        self.add_mol_cmd(menu,mols,"ChemShell",self.chemshell_calced)

    def add_mol_cmd(self,menu,mols,txt,fnc,all=0):
        if len(mols) == 0:
            menu.add_command(label=txt, underline=0,state="disabled")
        elif len(mols) == 1:
            menu.add_command(label=txt, underline=0, 
                                 command=lambda f=fnc,o=mols[0] : f(o))
        else:
            cascade = Menu(menu,tearoff=0)
            menu.add_cascade(label=txt, menu=cascade)
            for obj in mols:
                cascade.add_command(label=obj.name,
                                    command= lambda f=fnc,o=obj : f(o))
            if all:
                cascade.add_separator()
                cascade.add_command(label='All',
                                    command= lambda f=fnc,o=None : f(o,all=1))
                
    def add_field_cmd(self,menu,fields,txt,fnc):
        if len(fields) == 0:
            menu.add_command(label=txt, underline=0,state="disabled")
        elif len(fields) == 1:
            menu.add_command(label=txt, underline=0, 
                                 command=lambda f=fnc,o=fields[0] : f(o))
        else:
            cascade = Menu(menu,tearoff=0)
            menu.add_cascade(label=txt, menu=cascade)
            for obj in fields:
                cascade.add_command(label=obj.name,
                                    command= lambda f=fnc,o=obj : f(o))

    def testcmd(self):
        """ this can be used to explore problems with threads etc
        """
        job = BackgroundJob()
        job.add_step(RUN_APP,'test cmd',local_command="cmdx.exe")
        job.run()

    def testcmd2(self):
        job = BackgroundJob()
        job.add_step(RUN_APP,'test cmd',local_command="cmdx.exe")

        self.job_editor.manager.RegisterJob(job)
        self.job_editor.show()

        self.job_thread = JobThread(job)

        try:
            self.job_thread.start()
        except RuntimeError,e:
            print 'exception'
            self.error(str(e))
        print 'job done'

    def DebugMenu(self):
        #mbutton = Menubutton(self.mBar, text='Debug', underline=0)
        #mbutton.pack(side=LEFT, padx="2m")
        mbutton = self.menuBar.component('Debug-button')
        menu = Menu(mbutton, tearoff=0, postcommand=self.post_debug_menu)
        self.debug_menu=menu
        mbutton['menu'] = menu
        return mbutton

    def post_debug_menu(self):
        menu = self.debug_menu
        menu.delete(0,Tkinter.AtEnd())
        menu.add_command(label='Debug Window', underline=0, 
                command=lambda x=self: x.open_debug_window())

        #menu.add_separator()


    def ShellMenu(self):
        #mbutton = Menubutton(self.mBar, text='Debug', underline=0)
        #mbutton.pack(side=LEFT, padx="2m")
        mbutton = self.menuBar.component('Shell-button')
        menu = Menu(mbutton, tearoff=0, postcommand=self.post_shell_menu)
        self.shell_menu=menu
        mbutton['menu'] = menu
        return mbutton

    def post_shell_menu(self):
        menu = self.shell_menu
        menu.delete(0,Tkinter.AtEnd())
        menu.add_command(label='Idle Shell', underline=0, 
                command=lambda x=self: x.myshell())
        #menu.add_separator()

    def open_debug_window(self):
        deb_setwidget(self.debug_window.text)
        self.debug_window.deiconify()

    def HelpMenu(self):
        """Create the help menu
        """
        self.toggleBalloonVar = IntVar()
        self.toggleBalloonVar.set(1)
        #      self.setting = Setting()
        mbutton = self.menuBar.component('Help-button')

        menu = self.menuBar.component('Help-menu')
        # temporarily use an explicitly created menu to avoid
        # error messages from ballon help
        #self.help_menu=Menu(mbutton, tearoff=0, postcommand=self.post_compute_menu)
        self.menuBar.addmenuitem('Help', 'checkbutton',
                                 'Toggle balloon help',
                                 label='Balloon help',
                                 variable = self.toggleBalloonVar,
                                 command=self.toggleBalloon)

        self.menuBar.addmenuitem('Help', 'command',
                                 'Introduction',
                                 label='Introductory Documentation',
                                 command = lambda s=self, lab="Introduction":
                                 s.showhelp(lab))

        self.menuBar.addmenuitem('Help', 'separator', '')

        self.menuBar.addmenuitem('Help', 'command',
                                 'File Menu',
                                 label='Help on File Menu',
                                 command = lambda s=self, lab="File Menu":
                                 s.showhelp(lab))

        self.menuBar.addmenuitem('Help', 'command',
                                 'Edit Menu',
                                 label='Help on Edit Menu',
                                 command = lambda s=self, lab="Edit Menu":
                                 s.showhelp(lab))

        self.menuBar.addmenuitem('Help', 'command',
                                 'Views Menu',
                                 label='Help on Views Menu',
                                 command = lambda s=self, lab="View Menu":
                                 s.showhelp(lab))

        self.menuBar.addmenuitem('Help', 'command',
                                 'Compute Menu',
                                 label='Help on Compute Menu',
                                 command = lambda s=self, lab="Compute Menu":
                                 s.showhelp(lab))

        self.menuBar.addmenuitem('Help', 'command',
                                 'Shell Menu',
                                 label='Help on Shell Menu',
                                 command = lambda s=self, lab="Shell Menu":
                                 s.showhelp(lab))

        self.menuBar.addmenuitem('Help', 'separator', '')
        
        self.menuBar.addmenuitem('Help', 'command',
                                 'Key Bindings',
                                 label='Key Bindings',
                                 command = lambda s=self, lab="Key Bindings":
                                 s.showhelp(lab))

        self.menuBar.addmenuitem('Help', 'separator', '')
        
        self.menuBar.addmenuitem('Help', 'command',
                                 'About',
                                 label='About',
                                 command = self.about)

    def showhelp(self,lab):
        """Call on the help modlue to open a browser or display a widget with the help.
        """
        htmlfile,txtfile = viewer.help.getfiles(lab)
        viewer.help.displayhelp(htmlfile,txtfile, lab)
        

    def toggleBalloon(self):
        # from abstractapp
        if self.toggleBalloonVar.get():
            #self.__balloon.configure(state = 'both')
            self.balloon.configure(state = 'both')
        else:
            #self.__balloon.configure(state = 'status')
            self.balloon.configure(state = 'status')

    #
    # The following bit of code is very similar to that
    # used in the calculation editor to control the visualisation
    # of results
    #
    def open_visualise_window(self):
        """Open a new window with all the graphics controls """
        self.__update_data_list()
        self.data_dialog.show()

    def quick_mol_view(self,mols):
        """create a default image of a molecule and include it
        in the tables (vis_dict, vis_list)
        Then attempt to fit everything on screen
        """
        flag=1
        for mol in mols:
            vis = self.molecule_visualiser(self.master,self,mol)
            t = id(mol)
            self.vis_dict[t] = [vis]
            self.vis_list.append(vis)
            self.__update_vis_list()
            if flag:
                vis.Show(update=0)
#####                flag=0
        self.fit_to_window()

    def build_distance_dialog(self,include_xyz=0):
        """Create a dialog which we will use to 
           determine distances 
        """
        dialog = Pmw.Dialog(self.master,
            title='Enter Distance',
            buttons = ('OK','Cancel'))

        labels = []
        dialog.withdraw()
        i = dialog.interior()

        if include_xyz:

            grp = Pmw.Group(i,tag_text = 'Reference Position')
            ig = grp.interior()

            dialog.x = Pmw.Counter(
                ig,
                labelpos = 'w', label_text = 'x',
                increment = 1,
                entryfield_entry_width = 6,
                entryfield_value = 0,
                entryfield_validate = { 'validator' : 'real' })

            dialog.x.pack(expand='yes',fill='x',side='left')

            dialog.y = Pmw.Counter(
                ig,
                labelpos = 'w', label_text = 'y',
                increment = 1,
                entryfield_entry_width = 6,
                entryfield_value = 0,
                entryfield_validate = { 'validator' : 'real' })

            dialog.y.pack(expand='yes',fill='x',side='left')

            dialog.z = Pmw.Counter(
                ig,
                labelpos = 'w', label_text = 'z',
                increment = 1,
                entryfield_entry_width = 6,
                entryfield_value = 0,
                entryfield_validate = { 'validator' : 'real' })

            dialog.z.pack(expand='yes',fill='x',side='left')
            grp.pack(expand='yes',fill='x',side='top')

        d = {'counter' : 'real' }
        dialog.w_val = Pmw.Counter(
            i,
            datatype=d,
            labelpos = 'w', label_text = 'd = ',
            increment = 0.5,
            entryfield_entry_width = 10,
            entryfield_value = 1.0,
            entryfield_validate = { 'validator' : 'real' })


        dialog.w_val.pack(expand='yes',fill='x',side='top')

        if include_xyz:
            self.distance_dialog2 = dialog
        else:
            self.distance_dialog = dialog            
    

    def build_extend_dialog(self):
        """Create a dialog which we will use to 
           determine extent of periodic images represented
        """
        self.extend_dialog = Pmw.Dialog(self.master,
            title='Extend',
            buttons = ('OK','Cancel'))

        labels = []
        self.extend_dialog.withdraw()
        i = self.extend_dialog.interior()
        self.extend_dialog.fx = Pmw.Group(i,tag_text = 'X range')
        self.extend_dialog.fy = Pmw.Group(i,tag_text = 'Y range')
        self.extend_dialog.fz = Pmw.Group(i,tag_text = 'Z range')

        self.extend_dialog.minx = Pmw.Counter(
            self.extend_dialog.fx.interior(), 
            labelpos = 'w', label_text = 'min',
            increment = 1,
            entryfield_entry_width = 6,
            entryfield_value = 0,
            entryfield_validate = { 'validator' : 'integer' })

        self.extend_dialog.minx.pack(expand='yes',fill='x',side='left')

        self.extend_dialog.maxx = Pmw.Counter(
            self.extend_dialog.fx.interior(), 
            labelpos = 'w', label_text = 'max',
            increment = 1,
            entryfield_entry_width = 6,
            entryfield_value = 0,
            entryfield_validate = { 'validator' : 'integer' })

        self.extend_dialog.maxx.pack(expand='yes',fill='x',side='left')

        labels = labels + [self.extend_dialog.fx]

        self.extend_dialog.miny = Pmw.Counter(
            self.extend_dialog.fy.interior(), 
            labelpos = 'w', label_text = 'min',
            increment = 1,
            entryfield_entry_width = 6,
            entryfield_value = 0,
            entryfield_validate = { 'validator' : 'integer' })

        self.extend_dialog.miny.pack(expand='yes',fill='x',side='left')

        self.extend_dialog.maxy = Pmw.Counter(
            self.extend_dialog.fy.interior(), 
            labelpos = 'w', label_text = 'max',
            increment = 1,
            entryfield_entry_width = 6,
            entryfield_value = 0,
            entryfield_validate = { 'validator' : 'integer' })

        self.extend_dialog.maxy.pack(expand='yes',fill='x',side='left')

        labels = labels + [self.extend_dialog.fy]

        self.extend_dialog.minz = Pmw.Counter(
            self.extend_dialog.fz.interior(), 
            labelpos = 'w', label_text = 'min',
            increment = 1,
            entryfield_entry_width = 6,
            entryfield_value = 0,
            entryfield_validate = { 'validator' : 'integer' })

        self.extend_dialog.minz.pack(expand='yes',fill='x',side='left')

        self.extend_dialog.maxz = Pmw.Counter(
            self.extend_dialog.fz.interior(), 
            labelpos = 'w', label_text = 'max',
            increment = 1,
            entryfield_entry_width = 6,
            entryfield_value = 0,
            entryfield_validate = { 'validator' : 'integer' })

        self.extend_dialog.maxz.pack(expand='yes',fill='x',side='left')

        labels = labels + [self.extend_dialog.fz]

        self.extend_dialog.fx.pack(expand='yes',fill='x',side='top')
        self.extend_dialog.fy.pack(expand='yes',fill='x',side='top')
        self.extend_dialog.fz.pack(expand='yes',fill='x',side='top')

        Pmw.alignlabels(labels)

    def build_data_dialog(self):

        """Create a dialog which we will use to 
        visualise objects as read in from files
        """
        self.data_dialog = Pmw.MegaToplevel(
            title='Visualise')

        self.data_dialog.withdraw()

        self.sel_height = 10
        self.data_dialog.listbox = Pmw.ScrolledListBox(
            self.data_dialog.interior(),
            listbox_selectmode='extended',
            listbox_height=self.sel_height,
            selectioncommand=self.__click_result)

        self.data_dialog.listbox.pack(expand = 1, fill='x')

        self.data_dialog.buttonbox = Pmw.ButtonBox(self.data_dialog.interior())

        self.data_dialog.buttonbox.add('Options',command = self.__data_options)
        self.data_dialog.buttonbox.add('Show',command = self.__data_show)
        self.data_dialog.buttonbox.add('Hide',command = self.__data_hide)
        self.data_dialog.buttonbox.add('Connect',command = self.__data_connect)
        self.data_dialog.buttonbox.add('Edit',command = self.__data_edit)
        self.data_dialog.buttonbox.add('Delete',command = self.__data_destroy)

        self.data_dialog.buttonbox.pack(expand = 1, fill='x')


    def __update_data_list(self):

        # load a list of the result objects into the selector
        self.data_dialog.listbox.delete(0,'end')
        if not len(self.data_list):
            self.data_dialog.listbox.insert(Tkinter.AtEnd(), 'No Results Yet')
        else:
            for r in self.data_list:
                txt = r.name + ' ; ' + r.title
                self.data_dialog.listbox.insert(Tkinter.AtEnd(), txt)


    def __click_result(self):
        cursel = self.data_dialog.listbox.curselection()
        nsel = len(cursel)
        sels = self.data_dialog.listbox.getcurselection()
        print 'click results', sels

    def __data_options(self):
        self.__control_data('Options')

    def __data_show(self):
        self.__control_data('Show')

    def __data_hide(self):
        self.__control_data('Hide')

    def __data_connect(self):
        cursel = self.data_dialog.listbox.curselection()
        targets = []
        for sel in cursel:
            ix = int(sel)
            if ix < len(self.data_list):
                targets.append(ix)

        for ix in targets:
            o  = self.data_list[ix]
            t1 = string.split(str(o.__class__),'.')
            myclass = t1[len(t1)-1]
            if myclass == 'Indexed':
                self.connect_model(o)
            elif myclass == 'Zmatrix':
                self.connect_model(o)
            else:
                print 'cant connect (not a molecule)'

    def __data_edit(self):
        cursel = self.data_dialog.listbox.curselection()
        targets = []
        for sel in cursel:
            ix = int(sel)
            if ix < len(self.data_list):
                targets.append(ix)

        for ix in targets:
            o  = self.data_list[ix]
            t1 = string.split(str(o.__class__),'.')
            myclass = t1[len(t1)-1]
            if myclass == 'Indexed' or myclass == 'Zmatrix':
                self.edit_coords(o)
            else:
                print 'cant edit (not a molecule)'

    def __data_destroy(self):
        """Deletion of the selected objects from the listbox"""

        cursel = self.data_dialog.listbox.curselection()

        temp = []
        for res in self.data_list:
            temp.append(1)

        for sel in cursel:
            ix = int(sel)
            if ix < len(self.data_list):
                o  = self.data_list[ix]
                t = id(o)
                try:
                    visl = self.vis_dict[t]
                    for vis in visl:
                        vis.delete()
                except KeyError:
                    pass
                temp[ix] = 0

        newres = []
        for ix in range(len(self.data_list)):
            if temp[ix]:
                newres.append(self.data_list[ix])

        self.data_list = newres

        self.__update_data_list()
        self.__update_vis_list()

    def __control_data(self,cmd):

        """Handles processing of controls for a selection
        of calculation results. Creates a visualisation object
        if not already defined
        """

        cursel = self.data_dialog.listbox.curselection()
        targets = []
        for sel in cursel:
            ix = int(sel)
            if ix < len(self.data_list):
                targets.append(ix)

        for ix in targets:
            o  = self.data_list[ix]
            t = id(o)
            try:
                visl = self.vis_dict[t]
            except KeyError:
                # There is no visualiser, try and make one
                # take the last field of the class specification
                vis  = self.visualise(o)
                visl = [ vis ]

            for vis in visl:
                if cmd == 'Hide':
                    if vis:
                        vis.Hide()
                elif cmd == 'Show':
                    if vis:
                        vis.Show()
                if cmd == 'Options':
                    if vis:
                        vis.Open()

    def visualise(self, o, visualiser=None,open_widget=0 ):
            
        t1 = string.split(str(o.__class__),'.')
        myclass = t1[len(t1)-1]
        t = id(o)

        if visualiser:
            vis = visualiser()
        else:
            vis = None
            if myclass == 'Indexed' or myclass == 'Zmatrix':
                vis = self.molecule_visualiser(self.master,self,o)
            elif myclass == 'VibFreq' :
                # create a vibration visualiser
                try:
                    refmol = o.reference
                except AttributeError:
                    refmol = self.choose_mol()
                vis = self.vibration_visualiser(self.master, self, o, mol=refmol)
                # best have this one open from the start or nothing will happen
                vis.Open()
            elif myclass == 'Field':
                # Data visualisation - rather confusing
                # New Field Class
                try:
                    nd = len(o.dim)
                    if nd == 1:
                        self.warn('No viewer available for 1D data')
                        return None
                    elif nd == 2:
                        vis = self.slice_visualiser(self.master,self,o)
                    elif o.title == 'density':
                        #vis = self.density_visualiser(self.master,self,o)
                        vis = self.colour_surface_visualiser(self.master,self,o)
                    else:
                        vis = self.orbital_visualiser(self.master,self,o)
                        
                except KeyError:
                    pass
                    #except AttributeError:
                    # Irregular Dataset
                    #vis = self.irregular_data_visualiser(self.master,self,o)

            else:
                print 'Warning - cant yet visualise', myclass
                return None
        try:
            x = self.vis_dict[t]
            self.vis_dict[t].append(vis)
        except KeyError:
            self.vis_dict[t] = [vis]

        if open_widget:
            vis.Open()                    

        self.vis_list.append(vis)
        self.__update_vis_list()
        # to get correct view/show/hide
        # self.__update_data_list()
        vis.Show()
        return vis

    def graphics(self):
        """Open a new window with all the graphics controls """

        self.__update_vis_list()
        self.vis_dialog.show()

    def build_vis_dialog(self):

        """Create a dialog which we will use to control
        the visibility and parameters of the objects in the viewer
        """

        self.vis_dialog = Pmw.MegaToplevel(
            title='visualisation options')

        self.vis_dialog.withdraw()

        self.sel_height = 10
        self.vis_dialog.listbox = Pmw.ScrolledListBox(
            self.vis_dialog.interior(),
            listbox_selectmode='extended',
            listbox_height=self.sel_height,
            selectioncommand=self.__click_result)

        self.vis_dialog.listbox.pack(expand = 1, fill='x')

        self.vis_dialog.buttonbox = Pmw.ButtonBox(self.vis_dialog.interior())

        self.vis_dialog.buttonbox.add('Options',command = self.__vis_options)
        self.vis_dialog.buttonbox.add('Show',command = self.__vis_show)
        self.vis_dialog.buttonbox.add('Hide',command = self.__vis_hide)
        self.vis_dialog.buttonbox.add('Delete',command = self.__vis_destroy)

        self.vis_dialog.buttonbox.pack(expand = 1, fill='x')

    def __update_vis_list(self):
        """load a list of the current visualiser objects into the selector"""
        self.vis_dialog.listbox.delete(0,'end')
        if not len(self.vis_list):
            self.vis_dialog.listbox.insert(Tkinter.AtEnd(), 'No Graphics Yet')
        else:
            for r in self.vis_list:
                txt = r.GetTitle()
                self.vis_dialog.listbox.insert(Tkinter.AtEnd(), txt)

    def __click_vis(self):
        cursel = self.vis_dialog.listbox.curselection()
        nsel = len(cursel)
        sels = self.vis_dialog.listbox.getcurselection()
        print 'click results', sels

    def __vis_options(self):
        self.__control_vis('Options')

    def __vis_show(self):
        self.__control_vis('Show')

    def __vis_hide(self):
        self.__control_vis('Hide')

    def __vis_destroy(self):
        """Deletion of the selected objects from the listbox"""

        cursel = self.vis_dialog.listbox.curselection()

        temp = []

        for res in self.vis_list:
            temp.append(1)

        for sel in cursel:
            # this code is wrong - fortunately not used at present
            ix = int(sel)
            vis = self.vis_list[ix]
            for x  in self.vis_dict.keys():
                if self.vis_dict[x] == vis:
                    del self.vis_dict[x]
            vis.delete()
            temp[ix] = 0

        newvis=[]
        for ix in range(len(self.vis_list)):
            if temp[ix]:
                newvis.append(self.vis_list[ix])

        self.vis_list = newvis
        self.__update_vis_list()

    def __control_vis(self,cmd):
        """Handles processing of controls for a visualiser"""

        cursel = self.vis_dialog.listbox.curselection()
        targets = []
        for sel in cursel:
            ix = int(sel)
            vis = self.vis_list[ix]
            if cmd == 'Hide':
                vis.Hide()
            elif cmd == 'Show':
                vis.Show()
            if cmd == 'Options':
                vis.Open()

    def setscale(self):
        scale=askfloat(title='Set scale', prompt='Scale', 
                initialvalue=self.grid.scale, 
                minvalue=0.1, maxvalue=100.0)
        self.setscale(scale)

    def bgcolor(self):
        color=askcolor()
        self.setbgcolor(color[0])

    def fgcolor(self):
        color=askcolor()
        self.setfgcolor(color[0])

    def colorheight(self):
        self.setheightcolor()

    def ask_load_from_file(self):
        """Ask for a file to load structure from"""
        filename = askopenfilename(
            defaultextension='',
            initialdir=self.user_directory,
            filetypes=[('Molecules','.xyz'),
                       ('Molecules','.pdb'),
                       ('Molecules','.pun'),
                       ('Molecules','.c'),
                       ('Molecules','.crd'),
                       ('Molecules','.z'),
                       ('Molecules','.cml'),
                       ('Molecules','.xml'),
                       ('Molecules','.zmt'),
                       ('Molecules','.gjf'),
                       ('Molecules','.mol'),
                       ('XYZ','.xyz'),
                       ('PDB','.pdb'),
                       ('PDB','.PDB'),
                       ('CML','.cml'),
                       ('CML','.xml'),
                       ('DL_POLY CONFIG','CONFIG'),
                       ('DL_POLY HISTORY','HISTORY'),
                       ('Zmatrix','.zmt'),
                       ('GAMESS-UK Input','.in'),
                       ('Other Output','.out'),
                       ('Gaussian Output','.gjf'),
                       ('Gaussian Cube','.cube'),
                       ('All', '*')])

        if filename:
            err = self.load_from_file( filename )
            if err:
                self.error( "There was a problem reading in structures from the file %s" % filename )
                return
            
            # add to any open dialogs
            self.__update_data_list()

            # store the directory part for future file operations
            dirname = os.path.dirname(filename)
            self.user_directory = dirname
            print 'user directory is now',self.user_directory


    def load_from_file(self,filename=None):

        if not filename:
            print 'Must specify a file to read!'
            return
        
        words2 = string.split(filename,'/')
        name = words2[-1]
        words = string.split(name,'.')
        root = words[0]
        objs = []
        
        form = 'PUN'

        if len(words) == 1:
            if filename == 'CONFIG':
                form = 'dlpcfg'
                print 'form=dlpcfg'
            elif filename == 'HISTORY':
                form = 'dlphist'
                print 'form=dlphist'
        else:
            ext = words[-1]
            if ext == 'xyz':
                form = 'XYZ'
            if ext == 'pdb':
                form = 'PDB'
            if ext == 'PDB':
                form = 'PDB'
            if ext == 'crd':
                form = 'CRD'
            if ext == 'pun':
                form = 'PUN'
            if ext == 'c':
                form = 'PUN'
            if ext == 'z':
                form = 'PUN'
            if ext == 'zmt':
                form = 'ZMT'
            if ext == 'cml':
                form = 'CML'
            if ext == 'xml':
                form = 'CML'
            if ext == 'gjf':
                form = 'GAU'
            if ext == 'cube':
                form = 'CUBE'
            if ext == 'mol':
                form = 'MOL'
            if ext == 'RHO':
                form = 'SMG'
            if ext == 'vtk':
                form = 'vtk'
            elif ext == 'sys':
                form = 'SYS'
            elif ext == 'bs':
                form = 'XBS'
            elif ext == 'out':
                form = 'OUT'
            elif ext == 'in':
                form = 'GAMIN'

        if form == 'PDB':
            objs = self.rdpdb(filename,root)
        elif form == 'PUN':
            objs = self.rdpun(filename,root)
        elif form == 'ZMT':
            objs = self.rdzmt(filename,root)
        elif form == 'CML':
            objs = self.rdcml(filename,root)
        elif form == 'GAMIN':
            objs = self.rdgamin(filename,root)
        elif form == 'MOL':
            objs = self.rdmol(filename,root)
        elif form == 'SMG':
            objs = self.rdsmeagol(filename,root,ext)
        elif form == 'vtk':
            objs = self.rdvtk(filename,root)
        elif form == 'dlpcfg':
            print 'calling rdcfg'
            objs = self.rdcfg(filename)
        elif form == 'dlphist':
            print 'calling rdhist'
            objs = self.rdhist(filename)
        elif form == 'CUBE':
            objs = self.rdcube(filename)
        elif form == 'OUT':
            objs = self.rdout(filename,root)
        else:
            fileh = open(filename,'r')
            if form == 'XYZ':
                objs = self.rdxyz(fileh,root)
            elif form == 'CRD':
                objs = self.rdcrd(fileh,root)
            elif form == 'GAU':
                objs = self.rdgjf(fileh,root)
            else:
                print 'No reader for format ',form
            fileh.close()

        if not objs:
            return 1
        else:
            for o in objs:
                print 'obj',o
                t = id(o)
                self.file_dict[t] = file
            return 0
                
    def rdout(self,filename,root):
        """
           We scan the output to determine what sort of output we are reading
           and then call the relevant reader to parse the file. We then return
           the objects found by the reader.
        """

        objs = None
        prog = self.scan_output( filename )
        if not prog:
            print "Cannot determine output file type for file: %s" % filename
            return None
        elif ( prog == "GAMESS-UK"):
            objs = self.rdgamout( filename, root )
        elif ( prog == "DALTON"):
            objs = self.rddalout( filename, root )
        else:
            print "Bad output type returned by scan_output!"

        return objs

    def scan_output(self, filename):
        """ Scan through an output to determine which programme produced it
            We compare each line against a list of regular expressions that
            are considered indicative of a particular programmes output and then
            break out as soon as we hit a match.
        """

        # Dictionary to hold regular expressions and the return value
        redict = {
            re.compile('\s*\*\s*===  G A M E S S - U K    ===\s*\*') : 'GAMESS-UK',
            re.compile('\s*\*{11}  DALTON - An electronic structure program  \*{11}') : 'DALTON',
            }
        
        f = open( filename, 'r' )

        done = None
        retval = None
        while not done:

            line = f.readline()
            if not line:
                print "Error reading file in scan_output!"
                done = 1
                break
            
            for myre in redict.items():
                if myre[0].match( line ):
                    retval = myre[1]
                    done = 1
                    break

        f.close()
        return retval
        
    def rdzmt(self,file,root):
        """Load from a zmatrix
        """
        model = Zmatrix(file=file)
        model.title = root
        model.name = self.make_unique_name(root)
        self.connect_model(model)
        self.quick_mol_view([model])
        self.append_data(model)
        return [model]

    def rdcml(self,file,root):
        import cml

        atomDict=cml.atomInfo(file)
        model = Zmatrix()
        model.title = root
        model.name = self.make_unique_name(root)

        for i in range(0,len(atomDict)):

            try:
                x = float(atomDict[i]['x3'])
                y = float(atomDict[i]['y3'])
                z = float(atomDict[i]['z3'])
            except KeyError:
                x = float(atomDict[i]['x2'])
                y = float(atomDict[i]['y2'])
                z = 0.0
                                   
            a = ZAtom()
            a.coord = [x,y,z]
            trans = string.maketrans('a','a')
            a.symbol = string.capitalize(atomDict[i]['elementType'])
            #a.name = a.symbol + string.zfill(len(atomDict.keys())+1,2)
            a.name = a.symbol 

            model.atom.append(a)
        self.quick_mol_view([model])
        self.append_data(model)

        ###self.connect_model(model)

        return [model]

    def rdgamout(self,file,root):
        """ Read in the structures from a GAMESS-UK output file. This uses
            the reader in ccp1gui/gamessoutreader.py, which returns a list
            of molecules. In retrospect it may be better to sort this bit
            out of the reader and create a file to collect all the readers
            together.
        """
        
        r = GamessOutputReader(file)
        count = 1
        for model in r.molecules:
            if r.title:
                model.title = r.title
            else:
                model.title = "Mol from " + file
            if len(r.molecules) > 1:
                model.title = model.title + ' # ' + str(count)
            model.name = self.make_unique_name(root)
            self.quick_mol_view([model])
            self.append_data(model)
            self.connect_model(model)
            count = count + 1

        for vib in r.normalModes:
            self.append_data(vib)
            vib.name = self.make_unique_name(root,vib.title)

        if len( r.molecules ) == 0:
            return None
        else:
            return [ r.molecules ]

    def rdgamin(self,filename,root):
        """ Read a GAMESS-UK input file. Currently this only reads in the
            structure of the molecule and no calculation details. It parses
            the z-matrix into a list and then uses the ZMatrix method with the
            load from list method. If it encounters a geom field it assumes everything
            that follows is gamess cartesian format and reformats each string so that it
            can be handled by the list method.
        """
        print "Reading GAMESS-UK input file: %s" % filename

        # root is the default filename, file is the filename, not the file handle
        try:
            file  = open(filename,'r')        #The file descriptor
        except:
            print 'Error opening file: %s in rdgamin' % fileName
            return None
        
        # loop to find where the coordinate specification starts
        finished = 0
        while not finished:
            line = file.readline()
            if not line: # EOF so return 
                finished = 1
                return None
                break

            line = string.strip( line )
            line = string.lower( line )
            
            if line:
                fields = string.split( line )
            else:
                # ignore empty lines
                continue
            if ( fields[0][0:4] == "zmat" ):
                mode = 'z'
                finished = 1
            elif ( fields[0][0:4] == "cart" ):
                mode = 'x'
                finished = 1
            elif ( fields[0][0:4] == "geom"):
                # Check for NWChem input style
                if ( len(fields) == 3 and fields[2][0:4] == 'nwch'):
                    mode = 'n'
                else:
                    mode = 'x'
                finished = 1

        zmat_buffer = []

        # We should now be at the start of a line beginning with zmat or geom
        # Append the header line we just read:
        zmat_buffer.append( line )
        
#        if ( fields[0][0:4] == "zmat" ):# start
#            mode = 'z'
#        elif (fields[0][0:4] == "geom" ): # start but need to flag the mode
#            mode = 'x'
#             if ( len( fields ) > 1 ):
#                 if ( fields[1][0:4] == "angs" ):
#                     zmat_buffer.append( "coordinates angstrom" )
#                 elif ( fields[1][0:4] == 'bohr' or fields[1][0:4] == 'a.u.' or fields[1][0:4] == 'au' ):
#                     zmat_buffer.append( "coordinates bohr" )
#                 else:
#                     print "Unknown modifier for geometry directive!"
#                     print "Offending line is %s" % line
#                    zmat_buffer.append( "coordinates" )
#        else:
#            # shouldn't ever get here
#            print "Error reading GAMESS-UK input"
#           return 1

        # loop to read in the coordinates
        reading = 1
        while ( reading ):
            line = file.readline()

            if not line: # EOF so return 
                reading = 0
                print "ERROR! Encountered EOF while reading in coordinates from GAMESS-UK Input file!"
                return None
                break
        
            line = string.strip( line )
            line = string.lower( line )
            
            if line:
                # See if the line has commas in it, as GAMESS-UK supports this as a
                # separator as well as whitespace
                if re.compile(",").search( line ):
                    fields = string.split( line, ','  )
                    line = string.join( fields ) # Rejoin split line using space as separator
                else:
                    fields = string.split( line )                    
            else:
                # ignore empty lines
                continue

            if ( fields[0][0] == "#" or fields[0][0] == "?" ): # ignore comments
                continue
            elif ( fields[0][0:3] == "end" ): # stop
                zmat_buffer.append( "end" )
                reading = 0
            else:
                if mode == 'z':
                    zmat_buffer.append( line )
                elif mode == 'x': # reformat the line
                    cart_string = fields[4] + "\t" + fields[0] + "\t" \
                                  + fields[1] + "\t" + fields[2]
                    zmat_buffer.append( cart_string )
                elif mode == 'n':
                    # Reformat the string from NWChem input format
                    cart_string = fields[0] + "\t" + fields[2] + "\t" \
                                  + fields[3] + "\t" + fields[4]
                    zmat_buffer.append( cart_string )
                    

        #self.debug = 1
        if ( self.debug == 1 ):
            print "viewer/main.py: rdgamin read zmat_buffer:"
            for line in zmat_buffer:
                print "zmat: ",line

        # Now we've got a buffer with the coordinates, create the model
        model = Zmatrix( list = zmat_buffer )
        model.title = root
        model.name = self.make_unique_name(root)
        self.connect_model(model)
        self.quick_mol_view([model])
        self.append_data(model)

        return [model]
        
    def rddalout( self, filename, root ):
        """ Get the structures from a Dalton Output file
        """
        d = DaltonOutputReader( ofile = filename )
        molecules = d.get_molecules()

        if not molecules:
            return None
        
        count = 1
        for mol in molecules:
            if d.title:
                mol.title = d.title
            else:
                mol.title = "Mol from " + filename
            if len( molecules ) > 1:
                mol.title = mol.title + ' # ' + str(count)
            mol.name = self.make_unique_name(root)
            mol.connect()
            self.quick_mol_view([mol])
            self.append_data(mol)
            #self.connect_model(mol)
            count = count + 1
        return [ molecules ]


    def rdxyz(self,file,root):
        """ Read in cartesian coordinates in XMOL .xyz file format.
            The xyz format can contain multiple frames so we need to
            check if we have come to the end of one frame and need to
            start another
        """

        models = []
        finished = 0
        line = file.readline()
        while( not finished ): # loop to cycle over all the frames
            words = string.split(line)

            # First word specifies the number of atoms
            try:
                natoms = int(words[0])
            except:
                finished = 1
                break

            model = Zmatrix()
            model.title = root
            model.name = self.make_unique_name(root)

            line = file.readline() # First line is a comment so ignore it
            for i in range(natoms):
                line = file.readline()

                # Make sure we got something to read...
                if not line:
                    print "Error reading coordinates in rdxyz!"
                    finished = 1
                    break
                    
                # Check we are not at the end of the current frame
                words = string.split(line)
                if ( len( words ) != 4 ):
                    print "Error reading coordinates in rdxyz!"
                    print "Offending line is: %s" % line
                    break # jump out of for loop and start next cycle
                
                atsym = words[0]
                try:
                    x = float(words[1])
                    y = float(words[2])
                    z = float(words[3])
                    a = ZAtom()
                    a.coord = [x,y,z]
                    a.symbol = name_to_element( words[0] )
                    a.name = a.symbol + string.zfill(i+1,2)
                    model.atom.append(a)
                    # atno = Element.sym2no[atsym]
                except:
                    print "Error reading coordinates in rdxyz!"
                    print "Offending line is: %s" % line
                    break # jump out of for loop and start next cycle

            self.connect_model(model)
            self.quick_mol_view([model])
            self.append_data(model)
            models.append( model )

            line = file.readline() # Go back to top of while loop with next line

        if len( models ) == 0:
            return None
        else:
            return [ models ]

    def rdgjf(self,file,root):
        """Load a zmatrix from a Gaussian input file
        """
        line = file.readline()
        zmatrix=[]
        zmatrix.append('zmatrix angstrom')
        linecount = -1
        zmat=0 
        oldmode = ''
        while line:
            linecount = linecount+1
            line=string.lstrip(line)
            fields = string.split(line)
            if not zmat: #Clumsy check for charge/spin field before gaussian zmatrix
                if len(fields) == 2:
                    try:
                        int(fields[0])
                    except:
                        line=file.readline()
                        continue
                    try:
                        int(fields[1])
                        zmat = 1
                        line=file.readline()
                        continue
                    except:
                        line=file.readline()
                        continue
                else:
                    line = file.readline()
                    continue
            if zmat:
                if len(fields) == 1: #can add various keyword stuff here
                      if str(fields[0])[:4] == 'vari':
                            mode = 'vari'
                            line=file.readline()
                            continue
                elif len(fields) == 5:
                      mode = 'cart'
                elif len(fields) == 7:
                      mode = 'inte'
                elif len(fields) == 2:
                      mode = 'vari'

                if (mode == 'cart'):
                      if (oldmode != 'cart'):
                            zmatrix.append('cartesian')
                      zmatrix.append(fields[0]+' '+fields[2]+' '+fields[3]+' '+fields[4])
                      oldmode = 'cart'

                if mode == 'inte':
                      if (oldmode != 'inte'):
                            zmatrix.append('internal')
                      zmatrix.append(string.join(fields,' '))
                      oldmode = 'inte'

                if mode == 'vari':
                      if (oldmode != 'vari'):
                            zmatrix.append('variables')
                      zmatrix.append(string.join(fields,' '))
                      oldmode = 'vari'

            line = file.readline()

        zmatrix.append('end\n')
        model = Zmatrix(list=zmatrix)
        model.title = root
        model.name = self.make_unique_name(root)
        self.connect_model(model)
        self.quick_mol_view([model])
        self.append_data(model)
        return [model]

    def rdmol(self,file,root):
        """Read in a small molecule from a file in MDL .mol file format. This reader
        has been constructed from the information found at:
        http://www.eyesopen.com/docs/html/smack/node13.html
        If this reader doesnt work it is almost certainly THEIR problem not MINE...
        """

        # root is the default filename, file is the filename, not the file handle
        molname = root

        f = open( file, 'r' )

        #Header block contains 3 lines: name, info & a comment - only need the name if present
        line = string.strip( f.readline() )
        if line:
            molname = string.split(line)[0]

        # set up the model
        model = Zmatrix()
        model.title = molname
        model.name = self.make_unique_name(molname)

        # Skip the other two header lines
        f.readline()
        f.readline()

        # Now read in # of molecules and bonds
        line = f.readline()
        try:
            natoms = int( line[0:3] )
            nbonds = int( line[4:6] )
        except:
            print "Error reading in # of atoms and bonds in rdmol!"
            return

        # Now cycle over the atom block reading in the coordinates
        atom_count = 0
        while ( atom_count < natoms ):
            line = f.readline()
            if ( not line or ( len(line) < 39 )  ):
                print "Error reading in atoms in rdmol!"
                return
            try:
                x = float( line[0:9] )
                y = float( line[10:19] )
                z = float( line[20:29] )
                symbol = string.strip( line[31:33] )
                charge = int( line[35:37] )
            except:
                print "Error reading atom line in rdmol!"

            a = ZAtom()
            a.coord = [ x, y, z ]
            a.symbol = string.capitalize(symbol)
            a.name = a.symbol + string.zfill(atom_count+1,2)
            model.atom.append(a)
            atom_count += 1

        # Index the model or adding bonds wont work
        model.reindex()

        # Now read in the bond block
        bond_count = 0
        while ( bond_count < nbonds ):
            line = f.readline()
            if ( not line or ( len(line) < 9 )  ):
                print "Error reading in bonds in rdmol!"
                return
            try:
                i1 = int( line[0:3] )
                i2 = int( line[4:6] )
                bond_order = int( line[7:9] )
            except:
                print "Error reading bond line in rdmol!"

            atom1 = model.atom[i1-1] # Rem we index from 0 , they start at 1
            atom2 = model.atom[i2-1]
            model.add_bond( atom1, atom2 )
            bond_count += 1

        f.close()
        self.update_from_object(model)
        self.quick_mol_view([model])
        self.append_data(model)
        return [ model ]
    
    def rdvtk(self,file,root):
        """ Read in data contained in a vtk format file.
            This is currrently a pretty brain-dead hack
            that assumes we are reading in structured points
            with aligned axes.
        
         """
        import vtk

        print "Reading VTK File"
        
        # Instantiate the field object
        field = objects.field.Field()
        
        reader = vtk.vtkDataSetReader()
        reader.SetFileName(file)
        field.vtkdata = reader.GetStructuredPointsOutput()
        #field.data = reader.GetStructuredGridOutput()
       
        if not field.vtkdata:
            print "Error creating data object while reading vtk file!"
            return 1

        #print field.data
        field.title = root
        field.name = self.make_unique_name(root)
        self.append_data(field)
        
        return [field]
   
    def rdsmeagol(self,file,root,ext):
        """ Read in the ouptut of the smeagol programme
            This uses the reader defined in the file interfaces/smeagolreader.py
        """

        # file is the path to the file
        # root is the filename minus suffix
        # ext is the filname extension
        try:
            from interfaces.smeagolreader import SmeagolReader
        except e:
            print "Cannot import smeagolreader in main.py rdsmeagol!"
            print e
            return

        if ( ext == 'RHO' ):
            fstype = ext
        else:
            fstype = None

        #print "fstype is ",fstype

        # Instantiate the SmeagolReader
        smeagolreader = SmeagolReader()

        if ( fstype ):
            smeagolreader.read( file, ftype=fstype )
        else:
            smeagolreader.read( file )

        for o in smeagolreader.objects:
            # take the last field of the class specification
            t1 = string.split(str(o.__class__),'.')
            myclass = t1[len(t1)-1]
            print 'unique',root, o.title
            o.name = self.make_unique_name(root,o.title)
            print 'o.name is', o.name

            if myclass == 'Field' :
                self.append_data(o)
            else:
                print "Unknown class returned by smeagolreader!"

            return smeagolreader.objects
        

    def append_data(self, data):
        self.data_list.append(data)
        # Initially the callback list is empty
        self.editing_callbacks[id(data)] = {}

    def update_from_object(self, obj):
        """Update dependencies from object obj
        """

        if self.debug_callbacks:
            print 'update_from_object: ID=',id(obj)
            print 'Callbacks:',self.editing_callbacks

        # Run the callbacks
        try:
            callbacks = self.editing_callbacks[id(obj)]
            for k in callbacks.keys():
                if self.debug_callbacks:
                    print 'Running callback',k
                try:
                    callbacks[k]()
                except Exception:
                    print 'warning: update_from_object - callback failed',k

        except KeyError:
            if self.debug_callbacks:
                print 'update_from_object - no callbacks'

        # Replace all graphical representations of a given object
        t = id(obj)
        if self.debug:
            deb('vis_update of '+str(t))
            deb(str(self.vis_dict))

        try:
            visl = self.vis_dict[t]
        except KeyError:
            if self.debug:
                print 'update_from_object - no visualisers'
            return
        for v in visl:
            if self.debug:
                print 'update vis'
            v.Build()

    def delete_callback(self,object,key=None):
        """Helper function to remove a callback from the table
        """
        if self.debug_callbacks:
            if key:
                print 'Deleting callback key=',key,'obj=',object
            else:
                print 'Deleting all callbacks for',object

        t = self.editing_callbacks[id(object)]

        if key:
            keylist = [key]
        else:
            keylist = t.keys()

        for key in keylist:

            del t[key]

            if key[0:3] == 'ZME':
                # Also remove the zme_dict entry
                if self.debug_callbacks:
                    print 'Deleting zme_dict key=',id(object)
                try:
                    del self.zme_dict[id(object)]
                except KeyError:
                    print 'zme_dict entry missing??'

            if key[0:4] == 'CALC':
                # Also remove the calced_dict entry
                if self.debug_callbacks:
                    print 'Deleting calced_dict key=',id(object)
                try:
                    del self.calced_dict[id(object)]
                except KeyError:
                    print 'calced_dict entry missing??'

    def rdcrd(self,file,root,map=charmm_map):
        """Loader for CHARMM CRD format files"""

        t=CRDReader(None,filepointer=file,root=root,map=charmm_map)

        # SHOW THEM ALL
        for model in t.objects:
            model.name = self.make_unique_name(root)
            self.connect_model(model)
            self.quick_mol_view([model])
            self.append_data(model)
        return t.objects

    def wrtpdb(self,file,model):
        """PDB reader, based on Konrad Hinsens Scientific Python"""

        from Scientific.IO import PDB
        pdbf = PDB.PDBFile(file,mode='w')
        for atom in model.atom:
            d = { 'position': atom.coord, 'name' : atom.name }
            pdbf.writeLine('ATOM',d)

    def rdpdb(self,file,root,map=charmm_map):
        """PDB reader, based on Konrad Hinsens Scientific Python"""

        model = Zmatrix()
        model.title = root
        model.name = self.make_unique_name(root)

        from Scientific.IO import PDB

        conf = PDB.Structure(file)
        print conf
        i=0
        trans = string.maketrans('a','a')
        for residue in conf.residues:
            for atom in residue:
                #print atom
                atsym = atom.name

                x = atom.position[0]
                y = atom.position[1]
                z = atom.position[2]
                # atno = Element.sym2no[atsym]
                a = ZAtom()
                a.coord = [x,y,z]

                print atsym

                try:
                    # for newer versions of Scientific
                    a.symbol = atom['element']
                except KeyError:
                    try:
                        txt_type = string.strip(atsym)
                        txt_type = string.upper(txt_type)
                        print 'trying to map',atsym
                        a.symbol = map[txt_type]
                        print 'done',a.symbol
                        #a.name = a.symbol + string.zfill(i+1,2)
                    except KeyError:
                        a.symbol = string.translate(atsym,trans,string.digits)
                        a.symbol = string.capitalize(a.symbol)

                a.name = a.symbol + string.zfill(i+1,2)
                model.atom.append(a)
                #print 'get number', a.symbol, a.get_number()
                i=i+1

        self.connect_model(model)
        self.quick_mol_view([model])
        self.append_data(model)

        return [model]

    def rdcfg(self,file):
        print 'rdcfg'
        reader = Dl_PolyCONFIGReader()
        model = reader.scan(file)
        print 'result', model
        print 'result', model.list()
        self.connect_model(model)
        self.append_data(model)
        self.quick_mol_view([model])
        return [reader.model]

    def rdhist(self,file):
        print 'rdhist'
        reader = Dl_PolyHISTORYReader()
        models = reader.scan(file)
        for model in models:
            print 'result', model
            print 'result', model.list()
            self.connect_model(model)
            self.append_data(model)
            self.quick_mol_view([model])
        return models

    def rdcube(self,file):
        print 'rdcube'
        reader = CubeReader()
        (model,field) = reader.ParseFile(file)
        model.name = self.make_unique_name("Structure from " + file)
        field.name = self.make_unique_name("Grid from " + file)
        self.connect_model(model)
        self.append_data(model)
        self.quick_mol_view([model])
        self.append_data(field)
        return [model,field]

    def rdpun(self,file,root):

        """Punchfile reader"""
        p = PunchReader()
        p.scan(file)

        #if not p.title:
        #    p.title = self.get_title()
        #if p.title == "untitled":
        #    p.title = self.get_input("mol_name")

        # construct the results list for visualisation

        mols = []
        for o in p.objects:

            # take the last field of the class specification
            t1 = string.split(str(o.__class__),'.')
            myclass = t1[len(t1)-1]

            print 'unique',root, o.title
            o.name = self.make_unique_name(root,o.title)
            print 'o.name is', o.name

            if myclass == 'VibFreq' :
                self.append_data(o)

            elif myclass == 'Indexed' or myclass == 'Zmatrix':
                # will need to organise together with other results
                # assume overwrite for now

                self.append_data(o)

                # Used by visualisers
                #o.title = name
                #o.list()
                mols.append(o)

            elif myclass == 'Brick':
                self.append_data(o)

            elif myclass == 'Field':
                self.append_data(o)

        self.quick_mol_view(mols)

        if self.debug:
            print 'rdpun: data list', self.data_list

        return p.objects

    def rdjagout(self,file):

        patt_start = regex.compile('^ *Input geometry')
        while(1):
            line = file.readline()
            if not line: break

            n = patt_start.match(line)
            if n >= 0: break
        line = file.readline() #skip the "angstroms" line
        line = file.readline() #skip the "atom   x y z" line

        while(1):
            line = file.readline()
            if not line: break
            words = string.split(line)
            if len(words) < 4: break
            words = string.split(line)
            atsym = words[0]
            x = eval(words[1])
            y = eval(words[2])
            z = eval(words[3])
            # Need to write a converter to clean up the Jaguar labels
            realsym = Element.cleansym(atsym)
            atno = Element.sym2no[realsym]
            a = ZAtom()
            a.coord = [x,y,z]
            self.addatom(a)

        return

    def rdjag(self,file):
        print 'Reading from a Jaguar file is not yet implemented!'
        return

    def rdsys(self,file):
        while 1:
            line = file.readline()
            if not line: break
            words = string.split(line)
            if words[0] == 'atom' :
                atname = words[2]
                atno = Element.name2no[atname]
                x = eval(words[3])*0.52918
                y = eval(words[4])*0.52918
                z = eval(words[5])*0.52918
                at = ZAtom(x,y,z,atno)
                self.addatom(at)
        return

    def rdxbs(self,file):
        while 1:
            line = file.readline()
            if not line: break
            words = string.split(line)
            if not words: break
            if words[0] == 'atom' :
                atsym = words[1]
                atno = Element.sym2no[atsym]
                x = eval(words[2])
                y = eval(words[3])
                z = eval(words[4])
                a = ZAtom()
                a.coord = [x,y,z]
                a.symbol = atsym
                self.addatom(a)
        return

    def rdmsc(self,file):

        while 1:
            line = file.readline()
            if not line: break
            words = string.split(line)
            if not words: continue
            if words[0] == 'atomlist':
                self.rdmscatomlist(file)
            if words[0] == 'fraglist':
                self.rdmscfraglist(file)
            if words[0] == 'charge':
                self.charge = eval(words[1])
            if words[0] == 'spin':
                self.charge = eval(words[1])
            if words[0] == 'fragmentbuffersize':
                self.fragmentbuffersize = eval(words[1])
        return

    def rdmscatomlist(self,file):
        while 1:
            line = file.readline()
            if not line: break
            words = string.split(line)
            if not words: continue
            if words[0] == 'endatomlist': break
            sym = words[0]
            x = eval(words[1])
            y = eval(words[2])
            z = eval(words[3])
            num = Element.sym2no[sym]
            at = Atom(x,y,z,num)
            self.addatom(at)
        return            

    def rdmscfraglist(self,file):
        while 1:
            line = file.readline()
            if not line: break
            words = string.split(line)
            if not words: continue
            if words[0] == 'endfraglist': break
            for word in words:
                self.fraglist.append(eval(word))
        return            

    def ask_save_to_file(self):

        """Save molecule to file"""

        #calcdir = re.sub(r"[^\/\\:]*$","",self.filename)
        #name    = re.split(r"[\/\\:]",self.filename)
        #name    = name[len(name)-1]
        #if name == "":
        #name = self.calc.get_name()+".zmt"
        #name = "temp.zmt"
        
        mol = self.choose_mol()

        if not mol:
            return

        t = id(mol)
        try:
            name = self.file_dict[t]
        except KeyError:
            name=""

        ofile = tkFileDialog.asksaveasfilename(
            initialfile = name,
            initialdir = '.',
            filetypes=[("Punch File","*.pun"),
                       ("PDB","*.pdb"),
                       ("CML","*.cml"),
                       ("MSI","*.msi"),
                       ("CHARMM","*.crd"),
                       ("SHELX .RES","*.res"),
                       ("Zmatrix File","*.zmt")])

        if len(ofile):
            self.save_to_file(mol,ofile)

    def save_to_file(self,mol,ofile):
        """Save to file, GAMESS-UK punch or zmatrix format"""
        
        words2 = string.split(ofile,'/')
        name = words2[-1]
        words = string.split(name,'.')
        root = words[0]
        try:
            ext = words[1]
        except IndexError:
            msg = "No filename extension supplied!\n"+\
            "File will not be saved"
            self.error(msg)
            return
        print 'File',ofile
        print 'Extension',ext
        if ext == 'zmt':
            txt = mol.output_zmat()
            fobj = open(ofile,'w')
            for rec in txt:
                fobj.write(rec + '\n')
            fobj.close()
        elif ext == 'pun':

            # to handle extended structures, check for
            # need to output cell
            try:
                prim = mol.primitive_atom
                if len(prim) != len(mol.atom):
                    t = not self.query("Write out Cell Vectors?")
            except AttributeError:
                t = 0

            txt = mol.output_coords_block(exclude_cell=t)
            #print 'Output Text',txt
            fobj = open(ofile,'w')
            for rec in txt:
                fobj.write(rec + '\n')
            fobj.close()
        elif ext == 'pdb':
            self.wrtpdb(ofile,mol)
        elif ext == 'cml':
            mol.wrtcml(ofile,title=mol.name)
        elif ext == 'msi':
            mol.wrtmsi(ofile)
        elif ext == 'crd':
            mol.wrtcrd(ofile)
        elif ext == 'res':
            mol.wrtres(ofile)

    def make_unique_name(self,name,title=None):

        old_names = self.get_names()
        suf = []
        suf.append('')
        for i in range(1,1000):
            suf.append('['+str(i)+']')
        orig = name
        sname = name
        # first try the title, if provided
        if title:
            t = string.maketrans(' ','_')
            name = string.translate(string.strip(title),t)
            sname = name
        else:
            name = orig
        try:
            index = old_names.index(name)
        except ValueError:
            return name

        # try a combination of name and title
        if title:
            t = string.maketrans(' ','_')
            name = orig + '.' + string.translate(string.strip(title),t)
            sname = name
            try:
                index = old_names.index(name)
            except ValueError:
                return name

        # finally append a suffix
        for s in suf:
            name = sname + s
            try:
                index = old_names.index(name)
            except ValueError:
                return name

    def connect_model(self,model,all=0):
        """Update connectivity for a structure and redisplay
        """
        if all:
            undo = []
            for d in self.data_list:
                t1 = string.split(str(d.__class__),'.')
                myclass = t1[len(t1)-1]
                if myclass == 'Indexed' or myclass == 'Zmatrix':
                    # NEED TO UPDATE BOND before this
                    d.update_bonds()
                    undo.append (lambda obj = d, oldc=d.bond: obj.apply_connect(oldc))
                    undo.append (lambda s = self, obj = d: update_from_object(obj))
                    d.connect(scale=self.conn_scale,toler=self.conn_toler)
                    self.update_from_object(d)
                self.undo_stack.append(undo)
        else:
            undo = []
            model.update_bonds()
            # NEED TO UPDATE BOND before this will work
            undo.append (lambda obj = model, oldc=model.bond: obj.apply_connect(oldc))
            undo.append (lambda s = self, obj = model: s.update_from_object(obj))
            self.undo_stack.append(undo)
            model.connect(scale=self.conn_scale,toler=self.conn_toler)
            self.update_from_object(model)

    def extend_model(self,model,all=0):
        """Generate a number of cells from the primitive cell
        contents
        """

        models = []
        if all:
            for d in self.data_list:
                t1 = string.split(str(d.__class__),'.')
                myclass = t1[len(t1)-1]
                if myclass == 'Indexed' or myclass == 'Zmatrix':
                    models.append(d)
        else:
            models = [model]

        for model in models:
            if len(model.cell) != 3 and len(model.cell) !=2 :
                self.error('cant extend '+model.name+' .. system is not periodic')
                return

        if len(models) == 0:
            self.warn('nothing to extend')
            return

        res = self.extend_dialog.activate()

        if res == 'OK':
            minx = int(self.extend_dialog.minx.get())
            maxx = int(self.extend_dialog.maxx.get())
            miny = int(self.extend_dialog.miny.get())
            maxy = int(self.extend_dialog.maxy.get())
            minz = int(self.extend_dialog.minz.get())
            maxz = int(self.extend_dialog.maxz.get())
        else:
            return

        if model in models:
            model.extend(minx,maxx,miny,maxy,minz,maxz)
            self.connect_model(model)
            # update_from_model skipped as there is a call at end of connect_model

    def delete_obj(self,model0,all=0):
        """Delete the model and all it representations
        """
        if all:
            deadmen=copy.copy(self.data_list)
        else:
            deadmen=[model0]

        for model in deadmen:
            # data list
            self.data_list.remove(model)
            # visualisers
            t = id(model)
            if self.vis_dict.has_key(t):
                for v in self.vis_dict[t]:
                    print 'deleting rep'
                    self.vis_list.remove(v)
                    v.Delete()
                del self.vis_dict[t]

            # destroy zme and calced instances
            # this should clear the relevant callbacks

            if self.zme_dict.has_key(t):
                self.zme_dict[t].Quit()

            if self.calced_dict.has_key(t):
                for ed in self.calced_dict[t]:
                    ed.Close()

            del model

        self.update()

    def gamessuk_calced(self,obj=None):
        c = GAMESSUKCalc(mol=obj)
        self.edit_calc(c)

    def molpro_calced(self,obj=None):
        c = MOLPROCalc(mol=obj)
        self.edit_calc(c)

    def dalton_calced(self,obj=None):
        c = DALTONCalc(mol=obj)
        self.edit_calc(c)

    def chemshell_calced(self,obj=None):
        c = ChemShellCalc(mol=obj)
        self.edit_calc(c)

    def dlpoly_calced(self,obj=None):
        c = DLPOLYCalc(mol=obj)
        self.edit_calc(c)

    def mopac_calced(self,obj=None):
        c= MopacCalc(mol=obj)
        self.edit_calc(c)

    def mndo_calced(self,obj=None):
        c= MNDOCalc(mol=obj)
        self.edit_calc(c)

    def choose_mol(self):

        mol_list = self.get_names(molecules_only=1)
        if len(mol_list) == 0:
            #
            # No molecules present ??? 
            #
            message_text = "No molecules to choose from present in viewer.\n" + \
                           "Please load a structure and retry."
            self.error(message_text)
            raise EditError,"No molecular structures present!"
        elif len(mol_list) == 1:
            #
            # Select the 1 molecule present...
            #
            mol_name = mol_list[0]
        else:
            #
            # Bring up a selection widget
            #
            self.result = Tkinter.StringVar()
            self.dialog = Pmw.Dialog(self.master,
                                     buttons = ('OK','Cancel'),
                                     title = 'Select Molecule',
                                     command = self.__StoreResult)
            self.var = Tkinter.StringVar()
            self.dialog.mol = Pmw.OptionMenu(
                self.dialog.interior(),
                labelpos = 'n', 
                label_text="Please select a molecular\nstructure "+
                "from the list",
                menubutton_textvariable = self.var,
                items = mol_list,
                initialitem = mol_list[0])
            self.dialog.mol.pack(fill='both')
            self.dialog.activate()
            if self.result.get() == 'OK':
                mol_name = self.var.get()
            else:
                raise EditError,"No molecular structure selected!"

        print 'mol_name',mol_name
        print 'data list', self.data_list

        for d in self.data_list:
            t1 = string.split(str(d.__class__),'.')
            myclass = t1[len(t1)-1]
            print 'class', myclass
            if myclass == 'Indexed' or myclass == 'Zmatrix':
                print 'check name ', d.name
                if mol_name == d.name:
                    t = d;
        return t


    def __StoreResult(self,option):
        """Store the name of the pressed button and destroy the 
           dialog box."""
        self.result.set(option)
        self.dialog.destroy()

    def edit_calc(self,calc):
        """Open an editor for a given calculation
        Also ensures correct handling of the target structure
        """
        obj = calc.get_input("mol_obj")
        if obj in self.data_list:
            print 'obj already loaded'
        else:
            print 'loading new obj'
            self.quick_mol_view([obj])
            self.append_data(obj)
            
        tt = id(obj)

        # First define a unique string to key the callback
        count = 1
        while 1:
            callback_key = 'CALC'+str(count)+'.'+str(id(obj))
            if self.editing_callbacks[id(obj)].has_key(callback_key):
                count = count + 1
            else:
                break
        if self.debug_callbacks:
            print 'Callback key is ',callback_key

        # Jens hack - have added the balloon keyword to get the main balloon passed through
        # so that the control in the main window works in the calc editor - not sure
        # if this is sensible though.
        ed = calc.edit(self.master,self,
                      vis=self.vis_dict[tt],
                      job_editor=self.job_editor,
                      reload_func= lambda s=self,t=str(id(obj)) : s.load_from_graph(t),
                      update_func= lambda o,s=self,t=str(id(obj)) : s.update_model(t,o),
                      on_exit=lambda s=self,k=callback_key,o=obj : s.delete_callback(o,k),
#                      balloon=self.__balloon )
                      balloon=self.balloon )
        if ed:
            try:
                ed.Show()
            except RuntimeError,exception:
                pass

            if self.calced_dict.has_key(id(obj)):
               self.calced_dict[id(obj)].append(ed)
            else:
               self.calced_dict[id(obj)] = [ed]

            self.editing_callbacks[id(obj)][callback_key] =  lambda editor=ed: editor.Reload()

    def undo(self):
        print 'undo stack',len(self.undo_stack)
        cmds = self.undo_stack.pop()
        print 'undo stack now',len(self.undo_stack)
        print 'executing',len(cmds),'steps'
        for c in cmds:
            c()
            
    def edit_coords(self,i):

        # First define a unique string to key the callback
        callback_key = 'ZME.'+str(id(i))
        if self.editing_callbacks[id(i)].has_key(callback_key):
            self.warn('This structure is already being edited!!')
            return

        if self.debug_callbacks:
            print 'Callback key is ',callback_key

        #print 'on edit',len(i.bond),len(i.atom[0].coord)

        e = ZME(self.master,reload_func= lambda s=self,t=str(id(i)) : s.load_from_graph(t),
                update_func= lambda o,s=self,t=str(id(i)) : s.update_model(t,o),
                export_selection_func = lambda mol,atoms,s=self :  s.select_from_zme(mol,atoms),
                import_selection_func = lambda mol,s=self :  s.provide_selection_to_zme(mol),
                on_exit=lambda s=self,k=callback_key,o=i : s.delete_callback(o,k))

        self.editing_callbacks[id(i)][callback_key] =  lambda editor=e: editor.Reload()
        self.zme_dict[id(i)] = e

    def select_from_zme(self,mol,atoms):
        """When an atom is selected in the zmatrix editor this function
        should cause the selection to be visible in the graphics window"""

        sel = self.sel()
        if len(atoms):
            if self.debug_selection:
                print 'upd sel',atoms
            sel.clear()
            sel.add(mol,atoms)
            self.update()

    def provide_selection_to_zme(self,mol):
        """When an atom is selected in the zmatrix editor this function
            should cause the selection to be visible in the graphics window"""
        sel = self.sel()
        return sel.get_by_mol(mol)

    def new_coords(self):
        # Start with a single atom
        i = Zmatrix()
        new = ZAtom()
        new.symbol = 'C'
        new.name   = 'C'
        i.insert_atom(0,new)
        self.new_molecule_index = self.new_molecule_index + 1
        i.title = 'New' + str(self.new_molecule_index)
        i.name = 'new' + str(self.new_molecule_index)

        #label='new'
        #cmd.load_model(i,label)
        #cmd.enable(label)

        # this is to handle the bug in windows which means a single
        # point doesn't show up
        i.hybridise(new,'sp3')

        self.append_data(i)
        vis = self.quick_mol_view([i])
        # We will need the editing tools
        self.toolwidget.show()

    def open_calc(self):
        """Open a calculation from a file"""

        #   initialdir = self.calcdir,

        ofile = tkFileDialog.askopenfilename(
            initialdir=self.user_directory,
            filetypes=[("Calc File","*.clc"),] )

        if len(ofile):
            fobj = open(ofile,'r')
            u = pickle.Unpickler(fobj)
            obj = u.load()
            fobj.close()
            self.edit_calc(obj)

    def about(self):
        """ """
        d=SimpleDialog(self.master, 
                title='About the CCP1 GUI Tk Viewer widget', 
                text='      CCP1 GUI Tk Viewer widget version 0.8  \n\n'
                     '       by Paul Sherwood, Huub van Dam and \n'
                     '                    Jens Thomas\n' 
                     '  http://www.cse.clrc.ac.uk/qcg/ccp1gui, 2004.\n\n'
                     '         Daresbury Laboratory\n',
                buttons= ['Close',],
                cancel=0)
        # copied from simpledialog source file, stops app exiting
        # on dialog close
        d.go()

    def edit_grid(self,i):
        """ Open a grid editor """

        if i.data:
            if not self.query("This will trash the data, Proceed?"):
                return

            i.data = None

        try:
            x = self.grid_vis
        except AttributeError:
            self.grid_vis = None

        window=GridEditor(self.master, i,
                          command=self.view_grid,
                          exitcommand=self.done_view_grid)
        window.show()

    def view_grid(self, field):
        """ callback for the grid editor to enable the grid to be visualised
        as it is being edited
        """
        # Create the image if not already active
        if not self.grid_vis:
            t = id(field)
            self.grid_vis = self.grid_visualiser(self.master,self,field)
            self.vis_dict[t] = [self.grid_vis]
            self.grid_vis.Show()

        self.grid_vis.Build()

    def done_view_grid(self, field):
        """ remove the image of the grid"""
        t = id(field)
        vis = self.vis_dict[t][0]
        vis.Hide()

    #
    # Support for CCP1 quantum chemistry interface
    #
    # get_names        returns the list of objects
    # load_from_graph  returns a molecule given its name
    #

    def get_names(self,molecules_only=0):
        list = []
        for d in self.data_list:
            t1 = string.split(str(d.__class__),'.')
            myclass = t1[len(t1)-1]
            if (not molecules_only) or (myclass == 'Indexed' or myclass == 'Zmatrix'):
                list.append(d.name)
        return list

    def load_from_graph(self,name):
        """return a structure from the viewer
        the second argument (name) should actually be the string form
        of the python id
        """
        print 'viewer: load_from_graph',name
        for d in self.data_list:
            t1 = string.split(str(d.__class__),'.')
            myclass = t1[len(t1)-1]
            if myclass == 'Indexed' or myclass == 'Zmatrix':
                #if name == d.name or name == str(id(d)):
                #    return d
                if name == str(id(d)):
                    return d
        self.warn('internal error: load failed')

    def update_model(self,name,obj):
        """Update a structure in the viewer
        From October 03, name is replaced by the python object id
        However, the name mapping is retained for compatibility
        with pymol
        """
        tobj = None
        if self.debug:
            print 'viewer: update_model',name

        # Look for a structure with the matching name
        for d in self.data_list:
            t1 = string.split(str(d.__class__),'.')
            myclass = t1[len(t1)-1]
            if myclass == 'Indexed' or myclass == 'Zmatrix' :
                if self.debug:
                    print 'Name check in viewer',d.name
                if name == d.name or name == str(id(d)):
                    tobj = d;

        if not tobj:
            self.warn("internal error in update of " +  name)
            return
        elif tobj == obj:
            # found it
            self.update_from_object(obj)
        else:
            print '   Replacing object contents'
            newd = []
            copycontents(tobj, obj)
            self.update_from_object(tobj)

    def import_objects(self,objects):
        """Provided to allow calculation editors to load
        data into the viewer

        All objects are assumed to have a name attribute which must
        be unique to allow it to be used to identify objects when returned from
        menus.

        Needs some more design work!!!
        """
        for o in objects:
            try:
                dum = o.get_name()
                if not dum:
                    dum = "None"
            except:
                dum = "???"
            o.name = self.make_unique_name(dum)
            self.append_data(o)
                    
    def import_objects_info(self,objects):
        """Provided to allow calculation editors to load
        data into the viewer
        This version pops up a dialog
        Needs some more design work!!!
        """
        txt = "Objects from calculation:\n"
        for o in objects:
            self.append_data(o)
            #
            # need to make a unique name
            #
            try:
                txt = txt + o.title + "\n"
            except AttributeError:
                txt = txt + "????\n"
            except:
                print 'Other error'
                txt = txt + "????\n"
                
        self.info(txt)

    def get_selection(self,name):
        """Load the selected atoms from molecule name"""
        #PS still work to do here to replace use of name with object id
        for d in self.data_list:
            t1 = string.split(str(d.__class__),'.')
            myclass = t1[len(t1)-1]
            if myclass == 'Indexed' or myclass == 'Zmatrix':
                if name == d.name:
                    mol = d
        if not mol:
            print 'no matching mol',name
            return ""

        sel = self.sel()
        return sel.get_by_mol(mol)

    def set_selection(self,name,atoms):
        """Set the current selection, using a list of atoms"""
        #PS still work to do here to replace use of name with object id
        print 'set_selection',name,atoms
        for d in self.data_list:
            t1 = string.split(str(d.__class__),'.')
            myclass = t1[len(t1)-1]
            if myclass == 'Indexed' or myclass == 'Zmatrix':
                if name == d.name:
                    mol = d

        if not mol:
            print 'no matching mol'
            return

        sel = self.sel()
        sel.clear()
        sel.add(mol,atoms)
        self.update()

    def map_names(self,mol,names):
        """Translate from a string containing names to atoms
        In this implementation the names are the integer labels
        counting from 1 (potentially dangerous)
        """
        res = []
        for txt in string.split(names):
            res.append(mol.atom[int(txt) - 1])
        return res

    def atom_names(self,atoms,exclude_dummies=0):
        """return a list of unique names to identify the atoms"""
        res = ""
        print 'atoms in atom_names', atoms
        for a in atoms:
            if exclude_dummies:
                res = res + str(a.get_index2() + 1) + " "
            else:
                res = res + str(a.get_index() + 1) + " "
        return res

    def get_angle(self,p1,p2,p3):

        r1 = cpv.distance(p1,p2)
        r2 = cpv.distance(p2,p3)
        r3 = cpv.distance(p1,p3)

        small = 1.0e-10
        cnv   = 57.29577951

        if r1 + r2 - r3 < small:
            # printf("trig error %f\n",r3-r1-r2)
            # This seems to happen occasionally for 180 angles 
            theta = 180.0
        else:
            theta = cnv*math.acos( (r1*r1 + r2*r2  - r3*r3) / (2.0 * r1*r2) )

        return theta;


    def get_dihedral(self,p1,p2,p3,p4):

        cnv=57.29577951

        vec_ij = cpv.sub(p1, p2)
        vec_kj = cpv.sub(p3, p2)
        vec_kl = cpv.sub(p3, p4)

        # vec1 is the normal to the plane defined by atoms i, j, and k    
        vec1 = cpv.cross_product(vec_ij,vec_kj)
        magvec1 = cpv.dot_product(vec1,vec1)

        #  vec2 is the normal to the plane defined by atoms j, k, and l
        vec2 = cpv.cross_product(vec_kl,vec_kj)
        magvec2 = cpv.dot_product(vec2,vec2)

        # the definition of a dot product is used to find the angle between  
        # vec1 and vec2 and hence the angle between the planes defined by    
        # atoms i, j, k and j, k, l                                          
        #                                                                    
        # the factor of pi (180.0) is present since when we defined the      
        # vectors vec1 and vec2, one used the right hand rule while the      
        # other used the left hand rule                                      

        dotprod = cpv.dot_product(vec1,vec2)
        #print magvec1, magvec2
        #print type(magvec1), type(magvec2)
        fac = dotprod / math.sqrt(magvec1*magvec2)
        if(fac > 1.0):
            fac = 1.0
        if(fac < -1.0):
            fac = -1.0
        dihed = 180.0 - cnv * math.acos(fac )

        # the dot product between the bond between atoms i and j and the     
        # normal to the plane defined by atoms j, k, and l is used to        
        # determine whether or not the dihedral angle is clockwise or        
        # anti_clockwise                                                     
        #                                                                    
        # if the dot product is positive, the rotation is clockwise          

        sign_check = cpv.dot_product(vec_ij,vec2)
        if( sign_check > 0.0):
            dihed = dihed * -1.0

        return dihed

    def list_contacts(self,model):
        """Output a list of the contacts to the gui's python terminal 
        """
        print 'Contacts for ',model.title
        sel = self.sel()
        sel = sel.get()
        tt = {}
        obj = {}
        for mol,atom in sel:
            if not tt.has_key(id(mol)):
                tt[id(mol)] = []
                obj[id(mol)] = mol
            tt[id(mol)].append(atom)
        for k in tt.keys():
            l = []
            for a in tt[k]:
                l.append(a.get_index())
            obj[k].find_contacts(contact_scale=self.contact_scale,contact_toler=self.contact_toler,pr=1,list=l)

    def list_model(self,model):
        """Bring up an editor to list the bond lengths and angles with a list of the coordinates.
        """
        data=[]
        data.append('Listing of %s\n' % model.title)
        data.append('Atoms\n')
        for a in model.atom:
            txt = ''
            try:
                for b in a.conn:
                    txt = txt + '%d ' % (b.get_index() + 1) 
            except AttributeError:
                pass
            data.append('%3d  %2s  %-6s  %10.4f %10.4f %10.4f   %8.3f  %s\n' % ( a.get_index()+1,  a.symbol, a.name,  a.coord[0],a.coord[1],a.coord[2], a.partial_charge, txt))
        self.infoeditor = Editor(self.interior(),title="Model List",data=data)
        return
            
    def list_geom(self,model):
        """List all the bonds and angles in this moleclue in an editor
        """
        data=[]
        data.append('Geometrical Info for %s\n' % model.title)
        for t in model.bonds_and_angles():
            data.append(t+"\n")
        self.infoeditor = Editor(self.interior(),title="Geometry List",data=data,directory=self.user_directory)

    def ask_watch_file(self):
        """Ask for a file to monitor for appended data"""
        file=askopenfilename(
            defaultextension='',
            initialdir=self.user_directory,
            filetypes=[('Molecules','.c'),
                       ('All', '*')])
        if not file:
            return

        words2 = string.split(file,'/')
        name = words2[-1]
        words = string.split(name,'.')
        root = words[0]

        p = PunchReader()

        p.scan(file)
        for o in p.objects:

            # take the last field of the class specification
            t1 = string.split(str(o.__class__),'.')
            myclass = t1[len(t1)-1]

            o.name = self.make_unique_name(root,o.title)

            if myclass == 'VibFreq' :
                self.append_data(o)

            elif myclass == 'Indexed' or myclass == 'Zmatrix':
                # will need to organise together with other results
                # assume overwrite for now
                self.append_data(o)
                self.quick_mol_view([o])

        self.__update_data_list()

        # create the Lock
        self.lock  = threading.RLock()
        # Create the queues
        self.queue1 = Queue.Queue()
        self.queue2 = Queue.Queue()

        self.periodicCall()
        self.watcher = SlaveThread(self.lock, self.queue1 ,self.upd_from_watch)
        self.watch_obj = o
        self.watch_reader = p
        self.watch_file=file
        self.mtime=os.stat(self.watch_file)[stat.ST_MTIME]

        try:
            self.watcher.start()
            self.watch_dialog.activate(globalMode = 'nograb')
        except RuntimeError,e:
            self.gui.error.configure(message_text = str(e))
            self.gui.error.activate()

    def end_watcher(self,event):
        self.watch_dialog.deactivate()
        self.queue2.put(999)
        
    #
    # This is executed in the slave thread
    #
    def upd_from_watch(self):
        if self.queue2.qsize():
            try:
                code = self.queue2.get()
                print 'watcher queue:', code
                if code ==999:
                    return 99
            except Queue.Empty:
                print 'empty'
                pass

        mtime = os.stat(self.watch_file)[stat.ST_MTIME]
        #print 'mtime',mtime
        if mtime != self.mtime:
            self.watch_reader.rescan(self.watch_file,object=self.watch_obj)
            self.mtime = mtime
            return 2
        else:
            return 0
    #
    # Stuff to handle slave threads, see jobman.py
    #
    def periodicCall(self):
        """
        Check every 100 ms if there is something new in the queue.
        """
        self.processIncoming()
        self.after(100, self.periodicCall)

    def processIncoming(self):
        """
        Handle all the messages currently in the queue (if any).
        """
        while self.queue1.qsize():
            try:
                msg = self.queue1.get(0)
                # Check contents of message and do what it says
                # As a test, we simply print it
                #print 'Queue get',msg
                if msg ==0: 
                    pass
                elif msg == 1:
                    pass
                elif msg == -1:
                    pass
                elif msg == 2:
                    # The file has changed
                    self.update_from_object(self.watch_obj)

            except Queue.Empty:
                print 'empty'
                pass

    def atom_info(self,mol,i):
        print 'mol: ',mol.title
        a = mol.atom[i]
        print 'atom:',i+1, a.name
        print 'posn:',a.coord
        print 'pchg:',a.partial_charge
        try:
            c = a.conn
        except AttributeError:
            c = []
        for t in c:
            print 'conn:',t.get_index()+1, t.name, distance(a.coord, t.coord)
        for t in c:
            for tt in c:
                if tt.get_index() >  t.get_index():
                    print '          ',t.get_index()+1, a.get_index()+1, tt.get_index()+1, \
                          self.get_angle(t.coord,a.coord, tt.coord)

    def measure_selection(self):
        selection = self.sel().get_ordered()
        #print selection
        if len(selection) >= 2:
            mol4,atom4 = selection[-1]
            mol3,atom3 = selection[-2]
            i3 = atom3.get_index() + 1
            i4 = atom4.get_index() + 1
            print 'Distance (', i3, ',',i4,') = ', mol4.get_distance(atom4,atom3)
        if len(selection) >= 3:
            mol2,atom2 = selection[-3]
            i2 = atom2.get_index() + 1
            #print 'Distance (', i2, ',',i3,') = ', mol4.get_distance(atom3,atom2)
            print 'Angle    (', i4,',',i3,',',i2,') =',mol2.get_angle(atom4,atom3,atom2)
        if len(selection) >= 4:
            mol1,atom1 = selection[-4]
            i1 = atom1.get_index() + 1
            #print 'Distance (', i1, ',',i2,') = ', mol4.get_distance(atom2,atom1)
            #print 'Angle (', i3,i2,i1,') =',mol2.get_angle(atom3,atom2,atom1)
            print 'Torsion  (',i4,',',i3,',',i2,',',i1,') =',mol2.get_dihedral(atom4,atom3,atom2,atom1)
    #
    # -------------  Animation Controls -------------------
    #

    def select_ani_images(self):
        """ Pop up the widget to select the images for an animation:
            Create the scene widget if it doesn't already exists.
            Regenerate the list of objects and refresh the widget if it does.
        """

        print 'start'
        if not self.ani_image_widget:
            from objects import selector
            print 'sel'
            self.ani_image_widget = selector.Selector( self.master, self )
            print 'show'
            self.ani_image_widget.show()
        else:
            print "self.ani_image_widget is ",str(self.ani_image_widget)
            self.ani_image_widget.refresh()
            self.ani_image_widget.show()

        print 'done'
        
    def ask_save_movie(self):
        """ The use has clicked on the button to save a movie
        """
        self.save_movie_dialog.show()

    def ani_reset(self):
        """ Build up a fresh animation list
            ani_list is a list of the images for the animation - stored
            in the order they will be shown.
        """
        # Build up a fresh animation list
        self.new_ani_list()

        # Redraw the selector
        if self.ani_image_widget:
            self.ani_image_widget.refresh()

        # Redraw the main window
        self.ani_refresh()

    def new_ani_list(self):
        """Generate a fresh ani_list from the objects in the data_list
           that have representations.
        """
        self.ani_list = [] 
        if len( self.data_list ):
            for obj in self.data_list:
                t = id(obj)
                try:
                    visl = self.vis_dict[t]
                    for vis in visl:
                        #if vis.IsShowing():
                        self.ani_list.append( vis )
                except KeyError:
                    # No representation so just pass
                    pass
            

    def ani_refresh(self):
        """ Reset the main window so that is clears out all images showing
            and displays the first one in the ani_list
        """
        print 'ani_refresh'
##         for obj in self.data_list:
##             t = id(obj)
##             print 'ani_refresh loop'
##             try:
##                 visl = self.vis_dict[t]
##                 for vis in visl:
##                     vis.Hide()
##             except KeyError:
##                 pass

        for v in self.vis_list:
            if v.IsShowing():
                v.Hide()

        #self._ani_hide_all()
        self.frame_no = 0
        print '_ani_show'
        if self._ani_show():
            print 'update'
            self.update()
            
    def ani_rew(self):
        """ Go to the first frame of the animation and display the image
        """
        self.frame_no = 0
        self._ani_hide_all()
        if self._ani_show():
            self.update()
        
    def ani_end(self):
        """ Go to the last frame of the animation and display the image.
        """
        lani = len(self.ani_list)
        if lani <= 1:
            print "ani_end: only one or no frames to display"
        else:
            self.frame_no = lani - 1
            self._ani_hide_all()
            if self._ani_show():
                self.update()

    def ani_bak(self):
        """ Step back a single frame in the animation
        """

        # Need to initialise frame_no if the animation toolbar was
        # open when objects were read in
        try:
            tmp = self.frame_no 
        except:
            self.frame_no = 0
            
        if self.frame_no > 0:
            self._ani_hide()
            self.frame_no -= 1
            if self._ani_show():
                self.update()
        else:
            #self.error( " Already at the start of animation.\nI can\'t go any further back!" )
            print " Already at the start of animation.\nI can\'t go any further back!"
            return
        #self._ani_show()

    def ani_fwd(self):
        """ Step forward a single frame in the animation
        """
        # Need to initialise frame_no if the animation toolbar was
        # open when objects were read in
        try:
            tmp =  self.frame_no
        except:
            self.frame_no = 0
            
        if self.frame_no < ( len(self.ani_list)-1 ):
            self._ani_hide()
            self.frame_no = self.frame_no+1
            if self._ani_show():
                self.update()
            #self.update()
        else:
            #self.error( " Already at the end of animation.\nI can\'t go any further forward!" )
            print " Already at the end of animation.\nI can\'t go any further forward!"
            return
    
    def ani_stop(self):
        """ Stop the animation
        """
        self.ani_stop = 1

    def ani_play(self):
        """ Play through the sequence of images from self.frame_no to the end
        """

        # Need to initialise frame_no if the animation toolbar was
        # open when objects were read in
        try:
            tmp =  self.frame_no
        except:
            self.frame_no = 0

        # If the ani_list is empty reset
        if len ( self.ani_list ) == 0 :
            self.ani_reset()
            #return

        # Go back to the start if we're at the end
        if (  self.frame_no == len( self.ani_list )-1  ):
            self._ani_hide()
            self.frame_no = 0

        # Display the current frame
        if self._ani_show():
            self.update()
            time.sleep(0.2)
        
        self.ani_stop = 0
        while ( self.frame_no <= len(self.ani_list)-2 ):

            print 'Frame:',self.frame_no
            self.interior().update()
            if self.ani_stop:
                return
            self._ani_hide()
            self.frame_no += 1
            if self._ani_show():
                self.update()
                time.sleep(0.2)

    def _ani_hide(self):
        """ Hide the current image as defined in self.frame_no
        """
        try:
            vis = self.ani_list[self.frame_no]
            vis._hide()
            # Hack so the view menu display what is showing/hidden
            vis.is_showing = 0
            #vis.Hide()
            #self.update()
        except IndexError:
            print "ani_hide: nothing to hide"
            pass

    def _ani_hide_all(self):
        """ Hide all the images in the animation list
        """
        for vis in self.ani_list:
            try:
                vis._hide()
                # Hack so the view menu display what is showing/hidden
                vis.is_showing = 0
            except IndexError:
                pass
            #self.update()

    def _ani_show(self):
        """ Show the image as specified by the current frame number.
            Return 1 if we have an image to show, None if not
        """
        try:
            print 'show',self.frame_no
            vis = self.ani_list[ self.frame_no ]
            vis._show()
            # Hack so the view menu display what is showing/hidden
            vis.is_showing = 1
#            vis.Show()
            #self.update()
            #print '_ani_show frame #',self.frame_no
            return 1
        except IndexError:
            print "ani_show: nothing to show"
            return None
            
                    
    #------------- messages -----------------------------

    def build_msg_dialog(self):
        """Message information"""
        dialog = Pmw.MessageDialog(self.master, 
                                   title = 'Information',
                                   iconpos='w',
                                   icon_bitmap='info',
                                   defaultbutton = 0)
        dialog.withdraw()
        self.msg_dialog  = dialog

    def info(self,txt):
        dialog = self.msg_dialog
        dialog.configure(message_text=txt)
        dialog.component('icon').configure(bitmap='info')
        dialog.configure(title="CCP1 GUI Information")
        dialog.activate()

    def warn(self,txt):
        dialog = self.msg_dialog
        dialog.configure(message_text=txt)
        dialog.configure(title='CCP1 GUI Warning')
        dialog.component('icon').configure(bitmap='warning')
        dialog.activate()

    def error(self,txt):
        dialog = self.msg_dialog
        dialog.configure(message_text=txt)
        dialog.configure(title='CCP1 GUI Error')
        dialog.component('icon').configure(bitmap='error')
        dialog.activate()


    #------------- yes/no questions --------------------------

    def build_query_dialog(self):
        self.query_dialog =  Pmw.MessageDialog(self.master,
                                               title = "Query:",
                                               iconpos='w',
                                               icon_bitmap='question',
                                               buttons = ("Yes","No"),
                                               command = self.__QueryResult)
        self.query_dialog.withdraw()


    def query(self,txt):
        self.dialogresult = 'Zzz'
        dialog = self.query_dialog
        dialog.configure(message_text=txt)
        dialog.configure(title='CCP1 GUI Query')
        dialog.component('icon').configure(bitmap='question')
        dialog.activate()
        if self.query_result == 'Zzz':
            print 'Problem'
        elif self.query_result == 'Yes':
            return 1
        else:
            return 0

    def __QueryResult(self,result):
        """Pmw silliness, need to get the result of a query. 
            Have to have a routine to store the result and remove the 
            window (sigh)."""
        print '__QueryResult',result
        self.query_result = result
        self.query_dialog.deactivate()


    #------------- watch -----------------------------

    def build_watch_dialog(self):
        self.watch_dialog = Pmw.Dialog(self.master,
                                 buttons = ('End',),
                                 title = 'Select Molecule',
                                 command = self.end_watcher)
        self.watch_dialog.withdraw()
        
    #------------- help -----------------------------

    def build_help_dialog(self):

        #fixedFont = Pmw.logicalfont('Courier',size=12)
        #text_font=("Courier", 10, "normal"),
        dialog = Pmw.TextDialog(self.master, scrolledtext_labelpos = 'n',
                                title = 'Help',
                                defaultbutton = 0,
                                text_bg = 'white',
                                label_text = '')
        dialog.withdraw()
        self.help_dialog  = dialog

    def open_help_dialog(self,label,txt):
        dialog = self.help_dialog
        dialog.configure(text_state = 'normal')
        dialog.delete('1.0','end')
        dialog.insert('end', txt)
        dialog.configure(label_text = label)
        dialog.configure(text_state = 'disabled')
        dialog.show()

    #-------------- Options -------------------------

    def build_options_dialog(self):
        """Options are set using a Notebook widget presented in
        a dialog widget
        """

        self.options_dialog = Pmw.Dialog(self.master,
                      buttons = ('Apply','Close and Apply','Cancel'),
                      title = 'CCP1 GUI: tkMolView Options',
                      command = self.store_options)

        nb = Pmw.NoteBook(self.options_dialog.interior())

        page = nb.add('Files')

        page = nb.add('Connectivity')

        grp = Pmw.Group(page,tag_text = 'Connection parameters')

        d = {'counter' : 'real' }
        self.w_conn_scale = Pmw.Counter(
            grp.interior(), 
            datatype = d,
            labelpos = 'w', label_text = "Radius Scale",
            increment = 0.1,
            entryfield_entry_width = 10,
            entryfield_value = self.conn_scale)
        self.w_conn_scale.pack(side='left')

        self.w_conn_toler = Pmw.Counter(
            grp.interior(), 
            datatype = d,
            labelpos = 'w', label_text = "Tolerance",
            increment = 0.1,
            entryfield_entry_width = 10,
            entryfield_value = self.conn_toler)
        self.w_conn_toler.pack(side='left')

        grp.pack(side='top',fill='x')

        grp = Pmw.Group(page,tag_text = 'Non-bonded Contact parameters')

        d = {'counter' : 'real' }
        self.w_contact_scale = Pmw.Counter(
            grp.interior(), 
            datatype = d,
            labelpos = 'w', label_text = "Radius Scale",
            increment = 0.1,
            entryfield_entry_width = 10,
            entryfield_value = self.contact_scale)
        self.w_contact_scale.pack(side='left')

        self.w_contact_toler = Pmw.Counter(
            grp.interior(), 
            datatype = d,
            labelpos = 'w', label_text = "Tolerance",
            increment = 0.1,
            entryfield_entry_width = 10,
            entryfield_value = self.contact_toler)
        self.w_contact_toler.pack(side='left')

        grp.pack(side='top',fill='x')

        page = nb.add('Visualisation')

        # Background colour
        f1 = Tkinter.Frame(page)
        self.cframe = Tkinter.Frame(f1)
        self.w_colorlab = Tkinter.Label(self.cframe,text='Background Colour:      ')

        self.bg_colour   =  '#%02x%02x%02x' % self.bg_rgb
        self.w_bgcolor = Tkinter.Button(self.cframe,
                               text = 'Choose',
                               foreground = self.bg_colour,
                               command= self.__choose_bg_colour)

        # Pick tolerance
        self.pktframe = Tkinter.Frame(f1)
        d = {'counter' : 'real' }
        self.w_picktol = Pmw.Counter(
            self.pktframe, 
            datatype = d,
            labelpos = 'w', label_text = "Pick Tolerance",
            increment = 0.005,
            entryfield_entry_width = 10,
            entryfield_value = self.pick_tolerance)

        f1.pack(side='top')

        self.w_picktol.pack(side='left')
        self.w_colorlab.pack(side='left')
        self.w_bgcolor.pack(side='left')

        self.pktframe.pack(side='left',fill='x')
        self.cframe.pack(side='left',fill='x')


        # Clipping
        self.clipframe = Pmw.Group(page,tag_text='Clipping Planes')
        d = {'counter' : 'real' }
        v = "Auto"
        if self.near:
            v = str(self.near)
        self.w_nearclip = Pmw.EntryField(
            self.clipframe.interior(), 
            labelpos = 'w', label_text = "Near",
            value = v)
        self.w_nearclip.pack(side='left')
        v = "Auto"
        if self.far:
            v = str(self.far)

        self.w_farclip = Pmw.EntryField(
            self.clipframe.interior(), 
            labelpos = 'w', label_text = "Far",
            value = v)
        self.w_farclip.pack(side='left')

        self.clipframe.pack(side='top',fill='x')   


        # Line Width and Point Size (Molecule drawings)
        self.mol_line_frame = Pmw.Group(page,tag_text="Molecule Line Drawing Settings")
        grp = self.mol_line_frame.interior()
        d = {'counter' : 'integer' }
        self.w_mol_line_width = Pmw.Counter(
            grp,
            datatype = d,
            labelpos = 'w', label_text = "Line Width",
            increment = 1,
            entryfield_entry_width = 5,
            entryfield_value = self.mol_line_width)

        self.w_mol_point_size = Pmw.Counter(
            grp,
            datatype = d,
            labelpos = 'w', label_text = "Point Size",
            increment = 1,
            entryfield_entry_width = 5,
            entryfield_value = self.mol_point_size)

        self.w_mol_line_width.pack(side='left')
        self.w_mol_point_size.pack(side='left')
        self.mol_line_frame.pack(side='top',fill='x')


        # Sphere representation and properties
        self.sphere_prop_frame = Pmw.Group(page,tag_text="Sphere Properties")
        grp = self.sphere_prop_frame.interior()
        f1 = Tkinter.Frame(grp)
        f2 = Tkinter.Frame(grp)
        d = {'counter' : 'integer' }

        self.w_mol_sphere_resolution = Pmw.Counter(
            f1,
            datatype = d,
            labelpos = 'w', label_text = "Resolution",
            increment = 1,
            entryfield_entry_width = 5,
            entryfield_value = self.mol_sphere_resolution)

        self.w_mol_sphere_specular_power = Pmw.Counter(
            f1,
            datatype = d,
            labelpos = 'w', label_text = "Specular Power",
            increment = 1,
            entryfield_entry_width = 5,
            entryfield_value = self.mol_sphere_specular_power)

        d = {'counter' : 'real' }

        self.w_mol_sphere_diffuse = Pmw.Counter(
            f2,
            datatype = d,
            labelpos = 'w', label_text = "Diffuse",
            increment = 0.1,
            entryfield_entry_width = 5,
            entryfield_value = self.mol_sphere_diffuse)

        self.w_mol_sphere_ambient = Pmw.Counter(
            f2,
            datatype = d,
            labelpos = 'w', label_text = "Ambient",
            increment = 0.1,
            entryfield_entry_width = 5,
            entryfield_value = self.mol_sphere_ambient)

        self.w_mol_sphere_specular = Pmw.Counter(
            f2,
            datatype = d,
            labelpos = 'w', label_text = "Specular",
            increment = 0.1,
            entryfield_entry_width = 5,
            entryfield_value = self.mol_sphere_specular)

        self.w_mol_sphere_resolution.pack(side='left')
        self.w_mol_sphere_specular_power.pack(side='left')
        f1.pack(side='top')
        self.w_mol_sphere_diffuse.pack(side='left')
        self.w_mol_sphere_ambient.pack(side='left')
        self.w_mol_sphere_specular.pack(side='left')
        f2.pack(side='top')
        self.sphere_prop_frame.pack(side='top',fill='x')


        # Cylinder  representation and properties
        self.cylinder_prop_frame = Pmw.Group(page,tag_text="Cylinder Properties")
        grp = self.cylinder_prop_frame.interior()
        f1 = Tkinter.Frame(grp)
        f2 = Tkinter.Frame(grp)
        d = {'counter' : 'integer' }

        self.w_mol_cylinder_resolution = Pmw.Counter(
            f1,
            datatype = d,
            labelpos = 'w', label_text = "Resolution",
            increment = 1,
            entryfield_entry_width = 5,
            entryfield_value = self.mol_cylinder_resolution)

        self.w_mol_cylinder_specular_power = Pmw.Counter(
            f1,
            datatype = d,
            labelpos = 'w', label_text = "Specular Power",
            increment = 1,
            entryfield_entry_width = 5,
            entryfield_value = self.mol_cylinder_specular_power)

        d = {'counter' : 'real' }

        self.w_mol_cylinder_diffuse = Pmw.Counter(
            f2,
            datatype = d,
            labelpos = 'w', label_text = "Diffuse",
            increment = 0.1,
            entryfield_entry_width = 5,
            entryfield_value = self.mol_cylinder_diffuse)

        self.w_mol_cylinder_ambient = Pmw.Counter(
            f2,
            datatype = d,
            labelpos = 'w', label_text = "Ambient",
            increment = 0.1,
            entryfield_entry_width = 5,
            entryfield_value = self.mol_cylinder_ambient)

        self.w_mol_cylinder_specular = Pmw.Counter(
            f2,
            datatype = d,
            labelpos = 'w', label_text = "Specular",
            increment = 0.1,
            entryfield_entry_width = 5,
            entryfield_value = self.mol_cylinder_specular)

        self.w_mol_cylinder_resolution.pack(side='left')
        self.w_mol_cylinder_specular_power.pack(side='left')
        f1.pack(side='top')
        self.w_mol_cylinder_diffuse.pack(side='left')
        self.w_mol_cylinder_ambient.pack(side='left')
        self.w_mol_cylinder_specular.pack(side='left')
        f2.pack(side='top')
        self.cylinder_prop_frame.pack(side='top',fill='x')

        # Line Width and Point Size (Field Representations drawings)
        self.field_line_frame = Pmw.Group(page,tag_text="Data Line Settings")
        grp = self.field_line_frame.interior()
        d = {'counter' : 'integer' }
        self.w_field_line_width = Pmw.Counter(
            grp, 
            datatype = d,
            labelpos = 'w', label_text = "Line Width",
            increment = 1,
            entryfield_entry_width = 5,
            entryfield_value = self.field_line_width)

        self.w_field_point_size = Pmw.Counter(
            grp,
            datatype = d,
            labelpos = 'w', label_text = "Point Size",
            increment = 1,
            entryfield_entry_width = 5,
            entryfield_value = self.field_point_size)

        self.w_field_line_width.pack(side='left')
        self.w_field_point_size.pack(side='left')
        self.field_line_frame.pack(side='top',fill='x')

        # Other options
        # rotation origin
        # - not so important now we have found 'r' key binding
        # in preferences store initial location for load/save
        # lod actors
        # clipping planes

        page = nb.add('Developmental')

        #hull_width = self.width,
        #hull_height = self.height,
        #createcommand=self.CreatePage,
        #    raisecommand=self.RaisePage,
        #    lowercommand=self.LowerPage)

        nb.pack(expand=1, fill='both')

        #self.options_notebook = nb
        nb.setnaturalsize()
        self.options_dialog.withdraw()
        
        #Associate widget with its helpfile
        viewer.help.sethelp(self.options_dialog,'Edit Options')

    def __choose_bg_colour(self):
        self.bg_rgb, self.bg_colour = askcolor(initialcolor=self.bg_colour)
        self.w_bgcolor.configure(foreground = self.bg_colour)

    def open_options_dialog(self):
        self.save_bg_rgb = self.bg_rgb
        self.save_pick_tolerance = self.pick_tolerance
        self.save_near = self.near
        self.save_far = self.far        
        self.options_dialog.activate(globalMode = 'nograb')

    def store_options(self,result):
        """Code executed when the dialog is closed"""
        if result == 'Apply' or result == 'Close and Apply':
            # Here we need to apply any options that have 
            # been modified
            print 'Store'
            self.set_bg_colour(self.bg_rgb)
            set_rc_var( 'bg_rgb', self.bg_rgb )

            self.pick_tolerance  = float(self.w_picktol.get())
            self.set_pick_tolerance()
            set_rc_var( 'pick_tolerance', self.pick_tolerance )

            txt = self.w_nearclip.get()
            if txt == "Auto":
                self.near = None
            else:
                self.near = float(txt)

            txt = self.w_farclip.get()
            if txt == "Auto":
                self.far = None
            else:
                self.far = float(txt)
            self.set_clipping_planes()

            self.conn_toler  = float(self.w_conn_toler.get())
            set_rc_var( 'conn_toler', self.conn_toler )
            self.conn_scale  = float(self.w_conn_scale.get())
            set_rc_var( 'conn_scale', self.conn_scale )
            self.contact_toler  = float(self.w_contact_toler.get())
            set_rc_var( 'contact_toler', self.contact_toler )
            self.contact_scale  = float(self.w_contact_scale.get())
            set_rc_var( 'contact_scale', self.contact_scale )

            self.mol_line_width = int(self.w_mol_line_width.get())
            set_rc_var( 'mol_line_width', self.mol_line_width )
            self.mol_point_size  = int(self.w_mol_point_size.get())
            set_rc_var( 'mol_point_size', self.mol_point_size )

            self.field_line_width = int(self.w_field_line_width.get())
            set_rc_var( 'field_line_width', self.field_line_width )
            self.field_point_size  = int(self.w_field_point_size.get())
            set_rc_var( 'field_point_size', self.field_point_size )

            self.mol_sphere_resolution = int(self.w_mol_sphere_resolution.get())
            set_rc_var( 'mol_sphere_resolution', self.mol_sphere_resolution )
            self.mol_sphere_specular_power = int(self.w_mol_sphere_specular_power.get())
            set_rc_var( 'mol_sphere_specular_power', self.mol_sphere_specular_power )
            self.mol_sphere_diffuse = float(self.w_mol_sphere_diffuse.get())
            set_rc_var( 'mol_sphere_diffuse', self.mol_sphere_diffuse )
            self.mol_sphere_ambient = float(self.w_mol_sphere_ambient.get())
            set_rc_var( 'mol_sphere_ambient', self.mol_sphere_ambient )
            self.mol_sphere_specular = float(self.w_mol_sphere_specular.get())
            set_rc_var( 'mol_sphere_specular', self.mol_sphere_specular )

            self.mol_cylinder_resolution = int(self.w_mol_cylinder_resolution.get())
            set_rc_var( 'mol_cylinder_resolution', self.mol_cylinder_resolution )
            self.mol_cylinder_specular_power = int(self.w_mol_cylinder_specular_power.get())
            set_rc_var( 'mol_cylinder_specular_power', self.mol_cylinder_specular_power )
            self.mol_cylinder_diffuse = float(self.w_mol_cylinder_diffuse.get())
            set_rc_var( 'mol_cylinder_diffuse', self.mol_cylinder_diffuse )
            self.mol_cylinder_ambient = float(self.w_mol_cylinder_ambient.get())
            set_rc_var( 'mol_cylinder_ambient', self.mol_cylinder_ambient )
            self.mol_cylinder_specular = float(self.w_mol_cylinder_specular.get())
            set_rc_var( 'mol_cylinder_specular', self.mol_cylinder_specular )

        else:
            # Cancel them
            self.bg_rgb = self.save_bg_rgb
            self.pick_tolerance = self.save_pick_tolerance

        if result == 'Close and Apply' or result == 'Cancel':
            self.options_dialog.deactivate(result)
            #self.options_dialog.close()

        self.update()

    #-------------- Command Window -------------------------

    def myshell(self):
        mypyshell(self.master)
        
    def build_command_window(self):
        self.shell_dialog = Pmw.TextDialog(self.master, scrolledtext_labelpos = 'n',
                                           title = 'Python Shell',
                                           buttons = ('Close',),
                                           label_text = '')
        self.text = self.shell_dialog.component('text')
        self.text.bind('<Return>', lambda e,s=self,g=globals(),l=locals(): s.ev(g,l,e) )
        self.shell_dialog.withdraw()
        #Associate widget with its helpfile
        viewer.help.sethelp(self.shell_dialog,'Python Shell')

#                               'viewer.pythonshell.txt')

    def ev(self,globals,locals,arg):
        line = self.text.get('insert linestart','insert lineend')
        exec line in globals,locals


    def define_colourmaps(self):
        self.colourmaps = []

        c = self.colourmap_func()
        self.colourmaps.append(c)
        c.set_title("black")
        c.set_range(-1.0,1.0)
        c.set_colours( [
            (0 , 0 , 0),
            (0 , 0 , 0)])
        c.build()

        c = self.colourmap_func()
        self.colourmaps.append(c)
        c.set_title("red-black-blue")
        c.set_range(-0.0001,0.0001)
        c.set_colours([
            (255 , 0 , 0),
            (0 , 0 , 0),
            (0 , 0 , 255)])
        c.build()

        c = self.colourmap_func()
        self.colourmaps.append(c)
        c.set_title("red-grey-blue")
        c.set_range(-1,1.)
        c.set_colours([
            (255 ,  0 ,  0),
            (250 , 20 , 20),
            (245 , 40 , 40),
            (240 , 70 , 70),
            (235 , 85 , 85),
            (230 , 100 , 100),
            (225 , 120 , 120),
            (220 , 150 , 150),
            (215 , 170 , 170),
            (210 , 190 , 190),
            (205 , 205 , 205),
            (190 , 190 , 210),
            (170 , 170 , 215),
            (150 , 150 , 220),
            (120 , 120 , 225),
            (100 , 100 , 230),
            ( 85,  85, 235),
            ( 70,  70, 240),
            ( 40,  40, 245),
            ( 20,  20, 250),
            (  0,  0, 255) ] )
        c.build()

        c = self.colourmap_func()
        self.colourmaps.append(c)
        c.set_title("red-blue")
        c.set_colours([
            (0 , 0 , 255),
            (1 , 0 , 254),
            (2 , 0 , 253),
            (3 , 0 , 252),
            (4 , 0 , 251),
            (5 , 0 , 250),
            (6 , 0 , 249),
            (7 , 0 , 248),
            (8 , 0 , 247),
            (9 , 0 , 246),
            (10 , 0 , 245),
            (11 , 0 , 244),
            (12 , 0 , 243),
            (13 , 0 , 242),
            (14 , 0 , 241),
            (15 , 0 , 240),
            (16 , 0 , 239),
            (17 , 0 , 238),
            (18 , 0 , 237),
            (19 , 0 , 236),
            (20 , 0 , 235),
            (21 , 0 , 234),
            (22 , 0 , 233),
            (23 , 0 , 232),
            (24 , 0 , 231),
            (25 , 0 , 230),
            (26 , 0 , 229),
            (27 , 0 , 228),
            (28 , 0 , 227),
            (29 , 0 , 226),
            (30 , 0 , 225),
            (31 , 0 , 224),
            (32 , 0 , 223),
            (33 , 0 , 222),
            (34 , 0 , 221),
            (35 , 0 , 220),
            (36 , 0 , 219),
            (37 , 0 , 218),
            (38 , 0 , 217),
            (39 , 0 , 216),
            (40 , 0 , 215),
            (41 , 0 , 214),
            (42 , 0 , 213),
            (43 , 0 , 212),
            (44 , 0 , 211),
            (45 , 0 , 210),
            (46 , 0 , 209),
            (47 , 0 , 208),
            (48 , 0 , 207),
            (49 , 0 , 206),
            (50 , 0 , 205),
            (51 , 0 , 204),
            (52 , 0 , 203),
            (53 , 0 , 202),
            (54 , 0 , 201),
            (55 , 0 , 200),
            (56 , 0 , 199),
            (57 , 0 , 198),
            (58 , 0 , 197),
            (59 , 0 , 196),
            (60 , 0 , 195),
            (61 , 0 , 194),
            (62 , 0 , 193),
            (63 , 0 , 192),
            (64 , 0 , 191),
            (65 , 0 , 190),
            (66 , 0 , 189),
            (67 , 0 , 188),
            (68 , 0 , 187),
            (69 , 0 , 186),
            (70 , 0 , 185),
            (71 , 0 , 184),
            (72 , 0 , 183),
            (73 , 0 , 182),
            (74 , 0 , 181),
            (75 , 0 , 180),
            (76 , 0 , 179),
            (77 , 0 , 178),
            (78 , 0 , 177),
            (79 , 0 , 176),
            (80 , 0 , 175),
            (81 , 0 , 174),
            (82 , 0 , 173),
            (83 , 0 , 172),
            (84 , 0 , 171),
            (85 , 0 , 170),
            (86 , 0 , 169),
            (87 , 0 , 168),
            (88 , 0 , 167),
            (89 , 0 , 166),
            (90 , 0 , 165),
            (91 , 0 , 164),
            (92 , 0 , 163),
            (93 , 0 , 162),
            (94 , 0 , 161),
            (95 , 0 , 160),
            (96 , 0 , 159),
            (97 , 0 , 158),
            (98 , 0 , 157),
            (99 , 0 , 156),
            (100 , 0 , 155),
            (101 , 0 , 154),
            (102 , 0 , 153),
            (103 , 0 , 152),
            (104 , 0 , 151),
            (105 , 0 , 150),
            (106 , 0 , 149),
            (107 , 0 , 148),
            (108 , 0 , 147),
            (109 , 0 , 146),
            (110 , 0 , 145),
            (111 , 0 , 144),
            (112 , 0 , 143),
            (113 , 0 , 142),
            (114 , 0 , 141),
            (115 , 0 , 140),
            (116 , 0 , 139),
            (117 , 0 , 138),
            (118 , 0 , 137),
            (119 , 0 , 136),
            (120 , 0 , 135),
            (121 , 0 , 134),
            (122 , 0 , 133),
            (123 , 0 , 132),
            (124 , 0 , 131),
            (125 , 0 , 130),
            (126 , 0 , 129),
            (127 , 0 , 128),
            (128 , 0 , 127),
            (129 , 0 , 126),
            (130 , 0 , 125),
            (131 , 0 , 124),
            (132 , 0 , 123),
            (133 , 0 , 122),
            (134 , 0 , 121),
            (135 , 0 , 120),
            (136 , 0 , 119),
            (137 , 0 , 118),
            (138 , 0 , 117),
            (139 , 0 , 116),
            (140 , 0 , 115),
            (141 , 0 , 114),
            (142 , 0 , 113),
            (143 , 0 , 112),
            (144 , 0 , 111),
            (145 , 0 , 110),
            (146 , 0 , 109),
            (147 , 0 , 108),
            (148 , 0 , 107),
            (149 , 0 , 106),
            (150 , 0 , 105),
            (151 , 0 , 104),
            (152 , 0 , 103),
            (153 , 0 , 102),
            (154 , 0 , 101),
            (155 , 0 , 100),
            (156 , 0 , 99),
            (157 , 0 , 98),
            (158 , 0 , 97),
            (159 , 0 , 96),
            (160 , 0 , 95),
            (161 , 0 , 94),
            (162 , 0 , 93),
            (163 , 0 , 92),
            (164 , 0 , 91),
            (165 , 0 , 90),
            (166 , 0 , 89),
            (167 , 0 , 88),
            (168 , 0 , 87),
            (169 , 0 , 86),
            (170 , 0 , 85),
            (171 , 0 , 84),
            (172 , 0 , 83),
            (173 , 0 , 82),
            (174 , 0 , 81),
            (175 , 0 , 80),
            (176 , 0 , 79),
            (177 , 0 , 78),
            (178 , 0 , 77),
            (179 , 0 , 76),
            (180 , 0 , 75),
            (181 , 0 , 74),
            (182 , 0 , 73),
            (183 , 0 , 72),
            (184 , 0 , 71),
            (185 , 0 , 70),
            (186 , 0 , 69),
            (187 , 0 , 68),
            (188 , 0 , 67),
            (189 , 0 , 66),
            (190 , 0 , 65),
            (191 , 0 , 64),
            (192 , 0 , 63),
            (193 , 0 , 62),
            (194 , 0 , 61),
            (195 , 0 , 60),
            (196 , 0 , 59),
            (197 , 0 , 58),
            (198 , 0 , 57),
            (199 , 0 , 56),
            (200 , 0 , 55),
            (201 , 0 , 54),
            (202 , 0 , 53),
            (203 , 0 , 52),
            (204 , 0 , 51),
            (205 , 0 , 50),
            (206 , 0 , 49),
            (207 , 0 , 48),
            (208 , 0 , 47),
            (209 , 0 , 46),
            (210 , 0 , 45),
            (211 , 0 , 44),
            (212 , 0 , 43),
            (213 , 0 , 42),
            (214 , 0 , 41),
            (215 , 0 , 40),
            (216 , 0 , 39),
            (217 , 0 , 38),
            (218 , 0 , 37),
            (219 , 0 , 36),
            (220 , 0 , 35),
            (221 , 0 , 34),
            (222 , 0 , 33),
            (223 , 0 , 32),
            (224 , 0 , 31),
            (225 , 0 , 30),
            (226 , 0 , 29),
            (227 , 0 , 28),
            (228 , 0 , 27),
            (229 , 0 , 26),
            (230 , 0 , 25),
            (231 , 0 , 24),
            (232 , 0 , 23),
            (233 , 0 , 22),
            (234 , 0 , 21),
            (235 , 0 , 20),
            (236 , 0 , 19),
            (237 , 0 , 18),
            (238 , 0 , 17),
            (239 , 0 , 16),
            (240 , 0 , 15),
            (241 , 0 , 14),
            (242 , 0 , 13),
            (243 , 0 , 12),
            (244 , 0 , 11),
            (245 , 0 , 10),
            (246 , 0 , 9),
            (247 , 0 , 8),
            (248 , 0 , 7),
            (249 , 0 , 6),
            (250 , 0 , 5),
            (251 , 0 , 4),
            (252 , 0 , 3),
            (253 , 0 , 2),
            (254 , 0 , 1),
            (255 , 0 , 0) ] )
        c.build()

        c = self.colourmap_func()
        self.colourmaps.append(c)
        c.set_title("rainbow")
        c.set_range(-1.0,1.0)
        c.set_colours([
            (255 , 0, 0 ),
            (255 , 6 , 0 ),
            (255 , 12 , 0 ),
            (255 , 18 , 0 ),
            (255 , 24 , 0 ),
            (255 , 30 , 0 ),
            (255 , 36 , 0 ),
            (255 , 42 , 0 ),
            (255 , 48 , 0 ),
            (255 , 54 , 0 ),
            (255 , 60 , 0 ),
            (255 , 66 , 0 ),
            (255 , 72 , 0 ),
            (255 , 78 , 0 ),
            (255 , 84 , 0 ),
            (255 , 90 , 0 ),
            (255 , 96 , 0 ),
            (255 , 102 , 0 ),
            (255 , 108 , 0 ),
            (255 , 114 , 0 ),
            (255 , 120 , 0 ),
            (255 , 126 , 0 ),
            (255 , 132 , 0 ),
            (255 , 138 , 0 ),
            (255 , 144 , 0 ),
            (255 , 150 , 0 ),
            (255 , 156 , 0 ),
            (255 , 162 , 0 ),
            (255 , 168 , 0 ),
            (255 , 174 , 0 ),
            (255 , 180 , 0 ),
            (255 , 186 , 0 ),
            (255 , 192 , 0 ),
            (255 , 198 , 0 ),
            (255 , 204 , 0 ),
            (255 , 210 , 0 ),
            (255 , 216 , 0 ),
            (255 , 222 , 0 ),
            (255 , 228 , 0 ),
            (255 , 234 , 0 ),
            (255 , 240 , 0 ),
            (255 , 246 , 0 ),
            (255 , 252 , 0 ),
            (250 , 255 , 0 ),
            (244 , 255 , 0 ),
            (238 , 255 , 0 ),
            (232 , 255 , 0 ),
            (226 , 255 , 0 ),
            (220 , 255 , 0 ),
            (214 , 255 , 0 ),
            (208 , 255 , 0 ),
            (202 , 255 , 0 ),
            (196 , 255 , 0 ),
            (190 , 255 , 0 ),
            (184 , 255 , 0 ),
            (178 , 255 , 0 ),
            (172 , 255 , 0 ),
            (166 , 255 , 0 ),
            (160 , 255 , 0 ),
            (154 , 255 , 0 ),
            (148 , 255 , 0 ),
            (142 , 255 , 0 ),
            (136 , 255 , 0 ),
            (130 , 255 , 0 ),
            (124 , 255 , 0 ),
            (118 , 255 , 0 ),
            (112 , 255 , 0 ),
            (106 , 255 , 0 ),
            (100 , 255 , 0 ),
            (94 , 255 , 0 ),
            (88 , 255 , 0 ),
            (82 , 255 , 0 ),
            (76 , 255 , 0 ),
            (70 , 255 , 0 ),
            (64 , 255 , 0 ),
            (58 , 255 , 0 ),
            (52 , 255 , 0 ),
            (46 , 255 , 0 ),
            (40 , 255 , 0 ),
            (34 , 255 , 0 ),
            (28 , 255 , 0 ),
            (22 , 255 , 0 ),
            (16 , 255 , 0 ),
            (10 , 255 , 0 ),
            (4 , 255 , 0 ),
            (0 , 255 , 2 ),
            (0 , 255 , 8 ),
            (0 , 255 , 14 ),
            (0 , 255 , 20 ),
            (0 , 255 , 26 ),
            (0 , 255 , 32 ),
            (0 , 255 , 38 ),
            (0 , 255 , 44 ),
            (0 , 255 , 50 ),
            (0 , 255 , 56 ),
            (0 , 255 , 62 ),
            (0 , 255 , 68 ),
            (0 , 255 , 74 ),
            (0 , 255 , 80 ),
            (0 , 255 , 86 ),
            (0 , 255 , 92 ),
            (0 , 255 , 98 ),
            (0 , 255 , 104 ),
            (0 , 255 , 110 ),
            (0 , 255 , 116 ),
            (0 , 255 , 122 ),
            (0 , 255 , 128 ),
            (0 , 255 , 134 ),
            (0 , 255 , 140 ),
            (0 , 255 , 146 ),
            (0 , 255 , 152 ),
            (0 , 255 , 158 ),
            (0 , 255 , 164 ),
            (0 , 255 , 170 ),
            (0 , 255 , 176 ),
            (0 , 255 , 182 ),
            (0 , 255 , 188 ),
            (0 , 255 , 194 ),
            (0 , 255 , 200 ),
            (0 , 255 , 206 ),
            (0 , 255 , 212 ),
            (0 , 255 , 218 ),
            (0 , 255 , 224 ),
            (0 , 255 , 230 ),
            (0 , 255 , 236 ),
            (0 , 255 , 242 ),
            (0 , 255 , 248 ),
            (0 , 255 , 255 ),
            (0 , 248 , 255 ),
            (0 , 242 , 255 ),
            (0 , 236 , 255 ),
            (0 , 230 , 255 ),
            (0 , 224 , 255 ),
            (0 , 218 , 255 ),
            (0 , 212 , 255 ),
            (0 , 206 , 255 ),
            (0 , 200 , 255 ),
            (0 , 194 , 255 ),
            (0 , 188 , 255 ),
            (0 , 182 , 255 ),
            (0 , 176 , 255 ),
            (0 , 170 , 255 ),
            (0 , 164 , 255 ),
            (0 , 158 , 255 ),
            (0 , 152 , 255 ),
            (0 , 146 , 255 ),
            (0 , 140 , 255 ),
            (0 , 134 , 255 ),
            (0 , 128 , 255 ),
            (0 , 122 , 255 ),
            (0 , 116 , 255 ),
            (0 , 110 , 255 ),
            (0 , 104 , 255 ),
            (0 , 98 , 255 ),
            (0 , 92 , 255 ),
            (0 , 86 , 255 ),
            (0 , 80 , 255 ),
            (0 , 74 , 255 ),
            (0 , 68 , 255 ),
            (0 , 62 , 255 ),
            (0 , 56 , 255 ),
            (0 , 50 , 255 ),
            (0 , 44 , 255 ),
            (0 , 38 , 255 ),
            (0 , 32 , 255 ),
            (0 , 26 , 255 ),
            (0 , 20 , 255 ),
            (0 , 14 , 255 ),
            (0 , 8 , 255 ),
            (0 , 2 , 255 ),
            (4 , 0 , 255 ),
            (10 , 0 , 255 ),
            (16 , 0 , 255 ),
            (22 , 0 , 255 ),
            (28 , 0 , 255 ),
            (34 , 0 , 255 ),
            (40 , 0 , 255 ),
            (46 , 0 , 255 ),
            (52 , 0 , 255 ),
            (58 , 0 , 255 ),
            (64 , 0 , 255 ),
            (70 , 0 , 255 ),
            (76 , 0 , 255 ),
            (82 , 0 , 255 ),
            (88 , 0 , 255 ),
            (94 , 0 , 255 ),
            (100 , 0 , 255 ),
            (106 , 0 , 255 ),
            (112 , 0 , 255 ),
            (118 , 0 , 255 ),
            (124 , 0 , 255 ),
            (130 , 0 , 255 ),
            (136 , 0 , 255 ),
            (142 , 0 , 255 ),
            (148 , 0 , 255 ),
            (154 , 0 , 255 ),
            (160 , 0 , 255 ),
            (166 , 0 , 255 ),
            (172 , 0 , 255 ),
            (178 , 0 , 255 ),
            (184 , 0 , 255 ),
            (190 , 0 , 255 ),
            (196 , 0 , 255 ),
            (202 , 0 , 255 ),
            (208 , 0 , 255 ),
            (214 , 0 , 255 ),
            (220 , 0 , 255 ),
            (226 , 0 , 255 ),
            (232 , 0 , 255 ),
            (238 , 0 , 255 ),
            (244 , 0 , 255 ),
            (250 , 0 , 255 ),
            (255 , 0 , 252 ),
            (255 , 0 , 246 ),
            (255 , 0 , 240 ),
            (255 , 0 , 234 ),
            (255 , 0 , 228 ),
            (255 , 0 , 222 ),
            (255 , 0 , 216 ),
            (255 , 0 , 210 ),
            (255 , 0 , 204 ),
            (255 , 0 , 198 ),
            (255 , 0 , 192 ),
            (255 , 0 , 186 ),
            (255 , 0 , 180 ),
            (255 , 0 , 174 ),
            (255 , 0 , 168 ),
            (255 , 0 , 162 ),
            (255 , 0 , 156 ),
            (255 , 0 , 150 ),
            (255 , 0 , 144 ),
            (255 , 0 , 138 ),
            (255 , 0 , 132 ),
            (255 , 0 , 126 ),
            (255 , 0 , 120 ),
            (255 , 0 , 114 ),
            (255 , 0 , 108 ),
            (255 , 0 , 102 ),
            (255 , 0 , 96 ),
            (255 , 0 , 90 ),
            (255 , 0 , 84 ),
            (255 , 0 , 78 ),
            (255 , 0 , 72 ),
            (255 , 0 , 66 ),
            (255 , 0 , 60 ),
            (255 , 0 , 54 ),
            (255 , 0 , 48 ),
            (255 , 0 , 42 ),
            (255 , 0 , 36 ),
            (255 , 0 , 30 ),
            (255 , 0 , 24 ),
            (255 , 0 , 18 ),
            (255 , 0 , 12 ),
            (255 , 0 , 6 ),
            (255 , 0 , 0 ) ] )        
        c.build()

        c = self.colourmap_func()
        self.colourmaps.append(c)
        c.set_title("rainbow plus half")
        c.set_range(-1.0,1.0)
        c.set_colours([
            (0 , 255 , 255 ),
            (0 , 248 , 255 ),
            (0 , 242 , 255 ),
            (0 , 236 , 255 ),
            (0 , 230 , 255 ),
            (0 , 224 , 255 ),
            (0 , 218 , 255 ),
            (0 , 212 , 255 ),
            (0 , 206 , 255 ),
            (0 , 200 , 255 ),
            (0 , 194 , 255 ),
            (0 , 188 , 255 ),
            (0 , 182 , 255 ),
            (0 , 176 , 255 ),
            (0 , 170 , 255 ),
            (0 , 164 , 255 ),
            (0 , 158 , 255 ),
            (0 , 152 , 255 ),
            (0 , 146 , 255 ),
            (0 , 140 , 255 ),
            (0 , 134 , 255 ),
            (0 , 128 , 255 ),
            (0 , 122 , 255 ),
            (0 , 116 , 255 ),
            (0 , 110 , 255 ),
            (0 , 104 , 255 ),
            (0 , 98 , 255 ),
            (0 , 92 , 255 ),
            (0 , 86 , 255 ),
            (0 , 80 , 255 ),
            (0 , 74 , 255 ),
            (0 , 68 , 255 ),
            (0 , 62 , 255 ),
            (0 , 56 , 255 ),
            (0 , 50 , 255 ),
            (0 , 44 , 255 ),
            (0 , 38 , 255 ),
            (0 , 32 , 255 ),
            (0 , 26 , 255 ),
            (0 , 20 , 255 ),
            (0 , 14 , 255 ),
            (0 , 8 , 255 ),
            (0 , 2 , 255 ),
            (4 , 0 , 255 ),
            (10 , 0 , 255 ),
            (16 , 0 , 255 ),
            (22 , 0 , 255 ),
            (28 , 0 , 255 ),
            (34 , 0 , 255 ),
            (40 , 0 , 255 ),
            (46 , 0 , 255 ),
            (52 , 0 , 255 ),
            (58 , 0 , 255 ),
            (64 , 0 , 255 ),
            (70 , 0 , 255 ),
            (76 , 0 , 255 ),
            (82 , 0 , 255 ),
            (88 , 0 , 255 ),
            (94 , 0 , 255 ),
            (100 , 0 , 255 ),
            (106 , 0 , 255 ),
            (112 , 0 , 255 ),
            (118 , 0 , 255 ),
            (124 , 0 , 255 ),
            (130 , 0 , 255 ),
            (136 , 0 , 255 ),
            (142 , 0 , 255 ),
            (148 , 0 , 255 ),
            (154 , 0 , 255 ),
            (160 , 0 , 255 ),
            (166 , 0 , 255 ),
            (172 , 0 , 255 ),
            (178 , 0 , 255 ),
            (184 , 0 , 255 ),
            (190 , 0 , 255 ),
            (196 , 0 , 255 ),
            (202 , 0 , 255 ),
            (208 , 0 , 255 ),
            (214 , 0 , 255 ),
            (220 , 0 , 255 ),
            (226 , 0 , 255 ),
            (232 , 0 , 255 ),
            (238 , 0 , 255 ),
            (244 , 0 , 255 ),
            (250 , 0 , 255 ),
            (255 , 0 , 252 ),
            (255 , 0 , 246 ),
            (255 , 0 , 240 ),
            (255 , 0 , 234 ),
            (255 , 0 , 228 ),
            (255 , 0 , 222 ),
            (255 , 0 , 216 ),
            (255 , 0 , 210 ),
            (255 , 0 , 204 ),
            (255 , 0 , 198 ),
            (255 , 0 , 192 ),
            (255 , 0 , 186 ),
            (255 , 0 , 180 ),
            (255 , 0 , 174 ),
            (255 , 0 , 168 ),
            (255 , 0 , 162 ),
            (255 , 0 , 156 ),
            (255 , 0 , 150 ),
            (255 , 0 , 144 ),
            (255 , 0 , 138 ),
            (255 , 0 , 132 ),
            (255 , 0 , 126 ),
            (255 , 0 , 120 ),
            (255 , 0 , 114 ),
            (255 , 0 , 108 ),
            (255 , 0 , 102 ),
            (255 , 0 , 96 ),
            (255 , 0 , 90 ),
            (255 , 0 , 84 ),
            (255 , 0 , 78 ),
            (255 , 0 , 72 ),
            (255 , 0 , 66 ),
            (255 , 0 , 60 ),
            (255 , 0 , 54 ),
            (255 , 0 , 48 ),
            (255 , 0 , 42 ),
            (255 , 0 , 36 ),
            (255 , 0 , 30 ),
            (255 , 0 , 24 ),
            (255 , 0 , 18 ),
            (255 , 0 , 12 ),
            (255 , 0 , 6 ),
            (255 , 0 , 0 ),
            (255 , 6 , 0 ),
            (255 , 12 , 0 ),
            (255 , 18 , 0 ),
            (255 , 24 , 0 ),
            (255 , 30 , 0 ),
            (255 , 36 , 0 ),
            (255 , 42 , 0 ),
            (255 , 48 , 0 ),
            (255 , 54 , 0 ),
            (255 , 60 , 0 ),
            (255 , 66 , 0 ),
            (255 , 72 , 0 ),
            (255 , 78 , 0 ),
            (255 , 84 , 0 ),
            (255 , 90 , 0 ),
            (255 , 96 , 0 ),
            (255 , 102 , 0 ),
            (255 , 108 , 0 ),
            (255 , 114 , 0 ),
            (255 , 120 , 0 ),
            (255 , 126 , 0 ),
            (255 , 132 , 0 ),
            (255 , 138 , 0 ),
            (255 , 144 , 0 ),
            (255 , 150 , 0 ),
            (255 , 156 , 0 ),
            (255 , 162 , 0 ),
            (255 , 168 , 0 ),
            (255 , 174 , 0 ),
            (255 , 180 , 0 ),
            (255 , 186 , 0 ),
            (255 , 192 , 0 ),
            (255 , 198 , 0 ),
            (255 , 204 , 0 ),
            (255 , 210 , 0 ),
            (255 , 216 , 0 ),
            (255 , 222 , 0 ),
            (255 , 228 , 0 ),
            (255 , 234 , 0 ),
            (255 , 240 , 0 ),
            (255 , 246 , 0 ),
            (255 , 252 , 0 ),
            (250 , 255 , 0 ),
            (244 , 255 , 0 ),
            (238 , 255 , 0 ),
            (232 , 255 , 0 ),
            (226 , 255 , 0 ),
            (220 , 255 , 0 ),
            (214 , 255 , 0 ),
            (208 , 255 , 0 ),
            (202 , 255 , 0 ),
            (196 , 255 , 0 ),
            (190 , 255 , 0 ),
            (184 , 255 , 0 ),
            (178 , 255 , 0 ),
            (172 , 255 , 0 ),
            (166 , 255 , 0 ),
            (160 , 255 , 0 ),
            (154 , 255 , 0 ),
            (148 , 255 , 0 ),
            (142 , 255 , 0 ),
            (136 , 255 , 0 ),
            (130 , 255 , 0 ),
            (124 , 255 , 0 ),
            (118 , 255 , 0 ),
            (112 , 255 , 0 ),
            (106 , 255 , 0 ),
            (100 , 255 , 0 ),
            (94 , 255 , 0 ),
            (88 , 255 , 0 ),
            (82 , 255 , 0 ),
            (76 , 255 , 0 ),
            (70 , 255 , 0 ),
            (64 , 255 , 0 ),
            (58 , 255 , 0 ),
            (52 , 255 , 0 ),
            (46 , 255 , 0 ),
            (40 , 255 , 0 ),
            (34 , 255 , 0 ),
            (28 , 255 , 0 ),
            (22 , 255 , 0 ),
            (16 , 255 , 0 ),
            (10 , 255 , 0 ),
            (4 , 255 , 0 ),
            (0 , 255 , 2 ),
            (0 , 255 , 8 ),
            (0 , 255 , 14 ),
            (0 , 255 , 20 ),
            (0 , 255 , 26 ),
            (0 , 255 , 32 ),
            (0 , 255 , 38 ),
            (0 , 255 , 44 ),
            (0 , 255 , 50 ),
            (0 , 255 , 56 ),
            (0 , 255 , 62 ),
            (0 , 255 , 68 ),
            (0 , 255 , 74 ),
            (0 , 255 , 80 ),
            (0 , 255 , 86 ),
            (0 , 255 , 92 ),
            (0 , 255 , 98 ),
            (0 , 255 , 104 ),
            (0 , 255 , 110 ),
            (0 , 255 , 116 ),
            (0 , 255 , 122 ),
            (0 , 255 , 128 ),
            (0 , 255 , 134 ),
            (0 , 255 , 140 ),
            (0 , 255 , 146 ),
            (0 , 255 , 152 ),
            (0 , 255 , 158 ),
            (0 , 255 , 164 ),
            (0 , 255 , 170 ),
            (0 , 255 , 176 ),
            (0 , 255 , 182 ),
            (0 , 255 , 188 ),
            (0 , 255 , 194 ),
            (0 , 255 , 200 ),
            (0 , 255 , 206 ),
            (0 , 255 , 212 ),
            (0 , 255 , 218 ),
            (0 , 255 , 224 ),
            (0 , 255 , 230 ),
            (0 , 255 , 236 ),
            (0 , 255 , 242 ),
            (0 , 255 , 248 ),
            (0 , 255 , 255 ) ] )
        c.build()

        c = self.colourmap_func()
        self.colourmaps.append(c)
        c.set_title("rainbow on black")
        c.set_range(-1.0,1.0)
        c.set_colours([
            (0 , 0 , 0),
            (10 , 0 , 0),
            (20 , 0 , 0),
            (30 , 0 , 0),
            (40 , 0 , 0),
            (50 , 0 , 0),
            (60 , 0 , 0),
            (70 , 0 , 0),
            (80 , 0 , 0),
            (90 , 0 , 0),
            (100 , 0 , 0),
            (110 , 0 , 0),
            (120 , 0 , 0),
            (130 , 0 , 0),
            (140 , 0 , 0),
            (150 , 0 , 0),
            (160 , 0 , 0),
            (170 , 0 , 0),
            (180 , 0 , 0),
            (190 , 0 , 0),
            (200 , 0 , 0),
            (210 , 0 , 0),
            (220 , 0 , 0),
            (230 , 0 , 0),
            (240 , 0 , 0),
            (250 , 0 , 0),
            (255 , 6 , 0 ),
            (255 , 18 , 0 ),
            (255 , 30 , 0 ),
            (255 , 42 , 0 ),
            (255 , 54 , 0 ),
            (255 , 66 , 0 ),
            (255 , 78 , 0 ),
            (255 , 90 , 0 ),
            (255 , 102 , 0 ),
            (255 , 114 , 0 ),
            (255 , 126 , 0 ),
            (255 , 138 , 0 ),
            (255 , 150 , 0 ),
            (255 , 162 , 0 ),
            (255 , 174 , 0 ),
            (255 , 186 , 0 ),
            (255 , 198 , 0 ),
            (255 , 210 , 0 ),
            (255 , 222 , 0 ),
            (255 , 234 , 0 ),
            (255 , 246 , 0 ),
            (250 , 255 , 0 ),
            (238 , 255 , 0 ),
            (232 , 255 , 0 ),
            (226 , 255 , 0 ),
            (220 , 255 , 0 ),
            (214 , 255 , 0 ),
            (208 , 255 , 0 ),
            (202 , 255 , 0 ),
            (196 , 255 , 0 ),
            (190 , 255 , 0 ),
            (184 , 255 , 0 ),
            (178 , 255 , 0 ),
            (172 , 255 , 0 ),
            (166 , 255 , 0 ),
            (160 , 255 , 0 ),
            (154 , 255 , 0 ),
            (148 , 255 , 0 ),
            (142 , 255 , 0 ),
            (136 , 255 , 0 ),
            (130 , 255 , 0 ),
            (124 , 255 , 0 ),
            (118 , 255 , 0 ),
            (112 , 255 , 0 ),
            (106 , 255 , 0 ),
            (100 , 255 , 0 ),
            (94 , 255 , 0 ),
            (88 , 255 , 0 ),
            (82 , 255 , 0 ),
            (76 , 255 , 0 ),
            (70 , 255 , 0 ),
            (64 , 255 , 0 ),
            (58 , 255 , 0 ),
            (52 , 255 , 0 ),
            (46 , 255 , 0 ),
            (40 , 255 , 0 ),
            (34 , 255 , 0 ),
            (28 , 255 , 0 ),
            (22 , 255 , 0 ),
            (16 , 255 , 0 ),
            (10 , 255 , 0 ),
            (4 , 255 , 0 ),
            (0 , 255 , 2 ),
            (0 , 255 , 8 ),
            (0 , 255 , 14 ),
            (0 , 255 , 20 ),
            (0 , 255 , 26 ),
            (0 , 255 , 32 ),
            (0 , 255 , 38 ),
            (0 , 255 , 44 ),
            (0 , 255 , 50 ),
            (0 , 255 , 56 ),
            (0 , 255 , 62 ),
            (0 , 255 , 68 ),
            (0 , 255 , 74 ),
            (0 , 255 , 80 ),
            (0 , 255 , 86 ),
            (0 , 255 , 92 ),
            (0 , 255 , 98 ),
            (0 , 255 , 104 ),
            (0 , 255 , 110 ),
            (0 , 255 , 116 ),
            (0 , 255 , 122 ),
            (0 , 255 , 128 ),
            (0 , 255 , 134 ),
            (0 , 255 , 140 ),
            (0 , 255 , 146 ),
            (0 , 255 , 152 ),
            (0 , 255 , 158 ),
            (0 , 255 , 164 ),
            (0 , 255 , 170 ),
            (0 , 255 , 176 ),
            (0 , 255 , 182 ),
            (0 , 255 , 188 ),
            (0 , 255 , 194 ),
            (0 , 255 , 200 ),
            (0 , 255 , 206 ),
            (0 , 255 , 212 ),
            (0 , 255 , 218 ),
            (0 , 255 , 224 ),
            (0 , 255 , 230 ),
            (0 , 255 , 236 ),
            (0 , 255 , 242 ),
            (0 , 255 , 248 ),
            (0 , 255 , 255 ),
            (0 , 248 , 255 ),
            (0 , 242 , 255 ),
            (0 , 236 , 255 ),
            (0 , 230 , 255 ),
            (0 , 224 , 255 ),
            (0 , 218 , 255 ),
            (0 , 212 , 255 ),
            (0 , 206 , 255 ),
            (0 , 200 , 255 ),
            (0 , 194 , 255 ),
            (0 , 188 , 255 ),
            (0 , 182 , 255 ),
            (0 , 176 , 255 ),
            (0 , 170 , 255 ),
            (0 , 164 , 255 ),
            (0 , 158 , 255 ),
            (0 , 152 , 255 ),
            (0 , 146 , 255 ),
            (0 , 140 , 255 ),
            (0 , 134 , 255 ),
            (0 , 128 , 255 ),
            (0 , 122 , 255 ),
            (0 , 116 , 255 ),
            (0 , 110 , 255 ),
            (0 , 104 , 255 ),
            (0 , 98 , 255 ),
            (0 , 92 , 255 ),
            (0 , 86 , 255 ),
            (0 , 80 , 255 ),
            (0 , 74 , 255 ),
            (0 , 68 , 255 ),
            (0 , 62 , 255 ),
            (0 , 56 , 255 ),
            (0 , 50 , 255 ),
            (0 , 44 , 255 ),
            (0 , 38 , 255 ),
            (0 , 32 , 255 ),
            (0 , 26 , 255 ),
            (0 , 20 , 255 ),
            (0 , 14 , 255 ),
            (0 , 8 , 255 ),
            (0 , 2 , 255 ),
            (4 , 0 , 255 ),
            (10 , 0 , 255 ),
            (16 , 0 , 255 ),
            (22 , 0 , 255 ),
            (28 , 0 , 255 ),
            (34 , 0 , 255 ),
            (40 , 0 , 255 ),
            (46 , 0 , 255 ),
            (52 , 0 , 255 ),
            (58 , 0 , 255 ),
            (64 , 0 , 255 ),
            (70 , 0 , 255 ),
            (76 , 0 , 255 ),
            (82 , 0 , 255 ),
            (88 , 0 , 255 ),
            (94 , 0 , 255 ),
            (100 , 0 , 255 ),
            (106 , 0 , 255 ),
            (112 , 0 , 255 ),
            (118 , 0 , 255 ),
            (124 , 0 , 255 ),
            (130 , 0 , 255 ),
            (136 , 0 , 255 ),
            (142 , 0 , 255 ),
            (148 , 0 , 255 ),
            (154 , 0 , 255 ),
            (160 , 0 , 255 ),
            (166 , 0 , 255 ),
            (172 , 0 , 255 ),
            (178 , 0 , 255 ),
            (184 , 0 , 255 ),
            (190 , 0 , 255 ),
            (196 , 0 , 255 ),
            (202 , 0 , 255 ),
            (208 , 0 , 255 ),
            (214 , 0 , 255 ),
            (220 , 0 , 255 ),
            (226 , 0 , 255 ),
            (232 , 0 , 255 ),
            (238 , 0 , 255 ),
            (244 , 0 , 255 ),
            (250 , 0 , 255 ),
            (255 , 0 , 252 ),
            (255 , 0 , 246 ),
            (255 , 0 , 240 ),
            (255 , 0 , 234 ),
            (255 , 0 , 228 ),
            (255 , 0 , 222 ),
            (255 , 0 , 216 ),
            (255 , 0 , 210 ),
            (255 , 0 , 204 ),
            (255 , 0 , 198 ),
            (255 , 0 , 192 ),
            (255 , 0 , 186 ),
            (255 , 0 , 180 ),
            (255 , 0 , 174 ),
            (255 , 0 , 168 ),
            (255 , 0 , 162 ),
            (255 , 0 , 156 ),
            (255 , 0 , 150 ),
            (255 , 0 , 144 ),
            (255 , 0 , 138 ),
            (255 , 0 , 132 ),
            (255 , 0 , 126 ),
            (255 , 0 , 120 ),
            (255 , 0 , 114 ),
            (255 , 0 , 108 ),
            (255 , 0 , 102 ),
            (255 , 0 , 96 ),
            (255 , 0 , 90 ),
            (255 , 0 , 84 ),
            (255 , 0 , 78 ),
            (255 , 0 , 72 ),
            (255 , 0 , 66 ),
            (255 , 0 , 60 ),
            (255 , 0 , 54 ),
            (255 , 0 , 48 ),
            (255 , 0 , 42 ),
            (255 , 0 , 36 ),
            (255 , 0 , 30 ),
            (255 , 0 , 24 ),
            (255 , 0 , 18 ),
            (255 , 0 , 12 ),
            (255 , 0 , 6 ),
            (255 , 0 , 0 ) ] )
        c.build()

def prtk(w):
    """Debugging utility to trace Tk widget trees"""
    print 'Widget :',w
    #print w.children
    for c in w.children.keys():
        print 'Child',c, w.children[c].__class__
        prtk(w.children[c])


def copycontents(to,fro):
    """Used to update an object by copying in the contents from another"""
    c = to.__class__
    d1 = c.__dict__
    try:
        d2 = fro.__dict__
    except AttributeError:
        d2 = {}
    for k in d2.keys():
        to.__dict__[k] = fro.__dict__[k]

if __name__ == "__main__":
    import sys
    #import profile

    # test imports
    try:
        import Scientific
    except ImportError:
        print "You need to install Scientific Python"
        sys.exit(-1)

    from vtkgraph import *
    root=Tk()
    root.withdraw()
    vt = VtkGraph(root)
    for file in sys.argv[1:]:
        print 'loading',file
        vt.load_from_file(file)
    vt.mainloop()
