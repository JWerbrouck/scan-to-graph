from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef, util
from rdflib.namespace import RDFS, RDF, NamespaceManager
from rdflib.plugins.sparql import prepareQuery
import rdflib
import sys
import ast
import os
import operator

g=rdflib.Graph()

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
g.namespace_manager.bind("xsd", XSD, override=False)

graph_to_parse = str(sys.argv[1])

if os.path.exists(graph_to_parse):
    try:
        file_format = rdflib.util.guess_format(graph_to_parse)
        g.parse(graph_to_parse, format=str(file_format))
    except:
        pass

#recreating the AssumptionDict
AssumptionQuery = prepareQuery('SELECT ?geom ?remark ?Assumptext WHERE {{?geom stg:hasModellingRemark ?remark. ?remark stg:denotesRemark ?Assumptext .} UNION {?geom stg:hasOcclusion ?remark. ?remark a stg:OccludedGeometry .} UNION {?remark a stg:InternalGeometry .}}',initNs={"stg" : STG})
assumptionList = g.query(AssumptionQuery)
AssumptionDict = {}
for qres in assumptionList:
    geometry = qres[0]
    RemarkType = qres [1]
    Assumptext = qres[2]

    instance=RemarkType.split("/")
    instance=instance[-1]
    inst_split = instance.split("_")
    inst_type = inst_split[0]
    inst_ID = inst_split[-1]
    inst_type = inst_type[0:4]
    try:
        Geom_split = geometry.split("/")
        Geom_split = Geom_split[-1].split("_")
        Geom_ID = Geom_split[-1]
    except: pass

    if str(inst_ID) not in AssumptionDict:
        if inst_type == "ASSU":
            AssumptionDict[str(Geom_ID)]= [str(Assumptext)]
        elif inst_type == "OCCL":
            AssumptionDict[str(Geom_ID)]= ["OCCLUDED_AREA"]
        elif inst_type == "GEOM":
            AssumptionDict[str(inst_ID)]= ["INNERPART"]
    else:
        if inst_type == "ASSU":
            AssumptionDict[str(Geom_ID)].append(str(remark))
        elif inst_type == "OCCL":
            AssumptionDict[str(Geom_ID)].append("OCCLUDED_AREA")
        elif inst_type == "GEOM":
            AssumptionDict[str(inst_ID)].append("INNERPART")

#recreating the Project Info Dictionary
ProjectInfoQuery = prepareQuery('SELECT ?site ?building ?coordinates WHERE {?site bot:hasBuilding ?building. ?site stg:hasOrigin ?origin. ?origin geo:asWKT ?coordinates}',initNs={"stg" : STG, "bot" : BOT, "geo" : GEO})
ProjectInfoList = g.query(ProjectInfoQuery)

ProjectInfo = {}
for list in ProjectInfoList:
    site = list[0]
    site = site.split("/")
    site = site[-1]
    ProjectInfo["SiteName"] = str(site)

    building = list[1]
    building = building.split("/")
    building = building [-1]
    ProjectInfo["BuildingName"] = str(building)

    coordinateWKT = list[2]
    coordinateWKT = coordinateWKT.split(">")
    coordinateSystem = coordinateWKT[0][1:]
    ProjectInfo["coordinateSystem"] = str(coordinateSystem)

    coordinates = coordinateWKT[-1].split('(')
    coordinates = coordinates[-1][:-1]
    coordinates = coordinates.split(" ")
    coordinate_real = []
    for co in coordinates:
        coordinate_real.append(str(co))

    coordinates = tuple(coordinate_real)
    ProjectInfo["coordinates"] = coordinates

#recreating the Topology Dictionary
TopoQuery = prepareQuery('SELECT ?storey ?space WHERE {?building bot:hasStorey ?storey. ?storey bot:hasSpace ?space}',initNs={"bot" : BOT})
TopoList = g.query(TopoQuery)

Topology = {}
for list in TopoList:
    storey = list[0].split("/")
    storey = storey[-1]
    space = list[1].split("/")
    space = space[-1]
    space = space.replace(storey,'')
    space = space[1:]
    if storey not in Topology:
        Topology[str(storey)] = [str(space)]
    else:
        Topology[str(storey)].append(str(space))

#recreating the Object Dictionary
InformationList = []
adjacent = prepareQuery('SELECT ?adjacentObject ?space WHERE {?space bot:adjacentElement ?adjacentObject}',initNs={"bot" : BOT})
contained = prepareQuery('SELECT ?containedObject ?space WHERE {?space bot:containsElement ?containedObject}',initNs={"bot" : BOT})

