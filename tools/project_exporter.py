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
import datetime

from qgis.core import *

from my_progress import MyProgress

#~ import logging

class ProjectExporter():
	
	def __init__(self, DBM, tr,progress = None):
		if progress is None:
			self.progress = MyProgress()
		else:
			self.progress = progress
			
		self.DBM = DBM
		self.tr = tr
		self.outFile = None
		
	def saveAsCFM(self,cfmFile):
		try:
			self.outFile = open(cfmFile,'w')
		except IOError:
			self.progress.setInfo(self.tr('Cannot open file: %s' %cfmFile),True)
		
		# print settings value here
		self.setHeader()
		self.setParameter('project_name')
		self.setParameter('project_descr')
		self.setParameter('basin_id')
		self.setParameter('paramset_id')
		self.setParameter('basin_blon')
		self.setParameter('basin_blat')
		self.setParameter('gisdatapath')
		self.setParameter('statespath')
		#~ self.setParameter('param_value.d1_molti_urban')
		#~ self.setParameter('param_value.d2_molti_urban')
		#~ self.setParameter('param_value.L_molti_urban')
		#~ self.setParameter('param_value.ks_molti')
		#~ self.setParameter('param_value.wc_molti')
		#~ self.setParameter('param_value.wg_molti')
		#~ self.setParameter('param_value.area_molti_urban')
		#~ self.setParameter('param_default.Wg0')
		#~ self.setParameter('param_default.Wc0')
		#~ self.setParameter('param_default.Wp0')
		#~ self.setParameter('param_default.ks')
		#~ self.setParameter('param_default.kf')
		#~ self.setParameter('param_default.CH')
		#~ self.setParameter('param_default.Alb')
		#~ self.setParameter('param_default.shape_urban')
		#~ self.setParameter('param_default.size_urban')
		#~ self.setParameter('param_default.L_urban')
		#~ self.setParameter('param_default.mann_urban')
		#~ self.setParameter('param_default.yfull_urban')
		#~ self.setParameter('param_default.nodearea_urban')
		self.setParameter('param_value.gamma___')
		self.setParameter('param_value.kappa___')
		self.setParameter('param_value.beta____')
		self.setParameter('param_value.alpha___')
		self.setParameter('param_value.CHfac___')
		self.setParameter('param_value.chafac__')
		self.setParameter('param_value.Tcost___')
		self.setParameter('param_value.kaps____')
		self.setParameter('param_value.nis_____')
		self.setParameter('param_value.wcel____')
		self.setParameter('param_value.celerfac')
		self.setParameter('param_value.Br0_____')
		self.setParameter('param_value.NBr_____')
		self.setParameter('param_value.n_Man___')
		self.setParameter('param_value.glo_loss')
		self.setParameter('initinfo.ws')
		self.setParameter('initinfo.wcsat')
		self.setParameter('initinfo.wgsat')
		self.setParameter('realtime')
		#~ self.setParameter('degradfac')
		self.setParameter('basestep')
		#~ self.setParameter('routtype')
		#~ self.setParameter('bilatype')
		#~ self.setParameter('enertype')
		self.setParameter('runtype')
		self.setParameter('timeseriespath')
		#~ self.setParameter('gaugetablepath')
		#~ self.setParameter('rain_file')
		#~ self.setParameter('tempmin_file')
		#~ self.setParameter('tempmax_file')
		#~ self.setParameter('radiation_file')
		#~ self.setParameter('wind_file')
		#~ self.setParameter('humidity_file')
		#~ self.setParameter('discharge_file')
		#~ self.setParameter('inout_file')
		#~ self.setParameter('wells_file')
		#~ self.setParameter('watertableini_file')
		#~ self.setParameter('urban.tr')
		#~ self.setParameter('urban.namf_a1')
		#~ self.setParameter('urban.namf_n')
		#~ self.setParameter('urban.namf_alp')
		#~ self.setParameter('urban.namf_eps')
		#~ self.setParameter('urban.namf_kap')
		self.setParameter('state_output.Qret')
		self.setParameter('state_output.res_rout')
		self.setParameter('state_output.Wc')
		self.setParameter('state_output.Wg')
		self.setParameter('state_output.Ws')
		self.setParameter('state_output.Wp')
		self.setParameter('state_output.Ts')
		self.setParameter('state_output.Td')
		self.setParameter('state_output.h')
		self.setParameter('state_output.evr')
		self.setParameter('state_output.ener')
		#~ self.setParameter('urban.rainlength')
		self.setParameter('urban.simlength')
		#~ self.setParameter('urban.basestep')
		self.setParameter('urban.dt')
		
		# close file
		try:
			self.outFile.close()
		except:
			print(self.tr('Cannot close file: %s' %cfmFile))
		

		
	def setParameter(self,key,parName=None):
		if parName is None: parName=key
		
		# get param values from DB
		values = self.DBM.getDefaultRecord(parName)
		
		if len(values)>0:
			#~ value = self.settings[key][0]
			#~ if value in ['']:
				#~ return
				
			name = values[0]
			value = values[1]
			if type(value) is float:
				value = str(value)
							
			description = values[2]
			required = True
			
			txt = '# '+name + '\n'
			txt += '# '+description + '\n'
			if required: txt+='# REQUIRED\n'
			else: txt+='# OPTIONAL\n'
			#txt+=str(parName)+'   '+str(value) +'\n\n'
			txt+=parName+'   '+value +'\n\n'
			# write to file
			self.writeToFile(txt)
		else:
			self.progress.setInfo(self.tr("Parameter %s does't exist"%(key)),True)

	def setGroup(self, groupName):
		# TODO: check if txt+=
		txt = '# '+groupName + '\n\n'
		# write to file
		self.writeToFile(txt)
		
	def writeToFile(self,txt):
		if self.outFile:
			try:
				#txt = txt.encode('ascii', 'ignore') # force txt writing skipping not supported character
				txt = str(txt)
				self.outFile.write(txt)
			except Exception as e:
				self.progress.setInfo(self.tr('Cannot write to file %s')%str(e),True)
	
	def setHeader(self):
		txt = '###  MOBIDIC-u Project File  ###\n'
		txt+='### Autogenerated file from ###\n'
		txt += '###       SMART-GREEN        ###\n\n'
		
		# write to file
		self.writeToFile(txt)