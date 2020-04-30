## Import libraries
import matplotlib.pyplot as plt
import os, sys, re, time, imp, numpy, yagmail
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
		
		try:
			
			if self.sender=='Raw data':
				import get_raw
				my_arg = get_raw.Get_raw()
			
			elif self.sender=='Tmin and Tmax':
				import get_Tmax_Tmin
				my_arg = get_Tmax_Tmin.Get_Tmax_Tmin()
			
			elif self.sender=='Std.Dev. in d':
				import get_vary_igp
				my_arg = get_vary_igp.Vary_igp()

			elif self.sender=='Index n':
				import get_m_d
				my_arg = get_m_d.Gmd()
				
			elif self.sender=='Absorption alpha':
				import alpha
				my_arg = alpha.Alpha()
			
			elif self.sender=='Wavenumber k':
				import k
				my_arg = k.K_class()
				
			self.emit(SIGNAL('pass_plots(PyQt_PyObject,PyQt_PyObject)'), my_arg, self.sender)
			
		except Exception as inst:
			
			if "common_xaxis" in inst.args:
				self.emit(SIGNAL('excpt_common_xaxis()') )
			
			elif "interpol" in inst.args:
				self.emit(SIGNAL('excpt_interpol()') )
				
			elif "squareroot" in inst.args:
				self.emit(SIGNAL('excpt_squareroot()') )
			




class Email_settings(QtGui.QDialog):

	def __init__(self, lcd, parent=None):
		QtGui.QDialog.__init__(self, parent)
		
		# constants
		self.emailrec_str = config_Swanepoel.emailrec
		self.emailset_str = config_Swanepoel.emailset
		
		self.lcd = lcd
		
		self.setupUi()

	def setupUi(self):
		
		grid_0 = QtGui.QGridLayout()
		
		self.lb4 = QtGui.QLabel("Active Gmail account:",self)
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
		self.le2.setFixedWidth(90)
		self.le2.textChanged.connect(self.on_text_changed2)
		self.le3 = QtGui.QLineEdit("password",self)
		self.le3.setFixedWidth(90)
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
		
		self.lb2 = QtGui.QLabel("Alert me when simulation is done?",self)
		self.cb2 = QtGui.QComboBox(self)
		mylist=["yes","no"]
		self.cb2.addItems(mylist)
		self.cb2.setCurrentIndex(mylist.index(self.emailset_str[1]))
		grid_0.addWidget(self.lb2,3,0)
		grid_0.addWidget(self.cb2,3,1)
		
		self.lb3 = QtGui.QLabel("Send data when simulation is done?",self)
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
		
		self.replace_line("config_Swanepoel.py",1,''.join(["emailrec=[\"",'\",\"'.join([i for i in self.emailrec_str]),"\"]\n"]))
		self.replace_line("config_Swanepoel.py",2,''.join(["emailset=[\"",'\",\"'.join([i for i in self.emailset_str]),"\"]"]))
		
		imp.reload(config_Swanepoel)
	
	
	def replace_line(self,file_name, line_num, text):
		
		lines = open(file_name, 'r').readlines()
		lines[line_num] = text
		out = open(file_name, 'w')
		out.writelines(lines)
		out.close()
		




class Send_email(QtGui.QDialog):

	def __init__(self, folder_str, parent=None):
		QtGui.QDialog.__init__(self, parent)
		
		# constants
		
		self.emailrec_str = config_Swanepoel.emailrec
		self.emailset_str = config_Swanepoel.emailset
		self.folder_str = folder_str
		
		self.all_files=["The attached files are some chosen data sent from a Swanepoel analysis computer."]

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
		
	def onActivated2(self, text):
		
		self.emailset_str[0] = str(text)

	def onActivated3(self, text):
		
		self.emailset_str[1] = str(text)
		
	def btn_send_email(self):
		
		try:
			self.yag = yagmail.SMTP(self.emailset_str[0])
			self.yag.send(self.emailrec_str, "File(s) sent from a Swanepoel analysis computer", contents=self.all_files)
			QtGui.QMessageBox.warning(self, 'Message', ''.join(["E-mail is sent to ", ' and '.join([i for i in self.emailrec_str]) ," including ",str(len(self.all_files[1:]))," attachment(s)!"]))
		except Exception,e:
			QtGui.QMessageBox.warning(self, 'Message',''.join(["Could not load Gmail account ",self.emailset_str[0],"! Try following steps:\n1. Check internet connection. Only wired internet will work, ie. no wireless.\n2. Check the account username and its password.\n3. Make sure that the account accepts less secure apps."]))
			

	def btn_clear_list(self):
	
		self.all_files=["The attached files are some chosen data sent from a Swanepoel analysis computer."]
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
		
		self.replace_line("config_Swanepoel.py",1,''.join(["emailrec=[\"",'\",\"'.join([i for i in self.emailrec_str]),"\"]\n"]) )
		imp.reload(config_Swanepoel)
		
	def replace_line(self,file_name, line_num, text):
		
		lines = open(file_name, 'r').readlines()
		lines[line_num] = text
		out = open(file_name, 'w')
		out.writelines(lines)
		out.close()
		
	def closeEvent(self,event):
	
		event.accept()








