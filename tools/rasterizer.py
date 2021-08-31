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

from qgis.core import *

from my_progress import MyProgress

class Rasterizer():
	def __init__(self,grid,progress = None):
		self.grid = grid
		
		if progress is None:
			self.progress = MyProgress()
		else:
			self.progress = progress
		
	def polyToRaster(self,polyLayer,fieldName='',multiply = 1.0,defaultValue=1):
		# get field index
		valueIdx = polyLayer.fields().indexFromName(fieldName)
		#~ print 'default value:',defaultValue
		#~ print 'field:',fieldName
		#~ print 'field idx:',valueIdx
		polyType = polyLayer.wkbType()
		# loop for each polygons
		i = -1
		#print 'name:',polyLayer.name()
		for poly in polyLayer.getFeatures():
			i+=1
			if valueIdx != -1: polyValue = poly.attributes()[valueIdx]
			elif type(defaultValue) is list:
				#print 'len of defaultValue:',len(defaultValue)
				#print 'feature:',i
				try:
					polyValue = defaultValue[i]
				except:
					polyValue = None
					
			else: polyValue = defaultValue
			
			if (polyValue == NULL):
				# go next
				continue
				
			if polyValue is None:
				# go next
				continue
			
			polyValue = float(polyValue)*multiply
			
			#~ print 'polyValue:',polyValue
			#~ if self.progress:	self.progress.setInfo('Processing polygon %s with value %s and type %s' %(i,polyValue,polyType))
		
			if polyType == QgsWkbTypes.MultiPolygon: # check multipolygon
				#~ print 'Is a multypolygon'
				self.scanMultiPoly(poly,polyValue)
			else:
				#~ print 'Is a singlepolygon'
				#~ print poly.geometry().asPolygon()
				self.scanLine(poly,polyValue)
	
	def scanMultiPoly(self,poly,polyValue):
		polyGeom = poly.geometry()
		for part in polyGeom.asGeometryCollection():
			#print 'type:',part.type()
			#print part.asPolygon()
			#print 'type:',part.asPolygon().type()
			singlePoly = QgsFeature()
			#singlePoly.setGeometry(part)
			singlePoly.setGeometry(QgsGeometry.fromPolygonXY([self.getPointList(part)]))
			self.scanLine(singlePoly,polyValue)
			
	def getPointList(self,geom):
		polygon = geom.asPolygon()
		#n = len(polygon[0])
		ptList = []
		for xy in polygon[0]:
			ptList.append(QgsPointXY(xy[0],xy[1]))
		
		return ptList
		
	def scanLine(self, poly,polyValue):
		#~ if self.progress:	self.progress.setInfo('Processing polygon %s with value %s' %(poly.id(),polyValue))
		isValid = False
		polyGeom = poly.geometry()
		#print polyGeom.asPolygon()
		# get extension of the poly
		bb = polyGeom.boundingBox()
		# calcolate raster dimension
		xll = bb.xMinimum()
		yll = bb.yMinimum()
		xur = bb.xMaximum()
		yur = bb.yMaximum()
		# transform extention to cell coordinates
		cll,rll = self.grid.coordToCell(xll, yll)
		cur,rur = self.grid.coordToCell(xur, yur)
		#~ print 'poly'
		#~ print polyGeom.exportToWkt()
		
		#~ print 'poly %s limit in cells:'%poly.id()
		#~ print 'll:',cll,rll
		#~ print 'ur',cur,rur
		# test all vertical lines
		if self.progress: self.progress.setPercentage(0) 
		for col in range(cll,cur+1,1):
			if self.progress: self.progress.setPercentage(100*float(col)/(cur+1-cll)) 
			# transform line cells to coordinates
			x0,y0 = self.grid.cellToCoord(col, rur)
			x1,y1 = self.grid.cellToCoord(col, rll)
			# create a new line
			pt0 = QgsPointXY(x0,y0+2*self.grid.dy)
			pt1 = QgsPointXY(x1,y1-2*self.grid.dy)
			line = QgsGeometry.fromPolylineXY([pt0,pt1])
			#print line.exportToWkt()
			# get intersection with polygon
			pts = self.linePolyIntersections(line,polyGeom)
			# check number of insertection is even
			#print 'Num. of intersections:',len(pts)
			#~ if len(pts) == 0:
				#~ if self.progress is not None:
					#~ self.progress.setInfo('Zero intersections between line %s and polygon %s. This can mean errors in geometry!'%(line.exportToWkt(),polyGeom.exportToWkt()))
					#~ self.progress.setPercentage(0) 
				#~ pass
			
			if len(pts) % 2 != 0:
				if self.progress is not None:
					self.progress.setInfo('Odd number of intersections %s' %len(pts))
					self.progress.setPercentage(0) 
				pass
			
			# loop in intersections and assign values to grid
			i = 0
			while i <= len(pts)-2:
				isValid = True
				y1 = pts[i].y()
				y2 = pts[i+1].y()
				# get row index
				c1,r1 = self.grid.coordToCell(x0, y1)
				c2,r2 = self.grid.coordToCell(x1, y2)
				# assign new value to the cell inside the range
				#print 'row lim:',y1,y2,r1,r2
				#self.data[(self.nrows-r2):(self.nrows-r1),c1] = polyValue
				#self.grid.data[(r1+1):(r2+1),c1] = polyValue
				# because it is zero based
				if c1< self.grid.ncols:
					self.grid.data[r1:r2,c1] = polyValue 
					
				i+=2 # go to the next couple of consecutive intersections
		
		#~ if not isValid:
			#~ if self.progress is not None:
				#~ self.progress.setInfo('Polygon %s as no intersections. This can mean errors in geometry!'%(polyGeom.exportToWkt()))
		
	def linePolyIntersections(self,lineGeom,polyGeom):
		intersections = polyGeom.intersection(lineGeom)
		points = self.parseIntersections(intersections)
		return points
		
	def parseIntersections(self,intersections):
		points = []
		wkt = intersections.asWkt()
		#print 'intersection:',wkt
		# split in two parts
		toks = wkt.split(' (',2)
		if len(toks) == 2:
			wkt = toks[1]
			# remove unused characters
			wkt = wkt.replace('),(',' ')
			wkt = wkt.replace('(','')
			wkt = wkt.replace(')','')
			wkt = wkt.replace(',','')
			# split in to number string
			toks = wkt.split(' ')
			i = 0
			while i < len(toks)-1:
				x = float(toks[i])
				y = float(toks[i+1])
				points.append(QgsPointXY(x,y))
				i+=2
		
		return points
			
if __name__ == '__console__':
	from gis_grid import GisGrid
	from my_progress import MyProgress
	# get active layer
	lay = iface.activeLayer()
	
	mask=None
	for lyr in QgsProject.instance().mapLayers().values():
		if lyr.name() == "Area drenata":
			mask = lyr
			break
	
	polyGrid = GisGrid()
	polyGrid.fitToLayer(mask,5,5)

	# rasterize
	prog = MyProgress()
	rast = Rasterizer(grid = polyGrid,progress = prog)
	rast.polyToRaster(lay,fieldName='WG0',defaultValue=1)
	polyGrid.saveAsASC('c:/test2/wg0.asc', progress = prog)
	polyGrid.saveAsMAT('c:/test2/wg0.mat','wg0',progress = prog)
	