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

import numpy as np
	
def importFromCSV(filename, colSep = ";", header = True, comTag = '#'):
	columnNames = []
	dataArray =np.array([])
	# oper CSV file
	in_file = open(filename,"r")
	i = 0
	while 1:
		in_line = in_file.readline()
		if len(in_line) == 0:
			break
		if in_line[0] == comTag:
			continue # skip line because is a comment

		# process the line
		in_line = in_line[:-1]
		values = in_line.split(colSep)
					
		if (i == 0 and header):
			# first is column name
			#print values
			print('header exist')
			columnNames = values
		else:
			# try to guess value types
			floatVals = [float(v) for v in values]
			#dataArray = np.append(dataArray,[floatVals])
			if len(dataArray)==0:
				dataArray =np.array(floatVals)
			else:
				dataArray = np.vstack([dataArray,floatVals])
			
		i+=1
				
	return dataArray