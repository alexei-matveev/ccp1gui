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
import threading

class JobThread(threading.Thread):
    """A simple class to execute a job from."""

    def __init__(self,job):
        threading.Thread.__init__(self,None,None,"JobMan")
        self.job        = job
        self.debug=0
    #
    # need to find out why thread errors are not
    # handled properly
    #
    #  bare except works ok, but perhaps 
    #  it would be better to trap failure within a job step ??
    #
    def run(self):
        """Run the calculation in a separate thread"""
        try:
            if self.debug:
                print 'JobThread: starting'
            self.job.run()
        except RuntimeError, e:
            if self.debug:
                print 'JobThread: exception caught'
        if self.debug:
            print 'JobThread: exiting'
