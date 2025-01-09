import math
from numpy import random
from time import perf_counter
from pixelcanvas import roundup

class Tree():
  def __init__(self): #canvas
    #repr stores list of lists indexed:(0) - total length, (1) - branch section lengths, (2) - branch features, (3) - time, (4) - branch order, (5) - growth scale factor (6) - leaf section lengths, (7) - leaf features
    #features is list of specifications for leaf or branch - angle for leaf (angle,index) for branch (negative angle is left, positive angle is right)
    #time is measured in seconds, length in pixels, angle in radians
    #sections and feaures are sorted from bottom to top
    #to fix long trunk protrusion at top will make top growth threshold a constant
    self.brownrowthresh = 5
    self.brown = '#8B6545'
    self.light_brown = '#9A6F4C'
 #index corresponds to number of leaves in a tile - 1, pointer to greens at that index is colour of tile, last colour covers all leaf counts higher than that index - 1
    self.leafcolourthresholds = [0,1,2,2,3]
    self.greens = ['#079803','#048500','#0C6F00','#1C5101'] #greens get darker as list continues
    self.apex_branch_thresholds = [9,6,3]
    self.leaf_thresholds = [int(10e9),3,2,1] #thresholds for primary and secondary branches
    self.first_growth_scaling_fac = 150 #growth scaling factor for 0th order
    self.length_ratio = 0.3 #ratio between n order and n+1 order growth function scaling factors
    self.branching_threshold_ratio = 0.7 #ratio between n order and n+1 order internode length
    self.global_time = 0
    self.max_order = 3
    self.max_visible_order = 2
    self.repr = [self._newbranch(0)]
    self.expand_offset = 10 #how many pixels canvas expands by when tree grows to big
     #stores positions of all leaves to render after branches
  #save tree state so that it can be reverted to
  def savestate(self):
    #cannot just assign repr to oldrepr as lists are passed by reference
    self.oldrepr = self._recdeepcopy(self.repr)
    self.oldglobal_time = self.global_time

  def recoverstate(self):
    self.repr = self._recdeepcopy(self.oldrepr)
    self.global_time = self.oldglobal_time

  #makes new list with the same values in it as list passed in
  def _recdeepcopy(self,l):
    if isinstance(l,list):
      return [self._recdeepcopy(elem) for elem in l]
    return l
    
  def tick(self,timestep):
    addrepr = []
    for branch in self.repr:
      branch[3] += timestep
      newlength = self._growthfunc(branch[5],branch[3])
      branch[1] = self._auxinweight(branch[1],newlength - branch[0])
      branch[6] = self._auxinweight(branch[6],newlength - branch[0])
      branch[0] = newlength
      #add pair of new branches if possible
      if branch[4] < self.max_order:
        bthresh = self._branching_threshold(self.global_time) * (self.branching_threshold_ratio ** branch[4])
        newsections = []
        for sec_index,sec_length in enumerate(branch[1]):
          branchflag = False
          if sec_index < len(branch[1]) - 1:
            if sec_length > bthresh:
              branchflag = True
          else:
            if sec_length > self.apex_branch_thresholds[branch[4]]:
              branchflag = True
          if branchflag:
            split1,split2 = sorted([self._splitsection(sec_length),self._splitsection(sec_length)])
            newsections += [split1,split2 - split1,sec_length - split2]
            addrepr.append(self._newbranch(branch[4]+1))
            addrepr.append(self._newbranch(branch[4]+1))
            branch1_angle = self._normalbounds(45,(45-25)/3,25,65)*math.pi/180
            branch2_angle = self._normalbounds(45,(45-25)/3,25,65)*math.pi/180
            #selecting if first or second branch goes to the left
            if random.choice([True,False]):
              branch1_angle = -branch1_angle
            else:
              branch2_angle = -branch2_angle
            branch[2].insert(len(newsections)-2,(branch2_angle,len(self.repr)+len(addrepr)-1)) 
            branch[2].insert(len(newsections)-2,(branch1_angle,len(self.repr)+len(addrepr)-2))
          else:
            newsections.append(sec_length)
        branch[1] = newsections
      #add leaves if possible
      newsections = []
      for sec_length in branch[6]:
        lthresh = self.leaf_thresholds[branch[4]]
        if sec_length > lthresh:
          nlength = self._splitsection(sec_length)
          newsections += [nlength, sec_length - nlength]
          #get leaf angle
          angle = random.uniform(-math.pi, math.pi)
          branch[7].insert(len(newsections)-2, angle)
        else:
          newsections.append(sec_length)
      branch[6] = newsections
    self.repr += addrepr
    self.global_time += timestep

  #rejection sampling generating normally distributed values within range
  #ensure <lb, >ub are unlikely
  def _normalbounds(self,mean,deviation,lb,ub):
    genval = lb
    while not (ub > genval > lb):
      genval = random.normal(loc = mean, scale = deviation)
    return genval
  
  #split current section into two:
  def _splitsection(self,length):
    #middle portion of internode of half the length is where new feature can occur
    newfeature = self._normalbounds(length/2,length/(4*3),length/4,3*length/4)
    return newfeature
  
  def _newbranch(self,order):
    return [0.1,[0.1],[],0,order,150 * (self.length_ratio ** order),[0.1],[]]
  
  #returns order 1 branching threshold at time t
  #5px at t=0, 12px after 100hrs
  def _branching_threshold(self, time):
    return time * 2e-3 + 5 
  
  def _growthfunc(self,scaling,time):
    if time <= 120:
      a = -5.95493e-8
      b = 1.38322e-5
      result =  a * time ** 3 + b * time ** 2
    else:
      #0.28118 coefficient scales function to 1 at 100 hours 
      result = 0.28118 * (math.log(time+100,10)-2)
    return result * scaling
  
  #width of branch as function of distance from the top
  def _widthfunc(self,topdist):
    #width of 15 at 150
    return 0.1*topdist

  #use auxin density function (1/(x+0.5)) to distribute new length to all sections of plant
  #IF YOU HAVE LENGTH OF 0 GROWTH ALSO WILL BE 0
  def _auxinweight(self,sections,addlength):
    sectionweights  = []
    #start from the top of the tree
    sections.reverse()
    cumlength = 0
    for csection in sections:
      #integrating density function
      sectionweights.append(math.log(cumlength+csection+0.5) - math.log(cumlength+0.5))
      cumlength += csection
    #section weights need to sum to addlength 
    weightsum = sum(sectionweights)
    sectionweights = [s*addlength/weightsum for s in sectionweights]
    nsections = [s+a for s,a in zip(sectionweights,sections)]
    nsections.reverse()
    return nsections

  def __str__(self):
    reprprint = [str(b) for b in self.repr]
    return "\n".join(reprprint)
  
  #wrap canvas functions and update leaf buffer dimensions
  def _changexdim(self,newpixw,canvas):
    canvas.changexdim(newpixw)
    self.leaf_buffer = [[0 for _ in range(canvas.pixw)] for _ in range(canvas.pixh)]
  
  def _changeydim(self,newpixw,canvas):
    canvas.changeydim(newpixw)
    self.leaf_buffer = [[0 for _ in range(canvas.pixw)] for _ in range(canvas.pixh)]

