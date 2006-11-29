##
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
"""This module implements the ChemShell specific calculation and
calculation editor classes.
"""

import sys
import os
import time
import string
import tkFileDialog

from   calc       import *
from   filepunch  import *
from   gamessuk   import *
from   mopac      import *
from   mndo       import *
from   dl_poly    import *

def extend_path(arg):
    """Add an element to the path if not already present"""
    t = os.environ['PATH']
    t2 = t.split(';')
    #print t2
    if arg not in t2:
        os.environ['PATH'] = t + ';' + arg

class ChemShellCalc(Calc):

    def __init__(self,**kw):

        apply(Calc.__init__,(self,),kw)

        self.set_program('ChemShell')

        self.qmcalc = None
        self.mmcalc = None

        self.saveqmcalc = { }
        self.savemmcalc = { }

        self.set_parameter('calctype','QM')

        self.set_parameter('conn_scale',1.0)
        self.set_parameter('conn_toler',0.5)
        self.set_parameter('export_connectivity',1)

        # Q M / M M
        self.set_parameter('qmcode','gamess')
        self.set_parameter('mmcode','dlpoly')
        self.set_parameter('coupling','shift')
        self.set_parameter('qm_region',[])
        self.set_parameter('use_qmmm_cutoff',0)
        self.set_parameter('qmmm_cutoff',0.0)
        self.set_parameter('dipole_adjust',0)

        self.set_parameter('embed_r2',0)
        self.set_parameter('embed_r3',0)

        # O P T I M I S A T I O N
        self.set_parameter('task','energy')
        self.set_parameter('optimiser','newopt_c')
        self.set_parameter('newopt_method','bfgs')
        self.set_parameter('max_opt_step',100)
        self.set_parameter('find_ts',0)
        self.set_parameter('ts_mode',1)

        self.set_parameter('use_active_region',0)
        self.set_parameter('active_atoms',[])
        self.set_parameter('use_template_z',0)

        self.set_parameter('residue_treatment',"Single Residue")
        self.set_parameter('hdlc_region',[])
        self.set_parameter('use_hdlc_constraints',0)
        self.set_parameter('hdlcopt_memory','10000')

        # D Y N A M I C S
        self.set_parameter('temp',293)
        self.set_parameter('tstep',0.001)
        self.set_parameter('ensemble','NVE')
        self.set_parameter('shake_option','none')
        self.set_parameter('update_freq',10)
        self.set_parameter('max_dyn_step',1000)
        self.set_parameter('traj_freq',10)
        self.set_parameter('store_traj',0)

    def get_editor_class(self):
        return ChemShellCalcEd

    def makejob(self,writeinput=1,graph=None):
        """ Prepare the ChemShell job:
        1) Generate the script
        2) Construct the sequence of job steps
        """

        # make sure we are using the current model
        print 'getmodel from chemshell object'
        self.GetModel()

        mol_name = self.get_input("mol_name")
        mol_obj  = self.get_input("mol_obj")

        print 'ID',id(mol_obj)
        print mol_obj.atom

        job_name = self.get_name()
        
        # create QM and MM calculation objects 
        # if they dont already exist to supply
        # relevant defaults

        if self.qmcalc == None:
            self.create_qm_calc()

        if self.mmcalc == None:
            self.create_mm_calc()

        # backup copy
        #cmd.load_model(mol_obj,job_name+'_0')

        file = open(job_name+'.c','w')
        wrcon = self.get_parameter('export_connectivity')

        txt = mol_obj.output_coords_block(write_connect=wrcon,write_dummies=0)
        print 'check geom', txt

        for line in txt:
            file.write(line+'\n')
        file.close
        print 'file done'
    
        self.infile = job_name+'.chm'
        self.outfile = job_name+'.log'

        file = open(job_name+'.chm','w')
        if writeinput:
            mol_obj  = self.get_input("mol_obj")
            self.__WrtChemShellInput(mol_obj,file)
            file.close()
            #
            # load contents of input for viewing/editing
            file = open(self.infile,'r')
            input = file.readlines()
            self.set_input("input_file",input)
            file.close()
        else:
            input = self.get_input("input_file")
            for a in input:
                file.write(a)
            file.close()

        #
        #  Need to decide what kind of job run
        # 
        hostname = self.get_parameter("hostname")
        username = self.get_parameter("username")


        job = jobmanager.LocalJob()
#            else:
#                # Haven't implemented UNIX fork interface yet
#                job = jobmanager.ForegroundJob()
#        elif hostname == 'hpcx':
#            job = jobmanager.RemoteForegroundJob('hpcx',username)
#        elif hostname == 'tcsg7':
#            job = jobmanager.RemoteForegroundJob('tcsg7',username)
#        else:
#            print 'unsupported host'
#            return None
        job.name = job_name

        job.add_step(DELETE_FILE,'remove old output',remote_filename=job_name+'.log',kill_on_error=0)
        job.add_step(DELETE_FILE,'remove old punch',remote_filename=job_name+'.pun',kill_on_error=0)
        job.add_step(COPY_OUT_FILE,'transfer input',local_filename=job_name+'.chm')

        ed = self.get_editor()
        # connect up the monitor to load structure back
        if ed:
            print 'add_mon'
            job.add_monitor(ed.monitor)
        else:
            print 'DONT add_mon'            
        

        from viewer.rc_vars import rc_vars

        if sys.platform[:3] == 'win':

            # This is for the cygwin1.dll
            extend_path('C:/cygwin/bin')

            # this way, all the settings in cygwin chemsh and rungamess are
            # picked up

            if rc_vars.has_key('gamessuk_script') and rc_vars['gamessuk_script']:
                # Need to strip off the last field
                extend_path(os.path.dirname(rc_vars['gamessuk_script']))

            if rc_vars.has_key('chemsh_script_dir') and rc_vars['chemsh_script_dir']:
                extend_path(rc_vars['chemsh_script_dir'])

            use_bash=1

            if not use_bash:
                os.environ['TCL_LIBRARY']='/usr/share/tcl8.4'
#                os.environ['TCLLIBPATH']='/cygdrive/c/chemsh/tcl'
                os.environ['TCLLIBPATH']='/cygdrive/e/chemsh/tcl'
#                chemshell_exe='"C:/chemsh/bin/chemshprog.exe"'
                chemshell_exe='"E:/chemsh/bin/chemshprog.exe"'                
                print 'Using ChemShell path ' + chemshell_exe
                job.add_step(RUN_APP,'run ChemShell',
                             local_command=chemshell_exe,
                             stdin_file=self.infile,
                             stdout_file=self.outfile)
            else:
                #
                # horrible hack for windows case
                # under bash, it seems to find the subprocess exectables OK
                # when started without a parent bash shell it seems not too
                # have not established why yet)
                #
                job.add_step(RUN_APP,'run ChemShell',
                             use_bash=1,
                             local_command='chemsh',
                             local_command_args=[self.infile],
                             stdout_file=self.outfile)

        else:
            # running with an argument (rather than stdin redirection)
            # takes advantage of Tcls handling of errors, this way the
            # script will return on error without writing the punchfile 
            job.add_step(RUN_APP,'run ChemShell',
                         local_command='chemsh',
                         local_command_args=[self.infile],
                         stdout_file=self.outfile)

        job.add_step(COPY_BACK_FILE,'recover log',remote_filename=self.outfile)
        job.add_step(COPY_BACK_FILE,'recover punch',remote_filename=job_name+'.pun')
        job.add_step(PYTHON_CMD,'load results',proc=lambda s=self,g=graph: s.endjob(g))
        job.add_tidy(self.endjob2)
        return job

    def endjob(self,graph):
        """This is executed when the job completes successfully"""
        # load contents of listing for viewing
        return 0,""
    
    def endjob2(self,code=0):
        """
        This function is executed in the main thread if the job completes
        satisfactorily
        """
        print 'endjob2 code=',code

        job_name = self.get_name()
        file = open(self.outfile,'r')
        self.ReadOutput(file)
        file.close()

        if code:
            return

        self.__RdChemShellPunch(job_name+'.pun')

        # scan the punchfile
        #if self.__ReadPunch(job_name+'.pun') != 1:
        #    raise JobError, "No molecular structure in Punchfile - check output"
        # problem here as that as we are running in a slave thread
        # we cannot use Tk .. so this is silent

        ed = self.get_editor()
        if ed:
            if ed.graph:
                ed.graph.import_objects(self.results)
            
                txt = "Objects loaded from punchfile:"
                txt = txt  + "Structure update" + '\n'
                for r in self.results:
                    txt = txt + r.title + '\n'
                ed.Info(txt)

            o = self.get_input("mol_obj")
            name = self.get_input("mol_name")
            o.list()
            if ed.update_func:
                ed.update_func(o)

    def set_qm_code(self,code):
        print code,  self.get_parameter("qmcode")
        oldcode = self.get_parameter("qmcode")
        if oldcode == code:
            return
        self.saveqmcalc[oldcode] = self.qmcalc
        self.qmcalc = self.saveqmcalc.get(code, None)
        self.set_parameter("qmcode",code)

    def create_qm_calc(self):
        code = self.get_parameter("qmcode")
        print 'QM code', code
        if code == "gamess":
            self.qmcalc = GAMESSUKCalc()
        elif code == "mopac":
            self.qmcalc = MopacCalc()
        elif code == "mndo":
            self.qmcalc = MNDOCalc()
        else:
            print 'cant start '+code

    def create_mm_calc(self):
        code = self.get_parameter("mmcode")
        if code == "dlpoly":
            self.mmcalc = DLPOLYCalc()
        else:
            print 'cant start '+code

    def scan(self):
        """Extract and Store results from a punchfile"""
        #mol_name = self.get_input("mol_name")
        #mol_obj  = self.get_input("mol_obj")
        #job_name = self.get_name()
        file = tkFileDialog.askopenfilename(filetypes=[("Punch File","*.pun"),("All Files","*.*")])
        job_name = self.get_name()
        self.__RdChemShellPunch(file)

    def __RdChemShellPunch(self,file):

        # the punchfile format is used
        p = PunchReader()
        p.scan(file)

        if not p.title:
            p.title = self.get_title()
        if p.title == "untitled":
            p.title = self.get_input("mol_name")

        self.results = []

        # construct the results list for visualisation
        for o in p.objects:

            # take the last field of the class specification
            t1 = string.split(str(o.__class__),'.')
            myclass = t1[len(t1)-1]

            if myclass == 'VibFreq' :
                # create a vibration visualiser
                self.results.append(o)

            if myclass == 'VibFreqSet' :
                # create a vibration set visualiser
                self.results.append(o)

            elif myclass == 'Indexed' or myclass == 'Zmatrix':
                #
                # We expect a single molecule to be returned
                # will need to organise together with other results
                # assume overwrite for now
                # 
                print 'Copying contents'
                oldo = self.get_input("mol_obj")
                copycontents(oldo,o)
                print 'Copying contents done'

            elif myclass == 'Brick':
                self.results.append(o)

    def __RunChemShell(self,jobname):
        f = os.popen('chemsh '+jobname+'.chm | tee '+jobname+'.log','w')
        status = f.close()
        if status == None:
            status = 0
        return status

    def __WrtChemShellInput(self,mol,file):

        self.file = file
        file.write("# This file was generated by the QUASI python GUI\n")
        file.write("# on " + time.asctime(time.localtime(time.time())) + '\n')
        file.write("# Title : " + self.title + '\n')

        file.write("global root \n")
        file.write("global theory_type \n")
        file.write("global qm_theory \n")
        file.write("global chemsh_default_connectivity_toler  \n")
        file.write("global chemsh_default_connectivity_scale \n")
        file.write("global qm \n")
        file.write("catch {file delete qm_trajectory.xyz} \n")
        file.write("catch {file delete qm_trajectory.coo} \n")
        file.write("# \n")
        file.write("# Future GUI control \n")
        file.write("# \n")
        file.write("set groups       undefined \n")
        file.write("set mxlist       4000 \n")
        file.write("set mxexcl       1000 \n")
        file.write("set diis         1 \n")
        file.write("set scratchdir   . \n")
        file.write("# \n")
        file.write("set contyp         undefined \n")
        file.write("set ctfirst        undefined \n")
        file.write("set recalc         0 \n")

        # For debugging.....
        file.write("set mm_list_option full \n")

        file.write("set scfconv        undefined \n")
        file.write("set g98_mem        1000000 \n")
        file.write("set guess          no \n")
        file.write("set basisfile      undefined\n")
        file.write("set ecpfile        undefined\n")
        file.write("set basisspec      undefined\n")

        file.write("set root       " + self.get_name() + '\n')
        file.write('set chemsh_default_connectivity_toler ' + str(self.get_parameter('conn_toler')) + '\n')
        file.write('set chemsh_default_connectivity_scale ' + str(self.get_parameter('conn_scale')) + '\n')
        file.write("set c2_conn    " + str(self.get_parameter('export_connectivity')) + '\n')

        if self.get_parameter('use_active_region'):
            file.write("set active_atoms { ")
            active = self.get_parameter('active_atoms')
            for a in active:
                file.write(str(a.get_index()) + '\n')
            file.write(" } \n")
        else:
            file.write("set active_atoms           undefined\n")


        # Set the theory type ( Level of theory ) 
        if self.get_parameter('calctype') == 'QM/MM':

            file.write("set theory_type hybrid\n")
            file.write("# \n")
            file.write("# Hybrid calculation controls ------------------------------------\n")
            file.write("# \n")

            # Set QMMM coupling  
            self.save_parm(file,'coupling')

            if self.get_parameter('coupling') == 'embed':
                self.save_parm(file,'embed_r2');
                self.save_parm(file,'embed_r3');

            if self.get_parameter('use_qmmm_cutoff'):
                self.save_parm(file,'qmmm_cutoff')
            else:
                self.undef_parm(file,'qmmm_cutoff')

            self.save_parm(file,'dipole_adjust');

            file.write('set qm_region { ')

            active = self.get_parameter('qm_region')
            for a in active:
                file.write(str(a.get_index() + 1) + '\n')
            file.write(" } \n")

        elif self.get_parameter('calctype') == 'QM':
            file.write("set theory_type         qm\n")

        elif self.get_parameter('calctype') == 'MM':
            file.write("set theory_type         mm\n")

        if self.get_parameter('calctype') == 'QM/MM' or \
               self.get_parameter('calctype') == 'MM':

            file.write("# \n")
            file.write("# MM calculation controls ----------------------------------------\n")
            file.write("# \n")

            if self.get_parameter('mmcode') == 'dlpoly':

                file.write("set mm_theory           dl_poly\n")

