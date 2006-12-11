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

LocalJob(Job)
   based on subprocess.Spawn for the main step
            subprocess.Pipe for file operations

LocalJobNoSpawn(Job)
   all operations use subprocess.Pipe
   no way to kill this
 
RemoteJob(Job)
   subprocess.Spawn(plink/ssh)
   not yet implemented

RemoteBatchJob(RemoteJob):
   base class for handling remote queueing systems

LoadLevelerJob(RemoteBatchJob)
   not yet implemented

"""

import subprocess
import sys
import os
import re
import time
import shutil
import socket
from viewer.paths import backup_dir
from viewer.rc_vars import rc_vars

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
JOBSTATUS_STOPPED    = 'Stopped'
JOBSTATUS_DONE    = 'Done'
JOBSTATUS_SAVED   = 'Saved'

JOBCMD_KILL ='Kill'
JOBCMD_CANCEL ='Cancel'

LOCALHOST = socket.gethostname()

class JobStep:
    """A container class for an element of a job"""
    def __init__(self,type,name,
                 local_filename=None,
                 remote_filename=None,
                 cmd=None,
                 proc=None,
                 jobname=None,
                 local_command=None,
                 local_command_args = None,
                 remote_command=None,
                 remote_command_args=None,
                 stdin_file=None,
                 stdout_file=None,
                 stderr_file=None,
                 monitor_file=None,
                 warn_on_error=0,
                 kill_on_error=1,
                 kill_cmd=None,
                 use_bash=0):

        # see list of valid types above
        self.type = type
        # just a descriptor for following progress
        if name:
            self.name = name
        else:
            self.name = 'Not named'
            
        self.local_filename=local_filename
        self.remote_filename=remote_filename
        self.cmd=cmd
        self.jobname=jobname
        self.proc=proc
        self.local_command=local_command
        self.local_command_args=local_command_args
        self.remote_command=remote_command
        self.remote_command_args=remote_command_args
        self.stdin_file=stdin_file
        self.stdout_file=stdout_file
        self.stderr_file=stderr_file
        self.monitor_file=monitor_file
        self.kill_on_error=kill_on_error
        self.warn_on_error=warn_on_error
        self.kill_cmd=kill_cmd
        self.use_bash=use_bash

class Job:

    """Base class for jobs

    handles construction of the job as a list of steps

    """

    def __init__(self,name=None,**kw):

        self.steps=[]
        self.msg=""
        self.host = socket.gethostname()
        if name:
            self.name =name
        else:
             self.name ='Job'
             
        self.jobtype = None

        # This variable is displayed in the job editor and should be updated to show the status
        # of the job.
        self.status = JOBSTATUS_IDLE
        self.active_step = None
        self.process = None
        self.tidy = None
        self.monitor = None
        self.job_parameters = {}
        self.poll_interval = 5 # How often we should wait when checking the status of a
                               # running job or when trying to kill a job
        self.stopjob = None # Flag that is set to indicate if a running job should stop
        self.restart = None # Flag that should be set by a job that is stopped during a run
                            # so that the run method can react accordingly on a restart
        self.thread = None
        
        self.debug = None
        
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
        
    def  clear_steps(self):
        """Remove any old job steps"""
        if self.debug:
            print 'Clearing out old job steps'
        self.steps = []

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
            
            if self.stopjob:
                print "Stopping job at step ",self.step_number
                self.prepare_restart(in_step=None)
                return None
                
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
                    raise JobError, "Unknown job step type: %s" % step.type
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
                
            # if step returns 2 job has been stopped in the middle of a step
            elif code == 2:
                print "Job stopped while running step: %s : %s" %(self.step_number,step.name)
                self.prepare_restart(in_step=1)
                return None
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
            cmd = 'del'
            args =  [step.remote_filename]
        else:
            cmd = 'rm'
            args = [step.remote_filename]

        pipe=subprocess.Pipe(cmd,args=args,debug=self.debug)
        code = pipe.run()
        if code:
            msg = pipe.msg
        else:
            msg = None
        return code,msg

    def delete_local_file(self,step):
        """ Delete a file on the local filesystem"""

        if not step.local_filename:
            return -1,"delete_local_file needs a filename!"
        
        try:
            os.remove( step.local_filename)
            msg = "Removed local file: %s" % step.local_filename
            code = 0
        except OSError:
            msg = "Failed to remove local file: %s" % step.local_filename
            code = -1
        return code,msg

    def copy_out_file(self,step):
        data = open(step.local_filename, "rb").read()
        if not step.remote_filename:
            step.remote_filename = step.local_filename

        if sys.platform[:3] == 'win':

            if '\0' in data:
                print file, "BinaryFile!"
                cmd = 'C:/Program Files/PuTTY/pscp.exe'
                args = [step.local_filename,
                        self.remoteuser+'@'+self.host+':'+step.remote_filename]
            else:
                # translation between dos and windows formats if needed
                newdata = re.sub("\r\n", "\n", data)
                t = open('unx_'+step.local_filename,"wb")
                t.write(newdata)
                t.close()
                cmd = 'C:/Program Files/PuTTY/pscp.exe'
                args = ['unx_'+ step.local_filename,
                        self.remoteuser+'@'+self.host+':'+step.remote_filename]
        else:
                cmd = 'scp'
                args = [step.local_filename,
                        self.remoteuser+'@'+self.host+':'+step.remote_filename]

        print 'copy out cmd',[cmd] + args
        p = subprocess.Pipe(cmd,args=args,debug=self.debug)
        code = p.run()
        print 'copy out code',code
        return code,None

    def copy_back_file(self,step):
        print self.remoteuser
        print self.host
        print step.remote_filename
        if not step.local_filename:
            step.local_filename = step.remote_filename

        if sys.platform[:3] == 'win':
            cmd = 'C:/Program Files/PuTTY/pscp.exe'
            args = [self.remoteuser+'@'+self.host+':'+step.remote_filename,
                    step.local_filename]
        else:
            cmd = 'scp'
            args = [self.remoteuser+'@'+self.host+':'+step.remote_filename,
                    step.local_filename]

        p = subprocess.Pipe(cmd,args=args,debug=self.debug)
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
            self._kill()
            self.status = JOBSTATUS_KILLED
            
    def _kill(self):
        """Attempt to kill the job"""
        print 'Kill unimplemented for this job type'
        raise AttributeError,"_kill unimplemented for jobtype %s" % self.jobtype

    def get_status(self):
        """Return the current status of the job"""
        return self.status

    def update_job_parameters(self, job_dict=None):
        """Update the job parameters either from the rc_vars or from a
           a dictionary if one is supplied
           Only updates for variables that already exist as keys in the
           job_parameters dictionary are permitted.

        """

        if not job_dict:
            global rc_vars
            job_dict = rc_vars
            
        for key,value in self.job_parameters.iteritems():
            if job_dict.has_key( key ):
                self.job_parameters[key] = job_dict[key]
                
        if self.debug:
            print "job update_job_parameters: parameters are now:"
            print self.job_parameters

    def stop(self):
        """
        This is called from the job_manager thread (not the one the job is running in)
        Set flag to indicate job should stop and wait 2 poll intervals for the job to
        stop.
        This can be used in 2 ways, to stop a job between steps or to stop a job when it
        is actively running a step. To stop a job between steps, no changes need to be made
        to the job - self.poll_interval is set to 5s in the main job class and if after waiting
        for 2 of these intervals the job hasn't stopped it is considered unstoppable
        For steps that can be stopped while they are running, some form of the below code needs
        to be added to the method:
        
        if self.stopjob:
                print "run_app_loop got stop "
                self.status = JOBSTATUS_STOPPED
                self.restart = 1
                return 2, "Stopped Job"

        The job.run method uses the return code of 2 to tell it that the job has stopped during a step
        The run method can use the self.restart flag to make sure that any initialisation stuff is only
        called when the step is initiated and not when it is restarted after a save
        
        """

        # Don't think we need to wory about locks here as only this method ever sets this
        self.stopjob = 1

        # Wait for the job to stop
        for i in range(2):
            if self.status == JOBSTATUS_STOPPED:
                break
            time.sleep( self.poll_interval )

        if not self.status == JOBSTATUS_STOPPED:
            print "Job could not be stopped"
            return 1
        else:
            print "Job Stopped successfully"
            self.stopjob = None
            self.thread = None
            return None
            

    def prepare_restart(self,in_step=None):
        """Delete all the steps that have already been carried out. If we were stopped
        mid-step, keep the current step for a restart and set the restart flag"""

        print "preparing_restart"
        if in_step:
            self.restart = 1
            self.steps = self.steps[self.step_number-1:]
        else:
            self.steps = self.steps[self.step_number:]

class LocalJob(Job):
    """Sub class for a job running on the local resource
    run_app uses fork/winprocess via Spawn
    everything else uses os.popen3 via Pipe
    """

    def __init__(self,**kw):
        apply(Job.__init__, (self,), kw)
        self.jobtype=LOCALHOST

    def allocate_scratch(self,step):
        pass

    def copy_out_file(self,step):
        """overload generic function as this is a local job type"""
        if not step.remote_filename:
            step.remote_filename = step.local_filename

        # PS: this is windows specific? unix ('mv') code missing
        if step.local_filename != step.remote_filename:
            cmd = 'del'
            args = [step.remote_filename]
            subprocess.Pipe(cmd,args=args,debug=self.debug).run()
            cmd = 'ren'
            args = [step.local_filename, step.remote_filename]
            subprocess.Pipe(cmd,args=args,debug=self.debug).run()
        return 0,None

    def run_app(self,step):
        """execute command
        """

        if sys.platform[:3] == 'win':

            if step.use_bash:
                # We are running in a Cygwin shell rather than the standard
                # windows process 
                # THIS DOESNT WORK .. nospawn variant
                step.local_command_args = [step.local_command] + step.local_command_args
                step.local_command = 'bash'

            # Remove stdout
            if step.stdout_file:
                f = os.popen('del '+step.stdout_file)
                status2 = f.close()

            self.process = subprocess.Spawn(step.local_command,
                                            args=step.local_command_args,
                                            debug=self.debug)
            if self.debug:
                print "Background job win: run_app cmd: ",self.process.cmd_as_string()
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
            self.process = subprocess.Spawn(step.local_command,
                                            args=step.local_command_args,
                                            debug=self.debug)
            if self.debug:
                print "Background job: run_app cmd: ",self.process.cmd_as_string()

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

    def copy_back_file(self,step):
        """ This provides a rename function when used in a local job"""

        if not step.local_filename:
            step.local_filename = step.remote_filename

        if step.local_filename != step.remote_filename:
            if sys.platform[:3] == 'win':
                cmd = 'ren'
                args = [step.remote_filename,step.local_filename]
                code = subprocess.Pipe(cmd,args=args,debug=self.debug).run()
                if code:
                    raise JobError, "failed to recover " +  step.remote_filename
            else:
                cmd = 'mv'
                args = [step.remote_filename,step.local_filename]
                code = subprocess.Pipe(cmd,args=args,debug=self.debug).run()
                if code:
                    raise JobError, "failed to recover " +  step.remote_filename
        return 0,None

    def clean_scratch(self,step):
        # Null function here
        return 0,None

    def _kill(self):

        if self.process:
            print 'attempting to kill process'
            self.status = JOBSTATUS_KILLPEND
            code = self.process.kill()
            print 'kill return code',code
            self.status = JOBSTATUS_KILLED
            return code
        else:
            return -1
    
class LocalJobNoSpawn(LocalJob):
    """Sub class for a job running on the current resource
    this is simply for testing, no threads or background spawn calls
    it uses the subprocess.Pipe to invoke the required calls
    """

    def __init__(self,**kw):
        apply(Job.__init__, (self,), kw)
        self.jobtype='Local Foreground'
        
    def allocate_scratch(self,step):
        return 0,None

    def run_app(self,step):

        if step.use_bash:

            cmd = step.local_command
            for arg in step.local_command_args:
                cmd = cmd + ' ' + arg
            if step.stdin_file:
                cmd = cmd + ' < '+ step.stdin_file
            if step.stdout_file:
                cmd = cmd + ' > ' + step.stdout_file
            file=open("bash.txt","wb")
            file.write(cmd)
            file.close()

            cmd="C:/cygwin/bin/bash.exe"
            args= ['<','bash.txt']
            p = subprocess.Pipe(cmd,args=args,debug=self.debug)
            code = p.run()

            return code,None

        else:

            cmd = step.local_command
            args = step.local_command_args

            if step.stdin_file:
                if not args:
                    args=[]
                args.append('<')
                args.append(step.stdin_file)
            if step.stdout_file:
                if not args:
                    args = []
                args.append('>')
                args.append(step.stdout_file)

            #print 'checking path'
            #p = subprocess.Pipe("echo $PATH",debug=self.debug)
            #code = p.run()        

            p = subprocess.Pipe(cmd,args=args,debug=self.debug)
            if self.debug:
                print 'ForegroundJob: cmd=',p.cmd_as_string()
            code = p.run()
            if code:
                print 'code from run_app',code
                print 'step.error',p.error
                print 'step.msg',p.msg
                return code, p.msg
            else:
                return 0, None


class RemoteJob(Job):
    """Base Class for jobs on remote systems accessible by ssh
    access. This class implements scratch file management
    and file transfer functions.
    Also allows a job to run as a remote foreground process (ssh)
    on the target system.
    """
    def __init__(self,host,remoteuser,**kw):
        apply(Job.__init__, (self,), kw)
        self.jobtype='Remote'
        self.host=host
        self.remoteuser=remoteuser

    def run_app(self,step):
        p = subprocess.PipeRemoteCmd(self.host,self.remoteuser,step.remote_command,step.remote_command_args)
        code=p.run()
        return code,None

class RemoteBatchJob(RemoteJob):
    """Instantiate the job using rsh/plink but in this case, the job
    has will be started in a batch queue and the run() method will
    exit only when the job has been run (or rejected) by the queue
    manager.
    Details of specific job managers are handled in the derived classes.
    """

    def __init__(self,host,remoteuser, **kw):
        apply(Job.__init__, (self,), kw)
        self.jobtype='BatchBase'
        self.jobID = None # used to query the job status
        self.poll_interval = 30 # how often to check the job state in the loop

    def run_app(self,step):
        print 'run_app method of RemoteBatchJob should be overloaded'


class LoadLevelerJob(RemoteBatchJob):
    """Class for a local loadleveler job"""
    def __init__(self,host,remoteuser,**kw):
        RemoteBatchJob.__init__(self,**kw)
        self.jobtype='LoadLeveler'

    def allocate_scratch(self,step):
        return 0,None

    def run_app(self,step):

        # ? remote working directory

        # Construct Loadleveler job file and
        # copy it over to the target host

        # Submit job 

        #Monitor Job Information
        running = 1
        result = 1
        while running:

            # Use llstatus


            #info = self.rmcs.getJobDetails(self.jobID)
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

    def clean_scratch(self,step):
        return 0,None


class RMCSJob(Job):
    """Class for running job's using Rik's Remote MyCondorSubmit"""
    def __init__(self,**kw):

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

        self.jobtype='RMCS'
        self.jobID = None # used to query the job status
        self.poll_interval = 30 # how often to check the job state in the loop
        self.srbftp = None
        self.rmcs = None
        
        # Variables that we use to write out the MCS file
        # Set to none so that we can check we have been passed them
        self.job_parameters['hosts'] = None
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

        #self.update_job_parameters()
            
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
        if step.local_filename not in self.job_parameters['inputfiles']:
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

        if not step.local_filename:
            local_filename = step.remote_filename
        else:
            local_filename = step.local_filename
            
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

        if local_filename != remote_filename:
            os.rename(remote_filename,local_filename)
            
        return 0,"Retrived file %s from srb" % local_filename

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

        if not self.restart:
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
                print
                print "rmcs_user: %s" % self.job_parameters['rmcs_user']
                print "rmcs_password: %s" % self.job_parameters['rmcs_password']

            #raise JobError,"Not on your nelly squire!"
            try:
                self.rmcs = rmcs.RMCS( self.job_parameters['rmcs_user'],
                                       self.job_parameters['rmcs_password'])
            except Exception,e:
                msg =  "Exception while creating rmcs:\n%s" % e
                raise JobError,msg

            try:
                self.jobID = self.rmcs.submitJob( mcs_file,
                                                  self.job_parameters['myproxy_user'],
                                                  self.job_parameters['myproxy_password'],
                                                  self.jobtype,
                                                  False)
            except Exception,e:
                msg = None
                try:
                    faultstring = e.faultstring
                except AttributeError:
                    pass
                else:
                    if faultstring == 'Authentication Failed':
                        msg =  "There was an Authentication Error on submitting your job!\n" +\
                              "Please check that your password is correct for the user: %s" % self.job_parameters['rmcs_user']
                    else:
                        msg = "There was an Error on submitting your job!\n" +\
                              "The soap faultstring is: %s" %  faultstring

                if not msg:
                    msg = "There was an error submitting your job! The error returned was:\n%s" % e

                raise JobError,msg

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
            # JOB-FAILED
            for key, val in info.items():
                print "%s \t %s" % (key, val)
                
            if info['jobState'] == 'FINISHED':
                msg = info['message']
                result = 0
                running = None
                break
            elif info['jobState'] in ['SUBMIT-FAILED','JOB-FAILED'] :
                msg = info['message']
                result = -1
                running = None
                break
            else:
                self.status = info['jobState']
            
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

        if len(self.job_parameters['hosts']) == 0:
            raise JobError,"RMCS needs at least one host to run on!\nPlease select a host in the job submission editor."


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

        # Determine job type
        if len(self.job_parameters['count']) > 1:
            job_type = 'mpi'
        else:
            job_type = 'single'
        mcs_file+='GlobusRSL            = (job_type=%s)\n' % job_type
        
        mcs_file+='pathToExe            = %s\n' % self.job_parameters['srb_executable_dir']
        
        # Buld up the machine list
        s = 'preferredMachineList = '
        for machine in self.job_parameters['hosts']:
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
        
        mcs_file+='Srecurse             = true\n'
        mcs_file+='Sdir                 = %s\n' % self.job_parameters['srb_output_dir']

        # Build up list of output files
        s = 'Sput                 = '
        for ofile in self.job_parameters['outputfiles']:
            s += ' %s ' % ofile
        s += '\n'
        mcs_file+=s
        
        mcs_file+='Queue\n'

        return mcs_file

    def _kill(self):
        """ Kill the job if we are running. We either use the supplied kill command, or
            our own if one wasn't supplied
        """
        self.rmcs.cancelJob(self.jobID)


class GridJob(Job):
    """ Base class for Grid jobs - defines various methods and data structures
        that should be common to most grid jobs.
        """
    def __init__(self,**kw):
        Job.__init__(self)

        self.host = None # Always set this to None here - only set to something when we have the host
        self.jobtype='Grid'
        self.jobID = None # holds the url of the job
        self.poll_interval = 10 # How often we should poll for the job status when running
        self.gsissh_port = 2222
        
        self.job_parameters = {} # Dictionary of job parameters for Nordugrid, RMCS, Growl etc jobs
        self.job_parameters['hosts'] = None
        self.job_parameters['count'] = '1'
        self.job_parameters['executable'] = None
        self.job_parameters['jobName'] = None
        self.job_parameters['jobtype'] = None
        self.job_parameters['stdin'] = None
        self.job_parameters['stdout'] = None
        self.job_parameters['stderr'] = None
        self.job_parameters['directory'] = None
        self.job_parameters['environment'] = {}

        # This is a list of all parameters that are usable in the CreateRSLString method
        # Only ones that are universally used should be added here, others should be added
        # by the relevant init method
        self.xrsl_parameters = ['arguments',
                                'count',
                                'cpuTime',
                                 'directory',
                                 'executable',
                                 'environment',
                                 'jobName',
                                 'jobtype',
                                 'stdin',
                                 'stdout',
                                 'stderr',
                                'wallTime'
                                ]
            

    def CheckProxy(self):
        """ Check that the user has a valid proxy and throw an exception if not"""
        cmd = 'grid-proxy-info'
        arg = '-e'
        ret = os.spawnlp(os.P_WAIT, cmd, cmd, arg )
        if ret:
            raise JobError, "Your proxy is not available! Please run grid-proxy-init to create\n \
            a proxy with a lifetime sufficient for your job."
        else:
            if self.debug:
                print "Proxy server is o.k."
            return None

    def CreateRSLString(self):
        """ Create a suitable rsl string to run the job from the job_parameters and
            the input and output files, executable, etc
            To save including all the job parameters in the xrsl string, we use the xrsl_variables
            list to determine which are valid.
        """

        # Not used as we build up the xrsl using the relevant tools instead
        #xrsl_string = '&'
        xrsl_string = ''
        for rsl_name,value in self.job_parameters.iteritems():
            #rsl_name = key.replace('ngrid_','')
            #print "CreateRSL got: %s : %s" % (rsl_name,value)
            if rsl_name not in self.xrsl_parameters:
                # Not a valid parameter so skip it
                continue
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
                    #xrsl_string += '(%s=%s)' % (rsl_name,value)
                    xrsl_string += '(%s="%s")' % (rsl_name,value)

        if self.debug:
            print "CreateRsl xrsl_string is: ",xrsl_string
        return xrsl_string



class GrowlJob(GridJob):
    """Class for running jobs with GROWL:
       http://www.growl.org.uk/

       Check we have a host to run on (len hosts)
       Get the path to the users home directory: grid-pwd
       
    """
    def __init__(self,**kw):
        GridJob.__init__(self)

        self.jobtype = 'GROWL'
        self.job_parameters['remote_home'] = None
        self.job_parameters['user_remote_dir'] = None # directory specified by the user
        self.job_parameters['directory'] = None # The full path to the working directory on the
                                                # remote machine (derived from user_remote_dir)
                                                
        self.job_parameters['jobmanager'] = None
        self.job_parameters['count'] = 1
        self.job_parameters['hosts'] = []

        # Make sure that the growl environment is set up:
        self.check_growl()
        
        # Now make sure that we have a valid proxy
        self.CheckProxy()
        self.debug=1


    def check_growl(self):
        """ Make sure that Growl has been set up and we can access the programmes we need to"""

        try:
            growl_home = os.environ['GROWL_HOME']
        except KeyError:
            raise JobError,"Cannot find environment variable GROWL_HOME!\n" +\
                  "Please run the command \". setup.sh\" in your Growl directory\n"+\
                  "and then restart the CCP1GUI."
    
    def get_host(self):
        """Return the name of the host that we are running on """

        if len( self.job_parameters['hosts'] ) != 1:
            raise JobError, "GrowlJob needs a single hostname to run job on!\nGot: %s" % self.job_parameters['hosts']
        
        self.host = self.job_parameters['hosts'][0]
        return self.host

    def get_remote_homedir(self):
        """Get the path to the home directory on the target machine """

        if self.debug:
            print "Getting remote_home_dir"

        if not self.job_parameters['remote_home']:
            host = self.get_host()
            #homedir = self.run_command( 'grid-pwd', args=[host] )
            homedir = self.grid_pwd( host )
            self.job_parameters['remote_home'] = homedir
        else:
            homedir = self.job_parameters['remote_home']
            
        if self.debug:
            print "Growl get_remote_homedir returning: %s" %  homedir
        return homedir

    def get_remote_dir(self):
        """Get full path to the working directory on the target machine.
           self.job_parameters['remote_dir'] should be None the first time
           this function is called so we set this on the first call.
           Subsequent calls just retrieve the value from the dictionary.
          
        """

        if not self.job_parameters['directory']:
            # Need to work out the path
            homedir = self.get_remote_homedir()
            if not self.job_parameters['user_remote_dir']:
                # Working in home directory
                remote_dir =  homedir+"/"
                self.job_parameters['directory'] = remote_dir
            else:
                # User has specified a working directory
                remote_dir = self.job_parameters['user_remote_dir']
                if remote_dir[-1] != "/": # Ensure there is a trailing slash
                    remote_dir += "/"
                if remote_dir[0] == "/": # Absolute path
                    self.job_parameters['directory'] = remote_dir
                else: # Relative path
                    if remote_dir[0] == "~":
                        remote_dir = remote_dir[1:]
                    remote_dir = homedir+"/"+remote_dir
                    self.job_parameters['directory'] = remote_dir
        else:
            remote_dir = self.job_parameters['directory']

        if self.debug:
            print "get_remote_dir returning: %s" % remote_dir
        return remote_dir


    def _run_command( self, command, args=None ):
        """Use subprocess Spawn to run a command and get the output and error
        """

        assert type(command) == str,"GrowlJob,_run_command command must be a string: %s" % command
        if args:
            cmd_string= command + ' ' + ' '.join(args)
        else:
            cmd_string = command
            
        if self.debug:
            print "GrowlJob _run_command running: %s" % (cmd_string)
            
        p = subprocess.Spawn( command, args=args ,debug=None)
        p.run()
        ret = p.wait()
        if ret < 0:
            raise JobError,"GrowlJob Error running command: %s!" % cmd_string
        
        output = p.get_output()
        if type(output) == str:
            # If it's multi-line we need to split it up
            output = output.split('\n')
        error = p.get_error()
        if type(error) == str:
            # If it's multi-line we need to split it up
            error = error.split('\n')

        return output,error

    def check_common_errors(self,output,error,command=None):
        """ Check the output and error streams for known common errors and raise
            a JobError if we encounter one
        """

        if not command:
            command = "No command name specified"
            
        # Concatenate output and error for the time being
        if output and error:
            output = output + error
        if not output:
            output = error

        # maps common error re's to the string we use when we raise the JobError
        # we cycle through this before we do owt to pick out any general errors we know about
        common_errors = {
            re.compile("Usage error:") : "Usage error for %s:\n%s" % (command,output),
            re.compile("Permission denied") : "Proxy Error for command: %s\nPlease run grid-proxy-init" % (command),
            re.compile(".*Name or service not known") : "Cannot contact machine!\n%s" % output,
            re.compile(".*cannot parse RSL stub") : "Supplied RSL was not valid!\n%s" % output,
            re.compile(".*No such file or directory") : "Cannot find file on remote machine!\n%s" % output,
            re.compile("GRAM Job submission failed") : "Job submission failed!\n%s" % output
            }

        if self.debug:
            print "check_common_errors command: %s" % command
            print "check_common_errors output: %s" % output

        # Check for any common errors
        for line in output:
            for error,msg in common_errors.iteritems():
                if error.match( line ):
                    raise JobError,msg

    def grid_which(self,host,executable):
        """Get the full path to the command on the remote machine"""

        assert type(host) == str and type(executable) == str,"Growl grid_which: args must be strings!"
        output,error = self._run_command( 'grid-which',args = [host,executable] )
        self.check_common_errors( output, error, command='grid-which' )

        m = None
        dir_re = re.compile("(^/\S*)") # group starts with / then anything that's not white space
        for line in output:
            m = dir_re.match( line )
            if m:
                return m.group(1)
        if not m:
            # We can't find it so return None so we can try and work out the full path ourselves
            return None

    def grid_pwd(self,host):
        """Return the home directory on the remote machine """

        output,error = self._run_command( 'grid-pwd',args = [host] )

        self.check_common_errors( output, error, command='grid-pwd' )

        # Re to check for the string we are after
        dir_re = re.compile("(^/\S*)") # group starts with / then anything that's not white space
        match = None
        for line in output:
            match = dir_re.match( line )
            if match:
                if self.debug:
                    print "grid_pwd returning: %s " % match.group(1)
                return match.group(1)
        if not match:
            raise JobError,"GrowlJob parse_output: grid-pwd failed!\n%s" % output
        

    def grid_cp(self,args):
        """Copy file a remote file"""

        output,error = self._run_command( 'grid-cp',args = args )
        self.check_common_errors( output, error, command='grid-cp' )
        # Need to add more specific error checking

    def grid_rm(self,host,file):
        """Remove a remote file"""

        output,error = self._run_command( 'grid-rm',args = [host,file] )
        self.check_common_errors( output, error, command='grid-rm' )
        # Need to add more specific error checking

    def grid_kill(self,jobID=None):
        """Kill a remote job"""

        if not jobID:
            jobID = self.jobID
            if not jobID:
                raise JobError,"grid-kill cannot find a valid job id!"

        output,error = self._run_command( 'globus-job-cancel',args = ['-force',jobID] )
        self.check_common_errors( output, error, command='grid-kill' )
        # Need to add more specific error checking

    def grid_status(self,url):
        """ Get the status of the  running job identified by the url supplied"""
        
        output,error = self._run_command( 'grid-status',args = [url] )
        self.check_common_errors( output, error, command='grid-status' )

        m = None
        stat_re = re.compile("(UNSUBMITTED|DONE|FAILED|ACTIVE|PENDING)") # Group is the any of the accepted stati
        for line in output:
            m = stat_re.match( line )
            if m:
                return m.group(1)
        # Only get here if we don't get a match
        raise JobError,"GrowlJob grid-staus got unrecognised output!\n%s" % output

    def grid_get_jobmanager(self,host):
        """See if we can determine the job manager on the remote machine
           If we can't we just return None
        """

        output,error = self._run_command( 'grid-get-jobmanager',args = [host] )
        self.check_common_errors( output, error, command='grid-get-jobmanager' )
        
        m = None
        # Need to add more specific error checking
        jman_re = re.compile("(^jobmanager-.*)") # group starts with / then anything that's not white space
        for line in output:
            m = jman_re.match( line )
            if m:
                return m.group(1)
        if not m:
            #raise JobError,"GrowlJob parse_output: grid-get-jobmanager could not find jobmanger!\n%s" % output
            print "GrowlJob parse_output: grid-get-jobmanager could not find jobmanger!\n%s" % output
            return None

    def grid_submit(self,host,rsl_string,executable,jobmanager=None):
        """
        Use globus-job-submit to submit a job
        """
        if jobmanager:
            host = host + "/" + jobmanager

        args = [ host, '-x', rsl_string, executable ]
        #print "running: globus-job-submit %s" % args
        #raise JobError,"Submit? I think not"
        output,error = self._run_command( 'globus-job-submit',args = args )
        self.check_common_errors( output, error, command='globus-job-submit' )

        m = None
        url_re = re.compile("(^https://.*)") # Group is the url string
        for line in output:
            m = url_re.match( line )
            if m:
                return m.group(1)
        if not m:
            raise JobError,"GrowlJob parse_output: grid-submit could not find returned url!\n%s" % output


    def job_cancel(self):
        """Cancel the current job"""

        if not self.jobID:
            raise JobError,"Growl job_cancel - no jobID!"

        args = ['-force',self.jobID]
        output,error = self._run_command( 'globus-job-cancel',args = args )
        self.check_common_errors( output, error, command='globus-job-cancel' )

        m = None
        url_re = re.compile("(Job canceled.)") # Group is the url string
        for line in output:
            m = url_re.match( line )
            if m:
                return m.group(1)
        if not m:
            #raise JobError,"GrowlJob cancel_job: error cancelling job!\n%s" % output
            print "GrowlJob cancel_job: error cancelling job!\n%s" % output
            return None


    def copy_out_file(self,step,kill_on_error=1):
        """ Copy out the file to the resource.
        """
        
        if not step.local_filename or not os.access( step.local_filename,os.R_OK ):
            return -1,"copy_out_file error accessing file: %s!" % step.local_filename
        
        host = self.get_host()
        path = self.get_remote_dir()

        # Format is similar to scp e.g. <local_file> <host>:<remote_path>
        args = [step.local_filename]
        if step.remote_filename:
            args.append( "%s:%s" % (  host, path+step.remote_filename ) )
        else:
            args.append( "%s:%s" % (  host, path+step.local_filename ) )

        if self.debug:
            print "GrowlJob copy_out_file running: %s" % 'grid-cp '+' '.join(args)
            
        self.grid_cp( args )
            
        return 0,"Copied file %s to %s" % (step.local_filename,host)

    def copy_back_file(self,step,kill_on_error=0):
        """ Copy out the file to the resource.
        """
        if self.debug:
            print "Growl copy_back_file: %s : %s" %( step.local_filename,step.remote_filename)
            
        if not step.remote_filename and not step.local_filename:
            return -1,"copy_back_file needs a filename!"

        if not step.remote_filename:
            remote_filename = step.local_filename
        else:
            remote_filename = step.remote_filename

        if not step.local_filename:
            local_filename = step.remote_filename
        else:
            local_filename = step.local_filename

        host = self.get_host()
        path = self.get_remote_dir()
        args = []
        args.append( "%s:%s" % ( host, path+remote_filename ))
        args.append( local_filename )

        if self.debug:
            print "GrowlJob copy_back_file running: %s" % 'grid-cp '+ ' '.join(args)

        self.grid_cp( args )
        
        #if local_filename != remote_filename:
        #    os.rename(remote_filename,local_filename)
            
        return 0,"Copied file %s from %s" % (step.local_filename,host)

    def delete_file(self,step):
        """ Delete a file on the remote machine
        """

        if not step.remote_filename:
            return -1,"GrowlJob delete_file needs a remote filename!"
        
        host = self.get_host()
        path = self.get_remote_dir() + step.remote_filename
        #ret = self.run_command('grid-rm',args=[host,path])
        
        code = -1
        msg = "Delete of remote file: %s failed!" % step.remote_filename
        try:
            ret = self.grid_rm(host,path)
            code = 0
            msg = "Deleted remote file: %s" % step.remote_filename
        except:
            pass
            
        return code,msg

    def run_app(self,step,kill_on_error=None,**kw):        
        """Submit the Growl Job using globus-job-submit
           We need to build up a string suitable for globus-job-submit of the form:
           globus-job-submit <hostname>/<jobmanager> -x <xrsl_string> <executable_path>
        
        """
        if not self.restart:
            self.submit(step)

        print "run_app Growl"

        # Loop to check status
        code = 0
        fin_stat = ['DONE', 'FAILED']
        running = 1
        while running:
            
            if self.stopjob:
                print "Growl run_app_loop got stop request"
                self.status = JOBSTATUS_STOPPED
                self.restart = 1
                code = 2
                ret = "Job stopped at user request"
                break
            
            ret = self.grid_status( self.jobID )
            if ret in fin_stat:
                if ret == 'FAILED':
                    code = -1
                break
            else:
                print "Growl job setting status to ",ret
                self.status = ret
                time.sleep( self.poll_interval )
                continue

        return code,ret


    def get_executable(self):
        """Return the correct executable name on the remote machine if we can work it out
           or None if we can't find it.
        """

        if not self.job_parameters['executable']:
            return None
        else:
            executable = self.job_parameters['executable']

        print "executable ",executable
        # If the exectuable begins with a slash assume it's an absolute path and return it
        if executable[0] == os.sep:
            print "full path"
            return executable

        # See if the executable is in the path
        host = self.get_host()
        path = self.grid_which(host,executable)
        if not path:
            # exe not in path, so we guess it's in the working directory we've been given
            remote_dir = self.get_remote_dir()
            return remote_dir + executable
        else:
            return path
    
    def submit(self,step):
        """ Prepare the job and then submit it"""

        remote_dir = self.get_remote_dir()

        # Set up any parameters so that we get a suitable rsl string when we call
        # CreateRSLString        
        if step.stdin_file:
            path = remote_dir+step.stdin_file
            self.job_parameters['stdin'] = path
        if step.stdout_file:
            path = remote_dir+step.stdout_file 

            self.job_parameters['stdout'] = path
        if step.stderr_file:
            path = remote_dir+step.stderr_file 
            self.job_parameters['stderr'] = path

        executable = self.get_executable()
        if not executable:
            raise JobError,"GrowlJob run_app needs an executable to run!"
        else:
            # Hack - need to null this so it doesn't end up in the rsl_string
            self.job_parameters['executable'] = None

        host = self.get_host()
        rsl_string = self.CreateRSLString()

        # Probably best to run with the default jobmanager
        # jobmanager = self.grid_get_jobmanager(host)
        if self.job_parameters['jobmanager']:
            jm = self.job_parameters['jobmanager']
        else:
            jm = None
        
        #raise JobError,"Noooooooo!!!!"
        self.jobID = self.grid_submit( host, rsl_string, executable, jobmanager=jm )
        print "job submitted: %s" % self.jobID
        return self.jobID

    def _kill(self):
        """ kill the job """
        
        self.grid_kill()
        
class NordugridJob(GridJob):
    """Class for running job's on the Nordugrid using ARCLIB:
       http://www.nordugrid.org
    """
    def __init__(self,**kw):
        GridJob.__init__(self)

        # Import the arclib modules
        self.init_arclib()
        
        # Now make sure that we have a valid proxy
        self.CheckProxy()
            
        # Looks like we are good to go...
        self.jobtype='Nordugrid'
        
        # See nordugrid source: nordugrid/arclib/mdsparser.cpp
        self.jobstat_finished = ( JOBSTATUS_KILLED, 'FINISHED','KILLED','FAILED','CANCELLING','CANCELLING' )
        
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

        xrsl_parameters = ['inputfiles','outputfiles','arguments','memory','disk','runTimeEnvironment',
                           'opsys','architechture','environment','gmlog']
        self.xrsl_parameters = self.xrsl_parameters + xrsl_parameters

        # Update the defaults with anything that is in the rc_vars dict
        #self.update_job_parameters()

        if self.name:
            self.job_parameters['jobName'] = self.name
        else:
            self.name = "CCP1GUINordugridJob"
            self.job_parameters['jobName'] = self.name

        if self.debug:
            #arclib.SetNotifyLevel(arclib.VERBOSE)
            arclib.SetNotifyLevel(arclib.INFO)
            #print "Nordugrid job inited successfully"

    def init_arclib(self):
        """ Check the arclib module is available """
        global arclib
        try:
            import arclib
        except ImportError:
            raise JobError,"Nordugrid job cannot be created as the arclib module cannot be imported!\n \
            Please make sure you have run the setup.sh script to set NORDUGRID_LOCATION, PYTHONPATH etc."


#     BELOW TWO METHODS ARE BROKEN with ARLIB < 0.5.56

#     def CheckProxy(self):
#         """ Check that the user has a valid proxy and throw an exception if not"""

#         cert = arclib.Certificate(arclib.PROXY)
#         if cert.IsExpired():
#             raise JobError, "Your proxy is not available! Please run grid-proxy-init to create\n \
#             a proxy with a lifetime sufficient for your job."
#             return 1
#         else:
#             return None

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


    def CreateRSL(self):
        """ Create the RSL for the Nordugrid job (using the GridJob CreateRSLString method)
        """

        # Not used as we build up the xrsl using the relevant tools instead
        xrsl_string = self.CreateRSLString()
        xrsl_string = '&'+xrsl_string
        
        try:
            xrsl = arclib.Xrsl( xrsl_string )
            return xrsl
        #except arclib.ARCLibError,e:
        #    raise JobError,"Nordugrid CreateRSL: supplied xrsl string was not valid!\n%s" % e
        except Exception,e:
            raise JobError,"Nordugrid CreateRSL: supplied xrsl string was not valid!\n%s" % e
        except:
            raise JobError,"Nordugrid CreateRSL: supplied xrsl string was not valid!"

    def GetTargets( self, xrsl ):
        """ Return a list of suitable targets based on the supplied xrsl_string"""

        if not xrsl:
            raise JobError,"GetTargets needs an xrsl!"

        try:
            targets = arclib.PrepareJobSubmission( xrsl )
#        except arclib.ARCLibError,e:
#            raise JobError, "Nordugrid GetTargets hit problems preparing job submission!\n%s" % e
        except Exception,e:
            raise JobError, "Nordugrid GetTargets hit problems preparing job submission!\n%s" % e
        except:
            raise JobError, "Nordugrid GetTargets hit problems preparing job submission!"

        if self.debug:
            print "Nordugird GetTargets returning:"
            print targets

        return targets

    def Submit( self, xrsl, targets ):
        """Submit the job described by the xrsl to the list of machines in targets
           and return the jobid that identifies this job.
        """

        try:
            self.jobID = arclib.SubmitJob( xrsl, targets )
#        except arclib.ARCLibError,e:
#            raise JobError,"Job Submission of job: <%s> failed!\n%s" % (xrsl,e)
        except Exception,e:
            raise JobError,"arclib job submission of job: <%s> failed!\n%s" % e
        except:
            raise JobError,"arclib job submission failed!"

        # Add job to ~/.ngjobs
        #arclib.AddJobID( self.jobID, self.name )
        if self.debug:
            print "Submit submitted jobname %s as: %s" % (self.name, self.jobID )
        return self.jobID

    def SubmitInSeparateProcess(self,xrsl):
        """
          Due to a problem with the querying of targets and submission needs to be run as two
          seperate processes as Python is not thread safe and the arclib library does not
          explicitly release the Global Interpereter Lock (GIL) when it queries the network,
          so the job thread will hang everything while it waits for the network call to return.
       """

        # Create a file we can used for dumping out the targets in one process and read
        # them back in, in t'other
        cwd = os.getcwd()
        jobid_file = cwd + os.sep + '.arclibCurrentJobID'
        if not os.access( cwd, os.W_OK ) or ( os.access(jobid_file,os.F_OK)
                                              and not os.access(jobid_file,os.W_OK) ):
            raise JobError,"Cannot create file %s in Nordugrid run_app!\n"+\
                      "Please make sure that you have read/write permission for the directory:\n%s" \
                      %(jobid_file,cwd)

        if os.access(jobid_file,os.F_OK):
            try:
                os.remove( jobid_file )
            except:
                raise JobError,"Cannot delete file %s in Nordugrid GetTargets!\n" % jobid_file

        pid = os.fork()
        if not pid:
            jobid = ''
            # Child process - submits job and writes out the jobid
            try:
                machines = self.GetTargets( xrsl )
                jobid = self.Submit( xrsl, machines )
            except Exception,e:
                print "Child encountered exception submitting job!"
                print e
            except:
                print "Child encountered exception submitting job!"

            f = open( jobid_file, 'w' )
            f.write( jobid )
            f.close()
            os._exit(0)
        else:
            # Parent code
            # loop and see if file has been created
            while 1:
                if os.access( jobid_file,os.R_OK ):
                    time.sleep( 1 ) # Make sure that the child has a chance to write everything out
                    break
                time.sleep( 0.2)

            try:
                f = open( jobid_file, 'r' )
                jobid = f.readline()
                f.close()
            except:
                raise JobError,"Error loading in jobid from %s in Nordugrid GetTargets!" % jobid_file

            # Probably uncessary...
            if jobid.endswith('\n'):
                jobid = jobid[:-1]

            # v. Check that we've got something sensible
            try:
                self.GetJobInfo( jobid=jobid )
            except:
                print "Main read jobid and found it was not valid"
                raise JobError,"There was a problem submitting the job!"

            # Looks valid so remove the file and set self.jobID
            try:
                os.remove( jobid_file )
            except:
                pass
            self.jobID = jobid
            return
        

    def GetJobInfo(self,jobid=None):
        """Get the job info for a job. Default is self.jobID unless we are
           supplied with a jobid
        """

        if not jobid:
            if not self.jobID:
                raise JobError,"GetJobStatus Nordugrid - no valid jobID found!"
            jobid = self.jobID

        try:
            jobinfo = arclib.GetJobInfo( jobid )
#        except arclib.ARCLibError,e:
#            raise JobError,"Nordugrid GetJobStaus error getting job info!\n%s"
        except Exception,e:
            raise JobError,"Nordugrid GetJobStaus error getting job info!\n%s" % e
        except:
            raise JobError,"Nordugrid GetJobStaus error getting job info!"

        return jobinfo        

    def run_app(self,step,kill_on_error=None,**kw):
        """Setup the job, submit it, loop and query status
           
        """

        print "Nordugrid run_app"
        if self.restart:
            self.init_arclib()
        else:
            if step.stdin_file:
                self.job_parameters['stdin'] = step.stdin_file
            if step.stdout_file:
                self.job_parameters['stdout'] = step.stdout_file
            if step.stderr_file:
                self.job_parameters['stderr'] = step.stderr_file
                        
            xrsl = self.CreateRSL()

            if 1:
                self.SubmitInSeparateProcess( xrsl )
            else:
                # Below requires the arclib threading stuff to have been sorted out
                machines = self.GetTargets( xrsl )
                if len(machines) == 0:
                    raise JobError,"No suitable machines could be found to submit to for the job:\n%s" % xrsl
                self.Submit( xrsl, machines )
        
        self.host = self.GetJobInfo().cluster
        running = 1
        message = 'None'
        result = 1
        while running:
            
            if self.stopjob:
                print "Nordugrid job got stop request"
                self.status = JOBSTATUS_STOPPED
                self.restart = 1
                return 2, "Stopped Job"
            
            job_info = self.GetJobInfo()
            self.host = job_info.cluster
            status = job_info.status
            self.status = status
            if status in self.jobstat_finished:
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
            directory = self.copy_back_rundir()
            message = "Job failed! All files have been copied back to the directory:\n%s\nPlease check this directory to see what went wrong." % directory
            
        return result, message
        

    def copy_back_rundir(self,jobid=None):
        """Copy back the directory with all the output files in it.
           This often dies with: Leaked globus_ftp_control_t
           This returns the name of the directory where all the files have been placed
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
#        except arclib.ARCLibError,e:
#            raise JobError,"Nordugird copy_back_dir hit error initialising FTPControl!\n%s" %e
        except Exception,e:
            raise JobError,"Nordugird copy_back_dir hit error initialising FTPControl!\n%s" %e
        except:
            raise JobError,"Nordugird copy_back_dir hit error initialising FTPControl!"

        print "downloading directory"
        print "ftpc.DownloadDirectory( \"%s\",\"%s\" )" %(  myjobid, dirname )

        try:
            ftpc.DownloadDirectory( myjobid, dirname )
