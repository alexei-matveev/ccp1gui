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
"""Subprocess handling classes.
The idea here is to implement a variety of procedures for controlling
subprocesses (typically system commands). All classes are subclassed
from the SubProcess class.

Pipe

   Unix/Windows pipe (invoking thread will wait)
   no control api possible, just wait for it
   follow-up code is generally just in-lined
   can simply use popen here?

Spawn

   fork or pythonwin process (no explicit threads)
   offers the chance to check its status, wait for it, kill it etc
   on unix, can use os.fork, os.waitpid(pid,nohang), os.kill
   on windows, could use spawnl and win32api.TerminateProcess
     - not sure of there is any way to check the status of the
       process 

PipeRemoteCmd(Pipe)
SpawnRemoteCmd(Spawn)

"""
    
import os
import sys
import threading
import time
import Queue
import signal
import subprocess
import unittest

if sys.platform[:3] == 'win':
    import winprocess
    import win32api, win32process, win32security
    import win32event, win32con, msvcrt, win32gui

#import jobmanager

class MyTime:
    def __init__(self):
        self.t0 = time.time()
    def time(self):
        return '%f4.2' % (time.time()-self.t0)

t = MyTime()

IDLE=0
DONE_PIPE=10
SPAWNING=1
SPAWNED=2
SLAVE_PIPE=3
SLAVE_SPAWN=4
KILLED=5
EXITED=6
FAILED=7

RUNTIME_ERROR='runtime-error'
KILL_CHILD='kill-child'
CHILD_EXITS='child-exits'
CHILD_STDOUT='child-stdout'
CHILD_STDERR='child-stderr'

def list_to_string(list):
    if len(list) == 0:
        return ""
    else:
        txt = ""
        for l in list[:-1]:
            txt = txt + l
        txt = txt + list[-1]
        return txt

