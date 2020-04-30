#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""



import traceback, sys, os, sqlite3, configparser
import re, serial, time, datetime, numpy, random, yagmail, visa, scipy.io
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm

from PyQt5.QtCore import QObject, QThreadPool, QTimer, QRunnable, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import (QWidget, QMainWindow, QLCDNumber, QMessageBox, QGridLayout, QHeaderView,
														 QLabel, QLineEdit, QComboBox, QFrame, QTableWidget, QTableWidgetItem,
														 QVBoxLayout, QHBoxLayout, QApplication, QMenuBar, QPushButton)

import MS257, K2001A
import MS257_dialog, K2001A_dialog, Oriel_dialog, Agilent34972A_dialog, Message_dialog
import Email_settings_dialog, Send_email_dialog, Instruments_dialog, Write2file_dialog







class WorkerSignals(QObject):
	
	# Create signals to be used
	update1 = pyqtSignal(object)
	update2 = pyqtSignal(object)
	update3 = pyqtSignal(object)
	update4 = pyqtSignal(object)
	warning = pyqtSignal(object)
	
	error = pyqtSignal(tuple)
	finished = pyqtSignal()








class Email_Worker(QRunnable):
	'''
	Worker thread
	:param args: Arguments to make available to the run code
	:param kwargs: Keywords arguments to make available to the run code
	'''
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
		'''
		Initialise the runner function with passed args, kwargs.
		'''
		# Retrieve args/kwargs here; and fire processing using them
		try:
			self.yag = yagmail.SMTP(self.emailset_str[0])
			self.yag.send(to=self.emailrec_str, subject=self.subject, contents=self.contents)
		except Exception as e:
			self.signals.warning.emit(str(e))
			
		self.signals.finished.emit()
			
			
			
			
			
			
			
			
					
					
					
					
					
