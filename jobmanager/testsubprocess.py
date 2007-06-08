#
# unit tests for the subprocess classes
#

# Specify these for your local system:
sshuser='psh'
sshhost='cselnx1.dl.ac.uk'
# first 3 chars of hostname issued on this host 
chkstr='cse'


#sshhost='login.hpcx.ac.uk'
#chkstr='l1f'

# on unix it helps if you use ssh-agent/ssh-add to allow ssh without a password prompt
# on windows, we suggest setting up putty+pageant

import subprocess
import unittest
import time

debug=0

class testSpawn(unittest.TestCase):
    """fork/pythonwin process management"""

    # implementation notes. get_output is available from spawn but
    # it doesn't seem to do anything

    def testA(self):
        """check echo on local host using a file connection on stdout"""
        self.proc = subprocess.Spawn('echo',['a','b'],debug=debug)
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
        p = subprocess.SpawnRemoteCmd(sshhost,sshuser,'hostname',debug=debug)
        o = open('test.out','w')

        code = p.run(stdout=o)
        self.assertEqual(code,subprocess.SPAWNED,"Command failed to run")

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
            p = subprocess.SpawnRemoteCmd(sshhost,sshuser,'sleep 10',debug=debug)
            code = p.run()
            self.assertEqual(code,subprocess.SPAWNED,"Command failed to run")
            code1 = p.wait(timeout=1000)
            code2 = p.wait(timeout=1000)
            code = p.kill()
            print 'kill code',code
            code3 = p.wait(timeout=1000)
            print 'run,wait codes',code, code3
            self.assertEqual([code1,code2,code3],[999,999,-2])
        else:
            # on linux, no waiting on pid yet
            p = subprocess.SpawnRemoteCmd(sshhost,sshuser,'sleep 10',debug=debug)
            code = p.run()
            self.assertEqual(code,subprocess.SPAWNED,"Command failed to run")
            print 'sleep 3',
            time.sleep(3)
            code = p.kill()
            self.assertEqual(code,0,"Unexpected code %d from kill" % code)
            code = p.wait()
            self.assertEqual(code,-2,"Unexpected code %d from wait" % code)

class testPipeRemoteCmd(unittest.TestCase):
    """ rsh/plink + host + simple command"""
    def testA(self):
        """Check PipeRemoteCmd by issuing hostname over ssh"""
        self.proc = subprocess.PipeRemoteCmd(sshhost,sshuser,'hostname',debug=debug)
        self.proc.run()
        output=self.proc.get_output()
        self.assertNotEqual(output,None,"Command failed ro tun")
        tester=output[0][:3]
        self.assertEqual(tester,chkstr)

class testSpawnRemoteCmd(unittest.TestCase):
    """ rsh/plink + host + simple command"""
    def testA(self):
        """check by issuing hostname over ssh"""
        self.proc = subprocess.SpawnRemoteCmd(sshhost,sshuser,'hostname',debug=debug)
        code = self.proc.run()
        self.assertEqual(code,subprocess.SPAWNED,"Command failed to run")

        code = self.proc.wait()
        self.assertEqual(code,0,"Wait returned unexpected code")

        output=self.proc.get_output()
        #error=self.proc.get_error()
        #print 'output:',output
        #print 'error:',error

        tester=output[:3]
        self.assertEqual(tester,chkstr)

if __name__ == "__main__":

    import sys
    print sys.argv
    if len(sys.argv) == 2 and sys.argv[1] == 'sel':
        # Build a test suite with required cases and run it

        myTestSuite = unittest.TestSuite()

        #myTestSuite.addTest(testSpawn("testA"))
        #myTestSuite.addTest(testSpawnRemoteProcess("testA"))
        #myTestSuite.addTest(testSpawnRemoteProcess("testB"))
        #myTestSuite.addTest(testPipeRemoteCmd("testA"))
        myTestSuite.addTest(testSpawnRemoteCmd("testA"))

        runner = unittest.TextTestRunner()
        runner.run(myTestSuite)
    else:
        print 'Running all tests'
        # Run all tests automatically
        unittest.main()


    