class SubProcess:

    def __init__(self,cmd,args=None,on_end=None,debug=0):
        """
           Base class for subprocess management.
           cmd  - the command to be excuted as a string (without any arguments)
           args - a list of strings that are the arguments that the command should be
                  invoked with. This can be None if the command is just to be invoked with
                  no additional arguments.
        """

        if cmd:
            assert type(cmd) == str, "jobmanager/subprocess.py: cmd argument to SubProcess must be a string!"
        self.cmd = cmd
        if args:
            assert type(args) == list, "jobmanager/subprocess.py: Arguments to SubProcess must be a list!"
        self.args =  args

        self.on_end = on_end
        self.stdin = None
        self.stdout = None
        self.stderr = None
        self.status = IDLE
        self.debug = debug
        #self.debug = 1

        self.output = []
        self.err = []
        self.status = IDLE

        if self.debug:
            print "SubProcess: self.cmd is: %s" % self.cmd
            print "            self.args is: %s" % self.args
    #
    #   main access functions (need to be replaced)
    #
    def kill(self):
        self.__should_overload('kill')

    def wait(self):
        self.__should_overload('wait')

    def run(self):
        self.__should_overload('run')

    def __should_overload(self,word):
        print 'SubProcess error'
        print 'A Derived class which overloads ',word,' should be used'

    def _spawn_child(self,**kw):

        if sys.platform[:3] == 'win':
            #def run(cmd, mSec=None, stdin=None, stdout=None, stderr=None, **kw):
            """
            Run cmd as a child process and return exit code.
            stdin, stdout, stderr:
            file objects for child I/O (use hStdin etc. to attach
            handles instead of files);
            default is caller's stdin,stdout & stderr;
            kw:    see Process.__init__ for more keyword options
            """
            cmd = self.cmd_as_string()
            if self.stdin is not None:
                kw['hStdin'] = msvcrt.get_osfhandle(self.stdin.fileno())
            if self.stdout is not None:
                kw['hStdout'] = msvcrt.get_osfhandle(self.stdout.fileno())
            if self.stderr is not None:
                kw['hStderr'] = msvcrt.get_osfhandle(self.stderr.fileno())
            if self.debug:
                print 'winprocess.Process',cmd,kw
            self.child = winprocess.Process(cmd, show=0, **kw)
        else:
            # Unix code

            if self.debug:
                print "spawn_child unix code"

            if self.stdin:
                # Have an input file so attach the fd to the child input
                child_stdin = self.stdin.fileno()
            else:
                # We don't need to do anything here as we assume that the
                # child doesn't need stdin
                pass

            # For stdout & stderr, if we were given a file give the fd the child,
            # otherwise we create a pipe to catch the stdout from the child
            if self.stdout:
                parent_stdout = None
                child_stdout = self.stdout.fileno()
            else:
                parent_stdout, child_stdout =  os.pipe()

            if self.stderr:
                parent_stderr = None
                child_stderr = self.stderr.fileno()
            else:
                parent_stderr, child_stderr =  os.pipe()

            if self.debug:
                print "calling fork"
                
            self.pid = os.fork()

            if self.pid:
                # we are the parent
                if self.debug:
                    print "parent code excuting"
                    print "process id is", self.pid

                # Close all the file descriptors that we don't need
                # and attach files to the read end of the pipes
                if self.stdin:
                    # Calling this causes an error - not sure why though
                    #os.close( child_stdin )
                    pass
                    
                if not self.stdout:
                    os.close( child_stdout )
                    # turn parent_stdout into a file object
                    self.stdout_file = os.fdopen( parent_stdout )
                    
                if not self.stderr:
                    os.close( child_stderr )
                    # turn parent_stderr into a file object
                    self.stderr_file = os.fdopen( parent_stderr )

            else:
                # Child code
                
                # Duplicate the file descriptors so that stdin comes from the file (if applicable)
                # and stdout & err go to the file descriptor that either points at the file we were
                # given or the parent end of the pipe

                if self.debug:
                    print "child code running:  os.execvp(%s,%s)"  % (self.cmd,self.args)

                if self.stdin:
                    os.dup2(child_stdin, 0)
                os.dup2(child_stdout, 1)
                os.dup2(child_stderr, 2)

                # Close all file descriptors bar stdin, out & err
                self.MAXFD = 256
                for i in range(3, self.MAXFD):
                    try:
                        os.close(i)
                    except:
                        pass

                # Need to include the command in the second argument to the execvp command
                if self.args:
                    self.args = [self.cmd] + self.args
                else:
                    self.args = [self.cmd]
                    
                try:
                    os.setsid() # Make child process group leader so we can stop child and all its children
                    os.nice(19)
                    # Below sets the handler for SIGHUP to that for SIG_IGN
                    # i.e. if we get told to hang up, we ignore it
                    signal.signal(signal.SIGHUP, signal.SIG_IGN)
                    os.execvp(self.cmd,self.args)
                except Exception,e:
                    #print "Error trying to execute: os.execvp(%s,%s)"  % (words[0],words)
                    print "Error trying to execute: os.execvp(%s,%s)"  % (self.cmd,self.args)
                    print e
                    os._exit(-1)
                #finally:
                else:
                    if self.debug:
                        print "child calling exit"
                    os._exit(1)

    def _wait_child(self,timeout=-1):

        if self.debug:
            print t.time(), 'child wait start'

        if sys.platform[:3] == 'win':
            mSec=timeout
            if self.child.wait(mSec) != win32event.WAIT_OBJECT_0:
                if self.debug:
                    print t.time(), 'child wait ends 1'
                return 999

            if self.debug:
                print t.time(), 'child wait ends 2'

            self.status = EXITED
            return self.child.exitCode()

        else:
            # UNIX/LINUX code
            if not self.pid:
                # This never gets called?
                print 'Child in Wait'
            else:
                # parent
                if self.debug:
                    print "parent executing wait"

                if not self.stdout:
                    self.output = self.stdout_file.read()
                    if self.debug:
                        print 'OUT:'
                        print self.output
                        
                if not self.stderr:
                    # No stderr file from user so we read the file
                    # created from the pipe
                    self.error = self.stderr_file.read()
                    if self.debug:
                        print 'ERR:'
                        print self.error
                else:
                    if self.debug:
                        # User gave us a stderr file so we open it and read it
                        # THIS IS BUST - NOT SURE OF THE BEST WAY TO FIX IT
                        # BUT IS PRETTY UNIMPORTANT AS THE FILE HAS BEEN SAVED
                        print "wait parent self.stderr is ",self.stderr
                        print 'ERR:'
                        self.error = self.stderr.read()
                
                proc, code = os.waitpid(self.pid, 0)
                self.status = EXITED
                return code
            
