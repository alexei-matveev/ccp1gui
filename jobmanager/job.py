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
"""Classes for jobs and job steps 

JobStep - component step, shared for for all job types. This
states in general terms what needs to happen at each step.

Job  - base class for all jobs, controls loop over steps but requires
the derived class for a particular job to implement the particular methods
allocate_scratch, delete_file, execute_shell etc

Subclasses for real jobs:

BackgroundJob
   based on subprocess.Spawn for the main step
            subprocess.ForegroundPipe for file operations
 
ForegroundJob
   all operations use subprocess.ForegroundPipe
 
 RemoteForegroundJob
   subprocess.Spawn(plink/ssh)
   not yet implemented

LoadLevelerJob
   not yet implemented

"""

import subprocess
import sys
import os
import re
import time
from viewer.paths import backup_dir
from viewer.rc_vars import rc_vars
import shutil

# These are placeholders for modules that will be loaded as required
SOAPpy = None
rmcs   = None
srbftp = None
arclib = None

ALLOCATE_SCRATCH='allocate-scratch'
DELETE_FILE='delete-file'
COPY_OUT_FILE='copy-out-file'
EXECUTE_SHELL='execute-shell'
RUN_APP='running....'
RUN_APP_BASH='running under bash....'
COPY_BACK_FILE='copy-back-file'
CLEAN_SCRATCH='clean-scratch'
PYTHON_CMD='python-code'
#
JOBSTATUS_IDLE    = 'Idle'
JOBSTATUS_RUNNING = 'Running'
JOBSTATUS_KILLPEND= 'Kill Pending'
JOBSTATUS_KILLED  = 'Killed'
JOBSTATUS_FAILED  = 'Failed'
JOBSTATUS_WARNING = 'Warning'
#JOBSTATUS_OK      = 'OK'
JOBSTATUS_DONE    = 'Done'

JOBCMD_KILL ='Kill'
JOBCMD_CANCEL ='Cancel'

class JobStep:
    """A container class for an element of a job"""
    def __init__(self,type,name,
                 local_filename=None,
                 remote_filename=None,
                 cmd=None,
                 proc=None,
                 jobname=None,
                 local_command=None,
                 remote_command=None,
                 stdin_file=None,
                 stdout_file=None,
                 stderr_file=None,
                 monitor_file=None,
                 warn_on_error=0,
                 kill_on_error=1,
                 kill_cmd=None):

        # see list of valid types above
        self.type = type
        # just a descriptor for following progress
        self.name = name
        self.local_filename=local_filename
        self.remote_filename=remote_filename
        self.cmd=cmd
        self.jobname=jobname
        self.proc=proc
        self.local_command=local_command
        self.remote_command=remote_command
        self.stdin_file=stdin_file
        self.stdout_file=stdout_file
        self.stderr_file=stderr_file
        self.monitor_file=monitor_file
        self.kill_on_error=kill_on_error
        self.warn_on_error = warn_on_error
        self.kill_cmd = kill_cmd
        self.job_parameters = {} # Dictionary of job parameters for Nordugrid, RMCS, Growl etc jobs

class Job:

    """Base class for jobs

    handles construction of the job as a list of steps
    """

    def __init__(self,name=None):

        self.steps=[]
        self.msg=""
        self.host = 'localhost'
        if name:
            self.name =name
        else:
             self.name ='Job'

        self.status = JOBSTATUS_IDLE
        self.active_step = None
        self.process = None
        self.tidy = None
        self.monitor = None
        self.debug = 1
        
    def __repr__(self):
        txt = self.jobtype + ':'
        for step in self.steps:
            txt = txt + step.type + '/'
        return txt

    def add_step(self,type,name,**kw):
        """Add a new job Step"""
        if self.debug:
            print 'adding job step: %s : %s' % (name,kw)
        self.steps.append(JobStep(type,name,**kw))

    def add_tidy(self,func):
        """Add a tidy function, python code run from the main GUI thread"""
        if self.debug:
            print 'adding tidy fn'
        self.tidy = func

    def add_monitor(self,func):
        """Add a monitor function, python code run periodically from the main GUI thread"""
        if self.debug:
            print 'adding monitor fn'
        self.monitor = func

    def run(self):
        """Main execution point, execute sequence of steps"""
        count = 0
        self.step_number = 0
        self.status = JOBSTATUS_RUNNING
        for step in self.steps:
            count = count + 1
            # flag to ensure diagnostics only get popped up once
            # per job step
            self.popup = 1
            # Notification of start here
            self.active_step = step
            self.step_number = count
            if self.debug:
                print 'Executing step #',self.step_number,':',step.type, step.name

            try:

                if step.type == ALLOCATE_SCRATCH:
                    code,message = self.allocate_scratch(step)
                elif step.type == DELETE_FILE:
                    code,message = self.delete_file(step)
                elif step.type == COPY_OUT_FILE:
                    code,message = self.copy_out_file(step)
                elif step.type == RUN_APP:
                    code,message = self.run_app(step)
                elif step.type == RUN_APP_BASH:
                    code,message = self.run_app_bash(step)
                elif step.type == EXECUTE_SHELL:
                    code,message = self.execute_shell(step)
                elif step.type == COPY_BACK_FILE:
                    code,message = self.copy_back_file(step)
                elif step.type == CLEAN_SCRATCH:
                    code,message = self.clean_scratch(step)
                elif step.type == PYTHON_CMD:
                    code,message = self.python_cmd(step)
                    if self.debug:
                        print 'Python Step code=',code,message
                else:
                    self.msg="unknown step type" + step.type
                    return -1
                
            except Exception, e:
                if self.debug:
                    print 'Fatal Exception in step: %s' % step.name
                    print 'Exception is: %s' % e
                self.status = JOBSTATUS_FAILED
                self.msg = str(e)
                return 1
                
            self.msg = message
            if self.debug:
                print 'test code',code,message

            if code == 0:
                #self.status = JOBSTATUS_OK
                if self.debug:
                    print 'Step OK :',step.name, message

            # Pass messages back for the user
            elif code == -1 and step.kill_on_error:
                self.status = JOBSTATUS_FAILED
                if message:
                    self.msg =  'Step \"%s\" failed: %s' % (step.name,message)
                else:
                    self.msg =  'Step Failed : no msg available'
                return 1

            # Pass messages back for the user
            elif step.warn_on_error == 1 :

                # code = 1 or code -1 and we are proceeding
            

                self.status = JOBSTATUS_WARNING
                print 'Step Warning :',step.name, message

                # ideally would wait here until the job editor
                # has picked up the message
                #print 'waiting'
                #for i in range(1000000):
                #    if not self.popup:
                #        print 'breaking'
                #        break

            else:
                #self.status = JOBSTATUS_OK
                if self.debug:
                    print 'Step failed, but proceed anyway:',step.name, message


        self.active_step = None
        self.status = JOBSTATUS_DONE
        if self.debug:
            print 'job run completed'

    def delete_file(self,step):
        if sys.platform[:3] == 'win':
            cmd = 'del ' + step.remote_filename
        else:
            cmd = 'rm ' + step.remote_filename

        pipe=subprocess.ForegroundPipe(cmd,debug=self.debug)
        code = pipe.run()
        if code:
            msg = pipe.msg
        else:
            msg = None
        return code,msg

    def copy_out_file(self,step):
        data = open(step.local_filename, "rb").read()
        if not step.remote_filename:
            step.remote_filename = step.local_filename

        if '\0' in data:
            print file, "BinaryFile!"
            cmd = '"C:/Program Files/PuTTY/pscp.exe" ' + step.local_filename + ' ' + self.remoteuser + '@' + self.host + ':' + self.remote_filename
        else:
            newdata = re.sub("\r\n", "\n", data)
            t = open('unx_'+step.local_filename,"wb")
            t.write(newdata)
            t.close()
            cmd = '"C:/Program Files/PuTTY/pscp.exe" ' + 'unx_' + step.local_filename  + ' ' + self.remoteuser + '@' + self.host + ':' + step.remote_filename

        print 'copy out cmd',cmd
        p = subprocess.ForegroundPipe(cmd,debug=self.debug)
        code = p.run()
        print 'copy out code',code
        return code,None

    def copy_back_file(self,step):
        print self.remoteuser
        print self.host
        print step.remote_filename
        if not step.local_filename:
            step.local_filename = step.remote_filename

        cmd = '"C:/Program Files/PuTTY/pscp.exe" ' + self.remoteuser + '@' + self.host + ':' + step.remote_filename + ' ' + self.local_filename
        print 'copy back cmd',cmd
        p = subprocess.ForegroundPipe(cmd,debug=self.debug)
        code = p.run()
        print 'copy out code',code
        return code,None


    def execute_shell(self,step):
        return -1,"execute shell unimplemented"


    def python_cmd(self,step):
        return step.proc()

    def execute_step(self):
        """Execute a single step
        This will be overridden in the particular types of job
        """
        pass

    # ? other methods might include pause?

    def kill(self):
        """Attempt to kill the job (dummy)"""
        print 'Kill unimplemented for this job type'
            

    def get_status(self):
        """Return the current status of the job"""
        return self.status

    def get_rcvars(self):
        """ Update any job parameters from the rc_vars.
        """

        global rc_vars
        for key,value in self.job_parameters.iteritems():
            if rc_vars.has_key(key):
                self.job_parameters[key]= rc_vars[key]
                
        if self.debug:
            print "job get_rcvars: parameters are now:"
            print self.job_parameters

    def update_job_parameters(self, job_dict):
        """Update the job parameters from the supplied dictionary
           Only updates for variables that already exist as keys in the
           job_parameters dictionary are permitted.
        """

        for key,value in self.job_parameters.iteritems():
            if job_dict.has_key( key ):
                self.job_parameters[key] = job_dict[key]
                
        if self.debug:
            print "job update_job_parameters: parameters are now:"
            print self.job_parameters


