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
from my_progress import MyProgress

class Interpolate():
	
	def __init__(self,progress= None):
		if progress is None:
			self.progress = MyProgress()
		else:
			self.progress = progress
		
	def _cellEuclideanDistance(self,c,r):
		edist = ((self.grid.dx*(self.grid.cols-c))**2+(self.grid.dy*(self.grid.rows-r))**2)**0.5
		return edist
		
	def _euclideanDistance(self,x,y):
		dxs = 0.5*self.grid.dx+self.grid.dx*self.grid.cols-(x-self.grid.xcell)
		#dys = float(self.grid.nrows)*self.grid.dy-0.5*self.grid.dy-self.grid.dy*self.grid.rows-(y-self.grid.ycell)
		dys = float(self.grid.nrows)*self.grid.dy-0.5*self.grid.dy-self.grid.dy*self.grid.rows-(y-self.grid.ycell)
		edist = (dxs**2+dys**2)**0.5
		return edist
		
	def nearestNeighbour(self,templateGrid,xlist,ylist,vlist=None):
		self.grid = templateGrid
		# set up grids for results
		minDist = self.grid.copy(-1)
		minIdx = self.grid.copy(-1)
		assVal = self.grid.copy(-1)
		maxSlope = self.grid.copy(0)
		flowDir = self.grid.copy(0)
		
		if vlist is None:
			vlist = range(0,len(xlist))
		
		# for each point in the list
		if self.progress:
			self.progress.setInfo('Interpolate ...')
			self.progress.setPercentage(0) 
			
		maxNum = len(xlist)
		for i in range(0,maxNum):
			xpos = xlist[i]
			ypos = ylist[i]
			val = vlist[i]
			# transform coordinates to cell index
			#~ xc, yc = self.grid.coordToCell(xpos,ypos)
			#print i,xpos,ypos,xc,yc
			# calculate euclidean distance
			#~ dist = self._cellEuclideanDistance(xc,yc)
			dist = self._euclideanDistance(xpos,ypos)
			# populate a new 2d-array with the value assigned to the point
			# populate a new 2d-array with the value to correct with
			if i == 0:
				minIdx.data = np.where(minDist.data == -1,i,minIdx.data)
				assVal.data = np.where(minDist.data == -1,val,assVal.data)
				minDist.data = np.where(minDist.data == -1,dist,minDist.data)
			else:
				minIdx.data = np.where(minDist.data > dist,i,minIdx.data)
				assVal.data = np.where(minDist.data > dist,val,assVal.data)
				minDist.data = np.where(minDist.data > dist,dist,minDist.data)
				
			if self.progress: self.progress.setPercentage(100.0*float(i)/maxNum)
			
		return minDist, minIdx, assVal


if __name__ == '__console__':
	from gis_grid import GisGrid
	from my_progress import MyProgress
	grd = GisGrid(ncols = 101, nrows = 125, xcell = 1496787.1437, ycell = 5038078.83499, dx = 5, dy=5)
	xs = [1497037.65979621163569391,1497039.8349771904759109,1497039.56194623489864171]
	ys = [5038415.50863726530224085,5038448.98926123604178429,5038442.81514563504606485]
	vals = [150.83,151.021801496235,150.96]
	prog = MyProgress()
	itp = Interpolate(prog)
	minDist, minIdx, assVal = itp.nearestNeighbour(grd,xs,ys,vals)
	minDist.saveAsASC('d:/test/minDist2.asc', progress = prog)
	minIdx.saveAsASC('d:/test/minIdx2.asc', progress = prog)
	assVal.saveAsASC('d:/test/assVal2.asc', progress = prog)
	