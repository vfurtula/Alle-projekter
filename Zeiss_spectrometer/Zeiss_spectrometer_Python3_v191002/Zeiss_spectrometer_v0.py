#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""


import time, sys, imp
from pyqtgraph.Qt import QtCore, QtGui
import config_zeiss
#from PyQt4 import QtGui, QtCore
#from PyQt4.QtCore import QThread, SIGNAL


class MainWindow(QtGui.QMainWindow):

	def __init__(self,parent=None):
		super(MainWindow, self).__init__(parent)
		
		MyBar = QtGui.QMenuBar(self)
		MyBar.setFixedWidth(80)
		self.MyBar2 = QtGui.QMenuBar(self)
		"""
    QMenuBar {
        background-color: rgb(49,49,49);
        color: rgb(255,255,255);
        border: 1px solid ;
    }

    QMenuBar::item {
        background-color: rgb(49,49,49);
        color: rgb(255,255,255);
    }

    QMenuBar::item::selected {
        background-color: rgb(30,30,30);
    }
		"""
		MyBar.setStyleSheet(''.join(['QMenuBar::item {background-color: yellow; }']))
		#MyBar.setStyleSheet(''.join(['QMenuBar {background-color: lightblue; }']))
		self.MyBar2.setStyleSheet(''.join(['QMenuBar::item::selected {background-color: lightblue; }']))
		MyBar.setToolTip("What do you wish to do? \nCALIBRATE stepper motor positions for the wavelengths or slit widths or \nSCAN wavelength and slit width while monitoring the signal.\nOnly one method is active at a time.")
		
		appMenu = MyBar.addMenu("Load app")
		
		self.appCalib = appMenu.addAction("Calibrate")
		self.appCalib.triggered.connect(self.runCalib)
		
		self.appScan = appMenu.addAction("Scan")
		self.appScan.triggered.connect(self.runScan)
		
		# main layout
		self.mainBar = QtGui.QHBoxLayout()
		self.mainBar.addWidget(MyBar)
		self.mainBar.addWidget(self.MyBar2)
		
		# main layout
		self.mainLayout = QtGui.QVBoxLayout()
		self.mainLayout.addLayout(self.mainBar)

		# central widget
		self.centralWidget = QtGui.QWidget()
		self.centralWidget.setLayout(self.mainLayout)

		# set central widget
		self.setCentralWidget(self.centralWidget)
		
		#self.move(50,50)
		self.setGeometry(50, 50, 400, 150)
		self.setWindowTitle('Automated Zeiss Monochromator')
		self.show()
		
		
	def runCalib(self):
		
		if self.appScan.isEnabled()==False:
			if not self.rg_scan.close():
				return None
			self.set_finished()
			
		imp.reload(config_zeiss)
		import Calib_Zeiss_spectrometer_GUI_v5
		self.rg_calib=Calib_Zeiss_spectrometer_GUI_v5.Run_gui(self.MyBar2)
		self.appCalib.setEnabled(False)
		
		self.mainLayout.addWidget(self.rg_calib)
		self.rg_calib.exec_()
		self.set_finished()
		
	def runScan(self):
		
		if self.appCalib.isEnabled()==False:
			if not self.rg_calib.close():
				return None
			self.set_finished()
		
		imp.reload(config_zeiss)
		import Scan_ZaberXmcb_GUI_v8
		self.rg_scan=Scan_ZaberXmcb_GUI_v8.Run_gui(self.MyBar2)
		self.appScan.setEnabled(False)
		
		self.mainLayout.addWidget(self.rg_scan)
		self.rg_scan.exec_()
		self.set_finished()
		
		
	def set_finished(self):
		
		if self.appCalib.isEnabled()==False:
			self.appCalib.setEnabled(True)
		
		if self.appScan.isEnabled()==False:
			self.appScan.setEnabled(True)
		
		self.MyBar2.clear()
		
		
	def closeEvent(self,event):
		
		if self.appCalib.isEnabled()==False:
			if self.rg_calib.close():
				self.set_finished()
				event.accept()
			else:
				event.ignore()
		
		if self.appScan.isEnabled()==False:
			if self.rg_scan.close():
				self.set_finished()
				event.accept()
			else:
				event.ignore()
		
		
def main():
	
	app=QtGui.QApplication(sys.argv)
	ex=MainWindow()
	#sys.exit(app.exec_())

	# avoid message 'Segmentation fault (core dumped)' with app.deleteLater()
	app.exec_()
	app.deleteLater()
	sys.exit()
	
if __name__=='__main__':
	
  main()
  
