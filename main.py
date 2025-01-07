import tkinter as tk
from pixelcanvas import PixelCanvas
from drawtree import Tree

#define background hex colour
blue = '#56B3F7'
def driver(root,tree,timestep,anistep,duration,ctime):
  ctime += timestep
  for _ in range(anistep):
    tree.tick(1)
  tree.render()
  if ctime + timestep <= duration:
    root.after(timestep*1000, driver,root,tree,timestep,anistep,duration,ctime)

root = tk.Tk()
screenscaling = 30
pixscaling = 25
root.geometry(f'{9*screenscaling}x{16*screenscaling}')
root.title('Prodtree')
treecanvas = PixelCanvas(root,pixscaling*9,pixscaling*16,13,bg = blue)
'''treecanvas.writeoutline([(10,0),[(10,10),(10,0),(0,0)]],'red')
treecanvas.render()'''
tree1 = Tree(treecanvas)
driver(root,tree1,1,30,600,0)
'''for _ in range(5000):
  tree1.tick(1)
tree1.render()'''
root.mainloop()

