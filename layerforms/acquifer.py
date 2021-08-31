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

from PyQt5.QtWidgets import QLineEdit, QComboBox, QDialogButtonBox
from qgis.core import *
from qgis.gui import *


def formOpen(dialog,layerid,featureid):
	global myDialog
	myDialog = dialog
		
	maFld = dialog.findChild(QLineEdit,'MA')
	maFld.setHidden(True)
	mfFld = dialog.findChild(QLineEdit,'MF')
	mfFld.setHidden(True)
	
	maCB = dialog.findChild(QComboBox,'MA_CB')
	updateYesNoItems(maCB, maFld)
	maCB.currentIndexChanged[str].connect(maFld.setText)
	
	mfCB = dialog.findChild(QComboBox,'MF_CB')
	updateYesNoItems(mfCB, mfFld)
	mfCB.currentIndexChanged[str].connect(mfFld.setText)
	
	flag = layerid.isEditable()
	maCB.setEnabled(flag)
	mfCB.setEnabled(flag)


def updateYesNoItems(comboBox, lineEdit):
	comboBox.addItems(['0','1'])
	val = lineEdit.text()
	
	if val == NULL:
		val = ''	
		
	index = comboBox.findText(val, QtCore.Qt.MatchFixedString)
	if index >= 0:
		comboBox.setCurrentIndex(index)