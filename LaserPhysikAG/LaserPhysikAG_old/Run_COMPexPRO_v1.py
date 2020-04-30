import os, sys, re, imp, serial, time, numpy, yagmail
import matplotlib as mpl
import matplotlib.cm as cm
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
#import pyqtgraph.opengl as gl
import pyqtgraph.exporters
#from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, SIGNAL
import config_COMPexPRO, COMPexPRO
import numpy.polynomial.polynomial as poly
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class Run_COMPexPRO_Thread(QThread):
	
	def __init__(self,*argv):
		QThread.__init__(self)
		
		# constants	
		self.end_flag=False
		
		self.rate = argv[0]
		self.hv = argv[1]
		self.timeout_str = argv[2]
		self.warmup_str = argv[3]
		self.warmup = argv[4]
		self.trigger_str = argv[5]
		self.gasmode_str = argv[6]
		self.pulse_time = argv[7]
		
		self.data_file = argv[8]
		self.timetrace_str = argv[9]
		self.COMPexPRO = argv[10]
		self.stopButton = argv[11]

	def __del__(self):
		
		self.wait()
	
	def abort(self):
		
		self.end_flag=True
	
	def run(self):
		
		self.COMPexPRO.set_timeout(self.timeout_str)
		self.COMPexPRO.set_trigger(self.trigger_str)
			
		if self.warmup_str=='ON':
			self.warmup_on()
		
		with open(self.data_file, 'w') as thefile:
			thefile.write("Your comment line - do NOT delete this line\n") 
			thefile.write("Col 0: Elapsed time [s]\nCol 1: Total counter (1000)\nCol 2: Pulse rate [Hz]\nCol 3: High volt. [kV]\n")
			thefile.write("Col 4: Beam energy [mJ]\nCol 5: Laser tube press. [mbar]\nCol 6: Laser tube temp. [C]\n")
			thefile.write("Col 7: Buffer press. [mbar]\n\n")
			thefile.write('%s\t\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' %(tuple(''.join(["Col ",str(tal)]) for tal in range(8))))
		
		self.start_source()
	
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
		self.COMPexPRO.set_opmode('SKIP')
		self.COMPexPRO.set_gasmode(self.gasmode_str)
		self.COMPexPRO.set_reprate(str(self.rate))
		self.COMPexPRO.set_hv(str(self.hv))

		str_on = self.COMPexPRO.set_opmode('ON')
		if str_on:
			if str_on=="ON":
				print "Pulsing, "+str_on
		
		self.stopButton.setText("STOP source")
		self.stopButton.setEnabled(True)
		time_start=time.time()
		
		while True:
			if self.end_flag==True:
				break
			elif time.time()-time_start>=self.pulse_time:
				break
			else:
				counter = self.COMPexPRO.get_counter()
				if counter!=None:
					self.emit(SIGNAL('update_pulse_lcd(PyQt_PyObject)'),counter)
				
				totalcounter = self.COMPexPRO.get_totalcounter()
				if totalcounter!=None:
					self.emit(SIGNAL('update_pulse_lcd2(PyQt_PyObject)'),totalcounter)
				
				egy = self.COMPexPRO.get_energy()
				lt_press = self.COMPexPRO.get_lt_press()
				lt_temp = self.COMPexPRO.get_lt_temp()
				buffer_press = self.COMPexPRO.get_buffer_press()
				f2_press = self.COMPexPRO.get_f2_press()
				f2_temp = self.COMPexPRO.get_f2_temp()
				pulse_diff = self.COMPexPRO.get_pulse_diff()
				pow_stab = self.COMPexPRO.get_pow_stab()
				
				time_elap=time.time()-time_start
				if egy!=None:
					self.emit(SIGNAL('make_update1(PyQt_PyObject,PyQt_PyObject)'),time_elap,1e-3*egy)
				if lt_press!=None and lt_temp!=None:
					self.emit(SIGNAL('make_update2(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),time_elap,1e-3*lt_press,lt_temp)
				if buffer_press!=None:
					self.emit(SIGNAL('make_update3(PyQt_PyObject,PyQt_PyObject)'),time_elap,1e-3*buffer_press)
				if f2_press!=None and f2_temp!=None:
					self.emit(SIGNAL('make_update4(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),time_elap,1e-3*f2_press,f2_temp)
				if pulse_diff!=None:
					self.emit(SIGNAL('make_update5(PyQt_PyObject,PyQt_PyObject)'),time_elap,pulse_diff)
				if pow_stab:
					if pow_stab=="YES":
						pow_stab=1
					elif pow_stab=="NO":
						pow_stab=0
					self.emit(SIGNAL('make_update6(PyQt_PyObject,PyQt_PyObject)'),time_elap,pow_stab)
				
				if totalcounter and egy and lt_press and lt_temp and buffer_press:
					with open(self.data_file, 'a') as thefile:
						thefile.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' %(time_elap,totalcounter,self.rate,self.hv,egy,lt_press,lt_temp,buffer_press))
			
		str_on = self.COMPexPRO.set_opmode('OFF')
		if str_on:
			if str_on[:3]=="OFF":
				print "Stopped, "+str_on
		
		if self.warmup_str=="ON":
			self.stopButton.setText("SKIP warm-up")
		else:
			self.stopButton.setText("STOP source")
			
			
			
			
class Email_dialog(QtGui.QDialog):

	def __init__(self, lcd, parent=None):
		QtGui.QDialog.__init__(self, parent)
		
		# constants
		self.emailrec_str = config_COMPexPRO.emailrec
		self.emailset_str = config_COMPexPRO.emailset
		
		self.lcd = lcd
		
		self.setupUi()

	def setupUi(self):
		
		grid_0 = QtGui.QGridLayout()
		
		self.lb4 = QtGui.QLabel("Active gmail account:",self)
		self.lb5 = QtGui.QLabel(self.emailset_str[0],self)
		self.lb5.setStyleSheet("color: magenta")
		grid_0.addWidget(self.lb4,0,0)
		grid_0.addWidget(self.lb5,0,1)
		
		self.btnNewGmail = QtGui.QPushButton("Register account",self)
		self.btnNewGmail.clicked.connect(self.btn_newgmail)
		self.btnNewGmail.setEnabled(False)
		grid_0.addWidget(self.btnNewGmail,1,0)
		
		grid_2 = QtGui.QGridLayout()
		self.le2 = QtGui.QLineEdit("username",self)
		self.le2.setFixedWidth(70)
		self.le2.textChanged.connect(self.on_text_changed2)
		self.le3 = QtGui.QLineEdit("password",self)
		self.le3.setFixedWidth(70)
		self.le3.setEchoMode(QtGui.QLineEdit.Password)
		self.le3.textChanged.connect(self.on_text_changed2)
		grid_2.addWidget(self.le2,0,0)
		grid_2.addWidget(self.le3,0,1)
		grid_0.addLayout(grid_2,1,1)
		
		self.lb1 = QtGui.QLabel("Receiver(s) comma(,) separated:",self)
		self.le1 = QtGui.QLineEdit()
		self.le1.setText(','.join([i for i in self.emailrec_str]))
		self.le1.textChanged.connect(self.on_text_changed)
		grid_0.addWidget(self.lb1,2,0)
		grid_0.addWidget(self.le1,2,1)
		
		self.lb2 = QtGui.QLabel("Send notification when pulsing is done?",self)
		self.cb2 = QtGui.QComboBox(self)
		mylist=["yes","no"]
		self.cb2.addItems(mylist)
		self.cb2.setCurrentIndex(mylist.index(self.emailset_str[1]))
		grid_0.addWidget(self.lb2,3,0)
		grid_0.addWidget(self.cb2,3,1)
		
		self.lb3 = QtGui.QLabel("Send data when pulsing is done?",self)
		self.cb3 = QtGui.QComboBox(self)
		self.cb3.addItems(mylist)
		self.cb3.setCurrentIndex(mylist.index(self.emailset_str[2]))
		grid_0.addWidget(self.lb3,4,0)
		grid_0.addWidget(self.cb3,4,1)
		
		self.btnSave = QtGui.QPushButton("Changes saved",self)
		self.btnSave.clicked.connect(self.btn_accepted)
		self.btnSave.setEnabled(False)
		
		grid_1 = QtGui.QGridLayout()
		grid_1.addWidget(self.btnSave,0,0)
		
		self.cb2.activated[str].connect(self.onActivated2)
		self.cb3.activated[str].connect(self.onActivated3)
		
		v0 = QtGui.QVBoxLayout()
		v0.addLayout(grid_0)
		v0.addLayout(grid_1)
		
		self.setLayout(v0)
		self.setWindowTitle("E-mail settings")
		
	def onActivated2(self, text):
		
		self.emailset_str[1] = str(text)
		self.btnSave.setText("*Save changes*")
		self.btnSave.setEnabled(True)
	
	def onActivated3(self, text):
		
		self.emailset_str[2] = str(text)
		self.btnSave.setText("*Save changes*")
		self.btnSave.setEnabled(True)
	
	def on_text_changed(self):
		
		self.emailrec_str = str(self.le1.text()).split(',')
		self.emailrec_str = [emails.strip() for emails in self.emailrec_str]
		
		for emails in self.emailrec_str:
			if not re.match(r"[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$", emails):
				self.btnSave.setText("*Invalid e-mail(s)*")
				self.btnSave.setEnabled(False)
			else:
				self.btnSave.setText("*Save changes*")
				self.btnSave.setEnabled(True)
	
	def on_text_changed2(self):
		
		if str(self.le2.text())!="username" and len(str(self.le2.text()))>0:
			if str(self.le3.text())!="password" and len(str(self.le3.text()))>0:
				self.btnNewGmail.setText("Register account")
				self.btnNewGmail.setEnabled(True)
			else:
				self.btnNewGmail.setText("*Invalid account*")
				self.btnNewGmail.setEnabled(False)
		else:
			self.btnNewGmail.setText("*Invalid account*")
			self.btnNewGmail.setEnabled(False)
	
	def btn_newgmail(self):
		
		yagmail.register(''.join([str(self.le2.text()),'@gmail.com']),str(self.le3.text()))
		self.btnNewGmail.setText("Account registered")
		self.btnNewGmail.setEnabled(False)
		
		self.emailset_str[0]=str(self.le2.text())
		self.lb5.setText(self.emailset_str[0])
		self.btnSave.setText("*Save changes*")
		self.btnSave.setEnabled(True)
	
	def btn_accepted(self):
		
		self.set_save()
		
		self.btnSave.setText("Changes saved")
		self.btnSave.setEnabled(False)
		
	def set_save(self):
		
		self.emailrec_str = str(self.le1.text()).split(',')
		timestr=time.strftime("%y%m%d-%H%M")
		self.lcd.display(timestr)
		
		self.replace_line("config_COMPexPRO.py",10,''.join(["timetrace=\"",timestr,"\"\n"]))
		self.replace_line("config_COMPexPRO.py",12,''.join(["emailrec=[\"",'\",\"'.join([i for i in self.emailrec_str]),"\"]\n"]))
		self.replace_line("config_COMPexPRO.py",13,''.join(["emailset=[\"",'\",\"'.join([i for i in self.emailset_str]),"\"]"]))
		
		imp.reload(config_COMPexPRO)
	
	
	def replace_line(self,file_name, line_num, text):
		
		lines = open(file_name, 'r').readlines()
		lines[line_num] = text
		out = open(file_name, 'w')
		out.writelines(lines)
		out.close()
		
		
		
		
class Send_email_dialog(QtGui.QDialog):

	def __init__(self, parent=None):
		QtGui.QDialog.__init__(self, parent)
		
		# constants
		self.emailset_str = config_COMPexPRO.emailset
		self.emailrec_str = config_COMPexPRO.emailrec
		self.folder_str = config_COMPexPRO.folder
		self.all_files=["The attached files are some chosen data sent from the PLD computer."]

		self.setupUi()

	def setupUi(self):
		
		self.lb0 = QtGui.QLabel("Receiver(s) comma(,) separated:",self)
		self.le1 = QtGui.QLineEdit()
		self.le1.setText(','.join([i for i in self.emailrec_str]))
		self.le1.textChanged.connect(self.on_text_changed)
		
		self.btnSave = QtGui.QPushButton("Receivers saved",self)
		self.btnSave.clicked.connect(self.btn_save)
		self.btnSave.setEnabled(False)
		
		self.btnSend = QtGui.QPushButton("Send e-mail",self)
		self.btnSend.clicked.connect(self.btn_send_email)
		self.btnSend.setEnabled(False)
		
		self.btnBrowse = QtGui.QPushButton("Pick files",self)
		self.btnBrowse.clicked.connect(self.btn_browse_files)
		
		self.btnClear = QtGui.QPushButton("Clear list",self)
		self.btnClear.clicked.connect(self.btn_clear_list)
		self.btnClear.setEnabled(False)
		
		# set layout
		
		grid_0 = QtGui.QGridLayout()
		grid_0.addWidget(self.lb0,0,0)
		grid_0.addWidget(self.le1,1,0)
		grid_0.addWidget(self.btnSave,2,0)
		
		grid_1 = QtGui.QGridLayout()
		grid_1.addWidget(self.btnSend,0,0)
		grid_1.addWidget(self.btnBrowse,0,1)
		grid_1.addWidget(self.btnClear,0,2)
		
		grid_2 = QtGui.QGridLayout()
		self.lb1 = QtGui.QLabel("No files selected!",self)
		grid_2.addWidget(self.lb1,0,0)
		
		v0 = QtGui.QVBoxLayout()
		v0.addLayout(grid_0)
		v0.addLayout(grid_1)
		v0.addLayout(grid_2)
		
		self.setLayout(v0)
		self.setWindowTitle("E-mail data")
		
		# re-adjust/minimize the size of the e-mail dialog
		# depending on the number of attachments
		v0.setSizeConstraint(v0.SetFixedSize)
		
	def btn_send_email(self):
		
		try:
			self.yag = yagmail.SMTP(self.emailset_str[0])
			self.yag.send(self.emailrec_str, "File(s) sent from a Swanepoel analysis computer", contents=self.all_files)
			QtGui.QMessageBox.warning(self, 'Message', ''.join(["E-mail is sent to ", ' and '.join([i for i in self.emailrec_str]) ," including ",str(len(self.all_files[1:]))," attachment(s)!"]))
		except Exception,e:
			QtGui.QMessageBox.warning(self, 'Message',''.join(["Could not load the gmail account ",self.emailset_str[0],"! Try following steps:\n1. Check internet connection. Only wired internet will work, ie. no wireless.\n2. Check the account username and its password.\n3. Make sure that the account accepts less secure apps."]))
			

	def btn_clear_list(self):
	
		self.all_files=["The attached files are some chosen data sent from the scatteromter computer."]
		self.lb1.setText("No files selected!")

		self.btnSend.setEnabled(False)
		self.btnClear.setEnabled(False)
	
	def btn_browse_files(self):
	
		for path in QtGui.QFileDialog.getOpenFileNames(self, 'Open file',''.join([self.folder_str,'/'])):
			self.all_files.extend([str(path)])
		
		for emails in self.emailrec_str:
			if not re.match(r"[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$", emails):
				self.btnSend.setEnabled(False)
			else:
				if len(self.all_files)==1:
					self.btnSend.setEnabled(False)
				else:
					self.btnSend.setEnabled(True)
					
		if len(self.all_files)==1:
			self.lb1.setText("No files selected!")
			self.btnClear.setEnabled(False)
		else:
			self.print_files = "Selected files:\n"
			self.tal = 0
			for paths in self.all_files[1:]:
				head, tail = os.path.split(paths)
				self.tal +=1
				self.print_files += ''.join([str(self.tal),': ',tail, "\n"])
				
			self.lb1.setText(self.print_files)
			self.btnClear.setEnabled(True)
			
	def on_text_changed(self):
		
		self.emailrec_str = str(self.le1.text()).split(',')
		self.emailrec_str = [emails.strip() for emails in self.emailrec_str]
		
		for emails in self.emailrec_str:
			if not re.match(r"[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$", emails):
				self.btnSend.setEnabled(False)
				self.btnSave.setText("*Invalid e-mail(s)*")
				self.btnSave.setEnabled(False)
			else:
				if len(self.all_files)==1:
					self.btnSend.setEnabled(False)
				else:
					self.btnSend.setEnabled(True)
				self.btnSave.setText("*Save receivers*")
				self.btnSave.setEnabled(True)
				
	def btn_save(self):
		
		self.btnSave.setText("Receivers saved")
		self.btnSave.setEnabled(False)
		
		self.replace_line("config_COMPexPRO.py",12,''.join(["emailrec=[\"",'\",\"'.join([i for i in self.emailrec_str]),"\"]\n"]) )
		imp.reload(config_COMPexPRO)
		
	def replace_line(self,file_name, line_num, text):
		
		lines = open(file_name, 'r').readlines()
		lines[line_num] = text
		out = open(file_name, 'w')
		out.writelines(lines)
		out.close()
		
	def closeEvent(self,event):
	
		event.accept()
			
			
			
			
class Run_COMPexPRO(QtGui.QWidget):

	def __init__(self):
		super(Run_COMPexPRO, self).__init__()
		
		# Initial read of the config file
		self.rate = config_COMPexPRO.rate
		self.hv = config_COMPexPRO.hv
		self.pulse_time = config_COMPexPRO.pulse_time
		self.schroll = config_COMPexPRO.schroll
		
		self.timeout_str = config_COMPexPRO.timeout
		self.warmup_str = config_COMPexPRO.warmup
		self.trigger_str = config_COMPexPRO.trigger
		self.gasmode_str = config_COMPexPRO.gasmode
		
		self.folder_str=config_COMPexPRO.folder
		self.filename_str=config_COMPexPRO.filename
		self.timetrace_str=config_COMPexPRO.timetrace
		self.COMPexPROport_str=config_COMPexPRO.COMPexPROport
		self.emailrec_str = config_COMPexPRO.emailrec
		self.emailset_str = config_COMPexPRO.emailset
		
		# Enable antialiasing for prettier plots		
		pg.setConfigOptions(antialias=True)
		self.initUI()
			
	def initUI(self):
		
		################### MENU BARS START ##################
		
		MyBar = QtGui.QMenuBar(self)
		fileMenu = MyBar.addMenu("File")
		fileSavePlt = fileMenu.addAction("Save plots")
		fileSavePlt.triggered.connect(self.set_save_plots)
		fileSavePlt.setShortcut('Ctrl+P')
		fileSaveSet = fileMenu.addAction("Save settings")        
		fileSaveSet.triggered.connect(self.set_save) # triggers closeEvent()
		fileSaveSet.setShortcut('Ctrl+S')
		self.fileClose = fileMenu.addAction("Close")        
		self.fileClose.triggered.connect(self.close) # triggers closeEvent()
		self.fileClose.setShortcut('Ctrl+X')
		
		modeMenu = MyBar.addMenu("Serial")
		self.conMode = modeMenu.addAction("Connect to serial")
		self.conMode.triggered.connect(self.set_connect)
		self.disconMode = modeMenu.addAction("Disconnect from serial")
		self.disconMode.triggered.connect(self.set_disconnect)
		
		serialMenu = MyBar.addMenu("Ports")
		self.rs232COMPexPRO = serialMenu.addAction("COMPexPRO")
		self.rs232COMPexPRO.triggered.connect(self.COMPexPRODialog)
		
		self.emailMenu = MyBar.addMenu("E-mail")
		self.emailSet = self.emailMenu.addAction("E-mail settings")
		self.emailSet.triggered.connect(self.email_set_dialog)
		self.emailData = self.emailMenu.addAction("E-mail data")
		self.emailData.triggered.connect(self.email_data_dialog)
		
		################### MENU BARS END ##################

		lbl1 = QtGui.QLabel("OPERATION settings:", self)
		lbl1.setStyleSheet("color: blue")	
		
		timeout_lbl = QtGui.QLabel("Timeout", self)
		self.combo0 = QtGui.QComboBox(self)
		mylist0=["ON","OFF"]
		self.combo0.addItems(mylist0)
		self.combo0.setCurrentIndex(mylist0.index(self.timeout_str))
		
		warmup_lbll = QtGui.QLabel("Warm-up", self)
		self.combo1 = QtGui.QComboBox(self)
		mylist1=["ON","OFF"]
		self.combo1.addItems(mylist1)
		self.combo1.setCurrentIndex(mylist1.index(self.warmup_str))
		
		trigger_lbl = QtGui.QLabel("Trigger", self)
		self.combo2 = QtGui.QComboBox(self)
		mylist2=["INT","EXT"]
		self.combo2.addItems(mylist2)
		self.combo2.setCurrentIndex(mylist2.index(self.trigger_str))
		
		gasmode_lbl = QtGui.QLabel("Gasmode", self)
		self.combo3 = QtGui.QComboBox(self)
		mylist3=["PREMIX","SINGLE GASES"]
		self.combo3.addItems(mylist3)
		self.combo3.setCurrentIndex(mylist3.index(self.gasmode_str))
		
		self.hv_lbl = QtGui.QLabel(''.join(["High volt. (",str(self.hv),") [kV]"]), self)
		self.sld_hv = QtGui.QSlider(QtCore.Qt.Horizontal,self)
		#self.sld_hv.setFocusPolicy(QtCore.Qt.NoFocus)
		self.sld_hv.tickPosition()
		self.sld_hv.setRange(190,300)
		self.sld_hv.setSingleStep(1)
		self.sld_hv.setPageStep(5)
		self.sld_hv.setValue(10*self.hv)
		
		self.rate_lbl = QtGui.QLabel(''.join(["Rep. rate (",str(self.rate),") [Hz]"]), self)
		self.sld_rate = QtGui.QSlider(QtCore.Qt.Horizontal,self)
		#self.sld_rate.setFocusPolicy(QtCore.Qt.NoFocus)
		self.sld_rate.tickPosition()
		self.sld_rate.setRange(1,50)
		self.sld_rate.setSingleStep(1)
		self.sld_rate.setPageStep(5)
		self.sld_rate.setValue(self.rate)
		
		#####################################################
		
		self.laser_type = QtGui.QLabel("",self)
		self.laser_type.setStyleSheet("color: magenta")
		laser_type_lbl = QtGui.QLabel(''.join(["Type of laser:"]),self)
		
		self.gas_menu = QtGui.QLabel("",self)
		self.gas_menu.setStyleSheet("color: magenta")
		gas_menu_lbl = QtGui.QLabel(''.join(["Gas menu no:"]),self)
		
		self.gas_wl = QtGui.QLabel("",self)
		self.gas_wl.setStyleSheet("color: magenta")
		gas_wl_lbl = QtGui.QLabel("Gas wavelength:",self)
		
		self.gas_mix = QtGui.QLabel("",self)
		self.gas_mix.setStyleSheet("color: magenta")
		gas_mix_lbl = QtGui.QLabel("Gas mixture:",self)
		
		self.pulse_counter = QtGui.QLabel("",self)
		self.pulse_counter.setStyleSheet("color: magenta")
		pulse_lbl1 = QtGui.QLabel("Counter (10^3):",self)
		
		self.pulse_tot = QtGui.QLabel("",self)
		self.pulse_tot.setStyleSheet("color: magenta")
		pulse_lbl2 = QtGui.QLabel("Total counter (10^3):",self)
		
		warmup_lbl2 = QtGui.QLabel("Warm-up [s]:",self)
		self.warmup = QtGui.QLabel("",self)
		if self.warmup_str=="ON":
			self.warmup.setStyleSheet("color: red")
			self.warmup.setText('480')
		else:
			self.warmup.setStyleSheet("color: green")
			self.warmup.setText('0')
		
		pulse_time_lbl = QtGui.QLabel("Max pulse time [s]",self)
		self.pulsetimeEdit = QtGui.QLineEdit(str(self.pulse_time),self)
		#self.pulsetimeEdit.setFixedWidth(100)
		
		self.resetButton = QtGui.QPushButton("Reset counter",self)
		
		#####################################################
		
		lbl4 = QtGui.QLabel("STORAGE with timetrace and schroll settings:", self)
		lbl4.setStyleSheet("color: blue")
		
		filename = QtGui.QLabel("File name",self)
		foldername = QtGui.QLabel("Folder name",self)
		self.filenameEdit = QtGui.QLineEdit(str(self.filename_str),self)
		self.folderEdit = QtGui.QLineEdit(str(self.folder_str),self)
		#self.filenameEdit.setFixedWidth(140)
		#self.folderEdit.setFixedWidth(100)
		
		#####################################################
		
		schroll_lbl = QtGui.QLabel("Schroll time",self)
		self.combo4 = QtGui.QComboBox(self)
		mylist4=["200","500","1000","2000","5000","10000"]
		self.combo4.addItems(mylist4)
		# initial combo settings
		self.combo4.setCurrentIndex(mylist4.index(str(self.schroll)))
		#self.combo4.setFixedWidth(85)
		
		#####################################################
		
		lbl5 = QtGui.QLabel("EXECUTE operation settings:", self)
		lbl5.setStyleSheet("color: blue")
		
		self.startButton = QtGui.QPushButton("Start source",self)
		self.stopButton = QtGui.QPushButton("",self)
		if self.warmup_str=="ON":
			self.stopButton.setText('SKIP warm-up')
		else:
			self.stopButton.setText('STOP source')
		
		
		#####################################################
		
		self.lcd = QtGui.QLCDNumber(self)
		self.lcd.setStyleSheet("color: red")
		self.lcd.setFixedHeight(50)
		self.lcd.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd.setNumDigits(11)
		self.lcd.display(self.timetrace_str)
			
		#####################################################
		#####################################################
		#####################################################
		
		# Add all widgets		
		g1_0 = QtGui.QGridLayout()
		g1_0.addWidget(MyBar,0,0)
		g1_0.addWidget(lbl1,1,0)

		g1_1 = QtGui.QGridLayout()
		g1_1.addWidget(timeout_lbl,0,0)
		g1_1.addWidget(self.combo0,1,0)
		g1_1.addWidget(warmup_lbll,0,1)
		g1_1.addWidget(self.combo1,1,1)
		g1_1.addWidget(trigger_lbl,0,2)
		g1_1.addWidget(self.combo2,1,2)
		g1_1.addWidget(gasmode_lbl,0,3)
		g1_1.addWidget(self.combo3,1,3)
		
		g1_2 = QtGui.QGridLayout()
		g1_2.addWidget(self.rate_lbl,0,0)
		g1_2.addWidget(self.sld_rate,1,0)
		g1_2.addWidget(self.hv_lbl,0,1)
		g1_2.addWidget(self.sld_hv,1,1)
		
		g1_3 = QtGui.QGridLayout()
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
		
		g1_4 = QtGui.QGridLayout()
		g1_4.addWidget(self.resetButton,0,0)
		g1_4.addWidget(warmup_lbl2,0,1)
		g1_4.addWidget(self.warmup,0,2)
		g1_4.addWidget(pulse_time_lbl,0,3)
		g1_4.addWidget(self.pulsetimeEdit,0,4)
		
		v1 = QtGui.QVBoxLayout()
		v1.addLayout(g1_0)
		v1.addLayout(g1_1)
		v1.addLayout(g1_2)
		v1.addLayout(g1_3)
		v1.addLayout(g1_4)

		#####################################################
		
		g3_0 = QtGui.QGridLayout()
		g3_0.addWidget(lbl4,0,0)
		
		g3_1 = QtGui.QGridLayout()
		g3_1.addWidget(filename,0,0)
		g3_1.addWidget(self.filenameEdit,1,0)
		g3_1.addWidget(foldername,0,1)
		g3_1.addWidget(self.folderEdit,1,1)
		g3_1.addWidget(schroll_lbl,0,2)
		g3_1.addWidget(self.combo4,1,2)
		
		g3_2 = QtGui.QGridLayout()
		g3_2.addWidget(self.lcd,0,0)
		
		v3 = QtGui.QVBoxLayout()
		v3.addLayout(g3_0)
		v3.addLayout(g3_1)
		v3.addLayout(g3_2)
		
		#####################################################
		
		g5_0 = QtGui.QGridLayout()
		g5_0.addWidget(lbl5,0,0)
		
		g5_1 = QtGui.QGridLayout()
		g5_1.addWidget(self.startButton,0,1)
		g5_1.addWidget(self.stopButton,0,2)
		
		v5 = QtGui.QVBoxLayout()
		v5.addLayout(g5_0)
		v5.addLayout(g5_1)
		
		#####################################################
		
		# add ALL groups from v1 to v6 in one vertical group v7
		v7 = QtGui.QVBoxLayout()
		v7.addLayout(v1)
		v7.addLayout(v3)
		v7.addLayout(v5)
	
		#####################################################
		
		# set GRAPHS and TOOLBARS to a new vertical group vcan
		vcan0 = QtGui.QGridLayout()
		self.pw1 = pg.PlotWidget() 
		vcan0.addWidget(self.pw1,0,0)
		
		vcan1 = QtGui.QGridLayout()
		self.pw3 = pg.PlotWidget()
		vcan1.addWidget(self.pw3,0,0)
		
		# SET ALL HORIZONTAL COLUMNS TOGETHER
		hbox = QtGui.QHBoxLayout()
		hbox.addLayout(v7)
		hbox.addLayout(vcan0)
		
		# SET VERTICAL COLUMNS TOGETHER TO FINAL LAYOUT
		vbox = QtGui.QVBoxLayout()
		vbox.addLayout(hbox)
		vbox.addLayout(vcan1)
		
		vcan2 = QtGui.QGridLayout()
		self.pw5 = pg.PlotWidget()
		vcan2.addWidget(self.pw5,0,0)
		self.pw2 = pg.PlotWidget()
		vcan2.addWidget(self.pw2,1,0)
		self.pw6 = pg.PlotWidget()
		vcan2.addWidget(self.pw6,2,0)
		self.pw7 = pg.PlotWidget()
		vcan2.addWidget(self.pw7,3,0)
		
		# SET HORIZONTAL COLUMNS TOGETHER TO FINAL LAYOUT
		hbox1 = QtGui.QHBoxLayout()
		hbox1.addLayout(vbox)
		hbox1.addLayout(vcan2)
		
		self.setLayout(hbox1) 
		
		##############################################
		
		# INITIAL SETTINGS PLOT 1
		
		self.p1_ = self.pw1.plotItem
		self.curve1=self.p1_.plot(pen='r')
		self.pw1.setTitle(''.join(["Energy after BEAM SPLITTER"]))
		self.pw1.setLabel('left', "Energy", units='J', color='red')
		self.pw1.setLabel('bottom', "Elapsed time", units='s', color='red')
		self.pw1.enableAutoRange()
		
		# INITIAL SETTINGS PLOT 2
		p6 = self.pw2.plotItem
		self.curve6=p6.plot(pen='r')
		#self.pw2.setLogMode(None,True)
		self.pw2.setTitle(''.join(["Trigger pulse diff."]))
		self.pw2.setLabel('left', "Pulse diff", units='', color='red')
		self.pw2.setLabel('bottom', "Elapsed time", units='s', color='red')
		self.pw2.enableAutoRange()
		
		# INITIAL SETTINGS PLOT 5
		p8 = self.pw5.plotItem
		self.curve8=p8.plot(pen='m')
		self.pw5.setTitle(''.join(["BUFFER gas press."]))
		self.pw5.setLabel('left', "Press.", units='bar', color='magenta')
		self.pw5.setLabel('bottom', "Elapsed time", units='s', color='magenta')
		self.pw5.enableAutoRange()
		
		# INITIAL SETTINGS PLOT 6
		self.p9 = self.pw6.plotItem
		self.curve9=self.p9.plot(pen='y')
		# create plot and add it to the figure
		self.p9_ = pg.ViewBox()
		self.curve11=pg.PlotCurveItem(pen='r')
		self.p9_.addItem(self.curve11)
		# connect respective axes to the plot 
		self.p9.scene().addItem(self.p9_)
		self.p9.getAxis('right').linkToView(self.p9_)
		self.p9_.setXLink(self.p9)
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw6.setDownsampling(mode='peak')
		self.pw6.setClipToView(True)
		self.pw6.enableAutoRange()
		# Labels and titels are placed here since they change dynamically
		self.pw6.setTitle(''.join(["F2 mix gas"]))
		self.pw6.setLabel('left', "Temp.", units='C', color='yellow')
		self.pw6.setLabel('right', "Press.", units='bar', color='red')
		self.pw6.setLabel('bottom', "Elapsed time", units='s', color='white')
		
		# INITIAL SETTINGS PLOT 7
		p10 = self.pw7.plotItem
		self.curve10=p10.plot(pen='y')
		self.pw7.setTitle(''.join(["Power stabilization (1=YES, 0=NO)"]))
		self.pw7.setLabel('left', "YES or NO", units='', color='yellow')
		self.pw7.setLabel('bottom', "Elapsed time", units='s', color='yellow')
		
		# INITIAL SETTINGS PLOT 3
		self.p1 = self.pw3.plotItem
		self.curve3=self.p1.plot(pen='w')
		self.curve4=self.p1.plot(pen='y')
		# create plot and add it to the figure
		self.p2 = pg.ViewBox()
		self.curve5=pg.PlotCurveItem(pen='r')
		self.p2.addItem(self.curve5)
		# connect respective axes to the plot 
		self.p1.scene().addItem(self.p2)
		self.p1.getAxis('right').linkToView(self.p2)
		self.p2.setXLink(self.p1)
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw3.setDownsampling(mode='peak')
		self.pw3.setClipToView(True)
		self.pw3.enableAutoRange()
		# Labels and titels are placed here since they change dynamically
		self.pw3.setTitle(''.join(["Temp. and press. in the LASER TUBE"]))
		self.pw3.setLabel('left', "Temp.", units='C', color='yellow')
		self.pw3.setLabel('right', "Press.", units='bar', color='red')
		self.pw3.setLabel('bottom', "Elapsed time", units='s', color='white')
		'''
		# INITIAL SETTINGS PLOT 4
		self.pw4 = gl.GLViewWidget()
		self.pw4.opts['distance'] = 0.03
		self.pw4.setWindowTitle('Scatter plot of sweeped poins')
		
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
		#self.pw4.addItem(ax2)
		#ax2.setLabel('latitude', color='#0000ff')
		self.sp1 = gl.GLScatterPlotItem()
		'''
		# Initialize and set titles and axis names for both plots
		
		##############################################
		
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
		self.startButton.clicked.connect(self.set_start)
		
		# cancel the script run
		self.stopButton.clicked.connect(self.set_stop)
		
		self.clear_vars_graphs()
		self.disconMode.setEnabled(False)
		self.allFields(False)
		self.stopButton.setEnabled(False)
		self.startButton.setEnabled(False)
		self.fileClose.setEnabled(True)
		
		self.setGeometry(10, 10, 1100, 800)
		self.move(0,0)
		self.setWindowTitle("COMPexPRO Photon Source Controller")
		self.show()
	
	def update_pulse_lcd(self,i):
		# i and j are always in meters
		self.pulse_counter.setText(str(i))
	
	def update_pulse_lcd2(self,i):
		# i and j are always in meters
		self.pulse_tot.setText(str(i))
		
	def set_reset(self):
		
		self.pulse_counter.setText(str(self.COMPexPRO.set_counter_reset()))
		
	def set_connect(self):
		
		try:
			self.COMPexPRO = COMPexPRO.COMPexPRO(self.COMPexPROport_str)
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message',"No response from the serial! Check the serial port name.")	
			return None
			
		
		try:
			self.COMPexPRO.set_timeout_(1)
			
			menu = self.COMPexPRO.get_menu()
			self.gas_menu.setText(menu[0])
			self.gas_wl.setText(menu[1])
			self.gas_mix.setText(menu[2])
			self.laser_type.setText(self.COMPexPRO.get_lasertype())
			
			print "COMPexPRO "+self.COMPexPRO.get_version()+" ready"
			
			self.pulse_counter.setText(str(self.COMPexPRO.get_counter()))
			self.pulse_tot.setText(str(self.COMPexPRO.get_totalcounter()))
		except Exception, e:
			self.COMPexPRO.close()
			QtGui.QMessageBox.warning(self, 'Message',"No response from the COMPexPRO photon source! Is the photon source powered and connected to serial?")	
			return None
		
		self.allFields(True)
		self.conMode.setEnabled(False)
		self.disconMode.setEnabled(True)
		self.rs232COMPexPRO.setEnabled(False)
			
	def set_disconnect(self):
		
		val_str=self.COMPexPRO.set_trigger('EXT')
		if val_str:
			if val_str=="EXT":
				print "COMPexPRO trigger set to external, "+val_str
		else:
			print "Could not set COMPexPRO trigger to EXT!"
		self.COMPexPRO.close()

		self.allFields(False)
		self.conMode.setEnabled(True)
		self.disconMode.setEnabled(False)
		self.rs232COMPexPRO.setEnabled(True)
	
	def allFields(self,trueorfalse):
		
		self.combo0.setEnabled(trueorfalse)
		self.combo1.setEnabled(trueorfalse)
		self.combo2.setEnabled(trueorfalse)
		self.combo3.setEnabled(trueorfalse)
		self.combo4.setEnabled(trueorfalse)
		
		self.sld_rate.setEnabled(trueorfalse)
		self.sld_hv.setEnabled(trueorfalse)
		
		self.filenameEdit.setEnabled(trueorfalse)
		self.folderEdit.setEnabled(trueorfalse)
		self.pulsetimeEdit.setEnabled(trueorfalse)
		self.resetButton.setEnabled(trueorfalse)
		self.startButton.setEnabled(trueorfalse)
	
	def COMPexPRODialog(self):

		text, ok = QtGui.QInputDialog.getText(self, 'Serial Port Dialog','Enter COMPexPRO port number:', text=self.COMPexPROport_str)
		if ok:
			self.COMPexPROport_str = str(text)
	
	def email_data_dialog(self):
		
		self.Send_email_dialog = Send_email_dialog()
		self.Send_email_dialog.exec_()
	
	def email_set_dialog(self):
		
		self.Email_dialog = Email_dialog(self.lcd)
		self.Email_dialog.exec_()
	
	def reload_email(self):
		
		imp.reload(config_COMPexPRO)	
		self.emailrec_str = config_COMPexPRO.emailrec
		self.emailset_str = config_COMPexPRO.emailset
	
	def changeRate(self, val):
		
		self.rate=val
		self.rate_lbl.setText(''.join(["Rep. rate (",str(val),") [Hz]"]))
		time.sleep(0.05)
		
	def changeHV(self, val):
		
		self.hv=val/10.0
		self.hv_lbl.setText(''.join(["High volt. (",str(val/10.0),") [kV]"]))
		time.sleep(0.05)
	
	def onActivated0(self, text):
		
		self.timeout_str=str(text)
		
		if str(text)=="ON":
			QtGui.QMessageBox.warning(self, 'Message',"Serial disruptions are present in ON mode. It is recommeneded to set timeout in OFF mode.")
		
	def onActivated1(self, text):
		
		self.warmup_str=str(text)
		
		if self.warmup_str=="ON":
			self.stopButton.setText('SKIP warm-up')
			self.warmup.setStyleSheet("color: red")
			self.warmup.setText('480')
		else:
			self.stopButton.setText('STOP source')
			self.warmup.setStyleSheet("color: green")
			self.warmup.setText('0')
	
	def onActivated2(self, text):
		
		self.trigger_str=str(text)
		
		if str(text)=="EXT":
			QtGui.QMessageBox.warning(self, 'Message',"Setting trigger to external mode requires external TTL signal for pulse triggering.")
	
	def onActivated3(self, text):
		
		self.gasmode_str=str(text)
		
	def onActivated4(self, text):
		
		self.schroll=int(text)
		
		
	def set_start(self):
		
		# For SAVING data
		if self.filename_str:
			self.string_filename=''.join([self.filename_str,self.timetrace_str])
		else:
			self.string_filename=''.join(["data_",self.timetrace_str])
			
		if self.folder_str:
			self.saveinfolder=''.join([self.folder_str,"/"])
			if not os.path.isdir(self.folder_str):
				os.mkdir(self.folder_str)
		else:
			self.saveinfolder=""
			
		self.data_file=''.join([self.saveinfolder,self.string_filename,".txt"])	
		
		self.clear_vars_graphs()
		self.allFields(False)
		self.stopButton.setEnabled(True)
		self.fileClose.setEnabled(False)
		self.disconMode.setEnabled(False)
		
		try:
			self.pulse_time = int(self.pulsetimeEdit.text())
			if self.pulse_time<=0:
				QtGui.QMessageBox.warning(self, 'Message',"Max pulse time is a positive non-zero integer!")
				return None
		except Exception,e:
			QtGui.QMessageBox.warning(self, 'Message',"Max pulse time is an integer!")
			return None
			
		self.get_thread=Run_COMPexPRO_Thread(self.rate,self.hv,self.timeout_str,self.warmup_str,self.warmup,self.trigger_str, self.gasmode_str, self.pulse_time,self.data_file,self.timetrace_str,self.COMPexPRO,self.stopButton)

		self.connect(self.get_thread, SIGNAL('update_pulse_lcd(PyQt_PyObject)'), self.update_pulse_lcd)
		self.connect(self.get_thread, SIGNAL('update_pulse_lcd2(PyQt_PyObject)'), self.update_pulse_lcd2)
		self.connect(self.get_thread, SIGNAL('make_update1(PyQt_PyObject,PyQt_PyObject)'), self.make_update1)
		self.connect(self.get_thread, SIGNAL('make_update2(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.make_update2)
		self.connect(self.get_thread, SIGNAL('make_update3(PyQt_PyObject,PyQt_PyObject)'), self.make_update3)
		self.connect(self.get_thread, SIGNAL('make_update4(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.make_update4)
		self.connect(self.get_thread, SIGNAL('make_update5(PyQt_PyObject,PyQt_PyObject)'), self.make_update5)
		self.connect(self.get_thread, SIGNAL('make_update6(PyQt_PyObject,PyQt_PyObject)'), self.make_update6)
		self.connect(self.get_thread, SIGNAL('finished()'), self.set_finished)
		self.get_thread.start()
		

	'''
	def surf_line_plot(self):
		
		if self.scan_mode=='ywise':
			n = len(self.x_fields)
			x = self.x_fields
			y = self.y_fields
			z = self.acc_volt.reshape((len(self.x_fields),len(self.y_fields) ))
			for i in range(n):
				pts = (x,y,z[i,:])
				self.plt1.setData(pos=pts, color=pg.glColor((i,n*1.3)), width=(i+1)/10., antialias=True)
				self.pw4.addItem(self.plt1)
				
		elif self.scan_mode=='xwise':
			n = len(self.y_fields)
			x = self.x_fields
			y = self.y_fields
			z = self.acc_volt.reshape((len(self.x_fields),len(self.y_fields) ))
			for i in range(n):
				pts = (x,y,z[:,i])
				self.plt1.setData(pos=pts, color=pg.glColor((i,n*1.3)), width=(i+1)/10., antialias=True)
				self.pw4.addItem(self.plt1)
	'''

	
	
	
	def make_update1(self,time_elap,energy):
    
		self.all_energy.extend([ energy ])
		if len(self.all_energy)>self.schroll:
			self.plot_time_egy[:-1] = self.plot_time_egy[1:]  # shift data in the array one sample left
			self.plot_time_egy[-1] = time_elap
			self.plot_energy_egy[:-1] = self.plot_energy_egy[1:]  # shift data in the array one sample left
			self.plot_energy_egy[-1] = energy
		else:
			self.plot_time_egy.extend([ time_elap ])
			self.plot_energy_egy.extend([ energy ])

		self.curve1.setData(self.plot_time_egy, self.plot_energy_egy)
	
	

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

		self.get_thread.abort()
		
	def clear_vars_graphs(self):
		
		# PLOT 1 initial canvas settings
		self.all_energy=[]
		self.plot_time_egy=[]
		self.plot_energy_egy=[]
		
		self.curve1.clear()
		
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
		
		

	def set_save(self):
		
		self.timetrace_str=time.strftime("%y%m%d-%H%M")
		self.reload_email()
		
		with open("config_COMPexPRO.py", 'w') as thefile:
			thefile.write( ''.join(["rate=",str(self.rate),"\n"]) )
			thefile.write( ''.join(["hv=",str(self.hv),"\n"]) )
			thefile.write( ''.join(["pulse_time=",str(self.pulsetimeEdit.text()),"\n"]) )
			thefile.write( ''.join(["schroll=",str(self.schroll),"\n"]) )
			
			thefile.write( ''.join(["timeout=\"",self.timeout_str,"\"\n"]) )
			thefile.write( ''.join(["warmup=\"",self.warmup_str,"\"\n"]) )
			thefile.write( ''.join(["trigger=\"",self.trigger_str,"\"\n"]) )
			thefile.write( ''.join(["gasmode=\"",self.gasmode_str,"\"\n"]) )
			
			thefile.write( ''.join(["folder=\"",str(self.folderEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["filename=\"",str(self.filenameEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["timetrace=\"",self.timetrace_str,"\"\n"]) )
			thefile.write( ''.join(["COMPexPROport=\"",self.COMPexPROport_str,"\"\n"]) )
			thefile.write( ''.join(["emailrec=[\"",'\",\"'.join([i for i in self.emailrec_str]),"\"]\n"]) )
			thefile.write( ''.join(["emailset=[\"",'\",\"'.join([i for i in self.emailset_str]),"\"]\n"]) )
			
		self.lcd.display(self.timetrace_str)
	
	def set_finished(self):

		self.allFields(True)
		self.stopButton.setEnabled(False)
		self.conMode.setEnabled(False)
		self.disconMode.setEnabled(True)
		self.rs232COMPexPRO.setEnabled(False)
		
		self.reload_email()
		if self.emailset_str[1] == "yes":
			self.send_notif()
		if self.emailset_str[2] == "yes":
			self.send_data()
	
	def send_notif(self):
		
		try:
			self.yag = yagmail.SMTP(self.emailset_str[0])
			self.yag.send(to=self.emailrec_str, subject="COMPexPRO pulsing is done!", contents="COMPexPRO pulsing is done. Please visit the experiment site and make sure that all light sources are switched off.")
		except Exception,e:
			QtGui.QMessageBox.warning(self, 'Message',''.join(["Could not load the gmail account ",self.emailset_str[0],"! Try following steps:\n1. Check internet connection. Only wired internet will work, ie. no wireless.\n2. Check the account username and its password.\n3. Make sure that the account accepts less secure apps."]))
			
	def send_data(self):
		
		try:
			self.yag = yagmail.SMTP(self.emailset_str[0])
			self.yag.send(to=self.emailrec_str, subject="COMPexPRO data from the latest pulsing!", contents=["COMPexPRO pulsing is done and the logged data is attached to this email. Please visit the experiment site and make sure that all light sources are switched off.", self.data_file ])
		except Exception,e:
			QtGui.QMessageBox.warning(self, 'Message',''.join(["Could not load gmail account ",self.emailset_str[0],"! Try following steps:\n1. Check internet connection. Only wired internet will work, ie. no wireless.\n2. Check the account username and its password.\n3. Make sure that the account accepts less secure apps."]))
			
	def closeEvent(self, event):
		reply = QtGui.QMessageBox.question(self, 'Message', "Quit now? Any changes not saved will stay unsaved!", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes:
			if hasattr(self, 'COMPexPRO'):
				if self.conMode.isEnabled()==False:
					if not hasattr(self, 'get_thread'):
						val_str=self.COMPexPRO.set_trigger('EXT')
						if val_str:
							if val_str=="EXT":
								print "COMPexPRO trigger set to external, "+val_str
						else:
							print "Could not set COMPexPRO trigger to EXT!"
						self.COMPexPRO.close()
						event.accept()
					else:
						if self.get_thread.isRunning():
							QtGui.QMessageBox.warning(self, 'Message', "Pulsing in progress. Stop the photon source then quit!")
							event.ignore()
						else:
							val_str=self.COMPexPRO.set_trigger('EXT')
							if val_str:
								if val_str=="EXT":
									print "COMPexPRO trigger set to external, "+val_str
							else:
								print "Could not set COMPexPRO trigger to EXT!"
							self.COMPexPRO.close()
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
		
		# For SAVING data
		if self.filename_str:
			self.string_filename=''.join([self.filename_str,self.timetrace_str])
		else:
			self.string_filename=''.join(["data_",self.timetrace_str])
			
		if self.folder_str:
			self.saveinfolder=''.join([self.folder_str,"/"])
			if not os.path.isdir(self.folder_str):
				os.mkdir(self.folder_str)
		else:
			self.saveinfolder=""
		
		save_plot1=''.join([self.saveinfolder,self.string_filename,'_BeamEnergy.png'])	
		save_plot2=''.join([self.saveinfolder,self.string_filename,'_LaserTube.png'])	

		# create an exporter instance, as an argument give it
		# the item you wish to export
		exporter = pg.exporters.ImageExporter(self.p1_)
		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_plot1)
		
		exporter = pg.exporters.ImageExporter(self.p1)
		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_plot2)
		
		#plt.savefig(save_plot3)
		
#########################################
#########################################
#########################################

def main():
	
	app = QtGui.QApplication(sys.argv)
	ex = Run_COMPexPRO()
	sys.exit(app.exec_())

if __name__ == '__main__':
	
	main()