#repr stores list of lists indexed:(0) - total length, (1) - section lengths, (2) - features, (3) - time, (4) - branch order, (5) - growth scale factor
#('L',type,stage) for leaf ('B',angle,index) for branch (negative angle is left, positive angle is right)
  #wrap recursiverender
  def render(self,canvas,bottom_offset = 0):
    self.leaf_buffer = [[0 for _ in range(canvas.pixw)] for _ in range(canvas.pixh)]
    #start render at bottom centre
    rootx = int(canvas.pixw/2) + self._widthfunc(self.repr[0][0])/2
    rooty = canvas.pixh - bottom_offset -1
    addx,addy = self._recursiverender(rootx,rooty,canvas)
    if addx == 0 and addy == 0:
      self._postprocesstrunk(canvas)
      self._renderleafbuffer(canvas)
    else:
      #round addx and addy up self.pixh
      addx = int(math.ceil(addx/self.expand_offset) * self.expand_offset)
      addy = int(math.ceil(addy/self.expand_offset) * self.expand_offset)
      displayratio = canvas.perfect_width/canvas.perfect_height
      newpixw = canvas.pixw + addx
      newpixh = canvas.pixh + addy
      newratio = newpixw/newpixh
      if displayratio < newratio:
        self._changexdim(newpixw,canvas)
      else:
        self._changeydim(newpixh,canvas)
      rootx = int(canvas.pixw/2) + self._widthfunc(self.repr[0][0])/2
      rooty = canvas.pixh - bottom_offset - 1
      addx,addy = self._recursiverender(rootx,rooty,canvas)
      if addx == 0 and addy == 0:
        self._postprocesstrunk(canvas)
        self._renderleafbuffer(canvas)
      else:
        raise RuntimeError('tree render failed twice')
      
  def _renderleafbuffer(self,canvas):
    for rowindex,row in enumerate(self.leaf_buffer):
      for colindex,tile in enumerate(row):
        if tile != 0:
          if tile <= len(self.leafcolourthresholds):
            write = self.greens[self.leafcolourthresholds[tile - 1]]
          else:
            write = self.greens[self.leafcolourthresholds[-1]]
          canvas.displayarray[rowindex][colindex] = write
    #clear leaf buffer after writing it
    self.leaf_buffer = [[0 for _ in range(canvas.pixw)] for _ in range(canvas.pixh)]

