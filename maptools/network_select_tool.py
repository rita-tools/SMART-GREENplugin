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

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from .smartgreen_maptool import SmartGreenMapTool

# Import the PyQt and QGIS libraries
from qgis.core import *
from qgis.gui import *
import os.path
import time

class NetworkSelectTool(SmartGreenMapTool):
    """
    The map tool used to find TREES (upstream or downstream)
    """
    direction = "downstream"

    def __init__(self,iface, button,direction = -1):
        SmartGreenMapTool.__init__(self, iface, button)
        self.direction = direction
        
    def getTree(self, point):
        """
        Does the work. Tracks the graph up- or downstream.
        :param point: The node from which the tracking should be started
        """

        now = time.time()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        self.msg_bar.showMessage("X,Y = %s,%s" % (str(point.x()),str(point.y())))
        # get current layer
        lay = self.iface.activeLayer()
        
        if lay is None:
          QApplication.restoreOverrideCursor()
          later = time.time()
          difference = int(later - now)
          print('execution time %s' % (difference))
          return

        # select first segment of the layer base on the clicked point
        radius = QgsMapTool.searchRadiusMU(self.canvas)
        searchRect = QgsRectangle(self.lastClickedPoint.x()-radius,self.lastClickedPoint.y()-radius,self.lastClickedPoint.x()+radius,self.lastClickedPoint.y()+radius)
        #request = QgsFeatureRequest().setFilterRect(searchRect)
        #print request
        #it = lay.getFeatures(request)
        #ids = [i.id() for i in it] #select only the features for which the expression is true
        #print ids
        #lay.selectByIds(ids)
        lay.removeSelection()
        lay.selectByRect(searchRect,0)
        
        FT = flowTrace(lay,self.direction)
        ids = FT.select(None,None)
        
        if ids is None:
          QApplication.restoreOverrideCursor()
          return
        
        # select based on id
        #request = QgsFeatureRequest().setFilterFids(id_list)
        lay.selectByIds(ids)
        self.canvas.refresh()
        
        QApplication.restoreOverrideCursor()
        later = time.time()
        difference = int(later - now)
        print('execution time %s' % (difference))

    def canvasMoveEvent(self, event):
        """
        Whenever the mouse is moved update the rubberband and the snapping.
        :param event: QMouseEvent with coordinates
        """
        pass
       
    def rightClicked(self, _):
        """
        Resets the rubberband on right clickl
        :param _: QMouseEvent
        """
        pass

    def leftClicked(self, event):
        """
        Snaps to the network graph
        :param event: QMouseEvent
        """
        # store last clicked point
        
        self.lastClickedPoint = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos().x(), event.pos().y())
        #print 'ClickedPoint:',self.lastClickedPoint
        self.getTree(self.lastClickedPoint)
        
    def setActive(self):
        """
        Activates this map tool
        """
        self.saveTool = self.canvas.mapTool()
        self.canvas.setMapTool(self)

    def deactivate(self):
        """
        Deactivates this map tool. Removes the rubberband etc.
        """
        #super(NetworkSelectTool, self).deactivate()
        #MobidicUIMapTool.deactivate(self)
        try:
          SmartGreenMapTool.deactivate(self)
        except Exception as e:
            print(str(e))


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
            #print 'feat id:',feature.id()
        
        d = 1
        #loop through selection list
        while selection_list:
            d+=1
            #if d > 10000: # for debug
            #    break
            
            #get selected features
            request = QgsFeatureRequest().setFilterFid(selection_list[0])
            feature = QgsFeature()
            self.lay.getFeatures(request).nextFeature(feature)
            
            # get list of nodes
            try:
                nodes = feature.geometry().asPolyline()
            except:
            #~ print 'nodes:',nodes
            #if len(nodes) ==  0:
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
                #~ print 'nodes:',nodes
                #if len(nodes) ==  0:
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
                    #print 'feat id:',feature.id()
                    #print 'objid:',feature['FILE_ID']
                    #add feature to final list
                    #final_list.append(feature.id()) # moved down to prevent infinite loop
                    
                    #add feature to selection list to keep selecting upstream line segments
                    #selection_list.append(feature.id())
                                        
                    if feature.id() not in final_list: #selection_list: # changed to prevent infinite loop!
                        #add feature to selection list
                        selection_list.append(feature.id())
                        
                    final_list.append(feature.id())
                        
            #remove feature from selection list
            selection_list.pop(0)
            
        # return final list
        return final_list

class flowTraceSI:


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
        if self.lay.wkbType()!=QgsWkbTypes.LineString and self.lay.wkbType()!=QgsWkbTypes.MultiLineString and\
            self.lay.wkbType()!=QgsWkbTypes.LineString25D and self.lay.wkbType()!=QgsWkbTypes.MultiLineString25D:
          return None

        #get provider
        provider = self.lay.dataProvider()
        
        # Get all the features to start
        allfeatures = {feature.id(): feature for (feature) in self.lay.getFeatures()}

        
        # Build the spatial index for faster lookup.
        print('before spatialinex')
        index = QgsSpatialIndex()
        for f in allfeatures.values():            
            #populate spatialindex
            index.insertFeature(f)

        print('after spatialinex')
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
            #if len(nodes) ==  0:
            except:
                nodes = feature.geometry().asMultiPolyline()
                nodes = nodes[0]
                #~ print 'nodes:',nodes
            
            # get upstream node
            upstream_coord = nodes[self.up]
                        
            # select all features around upstream coordinate using a bounding box
            searchRect = QgsRectangle(upstream_coord.x() - self.rec, upstream_coord.y() - self.rec, upstream_coord.x() + self.rec, upstream_coord.y() + self.rec)
            #request = QgsFeatureRequest().setFilterRect(searchRect)
            ids = index.intersects(searchRect)
            request = QgsFeatureRequest().setFilterFids(ids)
            features = self.lay.getFeatures(request)
                        
            #iterate through requested features
            for feature in features:
                #get list of nodes
                #print feature.id()
                try:
                    nodes = feature.geometry().asPolyline()
                #~ print 'nodes:',nodes
                #if len(nodes) ==  0:
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
            #print '# after pop',len(selection_list)
            
        # return final list
        return final_list
