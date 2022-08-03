import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import re
import numpy
import collections
import logging
import json
import platform

#
# BrainZoneDetector
#

class BrainZoneDetector(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "2. Brain Zone Detector"  # TODO make this more human readable by adding spaces
        self.parent.categories = ["SEEGA"]
        self.parent.dependencies = []
        self.parent.contributors = ["G. Arnulfo (Univ. Genoa) & M. Narizzano (Univ. Genoa)"]
        self.parent.helpText = """
    This tool localize the brain zone of a set of points choosen from a markups 
    """
        self.parent.acknowledgementText = """
"""  # replace with organization, grant and thanks.


#
# Brain Zone DetectorWidget
#

class BrainZoneDetectorWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # [TODO]
        # Si potrebbe avere un file di configurazione che contiene eventualmente un path alla colorlut
        # Se non e' vuoto allora lo prendo se no prendo questo di default
        if platform.system() == "Darwin":
            self.lutPath = (os.path.join(slicer.app.slicerHome, 'Extensions-30893/SlicerFreeSurfer/share/Slicer-5.0/qt-loadable-modules/FreeSurferImporter/FreeSurferColorLUT20120827.txt'),\
                       os.path.join(slicer.app.slicerHome, 'Extensions-30893/SlicerFreeSurfer/share/Slicer-5.0/qt-loadable-modules/FreeSurferImporter/FreeSurferColorLUT20060522.txt'),\
                       os.path.join(slicer.app.slicerHome, 'Extensions-30893/SlicerFreeSurfer/share/Slicer-5.0/qt-loadable-modules/FreeSurferImporter/FreeSurferColorLUT20150729.txt'),\
                       os.path.join(slicer.app.slicerHome, 'Extensions-30893/SlicerFreeSurfer/share/Slicer-5.0/qt-loadable-modules/FreeSurferImporter/Simple_surface_labels2002.txt'))
        else:
            self.lutPath = (os.path.join(slicer.app.slicerHome,'NA-MIC/Extensions-30893/SlicerFreeSurfer/share/Slicer-5.0/qt-loadable-modules/FreeSurferImporter/FreeSurferColorLUT20120827.txt'), \
                            os.path.join(slicer.app.slicerHome,'NA-MIC/Extensions-30893/SlicerFreeSurfer/share/Slicer-5.0/qt-loadable-modules/FreeSurferImporter/FreeSurferColorLUT20060522.txt'), \
                            os.path.join(slicer.app.slicerHome,'NA-MIC/Extensions-30893/SlicerFreeSurfer/share/Slicer-5.0/qt-loadable-modules/FreeSurferImporter/FreeSurferColorLUT20150729.txt'), \
                            os.path.join(slicer.app.slicerHome,'NA-MIC/Extensions-30893/SlicerFreeSurfer/share/Slicer-5.0/qt-loadable-modules/FreeSurferImporter/Simple_surface_labels2002.txt'))


        print (self.lutPath)
        # [END TODO]

        atlasNode = slicer.mrmlScene.GetNodesByName('aparc*').GetItemAsObject(0)
        reconFileNode = slicer.mrmlScene.GetNodesByName('recon').GetItemAsObject(0)

        self.zonedetectionCB = ctk.ctkCollapsibleButton()
        self.zonedetectionCB.text = "Brain Zone Detection"

        self.layout.addWidget(self.zonedetectionCB)

        self.zoneDetectionLayout = qt.QFormLayout(self.zonedetectionCB)

        ### Select Atlas
        self.atlasInputSelector = slicer.qMRMLNodeComboBox()
        self.atlasInputSelector.nodeTypes = ("vtkMRMLLabelMapVolumeNode","vtkMRMLScalarVolumeNode")
        #self.atlasInputSelector.addAttribute("vtkMRMLScalarVolumeNode", "LabelMap", 0)
        self.atlasInputSelector.selectNodeUponCreation = True
        self.atlasInputSelector.addEnabled = False
        self.atlasInputSelector.removeEnabled = False
        self.atlasInputSelector.noneEnabled = True
        self.atlasInputSelector.showHidden = False
        self.atlasInputSelector.showChildNodeTypes = False
        self.atlasInputSelector.setMRMLScene(slicer.mrmlScene)
        self.atlasInputSelector.setToolTip("Pick the volumetric Atlas.")
        self.zoneDetectionLayout.addRow("Volumetric parcels: ", self.atlasInputSelector)

        self.dialog = qt.QFileDialog()
        self.dialog.setFileMode(qt.QFileDialog.AnyFile)
        self.dialog.setToolTip("Pick the input to the algorithm.")

        self.fidsSelectorZone = slicer.qMRMLNodeComboBox()
        self.fidsSelectorZone.nodeTypes = (("vtkMRMLMarkupsFiducialNode"), "")
        self.fidsSelectorZone.selectNodeUponCreation = False
        self.fidsSelectorZone.addEnabled = False
        self.fidsSelectorZone.removeEnabled = False
        self.fidsSelectorZone.noneEnabled = True
        self.fidsSelectorZone.setMRMLScene(slicer.mrmlScene)
        self.fidsSelectorZone.setToolTip("Select a fiducial list")
        self.zoneDetectionLayout.addRow("Fiducial : ", self.fidsSelectorZone)

        self.lutSelector = qt.QComboBox()
        # instead of filling hardwired values
        # we can check share/Freesurfer folder and
        # fill selector with available files
        self.lutSelector.addItem('FreeSurferColorLUT20120827')
        self.lutSelector.addItem('FreeSurferColorLUT20060522')
        self.lutSelector.addItem('FreeSurferColorLUT20150729')
        self.lutSelector.addItem('Simple_surface_labels2002')


        self.ROISize = qt.QLineEdit("7")
        self.ROISize.setToolTip("Define side length of cubic region centered in contact centroid")
        self.ROISize.setInputMask("D")

        # Run Zone Detection button
        self.zoneButton = qt.QPushButton("Apply")
        self.zoneButton.toolTip = "Run the algorithm."
        self.zoneButton.enabled = True

        self.zoneDetectionLayout.addRow("Spherical Region Side Length:", self.ROISize)
        self.zoneDetectionLayout.addRow(self.lutSelector)
        self.zoneDetectionLayout.addRow(self.zoneButton)

        if atlasNode:
            self.atlasInputSelector.setCurrentNode(atlasNode)
        if reconFileNode:
            self.fidsSelectorZone.setCurrentNode(reconFileNode)

        # connections
        self.zoneButton.connect('clicked(bool)', self.onZoneButton)

    #######################################################################################
    ###  onZoneButton                                                                 #####
    #######################################################################################
    def onZoneButton(self):
        slicer.util.showStatusMessage("START Zone Detection")
        print ("RUN Zone Detection Algorithm")
        BrainZoneDetectorLogic().runZoneDetection(self.fidsSelectorZone.currentNode(), \
                                                  self.atlasInputSelector.currentNode(), \
                                                  self.lutPath, int(self.ROISize.text),self.lutSelector.currentIndex)
        print ("END Zone Detection Algorithm")
        slicer.util.showStatusMessage("END Zone Detection")

    def cleanup(self):
        pass


#########################################################################################
####                                                                                 ####
#### BrainZoneDetectorLogic                                                          ####
####                                                                                 ####
#########################################################################################
class BrainZoneDetectorLogic(ScriptedLoadableModuleLogic):
    """
  """

    def __init__(self):
        # Create a Progress Bar
        self.pb = qt.QProgressBar()

    def runZoneDetection(self, fids, inputAtlas, colorLut, sideLength,lutIdx):
        # initialize variables that will hold the number of fiducials
        nFids = fids.GetNumberOfFiducials()
        # the volumetric atlas
        atlas = slicer.util.array(inputAtlas.GetName())
        # an the transformation matrix from RAS coordinte to Voxels
        ras2vox_atlas = vtk.vtkMatrix4x4()
        inputAtlas.GetRASToIJKMatrix(ras2vox_atlas)

        # read freesurfer color LUT. It could possibly
        # already exists within 3DSlicer modules
        # but in python was too easy to read if from scratch that I simply
        # read it again.
        # FSLUT will hold for each brain area its tag and name
        FSLUT = {}
        with open(colorLut[lutIdx], 'r') as f:
            for line in f:
                if not re.match('^#', line) and len(line) > 10:
                    lineTok = re.split('\s+', line)
                    FSLUT[int(lineTok[0])] = lineTok[1]

        with open(os.path.join(os.path.dirname(__file__), './Resources/parc_fullnames.json')) as dataParcNames:
            parcNames = json.load(dataParcNames)

        with open(os.path.join(os.path.dirname(__file__), './Resources/parc_shortnames.json')) as dataParcAcronyms:
            parcAcronyms = json.load(dataParcAcronyms)

        # Initialize the progress bar pb
        self.pb.setRange(0, nFids)
        self.pb.show()
        self.pb.setValue(0)

        # Update the app process events, i.e. show the progress of the
        # progress bar
        slicer.app.processEvents()

        listParcNames = [x for v in parcNames.values() for x in v]
        listParcAcron = [x for v in parcAcronyms.values() for x in v]

        for i in xrange(nFids):
            # update progress bar
            self.pb.setValue(i + 1)
            slicer.app.processEvents()

            # Only for Active Fiducial points the GMPI is computed
            if fids.GetNthFiducialSelected(i) == True:

                # instantiate the variable which holds the point
                currContactCentroid = [0, 0, 0]

                # copy current position from FiducialList
                fids.GetNthFiducialPosition(i, currContactCentroid)

                # append 1 at the end of array before applying transform
                currContactCentroid.append(1)

                # transform from RAS to IJK
                voxIdx = ras2vox_atlas.MultiplyFloatPoint(currContactCentroid)
                voxIdx = numpy.round(numpy.array(voxIdx[:3])).astype(int)

                # build a -sideLength/2:sideLength/2 linear mask
                mask = numpy.arange(int(-numpy.floor(sideLength / 2)), int(numpy.floor(sideLength / 2) + 1))

                # get Patch Values from loaded Atlas in a sideLenght**3 region around
                # contact centroid and extract the frequency for each unique
                # patch Value present in the region

                [X, Y, Z] = numpy.meshgrid(mask, mask, mask)
                maskVol = numpy.sqrt(X ** 2 + Y ** 2 + Z ** 2) <= numpy.floor(sideLength / 2)

                X = X[maskVol] + voxIdx[0]
                Y = Y[maskVol] + voxIdx[1]
                Z = Z[maskVol] + voxIdx[2]

                patchValues = atlas[Z, Y, X]

                # Find the unique values on the matrix above
                uniqueValues = numpy.unique(patchValues)

                # Flatten the patch value and create a tuple
                patchValues = tuple(patchValues.flatten(1))

                voxWhite = patchValues.count(2) + patchValues.count(41)
                voxGray = len(patchValues) - voxWhite
                PTD = float(voxGray - voxWhite) / (voxGray + voxWhite)

                # Create an array of frequency for each unique value
                itemfreq = [patchValues.count(x) for x in uniqueValues]

                # Compute the max frequency
                totPercentage = numpy.sum(itemfreq)

                # Recover the real patch names
                patchNames = [re.sub('((ctx_.h_)|(Right|Left)-(Cerebral-)?)', '', FSLUT[pValues]) for pValues in uniqueValues]
                patchAcron = list()
                for currPatchName in patchNames:
                    currPatchAcron = ''
                    for name, acron in zip(listParcNames, listParcAcron):
                        if currPatchName == name:
                            currPatchAcron = acron

                    if currPatchAcron:
                        patchAcron.append(currPatchAcron)
                    else:
                        patchAcron.append(currPatchName)

                # Create the zones
                parcels = dict(zip(itemfreq, patchAcron))

                # prepare parcellation string with percentage of values
                # within the ROI centered in currContactCentroid
                # [round( float(k) / totPercentage * 100 ) for k,v in parcels.iteritems()]
                ordParcels = collections.OrderedDict(sorted(parcels.items(), reverse=True))
                anatomicalPositionsString = [','.join([v, str(round(float(k) / totPercentage * 100))]) for k, v in
                                             ordParcels.iteritems()]
                anatomicalPositionsString.append('PTD, {:.2f}'.format(PTD))

                # Preserve if some old description was already there
                fids.SetNthMarkupDescription(i, fids.GetNthMarkupDescription(i) + " " + ','.join(
                    anatomicalPositionsString))
