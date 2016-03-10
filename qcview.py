#! /usr/bin/env python
# -*- coding: utf-8 -*-

# File create by Daniel Garcia dgarcia@bic.mni.mcgill.ca
#
# TODO use a csvreader to read write csv files

""" Vtk application to check from a series of jpgs or ppm images.
It has the option to create a csv file with the results of the qc evaluation

Please use it as a stand-alone script on command line
"""
version="1.1"
try:
  import vtk
except ImportError:
  print ""
  print " ** ERROR: vtk not found, please check your implementation"
  print ""
  sys.exit(1)
import vtk
import os,sys
from optparse import OptionParser
from optparse import OptionGroup


class PathTool:
  """ Structure to contain each object """
  def __init__(self,ids,path):
    self.ids=ids # list of ids: e.g. id,visit,sex, ...
    self.path=path # path to a jpg

class FileFinder:
  """ read image list from a file
  """
  def getImages(self):
    return self.images

  def __init__(self,filepath):
    self.images=[]
    p = open(filepath)
    images = p.readlines()
    p.close()

    for a in images :
      a=a.rstrip('\n')
      b = a.split(',')
      if len(b)==2:
        fid = b[0]
        fpath = b[1]
      else:
        fid = b[0]
        fpath = b[0]

      if 1: #os.path.exists(fpath):
        pt=PathTool([fid],fpath)
        self.images.append(pt)

    print " found  " + str(len(self.images))+" images"

class ListFinder:
  """ Create an image structure using the list
  """
  def getImages(self):
    return self.images

  def replaceVariables(self,image,subject):
    newword=image
    for i in range(0,len(subject)):
      var="#V"+str(i)+"#"
      newword=newword.replace(var,subject[i])
    return newword
  
  def __init__(self,subjectslist,imagepath):
    
    print " -- ListFinder: \n        list: "+subjectslist+"\n        imagepath: "+imagepath
    # final images are stored here
    self.images=[]
    self.imagepath=imagepath
    p=open(subjectslist)
    self.subjects=p.readlines()
    p.close()

    for s in self.subjects:
      sp=s[:-1].split(",")
      simage=self.replaceVariables(imagepath,sp)
      sp.append(os.path.basename(simage))
      x=PathTool(sp,simage)
      self.images.append(x)
    # final images
    print "                found "+str(len(self.images))+" images and "+str(len(self.images[0].ids))+" ids"

class PathFinder:
  """ Create a image structure using the path with * 
        only * are supported (no ? or other special characters)
  """
  def __init__(self,searchpath):
    #if os.path.exists(searchpath):
      #self.searchpath=os.path.abspath(searchpath)

    print " -- PathFinder: searching the path "+str(searchpath)

    path="" # common path
    jokers=[] #jokers for selection

    for s in searchpath:
      nb_jokers=s.count("*")
      sp=s.split("/")
      
      # Accelerate search
      # Path is the common part before the first *
      for i in sp:
        nb=i.count("*")
        if nb==0 and len(jokers)==0:
          path=os.path.abspath(path+os.sep+i)
          continue
        jokers.append(i)


      tt=PathTool([],path)
      files=[tt]
      for x in jokers:
        temp=self.selectedFiles(files,x)
        files=temp

      #final images
      self.images=files
      if len(self.images)>0:
        print "                found "+str(len(self.images))+" images and "+str(len(self.images[0].ids))+" ids"
      else:
        print "                found no images!!"

  def getImages(self):
    return self.images

  def selectedFiles(self,files,selection):
    
    selected=[]
    for p in files:


      # first path, next items selection
      file=p.path
      #print " XX "+file
      # extra selection items
      ids=p.ids
      #print " ids "+str(ids)

      # if it is a dir (open files)
      files=[]
      if os.path.isdir(file):
        files=os.listdir(file)
        files.sort()
      else:
        continue

      se=selection.split('*')
      for f in files:
        ok=True
        for s in se:
          if f.count(s) == 0:
            ok=False
            break
        if ok==True:
          filename=file+os.sep+f
          item=[]
          item.extend(ids)
          if len(se)>1: # we don't want the last name in it!
            item.append(f)
          tt=PathTool(item,filename)
          selected.append(tt)
    return selected


