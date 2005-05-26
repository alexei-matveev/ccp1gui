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
#!/usr/bin/env python

import sys
from xml.dom.minidom import parse
from xml.xpath import Evaluate

def atomInfo(xmlFile):
    
    #get DOM object
    xmldoc=open(xmlFile)
    doc=parse(xmldoc)

    #get the namespaces used in the xml document
    nsMap = {}
    ns_nodes = Evaluate('namespace::node()',doc.documentElement)
    for ns in ns_nodes:
        nsMap[ns.value]=ns.localName

    #initialise objects
    idlist=[]
    attribDict={}
    atomDict={}
    
    #get atomArray nodes
    #remember to check through all the namespaces
    atomArrayNodes=doc.getElementsByTagName("atomArray")
    for ns in nsMap.keys():
        atomArrayNodes+=doc.getElementsByTagNameNS(ns,"atomArray")

    #get the atom nodes for each atomArray node
    #remember to check through all the namespaces
    for atomArrayNode in atomArrayNodes:
        atomNodes=atomArrayNode.getElementsByTagName("atom")
        for ns in nsMap.keys():
            atomNodes+=atomArrayNode.getElementsByTagNameNS(ns,"atom")

        #check for the use of arrays (no 'atom' nodes)
        atomArrayInfo={}
        if atomNodes==[]:
            
            atomArrayChildNodes=atomArrayNode.childNodes
            for atomArrayChildNode in atomArrayChildNodes:
                if atomArrayChildNode.nodeType==atomArrayChildNode.ELEMENT_NODE:
                    dataName=atomArrayChildNode.getAttribute('builtin')
                    subChildNodes=atomArrayChildNode.childNodes
                    for subChildNode in subChildNodes:
                        data=subChildNode.data.encode("ascii").split()
                        atomArrayInfo.update({dataName:data})
            for i in range(0,len(atomArrayInfo['atomId'])):
                for key in atomArrayInfo.keys():
                    #if key!='atomId':
                    attribDict.update({key:atomArrayInfo[key][i]})
                    #atomDict.update({atomArrayInfo['atomId'][i]:attribDict})
                    atomDict.update({i:attribDict})
                attribDict={}

        #get the attribute nodes for each atom node
        i=0
        for atomNode in atomNodes:
            attrib=atomNode.attributes
            for attribNode in attrib.values():
                #if attribNode.name=="id":
                #    id=attribNode.value
                #    idlist.append(id)
                #else:
                attribDict.update({attribNode.name:attribNode.value.encode("ascii")})

            #The following obtains data from CML-1 markup

            #get the child nodes of each atom node
            atomChildNodes=atomNode.childNodes
           
            #get the data name of each child node
            for atomChildNode in atomChildNodes:
                if atomChildNode.nodeType==atomChildNode.ELEMENT_NODE:
                    dataName=atomChildNode.getAttribute("builtin")

                    #get the data value from the text node of each child element node
                    subAtomChildNodes=atomChildNode.childNodes
                    for subAtomChildNode in subAtomChildNodes:
                        if subAtomChildNode.nodeType==subAtomChildNode.TEXT_NODE:
                            dataValue=subAtomChildNode.data.encode("ascii")
                            attribDict.update({dataName:dataValue})
            
            #atomDict.update({id:attribDict})
            atomDict.update({i:attribDict})
            attribDict={}
            i=i+1
            
    return atomDict
