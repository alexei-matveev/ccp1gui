#
# unit tests for the job and process classes
#
import subprocess
import unittest

# Specify 
sshhost='login.hpcx.ac.uk'

class testSpawn(unittest.TestCase):
    """fork/pythonwin process management"""

    # implementation notes. get_output is available from spawn but
    # it doesn't seem to do anything

    def testA(self):
        """check echo on local host using a file connection on stdout"""
        self.proc = subprocess.Spawn('echo',['a','b'],debug=1)
        o = open('test.out','w')
        self.proc.run(stdout=o)
        self.proc.wait()
        o.close()
        o = open('test.out','r')
        output = o.readlines()
        print 'output=',output
        self.assertEqual(output,['a b\n'])

class testSpawnRemoteProcess(unittest.TestCase):
    """fork/pythonwin process management"""

    def testA(self):
        """Execute ssh and check output"""
        # on windows, the code returns 999 from wait until the
        # process has dies, then -2
        print 'Test Spawn for Remote Process'
        p = subprocess.SpawnRemoteCmd(sshhost,'hostname',debug=0)
        o = open('test.out','w')
        code = p.run(stdout=o)
        code1 = p.wait()
        print 'run code',code
        print 'wait code',code1
        #self.assertEqual([code1,code2],[0,-2])
        o.close()
        o = open('test.out','r')
        output = o.readlines()
        print 'output=',output
        self.assertNotEqual(output,None,"Command failed ro tun")
        tester=output[0][:3]
        self.assertEqual(tester,'l1f')

    def testB(self):
        """Execute ssh and check that it is capable of being killed"""
        # on windows, the code returns 999 from wait until the
        # process has dies, then -2
        print 'Test Spawn for Remote Process'
        p = subprocess.SpawnRemoteCmd(sshhost,'sleep 4',debug=0)
        code = p.run()
        print 'run code',code
        code1 = p.wait(timeout=1000)
        code2 = p.wait(timeout=1000)
        code = p.kill()
        print 'kill code',code
        code3 = p.wait(timeout=1000)
        print 'wait codes',code1, code2, code3
        self.assertEqual([code1,code2,code3],[999,999,-2])


class testRemoteProcess(unittest.TestCase):
    """ rsh/plink + host + simple command"""
    def setUp(self):
        self.proc = subprocess.RemoteProcess(sshhost,'hostname',debug=0)
    def testA(self):
        """check by issuing hostname over ssh"""
        self.proc.run()
        output=self.proc.get_output()
        self.assertNotEqual(output,None,"Command failed ro tun")
        tester=output[0][:3]
        self.assertEqual(tester,'l1f')

if __name__ == "__main__":

    if 1:
        # Run all tests automatically
        unittest.main()
    else:
        # Build a test suite with required cases and run it

        myTestSuite = unittest.TestSuite()

        #myTestSuite.addTest(testSpawn("testA"))
        myTestSuite.addTest(testSpawnRemoteProcess("testA"))
        myTestSuite.addTest(testSpawnRemoteProcess("testB"))
        #myTestSuite.addTest(testSlaveSpawn("testA"))
        #myTestSuite.addTest(testRemoteProcess("testA"))

        runner = unittest.TextTestRunner()
        runner.run(myTestSuite)
    
