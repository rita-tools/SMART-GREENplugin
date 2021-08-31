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

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QTableView, QAbstractItemView, QVBoxLayout, QHBoxLayout, QTreeWidget, QTabWidget, \
	QSplitter, QMainWindow, QAction, QMenu, QFileDialog, QTreeWidgetItem, QListWidgetItem


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
				return '{:10.3f}'.format(self.datatable[i][j])
			else:
				return '{:10.3f}'.format(self.datatable[i][j])
		else:
			return None#QtCore.QVariant()

	#~ def flags(self, index):
		#~ return Qt.ItemIsEnabled
		
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
		#self.tableList = QListWidget()
		self.tableList = QTreeWidget()
		dataTab = QTabWidget()
		
		self.tableTab = DataTableWidget()
		#self.chartTab = ChartWidget()
		
		dataTab.addTab(self.tableTab,self.tr('Table'))
		#dataTab.addTab(self.chartTab,self.tr('Chart'))
		
		splitView = QSplitter(Qt.Horizontal)
		splitView.addWidget(self.tableList)
		splitView.addWidget(dataTab)
		splitView.setSizes([100,200])
		
		hbox.addWidget(splitView)
		self.setLayout(hbox)

class ResultsMainwindow(QMainWindow):
	def __init__(self,plugin_dir, DBM):
		super(ResultsMainwindow, self).__init__()
		self.plugin_dir = plugin_dir
		self.DBM = DBM
		# define variable to be shown
		self.varDict = {'Hnode-H':self.tr('Water level (m)'),'Hnode-Qoverflow':self.tr('Overflow discharge (m^3/s)'),
							  'Qret-Qout': self.tr('Conduit discharge (m^3/s)'), 'Qret-Aaverage': self.tr('Conduit wetted area (m^2)'), 'Qret-Raverage': self.tr('Conduit hydraulic radius (m)'),
							  'GIs_route-reserv_Vol':self.tr('Stored volume (m^3)'),\
							  'GIs_route-reserv_h':self.tr('Stored water depth (m)'),\
							  'GIs_route-reserv_Qin':self.tr('Inflow (m^3/s)'),\
							  'GIs_route-reserv_Qrete':self.tr('Outflow (m^3/s)'),\
							  'GIs_route-reserv_Qinf':self.tr('Infiltration (m^3/s)'),\
							  'GIs_route-reserv_Qover':self.tr('Overflow (m^3/s)'),\
							  'GIs_route-soil_Q2node':self.tr('Overland flow (m^3/s)'),\
							  'GIs_route-soil_relSATgrav':self.tr('Average relative gravitational saturation level (-)'),\
							  'GIs_route-soil_relSATcap':self.tr('Average relative capillary saturation level (-)'),\
							  'GIs_route-soil_relSAT':self.tr('Average total saturation level (-)'),\
							  }
		
		self.initUI()
		
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
		self._addmenuitem(self.manMenu, 'ExportTable', self.tr('Export'), self.exportTable)
		
		menubar.addMenu(self.manMenu)
		
		self.toolBar = self.addToolBar('Manage')
		self._addAction(self.toolBar, 'ExportTable', self.tr('Export'), self.exportTable,False)
		
		self.statusBar()

		#self.setGeometry(300, 300, 300, 200)
		self.setWindowTitle(self.tr('Results'))    
		#self.show()
		
		# add central widget
		self.mw = MainWidget()
		self.setCentralWidget(self.mw)
		
		# update values
		self.updateListTable()
		
		# connect 
		self.mw.tableList.currentItemChanged.connect(self.updateDataTable)
		self.mw.tableList.currentItemChanged.connect(self.makeStat)
						
	def exportTable(self):
		sep = '\t'
		item = self.mw.tableList.currentItem()
		varName = str(item.text(0))
		# open a dialog to select output filename
		filename = QFileDialog.getSaveFileName(self, self.tr('Export %s to')%varName, None,"Comma Separated Values (*.CSV)")
		filename = filename[0]
		try:
			f = open(filename,'w')
			f.write(sep.join(self.dataArray.dataheader)+'\n')
			for i in range(0,self.dataArray.rowCount()):
				f.write(sep.join(map(str, self.dataArray.datatable[i]))+'\n')
		except Exception as e:
			# do nothing
			print('ERROR',str(e))
			return
				
				
	def updateListTable(self):
		# clear all value
		self.mw.tableList.clear()
		
		header = QTreeWidgetItem([self.tr("Results")])
		self.mw.tableList.setHeaderItem(header)

		# add root entries [discharge],[water level], [water elevation]
		nodesRoot = QTreeWidgetItem(self.mw.tableList, [self.tr("Nodes")])
		linksRoot = QTreeWidgetItem(self.mw.tableList, [self.tr("Links")])
		lidsRoot = QTreeWidgetItem(self.mw.tableList, [self.tr("LIDs")])
		
		varList = self.varDict.keys()
		for varName in varList:
			item = QListWidgetItem(self.varDict[varName])
			if varName.startswith('Qret'):
				# use obj_id from links
				item = QTreeWidgetItem(linksRoot,[self.varDict[varName]])
			elif varName.startswith('GIs_route'):
				# use obj_id from lids
				item = QTreeWidgetItem(lidsRoot,[self.varDict[varName]])
			else:
				# use obj_id from nodes
				item = QTreeWidgetItem(nodesRoot,[self.varDict[varName]])
			
			item.setIcon(0,QIcon(self.plugin_dir+'/icons/Table.svg'));
			
		self.updateDataTable(None)
		
	def updateDataTable(self,item):
		if item:
			varName = str(item.text(0))
			if not varName in list(self.varDict.values()):
				# varName is a root name
				self.dataArray = ArrayTableModel(parent=None, data = [], header = [])
				self.mw.tableTab.arrayView.setModel(self.dataArray)
			else:
				varName = list(self.varDict.keys())[list(self.varDict.values()).index(varName)]
				self.dataArray = ArrayTableModel(parent=None, data = [], header = [])
				# populate model with data
				matrix = self.DBM.getArray(varName=varName,tableName='results')
				# invert row and cols
				tranMatrix = matrix.transpose()
				
				for i,row in enumerate(tranMatrix):
					self.dataArray.datatable.append(tuple(row))
					
				# update header with object id 
				#~ nCols = self.dataArray.columnCount()
				#~ self.dataArray.dataheader = ['t'+str(i) for i in range(1,nCols+1)]
				if varName.startswith('Qret'):
					# use obj_id from links
					self.dataArray.dataheader = self.DBM.getColumnValues(fieldName='OBJ_ID',tableName='Links')
				elif varName.startswith('GIs_route'):
					# use obj_id from lids
					self.dataArray.dataheader = self.DBM.getColumnValues(fieldName='OBJ_ID',tableName='Lids')
				else:
					# use obj_id from nodes
					self.dataArray.dataheader = self.DBM.getColumnValues(fieldName='OBJ_ID',tableName='Nodes')
					
				self.mw.tableTab.arrayView.setModel(self.dataArray)
				self.mw.tableTab.arrayView.selectionModel().selectionChanged.connect(self.makeStat)
				
	def makeStat(self):
		from scipy import stats
		
		cellValues = self.mw.tableTab.arrayView.selectedIndexes ()
		if len(cellValues)==0:
			msg = self.tr('n. of cells: --, min: --, max: --, mean: --, variance: --, skewness: --, kurtosis: --')
		else:
			vals = [float(self.mw.tableTab.arrayView.model().data(x)) for x in cellValues]
			
			# report some statistics from links and node attributes
			nobs, minmax, mean, variance, skewness, kurtosis = stats.describe(vals,nan_policy ='omit')
			msg = self.tr('n. of cells: %s, min: %s, max: %s, mean: %s, variance: %s, skewness: %s, kurtosis: %s')%(nobs, minmax[0],minmax[1],mean,variance,skewness, kurtosis)
			
		self.statusBar().showMessage(msg)