#                if code == 0:
#                    return 0
#                else:
#                    return status


##                 if len(txt) == 0:
##                     # Process died somehow before results could be sent through
##                     self.output = ""
##                     self.error = "slave process killed"
##                     self.status = code
##                     self.status1 = None
##                     self.status2 = None
##                 else:
##                     self.output = txt[0]
##                     self.error = txt[1]
##                     if txt[2] == "None":
##                         self.status = None
##                     else:
##                         self.status = int(txt[2])
##                     if txt[3] == "None":
##                         self.status1 = None
##                     else:
##                         self.status1 = int(txt[3])
##                     if txt[4] == "None":
##                         self.status2 = None
##                     else:
##                         self.status2 = int(txt[4])


##                 self.output = ""
##                 self.error = "slave process killed"
##                 self.status = code
##                 self.status1 = None
##                 self.status2 = None


                if len(self.error):
##                if code != 0:
                    msg = 'Result on Stderr:'
                    for ttt in self.error:
                        msg = msg + ttt
                    self.msg = msg
##                    self.msg = "slave process died"
                    return -1
                    #self.status = EXITED
                    #if status:
                    #    print 'close status', status
                    #    return -1
                else:
                    return 0

    def _kill_child(self):

        if sys.platform == 'mac':
            print 'Dont know how to do _kill_child on mac'
            return -1

        elif sys.platform[:3] == 'win':
            self.child.kill()
            return self.child.exitCode()
        else:
            if not self.pid:
                if self.debug: print 'Child in Kill'
            else:
                if self.debug: print 'Killing PID ',self.pid
                sig = 'KILL'
                signals = {'QUIT': 3, 'KILL': 9, 'STOP': 23, 'CONT': 25}
                try:
                    os.kill(-self.pid,signals[sig]) # -pid since we did set pgid to pid
                    #                                  and we are trying to kill all children too
                    # jmht version
                    #os.kill(self.pid,signals[sig]) 
                except os.error,e:
                    print "kill - %s of process %d failed" % (sig,self.pid)
                    print e
                                            
                # The return code from the dying process will be
                # returned by the waitpid
                return 0

    def cmd_as_string(self):
        """Return the command to be invoked, together with it's arguments as a single string
        """
        if self.debug:
            print 'cmd_as_string, checking for embedded spaces'
            print 'cmd', self.cmd, " " in self.cmd

        if " " in self.cmd:
            cmd = '"'+self.cmd+'"'
        else:
            cmd = self.cmd


        if self.args:
            for arg in self.args:
                if self.debug:
                    print 'arg', arg, " " in arg
                if " " in arg:
                    # need to quote args containing spaces
                    cmd += ' "' + arg + '"'
                else:
                    cmd += ' ' + arg
        return cmd

class Pipe(SubProcess):
    """Class to manage os.popen3
    So far we have not managed to detect errors using this approach
    (except that there is output on the stderr channel)
    april 2005... try making this fatal and see what happens
    """

    def __init__(self,cmd,args=None,**kw):
        SubProcess.__init__(self,cmd,args=args,**kw)        

    def run(self):

        # Note from the documentation...
        # These methods do not make it possible to retrieve
        # the return code from the child processes

        cmd = self.cmd_as_string()
        if self.debug:
            print 'Pipe.run, calling popen3 on',cmd
        #(stdin,stdout,stderr) = os.popen3(cmd)
        p =subprocess.Popen(cmd,
                            shell=True,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            close_fds=True)
        (stdin, stdout, stderr) = (p.stdin, p.stdout, p.stderr)
            

        self.output = stdout.readlines()
        self.error = stderr.readlines()
        if self.debug:
            print 'output', self.output
            print 'error', self.error
        status = stdout.close()
        if self.debug:
            print 'status on closing stout', status 

        status1 = stderr.close()
        if self.debug:
            print 'status on closing sterr', status1

        status2 = stdin.close()
        if self.debug:
            print 'status on closing stdin', status2

        if len(self.error):
            msg = 'Result on Stderr:'
            for t in self.error:
                msg = msg + t
            self.msg = msg
            return -1

        self.status = DONE_PIPE
        if not status:
            return 0
        else:
            return status

    def get_output(self):

        if self.status == DONE_PIPE:
            # finished processes will have stored it here
            # (see pipe)
            return self.output
        else:
            return None


