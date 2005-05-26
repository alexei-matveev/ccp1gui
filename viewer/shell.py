import os
import sys
real_stdout = sys.stdout 
real_stderr = sys.stderr 

class ShellEnv:
    """A containter class to hold information that might be needed
    in sub-shells such as the interactive python shell"""
    def __init__(self):
        self.var = 1
        self.tkmol = None

env = ShellEnv()

#http://mail.python.org/pipermail/python-bugs-list/2000-April/000714.html
######IdleConf.load(os.path.join(os.path.dirname(__file__), 'idle8'))

from idle import IdleConf
idle_dir = os.path.dirname(IdleConf.__file__)
IdleConf.load(idle_dir)

# defer importing Pyshell until IdleConf is loaded
from idle import PyShell

class MyPyShell(PyShell.PyShell):
    """A version of PyShell that doesnt set Tkinter._default_root to None
    """
    def begin(self):
        self.resetoutput()
        self.write("Python %s on %s\n%s\nIDLE %s -- press F1 for help\n" %
                   (sys.version, sys.platform, self.COPYRIGHT,
                    PyShell.idlever.IDLE_VERSION))

        self.interp.runsource('global env')
        self.write('global env\n')
        self.interp.runsource('gui = env.tkmol')
        self.write('gui = env.tkmol\n')
        self.interp.runsource('print "gui.data_list comprises",len(gui.data_list),"objects"')
        self.interp.runsource('print "gui.vis_list comprises",len(gui.vis_list),"objects"')	    
        try:
            sys.ps1
        except AttributeError:
            sys.ps1 = ">>> "
        self.showprompt()

    def close(self, *args, **kw):
        ret = apply(PyShell.PyShell.close, (self,) + args, kw)
        sys.stdout = real_stdout
        sys.stderr = real_stderr
        return ret

def mypyshell(root):
    """Create the IDLE Python shell window
    """
    idle_dir = os.path.dirname(IdleConf.__file__)
    IdleConf.load(idle_dir)
    flist = PyShell.PyShellFileList(root)
    shell = MyPyShell(flist)
    interp = shell.interp
    flist.pyshell = shell
    shell.begin()

if __name__ == "__main__":
    import Tkinter
    root=Tkinter.Tk()
    mypyshell(root)
    root.mainloop()


