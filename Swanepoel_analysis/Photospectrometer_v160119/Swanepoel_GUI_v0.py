import os, sys, serial, time
import numpy, importlib
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, SIGNAL
import config_Swanepoel


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
				time.sleep(0.5)
				
				



class Run_CM110(QtGui.QWidget):

	def __init__(self):
		super(Run_CM110, self).__init__()
		
		# Initial read of the config file
		self.config_file = config_Swanepoel.current_config_file
		head, tail = os.path.split(self.config_file)
		sys.path.insert(0, head)
		self.cf = __import__(tail[:-3])
		
		# load all relevant parameters
		self.loadSubFilmOlis_str = self.cf.loadSubFilmOlis_str
		self.loadSubFilmFTIR_str = self.cf.loadSubFilmFTIR_str 
		self.loadSubOlis_str = self.cf.loadSubOlis_str
		self.loadSubFTIR_str = self.cf.loadSubFTIR_str
		
		self.fit_linear_spline=self.cf.fit_linear_spline
		self.num_periods=self.cf.num_periods
		self.iterations=self.cf.iterations
		self.Expected_Substrate_Dev=self.cf.Expected_Substrate_Dev
		self.strong_abs_start_eV=self.cf.strong_abs_start_eV
		self.gaussian_factors=self.cf.gaussian_factors
		self.gaussian_borders=self.cf.gaussian_borders
		self.index_m1_sections=self.cf.index_m1_sections
		self.fit_poly_order=self.cf.fit_poly_order
		self.fit_poly_ranges=self.cf.fit_poly_ranges
		
		self.filename_str=self.cf.filename
		self.folder_str=self.cf.save_analysis_folder
		self.timestr=self.cf.timestr
		
		self.initUI()
			
	def initUI(self):
		
		################### MENU BARS START ##################
		MyBar = QtGui.QMenuBar(self)
		
		fileMenu = MyBar.addMenu("File")
		
		fileSavePlt = fileMenu.addAction("Save plots")
		fileSavePlt.triggered.connect(self.set_save_plots)
		fileSavePlt.setShortcut('Ctrl+P')
		
		fileSaveSet = fileMenu.addAction("Save config to file")        
		fileSaveSet.triggered.connect(self.saveConfig) 
		fileSaveSet.setShortcut('Ctrl+S')
		
		fileSaveSet = fileMenu.addAction("Load config from file")        
		fileSaveSet.triggered.connect(self.loadConfig) 
		fileSaveSet.setShortcut('Ctrl+O')
		
		fileClose = fileMenu.addAction("Close")        
		fileClose.triggered.connect(self.close) # triggers closeEvent()
		fileClose.setShortcut('Ctrl+X')
		
		loadMenu = MyBar.addMenu("Load data")
		loadSubOlis = loadMenu.addAction("Substrate Olis file")
		loadSubFilmOlis = loadMenu.addAction("Substrate + thin film Olis file")
		loadSubFTIR = loadMenu.addAction("Substrate FTIR file")
		loadSubFilmFTIR = loadMenu.addAction("Substrate + thin film FTIR file")
		
		loadSubOlis.triggered.connect(self.loadSubOlisDialog)
		loadSubFilmOlis.triggered.connect(self.loadSubFilmOlisDialog)
		loadSubFTIR.triggered.connect(self.loadSubFTIRDialog)
		loadSubFilmFTIR.triggered.connect(self.loadSubFilmFTIRDialog)
		
		################### MENU BARS END ##################
		
		# status info which button has been pressed
		Start_lbl = QtGui.QLabel("ANALYSIS methods and plots", self)
		Start_lbl.setStyleSheet("color: blue")
		
		####################################################
		
		Step1_lbl = QtGui.QLabel("STEP 1. Plot raw data and find the corresponding minima and maxima positions using Gaussian filter settings.", self)
		Step1_lbl.setStyleSheet("color: black")
		Step1_lbl.setWordWrap(True)
		self.Step1_Button = QtGui.QPushButton("Plot raw data",self)
		self.button_style(self.Step1_Button,'black')
		
		Step2_lbl = QtGui.QLabel("STEP 2. Apply flattening to raw data in order to catch vertical oscillations.", self)
		Step2_lbl.setStyleSheet("color: black")
		Step2_lbl.setWordWrap(True)
		self.Step2_Button = QtGui.QPushButton("Apply flattening",self)
		self.button_style(self.Step2_Button,'black')
		
		Step3_lbl = QtGui.QLabel("STEP 3. Find calibration arrays A and W based on the PSG and PSA angles in the config file.", self)
		Step3_lbl.setStyleSheet("color: black")
		Step3_lbl.setWordWrap(True)
		self.Step3_Button = QtGui.QPushButton("Calibrate",self)
		self.button_style(self.Step3_Button,'black')
		
		Step4_lbl = QtGui.QLabel("STEP 4. Make multidimensional scans and calculate Mueller elements based on A and W from the above calibration procedure.", self)
		Step4_lbl.setStyleSheet("color: black")
		Step4_lbl.setWordWrap(True)
		self.Step4_Button = QtGui.QPushButton("Scan",self)
		self.button_style(self.Step4_Button,'black')
		
		Step5_lbl = QtGui.QLabel("STEP 5. Monitor selected analog port (detector) continuously. This option is useful when aligning optic components by hand.", self)
		Step5_lbl.setStyleSheet("color: black")
		Step5_lbl.setWordWrap(True)
		self.Step5_Button = QtGui.QPushButton("Monitor detector",self)
		self.button_style(self.Step5_Button,'black')
		
		####################################################
		loads_lbl = QtGui.QLabel("RAW data files", self)
		loads_lbl.setStyleSheet("color: blue")
		
		configFile_lbl = QtGui.QLabel("Current config file", self)
		self.config_file_lbl = QtGui.QLabel("", self)
		self.config_file_lbl.setStyleSheet("color: green")
		
		loadSubOlis_lbl = QtGui.QLabel("OLIS substrate", self)
		self.loadSubOlisFile_lbl = QtGui.QLabel("", self)
		self.loadSubOlisFile_lbl.setStyleSheet("color: magenta")
			
		loadSubFilmOlis_lbl = QtGui.QLabel("OLIS substrate + thin film", self)
		self.loadSubFilmOlisFile_lbl = QtGui.QLabel("", self)
		self.loadSubFilmOlisFile_lbl.setStyleSheet("color: magenta")
		
		loadSubFTIR_lbl = QtGui.QLabel("FTIR substrate", self)
		self.loadSubFTIRFile_lbl = QtGui.QLabel("", self)
		self.loadSubFTIRFile_lbl.setStyleSheet("color: magenta")
		
		loadSubFilmFTIR_lbl = QtGui.QLabel("FTIR substrate + thin film", self)
		self.loadSubFilmFTIRFile_lbl = QtGui.QLabel("", self)
		self.loadSubFilmFTIRFile_lbl.setStyleSheet("color: magenta")
		
		####################################################
		
		lbl3 = QtGui.QLabel("BASIC analysis settings", self)
		lbl3.setStyleSheet("color: blue")	
		
		interpol_lbl = QtGui.QLabel("Interpolation method", self)
		self.combo4 = QtGui.QComboBox(self)
		self.mylist4=["spline","linear"]
		self.combo4.addItems(self.mylist4)
		
		numper_lbl = QtGui.QLabel("Extend no. of periods for extrema search", self)
		self.combo5 = QtGui.QComboBox(self)
		self.mylist5=["0","1","2","3","4"]
		self.combo5.addItems(self.mylist5)
		
		iter_lbl = QtGui.QLabel("No. of iterations for T flattening", self)
		self.combo6 = QtGui.QComboBox(self)
		self.mylist6=["1","2","3","4","5"]
		self.combo6.addItems(self.mylist6)
		
		subdev_lbl = QtGui.QLabel("Expected substrate n uncertainty", self)
		self.subdevEdit=QtGui.QLineEdit("",self)
		
		strongabs_lbl = QtGui.QLabel("Expected strong absorption start [eV]", self)
		self.strongabsEdit=QtGui.QLineEdit("",self)
		
		####################################################
		
		lbl1 = QtGui.QLabel("GAUSSIAN filter settings", self)
		lbl1.setStyleSheet("color: blue")	
		
		factors_lbl = QtGui.QLabel("Gaussian factors", self)
		self.factorsEdit = QtGui.QLineEdit("",self)
		self.factorsEdit.setFixedWidth(200)
		
		borders_lbl = QtGui.QLabel("Gaussian borders", self)
		self.bordersEdit = QtGui.QLineEdit("",self)
		self.bordersEdit.setFixedWidth(200)
		
		##############################################
		
		lbl2 = QtGui.QLabel("REFRACTIVE index n fitting", self)
		lbl2.setStyleSheet("color: blue")	
		
		poly_lbl = QtGui.QLabel("Polynimial order", self)
		self.combo1 = QtGui.QComboBox(self)
		self.mylist1=["1","2","3","4"]
		self.combo1.addItems(self.mylist1)
		
		polybord_lbl = QtGui.QLabel("Polyfit borders", self)
		self.poly_bordersEdit = QtGui.QLineEdit("",self)
		self.poly_bordersEdit.setFixedWidth(200)
		
		m1bord_lbl = QtGui.QLabel("Index m1 borders", self)
		self.m1_bordersEdit = QtGui.QLineEdit("",self)
		self.m1_bordersEdit.setFixedWidth(200)
		
		##############################################
		
		lbl4 = QtGui.QLabel("STORAGE filename and location settings", self)
		lbl4.setStyleSheet("color: blue")
		filename_lbl = QtGui.QLabel("File, Folder",self)
		self.filenameEdit = QtGui.QLineEdit("",self)
		self.folderEdit = QtGui.QLineEdit("",self)
		
		##############################################
		
		# status info which button has been pressed
		self.elapsedtime_str = QtGui.QLabel("TIME trace for storing plots and data", self)
		self.elapsedtime_str.setStyleSheet("color: blue")
		
		##############################################
		
		self.lcd = QtGui.QLCDNumber(self)
		self.lcd.setStyleSheet("color: red")
		self.lcd.setFixedHeight(60)
		self.lcd.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd.setNumDigits(11)
		self.lcd.display(self.timestr)
			
		##############################################
		
		# Add all widgets		
		g1_0 = QtGui.QGridLayout()
		g1_0.addWidget(MyBar,0,0)
		g1_1 = QtGui.QGridLayout()
		g1_1.addWidget(loads_lbl,0,0)
		g1_1.addWidget(configFile_lbl,1,0)
		g1_1.addWidget(self.config_file_lbl,1,1)
		g1_1.addWidget(loadSubOlis_lbl,2,0)
		g1_1.addWidget(self.loadSubOlisFile_lbl,2,1)
		g1_1.addWidget(loadSubFilmOlis_lbl,3,0)
		g1_1.addWidget(self.loadSubFilmOlisFile_lbl,3,1)
		g1_1.addWidget(loadSubFTIR_lbl,4,0)
		g1_1.addWidget(self.loadSubFTIRFile_lbl,4,1)
		g1_1.addWidget(loadSubFilmFTIR_lbl,5,0)
		g1_1.addWidget(self.loadSubFilmFTIRFile_lbl,5,1)
		
		g1_8 = QtGui.QGridLayout()
		g1_8.addWidget(lbl3,0,0)
		g1_8.addWidget(interpol_lbl,1,0)
		g1_8.addWidget(self.combo4,1,1)
		g1_8.addWidget(numper_lbl,2,0)
		g1_8.addWidget(self.combo5,2,1)
		g1_8.addWidget(iter_lbl,3,0)
		g1_8.addWidget(self.combo6,3,1)
		g1_8.addWidget(subdev_lbl,4,0)
		g1_8.addWidget(self.subdevEdit,4,1)
		g1_8.addWidget(strongabs_lbl,5,0)
		g1_8.addWidget(self.strongabsEdit,5,1)
		
		g1_2 = QtGui.QGridLayout()
		g1_2.addWidget(lbl1,0,0)
		g1_3 = QtGui.QGridLayout()
		g1_3.addWidget(factors_lbl,0,0)
		g1_3.addWidget(self.factorsEdit,0,1)
		g1_3.addWidget(borders_lbl,1,0)
		g1_3.addWidget(self.bordersEdit,1,1)
		
		g1_4 = QtGui.QGridLayout()
		g1_4.addWidget(lbl2,0,0)
		g1_5 = QtGui.QGridLayout()
		g1_5.addWidget(poly_lbl,0,0)
		g1_5.addWidget(self.combo1,0,1)
		g1_5.addWidget(polybord_lbl,1,0)
		g1_5.addWidget(self.poly_bordersEdit,1,1)
		g1_5.addWidget(m1bord_lbl,2,0)
		g1_5.addWidget(self.m1_bordersEdit,2,1)
		
		g4_0 = QtGui.QGridLayout()
		g4_0.addWidget(lbl4,0,0)
		g4_1 = QtGui.QGridLayout()
		g4_1.addWidget(filename_lbl,0,0)
		g4_1.addWidget(self.filenameEdit,0,1)
		g4_1.addWidget(self.folderEdit,0,2)
		
		g6_0 = QtGui.QGridLayout()
		g6_0.addWidget(self.elapsedtime_str,0,0)
		g6_0.addWidget(self.lcd,1,0)
		
		v1 = QtGui.QVBoxLayout()
		v1.addLayout(g1_0)
		v1.addLayout(g1_1)
		v1.addLayout(g1_8)
		v1.addLayout(g1_2)
		v1.addLayout(g1_3)
		v1.addLayout(g1_4)
		v1.addLayout(g1_5)
		v1.addLayout(g4_0)
		v1.addLayout(g4_1)
		v1.addLayout(g6_0)
		
		###################################################
		
		g1_6 = QtGui.QGridLayout()
		g1_6.addWidget(Start_lbl,0,0)
		g1_7 = QtGui.QGridLayout()
		g1_7.addWidget(Step1_lbl,0,0)
		g1_7.addWidget(self.Step1_Button,1,0)
		g1_7.addWidget(Step2_lbl,2,0)
		g1_7.addWidget(self.Step2_Button,3,0)
		g1_7.addWidget(Step3_lbl,4,0)
		g1_7.addWidget(self.Step3_Button,5,0)
		g1_7.addWidget(Step4_lbl,6,0)
		g1_7.addWidget(self.Step4_Button,7,0)
		g1_7.addWidget(Step5_lbl,8,0)
		g1_7.addWidget(self.Step5_Button,9,0)
		v0 = QtGui.QVBoxLayout()
		v0.addLayout(g1_6)
		v0.addLayout(g1_7)
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		hbox = QtGui.QHBoxLayout()
		hbox.addLayout(v1)
		hbox.addLayout(v0)
		self.setLayout(hbox) 
		
		###############################################################################
		
		# reacts to choises picked in the menu
		self.combo1.activated[str].connect(self.onActivated1)
		self.combo4.activated[str].connect(self.onActivated4)
		self.combo5.activated[str].connect(self.onActivated5)
		self.combo6.activated[str].connect(self.onActivated6)
		
		# reacts to choises picked in the menu
		self.Step1_Button.clicked.connect(self.set_run)
		self.Step2_Button.clicked.connect(self.set_run)
		self.Step3_Button.clicked.connect(self.set_run)
		self.Step4_Button.clicked.connect(self.set_run)
		self.Step5_Button.clicked.connect(self.set_run)
		
		self.set_field_vals()
		self.allEditFields(True)
		
		self.move(0,0)
		#self.setGeometry(100, 100, 1300, 800)
		self.setWindowTitle("Swanepoel method for determination of thickness and optical constants")
		self.show()
	
	
	def set_field_vals(self):
		
		head, tail = os.path.split(self.config_file)
		self.config_file_lbl.setText(tail)
		
		head, tail = os.path.split(self.loadSubOlis_str)
		self.loadSubOlisFile_lbl.setText(tail)
		
		head, tail = os.path.split(self.loadSubFilmOlis_str)
		self.loadSubFilmOlisFile_lbl.setText(tail)
		
		head, tail = os.path.split(self.loadSubFTIR_str)
		self.loadSubFTIRFile_lbl.setText(tail)
		
		head, tail = os.path.split(self.loadSubFilmFTIR_str)
		self.loadSubFilmFTIRFile_lbl.setText(tail)
		
		##############################################
		
		self.combo4.setCurrentIndex(self.mylist4.index(self.fit_linear_spline))
		self.combo5.setCurrentIndex(self.mylist5.index(str(self.num_periods)))
		self.combo6.setCurrentIndex(self.mylist6.index(str(self.iterations)))
		
		self.subdevEdit.setText(str(self.Expected_Substrate_Dev))
		self.strongabsEdit.setText(str(self.strong_abs_start_eV))
		
		##############################################
		
		self.factorsEdit.setText(', '.join([str(i) for i in self.gaussian_factors] ))
		self.bordersEdit.setText(', '.join([str(i) for i in self.gaussian_borders] ))
		
		##############################################
		
		self.combo1.setCurrentIndex(self.mylist1.index(str(self.fit_poly_order)))
		self.poly_bordersEdit.setText(', '.join([str(i) for i in self.fit_poly_ranges] ))
		self.m1_bordersEdit.setText(', '.join([str(i) for i in self.index_m1_sections] ))
		
		##############################################
		
		self.filenameEdit.setText(str(self.filename_str))
		self.folderEdit.setText(str(self.folder_str))
		self.lcd.display(self.timestr)
		
	def button_style(self,button,color):
		
		button.setStyleSheet(''.join(['QPushButton {background-color: lightblue; font-size: 18pt; color: ',color,'}']))
		button.setFixedWidth(280)
		button.setFixedHeight(75)		
	
	def allEditFields(self,trueorfalse):
		
		self.combo1.setEnabled(trueorfalse)
		self.combo4.setEnabled(trueorfalse)
		self.combo5.setEnabled(trueorfalse)
		self.combo6.setEnabled(trueorfalse)
		
		self.factorsEdit.setEnabled(trueorfalse)
		self.bordersEdit.setEnabled(trueorfalse)
		self.m1_bordersEdit.setEnabled(trueorfalse)
		self.poly_bordersEdit.setEnabled(trueorfalse)
		
		self.filenameEdit.setEnabled(trueorfalse)
		self.folderEdit.setEnabled(trueorfalse)
	
	def loadConfig(self):
		
		old_head, old_tail = os.path.split(self.config_file)
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Load Config File Dialog',old_head)
		
		if fname:
			self.config_file = str(fname)
			head, tail = os.path.split(str(fname))
			sys.path.insert(0, head)
			self.set_load_config(tail)
			
	def saveConfig(self):
		
		fname = QtGui.QFileDialog.getSaveFileName(self, 'Save Config File Dialog',self.config_file[:-3])
		
		if fname:
			self.config_file = str(fname)
			head, tail = os.path.split(str(fname))
			self.set_save_config()
	
	def loadSubOlisDialog(self):
		
		old_head, old_tail = os.path.split(self.loadSubOlis_str)
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file',old_head)
		
		if fname:
			self.loadSubOlis_str = str(fname)
			head, tail = os.path.split(str(fname))
			self.loadSubOlisFile_lbl.setText(tail)
			
	def loadSubFilmOlisDialog(self):
		
		old_head, old_tail = os.path.split(self.loadSubFilmOlis_str)
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file',old_head)
		
		if fname:
			self.loadSubFilmOlis_str = str(fname)
			head, tail = os.path.split(str(fname))
			self.loadSubFilmOlisFile_lbl.setText(tail)
			
	def loadSubFTIRDialog(self):
		
		old_head, old_tail = os.path.split(self.loadSubFTIR_str)
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file',old_head)
		
		if fname:
			self.loadSubFTIR_str = str(fname)
			head, tail = os.path.split(str(fname))
			self.loadSubFTIRFile_lbl.setText(tail)
			
	def loadSubFilmFTIRDialog(self):
		
		old_head, old_tail = os.path.split(self.loadSubFilmFTIR_str)
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file',old_head)
		
		if fname:
			self.loadSubFilmFTIR_str = str(fname)
			head, tail = os.path.split(str(fname))
			self.loadSubFilmFTIRFile_lbl.setText(tail)
	
	def onActivated1(self, text):
		
		self.fit_poly_order = int(text)
	
	def onActivated4(self, text):
		
		self.fit_linear_spline=str(text)
	
	def onActivated5(self, text):
		
		self.num_periods=int(text)
		
	def onActivated6(self, text):
		
		self.iterations=int(text)
	
	
	def set_run(self):
		
		sender = self.sender()
		if sender.text()=='Plot raw data':
			self.set_save_config()
			import Get_TM_Tm_v0
			Get_TM_Tm_v0.Get_TM_Tm().make_plots()
			
			self.button_style(self.Step1_Button,'red')
			self.button_style(self.Step2_Button,'grey')
			self.button_style(self.Step3_Button,'grey')
			self.button_style(self.Step4_Button,'grey')
			self.button_style(self.Step5_Button,'grey')
			
		elif sender.text()=='Apply flattening':
			self.set_save_config()
			import get_extrema
			get_extrema.Find_extrema().make_plots()
			
			self.button_style(self.Step2_Button,'red')
			self.button_style(self.Step1_Button,'grey')
			self.button_style(self.Step3_Button,'grey')
			self.button_style(self.Step4_Button,'grey')
			self.button_style(self.Step5_Button,'grey')
		elif sender.text()=='Calibrate':
			import Scatterometer_calib_GUI_v0
			self.pp=Scatterometer_calib_GUI_v0.run_zaber_gui()
			self.button_style(self.Step3_Button,'red')
			self.button_style(self.Step2_Button,'grey')
			self.button_style(self.Step1_Button,'grey')
			self.button_style(self.Step4_Button,'grey')
			self.button_style(self.Step5_Button,'grey')
		elif sender.text()=='Scan':
			import Scatterometer_scan_GUI_v4
			self.pp=Scatterometer_scan_GUI_v4.run_zaber_gui()
			self.button_style(self.Step4_Button,'red')
			self.button_style(self.Step2_Button,'grey')
			self.button_style(self.Step1_Button,'grey')
			self.button_style(self.Step3_Button,'grey')
			self.button_style(self.Step5_Button,'grey')
		elif sender.text()=='Monitor detector':
			import Detector_monitor_GUI_v0
			self.pp=Detector_monitor_GUI_v0.Det_Mon()
			self.button_style(self.Step5_Button,'red')
			self.button_style(self.Step4_Button,'grey')
			self.button_style(self.Step2_Button,'grey')
			self.button_style(self.Step1_Button,'grey')
			self.button_style(self.Step3_Button,'grey')
			
		self.get_my_Thread=my_Thread(sender.text(),self.pp)
		self.connect(self.get_my_Thread,SIGNAL('finished()'),self.set_finished)
		
		self.allButtons_torf(False)

		self.get_my_Thread.start()
	
	def set_cancel(self):

		self.get_thread.abort()
		
		self.allEditFields(True)
		self.cancelButton.setEnabled(False)
		self.runButton.setEnabled(True)
		
	def clear_vars_graphs(self):
		# PLOT 1 initial canvas settings
		self.all_wl=[]
		self.all_volts=[]
		self.all_X_volts=[]
		self.all_times=[]
		self.all_raw=[]
		self.plot_wl=[]
		self.plot_volts=[]
		self.plot_X_volts=[]
		self.plot_times=[]
		self.plot_raw=[]
		self.curve1.setData(self.plot_wl, self.plot_volts)
		self.curve6.setData(self.plot_wl, self.plot_X_volts)
		self.curve5.setData(self.plot_wl, self.plot_raw)
		self.curve7.setData(self.plot_times, self.plot_X_volts)
		self.curve3.setData(self.plot_times, self.plot_volts)
		self.pw1.enableAutoRange()
		# Labels and titels are placed here since they change dynamically
		self.pw1.setTitle(''.join(["CM110 scan as function of wavelength"]))
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
		self.p1.setTitle(''.join(["CM110 scan as function of time"]))
		self.p1.setLabel('left', "Lock-in voltage", units=self.unit_str, color='red')
		self.p1.setLabel('bottom', "Elapsed time", units='s')
	
	def set_save_config(self):
		
		self.timestr=time.strftime("%y%m%d-%H%M")
		self.lcd.display(self.timestr)
		
		with open(''.join([self.config_file,".py"]), 'w') as thefile:
			# film+substrate measurements
			thefile.write( ''.join(["loadSubOlis_str=\"",self.loadSubOlis_str,"\"\n"]))
			thefile.write( ''.join(["loadSubFTIR_str=\"",self.loadSubFTIR_str,"\"\n"]))
			thefile.write( ''.join(["loadSubFilmOlis_str=\"",self.loadSubFilmOlis_str,"\"\n"]))
			thefile.write( ''.join(["loadSubFilmFTIR_str=\"",self.loadSubFilmFTIR_str,"\"\n"]))
		
			thefile.write( ''.join(["fit_linear_spline=\"",self.fit_linear_spline,"\"\n"]))
			thefile.write( ''.join(["Expected_Substrate_Dev=",str(self.subdevEdit.text()),"\n"]))
			thefile.write( ''.join(["gaussian_factors=[",str(self.factorsEdit.text()),"]\n"]))
			thefile.write( ''.join(["gaussian_borders=[",str(self.bordersEdit.text()),"]\n"]))
			thefile.write( ''.join(["index_m1_sections=[",str(self.m1_bordersEdit.text()),"]\n"]))
			thefile.write( ''.join(["num_periods=",str(self.num_periods),"\n"]))
			thefile.write( ''.join(["iterations=",str(self.iterations),"\n"]))
			thefile.write( ''.join(["strong_abs_start_eV=",str(self.strongabsEdit.text()),"\n"]))
			thefile.write( ''.join(["fit_poly_order=",str(self.fit_poly_order),"\n"]))
			thefile.write( ''.join(["fit_poly_ranges=[",str(self.poly_bordersEdit.text()),"]\n"]))

			thefile.write( ''.join(["filename=\"",self.filename_str,"\"\n"]))
			thefile.write( ''.join(["save_analysis_folder=\"",self.folder_str,"\"\n"]))
			thefile.write( ''.join(["timestr=\"",self.timestr,"\""]))	
	
		mymodule=reload(self.cf)
		
		# load all relevant parameters
		self.loadSubFilmOlis_str = mymodule.loadSubFilmOlis_str
		self.loadSubFilmFTIR_str = mymodule.loadSubFilmFTIR_str 
		self.loadSubOlis_str = mymodule.loadSubOlis_str
		self.loadSubFTIR_str = mymodule.loadSubFTIR_str
		
		self.fit_linear_spline=mymodule.fit_linear_spline
		self.num_periods=mymodule.num_periods
		self.iterations=mymodule.iterations
		self.Expected_Substrate_Dev=mymodule.Expected_Substrate_Dev
		self.strong_abs_start_eV=mymodule.strong_abs_start_eV
		self.gaussian_factors=mymodule.gaussian_factors
		self.gaussian_borders=mymodule.gaussian_borders
		self.index_m1_sections=mymodule.index_m1_sections
		self.fit_poly_order=mymodule.fit_poly_order
		self.fit_poly_ranges=mymodule.fit_poly_ranges
		
		self.filename_str=mymodule.filename
		self.folder_str=mymodule.save_analysis_folder
		self.timestr=mymodule.timestr
	
	
	def set_load_config(self,tail):
		
		with open("config_Swanepoel.py", 'w') as thefile:
			thefile.write( ''.join(["current_config_file=\"",self.config_file,"\""]))
			
		self.cf = __import__(tail[:-3])
		
		self.loadSubFilmOlis_str = self.cf.loadSubFilmOlis_str
		self.loadSubFilmFTIR_str = self.cf.loadSubFilmFTIR_str 
		self.loadSubOlis_str = self.cf.loadSubOlis_str
		self.loadSubFTIR_str = self.cf.loadSubFTIR_str
		
		self.fit_linear_spline=self.cf.fit_linear_spline
		self.Expected_Substrate_Dev=self.cf.Expected_Substrate_Dev
		self.gaussian_factors=self.cf.gaussian_factors
		self.gaussian_borders=self.cf.gaussian_borders
		self.index_m1_sections=self.cf.index_m1_sections
		self.num_periods=self.cf.num_periods
		self.iterations=self.cf.iterations
		self.strong_abs_start_eV=self.cf.strong_abs_start_eV
		self.fit_poly_order=self.cf.fit_poly_order
		self.fit_poly_ranges=self.cf.fit_poly_ranges
		
		self.filename_str=self.cf.filename
		self.folder_str=self.cf.save_analysis_folder
		self.timestr=self.cf.timestr
		
		self.set_field_vals()
		
	def set_finished(self):
		
		self.allEditFields(True)
		
	def closeEvent(self, event):
		
		reply = QtGui.QMessageBox.question(self, 'Message', "Quit now? Any changes that are not saved will stay unsaved!", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes:
			if hasattr(self, 'CM110') and hasattr(self, 'Ard'):
				if self.conMode.isEnabled()==False:
					if not hasattr(self, 'get_thread'):
						self.Ard.close()
						self.CM110.close()
						self.SR850.close()
						event.accept()
					else:
						if self.get_thread.isRunning():
							QtGui.QMessageBox.warning(self, 'Message', "Run in progress. Cancel the run then quit!")
							event.ignore()
						else:
							self.Ard.close()
							self.CM110.close()
							self.SR850.close()
							event.accept()
				else:
					pass
			else:
				event.accept()
		else:
		  event.ignore() 
		
	##########################################
	
	def set_save_plots(self):
		
		self.filename_str=str(self.filenameEdit.text())
		self.folder_str=str(self.folderEdit.text())
		
		# For SAVING graphs
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
	ex = Run_CM110()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()