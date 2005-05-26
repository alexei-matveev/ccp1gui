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

RUNTIME_ERROR='runtime-error'
KILL_CHILD='kill-child'
CHILD_EXITS='child-exits'
CHILD_STDOUT='child-stdout'
CHILD_STDERR='child-stderr'

class SubProcess:

    def __init__(self,cmd,on_end=None,debug=0):

        self.cmd = cmd
        self.on_end = on_end
        self.stdin = None
        self.stdout = None
        self.stderr = None
        self.status = IDLE
        self.debug = debug
        self.output = []
        self.err = []
        self.status = IDLE
        self.debug = debug
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

        if sys.platform == 'mac':
            print 'Dont know how to run on mac'
            return -1

        elif sys.platform[:3] == 'win':
            #def run(cmd, mSec=None, stdin=None, stdout=None, stderr=None, **kw):
            """
            Run cmd as a child process and return exit code.
            stdin, stdout, stderr:
            file objects for child I/O (use hStdin etc. to attach
            handles instead of files);
            default is caller's stdin,stdout & stderr;
            kw:    see Process.__init__ for more keyword options
            """
            if self.stdin is not None:
                kw['hStdin'] = msvcrt.get_osfhandle(self.stdin.fileno())
            if self.stdout is not None:
                kw['hStdout'] = msvcrt.get_osfhandle(self.stdout.fileno())
            if self.stderr is not None:
                kw['hStderr'] = msvcrt.get_osfhandle(self.stderr.fileno())
            if self.debug:
                print 'winprocess.Process',self.cmd,kw
            self.child = winprocess.Process(self.cmd, **kw)
        else:
            # UNIX
            #
            # The code for fork will be here
            #

            print 'new UNIX pipe',self.cmd
            #f = os.popen(self.cmd,'w')
            #self.pipe = f
            #status = f.close()

            (self.stdin_pipe,self.stdout_pipe,self.stderr_pipe) = os.popen3(self.cmd)


    def _wait_child(self,timeout=-1):

        print 'child wait start'

        if self.debug:
            print t.time(), 'child wait start'

        if sys.platform == 'mac':
            print 'Dont know how to do wait_child on mac'
            return -1

        elif sys.platform[:3] == 'win':
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
            # UNIX
            # To be replaced with code for fork
            #

            self.output = self.stdout_pipe.readlines()
            self.error = self.stderr_pipe.readlines()

            if self.debug:
                print 'output', self.output
                print 'error', self.error

            status = self.stdout_pipe.close()
            if self.debug:
                print 'status on out', status 

            status1 = self.stderr_pipe.close()
            if self.debug:
                print 'status on err', status1

            status2 = self.stdin_pipe.close()
            if self.debug:
                print 'status on in', status2

            print 'unix wait', self.error, self.debug
            if len(self.error):
                msg = 'Result on Stderr:'
                for ttt in self.error:
                    msg = msg + ttt
                self.msg = msg
                return -1

            #status = self.pipe.close()
            #self.status = EXITED
            #if status:
            #    print 'close status', status
            #    return -1
            else:
                return 0

    def _kill_child(self):
        self.child.kill()
        return self.child.exitCode()


