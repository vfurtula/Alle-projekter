import os, sys, serial, time
import numpy
import scipy.interpolate
#from numpy.polynomial import polynomial as P
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.exporters
#from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, SIGNAL
import ZaberTmca
import zaber_position as zp
import config_zaber, ArdMega2560

class zaber_Thread(QThread):
    
	def __init__(self, sender, Za, Ard, calib_file, avg_pts, *argv):
		QThread.__init__(self)
		
		self.sender=sender
		self.Za=Za
		self.Ard=Ard
		self.calib_file=calib_file
		self.avg_pts=avg_pts
		if len(argv)==1:
		  self.move_num=argv[0]
		elif len(argv)==2:
		  self.alignEdit_nm=argv[0]
		  dummy=argv[1]
		elif len(argv)==7:
			self.start_ = argv[0]
			self.stop_ = argv[1]
			self.step_ = argv[2]
			self.dwell_time = argv[3]
			self.dwell_time_ard = argv[4]/1000.0 #convert to milliseconds
			self.save_to_file = argv[5]
			self.analogref = argv[6]
		else:
		  pass
    
	def __del__(self):
	  
	  self.wait()

	def run(self):
		  
		if self.sender==u'\u25b2':
			min_pos=self.Za.move_Relative(15)
			pos_nm=self.get_nm(min_pos)
			bit_step=self.Ard.get_val(self.avg_pts)
			self.emit(SIGNAL('more_tals(QString,QString,QString)'), str(min_pos), str(pos_nm), str(bit_step))
			with open('zaber_position.py', 'w') as thefile:
			  thefile.write( ''.join(['Position=',str(min_pos),'\n']) )
			  
		elif self.sender==u'\u25bc':
			min_pos=self.Za.move_Relative(-15)
			pos_nm=self.get_nm(min_pos)
			bit_step=self.Ard.get_val(self.avg_pts)
			self.emit(SIGNAL('more_tals(QString,QString,QString)'), str(min_pos), str(pos_nm), str(bit_step))
			with open('zaber_position.py', 'w') as thefile:
			  thefile.write( ''.join(['Position=',str(min_pos),'\n']) )
			  
		elif self.sender=='Move rel':
			min_pos=self.Za.move_Relative(self.move_num)
			pos_nm=self.get_nm(min_pos)
			bit_step=self.Ard.get_val(self.avg_pts)
			self.emit(SIGNAL('more_tals(QString,QString,QString)'), str(min_pos), str(pos_nm), str(bit_step))
			with open('zaber_position.py', 'w') as thefile:
			  thefile.write( ''.join(['Position=',str(min_pos),'\n']) )
			  
		elif self.sender=='Move abs':
			min_pos=self.Za.move_Absolute(self.move_num)
			pos_nm=self.get_nm(min_pos)
			bit_step=self.Ard.get_val(self.avg_pts)
			self.emit(SIGNAL('more_tals(QString,QString,QString)'), str(min_pos), str(pos_nm), str(bit_step))
			with open('zaber_position.py', 'w') as thefile:
			  thefile.write( ''.join(['Position=',str(min_pos),'\n']) )
			  
		elif self.sender=='Move to nm':
			position=self.get_pos(self.move_num)
			min_pos=self.Za.move_Absolute(position)
			bit_step=self.Ard.get_val(self.avg_pts)
			self.emit(SIGNAL('more_tals(QString,QString,QString)'), str(min_pos), str(round(self.move_num,1)), str(bit_step))
			with open('zaber_position.py', 'w') as thefile:
			  thefile.write( ''.join(['Position=',str(min_pos),'\n']) )
						
		elif self.sender=='Start scan':
			# open calib file and plot
			if not self.calib_file:
				raise ValueError('Empty calibration file path!')
			else:
				# create elapsed time text file and close it
				with open(''.join([self.save_to_file[:-4],'_ElapsedTime.txt']), 'w') as thefile:
					thefile.write("Your edit line - do NOT delete this line\n")
					thefile.write("Wavelength [nm], Voltage [mV], Raw output [bit step], Elapsed time [s]\n")
				# create regular text file, make headings and close it
				with open(self.save_to_file, 'w') as thefile:
					thefile.write("Your edit line - do NOT delete this line\n")
					thefile.write("Wavelength [nm], Voltage [mV], Raw output [bit step], Elapsed time [s]\n")
				x=[]
				y=[]
				with open(self.calib_file, 'r') as thefile:
					for line in thefile:
						columns = line.split()
						x.extend([int(columns[0])]) #microstep pos.
						y.extend([round(float(columns[1]),1)]) #wavelength
				if not x:
					raise ValueError('Empty calib file!')
				elif min(self.start_)<min(y) or max(self.stop_)>max(y):
					raise ValueError('Input wavelength(s) outside the calib file bounds!')
				else:
					#spline
					wv_curve=scipy.interpolate.splrep(y, x, k=3, s=0)
					#linear
					#wv_curve = scipy.interpolate.splrep(y, x, k=1, s=0)
					time_start=time.time()
					for start,stop,step,dwell in zip(self.start_,self.stop_,self.step_,self.dwell_time):
						if stop==self.stop_[-1]:
							wv_scanlist=numpy.arange(start,stop+step,step)
						else:
							wv_scanlist=numpy.arange(start,stop,step)
						positions = scipy.interpolate.splev(wv_scanlist, wv_curve, der=0)
						divs=int(dwell/self.dwell_time_ard)
						for ff,pp in zip(wv_scanlist,positions):
							min_pos=self.Za.move_Absolute(int(pp))
							pos_nm=self.get_nm(min_pos)
							bit_step=self.Ard.get_val(self.avg_pts)
							self.emit(SIGNAL('more_tals(QString,QString,QString)'), str(min_pos), str(pos_nm), str(bit_step))
							self.emit(SIGNAL('curve3_data(QString,QString)'), str(min_pos), str(ff))
							with open('zaber_position.py', 'w') as thefile:
							  thefile.write( ''.join(['Position=',str(min_pos),'\n']) )
							
							for ii in range(divs):
								time_ard_start=time.time()
								time_elap=time_ard_start-time_start
								bit_step=self.Ard.get_val(self.avg_pts)
								volt_str=self.analogref*(bit_step/1023.0) 
								with open(''.join([self.save_to_file[:-4],'_ElapsedTime.txt']), 'a') as thefile:
									thefile.write("%s" %ff)
									thefile.write("\t%s" %volt_str)
									thefile.write("\t%s" %bit_step)
									thefile.write("\t%s\n" %time_elap)
								self.emit(SIGNAL('volt_data(QString,QString,QString)'), str(time_elap),str(ff),str(volt_str))
								#time.sleep(self.dwell_time_ard)
								while (time.time()-time_ard_start)<self.dwell_time_ard:
									pass
							
							self.emit(SIGNAL('time_data(QString,QString,QString,QString)'), str(time_elap),str(ff),str(min_pos),str(volt_str))
							with open(self.save_to_file, 'a') as thefile:
								thefile.write("%s" %ff)
								thefile.write("\t%s" %volt_str)
								thefile.write("\t%s" %bit_step)
								thefile.write("\t%s\n" %time_elap)
								
		elif self.sender=='-> nm':
			min_pos=self.get_pos(self.alignEdit_nm)
			self.Za.set_Current_Position(min_pos)
			bit_step=self.Ard.get_val(self.avg_pts)
			self.emit(SIGNAL('more_tals(QString,QString,QString)'), str(min_pos), str(self.alignEdit_nm), str(bit_step))
			with open('zaber_position.py', 'w') as thefile:
			  thefile.write( ''.join(['Position=',str(min_pos),'\n']) )
			  
		elif self.sender=='STOP MOVE':
			min_pos=self.Za.set_Stop()
			pos_nm=self.get_nm(min_pos)
			bit_step=self.Ard.get_val(self.avg_pts)
			self.emit(SIGNAL('more_tals(QString,QString,QString)'), str(min_pos), str(pos_nm), str(bit_step))
			with open('zaber_position.py', 'w') as thefile:
			  thefile.write( ''.join(['Position=',str(min_pos),'\n']) )
			  
		elif self.sender=='Cancel scan':
			min_pos=self.Za.set_Stop()
			pos_nm=self.get_nm(min_pos)
			bit_step=self.Ard.get_val(self.avg_pts)
			self.emit(SIGNAL('more_tals(QString,QString,QString)'), str(min_pos), str(pos_nm), str(bit_step))
			with open('zaber_position.py', 'w') as thefile:
			  thefile.write( ''.join(['Position=',str(min_pos),'\n']) )
		else:
		  pass
	
	def get_pos(self,nm):
		
		x=[]
		y=[]
		with open(self.calib_file, 'r') as thefile:
			for line in thefile:
				columns = line.split()
				x.extend([int(columns[0])]) #microstep pos.
				y.extend([round(float(columns[1]),1)]) #wavelength

		if nm>=min(y) and nm<=max(y):
			#spline
			pos_curve=scipy.interpolate.splrep(y, x, k=3, s=0)
			#linear
			#wv_curve = scipy.interpolate.splrep(x, y, k=1, s=0)
			pos_pos = scipy.interpolate.splev(nm, pos_curve, der=0)
			return int(round(pos_pos))
		
	def get_nm(self,pos):
		
		x=[]
		y=[]
		with open(self.calib_file, 'r') as thefile:
			for line in thefile:
				columns = line.split()
				x.extend([int(columns[0])]) #microstep pos.
				y.extend([round(float(columns[1]),1)]) #wavelength

		if pos>=min(x) and pos<=max(x):
			#spline
			wv_curve=scipy.interpolate.splrep(x, y, k=3, s=0)
			#linear
			#wv_curve = scipy.interpolate.splrep(x, y, k=1, s=0)
			pos_nm = scipy.interpolate.splev(pos, wv_curve, der=0)
			return round(pos_nm,1)
  
