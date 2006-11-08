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

ForegroundPipe
   Unix/Windows pipe (invoking thread will wait)
   no control api possible, just wait for it
   follow-up code is generally just in-lined
   can simply use popen here?

SlavePipe
   Unix/Windows pipe but in a slave thread
   - no control but at least the main program keeps running
     (or at least one would expect so, this doesn't seem to
     be run on windows)

    NB does not support stdin= arg as used by Spawn

Spawn
   fork or pythonwin process (no explicit threads)
   offers the chance to check its status, wait for it, kill it etc
   on unix, can use os.fork, os.waitpid(pid,nohang), os.kill
   on windows, could use spawnl and win32api.TerminateProcess
     - not sure of there is any way to check the status of the
       process 

SlaveSpawn
   As spawn, but under a new thread
   A new thread is spawned which then forks/spawns the new
   process as for 2)
    - the new thread can poll the subprocess and check output etc
    - the new thread can check a queue to find out from the main
      process if any action (e.g. kill) is requested
    - the new thread can execute follow-up code 
    - a timeout is possible

RemoteProcess(ForegroundPipe)
"""
    
import os
import sys
import threading
import time
import Queue
import signal

if sys.platform[:3] == 'win':
    import winprocess
    import win32api, win32process, win32security
    import win32event, win32con, msvcrt, win32gui

import jobmanager

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

    #def __init__(self,cmd,on_end=None,debug=0):
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
            self.child = winprocess.Process(cmd, **kw)
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
                if self.stdin:
                    os.dup2(child_stdin, 0)
                os.dup2(child_stdout, 1)
                os.dup2(child_stderr, 2)

                # Close all file descriptors bar stdin,out & err
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
                    #words = self.cmd.split()
                    if self.debug:
                        #print "child running:  os.execvp(%s,%s)"  % (words[0],words)
                        print "child running:  os.execvp(%s,%s)"  % (self.cmd,self.args)
                    #os.execvp(words[0],words)
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
                    print 'OUT:'
                    print self.output
                        
                if not self.stderr:
                    # No stderr file from user so we read the file
                    # created from the pipe
                    self.error = self.stderr_file.read()
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
                print 'Child in Kill'
            else:
                print 'Killing PID ',self.pid
                sig = 'KILL'
                signals = {'QUIT': 3, 'KILL': 9, 'STOP': 23, 'CONT': 25}
                try:
                    #os.kill(-self.pid,signals[sig]) # -pid since we did set pgid to pid
                    os.kill(self.pid,signals[sig]) # -pid since we did set pgid to pid
                    # and we are trying to kill all children too
                except os.error,e:
                    print "kill - %s of process %d failed" % (sig,self.pid)
                    print e
                                            
                # The return code from the dying process will be
                # returned by the waitpid
                return 0

    def cmd_as_string(self):
        """Return the command to be invoked, together with it's arguments as a single string
        """
        cmd = self.cmd
        if self.args:
            for arg in self.args:
                cmd += ' ' + arg
        return cmd

class ForegroundPipe(SubProcess):
    """Class to manage os.popen3
    So far we have not managed to detect errors using this approach
    (except that there is output on the stderr channel)
    april 2005... try making this fatal and see what happens

    """

    def __init__(self,cmd,**kw):
        apply(SubProcess.__init__, (self,cmd,) , kw)        

    def run(self):

        # Note from the documentation...
        # These methods do not make it possible to retrieve
        # the return code from the child processes

        cmd = self.cmd_as_string()
        (stdin,stdout,stderr) = os.popen3(cmd)
        self.output = stdout.readlines()
        self.error = stderr.readlines()
        if self.debug:
            print 'output', self.output
            print 'error', self.error
        status = stdout.close()
        if self.debug:
            print 'status on out', status 

        status1 = stderr.close()
        if self.debug:
            print 'status on err', status1

        status2 = stdin.close()
        if self.debug:
            print 'status on in', status2

        print 'status,1,2',status,status1,status2

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

class SlavePipe(SubProcess):

    """Spawn a thread which then uses a pipe to run the commmand
    This method runs the requested command in a subthread
    the wait method can be used to check progress
    however there is no kill available (no child pid)
    ... maybe there is a way to destroy the thread together with the child??

    for consistency with spawn it would be ideal if stdin,out,err could
    be provided to route these streams, at the moment they are echoed and saved in.

    """
    def __init__(self,cmd,**kw):
        apply(SubProcess.__init__, (self,cmd,) , kw)

    def run(self):

        # create a Lock
        self.lock  = threading.RLock()

        # Create the queues
        self.queue = Queue.Queue()

        self.status = SLAVE_PIPE
        self.slavethread = SlaveThread(self.lock, self.queue, None, self.__slave_pipe_proc)

        if self.debug:
            print t.time(),'SlavePipe: slave thread starting'
        self.slavethread.start()
        if self.debug:
            print t.time(),'SlavePipe thread started'

    def wait(self,timeout=None):
        """Wait..  """
        count = 0
        if timeout:
            tester = timeout
            incr = 1
        else:
            tester = 1
            incr = 0

        while count < tester:
            if timeout:
                count = count + incr

            try:
                tt = self.queue.get(0)
                if tt == CHILD_STDOUT:
                    tt2 = self.queue.get(0)
                    for x in tt2:
                        self.output.append(x)
                        print  'stdout>',x,

                elif tt == CHILD_STDERR:
                    tt2 = self.queue.get(0)
                    for x in tt2:
                        self.err.append(x)
                        print  'stderr>',x,

                elif tt == CHILD_EXITS:
                    code = self.queue.get(0)
                    if self.debug:
                        print t.time(),'done'
                    return code

            except Queue.Empty:
                if self.debug:
                    print t.time(), 'queue from slave empty, sleep .1'
                time.sleep(0.1)
        print t.time(),'wait timed out'

    def kill(self):
        """(not implemented) """
        if self.debug:
            print t.time(), 'kill'
        print 'kill not available for SlavePipe class'

    def get_output(self):
        """Retrieve any pending data on the pipe to the slave process """

        while 1:
            try:
                tt = self.queue.get(0)
                if tt == CHILD_STDOUT:
                    tt2 = self.queue.get(0)
                    for x in tt2:
                        self.output.append(x)
                        print  'stdout>',x,

                elif tt == CHILD_STDERR:
                    tt2 = self.queue.get(0)
                    for x in tt2:
                        self.err.append(x)
                        print  'stderr>',x,

                elif tt == CHILD_EXITS:
                    code = self.queue.get(0)
                    if self.debug:
                        print t.time(),'done'
                    return code

            except Queue.Empty:
                break

        return self.output

    def __slave_pipe_proc(self,lock,queue,queue1):

        """ this is the code executed in the slave thread when a
        (foreground) pipe is required

        will return stdout and stderr over the queue
        queue1 is not used
        """
        cmd = self.cmd_as_string()
        if self.debug:
            print t.time(), 'invoke command',cmd

        (stdin,stdout,stderr) = os.popen3(cmd)

        if self.debug:
            print t.time(),'command exits'

        while 1:
            if self.debug:
                print t.time(),'read out'
            txt =  stdout.readlines()
            if txt:
                if self.debug:
                    print t.time(),'read out returns', txt[0],' etc'
                queue.put(CHILD_STDOUT)
                queue.put(txt)
            else:
                if self.debug:
                    print 'out is none'

            txt2 =  stderr.readlines()
            if txt2:
                if self.debug:
                    print t.time(),'read err returns', txt2[0],' etc'
                queue.put(CHILD_STDERR)
                queue.put(txt2)
            else:
                if self.debug:
                    print 'err is none'                

            if not txt or not txt2:
                break

        status = stdout.close()
        if self.debug:
            print 'stdout close status',status

        status = stdin.close()
        if self.debug:
            print 'stdin close status',status

        status = stderr.close()
        if self.debug:
            print 'stderr  close status',status
        if self.debug:
            print t.time(),'put to close:', CHILD_EXITS

        queue.put(CHILD_EXITS)
        code = 0
        queue.put(code)

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
            print 'Spawn in wait',self.status
            if self.debug:
                print t.time(), 'class Spawn, err'

            if self.debug:
                print 'return -2'
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

class SlaveSpawn(SubProcess):
    """Use a pythonwin process or fork with controlling thread

    2 queues connect launching thread to control thread

    issues ...
    spawn will need its streams, part
    """

    def __init__(self,cmd,**kw):
        apply(SubProcess.__init__, (self,cmd,) , kw)        

    def run(self,stdin=None,stdout=None,stderr=None):

        self.stdin=stdin
        self.stdout=stdout
        self.stderr=stderr

        # create a Lock
        self.lock  = threading.RLock()

        # Create the queues
        self.queue = Queue.Queue()
        self.queue1 = Queue.Queue()

        self.status = SLAVE_SPAWN
        self.slavethread = SlaveThread(self.lock, self.queue ,self.queue1,self.__slave_spawn_proc)

        if self.debug:
            print t.time(),'threadedSpawn: slave thread starting'
        self.slavethread.start()
        if self.debug:
            print t.time(),'threadedSpawn returns'

    def kill(self):
        """pass kill signal to controlling thread """
        if self.debug:
            print t.time(), 'queue.put ',KILL_CHILD
        self.queue1.put(KILL_CHILD)

    def __slave_spawn_proc(self,loc,queue,queue1):
        """ this is the code executed in the slave thread
        when a (background) spawn/fork is required
        will return stdout and stderr over the queue
        """

        if self.debug:
            print t.time(), 'slave spawning', self.cmd_as_string()

        self._spawn_child()

        while 1:
            if self.debug:
                print t.time(),'check loop'
            # check status of child
            # this should return immediately
            code = self._wait_child(timeout=0)
            if self.debug:
                print t.time(),'check code',code

            if code != 999:
                # child has exited pass back return code
                queue.put(CHILD_EXITS)
                queue.put(code)
                # Attempt to execute any termination code
                if self.on_end:
                    self.on_end()
                break

            # check for intervention
            try:
                if self.debug:
                    print t.time(), 'slave get'
                tt = queue1.get(0)
                if self.debug:
                    print t.time(), 'slave gets message for child', tt
                if tt == KILL_CHILD:
                    code = self._kill_child()
                    break
            except Queue.Empty:
                if self.debug:
                    print t.time(), 'no child message sleeping'

            time.sleep(0.1)

        queue.put(CHILD_EXITS)
        queue.put(code)

        #
        # Currently these are not set up 
        #   here (cf the popen3 based one)
        #
        #status = stdout.close()
        #status = stdin.close()
        #status = stderr.close()

    def wait(self,timeout=None):
        """wait for process to finish """
        if self.debug:
            print t.time(), 'wait'

        count = 0
        if timeout:
            tester = timeout
            incr = 1
        else:
            tester = 1
            incr = 0

        while count < tester:
            if timeout:
                count = count + incr

            try:
                tt = self.queue.get(0)
                if tt == CHILD_STDOUT:
                    tt2 = self.queue.get(0)
                    for x in tt2:
                        print  'stdout>',x,

                elif tt == CHILD_STDERR:
                    tt2 = self.queue.get(0)
                    for x in tt2:
                        print  'stderr>',x,

                elif tt == CHILD_EXITS:
                    code = self.queue.get(0)
                    if self.debug:
                        print t.time(),'done'
                    return code

            except Queue.Empty:
                if self.debug:
                    print t.time(), 'queue from slave empty, sleep .1'
                time.sleep(0.1)

        print t.time(),'wait timed out'


class SlaveThread(threading.Thread):
    """The slave thread runs separate thread
    For control it has 
    - a lock (not used at the moment)
    - a queue object to communicate with the GUI thread
    - a procedure to run
    """

    def __init__(self,lock,queue,queue1,proc):
        threading.Thread.__init__(self,None,None,"JobMan")
        self.lock       = lock
        self.queue      = queue
        self.queue1     = queue1
        self.proc       = proc

    def run(self):
        """ call the specified procedure"""
        try:
            code = self.proc(self.lock,self.queue,self.queue1)
        except RuntimeError, e:
            self.queue.put(RUNTIME_ERROR)

class RemoteProcess(ForegroundPipe):

    def __init__(self,host,cmd,**kw):
        """Run a command on a remote host"""
        apply(SubProcess.__init__, (self,None,) , kw)        

        if sys.platform[:3] == 'win':
            self.cmd = '"C:/Program Files/PuTTY/plink.exe"' 
            self.args = [host, cmd ]
            print 'remote command:',self.cmd_as_string()
        else:
            self.cmd = 'ssh'
            self.args =  [host, cmd]

class SpawnRemoteCmd(Spawn):

    def __init__(self,host,cmd,**kw):
        """Run a command on a remote host using winprocess/fork locally"""

        Spawn.__init__(self,None,**kw)        
        if sys.platform[:3] == 'win':
            self.cmd = '"C:/Program Files/PuTTY/plink.exe"' 
            self.args = [host, cmd ]
            print 'remote command:',self.cmd_as_string()
        else:
            self.cmd = 'ssh'
            self.args =  [host, cmd]


# test this using unit test framework (testsubprocess.py)

