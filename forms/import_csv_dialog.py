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

from PyQt5.QtCore import QMetaObject
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QGridLayout

from .custom_input import NumericInput, CheckInput,LayerInput,StringInput,FileInput,ListInput

from qgis.core import *
from qgis.gui import *

import os


class ImportCsvDialog(QDialog):
	def __init__(self,driver):
		QDialog.__init__(self) 
		
		self.driver = driver
		
		self.setObjectName('importcsv')
		self.setWindowTitle(self.tr('Import from CSV'))
		
		self.resize(400, 300)
		
		# create input box
		self.fileName = FileInput(self.tr('File name'),'','opencsv',self.tr('Import time series from a CSV file'))
		self.colSep = ListInput(self.tr('Separator'), ['tab',',',';',' '],self.tr('Select character that separates columns'))
		self.headerExist = CheckInput(self.tr('Header'), True,self.tr('First row is the header'))
		
		self.buttonBox = QDialogButtonBox(self)
		self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
		self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
		self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
		self.buttonBox.setObjectName("buttonBox")
		
		grid = QGridLayout()
		grid.setSpacing(1)

		grid.addWidget(self.fileName, 1, 0)
		grid.addWidget(self.colSep, 2, 0)
		grid.addWidget(self.headerExist, 3, 0)
		grid.addWidget(self.buttonBox,4,0)
		
		self.setLayout(grid)

		self.buttonBox.accepted.connect(self.accept)
		self.buttonBox.rejected.connect(self.reject)
		QMetaObject.connectSlotsByName(self)

	def updateValues(self):
		# update settings
		pass
		
	def getParameterValue(self):
		return [self.fileName.getValue(),self.colSep.getValue(),self.headerExist.getValue()]