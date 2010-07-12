#!/usr/bin/python
#
# Script to run the ccp1gui and inform the user if they don't have the required modules installed.
#

import os,sys,platform
import traceback


def get_install_info():
    """Return a message telling the user what they need to install on a particular platform"""


    #
    # Dictionary mapping system->advice
    #
    install_info = {

#
# SuSE
#
        'SuSE' : """Sorry but the CCP1GUI cannot run on your system as some additional Python modules are not available.

Under SuSE, the following rpm files will need to installed:

python-tk
vtk-python

In addition, to access the full functionality of the CCP1GUI you should also install:

python-numpy
python-scipy

If you have problems getting any of the above to work, please send an email describing your problems to the user list at ccp1gui-users@lists.sourceforge.net""",

#
# Ubuntu
#
        'Ubuntu' : """Sorry but the CCP1GUI cannot run on your system as some additional Python modules are not available.

Under Ubuntu, the following packages need to installed:

python-tk
python-vtk
python-pmw
python-numeric
python-numeric-ext

These packages can be installed using apt-get or synaptic if the Universe repositories have been enabled. For advice on how to do this see:

http://help.ubuntu.com/community/Repositories/Ubuntu

If you have problems getting any of the above to work, please send an email describing your problems to the user list at ccp1gui-users@lists.sourceforge.net""",

#
# Windows
#
        'Windows' : """Sorry but the CCP1GUI cannot run because you do not appear to have a python-enabled vtk installed. Binaries can be downloaded from those kindly made available by Christoph Gohlke:

http:///www.lfd.uci.edu/~gohlke/pythonlibs/

If you use Christoph's binaries, make sure you download binaries for numpy and scipy as well.

Alternatively a packaged version of Python with vtk, numpy and scipy is available from Enthought:

http://www.enthought.com/products/epd.php

If using Christoph's binaries, extract the zip file and then copy the folder called "vtk" into:

C:\Python26\Lib\site-packages

(or similar for your system). You will also need to add the full path to this folder ("C:\Python26\Lib\site-packages\vtk") to your PATH environment variable.

If you can't, or have done that and are still seeing this message, click "Ok" to point us at where the zip file has been extracted.

Otherwise click "Cancel" to close this dialog.

If you have problems getting any of the above to work, please send an email describing your problems to the user list at ccp1gui-users@lists.sourceforge.net"""


        }

    # Work out the platform and return the message
    if platform.system() == 'Windows':
        return install_info['Windows']
    elif platform.system() == 'Linux':
        # In future use platform.linux_distribution, but for now keep backwards compatibility
        if platform.dist()[0].strip() == 'SuSE':
            return install_info['SuSE']
        elif platform.dist()[0].strip() == 'Ubuntu':
            return install_info['Ubuntu']
    
    return """\
Sorry, we haven't tested the CCP1GUI on your type of system so don't know the names of the modules you need to install.

Please email ccp1gui-users@lists.sourceforge.net for advice on how to get the CCP1GUI working on your system."""


# Need to add the gui directory to the python path so 
# that all the modules can be imported
gui_path = os.path.split(os.path.dirname( os.path.realpath( __file__ ) ))[0]
sys.path.append(gui_path)

try:
    import Tkinter
    import tkMessageBox, tkFileDialog
except ImportError:
    # Need to work out something sensible to do here - e.g. fire up native gui on Windows gui etc.
    #
    # print traceback
    #
    traceback.print_exc()
    #
    # Now our message
    msg = get_install_info()
    print "\n"
    print msg
    sys.exit(1)


# Start root here and withdraw, otherwise we have the root Tk window hanging around looking lost
# when we fire up any dialogues
tkroot = Tkinter.Tk()
tkroot.withdraw()

try:
    import vtk
except ImportError:
    if platform.system() =='Windows':
        #
        # Windows somewhat special - if they couldn't install the vtk stuff into their Python installation
        # or aren't too sure how to set environment variables etc, we try and help them.
        #
        msg = get_install_info()
        if not tkMessageBox.askokcancel(message=msg):
            sys.exit(1)

        # Got a yes so work out where the binaries are and set the PATH and PYTHONPATH accordingly
        vtkroot = tkFileDialog.askdirectory()
        if not vtkroot:
            # No directory so quit
            sys.exit(1)

        #vtkroot="C:\Users\jmht\Downloads\VTK-5.4.2-win32-py2.6"
        vtkbin=vtkroot+os.sep+'vtk'

        # Add to PATH and PYTHONPATH
        os.environ['PATH']+=os.pathsep+vtkbin
        sys.path.append(vtkroot)

    else:
        # Get traceback string
        msg=traceback.format_exc()+"\n"
        # Add our message to it
        msg+=get_install_info()
        tkMessageBox.showinfo(message=msg)
        sys.exit(1)

#
# Final checks under Windows
#
if platform.system() =='Windows':
    # Here we should have Tkinter and vtk - Pmw we hope is in our directory so it's just
    # Mark Hammond's win32 extensions.
    try:
        import win32api
    except ImportError:
        msg="""Sorry but the CCP1GUI cannot run as you do not have the win32 extensions installed.

    These can be downloaded from the pywin32 website at:

    http://sourceforge.net/projects/pywin32

    Please install them and then try again.

    If you continue to experience problems, please send an email describing your problems to the user list at ccp1gui-users@lists.sourceforge.net"""
        tkMessageBox.showinfo(message=msg)
        sys.exit(1)

    #
    # Finally, make sure we can load the vtkRenderingPythonTkWidgets.dll
    #
    r=None
    try:
        import viewer.vtkTkRenderWidgetCCP1GUI
        r=viewer.vtkTkRenderWidgetCCP1GUI.vtkTkRenderWidgetCCP1GUI(tkroot)
    except Tkinter.TclError,e:
        #
        # See if the vtkRenderingPythonTkWidgets.dll is in the vtk directory
        #
        dllname='vtkRenderingPythonTkWidgets.dll'
        vtkdir=os.path.dirname(vtk.__file__)
        dllfile=vtkdir+os.sep+dllname
        if os.access(dllfile,os.X_OK):
            # Found the dll file so add to the system path
            os.environ['PATH']+=os.pathsep+vtkdir
            print "Added: %s to PATH environment variable." % vtkdir
        else:
            msg="""Sorry, but the CCP1GUI cannot start as the vtk dll %s cannot be loaded.
This file needs to be in your system path. If you can find this file, please add the directory to the PATH environment variable and restart the CCP1GUI.

If you continue to experience problems, please send an email describing your problems to the user list at ccp1gui-users@lists.sourceforge.net""" % dllname
            tkMessageBox.showinfo(message=msg)
            sys.exit(1)

    # We might still have the r vtkTkRenderWidgetCCP1GUI hanging around - it doesn't seem to cause problems
    # but destroy anyway
    if r:
        r.destroy()
        

# Everything should be set up now so run and pray...        
import viewer.vtkgraph

vt = viewer.vtkgraph.VtkGraph(tkroot)
for file in sys.argv[1:]:
    print 'loading',file
    vt.load_from_file(file)
    
vt.mainloop()  

