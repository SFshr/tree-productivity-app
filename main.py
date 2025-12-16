import tkinter as tk
import pickle
import json
import os
from PIL import Image as im
from tkinter import font
from datetime import datetime,timedelta
import ctypes

from drawtree import Tree
from screens import *
from pixelcanvas import PixelCanvas

#needed to change checkinday to today
class App(tk.Tk):
  def __init__(self, *args,**kwargs):
    tk.Tk.__init__(self, *args, **kwargs)
    self.checkinday = 2
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
    self.font_col = 'white'
    self.highlight_col = '#F1DAC4'
    self.skycol ='#56B3F7'
    #files and folders needed in this project:
    self.appfoldername = 'appdata'
    self.treenamesfile = 'assets/treenames.txt'
    self.newtreeiconfile = 'assets/addtreeicon.png'
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
          #notiftimes contains lists with 4 elements - day of week,hours,minutes,tree
          #notiftimes is chronologically sorted
          #week indexed from 0 on monday
          self.notiftimes = appstate['notiftimes']
          #focustimes is dictionary indexed by date DD-MM-YYYY, values are dictonary indexed by treeindex with values of number of minutes studied that day (float)
          self.focustimes = appstate['focustimes']
          #streak is 2-element list with date string of last day app has been used and integer for how many days in a row the app has been used
          self.streak = appstate['streak']
          yesterday = datetime.now() - timedelta(days = 1)
          if self.streak[0] == yesterday.strftime("%d-%m-%Y"):
            self.streak[1] += 1
          elif self.streak[0] != datetime.now().strftime("%d-%m-%Y"):
            self.streak[1] = 1
          self.streak[0] = datetime.now().strftime("%d-%m-%Y")
      except:
        raise FileNotFoundError('app data could not be accessed')
    else:
      newuser = True
      os.makedirs(self.appfoldername)
      self.treedatadict = {}
      self.focustimepreset = 5
      self.notiftimes = []
      self.focustimes = {}
      self.streak = [datetime.now().strftime("%d-%m-%Y"),1]
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
    screenclasses = [Focusscreen,Mainscreen,Maketreescreen,Newreminderscreen,Notifscreen,Checkinscreen]
    self.screendict = {}
    for screenclass in screenclasses:
      screen = screenclass(container,self)
      self.screendict[screenclass.__name__] = screen
      screen.grid(row=0,column=0,sticky="nsew")
    #save data when program is closed:
    self.protocol("WM_DELETE_WINDOW", self._on_shutdown)
    if newuser:
      self.screendict['Maketreescreen'].inputnewtree()
      self.show_screen('Maketreescreen')
    else:
      self.show_screen('Mainscreen')

  def notifdriver(self):
    now = datetime.now()
    for notif in self.notiftimes:
      if notif[0] == now.weekday() and notif[1] == now.hour and notif[2] == now.minute:
        self.notifier.send(title = 'Study!', message = f'Reminder to grow {notif[3]}')
    self.after(1000*60,self.notifdriver)
  #time in minutes
  def addfocustime(self,index,time):
    datekey = datetime.now().strftime("%d-%m-%Y")
    if datekey in self.focustimes.keys():
      if index in self.focustimes[datekey].keys():
        self.focustimes[datekey][index] += time
      else:
        self.focustimes[datekey][index] = time
    else:
      self.focustimes[datekey] = {index:time}
  
  def focustimeday(self,dateob,index):
    datekey = dateob.strftime("%d-%m-%Y")
    if datekey in self.focustimes.keys():
      if index in self.focustimes[datekey].keys():
        return self.focustimes[datekey][index]
    return 0
  
  #returns minutes studied since last checkin
  def focustimeweek(self,dateob,index):
    checkin_before = dateob - timedelta(days=(dateob.weekday() + 7 - self.checkinday) % 7)
    focustotal = 0
    while checkin_before <= dateob:
      focustotal += self.focustimeday(checkin_before,index)
      checkin_before += timedelta(days=1)
    return focustotal

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
      appdata = {'treedatadict':self.treedatadict,'focustimepreset':self.focustimepreset, 'notiftimes':self.notiftimes, 'focustimes':self.focustimes, 'streak':self.streak}
      with open(self.statefname,'w') as f:
        json.dump(appdata,f,indent=4)
    except:
      error = TypeError('could not save app data in json')
    return error

if __name__ == '__main__':
  try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
  except:
    pass
  app = App()
  app.mainloop()
