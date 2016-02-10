#########################################################################################
### Name convention: Gui Object should have suffix CB for Collapsible
### Button, TB toolbox button etc...
#########################################################################################
import struct 
import os
import unittest
import subprocess
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import numpy
import re
import collections
import json
import math

"""Uses ScriptedLoadableModule base class, available at:
https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
"""
#########################################################################################
####                                                                                 ####
####  DEETO #############################################################################
####                                                                                 ####
#########################################################################################
class DEETO(ScriptedLoadableModule):

#########################################################################################
#### __init__ 
#########################################################################################
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "DEETO" # TODO make this more human readable by adding spaces
    self.parent.categories = ["SEEGA"]
    self.parent.dependencies = []
    self.parent.contributors = ["G. Arnulfo (Univ. Genoa) & M. Narizzano (Univ. Genoa)"]
    self.parent.helpText = """
    seeg electroDE rEconstruction TOol (DEETO):
        This tool reconstructs the position of SEEG electrode contacts 
        from a post-implant Cone-beam CT scan.
    """
    self.parent.acknowledgementText = """
    This file was originally developed by Gabriele Arnulfo & Massimo Narizzano
    """ 
    ## READ the configuration files under the Config/ directory
    self.parentPath = os.path.dirname(parent.path)  
    self.configPath =  self.parentPath + "/Config/deeto.config"
    self.electrodeTypesPath =  self.parentPath + "/Config/electrodes.config"
    
    # Locate the deeto executable path
    with open(self.configPath) as data_file:    
      tmpConfigData = json.load(data_file)

    self.deetoExecutablePath =  self.parentPath + "/" + tmpConfigData["deeto"]

#########################################################################################
####                                                                                 ####
####  DEETOWidget #######################################################################
####                                                                                 ####
#########################################################################################
class DEETOWidget(ScriptedLoadableModuleWidget):

#######################################################################################
### setup 
#######################################################################################
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    #### Some variables
    self.configurationSetup()
    self.segmentationSetup()

#######################################################################################
### configurationSetup 
### Collapsible button, where are stored the information for the segmentation module
### for example the deeto executable location, etc... 
#######################################################################################
  def configurationSetup(self):
    #### Create a Collapsible Button
    self.setupCB = ctk.ctkCollapsibleButton()
    self.setupCB.text = "DEETO - Configuration"
    self.setupCB.collapsed = True
    self.layout.addWidget(self.setupCB)
    
    #### Collapsible button layout
    self.setupFL = qt.QFormLayout(self.setupCB)
    
    #### Tool Box for changing deeto Executable
    self.deetoTB = qt.QToolButton()
    self.deetoTB.setText("...")
    self.deetoTB.toolTip = "Change deeto executable"
    self.deetoTB.enabled = True
    self.deetoTB.connect('clicked(bool)', self.ondeetoTB)

    #### Line Edit button, where the executable path is shown
    self.deetoLE = qt.QLineEdit(slicer.modules.DEETOInstance.deetoExecutablePath)
    self.deetoLE.setDisabled(True)
    self.deetoLE.setMaximumWidth(100)
    self.deetoLE.setFixedWidth(400)

    #### Buttons Layout
    self.deetoButtonsHBL = qt.QHBoxLayout()
    self.deetoButtonsHBL.addWidget(self.deetoLE)
    self.deetoButtonsHBL.addWidget(self.deetoTB)

    #### Aggiungo il bottone al layout
    self.setupFL.addRow("DEETO executable: ", self.deetoButtonsHBL)

    #### Button to change the deeto executable location
    #### It is called in ondeetoTB, when deetoTB is selected 
    self.deetoFD = qt.QFileDialog()
    self.deetoFD.setFileMode(qt.QFileDialog.AnyFile)
    self.deetoFD.setToolTip( "Pick the input to the algorithm." )


