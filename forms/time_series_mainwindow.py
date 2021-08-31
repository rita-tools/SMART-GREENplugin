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

from os.path import  basename
import numpy as np
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QTableView, QAbstractItemView, QVBoxLayout, QHBoxLayout, QListWidget, QTabWidget, \
	QSplitter, QMainWindow, QAction, QMenu, QFileDialog, QMessageBox, QListWidgetItem

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

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
		self.tableList = QListWidget()
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

class TimeSeriesMainwindow(QMainWindow):
	def __init__(self,plugin_dir, DBM,weatherstationslayer= None):
		super(TimeSeriesMainwindow, self).__init__()
		self.plugin_dir = plugin_dir
		self.DBM = DBM
		self.weatherstationslayer = weatherstationslayer
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
		self._addmenuitem(self.manMenu, 'NewTable', self.tr('New'), self.addNewTable)
		self._addmenuitem(self.manMenu, 'ImportTable', self.tr('Import'), self.importNewTable)
		self._addmenuitem(self.manMenu, 'ExportTable', self.tr('Export'), self.exportTable)
		self._addmenuitem(self.manMenu, 'DeleteTable', self.tr('Delete'), self.deleteTable)
		
		menubar.addMenu(self.manMenu)
		
		self.toolBar = self.addToolBar('Manage')
		self._addAction(self.toolBar, 'NewTable', self.tr('New'), self.addNewTable,False)
		self._addAction(self.toolBar, 'ImportTable', self.tr('Import'), self.importNewTable,False)
		self._addAction(self.toolBar, 'ExportTable', self.tr('Export'), self.exportTable,False)
		self._addAction(self.toolBar, 'DeleteTable', self.tr('Delete'), self.deleteTable,False)
		

		#~ exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)        
		#~ exitAction.setShortcut('Ctrl+Q')
		#~ exitAction.setStatusTip('Exit application')
		#~ exitAction.triggered.connect(QtGui.qApp.quit)

		self.statusBar()

		#self.setGeometry(300, 300, 300, 200)
		self.setWindowTitle(self.tr('Time series'))    
		#self.show()
		
		# add central widget
		self.mw = MainWidget()
		self.setCentralWidget(self.mw)
		
		# update values
		self.updateListTable()
		
		# connect 
		self.mw.tableList.currentItemChanged.connect(self.updateDataTable)
		self.mw.tableList.currentItemChanged.connect(self.updateChart)
		
	def addNewTable(self):
		from forms.create_hyetograph_dialog import CreateHyetographDialog
		from tools.create_hyetograph import createHyetograph
		dlg = CreateHyetographDialog(self.tr) 
		# show the dialog
		#print 'self.weatherstationslayer:', self.weatherstationslayer
		if self.weatherstationslayer:
			dlg.show()
			result = dlg.exec_() 
			# See if OK was pressed
			if result == 1: 
				res = dlg.getParameterValue()
				# work with selection or all points
				duration = res[0]
				step = res[1]
				returnTime = res[2]
				method = res[3]
				relativePeakTime = res[4]
				name = res[5]
				useSelection = res[6]
				updateLayer = res[7]
				
				selection = []
				if useSelection:
					selection = self.weatherstationslayer.selectedFeatures()
				else:
					#selection = layer.getFeatures()
					# layer.getFeatures() LOCKs database :(
					for feat in self.weatherstationslayer.getFeatures():
						selection.append(feat)
						
				if updateLayer:
					self.weatherstationslayer.startEditing()
				
				tableIdx = self.weatherstationslayer.fields().indexFromName('TABLE')
				
				for feature in selection:
					#get attributes
					attrs = feature.attributes()
					# run the script
					hyetograph = createHyetograph(duration = duration, step = step, \
													par_a1 = feature['A1'], par_n = feature['N'],
													par_alp = feature['ALP'], par_eps = feature['EPS'], par_kap = feature['KAP'],\
													par_Tr = returnTime,\
													relativePeakTime = relativePeakTime,\
													method = method)
					# save to csv file
					newTablename = name+' - '+feature['OBJ_ID']
					#self.DBM.importNumpyArray(newTablename, ['time','intensity','depth'], ['REAL','REAL','REAL'], hyetograph)
					self.DBM.setArray(varName=newTablename,nArray= hyetograph,tableName='precipitations')
					
					if updateLayer:
						# update layer field
						#print 'update field'
						self.weatherstationslayer.changeAttributeValue(feature.id(),tableIdx,newTablename,attrs[tableIdx])
					
				# exit editing and save
				if updateLayer:
					#print 'save editing editing'
					self.weatherstationslayer.commitChanges()
					self.weatherstationslayer.updateExtents()
			
			# update list view
			self.updateListTable()
						
		
	def importNewTable(self):
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
			
			hyetograph = importFromCSV(filename, colSep, headerExists)
			
			self.DBM.setArray(varName=newTablename,nArray= hyetograph,tableName='precipitations')
			
		# update list view
		self.updateListTable()
		
	def exportTable(self):
		sep = '\t'
		item = self.mw.tableList.currentItem()
		varName = str(item.text())
		# open a dialog to select output filename
		filename = QFileDialog.getSaveFileName(self, self.tr('Export %s to')%varName, None,"Comma Separated Values (*.CSV)")
		try:
			f = open(filename,'w')
			f.write((sep.join(self.dataArray.dataheader)+'\n').encode('utf-8'))
			for i in range(0,self.dataArray.rowCount()):
				f.write(sep.join(map(str, self.dataArray.datatable[i]))+'\n')
		except Exception as e:
			#print 'exportTable:',str(e)
			# do nothing
			return
				
				
	def deleteTable(self):
		item = self.mw.tableList.currentItem()
		varName = str(item.text())
		reply = QMessageBox.question(self, 'SMARTGREEN',
													self.tr('Would you like to delete %s table?'%(varName)),
													QMessageBox.Yes | QMessageBox.No)

		if reply == QMessageBox.Yes:
			# delete row in precipitations table
			self.DBM.deleteRow(tableName='precipitations',fieldName='OBJ_ID',rowValue= varName)
			
		self.updateListTable()
		
	def updateListTable(self):
		# clear all value
		self.mw.tableList.clear()
		
		varList = self.DBM.getColumnValues(fieldName='OBJ_ID',tableName='precipitations')
		for varName in varList:
			item = QListWidgetItem(varName)
			item.setIcon(QIcon(self.plugin_dir+'/icons/Table.svg'));
			self.mw.tableList.addItem(item)
			
		# select first item
		self.mw.tableList.setCurrentRow(-1)
		if self.mw.tableList.count() > 0:
			self.mw.tableList.item(0).setSelected(True)
		
		self.mw.tableList.setFocus()
		
	def updateDataTable(self,item):
		if item:
			varName = str(item.text())
			self.dataArray = ArrayTableModel(parent=None, data = [],
											 header = [self.tr('time (min)'), self.tr('intensity (mm/h)'),self.tr('heigth (mm)')])
			# populate model with data
			matrix = self.DBM.getArray(varName=varName,tableName='precipitations')
			for i,row in enumerate(matrix):
				self.dataArray.datatable.append(tuple(row))
				
			self.mw.tableTab.arrayView.setModel(self.dataArray)
		
	def updateChart(self):
		self.mw.chartTab.clearAll()
		if self.dataArray:
			x = self.dataArray.getColumnValue(0)
			y = self.dataArray.getColumnValue(1)
			z = self.dataArray.getColumnValue(2)
			z = np.cumsum(z)
		
			if x is not None: self.mw.chartTab.addBarPlot(x=x,y=y,width=x[1]-x[0],color='b',name = self.tr('intensity (mm/h)'))
				
			if z is not None: self.mw.chartTab.addLinePlot(x=x,y=z,lineType='-',color='r',name = self.tr('rain depth (mm)'),yaxis = 2)
							
			self.mw.chartTab.setAxes(xlabs = None, ylabs = None, xTitle = self.tr('time (min)'),
									 yTitle = self.tr('intensity (mm/h)'), y2Title = self.tr('cumulative (mm)'), mainTitle = None)
			self.mw.chartTab.canvas.draw()