#        except arclib.ARCLibError,e:
#            raise JobError,"Nordugird copy_back_dir hit error during download!\n%s" %e
        except arclib.FTPControlError,e:
            raise JobError,"Nordugird copy_back_dir hit error during download!\n%s" %e
        except Exception,e:
            raise JobError,"Nordugird copy_back_dir hit error during download!\n%s" %e
        except:
            raise JobError,"Nordugird copy_back_dir hit error during download!"

        return dirname

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
#        except arclib.ARCLibError,e:
#            raise JobError,"Nordugrid copy_back_file error intialising FTPControl!\n%s" % e
        except Exception,e:
            raise JobError,"Nordugrid copy_back_file error intialising FTPControl!\n%s" % e
        except:
            raise JobError,"Nordugrid copy_back_file error intialising FTPControl!"
            
        rundir = self.jobID
        fileURL = rundir + "/" + remote_filename
        print "copy_back_file fileURL: %s" % fileURL
        local_filenam = os.getcwd() + os.sep + os.path.basename( local_filename )
        print "copy_back_file local_filename: %s" % local_filename
            
        try:
            ftpc.Download( fileURL, local_filename )
#        except arclib.ARCLibError,e:
#            raise JobError,"Nordugrid copy_back_file error retrieving file: %s\n%s" % (fileURL,e)
        except Exception,e:
            raise JobError,"Nordugrid copy_back_file error retrieving file: %s\n%s" % (fileURL,e)
        except:
            raise JobError,"Nordugrid copy_back_file error retrieving file: %s" % fileURL

        return 0,"Retrived file %s from Nordugrid" % local_filename

    def _kill(self):
        """ Kill the job if we are running. We either use the supplied kill command, or
            our own if one wasn't supplied
        """

        print "Killing Nordugrid job "
        self.status = JOBSTATUS_KILLPEND
        if not self.jobID:
            raise JobError,"kill Nordugrid Job - cannot find a jobID!"
        try:
            arclib.CancelJob( self.jobID )
