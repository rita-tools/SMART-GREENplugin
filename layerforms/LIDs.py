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

from PyQt5.QtWidgets import QLineEdit, QComboBox, QTabWidget, QDialogButtonBox, QLabel
from qgis.core import *
from qgis.gui import *

def formOpen(dialog,layerid,featureid):
	global myDialog
	myDialog = dialog
	global layer
	layer = layerid
	global feature
	feature = featureid
	
	# hide dummy QLineBox
	global typeFld
	typeFld = dialog.findChild(QLineEdit,'TYPE')
	typeFld.setHidden(True)
	
	global nodeToFld
	nodeToFld = dialog.findChild(QLineEdit,'NODE_TO')
	nodeToFld.setHidden(True)
	
	global catFld
	catFld = dialog.findChild(QLineEdit,'CAT')
	catFld.setHidden(True)
		
	# populate combos with value
	global typeCB
	typeCB = dialog.findChild(QComboBox,'TYPE_CB')
	updateTypeItems(typeCB)
	typeCB.currentIndexChanged[str].connect(updateTypeFld)
	typeCB.currentIndexChanged[str].connect(updateParamFld)
	updateSelected(typeCB, typeFld)
	
	global nodeToCB
	nodeToCB = dialog.findChild(QComboBox,'NODE_TO_CB')
	updateNodeItems(nodeToCB, nodeToFld)
	nodeToCB.currentIndexChanged[str].connect(updateNodetoFld)
	updateSelected(nodeToCB, nodeToFld)
	
	global catCB
	catCB = dialog.findChild(QComboBox,'CAT_CB')
	updateCatItems(catCB)
	catCB.currentIndexChanged[str].connect(updateCatFld)
	catCB.currentIndexChanged[str].connect(hideShowParameterFlds)
	updateSelected(catCB, catFld)
	# connect also catFld
	catFld.textChanged[str].connect(lambda: updateSelected(catCB, catFld))
	
	global idFld
	idFld = dialog.findChild(QLineEdit,'OBJ_ID')
	if layer.isEditable(): updateIdFld()
	
	# link editing layer status to function to enable combobox
	#layer.editingStarted.connect(enableCombo)
	#layer.editingStopped.connect(enableCombo)
	
	if layer.isEditable():
		nodeToCB.setEnabled(True)
		typeCB.setEnabled(True)
	else:
		nodeToCB.setEnabled(False)
		typeCB.setEnabled(False)
		
	# get label "icon " and load iMage
	#~ imageLabel = dialog.findChild(QLabel,'IMAGE')
	#~ pixmap = QPixmap('C:/Users/enrico/.qgis2/python/plugins/SMARTGREEN/ui/LIDs.jpg')
	#~ imageLabel.setPixmap(pixmap)
	
	# set current tab
	tabs = dialog.findChild(QTabWidget,'tabWidget')
	tabs.setCurrentIndex(0)

def __updateNodeItems(comboBox, lineEdit):
	# get unique value list from nodes --> obj_id
	DBM = qgis.utils.plugins['SMARTGREEN'].DBM
	lay = qgis.utils.plugins['SMARTGREEN'].getLayerBySource(DBM.getDefault('qgis.nodeslayer'))
	idx = lay.fields().indexFromName(DBM.getDefault('qgis.nodeslayer.field.obj_id'))
	values = list(lay.uniqueValues(idx))
	values = ['NULL']+values
	comboBox.addItems(['']+values)
	
def updateNodeItems(comboBox, lineEdit):
	if feature is not None:
		# get unique value list from nodes --> obj_id
		DBM = qgis.utils.plugins['SMARTGREEN'].DBM
		lay = qgis.utils.plugins['SMARTGREEN'].getLayerBySource(DBM.getDefault('qgis.nodeslayer'))
		# get list of nodes
		#~ idx = lay.fields().indexFromName(DBM.getDefault('qgis.nodeslayer.field.obj_id'))
		#~ objList = lay.uniqueValues(idx)
		# calculate distance from feature to nodes
		distList = []
		objList = []
		for node in lay.getFeatures():
			geom = feature.geometry()
			if geom:
				dist = int(geom.distance(node.geometry()))
				distList.append(dist)
				objList.append(node['OBJ_ID'])
			
		# order objList and distList from the closest
		objList[:] = [i for d,i in sorted(zip(distList,objList))]
		distList[:] = sorted(distList)
		
		allItems = ["{} [{} u.m.]".format(a_, b_) for a_, b_ in zip(objList,distList)]
		
		allItems  = ['NULL']+allItems 
		comboBox.addItems(['']+allItems)
	
def updateTypeItems(comboBox):
	#DBM = qgis.utils.plugins['SMARTGREEN'].DBM
	tr = qgis.utils.plugins['SMARTGREEN'].tr
	#lay = qgis.utils.plugins['SMARTGREEN'].getLayerBySource(DBM.getDefault('qgis.table.lidtypes'))
	#lay = qgis.utils.plugins['SMARTGREEN'].DBM.getTableAsLayer(DBM.getDefault('qgis.table.lidtypes'),'lidtypes')
	
	#~ allItems = []
	#~ for feat in lay.getFeatures():
		#~ allItems.append("{} [{}]".format(feat['OBJ_ID'], feat['NAME']))
	
	allItems = [tr('1 [barrel]'),tr('2 [drained well]'),tr('3 [drained barrel]'),tr('4 [green roof]'),tr('5 [permeable pavement]')]
	allItems  = ['','NULL']+allItems 
	comboBox.addItems(allItems)
	
