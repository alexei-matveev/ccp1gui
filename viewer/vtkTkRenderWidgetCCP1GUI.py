import sys
import vtk
import vtk.tk.vtkTkRenderWidget

from viewer.debug import deb

class vtkTkRenderWidgetCCP1GUI(vtk.tk.vtkTkRenderWidget.vtkTkRenderWidget):

    """We override the vtkTkRenderWidget to supply some of our own methods and change the default key bindings"""
    
    def __init__(self, master, cnf={}, **kw):


        # Below is a horrible hack to deal with a bug when python > 2.6 and vtk < 5.4, see:
        # http://www.vtk.org/pipermail/vtkusers/2008-September/096743.html
        #
        # We can't use the Tkinter.wantobjects=0 fix as it breaks other stuff
        # within Tkinter.
        #
        # Although this supposedly appeared in Py 2.3, it doesn't seem
        # to have made it into any packaged version before 2.6
        # The problem was fixed in the vtkLoadPythonTkWidgets file on 03/07/2009
        # which corresponds to vtk 5.4
        # 
        # To get around it, we poke a fixed version of vtkLoadPythonTkWidgets from our repository
        # into the module namespace
        vtk_version = map(int,vtk.vtkVersion.GetVTKVersion().split('.'))
        if (sys.version_info[0] >= 2 and sys.version_info[1] >= 6) and (vtk_version[0] <= 5 and vtk_version[1] <= 4):
            from viewer.vtkLoadPythonTkWidgets import vtkLoadPythonTkWidgets
            vtk.tk.vtkTkRenderWidget.vtkLoadPythonTkWidgets=vtkLoadPythonTkWidgets

        #
        # Now we can carry on and init the bass class.
        #
        vtk.tk.vtkTkRenderWidget.vtkTkRenderWidget.__init__(self,master, kw)

        # Base vtkTkRenderWidget uses a vtkCellPicker
        self._Picker=vtk.vtkPointPicker()

        # Here we set out own variables
        self.camera_x = 0.
        self.camera_y = 0.
        self.camera_z = 1.

        self.near = None
        self.far = None

        self.debug=1

        # Override the default bindings with some of our own
        self.UpdateBindings()

        #
        # Methods we override
        #
    def Reset(self):
        """ Restore the initial settings"""
        #print 'Reset'
        if self._CurrentRenderer:
            self._CurrentCamera = self._CurrentRenderer.GetActiveCamera()
            camera = self._CurrentCamera
            camera.SetFocalPoint((0.,0.,0.))
            camera.SetPosition((self.camera_x,self.camera_y,self.camera_z))
            camera.SetViewUp((0.,1.,0.))
            self._CurrentRenderer.ResetCameraClippingRange()
            #print camera
            self.Render()

    def Enter(self,x,y):

        self._OldFocus=self.focus_get()
        self.focus()

        #
        # Original code:
        #self.StartMotion(x, y)
        #

        self.UpdateRenderer(x,y)

    def StartMotion(self,e,but):

        #
        # Original Code:
        #self.GetRenderWindow().SetDesiredUpdateRate(self._DesiredUpdateRate)
        #self.UpdateRenderer(x,y)
        #

        #print 'start motion'
        self.old_x = e.x
        self.old_y = e.y
        self.picked_mol = None
        self.UpdateRenderer(e.x,e.y)

    def EndMotion(self,e,but):
        
        #
        # Original code:
        #self.GetRenderWindow().SetDesiredUpdateRate(self._StillUpdateRate)
        #

        #print 'end motion'
        if e.x == self.old_x and e.y == self.old_y:
            self.PickActor(e.x,e.y,but)
                
        if self._CurrentRenderer:
            self.Render()

    def PickActor(self,x,y,but):
        """We add the but argument so we can call handlepick.
        Otherwise the code is as the original
        """
        
        if self.debug: deb("PickActor: %s : %s : %s" % (x,y,but))
        if self._CurrentRenderer:

            renderer = self._CurrentRenderer
            picker = self._Picker
            
            windowY = self.winfo_height()
            picker.Pick(x,(windowY - y - 1),0.0,renderer)

            deb("Pick returns: %s" % picker.GetPointId() )
            self.handlepick(but)
            
            assembly = picker.GetAssembly()

            #print 'pick', assembly, picker, picker.GetPath()
            #print '1st node', picker.GetPath().GetFirstNode()

            if (self._PickedAssembly != None and
                self._PrePickedProperty != None):
                self._PickedAssembly.SetProperty(self._PrePickedProperty)
                # release hold of the property
                self._PrePickedProperty.UnRegister(self._PrePickedProperty)
                self._PrePickedProperty = None

            if (assembly != None):
                self._PickedAssembly = assembly
                self._PrePickedProperty = self._PickedAssembly.GetProperty()
                # hold onto the property
                self._PrePickedProperty.Register(self._PrePickedProperty)
                self._PickedAssembly.SetProperty(self._PickedProperty)

            self.Render()
    
        #
        # Our own Methods
        #
    def UpdateBindings(self):
        """Bindings that differ from the defaults"""
        self.bind("<ButtonPress-1>",
                  lambda e,s=self: s.StartMotion(e,1))
        self.bind("<ButtonRelease-1>",
                  lambda e,s=self: s.EndMotion(e,1))
        self.bind("<ButtonPress-2>",
                  lambda e,s=self: s.StartMotion(e,2))
        self.bind("<ButtonRelease-2>",
                  lambda e,s=self: s.EndMotion(e,2))
        self.bind("<ButtonPress-3>",
                  lambda e,s=self: s.StartMotion(e,3))
        self.bind("<ButtonRelease-3>",
                  lambda e,s=self: s.EndMotion(e,3))

        self.bind("<Shift-B1-Motion>",
                  lambda e,s=self: s.RotateZ(e.x,e.y))

        self.bind("<KeyPress-r>",
                  lambda e,s=self: s.Reset())
        self.bind("<KeyPress-f>",
                  lambda e,s=self: s.ResetToFit(e.x,e.y))
        self.bind("<KeyPress-p>",
                  lambda e,s=self: s.PickActor(e.x,e.y,0))


        # Keypad bindings
        # 5
        self.bind("<KeyPress-Clear>",
                  lambda e,s=self: s.Reset())
        # 7,9
        self.bind("<KeyPress-Home>",
                  lambda e,s=self: s.FixedRot('z',10))
        self.bind("<KeyPress-Prior>",
                  lambda e,s=self: s.FixedRot('z',-10))

        # 8,2
        self.bind("<KeyPress-Up>",
                  lambda e,s=self: s.FixedRot('x',-10))
        self.bind("<KeyPress-Down>",
                  lambda e,s=self: s.FixedRot('x',10))
        # 4,6
        self.bind("<KeyPress-Left>",
                  lambda e,s=self: s.FixedRot('y',10))
        self.bind("<KeyPress-Right>",
                  lambda e,s=self: s.FixedRot('y',-10))

        # 1,3
        self.bind("<KeyPress-End>",
                  lambda e,s=self: s.FixedZoom(0.9))
        self.bind("<KeyPress-Next>",
                  lambda e,s=self: s.FixedZoom(1.1))


        self.bind("<Enter>",
                  lambda e,s=self: s.Enter(e.x,e.y))
        self.bind("<Leave>",
                  lambda e,s=self: s.Leave(e.x,e.y))
        self.bind("<Expose>",
                  lambda e,s=self: s.Expose())

            
    def ResetToFit(self,x,y):
        """ Try and show all the visible actors"""
        if self._CurrentRenderer:
            self._CurrentRenderer.ResetCamera()
            
        self.Render()

    def firstrenderer(self):
        renderers = self._RenderWindow.GetRenderers()
        numRenderers = renderers.GetNumberOfItems()
        #print 'numrenderers',numRenderers
        self._CurrentRenderer = None
        renderers.InitTraversal()
        #for i in range(0,numRenderers):
        self._CurrentRenderer = renderers.GetNextItem()

    def SetCamera(self,x,y,z):
        self.camera_x = x
        self.camera_y = y
        self.camera_z = z

    def SetNearClippingPlane(self,near):
        self.near = near

    def SetFarClippingPlane(self,far):
        self.far = far
    
    def RotateZ(self,x,y):
        if self._CurrentRenderer:
            
            self._CurrentCamera.Roll(self._LastX - x)
            #self._CurrentCamera.Elevation(y - self._LastY)
            self._CurrentCamera.OrthogonalizeViewUp()
            
            self._LastX = x
            #self._LastY = y
            
            self._CurrentRenderer.ResetCameraClippingRange()
            self.Render()

    def FixedRot(self,axis,amount):

        #print 'FixedRot',axis,amount
        
        if self._CurrentRenderer:
            if axis == 'z':
                self._CurrentCamera.Roll(amount)
            elif axis == 'y':
                self._CurrentCamera.Azimuth(amount)
            elif axis == 'x':
                self._CurrentCamera.Elevation(amount)

            self._CurrentCamera.OrthogonalizeViewUp()
            self._CurrentRenderer.ResetCameraClippingRange()
            self.Render()

    def FixedZoom(self,zoomFactor):
        if self._CurrentRenderer:

            renderer = self._CurrentRenderer
            camera = self._CurrentCamera

            
            self._CurrentZoom = self._CurrentZoom * zoomFactor

            if camera.GetParallelProjection():
                parallelScale = camera.GetParallelScale()/zoomFactor
                camera.SetParallelScale(parallelScale)
            else:
                camera.Dolly(zoomFactor)
                renderer.ResetCameraClippingRange()

            self.Render()

    def SetOrigin(self,x,y,z):
        """ Define the new origin for rotation, also gives the appearance
            of a translation to put the new origin at the centre """

        if self._CurrentRenderer:
            camera = self._CurrentCamera
            (pPoint0,pPoint1,pPoint2) = camera.GetPosition()
            (fPoint0,fPoint1,fPoint2) = camera.GetFocalPoint()

            camera.SetFocalPoint((x,y,z))
            camera.SetPosition((x + pPoint0 - fPoint0,
                                y + pPoint1 - fPoint1,
                                z + pPoint2 - fPoint2))

            #self._CurrentRenderer.ResetCamera(x-0.1,x+0.1,
            #y-0.1,y+0.1,
            #z-0.1,z+0.1)
        self.Render()
