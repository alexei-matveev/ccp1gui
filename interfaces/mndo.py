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
import os
import string

import tkFileDialog

from qm import *
from filepunch import *
from objects.periodic import z_to_el

homolumoa = 0

MENU_ENER  = "Energy"
MENU_GRAD  = "Gradient"
MENU_OPT   = "Geometry Optimisation"

class MNDOCalc(QMCalc):
    """MNDO specific calculation class"""

    def __init__(self,**kw):
        apply(QMCalc.__init__,(self,),kw)
        self.set_parameter("task",MENU_ENER)
        self.set_parameter("theory","AM1")
        self.set_parameter("symmetry",1)
        self.set_parameter("scf_method","rhf")
        self.set_parameter("hamiltonian","am1")
        self.set_parameter("basis","STO")
        self.set_parameter("scf_maxcyc","200")
        self.set_parameter("restart","0")
        self.set_parameter("accuracy","medium")
        self.set_output("ana_frequencies",0)
        self.set_parameter('job_name','unnamed')
        # need to replace with MNDO's accuracy parameter
        self.set_parameter("scf_threshold",6)

        # this stuff almost certainly shouldnt be here
        # but it enables WriteInput to run
        directory = self.get_parameter("directory")
        job_name = self.get_parameter("job_name")
        self.infile = directory+os.sep+job_name+'.in'
        self.outfile = directory+os.sep+job_name+'.out'

    def get_editor_class(self):
        return MNDOCalcEd

    def WriteInput(self):

        mol_name = self.get_input("mol_name")
        mol_obj  = self.get_input("mol_obj")
        job_name = self.get_parameter("job_name")
        directory = self.get_parameter("directory")

        filename = self.infile
        writeinput_err = self.__WriteInput(mol_obj,filename)
        if writeinput_err:
            return

        # load contents of input for viewing
        file = open(self.infile,"r")
        input = file.readlines()
        self.set_input("input_file",input)
        file.close()


    def __WriteInput(self,mol,filename):
        """MNDO input writer, based on parts of the ChemShell function written by
        the group of Walter Thiel
        """

        file = open(filename,'w') 

        task = self.get_parameter("task")
        scf_method = self.get_parameter("scf_method")

        link_atom_indices=[]
        link_atom_option=None

        # Set to 1 when old vectors are available on fort.11
        self.chk = 0

        # SCF type / multiplicity
        # scftype   mult   imult  iuhf
        #-------------------------------
        # rhf       1      undef  undef
        # rhf       N      N      -1
        # rohf      1      1      -1
        # rohf      N      N      -1
        # uhf       1      1       1
        # uhf       N      N       1

        scftype = self.get_parameter("scf_method")
        mult = self.get_parameter("spin")

        if scftype == "rhf":
            if mult == 1:
                imult=None
                iuhf=None
            else:
                imult=mult
                iuhf=-1
        elif scftype == "rohf":
            if mult == 1:
                imult=1
                iuhf=-1
            else:
                imult=mult
                iuhf=-1
        elif scftype == "uhf":
            if mult == 1:
                imult=1
                iuhf=1
            else:
                imult=mult
                iuhf=1

        #  mndo string settings based on the keyword setting
        charge = self.get_parameter("charge")
        if charge != 0:
            khargestr = "kharge"+str(charge)
        else:
            khargestr = ""

        hamiltonian = self.get_parameter("hamiltonian")

        # hamiltonian (iop=)
        ham_to_iop = { 
            "mndo/d"  : -10,
            "pm3"     : -7,
            "am1"     : -2,
            "mndo"    :  0,
            "mindo/3" :  1,
            "cndo/2"  :  2,
            "om1"     : -5,
            "om2"     : -6 }

        iop = None
        if iop == None:
            try:
                iopstr = "iop="+str(ham_to_iop[hamiltonian])
            except KeyError:
                print 'unrecognised hamiltonian'
                return None
        else:
            iopstr="iop="+str(iop)

        if imult == None:
            imultstr=""
        else:
            imultstr="imult="+str(imult)

        if iuhf == None:
            iuhfstr=""
        else:
            iuhfstr="iuhf="+str(iuhf)

        nprint = None
        if nprint == None:
            nprintstr=""
        else:
            nprintstr="nprint="+str(nprint)

        iscf = None
        if iscf == None:
            iscfstr=""
        else:
            iscfstr="iscf="+str(iscf)

        idiis = None
        if idiis == None:
            idiisstr=""
        else:
            idiisstr="idiis="+str(idiis)

        ipsana = None
        if ipsana == None:
            ipsanastr =""
        else:
            ipsanastr ="ipsana="+str(ipsana)

        mprint = None
        if mprint == None:
            mprintstr =""
        else:
            mprintstr ="mprint="+str(mprint)

        nstart = None
        if nstart == None:
            nstartstr =""
        else:
            nstartstr ="nstart="+str(nstart)

        # Build up the input lines for the mndo input file

        optstr1 = khargestr + " " + iopstr + " " + idiisstr + " " + ipsanastr + " " + \
                  nstartstr + " " + imultstr + " " + iuhfstr
        optstr2 = nprintstr + " " + mprintstr + " " + iscfstr 
        optstr3="igeom=1 iform=1 nsav15=4 ipubo=1"

        if self.chk:
            trialstr="ktrial=11"
        else:
            trialstr=""

        if task == MENU_ENER:
            optstr3 = optstr3 + " jop=-1"
            enerflag = 1
            gradflag = 0
        elif task == MENU_GRAD:
            optstr3 = optstr3 + " jop=-2"
            enerflag = 1
            gradflag = 1
        elif task == MENU_OPT:
            optstr3 = optstr3 + " jop=0"
            enerflag = 1
            gradflag = 1
        #
        #  ================= Generate MNDO97 input file =================
        #

        #  Keyword cards
        file.write(optstr1+" + \n")
        file.write(optstr2+" + \n")

        optstr = ""
        if len(optstr) or len(trialstr) != 0:
            file.write(optstr+" "+trialstr)

        ###set nbq [ get_number_of_bqs coords=$coords ]
        nbq=0
        file.write(optstr3 + "\n")
        file.write("MNDO file from the CCP1 GUI\n\n")
        #
        # Output coordinate information
        # (see helper functions in ../interface_gamess/interface.c)
        #

        if task == MENU_OPT:
            tt = ' 1 '
        else:
            tt = ' 0 '
            
        for a in mol.atom:
            file.write(
                str(a.get_number()) + ' ' +
                str(a.coord[0]) + tt +
                str(a.coord[1]) + tt +
                str(a.coord[2]) + tt + '\n')
        # Termination of coordinates
        file.write("0 0.0 0 0.0 0 0.0 0\n")

        # Output of point charges
        #if { $binary == 1 } {
        #format_mndo_bq_list_long file $jobname.in
        #} else {
        #format_mndo_bq_list file $jobname.in
        #}

        # Input writing finishes here
        file.close()
        return 0

    def makejob(self,writeinput=1,graph=None):
        """Build the MNDO job"""

        self.GetModel()
        mol_obj  = self.get_input("mol_obj")
        job_name = self.get_name()

        directory = self.get_parameter("directory")
        job_name = self.get_parameter("job_name")
        self.infile = directory+os.sep+job_name+'.in'
        self.outfile = directory+os.sep+job_name+'.out'

        if writeinput:
            self.WriteInput()
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

        # Delete old vectors
        if self.chk == 0:
            job.add_step(DELETE_FILE,'remove old vectors',remote_filename="fort.11",kill_on_error=0)
        job.add_step(DELETE_FILE,'remove old output',remote_filename=self.outfile,kill_on_error=0)
        job.add_step(COPY_OUT_FILE,'transfer input',local_filename=self.infile)

        # Local windows job, search for local executable
        if sys.platform[:3] == 'win' and hostname == 'localhost':
            # Name of executable, assume install of exe into exe subdirectory
            try:
                install_dir = os.environ['MNDO_BIN']
                mndo_exe=install_dir+'\mndo.exe'
            except KeyError:
                mndo_exe=root_path+'/exe/mndo.exe'
            print 'Using MNDO path ' + mndo_exe
            job.add_step(RUN_APP,'run MNDO',local_command=mndo_exe,stdin_file=None,stdout_file=None)
        elif sys.platform[:3] == 'mac':
            pass
        else:
            mndo_exe="mndo"
            job.add_step(RUN_APP,'run MNDO',local_command=mndo_exe,stdin_file=self.infile,stdout_file=self.outfile)

        job.add_step(COPY_BACK_FILE,'recover log',remote_filename=self.outfile)

        #if sys.platform[:3] == 'win':
        #    job.add_step(COPY_BACK_FILE,'fetch punch',local_filename=job_name+'.pun',remote_filename='ftn058')
        #else:
        #    job.add_step(COPY_BACK_FILE,'recover punch',remote_filename=job_name+'.pun')

        job.add_step(PYTHON_CMD,'load results',proc=lambda s=self,g=graph: s.endjob(g))
        job.add_tidy(self.endjob2)
        return job

    def endjob(self,graph):
        """This is executed when the job completes successfully
        from within the job thread
        it should not perform Tk operations
        """
        return 0,""

    def endjob2(self,code=0):

        """This function is executed in the main thread if the job completes
        satisfactorily"""

        print 'endjob2'
        if self.debug:
            print 'running endjob2 code=',code

        # load contents of listing for viewing
        if self.debug_slave:
            print 'endjob....'
        job_name = self.get_parameter("job_name")
        directory = self.get_parameter("directory")

        #file = open(directory+'/'+job_name+'.out','r')
        file = open(self.outfile,'r')
        self.ReadOutput(file)
        file.close()

        # load in fort.15  ... only in case of success
        if code:
            return
        
        fp = open(directory + '/fort.15',"r")
        line = fp.readline()
        ttt = ["coordinates angstrom"]
        if line[:31] == " CARTESIAN COORDINATES: NUMAT =":
            nat_rd = int(line[31:])
            for i in range(nat_rd):
                line = fp.readline()
                words = line.split()
                txt = z_to_el[int(words[1])] + " " + words[2] + " " + words[3] + " " + words[4]
                ttt.append(txt)

        print ttt

        o = self.get_input("mol_obj")
        res = Zmatrix(list=ttt)
        res.connect()
        res.name = "unnamed"
        res.title = "untitled"
        print res
        res.list()
        #self.results = [ res ]

        # problem here as that as we are running in a slave thread
        # we cannot use Tk .. so this is silent

        ed = self.get_editor()
        if ed:
            try:
                ed.connect_model(res)
            except AttributeError:
                pass

            if ed.graph:
                #ed.graph.import_objects(self.results)
                txt = "Objects loaded from punchfile:"
                txt = txt  + "Structure update" '\n'
                #for r in self.results:
                #    txt = txt + r.title + '\n'
                ed.Info(txt)
            # Update 
            if ed.update_func:
                o = self.get_input("mol_obj")
                #name = self.get_input("mol_name")
                print 'performing update using res'
                ed.update_func(res)

    def get_theory(self):
        return self.get_parameter("theory")

    def check_direct(self):
        return 0

