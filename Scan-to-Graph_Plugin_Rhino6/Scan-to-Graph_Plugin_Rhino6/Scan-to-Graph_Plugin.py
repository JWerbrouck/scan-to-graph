import System
import Rhino
import Rhino.UI
import Eto.Drawing as drawing
import Eto.Forms as forms
import rhinoscriptsyntax as rs
import scriptcontext as sc
import csv
import subprocess
import ast
import os
import webbrowser
from os import listdir,mkdir
from os.path import isdir
import fnmatch
import shutil
import time
from time import strftime, gmtime, sleep

global pythonversion
pythonversion = str("C:/Python27/python.exe")

global cloudcompare_path
cloudcompare_path = str(r"C:\Program Files\CloudCompareStereo\CloudCompare.exe")

global ProjectFolder
ProjectFolder = os.path.dirname(os.path.realpath(__file__)).encode('string-escape')

#main class for the project info tab
class Project_Info(forms.Panel):
    #main layout
    def __init__(self):
        self.MainInfo = self.MainInfo()
        self.Topology = self.Topology()
        
        self.Topology.Visible = True
        
        
        self.iTabLayout = forms.DynamicLayout()
        self.iTabLayout.Padding = drawing.Padding(10)
        self.iTabLayout.Spacing = drawing.Size(5,5)
        
        self.iTabLayout.AddRow(self.MainInfo)
        self.iTabLayout.AddRow(self.Topology)
        self.iTabLayout.AddRow("")
        
        self.Content = self.iTabLayout
    
    #layout for defining the storeys and spaces
    def Topology(self):
        self.TopoGroupBox = forms.GroupBox(Text = "Project Topology")
        self.TopoGroupBox.Padding = drawing.Padding(10)
        self.TopoLayout = forms.DynamicLayout()
        self.TopoLayout.Padding = drawing.Padding(10)
        self.TopoLayout.Spacing = drawing.Size(5,5)
        
        self.StoreyLayout = forms.DynamicLayout()
        self.StoreyLayout.Padding = drawing.Padding(10)
        self.StoreyLayout.Spacing = drawing.Size(5,5)
        
        self.SpaceLayout = forms.DynamicLayout()
        self.SpaceLayout.Padding = drawing.Padding(10)
        self.SpaceLayout.Spacing = drawing.Size(5,5)
        
        self.StoreyLabel = forms.Label(Text = "Storeys: ")
        Project_Info.Storeys = []
        Project_Info.StoreyBox = forms.ListBox(DataStore = Project_Info.Storeys)
        self.AddStorey = forms.Button(Text = "Add Storey")
        self.RemoveStorey = forms.Button(Text = "Remove Storey", Enabled = False)
        Project_Info.TopoDict = {}
        
        self.AddStorey.Click += self.AddNewStorey
        self.RemoveStorey.Click += self.RemoveExistingStorey
        
        self.SpaceLabel = forms.Label(Text = "Spaces: ")
        Project_Info.Spaces = []
        Project_Info.SpaceBox = forms.ListBox(DataStore = Project_Info.Spaces)
        Project_Info.StoreyBox.SelectedIndexChanged += self.ChangeSpaceDisplay
        self.AddSpace = forms.Button(Text = "Add Space",Enabled = False)
        self.RemoveSpace = forms.Button(Text = "Remove Space", Enabled = False)
        
        self.AddSpace.Click += self.AddNewSpace
        self.RemoveSpace.Click += self.RemoveExistingSpace
        
        self.StoreyLayout.BeginVertical()
        self.StoreyLayout.AddRow(self.StoreyLabel)
        self.StoreyLayout.AddRow(Project_Info.StoreyBox)
        self.StoreyLayout.EndVertical()
        self.StoreyLayout.BeginVertical()
        self.StoreyLayout.AddRow(self.AddStorey," ", self.RemoveStorey)
        
        self.SpaceLayout.BeginVertical()
        self.SpaceLayout.AddRow(self.SpaceLabel)
        self.SpaceLayout.AddRow(Project_Info.SpaceBox)
        self.SpaceLayout.EndVertical()
        self.SpaceLayout.BeginVertical()
        self.SpaceLayout.AddRow(self.AddSpace," ",self.RemoveSpace)
        
        self.TopoLayout.AddRow(self.StoreyLayout,self.SpaceLayout)
        self.TopoGroupBox.Content = self.TopoLayout
        
        return self.TopoGroupBox
    
    #this button allows to create a new space contained in the currently selected storey
    def AddNewSpace(self,sender,e):
        if len(Project_Info.Storeys)>0:
            storey = Project_Info.StoreyBox.DataStore[Project_Info.StoreyBox.SelectedIndex]
            rc, text  = Rhino.UI.Dialogs.ShowEditBox("Space Name", "Enter the name of the space",None, 0)
            if rc != True: return None
            else:
                if len(text)>0:
                    Project_Info.TopoDict[storey].append(text)
                    Project_Info.Spaces.append(text)
                    Project_Info.SpaceBox.DataStore = Project_Info.TopoDict[storey]
                    self.RemoveSpace.Enabled = True
    
    #this button deletes the currently selected space
    def RemoveExistingSpace(self,sender,e):
        if len(Project_Info.Spaces)>0:
            storey = Project_Info.StoreyBox.DataStore[Project_Info.StoreyBox.SelectedIndex]
            space = Project_Info.SpaceBox.DataStore[Project_Info.SpaceBox.SelectedIndex]
            if space in Project_Info.TopoDict[storey]:
                Project_Info.TopoDict[storey].remove(space)
                Project_Info.Spaces.remove(space)
                print space, "removed"
            if len(Project_Info.TopoDict[storey])==0:
                self.RemoveSpace.Enabled = False
            try:
                Project_Info.SpaceBox.DataStore = Project_Info.TopoDict[storey]
            except: pass
        else: 
            print "no spaces left!"
            storey = Project_Info.SpaceBox.DataStore=[]
    
    #when another storey is selected in the storey list, the spaces it contains are displayed in the space list
    def ChangeSpaceDisplay(self,sender,e):
        storey = Project_Info.StoreyBox.DataStore[Project_Info.StoreyBox.SelectedIndex]
        Project_Info.SpaceBox.DataStore = Project_Info.TopoDict[storey]
    
    #this button removes a storey and its constituting spaces
    def RemoveExistingStorey(self,sender,e):
        if len(Project_Info.Storeys)==0:
            self.RemoveStorey.Enabled = False
            print "no storeys left!" 
        else:
            try:
                storey = Project_Info.StoreyBox.DataStore[Project_Info.StoreyBox.SelectedIndex]
                Project_Info.Storeys.remove(storey)
                if storey in Project_Info.TopoDict:
                    del Project_Info.TopoDict[storey]
                if len(Project_Info.Storeys)==0:
                    self.RemoveStorey.Enabled = False
                    self.RemoveSpace.Enabled = False
                    self.AddSpace.Enabled = False
                    Project_Info.SpaceBox.DataStore = []
                Project_Info.StoreyBox.DataStore = Project_Info.Storeys
                Project_Info.StoreyBox.SelectedIndex = 0
                newstorey = Project_Info.StoreyBox.DataStore[Project_Info.StoreyBox.SelectedIndex]
                Project_Info.SpaceBox.DataStore = Project_Info.TopoDict[newstorey]

            except: pass
    
    #this button allows to create a new storey and activates the create/delete buttons when at least one storey was created
    def AddNewStorey(self, sender, e):
        rc, text  = Rhino.UI.Dialogs.ShowEditBox("Storey Name", "Enter the name of the storey", None, 0)
        if rc != True: return None
        else:
            if len(text)>0:
                Project_Info.Storeys.append(str(text))
                Project_Info.StoreyBox.DataStore = Project_Info.Storeys
                Project_Info.TopoDict[text] = []
                self.RemoveStorey.Enabled = True
                self.AddSpace.Enabled = True
    
    #layout for the main project info: sitename, buildingname, geocoordinates and geocoordinate system
    def MainInfo(self):
        Project_Info.ProjectInfo={}
        self.InfoGroupBox = forms.GroupBox(Text = "Main Project Info")
        self.InfoGroupBox.Padding = drawing.Padding(10)
        self.Label_SiteName = forms.Label(Text = "Sitename: ")
        Project_Info.TextBox_SiteName = forms.TextBox()
        Project_Info.TextBox_SiteName.LostFocus += self.setProjectInfo
        
        self.Label_BuildingName = forms.Label(Text = "Buildingname: ")
        Project_Info.TextBox_BuildingName = forms.TextBox()
        Project_Info.TextBox_BuildingName.LostFocus += self.setProjectInfo
        
        self.Link_OpenGIS = forms.LinkButton(Text = "Coordinate System: ")
        self.Link_OpenGIS.Click += self.GCSClick
        Project_Info.CoordinateSystem = forms.TextBox(Text = "http://www.opengis.net/def/crs/EPSG/0/31370")
        Project_Info.CoordinateSystem.LostFocus += self.setProjectInfo
        
        Xlabel = forms.Label(Text = "x-coordinates")
        Ylabel = forms.Label(Text = "y-coordinates")
        Zlabel = forms.Label(Text = "z-coordinates")
        Project_Info.Xcoord = forms.TextBox(Text = "0")
        Project_Info.Ycoord = forms.TextBox(Text = "0")
        Project_Info.Zcoord = forms.TextBox(Text = "0")
        Project_Info.Xcoord.LostFocus += self.setProjectInfo
        Project_Info.Ycoord.LostFocus += self.setProjectInfo
        Project_Info.Zcoord.LostFocus += self.setProjectInfo
        
        Project_Info.ExportSTP = forms.CheckBox(Text = "include STEP geometry in Graph", Checked = False)
        Project_Info.ImportSTP = forms.CheckBox(Text = "import STEP geometry to an empty .3dm file (Unstable - graph info cannot be used)", Checked = False)
        
        self.InfoLayout = forms.DynamicLayout()
        self.InfoLayout.Padding = drawing.Padding(10)
        self.InfoLayout.Spacing = drawing.Size(5, 5)
        
        self.InfoLayout.BeginVertical()
        self.InfoLayout.AddRow(self.Label_SiteName,"            ",Project_Info.TextBox_SiteName)
        self.InfoLayout.AddRow(self.Label_BuildingName,"     ",Project_Info.TextBox_BuildingName)
        self.InfoLayout.AddRow("")
        self.InfoLayout.AddRow(self.Link_OpenGIS,"     ",Project_Info.CoordinateSystem)
        self.InfoLayout.AddRow(Xlabel,"     ",Project_Info.Xcoord)
        self.InfoLayout.AddRow(Ylabel,"     ",Project_Info.Ycoord)
        self.InfoLayout.AddRow(Zlabel,"     ",Project_Info.Zcoord)
        self.InfoLayout.AddRow("")
        self.InfoLayout.EndVertical()
        self.InfoLayout.BeginVertical()
        self.InfoLayout.AddRow(Project_Info.ExportSTP)
        self.InfoLayout.AddRow(Project_Info.ImportSTP)
        self.InfoLayout.EndVertical()
        self.InfoGroupBox.Content = self.InfoLayout
        
        return self.InfoGroupBox
    
    #the Project Info is written to the Project info Dictionary when one of the project info buttons loses focus. Sorry for the abundancy...
    def setProjectInfo(self,sender,e):
        X = str(Project_Info.Xcoord.Text)
        Y = str(Project_Info.Ycoord.Text)
        Z = str(Project_Info.Zcoord.Text)
        Project_Info.ProjectInfo["coordinates"]=(X,Y,Z)
        Project_Info.ProjectInfo["coordinateSystem"] = Project_Info.CoordinateSystem.Text
        Project_Info.ProjectInfo["SiteName"] = Project_Info.TextBox_SiteName.Text
        Project_Info.ProjectInfo["BuildingName"] = Project_Info.TextBox_BuildingName.Text
    
    #an OpenGIS webpage with current GeoCoordinateSystems opens in the default webbrowser
    def GCSClick(self,sender,e):
        webbrowser.open("http://www.opengis.net/def/crs/EPSG/0")

