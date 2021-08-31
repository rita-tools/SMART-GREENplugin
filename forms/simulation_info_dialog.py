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

from .custom_input import StringInput

from qgis.gui import *

import os


class SimulationInfoDialog(QDialog):
	def __init__(self):
		QDialog.__init__(self) 
		
		self.setObjectName("NewProject")
		self.resize(400, 300)
		self.setWindowTitle(self.tr("SMARTGREEN - new simulation"))
		
		# create input box
		self.prjName = StringInput(self.tr('Name:'),self.tr('Something of meaningful'),
								   self.tr('Write here the name of the simulation'))
		self.descrName = StringInput(self.tr('Description:'),self.tr('Something of meaningful'),
									 self.tr('Write here the description of the simulation'),False)
		
		self.buttonBox = QDialogButtonBox(self)
		self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
		self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
		self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
		self.buttonBox.setObjectName("buttonBox")
		
		grid = QGridLayout()
		grid.setSpacing(1)

		grid.addWidget(self.prjName, 1, 0)
		grid.addWidget(self.descrName, 2,0)
		grid.addWidget(self.buttonBox,3,0)
		
		self.setLayout(grid)

		self.buttonBox.accepted.connect(self.accept)
		self.buttonBox.rejected.connect(self.reject)
		QMetaObject.connectSlotsByName(self)
		
	def getValues(self):
		prjName = str(self.prjName.getValue())
		descrName = str(self.descrName.getValue())
		
		return prjName,descrName