class MNDOCalcEd(QMCalcEd):

    def __init__(self,root,calc,graph,**kw):
        apply(QMCalcEd.__init__, (self,root,calc,graph), kw)

        self.tasks = [MENU_ENER, MENU_GRAD, MENU_OPT]
##        self.tasks = ["energy", 
##                      "optimise internal coord.", 
##                      "optimise cartesian coord."]

        self.theories["energy"] = ["AM1", "PM3" ]
        self.basissets = ["STO"]
        self.AddPage("SCFPage","SCF")

        self.scf_methods = {}
        tmp =  ["rhf","rohf","uhf"]
        self.scf_methods[MENU_ENER] = tmp
        self.scf_methods[MENU_GRAD] = tmp
        self.scf_methods[MENU_OPT] = tmp

        self.hamiltonians = [ "mndo/d", "pm3", "am1", "mndo", "mindo/3", "cndo/2", "om1" , "om2" ]

        # self.AddPage("DirectivesPage","Directives")
        self.homolumo    = Tkinter.BooleanVar()
        self.chargeden   = Tkinter.BooleanVar()
        self.frequencies = Tkinter.BooleanVar()

        #Create the tools used in the Molecule tab - spin & charge created in QM.
        self.task_tool = SelectOptionTool(self,'task','Task',self.tasks,command=self.__taskupdate)
        #Used to specify task
        self.tasktoolvalue = self.task_tool.widget.getvalue() 

        self.checkspin_widget = Tkinter.Button(self.interior(),
                                             text = 'Check Spin',
                                             command = self.__CheckSpin)
        self.symmetry_tool = BooleanTool(self,'symmetry','Use Symmetry')

        mol_obj = self.calc.get_input('mol_obj')