class BackgroundJob(Job):
    """Sub class for a job running on the local resource

    This version uses
       - a control thread which then uses fork/spawn
       - 2 communication queues to allow the main (calling)
         thread to check job status (e.g. to update the view)
         or to kill the job
    """

    def __init__(self,**kw):
        apply(Job.__init__, (self,), kw)
        self.jobtype='Local Background'

    def allocate_scratch(self,step):
        pass

    def copy_out_file(self,step):
        """overload generic function as this is a local job type"""
        if not step.remote_filename:
            step.remote_filename = step.local_filename

        if step.local_filename != step.remote_filename:
            cmd = 'del ' + self.remote_filename
            subprocess.ForegroundPipe(cmd,debug=self.debug).run()
            cmd = 'ren ' + self.local_filename + ' ' + step.remote_filename
            subprocess.ForegroundPipe(cmd,debug=self.debug).run()
        return 0,None

    def run_app(self,step):
        # Support for a generic application interface
        if sys.platform == 'mac':
            print 'Dont know how to run on mac'
            return -1
        elif sys.platform[:3] == 'win':

            # Remove stdout
            if step.stdout_file:
                f = os.popen('del '+step.stdout_file)
                status2 = f.close()

            #cmd = self.local_command + ' < ' + step.stdin_file + ' > ' + step.stdout_file
            cmd = step.local_command 

            if self.debug:
                print "Background job win: run_app cmd: ",cmd
            self.process = subprocess.Spawn(cmd,debug=self.debug)
            if step.stdin_file:
                i = open(step.stdin_file,'r')
            else:
                i = None
            if step.stdout_file:
                o = open(step.stdout_file,'w')
            else:
                o = None

            e=open('stderrfile','w')
            self.process.run(stdin=i,stdout=o,stderr=e)
            code = self.process.wait()
            self.process = None
            if o:
                o.close()
            if i:
                i.close()

            e.close()
            e = open('stderrfile','r')
            txt = e.readlines()
            e.close()
            print 'stderr is ',txt
            if len(txt):
                msg = 'txt on Stderr:\n'
                for t in txt:
                    msg = msg + t + '\n'
                raise JobError, msg

            if code != 0: 
                raise JobError, "Unexpected Exit code=" + str(code)

        else:
            # Unix code
            # !! Paul Feb 2004 what happened to stdin, stdout
            # may need to fix here and the bash version
            # - hacked back April 05
            
            # jmht - this won't work with Spawn, as the command will be executed with
            # < and > as arguments and won't be used to pipe stdin & stdout
            #if step.stdin_file:
            #    cmdtmp = cmdtmp + ' < ' + step.stdin_file
            #if step.stdout_file:
            #    cmdtmp = cmdtmp + ' > ' + step.stdout_file                
                
            cmd = step.local_command
            if self.debug:
                print "Background job: run_app cmd: ",cmd
                
            self.process = subprocess.Spawn(cmd,debug=self.debug)

            # Open any files we may have been given and give these to the run method
            if step.stdin_file:
                stdin = open(step.stdin_file,'r')
            else:
                stdin = None
            if step.stdout_file:
                stdout = open(step.stdout_file,'w')
            else:
                stdout = None

            #stderr = open('stderrfile','w')
                
            self.process.run(stdin=stdin, stdout=stdout)
            
            code = self.process.wait()
            if code != 0: 
                msg = ""
                for tt in self.process.error:
                    msg = msg + tt
                raise JobError, "Unexpected Exit code=" + str(code) + " : " + msg

        return 0,None


    def run_app_bash(self,step):
        #
        # Support for a generic application interface
        # This one spawns under control of the Cygwin bash shell
        # this seems to help the system command issued from within ChemShell
        # to work properly
        #
        print 'run_app_bash'
        if sys.platform == 'mac':
            print 'Dont know how to run on mac'
            return -1
        elif sys.platform[:3] == 'win':

            # Remove stdout
            if step.stdout_file:
                f = os.popen('del '+step.stdout_file)
                status2 = f.close()

            # Use of input file for bash worked OK.. may be useful one day for
            # case we need to pass multi-line commands to bash
            # create as binary to avoid \r hassles
            #file=open("bash.txt","wb")
            # redirection works here but is not needed as stdin/out are handled by Spawn
            #file.write(step.local_command+'\n')
            #file.write(cmd)
            #file.close()
            #cmd="C:/cygwin/bin/bash.exe bash.txt"            

            # various permutations tried...
            #cmd = step.local_command + ' < ' + step.stdin_file + ' > ' + step.stdout_file + ' \n'
            #cmd = step.local_command
            #chemshell_exe='"C:/chemsh/bin/chemshprog.exe"'
            #file.write('chemsh < new.chm > new.log\n')
            #file.write('"C:/chemsh/bin/chemshprog.exe" < new.chm > new.out \n')
            #cmd = step.local_command + ' < ' + step.stdin_file + ' > ' + step.stdout_file + ' \n'
            #cmd='echo hello>junk.txt\n'

            #This works OK as well
            #cmd="C:/cygwin/bin/bash.exe "+step.local_command
            # But NOTE trying to use input redirection (<) here fails
            # in contrast to the foreground case where its OK

            # This seems the simplest form of the command
            cmd="bash "+step.local_command

            print 'Spawn on ',cmd
            #import os
            #print 'PATH is',os.environ['PATH']

            self.process = subprocess.Spawn(cmd,debug=self.debug)
            if step.stdin_file:
                i = open(step.stdin_file,'r')
            else:
                i = None
            if step.stdout_file:
                o = open(step.stdout_file,'w')
            else:
                o = None
            e = open('stderrfile','w')
            self.process.run(stdin=i,stdout=o,stderr=e)
            code = self.process.wait()
            print 'return code',code
            self.process = None
            if o:
                o.close()
            if i:
                i.close()
            if e:
                e.close()
            if code != 0: 
                e = open('stderrfile')
                txt = e.readlines()
                e.close()
                print 'err txt',txt
                msg = "Unexpected Exit code=" + str(code) + '\n'
                msg = msg + 'Stderr from process follows:\n'
                for t in txt:
                    msg = msg + t
                raise JobError, msg

        else:
            # Unix code
            cmd = step.local_command
            self.process = subprocess.Spawn(cmd,debug=self.debug)
            self.process.run()
            code = self.process.wait()
            if code != 0: 
                raise JobError, "Unexpected Exit code=" + str(code)

        return 0,None



    def copy_back_file(self,step):
        """ This provides a rename function when used in a local job"""

        if not step.local_filename:
            step.local_filename = step.remote_filename

        if step.local_filename != step.remote_filename:
            if sys.platform[:3] == 'win':
                cmd = 'ren ' + step.remote_filename + ' ' + step.local_filename
                code = subprocess.ForegroundPipe(cmd,debug=self.debug).run()
                if code:
                    raise JobError, "failed to recover " +  step.remote_filename
            else:
                cmd = 'mv ' + step.remote_filename + ' ' + step.local_filename
                code = subprocess.ForegroundPipe(cmd,debug=self.debug).run()
                if code:
                    raise JobError, "failed to recover " +  step.remote_filename
        return 0,None

    def clean_scratch(self,step):
        # Null function here
        return 0,None

    def kill(self):

        if self.active_step and self.active_step.kill_cmd:
                print 'running kill cmd for the current step'
                self.status = JOBSTATUS_KILLPEND
                self.active_step.kill_cmd()
                #    self.status = JOBSTATUS_KILLED

        elif self.process:
            print 'attempting to kill process'
            self.status = JOBSTATUS_KILLPEND
            code = self.process.kill()
            print 'kill return code',code
            self.status = JOBSTATUS_KILLED
            return code
        else:
            return -1
    