class Spawn(SubProcess):
    """Interface to pythonwin Process() or fork on UNIX
    stdin,stdout should be passed to run
    wait supports timeout
    kill is available
    ToDo: introduce internal status to trap wait/kill
    """
    def __init__(self,cmd,args=None,**kw):
        SubProcess.__init__(self,cmd,args=args,**kw)        

    def run(self,stdin=None,stdout=None,stderr=None):
        """ Execute the command as a subprocess using fork(UNIX) or spawn(Win32)
            If passed in, stdin, stdout & stderr should be open files
        """

        if self.debug:
           print t.time(), 'class Spawn, method run, _spawn_child'
        self.status = SPAWNING

        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

        ret = self._spawn_child()
        if ret == -1:
            print "subprocess:Spawn - _spawn_child failed!"
            self.status = FAILED
        else:
            self.status = SPAWNED

        return self.status

    def kill(self):
        code = self._kill_child()
        self.status = KILLED
        return code

    def wait(self,**kw):
        if self.status == FAILED:
            if self.debug:
                print "subprocess:Spawn wait got FAILED!"
                return -1
            
        elif self.status == SPAWNED:
            if self.debug:
                print t.time(), 'class Spawn, method wait _wait_child'

            code  = self._wait_child(**kw)
            if self.debug:
                print 'wait code',code
            return code

        else:
            if self.debug:
                print t.time(), 'class Spawn in wait, self.status =',self.status
                print 'will return -2'

            return -2

    def get_output(self):
        if self.status == EXITED:
            return self.output
        else:
            return None

    def get_error(self):
        if self.status == EXITED:
            return self.error
        else:
            return None

class PipeRemoteCmd(Pipe):
    """Run a command on a remote host using a pipe locally    """    
    #
    #  PS: handing around username needed for unix but
    #      it is not used when using Putty
    #
    def __init__(self,host,user,cmd,**kw):
        Pipe.__init__(self,cmd,**kw)
        self.host=host
        self.user=user

    def run(self,**kw):

        if self.debug:
            print 'PipeRemoteCmd cmd,args=',self.cmd, self.args

        # combine command and arguments as presented
        # hopefully no spaces as this will be a unix command
        cmd = self.cmd_as_string()

        # Add redirection - omit for now as not needed, we'll need
        # to decide whether local or remote files are correct here

#         if stdin_file:
#             cmd = cmd + ' <'+stdin_file
#         if stdout_file:
#             cmd = cmd + ' >'+stdout_file
            
        if sys.platform[:3] == 'win':
            self.cmd = '"C:/Program Files/PuTTY/plink.exe"' 
            # just two args, the host and everything else, which should get quoted
            # because it has embedded spaces
            self.args = [self.host, cmd ] 
            print 'remote command:',self.cmd_as_string()
        else:
            self.cmd = 'ssh'
            #self.args =  [self.user+'@'+self.host, cmd] + args
            self.args =  [self.user+'@'+self.host, cmd]

        Pipe.run(self,**kw)        


class SpawnRemoteCmd(Spawn):
    """Run a command on a remote host using winprocess/fork locally"""
    def __init__(self,host,user,cmd,**kw):
        Spawn.__init__(self,None,**kw)        
        if sys.platform[:3] == 'win':
            self.cmd = '"C:/Program Files/PuTTY/plink.exe"' 
            self.args = [host, cmd ]
            print 'remote command:',self.cmd_as_string()
        else:
            self.cmd = 'ssh'
            self.args =  [user+'@'+host, cmd]

