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

import os
import os.path as osp
from os.path import dirname, join, exists, abspath, isfile, basename
import sys
import inspect
from shutil import copyfile
import numpy as np
import glob
import operator

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QTableView, QAbstractItemView, QVBoxLayout, QHBoxLayout, QTreeWidget, QTabWidget, \
	QSplitter, QMainWindow, QAction, QMenu, QFileDialog, QMessageBox, QInputDialog, QTreeWidgetItem
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

class DataTableWidget(QWidget):
	def __init__(self, parent=None,secondAxis = True):
		QWidget.__init__(self) 
		
		# table view
		self.arrayView = QTableView()
		self.arrayView.setSelectionBehavior(QAbstractItemView.SelectItems)
		self.arrayView.setAlternatingRowColors(True)
		# add layout
		layout = QVBoxLayout()
		layout.addWidget(self.arrayView)
		self.setLayout(layout)
		

class ChartWidget(QWidget):
	def __init__(self, parent=None,secondAxis = True):
		QWidget.__init__(self) 
		
		# a figure instance to plot on
		self.figure = plt.figure()
		
		# this is the Canvas Widget that displays the `figure`
		# it takes the `figure` instance as a parameter to __init__
		self.canvas = FigureCanvas(self.figure)
		
		# this is the Navigation widget
		# it takes the Canvas widget and a parent
		self.toolbar = NavigationToolbar(self.canvas, self)

		# set the layout
		layout = QVBoxLayout()
		layout.addWidget(self.toolbar)
		layout.addWidget(self.canvas)
		self.setLayout(layout)
		
		self.plotList = []
		self.ax = self.figure.add_subplot(111)
		
		#self.ax2 = self.ax.twinx()
		if secondAxis: self.ax2 = self.ax.twinx()
				
		#legend = self.ax.legend(loc='upper center', shadow=True)
		self.h = []
		self.l = []
		
	def setAxes(self, xlabs = None, ylabs = None, xTitle = None, yTitle = None, y2Title = None, mainTitle = None):
		#self.ax.subplots_adjust(left=2.0, right=2.0)
		if xlabs is not None: self.ax.set_xticklabels(xlabs)
		if ylabs is not None: self.ax.set_yticklabels(ylabs)
		if mainTitle is not None: self.ax.set_title(mainTitle)
		if xTitle is not None: self.ax.set_xlabel(xTitle)
		if yTitle is not None: self.ax.set_ylabel(yTitle)
		if y2Title is not None: self.ax2.set_ylabel(y2Title)
		
		#ax.set_xticks(ind + width / 2)
		plt.tight_layout()
		
	def addBarPlot(self,x,y,width=1,color='b',name = 'barplot'):
		
		# add some text for labels, title and axes ticks
		bars = self.ax.bar(x, y, width=width, color=color, edgecolor='white')
		self.plotList.append(bars)
		
		self.h.append(bars)
		self.l.append(name)
		#self.ax.legend(self.h, self.l)
		#~ h, l = self.ax.get_legend_handles_labels()
		#~ h += (bars,)
		#~ l += (name,)
		#self.ax.legend(h, l)
		
	def addLinePlot(self,x,y,lineType='-',color='r',name = 'lineplot',yaxis = 1):
		if yaxis == 1:
			lines, = self.ax.plot(x,y, lineType,color=color)
			#cursor1 = FollowDotCursor(self.ax, x, y)
		else:
			lines, = self.ax2.plot(x,y, lineType,color=color)
			#cursor1 = FollowDotCursor(self.ax2, x, y)
				
		self.plotList.append(lines)
		self.h.append(lines)
		self.l.append(name)
		if yaxis == 1:
			self.ax.legend(self.h, self.l)
		else:
			self.ax2.legend(self.h, self.l)
		
	def clearAll(self):
		self.ax.clear()
		if self.ax2: self.ax2.clear()
		self.h = []
		self.l = []
		self.canvas.draw()


