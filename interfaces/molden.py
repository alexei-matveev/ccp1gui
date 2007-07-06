""" Interface code for MOLDEN

assumes a somewhat doctored version of MOLDEN

"""

from objects.field import *
from jobmanager import *
from viewer.defaults import defaults
from viewer.paths import find_exe
import sys, os

class MoldenDriver:

    def __init__(self, wavefunctionfile):
        """ Initialise buy specifying the file (Molden or GAMESS-UK
        that molden will use to get the wavefunction) """
        self.wfn = wavefunctionfile
        if not os.access(wavefunctionfile,os.R_OK):
            raise Exception, 'MoldenDriver: wfn file '+wavefunctionfile+' is not readable'

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
                 
        fp.write("FILE="+self.wfn+" WRBAS\n")

        fp.close()

        if sys.platform[:3] == 'win':
            # Convert the file
            if os.access('omolden.dat', os.R_OK):
                os.unlink('omolden.dat')
            os.rename('molden.dat','omolden.dat')
            t = open('molden.dat',"wb")
            o = open('omolden.dat',"rb")
            while 1:
                data = o.read(4096)
                if data == "":
                    break
                newdata = re.sub("\r\n","\n",data)
                t.write(newdata)
            t.close()
            o.close()
            if os.access('omolden.dat', os.R_OK):
                os.unlink('omolden.dat')

        # execute MOLDEN
        molden_exe = self.get_executable()
        if not molden_exe:
            raise CalcError,"Cannot find a molden_executable to run!"

        if sys.platform[:3] == 'win':
            # Windows/Cygwin
            job = jobmanager.LocalJob()
        else:
            job = jobmanager.LocalJob()
            
        #job.debug = 1
        job.add_step(DELETE_FILE,'remove 3dgridfile',remote_filename='3dgridfile',kill_on_error=0)        
        job.add_step(RUN_APP,
                     'run molden',
                     local_command=molden_exe,
                     local_command_args=['molden.dat']
                     )
        #job.debug=1
        job.run()

        if not os.access('3dgridfile', os.R_OK):
            print 'Problem reading molden field - You need an adapted molden for use with CCP1GUI'
            print 'See www.cse.scitech.ac.uk/ccg/software/ccp1gui/molden.shtml'
            raise Exception,'Problem reading molden field - You need an adapted molden for use with CCP1GUI'

        # Load resultant field into a grid
        self.field = Field(nd=3)
        self.field.read_molden('3dgridfile')

    def get_executable(self):
        """Find an executable to run"""
        global defaults,find_exe

        molden_exe = defaults.get_value('molden_exe')
        if not molden_exe:
            if sys.platform[:3] == 'win':
                molden_exe = find_exe( 'molden.exe')
            else:
                molden_exe = find_exe('molden')

        print "using molden_exe: %s" %molden_exe
        return molden_exe

if __name__ == "__main__":
    #t=MoldenDriver("c:\molden4.4_hvd\ex1\cyclopropaan.out")
    t=MoldenDriver("/home/psh/molden4.4_hvd/ex1/cyclopropaan.out")
    t.ComputePlot((1,2,3))
    

