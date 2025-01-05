from tkinter import Tk, Canvas,Frame,BOTH
import math
#implement rounding 0.5 up (even for negatives) rather than rounding 0.5 to nearest even integer
def roundup(n):
  return int(math.floor(n+0.5))

def print2D(a):
  for l in a:
    print(l)

class PixelCanvas(Canvas):
  #assume width,height are factors of integer pixsize
  def __init__(self,parent,width,height,pixsize,**kwargs):
    self.perfect_width = width
    self.perfect_height = height
    self.pixsize = pixsize
    self.pixw = int(width/pixsize)
    self.pixh = int(height/pixsize)
    self._resetdisplay()
    self.width = pixsize*self.pixw
    self.height = pixsize*self.pixh
    super().__init__(parent,width = self.width, height = self.height, highlightthickness = 0,**kwargs)
    self.pack()
  
  def changexdim(self,pixlen):
    self.pixsize = int(self.perfect_width/pixlen)
    self.pixw = pixlen
    self.pixh = int(self.perfect_height/self.pixsize)
    self.height = self.pixh*self.pixsize
    self.width = self.pixw*self.pixsize
    self.config(height = self.height, width = self.width, bd = 0)
    self._resetdisplay()
  
  def changeydim(self,pixlen):
    self.pixsize = int(self.perfect_height/pixlen)
    self.pixh = pixlen
    self.pixw = int(self.perfect_width/self.pixsize)
    self.height = self.pixh*self.pixsize
    self.width = self.pixw*self.pixsize
    self.config(height = self.height, width = self.width, bd = 0)
    self._resetdisplay()

  #reset display array after every frame
  def _resetdisplay(self):
    self.displayarray = [[None for _ in range(self.pixw)] for _ in range(self.pixh)]

  def render(self):
    #remove previous frame
    self.delete('all')
    #draw the corresponding pixel square for every element in displayarray
    for rownum,displayrow in enumerate(self.displayarray):
      for colnum,cpixel in enumerate(displayrow):
        xoff = colnum*self.pixsize
        yoff = rownum*self.pixsize
        if cpixel != None:
          self.create_rectangle(xoff,yoff,xoff+self.pixsize,yoff+self.pixsize, fill = cpixel, outline = "")
    self._resetdisplay()

  #for filling in shape outlines - only want shape boundary to be visible to floodfill
  def _tempdisplay(self):
    self.temp_displayarray = self.displayarray
    self._resetdisplay()
  
  #draw new display over original display
  def _restoredisplay(self):
    for colnum, row in enumerate(self.temp_displayarray):
      for rownum, cpix in enumerate(row):
        if self.displayarray[colnum][rownum] == None:
          self.displayarray[colnum][rownum] = cpix

  #helper for writecurve, writes a vertical line to the displayarray
  def _writecol(self,column,rowstart,rowstop,colour):
    for crow in range(rowstart,rowstop+1):
      self.displayarray[crow][column] = colour

  #func takes in x coordinate, returns tuple of all y values for that x
  #draws porton of curve between xstart and xstop
  #cstart has to be less than cstop!
  def writecurve(self,func,xstart,xstop,colour,thin = True):
    #get start and end pixels
    cstart = roundup(xstart)
    cstop = roundup(xstop)
    rstarts = [(roundup(y),False) for y in func(xstart)]
    rstops = [(roundup(y),False) for y in func(xstop)]
    for ccolumn in range(cstart,cstop+1):
      partitions = []
      lintercept  = [(roundup(y),False) for y in func(ccolumn-0.5)]
      rintercept = [(roundup(y),True) for y in func(ccolumn+0.5)]
      #collect all curve points
      if ccolumn == cstart:
        partitions += rstarts
      else:
        partitions += lintercept
      if ccolumn == cstop:
        partitions += rstops
      else:
        partitions += rintercept
      partitions.sort(key = lambda x:x[0])
      #cover points out of canvas bounds
      partitions = [point for point in partitions if point[0] >= 0]
      if len(partitions)%2:
        partitions.insert(0,(0,False))
      partitions = [point for point in partitions if point[0] < self.pixh]
      if len(partitions)%2:
        partitions.append((self.pixh-1,False))
      for cpointindex in range(0,len(partitions),2):
        spoint,spointflag = partitions[cpointindex]
        epoint,epointflag = partitions[cpointindex+1]
        #make line thinner
        if thin:
          if spointflag and epointflag:
            spoint += 1
            epoint -= 1
          elif spoint!=epoint:
            if spointflag:
              spoint += 1
            elif epointflag:
              epoint -= 1
        self._writecol(ccolumn,spoint,epoint,colour)

  #lines defined with start and end coordinates
  def writeline(self,xstart,ystart,xstop,ystop,colour,thin = True):
    #construct line function passing through points using point slope form
    if roundup(xstop) != roundup(xstart):
      gradient = (ystop - ystart)/(xstop - xstart)
      if xstart>xstop:
        self.writecurve(lambda x:(gradient*(x - xstart)+ystart,),xstop,xstart,colour,thin = thin)
      else:
        self.writecurve(lambda x:(gradient*(x - xstart)+ystart,),xstart,xstop,colour,thin = thin)
    #for vertical lines:
    else:
      if ystart>ystop:
        ystart,ystop = ystop,ystart
      self._writecol(roundup(xstart),roundup(ystart),roundup(ystop),colour)
  
  #coords is list of 2-tuples
  def writeoutline(self,coords,colour,thin = True):
    coords.append(coords[0])
    for icoord in range(len(coords)-1):
      self.writeline(*coords[icoord],*coords[icoord+1],colour,thin = thin)

  #need to construct a temporary canvas to fill the outline of the shape in 
  def writeshape(self,coords,colour,thin = True):
    offsets = [(1,0),(-1,0),(0,1),(0,-1)]
    self._tempdisplay()
    self.writeoutline(coords,colour,thin = thin)
    xcoords = []
    ycoords = []
    for x,y in coords:
      xcoords.append(x)
      ycoords.append(y)
    miny = roundup(min(ycoords) - 1)
    maxy = roundup(max(ycoords) + 1)
    minx = roundup(min(xcoords) - 1)
    maxx = roundup(max(xcoords) + 1)
    seenset = set([(minx,miny)])
    tovisit = [(minx,miny)]
    while tovisit:
      c1,c2 = tovisit.pop()
      for o1,o2 in offsets:
        select = False
        n1 = c1 + o1
        n2 = c2 + o2
        if maxx >= n1 >= minx and maxy >= n2 >= miny and (n1,n2) not in seenset: 
          if self.pixw > n1 >= 0 and self.pixh > n2 >= 0:
            if self.displayarray[n2][n1] != colour:
              select = True
          else:
            select = True
        if select:
          seenset.add((n1,n2))
          tovisit.append((n1,n2))
    for x in range(minx+1,maxx):
      for y in range(miny+1,maxy):
        if (x,y) not in seenset:
          self.displayarray[y][x] = colour
    self._restoredisplay()