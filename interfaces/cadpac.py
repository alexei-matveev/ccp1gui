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
#######################################################################
#
#  This file implements the CADPAC specific calculation and
#  calculation editor classes. 
#
#######################################################################

import tkFileDialog
from filemolden import *
import os
import string

from qm import *

class CADPACCalc(QMCalc):
    '''CADPAC specifics.'''

    def __init__(self,title="untitled"):
        print self
        QMCalc.__init__(self,"CADPAC",title)
        self.set_task("energy")
        self.set_theory("RHF")
        self.set_input("basis","631G*")
        self.set_parameter("scf_maxcyc",50)
        self.set_parameter("scf_threshold",6)
        self.set_parameter("scf_level_init",1.0)
        self.set_parameter("scf_level_it",10)
        self.set_parameter("scf_level_final",0.1)
        self.set_parameter("predirectives",
             "#file ed3 ed3 keep\n"+
             "#memory 20000000\n"+
             "#time 600\n")
        self.set_parameter("classidirectives",
             "#restart new\n#super off nosym\n#adapt off\n"+
             "#integral high\n#accuracy 30 15\n#bypass one two\n"+
             "#mfile memory\n")
        self.set_parameter("classiidirectives",
             "#maxcyc 50\n#threshold 7\n#swap\n#  1 2\n#end\n"+
             "#dft lebedev element c 302\n"+
             "#dft log element c 75 3.0\n")
        self.set_parameter("classiiidirectives",
             "#core\n#  1 to 10\n#end\n"+
             "#active\n#  11 to 50\n#end\n"+
             "#direct 8 6 34\n#diagmode vmin 50\n"+
             "#trial diag select 25\n")
              
        self.set_output("ana_homolumo",0)
        self.set_output("ana_chargeden",0)
        self.set_output("ana_frequencies",0)
        self.set_parameter("autoz",1)

    def get_editor_class(self):
        return CADPACCalcEd

    def run(self):
        '''Run the CADPAC job:
           1) Generate the input-file
           2) Launch the calculation
           3) Parse the output/punch file
           4) Extract and store the results'''
        mol_name = self.get_input("mol_name")
        mol_obj  = self.get_input("mol_obj")
        job_name = self.get_name()
        file = open(job_name+'.in','w')
        self.__WrtCADPACInput(mol_obj,file)
        file.close()
        status = self.__RunCADPAC(job_name)
        file = open(job_name+'.out','r')
        self.ReadOutput(file)
        file.close()
        self.__RdCADPACPunch(job_name+'.mdn')
        if status!=0:
           raise RuntimeError,"CADPAC calculation failed: "+str(status)

    def scan(self):
        '''Extract and Store results from a punchfile'''
        file = tkFileDialog.askopenfilename(filetypes=[("Molden File","*.mdn"),("All Files","*.*")])
        file=str(file)
        job_name = self.get_name()
        self.__RdCADPACPunch(file)
        
    def __RdCADPACPunch(self,file):
        p = MoldenReader()
        p.scan(file)
      
        if not p.title:
           p.title = self.get_title()
        if p.title == "untitled":
           p.title = self.get_input("mol_name")
        mol2 = None

        for o in p.objects:
            # take the last field of the class specification
            t1 = string.split(str(o.__class__),'.')
            myclass = t1[len(t1)-1]
            if myclass == 'VibFreq' :
               label="v=%10.3f" %(o.freq)
               self.set_output(label,o)
               mol = p.coordinates
               if (mol):
                  if (not mol2):
                     mol2 = copy.deepcopy(mol)
               else:
                  print 'cant visualise normal coords without structure'
                  raise RuntimeError

               cmd.load_model(mol2,label)
               nf = 20
               scale = 0.3
               inc = acos(0.0)*2.0/float(nf)
               for t in range(nf):
                   fac = scale * sin(float(t) * inc)
                   for i in range(len(mol2.atom)):
                       for j in range(3):
                           mol2.atom[i].coord[j] = mol.atom[i].coord[j] + \
                                                   o.atoms[i].coord[j]*fac
                   cmd.load_model(mol2,label)
            elif myclass == 'Indexed':
                mol_inp = self.get_input("mol_name")
                if self.has_output("mol_name"):
                   mol_outp= self.get_output("mol_name")
                else:
                   mol_outp = mol_inp
                if mol_inp == mol_outp:
                   t = cmd.get_names("objects")
                   count = 0
                   name = None
                   for tt in t:
                       type = cmd.get_type(tt)
                       if type == 'object:molecule':
                          count = count + 1
                          if name == None:
                             name=tt
                             cmd.lock()
                             ftype = cmd.loadable.model
                             state = 1
                             finish = 1
                             discrete = 0
                             object = o
                             o.list()
                             r = cmd.load_object(ftype,object,name,state,finish,discrete)
                             cmd.unlock()
                else:
                   o.list()
                   cmd.load_model(o,mol_outp)
                   cmd.enable(mol_outp)
                self.set_output("mol_name",mol_outp)
                self.set_output("mol_obj",cmd.get_model(mol_outp))
            elif myclass == 'Brick':
                cmd.load_brick(o,o.title)
                # cmd.enable(o.title)
                cmd.color("red",o.title)
                print 'title ' + o.title
                if o.title == 'HOMO' or o.title == 'LUMO':
                   lvl = 0.-0.05
                   name = o.title+"0_05"
                   cmd.do("isomesh %s = %s,%0.3f" %(name,o.title,lvl))
                   cmd.color("red","%s" %(name))
                   name = o.title+"_0_05"
                   cmd.do("isomesh %s = %s,%0.3f" %(name,o.title,-lvl))
                   cmd.color("blue","%s" %(name))
                else:
                   lvl = 0.03
                   name = o.title+"0_03"
                   cmd.do("isomesh %s = %s,%0.3f" %(name,o.title,lvl))
                   cmd.color("green","%s" %(name))
            else:
               print 'cant yet visualise', myclass
               raise RuntimeError


    def __RunCADPAC(self,jobname):
        f = os.popen('cadpac < '+jobname+'.in > '+jobname+'.out','w')
        status = f.close()
        if status == None:
           status = 0
        f = os.popen('cad2mol '+jobname+'.out','w')
        stat = f.close()
        if status == 0 and stat != None:
           status = stat
        return status

    def __WrtCADPACInput(self,mol,file):
        scf_rks = [ "LDA" , "LDAX"   , "BLYP"   , "BP86" , "BP91",
                    "HCTH", "HCTH147", "HCTH407", "PBE"  , "BPE0", 
                    "B97" , "B97-1"  , "B3LYP"  , "B3P86", "B3P91"]
        scf_uks = ["ULDA" ,"ULDAX"   ,"UBLYP"   ,"UBP86" ,"UBP91",
                   "UHCTH","UHCTH147","UHCTH407","UPBE"  ,"UBPE0", 
                   "UB97" ,"UB97-1"  ,"UB3LYP"  ,"UB3P86","UB3P91"]
        #file.write(self.get_parameter("predirectives"))
        self.__WrtTitle(file)
        file.write('SYMMETRY\nC1\nEND\n')
        file.write('BASIS ' + self.get_input("basis")+'\n')
        self.__WrtGeometry(mol,file)
        self.__WrtState(file)
        #file.write(self.get_parameter("classidirectives"))
        theory  = self.get_theory()
        task    = self.get_task()
        #classii = self.get_parameter("classiidirectives")
        #i = string.count(classii,"runtype")+string.count(classii,"scftype")
        if task == 'saddle':
           file.write('OPTIMISE SADDLE\nFCM\n')
        else:
           file.write(string.upper(task)+'\n')
        if scf_rks.count(theory) > 0:
           if self.get_input("spin") > 1:
              file.write('ROHF\n')
           else:
              pass
              #file.write('RHF\n')
           file.write('KOHNSHAM '+theory+'\n')
        elif scf_uks.count(theory) > 0:
           file.write('UHF\nKOHNSHAM '+theory[1:]+'\n')
        else:
           if theory != 'RHF':
              file.write(theory+'\n')
        file.write('START\nFINISH\n')

    def __WrtTitle(self,file):
        file.write('TITLE\n'+self.get_title()+'\n')

    def __WrtState(self,file):
        file.write('MULTIPLICITY '+str(self.get_input("spin"))+'\n')
        file.write('CHARGE '+str(self.get_input("charge"))+'\n')

    def __WrtGeometry(self,mol,file):
        file.write('ATOMS\n')
        for a in mol.atom:
            t = string.lower(a.symbol)[:2]
            print t
            if t[1:2] == string.upper(t[1:2]):
                t = t[:1]
            print t
            file.write(a.symbol + ' ' +
                    str(a.get_number()) + ' ' +
                    str(a.coord[0]) + ' ' +
                    str(a.coord[1]) + ' ' +
                    str(a.coord[2]) + '\n')
        file.write('END\n')

