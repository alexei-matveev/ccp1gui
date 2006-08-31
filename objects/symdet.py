import Numeric, LinearAlgebra
import copy,math
#,sys,quaternion
#from vector import Vector

global thresh
thresh = 0.1

debug = None

def tightCartesian(atom1,atom2):
    global thresh
    if atom1.dist2(atom2) < thresh:
        return 1
    else:
        if atom1.dist2(atom2) < thresh:
            print atom1,'and',atom2,'are too far apart (', atom1.dist2(atom2),')'

class SymOp:    
    def __init__(self, n, axis, parity = 1):
        """Defines a symmetry operation, as a possible
        inversion followed by a rotation 2*pi/n around
        axis (does not have to be normalized)."""
        #self.q = quaternion.rotor(axis,2*math.pi/n)
        self.q = rotor(axis,2*math.pi/n)
        self.fixAngle()
        self.parity = parity
        if parity == 1 or n % 2 == 0:
            self.order = n
        else:
            self.order = 2*n

    def fixAngle(self):
        q = self.q
        if q[0] < 0:
            q[0] = -q[0]
            q[1] = -q[1]
            q[2] = -q[2]
            q[3] = -q[3]

    def angle(self):
        return self.q.angle()
            
    def transform(self, r):
        return Vector(self.q.rotate(self.parity*r))

    def getOrder(self):
        """Calculate the order of the operation by brute force, if
        neccessary."""
        if not self.order:
            order = 1
            opn = copy.deepcopy(self)
            while not opn.isUnity():
                opn = opn.compose(self)
                order += 1
            self.order = order
        return self.order

    def compose(self, op2):
        newop = SymOp(1,Vector(1,0,0))
        newop.q = self.q*op2.q
        newop.parity = self.parity*op2.parity
        newop.order = None
        newop.fixAngle()
        return newop
    
    def equalTo(self,op,threshold = 1e-12):
        return self.parity == op.parity and (self.q.dist2(op.q) < threshold or
                                             self.q.dist2(-1*op.q) < threshold)
                
    def __eq__(self,op):
        return self.equalTo(op)

    def isUnity(self,threshold = 1e-12):
        return self.parity == 1 and abs(self.q[0]-1) < threshold

    def isInversion(self,threshold = 1e-12):
        return self.parity == -1 and abs(self.q[0]-1) < threshold

    def orthogonalTo(self,op):
	return self.q.orthogonalTo(op.q)

    def parallelTo(self,op):
	return self.q.parallelTo(op.q)

    def __str__(self):
        n = self.getOrder()
        if self.parity == -1:
            if n == 2:
                if self.isInversion():
                    return "i"
                else:
                    return "sigma" + str(Vector(self.q.c[1:]).normalized())
            else:
                return "S%i" % n + str(Vector(self.q.c[1:]).normalized())
        else:
            return "C%i" % n + str(self.q.c)
            return "C%i" % n + str(Vector(self.q.c[1:]).normalized())

    