##                if(!use_charmm && !strcmp(mm_def_file,"undefined")){
##                     msU_MSG_Display(msU_MSG_TEXTPORT, "ERRSTR_NO_MMDEFS", &status);
##                     msU_MSG_Display(msU_MSG_CONFIRM, "ERRSTR_NO_MMDEFS", &status);
##                     return -1;
##                 }

                file.write("# \n")
                file.write("# DL POLY Controls -----------------------------------------------\n")
                file.write("# \n")

                file.write("set from_quanta          " + str(self.mmcalc.get_parameter('from_quanta')) + '\n')
                file.write("set mm_defs              " + self.mmcalc.get_parameter('mm_defs')  + '\n')

                if self.mmcalc.get_parameter('from_quanta'):
                    file.write( "set scale14        {0.5, 1.0}\n")
                else:
                    file.write( "set scale14        {" + \
                                str(self.mmcalc.get_parameter('scale1')) + ' ' + \
                                str(self.mmcalc.get_parameter('scale4'))  + ' } \n')

                file.write("set exact_srf           " + str(self.mmcalc.get_parameter('use_exact_srf')) + '\n')
                file.write("set use_cutoff          " + str(self.mmcalc.get_parameter('use_cutoff'))  + '\n')
                if self.mmcalc.get_parameter('use_cutoff'):
                    file.write("set mm_cutoff                 " + str(self.mmcalc.get_parameter('pairlist_cutoff')) + '\n')
                else:
                    file.write("set mm_cutoff                 undefined\n")

                file.write("set use_pairlist        " + str(self.mmcalc.get_parameter('use_pairlist')) + '\n')

                file.write("set use_charmm           " + str(self.mmcalc.get_parameter('use_charmm')) + '\n')
                if self.mmcalc.get_parameter('use_charmm'):
                    file.write("set charmm_pdb_file      " + self.mmcalc.get_parameter('charmm_pdb_file') + '\n');
                    file.write("set charmm_psf_file      " + self.mmcalc.get_parameter('charmm_psf_file') + '\n');
                    file.write("set charmm_parm_file     " + self.mmcalc.get_parameter('charmm_parm_file') + '\n');
                    file.write("set charmm_mass_file     " + self.mmcalc.get_parameter('charmm_mass_file') + '\n');

            elif self.get_parameter('mmcode') == 'gulp':
                file.write("set mm_theory   gulp\n")

##       if(!strcmp(gulp_ff,"undefined")){
## 	msU_MSG_Display(msU_MSG_TEXTPORT, "ERRSTR_NO_GULPDEFS", &status);
## 	msU_MSG_Display(msU_MSG_CONFIRM, "ERRSTR_NO_GULPDEFS", &status);
## 	return -1;
##       }

##       if(gulp_atom_type && !strcmp(mm_def_file,"undefined")){
## 	msU_MSG_Display(msU_MSG_TEXTPORT, "ERRSTR_NO_MMDEFS", &status);
## 	msU_MSG_Display(msU_MSG_CONFIRM, "ERRSTR_NO_MMDEFS", &status);
## 	return -1;
##       }

##     file.write("# \n")
##     file.write("# GULP Controls -----------------------------------------------\n")
##     file.write("# \n")
##     file.write("gulp_ff                   ",gulp_ff);  
##     file.write("set add_shells               ",gulp_add_shells);  
##     file.write("set gulp_atom_type              ",gulp_atom_type);  
##   }

        elif self.get_parameter('mmcode') == 'charmm':
            file.write("set mm_theory          charmm\n")

        if self.get_parameter('calctype') == 'QM' or \
            self.get_parameter('calctype') == 'QM/MM':

            file.write("\n")
            file.write("# \n")
            file.write("# QM calculation controls ----------------------------------------\n")
            file.write("# \n")
            file.write("set mult                " + str(self.qmcalc.get_parameter("spin"))+'\n')
            file.write("set charge              " + str(self.qmcalc.get_parameter("charge"))+'\n')
            file.write("set qm_theory           " + self.get_parameter("qmcode") + '\n')

##     if self.qmcalc.get_parameter('basis_type') == BASTYP_LIB:
##       file.write("basisfile","undefined");
##       file.write("ecpfile","undefined");
##       file.write("basis","undefined");
##       /* Set the Basis set  */ 
##       switch (basis_set) {
##       case BS0:
## 	file.write("set basisspec {" + bas + "  all }");
##     case BASTYP_FIL:
##       file.write("basisspec","undefined");
##       file.write("basisfile",basis_file);
##       file.write("ecpfile",ecp_file);
##       file.write("basis","undefined");
##       break;
##     case BASTYP_KEY:
##       file.write("basisspec","undefined");
##       file.write("basisfile","undefined");
##       file.write("ecpfile","undefined");
##       file.write("basis",basis_key);
##       break;
##     }
##     /* file.write("basis",basis); */

            translate_hamiltonian = { 
               "AM1" : "am1", "PM3" : "pm3",
               "RHF" : "hf" , "UHF" : "hf",
               "Direct RHF" : "hf" , "Direct UHF" : "hf",
               "MP2" : "mp2" ,
               "B3LYP" : "b3lyp", "UB3LYP" : "b3lyp", 
               "BLYP": "blyp", "UBLYP" : "blyp",
               "SVWN" : "s-vwn", "USVWN" : "s-vwn", 
               "HCTH" : "hcth", "UHCTH" : "hcth",
               "FT97" : "ft97", "UFT97" : "ft97" }

            translate_hamiltonian2 = { 
               "AM1" : "rhf", "PM3" : "rhf" ,
               "RHF"   : "rhf", "UHF"    : "uhf",
               "Direct RHF" : "rhf" , "Direct UHF" : "uhf",
               "MP2"   : "rhf",
               "B3LYP" : "rhf", "UB3LYP" : "uhf", 
               "BLYP"  : "rhf", "UBLYP" : "uhf",
               "SVWN"  : "rhf", "USVWN" : "uhf", 
               "HCTH"  : "rhf", "UHCTH" : "uhf",
               "FT97"  : "rhf", "UFT97" : "uhf" }

            theory = self.qmcalc.get_theory()
            print 'Current theory', theory
            file.write("set hamiltonian         " + translate_hamiltonian[theory] + '\n')