class ForegroundPipe(SubProcess):
    """Class to manage os.popen3
    So far we have not managed to detect errors using this approach
    (except that there is output on the stderr channel)

    april 2005... try making this fatal and see what happens

    """

    def __init__(self,cmd,**kw):
        apply(SubProcess.__init__, (self,cmd,) , kw)        

    def run(self):

        if sys.platform == 'mac':
            print 'Dont know how to run on mac'
            return -1
        else:
            # Windows and Unix
            # Note from the documentation...
            # These methods do not make it possible to retrieve
            # the return code from the child processes

            (stdin,stdout,stderr) = os.popen3(self.cmd)
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
        if self.debug:
            print t.time(), 'invoke command', self.cmd

        (stdin,stdout,stderr) = os.popen3(self.cmd)

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
    def __init__(self,cmd,**kw):
        apply(SubProcess.__init__, (self,cmd,) , kw)        

    def run(self,stdin=None,stdout=None,stderr=None):
        """ execute the command as a subprocess using fork(UNIX) or spawn(Win32) """

        if self.debug:
            print t.time(), 'class Spawn, method run, _spawn_child'
        self.status = SPAWNING

        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

        self._spawn_child()

        self.status = SPAWNED

    def kill(self):
        code = self._kill_child()
        self.status = KILLED
        return code

    def wait(self,**kw):


        if self.status == SPAWNED:

            if self.debug:
                print t.time(), 'class Spawn, method wait _wait_child'

            code  = self._wait_child(**kw)
            if self.debug:
                print 'wait code',code
            return code
        else:

            if self.debug:
                print t.time(), 'class Spawn, err'

            if self.debug:
                print 'return -2'
            return -2


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
            print t.time(), 'slave spawning', self.cmd

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

        if sys.platform == 'mac':
            print 'Dont know how to run on mac'
            return -1
        elif sys.platform[:3] == 'win':
            self.cmd = '"C:/Program Files/PuTTY/plink.exe"' + ' ' + host + ' ' + cmd 
            print 'remote command:',self.cmd
        else:
            self.cmd = 'ssh' + ' ' + host + ' ' + cmd


