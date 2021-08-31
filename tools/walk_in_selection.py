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

# Import the PyQt and QGIS libraries
from qgis.core import *

class walkInSelection:

	def __init__(self, lay, nodesLayer = None):
		self.lay = lay
		self.nodesLayer = nodesLayer

		# set up tolerance, etc, ...
		crs = self.lay.crs().authid()
		if crs == 'EPSG:4269':
			self.rec = .0001
			self.tol = .0001
		else:
			self.rec = 1
			self.tol = 1

	def unload(self):
		pass

	def getNodeByID(self,nodeId):
		if self.nodesLayer is None: return None
		expr = QgsExpression( "\"%s\" like '%s'"%('OBJ_ID',nodeId))
		features = self.nodesLayer.getFeatures( QgsFeatureRequest( expr ) )
		feat = QgsFeature()
		features.nextFeature(feat)
		return feat

	def getData(self):
		# setup empty variables
		cumDist = []
		elev = []
		diams = []
		elevTop = []
		elevBot = []
		dimList = []
		nodeId = []
		linkId = []

		# make a temporary layer with selected features list
		feats = [feat for feat in self.lay.selectedFeatures()]

		if len(feats)==0:
			return cumDist,elev,diams,elevBot, elevTop,dimList

		cumDist = [0.0]

		# Convert its geometry type enum to a string we can pass to
		# QgsVectorLayer's constructor
		layGeometryType = ['Point','Line','Polygon'][self.lay.geometryType()]
		#print 'lay type:',self.lay.geometryType()
		layGeometryType = 'MultiLineString'
		#print 'layGeometryType:',layGeometryType

		# Convert its CRS to a string we can pass to QgsVectorLayer's constructor
		layCRS = self.lay.crs().authid()

		# Make the output layer
		mem_layer = QgsVectorLayer(layGeometryType + '?crs='+layCRS, self.lay.name() + u'_copy', 'memory')
		#print 'mem_layer:',mem_layer
		#~ with edit(mem_layer):
		mem_layer_data = mem_layer.dataProvider()
		attr = self.lay.dataProvider().fields().toList()
		mem_layer_data.addAttributes(attr)
		mem_layer.updateFields()
		mem_layer_data.addFeatures(feats)
		#print 'ok edit!'

		# select the first element
		for feat in mem_layer.getFeatures():
			#print 'ok selection:',feat.id()
			mem_layer.select(feat.id())
			break

		# go upstream to find the start point
		FT = flowTrace(mem_layer,-1)
		ids = FT.select(None,None)
		#print 'ids upstream:',ids

		#print 'the upper link:',ids[-1]

		# select the last feature ids
		mem_layer.removeSelection()

		mem_layer.select(ids[-1])

		# walk downstream to collect elevation and distance
		FT = flowTrace(mem_layer,1)
		ids = FT.select(None,None)
		#print 'ids downstream:',ids

		# go to the id list and get attributes
		isFirst = True
		for id in ids:
			iterator = mem_layer.getFeatures(QgsFeatureRequest().setFilterFid(id))
			feature = next(iterator)
			linkId.append(feature["OBJ_ID"])
			dist = feature["LENGTH"]
			if (dist == NULL): dist = None
			newDist = cumDist[-1]+dist
			elev_start = feature["ELEV_START"]
			if (elev_start == NULL): elev_start = None
			cumDist.append(newDist)
			elev.append(elev_start)
			elev_end = feature["ELEV_END"]
			if (elev_end == NULL): elev_end = None
			cumDist.append(newDist)
			elev.append(elev_end)
			d = feature['DIAM']
			if (d == NULL):
				d = feature['DIM1']
			if (elev_end == NULL): d = None
			diams.append(d)
			diams.append(d) #add twice

			# get also the start and ending node
			if isFirst:
				startNode = feature['NODE_START']
				node = self.getNodeByID(startNode)
				isFirst = False
				if node:
					nodeId.append(node["OBJ_ID"])
					elevTop.append(node['ELEV_TOP'])
					elevBot.append(node['ELEV_BOT'])
					surf = node['AREA']
					if (surf == NULL):
						dim = 1.0
					else:
						dim = 2.0*(surf/3.14)**0.5
					dimList.append(dim)

			endNode = feature['NODE_END']
			node = self.getNodeByID(endNode)
			if node:
				nodeId.append(node["OBJ_ID"])
				elevTop.append(node['ELEV_TOP'])
				elevBot.append(node['ELEV_BOT'])
				surf = node['AREA']
				if (surf == NULL):
					dim = 1.0
				else:
					dim = 2.0*(surf/3.14)**0.5
				dimList.append(dim)

		#delete last item
		cumDist = cumDist[:-1]
		#print 'cumDist:',cumDist
		#print 'elev:',elev
		return cumDist,elev,diams,elevBot, elevTop,dimList,linkId,nodeId


