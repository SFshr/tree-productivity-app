import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image as im, ImageTk
import random
from pixelcanvas import PixelCanvas
from cwidgets import *

class Mainscreen(cFrame):
  def __init__(self,parent,controller):
    super().__init__(controller, parent)
    self.controller = controller
    self.treepicturesf = 5
    self.tk_treepictures = {}
    self.treebuttonframe = {}
    self.newtreeicon = None
    self.treegridwidth = 3
    #focus time is in minutes
    self.min_focustime = 2
    self.max_focustime = 6 * 60
    #frame for all the tree buttons
    self.treeframe = cFrame(self.controller, self)
    self.treeframe.pack(side="top", fill="both", expand=True)
    #frame for time slider and edit button
    self.controlframe = cFrame( self.controller, self)
    self.controlframe.pack(side="bottom", fill="x", expand=False)
    #treebuttons
    for placeindex,treeindex in enumerate(self.controller.treepicturedict.keys()):
      ygrid,xgrid = divmod(placeindex,self.treegridwidth)
      self.addtreebutton(treeindex,xgrid,ygrid)
    self.timeslider = cSlider(self.controller, self.controlframe, from_=self.min_focustime, to=self.max_focustime, command = self._updatetimelabel, value = self.controller.focustimepreset ,orient="horizontal",length = 200)
    self.timeslider.pack(side="bottom", pady = 10)
    self.timelabel = cLabel(self.controller,self.controlframe)
    self.timelabel.pack(side="bottom")
    self.editbutton = cButton(self.controller, self.controlframe, text = 'edit', command = self._edittrees)
    self.editbutton.pack()
    self._updatetimelabel(self.controller.focustimepreset)

  def _edittrees(self):
    self.editbutton.config(text = 'done', command = self._stoptreeedit)
    if not self.newtreeicon:
      newtreeicon = im.open(self.controller.newtreeiconfile)
      newtreeicon = newtreeicon.resize((self.controller.initialcanvaspixdims[0]*self.treepicturesf,self.controller.initialcanvaspixdims[1]*self.treepicturesf),im.NEAREST)
      self.newtreeicon = ImageTk.PhotoImage(newtreeicon)
    ygrid,xgrid = divmod(len(self.treebuttonframe),self.treegridwidth)
    self.addtreebuttonframe = self._addoptionbutton(self.newtreeicon,'new tree',self._newtreebuttonfunc,xgrid,ygrid)

  def _stoptreeedit(self):
    self.editbutton.config(text = 'edit', command = self._edittrees)
    self.addtreebuttonframe.destroy()

  def _newtreebuttonfunc(self):
    self.controller.screendict['Maketreescreen'].inputnewtree()
    self.controller.show_screen('Maketreescreen')
    self._stoptreeedit()

  def _updatetimelabel(self,time):
    hours,minutes = divmod(int(float(time)),60)
    self.timelabel.config(text = f'{hours} hours {minutes} minutes')

  def addnewtreebutton(self,treeindex):
    ygrid,xgrid = divmod(len(self.treebuttonframe),self.treegridwidth)
    self.addtreebutton(treeindex,xgrid,ygrid)

  def addtreebutton(self,treeindex,xgrid,ygrid):
    tkpicture = self._gettkpicture(treeindex)
    self.tk_treepictures[treeindex] = tkpicture
    treename = self.controller.treedatadict[treeindex][0]
    buttonframe = self._addoptionbutton(tkpicture,treename,self._returntreeclick(treeindex),xgrid,ygrid)
    self.treebuttonframe[treeindex] = buttonframe
  
  def _addoptionbutton(self,tkpicture,treename,onbuttonclick,xgrid,ygrid):
    buttonframe = cFrame(self.controller, self.treeframe)
    buttonframe.grid(row = ygrid, column = xgrid, padx = 5, pady = 5)
    treebutton = cButton(self.controller, buttonframe, image = tkpicture, command = onbuttonclick)
    treebutton.pack()
    namelabel = cLabel(self.controller,buttonframe,text = treename)
    namelabel.pack()
    return buttonframe

  def updatetreebutton(self,treeindex):
    tkpicture = self._gettkpicture(treeindex)
    self.tk_treepictures[treeindex] = tkpicture
    self.treebuttonframe[treeindex].children['!cbutton'].config(image=tkpicture)

  def deletetreebutton(self,treeindex):
    self.treebuttonframe[treeindex].destroy()
    del self.treebuttonframe[treeindex]
    del self.tk_treepictures[treeindex]

  def _gettkpicture(self,treeindex):
    treepicture,_ = self.controller.treepicturedict[treeindex]
    treepicture = treepicture.resize((self.controller.initialcanvaspixdims[0]*self.treepicturesf,self.controller.initialcanvaspixdims[1]*self.treepicturesf),im.NEAREST)
    return ImageTk.PhotoImage(treepicture)
  
  
#returns function which starts focus session for tree corresponding to index
  def _returntreeclick(self,index):
    def func():
      focustime = int(self.timeslider.get())
      self.controller.focustimepreset = focustime
      self.controller.screendict['Focusscreen'].focus(index,focustime)
      self.controller.show_screen('Focusscreen')
    return func
  