##      set bas  self.qmcalc.get_input("basis")
##      file.write("set basisspec {" + bas + "  all }")

            temp = translate_hamiltonian2[theory]
            if self.qmcalc.get_parameter("spin") == 1:
                file.write("set scfwf              " + temp + '\n')
            else:
                if temp == "rhf":
                    file.write("set scfwf                 rohf\n")
                else:
                    file.write("set scfwf                 uhf\n")

            file.write("set qm_optstr            undefined \n")
            file.write("set qm_restart          " + str(self.qmcalc.get_parameter('restart'))+'\n')
            file.write("set qm_accuracy         " + str(self.qmcalc.get_parameter('accuracy'))+'\n')

        if self.get_parameter('calctype') == 'QM':
            self.write_qm_theory(file)
        elif self.get_parameter('calctype') == 'MM':
            if self.get_parameter('mmcode') == 'dlpoly':
                self.write_dl_poly(file)
            elif self.get_parameter('mmcode') == 'gulp':
                self.write_gulp(file)
        elif self.get_parameter('calctype') == 'QM/MM':
            if self.get_parameter('mmcode') == 'dlpoly':
                self.write_dl_poly(file)
            elif self.get_parameter('mmcode') == 'gulp':
                self.write_gulp(file)
            self.write_qm_theory(file)

            if self.get_parameter('coupling') == 'embed':
                self.write_embed(file)
            else:
                self.write_hybrid(file)
        self.write_save_final_structure(file)


        if self.get_parameter('task') == 'energy':

            file.write("set function            single_point_energy\n")
            self.write_energy(file)

        elif self.get_parameter('task') == 'dynamics':

            file.write("set function            dynamics\n")
            file.write("# \n")
            file.write("# Molecular Dynamics Controls ---------------------------------\n")
            file.write("# \n")
            file.write("set temperature           " + str(self.get_parameter('temp')) + '\n')
            file.write("set tstep                 " + str(self.get_parameter('tstep')) + '\n')
            file.write("set ensemble              " + self.get_parameter('ensemble') + '\n')
            file.write("set shake                 " + self.get_parameter('shake_option') + '\n')
            file.write("set max_dyn_step          " + str(self.get_parameter('max_dyn_step')) + '\n')
            file.write("set upd_freq              " + str(self.get_parameter('max_dyn_step')) + '\n')
            file.write("set traj_freq             " + str(self.get_parameter('traj_freq')) + '\n')
            file.write("set store_traj            " + str(self.get_parameter('store_traj')) + '\n')

            self.write_dynamics(file)

        elif self.get_parameter('task') == 'frequencies':

            file.write("set function               hessian\n")
            file.write("# \n")
            file.write("# Frequency Controls ---------------------------------\n")
            file.write("# \n")

            file.write("set act_arg \"\" \n")
            file.write("if { \"$active_atoms\" != \"undefined\" } { set act_arg \"active_atoms = [ list $active_atoms ] \"} \n")
            file.write("  \n")

            self.write_hess(file)

        elif self.get_parameter('task') == 'optimise':

            file.write("# \n")
            file.write("# Geometry Optimisation Controls ---------------------------------\n")
            file.write("# \n")
            file.write("set maxstep             " + str(self.get_parameter('max_opt_step')) + '\n')

            file.write('set newopt_method    ' + self.get_parameter('newopt_method') + '\n')
            file.write("set find_ts          " + str(self.get_parameter('find_ts')) + '\n' )
            file.write("set ts_mode          " + str(self.get_parameter('ts_mode')) + '\n')

            file.write("set act_arg \"\" \n")
            file.write("if { \"$active_atoms\" != \"undefined\" } { set act_arg \"active_atoms = [ list $active_atoms ] \"} \n")
            file.write("  \n")

            if self.get_parameter('optimiser') == 'newopt_c':

                file.write("set function               newopt\n")
                if self.get_parameter('find_ts') == 1:
                    self.write_newopt_ts(file)
                else:
                    self.write_newopt_min(file)

            elif self.get_parameter('optimiser') == 'newopt_z':

                file.write("set function            newopt\n")

                use_template_z = self.get_parameter('use_template_z')
                file.write("set use_template_z            " + str(use_template_z) + '\n')
                if use_template_z:
                    file.write("set template_z            " + template_z + '\n')

                if self.get_parameter('find_ts') == 1:
                    self.write_newopt_z_ts(file)
                else:
                    self.write_newopt_z_min(file)
            elif self.get_parameter('optimiser') == 'hdlcopt':


                file.write("set function            hdlcopt\n")

                map = { "Single Residue"      : 'single', \
                        "PDB Residues"        : 'pdb',  \
                        "Cartesian/Select"    : 'select_and_cartesian',\
                        "PDB Residues/Select" : 'select_and_pdb' }

                file.write("set residue_treatment       " + map[self.get_parameter('residue_treatment')] + '\n')
                file.write("set hdlc_region {\n")
                active = self.get_parameter('hdlc_region')
                for a in active:
                    file.write(str(a.get_index()) + '\n')
                file.write(" } \n")

                file.write("set hdlcopt_memory      " + str(self.get_parameter('hdlcopt_memory')) + '\n')

                ## Internal coordinate constraints
                file.write("set use_hdlc_constraints  " + str(self.get_parameter('use_hdlc_constraints')) + '\n')

            ##     if(use_hdlc_constraints){
            ##       file.write("set constraints {");
            ##       for(i=0;i<5;i++){
            ## 	switch(constraint_type[i]){
            ## 	case BOND:
            ## 	  file.write(" { bond %d %d %f} \n", constr[i][0],constr[i][1],constraint_value[i]);
            ## 	  break; 
            ## 	case ANGLE:
            ## 	  file.write(" { angle %d %d %d %f} \n", constr[i][0],constr[i][1],constr[i][2],
            ## 		  constraint_value[i]);
            ## 	  break;
            ## 	case TORSION:
            ## 	  file.write(" { torsion %d %d %d %d %f}\n", constr[i][0],constr[i][1],
            ## 		  constr[i][2],constr[i][3],
            ## 		  constraint_value[i]);
            ## 	  break;
            ## 	}
            ##       }
            ##       file.write("}\n");

                self.write_hdlcopt_update(file)

                if self.get_parameter('find_ts') == 1:
                    self.write_hdlcopt_ts(file)
                else:
                    self.write_hdlcopt_min(file)

