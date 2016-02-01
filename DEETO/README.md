### INTRO
DEETO is a 3D slicer[1] module for the automatic segmentation of deep
intracranial electrode contats. [TODO] more intro

### CONFIGURATION 

DEETO needs deeto-slicer (deetoS), a simplified (and branch) version of the
command line tool named deeto[2]. deetoS can be downloaded from [4]


For simplicity we provide different precompiled static versions of
deetoS that can be found in the directory DEETO/deetoS/.

The module DEETO should run on most of the linux-like platforms. If a
different platform is used some executable are provided in the
DEEETO/deetoS/ directory. In order to change platform the
Config/deeto.config file should be modified by replacing the
"deetoS/deeto-static-linux64" with the own platform one.  DEETO
support the following platforms:

(i) Ubuntu 64 bits "deetoS/deeto-static-linux64"
(ii) Windows 64 bits [TODO]
(iii)Mac OS X 64 bits [TODO]

However if your machine is not listed above you can download the
sources from https://github.com/mnarizzano/DEETO/tree/deeto-slicer,
compile it and modify the Config/deeto.config file with the path to
the executable generated. 

[XXX NOTICE XXX] Please notice that the library used by deetoS on some
platform could be in conflict with 3Dslicer or python: in this case is
preferable to compile it statically. However, in this case you should
first compile the ITK libraries[3] statically. So please follow the
instruction in the deeto-slicer[4] README file.


### DIRECTORIES STRUCTURE and files description

- /. is <home> 
- <home>/README.md : this file
- <home>/DEETO.py, : python script for 3D-SLICER
- <home>/DEETO.pyc ... ?
- <home>/Config/   : contains configuration files used by the DEETO.py (deeto.config, electrodes.config)
- <home>/DeetoS/   : contains the deeto-slicer static executables 
- <home>/Testing/  : ... ?
- <home>/Tmp/      : it may contains some temporary files used by deeto.   



[1] cite 3Dslicer 
[2] https://github.com/mnarizzano/DEETO
[3] http://www.itk.org/ITK/resources/software.html
[4] https://github.com/mnarizzano/DEETO/tree/deeto-slicer