class SymGroup:
    def __init__(self):
        self.elements = [] # all elements except the unit element
        self.Cinf_axis = None

    def setCinf(self,axis):
        self.Cinf_axis = axis

    def hasElement(self,op):
        return op.isUnity() or op in self.elements

    def addElement(self,op):
	op.fixAngle()
        if not op.isUnity() and not op in self.elements:
            self.elements.append(op)
            for e in self.elements:
                self.addElement(op.compose(e))
                self.addElement(e.compose(op))

    def printElements(self):
        if self.Cinf_axis:
            print 'Cinf axis:',self.Cinf_axis
        print 'Remaining elements: (Order parity)'
        for e in self.elements:
            print e

    def generators(self):
        """Return a list of generators of the group. Prefer generators
        with small angles."""
        self.elements.sort(lambda x,y: cmp(x.angle(),y.angle()))
        G2 = SymGroup()
        gen = []
        for op in self.elements:
            if not op in G2.elements:
                gen.append(op)
                G2.addElement(op)
        # If i is in the group, make the other generators
        # be of even parity.
        inv = SymOp(1,Vector(1,0,0),-1)
        if inv in gen:
            gen = copy.deepcopy(gen)
            for op in gen:
                if not op.isInversion() and op.parity == -1:
                    op.parity = 1        
        return gen

    def label(self, gen = None):
        """Return point group label"""
        if not gen:
            gen = self.generators()
        inv = SymOp(1,Vector(1,0,0),-1)
        if inv in self.elements:
            has_inv = 1
        else:
            has_inv = 0
        if self.Cinf_axis:
            if has_inv:
                return 'Dinf,h'
            else:
                return 'Cinf,v'
        elif len(gen) == 0:
            return 'C1'
        else:
	    Cnlist = []
            for e in self.elements:
                if e.parity == 1 and e.getOrder() >= 3:
		    found = 0
                    for Cn in Cnlist:
                        if e.parallelTo(Cn):
                           found = 1
                           break
                    if not found:
                        Cnlist.append(e)                        
            if len(Cnlist) > 1:
                if not has_inv:
                    return 'Td'
                else:
                    for e in self.elements:
                        if e.parity == 1 and e.getOrder() == 5:
                            return 'Ih'
                    return 'Oh'
            else:
                Cn_max = None
                for e in self.elements:
                    if e.parity == 1:
                        if Cn_max:
                            if e.getOrder() > Cn_max.getOrder():
                                Cn_max = e
                        else:
                            Cn_max = e
                if Cn_max:
                    n = Cn_max.getOrder()
                    sigmah = 0
                    for e in self.elements:
                        if e.parity == -1 and e.getOrder() == 2 and e.parallelTo(Cn_max):
                            sigmah = 1
                    nC2 = 0
                    for e in self.elements:
                         if e.parity == 1 and e.getOrder() == 2 and e.orthogonalTo(Cn_max):
                             nC2 += 1
                    if nC2 == n:
                         if sigmah:
                                 return 'D%ih' % n
                         else:
                             return 'Dn or Dnd'                      
                    if sigmah:
                        return 'C%ih' % n
                    nsigmav = 0
                    for e in self.elements:
                        if e.parity == -1 and e.getOrder() == 2 and e.orthogonalTo(Cn_max):
                            nsigmav += 1
                    if nsigmav == n:
                        return 'C%iv' % n
                    for e in self.elements:
                        if e.parity == -1 and e.getOrder() == 2*n:
                            return 'S%i' % 2*n
                    return 'C%i' % n                                        
                # no Cn axis
                for e in self.elements:
                    if e.parity == -1 and e.getOrder() == 2:
                        return 'Cs'
                if has_inv:
                    return 'Ci'
                return 'C1'
        return 'Error2'
                            
    def printGroup(self):
        gen = self.generators()
        print self.label(gen)
        print 'Generators:'
        if self.Cinf_axis:
            print 'Cinf',self.Cinf_axis
        for e in gen:
            print e
	print 'Elements:'
        for e in self.elements:
            print e
    
