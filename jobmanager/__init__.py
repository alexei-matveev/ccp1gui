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
"""Job manager and editor Tkinter interface to control jobs 
"""

from jobmanager.job import *
from jobmanager.subprocess import *
from jobmanager.jobeditor import *
from jobmanager.jobthread import *

if sys.platform[:3] == 'win':
    import jobmanager.winprocess

# Constants
#
MODIFIED  = "Modified"
SUBMITTED = "Submitted"
RUNNING   = "Running"
KILLED    = "Killed"
DONE      = "Done"


class JobManager:

    def __init__(self):
        self.active_jobs = []

    def RegisterJob(self,job):
        self.active_jobs.append(job)