if __name__ == "__main__":

    if 1:
        os.environ['TCL_LIBRARY']='/usr/share/tcl8.4'
        os.environ['TCLLIBPATH']='/cygdrive/c/chemsh/tcl'
        print 'Testing Spawn ChemShell'
        jobname='small'
        cmd = '"C:/chemsh/bin/chemshprog.exe" < small.chm'
        print cmd
        p = ForegroundPipe(cmd)
        p.run()

    if 0:
        print 'Testing Spawn'
        jobname='small'
        cmd = '"C:/Program Files/DeLano Scientific/PyMOL/modules/ccp1gui/exe/gamess.exe"'
        print cmd
        p = Spawn(cmd)
        i = open('small.in','r')
        o = open('small.out','w')    
        p.run(stdin=i,stdout=o)
        o.close()
        i.close()
        code = p.wait()
        print 'return code',code

    if 0:
        print 'Testing SlaveSpawn'
        jobname='small'
        cmd = '"C:/Program Files/DeLano Scientific/PyMOL/modules/ccp1gui/exe/gamess.exe"'
        print cmd
        p = SlaveSpawn(cmd,debug=1)
        i = open('small.in','r')
        o = open('small.out','w')
        e = open('small.err','w')
        p.run(stdin=i)
        code = p.wait()
        o.close()
        i.close()
        e.close()
        print 'return code',code

    if 0:
        print 'Testing ForegroundPipe'
        jobname='small'
        cmd = '"C:/Program Files/DeLano Scientific/PyMOL/modules/ccp1gui/exe/gamess.exe" < '+jobname+'.in > ' + jobname+'.out'
        print cmd
        p = ForegroundPipe(cmd)
        code = p.run()
        print 'return code',code

    if 0:
        print 'Testing SlavePipe'
        jobname='small'
        cmd = '"C:/Program Files/DeLano Scientific/PyMOL/modules/ccp1gui/exe/gamess.exe" < '+jobname+'.in > ' + jobname+'.out'
        print cmd
        p = SlavePipe(cmd,debug=1)
        code = p.run()
        print 'run return code',code
        code = p.wait()
        print 'wait return code',code

    if 0:
        jobname='small'
        cmd = '"C:/Program Files/DeLano Scientific/PyMOL/modules/ccp1gui/exe/gamess.exe" < '+jobname+'.in > ' + jobname+'.out'
        print cmd
        p = Spawn(cmd)
        i = open('small.in','r')
        o = open('small.out','w')    
        p.run(stdin=i,stdout=o)
        o.close()
        code = p.wait()
        print 'return code',code

    if 0:
        print 'Test Pipe for Remote Process'
        host = 'hpcx'
        cmd = 'pwd'
        rcmd = '"C:/Program Files/PuTTY/plink.exe"' + ' ' + host + ' ' + cmd 
        print 'remote command:',rcmd
        #p = RemoteProcess('tcsg7','pwd')
        #p = RemoteProcess('hpcx','pwd')
        p = ForegroundPipe(rcmd)
        code = p.run()

    if 0:
        print 'Test SlavePipe for Remote Process'
        host = 'hpcx'
        cmd = 'pwd'
        rcmd = '"C:/Program Files/PuTTY/plink.exe"' + ' ' + host + ' ' + cmd 
        if self.debug:
            print 'remote command:',rcmd
        p = SlavePipe(rcmd)
        code = p.run()
        if self.debug:
            print 'run code',code
        code = p.wait()
        if self.debug:
            print 'wait code',code

    if 0:
        print 'Test Spawn and kill for Remote Process'
        host = 'hpcx'
        cmd = 'sleep 4'
        rcmd = '"C:/Program Files/PuTTY/plink.exe"' + ' ' + host + ' ' + cmd 
        print 'remote command:',rcmd
        p = Spawn(rcmd,debug=1)
        code = p.run()
        print 'run code',code

        code = p.wait(timeout=3000)

        print 'wait code',code

        code = p.kill()
        print 'kill code',code

        code = p.wait(timeout=3000)
        print 'wait code',code

    if 0:
        print 'Test Spawn for Remote Process'
        host = 'hpcx'
        cmd = 'sleep 4'
        rcmd = '"C:/Program Files/PuTTY/plink.exe"' + ' ' + host + ' ' + cmd 
        print 'remote command:',rcmd
        p = Spawn(rcmd,debug=1)
        code = p.run()
        print 'run code',code

        code = p.wait(timeout=3000)
        print 'wait code',code

        code = p.kill()
        print 'kill code',code

        code = p.wait(timeout=3000)
        print 'wait code',code
        code = p.wait(timeout=3000)
        print 'wait code',code
        code = p.wait(timeout=3000)
        print 'wait code',code


    #p.spawn()
    #p.threadedPipe()
    #cmd = '"C:/Program Files/DeLano Scientific/PyMOL/modules/ccp1gui/exe/gamess.exe" < '+jobname+'.in'
    #cmd = '"C:/Program Files/PuTTY/pscp.exe" small.in tcsg7:'
    #cmd = '"C:/Program Files/PuTTY/pscp.exe" small.in psh@login.hpcx.ac.uk:'
    #p = RemoteProcess('hpcx','export GAMESS_PROJECT=z001;/usr/local/packages/gamessuk/rungamess/rungamess -q small')
    #p.spawn()
    #code = p.wait()
    #print 'return code',code
    #if not code:
    #    for t in p.get_output():
    #        print t,
    # The pipe  seems fine, except we have not managed to store the
    # output anywhere
    # p = RemoteProcess('hpcx','llq | grep psh')
    #code = p.pipe()

    #i = open('test.in','r')
    #p.threadedSpawn()
    #print 'return code',code
    #if not code:
    #    for t in p.get_output():
    #        print t,

    if 0:
        #p = SubProcess("notepad.exe")
        jobname='test'

        #cmd = 'notepady.exe'
        p = SubProcess(cmd)
        #p.threadedPipe()
        i = open('test.in','r')
        p.threadedSpawn(stdin=i)
        time.sleep(3)
        code = p.kill()

    if 0:
        i = open('test.in','r')
        #o = open('test.out','w')
        p.spawn(stdin=i,stdout=None)
        i.close()
        #p.wait(timeout=-1)
        print 'kill returns code',code
        #o.close()
        #print 'p.output returns',p.get_output()
        #code = p.wait()
        #print 'p.wait returns',code
        #print p.get_output()
