"""
A utility to wrap up the PlotCanvas widget from Scientific Python
"""
import Tkinter
import Scientific.TkWidgets.TkPlotCanvas
import Numeric
import math


t=['red','orange','yellow','green','blue','violet','black']
lincol=[];
for i in range(0,10):
    lincol=lincol+t
markcol=lincol


def Plot2D(stuff):
    window = Tkinter.Frame()
    window.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)

    def select(value):
        c.select(value)

    def display(value):
        select(value)
        print value

    c = Scientific.TkWidgets.TkPlotCanvas.PlotCanvas(window, "300", "200", relief=Tkinter.SUNKEN, border=2,
                   zoom = 1, select = display)
    c.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, expand=Tkinter.YES)
    object = Scientific.TkWidgets.TkPlotCanvas.PlotGraphics(stuff)
    #Button(window, text='Draw', command=lambda o=object:
    #       c.draw(o, 'automatic', 'automatic')).pack(side=LEFT)
    Tkinter.Button(window, text='PostScript', command=lambda canv=c : canv.canvas.postscript(file='plot.ps')).pack(side=Tkinter.LEFT)
    Tkinter.Button(window, text='Redraw', command=c.redraw).pack(side=Tkinter.LEFT)
    Tkinter.Button(window, text='Quit', command=window.quit).pack(side=Tkinter.RIGHT)
    c.draw(object, 'automatic', 'automatic')
    window.mainloop()




if __name__ == '__main__':

    data1 = 2.*math.pi*Numeric.arange(200)/200.
    data1.shape = (100, 2)
    data1[:,1] = Numeric.sin(data1[:,0])
    lines1 = Scientific.TkWidgets.TkPlotCanvas.PolyLine(data1, color='green')
    pi = math.pi
    lines2 = Scientific.TkWidgets.TkPlotCanvas.PolyLine([(0., 0.), (pi/2., 1.), (pi, 0.), (3.*pi/2., -1),
                       (2.*pi, 0.)], color='red')

    markers = Scientific.TkWidgets.TkPlotCanvas.PolyMarker([(0., 0.), (pi/2., 1.), (pi, 0.), (3.*pi/2., -1),
                          (2.*pi, 0.)], color='blue', fillcolor='blue', 
                         marker='triangle')

    Plot2D([lines1, lines2, markers])

