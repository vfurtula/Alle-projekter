import os, sys, serial, time
import numpy, functools
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.exporters
#from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, SIGNAL
import config_calib, ESP300, MOTORSTEP_DRIVE

class Det_Mon_Thread(QThread):
	
	def __init__(self,*argv):
		QThread.__init__(self)
		
		# constants	
		self.end_flag=False
		
		self.analog_pin = argv[0]
		self.shutter_pin = argv[1]
		self.avg_pts = argv[2]
		self.Md = argv[3]

	def __del__(self):
		
		self.wait()
	
	def stop_monit(self):
		
		self.end_flag=True
		
	def run(self):
		
		time_start=time.time()
		while not self.end_flag:
			ard_volt=self.Md.read_analog(self.analog_pin,self.avg_pts)
			time_elap=time.time()-time_start						
			self.emit(SIGNAL('make_update2(PyQt_PyObject,PyQt_PyObject)'),ard_volt,time_elap)
		
		

class Det_Mon(QtGui.QWidget):

	def __init__(self):
		super(Det_Mon, self).__init__()
		
		# Initial read of the config file
		self.analog_pin=config_calib.Analog_pin
		self.shutter_pin=config_calib.Shutter_pin
		self.avg_pts=config_calib.Avgpts
		self.ardport_str = config_calib.ardport

		# Enable antialiasing for prettier plots		
		pg.setConfigOptions(antialias=True)
		self.initUI()
			
	def initUI(self):
		
		################### MENU BARS START ##################
		
		MyBar = QtGui.QMenuBar(self)
		fileMenu = MyBar.addMenu("File")
		fileClose = fileMenu.addAction("Close")        
		fileClose.triggered.connect(self.close) # triggers closeEvent()
		fileClose.setShortcut('Ctrl+X')
				
		modeMenu = MyBar.addMenu("Mode")
		self.conMode = modeMenu.addAction("Connect to serial")
		self.conMode.triggered.connect(self.set_connect)
		self.disconMode = modeMenu.addAction("Disconnect from serial")
		self.disconMode.triggered.connect(self.set_disconnect)
		self.conMode.setEnabled(True)
		self.disconMode.setEnabled(False)
		
		serialMenu = MyBar.addMenu("Serial port")
		self.serialArd = serialMenu.addAction("Arduino")
		self.serialArd.triggered.connect(self.ArdDialog)
				
		################### MENU BARS END ##################
		
		
		#####################################################
		lbl1 = QtGui.QLabel("ANALOG/DIGITAL settings", self)
		lbl1.setStyleSheet("color: blue")
		
		analog_pin_lbl = QtGui.QLabel("Analog pin no.", self)
		self.combo0 = QtGui.QComboBox(self)
		mylist0=["0","1","2","3"]
		self.combo0.addItems(mylist0)
		self.combo0.setCurrentIndex(mylist0.index(str(self.analog_pin)))
		
		shutter_pin_lbl = QtGui.QLabel("Shutter pin no.", self)
		self.combo3 = QtGui.QComboBox(self)
		mylist3=["45","46","47","48"]
		self.combo3.addItems(mylist3)
		self.combo3.setCurrentIndex(mylist3.index(str(self.shutter_pin)))
		
		avgpts_lbl = QtGui.QLabel("Averaging points", self)
		self.combo1 = QtGui.QComboBox(self)
		mylist1=["5","20","100","200","500","1000","2000"]
		self.combo1.addItems(mylist1)
		self.combo1.setCurrentIndex(mylist1.index(str(self.avg_pts)))
		
		lbl2 = QtGui.QLabel("PLOT options", self)
		lbl2.setStyleSheet("color: blue")
		schroll_lbl = QtGui.QLabel("Schroll elapsed time after",self)
		self.combo2 = QtGui.QComboBox(self)
		mylist2=[".5k points","1k points","2k points","5k points","10k points"]
		mylist2_tal=[500, 1000, 2000, 5000, 10000]
		self.combo2.addItems(mylist2)
		# initial combo settings
		self.combo2.setCurrentIndex(0)
		self.schroll_time=mylist2_tal[0]
		
		##############################################
		
		lbl3 = QtGui.QLabel("OPERATION mode", self)
		lbl3.setStyleSheet("color: blue")
		self.runButton = QtGui.QPushButton("START",self)
		self.runButton.setEnabled(False)
		self.cancelButton = QtGui.QPushButton("STOP",self)
		self.cancelButton.setEnabled(False)
		
		self.openShutter = QtGui.QPushButton("Open shutter",self)
		self.closeShutter = QtGui.QPushButton("Close shutter",self)
		self.openShutter.setEnabled(False)
		self.closeShutter.setEnabled(False)
		
		dummy_lbl = QtGui.QLabel("", self)
		
		##############################################
		# Add all widgets		
		g2_0 = QtGui.QVBoxLayout()
		g2_0.addWidget(MyBar)
		g2_0.addWidget(lbl1)
		g2_1 = QtGui.QGridLayout()
		g2_1.addWidget(analog_pin_lbl,1,0)
		g2_1.addWidget(self.combo0,1,1)
		g2_1.addWidget(shutter_pin_lbl,2,0)
		g2_1.addWidget(self.combo3,2,1)
		g2_1.addWidget(avgpts_lbl,3,0)
		g2_1.addWidget(self.combo1,3,1)
		v2 = QtGui.QVBoxLayout()
		v2.addLayout(g2_0)
		v2.addLayout(g2_1)
		
		g7_0 = QtGui.QGridLayout()
		g7_0.addWidget(lbl2,0,0)
		g7_1 = QtGui.QGridLayout()
		g7_1.addWidget(schroll_lbl,0,0)
		g7_1.addWidget(self.combo2,0,1)
		v7 = QtGui.QVBoxLayout()
		v7.addLayout(g7_0)
		v7.addLayout(g7_1)
		
		g5_0 = QtGui.QGridLayout()
		g5_0.addWidget(lbl3,0,0)
		g5_1 = QtGui.QGridLayout()
		g5_1.addWidget(self.runButton,0,0)
		g5_1.addWidget(self.cancelButton,0,1)
		g5_1.addWidget(self.openShutter,1,0)
		g5_1.addWidget(self.closeShutter,1,1)
		v5 = QtGui.QVBoxLayout()
		v5.addLayout(g5_0)
		v5.addLayout(g5_1)
		
		# add all groups from v1 to v6 in one vertical group v7
		v8 = QtGui.QVBoxLayout()
		v8.addLayout(v2,1)
		v8.addLayout(v7)
		v8.addLayout(v5)
		v8.addWidget(dummy_lbl,3)
	
		# set graph  and toolbar to a new vertical group vcan
		self.pw2 = pg.PlotWidget()

		# SET ALL VERTICAL COLUMNS TOGETHER
		hbox = QtGui.QHBoxLayout()
		hbox.addLayout(v8,1)
		hbox.addWidget(self.pw2,3.75)
		self.setLayout(hbox) 
		
		# PLOT 2 settings
		# create plot and add it to the figure canvas
		self.p1 = self.pw2.plotItem
		self.curve2=self.p1.plot(pen='w')
		# connect respective axes to the plot 
		self.p1.showAxis('left')
		self.p1.getAxis('left').setLabel("Arb unit, 1023=5V", units="", color='yellow')
		self.p1.getAxis('bottom').setLabel("Elapsed time", units="s", color='yellow')
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw2.setDownsampling(mode='peak')
		self.pw2.setClipToView(True)
		
		# Initialize and set titles and axis names for both plots
		#self.clear_vars_graphs()
		###############################################################################
		
		# reacts to choises picked in the menu
		self.combo0.activated[str].connect(self.onActivated0)
		self.combo1.activated[str].connect(self.onActivated1)
		self.combo2.activated[str].connect(self.onActivated2)
		self.combo3.activated[str].connect(self.onActivated3)
		
		
		# run or cancel the main script
		self.runButton.clicked.connect(self.set_run)
		self.cancelButton.clicked.connect(self.set_cancel)
		self.openShutter.clicked.connect(self.open_shutter)
		self.closeShutter.clicked.connect(self.close_shutter)
		
		self.allEditFields(False)
		
		self.send_close_signal=False
		#self.setGeometry(600,0,1300,800)
		self.move(600,0)
		self.setWindowTitle("Scatterometer - monitor detector")
		self.show()
			
	def allEditFields(self,trueorfalse):
		
		self.combo0.setEnabled(trueorfalse)
		self.combo1.setEnabled(trueorfalse)
		self.combo2.setEnabled(trueorfalse)
		self.combo3.setEnabled(trueorfalse)
		self.runButton.setEnabled(trueorfalse)
	
	def ArdDialog(self):

		text, ok = QtGui.QInputDialog.getText(self, 'Serial Port Dialog',
																				'Enter Arduino serial:', text=self.ardport_str)
		if ok:
			self.ardport_str = str(text)
	
	def onActivated0(self, text):
		
		self.analog_pin = int(text)
	
	def onActivated1(self, text):
		
		self.avg_pts = str(text)
	
	def onActivated2(self, text):
		
		if str(text)==".5k points":
			self.schroll_time=500
		elif str(text)=="1k points":
			self.schroll_time=1000
		elif str(text)=="2k points":
			self.schroll_time=2000
		elif str(text)=="5k points":
			self.schroll_time=5000
		elif str(text)=="10k points":
			self.schroll_time=10000
		else:
			pass
	
	def onActivated3(self, text):
		
		self.shutter_pin = int(text)
	
	def open_shutter(self):
		
		self.openShutter.setEnabled(False)
		self.closeShutter.setEnabled(True)
	
	def close_shutter(self):
		
		self.openShutter.setEnabled(True)
		self.closeShutter.setEnabled(False)
	
	def set_run(self):
		
		self.clear_vars_graphs()
		
		self.allEditFields(False)
		self.cancelButton.setEnabled(True)
		self.runButton.setEnabled(False)
		self.disconMode.setEnabled(False)
		self.serialArd.setEnabled(False)
		
		self.get_thread=Det_Mon_Thread(self.analog_pin,self.shutter_pin,self.avg_pts,self.Md)	
		self.connect(self.get_thread, SIGNAL('make_update2(PyQt_PyObject,PyQt_PyObject)'), self.make_update2)
		self.connect(self.get_thread, SIGNAL('finished()'), self.set_finished)

		self.get_thread.start()
		
	def make_update2(self,volts,timelist):
    
		self.all_time_tr.extend([ timelist ])

		if len(self.all_time_tr)>self.schroll_time:
			self.plot_time_tr[:-1] = self.plot_time_tr[1:]  # shift data in the array one sample left
			self.plot_time_tr[-1] = timelist
			self.plot_volts_tr[:-1] = self.plot_volts_tr[1:]  # shift data in the array one sample left
			self.plot_volts_tr[-1] = volts
		else:
			self.plot_volts_tr.extend([ volts ])
			self.plot_time_tr.extend([ timelist ])

		self.curve2.setData(self.plot_time_tr, self.plot_volts_tr)

	def clear_vars_graphs(self):
		
		# PLOT 2 initial canvas settings
		self.all_time_tr=[]
		self.plot_volts_tr=[]
		self.plot_time_tr=[]
		self.curve2.clear()

	def set_connect(self):

		try:
			self.Md = MOTORSTEP_DRIVE.MOTORSTEP_DRIVE(self.ardport_str)
			self.Md.set_timeout(2)
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message',"No response from the Arduino serial port! Check the Arduino port name and check the cable connection.")
			return None
			
		self.conMode.setEnabled(False)
		self.disconMode.setEnabled(True)
		self.serialArd.setEnabled(False)
		
		self.allEditFields(True)
		
		self.close_shutter()
			
	def set_disconnect(self):

		self.Md.close()
		
		self.allEditFields(False)
		self.conMode.setEnabled(True)
		self.disconMode.setEnabled(False)
		self.serialArd.setEnabled(True)
	
		self.close_shutter()
		self.openShutter.setEnabled(False)
	
	def set_cancel(self):

		self.get_thread.stop_monit()
		
		self.allEditFields(True)
		self.cancelButton.setEnabled(False)
		self.runButton.setEnabled(True)
	
	def set_finished(self):
		
		self.cancelButton.setEnabled(False)
		self.allEditFields(True)
		self.disconMode.setEnabled(True)
		self.serialArd.setEnabled(True)
	
	def closeEvent(self, event):
		
		reply = QtGui.QMessageBox.question(self, 'Message', "Quit now? Serial ports will be flushed and disconnected!", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes:
			if hasattr(self, 'Md'):	
				if not hasattr(self, 'get_thread'):
					if self.conMode.isEnabled()==True:
						self.send_close_signal=True
						event.accept()
					elif self.disconMode.isEnabled()==True:
						self.Md.close()
						self.send_close_signal=True
						event.accept()
				elif hasattr(self, 'get_thread'):
					if self.get_thread.isRunning():
						QtGui.QMessageBox.warning(self, 'Message', "Active monitoring in progress. Press STOP before closing the program!")
						event.ignore()
					else:
						if self.conMode.isEnabled()==True:
							self.send_close_signal=True
							event.accept()
						elif self.disconMode.isEnabled()==True:
							self.Md.close()
							self.send_close_signal=True
							event.accept()
			else:
				self.send_close_signal=True
				event.accept()
		else:
			event.ignore()  
			
	##########################################
	def send_signal(self):
		
		return self.send_close_signal

#########################################
#########################################

def main():
	
	app = QtGui.QApplication(sys.argv)
	ex = Det_Mon()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()