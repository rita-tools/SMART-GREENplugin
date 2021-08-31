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

from qgis.core import *

#~ import logging

class DrainageGeomExporter():
	
	def __init__(self, progress = None):
		self.linksLayer = None
		self.nodesLayer = None
		self.grid = None
		self.DBM = None
		self.progress = progress
		#~ logging.basicConfig(filename='d:/test_smartgreen/testlog2.log',level=logging.DEBUG)
		
	def setLinksLayer(self,linksLayer,f_id,f_shape,f_diam,f_d1,f_d2,f_d3,f_d4,f_z1,f_z2,f_n1,f_n2,f_length,f_mann,f_table):
		self.linksLayer = linksLayer
		self.f_id = f_id
		self.f_shape = f_shape
		self.f_diam = f_diam
		self.f_d1 = f_d1
		self.f_d2 = f_d2
		self.f_d3 = f_d3
		self.f_d4 = f_d4
		self.f_z1 = f_z1
		self.f_z2 = f_z2
		self.f_n1 = f_n1
		self.f_n2 = f_n2
		self.f_length = f_length
		self.f_mann = f_mann
		self.f_table = f_table
		
	def setNodesLayer(self,nodesLayer,f_nodeid,f_zb,f_zg,f_astore,f_table):
		self.nodesLayer = nodesLayer
		self.f_nodeid = f_nodeid
		self.f_zb = f_zb
		self.f_zg = f_zg
		#self.f_yfull = f_yfull
		self.f_astore = f_astore
		self.f_table = f_table
		
	def setGrid(self, grid):
		self.grid = grid
		
	def setDBM(self,DBM):
		self.DBM = DBM
		
	def resetFeatureId(self):
		# it seems not working
		with edit(self.nodesLayer):
			i = 0
			for feat in self.nodesLayer.getFeatures():
				feat.setFeatureId(i)
				i+=1
		
		with edit(self.linksLayer):
			i = 0
			for feat in self.linksLayer.getFeatures():
				feat.setFeatureId(i)
				i+=1
	
	def rowIdLookUpTables(self):
		self.linksRows = {}
		i = 1
		for feat in self.linksLayer.getFeatures():
			self.linksRows.update({feat.id():i})
			i+=1
		
		self.nodesRows = {}
		i = 1
		for feat in self.nodesLayer.getFeatures():
			self.nodesRows.update({feat.id():i})
			i+=1

	def featToCoordArray(self,feature):
		xs = []
		ys = []
		
		geom = feature.geometry()
		geomType = geom.wkbType()
		#print 'geomType:',geomType
		
		if geomType==QgsWkbTypes.Point:
			vertex = geom.asPoint()
			#print 'vertex of point string:',vertex
			xs.append(vertex[0])
			ys.append(vertex[1])
			
		if geomType==QgsWkbTypes.LineString:
			vertex = geom.asPolyline()
			#print 'vertex of line string:',vertex
			n = len(vertex[0])
			for i in range(n):
				xs.append(vertex[i][0])
				ys.append(vertex[i][1])
				
		if geomType==QgsWkbTypes.Polygon:
			vertex = geom.asPolygon()
			
		if geomType==QgsWkbTypes.MultiPoint:
			#~ print 'Layer is a multi-point layer'
			multiPoint = geom.asMultiPoint()
			#print 'multiPoint string:',multiPoint
			vertex = multiPoint[0]
			xs.append(vertex[0])
			ys.append(vertex[1])
			
		if (geomType==QgsWkbTypes.MultiLineString) or (geomType==QgsWkbTypes.MultiLineString25D):
			#~ print 'Layer is a multi-line layer'
			multiLine = geom.asMultiPolyline()
			#print 'multiLine string:',multiLine
			#print 'multiLine:',multiLine
			#~ vertex = multiLine[0]
			#~ n = len(vertex[0])
			#~ for i in range(n):
				#~ xs.append(vertex[i][0])
				#~ ys.append(vertex[i][1])
			# fix multiple segments line
			for line in multiLine:
				for vertex in line:
					xs.append(vertex[0])
					ys.append(vertex[1])
			
			
		if geomType==QgsWkbTypes.MultiPolygon:
			if self.progress is not None: self.progress.setInfo('Unmanaged layer type: %s (multi-polygon)'%(geomType),True)
			return

		if geomType==100:
			if self.progress is not None: self.progress.setInfo('Unmanaged layer type: %s (data-only)'%(geomType),True)
			return
			
		return xs,ys
		
	def sectionGeometry(self, sec_type,diam,d1,d2,d3,d4,mann,slope):
		# set NULL to np.nan
		if (diam == NULL): diam = np.nan
		if (d1 == NULL): d1 = np.nan
		if (d2 == NULL): d2 = np.nan
		if (d3 == NULL): d3 = np.nan
		if (d4 == NULL): d4 = np.nan
		if (mann == NULL): mann = np.nan
		if (slope == NULL): slope = np.nan
		
		if sec_type in ['C', 'CIRCULAR','04']:
			#print 'is circular'
			sec_type = 'CIRCULAR'
			d1 = diam
			D = diam
			d1derived = np.nan
			yFull = D
			Afull = 0.25*np.pi*D*D
			Rfull = 0.25*D
			wMax = D
			yWmax = 0.5*D
			isopen = 0
			h96 = 0.96*D
			w96yFull  = 2*((0.5*D)**2-(h96-0.5*D)**2)**0.5
			
		if sec_type in ['T', 'TRAPEZOIDAL']:
			# d1 = heigth
			# d2 = bottom width
			# d3 = slope of rigth side wall (horizontal upper cathetus/height)
			# d4 = slope of left side wall (horizontal upper cathetus/height)
			sec_type = 'TRAPEZOIDAL'
			h = d1
			wBot = d2
			s1 = d3
			s2 = d4
			wMax = wBot + h*(s1+s2)
			d1derived = (1+s1^2)^0.5 + (1+s2^2)^0.5 #length of side walls per unit of depth
			yFull = h
			Afull = (wBot + wMax)*h*0.5
			Rfull = Afull/(wBot+h*d1derived)
			wMax = wMax
			yWmax = h
			isopen = 1
			w96yFull = wBot+0.96*h*(s1+s2)
			
		if sec_type in ['R', 'RECTANGULAR','05']:
			sec_type = 'RECTANGULAR'
			# d1 = height
			# d2 = width
			
			d1derived = np.nan
			yFull = d1
			Afull = d1*d2
			Rfull = Afull/(2*d1+d2) # TODO check hydraulic radius
			wMax = d2
			yWmax = d1
			isopen = 0
			w96yFull = d2
		
		# TODO: Vfull
		#~ print 'mann:',mann
		#~ print 'slope:',slope
		#~ print 'Rfull:',Rfull
				
		Vfull = (1.0/mann)*(np.absolute(slope)**0.5)*Rfull**(2.0/3.0) #normal flow at full conditions
		###ret(i).geometry.Vfull = 1/ret(i).manning*sqrt(ret(i).slope)*ret(i).geometry.Rfull^(2/3); %normal flow at full conditions
		
		#np.array([sec_type], dtype='<U8')
		geomTuple = (np.array([sec_type]),\
							np.array([[d1]]),np.array([[d2]]),np.array([[d3]]),np.array([[d4]]),\
							np.array([[d1derived]]),np.array([[yFull]]),np.array([[Afull]]),np.array([[Rfull]]),\
							np.array([[wMax]]),np.array([[yWmax]]),np.array([[isopen]], dtype=np.uint8),np.array([[w96yFull]]),
							np.array([[Vfull]]))
		
		geomArray = np.array([[geomTuple]],\
										dtype=[('shape', 'O'), ('d1', 'O'), ('d2', 'O'), ('d3', 'O'), ('d4', 'O'),\
													('d1derived', 'O'), ('yFull', 'O'), ('Afull', 'O'), ('Rfull', 'O'),\
													('wMax', 'O'), ('yWmax', 'O'),('isopen', 'O'), ('w96yFull', 'O'),('Vfull', 'O')])
		
		return geomArray


	def linksToMat(self,matFileName):
		## ret      = struct('code',id,'xx',X,'yy',Y,'invert1',invert1,'invert2',invert2,'L',L,'slope',slope,'manning',manning,'geometry',[],'n1code',n1,'n2code',n2);
		
		"""
		INPUTS:
		f_id	   = name of field containing conduits unique ID [string]
		f_shape	= name of field containing conduits shape code - required (missing causes exiting) [string]
		f_d1	   = name of fields containing conduits cross section characteristic length d1 - required - [cell array of strings]
		f_d2	   = name of fields containing conduits cross section characteristic length d2 - optional - [cell array of strings or void] 
		f_d3	   = name of fields containing conduits cross section characteristic length d3 - optional - [cell array of strings or void]
		f_d4	   = name of fields containing conduits cross section characteristic length d4 - optional - [cell array of strings or void]
		f_z1	   = name of field containing conduit invert elevation at starting point - required (missing causes exiting) [string]
		f_z2	   = name of field containing conduit invert elevation at final point - required (missing causes exiting) [string]
		f_n1	   = name of field containing code of conduit starting node - required (missing causes exiting) [string]
		f_n2	   = name of field containing code of conduit final node - required (missing causes exiting) [string]
		f_length   = name of field containing conduits length - optional - [string or void]
		f_mann	 = name of field containing conduits Manning's coefficient - optional - [string or void] 

		OUTPUTS:
		ret		= conduits structure
					.code	= conduit unique ID [1x1]
					.xx	  = conduit x-coordinates [double array]
					.yy	  = conduit y-coordinates [double array]
					.invert1 = conduit invert elevation at starting point (m a.s.l.) [1x1]
					.invert2 = conduit invert elevation at final point (m a.s.l.) [1x1]
					.L	   = conduit length (m) [1x1]
					.slope   = conduit slope (-) [1x1]
					.manning = conduit Manning's coefficient (s/m^1/3) [1x1]
					.n1code  = code of conduit starting node (-) [1x1]
					.n2code  = code of conduit final node (-) [1x1]
					.geometry.shape = conduit cross sectional shape [string] - 'CIRCULAR' 'RECTANGULAR' 'TRAPEZOIDAL'
					.geometry.d1	= cross section characteristic length scale d1 (m) [1x1]
					.geometry.d2	= cross section characteristic length scale d2 (m) [1x1]
					.geometry.d3	= cross section characteristic length scale d3 (m) [1x1]
					.geometry.d4	= cross section characteristic length scale d4 (m) [1x1]

		"""
		
		attrList = []
		#print 'in linksToMat',self.linksLayer
		featNum = self.linksLayer.featureCount()
		features = self.linksLayer.getFeatures()
		# update row id lookup table
		self.rowIdLookUpTables()
		
		i = 0
		for feat in features:
			i+=1
			if self.progress is not None: self.progress.setPercentage(100.0*i/float(featNum))
		
			# get geometry
			xx,yy = self.featToCoordArray(feat)
			# get attributes
			#dtype=[('code', 'O'),('xx', 'O'),('yy', 'O'),('invert1', 'O'),('invert2', 'O'),('L', 'O'),('slope', 'O'),('manning', 'O'),('geometry', 'O'),('n1code', 'O'),('n2code', 'O'),
			# ('n1', 'O'),('n2', 'O'),('offset1', 'O'),('offset2', 'O')])
			#linkId = np.array([[feat[self.f_id]]], dtype=np.uint16)
			linkId = np.array([[feat[self.f_id]]])
			xx = np.array([xx])
			yy = np.array([yy])
			invert1 = np.array([[feat[self.f_z1]]])
			invert2 = np.array([[feat[self.f_z2]]])
			L = np.array([[feat[self.f_length]]])

			try: slope = (feat[self.f_z1]-feat[self.f_z2])/feat[self.f_length]
			except: slope = 0.0

			manning = np.array([[feat[self.f_mann]]])
			#print 'geometry input',feat[self.f_shape],feat[self.f_d1],feat[self.f_d2],feat[self.f_d3],feat[self.f_d4]
			geometry = self.sectionGeometry(feat[self.f_shape],feat[self.f_diam],feat[self.f_d1],feat[self.f_d2],
											feat[self.f_d3],feat[self.f_d4],feat[self.f_mann],
											slope)

			slope = np.array([[slope]])
			#n1code = np.array([[feat[self.f_n1]]], dtype=np.uint16)
			#n2code = np.array([[feat[self.f_n2]]], dtype=np.uint16)
			n1code = np.array([[feat[self.f_n1]]])
			n2code = np.array([[feat[self.f_n2]]])
			
			node = self.getNodeByID(feat[self.f_n1])
			#n1 = np.array([[node.id()]], dtype=np.uint16)
			#n1 = np.array([[node.id()]])
			n1 = np.array([[self.nodesRows[node.id()]]])
			try: offset1 = feat[self.f_z1]-node[self.f_zb]
			except: offset1 = 0.0

			offset1 = np.array(offset1)
			
			node = self.getNodeByID(feat[self.f_n2])
			#n2 = np.array([[node.id()]], dtype=np.uint16)
			#n2 = np.array([[node.id()]])
			n2 = np.array([[self.nodesRows[node.id()]]])
			try: offset2 = feat[self.f_z2]-node[self.f_zb]
			except: offset2 = 0.0
			offset2 = np.array(offset2)
			
			# TODO: check n1 and n2 meaning (feature id?)
			
			#print feat.id(),linkId,xx,yy,invert1,invert2,L,slope,manning,geometry,n1code,n2code,n1,n2,offset1,offset2,n1,n2
			attrTuple = (linkId,xx,yy,invert1,invert2,L,slope,manning,geometry,n1code,n2code,n1,n2,offset1,offset2)
			
			attrList.append([attrTuple])
		
		
		attrArray = np.array(attrList,\
										dtype=[('code', 'O'),('xx', 'O'),('yy', 'O'),('invert1', 'O'),('invert2', 'O'),\
													('L', 'O'),('slope', 'O'),('manning', 'O'),('geometry', 'O'),\
													('n1code', 'O'),('n2code', 'O'),('n1', 'O'),('n2', 'O'),('offset1', 'O'),('offset2', 'O')])
													
		
		self.saveAsMAT(matFileName,attrArray,'ret',self.progress)

	def getNodeByID(self,nodeId):
		expr = QgsExpression( "\"%s\" like '%s'"%(self.f_nodeid,nodeId))
		features = self.nodesLayer.getFeatures( QgsFeatureRequest( expr ) )
		feat = QgsFeature()
		features.nextFeature(feat)
		return feat
		
	def getLinkByNodeId(self,nodeId,isEnd= False):
		expr = QgsExpression( "\"%s\" like '%s'"%(self.f_n1,nodeId))
		if isEnd: expr = QgsExpression( "\"%s\" like '%s'"%(self.f_n2,nodeId))
		
		features = self.linksLayer.getFeatures( QgsFeatureRequest( expr ) )
		featList = []
		for f in features:
			featList.append(f)
			
		return featList
		
	def nodesToMat(self,matFileName):
		attrList = []
		
		featNum = self.nodesLayer.featureCount()
		
		features = self.nodesLayer.getFeatures()
		i = 0
		for feat in features:
			i+=1
			if self.progress is not None: self.progress.setPercentage(100.0*i/float(featNum))
			#logging.debug('node id: %s'%feat.id())
			# get geometry
			xx,yy = self.featToCoordArray(feat)
			# get attributes
			#dtype=[('code', 'O'),('xx', 'O'),('yy', 'O'),('invert1', 'O'),('invert2', 'O'),('L', 'O'),('slope', 'O'),('manning', 'O'),('geometry', 'O'),('n1code', 'O'),('n2code', 'O'),
			# ('n1', 'O'),('n2', 'O'),('offset1', 'O'),('offset2', 'O')])
			#nodeId = np.array([[feat[self.f_nodeid]]], dtype=np.uint16)
			nodeId = np.array([[feat[self.f_nodeid]]])
			#logging.debug('nodeId: %s'%str(nodeId))
			xx = np.array([xx])
			yy = np.array([yy])
			#logging.debug('xx: %s'%str(xx))
			#logging.debug('yy: %s'%str(yy))
			invert = np.array([[feat[self.f_zb]]])
			#logging.debug('invert: %s'%str(invert))
			#yFull = np.array([[feat[self.f_yfull]]])
			yFull = np.array([[feat[self.f_zg]-feat[self.f_zb]]])
			#logging.debug('yFull: %s'%str(yFull))
			Astore = np.array([[feat[self.f_astore]]])
			#logging.debug('Astore: %s'%str(Astore))
			
			# new attribute
			linkOutList = self.getLinkByNodeId(feat[self.f_nodeid],isEnd= False)
			
			linkOutCode = []
			linkOutId = []
			crownOut = []
			for linkOut in linkOutList:
				linkOutCode.append(linkOut[self.f_id])
				#linkOutId.append(linkOut.id())
				linkOutId.append(self.linksRows[linkOut.id()])
				
				if linkOut[self.f_shape] in ['C', 'CIRCULAR','04']:
					crownOut.append(linkOut[self.f_z1] + linkOut[self.f_diam])
				else:
					crownOut.append(linkOut[self.f_z1] + linkOut[self.f_d1])
			
			#print '=== node id:',feat[self.f_nodeid]
			#print 'linkOutCode:',linkOutCode
			#print 'linkOutId:',linkOutId
			#~ linkOUTcode = np.array([linkOutCode], dtype=np.object).T
			#linkOUTcode = np.array([linkOutCode]).T
			linkOUTcode = linkOutCode
			#linkOUTcode = np.array([linkOutId]).T
			#print 'linkOUTcode:',linkOUTcode
			linkOUT = np.array([linkOutId]).T
			crown1 = np.array([crownOut]).T
			
			#~ #linkOUTcode = np.array([[np.nan]])
			#~ #linkOUT = np.array([[np.nan]])
			#~ linkOUTcode = np.array([[]])
			#~ linkOUT = np.array([[]])
			#~ crown1 = np.nan
			
			#~ if link1 is not None:
				#~ linkOUTcode = np.array([[link1[self.f_id]]])
				#~ linkOUT = np.array([[link1.id()]],dtype=np.uint16)
				#~ if link1[self.f_shape] in ['C', 'CIRCULAR','04']:
					#~ crown1 = link1[self.f_z1] + link1[self.f_diam]
				#~ else:
					#~ print 'self.f_z1:',self.f_z1
					#~ print 'self.f_d1:',self.f_d1
					#~ try:
						#~ crown1 = link1[self.f_z1] + link1[self.f_d1]
					#~ except:
						#~ print 'ERROR at link %s'%link1.id()
						#~ print 'ID:', link1['OBJ_ID']
						#~ print 'ELEV:', link1[self.f_z1]
						#~ print 'DIAM:', link1[self.f_d1]
						#~ break
				
			#~ logging.debug('linkOUTcode: %s'%str(linkOUTcode))
			#~ logging.debug('linkOUT: %s'%str(linkOUT))
			#~ logging.debug('crown1: %s'%str(crown1))
				
			linkInList = self.getLinkByNodeId(feat[self.f_nodeid],isEnd= True)
			
			linkInCode = []
			linkInId = []
			crownIn = []
			for linkIn in linkInList:
				linkInCode.append(linkIn[self.f_id])
				#linkInId.append(linkIn.id())
				#linkInId.append(self.DBM.getRowId(table='links', ids = [linkIn[self.f_id]], idFld='OBJ_ID'))
				linkInId.append(self.linksRows[linkIn.id()])
				
				if linkIn[self.f_shape] in ['C', 'CIRCULAR','04']:
					crownIn.append(linkIn[self.f_z1] + linkIn[self.f_diam])
				else:
					crownIn.append(linkIn[self.f_z1] + linkIn[self.f_d1])
					
			#~ linkINcode = np.array([linkInCode], dtype=np.object).T
			#linkINcode = np.array([linkInCode]).T
			linkINcode = linkInCode
			#linkINcode = np.array([linkInId]).T
			linkIN = np.array([linkInId]).T
			crown2 = np.array([crownIn]).T 
			
			#~ #linkINcode = np.array([[np.nan]])
			#~ #linkIN = np.array([[np.nan]])
			#~ linkINcode = np.array([[]])
			#~ linkIN = np.array([[]])
			#~ crown2 = np.nan
			
			#~ if link2 is not None:
				#~ linkINcode = np.array([[link2[self.f_id]]])
				#~ linkIN = np.array([[link2.id()]],dtype=np.uint16)
				#~ if link2[self.f_shape] in ['C', 'CIRCULAR','04']:
					#~ crown2 = link2[self.f_z2] + link2[self.f_diam]
				#~ else:
					#~ crown2 = link2[self.f_z2] + link2[self.f_d1]
				
			#~ logging.debug('linkINcode: %s'%str(linkINcode))
			#~ logging.debug('linkIN: %s'%str(linkIN))
			#~ logging.debug('crown2: %s'%str(crown2))
			
			nodeType = np.array([[u'JUNCTION']])
			if len(linkOutList)== 0: nodeType = np.array([[u'OUTLET']])
			
			#~ logging.debug('nodeType: %s'%str(nodeType))
			allCrown = crownIn+crownOut
			#~ elevCrown = np.array([[np.nanmax([crown1,crown2])]])
			elevCrown = np.array([[np.nanmax([allCrown])]])
			#~ logging.debug('elevCrown: %s'%str(elevCrown))
			yCrown    = elevCrown - np.array([[feat[self.f_zb]]])
			#~ print 'feat.id:',feat.id()
			#~ print 'crown1:',crown1
			#~ print 'crown2:',crown2
			#~ print 'elevCrown:',elevCrown
			#~ print 'feat[self.f_zb]:',feat[self.f_zb]
			#~ print 'yCrown:',yCrown
			
			#~ logging.debug('yCrown: %s'%str(yCrown))
			#Hfull     = np.array([[feat[self.f_yfull] + feat[self.f_zb]]])
			Hfull     = np.array([[feat[self.f_zg]]])
			
			#~ logging.debug('Hfull: %s'%str(Hfull))
			
			c,r = self.grid.coordToCell(xpos = xx[[0]], ypos=yy[[0]])
			#~ logging.debug('c,r: %s,%s'%(c,r))
			#cell = np.array([[self.grid.sub2ind(rows = r, cols = c)]], dtype=np.uint16)
			#print 'id: %s, row: %s, col: %s'%(nodeId,r,c)
			cell = np.array([[self.grid.sub2ind(rows = r, cols = c)]])
			#~ logging.debug('cell: %s'%(cell))
		
			attrTuple = (nodeId,xx,yy,invert,yFull,Astore,linkINcode,linkOUTcode,linkIN,linkOUT,nodeType,elevCrown,yCrown,Hfull,cell)
			#print 'attrTuple',attrTuple
			#logging.debug(attrTuple)
			
			attrList.append([attrTuple])
			#~ logging.debug('=== end point ===')
		
		attrArray = np.array(attrList,\
									dtype=[('code', 'O'), ('xx', 'O'), ('yy', 'O'), ('invert', 'O'), ('yFull', 'O'), ('Astore', 'O'),
									('linkINcode', 'O'), ('linkOUTcode', 'O'), ('linkIN', 'O'), ('linkOUT', 'O'),
									('type', 'O'), ('elevCrown', 'O'), ('yCrown', 'O'), ('Hfull', 'O'),
									('cell', 'O')])
									
		self.saveAsMAT(matFileName,attrArray,'node',self.progress)
		
	def saveAsMAT(self,filename,data, name,progress = None):
		dataDict = {}
		
		if os.path.exists(filename):
			dataDict = sio.loadmat(filename)
		
		dataDict[name] = data
		
		try:
			sio.savemat(filename, dataDict,do_compression =True)
			if self.progress is not None: progress.setInfo('Data %s are exported to %s'%(name,filename),False)
		except IOError:
			#print 'Cannot save file: %s' %filename
			if self.progress is not None: progress.setInfo('Cannot save to %s because %s' %(filename,str(IOError)),True)
		except:
			if self.progress is not None: progress.setInfo('Unmanaged error on "%s"' %(name),True)