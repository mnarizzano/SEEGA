# SEEGA

[//]:# (![alt tag](https://raw.githubusercontent.com/mnarizzano/SEEGA/master/SEEG_Assistant.png))

To cite the work please refer to:

1. Narizzano M., Arnulfo G., Ricci S., Toselli B., Canessa A., Tisdall M., Fato M. M., Cardinale F. “SEEG Assistant: a 3DSlicer extension to support epilepsy surgery” BMC Bioinformatics (2017) doi;10.1186/s12859-017-1545-8, In Press
2. Arnulfo G, Narizzano M, Cardinale F, Fato MM, Palva JM. Automatic segmentation of deep intracerebral electrodes in computed tomography scans. BMC Bioinforma. 2015;16(1):99.

## Installation 

Full installation instructions are provided [here](https://github.com/mnarizzano/SEEGA/wiki)

## Background: 
In the evaluation of Stereo-Electroencephalography (SEEG)
signals, the physicist’s workflow involves several operations, including determining
the position of individual electrode contacts in terms of both relationship to grey
or white matter and location in specific brain regions. These operations are (i)
generally carried out manually by experts with limited computer support, (ii)
hugely time consuming, and (iii) often inaccurate, incomplete, and prone to
errors.

## Results: 
In this paper we present SEEG Assistant, a set of tools integrated in a
single 3DSlicer extension, which aims to assist neurosurgeons in the analysis of
post-implant structural data and hence aid the neurophysiologist in the
interpretation of SEEG data. SEEG Assistant consists of (i) a module to localize
the electrode contact positions using imaging data from a thresholded
post-implant CT, (ii) a module to determine the most probable cerebral location
of the recorded activity, and (iii) a module to compute the Grey Matter Proximity
Index, i.e. the distance of each contact from the cerebral cortex, in order to
discriminate between white and grey matter location of contacts. Finally,
exploiting 3DSlicer capabilities, SEEG Assistant offers a Graphical User Interface
that simplifies the interaction between the user and the tools. SEEG Assistant
has been tested on 40 patients segmenting 555 electrodes, and it has been used
to identify the neuroanatomical loci and to compute the distance to the nearest
cerebral cortex for 9626 contacts. We also performed manual segmentation and
compared the results between the proposed tool and gold-standard clinical
practice. As a result, the use of SEEG Assistant decreases the post implant
processing time by more than 2 orders of magnitude, improves the quality of
results and decreases, if not eliminates, errors in post implant processing.

## Conclusions: 
The SEEG Assistant Framework for the first time supports
physicists by providing a set of open-source tools for post-implant processing of
SEEG data. Furthermore, SEEG Assistant has been integrated into 3D Slicer, a
software platform for the analysis and visualization of medical images,
overcoming limitations of command-line tools.
