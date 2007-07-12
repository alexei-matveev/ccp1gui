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
"""A Pmw-based widget to show status of jobs

At present only interaction supported is kill.
Still a lot of work to do under Unix.
"""
import os
import sys
import time
import Tkinter
import Pmw
import sys

import string
import jobmanager
from jobmanager.subprocess import *
from jobmanager.job import *
from jobmanager.jobeditor import *
from jobmanager.jobthread import *
import cPickle # to pickle jobs
#
#
# Job Editor class
#
class JobEditor(Pmw.MegaToplevel):

    frameWidth       = 600
    frameHeight      = 100
    if sys.platform == 'mac':
        pass
    elif sys.platform[:3] == 'win':
        frameWidth       = 350
        frameHeight      = 150 
    else:
        pass

    update_interval=200

    def __init__(self,root,manager,report_func=None):

        Pmw.MegaToplevel.__init__(self, root)
        self.root = root
        self.manager=manager
        self.sel_height = 20
        self.title('Job Manager')
        self.debug = 0

        self.__build()
        self.report_func = report_func
        self.old_items = []
        self.check_jobs()
        self.after(self.update_interval,self.update)

        self.error = Pmw.MessageDialog(self.root,
              title = "Error", iconpos='w', icon_bitmap='error',
              buttons = ("Dismiss",))

        self.warning = Pmw.MessageDialog(self.root,
              title = "Warning", iconpos='w', icon_bitmap='error',
              buttons = ("Dismiss",))

        self.info = Pmw.MessageDialog(self.root,
              title = "Job Editor Info", iconpos='w', icon_bitmap='info',
              buttons = ("Dismiss",))
        
        self.error.withdraw()
        self.info.withdraw()
        self.warning.withdraw()

        self.geometry('%dx%d' % (self.frameWidth, self.frameHeight) )

        # Ensure that when the user kills us with the window manager we behave as expected
        self.userdeletefunc( lambda s=self: s.ask_quit() )
        self.usermodaldeletefunc( lambda s=self: s.ask_quit() )
        
        #self.error.configure(message_text='test')
        #self.error.show()

    def Error(self,message):
        """Display the error dialog with message"""
        self.error.configure(message_text = message)
        self.error.show()

    def show(self, **kw):
        m = re.match('(\d+)x(\d+)\+(-?\d+)\+(-?\d+)',self.root.geometry())
        msx,msy,mpx,mpy = int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4))
        #print 'master geom',    msx,msy,mpx,mpy
        #self.geometry('%dx%d+%d+%d' % (self.frameWidth, self.frameHeight, mpx+msx+8,mpy+msy+24))
        self.geometry('+%d+%d' % (mpx+msx+8,mpy+msy+24))
        apply(Pmw.MegaToplevel.show,(self,),kw)

    def update(self):
        """ update of the status of the job editor widget and reschedule the next call"""
        try:
            self.check_jobs()
            self.after(self.update_interval,self.update)
        except Exception, e:
            print 'update of job editor failed',e
            #self.after(self.update_interval,self.update)        

    def __build(self):
        interior = self.interior()
        self.frame = self.createcomponent('frame', (), None, Tkinter.Frame,
                                          (interior,), height=12, width=500)
        # Main atom selection/display widet
        fixedFont = Pmw.logicalfont('Courier',size=12)
        self.sel = self.createcomponent('selector', (), None,
                                        Pmw.ScrolledListBox,
                                        (self.frame,),
                                        listbox_selectmode='extended',
                                        listbox_height=self.sel_height,
                                        listbox_font=fixedFont,
                                        listbox_background='white',
                                        selectioncommand=self.__click_job)

        self.line =         self.createcomponent('buttonframe', (), None,
                                                 Tkinter.Frame,(self.frame,),
                                                 height=10, width=300 )

        self.kill =       self.createcomponent('killbutton', (), None,
                                               Tkinter.Button,(self.line,),
                                               text="Kill",
                                               command=self.__kill_job)
        self.kill.pack(side='left') 