class vtkQC:

  def __init__(self,images,csvfile,clobber,zoom1):

    self.iren=None
    self.current=0 # Actual image in the render
    self.islast=False # Actual image in the render
    self.images=images # List with images and parameters
    self.clobber=clobber
    self.messages=["PASSED","FAILED"]
    self.qc=[] # List with images and parameters
    self.csvfile=csvfile # output csv file
    self.zoom1=zoom1 # reset zoom to 1

    if self.csvfile is not None and os.path.exists(self.csvfile) and self.clobber==False:
      print " -- CSV file already exists: importing previous results "+csvfile
      p=open(self.csvfile)
      self.qc=p.readlines()

      if len(self.qc) == 0:
        print "        Empty file!"
      else:
        print "        Removing processed images from the list"
        lenqc=len(self.qc[0].split(','))
        lenima=len(self.images[0].ids)

        eliminateitems=[]
        if lenqc <= lenima:
          print " ** ERROR in qc: number of item does not correspond with images structure!"
          print "    IMA[0] =   "+str(self.images[0].ids)
          print "    QC [0] =   "+str(self.qc[0])
          print "    Use --clobber to continue erasing the qc file"
          sys.exit(1)
        else:

          for i in self.images: # Check every image
            insideqc=False

            for q in self.qc:   # Check every qc
              qcline=q.split(',')
              insideqc=True

              for j in range(0,lenima): #check all item
                if i.ids[j] != qcline[j] :
                  insideqc=False
                  break

              if insideqc==True:
                break

            if insideqc==True:
              print "        Removing "+str(i.ids)
              eliminateitems.append(i)
          before=len(images)
          for i in eliminateitems:
            self.images.remove(i)
          print " -- Size before/after "+str(before)+"/"+str(len(self.images))
    if len(self.images) < 1:
      print " -- No images to check!"
      return

  def saving(self):
    if self.csvfile is not None:
      print " -- Saving qc file now"
      csv=open(self.csvfile,"w") # output csv file pointer
      csv.writelines(self.qc)
      csv.close()
    else:
      print " -- No file was set to save the qc!"


  """ Observer to set behaviour to buttons"""
  def KeyPressed(self,obj, event):

    rwi=obj.GetInteractor()
    key=rwi.GetKeyCode()
    key2=rwi.GetKeySym() # for backspace
    #print key+" "+key2
    if  key == 'e' or key == 'E' or key == 'f' or key == 'F' or key == 'p' or key == 'P' :
      # Remove keys from the default "style"
      pass
    elif key == 'R' or key == 'r' :
      print " -- Reset Camera View "
      print " ParallelScale "+str(self.cam1.GetParallelScale())
      print " GetFocalPoint "+str(self.cam1.GetFocalPoint())
      print " GetPosition "+str(self.cam1.GetPosition())

      self.resetCamera()
    elif key == 'T' or key == 't' :
      print " ParallelScale "+str(self.cam1.GetParallelScale())
      print " GetFocalPoint "+str(self.cam1.GetFocalPoint())
      print " GetPosition "+str(self.cam1.GetPosition())

      
    elif key2 == 'BackSpace':
      if self.current>0: 
        print " -- Previous Image"
        
        # Remove all possible missing images
        if self.csvfile is not None:
          # check if next image is missing and erase all missing
          while True:
            if len(self.qc)>0 and self.qc[-1].count("MISSING"):
              print " -- Skipping another image!"
              self.qc.pop()
              self.current=self.current-1 #set current to next image
            else:
              break
          # Now remove the real last one
          last=self.qc.pop()
          print "    Removing last item of the qc ::"+last

        self.islast=False
        self.current=self.current-1 #set current to next image
        self.readImage()
      else:
        print " -- Already at the first image loaded!"
        if self.csvfile is not None and len(self.qc)>0:
          print "           Images that already had a qc in "+self.csvfile+" were not opened"
          print "           Please, remove manually the entries or just use -clobber to overwrite"

     
    elif  key2 == 'Left':
      if self.current>0: 
        print " -- Previous Image "
        self.current=self.current-1 #set current to next image
        self.readImage()
      else:
        print " -- Already at the first image!"
      
    elif  key2 == 'Right':
      if self.current>=(len(self.images)-1):
        print " -- Already at the last image!"
      else:
        print " -- Next Image"
        self.current=self.current+1 #set current to next image
        self.readImage()
    
    elif key.isdigit():
      # include other behaviors in this if
      #print " -- Number found! "+key
      nkey=int(key)
      
      if self.csvfile is not None and not self.islast:
        label=''
        if nkey>=len(self.messages):
          print " -- WARNING : Label not defined, ignoring number "+key
          
          return
        else:
          label=self.messages[nkey]
        
        string=",".join(self.images[self.current].ids)
        print string+","+label
        self.qc.append(string+","+label+"\n")

      if self.current>=(len(self.images)-1):
        print " -- Already at the last image!"
        self.islast=True
      else:
        print " -- Next Image"
        self.current=self.current+1 #set current to next image
        self.readImage()
      

    else: #leave normal interaction style
      obj.OnChar()

  """ read image """
  def readImage(self):

    # pass to the next image
    # check if the image exists
    while True:

      # check if last!
      if self.islast==True:
        print " -- Already at the last image!"
        break

      elif self.current>= len(self.images):
        print " -- End of images! "
        self.islast=True
        #self.iren.ExitCallback()
        break 

      filename=self.images[self.current].path
      print "fn : " + filename
      # check if image exists (mainly for list based qc)
      if not os.path.exists(filename):
        # write missing and continue
        if self.csvfile is not None:
          string=",".join(self.images[self.current].ids)
          print string+",MISSING!!!"
          self.qc.append(string+",MISSING\n")
        else:
          print " -- Missing Image! "
          print "    "+filename
        self.current=self.current+1
        continue

      # if image exists, load next image
      else:
        
        if filename.endswith("jpg") or filename.endswith("jpeg") or filename.endswith("JPG"):
          self.jpeg.SetFileName(filename)
          self.jpeg.Update()
          self.iajpeg.SetVisibility(1)
          self.iappm.SetVisibility(0)
        else:
          self.ppm.SetFileName(filename)
          self.ppm.Update()
          self.iappm.SetVisibility(1)
          self.iajpeg.SetVisibility(0)

        print "QC len "+str(len(self.qc)) + "  " + self.qc[self.current]

        self.txt.SetInput("rrr" + str(self.current))

        title=",".join(self.images[self.current].ids)
        self.renWin.SetWindowName(title+" --> "+filename)
        self.renWin.Render()
        break #end while True

  def resetCamera(self):
    # Make the image to fill the background
    print " -- Reset Camera "
    origin= self.iappm.GetOrigin()
    spacing=self.ppm.GetDataSpacing()
    extent= self.ppm.GetDataExtent()
    
    if not self.iappm.GetVisibility():
      origin=self.iajpeg.GetOrigin()
      spacing=self.jpeg.GetDataSpacing()
      extent= self.jpeg.GetDataExtent()

    # if jpg it make error rrr : self.ppm.Update()

    self.jpeg.Update()
 
    #print spacing #print extent #print origin

    xc = origin[0] + 0.5*(extent[0] + extent[1])*spacing[0]
    yc = origin[1] + 0.5*(extent[2] + extent[3])*spacing[1]
    xd = (extent[1] - extent[0] + 1)*spacing[0];
    yd = (extent[3] - extent[2] + 1)*spacing[1];
    d = self.cam1.GetDistance();

    #print xc print yc print xd print yd print d

    self.cam1.SetParallelScale(0.5*yd);
    self.cam1.SetFocalPoint(xc,yc,0.0);
    self.cam1.SetPosition(xc,yc,d);
    self.renWin.Render()

  def setMessages(self,messages):
    self.messages=messages
    print " -- Messages defined "
    for i in range(0,len(messages)):
      print "      "+str(i)+" : "+messages[i]
    print ""
    
  """ execute the loop for the rendering """
  def run(self):

    # Create reader
    self.jpeg = vtk.vtkJPEGReader() # read jpegs
    
    self.ppm =  vtk.vtkPNMReader()  # read pnm, ppm
    
    self.iajpeg = vtk.vtkImageActor()
    self.iajpeg.SetInput(self.jpeg.GetOutput())
    self.iajpeg.InterpolateOff()
    
    self.iappm = vtk.vtkImageActor()
    self.iappm.SetInput(self.ppm.GetOutput())
    self.iappm.InterpolateOff()
    
    # Create the RenderWindow, Renderer and both Actors
    self.ren    = vtk.vtkRenderer()
    # Add the actors to the renderer, set the background and size
    self.ren.AddActor(self.iajpeg)
    self.ren.AddActor(self.iappm)
    self.ren.SetBackground(0.1, 0.2, 0.4)

    # create a text actor
    txt = vtk.vtkTextActor()
    txt.SetInput("Hello World!")
    txtprop=txt.GetTextProperty()
    txtprop.SetFontFamilyToArial()
    txtprop.SetFontSize(18)
    txtprop.SetColor(1,1,1)
    txt.SetDisplayPosition(20,30)
    self.txt=txt
    # assign actor to the renderer
    self.ren.AddActor(txt)


    self.renWin = vtk.vtkRenderWindow()
    self.renWin.AddRenderer(self.ren)
    self.renWin.SetSize(500, 500)

    self.iren   = vtk.vtkRenderWindowInteractor()
    self.iren.SetRenderWindow(self.renWin)
    self.iren.Initialize()

    outval=self.readImage()

    if outval=="error":
      print " -- NO images found: Please check your input"
      return
    renderSize=self.renWin.GetSize()

    self.renWin.Render()
    self.cam1 = self.ren.GetActiveCamera()
    self.cam1.ParallelProjectionOn();
    self.ren.ResetCameraClippingRange()
    
    self.resetCamera()

    # Create an image interactor style and associate it with the
    # interactive renderer. Then assign some callbacks with the
    # appropriate events. THe callbacks are implemented as Python functions.
    self.interactor = vtk.vtkInteractorStyleImage()
    self.iren.SetInteractorStyle(self.interactor)
    ktag=self.interactor.HasObserver("CharEvent")
    self.interactor.RemoveObserver(ktag)
    self.interactor.AddObserver("CharEvent", self.KeyPressed)


    self.renWin.Render()
    self.iren.Start()
    # saving qcfile at the end of the loop
    self.saving()

