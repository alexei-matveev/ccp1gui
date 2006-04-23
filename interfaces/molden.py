""" Interface code for MOLDEN

assumes a somewhat doctored version of MOLDEN

"""

from objects.field import *
from jobmanager import *

class MoldenDriver:

    def __init__(self, wavefunctionfile):
        """ Initialise buy specifying the file (Molden or GAMESS-UK
        that molden will use to get the wavefunction) """
        self.wfn = wavefunctionfile

    def ComputePlot(self,planespec,npts=21,edge=None,mo=None):
        """driver for Molden calculations
        """
        # create molden directive file
        fp = open("molden.dat","w")
        title="CCP1GUI MOLDEN Calculation"
        if mo:
            title = title + " MO " + str(mo)
        else:
            title = title + " density"
        
        fp.write(title + '\n')
        
        if len(planespec) == 3:
            fp.write("PLANE="+str(planespec) + " space" )
        if edge:
            fp.write(" EDGE="+str(edge))
        if mo:
            fp.write(" PSI="+str(mo))
        fp.write(" NPTSX="+str(npts)+" NPTSY="+str(npts)+" NPTSZ="+str(npts))
        fp.write("\n")
                 
        fp.write("FILE="+self.wfn+" WRBAS")

        fp.close()

        # execute MOLDEN

        #import os
        #os.system("/home/psh/molden4.4_hvd/molden.nox molden.dat")

        # Windows/Cygwin
        job = jobmanager.BackgroundJob()
        job.debug = 1
        job.add_step(DELETE_FILE,'remove 3dgridfile',remote_filename='3dgridfile',kill_on_error=0)        
        molden_exe = "C:/molden4.4_hvd/molden.exe"
        job.add_step(RUN_APP,'run molden',local_command=molden_exe + " molden.dat")
        job.run()

        # Load resultant field into a grid
        self.field = Field(nd=3)
        self.field.read_molden('3dgridfile')


if __name__ == "__main__":
    t=MoldenDriver("c:\molden4.4_hvd\ex1\cyclopropaan.out")
    t.ComputePlot((1,2,3))
    