#            except arclib.ARCLibError,e:
#                raise JobError,"kill Nordugrid Job - error killing job!\n%s" % e
        except Exception,e:
            raise JobError,"kill Nordugrid Job - error killing job!\n%s" % e
        except:
            raise JobError,"kill Nordugrid Job - error killing job!"

        # Need to wait for the job to die
        for i in range(2):
            status = self.GetJobInfo().status
            if status in self.jobstat_finished:
                self.status = JOBSTATUS_KILLED
                return None
            time.sleep( self.poll_interval )

        # Only get here if the job couldnt' be stopped in 2 poll intervals
        self.status = JOBSTATUS_FAILED
        return 1

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
#        except arclib.ARCLibError,e:
#            raise JobError,"Nordugrid clean error cleaning job: %s!\n%s" %( myjobid,e)
        except Exception,e:
            raise JobError,"Nordugrid clean error cleaning job: %s!\n%s" %( myjobid,e)
        except:
            raise JobError,"Nordugrid clean error cleaning job: %s " % myjobid
        
        try:
            arclib.RemoveJobID( myjobid)
#        except arclib.ARCLibError,e:
#            raise JobError,"Nordugrid clean error removing jobID: %s\n%s" % (myjobid,e)
        except Exception,e:
            raise JobError,"Nordugrid clean error removing jobID: %s\n%s" % (myjobid,e)
        except:
            raise JobError,"Nordugrid clean error removing jobID: %s" % myjobid

