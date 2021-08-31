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

from PyQt5.QtCore import QRect, QMetaObject,Qt
from PyQt5.QtWidgets import QDialog, QGridLayout, QDialogButtonBox

from .custom_input import NumericInput, StringInput, CheckInput,VectorLayerInput,FieldInput,ListInput


class CreateHyetographDialog(QDialog):
	def __init__(self,tr = None):
		QDialog.__init__(self)
				
		self.setObjectName("CreateHyetograph")
		self.setWindowTitle(self.tr('Create hyetograph'))
		self.resize(400, 100)
		
		grid = QGridLayout()
		grid.setSpacing(1)
		
		self.duration = NumericInput(self.tr('Duration (min)'),60,self.tr('The duration time of the rain event in minutes'))
		self.step = NumericInput(self.tr('Step (min)'),5,self.tr('The time step in minutes'))
		self.returnTime = NumericInput(self.tr('Return time (y)'),10,self.tr('The return time period in years'))
		self.method = ListInput(self.tr('method'),[self.tr('uniform'),self.tr('chicago')],self.tr('The method to use to build the time serie'))
		self.relativePeakTime = NumericInput(self.tr('Relative time of peak'),0.5,self.tr('The center of the rainfall event for Chicago method (0-1)'))
		self.serieName = StringInput(self.tr('Name'),self.tr('Something of meaningfull'),self.tr('The name to assign to the output serie'),True)
		self.useSelection = CheckInput(self.tr('Use selection'),False,self.tr('Make a time series for all the selected features'))
		self.updateLayer = CheckInput(self.tr('Update layer'),True,self.tr('Update table field in weather stations layer'))
		
		#~ grid.addWidget(self.weatherStationslayer, 1, 0)
		grid.addWidget(self.duration, 2,0)
		grid.addWidget(self.step, 3,0)
		grid.addWidget(self.returnTime, 4,0)
		grid.addWidget(self.method, 5,0)
		grid.addWidget(self.relativePeakTime, 6,0)
		grid.addWidget(self.serieName, 7,0)
		#~ grid.addWidget(self.useSelection, 8,0)
		grid.addWidget(self.updateLayer, 9,0)
		
		self.buttonBox = QDialogButtonBox(self)
		self.buttonBox.setGeometry(QRect(30, 240, 341, 32))
		self.buttonBox.setOrientation(Qt.Horizontal)
		self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
		self.buttonBox.setObjectName("buttonBox")
		
		grid.addWidget(self.buttonBox,10,0)
		
		self.setLayout(grid)
		
		self.buttonBox.accepted.connect(self.accept)
		self.buttonBox.rejected.connect(self.reject)
		QMetaObject.connectSlotsByName(self)
	
	def getParameterValue(self):
		m = self.method.getValue()
		if m == self.tr('uniform'):
			m = 'uniform'
		elif m == self.tr('chicago'):
			m = 'chicago'
		elif m == self.tr('alternating block'):
			m = 'alternatingblock'
		else:
			m = 'not defined'
		
		res = (self.duration.getValue(),self.step.getValue(),self.returnTime.getValue(),\
				m,self.relativePeakTime.getValue(),\
				self.serieName.getValue(),self.useSelection.getValue(),self.updateLayer.getValue())
		return res