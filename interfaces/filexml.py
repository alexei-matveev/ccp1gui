
#import methods from the python wrapper

from _libpyagentx import *
from objects.zmatrix import *
from objects.vibfreq import *

class XMLReader:

    def __init__(self):

        self.objects=[]
        self.xml_error=0
        self.owl_file = None
        self.rdf_file = None
        
        #initialise

        axParserStart()
        
        #specify the number of evaluations to cache

        axCache(1000)

        #set the base URI for resources

        axBaseUri("http://www.grids.ac.uk/eccp/owl-ontologies#")

    def read_mappings(self,file):

        # load the mapping documents

        self.xml_error=0
        datafile="file://"+file
        self.xml_error=axGetUri(datafile)
        if not self.xml_error:
            self.rdf_file = file
        return self.xml_error

    def read_ontology(self,file):
    
        #load the ontology documents

        self.xml_error=0
        datafile="file://"+file
        self.xml_error=axGetUri(datafile)
        if not self.xml_error:
            self.owl_file = file
        return self.xml_error
    
    def read_data_file(self,file):
    
        #load the data documents

        self.xml_error=0
        datafile="file://"+file
        self.xml_error=axDataGetUri(datafile)

        return self.xml_error

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
                    vec=Vector([float(xv),float(yv),float(zv)])
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
        
        model = Zmatrix()
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
        
            a = ZAtom()
            
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

        self.objects.append(model)
        self.mol=model

        return self.xml_error
        

    def cleanup(self):

        #clean up
        
        axParserFinish()

if __name__ == "__main__":
    import os
    #agentXroot = "/Users/jmht/work/CODES/AGENTX/AgentX-0.3.6/"
    agentXroot = "/home/jmht/Documents/GuiCCP1/AgentX/AgentX-0.3.6"

    xd = XMLReader()
    
    # Read an ontology
    ontfile = agentXroot + "/ontology/ontology.owl"
    print "loading ",ontfile
    xd.read_ontology(ontfile)

    # Read a mapping file
    mapfile = agentXroot + "/map/map.rdf"
    xd.read_mappings(mapfile)
    print "loading ",mapfile

    # Read in the molecule
    datafile = agentXroot + "/examples/xml/dlpoly.xml"
    xd.read_data_file(datafile)
    print "loading ",datafile
    xd.read_coordinates(".xml")
    xd.read_normal()
    xd.cleanup()
 
    print "object1 is"
    for o in xd.objects:
        print o.title
        print len(o.atom)
        #print o.__dict__
    
    xd = XMLReader()
    xd.read_ontology(ontfile)
    xd.read_mappings(mapfile)
    datafile = agentXroot + "/examples/xml/siesta.xml"
    xd.read_data_file(datafile)
    xd.read_coordinates(".xml")
    xd.read_normal()
    xd.cleanup()

    print "object2 is"
    for o in xd.objects:
        print o.title
        print len(o.atom)
        #print o.__dict__