def updateCatItems(comboBox):
	tr = qgis.utils.plugins['SMARTGREEN'].tr
	allItems = []
	allItems  = ['']+[tr('1 [Reservoir like]'),tr('2 [Soil like]')]
	comboBox.addItems(['']+allItems)
	
def __updateSelected(comboBox, lineEdit, addName = False):
	val = lineEdit.text()
	if val == NULL:
		val = ''
		
	if addName:
		DBM = qgis.utils.plugins['SMARTGREEN'].DBM
		#lay = qgis.utils.plugins['SMARTGREEN'].getLayerBySource(DBM.getDefault('qgis.table.lidtypes'))
		lay = qgis.utils.plugins['SMARTGREEN'].DBM.getTableAsLayer(DBM.getDefault('qgis.table.lidtypes'),'lidtypes')
		idx = lay.fields().indexFromName('OBJ_ID')
		keys = lay.uniqueValues(idx)
		idx = lay.fields().indexFromName('NAME')
		values = lay.uniqueValues(idx)
		
		allItems = ['','NULL']+["{} [{}]".format(a_, b_) for a_, b_ in zip(values,keys)]
		keys = ['','NULL']+keys
		val = allItems[keys.index(val)]

	index = comboBox.findText(val, QtCore.Qt.MatchStartsWith)
	if index >= 0:
		comboBox.setCurrentIndex(index)

def updateSelected(comboBox, lineEdit):
	val = lineEdit.text()
	if val == NULL:
		val = ''

	index = comboBox.findText(val, QtCore.Qt.MatchStartsWith)
	if index >= 0:
		comboBox.setCurrentIndex(index)

def updateTypeFld(txt):
	#id = txt[txt.find("[")+1:txt.find("]")]
	id = txt[0:txt.find(" ")]
	typeFld.setText(id)
	
def updateCatFld(txt):
	id = txt[0:txt.find(" ")]
	catFld.setText(id)
	
def updateParamFld():
	typeId = typeFld.text()
	#print 'typeId:',typeId
	if typeId == NULL: return
	if typeId == 'NULL': return
	if typeId == 'NUL': return
		
	# get parameters from the list of lids type
	DBM = qgis.utils.plugins['SMARTGREEN'].DBM
	#lay = qgis.utils.plugins['SMARTGREEN'].getLayerBySource(DBM.getDefault('qgis.table.lidtypes'))
	lay = qgis.utils.plugins['SMARTGREEN'].DBM.getTableAsLayer(DBM.getDefault('qgis.table.lidtypes'),'lidtypes')
	
	query = "\"%s\" LIKE '%s'"%('OBJ_ID',typeId)
	#print query
	expr = QgsExpression(query)
	record = QgsFeature()
	lay.getFeatures( QgsFeatureRequest( expr )).nextFeature(record)
	print('fields:',record.fields().names())
	
	# populate value
	fldList = ['CAT','VOL','HEIGHT','DIAM_OUT','HEIGHT_OUT','DEPTH','KS_SOIL','TETA_SAT','TETA_FC','TETA_WP','SLOPE','WP_MAX','KS_SUB']
	if layer.isEditable():
		for fldName in fldList:
			if fldName in record.fields().names():
				if not (record[fldName] == NULL):
					fld = myDialog.findChild(QLineEdit,fldName)
					fld.setText(str(record[fldName]))

def updateNodetoFld(txt):
	id = txt[0:txt.find(" ")]
	nodeToFld.setText(id)
	
def updateIdFld():
	val = idFld.text()
	
	if val == NULL:
		val = ''
		
	if val == 'NULL':
		val = ''
		
	if val == '':
		# update area field
		if feature:
			# get maximum value from table
			#~ DBM = qgis.utils.plugins['SMARTGREEN'].DBM
			#~ maxVal = DBM.getMaxValue('LIDs','OBJ_ID')
			#~ if maxVal =='':
				#~ maxVal = 1
			#~ elif maxVal is None:
				#~ maxVal = 1
			#~ else:
				#~ maxVal = int(maxVal)+1
			maxVal = 0
			for feat in layer.getFeatures():
				featId = int(feat['OBJ_ID'])
				if maxVal <featId: maxVal = featId
			
			maxVal+=1
			
			idFld.setText(str(maxVal))
			
def hideShowParameterFlds(self):
	cat = catFld.text()
	
	list1 = ['VOL','HEIGHT','DIAM_OUT','HEIGHT_OUT']
	list2 = ['DEPTH','KS_SOIL','TETA_SAT','TETA_FC','TETA_WP','SLOPE','WP_MAX']
	
	if cat in ['1','Reservoir']:
		hideList1 = False
		hideList2 = True
	else:
		hideList1 = True
		hideList2 = False
		
	for name in list1:
		fld = myDialog.findChild(QLineEdit,name)
		fld.setHidden(hideList1)
		lbl = myDialog.findChild(QLabel,name+'_LBL')
		lbl.setHidden(hideList1)
		
	for name in list2:
		fld = myDialog.findChild(QLineEdit,name)
		fld.setHidden(hideList2)
		lbl = myDialog.findChild(QLabel,name+'_LBL')
		lbl.setHidden(hideList2)
	
def enableCombo():
	if nodeToCB.isEnabled(): nodeToCB.setEnabled(False)
	else: nodeToCB.setEnabled(True)
	if typeCB.isEnabled(): typeCB.setEnabled(False)
	else: typeCB.setEnabled(True)
	if catCB.isEnabled(): catCB.setEnabled(False)
	else: catCB.setEnabled(True)