class run_zaber_gui(QtGui.QWidget):
  
	def __init__(self):
		super(run_zaber_gui, self).__init__()
		
		#####################################################
		# constants
		self.numofintervals=config_zaber.NumOfIntervals
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
	
		self.initUI()
    
	def initUI(self):
				
		lbl2 = QtGui.QLabel("ARDUINO Mega2560 settings:", self)
		lbl2.setStyleSheet("color: blue")
		dwelltime_ard = QtGui.QLabel("Dwell time [ms]",self)
		avgpts_lbl = QtGui.QLabel("Averaging points", self)
		self.dwelltimeEdit_ard = QtGui.QLineEdit(str(self.dwell_time_ard),self)
		self.combo1 = QtGui.QComboBox(self)
		mylist1=["1","5","20","50","100","200"]
		self.combo1.addItems(mylist1)
		self.combo1.setCurrentIndex(mylist1.index(str(self.avg_pts)))
		
		##############################################
		
		lbl3 = QtGui.QLabel("ZEISS scan parameters:", self)
		lbl3.setStyleSheet("color: blue")
		intervals_lbl = QtGui.QLabel("Number of intervals", self)
		self.combo2 = QtGui.QComboBox(self)
		mylist2=["1","2","3"]
		self.combo2.addItems(mylist2)
		self.combo2.setCurrentIndex(mylist2.index(str(self.numofintervals)))
		start_lbl = QtGui.QLabel("Start[nm]",self) 
		stop_lbl = QtGui.QLabel("Stop[nm]",self)
		step_lbl = QtGui.QLabel("Step[nm]",self)
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
		self.movewlButton.setStyleSheet('QPushButton {color: magenta}')
		self.movewlEdit = QtGui.QLineEdit("",self)
		self.stopButton = QtGui.QPushButton('STOP MOVE',self)
		self.stopButton.setEnabled(False)	
		
		##############################################
		
		self.timetrace_str = QtGui.QLabel("TIME trace for storing plots and data:", self)
		self.timetrace_str.setStyleSheet("color: blue")	
		
		##############################################

		self.lcd = QtGui.QLCDNumber(self)
		self.lcd.setStyleSheet("color: black")
		self.lcd.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd.setNumDigits(6)
		self.lcd.display(self.Position)
		
		self.lcd2 = QtGui.QLCDNumber(self)
		self.lcd2.setStyleSheet("color: magenta")
		self.lcd2.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd2.setNumDigits(6)
		self.lcd2.display('000000')
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
		self.zeiss_lbl = QtGui.QLabel("ZEISS alignment:", self)
		self.zeiss_lbl.setStyleSheet("color: blue")
		self.alignEdit = QtGui.QLineEdit("",self)
		self.setzeroButton = QtGui.QPushButton('-> nm',self)
		self.setzeroButton.setStyleSheet('QPushButton {color: magenta}')
		self.setzeroButton.setFixedWidth(70)
		#self.setzeroButton.setStyleSheet('QPushButton {color: black}')

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
		fileClose = fileMenu.addAction("Close")        
		fileClose.triggered.connect(self.close) # triggers closeEvent()
		fileClose.setShortcut('Ctrl+X')
		
		modeMenu = MyBar.addMenu("Mode")
		self.conMode = modeMenu.addAction("Connect to serial")
		self.conMode.triggered.connect(self.set_connect)
		self.disconMode = modeMenu.addAction("Disconnect from serial")
		self.disconMode.triggered.connect(self.set_disconnect)
		
		serialMenu = MyBar.addMenu("Serial")
		self.serialZaber = serialMenu.addAction("Zaber stepper")
		self.serialZaber.triggered.connect(self.ZaberDialog)
		self.serialArd = serialMenu.addAction("Arduino")
		self.serialArd.triggered.connect(self.ArdDialog)
		
		calibMenu = MyBar.addMenu("Calib")
		calibZeiss = calibMenu.addAction("Load calib file")
		calibZeiss.setShortcut('Ctrl+O')
		calibZeiss.triggered.connect(self.loadCalibDialog)
		calibZeiss.triggered.connect(self.view_calib_data)
		
		################### MENU BARS END ##################
		
		g4_0=QtGui.QGridLayout()
		g4_0.addWidget(MyBar,0,0)
		v4 = QtGui.QVBoxLayout()
		v4.addLayout(g4_0)
		
		g6_0 = QtGui.QGridLayout()
		g6_0.addWidget(lbl2,0,0)
		g6_1 = QtGui.QGridLayout()
		g6_1.addWidget(dwelltime_ard,0,0)
		g6_1.addWidget(avgpts_lbl,1,0)
		g6_1.addWidget(self.dwelltimeEdit_ard,0,1)
		g6_1.addWidget(self.combo1,1,1)
		v6 = QtGui.QVBoxLayout()
		v6.addLayout(g6_0)
		v6.addLayout(g6_1)
		
		g7_0 = QtGui.QGridLayout()
		g7_0.addWidget(lbl3,0,0)
		g7_3 = QtGui.QGridLayout()
		g7_3.addWidget(intervals_lbl,0,0)
		g7_3.addWidget(self.combo2,0,1)
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
		v7.addLayout(g7_3)
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
		v_all.addLayout(v6)
		v_all.addLayout(v7)
		v_all.addWidget(v8)
		v_all.addWidget(h4)
		v_all.addWidget(v1)
		v_all.addWidget(g9_0)
		
		# set graph  and toolbar to a new vertical group vcan
		g0_0 = QtGui.QGridLayout()
		self.pw0 = pg.PlotWidget(name="Plot1")  ## giving the plots names allows us to link their axes together
		self.pw0.setTitle('Stepper dynamics')
		self.pw0.setLabel('left', 'stepper micropos.')
		self.pw0.setLabel('bottom', 'no. of moves')
		g0_0.addWidget(self.pw0,0,0)
		
		self.pw1 = pg.PlotWidget(name="Plot2")  ## giving the plots names allows us to link their axes together
		self.pw1.setTitle('Zeiss scan')
		self.pw1.setLabel('bottom', 'wavelength', units='nm')
		self.pw1.setLabel('left', "Voltage", units='mV', color='yellow')
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
		self.p0.getAxis('right').setLabel("Arduino bit step", color='yellow')
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
		self.p3.getAxis('right').setLabel("Voltage", units='mV', color='yellow')
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
		self.combo2.activated[str].connect(self.onActivated2)
		
		self.setzeroButton.clicked.connect(self.set_zero)
		self.combo1.activated[str].connect(self.onActivated1)
		
		self.upButton.clicked.connect(self.move_jog)
		self.downButton.clicked.connect(self.move_jog)
		self.moverelButton.clicked.connect(self.move_rel)
		self.moveabsButton.clicked.connect(self.move_abs)
		self.movewlButton.clicked.connect(self.move_to_nm)
		self.stopButton.clicked.connect(self.move_stop)
		
		self.setGeometry(30,30,1200,550)
		self.setWindowTitle('Zeiss spectrometer')
		self.show()
		self.view_calib_data()

	##########################################
	def ZaberDialog(self):

		text, ok = QtGui.QInputDialog.getText(self, 'Serial Port Dialog',
																				'Enter Zaber stepper serial:', text=self.zaberport_str)
		if ok:
			self.zaberport_str = str(text)
	
	def ArdDialog(self):

		text, ok = QtGui.QInputDialog.getText(self, 'Serial Port Dialog',
																				'Enter Arduino serial:', text=self.ardport_str)
		if ok:
			self.ardport_str = str(text)
	
	def loadCalibDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file','C:/Documents and Settings/PLD User/My Documents/Vedran_work_folder/Zeiss_spectrometer/Calib_files')
		if fname:
			self.calib_file_str = str(fname)
		
	def set_connect(self):
		
		while True:
		  try:
				self.Za = ZaberTmca.Zaber_Tmca(self.zaberport_str)
				self.Ard = ArdMega2560.ArdMega2560(self.ardport_str)
				initial_bit = self.Ard.get_val(self.avg_pts)
				break
		  except ValueError:
				pass
			
		# constants
		hc=self.Za.set_Hold_Current(40)
		rc=self.Za.set_Running_Current(40)
		ts=self.Za.set_Target_Speed(2*100)
		micstep=self.Za.set_Microstep_Resolution(2*32)
		max_pos=self.Za.set_Maximum_Position(250000)
		#return microstep resolution
		#micstep=self.Za.return_Setting(37)

		hc_str=''.join([str(hc)," / ",str(rc)," amps" ])
		print "Hold / Running current:", hc_str
		ts_str=''.join([str(ts), " rpm"])
		print "Target speed:", ts_str
		micstep_str=''.join([str(micstep), " microsteps/s"])
		print "Microstep resolution:", micstep_str
		max_pos_str=''.join([str(max_pos), " microsteps"])
		print "Maximum position:", max_pos_str

		# constants
		self.Za.set_Current_Position(int(self.Position))

		# disable/enable potentiometer 
		# A value of 1 disables the potentiometer preventing manual adjustment of the device. 
		# The default value is 0 on all devices. 
		Cmd_bytes, Cmd_mode = self.Za.return_Device_Mode()
		if Cmd_bytes[3]=='0':
		  self.Za.set_Device_Mode(Cmd_mode+2**3)
		  
		# disable/enable move tracking
		# A value of 1 enables the Move Tracking response during move commands. 
		# The device will return its position periodically when a move command is executed. 
		# The Disable Auto-Reply option takes precedence over this option. The default value is 0 on all devices. 
		Cmd_bytes, Cmd_mode = self.Za.return_Device_Mode()
		if Cmd_bytes[4]=='1':
		  self.Za.set_Device_Mode(Cmd_mode-2**4)
		
		self.allButtons_torf(True)
		self.conMode.setEnabled(False)
		self.disconMode.setEnabled(True)
		self.serialZaber.setEnabled(False)
		self.serialArd.setEnabled(False)
		
		self.all_pos=[self.Position]
		self.some_bits=[initial_bit]
		
	def set_disconnect(self):

		self.Ard.close()
		self.Za.set_Hold_Current(0)
		self.Za.close()
		
		self.allButtons_torf(False)
		self.conMode.setEnabled(True)
		self.disconMode.setEnabled(False)
		self.serialZaber.setEnabled(True)
		self.serialArd.setEnabled(True)
		
	def allButtons_torf(self,text):
		
		self.dwelltimeEdit_ard.setEnabled(text)
		self.combo1.setEnabled(text)
		self.combo2.setEnabled(text)
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
			if hasattr(self, 'Za') and hasattr(self, 'Ard'):
				if self.conMode.isEnabled()==False:
					if not hasattr(self, 'get_zaber_Thread'):
						self.Ard.close()
						self.Za.set_Hold_Current(0)
						self.Za.close()
						event.accept()
					else:
						if self.get_zaber_Thread.isRunning():
							QtGui.QMessageBox.warning(self, 'Message', "Run in progress. Cancel the run then quit!")
							event.ignore()
						else:
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
			self.curve2.setData(x,y) 
			
			wv_scanlist=numpy.arange(y[0],y[-1]+0.1,0.1)
			#spline
			wv_curve=scipy.interpolate.splrep(y, x, k=3, s=0)
			#linear
			#wv_curve = scipy.interpolate.splrep(y, x, k=1, s=0)		
			positions = scipy.interpolate.splev(wv_scanlist, wv_curve, der=0)
			self.curve1.setData(positions,wv_scanlist)
			
			if self.Position<min(x) or self.Position>max(x):
				self.lcd2.display('------')
			else:
				# Update the LCD display lcd2 with the wavelength which
				# corresponds to the saved Zaber microposition
				wv_curve2=scipy.interpolate.splrep(x, y, k=3, s=0)
				first_pos_nm = scipy.interpolate.splev(self.Position, wv_curve2, der=0)
				self.lcd2.display(str(round(first_pos_nm,1)))
					
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message', 
														"Something is wrong with Calib file! Do you have a Calib file with 2 columns, no headers, and all inputs are digits?")
			self.lcd2.display('----')
			self.curve1.setData([],[])
			self.curve2.setData([],[])				
			
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
		self.all_bits=[]
		self.some_pos=[]
		self.some_time=[]
		self.some_wv=[]
		self.some_volts=[]
		self.curve3_nm=[]
		self.curve3_pos=[]
		
		self.curve3.setData([],[])
		self.curve4.setData([],[])
		self.curve5.setData([],[])
		self.curve6.setData([],[])
		self.curve8.setData([],[])
		
		start_sc = [round(float(self.startEdit[ii].text()),1) for ii in range(self.numofintervals)]
		stop_sc = [round(float(self.stopEdit[ii].text()),1) for ii in range(self.numofintervals)]
		step_sc = [round(float(self.stepEdit[ii].text()),1) for ii in range(self.numofintervals)]
		dwell_zaber = [float(self.dwelltimeEdit[ii].text()) for ii in range(self.numofintervals)]
		dwell_ard = float(self.dwelltimeEdit_ard.text())
		
		#for ff,pp in zip(wv_scanlist,positions):
		for i,j in zip(start_sc,stop_sc):
			if i<self.min_y_calib or i>self.max_y_calib or j<self.min_y_calib or j>self.max_y_calib:
				myvar=False
				break
			else:
				myvar=True
		
		if myvar==False:	
			QtGui.QMessageBox.warning(self, 'Message',
														''.join(['Valid scan range is from ',str(self.min_y_calib),' nm to ',str(self.max_y_calib),' nm.' ]) )
		else:
			
			self.Za.close()
			self.Ard.close()
			time.sleep(0.25)
			self.Za = ZaberTmca.Zaber_Tmca(self.zaberport_str)
			self.Ard = ArdMega2560.ArdMega2560(self.ardport_str)
			
			
			self.cancelscanButton.setEnabled(True)
			self.disconMode.setEnabled(False)
			self.allButtons_torf(False)
			
			sender = self.sender()
			self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.Ard,self.calib_file_str,self.avg_pts,start_sc,stop_sc,step_sc,dwell_zaber,dwell_ard,save_to_file,self.analogref)
			self.connect(self.get_zaber_Thread,SIGNAL("more_tals(QString,QString,QString)"),self.more_tals)
			self.connect(self.get_zaber_Thread,SIGNAL("curve3_data(QString,QString)"),self.curve3_data)
			self.connect(self.get_zaber_Thread,SIGNAL("time_data(QString,QString,QString,QString)"),self.time_data)
			self.connect(self.get_zaber_Thread,SIGNAL("volt_data(QString,QString,QString)"),self.volt_data)
			self.connect(self.get_zaber_Thread,SIGNAL('finished()'), self.set_finished)
			
			self.get_zaber_Thread.start()
  
	def move_stop(self):
		
		self.get_zaber_Thread.terminate()
		
		self.disconMode.setEnabled(True)
		self.allButtons_torf(True)
		
		sender = self.sender()
		get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.Ard,self.calib_file_str,self.avg_pts)
		self.connect(get_zaber_Thread,SIGNAL("more_tals(QString,QString,QString)"),self.more_tals)
		self.connect(get_zaber_Thread,SIGNAL('finished()'), self.set_finished)
		
		get_zaber_Thread.start()

	def set_zero(self):
		
		move_num=round(float(self.alignEdit.text()),1)
		if move_num<self.min_y_calib or move_num>self.max_y_calib:
			QtGui.QMessageBox.warning(self, 'Message',
														 ''.join(['Valid range is from ',str(self.min_y_calib),' nm to ',str(self.max_y_calib),' nm.' ]) )
		else:
			sender = self.sender()
			get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.Ard,self.calib_file_str,self.avg_pts,move_num,0)
			self.connect(get_zaber_Thread,SIGNAL("more_tals(QString,QString,QString)"),self.more_tals)
			self.connect(get_zaber_Thread, SIGNAL('finished()'), self.set_finished)

			get_zaber_Thread.start()    
	
	def move_to_nm(self):
		
		move_num = round(float(self.movewlEdit.text()),1)
		if move_num<self.min_y_calib or move_num>self.max_y_calib:
			QtGui.QMessageBox.warning(self, 'Message',
														 ''.join(['Valid range is from ',str(self.min_y_calib),' nm to ',str(self.max_y_calib),' nm.' ]) )
		else:
			self.stopButton.setEnabled(True)
			self.disconMode.setEnabled(False)
			self.allButtons_torf(False)
			
			sender = self.sender()
			self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.Ard,self.calib_file_str,self.avg_pts,move_num)
			self.connect(self.get_zaber_Thread,SIGNAL("more_tals(QString,QString,QString)"),self.more_tals)
			self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
			
			self.get_zaber_Thread.start()
		
	def move_rel(self):
		
		# update the lcd motorstep position
		move_num = int(self.moverelEdit.text())
		self.stopButton.setEnabled(True)
		self.disconMode.setEnabled(False)
		self.allButtons_torf(False)
		
		sender = self.sender()
		self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.Ard,self.calib_file_str,self.avg_pts,move_num)
		self.connect(self.get_zaber_Thread,SIGNAL("more_tals(QString,QString,QString)"),self.more_tals)
		self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
		
		self.get_zaber_Thread.start()
		
	def move_abs(self):
		
		# update the lcd motorstep position
		move_num = int(self.moveabsEdit.text())
		self.stopButton.setEnabled(True)
		self.disconMode.setEnabled(False)
		self.allButtons_torf(False)
		
		sender = self.sender()
		self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.Ard,self.calib_file_str,self.avg_pts,move_num)
		self.connect(self.get_zaber_Thread,SIGNAL("more_tals(QString,QString,QString)"),self.more_tals)
		self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
		    
		self.get_zaber_Thread.start()
		
	def move_jog(self):
		
		# update the lcd motorstep position
		sender = self.sender()
		self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.Ard,self.calib_file_str,self.avg_pts)
		self.connect(self.get_zaber_Thread,SIGNAL("more_tals(QString,QString,QString)"),self.more_tals)
		self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
		
		self.get_zaber_Thread.start()
	
	def set_elapsedtime_text(self):
		
		self.lcd3.display(self.timestr)
		
	def more_tals(self,pos,pos_nm,bits):
		
		self.lcd.display(pos)
		self.lcd2.display(pos_nm)
		self.some_bits.extend([ int(bits) ])
		self.all_pos.extend([ int(pos) ])    
		
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
		self.curve7.setData(self.some_bits)
	
	def curve3_data(self,pos,nm):
		
		self.curve3_nm.extend([ round(float(nm),1) ])
		self.curve3_pos.extend([ int(pos) ])
		self.curve3.setData(self.curve3_pos,self.curve3_nm)
		
	def time_data(self,time,iii,pos,volts):
		
		self.some_wv.extend([ float(iii) ])
		self.some_pos.extend([ int(pos) ])
		self.some_time.extend([ float(time) ])
		self.some_volts.extend([ round(float(volts),1) ])		
		self.curve6.setData(self.some_time, self.some_volts)
		self.curve8.setData(self.some_wv, self.some_volts)

	def volt_data(self,time,nm,volts):
		
		self.all_wv.extend([ float(nm) ])
		self.all_bits.extend([ int(float(volts)) ])
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
		self.disconMode.setEnabled(True)
		self.allButtons_torf(True)

	def onActivated1(self, text):
		
		self.avg_pts = int(text)
	
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
		with open("config_zaber.py", 'w') as thefile:
			
			thefile.write( ''.join(["NumOfIntervals=",str(self.numofintervals),"\n"]) )
			thefile.write( ''.join(["Start=[",','.join([str(self.startEdit[ii].text()) for ii in range(self.numofintervals)]),"]\n"]) )
			thefile.write( ''.join(["Stop=[",','.join([str(self.stopEdit[ii].text()) for ii in range(self.numofintervals)]),"]\n"]) )
			thefile.write( ''.join(["Step=[",','.join([str(self.stepEdit[ii].text()) for ii in range(self.numofintervals)]),"]\n"]) )
			thefile.write( ''.join(["Wait_time=[",','.join([str(self.dwelltimeEdit[ii].text()) for ii in range(self.numofintervals)]),"]\n"]) )
			thefile.write( ''.join(["Wait_time_ard=",str(self.dwelltimeEdit_ard.text()),"\n"]) )
			thefile.write( ''.join(["Avg_pts=",str(self.avg_pts),"\n"]) )
			thefile.write( ''.join(["Analogref=",str(self.analogref),"\n"]) )
			thefile.write( ''.join(["calibfile=\"",self.calib_file_str,"\"\n"]) )
			thefile.write( ''.join(["filename=\"",str(self.filenameEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["create_folder=\"",str(self.folderEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["timestr=\"",self.timestr,"\"\n"]) )
			thefile.write( ''.join(["zaberport=\"",self.zaberport_str,"\"\n"]) )
			thefile.write( ''.join(["ardport=\"",self.ardport_str,"\"\n"]) )

		reload(config_zaber)
		self.numofintervals=config_zaber.NumOfIntervals
		self.start = config_zaber.Start
		self.stop = config_zaber.Stop
		self.step = config_zaber.Step
		self.dwell_time = config_zaber.Wait_time
		self.dwell_time_ard = config_zaber.Wait_time_ard
		self.avg_pts = config_zaber.Avg_pts
		self.analogref = config_zaber.Analogref	
		self.calib_file_str = config_zaber.calibfile
		self.filename_str=config_zaber.filename
		self.folder_str=config_zaber.create_folder
		self.timestr=config_zaber.timestr
		self.zaberport_str = config_zaber.zaberport
		self.ardport_str = config_zaber.ardport

def main():
  
  app=QtGui.QApplication(sys.argv)
  ex=run_zaber_gui()
  sys.exit(app.exec_())
    
if __name__=='__main__':
  main()
  
