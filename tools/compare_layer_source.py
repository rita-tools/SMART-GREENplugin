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


def compareLayerSource(path1,path2):
	path1 = path1.replace('\\','/')
	path2 = path2.replace('\\','/')
	res = False
	if path1==path2:
		res = True
		
	if res == False:
		# if first test is false, try comparing only the last part of both the path
		toks1 = path1.split('|')
		toks2 = path2.split('|')
			
		if len(toks1) == len(toks2):
			if len(toks1)==2:
				if toks1[1] == toks2[1]:
					res = True
				else:
					res = False
			else:
				res = False
		else:
			res = False
			
	if res==False:
		toks1 = path1.split('|layername=')
		if len(toks1)==2:
			if toks1[1]==path2:
				res = True
			else:
				res=False
			
	return res
		