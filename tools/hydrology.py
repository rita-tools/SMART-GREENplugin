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
import copy

#import logging

class Hydrology():
	
	def __init__(self, progress= None):
		self.progress = progress
		# default
		#~ self.rstep = np.array([-1,-1,-1,0,1,1,1,0])
		#~ self.cstep = np.array([1,0,-1,-1,-1,0,1,1])
		#~ self.defaultUseCode = [1,2,3,4,5,6,7,8]

		self.rstep = np.array([-1,-1,-1,0,+1,+1,+1,0])
		self.cstep = np.array([-1,0,+1,+1,+1,0,-1,-1])
		#self.defaultUseCode = [5,6,7,8,1,2,3,4]
		self.defaultUseCode = [1,2,3,4,5,6,7,8]
				
		#logging.basicConfig(filename='d:/test_smartgreen/testlog3.log',level=logging.DEBUG)
		
	def calcGradMap(self,startGrid,distGrid,gradient = 0.01):
		return startGrid+distGrid*gradient
		
	def stack8point(self,flowDir):
		#				7 6 5
		# pointers  8	4
		#		  		1 2 3
		self.rstep = np.array([-1,-1,-1,0,+1,+1,+1,0])
		self.cstep = np.array([-1,0,+1,+1,+1,0,-1,-1])
		self.defaultUseCode = [1,2,3,4,5,6,7,8]
		# st8 = matrice che riporta, per ciascuna cella, l'indice assoluto delle celle contribuenti (secondo le 8 direzioni)
		zp = flowDir.data
		zp = np.flip(zp,0) #flip array
		r,c = zp.shape
		#logging.debug('shape: (%s,%s)'%(n,m))
		#~ st8 = np.zeros((8,r,c))
		# reshape
		# change array shape to fit matlab 3d structure
		#st8 = np.swapaxes(st8.T, 0, 1)
		st8 = np.zeros((8,c,r))
		st8 = st8.T
		
		for h in range(0,8):
			st = np.zeros((r,c))
			#print 'count of %s: %s'%(self.defaultUseCode[h],len(zp[zp==self.defaultUseCode[h]]))
			itemIndex= np.where(zp==self.defaultUseCode[h])
			#~ print 'itemIndex0:',itemIndex
			
			i0 = copy.deepcopy(itemIndex[0])
			j0 = copy.deepcopy(itemIndex[1])

			#~ print 'BEFORE SUB2IND'
			#~ print 'i0:',i0
			#~ print 'j0:',j0
			
			k = flowDir.sub2ind((r,c),r-i0, j0, True, True)
			
			#~ print 'k:',k
			
			#~ print 'itemIndex1:',itemIndex
			
			i1 = copy.deepcopy(itemIndex[0])
			j1 = copy.deepcopy(itemIndex[1])
			
			#~ print 'AFTER SUB2IND'
			#~ print 'i1:',i1
			#~ print 'j1:',j1
			
			#print k #OK
			#i=i-self.rstep[h]
			i=i1+self.rstep[h]
			j=j1+self.cstep[h]
			#~ print 'i_to',str(i)
			#~ print 'j_to',str(j)
			# limit i,j to the maximum number of rows and cols
			j  = j[np.where(np.logical_and(i>=0,i<r))]
			k  = k[np.where(np.logical_and(i>=0,i<r))]
			i  = i[np.where(np.logical_and(i>=0,i<r))]
			i  = i[np.where(np.logical_and(j>=0,j<c))]
			k  = k[np.where(np.logical_and(j>=0,j<c))]
			j  = j[np.where(np.logical_and(j>=0,j<c))]
			#~ print 'i_to_lim',str(i)
			#~ print 'j_to_lim',str(j)
			st[i,j]=k
			st8[:,:,h]=st
		
		st = st8[:,:,0].squeeze()
		itemIndex = np.nonzero(st > 0)
		i = itemIndex[0]
		j = itemIndex[1]
		k1 = flowDir.sub2ind((r,c),r-i,j,True, True)
		k1 = np.array([k1])
		k1 = k1.T
		
		st = st8[:,:,1].squeeze()
		itemIndex = np.nonzero(st > 0)
		i = itemIndex[0]
		j = itemIndex[1]
		k2 = flowDir.sub2ind((r,c),r-i,j,True, True)
		k2 = np.array([k2])
		k2 = k2.T
		
		st = st8[:,:,2].squeeze()
		itemIndex = np.nonzero(st > 0)
		i = itemIndex[0]
		j = itemIndex[1]
		k3 = flowDir.sub2ind((r,c),r-i,j,True, True)
		k3 = np.array([k3])
		k3 = k3.T
		
		st = st8[:,:,3].squeeze()
		itemIndex = np.nonzero(st > 0)
		i = itemIndex[0]
		j = itemIndex[1]
		k4 = flowDir.sub2ind((r,c),r-i,j,True, True)
		k4 = np.array([k4])
		k4 = k4.T
		
		st = st8[:,:,4].squeeze()
		itemIndex = np.nonzero(st > 0)
		i = itemIndex[0]
		j = itemIndex[1]
		k5 = flowDir.sub2ind((r,c),r-i,j,True, True)
		k5 = np.array([k5])
		k5 = k5.T
		
		st = st8[:,:,5].squeeze()
		itemIndex = np.nonzero(st > 0)
		i = itemIndex[0]
		j = itemIndex[1]
		k6 = flowDir.sub2ind((r,c),r-i,j,True, True)
		k6 = np.array([k6])
		k6 = k6.T
		
		st = st8[:,:,6].squeeze()
		itemIndex = np.nonzero(st > 0)
		i = itemIndex[0]
		j = itemIndex[1]
		k7 = flowDir.sub2ind((r,c),r-i,j,True, True)
		k7 = np.array([k7])
		k7 = k7.T
		
		st = st8[:,:,7].squeeze()
		itemIndex = np.nonzero(st > 0)
		i = itemIndex[0]
		j = itemIndex[1]
		k8 = flowDir.sub2ind((r,c),r-i,j,True, True)
		k8 = np.array([k8])
		k8 = k8.T
		
		return k1,k2,k3,k4,k5,k6,k7,k8,st8
		
	def setCode(self,fdCode):
		if fdCode == 'esri':
			#~ self.rstep = np.array([-1,-1,-1,0,1,1,1,0])
			#~ self.cstep = np.array([1,0,-1,-1,-1,0,1,1])
			#~ self.defaultUseCode = [128,62,32,16,8,4,2,1]
			self.rstep = np.array([-1,-1,-1,0,1,1,1,0])
			self.cstep = np.array([-1,0,+1,+1,+1,0,-1,-1])
			self.defaultUseCode = [1,2,3,4,5,6,7,8]
		elif fdCode == 'mobidic':
			self.rstep = np.array([-1,-1,-1,0,+1,+1,+1,0])
			self.cstep = np.array([-1,0,+1,+1,+1,0,-1,-1])
			self.defaultUseCode = [1,2,3,4,5,6,7,8]
			#self.defaultUseCode = [5,6,7,8,1,2,3,4]
		else:
			self.rstep = np.array([-1,-1,-1,0,1,1,1,0])
			#self.cstep = np.array([1,0,-1,-1,-1,0,1,1])
			self.cstep = np.array([-1,0,+1,+1,+1,0,-1,-1])
			self.defaultUseCode = [1,2,3,4,5,6,7,8]
			
		
	def flowDirectionAndSlope(self, demGrid, fdCode = 'grass'):
		# make a new grid to store data and set values to zero
		maxSlope = demGrid.copy(0)
		flowDir = demGrid.copy(0)
		
		if self.progress:
			self.progress.setInfo('Flow Directions ...')
			self.progress.setPercentage(0) 
		# enlarge the grid boundaries of the dem
		largeDem = np.zeros((demGrid.nrows+2,demGrid.ncols+2), dtype=np.float)+demGrid.nodata
		#print 'largeDem:', largeDem.shape
		#print 'Dem:', demGrid.shape
		largeDem[1:demGrid.nrows+1,1:demGrid.ncols+1] = demGrid.data
		# mask nodata
		#largeDem = np.ma.masked_where((largeDem == demGrid.nodata), largeDem)
		largeDem[largeDem == demGrid.nodata] = 10000 # too big to exist in nature ...
		#print largeDem
		
		
		delta = ((self.cstep.astype(np.float32)*demGrid.dx)**2+(self.rstep.astype(np.float32)*demGrid.dy)**2)**0.5

		if fdCode == 'esri':
					self.defaultUseCode = [128,62,32,16,8,4,2,1]
			
		if fdCode == 'mobidic':
			self.rstep = np.array([-1,-1,-1,0,+1,+1,+1,0])
			self.cstep = np.array([-1,0,+1,+1,+1,0,-1,-1])
			self.defaultUseCode = [1,2,3,4,5,6,7,8]
			
		if fdCode == 'grass':
			self.rstep = np.array([-1,-1,-1,0,1,1,1,0])
			self.cstep = np.array([1,0,-1,-1,-1,0,1,1])
			self.defaultUseCode = [1,2,3,4,5,6,7,8]
		
		useCode = self.defaultUseCode
		# loop in the 8 directions and calcolate slopes
		# get the maximum slope and assign the direction
		for i in range(0,len(useCode)):
			# positive slope value means downstream
			#print 'slice of largeDem:', largeDem[1+rstep[i]:1+self.nrows+rstep[i],1+cstep[i]:1+self.ncols+cstep[i]].shape
			#slope = (demGrid.data-largeDem[1+self.rstep[i]:1+demGrid.nrows+self.rstep[i],1+self.cstep[i]:1+demGrid.ncols+self.cstep[i]])/delta[i]
			slope = (largeDem[1:1+demGrid.nrows,1:1+demGrid.ncols]-largeDem[1+self.rstep[i]:1+demGrid.nrows+self.rstep[i],1+self.cstep[i]:1+demGrid.ncols+self.cstep[i]])/delta[i]
			flowDir.data = np.where(maxSlope.data < slope,useCode[i],flowDir.data)
			maxSlope.data = np.where(maxSlope.data < slope,slope,maxSlope.data)
			if self.progress: self.progress.setPercentage(100*float(i)/len(useCode)) 
			# check cells
			#~ print 'cell elev:',largeDem[422+1,308+1]
			#~ print 'to cell elev:',largeDem[422+1+self.rstep[i],308+1+self.cstep[i]]
			#~ print 'delta dist:',delta[i]
			#~ print 'slope:',slope[422,308]
			#~ print 'maxSlope:',maxSlope.data[422,308]
			#~ print 'flowdir:',flowDir.data[422,308]
		
		return flowDir,maxSlope
		
		
	def contributingArea(self,dirGrid,asSurface = True):
		# init variable
		self.ang = dirGrid
		self.sca = dirGrid.copy(0.0)
		
		if self.progress: self.progress.setPercentage(0)
		
		# Call drainage area subroutine for each cell			  
		# working from the middle out to avoid deep recursions  

		# lower block
		# TODO: check if division creates empty values
		for j in range(int(self.ang.nrows/2),self.ang.nrows-1):
			if self.progress: self.progress.setPercentage(100*float(j-self.ang.nrows/2)/self.ang.nrows) 
			for i in range(int(self.ang.ncols/2),self.ang.ncols-1): self.d8Area(j, i)
			for i in range(int(self.ang.ncols/2),0,-1): self.d8Area(j, i)
		# upper block
		for j in range(int(self.ang.nrows/2),0,-1):
			if self.progress: self.progress.setPercentage(100*float(self.ang.nrows-j)/self.ang.nrows) 
			for i in range(int(self.ang.ncols/2),self.ang.ncols-1): self.d8Area(j, i)
			for i in range(int(self.ang.ncols/2),0,-1): self.d8Area(j, i)
		
		if self.progress: self.progress.setPercentage(100) 
		self.sca.data = np.where(self.sca.data == 0.0,self.sca.nodata,self.sca.data)
		if asSurface:
			self.sca = self.sca*self.sca.dx*self.sca.dy
		
		if self.progress: self.progress.setPercentage(0)
		return self.sca
	
	def d8Area(self,j, i,con= 0,ccheck = False):
		# con is a flag that signifies possible contaminatin of sca
		# due to edge effects
		if self.sca.data[j, i] == 0.0: #self.sca.nodata:	# i.e., if the cell hasn't been looked at yet
			if (i != 0) and (i != self.sca.ncols - 1) and (j != 0) and (j != self.sca.nrows - 1) and (self.ang.data[j, i] != self.ang.nodata):
				# i.e. the cell isn't outside domain
				# Specific catchment area of single grid cell is dx
				# This is area per unit contour width.
				self.sca.data[j, i] = 1.0
				for k in range(0,8):
					inw = i + self.cstep[k]
					jnw = j + self.rstep[k]
					# for each neighboring cell, verify that it put water in it
					# draining back to the cell in question
					kback = k + 4 +1 # +1 because k is zero based
					if (kback > 8): kback = kback - 8

					if (kback == self.ang.data[jnw, inw]): #adiacent cell drain in it
						self.d8Area(jnw, inw)
						# HERE THE FLAG FOR EDGE DETECTION
						if (self.sca.data[jnw, inw] == self.sca.nodata): con = -1
						
						self.sca.data[j, i] = self.sca.data[j, i] + self.sca.data[jnw, inw]
					
					if (self.ang.data[jnw, inw] == self.ang.nodata): con = -1
		
				# added by EAC08: check for edge contamination
				if (con == -1 and ccheck == True):
					self.sca.data[j, i] = self.sca.nodata

		