##########################################################
#
#
# Unittesting stuff goes here
#
#
##########################################################

# Specify these for your local system:
sshuser='jmht'
sshhost='cselnx1.dl.ac.uk'
# first 3 chars of hostname issued on this host 
chkstr='cse'

class testSpawn(unittest.TestCase):
    """fork/pythonwin process management"""

    # implementation notes. get_output is available from spawn but
    # it doesn't seem to do anything

    def testA(self):
        """check echo on local host using a file connection on stdout"""
        self.proc = Spawn('echo',['a','b'],debug=0)
        o = open('test.out','w')
        self.proc.run(stdout=o)
        self.proc.wait()
        o.close()
        o = open('test.out','r')
        output = o.readlines()
        self.assertEqual(output,['a b\n'])

class testSpawnRemoteProcess(unittest.TestCase):
    """fork/pythonwin process management"""

    def testA(self):
        """Execute ssh and check output"""
        # on windows, the code returns 999 from wait until the
        # process has died, then -2
        p = SpawnRemoteCmd(sshhost,sshuser,'hostname',debug=0)
        o = open('test.out','w')

        code = p.run(stdout=o)
        self.assertEqual(code,SPAWNED,"Command failed to run")

        code1 = p.wait()
        self.assertEqual(code1,0,"Unexpected code %d from wait" % code1)

        o.close()
        o = open('test.out','r')
        output = o.readlines()
        o.close()
        self.assertNotEqual(output,None,"Command failed to produce output")

        tester=output[0][:3]
        self.assertEqual(tester,chkstr,"Unexpected output from hostname")

    def testB(self):
        """Execute ssh and check that it is capable of being killed"""

        have_wait = 0
        if have_wait:
            # on windows, the code returns 999 from wait until the
            # process has dies, then -2
            p = SpawnRemoteCmd(sshhost,sshuser,'sleep 10',debug=0)
            code = p.run()
            self.assertEqual(code,SPAWNED,"Command failed to run")
            code1 = p.wait(timeout=1000)
            code2 = p.wait(timeout=1000)
            code = p.kill()
            code3 = p.wait(timeout=1000)
            self.assertEqual([code1,code2,code3],[999,999,-2])
        else:
            # on linux, no waiting on pid yet
            p = SpawnRemoteCmd(sshhost,sshuser,'sleep 10',debug=0)
            code = p.run()
            self.assertEqual(code,SPAWNED,"Command failed to run")
            time.sleep(3)
            code = p.kill()
            self.assertEqual(code,0,"Unexpected code %d from kill" % code)
            code = p.wait()
            self.assertEqual(code,-2,"Unexpected code %d from wait" % code)

class testPipeRemoteCmd(unittest.TestCase):
    """ rsh/plink + host + simple command"""
    def testA(self):
        """Check PipeRemoteCmd by issuing hostname over ssh"""
        self.proc = PipeRemoteCmd(sshhost,sshuser,'hostname',debug=0)
        self.proc.run()
        output=self.proc.get_output()
        self.assertNotEqual(output,None,"Command failed ro tun")
        tester=output[0][:3]
        self.assertEqual(tester,chkstr)

class testSpawnRemoteCmd(unittest.TestCase):
    """ rsh/plink + host + simple command"""
    def testA(self):
        """check by issuing hostname over ssh"""
        self.proc = SpawnRemoteCmd(sshhost,sshuser,'hostname',debug=0)
        code = self.proc.run()
        self.assertEqual(code,SPAWNED,"Command failed to run")

        code = self.proc.wait()
        #self.assertEqual(code,0,"Wait returned unexpected code")
        self.assertEqual(code,0)

        output=self.proc.get_output()
        #error=self.proc.get_error()
        #print 'output:',output
        #print 'error:',error

        tester=output[:3]
        self.assertEqual(tester,chkstr)

if __name__ == "__main__":
    unittest.main()
