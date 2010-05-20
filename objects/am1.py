# By Patrik Jakobsson and Ulf Ekstrom 2005-2007.
from __future__ import generators
import os,sys
if __name__ == "__main__":
    # Need to add the gui directory to the python path so 
    # that all the modules can be imported
    gui_path = os.path.split(os.path.dirname( os.path.realpath( __file__ ) ))[0]
    sys.path.append(gui_path)

# Import python modules
import math
import unittest

# Import our modules
import objects.numeric
import objects.linalg

# Evaluation variables
get_E_calls = 0

# Global variables
debug = 0               # For debugging. Displays debugging info
Au2Angstrom = 0.529167  # Conversion factors between atomic and metric units
Hartree2eV = 27.211396
int_res = 1e-14

# Global parameters
derivative_step = 0.001         # Step size (h) when calculating derivatives
linesearch_initial_step = 0.1  # Step size used at the beginning of a line-search
goldenratio_precision = 0.001 # Precision of the golden ratio optimization

# Effective nuclear charge 
Z = {'H':1, 'C':4,'N':5,'O':6, 'F':7}
number_of_orbitals = {'H':1, 'C':4, 'N':4, 'O':4, 'F':4}

# List which atoms we have parameters for - please add to this
# list when you add new atoms
AM1atoms = [ 'H','C','N','O','F']

# AM1 parameters
Us =    {'H':-11.396427, 'C':-52.028658, 'N':-71.86,     'O':-97.83,     'F':-136.105579}
Up =    {                'C':-39.614239, 'N':-57.167581, 'O':-78.26238,  'F':-104.889995}
zetas = {'H':1.188078,   'C':1.808665,   'N':2.315410,   'O':3.108032,   'F':3.770082}
zetap = {                'C':1.685116,   'N':2.157940,   'O':2.524039,   'F':2.49467}
betas = {'H':-6.173787,  'C':-15.715783, 'N':-20.299110, 'O':-29.272773, 'F':-69.590277}
betap = {                'C':-7.719283,  'N':-18.238666, 'O':-29.272773, 'F':-27.92236}
alpha = {'H':2.882324,   'C':2.648274,   'N':2.947286,   'O':4.455371,   'F':5.5178}

K1 = {'H': 0.122796,  'C': 0.011355,  'N': 0.025251,  'O':0.280962, 'F':0.242079}
K2 = {'H': 0.005090,  'C': 0.045924,  'N': 0.028953,  'O':0.081430, 'F':0.003607}
K3 = {'H': -0.018336, 'C': -0.020061, 'N': -0.005806, 'O':0.0,      'F':0.0}
K4 = {'H': 0.0,       'C': -0.001260, 'N': 0.0,       'O':0.0,      'F':0.0}
L1 = {'H': 5.0,       'C': 5.0,       'N': 5.0,       'O':5.0,      'F':4.8}
L2 = {'H': 5.0,       'C': 5.0,       'N': 5.0,       'O':7.0,      'F':4.6}
L3 = {'H': 2.0,       'C': 5.0,       'N': 2.0,       'O':0.0,      'F':0.0}
L4 = {'H': 0.0,       'C': 5.0,       'N': 0.0,       'O':0.0,      'F':0.0}
M1 = {'H': 1.2,       'C': 1.6,       'N': 1.5,       'O':0.847918, 'F':0.93}
M2 = {'H': 1.8,       'C': 1.85,      'N': 2.1,       'O':1.445071, 'F':1.66}
M3 = {'H': 2.1,       'C': 2.05,      'N': 2.4,       'O':0.0,      'F':0.0}
M4 = {'H': 0.0,       'C': 2.65,      'N': 0.0,       'O':0.0,      'F':0.0}

gss =  {'H':12.848, 'C':12.23, 'N':13.59, 'O':15.42, 'F':16.92}
gsp =  {            'C':11.47, 'N':12.66, 'O':14.48, 'F':17.25} # swapped carbon sp, pp
gpp =  {            'C':11.08, 'N':12.98, 'O':14.52, 'F':16.71}
gppp = {            'C':9.84,  'N':11.59, 'O':12.98, 'F':14.91}
hss =  {'H':12.848, 'C':12.23, 'N':13.59, 'O':15.42, 'F':16.92}
hpp =  {            'C':11.08, 'N':12.98, 'O':14.52, 'F':16.71} # fixed carbon
hsp =  {            'C':2.43,  'N':3.14,  'O':3.94,  'F':4.83}
hppp = {            'C':0.62,  'N':0.70,  'O':0.77,  'F':0.84}#!!!guessing!!!

# parameters from mopac/block.f
# DD, QQ, AM,AD,AQ
# DD and QQ:
multipole_separation =  { 'C':[0.8236736, 0.7268015],
                          'N':[0.6433247, 0.5675528],
                          'O':[0.4988896, 0.4852322],
                          'F':[0.4145203, 0.4909446] }
# AM AD AQ:
AMDQ = {'H':[0.4721793],
        'C':[0.4494671, 0.6082946, 0.6423492],
        'N':[0.4994487, 0.7820840, 0.7883498],
        'O':[0.5667034, 0.9961066, 0.9065223],
        'F':[0.6218302, 1.2088792, 0.9449355]}

# Tabulated multipole distributions for each orbital pair of each
# atom.  multipoles['O'] gives a list of charges multipole
# distributions [ [(0,0), [[x,y,z,rho,q]..]] .. ] with the origin at
# 0, for oxygen. The units here is au!!
multipoles = {} 

def atom_multipoles(atomsymbol):
  P = []
  rhom = 0.5/AMDQ[atomsymbol][0]
  P.append([(0,0),[[0.0,0.0,0.0,rhom,1.0]]])
  if atomsymbol == 'H':
    return P
  D1 = multipole_separation[atomsymbol][0]
  rhod = 0.5/AMDQ[atomsymbol][1]
  # sp
  for i in range(1,4):
    q1 = [0,0,0,rhod,0.5]
    q1[i-1] += D1
    q2 = [0,0,0,rhod,-0.5]
    q2[i-1] -= D1
    P.append([(0,i),[q1,q2]])
  # pipi
  D2 = multipole_separation[atomsymbol][1]
  rhoq = 0.5/AMDQ[atomsymbol][2]
  for i in range(1,4):
    q1 = [0,0,0,rhoq,-0.5]
    q2 = [0,0,0,rhoq,0.25]
    q2[i-1] += 2*D2
    q3 = [0,0,0,rhoq,0.25]
    q3[i-1] -= 2*D2
    q4 = [0,0,0,rhom,1.0]
    P.append([(i,i),[q1,q2,q3,q4]])
  # pipj
  for i in range(1,4):
    for j in range(i+1,4):
      if (i,j) != (1,2): # don't add xy, use that xy = 1/2*[(x'+y')*(x'-y')] in the integral code
        q1 = [0,0,0,rhoq,0.25]
        q1[i-1] += D2
        q1[j-1] += D2
        q2 = [0,0,0,rhoq,0.25]
        q2[i-1] -= D2
        q2[j-1] -= D2
        q3 = [0,0,0,rhoq,-0.25]
        q3[i-1]  = D2
        q3[j-1] -= D2
        q4 = [0,0,0,rhoq,-0.25]
        q4[i-1] -= D2
        q4[j-1]  = D2
        P.append([(i,j),[q1,q2,q3,q4]])
  return P

