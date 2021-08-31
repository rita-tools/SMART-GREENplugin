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

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMessageBox

from .smartgreen_maptool import SmartGreenMapTool

# Import the PyQt and QGIS libraries
from qgis.gui import *
from qgis.core import *
import numpy as np

from forms.chart_dialog import ChartDialog
from tools.compare_layer_source import compareLayerSource

import matplotlib.pyplot as plt

class PlotTool(QgsMapToolIdentify):
	"""
	The map tool used to interrogate vector map
	"""
	def __init__(self, iface, qgsMapToolIdentifyAction,sgplugin):
		self.iface = iface
		self.canvas = iface.mapCanvas()
		QgsMapToolIdentify.__init__(self, self.canvas)
		self.qgsMapToolIdentifyAction = qgsMapToolIdentifyAction
		self.sgplugin = sgplugin
		self.DBM = sgplugin.DBM
		self.rbDict = {}

	def canvasReleaseEvent(self, mouseEvent):
		#print 'mouse released'
		results = self.identify(mouseEvent.x(),mouseEvent.y(),self.TopDownStopAtFirst, self.VectorLayer)
		
		# del rubber bands
		self.delRubbers()
		# clear from all previous lines ...
		#self.dlg = self.sgplugin.smDock.plotArea
		#self.dlg.clearAll()
		
		# activate plot tab
		# self.sgplugin.smDock.setTab('Plot')
		
		if len(results) > 1:
			QMessageBox.information(None, "Info", u"More than one object!") 
		elif len(results) == 1:
			self.feat = results[0].mFeature
			self.lay = results[0].mLayer
			# populate feature id vs counter dictionary
			id2Row = self.getIdRowLookTable(self.lay)
			#self.rowId = self.feat.id()-1
			self.rowId = id2Row[self.feat.id()]
			
			#rType = self.lay.wkbType()
			rType = QgsWkbTypes.PolygonGeometry
			rGeom = self.feat.geometry()
			rGeom = rGeom.buffer(float(4), int(1))

			# print('rtype:',rType)
			# if rType in [QgsWkbTypes.Point,QgsWkbTypes.MultiPoint,QgsWkbTypes.PointZ,QgsWkbTypes.Point25D,QgsWkbTypes.MultiPoint25D]:
			# 	rType = QgsWkbTypes.PolygonGeometry
			# 	rGeom = rGeom.buffer(float(4), int(1))
			# elif rType in [QgsWkbTypes.LineString ,QgsWkbTypes.MultiLineString ,QgsWkbTypes.LineStringZ ,QgsWkbTypes.MultiLineStringZ]:
			# 	rType = QgsWkbTypes.LineGeometry
			# else:
			# 	rType = QgsWkbTypes.PolygonGeometry

			self.rbDict[self.rowId] = QgsRubberBand(self.iface.mapCanvas(), rType)
			self.rbDict[self.rowId].setColor( QColor( 0,255,0,100 ) )
			self.rbDict[self.rowId].setWidth( 4 )
			self.rbDict[self.rowId].addGeometry(rGeom, None) 
			
			# setup series to plot
			if compareLayerSource(self.lay.source(),self.DBM.getDefault('qgis.networklayer')):
				objId = self.feat[self.DBM.getDefault('qgis.networklayer.field.obj_id')]
				self.dlg = ChartDialog(title=self.tr('Layer: %s - object id: %s - feature id: %s - row id: %s')
											 %(self.lay.name(),objId,self.feat.id(),self.rowId), secondAxis = False)
				self.dlg.rejected.connect(self.delRubbers) # del rubber bands
				# get data from discharge table
				matrix = self.DBM.getArray(varName=objId,tableName='discharges')
				minList = None
				valList = None
				if matrix is not None:
					minList = []
					valList = []
					for i,row in enumerate(matrix):
						minList.append(row[0])
						valList.append(row[1])
						
				self.plotLinkResults(minList, valList)
				#self.dlg.repaint()
				# show dialog
				self.dlg.show()
			elif compareLayerSource(self.lay.source(),self.DBM.getDefault('qgis.nodeslayer')):
				objId = self.feat[self.DBM.getDefault('qgis.nodeslayer.field.obj_id')]
				topElev = self.feat[self.DBM.getDefault('qgis.nodeslayer.field.elev_top')]
				if (topElev == NULL): topElev = None
				botElev = self.feat[self.DBM.getDefault('qgis.nodeslayer.field.elev_bot')]
				if (botElev == NULL): botElev = None
				self.dlg = ChartDialog(title=self.tr('Layer: %s - object id: %s - feature id: %s - row id: %s')%
											 (self.lay.name(),objId,self.feat.id(),self.rowId), secondAxis = True)
				self.dlg.rejected.connect(self.delRubbers) # del rubber bands
				
				# get data from discharge table
				matrix = self.DBM.getArray(varName=objId,tableName='waterlevels')
				minList = None
				valList = None
				if matrix is not None:
					minList = []
					valList = []
					for i,row in enumerate(matrix):
						minList.append(row[0])
						valList.append(row[1])
				
				self.plotNodeResults(topElev,botElev,minList,valList)
				#self.dlg.repaint()
				# show dialog
				self.dlg.show()
			elif compareLayerSource(self.lay.source(),self.DBM.getDefault('qgis.lidlayer')):
				objId = self.feat[self.DBM.getDefault('qgis.lidlayer.field.obj_id')]
				topElev = self.feat[self.DBM.getDefault('qgis.lidlayer.field.height')]
				if (topElev == NULL): topElev = None
				category = self.feat[self.DBM.getDefault('qgis.lidlayer.field.cat')]
				if (category == NULL): category = -1
				self.dlg = ChartDialog(title=self.tr('Layer: %s - object id: %s - feature id: %s - row id: %s')%
											 (self.lay.name(),objId,self.feat.id(),self.rowId), secondAxis = True)
				self.dlg.rejected.connect(self.delRubbers) # del rubber bands
				self.plotLIDResults(category, topElev)
				# show dialog
				self.dlg.show()
			else:
				#self.dlg.clearAll()
				#self.dlg.repaint()
				pass
			
		else:
			#self.qgsMapToolIdentifyAction.canvasReleaseEvent(mouseEvent)
			pass
			
			
	def plotLIDResults(self,category = -1, topElev = None):
		if category in ['1',1]:
			# reservoir like
			varToPlotList = ['GIs_route-reserv_Qin','GIs_route-reserv_Qrete','GIs_route-reserv_h']
			labs = [self.tr('Inflow (m^3/s)'),self.tr('Outflow (m^3/s)'),self.tr('Stored water depth (m)')]
			cols = ['g','b','m']
			ltypes = ['-','-','-']
			axNum = [1,1,2]
		elif category in ['2',2]:
			# drained surface like
			return
		else:
			return
			
		for i,varToPlot in enumerate(varToPlotList):
			y = self.DBM.getArray(varToPlot)
			y = y[self.rowId]
			nval = y.size
			x = np.array(range(1,nval+1))
			self.dlg.addLinePlot(x,y, lineType = ltypes[i], color = cols[i],name = labs[i], yaxis = axNum[i])
		
		if topElev is not None:
			# show the upper elevation of the nodes
			y = [topElev] * nval
			self.dlg.addLinePlot(x,y, lineType = '--', color = 'dimgray',name = self.tr('Reservoir top (m)'), yaxis = 2)
			
		self.dlg.setAxes(xlabs = None, ylabs = None, xTitle = self.tr('Time step'), yTitle = self.tr('Discharge (m^3/s)'), y2Title = self.tr('Heigth (m)'), mainTitle = self.tr('Time series'))
		self.dlg.updateLimits()
		plt.tight_layout()
			
	def plotNodeResults(self,topElev= None, botElev=None, xcal = None, ycal = None):
		varToPlotList = ['Hnode-Qoverflow','Hnode-H']
		labs = [self.tr('Overflow'),self.tr('Water level')]
		cols = ['r','m']
		ltypes = ['-','-']
		axNum = [1,2]
		
		#~ self.sgplugin.smDock.replacePlot(True)
		#~ self.dlg = self.sgplugin.smDock.plotArea
		#self.dlg.secondAxis(True)
		#self.dlg.clearAll()
		for i,varToPlot in enumerate(varToPlotList):
			y = self.DBM.getArray(varToPlot)
			y = y[self.rowId]
			nval = y.size
			x = np.array(range(1,nval+1))
			self.dlg.addLinePlot(x,y, lineType = ltypes[i], color = cols[i],name = labs[i], yaxis = axNum[i])
		
		if topElev is not None:
			# show the upper elevation of the nodes
			y = [topElev] * nval
			self.dlg.addLinePlot(x,y, lineType = '--', color = 'dimgray',name = self.tr('Node top'), yaxis = 2)
			
		if botElev is not None:
			# show the upper elevation of the nodes
			y = [botElev] * nval
			self.dlg.addLinePlot(x,y, lineType = ':', color = 'gray',name = self.tr('Node bot'), yaxis = 2)
			
		if (xcal and ycal):
			# plot calibration data
			self.dlg.addLinePlot(xcal,ycal, lineType = 'o', color = 'r',name = self.tr('Observed'), yaxis = axNum[i])
		
		self.dlg.setAxes(xlabs = None, ylabs = None, xTitle = self.tr('Time step'), yTitle = self.tr('Discharge (m^3/s)'), y2Title = self.tr('Elevation (m a.s.l)'), mainTitle = self.tr('Time series'))
		self.dlg.updateLimits()
		plt.tight_layout()
		
	def plotLinkResults(self, xcal = None, ycal = None):
		#~ varToPlotList = ['Qret-Qout','Qret-H1','Qret-H2']
		#~ labs = ['Q','H1','H2']
		#~ cols = ['b','r','r']
		#~ ltypes = ['-','-','--']
		#~ axNum = [1,2,2]
		varToPlotList = ['Qret-Qout']
		labs = [self.tr('Discharge')]
		cols = ['b']
		ltypes = ['-']
		axNum = [1]
		#~ self.sgplugin.smDock.replacePlot(False)
		#~ self.dlg = self.sgplugin.smDock.plotArea
		#self.dlg.secondAxis(False)
		#self.dlg.clearAll()
		for i,varToPlot in enumerate(varToPlotList):
			y = self.DBM.getArray(varToPlot)
			y = y[self.rowId]
			x = np.array(range(1,y.size+1))
			q = np.sum(y)*60
			qmax = np.max(y)
			xq = 1+np.where(y==np.max(y))[0][0] #np.mean(x[x>0]) # note that is zero based!
			yq = np.mean(y[y>0])
			self.dlg.addLinePlot(x,y, lineType = ltypes[i], color = cols[i],name = labs[i], yaxis = axNum[i])

		self.dlg.addText(('V = %.2f'%q),xq,yq)
		self.dlg.addText((self.tr('Qmax = %.3f at %s min')%(qmax,xq)),1.1*xq,qmax)
		self.dlg.addSinglePointPlot(xq,qmax)
		
		if (xcal and ycal):
			# plot calibration data
			self.dlg.addLinePlot(xcal,ycal, lineType = 'o', color = 'r',name = self.tr('Observed'), yaxis = axNum[i])
		
		#~ self.dlg.setAxes(xlabs = None, ylabs = None, xTitle = 'time step', yTitle = 'Discharge (m^3/s)', y2Title = 'Elevation (m a.s.l)', mainTitle = 'Time series')
		self.dlg.setAxes(xlabs = None, ylabs = None, xTitle = self.tr('Time step'), yTitle = self.tr('Discharge (m^3/s)'), y2Title = None, mainTitle = self.tr('Time series'))
		self.dlg.updateLimits()
		plt.tight_layout()
		
			
	def delRubbers(self):
		for k in self.rbDict.keys():
			self.iface.mapCanvas().scene().removeItem(self.rbDict[k])
			#del self.rbDict[k]

		self.rbDict = {}
			
	def getRowIdLookTable(self,layer):
		i = 0
		res = {}
		for feat in layer.getFeatures():
			id = feat.id()
			res.update({i:id})
			i+=1
		
		return res
		
	def getIdRowLookTable(self,layer):
		i = 0
		res = {}
		for feat in layer.getFeatures():
			id = feat.id()
			res.update({id:i})
			i+=1
		
		return res
			
	def setActive(self):
		"""
		Activates this map tool
		"""
		self.saveTool = self.canvas.mapTool()
		self.canvas.setMapTool(self)
		
	def deactivate(self):
		"""
		Deactivates this map tool. Removes the rubberband etc.
		"""
		#super(NetworkSelectTool, self).deactivate()
		#MobidicUIMapTool.deactivate(self)
		#print 'in vectorIdentify deactivate'
		try:
			self.delRubbers()
			self.qgsMapToolIdentifyAction.setChecked(False)
			QgsMapToolIdentify.deactivate(self)
			
		except Exception as e:
			print(str(e))
		