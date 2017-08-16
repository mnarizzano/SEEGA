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
####  Contact Position Estimator                                                     ####
####                                                                                 ####
#########################################################################################
class Finalizer(ScriptedLoadableModule):
    #####################################################################################
    #### __init__
    #####################################################################################
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "4. Finalizer"
        self.parent.categories = ["SEEGA"]
        self.parent.dependencies = []
        self.parent.contributors = ["G. Arnulfo (Univ. Genoa) & M. Narizzano (Univ. Genoa)"]
        self.parent.helpText = """seeg electroDE rEconstruction TOol (ContactPositionEstimator):
                    This tool reconstructs the position of SEEG electrode contacts
                    from a post-implant Cone-beam CT scan."""
        self.parent.acknowledgementText = """This file was originally developed by Gabriele Arnulfo & Massimo Narizzano"""

        self.channelFile = ''




#########################################################################################
####                                                                                 ####
####  FinalizerWidget                                                 ####
####                                                                                 ####
#########################################################################################
class FinalizerWidget(ScriptedLoadableModuleWidget):
    #######################################################################################
    ### setup
    #######################################################################################


    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        #### Collapsible Button --- montage
        self.finalizerCBSave = ctk.ctkCollapsibleButton()
        self.finalizerCBSave.text = "1. Montage"
        self.finalizerCBSave.contentsLineWidth = 1
        self.layout.addWidget(self.finalizerCBSave)

        #### Collapsible Button layout
        self.finalizerFLSave = qt.QFormLayout(self.finalizerCBSave)

        self.tableBox = slicer.qMRMLNodeComboBox()
        self.tableBox.nodeTypes = (("vtkMRMLMarkupsFiducialNode"), "")
        self.tableBox.selectNodeUponCreation = False
        self.tableBox.addEnabled = False
        self.tableBox.removeEnabled = False
        self.tableBox.noneEnabled = True
        self.tableBox.setMRMLScene(slicer.mrmlScene)
        self.tableBox.setToolTip("Select a fiducial list")

        # Create montage files
        # NOTE: TODO fix this using qSlicerDataDialog i.e. add the 21E file format
        #   to the supported file formats in slicer, implement a reader that converts the
        #   21E to a markup fiducial list.
        self.channelFileTB = qt.QToolButton()
        self.channelFileTB.setText("...")
        self.channelFileTB.toolTip = "Channel File"
        self.channelFileTB.enabled = True
        self.channelFileTB.connect('clicked(bool)', self.onChannelFileTB)

        #### Line Edit button, where the executable path is shown
        self.channelFileLE = qt.QLineEdit()
        self.channelFileLE.setDisabled(True)
        self.channelFileLE.setMaximumWidth(200)
        self.channelFileLE.setFixedWidth(300)

        #### Buttons Layout
        self.channelFileHBL = qt.QHBoxLayout()
        self.channelFileHBL.addWidget(self.channelFileLE)
        self.channelFileHBL.addWidget(self.channelFileTB)

        self.saveMontagePB = qt.QPushButton("Save Montage")
        self.saveMontagePB.toolTip = "Save Montage"
        self.saveMontagePB.enabled = False
        self.saveMontagePB.connect('clicked(bool)', self.onSaveMontageClick)

        self.createMontagePB = qt.QPushButton("Create Montage")
        self.createMontagePB.toolTip = "Create Montage"
        self.createMontagePB.enabled = True
        self.createMontagePB.connect('clicked(bool)', self.onMontageCreation)

        self.finalizerFLSave.addRow(self.channelFileHBL)
        self.finalizerFLSave.addWidget(self.tableBox)

        self.finalizerFLSave.addWidget(self.createMontagePB)
        self.finalizerFLSave.addWidget(self.saveMontagePB)


        #### Collapsible Button --- Split Fiducial
        self.finalizerCBSplit = ctk.ctkCollapsibleButton()
        self.finalizerCBSplit.text = "2. Split Fiducials"
        self.finalizerCBSplit.contentsLineWidth = 1
        self.layout.addWidget(self.finalizerCBSplit)
        #### Collapsible Button layout
        self.finalizerFLSplit = qt.QFormLayout(self.finalizerCBSplit)


        # SPLIT Fiducial Combobox
        self.fiducialSplitBox = slicer.qMRMLNodeComboBox()
        self.fiducialSplitBox.nodeTypes = (("vtkMRMLMarkupsFiducialNode"), "")
        self.fiducialSplitBox.selectNodeUponCreation = False
        self.fiducialSplitBox.addEnabled = False
        self.fiducialSplitBox.removeEnabled = False
        self.fiducialSplitBox.noneEnabled = True
        self.fiducialSplitBox.setMRMLScene(slicer.mrmlScene)
        self.fiducialSplitBox.setToolTip("Select a fiducial list")

        # SPLIT Fiducials Button
        self.splitFiducialPB = qt.QPushButton("Split Fiducial List")
        self.splitFiducialPB.toolTip = "Split Fiducial file, one for each electrode"
        self.splitFiducialPB.enabled = True
        self.splitFiducialPB.connect('clicked(bool)',self.onsplitFiducialClick)

        self.finalizerFLSplit.addWidget(self.fiducialSplitBox)
        self.finalizerFLSplit.addWidget(self.splitFiducialPB)

        # Collapsible Button Layout - Report
        self.finalizerCBDoc = ctk.ctkCollapsibleButton()
        self.finalizerCBDoc.text = "3. Report"
        self.finalizerCBDoc.contentsLineWidth = 1
        self.layout.addWidget(self.finalizerCBDoc)

    #######################################################################################
    # onSplitFiducialClick
    #######################################################################################
    def onsplitFiducialClick(self):
        """ onSplitFiducialClick  """

        def uniquify(seq):
            # order preserving
            checked = []
            for e in seq:
                if e not in checked:
                    checked.append(e)
            return checked

        # read get the fiducial file reconstructed
        fiducialData = self.fiducialSplitBox.currentNode()

        # Get channel names
        chLabels = [fiducialData.GetNthFiducialLabel(i) for i in xrange(fiducialData.GetNumberOfFiducials())]

        # Extract electrode name from channel names
        elLabels = [re.match('[A-Z]*\'?', x).group(0) for x in chLabels]
        uniqueElLabels = uniquify(elLabels)

        # count for each electrode name the number of segmented contacts
        elChCounts = [elLabels.count(x) for x in uniqueElLabels]

        print "SPLITTING FIDUCIAL FILES"

        offset = 0
        for elIdx in xrange(len(uniqueElLabels)):

            elLabel = uniqueElLabels[elIdx]
            newFids = slicer.util.getNode(slicer.modules.markups.logic().AddNewFiducialNode(elLabel))

            for chIdx in xrange(elChCounts[elIdx]):
                # we have to create a separate fiducial file for
                # each electrode and populate with corresponding
                # channel positions and labels
                P = [0.0, 0.0, 0.0]
                fiducialData.GetNthFiducialPosition(chIdx + offset, P)
                newFids.AddFiducial(P[0], P[1], P[2])
                newFids.SetNthFiducialLabel(chIdx, fiducialData.GetNthFiducialLabel(chIdx + offset))
                newFids.SetNthMarkupDescription(chIdx, fiducialData.GetNthMarkupDescription(chIdx + offset))

            slicer.modules.markups.logic().SetAllMarkupsLocked(newFids, True)
            offset += elChCounts[elIdx]
        print "DONE"
    def onSaveMontageClick(self):
        # read the table
        # save it as brainstom compliant file
        fileDialog = qt.QFileDialog()
        fileDialog.setFileMode(0)

        basePath = fileDialog.getExistingDirectory()

        referencingSchemeNode = self.tableBox.currentNode()
        rows = referencingSchemeNode.GetNumberOfRows()

        fileName = os.path.join(basePath,referencingSchemeNode.GetName()+'.mon')

        with open(fileName,'w') as f:
            for rowIdx in range(0,rows):

                strLine = referencingSchemeNode.GetCellText(rowIdx,0)+":"+\
                          referencingSchemeNode.GetCellText(rowIdx,1)+","+\
                          referencingSchemeNode.GetCellText(rowIdx,2)+"\n"

                f.write(strLine)


        return True
    def onMontageCreation(self):
        slicer.util.showStatusMessage("START Montage Creation")
        print "RUN Montage Creation"
        FinalizerLogic().runMontageCreation(self.tableBox.currentNode(),self.channelFile)


        print "END Montage Creation"
        self.saveMontagePB.enabled = True
        slicer.util.showStatusMessage("END Montage Creation")
    def onChannelFileTB(self):
        fileName = qt.QFileDialog.getOpenFileName()
        self.channelFileLE.setText(fileName)
        self.channelFile = fileName