# float = vdist(a,b)
# returns distance between atoms a and b
def vdist(a,b):
  return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2 + (a.z - b.z)**2)

# Cross product of vectors a and b
def cross(a,b):
  return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])

# Scalar product of vectors a and b
def dot(a,b):
  return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

# Prints matrix a
def printmat(a,d=3):
  print array2string(a,precision=d)

# Returns a string with the orbital type ('s' or 'p')
def orbital_type(n):
  if(n == 0):
    return 's'
  else:
    return 'p'

##
# Atom class
# Properties:
#  symbol       - symbol of the atom ('H','O','N',etc.)
#  x/y/z      - cartesian coordinates of the atom
#  orbitals[] - a list of the IDs of the child orbitals of the atom
##
class Atom:
  def __init__(self, name='', symbol='', x = 0.0, y = 0.0, z = 0.0, n = 0):
    self.name = name
    self.symbol = symbol
    self.x = float(x)
    self.y = float(y)
    self.z = float(z)
    self.orbitals = []
    for i in range(number_of_orbitals[symbol]):
      self.orbitals.append(n + i)

##
# Orbital class
# Properties:
#  atom  - ID of the parent atom
#  ot    - orbital type, 0=s / 1=px / 2=py / 3=pz
#  U     - kinetic energy
#  alpha - AM1 parameter
#  beta  - AM1 parameter
#  zeta  - AM1 parameter
##
class Orbital:

  def __init__(self, atom=0, ot=0, x = 0.0, y = 0.0, z = 0.0, U = 0.0, beta = 0.0, alpha = 0.0, zeta = 0.0):		
    self.atom = atom
    self.ot = ot
    self.U = U
    self.alpha = alpha
    self.beta = beta
    self.zeta = zeta