class ArrayTableModel(QAbstractTableModel): 
	def __init__(self, parent=None, data = [], header = []): 
		super(ArrayTableModel, self).__init__()
		# list of tuple, each tuple is a record of the table
		self.datatable = data
		self.dataheader = header
		
	def update(self, dataIn,headerIn = None):
		self.datatable = dataIn
		self.dataheader = headerIn

	def rowCount(self, parent=QModelIndex()):
		#print 'rowCount',len(self.datatable) 
		return len(self.datatable) 

	def columnCount(self, parent=QModelIndex()):
		if self.rowCount()>0:
			#print 'colCount',self.datatable[0]
			return len(self.datatable[0]) 
		else:
			return 0
		
	def getColumnValue(self, columnIndex):
		res = []
		
		if self.columnCount()==0:
			return
			
		if ((columnIndex >=0) and (columnIndex < self.columnCount())):
			for val in self.datatable:
				res.append(val[columnIndex])
				
		return res
			

	def data(self, index, role=Qt.DisplayRole):
		i = index.row()
		j = index.column()
		if role == Qt.DisplayRole:
			#return '{0}'.format(self.datatable[i][j])
			if j==0:
				return '{:10.1f}'.format(self.datatable[i][j])
			else:
				return '{:10.2f}'.format(self.datatable[i][j])
		else:
			return None#QtCore.QVariant()

	def flags(self, index):
		return Qt.ItemIsEnabled
		
	def headerData(self, section, orientation, role=Qt.DisplayRole):
		if role == Qt.DisplayRole and orientation == Qt.Horizontal:
			return self.dataheader[section]
			
		return QAbstractTableModel.headerData(self, section, orientation, role)
	
class MainWidget(QWidget):
	def __init__(self):
		super(MainWidget, self).__init__()
		self.initUI()
		
	def initUI(self):
		# add splitter
		# add list on the left
		# add tabs on the right
		# add a tab with a tableview
		# add a tab with a chartview
		hbox = QHBoxLayout(self)
		self.tableList = QTreeWidget()
		dataTab = QTabWidget()
		
		self.tableTab = DataTableWidget()
		self.chartTab = ChartWidget()
		
		dataTab.addTab(self.tableTab,self.tr('Table'))
		dataTab.addTab(self.chartTab,self.tr('Chart'))
		
		splitView = QSplitter(Qt.Horizontal)
		splitView.addWidget(self.tableList)
		splitView.addWidget(dataTab)
		splitView.setSizes([100,200])
		
		hbox.addWidget(splitView)
		self.setLayout(hbox)

