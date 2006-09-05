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
#
#
# Job Editor class
#
class JobEditor(Pmw.MegaToplevel):

    frameWidth       = 300
    frameHeight      = 100
    if sys.platform == 'mac':
        pass
    elif sys.platform[:3] == 'win':
        frameWidth       = 350
        frameHeight      = 150 
    elif sys.platform[:5] == 'linux':
        pass
    else:
        pass

    update_interval=200

    def __init__(self,root,manager,report_func=None):

        Pmw.MegaToplevel.__init__(self, root)
        self.root = root
        self.manager=manager
        self.sel_height = 20

        self.title('Job Manager')

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
              title = "Info", iconpos='w', icon_bitmap='info',
              buttons = ("Dismiss",))

        self.error.withdraw()
        self.info.withdraw()
        self.warning.withdraw()

        self.geometry('%dx%d' % (self.frameWidth, self.frameHeight) )

        #self.error.configure(message_text='test')
        #self.error.show()

    def show(self, **kw):
        m = re.match('(\d+)x(\d+)\+(\d+)\+(\d+)',self.root.geometry())
        msx,msy,mpx,mpy = int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4))
        print 'master geom',    msx,msy,mpx,mpy
        #self.geometry('%dx%d+%d+%d' % (self.frameWidth, self.frameHeight, mpx+msx+8,mpy+msy+24))
        self.geometry('+%d+%d' % (mpx+msx+8,mpy+msy+24))
        apply(Pmw.MegaToplevel.show,(self,),kw)

    def update(self):
        """ update of the status of the job editor widget and reschedule the next call"""
        print 'job editor update'
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
        self.kill.pack() 
        self.line.pack(side='bottom')
        self.sel.pack(fill='both',expand=1)
        self.frame.pack(fill='both',expand=1)

    def __click_job(self):
        cursel = self.sel.curselection()
        nsel = len(cursel)
        sels = self.sel.getcurselection()

    def __kill_job(self):
        sels = self.sel.getcurselection()
        print sels
        for sel in sels:
            words = string.split(sel)
            print words
            try:
                ix = int(words[0])
                self.manager.active_jobs[ix-1].kill()
            except ValueError:
                pass

    def check_jobs(self):
        """Load the selectionbox with the current status information
        on all the jobs
        Also runs any monitor code in the master thread. This can perform
        such tasks as updating a molecule or diagnostic graph
        """
        items = []
        items.append('Job# Host       Jobname  Status  Job Step')

        i = 0
        j = 1
        error_messages = []
        warning_messages = []
        info_messages = []

        for job in self.manager.active_jobs:
            if job.active_step:
                yyy = job.active_step.name
            else:
                yyy = ''

            txt = '%2d : %-10s %-8s %-10s %s' % (i+1,job.host,job.name,job.status,yyy)
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
                        job.tidy(code=1)
                    except Exception, e:  
                        #info_messages.append(str(e))
                        #items.append(str(e))
                        #job.status = JOBSTATUS_FAILED
                        #job.msg = job.msg + (str(e))
                        # delete to stop execution again
                        pass
                    job.tidy = None

            if job.status == JOBSTATUS_WARNING:
                if job.msg and job.popup:
                    warning_messages.append(job.msg)
                    job.popup=0

            if job.status == JOBSTATUS_OK:
                if job.msg and job.popup:
                    info_messages.append(job.msg)
                    job.popup=0

            if job.status == JOBSTATUS_RUNNING:
                try:
                    # Run any monitor code
                    if job.monitor:
                        if job.debug:
                            print 'Running job monitor'
                        job.monitor()
                except Exception, e:
                    print 'update of monitor code failed',e

            if job.status == JOBSTATUS_DONE:
                if job.msg and job.popup:
                    info_messages.append(job.msg)
                    job.popup=0

                if job.tidy:
                    print 'Executing tidy function'
                    try:
                        job.tidy()
                    except Exception, e:  
                        info_messages.append(str(e))
                        items.append(str(e))
                        job.status = JOBSTATUS_FAILED
                        job.msg = (str(e))
                        # delete to stop execution again
                        job.popup=0                        
                    job.tidy = None

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
            self.error.configure(message_text = msg)
            #self.error.activate()
            self.error.show()
        for msg in warning_messages:
            self.warning.configure(message_text = msg)
            #self.warning.activate()
            self.warning.show()
        for msg in info_messages:
            self.info.configure(message_text = msg)
            #self.info.activate()
            self.info.show()

def testpy():
    print 'testpy'
    time.sleep(3)
    print 'testpy done'

def crappy():
    time.sleep(1)
    i = j
    return 0,"crappy OK"

def sleepy():
    time.sleep(1)
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

    job = jobmanager.BackgroundJob()
    manager.RegisterJob(job)
    job.add_step(PYTHON_CMD,'sleepy',proc=sleepy)
    job.add_step(PYTHON_CMD,'crappy',proc=crappy)
    job.run()
    print 'XXX'

if __name__ == "__main__":

    root = Tkinter.Tk()
    button = Tkinter.Button(root,text='Start test',command=testit)
    button.pack()

    manager = jobmanager.JobManager()
    job_editor = jobmanager.JobEditor(root,manager)
    job_editor.show()
    root.mainloop()