##
# Molecule class
# Properties:
#  atoms[] - a list of the IDs of the atoms in the molecule
#  orbitals[] - a list of the IDs of the orbitals in the molecule
#  tc_te{} - a list of the two-center two-electron integrals needed
#  Eeval - Countes number of calls to get_E(), i.e. the number of energy calculations
# Member functions:
#  add() - adds an atom to the molecule. The belonging orbitals are created automaticly
##
class Molecule:
  def __init__(self, symbol = ''):
    self.atoms = []
    self.orbitals = []
    self.tc_te = {}
    self.Eeval = 0 # Debug: counts number of energy calculations
  def add(self, name='',symbol = '', x = 0.0, y = 0.0, z = 0.0):
    self.atoms.append(Atom( name, symbol, x, y, z, len(self.orbitals)))
    for i in range(number_of_orbitals[symbol]):
      b = 0.0
      U = 0.0
      zeta = 0.0
      if(i==0):
        b = betas[symbol]
        U = Us[symbol]
        zeta = zetas[symbol]
      else:
        b = betap[symbol]
        U = Up[symbol]
        zeta = zetap[symbol]			
      self.orbitals.append(Orbital(len(self.atoms)-1, i, x, y, z, U, b, alpha[symbol],zeta))
    if not multipoles.has_key(symbol):
      multipoles[symbol] = atom_multipoles(symbol)
  def number_of_electrons(self):
    n = 0
    for i in range(len(self.atoms)):
      n = n + Z[self.atoms[i].symbol]
    return n	

    ##
    # Calculates the overlap (S) matrix. WORKS!
    ##	
  def get_S(self,part=-1):
    def overlap_quantum(nA,lA,zA,nB,lB,zB,tA,R):
      z = 0.5*(zA+zB)
      t = (zA-zB)/(zA+zB)
      p = 0.5*(zA+zB)*R
      if(zB == zA):
        # 1s|1s
        if((nA == 1) and (nB == 1)):
          return (1+p+1.0/3*p**2)*math.exp(-p)
        # 2s|2s
        if((nA == 2) and (lA == 0) and (nB == 2) and (lB == 0)):
          return (1+p+4.0/9*p**2+1.0/9*p**3+1.0/45*p**4)*math.exp(-p)
        # 2s|pz
        if((nA == 2) and (lA == 0) and (nB == 2) and (lB == 1) and (tA == 0)):
          return 1.0/(2*math.sqrt(3))*p*(1+p+7.0/15*p**2+2.0/15*p**3)*math.exp(-p)
        # pz|pz
        if((nA == 2) and (lA == 1) and (nB == 2) and (lB == 1) and (tA == 0)):
          return -(-1-p-1.0/5*p**2+2.0/15*p**3+1.0/15*p**4)*math.exp(-p)
        # px|px // py|py
        if((nA == 2) and (lA == 1) and (nB == 2) and (lB == 1) and (tA == 1)):
          return (1+p+2.0/5*p**2+1.0/15*p**3)*math.exp(-p)
      k = 0.5*(t+1.0/t)
      pa = (1+t)*p
      pb = (1-t)*p
      # 1s|2s
      if nA == 1 and lA == 0 and nB == 2 and lB == 0:
        #jmht return ((math.sqrt(1-t**2)/(sqrt(3)*t*p))
        return ((math.sqrt(1-t**2)/(math.sqrt(3)*t*p))
          *(-(1-k)*(2*(1+k)*(2-3*k)+(1-2*k)*pa)
          *math.exp(-pa)+(1+k)*(2*(1-k)*(2-3*k)+4*(1-k)*pb+pb**2)
          *math.exp(-pb)))
      # 1s|2pz
      elif nA == 1 and lA == 0 and nB == 2 and lB == 1 and tA == 0:
        return (math.sqrt((1+t)/(1-t))/(t*p**2)
          *(-(1-k)**2*(6*(1+k)*(1+pa)+2*pa**2)
          *math.exp(-pa)+(1+k)
          *(6*(1-k)**2*(1+pb)+4*(1-k)*pb**2+pb**3)*math.exp(-pb)))
      # 2s|2pz
      elif nA == 2 and lA == 0 and nB == 2 and lB == 1 and tA == 0:
        return (math.sqrt((1+t)/(1-t))*1.0/(math.sqrt(3)*t*p**2)
          *(-(1-k)**2*(6*(1+k)*(3+4*k)*(1+pa)+2*(5+6*k)*pa**2+2*pa**3)*math.exp(-pa)
          +(1+k)*(6*(1-k)**2*(3+4*k)*(1+pb)+4*(1-k)*(2+3*k)*pb**2+(1+2*k)*pb**3)
          *math.exp(-pb)))			
      # 2pz|2pz
      elif nA == 2 and lA == 1 and nB == 2 and lB == 1 and tA == 0:
        return -((1.0/(math.sqrt(1-t**2)*t*p**3)) # negative sign added - ulfek
          *(-(1-k)**2*(48*(1+k)**2*(1+pa+0.5*pa**2)
          +2*(5+6*k)*pa**3+2*pa**4)*math.exp(-pa)
          +(1+k)**2*(48*(1-k)**2*(1+pb+0.5*pb**2)
          +2*(5-6*k)*pb**3+2*pb**4)*math.exp(-pb)))
      # 2px|2px
      elif nA == 2 and lA == 1 and nB == 2 and lB == 1 and tA == 1:
        return ((1.0/(math.sqrt(1-t**2)*t*p**3))
          *(-(1-k)**2*(24*(1+k)**2*(1+pa)+12*(1+k)*pa**2+2*pa**3)*math.exp(-pa)
          +(1+k)**2*(24*(1-k)**2*(1+pb)+12*(1-k)*pb**2+2*pb**3)*math.exp(-pb)))
      # 2s|2s
      elif nA == 2 and lA == 0 and nB == 2 and lB == 0 and tA == 0:
        return ((math.sqrt(1-t**2)/(3.0*t*p))
          *(-(1-k)*(2*(1+k)*(7-12*k**2)+4*(1+k)*(2-3*k)*pa+(1-2*k)*pa**2)
          *math.exp(-pa)+(1+k)
          *(2*(1-k)*(7-12*k**2)+4*(1-k)*(2+3*k)*pb+(1+2*k)*pb**2)
          *math.exp(-pb)))
      else:
        raise Exception
    def overlap_prime(nA,lA,tA,zA,nB,lB,tB,zB,R):
      if((tA == 's') or (tA == 'pz')):
        tA = 0
      else:
        tA = 1
      if((tB == 's') or (tB == 'pz')):
        tB = 0
      else:
        tB = 1
      if(tB == tA):
        if(nA>nB):
          return overlap_quantum(nB,lB,zB,nA,lA,zA,tA,R/Au2Angstrom)
        else:
          return overlap_quantum(nA,lA,zA,nB,lB,zB,tA,R/Au2Angstrom)
      else:
        return 0.0
      ##
      # Calculates the overlap of orbitals a and b
      ##
    def overlap(a,b):
      ##
      # orbital_type returns the type of orbital associated with integer n.
      #  0 is s; 1,2,3 is px,py,pz respectively
      ##
      def orbital_type_detail(n):
        if(n==0):
          return 's'
        elif(n==1):
          return 'px'
        elif(n==2):
          return 'py'
        elif(n==3):
          return 'pz'
        
      # First, take care of the elementary case of the two
      #  orbitals residing on the same atom
      if(self.orbitals[a].atom == self.orbitals[b].atom):
        if(a == b):
          return 1.0
        else:
          return 0.0
      # For convenience, make sure l(A)<=l(B)
      if(self.orbitals[a].ot > self.orbitals[b].ot):
        # If so, swap them
        tmp = b
        b = a
        a = tmp
      # Get some molecular properties
      # We need the zeta value (exponential) for the orbitals
      zA = self.orbitals[a].zeta
      zB = self.orbitals[b].zeta
      # quantum number n
      if (self.atoms[self.orbitals[a].atom].symbol == 'H'):
        nA = 1
      else:
        nA = 2
      if (self.atoms[self.orbitals[b].atom].symbol == 'H'):
        nB = 1
      else:
        nB = 2
      # orbital type (x,px,py,px)
      otA = orbital_type_detail(self.orbitals[a].ot)
      otB = orbital_type_detail(self.orbitals[b].ot)
      # separation distance R
      posA = (self.atoms[self.orbitals[a].atom].x,self.atoms[self.orbitals[a].atom].y,self.atoms[self.orbitals[a].atom].z)
      posB = (self.atoms[self.orbitals[b].atom].x,self.atoms[self.orbitals[b].atom].y,self.atoms[self.orbitals[b].atom].z)
      Rvec = (posA[0]-posB[0],posA[1]-posB[1],posA[2]-posB[2])
      R = math.sqrt(Rvec[0]**2+Rvec[1]**2+Rvec[2]**2)
      # If two 's' orbitals, calculate them directly
      if(otA == 's'):
        orbA = ('s',nA,zA)
      if(otB == 's'):
        orbB = ('s',nB,zB)
      if((otA == otB) and (otA == 's')):
        I = overlap_prime(nA,0,'s',zA,nB,0,'s',zB,R)
        return I
      # If one 's' and one 'p' orbital, it's also simple (if so, orbital A is the 's' orbital
      if(otA == 's'):
        normR = (1.0/R*Rvec[0],1.0/R*Rvec[1],1.0/R*Rvec[2])
        if(otB == 'px'):
          I = normR[0]*overlap_prime(nA,0,'s',zA,nB,1,'pz',zB,R)
        elif(otB == 'py'):
          I = normR[1]*overlap_prime(nA,0,'s',zA,nB,1,'pz',zB,R)
        elif(otB == 'pz'):
          I = normR[2]*overlap_prime(nA,0,'s',zA,nB,1,'pz',zB,R)
        return I
      # The case of two p-orbitals are a little more complicated.
      # First, move the two atoms so:
      #  r(A) = (0,0,0)
      #  r(B) = (0,0,R)
      # Also, rotate coordinate systems to align
      #  pz with the vector R
      # This is necessary in order to evaluate the integral
      # Old basis vectors
      e1 = (1.0,0.0,0.0)
      e2 = (0.0,1.0,0.0)
      e3 = (0.0,0.0,1.0)
      # Calculate the new basis vectors, f1, f2 and f3
      # f3 will simply be in the R direction
      f3 = (1.0/R*Rvec[0],1.0/R*Rvec[1],1.0/R*Rvec[2])
      # f1 will be the cross product (f3 x e3)
      if(abs(f3[0]*e3[0]+f3[1]*e3[1]+f3[2]*e3[2]) < 0.999):
        f1 = cross(f3,e3)
      else:
        f1 = cross(f3,e2)
      f1l = math.sqrt(f1[0]**2+f1[1]**2+f1[2]**2)
      f1 = (1/f1l*f1[0],1/f1l*f1[1],1/f1l*f1[2])
      # and f2 = (f3 x f1)
      f2 = cross(f3,f1)
      if otA == 'px':
        orbA = ('px',nA,zA,f1[0],f2[0],f3[0])
      elif otA == 'py':
        orbA = ('py',nA,zA,f1[1],f2[1],f3[1])
      elif otA == 'pz':
        orbA = ('pz',nA,zA,f1[2],f2[2],f3[2])
      else:
        raise Exception
      if otB == 'px':
        orbB = ('px',nB,zB,f1[0],f2[0],f3[0])
      elif otB == 'py':
        orbB = ('py',nB,zB,f1[1],f2[1],f3[1])
      elif otB == 'pz':
        orbB = ('pz',nB,zB,f1[2],f2[2],f3[2])
      else:
        raise Exception
      xx = overlap_prime(nA,1,'px',zA,nB,1,'px',zB,R)
      I = orbA[3]*orbB[3]*xx
      I = I + orbA[4]*orbB[4]*xx # yy overlap == xx overlap
      I = I + orbA[5]*orbB[5]*overlap_prime(nA,1,'pz',zA,nB,1,'pz',zB,R)			
      return I
    n = len(self.orbitals)
    S = objects.numeric.array((((0.0,)*n,)*n))
    # Calculate overlap for atom 'part' only
    if part != -1:
      for orb in self.atoms[part].orbitals:
        for i in range(n):
          S[i][orb]=overlap(i,orb)
          S[orb][i]=S[i][orb]
      self.S = S
      return S
    # Else, calculate for all atoms
    n = len(self.orbitals)
    S = objects.numeric.array((((0.0,)*n,)*n))
    for i in range(n):
      S[i][i] = 1.0
      for j in range(n)[(i+1):]:
        S[i][j] = overlap(i,j)
        S[j][i] = S[i][j]
      self.S = S
    return S
  def tc_te_diatom(self, atom1, atom2, noscreen = 0):
    """Return a list of the two electron integrals between
    atom1 and atom2, on the form [[(i,j,k,l),int_ijkl],..].
    Only nonzero integrals are returned. The integrals
    are calculated in a diatomic frame, with z as the
    direction between atoms, and then transformed to
    global coordinates."""		
    def normalize(a):
      #jmhtl = sqrt(a[0]**2 + a[1]**2 + a[2]**2)
      l = math.sqrt(a[0]**2 + a[1]**2 + a[2]**2)
      a[0] /= l
      a[1] /= l
      a[2] /= l
    def multipole_interaction(P1,P2,Rz,printr=0):
      """Return the MNDO approximation to (i,j|k,l),
      in the diatomic frame. P1 and P2 are lists of
      point charges from the multipoles table. Rz is
      the separation in the z direction."""
      def f1(r,rhoA,rhoB):
        return 1.0/math.sqrt(r**2 + (rhoA+rhoB)**2)
      def dist(a,b,Rz):
        r = math.sqrt((b[0]-a[0])**2 + (b[1]-a[1])**2 + (b[2]-a[2]+Rz)**2)
        if printr:
          print 'r:',r
        return r
      Rz /= Au2Angstrom
      J = 0
      for q1 in P1:
        for q2 in P2:
          J += q1[4]*q2[4]*f1(dist(q1,q2,Rz),q1[3],q2[3])
      return J*Hartree2eV
    
    if atom2.symbol == 'H' and atom1.symbol != 'H':
      return self.tc_te_diatom(atom2,atom1) # make sure H comes as atom1 below
    
    # Set up a diatomic coordinate system, as much as needed
    z = [atom2.x - atom1.x, atom2.y - atom1.y, atom2.z - atom1.z]
    #jmht R = sqrt(z[0]**2 + z[1]**2 + z[2]**2)
    R = math.sqrt(z[0]**2 + z[1]**2 + z[2]**2)
  
    idx1 = atom1.orbitals[0] # index of s orbital on this atom. Assume px = idx1 + 1 etc.
    idx2 = atom2.orbitals[0]
    # Calculate the integrals in the diatomic coordinate system Jijkl
    # Calculate ALL integrals now, even those which are zero or identical
    P1 = multipoles[atom1.symbol]
    P2 = multipoles[atom2.symbol]
    # TODO: don't calculate integrals which has an odd number of x's or y's
    # TODO: don't calculate both x and y integrals when possible
    diints = []
    for p1 in P1:
      for p2 in P2:
        Jdi = multipole_interaction(p1[1],p2[1],R)
        if abs(Jdi) > 1e-14:
          diints.append([(p1[0][0],p1[0][1],p2[0][0],p2[0][1]),Jdi])
          # Add the other possible integral combinations.
          # TODO: do this in a more efficient way
          if p1[0][0] != p1[0][1]:
            diints.append([(p1[0][1],p1[0][0],p2[0][0],p2[0][1]),Jdi])
            if p2[0][0] != p2[0][1]:
              diints.append([(p1[0][1],p1[0][0],p2[0][1],p2[0][0]),Jdi])
          if p2[0][0] != p2[0][1]:
            diints.append([(p1[0][0],p1[0][1],p2[0][1],p2[0][0]),Jdi])
    if atom1.symbol == 'H' and atom2.symbol == 'H':
      return [[(idx1,idx1,idx2,idx2),diints[0][1]]]
    #Mopac uses (xy|xy) = 1/2*[(xx|xx) - (xx|yy)], so we use that as well.
    Jxyxy = 0
    for J in diints:
      if J[0] == (1,1,1,1):
        Jxyxy += J[1]
      if J[0] == (1,1,2,2):
        Jxyxy -= J[1]
    diints.append([(1,2,1,2),0.5*Jxyxy])
    diints.append([(2,1,1,2),0.5*Jxyxy])
    diints.append([(1,2,2,1),0.5*Jxyxy])
    diints.append([(2,1,2,1),0.5*Jxyxy])
    # Need (ss|sp) and (ss|pp) etc, so set up coordinate system
    z[0] /= R
    z[1] /= R
    z[2] /= R
    # Obtain any two vectors x and y orthogonal to z
    if abs(z[2]) < 0.7:
      x = [z[1],-z[0],z[2]]
    else:
      x = [z[2],z[1],-z[0]]
    c = dot(x,z)
    x[0] -= c*z[0]
    x[1] -= c*z[1]
    x[2] -= c*z[2]
    normalize(x)
    y = cross(z,x)
    # frame[i][j] is how i looks in global coordinates (j)
    frame = [[1.0, 0   , 0   , 0],
       [0 , x[0], x[1], x[2]],
       [0 , y[0], y[1], y[2]],
       [0 , z[0], z[1], z[2]]]
  
    # transform integrals to global coordinate system
    # Calculate (ij|kl), i <= j, k <=l 
    ints = []
    n1 = len(atom1.orbitals)
    n2 = len(atom2.orbitals)
    for i in range(n1):
      for j in range(i,n1):
        for k in range(n2):
          for l in range(k,n2):
            J = 0
            for Jdi in diints:
              J += (Jdi[1]
                    *frame[Jdi[0][0]][i]
                    *frame[Jdi[0][1]][j]
                    *frame[Jdi[0][2]][k]
                    *frame[Jdi[0][3]][l])
            if noscreen or abs(J) > 1e-14:
              ints.append([(idx1+i,idx1+j,idx2+k,idx2+l),J])
    return ints
  
    ##
    # two-center two-electron integrals of orbitals a, b, c, d
    ##
  def tc_te_int(self,a,b,c,d,printint=False):
    raise Exception("vad ska vara har?")

    ##
    # coulumb integrals of orbitals a and b
    ##
  def get_g_and_h(self):
    n = len(self.orbitals)
    g = objects.numeric.array((((0.0,)*n,)*n))
    h = objects.numeric.array((((0.0,)*n,)*n))
    for i in range(n):
      for j in range(n):
        ## a and b must reside on the same atom
        if(self.orbitals[i].atom == self.orbitals[j].atom):
          symbol = self.atoms[self.orbitals[i].atom].symbol
          t1 = orbital_type(self.orbitals[i].ot)
          t2 = orbital_type(self.orbitals[j].ot)
          
          ## make difference between |px,px> and |px,py>
          if((t1 == 'p') and (t2 == 'p')):
            if(self.orbitals[i].ot != self.orbitals[j].ot):
              t2 = 'pp'
          t = t1+t2
          
          if(t == 'ss'):
            g[i][j] = gss[symbol]
            h[i][j] = hss[symbol]
          elif((t == 'sp') or (t == 'ps')):
            g[i][j] = gsp[symbol]
            h[i][j] = hsp[symbol]
          elif(t == 'pp'):
            g[i][j] = gpp[symbol]
            h[i][j] = hpp[symbol]
          elif(t == 'ppp'):
            g[i][j] = gppp[symbol]
            h[i][j] = hppp[symbol]
        else:
          g[i][j] = 0.0
          h[i][j] = 0.0
    self.h = h
    self.g = g
    return g
		
    ##
    # one-center one-electron energy integral of orbitals a and b (on the same atom)
    ##
  def get_V(self):
    def f2(R):
      return 0.0
    n = len(self.orbitals)
    V = objects.numeric.array((((0.0,)*n,)*n))
    for i in range(n):
      for j in range(n):
        for B in range(len(self.atoms)):
          if(self.orbitals[i].atom != B):
            R = vdist(self.atoms[B],self.atoms[self.orbitals[i].atom])
            c = self.atoms[B].orbitals[0]
            if self.tc_te.has_key((i,j,c,c)):
              V[i][j] = V[i][j] + (-1)*Z[self.atoms[B].symbol]*self.tc_te[(i,j,c,c)] + f2(R)
    self.V = V
    return V

    ##
    # Performs Extended Huckel calculation to obtain initial guess for the fock matrix, F.
    ##		
  def EH(self):
    n = len(self.orbitals)
    F = objects.numeric.array((((0.0,)*n,)*n))
    for i in range(n):
      U = Us[self.atoms[self.orbitals[i].atom].symbol]
      if(self.orbitals[i].ot != 0):
        U = Up[self.atoms[self.orbitals[i].atom].symbol]
      F[i][i] = U
      for j in range(n)[(i+1):]:
        Ui = Us[self.atoms[self.orbitals[i].atom].symbol]
        if(self.orbitals[i].ot != 0):
          Ui = Up[self.atoms[self.orbitals[i].atom].symbol]
        Uj = Us[self.atoms[self.orbitals[j].atom].symbol]
        if(self.orbitals[j].ot != 0):
          Uj = Up[self.atoms[self.orbitals[j].atom].symbol]
          
        F[i][j] = (1.75 / 2) * (Ui+Uj)*self.S[i][j]
        F[j][i] = F[i][j]
    self.F = F
        
    return F
			

    ##
    # Calculate two-electron part of the Fock matrix, given P and overlap matrices
    ##
  def twofock(self,P):
    ##
    # orbital_type returns the type of orbital associated with integer n. 0 is s; 1,2,3 is px,py,pz respectively
    ##
    def orbital_type(n):
      if(n == 0):
        return 's'
      else:
        return 'p'
      
    def f(i,j):
      if(i==j):
        S = 0
        for n in self.atoms[self.orbitals[i].atom].orbitals:
          S += P[n][n]*(self.g[i][n] - 0.5*self.h[i][n])
        for B in range(len(self.atoms)):
          if(self.orbitals[i].atom != B):
            for l in self.atoms[B].orbitals:
              for s in self.atoms[B].orbitals:
                if self.tc_te.has_key((i,i,l,s)):
                  S += P[l][s]*self.tc_te[(i,i,l,s)]
        return S
      elif(self.orbitals[i].atom == self.orbitals[j].atom):				
        S = 0.5*P[i][j]*(3.0*self.h[i][j] - self.g[i][j])
        for B in range(len(self.atoms)):
          if(self.orbitals[i].atom != B):
            for l in self.atoms[B].orbitals:
              for s in self.atoms[B].orbitals:
                if self.tc_te.has_key((i,j,l,s)):
                  S += P[l][s]*self.tc_te[(i,j,l,s)]
        return S
      else:
        S = 0.0
        for n in self.atoms[self.orbitals[i].atom].orbitals:
          for s in self.atoms[self.orbitals[j].atom].orbitals:
            if self.tc_te.has_key((i,n,j,s)):
              S -= 0.5*P[n][s]*self.tc_te[(i,n,j,s)]
        return S
  
    # Calculate the two electron part of the fock matrix F
    n = len(self.orbitals)
    F = objects.numeric.array((((0.0,)*n,)*n))
  
    for i in range(n):
      for j in range(i,n):
        F[i][j] = f(i,j)
        F[j][i] = F[i][j]
    self.F=F
    return F
  
    # Core energy. WORKS!
  def Ecore(self):
    def F(a,R):
      symbol = self.atoms[a].symbol
      S  = K1[symbol]*math.exp(-L1[symbol]*(R-M1[symbol])**2)
      S += K2[symbol]*math.exp(-L2[symbol]*(R-M2[symbol])**2)
      S += K3[symbol]*math.exp(-L3[symbol]*(R-M3[symbol])**2)
      S += K4[symbol]*math.exp(-L4[symbol]*(R-M4[symbol])**2)
      return S
    
    Ec = 0.0
    for A in range(len(self.atoms)):
      for B in range(A+1,len(self.atoms)):
        R = vdist(self.atoms[A],self.atoms[B])				
        Q = Z[self.atoms[A].symbol]*Z[self.atoms[B].symbol]
        orbital1 = self.atoms[A].orbitals[0]
        orbital2 = self.atoms[B].orbitals[0]
        if self.tc_te.has_key((orbital1,orbital1,orbital2,orbital2)):
          repuls = self.tc_te[(orbital1,orbital1,orbital2,orbital2)]
        enuc = Q*repuls
        scale = (math.exp(-self.orbitals[self.atoms[A].orbitals[0]].alpha*R) +
           math.exp(-self.orbitals[self.atoms[B].orbitals[0]].alpha*R))
        scale = abs(scale*enuc) + Q/R*(F(A,R) + F(B,R))
        Ec += enuc + scale
    self.Ec = Ec
    return Ec
  def Energy(self,F,P):
    # Calculate Eel
    Eel = 0.0
    n = len(self.orbitals)
    if debug:
      print 'In Energy(): F, H, P:'
      print F
      print self.H
      print P
    for i in range(n):
      for j in range(n):
        Eel += 0.5*P[i][j]*(self.H[i][j] + F[i][j])
    
    # Total energy = electric energy + core repulsion energy
    if debug:
      print 'Electronic energy:',Eel
      print 'Nuclear repulsion energy:',self.Ec
    E = Eel + self.Ec
    return E
	

  def get_P(self,F):
    Fp = F+self.H
    Energy , C = objects.linalg.eigh(Fp)
    # jmht no longer need the transpose as we use the same format as numpy
    #C = objects.numeric.transpose(C)
    if 0:
      print 'Eigenvalues:',Energy
      print 'Orbitals:'
      print C
    self.eig = Energy
    self.mo = C
    n = len(self.orbitals)
    P = objects.numeric.zeros((n,n)) * 0.0
    for i in range(n):
      for j in range(n):
        P[i][j] = 0.0
        for k in range(self.number_of_electrons()/2):
          P[i][j] += 2*C[i][k]*C[j][k]
    self.P = P
    return P

  def calc_H(self,part=-1):
    def b(a,b):
      return 0.5*(self.orbitals[a].beta+self.orbitals[b].beta)*self.S[a][b]
    n = len(self.orbitals)
    
    if part != -1:
      H = self.H
      for j in self.atoms[part].orbitals:
        for i in range(n):
          S = 0.0
          if(i==j):
            if(self.orbitals[i].ot != 0):
              S = Up[self.atoms[self.orbitals[i].atom].symbol]
            else:
              S = Us[self.atoms[self.orbitals[i].atom].symbol]
            H[i][j] = S + self.V[i][j]
          else:
            H[i][j] = b(i,j)
          H[j][i]=H[i][j]
      self.H = H
      return
    H = objects.numeric.zeros((n,n)) * 0.0
    for j in range(n):
      for i in range(j,n):
        S = 0.0
        if(i==j):
          if(self.orbitals[i].ot != 0):
            S = Up[self.atoms[self.orbitals[i].atom].symbol]
          else:
            S = Us[self.atoms[self.orbitals[i].atom].symbol]
        if self.orbitals[i].atom == self.orbitals[j].atom:
          H[i][j] = S + self.V[i][j]
        else:
          H[i][j] += b(i,j)
        H[j][i]=H[i][j]    # BUG, this line was missing!!!
    self.H=H
    if debug:
      print 'H:'
      print self.H

  def calc_tc_te(self,atom=-1):
    "Calculates the two-center two-electron integrals for the molecule."
    "if optional parameter 'atom' is passed, only integrals involving the atom # 'atom' is recalculated"
    # Only for orbitals on 'atom'?
    if atom!=-1:
      a = atom
      for b in range(len(self.atoms))[a+1:]:
        x = self.tc_te_diatom(self.atoms[a],self.atoms[b],noscreen = 1)
        for i in range(len(x)):
          self.tc_te[x[i][0]] = x[i][1]
          self.tc_te[(x[i][0][2],x[i][0][3],x[i][0][0],x[i][0][1])] = self.tc_te[x[i][0]]
    else:
      self.tc_te = {} # Clear the integral dict to get rid of old values
      for a in range(len(self.atoms)):
        for b in range(a+1,len(self.atoms)):
          x = self.tc_te_diatom(self.atoms[a],self.atoms[b])
          for i in range(len(x)):
            integral = x[i][1]
            self.tc_te[x[i][0]] = integral
            self.tc_te[(x[i][0][2],x[i][0][3],x[i][0][0],x[i][0][1])] = integral
            self.tc_te[(x[i][0][2],x[i][0][3],x[i][0][1],x[i][0][0])] = integral
            self.tc_te[(x[i][0][3],x[i][0][2],x[i][0][0],x[i][0][1])] = integral
            self.tc_te[(x[i][0][3],x[i][0][2],x[i][0][1],x[i][0][0])] = integral
            self.tc_te[(x[i][0][0],x[i][0][1],x[i][0][3],x[i][0][2])] = integral
            self.tc_te[(x[i][0][1],x[i][0][0],x[i][0][2],x[i][0][3])] = integral
            self.tc_te[(x[i][0][1],x[i][0][0],x[i][0][3],x[i][0][2])] = integral
      #print 'integrals:'
      #for k in self.tc_te.keys():
      #	print k,self.tc_te[k]

    ##
    # Calculates the energy by doing a full SCF
    ##
  def get_E(self,part=-1,partb=-1):
    def mx(a): #Returns maximum value in matrix a
      m = 0.0
      for i in range(len(a)):
        for j in range(len(a)):
          if abs(a[i][j])>m:
            m = abs(a[i][j])
      return m
          
    self.get_g_and_h()
    # Default, calculate all properties from scratch
    if part == -1:
      self.get_S() 
      self.calc_tc_te()
      self.get_V()
      self.calc_H()
      F0 = self.EH()
      P = self.get_P(F0)
  
    # If only one particle 'part' has moved, reuse as many values as possible
    else:
      self.get_S(part)
      if partb != -1:
        self.get_S(partb)
      self.calc_tc_te()
      self.get_V()
      self.calc_H()
      P = self.P
      
    E1 = 0.0
  
    self.Ecore()
    G = self.twofock(P)
    niter = 0
    E2 = self.Energy(G+self.H,P)
    ##
    # TODO: Find a good convergence condition
    ##
    damp = 0.0
    E_down = 0 #Increase when energy is going down, zero when going up
    maxiter = 50
    mindiff = 1e-4
    while niter<1 or (niter < maxiter and mx(P-Po)>mindiff):
      niter += 1
      Po = P
      P = self.get_P(G)
      P = (1 - damp)*P + damp*Po
      G = self.twofock(P)
      E1 = E2
      E2 = self.Energy(G+self.H,P)
      if E2 > E1:
        damp = 0.5*(1 + damp)
        E_down = 0
