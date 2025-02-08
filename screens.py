import tkinter as tk
from tkinter import messagebox
from PIL import Image as im, ImageTk
import random
import numpy as np
from bisect import insort,bisect_right
from datetime import datetime,timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from pixelcanvas import PixelCanvas, hextorgb
from cwidgets import *

def _roundhours(hours):
  hours = round(hours,1)
  if hours.is_integer():
    return int(hours)
  return hours
  
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
    if datetime.now().weekday() == self.controller.checkinday:
      checkinframe = cFrame(self.controller,self,highlightbackground = self.controller.font_col, highlightthickness = 1)
      checkinframe.pack(padx = 5,pady = 5,ipady = 5,ipadx = 5)
      checkinlabel = cLabel(self.controller,checkinframe,text = 'Your weekly progress report is ready!')
      checkinlabel.pack()
      viewcheckin = cButton(self.controller, checkinframe, command = self._switchtocheckin, text = 'view')
      viewcheckin.pack(pady = (5,0))
    #frame for all the tree buttons
    self.treeframe = cFrame(self.controller, self)
    self.treeframe.pack(side="top", fill="both", expand=True)
    self.drawtreeoptions()
    #frame for time slider and edit button
    self.controlframe = cFrame(self.controller, self)
    self.controlframe.pack(side="bottom", fill="x", expand=False,ipady = 10)
    self.timelabel = cLabel(self.controller,self.controlframe)
    self.timelabel.pack()
    self.timeslider = cSlider(self.controller, self.controlframe, from_=self.min_focustime, to=self.max_focustime, command = self._updatetimelabel, value = self.controller.focustimepreset ,orient="horizontal",length = 200)
    self.timeslider.pack(pady = 10)
    self.editbutton = cButton(self.controller, self.controlframe, text = 'edit', command = self._edittrees)
    self.editbutton.pack(side = tk.LEFT,padx = 10)
    self.notificationbutton = cButton(self.controller, self.controlframe, text = 'reminders', command = self. _changetonotifs)
    self.notificationbutton.pack(side = tk.RIGHT,padx = 10)
    self._updatetimelabel(self.controller.focustimepreset)

  def drawtreeoptions(self):
    for placeindex,treeindex in enumerate(self.controller.treepicturedict.keys()):
      ygrid,xgrid = divmod(placeindex,self.treegridwidth)
      self.addtreebutton(treeindex,xgrid,ygrid)

  def _returndeletetree(self,index):
    def deletetree():
      result = messagebox.askyesno(message = 'Do you want this tree to be permanently deleted?')
      if result:
        self.controller.deletetree(index)
    return deletetree

  def _switchtocheckin(self):
    self.controller.show_screen('Checkinscreen')

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
    self.delbuttons = []
    for index,frame in self.treebuttonframe.items():
      delbutton = cButton(self.controller, frame, text = 'delete', command = self._returndeletetree(index),width = 6)
      delbutton.pack()
      self.delbuttons.append(delbutton)

  def _stoptreeedit(self):
    self.editbutton.config(text = 'edit', command = self._edittrees)
    self.addtreebuttonframe.destroy()
    for delbutton in self.delbuttons:
      delbutton.destroy()

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
    self.updatepercent(treeindex)

  def updatepercent(self,treeindex):
    focustime = self.controller.focustimeweek(datetime.now(),treeindex)
    timequota = self.controller.treedatadict[treeindex][2]
    percent = int((focustime/timequota)*100)
    self.treebuttonframe[treeindex].children['!clabel2'].config(text=f'{percent}%')

  def _addoptionbutton(self,tkpicture,treename,onbuttonclick,xgrid,ygrid):
    buttonframe = cFrame(self.controller, self.treeframe, height = 145, width = tkpicture.width())
    padx = (self.controller.screenwidth - self.treegridwidth * tkpicture.width())/(self.treegridwidth * 2)
    buttonframe.grid(row = ygrid, column = xgrid, padx = padx, pady = 10)
    treebutton = tk.Button(buttonframe, image = tkpicture, command = onbuttonclick, width = tkpicture.width() - 4, height = tkpicture.height() - 4)
    treebutton.pack()
    namelabel = cLabel(self.controller,buttonframe,text = treename)
    namelabel.pack()
    percentlabel = cLabel(self.controller,buttonframe)
    percentlabel.pack()
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
    self.canvas.pack(pady = (25,5))
    self.subjectlabel = cLabel(self.controller, self,fontindex = 2)
    self.subjectlabel.pack()
    self.timeleftlabel = cLabel(self.controller, self, fontindex = 3)
    self.timeleftlabel.pack(ipady = 0,pady = 0)
    self.stopbutton = cButton(self.controller,self, text = 'Stop early', command=self._stopearly)
    self.stopbutton.pack()

  def _stopearly(self):
    result = messagebox.askyesno(message = 'Your progress will not be saved. Are you sure you want to stop?')
    if result:
      self.premature_endfocus()

