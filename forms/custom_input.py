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

from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QPlainTextEdit, QGridLayout, QComboBox, QListWidget, QCheckBox, \
	QPushButton, QFileDialog

from forms import GdalTools_utils as Utils
import os.path as osp

from qgis.core import *
from qgis.gui import *

class StringInput(QWidget):
	def __init__(self, labelString, defaultValue,descr = '', singleLine = True):
		super(StringInput, self).__init__()
		self.setWhatsThis(descr)
		self.label = QLabel(labelString)
		self.singleLine = singleLine
		if singleLine:
			self.input = QLineEdit()
			self.input.setText(str(defaultValue))
		else:
			self.input = QPlainTextEdit()
			self.input.setPlainText(str(defaultValue))
		
		grid = QGridLayout()
		grid.setSpacing(1)
		grid.addWidget(self.label, 0, 0)
		grid.addWidget(self.input, 1, 0)
		
		self.setLayout(grid)
	
	def getValue(self):
		if self.singleLine:
			return self.input.text()
		else:
			return self.input.toPlainText()

class NumericInput(QWidget):
	def __init__(self, labelString, defaultValue,descr = '', convertTo = 'float'):
		super(NumericInput, self).__init__()
		self.convertTo = convertTo
		self.setWhatsThis(descr)
		self.label = QLabel(labelString)
		self.input = QLineEdit()
		#validator = QDoubleValidator(1,10,2,self);
		#input.setValidator(validator);
		self.input.setText(str(defaultValue))
		grid = QGridLayout()
		grid.setSpacing(10)
		grid.addWidget(self.label, 1, 0)
		grid.addWidget(self.input, 1, 1)
		
		self.setLayout(grid)
	
	def getValue(self):
		if self.convertTo == 'float':
			return float(self.input.text())
		else:
			return int(self.input.text())
	
	def setTitle(self,newTitle):
		self.label.setText(newTitle)

class FieldInput(QWidget):
	def __init__(self, objName, labelString, defaultValue,descr = '',unit = None):
		super(FieldInput, self).__init__()
		#~ self.__name__ = "Custom_FieldInput"
		self.setObjectName(objName)
		self.defaultValue = defaultValue
		if unit == '': unit = None
		self.unit = unit
		self.setWhatsThis(descr)
		self.label = QLabel(labelString)
		self.comboField = QComboBox()
		self.comboUnit = QComboBox()
		self.comboUnit.setMaximumWidth(40)
		self.updateUnitList(unit)
		#validator = QDoubleValidator(1,10,2,self);
		#input.setValidator(validator);
		self.updateFieldList(None,defaultValue)
		self.updateUnitList(unit)
		
		grid = QGridLayout()
		grid.setSpacing(2)
		grid.addWidget(self.label, 1, 0)
		grid.addWidget(self.comboField, 1, 1)
		grid.addWidget(self.comboUnit, 1, 2)
		
		self.setLayout(grid)
	
	def getValue(self):
		value = self.comboField.currentText()
		unit = self.comboUnit.currentText()
		if unit == '-':
			unit = None
			
		if unit == '':
			unit = None
		
		return (value,unit)
		
	def setValue(self,layerPath = None):
		#print 'setValue',layerPath, self.defaultValue,self.unit
		self.updateFieldList(layerPath, self.defaultValue)
		self.updateUnitList(self.unit)
	
	def setTitle(self,newTitle):
		self.label.setText(newTitle)
		
	def updateFieldList(self,layerPath = None, selectedItem= None):
		#print layerPath, selectedItem
		self.comboField.clear()
		if layerPath is not None:
			# get layer from registry
			for vlayer in QgsProject.instance().mapLayers().values():
				if vlayer.source() == layerPath:
					break
					
			#vlayer = QgsVectorLayer(layerPath, "new", "ogr")
			# get layer fields
			self.comboField.addItem('')
			for field in vlayer.fields():
				self.comboField.addItem(field.name())
		
		if selectedItem is not None:
			index = self.comboField.findText(selectedItem)
			#print index
			if index != -1:
				self.comboField.setCurrentIndex(index)
	
	def updateUnitList(self,selectedItem= None):
		self.comboUnit.clear()
		self.comboUnit.addItems(['-','km','m','cm','mm'])
		
		if selectedItem is None:
			self.comboUnit.setEnabled(False)
			selectedItem = '-'
		
		index = self.comboUnit.findText(selectedItem)
		self.comboUnit.setCurrentIndex(index)
			