adjacentList = g.query(adjacent)
containedList = g.query(contained)

ObjectSpaces = {}
dominantSpaces = {}
for list in adjacentList:
    adjacentObject = list[0].split("/")
    adjacentObject = str(adjacentObject[-1])

    space = list[1].split("/")
    space = str(space[-1])
    if space not in dominantSpaces:
        dominantSpaces[space] = 1
    else:
        dominantSpaces[space] +=1

    if adjacentObject not in ObjectSpaces:
        ObjectSpaces[adjacentObject] = [space]
    else:
        ObjectSpaces[adjacentObject].append(space)

for list in containedList:
    containedObject = list[0].split("/")
    containedObject = str(containedObject[-1])

    space = list[1].split("/")
    space = str(space[-1])
    if space not in dominantSpaces:
        dominantSpaces[space] = 1
    else:
        dominantSpaces[space] +=1

    if containedObject not in ObjectSpaces:
        ObjectSpaces[containedObject] = [space]
    else:
        ObjectSpaces[containedObject].append(space)

sorted_dominantSpaces = sorted(dominantSpaces.items(), key=operator.itemgetter(1))
sorted_dominantSpaces = reversed(sorted_dominantSpaces)
dominantSpaces_onlySpaces = []
for item in sorted_dominantSpaces:
    dominantSpaces_onlySpaces.append(item[0])

dominantSpaces_onlySpaces = tuple(dominantSpaces_onlySpaces)

MainObjects = []
for object, spaces in ObjectSpaces.iteritems():
    ObjectDict = {}
    ObjectDict["Name"] = str(object)
    MainObjects.append(str(object))
    if len(spaces)==1:
        for storey, room in Topology.iteritems():
            if storey in spaces[0]:
                space = spaces[0].replace(storey,"")
                space = space[1:]
                ObjectDict["Space"] = str(space)
                ObjectDict["Storey"] = str(storey)

    else:
        SpaceIndex = {}
        for space in spaces:
            for item in dominantSpaces_onlySpaces:
                if space == item:
                    index = dominantSpaces_onlySpaces.index(item)
                    SpaceIndex[space]=index
        sorted_SpaceIndex = sorted(SpaceIndex.items(), key=operator.itemgetter(1))
        space1 = sorted_SpaceIndex[0][0]
        space2 = sorted_SpaceIndex[1][0]
        for storey, space in Topology.iteritems():
            if storey in space1:
                space1 = space1.replace(storey,"")
                space1 = space1[1:]
                ObjectDict["Space"] = str(space1)
                ObjectDict["Storey"] = str(storey)
            if storey in space2:
                space2 = space2.replace(storey,"")
                space2 = space2[1:]
                ObjectDict["Space2"] = str(space2)
                ObjectDict["Adjacent"] = "True"

    InformationList.append(ObjectDict)

mainhosted = prepareQuery('SELECT ?object ?space ?hostingelement WHERE {{?space bot:containsElement ?object. ?hostingelement bot:hostsElement ?object} UNION {?space bot:adjacentElement ?object. ?hostingelement bot:hostsElement ?object}}',initNs={"stg": STG, "bot" : BOT})
pc_hostList = g.query(mainhosted)

for item in pc_hostList:
    object = item[0].split("/")
    object = object[-1]

    host = item[2].split("/")
    host = host[-1]

    for ObjectDict in InformationList:
        if ObjectDict["Name"] == str(object):
            ObjectDict["isHostedBy"] = str(host)

pcDict = {}
pointclouds = prepareQuery('SELECT ?object ?pc WHERE {?object stg:hasPointCloudFile ?pc.}',initNs={"stg": STG})
pointcloudslist = g.query(pointclouds)
for item in pointcloudslist:
    object = item[0].split("/")
    object = str(object[-1])
    pc = item[1].split("/")
    pc = str(pc[-1])
    if object not in pcDict:
        pcDict[object] = [pc]
    else:
        pcDict[object].append(pc)

for object, pc in pcDict.iteritems():
    for ObjectDict in InformationList:
        if ObjectDict["Name"] == object:
            ObjectDict["PointCloud"] = pc

