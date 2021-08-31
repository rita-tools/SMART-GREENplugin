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

# add localization

from collections import OrderedDict
import sys
import os.path as osp

from PyQt5.QtCore import QVariant
from qgis.core import *
from qgis.gui import *


class SmartGreenSettings():
	def __init__(self, tr = None):
		"""
		Settings data structure:
		settings is a dictionary where
		the key is the name of the variable
		while the value is a list of 4 objects:
		[value,name,description, isrequired,limits]
		"""
		if tr is None:
			self.tr = lambda x: x
		else:
			self.tr = tr
		
		self.settings = OrderedDict()
		self.setDefault()
		#self.readFile(osp.join(osp.dirname(sys.modules[__name__].__file__),'usersettings.dat'))
		# load project settings
		#self.readFromProject()
		
	
	def readFile(self, fname):
		# check if file exists
		try:
			with open(fname) as f:
				lines = f.readlines()
				
			# you may also want to remove whitespace characters like `\n` at the end of each line
			lines = [x.strip() for x in lines] 
			# loop in lines
			for i in range(0,len(lines)):
				# check if the line start with #
				if lines[i] !='' and lines[i][0] != '#':
					# split the line in key-value
					toks = lines[i].split(' ',1)
					key = toks[0]
					value = toks[1].strip() if len(toks) == 2 else None
					self.updateValue(key,value)
		except:
			# do nothing
			return
			
	def saveFile(self, fname):
		try:
			f = open(fname,'w')
			newline = '##### SMART-GREEN CONFIGURATION FILE ##### ' + '\n'
			f.write(newline)
			newline = '##### create by SMART-GREEN plugin ##### ' + '\n\n'
			f.write(newline)
			for key in self.settings:
				# make a new line
				newline = '# ' + self.tr(self.settings[key][1]) + '\n'
				f.write(newline)
				newline = '# ' + self.tr(self.settings[key][2]) + '\n'
				f.write(newline)
				newline = key + ' ' + str(self.settings[key][0]) + '\n\n'
				f.write(newline)
		except IOError:
			print(self.tr('Cannot save file: %s' %fname))
		finally:
			f.close()
			
	def saveToProject(self):
		proj = QgsProject.instance()
		# store values
		for key in self.settings:
			proj.writeEntry("SMARTGREEN", key, str(self.settings[key][0]))

	def printSettings(self):
		for key in self.settings:
			print(key, ':', str(self.settings[key][0]))

	def readFromProject(self, proj):
		#print 'in settings, proj:',proj
		for key in self.settings:
			value = proj.readEntry("SMARTGREEN", key, str(self.settings[key][0]))[0]
			if value is not None:
				self.updateValue(key,value)

	def updateValue(self,key,value):
		other = None
		if isinstance(value, tuple):
			# split variable
			other = value[1]
			value = value[0]
		
		# by default, value is a string
		#~ castType = self.settings[key][3]
		#~ if castType == QVariant.Double:
			#~ value = float(value)
		#~ if castType == QVariant.Int:
			#~ value = int(value)
			
		try:
			value = float(value)
		except:
			value = str(value)
		
		# update value
		if key in self.settings:
			self.settings[key][0]=value
			if other is not None:
				self.settings[key][5]=other
		else:
			print(self.tr('Unmanaged key <%s> with value <%s>' % (key, value)))

	def valueExist(self,value):
		res = False
		# uniform slash
		value = str(value).replace('\\','/')
		for key in self.settings:
			#print 'in valueExist:',self.settings[key][0]
			compare = str(self.settings[key][0]).replace('\\','/')
			if value == compare:
				res = True
				break
				
		return res
			
	def getLayerBySource2(self,source):
		print('In getLayerBySource:', source)
		layer=None
		for lyr in QgsProject.instance().mapLayers().values():
			if lyr.source() == source:
				layer = lyr
				break
				
		if layer is None:
			# create a new layer from source
			layer = QgsVectorLayer(source,osp.basename(source), "ogr")
			
		return layer
		
	def getLayerBySource(self,source):
		layer=None
		source = source.replace('\\','/')
		#print 'source:',source
		for lyr in QgsProject.instance().mapLayers().values():
			#print '-->',lyr.source()
			if lyr.source().replace('\\','/') == source:
				layer = lyr
				break
				
		#~ if layer is None:
			#~ # create a new layer from source
			#~ layer = QgsVectorLayer(source,basename(source), "ogr")
			
		return layer
				
		
	def setDefault(self):
		self.settings = OrderedDict()
		self.settings['qgis.dblite'] = ['','Tables database', 'The database where to store tables',QVariant.String, True, '-']
		#~ self.settings['qgis.cellsize'] = [5.0,'Cell size', 'Dimention of a squared cell',QVariant.Double, True, '-']
		
		#~ self.settings['qgis.networklayer']=['','Network layer', 'The vector layer containing the drainage network','TEXT', True, '-']
		#~ self.settings['qgis.networklayer.field.obj_id']=['OBJ_ID',  'Line id', 'Field name of conduits numerical id. in urban drainage network attribute table', 'TEXT', True, None]
		#~ self.settings['qgis.networklayer.field.obj_start']=['NODE_START', 'Start node', 'Field name of conduits starting node id in network attribute table', 'TEXT', True, None]
		#~ self.settings['qgis.networklayer.field.obj_end']=['NODE_END', 'End node', 'Field name of conduits final node id in network attribute table', 'TEXT', True, None]
		#~ self.settings['qgis.networklayer.field.s_shape']=['S_SHAPE', 'Conduit shape', 'Field name of conduits cross sectional shape in network attribute table', 'TEXT', True, None]
		#~ self.settings['qgis.networklayer.field.diam']=['DIAM', 'Diameter', 'Field name of conduits cross section diameter (for circular conduit only)', 'FLOAT', True, 'm']
		#~ self.settings['qgis.networklayer.field.dim1']=['DIM1', 'First dimension', 'Field name of conduits cross section characteristic length D1 (heigth in all the case)', 'FLOAT', True, 'm']
		#~ self.settings['qgis.networklayer.field.dim2']=['DIM2', 'Second dimension', 'Field name of conduits cross section characteristic length D2 (width in case of rectangula or ellipital section)', 'FLOAT', True, 'm']
		#~ self.settings['qgis.networklayer.field.dim3']=['DIM3', 'Third dimension', 'Field name of conduits cross section characteristic length D3 (slope in case of trapezoidal channel)', 'FLOAT', False, None]
		#~ self.settings['qgis.networklayer.field.dim4']=['DIM4', 'Fourth dimension', 'Field name of conduits cross section characteristic length D4 (slope in case of trapezoidal channel)', 'FLOAT', False, None]
		#~ self.settings['qgis.networklayer.field.table']=['TABLE', 'Section table', 'Field name of the name of the table with natural section points ', 'TEXT', False, None]
		#~ self.settings['qgis.networklayer.field.elev_start']=['ELEV_START', 'Elevation start', 'Field name of conduits invert elevation at starting point in network attribute table', 'FLOAT', True, 'm']
		#~ self.settings['qgis.networklayer.field.elev_end']=['ELEV_END', 'Elevation end', 'Field name of conduits invert elevation at final point in network attribute table', 'FLOAT', True, 'm']
		#~ self.settings['qgis.networklayer.field.mann']=['MANN', 'Manning n', 'Field name of Manning n in network attribute table', 'FLOAT', False,None]
		#~ self.settings['qgis.networklayer.field.length']=['LENGTH', 'Conduit length', 'Field name of conduits length', 'FLOAT', False, 'm']
		#~ self.settings['qgis.networklayer.field.msg']=['MSG', 'Message', 'Field name for messages to the user', 'TEXT', False, None]
		
		#~ self.settings['qgis.nodeslayer']=['','Nodes layer', 'The vector layer containing the drainage network nodes','TEXT', True, None]
		#~ self.settings['qgis.nodeslayer.field.obj_id']=['OBJ_ID', 'Point id field', 'Field name of nodes numerical id. in the attribute table', 'TEXT', True, None]
		#~ self.settings['qgis.nodeslayer.field.elev_bot']=['ELEV_BOT', 'Elevation at bottom field', 'Field name of node invert elevation in the attribute table (m a.s.l.)', 'FLOAT', True, 'm']
		#~ self.settings['qgis.nodeslayer.field.elev_top']=['ELEV_TOP', 'Elevation at top field', 'Field name of node top elevation in the attribute table (m a.s.l.)', 'FLOAT', True, 'm']
		#~ self.settings['qgis.nodeslayer.field.depth']=['DEPTH', 'Depth field', 'Field name of node depth in the attribute table (m)', 'FLOAT', True, 'm']
		#~ self.settings['qgis.nodeslayer.field.area']=['AREA', 'Area field', 'Field name of node planar area in the attribute table (m^2)', 'FLOAT', True, 'm2']
		#~ self.settings['qgis.nodeslayer.field.table']=['TABLE', 'Area-depth table', 'Contain the name of the area-depth relation', 'TEXT', True, None]
		#~ self.settings['qgis.nodeslayer.field.msg']=['MSG', 'Message', 'Field name message to the user', 'TEXT', True, None]
		
		#~ self.settings['qgis.subcatchmentslayer']=['','Subcatchments layer', 'The vector layer containing the drainage area','TEXT', True, '-']
		#~ self.settings['qgis.subcatchmentslayer.field.obj_id']=['OBJ_ID', 'Catchment id', 'Field name of catchment id in the attribute table', 'TEXT', True, None]
		#~ self.settings['qgis.subcatchmentslayer.field.node_id']=['NODE_ID', 'Node id', 'Field name of node id connected to the catchment', 'TEXT', True, None]
		#~ self.settings['qgis.subcatchmentslayer.field.msg']=['MSG', 'Message', 'Field name message to the user', 'TEXT', True, None]
		
		#~ self.settings['qgis.weatherstationslayer']=['','Weather Stations layer', 'The vector layer containing the weather stations positions','TEXT', True, None]
		#~ self.settings['qgis.weatherstationslayer.field.obj_id']=['OBJ_ID', 'Weather station id', 'The name of the field that contains the weather stations id in the attribute table.', 'TEXT', True, None]
		#~ self.settings['qgis.weatherstationslayer.field.name']=['NAME', 'Name', 'The name of the field that contains the weather stations name in the attribute table.', 'TEXT', True, None]
		#~ self.settings['qgis.weatherstationslayer.field.a1']=['A1', 'a1', 'The name of the field that that contains the DDF a1 parameter (h=a1*w*d^n, w=eps+alp/kap*(1-(ln(Tr/(1-Tr)))^kap))', 'FLOAT', True, None]
		#~ self.settings['qgis.weatherstationslayer.field.n']=['N', 'n', 'The name of the field that that contains the DDF n parameter (h=a1*w*d^n, w=eps+alp/kap*(1-(ln(Tr/(1-Tr)))^kap))', 'FLOAT', True, None]
		#~ self.settings['qgis.weatherstationslayer.field.alp']=['ALP', 'alp', 'The name of the field that that contains the DDF alp parameter (h=a1*w*d^n, w=eps+alp/kap*(1-(ln(Tr/(1-Tr)))^kap))', 'FLOAT', True, None]
		#~ self.settings['qgis.weatherstationslayer.field.eps']=['EPS', 'eps', 'The name of the field that that contains the DDF eps parameter (h=a1*w*d^n, w=eps+alp/kap*(1-(ln(Tr/(1-Tr)))^kap))', 'FLOAT', True, None]
		#~ self.settings['qgis.weatherstationslayer.field.kap']=['KAP', 'kap', 'The name of the field that that contains the DDF kap parameter (h=a1*w*d^n, w=eps+alp/kap*(1-(ln(Tr/(1-Tr)))^kap))', 'FLOAT', True, None]
		#~ self.settings['qgis.weatherstationslayer.field.table']=['TABLE', 'Data file', 'The name of the field that that will contains weather data (datetime, rain, temperature, ...)', 'TEXT', True, None]
		#~ self.settings['qgis.weatherstationslayer.field.msg']=['MSG', 'Message', 'Field name message to the user', 'TEXT', True, None]
		
		#~ self.settings['qgis.soilslayer']=['','Soil layer', 'The vector layer containing the soils type','TEXT', True, None]
		#~ self.settings['qgis.soilslayer.field.obj_id']=['OBJ_ID', 'Soil id', 'Field name of soil id in the attribute table.', 'TEXT', True, None]
		#~ self.settings['qgis.soilslayer.field.ks']=['KS', 'Ks', 'Soil hydraulic conductivity (mm/h)', 'FLOAT', True, None]
		#~ self.settings['qgis.soilslayer.field.wg0']=['WG0', 'Wg0', 'Large pore water holding capacity (mm)', 'FLOAT', True, None]
		#~ self.settings['qgis.soilslayer.field.wc0']=['WC0', 'Wc0', 'Small pore water holding capacity (mm)', 'FLOAT', True, None]
		#~ self.settings['qgis.soilslayer.field.msg']=['MSG', 'Message', 'Field name message to the user', 'TEXT', True, None]
				
		#~ self.settings['qgis.landuseslayer']=['','Landuse layer', 'The vector layer containing the land use','TEXT', True, None]
		#~ self.settings['qgis.landuseslayer.field.obj_id']=['OBJ_ID', 'land use id', 'Field name of land use id in the attribute table', 'TEXT', True, None]
		#~ self.settings['qgis.landuseslayer.field.wp0']=['WP0', 'Wp0', 'Interception (mm)', 'FLOAT', True, None]
		#~ self.settings['qgis.landuseslayer.field.ch']=['CH', 'Ch', 'Turbulent exchange coefficient (-)', 'FLOAT', True, None]
		#~ self.settings['qgis.landuseslayer.field.alb']=['ALB', 'Alb', 'Albedo (-)', 'FLOAT', True, None]
		#~ self.settings['qgis.landuseslayer.field.msg']=['MSG', 'Message', 'Field name message to the user', 'TEXT', True, None]
		
		#~ self.settings['qgis.acquiferlayer']=['','Landuse layer', 'The vector layer containing the land use','TEXT', True, None]
		#~ self.settings['qgis.acquiferlayer.field.obj_id']=['OBJ_ID', 'Acquifer id', 'Field name of acquifer id in the attribute table', 'TEXT', True, None]
		#~ self.settings['qgis.acquiferlayer.field.kf']=['KF', 'Acquifer conductivity (mm/s)', 'Field name of the acquifer conductivity (mm/s) in the attribute table', 'FLOAT', True, None]
		#~ self.settings['qgis.acquiferlayer.field.ma']=['MA', 'Artesian acquifer extension (0/1)', 'Field name of the artesian acquifer extension (0/1) in the attribute table', 'INTEGER', True, None]
		#~ self.settings['qgis.acquiferlayer.field.mf']=['MF', 'Freatic acquifer extension (0/1)', 'Field name of freatic acquifer extension (0/1) in the attribute table', 'INTEGER', True, None]
		#~ self.settings['qgis.acquiferlayer.field.msg']=['MSG', 'Message', 'Field name message to the user', 'TEXT', True, None]
		
		#~ self.settings['qgis.lidlayer']=['','LID', 'Low Impact Infrastructure map','TEXT', True, None]
		#~ self.settings['qgis.lidlayer.field.obj_id']=['OBJ_ID','Object identifier', 'An unique id for the LID','TEXT', True, None]
		#~ self.settings['qgis.lidlayer.field.name']=['NAME','Name', 'Explicative name of the LID','TEXT', True, None]
		#~ self.settings['qgis.lidlayer.field.area']=['AREA','Area', 'Area in squared meters','FLOAT', True, None]
		#~ self.settings['qgis.lidlayer.field.type']=['TYPE','Type', 'Type of LID','TEXT', True, None]
		#~ self.settings['qgis.lidlayer.field.node_to']=['NODE_TO','Draining node', 'The node id where the LID drains','TEXT', True, None]
		#~ self.settings['qgis.lidlayer.field.msg']=['MSG', 'Message', 'Field name message to the user', 'TEXT', True, None]
		
		#~ # tables
		#~ self.settings['qgis.table.soils']=['','Soils parameters', 'Path to table that contains soils parameters',QVariant.String, True, None]
		#~ self.settings['qgis.table.landuses']=['','Landuses parameters', 'Path to table that contains landuses parameters',QVariant.String, True, None]
		#~ self.settings['qgis.table.manning']=['','Manning n', "Path to table that contains Manning's coefficients",QVariant.String, True, None]
		
		#~ self.settings['qgis.table.section_shapes']=['','Section shapes', "Path to table that contains section shapes lookup table",QVariant.String, True, None]
		#~ self.settings['qgis.table.lidtypes']=['','LID types', "Path to table that contains LID types",QVariant.String, True, None]
		#~ self.settings['qgis.table.lidsoiltypes']=['','LID soil types', "Path to table that contains soil layers characteristics",QVariant.String, True, None]
		#~ self.settings['qgis.table.lidvegtypes']=['','LID vegetation types', "Path to table that contains vegetation characteristics",QVariant.String, True, None]
		#~ self.settings['qgis.table.lidsubtypes']=['','LID sublayer types', "Path to table that contains sublayer characteristics",QVariant.String, True, None]
		
		#~ # default table
		#~ self.settings['qgis.table.defaultconstants']=['','Physical constant', "Path to table that contains physical constant values",QVariant.String, True, None]
		#~ self.settings['qgis.table.defaulthydraulicparameters']=['','Hydraulic parameters', "Path to table that hydraulic parameter values",QVariant.String, True, None]
		#~ self.settings['qgis.table.defaulthydrologicalparameters']=['','Hydrological constant', "Path to table that contains hydrological parameter values",QVariant.String, True, None]
		#~ self.settings['qgis.table.defaultprojectmetadata']=['','Project metadata', "Path to table that contains project metadata",QVariant.String, True, None]
		#~ self.settings['qgis.table.defaultsimulationparameters']=['','Simulation settings', "Path to table that contains simulation settings",QVariant.String, True, None]
				
		#~ # general project settings
		#~ self.settings['project_name']=['Replace with something of meaningfull','Project name', 'Nickname of the project',QVariant.String, True, None]
		#~ self.settings['project_descr']=['Replace with something of meaningfull','Project description', 'Description of the project',QVariant.String, True, None]
		#~ self.settings['basin_id']=['basin_id', 'Basin id','Nickname of basin (Any string with no blank characters)', QVariant.String, True, None]
		#~ self.settings['paramset_id']=['simulation_parameters_id',  'Simulation id','Nickname of parameters set (Any string with no blank characters)', QVariant.String, True, None]
		#~ self.settings['basin_blon']=[11.0,  'Basin centroid longidute', 'Longitude of basin approx. baricenter (deg. East)', QVariant.Double, True, None]
		#~ self.settings['basin_blat']=[44.0,  'Basin centroid latitude', 'Latitude of basin approx. baricenter (deg. North)', QVariant.Double, True, None]
		#~ self.settings['gisdatapath']=['gisdata.mat', 'Consolidate dataset path', 'Consolidated dataset to be created by GIS preprocessing (pathname)', QVariant.String, True, None]
		#~ self.settings['statespath']=['states','Output path', 'Directory where the model states will be stored (directory path including terminal \\)', QVariant.String, True, None]
		
		#~ # default parameters multipliers
		#~ self.settings['param_value.d1_molti_urban']=[1.0, 'Multiplying factor for dimension 1', 'Multiplying factor of conduits cross section characteristic length D1, non dimensional', QVariant.Double, False, None]
		#~ self.settings['param_value.d2_molti_urban']=[1.0, 'Multiplying factor for dimension 2', 'Multiplying factor of conduits cross section characteristic length D2, non dimensional', QVariant.Double, False, None]
		#~ self.settings['param_value.L_molti_urban']=[1.0, 'Multiplying factor for length', 'Multiplying factor of conduits length, non dimensional', QVariant.Double, False, None]
		#~ self.settings['param_value.ks_molti']=[1.0, 'Multiplying factor of soil hydraulic conductivity (-)', 'Multiplying factor of soil hydraulic conductivity, non dimensional', QVariant.Double, False, None]
		#~ self.settings['param_value.wc_molti']=[1.0, 'Multiplying factor of maximum water holding capacity in soil small pores (-)', 'Multiplying factor of maximum water holding capacity in soil small pores, non dimensional', QVariant.Double, False, None]
		#~ self.settings['param_value.wg_molti']=[1.0, 'Multiplying factor of maximum water holding capacity in soil large pores (-)', 'Multiplying factor of maximum water holding capacity in soil large pores, non dimensional', QVariant.Double, False, None]
		#~ self.settings['param_value.area_molti_urban']=[1.0, 'Multiplying factor for area', 'Multiplying factor of nodes area, non dimensional', QVariant.Double, False, None]
				
		#~ # default hydrological parameters
		#~ self.settings['param_default.Wg0']=[500.0,  'Large pore water holding capacity (mm)', 'Default value of maximum water holding capacity in soil large pores in millimiters', QVariant.Double, True, 1]
		#~ self.settings['param_default.Wc0']=[300.0, 'Small pore water holding capacity (mm)', 'Default value of maximum water holding capacity in soil small pores, in millimiters', QVariant.Double, True, 1]
		#~ self.settings['param_default.Wp0']=[5.0, 'Interception (mm)', 'Default value of maximum water interceptable by vegetation, in millimiters', QVariant.Double, True, 1]
		#~ self.settings['param_default.ks']=[10.0, 'Soil hydraulic conductivity (mm/h)', 'Default value of soil hydraulic conductivity, in millimiters per hour', QVariant.Double, True, 1]
		#~ self.settings['param_default.kf']=[1e-07,'Acquifer conductivity (mm/s)', 'Default value of (real or ideal) aquifer conductivity, in meters per second', QVariant.Double, True, 1]
		#~ self.settings['param_default.CH']=[1e-03, 'Turbulent exchange coefficient (-)', 'Default value of turbulent exchange coeff. for heat, non dimensional', QVariant.Double, True, 1]
		#~ self.settings['param_default.Alb']=[2e-01, 'Albedo (-)', 'Default value of surface albedo, non dimensional ([positive number in float or exp notation])', QVariant.String, True, 1]
		
		#~ # default hydraulic parameters
		#~ self.settings['param_default.shape_urban']=['C', 'Shape','Section shape (code)', QVariant.String, True, 1]
		#~ self.settings['param_default.size_urban']=[0.8, 'Diameter (m)','Default value of conduits characteristic size, in meters', QVariant.Double, True, 1]
		#~ #self.settings['param_default.mat_urban']=['default', 'Material','Conduit material', QVariant.String, True, 1]
		#~ self.settings['param_default.L_urban']=[100.0, 'Length (m)', 'Default value of conduits length, in meters', QVariant.Double, True, 1]
		#~ self.settings['param_default.mann_urban']=[0.017, 'Manning\'s coefficient', 'Default value of conduits Manning\'s coefficient, in s/m^(1/3)', QVariant.Double, True, 1]
		#~ self.settings['param_default.yfull_urban']=[0.7, 'Default node depth', 'Default value of maximum water depth in nodes, in meters', QVariant.Double, True, 1]
		#~ self.settings['param_default.nodearea_urban']=[1.16, 'Default node area', 'Default value of nodes area, in squared meters', QVariant.Double, True, 1]
						
		# default gridded data filename
		self.settings['param_rasterfile.zz']=['dem.tif',  'Digital elevation model', 'Grid of basin elevation in meters above sea level (pathname)', QVariant.String, True, None]
		self.settings['param_rasterfile.zp']=['flowdir.tif',  'Flow direction grid', 'Grid of flow directions in 1-2-3-4-5-6-7-8 notation (pathname)', QVariant.String, True, None]
		self.settings['param_raster.pointertype']=['GRASS',  'Flow direction convention', 'Convention for flow directions (one amnog <ARC> or <GRASS>; default is <ARC>)', QVariant.String, False, None]
		self.settings['param_rasterfile.zr']=['flowaccum.tif',  'Flow accumulation grid','Grid of flow accumulation as number of upstream cells (pathname)', QVariant.String, True, None]
		self.settings['param_rasterfile.Wg0']=['wgmax.tif', 'Large pore water holding capacity (mm)', 'Grid of maximum water holding capacity in soil large pores, in millimiters (pathname)', QVariant.String, False, None]
		self.settings['param_rasterfile.Wc0']=['wcmax.tif', 'Small pore water holding capacity (mm)', 'Grid of maximum water holding capacity in soil small pores, in millimiters (pathname)', QVariant.String, False, None]
		self.settings['param_rasterfile.Wp0']=['wpmax.tif', 'Interception (mm)', 'Grid of maximum water interceptable by vegetation, in millimiters (pathname)', QVariant.String, False, None]
		self.settings['param_rasterfile.ks']=['ks.tif', 'Soil hydraulic conductivity (mm/h)', 'Grids of soil hydraulic conductivity, in millimiters per hour (pathname)', QVariant.String, False, None]
		self.settings['param_rasterfile.kf']=['kf.tif', 'Acquifer conductivity (mm/h)', 'Grid of (real or ideal) aquifer conductivity, in meters per second (pathname', QVariant.String, False, None]
		self.settings['param_rasterfile.CH']=['ch.tif', 'Turbulent exchange coefficient (-)', 'Grid of turbulent exchange coeff. for heat, non dimensional (pathname)', QVariant.String, False, None]
		self.settings['param_rasterfile.Alb']=['alb.tif', 'Albedo (-)', 'Grid of surface albedo, non dimensional (pathname)', QVariant.String, False, None]
		self.settings['param_rasterfile.Ma']=['ma.tif', 'Artesian acquifer extension', 'Grid of binary mask (0,1) defining the artesian aquifer extension (pathname)', QVariant.String, False, None]
		self.settings['param_rasterfile.Mf']=['mf.tif', 'Freatic acquifer extension', 'Grid of binary mask (0,1) defining the freatic aquifer extension (pathname)', QVariant.String, False, None]
		
		# drainage network file structure
		self.settings['param_shapefile.ret_urban']=['network.shp',  'Drainage network', 'Shape of urban drainage network (pathname to .shp file)', 'TEXT', True, None]
		self.settings['tablefile_key1.ret_urban']=['LINE_ID',  'Line id field', 'Field name of conduits numerical id. in urban drainage network attribute table', 'TEXT', True, None]
		self.settings['tablefile_key2.ret_urban']=['OBJ_START', 'Start node field', 'Field name of conduits starting node id in network attribute table', 'TEXT', True, None]
		self.settings['tablefile_key3.ret_urban']=['OBJ_END', 'End node field', 'Field name of conduits final node id in network attribute table', 'TEXT', True, None]
		self.settings['tablefile_key4.ret_urban']=['S_SHAPE', 'Conduit shape field', 'Field name of conduits cross sectional shape in network attribute table', 'TEXT', True, ('circular','rectangular')]
		self.settings['tablefile_key51.ret_urban']=['DIM1', 'First dimension field', 'Field name of conduits cross section characteristic length D1 (diameter for circular; height for rectangular) in network attribute table, in meter ', 'FLOAT', True, None]
		self.settings['tablefile_key52.ret_urban']=['DIM2', 'Second dimension field', 'Field name of conduits cross section characteristic length D2 (width for rectangular) in network attribute table, in meter ', 'FLOAT', False, None]
		self.settings['tablefile_key6.ret_urban']=['ELEV_START', 'Elevation start field', 'Field name of conduits invert elevation at starting point in network attribute table (m a.s.l.)', 'FLOAT', True, None]
		self.settings['tablefile_key7.ret_urban']=['ELEV_END', 'Elevation end field', 'Field name of conduits invert elevation at final point in network attribute table (m a.s.l.)', 'FLOAT', True, None]
		self.settings['tablefile_key8.ret_urban']=['MAT', 'Conduit material field', 'Field name of conduits material in network attribute table', 'TEXT', False,None]
		self.settings['tablefile_key9.ret_urban']=['MANN', 'Manning coefficient field', 'Field name of conduits Manning\'s coefficient (m^1/3 s^-1)', 'FLOAT', False, None]
		self.settings['tablefile_key10.ret_urban']=['LENGTH', 'Conduit length field', 'Field name of conduits length, in meters', 'FLOAT', False, None]
		
		# drainage nodes file structure
		self.settings['param_shapefile.nodes_urban']=['nodes.shp', 'Drainage nodes', 'Shape of nodes in urban drainage network (pathname to .shp file)', 'TEXT', True, None]
		self.settings['tablefile_key1.nodes_urban']=['OBJ_ID', 'Point id field', 'Field name of nodes numerical id. in the attribute table', 'TEXT', True, None]
		self.settings['tablefile_key2.nodes_urban']=['ELEV_BOT', 'Elevation at bottom field', 'Field name of node invert elevation in the attribute table (m a.s.l.)', 'FLOAT', True, None]
		self.settings['tablefile_key3.nodes_urban']=['ELEV_TOP', 'Elevation at top field', 'Field name of node top elevation in the attribute table (m a.s.l.)', 'FLOAT', True, None]
		self.settings['tablefile_key4.nodes_urban']=['DEPTH', 'Height field', 'Field name of node maximum water depth, in meters', 'FLOAT', False, None]
		self.settings['tablefile_key5.nodes_urban']=['AREA', 'Area field', 'Field name of node area, in squared meters', 'FLOAT', False, None]
		
		# streams network structure
		self.settings['param_shapefile.ret']=['streams.shp', 'Streams shapefile', 'Shape of river network (pathname)', QVariant.String, True, None]
		self.settings['param_tablefile.ret']=['streams.dbf', 'Streams table', 'Attribute table of river network (pathname)', QVariant.String, True, None]
		self.settings['tablefile_key1.ret']=['STREAM_ID', 'Streams id field', 'Field name of streams id. in network attribute table', QVariant.String, True, None]
		self.settings['tablefile_key2.ret']=['FROM_NODE', 'Streams from node field', 'Field name of streams start nodes in network attribute table', QVariant.String, True, None]
		self.settings['tablefile_key3.ret']=['TO_NODE', 'Streams to node field', 'Field name of streams end nodes in network attribute table', QVariant.String, True, None]
		self.settings['param_shapefile.res']=['reservoirs.shp', 'Reservoirs shapefile', 'Shape of reservoirs and lakes (pathname)', QVariant.String, False, None]
		self.settings['param_tablefile.res']=['reservoirs.dbf', 'Reservoirs table', 'Attribute table of reservoirs and lakes (pathname)', QVariant.String, False, None]
		self.settings['tablefile_key1.res']=['DAM_ID', 'Reservoirs id field', 'Field name of reservoirs and lakes id. in attribute table', QVariant.String, False, None]
		self.settings['tablefile_key2.res']=['DAM_ZTOP', 'Reservoirs top elevation', 'Field name of dam top elevation in reservoirs attribute table', QVariant.String, False, None]
		self.settings['tablefile_key3.res']=['DAM_START', 'Reservoirs starting operation date field', 'Field name of starting operation date in reservoirs attribute table', QVariant.String, False, None]
		
		#~ # default physical constants
		#~ self.settings['param_value.gamma___']=[1.679033e-06, 'Percolation coefficient (1/s)', 'Percolation coefficient, in one over seconds', QVariant.Double, True, None]
		#~ self.settings['param_value.kappa___']=[1e-04, 'Adsorption coefficient (1/s)','Adsorption coefficient, in one over seconds', QVariant.Double, True, None]
		#~ self.settings['param_value.beta____']=[1.576345e-06, 'Hypodermic flow coefficient (1/s)', 'Hypodermic flow coefficient, in one over seconds', QVariant.Double, True, None]
		#~ self.settings['param_value.alpha___']=[1e-03, 'Hillslope flow coefficient (1/s)', 'Hillslope flow coefficient, in one over seconds', QVariant.Double, True, None]
		#~ self.settings['param_value.CHfac___']=[0.5, 'Multiplying factor of turbulent exchange coeff. for heat (-)', 'Multiplying factor of turbulent exchange coeff. for heat, non dimensional', QVariant.Double, False, None]
		#~ self.settings['param_value.chafac__']=[1.0, 'Scale factor for fraction of channalized flow (-)', 'Scale factor for fraction of channalized flow, non dimensional', QVariant.Double, False, None]
		#~ self.settings['param_value.Tcost___']=[2.950e+02, 'Deep ground temperature (°K)', 'Deep ground temperature, in deg. Kelvin', QVariant.Double, True, None]
		#~ self.settings['param_value.kaps____']=[0.8, 'Soil thermal conductivity (W/m°K', 'Soil thermal conductivity, in watts per meter per deg.', QVariant.Double, True, None]
		#~ self.settings['param_value.nis_____']=[1.0e-05, 'Soil thermal diffusivity (m^2/s)', 'Soil thermal diffusivity, in square meters per second', QVariant.Double, True, None]
		#~ self.settings['param_value.wcel____']=[5.180, 'Flood wave celerity in channels (m/s)', 'Flood wave celerity in channels, in meters per second', QVariant.Double, True, None]
		#~ self.settings['param_value.celerfac']=[1.0, 'Scale factor for wave celerity in channels (-)', 'Scale factor for wave celerity in channels, non dimensional', QVariant.Double, False, None]
		#~ self.settings['param_value.Br0_____']=[1.0, 'Width of channels with first Strahler order (-)', 'Width of channels with first Strahler order, in meters', QVariant.Double, True, None]
		#~ self.settings['param_value.NBr_____']=[1.5, 'Exponent of the realtion B=O^N', 'Exponent of the realtion B=O^N, where B=Width of channels and O=Strahler order (positive number > 1)', QVariant.Double, True, None]
		#~ self.settings['param_value.n_Man___']=[3.0e-02, 'Manning\'s roughness coefficient for channels (s/m^(1/3))', 'Manning roughness coefficient for channels, in seconds over meters to one third', QVariant.Double, True, None]
		#~ self.settings['param_value.glo_loss']=[0.0, 'Global water loss from aquifers (m^3/s)', 'Global water loss from aquifers, in cubic meters per second', QVariant.Double, False, None]
		
		# default hydrological parameters
		self.settings['initinfo.ws']=[0.0, 'Inital depth of hillsope runoff (m)', 'Inital depth of hillsope runoff, in meters', QVariant.Double, False, None]
		self.settings['initinfo.wcsat']=[0.0, 'Inital relative saturation of capillary soil (-)', 'Inital relative saturation of capillary soil, non dimensional (in the range 0-1)', QVariant.Double, False,[0,1]]
		self.settings['initinfo.wgsat']=[0.0, 'Inital relative saturation of gravitational soil (-)', 'Inital relative saturation of gravitational soil, non dimensional (in the range 0-1)', QVariant.Double, False, [0,1]]
		self.settings['realtime']=[-1, 'Real time mode', 'Option to wait for new data at end of computation (realtime mode) (integer number, <0>=NO, <1>=YES, <-1>=CALIBRATION (AVOID RE-INTERPOLATION of METEOROLOGICAL DATA))', QVariant.Int, True,{'NO':0, 'YES':1, 'CALIBRATION':-1}]
		self.settings['degradfac']=[1, 'Degradation factor', 'Degradation factor from grid data space resolution to model space resolution, non dimensional (positive integer number)', QVariant.Int, True,1]
		self.settings['basestep']=[300.0, 'Time step (s)', 'Data and model time step, in seconds (positive number in float, eg: 86400 for daily data)', QVariant.Double, True,1]
		self.settings['routtype']=['None', 'Channel routing scheme', 'Type of channel routing scheme - ONLY NON URBAN RUNS (one amnog the following options <None>, <Musk>, <MuskCun>, <Lag>, <Linear>)', QVariant.String, True,{'None':'None', 'Musk':'Musk', 'MuskCun':'MuskCun', 'Lag':'Lag','Linear':'Linear'}]
		self.settings['bilatype']=['BUCKET', 'Soil hydrology scheme', 'Type of soil hydrology scheme (one amnog the following options <BUCKET>, <CN>)', QVariant.String, True,{'BUCKET':'BUCKET', 'CN':'CN'}]
		self.settings['enertype']=['None', 'Surface energy balance scheme', 'Type of surface energy balance scheme ([one among the following options <None>, <1L>, <2L> (deprecated), <5L>, <Snow>)', QVariant.String, True,{'1L':'1L', '2L':'2L', '5L':'5L', 'Snow':'Snow'}]
		self.settings['runtype']=['URBAN', 'Simulation type', 'Type of simulation (one amnog the following options <URBAN>, <NATURAL>; default is <NATURAL>)', QVariant.String, False, {'URBAN':'URBAN', 'NATURAL':'NATURAL'}]
		self.settings['timeseriespath']=['meteodata', 'Meteo data path', 'Directory where the micromet data files reside (directory path including terminal \\)', QVariant.String, True, None]
		self.settings['gaugetablepath']=['None', 'Stations characteristics path', 'Table of ground micromet stations characteristics - ONLY NON URBAN RUNS and ONLY if meteodata.mat file is not present (full pathname to .txt file)', QVariant.String, True, None]
		self.settings['rain_file']=['None', 'Precipitation data', 'Precipitation data, in tenths of millimiter - ONLY NON URBAN RUNS and ONLY if meteodata.mat file is not present (name of .dbf file)', QVariant.String, True, None]
		self.settings['tempmin_file']=['None', 'Minimum air temperature data', 'Minimum air temperature data, in tenths of deg. Celsius - ONLY NON URBAN RUNS and ONLY if meteodata.mat file is not present ([name of .dbf file)', QVariant.String, True, None]
		self.settings['tempmax_file']=['None', 'Maximum air temperature data', 'Maximum air temperature data, in tenths of deg. Celsius - ONLY NON URBAN RUNS and ONLY if meteodata.mat file is not present ([name of .dbf file)', QVariant.String, True, None]
		self.settings['radiation_file']=['None', 'Total radiation data', 'Total incoming radiation data, in watts per square meter - ONLY NON URBAN RUNS and ONLY if meteodata.mat file is not present ([name of .dbf file)', QVariant.String, True, None]
		self.settings['wind_file']=['None', 'Wind speed data', 'Wind speed data, in tenths of meters per second - ONLY NON URBAN RUNS and ONLY if meteodata.mat file is not present ([name of .dbf file)', QVariant.String, True, None]
		self.settings['humidity_file']=['None', 'Air humidity (%)', 'Air relative humidity data, in percent - ONLY NON URBAN RUNS and ONLY if meteodata.mat file is not present ([name of .dbf file)', QVariant.String, True, None]
		self.settings['discharge_file']=['None', 'Discharge data (l/s)', 'Discharge data, in liters per seconds (name of .dbf file', QVariant.String, False, None]
		self.settings['inout_file']=['None', 'Point diversion', 'Table of point diversions and discharges from surface water bodies ([name of .dbf file)', QVariant.String, False, None]
		self.settings['wells_file']=['None', 'Wells', 'Table of point diversions from groundater (wells) ([name of .dbf file)', QVariant.String, False, None]
		self.settings['watertableini_file']=['None', 'Aquifer head (m a.s.l.)', 'Grid of aquifer initial head, in meters above sea level (pathname)', QVariant.String, False, None]
		self.settings['urban.tr']=[5.0, 'Return time (y)', 'Return time of the rainfall event, in years', QVariant.Double, True, None]
		self.settings['urban.namf_a1']=['a1.csv', 'a1 (-)', 'RDF a1 parameter (h=a1*w*d^n, w=eps+alp/kap*(1-(ln(Tr/(1-Tr)))^kap)) (pathname to .csv file)', QVariant.String, True, None]
		self.settings['urban.namf_n']=['n.csv', 'n (-)', 'RDF n parameter (h=a1*w*d^n, w=eps+alp/kap*(1-(ln(Tr/(1-Tr)))^kap)) (pathname to .csv file)', QVariant.String, True, None]
		self.settings['urban.namf_alp']=['alp.csv', 'alp (-)', 'RDF alp parameter (h=a1*w*d^n, w=eps+alp/kap*(1-(ln(Tr/(1-Tr)))^kap)) (pathname to .csv file)', QVariant.String, True, None]
		self.settings['urban.namf_eps']=['eps.csv', 'eps (-)', 'RDF eps parameter (h=a1*w*d^n, w=eps+alp/kap*(1-(ln(Tr/(1-Tr)))^kap)) (pathname to .csv file)', QVariant.String, True, None]
		self.settings['urban.namf_kap']=['kap.csv', 'kap (-)', 'RDF kap parameter (h=a1*w*d^n, w=eps+alp/kap*(1-(ln(Tr/(1-Tr)))^kap)) (pathname to .csv file)', QVariant.String, True, None]
		
		# output save options
		self.settings['state_output.Qret']=[1, 'Save states for streams', 'Option to save states of streams network for results analysis (<0>=NO, <1>=YES)', QVariant.Int, True]
		self.settings['state_output.res_rout']=[0, 'Save states for reservoirs', 'Option to save states of reservoirs and lakes for results analysis (<0>=NO, <1>=YES)', QVariant.Int, True]
		self.settings['state_output.Wc']=[1, 'Save states for small pores', 'Option to save states of soil small pores for results analysis (<0>=NO, <1>=YES)', QVariant.Int, True]
		self.settings['state_output.Wg']=[1, 'Save states for large pores', 'Option to save states of soil large pores for results analysis (<0>=NO, <1>=YES)', QVariant.Int, True]
		self.settings['state_output.Ws']=[1, 'Save states for TODO', '(<0>=NO, <1>=YES)', QVariant.Int, False]
		self.settings['state_output.Wp']=[0, 'Save states for TODO', '(<0>=NO, <1>=YES)', QVariant.Int, False]
		self.settings['state_output.Ts']=[0, 'Save states for land surface temperature', 'Option to save states of land surface temperature for results analysis (<0>=NO, <1>=YES)', QVariant.Int, True]
		self.settings['state_output.Td']=[0, 'Save states for ground temperature', 'Option to save states of ground temperature for results analysis (<0>=NO, <1>=YES)', QVariant.Int, True]
		self.settings['state_output.h']=[0, 'Save states for acquifer', 'Option to save states of aquifers for results analysis (<0>=NO, <1>=YES)', QVariant.Int, True]
		self.settings['state_output.evr']=[0, 'Save states for evapotranspiration TODO', 'Option to save states of evapotranspiration and precipitation for results analysis (<0>=NO, <1>=YES)', QVariant.String, True]
		self.settings['state_output.ener']=[0, 'Save states for evapotranspiration TODO', 'Option to save states of evapotranspiration and precipitation for results analysis (<0>=NO, <1>=YES)', QVariant.String, True]
		self.settings['urban.rainlength']=[3.0, 'Rainfall duration (h)', 'Rainfall duration, in hours', QVariant.Double, True]
		self.settings['urban.simlength']=[15.0, 'Simulation duration (h)', 'Simulation duration, in hours', QVariant.Double, True]
		

if __name__ == '__console__':
	pass