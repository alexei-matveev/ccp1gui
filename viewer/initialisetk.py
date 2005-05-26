"""Set up defaults for the Tk Widgets

For testing purposes, all widgets should call initialiseTk
"""
def initialiseTk(root):
    pad = ' '
    # Initialise platform-specific options
    import sys
    if sys.platform == 'mac':
        initialiseTk_mac(root)
    elif sys.platform == 'win32':
        initialiseTk_win32(root)
    else:
        initialiseTk_unix(root)

def initialiseTk_colors_common(root):
    root.option_add('*Listbox*background', 'white')
    root.option_add('*Listbox*Font', 'Courier 8')
    root.option_add('*Text.background', 'white')
    #root.option_add('*background', 'grey')
    #root.option_add('*foreground', 'black')
    #root.option_add('*EntryField.Entry.background', 'white')
    #root.option_add('*Entry.background', 'white')      
    #root.option_add('*MessageBar.Entry.background', 'gray85')
    #root.option_add('*Listbox*selectBackground', 'dark slate blue')
    #root.option_add('*Listbox*selectForeground', 'white')
    pass

def initialiseTk_win32(root):
    initialiseTk_colors_common(root)
    #root.option_add('*Font', 'Verdana 9 bold')
    #root.option_add('*Menu*Font', 'Verdana 9')
    #root.option_add('*Button*Font', 'Verdana 9')
    #root.option_add('*Menubutton*Font', 'Verdana 9')
    #root.option_add('*Listbox*Font', 'Courier 8')
    #root.option_add('*Entry.font', 'courier 8')
    #root.option_add('*Label.font', 'courier 8 bold')

def initialiseTk_mac(root):
    initialiseTk_colors_common(root)

def initialiseTk_unix(root):
    initialiseTk_colors_common(root)
    #root.option_add('*Entry.font', 'courier 10')      
    #root.option_add('*Label.font', 'courier 10 bold')      
    #root.option_add('*Listbox*font', 'courier 10')
