import os, os.path, sys, serial, time
import numpy as np
import scipy.interpolate
#from numpy.polynomial import polynomial as P
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.exporters
#from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, SIGNAL
import test_zaberTmca
import zaber_position as zp
import config_zaber, ArdMega2560

class zaber_Thread(QThread):
  
	def __init__(self, *args):
		QThread.__init__(self)

		if len(args)==4:
		  self.sender=args[0]
		  self.Za=args[1]
		  self.Ard=args[2]
		  self.calib_file=args[3]
		elif len(args)==5:
		  self.sender=args[0]
		  self.Za=args[1]
		  self.Ard=args[2]
		  self.calib_file=args[3]
		  self.move_num=args[4]
		elif len(args)==9:
			self.sender=args[0]
			self.Za=args[1]
			self.Ard=args[2]
			self.calib_file=args[3]
			self.start_ = args[4]
			self.stop_ = args[5]
			self.step_ = args[6]
			self.dwell_time = args[7]
			self.dwell_time_ard = args[8]/1000.0 #convert to milliseconds
		else:
		  pass
    
	def __del__(self):
	  
	  self.wait()

	def run(self):
		  
		if self.sender==u'\u25b2':
			min_pos=self.Za.move_Relative(5)
			pos_nm=self.get_nm(min_pos)
			self.emit(SIGNAL('more_tals(QString,QString)'), str(min_pos), str(pos_nm))
			with open('zaber_position.py', 'w') as thefile:
			  thefile.write( ''.join(['Position=',str(min_pos),'\n']) )
			  
		elif self.sender==u'\u25bc':
			min_pos=self.Za.move_Relative(-5)
			pos_nm=self.get_nm(min_pos)
			self.emit(SIGNAL('more_tals(QString,QString)'), str(min_pos), str(pos_nm))
			with open('zaber_position.py', 'w') as thefile:
			  thefile.write( ''.join(['Position=',str(min_pos),'\n']) )
			  
		elif self.sender=='Move rel':
			min_pos=self.Za.move_Relative(self.move_num)
			pos_nm=self.get_nm(min_pos)
			self.emit(SIGNAL('more_tals(QString,QString)'), str(min_pos), str(pos_nm))
			with open('zaber_position.py', 'w') as thefile:
			  thefile.write( ''.join(['Position=',str(min_pos),'\n']) )
			  
		elif self.sender=='Move abs':
			min_pos=self.Za.move_Absolute(self.move_num)
			pos_nm=self.get_nm(min_pos)
			self.emit(SIGNAL('more_tals(QString,QString)'), str(min_pos), str(pos_nm))
			with open('zaber_position.py', 'w') as thefile:
			  thefile.write( ''.join(['Position=',str(min_pos),'\n']) )
			  
		elif self.sender=='Move to nm':
			# open calib file and plot
			if not self.calib_file:
				raise ValueError('Empty calibration file path!')
			else:
				x=[]
				y=[]
				with open(self.calib_file, 'r') as thefile:
					for line in thefile:
						columns = line.split()
						x.extend([int(columns[0])]) #microstep pos.
						y.extend([int(columns[1])]) #wavelength
				if not x:
					raise ValueError('Empty calib file!')
				elif self.move_num<min(y) or self.move_num>max(y):
					raise ValueError('Input wavelength outside the calib file bounds!')
				else:
					#spline
					wv_curve=scipy.interpolate.splrep(y, x, k=3, s=0)
					#linear
					#wv_curve = scipy.interpolate.splrep(y, x, k=1, s=0)
					position = scipy.interpolate.splev(self.move_num, wv_curve, der=0)
					# pass microstepper position to zaber
					min_pos=self.Za.move_Absolute(int(position))
					pos_nm=self.get_nm(min_pos)
					self.emit(SIGNAL('more_tals(QString,QString)'), str(min_pos), str(pos_nm))
					with open('zaber_position.py', 'w') as thefile:
					  thefile.write( ''.join(['Position=',str(min_pos),'\n']) )
						
		elif self.sender=='Start scan':
			# open calib file and plot
			if not self.calib_file:
				raise ValueError('Empty calibration file path!')
			else:
				x=[]
				y=[]
				with open(self.calib_file, 'r') as thefile:
					for line in thefile:
						columns = line.split()
						x.extend([int(columns[0])]) #microstep pos.
						y.extend([int(columns[1])]) #wavelength
				if not x:
					raise ValueError('Empty calib file!')
				elif self.start_<min(y) or self.stop_>max(y):
					raise ValueError('Input wavelength(s) outside the calib file bounds!')
				else:
					wv_scanlist=range(self.start_,self.stop_+self.step_,self.step_)
					#spline
					wv_curve=scipy.interpolate.splrep(y, x, k=3, s=0)
					#linear
					#wv_curve = scipy.interpolate.splrep(y, x, k=1, s=0)
					positions = scipy.interpolate.splev(wv_scanlist, wv_curve, der=0)
					divs=int(self.dwell_time/self.dwell_time_ard)
					time_start=time.time()
					for ff,pp in zip(wv_scanlist,positions):
						min_pos=self.Za.move_Absolute(int(pp))
						pos_nm=self.get_nm(min_pos)
						self.emit(SIGNAL('more_tals(QString,QString)'), str(min_pos), str(pos_nm))
						with open('zaber_position.py', 'w') as thefile:
						  thefile.write( ''.join(['Position=',str(min_pos),'\n']) )
						  
						for ii in range(divs):
							bit_step=self.Ard.get_val()
							time_elap=time.time()-time_start
							self.emit(SIGNAL('volt_data(QString,QString,QString)'), str(time_elap),str(ff),str(bit_step))
							time.sleep(self.dwell_time_ard)
							
						self.emit(SIGNAL('time_data(QString,QString,QString,QString)'), str(time_elap),str(ff),str(min_pos),str(bit_step))
		    
		elif self.sender=='->500':
			min_pos=500
			self.Za.set_Current_Position(min_pos)
			pos_nm=self.get_nm(min_pos)
			self.emit(SIGNAL('more_tals(QString,QString)'), str(min_pos), str(pos_nm))
			with open('zaber_position.py', 'w') as thefile:
			  thefile.write( ''.join(['Position=',str(min_pos),'\n']) )
			  
		elif self.sender=='STOP MOVE':
			min_pos=self.Za.set_Stop()
			pos_nm=self.get_nm(min_pos)
			self.emit(SIGNAL('more_tals(QString,QString)'), str(min_pos), str(pos_nm))
			with open('zaber_position.py', 'w') as thefile:
			  thefile.write( ''.join(['Position=',str(min_pos),'\n']) )
			  
		elif self.sender=='Cancel scan':
			min_pos=self.Za.set_Stop()
			pos_nm=self.get_nm(min_pos)
			self.emit(SIGNAL('more_tals(QString,QString)'), str(min_pos), str(pos_nm))
			with open('zaber_position.py', 'w') as thefile:
			  thefile.write( ''.join(['Position=',str(min_pos),'\n']) )
		else:
		  pass
		
	def get_nm(self,pos):
		if not self.calib_file:
			return '----'
		else:
			x=[]
			y=[]
			with open(self.calib_file, 'r') as thefile:
				for line in thefile:
					columns = line.split()
					x.extend([int(columns[0])]) #microstep pos.
					y.extend([int(columns[1])]) #wavelength
			if not x:
				return '----'
			elif pos<min(x) or pos>max(x):
				return '----'
			else:
				#spline
				wv_curve=scipy.interpolate.splrep(x, y, k=3, s=0)
				#linear
				#wv_curve = scipy.interpolate.splrep(x, y, k=1, s=0)
				pos_nm = scipy.interpolate.splev(pos, wv_curve, der=0)
				return int(round(pos_nm))
  
