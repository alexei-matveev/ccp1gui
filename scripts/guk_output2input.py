
import sys,os,re,getopt

from interfaces.gamessuk import GAMESSUKCalc
from interfaces.gamessoutputreader import GamessOutputReader
from objects.zmatrix import Zmatrix, ZmatrixSequence
#from ccp1gui.interfaces.filepunch import PunchReader
from interfaces.filepunch import PunchReader


def get_input_from_output( ofile ):
    """Return a list with the input"""

    debug = 0
    fd = open( ofile,'r')

    inputl = []
    inputre =  re.compile('^ >>>>> ')
    line = fd.readline()
    while line:
        if inputre.match( line ):
            inputl.append( line[7:] )
            break
        line =fd.readline()
    
    if not len( inputl ):
        # got to the end of the file and didn't match inputre
        return None

    line = fd.readline()
    while inputre.match( line ):
        inputl.append( line[7:] )
        line = fd.readline()

    fd.close()
    
    if debug:
        print "input"
        for l in inputl:
            print l,

    return inputl


def get_last_geom_from_file( filepath, ftype, request_z=None):
    """Read a GAMESS-UK output or punch file to get the last geometry and
       return this as a list suitable for writing out to file
      if request_z is set we try and return a zmatrix
    """
    debug = 0

    output=None
    punch=None

    if ftype == 'out':
        output = filepath
    elif ftype == 'pun':
        punch = filepath
    else:
        print "File needs to be a punch (.pun) or an ouptut file (.out)"
        sys.exit(1)


    molecules = []
    sequence = None

    if ftype == 'pun':
        print "Scanning punch file: %s" % punch
        reader = PunchReader()
        reader.scan( punch )
        objects = reader.objects
    elif ftype == 'out':
        print "Scanning output file: %s" % output
        reader = GamessOutputReader( output )
        objects = reader.molecules

    # Grab a molecule or sequence
    for o in objects:
        # take the last field of the class specification
        t1 = str(o.__class__).split('.')
        myclass = t1[len(t1)-1]

        #print 'LOADING up',myclass
        if myclass == 'Indexed' or myclass == 'Zmatrix':
            molecules.append( o )

        elif myclass == 'ZmatrixSequence':
            o.connect()
            sequence = o

    # Create a molecule object from the last one
    if len(molecules):
        mol = molecules[-1]
    elif sequence:
        mol = sequence.frames[-1]
        mol.name = mol.title

    # Now write out the new geometry
    calc = GAMESSUKCalc()
    lastgeom = calc.write_molecule( mol, request_z=request_z)

    if debug:
        print "lastgeom"
        for l in lastgeom:
            print l,

    return lastgeom

def update_input_geom( oldinput, lastgeom ):
    """ Take the gamessuk input oldinput (as a list) and replace the geometry
        section with that from lastgeom (also a list)
    """

    startgeom = re.compile( '^ *geom|^ *zmat',re.IGNORECASE )
    endgeom = re.compile( '^ *end',re.IGNORECASE )

    newinput = []
    skip = None
    for line in oldinput:
        if startgeom.match( line ):
            skip = 1
            newinput += lastgeom # insert the last geometry
        elif endgeom.match( line ):
            if skip:
                skip = None
                continue
        if not skip:
            #print "addding line: %s " % line
            newinput.append( line)

    return newinput


def usage():
    print """
This script will take a GAMESS-UK output file extract the last geometry
calculated and create a new input file (with the same options as old one),
but with the last geometry as the input geometry.

Usage is: %s [options] <GAMESS-UK_output_file>

Options:
-h,--help           print this help
-z,--zmtarix       try and create input geometry as zmatrix
                    (default is Cartesian)
""" % sys.argv[0]

try:
    opts, args = getopt.getopt(sys.argv[1:], "zh", ["zmatrix","help"])
except getopt.GetoptError:
    # print help information and exit:
    usage()
    sys.exit(2)

request_z=None
filepath=None
for o, a in opts:
    if o in ("-z","--zmatrix"):
        request_z = True
    if o in ("-h", "--help"):
        usage()
        sys.exit()

if len(args) == 1:
    filepath = args[0]
else:
    usage()
    sys.exit(2)

filepath = os.path.abspath( filepath )
directory, filename = os.path.split( filepath )
ftype = os.path.splitext( filename )[1].lower()[1:] # remove dot from extension
filename = os.path.splitext( filename )[0]

lastgeom = get_last_geom_from_file( filepath, ftype, request_z=1)
oldinput = get_input_from_output( filepath )
newinput = update_input_geom( oldinput, lastgeom )

newname = filename+'.in'
inputf = open( newname, 'w' )
for line in newinput:
    inputf.write( line )
print "Wrote input file: %s" % newname
inputf.close()
