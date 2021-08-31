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
import math
import os
import scipy.io as sio

from qgis.core import *

from my_progress import MyProgress

#~ import logging

class LidsExporter():
	
	def __init__(self, progress = None):
		self.lidsLayer = None
		if progress is None:
			self.progress = MyProgress()
		else:
			self.progress = progress
		#~ logging.basicConfig(filename='d:/test_smartgreen/testlog2.log',level=logging.DEBUG)
		self.Wc0 = []
		self.Wg0 = []
		self.Wp0 = []
		self.ks0 = []
		self.nodeIdx = []
		
		
	def setLidsLayer(self,lidsLayer,f_id = 'OBJ_ID',f_name = 'NAME',f_nodeTo = 'NODE_TO',f_cat = 'CAT',\
								f_vol = 'VOL', f_height = 'HEIGHT', f_diam_out='DIAM_OUT', f_height_out = 'HEIGHT_OUT',\
								f_depth = 'DEPTH', f_ks_soil = 'KS_SOIL', f_teta_sat = 'TETA_SAT', f_teta_fc = 'TETA_FC',\
								f_teta_wp = 'TETA_WP', f_slope = 'SLOPE', f_wp_max = 'WP_MAX', f_ks_sub = 'KS_SUB', f_type = 'TYPE'):
		self.lidsLayer = lidsLayer
		self.f_id = f_id
		self.f_name = f_name
		self.f_nodeTo = f_nodeTo
		self.f_cat = f_cat
		self.f_vol = f_vol
		self.f_height = f_height
		self.f_diam_out = f_diam_out
		self.f_height_out = f_height_out
		self.f_depth = f_depth
		self.f_ks_soil = f_ks_soil
		self.f_teta_sat = f_teta_sat
		self.f_teta_fc = f_teta_fc
		self.f_teta_wp = f_teta_wp
		self.f_slope = f_slope
		self.f_wp_max = f_wp_max
		self.f_ks_sub = f_ks_sub
		self.f_type = f_type
		
		
	def setNodesLayer(self,nodesLayer,f_nodeid,f_zb,f_zg,f_astore,f_table):
		self.nodesLayer = nodesLayer
		self.f_nodeid = f_nodeid
		self.f_zb = f_zb
		self.f_zg = f_zg
		#self.f_yfull = f_yfull
		self.f_astore = f_astore
		self.f_table = f_table
		self.rowIdLookUpTables()
		
	def setLidsGrid (self,grid):
		self.grid = grid
		
	def rowIdLookUpTables(self):
		self.nodesRows = {}
		i = 1
		for feat in self.nodesLayer.getFeatures():
			self.nodesRows.update({feat.id():i})
			i+=1
			
	def getNodeByID(self,nodeId):
		expr = QgsExpression( "\"%s\" like '%s'"%(self.f_nodeid,nodeId))
		features = self.nodesLayer.getFeatures( QgsFeatureRequest( expr ) )
		feat = QgsFeature()
		features.nextFeature(feat)
		return feat
		
	def featToCoordArray(self,feature):
		xs = []
		ys = []
		
		geom = feature.geometry()
		geomType = geom.wkbType()
		
		try:
			if geomType==QgsWkbTypes.Point:
				vertex = geom.asPoint()
				xs.append(vertex[0])
				ys.append(vertex[1])
				
			if geomType==QgsWkbTypes.LineString:
				vertex = geom.asPolyline()
				n = len(vertex[0])
				for i in range(n):
					xs.append(vertex[i][0])
					ys.append(vertex[i][1])

			if geomType==QgsWkbTypes.Polygon:
				vertex = geom.asPolygon()[0]
				n = len(vertex)
				for i in range(n):
					xs.append(vertex[i][0])
					ys.append(vertex[i][1])
				
			if geomType==QgsWkbTypes.MultiPoint:
				#~ print 'Layer is a multi-point layer'
				multiPoint = geom.asMultiPoint()
				vertex = multiPoint[0]
				xs.append(vertex[0])
				ys.append(vertex[1])
				
			if geomType==QgsWkbTypes.MultiLineString:
				#~ print 'Layer is a multi-line layer'
				multiLine = geom.asMultiPolyline()
				vertex = multiLine[0]
				n = len(vertex[0])
				for i in range(n):
					xs.append(vertex[i][0])
					ys.append(vertex[i][1])
				
			if geomType==QgsWkbTypes.MultiPolygon:
				multiPoly = geom.asMultiPolygon()
				#~ print 'multiPoly:',multiPoly
				vertex = multiPoly[0]
				#~ print 'vertex1:',vertex
				vertex = vertex[0]
				#~ print 'vertex2:',vertex
				n = len(vertex[0])
				for i in range(n):
					xs.append(vertex[i][0])
					ys.append(vertex[i][1])
				
			if geomType==100:
				if self.progress: self.progress.setInfo('Feature as no geometry',True)
		
		except Exception as e:
			if self.progress: self.progress.setInfo('Unable to export feature id %s because %s'%(feature.id(),str(e)),True)
				
		return xs,ys
		
	def lidsToMat(self,matFileName):
		## GIs = struct('id',id,'name',name,'xx',X,'yy',Y,'type',type,'node_code',node,'Nlayers',Nlayers,
		## 'soil_type',[],'soil_thickness',[], 'soil_porosity',[], 'soil_fieldcap',[], 'soil_wiltpoint',[],'soil_Ks',[]
		## 'veget_type',vegtype,
		## 'sublayer_type',subtype,
		## 'reserv_Vmax',Vmax,'reserv_hmax',hmax,'reserv_D',Dreserv,'reserv_Doutlet',Doutlet,'reserv_drainKs',drain_ks);
		
		## Categories of GIs 
		## 1 reservoir
		## 2 drained well
		## 3 drained reservoir
		## 4 green roof
		## 5 pervious surface
		
		attrList = []
			
		#print 'in linksToMat',self.linksLayer
		featNum = self.lidsLayer.featureCount()
		features = self.lidsLayer.getFeatures()
		i = 0
		for feat in features:
			i+=1
			if self.progress: self.progress.setPercentage(100.0*i/float(featNum))

			if (feat[self.f_nodeTo] == NULL) or ((feat[self.f_nodeTo] is None)):
				# go next
				continue

			# TODO: something better to fix unavailable node
			if feat[self.f_nodeTo] in ['','NULL','NUL','null','nul']:
				# go next
				continue


			if (feat[self.f_id] == NULL) or (feat[self.f_id] is None):
				# go next
				continue

			# general LIDS parameters
			xx, yy = self.featToCoordArray(feat)
			# get attributes
			lidId = np.array([[feat[self.f_id]]])
			lidName = np.array([[feat[self.f_name]]])
			xx = np.array([xx])
			yy = np.array([yy])
			lidCat = feat[self.f_cat] # check lid category management
			node_code = np.array([[feat[self.f_nodeTo]]])
			
			# get node row
			node = self.getNodeByID(feat[self.f_nodeTo])
			nodeId = node.id()
			# check if node exist
			if nodeId < 0: continue

			nodeRow = self.nodesRows[nodeId]

			self.nodeIdx.append(nodeRow)
			nodeRow = np.array([[nodeRow]])
			
			# get cells list
			#~ print 'min self grid:',self.grid.min()
			#~ print 'max self grid:',self.grid.max()
			#~ print 'target field:',self.f_id
			#~ print 'target value:',feat[self.f_id]
			
			idx = np.where(self.grid.data==float(feat[self.f_id]))
			#~ print 'cell coords:',idx
			r = idx[0].tolist()
			c = idx[1].tolist()
			#idx = self.grid.sub2indNew(self.grid.data.shape, r, c)
			idx = self.grid.sub2indMat(self.grid.data.shape, r, c)
			cells = np.array([idx]).T
			
			# set all parameters to NAN
			lidsType = np.array([[np.nan]])
			isolato_monte = np.array([[np.nan]])
			isolato_valle = np.array([[np.nan]])
			Nlayers = np.array([[np.nan]])
			soil_type = np.array([[np.nan]])
			soil_thickness = np.array([[np.nan]])
			soil_porosity = np.array([[np.nan]])
			soil_fieldcap = np.array([[np.nan]])
			soil_wiltpoint = np.array([[np.nan]])
			soil_Ks = np.array([[np.nan]])
			Wg_max = np.array([[np.nan]])
			Wc_max = np.array([[np.nan]])
			ks = np.array([[np.nan]])
			Wp_max = np.array([[np.nan]])
			Ks_sub = np.array([[np.nan]])
			reserv_Vmax = np.array([[np.nan]])
			reserv_hmax = np.array([[np.nan]])
			reserv_hmin = np.array([[np.nan]])
			reserv_D = np.array([[np.nan]])
			reserv_Doutlet = np.array([[np.nan]])
			reserv_drainKs = np.array([[np.nan]])
			reserv_dz2gw = np.array([[np.nan]])
			
			
			#~ print 'lidCat:',lidCat
			
			if lidCat in [1,'1']:
				#type = np.array([[3.0]])
				lidsType = np.array([int(feat[self.f_type])])
				# get reservoir specific parameters
				reserv_Vmax = np.array([feat[self.f_vol]])
				reserv_hmax = np.array([feat[self.f_height]])
				reserv_hmin = np.array([feat[self.f_height_out]])
				reserv_D = 2*((reserv_Vmax/reserv_hmax)/np.pi)**0.5 # calculate diameter from volume and height
				reserv_Doutlet = np.array([feat[self.f_diam_out]])
				reserv_drainKs = np.array([feat[self.f_ks_sub]])
				reserv_dz2gw = np.array([[99999]]) # to be fixed controll on water table
				#reserv_dz2gw = np.array([[0.0]]) # to be fixed controll on water table
				# add empty value
				self.Wg0.append(None) # add to list
				self.Wc0.append(None) # add to list
				self.ks0.append(None)
				self.Wp0.append(None)
			
			if lidCat in [2,'2']: # check mobidic u
				#type = np.array([[5.0]])
				lidsType = np.array([int(feat[self.f_type])])
				isolato_monte = np.array([[1.0]])
				isolato_valle = np.array([[1.0]])
				
				# get soil specific parameters
				Nlayers = np.array([[1.0]])
				soil_type = np.array(['standard'])
				soil_thickness = np.array([feat[self.f_depth]])
				soil_porosity = np.array([feat[self.f_teta_sat]])
				soil_fieldcap = np.array([feat[self.f_teta_fc]])
				soil_wiltpoint = np.array([feat[self.f_teta_wp]])
				soil_Ks = np.array([feat[self.f_ks_soil]])
				
				# derive soil parameters
				#print 'LID name:',lidName
				#print 'soil_porosity:',soil_porosity
				#print 'soil_fieldcap:',soil_fieldcap
				#print 'soil_thickness:',soil_thickness
				Wg_max = np.sum((soil_porosity-soil_fieldcap)*soil_thickness)
				#~ print 'Wg_max:',Wg_max
				#self.Wg0.append(Wg_max[-1].tolist()) # add to list
				self.Wg0.append(Wg_max) # add to list
				#~ print 'self.Wg0:',self.Wg0
				
				#~ print 'soil_fieldcap:',soil_fieldcap
				#~ print 'soil_wiltpoint:',soil_wiltpoint
				#~ print 'soil_thickness:',soil_thickness
				Wc_max = np.sum((soil_fieldcap-soil_wiltpoint)*soil_thickness)
				#print 'Wc_max:',Wc_max
				self.Wc0.append(Wc_max) # add to list
				#print 'self.Wc0:',self.Wc0
				
				ks = np.sum((soil_Ks*soil_thickness)/np.sum(soil_thickness))
				self.ks0.append(ks)
				
				# get vegetation specific parameters
				#Wp_max = np.array([0.001*float(self.getVegPars(lidType,'wp_max'))]) #mm to m
				Wp_max = np.array([feat[self.f_wp_max]])
				self.Wp0.append(Wp_max)
				
				# get sublayer specific parameters
				Ks_sub = np.array([feat[self.f_ks_sub]])
				
				
			#print feat.id(),linkId,xx,yy,invert1,invert2,L,slope,manning,geometry,n1code,n2code,n1,n2,offset1,offset2,n1,n2
			attrTuple = (lidId,lidName,xx,yy,lidsType,node_code,nodeRow,cells,\
								isolato_monte,isolato_valle,\
								Nlayers,soil_type,soil_thickness,soil_porosity,soil_fieldcap,soil_wiltpoint,soil_Ks,\
								Wg_max,Wc_max,ks,\
								Wp_max,\
								Ks_sub,\
								reserv_Vmax,reserv_hmax,\
								reserv_hmin,reserv_hmin,\
								reserv_D,reserv_D,reserv_Doutlet,reserv_drainKs,reserv_drainKs,\
								reserv_dz2gw,reserv_dz2gw)
			
			attrList.append([attrTuple])
			
		attrArray = np.array(attrList,\
										dtype=[('lidId', 'O'),('lidName', 'O'),('xx', 'O'),('yy', 'O'),('type', 'O'),('node_code', 'O'),('node', 'O'),('cells', 'O'),\
													('isolato_monte', 'O'),('isolato_valle', 'O'),\
													('Nlayers', 'O'),('soil_type', 'O'),('soil_thickness', 'O'),('soil_porosity', 'O'),('soil_fieldcap', 'O'),('soil_wiltpoint', 'O'),('soil_Ks', 'O'),\
													('Wg_max', 'O'),('Wc_max', 'O'),('ks', 'O'),\
													('Wp_max', 'O'),\
													('Ks_sub', 'O'),\
													('reserv_Vmax', 'O'),('reserv_hmax', 'O'),\
													('reserv_hmin', 'O'),('hmin', 'O'),\
													('reserv_D', 'O'),('reserv_drainD','O'),('reserv_Doutlet', 'O'),('reserv_drainKs', 'O'),('reserv_ks', 'O'),\
													('reserv_dz2gw', 'O'),('dz2gw', 'O')])
													
		self.saveAsMAT(matFileName,attrArray,'GIs',self.progress)
		
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
		except:
			if progress is not None: progress.setInfo('Unmanaged error on "%s"' %(name),True)