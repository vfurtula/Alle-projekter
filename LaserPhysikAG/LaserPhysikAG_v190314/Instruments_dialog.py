#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""


import os, re, serial, time, yagmail, configparser

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QMessageBox, QGridLayout, QCheckBox, QLabel, QLineEdit, QComboBox, QFrame, QVBoxLayout, QHBoxLayout, QMenuBar, QPushButton)

import COMPexPRO, PM100USBdll



class Instruments_dialog(QDialog):
	
	def __init__(self, parent, inst_list, timer):
		super().__init__(parent)
		
		# Initial read of the config file
		self.config = configparser.ConfigParser()
		
		try:
			self.config.read("config.ini")
			
			self.compexproport_str=self.config.get("Instruments","compexproport").strip().split(",")[0]
			self.compexproport_check=self.bool_(self.config.get("Instruments","compexproport").strip().split(",")[1])
			self.pm100usbport_str=self.config.get("Instruments","pm100usbport").strip().split(",")[0]
			self.pm100usbport_check=self.bool_(self.config.get("Instruments","pm100usbport").strip().split(",")[1])
			self.testmode_check=self.bool_(self.config.get("Instruments","testmode"))
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
		
		compexPro_lbl = QLabel("COMPexPRO serial port",self)
		compexPro_lbl.setStyleSheet("color: blue")
		self.compexProEdit = QLineEdit(self.compexproport_str,self)
		self.compexProEdit.textChanged.connect(self.on_text_changed)
		self.compexProEdit.setEnabled(self.compexproport_check)
		self.compexProEdit.setFixedWidth(325)
		self.cb_compexPro = QCheckBox("",self)
		self.cb_compexPro.toggle()
		self.cb_compexPro.setChecked(self.compexproport_check)
		self.compexPro_status = QLabel("",self)
		
		pm100usb_lbl = QLabel("PM100USB serial port",self)
		pm100usb_lbl.setStyleSheet("color: blue")
		self.pm100usbEdit = QLineEdit(self.pm100usbport_str,self)
		self.pm100usbEdit.textChanged.connect(self.on_text_changed)
		self.pm100usbEdit.setEnabled(self.pm100usbport_check)
		self.pm100usbEdit.setFixedWidth(325)
		self.cb_pm100usb = QCheckBox("",self)
		self.cb_pm100usb.toggle()
		self.cb_pm100usb.setChecked(self.pm100usbport_check)
		self.pm100usb_status = QLabel("",self)
		
		testmode_lbl = QLabel("Connect instruments in the TEST mode",self)
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
		
		g0_0.addWidget(compexPro_lbl,0,0)
		g0_0.addWidget(self.cb_compexPro,0,1)
		g0_0.addWidget(self.compexProEdit,1,0)
		g0_0.addWidget(self.compexPro_status,2,0)
		g0_0.addWidget(empty_string,3,0)
		
		g0_0.addWidget(pm100usb_lbl,4,0)
		g0_0.addWidget(self.cb_pm100usb,4,1)
		g0_0.addWidget(self.pm100usbEdit,5,0)
		g0_0.addWidget(self.pm100usb_status,6,0)
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
		
		self.cb_compexPro.stateChanged.connect(self.compexPro_stch)
		self.cb_pm100usb.stateChanged.connect(self.pm100usb_stch)
		
		##############################################
		
		# Connection warnings
		if self.inst_list.get("COMPexPRO") and not self.inst_list.get("COMPexPRO_tm"):
			self.compexPro_status.setText("Status: CONNECTED")
			self.compexPro_status.setStyleSheet("color: green")
		elif self.inst_list.get("COMPexPRO") and self.inst_list.get("COMPexPRO_tm"):
			self.compexPro_status.setText("Status: CONNECTED in TESTMODE")
			self.compexPro_status.setStyleSheet("color: magenta")
		else:
			self.compexPro_status.setText("Status: unknown")
			self.compexPro_status.setStyleSheet("color: black")
			
		if self.inst_list.get("PM100USB") and not self.inst_list.get("PM100USB_tm"):
			self.pm100usb_status.setText("Status: CONNECTED")
			self.pm100usb_status.setStyleSheet("color: green")
		elif self.inst_list.get("PM100USB") and self.inst_list.get("PM100USB_tm"):
			self.pm100usb_status.setText("Status: CONNECTED in TESTMODE")
			self.pm100usb_status.setStyleSheet("color: magenta")
		else:
			self.pm100usb_status.setText("Status: unknown")
			self.pm100usb_status.setStyleSheet("color: black")
			
		##############################################
		
		# Check boxes
		"""
		if not self.checked_list.get("COMPexPRO"):
			self.cb_compexPro.setChecked(False)
		
		if not self.checked_list.get("PM100USB"):
			self.cb_pm100usb.setChecked(False)
		
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
		
		
	def compexPro_stch(self, state):
		
		self.on_text_changed()
		if state in [Qt.Checked,True]:
			self.compexProEdit.setEnabled(True)
		else:
			self.compexProEdit.setEnabled(False)
			
			
	def pm100usb_stch(self, state):
		
		self.on_text_changed()
		if state in [Qt.Checked,True]:
			self.pm100usbEdit.setEnabled(True)
		else:
			self.pm100usbEdit.setEnabled(False)
			
			
	def on_text_changed(self):
		
		self.saveButton.setText("*Save settings*")
		self.saveButton.setEnabled(True)
		
		
	def set_connect(self):
		
		##########################################
		
		if self.cb_testmode.isChecked():
			if self.cb_compexPro.isChecked():
				if self.inst_list.get("COMPexPRO"):
					if not self.inst_list.get("COMPexPRO").is_open():
						self.COMPexPRO = COMPexPRO.COMPexPRO(self.compexproport_str, True)
						self.compexPro_status.setText("Status: TEST MODE activated")
						self.compexPro_status.setStyleSheet("color: magenta")
						self.inst_list.update({"COMPexPRO":self.COMPexPRO})
						self.inst_list.update({"COMPexPRO_tm":True})
				else:
					self.COMPexPRO = COMPexPRO.COMPexPRO(self.compexproport_str, True)
					self.compexPro_status.setText("Status: TEST MODE activated")
					self.compexPro_status.setStyleSheet("color: magenta")
					self.inst_list.update({"COMPexPRO":self.COMPexPRO})
					self.inst_list.update({"COMPexPRO_tm":True})
			else:
				if self.inst_list.get("COMPexPRO"):
					if self.inst_list.get("COMPexPRO").is_open():
						self.inst_list.get("COMPexPRO").close()
					self.inst_list.pop("COMPexPRO", None)
					self.compexPro_status.setText("Status: No device connected!")
					self.compexPro_status.setStyleSheet("color: red")
				
			##########################################
			
			if self.cb_pm100usb.isChecked():
				if self.inst_list.get("PM100USB"):
					if not self.inst_list.get("PM100USB").is_open():
						self.PM100USB = PM100USBdll.PM100USBdll(self.pm100usbport_str, True)
						self.pm100usb_status.setText("Status: TEST MODE activated")
						self.pm100usb_status.setStyleSheet("color: magenta")
						self.inst_list.update({"PM100USB":self.PM100USB})
						self.inst_list.update({"PM100USB_tm":True})
				else:
					self.PM100USB = PM100USBdll.PM100USBdll(self.pm100usbport_str, True)
					self.pm100usb_status.setText("Status: TEST MODE activated")
					self.pm100usb_status.setStyleSheet("color: magenta")
					self.inst_list.update({"PM100USB":self.PM100USB})
					self.inst_list.update({"PM100USB_tm":True})
			else:
				if self.inst_list.get("PM100USB"):
					if self.inst_list.get("PM100USB").is_open():
						self.inst_list.get("PM100USB").close()
					self.inst_list.pop("PM100USB", None)
					self.pm100usb_status.setText("Status: No device connected!")
					self.pm100usb_status.setStyleSheet("color: red")
					
			##########################################
			
			keys = self.inst_list.keys() & ["COMPexPRO","PM100USB"]
			if not keys:
				QMessageBox.critical(self, "Message","No instruments connected. At least 1 instrument is required.")
				return
			else:
				self.save_()
				
		else:
			if self.cb_compexPro.isChecked():
				if self.inst_list.get("COMPexPRO"):
					if not self.inst_list.get("COMPexPRO").is_open():
						try:
							self.COMPexPRO = COMPexPRO.COMPexPRO(self.compexproport_str, False)
							self.compexPro_status.setText("Status: CONNECTED")
							self.compexPro_status.setStyleSheet("color: green")
							self.inst_list.update({"COMPexPRO":self.COMPexPRO})
							self.inst_list.update({"COMPexPRO_tm":True})
						except Exception as e:
							QMessageBox.warning(self, "Message",str(e))	
							return
						
						try:
							self.COMPexPRO.set_timeout_(None)
							
							menu = self.COMPexPRO.get_menu()
							self.gas_menu.setText(menu[0])
							self.gas_wl.setText(menu[1])
							self.gas_mix.setText(menu[2])
							self.laser_type.setText(self.COMPexPRO.get_lasertype())
							
							print("COMPexPRO ",self.COMPexPRO.get_version()," ready")
							
							self.pulse_counter.setText(str(self.COMPexPRO.get_counter()))
							self.pulse_tot.setText(str(self.COMPexPRO.get_totalcounter()))
						except Exception as e:
							self.COMPexPRO.close()
							QMessageBox.warning(self, "Message","No response from the COMPexPRO photon source! Is the photon source powered and connected to serial?")	
							return
				else:
					try:
						self.COMPexPRO = COMPexPRO.COMPexPRO(self.compexproport_str, False)
						self.compexPro_status.setText("Status: CONNECTED")
						self.compexPro_status.setStyleSheet("color: green")
						self.inst_list.update({"COMPexPRO":self.COMPexPRO})
						self.inst_list.update({"COMPexPRO_tm":True})
					except Exception as e:
						QMessageBox.warning(self, "Message",str(e))	
						return
					
					try:
						self.COMPexPRO.set_timeout_(None)
						
						menu = self.COMPexPRO.get_menu()
						self.gas_menu.setText(menu[0])
						self.gas_wl.setText(menu[1])
						self.gas_mix.setText(menu[2])
						self.laser_type.setText(self.COMPexPRO.get_lasertype())
						
						print("COMPexPRO ",self.COMPexPRO.get_version()," ready")
						
						self.pulse_counter.setText(str(self.COMPexPRO.get_counter()))
						self.pulse_tot.setText(str(self.COMPexPRO.get_totalcounter()))
					except Exception as e:
						self.COMPexPRO.close()
						QMessageBox.warning(self, "Message","No response from the COMPexPRO photon source! Is the photon source powered and connected to serial?")	
						return
				
			else:
				if self.inst_list.get("COMPexPRO"):
					if self.inst_list.get("COMPexPRO").is_open():
						self.inst_list.get("COMPexPRO").close()
					self.inst_list.pop("COMPexPRO", None)
					self.compexPro_status.setText("Status: No device connected!")
					self.compexPro_status.setStyleSheet("color: red")
					
			##########################################
			
			if self.cb_pm100usb.isChecked():
				if self.inst_list.get("PM100USB"):
					if not self.inst_list.get("PM100USB").is_open():
						try:
							self.PM100USB = PM100USBdll.PM100USBdll(self.pm100usbport_str, False)
							self.pm100usb_status.setText("Status: CONNECTED")
							self.pm100usb_status.setStyleSheet("color: green")
							self.inst_list.update({"PM100USB":self.PM100USB})
							self.inst_list.update({"PM100USB_tm":True})
						except Exception as e:
							QMessageBox.warning(self, "Message",str(e))
							return
						
						try:
							val = self.PM100USB.findRsrc()
							print("PM100USB power meter ID:\n\t",self.PM100USB.getRsrcName(val-1))
						except Exception as e:
							self.PM100USB.close()
							QMessageBox.warning(self, "Message","No response from the PM100USB device! Does the USB port point to correct PM100USB device?")
							return
				else:
					try:
						self.PM100USB = PM100USBdll.PM100USBdll(self.pm100usbport_str, False)
						self.pm100usb_status.setText("Status: CONNECTED")
						self.pm100usb_status.setStyleSheet("color: green")
						self.inst_list.update({"PM100USB":self.PM100USB})
						self.inst_list.update({"PM100USB_tm":True})
					except Exception as e:
						QMessageBox.warning(self, "Message",str(e))
						return
					
					try:
						val = self.PM100USB.findRsrc()
						print("PM100USB power meter ID:\n\t",self.PM100USB.getRsrcName(val-1))
					except Exception as e:
						self.PM100USB.close()
						QMessageBox.warning(self, "Message","No response from the PM100USB device! Does the USB port point to correct PM100USB device?")
						return
				
			else:
				if self.inst_list.get("PM100USB"):
					if self.inst_list.get("PM100USB").is_open():
						self.inst_list.get("PM100USB").close()
					self.inst_list.pop("PM100USB", None)
					self.pm100usb_status.setText("Status: No device connected!")
					self.pm100usb_status.setStyleSheet("color: red")
					
			##########################################
			
			keys = self.inst_list.keys() & ["COMPexPRO","PM100USB"]
			if not keys:
				QMessageBox.critical(self, "Message","No instruments connected. At least 1 instrument is required.")
				return
			else:
				self.save_()
		
		
	def save_(self):
		
		self.config.set("Instruments", 'testmode', str(self.cb_testmode.isChecked()) )
		self.config.set("Instruments", "compexproport", ",".join([str(self.compexProEdit.text()), str(self.cb_compexPro.isChecked()) ]) )
		self.config.set("Instruments", "pm100usbport", ",".join([str(self.pm100usbEdit.text()), str(self.cb_pm100usb.isChecked())]) )
		
		with open("config.ini", "w") as configfile:
			self.config.write(configfile)
			
		self.saveButton.setText("Settings saved")
		self.saveButton.setEnabled(False)
	
	
	def close_(self):
		
		self.close()
			
			
	def closeEvent(self,event):
		
		if self.inst_list:
			self.timer.start(1000*60*5)
		event.accept()
	

