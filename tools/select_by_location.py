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

from processing.tools import vector
import processing
from qgis.core import QgsGeometry, QgsFeatureRequest

from my_progress import MyProgress

def selectByLocation(inputLayer,selectLayer,method,predicates,precision, progress = None):
	processing.run("native:selectbylocation",
				   {'INPUT': inputLayer.name(), 'PREDICATE': [0],
					'INTERSECT': selectLayer.name(), 'METHOD': method})

def selectByLocationOLD(inputLayer,selectLayer,method,predicates,precision, progress = None):
	
	if progress is None:
		progress = MyProgress()
	
	oldSelection = set(inputLayer.selectedFeatureIds())
	inputLayer.removeSelection()
	index = vector.spatialindex(inputLayer)

	if 'disjoint' in predicates:
		disjoinSet = []
		for feat in vector.features(inputLayer):
			disjoinSet.append(feat.id())

	geom = QgsGeometry()
	selectedSet = []
	features = vector.features(selectLayer)
	total = 100.0 / len(features)
	for current, f in enumerate(features):
		geom = vector.snapToPrecision(f.geometry(), precision)
		bbox = vector.bufferedBoundingBox(geom.boundingBox(), 0.51 * precision)
		intersects = index.intersects(bbox)

		for i in intersects:
			request = QgsFeatureRequest().setFilterFid(i)
			feat = inputLayer.getFeatures(request).next()
			tmpGeom = vector.snapToPrecision(feat.geometry(), precision)

			res = False
			for predicate in predicates:
				if predicate == 'disjoint':
					if tmpGeom.intersects(geom):
						try:
							disjoinSet.remove(feat.id())
						except:
							pass  # already removed
				else:
					if predicate == 'intersects':
						res = tmpGeom.intersects(geom)
					elif predicate == 'contains':
						res = tmpGeom.contains(geom)
					elif predicate == 'equals':
						res = tmpGeom.equals(geom)
					elif predicate == 'touches':
						res = tmpGeom.touches(geom)
					elif predicate == 'overlaps':
						res = tmpGeom.overlaps(geom)
					elif predicate == 'within':
						res = tmpGeom.within(geom)
					elif predicate == 'crosses':
						res = tmpGeom.crosses(geom)
					if res:
						selectedSet.append(feat.id())
						break

		if progress is not None: progress.setPercentage(int(current * total))

	if 'disjoint' in predicates:
		selectedSet = selectedSet + disjoinSet

	if method == 1:
		selectedSet = list(oldSelection.union(selectedSet))
	elif method == 2:
		selectedSet = list(oldSelection.difference(selectedSet))

	return selectedSet