#time measured in minutes, self.timeleft in seconds
  def focus(self,treeindex,time):
    self.totaltime = time
    self.timeleft = time * 60
    self.subjectlabel.config(text = self.controller.treedatadict[treeindex][1])
    self.ctreeindex = treeindex
    self.ctree = self.controller.fetchtree(treeindex)
    self.ctree.savestate()
    self.nowfocused = True
    self._driver()
 
  def _endfocus(self):
    self.controller.addfocustime(self.ctreeindex,self.totaltime)
    self.controller.screendict['Mainscreen'].updatepercent(self.ctreeindex)
    self.ctree.render(self.canvas)
    image = self.canvas.renderimage()
    self.controller.changetreepicture(self.ctreeindex,image)
    self.nowfocused = False
    self.controller.show_screen('Mainscreen')
  
  def premature_endfocus(self):
    self.controller.addfocustime(self.ctreeindex,self.totaltime - self.timeleft/60)
    self.controller.screendict['Mainscreen'].updatepercent(self.ctreeindex)
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

class Checkinscreen(cFrame):
  def __init__(self,parent,controller):
    super().__init__(controller, parent)
    self.controller = controller
    containerframe = cFrame(self.controller,self)
    containerframe.pack(side="top", fill="both", expand=True)
    containerframe.grid_rowconfigure(0, weight=1)
    containerframe.grid_columnconfigure(0, weight=1)
    controlframe = cFrame(self.controller,self)
    controlframe.pack(side="bottom", fill="x", expand=False, ipady = 10)
    backbutton = cButton(self.controller,controlframe,text = 'back', command = self._backbutton)
    backbutton.pack(side = 'left',padx = 10)
    self.screentoggle = cButton(self.controller,controlframe)
    self.screentoggle.pack(side = 'right',padx = 10)
    screenclasses = [Statsscreen,Quotascreen]
    self.screendict = {}
    for screenclass in screenclasses:
      screen = screenclass(containerframe,controller)
      screen.grid(row=0,column=0,sticky="nsew")
      self.screendict[screenclass.__name__] = screen
    self.showscreen('Statsscreen')
  
  def showscreen(self,name):
    if name=='Statsscreen':
      self.screentoggle.config(command = self._returnshowscreen('Quotascreen'),text = 'time goals')
    else:
      self.screentoggle.config(command = self._returnshowscreen('Statsscreen'), text = 'stats')
    self.screendict[name].tkraise()
  
  def _returnshowscreen(self,name):
    def showwrapper():
      self.showscreen(name)
    return showwrapper
  
  def _backbutton(self):
    self.controller.show_screen('Mainscreen')

