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

from PyQt5.QtWidgets import QLineEdit, QLayout, QComboBox, QDialogButtonBox
from PyQt5.QtCore import Qt
from qgis.core import NULL

def formOpen(dialog,layerid,featureid):
	global myDialog
	myDialog = dialog
	global layer
	layer = layerid
	global feature
	feature = featureid
	
	# hide dummy QLineBox
	objStartFld = dialog.findChild(QLineEdit,'NODE_START')
	objEndFld = dialog.findChild(QLineEdit,'NODE_END')
	sShapeFld = dialog.findChild(QLineEdit,'S_SHAPE')
	tableFld = dialog.findChild(QLineEdit,'TABLE')
	objStartFld.setHidden(True)
	objEndFld.setHidden(True)
	sShapeFld.setHidden(True)
	tableFld.setHidden(True)
	
	# set fixed size
	dialog.layout().setSizeConstraint( QLayout.SetFixedSize )
	dialog.setWindowFlags(Qt.MSWindowsFixedSizeDialogHint)
	#dialog.setFixedSize(dialog.width(),dialog.height())
	
	#~ # polupate combos with value
	objStartCB = dialog.findChild(QComboBox,'NODE_START_CB')
	updateNodeItems(objStartCB, objStartFld)
	objStartCB.currentIndexChanged[str].connect(objStartFld.setText)
	
	objEndCB = dialog.findChild(QComboBox,'NODE_END_CB')
	updateNodeItems(objEndCB, objEndFld)
	objEndCB.currentIndexChanged[str].connect(objEndFld.setText)
	
	sShapeCB = dialog.findChild(QComboBox,'S_SHAPE_CB')
	updateShapeItems(sShapeCB,sShapeFld)
	#sShapeCB.currentIndexChanged[str].connect(hideShowElem)
	sShapeCB.currentIndexChanged[str].connect(sShapeFld.setText)
	
	tableCB = dialog.findChild(QComboBox,'TABLE_CB')
	updateTableItems(tableCB,tableFld)
	tableCB.currentIndexChanged[str].connect(tableFld.setText)
	
	if layer.isEditable():
		objStartCB.setEnabled(True)
		objEndCB.setEnabled(True)
		sShapeCB.setEnabled(True)
		tableCB.setEnabled(True)

def updateNodeItems(comboBox, lineEdit):
	# get unique value list from nodes --> obj_id
	DBM = qgis.utils.plugins['SMARTGREEN'].DBM
	lay = qgis.utils.plugins['SMARTGREEN'].getLayerBySource(DBM.getDefault('qgis.nodeslayer'))
	idx = lay.fields().indexFromName(DBM.getDefault('qgis.nodeslayer.field.obj_id'))
	values = list(lay.uniqueValues(idx))
	values = ['NULL']+values
	comboBox.addItems(['']+values)
	val = lineEdit.text()
	if val == NULL:
		val = ''
				
	index = comboBox.findText(val, Qt.MatchFixedString)
	if index >= 0:
		comboBox.setCurrentIndex(index)
	
def updateShapeItems(comboBox, lineEdit):
	values = ['NULL','C','R','E','N']
	comboBox.addItems(['']+values)
	
	val = lineEdit.text()
	
	if val == NULL:
		val = ''
		
	index = comboBox.findText(val, Qt.MatchFixedString)
	if index >= 0:
		comboBox.setCurrentIndex(index)
	
	
def updateTableItems(comboBox, lineEdit):
	#values = ['NULL','t1','t2','t3','t4']
	values = qgis.utils.plugins['SMARTGREEN'].getTableList()
	
	comboBox.addItems(['']+values)
	
	val = lineEdit.text()
	
	if val == NULL:
		val = ''
		
	index = comboBox.findText(val, Qt.MatchFixedString)
	if index >= 0:
		comboBox.setCurrentIndex(index)