#######################################################################################
### segmentationSetup #
#######################################################################################
  def segmentationSetup(self):
    #### Collapsible Button --- General Frame
    self.segmentationCB = ctk.ctkCollapsibleButton()
    self.segmentationCB.text = "DEETO - Segmentation"
    self.segmentationCB.contentsLineWidth = 1
    self.layout.addWidget(self.segmentationCB)
    #### Collapsible Button layout
    self.segmentationFL  = qt.QFormLayout(self.segmentationCB)

    #### Choose Fiducial - Section
    #### Select box a tendina ComboBox -- 
    self.fiducialCBox = slicer.qMRMLNodeComboBox()
    self.fiducialCBox.nodeTypes = ( ("vtkMRMLMarkupsFiducialNode"), "" )
    self.fiducialCBox.selectNodeUponCreation = False
    self.fiducialCBox.addEnabled = False
    self.fiducialCBox.removeEnabled = False
    self.fiducialCBox.noneEnabled = True
    self.fiducialCBox.setMRMLScene( slicer.mrmlScene )
    self.fiducialCBox.setToolTip("Select a fiducial list")
    #### Add fiducial to the Collapsible Buttonx
    self.segmentationFL.addRow("Fiducial List",self.fiducialCBox)
    #### Connect the fiducial list to the 
    self.fiducialCBox.connect('currentNodeChanged(bool)', self.onfiducialCBox)
 
    #### Configure Segmentation - Section
    ### Read from files the list of the modules
    with open(slicer.modules.DEETOInstance.electrodeTypesPath) as data_file:    
      self.models = json.load(data_file)

    #### Create the caption table for the configuration
    self.tableCaption = ["Name","Type/Model","Tail","Head"]
    self.tableHsize  = [80,180,50,50]
    self.captionGB = qt.QGroupBox(self.segmentationCB)
    self.captionBL = qt.QHBoxLayout(self.captionGB)
    self.captionBL.setMargin(1)
    for i in (xrange(len(self.tableCaption))):
      a = qt.QLabel(self.tableCaption[i],self.captionGB)
      a.setMaximumWidth(self.tableHsize[i])
      a.setMaximumHeight(20)
      a.setStyleSheet("qproperty-alignment: AlignCenter;")
      self.captionBL.addWidget(a)
      
    self.segmentationFL.addRow("",self.captionGB)
    self.electrodeList = [] 

