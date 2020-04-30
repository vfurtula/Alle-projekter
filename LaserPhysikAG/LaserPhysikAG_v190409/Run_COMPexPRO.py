#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 22 10:35:01 2019

@author: Vedran Furtula
"""

import os, sys, re, serial, time, numpy, yagmail, shutil, configparser
import matplotlib.cm as cm
import numpy.polynomial.polynomial as poly
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

import pyqtgraph as pg
import pyqtgraph.exporters

from PyQt5.QtCore import Qt, QObject, QThreadPool, QTimer, QRunnable, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QWidget, QMainWindow, QLCDNumber, QMessageBox, QGridLayout, QHeaderView, QFileDialog, QLabel, QLineEdit, QComboBox, QFrame, QTableWidget, QTableWidgetItem, QSlider, QInputDialog, QVBoxLayout, QHBoxLayout, QApplication, QMenuBar, QPushButton, QDialog)

import Email_settings_dialog, Send_email_dialog, Instruments_dialog, Load_config_dialog, Message_dialog

import COMPexPRO, PM100USBdll

import asyncio







class WorkerSignals(QObject):
	# Create signals to be used
	
	make_update1 = pyqtSignal(object,object,object)
	make_update2 = pyqtSignal(object,object,object)
	make_update3 = pyqtSignal(object,object)
	make_update4 = pyqtSignal(object,object,object)
	make_update5 = pyqtSignal(object,object)
	make_update6 = pyqtSignal(object,object)
	
	update_pulse_lcd = pyqtSignal(object)
	update_pulse_lcd2 = pyqtSignal(object)
	
	warning = pyqtSignal(object)
	error = pyqtSignal(tuple)
	
	finished = pyqtSignal()
	
	
	
	
	
	
	
	
	
class Email_Worker(QRunnable):
	"""
	Worker thread
	:param args: Arguments to make available to the run code
	:param kwargs: Keywords arguments to make available to the run code
	"""
	def __init__(self,*argv):
		super(Email_Worker, self).__init__()
		
		# constants	
		self.subject = argv[0].subject
		self.contents = argv[0].contents
		self.emailset_str = argv[0].settings
		self.emailrec_str = argv[0].receivers
		
		self.signals = WorkerSignals()
		
		
	@pyqtSlot()
	def run(self):
		asyncio.set_event_loop(asyncio.new_event_loop())
		"""
		Initialise the runner function with passed args, kwargs.
		"""
		# Retrieve args/kwargs here; and fire processing using them
		try:
			self.yag = yagmail.SMTP(self.emailset_str[0])
			self.yag.send(to=self.emailrec_str, subject=self.subject, contents=self.contents)
		except Exception as e:
			self.signals.warning.emit(str(e))
			
		self.signals.finished.emit()
	
	
	
	
	
	
	
class Run_COMPexPRO_Thread(QRunnable):
	
	def __init__(self,*argv):
		super(Run_COMPexPRO_Thread, self).__init__()
		# constants	
		self.end_flag=False
		
		self.rate = argv[0]
		self.hv = argv[1]
		self.timeout_str = argv[2]
		self.warmup_bool = argv[3]
		self.warmup = argv[4]
		self.trigger_str = argv[5]
		self.gasmode_str = argv[6]
		self.pulse_time = argv[7]
		
		self.data_file = argv[8]
		self.timetrace_str = argv[9]
		self.inst_list = argv[10]
		self.stopButton = argv[11]
		
		self.signals = WorkerSignals()
	
	def abort(self):
		
		self.end_flag=True
	
	@pyqtSlot()
	def run(self):
		
		if self.inst_list.get('COMPexPRO'):
			self.inst_list.get('COMPexPRO').set_timeout(self.timeout_str)
			self.inst_list.get('COMPexPRO').set_trigger(self.trigger_str)
			
		if self.warmup_bool:
			self.warmup_on()
		
		if self.inst_list.get('COMPexPRO') and self.inst_list.get('PM100USB'):
			with open(self.data_file, "w") as thefile:
				thefile.write("Your comment line - do NOT delete this line\n") 
				thefile.write("Col 0: Elapsed time [s]\nCol 1: Total counter (1000)\nCol 2: Pulse rate [Hz]\nCol 3: High volt. [kV]\n")
				thefile.write("Col 4: Beam energy [mJ]\nCol 5: Laser tube press. [mbar]\nCol 6: Laser tube temp. [C]\n")
				thefile.write("Col 7: Buffer press. [mbar]\n")
				thefile.write("Col 8: Power meter PM100USB [Watt]\n\n")
				thefile.write("%s\t\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" %(tuple("".join(["Col ",str(tal)]) for tal in range(9))))
		
		elif self.inst_list.get('COMPexPRO') and not self.inst_list.get('PM100USB'):
			with open(self.data_file, "w") as thefile:
				thefile.write("Your comment line - do NOT delete this line\n") 
				thefile.write("Col 0: Elapsed time [s]\nCol 1: Total counter (1000)\nCol 2: Pulse rate [Hz]\nCol 3: High volt. [kV]\n")
				thefile.write("Col 4: Beam energy [mJ]\nCol 5: Laser tube press. [mbar]\nCol 6: Laser tube temp. [C]\n")
				thefile.write("Col 7: Buffer press. [mbar]\n\n")
				thefile.write("%s\t\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" %(tuple("".join(["Col ",str(tal)]) for tal in range(8))))
		
		elif self.inst_list.get('PM100USB') and not self.inst_list.get('COMPexPRO'):
			with open(self.data_file, "w") as thefile:
				thefile.write("Your comment line - do NOT delete this line\n") 
				thefile.write("Col 0: Elapsed time [s]\n")
				thefile.write("Col 1: Power meter PM100USB [Watt]\n\n")
				thefile.write("%s\t\t%s\n" %(tuple("".join(["Col ",str(tal)]) for tal in range(2))))
		
		try:
			self.start_source()
		except:
			traceback.print_exc()
			exctype, value = sys.exc_info()[:2]
			self.signals.error.emit((exctype, value, traceback.format_exc()))
		else:
			pass
		finally:
			self.signals.finished.emit()  # Done
		
		
	def warmup_on(self):
		
		self.stopButton.setText("SKIP warm-up")
		for tal in range(480)[::-1]:
			if tal==0:
				self.warmup.setStyleSheet("color: green")
			self.warmup.setText(str(tal))
			time.sleep(1)
			if self.end_flag==True:
				self.stopButton.setEnabled(False)
				break
			
			
	def start_source(self):
		
		self.end_flag=False
		# call the COMPexPRO port
		if self.inst_list.get('COMPexPRO'):
			self.inst_list.get('COMPexPRO').set_opmode("SKIP")
			self.inst_list.get('COMPexPRO').set_gasmode(self.gasmode_str)
			self.inst_list.get('COMPexPRO').set_reprate(str(self.rate))
			self.inst_list.get('COMPexPRO').set_hv(str(self.hv))
		
		# Power meter settings
		if self.inst_list.get('PM100USB'):
			self.inst_list.get('PM100USB').setWavelength(248)
			print("PM100USB wavelength:\n\t",self.inst_list.get('PM100USB').getWavelength(0),"nm")
			
			self.inst_list.get('PM100USB').setPowerRange(0)
			print("PM100USB power range:\n\t",self.inst_list.get('PM100USB').getPowerRange(0),"W")
		
		if self.inst_list.get('COMPexPRO'):
			str_on = self.inst_list.get('COMPexPRO').set_opmode("ON")
			if str_on=="ON":
				print("Pulsing, ",str_on)
		
		self.stopButton.setText("STOP source")
		self.stopButton.setEnabled(True)
		
		time_start=time.time()
		while time.time()-time_start<self.pulse_time:
			if self.end_flag:
				break
			
			if self.inst_list.get('PM100USB'):
				pm_power = self.inst_list.get('PM100USB').measPower()
			
			if self.inst_list.get('COMPexPRO'):
				counter = self.inst_list.get('COMPexPRO').get_counter()
				totalcounter = self.inst_list.get('COMPexPRO').get_totalcounter()
				
				egy = self.inst_list.get('COMPexPRO').get_energy()
				lt_press = self.inst_list.get('COMPexPRO').get_lt_press()
				lt_temp = self.inst_list.get('COMPexPRO').get_lt_temp()
				buffer_press = self.inst_list.get('COMPexPRO').get_buffer_press()
				f2_press = self.inst_list.get('COMPexPRO').get_f2_press()
				f2_temp = self.inst_list.get('COMPexPRO').get_f2_temp()
				pulse_diff = self.inst_list.get('COMPexPRO').get_pulse_diff()
				pow_stab = self.inst_list.get('COMPexPRO').get_pow_stab()
			
				self.signals.update_pulse_lcd.emit(counter)
				self.signals.update_pulse_lcd2.emit(totalcounter)
				
				
			time_elap=time.time()-time_start
			if self.inst_list.get('COMPexPRO') and self.inst_list.get('PM100USB'):
				self.signals.make_update1.emit(time_elap,1e-3*egy,pm_power)
				self.signals.make_update2.emit(time_elap,1e-3*lt_press,lt_temp)
				self.signals.make_update3.emit(time_elap,1e-3*buffer_press)
				self.signals.make_update4.emit(time_elap,1e-3*f2_press,f2_temp)
				self.signals.make_update5.emit(time_elap,pulse_diff)
				if pow_stab=="YES":
					pow_stab=1
				elif pow_stab=="NO":
					pow_stab=0
				self.signals.make_update6.emit(time_elap,pow_stab)
				
				time_elap=format(time_elap, "010.4f")
				egy=format(egy, "05.3f")
				pm_power=format(pm_power, "05.3f")
				
				with open(self.data_file, "a") as thefile:
					thefile.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" %(time_elap,totalcounter,self.rate,self.hv,egy,lt_press,lt_temp,buffer_press,pm_power))
					
			elif self.inst_list.get('COMPexPRO') and not self.inst_list.get('PM100USB'):
				self.signals.make_update1.emit(time_elap,1e-3*egy,-1)
				self.signals.make_update2.emit(time_elap,1e-3*lt_press,lt_temp)
				self.signals.make_update3.emit(time_elap,1e-3*buffer_press)
				self.signals.make_update4.emit(time_elap,1e-3*f2_press,f2_temp)
				self.signals.make_update5.emit(time_elap,pulse_diff)
				if pow_stab=="YES":
					pow_stab=1
				elif pow_stab=="NO":
					pow_stab=0
				self.signals.make_update6.emit(float(time_elap),pow_stab)
				
				time_elap=format(time_elap, "010.4f")
				egy=format(egy, "05.3f")
				
				with open(self.data_file, "a") as thefile:
					thefile.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" %(time_elap,totalcounter,self.rate,self.hv,egy,lt_press,lt_temp,buffer_press))
					
			elif self.inst_list.get('PM100USB') and not self.inst_list.get('COMPexPRO'):
				self.signals.make_update1.emit(time_elap,-1,pm_power)
				
				time_elap=format(time_elap, "010.4f")
				pm_power=format(pm_power, "05.3f")
				
				with open(self.data_file, "a") as thefile:
					thefile.write("%s\t%s\n" %(time_elap,pm_power))
					
					
		if self.inst_list.get('COMPexPRO'):
			str_off = self.inst_list.get('COMPexPRO').set_opmode("OFF")
			if str_off[:3]=="OFF":
				print("Stopped, ",str_off)
		
		if self.warmup_bool:
			self.stopButton.setText("SKIP warm-up")
		else:
			self.stopButton.setText("STOP source")
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
class Run_COMPexPRO(QMainWindow):
	
	def __init__(self):
		super().__init__()
		
		self.load_()
		
		# Enable antialiasing for prettier plots		
		pg.setConfigOptions(antialias=True)
		self.initUI()
			
	def initUI(self):
		
		################### MENU BARS START ##################
		
		MyBar = QMenuBar(self)
		fileMenu = MyBar.addMenu("File")
		self.fileLoadAs = fileMenu.addAction("Config section settings")        
		self.fileLoadAs.triggered.connect(self.load_config_dialog)
		fileSavePlt = fileMenu.addAction("Save plots")
		fileSavePlt.triggered.connect(self.save_plots)
		fileSavePlt.setShortcut("Ctrl+P")
		fileSaveSet = fileMenu.addAction("Save settings")        
		fileSaveSet.triggered.connect(self.save_) # triggers closeEvent()
		fileSaveSet.setShortcut("Ctrl+S")
		self.fileClose = fileMenu.addAction("Close")        
		self.fileClose.triggered.connect(self.close) # triggers closeEvent()
		self.fileClose.setShortcut("Ctrl+X")
		
		instMenu = MyBar.addMenu("Instruments")
		self.conMode = instMenu.addAction("Load instruments")
		self.conMode.triggered.connect(self.instrumentsDialog)
		
		self.emailMenu = MyBar.addMenu("E-mail")
		self.emailSet = self.emailMenu.addAction("E-mail settings")
		self.emailSet.triggered.connect(self.email_set_dialog)
		self.emailData = self.emailMenu.addAction("E-mail data")
		self.emailData.triggered.connect(self.email_data_dialog)
		
		################### MENU BARS END ##################

		lbl1 = QLabel("OPERATION settings:", self)
		lbl1.setStyleSheet("color: blue")	
		
		timeout_lbl = QLabel("Timeout", self)
		self.combo0 = QComboBox(self)
		self.mylist0=["ON","OFF"]
		self.combo0.addItems(self.mylist0)
		self.combo0.setCurrentIndex(self.mylist0.index(self.timeout_str))
		
		warmup_lbll = QLabel("Warm-up", self)
		self.combo1 = QComboBox(self)
		self.mylist1=["ON","OFF"]
		self.combo1.addItems(self.mylist1)
		self.combo1.setCurrentIndex(self.mylist1.index(self.warmup_str))
		self.warmup_bool=self.bool_(self.warmup_str)
		
		trigger_lbl = QLabel("Trigger", self)
		self.combo2 = QComboBox(self)
		self.mylist2=["INT","EXT"]
		self.combo2.addItems(self.mylist2)
		self.combo2.setCurrentIndex(self.mylist2.index(self.trigger_str))
		
		gasmode_lbl = QLabel("Gasmode", self)
		self.combo3 = QComboBox(self)
		self.mylist3=["PREMIX","SINGLE GASES"]
		self.combo3.addItems(self.mylist3)
		self.combo3.setCurrentIndex(self.mylist3.index(self.gasmode_str))
		
		self.hv_lbl = QLabel("".join(["High volt. (",str(self.hv),") [kV]"]), self)
		self.sld_hv = QSlider(Qt.Horizontal,self)
		#self.sld_hv.setFocusPolicy(Qt.NoFocus)
		self.sld_hv.tickPosition()
		self.sld_hv.setRange(190,300)
		self.sld_hv.setSingleStep(1)
		self.sld_hv.setPageStep(5)
		self.sld_hv.setValue(10*self.hv)
		
		self.rate_lbl = QLabel("".join(["Rep. rate (",str(self.rate),") [Hz]"]), self)
		self.sld_rate = QSlider(Qt.Horizontal,self)
		#self.sld_rate.setFocusPolicy(Qt.NoFocus)
		self.sld_rate.tickPosition()
		self.sld_rate.setRange(1,50)
		self.sld_rate.setSingleStep(1)
		self.sld_rate.setPageStep(2)
		self.sld_rate.setValue(self.rate)
		
		#####################################################
		
		self.laser_type = QLabel("",self)
		self.laser_type.setStyleSheet("color: magenta")
		laser_type_lbl = QLabel("".join(["Type of laser:"]),self)
		
		self.gas_menu = QLabel("",self)
		self.gas_menu.setStyleSheet("color: magenta")
		gas_menu_lbl = QLabel("".join(["Gas menu no:"]),self)
		
		self.gas_wl = QLabel("",self)
		self.gas_wl.setStyleSheet("color: magenta")
		gas_wl_lbl = QLabel("Gas wavelength:",self)
		
		self.gas_mix = QLabel("",self)
		self.gas_mix.setStyleSheet("color: magenta")
		gas_mix_lbl = QLabel("Gas mixture:",self)
		
		self.pulse_counter = QLabel("",self)
		self.pulse_counter.setStyleSheet("color: magenta")
		pulse_lbl1 = QLabel("Counter (10^3):",self)
		
		self.pulse_tot = QLabel("",self)
		self.pulse_tot.setStyleSheet("color: magenta")
		pulse_lbl2 = QLabel("Total counter (10^3):",self)
		
		warmup_lbl2 = QLabel("Warm-up [s]:",self)
		self.warmup = QLabel("",self)
		if self.warmup_bool:
			self.warmup.setStyleSheet("color: red")
			self.warmup.setText("480")
		else:
			self.warmup.setStyleSheet("color: green")
			self.warmup.setText("0")
		
		pulse_time_lbl = QLabel("Pulsing time [s]:",self)
		self.pulsetimeEdit = QLineEdit(str(self.pulse_time),self)
		self.pulsetimeEdit.setFixedWidth(60)
		
		self.resetButton = QPushButton("Reset counter",self)
		
		#####################################################
		
		lbl4 = QLabel("STORAGE with timetrace and schroll settings:", self)
		lbl4.setStyleSheet("color: blue")
		
		filename = QLabel("Create folder and file:",self)
		self.filenameEdit = QLineEdit(str(self.filename_str),self)
		#self.filenameEdit.setFixedWidth(140)
		
		#####################################################
		
		schroll_lbl = QLabel("Schroll pts:",self)
		self.combo4 = QComboBox(self)
		self.mylist4=["100","200","500","1000","2000"]
		self.combo4.addItems(self.mylist4)
		# initial combo settings
		self.combo4.setCurrentIndex(self.mylist4.index(str(self.schroll)))
		#self.combo4.setFixedWidth(85)
		
		#####################################################
		
		lbl5 = QLabel("EXECUTE operation settings:", self)
		lbl5.setStyleSheet("color: blue")
		
		self.startButton = QPushButton("Start source",self)
		self.stopButton = QPushButton("",self)
		if self.warmup_bool:
			self.stopButton.setText("SKIP warm-up")
		else:
			self.stopButton.setText("STOP source")
		
		
		#####################################################
		
		self.lcd = QLCDNumber(self)
		self.lcd.setStyleSheet("color: red")
		self.lcd.setFixedHeight(50)
		self.lcd.setSegmentStyle(QLCDNumber.Flat)
		self.lcd.setNumDigits(11)
		self.lcd.display(self.timetrace_str)
			
		#####################################################
		#####################################################
		#####################################################
		
		# Add all widgets		
		g1_0 = QGridLayout()
		g1_0.addWidget(MyBar,0,0)
		g1_0.addWidget(lbl1,1,0)

		g1_1 = QGridLayout()
		g1_1.addWidget(timeout_lbl,0,0)
		g1_1.addWidget(self.combo0,1,0)
		g1_1.addWidget(warmup_lbll,0,1)
		g1_1.addWidget(self.combo1,1,1)
		g1_1.addWidget(trigger_lbl,0,2)
		g1_1.addWidget(self.combo2,1,2)
		g1_1.addWidget(gasmode_lbl,0,3)
		g1_1.addWidget(self.combo3,1,3)
		
		g1_2 = QGridLayout()
		g1_2.addWidget(self.rate_lbl,0,0)
		g1_2.addWidget(self.sld_rate,1,0)
		g1_2.addWidget(self.hv_lbl,0,1)
		g1_2.addWidget(self.sld_hv,1,1)
		
		g1_3 = QGridLayout()
		g1_3.addWidget(gas_mix_lbl,0,0)
		g1_3.addWidget(self.gas_mix,0,1)
		g1_3.addWidget(laser_type_lbl,0,2)
		g1_3.addWidget(self.laser_type,0,3)
		g1_3.addWidget(gas_menu_lbl,1,0)
		g1_3.addWidget(self.gas_menu,1,1)
		g1_3.addWidget(gas_wl_lbl,1,2)
		g1_3.addWidget(self.gas_wl,1,3)
		g1_3.addWidget(pulse_lbl1,2,0)
		g1_3.addWidget(self.pulse_counter,2,1)
		g1_3.addWidget(pulse_lbl2,2,2)
		g1_3.addWidget(self.pulse_tot,2,3)
		
		g1_4 = QGridLayout()
		g1_4.addWidget(self.resetButton,0,0)
		g1_4.addWidget(warmup_lbl2,0,1)
		g1_4.addWidget(self.warmup,0,2)
		g1_4.addWidget(pulse_time_lbl,0,3)
		g1_4.addWidget(self.pulsetimeEdit,0,4)
		
		v1 = QVBoxLayout()
		v1.addLayout(g1_0)
		v1.addLayout(g1_1)
		v1.addLayout(g1_2)
		v1.addLayout(g1_3)
		v1.addLayout(g1_4)

		#####################################################
		
		g3_0 = QGridLayout()
		g3_0.addWidget(lbl4,0,0)
		
		g3_1 = QGridLayout()
		g3_1.addWidget(filename,0,0)
		g3_1.addWidget(self.filenameEdit,1,0)
		g3_1.addWidget(schroll_lbl,0,1)
		g3_1.addWidget(self.combo4,1,1)
		
		g3_2 = QGridLayout()
		g3_2.addWidget(self.lcd,0,0)
		
		v3 = QVBoxLayout()
		v3.addLayout(g3_0)
		v3.addLayout(g3_1)
		v3.addLayout(g3_2)
		
		#####################################################
		
		g5_0 = QGridLayout()
		g5_0.addWidget(lbl5,0,0)
		
		g5_1 = QGridLayout()
		g5_1.addWidget(self.startButton,0,1)
		g5_1.addWidget(self.stopButton,0,2)
		
		v5 = QVBoxLayout()
		v5.addLayout(g5_0)
		v5.addLayout(g5_1)
		
		#####################################################
		
		# add ALL groups from v1 to v6 in one vertical group v7
		v7 = QVBoxLayout()
		v7.addLayout(v1)
		v7.addLayout(v3)
		v7.addLayout(v5)
	
		#####################################################
		
		# set GRAPHS and TOOLBARS to a new vertical group vcan
		vcan0 = QGridLayout()
		self.pw1 = pg.PlotWidget() 
		vcan0.addWidget(self.pw1,0,0)
		
		vcan1 = QGridLayout()
		self.pw3 = pg.PlotWidget()
		vcan1.addWidget(self.pw3,0,0)
		
		# SET ALL HORIZONTAL COLUMNS TOGETHER
		hbox = QHBoxLayout()
		hbox.addLayout(v7)
		hbox.addLayout(vcan0)
		
		# SET VERTICAL COLUMNS TOGETHER TO FINAL LAYOUT
		vbox = QVBoxLayout()
		vbox.addLayout(hbox)
		vbox.addLayout(vcan1)
		
		vcan2 = QGridLayout()
		self.pw5 = pg.PlotWidget()
		vcan2.addWidget(self.pw5,0,0)
		self.pw2 = pg.PlotWidget()
		vcan2.addWidget(self.pw2,1,0)
		self.pw6 = pg.PlotWidget()
		vcan2.addWidget(self.pw6,2,0)
		self.pw7 = pg.PlotWidget()
		vcan2.addWidget(self.pw7,3,0)
		
		# SET HORIZONTAL COLUMNS TOGETHER TO FINAL LAYOUT
		hbox1 = QHBoxLayout()
		hbox1.addLayout(vbox)
		hbox1.addLayout(vcan2)
		
		##############################################
		
		# INITIAL SETTINGS PLOT 1
		self.p1_ = self.pw1.plotItem
		self.curve1=self.p1_.plot(pen="r")
		# create plot and add it to the figure
		self.p9_1 = pg.ViewBox()
		self.curve1_1=pg.PlotCurveItem(pen="m")
		self.p9_1.addItem(self.curve1_1)
		# connect respective axes to the plot 
		self.p1_.scene().addItem(self.p9_1)
		self.p1_.getAxis("right").linkToView(self.p9_1)
		self.p9_1.setXLink(self.p1_)
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw1.setDownsampling(mode="peak")
		self.pw1.setClipToView(True)
		self.pw1.enableAutoRange()
		# Labels and titels are placed here since they change dynamically
		self.pw1.setTitle("".join(["Energy after BEAM SPLITTER"]))
		self.pw1.setLabel("left", "Energy", units="J", color="red")
		self.pw1.setLabel("right", "PM100USB", units="W", color="magenta")
		self.pw1.setLabel("bottom", "Elapsed time", units="s", color="white")
		self.pw1.enableAutoRange()
		
		
		# INITIAL SETTINGS PLOT 2
		p6 = self.pw2.plotItem
		self.curve6=p6.plot(pen="r")
		#self.pw2.setLogMode(None,True)
		self.pw2.setTitle("".join(["Trigger pulse diff."]))
		self.pw2.setLabel("left", "Pulse diff", units="", color="red")
		self.pw2.setLabel("bottom", "Elapsed time", units="s", color="red")
		self.pw2.enableAutoRange()
		
		
		# INITIAL SETTINGS PLOT 5
		p8 = self.pw5.plotItem
		self.curve8=p8.plot(pen="m")
		self.pw5.setTitle("".join(["BUFFER gas press."]))
		self.pw5.setLabel("left", "Press.", units="bar", color="magenta")
		self.pw5.setLabel("bottom", "Elapsed time", units="s", color="magenta")
		self.pw5.enableAutoRange()
		
		
		# INITIAL SETTINGS PLOT 6
		self.p9 = self.pw6.plotItem
		self.curve9=self.p9.plot(pen="y")
		# create plot and add it to the figure
		self.p9_ = pg.ViewBox()
		self.curve11=pg.PlotCurveItem(pen="r")
		self.p9_.addItem(self.curve11)
		# connect respective axes to the plot 
		self.p9.scene().addItem(self.p9_)
		self.p9.getAxis("right").linkToView(self.p9_)
		self.p9_.setXLink(self.p9)
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw6.setDownsampling(mode="peak")
		self.pw6.setClipToView(True)
		self.pw6.enableAutoRange()
		# Labels and titels are placed here since they change dynamically
		self.pw6.setTitle("".join(["F2 mix gas"]))
		self.pw6.setLabel("left", "Temp.", units="C", color="yellow")
		self.pw6.setLabel("right", "Press.", units="bar", color="red")
		self.pw6.setLabel("bottom", "Elapsed time", units="s", color="white")
		
		
		# INITIAL SETTINGS PLOT 7
		p10 = self.pw7.plotItem
		self.curve10=p10.plot(pen="y")
		self.pw7.setTitle("".join(["Power stabilization (1=YES, 0=NO)"]))
		self.pw7.setLabel("left", "YES or NO", units="", color="yellow")
		self.pw7.setLabel("bottom", "Elapsed time", units="s", color="yellow")
		
		
		# INITIAL SETTINGS PLOT 3
		self.p1 = self.pw3.plotItem
		self.curve3=self.p1.plot(pen="w")
		self.curve4=self.p1.plot(pen="y")
		# create plot and add it to the figure
		self.p2 = pg.ViewBox()
		self.curve5=pg.PlotCurveItem(pen="r")
		self.p2.addItem(self.curve5)
		# connect respective axes to the plot 
		self.p1.scene().addItem(self.p2)
		self.p1.getAxis("right").linkToView(self.p2)
		self.p2.setXLink(self.p1)
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw3.setDownsampling(mode="peak")
		self.pw3.setClipToView(True)
		self.pw3.enableAutoRange()
		# Labels and titels are placed here since they change dynamically
		self.pw3.setTitle("".join(["Temp. and press. in the LASER TUBE"]))
		self.pw3.setLabel("left", "Temp.", units="C", color="yellow")
		self.pw3.setLabel("right", "Press.", units="bar", color="red")
		self.pw3.setLabel("bottom", "Elapsed time", units="s", color="white")
		"""
		
		# INITIAL SETTINGS PLOT 4
		self.pw4 = gl.GLViewWidget()
		self.pw4.opts["distance"] = 0.03
		self.pw4.setWindowTitle("Scatter plot of sweeped poins")
		
		#zx = gl.GLGridItem()
		#zx.rotate(90, 0, 1, 0) # zx-plane
		#zx.translate(-1, 0, 0)
		#zx.scale(0.1,0.1,0.1,local=True)
		#self.pw4.addItem(zx)
		
		zy = gl.GLGridItem()
		zy.rotate(90, 1, 0, 0) # zy-plane
		zy_spacing=1e-3 # Volts
		zy.translate(0, 0, 10*zy_spacing)
		zy.scale(zy_spacing,zy_spacing,zy_spacing,local=True)
		self.pw4.addItem(zy)
		
		xy = gl.GLGridItem()
		xy_spacing=1e-3 # Meters
		xy.translate(0, -10*xy_spacing, 0) # xy-plane
		xy.scale(xy_spacing,xy_spacing,xy_spacing,local=True)
		self.pw4.addItem(xy)
		## create a new AxisItem, linked to view
		#ax2 = gl.GLAxisItem()
		#ax2.setSize(x=10,y=10,z=10)
		#self.pw4.addItem(ax2)self.conMode.setEnabled(True)
		#ax2.setLabel("latitude", color="#0000ff")
		self.sp1 = gl.GLScatterPlotItem()
		"""
		# Initialize and set titles and axis names for both plots
		
		##############################################
		
		self.inst_list = {}
		
		self.threadpool = QThreadPool()
		print("Multithreading in Run_COMPexPRO with maximum %d threads" % self.threadpool.maxThreadCount())
		
		self.isRunning = False
		
		# reacts to drop-down menus
		self.combo0.activated[str].connect(self.onActivated0)
		self.combo1.activated[str].connect(self.onActivated1)
		self.combo2.activated[str].connect(self.onActivated2)
		self.combo3.activated[str].connect(self.onActivated3)
		self.combo4.activated[str].connect(self.onActivated4)
		
		self.sld_rate.valueChanged[int].connect(self.changeRate)
		self.sld_hv.valueChanged[int].connect(self.changeHV)
		
		# run the main script
		self.resetButton.clicked.connect(self.set_reset)
		
		# run the main script
		self.startButton.clicked.connect(self.set_run)
		
		# cancel the script run
		self.stopButton.clicked.connect(self.set_stop)
		
		self.clear_vars_graphs()
		self.allFields(False)
		self.stopButton.setEnabled(False)
		self.startButton.setEnabled(False)
		self.fileLoadAs.setEnabled(True)
		
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.set_disconnect)
		self.timer.setSingleShot(True)
		
		##############################################
		
		self.setGeometry(30, 80, 1400, 900)
		self.setWindowTitle("COMPexPRO Photon Source Controller")
		# re-adjust/minimize the size of the e-mail dialog
		# depending on the number of attachments
		#hbox1.setSizeConstraint(hbox1.SetFixedSize)
		
		w = QWidget()
		w.setLayout(hbox1)
		self.setCentralWidget(w)
		self.show()
		
		
	def instrumentsDialog(self):
		
		self.Inst = Instruments_dialog.Instruments_dialog(self,self.inst_list,self.timer,self.gas_menu,self.gas_wl,self.gas_mix,self.laser_type,self.pulse_counter,self.pulse_tot)
		self.Inst.exec()
		
		if self.inst_list.get("COMPexPRO"):
			self.allFields(True)
		elif self.inst_list.get("PM100USB") and not self.inst_list.get("COMPexPRO"):
			self.allFields(False)
			self.combo4.setEnabled(True)
			self.filenameEdit.setEnabled(True)
		else:
			self.allFields(False)
			
		if not self.inst_list.get("COMPexPRO") and not self.inst_list.get("PM100USB"):
			self.startButton.setText("Load instrument!")
			self.startButton.setEnabled(False)
		else:
			self.startButton.setText("Scan")
			self.startButton.setEnabled(True)
			
			
	def initUI_(self):
		
		self.combo0.setCurrentIndex(self.mylist0.index(self.timeout_str))
		self.combo1.setCurrentIndex(self.mylist1.index(self.warmup_str))
		self.combo2.setCurrentIndex(self.mylist2.index(self.trigger_str))
		self.combo3.setCurrentIndex(self.mylist3.index(self.gasmode_str))
		self.combo4.setCurrentIndex(self.mylist4.index(str(self.schroll)))
		
		self.rate_lbl.setText("".join(["Rep. rate (",str(self.rate),") [Hz]"]))
		self.sld_rate.setValue(self.rate)
		
		self.hv_lbl.setText("".join(["High volt. (",str(self.hv/10.0),") [kV]"]))
		self.sld_hv.setValue(10*self.hv)
		
		self.filenameEdit.setText(self.filename_str)
		self.pulsetimeEdit.setText(str(self.pulse_time))
		
		
	def update_pulse_lcd(self,i):
		
		self.pulse_counter.setText(str(i))
		
		
	def update_pulse_lcd2(self,i):
		
		self.pulse_tot.setText(str(i))
		
		
	def set_reset(self):
		
		self.pulse_counter.setText(str(self.inst_list.get("COMPexPRO").set_counter_reset()))
		
		
	def set_disconnect(self):
		
		##########################################
		
		if self.inst_list.get("COMPexPRO"):
			val_str=self.inst_list.get("COMPexPRO").set_trigger("EXT")
			if val_str=="EXT":
				print("COMPexPRO trigger set to external, ",val_str)
			else:
				print("Could not set COMPexPRO trigger to EXT!")
			
			if self.inst_list.get("COMPexPRO").is_open():
				self.inst_list.get("COMPexPRO").close()
			self.inst_list.pop('COMPexPRO', None)
				
		##########################################
		
		if self.inst_list.get("PM100USB"):
			if self.inst_list.get("PM100USB").is_open():
				self.inst_list.get("PM100USB").close()
			self.inst_list.pop('PM100USB', None)
			
		##########################################
		
		print("All ports DISCONNECTED")
		
		self.allFields(False)
		self.conMode.setEnabled(True)
		self.fileLoadAs.setEnabled(True)
		self.stopButton.setEnabled(False)
		self.startButton.setText("Load instrument!")
		self.startButton.setEnabled(False)
		
		
	def allFields(self,trueorfalse):
		
		self.combo0.setEnabled(trueorfalse)
		self.combo1.setEnabled(trueorfalse)
		self.combo2.setEnabled(trueorfalse)
		self.combo3.setEnabled(trueorfalse)
		self.combo4.setEnabled(trueorfalse)
		
		self.sld_rate.setEnabled(trueorfalse)
		self.sld_hv.setEnabled(trueorfalse)
		
		self.filenameEdit.setEnabled(trueorfalse)
		self.pulsetimeEdit.setEnabled(trueorfalse)
		self.resetButton.setEnabled(trueorfalse)
			
			
	def changeRate(self, val):
		
		self.rate=val
		self.rate_lbl.setText("".join(["Rep. rate (",str(val),") [Hz]"]))
		time.sleep(0.05)
		
		
	def changeHV(self, val):
		
		self.hv=val/10.0
		self.hv_lbl.setText("".join(["High volt. (",str(val/10.0),") [kV]"]))
		time.sleep(0.05)
		
		
	def onActivated0(self, text):
		
		self.timeout_str=str(text)
		
		if str(text)=="ON":
			QMessageBox.warning(self, "Message","Serial disruptions are present in ON mode. It is recommeneded to set timeout in OFF mode.")
		
	
	def bool_(self,txt):
		
		if txt=="ON":
			return True
		elif txt=="OFF":
			return False
		
	
	def onActivated1(self, text):
		
		self.warmup_str=str(text)
		self.warmup_bool=self.bool_(str(text))
		
		if self.warmup_bool:
			self.stopButton.setText("SKIP warm-up")
			self.warmup.setStyleSheet("color: red")
			self.warmup.setText("480")
		else:
			self.stopButton.setText("STOP source")
			self.warmup.setStyleSheet("color: green")
			self.warmup.setText("0")
			
			
	def onActivated2(self, text):
		
		self.trigger_str=str(text)
		
		if str(text)=="EXT":
			QMessageBox.warning(self, "Message","Setting trigger to external mode requires external TTL signal for pulse triggering.")
			
			
	def onActivated3(self, text):
		
		self.gasmode_str=str(text)
		
		
	def onActivated4(self, text):
		
		self.schroll=int(text)
		
		
	def set_run(self):
		
		if not self.inst_list.get("PM100USB") and not self.inst_list.get("COMPexPRO"):
			QMessageBox.critical(self, 'Message',"No instruments connected. At least 1 instrument is required.")
			return
		
		try:
			self.pulse_time = int(self.pulsetimeEdit.text())
			if self.pulse_time<=0:
				QMessageBox.warning(self, "Message","Max pulse time is a positive non-zero integer!")
				return None
		except Exception as e:
			QMessageBox.warning(self, "Message","Max pulse time is an integer!")
			return
		
		# For SAVING data
		self.data_file="".join([self.create_file(str(self.filenameEdit.text())),".txt"])
		
		self.clear_vars_graphs()
		self.allFields(False)
		self.conMode.setEnabled(False)
		self.stopButton.setEnabled(True)
		self.startButton.setEnabled(False)
		self.fileClose.setEnabled(False)
		self.fileLoadAs.setEnabled(False)
		
		self.isRunning = True
		#self.config.read(''.join([self.cwd,"/config.ini"]))
		self.timer.stop()
		
		self.worker = Run_COMPexPRO_Thread(self.rate,self.hv,self.timeout_str,self.warmup_bool,self.warmup,self.trigger_str, self.gasmode_str, self.pulse_time,self.data_file,self.timetrace_str,self.inst_list,self.stopButton)
		
		self.worker.signals.update_pulse_lcd.connect(self.update_pulse_lcd)
		self.worker.signals.update_pulse_lcd2.connect(self.update_pulse_lcd2)
		self.worker.signals.make_update1.connect(self.make_update1)
		self.worker.signals.make_update2.connect(self.make_update2)
		self.worker.signals.make_update3.connect(self.make_update3)
		self.worker.signals.make_update4.connect(self.make_update4)
		self.worker.signals.make_update5.connect(self.make_update5)
		self.worker.signals.make_update6.connect(self.make_update6)
		self.worker.signals.finished.connect(self.finished)
		
		# Execute
		self.threadpool.start(self.worker)
		
		
		
	"""
	def surf_line_plot(self):
		
		if self.scan_mode=="ywise":
			n = len(self.x_fields)
			x = self.x_fields
			y = self.y_fields
			z = self.acc_volt.reshape((len(self.x_fields),len(self.y_fields) ))
			for i in range(n):
				pts = (x,y,z[i,:])
				self.plt1.setData(pos=pts, color=pg.glColor((i,n*1.3)), width=(i+1)/10., antialias=True)
				self.pw4.addItem(self.plt1)
				
		elif self.scan_mode=="xwise":
			n = len(self.y_fields)
			x = self.x_fields
			y = self.y_fields
			z = self.acc_volt.reshape((len(self.x_fields),len(self.y_fields) ))
			for i in range(n):
				pts = (x,y,z[:,i])
				self.plt1.setData(pos=pts, color=pg.glColor((i,n*1.3)), width=(i+1)/10., antialias=True)
				self.pw4.addItem(self.plt1)
	"""
	
	
	def email_data_dialog(self):
		
		self.Send_email_dialog = Send_email_dialog.Send_email_dialog(self)
		self.Send_email_dialog.exec()
		
		
	def email_set_dialog(self):
		
		self.Email_dialog = Email_settings_dialog.Email_dialog(self, self.lcd)
		self.Email_dialog.exec()
		
		
	def load_config_dialog(self):
		
		self.Load_config_dialog = Load_config_dialog.Load_config_dialog(self, self.config, self.load_, self.initUI_)
		self.Load_config_dialog.exec()
		
		#self.load_()
		#self.initUI_()
		
		
	def create_file(self,mystr):
		
		head, tail = os.path.split(mystr)
		if head:
			if head[0] in ["/","\\"]:
				QMessageBox.critical(self, "Message","Path name should NOT start with a forward slash (/) nor backward slash (\)")
				return ""
		else:
			QMessageBox.warning(self, "Message","No path to folder(s) provided!")
			return ""
		
		if tail:
			saveinfile="".join(["/",head,"/",tail,"_",self.timetrace_str])
		else:
			saveinfile="".join(["/",head,"/data_",self.timetrace_str])
		
		totalpath = ''.join([self.cwd,"/",saveinfile])
		
		try:
			os.makedirs(os.path.dirname(totalpath), exist_ok=True)
		except Exception as e:
			QMessageBox.critical(self, "Message","".join(["Folder named ",head," not valid!\n",str(e)]))
			return ""
		
		return totalpath
		
		
	def make_update1(self,time_elap,energy,power):
    
		self.all_energy.extend([ energy ])
		if len(self.all_energy)>self.schroll:
			self.plot_time_egy[:-1] = self.plot_time_egy[1:]  # shift data in the array one sample left
			self.plot_time_egy[-1] = time_elap
			self.plot_energy_egy[:-1] = self.plot_energy_egy[1:]  # shift data in the array one sample left
			self.plot_energy_egy[-1] = energy
			self.plot_pm_power[:-1] = self.plot_pm_power[1:]  # shift data in the array one sample left
			self.plot_pm_power[-1] = power
		else:
			self.plot_time_egy.extend([ time_elap ])
			self.plot_energy_egy.extend([ energy ])
			self.plot_pm_power.extend([ power ])
		
		## Handle view resizing 
		def updateViews():
			## view has resized; update auxiliary views to match
			self.p9_1.setGeometry(self.p1_.vb.sceneBoundingRect())
			#p3.setGeometry(p1.vb.sceneBoundingRect())

			## need to re-update linked axes since this was called
			## incorrectly while views had different shapes.
			## (probably this should be handled in ViewBox.resizeEvent)
			self.p9_1.linkedViewChanged(self.p1_.vb, self.p9_1.XAxis)
			#p3.linkedViewChanged(p1.vb, p3.XAxis)
		
		updateViews()
		self.p1_.vb.sigResized.connect(updateViews)
		self.curve1.setData(self.plot_time_egy, self.plot_energy_egy)
		self.curve1_1.setData(self.plot_time_egy, self.plot_pm_power)
	
	

	def make_update2(self,time_elap,press,temp):
    
		self.all_press.extend([ press ])
		if len(self.all_press)>self.schroll:
			self.plot_time_tt[:-1] = self.plot_time_tt[1:]  # shift data in the array one sample left
			self.plot_time_tt[-1] = time_elap
			self.plot_press_tt[:-1] = self.plot_press_tt[1:]  # shift data in the array one sample left
			self.plot_press_tt[-1] = press
			self.plot_temp_tt[:-1] = self.plot_temp_tt[1:]  # shift data in the array one sample left
			self.plot_temp_tt[-1] = temp
		else:
			self.plot_time_tt.extend([ time_elap ])
			self.plot_press_tt.extend([ press ])
			self.plot_temp_tt.extend([ temp ])
			
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
		self.curve4.setData(self.plot_time_tt, self.plot_temp_tt)
		self.curve5.setData(self.plot_time_tt, self.plot_press_tt)
		
		
	def make_update3(self,time_elap,buff_press):
    
		self.all_buff_press.extend([ buff_press ])
		if len(self.all_buff_press)>self.schroll:
			self.plot_time_buff[:-1] = self.plot_time_buff[1:]  # shift data in the array one sample left
			self.plot_time_buff[-1] = time_elap
			self.plot_buff_press[:-1] = self.plot_buff_press[1:]  # shift data in the array one sample left
			self.plot_buff_press[-1] = buff_press
		else:
			self.plot_time_buff.extend([ time_elap ])
			self.plot_buff_press.extend([ buff_press ])

		self.curve8.setData(self.plot_time_buff, self.plot_buff_press)
		
		
		
	def make_update4(self,time_elap,press,temp):
    
		self.all_f2_press.extend([ press ])
		if len(self.all_f2_press)>self.schroll:
			self.plot_time_f2[:-1] = self.plot_time_f2[1:]  # shift data in the array one sample left
			self.plot_time_f2[-1] = time_elap
			self.plot_press_f2[:-1] = self.plot_press_f2[1:]  # shift data in the array one sample left
			self.plot_press_f2[-1] = press
			self.plot_temp_f2[:-1] = self.plot_temp_f2[1:]  # shift data in the array one sample left
			self.plot_temp_f2[-1] = temp
		else:
			self.plot_time_f2.extend([ time_elap ])
			self.plot_press_f2.extend([ press ])
			self.plot_temp_f2.extend([ temp ])
			

		## Handle view resizing 
		def updateViews():
			## view has resized; update auxiliary views to match
			self.p9_.setGeometry(self.p9.vb.sceneBoundingRect())
			#p3.setGeometry(p1.vb.sceneBoundingRect())

			## need to re-update linked axes since this was called
			## incorrectly while views had different shapes.
			## (probably this should be handled in ViewBox.resizeEvent)
			self.p9_.linkedViewChanged(self.p9.vb, self.p9_.XAxis)
			#p3.linkedViewChanged(p1.vb, p3.XAxis)
			
		updateViews()
		self.p9.vb.sigResized.connect(updateViews)
		self.curve9.setData(self.plot_time_f2, self.plot_temp_f2)
		self.curve11.setData(self.plot_time_f2, self.plot_press_f2)
		
		
	def make_update5(self,time_elap,diff):
		
		self.all_diff.extend([ diff ])
		if len(self.all_diff)>self.schroll:
			self.plot_time_diff[:-1] = self.plot_time_diff[1:]  # shift data in the array one sample left
			self.plot_time_diff[-1] = time_elap
			self.plot_diff[:-1] = self.plot_diff[1:]  # shift data in the array one sample left
			self.plot_diff[-1] = diff
		else:
			self.plot_time_diff.extend([ time_elap ])
			self.plot_diff.extend([ diff ])

		self.curve6.setData(self.plot_time_diff, self.plot_diff)
		
	
	def make_update6(self,time_elap,yon):
		
		self.all_yon.extend([ yon ])
		if len(self.all_yon)>self.schroll:
			self.plot_time_yon[:-1] = self.plot_time_yon[1:]  # shift data in the array one sample left
			self.plot_time_yon[-1] = time_elap
			self.plot_yon[:-1] = self.plot_yon[1:]  # shift data in the array one sample left
			self.plot_yon[-1] = yon
		else:
			self.plot_time_yon.extend([ time_elap ])
			self.plot_yon.extend([ yon ])

		self.curve10.setData(self.plot_time_yon, self.plot_yon)
		
		
	def set_stop(self):

		self.worker.abort()
		
		
	def clear_vars_graphs(self):
		
		# PLOT 1 initial canvas settings
		self.all_energy=[]
		self.plot_time_egy=[]
		self.plot_energy_egy=[]
		self.plot_pm_power=[]
		
		self.curve1.clear()
		self.curve1_1.clear()
		
		# PLOT 2 initial canvas settings
		self.all_press=[]
		self.plot_time_tt=[]
		self.plot_temp_tt=[]
		self.plot_press_tt=[]
		
		self.curve4.clear()
		self.curve5.clear()
		
		# PLOT 3 initial canvas settings
		self.all_buff_press=[]
		self.plot_time_buff=[]
		self.plot_buff_press=[]
		
		self.curve8.clear()
		
		# PLOT 4 initial canvas settings
		self.all_diff=[]
		self.plot_time_diff=[]
		self.plot_diff=[]
		
		self.curve6.clear()
		
		# PLOT 5 initial canvas settings
		self.all_f2_press=[]
		self.plot_time_f2=[]
		self.plot_temp_f2=[]
		self.plot_press_f2=[]
		
		self.curve9.clear()
		self.curve11.clear()
		
		# PLOT 6 initial canvas settings
		self.all_yon=[]
		self.plot_time_yon=[]
		self.plot_yon=[]
		
		self.curve10.clear()
		
		
		
		
		
	def load_(self):
		
		# Initial read of the config file
		self.config = configparser.ConfigParser()
		self.cwd = os.getcwd()
		try:
			self.config.read(''.join([self.cwd,"/config.ini"]))
			self.last_used_scan = self.config.get("LastScan","last_used_scan")
			
			self.rate = int(self.config.get(self.last_used_scan,"rate"))
			self.hv = float(self.config.get(self.last_used_scan,"hv"))
			self.pulse_time = int(self.config.get(self.last_used_scan,"pulse_time"))
			self.schroll = int(self.config.get(self.last_used_scan,"schroll"))
			
			self.timeout_str = self.config.get(self.last_used_scan,"timeout")
			self.warmup_str = self.config.get(self.last_used_scan,"warmup")
			self.trigger_str = self.config.get(self.last_used_scan,"trigger")
			self.gasmode_str = self.config.get(self.last_used_scan,"gasmode")
			
			self.filename_str = self.config.get(self.last_used_scan,"filename")
			self.timetrace_str = self.config.get(self.last_used_scan,"timetrace")
			
			self.COMPexPROport_str = self.config.get("Instruments","COMPexPROport")
			self.PM100USBport_str = self.config.get("Instruments","PM100USBport")
			
			self.emailrec_str = self.config.get(self.last_used_scan,"emailrec").strip().split(",")
			self.emailset_str = self.config.get(self.last_used_scan,"emailset").strip().split(",")
			
		except configparser.NoOptionError as nov:
			QMessageBox.critical(self, "Message","".join(["Main FAULT while reading the config.ini file\n",str(nov)]))
			raise
		
		
	def save_(self):
		self.timetrace_str=time.strftime("%y%m%d-%H%M")
		self.lcd.display(self.timetrace_str)
		
		self.config.set("LastScan","last_used_scan", self.last_used_scan )
		
		self.config.set(self.last_used_scan,"rate", str(self.rate) )
		self.config.set(self.last_used_scan,"hv", str(self.hv) )
		self.config.set(self.last_used_scan,"pulse_time", str(self.pulse_time) )
		self.config.set(self.last_used_scan,"schroll", str(self.schroll) )
		
		self.config.set(self.last_used_scan,"timeout", str(self.timeout_str) )
		self.config.set(self.last_used_scan,"warmup", str(self.warmup_str) )
		self.config.set(self.last_used_scan,"trigger", str(self.trigger_str) )
		self.config.set(self.last_used_scan,"gasmode", self.gasmode_str )
		
		
		self.config.set(self.last_used_scan,"filename", str(self.filenameEdit.text()) )
		self.config.set(self.last_used_scan,"timetrace",self.timetrace_str)
		
		self.config.set("Instruments","COMPexPROport", self.COMPexPROport_str )
		self.config.set("Instruments","PM100USBport", self.PM100USBport_str )
		with open(''.join([self.cwd,"/config.ini"]), "w") as configfile:
			self.config.write(configfile)
		
		
	def finished(self):
		
		try:
			self.config.read(''.join([self.cwd,"/config.ini"]))
			self.emailset_str = self.config.get(self.last_used_scan,"emailset").strip().split(",")
		except configparser.NoOptionError as nov:
			QMessageBox.critical(self, "Message","".join(["Main FAULT while reading the config.ini file\n",str(nov)]))
			return
		
		self.allFields(True)
		self.conMode.setEnabled(True)
		self.stopButton.setEnabled(False)
		self.startButton.setEnabled(True)
		self.fileClose.setEnabled(True)
		self.fileLoadAs.setEnabled(True)
		
		self.isRunning = False
		
		if self.emailset_str[1] == "yes":
			self.send_notif()
		if self.emailset_str[2] == "yes":
			self.send_data()
		
		if self.inst_list.get("COMPexPRO"):
			self.allFields(True)
		elif self.inst_list.get("PM100USB") and not self.inst_list.get("COMPexPRO"):
			self.allFields(False)
			self.combo4.setEnabled(True)
			self.filenameEdit.setEnabled(True)
		else:
			self.allFields(False)
			
		if not self.inst_list.get("PM100USB") and not self.inst_list.get("COMPexPRO"):
			self.startButton.setText("Load instrument!")
			self.startButton.setEnabled(False)
		else:
			self.startButton.setText("Scan")
			self.startButton.setEnabled(True)
			
		self.timer.start(1000*300)
	
	
	def warning(self, mystr):
		
		QMessageBox.warning(self, "Message", mystr)
		
		
	def critical(self, mystr):
		
		QMessageBox.critical(self, "Message", mystr)
	
	
	def send_notif(self):
		
		self.md1 = Message_dialog.Message_dialog(self, "Sending notification", "...please wait...")
		
		contents=["The scan is done. Please visit the experiment site and make sure that all light sources are switched off."]
		subject="The scan is done"
		
		obj = type("obj",(object,),{"subject":subject, "contents":contents, "settings":self.emailset_str, "receivers":self.emailrec_str})
		worker=Email_Worker(obj)
		
		worker.signals.warning.connect(self.warning)
		worker.signals.finished.connect(self.finished1)
		
		# Execute
		self.threadpool.start(worker)
		
	def finished1(self):
		
		self.md1.close_()
		
		
	def send_data(self):
		
		self.md2 = Message_dialog.Message_dialog(self, "Sending data", "...please wait...")
		
		contents=["The scan is  done and the logged data is attached to this email. Please visit the experiment site and make sure that all light sources are switched off.", self.data_file]
		subject="The scan data from the latest scan!"
		
		obj = type("obj",(object,),{"subject":subject, "contents":contents, "settings":self.emailset_str, "receivers":self.emailrec_str})
		worker=Email_Worker(obj)
		
		worker.signals.warning.connect(self.warning)
		worker.signals.finished.connect(self.finished2)
		
		# Execute
		self.threadpool.start(worker)
		
	def finished2(self):
		
		self.md2.close_()
	
	
	
	
	
	
	
	def closeEvent(self, event):
		reply = QMessageBox.question(self, "Message", "Quit now? Any changes not saved will stay unsaved!", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
		
		if reply == QMessageBox.Yes:
			
			if self.inst_list.get('COMPexPRO'):
				if not hasattr(self, "worker"):
					val_str=self.inst_list.get('COMPexPRO').set_trigger("EXT")
					if val_str:
						if val_str=="EXT":
							print("COMPexPRO trigger set to external, ",val_str)
					else:
						print("Could not set COMPexPRO trigger to EXT!")
					if self.inst_list.get('COMPexPRO').is_open():
						self.inst_list.get('COMPexPRO').close()
				else:
					if self.isRunning:
						QMessageBox.warning(self, "Message", "Pulsing in progress. Stop the photon source then quit!")
						event.ignore()
						return
					else:
						val_str=self.inst_list.get('COMPexPRO').set_trigger("EXT")
						if val_str:
							if val_str=="EXT":
								print("COMPexPRO trigger set to external, ",val_str)
						else:
							print("Could not set COMPexPRO trigger to EXT!")
						if self.inst_list.get('COMPexPRO').is_open():
							self.inst_list.get('COMPexPRO').close()
			
			
			if self.inst_list.get('PM100USB'):
				if not hasattr(self, "worker"):
					if self.inst_list.get('PM100USB').is_open():
						self.inst_list.get('PM100USB').close()
				else:
					if self.isRunning:
						QMessageBox.warning(self, "Message", "Pulsing in progress. Stop the photon source then quit!")
						event.ignore()
						return
					else:
						if self.inst_list.get('PM100USB').is_open():
							self.inst_list.get('PM100USB').close()
							
							
			if hasattr(self, "timer"):
				if self.timer.isActive():
					self.timer.stop()
							
			event.accept()
		else:
		  event.ignore()
		  
		  
	##########################################
	
	
	def save_plots(self):
		
		self.filename_str=str(self.filenameEdit.text())
		
		# For SAVING data
		save_plot1="".join([self.create_file(self.filename_str),"_BeamEnergy.png"])	
		save_plot2="".join([self.create_file(self.filename_str),"_LaserTube.png"])	

		# create an exporter instance, as an argument give it
		# the item you wish to export
		exporter = pg.exporters.ImageExporter(self.p1_)
		# set export parameters if needed
		#exporter.parameters()["width"] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_plot1)
		
		exporter = pg.exporters.ImageExporter(self.p1)
		# set export parameters if needed
		#exporter.parameters()["width"] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_plot2)
		
		#plt.savefig(save_plot3)
		
#########################################
#########################################
#########################################

#########################################
#########################################
#########################################
	
	
def main():
	
	app = QApplication(sys.argv)
	ex = Run_COMPexPRO()
	#sys.exit(app.exec())

	# avoid message "Segmentation fault (core dumped)" with app.deleteLater()
	app.exec()
	app.deleteLater()
	sys.exit()
	
	
if __name__ == "__main__":
		
	main()