class PointSet:
    def __init__(self, pset = []):
        self.pset = copy.deepcopy(pset)
        self.indices = [-1]*len(pset)
        
    def addPoint(self, point, index = -1):
        "Add a point (Vector) to the set."
        self.pset.append(point)
        self.indices.append(index)

    def export(self):
        points = []
        for i in range(len(self.pset)):
            r = self.pset[i]
            points.append([self.indices[i],[r[0],r[1],r[2]]])
        return points
                
    def points(self):
        return self.pset

    def nrPoints(self):
        return len(self.pset)

    def scale(self,c):
        for i in range(len(self.pset)):
            self.pset[i] = c*self.pset[i]
        
    def translate(self,dr):
        for i in range(len(self.pset)):
            self.pset[i] = self.pset[i] + dr
            
    def rotate(self,axis,angle):
        #R = quaternion.rotor(axis,angle)
        R = rotor(axis,angle)
        for i in range(len(self.pset)):
            self.pset[i] = R.rotate(self.pset[i])

    def mapNearest(self, set2, quick = 1):
        """Return a list of indices mapping each point i in
        self to map[i] in set 2, to minimize the sum of the squares
        of the distances. Not guaranteed to find the optimal fit!"""
        if len(self.pset) != len(set2.pset):
            return None
        # first do an intial guess
        remain = range(len(self.pset))
        themap = []
        for p in self.pset:
            mind2 = p.dist2(set2.pset[remain[0]])
            minj  = 0
            for j in range(1,len(remain)):
                m = p.dist2(set2.pset[remain[j]])
                if m < mind2:
                    mind2 = m
                    minj = j
            themap.append(remain[minj])
            remain[minj:minj+1] = []
        if quick:
            return themap
        # check if we can win anything by swapping pairs
        def dist2(i,j):
            return self.pset[i].dist2(set2.pset[themap[j]])
        again = 1
        while again:
            again = 0
            for i in range(len(themap)):
                for j in range(i+1,len(themap)):
                    if dist2(i,i) + dist2(j,j) > dist2(i,j) + dist2(j,i):
                        tmp = themap[i]
                        themap[i] = themap[j]
                        themap[j] = tmp
                        again = 1
                        break
                if again:
                    break
        return themap

    def hasPoint(self, r, testSame):
        """Test if there is a point p in the set for which
        testSame(r,p) is true."""
        for p in self.pset:
            if testSame(r,p):
                return 1
        return 0

    def addTo(self, set2, mapping = None):
        """'Add' the positions of set2 to self, as part of an averaging."""
        if not mapping:
            mapping = self.mapNearest(set2)
        for i in range(len(mapping)):
            self.pset[i] = self.pset[i] + set2.pset[mapping[i]]

    def matches(self, set2, testSame, mapping = None):
        if not mapping:
            mapping = self.mapNearest(set2)
        for i in range(len(mapping)):
            if not testSame(self.pset[i],set2.pset[mapping[i]]):
                return 0
        return 1

    def transform(self,op):
        ps = PointSet()
        for p in self.pset:
            ps.addPoint(op.transform(p))
        return ps
            
    def hasSymmetry(self, op, testSame): # 75% time of testcase spent here
        """Test if op (a SymOp) is a symmetry of the pointset,
        with the maximum deviation^2 = maxdev2."""
        newpoints = []
        # do an optimistic test first
        for p in self.pset:
            opp = op.transform(p)
            if not self.hasPoint(opp,testSame):
                return 0
            newpoints.append(opp)
        # do a complete test
        return self.matches(PointSet(newpoints),testSame) # slow

    def deleteRedundant(self,op,testSame):
        """Delete those points which can be recovered by applying op
        multiple times to the remaining points. Return number of
        deleted points.
        """
        ndel = 0
        i = 0
        while i < len(self.pset):
            mod = 0
            for p in self.pset:
                if p != self.pset[i] and testSame(op.transform(p),self.pset[i]):
                    del self.pset[i:i+1]
                    ndel += 1
                    mod = 1
                    break
            if not mod:
                i += 1
        return ndel

    def addRedundant(self,op,testSame):
        """Add those new points which can be created by applying op to
        the existing points. Return number of points added.
        Powers of op are not considered, which means you might have to
        run this function until it returns 0 to generate all points.
        """
        nadd = 0
        new = []
        for p in self.pset:
            new.append(op.transform(p))
        for pn in new:
            found = 0
            for p in self.pset:
                if testSame(pn,p):
                    found = 1
                    break
            if not found:
                self.pset.append(pn)
                nadd += 1
        return nadd
            
    def symmetrize(self, ops):
        Sorig = copy.deepcopy(self)
        for op in ops:
            self.addTo(Sorig.transform(op))
        self.scale(1.0/(len(ops)+1))