#go through all rows in displayarray, if number of brown pixels in a row is more than self.brownrowthresh make some of the middle ones lighter brown
  def _postprocesstrunk(self,canvas):
    #list of 3-tuple (rowindex, start column index, end column index)
    light_brown_rowwrites = []
    for rowindex,row in enumerate(canvas.displayarray):
      startbrown = None
      endbrown = None
      for colindex, pixelcol in enumerate(row):
        if pixelcol == self.brown:
          if startbrown == None:
            startbrown = colindex
            endbrown = colindex
          else:
            endbrown = colindex
        if (self._stopbrownrow(rowindex,colindex,canvas) or colindex + 1 == len(row)) and startbrown != None:
          brownlength = endbrown - startbrown + 1
          if brownlength > self.brownrowthresh:
            light_brown_rowwrites.append((rowindex,startbrown + 2, endbrown - 2))
          startbrown = None
          endbrown = None
    #make the changes
    for rowindex,startcol,endcol in light_brown_rowwrites:
      for colindex in range(startcol,endcol + 1):
        canvas.displayarray[rowindex][colindex] = self.light_brown

  #helper function for _postprocesstrunk
  def _stopbrownrow(self,rowindex,colindex,canvas):
    offsets = [-1,0,1]
    for yoff in offsets:
      crow = rowindex + yoff
      if len(canvas.displayarray) > crow >= 0:
        if canvas.displayarray[crow][colindex] != self.brown:
          return True
    return False

 #fail is flag to see if tree fits in current canvas, if not we carry on to see what canvas size we need then render starts again with enlarged canvas
 #in order to make branches come out of the correct place rootx,rooty now corresponds to branch vertex furthest down the trunk
 #if angle is 0, it corresponds to right bottom
  def _recursiverender(self,rootx,rooty,canvas,bpoint = 0, angle = 0, fail = False):
    cbranch = self.repr[bpoint]
    bwidth = self._widthfunc(cbranch[0])
    sintheta = math.sin(angle)
    costheta = math.cos(angle)
    #1st base point
    p1 = (rootx,rooty)
    #p2 is other base point, p3 is top point
    if angle >= 0:
      p2 = (rootx - costheta * bwidth, rooty - sintheta * bwidth)
      p3 = (rootx - costheta * bwidth/2 + sintheta * cbranch[0], rooty - sintheta * bwidth/2 - costheta * cbranch[0])
      midbase = (rootx - costheta * bwidth/2, rooty - sintheta * bwidth/2)
    else:
      p2 = (rootx + costheta * bwidth, rooty + sintheta * bwidth)
      p3 = (rootx + costheta * bwidth/2 + sintheta * cbranch[0], rooty + sintheta * bwidth/2 - costheta * cbranch[0])
      midbase = (rootx + costheta * bwidth/2, rooty + sintheta * bwidth/2)
    plist = [p1,p2,p3]
    #traverse leaf features to draw leaves
    cumlength = 0
    xleafcoords = []
    yleafcoords = []
    for findex,leafangle in enumerate(cbranch[7]):
      cumlength += cbranch[6][findex]
      cwidth = self._widthfunc(cbranch[0] - cumlength)
      leafoffset = math.sin(leafangle) * (cwidth/2 +1) #allow leaf to form outside branch
      xleafcoords.append(midbase[0] + cumlength * sintheta + costheta * leafoffset)
      yleafcoords.append(midbase[1] - cumlength * costheta + sintheta * leafoffset)
    #check all points are in canvas bounds
    xs = [x for x,y in plist] + xleafcoords
    ys = [y for x,y in plist] + yleafcoords
    miny = roundup(min(ys))
    maxy = roundup(max(ys))
    minx = roundup(min(xs))
    maxx = roundup(max(xs))
    if miny < 0:
      addy = -miny
    else:
      addy = 0
    addx = max([maxx - canvas.pixw + 1,-minx]) * 2
    if addx < 0:
      addx = 0
    if addx > 0 or addy > 0:
      fail = True
    if not fail:
      if cbranch[4] <= self.max_visible_order:
        canvas.writeshape([p1,p2,p3],self.brown,thin = True)
      for leafx,leafy in zip(xleafcoords,yleafcoords):
        leafx = roundup(leafx)
        leafy = roundup(leafy)
        self.leaf_buffer[leafy][leafx] += 1
    #traverse branch features to recursively draw branches
    cumlength = 0
    for findex,feature in enumerate(cbranch[2]):
      csectionlength = cbranch[1][findex]
      cumlength += csectionlength
      cwidth = self._widthfunc(cbranch[0] - cumlength)
      if addx > 0 or addy > 0:
        fail = True
      if feature[0] > 0:
        new_addx,new_addy = self._recursiverender(midbase[0] + cumlength * sintheta + costheta * cwidth/2, midbase[1] - cumlength * costheta + sintheta * cwidth/2,canvas, bpoint = feature[1], angle = angle + feature[0], fail = fail)
      else:
        new_addx,new_addy = self._recursiverender(midbase[0] + cumlength * sintheta - costheta * cwidth/2, midbase[1] - cumlength * costheta - sintheta * cwidth/2,canvas, bpoint = feature[1], angle = angle + feature[0], fail = fail)
      #add bezier curve to smooth out transition between root and trunk
      #This code only works for 1st order branches and when root is straight!
      if cbranch[4] == 0 and not fail:#(self,coords,colour,thin = True)
        oldwidth = self._widthfunc(cbranch[0] - cumlength + csectionlength)
        nextbranch = self.repr[feature[1]]
        nextbranchsectionlength = nextbranch[1][0]
        nextwidth = self._widthfunc(nextbranch[0])
        nextwidthaftersection = self._widthfunc(nextbranch[0] - nextbranchsectionlength)
        cosbangle = math.cos(feature[0])
        sinbangle = math.sin(feature[0])
        #don't need to check for fail for these draws as they are bounded by points that have been already checked for
        if feature[0] > 0:
          #2nd point is intersection between branch and trunk, 1st is further down on trunk, 3rd is further up on branch
          p1 = (midbase[0] + oldwidth/2, midbase[1] - cumlength + csectionlength)
          p2 = (midbase[0] + cwidth/2, midbase[1] - cumlength)
          p3 = (midbase[0] + cwidth/2 - cosbangle * nextwidth/2 + sinbangle * nextbranchsectionlength + cosbangle * nextwidthaftersection/2, midbase[1] - cumlength - sinbangle * nextwidth/2 - cosbangle * nextbranchsectionlength + sinbangle * nextwidthaftersection/2)
          canvas.writeshape([[p1,p2,p3],p2],self.brown)
        else:
          p1 = (midbase[0] - oldwidth/2, midbase[1] - cumlength + csectionlength)
          p2 = (midbase[0] - cwidth/2, midbase[1] - cumlength)
          p3 = (midbase[0] - cwidth/2 + cosbangle * nextwidth/2 + sinbangle * nextbranchsectionlength - cosbangle * nextwidthaftersection/2, midbase[1] - cumlength + sinbangle * nextwidth/2 - cosbangle * nextbranchsectionlength - sinbangle * nextwidthaftersection/2)
          canvas.writeshape([[p1,p2,p3],p2],self.brown)
      if new_addx > addx:
        addx = new_addx
      if new_addy > addy:
        addy = new_addy
    return (addx,addy)
  