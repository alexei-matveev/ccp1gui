import xml.sax
import sys, StringIO
from UserDict import UserDict
from Scientific.Geometry.VectorModule import *
from objects import zmatrix
from objects import vibfreq

# CML 1.01 Parser adapted to read molpro 2006.1 outputs into CCP1 GUI
# taken from web page
# http://cheminfo.informatics.indiana.edu/~rguha/code/python/cml101.py
# by Rajarshi Guha 
# <rajarshi@presidency.com> Oct, 2002

#
# IF THIS CODE SEGFAULTS ON PARSE CHECK STATUS OF libexpat.so
# there is a clash with vtk, you may need
# export LD_PRELOAD=/usr/lib/libexpat.so
# to ensure you have the correct version
# see e.g. http://mail.python.org/pipermail/python-bugs-list/2005-September/030488.html
# PS June 2007
#

class MolproXMLContentHandler(xml.sax.ContentHandler):
    """
    This class basically overrides the default ContentHandler class
    in the SAX parser returned by xml.sax.make_parser(). 

    It is designed to handle CML 1.01 (DTD found at http://www.xml-cml.org/)

    This class takes in an empty list, which it will fill up with instances
    of the Molecule class, for each <molecule></molecule> tag set it finds in
    the supplied CML file. This also allows you to parse multiple files
    (each containg any number of molecules) and they are all contained in
    the user supplied list.

    Currently it handles the <bond>, <bondArray>, <atom>, <atomArray>,
    <molecule>, <string>, <float> elements. An important element that needs
    attention is the <array> element. The CML 1.01 DTD mentions the <array> element,
    but the examples I got dont seem to have this element. However, some old
    CML files I have (which dont look like CML 1.01?) have a number of <array> tags.
    I need to be able to process them
    """
    def __init__(self, m):
        self.m = m
        
        self.currattr = None
        self.tmpstr = ''
        self.tmpmol = None
        self.tmpatom = None
        self.tmpbond = None
        
        self.inFloat = 0
        self.inString = 0
        self.inAtom = 0
        self.inBond = 0
        self.inAtomArray = 0
        self.inBondArray = 0
        self.inMolecule = 0
        self.inVib = 0 
        self.inNormCoord = 0 

    def startDocument(self):
        print 'Doc handling started'

    def endDocument(self):
        print 'Doc handling ended'

    def startElement(self, name, attrs):

        self.currattr = attrs

        #print 'start-element',name, attrs

        # MOLPRO 

        if name == 'cml:molecule':
            self.jobtitle=attrs['title'].encode('ascii')

        if name == 'cml:atomArray':
            self.inMolecule = 1
            self.tmpmol = zmatrix.Zmatrix()

        if name == 'cml:atom':
            self.inMolecule = 1
            atom = zmatrix.ZAtom()
            self.tmpmol.atom.append(atom)
            atom.coord=[float(attrs['x3']),float(attrs['y3']),float(attrs['z3'])]
            atom.symbol=attrs['elementType'].encode('ascii')
            atom.name=atom.symbol

        if name == 'molecule':
            self.inMolecule = 1
            self.tmpmol = Molecule(self.currattr)

        if name == 'vibrations':
            self.inVib = 1
            self.tmpVibFreqSet = vibfreq.VibFreqSet()
            self.tmpVibFreqSet.title  = 'Normal Modes for' + self.jobtitle
            
        if name == 'normalCoordinate':
            self.inNormCoord = 1
            self.tmpFreq =float(attrs['wavenumber'])
            self.tmpstr = ''

        if name == 'string':
            self.tmpstr = ''
            self.inString = 1

            if self.currattr['builtin'] == 'atomRef' and self.inBond:
                self.tmpbond['atomRef'] = []
            
        if name == 'float':
            self.tmpstr = ''
            self.inFloat = 1
            
        if name == 'atomArray':
            self.inAtomArray = 1
            self.tmpmol.atomlist = []

        if name == 'bondArray':
            self.inBondArray = 1
            self.tmpmol.bondlist = []

        if name == 'atom' and self.inAtomArray:
            self.tmpatom = Atom()
            self.inAtom = 1
            self.tmpatom['atomid'] = attrs['id']

        if name == 'bond' and self.inBondArray:
            self.tmpbond = Bond()
            self.inBond = 1
            self.tmpbond['bondid'] = attrs['id']

    def characters(self,ch):
        self.tmpstr += ch

    def endElement(self, name):

        #print 'end-element',name

        if name == 'cml:atomArray': 
            self.m.append( self.tmpmol )
            self.inMolecule = 0

        if name == 'molecule': 
            self.tmpmol.numatom = len(self.tmpmol.atomlist)
            self.tmpmol.numbond = len(self.tmpmol.bondlist)
            self.m.append( self.tmpmol )
            self.inMolecule = 0

        if name == 'normalCoordinate': 
            self.inNormCoord=0
            #print 'VIB:', self.tmpstr
            rr = self.tmpstr.encode('ascii').split()
            n = len(rr)/3
            disp = []
            count=0
            for i in range(0,n):
                vec = Vector([ float(rr[count+0]) , float(rr[count+1]), float(rr[count+2]) ])
                count = count + 3
                disp.append(vec)
            self.tmpVibFreqSet.add_vib(disp,self.tmpFreq)

        if name == 'vibrations':
            self.m.append( self.tmpVibFreqSet )

        # We have a Atom element data
        if name == 'string' and self.inAtom: 
            self.tmpatom[ self.currattr['builtin'] ] = self.tmpstr
            self.inString = 0
        if name == 'float' and self.inAtom:
            self.tmpatom[ self.currattr['builtin'] ] = float(self.tmpstr)
            self.inFloat = 0

        # We have a Bond element data   
        if name == 'string' and self.inBond:
            if self.currattr['builtin'] == 'atomRef':
                self.tmpbond['atomRef'].append( self.tmpstr )
            else:
                self.tmpbond[ self.currattr['builtin'] ] = self.tmpstr
            self.inString = 0
        if name == 'float' and self.inBond:
            self.tmpbond[ self.currattr['builtin'] ] = float(self.tmpstr)
            self.inFloat = 0

        # OK, we have all the data for this bond, append it to the molecule 
        # bond list
        if name == 'bond':
            self.tmpmol.bondlist.append(self.tmpbond)
            self.inBond = 0
            
        # OK, we have all the data for this atom, append it to the
        # molecule atom  list
        if name == 'atom':
            self.tmpmol.atomlist.append( self.tmpatom )
            self.inAtom = 0
            
        if name == 'bondArray':
            self.inBondArray = 0
        if name == 'atomArray':
            self.inAtomArray = 0

    def skippedEntity(self,name):
        pass

if __name__ == '__main__':

    if len(sys.argv) == 1:
        print """
        Usage: cml101.py CML_FILE ...

        Wil parse a list of CML files (which can containm one or more
        molecule definitions) and stores the information in a Molecule
        class. See the source to get more info about Molecule, Atom &
        Bond classes.

        No error handling yet, so you need to supply a well formed CML
        file.
        """
    m = []

    parser = xml.sax.make_parser()
    parser.setFeature( xml.sax.handler.feature_namespaces, 0 )

    ch = MolproXMLContentHandler(m)

    parser.setContentHandler(ch)
    for i in sys.argv[1:]:
        parser.parse(i)

    print  'Parsed %s objects' % ( len(m) )
    for i in m:
        i.list()