if __name__=="__main__":

  version = "1.0"
  usage = """usage: %prog [1.jpg] [2.jpg] ... [N.jpg][-q <qcfile.csv>]
   or: %prog -s 'search_exp' [-q <qcfile.csv>]
   or: %prog -l <subjects.list> -i <image_path> [-q <qcfile.csv>]
   """
  
  fullhelp="""
   ** Input options:
             This is a QC viewer. Images can be selected by three means:
              1) Give images directly:
                  qcfile will have two columns  'filename,qcresult'
                  
              2) search line : e.g.: -s '~/images/*/v*/qc/*.jpg'
                          example image '~/image/id001/v01/qc/qc_t1.jpg'
                  qcfile will have for columns 'id001,v01,qc_t1.jpg,qcresult'

              c) using a subjects list (id,visit,...) 
                 and a image path ~/images/#V0#/#V1#/qc/qc_t1t2_#V0#_#V1#.jpg
                 #V0# refers to the first column of the subjects.list

                 the qcfile will copy all the columns from the list and add a qc column 

    ** The qcfile.csv:
              Unless clobber, if the qc file exists it is read and all the images 
               already in the qcfile are removed from the qc viewer

    ** The keyboard interaction:
              q: quit the viewer saving the qcfile
              r: reset the zooming to the full screen option
              
              0-9: Pass to next image, saving the number into the qcfile (or the associated message)
                  Option -m allows to configurate the qc messages, default FAILED:PASS
              
              Backspace: Goes back to the previous image removing the performed qc
              
  """
  
  parser = OptionParser(usage=usage,version=version)
  group= OptionGroup(parser," ** List based options "," Options using a list as input")
  group.add_option("-l", "--list", dest="list", help="CSV file with the list of subjects")
  group.add_option("-i", "--image-path", dest="ipath", help="Image path using values (#V0#) in the path")
  group.add_option("-f", "--image-file-path", dest="fpath", help="file containing all image to be reviewed")
  parser.add_option_group(group)
  group= OptionGroup(parser," ** Search based options "," Options using a search expression as input. Only * is accepted")
  group.add_option("-s", "--search", dest="search", help="Search expresion (only * accepted)")
  parser.add_option_group(group)
  group= OptionGroup(parser," ** Output options "," Output options")
  group.add_option("-q", "--qcfile", dest="qcfile", help="QC output file (.csv)")
  group.add_option("-c", "--clobber", dest="clobber", help="Clobber QC file, not reading the content",default=False,action="store_true")
  group.add_option("-m", "--messages", dest="messages", help="Predefine csv messages e.g: FAILED:PASSED",default="FAILED:PASSED")
  parser.add_option_group(group)
  parser.add_option("-H", "--full-help", dest="fhelp", help="Get a larger help message",action="store_true")
  parser.add_option("-z", "--zoom1", dest="zoom1", help="Set default zoom to x1",action="store_true")

  (opts, args) = parser.parse_args()

  if opts.fhelp is True:
    print fullhelp
    sys.exit(0)

  if opts.qcfile is None:
    print ""
    print ""
    print " -- WARNING: no qcfile was given. The output won't be saved!"
    print ""
    print ""

  images=[]
  if opts.search is not None:
    pf=PathFinder([opts.search])
    images=pf.getImages()
  elif opts.list is not None and opts.ipath is not None:
    lf=ListFinder(opts.list,opts.ipath)
    images=lf.getImages()
  elif opts.fpath is not None :
    lf=FileFinder(opts.fpath)
    images=lf.getImages()
  elif len(args)>=1:
    print " -- Using images in the command line"
    for a in args:
      if os.path.exists(a):
        pt=PathTool([a],a)
        images.append(pt)
  else:
    print " -- Choose one method to read the images!"
    print ""
    parser.print_help()
    sys.exit(1)

  print " -- Configuring rendering"
  qc=vtkQC(images,opts.qcfile,opts.clobber,opts.zoom1)
  if len(qc.images) > 0:
    if opts.messages:
      sp=opts.messages.split(':')
      qc.setMessages(sp)

    print " -- Running GUI"
    qc.run()
  print " -- Exiting "+sys.argv[0]