class MultiListInput(QWidget):
	def __init__(self,labelString, itemArray,descr = ''):
		super(MultiListInput, self).__init__()
		self.label = QLabel(labelString)
		self.list = QListWidget(self)
		# populate items
		self.list.addItems(itemArray)
		self.list.setSelectionMode(3) # set multiple selection
		grid = QGridLayout()
		grid.setSpacing(10)
		grid.addWidget(self.label, 1, 0)
		grid.addWidget(self.list, 1, 1)
		
		self.setLayout(grid)
		
	def getValue(self):
		res = [ i.text() for i in self.list.selectedItems()]
		return res
	
	def setTitle(self,newTitle):
		self.label.setText(newTitle)
	
	def clearList(self):
		self.list.clear
	
	def addItem(self,item):
		self.list.addItem(item)

	
class ListInput(QWidget):
	def __init__(self,labelString, itemArray,descr = ''):
		super(ListInput, self).__init__()
		self.label = QLabel(labelString)
		self.list = QComboBox(self)
		# populate items
		for item in itemArray:
			print(item)
			self.list.addItem(item)
		grid = QGridLayout()
		grid.setSpacing(10)
		grid.addWidget(self.label, 1, 0)
		grid.addWidget(self.list, 1, 1)
		
		self.setLayout(grid)
		
	def getValue(self):
		return self.list.currentText()
	
	def setTitle(self,newTitle):
		self.label.setText(newTitle)
	
	def clearList(self):
		self.list.clear
	
	def addItem(self,item):
		self.list.addItem(item)
	
class CheckInput(QWidget):
	def __init__(self, labelString, defaultValue,descr = ''):
		super(CheckInput, self).__init__()
		self.setWhatsThis(descr)
		self.input = QCheckBox(labelString)
		self.input.setChecked(defaultValue)
		#self.label = QLabel(labelString)
		
		grid = QGridLayout()
		grid.setSpacing(10)
		grid.addWidget(self.input, 1, 0)
		#grid.addWidget(self.label, 1, 1)
		
		self.setLayout(grid)
		
	def getValue(self):
		return self.input.isChecked()
	
	def setTitle(self,newTitle):
		#self.label.setText(newTitle)
		self.input.setText(newTitle)
		
class FileInput(QWidget):
	def __init__(self, labelString, defaultValue, type,descr = ''):
		super(FileInput, self).__init__()
		self.setWhatsThis(descr)
		self.label = QLabel(labelString)
		self.input = QLineEdit()
		self.button = QPushButton()
		self.input.setText(str(defaultValue))
		grid = QGridLayout()
		grid.setSpacing(10)
		grid.addWidget(self.label, 1, 0)
		grid.addWidget(self.input, 1, 1)
		grid.addWidget(self.button, 1, 3)
		
		self.setLayout(grid)
		
		# link action
		if (type == 'openraster'): self.button.clicked.connect(self.openRaster)
		if (type == 'saveraster'): self.button.clicked.connect(self.saveRaster)
		if (type == 'openvector'): self.button.clicked.connect(self.openVector)
		if (type == 'opensqlite'): self.button.clicked.connect(self.openSqlite)
		if (type == 'opencsv'): self.button.clicked.connect(self.openCSV)
		
	def getValue(self):
		return self.input.text()
	
	def setTitle(self,newTitle):
		self.label.setText(newTitle)
	
	def openRaster(self):
		# open qgis file browser
		lastUsedFilter = Utils.FileFilter.lastUsedRasterFilter()
		inputFile = Utils.FileDialog.getOpenFileName( self, self.label.text(), Utils.FileFilter.allRastersFilter(), lastUsedFilter )
		# TODO
		print('debug',inputFile)
		inputFile = inputFile[0]
		if not inputFile:
			return
		Utils.FileFilter.setLastUsedRasterFilter( lastUsedFilter )
		# update input box
		self.input.setText(inputFile)
	
	def saveRaster(self):
		# open qgis file browser
		lastUsedFilter = Utils.FileFilter.lastUsedRasterFilter()
		inputFile = Utils.FileDialog.getSaveFileName( self, self.label.text(), Utils.FileFilter.saveRastersFilter(), lastUsedFilter )
		inputFile = inputFile[0]
		if not inputFile:
			return
		Utils.FileFilter.setLastUsedRasterFilter( lastUsedFilter )
		# update input box
		self.input.setText(inputFile)
	
	def openVector(self):
		# open qgis file browser
		lastUsedFilter = Utils.FileFilter.lastUsedVectorFilter()
		inputFile = Utils.FileDialog.getOpenFileName( self, self.label.text(), Utils.FileFilter.allVectorsFilter(), lastUsedFilter )
		inputFile = inputFile[0]
		if not inputFile:
			return
		Utils.FileFilter.setLastUsedRasterFilter( lastUsedFilter )
		# update input box
		self.input.setText(inputFile)
		
	def openSqlite(self):
		#inputFile = Utils.FileDialog.getOpenFileName( self, self.label.text(), 'sqlite(*.sqlite)', 'sqlite(*.sqlite)' )
		inputFile = QFileDialog.getOpenFileName(None, self.label.text(), '', 'sqlite(*.sqlite)')
		inputFile = inputFile[0]
		if not inputFile:
			return
		# update input box
		self.input.setText(inputFile)
		
	def openCSV(self):
		#inputFile = Utils.FileDialog.getOpenFileName( self, self.label.text(), 'sqlite(*.sqlite)', 'sqlite(*.sqlite)' )
		inputFile = QFileDialog.getOpenFileName(None, self.label.text(), '', 'Comma Separated Values (*.CSV)')
		inputFile = inputFile[0]
		if not inputFile:
			return
		# update input box
		self.input.setText(inputFile)