class Focusscreen(cFrame):
  def __init__(self,parent,controller):
    super().__init__(controller, parent)
    #length of time between frames for simulation and animation
    self.simstep = 1
    self.timestep = 1
    self.controller = controller
    self.nowfocused = False
    pixlen = 20
    self.canvas = PixelCanvas(self,self.controller.initialcanvaspixdims[0]*pixlen,self.controller.initialcanvaspixdims[1]*pixlen,pixlen,bg = self.controller.skycol)
    self.canvas.pack()
    self.timeleftlabel = cLabel(self.controller, self, fontindex = 3)
    self.timeleftlabel.pack()
    self.stopbutton = cButton(self.controller,self, text = 'Stop early', command=self._stopearly)
    self.stopbutton.pack()

  def _stopearly(self):
    result = messagebox.askyesno(message = 'Your progress will not be saved. Are you sure you want to stop?')
    if result:
      self.premature_endfocus()

#time measured in minutes, self.timeleft in seconds
  def focus(self,treeindex,time):
    self.timeleft = time * 60
    #FOR TESTING
    self.timeleft = 5
    self.ctreeindex = treeindex
    self.ctree = self.controller.fetchtree(treeindex)
    self.ctree.savestate()
    self.nowfocused = True
    self._driver()
 
  def _endfocus(self):
    self.ctree.render(self.canvas)
    image = self.canvas.renderimage()
    self.controller.changetreepicture(self.ctreeindex,image)
    self.nowfocused = False
    self.controller.show_screen('Mainscreen')
  
  def premature_endfocus(self):
    self.ctree.recoverstate()
    self.nowfocused = False
    self.controller.show_screen('Mainscreen')

  def _driver(self):
    if self.nowfocused:
      for _ in range(self.simstep):
        self.ctree.tick(1)
      self.ctree.render(self.canvas)
      self.canvas.render()
      minsleft,seconds = divmod(self.timeleft,60)
      hoursleft,minsleft = divmod(minsleft,60)
      self.timeleftlabel.config(text = str(hoursleft).zfill(2) + ':' + str(minsleft).zfill(2) + ':' + str(seconds).zfill(2))
      if self.timeleft > 0:
        self.timeleft -= self.timestep
        self.controller.after(self.timestep*1000, self._driver)
      else:
        self._endfocus()

class Maketreescreen(cFrame):
  def __init__(self,parent,controller):
    super().__init__(controller, parent)
    self.controller = controller
    self.newtreeintro = cMessage(self.controller, self, fontindex = 2, width = self.controller.screenwidth, justify = 'left')
    self.newtreeintro.pack()
    self.newtreemessage = cMessage(self.controller, self, width = self.controller.screenwidth, justify = 'left')
    self.newtreemessage.pack()
    self.subjectboxlabel = cMessage(self.controller, self, width = self.controller.screenwidth, justify = 'center')
    self.subjectboxlabel.pack()
    self.subjectbox = cEntry(self.controller, self, width = 10)
    self.subjectbox.pack()
    self.nosubjectlabel = cLabel(self.controller, self, fontindex = 0, fg = 'red')
    self.nosubjectlabel.pack()
    self.quotaboxlabel = cMessage(self.controller, self, width = self.controller.screenwidth, justify = 'center')
    self.quotaboxlabel.pack()
    self.quotabox = cEntry(self.controller, self, width = 10)
    self.quotabox.pack()
    self.notnumberlabel = cLabel(self.controller, self, fontindex = 0, fg = 'red')
    self.notnumberlabel.pack()
    self.enterbutton = cButton(self.controller, self, text = 'create', command=self._finishinputtree)
    self.enterbutton.pack()
    self.treenameoptions = None


  def inputnewtree(self):
    if not self.treenameoptions:
      with open(self.controller.treenamesfile) as f:
        self.treenameoptions = [w.strip() for w in f.readlines()]
    self.treename = random.choice(self.treenameoptions)
    self.newtreeintro.config(text = f'Say hello to {self.treename}!')
    self.newtreemessage.config(text = f'a tulip tree from North America, {self.treename} will grow taller and stronger every focus session — reminding you that steady effort leads to great growth!\n')
    self.subjectboxlabel.config(text = f'Subject {self.treename} will help you study:')
    self.quotaboxlabel.config(text = f'Weekly hours you want to spend growing {self.treename}:')

  def _finishinputtree(self):
    subject = self.subjectbox.get()
    timequota = self.quotabox.get()
    correctinput = True
    if not timequota.replace('.', '', 1).isdigit():
      self.notnumberlabel.config(text = 'Enter a number')
      correctinput = False
    else:
      self.notnumberlabel.config(text = '')
    if not subject:
      self.nosubjectlabel.config(text = 'Enter a subject')
      correctinput = False
    else:
      self.nosubjectlabel.config(text = '')
    if correctinput:
      timequota = float(timequota)
      self.controller.makenewtree(self.treename,subject,int(timequota*60))
      self.controller.show_screen('Mainscreen')
 
      