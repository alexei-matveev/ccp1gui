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
import time

class SlaveThread(threading.Thread):
   '''The slave thread runs separate thread
      For control it has 
      - a lock (not used at the moment)
      - a queue object to communicate with the GUI thread
      - a procedure to run
      '''
   def __init__(self,lock,queue,proc):
      threading.Thread.__init__(self,None,None,"JobMan")
      self.lock       = lock
      self.queue      = queue
      self.proc       = proc

   def run(self):
      '''repeatedly call the specified procedure'''
      print 'running'
      self.queue.put(1)
      try:
         while 1:
             try:
                # Execute the proceedure of interest
                code = self.proc()
                # Return the code via the queue
                # In the case of code 99 we exit
                if code == 99:
                   self.queue.put(99)
                   return
                else:
                   self.queue.put(code)
             except:
                pass

             time.sleep(0.3)

      except RuntimeError, e:
         self.queue.put(-1)
