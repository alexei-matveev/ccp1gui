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
        self.monitor_file=monitor_file
        self.kill_on_error=kill_on_error
        self.warn_on_error = warn_on_error
        self.kill_cmd = kill_cmd

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
        self.debug = 0
        
    def __repr__(self):
        txt = self.jobtype + ':'
        for step in self.steps:
            txt = txt + step.type + '/'
        return txt

    def add_step(self,type,name,**kw):
        """Add a new job Step"""
        if self.debug:
            print 'adding job step',kw
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
                    print 'Fatal Exception:', step.name, e
                    print e
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
                    self.msg =  'Step Failed :' + step.name + " " + message
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

    if 1:
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