objectType = prepareQuery('SELECT ?object ?space ?type WHERE {{?space bot:containsElement ?object. ?object rdf:type ?type} UNION {?space bot:adjacentElement ?object. ?object rdf:type ?type}}',initNs={"stg": STG, "rdf": RDF, "bot" : BOT, "product" : PRODUCT})
objectTypeList = g.query(objectType)
for item in objectTypeList:
    object = item[0].split("/")
    object = object[-1]

    element_type = item[2].split("/")
    element_type = element_type[-1]

    if "bot#" not in element_type:
        element_type = element_type.split("#")
        namespace = element_type[0]
        namespace = namespace.split(".")
        namespace = namespace[0]
        element_type = element_type[1]
        element_type = str(namespace+":"+element_type)
        for ObjectDict in InformationList:
            if ObjectDict["Name"] == str(object):
                if "product:Product" not in element_type:
                    ObjectDict["Type"] = str(element_type)

ObjectGeometry = prepareQuery('SELECT ?object ?space ?geometry WHERE {{?space bot:containsElement ?object. ?object geo:hasGeometry ?geometry} UNION {?space bot:adjacentElement ?object. ?object geo:hasGeometry ?geometry}}',initNs={"stg": STG, "geo": GEO, "bot" : BOT})
GeometryList = g.query(ObjectGeometry)
geomDict = {}

for item in GeometryList:
    object = item[0].split("/")
    object = str(object[-1])

    geometry = item[2].split("/")
    geometry = geometry[-1]
    geometry = str(geometry.replace("GEOM_", ''))
    if object not in geomDict:
        geomDict[object] = [geometry]
    else:
        if geometry not in geomDict[object]:
            geomDict[object].append(geometry)

for object, geometries in geomDict.iteritems():
    for ObjectDict in InformationList:
        if ObjectDict["Name"] == object:
            ObjectDict["Geometry"] = geometries

HostedObjects = prepareQuery('SELECT ?object ?hostingobject ?type ?geometry WHERE {?hostingobject bot:hostsElement ?object. ?object a ?type. ?object geo:hasGeometry ?geometry}',initNs={"bot": BOT, "product": PRODUCT,"geo" : GEO})
AggregatedObjects = prepareQuery('SELECT ?object ?hostingobject ?type ?geometry WHERE {?hostingobject product:aggregates ?object. ?object a ?type. ?object geo:hasGeometry ?geometry}',initNs={"bot": BOT, "product": PRODUCT, "geo" : GEO})
AggregateList = g.query(AggregatedObjects)
HostedList = g.query(HostedObjects)
AllHostedElements = []
SubElements = []

for objects in AggregateList:
    element = str(objects[0]).split("/")
    element = element[-1]
    hostingElement = str(objects[1]).split("/")
    hostingElement = hostingElement[-1]
    element_type = str(objects[2])
    geometry = str(objects[3])
    if objects[3] is not None:
        geometry = geometry.split("_")
        geometry = geometry[-1]

    if objects[2] is not None:
        element_type = objects[2].split("/")
        element_type = element_type[-1]

        if "bot#" not in element_type:
            element_type = element_type.split("#")
            namespace = element_type[0]
            namespace = namespace.split(".")
            namespace = namespace[0]
            element_type = element_type[1]
            element_type = str(namespace+":"+element_type)
            for ObjectDict in InformationList:
                if ObjectDict["Name"] == str(object):
                    if "product:Product" not in element_type:
                        AllHostedElements.append((str(element),str(hostingElement),"hosted",element_type,geometry))
    else:
        AllHostedElements.append((str(element),str(hostingElement),"hosted",element_type,geometry))

for objects in HostedList:
    element = str(objects[0]).split("/")
    element = element[-1]
    hostingElement = str(objects[1]).split("/")
    hostingElement = hostingElement[-1]
    element_type = str([2])
    geometry = str(objects[3])
    if objects[3] is not None:
        geometry = geometry.split("_")
        geometry = geometry[-1]

    if objects[2] is not None:
        element_type = objects[2].split("/")
        element_type = element_type[-1]

        if "bot#" not in element_type:
            element_type = element_type.split("#")
            namespace = element_type[0]
            namespace = namespace.split(".")
            namespace = namespace[0]
            element_type = element_type[1]
            element_type = str(namespace+":"+element_type)
            for ObjectDict in InformationList:
                if ObjectDict["Name"] == str(object):
                    if "product:Product" not in element_type:
                        AllHostedElements.append((str(element),str(hostingElement),"hosted",element_type,geometry))
    else:
        AllHostedElements.append((str(element),str(hostingElement),"hosted",element_type,geometry))

GeomDict = {}
for SO,host,relationship,element_type,GEOM in AllHostedElements:
    if SO not in MainObjects:
        if SO not in GeomDict:
            GeomDict[SO] = [GEOM]
        else:
            GeomDict[SO].append(GEOM)