class run_zaber_gui(QtGui.QWidget):
  
	def __init__(self):
		super(run_zaber_gui, self).__init__()
		
		#####################################################
		# constants
		self.start = config_zaber.Start
		self.stop = config_zaber.Stop
		self.step = config_zaber.Step
		self.dwell_time = config_zaber.Wait_time
		self.dwell_time_ard = config_zaber.Wait_time_ard
		self.avg_pts = config_zaber.Avg_pts
		self.analogref = config_zaber.Analogref	
		self.calib_file_str = config_zaber.calibfile
		self.timestr = config_zaber.timestr
		self.filename_str = config_zaber.filename
		self.folder_str = config_zaber.create_folder	
		self.zaberport_str = config_zaber.zaberport
		self.ardport_str = config_zaber.ardport
		
		self.Position = zp.Position
		if not os.path.exists(self.calib_file_str):
			self.pos_nm='----'
			if not self.calib_file_str:
				print "Warning! Calib file path is empty!"
			else:
				with open(self.calib_file_str, 'w') as thefile:
					print "New calib file is created!"
		else:
			x=[]
			y=[]
			with open(self.calib_file_str, 'r') as thefile:
				for line in thefile:
					columns = line.split()
					x.extend([int(columns[0])]) #microstep pos.
					y.extend([int(columns[1])]) #wavelength
			if not x or not y:
				self.pos_nm='----'
			elif self.Position<min(x) or self.Position>max(x):
				self.pos_nm='----'
			else:
				#spline
				wv_curve=scipy.interpolate.splrep(x, y, k=3, s=0)
				#linear
				#wv_curve = scipy.interpolate.splrep(x, y, k=1, s=0)
				self.pos_nm = scipy.interpolate.splev(self.Position, wv_curve, der=0)
		
		if config_zaber.filename:
			self.saveinfile=''.join([config_zaber.filename,self.timestr])
			self.saveinfile_et=''.join([config_zaber.filename,"elapsedtime_",self.timestr])
		else:
			self.saveinfile=''.join(["data_",self.timestr])
			self.saveinfile_et=''.join(["data_elapsedtime_",self.timestr])
			
		if config_zaber.create_folder:
			self.saveinfolder=''.join([config_zaber.create_folder,"/"])
		else:
			self.saveinfolder=""
		#####################################################
		
		self.initUI()
    
	def initUI(self):

		opmode_lbl = QtGui.QLabel("COMMUNICATION mode:",self)
		opmode_lbl.setStyleSheet("color: blue")
		self.connectButton = QtGui.QPushButton('Connect to serial',self)
		self.disconnectButton = QtGui.QPushButton('Disconnect from serial',self)

		lbl1 = QtGui.QLabel("ZABER stepper settings:", self)
		lbl1.setStyleSheet("color: blue")
		stepperport = QtGui.QLabel("Stepper serial port",self)
		self.zaberportEdit = QtGui.QLineEdit(self.zaberport_str,self)
				
		lbl2 = QtGui.QLabel("ARDUINO Mega2560 settings:", self)
		lbl2.setStyleSheet("color: blue")
		dwelltime_ard = QtGui.QLabel("Dwell time [ms]",self)
		avgpts_lbl = QtGui.QLabel("Averaging points", self)
		ardport = QtGui.QLabel("Arduino serial port",self)
		self.dwelltimeEdit_ard = QtGui.QLineEdit(str(self.dwell_time_ard),self)
		self.ardportEdit = QtGui.QLineEdit(self.ardport_str,self)
		self.combo1 = QtGui.QComboBox(self)
		mylist1=["1", "5","10","20","50","100"]
		self.combo1.addItems(mylist1)
		self.combo1.setCurrentIndex(mylist1.index(str(self.avg_pts)))
		
		lbl3 = QtGui.QLabel("ZEISS scan parameters:", self)
		lbl3.setStyleSheet("color: blue")
		start_lbl = QtGui.QLabel("Start[nm]",self) 
		stop_lbl = QtGui.QLabel("Stop[nm]",self)
		step_lbl = QtGui.QLabel("Step[nm]",self)
		dwelltime = QtGui.QLabel("Dwell[s]",self)
		self.startEdit = QtGui.QLineEdit(str(self.start),self)
		self.stopEdit = QtGui.QLineEdit(str(self.stop),self)
		self.stepEdit = QtGui.QLineEdit(str(self.step),self)
		self.dwelltimeEdit = QtGui.QLineEdit(str(self.dwell_time),self)
		self.startscanButton = QtGui.QPushButton('Start scan',self)
		self.cancelscanButton = QtGui.QPushButton('Cancel scan',self)
		self.cancelscanButton.setEnabled(False)	
		
		lbl4 = QtGui.QLabel("STORAGE filename and location settings:", self)
		lbl4.setStyleSheet("color: blue")
		filename = QtGui.QLabel("File",self)
		foldername = QtGui.QLabel("Folder",self)
		self.filenameEdit = QtGui.QLineEdit(self.filename_str,self)
		self.folderEdit = QtGui.QLineEdit(self.folder_str,self)
		self.savesetButton = QtGui.QPushButton('Save settings',self)
		self.saveplotsButton = QtGui.QPushButton('Save plots',self)
		self.saveplotsButton.setEnabled(False)

		# status info which button has been pressed
		self.motorstep_lbl = QtGui.QLabel("ZABER stepper postion:", self)
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
		self.movewlButton = QtGui.QPushButton('Move to nm',self)
		self.movewlEdit = QtGui.QLineEdit(str(185),self)
		self.stopButton = QtGui.QPushButton('STOP MOVE',self)
		self.stopButton.setEnabled(False)		

		##############################################

		self.lcd = QtGui.QLCDNumber(self)
		self.lcd.setStyleSheet("color: black")
		self.lcd.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd.setNumDigits(6)
		self.lcd.display(self.Position)
		
		self.lcd2 = QtGui.QLCDNumber(self)
		self.lcd2.setStyleSheet("color: magenta")
		self.lcd2.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd2.setNumDigits(4)
		if isinstance(self.pos_nm, np.ndarray)==True:
			self.lcd2.display(str(int(round(self.pos_nm))))
		else:
			self.lcd2.display(self.pos_nm)

		##############################################

		# status info which button has been pressed
		self.zeiss_lbl = QtGui.QLabel("ZEISS calibration:", self)
		self.zeiss_lbl.setStyleSheet("color: blue")
		self.calibButton = QtGui.QPushButton('Save, next',self)
		self.calibEdit = QtGui.QLineEdit("",self)
		self.setzeroButton = QtGui.QPushButton('->500',self)
		self.setzeroButton.setFixedWidth(80)
		#self.setzeroButton.setStyleSheet('QPushButton {color: black}')
		self.viewcalibButton = QtGui.QPushButton('Load calib file',self)
		self.calibfileEdit = QtGui.QLineEdit(self.calib_file_str,self)
		self.reorderButton = QtGui.QPushButton('Reorder',self)
		self.reorderButton.setFixedWidth(80)
		self.reorderButton.setEnabled(False)
		self.calibCounter=0
		
		if os.path.exists("Zeiss_wavelengths.txt"):
			# open calib file and plot
			self.y_local=[]
			with open("Zeiss_wavelengths.txt", 'r') as thefile:
				for line in thefile:
					columns = line.split()
					self.y_local.extend([int(columns[0])])
					
			self.calibEdit.setText(str(self.y_local[self.calibCounter]))
			self.calibCounter+=1
		else:
			print "Zeiss_wavelengths.txt is missing. Type wavelengths manually."

		##############################################
		##############################################

		g4_0=QtGui.QGridLayout()
		g4_0.addWidget(opmode_lbl,0,0)
		g4_1=QtGui.QGridLayout()
		g4_1.addWidget(self.connectButton,0,0)
		g4_1.addWidget(self.disconnectButton,0,1)
		v4 = QtGui.QVBoxLayout()
		v4.addLayout(g4_0)
		v4.addLayout(g4_1)

		g5_0 = QtGui.QGridLayout()
		g5_0.addWidget(lbl1,0,0)
		g5_1 = QtGui.QGridLayout()
		g5_1.addWidget(stepperport,0,0)
		g5_1.addWidget(self.zaberportEdit,0,1)
		v5 = QtGui.QVBoxLayout()
		v5.addLayout(g5_0)
		v5.addLayout(g5_1)
		
		g6_0 = QtGui.QGridLayout()
		g6_0.addWidget(lbl2,0,0)
		g6_1 = QtGui.QGridLayout()
		g6_1.addWidget(ardport,0,0)
		g6_1.addWidget(dwelltime_ard,1,0)
		g6_1.addWidget(avgpts_lbl,2,0)
		g6_1.addWidget(self.ardportEdit,0,1)
		g6_1.addWidget(self.dwelltimeEdit_ard,1,1)
		g6_1.addWidget(self.combo1,2,1)
		v6 = QtGui.QVBoxLayout()
		v6.addLayout(g6_0)
		v6.addLayout(g6_1)
		
		g7_0 = QtGui.QGridLayout()
		g7_0.addWidget(lbl3,0,0)
		g7_1 = QtGui.QGridLayout()
		g7_1.addWidget(start_lbl,0,0)
		g7_1.addWidget(stop_lbl,0,1)
		g7_1.addWidget(step_lbl,0,2)
		g7_1.addWidget(dwelltime,0,3)
		g7_1.addWidget(self.startEdit,1,0)
		g7_1.addWidget(self.stopEdit,1,1)
		g7_1.addWidget(self.stepEdit,1,2)
		g7_1.addWidget(self.dwelltimeEdit,1,3)
		g7_2 = QtGui.QGridLayout()
		g7_2.addWidget(self.startscanButton,0,0)
		g7_2.addWidget(self.cancelscanButton,0,1)		
		v7 = QtGui.QVBoxLayout()
		v7.addLayout(g7_0)
		v7.addLayout(g7_1)
		v7.addLayout(g7_2)
		
		g8_0 = QtGui.QGridLayout()
		g8_0.addWidget(lbl4,0,0)
		g8_1 = QtGui.QGridLayout()
		g8_1.addWidget(filename,0,0)
		g8_1.addWidget(self.filenameEdit,0,1)
		g8_1.addWidget(foldername,0,2)
		g8_1.addWidget(self.folderEdit,0,3)
		g8_2 = QtGui.QGridLayout()
		g8_2.addWidget(self.savesetButton,0,0)
		g8_2.addWidget(self.saveplotsButton,0,1)
		v8 = QtGui.QVBoxLayout()
		v8.addLayout(g8_0)
		v8.addLayout(g8_1)
		v8.addLayout(g8_2)

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
		g3_1.addWidget(self.calibButton)
		g3_1.addWidget(self.setzeroButton)
		g3_2=QtGui.QSplitter(QtCore.Qt.Vertical)
		g3_2.addWidget(self.calibEdit)
		g3_2.addWidget(self.reorderButton)
		g3_4=QtGui.QSplitter(QtCore.Qt.Horizontal)
		g3_4.addWidget(self.viewcalibButton)
		g3_4.addWidget(self.calibfileEdit)
		g3_5 = QtGui.QSplitter(QtCore.Qt.Horizontal)
		g3_5.addWidget(g3_1)
		g3_5.addWidget(g3_2)
		g3_5.addWidget(self.lcd2)
		h4 = QtGui.QSplitter(QtCore.Qt.Vertical)
		h4.addWidget(g3_0)
		h4.addWidget(g3_5)
		h4.addWidget(g3_4)
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		v_all = QtGui.QVBoxLayout()
		v_all.addLayout(v4)
		v_all.addLayout(v5)
		v_all.addLayout(v6)
		v_all.addLayout(v7)
		v_all.addLayout(v8)
		v_all.addWidget(h4)
		v_all.addWidget(v1)
		
		# set graph  and toolbar to a new vertical group vcan
		g0_0 = QtGui.QGridLayout()
		self.pw0 = pg.PlotWidget(name="Plot1")  ## giving the plots names allows us to link their axes together
		self.pw0.setTitle('Stepper dynamics')
		self.pw0.setLabel('left', 'stepper micropos.')
		self.pw0.setLabel('bottom', 'no. of moves')
		g0_0.addWidget(self.pw0,0,0)
		
		self.pw1 = pg.PlotWidget(name="Plot2")  ## giving the plots names allows us to link their axes together
		self.pw1.setTitle('Zeiss scan')
		self.pw1.setLabel('left', 'wavelength', units='nm')
		self.pw1.setLabel('bottom', 'stepper micropos.')
		g0_0.addWidget(self.pw1,0,1)
		
		self.pw2 = pg.PlotWidget(name="Plot3")
		self.pw2.setTitle('Zeiss calib')
		self.pw2.setLabel('left', 'wavelength', units='nm')
		self.pw2.setLabel('bottom', 'stepper micropos.')
		g0_0.addWidget(self.pw2,1,0)
		
		self.pw3 = pg.PlotWidget(name="Plot4")
		self.pw3.setTitle('Zeiss scan')		
		self.pw3.setLabel('left', 'wavelength', units='nm', color='red')
		self.pw3.setLabel('bottom', 'elapsed time', units='s')
		g0_0.addWidget(self.pw3,1,1)
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		h_all = QtGui.QHBoxLayout()
		h_all.addLayout(v_all,1)
		h_all.addLayout(g0_0,4)
		self.setLayout(h_all)

		########################################
		self.alle_tal=[self.Position]
		# create plot and add it to the figure canvas		
		self.p0 = self.pw0.plotItem
		self.curve0=self.p0.plot(pen='r')
		
		self.p1 = self.pw1.plotItem		
		self.curve3=self.p1.plot(pen='w')
		
		self.p2 = self.pw2.plotItem		
		self.p2.addLegend()
		self.curve1=self.p2.plot(pen='b',name='spline')
		self.curve2=self.p2.plot(pen='m',name='raw data')
		
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

		self.connectButton.clicked.connect(self.set_connect)
		self.disconnectButton.clicked.connect(self.set_disconnect)
		self.disconnectButton.setEnabled(False)
		self.allButtons_torf(False)

		self.saveplotsButton.clicked.connect(self.set_save_plots)
		self.savesetButton.clicked.connect(self.set_save)
		
		self.startscanButton.clicked.connect(self.set_scan)
		self.cancelscanButton.clicked.connect(self.move_stop)
		
		self.upButton.clicked.connect(self.move_jog)
		self.downButton.clicked.connect(self.move_jog)

		self.moverelButton.clicked.connect(self.move_rel)
		self.moveabsButton.clicked.connect(self.move_abs)
		self.movewlButton.clicked.connect(self.move_to_nm)

		self.setzeroButton.clicked.connect(self.set_zero)
		self.stopButton.clicked.connect(self.move_stop)

		self.calibButton.clicked.connect(self.add_calib)
		self.reorderButton.clicked.connect(self.set_reorder)
		self.combo1.activated[str].connect(self.onActivated1)
		self.viewcalibButton.clicked.connect(self.view_calib_data)
		
		self.setGeometry(30,30,1500,700)
		self.setWindowTitle('Zeiss spectrometer')
		self.show()

	##########################################
	def set_connect(self):
		
		while True:
		  try:
				self.Za = test_zaberTmca.Zaber_Tmca(str(self.zaberportEdit.text()))
				self.Ard = ArdMega2560.ArdMega2560(str(self.ardportEdit.text()),int(self.avg_pts))
				break
		  except ValueError:
				pass
		
		
		# constants
		hc=self.Za.set_Hold_Current(40)
		rc=self.Za.set_Running_Current(40)
		ts=self.Za.set_Target_Speed(30)
		micstep=self.Za.set_Microstep_Resolution(16)
		#return microstep resolution
		#micstep=self.Za.return_Setting(37)

		hold_current=''.join([str(hc)," / ",str(rc)," amps" ])
		print "Hold / Running current:", hold_current
		tar_speed=''.join([str(ts), " rpm"])
		print "Target speed:", tar_speed
		mic_res=''.join([str(micstep), " microsteps/s"])
		print "Microstep resolution:", mic_res

		# constants
		self.Za.set_Current_Position(int(self.Position))

		# disable/enable potentiometer 
		Cmd_bytes, Cmd_mode = self.Za.return_Device_Mode()
		if Cmd_bytes[3]=='0':
		  self.Za.set_Device_Mode(Cmd_mode+2**3)
		# disable/enable move tracking
		Cmd_bytes, Cmd_mode = self.Za.return_Device_Mode()
		if Cmd_bytes[4]=='1':
		  self.Za.set_Device_Mode(Cmd_mode-2**4)
		
		self.allButtons_torf(True)
		self.connectButton.setEnabled(False)
		self.disconnectButton.setEnabled(True)
		self.zaberportEdit.setEnabled(False)
		self.ardportEdit.setEnabled(False)
		
	def set_disconnect(self):

		self.Ard.close()
		self.Za.set_Hold_Current(0)
		self.Za.close()
		
		self.allButtons_torf(False)
		self.connectButton.setEnabled(True)
		self.disconnectButton.setEnabled(False)
		self.zaberportEdit.setEnabled(True)
		self.ardportEdit.setEnabled(True)
		
	def allButtons_torf(self,text):
		
		self.dwelltimeEdit_ard.setEnabled(text)
		self.combo1.setEnabled(text)
		
		self.startEdit.setEnabled(text)
		self.stopEdit.setEnabled(text)
		self.stepEdit.setEnabled(text)
		self.dwelltimeEdit.setEnabled(text)
		self.startscanButton.setEnabled(text)
		#self.cancelscanButton.setEnabled(text)
		
		self.calibButton.setEnabled(text)
		self.calibEdit.setEnabled(text)
		self.setzeroButton.setEnabled(text)
		self.reorderButton.setEnabled(text)
		self.viewcalibButton.setEnabled(text)
		self.calibfileEdit.setEnabled(text)
		
		self.savesetButton.setEnabled(text)
		self.saveplotsButton.setEnabled(text)
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
			if hasattr(self, 'Za') and hasattr(self, 'Ard'):
				if self.connectButton.isEnabled()==False:
					self.Ard.close()
					self.Za.set_Hold_Current(0)
					self.Za.close()
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
  
	def add_calib(self):
		
		if not os.path.exists(str(self.calibfileEdit.text())):
			if not str(self.calibfileEdit.text()):
				raise ValueError("Empty calib file string!")
			else:
				with open(str(self.calibfileEdit.text()), 'w') as thefile:
					pass
		
		# save to calib file
		data_point = self.calibEdit.text()
		with open(str(self.calibfileEdit.text()), 'a') as thefile:
		  thefile.write('%s' %self.alle_tal[-1] )
		  if not data_point:
				raise ValueError("No calib value typed!")
		  else:
				thefile.write('\t%s\n' %data_point)
		
		# open calib file and plot
		self.x=[]
		self.y=[]
		with open(str(self.calibfileEdit.text()), 'r') as thefile:
		  for line in thefile:
				columns = line.split()
				self.x.extend([int(columns[0])])
				self.y.extend([int(columns[1])])
		
		self.curve2.setData(self.x,self.y)  
		#self.calibEdit.setText('')
		self.reorderButton.setEnabled(True)

		if os.path.exists("Zeiss_wavelengths.txt"):		
			if len(self.y_local)>self.calibCounter:
				self.calibEdit.setText(str(self.y_local[self.calibCounter]))
				self.calibCounter+=1
			else:
				print "No more wavelengths in the file Zeiss_wavelengths.txt" 
		else:
			pass

	def set_reorder(self):
		
		if os.path.exists(self.calibfileEdit.text()):
			# open calib file and get all x and y
			x=[]
			y=[]
			with open(str(self.calibfileEdit.text()), 'r') as thefile:
				for line in thefile:
					columns = line.split()
					x.extend([int(columns[0])])
					y.extend([int(columns[1])])
			# sort x element and their respective y
			sort_index = np.argsort(x)	
			sort_x=[]
			sort_y=[]	
			with open(str(self.calibfileEdit.text()), 'w') as thefile:
				for i in sort_index:
					thefile.write('%s\t' %x[i])
					thefile.write('%s\n' %y[i])				
					sort_x.extend([ x[i] ])
					sort_y.extend([ y[i] ])	
			self.curve2.setData(sort_x,sort_y)  
			#self.calibEdit.setText('')
		else:
			print "The calib file path does not exists!"
			
	def view_calib_data(self):
		
		if os.path.exists(self.calibfileEdit.text()):
			# open calib file and plot
			x=[]
			y=[]
			with open(str(self.calibfileEdit.text()), 'r') as thefile:
				for line in thefile:
					columns = line.split()
					x.extend([int(columns[0])])
					y.extend([int(columns[1])])
					
			self.curve2.setData(x,y) 
			
			wv_scanlist=range(y[0],y[-1]+1,1)
			#spline
			wv_curve=scipy.interpolate.splrep(y, x, k=3, s=0)
			#linear
			#wv_curve = scipy.interpolate.splrep(y, x, k=1, s=0)		
			positions = scipy.interpolate.splev(wv_scanlist, wv_curve, der=0)
			self.curve1.setData(positions,wv_scanlist)
		else:
			print "The calib file path does not exists!"
		
	def set_scan(self):
		
		self.all_pos=[]
		self.all_time=[]
		self.all_wv=[]
		self.all_bits=[]
		
		self.some_pos=[]
		self.some_time=[]
		self.some_wv=[]
		self.some_bits=[]
		
		self.curve3.setData([],[])
		self.curve4.setData([],[])
		self.curve5.setData([],[])
		self.curve6.setData([],[])
		
		start_sc = int(self.startEdit.text())
		stop_sc = int(self.stopEdit.text())
		step_sc = int(self.stepEdit.text())
		dwell_zaber = float(self.dwelltimeEdit.text())
		dwell_ard = float(self.dwelltimeEdit_ard.text())
		
		self.cancelscanButton.setEnabled(True)
		self.disconnectButton.setEnabled(False)
		self.allButtons_torf(False)

		sender = self.sender()
		self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.Ard,str(self.calibfileEdit.text()),start_sc,stop_sc,step_sc,dwell_zaber,dwell_ard)
		self.connect(self.get_zaber_Thread,SIGNAL("more_tals(QString,QString)"),self.more_tals)
		self.connect(self.get_zaber_Thread,SIGNAL("time_data(QString,QString,QString,QString)"),self.time_data)
		self.connect(self.get_zaber_Thread,SIGNAL("volt_data(QString,QString,QString)"),self.volt_data)
		self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
		
		self.get_zaber_Thread.start()
  
	def move_stop(self):
		
		self.get_zaber_Thread.terminate()
		self.disconnectButton.setEnabled(True)
		self.allButtons_torf(True)

		sender = self.sender()
		get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.Ard,str(self.calibfileEdit.text()))
		self.connect(get_zaber_Thread,SIGNAL("more_tals(QString,QString)"),self.more_tals)
		self.connect(get_zaber_Thread, SIGNAL('finished()'), self.set_finished)

		get_zaber_Thread.start()

	def set_zero(self):
		
		sender = self.sender()
		get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.Ard,str(self.calibfileEdit.text()))
		self.connect(get_zaber_Thread,SIGNAL("more_tals(QString,QString)"),self.more_tals)
		self.connect(get_zaber_Thread, SIGNAL('finished()'), self.set_finished)

		get_zaber_Thread.start()    
	
	def move_to_nm(self):
		
		# update the lcd motorstep position
		move_num = int(self.movewlEdit.text())
		self.stopButton.setEnabled(True)
		self.disconnectButton.setEnabled(False)
		self.allButtons_torf(False)
		
		sender = self.sender()
		self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.Ard,str(self.calibfileEdit.text()),move_num)
		self.connect(self.get_zaber_Thread,SIGNAL("more_tals(QString,QString)"),self.more_tals)
		self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
		
		self.get_zaber_Thread.start()
		
	def move_rel(self):
		
		# update the lcd motorstep position
		move_num = int(self.moverelEdit.text())
		self.stopButton.setEnabled(True)
		self.disconnectButton.setEnabled(False)
		self.allButtons_torf(False)
		
		sender = self.sender()
		self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.Ard,str(self.calibfileEdit.text()),move_num)
		self.connect(self.get_zaber_Thread,SIGNAL("more_tals(QString,QString)"),self.more_tals)
		self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
		
		self.get_zaber_Thread.start()
		
	def move_abs(self):
		
		# update the lcd motorstep position
		move_num = int(self.moveabsEdit.text())
		self.stopButton.setEnabled(True)
		self.disconnectButton.setEnabled(False)
		self.allButtons_torf(False)
		
		sender = self.sender()
		self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.Ard,str(self.calibfileEdit.text()),move_num)
		self.connect(self.get_zaber_Thread,SIGNAL("more_tals(QString,QString)"),self.more_tals)
		self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
		    
		self.get_zaber_Thread.start()
		
	def move_jog(self):
		
		# update the lcd motorstep position
		sender = self.sender()
		self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.Ard,str(self.calibfileEdit.text()))
		self.connect(self.get_zaber_Thread,SIGNAL("more_tals(QString,QString)"),self.more_tals)
		self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
		
		self.get_zaber_Thread.start()
		
	def more_tals(self,min_tal,pos_nm):
		
		self.lcd.display(min_tal)
		self.lcd2.display(pos_nm)
		self.alle_tal.extend([ int(min_tal) ])    
		self.curve0.setData(self.alle_tal)

	def time_data(self,time,iii,pos,bits):
		
		self.some_wv.extend([ int(iii) ])
		self.some_pos.extend([ int(pos) ])
		self.some_time.extend([ float(time) ])
		self.some_bits.extend([ int(bits) ])
		self.curve3.setData(self.some_pos,self.some_wv)
		self.curve6.setData(self.some_time, self.some_bits)

	def volt_data(self,time,iii,bit_step):
		
		self.all_wv.extend([ int(iii) ])
		self.all_bits.extend([ int(bit_step) ])
		self.all_time.extend([ float(time) ])
		
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
		self.curve4.setData(self.all_time, self.all_wv)
		self.curve5.setData(self.all_time, self.all_bits)

	def set_finished(self):
		
		self.cancelscanButton.setEnabled(False)
		self.stopButton.setEnabled(False)
		self.disconnectButton.setEnabled(True)
		self.allButtons_torf(True)

	def onActivated1(self, text):
		
		self.avg_pts = str(text)

	def set_save_plots(self):
		
		save_plot1=''.join([self.saveinfolder,self.saveinfile,'_stepper_dyn.png'])	
		save_plot2=''.join([self.saveinfolder,self.saveinfile_et,'_zeiss_calib.png'])	

		# create an exporter instance, as an argument give it
		# the item you wish to export
		exporter = pg.exporters.ImageExporter(self.pw0.plotItem)
		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_plot1)
		
		exporter = pg.exporters.ImageExporter(self.pw2.plotItem)
		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_plot2)

	def set_save(self):
		
		#self.saveplotsButton.setEnabled(True)
		
		self.timestr=time.strftime("%Y%m%d-%H%M%S")
		with open("config_zaber.py", 'w') as thefile:
			thefile.write( ''.join(["Start=",str(self.startEdit.text()),"\n"]) )
			thefile.write( ''.join(["Stop=",str(self.stopEdit.text()),"\n"]) )
			thefile.write( ''.join(["Step=",str(self.stepEdit.text()),"\n"]) )
			thefile.write( ''.join(["Wait_time=",str(self.dwelltimeEdit.text()),"\n"]) )
			thefile.write( ''.join(["Wait_time_ard=",str(self.dwelltimeEdit_ard.text()),"\n"]) )
			thefile.write( ''.join(["Avg_pts=",str(self.avg_pts),"\n"]) )
			thefile.write( ''.join(["Analogref=",str(self.analogref),"\n"]) )
			thefile.write( ''.join(["calibfile=\"",str(self.calibfileEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["filename=\"",str(self.filenameEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["create_folder=\"",str(self.folderEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["timestr=\"",self.timestr,"\"\n"]) )
			thefile.write( ''.join(["zaberport=\"",str(self.zaberportEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["ardport=\"",str(self.ardportEdit.text()),"\"\n"]) )

		reload(config_zaber)
		self.start = config_zaber.Start
		self.stop = config_zaber.Stop
		self.step = config_zaber.Step
		self.dwell_time = config_zaber.Wait_time
		self.dwell_time_ard = config_zaber.Wait_time_ard
		self.avg_pts = config_zaber.Avg_pts
		self.calib_file_str = config_zaber.calibfile
		self.filename_str=config_zaber.filename
		self.folder_str=config_zaber.create_folder
		self.timestr=config_zaber.timestr

		# For SAVING data and graphs
		if self.filename_str:
			self.saveinfile=''.join([self.filename_str,self.timestr])
			self.saveinfile_et=''.join([self.filename_str,"elapsedtime_",self.timestr])
		else:
			self.saveinfile=''.join(["data_",self.timestr])
			self.saveinfile_et=''.join(["data_elapsedtime_",self.timestr])
			
		if self.folder_str:
			self.saveinfolder=''.join([self.folder_str,"/"])
			if not os.path.isdir(self.folder_str):
				os.mkdir(self.folder_str)
		else:
			self.saveinfolder=""

def main():
  
  app=QtGui.QApplication(sys.argv)
  ex=run_zaber_gui()
  sys.exit(app.exec_())
    
if __name__=='__main__':
  main()
  
