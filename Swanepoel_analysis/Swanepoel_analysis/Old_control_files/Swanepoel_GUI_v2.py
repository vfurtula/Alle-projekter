## Import libraries
import matplotlib.pyplot as plt
import os, sys, serial, time
import numpy, importlib

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, SIGNAL
import config_Swanepoel


class my_Thread(QThread):
    
	def __init__(self, *argv):
		QThread.__init__(self)
		
		self.sender=argv[0]
    
	def __del__(self):
	  
	  self.wait()

	def run(self):
		
		if self.sender in ['Plot raw data','Find Tmin and Tmax']:
			import Get_TM_Tm_v0
			my_arg = Get_TM_Tm_v0.Get_TM_Tm()
			
		if self.sender=='Find Tmin and Tmax':
			import Get_TM_Tm_v0
			my_arg = Get_TM_Tm_v0.Get_TM_Tm()
			
		elif self.sender=='Find order no. m1':
			import get_m_d
			my_arg = get_m_d.Gmd()

		elif self.sender=='Plot n':
			import n
			my_arg = n.N_class()
			
		elif self.sender=='Plot absorption':
			import alpha
			my_arg = alpha.Alpha()
		
		elif self.sender=='Plot wavenumber k':
			import k
			my_arg = k.K_class()
			
		elif self.sender=='Plot sensitivity':
			import get_vary_igp
			my_arg = get_vary_igp.Vary_igp()
		
		self.emit(SIGNAL('pass_plots(PyQt_PyObject,PyQt_PyObject)'), my_arg, self.sender)



