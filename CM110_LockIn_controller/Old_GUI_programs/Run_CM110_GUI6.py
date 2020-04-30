import os, sys, serial, time
import numpy as np
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.exporters
#from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, SIGNAL
import config_Run_CM110

# following if-else statement is not necessary
if len(sys.argv)>1:
	raise ValueError("The function takes exactly 1 input argument!")
elif len(sys.argv)==1:
	pass

class runCM110(QThread):
	
	def __init__(self, sender,numofintervals,
			start,stop,step,dwell_time,dwell_time_ard,
			avg_pts,expand,offset,sens,unit_str, 
			filename_str,folder_str,timestr,analogref,
			cm110port_str,ardport_str):
		QThread.__init__(self)
		
		# constants	
		self.sender=sender	
		self.numofintervals = numofintervals
		self.start_ = start
		self.stop = stop
		self.step = step
		self.dwell_time = dwell_time
		self.dwell_time_ard = dwell_time_ard
		self.avg_pts = avg_pts
		self.expand = expand
		self.offset = offset
		self.sens = sens
		self.unit_str = unit_str
		self.filename_str = filename_str
		self.folder_str = folder_str
		self.timestr = timestr
		self.analogRef = analogref		
		self.cm110port_str = cm110port_str
		self.ardport_str = ardport_str
		
		if self.filename_str:
			self.string_filename=''.join([self.filename_str,self.timestr])
			self.string_elapsedtime=''.join([self.filename_str,"elapsedtime_",self.timestr])
		else:
			self.string_filename=''.join(["data_",self.timestr])
			self.string_elapsedtime=''.join(["data_elapsedtime_",self.timestr])
			
		if self.folder_str:
			self.saveinfolder=''.join([self.folder_str,"/"])
		else:
			self.saveinfolder=""

		#Initialize CM110 serial port
		self.ser_CM = serial.Serial(self.cm110port_str, 9600)
		time.sleep(0.2)
		
		#Initialize Arduino serial port and toggle DTR to reset Arduino
		self.ser_ARD = serial.Serial(self.ardport_str, 9600)
		time.sleep(0.2)

	def __del__(self):
		self.wait()
	
	def run(self):
		
		if self.sender=='Run':
	
			for start,stop,step,dwell in zip(self.start_,self.stop,self.step,self.dwell_time):
				if isinstance(start, float):
					raise ValueError("Monochromator start accepts integers only!")
				if self.start_<0 and self.start_>9000:
					raise ValueError("Minimum start wavelength is 0 nm and maximum 9000 nm.")
				if isinstance(stop, float):
					raise ValueError("Monochromator stop accepts integers only!")
				if self.stop<0 and self.stop>9000:
					raise ValueError("Minimum start wavelength is 0 nm and maximum 9000 nm.")
				if isinstance(step, float):
					raise ValueError("Monochromator step accepts integers only!")
				if dwell<1 or dwell>100:
					raise ValueError("CM110 dwell time is minimum 1 s and maximum 100 s!")
			
			if self.dwell_time_ard<10 or self.dwell_time_ard>self.dwell_time*1000:
				raise ValueError("Arduino dwell time is minimum 10 ms and maximum CM110 dwell time!")
			if isinstance(self.avg_pts, float):
				raise ValueError("Averaging only possibly using integers!")
			if self.avg_pts==0 or self.avg_pts>100:
				raise ValueError("The number of averaging points is minimum 1 and maximum 100")
			if self.offset<0 or self.offset>1:
				raise ValueError("Offset is a percentage value between 0 and 1!")
			if isinstance(self.expand, float):
				raise ValueError("Expand is required to be an integer")
			if self.expand<1 or self.expand>256:
				raise ValueError("Expand is an integer from 1 to 256!")
			if isinstance(self.sens, float):
				raise ValueError("Sensitivity is an integer!")
			if isinstance(self.unit_str, int) or isinstance(self.unit_str, float):
				raise ValueError("Sensitivity unit is a string!")
			
			self.my_file=''.join([self.saveinfolder,self.string_filename,".txt"])	
			open(self.my_file, 'w').close()
			
			self.elapsedtime_plot=''.join([self.saveinfolder,self.string_elapsedtime,".txt"])	
			open(self.elapsedtime_plot, 'w').close()
			
			#Initialize CM110 serial port
			print "Initialize CM110 serial port:", self.cm110port_str
			#self.ser_CM = serial.Serial(self.cm110port_str, 9600)
			#time.sleep(0.2)
			
			#Initialize Arduino serial port and toggle DTR to reset Arduino
			print "Initialize Arduino and set serial port:", self.ardport_str
			#self.ser_ARD = serial.Serial(self.ardport_str, 9600)
			#time.sleep(0.2)
			self.ser_ARD.setDTR(False)
			time.sleep(1)
			self.ser_ARD.flushInput()
			self.ser_ARD.setDTR(True)
			time.sleep(1.5)
			
			#UNITS
			self.emit(SIGNAL('make_update3(QString)'),"set units and reposition CM110...")
			self.ser_CM.write([chr(tal) for tal in [50,01] ]) #01 set units to nm
			print "...setting units to nm"
			time.sleep(5)
			
			#GOTO to the very start of the scan                         		
			#calculate condition parameters suitable for byte operation
			multiplicator=self.start_[0]/256 #highbyte, 0 for numbers below 256
			runtohere=self.start_[0]-256*multiplicator 
			#send the parameters to the CM110 monochromator
			self.ser_CM.write([chr(tal) for tal in [16,multiplicator,runtohere] ])
			print "...positioning scanner to the wavelength", self.start_[0], "nm"
			time.sleep(5)
			
			############################################################
			# Check input if a number, ie. digits or fractions such as 3.141
			# Source: http://www.pythoncentral.io/how-to-check-if-a-string-is-a-number-in-python-including-unicode/
			def is_number(s):
				try:
					float(s)
					return True
				except ValueError:
					pass

				try:
					import unicodedata
					unicodedata.numeric(s)
					return True
				except (TypeError, ValueError):
					pass

				return False
			####################################################################################

			#make a heading for the datafile with only last Arduino output for each wavelength
			with open(self.my_file, 'a') as thefile:
				thefile.write(''.join([ "Wavelength[nm], Lock-in voltage[", self.unit_str, "], Raw data[0..1023 steps], ", "Timetrace [sec]\n"]))

			#make a heading for the datafile with all the Arduino outputs
			with open(self.elapsedtime_plot, 'a') as thefile:
				thefile.write(''.join([ "Wavelength[nm], Lock-in voltage[", self.unit_str, "], Raw data[0..1023 steps], ", "Timetrace [sec]\n"]))
				
			###########################################
			print "The current monochromator position is:"
			time_start=time.time()
			
			for start,stop,step,dwell in zip(self.start_,self.stop,self.step,self.dwell_time):
				if stop==self.stop[-1]:
					wv_scanlist=range(start,stop+step,step)
				else:
					wv_scanlist=range(start,stop,step)
			
				#STEPSIZE
				self.ser_CM.write([chr(tal) for tal in [55,step] ]) #call STEP and set setepsize
				
				#Calculate dwelltime ratio
				dwelltimerat=int((dwell*1000)/self.dwell_time_ard)
						
				for new_position in wv_scanlist:
					self.emit(SIGNAL('make_update3(QString)'),"sweep the CM110...")
					# do not step the monochromator first time you enter then while loop
					print new_position, "nm"
					# WAITING time until the voltage is read from the serial
					for ii in range(dwelltimerat):
						time_ard_start=time.time()
						time_elap=time_ard_start-time_start
						# Send averaging points to the Arduino serial by
						# passing the number 43 (+ in ascii) and then averaging points 
						self.ser_ARD.write([chr(tal) for tal in [43,self.avg_pts]])
						# Read voltage data from the serial
						line = self.ser_ARD.readline()
						# first read voltage (bit no.) from the serial 
						if(len(line.split())==1): # expected no. of columns from Arduino
							for val in line.split():
								if is_number(val) and int(val)<2**10:
									Vout=self.analogRef*float(val)/(2**10-1)
									Vlockin=(self.offset+Vout/(self.expand*10))*self.sens
									with open(self.elapsedtime_plot, 'a') as thefile:
										thefile.write("%s" % new_position)
										thefile.write("\t%s" % Vlockin)
										thefile.write("\t%s" % val)
										thefile.write("\t%s\n" % time_elap)
										
									self.emit(SIGNAL('make_update2(QString,QString,QString)'),str(new_position),str(Vlockin),str(time_elap))
						# wait until self.dwell_time_ard, then go back and get a new value
						while (time.time()-time_ard_start)<self.dwell_time_ard/1000.0:
							pass
							
					#give a warning if the last entry voltage is hitting 1023 
					#if int(val)==2**10-1:
					#	print "warning...possible voltage overload!"

					# Save stepped wavelengths and voltage data in a textfile
					self.emit(SIGNAL('make_update1(QString,QString,QString,QString)'),str(new_position),str(Vlockin),str(time_elap),str(val))
					with open(self.my_file, 'a') as thefile:
						thefile.write("%s " % new_position)
						thefile.write("\t%s" % Vlockin)
						thefile.write("\t%s" % val)
						thefile.write("\t%s\n" % time_elap)
						
					# Do STEP
					self.ser_CM.write(chr(54))
		
	# close serial and clean up
	def close(self):
		# close serial
		print "Arduino and CM110 ports flushed and closed"
		self.ser_ARD.flush()
		self.ser_ARD.close()
		
		self.ser_CM.flush()
		self.ser_CM.close() 


