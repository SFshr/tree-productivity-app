import tkinter as tk
from tkinter import messagebox
from PIL import Image as im, ImageTk
import random
import numpy as np
from bisect import insort,bisect_right
from datetime import datetime

from pixelcanvas import PixelCanvas, hextorgb
from cwidgets import *

class Mainscreen(cFrame):
  def __init__(self,parent,controller):
    super().__init__(controller, parent)
    self.controller = controller
    self.treepicturesf = 8
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
    self.controlframe = cFrame(self.controller, self)
    self.controlframe.pack(side="bottom", fill="x", expand=False,ipady = 10)
    #treebuttons
    for placeindex,treeindex in enumerate(self.controller.treepicturedict.keys()):
      ygrid,xgrid = divmod(placeindex,self.treegridwidth)
      self.addtreebutton(treeindex,xgrid,ygrid)
    self.timelabel = cLabel(self.controller,self.controlframe)
    self.timelabel.pack()
    self.timeslider = cSlider(self.controller, self.controlframe, from_=self.min_focustime, to=self.max_focustime, command = self._updatetimelabel, value = self.controller.focustimepreset ,orient="horizontal",length = 200)
    self.timeslider.pack(pady = 10)
    self.editbutton = cButton(self.controller, self.controlframe, text = 'edit', command = self._edittrees)
    self.editbutton.pack(side = tk.LEFT,padx = 10)
    self.notificationbutton = cButton(self.controller, self.controlframe, text = 'reminders', command = self. _changetonotifs)
    self.notificationbutton.pack(side = tk.RIGHT,padx = 10)
    self._updatetimelabel(self.controller.focustimepreset)

  def _changetonotifs(self):
    self.controller.show_screen('Notifscreen')

  def _edittrees(self):
    self.editbutton.config(text = 'done', command = self._stoptreeedit)
    if not self.newtreeicon:
      newtreeicon = im.open(self.controller.newtreeiconfile)
      newtreeicon = newtreeicon.resize((self.controller.initialcanvaspixdims[0]*self.treepicturesf,self.controller.initialcanvaspixdims[1]*self.treepicturesf),im.NEAREST)
      #if self.controller.background_col is not in the right format just use black background
      newtreeicon = newtreeicon.convert('RGBA')
      r,g,b = hextorgb(self.controller.background_col,(0,0,0))
      background = im.new('RGB', newtreeicon.size, (r,g,b,1))
      #composite background with foreground
      background.paste(newtreeicon, (0, 0), newtreeicon)
      self.newtreeicon = ImageTk.PhotoImage(background)
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

  #This should not be a problem as one of the button styling should show through
  def _addoptionbutton(self,tkpicture,treename,onbuttonclick,xgrid,ygrid):
    buttonframe = cFrame(self.controller, self.treeframe, height = 145, width = tkpicture.width())
    padx = (self.controller.screenwidth - self.treegridwidth * tkpicture.width())/(self.treegridwidth * 2)
    buttonframe.grid(row = ygrid, column = xgrid, padx = padx, pady = 10)
    treebutton = tk.Button(buttonframe, image = tkpicture, command = onbuttonclick, width = tkpicture.width() - 4, height = tkpicture.height() - 4)
    treebutton.pack()
    namelabel = cLabel(self.controller,buttonframe,text = treename)
    namelabel.pack()
    return buttonframe

  def updatetreebutton(self,treeindex):
    tkpicture = self._gettkpicture(treeindex)
    self.tk_treepictures[treeindex] = tkpicture
    self.treebuttonframe[treeindex].children['!button'].config(image=tkpicture)

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
    self.canvas.pack(pady = 30)
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