##         # need to propagate the default basis back
##         self.basis_manager = self.calc.basis_manager
##         self.basis_tool = BasisTool(self,'basis','ECP','default_basis',
##                                     molecule=mol_obj,basis_manager=self.basis_manager)

##         #Create the tools used in the Theory tab
##         #self.guess_tool = GamessGuessTool(self,self.__guesscommand)
##         self.guessoption_tool = SelectOptionTool(self,'guess_method','Vectors',self.guess_options,
##                                                  self.__guesstype)
##         self.guessatoms_tool = SelectOptionTool(self,'guess_comp',None,self.compute_options)
##         self.guesssection1_tool = IntegerTool(self,'guess_sect1','Section a',0)
##         self.guesssection2_tool = IntegerTool(self,'guess_sect2','Section b',0)
##         self.guessgetqblock1_tool = IntegerTool(self,'getq_block1','File Block a',0)
##         self.guessgetqblock2_tool = IntegerTool(self,'getq_block2','File Block b',0)
##         self.guessgetqsection1_tool = IntegerTool(self,'getq_sect1','File Section a',0)
##         self.guessgetqsection2_tool = IntegerTool(self,'getq_sect2','File Section b',0)
        

        self.scfmethod_tool = SelectOptionTool(self,'scf_method',
                                               'SCF Method',
                                               self.scf_methods[self.tasktoolvalue],
                                               self.__scfmethod)

        self.hamiltonian_tool = SelectOptionTool(self,'hamiltonian',
                                                 'Hamiltonian',
                                                 self.hamiltonians)

        self.scfmaxcycles_tool = IntegerTool(self,'scf_maxcyc','Max. Cycles',1)
        self.scfthreshold_tool = IntegerTool(self,'scf_threshold','Threshold',3)

##         self.scfbypass_tool = BooleanTool(self,'scf_bypass', 'Bypass SCF')

##         self.scflevelinit_tool = FloatTool(self,'scf_level_init','Initial Levelshifter Value',0.0)
##         self.scflevelit_tool = IntegerTool(self,'scf_level_it','Cycle to change on',1)
##         self.scflevelfinal_tool = FloatTool(self,'scf_level_final','Final Levelshifter Value',0.0)
        

##         self.postscfmethod_tool = SelectOptionTool(self,'postscf_method',
##                                                    'Method',
##                                                    self.postscf_methods[self.tasktoolvalue])


##         #Create the tools for the DFT tab
##         self.dftfunctional_tool = SelectOptionTool(self,'dft_functional','Functional',self.dft_functionals)
##         self.dftaccuracy_tool = SelectOptionTool(self,'dft_grid','Grid setting',self.dft_grids)
##         self.dftweightscheme_tool = SelectOptionTool(self,'dft_weights',
##                                                      'DFT weighting scheme',
##                                                      self.dft_weights)

