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

def createHyetograph(duration, step, par_a1, par_n, par_alp, par_eps, par_kap, par_Tr, relativePeakTime = 0.5, method = 'uniform'):
	"""
	The function creates rainfall time series using
	Rainfall-Duration-Frequency curves parameters
	from selected weather station using both uniform
	and chicago methods
	"""
	# duration and step are in minutes but intensity is in mm/h and IDC needs for hours
	
	
	# force "method" to lower case
	method = method.lower()
	# create rainfall intensity serie
	if isinstance(step, (list, tuple)):
		dts = step
	else:
		dts = 0.5*(np.arange(0,duration,step)+np.arange(step,duration+step,step))
	
	# heigth of rain: =a1*w*d^n
	# where  w=eps+alp/kap*(1-(ln(Tr/(Tr-1)))^kap))
	prob = np.log(par_Tr/(par_Tr-1))
	#print 'prob:',prob
	par_w = par_eps+par_alp/par_kap*(1-(prob)**par_kap)
	#print 'par_w:',par_w
	
	redK = 1.0
	if duration<60:
		redK = (0.54*(duration)**0.25-0.5) # coefficient of reduction in case of rain event shorter than 1 hour
		
	#print 'redK:',redK
	
	# uniform or chicago
	if method == 'uniform':
		totRainDepth = redK*par_a1*par_w*(duration/60)**par_n # in mm
		rainIntensity = np.zeros(len(dts), dtype=np.float)+totRainDepth/(duration/60) # in mm/h
		rainDepth = rainIntensity * (step/60) # in mm
		#rainDepth = [totRainDepth/(float(duration)/step)]*len(rainIntensity)
	elif method == 'chicago':
		# calculate relative time
		peakTime = duration * relativePeakTime
		rdts = np.absolute(dts-peakTime)
		#~ print 'par_a1',par_a1
		#~ print 'par_w',par_w
		#~ print 'par_n',par_n
		#~ print 'rdts',rdts
		rainIntensity = redK*par_a1*par_w*par_n*(rdts/60)**(par_n-1) # in mm/h
		# replace inf value
		idx = np.where( rainIntensity == np.inf )
		#print idx[0]
		for i in idx[0]:
			# replace with the mean value before and after
			rainIntensity[i] = 0.5*(rainIntensity[i-1]+rainIntensity[i+1])
		
		rainDepth = rainIntensity * (step/60) # in mm
	elif method == 'alternatingblock':
		pass
	else:
		print('Unsupported method %s' % method)

	# return a table
	res = np.column_stack((dts,rainIntensity,rainDepth))
	return res
	

if __name__ == '__console__':
	#auno	enne	GEValp	GEVeps	GEVkap
	#29.74	0.31	0.30	0.82	-0.038
	print('uniform')
	uniform = createHyetograph(duration = 60, step = 5, par_a1 = 29.74, par_n = 0.31, par_alp = 0.30, par_eps = 0.82, par_kap = -0.038, par_Tr = 10.0, relativePeakTime = 0.5, method = 'uniform')
	print(uniform)
	print('chicago 5 min')
	chicago5min = createHyetograph(duration = 60, step = 5, par_a1 = 29.74, par_n = 0.31, par_alp = 0.30, par_eps = 0.82, par_kap = -0.038, par_Tr = 10.0, relativePeakTime = 0.5, method = 'chicago')
	print(chicago5min)
	print('chicago 10 min')
	chicago10min = createHyetograph(duration = 60, step = 10, par_a1 = 29.74, par_n = 0.31, par_alp = 0.30, par_eps = 0.82, par_kap = -0.038, par_Tr = 10.0, relativePeakTime = 0.5, method = 'chicago')
	print(chicago10min)
	print('chicago 1 min')
	chicago1min = createHyetograph(duration = 60, step = 1, par_a1 = 29.74, par_n = 0.31, par_alp = 0.30, par_eps = 0.82, par_kap = -0.038, par_Tr = 10.0, relativePeakTime = 0.5, method = 'chicago')
	print(chicago1min)
	print('chicago 5 min r = 0.375')
	chicago5min2 = createHyetograph(duration = 60, step = 5, par_a1 = 29.74, par_n = 0.31, par_alp = 0.30, par_eps = 0.82, par_kap = -0.038, par_Tr = 10.0, relativePeakTime = 0.375, method = 'chicago')
	print(chicago5min2)

