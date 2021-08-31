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

from PyQt5.QtCore import pyqtSignal, QMetaObject, QSettings
from PyQt5.QtWidgets import QDialog, QLineEdit, QCheckBox, QLabel
import inspect

from PyQt5 import uic

#qgis import
from qgis.core import *
from qgis.gui import *
#other
import os
import sys

import GdalTools_utils as Utils

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
	sys.path.insert(0, cmd_folder)


uiFilePath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'lid_params.ui'))
FormClass = uic.loadUiType(uiFilePath)[0]

class LidParams(QDialog,FormClass):

	closed = pyqtSignal()
	
	def __init__(self, DBM,nOfSelected = 0,parent = None):
		QDialog.__init__(self, parent)
		self.DBM = DBM
		self.setupUi(self)
		self.setWindowTitle(self.tr('SMARTGREEN - LID parameters'))
		
		# hide "dummy" field
		self.TYPE.setHidden(True)
		self.CAT.setHidden(True)
		
		# populate lists
		self.updateTypeItems(self.TYPE_CB)
		self.updateCatItems(self.CAT_CB)
		
		# update checkbox
		if nOfSelected==0:
			self.SELECTION_CB.setChecked(False)
			self.SELECTION_CB.setEnabled(False) 
			
		self.SELECTION_CB.setText(self.tr('Use selected features (%s)')%nOfSelected)
		
		# connect 
		self.TYPE_CB.currentIndexChanged[str].connect(self.updateTypeFld)
		self.TYPE_CB.currentIndexChanged[str].connect(self.updateParamFld)
		self.CAT_CB.currentIndexChanged[str].connect(self.updateCatFld)
		self.CAT_CB.currentIndexChanged[str].connect(self.hideShowParameterFlds)
		
		# connect also catFld
		self.CAT.textChanged[str].connect(lambda: self.updateSelected(self.CAT_CB, self.CAT))
	
		
		# set type to the first that starts with 1
		self.TYPE.setText('1')
		index = self.TYPE_CB.findText('1', QtCore.Qt.MatchStartsWith)
		if index >= 0:
			self.TYPE_CB.setCurrentIndex(index)
			self.CAT_CB.setCurrentIndex(index)
			self.updateParamFld() #populate parameters
			self.hideShowParameterFlds()
			
		# enable combos
		self.enableCombo()
		
		self.buttonBox.accepted.connect(self.accept)
		self.buttonBox.rejected.connect(self.reject)
		QMetaObject.connectSlotsByName(self)
		
	def closeEvent(self, event):
		self.closed.emit()
		
	def updateTypeItems(self,comboBox):
		allItems = [self.tr('1 [barrel]'),self.tr('2 [drained well]'),self.tr('3 [drained barrel]'),self.tr('4 [green roof]'),self.tr('5 [permeable pavement]')]
		comboBox.addItems(allItems)
		
	def updateCatItems(self,comboBox):
		allItems  = [self.tr('1 [Reservoir like]'),self.tr('2 [Soil like]')]
		comboBox.addItems(allItems)
		
	def updateTypeFld(self,txt):
		#id = txt[txt.find("[")+1:txt.find("]")]
		id = txt[0:txt.find(" ")]
		self.TYPE.setText(id)
		
	def updateCatFld(self,txt):
		id = txt[0:txt.find(" ")]
		self.CAT.setText(id)
		
	def updateSelected(self, comboBox, lineEdit):
		val = lineEdit.text()
		if val == NULL:
			val = ''

		index = comboBox.findText(val, QtCore.Qt.MatchStartsWith)
		if index >= 0:
			comboBox.setCurrentIndex(index)
		
	def updateParamFld(self):
		typeId = self.TYPE.text()
		if typeId == NULL: return
		if typeId == 'NULL': return
		if typeId == 'NUL': return
		
		lay = self.DBM.getTableAsLayer(self.DBM.getDefault('qgis.table.lidtypes'),'lidtypes')
		
		query = "\"%s\" LIKE '%s'"%('OBJ_ID',typeId)
		#print query
		expr = QgsExpression(query)
		record = lay.getFeatures( QgsFeatureRequest( expr )).next()
			
		# populate value
		fldList = ['CAT','VOL','HEIGHT','DIAM_OUT','HEIGHT_OUT','DEPTH','KS_SOIL','TETA_SAT','TETA_FC','TETA_WP','SLOPE','WP_MAX','KS_SUB']
		for fldName in fldList:
			val = record[fldName]
			if val == NULL:
				val = ''
				
			fld = self.findChild(QLineEdit,fldName)
			fld.setText(str(val))
				
				
	def getParameter(self):
		fldList = ['TYPE','CAT','VOL','HEIGHT','DIAM_OUT','HEIGHT_OUT','DEPTH','KS_SOIL','TETA_SAT','TETA_FC','TETA_WP','SLOPE','WP_MAX','KS_SUB']
		
		paramDict = {}
		
		for fldName in fldList:
			fld = self.findChild(QLineEdit,fldName)
			paramDict[fldName] = fld.text()
			
		# add also checkbox
		useSelection = self.findChild(QCheckBox,'SELECTION_CB')
		paramDict['USESELECTION'] = useSelection.isChecked()
		
		return paramDict
	
	def hideShowParameterFlds(self):
		cat = self.CAT.text()
		
		list1 = ['VOL','HEIGHT','DIAM_OUT','HEIGHT_OUT']
		list2 = ['DEPTH','KS_SOIL','TETA_SAT','TETA_FC','TETA_WP','SLOPE','WP_MAX']
		
		if cat in ['1','Reservoir']:
			hideList1 = False
			hideList2 = True
		else:
			hideList1 = True
			hideList2 = False
			
		for name in list1:
			fld = self.findChild(QLineEdit,name)
			fld.setHidden(hideList1)
			lbl = self.findChild(QLabel,name+'_LBL')
			lbl.setHidden(hideList1)
			
		for name in list2:
			fld = self.findChild(QLineEdit,name)
			fld.setHidden(hideList2)
			lbl = self.findChild(QLabel,name+'_LBL')
			lbl.setHidden(hideList2)
		
	def enableCombo(self):
		if self.TYPE_CB.isEnabled(): self.TYPE_CB.setEnabled(False)
		else: self.TYPE_CB.setEnabled(True)
		#~ if self.CAT_CB.isEnabled(): self.CAT_CB.setEnabled(False)
		#~ else: self.CAT_CB.setEnabled(True)