import tkinter as tk
from pixelcanvas import PixelCanvas
from drawtree import Tree

#define hex colours for tree
blue = '#56B3F7'
brown = '#8B6545'
green = '#078700'
def driver(root,tree,timestep,anistep,duration,colour,ctime):
  ctime += timestep
  for _ in range(anistep):
    tree.tick(1)
  tree.render()
  if ctime + timestep <= duration:
    root.after(timestep*1000, driver,root,tree,timestep,anistep,duration,colour,ctime)

root = tk.Tk()
screenscaling = 30
pixscaling = 25
root.geometry(f'{9*screenscaling}x{16*screenscaling}')
root.title('Prodtree')
treecanvas = PixelCanvas(root,pixscaling*9,pixscaling*16,13,bg = blue)
tree1 = Tree(treecanvas)
driver(root,tree1,1,30,600,brown,0)
'''for _ in range(500):
  tree1.tick(1)
tree1.render()'''
root.mainloop()