for tup in AllHostedElements:
    SO = tup[0]
    if SO not in MainObjects:
        SubElements.append(tup)

for SO,parent,relationship,element_type,geometry in SubElements:
    SODict = {}
    for Geom in GeomDict:
        if SO in GeomDict:
            SODict["Geometry"]=GeomDict[SO]
    SO = SO.split("_")
    new_SO =''
    for part in SO[2:]:
        new_SO += part
        new_SO += "_"
    new_SO = new_SO[:-1]
    SODict["Name"] = new_SO
    SODict["Relationship"] = relationship
    if element_type is not None:
        SODict["Type"] = str(element_type)


    for ObjectDict in InformationList:
        if parent in MainObjects:
            if ObjectDict["Name"] == parent:
                if "Aggregates" not in ObjectDict:
                    ObjectDict["Aggregates"] = (SODict,)
                else:
                    SOList = []
                    for item in ObjectDict["Aggregates"]:
                        SOList.append(item)
                    SOList.append(SODict)
                    ObjectDict["Aggregates"] = tuple(SOList)

for SO,parent,relationship,element_type,geometry in SubElements:
    SODict = {}
    SO = SO.split("_")
    new_SO =''
    for part in SO[2:]:
        new_SO += part
        new_SO += "_"
    new_SO = new_SO[:-1]
    SODict["Name"] = new_SO
    SODict["Relationship"] = relationship
    if element_type is not None:
        SODict["Type"] = str(element_type)

    if parent not in MainObjects:
        hostingElement = parent.split("_")
        new_hostingElement = ''
        for part in hostingElement[2:]:
            new_hostingElement += part
            new_hostingElement += "_"
        new_hostingElement = new_hostingElement[:-1]
        SODict["SOfromSO"] = new_hostingElement

        for ObjectDict in InformationList:
            if "Aggregates" in ObjectDict:
                for ParentSOdict in ObjectDict["Aggregates"]:
                    if ParentSOdict["Name"] == new_hostingElement:
                        SOList = []
                        for item in ObjectDict["Aggregates"]:
                            SOList.append(item)
                        SOList.append(SODict)
                        ObjectDict["Aggregates"] = tuple(SOList)

LOA = prepareQuery('SELECT ?object ?geom ?LOAvalue ?method WHERE {?object geo:hasGeometry ?geom. ?geom stg:hasLOA ?LOA. ?LOA stg:hasLOAvalue ?LOAvalue. ?LOA stg:usedDeviationAnalysis ?method}',initNs={"stg": STG,'geo': GEO})
LOAQuery = g.query(LOA)
LOA_List = []

for row in LOAQuery:
    object = str(row[0])
    object = object.split("/")
    object = object[-1]
    geom = str(row[1])
    value = str(row[2])
    method = str(row[3])
    geom = geom.split("_")
    geom = geom[-1]
    value = value.replace("LOA",'')
    LOA_List.append([object,geom,value,method])

for ObjectDict in InformationList:
    for row in LOA_List:
        object = row[0]
        geom = row[1]
        value = row[2]
        method = row[3]

        if ObjectDict["Name"] == object:
            if geom in ObjectDict["Geometry"]:
                if "LOA" in ObjectDict:
                    pass
                else: ObjectDict["LOA"] = value
                if "DeviationMethod" in ObjectDict:
                    pass
                else: ObjectDict["DeviationMethod"] = method
    """try:
        print ObjectDict["Name"],geom,ObjectDict["LOA"],ObjectDict["DeviationMethod"]
        print " "
    except: pass"""
    """if "Geometry" in ObjectDict:
        for geometry in ObjectDict["Geometry"]:
            for sublist in LOA_List:
                geom = sublist[0]
                if geometry == geom:
                    ObjectDict["LOA"] = str(value)
                    ObjectDict["DeviationMethod"] = method
                    print ObjectDict["Name"],geom,geometry,ObjectDict["LOA"],ObjectDict["DeviationMethod"]
                    print ' '"""


"""for ObjectDict in InformationList:
    for key, value in ObjectDict.iteritems():
        print key, value
    print ' '"""
for ObjectDict in InformationList:
    if "Aggregates" in ObjectDict:
        tup = ObjectDict["Aggregates"]
        BetweenList = []
        FinalList = []
        for item in tup:
            BetweenList.append(str(item))
        BetweenList2 = set(BetweenList)
        for item in BetweenList2:
            item = ast.literal_eval(item)
            FinalList.append(item)
        ObjectDict["Aggregates"] = tuple(FinalList)

Final = [ProjectInfo,Topology,InformationList,AssumptionDict]
print Final