#######################################################################################
###  onfiducialCBox   #
###  Create dynamically the electrode table, by reading the fiducial list selected, by 
###  (1) Clear old Fiducial Table
###  (2) If the selected fiducial list is not None Do
###      (a) Read the fiducial list and 
###      (b) for each point pair create an Electrode object containing:
###          name, target and entry coordinates and the flag 
###      (c) check simple error cases: (i) missing entry/target, 
###         (ii) more points than expected
### NB: unselected points will not be parsed
#######################################################################################
  def onfiducialCBox(self):
    # (1) CLEAR the list 
    self.clearTable() ### Eliminate the electrode list
    
    if self.fiducialCBox.currentNode() == None :
      return
    # (2.a) Read the fiducial list  
    operationLog = "" # error/warning Log string
    self.fids = self.fiducialCBox.currentNode()
    self.electrodeList = []
    for i in xrange(self.fids.GetNumberOfFiducials()):
      if self.fids.GetNthFiducialSelected(i) == True:
        P2 = [0.0, 0.0, 0.0]
        self.fids.GetNthFiducialPosition(i, P2)
        #[WARNING] The fiducial name convention is hard coded, change please[/WARNING]#
        # replace name with _1 or 1 with empty char
        self.name = re.sub(r"_?1","",self.fids.GetNthFiducialLabel(i))
        # find the electrode in list with the same name 
        el = [x for x in self.electrodeList if str(x.name.text) == self.name]
        if len(el) > 0 :
          if(len(el[0].target) > 0):
            # (2.c.II)  more points than expected
            operationLog += "WAR: \"" + self.name +"\" has defined more than 2 times"
          P1 = el[0].entry
          el[0].target = P2
          distance_P2_P1 = (pow(P2[0],2.0) + pow(P2[1],2.0) + pow(P2[2],2.0)) -\
                           (pow(P1[0],2.0) + pow(P1[1],2.0) + pow(P1[2],2.0))
          if distance_P2_P1 > 0 :
            el[0].entry = P2
            el[0].target = P1
        else :
          # (2.b) for each point pair create an Electrode object containing:
          #       name, target and entry coordinates and the flag
          # Add the electrode Line to the collapsible button (update the GUI)
          self.electrodeList.append(Electrode(self.name,self.segmentationCB,\
                                              self.models,self.tableHsize))
          self.electrodeList[len(self.electrodeList) - 1].entry = P2 

    # (2.c.i) Look for missing entry/target, 
    el = [x for x in self.electrodeList if (len(x.target) == 0)]
    for i in xrange(len(el)):
      operationLog += "ERR: \"" + el[i].name.text + "\" Missing entry or target"
      el[i].delete()
      self.electrodeList.remove(el[i])

    # Link the electrode to the Form
    for i in (xrange(len(self.electrodeList))):
      self.segmentationFL.addRow("",self.electrodeList[i].row)

    # notify error
    slicer.util.showStatusMessage(operationLog)
    if len(self.electrodeList) == 0:
      return
    # GUI CT Segmentation - Section
    # CT selector  input volume selector
    self.ctVolumeCB = slicer.qMRMLNodeComboBox()
    self.ctVolumeCB.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.ctVolumeCB.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.ctVolumeCB.selectNodeUponCreation = True
    self.ctVolumeCB.addEnabled = False
    self.ctVolumeCB.removeEnabled = False
    self.ctVolumeCB.noneEnabled = True
    self.ctVolumeCB.showHidden = False
    self.ctVolumeCB.showChildNodeTypes = False
    self.ctVolumeCB.setMRMLScene( slicer.mrmlScene )
    self.ctVolumeCB.setToolTip( "Pick the input to the algorithm." )
    
    self.volumeCtLabel = qt.QLabel("CT Volume")
    self.segmentationFL.addRow(self.volumeCtLabel, self.ctVolumeCB) # 

    # START Segmentation Button
    self.startSegmentationPB = qt.QPushButton("Start Segmentation")
    self.startSegmentationPB.toolTip = "Run the algorithm."
    self.startSegmentationPB.enabled = True
  
    self.segmentationFL.addRow("",self.startSegmentationPB)

    # connections
    self.startSegmentationPB.connect('clicked(bool)', self.onstartSegmentationPB)

    
#######################################################################################
### on DEETO BUTTON
#######################################################################################
  def ondeetoTB(self):
    """ on DEETO Tool Box Button Logic """
    fileName = qt.QFileDialog.getOpenFileName(self.deetoFD, \
                                              "Choose surf directory", "~", "")
    self.deetoLE.setText(fileName)
    slicer.modules.DEETOInstance.deetoExecutablePath = fileName

#######################################################################################
### on Start Segmentation, by reading 
#######################################################################################
  def onstartSegmentationPB(self):
    print "RUN SEGMENTATION ALGORITHM "
    DEETOLogic().runSegmentation(self.electrodeList,self.ctVolumeCB.currentNode(),\
                                 slicer.modules.DEETOInstance.parentPath,\
                                 slicer.modules.DEETOInstance.deetoExecutablePath,\
                                 self.models)
    print "END RUN SEGMENTATION ALGORITHM "

#######################################################################################
### clearTable
#######################################################################################
  def clearTable(self):
    if ((len(self.electrodeList) - 1) < 0) :
      return

    #### delete last row
    self.startSegmentationPB.setParent(None)
    self.startSegmentationPB.deleteLater()
    self.segmentationFL.takeAt(self.segmentationFL.count())

    #### delete last two rows (one is the label)
    self.ctVolumeCB.setParent(None)
    self.ctVolumeCB.deleteLater()
    self.volumeCtLabel.setParent(None)
    self.volumeCtLabel.deleteLater()
    self.segmentationFL.takeAt(self.segmentationFL.count())
    self.segmentationFL.takeAt(self.segmentationFL.count())

    
    last = len(self.electrodeList) - 1
    while last >= 0 :
      self.electrodeList[last].delete()
      self.electrodeList.remove(self.electrodeList[last])
      self.segmentationFL.takeAt(self.segmentationFL.count())
      last = len(self.electrodeList) - 1
      
    self.segmentationFL.update()
    # notify error
    slicer.util.showStatusMessage("")



