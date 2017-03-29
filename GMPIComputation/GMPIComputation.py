import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import re
import numpy

#########################################################################################
####                                                                                 ####
#### GMPIComputation  ###################################################################
####                                                                                 ####
#########################################################################################
class GMPIComputation(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "3. GMPIComputation" # TODO make this more human readable by adding spaces
        self.parent.categories = ["SEEGA"]
        self.parent.dependencies = []
        self.parent.contributors = ["Gabriele Arnulfo (Univ. Genoa) & Massimo Narizzano (Univ. Genoa)"]
        self.parent.helpText = """
    Compute the Gray Matter Proximity Index starting  .....
    """
        self.parent.acknowledgementText = """
    """

    #########################################################################################
####                                                                                 ####
#### GMPIComputationWidget ########## ###################################################
####                                                                                 ####
#########################################################################################
class GMPIComputationWidget(ScriptedLoadableModuleWidget):

    #######################################################################################
    ### setup
    #######################################################################################
    def setup(self):
        self.developerMode = True
        ScriptedLoadableModuleWidget.setup(self)

        # inspect current Scene and search for files called ?h_pial and ?h_white
        # if found fill the lists with relative nodes
        lhPialNode = slicer.mrmlScene.GetNodesByName('lh_pial').GetItemAsObject(0)
        rhPialNode = slicer.mrmlScene.GetNodesByName('rh_pial').GetItemAsObject(0)
        lhWhiteNode = slicer.mrmlScene.GetNodesByName('lh_white').GetItemAsObject(0)
        rhWhiteNode = slicer.mrmlScene.GetNodesByName('rh_white').GetItemAsObject(0)
        reconFileNode= slicer.mrmlScene.GetNodesByName('recon').GetItemAsObject(0)


        self.gmpiCB = ctk.ctkCollapsibleButton()
        self.gmpiCB.text = "GMPI Computation"
        self.layout.addWidget(self.gmpiCB)
        self.gmpiFL = qt.QFormLayout(self.gmpiCB)

        #### Left Pial selection box
        self.leftPialCBox = slicer.qMRMLNodeComboBox()
        self.leftPialCBox.nodeTypes = ( ("vtkMRMLModelNode"), "" )
        self.leftPialCBox.selectNodeUponCreation = True
        self.leftPialCBox.addEnabled = False
        self.leftPialCBox.removeEnabled = False
        self.leftPialCBox.noneEnabled = True
        self.leftPialCBox.showHidden = False
        self.leftPialCBox.showChildNodeTypes = False
        self.leftPialCBox.setMRMLScene( slicer.mrmlScene )
        self.leftPialCBox.setToolTip( "Pick the left pial." )
        self.gmpiFL.addRow("Left Pial: ", self.leftPialCBox)

        #### Left White selection box
        self.leftWhiteCBox = slicer.qMRMLNodeComboBox()
        self.leftWhiteCBox.nodeTypes = ( ("vtkMRMLModelNode"), "" )
        self.leftWhiteCBox.selectNodeUponCreation = True
        self.leftWhiteCBox.addEnabled = False
        self.leftWhiteCBox.removeEnabled = False
        self.leftWhiteCBox.noneEnabled = True
        self.leftWhiteCBox.showHidden = False
        self.leftWhiteCBox.showChildNodeTypes = False
        self.leftWhiteCBox.setMRMLScene( slicer.mrmlScene )
        self.leftWhiteCBox.setToolTip( "Pick the left pial." )


        #### Right Pial selection box
        self.rightPialCBox = slicer.qMRMLNodeComboBox()
        self.rightPialCBox.nodeTypes = ( ("vtkMRMLModelNode"), "" )
        self.rightPialCBox.selectNodeUponCreation = True
        self.rightPialCBox.addEnabled = False
        self.rightPialCBox.removeEnabled = False
        self.rightPialCBox.noneEnabled = True
        self.rightPialCBox.showHidden = False
        self.rightPialCBox.showChildNodeTypes = False
        self.rightPialCBox.setMRMLScene( slicer.mrmlScene )
        self.rightPialCBox.setToolTip( "Pick the right pial." )
        self.gmpiFL.addRow("Right Pial: ", self.rightPialCBox)

        #### Right White selection box
        self.rightWhiteCBox = slicer.qMRMLNodeComboBox()
        self.rightWhiteCBox.nodeTypes = ( ("vtkMRMLModelNode"), "" )
        self.rightWhiteCBox.selectNodeUponCreation = True
        self.rightWhiteCBox.addEnabled = False
        self.rightWhiteCBox.removeEnabled = False
        self.rightWhiteCBox.noneEnabled = True
        self.rightWhiteCBox.showHidden = False
        self.rightWhiteCBox.showChildNodeTypes = False
        self.rightWhiteCBox.setMRMLScene( slicer.mrmlScene )
        self.rightWhiteCBox.setToolTip( "Pick the right pial." )
        self.gmpiFL.addRow("Right White: ", self.rightWhiteCBox)




        self.gmpiFL.addRow("Left White: ", self.leftWhiteCBox)

        #### Fiducials list Combo Box
        self.fiducialsCBox = slicer.qMRMLNodeComboBox()
        self.fiducialsCBox.nodeTypes = ( ("vtkMRMLMarkupsFiducialNode"), "" )
        self.fiducialsCBox.selectNodeUponCreation = False
        self.fiducialsCBox.addEnabled = False
        self.fiducialsCBox.removeEnabled = False
        self.fiducialsCBox.noneEnabled = True
        self.fiducialsCBox.setMRMLScene( slicer.mrmlScene )
        self.fiducialsCBox.setToolTip("Select a fiducial list")
        self.gmpiFL.addRow("Fiducial : ", self.fiducialsCBox)


        # if nodes already exist load them in ComboBoxes
        if lhWhiteNode:
            self.leftWhiteCBox.setCurrentNode(lhWhiteNode)
        if rhWhiteNode:
            self.rightWhiteCBox.setCurrentNode(rhWhiteNode)
        if rhPialNode:
            self.rightPialCBox.setCurrentNode(rhPialNode)
        if lhPialNode:
            self.leftPialCBox.setCurrentNode(lhPialNode)

        if reconFileNode:
            self.fiducialsCBox.setCurrentNode(reconFileNode)

        #### GMPI Threshold Slider
        self.gmpiSlider = qt.QSlider(qt.Qt.Horizontal)
        self.gmpiSlider.setMinimum(-9)
        self.gmpiSlider.setMaximum(9)
        self.gmpiSlider.setValue(-3)

        #### GMPI Spin Box
        self.gmpiSpinBox = qt.QDoubleSpinBox()
        self.gmpiSpinBox.setRange(-1, 1)
        self.gmpiSpinBox.setSingleStep(0.1)
        self.gmpiSpinBox.setValue(float(self.gmpiSlider.value)/10)

        #### GMPI Slider e SpinBox Layout
        self.gmpiverticalLayout = qt.QHBoxLayout()

        self.gmpiverticalLayout.addWidget(self.gmpiSlider)
        self.gmpiverticalLayout.addWidget(self.gmpiSpinBox)
        self.gmpiFL.addRow("GMPI Threshold : ", self.gmpiverticalLayout)

        # GMPI Computation Detection button
        self.gmpiPB = qt.QPushButton("Apply")
        self.gmpiPB.toolTip = "Run the algorithm."
        self.gmpiPB.enabled = True

        # Create montage files
        self.montagePB = qt.QPushButton("Create Montage")
        self.montagePB.toolTip = "Create Montage"
        self.montagePB.enabled = True

        #### Aggiungo il bottone al layout
        self.gmpiFL.addRow(self.gmpiPB)
        self.gmpiFL.addRow(self.montagePB)

        # connections
        self.gmpiPB.connect('clicked(bool)', self.onGMPIComputation)
        self.montagePB.connect('clicked(bool)', self.onMontageCreation)

        self.gmpiSpinBox.valueChanged.connect(self.onSpinBoxValueChange)
        self.gmpiSlider.valueChanged.connect(self.onSliderValueChange)



    #######################################################################################
    ###  onGMPIComputation
    #######################################################################################
    def onGMPIComputation(self):
        slicer.util.showStatusMessage("START GMPI Computation")
        print "RUN GMPI Computation"
        GMPIComputationLogic().runGMPIComputation(self.fiducialsCBox.currentNode(), \
                                                  self.leftPialCBox.currentNode(), \
                                                  self.rightPialCBox.currentNode(), \
                                                  self.leftWhiteCBox.currentNode(), \
                                                  self.rightWhiteCBox.currentNode())


        print "END GMPI Computation"
        slicer.util.showStatusMessage("END GMPI Computation")

    def onMontageCreation(self):
        slicer.util.showStatusMessage("START Montage Creation")
        print "RUN Montage Creation"
        GMPIComputationLogic().runMontageCreation(self.fiducialsCBox.currentNode(), \
                                                  self.gmpiSlider)


        print "END Montage Creation"
        slicer.util.showStatusMessage("END Montage Creation")
    #######################################################################################
    ###  onSliderValueChange and onSpinBoxValueChange
    #######################################################################################
    def onSliderValueChange(self):
        self.gmpiSpinBox.setValue(float(self.gmpiSlider.value)/10)

    def onSpinBoxValueChange(self):
        self.gmpiSlider.setValue(float(self.gmpiSpinBox.value)*10)



#########################################################################################
####                                                                                 ####
#### GMPIComputationLogic  ##############################################################
####                                                                                 ####
#########################################################################################
class GMPIComputationLogic(ScriptedLoadableModuleLogic):
    """
    """
    #######################################################################################
    ###  __init___
    #######################################################################################
    def __init__(self):
        # Create a Progress Bar
        self.pb = qt.QProgressBar()

    #######################################################################################
    ###  findTheNearestVertex
    #######################################################################################
    def findNearestVertex(self,contact, surfaceVertices):
        dist = numpy.sqrt( numpy.sum( (contact - surfaceVertices)**2,axis=1) )
        return (surfaceVertices[ dist.argmin(),:],dist.argmin())

    #######################################################################################
    ###  computeGMPI
    #######################################################################################
    def computeGmpi(self,contact,pial,white):
        return (numpy.dot( (contact-white) , (pial - white) ) / numpy.linalg.norm((pial - white))**2 )

    #######################################################################################
    ###  runGMPIComputation
    #######################################################################################
    def runGMPIComputation(self,fids,leftPial,rightPial,leftWhite,rightWhite):

        # Check that the Fiducial has been selected
        if (fids == None):
            # notify error
            slicer.util.showStatusMessage("Error, No Fiducial selected")
            return

        # LEFT/RIGHT PIAL/WHITE must be selected
        if ((leftPial == None) or (rightPial == None) or \
                    (leftWhite == None) or (rightWhite == None)):
            # notify error
            slicer.util.showStatusMessage("Error, please select the four surfaces!")
            return

        # Set the parameters of the progess bar and show it
        self.pb.setRange(0,fids.GetNumberOfFiducials())
        self.pb.show()
        self.pb.setValue(0)
        slicer.app.processEvents()

        # Compute GMPI for each fiducial
        for i in xrange(fids.GetNumberOfFiducials()):
            # update progress bar
            self.pb.setValue(i+1)
            slicer.app.processEvents()

            # Only for Active Fiducial points the GMPI is computed
            if fids.GetNthFiducialSelected(i) == True:

                # Check if it is a left or right channel, by reading the contact
                # label. If the label contain the '(prime) char then the contact
                # is in the left emisphere, right otherwise
                #[TODO]: better way to do it?
                # within 3DSlicer volumes are represented in RAS/RAI (check) so
                # one can actually think of using channel position (e.g. positive
                # or negative x respect to the volume centre)
                # instead of using contact names (which
                # may significantly vary among centres)
                chLabel = fids.GetNthFiducialLabel(i)
                if re.search('^\w\d+',chLabel) is None:
                    # left channel
                    pial = leftPial.GetPolyData()
                    white = leftWhite.GetPolyData()
                else:
                    # right channel
                    pial = rightPial.GetPolyData()
                    white = rightWhite.GetPolyData()

                # we need to convert vtk object to numpy in order
                # to take advantage of numpy functions to compute the minimum distance
                pialVertices = vtk.util.numpy_support.vtk_to_numpy(pial.GetPoints().GetData())
                whiteVertices = vtk.util.numpy_support.vtk_to_numpy(white.GetPoints().GetData())

                # instantiate the variable which holds the point
                currContactCentroid = [0,0,0]

                # copy current position from FiducialList
                fids.GetNthFiducialPosition(i,currContactCentroid)

                # find nearest vertex coordinates
                [whiteNearVtx, whiteNearIdx] = self.findNearestVertex(currContactCentroid,whiteVertices)
                pialNearVtx = pialVertices[whiteNearIdx]

                # print ",".join([str(pialNearVtx),str(whiteNearVtx),str(currContactCentroid)])
                gmpi=float("{0:.3f}".format(self.computeGmpi(currContactCentroid,pialNearVtx,whiteNearVtx)))
                print fids.GetNthFiducialLabel(i)+" gmpi: "+ str(gmpi)

                self.descr = fids.GetNthMarkupDescription(i)
                if self.descr[-1:] is ',':
                    fids.SetNthMarkupDescription(i,' '.join([self.descr,'GMPI,',str(gmpi)]))
                else:
                    fids.SetNthMarkupDescription(i, ' '.join([self.descr, ', GMPI,', str(gmpi)]))




    def runMontageCreation(self,fids,gmpiThreshold):

        # class Implant:
        #     def __init__(self, electrodes=None):
        #         if electrodes:
        #             self.electrodes = electrodes
        #         else:
        #             self.electrodes = list()
        #         self.distances = numpy.ndarray()
        #
        #     def computeDistances(self):
        #         i = 0
        #         j = 0
        #         for el1 in self.electrodes:
        #             for el2 in self.electrodes:
        #                 self.distances[i,j] = numpy.sqrt( numpy.sum( (el1.chpos - el2.chpos)**2,axis=1) )
        #                 i = i +1
        #                 j = j +1



        class Electrode:
            def __init__(self, label, chpos=None, gmpi=None, ptd=None, isSubCtx=False):
                self.label = label
                self.gmpi = gmpi
                self.ptd = ptd
                self.chpos = chpos
                self.isSubCtx = isSubCtx

            def __add__(self, other):
                currElecName = re.match("[A-Z]+[']?",self.label).group(0)
                currChanNum = re.search("\d+", self.label).group(0)
                refLabel = currElecName + str(int(currChanNum) + 1)
                return refLabel


        # create table for BP and add it to the active scene
        bpTableNode = slicer.vtkMRMLTableNode()
        bpTableNode.SetName("BP")
        bpTableNode.AddColumn()
        bpTableNode.AddColumn()
        bpTableNode.AddColumn()
        slicer.mrmlScene.AddNode(bpTableNode)

        # cwTableNode = slicer.vtkMRMLTableNode()
        # cwTableNode.SetName("CW")
        # cwTableNode.AddColumn()
        # cwTableNode.AddColumn()
        # cwTableNode.AddColumn()
        # slicer.mrmlScene.AddNode(bpTableNode)


        # read fids and populate a dictionary
        implant = dict()
        for elIdx in xrange(1,fids.GetNumberOfFiducials()):
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

            implant[fids.GetNthFiducialLabel(elIdx)] = (chpos, gmpi, ptd, isSubCtx)

        # implant.computeDistances()

        # Create bipolar first
        row = 0
        for srcLabel,info in implant.iteritems():
            a = Electrode(srcLabel)
            refLabel = a+1

            if refLabel in implant.keys():
                bpLabel = srcLabel+'-'+refLabel
                bpTableNode.AddEmptyRow()
                bpTableNode.SetCellText(row, 0, bpLabel)
                bpTableNode.SetCellText(row, 1, srcLabel)
                bpTableNode.SetCellText(row, 2, '-'+refLabel)
                row = row + 1

        # Create Closest White scheme