#main class for the "scan-to-Graph" tab - element enrichment
class STG(forms.Panel):
    def __init__(self):
        self.STGLayout = forms.DynamicLayout()
        self.STGLayout.Padding = drawing.Padding(10)
        self.STGLayout.Spacing = drawing.Size(5,5)
        
        STG.SOList = []
        STG.SOList.append("self")
        STG.ProductTypes = self.GetProductTypes()
        STG.InformationList = self.GetBasicInfo()
        
        self.Information = self.CoreWidget()
        self.Information.Visible = False
        
        self.ObjectName = forms.Label(Text = "Object (Layer): ")
        STG.ObjectDropDown = forms.DropDown()
        
        self.StoreyLabel = forms.Label(Text = "Storey: ")
        self.SpaceLabel = forms.Label(Text = "Space: ")
        STG.StoreyDropDown = forms.DropDown(Enabled = False)
        STG.StoreyDropDown.DropDownOpening += self.setStoreyList
        STG.StoreyDropDown.SelectedIndexChanged += self.SaveObjectStorey
        STG.StoreyDropDown.GotFocus += self.setSpaceList
        
        self.SpaceLabel = forms.Label(Text = "Space: ")
        self.SelectedSpace = forms.Label(Text = "")
        self.SpaceButton = forms.Button(Text = "Select Space")
        
        STG.AssumptionDict = {}

        STG.SpaceDropDown = forms.DropDown(Enabled = False)
        STG.SpaceDropDown.SelectedIndexChanged += self.SaveObjectSpace
        
        STG.enableLOA = forms.CheckBox(Text = "set LOA     ", Visible = False)
        STG.enableLOA.CheckedChanged += self. LOAEnabled
        STG.LevelOfAccuracy = forms.NumericUpDown(DecimalPlaces = 0, Increment = 10, MaxValue = 50, MinValue = 10, Value = 10, Width = 40, Enabled = False, Visible = False)
        STG.MicroAnalysis = forms.CheckBox(Text = "Micro-scale", Enabled = False, Visible = False)
        STG.LevelOfAccuracy.LostFocus += self.setLOA
        STG.MicroAnalysis.CheckedChanged += self.setDeviationMethod

        self.PrintButton = forms.Button(Text = "Open currently set info in log.txt", Enabled = True,Visible = True)
        self.PrintButton.Click += self.Printer
        
        NewLayers = rs.LayerNames(sort = True)
        NewLayers.remove("Default")
        STG.ObjectDropDown.DataStore = NewLayers
        STG.ObjectDropDown.DropDownOpening += self.renewList
        STG.ObjectDropDown.SelectedIndexChanged += self.Change_Properties
        
        self.HostedCheckBox = forms.CheckBox(Text = "Hosted", Checked = False, Enabled = False)
        self.HostedCheckBox.CheckedChanged += self.HostedVisible
        self.HostedDropDown = forms.DropDown()
        self.HostedDropDown.Visible = False
        self.HostedDropDown.DropDownOpening +=self.renewHostedList
        self.HostedDropDown.SelectedIndexChanged += self.setHost
        
        self.AdjacentCheckBox = forms.CheckBox(Text = "Adjacent", Checked = False, Enabled = False)
        self.AdjacentCheckBox.CheckedChanged += self.AdjacentVisible
        self.AdjacentDropDown = forms.DropDown()
        self.AdjacentDropDown.Visible = False
        self.AdjacentDropDown.DropDownOpening +=self.renewAdjacentList
        self.AdjacentDropDown.SelectedIndexChanged += self.setSpace2
        
        self.STGLayout.BeginVertical()
        self.STGLayout.AddRow(self.ObjectName,STG.ObjectDropDown)
        self.STGLayout.AddRow(self.StoreyLabel, STG.StoreyDropDown)
        self.STGLayout.AddRow(self.SpaceLabel, STG.SpaceDropDown)
        self.STGLayout.AddRow(self.AdjacentCheckBox, self.AdjacentDropDown)
        self.STGLayout.AddRow(self.HostedCheckBox, self.HostedDropDown)
        self.STGLayout.EndVertical()
        self.STGLayout.BeginVertical()
        self.STGLayout.AddRow(STG.enableLOA,STG.LevelOfAccuracy,"    ", "    ", STG.MicroAnalysis)
        self.STGLayout.AddRow("")
        self.STGLayout.EndVertical()
        self.STGLayout.AddRow(self.Information)
        self.STGLayout.AddRow(self.PrintButton)
        self.STGLayout.AddRow(" ")
        self.Content = self.STGLayout
    
    #responds to the LOA method checkbox: links the scale of the used deviation analysis to the element
    def setDeviationMethod(self,sender,e):
        Object = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        for ObjectDict in STG.InformationList:
            if ObjectDict["Identifier"]==rs.LayerId(Object):
                if STG.MicroAnalysis.Checked == True:
                    ObjectDict["DeviationMethod"] = "MICROSCALE"
                else:
                    ObjectDict["DeviationMethod"] = "MACROSCALE"
    
    #makes the LOA numeric widget  and the LOA deviation method checkbox visible, when the 'set LOA' checkbox is checked
    def LOAEnabled(self,sender,e):
        Object = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        if STG.enableLOA.Checked == True:
            STG.LevelOfAccuracy.Enabled = True
            STG.LevelOfAccuracy.Visible = True
            STG.MicroAnalysis.Enabled = True
            STG.MicroAnalysis.Visible = True
            STG.MicroAnalysis.Checked = False
            """for ObjectDict in STG.InformationList:
                if ObjectDict["Identifier"]==rs.LayerId(Object):
                    ObjectDict["LOA"] = str(10)
                    ObjectDict["DeviationMethod"] = 'MACROSCALE'"""
            
        else:
            STG.LevelOfAccuracy.Enabled = False
            STG.LevelOfAccuracy.Visible = False
            STG.MicroAnalysis.Enabled = False
            STG.MicroAnalysis.Visible = False
            STG.MicroAnalysis.Checked = False
            
            for ObjectDict in STG.InformationList:
                if ObjectDict["Identifier"]==rs.LayerId(Object):
                    if "LOA" in ObjectDict:
                        del ObjectDict["LOA"]
                    if "DeviationMethod" in ObjectDict:
                        del ObjectDict["DeviationMethod"]
    
    #responds to the LOA numeric widget, links the LOA that was found in the deviation analysis to the element
    def setLOA(self,sender,e):
        Object = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        for ObjectDict in STG.InformationList:
            if ObjectDict["Identifier"]==rs.LayerId(Object):
                ObjectDict["LOA"] = int((STG.LevelOfAccuracy.Value/10))*10
                if STG.MicroAnalysis.Checked == True:
                    ObjectDict["DeviationMethod"] = "MICROSCALE"
                else:
                    ObjectDict["DeviationMethod"] = "MACROSCALE"
                print ObjectDict
    
    #avoids an initialisation crash by disabling buttons before any object is selected in the ObjectDropdown (before the first object is picked)
    global enableButtons
    def enableButtons(self):
        STG.SpaceDropDown.Enabled = True
        STG.StoreyDropDown.Enabled = True
        if len(STG.ObjectDropDown.DataStore)>=2:
            self.HostedCheckBox.Enabled = True
        else:
            self.HostedCheckBox.Enabled = False
        self.AdjacentCheckBox.Enabled = True
        self.Information.Visible = True
        self.PrintButton.Enabled = True
        self.PrintButton.Visible = True
        STG.enableLOA.Visible = True
    
    #renews the datastore in the Adjacent Object Dropdown when it is opened
    def renewAdjacentList(self,sender,e):
        Rooms = []
        KeepSelected = ""
        Object = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        for storey,rooms in Project_Info.TopoDict.iteritems():
            for room in rooms:
                Rooms.append(room)
                
        for ObjectDict in STG.InformationList:
                if ObjectDict["Identifier"]==rs.LayerId(Object):
                    if "Space2" in ObjectDict:
                        KeepSelected = ObjectDict["Space2"]
            
        self.AdjacentDropDown.DataStore = Rooms
        if KeepSelected in self.AdjacentDropDown.DataStore:
                index = self.AdjacentDropDown.DataStore.index(KeepSelected)
                self.AdjacentDropDown.SelectedIndex = index
    
    #renews the datastore in the Hosted Object Dropdown when it is opened
    def renewHostedList(self,sender,e):
        NewDataStore = []
        KeepSelected = ""
        Object = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        for ObjectDict in STG.InformationList:
                if ObjectDict["Identifier"]==rs.LayerId(Object):
                    if "isHostedBy" in ObjectDict:
                        KeepSelected = ObjectDict["isHostedBy"]
        for item in STG.ObjectDropDown.DataStore:
            NewDataStore.append(item)
        
        self.HostedDropDown.DataStore = sorted(NewDataStore)
        if KeepSelected in self.HostedDropDown.DataStore:
                index = self.HostedDropDown.DataStore.index(KeepSelected)
                self.HostedDropDown.SelectedIndex = index
    
    #The Adjacent Dropdown becomes visible when the checkbox is checked and there are rooms in the file (set in the Project Info Tab)
    def AdjacentVisible(self,sender,e):
        Layer = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        Rooms = []
        for storey,rooms in Project_Info.TopoDict.iteritems():
            for room in rooms:
                Rooms.append(room)
        if self.AdjacentCheckBox.Checked == True:
            if len(Rooms)>0:
                self.AdjacentDropDown.Enabled = True
                self.AdjacentDropDown.Visible = True
                
                STG.renewAdjacentList(self,0,0)
                for ObjectDict in STG.InformationList:
                    if ObjectDict["Identifier"]==rs.LayerId(Layer):
                        if "Space2" in ObjectDict:
                            if ObjectDict['Space2'] in self.AdjacentDropDown.DataStore:
                                index = self.AdjacentDropDown.DataStore.index(ObjectDict["Space2"])
                                self.AdjacentDropDown.SelectedIndex = index
                            else:
                                print 'error looking up hostedElement in datastore'
                        else:
                            if len(self.AdjacentDropDown.DataStore) >= 0:
                                self.AdjacentDropDown.SelectedIndex = 0
                                ObjectDict['Space2'] = self.AdjacentDropDown.DataStore[self.AdjacentDropDown.SelectedIndex]
                                ObjectDict['Adjacent'] = 'True'
            else: print 'no rooms defined yet'
        else:
            self.AdjacentDropDown.Enabled = False
            self.AdjacentDropDown.Visible = False
            for ObjectDict in STG.InformationList:
                if ObjectDict["Identifier"]==rs.LayerId(Layer):
                    if "Space2" in ObjectDict:
                        del ObjectDict["Space2"]
                    if "Adjacent" in ObjectDict:
                        del ObjectDict["Adjacent"]

    #when the Checkbox for the element being hosted is checked, the HostedDropdown becomes visible
    def HostedVisible(self, sender, e):
        Layer = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        if self.HostedCheckBox.Checked == True:
            self.HostedDropDown.Enabled = True
            self.HostedDropDown.Visible = True
            STG.renewHostedList(self,0,0)
            for ObjectDict in STG.InformationList:
                if ObjectDict["Identifier"]==rs.LayerId(Layer):
                    if "isHostedBy" in ObjectDict:
                        if ObjectDict['isHostedBy'] in self.HostedDropDown.DataStore:
                            index = self.HostedDropDown.DataStore.index(ObjectDict["isHostedBy"])
                            self.HostedDropDown.SelectedIndex = index
                        else:
                            print 'error looking up hostedElement in datastore'
                    else:
                        if len(self.HostedDropDown.DataStore) >= 0:
                            self.HostedDropDown.SelectedIndex = 0
                            ObjectDict['isHostedBy'] = self.HostedDropDown.DataStore[self.HostedDropDown.SelectedIndex]
        else:
            self.HostedDropDown.Enabled = False
            self.HostedDropDown.Visible = False
            for ObjectDict in STG.InformationList:
                if ObjectDict["Identifier"]==rs.LayerId(Layer):
                    if "isHostedBy" in ObjectDict:
                        del ObjectDict["isHostedBy"]
    
    #The list with the spaces adapts to which storey is selected in the Storey Dropdown
    def setSpaceList(self,sender,e):
        if self.StoreyDropDown.SelectedIndex >= 0:
            storey = self.StoreyDropDown.DataStore[self.StoreyDropDown.SelectedIndex]
            self.SpaceDropDown.DataStore = Project_Info.TopoDict[storey]
    
    #all information that is already set is printed to an external log file, which opens in the default text editor. 
    #This happens when clicking the Print information button at the bottom of this tab
    def Printer(self,sender,e):
        logfile = str(ProjectFolder + r'\\' + "log.txt")
        with open(logfile,"w") as log:
            try:
                print >>log,"PROJECT INFO:"
                if len(Project_Info.ProjectInfo)>0:
                    for key,value in Project_Info.ProjectInfo.iteritems():
                        print >>log,"    ",key,":",value
                else: print >>log,'Project Info not set'
                print >>log,' '
                print >>log,"PROJECT STOREYS/ROOMS:"
                if len(Project_Info.TopoDict)>0:
                    for key, value in Project_Info.TopoDict.iteritems():
                        print >>log,"    ",'storey ',key," has rooms:",value
                else: print >>log,"Storeys and rooms not set"
                print >>log,' '
                print >>log,"ASSUMPTIONS/OCCLUSIONS"
                if len(STG.AssumptionDict)>0:
                    for key,value in STG.AssumptionDict.iteritems():
                        if len(value)>0:
                            print >>log, "    ",key,":",value
                else: print >>log,'No assumptions or occlusions made'
                print >>log," "
                print >>log,"OBJECT INFORMATION: "
                for item in STG.InformationList:
                    print >>log," "
                    for key,value in item.iteritems():
                        if key == "Name":
                            print >>log,key, ":", value
                    for key,value in item.iteritems():
                        if key != "Name":
                            if key != "Aggregates":
                                print >>log, "     ",key,":", value
                    for key,value in item.iteritems():
                        if key == "Aggregates":
                            print >>log,"     ",key,":"
                            for item in value:
                                for SOkey,SOvalue in item.iteritems():
                                    if SOkey == "Name":
                                        print >>log,"             ", SOkey," : ",SOvalue
                                for SOkey,SOvalue in item.iteritems():
                                    if SOkey != "Name":
                                        print >>log,"             ", SOkey," : ",SOvalue
                                print >>log," "
                print >>log," "
                editor = os.getenv('EDITOR')
                if editor:
                    ps.system(editor + ' ' + logfile)
                else:
                    webbrowser.open(logfile)
                    
            except: print 'file writing did not succeed completely'
            
    #when the ObjectSpace changes in the DropDown list, this is immediately saved to the basic dictionary
    def SaveObjectSpace(self,sender,e):
        if STG.ObjectDropDown.SelectedIndex >= 0:
            Layer = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
            for ObjectDict in STG.InformationList:
                if ObjectDict["Identifier"]==rs.LayerId(Layer):
                    ObjectDict["Space"] = STG.SpaceDropDown.DataStore[STG.SpaceDropDown.SelectedIndex]
    
    #layout widget for the object's additional information: type, subobjects and info about subobjects, geometry and remarks on geometries
    def CoreWidget(self):
        self.CoreGB = forms.GroupBox(Text = "Object Information")
        self.CoreGB.Padding = drawing.Padding(10)
        self.CoreLayout = forms.DynamicLayout()
        self.CoreLayout.Padding = drawing.Padding(10)
        self.CoreLayout.Spacing = drawing.Size(5,5)
        
        Label_type = forms.Label(Text = "> Type: ")
        Product_Ontology_types = STG.ProductTypes
        self.DropDown_type = forms.DropDown(DataStore = STG.ProductTypes)
        self.DropDown_type.SelectedIndexChanged += self.SaveObjectType
        
        Label_aggregates = forms.Label(Text = "> Sub-Objects: ")
        Aggregates = self.Aggregate_Objects()
        Label_entities = forms.Label(Text = "Sub-Object has Geometries: ")
        Objects = self.SO_Geometry()
        STG.select_Objects = forms.Button(Text = "Select")
        STG.remove_Objects = forms.Button(Text = "Remove", Enabled = False)
        STG.select_Objects.Click += self.ObjectSelector
        STG.remove_Objects.Click += self.ObjectRemover
        
        STG.createAssumption = forms.Button(Text = "Remark", Enabled = False)
        STG.createAssumption.Click += self.Assumption
        
        STG.OcclusionButton = forms.Button(Text = "Occlusion", Enabled = False)
        STG.OcclusionButton.Click += self.Occlusion
        
        AssumptionWidget = self.AssumptionList()
        
        self.removeAssumptionButton = forms.Button(Text = "Remove", Enabled = False)
        self.removeAssumptionButton.Click += self.removeAssumption
        
        self.CoreLayout.BeginVertical()
        self.CoreLayout.AddRow(Label_type, self.DropDown_type, None, None)
        self.CoreLayout.AddRow('')
        self.CoreLayout.AddRow(Label_aggregates,None,None,None)
        self.CoreLayout.EndVertical()
        self.CoreLayout.BeginVertical()
        self.CoreLayout.AddRow(Aggregates)
        self.CoreLayout.AddRow(' ')
        self.CoreLayout.EndVertical()
        self.CoreLayout.BeginVertical()
        self.CoreLayout.AddRow(Label_entities, None,None,None)
        self.CoreLayout.EndVertical()
        self.CoreLayout.BeginVertical()
        self.CoreLayout.AddRow(Objects)
        self.CoreLayout.EndVertical()
        self.CoreLayout.BeginVertical()
        self.CoreLayout.AddRow(STG.createAssumption,STG.OcclusionButton,None,STG.remove_Objects,STG.select_Objects)
        self.CoreLayout.AddRow(" ")
        self.CoreLayout.EndVertical()
        self.CoreLayout.BeginVertical()
        self.CoreLayout.AddRow(AssumptionWidget)
        self.CoreLayout.EndVertical()
        self.CoreLayout.BeginVertical()
        self.CoreLayout.AddRow(None,None,None,self.removeAssumptionButton)
        self.CoreLayout.BeginVertical()
        self.CoreGB.Content = self.CoreLayout
        return self.CoreGB
    
    #links a remark on an occluded geometry to the geometry in the STG.AssumptionDict
    def Occlusion(self,sender,e):
        DisplayList = []
        index = self.SO_Geometry.SelectedIndex
        OccludedObject = str(self.SO_Geometry.DataStore[index])
        OccludedObject = OccludedObject.split(',')
        OccludedObject = OccludedObject[0]
        if OccludedObject in STG.AssumptionDict:
            if "OCCLUDED_AREA" not in STG.AssumptionDict[OccludedObject]:
                STG.AssumptionDict[OccludedObject].append("OCCLUDED_AREA")
        else:
            STG.AssumptionDict[OccludedObject] = []
            STG.AssumptionDict[OccludedObject].append("OCCLUDED_AREA")
        
        ParentObject = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        for ObjectDict in STG.InformationList:
            if ObjectDict["Identifier"]==rs.LayerId(ParentObject):
                if "Aggregates" in ObjectDict:
                    for SODict in ObjectDict["Aggregates"]:
                        if SODict["Name"] == self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex]:
                            for aggregate in SODict["Geometry"]:
                                if aggregate in STG.AssumptionDict:
                                    DisplayText = str(aggregate)
                                    DisplayList.append(DisplayText)
                                    
                                    List = []
                                    for item in STG.AssumptionDict[aggregate]:
                                        List.append(item)
                                    self.AssumptionList.DataStore = List
                                    self.removeAssumptionButton.Enabled = True
                                    
                                else:
                                    DisplayList.append(aggregate)
                                    
                                self.SO_Geometry.DataStore = DisplayList
                                
                if "Geometry" in ObjectDict:
                    for geometry in ObjectDict["Geometry"]:
                        if geometry in STG.AssumptionDict:
                            DisplayText = str(geometry)
                            DisplayList.append(DisplayText)
                            
                            List = []
                            for item in STG.AssumptionDict[geometry]:
                                List.append(item)
                            self.AssumptionList.DataStore = List
                            self.removeAssumptionButton.Enabled = True
                            
                        else:
                            DisplayList.append(geometry)
        self.SO_Geometry.SelectedIndex = index
        
        geometry = self.SO_Geometry.DataStore[self.SO_Geometry.SelectedIndex]
        if geometry in STG.AssumptionDict:
            List = []
            for item in STG.AssumptionDict[geometry]:
                List.append(item)
            self.AssumptionList.DataStore = List
            self.removeAssumptionButton.Enabled = True
        else:
            self.removeAssumptionButton.Enabled = False
            self.AssumptionList.DataStore = []
        if len(self.AssumptionList.DataStore) == 0:
            self.removeAssumptionButton.Enabled = False
   
    #links a general modelling remark (so not only 'assumptions', despite the name) to a geometry in the STG.AssumptionDict
    def Assumption(self,sender,e):
        index = self.SO_Geometry.SelectedIndex
        DisplayList = []
        rc, text  = Rhino.UI.Dialogs.ShowEditBox("Remark", "Add a modelling remark to this element:", None, 0)
        if rc != True: return None
        else:
            if len(text)>0:
                AssumptionObject = str(self.SO_Geometry.DataStore[index])
                AssumptionObject = AssumptionObject.split(',')
                AssumptionObject = AssumptionObject[0]
                if AssumptionObject in STG.AssumptionDict:
                    STG.AssumptionDict[AssumptionObject].append(text)
                else:
                    STG.AssumptionDict[AssumptionObject] = []
                    STG.AssumptionDict[AssumptionObject].append(text)
                ParentObject = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
                for ObjectDict in STG.InformationList:
                    if ObjectDict["Identifier"]==rs.LayerId(ParentObject):
                        if "Aggregates" in ObjectDict:
                            for SODict in ObjectDict["Aggregates"]:
                                if SODict["Name"] == self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex]:
                                    for aggregate in SODict["Geometry"]:
                                        if aggregate in STG.AssumptionDict:
                                            DisplayText = str(aggregate)
                                            DisplayList.append(DisplayText)
                                            
                                            List = []
                                            for item in STG.AssumptionDict[aggregate]:
                                                List.append(item)
                                            self.AssumptionList.DataStore = List
                                            self.removeAssumptionButton.Enabled = True
                                            
                                        else:
                                            DisplayList.append(aggregate)
                                            
                                        self.SO_Geometry.DataStore = DisplayList
                                        
                        if "Geometry" in ObjectDict:
                            for geometry in ObjectDict["Geometry"]:
                                if geometry in STG.AssumptionDict:
                                    DisplayText = str(geometry)
                                    DisplayList.append(DisplayText)
                                    
                                    List = []
                                    for item in STG.AssumptionDict[geometry]:
                                        List.append(item)
                                    self.AssumptionList.DataStore = List
                                    self.removeAssumptionButton.Enabled = True
                                    
                                else:
                                    DisplayList.append(geometry)
                        
                        
        
        self.SO_Geometry.SelectedIndex = index
        
        geometry = self.SO_Geometry.DataStore[self.SO_Geometry.SelectedIndex]
        if geometry in STG.AssumptionDict:
            List = []
            for item in STG.AssumptionDict[geometry]:
                List.append(item)
            self.AssumptionList.DataStore = List
            self.removeAssumptionButton.Enabled = True
        else:
            self.removeAssumptionButton.Enabled = False
            self.AssumptionList.DataStore = []
        if len(self.AssumptionList.DataStore) == 0:
            self.removeAssumptionButton.Enabled = False
    
    #Button to removes an object from the Geometries of a subobject (to remove a geometry from a main object, remove it from the layer)
    def ObjectRemover(self,sender,e):
        index = self.SO_Geometry.SelectedIndex
        selectedGeometry = self.SO_Geometry.DataStore[index]
        Object = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        for ObjectDict in STG.InformationList:
            if ObjectDict["Identifier"]==rs.LayerId(Object):
                for SODict in ObjectDict["Aggregates"]:
                    if SODict["Name"] == self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex]:
                        if self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex] != "self":
                            if "Geometry" in SODict:
                                if selectedGeometry in SODict["Geometry"]:
                                    SODict["Geometry"].remove(selectedGeometry)
                                    newList = []
                                    for item in SODict["Geometry"]:
                                        newList.append(str(item))
                                    self.SO_Geometry.DataStore = newList
                            
        if len(self.SO_Geometry.DataStore)>0:
            STG.createAssumption.Enabled = True
            STG.OcclusionButton.Enabled = True
            STG.remove_Objects.Enabled = True
        else: 
            STG.remove_Objects.Enabled = False
            
    #select the objects in the viewport that should be aggregated by the subobject. These geometries appear in the Geometry listbox of the subobject and can be selected or removed later on.
    def ObjectSelector(self,sender,e):
        STG.select_Objects.Enabled = False
        CurrentLayer = rs.CurrentLayer()
        activeLayers = []
        visibleLayers = []
        allLayers = rs.LayerNames()
        for Layer in allLayers:
            if rs.LayerLocked(Layer) == False:
                activeLayers.append(Layer)
            if rs.LayerVisible(Layer) == True:
                visibleLayers.append(Layer)
        
        ParentObject = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        rs.CurrentLayer(ParentObject)

        for Layer in allLayers:
            if Layer != ParentObject and Layer != "Default":
                rs.LayerLocked(Layer, True)
        SelectedObjects = rs.GetObjects("Select parts of Subobject " + self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex], group = True, preselect = False)
        
        if SelectedObjects is None:
            STG.select_Objects.Enabled = True
            return
        else: 
            STG.select_Objects.Enabled = True
            
                
        if sc.escape_test(False): return
        
        for Object in SelectedObjects:
            if rs.ObjectLayer(Object) == "Default":
                rs.ObjectLayer(Object, layer = ParentObject)
                
        SOName = self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex]
        for ObjectDict in STG.InformationList:
            if ObjectDict["Identifier"]==rs.LayerId(ParentObject):
                for SODict in ObjectDict["Aggregates"]:
                    if SODict["Name"] == self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex]:
                        if "Geometry" in SODict:
                            already_present = list(SODict["Geometry"])
                            for objectID in SelectedObjects:
                                if not str(objectID) in already_present:
                                    if rs.ObjectType(objectID) != 2:
                                        already_present.append(str(objectID))
                            SODict["Geometry"] = already_present
                        else:
                            items_to_add = []
                            for item in SelectedObjects:
                                if rs.ObjectType(item) != 2:
                                    items_to_add.append(str(item))
                            SODict["Geometry"] = items_to_add
                                
        for ObjectDict in STG.InformationList:
            if ObjectDict["Identifier"]==rs.LayerId(ParentObject):
                for SODict in ObjectDict["Aggregates"]:
                    if SODict["Name"] == self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex]:
                        if self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex] == "self":
                            geom_str = []
                            for geom in rs.ObjectsByLayer(ObjectLayer):
                                if rs.ObjectType(geom) != 2:
                                    geom_str.append(str(geom))
                            ObjectDict["Geometry"]= geom_str
                            self.SO_Geometry.DataStore = geom_str
                            self.SO_Geometry.Enabled = False
                            STG.select_Objects.Enabled = False
                        else:
                            DisplayList = []
                            for aggregate in SODict["Geometry"]:
                                if aggregate in STG.AssumptionDict:
                                    DisplayText = str(aggregate)
                                    DisplayList.append(DisplayText)
                                else:
                                    DisplayList.append(aggregate)
                                self.SO_Geometry.DataStore = DisplayList
                            self.SO_Geometry.Enabled = True
                            STG.select_Objects.Enabled = True
                            
        if len(self.SO_Geometry.DataStore)>0:
            STG.createAssumption.Enabled = True
            STG.OcclusionButton.Enabled = True
            STG.remove_Objects.Enabled = True
        else:
            STG.remove_Objects.Enabled = False
     
    #layout for the object-geometry listbox
    def SO_Geometry(self):
        self.SO_Geometry = forms.ListBox(Height = 150)
        Object_Info = []
        self.SO_Geometry.DataStore = Object_Info
        self.SO_Geometry.SelectedIndexChanged += self.SelectObjectInViewPort
        return self.SO_Geometry
    
    #layout for the assumption listbox at the bottom of the tab
    def AssumptionList(self):
        self.AssumptionList = forms.ListBox(Height = 100)
        Assumptions = []
        self.AssumptionList.DataStore = Assumptions
        return self.AssumptionList
    
    #when the remove button is pressed, the remark is deleted. A remark can be a general remark, an assumption , an 'INNERPART' remark or an occlusion. 
    def removeAssumption(self,sender,e):
        index = self.AssumptionList.SelectedIndex
        ParentObject = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        for ObjectDict in STG.InformationList:
            if ObjectDict["Identifier"]==rs.LayerId(ParentObject):
                if "Aggregates" in ObjectDict:
                    for SODict in ObjectDict["Aggregates"]:
                        if SODict["Name"] == self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex]:
                            for geometry in SODict["Geometry"]:
                                if self.SO_Geometry.DataStore[self.SO_Geometry.SelectedIndex] == geometry:
                                    if geometry in STG.AssumptionDict:
                                        STG.AssumptionDict[geometry].remove(self.AssumptionList.DataStore[index])
                                        self.AssumptionList.DataStore = STG.AssumptionDict[geometry]
                                    else:
                                        self.removeAssumptionButton.Enabled = False
                                    if len(self.AssumptionList.DataStore) == 0:
                                        self.removeAssumptionButton.Enabled = False
                                        del STG.AssumptionDict[geometry]
                                        
                if "Geometry" in ObjectDict:
                    for geometry in ObjectDict["Geometry"]:
                        if self.SO_Geometry.DataStore[self.SO_Geometry.SelectedIndex] == geometry:
                            if geometry in STG.AssumptionDict:
                                STG.AssumptionDict[geometry].remove(self.AssumptionList.DataStore[index])
                                self.AssumptionList.DataStore = STG.AssumptionDict[geometry]
                            else:
                                self.removeAssumptionButton.Enabled = False
                            if len(self.AssumptionList.DataStore) == 0:
                                self.removeAssumptionButton.Enabled = False
                                del STG.AssumptionDict[geometry]
    
   #when an element is selected in the subobject-geometry box, this element is also selected in the viewport and its remarks are displayed in the Remark Listbox
    def SelectObjectInViewPort(self, sender, e):
        try:
            index = self.SO_Geometry.SelectedIndex
            ParentObject = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
            for ObjectDict in STG.InformationList:
                if ObjectDict["Identifier"]==rs.LayerId(ParentObject):
                    if self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex] == "self":
                        geom_str = []
                        for geom in rs.ObjectsByLayer(ParentObject):
                            if rs.ObjectType(geom) != 2:
                                geom_str.append(str(geom))
                        ObjectDict["Geometry"]= geom_str
                        self.SO_Geometry.DataStore = geom_str
                        for geometry in ObjectDict["Geometry"]:
                            if self.SO_Geometry.DataStore[self.SO_Geometry.SelectedIndex] == geometry:
                                if geometry in STG.AssumptionDict:
                                    List = []
                                    for item in STG.AssumptionDict[geometry]:
                                        List.append(item)
                                    self.AssumptionList.DataStore = List
                                    self.removeAssumptionButton.Enabled = True
                                else:
                                    self.removeAssumptionButton.Enabled = False
                                    self.AssumptionList.DataStore = []
                                if len(self.AssumptionList.DataStore) == 0:
                                    self.removeAssumptionButton.Enabled = False
                                                
                    if "Aggregates" in ObjectDict:
                        for SODict in ObjectDict["Aggregates"]:
                            if SODict["Name"] == self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex]:
                                if self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex] != "self":
                                    self.SO_Geometry.Enabled = True
                                    for geometry in SODict["Geometry"]:
                                        if self.SO_Geometry.DataStore[self.SO_Geometry.SelectedIndex] == geometry:
                                            if geometry in STG.AssumptionDict:
                                                List = []
                                                for item in STG.AssumptionDict[geometry]:
                                                    List.append(item)
                                                self.AssumptionList.DataStore = List
                                                self.removeAssumptionButton.Enabled = True
                                            else:
                                                self.removeAssumptionButton.Enabled = False
                                                self.AssumptionList.DataStore = []
                                            if len(self.AssumptionList.DataStore) == 0:
                                                self.removeAssumptionButton.Enabled = False
    
            if index >= 0:
                item = str(self.SO_Geometry.DataStore[index])
                Rhino.RhinoApp.RunScript("_SelNone", False)
                Rhino.RhinoApp.RunScript("_SelId " + item + " _Enter", False)
        except: print "index out of range"
    
    #layout for the subobject settings
    def Aggregate_Objects(self):
        self.SOLayout = forms.DynamicLayout()
        self.SubObjectListBox = forms.ListBox(Height = 80)
        self.SubObjectListBox.DataStore = STG.SOList
        self.SubObjectListBox.SelectedIndexChanged += self.SaveSOProps
        
        self.SOInfo = forms.DynamicLayout()
        self.SOInfo.Padding = drawing.Padding(10)
        self.SOInfo.Spacing = drawing.Size(5,5)
        
        self.NewButton = forms.Button(Text = "Construct New")
        self.NewButton.Click += self.addAggregate
        
        self.DeleteButton = forms.Button(Text = "Delete")
        self.DeleteButton.Click += self.DeleteAggregate
        
        SOName = forms.Label(Text = "Name: ")
        self.SONameBox = forms.TextBox()
        self.SONameBox.LostFocus += self.refreshSOList
        
        SOType = forms.Label(Text = "Type: ")
        self.SOTypeBox = forms.DropDown()
        self.SOTypeBox.DataStore = STG.ProductTypes
        self.SOTypeBox.SelectedIndexChanged += self.SOTypeboxChanges
        
        self.SORelationship = forms.Label(Text = "Relationship with Parent: ")
        self.SORelationBox = forms.DropDown()
        self.RelationshipStore = ["aggregated","hosted"]
        self.SORelationBox.DataStore = self.RelationshipStore
        self.SORelationBox.SelectedIndex = 0
        self.SORelationBox.SelectedIndexChanged += self.SORelationChanges
        
        self.SOfromSOLabel = forms.Label(Text = "(opt.) Part of Sub-Object")
        self.SOfromSODropDown = forms.DropDown(DataStore = [])
        self.SOfromSODropDown.DropDownOpening += self.setSOfromSODataStore
        self.SOfromSODropDown.SelectedIndexChanged += self.SaveSOfromSO
        
        self.SOInfo.BeginVertical()
        self.SOInfo.AddRow(SOName,self.SONameBox)
        self.SOInfo.AddRow(SOType,self.SOTypeBox)
        self.SOInfo.AddRow(self.SORelationship,self.SORelationBox)
        self.SOInfo.AddRow(self.SOfromSOLabel, self.SOfromSODropDown)
        self.SOInfo.EndVertical()
        self.SOInfo.BeginVertical()
        self.SOInfo.AddRow('')
        self.SOInfo.AddRow(None,self.NewButton,self.DeleteButton)
        self.SOInfo.EndVertical()
        
        self.SOLayout.AddRow(self.SubObjectListBox,self.SOInfo)
        return self.SOLayout
    
    #the 'subobject-from-subobject' datastore contains all other subobjects of a main object. An object cannot be a subobject from itself. 
    def setSOfromSODataStore(self, sender, e):
        NewDataStore = []
        for item in self.SubObjectListBox.DataStore:
            NewDataStore.append(item)        
        NewDataStore.append('-NONE-')
        NewDataStore.remove('self')
        CurrentSO = self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex]
        NewDataStore.remove(CurrentSO)
        self.SOfromSODropDown.DataStore = sorted(NewDataStore)
        
    #initialisation of product types from the product Ontology (https://github.com/pipauwel/product)and the custom products from the custom_types.csv file in the installation directory
    def GetProductTypes(self):
        csvfile = str(ProjectFolder + r'\\' + "product_ontology.csv")
        ProductTypes = ["-not specified-"]
        with open(csvfile, 'rb') as csvreadfile:
            read = csv.reader(csvreadfile, dialect = 'excel')
            for item in read:
                if len(item)>0:
                    if "http" in item[0]:
                        item = item[0].split("#")
                        item = item[-1]
                        ProductTypes.append("product:"+item)
        
        csvfile = str(ProjectFolder + r'\\' + "custom_types.csv")
        with open(csvfile, 'rb') as csvreadfile:
            read = csv.reader(csvreadfile, dialect = 'excel')
            for item in read:
                if len(item)>0:
                    if "http" in item[0]:
                        item = item[0].split("#")
                        item = item[-1]
                        ProductTypes.append("stgp:"+item)
        return sorted(ProductTypes)

    #initialisation of available information when the plugin is started, 
    #based on the info that is present in the Layers that exist prior to starting the plugin: Layername, Identifier, Point Clouds, Objects, Geometry. The type is guessed from the layer's name
    def GetBasicInfo(self):
        InformationList = []
        ProjectLayers = rs.LayerNames()
        ProjectLayers.remove("Default")
        for Layer in ProjectLayers:
            LayerDict = {}
            LayerDict["Name"] = Layer
            LayerDict["Identifier"] = rs.LayerId(Layer)
            
            Layer_upper = Layer.upper()
            
            sortedlist = list(reversed(sorted(STG.ProductTypes, key = len)))
            Types_upper = []
            for type in sortedlist:
                if ':' in type:
                    type=type.split(':')
                    type=type[1]
                    type=type.upper()
                    Types_upper.append(type)
                else: Types_upper.append(type)
            for typeupper,type in zip(Types_upper,sortedlist):
                if typeupper in str(Layer_upper):
                    LayerDict["Type"] = type
                    break
            objects = rs.ObjectsByLayer(Layer)
            PointCloud = rs.ObjectsByType(2)
            pointclouds_in_layer = list(set(objects) & set(PointCloud))
            if len(pointclouds_in_layer)>0:
                #Point Cloud FileName => does not have URI yet!
                LayerDict["PointCloud"] = []
                for PC in pointclouds_in_layer:
                    LayerDict["PointCloud"].append(str(rs.ObjectName(PC)))
            InformationList.append(LayerDict)
            
        return InformationList
    
    #the Hosting Element is set when a new index is selected in the Hosted-Dropdown
    def setHost(self,sender,e):
        Layer = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        for ObjectDict in STG.InformationList:
            if ObjectDict["Identifier"]==rs.LayerId(Layer):
                ObjectDict["isHostedBy"] = self.HostedDropDown.DataStore[self.HostedDropDown.SelectedIndex]
    
    #the other space which is adjacent to an 'Adjacent element'. This hierarchy is fictional and exists purely in the plugin
    def setSpace2(self,sender,e):
        Layer = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        for ObjectDict in STG.InformationList:
            if ObjectDict["Identifier"]==rs.LayerId(Layer):
                ObjectDict["Space2"] = self.AdjacentDropDown.DataStore[self.AdjacentDropDown.SelectedIndex]
                ObjectDict["Adjacent"] = "True"
    
    #when the ObjectType changes in the TypeDropDown list, this type is immediately saved to the basic dictionary
    def SaveObjectType(self,sender,e):
        Layer = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        for ObjectDict in STG.InformationList:
            if ObjectDict["Identifier"]==rs.LayerId(Layer):
                ObjectDict["Type"] = self.DropDown_type.DataStore[self.DropDown_type.SelectedIndex]
                
    #when the ObjectStorey changes in the DropDown list, this is immediately saved to the basic dictionary
    def SaveObjectStorey(self,sender,e):
        if STG.ObjectDropDown.SelectedIndex >= 0:
            try:
                Layer = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
                for ObjectDict in STG.InformationList:
                    if ObjectDict["Identifier"]==rs.LayerId(Layer):
                        ObjectDict["Storey"] = STG.StoreyDropDown.DataStore[STG.StoreyDropDown.SelectedIndex]
                        STG.SpaceDropDown.DataStore = Project_Info.TopoDict[ObjectDict["Storey"]]
            except: 
                print 'error at selecting item in StoreyDropdown'
    
    #the datastore from the storey-dropdown is set to the storeys that were defined in the Project Info tab
    def setStoreyList(self,sender,e):
        copyList = []
        for item in Project_Info.Storeys:
            copyList.append(item)
        STG.StoreyDropDown.DataStore = copyList
                
    #when a new object is selected in the object dropdown menu, all widgets need to be refreshed to correspond to the attributes of the newly selected element
    def Change_Properties(self,sender,e):
        enableButtons(self)
        ObjectStore = []
        for ObjectDict in STG.InformationList:
            ObjectStore.append(ObjectDict["Name"])
        STG.ObjectDropDown.DataStore = ObjectStore
        Layer = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        NewLayer = True
        for ObjectDict in STG.InformationList:
            if ObjectDict["Identifier"]==rs.LayerId(Layer):
                NewLayer = False
                geom_str = []
                for geom in rs.ObjectsByLayer(Layer):
                    if rs.ObjectType(geom) != 2:
                        geom_str.append(str(geom))
                ObjectDict["Geometry"]= geom_str
                if ObjectDict["Name"] != Layer:
                    ObjectDict["Name"] = Layer
                if "Type" in ObjectDict:
                    index = STG.ProductTypes.index(ObjectDict["Type"])
                    self.DropDown_type.SelectedIndex = index
                else:
                    Layer_upper = Layer.upper()
                    sortedlist = list(reversed(sorted(STG.ProductTypes, key = len)))
                    Types_upper = [type.upper() for type in sortedlist]
                    for typeupper,type in zip(Types_upper,sortedlist):
                        if typeupper in str(Layer_upper):
                            ObjectDict["Type"] = type
                            index = STG.ProductTypes.index("  ")
                            self.DropDown_type.SelectedIndex = index
                            break
                try:
                    if "Storey" in ObjectDict:
                        if "Space" in ObjectDict:
                            #very strange bug changes also ObjectDict["Space"]
                            strangeBug = ObjectDict["Space"]
                            try:
                                StoreyIndex = Project_Info.Storeys.index(ObjectDict["Storey"])
                                STG.StoreyDropDown.SelectedIndex = StoreyIndex
                            except: print "could not set storey"
                        if "Space" in ObjectDict:
                            #ObjectDict["Space"] is reassigned to the strangeBug variable
                            ObjectDict["Space"] = strangeBug
                            try:
                                STG.SpaceDropDown.DataStore = Project_Info.TopoDict[ObjectDict["Storey"]]
                                index = STG.SpaceDropDown.DataStore.index(ObjectDict["Space"])
                                STG.SpaceDropDown.SelectedIndex = index
                            except: print "could not set space"
                    else:
                        if STG.StoreyDropDown.SelectedIndex>=0:
                            ObjectDict["Storey"] = STG.StoreyDropDown.DataStore[STG.StoreyDropDown.SelectedIndex]
                except: print "could not correctly set storey/space"
                try:
                    if "Space" in ObjectDict:
                        if "Storey" in ObjectDict:
                            STG.SpaceDropDown.DataStore = Project_Info.TopoDict[ObjectDict["Storey"]]
                            index = Project_Info.TopoDict[ObjectDict["Storey"]].index(ObjectDict["Space"])
                            STG.SpaceDropDown.SelectedIndex = index
                            
                    else: 
                        if "Storey" in ObjectDict:
                            if len(STG.SpaceDropDown.DataStore)>0:
                                ObjectDict["Space"] = STG.SpaceDropDown.DataStore[STG.SpaceDropDown.SelectedIndex]
                except: pass
                
                if "isHostedBy" in ObjectDict:
                    self.HostedCheckBox.Checked = True
                    STG.HostedVisible(self, 0, 0)
                else:
                    self.HostedCheckBox.Checked = False
                
                STG.SOList = ["self"]
                if "Aggregates" in ObjectDict:
                    for SODict in ObjectDict["Aggregates"]:
                        if "Name" in SODict:
                            self.SOList.append(SODict["Name"])
                        
                self.SubObjectListBox.DataStore = STG.SOList
                self.SubObjectListBox.SelectedIndex = 0
                if "Aggregates" in ObjectDict:
                    for SODict in ObjectDict["Aggregates"]:
                        if "Name" in SODict == STG.SOList[0]:
                            if "Type" in SODict:
                                SOindex = STG.ProductTypes.index(SODict["Type"])
                                self.SOTypeBox.SelectedIndex = SOindex
                                
                if "LOA" in ObjectDict:
                    STG.enableLOA.Checked = True
                    STG.LevelOfAccuracy.Enabled = True
                    STG.LevelOfAccuracy.Visible = True
                    STG.MicroAnalysis.Enabled = True
                    STG.MicroAnalysis.Visible = True
                    STG.LevelOfAccuracy.Value = int(ObjectDict["LOA"])
                    if ObjectDict["DeviationMethod"] == "MACROSCALE":
                        STG.MicroAnalysis.Checked = False
                    else:
                        STG.MicroAnalysis.Checked = True
                else:
                    STG.enableLOA.Checked = False
                    STG.LevelOfAccuracy.Enabled = False
                    STG.LevelOfAccuracy.Visible = False
                    STG.MicroAnalysis.Enabled = False
                    STG.MicroAnalysis.Visible = False
                
                
                if "Adjacent" in ObjectDict:
                    if ObjectDict["Adjacent"] == "True":
                        self.AdjacentCheckBox.Checked = True
                        self.AdjacentDropDown.Visible = True
                        self.AdjacentDropDown.Enabled = True
                        if "Space2" in ObjectDict:
                            self.AdjacentDropDown.SelectedIndex = self.AdjacentDropDown.DataStore.index(ObjectDict["Space2"])
                else:
                    self.AdjacentCheckBox.Checked = False
                    self.AdjacentDropDown.Visible = False
                    self.AdjacentDropDown.Enabled = False
                            
        if NewLayer == True:
            LayerDict = {}
            LayerDict["Name"] = Layer
            LayerDict["Identifier"] = rs.LayerId(Layer)
            Layer_upper = Layer.upper()
            
            sortedlist = list(reversed(sorted(STG.ProductTypes, key = len)))
            Types_upper = [type.upper() for type in sortedlist]
            for typeupper,type in zip(Types_upper,sortedlist):
                if typeupper in str(Layer_upper):
                    LayerDict["Type"] = type
            objects = rs.ObjectsByLayer(Layer)
            PointCloud = rs.ObjectsByType(2)
            pointclouds_in_layer = list(set(objects) & set(PointCloud))
            if len(pointclouds_in_layer)>0:
                #Point Cloud FileName => does not have URI yet!
                LayerDict["PointCloud"] = str(rs.ObjectName(pointclouds_in_layer[0])+".e57")
            else:
                LayerDict["PointCloud"] = None
            STG.InformationList.append(LayerDict)
        
        if len(self.SO_Geometry.DataStore)>0:
            STG.createAssumption.Enabled = True
            STG.OcclusionButton.Enabled = True
            STG.remove_Objects.Enabled = True
        else: 
            STG.createAssumption.Enabled = False
            STG.OcclusionButton.Enabled = False
            STG.remove_Objects.Enabled = False
        
        #blocking adaptations for "self"
        if self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex] == "self":
            self.SONameBox.Enabled = False
            self.SOTypeBox.SelectedIndex = self.DropDown_type.SelectedIndex
            self.SOTypeBox.Enabled = False
            self.SOfromSODropDown.Enabled = False
            self.SOfromSODropDown.Visible = False
            self.SORelationship.Visible = False
            self.SOfromSOLabel.Visible = False
            self.SORelationBox.Enabled = False
            self.SORelationBox.Visible = False
            geom_str = []
            for geom in rs.ObjectsByLayer(Layer):
                if rs.ObjectType(geom) != 2:
                    geom_str.append(str(geom))
            ObjectDict["Geometry"]= geom_str
            self.SO_Geometry.DataStore = geom_str
            self.SO_Geometry.Enabled = True
            STG.select_Objects.Enabled = False
            STG.remove_Objects.Enabled = False
            
        else:
            self.SO_Geometry.Enabled = True
            self.SONameBox.Enabled = True
            self.SOTypeBox.Enabled = True
            STG.select_Objects.Enabled = True
            self.SOfromSODropDown.Enabled = True
            self.SORelationBox.Enabled = True
            self.SOfromSODropDown.Visible = True
            self.SORelationBox.Visible = True
            self.SORelationship.Visible = True
            self.SOfromSOLabel.Visible = True
            
    #when the selected index from the SOfromSODropDown changes, this is saved to the Subobject information
    def SaveSOfromSO(self, sender, e):
        Layer = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        for ObjectDict in STG.InformationList:
            if ObjectDict["Identifier"]==rs.LayerId(Layer):
                if "Aggregates" in ObjectDict:
                    for SODict in ObjectDict["Aggregates"]:
                        if SODict["Name"] == self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex]:
                            SODict["SOfromSO"] = self.SOfromSODropDown.DataStore[self.SOfromSODropDown.SelectedIndex]
    
    #when the selected index from the SubObject list changes, all subobject widgets need to be refreshed to correspond to the attributes of the newly selected subobject
    def SaveSOProps(self,sender,e):
        self.SO_Geometry.Enabled = True
        Layer = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        SOName = self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex]

        SOType = self.SOTypeBox.DataStore[self.SOTypeBox.SelectedIndex]
        self.SONameBox.Text = str(SOName)      
        for ObjectDict in STG.InformationList:
            if ObjectDict["Identifier"]==rs.LayerId(Layer):
                if "Aggregates" in ObjectDict:
                    for SODict in ObjectDict["Aggregates"]:
                        if SODict["Name"] == self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex]:
                            self.SONameBox.Text = SODict["Name"]
                            if "Type" in SODict:
                                self.SOTypeBox.SelectedIndex = self.SOTypeBox.DataStore.index(SODict["Type"])
                            try:
                                if "Geometry" in SODict:
                                    DisplayList = []
                                    for aggregate in SODict["Geometry"]:
                                        DisplayList.append(aggregate)
                                        if aggregate in STG.AssumptionDict:
                                            List = []
                                            for item in STG.AssumptionDict[aggregate]:
                                                List.append(item)
                                            self.AssumptionList.DataStore = List
                                            self.removeAssumptionButton.Enabled = True
                                    self.SO_Geometry.DataStore = DisplayList
                                else:
                                    self.SO_Geometry.DataStore = []
                            except: print "error setting geometry"
                            try:
                                if "Relationship" in SODict:
                                    index = self.RelationshipStore.index(SODict["Relationship"])
                                    self.SORelationBox.SelectedIndex = index
                                else:
                                    self.SORelationBox.SelectedIndex = 0
                                    
                                if "SOfromSO" in SODict:
                                    PreventChanging = SODict["SOfromSO"]
                                    STG.setSOfromSODataStore(self, 0,0)
                                    SODict["SOfromSO"]=PreventChanging
                                    index = self.SOfromSODropDown.DataStore.index(SODict["SOfromSO"])
                                    self.SOfromSODropDown.SelectedIndex = index
                                    SODict["SOfromSO"] = PreventChanging
                                else:
                                    self.SOfromSODropDown.SelectedIndex = 0
                            except: print "error setting 'subobject from subobject'"
        try:
            if len(self.SO_Geometry.DataStore)>0:
                STG.createAssumption.Enabled = True
                STG.OcclusionButton.Enabled = True
                STG.remove_Objects.Enabled = True
                self.AssumptionList.DataStore = []
            else:
                STG.createAssumption.Enabled = False
                STG.OcclusionButton.Enabled = False
                self.AssumptionList.DataStore = []
                STG.remove_Objects.Enabled = False
            
            #blocking adaptations for "self"
            if self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex] == "self":
                self.SONameBox.Enabled = False
                self.SOTypeBox.SelectedIndex = self.DropDown_type.SelectedIndex
                self.SOTypeBox.Enabled = False
                self.SOfromSODropDown.Enabled = False
                self.SORelationBox.Enabled = False
                geom_str = []
                for geom in rs.ObjectsByLayer(Layer):
                    if rs.ObjectType(geom) != 2:
                        geom_str.append(str(geom))                
                ObjectDict["Geometry"]= geom_str
                self.SO_Geometry.DataStore = geom_str
                self.SO_Geometry.Enabled = True
                STG.select_Objects.Enabled = False
                self.SOfromSODropDown.Visible = False
                self.SORelationBox.Visible = False
                self.SORelationship.Visible = False
                self.SOfromSOLabel.Visible = False
                STG.remove_Objects.Enabled = False
                
            else:
                self.SO_Geometry.Enabled = True
                self.SONameBox.Enabled = True
                self.SOTypeBox.Enabled = True
                self.SOfromSODropDown.Enabled = True
                STG.select_Objects.Enabled = True
                self.SORelationBox.Enabled = True
                self.SOfromSODropDown.Visible = True
                self.SORelationBox.Visible = True
                self.SORelationship.Visible = True
                self.SOfromSOLabel.Visible = True
        except: print 'enabling/disabling buttons failed'
            
    #when the SubObject textbox looses focus, the list needs to be refreshed in case of namechanges
    def refreshSOList(self,sender,e):
        Layer = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        for ObjectDict in STG.InformationList:
            if ObjectDict["Identifier"]==rs.LayerId(Layer):
                if "Aggregates" in ObjectDict:
                    for SODict in ObjectDict["Aggregates"]:
                        if "SOfromSO" in SODict:
                            if SODict["SOfromSO"] == self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex]:
                                SODict["SOfromSO"] = self.SONameBox.Text
                        if SODict["Name"] == self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex]:
                            SODict["Name"] = self.SONameBox.Text
                
        STG.SOList[self.SubObjectListBox.SelectedIndex] = self.SONameBox.Text
        self.SubObjectListBox.DataStore = STG.SOList
        STG.setSOfromSODataStore(self, 0,0)
        
    #when the SubObject TypeBox changes item, this is saved to the Subobject information
    def SOTypeboxChanges(self,sender,e):
        Layer = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        for ObjectDict in STG.InformationList:
            if ObjectDict["Identifier"]==rs.LayerId(Layer):
                if "Aggregates" in ObjectDict:
                    for SODict in ObjectDict["Aggregates"]:
                        if SODict["Name"] == self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex]:
                            SODict["Type"] = self.SOTypeBox.DataStore[self.SOTypeBox.SelectedIndex]
    
    #when the SubObject-Object RelationShip (bot:hostsElement/product:aggregates) changes, this is saved to the Subobject information
    def SORelationChanges(self,sender,e):
        Layer = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        for ObjectDict in STG.InformationList:
            if ObjectDict["Identifier"]==rs.LayerId(Layer):
                if "Aggregates" in ObjectDict:
                    for SODict in ObjectDict["Aggregates"]:
                        if SODict["Name"] == self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex]:
                            SODict["Relationship"] = self.SORelationBox.DataStore[self.SORelationBox.SelectedIndex]

    #when the "construct new" button is pressed, a new subobject with a generic name 'undefined_aggregate' is constructed'
    def addAggregate(self,sender,e):
        unknown_aggregates = [0]
        for item in STG.SOList:
            if "undefined_aggregate_" in item:
                itemsplit = item.split('_')
                itemnumber = itemsplit[-1]
                unknown_aggregates.append(itemnumber)
        unknown_aggregates = sorted(unknown_aggregates)
        last = str(int(unknown_aggregates[-1])+1)
        newSO = str("undefined_aggregate"+'_'+str(last))
        STG.SOList.append(newSO)
        
        Object = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        for ObjectDict in STG.InformationList:
            if ObjectDict["Identifier"]==rs.LayerId(Object):
                newSODict = {}
                newSODict["Name"] = newSO
                newSODict["Type"] = STG.ProductTypes[0]
                newSODict["Relationship"] = self.RelationshipStore[0]
                
                if "Aggregates" in ObjectDict:
                    already_present = list(ObjectDict["Aggregates"])
                    already_present.append(newSODict)
                    ObjectDict["Aggregates"] = tuple(already_present)
                else:
                    ObjectDict["Aggregates"] = (newSODict,)
        self.SubObjectListBox.DataStore = STG.SOList
        
        #buttons are only enabled if they can work, to avoid a program crash
        if len(self.SO_Geometry.DataStore)>0:
            STG.createAssumption.Enabled = True
            STG.OcclusionButton.Enabled = True
            STG.remove_Objects.Enabled = True
        else:
            STG.remove_Objects.Enabled = False
        
        #you cannot change the name, type, relationship or 'subobject-from-subobject' from the 'self' object => this needs to be done at main object level
        if self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex] == "self":
            self.SONameBox.Enabled = False
            self.SOTypeBox.SelectedIndex = self.DropDown_type.SelectedIndex
            self.SOTypeBox.Enabled = False
            self.SOfromSODropDown.Enabled = False
            self.SORelationBox.Enabled = False
            self.SO_Geometry.Enabled = True
            STG.select_Objects.Enabled = False
            self.SOfromSODropDown.Visible = False
            self.SORelationBox.Visible = False
            self.SORelationship.Visible = False
            self.SOfromSOLabel.Visible = False
            STG.remove_Objects.Enabled = False
            
        else:
            self.SO_Geometry.Enabled = True
            self.SONameBox.Enabled = True
            self.SOTypeBox.Enabled = True
            self.SOfromSODropDown.Enabled = True
            STG.select_Objects.Enabled = True
            self.SORelationBox.Enabled = True
            self.SOfromSODropDown.Visible = True
            self.SORelationBox.Visible = True
            self.SORelationship.Visible = True
            self.SOfromSOLabel.Visible = True
        
    #when the "delete" button is pressed, the aggregate is removed from the file
    def DeleteAggregate(self, sender, e):
        Layer = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        for ObjectDict in STG.InformationList:
            if ObjectDict["Identifier"]==rs.LayerId(Layer):
                if "Aggregates" in ObjectDict:
                    for SODict in ObjectDict["Aggregates"]:
                        if SODict["Name"] == self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex]:
                            if self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex] != "self":
                                if "Aggregates" in ObjectDict:
                                    already_present = list(ObjectDict["Aggregates"])
                                    already_present.remove(SODict)
                                    ObjectDict["Aggregates"] = tuple(already_present)
        
        if self.SubObjectListBox.DataStore[self.SubObjectListBox.SelectedIndex] != "self":
            del STG.SOList[self.SubObjectListBox.SelectedIndex]
            self.SubObjectListBox.DataStore = STG.SOList
        else: print "'self' cannot be deleted"
                        
    #when the Object DropDown opens, the list with layers should be refreshed and the SubObject aggregates saved to the basic dictionary
    def renewList(self,sender,e):
        NewLayers = rs.LayerNames(sort = True)
        NewLayers.remove("Default")
        NewLayerIds = rs.LayerIds()
        NewLayerIds_str = []
        for fullid in NewLayerIds: 
            NewLayerIds_str.append(str(fullid))
        STG.ObjectDropDown.DataStore = NewLayers
        Layer = STG.ObjectDropDown.DataStore[STG.ObjectDropDown.SelectedIndex]
        for ObjectDict in STG.InformationList:
            if ObjectDict["Identifier"] not in NewLayerIds_str:
                STG.InformationList.remove(ObjectDict)
            if ObjectDict["Identifier"]==rs.LayerId(Layer):
                if ObjectDict["Name"] != Layer:
                    ObjectDict["Name"] = Layer