##         self.dftradial_tool = MenuCounterTool(self,
##                                               'dft_radialgrid',
##                                              'Radial Grid',
##                                              self.dft_radialgrids,
##                                              'dft_radialgridpoints',
##                                              'Number of points',
##                                              command = self.__dftradialgridpoints
##                                              )
##         self.radialgrid = self.dftradial_tool.firstmenu.getvalue()
        
##         self.dftangular_tool = MenuCounterMenuTool(self,
##                                                    'dft_angulargrid',
##                                                    'Angular Grid',
##                                                    self.dft_angulargrids,
##                                                    'dft_angulargridpoints',
##                                                    'Number of points',
##                                                    'dft_angulargridpoints',
##                                                    'Number of points',
##                                                    self.dft_lebedevpoints,
##                                                    command = self.__dftangulargridpoints
##                                                    )
##         self.angulargrid = self.dftangular_tool.firstmenu.getvalue()

##         self.dftjfit_tool = BooleanTool(self,'dft_jfit','Use Coulomb Fitting',self.__dftjbasselect)
##         self.dftjbas_tool = SelectOptionTool(self,'dft_jbas','Fitting Basis',self.dft_jbas)
##         self.dftschwarz_tool = IntegerTool(self,'dft_schwarz','Schwarz cutoff')

##         #Create the tools used in the Properties tab
##         self.homolumo_tool = BooleanTool(self, 'ana_homolumo', 'HOMO/LUMO')
##         self.homolumo1_tool = BooleanTool(self, 'ana_homolumo1', 'HOMO1/LUMO1')
##         self.homolumo2_tool = BooleanTool(self, 'ana_homolumo2', 'HOMO2/LUMO2')
##         self.homolumo3_tool = BooleanTool(self, 'ana_homolumo2', 'HOMO3/LUMO3')
##         self.homolumo4_tool = BooleanTool(self, 'ana_homolumo4', 'HOMO4/LUMO4') 
##         self.homolumo5_tool = BooleanTool(self, 'ana_homolumo5', 'HOMO5/LUMO5')
       
##         self.chargeden_tool = BooleanTool(self, 'ana_chargeden', 'Charge Density')
##         self.diffden_tool = BooleanTool(self, 'ana_diffden', 'Difference Density')
##         self.potential_tool = BooleanTool(self, 'ana_potential', 'Potential')
##         self.chargedengrad_tool = BooleanTool(self, 'ana_chargedengrad', 'Gradient Density')
##         self.spinden_tool = BooleanTool(self, 'ana_spinden', 'Spin Density')
##         self.frequencies_tool = BooleanTool(self, 'ana_frequencies', 'Finite Difference')
##         self.hessian_tool = BooleanTool(self, 'ana_hessian', "Analytic")

##         #Create the tools used in the Optimisation tab

##         self.optcoords_tool = SelectOptionTool(self,'optimiser', 'Opt. Coords',
##                                                self.optcoord_opts, self.__selectcoords)
##         self.find_ts_tool = BooleanTool(self,"find_ts","Locate Transition State",self.__findts)
##  #       self.optmethod_tool = SelectOptionTool(self,'optimiser_method','Method',self.optmethodopts)

##         self.optmaxcyc1_tool = IntegerTool(self,'max_opt_step','Energy evaluations',0)
##         self.optmaxcyc2_tool = IntegerTool(self,'max_opt_line','Line searches',0)
##         self.optxtol_tool = FloatTool(self,'opt_conv_thsld','Convergence Thresh.',0.0)        
##         self.optstepmax_tool = FloatTool(self,'max_opt_step_len','Max. Step size',0.0)        
##         self.optvalue_tool = FloatTool(self,'opt_value','Turning Point Accuracy',0.0)

##         self.optjorg_tool = BooleanTool(self,'opt_jorgensen','Use Jorgensen-Simons Algorithm',
##                                         self.__optjorgensen)
##         self.optpowell_tool = BooleanTool(self,'opt_powell','Use Powell Hessian update')
##         self.optbfgs_tool = SelectOptionTool(self,'opt_hess_update', 'Hessian Update Procedure',
##                                              self.optbfgs_opts)
##         self.optminhess_tool = FloatTool(self,'opt_min_hess','Min. Hessian Eigenvalue')
##         self.optmaxhess_tool = FloatTool(self,'opt_max_hess','Max. Hessian Eigenvalue')
##         self.optrfo_tool = MenuAndBooleanTool(self,'opt_rfo','opt_rfomode',
##                                               'Use Rational Function Optimisation',
##                                               'RFO Mode',self.optrfo_opts)

##         #Create the tools used for the Job tab
##         self.jobname_tool = TextFieldTool(self,'job_name','Job Name')
##         self.hostname_tool = SelectOptionTool(self,'hostname',  'Host name',
##                                               self.hostnames, command=self.__sethost)
##         self.hostname = self.hostname_tool.widget.getvalue()# get the hostname for the below tool      
##         self.submission_tool = SelectOptionTool(self,'submission','Job Submission',
##                                                 self.submissionpolicies[self.hostname])
##         self.username_tool = TextFieldTool(self,'username','User Name')
##         self.workingdirectory_tool = ChangeDirectoryTool(self,'directory','Working Directory')

