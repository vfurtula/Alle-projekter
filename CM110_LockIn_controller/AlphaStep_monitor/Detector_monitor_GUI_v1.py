import os, sys, imp, serial, time, numpy
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.exporters
#from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, SIGNAL
import config_alpha, ArdUno



class Det_Mon_Thread(QThread):
	
	def __init__(self,*argv):
		QThread.__init__(self)
		
		# constants	
		self.end_flag=False
		self.setrun = argv[0]

	def __del__(self):
		
		self.wait()
	
	def stop_monit(self):
		
		self.end_flag=True
		
	def run(self):
		
		save_to_file = self.setrun.save_to_file
		
		time_start=time.time()
		while not self.end_flag:
			ard_volt=self.setrun.arduno.read_analog(self.setrun.analog_pin, self.setrun.avg_pts)
			if ard_volt in [serial.SerialException, ValueError]:
				self.emit(SIGNAL('ArdUno_badValue(PyQt_PyObject)'),ard_volt)
				return
			time_elap=time.time()-time_start
			
			As = self.setrun.sens_plot*ard_volt*2.2/1023
			self.emit(SIGNAL('make_update2(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),As,ard_volt,time_elap)
			
			with open(save_to_file, 'a') as thefile:
				thefile.write("%s\t" %round(time_elap,6))
				thefile.write("%s\t" %int(As))
				thefile.write("%s\t" %ard_volt)
				thefile.write("%s\n" %self.setrun.avg_pts)
				
				
				
				
				
				
class timer_Thread(QThread):

	def __init__(self):
		QThread.__init__(self)
		
		self.time_start=time.time()
		self.run_timer=False
		
	def __del__(self):
		
		self.wait()
	
	def stop_timer(self):
		
		self.run_timer=True
			
	def run(self):
		
		while True:
			# a short time rest needed otherwise the program freezes
			time.sleep(0.25)
			if self.run_timer:
				return
			elif time.time()-self.time_start>5*60:
				self.emit(SIGNAL('disconnect_serial()'))
				return
			
			
			
			
			
			
class Run_gui(QtGui.QDialog):
	
	def __init__(self, parent=None):
		QtGui.QDialog.__init__(self, parent)
		
		# Initial read of the config file
		self.analog_pin=config_alpha.Analog_pin
		self.avg_pts=config_alpha.Avgpts
		self.schroll_pts = config_alpha.Schroll_pts
		self.filename_str = config_alpha.filename
		self.foldername_str = config_alpha.foldername	
		self.alpha_sens = config_alpha.alphastepsens
		self.timestr = config_alpha.timestr
		self.ardport_str = config_alpha.ardport

		# Enable antialiasing for prettier plots		
		pg.setConfigOptions(antialias=True)
		self.initUI()
			
	def initUI(self):
		
		################### MENU BARS START ##################
		
		MyBar = QtGui.QMenuBar(self)
		
		fileMenu = MyBar.addMenu("File")
		fileSaveSet = fileMenu.addAction("Save settings")
		fileSaveSet.triggered.connect(self.set_save)
		fileSaveSet.setShortcut('Ctrl+S')
		fileSavePlt = fileMenu.addAction("Save plots")
		fileSavePlt.triggered.connect(self.set_save_plots)
		fileSavePlt.setShortcut('Ctrl+P')
		fileClose = fileMenu.addAction("Close")        
		fileClose.triggered.connect(self.close) # triggers closeEvent()
		fileClose.setShortcut('Ctrl+X')
		
		modeMenu = MyBar.addMenu("Mode")
		self.conMode = modeMenu.addAction("Connect to serial")
		self.conMode.triggered.connect(self.set_connect)
		self.disconMode = modeMenu.addAction("Disconnect from serial")
		self.disconMode.triggered.connect(self.set_disconnect)
		self.conMode.setEnabled(True)
		
		serialMenu = MyBar.addMenu("Serial port")
		self.serialArd = serialMenu.addAction("Arduino")
		self.serialArd.triggered.connect(self.ArdDialog)
				
		################### MENU BARS END ##################
		
		
		#####################################################
		lbl1 = QtGui.QLabel("ANALOG settings", self)
		lbl1.setStyleSheet("color: blue")
		
		analog_pin_lbl = QtGui.QLabel("Analog pin no.", self)
		self.combo0 = QtGui.QComboBox(self)
		mylist0=["0","1","2","3"]
		self.combo0.addItems(mylist0)
		self.combo0.setCurrentIndex(mylist0.index(str(self.analog_pin)))
		
		avgpts_lbl = QtGui.QLabel("Averaging points", self)
		self.combo1 = QtGui.QComboBox(self)
		mylist1=["1","5","20","100","200","500","1000","2000"]
		self.combo1.addItems(mylist1)
		self.combo1.setCurrentIndex(mylist1.index(str(self.avg_pts)))
		
		##############################################
		
		lbl2 = QtGui.QLabel("PLOT options", self)
		lbl2.setStyleSheet("color: blue")
		schroll_lbl = QtGui.QLabel("Schroll elapsed time",self)
		self.combo2 = QtGui.QComboBox(self)
		mylist2=["250 pts","500 pts","1000 pts","2000 pts","5000 pts","10000 pts"]
		self.combo2.addItems(mylist2)
		self.combo2.setCurrentIndex(mylist2.index(''.join([str(self.schroll_pts)," pts"])))
		
		sens_lbl = QtGui.QLabel(u'Alpha Step sens [\u00c5s]', self)
		self.combo3 = QtGui.QComboBox(self)
		mylist3=["2500","5000","10k","25k","50k","100k","250k","500k","1000k"]
		self.combo3.addItems(mylist3)
		self.combo3.setCurrentIndex(mylist3.index(str(self.alpha_sens)))
		self.onActivated3(self.alpha_sens)
		
		##############################################
		
		lbl3 = QtGui.QLabel("OPERATION mode", self)
		lbl3.setStyleSheet("color: blue")
		self.runButton = QtGui.QPushButton("Start",self)
		self.runButton.setEnabled(False)
		self.cancelButton = QtGui.QPushButton("STOP",self)
		self.cancelButton.setEnabled(False)
		self.clearButton = QtGui.QPushButton("Clear",self)
		
		##############################################
		
		lbl4 = QtGui.QLabel("STORAGE location settings:", self)
		lbl4.setStyleSheet("color: blue")
		filename = QtGui.QLabel("Save to file",self)
		foldername = QtGui.QLabel("Save to folder",self)
		self.filenameEdit = QtGui.QLineEdit(self.filename_str,self)
		self.foldernameEdit = QtGui.QLineEdit(self.foldername_str,self)
		
		##############################################
		
		self.timetrace_str = QtGui.QLabel("TIME trace for storing plots and data:", self)
		self.timetrace_str.setStyleSheet("color: blue")	
		
		self.lcd1 = QtGui.QLCDNumber(self)
		self.lcd1.setStyleSheet("color: red")
		self.lcd1.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd1.setNumDigits(11)
		self.lcd1.display(self.timestr)
		self.lcd1.setFixedHeight(70)
		
		##############################################
		
		# Add all widgets		
		g2_0 = QtGui.QVBoxLayout()
		g2_0.addWidget(MyBar)
		g2_0.addWidget(lbl1)
		g2_1 = QtGui.QGridLayout()
		g2_1.addWidget(analog_pin_lbl,1,0)
		g2_1.addWidget(self.combo0,1,1)
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
		g7_1.addWidget(sens_lbl,1,0)
		g7_1.addWidget(self.combo3,1,1)
		v7 = QtGui.QVBoxLayout()
		v7.addLayout(g7_0)
		v7.addLayout(g7_1)
		
		g5_0 = QtGui.QGridLayout()
		g5_0.addWidget(lbl3,0,0)
		g5_1 = QtGui.QGridLayout()
		g5_1.addWidget(self.runButton,0,0)
		g5_1.addWidget(self.cancelButton,0,1)
		g5_1.addWidget(self.clearButton,0,2)
		v5 = QtGui.QVBoxLayout()
		v5.addLayout(g5_0)
		v5.addLayout(g5_1)
		
		g4_0 = QtGui.QGridLayout()
		g4_0.addWidget(lbl4,0,0)
		g4_1 = QtGui.QGridLayout()
		g4_1.addWidget(filename,0,0)
		g4_1.addWidget(self.filenameEdit,0,1)
		g4_1.addWidget(foldername,1,0)
		g4_1.addWidget(self.foldernameEdit,1,1)
		v4 = QtGui.QVBoxLayout()
		v4.addLayout(g4_0)
		v4.addLayout(g4_1)
		
		g9_0 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g9_0.addWidget(self.timetrace_str)
		g9_0.addWidget(self.lcd1)
		
		# add all groups from v1 to v6 in one vertical group v7
		v8 = QtGui.QVBoxLayout()
		v8.addLayout(v2,1)
		v8.addLayout(v7)
		v8.addLayout(v4)
		v8.addLayout(v5)
		v8.addWidget(g9_0)
	
		# set graph  and toolbar to a new vertical group vcan
		self.pw1 = pg.PlotWidget()

		# SET ALL VERTICAL COLUMNS TOGETHER
		hbox = QtGui.QHBoxLayout()
		hbox.addLayout(v8,1)
		hbox.addWidget(self.pw1,4)
		self.setLayout(hbox) 
		
		# PLOT 2 settings
		# create plot and add it to the figure canvas
		self.p1 = self.pw1.plotItem
		self.curve1=self.p1.plot(pen='w')
		# create plot and add it to the figure
		self.p0_1 = pg.ViewBox()
		self.curve2=pg.PlotCurveItem(pen='r')
		self.p0_1.addItem(self.curve2)
		# connect respective axes to the plot 
		#self.p1.showAxis('left')
		self.p1.getAxis('left').setLabel("Film thickness", units=u"\u00c5s", color='yellow')
		self.p1.showAxis('right')
		self.p1.getAxis('right').setLabel("Arb unit, 1023=1.1V", units="", color='red')
		self.p1.scene().addItem(self.p0_1)
		self.p1.getAxis('right').linkToView(self.p0_1)
		self.p0_1.setXLink(self.p1)
		
		self.p1.getAxis('bottom').setLabel("Points", units="", color='yellow')
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw1.setDownsampling(mode='peak')
		self.pw1.setClipToView(True)
		
		# Initialize and set titles and axis names for both plots
		self.clear_vars_graphs()
		###############################################################################
		
		# reacts to choises picked in the menu
		self.combo0.activated[str].connect(self.onActivated0)
		self.combo1.activated[str].connect(self.onActivated1)
		self.combo2.activated[str].connect(self.onActivated2)
		self.combo3.activated[str].connect(self.onActivated3)
		
		# run or cancel the main script
		self.runButton.clicked.connect(self.set_run)
		self.cancelButton.clicked.connect(self.set_cancel)
		self.clearButton.clicked.connect(self.set_clear)
		
		self.allEditFields(False)
		self.bad_vals=False
		
		self.setGeometry(10,300,800,300)
		#self.move(0,350)
		self.setWindowTitle("Alpha Step Monitor")
		self.show()
			
	def allEditFields(self,trueorfalse):
		
		self.combo0.setEnabled(trueorfalse)
		self.combo1.setEnabled(trueorfalse)
		self.combo2.setEnabled(trueorfalse)
		self.combo3.setEnabled(trueorfalse)
		self.clearButton.setEnabled(trueorfalse)
		self.filenameEdit.setEnabled(trueorfalse)
		self.foldernameEdit.setEnabled(trueorfalse)
		
		self.disconMode.setEnabled(trueorfalse)
		self.runButton.setEnabled(trueorfalse)
	
	def ArdDialog(self):

		text, ok = QtGui.QInputDialog.getText(self, 'Serial Port Dialog','Enter Arduino serial:', text=self.ardport_str)
		if ok:
			self.ardport_str = str(text)
	
	def onActivated0(self, text):
		
		self.analog_pin = int(text)
	
	def onActivated1(self, text):
		
		self.avg_pts = str(text)
	
	def onActivated2(self, text):
		
		old_st=self.schroll_pts
		
		my_string=str(text)
		self.schroll_pts=int(my_string.split()[0])
		
		if old_st>self.schroll_pts:
			self.set_clear()
			
	def onActivated3(self, text):
		
		if str(text)=="2500":
			self.sens_plot=2500
		elif str(text)=="5000":
			self.sens_plot=5000
		elif str(text)=="10k":
			self.sens_plot=10000
		elif str(text)=="25k":
			self.sens_plot=25000
		elif str(text)=="50k":
			self.sens_plot=50000
		elif str(text)=="100k":
			self.sens_plot=100000
		elif str(text)=="250k":
			self.sens_plot=250000
		elif str(text)=="500k":
			self.sens_plot=500000
		elif str(text)=="1000k":
			self.sens_plot=1000000
		else:
			pass
		
	def set_run(self):
		
		# Check for possible name conflicts
		self.prepare_file()
		self.timer.stop_timer()

		self.allEditFields(False)
		self.cancelButton.setEnabled(True)
		
		setrun_obj=type('setscan_obj',(object,),{'analog_pin':self.analog_pin, 'avg_pts':self.avg_pts, 'sens_plot':self.sens_plot, 'arduno':self.arduno,'save_to_file':self.save_to_file })
		
		self.get_thread=Det_Mon_Thread(setrun_obj)	
		self.connect(self.get_thread, SIGNAL('make_update2(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.make_update2)
		self.connect(self.get_thread, SIGNAL('ArdUno_badValue(PyQt_PyObject)'), self.ArdUno_badValue)
		self.connect(self.get_thread, SIGNAL('finished()'), self.set_finished)

		self.get_thread.start()
		
	def make_update2(self,As,volts,timelist):
    
		self.all_time_tr.extend([ timelist ])
		self.tal+=1
		
		if len(self.tals)>self.schroll_pts:
			self.tals[:-1] = self.tals[1:]  # shift data in the array one sample left
			self.tals[-1] = self.tal
			self.plot_as_tr[:-1] = self.plot_as_tr[1:]  # shift data in the array one sample left
			self.plot_as_tr[-1] = As
			#self.plot_time_tr[:-1] = self.plot_time_tr[1:]  # shift data in the array one sample left
			#self.plot_time_tr[-1] = timelist
			self.plot_volts_tr[:-1] = self.plot_volts_tr[1:]  # shift data in the array one sample left
			self.plot_volts_tr[-1] = volts
		else:
			self.tals.extend([ self.tal ])
			self.plot_as_tr.extend([ As ])
			self.plot_volts_tr.extend([ volts ])
			#self.plot_time_tr.extend([ timelist ])
		
		## Handle view resizing 
		def updateViews():
			## view has resized; update auxiliary views to match
			self.p0_1.setGeometry(self.p1.vb.sceneBoundingRect())
			#p3.setGeometry(p1.vb.sceneBoundingRect())

			## need to re-update linked axes since this was called
			## incorrectly while views had different shapes.
			## (probably this should be handled in ViewBox.resizeEvent)
			self.p0_1.linkedViewChanged(self.p1.vb, self.p0_1.XAxis)
			#p3.linkedViewChanged(p1.vb, p3.XAxis)
			
		updateViews()
		self.p1.vb.sigResized.connect(updateViews)

		self.curve1.setData(self.tals, self.plot_as_tr)
		self.curve2.setData(self.tals, self.plot_volts_tr)

	def clear_vars_graphs(self):
		
		# PLOT 2 initial canvas settings
		self.tal=-1
		self.tals=[]
		self.all_time_tr=[]
		self.plot_as_tr=[]
		self.plot_volts_tr=[]
		#self.plot_time_tr=[]
		self.curve1.clear()
		self.curve2.clear()

	def set_connect(self):

		try:
			self.arduno = ArdUno.ARDUNO(self.ardport_str)
			self.arduno.set_timeout(0.5)
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message',"No response from the Arduino serial port! Check the serial port name and the cable connection.")
			return
		
		self.allEditFields(True)
		self.conMode.setEnabled(False)
		self.serialArd.setEnabled(False)
		self.clearButton.setText("Clear")
		
		self.timer=timer_Thread()	
		self.connect(self.timer, SIGNAL('disconnect_serial()'), self.set_disconnect)
		
		self.timer.start()
		
	def set_disconnect(self):
		
		self.arduno.close()
		
		self.allEditFields(False)
		self.conMode.setEnabled(True)
		self.serialArd.setEnabled(True)
	
	def ArdUno_badValue(self,pyqt_object):
		
		self.bad_vals=pyqt_object
		
	def set_cancel(self):

		self.get_thread.stop_monit()
		
		self.allEditFields(True)
		self.cancelButton.setEnabled(False)
	
	def set_clear(self):
		
		self.clear_vars_graphs()
		self.clearButton.setEnabled(False)
		self.clearButton.setText("Cleared")
	
	def prepare_file(self):
		
		# Check for possible name conflicts
		if str(self.filenameEdit.text()):
			saveinfile=''.join([str(self.filenameEdit.text()),self.timestr])
		else:
			saveinfile=''.join(["data_",self.timestr])
			
		if str(self.foldernameEdit.text()):
			if not os.path.isdir(str(self.foldernameEdit.text())):
				os.mkdir(str(self.foldernameEdit.text()))
			saveinfolder=''.join([str(self.foldernameEdit.text()),"/"])
		else:
			saveinfolder=""
		
		self.save_to_file=''.join([saveinfolder,saveinfile,".txt"])
		
		if not os.path.isfile(self.save_to_file):
			# creates elapsed time text file and close it
			with open(self.save_to_file, 'w') as thefile:
				thefile.write("film thickness[As] = AlphaStep_sens*Ard_step*2.2/1023\n")
				thefile.write('Elapsed time [s], Film thickness [As], Raw data step, Averaging points\n')
				
				
	def set_finished(self):
		
		if self.bad_vals==serial.SerialException:
			QtGui.QMessageBox.warning(self, 'Message',"Arduino serial severed. Closing the program..." )
			sys.exit()
		
		self.cancelButton.setEnabled(False)
		
		if self.bad_vals==ValueError:
			QtGui.QMessageBox.warning(self, 'Message',"Arduino getting bad values. Closing the serial..." )
			self.bad_vals=False
			self.set_disconnect()
			return
		
		self.allEditFields(True)
		self.clearButton.setEnabled(True)
		self.clearButton.setText("Clear")
		
		self.timer=timer_Thread()	
		self.connect(self.timer, SIGNAL('disconnect_serial()'), self.set_disconnect)
		
		self.timer.start()
	
	def closeEvent(self, event):
		
		reply = QtGui.QMessageBox.question(self, 'Message', "Quit now? Serial port will be flushed and disconnected!", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes:
			
			if hasattr(self, 'arduno'):
				if not hasattr(self, 'get_thread'):
					if self.arduno.is_open():
						self.arduno.close()
				else:
					if self.get_thread.isRunning():
						QtGui.QMessageBox.warning(self, 'Message', "Active monitoring in progress. Press STOP before closing the program!")
						event.ignore()
						return
					else:
						if self.arduno.is_open():
							self.arduno.close()
							
			if hasattr(self, 'timer'):
				if self.timer.isRunning():
					self.timer.stop_timer()
					
			event.accept()
		else:
			event.ignore()
			
	def set_save_plots(self):
		
		if str(self.filenameEdit.text()):
			saveinfile=''.join([str(self.filenameEdit.text()),self.timestr])
		else:
			saveinfile=''.join(["data_",self.timestr])
			
		if str(self.foldernameEdit.text()):
			if not os.path.isdir(str(self.foldernameEdit.text())):
				os.mkdir(str(self.foldernameEdit.text()))
			saveinfolder=''.join([str(self.foldernameEdit.text()),"/"])
		else:
			saveinfolder=""
		
		save_plot1=''.join([saveinfolder,saveinfile,'.png'])	

		# create an exporter instance, as an argument give it
		# the item you wish to export
		exporter = pg.exporters.ImageExporter(self.pw1.plotItem)
		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_plot1)
		
		
	def set_save(self):
		
		self.timestr=time.strftime("%y%m%d-%H%M")
		
		self.replace_line("config_alpha.py",0, ''.join(["Analog_pin=",str(self.analog_pin),"\n"]) )
		self.replace_line("config_alpha.py",1, ''.join(["Avgpts=",str(self.avg_pts),"\n"]) )
		self.replace_line("config_alpha.py",2, ''.join(["Schroll_pts=",str(self.schroll_pts),"\n"]))
		self.replace_line("config_alpha.py",3, ''.join(["alphastepsens=\"",self.alpha_sens,"\"\n"]) )
		self.replace_line("config_alpha.py",4, ''.join(["filename=\"",str(self.filenameEdit.text()),"\"\n"]) )
		self.replace_line("config_alpha.py",5, ''.join(["foldername=\"",str(self.foldernameEdit.text()),"\"\n"]) )
		self.replace_line("config_alpha.py",6, ''.join(["timestr=\"",self.timestr,"\"\n"]) )
		self.replace_line("config_alpha.py",7, ''.join(["ardport=\"",self.ardport_str,"\"\n"]) )
		
		self.lcd1.display(self.timestr)
		imp.reload(config_alpha)
		
		
	def replace_line(self,file_name, line_num, text):
		
		lines = open(file_name, 'r').readlines()
		lines[line_num] = text
		out = open(file_name, 'w')
		out.writelines(lines)
		out.close()
		
		
		
#########################################
#########################################



def main():
	
	app = QtGui.QApplication(sys.argv)
	ex = Run_gui()
	
	# avoid message 'Segmentation fault (core dumped)' with app.deleteLater()
	app.exec_()
	app.deleteLater()
	sys.exit()

if __name__ == '__main__':
	main()
