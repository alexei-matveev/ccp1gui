"""
A utility to wrap up the PlotCanvas widget from Scientific Python
"""
from Tkinter import *
from Scientific.TkWidgets.TkPlotCanvas import *
import Numeric


t=['red','orange','yellow','green','blue','violet','black']
lincol=[];
for i in range(0,10):
    lincol=lincol+t
markcol=lincol


def Plot2D(stuff):
    window = Frame()
    window.pack(fill=BOTH, expand=YES)

    def select(value):
        c.select(value)

    def display(value):
        select(value)
        print value

    c = PlotCanvas(window, "300", "200", relief=SUNKEN, border=2,
                   zoom = 1, select = display)
    c.pack(side=TOP, fill=BOTH, expand=YES)
    object = PlotGraphics(stuff)
    #Button(window, text='Draw', command=lambda o=object:
    #       c.draw(o, 'automatic', 'automatic')).pack(side=LEFT)
    Button(window, text='PostScript', command=lambda canv=c : canv.canvas.postscript(file='plot.ps')).pack(side=LEFT)
    Button(window, text='Redraw', command=c.redraw).pack(side=LEFT)
    Button(window, text='Quit', command=window.quit).pack(side=RIGHT)
    c.draw(object, 'automatic', 'automatic')
    window.mainloop()




if __name__ == '__main__':

    data1 = 2.*Numeric.pi*Numeric.arange(200)/200.
    data1.shape = (100, 2)
    data1[:,1] = Numeric.sin(data1[:,0])
    lines1 = PolyLine(data1, color='green')
    pi = Numeric.pi
    lines2 = PolyLine([(0., 0.), (pi/2., 1.), (pi, 0.), (3.*pi/2., -1),
                       (2.*pi, 0.)], color='red')

    markers = PolyMarker([(0., 0.), (pi/2., 1.), (pi, 0.), (3.*pi/2., -1),
                          (2.*pi, 0.)], color='blue', fillcolor='blue', 
                         marker='triangle')

    Plot2D([lines1, lines2, markers])