if __name__ == '__console__':
	import gis_grid
	#reload(gis_grid)
	
	#~ from gis_grid import GisGrid
	#~ from my_progress import MyProgress
	#~ from interpolate import Interpolate
	#~ grd = GisGrid(ncols = 100, nrows = 100, xcell = 12.4, ycell = 23.7, dx = 0.05, dy=0.05)
	#~ xs = [14.1,15.3,16.4]
	#~ ys = [24.0,25.7,28.1]
	#~ vals = [3,2.2,6.1]
	#~ prog = MyProgress()
	#~ itp = Interpolate(prog)
	#~ minDist, minIdx, assVal = itp.nearestNeighbour(grd,xs,ys,vals)
	#~ # create a virtual dem
	#~ dem = assVal+minDist*0.01
	#~ hyd = Hydrology(prog)
	#~ flowDir,maxSlope = hyd.flowDirectionAndSlope(dem, fdCode = 'grass')
	#~ dem.saveAsASC('d:/test/dem.asc', progress = prog)
	#~ flowDir.saveAsASC('d:/test/flowDir.asc', progress = prog)
	#~ maxSlope.saveAsASC('d:/test/maxSlope.asc', progress = prog)
	#~ sca = hyd.contributingArea(flowDir)
	#~ sca.saveAsASC('d:/test/sca.asc', progress = prog)
	
	import numpy as np
	from gis_grid import GisGrid
	from my_progress import MyProgress
	from data_to_mat import dataToMat
	
	dirData = np.array([[3,2,1,1,1],[4,3,2,1,2],[5,3,3,2,1],[3,5,5,2,1,],[4,3,4,2,1],[4,4,4,2,1]])
	flowDir = GisGrid(ncols = 5, nrows = 6, xcell = 0, ycell = 0, dx = 1, dy=1)
	flowDir.data = dirData
	prog = MyProgress()
	hyd = Hydrology(prog)
	hyd.setCode('mobidic')
	k1,k2,k3,k4,k5,k6,k7,k8,st8 = hyd.stack8point(flowDir)
	
	dataToMat(filename = 'd:/test/st8.mat',data = dirData,name= 'zp',progress = prog)
	dataToMat(filename = 'd:/test/st8.mat',data = k1,name= 'sk1',progress = prog)
	dataToMat(filename = 'd:/test/st8.mat',data = k2,name= 'sk2',progress = prog)
	dataToMat(filename = 'd:/test/st8.mat',data = k3,name= 'sk3',progress = prog)
	dataToMat(filename = 'd:/test/st8.mat',data = k4,name= 'sk4',progress = prog)
	dataToMat(filename = 'd:/test/st8.mat',data = k5,name= 'sk5',progress = prog)
	dataToMat(filename = 'd:/test/st8.mat',data = k6,name= 'sk6',progress = prog)
	dataToMat(filename = 'd:/test/st8.mat',data = k7,name= 'sk7',progress = prog)
	dataToMat(filename = 'd:/test/st8.mat',data = k8,name= 'sk8',progress = prog)
	dataToMat(filename = 'd:/test/st8.mat',data = st8,name= 'st8',progress = prog)
	