#         self.suspendbutton =       self.createcomponent('suspendbutton', (), None,
#                                                Tkinter.Button,(self.line,),
#                                                text="Suspend",
#                                                command=self.suspend)
#         self.suspendbutton.pack(side='left')
        
#         self.savebutton =       self.createcomponent('savebutton', (), None,
#                                                Tkinter.Button,(self.line,),
#                                                text="Save",
#                                                command=self.save)
#         self.savebutton.pack(side='left')
        
#         self.startbutton =       self.createcomponent('startbutton', (), None,
#                                                Tkinter.Button,(self.line,),
#                                                text="Start",
#                                                command=self.start)
#         self.startbutton.pack(side='left') 
#         self.removebutton =       self.createcomponent('removebutton', (), None,
#                                                Tkinter.Button,(self.line,),
#                                                text="Remove",
#                                                command=self.remove)
#         self.removebutton.pack(side='left') 

        self.line.pack(side='bottom')
        self.sel.pack(fill='both',expand=1)
        self.frame.pack(fill='both',expand=1)

    def __click_job(self):
        cursel = self.sel.curselection()
        nsel = len(cursel)
        sels = self.sel.getcurselection()

    def __kill_job(self):
        """ Kill the selected jobs"""
        jobs = self.__get_sel_jobs()

        if not jobs:
            return
        
        for job in jobs:
            try:
                job.kill()
                #self.manager.RemoveJob( job )
            except Exception,e:
                self.Error("Error killing job: %s\n%s" % (job.name,e) )
                continue
            
    def __get_sel_jobs( self ):
        """Return a list of the currently selected jobs """

        jobs = []
        sels = self.sel.getcurselection()
        for sel in sels:
            words = string.split(sel)
            try:
                ix = int(words[0])
                job = self.manager.registered_jobs[ix-1]
                jobs.append( job )
            except ValueError:
                pass
            except IndexError:
                pass
        if len(jobs):
            return jobs
        else:
            return None

    def check_jobs(self):
        """Load the selectionbox with the current status information
        on all the jobs
        Also runs any monitor code in the master thread. This can perform
        such tasks as updating a molecule or diagnostic graph
        """
        items = []
        items.append('%-7s : %-20s : %-8s : %-10s : %-s' % ('Job No.','Host','Jobname','Status','Job Step'))
        i = 0
        j = 1
        error_messages = []
        warning_messages = []
        info_messages = []

        # Now loop over registered jobs
        for job in self.manager.registered_jobs:
            if job.active_step:
                yyy = job.active_step.name
            else:
                yyy = ''

            txt = '%-7d : %-20s : %-8s : %-10s : %s' % (i+1,job.host,job.name,job.status,yyy)
            items.append(txt)

            if job.status == JOBSTATUS_FAILED:
                txt = '*** ' + job.msg
                items.append(txt)
                if self.report_func:
                    self.report_func(job.msg)

                if job.msg and job.popup:
                    error_messages.append(job.msg)
                    job.popup=0

                # execute this but dont report failures
                # ... they might confuse the situation
                if job.tidy:
                    print 'Executing tidy function (on Failure)'
                    try:
                        job.tidy(1)
                    except Exception, e:  
                        #info_messages.append(str(e))
                        #items.append(str(e))
                        #job.status = JOBSTATUS_FAILED
                        #job.msg = job.msg + (str(e))
                        # delete to stop execution again
                        print "job tidy error"
                        print e
                        import traceback;traceback.print_exc()
                        pass
                    job.tidy = None

                # done everything so remove from active jobs
                #self.manager.RemoveJob(job)

            elif job.status == JOBSTATUS_WARNING:
                if job.msg and job.popup:
                    warning_messages.append(job.msg)
                    job.popup=0