class Statsscreen(cFrame):
  def __init__(self,parent,controller):
    super().__init__(controller, parent)
    self.controller = controller
    self.treenames = [t[0] for t in self.controller.treedatadict.values()]
    self.treeindexmap = {v[0]:k for k,v in self.controller.treedatadict.items()}
    if self.controller.streak[1] == 1:
      streaktext = f'You have a streak of 1 day, keep going!'
    else:
      streaktext = f'You have a streak of {self.controller.streak[1]} days, keep going!'
    streaklabel = cLabel(self.controller,self,text = streaktext,fontindex = 2, wraplength = self.controller.screenwidth - 10)
    streaklabel.pack(pady = (10,0))
    self.barframe = cFrame(self.controller,self)
    self.barframe.pack(pady = (0,20))
    self._getstats()
    self._renderbars(self.treestats['all'][0],self.dailycats)
    self.barchart.pack(padx = 10)
    self.whichtree = ttk.Combobox(self.barframe, values = self.treenames + ['Overall'], state = "readonly",width = 5)
    self.whichtree.set('Overall')
    self.whichtree.bind('<<ComboboxSelected>>', self._changebar)
    self.whichtree.pack(side = 'left', padx = (10,2))
    self.whichtime = ttk.Combobox(self.barframe, values = ['Days','Weeks'], state = "readonly",width = 5)
    self.whichtime.set('Days')
    self.whichtime.bind('<<ComboboxSelected>>', self._changebar)
    self.whichtime.pack(side = 'left', padx = 2)
    unmet = 0
    met = 0
    dateob = datetime.now() - timedelta(days = 1)
    for treeindex,treeval in self.controller.treedatadict.items():
      if self.controller.focustimeweek(dateob,treeindex) > treeval[2]:
        met += 1
      else:
        unmet += 1
    if met == 1:
      pietext = 'You met 1 goal:'
    else:
      pietext = f'You met {met} goals:'
    pielabel = cLabel(self.controller,self,text = pietext)
    pielabel.pack()
    fig, ax = plt.subplots(figsize=(1.4, 1.4))
    if met + unmet >0:
      ax.pie([met,unmet], colors=[self.controller.highlight_col,self.controller.background_inset_col],startangle=90,wedgeprops={'edgecolor': self.controller.font_col, 'linewidth': 0.6})
      ax.set_facecolor(self.controller.background_col)
      fig.patch.set_facecolor(self.controller.background_col)
      plt.tight_layout()
      plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
      canvas = FigureCanvasTkAgg(fig, master=self)
      canvas.draw()
      self.piechart = canvas.get_tk_widget()
      self.piechart.pack(pady = 0)

  def _changebar(self,event):
    self.barchart.destroy()
    treeselect = self.whichtree.get()
    if treeselect == 'Overall':
      treeindex = 'all'
    else:
      treeindex = self.treeindexmap[treeselect]
    if self.whichtime.get() == 'Days':
      timeindex = 0
      cats = self.dailycats
    else:
      timeindex = 1
      cats = self.weeklycats
    self._renderbars(self.treestats[treeindex][timeindex],cats)
    self.barchart.pack(before = self.whichtree,padx = 10)

  def _getstats(self):
    #treestats value is list of 2 lists - daily times in past week and weekly times in past 2 months
    self.treestats = {}
    #Get names for the bars
    self.dailycats = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    self.dailycats = self.dailycats[self.controller.checkinday:] + self.dailycats[:self.controller.checkinday]
    self.weeklycats = []
    dateob = datetime.now()
    dateob -= timedelta(days = 1)
    for _ in range(8):
      dateob -= timedelta(days = 7)
      self.weeklycats.append(dateob.strftime("%-d-"))
    self.weeklycats.reverse()
    #self.treestats['all'] stores combined data:
    self.treestats['all'] = []
    self.treestats['all'].append([0 for _ in range(7)])
    self.treestats['all'].append([0 for _ in range(8)])
    #Get time data
    for treeindex in self.controller.treedatadict.keys():
      self.treestats[treeindex] = []
      #past week:
      dateob = datetime.now() 
      dailytimes = []
      for _ in range(7):
        dateob -= timedelta(days = 1)
        dailytimes.append(_roundhours(self.controller.focustimeday(dateob,treeindex)/60))
      self.treestats[treeindex].append(list(reversed(dailytimes)))
      for i,time in enumerate(reversed(dailytimes)):
        self.treestats['all'][0][i] += time
      #past 2 months:
      dateob = datetime.now()
      dateob -= timedelta(days = 1)
      weeklytimes = []
      for _ in range(8):
        cweektime = self.controller.focustimeweek(dateob,treeindex)
        dateob -= timedelta(days = 7)
        weeklytimes.append(_roundhours(cweektime/60))
      self.treestats[treeindex].append(list(reversed(weeklytimes)))
      for i,time in enumerate(reversed(weeklytimes)):
        self.treestats['all'][1][i] += time

  def _renderbars(self,data,cats):
    fig, ax = plt.subplots(figsize=(3.6, 1.6))
    bars = ax.bar(cats, data, color=self.controller.highlight_col)
    ax.set_facecolor(self.controller.background_col)
    ax.tick_params(axis='x', colors = self.controller.font_col)  
    ax.tick_params(axis='y', colors = self.controller.font_col)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_edgecolor(self.controller.font_col)
    ax.spines['left'].set_edgecolor(self.controller.font_col)
    fig.patch.set_facecolor(self.controller.background_col)
    plt.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=self.barframe)
    canvas.draw()
    self.barchart = canvas.get_tk_widget()

class Quotascreen(cFrame):
  def __init__(self,parent,controller):
    super().__init__(controller, parent)
    self.controller = controller
    spacings = [40,40,60,25,20]
    padding = 15
    rowheight = 40
    yesterday = datetime.now() - timedelta(days = 1)
    ypos = 10
    xpos = 10
    for data, space in zip(['tree','goal','time spent','new goal'],spacings):
      l = cLabel(self.controller,self,text = data)
      l.place(x = xpos, y = ypos)
      xpos += padding + space
    ypos += rowheight
    self.entrylist = []
    for treeindex in self.controller.treedatadict.keys():
      name = self.controller.treedatadict[treeindex][0]
      timegoal = _roundhours(self.controller.treedatadict[treeindex][2]/60)
      timegoalstr = f'{timegoal} hrs'
      timespentstr = f'{_roundhours(self.controller.focustimeweek(yesterday,treeindex)/60)} hrs'
      xpos = 10
      for data, space in zip([name,timegoalstr,timespentstr],spacings):
        l = cLabel(self.controller,self,text = data)
        l.place(x = xpos, y = ypos)
        xpos += padding + space
      xpos += 6
      enterhours = cEntry(self.controller,self,width = 2)
      enterhours.insert(tk.END,timegoal)
      enterhours.bind("<FocusIn>", self._returnentryfocus(enterhours))
      enterhours.place(x = xpos, y = ypos-3)
      self.entrylist.append((treeindex,enterhours))
      xpos += spacings[3]
      l = cLabel(self.controller,self,text = ' hrs')
      l.place(x = xpos, y = ypos)
      enterhours.tkraise()
      ypos += rowheight
    savebutton = cButton(self.controller,self,text = 'save',command = self._savesettings)
    savebutton.place(x = padding, y = ypos)
  
  def _savesettings(self):
    for treeindex,entrybox in self.entrylist:
      try:
        self.controller.treedatadict[treeindex][2] = int(entrybox.get())*60
      except:
        pass

  def _returnentryfocus(self,entrybox):
    def entryfocus(arg):
      entrybox.delete(0, tk.END)
    return entryfocus