#########################################################################################
####                                                                                 ####
#### DEETOLogic #########################################################################
####                                                                                 ####
#########################################################################################
class DEETOLogic(ScriptedLoadableModuleLogic):

#######################################################################################
### runSegmentation
#######################################################################################
  def runSegmentation(self,elList,volume,parentPath,deetoExe,models):
    ### CHECK that both the fiducials and ct volume have been selected
    if (len(elList) == 0):
      # notify error
      slicer.util.showStatusMessage("Error, no electrode list selected")
      return
    if ( volume == None):
      # notify error
      slicer.util.showStatusMessage("Error, no volume selected")
      return
      
    ### CREATE A NEW FIDUCIAL LIST CALLED ...... [TODO]
    mlogic = slicer.modules.markups.logic()   
   
    ### 
    ### [TODO] Accrocchio, non so come cambiare questi parametri solo
    ### per il nodo corrente, invece che di default
    mlogic.SetDefaultMarkupsDisplayNodeTextScale(1.3)
    mlogic.SetDefaultMarkupsDisplayNodeGlyphScale(1.5)
    mlogic.SetDefaultMarkupsDisplayNodeColor(0.39,0.78,0.78)  # AZZURRO CACCA
    mlogic.SetDefaultMarkupsDisplayNodeSelectedColor(0.39,1.0,0.39)  # VERDONE CACCA
    
    fidNode = slicer.util.getNode(mlogic.AddNewFiducialNode("recon"))

    # Save the volume as has been modified
    self.tmpVolumeFile = parentPath + "/Tmp/tmp.nii.gz"
    self.saveNode(volume,self.tmpVolumeFile)
    # For each electrode "e":
    for i in xrange(len(elList)):
      tFlag = "-l" if (elList[i].tailCheckBox.isChecked() == True) else "-t"
      hFlag = "-h" if (elList[i].headCheckBox.isChecked() == True) else "-e"
      
      # Construct the cmdLine to run the segmentation on "e"
      cmdLine = [str(deetoExe),'-ct',str(self.tmpVolumeFile),\
                 hFlag, str(-1*elList[i].entry[0]), str(-1*elList[i].entry[1]), \
                 str(elList[i].entry[2]), tFlag ,\
                 str(-1*elList[i].target[0]),str(-1*elList[i].target[1]),\
                 str(elList[i].target[2]),'-m'] +\
        map(str,models[elList[i].model.currentText])
      print cmdLine
      # RUN the command line cmdLine. 
      # [NOTE] : I have used Popen since subprocess.check_output wont work at the moment
      # It Looks a problem of returning code from deetoS
      points = subprocess.Popen(cmdLine,stdout=subprocess.PIPE).communicate()[0].splitlines()
      print points

      ### For each of the point returned by deeto we add it to the new markup fiducial
      name = elList[i].name.text
      for p in range(0,(len(points) - 1),3):
        a = fidNode.AddFiducial(float(points[p]),float(points[p+1]),float(points[p+2]))
        fidNode.SetNthFiducialLabel(a, name + str((p/3) + 1))

      ### For each electrode we create a line from the start point to the last + 3mm
      ### Look for two points p1 and p3 starting from p1 and p2 (first and last point segmented
      last = len(points) - 1
      p1 = [float(points[0]), float(points[1]), float(points[2])]
      p2 = [float(points[last - 2]), float(points[last-1]), float(points[last])]
      delta = math.sqrt(math.pow((p1[0] - p2[0]),2) + math.pow((p1[1] - p2[1]),2) + math.pow((p1[2] - p2[2]),2)) 
      p3 = [0.0,0.0,0.0]
      p3[0] = p2[0] + (p2[0] - p1[0]) / delta * 3 # distance 3mm
      p3[1] = p2[1] + (p2[1] - p1[1]) / delta * 3 # distance 3mm
      p3[2] = p2[2] + (p2[2] - p1[2]) / delta * 3 # distance 3mm
      ### Create a vtk line
      lineSource = vtk.vtkLineSource()
      lineSource.SetPoint1(p1)
      lineSource.SetPoint2(p3)
      lineSource.SetResolution(100) ## why?
      lineSource.Update()
      ### Create a model of the line to add to the scene
      model = slicer.vtkMRMLModelNode()
      model.SetName(name + "_direction")
      model.SetAndObservePolyData(lineSource.GetOutput())
      modelDisplay = slicer.vtkMRMLModelDisplayNode()
      modelDisplay.SetSliceIntersectionVisibility(True) # Hide in slice view
      modelDisplay.SetVisibility(True) # Show in 3D view
      modelDisplay.SetColor(1,0,0)
      slicer.mrmlScene.AddNode(modelDisplay)
      model.SetAndObserveDisplayNodeID(modelDisplay.GetID())
      slicer.mrmlScene.AddNode(model)

