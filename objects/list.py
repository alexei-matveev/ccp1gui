import objects.object

class List(objects.object.CCP1GUI_Data):

    def __init__(self,type):
        self.type = type
        self.title = "List of " + type
        self.data = []

    def get_name(self):
        return self.title

    def __str__(self):
        return "List object + " + str(self.data)

    