class CM110(QtGui.QWidget):

	def __init__(self):
		super(CM110, self).__init__()
		
		# Initial read of the config file
		self.numofintervals = config_Run_CM110.NumOfIntervals
		self.start_ = config_Run_CM110.Start
		self.stop = config_Run_CM110.Stop
		self.step = config_Run_CM110.Step
		self.dwell_time = config_Run_CM110.Wait_time
		self.dwell_time_ard = config_Run_CM110.Wait_time_ard
		self.avg_pts = config_Run_CM110.Avg_pts
		self.expand = config_Run_CM110.Expand
		self.offset = config_Run_CM110.Offset
		self.sens = config_Run_CM110.Sensitivity
		self.unit_str = config_Run_CM110.Sens_unit
		self.filename_str=config_Run_CM110.filename
		self.folder_str=config_Run_CM110.create_folder
		self.timestr=config_Run_CM110.timestr
		self.analogref=config_Run_CM110.analogref
		self.cm110port_str=config_Run_CM110.cm110port
		self.ardport_str=config_Run_CM110.ardport
		
		# For SAVING data and graphs
		if self.filename_str:
			self.full_filename=''.join([self.filename_str,self.timestr])
			self.full_filename_time=''.join([self.filename_str,"elapsedtime_",self.timestr])
		else:
			self.full_filename=''.join(["data_",self.timestr])
			self.full_filename_time=''.join(["data_elapsedtime_",self.timestr])
			
		if self.folder_str:
			self.saveinfolder=''.join([self.folder_str,"/"])
			if not os.path.isdir(self.folder_str):
				os.mkdir(self.folder_str)
		else:
			self.saveinfolder=""
			
		# Enable antialiasing for prettier plots		
		pg.setConfigOptions(antialias=True)
		self.initUI()
			
	def initUI(self): 
		
		#####################################################
		lbl1 = QtGui.QLabel("MONOCHROMATOR CM110 settings:", self)
		lbl1.setStyleSheet("color: blue")	
		intervals_lbl = QtGui.QLabel("Number of intervals", self)
		self.combo4 = QtGui.QComboBox(self)
		mylist4=["1","2","3","4"]
		self.combo4.addItems(mylist4)
		self.combo4.setCurrentIndex(mylist4.index(str(self.numofintervals)))
		start_lbl = QtGui.QLabel("Start[nm]",self)
		stop_lbl = QtGui.QLabel("Stop[nm]",self)
		step_lbl = QtGui.QLabel("Step[nm]",self)
		dwelltime = QtGui.QLabel("Dwell[s]",self)
		cm110port = QtGui.QLabel("CM110 serial port",self)
		self.cm110portEdit = QtGui.QLineEdit(str(self.cm110port_str),self)
		self.startEdit = [QtGui.QLineEdit("",self) for tal in range(4)]
		self.stopEdit = [QtGui.QLineEdit("",self) for tal in range(4)]
		self.stepEdit = [QtGui.QLineEdit("",self) for tal in range(4)]
		self.dwelltimeEdit = [QtGui.QLineEdit("",self) for tal in range(4)]
		# disable those fields that will be ignored anyway
		for tal in range(4):
			if tal<self.numofintervals:
				self.startEdit[tal].setText(str(self.start_[tal]))
				self.stopEdit[tal].setText(str(self.stop[tal]))
				self.stepEdit[tal].setText(str(self.step[tal]))
				self.dwelltimeEdit[tal].setText(str(self.dwell_time[tal]))
			else:
				self.startEdit[tal].setEnabled(False)
				self.stopEdit[tal].setEnabled(False)
				self.stepEdit[tal].setEnabled(False)
				self.dwelltimeEdit[tal].setEnabled(False)
		
		lbl2 = QtGui.QLabel("ARDUINO Mega2560 settings:", self)
		lbl2.setStyleSheet("color: blue")
		dwelltime_ard = QtGui.QLabel("Dwell time [ms]",self)
		avgpts_lbl = QtGui.QLabel("Averaging points", self)
		ardport = QtGui.QLabel("Arduino serial port",self)
		self.dwelltimeEdit_ard = QtGui.QLineEdit(str(self.dwell_time_ard),self)
		self.ardportEdit = QtGui.QLineEdit(str(self.ardport_str),self)
		self.combo1 = QtGui.QComboBox(self)
		mylist=["1","5","10","20","50","100"]
		self.combo1.addItems(mylist)
		self.combo1.setCurrentIndex(mylist.index(str(self.avg_pts)))
		
		lbl3 = QtGui.QLabel("LOCK-IN amplifier settings:", self)
		lbl3.setStyleSheet("color: blue")
		expand = QtGui.QLabel("Expand, Offset",self)
		self.expandEdit = QtGui.QLineEdit(str(self.expand),self)
		self.offsetEdit = QtGui.QLineEdit(str(self.offset),self)
		sens = QtGui.QLabel("Sensitivity, Unit",self)
		self.sensEdit = QtGui.QLineEdit(str(self.sens),self)
		self.unitEdit = QtGui.QLineEdit(str(self.unit_str),self)
		
		lbl4 = QtGui.QLabel("STORAGE filename and location settings:", self)
		lbl4.setStyleSheet("color: blue")
		filename = QtGui.QLabel("File, Folder",self)
		self.filenameEdit = QtGui.QLineEdit(str(self.filename_str),self)
		self.folderEdit = QtGui.QLineEdit(str(self.folder_str),self)
		
		lbl6 = QtGui.QLabel("PLOT options:", self)
		lbl6.setStyleSheet("color: blue")
		schroll_lbl = QtGui.QLabel("Schroll elapsed time after",self)
		schroll2_lbl = QtGui.QLabel("Schroll wavelength after",self)
		self.combo2 = QtGui.QComboBox(self)
		self.combo3 = QtGui.QComboBox(self)
		mylist2=[".5k points","1k points","2k points","5k points","10k points"]
		mylist2_tal=[500, 1000, 2000, 5000, 10000]
		self.combo2.addItems(mylist2)
		self.combo3.addItems(mylist2)
		# initial combo settings
		self.combo2.setCurrentIndex(0)
		self.combo3.setCurrentIndex(0)
		self.schroll_time=mylist2_tal[0]
		self.schroll_wl=mylist2_tal[0]
		
		##############################################
		
		lbl5 = QtGui.QLabel("RECORD data and save images:", self)
		lbl5.setStyleSheet("color: blue")
		
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
		self.lcd.setNumDigits(11)
		self.lcd.display(self.timestr)
			
		##############################################
		# Add all widgets		
		g1_0 = QtGui.QGridLayout()
		g1_0.addWidget(lbl1,0,0)
		g1_1 = QtGui.QGridLayout()
		g1_1.addWidget(cm110port,0,0)
		g1_1.addWidget(self.cm110portEdit,0,1)
		g1_3 = QtGui.QGridLayout()
		g1_3.addWidget(intervals_lbl,0,0)
		g1_3.addWidget(self.combo4,0,1)
		g1_2 = QtGui.QGridLayout()
		g1_2.addWidget(start_lbl,0,0)
		g1_2.addWidget(stop_lbl,0,1)
		g1_2.addWidget(step_lbl,0,2)
		g1_2.addWidget(dwelltime,0,3)
		for tal in range(4):
			g1_2.addWidget(self.startEdit[tal],1+tal,0)
			g1_2.addWidget(self.stopEdit[tal],1+tal,1)
			g1_2.addWidget(self.stepEdit[tal],1+tal,2)
			g1_2.addWidget(self.dwelltimeEdit[tal],1+tal,3)
		v1 = QtGui.QVBoxLayout()
		v1.addLayout(g1_0)
		v1.addLayout(g1_1)
		v1.addLayout(g1_3)
		v1.addLayout(g1_2)
		
		g2_0 = QtGui.QGridLayout()
		g2_0.addWidget(lbl2,0,0)
		g2_1 = QtGui.QGridLayout()
		g2_1.addWidget(ardport,0,0)
		g2_1.addWidget(dwelltime_ard,1,0)
		g2_1.addWidget(avgpts_lbl,2,0)
		g2_1.addWidget(self.ardportEdit,0,1)
		g2_1.addWidget(self.dwelltimeEdit_ard,1,1)
		g2_1.addWidget(self.combo1,2,1)
		v2 = QtGui.QVBoxLayout()
		v2.addLayout(g2_0)
		v2.addLayout(g2_1)
		
		g3_0 = QtGui.QGridLayout()
		g3_0.addWidget(lbl3,0,0)
		g3_1 = QtGui.QGridLayout()
		g3_1.addWidget(expand,0,0)
		g3_1.addWidget(sens,1,0)
		g3_1.addWidget(self.expandEdit,0,1)
		g3_1.addWidget(self.offsetEdit,0,2)
		g3_1.addWidget(self.sensEdit,1,1)
		g3_1.addWidget(self.unitEdit,1,2)
		g3_1.minimumSize()
		v3 = QtGui.QVBoxLayout()
		v3.addLayout(g3_0)
		v3.addLayout(g3_1)
		
		g4_0 = QtGui.QGridLayout()
		g4_0.addWidget(lbl4,0,0)
		g4_1 = QtGui.QGridLayout()
		g4_1.addWidget(filename,0,0)
		g4_1.addWidget(self.filenameEdit,0,1)
		g4_1.addWidget(self.folderEdit,0,2)
		v4 = QtGui.QVBoxLayout()
		v4.addLayout(g4_0)
		v4.addLayout(g4_1)
				
		g7_0 = QtGui.QGridLayout()
		g7_0.addWidget(lbl6,0,0)
		g7_1 = QtGui.QGridLayout()
		g7_1.addWidget(schroll2_lbl,0,0)
		g7_1.addWidget(self.combo3,0,1)
		g7_1.addWidget(schroll_lbl,1,0)
		g7_1.addWidget(self.combo2,1,1)
		v7 = QtGui.QVBoxLayout()
		v7.addLayout(g7_0)
		v7.addLayout(g7_1)
		
		g5_0 = QtGui.QGridLayout()
		g5_0.addWidget(lbl5,0,0)
		g5_1 = QtGui.QGridLayout()
		g5_1.addWidget(save_str,0,0)
		g5_1.addWidget(run_str,1,0)
		g5_1.addWidget(saveplots_str,2,0)
		g5_1.addWidget(cancel_str,3,0)
		g5_1.addWidget(self.saveButton,0,1)
		g5_1.addWidget(self.runButton,1,1)
		g5_1.addWidget(self.saveplotsButton,2,1)
		g5_1.addWidget(self.cancelButton,3,1)
		v5 = QtGui.QVBoxLayout()
		v5.addLayout(g5_0)
		v5.addLayout(g5_1)
		
		g6_0 = QtGui.QGridLayout()
		g6_0.addWidget(self.status_str,1,0)
		g6_0.addWidget(self.elapsedtime_str,2,0)
		g6_1 = QtGui.QGridLayout()
		g6_1.addWidget(self.lcd,0,0)
		v6 = QtGui.QVBoxLayout()
		v6.addLayout(g6_0)
		v6.addLayout(g6_1)
		
		# add all groups from v1 to v6 in one vertical group v7
		v8 = QtGui.QVBoxLayout()
		v8.addLayout(v1,8)
		v8.addLayout(v2,4)
		v8.addLayout(v3,3)
		v8.addLayout(v4,2)
		v8.addLayout(v7,3)
		v8.addLayout(v5,5)
		v8.addLayout(v6,4)
	
		# set graph  and toolbar to a new vertical group vcan
		vcan = QtGui.QVBoxLayout()
		self.pw1 = pg.PlotWidget(name="Plot1")  ## giving the plots names allows us to link their axes together
		vcan.addWidget(self.pw1)
		self.pw2 = pg.PlotWidget(name="Plot2")
		vcan.addWidget(self.pw2)

		# SET ALL VERTICAL COLUMNS TOGETHER
		hbox = QtGui.QHBoxLayout()
		hbox.addLayout(v8,1)
		hbox.addLayout(vcan,3.75)
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
		self.clear_vars_graphs()
		###############################################################################
		
		# send status info which button has been pressed
		self.saveButton.clicked.connect(self.buttonClicked)
		self.runButton.clicked.connect(self.buttonClicked)
		self.cancelButton.clicked.connect(self.buttonClicked)
		self.saveplotsButton.clicked.connect(self.buttonClicked)
		#self.elapsedtimeButton.clicked.connect(self.buttonClicked)
		
		# reacts to choises picked in the menu
		self.combo1.activated[str].connect(self.onActivated)
		self.combo2.activated[str].connect(self.onActivated1)
		self.combo3.activated[str].connect(self.onActivated2)
		self.combo4.activated[str].connect(self.onActivated4)
		
		# save all paramter data in the config file
		self.saveButton.clicked.connect(self.set_save)
		self.saveButton.clicked.connect(self.set_elapsedtime_text)
	
		# run the main script
		self.runButton.clicked.connect(self.set_run)
		
		# save the plotted data
		self.saveplotsButton.clicked.connect(self.save_plots)
		
		# cancel the script run
		self.cancelButton.clicked.connect(self.set_cancel)
		
		self.setGeometry(100, 100, 1300, 1000)
		self.setWindowTitle("Monochromator CM110 Control Box And Data Acqusition")
		self.show()
			
	def allEditFields(self,trueorfalse):
		self.combo4.setEnabled(trueorfalse)
		for tal in range(4):
			if tal<self.numofintervals:
				self.startEdit[tal].setEnabled(trueorfalse)
				self.stopEdit[tal].setEnabled(trueorfalse)
				self.stepEdit[tal].setEnabled(trueorfalse)
				self.dwelltimeEdit[tal].setEnabled(trueorfalse)
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
	
	def onActivated4(self, text):
		
		self.numofintervals = int(text)
		for tal in range(4):
			if tal<self.numofintervals:				
				self.startEdit[tal].setEnabled(True)
				self.stopEdit[tal].setEnabled(True)
				self.stepEdit[tal].setEnabled(True)
				self.dwelltimeEdit[tal].setEnabled(True)
			else:
				self.startEdit[tal].setEnabled(False)
				self.stopEdit[tal].setEnabled(False)
				self.stepEdit[tal].setEnabled(False)
				self.dwelltimeEdit[tal].setEnabled(False)
		
	def set_run(self):
		
		# Initial read of the config file		
		sender = self.sender()
		start_sc = [int(self.startEdit[ii].text()) for ii in range(self.numofintervals)]
		stop_sc = [int(self.stopEdit[ii].text()) for ii in range(self.numofintervals)]
		step_sc = [int(self.stepEdit[ii].text()) for ii in range(self.numofintervals)]
		dwelltime = [float(self.dwelltimeEdit[ii].text()) for ii in range(self.numofintervals)]
		dwell_ard = float(self.dwelltimeEdit_ard.text())
		expand = int(self.expandEdit.text())
		offset = int(self.offsetEdit.text())
		sens = int(self.sensEdit.text())
		unit = str(self.unitEdit.text())
		filename = str(self.filenameEdit.text())
		folder = str(self.folderEdit.text())
		cm110port = str(self.cm110portEdit.text())
		ardport = str(self.ardportEdit.text())
		
		self.get_thread=runCM110(sender.text(),self.numofintervals,
			start_sc,stop_sc,step_sc,dwelltime,dwell_ard,
			self.avg_pts,expand,offset,sens,unit, 
			filename,folder,self.timestr,self.analogref,cm110port,ardport)
		#self.get_thread = runCM110()
		self.clear_vars_graphs()
		
		self.connect(self.get_thread, SIGNAL("make_update3(QString)"), self.make_update3)
		self.connect(self.get_thread, SIGNAL('make_update1(QString,QString,QString,QString)'), self.make_update1)		
		self.connect(self.get_thread, SIGNAL('make_update2(QString,QString,QString)'), self.make_update2)
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
		self.pw1.setTitle(''.join(["CM110 wl. step ",str(self.step),"nm, ","Avg.pts. ",str(self.avg_pts)]))
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
		self.p1.setTitle(''.join(["CM110 dwell time ",str(self.dwell_time),"s, ","Avg.pts. ",str(self.avg_pts)]))
		self.p1.setLabel('left', "Lock-in voltage", units=self.unit_str, color='red')
		self.p1.setLabel('bottom', "Elapsed time", units='s')
	
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
		
		self.timestr=time.strftime("%Y%m%d-%H%M")
		with open("config_Run_CM110.py", 'w') as thefile:
			thefile.write( ''.join(["NumOfIntervals=",str(self.numofintervals),"\n"]) )
			thefile.write( ''.join(["Start=[",','.join([str(self.startEdit[ii].text()) for ii in range(self.numofintervals)]),"]\n"]) )
			thefile.write( ''.join(["Stop=[",','.join([str(self.stopEdit[ii].text()) for ii in range(self.numofintervals)]),"]\n"]) )
			thefile.write( ''.join(["Step=[",','.join([str(self.stepEdit[ii].text()) for ii in range(self.numofintervals)]),"]\n"]) )
			thefile.write( ''.join(["Wait_time=[",','.join([str(self.dwelltimeEdit[ii].text()) for ii in range(self.numofintervals)]),"]\n"]) )
			thefile.write( ''.join(["Wait_time_ard=",str(self.dwelltimeEdit_ard.text()),"\n"]) )
			thefile.write( ''.join(["Avg_pts=",str(self.avg_pts),"\n"]) )
			thefile.write( ''.join(["Expand=",str(self.expandEdit.text()),"\n"]) )
			thefile.write( ''.join(["Offset=",str(self.offsetEdit.text()),"\n"]) )
			thefile.write( ''.join(["Sensitivity=",str(self.sensEdit.text()),"\n"]) )
			thefile.write( ''.join(["Sens_unit=\"",str(self.unitEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["filename=\"",str(self.filenameEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["create_folder=\"",str(self.folderEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["timestr=\"",self.timestr,"\"\n"]) )
			thefile.write( ''.join(["analogref=",str(self.analogref),"\n"]) )
			thefile.write( ''.join(["cm110port=\"",str(self.cm110portEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["ardport=\"",str(self.ardportEdit.text()),"\"\n"]) )
		
		reload(config_Run_CM110)
		self.numofintervals = config_Run_CM110.NumOfIntervals
		self.start_ = config_Run_CM110.Start
		self.stop = config_Run_CM110.Stop
		self.step = config_Run_CM110.Step
		self.dwell_time = config_Run_CM110.Wait_time
		self.dwell_time_ard = config_Run_CM110.Wait_time_ard
		self.avg_pts = config_Run_CM110.Avg_pts
		self.unit_str = config_Run_CM110.Sens_unit
		self.filename_str=config_Run_CM110.filename
		self.folder_str=config_Run_CM110.create_folder
		self.timestr=config_Run_CM110.timestr
		
		# For SAVING data and graphs
		if self.filename_str:
			self.full_filename=''.join([self.filename_str,self.timestr])
			self.full_filename_time=''.join([self.filename_str,"elapsedtime_",self.timestr])
		else:
			self.full_filename=''.join(["data_",self.timestr])
			self.full_filename_time=''.join(["data_elapsedtime_",self.timestr])
			
		if self.folder_str:
			self.saveinfolder=''.join([self.folder_str,"/"])
			if not os.path.isdir(self.folder_str):
				os.mkdir(self.folder_str)
		else:
			self.saveinfolder=""	
	
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
	
	# close event for x in upper-right corner
	def closeEvent(self, event):
		reply = QtGui.QMessageBox.question(self, 'Message', "Quit now? The microstep position will be saved and the stepper will turn off the hold current!", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes:
			if not hasattr(self, 'get_thread'):
				event.accept()
			else:
				if self.get_thread.isRunning():
					QtGui.QMessageBox.warning(self, 'Message', "Run in progress. Cancel the run then quit!")
					event.ignore()
				else:
					event.accept()
		else:
		  event.ignore() 
	##########################################
	
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
	ex = CM110()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()