#main class for the Point Cloud import Tab
class ImportPointCloud(forms.Panel):
    #main layout
    def __init__(self):
        self.folderLayout = forms.DynamicLayout()
        self.folder_label = forms.Label(Text = "Locate folder with .e57-files")
        self.folder_textbox = forms.TextBox(Width = 360, Text = None)
        self.folderButton = forms.Button(Width = 20, Text = "...")
        self.folderButton.Click += self.OnFolderButtonClick
        self.folderLayout.AddRow(None,self.folder_label,None,None)
        self.folderLayout.AddRow(None,self.folder_textbox, self.folderButton,None)
        
        self.InfoLabel = forms.Label(Text = "Octree Subdivision")
        
        global SampleOptions
        SampleOptions = ["OCTREE","SPATIAL","RANDOM"]
        self.SampleOption_Dropdown = forms.DropDown(DataStore = SampleOptions, SelectedIndex = 0)
        self.SampleOption_Dropdown.SelectedValueChanged += self.SetNumericOptions
        self.Numeric_updown = forms.NumericUpDown(DecimalPlaces = 0, Increment = 1, MaxValue = 21, MinValue = 1, Value = 10)
        self.Execute_Button = forms.Button(Text = "Execute", Enabled = False)
        self.Execute_Button.Click += self.subsampler
        
        
        self.OptionGroupBox=forms.GroupBox(Text = "SubSampling Options",Visible = False)
        self.OptionGroupBox.Padding = drawing.Padding(10)
        
        self.OptionLayout = forms.DynamicLayout()        
        self.OptionLayout.Spacing = drawing.Size(5,5)
        self.OptionLayout.BeginVertical()
        self.OptionLayout.AddRow(self.SampleOption_Dropdown, None, self.Numeric_updown, None, self.InfoLabel)
        self.OptionLayout.AddRow("")
        self.OptionLayout.EndVertical()
        self.OptionGroupBox.Content = self.OptionLayout
        
        self.EnableSubSampling = forms.CheckBox(Text = "Enable Subsampling", Checked = False)
        self.EnableSubSampling.CheckedChanged += self.enableSubSampling
        
        #layout that groups different layouts together in the window
        self.finalLayout = forms.DynamicLayout()
        self.finalLayout.Spacing = drawing.Size(15,15)
        self.finalLayout.BeginVertical()
        self.finalLayout.AddRow(' ')
        self.finalLayout.AddRow(self.folderLayout)
        self.finalLayout.AddRow(self.EnableSubSampling)
        self.finalLayout.AddRow(self.OptionGroupBox)
        self.finalLayout.EndVertical()
        self.finalLayout.BeginVertical()
        self.finalLayout.AddRow(None,None,None,self.Execute_Button)
        self.finalLayout.AddRow("")
        self.finalLayout.EndVertical()
        self.finalLayout.Padding = drawing.Padding(10)
        self.Content = self.finalLayout
    
    #when the subsampling checkbox is checked/unchecked, the subsampling options are made visible/invisible
    def enableSubSampling(self,sender,e):
        if self.EnableSubSampling.Checked == False:
            self.OptionGroupBox.Visible = False
        else:
            self.OptionGroupBox.Visible = True
    
    #the numeric options for the subsampling process depend on the method used
    def SetNumericOptions(self, sender, e):
        #OCTREE
        if self.SampleOption_Dropdown.SelectedIndex == 0:
            
            self.Numeric_updown.DecimalPlaces = 0
            self.Numeric_updown.Increment = 1
            self.Numeric_updown.MaxValue = 21
            self.Numeric_updown.MinValue = 1
            self.Numeric_updown.Value = 10
            self.InfoLabel.Text = "(Octree Subdivision)"
         
        #SPATIAL
        if self.SampleOption_Dropdown.SelectedIndex == 1:
            
            self.Numeric_updown.DecimalPlaces = 3
            self.Numeric_updown.Increment = 0.01
            self.Numeric_updown.MaxValue = 1
            self.Numeric_updown.MinValue = 0
            self.Numeric_updown.Value = 0.05
            self.InfoLabel.Text = "(step in m)"
            
        #RANDOM
        if self.SampleOption_Dropdown.SelectedIndex == 2:
            
            self.Numeric_updown.DecimalPlaces = 0
            self.Numeric_updown.Increment = 50000
            self.Numeric_updown.MaxValue = 2000000
            self.Numeric_updown.MinValue = 1
            self.Numeric_updown.Value = 200000
            self.InfoLabel.Text = "(Remaining points)"
    
    #select the FOLDER where the point clouds (.e57) are located
    def OnFolderButtonClick(self, sender, e):
        Folder  = forms.SelectFolderDialog()
        if Folder.ShowDialog(None) == forms.DialogResult.Cancel:
            return
        if Folder:
            self.folder_textbox.Text = Folder.Directory
        if os.path.isdir(self.folder_textbox.Text) == True:
            self.Execute_Button.Enabled = True
    
    #Subsampling process. Make sure that the folder contains no other folders and files, only the pointclouds that need to be subsampled should be present
    #otherwise, not all point clouds may be subsampled/imported (a future version may fix this)
    #the subsampling is outsourced to CloudCompare Stereo, which needs to be located at the default folder of C:\Program Files\CloudCompareStereo\CloudCompare.exe
    #or the folder needs to be changed below in the code
    def subsampler(self,sender,e):
        
        path = self.folder_textbox.Text
        option = SampleOptions[self.SampleOption_Dropdown.SelectedIndex]
        optionvalue = self.Numeric_updown.Value
        if self.SampleOption_Dropdown.SelectedIndex ==0:
            optionvalue = int(self.Numeric_updown.Value)
        
        files = listdir(path)
        
        files_in_folder = []
        files_extended = []
        for file in files:
            fullpath = str(path+r"\\"+file)
            #fullpath_raw = fullpath.encode('string-escape')
            if fnmatch.fnmatch(file, '*.e57'):
                files_in_folder.append(fullpath)
                
        if self.EnableSubSampling.Checked == True:
            for file in files_in_folder:
                cloudcompare_command = str(r'-C_EXPORT_FMT E57 -O' + ' ' + '"' + file + '"' + ' ' + r"-SS" + " " + option + " " + str(int(optionvalue)))
                
                passedstring = str('"' + cloudcompare_path + '"' + ' ' + cloudcompare_command)
                print passedstring
                command = subprocess.Popen(passedstring)
                files_extended = listdir(path)
            
            #timeout = time.time() + 3*len(files_in_folder)
            while (len(files_extended) < 2*len(files_in_folder)+1):
                files_extended = listdir(path)
                files_without_folders = []
                for file in files_extended:
                    if fnmatch.fnmatch(file, '*.e57'):
                        files_without_folders.append(fullpath)
                files_extended = files_without_folders
                files_extended.append("dummy")
                #if time.time() > timeout: break
                
            
            files_extended = listdir(path)
            
            newfolder = str(path + r'\\'+ "subsampled"+"_"+strftime("%Y-%m-%d_%Hh%M", gmtime()))
            if os.path.isdir(newfolder) == False:
                os.mkdir(newfolder)
            else: pass
            
            finalfolders = []
            for file in files_extended:
                if file not in files:
                    try:
                        shutil.move(str(path + r"\\" + file), str(newfolder + r"\\" + file))
                    except:
                        sleep(4)
                        shutil.move(str(path + r"\\" + file), str(newfolder + r"\\" + file))
                    finaldir = str(newfolder + r"\\" + file)
                    finalfolders.append((finaldir,file))
             
            for finaldir,file in finalfolders:
                FileName = finaldir
                file = str(file)
                LayerName_list = file.split("_")
                LayerName = ''
                for part in LayerName_list[:2]:
                        LayerName += part
                        LayerName +='_'
                LayerName = LayerName[:-1]
                command = ('! _Import '+'"'+FileName+'"'+' SelLast Move 0 @-'+Project_Info.Xcoord.Text+',-'+Project_Info.Ycoord.Text+' SelLast _-ChangeLayer n ' + LayerName + ' -Layer f ' + LayerName + ' _Enter')
                rs.Command(command)
                
        else:
            for filepath in files_in_folder:
                FileName = filepath
                print FileName
                LayerName_list = FileName.split(r"\\")
                LayerName_ext = LayerName_list[-1]
                LayerName_ext = LayerName_ext.split(".")
                LayerName = LayerName_ext[0]
                #command = ('! _Import '+'"'+FileName+'"'+' SelLast Move 0 @-104500,-194300 SelLast _-ChangeLayer n ' + LayerName + ' -Layer f ' + LayerName + ' _Enter')
                command = ('! _Import '+'"'+FileName+'"'+' SelLast Move 0 @-'+Project_Info.Xcoord.Text+',-'+Project_Info.Ycoord.Text+' SelLast _-ChangeLayer n ' + LayerName + ' -Layer f ' + LayerName + ' _Enter')
                rs.Command(command)