##            if job.status == JOBSTATUS_OK:
##                if job.msg and job.popup:
##                    info_messages.append(job.msg)
##                    job.popup=0

            elif job.status == JOBSTATUS_DONE:
                if job.msg and job.popup:
                    info_messages.append(job.msg)
                    job.popup=0

                if job.tidy:
                    print 'Executing tidy function after successful completion'
                    try:
                        job.tidy(0)
                    except Exception, e:
                        print "Exception executing job tidy"
                        import traceback;traceback.print_exc()
                        #info_messages.append(str(e))
                        error_messages.append(str(e))                        
                        items.append(str(e))
                        job.status = JOBSTATUS_FAILED
                        job.msg = (str(e))
                        # delete to stop execution again
                        job.popup=0                        
                    job.tidy = None
                    
                # done everything so remove from registered jobs
                #self.manager.RemoveJob(job)

            else:
            # Assume any other job status means that the job is still running
            #if job.status == JOBSTATUS_RUNNING:
                try:
                    # Run any monitor code
                    if job.monitor:
                        if job.debug:
                            print 'Running job monitor'
                        job.monitor()
                except Exception, e:
                    print 'update of monitor code failed',e

            # Increment the job counter
            i = i + 1

        if items != self.old_items:
            old_sel = self.sel.curselection()
            self.sel.setlist(items)
            for t in old_sel:
                self.sel.select_set(t)
            self.sel.see(len(items)-1)
            self.old_items = items

        # seems modal grab by these dialogs causes problems
        # when run from GUI
        # perhaps related to threading, or some problem with
        # root
        # (perhaps XP specific)

        for msg in error_messages:
            #self.error.configure(message_text = msg)
            #self.error.activate()
            #self.error.show()
            self.Error( msg )
        for msg in warning_messages:
            self.warning.configure(message_text = msg)
            #self.warning.activate()
            self.warning.show()
        for msg in info_messages:
            self.info.configure(message_text = msg)
            #self.info.activate()
            self.info.show()

    def ask_quit(self):
        """If there are active jobs, ask the user to kill/suspend them, otherwise, just quit.
        """

        jobs = self.manager.registered_jobs
        if len( jobs) > 0:
            for job in jobs:
                if job.status not in [ JOBSTATUS_IDLE, JOBSTATUS_KILLED, JOBSTATUS_FAILED,
                                       JOBSTATUS_STOPPED, JOBSTATUS_DONE, JOBSTATUS_SAVED ]:
            
                    print "got jobs"
                    msg = "You still have jobs active! Please stop or kill the jobs with\n" +\
                          "the jobmanager before exiting the CCP1GUI!"
                    self.Error( msg )
                    return 1
        
        self.quit()

    def quit(self):
        """ Withdram the job editor """
        self.withdraw()

    def start_job(self,job):
        """Start a job running
        Might be issues with storing the thread in the job object?
        """

        if self.debug:
            print "jobEditor start_job: ",job
            print job.steps

        # Display the job editor
        self.show()
            
        if job.thread:
            print "got a job thread ",job.thread
            if job.thread.isAlive():
                raise JobError,"This calculation is running already!"

        JobThread(job).start()
        
        if job not in self.manager.registered_jobs:
            self.manager.RegisterJob(job)

    def suspend(self):
        """
        See if the job can be stopped and call it's stop method
        """
        jobs = self.__get_sel_jobs()
        if not jobs:
            return
        for job in jobs:
            try:
                job.stop()
            except JobError,e:
                self.Error("Error stopping job: %s !\n%s" % (job.name,e) )
                continue
            if job.status != JOBSTATUS_STOPPED:
                self.Error("Error stopping job: %s!" % job.name )
                continue
            # Clear out the thread - not sure if this the best place to do this.
            job.thread = None
            
    def start(self):
        """
        Start the selected jobs
        """
        jobs = self.__get_sel_jobs()
        if not jobs:
            return
        for job in jobs:
            if job.status != JOBSTATUS_STOPPED:
                self.Error("Can only Start a stopped job!")
                return
            print "jobmanager Starting job ",job.name
            try:
                self.start_job( job )
            except Exception,e:
                self.Error("Error Starting job: %s\n%s" % (job.name, e ))

    def save(self):
        """Save the selected jobs"""
        jobs = self.__get_sel_jobs()
        if not jobs:
            return
        for job in jobs:
            if job.status != JOBSTATUS_STOPPED:
                self.Error( "Can only save a stopped job!" )
                continue
            try:
                self.pickle_job( job )
                job.status = JOBSTATUS_SAVED
            except Exception,e:
                self.Error( "Error pickling job:%s\n%s" % (job.name,e) )
                continue
        

    def remove(self):
        """Remove the selected job from the job manager"""
        jobs = self.__get_sel_jobs()
        if not jobs:
            return
        
        for job in jobs:
            if job.status not in [JOBSTATUS_STOPPED, JOBSTATUS_IDLE, JOBSTATUS_KILLED,
                                  JOBSTATUS_FAILED, JOBSTATUS_STOPPED, JOBSTATUS_DONE,
                                  JOBSTATUS_SAVED]:
                self.Error( "Error removing job: %s!\nCan only remove a completed job!" % job.name )
                return

            self.manager.RemoveJob(job)

            
    def prdict(self,obj,name,depth):
        """Cycle through an object and try and pickle the various
           objects - used for debugging pickling errors (see pickle_job)
        """
        try:
            myclass = obj.__class__
        except:
            myclass = ""

        try:
            fobj = open('junk.pkl','w')
            p = cPickle.Pickler(fobj)
            p.dump(obj)
            fobj.close()
            pkl='pickled ok'
        except:
            pkl='NOT PICKLABLE'
            

        for i in range(depth):
            print "   ",
        print name, pkl, obj, myclass

        try:
            dicts = obj.__dict__.keys()
        except AttributeError:
            dicts = []

        for y in dicts:
            o = obj.__dict__[y]
            self.prdict(o,y,depth+1)

    def pickle_job(self,job):
        """Pickle a stoppped Job"""
        
        if job.status != JOBSTATUS_STOPPED:
            self.Error( "Can only pickle a stopped job!" % job.name )
            return 1
        
        print "pickling job ",job.name
        fileobj = self._get_jobfile(job)
        p = cPickle.Pickler( fileobj )

        # Dirty hack - nuke everything that won't pickle will have to
        # deal with the mess when we unpickle the job.calculation
        # see restore_saved_jobs in viewer/main.py
        job.tidy = None # Looks like this won't pickle
        if job.calc.job:
            job.calc.job = None # this either
        i=0
        for step in job.steps:
            if step.type == PYTHON_CMD: # or these...
                print "Job step is a PYTHON_CMD and cannot be pickled!"
                job.steps[i] = None
            i+=1

        # For debugging pickling errors
        #self.prdict(job,'TOP',0)
        # Job should now be in a position to pickle
        p.dump( job )
        print "dumped ",job
        fileobj.close()

    def _get_jobfile(self,job):
        """
        Create a unique filename for the job and then return the opened file
        Might be best to work with jobID's 
        """
        filename = str(id(job))
        # strip any minus sign
        if filename[0] == '-':
            filename = filename[1:]
        filename+='.job'
        return open( filename, 'w' )

