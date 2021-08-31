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
from PyQt5.QtWidgets import QDialog, QTabWidget, QDialogButtonBox, QGridLayout, QScrollArea, QWidget, QFormLayout, \
	QLabel, QLineEdit

from custom_input import NumericInput, CheckInput,LayerInput


class DefaultsDialog(QDialog):
	def __init__(self,driver):
		QDialog.__init__(self) 
		self.DBM = driver
		self.nameList = []
				
		self.setObjectName("SetDefaults")
		self.setWindowTitle(self.tr('Set default values'))
		self.resize(400, 300)
		
		self.constants = [('param_value.gamma___',self.tr('Percolation (1/s)'),self.tr('Percolation coefficient (1/s)')),\
								('param_value.kappa___',self.tr('Adsorption (1/s)'),self.tr('Adsorption coefficient (1/s)')),\
								('param_value.beta____',self.tr('Hypodermic flow (1/s)'),self.tr('Hypodermic flow coefficient (1/s)')),\
								('param_value.alpha___',self.tr('Hillslope flow (1/s)'),self.tr('Hillslope flow coefficient (1/s)')),\
								('param_value.CHfac___',self.tr('Turbulent exchange (-)'),self.tr('Multiplying factor of turbulent exchange coeff. for heat (-)')),\
								('param_value.chafac__',self.tr('Fraction of channalized flow (-)'),self.tr('Scale factor for fraction of channalized flow (-)')),\
								('param_value.Tcost___',self.tr('Deep ground temperature (K)'),self.tr('Deep ground temperature (K)')),\
								('param_value.kaps____',self.tr('Soil thermal conductivity (W/mK)'),self.tr('Soil thermal conductivity (W/mK)')),\
								('param_value.nis_____',self.tr('Soil thermal diffusivity (m^2/s)'),self.tr('Soil thermal diffusivity (m^2/s)')),\
								('param_value.wcel____',self.tr('Flood wave celerity (m/s)'),self.tr('Flood wave celerity in channels (m/s)')),\
								('param_value.celerfac',self.tr('Wave celerity (-)'),self.tr('Scale factor for wave celerity in channels (-)')),\
								('param_value.Br0_____',self.tr('Width of channels (-)'),self.tr('Width of channels with first Strahler order (-)')),\
								('param_value.NBr_____',self.tr('Width channel order relation'),self.tr('Exponent of the realtion B=O^N, where B=Width of channels and O=Strahler order (positive number > 1)')),\
								('param_value.n_Man___',self.tr('Channels Manning roughness'),self.tr('Manning roughness coefficient for channels (s/m^(1/3))')),\
								('param_value.glo_loss',self.tr('Global water loss (m^3/s)'),self.tr('Global water loss from aquifers (m^3/s)'))]
			
		self.hydraDefaults = [('param_default.shape_urban',self.tr('Section shape'),self.tr('Section shape (code)')),\
										('param_default.size_urban',self.tr('Conduit diameter (m)'),self.tr('Conduit diameter (m)')),\
										('param_default.min_diam',self.tr('Min conduit diameter (m)'),self.tr('Minimum conduit diameter (m)')),\
										('param_default.max_diam',self.tr('Max conduit diameter (m)'),self.tr('Maximum conduit diameter (m)')),\
										('param_default.L_urban',self.tr('Conduit length (m)'),self.tr('Conduit length (m)')),\
										('param_default.mann_urban',self.tr('Conduit roughness'),self.tr('Conduit Manning\'s coefficient')),\
										('param_default.yfull_urban',self.tr('Node depth (m)'),self.tr('Default node depth (m)')),\
										('param_default.nodearea_urban',self.tr('Node area (m^2)'),self.tr('Default node area (m^2)')),\
										('param_default.conduit_slope',self.tr('Conduit slope (m/m)'),self.tr('Default conduit slope to use if start and end elevation are not provided (m/m)'))]
										
		self.hydroDefaults = [('param_default.Wg0',self.tr('Large pore (mm)'),self.tr('Large pore water holding capacity (mm)')),\
										('param_default.Wc0',self.tr('Small pore (mm)'),self.tr('Small pore water holding capacity (mm)')),\
										('param_default.Wp0',self.tr('Interception (mm)'),self.tr('Interception (mm)')),\
										('param_default.ks',self.tr('Soil conductivity (mm/h)'),self.tr('Soil hydraulic conductivity (mm/h)')),\
										('param_default.kf',self.tr('Acquifer conductivity (mm/s)'),self.tr('Acquifer conductivity (mm/s)')),\
										('param_default.CH',self.tr('Turbulent exchange (-)'),self.tr('Turbulent exchange coefficient (-)')),\
										('param_default.Alb',self.tr('Albedo (-)'),self.tr('Albedo (-)'))]
		
		self.simSettings = [('project_name',self.tr('Project name'),self.tr('Project name')),\
									('project_descr',self.tr('Project description'),self.tr('Project description')),\
									('urban.simlength',self.tr('Simulation duration (hours)'),self.tr('Simulation duration in hours')),\
									('basestep',self.tr('Simulation base step (sec)'),self.tr('Simulation base step (in seconds)')),\
									('urban.dt',self.tr('Resolution time step (sec)'),self.tr('Time used during iteration (in seconds)')),\
									('initinfo.ws',self.tr('Initial runoff depth (m)'),self.tr('Initial depth of hillsope runoff (m)')),\
									('initinfo.wcsat',self.tr('Initial relative saturation of capillary soil (-)'),self.tr('Initial relative saturation of capillary soil (-)')),\
									('initinfo.wgsat',self.tr('Initial relative saturation of gravitational soil (-)'),self.tr('Initial relative saturation of gravitational soil (-)')),\
									('qgis.cellsize',self.tr('Cell size (map unit)'),self.tr('Dimension of the discretization cell')),\
									('realtime',self.tr('Overwrite interpolated data'),self.tr('Overwrite interpolated data: 0=NO, 1=YES, -1=CALIBRATION (avoid re-interpolation)'))]
																		
		self.toolSettings = [('qgis.bufferdistance',self.tr('Buffer distance (map unit)'),self.tr('Buffer distance to use to create subcatchments')),\
									('qgis.buffersegments',self.tr('Buffer segments'),self.tr('Buffer segments number to use to create subcatchments'))]
		
		
		# create tab form
		self.settingsTab = QTabWidget()
		
		# initialize tab
		self.setupTab(tabName = self.tr("Physical constants"),paramList=self.constants)
		self.setupTab(tabName = self.tr("Hydraulic"),paramList=self.hydraDefaults)
		self.setupTab(tabName = self.tr("Hydrology"),paramList=self.hydroDefaults)
		self.setupTab(tabName = self.tr("Simulation settings"),paramList=self.simSettings)
		self.setupTab(tabName = self.tr("Tools options"),paramList=self.toolSettings)
		
		# add button
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

	def setupTab(self,tabName,paramList):
		tab = QScrollArea()
		tab.setWidget(QWidget())
		tab_layout = QFormLayout(tab.widget())
		tab.setWidgetResizable(True)

		for param in paramList:
			labValue = QLabel(param[1])
			labValue.setWhatsThis(param[2])
			textValue = QLineEdit()
			textValue.setObjectName(param[0])
			paramVal = self.DBM.getDefault(param[0])
			if type(paramVal) is float:
				paramVal = str(self.DBM.getDefault(param[0]))
			else:
				#paramVal = self.DBM.getDefault(param[0]).encode('utf-8')
				paramVal = self.DBM.getDefault(param[0])
			
				
			textValue.setText(paramVal)
			# connect to update
			#textValue.updateList
			tab_layout.addRow(labValue,textValue)
		
		self.settingsTab.addTab(tab, tabName)
		
	def updateList(self,paramFld):
		self.nameList.append(paramFld.objectName())
		
	def updateFromList(self,paramList):
		for param in paramList:
			paramFld = self.findChild(QLineEdit,param[0])
			paramValue = str(paramFld.text())
			# update value
			self.DBM.setDefault(param[0],paramValue)
		
	def updateValues(self):
		self.updateFromList(self.constants)
		self.updateFromList(self.hydraDefaults)
		self.updateFromList(self.hydroDefaults)
		self.updateFromList(self.simSettings)
		self.updateFromList(self.toolSettings)
