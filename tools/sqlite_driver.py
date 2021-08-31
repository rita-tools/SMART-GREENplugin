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

import os
import numpy as np
import sqlite3 as sqlite
import io

from qgis.core import *

from my_progress import MyProgress

def adapt_array(arr):
	"""
	http://stackoverflow.com/a/31312102/190597 (SoulNibbler)
	"""
	out = io.BytesIO()
	np.save(out, arr)
	out.seek(0)
	return sqlite.Binary(out.read())

def convert_array(text):
	out = io.BytesIO(text)
	out.seek(0)
	return np.load(out)

# Converts np.array to TEXT when inserting
sqlite.register_adapter(np.ndarray, adapt_array)

# Converts TEXT to np.array when selecting
sqlite.register_converter("ARRAY", convert_array)

class SQLiteDriver():
	
	def __init__(self, filename, overwrite = True, progress = None):
		self.conn = None
		self.cur = None
		self.DBName = filename
		if progress is None:
			self.progress = MyProgress()
		else:
			self.progress = progress
		
		# create a new file if necessary
		try:
			if not os.path.exists(filename):
				# create a new file if necessary
				self.startConnection()
				self.stopConnection()
			else:
				if overwrite:
					os.remove(filename)
					self.startConnection()
					self.stopConnection()
				else:
					# do nothing, simply store the name of the file
					pass
		except Exception as e:
			self.progress.setInfo(str(e),True)

	def createSettingsTable(self, commonCrs):
		initTableSQL =	"""
		CREATE TABLE geometry_columns (
															f_table_name TEXT, 
															f_geometry_column TEXT, 
															geometry_type INTEGER, 
															coord_dimension INTEGER, 
															srid INTEGER,
															geometry_format TEXT );
		
		CREATE TABLE spatial_ref_sys (
														srid INTEGER UNIQUE,
														auth_name TEXT,
														auth_srid INTEGER,
														srtext TEXT  );
		"""
		crsSQL = """
		INSERT INTO spatial_ref_sys (srid, auth_name , auth_srid, srtext)
		VALUES  (1, '%s', '%s', '%s' );
		""" %(commonCrs.description(), commonCrs.authid(), commonCrs.toWkt())
		sql = initTableSQL+'\n'+crsSQL
		self.executeSQL(sql)
		
	def startConnection(self):
		# start connection
		self.conn = sqlite.connect(self.DBName,detect_types=sqlite.PARSE_DECLTYPES)
		# creating a Cursor
		self.cur = self.conn.cursor()
		
	def stopConnection(self):
		# run VACUUM to reduce the size
		self.conn.rollback()
		#self.cur.execute('VACUUM')
		self.conn.close()
		
	def executeSQL(self,sql):
		try:
			self.startConnection()
			self.cur.executescript(sql)
		except:
			self.progress.setInfo('SQL error at %s' %(sql),True)
		finally:
			self.stopConnection()
	
	def getTableAsLayer(self,name,displayName = None):
		if displayName is None: displayName = name
		# something like 'D:\\test_smartgreen\\aaaa_DATA\\tables.sqlite|layername=landuses'
		print('name',name)
		toks = name.split('|layername=')
		if len(toks)==2:
			name = toks[1]
			uri = '%s|layername=%s' % (self.DBName, name)
		else:
			uri = name

		print('uri', uri)
		table = None
		try:
			table = QgsVectorLayer(uri, displayName, 'ogr')
		except:
			pass
			
		return table
		
	def getTableSource(self,name):
		uri = '%s|layername=%s'%(self.DBName,name)
		return uri

	def parseValues(self, attrs):
		for i,a in enumerate(attrs):
			if type(a) =='unicode':
				a = a.encode('utf-8')

			a = '%s'%a
			a = a.replace("'","''")
			attrs[i] = a
		
		return attrs
		
	def joinRecord(self, data, digit = 3):
		data = [str(round(d,digit)) for d in data.tolist()]
		joinedData = "', '".join(data)
		joinedData = "('"+ joinedData +"')"
		return joinedData
		
	def importNumpyArray(self, name, columnNames, columnTypes, values, overwrite=True):
		from numpy import apply_along_axis
		#name = name.encode('utf-8')
		name = "'%s'"%name
		numCols = len(columnNames)
		fields = ', '.join(columnNames)
		fields_types = ["{} {}".format(f, t) for f, t in zip(columnNames, columnTypes)]
		fields_types = ', '.join(fields_types)
		concatValues = []
		nrows,ncols = values.shape
		for r in range(0,nrows):
			concatValues.append(self.joinRecord(values[r,:]))
		
		#concatValues = apply_along_axis(self.joinRecord, axis=1, arr=values)
		concatValues = ', '.join(concatValues)
		
		sql = 'BEGIN; '
		# drop table is exist
		if overwrite: sql += 'DROP TABLE IF EXISTS %s; ' %(name)
		# create table
		sql += 'CREATE TABLE %s (%s); ' %(name,fields_types)
		# populate table
		sql += 'INSERT INTO %s (%s) VALUES %s; ' %(name,fields,concatValues)
		sql += 'COMMIT;'
		
		try:
			self.startConnection()
			self.cur.executescript(sql)
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
		finally:
			self.stopConnection()
		

	def importCSV(self,filename,name, columnTypes = [], column_sep = ";", overwrite = True):
		columnNames = []
		#columnTypes = []
		concatValues = []
		# oper CSV file
		in_file = open(filename,"r")
		i = 0
		while 1:
			in_line = ''

			try:
				in_line = in_file.readline()
			except Exception as e:
				self.progress.setInfo('Parse error %s at line %s of filename %s' % (str(e), i+1,filename), True)

			if len(in_line) == 0:
				break

			if in_line[0] == '#':
				i = 0 # make valid line counter to zero
				pass # skip comments
			else:
				# process the line
				in_line = in_line[:-1]
				#print 'LN %d: %s'%(i,in_line)
				values = in_line.split(column_sep)
				if i == 0:
					# first is column name
					#print values
					columnNames = self.parseValues(values)
				else:
					# try to guess value types
					if len(columnTypes)!=len(columnNames):
						for val in values:
							try:
								toNumber = float(val)
								columnTypes.append('REAL')
							except:
								columnTypes.append('TEXT')

					concatValues.append("('"+ "', '".join(self.parseValues(values))+"')")

				i+=1
		
		fields = ', '.join(columnNames)
		fields_types = ["{} {}".format(f, t) for f, t in zip(columnNames, columnTypes)]
		fields_types = ', '.join(fields_types)
		concatValues = ', '.join(concatValues)
		
		#name = name.encode('utf-8')
		
		sql = 'BEGIN; '
		# drop table is exist
		if overwrite: sql += 'DROP TABLE IF EXISTS "%s"; ' %(name)
		# create table
		sql += 'CREATE TABLE "%s" (%s); ' %(name,fields_types)
		# populate table
		sql += 'INSERT INTO "%s" (%s) VALUES %s; ' %(name,fields,concatValues)
		sql += 'COMMIT;'
		
		try:
			self.startConnection()
			self.cur.executescript(sql)
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
		finally:
			self.stopConnection()
			
		
	def getTableFromLayer(self,layer):
		# dbname='D:/test_smartgreen\\aaaa_DATA.sqlite' table="soils" (geom) sql=
		marker = 'table="'
		source = layer.source()
		idx = source.index(marker)+len(marker)
		source = source[idx:]
		# get firt accourence of "
		idx = source.index('" ')
		source = source[:idx]
		return source
		
	def getNameFromLayer(self,layer):
		# D:/test_smartgreen\aaaa_DATA.sqlite|layername=nodes
		marker = '|layername='
		source = layer.source()
		#print 'source:',source
		#source = source.replace('\\','/')
		idx = source.index(marker)+len(marker)
		source = source[idx:]
		# get firt accourence of "
		#~ idx = source.index('" ')
		#~ source = source[:idx]
		return source
		
	def getTableFields(self, tablename):
		try:
			self.startConnection()
			sql = """PRAGMA table_info("%s")"""%(tablename)
			res = self.cur.execute(sql)
			data = self.cur.fetchall()
			names = ''
			for d in data:
				names = names+', '+d[1]
				
			# remove first 2 characters
			names = names[2:]
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
			names= ''
		finally:
			self.stopConnection()
			return names
			
	def getFieldsList(self, tablename):
		names = []
		try:
			self.startConnection()
			sql = """PRAGMA table_info("%s")"""%(tablename)
			res = self.cur.execute(sql)
			data = self.cur.fetchall()
			
			for d in data:
				names.append(d[1])
				
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
			names= []
		finally:
			self.stopConnection()
			return names
			
	def getTablesList(self):
		try:
			self.startConnection()
			sql = """SELECT name FROM sqlite_master WHERE type='table';"""
			res = self.cur.execute(sql)
			data = self.cur.fetchall()
			names = []
			for d in data:
				names.append(d[0])
				
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
			names= []
		finally:
			self.stopConnection()
			return names
			
	def removeTable(self, tablename):
		try:
			self.startConnection()
			sql = """DROP TABLE IF EXISTS '%s'""" %(tablename)
			res = self.cur.execute(sql)
			data = self.cur.fetchall()
			names = data
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
			names= ''
		finally:
			self.stopConnection()
			return names
			
	def deleteRow(self,tableName,fieldName,rowValue):
		try:
			self.startConnection()
			sql = """DELETE FROM %s WHERE %s = '%s'""" %(tableName, fieldName,rowValue)
			print(sql)
			res = self.cur.execute(sql)
			self.conn.commit() #!!!!!
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
		finally:
			self.stopConnection()
		
	def addVectorTable(self,name, fieldList, typeList, vectorType):
		# add default fields
		fieldList = ['ogc_fid','GEOMETRY'] + fieldList
		typeList = ['INTEGER PRIMARY KEY','BLOB'] + typeList
		fieldDefinition = ["'{}' {}".format(f, t) for f, t in zip(fieldList, typeList)]
		fieldDefinition = ', '.join(fieldDefinition)
		createVectorSQL = "CREATE TABLE '%s' (%s);" %(name,fieldDefinition)
		# update geometry columns
		updateSQL = """INSERT INTO geometry_columns (f_table_name, f_geometry_column , geometry_type, coord_dimension, srid, geometry_format)
								VALUES  ('%s', 'GEOMETRY', %s, 2, 1, 'WKB' );""" %(name,vectorType)
		sql = createVectorSQL+'\n'+updateSQL
		self.executeSQL(sql)
		
	def getDataFromTable(self,tableName,fieldList = ['*'],filter = None):
		fieldStr = ', '.join(fieldList)
		getDataSQL = "SELECT %s FROM '%s'" %(fieldStr,tableName)
		if filter is not None:
			getDataSQL+= ' WHERE '+str(filter)
		
		# run the query
		rows = None
		try:
			self.startConnection()
			res = self.cur.execute(getDataSQL)
			rows = self.cur.fetchall()
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),getDataSQL),True)
		finally:
			self.stopConnection()
		
		return rows
		
		
	def importFromLayer(self,fromLayer, toLayer, importData, settings, idList = []):
		"""
		Import geometry and attributes from a 'from layer' to a 'to layer'.
		Attributes are imported according to the conversion rules stored in settings
		"""
		
		toLayerType = toLayer.wkbType()
		fromLayerType = fromLayer.wkbType()
		
		#~ print 'importData:',importData
		
		if 	fromLayer.selectedFeatureCount()>0:
			# use current selection
			#print 'num. of selected features:',fromLayer.selectedFeatureCount()
			selection = fromLayer.selectedFeatures()
		else:
			# try with a list of ids provided by the user
			request = QgsFeatureRequest().setFilterFids(idList)
			selection = fromLayer.getFeatures(request)
			
		# something like: "crs":{"type":"name","properties":{"name":"EPSG:4326"}}
		vcrsAuthid = '"crs":{"type":"name","properties":{"name":"%s"}}' %(fromLayer.crs().authid())

		toTablename = self.getNameFromLayer(toLayer)
		
		# changes are only possible when editing the layer
		sql = 'INSERT INTO "%s" ' %(toTablename)
		fields = self.getTableFields(toTablename)
		toks = fields.split(', ')
		nFields = len(toks)
		#nFields = len(fromFldList)
		
		#sql += '(%s) ' %(fields)
		sql += '("%s") ' %('", "'.join(toks))
		
		sql += ' VALUES (%s)' %(', '.join(['?']*nFields))
		
		attrList = []
		for selectedFeat in selection:
			# get attribute value and transform it if necessary
			featAttr= (None,)
			# add the geometry blob
			geom = selectedFeat.geometry() # get geometry
			# Match geometry type
			# TODO: check types match
			if ((toLayerType == QgsWkbTypes.MultiPoint) or (toLayerType == QgsWkbTypes.Point))\
					and\
					((fromLayerType != QgsWkbTypes.MultiPoint) or (fromLayerType != QgsWkbTypes.Point) or (fromLayerType != QgsWkbTypes.PointZ)):
				# force centroid extraction
				geom = geom.centroid() #.asPoint()
			
			flag = geom.convertToMultiType() # cast geometry to multipart
			geomWKB = geom.asWkb() # export in well known binary format
			featAttr += (memoryview(geomWKB),)
			
			toFldVars = importData.keys()
			#print('toFldVars:',toFldVars)
			for i,toFldVar in enumerate(toFldVars):
				fromField,unit = importData[toFldVar]
				# get attribute value
				idx = fromLayer.fields().indexFromName(fromField)
				print('from',fromField,'-->',idx)
				
				value = None
				if idx>-1:
					value = selectedFeat.attributes()[idx]
					print(value, '-->', idx)
					#print 'value type',type(value)
					if (value == NULL):
						value = None
					else:
						# check if type of value is the same of the destination field
						toFldIdx = toLayer.fields().indexFromName(settings.getDefault(toFldVar))
						toFld = toLayer.fields().field(toFldIdx)
						print('to',toFld, '-->', toFldIdx)

						if toFldIdx>-1:
							#print fld.name(),fld.type()
							#print toFld.name(),'-',toFld.type(),'-',toFld.typeName()
							if toFld.typeName() == 'String':
								if not isinstance(value, str):
									value = '{0:g}'.format(value)
						
				#print  fromField, '- (',unit,') -->',settings[toFldVar][0],value,idx
				
				if unit == 'm':
					unit = 1.0
				elif unit == 'cm':
					unit = 0.01
				elif unit == 'mm':
					unit = 0.001
				else:
					unit = None
				
				#if (unit is not None) and (value is not None) and not isinstance(value, str): value = value * unit
				try: value = value * unit
				except: value = value

				#~ if toFldVar in settings:
					#~ toField = settings[toFldVar][0]
				#~ else:
					#~ toField = toFldList[i]
				
				# add the source layer to message
				#print 'fromField:',fromField
				if toFldVar == 'qgis.networklayer.field.msg':
					if (value is None) or (value == ''):
						value='4(%s)'%fromLayer.name()
					else:
						value+=', 4(%s)'%fromLayer.name()
				
				featAttr+=(value,)
			
			
			# append featAttr to attrList
			attrList.append(featAttr)
			#attrList = list(featAttr)
			#attrList[0] = 1
		
		#print sql
		try:
			self.startConnection()
			#self.cur.executemany(sql, attrList)
			self.cur.executemany(sql, attrList)
			self.conn.commit()
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
		finally:
			self.stopConnection()
			
		# update layer's extent when new features have been added
		# because change of extent in provider is not propagated to the layer
		toLayer.updateExtents()
		toLayer.triggerRepaint()
		
	def importFromDB(self,fromDB,tableName):
		try:
			self.startConnection()
			sql = "ATTACH DATABASE '%s' AS other; INSERT INTO %s SELECT * FROM %s;"%(fromDB,tableName,'other'+'.'+tableName)
			self.progress.setInfo('SQL: %s' %(sql),False)
			self.cur.executescript(sql)
			self.conn.commit()
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
		finally:
			self.stopConnection()
			
	def setDefault(self,defaultName,defaultValue, verbose= True):
		defaultTables = ['defaultprojectmetadata','defaultsimulationparameters','defaultconstants','defaulthydraulicparameters','defaulthydrologicalparameters','defaultdbstructure']
		for defaultTable in defaultTables:
			# search params
			# cursor.execute('INSERT INTO foo VALUES (?, ?)', ("It's okay", "No escaping necessary")
			#sql = "UPDATE %s SET value = '%s' WHERE id = '%s';"%(defaultTable,defaultValue,defaultName)
			sql = "UPDATE %s SET value = ? WHERE id = '%s';"%(defaultTable,defaultName)
			try:
				#print 'Running: %s' %(sql)
				self.startConnection()
				#res = self.cur.execute(sql)
				res = self.cur.execute(sql,(defaultValue,))
				self.conn.commit()
			except Exception as e:
				if verbose: self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
			finally:
				self.stopConnection()
		
	def getDefault(self,defaultName, verbose = True):
		defaultTables = ['defaultprojectmetadata','defaultsimulationparameters','defaultconstants','defaulthydraulicparameters','defaulthydrologicalparameters','defaultdbstructure']
		defaultValues = []
		for defaultTable in defaultTables:
			# search params
			try:
				self.startConnection()
				sql = "SELECT value FROM %s WHERE id = '%s';"%(defaultTable,defaultName)
				res = self.cur.execute(sql)
				data = self.cur.fetchall()
				for d in data:
					defaultValues.append(d[0])
					
			except Exception as e:
				if verbose: self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
				#defaultValues= []
			finally:
				self.stopConnection()
		
		return defaultValues[0]
		
	def getDefaultRecord(self,defaultName):
		defaultTables = ['defaultprojectmetadata','defaultsimulationparameters','defaultconstants','defaulthydraulicparameters','defaulthydrologicalparameters','defaultdbstructure']
		defaultValues = []
		for defaultTable in defaultTables:
			# search params
			try:
				self.startConnection()
				sql = "SELECT * FROM %s WHERE id = '%s';"%(defaultTable,defaultName)
				res = self.cur.execute(sql)
				data = self.cur.fetchall()
				for d in data:
					defaultValues.append(d)
					
			except Exception as e:
				self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
				#defaultValues= []
			finally:
				self.stopConnection()
				

		if len(defaultValues) > 0:
			res = defaultValues[0]
		else:
			self.progress.setInfo('Unable to find %s' %(defaultName),True)
			res = []
		
		return res
		
	def getRecord(self,tableName,fieldsList,filterFld, filterValue):
		resValues= []
		
		if isinstance(fieldsList,list):
			fieldsList = ','.join(fieldsList)
			
		if fieldsList == '': fieldsList='*'
		
		try:
			self.startConnection()
			if filterFld =='': sql = "SELECT %s FROM %s;"%(fieldsList,tableName)
			else: sql = "SELECT %s FROM %s WHERE %s = '%s';"%(fieldsList,tableName,filterFld,filterValue)
			res = self.cur.execute(sql)
			data = self.cur.fetchall()
			for d in data:
				resValues.append(d)
				
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
		finally:
			self.stopConnection()
			
		return resValues
		
	def createArrayTable(self,tableName='results'):
		try:
			self.startConnection()
			sql = 'CREATE TABLE IF NOT EXISTS "%s" (%s)' %(tableName,'OBJ_ID TEXT UNIQUE, VALARRAY ARRAY')
			self.cur.execute(sql)
			self.conn.commit() #!!!!!
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
		finally:
			self.stopConnection()
		
	def setArray(self,varName,nArray,tableName='results'):
		try:
			self.startConnection()
			sql = 'CREATE TABLE IF NOT EXISTS "%s" (%s)' %(tableName,'OBJ_ID TEXT UNIQUE, VALARRAY ARRAY')
			self.cur.execute(sql)
			sql = 'INSERT OR REPLACE INTO %s (OBJ_ID, VALARRAY) VALUES (?, ?)'%(tableName)
			self.cur.execute(sql, (varName, nArray,))
			self.conn.commit() #!!!!!
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
		finally:
			self.stopConnection()
			
	def setArrayName(self,oldVarName, newVarName, tableName):
		try:
			self.startConnection()
			# check if value already exists
			sql = "SELECT * FROM %s WHERE %s ='%s'" %(tableName,'OBJ_ID',newVarName)
			res = self.cur.execute(sql)
			data = self.cur.fetchall()
			defaultValues = []
			for d in data:
				defaultValues.append(d)
			
			if len(defaultValues) ==0:
				# if not, update old value
				sql = "UPDATE %s SET OBJ_ID = '%s' WHERE OBJ_ID ='%s'"%(tableName,newVarName,oldVarName)
				self.cur.execute(sql)
				self.conn.commit() #!!!!!
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
		finally:
			self.stopConnection()
		
		
		
			
	def getArray(self,varName,tableName='results'):
		data = None
		try:
			self.startConnection()
			sql = "SELECT VALARRAY FROM %s WHERE OBJ_ID = '%s';" %(tableName,varName)
			self.cur.execute(sql)
			data = self.cur.fetchone()[0]
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
		finally:
			self.stopConnection()
		
		return data
		
	def getColumnValues(self,fieldName,tableName):
		defaultValues = []
		try:
			self.startConnection()
			sql = "SELECT %s FROM %s;" %(fieldName,tableName)
			self.cur.execute(sql)
			data = self.cur.fetchall()
			for d in data:
				defaultValues.append(d[0])
				
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
		finally:
			self.stopConnection()
		
		return defaultValues
		
	def replaceAllColumnValues(self,tableName,colName,tupleList):
		sql = ''
		#~ try:
			#~ self.startConnection()
			#~ sql = 'ALTER TABLE %s ADD COLUMN %s REAL default null;'%(tableName, colName)
			#~ self.cur.execute(sql)
		#~ except Exception as e:
			#~ print 'SQL error %s at %s' %(str(e),sql)
		#~ finally:
			#~ self.stopConnection()
		
		try:
			self.startConnection()
			sql = 'UPDATE %s SET %s= ? WHERE ogc_fid=?'%(tableName,colName)
			self.cur.executemany(sql, tupleList)
			self.conn.commit() #!!!!!
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
		finally:
			self.stopConnection()
			
	def getMaxValue(self,tableName,colName):
		maxValue = None
		try:
			self.startConnection()
			sql = 'SELECT MAX(%s) FROM %s'%(colName,tableName)
			self.cur.execute(sql)
			data = self.cur.fetchall()
			for d in data:
				maxValue = d[0]
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
		finally:
			self.stopConnection()
			
		return maxValue
		
	def getRowId(self,table, ids, idFld):
		res = []

		try:
			for id in ids:
				self.startConnection()
				sql = 'SELECT rowid FROM %s WHERE %s = "%s"'%(table,idFld,id)
				self.cur.execute(sql)
				data = self.cur.fetchall()
				for d in data:
					res.append(int(d[0]))
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
		finally:
			self.stopConnection()
			
		return res
		
	def getAllFollowingLink(self,nodeStart = 'NODE_START',nodeEnd ='NODE_END',downStream = False):
		if not downStream:
			nodeStart = 'NODE_END'
			nodeEnd ='NODE_START'
			
		defaultValues = []
		
		try:
			self.startConnection()
			#sql = "SELECT links.OBJ_ID FROM links WHERE links.NODE_START IN (SELECT nodes.OBJ_ID FROM nodes, links WHERE nodes.OBJ_ID = links.NODE_END);"
			sql = "SELECT links.OBJ_ID FROM links WHERE links.%s IN (SELECT nodes.OBJ_ID FROM nodes, links WHERE nodes.OBJ_ID = links.%s);"%(nodeEnd,nodeStart)
			self.cur.execute(sql)
			data = self.cur.fetchall()
			for d in data:
				defaultValues.append(d[0])
				
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
		finally:
			self.stopConnection()
		
		return defaultValues
		
	def getFollowingLink(self,nodeId,nodeFld):
		defaultValues = []
		try:
			self.startConnection()
			#sql = "SELECT links.OBJ_ID FROM links WHERE links.NODE_START IN (SELECT nodes.OBJ_ID FROM nodes, links WHERE nodes.OBJ_ID = links.NODE_END);"
			sql = "SELECT links.OBJ_ID FROM links WHERE links.%s = '%s';"%(nodeFld,nodeId)
			self.cur.execute(sql)
			data = self.cur.fetchall()
			for d in data:
				defaultValues.append(d[0])
				
		except Exception as e:
			self.progress.setInfo('SQL error %s at %s' %(str(e),sql),True)
		finally:
			self.stopConnection()
		
		return defaultValues
		
		
	def testArrayOK2(self):
		print('in <testArray>')
		x = np.arange(12).reshape(2,6)
		print(type(x))
		
		#~ self.setArray(varName = 'x',nArray = x, tableName='results')
		#~ res = self.getArray(varName = 'x',tableName='results')
		#~ print 'res:',res
		self.startConnection()
		
		self.cur.execute("create table results (varname TEXT, varvalue ARRAY)")
		#self.cur.execute("create table results (varname TEXT, varvalue BLOB)")
		print('after create')
		self.cur.execute("insert into results (varname,varvalue) values (?,?)", ('x',x,))
		
		#~ out = io.BytesIO()
		#~ np.save(out, x)
		#~ out.seek(0)
		#~ binx = sqlite.Binary(out.read())
		
		
		#~ self.cur.execute("insert into results (varname,varvalue) values (?,?)", ('x',binx))
		print('after insert')

		self.conn.commit() #!!!!!
		
		
		self.stopConnection()
		
		self.startConnection()
		self.cur.execute("select varname,varvalue from results")
		print('after select')
		rec = self.cur.fetchone()
		name = rec[0]
		data = rec[1]
		
		#~ databin = rec[1]
		
		#~ out = io.BytesIO(databin)
		#~ out.seek(0)
		#~ data =  np.load(out)

		print(name)
		print(data)
		print(type(data))
		
		self.stopConnection()
		
	def testGetArray(self):
		self.startConnection()
		self.cur.execute("select varname,varvalue from results")
		rec = self.cur.fetchone()
		
		name = rec[0]
		data = rec[1]

		print(name)
		print(data)
		print(type(data))
		
		self.stopConnection()
		
		
	def testArrayOK(self):
		print('in <testArrayOK>')
		x = np.arange(12).reshape(2,6)
		print(type(x))

		con = sqlite.connect(":memory:", detect_types=sqlite.PARSE_DECLTYPES)
		print('after connect')
		cur = con.cursor()
		print('after cursor')
		cur.execute("create table test (id TEXT, arr ARRAY)")
		print('after create')
		cur.execute("insert into test (id,arr) values (?,?)", ('x',x,))
		print('after insert')
		cur.execute("select id,arr from test")
		print('after select')
		rec = cur.fetchone()
		name = rec[0]
		data = rec[1]

		print(name)
		print(data)
		print(type(data))

		

