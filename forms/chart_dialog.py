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

import sys

from PyQt5.QtWidgets import QDialog, QPushButton, QVBoxLayout, QMainWindow, QMessageBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

import numpy as np

import random

class ChartDialog(QDialog):
	def __init__(self, parent=None, title = '', secondAxis = True):
		QDialog.__init__(self)
		
		self.setWindowTitle(title)
		
		# a figure instance to plot on
		self.figure = plt.figure()

		# this is the Canvas Widget that displays the `figure`
		# it takes the `figure` instance as a parameter to __init__
		self.canvas = FigureCanvas(self.figure)
		
		# this is the Navigation widget
		# it takes the Canvas widget and a parent
		self.toolbar = NavigationToolbar(self.canvas, self)

		# Just some button connected to `plot` method
		self.button = QPushButton('Plot')
		self.button.clicked.connect(self.plot)

		# set the layout
		layout = QVBoxLayout()
		layout.addWidget(self.toolbar)
		layout.addWidget(self.canvas)
		#layout.addWidget(self.button)
		self.setLayout(layout)
		
		self.plotList = []
		self.ax = self.figure.add_subplot(111)
		if secondAxis: self.ax2 = self.ax.twinx()
		
		legend = self.ax.legend(loc='upper center', shadow=True)
		self.h = []
		self.l = []

	def setAxes(self, xlabs = None, ylabs = None, xTitle = None, yTitle = None, y2Title = None, mainTitle = None):
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
		
		h, l = self.ax.get_legend_handles_labels()
		h += (bars,)
		l += (name,)
		self.ax.legend(h, l)

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
		self.ax.legend(self.h, self.l)
		
	def addSinglePointPlot(self,x,y,color='b',yaxis=1):
		if yaxis == 1:
			points, = self.ax.plot([x], [y], marker='o', markersize=3, color=color)
		else:
			points, = self.ax2.plot([x], [y], marker='o', markersize=3, color=color)

	def addInfVertical(self,x):
		self.ax.axvline(x=x, color='k', linestyle='-')
		
	def drawConduit(self,x1,y1,x2,y2,h):
		xs = [x1,x2,x2, x1]
		ys = [y1,y2,y2+h, y1+h]
		xy = np.column_stack([xs, ys])
		#print 'xy:',xy
		poly = Polygon(xy,edgecolor='black',facecolor='lightgray')
		self.ax.add_patch(poly)
		self.ax.autoscale_view()

	def drawManhole(self,Hb,Ht,pos,diam=1):
		xs = [pos-0.5*diam,pos+0.5*diam,pos+0.5*diam, pos-0.5*diam]
		ys = [Hb,Hb,Ht, Ht]
		xy = np.column_stack([xs, ys])
		#print 'xy:',xy
		poly = Polygon(xy,edgecolor='black',facecolor='gray')
		self.ax.add_patch(poly)
		self.ax.autoscale_view()

	def plot(self):
		''' plot some random stuff '''
		# random data
		ind = range(10)
		width = 1
		data = [random.random() for i in ind]
		
		# discards the old graph
		self.ax.hold(False)
		
		# create add plot
		self.addBarPlot(ind,data)
		#self.addLinePlot(ind,data)
		# refresh canvas
		self.canvas.draw()
		
	def addText(self, txt, xpos,ypos,rotAngle = 0.0):
		#print 'add text %s in (%s,%s)'%(txt,xpos, ypos)
		try:
			self.ax.text(xpos, ypos, txt,rotation = rotAngle, rotation_mode	='anchor',ha	= 'center',va	= 'center' )
			self.canvas.draw()
		except:
			pass
		
	def updateLimits(self):
		# recompute the ax.dataLim
		self.ax.relim()
		# update ax.viewLim using the new dataLim
		self.ax.autoscale_view()

if __name__ == '__console__':
	#app = QtGui.QApplication(sys.argv)

	main = QMainWindow()
	main.show()

	#sys.exit(app.exec_())