#        print 'Energy going up, setting damping to ',damp
      else:
        E_down += 1
        if E_down > 3:
          damp *= 0.5
#          print 'Energy going down fine, setting damping to ',damp
    self.G = G
    self.P = P
    self.Eeval += 1
    if niter >= maxiter:
      print 'WARNING: SCF not converged in %i iterations, last energy difference:' % maxiter,E2-E1
    return E2

    ##
    # Calculates the energy using only the current bond-order matrix
    ##
  def get_fd_E(self,P,part=-1,partb=-1):
    self.get_g_and_h()
    # Default, calculate all properties from scratch
    if part == -1:
      self.get_S() 
      self.calc_tc_te()
    # If only one particle 'part' has moved, reuse as many values as possible
    else:
      self.get_S(part)
      if partb != -1:
        self.get_S(partb)
      self.calc_tc_te()
      P = self.P    
    self.get_V()
    self.calc_H()
    self.Ecore()
    G = self.twofock(P)
    E = self.Energy(G+self.H,P)
    return E
  
  def gradient(self,fixed = -1):
    self.get_E()
    n = len(self.atoms)
    grad = objects.numeric.array(((0.0,)*3*n,))
    grad = objects.numeric.reshape(grad,(3*n,1))
    for a in range(n):
      if fixed != -1 and fixed[a] == 1:
        grad[3*a:3*a+3] = 0.0
        continue
      for i in ['x','y','z']:
        self.atoms[a].__dict__[i] += derivative_step
        E1 = self.get_E(a)
        self.atoms[a].__dict__[i] -= 2*derivative_step
        E2 = self.get_E(a)
        self.atoms[a].__dict__[i] += derivative_step
        grad[3*a+['x','y','z'].index(i)] = (E1-E2)/(2*derivative_step)
    return grad
  
    # Frozen density gradient
  def fd_gradient(self,fixed = -1,fourpoint = 0):
    self.get_E()
    n = len(self.atoms)
    grad = objects.numeric.array(((0.0,)*3*n,))
    grad = objects.numeric.reshape(grad,(3*n,1))
    for a in range(n):
