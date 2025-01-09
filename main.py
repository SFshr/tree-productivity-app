import tkinter as tk
import pickle
import json
import os
from PIL import Image as im, ImageTk

from pixelcanvas import PixelCanvas
from drawtree import Tree

class App(tk.Tk):
  def __init__(self, *args,**kwargs):
    tk.Tk.__init__(self, *args, **kwargs)
    #window:
    screenscaling = 30
    self.geometry(f'{9*screenscaling}x{16*screenscaling}')
    self.title('Prodtree')
    #tree stuff:
    self.appfoldername = 'appdata'
    self.statefname = os.path.join(self.appfoldername,'appstate.json')
    if os.path.exists(self.appfoldername):
      newuser = False
      try:
        with open(self.statefname, 'r') as f:
          appstate = json.load(f)
          self.alltrees = appstate['alltrees']
      except:
        raise FileNotFoundError('appdata folder did not have app state file inside')
    else:
      newuser = True
      os.makedirs(self.appfoldername)
      self.alltrees = []
    self.blue ='#56B3F7'
    #treedict,treepicturedict keys are integerss
    #treepicturedict stores tuple with PIL photoimage objects of tree states and a flag to say if they have been changed this session or not
    self.treepicturedict = {i:(im.open(self._treepicturefilescheme(i)),False) for i in self.alltrees}
    #treedict stores tree objects brought into memory
    self.treedict = {}
    self.initialcanvaspixdims = (17,30) #holds number of pixels long and high pixel canvas is for tree just created
    #manage screens:
    #container holds all screens
    container = tk.Frame(self)
    container.pack(side="top", fill="both", expand=True)
    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)
    screenclasses = [Focusscreen,Mainscreen]
    self.screendict = {}
    for screenclass in screenclasses:
      screen = screenclass(container,self)
      self.screendict[screenclass.__name__] = screen
      screen.grid(row=0,column=0,sticky="nsew")
    self.show_screen('Mainscreen')
    #save data when program is closed:
    self.protocol("WM_DELETE_WINDOW", self._on_shutdown)
  
  #need to create setter functions for treepicturedict so that we can change main screen button pictures when trees change
  def changetreepicture(self,index,newpicture):
    self.treepicturedict[index] = (newpicture,True)
    self.screendict['Mainscreen'].updatetreebutton(index)

  def deletetreepicture(self,index):
    del self.treepicturedict[index]
    self.screendict['Mainscreen'].deletetreebutton(index)

  def addtreepicture(self,index,newpicture):
    self.treepicturedict[index] = (newpicture,True)
    self.screendict['Mainscreen'].addtreebutton(index)

  def _treefilescheme(self,index):
    return os.path.join(self.appfoldername,f'tree-{index}.pkl')
  
  def _treepicturefilescheme(self,index):
    return os.path.join(self.appfoldername,f'treesnapshot-{index}.png')
  
  def show_screen(self,name):
    self.screendict[name].tkraise()
  
  def savetree(self,treeindex):
    fname = self._treefilescheme(treeindex)
    try:
      with open(fname,'wb') as treefile:
        pickle.dump(self.treedict[treeindex],treefile)
      return None
    except:
       return TypeError('Tree type cannot be pickled')
    
  def treefromfile(self,treeindex):
    fname = self._treefilescheme(treeindex)
    try:
      with open(fname,'rb') as treefile:
        self.treedict[treeindex] = pickle.load(treefile)
    except FileNotFoundError:
      raise RuntimeError('Attempted to fetch nonexistent tree')
    
  #if tree object in memory return, else bring it into memory
  def fetchtree(self,treeindex):
    if treeindex not in self.treedict.keys():
      self.treefromfile(treeindex)
    return self.treedict[treeindex]
    
  def makenewtree(self):
    if self.alltrees:
      treeindex = max(self.alltrees) + 1
    else:
      treeindex = 0
    newtree = Tree()
    self.treedict[treeindex] = newtree
    self.alltrees.append(treeindex)
    canvas = PixelCanvas(self,*self.initialcanvaspixdims,1,bg = self.blue)
    newtree.render(canvas)
    image = canvas.renderimage()
    self.addtreepicture(treeindex,image)

  def deletetree(self,treeindex):
    try:
      del self.treedict[treeindex]
    except:
      raise RuntimeError('No tree at index to delete')
    self.deletetreepicture(treeindex)
    self.alltrees.remove(treeindex)
    os.remove(self._treefilescheme(treeindex))
    os.remove(self._treepicturefilescheme(treeindex))

  def _on_shutdown(self):
    error = self.savesession()
    self.destroy()
    if error:
      raise error

  def savesession(self):
    error = None
    for treeindex in self.treedict.keys():
      perror = self.savetree(treeindex)
      if perror:
        error = error
    try:
      for treeindex,(treepicture,changeflag) in self.treepicturedict.items():
        if changeflag:
          treepicture.save(self._treepicturefilescheme(treeindex))
    except:
      error = TypeError('could not save tree image objects')
    try:
      appdata = {'alltrees':self.alltrees}
      with open(self.statefname,'w') as f:
        json.dump(appdata,f,indent=4)
    except:
      error = TypeError('could not save app data in json')
    return error

