#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""


import matplotlib.pyplot as plt
import os, sys, re, time, numpy, yagmail, configparser, pathlib

from PyQt5.QtCore import QObject, QThreadPool, QTimer, QRunnable, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QDialog, QWidget, QMainWindow, QCheckBox, QLCDNumber, QMessageBox, QGridLayout,
														 QInputDialog, QLabel, QLineEdit, QComboBox, QVBoxLayout,
														 QHBoxLayout, QApplication, QMenuBar, QPushButton, QFileDialog)

import Email_settings_dialog, Send_email_dialog, Load_config_dialog





class WorkerSignals(QObject):
	# Create signals to be used
	lcd = pyqtSignal(object)
	pass_plots = pyqtSignal(object)
	
	error = pyqtSignal(object)
	finished = pyqtSignal()
	
	
	
class Worker(QRunnable):
	'''
	Worker thread
	:param args: Arguments to make available to the run code
	:param kwargs: Keywords arguments to make available to the run code
	'''
	def __init__(self, *argv):
		super(Worker, self).__init__()
		
		self.sender = argv[0]
		self.cwd = argv[1]
		
		self.signals = WorkerSignals()
		
		
	def abort(self):
		self.abort_flag=True
		
		
	@pyqtSlot()
	def run(self):
		try:
			if self.sender=='Raw data':
				import get_raw
				my_arg = get_raw.Get_raw(self.cwd)
				
			elif self.sender=='Tmin and Tmax':
				import get_Tmax_Tmin
				my_arg = get_Tmax_Tmin.Get_Tmax_Tmin(self.cwd)
				
			elif self.sender=='Std.Dev. in d':
				import get_vary_igp
				my_arg = get_vary_igp.Vary_igp(self.cwd)
				
			elif self.sender=='Index n':
				import get_m_d
				my_arg = get_m_d.Gmd(self.cwd)
				
			elif self.sender=='Absorption alpha':
				import alpha
				my_arg = alpha.Alpha(self.cwd)
				
			elif self.sender=='Wavenumber k':
				import k
				my_arg = k.K_class(self.cwd)
				
			self.signals.pass_plots.emit([my_arg, self.sender])

		except Exception as inst:
			
			self.signals.error.emit(str(inst))

		self.signals.finished.emit()









