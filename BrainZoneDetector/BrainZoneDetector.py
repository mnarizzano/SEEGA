import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import re
import numpy
import logging

#
# BrainZoneDetector
#

class BrainZoneDetector(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Brain Zone Detector" # TODO make this more human readable by adding spaces
    self.parent.categories = ["SEEGA"]
    self.parent.dependencies = []
    self.parent.contributors = ["G. Arnulfo (Univ. Genoa) & M. Narizzano (Univ. Genoa)"]
    self.parent.helpText = """
    This tool localize the brain zone of a set of points choosen from a markups 
    """
    self.parent.acknowledgementText = """
""" # replace with organization, grant and thanks.

#
# Brain Zone DetectorWidget
#

class BrainZoneDetectorWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    
    #[TODO]
    # Si potrebbe avere un file di configurazione che contiene eventualmente un path alla colorlut
    # Se non e'vuoto allora lo prendo se no prendo questo di default
    self.lutPath = os.path.join(slicer.app.slicerHome,'share/FreeSurfer/FreeSurferColorLUT20120827.txt')
    print self.lutPath
    #[END TODO]

    self.zonedetectionCB = ctk.ctkCollapsibleButton()
    self.zonedetectionCB.text = "Brain Zone Detection"

    self.layout.addWidget(self.zonedetectionCB)

    self.zoneDetectionLayout = qt.QFormLayout(self.zonedetectionCB)

    ### Select Atlas
    self.atlasInputSelector = slicer.qMRMLNodeComboBox()
    self.atlasInputSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.atlasInputSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.atlasInputSelector.selectNodeUponCreation = True
    self.atlasInputSelector.addEnabled = False
    self.atlasInputSelector.removeEnabled = False
    self.atlasInputSelector.noneEnabled = True
    self.atlasInputSelector.showHidden = False
    self.atlasInputSelector.showChildNodeTypes = False
    self.atlasInputSelector.setMRMLScene( slicer.mrmlScene )
    self.atlasInputSelector.setToolTip( "Pick the volumetric Atlas." )
    self.zoneDetectionLayout.addRow("Volumetric parcels: ", self.atlasInputSelector)

    
    self.dialog = qt.QFileDialog()
    self.dialog.setFileMode(qt.QFileDialog.AnyFile)
    self.dialog.setToolTip( "Pick the input to the algorithm." )

    self.fidsSelectorZone = slicer.qMRMLNodeComboBox()
    self.fidsSelectorZone.nodeTypes = ( ("vtkMRMLMarkupsFiducialNode"), "" )
    self.fidsSelectorZone.selectNodeUponCreation = False
    self.fidsSelectorZone.addEnabled = False
    self.fidsSelectorZone.removeEnabled = False
    self.fidsSelectorZone.noneEnabled = True
    self.fidsSelectorZone.setMRMLScene( slicer.mrmlScene )
    self.fidsSelectorZone.setToolTip("Select a fiducial list")
    self.zoneDetectionLayout.addRow("Fiducial : ", self.fidsSelectorZone)
    
    # Run Zone Detection button
    self.zoneButton = qt.QPushButton("Apply")
    self.zoneButton.toolTip = "Run the algorithm."
    self.zoneButton.enabled = True


    #### Aggiungo il bottone al layout
    self.zoneDetectionLayout.addRow(self.zoneButton)

    # connections
    self.zoneButton.connect('clicked(bool)', self.onZoneButton)

#######################################################################################
###  onZoneButton #
#######################################################################################
  def onZoneButton(self):
    slicer.util.showStatusMessage("START Zone Detection")
    print "RUN Zone Detection Algorithm"
    BrainZoneDetectorLogic().runZoneDetection(self.fidsSelectorZone.currentNode(),\
                                         self.atlasInputSelector.currentNode(),\
                                         self.lutPath)
    print "END Zone Detection Algorithm"
    slicer.util.showStatusMessage("END Zone Detection")
    
  def cleanup(self):
    pass


#
# Zone DetectorLogic
#

class BrainZoneDetectorLogic(ScriptedLoadableModuleLogic):
  """
  """
  def __init__(self):
    # Create a Progress Bar
    self.pb = qt.QProgressBar()

  def runZoneDetection(self,fids,inputAtlas,colorLut):
    #[TODO] CHE FA QUI
    nFids = fids.GetNumberOfFiducials()    
    atlas = slicer.util.array(inputAtlas.GetName())
    ras2vox_atlas = vtk.vtkMatrix4x4()
    inputAtlas.GetRASToIJKMatrix(ras2vox_atlas)

    #[TODO] CHE FA QUI????
    FSLUT = {}
    with open(colorLut,'r') as f:
      for line in f:
        if not re.match('^#',line) and len(line)>10:
          lineTok = re.split('\s+',line)
          FSLUT[int(lineTok[0])] = lineTok[1]

    # Initialize the progress bar pb          
    self.pb.setRange(0,nFids)
    self.pb.show()
    self.pb.setValue(0)

    # Update the app process events, i.e. show the progress of the
    # progress bar
    slicer.app.processEvents()

    for i in xrange(nFids):
      # update progress bar
      self.pb.setValue(i+1)
      slicer.app.processEvents()

      # istantiate the variable which holds the point
      currContactCentroid = [0,0,0]      
      # copy current position from FiducialList
      fids.GetNthFiducialPosition(i,currContactCentroid)

      # append 1 at the end of array before applying transform
      currContactCentroid.append(1)

      # transform from RAS to IJK
      voxIdx = ras2vox_atlas.MultiplyFloatPoint(currContactCentroid)
      voxIdx = numpy.round(numpy.array(voxIdx[:3])).astype(int)
      
      # build a -3:3 linear mask
      mask = numpy.arange(-3,4)

      # get Patch Values from loaded Atlas in a 7x7x7 region around
      # contact centroid and extract the frequency for each unique
      # patch Value present in the region
      patchValues = atlas[numpy.ix_(mask+voxIdx[2],\
                                    mask+voxIdx[1],\
                                    mask+voxIdx[0])]
      # Find the unique values on the matrix above
      uniqueValues = numpy.unique(patchValues)

      # Flatten the patch value and create a tuple
      patchValues = tuple(patchValues.flatten(1))
      # Create an array of frequency for each unique value
      itemfreq = [patchValues.count(x) for x in uniqueValues]
      # Compute the max frequency
      totPercentage = numpy.sum(itemfreq)
      # Recover the real patch names
      patchNames = [FSLUT[pValues] for pValues in uniqueValues]
      # Create the zones
      parcels = dict(zip(itemfreq,patchNames))
      print parcels
      #[TODO] COSA FA QUI???
      anatomicalPositionsString = [','.join([v,str( round( float(k) / totPercentage * 100 ))])\
                                   for k,v in parcels.iteritems()]
      #      print ','.join(anatomicalPositionsString)
      fids.SetNthMarkupDescription(i,','.join(anatomicalPositionsString))