##         #Create the tools used in the Restart Group
##         self.ed0keep_tool = BooleanTool(self, 'ed0_keep', 'specify',
##                                         command=lambda s=self: s.__keepfile('ed0'))
##         self.ed0path_tool = ChangeDirectoryTool(self,'ed0_path','')
##         self.ed2keep_tool = BooleanTool(self, 'ed2_keep', 'keep',
##                                         command=lambda s= self: s.__keepfile('ed2'))
##         self.ed2name_tool = BooleanTool (self, 'ed2_specify','specify ',
##                                          command=lambda s=self: s.__keepfile('ed2'))
##         self.ed2path_tool = FileTool(self,'ed2_path','',
##                                       filetypes=[('Mainfiles','*.ed2'), ('All files','*.*')])
##         self.ed3keep_tool = BooleanTool(self, 'ed3_keep', 'keep',
##                                         command=lambda s = self: s.__keepfile('ed3'))
##         self.ed3name_tool = BooleanTool (self, 'ed3_specify','specify ',
##                                          command=lambda s=self: s.__keepfile('ed3'))
##         self.ed3path_tool = FileTool(self,'ed3_path','',
##                                      filetypes=[('Dumpfiles','*.ed3'), ('All files','*.*')])
##         self.ed7keep_tool = BooleanTool(self, 'ed7_keep', 'keep',
##                                         command=lambda s = self: s.__keepfile('ed7'))
##         self.ed7name_tool = BooleanTool (self, 'ed7_specify','specify ',
##                                          command=lambda s=self: s.__keepfile('ed7'))
##         self.ed7path_tool = FileTool(self,'ed7_path','',
##                                       filetypes=[('Tempfiles','*.ed7'), ('All files','*.*')])
##         self.ed14keep_tool = BooleanTool(self, 'ed14_keep', 'specify',
##                                         command=lambda s=self: s.__keepfile('ed14'))
##         self.ed14path_tool = FileTool(self,'ed14_path','',
##                                       filetypes=[('Dumpfiles','*.ed3'), ('All files','*.*')],
##                                       action="open")

        self.LayoutToolsTk()

        self.__initialisetools()

    def __initialisetools(self):
        pass

    def __taskupdate(self,task):
        """Update the SCF and post-SCF methods for the task that has been selected
           and hide the optimisation tab
        """
        self.scfmethod_tool.SetItems(self.scf_methods[task])
####        self.postscfmethod_tool.SetItems(self.postscf_methods[task])
        if task != 'Geometry Optimisation':
            self.notebook.tab('Optimisation').configure(state="disabled")
        else:
            self.notebook.tab('Optimisation').configure(state="active")

    def LayoutToolsTk(self):
        """Place the widgets belonging to the tools (ChargeTool etc)
        This will generally be replaced by a more specific function
        for a particular code interface.
        """
        #Add Molecule tab
        page = self.notebook.add('Molecule',tab_text='Molecule')
        
        # Associate helpfile with notebook frame
        tab = self.notebook.tab('Molecule')
        viewer.help.sethelp(tab,'Molecule Tab')

        page.optgroup = Pmw.Group(page,tag_text="Options")
        page.optgroup.pack(expand='yes',fill='both')
##         page.basisgroup = Pmw.Group(page,tag_text="Basis Selector")
##         page.basisgroup.pack(expand='yes',fill='both')

        self.title_tool.widget.pack(in_=page.optgroup.interior())
        self.task_tool.widget.pack(in_=page.optgroup.interior())
        self.scfmethod_tool.widget.pack(in_=page.optgroup.interior())
        self.hamiltonian_tool.widget.pack(in_=page.optgroup.interior())
        self.charge_tool.widget.pack(in_=page.optgroup.interior())
        self.spin_tool.widget.pack(in_=page.optgroup.interior())
        self.checkspin_widget.pack(in_=page.optgroup.interior())

##         self.symmetry_tool.widget.pack(in_=page.optgroup.interior())

##         Pmw.alignlabels([self.charge_tool.widget, self.spin_tool.widget])
##         self.basis_tool.widget.pack(in_=page.basisgroup.interior())

##         #Add Theory tab
##         page = self.notebook.add('Theory',tab_text='Theory')
##         # Associate helpfile with notebook frame
##         tab = self.notebook.tab('Theory')
##         tkmolview.help.sethelp(tab,'Theory Tab')
        
##         page.guessgroup = Pmw.Group(page,tag_text="Guess")
##         page.guessgroup.pack(expand='yes',fill='both')
##         self.guessoption_tool.widget.pack(in_=page.guessgroup.interior(),side='left')
##         page.guessframe = Tkinter.Frame(page.guessgroup.interior())
##         page.guessframe.pack(in_=page.guessgroup.interior(),side='left')
##         self.guessatoms_tool.SetParent(page.guessframe)
##         self.guesssection1_tool.SetParent(page.guessframe)
##         self.guesssection2_tool.SetParent(page.guessframe)
##         self.guessgetqblock1_tool.SetParent(page.guessframe)
##         self.guessgetqsection1_tool.SetParent(page.guessframe)
##         self.guessgetqblock2_tool.SetParent(page.guessframe)
##         self.guessgetqsection2_tool.SetParent(page.guessframe)

