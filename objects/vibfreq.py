#
#    This file is part of the CCP1 Graphical User Interface (ccp1gui)
# 
#   (C) 2002-2007 CCLRC Daresbury Laboratory
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
"""A container class for normal modes and associated the vibrational
frequencies.
"""

class VibFreqSet:
   def __init__(self):
      self.vibs = []
      self.title = 'Normal Modes'
      self.vibtitles = []
      self.vib_count = 0

   def list(self):
      print 'Vib Freq Set - freqs:',
      for v in self.vibs:
         print v.title,

   def add_vib(self,disp,freq=None):
      """convenience function to add a new vibration making sure the
      title is unique (if not, the selector widget won't work..)"""
      v = VibFreq(self.vib_count)
      self.vib_count = self.vib_count+1
      self.vibs.append(v)
      v.displacement=disp
      if freq is not None:
         self.set_freq(v,freq)
      else:
         v.title='v #'+str(self.vib_count)
         v.freq = -1
      return v

   def set_freq(self, v, freq):
      v.freq = freq
      for discriminator in [ '', '_2', '_3', '_4', '_6','_7','_8']:
         title = 'v'+str(freq)+discriminator
         try:
            self.vibtitles.index(title)
         except ValueError:
            break
      v.title = title
      self.vibtitles.append(title)

class VibFreq:
   def __init__(self,index):
      self.index=index
      self.name=None
      self.reference = None
      self.freq=0.0
      self.title="v???"

   def get_name(self):
      return self.title

if __name__ == "__main__":
   v = VibFreqSet()
   v1 = v.add_vib([],100)
   v2 = v.add_vib([])
   v.set_freq(v2,100)
   v.list()