class ForegroundJob(Job):
    """Sub class for a job running on the current resource

    this is simply for testing, no threads or background spawn calls
    it uses the SubProcess.pipe to invoke the required calls
    """

    def __init__(self,**kw):
        apply(Job.__init__, (self,), kw)
        self.jobtype='Local Background'
        
    def allocate_scratch(self,step):
        return 0,None

    def copy_out_file(self,step):

        """Transfer file from execution host

        overloads the generic function as this is a local job type, we just
        rename the file
        """

        if not step.remote_filename:
            step.remote_filename = step.local_filename

        if step.local_filename != step.remote_filename:
            cmd = 'del ' + self.remote_filename
            subprocess.ForegroundPipe(cmd,debug=self.debug).run()
            cmd = 'ren ' + self.local_filename + ' ' + step.remote_filename
            subprocess.ForegroundPipe(cmd,debug=self.debug).run()
        return 0,None

    def run_app(self,step):

        cmd = step.local_command
        if step.stdin_file:
            cmd = cmd + ' < '+ step.stdin_file
        if step.stdout_file:
            cmd = cmd + ' > ' + step.stdout_file

        #print 'checking path'
        #p = subprocess.ForegroundPipe("echo $PATH",debug=self.debug)
        #code = p.run()        

        if self.debug:
            print 'ForegroundJob: cmd=',cmd
        p = subprocess.ForegroundPipe(cmd,debug=self.debug)
        code = p.run()
        if code:
            print 'code from run_app',code
            print 'step.error',p.error
            print 'step.msg',p.msg
            return code, p.msg
        else:
            return 0, None


    def run_app_bash(self,step):

        cmd = step.local_command
        if step.stdin_file:
            cmd = cmd + ' < '+ step.stdin_file
        if step.stdout_file:
            cmd = cmd + ' > ' + step.stdout_file
        print 'ForegroundJob: cmd=',cmd

        file=open("bash.txt","wb")
        file.write(cmd)
        file.close()

        cmd="C:/cygwin/bin/bash.exe < bash.txt"
        p = subprocess.ForegroundPipe(cmd,debug=self.debug)
        code = p.run()

        return code,None

    def copy_back_file(self,step):
        return 0,None

    def clean_scratch(self,step):
        return 0,None

    def kill(self):
        """Attempt to kill the job (dummy)"""
        if self.active_step:
            if self.active_step.kill_cmd:
                self.status = JOBSTATUS_KILLPEND
                print 'running kill cmd'
                self.active_step.kill_cmd()