#      if a==0:
#        grad[3*a:3*a+3] = 0.0
#        continue
      for i in ['x','y','z']:
        orig = self.atoms[a].__dict__[i]
        if fourpoint == 0:
          self.atoms[a].__dict__[i] = orig + derivative_step
          E1 = self.get_fd_E(self.P,a)
          self.atoms[a].__dict__[i] = orig - derivative_step
          E2 = self.get_fd_E(self.P,a)
          self.atoms[a].__dict__[i] = orig
          grad[3*a+['x','y','z'].index(i)] = (E1-E2)/(2*derivative_step)
        else:
          self.atoms[a].__dict__[i] = orig + 2*derivative_step
          E1 = self.get_fd_E(self.P,a)
          self.atoms[a].__dict__[i] = orig + derivative_step
          E2 = self.get_fd_E(self.P,a)
          self.atoms[a].__dict__[i] = orig - derivative_step
          E3 = self.get_fd_E(self.P,a)
          self.atoms[a].__dict__[i] = orig - 2*derivative_step
          E4 = self.get_fd_E(self.P,a)
          self.atoms[a].__dict__[i] = orig
          grad[3*a+['x','y','z'].index(i)] = (E4-8*(E3-E2)-E1)/(12*derivative_step)
    return grad
  
  def fd_hessian(self,fixed=-1):
    self.get_E()
    n = len(self.atoms)
    hess = objects.numeric.array(((0.0,)*(3*n)**2,))
    hess = objects.numeric.reshape(hess,(3*n,3*n))
    for a in range(n):
      if fixed != -1 and fixed[a] == 1:
        hess[3*a:3*a+3][1:3*n] = 0.0
        hess[3*a,3*a] = 1.0
        hess[3*a+1,3*a+1] = 1.0
        hess[3*a+2,3*a+2] = 1.0
        continue
      
    for i in ['x','y','z']:
      self.atoms[a].__dict__[i] += derivative_step
      g1 = self.fd_gradient(fixed)
      self.atoms[a].__dict__[i] -= 2*derivative_step
      g2 = self.fd_gradient(fixed)
      self.atoms[a].__dict__[i] += derivative_step
      for j in range(3*n):
        g1[j]=1/(2*derivative_step)*float(g1[j])
        g2[j]=1/(2*derivative_step)*float(g2[j])
        hess[j][3*a+['x','y','z'].index(i)]+=1*0.5*(g1[j]-g2[j])
        hess[3*a+['x','y','z'].index(i)][j]+=1*0.5*(g1[j]-g2[j])
          
    return hess
  
  def hessian(self,fixed=-1):
    E = self.get_E()
    P = self.P
    n = len(self.atoms)
    hess = objects.numeric.array(((0.0,)*(3*n)**2,))
    hess = objects.numeric.reshape(hess,(3*n,3*n))
    for a in range(3*n):
      atoma=a/3
      if fixed != -1 and fixed[atoma] == 1:
        hess[a][1:3*n] = 0.0
        hess[a][a] = 1.0
        continue
      
      keya = 'x'
      if a%3 == 1:
        keya = 'y'
      if a%3 == 2:
        keya = 'z'
      self.atoms[atoma].__dict__[keya] += 2*derivative_step
      E1 = self.get_E(atoma)
      self.P = P
      self.atoms[atoma].__dict__[keya] -= derivative_step
      E2 = self.get_E(atoma)
      self.P = P
      self.atoms[atoma].__dict__[keya] -= 2*derivative_step
      E3 = self.get_E(atoma)
      self.P = P
      self.atoms[atoma].__dict__[keya] -= derivative_step
      E4 = self.get_E(atoma)
      self.P = P
      self.atoms[atoma].__dict__[keya] += 2*derivative_step
      hess[a][a] = (-E1+16*E2-30*E+16*E3-E4)/(12*derivative_step**2)
  
      for b in range(3*n)[a+1:]:
        keyb = 'x'
        if a%3 == 1:
          keyb = 'y'
        if a%3 == 2:
          keyb = 'z'
        atomb=b/3
        
        self.atoms[atoma].__dict__[keya] += derivative_step
        self.atoms[atomb].__dict__[keyb] += derivative_step
        E1 = self.get_E(atoma,atomb)
        self.P = P
        self.atoms[atomb].__dict__[keyb] -= 2*derivative_step
        E2 = self.get_E(atoma,atomb)
        self.P = P
        self.atoms[atoma].__dict__[keya] -= 2*derivative_step
        self.atoms[atomb].__dict__[keyb] += 2*derivative_step
        E3 = self.get_E(atoma,atomb)
        self.P = P
        self.atoms[atomb].__dict__[keyb] -= 2*derivative_step
        E4 = self.get_E(atoma,atomb)
        self.P = P
        self.atoms[atoma].__dict__[keya] += derivative_step
        self.atoms[atomb].__dict__[keyb] += derivative_step
        hess[a][b] = (E1-E2-E3+E4)/(4*derivative_step**2)
    for a in range(3*n):
      for b in range(3*n)[a+1:]:
        hess[b][a] = hess[a][b]
    return hess

  def pos(self):
    n = len(self.atoms)
    r = objects.numeric.array(((0.0,)*3*n,))
    r = objects.numeric.reshape(r,(3*n,1))
    for i in range(n):
      r[3*i] = self.atoms[i].x
      r[3*i+1] = self.atoms[i].y
      r[3*i+2] = self.atoms[i].z
    return r

  def linesearch_quadratic(self,E,d,backward_search_ok=0):
    def move(d,h):
      for i in range(len(self.atoms)):
        self.atoms[i].x += h*float(d[3*i])
        self.atoms[i].y += h*float(d[3*i+1])
        self.atoms[i].z += h*float(d[3*i+2])
    def norm(x):
      s = 0.0
      for i in range(len(x)):
        s += x[i]**2
      #jmht return sqrt(s)
      return math.sqrt(s)
    E0 = E
    dn = d/norm(d)
    h = 0.1
    # dummy values on entry
    E1 = E0 + 1
    E2 = E0
    hopt = -1
    q = -1
    p = 1
    Eopt = E + 1
    while p > 0 or q < 0 or hopt < 0 or E2 < E1 or Eopt > E:
      move(dn,h)
      E1 = self.get_E()
      move(dn,h)
      E2 = self.get_E()
      move(dn,-2*h)
