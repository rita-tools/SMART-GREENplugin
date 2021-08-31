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
 
credits: Buffer.py (C) 2012 by Victor Olaya
"""

__author__ = 'UNIMI'
__date__ = '2017-04-21'
__copyright__ = '(C) 2017 by UNIMI'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.core import QgsFeature, QgsGeometry
from qgis.core import *
from qgis.gui import *

from processing.core.ProcessingLog import ProcessingLog
from processing.tools import vector


def buffering(progress, writer, distance, field, useField, layer, dissolve,segments, fillHoles = True, idList = None):
	# TODO: in case of multiple feature, buffer should be created following the closest feature order in order to obtain ovelapping
	
	if useField:
		field = layer.fieldNameIndex(field)

	outFeat = QgsFeature()
	inFeat = QgsFeature()
	inGeom = QgsGeometry()
	outGeom = QgsGeometry()

	current = 0
	#features = vector.features(layer)
	if idList is None:
		features = layer.getFeatures()
	else:
		features = idList
	
	
	total = 100.0 / float(layer.featureCount())
	
	otherFeatures = []
	# With dissolve
	if dissolve:
		#print 'ok dissolve ...'
		first = True
		for inFeat in features:
			if isinstance(inFeat, int):
				inFeatID = inFeat
				inFeat = QgsFeature()
				layer.getFeatures(QgsFeatureRequest().setFilterFid(inFeatID)).nextFeature(inFeat)
			#print 'link id:',inFeat['OBJ_ID']
			attrs = inFeat.attributes()
			if useField:
				value = attrs[field]
			else:
				value = distance

			inGeom = QgsGeometry(inFeat.geometry())
			
			if inGeom.isEmpty():
				ProcessingLog.addToLog(ProcessingLog.LOG_WARNING, 'Feature {} has empty geometry. Skipping...'.format(inFeat.id()))
				continue
			if not inGeom.isGeosValid():
				ProcessingLog.addToLog(ProcessingLog.LOG_WARNING, 'Feature {} has invalid geometry. Skipping...'.format(inFeat.id()))
				continue
			outGeom = inGeom.buffer(float(value), int(segments))
			
			if first:
				tempGeom = QgsGeometry(outGeom)
				first = False
			else:
				if tempGeom.intersects(outGeom):
					tempGeom = tempGeom.combine(outGeom)
				else:
					#~ if progress is not None: progress.setInfo('Geometries are not intersecting. Use larger buffer distance.', True)
					#~ outFeat = QgsFeature()
					#~ outFeat.setGeometry(QgsGeometry(tempGeom))
					#~ #outFeat.setAttributes(attrs)
					#~ otherFeatures.append(outFeat)
					#~ tempGeom = QgsGeometry(outGeom)
					#~ first = True
					#print 'cannot intersect'
					pass
			
			current += 1
			if progress is not None: progress.setPercentage(int(current * total))

		if fillHoles:
			polyList = tempGeom.asPolygon()
			#polyList = tempGeom.asMultiPolygon()
			#~ tempPolyList = []
			#~ for p in polyList:
				#~ tempPolyList.append(p[0])
				
			tempGeom = QgsGeometry.fromPolygonXY([polyList[0]])
			#tempGeom = QgsGeometry.fromMultiPolygon([tempPolyList])
								
		outFeat = QgsFeature()
		outFeat.setGeometry(tempGeom)
		#outFeat.setAttributes(attrs)
		otherFeatures.append(outFeat)
		writer.addFeatures(otherFeatures)
	else:
		# Without dissolve
		for inFeat in features:
			attrs = inFeat.attributes()
			if useField:
				value = attrs[field]
			else:
				value = distance
			inGeom = QgsGeometry(inFeat.geometry())
			if inGeom.isGeosEmpty():
				ProcessingLog.addToLog(ProcessingLog.LOG_WARNING, 'Feature {} has empty geometry. Skipping...'.format(inFeat.id()))
				continue
			if not inGeom.isGeosValid():
				ProcessingLog.addToLog(ProcessingLog.LOG_WARNING, 'Feature {} has invalid geometry. Skipping...'.format(inFeat.id()))
				continue

			outGeom = inGeom.buffer(float(value), int(segments))
			outFeat.setGeometry(outGeom)
			#outFeat.setAttributes(attrs)
			writer.addFeatures([outFeat])
			current += 1
			if progress is not None: progress.setPercentage(int(current * total))

	del writer