# #########################################################################################
# #
# # FinalizerLogic
# #
# #########################################################################################
class FinalizerLogic(ScriptedLoadableModuleLogic):

    def __init__(self):
        self.pb = qt.QProgressBar()

    def runMontageCreation(self,fids,channelFile):

        class Implant:
            def __init__(self, electrodes=None):
                if electrodes:
                    self.electrodes = electrodes
                    self.distances = numpy.ndarray(len(electrodes))
                else:
                    self.electrodes = list()
                    self.distances = numpy.ndarray((1,1))

            def append(self,electrode):
                self.electrodes.append(electrode)

            def computeDistances(self):
                # re-allocare distances matrix
                self.distances = numpy.ndarray( ( len(self.electrodes),len(self.electrodes) ) )
                i = 0
                j = 0
                for el1 in self.electrodes:
                    for el2 in self.electrodes:
                        # need to check whether the two channels are recording
                        # from the same hemisphere ... WHY? I mean volume conduction is
                        # volume conduction ... so does it matter much if ref is in the other hemisphere
                        # would it be better to reduce ref-ch distance instead of preserving
                        # laterality?

                        if (el1.isRight and el2.isRight) or (el1.isLeft and el2.isLeft):
                            self.distances[i,j] = numpy.sqrt(numpy.sum((numpy.array(el1.chpos) - numpy.array(el2.chpos))**2))
                        else:
                            self.distances[i,j] = 1000

                        i += 1
                    j += 1
                    i = 0

            def find(self,electrode):
                try:
                    return self.electrodes.index(electrode)
                except ValueError:
                    return None

            def buildWhiteChannelsList(self):

                whiteReferenceChannels = [ind for ind in xrange(0,len(self.electrodes)) \
                                          if self.electrodes[ind].gmpi < -0.3 and self.electrodes[ind].ptd < 0 \
                                          and not self.electrodes[ind].isSubCtx]
                return whiteReferenceChannels

            def findWhiteReference(self,electrode,gmpiThreshold):
                srcIdx = self.electrodes.index(electrode)
                if not electrode.isSubCtx:
                    refIndices = self.buildWhiteChannelsList()
                    refIdx = refIndices[self.distances[srcIdx,refIndices].argmin()]
                    return self.electrodes[refIdx]
                else:
                    refIndices = self.buildWhiteChannelsList()
                    refIdx = refIndices[self.distances[srcIdx,refIndices].argmin()]
                    return self.electrodes[refIdx]

        class Electrode:
            def __init__(self, label, chpos=None, gmpi=None, ptd=None, isSubCtx=False):
                self.label = label
                self.gmpi = gmpi
                self.ptd = ptd
                self.chpos = chpos
                self.isSubCtx = isSubCtx
                self.isRight = re.search('[A-Z]\d+',label)
                self.isLeft = re.search('[A-Z]\'\d+',label)

            def __add__(self, other):
                currElecName = re.match("[A-Z]+[']?",self.label).group(0)
                currChanNum = re.search("\d+", self.label).group(0)
                refLabel = currElecName + str(int(currChanNum) + 1)
                refElec = Electrode(refLabel)
                return refElec

            def __eq__(self,other):
                if self.label == other.label:
                    return True
                else:
                    return False

            def __str__(self):
                if self.isRight:
                    side = 'r'
                else:
                    side = 'l'
                return self.label+' '+side


        # create table for BP and add it to the active scene
        bpTableNode = slicer.vtkMRMLTableNode()
        bpTableNode.SetName("BP")
        bpTableNode.AddColumn()
        bpTableNode.AddColumn()
        bpTableNode.AddColumn()
        slicer.mrmlScene.AddNode(bpTableNode)

        cwTableNode = slicer.vtkMRMLTableNode()
        cwTableNode.SetName("CW")
        cwTableNode.AddColumn()
        cwTableNode.AddColumn()
        cwTableNode.AddColumn()
        slicer.mrmlScene.AddNode(cwTableNode)

        # read the list of channels which the
        # signals have been recorded from
        channelList = []
        with open(channelFile,"r") as file:
            # skip first line
            file.readline()
            for line in file:
                if '[REFERENCE]' in line:
                    break
                else:
                    channelName = line.split('=')[1]
                    channelName = channelName.strip('\n').strip('\r')
                    channelList.append(channelName)

        # channelList now contains the recorded channels only
        # in the recorded order too

        # read fids and populate a dictionary
        # implantDict = dict()
        implant = Implant()
        # we should iterate the channel list
        # and find relevant information in the fiducial file
        tmpImplant = []
        for elIdx in xrange(0,fids.GetNumberOfFiducials()):
            tmpImplant.append(fids.GetNthFiducialLabel(elIdx))

        for channel in channelList:
            try:
                elIdx = tmpImplant.index(channel)
            except ValueError:
                continue

            if elIdx:
                chpos = [0.0, 0.0, 0.0]
                fids.GetNthFiducialPosition(elIdx,chpos)
                desc = fids.GetNthMarkupDescription(elIdx)
                desc = re.split(',', desc)
                descDict = dict()
                for k,v in zip(desc[::2],desc[1::2]):
                    descDict[k.strip()] = float(v)

                if descDict.has_key('GMPI'):
                    gmpi = descDict['GMPI']
                else:
                    gmpi = numpy.nan
                if descDict.has_key('PTD'):
                    ptd = descDict['PTD']
                else:
                    ptd = numpy.nan

                # we need to separate the anatomical names to differentiate between subcortical
                # and cortical channels.
                isSubCtx = any([descDict.has_key(x) for x in ('Hip','Put','Amy','Cau','Tal')])

                # implantDict[fids.GetNthFiducialLabel(elIdx)] = (chpos, gmpi, ptd, isSubCtx)
                implant.append(Electrode(fids.GetNthFiducialLabel(elIdx),chpos,gmpi,ptd,isSubCtx))
        implant.computeDistances()

        # Create bipolar first
        row = 0
        for srcElec in implant.electrodes:

            refElec = srcElec+1

            if implant.find(refElec):
                bpLabel = srcElec.label+'-'+refElec.label
                bpTableNode.AddEmptyRow()
                bpTableNode.SetCellText(row, 0, str(bpLabel))
                bpTableNode.SetCellText(row, 1, str(srcElec.label))
                bpTableNode.SetCellText(row, 2, str('-'+refElec.label))
                row += 1

        # Create Closest White scheme
        row = 0
        for srcElec in implant.electrodes:

            refElec = implant.findWhiteReference(srcElec,-0.3)
            if refElec and srcElec.gmpi > -0.3:
                cwLabel = srcElec.label + '-' + refElec.label
                cwTableNode.AddEmptyRow()
                cwTableNode.SetCellText(row, 0, str(cwLabel))
                cwTableNode.SetCellText(row, 1, str(srcElec.label))
                cwTableNode.SetCellText(row, 2, str('-' + refElec.label))
                row += 1




