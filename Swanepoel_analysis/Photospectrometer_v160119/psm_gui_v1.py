import os, sys, time
#import matplotlib.pyplot as plt
#from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
#from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.exporters
#from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, SIGNAL
import config_file

class PSM_GUI(QtGui.QWidget):

	def __init__(self):
		super(PSM_GUI, self).__init__()
		
		# Initial read of the config file
		self.film_sub_olis = config_file.film_sub_olis
		self.film_sub_ftir = config_file.film_sub_ftir
		self.sub_olis = config_file.sub_olis
		self.sub_ftir = config_file.sub_ftir
		self.fit_linear_spline = config_file.fit_linear_spline
		
		self.data_in=config_file.input_data_folder
		self.data_out=config_file.output_data_folder
		self.filename_str=config_file.filename_str
		self.timestr=config_file.timestr

		# For SAVING data and graphs
		if self.filename_str:
			self.full_filename=''.join([self.filename_str,self.timestr])
		elif self.film_sub_olis:
			self.full_filename=''.join([self.film_sub_olis,self.timestr])
		elif self.film_sub_ftir:
			self.full_filename=''.join([self.film_sub_ftir,self.timestr])
		else:
			raise ValueError('Measurement file name(s) are required!')
		
			
		if self.data_out:
			self.saveinfolder=''.join([self.data_out,"/"])
			if not os.path.isdir(self.data_out):
				os.mkdir(self.data_out)
		else:
			self.saveinfolder=""
			
		self.initUI()
			
	def initUI(self): 
		
		#####################################################

		lbl0 = QtGui.QLabel("LOAD raw data:", self)
		lbl0.setStyleSheet("color: blue")
		olis_lbl = QtGui.QLabel("Olis: sub+film, sub ",self)
		self.olis_sfEdit = QtGui.QLineEdit(str(self.film_sub_olis),self)
		self.olis_sEdit = QtGui.QLineEdit(str(self.sub_olis),self)
		ftir_lbl = QtGui.QLabel("Ftir: sub+film, sub ",self)
		self.ftir_sfEdit = QtGui.QLineEdit(str(self.film_sub_ftir),self)
		self.ftir_sEdit = QtGui.QLineEdit(str(self.sub_ftir),self)
		interp_lbl = QtGui.QLabel("Interpolation", self)
		self.combo1 = QtGui.QComboBox(self)
		mylist=["linear", "spline"]
		self.combo1.addItems(mylist)
		self.combo1.setCurrentIndex(mylist.index(str(self.fit_linear_spline)))
		
		lbl1 = QtGui.QLabel("STORAGE filename and location:", self)
		lbl1.setStyleSheet("color: blue")
		filename = QtGui.QLabel("File, Folder",self)
		self.filenameEdit = QtGui.QLineEdit(str(self.filename_str),self)
		self.data_outEdit = QtGui.QLineEdit(str(self.data_out),self)
		
		##############################################
		
		lbl2 = QtGui.QLabel("RECORD data and save images:", self)
		lbl2.setStyleSheet("color: blue")
		
		save_str = QtGui.QLabel("Store settings", self)
		self.saveButton = QtGui.QPushButton("Save",self)
		self.saveButton.setEnabled(True)
		
		run_str = QtGui.QLabel("Record lock-in data", self)
		self.runButton = QtGui.QPushButton("Run",self)
		self.runButton.setEnabled(True)
		
		saveplots_str = QtGui.QLabel("Save plots as png", self)
		self.saveplotsButton = QtGui.QPushButton("Save plots",self)
		self.saveplotsButton.setEnabled(True)
		'''
		elapsedtime_str = QtGui.QLabel('Show voltage vs. time', self)
		self.elapsedtimeButton = QtGui.QPushButton("Plot 2",self)
		self.elapsedtimeButton.setEnabled(False)
		'''
		cancel_str = QtGui.QLabel("Cancel current run", self)
		self.cancelButton = QtGui.QPushButton("Cancel",self)
		self.cancelButton.setEnabled(False)
		
		##############################################
		
		# status info which button has been pressed
		self.status_str = QtGui.QLabel("Edit settings and press SAVE!", self)
		self.status_str.setStyleSheet("color: green")
		
		##############################################
		
		# status info which button has been pressed
		self.elapsedtime_str = QtGui.QLabel("TIME trace for storing plots and data:", self)
		self.elapsedtime_str.setStyleSheet("color: blue")
		
		##############################################
		
		self.lcd = QtGui.QLCDNumber(self)
		self.lcd.setStyleSheet("color: red")
		self.lcd.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd.setNumDigits(13)
		self.lcd.display(self.timestr)
			
		##############################################
		# Add all widgets
		g0_0 = QtGui.QGridLayout()
		g0_0.addWidget(lbl0,0,0)
		g0_1 = QtGui.QGridLayout()
		g0_1.addWidget(olis_lbl,0,0)
		g0_1.addWidget(ftir_lbl,1,0)
		g0_1.addWidget(interp_lbl,2,0)
		g0_1.addWidget(self.olis_sfEdit,0,1)
		g0_1.addWidget(self.olis_sEdit,0,2)
		g0_1.addWidget(self.ftir_sfEdit,1,1)
		g0_1.addWidget(self.ftir_sEdit,1,2)		
		g0_1.addWidget(self.combo1,2,1)
		v0 = QtGui.QVBoxLayout()
		v0.addLayout(g0_0)
		v0.addLayout(g0_1)
				
		g1_0 = QtGui.QGridLayout()
		g1_0.addWidget(lbl1,0,0)
		g1_1 = QtGui.QGridLayout()
		g1_1.addWidget(filename,0,0)
		g1_1.addWidget(self.filenameEdit,0,1)
		g1_1.addWidget(self.data_outEdit,0,2)
		v1 = QtGui.QVBoxLayout()
		v1.addLayout(g1_0)
		v1.addLayout(g1_1)
		
		g2_0 = QtGui.QGridLayout()
		g2_0.addWidget(lbl2,0,0)
		g2_1 = QtGui.QGridLayout()
		g2_1.addWidget(save_str,0,0)
		g2_1.addWidget(run_str,1,0)
		g2_1.addWidget(saveplots_str,2,0)
		g2_1.addWidget(cancel_str,3,0)
		g2_1.addWidget(self.saveButton,0,1)
		g2_1.addWidget(self.runButton,1,1)
		g2_1.addWidget(self.saveplotsButton,2,1)
		g2_1.addWidget(self.cancelButton,3,1)
		v2 = QtGui.QVBoxLayout()
		v2.addLayout(g2_0)
		v2.addLayout(g2_1)
		
		g3_0 = QtGui.QGridLayout()
		g3_0.addWidget(self.status_str,1,0)
		g3_0.addWidget(self.elapsedtime_str,2,0)
		g3_1 = QtGui.QGridLayout()
		g3_1.addWidget(self.lcd,0,0)
		v3 = QtGui.QVBoxLayout()
		v3.addLayout(g3_0)
		v3.addLayout(g3_1)
		
		# add all groups from v1 to v6 in one vertical group v7
		v4 = QtGui.QVBoxLayout()
		v4.addLayout(v0)
		v4.addLayout(v1)
		v4.addLayout(v2)
		v4.addLayout(v3)

	
		# set graph  and toolbar to a new vertical group vcan
		vcan = QtGui.QGridLayout()
		self.pw0 = pg.PlotWidget(name="Plot0")  ## giving the plots names allows us to link their axes together
		vcan.addWidget(self.pw0,0,0)
		self.pw1 = pg.PlotWidget(name="Plot1")
		vcan.addWidget(self.pw1,0,1)
		self.pw2 = pg.PlotWidget(name="Plot2")  ## giving the plots names allows us to link their axes together
		vcan.addWidget(self.pw2,0,2)
		self.pw3 = pg.PlotWidget(name="Plot3")
		vcan.addWidget(self.pw3,1,0)
		self.pw4 = pg.PlotWidget(name="Plot4")  ## giving the plots names allows us to link their axes together
		vcan.addWidget(self.pw4,1,1)
		self.pw5 = pg.PlotWidget(name="Plot5")
		vcan.addWidget(self.pw5,1,2)
		

		# SET ALL VERTICAL COLUMNS TOGETHER
		hbox = QtGui.QHBoxLayout()
		hbox.addLayout(v4,1)
		hbox.addLayout(vcan,4)
		self.setLayout(hbox) 
		
    ##############################################
    # PLOT 1 settings
		# create plot and add it to the figure canvas		
		self.p0 = self.pw1.plotItem
		self.curve1=self.p0.plot()
		# create plot and add it to the figure
		self.p0vb = pg.ViewBox()
		self.curve5=pg.PlotCurveItem(pen=None)
		self.p0vb.addItem(self.curve5)
		# connect respective axes to the plot 
		self.p0.showAxis('right')
		self.p0.getAxis('right').setLabel("10-bit Arduino output")
		self.p0.scene().addItem(self.p0vb)
		self.p0.getAxis('right').linkToView(self.p0vb)
		self.p0vb.setXLink(self.p0)
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw1.setDownsampling(mode='peak')
		self.pw1.setClipToView(True)
		
		# PLOT 2 settings
		# create plot and add it to the figure canvas
		self.p1 = self.pw2.plotItem
		self.curve2=self.p1.plot(pen='r')
		self.curve3=self.p1.plot()
		# create plot and add it to the figure
		self.p2 = pg.ViewBox()
		self.curve4=pg.PlotCurveItem(pen='y')
		self.p2.addItem(self.curve4)
		# connect respective axes to the plot 
		self.p1.showAxis('right')
		self.p1.getAxis('right').setLabel("Wavelength", units='nm', color='yellow')
		self.p1.scene().addItem(self.p2)
		self.p1.getAxis('right').linkToView(self.p2)
		self.p2.setXLink(self.p1)
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw2.setDownsampling(mode='peak')
		self.pw2.setClipToView(True)
		
		# Initialize and set titles and axis names for both plots
		#self.clear_vars_graphs()
		###############################################################################
		
		# send status info which button has been pressed
		self.saveButton.clicked.connect(self.buttonClicked)
		self.runButton.clicked.connect(self.buttonClicked)
		self.cancelButton.clicked.connect(self.buttonClicked)
		self.saveplotsButton.clicked.connect(self.buttonClicked)
		#self.elapsedtimeButton.clicked.connect(self.buttonClicked)
		
		# reacts to choises picked in the menu
		self.combo1.activated[str].connect(self.onActivated)
		
		# save all paramter data in the config file
		self.saveButton.clicked.connect(self.set_save)
		self.saveButton.clicked.connect(self.set_elapsedtime_text)
	
		# run the main script
		self.runButton.clicked.connect(self.set_run)
		
		# save the plotted data
		self.saveplotsButton.clicked.connect(self.save_plots)
		
		# cancel the script run
		self.cancelButton.clicked.connect(self.set_cancel)
		
		self.setGeometry(100, 100, 1500, 1000)
		self.setWindowTitle('Photospetrometry data analyzer')
		self.show()
			
	def allEditFields(self,trueorfalse):
				
		self.startEdit.setEnabled(trueorfalse)
		self.stopEdit.setEnabled(trueorfalse)
		self.stepEdit.setEnabled(trueorfalse)
		self.dwelltimeEdit.setEnabled(trueorfalse)
		self.dwelltimeEdit_ard.setEnabled(trueorfalse)
		self.combo1.setEnabled(trueorfalse)
		self.combo2.setEnabled(trueorfalse)
		self.combo3.setEnabled(trueorfalse)
		self.expandEdit.setEnabled(trueorfalse)
		self.offsetEdit.setEnabled(trueorfalse)
		self.sensEdit.setEnabled(trueorfalse)
		self.unitEdit.setEnabled(trueorfalse)
		self.filenameEdit.setEnabled(trueorfalse)
		self.folderEdit.setEnabled(trueorfalse)
		self.cm110portEdit.setEnabled(trueorfalse)
		self.ardportEdit.setEnabled(trueorfalse)
	
	def check_dwelltime(self):
		
		dwelltimerat=(self.dwell_time_str*1000)/self.dwell_time_ard_str
		if dwelltimerat<=10:
			grade=", VERY LOW"
			self.dwelltime_ratio.setStyleSheet("color: red")
		elif dwelltimerat<=20:
			grade=", LOW"
			self.dwelltime_ratio.setStyleSheet("color: red")
		elif dwelltimerat>=100:
			grade=", VERY GOOD"
			self.dwelltime_ratio.setStyleSheet("color: green")
		elif dwelltimerat>=50:
			grade=", GOOD"
			self.dwelltime_ratio.setStyleSheet("color: green")
		else:
			grade=", OK"
			self.dwelltime_ratio.setStyleSheet("color: magenta")	
		self.dwelltime_ratio.setText(''.join(["Dwell time ratio is ",str(dwelltimerat),grade]))
		self.dwelltime_ratio.adjustSize()
		
	def buttonClicked(self):
  
		sender = self.sender()
		if sender.text()=="Run":
			self.status_str.setText("Run the scan...")
		if sender.text()=="Save":
			self.status_str.setText("Current settings saved")
		if sender.text()=="Save plots":
			self.status_str.setText("Plots saved to png files")
		if sender.text()=="Cancel":
			self.status_str.setText("Cancel the run...")
			
		self.status_str.adjustSize()
		#self.statusBar().showMessage(sender.text() + ' was pressed')
	
	def set_elapsedtime_text(self):
		
		self.lcd.display(self.timestr)
		#self.elapsedtime_str.setText(self.timestr)
		#self.elapsedtime_str.adjustSize()
		
	def onActivated(self, text):
		
		self.avg_pts = str(text)
	
	def onActivated1(self, text):
		
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
	
	def onActivated2(self, text):

		if str(text)==".5k points":
			self.schroll_wl=500
		elif str(text)=="1k points":
			self.schroll_wl=1000
		elif str(text)=="2k points":
			self.schroll_wl=2000
		elif str(text)=="5k points":
			self.schroll_wl=5000
		elif str(text)=="10k points":
			self.schroll_wl=10000
		else:
			pass
	
	def set_save(self):
		
		self.allEditFields(True)
		self.saveButton.setEnabled(True)
		self.cancelButton.setEnabled(False)
		self.runButton.setEnabled(True)
		self.saveplotsButton.setEnabled(True)
		#self.elapsedtimeButton.setEnabled(False)
		
		'''
		# replace all occurrences of 'sit' with 'SIT' and insert a line after the 5th
		for i, line in enumerate(fileinput.input(my_file_config, inplace=1)):
			if i==28: 
				sys.stdout.write(line.replace('start', 'START'))
		'''
		
		self.timestr=time.strftime("%Y%m%d-%H%M%S")
		with open("config_file.py", 'w') as thefile:
			thefile.write( ''.join(["Start=",str(self.startEdit.text()),"\n"]) )
			thefile.write( ''.join(["Stop=",str(self.stopEdit.text()),"\n"]) )
			thefile.write( ''.join(["Step=",str(self.stepEdit.text()),"\n"]) )
			thefile.write( ''.join(["Wait_time=",str(self.dwelltimeEdit.text()),"\n"]) )
			thefile.write( ''.join(["Wait_time_ard=",str(self.dwelltimeEdit_ard.text()),"\n"]) )
			thefile.write( ''.join(["Avg_pts=",str(self.avg_pts),"\n"]) )
			thefile.write( ''.join(["Expand=",str(self.expandEdit.text()),"\n"]) )
			thefile.write( ''.join(["Offset=",str(self.offsetEdit.text()),"\n"]) )
			thefile.write( ''.join(["Sensitivity=",str(self.sensEdit.text()),"\n"]) )
			thefile.write( ''.join(["Sens_unit=\"",str(self.unitEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["filename=\"",str(self.filenameEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["create_folder=\"",str(self.folderEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["timestr=\"",self.timestr,"\"\n"]) )
			thefile.write( ''.join(["analogref=",str(self.analogref_num),"\n"]) )
			thefile.write( ''.join(["cm110port=\"",str(self.cm110portEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["ardport=\"",str(self.ardportEdit.text()),"\"\n"]) )
		
		reload(config_CM110)
		self.step_str = config_file.Step
		self.dwell_time_str = config_file.Wait_time
		self.dwell_time_ard_str = config_file.Wait_time_ard
		self.avg_pts = config_file.Avg_pts
		self.unit_str = config_file.Sens_unit
		self.filename_str=config_file.filename
		self.data_out=config_file.create_folder
		self.timestr=config_file.timestr
		
		# For SAVING data and graphs
		if self.filename_str:
			self.full_filename=''.join([self.filename_str,self.timestr])
			self.full_filename_time=''.join([self.filename_str,"elapsedtime_",self.timestr])
		else:
			self.full_filename=''.join(["data_",self.timestr])
			self.full_filename_time=''.join(["data_elapsedtime_",self.timestr])
			
		if self.data_out:
			self.saveinfolder=''.join([self.data_out,"/"])
			if not os.path.isdir(self.data_out):
				os.mkdir(self.data_out)
		else:
			self.saveinfolder=""
		
		self.check_dwelltime()
		
	def set_run(self):
		
		self.get_thread = runCM110()
		self.clear_vars_graphs()
		
		self.connect(self.get_thread, SIGNAL("make_update3(QString)"), self.make_update3)
		
		self.connect(self.get_thread, SIGNAL('make_update1(QString,QString,QString,QString)'), self.make_update1)
		#timer = QtCore.QTimer()
		#timer.timeout.connect(self.make_update1)
		#timer.start(100)
		
		self.connect(self.get_thread, SIGNAL('make_update2(QString,QString,QString)'), self.make_update2)
		#timer = QtCore.QTimer()
		#timer.timeout.connect(self.make_update2)
		#timer.start(100)
		
		self.connect(self.get_thread, SIGNAL('finished()'), self.set_finished)

		self.get_thread.start()
		
		self.allEditFields(False)
		self.saveButton.setEnabled(False)
		self.cancelButton.setEnabled(True)
		self.runButton.setEnabled(False)
		self.saveplotsButton.setEnabled(False)
		#self.elapsedtimeButton.setEnabled(False)
				
		self.cancelButton.clicked.connect(self.get_thread.terminate)
		
	def make_update1(self,all_positions,endpoint_data,endpoints_times,raw_data):
    
		self.all_wl.extend([ int(all_positions) ])
		self.all_volts.extend([ float(endpoint_data)  ])	
		self.all_times.extend([ float(endpoints_times) ])
		self.all_raw.extend([ int(raw_data) ])
		
		if len(self.all_wl)>self.schroll_wl:
			self.plot_volts[:-1] = self.plot_volts[1:]  # shift data in the array one sample left
			self.plot_volts[-1] = float(endpoint_data)
			self.plot_wl[:-1] = self.plot_wl[1:]  # shift data in the array one sample left
			self.plot_wl[-1] = float(all_positions)
			self.plot_raw[:-1] = self.plot_raw[1:]  # shift data in the array one sample left
			self.plot_raw[-1] = int(raw_data)
		else:
			self.plot_wl.extend([ int(all_positions) ])
			self.plot_volts.extend([ float(endpoint_data)  ])
			self.plot_raw.extend([ int(raw_data)  ])
		self.curve1.setData(self.plot_wl, self.plot_volts)
		self.curve5.setData(self.plot_wl, self.plot_raw)
		
		## Handle view resizing 
		def updateViews():
			## view has resized; update auxiliary views to match
			self.p0vb.setGeometry(self.p0.vb.sceneBoundingRect())
			## need to re-update linked axes since this was called
			## incorrectly while views had different shapes.
			## (probably this should be handled in ViewBox.resizeEvent)
			self.p0vb.linkedViewChanged(self.p0.vb, self.p0vb.XAxis)
		updateViews()
		self.p0.vb.sigResized.connect(updateViews)
		
		###########################################################
		# Update curve3 in different plot
		if len(self.all_wl_tr)>=self.schroll_time:
			local_times=self.all_times[-self.counter:]
			local_volts=self.all_volts[-self.counter:]
			self.curve3.setData(local_times, local_volts)
		else:
			self.curve3.setData(self.all_times, self.all_volts)
		
	def make_update2(self,all_positions,all_data,timelist):
    
		self.all_wl_tr.extend([ int(all_positions) ])
		#self.all_volts_tr.extend([ float(all_data) ])
		#self.all_time_tr.extend([ float(timelist) ])
				
		if len(self.all_wl_tr)==self.schroll_time:
			self.counter=len(self.all_wl)

		if len(self.all_wl_tr)>self.schroll_time:
			self.plot_time_tr[:-1] = self.plot_time_tr[1:]  # shift data in the array one sample left
			self.plot_time_tr[-1] = float(timelist)
			self.plot_volts_tr[:-1] = self.plot_volts_tr[1:]  # shift data in the array one sample left
			self.plot_volts_tr[-1] = float(all_data)
			self.plot_wl_tr[:-1] = self.plot_wl_tr[1:]  # shift data in the array one sample left
			self.plot_wl_tr[-1] = int(all_positions)
		else:
			self.plot_wl_tr.extend([ int(all_positions) ])
			self.plot_volts_tr.extend([ float(all_data) ])
			self.plot_time_tr.extend([ float(timelist) ])

		## Handle view resizing 
		def updateViews():
			## view has resized; update auxiliary views to match
			self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
			#p3.setGeometry(p1.vb.sceneBoundingRect())

			## need to re-update linked axes since this was called
			## incorrectly while views had different shapes.
			## (probably this should be handled in ViewBox.resizeEvent)
			self.p2.linkedViewChanged(self.p1.vb, self.p2.XAxis)
			#p3.linkedViewChanged(p1.vb, p3.XAxis)
			
		updateViews()
		self.p1.vb.sigResized.connect(updateViews)
		self.curve2.setData(self.plot_time_tr, self.plot_volts_tr)
		self.curve4.setData(self.plot_time_tr, self.plot_wl_tr)
	
	def make_update3(self,info_string):
		
		self.status_str.setText(info_string)
		self.status_str.adjustSize()
	
	def set_cancel(self):
		
		#self.connect(self.get_thread, SIGNAL("make_update(QString)"), self.make_update)
		
		self.allEditFields(True)
		self.saveButton.setEnabled(True)
		self.cancelButton.setEnabled(False)
		self.runButton.setEnabled(True)
		self.saveplotsButton.setEnabled(True)
		#self.elapsedtimeButton.setEnabled(True)
	
	def clear_vars_graphs(self):
		# PLOT 1 initial canvas settings
		self.all_wl=[]
		self.all_volts=[]
		self.all_times=[]
		self.all_raw=[]
		self.plot_wl=[]
		self.plot_volts=[]
		self.plot_times=[]
		self.plot_raw=[]
		self.curve1.setData(self.plot_wl, self.plot_volts)
		self.curve5.setData(self.plot_wl, self.plot_raw)
		self.curve3.setData(self.plot_times, self.plot_volts)
		self.pw1.enableAutoRange()
		# Labels and titels are placed here since they change dynamically
		self.pw1.setTitle(''.join(["CM110 wl. step ",str(self.step_str),"nm, ","Avg.pts. ",str(self.avg_pts)]))
		self.pw1.setLabel('left', "Lock-in voltage", units=self.unit_str)
		self.pw1.setLabel('bottom', "Wavelength", units='nm')
		
		# PLOT 2 initial canvas settings
		self.all_wl_tr=[]
		#self.all_volts_tr=[]
		#self.all_time_tr=[]
		self.plot_wl_tr=[]
		self.plot_volts_tr=[]
		self.plot_time_tr=[]
		self.curve2.setData(self.plot_time_tr, self.plot_volts_tr)
		self.curve4.setData(self.plot_time_tr, self.plot_wl_tr)
		self.pw2.enableAutoRange()
		# Labels and titels are placed here since they change dynamically
		self.p1.setTitle(''.join(["CM110 dwell time ",str(self.dwell_time_str),"s, ","Avg.pts. ",str(self.avg_pts)]))
		self.p1.setLabel('left', "Lock-in voltage", units=self.unit_str, color='red')
		self.p1.setLabel('bottom', "Elapsed time", units='s')
		
	def set_finished(self):
		
		self.get_thread.close()	
		self.status_str.setText("Finished! Change settings, save and run")	
		self.status_str.adjustSize()
		
		self.allEditFields(True)
		self.saveButton.setEnabled(True)
		self.cancelButton.setEnabled(False)
		self.runButton.setEnabled(True)
		self.saveplotsButton.setEnabled(True)
		#self.elapsedtimeButton.setEnabled(True)
	
	def save_plots(self):
		
		save_plot1=''.join([self.saveinfolder,self.full_filename,'.png'])	
		save_plot2=''.join([self.saveinfolder,self.full_filename_time,'.png'])	

		# create an exporter instance, as an argument give it
		# the item you wish to export
		exporter = pg.exporters.ImageExporter(self.pw1.plotItem)
		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_plot1)
		
		exporter = pg.exporters.ImageExporter(self.pw2.plotItem)
		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_plot2)
		
#########################################
#########################################
#########################################

def main():
	
	app = QtGui.QApplication(sys.argv)
	ex = PSM_GUI()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()