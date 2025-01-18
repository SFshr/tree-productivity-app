import tkinter as tk
import pickle
import json
import os
from PIL import Image as im
from tkinter import font
from pixelcanvas import PixelCanvas
from drawtree import Tree
from screens import Mainscreen,Focusscreen,Maketreescreen

#also going to move screen classes into a seperate file called screens to make the codebase easier to navigate
class App(tk.Tk):
  def __init__(self, *args,**kwargs):
    tk.Tk.__init__(self, *args, **kwargs)
    #window:
    screenscaling = 30
    self.geometry(f'{9*screenscaling}x{16*screenscaling}')
    self.screenwidth = 9*screenscaling
    self.screenheight = 16*screenscaling
    self.title('Prodtree')
    #overall styling:
    fontsize_list = [10,14,20,45]
    self.default_fontindex = 1
    self.fontlist = [font.Font(family="DejaVu Sans Mono", size = size) for size in fontsize_list]
    self.background_col = '#161B33'
    self.background_inset_col = '#0D0C1D'
    self.font_col = 'white'#'#F1DAC4'
    self.skycol ='#56B3F7'
    #files and folders needed in this project:
    self.appfoldername = 'appdata'
    self.treenamesfile = 'treenames.txt'
    self.newtreeiconfile = 'addtreeicon.png'
    self.statefname = os.path.join(self.appfoldername,'appstate.json')
    #tree stuff:
    if os.path.exists(self.appfoldername):
      newuser = False
      try:
        with open(self.statefname, 'r') as f:
          appstate = json.load(f)
          #treedatadict values are [tree name, tree subject, time quota] with time quota measured in minutes
          self.treedatadict = appstate['treedatadict']
          self.focustimepreset = appstate['focustimepreset']
      except:
        raise FileNotFoundError('appdata could not be accessed')
    else:
      newuser = True
      os.makedirs(self.appfoldername)
      self.treedatadict = {}
      self.focustimepreset = 5
   
    #treedict,treepicturedict keys are integerss
    #treepicturedict stores tuple with PIL photoimage objects of tree states and a flag to say if they have been changed this session or not
    self.treepicturedict = {i:(im.open(self._treepicturefilescheme(i)),False) for i in self.treedatadict.keys()}
    #treedict stores tree objects brought into memory
    self.treedict = {}
    self.initialcanvaspixdims = (9,16) #holds number of pixels long and high pixel canvas is for tree just created
    #manage screens:
    #container holds all screens
    container = tk.Frame(self)
    container.pack(side="top", fill="both", expand=True)
    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)
    screenclasses = [Focusscreen,Mainscreen,Maketreescreen]
    self.screendict = {}
    for screenclass in screenclasses:
      screen = screenclass(container,self)
      self.screendict[screenclass.__name__] = screen
      screen.grid(row=0,column=0,sticky="nsew")
    self.show_screen('Mainscreen')
    #save data when program is closed:
    self.protocol("WM_DELETE_WINDOW", self._on_shutdown)
    if newuser:
      self.screendict['Maketreescreen'].inputnewtree()
      self.show_screen('Maketreescreen')
    else:
      self.show_screen('Mainscreen')

#edit button does not make the new tree icon appear, cannot start focus session now
#make background dark blue to make sure you can see the white edit button
  #need to create setter functions for treepicturedict so that we can change main screen button pictures when trees change
  def changetreepicture(self,index,newpicture):
    self.treepicturedict[index] = (newpicture,True)
    self.screendict['Mainscreen'].updatetreebutton(index)

  def deletetreepicture(self,index):
    del self.treepicturedict[index]
    self.screendict['Mainscreen'].deletetreebutton(index)

  def addtreepicture(self,index,newpicture):
    self.treepicturedict[index] = (newpicture,True)
    self.screendict['Mainscreen'].addnewtreebutton(index)

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
#when int converted to json and loaded back in maybe it becomes string?
  def makenewtree(self,treename,subject,quota):
    if self.treedatadict:
      treeindex = str(max([int(i) for i in self.treedatadict.keys()]) + 1)
    else:
      treeindex = 0
    newtree = Tree()
    self.treedict[treeindex] = newtree
    self.treedatadict[treeindex] = [treename,subject,quota]
    canvas = PixelCanvas(self,*self.initialcanvaspixdims,1,bg = self.skycol)
    newtree.render(canvas)
    image = canvas.renderimage()
    self.addtreepicture(treeindex,image)

  def deletetree(self,treeindex):
    try:
      del self.treedatadict[treeindex]
    except:
      raise RuntimeError('No tree at index to delete')
    self.deletetreepicture(treeindex)
    if treeindex in self.treedict.keys():
      del self.treedict[treeindex]
    os.remove(self._treefilescheme(treeindex))
    os.remove(self._treepicturefilescheme(treeindex))

  def _on_shutdown(self):
    if self.screendict['Focusscreen'].nowfocused:
      self.screendict['Focusscreen'].premature_endfocus()
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
      appdata = {'treedatadict':self.treedatadict,'focustimepreset':self.focustimepreset}
      with open(self.statefname,'w') as f:
        json.dump(appdata,f,indent=4)
    except:
      error = TypeError('could not save app data in json')
    return error

if __name__ == '__main__':
  app = App()
  app.mainloop()