##         page.scfgroup = Pmw.Group(page,tag_text="SCF")
##         page.scfgroup.pack(expand='yes',fill='both')
##         self.scfmethod_tool.widget.pack(in_=page.scfgroup.interior())
##         self.scfmaxcycles_tool.widget.pack(in_=page.scfgroup.interior())
##         self.scfthreshold_tool.widget.pack(in_=page.scfgroup.interior())
##         self.scfbypass_tool.widget.pack(in_=page.scfgroup.interior())

##         page.scflevelgroup = Pmw.Group(page,tag_text="SCF Level Shifters")
##         page.scflevelgroup.pack(in_=page.scfgroup.interior(),
##                                 expand='yes',
##                                 fill='both',
##                                 padx=10,
##                                 pady=10)
##         self.scflevelinit_tool.widget.pack(in_=page.scflevelgroup.interior())
##         self.scflevelit_tool.widget.pack(in_=page.scflevelgroup.interior())
##         self.scflevelfinal_tool.widget.pack(in_=page.scflevelgroup.interior())

##         page.postscfgroup = Pmw.Group(page,tag_text="Post SCF")
##         page.postscfgroup.pack(expand='yes',fill='both')

##         self.postscfmethod_tool.widget.pack(in_=page.postscfgroup.interior())

        
##         #Add DFT tab
##         page = self.notebook.add('DFT',tab_text='DFT')
##         # Associate helpfile with notebook frame
##         tab = self.notebook.tab('DFT')
##         tkmolview.help.sethelp(tab,'DFT Tab')
        
##         page.dftgroup1 = Pmw.Group(page,tag_text="Functional")
##         page.dftgroup1.pack(expand='yes',fill='both')
##         page.dftgroup2 = Pmw.Group(page,tag_text="Accuracy")
##         page.dftgroup2.pack(expand='yes',fill='both')
##         page.dftgroup3 = Pmw.Group(page,tag_text="Quadrature Types")
##         page.dftgroup3.pack(expand='yes',fill='both')
##         #page.dftgroup4 = Pmw.Group(page,tag_text="DFT Options4")
##         #page.dftgroup4.pack(expand='yes',fill='both')
##         page.dftgroup5 = Pmw.Group(page,tag_text="Coulomb Fitting")
##         page.dftgroup5.pack(expand='yes',fill='both')


##         self.dftfunctional_tool.widget.pack(in_=page.dftgroup1.interior())
##         self.dftaccuracy_tool.widget.pack(in_=page.dftgroup2.interior())
##         self.dftweightscheme_tool.widget.pack(in_=page.dftgroup2.interior())        
##         self.dftradial_tool.widget.pack(in_=page.dftgroup3.interior(),side='top')
##         self.dftangular_tool.widget.pack(in_=page.dftgroup3.interior(),side='top')
        
##         self.dftjfit_tool.SetParent(page.dftgroup5.interior())
##         self.dftjfit_tool.Pack()
##         self.dftjbas_tool.SetParent(page.dftgroup5.interior())
##         self.dftschwarz_tool.SetParent(page.dftgroup5.interior())

##         # Add Properties tab
##         page = self.notebook.add('Properties',tab_text='Properties')
        
##         # Associate helpfile with notebook frame
##         tab = self.notebook.tab('Properties')
##         tkmolview.help.sethelp(tab,'Properties Tab')
        
##         page.grgroup = Pmw.Group(page,tag_text="Graphical options")

##         page.grgroup.pack(expand='yes',fill='x')

##         page.mogroup = Pmw.Group(page.grgroup.interior(),tag_text="Orbital Plots")
##         page.mogroup.pack(expand='yes',fill='x',side='right')
##         self.homolumo_tool.widget.pack(in_=page.mogroup.interior())
##         self.homolumo1_tool.widget.pack(in_=page.mogroup.interior())
##         self.homolumo2_tool.widget.pack(in_=page.mogroup.interior())
##         self.homolumo3_tool.widget.pack(in_=page.mogroup.interior())
##         self.homolumo4_tool.widget.pack(in_=page.mogroup.interior())
##         self.homolumo5_tool.widget.pack(in_=page.mogroup.interior())

##         f = Frame(page.grgroup.interior())
##         f.pack(expand='yes',fill='x',side='left')
##         page.group2 = Pmw.Group(f,tag_text="Density and Potential")
##         page.group2.pack(expand='yes',fill='x',side='top')
##         self.chargeden_tool.widget.pack(in_=page.group2.interior())
##         self.diffden_tool.widget.pack(in_=page.group2.interior())
##         self.potential_tool.widget.pack(in_=page.group2.interior())
##         self.chargedengrad_tool.widget.pack(in_=page.group2.interior())
##         self.spinden_tool.widget.pack(in_=page.group2.interior())

##         page.editgrid_button = Tkinter.Button(f,command=self.edit_grid)
##         page.editgrid_button.config(text="Edit Grid")
##         page.editgrid_button.pack(side='bottom',padx=10,pady=20)

