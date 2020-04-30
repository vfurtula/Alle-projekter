import os, sys, serial, time
import numpy
import scipy.interpolate
#from numpy.polynomial import polynomial as P
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.exporters
#from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, SIGNAL
import config_stepper, MOTORSTEP_DRIVE

class zaber_Thread(QThread):
    
	def __init__(self, *argv):
		QThread.__init__(self)
		
		self.end_flag=False
		
		self.argv=argv
		self.sender=self.argv[0]
		self.Md=self.argv[1]
		self.calib_file=self.argv[2]
    
	def __del__(self):
	  
	  self.wait()

	def abort_move(self):
		
		self.end_flag=True
		self.Md.stop_move()
		
	def run(self):
		  
		if self.sender==u'\u25b2':
			min_pos=self.Md.move_Relative(1,5)
			pos_ang=self.get_ang(min_pos)
			ard_volt=self.Md.read_analog(1,10)
			self.emit(SIGNAL('more_tals(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), min_pos, pos_ang, ard_volt)
			
		elif self.sender==u'\u25bc':
			min_pos=self.Md.move_Relative(1,-5)
			pos_ang=self.get_ang(min_pos)
			ard_volt=self.Md.read_analog(1,10)
			self.emit(SIGNAL('more_tals(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), min_pos, pos_ang, ard_volt)
			  
		elif self.sender=='Move rel':
			move_num=self.argv[3]
			min_pos=self.Md.move_Relative(1,move_num)
			pos_ang=self.get_ang(min_pos)
			ard_volt=self.Md.read_analog(1,10)
			self.emit(SIGNAL('more_tals(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), min_pos, pos_ang, ard_volt)
			
		elif self.sender=='Move abs':
			move_num=self.argv[3]
			min_pos=self.Md.move_Absolute(1,move_num)
			pos_ang=self.get_ang(min_pos)
			ard_volt=self.Md.read_analog(1,10)
			self.emit(SIGNAL('more_tals(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), min_pos, pos_ang, ard_volt)
			  
		elif self.sender=='Move to ang':
			move_num=self.argv[3]
			position=self.get_pos(move_num)
			min_pos=self.Md.move_Absolute(1,position)
			pos_ang=self.get_ang(min_pos)
			ard_volt=self.Md.read_analog(1,10)
			self.emit(SIGNAL('more_tals(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), min_pos, pos_ang, ard_volt)
			
		elif self.sender=='-> ang':
			alignEdit_ang=self.argv[3]
			min_pos=self.get_pos(alignEdit_ang)
			self.Md.set_pos(1,min_pos)
			ard_volt=self.Md.read_analog(1,10)
			self.emit(SIGNAL('more_tals(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), min_pos, alignEdit_ang, ard_volt)
						
		elif self.sender=='Start scan':
			# open calib file and plot
			self.start_ = self.argv[3]
			self.stop_ = self.argv[4]
			self.step_ = self.argv[5]
			self.dwell_time = self.argv[6]
			self.save_to_file = self.argv[7]
			
			# create elapsed time text file and close it
			with open(''.join([self.save_to_file[:-4],'_ElapsedTime.txt']), 'w') as thefile:
				thefile.write("Your edit line - do NOT delete this line\n")
				thefile.write("Angle [dg], Voltage [V], Elapsed time [s]\n")
			# create regular text file, make headings and close it
			with open(self.save_to_file, 'w') as thefile:
				thefile.write("Your edit line - do NOT delete this line\n")
				thefile.write("Angle [dg], Voltage [V], Elapsed time [s]\n")
			
			time_start=time.time()
			for start,stop,step,dwell in zip(self.start_,self.stop_,self.step_,self.dwell_time):
				# Be careful with numpy.arange due to floating point errors. 
				# Always multiply up to integers and then divide back afterwards.
				wv_scanlist_=numpy.arange(int(10*start),int(10*stop),int(10*step))
				wv_scanlist=wv_scanlist_/10.0
				positions = self.get_pos(wv_scanlist)
				#positions = scipy.interpolate.splev(wv_scanlist, wv_curve, der=0)
				
				for ff,pp in zip(wv_scanlist,positions):
					if self.end_flag==True:
						break
					min_pos=self.Md.move_Absolute(1,pp)
					pos_ang=self.get_ang(min_pos)
					ard_volt=self.Md.read_analog(1,10)
					self.emit(SIGNAL('more_tals(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), min_pos, pos_ang, ard_volt)	
					self.emit(SIGNAL('curve3_data(PyQt_PyObject,PyQt_PyObject)'), min_pos, pos_ang)
					
					time_s=time.time()
					while (time.time()-time_s)<dwell:
						ard_volt=self.Md.read_analog(1,10)
						time_elap=time.time()-time_start
						self.emit(SIGNAL('volt_data(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), time_elap,pos_ang,ard_volt)
						with open(''.join([self.save_to_file[:-4],'_ElapsedTime.txt']), 'a') as thefile:
							thefile.write("%s" %pos_ang)
							thefile.write("\t%s" %ard_volt)
							thefile.write("\t%s\n" %time_elap)
							
					with open(self.save_to_file, 'a') as thefile:
						thefile.write("%s" %pos_ang)
						thefile.write("\t%s" %ard_volt)
						thefile.write("\t%s\n" %time_elap)
					self.emit(SIGNAL('time_data(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), time_elap,pos_ang,ard_volt)
				
				if self.end_flag==True:
					break
		else:
		  pass
	
	def get_pos(self,ang):
		
		x=[]
		y=[]
		with open(self.calib_file, 'r') as thefile:
			for line in thefile:
				columns = line.split()
				x.extend([int(columns[0])]) #microstep pos.
				y.extend([round(float(columns[1]),1)]) #Angle
				
		if numpy.min(ang)>=min(y) and numpy.max(ang)<=max(y):
			#spline
			pos_curve=scipy.interpolate.splrep(y, x, k=3, s=0)
			#linear
			#wv_curve = scipy.interpolate.splrep(x, y, k=1, s=0)
			pos_pos = scipy.interpolate.splev(ang, pos_curve, der=0)
			nums=numpy.rint(pos_pos) # round the up/down floats
			return nums.astype(int)
		
	def get_ang(self,pos):
		
		x=[]
		y=[]
		with open(self.calib_file, 'r') as thefile:
			for line in thefile:
				columns = line.split()
				x.extend([int(columns[0])]) #microstep pos.
				y.extend([round(float(columns[1]),1)]) #Angle

		if numpy.min(pos)>=min(x) and numpy.max(pos)<=max(x):
			#spline
			wv_curve=scipy.interpolate.splrep(x, y, k=3, s=0)
			#linear
			#wv_curve = scipy.interpolate.splrep(x, y, k=1, s=0)
			pos_ang = scipy.interpolate.splev(pos, wv_curve, der=0)
			return numpy.round(pos_ang,1)
  
class run_zaber_gui(QtGui.QWidget):
  
	def __init__(self):
		super(run_zaber_gui, self).__init__()
		
		#####################################################
		# constants
		self.numofintervals=config_stepper.NumOfIntervals
		self.start = config_stepper.Start
		self.stop = config_stepper.Stop
		self.step = config_stepper.Step
		self.dwell_time = config_stepper.Wait_time
		self.calib_file_str = config_stepper.calibfile
		self.timestr = config_stepper.timestr
		self.filename_str = config_stepper.filename
		self.folder_str = config_stepper.create_folder	
		self.stepperport_str = config_stepper.stepperport
	
		self.initUI()
    
	def initUI(self):

		##############################################
		
		lbl3 = QtGui.QLabel("Scan parameters:", self)
		lbl3.setStyleSheet("color: blue")
		start_lbl = QtGui.QLabel("Start[dg]",self) 
		stop_lbl = QtGui.QLabel("Stop[dg]",self)
		step_lbl = QtGui.QLabel("Step[dg]",self)
		dwelltime = QtGui.QLabel("Dwell[s]",self)
		self.startEdit = [QtGui.QLineEdit("",self) for tal in range(3)]
		self.stopEdit = [QtGui.QLineEdit("",self) for tal in range(3)]
		self.stepEdit = [QtGui.QLineEdit("",self) for tal in range(3)]
		self.dwelltimeEdit = [QtGui.QLineEdit("",self) for tal in range(3)]
		self.startscanButton = QtGui.QPushButton('Start scan',self)
		self.cancelscanButton = QtGui.QPushButton('Cancel scan',self)
		self.cancelscanButton.setEnabled(False)
		# disable those fields that will be ignored anyway
		for tal in range(3):
			if tal<self.numofintervals:
				self.startEdit[tal].setText(str(self.start[tal]))
				self.stopEdit[tal].setText(str(self.stop[tal]))
				self.stepEdit[tal].setText(str(self.step[tal]))
				self.dwelltimeEdit[tal].setText(str(self.dwell_time[tal]))
			else:
				self.startEdit[tal].setEnabled(False)
				self.stopEdit[tal].setEnabled(False)
				self.stepEdit[tal].setEnabled(False)
				self.dwelltimeEdit[tal].setEnabled(False)
		
		##############################################
		
		lbl4 = QtGui.QLabel("STORAGE filename and location settings:", self)
		lbl4.setStyleSheet("color: blue")
		filename = QtGui.QLabel("Save to file",self)
		foldername = QtGui.QLabel("Save to folder",self)
		self.filenameEdit = QtGui.QLineEdit(self.filename_str,self)
		self.folderEdit = QtGui.QLineEdit(self.folder_str,self)
		
		##############################################

		# status info which button has been pressed
		self.motorstep_lbl = QtGui.QLabel("Stepper postion:", self)
		self.motorstep_lbl.setStyleSheet("color: blue")
		self.upButton = QtGui.QPushButton(u'\u25b2',self)
		self.set_bstyle_v1(self.upButton)
		self.downButton = QtGui.QPushButton(u'\u25bc',self)
		self.set_bstyle_v1(self.downButton)
		self.moverelButton = QtGui.QPushButton('Move rel',self)
		self.moveabsButton = QtGui.QPushButton('Move abs',self)
		#self.moveabsButton.setStyleSheet('QPushButton {color: red}')
		self.moverelEdit = QtGui.QLineEdit(str(100),self)
		self.moveabsEdit = QtGui.QLineEdit(str(10000),self)
		self.movewlButton = QtGui.QPushButton('Move to ang',self)
		self.movewlButton.setStyleSheet('QPushButton {color: magenta}')
		self.movewlEdit = QtGui.QLineEdit("",self)
		self.stopButton = QtGui.QPushButton('STOP MOVE',self)
		self.stopButton.setEnabled(False)	
		
		##############################################

		self.lcd = QtGui.QLCDNumber(self)
		self.lcd.setStyleSheet("color: black")
		self.lcd.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd.setNumDigits(6)
		self.lcd.display('------')
		
		self.lcd2 = QtGui.QLCDNumber(self)
		self.lcd2.setStyleSheet("color: magenta")
		self.lcd2.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd2.setNumDigits(6)
		self.lcd2.display('------')
		#self.lcd2.setFixedWidth(120)

		self.lcd3 = QtGui.QLCDNumber(self)
		self.lcd3.setStyleSheet("color: red")
		self.set_lcd3_style(self.lcd3)
		self.lcd3.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd3.setNumDigits(11)
		self.lcd3.display(self.timestr)
		self.lcd3.setFixedWidth(280)
		##############################################

		# status info which button has been pressed
		self.zeiss_lbl = QtGui.QLabel("Alignment:", self)
		self.zeiss_lbl.setStyleSheet("color: blue")
		self.alignEdit = QtGui.QLineEdit("",self)
		self.setzeroButton = QtGui.QPushButton('-> ang',self)
		self.setzeroButton.setStyleSheet('QPushButton {color: magenta}')
		self.setzeroButton.setFixedWidth(70)
		#self.setzeroButton.setStyleSheet('QPushButton {color: black}')
		
		##############################################
		
		self.timetrace_str = QtGui.QLabel("TIME trace for storing plots and data:", self)
		self.timetrace_str.setStyleSheet("color: blue")	

		################### MENU BARS START ##################
		
		MyBar = QtGui.QMenuBar(self)
		fileMenu = MyBar.addMenu("File")
		fileSaveSet = fileMenu.addAction("Save settings")
		fileSaveSet.triggered.connect(self.set_save)
		fileSaveSet.triggered.connect(self.set_elapsedtime_text)
		fileSaveSet.setShortcut('Ctrl+S')
		fileSavePlt = fileMenu.addAction("Save plots")
		fileSavePlt.triggered.connect(self.set_save_plots)
		fileSavePlt.setShortcut('Ctrl+P')
		self.fileClose = fileMenu.addAction("Close")        
		self.fileClose.triggered.connect(self.close) # triggers closeEvent()
		self.fileClose.setShortcut('Ctrl+X')
		
		modeMenu = MyBar.addMenu("Mode")
		self.conMode = modeMenu.addAction("Connect to serial")
		self.conMode.triggered.connect(self.set_connect)
		self.disconMode = modeMenu.addAction("Disconnect from serial")
		self.disconMode.triggered.connect(self.set_disconnect)
		
		zeissMenu = MyBar.addMenu("Scan")
		self.zeissMode = zeissMenu.addAction("Number of intervals")
		self.zeissMode.triggered.connect(self.zeiss_intervals)
		
		serialMenu = MyBar.addMenu("Serial")
		self.serialStepper = serialMenu.addAction("Stepper driver")
		self.serialStepper.triggered.connect(self.StepperDialog)
		
		calibMenu = MyBar.addMenu("Calib")
		self.calibZeiss = calibMenu.addAction("Load calib file")
		self.calibZeiss.setShortcut('Ctrl+O')
		self.calibZeiss.triggered.connect(self.loadCalibDialog)
		self.calibZeiss.triggered.connect(self.view_calib_data)
		
		################### MENU BARS END ##################
		
		g4_0=QtGui.QGridLayout()
		g4_0.addWidget(MyBar,0,0)
		v4 = QtGui.QVBoxLayout()
		v4.addLayout(g4_0)

		g7_0 = QtGui.QGridLayout()
		g7_0.addWidget(lbl3,0,0)
		g7_1 = QtGui.QGridLayout()
		g7_1.addWidget(start_lbl,0,0)
		g7_1.addWidget(stop_lbl,0,1)
		g7_1.addWidget(step_lbl,0,2)
		g7_1.addWidget(dwelltime,0,3)
		for tal in range(3):
			g7_1.addWidget(self.startEdit[tal],1+tal,0)
			g7_1.addWidget(self.stopEdit[tal],1+tal,1)
			g7_1.addWidget(self.stepEdit[tal],1+tal,2)
			g7_1.addWidget(self.dwelltimeEdit[tal],1+tal,3)
		g7_2 = QtGui.QGridLayout()
		g7_2.addWidget(self.startscanButton,0,0)
		g7_2.addWidget(self.cancelscanButton,0,1)		
		v7 = QtGui.QVBoxLayout()
		v7.addLayout(g7_0)
		v7.addLayout(g7_1)
		v7.addLayout(g7_2)
		
		g8_0 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g8_0.addWidget(lbl4)
		g8_1 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g8_1.addWidget(filename)
		g8_1.addWidget(foldername)
		g8_2 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g8_2.addWidget(self.filenameEdit)
		g8_2.addWidget(self.folderEdit)
		g8_3 = QtGui.QSplitter(QtCore.Qt.Horizontal)
		g8_3.addWidget(g8_1)
		g8_3.addWidget(g8_2)
		v8 = QtGui.QSplitter(QtCore.Qt.Vertical)
		v8.addWidget(g8_0)
		v8.addWidget(g8_3)

		g0_0 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g0_0.addWidget(self.motorstep_lbl)
		g0_1 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g0_1.addWidget(self.upButton)
		g0_1.addWidget(self.downButton)
		g0_2 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g0_2.addWidget(self.lcd)
		h0 = QtGui.QSplitter(QtCore.Qt.Horizontal)
		h0.addWidget(g0_1)
		h0.addWidget(g0_2)
		g0_3=QtGui.QSplitter(QtCore.Qt.Vertical)
		g0_3.addWidget(self.moverelButton)
		g0_3.addWidget(self.moveabsButton)
		g0_3.addWidget(self.movewlButton)
		g0_4=QtGui.QSplitter(QtCore.Qt.Vertical)
		g0_4.addWidget(self.moverelEdit)
		g0_4.addWidget(self.moveabsEdit)
		g0_4.addWidget(self.movewlEdit)
		g0_5=QtGui.QSplitter(QtCore.Qt.Vertical)
		g0_5.addWidget(self.stopButton)
		h1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
		h1.addWidget(g0_5)
		h1.addWidget(g0_3)
		h1.addWidget(g0_4)
		v1 = QtGui.QSplitter(QtCore.Qt.Vertical)
		v1.addWidget(g0_0)
		v1.addWidget(h0)
		v1.addWidget(h1)
				
		g3_0=QtGui.QSplitter(QtCore.Qt.Vertical)
		g3_0.addWidget(self.zeiss_lbl)
		g3_1=QtGui.QSplitter(QtCore.Qt.Vertical)
		g3_1.addWidget(self.alignEdit)
		g3_1.addWidget(self.setzeroButton)
		g3_2=QtGui.QSplitter(QtCore.Qt.Horizontal)
		g3_2.addWidget(g3_1)
		g3_2.addWidget(self.lcd2)
		h4 = QtGui.QSplitter(QtCore.Qt.Vertical)
		h4.addWidget(g3_0)
		h4.addWidget(g3_2)
		
		g9_0 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g9_0.addWidget(self.timetrace_str)
		g9_0.addWidget(self.lcd3)
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		v_all = QtGui.QVBoxLayout()
		v_all.addLayout(v4)
		#v_all.addLayout(v6)
		v_all.addLayout(v7)
		v_all.addWidget(v8)
		v_all.addWidget(h4)
		v_all.addWidget(v1)
		v_all.addWidget(g9_0)
		
		# set graph  and toolbar to a new vertical group vcan
		g0_0 = QtGui.QGridLayout()
		self.pw0 = pg.PlotWidget(name="Plot1")  ## giving the plots names allows us to link their axes together
		self.pw0.setTitle('Stepper movements')
		self.pw0.setLabel('left', 'Stepper pos.')
		self.pw0.setLabel('bottom', 'no. of moves')
		g0_0.addWidget(self.pw0,0,0)
		
		self.pw1 = pg.PlotWidget(name="Plot2")  ## giving the plots names allows us to link their axes together
		self.pw1.setTitle('Scan')
		self.pw1.setLabel('bottom', 'angle')
		self.pw1.setLabel('left', "Voltage", units='V', color='yellow')
		g0_0.addWidget(self.pw1,0,1)
		
		self.pw2 = pg.PlotWidget(name="Plot3")
		self.pw2.setTitle('Calib')
		self.pw2.setLabel('left', 'angle')
		self.pw2.setLabel('bottom', 'Stepper pos.')
		g0_0.addWidget(self.pw2,1,0)
		
		self.pw3 = pg.PlotWidget(name="Plot4")
		self.pw3.setTitle('Scan')		
		self.pw3.setLabel('left', 'angle', color='red')
		self.pw3.setLabel('bottom', 'elapsed time', units='s')
		g0_0.addWidget(self.pw3,1,1)
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		h_all = QtGui.QHBoxLayout()
		h_all.addLayout(v_all)
		h_all.addLayout(g0_0)
		self.setLayout(h_all)

		########################################
		# create plot and add it to the figure canvas		
		#self.p0 = self.pw0.plotItem
		#self.curve0=self.p0.plot(pen='r')
		
		# PLOT 1 settings
		# create plot and add it to the figure canvas
		self.p0 = self.pw0.plotItem
		self.curve0=self.p0.plot(pen='r')
		# create plot and add it to the figure
		self.p0_1 = pg.ViewBox()
		self.curve7=pg.PlotCurveItem(pen='y')
		self.p0_1.addItem(self.curve7)
		# connect respective axes to the plot 
		self.p0.showAxis('right')
		self.p0.getAxis('right').setLabel("Voltage", units="V", color='yellow')
		self.p0.scene().addItem(self.p0_1)
		self.p0.getAxis('right').linkToView(self.p0_1)
		self.p0_1.setXLink(self.p0)
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw0.setDownsampling(mode='peak')
		self.pw0.setClipToView(True)
		
		# PLOT 2 settings
		self.p1 = self.pw1.plotItem		
		self.curve8=self.p1.plot(pen='w')
		
		# PLOT 3 settings
		self.p2 = self.pw2.plotItem		
		self.p2.addLegend()
		self.curve2=self.p2.plot(pen='m',name='raw data')
		self.curve1=self.p2.plot(pen='b',name='spline')
		self.curve3=self.p2.plot(pen='w',name='scan')
		
		# PLOT 4 settings
		# create plot and add it to the figure canvas
		self.p3 = self.pw3.plotItem
		self.curve4=self.p3.plot(pen='r')
		# create plot and add it to the figure
		self.p4 = pg.ViewBox()
		self.curve5=pg.PlotCurveItem(pen='y')
		self.curve6=pg.PlotCurveItem()
		self.p4.addItem(self.curve5)
		self.p4.addItem(self.curve6)
		# connect respective axes to the plot 
		self.p3.showAxis('right')
		self.p3.getAxis('right').setLabel("Voltage", units='V', color='yellow')
		self.p3.scene().addItem(self.p4)
		self.p3.getAxis('right').linkToView(self.p4)
		self.p4.setXLink(self.p3)
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw3.setDownsampling(mode='peak')
		self.pw3.setClipToView(True)
		
		#########################################

		self.disconMode.setEnabled(False)
		self.allButtons_torf(False)

		self.startscanButton.clicked.connect(self.set_scan)
		self.cancelscanButton.clicked.connect(self.move_stop)
		
		
		self.setzeroButton.clicked.connect(self.set_zero)
		#self.combo1.activated[str].connect(self.onActivated1)
		
		self.upButton.clicked.connect(self.move_jog)
		self.downButton.clicked.connect(self.move_jog)
		self.moverelButton.clicked.connect(self.move_rel)
		self.moveabsButton.clicked.connect(self.move_abs)
		self.movewlButton.clicked.connect(self.move_to_ang)
		self.stopButton.clicked.connect(self.move_stop)
		
		self.setGeometry(30,30,1200,550)
		self.setWindowTitle('Scatterometer')
		self.show()

	##########################################
	def StepperDialog(self):

		text, ok = QtGui.QInputDialog.getText(self, 'Serial Port Dialog','Enter stepper driver serial:', text=self.stepperport_str)
		if ok:
			self.stepperport_str = str(text)
	
	def loadCalibDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file','/home/vfurtula/Documents/Projects/Scatteromter/Calib_files')
		if fname:
			self.calib_file_str = str(fname)
		
	
	def zeiss_intervals(self):

		mylist2 = ["1","2","3"]
		text, ok = QtGui.QInputDialog.getItem(self, "Scan settings","Number of intervals", mylist2, mylist2.index(str(self.numofintervals)))
		if ok:
			self.onActivated2(str(text))
			
	def set_connect(self):
		
		try:
			self.Md = MOTORSTEP_DRIVE.MOTORSTEP_DRIVE(self.stepperport_str)
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message',"No response from stepper serial port! Check the port name and check the power line.")
			return None
		
		self.allButtons_torf(True)
		self.conMode.setEnabled(False)
		self.disconMode.setEnabled(True)
		self.serialStepper.setEnabled(False)	
		# constants
		max_pos=65000
		min_pos=0

		self.Md.set_minmax_pos(1,'max',max_pos)
		self.Md.set_minmax_pos(1,'min',min_pos)
		self.Md.drive_on(1)
		
		# constants
		self.Md.set_timeout(0.025)
		self.all_pos=[self.Md.get_pos(1)]
		self.lcd.display(str(self.all_pos[-1]))
		
		initial_volt = self.Md.read_analog(1,10)
		self.some_volts=[initial_volt]
		self.view_calib_data()
		
	def set_disconnect(self):

		self.Md.drive_off(1)
		self.Md.close()
		
		self.allButtons_torf(False)
		self.conMode.setEnabled(True)
		self.disconMode.setEnabled(False)
		self.serialStepper.setEnabled(True)
		
	def allButtons_torf(self,text):
		
		#self.dwelltimeEdit_ard.setEnabled(text)
		#self.combo1.setEnabled(text)
		self.zeissMode.setEnabled(text)
		self.calibZeiss.setEnabled(text)
		#self.combo2.setEnabled(text)
		for tal in range(3):
			if tal<self.numofintervals:
				self.startEdit[tal].setEnabled(text)
				self.stopEdit[tal].setEnabled(text)
				self.stepEdit[tal].setEnabled(text)
				self.dwelltimeEdit[tal].setEnabled(text)
		self.startscanButton.setEnabled(text)
		#self.cancelscanButton.setEnabled(text)
		

		self.alignEdit.setEnabled(text)
		self.setzeroButton.setEnabled(text)
		self.filenameEdit.setEnabled(text)
		self.folderEdit.setEnabled(text)
		
		self.upButton.setEnabled(text)
		self.downButton.setEnabled(text)
		self.moverelButton.setEnabled(text)
		self.moveabsButton.setEnabled(text)
		self.movewlButton.setEnabled(text)
		self.moverelEdit.setEnabled(text)
		self.moveabsEdit.setEnabled(text)
		self.movewlEdit.setEnabled(text)
		#self.stopButton.setEnabled(text)
	
	def closeEvent(self, event):
		reply = QtGui.QMessageBox.question(self, 'Message', "Quit now? The microstep position will be saved and the stepper will turn off the hold current!", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes:
			if hasattr(self, 'Md'):
				if self.conMode.isEnabled()==False:
					if not hasattr(self, 'get_zaber_Thread'):
						self.Md.drive_off(1)
						self.Md.close()
						event.accept()
					else:
						if self.get_zaber_Thread.isRunning():
							QtGui.QMessageBox.warning(self, 'Message', "Run in progress. Cancel the run then quit!")
							event.ignore()
						else:
							self.Md.drive_off(1)
							self.Md.close()
							event.accept()
				else:
					pass
			else:
				event.accept()
		else:
		  event.ignore() 
	##########################################

	def set_bstyle_v1(self,button):
		
		button.setStyleSheet('QPushButton {font-size: 25pt}')
		button.setFixedWidth(40)
		button.setFixedHeight(40)
  
	def set_lcd3_style(self,lcd):

		#lcd.setFixedWidth(40)
		lcd.setFixedHeight(60)
  
	def view_calib_data(self):
		
		try:
			x=[]
			y=[]
			with open(self.calib_file_str, 'r') as thefile:
				for line in thefile:
					columns = line.split()
					x.extend([int(columns[0])])
					y.extend([round(float(columns[1]),1)])
			
			self.min_y_calib=min(y)
			self.max_y_calib=max(y)			
			self.curve2.setData(x,[tal for tal in y])
			
			# Be careful with numpy.arange due to floating point errors. 
			# Always multiply up to integers and then divide back afterwards.			
			wv_scanlist_=numpy.arange(int(10*y[0]),int(10*(y[-1]+0.1)),int(10*0.1))
			wv_scanlist=wv_scanlist_/10.0
			#spline
			wv_curve=scipy.interpolate.splrep(y, x, k=3, s=0)
			#linear
			#wv_curve = scipy.interpolate.splrep(y, x, k=1, s=0)		
			positions = scipy.interpolate.splev(wv_scanlist, wv_curve, der=0)
			self.curve1.setData(positions,[tal for tal in wv_scanlist])
			
			if self.all_pos[-1]<min(x) or self.all_pos[-1]>max(x):
				self.lcd2.display('------')
			else:
				# Update the LCD display lcd2 with the angle which
				# corresponds to the saved stepper position
				wv_curve2=scipy.interpolate.splrep(x, y, k=3, s=0)
				first_pos_ang = scipy.interpolate.splev(self.all_pos[-1], wv_curve2, der=0)
				self.lcd2.display(str(round(first_pos_ang,1)))
					
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message', "Something is wrong with Calib file! Do you have a Calib file with 2 columns, no headers, and all inputs are digits?")
			self.lcd2.display('----')
			self.curve1.clear()
			self.curve2.clear()				
			
	def set_scan(self):
		
		if str(self.filenameEdit.text()):
			saveinfile=''.join([str(self.filenameEdit.text()),self.timestr])
			saveinfile_et=''.join([str(self.filenameEdit.text()),"elapsedtime_",self.timestr])
		else:
			saveinfile=''.join(["data_",self.timestr])
			saveinfile_et=''.join(["data_elapsedtime_",self.timestr])
			
		if str(self.folderEdit.text()):
			if not os.path.isdir(str(self.folderEdit.text())):
				os.mkdir(str(self.folderEdit.text()))
			saveinfolder=''.join([str(self.folderEdit.text()),"/"])
		else:
			saveinfolder=""
			
		save_to_file=''.join([saveinfolder,saveinfile,".txt"])	
		save_to_file_et=''.join([saveinfolder,saveinfile_et,".txt"])
		
		self.all_time=[]
		self.all_wv=[]
		self.all_volts=[]
		self.some_end_time=[]
		self.some_wv=[]
		self.some_end_volts=[]
		self.curve3_ang=[]
		self.curve3_pos=[]
		
		self.curve3.clear()
		self.curve4.clear()
		self.curve5.clear()
		self.curve6.clear()
		self.curve8.clear()
		
		start_sc = [round(float(self.startEdit[ii].text()),1) for ii in range(self.numofintervals)]
		stop_sc = [round(float(self.stopEdit[ii].text()),1) for ii in range(self.numofintervals)]
		step_sc = [round(float(self.stepEdit[ii].text()),1) for ii in range(self.numofintervals)]
		dwell_zaber = [float(self.dwelltimeEdit[ii].text()) for ii in range(self.numofintervals)]
		
		#for ff,pp in zip(wv_scanlist,positions):
		for i,j in zip(start_sc,stop_sc):
			if i<self.min_y_calib or i>self.max_y_calib or j<self.min_y_calib or j>self.max_y_calib:
				myvar=False
				break
			else:
				myvar=True
		
		if myvar==False:	
			QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid scan range is from ',str(self.min_y_calib),' deg to ',str(self.max_y_calib),' deg.' ]) )
		else:
			
			self.cancelscanButton.setEnabled(True)
			self.disconMode.setEnabled(False)
			self.fileClose.setEnabled(False)
			self.allButtons_torf(False)
			
			sender = self.sender()
			self.get_zaber_Thread=zaber_Thread(sender.text(),self.Md,self.calib_file_str,start_sc,stop_sc,step_sc,dwell_zaber,save_to_file)
			self.connect(self.get_zaber_Thread,SIGNAL("more_tals(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"),self.more_tals)
			self.connect(self.get_zaber_Thread,SIGNAL("curve3_data(PyQt_PyObject,PyQt_PyObject)"),self.curve3_data)
			self.connect(self.get_zaber_Thread,SIGNAL("time_data(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"),self.time_data)
			self.connect(self.get_zaber_Thread,SIGNAL("volt_data(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"),self.volt_data)
			self.connect(self.get_zaber_Thread,SIGNAL('finished()'), self.set_finished)
			
			self.get_zaber_Thread.start()
  
	def move_stop(self):
		
		self.get_zaber_Thread.abort_move()
		
	def set_zero(self):
		
		move_num=round(float(self.alignEdit.text()),1)
		if move_num<self.min_y_calib or move_num>self.max_y_calib:
			QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid range is from ',str(self.min_y_calib),' deg to ',str(self.max_y_calib),' deg.' ]) )
		else:
			sender = self.sender()
			get_zaber_Thread=zaber_Thread(sender.text(),self.Md,self.calib_file_str,move_num)
			self.connect(get_zaber_Thread,SIGNAL("more_tals(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"),self.more_tals)
			self.connect(get_zaber_Thread, SIGNAL('finished()'), self.set_finished)

			get_zaber_Thread.start()    
	
	def move_to_ang(self):
		
		move_num = round(float(self.movewlEdit.text()),1)
		if move_num<self.min_y_calib or move_num>self.max_y_calib:
			QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid range is from ',str(self.min_y_calib),' deg to ',str(self.max_y_calib),' deg.' ]) )
		else:
			self.stopButton.setEnabled(True)
			self.disconMode.setEnabled(False)
			self.fileClose.setEnabled(False)
			self.allButtons_torf(False)
			
			sender = self.sender()
			self.get_zaber_Thread=zaber_Thread(sender.text(),self.Md,self.calib_file_str,move_num)
			self.connect(self.get_zaber_Thread,SIGNAL("more_tals(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"),self.more_tals)
			self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
			
			self.get_zaber_Thread.start()
		
	def move_rel(self):
		
		# update the lcd motorstep position
		move_num = int(self.moverelEdit.text())
		move_tot = move_num+self.all_pos[-1]
		if move_tot<0 or move_tot>65000:
			QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid range is from ',str(0),' to ',str(65000),' microsteps.' ]) )
		else:
			self.stopButton.setEnabled(True)
			self.disconMode.setEnabled(False)
			self.fileClose.setEnabled(False)
			self.allButtons_torf(False)
			
			sender = self.sender()
			self.get_zaber_Thread=zaber_Thread(sender.text(),self.Md,self.calib_file_str,move_num)
			self.connect(self.get_zaber_Thread,SIGNAL("more_tals(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"),self.more_tals)
			self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
			
			self.get_zaber_Thread.start()
		
	def move_abs(self):
		
		# update the lcd motorstep position
		move_num = int(self.moveabsEdit.text())
		if move_num<0 or move_num>65000:
			QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid range is from ',str(0),' to ',str(65000),' microsteps.' ]) )
		else:
			self.stopButton.setEnabled(True)
			self.disconMode.setEnabled(False)
			self.fileClose.setEnabled(False)
			self.allButtons_torf(False)
			
			sender = self.sender()
			self.get_zaber_Thread=zaber_Thread(sender.text(),self.Md,self.calib_file_str,move_num)
			self.connect(self.get_zaber_Thread,SIGNAL("more_tals(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"),self.more_tals)
			self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
			    
			self.get_zaber_Thread.start()
		
	def move_jog(self):
		
		# update the lcd motorstep position
		sender = self.sender()
		self.get_zaber_Thread=zaber_Thread(sender.text(),self.Md,self.calib_file_str)
		self.connect(self.get_zaber_Thread,SIGNAL("more_tals(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"),self.more_tals)
		self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
		
		self.get_zaber_Thread.start()
	
	def set_elapsedtime_text(self):
		
		self.lcd3.display(self.timestr)
		
	def more_tals(self,pos,pos_ang,volts):
		
		self.lcd.display(str(pos))
		self.lcd2.display(str(pos_ang))
		self.some_volts.extend([ volts ])
		self.all_pos.extend([ pos ])    
		
		## Handle view resizing 
		def updateViews():
			## view has resized; update auxiliary views to match
			self.p0_1.setGeometry(self.p0.vb.sceneBoundingRect())
			#p3.setGeometry(p1.vb.sceneBoundingRect())

			## need to re-update linked axes since this was called
			## incorrectly while views had different shapes.
			## (probably this should be handled in ViewBox.resizeEvent)
			self.p0_1.linkedViewChanged(self.p0.vb, self.p0_1.XAxis)
			#p3.linkedViewChanged(p1.vb, p3.XAxis)
			
		updateViews()
		self.p0.vb.sigResized.connect(updateViews)
		self.curve0.setData(self.all_pos)
		self.curve7.setData(self.some_volts)
	
	def curve3_data(self,pos,ang):
		
		self.curve3_ang.extend([ ang ])
		self.curve3_pos.extend([ pos ])
		self.curve3.setData(self.curve3_pos,[tal for tal in self.curve3_ang])
		
	def time_data(self,time,iii,volts):
		
		self.some_end_time.extend([ time ])
		self.some_wv.extend([ iii ])
		self.some_end_volts.extend([ volts ])		
		self.curve6.setData(self.some_end_time, self.some_end_volts)
		self.curve8.setData([tal for tal in self.some_wv], self.some_end_volts)

	def volt_data(self,time,ang,volts):
		
		self.all_wv.extend([ ang ])
		self.all_volts.extend([ volts ])
		self.all_time.extend([ time ])
		
		## Handle view resizing 
		def updateViews():
			## view has resized; update auxiliary views to match
			self.p4.setGeometry(self.p3.vb.sceneBoundingRect())
			#p3.setGeometry(p1.vb.sceneBoundingRect())

			## need to re-update linked axes since this was called
			## incorrectly while views had different shapes.
			## (probably this should be handled in ViewBox.resizeEvent)
			self.p4.linkedViewChanged(self.p3.vb, self.p4.XAxis)
			#p3.linkedViewChanged(p1.vb, p3.XAxis)
			
		updateViews()
		self.p3.vb.sigResized.connect(updateViews)
		self.curve4.setData(self.all_time, [tal for tal in self.all_wv])
		self.curve5.setData(self.all_time, self.all_volts)

	def set_finished(self):
		
		self.cancelscanButton.setEnabled(False)
		self.stopButton.setEnabled(False)
		self.disconMode.setEnabled(True)
		self.fileClose.setEnabled(True)
		self.allButtons_torf(True)
	
	def onActivated2(self, text):
		
		self.numofintervals = int(text)
		for tal in range(3):
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
		
	def set_save_plots(self):
		
		if str(self.filenameEdit.text()):
			saveinfile=''.join([str(self.filenameEdit.text()),self.timestr])
			saveinfile_et=''.join([str(self.filenameEdit.text()),"elapsedtime_",self.timestr])
		else:
			saveinfile=''.join(["data_",self.timestr])
			saveinfile_et=''.join(["data_elapsedtime_",self.timestr])
			
		if str(self.folderEdit.text()):
			if not os.path.isdir(str(self.folderEdit.text())):
				os.mkdir(str(self.folderEdit.text()))
			saveinfolder=''.join([str(self.folderEdit.text()),"/"])
		else:
			saveinfolder=""
		
		save_plot1=''.join([saveinfolder,saveinfile,'_scan.png'])	
		save_plot2=''.join([saveinfolder,saveinfile_et,'_scan.png'])	

		# create an exporter instance, as an argument give it
		# the item you wish to export
		exporter = pg.exporters.ImageExporter(self.pw1.plotItem)
		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_plot1)
		
		exporter = pg.exporters.ImageExporter(self.pw3.plotItem)
		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_plot2)

	def set_save(self):
		
		self.timestr=time.strftime("%y%m%d-%H%M")
		with open("config_stepper.py", 'w') as thefile:
			
			thefile.write( ''.join(["NumOfIntervals=",str(self.numofintervals),"\n"]) )
			thefile.write( ''.join(["Start=[",','.join([str(self.startEdit[ii].text()) for ii in range(self.numofintervals)]),"]\n"]) )
			thefile.write( ''.join(["Stop=[",','.join([str(self.stopEdit[ii].text()) for ii in range(self.numofintervals)]),"]\n"]) )
			thefile.write( ''.join(["Step=[",','.join([str(self.stepEdit[ii].text()) for ii in range(self.numofintervals)]),"]\n"]) )
			thefile.write( ''.join(["Wait_time=[",','.join([str(self.dwelltimeEdit[ii].text()) for ii in range(self.numofintervals)]),"]\n"]) )
			thefile.write( ''.join(["calibfile=\"",self.calib_file_str,"\"\n"]) )
			thefile.write( ''.join(["filename=\"",str(self.filenameEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["create_folder=\"",str(self.folderEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["timestr=\"",self.timestr,"\"\n"]) )
			thefile.write( ''.join(["stepperport=\"",self.stepperport_str,"\"\n"]) )

		reload(config_stepper)
		self.numofintervals=config_stepper.NumOfIntervals
		self.start = config_stepper.Start
		self.stop = config_stepper.Stop
		self.step = config_stepper.Step
		self.dwell_time = config_stepper.Wait_time
		self.calib_file_str = config_stepper.calibfile
		self.filename_str=config_stepper.filename
		self.folder_str=config_stepper.create_folder
		self.timestr=config_stepper.timestr
		self.stepperport_str = config_stepper.stepperport

def main():
  
  app=QtGui.QApplication(sys.argv)
  ex=run_zaber_gui()
  sys.exit(app.exec_())
    
if __name__=='__main__':
  main()
  