class RemoteForegroundJob(Job):
    """Control of the job using rsh/plink"""

    def __init__(self,host,remoteuser, **kw):
        apply(Job.__init__, (self,), kw)
        self.jobtype='Remote Foreground Job'
        self.host=host
        self.remoteuser=remoteuser

    def allocate_scratch(self,step):
        return 0,None

    def run_gamessuk(self,step):
        cmd = "/usr/local/packages/gamessuk/rungamess/rungamess " + step.jobname
        rcmd = '"C:/Program Files/PuTTY/plink.exe"' + ' ' + self.host + ' ' + cmd 
        print 'remote command:',rcmd
        p = subprocess.Spawn(rcmd,debug=1)
        code = p.run()
        print 'run code',code
        code = p.wait()
        print 'wait code',code


    def clean_scratch(self,step):
        return 0,None

class LoadLevelerJob(Job):
    """Class for a local loadleveler job"""
    def __init__(self,host,remoteuser,**kw):
        apply(Job.__init__, (self,), kw)
        self.jobtype='LoadLeveler'
        self.host=host
        self.remoteuser=remoteuser
        
    def allocate_scratch(self,step):
        return 0,None

    def run_gamessuk(self,step):

        if 0:
            cmd = 'printenv'
            rcmd = '"C:/Program Files/PuTTY/plink.exe"' + ' ' + self.host + ' '+ cmd
            p = subprocess.SlavePipe(rcmd,debug=1)
            code = p.run()
            print 'run code',code
            code = p.wait()
            print 'OUT',p.get_output()
            return -1

        #cmd = "/usr/local/packages/gamessuk/rungamess/rungamess -p 4 -T 10 -q " + step.jobname
        cmd = "/hpcx/home/z001/z001/psh/GAMESS-UK/rungamess/rungamess -p 4 -T 10 -q " + step.jobname
        rcmd = '"C:/Program Files/PuTTY/plink.exe"' + ' ' + self.host + ' ' + cmd 
        print 'remote command:',rcmd
        p = subprocess.SlavePipe(rcmd,debug=0)
        code = p.run()
        print 'run code',code
        code = p.wait()
        print 'OUT',p.get_output()
        cmd = 'llq'
        rcmd = '"C:/Program Files/PuTTY/plink.exe"' + ' ' + self.host + cmd
        p = subprocess.SlavePipe(rcmd,debug=0)
        code = p.run()
        print 'run code',code
        code = p.wait()
        print 'OUT',p.get_output()

    def clean_scratch(self,step):
        return 0,None