#      print 'while,E0,E1,E2',E0,E1,E2
      if E2 < E1 and E2 < E0: # Go to r0 + 2h*d and continue from there
        E0 = E2
        E1 = E0 + 1
        E2 = E0
        h = 0.1
        move(dn,2*h)
#        print 'skipping to 2h'
      else:
        # E(h) = E0 + p*h + q/2*h^2 
        q = (E2 + E0 - 2*E1)/h**2
        p = (4*E1 - 3*E0 - E2)/(2*h)
        # E'(h) = 0 = p + q*h => h = -p/q
	if abs(q) < 1e-8:
		print q,E0,E1,E2,h
        hopt = -p/q
        if (hopt < 0 and not backward_search_ok) or (q < 0):
	  print 'h /= 2, q,hopt=',q,hopt
          h /= 2
        else:
          move(dn,hopt)
          Eopt = self.get_E()
          if Eopt > E:
            move(dn,-hopt)
            h /= 2
#    print 'Epredicted, Eactual',E0+hopt*p + hopt**2*q/2,Eopt
    if Eopt > E:
      print 'WARNING: Energy increasing at end of linesearch: E,Eopt',E,Eopt

  def steepestdescent(self, max_iter = 50, conv_res = 0.00001):
      E0 = self.get_E()
      g = self.fd_gradient()
      self.linesearch_quadratic(E0,-g)
      E1 = E0 + 2*conv_res
      niter = 0
      r0 = self.pos()
      while niter < 1 or niter < max_iter and abs(E0-E1) > conv_res:
          g = self.fd_gradient()
          self.linesearch_quadratic(E0,-g)
          E1 = E0
          E0 = self.get_E()
          r1 = self.pos()
          yield self.atoms, E0
          niter += 1
          r0 = r1
          
  def conjugategradient(self, max_iter = 100, gradient_threshold = 1e-3, energy_threshold = 1e-6):
      E0 = self.get_E()
      yield self.atoms, E0
      r0 = self.pos()
      g = self.fd_gradient(fourpoint=0)
      do = -g
      self.linesearch_quadratic(E0,-g)
      E1 = self.get_E()
      minE = E0
      if E1<minE:
          minE = E1
          r = self.pos()
      niter = 0
      r = self.pos()
      if debug:
        print '|g|/(1+|E|)',norm(g)/(1+abs(E1))
        print 'DE',abs(E0-E1) 
      while niter < max_iter and norm(g)/(1+abs(E1))>gradient_threshold and abs((E0-E1)/E1) > energy_threshold:
          r1 = self.pos()
          go = g
          g = self.fd_gradient(fourpoint=0)
          a = self.atoms[1]
          n = float(objects.numeric.matrixmultiply(objects.numeric.transpose(g),g)) - float(objects.numeric.matrixmultiply(objects.numeric.transpose(g),go)) 
          d = float(objects.numeric.matrixmultiply(objects.numeric.transpose(go),go))
          beta=n/d
          dn = -g + beta*do
          do = dn
          self.linesearch_quadratic(E1,dn,backward_search_ok=1)
          E0 = E1
          E1 = self.get_E()
          yield self.atoms, E1
          if E1<minE:
              minE = E1
              r = self.pos()
          r0 = r1
          niter += 1
          
  def newton(self, max_iter = 20, conv_res = 0.0001, fixed=-1):
    def move(direction):                                                                                        
      for i in range(len(self.atoms)):                                                                           
        self.atoms[i].x += float(direction[3*i])                                                                 
        self.atoms[i].y += float(direction[3*i+1])                                                               
        self.atoms[i].z += float(direction[3*i+2])                                                               
    E0 = self.get_E()
    yield self.atoms, E0
    rc = self.pos()                                                                                              
    gc = self.fd_gradient(fixed,fourpoint=1)                                                                     
    self.linesearch_quadratic(E0,-gc)                                                                            
    N = 0                                                                                                       
                                                                                                                  
    n = len(self.atoms)*3                                                                                        
    Bc = objects.numeric.array(((0.0,)*(n)**2,))                                                                            
    Bc = objects.numeric.reshape(Bc,(n,n))                                                                                      
    for i in range(n):                                                                                          
      Bc[i][i] = 10.0                                                                                           
    E1 = self.get_E()                                                                                            
                                                                                                                  
    rp = self.pos()                                                                                              
                                                                                                                  
    while N<1 or N < 50 and abs(E0-E1) > 0.1*conv_res: # and norm(rp-rc)/len(rp-rc) > 0.0001:                   
      gp = self.fd_gradient(fixed,fourpoint=1)                                                                   
      rp = self.pos()                                                                                            
      sc = rp - rc # geometry difference                                                                        
      yc = gp - gc # gradient difference                                                                        
      t1 = 1.0/float(objects.numeric.matrixmultiply(objects.numeric.transpose(yc),sc))*objects.numeric.matrixmultiply(yc,objects.numeric.transpose(yc))                         
      n2 = objects.numeric.matrixmultiply(objects.numeric.matrixmultiply(Bc,sc),objects.numeric.matrixmultiply(objects.numeric.transpose(sc),Bc))                               
      d2 = float(objects.numeric.matrixmultiply(objects.numeric.transpose(sc),objects.numeric.matrixmultiply(Bc,sc)))                                           
      Bp = Bc + t1 - n2/d2                # Update the Hessian                                                  
      # Now we have the gradient and the estimated Hessian.                                                     
      sN = -objects.numeric.matrixmultiply(inverse(Bp),gp) # The quasi-Newton step                                              
      steplen = min(0.2+0.25*N,1.0)        # This make the step larger as the number of iterations              
                                           #  and thus the precision of the estimation increases                
                                           # After a few cycles, a full step is taken                           
      #    move(steplen*sN)                                                                                     
      self.linesearch_quadratic(E1,sN,backward_search_ok=1)                                                      
      N += 1                                                                                                    
      rc = rp                                                                                                   
      gc = gp                                                                                                   
      Bc = Bp                                                                                                   
      E0 = E1                                                                                                   
      E1 = self.get_E()
      yield self.atoms, E1
    if N >= 50:                                                                                                 
      print "Maximum number of iterations reached"                                                              
    if abs(E0-E1) <= 0.1*conv_res:                                                                              
      print "Convergence resolution reached"                                                                    
