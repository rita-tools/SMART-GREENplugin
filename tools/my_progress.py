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

class MyProgress:
	def __init__(self):
		pass
		
	def setConsoleInfo(self,text):
		text = text.encode('utf-8')
		print('CONSOLE_INFO:', text)

	def error(self,text):
		text = text.encode('utf-8')
		print('ERROR:', text)

	def setPercentage(self,val,printPerc = False):
		if printPerc:
			nblock = int(val/10)
			blocks = ['#']*nblock
			lines = ['_']*(10-nblock)
			bar = blocks+lines
			print(''.join(bar) + '%s' % int(val) + '%')

	def setText(self, text):
		text = text.encode('utf-8')
		print('TEXT:', text)

	def setInfo(self,text, error=False):
		text = text.encode('utf-8')
		if error:
			print('ERROR: %s' % text)
		else:
			print('INFO:  %s' % text)

	def setCommand(self, text):
		text = text.encode('utf-8')
		print('CMD:', text)
		
		
		