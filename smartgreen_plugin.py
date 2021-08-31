# -*- coding: utf-8 -*-

"""
/***************************************************************************
 SMARTGREEN
 A QGIS plugin to support water managers in the process
 of building and simulating different land uses scenarios and LIDs planning.
 -------------------
		begin				: 2017-04-21
		copyright			: (C) 2017 by UNIMI
		email				: enrico.chiaradia@unimi.it
 ***************************************************************************/

/***************************************************************************
 *																		 *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or	 *
 *   (at your option) any later version.								   *
 *																		 *
 ***************************************************************************/
"""

__author__ = 'UNIMI'
__date__ = '2017-04-21'
__copyright__ = '(C) 2017 by UNIMI'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import os.path as osp
from os.path import dirname, join, exists, abspath, isfile, basename,abspath
import sys
import inspect
from shutil import copyfile
import numpy as np
import glob
import operator


import processing
from PyQt5.QtWidgets import QToolBar, QAction, QMenu, QMessageBox, QFileDialog
from processing.core.Processing import Processing
from processing.tools.system import getTempFilename

from PyQt5.QtCore import *
from PyQt5.QtGui import *

from qgis.core import *
from qgis.gui import *

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
	sys.path.insert(0, cmd_folder)

from .maptools.smartgreen_maptool import SmartGreenMapTool
from .maptools.network_select_tool import NetworkSelectTool
from .maptools.raster_identify_tool import RasterIdentifyTool
from .maptools.vector_identify_tool import VectorIdentifyTool
from .maptools.plot_tool import PlotTool

from .tools.my_progress import MyProgress
from .tools.translate import tr
from .tools.smartgreen_settings import SmartGreenSettings
from .tools.select_by_location import selectByLocation
from .tools.buffer import buffering
from .tools.sqlite_driver import SQLiteDriver
from .tools.gis_grid import GisGrid
from .tools.rasterizer import Rasterizer
from .tools.interpolate import Interpolate
from .tools.hydrology import Hydrology
from .tools.drainage_geom_exporter import DrainageGeomExporter
from .tools.weather_exporter import WeatherExporter
from .tools.project_exporter import ProjectExporter
from .tools.lids_exporter import LidsExporter
from .tools.data_to_mat import dataToMat
from .tools.walk_in_selection import walkInSelection
from .tools.import_from_mat import ImportFromMat
from .tools.sm_dock import SMDock

global globalSettings