#    if norm(rp-rc)/len(rp-rc) <= 0.0001:                                                                        
#      print "Displacement limit reached"                                                                        
    if abs(float(objects.numeric.matrixmultiply(objects.numeric.transpose(yc),yc))) < 0.01:                                                     
      print "Gradient change too small"                                                                         
    self.linesearch_quadratic(E0,-gp)                                                                            
    E1 = self.get_E()                                                                                            



  

  

#####################################################################
#
# Miscalleaneous functions that were previously in the file misc.py
#
#####################################################################
# Compute n!
def factorial(n):
	if((n == 0) or (n == 1)):
		return 1
	if(n<0):
		return 0
	p = 1
	for i in range(n+1)[2:]:
		p = p * i
	return p
# Binomial coefficients
def binom(n,m):
	if((n-m<0) or (m<0)):
		return 0
	return factorial(n)/(factorial(n-m)*factorial(m))
# Auxiliary function A(n,a)
def A(n,a):
	if(n==0):
		return (1.0/a)*math.exp(-a)
	return (1.0/a)*(n*A(n-1,a)+math.exp(-a))
# Auxiliary function B(n,a)
def B(n,a):
	if(a==0.0):
		return (1.0/(n+1))*(1+(-1)**n)
	if(n==0):
		return (1.0/a)*(math.exp(a)-math.exp(-a))
	return (1.0/a)*(n*B(n-1,a)+((-1)**n)*math.exp(a)-math.exp(-a))
