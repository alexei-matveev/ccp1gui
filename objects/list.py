class List:

    def __init__(self,type):
        self.type = type
        self.title = "List of " + type
        self.data = []
    def get_name(self):
        return self.title

    def __str__(self):
        return "List object + " + self.data

    