class SmartGreenPlugin:

	def __init__(self, iface):
		# Save reference to the QGIS interface
		self.iface = iface
		# refernce to map canvas
		self.canvas = self.iface.mapCanvas()
		# out click tool will emit a QgsPoint on every click
		self.clickTool = QgsMapToolEmitPoint(self.canvas)
		
		self.tr = tr
		
		# initialize plugin directory
		self.plugin_dir = os.path.dirname(__file__)
		# initialize locale
		locale = QSettings().value("locale/userLocale")[0:2]
		localePath = os.path.join(self.plugin_dir, 'i18n', 'smartgreen_ui_{}.qm'.format(locale))

		if os.path.exists(localePath):
			self.translator = QTranslator(QCoreApplication.instance())
			self.translator.load(localePath)

			if qVersion() > '4.3.3':
				QCoreApplication.installTranslator(self.translator)

		# Create an object that store settings and connect to project loading
		self.initSettings()
	
		self.iface.projectRead.connect(self.loadFromProject)
		self.iface.newProjectCreated.connect(self.initSettings)
		
		self.lastClickedPoint = None
		
		# load from project is exist
		proj = QgsProject.instance()
		if proj is not None:
			self.SGsettings.readFromProject(proj)

		# Add dockPanel
		self.smDock = None
		self.dockOpened = False
		self.initDockPanel()		
		
		self.DBM = None
		if self.settings['qgis.dblite'][0]!='':
			#print 'in __init__():',self.settings['qgis.dblite'][0]
			dbPath = self.settings['qgis.dblite'][0]
			#print "dbPath(prj):",dbPath
			# clear relative path
			wd = os.getcwd()
			os.chdir(self.getProjPath())
			dbPath = abspath(dbPath)
			#print "dbPath(abs):",dbPath
			os.chdir(wd)
			
			self.DBM = SQLiteDriver(dbPath,progress = self.smDock)
			
		#print 'DBM:',self.DBM
			
		globalSettings = self.settings
		
		self.clearConnection = True #manage connection segments
		
		
				
	def initSettings(self):
		#print 'init settings'
		self.SGsettings = SmartGreenSettings()
		self.settings = self.SGsettings.settings
		self.guiSettings = QSettings()
		

	def initGui(self):
		"""
		Create action that will start plugin configuration
		"""
		# add Main Menu
		self.mainMenu = self._addmenu(self.iface.mainWindow().menuBar(),'SMARTGREEN','&SMARTGREEN')

		# add Simulation Menu
		self.simMenu = self._addmenu(self.mainMenu,'Simulation',self.tr('Simulation'))
		self._addmenuitem(self.simMenu, 'NewSimulation', self.tr('New'), self.setNewSimulation)
		
		# add Build network Menu
		self.buildNetworkMenu = self._addmenu(self.simMenu,'BuildNetwork',self.tr('Network'))
		self._addmenuitem(self.buildNetworkMenu, 'ImportLinks', self.tr('Import links'), self.importLinks)
		self._addmenuitem(self.buildNetworkMenu, 'ImportNodes', self.tr('Import nodes'), self.importNodes)
		self.simMenu.addMenu(self.buildNetworkMenu)
		
		# add Check network Menu
		#self.checkdataMenu = self._addmenu(self.simMenu,'CheckData','Check network')
		self.checkdataMenu = self._addmenu(self.buildNetworkMenu,'CheckData',self.tr('Check network'))
		self.checkGeomMenu = self._addmenu(self.checkdataMenu,'Geometry',self.tr('Geometry'))
		self._addmenuitem(self.checkGeomMenu, 'FindDuplicates', self.tr('Find duplicates in geometry'), lambda: self.runAsThread(self.findDuplicates))
		self._addmenuitem(self.checkGeomMenu, 'CheckNodesNum', self.tr('Check nodes number'), lambda: self.runAsThread(self.checkNodesNumber))
		self.checkdataMenu.addMenu(self.checkGeomMenu)
		
		self.checkConnMenu = self._addmenu(self.checkdataMenu,'Connection',self.tr('Connection'))
		self._addmenuitem(self.checkConnMenu, 'CheckNodesLinksId', self.tr('Check nodes and links ids'), lambda: self.runAsThread(self.checkNodesId))
		self._addmenuitem(self.checkConnMenu, 'CheckLinkToNodes', self.tr('Check link-nodes correspondence'), lambda: self.runAsThread(self.checkLinkNodes))
		self._addmenuitem(self.checkConnMenu, 'CheckDetachedNodes', self.tr('Check detached nodes'), lambda: self.runAsThread(self.removeDetachedNode))
		self.checkdataMenu.addMenu(self.checkConnMenu)
		
		self.checkTopoMenu = self._addmenu(self.checkdataMenu,'Topography',self.tr('Topography'))
		self._addmenuitem(self.checkTopoMenu, 'fixLinkElev', self.tr('Fix link elevation'), lambda: self.runAsThread(self.fixLinkElev))
		#~ self._addmenuitem(self.checkTopoMenu, 'fixLinkElev', 'Fix link elevation', self.fixLinkElev)
		self._addmenuitem(self.checkTopoMenu, 'fixNodeBotElevations', self.tr('Fix lower elevation of node'), lambda: self.runAsThread(self.fixBotElevations))
		self.checkdataMenu.addMenu(self.checkTopoMenu)
		
		self.checkAttrMenu = self._addmenu(self.checkdataMenu,'Other attributes',self.tr('Other attributes'))
		self._addmenuitem(self.checkAttrMenu, 'fixAttributes', self.tr('Fix attributes'), lambda: self.runAsThread(self.fixAttributes))
		self._addmenuitem(self.checkAttrMenu, 'checkDim', self.tr('Check conduit dimensions'), lambda: self.runAsThread(self.checkDim))
		self._addmenuitem(self.checkAttrMenu, 'checkElevNode', self.tr('Check top elevation node'), lambda: self.runAsThread(self.checkTopElevNode))
		self.checkdataMenu.addMenu(self.checkAttrMenu)
		
		self._addmenuitem(self.checkdataMenu, 'fixAll', self.tr('Fix all network'),self.fixAll)
		
		#self.simMenu.addMenu(self.checkdataMenu)
		self.buildNetworkMenu.addMenu(self.checkdataMenu)
		
		# add Build Basin Menu
		self.buildBasinMenu = self._addmenu(self.simMenu,'BuildBasin',self.tr('Basin'))
		self._addmenuitem(self.buildBasinMenu, 'createSubCatchments', self.tr('Create subcatchments'), self.createSubCatchments)
		self._addmenuitem(self.buildBasinMenu, 'importLanduses', self.tr('Import landuses'), self.importLanduses)
		self._addmenuitem(self.buildBasinMenu, 'importSoils', self.tr('Import soils'), self.importSoils)
		self._addmenuitem(self.buildBasinMenu, 'importAcquifer', self.tr('Import Acquifer'), self.importAcquifer)
		self._addmenuitem(self.buildBasinMenu, 'checkBasinAttributes', self.tr('Check attributes'), lambda: self.runAsThread(self.fixBasinAttributes))
		
		self.simMenu.addMenu(self.buildBasinMenu)
		
		# add Build Basin Menu
		self.lidsMenu = self._addmenu(self.simMenu,'lids',self.tr('LIDs'))
		self._addmenuitem(self.lidsMenu, 'importLids', self.tr('Import LIDs'), self.importLids)
		self._addmenuitem(self.lidsMenu, 'setLidParams', self.tr('Set LID parameters (multiple)'), self.setLidsParams)
		self._addmenuitem(self.lidsMenu, 'setClosestNode', self.tr('Set closest node'), lambda: self.runAsThread(self.setClosestNode))
		self._addmenuitem(self.lidsMenu, 'checkLidAttribute', self.tr('Check LID attribute'), lambda: self.runAsThread(self.checkLidAttribute))
		
		self.simMenu.addMenu(self.lidsMenu)
		
		# add Setup rain event Menu
		self.buildPrecipitationMenu = self._addmenu(self.simMenu,'BuildPrecipitation',self.tr('Set Precipitation'))
		self._addmenuitem(self.buildPrecipitationMenu, 'importWheatherStations', self.tr('Import Wheather Stations'), self.importWeatherStations)
		self._addmenuitem(self.buildPrecipitationMenu, 'calculateTravelTime', self.tr('Calculate travel time'), self.maxNetworkTravelTime)
		self._addmenuitem(self.buildPrecipitationMenu, 'manageTimeSeries', self.tr('Manage time series'), self.showPrecipitationDialog)
		
		self.simMenu.addMenu(self.buildPrecipitationMenu)
		
		self.analysisMenu = self._addmenu(self.simMenu,'Analysis',self.tr('Analysis'))
		
		# add Export Menu
		self.exportMenu = self._addmenu(self.analysisMenu,'Export',self.tr('Export'))
		self._addmenuitem(self.exportMenu, 'gisdata', self.tr('Gis data'),  lambda: self.runAsThread(self.exportGISData))
		#self._addmenuitem(self.exportMenu, 'gisdata', 'Gis data',  self.exportGISData)
		self._addmenuitem(self.exportMenu, 'meteodata', self.tr('Precipitation data'), lambda: self.runAsThread(self.exportPrecipitation))
		self._addmenuitem(self.exportMenu, 'projdata', self.tr('Project data'),  lambda: self.runAsThread(self.exportProject))
		self._addmenuitem(self.exportMenu, 'exportAll', self.tr('Export all database'),lambda: self.runAsThread(self.exportAll))
		
		self.analysisMenu.addMenu(self.exportMenu)
		
		self._addmenuitem(self.analysisMenu, 'runMobidic', self.tr('Run MOBIDIC'),  lambda: self.runAsThread(self.runMobidic))
		self._addmenuitem(self.analysisMenu, 'importResults', self.tr('Import results'),  lambda: self.runAsThread(self.importResults))
		self._addmenuitem(self.analysisMenu, 'viewResults', self.tr('View results'),  self.viewResults)
		#self._addmenuitem(self.simMenu, 'importResults', 'Import Results',  self.importResults)
		
		self.simMenu.addMenu(self.analysisMenu)
		
		self.mainMenu.addMenu(self.simMenu)
		
		# add Advanced Menu
		self.advancedMenu = self._addmenu(self.mainMenu,'Advanced',self.tr('Advanced'))
		self._addmenuitem(self.advancedMenu, 'observedData', self.tr('Observed data'), self.showObservedDataDialog)
				
		self.simMenu.addMenu(self.advancedMenu)
		
		
		#~ # add Tools Menu
		#~ self.toolsMenu = self._addmenu(self.mainMenu,'Tools',self.tr('Tools'))
		#~ self._addmenuitem(self.toolsMenu, 'vector', self.tr('Import from vector'), self.importFromVector)
		#~ self._addmenuitem(self.toolsMenu, 'makeStatistics', self.tr('Calibration data'), self.showCalibrationDataDialog)
		#~ #self._addmenuitem(self.toolsMenu, 'getWMS', self.tr('get ARPA parameters'), self.getParamFromWMS)
		#~ self._addmenuitem(self.toolsMenu, 'manageDB', self.tr('Manage DB'), self.manageDB)
		#~ #self._addmenuitem(self.toolsMenu, 'setJoin', self.tr('Set join'), self.setJoin)
		#~ self._addmenuitem(self.toolsMenu, 'makeStatistics', self.tr('Statistics'), self.makeStatistics)
				
		#~ self.mainMenu.addMenu(self.toolsMenu)
				
		#self.initializationMenu.addSeparator()
		
		# add Edit Menu
		self.settingsMenu = self._addmenu(self.mainMenu,'Settings',self.tr('Settings'))
		self._addmenuitem(self.settingsMenu, 'setCommonSettings', self.tr('General settings'), self.setCommonSettings)
		self._addmenuitem(self.settingsMenu, 'setDefaults', self.tr('Default values'), self.setConstants)
								
		self.mainMenu.addMenu(self.settingsMenu)
		
		# add to the QGIS GUI

		menuBar = self.iface.mainWindow().menuBar()
		menuBar.insertMenu(self.iface.firstRightStandardMenu().menuAction(), self.mainMenu)
				
		# Add toolbar button and menu item
		self.toolBar = QToolBar('SMARTGREEN')
		self.toolBar.setObjectName('SMARTGREEN')
		iconSize = 16
		if self.guiSettings.value('IconSize') is not None:
			iconSize = int(self.guiSettings.value('IconSize'))
		
			
		self.toolBar.setIconSize(QSize(iconSize, iconSize))
		
		self._addAction(self.toolBar, 'selectUpstream', self.tr('Select Upstream'), self.selectUpstream,True)
		self._addAction(self.toolBar, 'selectDownstream', self.tr('Select Downstream'), self.selectDownstream,True)
		self._addAction(self.toolBar, 'vectorIdentify', self.tr('Vector Identify'), self.vectorIdentify,True)
		self._addAction(self.toolBar, 'plotResults', self.tr('Plot results'), self.plotResults,True)
		self._addAction(self.toolBar, 'altimetricChart', self.tr('Plot altimetric chart'), self.altimetricChart,False)
		
		self.iface.addToolBar(self.toolBar)
		
		# Init maptools
		self.upstream_tree_tool = NetworkSelectTool(self.iface, self._getAction(self.toolBar,'selectUpstream'),direction = -1)
		self.downstream_tree_tool = NetworkSelectTool(self.iface, self._getAction(self.toolBar,'selectDownstream'),direction = 1)
		self.vector_identify = VectorIdentifyTool(self.iface, self._getAction(self.toolBar,'vectorIdentify'))
		self.plot_results = PlotTool(self.iface, self._getAction(self.toolBar,'plotResults'),self)
		
	def initDockPanel(self):
		if self.smDock is None: self.smDock = SMDock(self.iface,self,self.iface.mainWindow())
		self.showDockPanel()
		self.smDock.closed.connect(self.setDockOpened)
		# connect dockpanel close event to setDockOpened
		self.smDock.setText(self.tr('SMARTGREEN is ready!'))
			
	def setDockOpened(self):
		if self.dockOpened== True: self.dockOpened = False
		else: self.dockOpened = True
			
	def showDockPanel(self):
		if self.dockOpened == False:
			self.iface.addDockWidget(self.smDock.location, self.smDock)
			self.setDockOpened()
		else:
			#print 'is true'
			pass
			
	def setCommonSettings(self):
		from forms.common_settings import CommonSettings
		# create and show the dialog 
		dlg = CommonSettings(self.iface.mainWindow(),self.tr('Edit common settings')) 
		# show the dialog
		dlg.show()
		result = dlg.exec_() 
		# See if OK was pressed
		if result == 1: 
			dlg.setSettings()
			
	def setConstants(self):
		from forms.defaults_dialog import DefaultsDialog
		# create and show the dialog 
		#dlg = DefaultsDialog(self.DBM,self.tr) 
		dlg = DefaultsDialog(self.DBM) 
		# show the dialog
		dlg.show()
		result = dlg.exec_() 
		# See if OK was pressed
		if result == 1: 
			dlg.updateValues()
		
	def setDefaults(self):
		pass
		
	def setSimulation(self):
		pass
					
	def unload(self):
		"""
		Remove the plugin menu item and icon
		"""
		self.toolBar.deleteLater()
		self.mainMenu.deleteLater()

		# unload dock panel
		try:
			self.smDock.close()
			self.smDock.deleteLater()
		except:
			pass
			
		self.dockOpened = False

	def _addmenuitem(self,parent, name, text, function):
		action = QAction(parent)
		action.setObjectName(name)
		action.setIcon(QIcon(self.plugin_dir+'/icons/'+name+'.svg'))
		action.setText(text)
		action.triggered.connect(function)
		parent.addAction(action)
		
	def _addAction(self,parent,name,text,function, checkable=False):
		action = QAction(parent)
		action.setObjectName(name)
		action.setIcon(QIcon(self.plugin_dir+'/icons/'+name+'.svg'))
		action.setText(text)
		action.setWhatsThis(self.tr("Select upstream network"))
		action.setCheckable(checkable)
		action.triggered.connect(function)
		parent.addAction(action)
	
	def _addmenu(self,parent,name,text):
		menu = QMenu(parent)
		menu.setObjectName(name)
		menu.setTitle(text)
		return menu
		
	def _getAction(self,parent,name):
		for action in parent.actions():
			if action.objectName() == name:
				return action
				
	def setFlagMoveToOthers(self):
		#print 'in setFlagMoveToOthers'
		self.flagMoveToOthers = True
		
	def setprojectIsLoaded(self):
		if self.projectIsLoaded: self.projectIsLoaded = False
		else: self.projectIsLoaded = False
		
	def showCriticalMessageBox(self,text,infoText,detailText):
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Critical)
		msg.setText(text)
		msg.setInformativeText(infoText)
		msg.setWindowTitle('SMARTGREEN')
		msg.setDetailedText(detailText)
		msg.setStandardButtons(QMessageBox.Ok)
		msg.exec_()
		
	def moveToOthers(self,layList):
		pass
		if self.projectIsLoaded == False:
			return
		
		if self.flagMoveToOthers == False:
			return

		self.projectIsLoaded = False
		self.flagMoveToOthers = False
		
		root = QgsProject.instance().layerTreeRoot()
		#layList = QgsProject.instance().mapLayers().values()
		
		for lay in layList:
			if not self.SGsettings.valueExist(lay.source()):
				#print '%s %s %s'%(lay.source(), lay.name(), lay.dataProvider().name())
				clonedLay = QgsVectorLayer(lay.source(), lay.name(), lay.dataProvider().name())
				#if not self.SGsettings.valueExist(lay.source()):
				groupIndex,mygroup = self.getGroupIndex(self.tr('Others'))
				#Add the layer to the QGIS Map Layer Registry
				QgsProject.instance().addMapLayer(clonedLay, False)
				#Insert the layer above the group
				mygroup.insertChildNode(groupIndex, QgsLayerTreeLayer(clonedLay))
				QgsProject.instance().removeMapLayers( [lay.id()] )
				
		self.flagMoveToOthers = True
				
	def removeMapLayers(self, layerIds):
		for ids in layerIds:
			lyr = QgsProject.instance().mapLayer(ids)  # returns QgsMapLayer pointer
			if lyr is not None:
				lyr_source = lyr.source()  # or .originalName()
				#print 'in removeMapLayers:', lyr_source
				if self.SGsettings.valueExist(lyr_source):
					self.showCriticalMessageBox(self.tr("Cannot remove the selected layer"),
															self.tr("Layer cannot be removed from the project because it is used by SMARTGREEN"),
															self.tr("Change file options under SMARTGREEN --> Settings--> File options "))
					# reload layer
				else:
					QgsProject.instance().removeMapLayers(ids)

				
	def getDataPath(self):
		# get the filename of the project file
		proj = QgsProject.instance()
		filename = proj.fileName()
		if filename == '':
			# ask to save the project first
			self.showCriticalMessageBox(self.tr("Please save the project first"),
													self.tr("Before continue you have to save the project"),
													self.tr("Go to Project --> Save "))
			return None
		else:
			# create directory tree
			rootName = os.path.basename(filename)
			rootName = rootName[:-4]
			rootPath = os.path.dirname(filename)
			dataDir = os.path.join(rootPath, rootName+'_DATA')
			if not os.path.exists(dataDir):
				os.makedirs(dataDir)
			return dataDir
			
	def getProjPath(self):
		proj = QgsProject.instance()
		if proj:
			filename = proj.fileName()
			rootPath = os.path.dirname(filename)
		else:
			rootPath = os.getcwd()
			
		return rootPath


	def setNewSimulation(self):
		# get the filename of the project file
		proj = QgsProject.instance()
		filename = proj.fileName()
		if filename == '':
			# ask to save the project first
			self.showCriticalMessageBox(self.tr("Please save the project first"),
													self.tr("Before continue you have to save the project"),
													self.tr("Go to Project --> Save "))
			return
		
		# Import the code for the dialog
		from forms.simulation_info_dialog import SimulationInfoDialog
		# create and show the dialog 
		dlg = SimulationInfoDialog() 
		# show the dialog
		#dlg.show()
		result = dlg.exec_() 
		# See if OK was pressed
		if result == 1: 
			self.createDB(filename)
			# set up empty project
			self.addEmptyLayers(filename)
			# add database layer
			self.loadBaseLayer()
			# update project name and description
			prjName,descrName = dlg.getValues()
			self.DBM.setDefault('project_name',prjName)
			self.DBM.setDefault('project_descr',descrName)
			
			self.plot_results.DBM = self.DBM
			
	def createDB(self, filename):
		# create db to store layers and tables
		rootName = os.path.basename(filename)
		rootName = rootName[:-4]
		rootPath = os.path.dirname(filename)
		db_filename = os.path.join(rootPath,rootName+'_DATA'+'.sqlite')
		self.DBM = SQLiteDriver(db_filename, progress = self.smDock)
		self.settings['qgis.dblite'][0] = db_filename
		
		#save DB path in the project
		self.SGsettings.saveToProject()
		
			
	def addEmptyLayers(self, filename):
		# get current mapCanvas crs and init db
		canvas = self.iface.mapCanvas()
		prjCrs = QgsProject.instance().crs()
		if prjCrs.mapUnits()>1:
			# ask to set projected coordinate system first
			self.showCriticalMessageBox(self.tr("Please set valid projection system"),
													self.tr("Before continue you have to set the project CRS to projected type"),
													self.tr("Go to Project --> Project properties --> SR"))
			return
		
		self.DBM.createSettingsTable(prjCrs)
		
		# create simulation project structure
		self.setupSimulationProject()
		
		# add default parameters
		self.openDefaultTable('defaultdbstructure',self.tr("DB structure"),self.DBM,self.tr('Defaults'),['TEXT','TEXT','TEXT','TEXT'])
		self.openDefaultTable('defaultprojectmetadata',self.tr("Project info"),self.DBM,self.tr('Defaults'),['TEXT','REAL','TEXT','TEXT'])
		self.openDefaultTable('defaultsimulationparameters',self.tr("Simulation settings"),self.DBM,self.tr('Defaults'),['TEXT','TEXT','TEXT','TEXT'])
		self.openDefaultTable('defaultconstants',self.tr("Physical constant"),self.DBM,self.tr('Defaults'),['TEXT','REAL','TEXT','TEXT'])
		self.openDefaultTable('defaulthydraulicparameters',self.tr("Hydraulic constant"),self.DBM,self.tr('Defaults'),['TEXT','REAL','TEXT','TEXT'])
		self.openDefaultTable('defaulthydrologicalparameters',self.tr("Hydrological constant"),self.DBM,self.tr('Defaults'),['TEXT','REAL','TEXT','TEXT'])
		
		# create new empty files and add to view
		# for nodes ...
		sf_filename = self.saveNodesSF('nodes')
		#self.DBM.setDefault('qgis.nodeslayer',sf_filename)
		self.addVectorLayerToTOC(filename = sf_filename,name =self.tr('Nodes'),group = self.tr('Hydraulics'),style ='nodes', formUi = 'nodes')
		# for network ...
		sf_filename = self.saveNetworkSF('links')
		#self.DBM.setDefault('qgis.networklayer',sf_filename)
		self.addVectorLayerToTOC(filename = sf_filename,name =self.tr('Links'),group = self.tr('Hydraulics'),style ='links', formUi = 'links')
		# for LID
		sf_filename = self.saveLIDlayerSF('LIDs')
		#self.DBM.setDefault('qgis.lidlayer',sf_filename)
		self.addVectorLayerToTOC(filename = sf_filename,name =self.tr('LIDs'),group = self.tr('Hydraulics'),style ='LIDs', formUi = 'LIDs')
		# for subcatchments ...
		sf_filename = self.saveSubcatchmentslayerSF('subcatchments')
		#self.DBM.setDefault('qgis.subcatchmentslayer',sf_filename)
		self.addVectorLayerToTOC(filename = sf_filename,name =self.tr('Subcatchments'),group = self.tr('Hydraulics'),style ='subcatchments', formUi = 'subcatchments')
		# for weather station ...
		sf_filename = self.saveWeatherstationslayerSF('weatherstations')
		#self.DBM.setDefault('qgis.weatherstationslayer',sf_filename)
		self.addVectorLayerToTOC(filename = sf_filename,name =self.tr('Weatherstations'),group = self.tr('Hydrology'),style ='weatherstations', formUi = 'weatherstations')
		# for soil type ...
		sf_filename = self.saveSoilslayerSF('soils')
		#self.DBM.setDefault('qgis.soilslayer',sf_filename)
		self.addVectorLayerToTOC(filename = sf_filename,name =self.tr('Soils'),group = self.tr('Hydrology'),style ='soils')
		# for landuse ...
		sf_filename = self.saveLanduseslayerSF('landuses')
		#self.DBM.setDefault('qgis.landuseslayer',sf_filename)
		self.addVectorLayerToTOC(filename = sf_filename,name =self.tr('Landuses'),group = self.tr('Hydrology'),style ='landuses')
		# for groundwater ...
		sf_filename = self.saveAcquiferlayerSF('acquifer')
		#self.DBM.setDefault('qgis.acquiferlayer',sf_filename)
		self.addVectorLayerToTOC(filename = sf_filename,name =self.tr('Acquifer'),group = self.tr('Hydrology'),style ='acquifer')
				
		# add default parameters
		self.openDefaultTable('landusesparameters',self.tr('Landuses params'),self.DBM,self.tr('Tables'))
		self.openDefaultTable('soilsparameters',self.tr('Soils params'),self.DBM,self.tr('Tables'))
		self.openDefaultTable('nofmanning',self.tr("n of Manning"),self.DBM,self.tr('Tables'),['TEXT','TEXT','REAL'])
		self.openDefaultTable('sectionshapes',self.tr("Section shapes"),self.DBM,self.tr('Tables'),['TEXT','TEXT','TEXT'])
		
		# add LIDs parameters
		self.openDefaultTable('lidtypes',self.tr("LID types"),self.DBM,self.tr('LIDs'),['TEXT','TEXT', 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'REAL', 'REAL','REAL', 'TEXT','TEXT', 'TEXT'])
		
		# add table to store array
		self.DBM.createArrayTable(tableName='results')
		self.DBM.createArrayTable(tableName='precipitations')
		self.DBM.createArrayTable(tableName='discharges')
		self.DBM.createArrayTable(tableName='waterlevels')
		
		# TODO: add snapping options? https://gis.stackexchange.com/questions/200735/qgis-doesnt-update-some-snapping-options-from-python
		
		
	def openDefaultTable(self, origTablename,newTablename,dbdriver, group, fieldTypes=[], addToTOC = False):
		# make a copy from default
		src = os.path.join(self.plugin_dir,'tables',origTablename+'.csv')
		dbdriver.importCSV(src,origTablename,columnTypes = fieldTypes)
		# load into qgis
		
		mylayer = dbdriver.getTableAsLayer(origTablename,newTablename)
		if mylayer is None:
			self.smDock.setInfo('In openDefaultTable, cannot find %s and/or %s'%(origTablename,newTablename), error = True)
			
		self.DBM.setDefault('qgis.table.'+origTablename,mylayer.source())
		#Add the layer to the QGIS Map Layer Registry
		if addToTOC:
			groupIndex,mygroup = self.getGroupIndex(group)
			QgsProject.instance().addMapLayer(mylayer, False)
			#Insert the layer above the group
			mygroup.insertChildNode(groupIndex, QgsLayerTreeLayer(mylayer))
		return mylayer
		
	def joinShpTable(self, layer, layerFld, table, tableFld,FldToBeShown = ''):
		# Set properties for the join
		joinObject = QgsVectorLayerJoinInfo()
		joinObject.joinLayerId = table.id()
		joinObject.joinFieldName = tableFld
		joinObject.targetFieldName = layerFld
		joinObject.memoryCache = True
		joinObject.prefix = ''
		if FldToBeShown != '': 	joinObject.setJoinFieldNamesSubset([FldToBeShown])
		res = layer.addJoin(joinObject)
		return res
		
	def saveNetworkSF(self, name):
		# define fields for feature attributes. A QgsFields object is needed
		fieldList = [self.DBM.getDefault('qgis.networklayer.field.obj_id'),\
						self.DBM.getDefault('qgis.networklayer.field.node_start'), self.DBM.getDefault('qgis.networklayer.field.node_end'),\
						self.DBM.getDefault('qgis.networklayer.field.s_shape'),\
						self.DBM.getDefault('qgis.networklayer.field.diam'),\
						self.DBM.getDefault('qgis.networklayer.field.dim1'), self.DBM.getDefault('qgis.networklayer.field.dim2'),\
						self.DBM.getDefault('qgis.networklayer.field.dim3'), self.DBM.getDefault('qgis.networklayer.field.dim4'),\
						self.DBM.getDefault('qgis.networklayer.field.table'),\
						self.DBM.getDefault('qgis.networklayer.field.elev_start'),self.DBM.getDefault('qgis.networklayer.field.elev_end'),\
						self.DBM.getDefault('qgis.networklayer.field.mann'),self.DBM.getDefault('qgis.networklayer.field.length'),self.DBM.getDefault('qgis.networklayer.field.tvalue'),\
						self.DBM.getDefault('qgis.networklayer.field.msg')]
						
		typeList = ['TEXT',\
						'TEXT','TEXT',\
						'TEXT',\
						'FLOAT',\
						'FLOAT','FLOAT',\
						'FLOAT','FLOAT',\
						'TEXT',\
						'FLOAT','FLOAT',\
						'FLOAT','FLOAT','FLOAT',\
						'TEXT']
						
		self.DBM.addVectorTable(name, fieldList, typeList, QgsWkbTypes.MultiLineString)
		return self.DBM.getTableSource(name)
		
	def saveNodesSF(self, name):		
		# define fields for feature attributes. A QgsFields object is needed
		fieldList = [self.DBM.getDefault('qgis.nodeslayer.field.obj_id'),\
						self.DBM.getDefault('qgis.nodeslayer.field.elev_bot'),self.DBM.getDefault('qgis.nodeslayer.field.elev_top'),\
						self.DBM.getDefault('qgis.nodeslayer.field.area'), self.DBM.getDefault('qgis.nodeslayer.field.table'), self.DBM.getDefault('qgis.nodeslayer.field.tvalue'),\
						self.DBM.getDefault('qgis.nodeslayer.field.msg')]
						
		typeList = ['TEXT',\
						'FLOAT','FLOAT',\
						'FLOAT','TEXT','FLOAT',\
						'TEXT']
		
		self.DBM.addVectorTable(name, fieldList, typeList, QgsWkbTypes.MultiPoint)
		return self.DBM.getTableSource(name)
		
	def saveSoilslayerSF(self, name):
		# define fields for feature attributes. A QgsFields object is needed
		fieldList = [self.DBM.getDefault('qgis.soilslayer.field.obj_id'),\
						self.DBM.getDefault('qgis.soilslayer.field.ks'),self.DBM.getDefault('qgis.soilslayer.field.wg0'),self.DBM.getDefault('qgis.soilslayer.field.wc0'),\
						self.DBM.getDefault('qgis.soilslayer.field.msg')]
		typeList = ['TEXT',\
						'FLOAT','FLOAT','FLOAT',\
						'TEXT']
		
		self.DBM.addVectorTable(name, fieldList, typeList, QgsWkbTypes.MultiPolygon)
		return self.DBM.getTableSource(name)
		
	def saveLanduseslayerSF(self, name):
		# define fields for feature attributes. A QgsFields object is needed
		fieldList = [self.DBM.getDefault('qgis.landuseslayer.field.obj_id'),self.DBM.getDefault('qgis.landuseslayer.field.wp0'),self.DBM.getDefault('qgis.landuseslayer.field.ch'),\
						self.DBM.getDefault('qgis.landuseslayer.field.alb'),self.DBM.getDefault('qgis.landuseslayer.field.msg')]
		typeList = ['TEXT','FLOAT','FLOAT',\
						'FLOAT','TEXT']
		
		self.DBM.addVectorTable(name, fieldList, typeList, QgsWkbTypes.MultiPolygon)
		return self.DBM.getTableSource(name)
		
	def saveWeatherstationslayerSF(self, name):
		# define fields for feature attributes. A QgsFields object is needed
		fieldList = [self.DBM.getDefault('qgis.weatherstationslayer.field.obj_id'),self.DBM.getDefault('qgis.weatherstationslayer.field.name'),\
						self.DBM.getDefault('qgis.weatherstationslayer.field.a1'), self.DBM.getDefault('qgis.weatherstationslayer.field.n'),\
						self.DBM.getDefault('qgis.weatherstationslayer.field.alp'),self.DBM.getDefault('qgis.weatherstationslayer.field.eps'),\
						self.DBM.getDefault('qgis.weatherstationslayer.field.kap'),self.DBM.getDefault('qgis.weatherstationslayer.field.table'),\
						self.DBM.getDefault('qgis.weatherstationslayer.field.msg')]
		typeList = ['TEXT','TEXT',\
						'FLOAT', 'FLOAT',\
						'FLOAT','FLOAT',\
						'FLOAT','TEXT',\
						'TEXT']
		
		self.DBM.addVectorTable(name, fieldList, typeList, QgsWkbTypes.MultiPoint)
		return self.DBM.getTableSource(name)
		
	def saveSubcatchmentslayerSF(self, name):
		# define fields for feature attributes. A QgsFields object is needed
		
		fieldList = [self.DBM.getDefault('qgis.subcatchmentslayer.field.obj_id'),
						self.DBM.getDefault('qgis.subcatchmentslayer.field.node_id'),
						self.DBM.getDefault('qgis.subcatchmentslayer.field.ks'),
						self.DBM.getDefault('qgis.subcatchmentslayer.field.wg0'),
						self.DBM.getDefault('qgis.subcatchmentslayer.field.wc0'),
						self.DBM.getDefault('qgis.subcatchmentslayer.field.wp0'),
						self.DBM.getDefault('qgis.subcatchmentslayer.field.ch'),
						self.DBM.getDefault('qgis.subcatchmentslayer.field.alb'),
						self.DBM.getDefault('qgis.subcatchmentslayer.field.kf'),
						self.DBM.getDefault('qgis.subcatchmentslayer.field.ma'),
						self.DBM.getDefault('qgis.subcatchmentslayer.field.mf'),
						self.DBM.getDefault('qgis.subcatchmentslayer.field.tvalue'),
						self.DBM.getDefault('qgis.subcatchmentslayer.field.msg')]
		typeList = ['TEXT','TEXT','FLOAT','FLOAT','FLOAT','FLOAT','FLOAT','FLOAT','FLOAT','FLOAT','FLOAT','FLOAT','TEXT']
		
		self.DBM.addVectorTable(name, fieldList, typeList, QgsWkbTypes.MultiPolygon)
		return self.DBM.getTableSource(name)

	def saveAcquiferlayerSF(self, name):
		# define fields for feature attributes. A QgsFields object is needed
		fieldList = [self.DBM.getDefault('qgis.acquiferlayer.field.obj_id'),\
						self.DBM.getDefault('qgis.acquiferlayer.field.kf'),self.DBM.getDefault('qgis.acquiferlayer.field.ma'),self.DBM.getDefault('qgis.acquiferlayer.field.mf'),\
						self.DBM.getDefault('qgis.acquiferlayer.field.msg')]
		typeList = ['TEXT',\
						'FLOAT','FLOAT','FLOAT',\
						'TEXT']
		
		self.DBM.addVectorTable(name, fieldList, typeList, QgsWkbTypes.MultiPolygon)
		return self.DBM.getTableSource(name)
		
	def saveLIDlayerSF(self, name):
		# define fields for feature attributes. A QgsFields object is needed
		fieldList = [self.DBM.getDefault('qgis.lidlayer.field.obj_id'),\
						self.DBM.getDefault('qgis.lidlayer.field.name'),self.DBM.getDefault('qgis.lidlayer.field.node_to'),self.DBM.getDefault('qgis.lidlayer.field.type'),self.DBM.getDefault('qgis.lidlayer.field.cat'),\
						self.DBM.getDefault('qgis.lidlayer.field.vol'),self.DBM.getDefault('qgis.lidlayer.field.height'),self.DBM.getDefault('qgis.lidlayer.field.diam_out'),\
						self.DBM.getDefault('qgis.lidlayer.field.height_out'),self.DBM.getDefault('qgis.lidlayer.field.depth'),self.DBM.getDefault('qgis.lidlayer.field.ks_soil'),\
						self.DBM.getDefault('qgis.lidlayer.field.teta_sat'),self.DBM.getDefault('qgis.lidlayer.field.teta_fc'),self.DBM.getDefault('qgis.lidlayer.field.teta_wp'),\
						self.DBM.getDefault('qgis.lidlayer.field.slope'),self.DBM.getDefault('qgis.lidlayer.field.wp_max'),self.DBM.getDefault('qgis.lidlayer.field.ks_sub'),\
						self.DBM.getDefault('qgis.lidlayer.field.msg')]
		typeList = ['TEXT',\
						'TEXT','TEXT','TEXT','TEXT',\
						'FLOAT','FLOAT','FLOAT',\
						'FLOAT','FLOAT','FLOAT',\
						'FLOAT','FLOAT','FLOAT',\
						'FLOAT','FLOAT','FLOAT',\
						'TEXT']
		
		self.DBM.addVectorTable(name, fieldList, typeList, QgsWkbTypes.MultiPolygon)
		return self.DBM.getTableSource(name)
		
		
	def setupSimulationProject(self):
		# define group tree
		root = QgsProject.instance().layerTreeRoot()
		self.hydraulicsGroup = root.addGroup(self.tr('Hydraulics'))
		self.hydrologyGroup = root.addGroup(self.tr('Hydrology'))
		#self.timeSeriesGroup = root.addGroup(self.tr('Time series'))
		#self.timeSeriesGroup = root.addGroup(self.tr('Tables'))
	
	def setLayers(self):
		# Import the code for the dialog
		from forms.layers_dialog import LayersDialog
		# create and show the dialog 
		dlg = LayersDialog(self.SGsettings) 
		# show the dialog
		dlg.show()
		result = dlg.exec_() 
		# See if OK was pressed
		if result == 1: 
			dlg.updateValues()
			# save to local path
			self.SGsettings.saveToProject()
		
	def setParameters(self):
		pass
		
	def setFilesDirectories(self):
		pass
		
	def loadlayer(self,pathToLayer,layerName, groupName):
		from os.path import isfile
		
		driver = None
		if pathToLayer == '':
			pass
		elif isfile(pathToLayer):
			driver = 'ogr'
		elif "wfs" in pathToLayer:
			driver = 'wfs'
		elif "wms" in pathToLayer:
			driver = 'wms'
		else:
			pass
		
		if driver is not None:
			lay = self.addVectorLayerToTOC(filename=pathToLayer,name=layerName,group=groupName,driver = driver, style = None, formUi = None)
			if lay is None:
				self.showCriticalMessageBox(self.tr('Unable to load a layer'),self.tr('Cannot load file %s'%pathToLayer),self.tr('please check if the file format is supported by OGR driver and/or the file exists'))
		
		
	def loadBaseLayer(self):
		from os.path import isfile
		s = QSettings()
		pathToLinks = s.value('SMARTGREEN/pathToLinks', '')
		pathToNodes = s.value('SMARTGREEN/pathToNodes', '')
		pathToLanduses = s.value('SMARTGREEN/pathToLanduses', '')
		pathToSoils = s.value('SMARTGREEN/pathToSoils', '')
		pathToWheatherStations = s.value('SMARTGREEN/pathToWheatherStations', '')
		pathToAcquifers = s.value('SMARTGREEN/pathToAcquifers', '')
		
		self.loadlayer(pathToLinks,self.tr('CAP links'), self.tr('Others'))
		self.loadlayer(pathToNodes,self.tr('CAP nodes'), self.tr('Others'))
		self.loadlayer(pathToLanduses,self.tr('Regional landuses'), self.tr('Others'))
		self.loadlayer(pathToSoils,self.tr('Regional soils'), self.tr('Others'))
		self.loadlayer(pathToWheatherStations,self.tr('Regional Wheather stations'), self.tr('Others'))
		self.loadlayer(pathToAcquifers,self.tr('Regional acquifer'), self.tr('Others'))
		
	def importLinks(self):
		lay = self.getLayerBySource(self.DBM.getDefault('qgis.networklayer'))
		self.importFromVector(lay)
		
	def importNodes(self):
		lay = self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer'))
		mask = self.getLayerBySource(self.DBM.getDefault('qgis.networklayer'))
		self.importFromVector(lay,mask)
		
	def importLanduses(self):
		lay = self.getLayerBySource(self.DBM.getDefault('qgis.landuseslayer'))
		mask = self.getLayerBySource(self.DBM.getDefault('qgis.subcatchmentslayer'))
		self.importFromVector(lay,mask)
		
	def importSoils(self):
		lay = self.getLayerBySource(self.DBM.getDefault('qgis.soilslayer'))
		mask = self.getLayerBySource(self.DBM.getDefault('qgis.subcatchmentslayer'))
		self.importFromVector(lay,mask)
		
	def importWeatherStations(self):
		lay = self.getLayerBySource(self.DBM.getDefault('qgis.weatherstationslayer'))
		mask = self.getLayerBySource(self.DBM.getDefault('qgis.subcatchmentslayer'))
		self.importFromVector(lay,mask)
		
	def importAcquifer(self):
		lay = self.getLayerBySource(self.DBM.getDefault('qgis.acquiferlayer'))
		mask = self.getLayerBySource(self.DBM.getDefault('qgis.subcatchmentslayer'))
		self.importFromVector(lay,mask)
		
	def importLids(self):
		lay = self.getLayerBySource(self.DBM.getDefault('qgis.lidlayer'))
		mask = self.getLayerBySource(self.DBM.getDefault('qgis.subcatchmentslayer'))
		self.importFromVector(lay,mask)
				
	def importFromVector(self, toLayer = None, maskLayer= None):
		from .forms.import_dialog import ImportDialog
		# create and show the dialog
		if toLayer is None: toLayer = self.iface.activeLayer()
		
		if toLayer is None:
			self.showCriticalMessageBox(self.tr("Please select a vector layer"),
													self.tr("Before continue you have to select a vector layer"),
													self.tr("Click on the layer name"))
			return
			
		if not isinstance(toLayer, QgsVectorLayer):
			self.showCriticalMessageBox(self.tr("Please select a vector layer"),
													self.tr("You have selected a layer of type %s. Before continue you have to select a vector layer" %(type(toLayer))),
													self.tr("Click on the layer name"))
			return
		
		
		if self.compareLayerSource(toLayer.source(),self.DBM.getDefault('qgis.networklayer')):
			# is the network layer
			dlg = ImportDialog(title = self.tr('Import into %s from existing layer'%(toLayer.name())),
										layType='line',settings = self.DBM,
										importTableName = os.path.join(self.plugin_dir,'tables','importnetwork.csv'),
										tr = self.tr) 
		elif self.compareLayerSource(toLayer.source(),self.DBM.getDefault('qgis.nodeslayer')):
			# is the network layer
			dlg = ImportDialog(title = self.tr('Import into %s from existing layer'%(toLayer.name())),
										layType='point',settings = self.DBM,
										importTableName = os.path.join(self.plugin_dir,'tables','importnodes.csv'),
										tr = self.tr)
		elif self.compareLayerSource(toLayer.source(),self.DBM.getDefault('qgis.subcatchmentslayer')):
			# is the network layer
			dlg = ImportDialog(title = self.tr('Import into %s from existing layer'%(toLayer.name())),
										layType='polygon',settings = self.DBM,
										importTableName = os.path.join(self.plugin_dir,'tables','importsubcatchments.csv'),
										tr = self.tr)
		elif self.compareLayerSource(toLayer.source(),self.DBM.getDefault('qgis.weatherstationslayer')):
			# is the network layer
			dlg = ImportDialog(title = self.tr('Import into %s from existing layer'%(toLayer.name())),
										layType='all',settings = self.DBM,
										importTableName = os.path.join(self.plugin_dir,'tables','importweatherstations.csv'),
										tr = self.tr)
		elif self.compareLayerSource(toLayer.source(),self.DBM.getDefault('qgis.soilslayer')):
			# is the network layer
			dlg = ImportDialog(title = self.tr('Import into %s from existing layer'%(toLayer.name())),
										layType='polygon',settings = self.DBM,
										importTableName = os.path.join(self.plugin_dir,'tables','importsoils.csv'),
										tr = self.tr)
		elif self.compareLayerSource(toLayer.source(),self.DBM.getDefault('qgis.landuseslayer')):
			# is the network layer
			dlg = ImportDialog(title = self.tr('Import into %s from existing layer'%(toLayer.name())),
										layType='polygon',settings = self.DBM,
										importTableName = os.path.join(self.plugin_dir,'tables','importlanduses.csv'),
										tr = self.tr)
		elif self.compareLayerSource(toLayer.source(),self.DBM.getDefault('qgis.acquiferlayer')):
			# is the network layer
			dlg = ImportDialog(title = self.tr('Import into %s from existing layer'%(toLayer.name())),
										layType='polygon',settings = self.DBM,
										importTableName = os.path.join(self.plugin_dir,'tables','importacquifer.csv'),
										tr = self.tr)
		elif self.compareLayerSource(toLayer.source(),self.DBM.getDefault('qgis.lidlayer')):
			# is the network layer
			dlg = ImportDialog(title = self.tr('Import into %s from existing layer'%(toLayer.name())),
										layType='polygon',settings = self.DBM,
										importTableName = os.path.join(self.plugin_dir,'tables','importlids.csv'),
										tr = self.tr)
		else:
			# it is not recognized
			self.showCriticalMessageBox(self.tr("Please select an other vector layer"),
													self.tr("You have selected the layer %s but it is not recognized as a valid layer (%s)" %(toLayer.name(),toLayer.source())),
													self.tr("Click on an other layer name"))
			return
			
		# show the dialog
		dlg.show()
		result = dlg.exec_() 
		
		# See if OK was pressed
		if result == 1: 
			data = dlg.getValues()
			# import from layer
			
			fromLayer = self.getLayerBySource(data['importFromLayer'])
			del data['importFromLayer']
			
			# select feature that intesect mask layer id defined
			if maskLayer is not None:
				selectByLocation(fromLayer,maskLayer,0,['intersects'],precision=0.001, progress = None)

			# check if there are selection in fromLayer
			if fromLayer.selectedFeatureCount()==0:
				self.showCriticalMessageBox(text='SMARTGREEN',
														infoText=self.tr('Import from layer failed because there is no selected features'),
														detailText=self.tr('Use select upstream tool in case of links layer or check watershed extension or use other selection tool.'))
				return
							
			self.DBM.importFromLayer(fromLayer, toLayer, data, self.DBM)
			
			# remember to save the option in to the project
			#self.SGsettings.saveToProject()
			# TODO: try also void 	setDataSource (const QString &dataSource, const QString &baseName, const QString &provider, bool loadDefaultStyleFlag=false)
			toLayer.updateExtents() # try to update extents ...
			toLayer.reload()
			#toLayer.setCacheImage(None)
			toLayer.triggerRepaint()
						
			# # as no prevoius solutions seems to update feature count and extents, force it adding/removing feature
			# toLayer.startEditing()
			# # add feature
			# newFeat = QgsFeature(toLayer.fields())
			#
			# for feat in fromLayer.getFeatures():
			# 	newFeat.setGeometry(feat.geometry())
			# 	flag = toLayer.addFeatures([newFeat])
			# 	if not flag: self.smDock.setInfo('In importFromVector, cannot add feature', error = True)
			# 	break
			#
			# toLayer.commitChanges()
			#
			# toLayer.updateExtents()
			#
			# toLayer.startEditing()
			# # delete last feature
			# toLayer.deleteSelectedFeatures()
			# toLayer.commitChanges()
			#
			# toLayer.updateExtents()
			
				
	def printSettings(self):
		self.SGsettings.printSettings()

	def runAsThread(self, function):
		self.smDock.setTab(self.tr('Report'))
		s = QSettings()
		debugMode = s.value('SMARTGREEN/debugMode', False)
		if debugMode == 'True':
			print('running in debug mode ...')
			from .tools.my_progress import MyProgress
			mp = MyProgress()
			function(progress = mp)
			QMessageBox.information(self.iface.mainWindow(), 'SMARTGREEN', self.tr("Process concluded. See python console for details"))
			return

		#print('running in user mode ...')
		try:
			from .tools.worker import Worker
			
			self.thread = QThread()
			self.worker = Worker(self.iface.mainWindow(),function, progress= None)
			#self.worker.ready.connect(self.myprogress.exec_)
			self.worker.reportProgress.connect(self.smDock.setPercentage)
			self.worker.reportMessage.connect(self.smDock.appendText)
			#self.worker.finished.connect(self.thread.quit)
			self.worker.finished.connect(self.processConcluded)
			#self.worker.finished.connect(self.myprogress.close)

			self.worker.moveToThread(self.thread)

			self.thread.started.connect(self.worker.process)
			#~ logging.info("Start thread")
			self.thread.start()
			#~ logging.info("End thread")
			#QMessageBox.information(self.iface.mainWindow(), 'SMARTGREEN', self.tr("Process concluded. See SMARTGREEN report tab for details"))
		except Exception as e:
			#~ log.exception("Error! %s"%(str(e)))
			if self.thread: self.thread.quit()
			self.showCriticalMessageBox('SMARTGREEN',self.tr("An error occurred! See details."),self.tr("Error message: %s")%(str(e)))
			#pass

	def processConcluded(self):
		if self.thread: self.thread.quit()
		QMessageBox.information(self.iface.mainWindow(), 'SMARTGREEN',
								self.tr("Process concluded. See SMARTGREEN report tab for details"))
	
	def exportAll(self, progress = None):
		progress.setInfo(self.tr('Export GIS data'),False)
		self.exportGISData(progress)
		progress.setInfo(self.tr('Export Precipitation data'),False)
		self.exportPrecipitation(progress)
		progress.setInfo(self.tr('Export Project data'),False)
		self.exportProject(progress)

	def exportProject(self,progress= None):
		# get qgis project full name
		prjFile = QFileInfo(QgsProject.instance().fileName())
		prjFP = prjFile.filePath()
		# replace extantion from prj to cfm
		cfmFP = prjFP[:-4]+'.cfm'
		self.DBM.setDefault('mobidicproject',cfmFP)
		
		prjAP = prjFile.absolutePath()
		
		outputPath = osp.join(prjAP,'states')
		# create dir if it doesn't exist
		if not osp.exists(outputPath):
			os.mkdir(outputPath)
			
		self.DBM.setDefault('statespath',osp.join(outputPath,''))
		
		# write MOBIDIC-u options
		PE = ProjectExporter(self.DBM,self.tr,progress)
		PE.saveAsCFM(cfmFP)
		if not progress is None: progress.setInfo(self.tr('Project exported to %s'%(cfmFP)))
		
	def exportPrecipitation(self,progress= None):
		# setup simulation variables
		prjFile = QFileInfo(QgsProject.instance().fileName())
		prjAP = prjFile.absolutePath()
		
		#outputPath = osp.dirname(self.settings['qgis.nodeslayer'][0])
		outputPath = osp.join(prjAP,'meteo')
		# create dir if it doesn't exist
		if not osp.exists(outputPath):
			os.mkdir(outputPath)
			
		self.DBM.setDefault('timeseriespath',osp.join(outputPath,''))
		
		WE = WeatherExporter(progress)
		WE.setWeatherstationsLayer(weatherstationsLayer = self.getLayerBySource(self.DBM.getDefault('qgis.weatherstationslayer')),\
												f_id = self.DBM.getDefault('qgis.weatherstationslayer.field.obj_id'),\
												f_name = self.DBM.getDefault('qgis.weatherstationslayer.field.name'),\
												f_datafile = self.DBM.getDefault('qgis.weatherstationslayer.field.table'))
												
		WE.setDB(self.DBM)
												
		WE.setSimulationExtreme(simulationTime = float(self.DBM.getDefault('urban.simlength')),\
												timeStep = (1.0/3600.0)*float(self.DBM.getDefault('basestep')))
		
		WE.weatherStationsToMat(self.DBM.getDefault('timeseriespath')+'meteodata.mat')
		
		if not progress is None:
			progress.setText(self.tr('Exportation concluded!'))
			progress.setPercentage(0)

	def exportGISData(self,progress= None):
		# TODO: set up temp path
		s = QSettings()
		tempPath = s.value('SMARTGREEN/pathToDebug', '')
		
		if not exists(tempPath):
			tempPath = None
		
		
		prjFile = QFileInfo(QgsProject.instance().fileName())
		prjAP = prjFile.absolutePath()
		
		outputPath = osp.join(prjAP,'geodata')
		# create dir if it doesn't exist
		if not osp.exists(outputPath):
			os.mkdir(outputPath)
			
		self.DBM.setDefault('gisdatapath',osp.join(outputPath,'gisdata.mat'))
		
		# get maximum extents
		ext = self.getMaximumExtent()
		
		# set lat lon of the centroid
		centerPt = ext.center()
		sourceCrs = QgsProject.instance().crs()
		destCrs = QgsCoordinateReferenceSystem(4326)
		tr = QgsCoordinateTransform(sourceCrs, destCrs,QgsProject.instance())
		centerPt = tr.transform(centerPt)
		print('orig point:',ext.center(),'center point:',centerPt)
		dataToMat(filename = self.DBM.getDefault('gisdatapath'),data = centerPt.x(),name= 'blon',progress = progress,tr = self.tr)
		dataToMat(filename = self.DBM.getDefault('gisdatapath'),data = centerPt.y(),name= 'blat',progress = progress,tr = self.tr)
				
		if progress: progress.setInfo(self.tr('Make a mask ...'))
		# make a raster mask
		mask = GisGrid()
		mask.fitToExtent(ext,dx = float(self.DBM.getDefault('qgis.cellsize')),dy=float(self.DBM.getDefault('qgis.cellsize')),nodata =  -3.4028234663852886e+038)
		RZ = Rasterizer(mask,progress)
		RZ.polyToRaster(polyLayer=self.getLayerBySource(self.DBM.getDefault('qgis.subcatchmentslayer')),fieldName='',multiply=1,defaultValue=1)
		if tempPath: mask.saveAsASC(filename = osp.join(tempPath,'mask.asc'),progress = progress)
		
		# export LIDs
		if progress: progress.setInfo(self.tr('Export LIDs ...'))
		
		# rasterize LIDs map
		lids  = mask.copy(mask.nodata)
		RZ = Rasterizer(lids,progress)
		# RASTERIZE OBJ_ID VALUES
		RZ.polyToRaster(polyLayer=self.getLayerBySource(self.DBM.getDefault('qgis.lidlayer')),fieldName='OBJ_ID',multiply=1,defaultValue=1)
		lids.saveAsMAT(filename = self.DBM.getDefault('gisdatapath'),name= 'GIraster',progress = progress)
		if tempPath: lids.saveAsASC(filename = osp.join(tempPath,'lids_mask.asc'),progress = progress)		
		
		# TODO: check flip data
		lids.data = np.flip(lids.data,0)
		
		LE = LidsExporter(progress)
		LE.setLidsLayer(self.getLayerBySource(self.DBM.getDefault('qgis.lidlayer')))
		LE.setNodesLayer(self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),\
									self.DBM.getDefault('qgis.nodeslayer.field.obj_id'),\
									self.DBM.getDefault('qgis.nodeslayer.field.elev_bot'),\
									self.DBM.getDefault('qgis.nodeslayer.field.elev_top'),\
									self.DBM.getDefault('qgis.nodeslayer.field.area'),\
									self.DBM.getDefault('qgis.nodeslayer.field.table')
									)
									
		LE.setLidsGrid(lids)

		LE.lidsToMat(matFileName = self.DBM.getDefault('gisdatapath')) #broken :(
				
		# save number of domain cells
		dataToMat(filename = self.DBM.getDefault('gisdatapath'),data = mask.count(),name= 'A',progress = progress,tr = self.tr)
		
		if progress: progress.setInfo(self.tr('Make a virtual dem ...'))
		# make virtual dem
		ITP = Interpolate(progress)
		
		# get point coordinates and value
		# load all points inside the extention, so we are sure that all points are inside the grid
		xs = []
		ys = []
		vals = []
		
		request = QgsFeatureRequest().setFilterRect(ext)
		inputLayer = self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer'))
		fieldIdx =  inputLayer.fields().indexFromName(self.DBM.getDefault('qgis.nodeslayer.field.elev_top'))
		features = inputLayer.getFeatures(request)
		if progress: progress.setText(self.tr('loop points ...'))
		for f in features:
			val = f.attributes()[fieldIdx]
			# exit from function if elevation is null
			if val == NULL:
				progress.setInfo(self.tr('Unable to export dataset because Null value for elevation in nodes layer at feature %s'%f['OBJ_ID']),True)
				return

			# get coordinates
			geom = f.geometry()
			geomType = geom.wkbType()
			if geomType==QgsWkbTypes.Point:
				vertex = geom.asPoint()
				xs.append(vertex[0])
				ys.append(vertex[1])
			elif geomType==QgsWkbTypes.MultiPoint:
				multiPoint = geom.asMultiPoint()
				vertex = multiPoint[0]
				xs.append(vertex[0])
				ys.append(vertex[1])
			else:
				pass
				
			vals.append(val)
		
		minDist, minIdx, assVal  = ITP.nearestNeighbour(mask,xs,ys,vals)
		
		demGrid = assVal+minDist*0.01
		if progress: progress.setText(self.tr('Save to  %s'%self.DBM.getDefault('gisdatapath')))
		zz = demGrid*mask
		zz.saveAsMAT(filename = self.DBM.getDefault('gisdatapath'),name= 'zz',progress = progress)
		if tempPath: zz.saveAsASC(filename = osp.join(tempPath,'zz.asc'),progress = progress)		
		L_cell2node = minDist*mask
		L_cell2node.saveAsMAT(filename = self.DBM.getDefault('gisdatapath'),name= 'L_cell2node',progress = progress)
		if tempPath: L_cell2node.saveAsASC(filename = osp.join(tempPath,'L_cell2node.asc'),progress = progress)		
		
		# make a map of point index (one-based)
		minDist, minIdx, assVal  = ITP.nearestNeighbour(mask,xs,ys,None)
		ch = (minIdx+1)*mask
		# overwrite where lids are defined
		self.rasterizeParam(ch,self.getLayerBySource(self.DBM.getDefault('qgis.lidlayer')),'',1,progress,LE.nodeIdx)
		#ch.saveAsASC(filename = osp.join(tempPath,'ch.asc'),progress = progress)
		
		ch.saveAsMAT(filename = self.DBM.getDefault('gisdatapath'),name= 'ch',progress = progress)
		
		if progress: progress.setText(self.tr('Make a flow direction grid ...'))
		# make flow direction
		HYD = Hydrology(progress)
		flowDir,maxSlope = HYD.flowDirectionAndSlope(demGrid, fdCode = 'grass')
		flowflowDirGRASS = flowDir*mask
		# replace data to fit mobidic code
		flowDirMobi = mask.copy(0.0)
		AI=[1,2,3,4,5,6,7,8]
		MD=[5,6,7,8,1,2,3,4]
		for i,ai in enumerate(AI):
			flowDirMobi.data[flowDir.data == ai] = MD[i]
		# mask flow direction
		flowDirMobi = flowDirMobi*mask
		if progress: progress.setText(self.tr('Make flow direction'))
		flowDirMobi.saveAsMAT(filename = self.DBM.getDefault('gisdatapath'),name= 'zp',progress = progress)
		#flowDirMobi.saveAsASC(filename = osp.join(tempPath,'zp_mobidic.asc'),progress = progress)
		# DEBUG 
		#~ flowDirGRASS,maxSlopeGRASS = HYD.flowDirectionAndSlope(demGrid, fdCode = 'grass')
		#~ flowflowDirGRASS = flowDirGRASS*mask
		#~ flowflowDirGRASS.saveAsASC(filename = 'D:/test_gisdata/zp_grass.asc',progress = progress)
		
		# mask slope
		maxSlope = maxSlope*mask
		if progress: progress.setText(self.tr('Make slope'))
		alpsur = (maxSlope**0.5)
		alpsurMean = alpsur.mean()
		alpsur = alpsur/alpsurMean
		alpsur.saveAsMAT(filename = self.DBM.getDefault('gisdatapath'),name= 'alpsur',progress = progress)
		#alpsur.saveAsASC(filename = osp.join(tempPath,'alpsur.asc'),progress = progress)		
		
		# calculate contributing area
		if progress: progress.setText(self.tr('Make contributing area'))
		zr = HYD.contributingArea(flowDir,False) # as number of cells
		zr.saveAsMAT(filename = self.DBM.getDefault('gisdatapath'),name= 'zr',progress = progress)
		if tempPath: zr.saveAsASC(filename = osp.join(tempPath,'zr.asc'),progress = progress)		
		# save max value of zr
		zrmax = zr.max()
		dataToMat(filename = self.DBM.getDefault('gisdatapath'),data = zrmax,name= 'zrmax',progress = progress,tr = self.tr)
		# save the index corresponding to zrmax
		ifoc = zr.getIndex(zrmax)
		dataToMat(filename = self.DBM.getDefault('gisdatapath'),data = ifoc,name= 'ifoc',progress = progress,tr = self.tr)
		# save index of flow path
		k1,k2,k3,k4,k5,k6,k7,k8,st8 = HYD.stack8point(flowDirMobi)
		
		dataToMat(filename = self.DBM.getDefault('gisdatapath'),data = k1,name= 'sk1',progress = progress,tr = self.tr)
		dataToMat(filename = self.DBM.getDefault('gisdatapath'),data = k2,name= 'sk2',progress = progress,tr = self.tr)
		dataToMat(filename = self.DBM.getDefault('gisdatapath'),data = k3,name= 'sk3',progress = progress,tr = self.tr)
		dataToMat(filename = self.DBM.getDefault('gisdatapath'),data = k4,name= 'sk4',progress = progress,tr = self.tr)
		dataToMat(filename = self.DBM.getDefault('gisdatapath'),data = k5,name= 'sk5',progress = progress,tr = self.tr)
		dataToMat(filename = self.DBM.getDefault('gisdatapath'),data = k6,name= 'sk6',progress = progress,tr = self.tr)
		dataToMat(filename = self.DBM.getDefault('gisdatapath'),data = k7,name= 'sk7',progress = progress,tr = self.tr)
		dataToMat(filename = self.DBM.getDefault('gisdatapath'),data = k8,name= 'sk8',progress = progress,tr = self.tr)
		dataToMat(filename = self.DBM.getDefault('gisdatapath'),data = st8,name= 'st8',progress = progress,tr = self.tr)
		
		# channelized flow fraction
		threchan=0 
		dataToMat(filename = self.DBM.getDefault('gisdatapath'),data = threchan,name= 'threchan',progress = progress,tr = self.tr)
		#~ cha=(zr-threchan)/zrmax
		#~ cha=cha*(cha > 0) # set cha minor that zero to zero
		cha  = mask.copy(1.0)
		cha.saveAsMAT(filename = self.DBM.getDefault('gisdatapath'),name= 'cha',progress = progress)
		if tempPath: cha.saveAsASC(filename = osp.join(tempPath,'cha.asc'),progress = progress)
		
		aann=1
		dataToMat(filename = self.DBM.getDefault('gisdatapath'),data = aann,name= 'aann',progress = progress,tr = self.tr)
		
		
		# rasterize soil variables
		if progress: progress.setText(self.tr('Export Wg0'))
		Wg0 = mask.copy(mask.nodata)
		self.rasterizeParam(Wg0,self.getLayerBySource(self.DBM.getDefault('qgis.subcatchmentslayer')),'WG0',0.001,progress)
		# overwrite where soils are defined
		self.rasterizeParam(Wg0,self.getLayerBySource(self.DBM.getDefault('qgis.soilslayer')),'WG0',0.001,progress)
		if tempPath: Wg0.saveAsASC(filename = osp.join(tempPath,'Wg0beforelids.asc'),progress = progress)
		# overwrite where lids are defined
		self.rasterizeParam(Wg0,self.getLayerBySource(self.DBM.getDefault('qgis.lidlayer')),'',1,progress,LE.Wg0)
		if tempPath: Wg0.saveAsASC(filename = osp.join(tempPath,'Wg0afterlids.asc'),progress = progress)
		Wg0.saveAsMAT(filename = self.DBM.getDefault('gisdatapath'),name= 'Wg0',progress = progress)
		#Wg0 = Wg0*1000
		if tempPath: Wg0.saveAsASC(filename = osp.join(tempPath,'Wg0.asc'),progress = progress)
		
		if progress: progress.setText(self.tr('Export Wc0'))
		Wc0 = mask.copy(mask.nodata)
		self.rasterizeParam(Wc0,self.getLayerBySource(self.DBM.getDefault('qgis.subcatchmentslayer')),'WC0',0.001,progress)
		self.rasterizeParam(Wc0,self.getLayerBySource(self.DBM.getDefault('qgis.soilslayer')),'WC0',0.001,progress)
		if tempPath: Wc0.saveAsASC(filename = osp.join(tempPath,'Wc0beforelids.asc'),progress = progress)
		# overwrite where lids are defined
		self.rasterizeParam(Wc0,self.getLayerBySource(self.DBM.getDefault('qgis.lidlayer')),'',1,progress,LE.Wc0)
		if tempPath: Wc0.saveAsASC(filename = osp.join(tempPath,'Wc0afterlids.asc'),progress = progress)
		Wc0.saveAsMAT(filename = self.DBM.getDefault('gisdatapath'),name= 'Wc0',progress = progress)
		
		if progress: progress.setText(self.tr('Export ks'))
		ks = mask.copy(mask.nodata)
		self.rasterizeParam(ks,self.getLayerBySource(self.DBM.getDefault('qgis.subcatchmentslayer')),'KS',1.0/3600/1000,progress) #mm/h to m/s
		self.rasterizeParam(ks,self.getLayerBySource(self.DBM.getDefault('qgis.soilslayer')),'KS',1.0/3600/1000,progress) #mm/h to m/s
		# overwrite where lids are defined
		self.rasterizeParam(ks,self.getLayerBySource(self.DBM.getDefault('qgis.lidlayer')),'',1,progress,LE.ks0) # already in m/s
		if tempPath: ks.saveAsASC(filename = osp.join(tempPath,'ksafterlids.asc'),progress = progress)
		ks.saveAsMAT(filename = self.DBM.getDefault('gisdatapath'),name= 'ks',progress = progress)
		
		# rasterize landuse variable #TODO #ERRORE
		if progress: progress.setText(self.tr('Export Wp0'))
		Wp0 = mask.copy(mask.nodata)
		self.rasterizeParam(Wp0,self.getLayerBySource(self.DBM.getDefault('qgis.subcatchmentslayer')),'WP0',0.001,progress)
		self.rasterizeParam(Wp0,self.getLayerBySource(self.DBM.getDefault('qgis.landuseslayer')),'WP0',0.001,progress)
		if tempPath: Wp0.saveAsASC(filename = osp.join(tempPath,'Wp0beforelids.asc'),progress = progress)
		# overwrite where lids are defined
		self.rasterizeParam(Wp0,self.getLayerBySource(self.DBM.getDefault('qgis.lidlayer')),'',1,progress,LE.Wp0)
		if tempPath: Wp0.saveAsASC(filename = osp.join(tempPath,'Wp0afterlids.asc'),progress = progress)
		
		Wp0.saveAsMAT(filename = self.DBM.getDefault('gisdatapath'),name= 'Wp0',progress = progress)
		if tempPath: Wp0.saveAsASC(filename = osp.join(tempPath,'Wp0.asc'),progress = progress)

		if progress: progress.setText(self.tr('Export CH'))
		CH = mask.copy(mask.nodata)
		self.rasterizeParam(CH,self.getLayerBySource(self.DBM.getDefault('qgis.subcatchmentslayer')),'CH',1.0,progress)
		self.rasterizeParam(CH,self.getLayerBySource(self.DBM.getDefault('qgis.landuseslayer')),'CH',1.0,progress)
		CH.saveAsMAT(filename = self.DBM.getDefault('gisdatapath'),name= 'CH',progress = progress)
		if tempPath: CH.saveAsASC(filename = osp.join(tempPath,'CH.asc'),progress = progress)
		
		if progress: progress.setText(self.tr('Export Alb'))
		Alb = mask.copy(mask.nodata)
		self.rasterizeParam(Alb,self.getLayerBySource(self.DBM.getDefault('qgis.subcatchmentslayer')),'ALB',1.0,progress)
		self.rasterizeParam(Alb,self.getLayerBySource(self.DBM.getDefault('qgis.landuseslayer')),'ALB',1.0,progress)
		Alb.saveAsMAT(filename = self.DBM.getDefault('gisdatapath'),name= 'Alb',progress = progress)
		if tempPath: Alb.saveAsASC(filename = osp.join(tempPath,'Alb.asc'),progress = progress)
		
		# rasterize aquifer variables ...
		if progress: progress.setText(self.tr('Export kf'))
		kf = mask.copy(mask.nodata)
		self.rasterizeParam(kf,self.getLayerBySource(self.DBM.getDefault('qgis.subcatchmentslayer')),'KF',1.0,progress)
		self.rasterizeParam(kf,self.getLayerBySource(self.DBM.getDefault('qgis.acquiferlayer')),'KF',1.0,progress)
		kf.saveAsMAT(filename = self.DBM.getDefault('gisdatapath'),name= 'Kf',progress = progress)
		if tempPath: kf.saveAsASC(filename = osp.join(tempPath,'kf.asc'),progress = progress)
		
		if progress: progress.setText(self.tr('Export Ma'))
		Ma = mask.copy(mask.nodata)
		self.rasterizeParam(Ma,self.getLayerBySource(self.DBM.getDefault('qgis.subcatchmentslayer')),'MA',1.0,progress)
		self.rasterizeParam(Ma,self.getLayerBySource(self.DBM.getDefault('qgis.acquiferlayer')),'MA',1.0,progress)
		Ma.saveAsMAT(filename = self.DBM.getDefault('gisdatapath'),name= 'Ma',progress = progress)
		if tempPath: Ma.saveAsASC(filename = osp.join(tempPath,'Ma.asc'),progress = progress)
		
		if progress: progress.setText(self.tr('Export Mf'))
		#Mf = mask.copy(mask.nodata)
		Mf = mask.copy(mask.nodata) # TODO: check why it is necessary
		self.rasterizeParam(Mf,self.getLayerBySource(self.DBM.getDefault('qgis.subcatchmentslayer')),'MF',1.0,progress)
		self.rasterizeParam(Mf,self.getLayerBySource(self.DBM.getDefault('qgis.acquiferlayer')),'MF',1.0,progress)
		Mf.saveAsMAT(filename = self.DBM.getDefault('gisdatapath'),name= 'Mf',progress = progress)
		if tempPath: Mf.saveAsASC(filename = osp.join(tempPath,'Mf.asc'),progress = progress)
		
		# set initial conditions
		Ws0  = mask.copy(0.0)
		Ws0.saveAsMAT(filename = self.DBM.getDefault('gisdatapath'),name= 'Ws0',progress = progress)
		if tempPath: Ws0.saveAsASC(filename = osp.join(tempPath,'Ws0.asc'),progress = progress)

		# new matrix
		cha_subflow  = mask.copy(1.0)
		cha_subflow.saveAsMAT(filename = self.DBM.getDefault('gisdatapath'),name= 'cha_subflow',progress = progress)
		if tempPath: cha_subflow.saveAsASC(filename = osp.join(tempPath,'cha_subflow.asc'),progress = progress)
		
		# export geometries ...
		
		if progress: progress.setText(self.tr('Export network geometries'))
		DGE = DrainageGeomExporter(progress)
				
		# TODO: add other geometry fields!!!
		DGE.setLinksLayer(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),\
									self.DBM.getDefault('qgis.networklayer.field.obj_id'),\
									self.DBM.getDefault('qgis.networklayer.field.s_shape'),\
									self.DBM.getDefault('qgis.networklayer.field.diam'),\
									self.DBM.getDefault('qgis.networklayer.field.dim1'),\
									self.DBM.getDefault('qgis.networklayer.field.dim2'),\
									self.DBM.getDefault('qgis.networklayer.field.dim3'),\
									self.DBM.getDefault('qgis.networklayer.field.dim4'),\
									self.DBM.getDefault('qgis.networklayer.field.elev_start'),\
									self.DBM.getDefault('qgis.networklayer.field.elev_end'),\
									self.DBM.getDefault('qgis.networklayer.field.node_start'),\
									self.DBM.getDefault('qgis.networklayer.field.node_end'),\
									self.DBM.getDefault('qgis.networklayer.field.length'),
									self.DBM.getDefault('qgis.networklayer.field.mann'),
									self.DBM.getDefault('qgis.networklayer.field.table'))
		
		DGE.setNodesLayer(self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),\
									self.DBM.getDefault('qgis.nodeslayer.field.obj_id'),\
									self.DBM.getDefault('qgis.nodeslayer.field.elev_bot'),\
									self.DBM.getDefault('qgis.nodeslayer.field.elev_top'),\
									self.DBM.getDefault('qgis.nodeslayer.field.area'),\
									self.DBM.getDefault('qgis.nodeslayer.field.table')
									)

		DGE.setGrid(zr)
		
		DGE.rowIdLookUpTables() # update lookup table id row index
		
		#DGE.setDBM(self.DBM)
		
		#DGE.resetFeatureId() # sometimes feature id() differes from counter
		
		DGE.linksToMat(matFileName = self.DBM.getDefault('gisdatapath'))
		DGE.nodesToMat(matFileName = self.DBM.getDefault('gisdatapath'))
		
		# init empty array
		if progress:
			progress.setText(self.tr('Export empty variables!'))
			progress.setPercentage(0)
		#emptyArr = np.array([0.0]) #check here!!!
		emptyArr = []
		labList = ['bfi', 'casse', 'fsand', 'gw_ne', 'href', 'hsoil', 'Kc_FAO_path', 'ksmax', 'ksmin', 'Kz_dz', 'reserv', 'soiltype', 'sorg', 'ss', 'Zb', 'zw']
		
		for i,lab in enumerate(labList):
			dataToMat(filename = self.DBM.getDefault('gisdatapath'),data = emptyArr,name= lab,progress = progress,tr = self.tr)
			if progress: progress.setPercentage(100.0*float(i)/float(len(labList)))
			
		if progress: 
			progress.setText(self.tr('Exportation concluded!'))
			progress.setPercentage(100)
				
	def rasterizeParam(self,grid,layer,field,multiply,progress,values=1):
		RZ = Rasterizer(grid,progress)
		RZ.polyToRaster(layer,field,multiply,values)
		
	def runMobidic(self,progress= None):
		import sys
		from subprocess import PIPE, Popen
		from threading  import Thread
		import os

		try:
			from Queue import Queue, Empty
		except ImportError:
			from queue import Queue, Empty  # python 3.x
		
		def enqueue_output(out, err, queue):
			for line in iter(out.readline, b''):
				queue.put(line)
			out.close()
			
			for e in iter(err.readline, b''):
				queue.put(e)
			err.close()
			
		# check if there are simulation file
		folderName = self.DBM.getDefault('statespath')
		root = ''
		fileList = glob.glob(folderName+'/'+root+'*.mat')
		numFile = len(fileList)
		
		if numFile>0:
			progress.setText(self.tr('Old simulation file will be removed'))
			for i,f in enumerate(fileList):
				os.remove(f)
				progress.setPercentage(100*float(i)/numFile)
		
		progress.setPercentage(0.0)
				
		s = QSettings()
		execPath = s.value('SMARTGREEN/pathToMOBIDIC', '')
		MCRpath = s.value('SMARTGREEN/pathToMATLAB', '')# MCRpath = 'C:/Program Files/MATLAB/MATLAB Compiler Runtime/v714/runtime/win64'
		
		arg1 = 'GOLOCAL'
		arg2 = 'MOBIDIC'
		arg3 = self.DBM.getDefault('mobidicproject')
		#print execPath,arg1,arg2
		progress.setText('%s %s %s %s'%(execPath,arg1,arg2,arg3))
		
		toks = os.environ['PATH'].split(';')	
		if not MCRpath in toks:
			os.environ['PATH'] = os.environ['PATH'] +';' + MCRpath
			
		#progress.setText('%s'%os.environ['PATH'])
		proc = Popen(([execPath,arg1,arg2,arg3]), shell=True, stdout=PIPE, stderr=PIPE) 
		
		q = Queue()
		t = Thread(target=enqueue_output, args=(proc.stdout, proc.stderr, q))
		t.daemon = True # thread dies with the program
		t.start()

		while t.isAlive():
			try:  line = q.get_nowait() # or q.get(timeout=.1)
			except Empty:
				# do nothing
				pass
			else: # got line
				# ... do something with line
				try:
					perc = float(line.strip())
					progress.setPercentage(100*perc)
				except ValueError:
					# TODO: check stream binary?
					progress.setText(str(line.strip()))
					#pass

		progress.setText(self.tr('Process concluded'))
	
	def createSubCatchments(self):
		# get network
		netLayer = self.getLayerBySource(self.DBM.getDefault('qgis.networklayer'))
		scLayer = self.getLayerBySource(self.DBM.getDefault('qgis.subcatchmentslayer'))
		scLayer.startEditing()
		# get outlet link
		from .tools.check_data import CheckData
		
		checker = CheckData(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),None)
		outLinkId = checker.getExtremeLinks(direction = 1)
		#print 'outLinkId:',outLinkId
		outLink = QgsFeature()
		netLayer.getFeatures(QgsFeatureRequest().setFilterFid(outLinkId[0])).nextFeature(outLink)
		
		# get the list of nearest links
		sortedLinkId = checker.getSortedLinks(startLink = outLink,direction=-1)
		#print 'sortedLinkId:',sortedLinkId
		
		# make a filled buffer of the neares links
		buffering(progress= None, writer = scLayer.dataProvider(), distance = self.DBM.getDefault('qgis.bufferdistance'),\
						field = None, useField =False, layer=netLayer, dissolve = True, segments= self.DBM.getDefault('qgis.buffersegments'),
						fillHoles = True,idList = sortedLinkId)
						
		# update attributes with defaults
		
		for feat in scLayer.getFeatures():
			scLayer.changeAttributeValue(feat.id(), scLayer.fields().indexFromName(self.DBM.getDefault('qgis.subcatchmentslayer.field.obj_id')), '%s%s'%('S',feat.id()))
			scLayer.changeAttributeValue(feat.id(), scLayer.fields().indexFromName(self.DBM.getDefault('qgis.subcatchmentslayer.field.wg0')), self.DBM.getDefault('param_default.Wg0'))
			scLayer.changeAttributeValue(feat.id(), scLayer.fields().indexFromName(self.DBM.getDefault('qgis.subcatchmentslayer.field.wc0')), self.DBM.getDefault('param_default.Wc0'))
			scLayer.changeAttributeValue(feat.id(), scLayer.fields().indexFromName(self.DBM.getDefault('qgis.subcatchmentslayer.field.wp0')), self.DBM.getDefault('param_default.Wp0'))
			scLayer.changeAttributeValue(feat.id(), scLayer.fields().indexFromName(self.DBM.getDefault('qgis.subcatchmentslayer.field.ks')), self.DBM.getDefault('param_default.ks'))
			scLayer.changeAttributeValue(feat.id(), scLayer.fields().indexFromName(self.DBM.getDefault('qgis.subcatchmentslayer.field.ch')), self.DBM.getDefault('param_default.CH'))
			scLayer.changeAttributeValue(feat.id(), scLayer.fields().indexFromName(self.DBM.getDefault('qgis.subcatchmentslayer.field.alb')), self.DBM.getDefault('param_default.Alb'))
			scLayer.changeAttributeValue(feat.id(), scLayer.fields().indexFromName(self.DBM.getDefault('qgis.subcatchmentslayer.field.kf')), self.DBM.getDefault('param_default.kf'))
			scLayer.changeAttributeValue(feat.id(), scLayer.fields().indexFromName(self.DBM.getDefault('qgis.subcatchmentslayer.field.ma')), 0)
			scLayer.changeAttributeValue(feat.id(), scLayer.fields().indexFromName(self.DBM.getDefault('qgis.subcatchmentslayer.field.mf')), 0)
			
		# commit to stop editing the layer
		scLayer.commitChanges()
		
		# update layer's extent when new features have been added
		# because change of extent in provider is not propagated to the layer
		scLayer.updateExtents()

	def getMaximumExtent(self):
		extent = QgsRectangle()
		extent.setMinimal()
		
		paramList = ['qgis.networklayer','qgis.nodeslayer','qgis.lidlayer','qgis.weatherstationslayer','qgis.subcatchmentslayer']
		
		for param in paramList:
			lyr = self.getLayerBySource(self.DBM.getDefault(param))
			if lyr.featureCount()>0:
				extent.combineExtentWith( lyr.extent() )
		
		return extent
	
	def manageDB(self):
		actionList = [self.tr('Delete'),self.tr('Reload'), self.tr('Import')]
		tableList = self.DBM.getTablesList()
		groupIndex = None
		mygroup = None
		from forms.manage_db_table_dialog import ManageDbTableDialog
		
		dlg = ManageDbTableDialog(self.SGsettings, self.tr,tableList, actionList) 
		# show the dialog
		dlg.show()
		result = dlg.exec_() 
		# See if OK was pressed
		if result == 1: 
			res = dlg.getParameterValue()
			tableNames = res[1]
			actionName = res[2]
			if actionName == actionList[2]:
				# ask for source db
				fromDB = QFileDialog.getOpenFileName(None, self.tr('Select source database'), '', 'sqlite(*.sqlite)')
				if not fromDB:
					return
				
			#print 'tableNames:',tableNames
			for tableName in tableNames:
				tableSource = self.DBM.getTableSource(tableName)
				tableLay = self.getLayerBySource(tableSource)
				
				if actionName == actionList[0]:
					# last control...
					reply = QMessageBox.question(self.iface.mainWindow(), 'SMARTGREEN',
													self.tr("Would you like to definitely remove table '%s'?"%tableName),
													QMessageBox.Yes | QMessageBox.No)

					if reply == QMessageBox.Yes:
						# remove table from TOC
						if tableLay is not None:
							QgsProject.instance().removeMapLayers( [tableLay.id()] )
						# remove table from DB
						# TODO: drop multiple table in one shot
						self.DBM.removeTable(tableName)
				if actionName == actionList[1]:
					# reload table
					# remove table from TOC
					if tableLay is not None:
						layNode = self.getNode(tableLay.id())
						if layNode is not None:
							groupIndex,mygroup = self.getGroupIndex(layNode.parent().name())
							QgsProject.instance().removeMapLayers( [tableLay.id()] )
					
					# load into qgis
					tableLay = self.DBM.getTableAsLayer(tableName)
					#Add the layer to the QGIS Map Layer Registry
					QgsProject.instance().addMapLayer(tableLay, False)
					#groupIndex,mygroup = self.getGroupIndex('Time series')
					#print type(tableLay)
					#Insert the layer above the group
					if mygroup is not None: mygroup.insertChildNode(groupIndex, QgsLayerTreeLayer(tableLay))
				if actionName == actionList[2]:
					# import table
					self.DBM.importFromDB(fromDB,tableName)
					if tableLay is not None:
						# to update layer extents
						self.addRemoveDummyFeature(tableLay)

	def addRemoveDummyFeature(self, lay):
		lay.startEditing()
		# add feature
		newFeat = QgsFeature(lay.fields())

		for feat in lay.getFeatures():
			newFeat.setGeometry(feat.geometry())
			flag = lay.addFeatures([newFeat],True)
			if not flag: self.smDock.setInfo('In addRemoveDummyFeature, cannot add feature', error = True)
			break
			
		lay.commitChanges()
		lay.updateExtents()
		lay.startEditing()
		# delete last feature
		lay.deleteSelectedFeatures()
		lay.commitChanges()
		lay.updateExtents()
		
	def addVectorLayerToTOC(self,filename,name,group,driver = 'ogr', style = None, formUi = None):
		#Get the layer tree object
		root = QgsProject.instance().layerTreeRoot()
		#Find the desired group by name
		mygroup = root.findGroup(group)
		if mygroup is None:
			# create a new group
			root.addGroup(group)
			mygroup = root.findGroup(group)
		
		#Get the group index
		groupIndex = len(mygroup.children())
		#Create the new layer object
		mylayer = QgsVectorLayer(filename, name, driver)
		if style is not None:
			mylayer.loadNamedStyle(os.path.join(self.plugin_dir,'styles',style+'.qml'))
			
		# add custom ui
		self.setFormUI(mylayer,formUi)
			
		#Add the layer to the QGIS Map Layer Registry
		QgsProject.instance().addMapLayer(mylayer, False)
		#Insert the layer above the group
		mygroup.insertChildNode(groupIndex, QgsLayerTreeLayer(mylayer))
		return mylayer
		
	def setFormUI(self,mylayer,formUi):
		if formUi is not None:
			# add custom ui and python function		
			EFC = QgsEditFormConfig()
			EFC.setUiForm(os.path.join(self.plugin_dir,'layerforms', formUi + '.ui'))
			EFC.setInitCodeSource(QgsEditFormConfig.PythonInitCodeSource.CodeSourceFile)
			EFC.setInitFilePath(os.path.join(self.plugin_dir,'layerforms',formUi + '.py'))
			EFC.setInitFunction('formOpen')
			mylayer.setEditFormConfig(EFC)
		
	def addTableToTOC(self,filename,name,group,driver = 'delimitedtext', sep = ';',formUi = None):
		groupIndex,mygroup = self.getGroupIndex(group)
		# edit source file
		uri='file:///'+filename+'?delimiter='+sep
		#Create the new layer object
		mylayer = QgsVectorLayer(uri, name, driver)
		# add custom ui
		if formUi is not None:
			# add custom ui and python function
			EFC = QgsEditFormConfig()
			EFC.setUiForm(os.path.join(self.plugin_dir, 'layerforms', formUi + '.ui'))
			EFC.setInitCodeSource(QgsEditFormConfig.PythonInitCodeSource.CodeSourceFile)
			EFC.setInitFilePath(os.path.join(self.plugin_dir, 'layerforms', formUi + '.py'))
			EFC.setInitFunction('formOpen')
			mylayer.setEditFormConfig(EFC)

		#Add the layer to the QGIS Map Layer Registry
		QgsProject.instance().addMapLayer(mylayer, False)
		#Insert the layer above the group
		mygroup.insertChildNode(groupIndex, QgsLayerTreeLayer(mylayer))
		return mylayer
		
	def getGroupIndex(self,group):
		#Get the layer tree object
		root = QgsProject.instance().layerTreeRoot()
		#Find the desired group by name
		mygroup = root.findGroup(group)
		if mygroup is None:
			# create a new group
			root.addGroup(group)
			mygroup = root.findGroup(group)
		
		#Get the group index
		groupIndex = len(mygroup.children())
		return groupIndex,mygroup
		
	def getNode(self,layId):
		#Get the layer tree object
		root = QgsProject.instance().layerTreeRoot()
		return root.findLayer(layId)
		
	def selectUpstream(self):
		# make our clickTool the tool that we'll use for now
		self.upstream_tree_tool.setActive()

	def selectDownstream(self):
		# make our clickTool the tool that we'll use for now
		self.downstream_tree_tool.setActive()
		
	def rasterIdentify(self):
		# make our clickTool the tool that we'll use for now
		self.raster_identify.setActive()
		
	def vectorIdentify(self):
		# make our clickTool the tool that we'll use for now
		self.vector_identify.setActive()
		
	def plotResults(self):
		# make our clickTool the tool that we'll use for now
		self.plot_results.setActive()
		
		
	def altimetricChart(self):
		WIS = walkInSelection(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')))
		x, y,d,Hb,Ht,dims,linkId,nodeId = WIS.getData()
		#~ print 'x:',x
		#~ print 'y:',y
		#~ print 'd:',d
		#~ print 'Hb:',Hb
		#~ print 'linkId:',linkId
		if len(x)>0:
			try:
				from forms.chart_dialog import ChartDialog
				dlg = ChartDialog(title=self.tr('Elevation profile'),secondAxis= False)
				nOfLinks = len(x)
				j = 0
				for i in range(0,nOfLinks,2):
					#~ xi = [x[i],x[i+1]]
					#~ yi = [y[i],y[i+1]]
					#~ dlg.addLinePlot(xi,yi, name = self.tr('line %s'%((i/2)+1)))
					dlg.drawConduit(x[i],y[i],x[i+1],y[i+1],d[i])
					#dlg.addInfVertical(x=x[i+1])
					xm = 0.5*(x[i]+x[i+1])
					ym = 0.5*(y[i]+y[i+1])+0.5*d[i]
					dlg.addText(linkId[j],xm,ym)
					j+=1

				x = [0]+x
				# add nodes:
				for i,hb in enumerate(Hb):
					#print 'add manhole (%s-%s-%s) at %s'%(Hb[i],Ht[i],dims[i],x[i*2])
					dlg.drawManhole(Hb[i],Ht[i],x[i*2],dims[i])
					# add label
					dlg.addText(nodeId[i],x[i*2],Ht[i],90.0)

				#dlg.addLinePlot(x,y, name = self.tr('profile'))
				dlg.setAxes(xlabs = None, ylabs = None, xTitle = self.tr('distance'), yTitle = self.tr('elevation'), mainTitle = self.tr('Elevation profile'))

				# show the dialog
				dlg.show()
			except Exception as e:
				self.showCriticalMessageBox(text=self.tr('Cannot show elevation profile'),
											infoText=self.tr('Maybe a problem with elevation values or dimensions. Please, check missing data first!'),
											detailText=str(e))

		else:
			self.showCriticalMessageBox(text = self.tr('Cannot show elevation profile'),
										infoText=self.tr('Not enought selected links!'),
										detailText=self.tr('Please select at least one link.'))
		
		
	def getLayerBySource(self,source):
		layer=None
		source = source.replace('\\','/')
		#print 'source:',source
		for lyr in QgsProject.instance().mapLayers().values():
			#print '-->',lyr.source()
			if lyr.source().replace('\\','/') == source:
				layer = lyr
				break
		
		if layer is None:
			# if layer is None maybe is the wrong path, try with the path of the qgis project
			# get qgis project full name
			prjFile = QgsProject.instance().fileName()
			rootName = os.path.basename(prjFile)
			rootName = rootName[:-4]
			rootPath = os.path.dirname(prjFile)
			db_filename = os.path.join(rootPath,rootName+'_DATA'+'.sqlite')
			# split source by '|'
			# new path should look like this: C:/pathto/prjname_DATA.sqlite|layername=links
			toks = source.split('|')
			if len(toks)==2:
				newSource = db_filename+'|'+toks[1]
			else:
				# source is exactly the name of the layer
				newSource = db_filename+'|layername='+source
				
			#print 'newSource:',newSource
			newSource = newSource.replace('\\','/')
			for lyr in QgsProject.instance().mapLayers().values():
				#print '-->',lyr.source()
				if lyr.source().replace('\\','/') == newSource:
					layer = lyr
					break

		return layer
		
	def showMessage(self):
		self.showCriticalMessageBox(self.tr("Project was loaded!"),
													self.tr("good ..."),
													self.tr("very good!"))
	
	def loadFromProject(self):
		proj = QgsProject.instance()
		#print 'in <loadFromProject> proj:',proj
		self.SGsettings.readFromProject(proj)
		if self.settings['qgis.dblite'][0]!='':
			#print 'in __init__():',self.settings['qgis.dblite'][0]
			dbPath = self.settings['qgis.dblite'][0]
			#print "dbPath(prj):",dbPath
			# clear relative path
			wd = os.getcwd()
			os.chdir(self.getProjPath())
			dbPath = abspath(dbPath)
			#print "dbPath(abs):",dbPath
			os.chdir(wd)
			
			self.DBM = SQLiteDriver(dbPath,progress = self.smDock)
			#self.DBM = SQLiteDriver(self.settings['qgis.dblite'][0],self.smDock)
			self.plot_results.DBM = self.DBM
		
	def setJoin(self):
		from forms.join_dialog import JoinDialog
		dlg = JoinDialog(self.SGsettings) 
		# show the dialog
		dlg.show()
		result = dlg.exec_() 
		# See if OK was pressed
		if result == 1: 
			res = dlg.getParameterValue()
			res = self.joinShpTable(layer = self.getLayerBySource(res[0]), layerFld = res[1],\
										table = self.getLayerBySource(res[2]), tableFld = res[3], FldToBeShown = res[4])
										
	
	def findDuplicates(self,progress=None):
		from tools.check_data import CheckData
		
		checker = CheckData(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),
							self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),
							progress = progress)
		checker.findDuplicates(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')))
		checker.findDuplicates(self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')))
	
	def checkNodesNumber(self,progress = None):
		from tools.check_data import CheckData
		
		checker = CheckData(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),
							self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),
							progress = progress)
		checker.checkNumberNodes()
										
	def checkNodesId(self,progress = None):
		from tools.check_data import CheckData
		
		checker = CheckData(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),
							progress = progress)
		checker.checkId(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),self.DBM.getDefault('qgis.networklayer.field.obj_id'),'L')
		checker.checkId(self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),self.DBM.getDefault('qgis.nodeslayer.field.obj_id'),'N')
	
	def checkLinkNodes(self,progress = None):
		from tools.check_data import CheckData
		
		checker = CheckData(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),
							self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),
							progress = progress)
		checker.checkLinkNodesConnection(self.DBM.getDefault('qgis.networklayer.field.node_start'),
															self.DBM.getDefault('qgis.networklayer.field.node_end'),
															self.DBM.getDefault('qgis.nodeslayer.field.obj_id'))
															
	def removeDetachedNode(self,progress = None):
		from tools.check_data import CheckData
		
		checker = CheckData(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),
							self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),
							progress = progress)
		checker.removeDetachedNode()
		
	def fixLinkElev(self,progress = None):
		from tools.check_data import CheckData
		checker = CheckData(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),
							self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),
							progress = progress)
						
		unresolvedList =checker.fixLinkElevs(startElevFld = self.DBM.getDefault('qgis.networklayer.field.elev_start'),
														endElevFld = self.DBM.getDefault('qgis.networklayer.field.elev_end'),
														startNodeFld = self.DBM.getDefault('qgis.networklayer.field.node_start'),
														endNodeFld = self.DBM.getDefault('qgis.networklayer.field.node_end'),
														nodeElevFld = self.DBM.getDefault('qgis.nodeslayer.field.elev_bot'),
														lengthFld = self.DBM.getDefault('qgis.networklayer.field.length'),
														slope = self.DBM.getDefault('param_default.conduit_slope'))
														
		
		
		for unresolved in unresolvedList:
			self.smDock.setInfo('Feature %s cannot be automatically fixed'%unresolved, error = True)
		
		# select features
		self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')).select(unresolvedList)
	
	def checkTopElevNode(self,progress = None):
		from tools.check_data import CheckData
		
		checker = CheckData(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),
							self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),
							progress = progress)
		# check top node elevation
		checker.checkElevTop(elevFld = self.DBM.getDefault('qgis.nodeslayer.field.elev_top'), elevOffset = self.DBM.getDefault('param_default.yfull_urban') )
		
	def fixAttributes(self,progress = None):
		from tools.check_data import CheckData
		
		checker = CheckData(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),
							self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),
							progress = progress)
		
		# replace NULL values from links and nodes attributes
		checker.replaceNull(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),self.DBM.getDefault('qgis.networklayer.field.s_shape'), self.DBM.getDefault('param_default.shape_urban'))
		checker.replaceNull(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),self.DBM.getDefault('qgis.networklayer.field.mann'), self.DBM.getDefault('param_default.mann_urban'))
		checker.replaceNull(self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),self.DBM.getDefault('qgis.nodeslayer.field.area'), self.DBM.getDefault('param_default.nodearea_urban'))
		
	def fixBasinAttributes(self,progress = None):
		from tools.check_data import CheckData
		
		checker = CheckData(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),
							self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),
							self.getLayerBySource(self.DBM.getDefault('qgis.lidlayer')),
							progress = progress)
		
		#Soils
		checker.replaceNull(self.getLayerBySource(self.DBM.getDefault('qgis.soilslayer')),self.DBM.getDefault('qgis.soilslayer.field.ks'), self.DBM.getDefault('param_default.ks'))
		checker.replaceNull(self.getLayerBySource(self.DBM.getDefault('qgis.soilslayer')),self.DBM.getDefault('qgis.soilslayer.field.wg0'), self.DBM.getDefault('param_default.Wg0'))
		checker.replaceNull(self.getLayerBySource(self.DBM.getDefault('qgis.soilslayer')),self.DBM.getDefault('qgis.soilslayer.field.wc0'), self.DBM.getDefault('param_default.Wc0'))
		
		#Landuses
		checker.replaceNull(self.getLayerBySource(self.DBM.getDefault('qgis.landuseslayer')),self.DBM.getDefault('qgis.landuseslayer.field.wp0'), self.DBM.getDefault('param_default.Wp0'))
		checker.replaceNull(self.getLayerBySource(self.DBM.getDefault('qgis.landuseslayer')),self.DBM.getDefault('qgis.landuseslayer.field.ch'), self.DBM.getDefault('param_default.CH'))
		checker.replaceNull(self.getLayerBySource(self.DBM.getDefault('qgis.landuseslayer')),self.DBM.getDefault('qgis.landuseslayer.field.alb'), self.DBM.getDefault('param_default.Alb'))
		
		#Acquifer
		checker.replaceNull(self.getLayerBySource(self.DBM.getDefault('qgis.acquiferlayer')),self.DBM.getDefault('qgis.acquiferlayer.field.kf'), self.DBM.getDefault('param_default.kf'))
		checker.replaceNull(self.getLayerBySource(self.DBM.getDefault('qgis.acquiferlayer')),self.DBM.getDefault('qgis.acquiferlayer.field.ma'), 1)
		checker.replaceNull(self.getLayerBySource(self.DBM.getDefault('qgis.acquiferlayer')),self.DBM.getDefault('qgis.acquiferlayer.field.mf'), 1)
		
	#~ def fixBasinAttributes(self,progress = None):
		#~ from tools.check_data import CheckData
		
		#~ checker = CheckData(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),self.getLayerBySource(self.DBM.getDefault('qgis.lidlayer')),progress)
		
		# update node_to
		
		# update other attribute

	def checkDim(self,progress = None):
		from tools.check_data import CheckData
		
		checker = CheckData(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),
							self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),
							progress = progress)
		
		# replace NULL values from links and nodes attributes
		checker.checkLinkDiam(self.DBM.getDefault('qgis.networklayer.field.diam'),self.DBM.getDefault('qgis.networklayer.field.dim1'),
											self.DBM.getDefault('qgis.networklayer.field.s_shape'),
											self.DBM.getDefault('qgis.networklayer.field.node_start'), self.DBM.getDefault('qgis.networklayer.field.node_end'),
											self.DBM.getDefault('param_default.min_diam'),self.DBM.getDefault('param_default.max_diam'))
		
	def checkElevations(self,progress = None):
		from tools.check_data import CheckData
		
		checker = CheckData(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),
							self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),
							progress = progress)
		checker.checkElevation()
		
	def fixBotElevations(self,progress = None):
		from tools.check_data import CheckData
		
		checker = CheckData(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),
							self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),
							progress = progress)
		checker.fixElevBot()

	def fixNodesElevations(self,progress = None):
		from tools.check_data import CheckData
		
		checker = CheckData(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),
							self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),
							progress = progress)
		# replace NULL top elevation with something near to the truth
		checker.fillEmptyElevation(elevField = self.DBM.getDefault('qgis.nodeslayer.field.elev_top'),\
												idPtField = self.DBM.getDefault('qgis.nodeslayer.field.obj_id'),\
												fromPtField = self.DBM.getDefault('qgis.networklayer.field.node_start'),\
												toPtField = self.DBM.getDefault('qgis.networklayer.field.node_end'))
												
		#print '====== CHECK BOTTOM ======'
												
		# replace NULL bottom elevation with something near to the truth										
		checker.fillEmptyElevation(elevField = self.DBM.getDefault('qgis.nodeslayer.field.elev_bot'),\
												idPtField = self.DBM.getDefault('qgis.nodeslayer.field.obj_id'),\
												fromPtField = self.DBM.getDefault('qgis.networklayer.field.node_start'),\
												toPtField = self.DBM.getDefault('qgis.networklayer.field.node_end'))

	def fixAll(self):
		reply = QMessageBox.question(self.iface.mainWindow(), 'SMARTGREEN',
													self.tr('Edit will be automatically saved. Would you like to continue?'),
													QMessageBox.Yes | QMessageBox.No)

		if reply == QMessageBox.Yes:
			self.runAsThread(self.fixAllTH)
			

	def fixAllTH(self,progress = None):
		from tools.check_data import CheckData
		if progress is None:
			progress = MyProgress()
			
		checker = CheckData(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),
							self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),
							progress = progress)
		
		# add Check data Menu
		progress.setInfo('Find duplicates', error = False)
		progress.setPercentage(10)
		checker.findDuplicates(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),fix= True)
		checker.findDuplicates(self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),fix= True)
				
		progress.setInfo('Check node numbers', error = False)
		progress.setPercentage(20)
		checker.checkNumberNodes(fix = True)
		
		progress.setInfo('Check link and node id', error = False)
		progress.setPercentage(30)
		checker.checkId(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),self.DBM.getDefault('qgis.networklayer.field.obj_id'),'L',True)
		checker.checkId(self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),self.DBM.getDefault('qgis.nodeslayer.field.obj_id'),'N',True)
		
		progress.setInfo('Check links nodes correspondence', error = False)
		progress.setPercentage(40)
		checker.checkLinkNodesConnection(self.DBM.getDefault('qgis.networklayer.field.node_start'),
															self.DBM.getDefault('qgis.networklayer.field.node_end'),
															self.DBM.getDefault('qgis.nodeslayer.field.obj_id'),
															True)
		
		progress.setInfo('Fix link elevations', error = False)
		
		
		progress.setInfo('Check detached node', error = False)
		progress.setPercentage(45)
		checker.removeDetachedNode(True)
		progress.setPercentage(50)
		
		flag=-1
		prevLen = 0
		while flag!=0:
			unresolvedList =checker.fixLinkElevs(startElevFld = self.DBM.getDefault('qgis.networklayer.field.elev_start'),
														endElevFld = self.DBM.getDefault('qgis.networklayer.field.elev_end'),
														startNodeFld = self.DBM.getDefault('qgis.networklayer.field.node_start'),
														endNodeFld = self.DBM.getDefault('qgis.networklayer.field.node_end'),
														nodeElevFld = self.DBM.getDefault('qgis.nodeslayer.field.elev_bot'),
														lengthFld = self.DBM.getDefault('qgis.networklayer.field.length'),
														slope = self.DBM.getDefault('param_default.conduit_slope'),
														fix=True)
												
			flag = prevLen-len(unresolvedList)
			prevLen=len(unresolvedList)
		
		for unresolved in unresolvedList:
			request = QgsFeatureRequest().setFilterFid(unresolved)
			feature = next(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')).getFeatures(request))
			progress.setInfo('Link %s  cannot be automatically fixed'%(feature['OBJ_ID']), error = True)
			
		progress.setInfo('Fix bottom node elevations', error = False)
		progress.setPercentage(60)
		checker.fixElevBot(fix = True)
		
		progress.setInfo('Fix all other attributes', error = False)
		progress.setPercentage(70)
		checker.replaceNull(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),self.DBM.getDefault('qgis.networklayer.field.s_shape'), self.DBM.getDefault('param_default.shape_urban'),True)
		checker.replaceNull(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),self.DBM.getDefault('qgis.networklayer.field.mann'), self.DBM.getDefault('param_default.mann_urban'),True)
		checker.replaceNull(self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),self.DBM.getDefault('qgis.nodeslayer.field.area'), self.DBM.getDefault('param_default.nodearea_urban'),True)
		
		progress.setInfo('Check conduit diameters', error = False)
		progress.setPercentage(80)
		checker.checkLinkDiam(self.DBM.getDefault('qgis.networklayer.field.diam'),self.DBM.getDefault('qgis.networklayer.field.dim1'),
											self.DBM.getDefault('qgis.networklayer.field.s_shape'),
											self.DBM.getDefault('qgis.networklayer.field.node_start'), self.DBM.getDefault('qgis.networklayer.field.node_end'),
											self.DBM.getDefault('param_default.min_diam'),self.DBM.getDefault('param_default.max_diam'),
											True)

		
		progress.setInfo('Fix Top node elevations', error = False)
		progress.setPercentage(90)
		checker.checkElevTop(elevFld = self.DBM.getDefault('qgis.nodeslayer.field.elev_top'), elevOffset = self.DBM.getDefault('param_default.yfull_urban'),fix =True)
		
	def setLanduseJoin(self):
		res = self.joinShpTable(layer = self.getLayerBySource(self.DBM.getDefault('qgis.landuseslayer')), layerFld = self.DBM.getDefault('qgis.landuseslayer.field.landuse_id'),\
										table = self.getLayerBySource(self.DBM.getDefault('qgis.table.landuses')), tableFld = 'id')
		
		if not res:
			self.smDock.setInfo('In setLanduseJoin, cannot make join', error = True)
			

	def importCSVTable(self):
		from forms.import_csv_dialog import ImportCsvDialog
		dlg = ImportCsvDialog(self.SGsettings, self.tr) 
		# show the dialog
		dlg.show()
		result = dlg.exec_() 
		# See if OK was pressed
		if result == 1:
			src = QFileDialog.getOpenFileName(None, self.tr('Open file'), None,self.tr('CSV files (*.csv)'))
			newTablename = dlg.getParameterValue()
			self.DBM.importCSV(src,newTablename,columnTypes = ['TEXT','TEXT','REAL'])
			
	def compareLayerSource(self,path1,path2):
		path1 = path1.replace('\\','/')
		path2 = path2.replace('\\','/')
		newPath1=''
		newPath2=''
		res = False
		if path1==path2:
			res = True
		
		if res == False:
			# try adding to path2 the path to the db
			#C:/pathto/test_DATA.sqlite|layername=LIDs
			newPath2 = self.settings['qgis.dblite'][0] +'|layername='+path2
			newPath2 = newPath2.replace('\\','/')
			
			if path1==newPath2:
				res = True
			
		if res == False:
			# try comparing only the last part of the path (back compatibility)
			# split path1 and extract the layer name
			toks =path1.split('|layername=')
			if len(toks)==2:
				newPath1 = toks[1]
				if newPath1==path2:
					res = True

		print('path1:', path1)
		print('newPath1:', newPath1)
		print('path2:', path2)
		print('newPath2:', newPath2)

		return res
			
			
	def getTableList(self,root = ''):
		value = ['','t1','t2','t3']
		return value
		
	def getParamFromWMS(self):
		wmsLayerList = ['A1-dati','N-dati','Alpha-dati','K-dati','eps-dati']
		fieldList = ['A1','N','ALP','KAP','EPS']
		start = "value_0 = '"
		end = "'\n"
		
		# get layer
		vLayer = self.getLayerBySource(self.DBM.getDefault('qgis.weatherstationslayer'))
		
		vLayer.startEditing()
		
		for i,wmsLayer in enumerate(wmsLayerList):
			self.smDock.setInfo('Try to connect to %s'%wmsLayer, error = False)
			urlWithParams = "contextualWMSLegend=0&crs=EPSG:32632&dpiMode=7&featureCount=10&format=image/png&layers=a1i&layers="
			urlWithParams += wmsLayer
			urlWithParams += "&styles=&styles=&url=http://idro.arpalombardia.it/cgi-bin/mapserv?map%3D/var/www/idro/pmapper-4.0/config/wms/pmapper_wms.map"
			
			# make a raster layer
			rLayer = QgsRasterLayer(urlWithParams, wmsLayer, 'wms')
			if rLayer.isValid():
				# loop in vlayer and write attribute
				for selectedFeat in vLayer.selectedFeatures():
					#print 'stats for ',selectedFeat.id(),qgis.analysis.cellInfoForBBox(rasterBBox,featureBBox,cellSizeX,cellSizeY)
					point = selectedFeat.geometry().centroid().asPoint()
					ident=rLayer.dataProvider().identify(point,QgsRaster.IdentifyFormatText)
					res = ident.results()
					#print res
					if len(res)>0:
						val = res[res.keys()[0]]
						val = (val.split(start))[1].split(end)[0]
						print('val:', val)
						print('field name:', fieldList[i])
						# save val to vLayer
						fldIdx = selectedFeat.fields().fields().indexFromName(fieldList[i])
						vLayer.changeAttributeValue(selectedFeat.id(),fldIdx,val,True)
			else:
				self.smDock.setInfo('Connection error to %s'%urlWithParams, error = True)
		
		# stop editing
		# commit to stop editing the layer
		#vLayer.commitChanges()
		
	def importResults(self, progress = None):
		folderName = self.DBM.getDefault('statespath')
		root = 'state_'
		MI = ImportFromMat(progress)
		varList = [['Hnode','H'],['Hnode','Qin'],['Hnode','Qout'],['Hnode','Qoverflow'],\
						['Qret','Qout'],['Qret','H1'],['Qret','H2'],['Qret','y1'],['Qret','y2'],['Qret','A1'],['Qret','A2'],\
						['Qret','Amid'],['Qret','Aaverage'],['Qret','Vaverage'],['Qret','Raverage'],['Qret','Froude'],\
						['Qret','Qdat'],['Qret','Qfinal'],['Qret','Alast'],\
						['GIs_route','reserv_Vol'],['GIs_route','reserv_h'],['GIs_route','reserv_Qin'],['GIs_route','reserv_Qrete'],\
						['GIs_route','reserv_Qinf'],['GIs_route','reserv_Qover'],['GIs_route','soil_Q2node'],\
						['GIs_route','soil_relSATgrav'],['GIs_route','soil_relSATcap'],['GIs_route','soil_relSAT']]
		data = MI.importFromFolder(folderName, root, varList)
		for i,var in enumerate(varList):
			adata = np.array(data[i]).T
			self.DBM.setArray(varName = '-'.join(var),nArray = adata, tableName='results')
			
		
		# load into qgis
		mylayer = self.DBM.getTableAsLayer(self.tr('results'))
		if mylayer is not None:
			if self.getLayerBySource(mylayer.source()) is None:
				# update db settings
				self.DBM.setDefault('qgis.table.'+'results',mylayer.source())
				
	def viewResults(self):
		from forms.results_mainwindow import ResultsMainwindow
		self.dlg = ResultsMainwindow(self.plugin_dir,self.DBM)
		self.dlg.show()

		
	def changeTValues(self, layer):
		# create a random array of new value
		myList = np.random.rand(5).tolist()
		#print 'myList:',myList
		#~ mytList = [(val,) for val in myList]
		#~ mytList=tuple(mytList)
		mytList = [(val,i+1) for i,val in enumerate(myList)]
		#print 'mytList',mytList
		# update table column
		self.DBM.replaceAllColumnValues(tableName = 'links',colName='TVALUE',tupleList=mytList)
		# refresh maps
		layer.triggerRepaint()
		# go on ...
	
	def viewClearAll(self):
		try:
			# assign the correct style
			layer = self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer'))
			layer.loadNamedStyle(os.path.join(self.plugin_dir,'styles','nodes.qml'))
			layer.setLayerName(self.tr('Nodes'))
			self.setFormUI(layer,'nodes')
			layer.triggerRepaint()
			# assign the correct style
			layer = self.getLayerBySource(self.DBM.getDefault('qgis.networklayer'))
			layer.loadNamedStyle(os.path.join(self.plugin_dir,'styles','links.qml'))
			layer.setLayerName(self.tr('Links'))
			self.setFormUI(layer,'links')
			layer.triggerRepaint()
			
		except Exception as e:
			self.showCriticalMessageBox(self.tr("Cannot update map layers"),
															self.tr("Layers cannot be update, see details"),
															str(e))
		
	def viewCustom(self):
		self.showCriticalMessageBox(self.tr("Function non supported yet"),
															self.tr("This function will be available in the next release"),
															'')
															
	def hideShowLidsNodeConnection(self):
		self.hideShowConnection(polyLay = self.getLayerBySource(self.DBM.getDefault('qgis.lidlayer')),
											nodeToFld = self.DBM.getDefault('qgis.lidlayer.field.node_to'),
											pointLay = self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),
											nodeIdFld = self.DBM.getDefault('qgis.nodeslayer.field.obj_id'),
											show = self.clearConnection)
										
		if self.clearConnection: self.clearConnection = False
		else: self.clearConnection = True
															
	def hideShowConnection(self,polyLay, nodeToFld, pointLay,nodeIdFld,show = True):
		# polyLay is supposed to be a polygon
		# pointLay is supposed to be a point
		if show:
			self.rbDict = {}
			for poly in polyLay.getFeatures():
				# get poly centroids
				cPoly = poly.geometry().centroid().asPoint()
				# get poly nodeTo value
				nodeToId = poly[nodeToFld]
				# get point
				sql = "\"%s\" like '%s'"%(nodeIdFld,nodeToId)
				expr = QgsExpression(sql)
				points = pointLay.getFeatures( QgsFeatureRequest( expr ) )
				for pt in points:
					node = pt.geometry().centroid().asPoint()
					# draw rubberband
					vertex = [QgsPoint(cPoly), QgsPoint(node)]
					self.rbDict[poly.id()] = QgsRubberBand(self.iface.mapCanvas(), False)
					self.rbDict[poly.id()].setToGeometry(QgsGeometry.fromPolyline(vertex), None)
					self.rbDict[poly.id()].setColor( QColor( 0,255,0,100 ) )
					self.rbDict[poly.id()].setLineStyle( Qt.DashLine )
					self.rbDict[poly.id()].setWidth( 4 )
		else:
			for k in self.rbDict.keys():
				self.iface.mapCanvas().scene().removeItem(self.rbDict[k])

			self.rbDict = {}
			
	def networkTravelTime(self):
		travelTime = self.calculateTravelTime(netLayer = self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),
											diamFld = self.DBM.getDefault('qgis.networklayer.field.diam'),
											mannFld = self.DBM.getDefault('qgis.networklayer.field.mann'),
											startElevFld = self.DBM.getDefault('qgis.networklayer.field.elev_start'),
											endElevFld = self.DBM.getDefault('qgis.networklayer.field.elev_end'),
											lengthFld =  self.DBM.getDefault('qgis.networklayer.field.length'))

		print(self.tr('Estimated travel time'))

		msg = QMessageBox()
		msg.setIcon(QMessageBox.Information)
		msg.setText(self.tr('Estimated travel time'))
		msg.setInformativeText(self.tr('Estimated travel time is %s (in minutes)')%int(travelTime/60))
		msg.setWindowTitle(self.tr('SMARTGREEN'))
		#msg.setDetailedText(detailText)
		msg.setStandardButtons(QMessageBox.Ok)
		msg.exec_()
		
	def maxNetworkTravelTime(self):
		# get init links
		from tools.check_data import CheckData
		checker = CheckData(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),progress=None)
		ids = checker.getExtremeLinks(direction = -1)
		
		linkLay=self.getLayerBySource(self.DBM.getDefault('qgis.networklayer'))
		maxTravelTime = 0.0
		maxTravelIds = []
		for id in ids:
			#print 'test feature id %s'%(id)
			linkLay.selectByIds([id])
			# select features
			for link in linkLay.selectedFeatures():
				ids = checker.getChainedLinks(link,direction = 1)
			
			linkLay.selectByIds(ids)
			
			travelTime = self.calculateTravelTime(netLayer = linkLay,
												diamFld = self.DBM.getDefault('qgis.networklayer.field.diam'),
												mannFld = self.DBM.getDefault('qgis.networklayer.field.mann'),
												startElevFld = self.DBM.getDefault('qgis.networklayer.field.elev_start'),
												endElevFld = self.DBM.getDefault('qgis.networklayer.field.elev_end'),
												lengthFld =  self.DBM.getDefault('qgis.networklayer.field.length'))
			
			if maxTravelTime<travelTime:
				maxTravelTime = travelTime
				maxTravelIds = ids
											
		linkLay.selectByIds(maxTravelIds)
		
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Information)
		msg.setText(self.tr('Estimated travel time is %s (in minutes)')%int(maxTravelTime/60))
		msg.setInformativeText(self.tr('Selection shows the maximum path'))
		msg.setWindowTitle('SMARTGREEN')
		#msg.setDetailedText(detailText)
		msg.setStandardButtons(QMessageBox.Ok)
		msg.exec_()
		
	def calculateTravelTime(self,netLayer,diamFld,mannFld,startElevFld,endElevFld,lengthFld):
		from tools.check_data import CheckData
		checker = CheckData(self.getLayerBySource(self.DBM.getDefault('qgis.networklayer')),self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer')),progress=None)
		
		travelTime = 0.0
		cumLength = 0.0
		nFeat = 0
		for feat in netLayer.selectedFeatures():
			#diam = feat[diamFld]
			diam = checker.getRefDimension(feat)
			mann = feat[mannFld]
			startElev = feat[startElevFld]
			endElev = feat[endElevFld]
			length = feat[lengthFld]
			# calculate wetted area
			radius = diam/4.0
			# calculate slope
			try: slope = (startElev-endElev)/length
			except: slope = 0.0

			if slope <=0:
				self.smDock.setInfo(('<a href="find;%s;%s">'+self.tr('Link %s')+'</a> '+ self.tr('has null or negative slope %s'))%(netLayer.id(),feat.id(),feat['OBJ_ID'],slope), error = True)
				slope = 0.001
			
			flowVel = (radius**(2.0/3.0))*(slope**0.5)/mann
			if flowVel>0:
				travelTime += length/flowVel # in second
				cumLength += length
				nFeat+=1
			else:
				self.smDock.setInfo(('<a href="find;%s;%s">'+self.tr('Link %s')+'</a> '+ self.tr('has negative flow velocity %s'))%(netLayer.id(),feat.id(),feat['OBJ_ID'],flowVel), error = True)
			
		# calculate average distance
		meanLength = cumLength/nFeat
		# TODO: calculate superficial flow time (needs rain intensity curve)
		return travelTime
		
	def getRowIdLookTable(self,layer):
		i = 0
		res = {}
		for feat in layer.getFeatures():
			id = feat.id()
			res.update({i:id})
			i+=1
		
		return res
		
	def makeStatistics(self):
		import numpy as np
		from scipy import stats
		# report some statistics from links and node attributes
		links = self.getLayerBySource(self.DBM.getDefault('qgis.networklayer'))
		elevStart = []
		elevEnd = []
		length = []
		for link in links.getFeatures():
			if link['ELEV_START'] == NULL: elevStart.append(np.nan)
			else: elevStart.append(link['ELEV_START'])
			if link['ELEV_END']== NULL: elevEnd.append(np.nan)
			else: elevEnd.append(link['ELEV_END'])
			if link['LENGTH']== NULL: length.append(np.nan)
			else: length.append(link['LENGTH'])
		
		
		# transfor to numpy array
		elevStart = np.array(elevStart)
		elevEnd = np.array(elevEnd)
		length = np.array(length)
		
		slope = (elevStart-elevEnd)/length
		
		self.smDock.appendText('<h1>Statistics</h1>')
		self.smDock.appendText('<table width="100%" cellspacing="0" cellpadding="2px">')
		self.smDock.appendText('<tr><th>Variable</th><th>n. obs</th><th>n. valid obs</th><th>sum</th><th>min</th><th>max</th><th>mean</th><th>variance</th><th>skewness</th><th>kurtosis</th></tr>')
		nobs, minmax, mean, variance, skewness, kurtosis = stats.describe(length,nan_policy ='omit')
		self.smDock.appendText('<tr><th>%s</th> <th>%s</th> <th>%s</th> <th>%s</th> <th>%s</th> <th>%s</th> <th>%s</th> <th>%s</th> <th>%s</th> <th>%s</th> </tr>'%('length',length.size,nobs,np.sum(length), minmax[0],minmax[1],mean,variance,skewness, kurtosis))
		nobs, minmax, mean, variance, skewness, kurtosis = stats.describe(slope,nan_policy ='omit')
		self.smDock.appendText('<tr><th>%s</th> <th>%s</th> <th>%s</th> <th>%s</th> <th>%s</th> <th>%s</th> <th>%s</th> <th>%s</th> <th>%s</th> <th>%s</th> </tr>'%('slope',slope.size,nobs,np.sum(slope), minmax[0],minmax[1],mean,variance,skewness, kurtosis))
		self.smDock.appendText('</table>')
		
	def showPrecipitationDialog(self):
		from forms.time_series_mainwindow import TimeSeriesMainwindow
		self.dlg = TimeSeriesMainwindow(self.plugin_dir,self.DBM,self.getLayerBySource(self.DBM.getDefault('qgis.weatherstationslayer')))
		self.dlg.show()
		
	def showObservedDataDialog(self):
		from forms.observed_data_mainwindow import ObservedDataMainwindow
		self.dlg = ObservedDataMainwindow(self.plugin_dir,self.DBM,None,None)
		self.dlg.show()
		
	def setLidsParams(self):
		# get lids layer
		lay = self.getLayerBySource(self.DBM.getDefault('qgis.lidlayer'))
		
		nOfSelection = lay.selectedFeatureCount()
		#open parameters input
		from forms.lid_params import LidParams
		dlg = LidParams(self.DBM,nOfSelection)
		result = dlg.exec_()
		
		# See if OK was pressed
		if result == 1: 
			# return parameters after closing form
			parList = dlg.getParameter()
			# set selected parameters to the selected features in lids shapefile
			
			if parList['USESELECTION']:
				# use only selection
				featureList = lay.selectedFeatures()
			else:
				# apply to all
				featureList = lay.getFeatures()
				
			# delete USESELECTION
			del parList['USESELECTION']
			
			fldList = parList.keys()
			
			# start editing section
			lay.startEditing()
			
			for feature in featureList:
				for fld in fldList:
					# get attribute
					value = parList[fld]
					#print fld,value
					# get field index
					fldIdx = lay.fields().indexFromName(fld)
					# update attributes
					lay.changeAttributeValue(feature.id(),fldIdx,value,True)
					
			lay.commitChanges()

		
	def setClosestNode(self,progress = None):
		fix = True
		
		lidsLayer = self.getLayerBySource(self.DBM.getDefault('qgis.lidlayer'))
		nodesLayer = self.getLayerBySource(self.DBM.getDefault('qgis.nodeslayer'))
		
		idList = []
		objIdList = []
		nodeIdList = []
		msgList = []
		
		nodetoIdx = lidsLayer.fields().indexFromName('NODE_TO')
		msgIdx = lidsLayer.fields().indexFromName('MSG')
		
		#create spatial index object to store nodes
		spIndex = QgsSpatialIndex() 
		nodes = nodesLayer.getFeatures() #gets all features in layer
		for n in nodes:
			spIndex.insertFeature(n)
		
		# select all lids feature without node connection
		expr = QgsExpression( "\"%s\" is Null"%'NODE_TO')
		lids = lidsLayer.getFeatures( QgsFeatureRequest( expr ) )
		
		for l in lids:
			objId = l['OBJ_ID']
			# get centroid of geometry
			geom = l.geometry().centroid().asPoint()
			
			# find the closest node
			nearestNodeIds = spIndex.nearestNeighbor(geom,1) # we need only one neighbour
			if len(nearestNodeIds)>0:
				nearestNodeId = nearestNodeIds[0]
				nearestNodeList = nodesLayer.getFeatures(QgsFeatureRequest().setFilterFid(nearestNodeId))
				nearestNode = QgsFeature()
				nearestNodeList.nextFeature(nearestNode)
				
				nearestNodeName = nearestNode['OBJ_ID']
				
				idList.append(l.id())
				objIdList.append(objId)
				nodeIdList.append(nearestNodeName)
				msgList.append('12(%s)'%'NODE_TO')
				
				# report finding
				if progress is not None: progress.setInfo('<a href="find;%s;%s">LLID %s</a> has no receiving node. The closest node name is %s'%(lidsLayer.id(),l.id(),objId,nearestNodeName), error = False)
			
				
				
		if fix: lidsLayer.startEditing()
		
		if lidsLayer.isEditable():
			for i, id in enumerate(idList):
				# update attributes
				if progress is not None: progress.setInfo('set "NODE_TO" of <a href="find;%s;%s">node %s</a> to %s'%
														  (lidsLayer.id(),id,objIdList[i],nodeIdList[i]), error = False)
				#print 'set bottom elevation of node %s to %s'%(id,elevList[i])
				lidsLayer.changeAttributeValue(id,nodetoIdx,nodeIdList[i],True)
				#self.appendMessage(lidsLayer,id,msgIdx,msgList[i])
				
		if fix:
			lidsLayer.commitChanges()
			lidsLayer.updateExtents()	
			
	def checkLidAttribute(self,progress = None):
		lidsLayer = self.getLayerBySource(self.DBM.getDefault('qgis.lidlayer'))
		
		list1 = ['VOL','HEIGHT','DIAM_OUT','HEIGHT_OUT']
		list2 = ['DEPTH','KS_SOIL','TETA_SAT','TETA_FC','TETA_WP','SLOPE','WP_MAX']
		
		lids = lidsLayer.getFeatures()
		
		for l in lids:
			# check LID id
			objId = l['OBJ_ID']
			
			if (objId == NULL) or (objId is None) or (objId =='NUL'):
				if progress is not None: progress.setInfo(('<a href="find;%s;%s">LID %s</a> '+self.tr('has no %s. It is not a mandatory attribute but this LID will not be exported!'))%(lidsLayer.id(),l.id(),objId,'OBJ_ID'), error = False)
			
			# check LID name
			name = l['NAME']
			if (name == NULL) or (name is None) or (name =='NUL'):
				if progress is not None: progress.setInfo(('<a href="find;%s;%s">LID %s</a> '+self.tr('has no %s. It is not a mandatory attribute.'))%(lidsLayer.id(),l.id(),objId,'NAME'), error = False)
				
			# check node_to
			nodeto = l['NODE_TO']
			if (nodeto == NULL) or (nodeto is None) or (nodeto =='NUL'):
				if progress is not None: progress.setInfo(('<a href="find;%s;%s">LID %s</a> '+self.tr('has no %s. It is a mandatory attribute.'))%(lidsLayer.id(),l.id(),objId,'NODE_TO'), error = True)
			
			# check lid type attributes
			
			LIDcat = l['CAT']
			
			if (LIDcat == NULL) or (LIDcat is None) or (LIDcat =='NUL'):
				if progress is not None: progress.setInfo(('<a href="find;%s;%s">LID  %s</a> '+self.tr('has no %s. It is a mandatory attribute.'))%(lidsLayer.id(),l.id(),objId,'CAT'), error = True)
				continue

			if LIDcat in ['1','Reservoir']:
				lidFields = list1
			else:
				lidFields = list2
			
			for fld in lidFields:
				val = l[fld]
				if (val == NULL) or (val is None) or (val =='NUL'):
					if progress is not None: progress.setInfo(('<a href="find;%s;%s">LID  %s</a> '+self.tr('has no %s. It is a mandatory attribute.'))%(lidsLayer.id(),l.id(),objId,fld), error = True)
		
		