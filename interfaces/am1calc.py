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
"""Implements the interface to the AM1 code from Linkoping
"""

import os
import string
import sys

import Tkinter
import Pmw
import tkFileDialog
import viewer.help
from objects import zmatrix

from qm import *

from objects import am1

MENU_ENER  = "Energy"
MENU_GRAD  = "Gradient"
MENU_OPT   = "Geometry Optimisation"

class AM1Calc(QMCalc):
    """Calculation object for the AM1 calculation
       

    """
#    def __init__(self, **kw):
    def __init__(self, initialMolecule=None, options=None, **kw):

        if not initialMolecule:
            print "AM1Calc needs a molecule!"
            return None
        else:
            self.initialMolecule = initialMolecule

        apply(QMCalc.__init__,(self,),kw)

        self.debug = 1

        self.molecules = []
        self.generator = None
        self.optstep = 0 # to count optimisation steps
        
        self.set_defaults( initialMolecule )
            
        # dictionary of options for the calculation
        if options:
            self.set_options( options )
            

    def set_defaults( self, molecule ):
        """ Set up the default values for the calculation """
        
        self.set_program('AM1')
        self.set_title( molecule.title )
        self.set_parameter('task',MENU_OPT)
        self.set_parameter('frozen_density', 1)
        self.set_parameter('fixed', -1)
        self.set_parameter('opt_method','Newton')

    def check_avail_parameters(self):
        """Check if we have parameters for all the atoms."""

        failed = []
        for atom in self.initialMolecule.atom:
            if not atom.symbol in am1.AM1atoms:
                print "symbol %s not in list" % atom.symbol
                failed.append(atom.symbol)
                
        if len(failed) >= 1:
            return failed
        else:
            return None


    def get_generator( self ):
        """Return a generator object that can be used to cycle through the
           geometry optimisation steps and return geometries.
        """

        Am1Mol = am1.Molecule()
        
        # Create the molecule
        for atom in self.initialMolecule.atom:
            Am1Mol.add( atom.name, atom.symbol,atom.coord[0], atom.coord[1], atom.coord[2] )
        if self.get_parameter( 'opt_method' ) == 'Newton':
            print "Running Newton calculation"
            self.generator = Am1Mol.newton( self.get_parameter('fixed'),
                                       self.get_parameter('frozen_density') )
        else:
            print "No calculation"

        return None


    def get_opt_step( self ):
        """Return a molecule and it's energy from an optimisation step"""

        if not self.generator:
            self.get_generator()

        try:
            atoms, energy = self.generator.next()
        except StopIteration:
            # Optimisation has completed
            return None, None
            
        self.optstep += 1

        Am1Mol = zmatrix.Zmatrix()
        for new in atoms:
            atom = zmatrix.ZAtom()
            atom.name = new.name
            atom.symbol = new.symbol
            atom.coord = [ new.x, new.y, new.z ]
            Am1Mol.atom.append( atom )

        if len(self.molecules) == 0:
            newmol = copy.deepcopy( self.initialMolecule )
        else:
            newmol = copy.deepcopy( self.molecules[-1] )
            
        newmol.name = '%s_%d' % ( newmol.title, self.optstep )
        newmol.import_geometry( Am1Mol )
        
        self.molecules.append( newmol )

        print "get_opt_step returning:"
        print energy
        print newmol
        
        return newmol,energy

if __name__ == "__main__":

    try:
        myfile = sys.argv[1]
        mol = zmatrix.Zmatrix()
        mol.load_from_file( myfile )
    except Exception,e:
        print "I need a file with coordinates/a zmatrix in it!"
        print e
        sys.exit(1)

    calc = AM1Calc( initialMolecule=mol )

    for i in range(2):
        print "Iteration %d" % i
        newmol, energy = calc.get_opt_step()
        print 'gen.next got'
        print 'newmol'
        print newmol
        print 'energy'
        print energy
