#
try:
    global env
    gui = env.tkmol
except NameError:
    print 'Error: This script should be run from the GUI shell window'
    import sys
    sys.exit()

for v in gui.vis_list:
    v.Hide()
