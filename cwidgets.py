import tkinter as tk
from tkinter import ttk

def setkwargs(controller,fontindex,kwargs):
  kwargs.setdefault("bg", controller.background_col)
  kwargs.setdefault("fg", controller.font_col)
  if not fontindex:
    fontindex = controller.default_fontindex
  kwargs.setdefault("font", controller.fontlist[fontindex])
  return kwargs

class cLabel(tk.Label):
  def __init__(self, controller, parent, fontindex = None, **kwargs):
    super().__init__(parent, **setkwargs(controller,fontindex,kwargs))

#use ttk for buttons to get around os restriction  
class cButton(ttk.Button):
  def __init__(self, controller, parent, fontindex = None, **kwargs):
    self.style = ttk.Style()
    if not fontindex:
      fontindex = controller.default_fontindex
    self.style.configure('style.TButton', 
                    background = controller.background_col,
                    foreground = controller.font_col,
                    font = controller.fontlist[fontindex])
    super().__init__(parent,style = 'style.TButton', **kwargs)

class cMessage(tk.Message):
  def __init__(self, controller, parent, fontindex = None, **kwargs):
    super().__init__(parent, **setkwargs(controller,fontindex,kwargs))

class cEntry(tk.Entry):
  def __init__(self, controller, parent, fontindex = None, **kwargs):
    kwargs.setdefault("bg", controller.background_inset_col)
    kwargs.setdefault("fg", controller.font_col)
    if not fontindex:
      fontindex = controller.default_fontindex
    kwargs.setdefault("font", controller.fontlist[fontindex])
    super().__init__(parent, **kwargs)

class cFrame(tk.Frame):
  def __init__(self, controller, parent, **kwargs):
    kwargs.setdefault("bg", controller.background_col)
    super().__init__(parent, **kwargs)

class cSlider(ttk.Scale):
  def __init__(self, controller, parent, **kwargs):
    self.style = ttk.Style()
    self.style.theme_use('default')
    self.style.configure('Style.Horizontal.TScale', 
                    background = controller.background_col,
                    troughcolor = controller.background_inset_col,
                    sliderrelief = controller.background_col
                    )               
    super().__init__(parent, style = 'Style.Horizontal.TScale',  **kwargs)
