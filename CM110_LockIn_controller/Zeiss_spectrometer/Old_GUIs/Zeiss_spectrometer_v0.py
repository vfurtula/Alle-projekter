import os, sys, time, imp
import numpy, functools
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.exporters
#from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, SIGNAL


class my_Thread(QThread):
    
	def __init__(self, *argv):
		QThread.__init__(self)
		
		self.sender=argv[0]
		self.pp=argv[1]
    
	def __del__(self):
	  
	  self.wait()

	def run(self):
		
		while True:
			if self.pp.send_signal()==True:
				break
			else:
				time.sleep(0.25)
	

class run_zaber_gui(QtGui.QWidget):
  
	def __init__(self):
		super(run_zaber_gui, self).__init__()
	
		self.initUI()
    
	def initUI(self):

		# status info which button has been pressed
		Start_lbl = QtGui.QLabel("What do you wish to do? Only one method is active at a time.", self)
		Start_lbl.setStyleSheet("color: blue")
		
		####################################################
		
		Calib_lbl = QtGui.QLabel("Calibrate true positions of the Zeiss spectrometer wavelengths.", self)
		Calib_lbl.setStyleSheet("color: black")
		Calib_lbl.setWordWrap(True)
		self.Calib_Button = QtGui.QPushButton("Calibrate",self)
		self.button_style(self.Calib_Button,'black')
		self.Calib_Button.setEnabled(False)
		
		Scan_lbl = QtGui.QLabel("Scan the Zeiss spectromter using up to 3 independent intervals.", self)
		Scan_lbl.setStyleSheet("color: black")
		Scan_lbl.setWordWrap(True)
		self.Scan_Button = QtGui.QPushButton("Scan",self)
		self.button_style(self.Scan_Button,'black')
		self.Scan_Button.setEnabled(False)
		
		####################################################
		
		g0_0 = QtGui.QGridLayout()
		g0_0.addWidget(Start_lbl,0,0)
		g0_1 = QtGui.QGridLayout()
		g0_1.addWidget(Calib_lbl,0,0)
		g0_1.addWidget(self.Calib_Button,0,1)
		g0_1.addWidget(Scan_lbl,1,0)
		g0_1.addWidget(self.Scan_Button,1,1)
		v0 = QtGui.QVBoxLayout()
		v0.addLayout(g0_0)
		v0.addLayout(g0_1)
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		self.setLayout(v0)
		
		####################################################

		# reacts to choises picked in the menu
		self.allButtons_torf(True)
		self.Calib_Button.clicked.connect(self.set_run)
		self.Scan_Button.clicked.connect(self.set_run)
		
		self.move(0,0)
		self.setWindowTitle('Automated Zeiss Spectrometer')
		self.show()
	
	def button_style(self,button,color):
		
		button.setStyleSheet(''.join(['QPushButton {background-color: lightblue; font-size: 18pt; color: ',color,'}']))
		button.setFixedWidth(200)
		button.setFixedHeight(50)
	
	def allButtons_torf(self,text):
		
		self.Calib_Button.setEnabled(text)
		self.Scan_Button.setEnabled(text)
		
	def closeEvent(self,event):
		
		reply = QtGui.QMessageBox.question(self, 'Message', "Quit now? Make sure all subprograms are closed.", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes:
			if not hasattr(self, 'get_my_Thread'):
				event.accept()
			else:
				if hasattr(self, 'get_my_Thread'):
					if self.get_my_Thread.isRunning():
						QtGui.QMessageBox.warning(self, 'Message', "A subprogram is still open. Close the subprogram before exiting the main window.")
						event.ignore()
					else:
						event.accept()
		else:
			event.ignore() 
	##########################################
	
	def set_run(self):
		
		sender = self.sender()
		if sender.text()=='Calibrate':
			import Calib_Zeiss_spectrometer_GUI_v2
			self.pp=Calib_Zeiss_spectrometer_GUI_v2.run_zaber_gui()
			self.button_style(self.Calib_Button,'red')
			self.button_style(self.Scan_Button,'grey')
		elif sender.text()=='Scan':
			import Scan_ZaberXmcb_GUI_v4
			self.pp=Scan_ZaberXmcb_GUI_v4.run_zaber_gui()
			self.button_style(self.Scan_Button,'red')
			self.button_style(self.Calib_Button,'grey')
			
		self.get_my_Thread=my_Thread(sender.text(),self.pp)
		self.connect(self.get_my_Thread,SIGNAL('finished()'),self.set_finished)
		
		self.allButtons_torf(False)

		self.get_my_Thread.start()
	
	def set_finished(self):
		
		self.button_style(self.Calib_Button,'black')
		self.button_style(self.Scan_Button,'black')
		self.allButtons_torf(True)

def main():
  
  app=QtGui.QApplication(sys.argv)
  ex=run_zaber_gui()
  sys.exit(app.exec_())
    
if __name__=='__main__':
  main()
  
