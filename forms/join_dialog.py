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

from PyQt5.QtCore import QRect, QMetaObject, Qt
from PyQt5.QtWidgets import QDialog, QGridLayout, QDialogButtonBox

from custom_input import NumericInput, CheckInput,VectorLayerInput,FieldInput


class JoinDialog(QDialog):
	def __init__(self,driver,tr = None):
		QDialog.__init__(self) 
		
		self.driver = driver
		self.settings = driver.settings
		
		if tr is None:
			self.tr = lambda x: x
		else:
			self.tr = tr
				
		self.setObjectName("JoinTable")
		self.setWindowTitle(self.tr('Join table'))
		self.resize(400, 100)
		
		grid = QGridLayout()
		grid.setSpacing(1)
		
		# Add Numeric input widget
		self.toLayer = VectorLayerInput(self.tr('Join to layer'),self.tr('A layer to apply join table'),\
									type = 'any', showOpenFile = False)
		self.toLayerField = FieldInput('Layer id','','The field of the layer that contains the identifier',None)
		
		self.fromTable = VectorLayerInput(self.tr('Join from table'),self.tr('A table to use as source in the join'),\
									type = 'any', showOpenFile = False)
		self.fromTableField = FieldInput('Table id','','The field of the table that contains the identifier',None)
		
		self.fromTableValue = FieldInput('Table id','','The field of the table that contains the identifier',None)
		
		grid.addWidget(self.toLayer, 1, 0)
		grid.addWidget(self.toLayerField, 2,0)
		grid.addWidget(self.fromTable, 3, 0)
		grid.addWidget(self.fromTableField, 4,0)
		grid.addWidget(self.fromTableValue, 5,0)
		
		self.buttonBox = QDialogButtonBox(self)
		self.buttonBox.setGeometry(QRect(30, 240, 341, 32))
		self.buttonBox.setOrientation(Qt.Horizontal)
		self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
		self.buttonBox.setObjectName("buttonBox")
		
		grid.addWidget(self.buttonBox,6,0)
		
		self.setLayout(grid)
		
		# connect
		self.toLayer.valueChanged.connect(self.toLayerField.setValue )
		self.fromTable.valueChanged.connect(self.fromTableField.setValue )
		self.fromTable.valueChanged.connect(self.fromTableValue.setValue )
		
		#update value based on current default
		self.toLayer.updateComboList('')
		self.fromTable.updateComboList('')
		
		self.buttonBox.accepted.connect(self.accept)
		self.buttonBox.rejected.connect(self.reject)
		QMetaObject.connectSlotsByName(self)
	
	def createFieldInput(self,key):
		#return FieldInput(self.settings[key][1],self.settings[key][0],self.settings[key][2],self.settings[key][5])
		pass
		
	def updateValues(self):
		# update network tab
		#~ self.driver.updateValue('qgis.soilslayer',self.nodelayer.getValue())
		#~ self.driver.updateValue( 'qgis.soilslayer.field.soil_id',self.field_node_id.getValue())
		pass
		
	def getParameterValue(self):
		res = (self.toLayer.getValue(),self.toLayerField.getValue()[0],self.fromTable.getValue(),
			   self.fromTableField.getValue()[0],self.fromTableValue.getValue()[0])
		return res