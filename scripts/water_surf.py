# experiment in scripting GAMESS-UK calculations
#
# notes
#
# - I had to hack the energy in from the outputreader to an attribute of calc
#   need a better way to (request&) hold results.. for example matrices from punchfile
#
#  - the codes habit of writing the resulting structure back over its input
#   is rather unexpected, especially as it comes back in cartesian coordinates,
#   we can solve this by creating a new structure each time
#
# run gamess-UK (foreground)
#
from interfaces.gamessuk import GAMESSUKCalc
from objects.zmatrix import Zmatrix, ZAtom

zm = [ "zmatrix angstrom",
       "o",
       "h 1 oh",
       "h 1 oh 2 hoh",
       "variables",
       "oh 1",
       "hoh 100"]

calc = GAMESSUKCalc()
calc.set_parameter('charge',0)
calc.set_parameter('job_name','water')

x = []
y = []
for angle in range(80,140,2):

    model=Zmatrix(list=zm)
    calc.set_input('mol_obj',model)
    v = model.find_var("hoh")
    v.value = angle
    model.calculate_coordinates()
    job = calc.makejob()
    if job:
        job.run()
        job.tidy()
        x.append(angle)
        y.append(calc.final_energy)


# ---------------------- HelloWorld2.py ----------------------
# 
# This program demonstrates the most basic methods in the
# BLT Graph package. If you want to develop your own 
# program, this example might be a good starting point.
# 

from Tkinter import *        # The Tk package
import Pmw                   # The Python MegaWidget package
import sys
master = Tk()                # make a Tk root window

mystack=[]

def zoom(x0, y0, x1, y1):
    g.xaxis_configure(min=x0, max=x1)
    g.yaxis_configure(min=y0, max=y1)
    
def mouseDrag(event):
    global x0, y0, x1, y1
    (x1, y1) = g.invtransform(event.x, event.y)
         
    g.marker_configure("marking rectangle", 
        coords = (x0, y0, x1, y0, x1, y1, x0, y1, x0, y0))
    
def mouseUp(event):
    global dragging
    global x0, y0, x1, y1
    
    if dragging:
        g.unbind(sequence="<Motion>")
        g.marker_delete("marking rectangle")
        
        if x0 <> x1 and y0 <> y1:

            # make sure the coordinates are sorted
            if x0 > x1: x0, x1 = x1, x0
            if y0 > y1: y0, y1 = y1, y0
     
            if event.num == 1:
               #print 'append',(x0,y0,x1,y1)
               mystack.append((x0,y0,x1,y1))
               zoom(x0, y0, x1, y1) # zoom in
            else:
               (X0, X1) = g.xaxis_limits()
               k  = (X1-X0)/(x1-x0)
               x0 = X0 -(x0-X0)*k
               x1 = X1 +(X1-x1)*k
               
               (Y0, Y1) = g.yaxis_limits()
               k  = (Y1-Y0)/(y1-y0)
               y0 = Y0 -(y0-Y0)*k
               y1 = Y1 +(Y1-y1)*k

               try:
                   x0,y0,x1,y1 = mystack.pop()
                   #print 'popped',(x0,y0,x1,y1)
                   x0,y0,x1,y1 = mystack.pop()
                   #print 'popped',(x0,y0,x1,y1)
                   zoom(x0, y0, x1, y1) # zoom out
               except IndexError:
                   pass
               
def mouseDown(event):
    global dragging, x0, y0
    dragging = 0
    
    if g.inside(event.x, event.y):
        dragging = 1
        (x0, y0) = g.invtransform(event.x, event.y)
        
        g.marker_create("line", name="marking rectangle", dashes=(2, 2))
        g.bind(sequence="<Motion>",  func=mouseDrag)

        if event.num == 1:
            (tx0, tx1) = g.xaxis_limits()
            (ty0, ty1) = g.yaxis_limits()
            #print 'append',(tx0,ty0,tx1,ty1)
            mystack.append((tx0,ty0,tx1,ty1))


if not Pmw.Blt.haveblt(master):     # is Blt installed?
   print("BLT is not installed!")

else:

   npoints = 0
   ncurves = 0             
   vector_x = []  # vector for the x values in the curves
   vector_y = []  # vector of vectors
   caption = []
   color = ['red', '#ff9900', 'blue', '#00cc00', 'black', 'grey']

   #-------------------------------------
   ncurves = 1
   vector_y.append([])
   caption.append("HF energy")
   title="angle bend potential"
   vector_x = x
   vector_y[0] = y
   #-------------------------------------

   
   g = Pmw.Blt.Graph(master)                     # make a new graph area
   g.pack(expand=1, fill='both')

   for c in range(ncurves):                      # for each curve...
      curvename = caption[c]                     # make a curvename
      g.line_create(curvename,                   # and create the graph
                    xdata=tuple(vector_x),       # with x-data,
                    ydata=tuple(vector_y[c]),    # and  y-data
                    color=color[c],             # and a nice color
                    symbol='')                   # ...and no markers

   g.bind(sequence="<ButtonPress>",   func=mouseDown)
   g.bind(sequence="<ButtonRelease>", func=mouseUp  )

   g.configure(title=title) # enter a title

   (X0, X1) = g.xaxis_limits()
   (Y0, Y1) = g.yaxis_limits()
   mystack.append((X0,Y0,X1,Y1))
   master.mainloop()                             # ...and wait for input