##file.write("\n")
##file.write("# \n")
##file.write("# Atomic charges -------------------------------------------------\n")
##file.write("# \n")
##if(writecharges(fp,0)){

    def write_qm_theory(self,file):

        if self.get_parameter('qmcode') == 'mopac' or self.get_parameter('qmcode') == 'mndo' :
            file.write("set bas {} \n")
        else:
            basis = self.qmcalc.get_parameter("basis")
            if 0 and basis:
                # Use the result of the basis manager
                # for more details see the basis manager module
                # file.write('basis\n')
                for entry in basis:
                    (ass_type, tag, b) = entry
                    print 'entry', ass_type, tag, b
                    if ass_type == 'TYPE.KEY':
                        file.write('%s %s\n' % (b, tag))
                    if ass_type == 'TYPE.EXPL':
                        b.list()
                        for shell in b.shells:
                            file.write('%s %s\n' % (shell.type, tag))
                            for p in shell.expansion:
                                print 'expansion',p,len(p)
                                if len(p) == 2:
                                    file.write( '%12.8f %8.4f\n' % (p[1],p[0]))
                                elif len(p) == 3:

                                    file.write( '%12.8f %8.4f %8.4f\n' % (p[1],p[0],p[2]))
                                else:
                                    print 'ELSE'
                #file.write('end\n')
                file.write('set bas sto3g\n')
            else:
                # Use the default
                basis = self.qmcalc.get_parameter("default_basis")
                if len(basis.split()) > 1:
                    file.write('set bas \"basis= {' + basis+'}\"\n')
                else:
                    file.write('set bas \"basis = ' + basis+'\"\n')

            #file.write("set basis               " +self.qmcalc.get_parameter("basis") + '\n' )
            #file.write("set bas [list basis= $basis ecpfile=$ecpfile  basisfile=$basisfile basisspec = $basisspec ] \n")

        file.write("set newscf {} \n")
        file.write("# Uncomment here if you need to use the newscf module \n")
        file.write("# set newscf {  scf_keywords = { { newscf } { maxcyc 100 } {softfail} {end} } } \n")

        file.write("set qm_theory_args [ list $newscf \\\n")
        file.write("       hamiltonian = $hamiltonian listing = ${root}_${qm_theory}.log \\\n")
        file.write(" 	 accuracy = $qm_accuracy \\\n")
        file.write("       charge = $charge mult = $mult scftype = $scfwf $bas] \n")

        file.write("set maxcyc              " + str(self.qmcalc.get_parameter('scf_maxcyc'))+'\n')

        if self.get_parameter('qmcode') == 'gamess':
            file.write("set symmetry            " + str(self.qmcalc.get_parameter('symmetry'))+'\n')
            file.write("set direct_scf          " + str(self.qmcalc.check_direct())+'\n')
            file.write("set adaption            " + str(self.qmcalc.get_parameter('adaption'))+'\n')
            file.write("set gamess_args [list \\\n")
            file.write("          direct = $direct_scf \\\n")
            file.write("          symmetry = $symmetry \\\n")
            file.write(" 	       adaption = $adaption maxcyc=$maxcyc ] \n")
            file.write("lappend qm_theory_args $gamess_args  \n")
        elif self.get_parameter('qmcode') == 'mndo':
            file.write(" 	set optarg {} \n")
            file.write("         if { $qm_optstr != \"undefined\" } { set optarg \"optstr=$qm_optstr\" } \n")
            file.write("         set mndo_args [list idiis=$diis maxcyc=$maxcyc $optarg] \n")
            file.write("         lappend qm_theory_args $mndo_args  \n")
        elif self.get_parameter('qmcode') == 'mopac':
            file.write(" 	set optarg {} \n")
            file.write("         if { $qm_optstr != \"undefined\" } { set optarg \"optstr=$qm_optstr\" } \n")
            file.write("         lappend qm_theory_args \" \" \n")
        elif self.get_parameter('qmcode') == 'turbomole':
            file.write("set ri_memory      1000000 \n")
            file.write("set use_ri              " + str(self.qmcalc.get_parameter('use_ri'))+'\n')
            file.write("if { $use_ri } {  \n")
            file.write(" 	set use_ri \"use_ri=1 ri_memory=$ri_memory\"  \n")
            file.write("} else { \n")
            file.write("   set use_ri \"use_ri=0\" \n")
            file.write("} \n")
            file.write("set turbomole_args [list  scratchdir=$scratchdir jobname=$root $use_ri ] \n")
            file.write("lappend qm_theory_args $turbomole_args \n")
        elif self.get_parameter('qmcode') == 'gaussian':
            file.write("         # if { $ecpspec != \"\" } { set ecpspec  \"ecpspec=$ecpspec\" } \n")
            file.write("         switch $scfconv { \n")
            file.write(" 		undefined { switch $function { \n")
            file.write(" 	               		 single_point_energy { set scfmodekey SP } \n")
            file.write("                        		 default { set scfmodekey Tight } \n")
            file.write(" 			    }    \n")
            file.write("                           } \n")
            file.write("         	default { set scfmodekey \"Conver=$scfconv\" } \n")
            file.write("        } \n")
            file.write("        if { $scfconv != \"undefined\" && $maxcyc == 64 } { \n")
            file.write("           set scfkey \"scf=($scfmodekey,maxcycle=$maxcyc)\" \n")
            file.write("        } elseif { $scfconv == \"undefined\" && $maxcyc != 64 } { \n")
            file.write("           set scfkey \"scf=($scfmodekey,maxcycle=$maxcyc)\" \n")
            file.write("        } elseif { $scfconv != \"undefined\" && $maxcyc != 64 } { \n")
            file.write("           set scfkey \"scf=($scfmodekey,maxcycle=$maxcyc)\" \n")
            file.write("        } else { \n")
            file.write("          set scfkey \"scf=($scfmodekey,maxcycle=$maxcyc)\" \n")
            file.write("        } \n")
            file.write("    \n")
            file.write(" #	set gaussian_args [list jobname=$root g98_mem=$g98_mem basis=$basis \\\n")
            file.write(" #        $ecpspec guess=$guess $scfkey ] \n")
            file.write("  \n")
            file.write(" 	set gaussian_args [list jobname=$root g98_mem=$g98_mem basis=$basis \\\n")
            file.write("               guess=$guess $scfkey ] \n")
            file.write("  \n")
            file.write(" 	lappend qm_theory_args $gaussian_args \n")

        if self.get_parameter('calctype') == 'QM':
            file.write(" set theory $qm_theory \n")
            file.write(" set theory_args $qm_theory_args \n")

    def write_hybrid(self,file):
        file.write("# \n")
        file.write("# Set up control arguments for embedding scheme \n")
        file.write("#  \n")
        file.write(" \n")
        file.write("set theory hybrid \n")
        file.write(" \n")
        file.write("switch $qmmm_cutoff { \n")
        file.write("    undefined { set cut \"\" } \n")
        file.write("    default   { set cut \"cutoff=$qmmm_cutoff\" } \n")
        file.write("}	 \n")
        file.write(" \n")
        file.write("if { $use_charmm } { \n")
        file.write("    set ch \"atom_charges= [ list $charges ]\" \n")
        file.write("} else { \n")
        file.write("    set ch \" \" \n")
        file.write("} \n")
        file.write(" \n")
        file.write("set theory_args [ list qm_region= $qm_region \\\n")
        file.write("coupling  = $coupling \\\n")
        file.write("	conn = $root.c \\\n")
        file.write("	$cut \\\n")
        file.write("	dipole_adjust = $dipole_adjust \\\n")
        file.write("	$ch \\\n")
        file.write("	groups= $groups \\\n")
        file.write("	qm_theory = $qm_theory : [ list $qm_theory_args ] \\\n")
        file.write("	mm_theory = $mm_theory : [ list $mm_theory_args conn = ${root}.c ] ] \n")


    def write_embed(self,file):
        file.write("# ensure all connections are absent \n")
        file.write("\n")
        file.write("global chemsh_default_connectivity_toler  \n")
        file.write("global chemsh_default_connectivity_scale \n")
        file.write("set chemsh_default_connectivity_toler  0.0 \n")
        file.write("set chemsh_default_connectivity_scale  0.0 \n")
        file.write("\n")
        file.write("# \n")
        file.write("# Stick the shells back on again \n")
        file.write("# (not held by Cerius-2 GUI yet) \n")
        file.write("# \n")
        file.write("switch $add_shells { \n")
        file.write("     undefined {} \n")
        file.write("     default { \n")
        file.write("        add_shells  coords=${root}.c symbols= $add_shells  \n")
        file.write("     } \n")
        file.write("} \n")
        file.write("newgulp gulp save_charges=yes gulp_keywords= {qok} mm_defs= $gulp_ff coords= ${root}.c energy=etmp gradient=gtmp \n")
        file.write("\n")
        file.write("gulp init \n")
        file.write("gulp delete \n")
        file.write("\n")
        file.write("\n")
        file.write("# \n")
        file.write("# Label QM atoms with a suffix 1 \n")
        file.write("# If this already seems to have been done, we can skip the construct -regions \n")
        file.write("# phase \n")
        file.write("# \n")
        file.write("\n")
        file.write("set skip 0 \n")
        file.write("set digits {1 2 3 4 5} \n")
        file.write("foreach atom {1 2 3 4 5} { \n")
        file.write("    set entry [ get_atom_entry coords=${root}.c atom_number=$atom ] \n")
        file.write("    set label [lindex $entry 0 ] \n")
        file.write("    set len [ string length $label ] \n")
        file.write("    set char [ string index $label [ expr $len - 1 ] ] \n")
        file.write("    if { [ lsearch $digits $char ] != -1 } { \n")
        file.write("       set skip 1 \n")
        file.write("    } \n")
        file.write("} \n")
        file.write("\n")
        file.write("if { ! $skip } { \n")
        file.write("     # \n")
        file.write("     # Copy fragment \n")
        file.write("     # \n")
        file.write("     fragment ${root}.ctmp new volatile \n")
        file.write("     copy_object from=${root}.c to=${root}.ctmp type=fragment \n")
        file.write("\n")
        file.write("     foreach atom $qm_region { \n")
        file.write(" 	set entry [ get_atom_entry coords=${root}.ctmp atom_number=$atom ] \n")
        file.write(" 	set label [lindex $entry 0 ] \n")
        file.write(" 	set newlabel ${label}1 \n")
        file.write(" 	set entry [ concat $newlabel [ lrange $entry 1 3 ] ] \n")
        file.write(" 	replace_atom_entry atom_number=$atom  coords=${root}.ctmp atom_entry= $entry \n")
        file.write("     } \n")
        file.write("\n")
        file.write("     flush_object ${root}.ctmp \n")
        file.write("\n")
        file.write("     puts stdout \" exec construct7 -regions \\\n") 
        file.write(" 	-input ${root}.ctmp \\\n")
        file.write(" 	-output ${root}.c  \\\n")
        file.write(" 	-cut_off_2 $embed_r2 \\\n")
        file.write(" 	-cut_off_3 $embed_r3 \" \n")
        file.write("\n")
        file.write("     set out [ exec construct7 -regions \\\n")
        file.write(" 	-input ${root}.ctmp \\\n")
        file.write(" 	-output ${root}.c  \\\n")
        file.write(" 	-cut_off_2 $embed_r2 \\\n")
        file.write(" 	-cut_off_3 $embed_r3 ] \n")
        file.write("\n")
        file.write("     puts stdout $out \n")
        file.write("\n")
        file.write("     delete_object  ${root}.ctmp \n")
        file.write(" } else { \n")
        file.write("     puts stdout \"Skipping construct -regions, fragment is already labelled\" \n")
        file.write(" } \n")
        file.write("\n")
        file.write("# \n")
        file.write("# Now pick up the new settings \n")
        file.write("# \n")
        file.write("source gui.chm \n")
        file.write("\n")
        file.write("format_list  \"New qm region:\"    $qm_region \n")
        file.write("format_list  \"New active_atoms:\" $active_atoms \n")
        file.write("format_list  \"QM charge for zero charge:\" $qm_charge \n")
        file.write("\n")
        file.write("set charge [ expr int ($charge + $qm_charge) ] \n")
        file.write("\n")
        file.write("# redefine qm_theory_args for new charge \n")
        file.write("set qm_theory_args [ list hamiltonian = $hamiltonian \\\n")
        file.write("         charge = $charge mult = $mult scftype = $scfwf $bas] \n")
        file.write("\n")
        file.write("# \n")
        file.write("# and discard the charges from the GUI \n")
        file.write("# The charges are missing for shells, and  \n")
        file.write("# construct has deleted QM charges anyway \n")
        file.write("# \n")
        file.write("set atom_charges undefined \n")
        file.write("# \n")
        file.write("# Now use electrostatic embedding option \n")
        file.write("# \n")
        file.write("set coupling shift \n")
        file.write("\n")
        file.write("set theory hybrid \n")
        file.write("\n")
        file.write("switch $qmmm_cutoff { \n")
        file.write("    undefined { set cut \"\" } \n")
        file.write("     default  { set cut \"cutoff=$qmmm_cutoff\" } \n")
        file.write("}	 \n")
        file.write("\n")
        file.write("# \n")
        file.write("# Note that the charges are now taken from the structure in this case \n")
        file.write("# \n")
        file.write("set theory_args [ list qm_region= $qm_region \\\n")
        file.write(" 	coupling  = $coupling \\\n")
        file.write(" 	conn = $root.c \\\n")
        file.write(" 	$cut \\\n")
        file.write(" 	dipole_adjust = $dipole_adjust \\\n")
        file.write(" 	groups= $groups \\\n")
        file.write(" 	qm_theory = $qm_theory : [ list $qm_theory_args ] \\\n")
        file.write(" 	mm_theory = $mm_theory : [ list $mm_theory_args conn = ${root}.c ] ] \n")

    def write_dl_poly(self,file):
        file.write("  \n")

        rootdir = "/cygdrive/c/python_dev/ccp1gui"

        if self.mmcalc.get_parameter('forcefield') == "UFF":
            #
            # it should use the chemshell internal version
            #
            #file.write("set defs [ list mm_defs=%s forcefield=uff ] \n" % (rootdir + "/uff.dat"))
            file.write("set defs forcefield=uff \n")

        elif self.mmcalc.get_parameter('use_charmm'):

            if self.mmcalc.get_parameter('from_quanta'):
                file.write(" 	    # This is Muelheim specific \n")
                file.write(" 	    # Cerius replaces the CHM_DATA variable \n")
                file.write(" 	    #set charmm_mass_file  /usr/users/msi/quanta98/data/MASSES.RTF \n")

            file.write("\n")
            file.write(" 	if { ! [ file exists ${root}_charmm.chm ] } { \n")
            file.write("  \n")
            file.write(" 	    puts stdout \"Running Charmm to access forcefield data\" \n")

            if self.mmcalc.get_parameter('from_quanta'):
                file.write(" 		# \n")
                file.write(" 		# Simplest case, a standard script can be used \n")
                file.write(" 		#  \n")
                file.write(" 		catch {file delete quanta.pdb} \n")
                file.write(" 		catch {file delete quanta.psf} \n")
                file.write(" 		catch {file delete quanta.prm} \n")
                file.write(" 		catch {file delete quanta.rtf} \n")
                file.write("  \n")
                file.write(" 		exec ln -s $charmm_psf_file  quanta.psf \n")
                file.write(" 		exec ln -s $charmm_parm_file quanta.prm \n")
                file.write(" 		exec ln -s $charmm_pdb_file  quanta.pdb \n")
                file.write(" 		exec ln -s $charmm_mass_file quanta.rtf \n")
                file.write("  \n")
                file.write(" 		# exec ln -s $root.pdb quanta.crd \n")
                file.write(" 		#exec ln -s $env(CHM_DATA)/MASSES.RTF quanta.rtf  \n")
                file.write(" 		 \n")
                file.write(" 		charmm.preinit charmm_script= from_quanta.inp \\\n")
                file.write(" 			coords= ${root}_charmm.c \\\n")
                file.write("  \n")
                file.write(" 		catch {file delete quanta.pdb} \n")
                file.write(" 		catch {file delete quanta.psf} \n")
                file.write(" 		catch {file delete quanta.prm} \n")
                file.write(" 		catch {file delete quanta.rtf} \n")
                file.write("  \n")
            else:
                file.write(" 		#  \n")
                file.write(" 		# Academic charmm.. probably will have \n")
                file.write(" 		# a more complex script here \n")
                file.write(" 		# \n")
                file.write("  \n")
                file.write(" 		charmm.preinit charmm_script= ${root}.inp \\\n")
                file.write(" 			coords= ${root}_charmm.c \\\n")
                file.write("  \n")

            file.write(" 	    load_charmm_types2  $charmm_mass_file charmm_types \n")

            file.write("  \n")
            file.write(" 	    # These requires CTCL (i.e. charmm running) \n")
            file.write(" 	    set types   [ get_charmm_types ] \n")
            file.write(" 	    set charges [ get_charmm_charges ] \n")
            file.write(" 	    set groups  [ get_charmm_groups ] \n")
            file.write("  \n")
            file.write(" 	    # \n")
            file.write(" 	    # so we can skip charmm in future \n")
            file.write(" 	    # \n")
            file.write("  \n")
            file.write(" 	    set fp [ open ${root}_charmm.chm w] \n")
            file.write(" 	    puts $fp \"set types   [ list $types  ]\" \n")
            file.write(" 	    puts $fp \"set charges [ list $charges]\" \n")
            file.write(" 	    puts $fp \"set groups  [ list $groups ]\" \n")
            file.write(" 	    close $fp \n")
            file.write("  \n")
            file.write(" 	    # end charmm \n")
            file.write(" 	    charmm.shutdown \n")
            file.write("  \n")
            file.write(" 	    load_connect_from_psf ${root}_charmm.c $charmm_psf_file \n")
            file.write("  \n")
            file.write(" 	} else { \n")
            file.write("\n")
            file.write(" 	    puts stdout \"Loading CHARMM data from  ${root}_charmm.chm\" \n")
            file.write("\n")
            file.write(" 	    source ${root}_charmm.chm \n")
            file.write("\n")
            file.write(" 	    load_connect_from_psf ${root}.c $charmm_psf_file \n")
            file.write("} \n")
            file.write("\n")
            file.write(" 	# This will ensure that subsequent PDB writes have  \n")
            file.write(" 	# full residue information \n")
            file.write("\n")
            file.write("\n")
            file.write(" 	read_pdb file = ${root}.pdb  \n")

            file.write("\n")
            file.write(" 	switch  $theory_type { \n")
            file.write(" 	    hybrid  { set ch \"\" } \n")
            file.write(" 	    default { set ch \"atom_charges = [list $charges ]\" } \n")
            file.write(" 	} \n")
            file.write("\n")
            file.write(" 	set defs [ list charmm_psf_file=$charmm_psf_file \\\n")
            file.write(" 		charmm_parameter_file = $charmm_parm_file \\\n")
            file.write(" 		charmm_mass_file = $charmm_mass_file \\\n")
            file.write(" 		$ch \\\n")
            file.write(" 		save_charges=yes \\\n")
            file.write(" 		atom_types= $types \\\n")
            file.write(" 		use_charmm_psf=yes \\\n")
            file.write(" 		]		 \n")
            file.write("\n")
            file.write("# Maybe load connectivity from PSF here \n")

        else:
            file.write(" 	set defs [ list mm_defs = $mm_defs ] \n")


        file.write("# Note verbosity reduced  \n")
        file.write("\n")
        file.write("switch $mm_cutoff { \n")
        file.write("     undefined { set cut \"\" } \n")
        file.write("     default  { set cut \"cutoff=$mm_cutoff\" } \n")
        file.write("}	 \n")
        file.write("\n")
        file.write("\n")
        file.write("switch  $theory_type { \n")
        file.write("     hybrid { set temp mxexcl=$mxexcl } \n")
        file.write("     default { set temp {} } \n")
        file.write("}\n")
        file.write("\n")
        file.write("# \n")
        file.write("# conn=$job.c is generally redundnant, but useful if we are  \n")
        file.write("# working with internal coordinates, or if  \n")
        file.write("#  \n")
        file.write("\n")
        file.write("set mm_theory_args [ list \\\n")
        # additional connectivity parameter if we are generating a zmatrix
        if self.get_parameter('optimiser') == 'newopt_z':
            file.write("     conn = ${root}.c \\\n")
        file.write(" 	scale14 = $scale14 \\\n")
        file.write(" 	exact_srf = $exact_srf \\\n")
        file.write(" 	use_pairlist = $use_pairlist \\\n")
        file.write(" 	list_option=$mm_list_option \\\n")
        file.write(" 	$cut $temp\\\n")
        file.write(" 	mxlist=$mxlist \\\n")
        file.write(" 	$defs ] \n")
        file.write("\n")
        file.write("#puts stdout \"Args to dl_poly $mm_theory_args\" \n")
        file.write("\n")
        file.write("# these will be overwritten in the hybrid cases \n")
        file.write("set theory $mm_theory \n")
        file.write("set theory_args $mm_theory_args \n")

    def write_gulp(self,file) :
        file.write("\n")
        file.write("set defs \"mm_defs=$gulp_ff unique_listing=yes\" \n")
        file.write("\n")
        file.write("if { \"$add_shells\" != \"undefined\" } { \n")
        file.write("     add_shells coords=${root}.c symbols= [ list $add_shells  ] \n")
        file.write("} \n")
        file.write("\n")
        file.write("switch $gulp_atom_type { \n")
        file.write("     1 { \n")
        file.write(" 	# \n")
        file.write(" 	#Explicitly type atoms using DL_POLY atom type engine \n")
        file.write(" 	# \n")
        file.write("\n")
        file.write(" 	set code [  dl_poly.init assign_only=yes \\\n")
        file.write(" 		mm_defs=$mm_defs \\\n")
        file.write(" 		coords=${root}.c \\\n")
        file.write(" 		export_type_list=types ] \n")
        file.write("\n")
        file.write(" 	puts stdout \"Types for gulp: $types\" \n")
        file.write(" 	set mm_theory_args  [ list $defs atom_types = $types ] \n")
        file.write("     } \n")
        file.write("\n")
        file.write("     0 { \n")
        file.write(" 	set mm_theory_args  [ list $defs ] \n")
        file.write("     } \n")
        file.write("} \n")
        file.write("\n")
        file.write("# these will be overwritten in the hybrid cases \n")
        file.write("set theory $mm_theory \n")
        file.write("set theory_args $mm_theory_args \n")

    def write_energy(self,file) :
        file.write("\n")
        file.write("energy coords=${root}.c \\\n")
        file.write("	energy=${root}.e \\\n")
        file.write("	theory = $theory : [ list $theory_args ] \n")
        file.write("\n")
        file.write("push_banner_flag 0 \n")
        file.write("puts stdout \"Energy from $theory = [ get_matrix_element matrix=${root}.e format=%f indices= {0 0} ] Hartrees\" \n")
        file.write("pop_banner_flag \n")
        file.write("\n")
        # Overwrite input structure 
        file.write("save_punch ${root} ${root}.c \n")


    def write_newopt_min(self,file):
        file.write("newopt maxstep=$maxstep method=$newopt_method \\\n")
        file.write(" 	function=copt : [ list $act_arg coords=${root}.c \\\n")
        file.write(" 	theory = $theory : [ list $theory_args ] ] \n")
        file.write("  \n")
        file.write("# \n")
        file.write("# Save resulting structre \n")
        file.write("# \n")
        # Overwrite input structure 
        file.write("save_punch ${root} copt.result   \n")
        # PDB for future jobs
        file.write("save_pdb ${root}_opt copt.result   \n")

    def write_newopt_ts(self,file):
        file.write(" # \n")
        file.write(" hessian \\\n")
        file.write(" 	function=copt : [ list $act_arg coords=${root}.c \\\n")
        file.write(" 	theory = $theory : [ list $theory_args ] ] hessian= ${root}.h  \n")
        file.write("  \n")
        file.write(" newopt maxstep=$maxstep \\\n")
        file.write(" 	method=baker \\\n")
        file.write(" 	input_hessian= ${root}.h \\\n")
        file.write(" 	follow_mode = $ts_mode \\\n")
        file.write(" 	function=copt : [ list $act_arg coords=${root}.c \\\n")
        file.write(" 	theory = $theory : [ list $theory_args ] ] \n")
        file.write("  \n")
        # Overwrite input structure 
        file.write("save_punch ${root} copt.result   \n")
        # PDB for future jobs
        file.write("save_pdb ${root}_opt copt.result   \n")


    def write_newopt_z_min(self,file):
        file.write(" # \n")
        file.write(" newopt maxstep=$maxstep method=$newopt_method \\\n")
        file.write(" 	function=zopt : [ list zmatrix=${root}.z \\\n")
        file.write(" 	theory = $theory : [ list $theory_args ] ] \n")
        file.write(" # \n")
        file.write(" # Save resulting structure \n")
        file.write(" # \n")
        file.write(" z_to_c zmatrix= zopt.result coords= ${root}_opt.c \n")
        # Overwrite input structure 
        file.write("save_punch ${root} ${root}_opt.c  \n")
        # PDB for future jobs
        file.write("save_pdb ${root}_opt ${root}_opt.c   \n")


    def write_newopt_z_ts(self,file):
        file.write("# \n")
        file.write("# method=$newopt_method  \n")
        file.write("# \n")
        file.write("hessian function=zopt : [ list zmatrix=${root}.z  \\\n")
        file.write(" 	theory = $theory : [ list $theory_args ] ] hessian= ${root}.h \n")
        file.write("\n")
        file.write("newopt maxstep=$maxstep method=baker \\\n")
        file.write(" 	function=zopt : [ list zmatrix=${root}.z \\\n")
        file.write(" 	theory = $theory : [ list $theory_args ] ] \\\n")
        file.write("         follow_mode = $ts_mode input_hessian= ${root}.h \n")
        file.write("# \n")
        file.write("# Save resulting structure \n")
        file.write("# \n")
        file.write("z_to_c zmatrix= zopt.result coords= ${root}_opt.c \n")
        file.write("# \n")
        # Overwrite input structure 
        file.write("save_punch ${root} ${root}_opt.c  \n")
        # PDB for future jobs
        file.write("save_pdb ${root}_opt ${root}_opt.c   \n")


    def write_hdlcopt_min(self,file):
        file.write("# \n")
        file.write("# Geometry optimisation using HDLCOpt \n")
        file.write("# \n")
        file.write("# Input parameters \n")
        file.write("#  root : name of root structure \n")
        file.write("#  use_hdlc_constraints, contraints \n")
        file.write("#  residue_treatment \n")
        file.write("#  charmm_pdb_file (only when residue treatment is pdb or select_and_pdb ) \n")
        file.write("#\n")
        file.write("\n")
        file.write("proc hdlcopt_update { args } { \n")
        file.write("\n")
        file.write("     global root \n")
        file.write("     global theory_type \n")
        file.write("     global qm_theory \n")
        file.write("\n")
        file.write("     parsearg update { coords } $args \n")
        file.write("     write_xyz coords=$coords file=update_${root}.xyz \n")
        file.write("\n")
        file.write("     switch  $theory_type { \n")
        file.write(" 	hybrid { \n")
        file.write(" 	    write_xyz coords=hybrid.${qm_theory}.coords file=ttt \n")
        file.write(" 	    exec cat ttt >> qm_trajectory.xyz \n")
        file.write(" 	    catch {file delete ttt} \n")
        file.write(" 	    copy_object type=fragment from=hybrid.${qm_theory}.coords to=ttt \n")
        file.write(" 	    exec cat ttt >> qm_trajectory.coo \n")
        file.write(" 	    catch {file delete ttt} \n")
        file.write(" 	} \n")
        file.write("     } \n")
        file.write("  \n")
        file.write("      end_module \n")
        file.write(" } \n")
        file.write("\n")
        file.write("\n")
        file.write(" if { $use_hdlc_constraints } {  \n")
        file.write("\n")
        file.write("     foreach constr $constraints { \n")
        file.write(" 	switch [ lindex $constr 0 ] { \n")
        file.write(" 	    bond {lappend tt [ lrange $constr 0 2] } \n")
        file.write(" 	    angle { lappend tt [ lrange $constr 0 3] } \n")
        file.write(" 	    torsion  {lappend tt [ lrange $constr 0 4] } \n")
        file.write(" 	} \n")
        file.write("     } \n")
        file.write("     set cons_internals \"constraints = [ list $tt ]\" \n")
        file.write("} else { \n")
        file.write("     set cons_internals \"\" \n")
        file.write("} \n")
        file.write("\n")
        file.write("\n")
        file.write("set reghdl $hdlcopt_memory   \n")
        file.write("\n")
        file.write("if { [ get_number_of_atoms coords=${root}.c ] > 1000 } {  \n")
        file.write("     set cfact 0.5 \n")
        file.write("} else { \n")
        file.write("     set cfact 0.0 \n")
        file.write("}   \n")
        file.write("\n")
        file.write("switch $residue_treatment { \n")
        file.write("     pdb { \n")
        file.write(" 	set res [ pdb_to_res \"$charmm_pdb_file\"  ] \n")
        file.write("     } \n")
        file.write("     single { \n")
        file.write(" 	set res [ res_selectall coords=${root}.c ] \n")
        file.write("     } \n")
        file.write("     select_and_cartesian { \n")
        file.write(" 	set res [ list core [list $hdlc_region ] ] \n")
        file.write(" 	puts stdout \"Residues : $res\" \n")
        file.write("\n")
        file.write("     } \n")
        file.write("     select_and_pdb { \n")
        file.write("\n")
        file.write(" 	# \n")
        file.write(" 	#  Combine HDLC core from GUI and  \n")
        file.write(" 	#  residues from PDB \n")
        file.write(" 	#  Here core residue is not significant \n")
        file.write(" 	 \n")
        file.write(" 	set res [ pdb_to_res $charmm_pdb_file  ] \n")
        file.write("\n")
        file.write(" 	set r_names [ lindex $res 0 ] \n")
        file.write(" 	set r_data  [ lindex $res 1 ] \n")
        file.write("\n")
        file.write(" 	catch {unset new_data} \n")
        file.write(" 	catch {unset new_names} \n")
        file.write("\n")
        file.write(" 	for { set res 0 } { $res < [ llength $r_names ] } { incr res 1 } { \n")
        file.write("\n")
        file.write(" 	    set name [ lindex $r_names $res ] \n")
        file.write(" 	    set data [ lindex $r_data $res ] \n")
        file.write(" 	     \n")
        file.write(" 	    set temp {} \n")
        file.write(" 	    foreach entry $data { \n")
        file.write(" 		if { [ lsearch $hdlc_region $entry ] == -1 } {  lappend temp $entry } \n")
        file.write(" 	    } \n")
        file.write("\n")
        file.write(" 	    switch [ llength $temp ] { \n")
        file.write(" 		0 - 1 - 2 { \n")
        file.write(" 		    # the remainder (moving part) is to small to be  \n")
        file.write(" 		    # optimised as a DLC residue, by removing the atoms \n")
        file.write(" 		    # it will be treated as cartesian  \n")
        file.write(" 		} \n")
        file.write("\n")
        file.write(" 		default { \n")
        file.write(" 		    lappend new_data  $temp \n")
        file.write(" 		    lappend new_names $name \n")
        file.write(" 		} \n")
        file.write(" 	    } \n")
        file.write(" 	} \n")
        file.write("\n")
        file.write(" 	set res [ list $new_names $new_data ] \n")
        file.write(" 	 \n")
        file.write(" 	set r_core    [ list core [ list  $hdlc_region ] ] \n")
        file.write(" 	set res  [ inlist function=merge residues= $res residues2= $r_core ] \n")
        file.write(" 	set core_atoms $hdlc_region   \n")
        file.write("\n")
        file.write(" 	set core \"core= [list $core_atoms] \" \n")
        file.write("\n")
        file.write(" 	puts stdout \"Final residue list: $res\" \n")
        file.write("     } \n")
        file.write("} \n")
        file.write("\n")
        file.write("# puts stdout [ list hdlcopt residues= $res  \\\n")
        file.write(" 	memory=$hdlcopt_memory reghdl=$reghdl cfact=$cfact $act_arg $cons_internals \\\n")
        file.write(" 	coords=${root}.c \\\n")
        file.write(" 	result=${root}.optimised \\\n")
        file.write(" 	maxfun=$maxstep \\\n")
        file.write(" 	update_procedure=hdlcopt_update \\\n")
        file.write(" 	theory = $theory : [ list $theory_args ] ] \n")
        file.write("\n")
        file.write("hdlcopt residues= $res  \\\n")
        file.write(" 	memory=$hdlcopt_memory reghdl=$reghdl cfact=$cfact $act_arg $cons_internals \\\n")
        file.write(" 	coords=${root}.c \\\n")
        file.write(" 	result=${root}.optimised \\\n")
        file.write(" 	update_procedure=hdlcopt_update \\\n")
        file.write(" 	maxfun=$maxstep \\\n")
        file.write(" 	theory = $theory : [ list $theory_args ] \n")
        file.write("\n")
        # Overwrite input structure 
        file.write("save_punch ${root} ${root}.optimised   \n")
        # PDB for future jobs
        file.write("save_pdb ${root}_opt ${root}.optimised   \n")


    def write_hdlcopt_ts(self,file) :
        file.write(" #\n")
        file.write(" #Control parameters \n")
        file.write(" #\n")
        file.write(" #  theory theory_args :  \n")
        file.write(" #  root \n")
        file.write(" #  residue_treatment \n")
        file.write(" #  charmm_pdb_file (only when residue treatment is  ) \n")
        file.write(" # \n")
        file.write("\n")
        file.write("if { $use_hdlc_constraints } {  \n")
        file.write("     foreach constr $constraints { \n")
        file.write(" 	switch [ lindex $constr 0 ] { \n")
        file.write(" 	    bond {lappend tt [ lrange $constr 0 2] } \n")
        file.write(" 	    angle { lappend tt [ lrange $constr 0 3] } \n")
        file.write(" 	    torsion  {lappend tt [ lrange $constr 0 4] } \n")
        file.write(" 	} \n")
        file.write("     } \n")
        file.write("     set cons_internals \"constraints = [ list $tt ] \" \n")
        file.write("} else { \n")
        file.write("    set cons_internals \"\" \n")
        file.write("} \n")
        file.write("\n")
        file.write("#set reghdl $hdlcopt_memory \n")
        file.write("set reghdl 0 \n")
        file.write("\n")
        file.write("if { [ get_number_of_atoms coords=${root}.c ] > 1000 } {  \n")
        file.write("     set cfact 0.5 \n")
        file.write("} else { \n")
        file.write("     set cfact 0.0 \n")
        file.write("}   \n")
        file.write("\n")
        file.write("if { \"$contyp\" == \"undefined\"  } { set contyp  0 }	 \n")
        file.write("if { \"$ctfirst\" == \"undefined\" } { set ctfirst 1 } \n")
        file.write("if { \"$recalc\" == \"undefined\"  } { set recalc  0 } \n")
        file.write("\n")
        file.write("switch $residue_treatment { \n")
        file.write("\n")
        file.write("     single { \n")
        file.write(" 	set res [ res_selectall coords=${root}.c ] \n")
        file.write(" 	set core_atoms [ lindex [ lindex $res 1 ] 0 ] \n")
        file.write("     } \n")
        file.write("     pdb { \n")
        file.write(" 	set res [ pdb_to_res $charmm_pdb_file  ] \n")
        file.write(" 	# Residue of interest is assumed to be first \n")
        file.write(" 	puts stdout \"Warning ... Assume core is 1st residue\" \n")
        file.write(" 	set core_atoms [ lindex [ lindex $res 0 ] 0 ]  \n")
        file.write("     } \n")
        file.write("     select_and_cartesian { \n")
        file.write(" 	set res [ list core [list $hdlc_region ] ] \n")
        file.write(" 	set core_atoms [ lindex [ lindex $res 0 ] 0 ] \n")
        file.write("     } \n")
        file.write("     select_and_pdb { \n")
        file.write(" 	# \n")
        file.write(" 	#  Combine HDLC core from GUI and  \n")
        file.write(" 	#  residues from PDB \n")
        file.write(" 	# \n")
        file.write(" 	set res [ pdb_to_res $charmm_pdb_file  ] \n")
        file.write("\n")
        file.write(" 	set r_names [ lindex $res 0 ] \n")
        file.write(" 	set r_data  [ lindex $res 1 ] \n")
        file.write("\n")
        file.write(" 	catch {unset new_data} \n")
        file.write(" 	catch {unset new_names} \n")
        file.write("\n")
        file.write(" 	for { set res 0 } { $res < [ llength $r_names ] } { incr res 1 } { \n")
        file.write("\n")
        file.write(" 	    set name [ lindex $r_names $res ] \n")
        file.write(" 	    set data [ lindex $r_data $res ] \n")
        file.write(" 	     \n")
        file.write(" 	    set temp {} \n")
        file.write(" 	    foreach entry $data { \n")
        file.write(" 		if { [ lsearch $hdlc_region $entry ] == -1 } {  lappend temp $entry } \n")
        file.write(" 	    } \n")
        file.write("\n")
        file.write(" 	    switch [ llength $temp ] { \n")
        file.write(" 		0 - 1 - 2 { \n")
        file.write(" 		    # the remainder (moving part) is to small to be  \n")
        file.write(" 		    # optimised as a DLC residue, by removing the atoms \n")
        file.write(" 		    # it will be treated as cartesian  \n")
        file.write(" 		} \n")
        file.write("\n")
        file.write(" 		default { \n")
        file.write(" 		    lappend new_data  $temp \n")
        file.write(" 		    lappend new_names $name \n")
        file.write(" 		} \n")
        file.write(" 	    } \n")
        file.write(" 	} \n")
        file.write("\n")
        file.write(" 	set res [ list $new_names $new_data ] \n")
        file.write(" 	 \n")
        file.write(" 	set r_core    [ list core [ list  $hdlc_region ] ] \n")
        file.write(" 	set res  [ inlist function=merge residues= $res residues2= $r_core ] \n")
        file.write(" 	set core_atoms $hdlc_region   \n")
        file.write(" 	# puts stdout \"Final residue list: $res\" \n")
        file.write("     } \n")
        file.write("} \n")
        file.write("\n")
        file.write("set core \"core= [list $core_atoms] \" \n")
        file.write("set nvar [ expr 3 * [ llength $core_atoms  ] ] \n")
        file.write("\n")
        file.write("# TODO - allow mode choice \n")
        file.write("\n")
        file.write("# puts stdout [ list  lockon=$ts_mode residues= $res  nvar= $nvar $core  \\\n")
        file.write(" 	recalc=$recalc contyp=$contyp \\\n")
        file.write(" 	ctfirst=$ctfirst \\\n")
        file.write(" 	memory=$hdlcopt_memory \\\n")
        file.write(" 	reghdl=$reghdl \\\n")
        file.write(" 	cfact=$cfact \\\n")
        file.write(" 	$act_arg $cons_internals \\\n")
        file.write(" 	coords=${root}.c \\\n")
        file.write(" 	result=${root}.ts.optimised \\\n")
        file.write(" 	maxfun=$maxstep \\\n")
        file.write(" 	update_procedure=hdlcopt_update \\\n")
        file.write(" 	theory = $theory : [ list $theory_args ] ] \n")
        file.write("\n")
        file.write("\n")
        file.write("hdlcopt lockon=$ts_mode residues= $res  nvar= $nvar $core  \\\n")
        file.write(" 	recalc=$recalc contyp=$contyp \\\n")
        file.write(" 	ctfirst=$ctfirst \\\n")
        file.write(" 	memory=$hdlcopt_memory \\\n")
        file.write(" 	reghdl=$reghdl \\\n")
        file.write(" 	cfact=$cfact \\\n")
        file.write(" 	$act_arg $cons_internals \\\n")
        file.write(" 	coords=${root}.c \\\n")
        file.write(" 	maxfun=$maxstep \\\n")
        file.write(" 	result=${root}.ts.optimised \\\n")
        file.write(" 	update_procedure=hdlcopt_update \\\n")
        file.write(" 	theory = $theory : [ list $theory_args ] \n")
        file.write("\n")
        # Overwrite input structure 
        file.write("save_punch ${root} ${root}.ts.optimised   \n")
        # PDB for future jobs
        file.write("save_pdb ${root}_ts ${root}.ts.optimised   \n")

    def write_hdlcopt_update(self,file):
        file.write("proc hdlcopt_update { args } { \n")
        file.write("     global root \n")
        file.write("     global theory_type \n")
        file.write("     global qm_theory \n")
        file.write("     parsearg update { coords } $args \n")
        file.write("     write_xyz coords=$coords file=update_${root}.xyz \n")
        file.write("     switch  $theory_type { \n")
        file.write(" 	hybrid { \n")
        file.write(" 	    write_xyz coords=hybrid.${qm_theory}.coords file=ttt \n")
        file.write(" 	    exec cat ttt >> qm_trajectory.xyz \n")
        file.write(" 	    catch {file delete ttt} \n")
        file.write(" 	    copy_object type=fragment from=hybrid.${qm_theory}.coords to=ttt \n")
        file.write(" 	    exec cat ttt >> qm_trajectory.coo \n")
        file.write(" 	    catch {file delete ttt} \n")
        file.write(" 	} \n")
        file.write("     } \n")
        file.write("     end_module \n")
        file.write("} \n")

    def write_hess(self,file):
        file.write("\n")
        file.write("force hessian=${root}.h \\\n")
        file.write(" 	$act_arg coords=${root}.c \\\n")
        file.write(" 	theory = $theory : [ list $theory_args ] \n")
        file.write("# \n")
        file.write("# Save resulting punchfile and normal modes \n")
        file.write("# \n")
        file.write("exec cp force.pun ${root}.pun \n")


    def write_hess_z(self,file):
        file.write("# \n")
        file.write("hessian hessian=${root}\\\n")
        file.write(" 	function=zopt : [ list zmatrix=${root}.z \\\n")
        file.write(" 	theory = $theory : [ list $theory_args ] ] \n")
        file.write("# \n")
        file.write("# Save resulting structure \n")
        file.write("# \n")
        file.write("#z_to_c zmatrix= zopt.result coords= ${root}_opt.c \n")
        file.write("#save_punch ${root}_opt ${root}_opt.c \n")


    def write_dynamics(self,file):
        file.write("\n")
        file.write("set con  \" \" \n")
        file.write("set grps \" \" \n")
        file.write("set rgd  \" \" \n")
        file.write("set shake_h  \" \" \n")
        file.write("\n")
        file.write("switch $shake { \n")
        file.write("    undefined {} \n")
        file.write("    default { set shake_h \"shake_h=$shake\" } \n")
        file.write("} \n")
        file.write("\n")
        file.write("puts stdout \" dyn1 coords=${root}.c \\\n")
        file.write(" 	theory= $theory : [ list $theory_args ] \\\n")
        file.write(" 	temperature = $temperature \\\n")
        file.write(" 	timestep = $tstep \\\n")
        file.write(" 	$con $grps $rgd $shake_h \\\n")
        file.write(" 	ensemble = $ensemble \" \n")
        file.write("\n")
        file.write("dynamics dyn1 coords=${root}.c \\\n")
        file.write(" 	theory= $theory : [ list $theory_args ] \\\n")
        file.write(" 	temperature = $temperature \\\n")
        file.write(" 	timestep = $tstep \\\n")
        file.write(" 	$con $grps $rgd $shake_h\\\n")
        file.write(" 	ensemble = $ensemble \\\n")
        file.write("\n")
        file.write("\n")
        file.write("# Initialise random velocities \n")
        file.write("dyn1 initvel \n")
        file.write("\n")
        file.write("# Need to add equilibration period \n")
        file.write("\n")
        file.write("set count 0 \n")
        file.write("\n")
        file.write("while {$count < $max_dyn_step } { \n")
        file.write("  \n")
        file.write("     if { ! [ expr $count % $upd_freq ] } { \n")
        file.write(" 	dyn1 update \n")
        file.write("     } \n")
        file.write("  \n")
        file.write("     dyn1 force \n")
        file.write("     if { $store_traj } {  \n")
        file.write(" 	if { ! [ expr $count % $traj_freq ] } { \n")
        file.write(" 	    copy_object from=dyn1.tempc to=FRAME type=fragment \n")
        file.write(" 	    set fp [ open FRAME.stamp w ]  \n")
        file.write(" 	    close $fp\n")
        file.write(" 	    dyn1 trajectory  \n")
        file.write(" 	} \n")
        file.write("     } \n")
        file.write("     dyn1 step \n")
        file.write("     dyn1 printe \"kcal mol-1\" \n")
        file.write("  \n")
        file.write("     incr count \n")
        file.write("} \n")
        file.write("\n")
        file.write("save_punch $root dyn1.tempc \n")
        file.write("\n")
        file.write("dyn1 dump \n")
        file.write("dyn1 destroy \n")
        file.write("\n")


    def write_save_final_structure(self,file):
        file.write("proc save_pdb {root coords} { \n")
        file.write("   # \n")
        file.write("   # Save resulting PDB file \n")
        file.write("   # \n")
        file.write("   push_banner_flag 0 \n")
        file.write("   puts stdout \"Structure saved as ${root}.pdb\" \n")
        file.write("   write_pdb file=${root}.pdb coords=${coords} \n")
        file.write("\n")
        file.write("   if { [ llength [ get_cell coords=${coords} ] ] == 9 } { \n")
        file.write(" 	puts stdout \"Structure saved as ${root}.xtl\" \n")
        file.write(" 	write_xtl file=${root}.xtl coords=${coords} \n")
        file.write("    } else { \n")
        file.write("  	puts stdout \"Structure saved as ${root}.msi\" \n")
        file.write(" 	write_msi file=${root}.msi coords=${coords} \n")
        file.write("     } \n")
        file.write("} \n")
        file.write("proc save_punch {root coords} { \n")
        file.write("   # \n")
        file.write("   # Save resulting punch format file \n")
        file.write("   # \n")
        file.write("   push_banner_flag 0 \n")
        file.write("   puts stdout \"Structure saved as ${root}.pun\" \n")
        file.write("   copy_object type=fragment from=$coords to=$root.pun\n")
        file.write("   pop_banner_flag 0 \n")
        file.write("}\n")


    def save_parm(self,file,tag):
        """ write out the Tcl statment to set the relevant variable"""
        file.write("set "  + tag + '            ' + str(self.get_parameter(tag)) + '\n')

    def undef_parm(self,file,tag):
        """ write out the Tcl statment to set the relevant variable to "undefined" """
        file.write("set "  + tag + '             undefined \n')

