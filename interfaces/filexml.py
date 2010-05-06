# import python modules
import os

#import methods from the python wrapper
from _libpyagentx import *

# import internal modules
import objects.zmatrix
import objects.vector
from viewer.defaults import defaults
from fileio import FileIO
from objects.vibfreq import *
        

class XML_IO(FileIO):

    def __init__(self,**kw):


        # Initialise base class
        FileIO.__init__(self,**kw)

        self.debug=1
        
        # State what our capabilites are
        self.can_read = True
        self.can_write = [ 'Zmatrix','Indexed' ]

        #self.objects=[]
        self.xml_error=0
        self.owl_file = None
        self.rdf_file = None
        
        #initialise

        axParserStart()
        
        #specify the number of evaluations to cache

        axCache(1000)

        #set the base URI for resources

        axBaseUri("http://www.grids.ac.uk/eccp/owl-ontologies#")

    def ReadFile(self, filepath=None, **kw ):
        """ Need to overwrite this to not set self.read to as we call
            this multiple times to read in the ontology, mapping etc.
        """
        if filepath:
            self._ParseFilepath( filepath )
                
        self._ReadFile(**kw)
        

    def _ReadFile(self,**kw):
        """ This will be called to read all three filetypes (ontology, mappings and xml)
            so it needs to determine it's actions from the file suffix
        """

        # For the time being use the file extensions to determine the filetype
        if self.ext == '.owl':
            # Ontology
            err = self.read_ontology( self.filepath )
            if err:
                print "####  There was an error reading the ontology file!  ####"
                return
            
            if self.debug:print "DEBUG: Read ontology from: %s " % self.filepath
            # set the defaults so that we don't have to read this in each time
            defaults.set_value('AgentX_ontology', self.filepath )
            return
                
        elif self.ext == '.rdf':
            # Mapping file
            err = self.read_mappings(self.filepath)
            if err:
                print "### There was an error reading the Mapping file! ####"
                return
            
            if self.debug: print "Read mapping from: %s " % self.filepath
            # set the defaults so that we don't have to read this in each time
            defaults.set_value('AgentX_mapping', self.filepath )
            return
                
        elif self.ext == '.xml':
            # data file
            self.read_datafile( self.filepath )
        else:
            print "XMLReader _readefile unknown filtype for file: %s" % self.filepath

        return

    def read_mappings(self,filepath):

        # load the mapping documents

        if self.debug: print "DEBUG reading mappings from %s" % filepath

        self.xml_error=0
        datafile="file://"+filepath
        self.xml_error=axGetUri(datafile)
        if not self.xml_error:
            self.rdf_file = filepath
            if self.debug:
                print "DEBUG: set rdf_file to ",self.owl_file,id(self.owl_file)
                print "DEBUG self is ",id(self)
                
        return self.xml_error

    def read_ontology(self,filepath):

        if self.debug: print "DEBUG reading ontology from %s" % filepath

        #load the ontology documents

        self.xml_error=0
        datafile="file://"+filepath
        self.xml_error=axGetUri(datafile)
        if not self.xml_error:
            self.owl_file = filepath
            #print "DEBUG: set owl_file to ",self.owl_file,id(self.owl_file)
            #print "DEBUG self is ",id(self)

        return self.xml_error
    
    def _read_datafile(self,filepath):
    
        #load the data documents

        print "_read_datafile: ",filepath

        self.xml_error=0
        datafile="file://"+filepath
        self.xml_error=axDataGetUri(datafile)

        return self.xml_error

    def read_datafile(self,filepath):
        """ Read in an xml output using agentX """

        if self.debug: print "DEBUG reading datafile from %s" % filepath
        
        global defaults
        
        # Can't check if we don't have ontology/mapping files as AgentX can get it's mappings and
        # ontologies from the working directory or a URL can be embedded in the actual xml file,
        # so not having a mapping or ontology cannot be considered an error

         # If the reader does not already have on owl or map file, we check to see if there
         # is one in the defaults
         
         
        #print "DEBUG: owl file is ",id(self.owl_file)
        #print "DEBUG: self is ",id(self)
        if not self.owl_file:
            #print "checking defaults for an ontology file..."
            # See if we've ontology/mapping files in the defaults and load then if so
            ofile = defaults.get_value( 'AgentX_ontology' )
            if ofile and os.access( ofile, os.R_OK):
                err = self.read_ontology(ofile)
                if err == -1:
                    print "Error reading in existing ontology from defaults: %s" % ofile
                else:
                    print "Read in AgentX ontology file specified in defaults: %s" % ofile
                        
        if not self.rdf_file:
            #print "checking defaults for a mapping file..."
            ofile = defaults.get_value( 'AgentX_mapping' )
            if ofile and os.access( ofile, os.R_OK):
                err = self.read_mappings(ofile)
                if err == -1:
                    print "Error reading in AgentX mapping file specified in defaults: %s" % ofile
                else:
                    print "Error eading AgentX mapping file from defaults: %s" % ofile

        self._read_datafile(self.filepath)
        if(self.xml_error):
            print "Error while reading XML data file!"
            return None
        
        self.read_coordinates(self.name)
        if(self.xml_error):
            print "Error while reading XML coordinates!"
            return None
        
        self.read_normal()
        if(self.xml_error):
            print "Error while reading XML normal coordinates!"
            return None
        
        # Reading went o.k. so if there are any objects copy them so
        # that we can destroy the xd reader object - otherwise it persists
        # and keeps using the old data objects - currently there is no way
        # to destory the data objects and keep the owl and map file references
        #objects = copy.deepcopy (xd.objects)
        
        # Destroy reader
        self.cleanup()

    def read_normal(self):

        self.xml_error=0

        noModes=0
        noMolecules=axSelect("Molecule")
        if(noMolecules==-1):
            self.xml_error=-1
            return -1
        if(noMolecules>0):noModes=axSelect("NormalMode")
        if(noModes==-1):
            self.xml_error=-1
            noModes=0
            
        for i in range(0,noModes):
            v = VibFreq(i+1)
            v.displacement=[]
            noCoords=axSelect("normalCoordinate")
            if(noCoords==-1):self.xml_error=1
            if(noCoords>=3):
                for j in range(0,(noCoords/3)):
                    xv=axValue()
                    axSelectNext()
                    yv=axValue()
                    axSelectNext()
                    zv=axValue()
                    axSelectNext()
                    vec=objects.vector.Vector([float(xv),float(yv),float(zv)])
                    v.displacement.append(vec)
                axDeselect()
                noprop=axSelect("frequency");
                if(noprop):
                    v.freq=float(axValue())
                    t='v%-10.0f' % v.freq
                    v.title = t
                    axDeselect()
            v.reference=self.mol
            self.objects.append(v)
            axSelectNext()
            
        if(noMolecules>0):axDeselect()
        if(noModes>0):axDeselect()

        return self.xml_error
 
    def read_coordinates(self,root):

        if self.debug: print "DEBUG: read_coordinates"

        self.xml_error=0
        
        cnt=0

