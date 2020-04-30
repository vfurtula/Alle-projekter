#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""


import os, re, serial, time, yagmail, configparser

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QMessageBox, QGridLayout, QCheckBox, QLabel, QLineEdit, QComboBox, QFrame, QVBoxLayout, QHBoxLayout, QMenuBar, QPushButton)

import ZaberXmcb_ascii, SR510



class Instruments_dialog(QDialog):
	
	def __init__(self, parent, inst_list, timer,cwd):
		super().__init__(parent)
		
		# Initial read of the config file
		self.config = configparser.ConfigParser()
		self.cwd = cwd
		
		try:
			self.config.read(''.join([self.cwd,"/config.ini"]))
			self.last_used_scan = self.config.get('LastScan','last_used_scan')
			
			self.Validrange_lambda = [int(i) for i in self.config.get(self.last_used_scan,'validrange_lambda').strip().split(',')]
			self.Validrange_slit = [int(i) for i in self.config.get(self.last_used_scan,'validrange_slit').strip().split(',')]
			self.Last_position_lambda = self.config.get(self.last_used_scan,'last_position_lambda').strip().split(',')
			self.Last_position_lambda = [int(self.Last_position_lambda[0]), float(self.Last_position_lambda[1])]
			self.Last_position_slit = self.config.get(self.last_used_scan,'last_position_slit').strip().split(',')
			self.Last_position_slit = [int(self.Last_position_slit[0]), float(self.Last_position_slit[1])]
			
			self.zaberport_str=self.config.get("Instruments","zaberport").strip().split(",")[0]
			self.zaberport_check=self.bool_(self.config.get("Instruments","zaberport").strip().split(",")[1])
			self.sr510port_str=self.config.get("Instruments","sr510port").strip().split(",")[0]
			self.sr510port_check=self.bool_(self.config.get("Instruments","sr510port").strip().split(",")[1])
			self.testmode_check=self.bool_(self.config.get("Instruments","testmode"))
			self.zaber_tm=self.bool_(self.config.get("Instruments","zaber_tm"))
			self.sr510_tm=self.bool_(self.config.get("Instruments","sr510_tm"))
			
		except configparser.NoOptionError as e:
			QMessageBox.critical(self, "Message","".join(["Main FAULT while reading the config.ini file\n",str(e)]))
			raise
			
		
		# Enable antialiasing for prettier plots
		self.inst_list = inst_list
		self.timer = timer
		
		self.initUI()
		
		
	def bool_(self,txt):
		
		if txt=="True":
			return True
		elif txt=="False":
			return False
		
		
	def initUI(self):
		
		empty_string = QLabel("",self)
		
		zaber_lbl = QLabel("Zaber serial port",self)
		zaber_lbl.setStyleSheet("color: blue")
		self.zaberEdit = QLineEdit(self.zaberport_str,self)
		self.zaberEdit.textChanged.connect(self.on_text_changed)
		self.zaberEdit.setEnabled(self.zaberport_check)
		self.zaberEdit.setFixedWidth(325)
		self.cb_zaber = QCheckBox("",self)
		self.cb_zaber.toggle()
		self.cb_zaber.setChecked(self.zaberport_check)
		self.zaber_status = QLabel("",self)
		
		sr510_lbl = QLabel("SR510 serial port",self)
		sr510_lbl.setStyleSheet("color: blue")
		self.sr510Edit = QLineEdit(self.sr510port_str,self)
		self.sr510Edit.textChanged.connect(self.on_text_changed)
		self.sr510Edit.setEnabled(self.sr510port_check)
		self.sr510Edit.setFixedWidth(325)
		self.cb_sr510 = QCheckBox("",self)
		self.cb_sr510.toggle()
		self.cb_sr510.setChecked(self.sr510port_check)
		self.sr510_status = QLabel("",self)
		
		testmode_lbl = QLabel("Connect instruments using the TESTMODE",self)
		testmode_lbl.setStyleSheet("color: magenta")
		self.cb_testmode = QCheckBox("",self)
		self.cb_testmode.toggle()
		self.cb_testmode.setChecked(self.testmode_check)
		
		self.connButton = QPushButton("Connect to selected ports",self)
		#self.connButton.setFixedWidth(150)
		
		self.saveButton = QPushButton("Save settings",self)
		self.saveButton.setEnabled(False)
		#self.saveButton.setFixedWidth(150)
		
		self.closeButton = QPushButton("CLOSE",self)
		self.closeButton.setEnabled(True)
		
		##############################################
		
		# Add all widgets
		g0_0 = QGridLayout()
		
		g0_0.addWidget(zaber_lbl,0,0)
		g0_0.addWidget(self.cb_zaber,0,1)
		g0_0.addWidget(self.zaberEdit,1,0)
		g0_0.addWidget(self.zaber_status,2,0)
		g0_0.addWidget(empty_string,3,0)
		
		g0_0.addWidget(sr510_lbl,4,0)
		g0_0.addWidget(self.cb_sr510,4,1)
		g0_0.addWidget(self.sr510Edit,5,0)
		g0_0.addWidget(self.sr510_status,6,0)
		g0_0.addWidget(empty_string,7,0)
		
		g0_0.addWidget(testmode_lbl,24,0)
		g0_0.addWidget(self.cb_testmode,24,1)
		
		g1_0 = QGridLayout()
		g1_0.addWidget(self.connButton,0,0)
		g1_0.addWidget(self.saveButton,0,1)
		
		g2_0 = QGridLayout()
		g2_0.addWidget(self.closeButton,0,0)
		
		v0 = QVBoxLayout()
		v0.addLayout(g0_0)
		v0.addLayout(g1_0)
		v0.addLayout(g2_0)
		
		self.setLayout(v0) 
    
    ##############################################
	
		# run the main script
		self.connButton.clicked.connect(self.set_connect)
		self.saveButton.clicked.connect(self.save_)
		self.closeButton.clicked.connect(self.close_)
		
		self.cb_zaber.stateChanged.connect(self.zaber_stch)
		self.cb_sr510.stateChanged.connect(self.sr510_stch)
		
		##############################################
		
		# Connection warnings
		if self.inst_list.get("zaber"):
			if self.zaber_tm:
				self.zaber_status.setText("Status: TESTMODE")
				self.zaber_status.setStyleSheet("color: magenta")
			else:
				self.zaber_status.setText("Status: CONNECTED")
				self.zaber_status.setStyleSheet("color: green")
		else:
			self.zaber_status.setText("Status: unknown")
			self.zaber_status.setStyleSheet("color: black")
			
		if self.inst_list.get("sr510"):
			if self.sr510_tm:
				self.sr510_status.setText("Status: TESTMODE")
				self.sr510_status.setStyleSheet("color: magenta")
			else:
				self.sr510_status.setText("Status: CONNECTED")
				self.sr510_status.setStyleSheet("color: green")
		else:
			self.sr510_status.setText("Status: unknown")
			self.sr510_status.setStyleSheet("color: black")
			
		##############################################
		
		# Check boxes
		"""
		if not self.checked_list.get("zaber"):
			self.cb_zaber.setChecked(False)
		
		if not self.checked_list.get("sr510"):
			self.cb_sr510.setChecked(False)
		
		if not self.checked_list.get("Oriel"):
			self.cb_oriel.setChecked(False)
		
		if not self.checked_list.get("K2001A"):
			self.cb_k2001a.setChecked(False)
		
		if not self.checked_list.get("Agilent34972A"):
			self.cb_a34972a.setChecked(False)
		
		if not self.checked_list.get("GUV"):
			self.cb_guv.setChecked(False)
		"""
		
		self.setWindowTitle("Pick-up instruments and connect")
		
		# re-adjust/minimize the size of the e-mail dialog
		# depending on the number of attachments
		v0.setSizeConstraint(v0.SetFixedSize)
		
		
	def zaber_stch(self, state):
		
		self.on_text_changed()
		if state in [Qt.Checked,True]:
			self.zaberEdit.setEnabled(True)
		else:
			self.zaberEdit.setEnabled(False)
			
			
	def sr510_stch(self, state):
		
		self.on_text_changed()
		if state in [Qt.Checked,True]:
			self.sr510Edit.setEnabled(True)
		else:
			self.sr510Edit.setEnabled(False)
			
			
	def on_text_changed(self):
		
		self.saveButton.setText("*Save settings*")
		self.saveButton.setEnabled(True)
		
		
	def set_connect(self):
		
		# Connect or disconnect zaber laser gun
		self.xmcb()
		
		# Connect or disconnect sr510 power meter
		self.sr510_()
		
		# Initialise all the instruments
		self.initialise()
		
		# Set the testmode check box correctly for the next run
		if self.sr510_tm and self.cb_sr510.isChecked():
			if self.zaber_tm and self.cb_zaber.isChecked():
				self.cb_testmode.setChecked(True)
			elif not self.cb_zaber.isChecked():
				self.cb_testmode.setChecked(True)
			else:
				self.cb_testmode.setChecked(False)
		elif not self.cb_sr510.isChecked():
			if self.zaber_tm and self.cb_zaber.isChecked():
				self.cb_testmode.setChecked(True)
			elif not self.cb_zaber.isChecked():
				self.cb_testmode.setChecked(False)
			else:
				self.cb_testmode.setChecked(False)
		else:
			self.cb_testmode.setChecked(False)
			
		if not self.inst_list.get("sr510") and not self.inst_list.get("zaber"):
			QMessageBox.critical(self, "Message","No instruments connected. At least 1 instrument is required.")
			return
		else:
			self.save_()
				
				
	def initialise(self):
		
		if self.inst_list.get('zaber'):
			# constants
			min_pos_lambda=self.Validrange_lambda[0]
			max_pos_lambda=self.Validrange_lambda[1]
			min_pos_slit=self.Validrange_slit[0]
			max_pos_slit=self.Validrange_slit[1]
			hc=25
			rc=50
			ms=2048
				
			try:
				self.inst_list.get('zaber').set_timeout(0.5)
				self.inst_list.get('zaber').set_Maximum_Position(1,1,max_pos_lambda)
				self.inst_list.get('zaber').set_Minimum_Position(1,1,min_pos_lambda)
				self.inst_list.get('zaber').set_Hold_Current(1,1,hc)
				self.inst_list.get('zaber').set_Running_Current(1,1,rc)
				self.inst_list.get('zaber').set_Max_Speed(1,1,ms)
				
				self.inst_list.get('zaber').set_Maximum_Position(1,2,max_pos_slit)
				self.inst_list.get('zaber').set_Minimum_Position(1,2,min_pos_slit)
				self.inst_list.get('zaber').set_Hold_Current(1,2,hc)
				self.inst_list.get('zaber').set_Running_Current(1,2,rc)
				self.inst_list.get('zaber').set_Max_Speed(1,2,ms)

				micstep_lambda=self.inst_list.get('zaber').return_Microstep_Resolution(1,1)
				sc=self.inst_list.get('zaber').return_System_Current(1)
				# TURN ON/OFF ALERTS
				if self.inst_list.get('zaber').return_Alert(1)==0:
					self.inst_list.get('zaber').set_Alert(1,1)
				
				self.inst_list.get('zaber').set_Current_Position(1,1,self.Last_position_lambda[0])
				self.inst_list.get('zaber').set_Current_Position(1,2,self.Last_position_slit[0])
			except Exception as e:
				self.inst_list.get('zaber').close()
				QMessageBox.warning(self, 'Message',"No response from the Zaber stepper! Is stepper powered and connected to the serial?")
				raise
				
			hc_str=''.join([str(hc*25e-3)," / ",str(rc*25e-3)," Amps" ])
			print("Hold / Running current:", hc_str)
			sys_str=''.join([ str(sc), " Amps" ])
			print("System current (0-5):", sys_str)
			ms_str=''.join([str(ms/1.6384), " microsteps/s"])
			print("Max speed:", ms_str)
			micstep_str=''.join([str(micstep_lambda), " microsteps/step"])
			print("Microstep resolution:", str(micstep_str))
			pos_lambda_str=''.join([str(min_pos_lambda)," to ", str(max_pos_lambda)," microsteps"])
			print(u"Stepper range for lambda:", pos_lambda_str)
			pos_slit_str=''.join([str(min_pos_slit)," to ", str(max_pos_slit)," microsteps"])
			print("Stepper range for slits:", pos_slit_str)
			
			
		if self.inst_list.get('sr510'):
			try:
				self.inst_list.get('sr510').set_timeout(1) # wait maximum 1 sec for response
				self.inst_list.get('sr510').set_wait(1) # wait 1*4ms between characters
			except Exception as e:
				self.inst_list.get('sr510').close()
				QMessageBox.warning(self, 'Message',"SR510 serial port does not respond! Is the lock-in powered and connected to the serial?")	
				raise
				
				
	def sr510_(self):
		
		# CLOSE the sr510 port before doing anything with the port
		if self.inst_list.get("sr510"):
			if self.inst_list.get("sr510").is_open():
				self.inst_list.get("sr510").close()
				self.inst_list.pop("sr510", None)
				self.sr510_status.setText("Status: device disconnected!")
				self.sr510_status.setStyleSheet("color: red")
				
		if self.cb_testmode.isChecked() and self.cb_sr510.isChecked():
			self.sr510_tm = True
			self.sr510 = SR510.SR510(str(self.sr510Edit.text()), self.sr510_tm)
			self.sr510_status.setText("Testmode: CONNECTED")
			self.sr510_status.setStyleSheet("color: magenta")
			self.inst_list.update({"sr510":self.sr510})
			
		elif not self.cb_testmode.isChecked() and self.cb_sr510.isChecked():
			try:
				self.sr510_tm = False
				self.sr510 = SR510.SR510(str(self.sr510Edit.text()), self.sr510_tm)
			except Exception as e:
				reply = QMessageBox.critical(self, 'SR510 testmode', ''.join(["SR510 could not return valid echo signal. Check the port name and check the connection.\n\n",str(e),"\n\nProceed into the testmode?"]), QMessageBox.Yes | QMessageBox.No)
				if reply == QMessageBox.Yes:
					self.sr510_tm = True
					self.sr510 = SR510.SR510(str(self.sr510Edit.text()), self.sr510_tm)
					self.sr510_status.setText("Testmode: CONNECTED")
					self.sr510_status.setStyleSheet("color: magenta")
					self.inst_list.update({"sr510":self.sr510})
				else:
					self.cb_sr510.setChecked(False)
			else:
				self.inst_list.update({"sr510":self.sr510})
				self.sr510_status.setText("Status: CONNECTED")
				self.sr510_status.setStyleSheet("color: green")
				
				val = self.inst_list.get("sr510").idn()
				print("SR510 lock-in ID:\n\t",val)
			
			
	def xmcb(self):
		
		# CLOSE the zaber port before doing anything with the port
		if self.inst_list.get("zaber"):
			if self.inst_list.get("zaber").is_open():
				self.inst_list.get("zaber").close()
				self.inst_list.pop("zaber", None)
				self.zaber_status.setText("Status: device disconnected!")
				self.zaber_status.setStyleSheet("color: red")
				
		if self.cb_testmode.isChecked() and self.cb_zaber.isChecked():
			self.zaber_tm = True
			self.zaber = ZaberXmcb_ascii.Zaber_Xmcb(str(self.zaberEdit.text()), self.zaber_tm)
			self.zaber_status.setText("Testmode: CONNECTED")
			self.zaber_status.setStyleSheet("color: magenta")
			self.inst_list.update({"zaber":self.zaber})
			
		if not self.cb_testmode.isChecked() and self.cb_zaber.isChecked():
			try:
				self.zaber_tm = False
				self.zaber = ZaberXmcb_ascii.Zaber_Xmcb(str(self.zaberEdit.text()), self.zaber_tm)
				self.zaber.set_timeout_(2)
				self.zaber.get_version()
			except Exception as e:
				reply = QMessageBox.critical(self, 'zaber testmode', ''.join(["Zaber could not return valid echo signal. Check the port name and check the connection to the laser.\n\n",str(e),"\n\nProceed into the testmode?"]), QMessageBox.Yes | QMessageBox.No)
				if reply == QMessageBox.Yes:
					self.zaber_tm = True
					self.zaber = ZaberXmcb_ascii.Zaber_Xmcb(str(self.zaberEdit.text()), self.zaber_tm)
					self.zaber_status.setText("Testmode: CONNECTED")
					self.zaber_status.setStyleSheet("color: magenta")
					self.inst_list.update({"zaber":self.zaber})
				else:
					self.cb_zaber.setChecked(False)
			else:
				self.inst_list.update({"zaber":self.zaber})
				self.zaber_status.setText("Status: CONNECTED")
				self.zaber_status.setStyleSheet("color: green")
				
				self.inst_list.get("zaber").set_timeout_(1)
				menu = self.inst_list.get("zaber").get_menu()
				self.gas_menu.setText(menu[0])
				self.gas_wl.setText(menu[1])
				self.gas_mix.setText(menu[2])
				self.laser_type.setText(self.inst_list.get("zaber").get_lasertype())
				self.pulse_counter.setText(str(self.inst_list.get("zaber").get_counter()))
				self.pulse_tot.setText(str(self.inst_list.get("zaber").get_totalcounter()))
				print("zaber ",self.inst_list.get("zaber").get_version()," ready")
				
				
	def save_(self):
		
		self.config.set("Instruments", 'testmode', str(self.cb_testmode.isChecked()) )
		self.config.set("Instruments", "zaberport", ",".join([str(self.zaberEdit.text()), str(self.cb_zaber.isChecked()) ]) )
		self.config.set("Instruments", "sr510port", ",".join([str(self.sr510Edit.text()), str(self.cb_sr510.isChecked())]) )
		self.config.set("Instruments", 'zaber_tm', str(self.zaber_tm) )
		self.config.set("Instruments", 'sr510_tm', str(self.sr510_tm) )
		
		with open(''.join([self.cwd,"/config.ini"]), "w") as configfile:
			self.config.write(configfile)
			
		self.saveButton.setText("Settings saved")
		self.saveButton.setEnabled(False)
	
	
	def close_(self):
		
		self.close()
			
			
	def closeEvent(self,event):
		
		if self.inst_list:
			self.timer.start(1000*60*5)
		event.accept()
	