homolumoa = 0

class ChemShellCalcEd(CalcEd):

    def __init__(self,root,calc,graph,**kw):

        apply(CalcEd.__init__, (self,root,calc,graph), kw)

        self.qmeditor = None
        self.mmeditor = None

        self.CreateCalcMenu(self.menu)
        self.CreateEditMenu(self.menu)
        self.CreateViewMenu(self.menu)
        
        # Task
        valid_tasks = [ 'energy', 'optimise', 'frequencies', 'dynamics' ]
        self.task_tool = SelectOptionTool(self,"task","Job Type",valid_tasks)
        items = [ "QM", "MM", "QM/MM" ] 
        self.calctype_tool = SelectOptionTool(
            self,"calctype","Calculation Type",items,command=self.__set_calctype)

        valid_qm_codes = [ "gamess", "gaussian", "mndo", "mopac" ]
        self.qmcode_tool = SelectOptionTool(self,"qmcode","QM Code",valid_qm_codes)
        valid_mm_codes = [ "dlpoly" , "gulp", "charmm" ]
        self.mmcode_tool = SelectOptionTool(self,"mmcode","MM Code",valid_mm_codes)
        # editqm, editmm see below

        # Coupling
        #connectivity group
        self.export_connectivity_tool = BooleanTool(self,"export_connectivity","Export Connectivity")
        self.conn_scale_tool = FloatTool(self,"conn_scale","Scale Factor")
        self.conn_toler_tool = FloatTool(self,"conn_toler","Tolerance")

        self.use_qmmm_cutoff_tool = BooleanTool(self,"use_qmmm_cutoff","Use QM/MM cutoff")
        self.qmmm_cutoff_tool = FloatTool(self,"qmmm_cutoff","QM/MM cutoff")

        self.dipole_adjust_tool = BooleanTool(self,"dipole_adjust","Dipole Adjust")
        valid_couplings = [ 'mechanical', 'shift', 'L0', 'L1', 'L2', 'aca', 'mechanical_aca', 'subtractive', 'embed' ]
        self.coupling_tool = SelectOptionTool(self,"coupling","QM/MM Coupling", valid_couplings)
        self.qm_region_tool=AtomSelectionTool(self,"qm_region","QM Region")

        # Geometry Optimisation oage
        options = [ 'newopt_c', 'newopt_z', 'hdlcopt' ]
        self.optimiser_tool = SelectOptionTool(self,"optimiser","Optimiser",options)
        options = [ 'descent', 'bfgs', 'bfgs2', 'conmin', 'diis' ]
        self.newopt_method_tool = SelectOptionTool(self,"newopt_method","NewOpt Method",options)
        self.max_opt_step_tool = IntegerTool(self,"max_opt_step","# Optimiser step",min=0)
        self.find_ts_tool = IntegerAndBooleanTool(self,"find_ts","ts_mode","Find TS","TS Mode",min=1)
        self.active_atoms_tool=AtomSelectionTool(self,"active_atoms","Active Atoms")
        self.use_active_region_tool=BooleanTool(self,"use_active_region","Partial Optimisation")

        # Still missing
        # use template z
        # template z name

        # HDLC group
        options = [ "Single Residue" , "PDB Residues", "Cartesian/Select", "PDB Residues/Select" ]
        self.residue_treatment_tool = SelectOptionTool(
            self,"residue_treatment","Residue Treatment",options)
        self.hdlc_region_tool=AtomSelectionTool(self,"active_atoms","Active Atoms")
        self.hdlcopt_memory_tool=IntegerTool(self,"hdlcopt_memory","HDLCOpt Memory",min=0)
        # Need to add constraints

        #Dynamics page
        self.max_dyn_step_tool = IntegerTool(self,"max_dyn_step","# Dynamics Steps",min=0)
        self.update_freq_tool = IntegerTool(self,"update_freq","Update Freq",min=0)
        self.temp_tool = FloatTool(self,"temp","Temperature",min=0.0)
        self.tstep_tool = FloatTool(self,"tstep","Time Step",min=0.0)
        item_labels = [ "NVE", "NVT", "NPT" ]
        self.ensemble_tool = SelectOptionTool(self,"ensemble","Ensemble",item_labels)
        item_labels = [ "none", "input", "ideal" ]
        self.shake_option_tool = SelectOptionTool(self,"shake_option","Shake Option",item_labels)
        self.store_trajectory_tool = BooleanTool(self,"store_traj","Store Trajectory")
        self.traj_freq_tool = IntegerTool(self,"traj_freq","Trajectory Frame Interval",min=0)

        self.LayoutToolsTk()
        
    def LayoutToolsTk(self):

        #page = self.notebook.add('Title',tab_text='Title')
        # TASK PAGE
        page = self.notebook.add('Task',tab_text='Task')
        labels = []
        self.task_tool.widget.pack(in_=page)
        self.calctype_tool.widget.pack(in_=page)

        self.f = Tkinter.Frame(page)
        self.f.pack(expand='yes',fill='x',side='top')
        self.qmgroup = Pmw.Group(self.f,tag_text="QM Options")
        self.mmgroup = Pmw.Group(self.f,tag_text="MM Options")

        self.editmm_widget = Tkinter.Button(self.mmgroup.interior())
        self.editmm_widget.config(command=self.__editmm)
        self.editmm_widget.config(text='Edit MM Options')

        self.editqm_widget = Tkinter.Button(self.qmgroup.interior())
        self.editqm_widget.config(command=self.__editqm)
        self.editqm_widget.config(text='Edit QM Options')
        
        self.qmcode_tool.widget.pack(in_=self.qmgroup.interior(),side='left')
        self.editqm_widget.pack(in_=self.qmgroup.interior(),side='left')
        self.mmcode_tool.widget.pack(in_=self.mmgroup.interior(),side='left')
        self.editmm_widget.pack(in_=self.mmgroup.interior(),side='left')

        self.__set_calctype('dum')

        # COUPLING PAGE
        page = self.notebook.add('Coupling',tab_text='Coupling')
        labels = []
        self.use_qmmm_cutoff_tool.widget.pack(in_=page)
        self.qmmm_cutoff_tool.widget.pack(in_=page)
        self.dipole_adjust_tool.widget.pack(in_=page)
        self.coupling_tool.widget.pack(in_=page)
        self.qm_region_tool.widget.pack(in_=page)
        #conn group
        page.conn_group = Pmw.Group(page,tag_text="Connectivity Options")
        self.export_connectivity_tool.widget.pack(in_=page.conn_group.interior())
        self.conn_scale_tool.widget.pack(in_=page.conn_group.interior())
        self.conn_toler_tool.widget.pack(in_=page.conn_group.interior())
        page.conn_group.pack()

        # OPTIMISATION PAGE
        page = self.notebook.add('Optimisation',tab_text='Optimisation')

        self.optimiser_tool.widget.pack(in_=page)
        self.newopt_method_tool.widget.pack(in_=page)
        self.max_opt_step_tool.widget.pack(in_=page)
        self.find_ts_tool.widget.pack(in_=page)

        self.active_group = Pmw.Group(page,tag_text="Active Atoms")
        self.active_group.pack(expand='yes',fill='x')
        self.active_atoms_tool.widget.pack(expand=1,fill='x',in_=self.active_group.interior())
        self.use_active_region_tool.widget.pack(expand=1,fill='x',in_=self.active_group.interior())

        self.hdlc_group = Pmw.Group(page,tag_text="HDLC Parameters")
        self.hdlc_group.pack(expand='yes',fill='x')
        self.residue_treatment_tool.widget.pack(expand='yes',fill='x',in_=self.hdlc_group.interior())
        self.hdlc_region_tool.widget.pack(expand=1,fill='x',in_=self.hdlc_group.interior())
        self.hdlcopt_memory_tool.widget.pack(expand = 1, fill = 'x',in_=self.hdlc_group.interior())


        # DYNAMICS PAGE
        page = self.notebook.add('Dynamics',tab_text='Dynamics')
        self.max_dyn_step_tool.widget.pack(in_=page)
        self.update_freq_tool.widget.pack(in_=page)
        self.temp_tool.widget.pack(in_=page)
        self.tstep_tool.widget.pack(in_=page)
        self.ensemble_tool.widget.pack(in_=page)
        self.shake_option_tool.widget.pack(in_=page)
        self.traj_group = Pmw.Group(page,tag_text="Trajectory Output")
        self.traj_group.pack(expand='yes',fill='x')
        self.store_trajectory_tool.widget.pack(in_=self.traj_group.interior())
        self.traj_freq_tool.widget.pack(in_=self.traj_group.interior())
        #labels = [ ] 
        #Pmw.AlignLabels(labels)
        
    def __set_calctype(self,dummy_option):
        """
        set visibility of controls depending in which type of calculation
        is requested
        """
        print '__set_calctype', self.calc.get_parameter('calctype')

        self.calctype_tool.ReadWidget()

        if self.calc.get_parameter('calctype') == 'QM' or \
           self.calc.get_parameter('calctype') == 'QM/MM':
            #labels = labels + [page.qmcode]
            self.qmgroup.pack(side='top')
        else:
            self.qmgroup.forget()

        if self.calc.get_parameter('calctype') == 'MM' or \
               self.calc.get_parameter('calctype') == 'QM/MM':
            #labels = labels + [page.mmcode]
            self.mmgroup.pack(side='top')
        else:
            self.mmgroup.forget()

    def __editmm(self):
        self.mmcode_tool.ReadWidget()
        if self.mmeditor != None:
            print 'renewing editor'
            self.mmeditor.EndEdit()

        if self.calc.mmcalc == None:
            self.calc.create_mm_calc()

        self.mmeditor = self.calc.mmcalc.edit(self.root,
                                              self.graph,
                                              vis=[self.mol_vis],
                                              master=self,
                                              reload_func=self.reload_func)
        print 'mm ed', self.mmeditor
        self.mmeditor.Show()

    def __editqm(self):
        self.qmcode_tool.ReadWidget()
        if self.qmeditor != None:
            print 'renewing editor'
            self.qmeditor.EndEdit()

        if self.calc.qmcalc == None:
            self.calc.create_qm_calc()

        #
        #  a reload_func should be provided to yeild the 
        #  qm molecule only
        #
        self.qmeditor = self.calc.qmcalc.edit(self.root,
                                              self.graph,
                                              vis=[self.mol_vis],
                                              master=self,
                                              reload_func=self.reload_func)
        self.qmeditor.Show()



    def monitor(self):
        """Transfer partially completed structure to GUI and update the graph widget
        """
        print 'monitor'
        # Update displayed structure if a new geometry has arrived
        if os.path.exists('FRAME.stamp'):
            p=PunchReader()
            os.unlink('FRAME.stamp')
            p.scan('FRAME')
            mol = self.calc.get_input('mol_obj')
            print 'UPDATE GEOM'
            mol.import_geometry(p.objects[0] )
            if self.graph:
                print 'UPDATE GRAPH'
                self.graph.update_from_object(mol)
            # Update graph widget
            #self.calcMon.update()
            #self.calcMon.show()

    def _get_qm_mol(self):
        """return the QM part of the system
        This is used by the qm calc editor to control (for example)
        the basis set editor.
        Not written yet
        """
        pass

    def LaunchCalcEd(self,calc):
        """Create a new calculation editor."""
        a = ChemShellCalcEd(calc)
        a.Show()


    def ClusterPage(self,page,action):

        # make_cluster
        # cluster algoritm
        # construct origin (3*float)
        # construct use origin atom
        # construct origin atom
        # construct cutoff
        # construct grid dimension
        # use_marvin_file
        # marvin_file_name
        # bq_layer (integer)

        # gulp_ff string
        # gulp_add_shells string
        # gulp_atom_type 0
        pass

    def Run(self,writeinput=1):
        """Run the calculation.
        First read any data from the qm and mm calculation pages, then
        proceed with normal run
        """
        if self.qmeditor:
            self.qmeditor.ReadWidgets()
        if self.mmeditor:
            self.mmeditor.ReadWidgets()
        CalcEd.Run(self,writeinput)

