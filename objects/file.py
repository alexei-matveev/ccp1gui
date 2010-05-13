""" A wrapper for a file so it can be passed around 
"""
import objects.object

GAMESSUK_INPUT = 1
GAMESSUK_OUTPUT = 2
GAMESSUK_PUNCH = 3

MOLPRO_INPUT = 11
MOLPRO_OUTPUT = 12
MOLPRO_XML = 13

MOLDEN_WFN = 21

class File(objects.object.CCP1GUI_Data):

    def __init__(self,filename,type=None):
        self.filename = filename
        self.type = type
        self.title = "File:"+self.filename
        self.name = "File:"+self.filename

    def get_name(self):
        return self.title

    def __str__(self):
        return "File object + " + self.filename

    def MoldenReadable(self):
        if self.type == GAMESSUK_OUTPUT:
            return 1
        if self.type == MOLDEN_WFN:
            return 1

    def ASCII(self):
        return 1


    