#main class for the SPARQL query tab
class SPARQL(forms.Panel):
    def __init__(self):
        self.stardogLabel = forms.Label(Text = "Name of the stardog database corresponding with this file: ")
        SPARQL.stardogGraph = forms.TextBox(Text = "")
        
        SPARQL.QueryField = forms.TextArea(Text = "SELECT ?ID ?s WHERE {?s stg:hasRhinoID ?ID}", Height = 250)
        
        self.QueryLabel = forms.Label(Text = "SPARQL SELECT Query")
        self.StardogWarning = forms.Label(Text = "(Make sure a Stardog Server is Running!)")
        self.ReasoningButton = forms.CheckBox(Text = "Enable Reasoning",Checked = True)
        SPARQL.QueryButton = forms.Button(Text = "Query")
        SPARQL.QueryButton.Click +=self.Query
        
        self.ClearButton = forms.Button(Text = 'Clear display')
        self.ClearButton.Click += self.ClearObjectDisplayModes
        
        self.resultLabel = forms.Label(Text = "Query results")
        SPARQL.results = forms.GridView()
        SPARQL.results.Height = 250
        SPARQL.results.SelectedRowsChanged += self.SelectObject
        
        # create the main tablayout
        qTabLayout = forms.DynamicLayout()
        qTabLayout.DefaultSpacing = drawing.Size(5, 5)
        qTabLayout.Padding = drawing.Padding(10)
        qTabLayout.BeginVertical()
        qTabLayout.AddRow(self.stardogLabel,SPARQL.stardogGraph)
        qTabLayout.EndVertical()
        qTabLayout.BeginVertical()
        qTabLayout.AddRow(self.QueryLabel)
        qTabLayout.AddRow(SPARQL.QueryField)
        qTabLayout.EndVertical()
        qTabLayout.BeginVertical()
        qTabLayout.AddRow(self.StardogWarning, None, SPARQL.QueryButton, self.ReasoningButton)
        qTabLayout.AddRow(" ")
        qTabLayout.EndVertical()
        qTabLayout.BeginVertical()
        qTabLayout.AddRow(self.resultLabel)
        qTabLayout.AddRow(SPARQL.results)
        qTabLayout.EndVertical()
        qTabLayout.BeginVertical()
        qTabLayout.AddRow(" ")
        qTabLayout.AddRow(None,None,None,self.ClearButton)
        qTabLayout.EndVertical()
        qTabLayout.AddRow(" ")
        self.Content = qTabLayout
        
    #selects possible geometrical results from a SPARQL query in the viewer
    def SelectObject(self,sender,e):
        Rhino.RhinoApp.RunScript("_SelNone", False)
        row = SPARQL.results.DataStore[SPARQL.results.SelectedRow]
        AllObjects = rs.AllObjects()
        AllObjects_str = []
        for item in AllObjects:
            AllObjects_str.append(str(item))
        for item in row:
            if item in AllObjects_str:
                rs.SelectObject(item)
        
    #brings the display back to default mode - if elements were set to 'rendered' because of the SPARQL query
    def ClearObjectDisplayModes(self,sender,e):
        CMD = str('_ClearAllObjectDisplayModes a')
        rs.Command(CMD,True)
        
    #grid that adapts to the amount of variables from the SPARQL query
    global SPARQLgrid
    def SPARQLgrid(n,URIdict):
        try:
            for pr,uri in URIdict.iteritems():
                for row in n:
                    rowindex = n.index(row)
                    for item in row:
                        itemindex = row.index(item)
                        if uri in item:
                            item = item.replace(str(uri),"")
                            prefixed = str(pr+":"+item)
                            n[rowindex][itemindex]= prefixed
        except: print 'could not replace all namespaces correctly'
                            
        try:
            Vars = n[0]
            SPARQL.results.Columns.Clear()
            for var in Vars:
                index = Vars.index(var)
                column = forms.GridColumn(AutoSize = True)
                column.HeaderText = var
                column.DataCell = forms.TextBoxCell(index)
                SPARQL.results.Columns.Add(column)
        except: print 'error'
        try:
            for row in n:
                rowindex = n.index(row)
                newrow = []
                for item in row:
                    newrow.append(item)
                if len(row)<len(Vars):
                    diff = len(Vars)-len(row)
                    for i in range(diff):
                        newrow.append(' ')
                n[rowindex] = newrow
                
            SPARQL.results.DataStore = tuple(n[1:])
        except: print 'error'
        
        Objects_query = []
        AllObjects = rs.AllObjects()
        AllObjects_str = []
        for item in AllObjects:
            AllObjects_str.append(str(item))
        try:
            for row in SPARQL.results.DataStore:
                for item in row:
                    if item in AllObjects_str:
                        Objects_query.append(item)
        except: print 'error'
        if len(Objects_query)>=1:
            rs.ViewDisplayMode(mode='Wireframe')
            CMD = str('_ClearAllObjectDisplayModes a')
            rs.Command(CMD,True)
            
            rs.SelectObjects(Objects_query)
            ObjectDM = str("_SetObjectDisplayMode m r")
            rs.Command(ObjectDM,True)
        
    #queries the graph with stardog => a Stardog Database with the corresponding graph should be running
    def Query(self, sender, e):
        query = repr(SPARQL.QueryField.Text).replace(r'\r\n','')
        query_upper = query.upper()
        split_query_to_retrieve_variables=query_upper.split('WHERE')
        firstPartOfQuery=split_query_to_retrieve_variables[0].split(' ')
        SPARQLvariables=[]
        for item in firstPartOfQuery:
            if len(item)>0:
                if item[0]=='?':
                    item=item[1:]
                    SPARQLvariables.append(item)
        reasoning = '--reasoning '
        if self.ReasoningButton.Checked == False:
            reasoning = ' '
        CMDcommand = str("stardog.bat query "+reasoning+str(SPARQL.stardogGraph.Text)+' "'+query+'" -f CSV')
        SeparateList = []
        URIdict = {}
        try:
            p=subprocess.check_output(CMDcommand)
            n = p.splitlines()
            for item in n:
                item = item.split(',')
                SeparateList.append(item)
                
            CMD_get_namespaces = str("stardog.bat namespace export "+str(SPARQL.stardogGraph.Text))
        
            prefix=subprocess.check_output(CMD_get_namespaces)
            prefix=prefix.splitlines()
            for item in prefix:
                if 'stardog' in item:
                    pass
                else:
                    item=item.split("<")
                    URI=item[-1].split(">")
                    URI=URI[0]
                    pr = item[0].split(":")
                    pr = pr[0].split(" ")
                    pr = pr[-1]
            
                    URIdict[pr]=URI
        except: print 'an error occured, please check Query and Stardog configurations (if necessary, perform query in Stardog Web Console or the command line)'
        SPARQLgrid(SeparateList,URIdict)
        
        
        
        
