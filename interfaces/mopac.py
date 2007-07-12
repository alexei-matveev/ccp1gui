#
#    This file is part of the CCP1 Graphical User Interface (ccp1gui)
# 
#   (C) 2002-2007 CCLRC Daresbury Laboratory
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
import tkFileDialog
from   qm import *
from   filepunch import *
import os
import string
from viewer.paths import root_path,find_exe
homolumoa = 0

class MopacCalc(QMCalc):
    """Mopac specifics"""

    def __init__(self,**kw):
        apply(QMCalc.__init__,(self,),kw)

        #self.debug=1
        self.set_program('MOPAC')
        self.set_parameter('job_name','untitled')
        self.set_parameter("task","energy")
        self.set_parameter("theory","AM1")
        self.set_parameter("basis","STO")
        self.set_parameter("maxcyc","200")
        self.set_parameter("restart","0")
        self.set_parameter("scf_maxcyc","100")
        self.set_parameter("accuracy","medium")
        self.set_parameter("keywords","")
        self.set_output("ana_frequencies",0)

    def get_editor_class(self):
        return MopacCalcEd

    def WriteInput(self):
        """Write the MOPAC input file"""
        self.GetModel()
        mol_name = self.get_input("mol_name")
        mol_obj  = self.get_input("mol_obj")
        job_name = self.get_parameter('job_name')
        self.infile=job_name+'.dat'
        self.outfile=job_name+'.out'

        directory = self.get_parameter("directory")
       
        file = open(self.infile,'w')
        self.__WriteInput(mol_obj,file)
        file.close()

        # load contents of input for viewing
        file = open(self.infile,'r')
        input = file.readlines()
        self.set_input("input_file",input)
        file.close()
        return self.infile

    def makejob(self,writeinput=1,graph=None):
        """ build the mopac job"""

        #Get an editor instance to pop up tk-error widgets
        ed = self.get_editor()

        self.GetModel()
        mol_obj = self.get_input("mol_obj")
        job_name = self.get_parameter('job_name')
        self.infile=job_name+'.dat'
        self.outfile=job_name+'.out'

        if writeinput:
            # maybe this should be moved elsewhere
            file = open(self.infile,'w')
            self.__WriteInput(mol_obj,file)
            file.close()

            # load contents of input for viewing
            file = open(self.infile,'r')
            input = file.readlines()
            self.set_input("input_file",input)
            file.close()
        else:
            input = self.get_input("input_file")
            file = open(self.infile,'w')
            for a in input:
                file.write(a)
            file.close()


        job = self.get_job()
        if not job:
            job = self.create_job()

        job.name = job_name

        job.add_step(DELETE_FILE,'remove old output',remote_filename=self.outfile,kill_on_error=0)
        job.add_step(COPY_OUT_FILE,'transfer input',local_filename=self.infile,kill_on_error=0)

        mopac_exe = self.get_executable(job=job)
        if not mopac_exe:
            ed.Error('Cannot find a mopac executable!')
            return None

        # Clear out steps in case we are reusing the job
        job.clear_steps()
        
        job.add_step(RUN_APP,
                     'run mopac',
                     local_command=mopac_exe,
                     local_command_args=[job_name])
        job.add_step(COPY_BACK_FILE,'recover log',remote_filename=self.outfile)
        job.add_tidy(self.endjob)
        return job

    def endjob(self,job_status_code):
        """
        Load results from MOPAC run
        
        This function is executed in the main thread when 
        the job completes.

        """

        if self.debug:
            print 'endjob'

        # this just load into the output viewer widget
        file = open(self.outfile,'r')
        self.ReadOutput(file)
        file.close()
        
        # Code is 1 on job failure
        if job_status_code == 1:
            print "skipping rest of mopac endjob as job failed 1"
            return

        # extract the structure (updates molecule)
        mol = self.get_input("mol_obj")
        self.results = [ self.ReadMopacOutput(self.outfile,mol) ]
        self.store_results_to_gui()

    def ReadMopacOutput(self,file,oldmol):
        """Loading of results from Mopac output file

        This approach is a bit heavy handed as we only
        load a molecule, but it we use the same machinery
        as the other codes so it can be extended in future

        """
        fp = open(file,'r')
        mol = copy.deepcopy(oldmol)
        out = fp.readlines()
        res = 0
        while len(out):
            a = out.pop(0)
            a = string.lstrip(a)
            a = string.rstrip(a)
            if a[0:10] == 'FINAL HEAT':
                res = 1
            if res and a == 'CARTESIAN COORDINATES':
                for i in range(3):
                    out.pop(0)
                fac = 1.0
                for i in range(len(mol.atom)):
                    rec= string.split(out.pop(0))
                    print rec
                    mol.atom[i].coord[0] = fac*float(rec[2])
                    mol.atom[i].coord[1] = fac*float(rec[3])
                    mol.atom[i].coord[2] = fac*float(rec[4])
                break
        fp.close()
        return mol

    def get_theory(self):
        return self.get_parameter("theory")

    def check_direct(self):
        return 0

    def __Read(self,file):
        pass

    def __WriteInput(self,mol,file):
        task = self.get_parameter("task")
        if task == "energy":
            txt = "1scf "
        elif task == "optimise":
            txt = "bfgs"
        else:
            txt = ""

        txt2 = self.get_parameter("theory")
        if txt2[0:2] == 'U ':
            txt2 = txt2[2:]
            txt3 = "uhf "
        else:
            txt3 = ""

        if self.get_parameter("spin") == 1:
            txt4 = " "
        elif self.get_parameter("spin") == 2:
            txt4 = "doublet "
        elif self.get_parameter("spin") == 3:
            txt4 = "triple "
        elif self.get_parameter("spin") == 4:
            txt4 = "quartet "
        elif self.get_parameter("spin") == 5:
            txt4 = "quintet "
        else:
            self.error('cannot run with mult = ' + str(self.get_parameter("spin")))

        file.write('xyz ' + txt + ' charge=' +str(self.get_parameter("charge")) + ' ' + 
                   txt2 + txt3 + txt4 + self.get_parameter("keywords") + '\n')
        file.write('This file was generate by CCP1GUI\n')
        file.write('\n')
        # we could write a zmatrix here
        #fac = 0.52917706
        fac = 1.0

        # Need to set the flag on all coordinates we want to optimise
        if task == "optimise":
            oflag = 1
        else:
            oflag = 0
            
        for a in mol.atom:
            file.write('%3d  %12.7f %d %12.7f %d %12.7f %d \n' % \
                       (a.get_number(), fac*a.coord[0],oflag,fac*a.coord[1],oflag,fac*a.coord[2],oflag))
        file.write('0  0 0   0 0   0 0\n')

    def get_executable(self,job=None):
        """Try to work out the location of the executable"""

        mopac_exe = None
        # First see if the user has set an executable path for the job
        # (also covers a value stored in the defaults)
        if job:
            mopac_exe = job.get_parameter("executable")
            if mopac_exe:
                if self.debug:
                    print "Using mopac_exe from job: %s" % mopac_exe
            else:
                mopac_exe = None
                
        if not mopac_exe:
            if sys.platform[:3] == 'win':
                # Name of executable, assume MOPAC 2007 standard Install
                try:
                    install_dir = os.environ['MOPAC_BIN']
                    mopac_exe=install_dir+'\mopac.exe'
                except KeyError:
                    mopac_exe="C:\Program Files\MOPAC\MOPAC2007.exe"
            else:
                # Unix case - check default path and gui directories
                for path in ['/opt/mopac/mopac','/opt/mopac/MOPAC2007.out']:
                    if  os.access( path, os.X_OK):
                        mopac_exe = path
                if not mopac_exe:
                    mopac_exe = find_exe('mopac')
                    
                if self.debug: print "Using mopac_exe from path: %s" % mopac_exe

        if self.debug:
            print "Using mopac_exe: %s" % mopac_exe
        return mopac_exe
        
    def get_editor_class(self):
        return MopacCalcEd