class LayerInput(QWidget):
	valueChanged = QtCore.pyqtSignal('QString')
	
	def __init__(self,labelString, descr = '', type = 'openvector'):
		super(LayerInput, self).__init__()
		self.label = QLabel(labelString)
		self.combo = QComboBox()
		self.updateComboList()
		self.button = QPushButton()
		self.button.setFixedSize(QtCore.QSize(22 ,22))
		self.button.setText('...')
				
		grid = QGridLayout()
		grid.setSpacing(1)
		grid.addWidget(self.label, 1, 0)
		#grid.addWidget(self.combo, 1, 1)
		#grid.addWidget(self.button, 1, 3)
		grid.addWidget(self.combo, 2, 0)
		grid.addWidget(self.button, 2, 1)
		
		self.setLayout(grid)
		
		# link action
		if (type == 'openraster'): self.button.clicked.connect(self.openRaster)
		if (type == 'saveraster'): self.button.clicked.connect(self.saveRaster)
		if (type == 'openvector'): self.button.clicked.connect(self.openVector)
		
		# connect signal
		self.combo.currentIndexChanged.connect(self.changeValueEmit)
	
	def changeValueEmit(self):
		self.valueChanged.emit(self.getValue())
		
	def updateComboList(self, selectedItem = None):
		# populate items
		#itemArray = [layer.name() for layer in QgsMapLayerRegistry.instance().mapLayers().values()]
		self.combo.clear()
		self.combo.addItem('')
		for layer in QgsProject.instance().mapLayers().values():
			self.combo.addItem(layer.name())
			if layer.source()== selectedItem:
				selectedItem = layer.name()
			
		if selectedItem is not None:
			index = self.combo.findText(selectedItem)
			if index != -1:
				self.combo.setCurrentIndex(index)
			
	
	def getValue(self):
		layName = self.combo.currentText()
		#print 'in LayerInput::getValue',layName
		value = None
		# if it is a complete file path that exist
		if osp.exists(layName):
			value = layName
		else:
			# else try looping in the layers list
			for layer in QgsProject.instance().mapLayers().values():
				if layer.name() == layName:
					value = layer.source()
				
		return value

	def setTitle(self,newTitle):
		self.label.setText(newTitle)

	def clearCombo(self):
		self.combo.clear

	def addItem(self,item):
		self.combo.addItem(item)
		
	def openRaster(self):
		# open qgis file browser
		lastUsedFilter = Utils.FileFilter.lastUsedRasterFilter()
		inputFile = Utils.FileDialog.getOpenFileName( self, self.label.text(), Utils.FileFilter.allRastersFilter(), lastUsedFilter )
		if not inputFile:
			return
		Utils.FileFilter.setLastUsedRasterFilter( lastUsedFilter )
		# upload layer
		
		# update input box
		self.updateComboList()
	
	def saveRaster(self):
		# open qgis file browser
		lastUsedFilter = Utils.FileFilter.lastUsedRasterFilter()
		inputFile = Utils.FileDialog.getSaveFileName( self, self.label.text(), Utils.FileFilter.saveRastersFilter(), lastUsedFilter )
		if not inputFile:
			return
		Utils.FileFilter.setLastUsedRasterFilter( lastUsedFilter )
		# update input box
		self.input.setText(inputFile)
	
	def openVector(self):
		# open qgis file browser
		lastUsedFilter = Utils.FileFilter.lastUsedVectorFilter()
		inputFile = Utils.FileDialog.getOpenFileName( self, self.label.text(), Utils.FileFilter.allVectorsFilter(), lastUsedFilter )
		if not inputFile:
			return
		Utils.FileFilter.setLastUsedRasterFilter( lastUsedFilter )
		# upload layer
		#vlayer = QgsVectorLayer(inputFile,osp.basename(inputFile), "ogr")
		# add layer to the registry
		#QgsMapLayerRegistry.instance().addMapLayer(vlayer)
		# update input box
		self.updateComboList()
		# add the new file to the list
		self.addItem(inputFile)
		
		
