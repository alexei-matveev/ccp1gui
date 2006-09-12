#!/usr/bin/env python

import srb
import os
import ConfigParser

class FailedLoginException(Exception):pass
class MissingLocalFileException(Exception):
    def __init__(self,args=None):
        self.args = args
    def __str__(self):
        return "srbftp: Missing Local file Exception for %s!" % self.args

class srb_ftp_interface(object):
    """
      FTP like interface to SRB allows uploading and downloading of files, plus creation of directories

      SRB parameters are held in a configuration file which should be of the form:

      [main]
      server: <server name>
      port: <port number>
      authmethod: <auth method>
      resource: <resource>
      domainhome: <domain>
      username: <username>
      password: <password>
      collectionhome: <collection home>

      The name of the configuration file is passed in when constructing this class

      The FTP commands supported (with a corresponding method) are:

      cd            Change directory on the remote (SRB) machine
      ls            List the names of the files in the current remote directory
      pwd           Find out the pathname of the current directory on the remote machine
      mkdir         Make a new directory within the current remote directory
      put           Copy a file from the local machine to the remote machine
      get           Copy a file from the remote machine to the local machine
      delete        Delete a file in the current remote directory
      lls           List the names of the files in the current local directory
      lpwd          Find out the pathname of the current directory on the local machine
      lcd           Change directory on the local machine
    """

    def __init__(self, config_file):


        if not config_file:
            raise IOError, 'srbftp needs a configuration file!'
            return
            
        config = ConfigParser.ConfigParser()

        fp = None
        try:
            fp = open(config_file)
        except Exception,e:
            print "Error opening srb configuration file: %s" % config_file
            print "Error is: %s" % e

        if not fp:
            raise IOError, 'Cannot open srb configuration file!'

        config.readfp( fp )

        self.SRBServerName = config.get('main', 'server')
        self.SRBPortNumber = config.get('main', 'port')
        self.SRBDomainHome = config.get('main', 'domainhome')
        self.SRBAuthMethod = config.get('main', 'authmethod')
        self.SRBResource   = config.get('main', 'resource')
        self.SRBUsername   = config.get('main', 'username')
        self.SRBPassword   = config.get('main', 'password')
        self.SRBHome       = config.get('main', 'collectionhome')

        self._pwd = self.sanitisePath(self.SRBHome)

        self._cid = srb.connect(self.SRBServerName, self.SRBPortNumber, self.SRBDomainHome, self.SRBAuthMethod, self.SRBUsername, self.SRBPassword, "")
        if self._cid < 0:
            raise FailedLoginException()

    def __del__(self):

        import srb # srb module needs to be reimported in order to close the connection
        srb.disconnect(self._cid)

    def cd(self, directory):

        if directory[0] == '/': # Absolute path
            self._pwd = self.sanitisePath(directory)
        elif directory[:2] == "..": # Up one directory
            parent, name = self.splitPath(self._pwd)
            self._pwd = parent
        elif directory[:3] == "../": # Up N directories
            parent, name = self.splitPath(self._pwd)
            self._pwd = parent
            self.cd(directory[3:]) # Recursively call this method to deal with multiple "../"s
        else: # Relative path
            self._pwd = self._pwd + "/" + self.sanitisePath(directory)

    def pwd(self):
        return self._pwd

    def ls(self, directory = None):
        """
        List the contents of the a remote directory.

        If a directory is passed in this will be listed, otherwise the current remote directory is listed.
        """

        if directory == None: directory = self._pwd

        content = []

        num_colls = srb.get_subcolls(self._cid, 0, directory)
        for i in range(num_colls):
            path = srb.get_subcoll_name(self._cid, i)
            parent, name = self.splitPath(path)
            content.append(name)

        num_objs = srb.get_objs_in_coll(self._cid, 0, 16, directory)
        for i in range(num_objs):
            name = srb.get_obj_metadata(self._cid, 0, i)
            content.append(name)

        return  content

    def mkdir(self, directory):
        if directory[0] == '/': # Absolute Path
            parent, child = self.splitPath(directory)
            srb.mk_collection(self._cid, 0, parent, child)
        else: # Relative Path
            srb.mk_collection(self._cid, 0, self._pwd, directory)

    def lcd(self, directory):
        os.chdir(directory)

    def lpwd(self):
        return os.getcwd()

    def lls(self):
        return os.listdir(os.getcwd())

    def delete(self, filename):
        srb.obj_delete(self._cid, filename, 0, self._pwd)

    def put(self, filename):

        # Check to see if local file exists

        if filename not in os.listdir(os.getcwd()):
            raise MissingLocalFileException(filename)

        # Create a list of files in the remote SRB directory so that you know to create
        # a new file or to truncate the existing one
    
        num_objs = srb.get_objs_in_coll(self._cid, 0, 16, self._pwd)

        objs = []

        for i in range(num_objs):
            objs.append(srb.get_obj_metadata(self._cid, 0, i)) # Create a list of files in collection

        # Test to see if filename is in list of files in the remote directory. 
        # If it is truncate the existing file
        # If it isn't create a new file to write into 

        if filename in objs:
            oflag = 513 # O_WRONLY = 1, O_TRUNC = 512, O_WRONLY | O_TRUNC = 513
            fd = srb.obj_open(self._cid, self._pwd, filename, oflag)
        else:
            fd = srb.obj_create(self._cid, 0, filename, '', self.SRBResource, self._pwd, '', -1)

        # Open the local file and write each line into the remote SRB file

        file = open(filename, 'r')

        while True:
            line = file.readline()
            if line == '':
                break
            srb.obj_write(self._cid, fd, line, len(line))

        # Close the local and remote files after use

        file.close()
        srb.obj_close(self._cid, fd)

    def get(self, filename):

        # Open the local and remote files

        file = open(filename, 'w')
        fd = srb.obj_open(self._cid, self._pwd, filename, 0)

        # Read data from the remote SRB file appending it to the local file

        offset = 0
        chunk_size = 1000

        while True:
            tmp = srb.obj_read(self._cid, fd, chunk_size)
            length = len(tmp)
            if length != 0:
                file.seek(offset)
                file.write(tmp)
                offset = offset + length
            else:
                break

        # Close the local and remote files after use

        file.close()
        srb.obj_close(self._cid, fd)


    def sanitisePath(self, path):
        """ Remove trailing '/' in path unless the path is '/'"""
        if path == '/':
            return '/'
        elif path[-1] == '/':
            return path[:-1]
        else:
            return path

    def splitPath(self, path):
        parent_name, name = self.sanitisePath(path).rsplit("/", 1)

        if parent_name == '':
            parent_name = '/'

        return parent_name, name