class Notifscreen(cFrame):
  def __init__(self,parent,controller):
    super().__init__(controller, parent)
    self.controller = controller
    #implement scrolling:
    self.scrolldowndist = 0
    self.scrollcanvas = tk.Canvas(self,bg = self.controller.background_inset_col,highlightthickness=0)
    self.scrollcanvas.pack(fill='both', expand = True)
    self.scrollframe = cFrame(self.controller, self.scrollcanvas,bg = self.controller.background_inset_col)
    self.scrollframe.bind("<Configure>", lambda _:self.scrollcanvas.configure(scrollregion=self.scrollcanvas.bbox("all")))
    self.scrollcanvas.create_window((0, 0), window=self.scrollframe, anchor="nw")
    self.scrollcanvas.bind_all("<MouseWheel>", self.on_mousewheel)
    self.deletedreminderindexes = []
    #frame for reminders
    #frame for back and new reminder button
    self.controlframe = cFrame(self.controller, self)
    self.controlframe.pack(side="bottom", fill="x", expand=False, ipady = 10)
    self.newreminderbutton = cButton(self.controller, self.controlframe, text = 'New', command = self._setreminder)
    self.newreminderbutton.pack(side = 'right',padx = 10)
    self.backbutton = cButton(self.controller, self.controlframe, text = 'Back', command = self._goback)
    self.backbutton.pack(side = 'left',padx = 10)
    self.days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    self._renderreminders()

  def on_mousewheel(self,event):
    canvasheight = self.scrollcanvas.winfo_height()
    contentlength = self.scrollframe.winfo_height()
    maxscrolldist = contentlength - canvasheight
    if maxscrolldist > 0:
      self.scrolldowndist += -event.delta*4
      if self.scrolldowndist < 0:
        self.scrolldowndist = 0
      elif self.scrolldowndist > maxscrolldist:
        self.scrolldowndist = maxscrolldist
      self.scrollcanvas.yview_moveto((self.scrolldowndist)/maxscrolldist)

  def _getactualindex(self,index):
    return index - bisect_right(self.deletedreminders,index)
  
  def _return_deletereminder(self,index):
    def _deletereminder():
      offset = bisect_right(self.deletedreminders,index)
      self.deletedreminders.insert(offset,index)
      nindex = index-offset
      self.reminderlist[nindex].destroy()
      del self.reminderlist[nindex]
      del self.controller.notiftimes[nindex]
      #force canvas redraw as elements were taking a while to delete
      self.scrollcanvas.update()
      self.scrollcanvas.update_idletasks()
    return _deletereminder

  def _goback(self):
    self.controller.show_screen('Mainscreen')

  def _renderreminders(self):
    self.reminderlist = []
    self.deletedreminders = []
    for reminder in self.scrollframe.winfo_children():
      reminder.destroy()
    for reminderindex in range(len(self.controller.notiftimes)):
      self.packreminder(reminderindex)
    
  def _return_changereminder(self,index):
    def changereminder():
       self._setreminder(index = self._getactualindex(index))
    return changereminder
  
  def _setreminder(self,index = None):
    self.controller.screendict['Newreminderscreen'].enternew(index)
    self.controller.show_screen('Newreminderscreen')

  def packreminder(self,index):
    reminderframe = cFrame(self.controller, self.scrollframe, highlightbackground = self.controller.background_inset_col, highlightthickness = 1.5, height = 80, width = self.controller.screenwidth)
    reminderframe.pack_propagate(False)
    reminderframe.pack(pady = 0, padx = 0,fill = 'x')
    lframe = cFrame(self.controller, reminderframe)
    lframe.pack(side='left', fill='y')
    rframe = cFrame(self.controller, reminderframe)
    rframe.pack(side='right', fill='y')
    reminder = self.controller.notiftimes[index]
    daylabel = cLabel(self.controller, lframe, text = f'Day: {self.days[reminder[0]]}')
    daylabel.pack(pady = 1.2, padx = 5, anchor="w")
    timelabel = cLabel(self.controller, lframe, text = f'Time: {str(reminder[1]).zfill(2)}:{str(reminder[2]).zfill(2)}')
    timelabel.pack(pady = 1.2, padx = 5, anchor="w")
    treelabel = cLabel(self.controller, lframe, text = f'Tree: {reminder[3]}')
    treelabel.pack(pady = 1.2, padx = 5, anchor="w")
    #vertically centre buttons
    #ignore last few screenshots why would pack verticallye center something??
    centre_frame = cFrame(self.controller, rframe)
    centre_frame.pack(expand=True)
    editbutton = cButton(self.controller,centre_frame,text = 'edit', command = self._return_changereminder(index))
    editbutton.pack(pady = 4, padx = 5)
    deletebutton =  cButton(self.controller,centre_frame,text = 'delete', command = self._return_deletereminder(index))
    deletebutton.pack(pady = 4, padx = 5)
    self.reminderlist.append(reminderframe)

#forgot to add name of tree to grow
#forgot delete button
class Newreminderscreen(cFrame):
  def __init__(self,parent,controller):
    super().__init__(controller, parent)
    self.controller = controller
    self.days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    self.dayindexdict = {self.days[i]:i for i in range(7)}
    self.index = None
    daylabel = cLabel(self.controller,self,text = 'Day:')
    daylabel.pack(pady = 10)
    self.dayselect = ttk.Combobox(self, values=self.days, state="readonly")
    self.dayselect.pack()
    timelabel = cLabel(self.controller,self,text = 'Time:')
    timelabel.pack(pady = 10)
    timeframe = cFrame(self.controller,self)
    timeframe.pack()
    self.hours = ttk.Spinbox(timeframe, from_=0, to=23, width=3, format="%02.0f")
    self.hours.pack(side = 'left', padx = 4)
    timedivider = cLabel(self.controller,timeframe, text = ':')
    timedivider.pack(side = 'left')
    self.mins = ttk.Spinbox(timeframe, from_=0, to=59, width=3, format="%02.0f")
    self.mins.pack(side = 'left', padx = 4)
    treelabel = cLabel(self.controller,self,text = 'Tree:')
    treelabel.pack(pady = 10)
    self.treeselect = ttk.Combobox(self, state="readonly")
    self.treeselect.pack()
    cancelbutton = cButton(self.controller,self, text = 'Back', command = self._cancel)
    cancelbutton.pack(side = 'left',padx = 10)
    savebutton = cButton(self.controller,self, text = 'Save', command = self._save)
    savebutton.pack(side = 'right',padx = 10)
 
  def _cancel(self):
    self.controller.show_screen('Notifscreen')
  
  def _save(self):
    notif = [self.dayindexdict[self.dayselect.get()],int(self.hours.get()),int(self.mins.get()),self.treeselect.get()]
    if self.index != None:
      del self.controller.notiftimes[self.index]
    insort(self.controller.notiftimes,notif)
    self.controller.screendict['Notifscreen']._renderreminders()
    self.controller.show_screen('Notifscreen')

  def enternew(self,index = None):
    self.index = index
    now = datetime.now()
    treenames = [value[0] for value in self.controller.treedatadict.values()]
    self.treeselect.config(values = treenames)
    if self.index != None:
      day,hour,minute,treename = self.controller.notiftimes[index]
      self.dayselect.set(self.days[day])
      self.hours.set(f'{hour:02d}')
      self.mins.set(f'{minute:02d}')
      self.treeselect.set(treename)
    else:
      self.dayselect.set(self.days[now.weekday()])
      self.hours.set(f'{now.hour:02d}')
      self.mins.set(f'{now.minute:02d}')
      self.treeselect.set(treenames[0])