#the overall layout of the plugin, which groups the tabs
class WidgetLayout(forms.Form):
    def __init__(self):
        self.Title = 'GeometryGraph'
        self.Padding = drawing.Padding(5)
        self.Resizable = True
        self.Maximizable = False
        self.Minimizable = False
        self.ShowInTaskbar = False
        widget_width = 640
        widget_height = 960
        self.MinimumSize = drawing.Size(widget_width, widget_height)
        
        #layout for specifying the location of the Graph
        self.folderLayout = forms.DynamicLayout()
        self.graph_label = forms.Label(Text = "   Project Name (C-disk):   ")
        self.graph_textbox = forms.TextBox(Width = 350, Text = None)
        
        self.URI_label = forms.Label(Text = "   Global URI:   ")
        self.URI_textbox = forms.TextBox(Width = 350, Text = None)
        
        self.folderButton = forms.Button(Text = "...")
        self.folderButton.Click += self.OnFolderButtonClick
        
        self.SerializeButton = forms.Button(Text = "Serialize",Enabled = False, Width = 120)
        self.SerializeButton.Click += self.Serialize
        self.SaveDictButton = forms.Button(Text = "Save as TXT",Enabled = False, Width = 120)
        self.SaveDictButton.Click += self.SaveDict
        
        self.folderLayout.AddRow(" ")
        self.folderLayout.AddRow(self.graph_label,self.graph_textbox, self.folderButton,"    ")
        self.folderLayout.AddRow(self.URI_label,self.URI_textbox, self.SerializeButton,"    ")
        self.folderLayout.AddRow(" "," ", self.SaveDictButton,"    ")
        
        #layout for tabs
        self.TabControl = self.MainTabs()
        tab_items = forms.StackLayoutItem(self.TabControl, True)
        self.tabLayout = forms.StackLayout()
        self.tabLayout.Spacing = 5
        self.tabLayout.HorizontalContentAlignment = forms.HorizontalAlignment.Stretch
        self.tabLayout.Items.Add(tab_items)
        
        #layout that groups different layouts together in the window
        self.finalLayout = forms.DynamicLayout()
        self.finalLayout.Spacing = drawing.Size(15,15)
        self.finalLayout.BeginVertical()
        self.finalLayout.AddRow(self.folderLayout)
        self.finalLayout.EndVertical()
        self.finalLayout.BeginVertical()
        self.finalLayout.AddRow(self.tabLayout)
        self.finalLayout.EndVertical()
        self.Content = self.finalLayout
        
        # FormClosed event handler
        self.Closed += self.OnFormClosed
    
    #an internal save of the plugin's dictionaries
    #all information is saved to a .txt file and can be retrieved directly when opening this file later
    def SaveDict(self,sender,e):
        GlobalURI = self.URI_textbox.Text
        FileName = self.graph_textbox.Text
        FileName = FileName.split(".")
        FileName = FileName[0]
        AllInfo = str(str(FileName)+'\n'+str(Project_Info.ProjectInfo)+'\n'+str(Project_Info.TopoDict)+'\n'+str(STG.InformationList)+'\n'+str(STG.AssumptionDict)+'\n'+str(GlobalURI))
        TXTfile = str(FileName+".txt")
        try:
            with open(TXTfile, 'w') as text_save:
                text_save.write(AllInfo)
            print 'save successful'
        except: 'save failed - please check input'
    
    #when the serialize button is pressed, the RDF graph is created by an external Python 2.7 script (IronPython does not fully support rdflib, the module that is used for this proces)
    #if the export STEP checkbox at the Project Info tab is checked, the graph will include STEP geometry
    def Serialize(self, sender, e):
        OpenDialog = self.graph_textbox.Text
        GlobalURI = self.URI_textbox.Text
        for Object in STG.InformationList:
            IDsInObject = rs.ObjectsByLayer(Object["Name"])
        pythonfile = str(ProjectFolder + r'\\' + "Dict-to-Graph.py")
        if Project_Info.ExportSTP.Checked == True:
            ext = OpenDialog.split('.')
            filePath = ext[0]
            filePath += str(r"\\GEOM\\")
            if not os.path.exists(filePath):
                os.makedirs(filePath)
            settingsList = {'GetSTPSettings': GetSTPSettings}
            initExport(filePath, settingsList,"stp")
        try:
            OpenDialog = OpenDialog.split('.')
            OpenDialog = OpenDialog[0]
            OpenDialog += ".ttl"
            
            arg1 = repr(OpenDialog)
        except: print "Please check Project Folder"
        try:
            arg2 = str(Project_Info.ProjectInfo)
        except: print "Please check Project Info"
        try:
            arg3 = str(Project_Info.TopoDict)
        except: print "Please check Project Topology"
        try:
            arg4 = str(STG.InformationList)
        except: print "Please check if there are objects (layers)"
        try:
            arg5 = str(STG.AssumptionDict)
        except: print 'Assumption error'
        try:
            arg6 = GlobalURI
        except: print "Please enter global URI"
        try:
            arg7 = rs.DocumentName()
        except: print "Rhinodocument needs to have a name"
        try:
            passedstring=str('"'+pythonversion+'" "'+pythonfile+'" "'+arg1+'" "'+arg2+'" "'+arg3+'" "'+arg4+'" "'+arg5+'" "'+arg6+'" "'+arg7+'"')
            print passedstring
            g=subprocess.check_output(passedstring)
        except: print 'serializing error'
    
    #this button states either the name of a new graph, in the selected folder, or loads an existing graph made by the plugin. TXT files (SaveDict function) can also be read.
    #note that, when the name is not changed after loading the graph, the graph will be overwritten
    #check the correct extension: when a .txt file is loaded, the extension needs to be changed to .ttl in order to be serialized to a Turtle file
    def OnFolderButtonClick(self, sender, e):
        New_ID_Dict = {}
        global OpenDialog
        OpenDialog  = rs.OpenFileName("Choose graph", "Turtle files or TXT-dictionaries (*.ttl; *.txt)|*.ttl;*.txt||")
        if OpenDialog:
            self.graph_textbox.Text = OpenDialog
            if os.path.exists(OpenDialog):
                SPARQL.QueryButton.Enabled = True
                pythonfile = pythonfile = str(ProjectFolder + r'\\' + "load_graph.py")
                STEPpythonfile = str(ProjectFolder + r'\\' + "STEPreconstruct.py")
                passedstring = str(pythonversion + ' "' + pythonfile + '" "' + OpenDialog+'"')
                STEPstring = str(pythonversion + ' "' + STEPpythonfile + '" "' + OpenDialog + '"')
                extension = OpenDialog.split(".")
                extension = extension[-1]
                if extension == "ttl":
                    try:
                        loadDicts = subprocess.check_output(passedstring)
                        loadDicts = ast.literal_eval(loadDicts)
                        Project_Info.ProjectInfo = loadDicts[0]
                        Project_Info.TopoDict = loadDicts[1]
                        STG.InformationList = loadDicts[2]
                        STG.AssumptionDict = loadDicts[3]
                    except: print "subprocess failed"
                    
                elif extension == "txt":
                    try:
                        with open(OpenDialog, 'r') as text_read:
                            content = text_read.readlines()
                            content = [x.strip() for x in content]
                            Project_Info.ProjectInfo = ast.literal_eval(content[1])
                            Project_Info.TopoDict = ast.literal_eval(content[2])
                            STG.InformationList = ast.literal_eval(content[3])
                            STG.AssumptionDict = ast.literal_eval(content[4])
                            try:
                                Global_URI = str(content[5])
                            except:
                                pass
                    except: print ".txt file could not be read"
                        
                NewLayers = rs.LayerNames(sort = True)
                NewLayers.remove("Default")
                STG.ObjectDropDown.DataStore = NewLayers
                
                try:
                    Project_Info.TextBox_SiteName.Text = str(Project_Info.ProjectInfo["SiteName"])
                    Project_Info.TextBox_BuildingName.Text = str(Project_Info.ProjectInfo["BuildingName"])
                    Project_Info.CoordinateSystem.Text = str(Project_Info.ProjectInfo["coordinateSystem"])
                    Project_Info.Xcoord.Text = Project_Info.ProjectInfo["coordinates"][0]
                    Project_Info.Ycoord.Text = Project_Info.ProjectInfo["coordinates"][1]
                    Project_Info.Zcoord.Text = Project_Info.ProjectInfo["coordinates"][2]
                except: print "Error while setting Project Info"
                try:
                    Project_Info.Storeys = []
                    for storey,spaces in Project_Info.TopoDict.iteritems():
                        Project_Info.Storeys.append(storey)
                    Project_Info.StoreyBox.DataStore = Project_Info.Storeys
                    storey = Project_Info.StoreyBox.DataStore[Project_Info.StoreyBox.SelectedIndex]
                    Project_Info.SpaceBox.DataStore = Project_Info.TopoDict[storey]
                except: print "Error while setting storeys and spaces"
            StardogSuggestion = repr(OpenDialog)
            StardogSuggestion = StardogSuggestion.split(r"\\")
            StardogSuggestion = StardogSuggestion[-1]
            StardogSuggestion = StardogSuggestion.split(".")
            StardogSuggestion = StardogSuggestion[0]
            SPARQL.stardogGraph.Text = StardogSuggestion
            self.SerializeButton.Enabled = True
            self.SaveDictButton.Enabled = True
            try:
                for ObjectDict in STG.InformationList:
                    ObjectDict["Identifier"] = rs.LayerId(ObjectDict["Name"])
            except: print "imported objects could not be matched to a layer, make sure you have a correct .3dm file opened"
            
            AllObjects = rs.AllObjects()
            if Project_Info.ImportSTP.Checked == True:
                if len(AllObjects) == 0 and extension == "ttl":
                    try:
                        STEP = subprocess.check_output(STEPstring)
                        STEP = ast.literal_eval(STEP)
                    except: print 'subprocess failed'
                    try:
                        for file in STEP:
                            CMD = str('_import "'+file+'"')
                            rs.Command(CMD)
                            old_id = file.split(r"\\")
                            old_id = old_id[-1].split(".")
                            old_id = old_id[0]
                            
                            new_id = rs.LastCreatedObjects()
                            if len(new_id)>1:
                                IDs = []
                                for item in new_id:
                                    IDs.append(item)
                                cmd2 = "_join "
                                for item in IDs:
                                    cmd2 += str(item)
                                    cmd2 += " "
                                rs.Command(cmd2)
                                new_id = rs.LastCreatedObjects()
                            new_id = new_id[0]
                            if old_id not in New_ID_Dict:
                                New_ID_Dict[old_id] = [str(new_id)]
                            else:
                                New_ID_Dict[old_id].append(str(new_id))
                        for ObjectDict in STG.InformationList:
                            if "Geometry" in ObjectDict:
                                for geom in ObjectDict["Geometry"]:
                                    for old, new in New_ID_Dict.iteritems():
                                        if geom == old:
                                            geom = new
                            if "Aggregates" in ObjectDict:
                                for SODict in ObjectDict["Aggregates"]:
                                    if "Geometry" in SODict:
                                        for geom in SODict["Geometry"]:
                                            for old, new in New_ID_Dict.iteritems():
                                                if geom == old:
                                                    geom = new
                                                    
                        NewLayers = rs.LayerNames(sort = True)
                        NewLayers.remove("Default")
                        STG.ObjectDropDown.DataStore = NewLayers
                    except: print 'fail'
                
            
    #exporting function via mcneel/rhinoscriptsyntax
    #https://github.com/mcneel/rhinoscriptsyntax/blob/master/Scripts/rhinoscript/layer.py
    #Export settings for STP export
    global GetSTPSettings
    def GetSTPSettings():
        e_str = "_Schema=AP214AutomotiveDesign "
        e_str+= "_ExportParameterSpaceCurves=No "
        e_str+= "_SplitClosedSurfaces=No "
        e_str+= "_LetImportingApplicationSetColorForBlackObjects=Yes """
        e_str+= "_Enter _Enter"
        return e_str
    #only Polysurfaces and Surfaces are exported to STEP: curves, points and pointclouds, for example, are not included
    global initExport
    def initExport(filePath, settingsList,fileType="stp"):
        #filter out the invalid objects (such as point clouds)
        objs = rs.ObjectsByType(16)
        if len(objs) > 0:
            for obj in objs:
                saveObjectsToFile(str(obj), [obj], fileType, filePath, settingsList)
        objs_srf = rs.ObjectsByType(8)
        if len(objs_srf) > 0:
            for obj in objs_srf:
                saveObjectsToFile(str(obj), [obj], fileType, filePath, settingsList)
    global saveObjectsToFile
    def saveObjectsToFile(name, objs, fileType, filePath, settingsList):
        rs.EnableRedraw(False)
        if len(objs) > 0:
            settings = settingsList["Get"+fileType.upper()+"Settings"]()
            rs.UnselectAllObjects()
            for obj in objs:
                rs.SelectObject(obj)
            name = "".join(name.split(" "))
            command = '-_Export "{}{}{}" {}'.format(filePath, name, "."+fileType.lower(), settings)
            try:
                rs.Command(command, True)
            except: print command
            rs.EnableRedraw(True)
            
    # Create the tabs: Project Info, Semantic Enrichment tab, Point Cloud import tab and SPARQL query tab
    def MainTabs(self):
        # creates a tab control
        control = self.CreateTabControl()
        
        # create and add a tab for defining Project Info
        WidgetLayout.tab2 = forms.TabPage()
        WidgetLayout.tab2.Text = "Project Info"  
        WidgetLayout.tab2.Content = self.TabInfo()
        control.Pages.Add(WidgetLayout.tab2)
        # create and add the tab for Graph Construction
        WidgetLayout.tab3 = forms.TabPage()
        WidgetLayout.tab3.Enabled = True
        WidgetLayout.tab3.Text = "Semantics"  
        WidgetLayout.tab3.Content = self.TabSTG()
        control.Pages.Add(WidgetLayout.tab3)
        # create and add the tab for Point Cloud import
        WidgetLayout.tab4 = forms.TabPage()
        WidgetLayout.tab4.Text = "Point Clouds"  
        WidgetLayout.tab4.Content = self.TabPC()
        control.Pages.Add(WidgetLayout.tab4)
        # create and add the tab for SPARQL Querying
        tab1 = forms.TabPage()
        tab1.Text = "Query"
        tab1.Content = self.SPARQLtab()
        control.Pages.Add(tab1)
        return control

    # Creates the tab control
    def CreateTabControl(self):
        tab = forms.TabControl()
        # Orient the tabs at the top
        tab.TabPosition = forms.DockPosition.Top
        return tab

    # Link tab to SPARQL class
    def SPARQLtab(self):
        control = forms.Panel()
        control.Content = SPARQL()
        return control

    # Link tab to Project_Info class
    def TabInfo(self):
        control = forms.Panel()
        control.Content = Project_Info()
        return control
        
    # Link tab to STG class
    def TabSTG(self):
        control = forms.Panel()
        control.Content = STG()
        return control
    
    #link tab to ImportPointCloud class
    def TabPC(self):
        control = forms.Panel()
        control.Content = ImportPointCloud()
        return control
        
    # Form Closed event handler
    def OnFormClosed(self, sender, e):
        # Dispose of the form and remove it from the sticky dictionary
        if sc.sticky.has_key('sample_modeless_form'):
            form = sc.sticky['sample_modeless_form']
            if form:
                form.Dispose()
                form = None
            sc.sticky.Remove('sample_modeless_form')
    
def TestWidgetLayout():
    # See if the form is already visible
    if sc.sticky.has_key('sample_modeless_form'):
        return
    
    # Create and show form
    form = WidgetLayout()
    form.Owner = Rhino.UI.RhinoEtoApp.MainWindow
    form.Show()
    # Add the form to the sticky dictionary so it
    # survives when the main function ends.
    sc.sticky['sample_modeless_form'] = form
    
if __name__ == '__main__':
    TestWidgetLayout()