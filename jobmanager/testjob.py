# Import python modules
import os
import unittest

# Import own modules
import jobmanager

class testGlobusJob(unittest.TestCase):
    """
    Test that the Globus job stuff works

    """

    HOST= 'dl1.nw-grid.ac.uk'
    stdin='stdin'
    stdout='stdout'
    stderr='stderr'


    def testJobmanagerFork(self):
        """
        Test the fork jobmanager when we are copying back several files
        and we have a number of arguments
        We use dd to test this as it's universally available and has different
        behaviour when using variable numbers of arguments

        """

        # Create a simple input file
        myinput ="""first line
second line
third line
fourth line
fifth line
sixth line
"""
        f = open( self.stdin ,'w' )
        f.writelines( myinput )
        f.close()
        

        # Create the job 
        job = jobmanager.GlobusJob()
        #job.debug=1

        # Set the parameters
        executable = '/bin/dd'
        arguments = ['bs=1','count=23','conv=ucase']
        job.set_parameter( 'executable', executable )
        job.set_parameter( 'jobmanager', 'jobmanager-fork' )
        job.set_parameter( 'host' , self.HOST )
        job.set_parameter( 'stdin' , self.stdin )
        job.set_parameter( 'arguments' , arguments )
        job.set_parameter( 'stdout' ,self.stdout )
        job.set_parameter( 'stderr' ,self.stderr )

        # Add the steps that define the job
        # Copy out the input
        job.add_step( jobmanager.COPY_OUT_FILE,
                      'transfer input: %s' % self.stdin,
                      local_filename=self.stdin,
                      remote_filename=self.stdin)

        # Run the application
        job.add_step(
            jobmanager.RUN_APP,
            'Running commmand: %s %s' % (executable, str(arguments) ),
            stdin_file=None
            )

        # Copy back stdout
        job.add_step(
            jobmanager.COPY_BACK_FILE,
            'Copying back stdout',
            remote_filename=self.stdout
            )
        
        # Copy back stderr
        job.add_step(
            jobmanager.COPY_BACK_FILE,
            'Copying back stderr',
            remote_filename=self.stderr
            )


        # Run the job
        code = job.run()

        # See how it went
        # Check if the job itself worked
        self.assertEqual( code, 0,
                         "Job Failed with code: %s!\n\n%s" % ( str(code),job.msg )
                          )

        # Check the stdout - first word on second line should be SECOND
        f = open(self.stdout,'r')
        line = f.readline()
        line = f.readline().strip()
        word1 = line.split()[0]
        f.close()
        self.assertEqual( word1, 'SECOND',
                          "stdout file was incorrect: 1st word on 2nd line was: %s" % word1)

        # Check the stdout - first word on 3rd line should be 23 for n bytes transferred
        f = open(self.stderr,'r')
        line = f.readline()
        line = f.readline()
        line = f.readline().strip()
        nbytes = int(line.split()[0])
        f.close()
        self.assertEqual( nbytes, 23,
                          "stder file was incorrect: 1st word on 3rd line was: %s" % nbytes)
        # Then clean up
        os.remove( self.stdin )
        os.remove( self.stdout )
        os.remove( self.stderr )



if 0:
    unittest.main()
else:
    myTestSuite = unittest.TestSuite()
    myTestSuite.addTest( testGlobusJob("testJobmanagerFork") )
    runner = unittest.TextTestRunner()
    runner.run(myTestSuite)


