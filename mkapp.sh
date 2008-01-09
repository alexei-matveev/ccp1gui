#!/bin/bash
#
# This script encompases everything I know about how to build the ccp1gui bundle
# on mac osx - it covers a few hacks that work around problems with the
# tools
#
# Firstly need to patch the distutils used by py2app. For instructions on how to
# do this see the setup.py file. py2app uses it's own disutils, so the build_py.py
# file that needs to be edited actually lives in the setuptools egg in the site-packges
# directory, which needs to be unzipped to access the files.
#
# To get the universal vtk build to work we need to use CVS versions of both
# vtk and cmake. The following Cmake variables need to be set:
#
# BUILD_SHARED_LIBS: ON
# CMAKE_OSX_ARCHITECTURES: ppc;i386
# VTK_USE_CARBON: ON
# VTK_USE_COCOA: OFF ( Default is on but 64-bit Tk not available: http://www.nabble.com/No-64-bit-Carbon--3D-Problem-for-Tk-Aqua--to11163138.html )
# VTk_WRAP_PYTHON: ON
# VTK_WRAP_TCL: ON
#
# There is a problem with how the vtk window interacts with the Tk window in
# the latest version of Active Tcl (8.4.16 and above). This manifests itself by
# the VTK window not being in the centre of the Tk window. This problem isn't
# present in TclTkAqua 8.4.10, although this is not a universal build. In the 
# end I was able to fix this by removing all the Tk/Tlc installations apart 
# from those in /System/Library/Frameworks which are 8.4 appear to be 
# universal binaries
#
# It also seems that for the time being, Tk 8.5 is not recommended
# http://mail.python.org/pipermail/python-dev/2007-December/075725.html
#
# Scientific python isn't packaged properly, as the .so files in the darwin
# subdirectory aren't found so these need to be copied across manually
#
# The VTK .so files that end up in the ccp1gui.app lib-dynload directory are
# the wrong ones and need to be symlinked to the ones on the Framework directory
#
# Any __import__ statements in the gui (currently only basis/basismanager.py)
# need to be changed as in:
#
# Below for the block of code ~line 40
#
#import basis.custom
#basis_module['custom'] = getattr(basis,"custom")
#
# Below for the bit of code in define_keyword_basis (~ 109 )
#
# import basis.keyword
# basis_module[keyword] = getattr(basis,'keyword')
#
# Icons - it should be possible to set the icon using the CFBundleIconFile
# key in the Info.Plist file, although this doesn't work for me. Instead,
# 1. Open a picture with the desired icon
# 2. Apple-C to copy it
# 3. Click on the ccp1gui.app folder and Apple-I to bring up the info box
# 4. Click on the icon in the upper LHC of the window and Apple-V to paste the pic
#
#
# To create the disk image for distribution:
# hdiutil create -srcfolder ./ccp1gui.app ./ccp1gui

# Hard-wired paths to directories

# bin directory of where the vtk build took place
vtkbuilddir=/Users/jmht/work/codes/CCP1GUI/ccp1gui_app/vtk/VTK_cvs_build/bin

# Where the Scientific Python .so files live
scisodir=/Library/Frameworks/Python.framework/Versions/2.5/lib/python2.5/site-packages/Scientific/darwin

# Internal app directories
fworkdir=dist/ccp1gui.app/Contents/Frameworks
dynlibdir=dist/ccp1gui.app/Contents/Resources/lib/python2.5/lib-dynload

# Create the application bundle
python setup.py py2app --frameworks \
$vtkbuilddir/libvtkRenderingPythonTkWidgets.5.1.0.dylib,\
$vtkbuilddir/libvtkRenderingPythonTkWidgets.5.1.dylib,\
$vtkbuilddir/libvtkRenderingPythonTkWidgets.dylib || exit 1

# Now copy Scientific .so files into it
# Need to manually copy these as using the --frameworks
# option puts them in the Frameworks directory, which isn't
# suitable
echo "Copying Scientific .so files"
for so in `ls ${scisodir}/*.so`
do
    echo "Copying $so ..."
    cp $so $dynlibdir/
done

# Now need to delete the errant vtk .so files and create symlinks
# Need relative paths so cd to the directory first
echo "Creating symlinks in $dynlibdir"
pushd $dynlibdir
fdir=../../../../Frameworks
for so in `ls libvtk*.so`
do
    rm -f $so
    ln -s ${fdir}/$so .
done
popd