def testpy():
    print 'testpy'
    time.sleep(3)
    print 'testpy done'

def crappy():
    time.sleep(1)
    i = j
    return 0,"crappy OK"

def sleepy():
    done=None
    i=0
    while not done:
        print "job sleeping"
        time.sleep(5)
        i+=1
        if i == 10:
            done = 1
            
    return 1,"sleepy done"

def testit():

    if 0:
        job = jobmanager.ForegroundJob(name='test1')
        job.add_step(COPY_OUT_FILE,'transfer input',local_filename='small.in')
        job.add_step(PYTHON_CMD,'python cleanup',proc=sleepy)
        job.add_step(RUN_GAMESSUK,'run gamess',jobname='small')
        job.add_step(PYTHON_CMD,'python cleanup',proc=sleepy)
        job.add_step(COPY_BACK_FILE,'recover punchfile',remote_filename='small.pun')
        job.add_step(PYTHON_CMD,'python cleanup',proc=testpy)

        manager.RegisterJob(job)
        job.run()

        job = ForegroundJob(name='test2')
        job.add_step(COPY_OUT_FILE,'transfer input',local_filename='small.in')
        job.add_step(PYTHON_CMD,'python cleanup',proc=sleepy)
        job.add_step(RUN_GAMESSUK,'run gamess',jobname='small')
        job.add_step(COPY_BACK_FILE,'recover punch',remote_filename='small.pun')
        #job.add_step(PYTHON_CMD,'python cleanup',proc=testpy)

        manager.RegisterJob(job)
        job.run()

    if 0:
        job = jobmanager.BackgroundJob()
        manager.RegisterJob(job)
        job.add_step(PYTHON_CMD,'sleepy',proc=sleepy)
        #job.add_step(PYTHON_CMD,'crappy',proc=crappy)
        job_thread = JobThread(job)
        job_thread.start()
        print 'XXX'

        
    if 0:
        import getpass
        rc_vars[ 'machine_list'] = ['lake.esc.cam.ac.uk']
        rc_vars[ 'nproc'] = '1'
        rc_vars['srb_config_file'] = os.path.expanduser('~/srb.cfg')
        rc_vars['srb_executable'] = 'gamess'
        rc_vars['srb_executable_dir'] = '/home/jmht.eminerals/test/executables'
        rc_vars['srb_input_dir'] = '/home/jmht.eminerals/test/test1'
        rc_vars['srb_output_dir'] = '/home/jmht.eminerals/test/test1'
        rc_vars['rmcs_user'] = getpass.getuser()
        rc_vars['rmcs_password'] = '4235227b51436ad86d07c7cf5d69bda2644984de'
        rc_vars['myproxy_user'] = getpass.getuser()
        rc_vars['myproxy_password'] = 'pythonGr1d'
        job = jobmanager.RMCSJob()
        manager.RegisterJob(job)
        job.add_step(COPY_OUT_FILE,'add srb file',local_filename='c2001_a.in')
        job.add_step(RUN_APP,'run rmcs',stdin_file='c2001_a.in',stdout_file='c2001_a.out')
        job.add_step(COPY_BACK_FILE,'Get srb results',local_filename='c2001_a.out')
        #job.run()
        
        job_thread = jobmanager.JobThread(job)
        try:
            #self.CheckData()
            job_thread.start()
        except Exception,e:
            print 'exception'
            print str(e)

    if 0:
        job = jobmanager.GrowlJob()
        #job.job_parameters['hosts'] = ['scarf.rl.ac.uk']
        job.job_parameters['hosts'] = ['scarf.rl.ac.uk']
        job.job_parameters['stdout'] = 'sleep.out'
        job.job_parameters['executable'] = 'sleep.sh'
        manager.RegisterJob(job)
        job.add_step( RUN_APP,
                      "Growl test")
        job_thread = JobThread(job)
        try:
            job_thread.start()
        except Exception,e:
            print "Got Exception"
            sys.exit(1)
        print 'XXX'


    if 0:
        job = jobmanager.BackgroundJob()
        manager.RegisterJob(job)
        #job.add_step(PYTHON_CMD,'sleepy',proc=sleepy)
        #job.add_step(PYTHON_CMD,'crappy',proc=crappy)
        #job_thread = JobThread(job)
        #job_thread.start()
        #print 'XXX'

    if 1:
        job = jobmanager.DummyJob()
        manager.RegisterJob(job)
        job.add_step(RUN_APP,'dummy')
        #job.add_step(PYTHON_CMD,'crappy',proc=crappy)
        job_thread = JobThread(job)
        job_thread.start()
        print 'XXX'


if __name__ == "__main__":

    root = Tkinter.Tk()
    button = Tkinter.Button(root,text='Start test',command=testit)
    button.pack()

    manager = jobmanager.JobManager()
    job_editor = jobmanager.JobEditor(root,manager)
    job_editor.show()
    root.mainloop()

