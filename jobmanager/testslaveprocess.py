import slaveprocess
import unittest

class testSlaveSpawn(unittest.TestCase):
    """fork/pythonwin process management with extra process"""

    # this is not longer needed for GUI operation
    # it also has not been adapted to take cmd + args separately
    # however it does seem to work
    def testA(self):
        """check echo on local host using stdout redirection"""
        self.proc = slaveprocess.SlaveSpawn('echo a b',debug=1)
        o = open('test.out','w')
        self.proc.run(stdout=o)
        self.proc.wait()
        o.close()
        o = open('test.out','r')
        output = o.readlines()
        print 'output=',output
        self.assertEqual(output,['a b\n'])

if __name__ == "__main__":
    if 1:
        # Run all tests automatically
        unittest.main()
    else:
        pass