class Molecule:
    def __init__(self):
        self.atomsets = {}

    def addAtom(self, label, pos, index = -1):
        "pos is of type Vector"
        if not self.atomsets.has_key(label):
            self.atomsets[label] = PointSet()
        self.atomsets[label].addPoint(Vector(pos),index)

    def hasSymmetry(self,op,testSame):
        print 'Testing',op,
        failed = 0
        for s in self.atomsets.items():
            if not s[1].hasSymmetry(op,testSame):
                print s[0],'no'
                failed = 1
        if failed:
            return 0
        else:
            print 'yes'
            return 1

    def export(self):
        """Return a list of atom coordinates and indices."""
        atoms = []
        for s in self.atomsets.values():
            atoms.extend(s.export())
        return atoms

    def getGroup(self, testSame, eigvals, eigrelthres = 0.1):
        """Return the SymGroup of the molecule. Does not move the
        origin permanently. Eigenvalues are considered identical if
        the relative difference is less than eigrelthres.
        eigvals are the eigenvalues of the x, y and z axes.
        """
        print "Eigenvalues:", eigvals
        G = SymGroup()
        axis = None
        other = None
        threedeg = None
        invop = SymOp(1,Vector([1,0,0]),-1)
        inv = 0
        if self.hasSymmetry(invop,testSame):
            G.addElement(invop)
            inv = 1
        mom = [[eigvals[0],Vector(1,0,0)],
               [eigvals[1],Vector(0,1,0)],
               [eigvals[2],Vector(0,0,1)]]
        # Do we have two zero eigenvalues?
        if abs(mom[0][0]) < eigrelthres and abs(mom[1][0]) < eigrelthres:
            print "Case 1"
            G.setCinf(0.5*(mom[0][1]+mom[1][1]))
            #jmht - check with Ulf
            #cm = self.centerOfMass()
            #self.translate(-cm)        
            return G
        # Or two or three identical ones (eigenvalues are sorted min..max)
        if mom[1][0] < mom[0][0]*(eigrelthres + 1):
            print "Case 2"
            axis = mom[2][1]
            other = [mom[0][1],mom[1][1]]
        if mom[2][0] < mom[0][0]*(eigrelthres + 1): 
            print "Case 3"
            if axis:
                threedeg = 1
            else:
                axis = mom[1][1]
                other = [mom[0][1],mom[2][1]]
        if mom[2][0] < mom[1][0]*(eigrelthres + 1):
            print "Case 4"
            if axis:
                threedeg = 1
            else:
                axis = mom[0][1]
                other = [mom[1][1],mom[2][1]]
        # Branch out
        # TODO: handle threedeg case better
        if threedeg or axis:
            print "Non Abelian"
            for n in [6,5,3,2]:
                Cn = SymOp(n,axis,1)
                if not G.hasElement(Cn) and self.hasSymmetry(Cn,testSame):
                    G.addElement(Cn)
            if not inv:
                for n in [6,5,3,2]:
                    S2n = SymOp(n,axis,-1)
                    if not G.hasElement(S2n) and self.hasSymmetry(S2n,testSame):
                        G.addElement(S2n)
            for on in other:
                C2 = SymOp(2,on,1)
                if not G.hasElement(C2) and self.hasSymmetry(C2,testSame):
                    G.addElement(C2)
                sigma = SymOp(2,on,-1)
                if not G.hasElement(sigma) and self.hasSymmetry(sigma,testSame):
                    G.addElement(sigma)
        # Easiest case, nondegenerate, abelian group
        else:
            print "Abelian"
            for on in [mom[0][1],mom[1][1],mom[2][1]]:
                C2 = SymOp(2,on,1)
                if not G.hasElement(C2) and self.hasSymmetry(C2,testSame):
                    G.addElement(C2)
                sigma = SymOp(2,on,-1)
                if not G.hasElement(sigma) and self.hasSymmetry(sigma,testSame):
                    G.addElement(sigma)
        return G

    def deleteRedundant(self, testSame, group = None):
        if not group:
            group = self.getGroup(testSame)
        gen = group.generators()
        for set in self.atomsets.values():
            ndel = 1
            while ndel:
                ndel = 0
                for op in group.elements:
                    ndel += set.deleteRedundant(op,testSame)
                    

    def addRedundant(self, testSame, group):
        totadd = 0
        for set in self.atomsets.values():
            nadd = 1
            while nadd:
                nadd = 0
                for op in group.elements:
                    nadd += set.addRedundant(op,testSame)
                totadd += nadd

    def symmetrize(self, testSame, eigvals, group = None):
        if not group:
            group = self.getGroup(testSame, eigvals)
        for set in self.atomsets.values():
            set.symmetrize(group.elements)