class RMCSJob(Job):
    """Class for running job's using Rik's Remote MyCondorSubmit"""
    def __init__(self,editor=None,**kw):

        # Before we do anything, make sure we can import the required modules
        global rmcs,srbftp,SOAPpy
        try:
            import SOAPpy
            import interfaces.rmcs as rmcs
            import interfaces.srbftp as srbftp
        except ImportError:
            raise JobError,"RMCS Job cannot import the SOAPpy module so the job cannot be run.\n \
            Please install the SOAPpy module"
        
        apply(Job.__init__, (self,), kw)

        self.jobtype='RMCS Job'
        self.jobID = None # used to query the job status
        self.poll_interval = 30 # how often to check the job state in the loop
        self.srbftp = None
        self.rmcs = None
        
        # Variables that we use to write out the MCS file
        # Set to none so that we can check we have been passed them
        self.job_parameters = {}
        self.job_parameters['machine_list'] = None
        self.job_parameters['count'] = None
        self.job_parameters['inputfiles'] = []
        self.job_parameters['outputfiles'] = []
        self.job_parameters['srb_config_file'] = None
        self.job_parameters['srb_input_dir'] = None
        self.job_parameters['srb_output_dir'] = None
        self.job_parameters['srb_executable_dir'] = None
        self.job_parameters['srb_executable']   = None
        self.job_parameters['rmcs_user'] = None
        self.job_parameters['rmcs_password'] = None
        self.job_parameters['myproxy_user'] = None
        self.job_parameters['myproxy_password'] = None

        self.get_rcvars()
            
        #self.input_files = []
        #self.output_files = []

    def copy_out_file(self,step,kill_on_error=1):
        """Add file to the list of files that we copy out
           and place the file in the srb.
           step.local_filename is the name of the file. If we are supplied with
           a step.remote_filename argument, we rename the file when putting it
           in the srb."""

        if not step.local_filename or not os.access( step.local_filename,os.R_OK ):
            return -1,"RMCS copy_out_file error accessing file: %s!" % step.local_filename

        #self.input_files.append(step.local_filename)
        self.job_parameters['inputfiles'].append(step.local_filename)
        try:
            srbftp_intfce = self._get_srbftp()
        except:
            return -1,"Error initialising srbftp interface in copy_out_file!"

        # Put input file in the srb and rename if necessary
        srbftp_intfce.cd(self.job_parameters['srb_input_dir'])
        
        if step.remote_filename:
            shutil.copyfile( step.local_filename, step.remote_filename )
            srbftp_intfce.put(step.remote_filename)
        else:
            srbftp_intfce.put(step.local_filename)
        return 0,"Placed file %s in the srb" % step.local_filename
            
    def copy_back_file(self,step,kill_on_error=None):
        """Get the file from the srb and rename it if necessary"""

        #if not step.remote_filename or not os.access( step.remote_filename,os.R_OK ):
        if not step.remote_filename and not step.local_filename:
            return -1,"RMCS copy_back_file error needs a filename!"

        if not step.remote_filename:
            remote_filename = step.local_filename
        else:
            remote_filename = step.remote_filename

        try:
            srbftp_intfce = self._get_srbftp()
        except:
            return -1,"Error initialising srbftp interface in copy_back_file!"
        
        srbftp_intfce.cd(self.job_parameters['srb_output_dir'])
        srbftp_intfce.get(remote_filename)

        if step.local_filename != remote_filename:
            os.rename(remote_filename,step.local_filename)
            
        return 0,"Retrived file %s from srb" % step.local_filename

    def _get_srbftp(self):
        """Return the srbftp object. If one doesn't exist create it"""
        
        if not self.srbftp:
            try:
                s = srbftp.srb_ftp_interface(self.job_parameters['srb_config_file'])
                self.srbftp = s
            except Exception,e:
                raise JobError,"Error getting srb_ftp_interface: %s" % e
                return None
            
        return self.srbftp
            
    def run_app(self,step,kill_on_error=None,**kw):
        """ This step covers rather a lot of tasks:
        
            1. Get any variables passed in when the step was added
            2. Write the MCS file
            4. Submit the MCS file
            5. Loop to check on the status of the job

            We don't kill this on error so that the output files are returned
            and the user can check what went wrong.
        """

        #1 update any variables we may have been passed
        # This may be redundant
        try:
            self.job_parameters['srb_input_dir'] = step.srb_input_dir
        except:
            pass
        try:
            self.job_parameters['srb_output_dir'] = step.srb_output_dir
        except:
            pass
        try:
            self.job_parameters['srb_executable']  = step.srb_executable
        except:
            pass
        try:
            self.job_parameters['srb_executable_dir'] = step.srb_executable_dir
        except:
            pass
        try:
            self.job_parameters['count'] = step.count
        except:
            pass
        
        # Make sure all the parameters have been set
        self._check_parameters()

        if step.stdin_file:
            if step.stdin_file not in self.job_parameters['inputfiles']:
                #self.input_files.append(step.stdin_file)
                self.job_parameters['inputfiles'].append(step.stdin_file)
        if step.stdout_file:
            if step.stdout_file not in self.job_parameters['outputfiles']:
                #self.output_files.append(step.stdout_file)
                self.job_parameters['outputfiles'].append(step.stdout_file)
        if step.stderr_file:
            if step.stderr_file not in self.job_parameters['outputfiles']:
                #self.output_files.append(step.stderr_file)
                self.job_parameters['outputfiles'].append(step.stderr_file)

        # Get the string with the mcs_file
        mcs_file = self._write_mcsfile(stdin=step.stdin_file,
                                       stdout=step.stdout_file)

        if self.debug:
            print "submitting job:"
            print mcs_file
        
        #Submit Job
        self.rmcs = rmcs.RMCS( self.job_parameters['rmcs_user'],
                               self.job_parameters['rmcs_password'])
        self.jobID = self.rmcs.submitJob( mcs_file,
                                     self.job_parameters['myproxy_user'],
                                     self.job_parameters['myproxy_password'],
                                     self.jobtype,
                                     False)

        #Monitor Job Information
        running = 1
        result = 1
        while running:
            info = self.rmcs.getJobDetails(self.jobID)
            # NB: info is a dictionary with the following structure:
            # message          prog running on lake.esc.cam.ac.uk
            # jobName          Jens Job
            # jobState         RUNNING
            # submitted        2006-09-05 14:45:08.868
            # jobID

            # Possible jobStates:
            # SUBMIT-PENDING
            # SUBMIT-FAILED
            # QUEING
            # RUNNING
            # FINISHED
            for key, val in info.items():
                print "%s \t %s" % (key, val)
                
            if info['jobState'] == 'FINISHED':
                msg = info['message']
                result = 0
                running = None
                break
            elif info['jobState'] == 'SUBMIT-FAILED':
                msg = info['message']
                result = -1
                running = None
                break
            
            time.sleep(self.poll_interval)

        return result,msg

    def _check_parameters(self):
        """Check that we have everything we need to run the job
           Raise a JobError if there is anything missing
        """
        for key,value in self.job_parameters.iteritems():
            if value == None:
                msg = "Cannot run job as parameter: <%s> has not been set!" % key
                raise JobError, msg

    def _write_mcsfile(self,stdin=None,stdout=None):
        """ Return  string containing the mcsfile"""
        
        # Write out the MCS file
        mcs_file = ''
        mcs_file+='Executable           = %s\n' % self.job_parameters['srb_executable']
        
        # Add stdin & stdout if necessary
        if stdin:
            mcs_file+='Input                = %s\n' % stdin
        if stdout:
            mcs_file+='Output               = %s\n' % stdout
            
        mcs_file+='notification         = NEVER\n'
        mcs_file+='GlobusRSL            = (job_type=single)\n'
        mcs_file+='pathToExe            = %s\n' % self.job_parameters['srb_executable_dir']
        
        # Buld up the machine list
        s = 'preferredMachineList = '
        for machine in self.job_parameters['machine_list']:
            s += ' %s ' % machine
        s += '\n'
        mcs_file+=s
        
        mcs_file+='jobType              = performance\n'
        mcs_file+='numOfProcs           = %s\n'% self.job_parameters['count']
        mcs_file+='Sforce               = true\n'
        mcs_file+='Sdir                = %s\n' % self.job_parameters['srb_input_dir']
        
        # Build up the list of input files
        s = 'Sget                 = '
        for ifile in self.job_parameters['inputfiles']:
            s += ' %s ' % ifile
        s += '\n'
        mcs_file+=s
        
        mcs_file+='Srecursive           = true\n'
        mcs_file+='Sdir                 = %s\n' % self.job_parameters['srb_output_dir']

        # Build up list of output files
        s = 'Sput                 = '
        for ofile in self.job_parameters['outputfiles']:
            s += ' %s ' % ofile
        s += '\n'
        mcs_file+=s
        
        mcs_file+='Queue\n'

        return mcs_file

    def kill(self):
        """ Kill the job if we are running. We either use the supplied kill command, or
            our own if one wasn't supplied
        """

        if self.active_step and self.active_step.kill_cmd:
                print 'running kill cmd for the current step'
                self.status = JOBSTATUS_KILLPEND
                self.active_step.kill_cmd()
                self.status = JOBSTATUS_KILLED
        elif self.active_step and not self.active_step.kill_cmd:
            print 'Running built-in kill for this step'
            self.status = JOBSTATUS_KILLPEND
            self.rmcs.cancelJob(self.jobId)
            self.status = JOBSTATUS_KILLED