class Run_gui(QMainWindow):

	def __init__(self):
		super().__init__()
		self.cwd = os.getcwd()
		print(self.cwd,"\n")
		
		self.initUI()
			
	def initUI(self):
		
    ################### MENU BARS START ##################
		MyBar = QMenuBar(self)

		fileMenu = MyBar.addMenu("File")

		self.fileSave = fileMenu.addAction("Save thinfilm config")        
		self.fileSave.triggered.connect(self.set_save_config) 
		self.fileSave.setShortcut('Ctrl+S')

		self.fileSaveAs = fileMenu.addAction("Add config section")        
		self.fileSaveAs.triggered.connect(self.addConfigSec)  

		self.fileLoadAs = fileMenu.addAction("Load config section")        
		self.fileLoadAs.triggered.connect(self.load_config_dialog)

		fileClose = fileMenu.addAction("Close")        
		fileClose.triggered.connect(self.close) # triggers closeEvent()
		fileClose.setShortcut('Ctrl+X')

		self.loadMenu = MyBar.addMenu("Load data")
		loadSubOlis = self.loadMenu.addAction("OLIS sub")
		loadSubFilmOlis = self.loadMenu.addAction("OLIS sub + thin film")
		loadSubFTIR = self.loadMenu.addAction("FTIR sub")
		loadSubFilmFTIR = self.loadMenu.addAction("FTIR sub + thin film")

		loadSubOlis.triggered.connect(self.loadSubOlisDialog)
		loadSubFilmOlis.triggered.connect(self.loadSubFilmOlisDialog)
		loadSubFTIR.triggered.connect(self.loadSubFTIRDialog)
		loadSubFilmFTIR.triggered.connect(self.loadSubFilmFTIRDialog)

		self.removeMenu = MyBar.addMenu("Remove data")
		removeSubOlis = self.removeMenu.addAction("OLIS sub")
		removeSubFilmOlis = self.removeMenu.addAction("OLIS sub + thin film")
		removeSubFTIR = self.removeMenu.addAction("FTIR sub")
		removeSubFilmFTIR = self.removeMenu.addAction("FTIR sub + thin film")

		removeSubOlis.triggered.connect(self.removeSubOlisDialog)
		removeSubFilmOlis.triggered.connect(self.removeSubFilmOlisDialog)
		removeSubFTIR.triggered.connect(self.removeSubFTIRDialog)
		removeSubFilmFTIR.triggered.connect(self.removeSubFilmFTIRDialog)

		self.emailMenu = MyBar.addMenu("E-mail")
		self.emailSettings = self.emailMenu.addAction("E-mail settings")
		self.emailSettings.triggered.connect(self.email_set_dialog)
		self.emailData = self.emailMenu.addAction("E-mail data")
		self.emailData.triggered.connect(self.email_data_dialog)

		helpMenu = MyBar.addMenu("Help")
		helpParam = helpMenu.addAction("Instructions")
		helpParam.triggered.connect(self.helpParamDialog)
		contact = helpMenu.addAction("Contact")
		contact.triggered.connect(self.contactDialog)

		################### MENU BARS END ##################

		# status info which button has been pressed
		Start_lbl = QLabel("ANALYSIS steps and plots", self)
		Start_lbl.setStyleSheet("color: blue")

		self.Step0_Button = QPushButton("Raw data",self)
		self.Step0_Button.setToolTip("STEP 0. Plot raw data for OLIS and FTIR")
		self.button_style(self.Step0_Button,'black')

		self.Step1_Button = QPushButton("Tmin and Tmax",self)
		self.Step1_Button.setToolTip("STEP 1. Find all the minima and maxima positions using Gaussian filter")
		self.button_style(self.Step1_Button,'black')

		self.Step2_Button = QPushButton("Std.Dev. in d",self)
		self.Step2_Button.setToolTip("STEP 2. Minimize standard deviation in the film thickness d")
		self.button_style(self.Step2_Button,'black')

		self.Step3_Button = QPushButton("Index n",self)
		self.Step3_Button.setToolTip("STEP 3. Plot refractive indicies n1 and n2")
		self.button_style(self.Step3_Button,'black')

		self.Step4_Button = QPushButton("Absorption alpha",self)
		self.Step4_Button.setToolTip("STEP 4. Plot abosorption alpha based on n2")
		self.button_style(self.Step4_Button,'black')

		self.Step5_Button = QPushButton("Wavenumber k",self)
		self.Step5_Button.setToolTip("STEP 5. Plot wavenumber k based on n2")
		self.button_style(self.Step5_Button,'black')

		####################################################

		# status info which button has been pressed
		self.NewFiles = QLabel('No files created yet!', self)
		self.NewFiles.setStyleSheet("color: blue")
		
		newfont = QFont("Times", 9, QFont.Normal) 
		self.NewFiles.setFont(newfont)
		
		'''
		self.NewFiles = numpy.zeros(5,dtype=object)
		for i in range(4):
			self.NewFiles[i] = QLabel(''.join([str(i+1),': ']), self)
			self.NewFiles[i].setStyleSheet("color: magenta")
		'''
			
		####################################################
		loads_lbl = QLabel("RAW data files", self)
		loads_lbl.setStyleSheet("color: blue")

		configFile_lbl = QLabel("Current thinfilm", self)
		self.config_file_lbl = QLabel("", self)
		self.config_file_lbl.setStyleSheet("color: green")

		loadSubOlis_lbl = QLabel("OLIS sub", self)
		self.loadSubOlisFile_lbl = QLabel("", self)
		self.loadSubOlisFile_lbl.setStyleSheet("color: magenta")
			
		loadSubFilmOlis_lbl = QLabel("OLIS sub + thin film", self)
		self.loadSubFilmOlisFile_lbl = QLabel("", self)
		self.loadSubFilmOlisFile_lbl.setStyleSheet("color: magenta")

		loadSubFTIR_lbl = QLabel("FTIR sub", self)
		self.loadSubFTIRFile_lbl = QLabel("", self)
		self.loadSubFTIRFile_lbl.setStyleSheet("color: magenta")

		loadSubFilmFTIR_lbl = QLabel("FTIR sub + thin film", self)
		self.loadSubFilmFTIRFile_lbl = QLabel("", self)
		self.loadSubFilmFTIRFile_lbl.setStyleSheet("color: magenta")

		self.cb_sub_olis = QCheckBox('',self)
		self.cb_sub_olis.toggle()
		self.cb_subfilm_olis = QCheckBox('',self)
		self.cb_subfilm_olis.toggle()
		self.cb_sub_ftir = QCheckBox('',self)
		self.cb_sub_ftir.toggle()
		self.cb_subfilm_ftir = QCheckBox('',self)
		self.cb_subfilm_ftir.toggle()

		plot_X_lbl = QLabel("Plot X axis in", self)
		self.combo2 = QComboBox(self)
		self.mylist2=["eV","nm"]
		self.combo2.addItems(self.mylist2)
		self.combo2.setFixedWidth(70)

		####################################################

		lbl1 = QLabel("GAUSSIAN filter settings", self)
		lbl1.setStyleSheet("color: blue")

		interpol_lbl = QLabel("Interpolation method", self)
		self.combo4 = QComboBox(self)
		self.mylist4=["spline","linear"]
		self.combo4.setToolTip("Interpolation method for local minima Tmin and local maxima Tmax can only be linear or spline.")
		self.combo4.addItems(self.mylist4)
		self.combo4.setFixedWidth(70)

		factors_lbl = QLabel("Gaussian factors", self)
		self.factorsEdit = QLineEdit("",self)
		self.factorsEdit.setToolTip("HIGH gaussian factor = broadband noise filtering.\nLOW gaussian factor = narrowband noise filtering.\nHigh gauissian factors (>2) will result in relatively large deviation from the raw data.\nGauissian factors of zero or near zero (<0.5) will closely follow trend of the raw data.")
		self.factorsEdit.setFixedWidth(200)

		borders_lbl = QLabel("Gaussian borders [eV]", self)
		self.bordersEdit = QLineEdit("",self)
		self.bordersEdit.setToolTip("Gaussian borders should be typed in ascending order and the number of\nborders is always one more compared with the number of Gaussian factors.")
		self.bordersEdit.setFixedWidth(200)

		##############################################

		lbl2 = QLabel("ABSORPTION alpha and n1 and n2", self)
		lbl2.setStyleSheet("color: blue")	

		poly_lbl = QLabel("Polyfit order", self)
		self.combo1 = QComboBox(self)
		self.mylist1=["1","2","3","4","5"]
		self.combo1.addItems(self.mylist1)
		self.combo1.setFixedWidth(70)

		polybord_lbl = QLabel("Polyfit range(s) [eV]", self)
		self.poly_bordersEdit = QLineEdit("", self)
		self.poly_bordersEdit.setFixedWidth(140)

		self.cb_polybord = QCheckBox('',self)
		self.cb_polybord.toggle()

		ignore_data_lbl = QLabel("No. of ignored points", self)
		self.ignore_data_ptsEdit = QLineEdit("",self)
		self.ignore_data_ptsEdit.setFixedWidth(140)

		corr_slit_lbl = QLabel("Correction slit width [nm]", self)
		self.corr_slitEdit = QLineEdit("",self)
		self.corr_slitEdit.setToolTip("Finite spectrometer bandwidth (slit width) in the transmission spectrum.")
		self.corr_slitEdit.setFixedWidth(140)

		##############################################

		lbl4 = QLabel("STORAGE location (folder/file)", self)
		lbl4.setStyleSheet("color: blue")
		self.filenameEdit = QLineEdit("",self)
		#self.filenameEdit.setFixedWidth(180)

		self.cb_save_figs = QCheckBox('Save figs',self)
		self.cb_save_figs.toggle()

		##############################################

		self.lcd = QLCDNumber(self)
		self.lcd.setStyleSheet("color: red")
		self.lcd.setFixedHeight(60)
		self.lcd.setSegmentStyle(QLCDNumber.Flat)
		self.lcd.setToolTip("Timetrace for saving files")
		self.lcd.setNumDigits(11)
			
		##############################################

		# Add all widgets		
		g1_0 = QGridLayout()
		g1_0.addWidget(MyBar,0,0)
		g1_1 = QGridLayout()
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
		g1_1.addWidget(plot_X_lbl,6,0)
		g1_1.addWidget(self.combo2,6,1)

		g1_2 = QGridLayout()
		g1_2.addWidget(lbl1,0,0)
		g1_3 = QGridLayout()
		g1_3.addWidget(interpol_lbl,0,0)
		g1_3.addWidget(self.combo4,0,1)
		g1_3.addWidget(factors_lbl,1,0)
		g1_3.addWidget(self.factorsEdit,1,1)
		g1_3.addWidget(borders_lbl,2,0)
		g1_3.addWidget(self.bordersEdit,2,1)

		g1_4 = QGridLayout()
		g1_4.addWidget(lbl2,0,0)
		g1_5 = QGridLayout()
		g1_5.addWidget(poly_lbl,0,0)
		g1_5.addWidget(self.combo1,0,1)
		g1_5.addWidget(polybord_lbl,1,0)
		g1_5.addWidget(self.poly_bordersEdit,1,1)
		g1_5.addWidget(self.cb_polybord,1,2)
		g1_5.addWidget(ignore_data_lbl,2,0)
		g1_5.addWidget(self.ignore_data_ptsEdit,2,1)
		g1_5.addWidget(corr_slit_lbl,3,0)
		g1_5.addWidget(self.corr_slitEdit,3,1)

		g4_0 = QGridLayout()
		g4_0.addWidget(lbl4,0,0)
		g4_0.addWidget(self.cb_save_figs,0,1)
		g4_1 = QGridLayout()
		g4_1.addWidget(self.filenameEdit,0,0)

		v1 = QVBoxLayout()
		v1.addLayout(g1_0)
		v1.addLayout(g1_1)
		v1.addLayout(g1_2)
		v1.addLayout(g1_3)
		v1.addLayout(g1_4)
		v1.addLayout(g1_5)
		v1.addLayout(g4_0)
		v1.addLayout(g4_1)

		###################################################

		g1_6 = QGridLayout()
		g1_6.addWidget(Start_lbl,0,0)
		g1_7 = QGridLayout()
		g1_7.addWidget(self.Step0_Button,0,0)
		g1_7.addWidget(self.Step1_Button,1,0)
		g1_7.addWidget(self.Step2_Button,2,0)
		g1_7.addWidget(self.Step3_Button,3,0)
		g1_7.addWidget(self.Step4_Button,4,0)
		g1_7.addWidget(self.Step5_Button,5,0)

		g1_8 = QGridLayout()
		g1_8.addWidget(self.NewFiles,0,0)
		g1_8.addWidget(self.lcd,1,0)


		v0 = QVBoxLayout()
		v0.addLayout(g1_6)
		v0.addLayout(g1_7)
		v0.addLayout(g1_8)

		# SET ALL VERTICAL COLUMNS TOGETHER
		hbox = QHBoxLayout()
		hbox.addLayout(v1)
		hbox.addLayout(v0)

		###############################################################################

		# reacts to choises picked in the menu
		self.combo1.activated[str].connect(self.onActivated1)
		self.combo2.activated[str].connect(self.onActivated2)
		self.combo4.activated[str].connect(self.onActivated4)

		# reacts to choises picked in the menu
		self.Step0_Button.clicked.connect(self.set_run)
		self.Step1_Button.clicked.connect(self.set_run)
		self.Step2_Button.clicked.connect(self.set_run)
		self.Step3_Button.clicked.connect(self.set_run)
		self.Step4_Button.clicked.connect(self.set_run)
		self.Step5_Button.clicked.connect(self.set_run)

		# reacts to choises picked in the checkbox
		self.cb_sub_olis.stateChanged.connect(self.sub_olis_check)
		self.cb_subfilm_olis.stateChanged.connect(self.subfilm_olis_check)
		self.cb_sub_ftir.stateChanged.connect(self.sub_ftir_check)
		self.cb_subfilm_ftir.stateChanged.connect(self.subfilm_ftir_check)
		self.cb_save_figs.stateChanged.connect(self.save_figs_check)
		self.cb_polybord.stateChanged.connect(self.polybord_check)
		
		self.set_load_config()
		self.filenameEdit.setText(self.filename_str)
		
		self.threadpool = QThreadPool()
		print("Multithreading in TEST_gui_v1 with maximum %d threads" % self.threadpool.maxThreadCount())
		self.isRunning = False
		
		self.move(0,0)
		#self.setGeometry(50, 50, 800, 500)
		hbox.setSizeConstraint(hbox.SetFixedSize)
		self.setWindowTitle("Swanepoel - thickness and optical constants for thin films")
		
		w = QWidget()
		w.setLayout(hbox)
		self.setCentralWidget(w)
		self.show()
		
		
	def bool_(self,txt):
		
		if txt=="True":
			return True
		elif txt=="False":
			return False
		
		
	def set_field_vals(self):
		
		self.config_file_lbl.setText(self.last_used_scan)
		
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
		if self.loadSubOlis_str=='':
			self.cb_sub_olis.setEnabled(False)
		else:
			self.cb_sub_olis.setEnabled(True)
		
		self.subfilm_olis_check(self.loadSubFilmOlis_check)
		self.cb_subfilm_olis.setChecked(self.loadSubFilmOlis_check)
		if self.loadSubFilmOlis_str=='':
			self.cb_subfilm_olis.setEnabled(False)
		else:
			self.cb_subfilm_olis.setEnabled(True)
		
		self.sub_ftir_check(self.loadSubFTIR_check)
		self.cb_sub_ftir.setChecked(self.loadSubFTIR_check)
		if self.loadSubFTIR_str=='':
			self.cb_sub_ftir.setEnabled(False)
		else:
			self.cb_sub_ftir.setEnabled(True)
		
		self.subfilm_ftir_check(self.loadSubFilmFTIR_check)
		self.cb_subfilm_ftir.setChecked(self.loadSubFilmFTIR_check)
		if self.loadSubFilmFTIR_str=='':
			self.cb_subfilm_ftir.setEnabled(False)
		else:
			self.cb_subfilm_ftir.setEnabled(True)
		
		self.save_figs_check(self.save_figs)
		self.cb_save_figs.setChecked(self.save_figs)
		
		##############################################

		if len(self.fit_poly_ranges)==0:
			self.fit_poly_ranges_check=False
			self.polybord_check(self.fit_poly_ranges_check)
			self.cb_polybord.setChecked(self.fit_poly_ranges_check)
		else:
			self.polybord_check(self.fit_poly_ranges_check)
			self.cb_polybord.setChecked(self.fit_poly_ranges_check)
		
		##############################################
		
		self.factorsEdit.setText(self.gaussian_factors)
		self.bordersEdit.setText(self.gaussian_borders)
		
		##############################################
		
		self.combo1.setCurrentIndex(self.mylist1.index(self.fit_poly_order))
		self.combo2.setCurrentIndex(self.mylist2.index(self.plot_X))
		self.combo4.setCurrentIndex(self.mylist4.index(self.fit_linear_spline))
		
		##############################################
		
		self.poly_bordersEdit.setText(self.fit_poly_ranges)
		self.ignore_data_ptsEdit.setText(self.ignore_data_pts)
		self.corr_slitEdit.setText(self.corr_slit)
		
		##############################################
		
		self.NewFiles.setToolTip(''.join(["Display newly created and saved files in /",self.filename_str,"/"]))
		self.lcd.display(self.timetrace)
		
		
	def button_style(self,button,color):
		
		button.setStyleSheet(''.join(['QPushButton {background-color: lightblue; font-size: 18pt; color: ',color,'}']))
		button.setFixedWidth(230)
		button.setFixedHeight(60)
		
		
	def addConfigSec(self):
		
		sections = ', '.join( self.config.sections() )
		#print(sections)
		text, ok = QInputDialog.getText(self, 'Add Config Section Dialog',''.join(['Sections already registered in the config file:\n', sections ,'\n\nCreate a new config section name:']), text=self.last_used_scan)
		if ok:
			try:
				self.last_used_scan = str(text)
				self.config.add_section(self.last_used_scan)
			except configparser.DuplicateSectionError as e:
				QMessageBox.critical(self, 'Message', str(e))
				return
			
			self.set_save_config()
			self.set_load_config()
			
			
	def loadSubOlisDialog(self):
		
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		files, _ = QFileDialog.getOpenFileNames(self,"Open files",''.join(['data','/']), "All Files (*);;Dat Files (*.dat);;Text Files (*.txt)", options=options)
		for afile in files:
			self.loadSubOlis_str = str(afile)
			head, tail = os.path.split(str(afile))
			self.loadSubOlisFile_lbl.setText(tail)
			self.cb_sub_olis.setEnabled(True)
			
			
	def loadSubFilmOlisDialog(self):
		
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		files, _ = QFileDialog.getOpenFileNames(self,"Open files",''.join(['data','/']), "All Files (*);;Dat Files (*.dat);;Text Files (*.txt)", options=options)
		for afile in files:
			self.loadSubFilmOlis_str = str(afile)
			head, tail = os.path.split(str(afile))
			self.loadSubFilmOlisFile_lbl.setText(tail)
			self.cb_subfilm_olis.setEnabled(True)
			
			
	def loadSubFTIRDialog(self):
		
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		files, _ = QFileDialog.getOpenFileNames(self,"Open files",''.join(['data','/']), "All Files (*);;Dat Files (*.dat);;Text Files (*.txt)", options=options)
		for afile in files:
			self.loadSubFTIR_str = str(afile)
			head, tail = os.path.split(str(afile))
			self.loadSubFTIRFile_lbl.setText(tail)
			self.cb_sub_ftir.setEnabled(True)
			
			
	def loadSubFilmFTIRDialog(self):
		
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		files, _ = QFileDialog.getOpenFileNames(self,"Open files",''.join(['data','/']), "All Files (*);;Dat Files (*.dat);;Text Files (*.txt)", options=options)
		for afile in files:
			self.loadSubFilmFTIR_str = str(afile)
			head, tail = os.path.split(str(afile))
			self.loadSubFilmFTIRFile_lbl.setText(tail)
			self.cb_subfilm_ftir.setEnabled(True)
			
			
	def removeSubOlisDialog(self):
		
		self.loadSubOlis_str = ''
		self.loadSubOlisFile_lbl.setText(self.loadSubOlis_str)
		
		self.loadSubOlis_check=False
		self.sub_olis_check(self.loadSubOlis_check)
		self.cb_sub_olis.setChecked(self.loadSubOlis_check)
		self.cb_sub_olis.setEnabled(False)
			
			
	def removeSubFilmOlisDialog(self):
		
		self.loadSubFilmOlis_str = ''
		self.loadSubFilmOlisFile_lbl.setText(self.loadSubFilmOlis_str)
		
		self.loadSubFilmOlis_check = False
		self.subfilm_olis_check(self.loadSubFilmOlis_check)
		self.cb_subfilm_olis.setChecked(self.loadSubFilmOlis_check)
		self.cb_subfilm_olis.setEnabled(False)
			
			
	def removeSubFTIRDialog(self):
		
		self.loadSubFTIR_str = ''
		self.loadSubFTIRFile_lbl.setText(self.loadSubFTIR_str)
		
		self.loadSubFTIR_check = False
		self.sub_ftir_check(self.loadSubFTIR_check)
		self.cb_sub_ftir.setChecked(self.loadSubFTIR_check)
		self.cb_sub_ftir.setEnabled(False)
			
			
	def removeSubFilmFTIRDialog(self):
		
		self.loadSubFilmFTIR_str = ''
		self.loadSubFilmFTIRFile_lbl.setText(self.loadSubFilmFTIR_str)
		
		self.loadSubFilmFTIR_check = False
		self.subfilm_ftir_check(self.loadSubFilmFTIR_check)
		self.cb_subfilm_ftir.setChecked(self.loadSubFilmFTIR_check)
		self.cb_subfilm_ftir.setEnabled(False)
		
	
	def load_config_dialog(self):
		
		self.Load_config_dialog = Load_config_dialog.Load_config_dialog(self, self.config)
		self.Load_config_dialog.exec()
		
		self.set_load_config()
		
		
	def email_data_dialog(self):
		
		self.Send_email_dialog = Send_email_dialog.Send_email_dialog(self, self.cwd)
		self.Send_email_dialog.exec()
		
		
	def email_set_dialog(self):
		
		self.Email_dialog = Email_settings_dialog.Email_dialog(self, self.lcd, self.cwd)
		self.Email_dialog.exec()
		
		
	def helpParamDialog(self):
		
		helpfile=''
		with open('config_Swanepoel_forklaringer.py','r') as f:
		  for line in f:
		    helpfile = helpfile+line
		
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Information)
		msg.setText("Apply Swanepoel analysis using following steps:")
		msg.setInformativeText(helpfile)
		msg.setWindowTitle("Help")
		#msg.setDetailedText(helpfile)
		msg.setStandardButtons(QMessageBox.Ok)
		#msg.setGeometry(1000, 0, 1000+250, 350)

		msg.exec_()	
	
	def contactDialog(self):

		QMessageBox.information(self, "Contact information","Suggestions, comments or bugs can be reported to vedran.furtula@ntnu.no")
		
		
	def onActivated1(self, text):
		
		self.fit_poly_order = int(text)
		
		
	def onActivated2(self, text):
		
		self.plot_X = str(text)
		
		
	def onActivated4(self, text):
		
		self.fit_linear_spline=str(text)
		
		
	def save_figs_check(self, state):
		  
		if state in [Qt.Checked,True]:
			self.save_figs=True
		else:
			self.save_figs=False
			
			
	def sub_olis_check(self, state):
		  
		if state in [Qt.Checked,True]:
			self.loadSubOlis_check=True
			self.loadSubOlisFile_lbl.setStyleSheet("color: magenta")
			self.cb_sub_olis.setText('incl')
		else:
			self.loadSubOlis_check=False
			self.loadSubOlisFile_lbl.setStyleSheet("color: grey")
			self.cb_sub_olis.setText('exc')
			
			
	def subfilm_olis_check(self, state):
		
		if state in [Qt.Checked,True]:
			self.loadSubFilmOlis_check=True
			self.loadSubFilmOlisFile_lbl.setStyleSheet("color: magenta")
			self.cb_subfilm_olis.setText('incl')
		else:
			self.loadSubFilmOlis_check=False
			self.loadSubFilmOlisFile_lbl.setStyleSheet("color: grey")
			self.cb_subfilm_olis.setText('exc')
			
			
	def sub_ftir_check(self, state):

		if state in [Qt.Checked,True]:
			self.loadSubFTIR_check=True
			self.loadSubFTIRFile_lbl.setStyleSheet("color: magenta")
			self.cb_sub_ftir.setText('incl')
		else:
			self.loadSubFTIR_check=False
			self.loadSubFTIRFile_lbl.setStyleSheet("color: grey")
			self.cb_sub_ftir.setText('exc')
			
			
	def subfilm_ftir_check(self, state):

		if state in [Qt.Checked,True]:
			self.loadSubFilmFTIR_check=True
			self.loadSubFilmFTIRFile_lbl.setStyleSheet("color: magenta")
			self.cb_subfilm_ftir.setText('incl')
		else:
			self.loadSubFilmFTIR_check=False
			self.loadSubFilmFTIRFile_lbl.setStyleSheet("color: grey")
			self.cb_subfilm_ftir.setText('exc')
			
			
	def polybord_check(self, state):

		if state in [Qt.Checked,True]:
			self.fit_poly_ranges_check=True
			self.poly_bordersEdit.setEnabled(True)
			self.cb_polybord.setText('incl')
		else:
			self.fit_poly_ranges_check=False
			self.poly_bordersEdit.setEnabled(False)
			self.cb_polybord.setText('exc')
	
	
	############################################################
	
	
	# Check input if a number, ie. digits or fractions such as 3.141
	# Source: http://www.pythoncentral.io/how-to-check-if-a-string-is-a-number-in-python-including-unicode/
	def is_int(self,s):
		try: 
		  int(s)
		  return True
		except ValueError:
		  return False

	def is_number(self,s):
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
	
	
	def create_file(self,mystr):
		
		head, tail = os.path.split(mystr)
		# Check for possible name conflicts
		if tail:
			saveinfile=''.join([tail,self.timetrace])
		else:
			saveinfile=''.join(["data_",self.timetrace])
			
		if head:
			if not os.path.isdir(head):
				pathlib.Path(head).mkdir(parents=True, exist_ok=True)
			saveinfolder=''.join([head,"/"])
		else:
			saveinfolder=""
		
		self.filename_str = ''.join([saveinfolder,saveinfile])
		
		return ''.join([saveinfolder,saveinfile])
	
	
	def set_run(self):
		
		sender = self.sender()
		
		## gaussian_borders and gaussian_factors warnings and errors
		gaus_bord=str(self.bordersEdit.text()).split(',')
		for tal in gaus_bord:
			if not self.is_number(tal):
				QMessageBox.critical(self, 'Message', "Gaussian borders must be real numbers!")
				return None
			elif float(tal)<0.0:
				QMessageBox.critical(self, 'Message', "Gaussian borders must be positive or zero!")
				return None

		if len(gaus_bord) < 2:
			QMessageBox.critical(self, 'Message', "You must enter at least 2 gaussian borders!")
			return None
		
		if not numpy.array_equal([numpy.float(i) for i in gaus_bord],numpy.sort([numpy.float(i) for i in gaus_bord])):
			QMessageBox.critical(self, 'Message', "The gaussian borders must be entered in the ascending order!")
			return None

		gaus_fact=str(self.factorsEdit.text()).split(',')
		for tal in gaus_fact:
			if not self.is_number(tal):
				QMessageBox.critical(self, 'Message', "Gaussian factors must be real numbers!")
				return None
			elif float(tal)<0.0:
				QMessageBox.critical(self, 'Message', "Gaussian factors must be positive or zero!")
				return None
		
		if len(gaus_fact) < 1:
			QMessageBox.critical(self, 'Message', "You must enter at least 1 gaussian factor!")
			return None
				
		if len(gaus_bord) != len(gaus_fact)+1:
			QMessageBox.critical(self, 'Message', "The number of gaussian factors is exactly one less than the number of gaussian borders!")
			return None


		## ignored data points warnings and errors
		ign_pts=str(self.ignore_data_ptsEdit.text())
		if not self.is_int(ign_pts):
			QMessageBox.critical(self, 'Message', "The number of ignored points is an integer!")
			return None
		elif int(ign_pts)<0:
			QMessageBox.critical(self, 'Message', "The number of ignored points is a positive integer!")
			return None
		
		
		## correction slit width warnings and errors
		corr_pts=str(self.corr_slitEdit.text())
		if not self.is_number(corr_pts):
			QMessageBox.critical(self, 'Message', "The correction slit width is a real number!")
			return None
		elif float(corr_pts)<0:
			QMessageBox.critical(self, 'Message', "The correction slit width is a positive number!")
			return None


		## fit_poly_ranges warnings and errors
		if self.fit_poly_ranges_check==True:
			polyfit_bord=str(self.poly_bordersEdit.text()).split(',')
			for tal in polyfit_bord:
				if not self.is_number(tal):
					QMessageBox.critical(self, 'Message', "The polyfit range enteries must be real numbers!")
					return None
				elif float(tal)<0.0:
					QMessageBox.critical(self, 'Message', "The polyfit range enteries must be positive or zero!")
					return None
				
			if len(polyfit_bord)<2 or len(polyfit_bord)%2!=0:
				QMessageBox.critical(self, 'Message', "The polyfit range list accepts minimum 2 or even number of enteries!")
				return None

			if not numpy.array_equal([numpy.float(i) for i in polyfit_bord],numpy.sort([numpy.float(i) for i in polyfit_bord])):
				QMessageBox.critical(self, 'Message', "The polyfit range list must be entered in ascending order!")
				return None
		
		
		# When all user defined enteries are approved save the data
		self.create_file(str(self.filenameEdit.text()))
		self.set_save_config()
		self.set_load_config()
		
		
		if sender.text()!='Raw data':
			
			## raw data files warnings and errors
			if not self.loadSubOlis_check and not self.loadSubFilmOlis_check:
				pass
			elif self.loadSubOlis_check and self.loadSubFilmOlis_check:
				pass
			else:
				QMessageBox.critical(self, 'Message', "Select both OLIS data files subfilmRAW and subRAW!")
				return None
			
			if not self.loadSubFTIR_check and not self.loadSubFilmFTIR_check:
				pass
			elif self.loadSubFTIR_check and self.loadSubFilmFTIR_check:
				pass
			else:
				QMessageBox.critical(self, 'Message', "Select both FTIR data files subfilmRAW and subRAW!")
				return None
			
			if not self.loadSubOlis_check and not self.loadSubFilmOlis_check and not self.loadSubFTIR_check and not self.loadSubFilmFTIR_check:
				QMessageBox.critical(self, 'Message', "No data files selected!")
				return None

		if sender.text()=='Raw data':
			
			if not self.loadSubOlis_check and not self.loadSubFilmOlis_check and not self.loadSubFTIR_check and not self.loadSubFilmFTIR_check:
				QMessageBox.critical(self, 'Message', "No raw data files selected!")
				return
			
			self.button_style(self.Step0_Button,'red')
			self.button_style(self.Step1_Button,'grey')
			self.button_style(self.Step2_Button,'grey')
			self.button_style(self.Step3_Button,'grey')
			self.button_style(self.Step4_Button,'grey')
			self.button_style(self.Step5_Button,'grey')
			
		elif sender.text()=='Tmin and Tmax':
			
			self.button_style(self.Step1_Button,'red')
			self.button_style(self.Step0_Button,'grey')
			self.button_style(self.Step2_Button,'grey')
			self.button_style(self.Step3_Button,'grey')
			self.button_style(self.Step4_Button,'grey')
			self.button_style(self.Step5_Button,'grey')
			
		elif sender.text()=='Std.Dev. in d':
			
			self.button_style(self.Step2_Button,'red')
			self.button_style(self.Step0_Button,'grey')
			self.button_style(self.Step1_Button,'grey')
			self.button_style(self.Step3_Button,'grey')
			self.button_style(self.Step4_Button,'grey')
			self.button_style(self.Step5_Button,'grey')
			
		elif sender.text()=='Index n':
			
			self.button_style(self.Step3_Button,'red')
			self.button_style(self.Step0_Button,'grey')
			self.button_style(self.Step1_Button,'grey')
			self.button_style(self.Step2_Button,'grey')
			self.button_style(self.Step4_Button,'grey')
			self.button_style(self.Step5_Button,'grey')
			
		elif sender.text()=='Absorption alpha':
			
			self.button_style(self.Step4_Button,'red')
			self.button_style(self.Step0_Button,'grey')
			self.button_style(self.Step1_Button,'grey')
			self.button_style(self.Step2_Button,'grey')
			self.button_style(self.Step3_Button,'grey')
			self.button_style(self.Step5_Button,'grey')
			
		elif sender.text()=='Wavenumber k':
			
			self.button_style(self.Step5_Button,'red')
			self.button_style(self.Step0_Button,'grey')
			self.button_style(self.Step1_Button,'grey')
			self.button_style(self.Step2_Button,'grey')
			self.button_style(self.Step3_Button,'grey')
			self.button_style(self.Step4_Button,'grey')
			
		else:
			return
		
		self.worker = Worker(sender.text(),self.cwd)
		
		self.worker.signals.pass_plots.connect(self.pass_plots)
		self.worker.signals.finished.connect(self.finished)
		
		# Execute
		self.threadpool.start(self.worker)
		
		
	def pass_plots(self,obj):
		
		my_obj, sender = obj
		
		my_str=''
		try:
			self.datafiles=my_obj.make_plots()
			for i,ii in zip(self.datafiles,range(len(self.datafiles))):
				head, tail = os.path.split(i)
				my_str+=''.join([str(ii+1),': ',tail,'\n'])

			self.NewFiles.setText(my_str)
			my_obj.show_plots()
			
		except Exception as inst:
			QMessageBox.critical(self, 'Message', str(inst))
			
			
	def set_load_config(self):
		
		# Initial read of the config file
		self.config = configparser.ConfigParser()
		
		try:
			self.config.read(''.join([self.cwd,os.sep,"config.ini"]))
			self.last_used_scan = self.config.get('LastScan','last_used_scan')
			
			self.loadSubOlis_str = self.config.get(self.last_used_scan,"loadsubolis").strip().split(':')[0]
			self.loadSubOlis_check = self.bool_(self.config.get(self.last_used_scan,'loadsubolis').strip().split(':')[1])
			self.loadSubFilmOlis_str = self.config.get(self.last_used_scan,'loadsubfilmolis').strip().split(':')[0]
			self.loadSubFilmOlis_check = self.bool_(self.config.get(self.last_used_scan,'loadsubfilmolis').strip().split(':')[1])
			self.loadSubFTIR_str = self.config.get(self.last_used_scan,'loadsubftir').strip().split(':')[0]
			self.loadSubFTIR_check = self.bool_(self.config.get(self.last_used_scan,'loadsubftir').strip().split(':')[1])
			self.loadSubFilmFTIR_str = self.config.get(self.last_used_scan,'loadsubfilmftir').strip().split(':')[0]
			self.loadSubFilmFTIR_check = self.bool_(self.config.get(self.last_used_scan,'loadsubfilmftir').strip().split(':')[1])
			self.fit_linear_spline = self.config.get(self.last_used_scan,'fit_linear_spline')
			self.gaussian_factors = self.config.get(self.last_used_scan,'gaussian_factors')
			self.gaussian_borders = self.config.get(self.last_used_scan,'gaussian_borders')
			self.ignore_data_pts = self.config.get(self.last_used_scan,'ignore_data_pts')
			self.corr_slit = self.config.get(self.last_used_scan,'corr_slit')
			self.fit_poly_order = self.config.get(self.last_used_scan,'fit_poly_order')
			self.fit_poly_ranges = self.config.get(self.last_used_scan,'fit_poly_ranges').strip().split(':')[0]
			self.fit_poly_ranges_check = self.bool_(self.config.get(self.last_used_scan,'fit_poly_ranges').strip().split(':')[1])
			self.filename_str = self.config.get(self.last_used_scan,'filename')
			self.timetrace = self.config.get(self.last_used_scan,'timetrace')
			self.save_figs = self.bool_(self.config.get(self.last_used_scan,'save_figs'))
			self.plot_X = self.config.get(self.last_used_scan,'plot_x')
			self.emailset_str = self.config.get(self.last_used_scan,'emailset').strip().split(',')
			self.emailrec_str = self.config.get(self.last_used_scan,'emailrec').strip().split(',')
			
		except configparser.NoOptionError as nov:
			QMessageBox.critical(self, 'Message',''.join(["Main FAULT while reading the config.ini file\n",str(nov)]))
			raise
		
		self.set_field_vals()
		
		
	def set_save_config(self):
		
		self.timetrace=time.strftime("%y%m%d-%H%M")
		self.lcd.display(self.timetrace)
		
		self.config.set('LastScan',"last_used_scan", self.last_used_scan )
		self.config.set(self.last_used_scan,"loadSubOlis", ':'.join([self.loadSubOlis_str, str(self.loadSubOlis_check)]) )
		self.config.set(self.last_used_scan,"loadSubFilmOlis", ':'.join([self.loadSubFilmOlis_str, str(self.loadSubFilmOlis_check)]) )
		self.config.set(self.last_used_scan,"loadSubFTIR", ':'.join([self.loadSubFTIR_str, str(self.loadSubFTIR_check)]) )
		self.config.set(self.last_used_scan,"loadSubFilmFTIR", ':'.join([self.loadSubFilmFTIR_str, str(self.loadSubFilmFTIR_check)]) )
		self.config.set(self.last_used_scan,"fit_linear_spline", self.fit_linear_spline )
		self.config.set(self.last_used_scan,"gaussian_factors", str(self.factorsEdit.text()) )
		self.config.set(self.last_used_scan,"gaussian_borders", str(self.bordersEdit.text()) )
		self.config.set(self.last_used_scan,"ignore_data_pts", str(self.ignore_data_ptsEdit.text()) )
		self.config.set(self.last_used_scan,"corr_slit", str(self.corr_slitEdit.text()) )
		self.config.set(self.last_used_scan,"fit_poly_order", str(self.fit_poly_order) ) 
		self.config.set(self.last_used_scan,"fit_poly_ranges", ':'.join([ str(self.poly_bordersEdit.text()), str(self.fit_poly_ranges_check)]) )
		self.config.set(self.last_used_scan,"filename", str(self.filenameEdit.text()) )
		self.config.set(self.last_used_scan,"timetrace", self.timetrace )	
		self.config.set(self.last_used_scan,"save_figs", str(self.save_figs) )
		self.config.set(self.last_used_scan,"plot_x", self.plot_X )
		self.config.set(self.last_used_scan, 'emailset', ','.join([i for i in self.emailset_str]))
		self.config.set(self.last_used_scan, 'emailrec', ','.join([i for i in self.emailrec_str]))
		
		with open(''.join([self.cwd,os.sep,"config.ini"]), "w") as configfile:
			self.config.write(configfile)
			
			
	def send_notif(self):
		
		try:
			self.yag = yagmail.SMTP(self.emailset_str[0])
			self.yag.send(to=self.emailrec_str, subject="Simulation is done!", contents="Simulation is done.")
		except Exception as e:
			QMessageBox.warning(self, 'Message',''.join(["Could not load the gmail account ",self.emailset_str[0],"! Try following steps:\n1. Check internet connection. Only wired internet will work, ie. no wireless.\n2. Check the account username and password.\n3. Make sure that the account accepts less secure apps."]))
			
			
	def send_data(self):
		print(self.datafiles)
		try:
			self.yag = yagmail.SMTP(self.emailset_str[0])
			mycont=["Simulation is done and the simulated data is attached to this email."]
			mycont.extend(self.datafiles)
			self.yag.send( to=self.emailrec_str, subject="Microstepper data from the latest scan!", contents=mycont )
		except Exception as e:
			QMessageBox.warning(self, 'Message',''.join(["Could not load gmail account ",self.emailset_str[0],"! Try following steps:\n1. Check internet connection. Only wired internet will work, ie. no wireless.\n2. Check the account username and password.\n3. Make sure that the account accepts less secure apps."]))
			
			
	def finished(self):
		
		if self.emailset_str[1] == "yes":
			self.send_notif()
		if self.emailset_str[2] == "yes":
			self.send_data()
			
		self.button_style(self.Step0_Button,'black')
		self.button_style(self.Step1_Button,'black')
		self.button_style(self.Step2_Button,'black')
		self.button_style(self.Step3_Button,'black')
		self.button_style(self.Step4_Button,'black')
		self.button_style(self.Step5_Button,'black')
	
	def allButtons_torf(self,trueorfalse,*argv):
		
		if argv[0]=='allfalse':
			self.cb_sub_olis.setEnabled(False)
			self.cb_subfilm_olis.setEnabled(False)
			self.cb_sub_ftir.setEnabled(False)
			self.cb_subfilm_ftir.setEnabled(False)
			
			self.poly_bordersEdit.setEnabled(False)
			
		self.fileSave.setEnabled(trueorfalse)
		self.fileSaveAs.setEnabled(trueorfalse)
		self.loadMenu.setEnabled(trueorfalse)
		self.emailMenu.setEnabled(trueorfalse)
		self.removeMenu.setEnabled(trueorfalse)
		
		self.cb_save_figs.setEnabled(trueorfalse)
		self.cb_polybord.setEnabled(trueorfalse)
		
		self.Step0_Button.setEnabled(trueorfalse)
		self.Step1_Button.setEnabled(trueorfalse)
		self.Step2_Button.setEnabled(trueorfalse)
		self.Step3_Button.setEnabled(trueorfalse)
		self.Step4_Button.setEnabled(trueorfalse)
		self.Step5_Button.setEnabled(trueorfalse)
		
		self.combo1.setEnabled(trueorfalse)
		self.combo2.setEnabled(trueorfalse)
		self.combo4.setEnabled(trueorfalse)
		
		self.factorsEdit.setEnabled(trueorfalse)
		self.bordersEdit.setEnabled(trueorfalse)
		self.ignore_data_ptsEdit.setEnabled(trueorfalse)
		self.corr_slitEdit.setEnabled(trueorfalse)
		
		self.filenameEdit.setEnabled(trueorfalse)
		
	def closeEvent(self,event):
		
		reply = QMessageBox.question(self, 'Message', "Quit now?", QMessageBox.Yes | QMessageBox.No)
		if reply == QMessageBox.Yes:
			event.accept()
		elif reply == QMessageBox.No:
			event.ignore()  
			
			
#########################################
#########################################
#########################################
	
	
def main():
	
	app = QApplication(sys.argv)
	ex = Run_gui()
	#sys.exit(app.exec_())

	# avoid message 'Segmentation fault (core dumped)' with app.deleteLater()
	app.exec()
	app.deleteLater()
	sys.exit()
	
	
if __name__ == '__main__':
	
	main()