def copycontents(to,fro):
    """Used to update an object by copying in the contents from another"""
    c = to.__class__
    d1 = c.__dict__
    try:
        d2 = fro.__dict__
    except AttributeError:
        d2 = {}
    for k in d2.keys():
        to.__dict__[k] = fro.__dict__[k]


# helper routine for sorting normal modes by frequency
def fcomp(a,b):
    if a.sorter > b.sorter:
        return 1
    if a.sorter < b.sorter:
        return -1
    return 0

def chemshell_z_modes():

    # First load the zmatrix defining the coordinate system
    p = PunchReader()
    p.scan("zopt.z_vis")
    # And the hessian matrix defining the normal modes
    p.scan("newopt.h_vis")
    z = p.objects[0]
    h = p.objects[1]

    # Convert hessian data to a Numeric array
    from Numeric import array
    t = []
    start = 0
    n = h.dimensions[0]
    for i in range(n):
        stop = start + n 
        t.append(h.data[start:stop])
        start = start + n
    h.array = array(t)
    #print h.array

    # Generate evals and evecs
    from LinearAlgebra import eigenvectors
    eval,evec = eigenvectors(h.array)
    print 'eval',eval
    print 'evec',evec

    # Generate Initial cartesians
    z.calculate_coordinates()
    # Save a reference structure
    z2 = z.copy()

    # conversion for angles
    pi_over_180 = math.atan(1.0) / 45.0
    radtodeg = 1.0 / pi_over_180

    scale = 0.5

    vs=VibFreqSet()
    vs.reference=z2
    vs.title = "modes of " + z2.title
    vs.name = "modes of " + z2.title

    # Loop over the eigenvectors
    for i in range(n):
        print '================ evec',i,'================'
        val = eval[i]
        vec = evec[i]
        #print 'Applying vec',vec
        # Apply a shift to the Internal coordinates relative to 
        # the reference structure
        for j in range(n):
            if z.variables[j].metric == 'a':
                fac = scale*radtodeg
            else:
                fac = scale
            print z.variables[j].name, z2.variables[j].value, vec[j]*scale
            z.variables[j].value = z2.variables[j].value + vec[j]*fac
        # Compute new coordinates
        z.calculate_coordinates()
        # Create a vibrational freq structure
        v = VibFreq(i)
        v.displacement = []
        # extra field for ordering
        v.sorter=val
        for ia in range(len(z.atom)):
            atom = z.atom[ia]
            ref  = z2.atom[ia]
            dx = atom.coord[0] - ref.coord[0]
            dy = atom.coord[1] - ref.coord[1]
            dz = atom.coord[2] - ref.coord[2]
            d = Vector(dx,dy,dz)
            print d
            v.displacement.append(d)
            v.freq = float(val)
            t='v%-10.5f' % v.freq
            v.title = t
            v.name = t

        vs.vibs.append(v)

    # Finally sort vibrations into ascending order
    vs.vibs.sort(fcomp)

    return [vs]