class Mainscreen(tk.Frame):
  def __init__(self,parent,controller):
    tk.Frame.__init__(self, parent)
    self.controller = controller
    self.treepicturesf = 6
    self.tk_treepictures = {}
    self.treebuttons = {}
    self.focustime = 0
    for treeindex in self.controller.treepicturedict.keys():
      self.addtreebutton(treeindex)

  def addtreebutton(self,treeindex):
    tkpicture = self._gettkpicture(treeindex)
    self.tk_treepictures[treeindex] = tkpicture
    treebutton = tk.Button(self, image=tkpicture, command=self._returntreeclick(treeindex))
    treebutton.pack()
    self.treebuttons[treeindex] = treebutton
  
  def updatetreebutton(self,treeindex):
    tkpicture = self._gettkpicture(treeindex)
    self.tk_treepictures[treeindex] = tkpicture
    self.treebuttons[treeindex].config(image=tkpicture)

  def deletetreebutton(self,treeindex):
    self.treebuttons[treeindex].destroy()
    del self.treebuttons[treeindex]
    del self.tk_treepictures[treeindex]
    
  def _gettkpicture(self,treeindex):
    treepicture,_ = self.controller.treepicturedict[treeindex]
    treepicture.resize((self.controller.initialcanvaspixdims[0]*self.treepicturesf,self.controller.initialcanvaspixdims[1]*self.treepicturesf),im.NEAREST)
    return ImageTk.PhotoImage(treepicture)
  
#returns function which starts focus session for tree corresponding to index
  def _returntreeclick(self,index):
    def func():
      self.controller.screendict['Focusscreen'].focus(index,self.focustime)
      self.controller.show_screen('Focusscreen')
    return func
  
class Focusscreen(tk.Frame):
  def __init__(self,parent,controller):
    tk.Frame.__init__(self, parent)
    
    #length of time between frames for simulation and animation
    self.simstep = 30
    self.timestep = 1
    self.controller = controller
    self.canvas = PixelCanvas(self,self.controller.initialcanvaspixdims[0]*13,self.controller.initialcanvaspixdims[1]*13,13,bg = self.controller.blue)
    self.canvas.pack()

#time measured in seconds
  def focus(self,treeindex,time):
    self.timeleft = time
    self.ctreeindex = treeindex
    self.ctree = self.controller.fetchtree(treeindex)
    self._driver()
  
  def _endfocus(self):
    self.ctree.render(self.canvas)
    image = self.canvas.renderimage()
    self.controller.treepicturedict[self.ctreeindex] = (image,True)

  def _driver(self):
    for _ in range(self.simstep):
      self.ctree.tick(1)
    self.ctree.render(self.canvas)
    self.canvas.render()
    if self.timeleft >= 0:
      self.timeleft -= self.timestep
      self.controller.after(self.timestep*1000, self._driver)
    else:
      self._endfocus()

if __name__ == '__main__':
  app = App()
  app.mainloop()