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

#Qt import
from PyQt5.QtCore import QMetaObject, QObject,Qt
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QDialogButtonBox

from qgis.PyQt import uic, QtCore, QtGui
try:
	from qgis.PyQt.QtGui import QDockWidget
except:
	from qgis.PyQt.QtWidgets import QDockWidget

#qgis import
from qgis.core import *
from qgis.gui import *
#other
import platform
import os
import time
import operator
import numpy as np
import sys
import inspect

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
	sys.path.insert(0, cmd_folder)

try:
	from PyQt4.Qwt5 import *
	Qwt5_loaded = True
except ImportError:
	Qwt5_loaded = False
	
try:
	from matplotlib import *
	import matplotlib
	matplotlib_loaded = True
except ImportError:
	matplotlib_loaded = False

uiFilePath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'SMDock.ui'))
FormClass = uic.loadUiType(uiFilePath)[0]

from forms.custom_input import StringInput, NumericInput, CheckInput


class SMDock(QDockWidget, FormClass):

	TITLE = "SMARTGREEN"
	TYPE = None
	
	closed = QtCore.pyqtSignal()
	
	def __init__(self, iface, smplugin, parent=None):
		QDockWidget.__init__(self, parent)
		
		self.nodeStyles = ['',self.tr('Max overflow'),self.tr('Max degree of filling')]
		self.linkStyles = ['',self.tr('Conduit slope'),self.tr('Conduit area contraction'),
						   self.tr('Max degree of filling'),self.tr('Max flow velocity'),self.tr('Max flow discharge')]
		
		self.setupUi(self)
		self.iface = iface
		self.smplugin = smplugin
		self.location = Qt.RightDockWidgetArea
		# init option tabs
		self.initViewTab()
		# test progress bar and console
		self.setPercentage(0)
		
		self.buttonBox.button(QDialogButtonBox.Abort).clicked.connect(self.stopThread)
		#QObject.connect(self.buttonBox, SIGNAL("reset()"), self.clearConsole)
		self.buttonBox.button(QDialogButtonBox.Reset).clicked.connect(self.clearConsole)
		QMetaObject.connectSlotsByName(self)
		
		self._console.anchorClicked.connect(self.on_anchor_clicked)
		
	def clearConsole(self):
		self._console.setHtml('')
		self.setText(self.tr('SMARTGREEN is ready!'))
				
	def stopThread(self):
		pass
				
	def closeEvent(self, event):
		self.closed.emit()
		
	def initViewTab(self):
		# update node view options
		self.nodeStyleCB.clear()
		self.nodeStyleCB.addItems(self.nodeStyles)
		self.nodeStyleCB.currentIndexChanged[str].connect(self.updateNodeStyle)
		
		self.showNodeID.stateChanged.connect(self.showNodeLabel)
		
		# update link view options
		self.linkStyleCB.clear()
		self.linkStyleCB.addItems(self.linkStyles)
		self.linkStyleCB.currentIndexChanged[str].connect(self.updateLinkStyle)
		
		self.showLinkID.stateChanged.connect(self.showLinkLabel)
		
		self.showLIDID.stateChanged.connect(self.showLIDLabel)
		
		self.showLIDConnection.stateChanged.connect(self.showConnection)
		
	def showNodeLabel(self,state):
		showLabel = False
		if state == QtCore.Qt.Checked: showLabel = True
		layer = self.smplugin.getLayerBySource(self.smplugin.DBM.getDefault('qgis.nodeslayer'))
		self.displaylabels(layer,showLabel)
	
	def showLinkLabel(self,state):
		showLabel = False
		if state == QtCore.Qt.Checked: showLabel = True
		layer = self.smplugin.getLayerBySource(self.smplugin.DBM.getDefault('qgis.networklayer'))
		self.displaylabels(layer,showLabel,True)
		
	def showLIDLabel(self,state):
		showLabel = False
		if state == QtCore.Qt.Checked: showLabel = True
		layer = self.smplugin.getLayerBySource(self.smplugin.DBM.getDefault('qgis.lidlayer'))
		self.displaylabels(layer,showLabel)
		
	def showConnection(self,state):
		showLabel = False
		if state == QtCore.Qt.Checked: showLabel = True
		layer = self.smplugin.getLayerBySource(self.smplugin.DBM.getDefault('qgis.lidlayer'))
		self.smplugin.hideShowLidsNodeConnection()
		
	def updateLinkStyle(self,selectedStyle):
		layer = self.smplugin.getLayerBySource(self.smplugin.DBM.getDefault('qgis.networklayer'))
		selectedStyle = self.linkStyleCB.currentText()
		idStyle = self.linkStyles.index(selectedStyle)

		#selectedStyle = nodeStyleCB.currentText()
		if idStyle == 1:  # Conduit Slope
			# get elevation and distance
			elevStart =  np.array(self.smplugin.DBM.getColumnValues(fieldName='ELEV_START',tableName='links'), dtype=np.float)
			elevEnd =  np.array(self.smplugin.DBM.getColumnValues(fieldName='ELEV_END',tableName='links'), dtype=np.float)
			dist =  np.array(self.smplugin.DBM.getColumnValues(fieldName='LENGTH',tableName='links'), dtype=np.float)
			# calculate slope
			slope = (np.array(elevStart)-np.array(elevEnd))/np.array(dist)
			# assign max values to tvalue in the link layer
			objIds = self.smplugin.getRowIdLookTable(layer)
			#print 'objIds:',objIds
			mytList = [(val,objIds[i]) for i,val in enumerate(slope)]
			self.smplugin.DBM.replaceAllColumnValues(tableName = 'links',colName='TVALUE',tupleList=mytList)
			# assign the correct style
			layer.loadNamedStyle(os.path.join(self.smplugin.plugin_dir,'styles','networkslope.qml'))
			layer.setName(self.tr('Links - slope (-)'))
		elif idStyle == 2: #Area contraction
			# get diameter and heigths
			linkId = np.array(self.smplugin.DBM.getColumnValues(fieldName='OBJ_ID',tableName='links'))
			endNodeId = np.array(self.smplugin.DBM.getColumnValues(fieldName='NODE_END',tableName='links'))
			diam = np.array(self.smplugin.DBM.getColumnValues(fieldName='DIAM',tableName='links'), dtype=np.float)
			dim1 = np.array(self.smplugin.DBM.getColumnValues(fieldName='DIM1',tableName='links'), dtype=np.float)
			dim2 = np.array(self.smplugin.DBM.getColumnValues(fieldName='DIM2',tableName='links'), dtype=np.float)
			dim3 = np.array(self.smplugin.DBM.getColumnValues(fieldName='DIM3',tableName='links'), dtype=np.float)
			dim4 = np.array(self.smplugin.DBM.getColumnValues(fieldName='DIM3',tableName='links'), dtype=np.float)
			shape = np.array(self.smplugin.DBM.getColumnValues(fieldName='S_SHAPE',tableName='links'))
			
			# calculate section area shape based
			
			area = np.pi*(diam*diam/4) # by default are all circular
			#area[shape=='C'] =np.pi*((diam[shape=='C'])*(diam[shape=='C'])/4)
			area[shape=='R'] =(dim1[shape=='R'])*(dim2[shape=='R'])
			area[shape=='T'] =0.5*(2*(dim2[shape=='T'])+(dim3[shape=='T'])*(dim1[shape=='T'])+(dim4[shape=='T'])*(dim1[shape=='T']))*(dim1[shape=='T'])
			area[shape=='E'] =np.pi*(0.5*(dim1[shape=='E']))*(0.5*(dim2[shape=='E']))
			
			#TODO: 'N' is not implemented 
			
			# get index of the following link element
			CF = []
			for i,id in enumerate(linkId):
				# get following links
				follIds = self.smplugin.DBM.getFollowingLink(nodeId =endNodeId[i],nodeFld='NODE_START')
				if len(follIds)==0:
					follIds = [id]
					
				follIds = np.array(follIds)
					
				# get index of following links
				follIdIdx = np.array(range(0,len(follIds)))
				for fId in follIds:
					try:
						follIdIdx[follIds==fId]=np.where(linkId == fId)[0]
					except Exception as e:
						self.setConsoleInfo('fId: %s' % str(fId))
						self.error('%s'%str(e))

				# get following links area
				follArea = np.sum(area[follIdIdx])
				
				# calculate contraction factor CF
				# <1: contraction (-)
				# =1: equal
				# >1: expantion
				CF.append(follArea/area[i])
			
			# assign contraction values to tvalue in the link layer
			objIds = self.smplugin.getRowIdLookTable(layer)
			#print 'objIds:',objIds
			mytList = [(val,objIds[i]) for i,val in enumerate(CF)]
			self.smplugin.DBM.replaceAllColumnValues(tableName = 'links',colName='TVALUE',tupleList=mytList)
			# assign the correct style
			layer.loadNamedStyle(os.path.join(self.smplugin.plugin_dir,'styles','networkareacontraction.qml'))
			layer.setName(self.tr('Links - section area contraction (-)'))
		elif idStyle == 3: # Max degree of filling
			# get matrix of the filled area
			y1 = self.smplugin.DBM.getArray(varName = 'Qret-y1')
			if y1 is None: return
			
			y2 = self.smplugin.DBM.getArray(varName = 'Qret-y2')
			if y2 is None: return
			
			ym = 0.5*(y1+y2)
			# calculate maximum value for each record
			ym = np.amax(ym,axis=1)
			# get diameter and heigth
			diam = self.smplugin.DBM.getColumnValues(fieldName='DIAM',tableName='links')
			heigth = self.smplugin.DBM.getColumnValues(fieldName='DIM1',tableName='links')
			
			# where diameter is null, get heigth
			for i,d in enumerate(diam):
				if diam[i] is None:
					diam[i] = heigth[i]
				
			rowmax = ym[0:len(diam)]/np.array(diam)
			# assign max values to tvalue in the link layer
			objIds = self.smplugin.getRowIdLookTable(layer)
			#print 'objIds:',objIds
			mytList = [(val,objIds[i]) for i,val in enumerate(rowmax)]
			self.smplugin.DBM.replaceAllColumnValues(tableName = 'links',colName='TVALUE',tupleList=mytList)
			# assign the correct style
			layer.loadNamedStyle(os.path.join(self.smplugin.plugin_dir,'styles','networkfilleddeg.qml'))
			layer.setName(self.tr('Links - degree of filling (%)'))
		elif idStyle == 4: # Max flow velocity
			# get matrix of the flow velocity
			meanArea = self.smplugin.DBM.getArray(varName = 'Qret-Vaverage')
			if meanArea is None: return
			# calculate maximum value for each record
			rowmax = np.amax(meanArea,axis=1)
			# assign max values to tvalue in the link layer
			objIds = self.smplugin.getRowIdLookTable(layer)
			#print 'objIds:',objIds
			mytList = [(val,objIds[i]) for i,val in enumerate(rowmax)]
			self.smplugin.DBM.replaceAllColumnValues(tableName = 'links',colName='TVALUE',tupleList=mytList)
			# assign the correct style
			layer.loadNamedStyle(os.path.join(self.smplugin.plugin_dir,'styles','networkvelocity.qml'))
			layer.setName(self.tr('Links - flow velocity (m/s)'))
		elif idStyle == 5: #Max flow discharge
			# get matrix of the discharge
			qOut = self.smplugin.DBM.getArray(varName = 'Qret-Qout')
			if qOut is None: return
			# calculate maximum value for each record
			rowmax = np.amax(qOut,axis=1)
			# assign max values to tvalue in the link layer
			objIds = self.smplugin.getRowIdLookTable(layer)
			mytList = [(val,objIds[i]) for i,val in enumerate(rowmax)]
			self.smplugin.DBM.replaceAllColumnValues(tableName = 'links',colName='TVALUE',tupleList=mytList)
			# assign the correct style
			layer.loadNamedStyle(os.path.join(self.smplugin.plugin_dir,'styles','networkdischarge.qml'))
			layer.setName(self.tr('Links - flow discharge (m^3/s)'))
		else:
			layer.loadNamedStyle(os.path.join(self.smplugin.plugin_dir,'styles','links.qml'))
			layer.setName(self.tr('Links'))
			
		self.smplugin.setFormUI(layer,'links')	
		layer.triggerRepaint()
		
	def updateNodeStyle(self,selectedStyle):
		layer = self.smplugin.getLayerBySource(self.smplugin.DBM.getDefault('qgis.nodeslayer'))
		selectedStyle = self.nodeStyleCB.currentText()
		idStyle = self.nodeStyles.index(selectedStyle)
		
		if idStyle == 1: #'Max overflow':
			# get matrix of the filled area
			qOverflow = self.smplugin.DBM.getArray(varName = 'Hnode-Qoverflow')
			if qOverflow is None: return
			
			# calculate maximum value for each record
			rowmax = np.amax(qOverflow,axis=1)
			rowmax = [float(x) for x in rowmax] # to prevent all zeros error
			# assign max values to tvalue in the link layer
			objIds = self.smplugin.getRowIdLookTable(layer)
			mytList = [(val,objIds[i]) for i,val in enumerate(rowmax)]
			self.smplugin.DBM.replaceAllColumnValues(tableName = 'nodes',colName='TVALUE',tupleList=mytList)
			# assign the correct style
			layer.loadNamedStyle(os.path.join(self.smplugin.plugin_dir,'styles','nodesqoverflow.qml'))
			layer.setName(self.tr('Nodes - overflow (m^3/s)'))
		elif idStyle == 2: #selectedStyle == 'Max degree of filling':
			# get matrix of the filled area
			hNode = self.smplugin.DBM.getArray(varName = 'Hnode-H')
			if hNode is None: return
			elevMax = np.amax(hNode,axis=1)
			# get node bottom elevation
			botElev = self.smplugin.DBM.getColumnValues(fieldName='ELEV_BOT',tableName='nodes')
			# get node top elevation
			topElev = self.smplugin.DBM.getColumnValues(fieldName='ELEV_TOP',tableName='nodes')
			#~ print 'botElev:',botElev
			#~ print 'topElev:',topElev
			
			# calculate maximum value for each record
			hWater = elevMax[0:len(botElev)]-botElev
			hNode = list(map(operator.sub, topElev,botElev))
			hNode = hNode[0:len(botElev)]
			# degree of filling
			fillDeg = hWater/hNode
			# assign max values to tvalue in the link layer
			layer = self.smplugin.getLayerBySource(self.smplugin.DBM.getDefault('qgis.nodeslayer'))
			objIds = self.smplugin.getRowIdLookTable(layer)
			mytList = [(val,objIds[i]) for i,val in enumerate(fillDeg)]
			self.smplugin.DBM.replaceAllColumnValues(tableName = 'nodes',colName='TVALUE',tupleList=mytList)
			# assign the correct style
			layer.loadNamedStyle(os.path.join(self.smplugin.plugin_dir,'styles','nodesfilleddeg.qml'))
			layer.setName(self.tr('Nodes - degree of filling (%)'))
		else:
			layer.loadNamedStyle(os.path.join(self.smplugin.plugin_dir,'styles','nodes.qml'))
			layer.setName(self.tr('Nodes'))
		
		self.smplugin.setFormUI(layer,'nodes')	
		layer.triggerRepaint()
		
	@QtCore.pyqtSlot(str,str)
	def appendText(self, text,col= None):
		if text != '':
			if col is None:
				text = text
			else:
				execTime = time.strftime("%H:%M:%S")
				text = '<font color="%s">%s - %s</font><br>' %(col,execTime,text)
			#~ htmlText = self._console.toHtml()
			#~ htmlText += text
			#~ self._console.setHtml(htmlText)
			textCursor = self._console.textCursor()
			textCursor.movePosition(QTextCursor.End)
			self._console.setTextCursor(textCursor)
			self._console.insertHtml(text)
			# scroll to the end
			sb = self._console.verticalScrollBar()
			sb.setValue(sb.maximum())
			
		
	def setConsoleInfo(self,text):
			self.appendText(text,'blue')
			#print 'INFO:',text
		
	def error(self,text):
		self.appendText(text,'red')
	
	@QtCore.pyqtSlot(int)
	def setPercentage(self,val):
		try:
			val = int(val)
		except:
			val = 0
		
		if val >100: val =100
		
		if val <0: val =0
		
		self._progressbar.setValue(val)
		#print 'PERC:',val
		
	def setText(self, text):
		self.appendText(text,'gray')
		
	def setInfo(self,text, error=False):
		if error:
			self.error(text)
		else:
			self.setConsoleInfo(text)
		
	def setCommand(self, text):
		self.appendText(text,'black')
				
	def setTab(self, tabName):
		for i in range(0,self.tab.count()):
			if self.tab.tabText(i) == tabName:
				self.tab.setCurrentIndex(i)
				
	def on_anchor_clicked(self,url):
		text = str(url.toString())
		toks = text.split(';')
		self._console.setSource(QtCore.QUrl()) #stops the page from changing
		if toks[0]=='find':
			# the second token should be the layer
			lay = QgsProject.instance().mapLayers()[toks[1]]
			lay.removeSelection()
			it = lay.getFeatures(QgsFeatureRequest().setFilterFid(int(toks[2])))
			ids = [i.id() for i in it]
			lay.select(ids)
			canvas = self.iface.mapCanvas()
			canvas.zoomToSelected(lay)
		elif toks[0]=='select':
			pass
		else:
			# do nothing
			pass
			
	def displaylabels(self,layer,draw, isLine = False):
		label = QgsPalLayerSettings()
		#label.readFromLayer(layer)
		label.enabled = True
		label.fieldName = 'OBJ_ID'
		label.drawLabels = draw
		if isLine: label.placement = QgsPalLayerSettings.Line
		#label.writeToLayer(layer)
		#self.iface.mapCanvas().refresh()
		layer.setLabeling(QgsVectorLayerSimpleLabeling(label))
		layer.triggerRepaint()