#        fac = 0.529177
        fac = 1
        
        #find all the data sets that relate to the concept 'Molecule'
        
        noMolecule=axSelect("Molecule")
        if(noMolecule==-1):
            print "Error selecting Molecule in read_coordinates!"
            self.xml_error=-1
            return -1
        elif(noMolecule==0):
            print "No molecules found when reading coordinates!"
            self.xml_error=-1
            return -1
        
        #find all the data sets, for the first Molecule, that relate to the
        #concept of Atom
        
        noatom=0
        noatom=axSelect("Atom")
        if noatom == 0:
            print "No atoms found when reading coordinates!"
            self.xml_error=-1
            return -1
        
        model = objects.zmatrix.Zmatrix()
        model.tidy=None
        
        trans = string.maketrans('a','a')
        
        for i in range(0,noatom):

            #for each Atom, get the x, y and z coordinates
            
            noprop=axSelect("xCoordinate")
            x = float(axValue())
            if(noprop):axDeselect()
                
            noprop=axSelect("yCoordinate")
            y = float(axValue())
            if(noprop):axDeselect()
            
            noprop=axSelect("zCoordinate")
            z = float(axValue())
            if(noprop):axDeselect()
            else: z=0.0
        
            a = objects.zmatrix.ZAtom()
            
            a.coord = [x*fac,y*fac,z*fac]
            
            noprop=axSelect("elementType")
            symbol=axValue()
            if(noprop):axDeselect()
            
            a.symbol = string.translate(symbol,trans,string.digits)
            a.symbol = string.capitalize(a.symbol)
            a.name = symbol
            a.index = cnt
            cnt = cnt + 1
            
            model.atom.append(a)
            
            #select the next atom
            
            axSelectNext()
            
        if(noatom):axDeselect()
        if(noMolecule):axDeselect()

        #self.objects.append(model)
        #print "got molecule ",model.atom
        self.molecules.append(model)
        self.mol=model

        return self.xml_error
        

    def cleanup(self):

        #clean up
        
        axParserFinish()

if __name__ == "__main__":
    import os
    agentXroot = "/home/jmht/Documents/codes/AgentX/AgentX-0.3.6"

    xd = XML_IO()
    
    # Read an ontology
    ontfile = agentXroot + "/ontology/ontology.owl"
    print "loading ",ontfile
    xd.ReadFile(filepath=ontfile)

    # Read a mapping file
    mapfile = agentXroot + "/map/map.rdf"
    print "loading ",mapfile
    xd.ReadFile(filepath=mapfile)

    # Read in the molecule
    datafile = agentXroot + "/examples/xml/dlpoly.xml"
    print "loading objects from",datafile
 
    for o in xd.GetObjects( filepath=datafile):
        print o.title
        print len(o.atom)
        #print o.__dict__
    
#     xd = XML_IO()
#     #xd.read_ontology(ontfile)
#     #xd.read_mappings(mapfile)
#     xd.ReadFile(filepath=ontfile)
#     xd.ReadFile(filepath=mapfile)
#     datafile = agentXroot + "/examples/xml/siesta.xml"
#     #xd.read_data_file(datafile)
#     xd.ReadFile(filepath=datafile)
#     #xd.read_coordinates(".xml")
#     #xd.read_normal()
#     #xd.cleanup()

#     print "object2 is"
#     for o in xd.GetObjects():
#         print o.title
#         print len(o.atom)
#         #print o.__dict__
