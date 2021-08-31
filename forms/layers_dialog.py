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
from PyQt5.QtWidgets import QDialog, QTabWidget, QWidget, QDialogButtonBox, QGridLayout

from custom_input import NumericInput, CheckInput,LayerInput,FieldInput


class LayersDialog(QDialog):
	def __init__(self,driver,tr = None):
		QDialog.__init__(self) 
		
		self.driver = driver
		self.settings = driver.settings
		
		if tr is None:
			self.tr = lambda x: x
		else:
			self.tr = tr
				
		self.setObjectName("SetLayers")
		self.setWindowTitle(self.tr('Set layers'))
		self.resize(400, 400)
		
		# create tab form
		self.settingsTab = QTabWidget()
		self.tab1 = QWidget()
		self.tab2 = QWidget()
		self.tab3 = QWidget()
		self.tab4 = QWidget()
		self.tab5 = QWidget()
		self.tab6 = QWidget()
		
		self.settingsTab.addTab(self.tab1,self.tr("Network"))
		self.settingsTab.addTab(self.tab2,self.tr("Nodes"))
		self.settingsTab.addTab(self.tab3,self.tr("Landuse"))
		self.settingsTab.addTab(self.tab4,self.tr("Soils"))
		self.settingsTab.addTab(self.tab5,self.tr("Weather Stations"))
		self.settingsTab.addTab(self.tab6,self.tr("Green infrastructures"))
		
		# initialize tab
		self.tab1UI()
		self.tab2UI()
		
		self.buttonBox = QDialogButtonBox(self)
		self.buttonBox.setGeometry(QRect(30, 240, 341, 32))
		self.buttonBox.setOrientation(Qt.Horizontal)
		self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
		self.buttonBox.setObjectName("buttonBox")
		
		grid = QGridLayout()
		grid.setSpacing(1)
		grid.addWidget(self.settingsTab,1,0)
		grid.addWidget(self.buttonBox,2,0)
		
		self.setLayout(grid)
		
		self.buttonBox.accepted.connect(self.accept)
		self.buttonBox.rejected.connect(self.reject)
		QMetaObject.connectSlotsByName(self)

	def tab1UI(self):
		grid = QGridLayout()
		grid.setSpacing(1)
		# Add Numeric input widget
		self.networklayer = LayerInput(self.settings['qgis.networklayer'][1],self.settings['qgis.networklayer'][2])
		self.field_net_id = self.createFieldInput('qgis.networklayer.field.net_id')
		self.field_obj_start = self.createFieldInput('qgis.networklayer.field.obj_start')
		self.field_obj_end = self.createFieldInput('qgis.networklayer.field.obj_end')
		self.field_s_shape = self.createFieldInput('qgis.networklayer.field.s_shape')
		self.field_diam = self.createFieldInput('qgis.networklayer.field.diam')
		self.field_heigth = self.createFieldInput('qgis.networklayer.field.heigth')
		self.field_width = self.createFieldInput('qgis.networklayer.field.width')
		self.field_elev_start = self.createFieldInput('qgis.networklayer.field.elev_start')
		self.field_elev_end = self.createFieldInput('qgis.networklayer.field.elev_end')
		self.field_mat = self.createFieldInput('qgis.networklayer.field.mat')
		self.field_length = self.createFieldInput('qgis.networklayer.field.length')

		grid.addWidget(self.networklayer, 1, 0)
		grid.addWidget(self.field_net_id, 2,0)
		grid.addWidget(self.field_obj_start, 3,0)
		grid.addWidget(self.field_obj_end, 4,0)
		grid.addWidget(self.field_s_shape, 5,0)
		grid.addWidget(self.field_diam, 6,0)
		grid.addWidget(self.field_heigth, 7,0)
		grid.addWidget(self.field_width, 8,0)
		grid.addWidget(self.field_elev_start, 9,0)
		grid.addWidget(self.field_elev_end, 10,0)
		grid.addWidget(self.field_mat, 11,0)
		grid.addWidget(self.field_length, 12,0)
		
		self.tab1.setLayout(grid)
		
		self.networklayer.valueChanged.connect(self.field_net_id.setValue )
		self.networklayer.valueChanged.connect(self.field_obj_start.setValue )
		self.networklayer.valueChanged.connect(self.field_obj_end.setValue )
		self.networklayer.valueChanged.connect(self.field_s_shape.setValue )
		self.networklayer.valueChanged.connect(self.field_diam.setValue )
		self.networklayer.valueChanged.connect(self.field_heigth.setValue )
		self.networklayer.valueChanged.connect(self.field_width.setValue )
		self.networklayer.valueChanged.connect(self.field_elev_start.setValue )
		self.networklayer.valueChanged.connect(self.field_elev_end.setValue )
		self.networklayer.valueChanged.connect(self.field_mat.setValue )
		self.networklayer.valueChanged.connect(self.field_length.setValue )
		
		#update value based on current default
		#print 'in tab1UI',self.settings['qgis.networklayer'][0]
		self.networklayer.updateComboList(self.settings['qgis.networklayer'][0])
		
	def tab2UI(self):
		grid = QGridLayout()
		grid.setSpacing(1)
		
		# Add Numeric input widget
		self.nodeslayer = LayerInput(self.settings['qgis.nodeslayer'][1],self.settings['qgis.nodeslayer'][2])
		self.field_node_id = self.createFieldInput('qgis.nodeslayer.field.node_id')
		self.field_elev_bot = self.createFieldInput('qgis.nodeslayer.field.elev_bot')
		self.field_elev_top = self.createFieldInput('qgis.nodeslayer.field.elev_top')
		
		grid.addWidget(self.nodeslayer, 1, 0)
		grid.addWidget(self.field_node_id, 2,0)
		grid.addWidget(self.field_elev_bot, 3,0)
		grid.addWidget(self.field_elev_top, 4,0)
		
		self.tab2.setLayout(grid)
		
		self.nodeslayer.valueChanged.connect(self.field_node_id.setValue )
		self.nodeslayer.valueChanged.connect(self.field_elev_bot.setValue )
		self.nodeslayer.valueChanged.connect(self.field_elev_top.setValue )
				
		#update value based on current default
		#print 'in tab1UI',self.settings['qgis.networklayer'][0]
		self.nodeslayer.updateComboList(self.settings['qgis.nodeslayer'][0])
		
	def createFieldInput(self,key):
		return FieldInput(self.settings[key][1],self.settings[key][0],self.settings[key][2],self.settings[key][5])
		
	def updateValues(self):
		# update network tab
		self.driver.updateValue('qgis.networklayer',self.networklayer.getValue())
		self.driver.updateValue( 'qgis.networklayer.field.net_id',self.field_net_id.getValue())
		self.driver.updateValue( 'qgis.networklayer.field.obj_start', self.field_obj_start.getValue())
		self.driver.updateValue( 'qgis.networklayer.field.obj_end', self.field_obj_end.getValue())
		self.driver.updateValue( 'qgis.networklayer.field.s_shape', self.field_s_shape.getValue())
		self.driver.updateValue( 'qgis.networklayer.field.diam', self.field_diam.getValue())
		self.driver.updateValue( 'qgis.networklayer.field.heigth', self.field_heigth.getValue())
		self.driver.updateValue( 'qgis.networklayer.field.width', self.field_width.getValue())
		self.driver.updateValue( 'qgis.networklayer.field.elev_start', self.field_elev_start.getValue())
		self.driver.updateValue( 'qgis.networklayer.field.elev_end', self.field_elev_end.getValue())
		self.driver.updateValue( 'qgis.networklayer.field.mat', self.field_mat.getValue())
		self.driver.updateValue( 'qgis.networklayer.field.length', self.field_length.getValue())
		# update node tab
		self.driver.updateValue('qgis.nodeslayer',self.nodeslayer.getValue())
		self.driver.updateValue( 'qgis.nodeslayer.field.node_id', self.field_node_id.getValue())
		self.driver.updateValue( 'qgis.nodeslayer.field.elev_bot', self.field_elev_bot.getValue())
		self.driver.updateValue( 'qgis.nodeslayer.field.elev_top', self.field_elev_top.getValue())
		

