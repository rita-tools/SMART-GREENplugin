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

from .smartgreen_maptool import SmartGreenMapTool

# Import the PyQt and QGIS libraries
from qgis.core import *
from qgis.gui import *
import os.path
import time

class RasterIdentifyTool(SmartGreenMapTool):
	"""
	The map tool used to interrogate raster map
	"""

	def __init__(self,iface, button):
		SmartGreenMapTool.__init__(self, iface, button)
		self.iface = iface
		
	def display_point(self, point):
		# report map coordinates from a canvas click
		layer = self.iface.activeLayer()

		if layer is not None:
			if isinstance(layer,QgsRasterLayer):
				width = layer.width()
				height = layer.height()

				xsize = layer.rasterUnitsPerPixelX()
				ysize = layer.rasterUnitsPerPixelY()

				extent = layer.extent()

				ymax = extent.yMaximum()
				xmin = extent.xMinimum()

				#row in pixel coordinates
				row = int(((ymax - point.y()) / ysize) + 1)

				#row in pixel coordinates
				column = int(((point.x() - xmin) / xsize) + 1)

				if row <= 0 or column <=0 or row > height or column > width:
					row = "out of extent"
					column = "out of extent"

			else:
				row = "no raster"
				column = "no raster"
		
		text = 'Row: %s\nCol: %s' %(row, column)
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Information)
		msg.setText(text)
		msg.setWindowTitle('SMARTGREEN')
		msg.setStandardButtons(QMessageBox.Ok)
		msg.exec_()


	def canvasMoveEvent(self, event):
		"""
		Whenever the mouse is moved update the rubberband and the snapping.
		:param event: QMouseEvent with coordinates
		"""
		pass

	def rightClicked(self, _):
		"""
		Resets the rubberband on right clickl
		:param _: QMouseEvent
		"""
		pass

	def leftClicked(self, event):
		"""
		Snaps to the network graph
		:param event: QMouseEvent
		"""
		# store last clicked point
		
		self.lastClickedPoint = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos().x(), event.pos().y())
		#print 'ClickedPoint:',self.lastClickedPoint
		self.display_point(self.lastClickedPoint)
		
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
		print('in rasterIdentify deactivate')
		try:
			SmartGreenMapTool.deactivate(self)
		except Exception as e:
			print(str(e))
