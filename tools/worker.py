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

from time import sleep

from PyQt5.QtCore import QObject, pyqtSignal


class Worker(QObject):
	finished = pyqtSignal()
	ready = pyqtSignal()
	reportProgress = pyqtSignal(int)
	reportMessage = pyqtSignal(str,str)
	
	def __init__(self,parent,function,*args, **kwargs):
		QObject.__init__(self,parent)
		self.function = function
		self.args = args
		self.kwargs = kwargs
		self.kwargs['progress']= self # make worker as progress output
		
	def setConsoleInfo(self,text):
		self.reportMessage.emit(text,'blue')
		
	def error(self,text):
		self.reportMessage.emit(text,'red')
	
	def setText(self, text):
		self.reportMessage.emit(text,'gray')
		
	def setInfo(self,text, error=False):
		if error:
			self.error(text)
		else:
			self.setConsoleInfo(text)
		
	def setCommand(self, text):
		self.reportMessage.emit(text,'black')
		
	def setPercentage(self,val):
		try:
			val = int(val)
		except:
			val = 0
			
		self.reportProgress.emit(val)

	def process(self):
		#print('Worker thread ID: %s' % int(QThread.currentThreadId()))
		#print("Worker started")
		self.setInfo(self.tr('%s starts ...')%str(self.function.__name__))
		self.setPercentage(0)
		#self.reportMessage.emit(text,'gray')
		self.ready.emit()

		# print('In process: before running function')
		# print('kwargs:',self.kwargs)
		self.function(*self.args, **self.kwargs)
		
		self.setInfo(self.tr('%s ends.')%str(self.function.__name__))
		self.setPercentage(0)
		#print("Worker terminates...")
		self.finished.emit()
