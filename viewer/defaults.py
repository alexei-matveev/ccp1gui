import sys, os, re
import traceback

class Defaults:
    """ An object to hold the default values for the ccp1gui and
        read/write them from the ccp1gui rc file
    """

    
    debug = None
    defaults = {}

    if sys.platform[:3] == 'win':
        rcfile = os.path.expandvars('$USERPROFILE\ccp1guirc.py')
    else:
        rcfile = os.path.expandvars('$HOME/.ccp1guirc.py')

    def __init__(self):
        """ Initialise the object from default values and then from the rc file
        """

        if self.debug:print "initing defaults"
        self.set_defaults()
        self.read_from_file()


    def set_defaults(self):
        """
           Set the defaults for the ccp1gui
        """
        self.defaults['conn_scale'] = 1.0
        self.defaults['conn_toler']   = 0.5
        self.defaults['contact_scale'] = 1.0
        self.defaults['contact_toler']   = 1.5
        self.defaults['bg_rgb'] = (0,0,0)
        self.defaults['pick_tolerance'] = 0.01
        self.defaults['show_selection_by_colour'] = 1
        self.defaults['field_line_width']  =  1
        self.defaults['field_point_size']  =  2
        # Molecule variables
        self.defaults['mol_line_width']  =  3
        self.defaults['mol_point_size']  =  4
        self.defaults['mol_sphere_resolution'] = 8
        self.defaults['mol_sphere_specular'] = 1.0
        self.defaults['mol_sphere_diffuse'] = 1.0
        self.defaults['mol_sphere_ambient'] = 0.4
        self.defaults['mol_sphere_specular_power'] = 5
        self.defaults['mol_cylinder_resolution'] = 8
        self.defaults['mol_cylinder_specular'] = 0.7
        self.defaults['mol_cylinder_diffuse'] = 0.7
        self.defaults['mol_cylinder_ambient'] = 0.4
        self.defaults['mol_cylinder_specular_power'] = 10
        # Executable, script and directory locations
        self.defaults['am1'] = None
        self.defaults['chemsh_script_dir'] = None
        # Stereo visulaisation
        self.defaults['stereo'] = None
        # dont remember paths between restarts
        self.defaults['old_path'] = 0
        # dont prompt for guk input file overwrites
        self.defaults['guk_check_overwrite_input'] = 0
        self.defaults['user_path'] = None


    def read_from_file(self):
        """
        Read the users rc file from disk and populate the defaults dictionary
        """

        if not os.path.isfile( self.rcfile ):
            # No ccp1guirc file so we can return
            if self.debug:print "No user preferences file: %s found" % self.rcfile
            return
        
        # Pull any variables out
        defaults_buff = []
        f = open( self.rcfile )

        for line in f.readlines():
            defaults_buff.append(line)
        f.close()

        for line in defaults_buff:
            if re.compile( '###################### End User Defaults #####################' ).match( line ):
                break
            elif re.compile( '^[a-zA-Z][a-zA-Z1-9 _-]*={1}.*' ).match( line ):
                # Re is anything beginning at the start of a line with a letter that has a string of letters
                # and numbers followed by a single equals sign - this _should_ cover most things...
                split = line.split('=')
                key = split[0].strip()
                value = split[1].strip()

                # Need to instantiate each value as otherwise it is just a string and we need an object
                value = eval(value)

                # Set as an attribute of defaults
                self.defaults[key] = value

    def write_to_file(self):
        """ Write the update default values to file"""

        if self.debug: print "writing ccp1guirc file"

        # Save the user path to the dictionary so that we can
        # start from there on a restart
        #rc_vars['user_path'] = paths['user']
        

        if not os.path.isfile( self.rcfile ):
            # No ccp1guirc file found, so just dump out the dictionary to a new ccp1guirc file
            try:
                rc_file = open( self.rcfile, 'w' ) # Open File in write mode
            except IOError,e:
                print "Cant create user rc file. I give up..."
                traceback.print_exc()
                return

            rc_file.write("# This ccp1guirc file has been created by the CCP1GUI as no\n")
            rc_file.write("# user file could be found\n#\n#\n")
            for name,value in self.defaults.iteritems():
                if type(value) is str:
                    # Need to quote strings
                    rc_file.write( "%s = \'%s\'\n" % ( name, str(value) ) )
                else:
                    rc_file.write( "%s = %s\n" % ( name,str(value) ) )

            rc_file.write( '###################### End User Defaults #####################\n' )
            # Have dumped dictionary so quit here
            return

        # Read the file into a buffer
        try:
            rc_file = open( self.rcfile, 'r' )
            rc_buff = rc_file.readlines()
            rc_file.close()
        except Exception,e:
            print "Error reading ccp1guirc file!"
            traceback.print_exc()
            return

        # For each line of the file, if a variable appears at the start of the line
        # we replace the old value with the one from the rc_vars dictionary
        count = 0
        last_var = 0
        keys = [] # list to remember which keys we have written out
        for line in rc_buff:
            for var_name in self.defaults.keys():
                re_str = '^'+var_name+' *='
                if re.compile( re_str ).match( line ):
                    last_var = count
                    keys.append( var_name )
                    # replace that line in the buffer with the new value
                    if type(self.defaults[var_name]) is str:
                        rc_buff[ count ] = "%s = \'%s\'\n" % (var_name, str(self.defaults[var_name]) )
                    else:
                        rc_buff[ count ] = "%s = %s\n" % (var_name, str(self.defaults[var_name]) )
            count += 1

        # Now see if there are any variables in the self.defaults that we didn't write out
        # because they have been added this session. We add these into the file at the
        # spot we found the last variable.
        newvar_buff = []
        for key,var in self.defaults.iteritems():
            if  key not in keys:
                if type(self.defaults[key]) is str:
                    newvar_buff.append("%s = \'%s\'\n" % (key, str(self.defaults[key]) ))
                else:
                    newvar_buff.append("%s = %s\n" % (key, str(self.defaults[key]) ))
                    
        if len(newvar_buff) > 0:
            for line in newvar_buff:
                rc_buff.insert(last_var+1,line)

        # Write out the ammended file
        try:
            rc_file = open( self.rcfile, 'w')
            for line in rc_buff:
                rc_file.write( line )
        except Exception:
            print "Can't write rc_file %s " % self.rcfile
            print "Error is:"
            traceback.print_exc()
        

    def get_value(self,name):
        """
        Return a value from the defaults dictionary
        Empty strings are returned as None
        """

        value= None
        if self.defaults.has_key( name ):
            value = self.defaults[ name ]
            if type(value) == str and len(value) == 0:
                value = None
        return value
            

    def set_value(self,name,value):
        """
        Set a value in the defaults dictionary
        Empty strings are set as None
        """

        if type(value) == str and len(value) == 0:
            value = None
        self.defaults[ name ] = value

    def iteritems(self):
        """ call the iteritems function on self.defaults"""
        return self.defaults.iteritems()

    def keys(self):
        """ call the iteritems function on self.defaults"""
        return self.defaults.keys()

    def values(self):
        """ call the iteritems function on self.defaults"""
        return self.defaults.values()


# Instantiate the object that everything can use
defaults = Defaults()