class MopacCalcEd(QMCalcEd):

    def __init__(self,root,calc,graph,**kw):

        apply(QMCalcEd.__init__, (self,root,calc,graph), kw)

#      self.tasks = ["energy", 
#                    "optimise internal coord.", 
#                    "optimise cartesian coord."]

        self.tasks = ["energy", 
                      "optimise" ]

        self.theories["energy"] = [
             "MNDO", "MINDO/3", "AM1", "PM3", "U MNDO", "U MINDO/3", "U AM1", "U PM3" ]

        self.theories["optimise"] = self.theories["energy"]
        self.basissets = ["STO"]
        self.submission_policies = [ LOCALHOST ]

        self.task_tool = SelectOptionTool(self,"task","Task",self.tasks,command=self.__taskupdate)

        #Used to specify task
        self.tasktoolvalue = self.task_tool.widget.getvalue() 
        self.theory_tool = SelectOptionTool(self,"theory","Hamiltonian",self.theories[self.tasktoolvalue],command=self.__theoryupdate)
        self.keywords_tool = TextTool(self,"keywords","Keywords")

        self.checkspin_widget = Tkinter.Button(self.interior(),
                                             text = 'Check Spin',
                                             command = self.calc.CheckSpin)

        #Create the tools used for the Job tab
#        self.hostname_tool = SelectOptionTool(self,'hostname','Host name',self.hostnames,command=self.__sethost)
#        self.hostname = self.hostname_tool.widget.getvalue()# line to get the hostname for the below tool      
#        self.submission_tool = SelectOptionTool(self,'submission','Job Submission',
#                                                      self.submissionpolicies['localhost'])

        #self.username_tool = TextFieldTool(self,'username','User Name')
        #self.workingdirectory_tool = TextFieldTool(self,'directory','Working Directory')
        self.jobname_tool = TextFieldTool(self,'job_name','Job Name')
        self.balloon.bind(self.jobname_tool.widget, 'Specify the prefix for all output files')
        self.submission_tool = SelectOptionTool(self,'submission','Job Submission',
                                                self.submission_policies)

        self.LayoutToolsTk()

    def __taskupdate(self,task):
        """ Update the choice of theories
        """
        self.theory_tool.SetItems(self.theories[task])

    def __theoryupdate(self,task):
        pass


