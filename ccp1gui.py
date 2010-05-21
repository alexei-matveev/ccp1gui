#!/usr/bin/python
#
# Script to run the ccp1gui and inform the user if they don't have the required modules installed.
#

import os,sys
if __name__ == "__main__":
    # Need to add the gui directory to the python path so 
    # that all the modules can be imported
    gui_path = os.path.split(os.path.dirname( os.path.realpath( __file__ ) ))[0]
    sys.path.append(gui_path)

try:
    import Tkinter
    import tkMessageBox, tkFileDialog
except ImportError:
    # Need to work out something sensible to do here - fire up Windows gui etc
    sys.exit(1)

# Start root here and withdraw, otherwise we have the root Tk window hanging around looking lost
# when we fire up any dialogues
tkroot = Tkinter.Tk()
tkroot.withdraw()

try:
    import vtk
except ImportError:
    if sys.platform[:3]=='win':
        msg="""Sorry but the CCP1GUI cannot run because you do not appear to have a python-enabled vtk installed. Binaries can be downloaded from those kindly made available by Christoph Gohlke:

http:///www.lfd.uci.edu/~gohlke/pythonlibs/

If you use Christoph's binaries, make sure you download binaries for numpy and scipy as well.

Alternatively a packaged version of Python with vtk, numpy and scipy is available from Enthought:

http://www.enthought.com/products/epd.php

If using Christoph's binaries, extract the zip file and then copy the folder called "vtk" into:

C:\Python26\Lib\site-packages

(or similar for your system). You will also need to add the full path to this folder ("C:\Python26\Lib\site-packages\vtk") to your PATH environment variable.

If you can't, or have done that and are still seeing this message, click "Ok" to point us at where the zip file has been extracted.

Otherwise click "Cancel" to close this dialog."""
                
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
        # Linux/OSX branch for trying to import vtk
        pass

#
# Final checks under windows
#
if sys.platform[:3]=='win':
    # Here we should have Tkinter and vtk - Pmw we hope is in our directory so it's just
    # Mark Hammond's win32 extensions.
    try:
        import win32api
    except ImportError:
        msg="""Sorry but the CCP1GUI cannot run as you do not have the win32 extensions installed.

    These can be downloaded from the pywin32 website at:

    http://sourceforge.net/projects/pywin32

    Please install them and then try again."""
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
""" % dllname
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

