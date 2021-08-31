# -*- coding: utf-8 -*-

import os
import scipy.io as sio
from qgis.core import NULL

def dataToMat(filename,data,name,progress = None,tr=None):
	dataDict = {}
	
	if os.path.exists(filename):
		dataDict = sio.loadmat(filename)
	
	dataDict[name] = data
	
	try:
		sio.savemat(filename, dataDict,do_compression =True)
		if progress is not None: progress.setInfo(tr('Grid %s exported to %s')%(name,filename),False)
	except IOError:
		if progress is not None: progress.setInfo(tr('Cannot save to %s because %s') %(filename,str(IOError)),True)
		
		
if __name__=='__console__':
    from numpy import array,uint16,uint8,nan
    
    data = array([[ (array([[19318]], dtype=uint16),
                    array([[ 1497040.46966712,  1497039.41146712]]),
                    array([[ 5038371.91680208,  5038328.8349919 ]]),
                    array([[ 148.74]]), array([[ 148.6]]),
                    array([[ 43.09]]), array([[ 0.00324901]]),
                    array([[ 0.013]]),
                    array([[ (array([u'C'], dtype='<U8'),
                                array([[ 0.4]]),
                                array([[NULL]], dtype=object),
                                array([[NULL]], dtype=object),
                                array([[NULL]], dtype=object),
                                array([[ nan]]),
                                array([[ 0.4]]),
                                array([[ 0.12566371]]),
                                array([[ 0.1]]),
                                array([[ 0.4]]),
                                array([[ 0.2]]),
                                array([[0]], dtype=uint8),
                                array([[ 0.42962309]]),
                                array([[ 0.94463874]]))]], 
                                dtype=[('shape', 'O'), ('d1', 'O'), ('d2', 'O'), ('d3', 'O'), ('d4', 'O'),
                                            ('d1derived', 'O'), ('yFull', 'O'), ('Afull', 'O'), ('Rfull', 'O'), ('wMax', 'O'), ('yWmax', 'O'),
                                            ('isopen', 'O'),('w96yFull', 'O'), ('Vfull', 'O')]),
                    array([[u'16788']], dtype='<U8'), array([[u'17199']], dtype='<U8'),
                    array([[5]], dtype=uint16), array([[6]], dtype=uint16),
                    array(-1.3499999999999943), array(-1.0400000000000205))],
                    [ (array([[9999]], dtype=uint16),
                    array([[ 1497040.46966712,  1497039.41146712]]),
                    array([[ 5038371.91680208,  5038328.8349919 ]]),
                    array([[ 148.74]]), array([[ 148.6]]),
                    array([[ 43.09]]), array([[ 0.00324901]]),
                    array([[ 0.013]]),
                    array([[ (array([u'C'], dtype='<U8'),
                                array([[ 0.4]]),
                                array([[NULL]], dtype=object),
                                array([[NULL]], dtype=object),
                                array([[NULL]], dtype=object),
                                array([[ nan]]),
                                array([[ 0.4]]),
                                array([[ 0.12566371]]),
                                array([[ 0.1]]),
                                array([[ 0.4]]),
                                array([[ 0.2]]),
                                array([[0]], dtype=uint8),
                                array([[ 0.42962309]]),
                                array([[ 0.94463874]]))]], 
                                dtype=[('shape', 'O'), ('d1', 'O'), ('d2', 'O'), ('d3', 'O'), ('d4', 'O'),
                                            ('d1derived', 'O'), ('yFull', 'O'), ('Afull', 'O'), ('Rfull', 'O'), ('wMax', 'O'), ('yWmax', 'O'),
                                            ('isopen', 'O'),('w96yFull', 'O'), ('Vfull', 'O')]),
                    array([[u'16788']], dtype='<U8'), array([[u'17199']], dtype='<U8'),
                    array([[5]], dtype=uint16), array([[6]], dtype=uint16),
                    array(-1.3499999999999943), array(-1.0400000000000205))]],
                    dtype=[('code', 'O'),('xx', 'O'),('yy', 'O'),('invert1', 'O'),('invert2', 'O'),
                                ('L', 'O'),('slope', 'O'),('manning', 'O'),('geometry', 'O'),
                                ('n1code', 'O'),('n2code', 'O'),('n1', 'O'),('n2', 'O'),
                                ('offset1', 'O'),('offset2', 'O')])

    dataToMat(filename = 'D:/test_smartgreen/tocheck.mat',data = data,name='ret',progress = None)