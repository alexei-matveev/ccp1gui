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
"""helper module to manage pathnames
"""

# see http://www.pythonmac.org/wiki/FAQ#head-c88c53edb2f911e57c92adf2625ca2b73aa6fc6d
import os
import sys
import tarfile
import shutil
import __main__

version=sys.version_info #The version of python we are using

try:
    # Below accpeted way of doing things for Python > 2.2
    mainscriptdir=os.path.dirname(os.path.abspath(__main__.__file__))
except AttributeError:
    import debug
    x=os.path.abspath(debug.__file__) # Get the full path to the debug file
    mainscriptdir=os.path.dirname(x)

gui_path = os.path.split(mainscriptdir)[0]
root_path = os.path.split(gui_path)[0]
python_path = os.path.split(os.__file__)[0]
user_path = root_path

paths = {}
paths['root'] = root_path
paths['gui'] = gui_path
paths['python'] = python_path
paths['user'] = user_path
        
#### Useful functions #####
def find_exe( executable,path=None ):
    """
         Find an executable - return the path to the excutable or None if
         the executable can't be found.
         
        'paths' - a list of additional paths to search aside from the system and gui paths
    """

    print "Trying to find executable: ",executable

    if path:
        assert type(path) == list, "find_exe paths argument requires a list of paths to search!"
        pathlist = path
    else:
        pathlist = []
    
    # Get list of paths
    ospath = os.environ['PATH']
    pathlist += ospath.split( os.pathsep )

    # Always append the main ccp1gui directory & the root directory
    pathlist.append( paths['gui'] )
    pathlist.append( paths['root'] )

    exe = None
    got = None
    for path in pathlist:
        fname = path + os.sep + executable
        if os.access( fname, os.X_OK):
            exe = os.path.abspath( fname )
            got = 1
            break
    return exe

def backup_dir(directory):
    """ Tar and gzip a given directory and then delete the directory.
    """

    print "Backing up directory %s" % directory
    nbackup = 15 # Number of supported backup copies
    
    zipname = directory + ".tar.gz"
    if os.access( zipname, os.F_OK ):
        for i in range(nbackup):
            newname = zipname + "." + str(i)
            if not os.access( newname, os.F_OK ):
                zipname = newname
                break
            if i == nbackup-1:
                print "backup_dir ran out of backups!"
                return None
            
    # zipname is now the name of the new archive
    t = tarfile.open( zipname,'w:gz')
    for dlist in os.walk( directory ):
        for f in dlist[2]:
            fpath = os.path.join( dlist[0],f )
            print "Adding file: %s" % fpath
            t.add( fpath )

    t.close()
    

if __name__ == "__main__":
    print 'Python',python_path
    print 'GUI   ',gui_path
    print 'Root  ',root_path
    print 'User  ',user_path