class flowTrace:

	def __init__(self,lay, direction = -1):
		self.lay = lay
		
		# set up tolerance, etc, ...
		crs = self.lay.crs().authid()
		if crs == 'EPSG:4269':
			self.rec = .0001
			self.tol = .0001
		else:
			self.rec = 1
			self.tol = 1
			
		# set up direction
		if direction <0:
			self.up = 0
			self.down = -1
		else:
			self.up = -1
			self.down = 0

	def unload(self):
		pass

	# select 
	def select(self,xpos=None,ypos=None):
		#setup final selection list
		final_list = []
		#setup temporary selection list
		selection_list = []
		
		# get layer type
		if self.lay.wkbType()!=QgsWkbTypes.LineString and self.lay.wkbType()!=QgsWkbTypes.MultiLineString and self.lay.wkbType()!=QgsWkbTypes.LineString25D and self.lay.wkbType()!=QgsWkbTypes.MultiLineString25D:
			return None

		#get provider
		provider = self.lay.dataProvider()
		#get current selection or select feature by point
		features = self.lay.selectedFeatures()
		
		if (len(features)==0) and not (xpos is None) and not (ypos is None):
			searchRect = QgsRectangle(xpos-self.rec,ypos-self.rec,xpos+self.rec,ypos+self.rec)
			request = QgsFeatureRequest().setFilterRect(searchRect)
			features = self.lay.getFeatures(request)
		
		if len(features)==0:
			# return empty final list
			return final_list
			
		#iterate through features to add to lists
		for feature in features:			
			# add selected features to final list
			final_list.append(feature.id())
			# add selected features to selection list for while loop
			selection_list.append(feature.id())
			
		#loop through selection list
		while selection_list:
			#get selected features
			request = QgsFeatureRequest().setFilterFid(selection_list[0])
			feature = QgsFeature()
			self.lay.getFeatures(request).nextFeature(feature)
			
			# get list of nodes
			try:
				nodes = feature.geometry().asPolyline()
				#~ print 'nodes:',nodes
			except:
				nodes = feature.geometry().asMultiPolyline()
				nodes = nodes[0]
				#~ print 'nodes:',nodes
				
			# get upstream node
			upstream_coord = nodes[self.up]
						
			# select all features around upstream coordinate using a bounding box
			searchRect = QgsRectangle(upstream_coord.x() - self.rec, upstream_coord.y() - self.rec, upstream_coord.x() + self.rec, upstream_coord.y() + self.rec)
			request = QgsFeatureRequest().setFilterRect(searchRect)
			features = self.lay.getFeatures(request)
						
			#iterate through requested features
			for feature in features:
				#get list of nodes
				#print feature.id()
				try:
					nodes = feature.geometry().asPolyline()
				except:
					nodes = feature.geometry().asMultiPolyline()
					nodes = nodes[0]
					#~ print 'nodes:',nodes
				
				#get downstream node
				downstream_coord = nodes[self.down]
				
				#setup distance
				distance = QgsDistanceArea()
				
				#get distance from downstream node to upstream node
				dist = distance.measureLine(downstream_coord, upstream_coord)
				
				#Below is the distance rounded to 2 decimal places only needed during testing
				#dist = round (distance.measureLine(downstream_coord, upstream_coord), 2)
				
				if dist < self.tol:
					#add feature to final list
					final_list.append(feature.id())
					
					#add feature to selection list to keep selecting upstream line segments
					#selection_list.append(feature.id())
										
					if feature.id() not in selection_list:
						#add feature to selection list
						selection_list.append(feature.id())
				
			#remove feature from selection list
			selection_list.pop(0)
			
		# return final list
		return final_list

