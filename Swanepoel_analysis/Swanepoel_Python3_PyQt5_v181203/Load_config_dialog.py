#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""

import os, re, serial, time

from PyQt5.QtWidgets import (QDialog, QMessageBox, QGridLayout, QLabel, QLineEdit, QComboBox, QVBoxLayout, QPushButton)



class Load_config_dialog(QDialog):

	def __init__(self, parent, config):
		super().__init__(parent)
		
		# constants
		self.config = config
		self.last_used_film = self.config.get('DEFAULT','last_used_film')

		self.setupUi()

	def setupUi(self):
		
		#self.lb0 = QLabel("Receiver(s) comma(,) separated:",self)
		#self.le1 = QLineEdit()
		#self.le1.setText(', '.join([i for i in self.emailrec_str]))
		#self.le1.textChanged.connect(self.on_text_changed)
		
		self.lbl = QLabel("Pick a section from the config file:", self)
		self.combo1 = QComboBox(self)
		mylist1=self.config.sections()
		self.combo1.addItems(mylist1)
		self.combo1.setCurrentIndex(mylist1.index(self.last_used_film))
		#self.combo1.setFixedWidth(90)
		
		self.combo1.activated[str].connect(self.onActivated1)
		
		self.btnAccept = QPushButton("Accept",self)
		self.btnAccept.clicked.connect(self.btn_accept)
		#self.btnAccept.setFixedWidth(90)
		
		self.btnReject = QPushButton("Reject",self)
		self.btnReject.clicked.connect(self.btn_reject)
		#self.btnReject.setFixedWidth(90)
		
		# set layout
		grid_0 = QGridLayout()
		grid_0.addWidget(self.lbl,0,0)
		grid_0.addWidget(self.combo1,1,0)
		
		grid_1 = QGridLayout()
		grid_1.addWidget(self.btnAccept,0,0)
		grid_1.addWidget(self.btnReject,0,1)

		v1 = QVBoxLayout()
		v1.addLayout(grid_0)
		v1.addLayout(grid_1)
		
		self.setLayout(v1)
		self.setWindowTitle("Load from config file dialog")
		
		
	def onActivated1(self, text):
		
		self.last_used_film=str(text)
		
		
	def btn_accept(self):
		
		self.config.set('DEFAULT',"last_used_film", self.last_used_film )
		
		with open('config.ini', 'w') as configfile:
			self.config.write(configfile)
			
		self.close()
	
	
	def btn_reject(self):
			
		self.close()
		
		
	def closeEvent(self,event):
	
		event.accept()