#    def __sethost(self,host):
#        """Update the submission types for the particular host.
#        """
#        self.submission_tool.SetItems(self.submissionpolicies[host])

    def LayoutToolsTk(self):

        #Add Molecule tab
        page = self.notebook.add('Molecule',tab_text='Molecule')
        page.optgroup = Pmw.Group(page,tag_text="Options")
        page.optgroup.pack(expand='yes',fill='both')

        page.keygroup = Pmw.Group(page,tag_text="Options")
        page.keygroup.pack(expand='yes',fill='both')
        
        self.title_tool.widget.pack(in_=page.optgroup.interior())
        self.task_tool.widget.pack(in_=page.optgroup.interior())
        self.theory_tool.widget.pack(in_=page.optgroup.interior())
        self.charge_tool.widget.pack(in_=page.optgroup.interior())
        self.spin_tool.widget.pack(in_=page.optgroup.interior())
        self.checkspin_widget.pack(in_=page.optgroup.interior())

        self.keywords_tool.widget.pack(in_=page.keygroup.interior())

        Pmw.alignlabels([self.charge_tool.widget, self.spin_tool.widget])


        #Add Job tab
        page = self.notebook.add('Job',tab_text='Job')
        page.jobgroup = Pmw.Group(page,tag_text="Job Group")
        page.jobgroup.pack(side='top',expand='yes',fill='both')

#        self.hostname_tool.widget.pack(in_=page.jobgroup.interior())
#        self.submission_tool.widget.pack(in_=page.jobgroup.interior())
#        self.username_tool.widget.pack(in_=page.jobgroup.interior())
#        self.workingdirectory_tool.widget.pack(in_=page.jobgroup.interior())

        # Job submission
        self.submission_frame = Tkinter.Frame(page.jobgroup.interior())
        self.submission_frame.pack()
        self.submission_config_button = Tkinter.Button(self.submission_frame,
                                                       text='Configure...',
                                                       command=self.open_jobsub_editor)
        self.submission_tool.widget.pack(in_=self.submission_frame,side='left')
        self.submission_config_button.pack(side='left')#
        

    def LaunchCalcEd(self,calc):
        """Create a new calculation editor."""
        a = MopacCalcEd(calc)
        a.Show()


    def TaskPage(self,page,action):
        QMCalcEd.TaskPage(self,page,action)
        # Create a group for the checkboxes
        if action == Create:
            page.group = Pmw.Group(page,tag_text="Analysis options")
            page.group.pack(expand='yes',fill='x')

    def SCFPage(self,page,action):
        """Maintain the SCF page."""
        labels = []

    def KeywordsPage(self,page,action):
        """Entry for various directives not covered by GUI yet:
        In this case just offers additional keywords """

        if action == Create:
            page.panes = Pmw.PanedWidget(page)
            page.panes.add('keywords',size=100,min=50)
            page.panes.pack(expand=1,fill='both')

        # Sort out keywords
        if action == Create:
            page.keywords = Pmw.ScrolledText(page.panes.pane('keywords'),
                         labelpos = 'nw', label_text = 'Additional Keywords',
                         borderframe = 1)
            page.keywords.settext(self.calc.get_parameter("keywords"))
            page.keywords.pack(expand=1,fill='x')
        elif action == Lower:
            keywords = page.keywords.get()
            length = len(keywords)
            if length == 1:
                keywords = ""
            elif keywords[length-2] == '\n':
                keywords = keywords[:length-1]
            self.calc.set_parameter("keywords",keywords)
        else: 
            page.keywords.settext(self.calc.get_parameter("keywords"))

if __name__ == "__main__":

    from mopac import *
    from objects.zmatrix import *
    from jobmanager import *
    model = Zmatrix()
    atom = ZAtom()
    atom.symbol = 'C'
    atom.name = 'C0'
    model.insert_atom(0,atom)
    atom = ZAtom()
    atom.symbol = 'P'
    atom.name = 'P'
    atom.coord = [ 1.,0.,0. ]
    model.insert_atom(1,atom)

    root=Tk()
    calc = MopacCalc()
    calc.set_input('mol_obj',model)
    jm = JobManager()
    je = JobEditor(root,jm)
    vt = MopacCalcEd(root,calc,None,job_editor=je)
    root.mainloop()