class ObservedDataMainwindow(QMainWindow):
	def __init__(self,plugin_dir, DBM, linkslayer= None, nodeslayer= None):
		super(ObservedDataMainwindow, self).__init__()
		self.plugin_dir = plugin_dir
		self.DBM = DBM
		self.linkstationslayer = linkslayer
		self.nodestationslayer = nodeslayer
		self.initUI()
		
	def closeEvent(self,event):
		self.mw.chartTab.clearAll()
		
	def _addmenuitem(self,parent, name, text, function):
		action = QAction(parent)
		action.setObjectName(name)
		action.setIcon(QIcon(self.plugin_dir+'/icons/'+name+'.svg'))
		action.setText(text)
		action.triggered.connect(function)
		parent.addAction(action)
		
	def _addAction(self,parent,name,text,function, checkable=False):
		action = QAction(parent)
		action.setObjectName(name)
		action.setIcon(QIcon(self.plugin_dir+'/icons/'+name+'.svg'))
		action.setText(text)
		#action.setWhatsThis(self.tr("Select upstream network"))
		action.setCheckable(checkable)
		action.triggered.connect(function)
		parent.addAction(action)
	
	def _addmenu(self,parent,name,text):
		menu = QMenu(parent)
		menu.setObjectName(name)
		menu.setTitle(text)
		return menu

	def initUI(self):
		menubar = self.menuBar()
		self.manMenu = self._addmenu(menubar,'ManMenu',self.tr('File'))
		self._addmenuitem(self.manMenu, 'ImportTable', self.tr('Import'), self.importNewTable)
		self._addmenuitem(self.manMenu, 'ExportTable', self.tr('Export'), self.exportTable)
		self._addmenuitem(self.manMenu, 'DeleteTable', self.tr('Delete'), self.deleteTable)
		self._addmenuitem(self.manMenu, 'RenameTable', self.tr('Rename'), self.renameTable)
		
		menubar.addMenu(self.manMenu)
		
		self.toolBar = self.addToolBar('Manage')
		self._addAction(self.toolBar, 'ImportTable', self.tr('Import'), self.importNewTable,False)
		self._addAction(self.toolBar, 'ExportTable', self.tr('Export'), self.exportTable,False)
		self._addAction(self.toolBar, 'DeleteTable', self.tr('Delete'), self.deleteTable,False)
		self._addAction(self.toolBar, 'RenameTable', self.tr('Rename'), self.renameTable,False)
		

		#~ exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)        
		#~ exitAction.setShortcut('Ctrl+Q')
		#~ exitAction.setStatusTip('Exit application')
		#~ exitAction.triggered.connect(QtGui.qApp.quit)

		self.statusBar()

		#self.setGeometry(300, 300, 300, 200)
		self.setWindowTitle(self.tr('Observed data'))    
		#self.show()
		
		# add central widget
		self.mw = MainWidget()
		self.setCentralWidget(self.mw)
		
		# update values
		self.updateListTable()
		
		# connect 
		self.mw.tableList.currentItemChanged.connect(self.updateDataTable)
		self.mw.tableList.currentItemChanged.connect(self.updateChart)
		
	def importNewTable(self):
		item = self.mw.tableList.currentItem()
		tableId = ''
		if item:
			self.selectedItem = item
			self.parentItem = self.selectedItem.parent()
			if self.parentItem:
				rootName = self.parentItem.text(0)
			else:
				rootName = self.selectedItem.text(0)
			
			if rootName == self.tr("discharges"):
				tableId = 'discharges'
			elif rootName == self.tr("water levels"):
				tableId = 'waterlevels'
			else:
				pass
		else:
			return
			
		from forms.import_csv_dialog import ImportCsvDialog
		from tools.import_from_CSV import importFromCSV
		
		dlg = ImportCsvDialog(self.DBM) 
		# show the dialog
		dlg.show()
		result = dlg.exec_() 
		# See if OK was pressed
		if result == 1: 
			res = dlg.getParameterValue()
			filename = res[0]
			newTablename = basename(filename)[:-4]
			colSep = res[1]
			if colSep == 'tab': colSep = '\t'
						
			headerExists = res[2]
			
			timeserie = importFromCSV(filename, colSep, headerExists)
			
			self.DBM.setArray(varName=newTablename,nArray= timeserie,tableName=tableId)
			
		# update list view
		self.updateListTable()
		
	def exportTable(self):
		sep = '\t'
		item = self.mw.tableList.currentItem()
		if item.parent():
			varName = str(item.text(0))
			# open a dialog to select output filename
			filename = QFileDialog.getSaveFileName(self, self.tr('Export %s to')%varName, None,"Comma Separated Values (*.CSV)")
			try:
				f = open(filename,'w')
				f.write(sep.join(self.dataArray.dataheader)+'\n')
				for i in range(0,self.dataArray.rowCount()):
					f.write(sep.join(map(str, self.dataArray.datatable[i]))+'\n')
			except:
				# do nothing
				return
					
				
	def deleteTable(self):
		item = self.mw.tableList.currentItem()
		if item:
			self.selectedItem = item
			self.parentItem = self.selectedItem.parent()
		else:
			return

		if self.selectedItem:
			varName = self.selectedItem.text(0)
			if self.parentItem:
				if self.parentItem.text(0) == self.tr("discharges"):
					tableId = 'discharges'
					reply = QMessageBox.question(self, 'SMARTGREEN',
																self.tr('Would you like to delete "%s" table from "%s"?'%(varName,self.parentItem.text(0))),
																QMessageBox.Yes | QMessageBox.No)

					if reply == QMessageBox.Yes:
						# delete row in precipitations table
						self.DBM.deleteRow(tableName=tableId,fieldName='OBJ_ID',rowValue= varName)
		
				elif self.parentItem.text(0) == self.tr("water levels"):
					tableId = 'waterlevels'
					reply = QMessageBox.question(self, 'SMARTGREEN',
																self.tr('Would you like to delete "%s" table from "%s"?'%(varName,self.parentItem.text(0))),
																QMessageBox.Yes | QMessageBox.No)

					if reply == QMessageBox.Yes:
						# delete row in precipitations table
						self.DBM.deleteRow(tableName=tableId,fieldName='OBJ_ID',rowValue= varName)
						
				else:
					pass
					
		self.updateListTable()
		
	def renameTable(self):
		oldValue = self.selectedItem.text(0)
		item = self.mw.tableList.currentItem()
		if item:
			self.selectedItem = item
			self.parentItem = self.selectedItem.parent()
		else:
			return
			
		if self.parentItem:
			if self.parentItem.text(0) == self.tr("discharges"):
				tableId = 'discharges'
				text, ok = QInputDialog.getText(self, 'SMARTGREEN', self.tr('Rename "%s" with:')%oldValue)
				if ok:
					newValue = str(text)
					self.DBM.setArrayName(oldVarName = oldValue, newVarName = newValue, tableName= tableId)
					
			elif self.parentItem.text(0) == self.tr("water levels"):
				tableId = 'waterlevels'
				text, ok = QInputDialog.getText(self, 'SMARTGREEN', self.tr('Rename "%s" with:')%oldValue)
				if ok:
					newValue = str(text)
					self.DBM.setArrayName(oldVarName = oldValue, newVarName = newValue, tableName= tableId)
			else:
				pass
				
		self.updateListTable()
		
	def updateListTable(self):
		# clear all value
		self.mw.tableList.clear()
		
		header = QTreeWidgetItem([self.tr("Data series:")])
		self.mw.tableList.setHeaderItem(header)

		# add root entries [discharge],[water level], [water elevation]
		qRoot = QTreeWidgetItem(self.mw.tableList, [self.tr("discharges")])
		wlRoot = QTreeWidgetItem(self.mw.tableList, [self.tr("water levels")])
		#root.setData(2, QtCore.Qt.EditRole, 'Some hidden data here')	# Data set to column 2, which is not visible

		varList = self.DBM.getColumnValues(fieldName='OBJ_ID',tableName='discharges')
		for varName in varList:
			item = QTreeWidgetItem(qRoot,[varName])
			item.setIcon(0,QIcon(self.plugin_dir+'/icons/Table.svg'))
			
		varList = self.DBM.getColumnValues(fieldName='OBJ_ID',tableName='waterlevels')
		for varName in varList:
			item = QTreeWidgetItem(wlRoot,[varName])
			item.setIcon(0,QIcon(self.plugin_dir+'/icons/Table.svg'))
			
		self.updateDataTable(None)
			
		#~ # select first item
		#~ self.mw.tableList.setCurrentRow(-1)
		#~ if self.mw.tableList.count() > 0:
			#~ self.mw.tableList.item(0).setSelected(True)
		
		#~ self.mw.tableList.setFocus()
		
	def updateDataTable(self,item):
		if item:
			self.selectedItem = item
			self.dataArray = ArrayTableModel(parent=None, data = [], header = [self.tr('time (min)'), self.tr('value')])
			self.parentItem = self.selectedItem.parent()
		else:
			self.dataArray = ArrayTableModel(parent=None, data = [], header = [self.tr('time (min)'), self.tr('value')])
			self.dataArray.datatable = []
			self.mw.tableTab.arrayView.setModel(self.dataArray)
			return

		#print 'text of self.selectedItem:',self.selectedItem.text(0)
		
		if self.selectedItem:
			varName = self.selectedItem.text(0)
			if self.parentItem:
				#print 'text of self.parentItem:',self.parentItem.text(0)
				if self.parentItem.text(0) == self.tr("discharges"):
					tableId = 'discharges'
					# populate model with data
					matrix = self.DBM.getArray(varName=varName,tableName=tableId)
					for i,row in enumerate(matrix):
						self.dataArray.datatable.append(tuple(row))
						
					self.mw.tableTab.arrayView.setModel(self.dataArray)
				elif self.parentItem.text(0) == self.tr("water levels"):
					tableId = 'waterlevels'
					# populate model with data
					matrix = self.DBM.getArray(varName=varName,tableName=tableId)
					for i,row in enumerate(matrix):
						self.dataArray.datatable.append(tuple(row))
						
					self.mw.tableTab.arrayView.setModel(self.dataArray)
				else:
					pass
			else:
				self.dataArray.datatable = []
				self.mw.tableTab.arrayView.setModel(self.dataArray)
				
		
	def updateChart(self):
		self.mw.chartTab.clearAll()
		ylab = ''
		if self.parentItem:
				if self.parentItem.text(0) == self.tr("discharges"):
					ylab = self.tr('discharge (m^3/s)')
				elif self.parentItem.text(0) == self.tr("water levels"):
					ylab = self.tr('water levels (m)')
				else:
					ylab = ''
					
		if self.dataArray:
			x = self.dataArray.getColumnValue(0)
			y = self.dataArray.getColumnValue(1)
			
			if y is not None: self.mw.chartTab.addLinePlot(x=x,y=y,lineType='o',color='b',name = ylab,yaxis = 1)
							
			self.mw.chartTab.setAxes(xlabs = None, ylabs = None, xTitle = self.tr('time (min)'), yTitle = ylab, y2Title = None, mainTitle = None)
			self.mw.chartTab.canvas.draw()