if __name__ == '__console__':
	DBM = SQLiteDriver('d:/test/dabuttare6_DATA.sqlite', False)
	#~ myList = np.random.rand(5).tolist()
	#~ print 'myList:',myList
	#mytList = [(val,) for val in myList]
	#mytList=tuple(mytList)
	#~ #mytList = ((val,) for val in myList)
	#~ mytList = (tuple(val) for val in myList)
	mytList = [(1,1), (2,2), (3,3), (4,4), (5,5)]
	print('myTuple:', mytList)
	# update table column
	DBM.replaceAllColumnValues(tableName = 'links',colName='tValue',tupleList=mytList)

	
	#~ ## CREATE TABLE t(x INTEGER, y, z, PRIMARY KEY(x ASC));
	#~ DBM = SQLiteDriver('d:/test/dbtest.sqlite')
	#~ initTableSQL =	"""
	#~ CREATE TABLE geometry_columns (f_table_name VARCHAR,
													#~ f_geometry_column VARCHAR,
													#~ geometry_type INTEGER,
													#~ coord_dimension INTEGER,
													#~ srid INTEGER,
													#~ geometry_format VARCHAR );
	#~ CREATE TABLE spatial_ref_sys (srid INTEGER UNIQUE,
													#~ auth_name TEXT,
													#~ auth_srid TEXT,
													#~ srtext TEXT);
	#~ CREATE TABLE 'links' (ogc_fid INTEGER PRIMARY KEY,
										#~ 'GEOMETRY' BLOB,
										#~ 'line_id' VARCHAR(254),
										#~ 'obj_start' VARCHAR(254),
										#~ 'obj_end' VARCHAR(254),
										#~ 's_shape' VARCHAR(254),
										#~ 'heigth' FLOAT,
										#~ 'width' FLOAT,
										#~ 'elev_start' FLOAT,
										#~ 'elev_end' FLOAT,
										#~ 'mat' VARCHAR(254),
										#~ 'mann' FLOAT,
										#~ 'length' FLOAT,
										#~ 'msg' VARCHAR(254));

	#~ CREATE TABLE 'nodes' (ogc_fid INTEGER PRIMARY KEY,
										#~ 'GEOMETRY' BLOB,
										#~ 'node_id' VARCHAR(254),
										#~ 'obj_start' VARCHAR(254),
										#~ 'obj_end' VARCHAR(254),
										#~ 'msg' VARCHAR(254));
										
	#~ INSERT INTO geometry_columns (f_table_name, f_geometry_column , geometry_type, coord_dimension, srid, geometry_format)
	#~ VALUES  ('links', 'GEOMETRY', 2, 2, 1, 'WKB' ),('nodes', 'GEOMETRY', 1, 2, 1, 'WKB' );

	#~ INSERT INTO spatial_ref_sys (srid, auth_name , auth_srid, srtext)
	#~ VALUES  (1, 'WGS 84 / UTM zone 32N', '32632', 'PROJCS["WGS 84 / UTM zone 32N",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",9],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH],AUTHORITY["EPSG","32632"]]' );
	#~ """
	#~ DBM.executeSQL(initTableSQL)
	#~ print 'OK'