def chemshell_c_modes():

    # First load the structure defining the coordinate system
    p = PunchReader()
    p.scan("copt.c_vis")
    # And the hessian matrix defining the normal modes
    p.scan("newopt.h_vis")
    z = p.objects[0]
    h = p.objects[1]

    # Convert hessian data to a Numeric array
    from Numeric import array
    t = []
    start = 0
    n = h.dimensions[0]
    for i in range(n):
        stop = start + n 
        t.append(h.data[start:stop])
        start = start + n
    h.array = array(t)
    #print h.array

    # Generate evals and evecs
    from LinearAlgebra import eigenvectors
    eval,evec = eigenvectors(h.array)
    #print 'eval',eval
    #print 'evec',evec

    # Generate Initial cartesians
    # z.calculate_coordinates()
    # Save a reference structure
    z2 = z.copy()

    # if the hessian is smaller than expected, load active atoms specification
    tester = 3*len(z.atom) - n
    if tester > 0:
        try:
            f = open("copt.vis_active.txt","r")
        except:
            print "copt.vis_active.txt file is needed to define active atoms"
            return []
        txt = f.readlines()
        f.close()
        active_atoms=[]
        for t in txt:
            for tt in t.split():
                active_atoms.append(int(tt)-1)
        print "Active atoms : ",active_atoms,"hessian dim ",n
        if 3*len(active_atoms) != n:
            print "active atoms list is incorrect length for newopt.h_vis matrix"
            return []
    else:
        active_atoms = range(len(z.atom))

    vs=VibFreqSet()
    vs.reference=z2
    vs.title = "modes of " + z2.title
    vs.name = "modes of " + z2.title
    # Loop over the eigenvectors
    for i in range(n):
        #print '================ evec',i,'================'
        val = eval[i]
        vec = evec[i]

        # Create a vibrational freq structure
        v = VibFreq(i)
        v.reference = z2
        v.displacement = []
        # extra field for ordering
        v.sorter=val

        nullv = Vector(0.,0.,0.)
        for i in range(len(z.atom)):
            v.displacement.append(nullv)

        for i in range(len(active_atoms)):
            ia = active_atoms[i]
            ref  = z2.atom[ia]
            off=3*(i)
            dx = vec[off]
            dy = vec[off+1]
            dz = vec[off+2]
            d = Vector(dx,dy,dz)
            v.displacement[ia]=d
            v.freq = float(val)
            t='v%-10.5f' % v.freq
            v.title = t
            v.name = t

        vs.vibs.append(v)

    # Finally sort vibrations into ascending order
    vs.vibs.sort(fcomp)

    return [vs]

if __name__ == "__main__":

    import sys
#    print sys.path
    
    from interfaces.chemshell import *
    from objects.zmatrix import *

    from jobmanager import *
    model = Zmatrix()
    model.title = "chemshell test"
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
    calc = ChemShellCalc()
    calc.set_input('mol_obj',model)
    jm = JobManager()
    je = JobEditor(root,jm)
    vt = ChemShellCalcEd(root,calc,None,job_editor=je)
    vt.Run()
    root.mainloop()
