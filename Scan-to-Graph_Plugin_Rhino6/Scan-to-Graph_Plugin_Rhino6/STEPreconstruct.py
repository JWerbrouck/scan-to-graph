from rdflib import Namespace
from rdflib.plugins.sparql import prepareQuery
import rdflib
import os
import sys

graph = sys.argv[1]

#graph = str(r"C:\Users\jeroe\Desktop\FINAL_Turtle\CS_PresenceChamber_geom.ttl")
query = str('SELECT ?STEP ?RhinoID WHERE {?entity stg:asSTEP ?STEP . ?entity stg:hasRhinoID ?RhinoID}')

g=rdflib.Graph()
STG = Namespace("https://raw.githubusercontent.com/JWerbrouck/scan-to-graph/master/stg.ttl#")
g.namespace_manager.bind("stg", STG, override=False)

if os.path.exists(graph):
    try:
        file_format = rdflib.util.guess_format(graph)
        g.parse(graph, format=str(file_format))
    except:
        pass

AllFiles = []
STEPQuery = prepareQuery(query,initNs={"stg" : STG})
storeFolder = graph.rstrip(".ttl") + r"/GEOM/reconstruction/"
STEPS = g.query(STEPQuery)
for row in STEPS:
    if not os.path.exists(storeFolder):
        os.makedirs(storeFolder)
    reconstructionFile = str(storeFolder + row[1] + ".stp")
    reconstruction = open(reconstructionFile,'w')
    AllFiles.append(str(reconstructionFile))
    for line in row[0]:
        reconstruction.write(line)

print str(AllFiles)