class Run_gui(QtGui.QWidget):

	def __init__(self):
		super(Run_gui, self).__init__()
		
		self.initUI()
			
	def initUI(self):
		
    ################### MENU BARS START ##################
		MyBar = QtGui.QMenuBar(self)

		fileMenu = MyBar.addMenu("File")

		self.fileSave = fileMenu.addAction("Save config file")        
		self.fileSave.triggered.connect(self.set_save_config) 
		self.fileSave.setShortcut('Ctrl+S')

		self.fileSaveAs = fileMenu.addAction("Save config file as")        
		self.fileSaveAs.triggered.connect(self.saveConfigAs) 

		fileLoad = fileMenu.addAction("Load config from file")        
		fileLoad.triggered.connect(self.loadConfig) 
		fileLoad.setShortcut('Ctrl+O') 

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
		self.emailSettings.triggered.connect(self.email_settings_dialog)
		self.emailData = self.emailMenu.addAction("E-mail data")
		self.emailData.triggered.connect(self.email_data_dialog)

		helpMenu = MyBar.addMenu("Help")
		helpParam = helpMenu.addAction("Instructions")
		helpParam.triggered.connect(self.helpParamDialog)
		contact = helpMenu.addAction("Contact")
		contact.triggered.connect(self.contactDialog)

		################### MENU BARS END ##################

		# status info which button has been pressed
		Start_lbl = QtGui.QLabel("ANALYSIS steps and plots", self)
		Start_lbl.setStyleSheet("color: blue")

		self.Step0_Button = QtGui.QPushButton("Raw data",self)
		self.Step0_Button.setToolTip("STEP 0. Plot raw data for OLIS and FTIR")
		self.button_style(self.Step0_Button,'black')

		self.Step1_Button = QtGui.QPushButton("Tmin and Tmax",self)
		self.Step1_Button.setToolTip("STEP 1. Find all the minima and maxima positions using Gaussian filter")
		self.button_style(self.Step1_Button,'black')

		self.Step2_Button = QtGui.QPushButton("Std.Dev. in d",self)
		self.Step2_Button.setToolTip("STEP 2. Minimize standard deviation in the film thickness d")
		self.button_style(self.Step2_Button,'black')

		self.Step3_Button = QtGui.QPushButton("Index n",self)
		self.Step3_Button.setToolTip("STEP 3. Plot refractive indicies n1 and n2")
		self.button_style(self.Step3_Button,'black')

		self.Step4_Button = QtGui.QPushButton("Absorption alpha",self)
		self.Step4_Button.setToolTip("STEP 4. Plot abosorption alpha based on n2")
		self.button_style(self.Step4_Button,'black')

		self.Step5_Button = QtGui.QPushButton("Wavenumber k",self)
		self.Step5_Button.setToolTip("STEP 5. Plot wavenumber k based on n2")
		self.button_style(self.Step5_Button,'black')

		####################################################

		# status info which button has been pressed
		self.NewFiles = QtGui.QLabel('No files created yet!', self)
		self.NewFiles.setStyleSheet("color: magenta")
		'''
		self.NewFiles = numpy.zeros(5,dtype=object)
		for i in range(4):
			self.NewFiles[i] = QtGui.QLabel(''.join([str(i+1),': ']), self)
			self.NewFiles[i].setStyleSheet("color: magenta")
		'''
			
		####################################################
		loads_lbl = QtGui.QLabel("RAW data files", self)
		loads_lbl.setStyleSheet("color: blue")

		configFile_lbl = QtGui.QLabel("Current config file", self)
		self.config_file_lbl = QtGui.QLabel("", self)
		self.config_file_lbl.setStyleSheet("color: green")

		loadSubOlis_lbl = QtGui.QLabel("OLIS sub", self)
		self.loadSubOlisFile_lbl = QtGui.QLabel("", self)
		self.loadSubOlisFile_lbl.setStyleSheet("color: magenta")
			
		loadSubFilmOlis_lbl = QtGui.QLabel("OLIS sub + thin film", self)
		self.loadSubFilmOlisFile_lbl = QtGui.QLabel("", self)
		self.loadSubFilmOlisFile_lbl.setStyleSheet("color: magenta")

		loadSubFTIR_lbl = QtGui.QLabel("FTIR sub", self)
		self.loadSubFTIRFile_lbl = QtGui.QLabel("", self)
		self.loadSubFTIRFile_lbl.setStyleSheet("color: magenta")

		loadSubFilmFTIR_lbl = QtGui.QLabel("FTIR sub + thin film", self)
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

		plot_X_lbl = QtGui.QLabel("Plot X axis in", self)
		self.combo2 = QtGui.QComboBox(self)
		self.mylist2=["eV","nm"]
		self.combo2.addItems(self.mylist2)
		self.combo2.setFixedWidth(70)

		####################################################

		lbl1 = QtGui.QLabel("GAUSSIAN filter settings", self)
		lbl1.setStyleSheet("color: blue")

		interpol_lbl = QtGui.QLabel("Interpolation method", self)
		self.combo4 = QtGui.QComboBox(self)
		self.mylist4=["spline","linear"]
		self.combo4.setToolTip("Interpolation method for local minima Tmin and local maxima Tmax can only be linear or spline.")
		self.combo4.addItems(self.mylist4)
		self.combo4.setFixedWidth(70)

		factors_lbl = QtGui.QLabel("Gaussian factors", self)
		self.factorsEdit = QtGui.QLineEdit("",self)
		self.factorsEdit.setToolTip("HIGH gaussian factor = broadband noise filtering.\nLOW gaussian factor = narrowband noise filtering.\nHigh gauissian factors (>2) will result in relatively large deviation from the raw data.\nGauissian factors of zero or near zero (<0.5) will closely follow trend of the raw data.")
		self.factorsEdit.setFixedWidth(200)

		borders_lbl = QtGui.QLabel("Gaussian borders [eV]", self)
		self.bordersEdit = QtGui.QLineEdit("",self)
		self.bordersEdit.setToolTip("Gaussian borders should be typed in ascending order and the number of\nborders is always one more compared with the number of Gaussian factors.")
		self.bordersEdit.setFixedWidth(200)

		##############################################

		lbl2 = QtGui.QLabel("ABSORPTION alpha and n1 and n2", self)
		lbl2.setStyleSheet("color: blue")	

		poly_lbl = QtGui.QLabel("Polyfit order", self)
		self.combo1 = QtGui.QComboBox(self)
		self.mylist1=["1","2","3","4","5"]
		self.combo1.addItems(self.mylist1)
		self.combo1.setFixedWidth(70)

		polybord_lbl = QtGui.QLabel("Polyfit range(s) [eV]", self)
		self.poly_bordersEdit = QtGui.QLineEdit("",self)
		self.poly_bordersEdit.setFixedWidth(140)

		self.cb_polybord = QtGui.QCheckBox('',self)
		self.cb_polybord.toggle()

		ignore_data_lbl = QtGui.QLabel("No. of ignored points", self)
		self.ignore_data_ptsEdit = QtGui.QLineEdit("",self)
		self.ignore_data_ptsEdit.setFixedWidth(140)

		corr_slit_lbl = QtGui.QLabel("Correction slit width [nm]", self)
		self.corr_slitEdit = QtGui.QLineEdit("",self)
		self.corr_slitEdit.setToolTip("Finite spectrometer bandwidth (slit width) in the transmission spectrum.")
		self.corr_slitEdit.setFixedWidth(140)

		##############################################

		lbl4 = QtGui.QLabel("STORAGE location (file, folder)", self)
		lbl4.setStyleSheet("color: blue")
		self.filenameEdit = QtGui.QLineEdit("",self)
		self.folderEdit = QtGui.QLineEdit("",self)
		self.filenameEdit.setFixedWidth(180)
		self.folderEdit.setFixedWidth(180)

		self.cb_save_figs = QtGui.QCheckBox('Save figs',self)
		self.cb_save_figs.toggle()

		##############################################

		self.lcd = QtGui.QLCDNumber(self)
		self.lcd.setStyleSheet("color: red")
		self.lcd.setFixedHeight(60)
		self.lcd.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd.setToolTip("Timetrace for saving files")
		self.lcd.setNumDigits(11)
			
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
		g1_1.addWidget(plot_X_lbl,6,0)
		g1_1.addWidget(self.combo2,6,1)

		g1_2 = QtGui.QGridLayout()
		g1_2.addWidget(lbl1,0,0)
		g1_3 = QtGui.QGridLayout()
		g1_3.addWidget(interpol_lbl,0,0)
		g1_3.addWidget(self.combo4,0,1)
		g1_3.addWidget(factors_lbl,1,0)
		g1_3.addWidget(self.factorsEdit,1,1)
		g1_3.addWidget(borders_lbl,2,0)
		g1_3.addWidget(self.bordersEdit,2,1)

		g1_4 = QtGui.QGridLayout()
		g1_4.addWidget(lbl2,0,0)
		g1_5 = QtGui.QGridLayout()
		g1_5.addWidget(poly_lbl,0,0)
		g1_5.addWidget(self.combo1,0,1)
		g1_5.addWidget(polybord_lbl,1,0)
		g1_5.addWidget(self.poly_bordersEdit,1,1)
		g1_5.addWidget(self.cb_polybord,1,2)
		g1_5.addWidget(ignore_data_lbl,2,0)
		g1_5.addWidget(self.ignore_data_ptsEdit,2,1)
		g1_5.addWidget(corr_slit_lbl,3,0)
		g1_5.addWidget(self.corr_slitEdit,3,1)

		g4_0 = QtGui.QGridLayout()
		g4_0.addWidget(lbl4,0,0)
		g4_0.addWidget(self.cb_save_figs,0,1)
		g4_1 = QtGui.QGridLayout()
		g4_1.addWidget(self.filenameEdit,0,0)
		g4_1.addWidget(self.folderEdit,0,1)

		v1 = QtGui.QVBoxLayout()
		v1.addLayout(g1_0)
		v1.addLayout(g1_1)
		v1.addLayout(g1_2)
		v1.addLayout(g1_3)
		v1.addLayout(g1_4)
		v1.addLayout(g1_5)
		v1.addLayout(g4_0)
		v1.addLayout(g4_1)

		###################################################

		g1_6 = QtGui.QGridLayout()
		g1_6.addWidget(Start_lbl,0,0)
		g1_7 = QtGui.QGridLayout()
		g1_7.addWidget(self.Step0_Button,0,0)
		g1_7.addWidget(self.Step1_Button,1,0)
		g1_7.addWidget(self.Step2_Button,2,0)
		g1_7.addWidget(self.Step3_Button,3,0)
		g1_7.addWidget(self.Step4_Button,4,0)
		g1_7.addWidget(self.Step5_Button,5,0)

		g1_8 = QtGui.QGridLayout()
		g1_8.addWidget(self.NewFiles,0,0)
		g1_8.addWidget(self.lcd,1,0)


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

		self.move(0,0)
		#self.setGeometry(50, 50, 800, 500)
		hbox.setSizeConstraint(hbox.SetFixedSize)
		self.setWindowTitle("Swanepoel - thickness and optical constants for thin films")
		self.show()

		try:
			# Initial read of the config file
			self.config_file = config_Swanepoel.current_config_file
			
		except Exception,e:
			QtGui.QMessageBox.critical(self, 'Message', "Could not load file path from the Swanepoel config file!")
		
		
		try:
			head, tail = os.path.split(self.config_file)
			self.cf = imp.load_source(tail[:-3],self.config_file)
			
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
			self.gaussian_factors=self.cf.gaussian_factors
			self.gaussian_borders=self.cf.gaussian_borders

			self.fit_poly_order=self.cf.fit_poly_order
			self.ignore_data_pts=self.cf.ignore_data_pts
			self.corr_slit=self.cf.corr_slit

			self.fit_poly_ranges=self.cf.fit_poly_ranges[0]
			self.fit_poly_ranges_check=self.cf.fit_poly_ranges[1]

			self.filename_str=self.cf.filename
			self.folder_str=self.cf.folder
			self.timestr=self.cf.timestr
			self.save_figs=self.cf.save_figs
			self.plot_X=self.cf.plot_X
			
			self.set_field_vals()

		except Exception,e:
			QtGui.QMessageBox.critical(self, 'Message', "Could not load all parameters from the selected config file! Pick another config file.")
			self.allButtons_torf(False,'allfalse')
			
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
		
		self.factorsEdit.setText(', '.join([str(i) for i in self.gaussian_factors] ))
		self.bordersEdit.setText(', '.join([str(i) for i in self.gaussian_borders] ))
		
		##############################################
		
		self.combo1.setCurrentIndex(self.mylist1.index(str(self.fit_poly_order)))
		self.combo2.setCurrentIndex(self.mylist2.index(str(self.plot_X)))
		self.combo4.setCurrentIndex(self.mylist4.index(self.fit_linear_spline))
		
		##############################################
		
		self.poly_bordersEdit.setText(', '.join([str(i) for i in self.fit_poly_ranges] ))
		self.ignore_data_ptsEdit.setText(str(self.ignore_data_pts))
		self.corr_slitEdit.setText(str(self.corr_slit))
		
		##############################################
		
		self.filenameEdit.setText(str(self.filename_str))
		self.folderEdit.setText(str(self.folder_str))
		self.NewFiles.setToolTip(''.join(["Display newly created and saved files in /",self.folder_str,"/"]))
		self.lcd.display(self.timestr)
		
	def button_style(self,button,color):
		
		button.setStyleSheet(''.join(['QPushButton {background-color: lightblue; font-size: 18pt; color: ',color,'}']))
		button.setFixedWidth(230)
		button.setFixedHeight(60)		
	
	def loadConfig(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Load Config File Dialog', self.config_file)
		
		if fname:
			self.config_file = str(fname)
			
			head, tail = os.path.split(self.config_file)
			self.cf = imp.load_source(tail[:-3], self.config_file)
			
			self.set_load_config()
			
	def saveConfigAs(self):
		
		fname = QtGui.QFileDialog.getSaveFileName(self, 'Save Config File Dialog',self.config_file)
		
		if fname:
			self.set_save_config_as(str(fname))
	
	
	
	def loadSubOlisDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file',self.loadSubOlis_str)
		
		if fname:
			self.loadSubOlis_str = str(fname)
			head, tail = os.path.split(str(fname))
			self.loadSubOlisFile_lbl.setText(tail)
			self.cb_sub_olis.setEnabled(True)
			
	def loadSubFilmOlisDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file',self.loadSubFilmOlis_str)
		
		if fname:
			self.loadSubFilmOlis_str = str(fname)
			head, tail = os.path.split(str(fname))
			self.loadSubFilmOlisFile_lbl.setText(tail)
			self.cb_subfilm_olis.setEnabled(True)
			
	def loadSubFTIRDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file',self.loadSubFTIR_str)
		
		if fname:
			self.loadSubFTIR_str = str(fname)
			head, tail = os.path.split(str(fname))
			self.loadSubFTIRFile_lbl.setText(tail)
			self.cb_sub_ftir.setEnabled(True)
			
	def loadSubFilmFTIRDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file',self.loadSubFilmFTIR_str)
		
		if fname:
			self.loadSubFilmFTIR_str = str(fname)
			head, tail = os.path.split(str(fname))
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
		
	def email_data_dialog(self):
		
		self.Send_email = Send_email(self.folder_str)
		self.Send_email.exec_()

	def email_settings_dialog(self):
		
		Email_set = Email_settings(self.lcd)
		Email_set.exec_()
		
	def helpParamDialog(self):
		
		helpfile=''
		with open('config_Swanepoel_forklaringer.py','r') as f:
		  for line in f:
		    helpfile = helpfile+line
		
		msg = QtGui.QMessageBox()
		msg.setIcon(QtGui.QMessageBox.Information)
		msg.setText("Apply Swanepoel analysis using following steps:")
		msg.setInformativeText(helpfile)
		msg.setWindowTitle("Help")
		#msg.setDetailedText(helpfile)
		msg.setStandardButtons(QtGui.QMessageBox.Ok)
		#msg.setGeometry(1000, 0, 1000+250, 350)

		msg.exec_()	
	
	def contactDialog(self):

		QtGui.QMessageBox.information(self, "Contact information","Suggestions, comments or bugs can be reported to vedran.furtula@ntnu.no")
		
	
	def onActivated1(self, text):
		
		self.fit_poly_order = int(text)
		
	def onActivated2(self, text):
		
		self.plot_X = str(text)
	
	def onActivated4(self, text):
		
		self.fit_linear_spline=str(text)
		
	def save_figs_check(self, state):
		  
		if state in [QtCore.Qt.Checked,True]:
			self.save_figs=True
		else:
			self.save_figs=False

	def sub_olis_check(self, state):
		  
		if state in [QtCore.Qt.Checked,True]:
			self.loadSubOlis_check=True
			self.loadSubOlisFile_lbl.setStyleSheet("color: magenta")
			self.cb_sub_olis.setText('incl')
		else:
			self.loadSubOlis_check=False
			self.loadSubOlisFile_lbl.setStyleSheet("color: grey")
			self.cb_sub_olis.setText('exc')
			
	def subfilm_olis_check(self, state):
		
		if state in [QtCore.Qt.Checked,True]:
			self.loadSubFilmOlis_check=True
			self.loadSubFilmOlisFile_lbl.setStyleSheet("color: magenta")
			self.cb_subfilm_olis.setText('incl')
		else:
			self.loadSubFilmOlis_check=False
			self.loadSubFilmOlisFile_lbl.setStyleSheet("color: grey")
			self.cb_subfilm_olis.setText('exc')
			
	def sub_ftir_check(self, state):

		if state in [QtCore.Qt.Checked,True]:
			self.loadSubFTIR_check=True
			self.loadSubFTIRFile_lbl.setStyleSheet("color: magenta")
			self.cb_sub_ftir.setText('incl')
		else:
			self.loadSubFTIR_check=False
			self.loadSubFTIRFile_lbl.setStyleSheet("color: grey")
			self.cb_sub_ftir.setText('exc')
			
	def subfilm_ftir_check(self, state):

		if state in [QtCore.Qt.Checked,True]:
			self.loadSubFilmFTIR_check=True
			self.loadSubFilmFTIRFile_lbl.setStyleSheet("color: magenta")
			self.cb_subfilm_ftir.setText('incl')
		else:
			self.loadSubFilmFTIR_check=False
			self.loadSubFilmFTIRFile_lbl.setStyleSheet("color: grey")
			self.cb_subfilm_ftir.setText('exc')
	
	def polybord_check(self, state):

		if state in [QtCore.Qt.Checked,True]:
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
	
	
	
	def set_run(self):
		
		sender = self.sender()
		
		## gaussian_borders and gaussian_factors warnings and errors
		gaus_bord=str(self.bordersEdit.text()).split(',')
		for tal in gaus_bord:
			if not self.is_number(tal):
				QtGui.QMessageBox.critical(self, 'Message', "Gaussian borders must be real numbers!")
				return None
			elif float(tal)<0.0:
				QtGui.QMessageBox.critical(self, 'Message', "Gaussian borders must be positive or zero!")
				return None

		if len(gaus_bord) < 2:
			QtGui.QMessageBox.critical(self, 'Message', "You must enter at least 2 gaussian borders!")
			return None
		
		if not numpy.array_equal([numpy.float(i) for i in gaus_bord],numpy.sort([numpy.float(i) for i in gaus_bord])):
			QtGui.QMessageBox.critical(self, 'Message', "The gaussian borders must be entered in the ascending order!")
			return None

		gaus_fact=str(self.factorsEdit.text()).split(',')
		for tal in gaus_fact:
			if not self.is_number(tal):
				QtGui.QMessageBox.critical(self, 'Message', "Gaussian factors must be real numbers!")
				return None
			elif float(tal)<0.0:
				QtGui.QMessageBox.critical(self, 'Message', "Gaussian factors must be positive or zero!")
				return None
		
		if len(gaus_fact) < 1:
			QtGui.QMessageBox.critical(self, 'Message', "You must enter at least 1 gaussian factor!")
			return None
				
		if len(gaus_bord) != len(gaus_fact)+1:
			QtGui.QMessageBox.critical(self, 'Message', "The number of gaussian factors is exactly one less than the number of gaussian borders!")
			return None


		## ignored data points warnings and errors
		ign_pts=str(self.ignore_data_ptsEdit.text())
		if not self.is_int(ign_pts):
			QtGui.QMessageBox.critical(self, 'Message', "The number of ignored points is an integer!")
			return None
		elif int(ign_pts)<0:
			QtGui.QMessageBox.critical(self, 'Message', "The number of ignored points is a positive integer!")
			return None
		
		
		## correction slit width warnings and errors
		corr_pts=str(self.corr_slitEdit.text())
		if not self.is_number(corr_pts):
			QtGui.QMessageBox.critical(self, 'Message', "The correction slit width is a real number!")
			return None
		elif float(corr_pts)<0:
			QtGui.QMessageBox.critical(self, 'Message', "The correction slit width is a positive number!")
			return None


		## fit_poly_ranges warnings and errors
		if self.fit_poly_ranges_check==True:
			polyfit_bord=str(self.poly_bordersEdit.text()).split(',')
			for tal in polyfit_bord:
				if not self.is_number(tal):
					QtGui.QMessageBox.critical(self, 'Message', "The polyfit range enteries must be real numbers!")
					return None
				elif float(tal)<0.0:
					QtGui.QMessageBox.critical(self, 'Message', "The polyfit range enteries must be positive or zero!")
					return None
				
			if len(polyfit_bord)<2 or len(polyfit_bord)%2!=0:
				QtGui.QMessageBox.critical(self, 'Message', "The polyfit range list accepts minimum 2 or even number of enteries!")
				return None

			if not numpy.array_equal([numpy.float(i) for i in polyfit_bord],numpy.sort([numpy.float(i) for i in polyfit_bord])):
				QtGui.QMessageBox.critical(self, 'Message', "The polyfit range list must be entered in ascending order!")
				return None
		
		
		# When all user defined enteries are approved save the data
		self.set_save_config()
		
		
		if sender.text()=='Raw data':
			
			if not self.loadSubOlis_check and not self.loadSubFilmOlis_check and not self.loadSubFTIR_check and not self.loadSubFilmFTIR_check:
				QtGui.QMessageBox.critical(self, 'Message', "No raw data files selected!")
				return None
			

		if sender.text()!='Raw data':
			
			## raw data files warnings and errors
			if not self.loadSubOlis_check and not self.loadSubFilmOlis_check:
				pass
			elif self.loadSubOlis_check and self.loadSubFilmOlis_check:
				pass
			else:
				QtGui.QMessageBox.critical(self, 'Message', "Select both OLIS data files subfilmRAW and subRAW!")
				return None
			
			if not self.loadSubFTIR_check and not self.loadSubFilmFTIR_check:
				pass
			elif self.loadSubFTIR_check and self.loadSubFilmFTIR_check:
				pass
			else:
				QtGui.QMessageBox.critical(self, 'Message', "Select both FTIR data files subfilmRAW and subRAW!")
				return None
			
			if not self.loadSubOlis_check and not self.loadSubFilmOlis_check and not self.loadSubFTIR_check and not self.loadSubFilmFTIR_check:
				QtGui.QMessageBox.critical(self, 'Message', "No data files selected!")
				return None

		if sender.text()=='Raw data':
			
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
		
		self.get_my_Thread=my_Thread(sender.text())
		self.connect(self.get_my_Thread,SIGNAL("pass_plots(PyQt_PyObject,PyQt_PyObject)"),self.pass_plots)
		self.connect(self.get_my_Thread,SIGNAL("excpt_common_xaxis()"),self.excpt_common_xaxis)
		self.connect(self.get_my_Thread,SIGNAL("excpt_interpol()"),self.excpt_interpol)
		self.connect(self.get_my_Thread,SIGNAL("excpt_squareroot()"),self.excpt_squareroot)
	
		self.connect(self.get_my_Thread,SIGNAL('finished()'),self.set_finished)

		self.get_my_Thread.start()

	def excpt_common_xaxis(self):
		
		QtGui.QMessageBox.critical(self, 'Message', "Tmin and Tmax curves have x values in different ranges, ie. no overlap is found. Inspect the raw data and adjust the gaussian borders and the gaussian factors!")
	
	def excpt_interpol(self):
		
		QtGui.QMessageBox.critical(self, 'Message', "Could not interpolate x_data for T_sub. Probably the x_data in Tr covers wider range than the x_data in T_sub.")
	
	def excpt_squareroot(self):
		
		QtGui.QMessageBox.critical(self, 'Message', "Can not take squareroot of negative numbers! The calculated refractive index n might not be physical.")
	
	def pass_plots(self,my_obj,sender):
		
		my_str=''
		try:
			data_names=my_obj.make_plots()
			for i,ii in zip(data_names,range(len(data_names))):
				head, tail = os.path.split(i)
				my_str+=''.join([str(ii+1),': ',tail,'\n'])

			self.NewFiles.setText(my_str)
			my_obj.show_plots()
			
		except Exception as inst:
			if "common_xaxis" in inst.args:
				self.excpt_common_xaxis()

			elif "interpol" in inst.args:
				self.excpt_interpol()
				
			elif "squareroot" in inst.args:
				self.excpt_squareroot()
		
				
	def set_save_config(self):
		
		self.timestr=time.strftime("%y%m%d-%H%M")
		self.lcd.display(self.timestr)
		
		with open(self.config_file, 'w') as thefile:
			# film+substrate measurements
			thefile.write( ''.join(["loadSubOlis=[\"",self.loadSubOlis_str,"\",", str(self.loadSubOlis_check),"]\n"]))
			thefile.write( ''.join(["loadSubFilmOlis=[\"",self.loadSubFilmOlis_str,"\",", str(self.loadSubFilmOlis_check),"]\n"]))
			thefile.write( ''.join(["loadSubFTIR=[\"",self.loadSubFTIR_str,"\",", str(self.loadSubFTIR_check),"]\n"]))
			thefile.write( ''.join(["loadSubFilmFTIR=[\"",self.loadSubFilmFTIR_str,"\",", str(self.loadSubFilmFTIR_check),"]\n"]))
			
			thefile.write( ''.join(["fit_linear_spline=\"",self.fit_linear_spline,"\"\n"]))
			thefile.write( ''.join(["gaussian_factors=[",str(self.factorsEdit.text()),"]\n"]))
			thefile.write( ''.join(["gaussian_borders=[",str(self.bordersEdit.text()),"]\n"]))
			thefile.write( ''.join(["ignore_data_pts=",str(self.ignore_data_ptsEdit.text()),"\n"]))
			thefile.write( ''.join(["corr_slit=",str(self.corr_slitEdit.text()),"\n"]))
			thefile.write( ''.join(["fit_poly_order=",str(self.fit_poly_order),"\n"]))
			thefile.write( ''.join(["fit_poly_ranges=[[",str(self.poly_bordersEdit.text()),"],",str(self.fit_poly_ranges_check),"]\n"]))

			thefile.write( ''.join(["filename=\"",str(self.filenameEdit.text()),"\"\n"]))
			thefile.write( ''.join(["folder=\"",str(self.folderEdit.text()),"\"\n"]))
			thefile.write( ''.join(["timestr=\"",self.timestr,"\"\n"]))	
			thefile.write( ''.join(["save_figs=",str(self.save_figs),"\n"]))
			thefile.write( ''.join(["plot_X=\"",self.plot_X,"\""]))
		
		head, tail = os.path.split(self.config_file)
		self.cf=imp.load_source(tail[:-3], self.config_file)
		self.set_load_config()
		
	def set_save_config_as(self,config_file):
		
		with open(config_file, 'w') as thefile:
			# film+substrate measurements
			thefile.write( ''.join(["loadSubOlis=[\"",self.loadSubOlis_str,"\",", str(self.loadSubOlis_check),"]\n"]))
			thefile.write( ''.join(["loadSubFilmOlis=[\"",self.loadSubFilmOlis_str,"\",", str(self.loadSubFilmOlis_check),"]\n"]))
			thefile.write( ''.join(["loadSubFTIR=[\"",self.loadSubFTIR_str,"\",", str(self.loadSubFTIR_check),"]\n"]))
			thefile.write( ''.join(["loadSubFilmFTIR=[\"",self.loadSubFilmFTIR_str,"\",", str(self.loadSubFilmFTIR_check),"]\n"]))
			
			thefile.write( ''.join(["fit_linear_spline=\"",self.fit_linear_spline,"\"\n"]))
			thefile.write( ''.join(["gaussian_factors=[",str(self.factorsEdit.text()),"]\n"]))
			thefile.write( ''.join(["gaussian_borders=[",str(self.bordersEdit.text()),"]\n"]))
			thefile.write( ''.join(["ignore_data_pts=",str(self.ignore_data_ptsEdit.text()),"\n"]))
			thefile.write( ''.join(["corr_slit=",str(self.corr_slitEdit.text()),"\n"]))
			thefile.write( ''.join(["fit_poly_order=",str(self.fit_poly_order),"\n"]))
			thefile.write( ''.join(["fit_poly_ranges=[[",str(self.poly_bordersEdit.text()),"],",str(self.fit_poly_ranges_check),"]\n"]))

			thefile.write( ''.join(["filename=\"",str(self.filenameEdit.text()),"\"\n"]))
			thefile.write( ''.join(["folder=\"",str(self.folderEdit.text()),"\"\n"]))
			thefile.write( ''.join(["timestr=\"",self.timestr,"\"\n"]))	
			thefile.write( ''.join(["save_figs=",str(self.save_figs),"\n"]))
			thefile.write( ''.join(["plot_X=\"",self.plot_X,"\""]))
			
			
	def set_load_config(self):
		
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
		
		self.fit_poly_order=self.cf.fit_poly_order
		self.ignore_data_pts=self.cf.ignore_data_pts
		self.corr_slit=self.cf.corr_slit
		
		self.fit_poly_ranges=self.cf.fit_poly_ranges[0]
		self.fit_poly_ranges_check=self.cf.fit_poly_ranges[1]
		
		self.filename_str=self.cf.filename
		self.folder_str=self.cf.folder
		self.timestr=self.cf.timestr
		self.save_figs=self.cf.save_figs
		self.plot_X=self.cf.plot_X
		
		self.set_field_vals()
		self.allButtons_torf(True,'')
		
		self.replace_line("config_Swanepoel.py",0,''.join(["current_config_file=\"",self.config_file,"\"\n"]) )
		imp.reload(config_Swanepoel)
		

			
	def replace_line(self,file_name, line_num, text):
		
		lines = open(file_name, 'r').readlines()
		lines[line_num] = text
		out = open(file_name, 'w')
		out.writelines(lines)
		out.close()
		
	def set_finished(self):
		
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
		self.folderEdit.setEnabled(trueorfalse)
		
	def closeEvent(self,event):
		
		reply = QtGui.QMessageBox.question(self, 'Message', "Quit now?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes:
			event.accept()
		elif reply == QtGui.QMessageBox.No:
			event.ignore()  
			
#########################################
#########################################
#########################################

def main():
	
	app = QtGui.QApplication(sys.argv)
	ex = Run_gui()
	sys.exit(app.exec_())

if __name__ == '__main__':
	
	main()
