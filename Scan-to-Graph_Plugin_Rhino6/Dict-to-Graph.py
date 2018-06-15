from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef, util
from rdflib.namespace import RDFS, RDF, NamespaceManager
import rdflib
import sys
import ast
import os
from os import listdir
from os.path import isfile, join
import uuid

g=rdflib.Graph()

FileName = sys.argv[1]
print FileName
FileName = FileName.replace(r'\\','/')
FileName = FileName[1:-1]
print str(FileName)
ProjectInfo = sys.argv[2]
Topology = sys.argv[3]
Objects = sys.argv[4]
Assumptions = sys.argv[5]
GlobalURI = sys.argv[6]
RhinoDoc = sys.argv[7]
RhinoDoc = RhinoDoc.split(".")
RhinoDoc = RhinoDoc[0]

ProjectName = FileName.split(r"\\")
ProjectName = ProjectName[-1].split("/")
ProjectName = ProjectName[-1].split(".")
ProjectName = ProjectName[0]
print " "
if GlobalURI[-1] == "/":
    BasicURI = str(GlobalURI+ProjectName+"/")
else:
    BasicURI = str(GlobalURI+"/"+ProjectName+"/")
n = Namespace(BasicURI)

BOT = Namespace("https://w3id.org/bot#")
STG = Namespace("https://raw.githubusercontent.com/JWerbrouck/scan-to-graph/master/stg.ttl#")
STGP = Namespace("https://raw.githubusercontent.com/JWerbrouck/scan-to-graph/master/stgp.ttl#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
PRODUCT = Namespace("https://w3id.org/product#")
GEO = Namespace("http://www.opengis.net/ont/geosparql#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")

g.namespace_manager.bind("bot", BOT, override=False)
g.namespace_manager.bind("stg", STG, override=False)
g.namespace_manager.bind("stgp", STGP, override=False)
g.namespace_manager.bind("owl", OWL, override=False)
g.namespace_manager.bind("product", PRODUCT, override=False)
g.namespace_manager.bind("geo", GEO, override=False)
g.namespace_manager.bind("inst", n, override=False)
g.namespace_manager.bind("xsd", XSD, override=False)


ProjectInfo = ast.literal_eval(ProjectInfo)
Topology = ast.literal_eval(Topology)
Objects = ast.literal_eval(Objects)
Assumptions = ast.literal_eval(Assumptions)

geomPath = FileName.rstrip(".ttl") + str(r"/GEOM/")

for key,value in ProjectInfo.iteritems():
    if key == 'BuildingName':
        BuildingName = URIRef(n+value)
    if key == 'SiteName':
        SiteName = URIRef(n+value)
    if 'coordinates' in ProjectInfo:
        x = ProjectInfo['coordinates'][0]
        y = ProjectInfo['coordinates'][1]
        z = ProjectInfo['coordinates'][2]
        if 'coordinateSystem' in ProjectInfo:
            geostring = str('<'+ProjectInfo['coordinateSystem']+'>'+'\nPoint('+x+' '+y+' '+z+')')

        #default geocoordinatesystem = Lambert72 (because cartesian...)
        else:
            geostring = str('"'+'<'+'http://www.opengis.net/def/crs/EPSG/0/31370'+'>'+'\nPoint('+x+' '+y+' '+z+')"^^<http://www.opengis.net/ont/geosparql#wktLiteral>')

        GeoReference = Literal(geostring,datatype=GEO.wktLiteral)

#print BuildingName,SiteName,x,y,z
RhinoFile = URIRef(n+'RF_'+RhinoDoc)
RhinoLocal = Literal(r"C:/STG/"+ProjectName+"/"+"RhinoFiles/" + RhinoDoc + '.3dm')
g.add((SiteName,BOT.hasBuilding,BuildingName))
g.add((SiteName,STG.hasRhinoFile,RhinoFile))
g.add((RhinoFile,STG.hasLocalVersion,RhinoLocal))
ProjectOrigin = URIRef(n + "ProjectOrigin")
g.add((SiteName,STG.hasOrigin,ProjectOrigin))
g.add((ProjectOrigin,GEO.asWKT,GeoReference))

AddedAssumptions = []
AddedGeom = []
OcclusionList = []
#assigning Topology
for storey,spaces in Topology.iteritems():
    storeyRef = URIRef(n+storey)
    g.add((BuildingName,BOT.hasStorey,storeyRef))
    for space in spaces:
        Space_in_Storey = str(storey+"_"+space)
        space = URIRef(n+Space_in_Storey)
        g.add((storeyRef,BOT.hasSpace,space))

for ID,assumptions in Assumptions.iteritems():
    if ID not in AddedAssumptions:
        AddedAssumptions.append(ID)
        if len(assumptions)>0:
            Representation = URIRef(n+"GEOM_"+ID)
            for remark in assumptions:
                if "OCCLUDED_AREA" in remark:
                    occl_id = str(uuid.uuid4())
                    Occlusion = URIRef(n + "OCCLUSION_"+occl_id)
                    g.add((Representation,STG.hasOcclusion,Occlusion))
                    g.add((Occlusion,RDF.type,STG.OccludedGeometry))
                    OcclusionList.append(ID)
                elif "INNERPART" in remark:
                    g.add((Representation,RDF.type,STG.InternalGeometry))
                else:
                    assumpt_id = str(uuid.uuid4())
                    Assumption = URIRef(n + "ASSUMPTION_"+assumpt_id)
                    AssumptionText = Literal(remark,datatype=XSD.string)
                    g.add((Representation,STG.hasModellingRemark,Assumption))
                    g.add((Assumption,RDF.type,STG.Assumption))
                    g.add((Assumption,STG.denotesRemark,AssumptionText))

for Object in Objects:
    ObjName = URIRef(n+Object["Name"].replace(" ", "_"))

    if "Storey" in Object and "Space" in Object:
        if "Adjacent" in Object:
            Space_in_Storey = str(Object["Storey"]+"_"+Object["Space"])
            ObjSpace = URIRef(n+Space_in_Storey)
            g.add((ObjSpace,BOT.adjacentElement,ObjName))
            if "Space2" in Object:
                for storey,spaces in Topology.iteritems():
                    for space in spaces:
                        if Object['Space2'] == space:
                            AdjacentSpace_in_Storey = str(storey+'_'+space)
                            Obj_AdjacentSpace = URIRef(n+AdjacentSpace_in_Storey)
                            g.add((Obj_AdjacentSpace,BOT.adjacentElement,ObjName))
                            g.add((ObjSpace,BOT.adjacentZone,Obj_AdjacentSpace))
        else:
            Space_in_Storey = str(Object["Storey"]+"_"+Object["Space"])
            ObjSpace = URIRef(n+Space_in_Storey)
            g.add((ObjSpace,BOT.containsElement,ObjName))

    if "Type" in Object:
        if Object["Type"] != "-not specified-":
            type = Object['Type'].split(":")
            if type[0] == "product":
                ObjType = URIRef(PRODUCT+type[1])
            elif type[0] == "stgp":
                ObjType = URIRef(STGP+type[1])
            g.add((ObjName,RDF.type,ObjType))
            g.add((ObjName,RDF.type,BOT.Element))
        else:
            g.add((ObjName,RDF.type,PRODUCT.Product))
            g.add((ObjName,RDF.type,BOT.Element))
    else:
        g.add((ObjName,RDF.type,PRODUCT.Product))
        g.add((ObjName,RDF.type,BOT.Element))

    if 'PointCloud' in Object:
        if Object['PointCloud'] != None:
            for PC in Object["PointCloud"]:
                PCstring = str("C:/STG/"+str(ProjectName)+"/"+"PointClouds/"+str(PC)+'.e57')
                PCref = Literal(PCstring)
                PC_URI = URIRef(n+"PC_"+PC)
                g.add((ObjName,STG.hasLocalVersion,PCref))
                g.add((ObjName,STG.hasPointCloudFile,PC_URI))

    if 'isHostedBy' in Object:
        ObjHostedBy = URIRef(n+Object["isHostedBy"].replace(" ", "_"))
        g.add((ObjHostedBy,BOT.hostsElement,ObjName))

    if 'Aggregates' in Object:
        for SODict in Object['Aggregates']:
            index = str(Objects.index(Object))
            SOName = URIRef(n+'_'+index+"_"+SODict['Name'].replace(" ", "_"))
            if 'SOfromSO' in SODict:
                if SODict['SOfromSO'] != '-NONE-':
                    SOHost = URIRef(n+'_'+index+"_"+SODict["SOfromSO"].replace(" ", "_"))
                else:
                    SOHost = ObjName
            else:
                SOHost = ObjName
            if SODict['Relationship'] == 'hosted':
                g.add((SOHost,BOT.hostsElement,SOName))
            elif SODict['Relationship'] == 'aggregated':
                g.add((SOHost,PRODUCT.aggregates,SOName))

            if 'Type' in SODict:
                if SODict["Type"] != "-not specified-":
                    type = SODict['Type'].split(":")
                    if type[0] == "product":
                        ObjType = URIRef(PRODUCT+type[1])
                    elif type[0] == "stgp":
                        ObjType = URIRef(STGP+type[1])
                    g.add((SOName,RDF.type,ObjType))
                    g.add((SOName,RDF.type,BOT.Element))
                else:
                    g.add((SOName,RDF.type,PRODUCT.BuildingElementPart))
                    g.add((SOName,RDF.type,BOT.Element))
            else:
                g.add((SOName,RDF.type,PRODUCT.BuildingElementPart))
                g.add((SOName,RDF.type,BOT.Element))

            if 'Geometry' in SODict:
                geomPath = FileName.rstrip(".ttl") + str(r"/GEOM/")
                Geometry = []
                if os.path.exists(geomPath):
                    Geometry = [f for f in listdir(geomPath) if isfile(join(geomPath, f))]
                    if len(Geometry)>0:
                        for RhinoID in Geometry:
                            if RhinoID.split(".")[1] == "stp":
                                Geom_inst = RhinoID.rstrip(".stp")
                                if Geom_inst in SODict["Geometry"]:
                                    Representation = URIRef(n+"GEOM_"+Geom_inst)
                                    if Representation not in AddedGeom:
                                        AddedGeom.append(Representation)
                                        IDfilePath = geomPath + RhinoID
                                        file = open(IDfilePath, 'r')
                                        fileContent = ''
                                        for row in file:
                                            fileContent += row
                                        STPgeom = Literal(fileContent,datatype=STG.STEPRepresentation)

                                        g.add((Representation,STG.asSTEP,STPgeom))
                                        IDLiteral = Literal(Geom_inst,datatype=STG.RhinoID)
                                        g.add((SOName,GEO.hasGeometry,Representation))
                                        g.add((Representation,STG.hasRhinoID,IDLiteral))

                                        if "LOA" in Object and "DeviationMethod" in Object:
                                            if Geom_inst not in OcclusionList:
                                                LOArepr =  URIRef(n+"LOA-"+Geom_inst)
                                                LOAValue = str(Object["LOA"])
                                                LOAstring = str('LOA'+LOAValue)
                                                LOALiteral = Literal(LOAstring)
                                                LOAscale = Literal(str(Object["DeviationMethod"]))
                                                g.add((Representation,STG.hasLOA,LOArepr))
                                                g.add((LOArepr,STG.hasLOAvalue,LOALiteral))
                                                g.add((LOArepr,STG.usedDeviationAnalysis,LOAscale))

                else:
                    for Geom_inst in SODict["Geometry"]:
                        Representation = URIRef(n+"GEOM_"+Geom_inst)
                        IDLiteral = Literal(Geom_inst,datatype=STG.RhinoID)
                        g.add((SOName,GEO.hasGeometry,Representation))
                        g.add((Representation,STG.hasRhinoID,IDLiteral))
                        if "LOA" in Object and "DeviationMethod" in Object:
                            if Geom_inst not in OcclusionList:
                                LOArepr =  URIRef(n+"LOA-"+Geom_inst)
                                LOAValue = str(Object["LOA"])
                                LOAstring = str('LOA'+LOAValue)
                                LOALiteral = Literal(LOAstring)
                                LOAscale = Literal(str(Object["DeviationMethod"]))
                                g.add((Representation,STG.hasLOA,LOArepr))
                                g.add((LOArepr,STG.hasLOAvalue,LOALiteral))
                                g.add((LOArepr,STG.usedDeviationAnalysis,LOAscale))

    if "Geometry" in Object:
        geomPath = FileName.rstrip(".ttl") + str(r"/GEOM/")
        Geometry = []
        if os.path.exists(geomPath):
            Geometry = [f for f in listdir(geomPath) if isfile(join(geomPath, f))]
            if len(Geometry)>0:
                for RhinoID in Geometry:
                    if RhinoID.split(".")[1] == "stp":
                        Geom_inst = RhinoID.rstrip(".stp")
                        if Geom_inst in Object["Geometry"]:
                            Representation = URIRef(n+"GEOM_"+Geom_inst)
                            if Representation not in AddedGeom:
                                AddedGeom.append(Representation)
                                IDfilePath = geomPath + RhinoID
                                file = open(IDfilePath, 'r')
                                fileContent = ''
                                for row in file:
                                    fileContent += row
                                STPgeom = Literal(fileContent,datatype=STG.STEPRepresentation)
                                g.add((Representation,STG.asSTEP,STPgeom))
                                IDLiteral = Literal(Geom_inst,datatype=STG.RhinoID)
                                g.add((ObjName,GEO.hasGeometry,Representation))
                                g.add((Representation,STG.hasRhinoID,IDLiteral))

                                if "LOA" in Object and "DeviationMethod" in Object:
                                    if Geom_inst not in OcclusionList:
                                        LOArepr =  URIRef(n+"LOA-"+Geom_inst)
                                        LOAValue = str(Object["LOA"])
                                        LOAstring = str('LOA'+LOAValue)
                                        LOALiteral = Literal(LOAstring)
                                        LOAscale = Literal(str(Object["DeviationMethod"]))
                                        g.add((Representation,STG.hasLOA,LOArepr))
                                        g.add((LOArepr,STG.hasLOAvalue,LOALiteral))
                                        g.add((LOArepr,STG.usedDeviationAnalysis,LOAscale))

        else:
            for Geom_inst in Object["Geometry"]:
                Representation = URIRef(n+"GEOM_"+Geom_inst)
                IDLiteral = Literal(Geom_inst,datatype=STG.RhinoID)
                g.add((ObjName,GEO.hasGeometry,Representation))
                g.add((Representation,STG.hasRhinoID,IDLiteral))

                LOArepr =  URIRef(n+"LOA-"+Geom_inst)
                if "LOA" in Object and "DeviationMethod" in Object:
                    if Geom_inst not in OcclusionList:
                        LOArepr =  URIRef(n+"LOA-"+Geom_inst)
                        LOAValue = str(Object["LOA"])
                        LOAstring = str('LOA'+LOAValue)
                        LOALiteral = Literal(LOAstring)
                        LOAscale = Literal(str(Object["DeviationMethod"]))
                        g.add((Representation,STG.hasLOA,LOArepr))
                        g.add((LOArepr,STG.hasLOAvalue,LOALiteral))
                        g.add((LOArepr,STG.usedDeviationAnalysis,LOAscale))

g.serialize(destination=FileName,format='turtle')