class JobError(RuntimeError):
    def __init__(self,args=None):
        self.args = args

class DummyJob(Job):
    """ Dummy job for testing"""

    notes = """
    Job in some form of loop while running
    keeps checking a save variable to see whether should carry on (thread locking issues)
    if save set (per job with button cf kill in job manager, or from trying to close jobmanager
    with active jobs, then job breaks out of loop -> stop method for all can_stop job steps
    then job save method - sorts out job stack so that can just call run to restart
    job editor then pickles the job after the save call
    on restart, just loop over any saved jobs adding them to the jobmanager and callling run

    methods:
    job -> stop (generic) : sets save variable
       ---- step run method checks save variable, if so returns a specific code to the generic run
       method that tells it to stop looping through the job steps
       run method then calls prepare_save if successful
    ## how to know when stop has been successful? - job must change status to stopped so editor can check?
    job -> prepare_save (generic) : puts above on job stack
    jobstep -> stop (specific) - must be part of the run method
    jobstep -> restart (specific) : method to replace current one on job stack
    jobeditor:
       call stop on job
       if returns o.k. pickle job
    
    """
    def __init__(self,**kw):
        print "initting dummy job"
        Job.__init__(self)
        self.jobtype='Dummmy'
        
    def delete_file(self,step,**kw):
        print "Dummy job delete file"
        return 0,'deleted file'
    def copy_out_file(self,step,**kw):
        print "Dummy job copy_out_file"
        return 0,'copied out file'
    def copy_back_file(self,step,**kw):
        print "Dummy job copy_back_file"
        return 0,'copied back file'
    def run_app(self,step,**kw):
        print "Dummy job run_app"

        self.fname = 'dummy_job.file'

        if not self.restart:
            f = open( self.fname,'w')
            f.write("dummy job\n")
            f.close()

        while os.access( self.fname, os.R_OK ):
            print "Job running..."
            if self.stopjob:
                print "run_app_loop got stop "
                self.status = JOBSTATUS_STOPPED
                self.restart = 1
                return 2, "Stopped Job"
            else:
                time.sleep( self.poll_interval )

        print "Job finished"
        return 0,'ran app'

    def _kill(self):
        self.status = JOBSTATUS_KILLPEND
        try:
            os.remove( self.fname )
        except:
            print "Error removing ",self.fname
        self.status = JOBSTATUS_KILLED
    