##         page.vgroup = Pmw.Group(page,tag_text="Frequencies")
##         page.vgroup.pack(expand='yes',fill='x')
##         self.frequencies_tool.widget.pack(in_=page.vgroup.interior())
##         self.hessian_tool.widget.pack(in_=page.vgroup.interior())

##         Pmw.alignlabels([self.homolumo_tool.widget,
##                          self.homolumo1_tool.widget,
##                          self.homolumo2_tool.widget,
##                          self.homolumo3_tool.widget,
##                          self.homolumo4_tool.widget,
##                          self.homolumo5_tool.widget])

##         Pmw.alignlabels([self.potential_tool.widget,
##                          self.chargeden_tool.widget,
##                          self.diffden_tool.widget,
##                          self.chargedengrad_tool.widget,
##                          self.spinden_tool.widget,
##                          page.editgrid_button])


        #Add Optimisation tab
        page = self.notebook.add('Optimisation',tab_text='Optimisation')
        
        # Associate helpfile with notebook frame
        tab = self.notebook.tab('Optimisation')
        viewer.help.sethelp(tab,'Optimisation Tab')
        
##         page.rungroup = Pmw.Group(page,tag_text="Runtype")
##         page.rungroup.pack(expand='yes',fill='both')
##         self.optcoords_tool.widget.pack(in_=page.rungroup.interior())
##         self.find_ts_tool.widget.pack(in_=page.rungroup.interior())

##         page.searchgroup = Pmw.Group(page,tag_text="Search Procedure")
##         page.searchgroup.pack(expand='yes',fill='both')
##         self.optmaxcyc1_tool.SetParent(page.searchgroup.interior())
##         self.optmaxcyc1_tool.Pack()
##         self.optmaxcyc2_tool.SetParent(page.searchgroup.interior())
##         self.optmaxcyc2_tool.Pack()
##         self.optxtol_tool.SetParent(page.searchgroup.interior())
##         self.optxtol_tool.Pack()
##         self.optstepmax_tool.SetParent(page.searchgroup.interior())
##         self.optstepmax_tool.Pack()
##         self.optvalue_tool.SetParent(page.searchgroup.interior())
##         self.optvalue_tool.Pack()
##         Pmw.alignlabels([self.optmaxcyc1_tool.widget, self.optmaxcyc2_tool.widget,
##                          self.optxtol_tool.widget, self.optstepmax_tool.widget,
##                          self.optvalue_tool.widget])
        
##         page.jorggroup = Pmw.Group(page,tag_text="Jorgensen-Simons Algorithm")
##         page.jorggroup.pack(expand='yes',fill='both')
##         self.optjorg_tool.SetParent(page.jorggroup.interior())
##         self.optjorg_tool.Pack()
##         self.optpowell_tool.SetParent(page.jorggroup.interior())
##         self.optbfgs_tool.SetParent(page.jorggroup.interior())
##         self.optminhess_tool.SetParent(page.jorggroup.interior())
##         self.optmaxhess_tool.SetParent(page.jorggroup.interior())
##         self.optrfo_tool.SetParent(page.jorggroup.interior())
##         Pmw.alignlabels([self.optjorg_tool.widget, self.optpowell_tool.widget,
##                          self.optbfgs_tool.widget, self.optminhess_tool.widget,
##                          self.optmaxhess_tool.widget, self.optrfo_tool.widget])

##         #Add Job tab
##         page = self.notebook.add('Job',tab_text='Job')

##         # Associate helpfile with notebook frame
##         tab = self.notebook.tab('Job')
##         tkmolview.help.sethelp(tab,'Job Tab')
        
##         page.jobgroup = Pmw.Group(page,tag_text="Job Group")
##         page.jobgroup.pack(side='top',expand='yes',fill='both')

##         self.jobname_tool.widget.pack(in_=page.jobgroup.interior())
##         self.hostname_tool.widget.pack(in_=page.jobgroup.interior())
##         self.submission_tool.widget.pack(in_=page.jobgroup.interior())
##         self.username_tool.widget.pack(in_=page.jobgroup.interior())
##         self.workingdirectory_tool.widget.pack(in_=page.jobgroup.interior())

##         #Add Restart group
##         page.fpathgroup = Pmw.Group(page,tag_text="File Path Group")
##         page.fpathgroup.pack(expand='yes',fill='both')

##         #Need to create multiple frames so things can be packed and forgotten
##         # without the order getting all jumbled.
##         page.ed0frame = Tkinter.Frame(page.fpathgroup.interior())
##         page.ed0frame.pack(in_=page.fpathgroup.interior(),side='top',
##                              expand='yes', fill='both')
##         ed0label = Tkinter.Label(page.ed0frame, text='ECP Libraries (ed0) ')
##         ed0label.pack(side='left')
##         self.ed0keep_tool.SetParent(page.ed0frame)
##         self.ed0path_tool.SetParent(page.ed0frame)
##         self.ed0keep_tool.widget.pack(in_=page.ed0frame, side='left')

