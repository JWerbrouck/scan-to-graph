# Scan-to-graph framework
Linking Data: Semantic enrichment of the existing building geometry
STG ontology and Rhino Plugin for semantic enrichment with Linked Data technologies.

#created in context of a master dissertation in Engineering: Architecture at Ghent University
(author: Jeroen Werbrouck, supervised by Prof. Pieter Pauwels, Willem Bekers and Mathias Bonduel)

The text of the dissertation is available at the Library of the Department of Architecture and Urban Planning at the Faculty of Engineering and Architecture (https://lib.ugent.be/).

Repository containing the files created for the scan-to-graph framework: the STG ontology for keeping track of modelling assumptions and sources, the plugin source code as a .zip folder and the plugin documentation (installation, dependencies and main functionality) as pdf. The plugin allows to define a building site, building, storeys and spaces, which contain objects or are adjacent to them. The objects (Rhino geometries contained in a Layer) are semantically determined used the Building Product Ontology (https://github.com/pipauwel/product). Further on, assumptions, occlusions or other remarks can be mapped to these objects, in case of an as-is geometric 3D reconstruction project. The plugin makes use of Linked Data (using the Resource Description Framework RDF). The application contains four main tabs: 
1) Project Info Tab: setting the building site, the building itself, its storeys and spaces as well as the georeference coordinates and the GCS for which these geocoordinates are valid.
2) Semantic enrichment tab: to semantically enrichen geometries in a Rhino document
3) Point cloud tab: to import point clouds into different layers (which represent the objects), allowing to subsampling them by calling CloudCompare (stereo) (http://www.danielgm.net/cc/) via the command line.
4) SPARQL query tab: uses Stardog (https://www.stardog.com/) to query the graphs and visualize possible geometric results in the Rhino viewports.

More documentation is available at the "scan-to-graph plugin documentation" pdf.
