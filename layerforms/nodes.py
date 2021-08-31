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


from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLineEdit, QComboBox, QDialogButtonBox
from qgis.core import NULL

def formOpen(dialog,layerid,featureid):
	global myDialog
	myDialog = dialog
	global layer
	layer = layerid
	global feature
	feature = featureid
	
	# hide dummy QLineBox
	tableFld = dialog.findChild(QLineEdit,'TABLE')
	tableFld.setHidden(True)
	
	#~ # polupate combos with value
	
	tableCB = dialog.findChild(QComboBox,'TABLE_CB')
	updateTableItems(tableCB,tableFld)
	tableCB.currentIndexChanged[str].connect(tableFld.setText)
	
	if layer.isEditable():
		tableCB.setEnabled(True)

def updateTableItems(comboBox, lineEdit):
	values = qgis.utils.plugins['SMARTGREEN'].getTableList()
	comboBox.addItems(['']+values)
	
	val = lineEdit.text()
	
	if val == NULL:
		val = ''
		
	index = comboBox.findText(val, Qt.MatchFixedString)
	if index >= 0:
		comboBox.setCurrentIndex(index)