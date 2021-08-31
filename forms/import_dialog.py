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
from PyQt5.QtWidgets import QDialog, QGridLayout, QDialogButtonBox, QMessageBox

from .custom_input import VectorLayerInput,FieldInput
from collections import OrderedDict
import os.path as osp


class ImportDialog(QDialog):
	def __init__(self,title,layType,settings,importTableName,tr=None):
		QDialog.__init__(self) 
		
		self.settings = settings
		
		if tr is not None:
			self.tr = tr
		
		self.setObjectName("ImportDialog")
		self.setWindowTitle(title)
		self.resize(400, 400)
		self.grid = QGridLayout()
		self.grid.setSpacing(1)
		# Add Numeric input widget
		self.inputlayer = VectorLayerInput(self.tr('Import from'),self.tr('Choose a layer'),\
									type = layType, showOpenFile = False)
		self.row = 0
		self.grid.addWidget(self.inputlayer,self.row,0)
		self.row+=1
		# Add other field based on file table
		self.initFromTable(importTableName)
		# Add buttons box
		self.buttonBox = QDialogButtonBox(self)
		self.buttonBox.setGeometry(QRect(30, 240, 341, 32))
		self.buttonBox.setOrientation(Qt.Horizontal)
		self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
		self.buttonBox.setObjectName("buttonBox")
		
		self.grid.addWidget(self.buttonBox,self.row,0)
		
		self.setLayout(self.grid)
		
		self.buttonBox.accepted.connect(self.accept)
		self.buttonBox.rejected.connect(self.reject)
		QMetaObject.connectSlotsByName(self)
		
	def initFromTable(self,filename, skipLines = 1, column_sep = ';'):
		# check if file exists, otherwise exit
		
		if not osp.isfile(filename):
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Critical)
			msg.setText(self.tr('Cannot load import settings'))
			msg.setInformativeText(self.tr('Cannot find %s') %(osp.basename(filename)))
			msg.setWindowTitle('SMARTGREEN')
			msg.setDetailedText(self.tr('Import function requires that %s exist in %s')%(osp.basename(filename),osp.dirname(filename)))
			msg.setStandardButtons(QMessageBox.Ok)
			msg.exec_()
			return
			
		in_file = open(filename,"r")
		i = 0
		while 1:
			in_line = in_file.readline()
			if len(in_line) == 0:
				break
			
			if in_line[0] == '#':
				i = 0 # make valid line counter to zero
				pass # skip comments
			else:
				# process the line
				in_line = in_line[:-1]
				#print 'LN %d: %s'%(i,in_line)
				values = in_line.split(column_sep)
				if i < skipLines:
					# first is column name
					pass # skip lines
				else:
					#add new field
					#print 'values:',values
					id,val,name,descr = self.settings.getDefaultRecord(values[0])
					customFld = FieldInput(values[0],self.tr(name),values[1],self.tr(descr),values[2])
					self.grid.addWidget(customFld, self.row, 0)
					self.inputlayer.valueChanged.connect(customFld.setValue )
					self.row +=1
					
			i+=1
			
	def getValues(self):
		res = OrderedDict()
		res['importFromLayer'] = self.inputlayer.getValue()
		items = (self.grid.itemAt(i).widget() for i in range(self.grid.count())) 
		for w in items:
			if isinstance(w, FieldInput):
				res[w.objectName()] = w.getValue()
				
		return res
				