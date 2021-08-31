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

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt

from .smartgreen_maptool import SmartGreenMapTool

# Import the PyQt and QGIS libraries
from qgis.core import *
from qgis.gui import *
import os.path
import time

class VectorIdentifyTool(QgsMapToolIdentify):
	"""
	The map tool used to interrogate vector map
	"""
	def __init__(self, iface, qgsMapToolIdentifyAction):
		self.iface = iface
		self.canvas = iface.mapCanvas()
		QgsMapToolIdentify.__init__(self, self.canvas)
		self.qgsMapToolIdentifyAction = qgsMapToolIdentifyAction

	def canvasReleaseEvent(self, mouseEvent):
		#print 'mouse released'
		results = self.identify(mouseEvent.x(),mouseEvent.y(),self.TopDownStopAtFirst, self.VectorLayer)
		if len(results) > 1:
			QMessageBox.information(None, "Info", u"More than one object!") 
		elif len(results) == 1:
			featureForm = self.iface.getFeatureForm(results[0].mLayer, results[0].mFeature)
			#featureForm.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
			featureForm.setWindowFlags(Qt.Dialog)
			featureForm.show()
		else:
			#self.qgsMapToolIdentifyAction.canvasReleaseEvent(mouseEvent)
			pass
			
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
			self.qgsMapToolIdentifyAction.setChecked(False)
			QgsMapToolIdentify.deactivate(self)
		except Exception as e:
			#print str(e)
			pass
		