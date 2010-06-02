#
# Base class to hold any methods used by all CCP1GUI Data objects
#
class CCP1GUI_Data:
    
    def __init__(self):
        pass

    def GetClass(self):
        """Return the last bit of the class decription as the objects class"""
        myclass = str(self.__class__).split('.')[-1]
        return myclass
