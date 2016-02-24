cmake_minimum_required(VERSION 2.8.9)

project(SEEG Assistant)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/SEEG Assistant")
set(EXTENSION_CATEGORY "SEEG ")
set(EXTENSION_CONTRIBUTORS "John Doe (AnyWare Corp.)")
set(EXTENSION_DESCRIPTION "SEEG Assistan is a framework that aims to assist a neurosurgeon in the analysis of SEEG image data in order to simplify the tasks of a neurophysiologist in the epilepsy surgery. ")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/SEEG Assistant.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/SEEG Assistant/Screenshots/1.png")

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(DEETO)
add_subdirectory(Zone Detector)
add_subdirectory(GMPI Computation)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