class VectorLayerInput(QWidget):
	valueChanged = QtCore.pyqtSignal('QString')
	
	def __init__(self,labelString, descr = '', type = 'any', showOpenFile = True):
		super(VectorLayerInput, self).__init__()
		# TODO: better fix for type selection
		if type in ['any','all']:
			self.type = [QgsWkbTypes.Unknown, QgsWkbTypes.Point,QgsWkbTypes.PointZ, QgsWkbTypes.LineString, QgsWkbTypes.Polygon,
						QgsWkbTypes.MultiPoint, QgsWkbTypes.MultiLineString, QgsWkbTypes.MultiLineStringZ, QgsWkbTypes.MultiPolygon,
						QgsWkbTypes.NoGeometry,
						QgsWkbTypes.Point25D, QgsWkbTypes.LineString25D, QgsWkbTypes.Polygon25D, QgsWkbTypes.MultiPoint25D, \
						QgsWkbTypes.MultiLineString25D, QgsWkbTypes.MultiPolygon25D ]
		elif type == 'point':
			self.type = [QgsWkbTypes.Point,QgsWkbTypes.PointZ, QgsWkbTypes.MultiPoint,QgsWkbTypes.Point25D,QgsWkbTypes.MultiPoint25D]
		elif type == 'line':
			self.type = [QgsWkbTypes.LineString, QgsWkbTypes.MultiLineString, QgsWkbTypes.MultiLineStringZ, QgsWkbTypes.LineString25D]
		elif type == 'polygon':
			self.type = [QgsWkbTypes.Polygon, QgsWkbTypes.MultiPolygon, QgsWkbTypes.Polygon25D, QgsWkbTypes.MultiPolygon25D ]
		else:
			print('not supported vector type')

		grid = QGridLayout()
		grid.setSpacing(1)
		
		self.label = QLabel(labelString)
		self.combo = QComboBox()
		self.updateComboList()
		
		grid.addWidget(self.label, 1, 0)
		grid.addWidget(self.combo, 2, 0)
		
		if showOpenFile:
			self.button = QPushButton()
			self.button.setFixedSize(QtCore.QSize(22 ,22))
			self.button.setText('...')
			grid.addWidget(self.button, 2, 1)
			self.button.clicked.connect(self.openVector)
		
		self.setLayout(grid)
		
		# connect signal
		self.combo.currentIndexChanged.connect(self.changeValueEmit)
	
	def changeValueEmit(self):
		self.valueChanged.emit(self.getValue())
		
	def updateComboList(self, selectedItem = None):
		# populate items
		#itemArray = [layer.name() for layer in QgsMapLayerRegistry.instance().mapLayers().values()]
		self.combo.clear()
		#self.combo.addItem('')
		items = ['']
		for layer in QgsProject.instance().mapLayers().values():
			if not isinstance(layer,QgsRasterLayer):
				if layer.wkbType() in self.type:
					#self.combo.addItem(layer.name())
					items.append(layer.name())
					if layer.source()== selectedItem:
						selectedItem = layer.name()
		# sort items
		items.sort()
		self.combo.addItems(items)
		
		if selectedItem is not None:
			index = self.combo.findText(selectedItem)
			if index != -1:
				self.combo.setCurrentIndex(index)
		
	def getValue(self):
		layName = self.combo.currentText()
		#print 'in LayerInput::getValue',layName
		value = None
		# if it is a complete file path that exist
		if osp.exists(layName):
			value = layName
		else:
			# else try looping in the layers list
			for layer in QgsProject.instance().mapLayers().values():
				if layer.name() == layName:
					value = layer.source()
					
		return value

	def setTitle(self,newTitle):
		self.label.setText(newTitle)

	def clearCombo(self):
		self.combo.clear

	def addItem(self,item):
		self.combo.addItem(item)
		
	def openVector(self):
		# open qgis file browser
		lastUsedFilter = Utils.FileFilter.lastUsedVectorFilter()
		inputFile = Utils.FileDialog.getOpenFileName( self, self.label.text(), Utils.FileFilter.allVectorsFilter(), lastUsedFilter )
		if not inputFile:
			return
		Utils.FileFilter.setLastUsedRasterFilter( lastUsedFilter )
		# upload layer
		#vlayer = QgsVectorLayer(inputFile,osp.basename(inputFile), "ogr")
		# add layer to the registry
		#QgsMapLayerRegistry.instance().addMapLayer(vlayer)
		# update input box
		self.updateComboList()
		# add the new file to the list
		self.addItem(inputFile)