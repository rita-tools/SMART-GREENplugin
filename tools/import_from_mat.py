import scipy.io as sio
import numpy as np
import glob
from my_progress import MyProgress

class ImportFromMat():
	
	def __init__(self, progress = None):
		if progress is None:
			self.progress = MyProgress()
		else:
			self.progress = progress
		

	def importFromMat(self,filename,gKeyList,rec = -1):
		data = sio.loadmat(filename)
		#print 'data.keys():',data.keys()
		res = []
		for gk in gKeyList:
			if gk[0] in data.keys():
				tempData = data
				for k in gk:
					#print 'k:',k
					tempData = tempData[k]
					
				if rec >=0:
					tempData = tempData[rec][0][0][0]
				else:
					tempData = [d[0][0][0] for d in tempData]
			else:
				tempData = []
			
			res.append(tempData)
			
		return res
		
	def importFromFolder(self,folderName, root, varList):
		self.progress.setInfo('processing file ...', error = False)
		fileList = glob.glob(folderName+'/'+root+'*.mat')
		numFile = len(fileList)
		
		data = [[] for c in range(len(varList))]
		for f in fileList:
			self.progress.setInfo('... %s'%f, error = False)
			res = None
			try:
				res = self.importFromMat(f,varList)
			except Exception as e:
				self.progress.setInfo('Error loading mat file %s'%str(e), error = True)
				
			if res is not None:	
				for v,val in enumerate(varList):
					data[v].append(res[v])
			
		
		return data
	
if __name__=='__console__':
	folderName = 'D:/enricodata/progetto_SMARTGREEN/simulazioni/stato_esempio/states'
	root = 'state_'
	MI = ImportFromMat()
	data = MI.importFromFolder(folderName, root)
	#print '=== List ==='
	#print data
	adata = np.array(data).T
	print('=== narray ===')
	print(adata)

	from forms.chart_dialog import ChartDialog
	dlg = ChartDialog(title='test chart')
	y = adata[20]
	x = np.array(range(1,y.size+1))
	dlg.addLinePlot(x,y, name = 'discarge')
	dlg.setAxes(xlabs = None, ylabs = None, xTitle = 'time', yTitle = 'elevation', mainTitle = 'Altimetric Chart')
	dlg.show()