#######################################################################################
### saveNode
#######################################################################################
  def saveNode(self,node, filename, properties={}):
    """Save 'node' data into 'filename'.
    It is the user responsability to provide the appropriate file extension.
    User has also the possibility to overwrite the fileType internally retrieved using
    method 'qSlicerCoreIOManager::fileWriterFileType(vtkObject*)'. This can be done
    by specifiying a 'fileType'attribute to the optional 'properties' dictionary.
    """
    from slicer import app
    properties["nodeID"] = node.GetID();
    properties["fileName"] = filename
    if hasattr(properties, "fileType"):
      filetype = properties["fileType"]
    else:
      filetype = app.coreIOManager().fileWriterFileType(node)
    return app.coreIOManager().saveNodes(filetype, properties)



#########################################################################################
####                                                                                 ####
#### Electrode ##########################################################################
####                                                                                 ####
#########################################################################################
class Electrode():

#######################################################################################
### __init__
#######################################################################################
  def __init__ (self,name,configurationCB,models,hsize):

    ## target and entry point
    self.target = []
    self.entry  = []

    #### Crea a new GroupBOX i.e. a line
    self.row = qt.QGroupBox(configurationCB)
    self.hlayout = qt.QHBoxLayout(self.row)
    self.hlayout.setMargin(1)
    #### Crea a new label
    self.name = qt.QLabel(name,self.row)
    self.name.setMaximumWidth(hsize[0])
    self.name.setMaximumHeight(20)
    self.hlayout.addWidget(self.name)

    #### Set the model list combo box
    self.model = qt.QComboBox(self.row)
    for k in models.keys():
      self.model.addItem(k)
    self.model.setMaximumWidth(hsize[1])
    self.model.setMaximumHeight(20)
    self.model.setStyleSheet("qproperty-alignment: AlignCenter;")
    self.hlayout.addWidget(self.model)
    #### Tail Check Box
    self.tailCheckBox = qt.QCheckBox(self.row)
    self.tailCheckBox.setMaximumWidth(hsize[2])
    self.tailCheckBox.setMaximumHeight(20)
    self.tailCheckBox.setStyleSheet("qproperty-alignment: AlignCenter;")
    self.hlayout.addWidget(self.tailCheckBox)
    ### Head CheckBox
    self.headCheckBox = qt.QCheckBox(self.row)
    self.headCheckBox.setMaximumWidth(hsize[3])
    self.headCheckBox.setMaximumHeight(20)
    self.headCheckBox.setStyleSheet("qproperty-alignment: AlignCenter;")
    self.hlayout.addWidget(self.headCheckBox)

#######################################################################################
### delete
#######################################################################################
  def delete (self):
    self.row.setParent(None)
    self.row.deleteLater()