class Quaternion:
    def __init__(self, c = None):
        if c:
            self.c = [c[0],c[1],c[2],c[3]]
        else:
            self.c = [0.0]*4
    
    def __getitem__(self, i):
        return self.c[i]

    def __setitem__(self, i, val):
        self.c[i] = val

    def mul(self, q2):
        return Quaternion([self[0]*q2[0] - self[1]*q2[1] - self[2]*q2[2] - self[3]*q2[3],
                           self[0]*q2[1] + self[1]*q2[0] + self[2]*q2[3] - self[3]*q2[2],
                           self[0]*q2[2] + self[2]*q2[0] + self[3]*q2[1] - self[1]*q2[3],
                           self[0]*q2[3] + self[3]*q2[0] + self[1]*q2[2] - self[2]*q2[1]])

    def __str__(self):
        return "%g + %gi + %gj + %gk" % (self[0],self[1],self[2],self[3])

    def __mul__(self, q):
        return self.mul(q)

    def conj(self):
        return Quaternion([self.c[0],-self.c[1],-self.c[2],-self.c[3]])

    def abs2(self):
        return self.c[0]**2 + self.c[1]**2 + self.c[2]**2 + self.c[3]**2

    def dist2(self,q):
        return (self.c[0] - q[0])**2 + (self.c[1] - q[1])**2 + (self.c[2] - q[2])**2 + (self.c[3] - q[3])**2

    def __abs__(self):
        return math.sqrt(self.abs2())

    def __rmul__(self,c):
        return Quaternion([c*self.c[0],c*self.c[1],c*self.c[2],c*self.c[3]])

    def inverse(self):
        return (1.0/self.abs2())*self.conj()

    def rotate(self,v):
        """Return QvQ~. Could be programmed more efficiently."""
        vq = Quaternion([0,v[0],v[1],v[2]])
        vr = self*vq*self.conj()
        return vr.c[1:]

    def angle(self):
        """Assuming that the quaternion is normalized, return the
        rotation angle."""
        return 2*math.acos(self.c[0])

    def orthogonalTo(self,q,thres = 1e-6):
	n1 = Vector(self.c[1],self.c[2],self.c[3]).normalized()
	n2 = Vector(q.c[1],q.c[2],q.c[3]).normalized()
	return abs(n1.dot(n2)) < thres

    def parallelTo(self,q,thres = 1e-6):
	n1 = Vector(self.c[1],self.c[2],self.c[3]).normalized()
	n2 = Vector(q.c[1],q.c[2],q.c[3]).normalized()
	return abs(abs(n1.dot(n2)) - 1)  < thres

def rotor(axis,angle):
    """Return a quaternion that rotates angle radians around
    the axis vector (does not have to be normalized), in a right-
    handed sense."""
    c = math.sin(angle/2)/math.sqrt(axis[0]**2 + axis[1]**2 + axis[2]**2)
    return Quaternion([math.cos(angle/2),c*axis[0],c*axis[1],c*axis[2]])

class Vector:
    def __init__(self, x = [0,0,0], y = None, z = None):
        if y != None:
            self.r = [x,y,z]
        else:
            self.r = copy.copy(x)
    def __getitem__(self, i):
        return self.r[i]    
    def dot(self,v):
        return self[0]*v[0] + self[1]*v[1] + self[2]*v[2]
    def cross(self,v):
        return Vector(self[1]*v[2] - self[2]*v[1],
                      self[2]*v[0] - self[0]*v[2],
                      self[0]*v[1] - self[1]*v[0])
    def scaled(self,c):
        return Vector(c*self[0],c*self[1],c*self[2])
    def abs2(self):
        return self[0]*self[0] + self[1]*self[1] + self[2]*self[2]
    def __abs__(self):
        return math.sqrt(self.abs2())
    def normalized(self):
        return self.scaled(1.0/math.sqrt(self.abs2()))
    def __add__(self,v):
        return Vector(self[0]+v[0],self[1]+v[1],self[2]+v[2])
    def __sub__(self,v):
        return Vector(self[0]-v[0],self[1]-v[1],self[2]-v[2])
    def __str__(self):
        return "(%.6f, %.6f, %.6f)" % (self.r[0],self.r[1],self.r[2])
    def __rmul__(self,c):
        return self.scaled(c)
    def __mul__(self,c):
        return self.scaled(c)
    def __neg__(self):
        return -1*self
    def dist2(self,p):
        return (self-p).abs2()
    def dist(self,p):
        return abs(self-p)


if __name__ == "__main__":
    import zmatrix, sys,os 

    if len(sys.argv) == 1:
        print "I need a file to test!"
        sys.exit(1)
        
    myfile = sys.argv[1]
    if  not os.access( myfile, os.R_OK ):
        print "I need a file to test!"
        sys.exit(1)
        
    mol = zmatrix.Zmatrix()
    mol.load_from_file( myfile )

    print "mol is ",mol.atom
    
    #mol.Symmetrise()
    #mol.toStandardOrientation()

    print "Group is: %s" % mol.getSymmetry( thresh = 0.001)
    

# M = Molecule()
# f = open('d6h.sym','r')
# M.read(f)
# f.close()
# M.toStandardOrientation()
# #M.symmetrize(tightCartesian)
# #M.toStandardOrientation()
# G = M.getGroup(tightCartesian)
# #M.deleteRedundant(tightCartesian,G)
# #M.addRedundant(tightCartesian,G)
# f = open('out.xyz','w')
# M.writeXYZ(f)
# f.close()
