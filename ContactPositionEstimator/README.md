################################################
### INTRODUCTION
################################################
DEETO is a 3D slicer[1] module for the automatic segmentation of deep
intracranial electrode contats. [TODO] more intro

This file has been organized in the following sections:

1. MODULE CONFIGURATION
2. HOW TO ADD DEETO IN SLICER
3. A QUICK INTRODUCTION TO DEETO USE
4. MISCELLANEAS
5. DIRECTORY STRUCTURE
6. BIBLIOGRAFY

################################################
### 1 MODULE CONFIGURATION 
################################################
DEETO needs deeto-slicer (deetoS), a simplified (and branch) version
of the command line tool named deeto[2]. deetoS can be downloaded from
[3] For simplicity we provide different precompiled static versions of
deetoS that can be found in the directory DEETO/deetoS/.

################################################
#### 1.1 CONFIGURATION UNDER LINUX
################################################
DO NOTHING

################################################
#### 1.2 CONFIGURATION UNDER WINDOWS 64 bits
################################################
1. Check if the Visual Studio 2015 redistributables components have
   been installed. If they are not installed, please install them at[4] 
2. Modify the config file under "DEEETO/Config/deeto.config" by
   replacing the line
      {"deeto": "DeetoS/deeto-static-linux64"} 
   with the line
      {"deeto": "DeetoS/deeto-winx64-static-vs2015.exe"}
3. If there is no deetoS SO version for your system, please download
   the deetoS sources from[3] and compile it following the README
   instructions. Once you have created the executable, say it
   "deeto-exec", then add it to the DEETO/DeetoS/" directory and
   modify the config file "DEEETO/Config/deeto.config" by replacing
   the line
      {"deeto": "DeetoS/deeto-static-linux64"} 
   with the line
      {"deeto": "DeetoS/deeto-winx64-static-vs2015.exe"} (or with the name you give to it.

################################################
#### 1.3 CONFIGURATION UNDER MAC OX	
################################################
TODO

################################################
### 2 HOW TO ADD DEETO IN SLICER
################################################
DEETO has been tested with Slicer 4.5 version under both Linux Ubuntu
and Windows 8.1 64 bits. The procedure is the same for both Windows
and Linux. In order to include DEETO as Slicer module you should:

1. Run Slicer
2. Under "Edit->Application Settings" select Modules from the left list
3. In "Additional module paths" select ">>" to show the Frame "Paths"
4. Push "Add" button and select "SEEGA/DEETO/DEETO.py"
5. Restart Slicer 
6. Among Modules you should find DEETO.

################################################
### 3 A QUICK INTRODUCTION TO DEETO USE
################################################

DEETO is divided into two "Collapsible buttons", namely:

1. DEETO - Configuration
2. DEETO - Segmentation

################################################
#### 3.1) DEETO - Configuration
################################################

Here it is possible to change temporarily the deetoS executable path,
by using the dialog box "..." . It is an alternative to the 1.2.2
step, but please notice that this change is temporary, once Slicer is
restarted it is again setted as in its configuration file.

################################################
#### 3.2 DEETO - Segmentation
################################################
In order to segment a set of contacts DEETO follows this procedure:

1. Add a fiducial files to the scene
2. Add a CT volume to the scene. WARNING: the volume and the fiducials
   must be on the same space
3. From the Markups Module choose which electrodes you want to
   segment, by selecting/unselecting points in the Markups module
4. Go to DEETO Module, then select a fiducial file from the "Fiducial
   List". Once selected automatically the electrodes that can be
   segmented appear in the list below the Selection List.  For each
   electrode you can select which type of the electrode deetoS should
   look for and the checkbox Tail and Head can be checked. This two
   flags tells to DEETO that Tail and Head have been carefully choosen
   (if checked) and DEETO should not look for them. 
5. Once the Fiducial List has been choosen, the "CT Volume" list also
   appears, and you should choose a volume to segment.
6. Finally push "Start Segmentation" button to start the segmentation
7. Once deetoS complete the segmentation a new Markups fiducial file
   named "recon" is created and automatically added to the scene.
8. Refine the Segmentation: it may be the case that some electrodes
   have not been correctly segmentated. In this case the most big
   problem should be the search of the tail and/or the head. So if you
   want to refine the search please select only the electrode of which
   you want to refine the Segmentation, and of these electrodes checks
   the Tail and Head check box. Please be warned that:
   a. You should be sure that the entry and target points of each
      electrodes are placed correctly if Tail and Head are checked
   b. A new fiducial with the selected electrodes segmented is created
      with the same name of the previous one.

################################################
#### 4. Miscellanea 
################################################

################################################
#### 4.1 Fiducial points name convention
################################################
At the moment DEETO assume that each electrode has an entry and
a target point. The name of each point has to follow these rules:
- it can be a single letter (not strict) followed by a ' (optionally)
- optionally it can be followed by the suffix  1
- optionally it can be followed by the suffix "_1"

Moreover

- It is not necessary to distinguish beetween target and entry
- Target and Entry of each electrode should be named with the same letter

Please notice that if the rules above are not respected 
deeto can not start the search.

################################################
#### 4.2 Electrode Types
################################################
TODO

##################################################
### 5 DIRECTORY STRUCTURE
################################################

- \<home\> refers to the place where you put DEETO directory
- \<home\>/README.md : this file
- \<home\>/DEETO.py, : python script for 3D-SLICER
- \<home\>/DEETO.pyc ... ?
- \<home\>/Config/   : contains configuration files used by the DEETO.py (deeto.config, electrodes.config)
- \<home\>/DeetoS/   : contains the deeto-slicer static executables 
- \<home\>/Testing/  : ... ?
- \<home\>/Tmp/      : it may contains some temporary files used by deeto.   



################################################
### 6 BIBLIOGRAFY
################################################

[1] http://www.slicer.org

[2] https://github.com/mnarizzano/DEETO

[3] https://github.com/mnarizzano/DEETO/tree/deeto-slicer

[4] https://www.microsoft.com/it-it/download/details.aspx?id=48145
    (4/Feb/2016 last checked)