def gamma(x):
	if (x == 0.5):
		#jmht return sqrt(pi)
		return math.sqrt(pi)
	elif(x == 1):
		return 1.0
	else:
		return (x-1)*gamma(x-1)
def norm(g):
  s = 0
  for i in range(len(g)):
    s += float(g[i])**2
  return math.sqrt(s)


##########################################
#
# Unittesting stuff
# 
##########################################

class AM1TestCases(unittest.TestCase):

    def testCH2(self):
        
        # Create the molecule
        Am1Mol = Molecule()

        Am1Mol.add( 'C','C',0.0,0.0,0.0 )
        Am1Mol.add( 'H','H',1.0,0.0,0.0 )
        Am1Mol.add( 'H','H',1.0,1.0,0.0 )

        max_iter=100
        gradient_threshold=1e-6
        energy_threshold=1e-3

        generator = Am1Mol.conjugategradient( max_iter,
                                              gradient_threshold,
                                             energy_threshold )
        done=0
        while not done:
            try:
                atoms,energy = generator.next()
            except StopIteration:
                done=1
                break
        
        self.assertAlmostEqual(energy,-150.72230108)
            


    def testH2O(self):
        
        # Create the molecule
        Am1Mol = Molecule()

        Am1Mol.add( 'O','O',0.0,0.0,0.0 )
        Am1Mol.add( 'H','H',0.0,0.0,1.05 )
        Am1Mol.add( 'H','H',0.934609,0.0,-0.224954 )

        max_iter=100
        gradient_threshold=1e-6
        energy_threshold=1e-3

        generator = Am1Mol.conjugategradient( max_iter,
                                              gradient_threshold,
                                             energy_threshold )
        done=0
        while not done:
            try:
                atoms,energy = generator.next()
            except StopIteration:
                done=1
                break
        
        self.assertAlmostEqual(energy,-348.40642501570665)

def testMe():
    """Return a unittest test suite with all the testcases that should be run by the main 
    gui testing framework."""

    return  unittest.TestLoader().loadTestsFromTestCase(AM1TestCases)


if __name__ == "__main__":

    unittest.main()
