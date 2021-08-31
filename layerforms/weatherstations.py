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


from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLineEdit, QComboBox, QDialogButtonBox, QPushButton
from qgis.core import NULL, QgsRasterLayer,QgsRaster


def formOpen(dialog,layerid,featureid):
	global myDialog
	myDialog = dialog
	global layer
	layer = layerid
	global feature
	feature = featureid
	
	# hide dummy QLineBox
	tableFld = dialog.findChild(QLineEdit,'TABLE')
	tableFld.setHidden(True)
		
	#~ # populate combos with value
	tableCB = dialog.findChild(QComboBox,'TABLE_CB')
	updateTableItems(tableCB, tableFld)
	tableCB.currentIndexChanged[str].connect(tableFld.setText)
	
	if layer.isEditable():
		tableCB.setEnabled(True)
	else:
		tableCB.setEnabled(False)
	
	# select button
	#A1,N,ALP,EPS,KAP
	a1_Btn = dialog.findChild(QPushButton,'A1_BTN')
	n_Btn = dialog.findChild(QPushButton,'N_BTN')
	alp_Btn = dialog.findChild(QPushButton,'ALP_BTN')
	eps_Btn = dialog.findChild(QPushButton,'EPS_BTN')
	kap_Btn = dialog.findChild(QPushButton,'KAP_BTN')
	
	# connect button with function
	#['A1-dati','N-dati','Alpha-dati','K-dati','eps-dati']
	a1_Btn.clicked.connect(lambda: getFromWMS(a1_Btn))
	n_Btn.clicked.connect(lambda: getFromWMS(n_Btn))
	alp_Btn.clicked.connect(lambda: getFromWMS(alp_Btn))
	eps_Btn.clicked.connect(lambda: getFromWMS(eps_Btn))
	kap_Btn.clicked.connect(lambda: getFromWMS(kap_Btn))
	
	# activate buttons if layer is editable
	isEditable = layer.isEditable()
	a1_Btn.setEnabled(isEditable)
	n_Btn.setEnabled(isEditable)
	alp_Btn.setEnabled(isEditable)
	eps_Btn.setEnabled(isEditable)
	kap_Btn.setEnabled(isEditable)

def getFromWMS(btn):
	wmsLayers = {'A1':'A1-dati','N':'N-dati','ALP':'Alpha-dati','KAP':'K-dati','EPS':'eps-dati'}
	btnName = btn.objectName()
	toks = btnName.split('_')
	wmsLayer = wmsLayers[toks[0]]
	start = "value_0 = '"
	end = "'\n"
	val = None
	
	urlWithParams = "contextualWMSLegend=0&crs=EPSG:32632&dpiMode=7&featureCount=10&format=image/png&layers=a1i&layers="
	urlWithParams += wmsLayer
	urlWithParams += "&styles=&styles=&url=http://idro.arpalombardia.it/cgi-bin/mapserv?map%3D/var/www/idro/pmapper-4.0/config/wms/pmapper_wms.map"
	
	# make a raster layer
	try:
		rLayer = QgsRasterLayer(urlWithParams, wmsLayer, 'wms')
		if rLayer.isValid():
			# loop in vlayer and write attribute
			#print 'stats for ',selectedFeat.id(),qgis.analysis.cellInfoForBBox(rasterBBox,featureBBox,cellSizeX,cellSizeY)
			point = feature.geometry().centroid().asPoint()
			ident=rLayer.dataProvider().identify(point,QgsRaster.IdentifyFormatText)
			res = ident.results()
			print(res)
			if len(res)>0:
				val = res[res.keys()[0]]
				val = (val.split(start))[1].split(end)[0]
				
	except Exception as e:
		qgis.utils.plugins['SMARTGREEN'].showCriticalMessageBox(self.tr("Connection error to %s"%(urlWithParams)),
															self.tr("Layer cannot be update, see details"),
															str(e))
	
	if val is not None:
		# get Qlineedit
		valLE = myDialog.findChild(QLineEdit,toks[0])
		# set text
		valLE.setText(str(val))
		
def updateTableItems(comboBox, lineEdit):
	# get unique value list from nodes --> obj_id
	DBM = qgis.utils.plugins['SMARTGREEN'].DBM
	#~ lay = DBM.getTableAsLayer(DBM.getDefault('qgis.table.precipitations'),'precipitations')
	#~ if lay is None: return
	
	#~ idx = lay.fields().indexFromName('OBJ_ID')
	#~ values = lay.uniqueValues(idx)
	values = DBM.getColumnValues(fieldName='OBJ_ID',tableName='precipitations')
	values = ['NULL']+values
	comboBox.clear() # remove all item because it is called twice :(
	comboBox.addItems(['']+values)
	val = lineEdit.text()
	print('val:', val)
	if val == NULL:
		val = ''
				
	index = comboBox.findText(val, Qt.MatchFixedString)
	if index >= 0:
		comboBox.setCurrentIndex(index)
	
	