class NordugridJob(Job):
    """Class for running job's on the Nordugrid"""
    def __init__(self,editor=None,**kw):
        apply(Job.__init__, (self,), kw)

        # Check the arclib module is available
        global arclib
        try:
            import arclib
        except ImportError:
            raise JobError,"Nordugrid job cannot be created as the arclib module cannot be imported!\n \
            Please make sure you have run the setp.sh script to set NORDUGRID_LOCATION, PYTHONPATH etc."

        # Now make sure that we have a valid proxy
        self.CheckProxy()
            
        # Looks like we are good to go...
        
        self.jobtype='Nordugrid Job'
        self.jobID = None # used to query the job status
        self.poll_interval = 30 # how often to check the job state in the loop

        
        # Variables that we use to write out the MCS file
        # Set to none so that we can check we have been passed them
        self.job_parameters = {}
        self.job_parameters['count'] = '1'
        self.job_parameters['inputfiles'] = {}
        self.job_parameters['outputfiles'] = {}
        self.job_parameters['outputfiles']["\"/\""]=None # Means keep everything
        self.job_parameters['executable'] = None
        self.job_parameters['arguments'] = None
        self.job_parameters['jobName'] = None
        self.job_parameters['stdin'] = None
        self.job_parameters['stdout'] = None
        self.job_parameters['stderr'] = None
        self.job_parameters['cpuTime'] = None
        self.job_parameters['wallTime'] = None
        self.job_parameters['memory'] = None
        self.job_parameters['disk'] = None
        self.job_parameters['runTimeEnvironment'] = None
        self.job_parameters['opsys'] = None
        self.job_parameters['gmlog'] = 'gmlog'
        self.job_parameters['architechture'] = None
        self.job_parameters['environment'] = {}

        # Update the defaults with anything that is in the rc_vars dict
        self.get_rcvars()

        if self.name:
            self.job_parameters['jobName'] = self.name
        else:
            self.name = "CCP1GUINordugridJob"
            self.job_parameters['jobName'] = self.name

        if self.debug:
            print "Nordugrid job iniited successfully"

    def CheckProxy(self):
        """ Check that the user has a valid proxy and throw an exception if not"""

        cert = arclib.Certificate(arclib.PROXY)
        if cert.IsExpired():
            raise JobError, "Your proxy is not available! Please run grid-proxy-init to create\n \
            a proxy with a lifetime sufficient for your job and then restart the CCP1GUI."
            return 1
        else:
            return None

#     def CreateRSL(self, rsl_dict=None):
#         """ Create a suitable rsl to run the job from the job_parameters and
#             the input and output files, executable, etc
#             Currently we only do equals - other operators will hjave to follow later
#         """

#         # Create a blank xrsl
#         xrsl = arclib.Xrsl(arclib.operator_and)
        
#         for key,value in self.job_parameters.iteritems():
#             rsl_name = key.replace('ngrid_','')
#             if value:
#                 if type(value) == list:
#                     pass
#                 elif type(value) == dict:
#                     # Dictionaries currently for input & outputfiles and environment variables
#                     # can all be handled in the same way
#                     if len(value) > 0:
#                         #xrsl_str += '(%s=' % rsl_name
#                         #for dkey,dvalue in value.iteritems():
#                         #    if dvalue == None:
#                         #        xrsl_str += '(\\"%s\\" \\"\\")' % dkey
#                         #    else:
#                         #        xrsl_str += '(\\"%s\\" \\"%s\\")' % ( dkey, dvalue )
#                         #xrsl_str += ')'
#                         pass
#                 else:
#                     try:
#                         xrsl.AddRelation( arclib.XrslRelation( rsl_name, arclib.operator_eq, value ),True)
#                     except Exception,e:
#                         raise JobError,"CreateRsl encountered error with: %s = %s\nError was: %s" % (key,value,e)

#         print "CreateRsl returning: ",xrsl
#         return xrsl


    def CreateRSL(self ):
        """ Create a suitable rsl string to run the job from the job_parameters and
            the input and output files, executable, etc
        """

        # Not used as we build up the xrsl using the relevant tools instead
        xrsl_string = '&'
        for rsl_name,value in self.job_parameters.iteritems():
            #rsl_name = key.replace('ngrid_','')
            #print "CreateRSL got: %s : %s" % (rsl_name,value)
            if value:
                if type(value) == list:
                    pass
                elif type(value) == dict:
                    # Dictionaries currently for input & outputfiles and environment variables
                    # can all be handled in the same way
                    if len(value) > 0:
                        xrsl_string += '(%s=' % rsl_name
                        for dkey,dvalue in value.iteritems():
                            if dvalue == None:
                                xrsl_string += '(%s "")' % dkey
                            else:
                                xrsl_string += '(%s %s)' % ( dkey, dvalue )
                        xrsl_string += ')'
                else:
#                    xrsl_string += '(%s=%s)' % (rsl_name,value)
                    xrsl_string += '(%s="%s")' % (rsl_name,value)

        print "CreateRsl xrsl_string is: ",xrsl_string

        try:
            xrsl = arclib.Xrsl( xrsl_string )
        #except Exception,e:
        except:
            raise JobError,"Nordugrid CreateRSL: supplied xrsl string was not valid!"

        return xrsl
    
    def GetTargets( self, xrsl ):
        """ Return a list of suitable targets based on the supplied xrsl_string"""

        if not xrsl:
            raise JobError,"GetTargets needs an xrsl!"

        try:
            targets = arclib.PrepareJobSubmission( xrsl )
        except Exception,e:
            raise JobError, "Nordugrid GetTargets hit problems preparing job submission!\n%s" % e
        except:
            raise JobError, "Nordugrid GetTargets hit problems preparing job submission!"

        #print "Nordugrid GetTargets returning"
        #for t in targets:
        #    print t
        return targets


    def Submit( self, xrsl, targets ):
        """Submit the job described by the xrsl to the list of machines in targets
           and return the jobid that identifies this job.
        """

        try:
            self.jobID = arclib.SubmitJob( xrsl, targets )
        except Exception,e:
            raise JobError,"Job Submission of job: <%s> failed!\n%s" % (xrsl,e)
        except:
            raise JobError,"Job Submission of job: <%s> failed!" % xrsl

        # Add job to ~/.ngjobs
        arclib.AddJobID( self.jobID, self.name )
        print "Submit submitted jobname %s as: %s" % (self.name, self.jobID )

        return self.jobID

    def GetJobInfo(self,jobid=None):
        """Get the job info for a job. Default is self.jobID unless we are
           supplied with a jobid
        """

        if jobid:
            myjobid = jobid
        else:
            if not self.jobID:
                raise JobError,"GetJobStatus Nordugrid - no valid jobID found!"
            myjobid = self.jobID

        try:
            jobinfo = arclib.GetJobInfo( myjobid )
        except Exception,e:
            raise JobError,"Nordugrid GetJobStaus error getting job info!\n%s"
        except:
            raise JobError,"Nordugrid GetJobStaus error getting job info!"

        return jobinfo

    def run_app(self,step,kill_on_error=None,**kw):
        """Setup the job, submit it, loop and query status"""

        print "Nordugrid run_app"
        if step.stdin_file:
            self.job_parameters['stdin'] = step.stdin_file
        if step.stdout_file:
            self.job_parameters['stdout'] = step.stdout_file
        if step.stderr_file:
            self.job_parameters['stderr'] = step.stderr_file

        xrsl = self.CreateRSL()
    
        machines = self.GetTargets( xrsl )
        if len(machines) == 0:
            raise JobError,"No suitable machines could be found to submit to for the job:\n%s" % xrsl
        
        #raise JobError,'No Way Dude!'
        self.Submit( xrsl, machines )

        running = 1
        message = 'None'
        result = 1
        while running:
            job_info = self.GetJobInfo()
            status = job_info.status
            print "got status",status
            # See nordugrid source: nordugrid/arclib/mdsparser.cpp
            statuses = ( 'FINISHED','KILLED','FAILED','CANCELLING','CANCELLING' )
            if status in statuses:
                running = None
                if status == 'FINISHED':
                    running = None
                    result = 0
                    message = "Job %s ran on cluster %s" % (job_info.job_name,
                                                            job_info.cluster)
                    break
                    #return result,message
                else:
                    running = None
                    result = -1
                    message = "Job %s ran on cluster %s" % (job_info.job_name,
                                                            job_info.cluster)
                    break
                    # Job failed in some way so bring back all the files for a postmortem
                    #self.copy_back_rundir()
                    #return result,message
            else:
                print "Nordugrid Job %s status is: %s" % (self.jobID,status)

            time.sleep(self.poll_interval)


        if result == -1:
            # Job failed in some way so bring back all the files for a postmortem
            self.copy_back_rundir()
            
        return result, message
        

    def copy_back_rundir(self,jobid=None):
        """Copy back the directory with all the output files in it.
           This often dies with: Leaked globus_ftp_control_t
        """
        if self.debug:
            print "Nordugrid copy_bck_rundir:"
            
        if jobid:
            myjobid = jobid
        else:
            if not self.jobID:
                raise JobError,"copy_back_rundir Nordugrid - no valid jobID found!"
            myjobid = self.jobID

        if self.name:
            job_name = self.name
        else:
            job_name = myjobid.split("/")[-1]

        dirname = os.getcwd()+ os.sep + job_name
        print "copy_back_rundir getting directory is ",myjobid
        print "directory will be ",dirname

        if os.access( dirname, os.F_OK):
            # Need to move any old job directories aside
            global backup_dir
            print "Old job directory %s exists. Moving it aside" %  dirname
            try:
                backup_dir( dirname )
            except Exception,e:
                raise JobError,"Nordugrid copy_back_rundir problem backing up %s!\n%s" % ( dirname,e )

            # Remove the old directory
            try:
                shutil.rmtree( dirname )
            except Exception,e:
                raise JobError,"Nordugrid copy_back_rundir error removing old rundirectory: %s!\n%s" % ( dirname,e )
        # Now create a directory for the files
        os.mkdir( dirname )

        try:
            ftpc = arclib.FTPControl()
        except Exception,e:
            raise JobError,"Nordugird copy_back_dir hit error initialising FTPControl!\n%s" %e
        except:
            raise JobError,"Nordugird copy_back_dir hit error initialising FTPControl!"

        print "downloading directory"
        print "ftpc.DownloadDirectory( \"%s\",\"%s\" )" %(  myjobid, dirname )

        try:
            ftpc.DownloadDirectory( myjobid, dirname )
        except Exception,e:
            raise JobError,"Nordugird copy_back_dir hit error during download!\n%s" %e
        except:
            raise JobError,"Nordugird copy_back_dir hit error during download!"

    def copy_out_file(self,step,kill_on_error=1):
        """Append the file to the list of files that are to be copied out"""

        if self.debug:
            print "Nordugrid copying out file: %s : %s" %( step.local_filename,step.remote_filename)
            
        if not step.remote_filename and not step.local_filename:
            return -1,"Nordugrid copy_out_file needs a filename!"

        if not step.remote_filename:
            remote_filename = None
        else:
            remote_filename = step.remote_filename

        self.job_parameters['inputfiles'][step.local_filename] = remote_filename

        return 0,"Appended %s to list of files to copy out" % step.local_filename


    def copy_back_file(self,step,kill_on_error=None):
        """Get the file back from Nordugrid and rename it if necessary"""

        if self.debug:
            print "Nordugrid copy_back_file: %s : %s" %( step.local_filename,step.remote_filename)
            
        if not step.remote_filename and not step.local_filename:
            return -1,"Nordugrid copy_back_file needs a filename!"

        if not step.remote_filename:
            remote_filename = step.local_filename
        else:
            remote_filename = step.remote_filename

        if not step.local_filename:
            local_filename = step.remote_filename
        else:
            local_filename = step.local_filename
            

        if not self.jobID:
            raise JobError,"Nordugrid copy_back_file error no valid jobID found!"

        try:
            ftpc = arclib.FTPControl()
        except Exception,e:
            raise JobError,"Nordugrid copy_back_file error intialising FTPControl!\n%s" % e
        except:
            raise JobError,"Nordugrid copy_back_file error intialising FTPControl!"
            
        rundir = self.jobID
        fileURL = rundir + "/" + remote_filename
        print "copy_back_file fileURL: %s" % fileURL
        local_filename = os.getcwd() + os.sep + os.path.basename( local_filename )
        print "copy_back_file local_filename: %s" % local_filename
            
        try:
            ftpc.Download( fileURL, local_filename )
        except Exception,e:
            raise JobError,"Nordugrid copy_back_file error retrieving file: %s\n%s" % (fileURL,e)
        except:
            raise JobError,"Nordugrid copy_back_file error retrieving file: %s" % fileURL
            
        return 0,"Retrived file %s from Nordugrid" % local_filename

    def kill(self):
        """ Kill the job if we are running. We either use the supplied kill command, or
            our own if one wasn't supplied
        """

        if self.active_step and self.active_step.kill_cmd:
                print 'running kill cmd for the current step'
                self.status = JOBSTATUS_KILLPEND
                self.active_step.kill_cmd()
                self.status = JOBSTATUS_KILLED
        elif self.active_step and not self.active_step.kill_cmd:
            print 'Running built-in kill for this step'
            self.status = JOBSTATUS_KILLPEND

            if not self.jobID:
                raise JobError,"kill Nordugrid Job - cannot find a jobID!"

            try:
                arclib.CancelJob( self.jobID )
            except Exception,e:
                raise JobError,"kill Nordugrid Job - error killing job!\n%s" % e
            except:
                raise JobError,"kill Nordugrid Job - error killing job!"
            
            self.status = JOBSTATUS_KILLED

    def clean( self, jobid=None ):
        """Clean (remove all external files) for the job. By default clean the job
           that is identified by the self.jobID unless we have been given a jobid as
           a keyword argument.
        """

        if jobid:
            myjobid = jobid
        else:
            if not self.jobID:
                raise JobError,"clean Nordugrid - no valid jobID found!"
            myjobid = self.jobID

        try:
            arclib.CleanJob( myjobid )
        except Exception,e:
            raise JobError,"Nordugrid clean error cleaning job: %s!\n%s" %( myjobid,e)
        except:
            raise JobError,"Nordugrid clean error cleaning job: %s " % myjobid
        
        try:
            arclib.RemoveJobID( myjobid)
        except Exception,e:
            raise JobError,"Nordugrid clean error removing jobID: %s\n%s" % (myjobid,e)
        except:
            raise JobError,"Nordugrid clean error removing jobID: %s" % myjobid