##         page.ed2frame = Tkinter.Frame(page.fpathgroup.interior())
##         page.ed2frame.pack(in_=page.fpathgroup.interior(),side='top',
##                              expand='yes', fill='both')
##         ed2label = Tkinter.Label(page.ed2frame, text='Mainfile (ed2) ')
##         ed2label.pack(side='left')
##         self.ed2keep_tool.SetParent(page.ed2frame)
##         self.ed2name_tool.SetParent(page.ed2frame)
##         self.ed2path_tool.SetParent(page.ed2frame)
##         self.ed2keep_tool.widget.pack(in_=page.ed2frame, side='left')

##         page.ed3frame = Tkinter.Frame(page.fpathgroup.interior())
##         page.ed3frame.pack(in_=page.fpathgroup.interior(),side='top',
##                              expand='yes', fill='x')
##         ed3label = Tkinter.Label(page.ed3frame, text='Dumpfile (ed3) ')
##         ed3label.pack(side='left')
##         self.ed3keep_tool.SetParent(page.ed3frame)
##         self.ed3path_tool.SetParent(page.ed3frame)
##         self.ed3name_tool.SetParent(page.ed3frame)
##         self.ed3keep_tool.widget.pack(in_=page.ed3frame, side='left')

##         page.ed7frame = Tkinter.Frame(page.fpathgroup.interior())
##         page.ed7frame.pack(in_=page.fpathgroup.interior(),side='top',
##                              expand='yes', fill='both')
##         ed7label = Tkinter.Label(page.ed7frame, text='Tempfile (ed7) ')
##         ed7label.pack(side='left')
##         self.ed7keep_tool.SetParent(page.ed7frame)
##         self.ed7name_tool.SetParent(page.ed7frame)
##         self.ed7path_tool.SetParent(page.ed7frame)
##         self.ed7keep_tool.widget.pack(in_=page.ed7frame, side='left')

##         page.ed14frame = Tkinter.Frame(page.fpathgroup.interior())
##         page.ed14frame.pack(in_=page.fpathgroup.interior(),side='top',
##                              expand='yes', fill='both')
##         ed14label = Tkinter.Label(page.ed14frame, text='Foreign Dumpfile (ed14) ')
##         ed14label.pack(side='left')
##         self.ed14keep_tool.SetParent(page.ed14frame)
##         self.ed14path_tool.SetParent(page.ed14frame)
##         self.ed14keep_tool.widget.pack(in_=page.ed14frame, side='left')

##         Pmw.alignlabels([self.ed0keep_tool.widget,
##                          self.ed0path_tool.widget,
##                          self.ed2keep_tool.widget,
##                          self.ed2path_tool.widget,
##                          self.ed2name_tool.widget,
##                          self.ed2keep_tool.widget,
##                          self.ed3path_tool.widget,
##                          self.ed3name_tool.widget,
##                          self.ed3keep_tool.widget,
##                          self.ed7path_tool.widget,
##                          self.ed7name_tool.widget,
##                          self.ed7keep_tool.widget,
##                          self.ed14path_tool.widget,
##                          self.ed14keep_tool.widget])



    def TaskPage(self,page,action):
        QMCalcEd.TaskPage(self,page,action)

        # Create a group for the checkboxes
        if action == Create:
            page.group = Pmw.Group(page,tag_text="Analysis options")
            page.group.pack(expand='yes',fill='x')

    def SCFPage(self,page,action):
        """Maintain the SCF page."""
        labels = []

    def DirectivesPage(self,page,action):
        """Entry for various directives not covered by GUI yet"""
        pass
        

    def __CheckSpin(self):
        for tool in self.tools:
            tool.ReadWidget()
        self.calc.CheckSpin()


    def __scfmethod(self,scf):
        """Configure all widgets and variables that depend on the SCF type.
        """
        self.scfmethod_tool.ReadWidget()
        #if (scf == 'DFT') or (scf == 'UDFT') or (scf == 'Direct DFT') or (scf == 'Direct UDFT'):
        #    self.notebook.tab('DFT').configure(state="active")
        #else:
        #    self.notebook.tab('DFT').configure(state="disabled")
        #    
        # REM the default 'enter' and 'vectors' sections are configured in the __guesstype
        #  method as this is always run after the __scfmethod is invoked
        #guess = self.calc.get_parameter("guess_method")
        #self.__guesstype("")

if __name__ == "__main__":
    from mndo import *
    from objects.zmatrix import *
    from jobmanager import *
    model = Zmatrix()
    atom = ZAtom()
    atom.symbol = 'C'
    atom.name = 'C'
    model.insert_atom(0,atom)
    atom = ZAtom()
    atom.symbol = 'Cl'
    atom.name = 'Cl'
    atom.coord = [ 1.,0.,0. ]
    model.insert_atom(1,atom)
    atom = ZAtom()
    atom.symbol = 'H'
    atom.name = 'H'
    atom.coord = [ 1.,1.,0. ]
    model.insert_atom(1,atom)

    root=Tk()
    calc = MNDOCalc()
    calc.set_input('mol_obj',model)
    calc.set_parameter('task',MENU_OPT)
    jm = JobManager()
    je = JobEditor(root,jm)
    vt = MNDOCalcEd(root,calc,None,job_editor=je)
    vt.Run()
    #calc.WriteInput()

    root.mainloop()