class Run_TEST(QMainWindow):
	
	def __init__(self):
		super().__init__()
		
		self.load_()
		
		# Enable antialiasing for prettier plots		
		self.initUI()
			
	def initUI(self):
		
		################### MENU BARS START ##################
		
		MyBar = QMenuBar(self)
		fileMenu = MyBar.addMenu("File")
		write2file = fileMenu.addAction("Write to file")
		write2file.triggered.connect(self.write2fileDialog)
		fileSaveSet = fileMenu.addAction("Save settings")        
		fileSaveSet.triggered.connect(self.save_) # triggers closeEvent()
		fileSaveSet.setShortcut('Ctrl+S')
		fileClose = fileMenu.addAction("Close")        
		fileClose.triggered.connect(self.close) # triggers closeEvent()
		fileClose.setShortcut('Ctrl+X')
		
		self.emailMenu = MyBar.addMenu("E-mail")
		self.emailSet = self.emailMenu.addAction("E-mail settings")
		self.emailSet.triggered.connect(self.email_set_dialog)
		self.emailData = self.emailMenu.addAction("E-mail data")
		self.emailData.triggered.connect(self.email_data_dialog)
				
		################### MENU BARS END ##################
		
		lbl0 = QLabel("Register new instrument:", self)
		lbl0.setStyleSheet("color: blue")
		
		lbl01 = QLabel("Type:", self)
		self.lbl01_Edit = QLineEdit('',self)
		self.lbl01_Edit.setFixedWidth(200)
		lbl02 = QLabel("Make:", self)
		self.lbl02_Edit = QLineEdit('',self)
		self.lbl02_Edit.setFixedWidth(200)
		lbl03 = QLabel("Weight:", self)
		self.lbl03_Edit = QLineEdit('',self)
		self.lbl03_Edit.setFixedWidth(75)
		lbl04 = QLabel("Size:", self)
		self.lbl04_Edit = QLineEdit('',self)
		self.lbl04_Edit.setFixedWidth(110)
		
		lbl05 = QLabel("Search in the database:", self)
		lbl05.setStyleSheet("color: blue")
		self.lbl05_Edit = QLineEdit('',self)
		self.lbl05_Edit.textChanged.connect(self.search)
		self.lbl05_Edit.setFixedHeight(35)
		
		self.regButton = QPushButton("Register row",self)
		self.regButton.setStyleSheet('QPushButton {font-size: 15pt}')
		self.regButton.setFixedHeight(50)
		#self.regButton.setFixedWidth(110)
		
		self.unregButton = QPushButton("Unregister row(s)",self)
		self.unregButton.setStyleSheet('QPushButton {font-size: 15pt}')
		self.unregButton.setFixedHeight(50)
		#self.unregButton.setFixedWidth(110)
		self.unregButton.setEnabled(False)
		
		self.unregSearchButton = QPushButton("Unregister row(s)",self)
		self.unregSearchButton.setStyleSheet('QPushButton {font-size: 15pt}')
		#self.unregButton.setFixedHeight(50)
		#self.unregButton.setFixedWidth(110)
		self.unregSearchButton.setEnabled(False)
		
		##############################################
		
		lbl06 = QLabel("ID-number:", self)
		self.lcd = QLCDNumber(self)
		self.lcd.setStyleSheet("color: red")
		self.lcd.setFixedHeight(50)
		self.lcd.setSegmentStyle(QLCDNumber.Flat)
		self.lcd.setNumDigits(9)
		self.lcd.display(self.time_str+'-'+self.num_str)
		
		##############################################
		
		# create upload table
		self.add2tab = self.createTable()
		selectionModel = self.add2tab.selectionModel()
		selectionModel.selectionChanged.connect(self.selChanged)
		
		# create search table
		self.searchInTab = self.createTable()
		selectionModel = self.searchInTab.selectionModel()
		selectionModel.selectionChanged.connect(self.selSearchChanged)
		
		##############################################
		
		# Add all widgets
		g1_0 = QVBoxLayout()
		g1_0.addWidget(MyBar)
		g1_0.addWidget(lbl0)
		
		g1_1 = QGridLayout()
		g1_1.addWidget(lbl01,0,0)
		g1_1.addWidget(self.lbl01_Edit,1,0)
		g1_1.addWidget(lbl02,0,1)
		g1_1.addWidget(self.lbl02_Edit,1,1)
		g1_1.addWidget(lbl03,0,2)
		g1_1.addWidget(self.lbl03_Edit,1,2)
		g1_1.addWidget(lbl04,0,3)
		g1_1.addWidget(self.lbl04_Edit,1,3)
		
		g1_2 = QGridLayout()
		g1_2.addWidget(lbl06,0,0)
		g1_2.addWidget(self.lcd,1,0)
		g1_2.addWidget(self.regButton,1,1)
		g1_2.addWidget(self.unregButton,1,2)
		
		g1_3 = QGridLayout()
		g1_3.addWidget(self.add2tab,0,0)
		
		g1_4 = QGridLayout()
		g1_4.addWidget(lbl05,0,0)
		g1_4.addWidget(self.lbl05_Edit,1,0)
		g1_4.addWidget(self.unregSearchButton,1,1)
		
		g1_5 = QGridLayout()
		g1_5.addWidget(self.searchInTab,0,0)
		
		# add all groups from v1 to v6 in one vertical group v7
		v0 = QVBoxLayout()
		v0.addLayout(g1_0)
		v0.addLayout(g1_1)
		v0.addLayout(g1_2)
		v0.addLayout(g1_3)
		v0.addLayout(g1_4)
		v0.addLayout(g1_5)
		
		##############################################
		
		# Initialize and set titles and axis names for both plots
		self.clear_vars_graphs()
		
		##############################################
		
		# save all paramter data in the config file
		#self.saveButton.clicked.connect(self.save_)
		#self.saveButton.clicked.connect(self.set_elapsedtime_text)
	
		# run the main script
		self.regButton.clicked.connect(self.register)
		self.unregButton.clicked.connect(self.unregister)
		self.unregSearchButton.clicked.connect(self.unregisterSearch)
		
		##############################################
		
		#self.allEditFields(False)
		
		self.threadpool = QThreadPool()
		print("Multithreading in TEST_gui_v1 with maximum %d threads" % self.threadpool.maxThreadCount())
		self.isRunning = False
		self.prepare_file()
		
		##############################################
		
		#self.setGeometry(100, 100, 800, 450)
		self.setWindowTitle("LIMS - NTNU, Institutt for fysikk")
		# re-adjust/minimize the size of the e-mail dialog
		# depending on the number of attachments
		v0.setSizeConstraint(v0.SetFixedSize)
		
		w = QWidget()
		w.setLayout(v0)
		self.setCentralWidget(w)
		self.show()
		
		
	def set_bstyle_v1(self,button):
		button.setStyleSheet('QPushButton {font-size: 25pt}')
		button.setFixedWidth(40)
		button.setFixedHeight(65)
		
		
	def createTable(self):
		tableWidget = QTableWidget()
		#tableWidget.setFixedWidth(260)
		
		# When you click on an item, the entire row is selected
		tableWidget.setSelectionBehavior(QTableWidget.SelectRows)
		
		# set row count
		#tableWidget.setRowCount(20)
		
		# set column count
		tableWidget.setColumnCount(6)
		# hide grid
		tableWidget.setShowGrid(False)
		# hide vertical header
		vh = tableWidget.verticalHeader()
		vh.setVisible(False)
		# set the font
		font = QFont("Courier New", 9)
		tableWidget.setFont(font)
		tableWidget.setStyleSheet("color: blue")
		
		# place content into individual table fields
		#tableWidget.setItem(0,0, QTableWidgetItem("abe"))
		
		tableWidget.setHorizontalHeaderLabels(["Type","Make","Weight","Size","ID number","*Status*"])
		
		# set horizontal header properties
		hh = tableWidget.horizontalHeader()
		for tal in range(6):
			if tal==5:
				hh.setSectionResizeMode(tal, QHeaderView.Stretch)
				#hh.setColumnWidth(tal, 75)
			else:
				hh.setSectionResizeMode(tal, QHeaderView.ResizeToContents)
		
		# set column width to fit contents
		tableWidget.resizeColumnsToContents()
		
		# enable sorting
		#tableWidget.setSortingEnabled(True)
		
		return tableWidget
	
	
	def allEditFields(self,trueorfalse):
		
		self.startEdit.setEnabled(trueorfalse)
		self.stopEdit.setEnabled(trueorfalse)
		self.stepEdit.setEnabled(trueorfalse)
		self.dwelltimeEdit.setEnabled(trueorfalse)
		
		self.runButton.setEnabled(trueorfalse)
		
		self.combo2.setEnabled(trueorfalse)
		self.combo3.setEnabled(trueorfalse)
		self.combo4.setEnabled(trueorfalse)
		if not self.inst_list.get("Oriel"):
			self.combo5.setEnabled(False)
		else:
			self.combo5.setEnabled(trueorfalse)
		self.combo6.setEnabled(trueorfalse)
		self.combo7.setEnabled(trueorfalse)
			
			
	def write2fileDialog(self):
		
		self.Write2file_dialog = Write2file_dialog.Write2file_dialog(self, self.config)
		self.Write2file_dialog.exec()
		
		
	def email_data_dialog(self):
		
		self.Send_email_dialog = Send_email_dialog.Send_email_dialog(self, self.config)
		self.Send_email_dialog.exec()
		
		
	def email_set_dialog(self):
		
		self.Email_dialog = Email_settings_dialog.Email_dialog(self, self.config)
		self.Email_dialog.exec()
		
		
	def create_file(self,mystr):
		
		head, tail = os.path.split(mystr)
		# Check for possible name conflicts
		if tail:
			saveinfile=''.join([tail])
		else:
			saveinfile=''.join(["SQLdatabase"])
			
		if head:
			if not os.path.isdir(head):
				os.mkdir(head)
			saveinfolder=''.join([head,"/"])
		else:
			saveinfolder=""
			
		return ''.join([saveinfolder,saveinfile])
	
	
	def prepare_file(self):
		'''
		# Save to a textfile
		if self.write2txt_check:
			self.textfile = ''.join([self.create_file(self.write2txt_str),".txt"])
			with open(self.textfile, 'w') as thefile:
				thefile.write(''.join(["Type\tMake\tWeight\tSize\n"]))
		
		# Save to a MATLAB datafile
		if self.write2mat_check:
			self.matfile = ''.join([self.create_file(self.write2mat_str),".mat"])
		'''
		
		# First delete the database file if it exists
		self.dbfile = ''.join([self.create_file(self.write2db_str),".db"])
		
		# Create or load a table for new inputs
		self.conn = sqlite3.connect(self.dbfile)
		self.db = self.conn.cursor()
		self.db.execute('''CREATE TABLE IF NOT EXISTS table1 (type text, make text, weight text, size text, idnumber text, status text)''')
		
		# Create virtual table for full text searches
		self.db.execute('''CREATE VIRTUAL TABLE IF NOT EXISTS table1Search USING fts4(type text, make text, weight text, size text, idnumber text, status text)''')
		#self.db.execute("DELETE FROM table1Search" )
		#self.db.execute("INSERT INTO table1Search SELECT type, make, weight, size, idnumber FROM table1" )
		
		
	def register(self):
		
		if not str(self.lbl01_Edit.text()) and not str(self.lbl02_Edit.text()) and not str(self.lbl03_Edit.text()) and not str(self.lbl04_Edit.text()):
			QMessageBox.critical(self, 'Message', "All fields are empty!")
			return
			
		self.updateNumber()
		
		# Save to a database file
		'''CREATE TABLE spectra (wavelength real, voltage real, position text, shutter real, idnumber real, absolutetime text)'''
		self.db.execute(''.join(["INSERT INTO table1 VALUES ('",str(self.lbl01_Edit.text()),"','", str(self.lbl02_Edit.text()), "','", str(self.lbl03_Edit.text()),"','", str(self.lbl04_Edit.text()),"','", self.time_str+'-'+self.num_str, "','", 'REGISTERED',"')"]))
		
		self.db.execute(''.join(["INSERT INTO table1Search VALUES ('",str(self.lbl01_Edit.text()),"','", str(self.lbl02_Edit.text()), "','", str(self.lbl03_Edit.text()),"','", str(self.lbl04_Edit.text()),"','", self.time_str+'-'+self.num_str, "','", 'REGISTERED',"')"]))
		# Save (commit) the changes
		self.conn.commit()
			
		#################################################
		'''
		if self.write2mat_check:
			# save to a MATLAB file
			matdata={}
			matdata['wavelength']=self.new_position_
			matdata['voltage']=self.all_data_
			matdata['position']=self.pos_
			matdata['shutter']=self.shutter_
			matdata['idnumber']=self.timelist_
			matdata['absolutetime']=self.dateandtime_
			
			scipy.io.savemat(self.matfile, matdata)
			#print(scipy.io.loadmat(self.matfile).keys()) 
			#b = scipy.io.loadmat(self.matfile)
			#print(b['wavelength'])
		
		#################################################
		
		if self.write2txt_check:
			# Save to a readable textfile
			with open(self.textfile, 'a') as thefile:
				thefile.write("%s " %str(self.lbl01_Edit.text()))
				thefile.write("\t%s" %str(self.lbl02_Edit.text()))
				thefile.write("\t%s" %str(self.lbl03_Edit.text()))
				thefile.write("\t%s\n" %str(self.lbl04_Edit.text()))
		'''
		#################################################
		
		self.save_()
		
		self.tal+=1
		
		# set row height
		self.add2tab.setRowCount(self.tal+1)
		self.add2tab.setRowHeight(self.tal,14)
		
		# add row elements
		self.add2tab.setItem(self.tal, 0, QTableWidgetItem(str(self.lbl01_Edit.text())) )
		self.add2tab.setItem(self.tal, 1, QTableWidgetItem(str(self.lbl02_Edit.text())) )
		self.add2tab.setItem(self.tal, 2, QTableWidgetItem(str(self.lbl03_Edit.text())) )
		self.add2tab.setItem(self.tal, 3, QTableWidgetItem(str(self.lbl04_Edit.text())) )
		self.add2tab.setItem(self.tal, 4, QTableWidgetItem(self.time_str+'-'+self.num_str) )
		self.add2tab.setItem(self.tal, 5, QTableWidgetItem("REGISTERED") )
		self.add2tab.item(self.tal, 5).setForeground(QColor(0,204,0) ) # dark green
		
		
	def selChanged(self):
		
		self.unregButton.setEnabled(True)
		try:
			row = self.add2tab.currentItem().row()
			col = self.add2tab.currentItem().column()
		except Exception as e:
			QMessageBox.critical(self, 'Message', str(e))
			return
		
		self.lbl01_Edit.setText(str(self.add2tab.item(row,0).text()) )
		self.lbl02_Edit.setText(str(self.add2tab.item(row,1).text()) )
		self.lbl03_Edit.setText(str(self.add2tab.item(row,2).text()) )
		self.lbl04_Edit.setText(str(self.add2tab.item(row,3).text()) )
		
		
	def selSearchChanged(self):
		
		self.unregSearchButton.setEnabled(True)
		try:
			row = self.searchInTab.currentItem().row()
			col = self.searchInTab.currentItem().column()
		except Exception as e:
			QMessageBox.critical(self, 'Message', str(e))
			return
		
		self.lbl01_Edit.setText(str(self.searchInTab.item(row,0).text()) )
		self.lbl02_Edit.setText(str(self.searchInTab.item(row,1).text()) )
		self.lbl03_Edit.setText(str(self.searchInTab.item(row,2).text()) )
		self.lbl04_Edit.setText(str(self.searchInTab.item(row,3).text()) )
		
		
	def unregister(self):
		
		#rows=[]
		for idx in self.add2tab.selectionModel().selectedRows():
			row=idx.row()
			#rows.append([idx.row()])
			#row = self.add2tab.currentItem().row()
			#col = self.add2tab.currentItem().column()
			
			if str(self.add2tab.item(row,5).text()) in ["UNREGISTERED","*REGISTERED*"]:
				QMessageBox.warning(self, 'Message', ''.join(["The item with ID-number \"", str(self.add2tab.item(row,4).text()), "\" is already removed!"]) )
			else:
				self.add2tab.setItem(row, 5, QTableWidgetItem("*REGISTERED*") )
				self.add2tab.item(row, 5).setForeground(QColor(0,204,0) ) # dark green
				
				# Save to a database file
				'''CREATE TABLE spectra (wavelength real, voltage real, position text, shutter real, idnumber real, absolutetime text)'''
				self.db.execute("UPDATE table1 SET status=? WHERE idnumber=?", ('UNREGISTERED', str(self.add2tab.item(row,4).text())))
				self.db.execute("UPDATE table1Search SET status=? WHERE idnumber=?", ('UNREGISTERED', str(self.add2tab.item(row,4).text())))
				
				# Save (commit) the changes
				self.conn.commit()
				
				#################################################
				
				self.tal+=1
				
				# set row height
				self.add2tab.setRowCount(self.tal+1)
				self.add2tab.setRowHeight(self.tal,14)
				
				# add row elements
				self.add2tab.setItem(self.tal, 0, QTableWidgetItem(str(self.add2tab.item(row,0).text())) )
				self.add2tab.setItem(self.tal, 1, QTableWidgetItem(str(self.add2tab.item(row,1).text())) )
				self.add2tab.setItem(self.tal, 2, QTableWidgetItem(str(self.add2tab.item(row,2).text())) )
				self.add2tab.setItem(self.tal, 3, QTableWidgetItem(str(self.add2tab.item(row,3).text())) )
				self.add2tab.setItem(self.tal, 4, QTableWidgetItem(str(self.add2tab.item(row,4).text())) )
				self.add2tab.setItem(self.tal, 5, QTableWidgetItem("UNREGISTERED") )
				self.add2tab.item(self.tal, 5).setForeground(QColor(255,0,0) ) # dark green
				
		self.unregButton.setEnabled(False)
		
		
	def search(self):
		
		self.searchInTab.clearContents()
		self.tal_=-1
		for row in self.db.execute("SELECT * FROM table1Search WHERE table1Search MATCH ?", (''.join([str(self.lbl05_Edit.text()),'*']),)):
			# set row height
			self.tal_+=1
			self.searchInTab.setRowCount(self.tal_+1)
			self.searchInTab.setRowHeight(self.tal_,14)
			
			tal=0
			for element in row:
				# add row elements
				self.searchInTab.setItem(self.tal_, tal, QTableWidgetItem(element) )
				tal+=1
			
			self.searchInTab.setItem(self.tal_, 5, QTableWidgetItem("REGISTERED") )
			self.searchInTab.item(self.tal_, 5).setForeground(QColor(0,204,0) ) # dark green
			
			
	def unregisterSearch(self):
		
		#rows=[]
		for idx in self.searchInTab.selectionModel().selectedRows():
			row=idx.row()
			#rows.append([idx.row()])
			#row = self.searchInTab.currentItem().row()
			#col = self.searchInTab.currentItem().column()
			
			if str(self.searchInTab.item(row,5).text()) in ["UNREGISTERED","*REGISTERED*"]:
				QMessageBox.warning(self, 'Message', ''.join(["The item with ID-number \"", str(self.searchInTab.item(row,4).text()), "\" is already removed!"]) )
			else:
				self.searchInTab.setItem(row, 5, QTableWidgetItem("*REGISTERED*") )
				self.searchInTab.item(row, 5).setForeground(QColor(0,204,0) ) # dark green
				
				# Save to a database file
				'''CREATE TABLE spectra (wavelength real, voltage real, position text, shutter real, idnumber real, absolutetime text)'''
				self.db.execute("UPDATE table1 SET status=? WHERE idnumber=?", ('UNREGISTERED', str(self.searchInTab.item(row,4).text())))
				self.db.execute("UPDATE table1Search SET status=? WHERE idnumber=?", ('UNREGISTERED', str(self.searchInTab.item(row,4).text())))
				
				# Save (commit) the changes
				self.conn.commit()
				
				#################################################
				
				self.tal+=1
				
				# set row height
				self.add2tab.setRowCount(self.tal+1)
				self.add2tab.setRowHeight(self.tal,14)
				
				# add row elements
				self.add2tab.setItem(self.tal, 0, QTableWidgetItem(str(self.searchInTab.item(row,0).text())) )
				self.add2tab.setItem(self.tal, 1, QTableWidgetItem(str(self.searchInTab.item(row,1).text())) )
				self.add2tab.setItem(self.tal, 2, QTableWidgetItem(str(self.searchInTab.item(row,2).text())) )
				self.add2tab.setItem(self.tal, 3, QTableWidgetItem(str(self.searchInTab.item(row,3).text())) )
				self.add2tab.setItem(self.tal, 4, QTableWidgetItem(str(self.searchInTab.item(row,4).text())) )
				self.add2tab.setItem(self.tal, 5, QTableWidgetItem("UNREGISTERED") )
				self.add2tab.item(self.tal, 5).setForeground(QColor(255,0,0) ) # dark green
				
		self.unregSearchButton.setEnabled(False)
			
			
	def finished(self):
		
		if self.write2db_check:
			for row in self.db.execute('SELECT voltage, idnumber FROM spectra WHERE idnumber>? ORDER BY idnumber DESC', (10,)):
				print(row)
			print('\r')
			
			for row in self.db.execute('SELECT shutter, voltage, idnumber, absolutetime FROM spectra WHERE idnumber BETWEEN ? AND ? AND shutter=? ORDER BY idnumber DESC', (5,15,0)):
				print(row)
			print('\r')
			
			lis=[1450.0,1,'B']
			for row in self.db.execute('SELECT * FROM spectra WHERE wavelength=? AND shutter=? AND position=?',(lis[0],lis[1],lis[2])):
				print(row)
			
			# We can also close the connection if we are done with it.
			# Just be sure any changes have been committed or they will be lost.
			self.conn.close()
		
		self.load_()
		if self.emailset_str[1] == "yes":
			self.send_notif()
		if self.emailset_str[2] == "yes":
			self.send_data()
		
		#self.make_3Dplot()
		
		self.isRunning=False
		
		self.allEditFields(True)
		self.regButton.setText("Register")
		
		
	def warning(self, mystr):
		
		QMessageBox.warning(self, 'Message', mystr)
	
	
	def send_notif(self):
		
		self.md1 = Message_dialog.Message_dialog(self, "Sending notification", "...please wait...")
		
		contents=["The scan is done. Please visit the experiment site and make sure that all light sources are switched off."]
		subject="The scan is done"
		
		obj = type('obj',(object,),{'subject':subject, 'contents':contents, 'settings':self.emailset_str, 'receivers':self.emailrec_str})
		worker=Email_Worker(obj)
		
		worker.signals.warning.connect(self.warning)
		worker.signals.finished.connect(self.finished1)
		
		# Execute
		self.threadpool.start(worker)
		
	def finished1(self):
		
		self.md1.close_()
		
		
	def send_data(self):
		
		self.md2 = Message_dialog.Message_dialog(self, "Sending data", "...please wait...")
		
		contents=["The scan is  done and the logged data is attached to this email. Please visit the experiment site and make sure that all light sources are switched off."]
		subject="The scan data from the latest scan!"
		
		if self.write2txt_check:
			contents.extend([self.textfile])
		if self.write2db_check:
			contents.extend([self.dbfile])
		if self.write2mat_check:
			contents.extend([self.matfile])
			
		obj = type('obj',(object,),{'subject':subject, 'contents':contents, 'settings':self.emailset_str, 'receivers':self.emailrec_str})
		worker=Email_Worker(obj)
		
		worker.signals.warning.connect(self.warning)
		worker.signals.finished.connect(self.finished2)
		
		# Execute
		self.threadpool.start(worker)
		
		
	def finished2(self):
		
		self.md2.close_()
		
		
	def clear_vars_graphs(self):
		# PLOT 2 initial canvas settings
		self.tal = -1
		
		self.new_position_=[]
		self.all_data_=[]
		self.pos_=[]
		self.shutter_=[]
		self.timelist_=[]
		self.dateandtime_=[]
		self.add2tab.clearContents()
		
		
	def load_(self):
		# Initial read of the config file
		self.config = configparser.ConfigParser()
		
		try:
			self.config.read('config.ini')
			
			self.write2txt_str=self.config.get('DEFAULT','write2txt').strip().split(',')[0]
			self.write2txt_check=self.bool_(self.config.get('DEFAULT','write2txt').strip().split(',')[1])
			self.write2db_str=self.config.get('DEFAULT','write2db').strip().split(',')[0]
			self.write2db_check=self.bool_(self.config.get('DEFAULT','write2db').strip().split(',')[1])
			self.write2mat_str=self.config.get('DEFAULT','write2mat').strip().split(',')[0]
			self.write2mat_check=self.bool_(self.config.get('DEFAULT','write2mat').strip().split(',')[1])
			self.time_str = self.config.get('DEFAULT','timetrace')
			self.num_str = self.config.get('DEFAULT','numtrace')
			
			self.emailrec_str = self.config.get('DEFAULT','emailrec').strip().split(',')
			self.emailset_str = self.config.get('DEFAULT','emailset').strip().split(',')
		except configparser.NoOptionError as nov:
			QMessageBox.critical(self, 'Message',''.join(["Main FAULT while reading the config.ini file\n",str(nov)]))
			raise
		
		
	def bool_(self,txt):
		
		if txt=="True":
			return True
		elif txt=="False":
			return False
		
	
	def updateNumber(self):
		
		time_str=time.strftime("%y%m%d")
		self.num_str = int(self.num_str)
		
		if time_str==self.time_str:
			self.num_str+=1
		else:
			self.num_str=0
		
		self.num_str = str(self.num_str)
		
		
	def save_(self):
		self.time_str=time.strftime("%y%m%d")
		self.lcd.display(self.time_str+'-'+self.num_str)
		
		self.config.set('DEFAULT','timetrace',self.time_str)
		self.config.set('DEFAULT','numtrace',self.num_str)
		
		with open('config.ini', 'w') as configfile:
			self.config.write(configfile)
			
			
	def closeEvent(self, event):
		reply = QMessageBox.question(self, 'Message', "Quit now? Changes will not be saved!", QMessageBox.Yes | QMessageBox.No)
		if reply == QMessageBox.Yes:
			event.accept()
		else:
		  event.ignore() 
		
		
#########################################
#########################################
#########################################
	
	
def main():
	
	app = QApplication(sys.argv)
	ex = Run_TEST()
	#sys.exit(app.exec())

	# avoid message 'Segmentation fault (core dumped)' with app.deleteLater()
	app.exec()
	app.deleteLater()
	sys.exit()
	
	
if __name__ == '__main__':
		
	main()
	
	