homolumoa = 0

class CADPACCalcEd(QMCalcEd):

    def __init__(self,calc,**kw):
        apply(QMCalcEd.__init__, (self,calc), kw)
        self.tasks = ["energy", "optimise", "saddle"]
        self.theories["energy"] = [
             "RHF",  "ROHF",    "UHF",     "MP2", 
             "LDA" , "LDAX"   , "BLYP"   , "BP86" , "BP91",
             "HCTH", "HCTH147", "HCTH407", "PBE"  , "BPE0",
             "B97" , "B97-1"  , "B3LYP"  , "B3P86", "B3P91",
             "ULDA" ,"ULDAX"   ,"UBLYP"   ,"UBP86" ,"UBP91",
             "UHCTH","UHCTH147","UHCTH407","UPBE"  ,"UBPE0",
             "UB97" ,"UB97-1"  ,"UB3LYP"  ,"UB3P86","UB3P91"]
        self.theories["optimise"] = [
             "RHF",  "ROHF",    "UHF",     "MP2", 
             "LDA" , "LDAX"   , "BLYP"   , "BP86" , "BP91",
             "HCTH", "HCTH147", "HCTH407", "PBE"  , "BPE0",
             "B97" , "B97-1"  , "B3LYP"  , "B3P86", "B3P91",
             "ULDA" ,"ULDAX"   ,"UBLYP"   ,"UBP86" ,"UBP91",
             "UHCTH","UHCTH147","UHCTH407","UPBE"  ,"UBPE0",
             "UB97" ,"UB97-1"  ,"UB3LYP"  ,"UB3P86","UB3P91"]
        self.theories["saddle"] = [
             "RHF", "MP2"]
        self.basissets = [
             "STO3G", "321G", "631G", "6311G", "321G*", "631G*", "6311G*",
             "321G**", "631G**", "6311G**", "DZ", "DZP", "TZ", "TZ2P",
             "631G2DP", "631GE", "SADLEJ", "PVDZ", "PVTZ"]
        self.AddPage("SCFPage","SCF")
        #self.AddPage("DirectivesPage","Directives")
        self.homolumo    = Tkinter.BooleanVar()
        self.chargeden   = Tkinter.BooleanVar()
        self.frequencies = Tkinter.BooleanVar()

    def LaunchCalcEd(self,calc):
        '''Create a new calculation editor.'''
        a = GAMESSUKCalcEd(calc)
        a.Show()

    def TaskPage(self,page,action):
        QMCalcEd.TaskPage(self,page,action)
        
        # Create a group for the checkboxes

        if action == Create:
           page.group = Pmw.Group(page,tag_text="Analysis options")
           page.group.pack(expand='yes',fill='x')

        # Sort out HOMO/LUMO

        if action == Create:
           page.homolumo = Tkinter.Checkbutton(page.group.interior())
           page.homolumo.config(text="HOMO / LUMO",variable=self.homolumo)
           page.homolumo.pack(expand='yes',anchor='w',padx=10)
        elif action == Lower:
           self.calc.set_output("ana_homolumo",self.homolumo.get())
        self.homolumo.set(self.calc.get_output("ana_homolumo"))

        # Sort out CHARGE DENSITY

        if action == Create:
           page.chargeden = Tkinter.Checkbutton(page.group.interior())
           page.chargeden.config(text="Charge Density",variable=self.chargeden)
           page.chargeden.pack(expand='yes',anchor='w',padx=10)
        elif action == Lower:
           self.calc.set_output("ana_chargeden",self.chargeden.get())
        self.chargeden.set(self.calc.get_output("ana_chargeden"))

        # Sort out FREQUENCIES

        if action == Create:
           page.frequencies = Tkinter.Checkbutton(page.group.interior())
           page.frequencies.config(text="Frequencies",variable=self.frequencies)
           page.frequencies.pack(expand='yes',anchor='w',padx=10)
        elif action == Lower:
           self.calc.set_output("ana_frequencies",self.frequencies.get())
        self.frequencies.set(self.calc.get_output("ana_frequencies"))


    def SCFPage(self,page,action):
        '''Maintain the SCF page.'''
        labels = []

        # Sort out MAXCYC

        if action == Create:
           page.maxcyc = Pmw.EntryField(page,
                        labelpos = 'w', label_text = "Max. Cycles",
                        validate = {'validator' : 'integer', 'min' : 1 },
                        value = self.calc.get_parameter("scf_maxcyc"))
           page.maxcyc.pack(expand = 1, fill = 'x')
           labels = labels + [page.maxcyc]
        elif action == Lower:
           self.calc.set_parameter("scf_maxcyc",page.maxcyc.get())
        else:  # action == Raise
           page.maxcyc.setentry(self.calc.get_parameter("scf_maxcyc"))

        # Sort out THRESHOLD

        if action == Create:
           page.thresh = Pmw.EntryField(page,
                        labelpos = 'w', label_text = "Threshold",
                        validate = {'validator' : 'integer', 'min' : 3, 
                                    'max' : 15 },
                        value = self.calc.get_parameter("scf_threshold"))
           page.thresh.pack(expand = 1, fill = 'x')
           labels = labels + [page.thresh]
        elif action == Lower:
           self.calc.set_parameter("scf_threshold",page.thresh.get())
        else:  # action == Raise
           page.thresh.setentry(self.calc.get_parameter("scf_threshold"))

        # Sort out LEVEL

        if action == Create:
           page.level1 = Pmw.EntryField(page,
                        labelpos = 'w', label_text = "Initial level-shift",
                        validate = {'validator' : 'real' , 'min' : 0.0 },
                        value = self.calc.get_parameter("scf_level_init"))
           page.levelit = Pmw.EntryField(page,
                        labelpos = 'w', label_text = "Initial #iterations",
                        validate = {'validator' : 'integer' , 'min' : 0 },
                        value = self.calc.get_parameter("scf_level_it"))
           page.level2 = Pmw.EntryField(page,
                        labelpos = 'w', label_text = "Final level-shift",
                        validate = {'validator' : 'real' , 'min' : 0.0 },
                        value = self.calc.get_parameter("scf_level_final"))
           page.level1.pack(expand='yes',fill='x')
           page.levelit.pack(expand='yes',fill='x')
           page.level2.pack(expand='yes',fill='x')
           labels = labels + [page.level1,page.levelit,page.level2]
        elif action == Lower:
           self.calc.set_parameter("scf_level_init" ,page.level1.get())
           self.calc.set_parameter("scf_level_it"   ,page.levelit.get())
           self.calc.set_parameter("scf_level_final",page.level2.get())
        else:
           page.level1.setentry(self.calc.get_parameter("scf_level_init"))
           page.levelit.setentry(self.calc.get_parameter("scf_level_it"))
           page.level2.setentry(self.calc.get_parameter("scf_level_final"))

        # Sort out the alignment of the labels

        if action == Create:
           Pmw.alignlabels(labels)

    def DirectivesPage(self,page,action):
        '''Entry for various directives not covered by GUI yet:
           1) Predirectives '''

        if action == Create:
           page.panes = Pmw.PanedWidget(page)
           page.panes.add('predir',min=75)
           page.panes.add('classi',min=75)
           page.panes.add('classii',min=75)
           page.panes.add('classiii',min=75)
           page.panes.pack(expand=1,fill='both')

        # Sort out PREDIRECTIVES

        if action == Create:
           page.predir = Pmw.ScrolledText(page.panes.pane('predir'),
                        labelpos = 'nw', label_text = 'Pre-directives',
                        borderframe = 1)
           page.predir.settext(self.calc.get_parameter("predirectives"))
           page.predir.pack()
        elif action == Lower:
           self.calc.set_parameter("predirectives",page.predir.get())
        else: 
           page.predir.settext(self.calc.get_parameter("predirectives"))

        # Sort out CLASS 1 DIRECTIVES

        if action == Create:
           page.classi = Pmw.ScrolledText(page.panes.pane('classi'),
                        labelpos = 'nw', label_text = 'Class I directives',
                        borderframe = 1)
           page.classi.settext(self.calc.get_parameter("classidirectives"))
           page.classi.pack()
        elif action == Lower:
           self.calc.set_parameter("classidirectives",page.classi.get())
        else: 
           page.classi.settext(self.calc.get_parameter("classidirectives"))

        # Sort out CLASS 2 DIRECTIVES

        if action == Create:
           page.classii = Pmw.ScrolledText(page.panes.pane('classii'),
                        labelpos = 'nw', label_text = 'Class II directives',
                        borderframe = 1)
           page.classii.settext(self.calc.get_parameter("classiidirectives"))
           page.classii.pack()
        elif action == Lower:
           self.calc.set_parameter("classiidirectives",page.classii.get())
        else: 
           page.classii.settext(self.calc.get_parameter("classiidirectives"))

        # Sort out CLASS 3 DIRECTIVES

        if action == Create:
           page.classiii = Pmw.ScrolledText(page.panes.pane('classiii'),
                        labelpos = 'nw', label_text = 'Class III directives',
                        borderframe = 1)
           page.classiii.settext(self.calc.get_parameter("classiiidirectives"))
           page.classiii.pack()
        elif action == Lower:
           self.calc.set_parameter("classiiidirectives",page.classiii.get())
        else: 
           page.classiii.settext(self.calc.get_parameter("classiiidirectives"))
