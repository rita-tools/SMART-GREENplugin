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
import os
import scipy.io as sio
import datetime

from qgis.core import *

#~ import logging
from my_progress import MyProgress

class WeatherExporter():
	
	def __init__(self, progress = None):
		self.weatherstationsLayer = None
		if progress is None:
			self.progress = MyProgress()
		else:
			self.progress = progress
		#~ logging.basicConfig(filename='d:/test_smartgreen/testlog2.log',level=logging.DEBUG)
		
	def setWeatherstationsLayer(self,weatherstationsLayer,f_id,f_name,f_datafile):
		self.weatherstationsLayer = weatherstationsLayer
		self.f_id = f_id
		self.f_name = f_name
		self.f_datafile = f_datafile
		
	def setSimulationExtreme(self,simulationTime,timeStep):
		# both must be in hours
		self.simTime = simulationTime
		self.timeStep = timeStep
		
	def setDB(self,DB):
		self.DB = DB
		
	def weatherStationsToMat(self,matFileName):
		# loop in weatherStations layer
		# if datafile exist then export ws metadata and datafile to map
		attrList = []
		
		#~ sp       = rainfall (mm)
		#~ s_ta_max = air maximum temperature (deg.C)
		#~ s_ta_min = air minimum temperature (deg.C)
		#~ s_ua     = air relative humidity (%)
		#~ s_vv     = average wind speed (m/s)
		#~ s_ra     = incoming solar radiation (W/m2)
		
		wsIds, wsNames, xxs, yys, elevs, rainTables = self.getMeteoData()
		
		sp = []
		s_ta_max = []
		s_ta_min = []
		s_ua = []
		s_vv = []
		s_ra = []
		
		#~ print 'self.timeStep:', self.timeStep
		#~ print 'self.simTime:', self.simTime
				
		for i, rainTable in enumerate(rainTables):
			wsId = np.array([[wsIds[i]]])
			xx = np.array([xxs[i]])
			yy = np.array([yys[i]])
			elev = np.array([[elevs[i]]])
			
			# get table data
			#tRows = self.DB.getDataFromTable(rainTable)
			tRows =  self.DB.getArray(rainTable,tableName='precipitations')
			
			timeSteps = []
			precInt = []
			for row in tRows:
				timeSteps.append(float(row[0])/60.0) # in hours
				precInt.append(float(row[1])) # in mm/hour
				
			# resample data to fit simulation parameters
			simTimeSteps = np.linspace(0.5*self.timeStep, self.simTime-0.5*self.timeStep, int(self.simTime//self.timeStep))
			#~ print 'simTimeSteps:',simTimeSteps
			simPrecInt = np.interp(simTimeSteps, timeSteps, precInt)
			#~ print 'simPrecInt1:',simPrecInt
			# set precipitation intensity to zero for time steps greater than precipitation time
			precDur = max(timeSteps)
			#~ print 'precDur:',precDur
			simPrecInt[simTimeSteps>precDur] = 0.0
			#~ print 'simPrecInt2:',simPrecInt
			simPrecDepth = simPrecInt*self.timeStep
			#~ print 'simPrecDepth:',simPrecDepth
			# transform time to ordinal
			precTimes = self.timeStepsToOrdinal(simTimeSteps)
			# reshape series
			precTimes = self.flipArray(precTimes)
			precDepths = self.flipArray(simPrecDepth)
			# make attribute structures
			sp.append([(wsId,xx,yy,elev,precTimes,precDepths)])
			
			if i ==0:
				# add other variables only one time in order to avoid repeated values
				s_ta_max.append([(wsId,xx,yy,elev,precTimes,self.defaultData(20.0,len(precTimes)))])
				s_ta_min.append([(wsId,xx,yy,elev,precTimes,self.defaultData(10.0,len(precTimes)))])
				s_ua.append([(wsId,xx,yy,elev,precTimes,self.defaultData(70.0,len(precTimes)))])
				s_vv.append([(wsId,xx,yy,elev,precTimes,self.defaultData(3.0,len(precTimes)))])
				s_ra.append([(wsId,xx,yy,elev,precTimes,self.defaultData(100.0,len(precTimes)))])
		
		# export to mat file
		sp = np.array(sp, dtype=[('code', 'O'), ('est', 'O'), ('nord', 'O'), ('quota', 'O'), ('time', 'O'), ('dati', 'O')])
		self.saveAsMAT(matFileName,sp,'sp',self.progress)
		s_ta_max = np.array(s_ta_max, dtype=[('code', 'O'), ('est', 'O'), ('nord', 'O'), ('quota', 'O'), ('time', 'O'), ('dati', 'O')])
		self.saveAsMAT(matFileName,s_ta_max,'s_ta_max',self.progress)
		s_ta_min = np.array(s_ta_min, dtype=[('code', 'O'), ('est', 'O'), ('nord', 'O'), ('quota', 'O'), ('time', 'O'), ('dati', 'O')])
		self.saveAsMAT(matFileName,s_ta_min,'s_ta_min',self.progress)
		s_ua = np.array(s_ua, dtype=[('code', 'O'), ('est', 'O'), ('nord', 'O'), ('quota', 'O'), ('time', 'O'), ('dati', 'O')])
		self.saveAsMAT(matFileName,s_ua,'s_ua',self.progress)
		s_vv = np.array(s_vv, dtype=[('code', 'O'), ('est', 'O'), ('nord', 'O'), ('quota', 'O'), ('time', 'O'), ('dati', 'O')])
		self.saveAsMAT(matFileName,s_vv,'s_vv',self.progress)
		s_ra = np.array(s_ra, dtype=[('code', 'O'), ('est', 'O'), ('nord', 'O'), ('quota', 'O'), ('time', 'O'), ('dati', 'O')])
		self.saveAsMAT(matFileName,s_ra,'s_ra',self.progress)
		
	def getMeteoData(self):
		wsIds = []
		wsNames = []
		xxs = []
		yys = []
		elevs = []
		rainTables = []
		
		featNum = self.weatherstationsLayer.featureCount()
		features = self.weatherstationsLayer.getFeatures()
		
		i = 0
		for feat in features:
			i+=1
			self.progress.setPercentage(100.0*i/float(featNum))
			
			wsDatafile = feat[self.f_datafile]
			rainTableLay = self.DB.getTableAsLayer(wsDatafile)
			
			if rainTableLay is not None:
				# get station id and name
				wsIds.append(feat[self.f_id])
				wsNames.append(feat[self.f_name])
				# get geometry
				xx,yy = self.featToCoordArray(feat)
				xxs.append(xx)
				yys.append(yy)
				elevs.append(100.0)
				rainTables.append(wsDatafile)
			else:
				self.progress.setInfo('Weather station %s <id: %s>has no valid precipitation table'%(feat[self.f_name],feat[self.f_id]), True)
		
		return wsIds, wsNames, xxs, yys, elevs, rainTables
		
	def __weatherStationsToMat(self,matFileName):
		# loop in weatherStations layer
		# if datafile exist then export ws metadata and datafile to map
		attrList = []
		featNum = self.weatherstationsLayer.featureCount()
		features = self.weatherstationsLayer.getFeatures()
		i = 0
		
		#~ sp       = rainfall (mm)
		#~ s_ta_max = air maximum temperature (deg.C)
		#~ s_ta_min = air minimum temperature (deg.C)
		#~ s_ua     = air relative humidity (%)
		#~ s_vv     = average wind speed (m/s)
		#~ s_ra     = incoming solar radiation (W/m2)
		
		sp = []
		s_ta_max = []
		s_ta_min = []
		s_ua = []
		s_vv = []
		s_ra = []
		
		
		for feat in features:
			i+=1
			self.progress.setPercentage(100.0*i/float(featNum))
			
			# get datafile
			wsId = feat[self.f_id]
			wsName = feat[self.f_name]
			wsDatafile = feat[self.f_datafile]
			rainTable = self.DB.getTableAsLayer(wsDatafile)
			
			if rainTable is not None:
				# get geometry
				xx,yy = self.featToCoordArray(feat)
				wsId = np.array([[wsId]])
				xx = np.array([xx])
				yy = np.array([yy])
				elev = np.array([[100]])
				
				# get precipitation data, interpolated if necessary
				precTimes, precInts, precDepths = self.getPrecipitationData(rainTable,'time','intensity')
				# transform time to ordinal
				precTimes = self.timeStepsToOrdinal(precTimes)
				# reshape series
				precTimes = self.flipArray(precTimes)
				precDepths = self.flipArray(precDepths)
				# make attribute structures
				sp.append((wsId,xx,yy,elev,precTimes,precDepths))
				# add other variables
				s_ta_max.append((wsId,xx,yy,elev,precTimes,self.defaultData(20.0,len(precTimes))))
				s_ta_min.append((wsId,xx,yy,elev,precTimes,self.defaultData(10.0,len(precTimes))))
				s_ua.append((wsId,xx,yy,elev,precTimes,self.defaultData(70.0,len(precTimes))))
				s_vv.append((wsId,xx,yy,elev,precTimes,self.defaultData(3.0,len(precTimes))))
				s_ra.append((wsId,xx,yy,elev,precTimes,self.defaultData(100.0,len(precTimes))))
			else:
				self.progress.setInfo('Weather station %s <id: %s>has no valid precipitation table'%(wsName,wsId), True)
		
		# export to mat file
		sp = np.array(sp, dtype=[('code', 'O'), ('est', 'O'), ('nord', 'O'), ('quota', 'O'), ('time', 'O'), ('dati', 'O')])
		self.saveAsMAT(matFileName,sp,'sp',self.progress)
		s_ta_max = np.array(s_ta_max, dtype=[('code', 'O'), ('est', 'O'), ('nord', 'O'), ('quota', 'O'), ('time', 'O'), ('dati', 'O')])
		self.saveAsMAT(matFileName,s_ta_max,'s_ta_max',self.progress)
		s_ta_min = np.array(s_ta_min, dtype=[('code', 'O'), ('est', 'O'), ('nord', 'O'), ('quota', 'O'), ('time', 'O'), ('dati', 'O')])
		self.saveAsMAT(matFileName,s_ta_min,'s_ta_min',self.progress)
		s_ua = np.array(s_ua, dtype=[('code', 'O'), ('est', 'O'), ('nord', 'O'), ('quota', 'O'), ('time', 'O'), ('dati', 'O')])
		self.saveAsMAT(matFileName,s_ua,'s_ua',self.progress)
		s_vv = np.array(s_vv, dtype=[('code', 'O'), ('est', 'O'), ('nord', 'O'), ('quota', 'O'), ('time', 'O'), ('dati', 'O')])
		self.saveAsMAT(matFileName,s_vv,'s_vv',self.progress)
		s_ra = np.array(s_ra, dtype=[('code', 'O'), ('est', 'O'), ('nord', 'O'), ('quota', 'O'), ('time', 'O'), ('dati', 'O')])
		self.saveAsMAT(matFileName,s_ra,'sp',self.progress)
			
	def getPrecipitationData(self,dataLayer, f_time, f_intensity):
		features = dataLayer.getFeatures()
		# get data
		timeSteps = []
		precInt = []
		for feat in features:
			timeSteps.append(feat[f_time])
			precInt.append(feat[f_intensity])
		
		# resample data to fit simulation parameters
		simTimeSteps = np.linspace(0.5*self.timeStep, self.simTime-0.5*self.timeStep, self.simTime/self.timeStep)
		simPrecInt = np.interp(simTimeSteps, timeSteps, precInt)
		simPrecDepth = simPrecInt*self.timeStep
		
		return simTimeSteps,simPrecInt,simPrecDepth
		
	def timeStepsToOrdinal(self, timeSteps):
		d = datetime.datetime.now()
		dd = d.toordinal() + 366
		#timeSteps = timeSteps*60/86400
		timeSteps = timeSteps/24.0 #hours to days
		dd = dd+timeSteps
		return dd
		
	def flipArray(self,x):
		y = x[None]
		y = y.T
		return y
		
	def defaultData(self,val, num):
		a = np.zeros(num)+val
		a = self.flipArray(a)
		return a

	def featToCoordArray(self,feature):
		xs = []
		ys = []
		
		geom = feature.geometry()
		geomType = geom.wkbType()
		
		if geomType==QgsWkbTypes.Point:
			vertex = geom.asPoint()
			xs.append(vertex[0])
			ys.append(vertex[1])
			
		if geomType==QgsWkbTypes.MultiPoint:
			multiPoint = geom.asMultiPoint()
			vertex = multiPoint[0]
			xs.append(vertex[0])
			ys.append(vertex[1])
			
		if geomType==QgsWkbTypes.LineString:
			print('Layer is a line layer')

		if geomType==QgsWkbTypes.Polygon:
			print('Layer is a polygon layer')

		if geomType==QgsWkbTypes.MultiPolygon:
			print('Layer is a multi-polygon layer')

		if geomType==100:
			print('Layer is a data-only layer')

		return xs,ys
		
	def saveAsMAT(self,filename,data, name,progress = None):
		dataDict = {}
		
		if os.path.exists(filename):
			dataDict = sio.loadmat(filename)
		
		dataDict[name] = data
		
		try:
			sio.savemat(filename, dataDict,do_compression =True)
			if progress is not None: progress.setInfo('Data %s are exported to %s'%(name,filename),False)
		except IOError:
			#print 'Cannot save file: %s' %filename
			if progress is not None: progress.setInfo('Cannot save to %s because %s' %(filename,str(IOError)),True)
			