if __name__ == "__main__":

    def testpy():
        i=j
        time.sleep(3)

    if 1:
        print 'testing remote foreground job'
        job = LoadLevelerJob('hpcx','psh')
        job.add_step(COPY_OUT_FILE,'transfer input',local_filename='small2.in')
        job.add_step(RUN_APP,'run gamess',local_command='rungamess',local_command_args='small',jobname='small2')
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
        rc_vars[ 'hosts'] = ['lake.esc.cam.ac.uk']
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

    if 0:
        print 'testing nordugrid job'
        
        job_parameters = {}
        job_parameters['count'] = '1'
        job_parameters['outputfiles'] = {"\"/\"": None}
        job_parameters['executable'] = '/bin/hostname'
        job_parameters['jobName'] = 'Check_Hostname'
        job_parameters['stdout'] = 'hostname.out'
        job_parameters['stderr'] = 'hostname.err'

        job = NordugridJob()
        job.update_job_parameters( job_dict = job_parameters )
        job.add_step(RUN_APP,'run nordugrid')
        print job.CreateRSL()
#         job.add_step(COPY_BACK_FILE,'Copy Back Results',local_filename='SC4H4.out')
        #job.run()
#         job.copy_back_rundir()
#         job.clean()
        print 'end jens job'

    if 0:
        print 'testing GROWL job'
        
        job = GrowlJob()
        job.job_parameters['hosts'] = ['scarf.rl.ac.uk']
        job.job_parameters['count'] = 2
        job.job_parameters['jobtype'] = 'mpi'
        
        #job.job_parameters['executable'] = "hostname"
        #job.job_parameters['executable'] = "env"
        job.job_parameters['executable'] = "gamess-uk"
        job.job_parameters['environment']['ftn058'] = 'untitled.pun'
        #job.job_parameters['user_remote_dir'] = "jens"
        #job.add_step(DELETE_FILE,'Growl Delete File',remote_filename='untitled.out',kill_on_error=0)
        #job.add_step(DELETE_FILE,'Growl Delete File',remote_filename='ftn058',kill_on_error=0)
        #job.add_step(COPY_OUT_FILE,'Growl Copy Out File',local_filename='untitled.in')
        #job.add_step(RUN_APP,'Run Growl Job',stdout_file='untitled.out',stderr_file='untitled.err')
        #job.add_step(RUN_APP,'Run Growl Job',stdin_file='untitled.in',stdout_file='untitled.out',stderr_file='untitled.err')
        #job.add_step(COPY_BACK_FILE,'Growl Copy Back File',local_filename='untitled.out')
        #job.add_step(COPY_BACK_FILE,'Growl Copy Back File',local_filename='ftn058')
        #job.add_step(COPY_BACK_FILE,'Growl Copy Back File',local_filename='untitled.err')
        #job.run()
        #job.grid_pwd( 'scarf.rl.ac.uk' )
        path = job.grid_which( 'scarf.rl.ac.uk','hostname' )
        print "path is ",path
        jm = job.grid_get_jobmanager( 'scarf.rl.ac.uk')
        print "jm is ",jm
        url = job.grid_submit( 'scarf.rl.ac.uk','(stdout="out.txt")',path,jobmanager=jm)
        print "url is ",url