class JobError(RuntimeError):
    def __init__(self,args=None):
        self.args = args

if __name__ == "__main__":

    def testpy():
        i=j
        time.sleep(3)

    if 0:
        print 'testing remote foreground job'
        job = LoadLevelerJob('hpcx','psh')
        job.add_step(COPY_OUT_FILE,'transfer input',local_filename='small2.in')
        job.add_step(RUN_GAMESSUK,'run gamess',jobname='small2')
        job.add_step(COPY_BACK_FILE,'fetch log',remote_filename='small2.out')
        job.add_step(COPY_BACK_FILE,'fetch punch',remote_filename='small2.pun')
        job.add_step(PYTHON_CMD,'cleanup',proc=testpy)
        job.run()

    if 0:
        print 'testing exception'
        job = ForegroundJob()
        job.add_step(PYTHON_CMD,'cleanup',proc=testpy)
        job.run()
    
    if 0:
        print 'testing local background job (Windows)'
        job = BackgroundJob()
        job.add_step(DELETE_FILE,'kill old pun',remote_filename='small2.pun')
        job.add_step(COPY_OUT_FILE,'transfer input',local_filename='small2.in')
        gamess_exe = "c:\\python_dev\\ccp1gui\\exe\\gamess.exe"
        job.add_step(RUN_APP,'run gamess',local_command=gamess_exe,stdin_file='small2.in',stdout_file='small2.out')
        job.add_step(COPY_BACK_FILE,'fetch log',remote_filename='small2.out')
        job.add_step(COPY_BACK_FILE,'fetch punch',local_filename='small2.pun',remote_filename='ftn058')
        job.run()

    if 0:
        print 'testing local chemshell job (Windows)'
        import os
        os.environ['TCL_LIBRARY']='/usr/share/tcl8.4'
        os.environ['TCLLIBPATH']='/cygdrive/e/chemsh/tcl'
        chemshell_exe='"E:/chemsh/bin/chemshprog.exe"'
        job = ForegroundJob()
        job.add_step(DELETE_FILE,'kill old pun',remote_filename='small2.pun',kill_on_error=0)
        job.add_step(COPY_OUT_FILE,'transfer input',local_filename='small2.chm')
        job.add_step(RUN_APP_BASH,'run gamess',local_command=chemshell_exe,stdin_file='small2.chm',stdout_file='small2.out')
        #job.add_step(COPY_BACK_FILE,'fetch log',remote_filename='small2.out')
        #job.add_step(COPY_BACK_FILE,'fetch punch',local_filename='small2.pun',remote_filename='ftn058')
        job.run()
        print 'done'

    if 0:
        print 'testing rmcs job'
        rc_vars[ 'machine_list'] = ['lake.esc.cam.ac.uk']
        rc_vars[ 'count'] = '1'
        rc_vars['srb_config_file'] ='/home/jmht/srb.cfg'
        rc_vars['srb_executable'] = 'gamess'
        rc_vars['srb_executable_dir'] = '/home/jmht.eminerals/test/executables'
        rc_vars['srb_input_dir'] = '/home/jmht.eminerals/test/test1'
        rc_vars['srb_output_dir'] = '/home/jmht.eminerals/test/test1'
        rc_vars['rmcs_user'] = 'jmht'
        rc_vars['rmcs_password'] = '4235227b51436ad86d07c7cf5d69bda2644984de'
        rc_vars['myproxy_user'] = 'jmht'
        rc_vars['myproxy_password'] = 'pythonGr1d'
        
        job = RMCSJob()
        #job.add_step(DELETE_FILE,'kill old pun',remote_filename='small2.pun',kill_on_error=0)
        #job.add_step(COPY_OUT_FILE,'add srb file',local_filename='c2001_a.in', remote_filename='zoom.in')
        job.add_step(COPY_OUT_FILE,'add srb file',local_filename='c2001_a.in')
        job.add_step(RUN_APP,'run rmcs',stdin_file='c2001_a.in',stdout_file='c2001_a.out')
        #job.add_step(COPY_BACK_FILE,'Get srb results',local_filename='c2001_a.out')
        #job.add_step(COPY_BACK_FILE,'Get srb results',local_filename='c2001_a.out',remote_filename='output.txt')
        job.run()
        print 'rmcs done'

    if 1:
        print 'testing nordugrid job'
        
        #rc_vars[ 'machine_list'] = ['lake.esc.cam.ac.uk']
        #rc_vars[ 'ngrid_executable'] = '/bin/hostname' 
        #rc_vars['ngrid_stdout'] = 'jens.out'
        #targets = job.GetTargets( xrsl )
        #jobid = job.Submit( xrsl, targets )
        
        #rc_vars[ 'ngrid_executable'] = 'gamess'
        job = NordugridJob()
        job.copy_back_rundir( jobid = 'gsiftp://lheppc10.unibe.ch:2811/jobs/192241158660877746759701')
        
#         job.add_step(COPY_OUT_FILE,'Copying out files',local_filename='gamess')
#         job.add_step(COPY_OUT_FILE,'Copying out files',local_filename='SC4H4.in')
# #         #job.run()
# #         #xrsl = job.CreateRSL()
#         job.add_step(RUN_APP,'run nordugrid',stdin_file='SC4H4.in',stdout_file='SC4H4.out',executable='gamess')
#         job.add_step(COPY_BACK_FILE,'Copy Back Results',local_filename='SC4H4.out')
#         job.add_step(COPY_BACK_FILE,'Copy Back Results',local_filename='xxxx.ed3')
#         job.add_step(COPY_BACK_FILE,'Copy Back Results',local_filename='pun.ed3')
#         job.run()
#         job.clean()
        print 'end jens job'
