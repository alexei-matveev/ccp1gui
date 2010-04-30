"""
This collection of routines are alternatives to those
in subprocess.py but which create additional controlling
threads.

Since this feature is not needed in the GUI as a separate thread
is spawned of to handle each job they are no longer needed,
but retained for possible future use.

"""
import os,sys
if __name__ == "__main__":
    # Need to add the gui directory to the python path so 
    # that all the modules can be imported
    gui_path = os.path.split(os.path.dirname( os.path.realpath( __file__ ) ))[0]
    sys.path.append(gui_path)

import threading
import subprocess
import time
import Queue
import unittest

import ccp1gui_subprocess

class SlavePipe(ccp1gui_subprocess.SubProcess):

    """Spawn a thread which then uses a pipe to run the commmand
    This method runs the requested command in a subthread
    the wait method can be used to check progress
    however there is no kill available (no child pid)
    ... maybe there is a way to destroy the thread together with the child??

    for consistency with spawn it would be ideal if stdin,out,err could
    be provided to route these streams, at the moment they are echoed and saved in.

    """
    def __init__(self,cmd,**kw):
        ccp1gui_subprocess.SubProcess.__init__(self,cmd,**kw)

    def run(self):

        # create a Lock
        self.lock  = threading.RLock()

        # Create the queues
        self.queue = Queue.Queue()

        self.status = ccp1gui_subprocess.SLAVE_PIPE
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
                if tt == ccp1gui_subprocess.CHILD_STDOUT:
                    tt2 = self.queue.get(0)
                    for x in tt2:
                        self.output.append(x)
                        print  'stdout>',x,

                elif tt == ccp1gui_subprocess.CHILD_STDERR:
                    tt2 = self.queue.get(0)
                    for x in tt2:
                        self.err.append(x)
                        print  'stderr>',x,

                elif tt == ccp1gui_subprocess.CHILD_EXITS:
                    code = self.queue.get(0)
                    if self.debug:
                        print t.time(),'done'
                    return code

            except Queue.Empty:
                if self.debug:
                    print t.time(), 'queue from slave empty, sleep .1'
                time.sleep(0.1)
        #print t.time(),'wait timed out'

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
                if tt == ccp1gui_subprocess.CHILD_STDOUT:
                    tt2 = self.queue.get(0)
                    for x in tt2:
                        self.output.append(x)
                        print  'stdout>',x,

                elif tt == ccp1gui_subprocess.CHILD_STDERR:
                    tt2 = self.queue.get(0)
                    for x in tt2:
                        self.err.append(x)
                        print  'stderr>',x,

                elif tt == ccp1gui_subprocess.CHILD_EXITS:
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

        #(stdin,stdout,stderr) = os.popen3(cmd)
        p =subprocess.Popen(cmd,
                            shell=True,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            close_fds=True)
        (stdin, stdout, stderr) = (p.stdin, p.stdout, p.stderr)

        if self.debug:
            print t.time(),'command exits'

        while 1:
            if self.debug:
                print t.time(),'read out'
            txt =  stdout.readlines()
            if txt:
                if self.debug:
                    print t.time(),'read out returns', txt[0],' etc'
                queue.put(ccp1gui_subprocess.CHILD_STDOUT)
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
            print t.time(),'put to close:', ccp1gui_subprocess.CHILD_EXITS

        queue.put(ccp1gui_subprocess.CHILD_EXITS)
        code = 0
        queue.put(code)



class SlaveSpawn(ccp1gui_subprocess.SubProcess):
    """Use a pythonwin process or fork with controlling thread

    2 queues connect launching thread to control thread

    issues ...
    spawn will need its streams, part
    """

    def __init__(self,cmd,**kw):
        ccp1gui_subprocess.SubProcess.__init__(self,cmd,**kw)        

    def run(self,stdin=None,stdout=None,stderr=None):

        self.stdin=stdin
        self.stdout=stdout
        self.stderr=stderr

        # create a Lock
        self.lock  = threading.RLock()

        # Create the queues
        self.queue = Queue.Queue()
        self.queue1 = Queue.Queue()

        self.status = ccp1gui_subprocess.SLAVE_SPAWN
        self.slavethread = SlaveThread(self.lock, self.queue ,self.queue1,self.__slave_spawn_proc)

        if self.debug:
            print t.time(),'threadedSpawn: slave thread starting'
        self.slavethread.start()
        if self.debug:
            print t.time(),'threadedSpawn returns'

    def kill(self):
        """pass kill signal to controlling thread """
        if self.debug:
            print t.time(), 'queue.put ',ccp1gui_subprocess.KILL_CHILD
        self.queue1.put(ccp1gui_subprocess.KILL_CHILD)

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
                queue.put(ccp1gui_subprocess.CHILD_EXITS)
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
                if tt == ccp1gui_subprocess.KILL_CHILD:
                    code = self._kill_child()
                    break
            except Queue.Empty:
                if self.debug:
                    print t.time(), 'no child message sleeping'

            time.sleep(0.1)

        queue.put(ccp1gui_subprocess.CHILD_EXITS)
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
                if tt == ccp1gui_subprocess.CHILD_STDOUT:
                    tt2 = self.queue.get(0)
                    for x in tt2:
                        print  'stdout>',x,

                elif tt == ccp1gui_subprocess.CHILD_STDERR:
                    tt2 = self.queue.get(0)
                    for x in tt2:
                        print  'stderr>',x,

                elif tt == ccp1gui_subprocess.CHILD_EXITS:
                    code = self.queue.get(0)
                    if self.debug:
                        print t.time(),'done'
                    return code

            except Queue.Empty:
                if self.debug:
                    print t.time(), 'queue from slave empty, sleep .1'
                time.sleep(0.1)

        #print t.time(),'wait timed out'


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
            self.queue.put(ccp1gui_subprocess.RUNTIME_ERROR)


##########################################################
#
#
# Unittesting stuff goes here
#
#
##########################################################

class testSlaveSpawn(unittest.TestCase):
    """fork/pythonwin process management with extra process"""

    # this is not longer needed for GUI operation
    # it also has not been adapted to take cmd + args separately
    # however it does seem to work
    def testA(self):
        """check echo on local host using stdout redirection"""
        self.proc = SlaveSpawn('echo a b',debug=0)
        o = open('test.out','w')
        self.proc.run(stdout=o)
        self.proc.wait()
        o.close()
        o = open('test.out','r')
        output = o.readlines()
        print 'output=',output
        self.assertEqual(output,['a b\n'])

if __name__ == "__main__":
    # Run all tests automatically
    unittest.main()
