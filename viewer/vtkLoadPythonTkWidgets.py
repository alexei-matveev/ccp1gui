"""
This file is taken from the VTK project: http://www.vtk.org

VTK is an open-source toolkit licensed under the BSD license.

Copyright (c) 1993-2008 Ken Martin, Will Schroeder, Bill Lorensen
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    * Neither name of Ken Martin, Will Schroeder, or Bill Lorensen nor the names of any contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

import sys, os, string

def vtkLoadPythonTkWidgets(interp):
    """vtkLoadPythonTkWidgets(interp) -- load vtk-tk widget extensions

    This is a mess of mixed python and tcl code that searches for the
    shared object file that contains the python-vtk-tk widgets.  Both
    the python path and the tcl path are searched.
    """
    name = 'vtkRenderingPythonTkWidgets'
    pkgname = string.capitalize(string.lower(name))

    # find out if the file is already loaded
    loaded = interp.call('info', 'loaded')
    if string.find(loaded, pkgname) >= 0:
        return

    # create the platform-dependent file name
    prefix = ''
    if sys.platform == 'cygwin':
        prefix = 'cyg'
    elif os.name == 'posix':
        prefix = 'lib'
    extension = interp.call('info', 'sharedlibextension')
    filename = prefix+name+extension

    # create an extensive list of paths to search
    pathlist = sys.path
    # add tcl paths, ensure that {} is handled properly
    try:
        auto_paths = string.split(interp.getvar('auto_path'))
    except AttributeError:
        auto_paths = interp.getvar('auto_path')
    for path in auto_paths:
        prev = str(pathlist[-1])
        try:            
            # try block needed when one uses Gordon McMillan's Python
            # Installer.
            if len(prev) > 0 and prev[0] == '{' and prev[-1] != '}':
                pathlist[-1] = prev+' '+path
            else:
                pathlist.append(path)
        except AttributeError:
            pass
    # a common place for these sorts of things  
    if os.name == 'posix':
        pathlist.append('/usr/local/lib')

    # attempt to load
    for path in pathlist:
        try:
            # If the path object is not str, it means that it is a
            # Tkinter path object.
            if type(path) != str:
              path = path.string
            # try block needed when one uses Gordon McMillan's Python
            # Installer.
            if len(path) > 0 and path[0] == '{' and path[-1] == '}':
                path = path[1:-1]
            fullpath = os.path.join(path, filename)
        except AttributeError:
            pass
        if ' ' in fullpath:
            fullpath = '{'+fullpath+'}'
        if interp.eval('catch {load '+fullpath+' '+pkgname+'}') == '0':
            return

    # re-generate the error
    interp.call('load', filename)
    