class Run_CM110(QtGui.QWidget):

	def __init__(self):
		super(Run_CM110, self).__init__()
		
		# Initial read of the config file
		self.config_file = config_Swanepoel.current_config_file
		head, tail = os.path.split(self.config_file)
		sys.path.insert(0, head)
		self.cf = __import__(tail[:-3])
		
		# load all relevant parameters
		self.loadSubOlis_str = self.cf.loadSubOlis[0]
		self.loadSubFilmOlis_str = self.cf.loadSubFilmOlis[0]
		self.loadSubFTIR_str = self.cf.loadSubFTIR[0]
		self.loadSubFilmFTIR_str = self.cf.loadSubFilmFTIR[0] 
		
		self.loadSubOlis_check = self.cf.loadSubOlis[1]
		self.loadSubFilmOlis_check = self.cf.loadSubFilmOlis[1]
		self.loadSubFTIR_check = self.cf.loadSubFTIR[1]
		self.loadSubFilmFTIR_check = self.cf.loadSubFilmFTIR[1] 
		
		self.fit_linear_spline=self.cf.fit_linear_spline
		self.strong_abs_start_eV=self.cf.strong_abs_start_eV
		self.gaussian_factors=self.cf.gaussian_factors
		self.gaussian_borders=self.cf.gaussian_borders
		self.index_m1_sections=self.cf.index_m1_sections
		self.fit_poly_order=self.cf.fit_poly_order
		self.fit_poly_ranges=self.cf.fit_poly_ranges
		
		self.filename_str=self.cf.filename
		self.folder_str=self.cf.folder
		self.timestr=self.cf.timestr
		self.save_figs=self.cf.save_figs
		
		self.initUI()
			
	def initUI(self):
		
		################### MENU BARS START ##################
		MyBar = QtGui.QMenuBar(self)
		
		fileMenu = MyBar.addMenu("File")
		
		fileSave = fileMenu.addAction("Save config file")        
		fileSave.triggered.connect(self.set_save_config) 
		fileSave.setShortcut('Ctrl+S')
		
		fileSaveAs = fileMenu.addAction("Save config file as")        
		fileSaveAs.triggered.connect(self.saveConfig) 
		
		fileLoad = fileMenu.addAction("Load config from file")        
		fileLoad.triggered.connect(self.loadConfig) 
		fileLoad.setShortcut('Ctrl+O') 
		
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
		Start_lbl = QtGui.QLabel("ANALYSIS steps and plots", self)
		Start_lbl.setStyleSheet("color: blue")
		
		Step0_lbl = QtGui.QLabel("STEP 0. Plot raw data and consider its quality for Swanepoel analysis.", self)
		Step0_lbl.setStyleSheet("color: black")
		Step0_lbl.setWordWrap(True)
		self.Step0_Button = QtGui.QPushButton("Plot raw data",self)
		self.button_style(self.Step0_Button,'black')
		
		Step1_lbl = QtGui.QLabel("STEP 1. Find all the minima and maxima positions using Gaussian filter settings. Apply flattening to raw data in order to catch vertical oscillations.", self)
		Step1_lbl.setStyleSheet("color: black")
		Step1_lbl.setWordWrap(True)
		self.Step1_Button = QtGui.QPushButton("Find Tmin and Tmax",self)
		self.button_style(self.Step1_Button,'black')
		
		Step2_lbl = QtGui.QLabel("STEP 2. Plot refractive index n assuming transparent region and assuming weak and medium absorption region.", self)
		Step2_lbl.setStyleSheet("color: black")
		Step2_lbl.setWordWrap(True)
		self.Step2_Button = QtGui.QPushButton("Plot n",self)
		self.button_style(self.Step2_Button,'black')
		
		Step3_lbl = QtGui.QLabel("STEP 3. Plot l/2 versus n/lambda to determine the order number m1 and film thickness d. Finally, plot the ref index n1 and the improved ref index n2.", self)
		Step3_lbl.setStyleSheet("color: black")
		Step3_lbl.setWordWrap(True)
		self.Step3_Button = QtGui.QPushButton("Find order no. m1",self)
		self.button_style(self.Step3_Button,'black')
		
		Step4_lbl = QtGui.QLabel("STEP 4. Extrapolate the refractive index n2 (Step 3) into the strong abosrption region. Plot abosorption alpha based on calculated n2.", self)
		Step4_lbl.setStyleSheet("color: black")
		Step4_lbl.setWordWrap(True)
		self.Step4_Button = QtGui.QPushButton("Plot absorption",self)
		self.button_style(self.Step4_Button,'black')
		
		Step5_lbl = QtGui.QLabel("STEP 5. Plot wavenumber k based on the refractive index n2.", self)
		Step5_lbl.setStyleSheet("color: black")
		Step5_lbl.setWordWrap(True)
		self.Step5_Button = QtGui.QPushButton("Plot wavenumber k",self)
		self.button_style(self.Step5_Button,'black')
		
		Step6_lbl = QtGui.QLabel("STEP 6. Check the sensitivity of the order number m1 and film thickness d as a function of ignored data points.", self)
		Step6_lbl.setStyleSheet("color: black")
		Step6_lbl.setWordWrap(True)
		self.Step6_Button = QtGui.QPushButton("Plot sensitivity",self)
		self.button_style(self.Step6_Button,'black')
		
		####################################################
		
		# status info which button has been pressed
		NewFiles_lbl = QtGui.QLabel("NEWLY created and saved files", self)
		NewFiles_lbl.setStyleSheet("color: blue")
		
		self.NewFiles = numpy.zeros(5,dtype=object)
		for i in range(5):
			self.NewFiles[i] = QtGui.QLabel(''.join([str(i+1),': ']), self)
			self.NewFiles[i].setStyleSheet("color: magenta")
			
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
		
		self.cb_sub_olis = QtGui.QCheckBox('',self)
		self.cb_sub_olis.toggle()
		self.cb_subfilm_olis = QtGui.QCheckBox('',self)
		self.cb_subfilm_olis.toggle()
		self.cb_sub_ftir = QtGui.QCheckBox('',self)
		self.cb_sub_ftir.toggle()
		self.cb_subfilm_ftir = QtGui.QCheckBox('',self)
		self.cb_subfilm_ftir.toggle()
		
		####################################################
		
		lbl3 = QtGui.QLabel("BASIC analysis settings", self)
		lbl3.setStyleSheet("color: blue")	
		
		interpol_lbl = QtGui.QLabel("Interpolation method", self)
		self.combo4 = QtGui.QComboBox(self)
		self.mylist4=["spline","linear"]
		self.combo4.addItems(self.mylist4)
		
		strongabs_lbl = QtGui.QLabel("Strong absorption start [eV]", self)
		self.strongabsEdit=QtGui.QLineEdit("",self)
		
		####################################################
		
		lbl1 = QtGui.QLabel("GAUSSIAN filter settings", self)
		lbl1.setStyleSheet("color: blue")	
		
		factors_lbl = QtGui.QLabel("Gaussian factors", self)
		self.factorsEdit = QtGui.QLineEdit("",self)
		self.factorsEdit.setFixedWidth(200)
		
		borders_lbl = QtGui.QLabel("Gaussian borders [eV]", self)
		self.bordersEdit = QtGui.QLineEdit("",self)
		self.bordersEdit.setFixedWidth(200)
		
		##############################################
		
		lbl2 = QtGui.QLabel("REFRACTIVE index n fitting", self)
		lbl2.setStyleSheet("color: blue")	
		
		poly_lbl = QtGui.QLabel("Polynimial order", self)
		self.combo1 = QtGui.QComboBox(self)
		self.mylist1=["1","2","3","4"]
		self.combo1.addItems(self.mylist1)
		
		polybord_lbl = QtGui.QLabel("Polyfit range(s) [eV]", self)
		self.poly_bordersEdit = QtGui.QLineEdit("",self)
		self.poly_bordersEdit.setFixedWidth(200)
		
		m1bord_lbl = QtGui.QLabel("m1 range(s) [n/lambda]", self)
		self.m1_bordersEdit = QtGui.QLineEdit("",self)
		self.m1_bordersEdit.setFixedWidth(200)
		
		##############################################
		
		lbl4 = QtGui.QLabel("STORAGE location (file, folder)", self)
		lbl4.setStyleSheet("color: blue")
		self.filenameEdit = QtGui.QLineEdit("",self)
		self.folderEdit = QtGui.QLineEdit("",self)
		
		self.cb_save_figs = QtGui.QCheckBox('Save figs',self)
		self.cb_save_figs.toggle()
		
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
		g1_1.addWidget(self.cb_sub_olis,2,2)
		g1_1.addWidget(loadSubFilmOlis_lbl,3,0)
		g1_1.addWidget(self.loadSubFilmOlisFile_lbl,3,1)
		g1_1.addWidget(self.cb_subfilm_olis,3,2)
		g1_1.addWidget(loadSubFTIR_lbl,4,0)
		g1_1.addWidget(self.loadSubFTIRFile_lbl,4,1)
		g1_1.addWidget(self.cb_sub_ftir,4,2)
		g1_1.addWidget(loadSubFilmFTIR_lbl,5,0)
		g1_1.addWidget(self.loadSubFilmFTIRFile_lbl,5,1)
		g1_1.addWidget(self.cb_subfilm_ftir,5,2)
		
		g1_8 = QtGui.QGridLayout()
		g1_8.addWidget(lbl3,0,0)
		g1_8.addWidget(interpol_lbl,1,0)
		g1_8.addWidget(self.combo4,1,1)
		g1_8.addWidget(strongabs_lbl,2,0)
		g1_8.addWidget(self.strongabsEdit,2,1)
		
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
		g4_0.addWidget(self.cb_save_figs,0,1)
		g4_1 = QtGui.QGridLayout()
		g4_1.addWidget(self.filenameEdit,0,0)
		g4_1.addWidget(self.folderEdit,0,1)
		
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
		g1_7.addWidget(Step0_lbl,0,0)
		g1_7.addWidget(self.Step0_Button,0,1)
		g1_7.addWidget(Step1_lbl,1,0)
		g1_7.addWidget(self.Step1_Button,1,1)
		g1_7.addWidget(Step2_lbl,2,0)
		g1_7.addWidget(self.Step2_Button,2,1)
		g1_7.addWidget(Step3_lbl,3,0)
		g1_7.addWidget(self.Step3_Button,3,1)
		g1_7.addWidget(Step4_lbl,4,0)
		g1_7.addWidget(self.Step4_Button,4,1)
		g1_7.addWidget(Step5_lbl,5,0)
		g1_7.addWidget(self.Step5_Button,5,1)
		g1_7.addWidget(Step6_lbl,6,0)
		g1_7.addWidget(self.Step6_Button,6,1)
		
		g1_8 = QtGui.QGridLayout()
		g1_8.addWidget(NewFiles_lbl,0,0)
		for i in range(5):
			g1_8.addWidget(self.NewFiles[i],1+i,0)
		
		v0 = QtGui.QVBoxLayout()
		v0.addLayout(g1_6)
		v0.addLayout(g1_7)
		v0.addLayout(g1_8)
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		hbox = QtGui.QHBoxLayout()
		hbox.addLayout(v1)
		hbox.addLayout(v0)
		self.setLayout(hbox) 
		
		###############################################################################
		
		# reacts to choises picked in the menu
		self.combo1.activated[str].connect(self.onActivated1)
		self.combo4.activated[str].connect(self.onActivated4)
		
		# reacts to choises picked in the menu
		self.Step0_Button.clicked.connect(self.set_run)
		self.Step1_Button.clicked.connect(self.set_run)
		self.Step2_Button.clicked.connect(self.set_run)
		self.Step3_Button.clicked.connect(self.set_run)
		self.Step4_Button.clicked.connect(self.set_run)
		self.Step5_Button.clicked.connect(self.set_run)
		self.Step6_Button.clicked.connect(self.set_run)
		
		# reacts to choises picked in the checkbox
		self.cb_sub_olis.stateChanged.connect(self.sub_olis_check)
		self.cb_subfilm_olis.stateChanged.connect(self.subfilm_olis_check)
		self.cb_sub_ftir.stateChanged.connect(self.sub_ftir_check)
		self.cb_subfilm_ftir.stateChanged.connect(self.subfilm_ftir_check)
		self.cb_save_figs.stateChanged.connect(self.save_figs_check)
		
		self.set_field_vals()
		self.allButtons_torf(True)
		
		self.move(0,0)
		#self.setGeometry(100, 100, 1300, 800)
		self.setWindowTitle("Swanepoel method for determination of thickness and optical constants for thin films")
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
		
		self.sub_olis_check(self.loadSubOlis_check)
		self.cb_sub_olis.setChecked(self.loadSubOlis_check)
		
		self.subfilm_olis_check(self.loadSubFilmOlis_check)
		self.cb_subfilm_olis.setChecked(self.loadSubFilmOlis_check)
		
		self.sub_ftir_check(self.loadSubFTIR_check)
		self.cb_sub_ftir.setChecked(self.loadSubFTIR_check)
		
		self.subfilm_ftir_check(self.loadSubFilmFTIR_check)
		self.cb_subfilm_ftir.setChecked(self.loadSubFilmFTIR_check)
		
		self.save_figs_check(self.save_figs)
		self.cb_save_figs.setChecked(self.save_figs)
		
		##############################################
		
		self.combo4.setCurrentIndex(self.mylist4.index(self.fit_linear_spline))
		
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
		button.setFixedWidth(250)
		button.setFixedHeight(65)		
	
	def loadConfig(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Load Config File Dialog',self.config_file)
		
		if fname:
			self.config_file = str(fname)
			head, tail = os.path.split(str(fname))
			sys.path.insert(0, head)
			self.set_load_config(tail)
			
	def saveConfig(self):
		
		fname = QtGui.QFileDialog.getSaveFileName(self, 'Save Config File Dialog',self.config_file)
		
		if fname:
			self.config_file = str(fname)
			head, tail = os.path.split(str(fname))
			sys.path.insert(0, head)
			self.set_save_config()
	
	def loadSubOlisDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file',self.loadSubOlis_str)
		
		if fname:
			self.loadSubOlis_str = str(fname)
			head, tail = os.path.split(str(fname))
			self.loadSubOlisFile_lbl.setText(tail)
			
	def loadSubFilmOlisDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file',self.loadSubFilmOlis_str)
		
		if fname:
			self.loadSubFilmOlis_str = str(fname)
			head, tail = os.path.split(str(fname))
			self.loadSubFilmOlisFile_lbl.setText(tail)
			
	def loadSubFTIRDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file',self.loadSubFTIR_str)
		
		if fname:
			self.loadSubFTIR_str = str(fname)
			head, tail = os.path.split(str(fname))
			self.loadSubFTIRFile_lbl.setText(tail)
			
	def loadSubFilmFTIRDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file',self.loadSubFilmFTIR_str)
		
		if fname:
			self.loadSubFilmFTIR_str = str(fname)
			head, tail = os.path.split(str(fname))
			self.loadSubFilmFTIRFile_lbl.setText(tail)
	
	def onActivated1(self, text):
		
		self.fit_poly_order = int(text)
	
	def onActivated4(self, text):
		
		self.fit_linear_spline=str(text)



	def save_figs_check(self, state):
		  
		if state in [QtCore.Qt.Checked,True]:
			self.save_figs=True
		else:
			self.save_figs=False

	def sub_olis_check(self, state):
		  
		if state in [QtCore.Qt.Checked,True]:
			self.loadSubOlisFile_lbl.setStyleSheet("color: magenta")
			self.cb_sub_olis.setText('inc')
		else:
			self.loadSubOlisFile_lbl.setStyleSheet("color: grey")
			self.cb_sub_olis.setText('exc')
			
	def subfilm_olis_check(self, state):
		  
		if state in [QtCore.Qt.Checked,True]:
			self.loadSubFilmOlisFile_lbl.setStyleSheet("color: magenta")
			self.cb_subfilm_olis.setText('inc')
		else:
			self.loadSubFilmOlisFile_lbl.setStyleSheet("color: grey")
			self.cb_subfilm_olis.setText('exc')
			
	def sub_ftir_check(self, state):

		if state in [QtCore.Qt.Checked,True]:
			self.loadSubFTIRFile_lbl.setStyleSheet("color: magenta")
			self.cb_sub_ftir.setText('inc')
		else:
			self.loadSubFTIRFile_lbl.setStyleSheet("color: grey")
			self.cb_sub_ftir.setText('exc')
			
	def subfilm_ftir_check(self, state):

		if state in [QtCore.Qt.Checked,True]:
			self.loadSubFilmFTIRFile_lbl.setStyleSheet("color: magenta")
			self.cb_subfilm_ftir.setText('inc')
		else:
			self.loadSubFilmFTIRFile_lbl.setStyleSheet("color: grey")
			self.cb_subfilm_ftir.setText('exc')

	def cb_check(self):

		a = self.cb_sub_olis.isChecked()
		b = self.cb_subfilm_olis.isChecked()
		c = self.cb_sub_ftir.isChecked()
		d = self.cb_subfilm_ftir.isChecked()

		return a,b,c,d
	
	
  
	def set_run(self):
		
		self.set_save_config()
		sender = self.sender()
		a,b,c,d = self.cb_check()

		if a and not self.loadSubOlis_str:
			QtGui.QMessageBox.warning(self, 'Message', "Selected file path is empty. Load subRAW Olis file!")
			return None

		if b and not self.loadSubFilmOlis_str:
			QtGui.QMessageBox.warning(self, 'Message', "Selected file path is empty. Load subfilmRAW Olis file!")
			return None

		if c and not self.loadSubFTIR_str:
			QtGui.QMessageBox.warning(self, 'Message', "Selected file path is empty. Load subRAW FTIR file!")
			return None

		if d and not self.loadSubFilmFTIR_str:
			QtGui.QMessageBox.warning(self, 'Message', "Selected file path is empty. Load subfilmRAW FTIR file!")
			return None



		if sender.text()!='Plot raw data':
			
			## raw data files warnings and errors
			if not a and not b:
				pass
			elif a and b:
				pass
			else:
				QtGui.QMessageBox.warning(self, 'Message', "Select both OLIS data files subfilmRAW and subRAW!")
				return None
			
			if not c and not d:
				pass
			elif c and d:
				pass
			else:
				QtGui.QMessageBox.warning(self, 'Message', "Select both FTIR data files subfilmRAW and subRAW!")
				return None
			
			if not a and not b and not c and not d:
				QtGui.QMessageBox.warning(self, 'Message', "No data files selected!")
				return None
			
			## gaussian_borders and gaussian_factors warnings and errors
			if len(self.gaussian_borders) < 2:
				QtGui.QMessageBox.warning(self, 'Message', "You must enter at least 2 gaussian borders and at least 1 gaussian factor!")
				return None
			
			for tals in self.gaussian_factors:
				if tals<0:
					QtGui.QMessageBox.warning(self, 'Message', "Gaussian factors must be positive or zero!")
					return None
					
			if len(self.gaussian_borders) != len(self.gaussian_factors)+1:
				QtGui.QMessageBox.warning(self, 'Message', "The number of gaussian factors is exactly one less than the number of gaussian borders!")
				return None
			
			if not numpy.array_equal(self.gaussian_borders,numpy.sort(self.gaussian_borders)):
				QtGui.QMessageBox.warning(self, 'Message', "The gaussian borders must be entered in ascending order!")
				return None
			
			## index_m1_sections warnings and errors
			if len(self.index_m1_sections)<2:
				QtGui.QMessageBox.warning(self, 'Message', "The order no. m1 section list accepts minimum 2 enteries!")
				return None
			elif len(self.index_m1_sections)%2!=0:
				QtGui.QMessageBox.warning(self, 'Message', "The order no. m1 section list accepts only even number of enteries!")
				return None
			
			if not numpy.array_equal(self.index_m1_sections,numpy.sort(self.index_m1_sections)):
				QtGui.QMessageBox.warning(self, 'Message', "The order no. m1 section list must be entered in ascending order!")
				return None
			
			if len(self.index_m1_sections)==0:
				QtGui.QMessageBox.warning(self, 'Message', "The order no. m1 section list is empty! All points will be used to find the polyfit curve!")
		
			
			## fit_poly_ranges warnings and errors
			if len(self.fit_poly_ranges)<2:
				QtGui.QMessageBox.warning(self, 'Message', "The polyfit list accepts minimum 2 enteries!")
				return None
			elif len(self.fit_poly_ranges)%2!=0:
				QtGui.QMessageBox.warning(self, 'Message', "The polyfit list accepts only even number of enteries!")
				return None
			
			if not numpy.array_equal(self.fit_poly_ranges,numpy.sort(self.fit_poly_ranges)):
				QtGui.QMessageBox.warning(self, 'Message', "The polyfit list must be entered in ascending order!")
				return None
			
			if len(self.fit_poly_ranges)==0:
				QtGui.QMessageBox.warning(self, 'Message', "The polyfit list is empty! All points will be used to fit n2 curve!")
			
			## strong_abs_start_eV warings and errors
			if self.strong_abs_start_eV <= 0:
				QtGui.QMessageBox.warning(self, 'Message', "Strong absorption start entery can not be zero or negative!")
				return None
			elif not self.strong_abs_start_eV:
				QtGui.QMessageBox.warning(self, 'Message', "Strong absorption start entery is empty. Strong absorption will start from the last extrema determined by the program.")
		
		if sender.text()=='Plot raw data':
			
			self.button_style(self.Step0_Button,'red')
			self.button_style(self.Step1_Button,'grey')
			self.button_style(self.Step2_Button,'grey')
			self.button_style(self.Step3_Button,'grey')
			self.button_style(self.Step4_Button,'grey')
			self.button_style(self.Step5_Button,'grey')
			self.button_style(self.Step6_Button,'grey')
		
		elif sender.text()=='Find Tmin and Tmax':
			
			self.button_style(self.Step1_Button,'red')
			self.button_style(self.Step0_Button,'grey')
			self.button_style(self.Step2_Button,'grey')
			self.button_style(self.Step3_Button,'grey')
			self.button_style(self.Step4_Button,'grey')
			self.button_style(self.Step5_Button,'grey')
			self.button_style(self.Step6_Button,'grey')

		elif sender.text()=='Find order no. m1':
			
			self.button_style(self.Step3_Button,'red')
			self.button_style(self.Step0_Button,'grey')
			self.button_style(self.Step1_Button,'grey')
			self.button_style(self.Step2_Button,'grey')
			self.button_style(self.Step4_Button,'grey')
			self.button_style(self.Step5_Button,'grey')
			self.button_style(self.Step6_Button,'grey')
		
		elif sender.text()=='Plot n':
			
			self.button_style(self.Step2_Button,'red')
			self.button_style(self.Step0_Button,'grey')
			self.button_style(self.Step1_Button,'grey')
			self.button_style(self.Step3_Button,'grey')
			self.button_style(self.Step4_Button,'grey')
			self.button_style(self.Step5_Button,'grey')
			self.button_style(self.Step6_Button,'grey')
		
		elif sender.text()=='Plot absorption':
			
			self.button_style(self.Step4_Button,'red')
			self.button_style(self.Step0_Button,'grey')
			self.button_style(self.Step1_Button,'grey')
			self.button_style(self.Step2_Button,'grey')
			self.button_style(self.Step3_Button,'grey')
			self.button_style(self.Step5_Button,'grey')
			self.button_style(self.Step6_Button,'grey')
		
		elif sender.text()=='Plot wavenumber k':
			
			self.button_style(self.Step5_Button,'red')
			self.button_style(self.Step0_Button,'grey')
			self.button_style(self.Step1_Button,'grey')
			self.button_style(self.Step2_Button,'grey')
			self.button_style(self.Step3_Button,'grey')
			self.button_style(self.Step4_Button,'grey')
			self.button_style(self.Step6_Button,'grey')
			
		elif sender.text()=='Plot sensitivity':
			
			self.button_style(self.Step6_Button,'red')
			self.button_style(self.Step0_Button,'grey')
			self.button_style(self.Step1_Button,'grey')
			self.button_style(self.Step2_Button,'grey')
			self.button_style(self.Step3_Button,'grey')
			self.button_style(self.Step4_Button,'grey')
			self.button_style(self.Step5_Button,'grey')
		
		self.get_my_Thread=my_Thread(sender.text())
		self.connect(self.get_my_Thread,SIGNAL("pass_plots(PyQt_PyObject,PyQt_PyObject)"),self.pass_plots)
		self.connect(self.get_my_Thread,SIGNAL('finished()'),self.set_finished)

		self.allButtons_torf(False)

		self.get_my_Thread.start()

	def pass_plots(self,my_obj,sender):
		
		for tal in range(5):
			self.NewFiles[tal].setText(''.join([str(tal+1),': ']))
		
		if sender=='Plot raw data':
			data_names=my_obj.plot_raw()
		else:
			data_names=my_obj.make_plots()
			
		for i,ii in zip(data_names,range(len(data_names))):
			self.NewFiles[ii].setText(''.join([str(ii+1),': ',i]))
			
		my_obj.show_plots()
			
	def set_save_config(self):
		
		self.timestr=time.strftime("%y%m%d-%H%M")
		self.lcd.display(self.timestr)
		
		a,b,c,d = self.cb_check()
		
		with open(''.join([self.config_file]), 'w') as thefile:
			# film+substrate measurements
			thefile.write( ''.join(["loadSubOlis=[\"",self.loadSubOlis_str,"\",", str(a),"]\n"]))
			thefile.write( ''.join(["loadSubFilmOlis=[\"",self.loadSubFilmOlis_str,"\",", str(b),"]\n"]))
			thefile.write( ''.join(["loadSubFTIR=[\"",self.loadSubFTIR_str,"\",", str(c),"]\n"]))
			thefile.write( ''.join(["loadSubFilmFTIR=[\"",self.loadSubFilmFTIR_str,"\",", str(d),"]\n"]))
			
			thefile.write( ''.join(["fit_linear_spline=\"",self.fit_linear_spline,"\"\n"]))
			thefile.write( ''.join(["gaussian_factors=[",str(self.factorsEdit.text()),"]\n"]))
			thefile.write( ''.join(["gaussian_borders=[",str(self.bordersEdit.text()),"]\n"]))
			thefile.write( ''.join(["index_m1_sections=[",str(self.m1_bordersEdit.text()),"]\n"]))
			thefile.write( ''.join(["strong_abs_start_eV=",str(self.strongabsEdit.text()),"\n"]))
			thefile.write( ''.join(["fit_poly_order=",str(self.fit_poly_order),"\n"]))
			thefile.write( ''.join(["fit_poly_ranges=[",str(self.poly_bordersEdit.text()),"]\n"]))

			thefile.write( ''.join(["filename=\"",str(self.filenameEdit.text()),"\"\n"]))
			thefile.write( ''.join(["folder=\"",str(self.folderEdit.text()),"\"\n"]))
			thefile.write( ''.join(["timestr=\"",self.timestr,"\"\n"]))	
			thefile.write( ''.join(["save_figs=",str(self.save_figs)]))
	
		mymodule=reload(self.cf)
		
		# load all relevant parameters
		self.loadSubOlis_str = mymodule.loadSubOlis[0]
		self.loadSubFilmOlis_str = mymodule.loadSubFilmOlis[0]
		self.loadSubFTIR_str = mymodule.loadSubFTIR[0]
		self.loadSubFilmFTIR_str = mymodule.loadSubFilmFTIR[0] 
		
		self.loadSubOlis_check = mymodule.loadSubOlis[1]
		self.loadSubFilmOlis_check = mymodule.loadSubFilmOlis[1]
		self.loadSubFTIR_check = mymodule.loadSubFTIR[1]
		self.loadSubFilmFTIR_check = mymodule.loadSubFilmFTIR[1] 
		
		self.fit_linear_spline=mymodule.fit_linear_spline
		self.strong_abs_start_eV=mymodule.strong_abs_start_eV
		self.gaussian_factors=mymodule.gaussian_factors
		self.gaussian_borders=mymodule.gaussian_borders
		self.index_m1_sections=mymodule.index_m1_sections
		self.fit_poly_order=mymodule.fit_poly_order
		self.fit_poly_ranges=mymodule.fit_poly_ranges
		
		self.filename_str=mymodule.filename
		self.folder_str=mymodule.folder
		self.timestr=mymodule.timestr
		self.save_figs=mymodule.save_figs
	
	
	def set_load_config(self,tail):
		
		with open("config_Swanepoel.py", 'w') as thefile:
			thefile.write( ''.join(["current_config_file=\"",self.config_file,"\""]))
			
		self.cf = __import__(tail[:-3])
		
		self.loadSubOlis_str = self.cf.loadSubOlis[0]
		self.loadSubFilmOlis_str = self.cf.loadSubFilmOlis[0]
		self.loadSubFTIR_str = self.cf.loadSubFTIR[0]
		self.loadSubFilmFTIR_str = self.cf.loadSubFilmFTIR[0] 

		self.loadSubOlis_check = self.cf.loadSubOlis[1]
		self.loadSubFilmOlis_check = self.cf.loadSubFilmOlis[1]
		self.loadSubFTIR_check = self.cf.loadSubFTIR[1]
		self.loadSubFilmFTIR_check = self.cf.loadSubFilmFTIR[1]
		
		self.fit_linear_spline=self.cf.fit_linear_spline
		self.gaussian_factors=self.cf.gaussian_factors
		self.gaussian_borders=self.cf.gaussian_borders
		self.index_m1_sections=self.cf.index_m1_sections
		self.strong_abs_start_eV=self.cf.strong_abs_start_eV
		self.fit_poly_order=self.cf.fit_poly_order
		self.fit_poly_ranges=self.cf.fit_poly_ranges
		
		self.filename_str=self.cf.filename
		self.folder_str=self.cf.folder
		self.timestr=self.cf.timestr
		self.save_figs=self.cf.save_figs
		
		self.set_field_vals()
	
	def set_finished(self):
		
		self.button_style(self.Step0_Button,'black')
		self.button_style(self.Step1_Button,'black')
		self.button_style(self.Step2_Button,'black')
		self.button_style(self.Step3_Button,'black')
		self.button_style(self.Step4_Button,'black')
		self.button_style(self.Step5_Button,'black')
		self.button_style(self.Step6_Button,'black')
		self.allButtons_torf(True)
	
	def allButtons_torf(self,trueorfalse):
		
		self.cb_sub_olis.setEnabled(trueorfalse)
		self.cb_subfilm_olis.setEnabled(trueorfalse)
		self.cb_sub_ftir.setEnabled(trueorfalse)
		self.cb_subfilm_ftir.setEnabled(trueorfalse)
		self.cb_save_figs.setEnabled(trueorfalse)
		
		self.Step0_Button.setEnabled(trueorfalse)
		self.Step1_Button.setEnabled(trueorfalse)
		self.Step2_Button.setEnabled(trueorfalse)
		self.Step3_Button.setEnabled(trueorfalse)
		self.Step4_Button.setEnabled(trueorfalse)
		self.Step5_Button.setEnabled(trueorfalse)
		self.Step6_Button.setEnabled(trueorfalse)
		
		self.combo1.setEnabled(trueorfalse)
		self.combo4.setEnabled(trueorfalse)
		
		self.factorsEdit.setEnabled(trueorfalse)
		self.bordersEdit.setEnabled(trueorfalse)
		self.m1_bordersEdit.setEnabled(trueorfalse)
		self.poly_bordersEdit.setEnabled(trueorfalse)
		
		self.filenameEdit.setEnabled(trueorfalse)
		self.folderEdit.setEnabled(trueorfalse)
		
	def closeEvent(self,event):
		
		reply = QtGui.QMessageBox.question(self, 'Message', "Quit now?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes:
			event.accept()
		else:
			event.ignore()  
	
#########################################
#########################################
#########################################

def main():
	
	app = QtGui.QApplication(sys.argv)
	ex = Run_CM110()
	sys.exit(app.exec_())

if __name__ == '__main__':
	
	main()