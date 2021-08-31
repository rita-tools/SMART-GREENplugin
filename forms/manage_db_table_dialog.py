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

from custom_input import StringInput, ListInput, MultiListInput


class ManageDbTableDialog(QDialog):
	def __init__(self,driver,tr = None,tablenames = [],actionnames = []):
		QDialog.__init__(self) 
		
		self.driver = driver
		self.settings = driver.settings
		
		if tr is None:
			self.tr = lambda x: x
		else:
			self.tr = tr
				
		self.setObjectName("ManageDbTable")
		self.setWindowTitle(self.tr('Manage DB tables'))
		self.resize(400, 100)
		
		grid = QGridLayout()
		grid.setSpacing(1)
		
		# Add Numeric input widget
		self.dbpath = StringInput(self.tr('Database'), self.settings['qgis.dblite'][0],self.tr('Selected database'))
		self.dbpath.setEnabled(False) # make grayed
		self.tables = MultiListInput(self.tr('Tables'),tablenames,self.tr('Select one or more tables'))
		self.actions = ListInput(self.tr('Actions'),actionnames,self.tr('Select the action to do'))
		
		grid.addWidget(self.dbpath, 1, 0)
		grid.addWidget(self.tables, 2,0)
		grid.addWidget(self.actions, 3,0)
		
		self.buttonBox = QDialogButtonBox(self)
		self.buttonBox.setGeometry(QRect(30, 240, 341, 32))
		self.buttonBox.setOrientation(Qt.Horizontal)
		self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
		self.buttonBox.setObjectName("buttonBox")
		
		grid.addWidget(self.buttonBox,4,0)
		
		self.setLayout(grid)
		
		self.buttonBox.accepted.connect(self.accept)
		self.buttonBox.rejected.connect(self.reject)
		QMetaObject.connectSlotsByName(self)
		
	def getParameterValue(self):
		res = (self.dbpath.getValue(),\
				self.tables.getValue(),\
				self.actions.getValue(),)
		return res