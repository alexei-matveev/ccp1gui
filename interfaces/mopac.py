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
import tkFileDialog
from   qm import *
from   filepunch import *
import os
import string
from viewer.paths import root_path
homolumoa = 0

class MopacCalc(QMCalc):
    '''Mopac specifics.'''

    def __init__(self,**kw):
        apply(QMCalc.__init__,(self,),kw)
        self.set_program('MOPAC')
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
        job_name = self.get_name()
        if sys.platform[:3] == 'win':
            self.infile='FOR005'
            self.outfile='FOR006'
        else:
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

    def makejob(self,writeinput=1,graph=None):
        """ build the mopac job"""
        self.GetModel()
        mol_obj  = self.get_input("mol_obj")
        job_name = self.get_name()

        if sys.platform[:3] == 'win':
            self.infile='FOR005'
            self.outfile='FOR006'
        else:
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

        hostname = self.get_parameter("hostname")
        username = self.get_parameter("username")

        if hostname == 'localhost':
            #job = jobmanager.BackgroundJob()
            # jmht Background job doesn't work currently so this is just a quick hack
            job = jobmanager.ForegroundJob()
        elif hostname == 'hpcx':
            job = jobmanager.RemoteForegroundJob('hpcx',username)
        elif hostname == 'tcsg7':
            job = jobmanager.RemoteForegroundJob('tcsg7',username)
        else:
            print 'unsupported host'
            return None

        job.name = job_name

        job.add_step(DELETE_FILE,'remove old output',remote_filename=self.outfile,kill_on_error=0)
        job.add_step(COPY_OUT_FILE,'transfer input',local_filename=self.infile,kill_on_error=0)

        # Local windows job, search for local executable
        if sys.platform[:3] == 'win' and hostname == 'localhost':
            # Name of executable, assume install of exe into exe subdirectory
            try:
                install_dir = os.environ['MOPAC_BIN']
                mopac_exe=install_dir+'\mopac.exe'
            except KeyError:
                mopac_exe=root_path+'/exe/mopac.exe'
            print 'Using MOPAC path ' + mopac_exe
            job.add_step(RUN_APP,'run mopac',local_command=mopac_exe)
        else:
            # See if we can work out the location of the sript
            mopac_exe = self.find_runmopac()
            if not mopac_exe:
                return
            mopac_cmd=mopac_exe+" "+job_name
            #mopac_exe="runmopac "+job_name
            #job.add_step(RUN_APP,'run mopac',local_command=mopac_exe,stdin_file=self.infile)
            job.add_step(RUN_APP,'run mopac',local_command=mopac_cmd,stdout_file=self.outfile)

        job.add_step(COPY_BACK_FILE,'recover log',remote_filename=self.outfile)
        job.add_step(PYTHON_CMD,'load results',proc=lambda s=self,g=graph: s.endjob(g))
        job.add_tidy(self.endjob2)
        return job

    def endjob(self,graph):
        """
        This is executed when the job completes successfully
        """
        # load contents of listing for viewing
        print 'endjob....'
        job_name = self.get_name()

        # load contents of listing for viewing
        file = open(self.outfile,'r')
        self.__ReadOutput(file)
        file.close()

        file = open(self.outfile,'r')
        # this just load into the browser
        self.ReadOutput(file)
        file.close()

        self.results = []
        # problem here as that as we are running in a slave thread
        # we cannot use Tk .. so this is silent
        if graph:
            graph.import_objects(self.results)

        txt = "Objects loaded from punchfile:"
        txt = txt  + "Structure update" + '\n'
        for r in self.results:
            txt = txt + r.title + '\n'
            
        return 0,txt

    def endjob2(self):
        '''
        This function is executed in the main thread if the job completes
        satisfactorily
        '''
        print 'endjob2'
        o = self.get_input("mol_obj")
        name = self.get_input("mol_name")
        o.list()
        calced = self.get_editor()
        if calced:
            if calced.update_func:
                calced.update_func(o)

    def old_endjob(self):
        """
        This is executed when the job completes successfully
        """

        #if self.__ReadPunch(job_name+'.pun') != 1:
        #    raise JobError, "No molecular structure in Punchfile - check output"

    def scan(self):
        '''Extract and Store results from a punchfile'''
        raise RuntimeError,"scan mopac not supported"
        #mol_name = self.get_input("mol_name")
        #mol_obj  = self.get_input("mol_obj")
        #job_name = self.get_name()
        file = tkFileDialog.askopenfilename(filetypes=[("Punch File","*.pun"),("All Files","*.*")])
        job_name = self.get_name()
        self.__RdMopacPunch(file)

    def get_theory(self):
        return self.get_parameter("theory")

    def check_direct(self):
        return 0

    def __Read(self,file):
        pass

    def __WriteInput(self,mol,file):
        if self.get_parameter("task") == "energy":
            txt = "1scf "
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
        file.write('This file was generate by the CCP1 PyMol GUI\n')
        file.write('\n')
        # we could write a zmatrix here
        #fac = 0.52917706
        fac = 1.0
        for a in mol.atom:
            file.write('%3d  %12.7f %d %12.7f %d %12.7f %d \n' % \
                       (a.get_number(), fac*a.coord[0],0,fac*a.coord[1],0,fac*a.coord[2],0))
        file.write('0  0 0   0 0   0 0\n')


    def __ReadOutput(self,file):
        '''Loading of results from Mopac output file
        - need to use a more sensible routing of results
        '''
        mol  = self.get_input("mol_obj")
        name  = self.get_input("mol_name")

        out = file.readlines()
        res = 0

        ed = self.get_editor()

        while len(out):
            a = out.pop(0)
            a = string.lstrip(a)
            a = string.rstrip(a)
            #print 'XX'+a+'XX'
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
            
    def find_runmopac(self):
        """
           Try to work out the location of the run_mopac script
        """
        # Get an editor for popping up error widgets
        ed = self.get_editor()
        
        # See if we can work out where the runmopac script lives
        from jobmanager import subprocess
        cmd="which run_mopac"
        p = subprocess.ForegroundPipe(cmd)
        code = p.run()
        script = None
        if p.error:
            print 'Error trying to locate run_mopac script '+str(p.error)
        else:
            if ( len( p.output ) > 0 ):
                # Output is a list containing a string with an endline char
                output = p.output[0]
                script = output[:-1]
                
        if not script:
            ed.Error("A script called \"run_mopac\" could not be found.\n" +
                      "Please ensure that a script called \"run_mopac\" is\n" +
                     "in your path before starting the GUI.")
            
        return script
        
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

        self.task_tool = SelectOptionTool(self,"task","Task",self.tasks,command=self.__taskupdate)

        #Used to specify task
        self.tasktoolvalue = self.task_tool.widget.getvalue() 
        self.theory_tool = SelectOptionTool(self,"theory","Hamiltonian",self.theories[self.tasktoolvalue],command=self.__theoryupdate)
        self.keywords_tool = TextTool(self,"keywords","Keywords")

        self.checkspin_widget = Tkinter.Button(self.interior(),
                                             text = 'Check Spin',
                                             command = self.calc.CheckSpin)

        #Create the tools used for the Job tab
        self.hostname_tool = SelectOptionTool(self,'hostname','Host name',self.hostnames,command=self.__sethost)
        self.hostname = self.hostname_tool.widget.getvalue()# line to get the hostname for the below tool      
        self.submission_tool = SelectOptionTool(self,'submission','Job Submission',
                                                      self.submissionpolicies[self.hostname])

        self.username_tool = TextFieldTool(self,'username','User Name')
        self.workingdirectory_tool = TextFieldTool(self,'directory','Working Directory')

        self.LayoutToolsTk()

    def __taskupdate(self,task):
        """ Update the choice of theories
        """
        self.theory_tool.SetItems(self.theories[task])

    def __theoryupdate(self,task):
        pass


    def __sethost(self,host):
        """Update the submission types for the particular host.
        """
        self.submission_tool.SetItems(self.submissionpolicies[host])

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

        self.hostname_tool.widget.pack(in_=page.jobgroup.interior())
        self.submission_tool.widget.pack(in_=page.jobgroup.interior())
        self.username_tool.widget.pack(in_=page.jobgroup.interior())
        self.workingdirectory_tool.widget.pack(in_=page.jobgroup.interior())

    def LaunchCalcEd(self,calc):
        '''Create a new calculation editor.'''
        a = MopacCalcEd(calc)
        a.Show()


    def TaskPage(self,page,action):
        QMCalcEd.TaskPage(self,page,action)
        # Create a group for the checkboxes
        if action == Create:
            page.group = Pmw.Group(page,tag_text="Analysis options")
            page.group.pack(expand='yes',fill='x')

    def SCFPage(self,page,action):
        '''Maintain the SCF page.'''
        labels = []

    def KeywordsPage(self,page,action):
        '''Entry for various directives not covered by GUI yet:
            In this case just offers additional keywords '''

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
