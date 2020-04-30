# -*- coding: utf-8 -*-
"""
Demonstrates a way to put multiple axes around a single plot. 

(This will eventually become a built-in feature of PlotItem)

"""
#import initExample ## Add path to library (just for examples; you do not need this)

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np

pg.mkQApp()

pw = pg.PlotWidget()
pw.show()
pw.setWindowTitle('pyqtgraph example: MultiplePlotAxes')
p1 = pw.plotItem
p1.setLabels(left='axis 1')

## create a new ViewBox, link the right axis to its coordinate system
p2 = pg.ViewBox()
p1.showAxis('right')
p1.scene().addItem(p2)
p1.getAxis('right').linkToView(p2)
p2.setXLink(p1)
p1.getAxis('right').setLabel('axis2', color='#0000ff')

## create third ViewBox. 
## this time we need to create a new axis as well.
p3 = pg.ViewBox()
ax3 = pg.AxisItem('right')
p1.layout.addItem(ax3, 2, 3)
p1.scene().addItem(p3)
ax3.linkToView(p3)
p3.setXLink(p1)
ax3.setZValue(-10000)
ax3.setLabel('axis 3', color='#ff0000')

ged1=p1.plot()
ged2=pg.PlotCurveItem(pen='b')
p2.addItem(ged2)
ged3=pg.PlotCurveItem(pen='r')
p3.addItem(ged3)

aa=[]
bb=[]
cc=[]
num=0
## Handle view resizing 
def updateViews():
	global p1, p2, p3, num
	
	aa.extend([ num ])
	bb.extend([ num**2 ])
	cc.extend([ num**3 ])
	
	## view has resized; update auxiliary views to match
	
	p2.setGeometry(p1.vb.sceneBoundingRect())
	p3.setGeometry(p1.vb.sceneBoundingRect())
	
	## need to re-update linked axes since this was called
	## incorrectly while views had different shapes.
	## (probably this should be handled in ViewBox.resizeEvent)
	p2.linkedViewChanged(p1.vb, p2.XAxis)
	p3.linkedViewChanged(p1.vb, p3.XAxis)
	
	ged1.setData(aa)
	ged2.setData(bb)
	ged3.setData(cc)
	if num==10:
		ged1.clear()
		ged2.clear()
		ged3.clear()
		num=0
	
	num+=1

p1.vb.sigResized.connect(updateViews)
timer = QtCore.QTimer()
timer.timeout.connect(updateViews)
timer.start(1000)




## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
	import sys
	if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
		QtGui.QApplication.instance().exec_()
