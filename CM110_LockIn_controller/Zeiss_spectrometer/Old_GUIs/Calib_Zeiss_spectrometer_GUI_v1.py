import os, sys, serial, time
import numpy
import scipy.interpolate
#from numpy.polynomial import polynomial as P
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.exporters
#from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, SIGNAL
import ZaberXmcb_ascii
import zaber_position as zp
import config_calib

class zaber_Thread(QThread):
    
	def __init__(self, sender, Za, calib_file, *argv):
		QThread.__init__(self)
		
		self.end_flag=False
		
		self.sender=sender
		self.Za=Za
		self.calib_file=calib_file
		if argv:
			self.move_num=argv[0]
    
	def __del__(self):
	  
	  self.wait()
	  
	def abort_move(self):
		
		self.end_flag=True
	
	def return_pos_if_stopped(self):
		
		while True:
			if self.end_flag==True:
				self.Za.set_Stop(1,1)
				return self.Za.return_Position_When_Stopped(1,1)
				break
			else:
				min_pos=self.Za.return_Position_When_Stopped(1,1)
				if min_pos==None:
					pass
				else:
					return min_pos
					break
		
	def update(self):
		
		min_pos=self.return_pos_if_stopped()
		pos_nm=self.get_nm(min_pos)
		self.emit(SIGNAL('more_tals(QString,QString)'), str(min_pos), str(pos_nm))
		with open('zaber_position.py', 'w') as thefile:
		  thefile.write( ''.join(['Position=',str(min_pos),'\n']) )

	def run(self):
		  
		if self.sender==u'\u25b2':
			self.Za.move_Relative(1,1,15)
			self.update()
			  
		elif self.sender==u'\u25bc':
			self.Za.move_Relative(1,1,-15)
			self.update()
  
		elif self.sender=='Move rel':
			self.Za.move_Relative(1,1,self.move_num)
			self.update()
			  
		elif self.sender=='Move abs':
			self.Za.move_Absolute(1,1,self.move_num)
			self.update()
			  
		elif 'Move to nm' in self.sender or 'Adjust' in self.sender:
			position=self.get_pos(self.move_num)
			self.Za.move_Absolute(1,1,position)
			self.update()
					  
		elif self.sender=='-> nm':
			min_pos=self.get_pos(self.move_num)
			self.Za.set_Current_Position(1,1,min_pos)
			self.emit(SIGNAL('more_tals(QString,QString)'), str(min_pos), str(self.move_num))
			with open('zaber_position.py', 'w') as thefile:
			  thefile.write( ''.join(['Position=',str(min_pos),'\n']) )
			  
		else:
		  pass
	
	def get_pos(self,nm):

		x=[]
		y=[]
		with open(self.calib_file, 'r') as thefile:
			for line in thefile:
				columns = line.split()
				x.extend([int(columns[0])]) #microstep pos.
				y.extend([round(float(columns[1]),1)]) #wavelength in nm

		if nm<=max(y) and nm>=min(y):
			#spline
			pos_curve=scipy.interpolate.splrep(y, x, k=3, s=0)
			#linear
			#wv_curve = scipy.interpolate.splrep(x, y, k=1, s=0)
			pos_zaber = scipy.interpolate.splev(nm, pos_curve, der=0)
			return int(round(pos_zaber))
		
	def get_nm(self,pos):

		x=[]
		y=[]
		with open(self.calib_file, 'r') as thefile:
			for line in thefile:
				columns = line.split()
				x.extend([int(columns[0])]) #microstep pos.
				y.extend([round(float(columns[1]),1)]) #wavelength
				
		if pos>=min(x) and pos<=max(x):
			#spline
			wv_curve=scipy.interpolate.splrep(x, y, k=3, s=0)
			#linear
			#wv_curve = scipy.interpolate.splrep(x, y, k=1, s=0)
			pos_nm = scipy.interpolate.splev(pos, wv_curve, der=0)
			return round(pos_nm,1)
			
class run_zaber_gui(QtGui.QWidget):
  
	def __init__(self):
		super(run_zaber_gui, self).__init__()
		
		#####################################################
		# constants
		self.wavelength_str = config_calib.wavelengthfile
		self.calib_file_str = config_calib.calibfile
		self.filename_str = config_calib.filename
		self.folder_str = config_calib.create_folder
		self.timestr = config_calib.timestr
		self.zaberport_str = config_calib.zaberport
		
		self.all_pos=[zp.Position]
		
		self.initUI()
    
	def initUI(self):
		
		################### MENU BARS START ##################
		
		MyBar = QtGui.QMenuBar(self)
		fileMenu = MyBar.addMenu("File")
		fileSavePlt = fileMenu.addAction("Save calib plot")
		fileSavePlt.triggered.connect(self.set_save_plots)
		fileSavePlt.setShortcut('Ctrl+P')
		fileSaveSet = fileMenu.addAction("Save settings")        
		fileSaveSet.triggered.connect(self.set_save) # triggers closeEvent()
		fileSaveSet.setShortcut('Ctrl+S')
		fileClose = fileMenu.addAction("Close")        
		fileClose.triggered.connect(self.close) # triggers closeEvent()
		fileClose.setShortcut('Ctrl+X')
				
		modeMenu = MyBar.addMenu("Mode")
		self.conMode = modeMenu.addAction("Connect to serial")
		self.conMode.triggered.connect(self.set_connect)
		self.disconMode = modeMenu.addAction("Disconnect from serial")
		self.disconMode.triggered.connect(self.set_disconnect)
		
		serialMenu = MyBar.addMenu("Serial")
		self.serialZaber = serialMenu.addAction("Zaber stepper")
		self.serialZaber.triggered.connect(self.ZaberDialog)
		
		calibMenu = MyBar.addMenu("Calib")
		calibZeiss = calibMenu.addAction("Load ref calib file")
		calibZeiss.setShortcut('Ctrl+O')
		waveZeiss = calibMenu.addAction("Load wavelength file")
		waveZeiss.setShortcut('Ctrl+W')
		calibZeiss.triggered.connect(self.loadCalibDialog)
		calibZeiss.triggered.connect(self.view_calib_data)
		waveZeiss.triggered.connect(self.loadWaveDialog)
		
		################### MENU BARS END ##################


		##############################################
		
		lbl4 = QtGui.QLabel("STORE new calib file in the location:", self)
		lbl4.setStyleSheet("color: blue")
		filename = QtGui.QLabel("File name",self)
		foldername = QtGui.QLabel("Folder name",self)
		self.filenameEdit = QtGui.QLineEdit(self.filename_str,self)
		self.folderEdit = QtGui.QLineEdit(self.folder_str,self)
		
		##############################################

		# status info which button has been pressed
		self.motorstep_lbl = QtGui.QLabel("ZABER stepper postion:", self)
		self.motorstep_lbl.setStyleSheet("color: blue")
		self.upButton = QtGui.QPushButton(u'\u25b2',self)
		self.set_bstyle_v1(self.upButton)
		self.downButton = QtGui.QPushButton(u'\u25bc',self)
		self.set_bstyle_v1(self.downButton)
		self.moverelButton = QtGui.QPushButton('Move rel',self)
		self.moveabsButton = QtGui.QPushButton('Move abs',self)
		#self.moveabsButton.setStyleSheet('QPushButton {color: red}')
		self.moverelEdit = QtGui.QLineEdit(str(100),self)
		self.moveabsEdit = QtGui.QLineEdit(str(10000),self)
		self.movewlButton = QtGui.QPushButton('Move to nm',self)
		self.movewlButton.setStyleSheet('QPushButton {color: magenta}')
		self.movewlEdit = QtGui.QLineEdit("",self)
		self.stopButton = QtGui.QPushButton('STOP MOVE',self)
		self.stopButton.setEnabled(False)	
		
		##############################################

		# status info which button has been pressed
		self.zeiss_lbl = QtGui.QLabel("ZEISS alignment:", self)
		self.zeiss_lbl.setStyleSheet("color: blue")
		self.alignEdit = QtGui.QLineEdit("",self)
		self.setzeroButton = QtGui.QPushButton('-> nm',self)
		self.setzeroButton.setStyleSheet('QPushButton {color: magenta}')
		self.setzeroButton.setFixedWidth(70)
		#self.setzeroButton.setStyleSheet('QPushButton {color: black}')
		
		##############################################
		
		# status info which button has been pressed
		self.zeiss_cal_lbl = QtGui.QLabel("ZEISS calibration:", self)
		self.zeiss_cal_lbl.setStyleSheet("color: blue")
		self.calibButton = QtGui.QPushButton('',self)
		self.calibButton.setStyleSheet('QPushButton {color: magenta}')
		self.calibSaveButton = QtGui.QPushButton('',self)
		#self.reorderButton = QtGui.QPushButton('Reorder',self)
		#self.reorderButton.setFixedWidth(65)
		#self.reorderButton.setEnabled(False)
		
		##############################################
		
		self.timetrace_str = QtGui.QLabel("TIME trace for storing plots and data:", self)
		self.timetrace_str.setStyleSheet("color: blue")	
		
		##############################################
		
		self.lcd = QtGui.QLCDNumber(self)
		self.lcd.setStyleSheet("color: black")
		self.lcd.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd.setNumDigits(6)
		self.lcd.display(self.all_pos[-1])
		
		self.lcd2 = QtGui.QLCDNumber(self)
		self.lcd2.setStyleSheet("color: magenta")
		self.lcd2.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd2.setNumDigits(6)
		self.lcd2.display('000000')
		#self.lcd2.setFixedWidth(120)
		
		self.lcd3 = QtGui.QLCDNumber(self)
		self.lcd3.setStyleSheet("color: red")
		self.set_lcd3_style(self.lcd3)
		self.lcd3.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd3.setNumDigits(11)
		self.lcd3.display(self.timestr)
		#self.lcd3.setFixedWidth(280)
		##############################################
		'''
		if str(self.filenameEdit.text()):
			saveinfile=''.join([str(self.filenameEdit.text()),'_',self.timestr])
		else:
			saveinfile=''.join(["calib_",self.timestr])
			
		if str(self.folderEdit.text()):
			if not os.path.isdir(str(self.folderEdit.text())):
				os.mkdir(str(self.folderEdit.text()))
			saveinfolder=''.join([str(self.folderEdit.text()),"/"])
		else:
			saveinfolder=""
			
		self.save_to_file=''.join([saveinfolder,saveinfile,".txt"])
		'''
		##############################################
		
		try:
			self.y_local=[]
			self.calibCounter=0
			with open(self.wavelength_str, 'r') as thefile:
				for line in thefile:
					columns = line.split()
					self.y_local.extend([round(float(columns[0]),1)])
			self.calibButton.setText(''.join(['Adjust to ',str(self.y_local[self.calibCounter]),' nm']))
			self.wl_point=self.y_local[self.calibCounter]	
			self.calibSaveButton.setText(''.join(['Save at ',str(self.wl_point),' nm' ]))
			#self.calibCounter+=1
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message',"Something is wrong with the wavelength file! Do you have a wavelength file with 1 column, no headers, and all inputs are digits?")
			self.calibButton.setText('Adjust to ---- nm')
			self.calibButton.setEnabled(False)
			self.calibSaveButton.setEnabled(False)
			
		##############################################

		g4_0=QtGui.QGridLayout()
		g4_0.addWidget(MyBar,0,0)
		v4 = QtGui.QVBoxLayout()
		v4.addLayout(g4_0)
				
		g8_0 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g8_0.addWidget(lbl4)
		g8_1 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g8_1.addWidget(filename)
		g8_1.addWidget(foldername)
		g8_2 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g8_2.addWidget(self.filenameEdit)
		g8_2.addWidget(self.folderEdit)
		g8_3 = QtGui.QSplitter(QtCore.Qt.Horizontal)
		g8_3.addWidget(g8_1)
		g8_3.addWidget(g8_2)
		v8 = QtGui.QSplitter(QtCore.Qt.Vertical)
		v8.addWidget(g8_0)
		v8.addWidget(g8_3)

		g0_0 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g0_0.addWidget(self.motorstep_lbl)
		g0_1 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g0_1.addWidget(self.upButton)
		g0_1.addWidget(self.downButton)
		g0_2 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g0_2.addWidget(self.lcd)
		h0 = QtGui.QSplitter(QtCore.Qt.Horizontal)
		h0.addWidget(g0_1)
		h0.addWidget(g0_2)
		g0_3=QtGui.QSplitter(QtCore.Qt.Vertical)
		g0_3.addWidget(self.moverelButton)
		g0_3.addWidget(self.moveabsButton)
		g0_3.addWidget(self.movewlButton)
		g0_4=QtGui.QSplitter(QtCore.Qt.Vertical)
		g0_4.addWidget(self.moverelEdit)
		g0_4.addWidget(self.moveabsEdit)
		g0_4.addWidget(self.movewlEdit)
		g0_5=QtGui.QSplitter(QtCore.Qt.Vertical)
		g0_5.addWidget(self.stopButton)
		h1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
		h1.addWidget(g0_5)
		h1.addWidget(g0_3)
		h1.addWidget(g0_4)
		v1 = QtGui.QSplitter(QtCore.Qt.Vertical)
		v1.addWidget(g0_0)
		v1.addWidget(h0)
		v1.addWidget(h1)
		
		g3_0=QtGui.QSplitter(QtCore.Qt.Vertical)
		g3_0.addWidget(self.zeiss_lbl)
		g3_1=QtGui.QSplitter(QtCore.Qt.Vertical)
		g3_1.addWidget(self.alignEdit)
		g3_1.addWidget(self.setzeroButton)
		g3_2=QtGui.QSplitter(QtCore.Qt.Horizontal)
		g3_2.addWidget(g3_1)
		g3_2.addWidget(self.lcd2)
		h4 = QtGui.QSplitter(QtCore.Qt.Vertical)
		h4.addWidget(g3_0)
		h4.addWidget(g3_2)
		
		g5_0=QtGui.QSplitter(QtCore.Qt.Vertical)
		g5_0.addWidget(self.zeiss_cal_lbl)
		g5_1=QtGui.QSplitter(QtCore.Qt.Horizontal)
		g5_1.addWidget(self.calibButton)
		g5_1.addWidget(self.calibSaveButton)
		h5 = QtGui.QSplitter(QtCore.Qt.Vertical)
		h5.addWidget(g5_0)
		h5.addWidget(g5_1)
		
		g9_0 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g9_0.addWidget(self.timetrace_str)
		g9_0.addWidget(self.lcd3)
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		v_all = QtGui.QVBoxLayout()
		v_all.addLayout(v4)
		v_all.addWidget(v8)
		v_all.addWidget(h4)
		v_all.addWidget(h5)
		v_all.addWidget(v1)
		v_all.addWidget(g9_0)
		
		# set graph  and toolbar to a new vertical group vcan
		g0_0 = QtGui.QGridLayout()
		self.pw0 = pg.PlotWidget(name="Plot2")  ## giving the plots names allows us to link their axes together
		self.pw0.setTitle('Ref calib file')
		self.pw0.setLabel('left', 'wavelength', units='nm')
		self.pw0.setLabel('bottom', 'stepper micropos.')
		g0_0.addWidget(self.pw0,0,1)
		
		self.pw2 = pg.PlotWidget(name="Plot1")
		self.pw2.setTitle('New calib file')
		self.pw2.setLabel('left', 'wavelength', units='nm')
		self.pw2.setLabel('bottom', 'stepper micropos.')
		g0_0.addWidget(self.pw2,0,0)
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		h_all = QtGui.QHBoxLayout()
		h_all.addLayout(v_all)
		h_all.addLayout(g0_0)
		self.setLayout(h_all)

		########################################
		# create plot and add it to the figure canvas		
		self.p0 = self.pw0.plotItem
		self.p0.addLegend()
		#self.curve0=self.p0.plot(pen='r')
		self.curve0_1=self.p0.plot(pen='m',name='raw data')
		self.curve0_2=self.p0.plot(pen='b',name='spline')
		#self.pw0.setDownsampling(mode='peak')
		#self.pw0.setClipToView(True)
		
		# PLOT 3 settings
		self.p2 = self.pw2.plotItem		
		self.p2.addLegend()
		self.curve2=self.p2.plot(pen='m',name='raw data')
		self.curve1=self.p2.plot(pen='b',name='spline')
		#self.curve3=self.p2.plot(pen='w',name='scan')
		
		#########################################

		self.disconMode.setEnabled(False)
		self.allButtons_torf(False)
	
		self.calibSaveButton.clicked.connect(self.add_calib)
		self.calibButton.clicked.connect(self.move_to_nm2)
		self.calibButton.clicked.connect(self.update_calib_button)
		self.setzeroButton.clicked.connect(self.set_zero)
		#self.reorderButton.clicked.connect(self.set_reorder)
		
		self.upButton.clicked.connect(self.move_jog)
		self.downButton.clicked.connect(self.move_jog)
		self.moverelButton.clicked.connect(self.move_rel)
		self.moveabsButton.clicked.connect(self.move_abs)
		self.movewlButton.clicked.connect(self.move_to_nm)
		self.stopButton.clicked.connect(self.move_stop)
		
		self.setGeometry(30,30,1200,550)
		self.setWindowTitle('Zeiss spectrometer calibration')
		self.show()
		self.view_calib_data()

	##########################################
	
	def set_lcd3_style(self,lcd):

		#lcd.setFixedWidth(40)
		lcd.setFixedHeight(60)
	
	def ZaberDialog(self):

		text, ok = QtGui.QInputDialog.getText(self, 'Serial Port Dialog','Enter Zaber stepper serial:', text=self.zaberport_str)
		if ok:
			self.zaberport_str = str(text)
	
	def loadCalibDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file','C:/Documents and Settings/PLD User/My Documents/Vedran_work_folder/Zeiss_spectrometer/Calib_files')
		if fname:
			self.calib_file_str = str(fname)
	
	def loadWaveDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file','C:/Documents and Settings/PLD User/My Documents/Vedran_work_folder/Zeiss_spectrometer/Wavelength_files')
		if fname:
			self.wavelength_str = str(fname)
		
		try:
			self.y_local=[]
			self.calibCounter=0
			with open(self.wavelength_str, 'r') as thefile:
				for line in thefile:
					columns = line.split()
					self.y_local.extend([round(float(columns[0]),1)])
			self.calibButton.setText(''.join(['Adjust to ',str(self.y_local[self.calibCounter]),' nm']))
			self.wl_point=self.y_local[self.calibCounter]
			self.calibSaveButton.setText(''.join(['Save at ',str(self.wl_point),' nm' ]))
			#self.calibCounter+=1
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message',"Something is wrong with the wavelength file! Do you have a wavelength file with 1 column, no headers, and all inputs are digits?")
			self.calibButton.setText('Adjust to ---- nm')
			self.calibButton.setEnabled(False)
			self.calibSaveButton.setEnabled(False)
			
	def set_connect(self):
		
		try:
			self.Za = ZaberTmca_ascii.Zaber_Tmca(self.zaberport_str)
			self.allButtons_torf(True)
			self.conMode.setEnabled(False)
			self.disconMode.setEnabled(True)
			self.serialZaber.setEnabled(False)
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message',"No response from Zaber serial port! Check the port name and check the power line.")

		# constants
		max_pos=245000
		min_pos=0
		hc=20
		rc=20
		ms=2048
		
		self.Za.set_Maximum_Position(1,1,max_pos)
		self.Za.set_Minimum_Position(1,1,min_pos)
		self.Za.set_Hold_Current(1,1,hc)
		self.Za.set_Running_Current(1,1,rc)
		self.Za.set_Max_Speed(1,1,ms)
		
		micstep=self.Za.return_Microstep_Resolution(1,1)
		sc=self.Za.return_System_Current(1)

		hc_str=''.join([str(hc*25e-3)," / ",str(rc*25e-3)," Amps" ])
		print "Hold / Running current:", hc_str
		sys_str=''.join([ str(sc), " Amps" ])
		print "System current (0-5):", sys_str
		ms_str=''.join([str(ms/1.6384), " microsteps/s"])
		print "Max speed:", ms_str
		micstep_str=''.join([str(micstep), " microsteps/step"])
		print "Microstep resolution:", str(micstep_str)
		min_pos_str=''.join([str(min_pos), " microsteps"])
		print "Minimum position:", min_pos_str
		max_pos_str=''.join([str(max_pos), " microsteps"])
		print "Maximum position:", max_pos_str

		# constants
		if self.Za.return_Alert(1)==0:
			self.Za.set_Alert(1,1)
		self.Za.set_timeout(0.025)
		self.Za.set_Current_Position(1,1,self.all_pos[-1])

	def set_disconnect(self):

		self.Za.set_Hold_Current(1,1,0)
		self.Za.close()
		
		self.allButtons_torf(False)
		self.conMode.setEnabled(True)
		self.disconMode.setEnabled(False)
		
	def allButtons_torf(self,text):
		
		self.calibButton.setEnabled(text)
		self.alignEdit.setEnabled(text)
		self.setzeroButton.setEnabled(text)
		self.calibSaveButton.setEnabled(text)
		#self.reorderButton.setEnabled(text)
		
		self.filenameEdit.setEnabled(text)
		self.folderEdit.setEnabled(text)
		
		self.upButton.setEnabled(text)
		self.downButton.setEnabled(text)
		self.moverelButton.setEnabled(text)
		self.moveabsButton.setEnabled(text)
		self.movewlButton.setEnabled(text)
		self.moverelEdit.setEnabled(text)
		self.moveabsEdit.setEnabled(text)
		self.movewlEdit.setEnabled(text)
		#self.stopButton.setEnabled(text)
	
	def closeEvent(self, event):
		
		reply = QtGui.QMessageBox.question(self, 'Message', "Quit now? The microstep position will be saved and the stepper will turn off the hold current!", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes:
			if hasattr(self, 'Za'):
				if self.conMode.isEnabled()==False:
					if not hasattr(self, 'get_zaber_Thread'):
						self.Za.set_Hold_Current(1,1,0)
						self.Za.close()
						event.accept()
					else:
						if self.get_zaber_Thread.isRunning():
							QtGui.QMessageBox.warning(self, 'Message', "Run in progress. Cancel the run then quit!")
							event.ignore()
						else:
							self.Za.set_Hold_Current(1,1,0)
							self.Za.close()
							event.accept()
				else:
					pass
			else:
				event.accept()
		else:
		  event.ignore() 
	##########################################

	def set_bstyle_v1(self,button):
		
		button.setStyleSheet('QPushButton {font-size: 25pt}')
		button.setFixedWidth(40)
		button.setFixedHeight(40)
  
	def add_calib(self):
		
		if str(self.filenameEdit.text()):
			saveinfile=''.join([str(self.filenameEdit.text()),'_',self.timestr])
		else:
			saveinfile=''.join(["calib_",self.timestr])
			
		if str(self.folderEdit.text()):
			if not os.path.isdir(str(self.folderEdit.text())):
				os.mkdir(str(self.folderEdit.text()))
			saveinfolder=''.join([str(self.folderEdit.text()),"/"])
		else:
			saveinfolder=""
			
		self.save_to_file=''.join([saveinfolder,saveinfile,".txt"])
		
		if not os.path.exists(self.save_to_file):
			print "Calib file created: ", self.save_to_file
			with open(self.save_to_file, 'w') as thefile:
				pass
			
		with open(self.save_to_file, 'r') as thefile:
			# read a list of lines into data
			data = thefile.readlines()
		
		if data and str(self.wl_point) in data[-1]:
			data[-1]=''.join([str(self.all_pos[-1]),'\t',str(self.wl_point),'\n'])
			with open(self.save_to_file, 'w') as thefile:
				thefile.writelines(data)
		else:
			with open(self.save_to_file, 'a') as thefile:
				thefile.write('%s' %self.all_pos[-1] )
				thefile.write('\t%s\n' %self.wl_point)
		
		# open calib file and plot
		x=[]
		y=[]
		with open(self.save_to_file, 'r') as thefile:
		  for line in thefile:
				columns = line.split()
				x.extend([int(columns[0])])
				y.extend([round(float(columns[1]),1)])
		
		self.curve2.setData(x,y)  
		#self.reorderButton.setEnabled(True)
	
	def update_calib_button(self):
		
		if len(self.y_local)-1>self.calibCounter:
			self.wl_point=self.y_local[self.calibCounter]
			self.calibSaveButton.setText(''.join(['Save at ',str(self.wl_point),' nm' ]))
			
			self.calibCounter+=1
			self.calibButton.setText(''.join(['Adjust to ',str(self.y_local[self.calibCounter]),' nm']))
		else:
			self.wl_point=self.y_local[self.calibCounter]
			self.calibSaveButton.setText(''.join(['Save at ',str(self.wl_point),' nm' ]))
			
			self.calibCounter=0
			self.calibButton.setText(''.join(['Adjust to ',str(self.y_local[self.calibCounter]),' nm']))

			
	'''
	def set_reorder(self):
		
		if os.path.exists(self.filenameEdit.text()):
			# open calib file and get all x and y
			x=[]
			y=[]
			with open(self.save_to_file, 'r') as thefile:
				for line in thefile:
					columns = line.split()
					x.extend([int(columns[0])])
					y.extend([round(float(columns[1]),1)])
			# sort x element and their respective y
			sort_index = numpy.argsort(x)	
			sort_x=[]
			sort_y=[]	
			with open(self.save_to_file, 'w') as thefile:
				for i in sort_index:
					thefile.write('%s\t' %x[i])
					thefile.write('%s\n' %y[i])				
					sort_x.extend([ x[i] ])
					sort_y.extend([ y[i] ])	
			self.curve2.setData(sort_x,sort_y)  
			#self.alignEdit.setText('')
		else:
			print "Warning! The calib file path does not exists!"
	'''
		
	def view_calib_data(self):
		
		try:
			x=[]
			y=[]
			with open(self.calib_file_str, 'r') as thefile:
				for line in thefile:
					columns = line.split()
					x.extend([int(columns[0])])
					y.extend([round(float(columns[1]),1)])
			
			self.min_y_calib=min(y)
			self.max_y_calib=max(y)			
			self.curve0_1.setData(x,y) 
			
			wv_fine=numpy.arange(y[0],y[-1]+0.1,0.1)
			#spline
			wv_curve=scipy.interpolate.splrep(y, x, k=3, s=0)
			#linear
			#wv_curve = scipy.interpolate.splrep(y, x, k=1, s=0)		
			positions_fine = scipy.interpolate.splev(wv_fine, wv_curve, der=0)
			self.curve0_2.setData(positions_fine,wv_fine)
			
			if self.all_pos[-1]<min(x) or self.all_pos[-1]>max(x):
				self.lcd2.display('------')
			else:
				# Update the LCD display lcd2 with the wavelength which
				# corresponds to the saved Zaber microposition
				wv_curve2=scipy.interpolate.splrep(x, y, k=3, s=0)
				first_pos_nm = scipy.interpolate.splev(self.all_pos[-1], wv_curve2, der=0)
				self.lcd2.display(str(round(first_pos_nm,1)))
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message', 
														"Something is wrong with ref calib file! Do you have a ref Calib file with 2 columns, no headers, and all inputs are digits?")
			self.lcd2.display('------')
			self.curve0_1.setData([],[])
			self.curve0_2.setData([],[])	
	
	def move_stop(self):
		
		self.get_zaber_Thread.abort_move()
		self.disconMode.setEnabled(True)
		self.allButtons_torf(True)

	def set_zero(self):
		
		move_num=round(float(self.alignEdit.text()),1)
		if move_num<self.min_y_calib or move_num>self.max_y_calib:
			QtGui.QMessageBox.warning(self, 'Message',
														 ''.join(['Valid range is from ',str(self.min_y_calib),' nm to ',str(self.max_y_calib),' nm.' ]) )
		else:
			sender = self.sender()
			get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.calib_file_str,move_num)
			self.connect(get_zaber_Thread,SIGNAL("more_tals(QString,QString)"),self.more_tals)
			self.connect(get_zaber_Thread, SIGNAL('finished()'), self.set_finished)

			get_zaber_Thread.start()
	
	def move_to_nm(self):
		
		# update the lcd motorstep position
		move_num = round(float(self.movewlEdit.text()),1)
		if move_num<self.min_y_calib or move_num>self.max_y_calib:
			QtGui.QMessageBox.warning(self, 'Message',
														 ''.join(['Valid range is from ',str(self.min_y_calib),' nm to ',str(self.max_y_calib),' nm.' ]) )
		else:
			self.stopButton.setEnabled(True)
			self.disconMode.setEnabled(False)
			self.allButtons_torf(False)
			
			sender = self.sender()
			self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.calib_file_str,move_num)
			self.connect(self.get_zaber_Thread,SIGNAL("more_tals(QString,QString)"),self.more_tals)
			self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
			
			self.get_zaber_Thread.start()
		
	def move_to_nm2(self):
		
		# update the lcd motorstep position
		move_num = round(self.y_local[self.calibCounter],1)
		print move_num
		self.stopButton.setEnabled(True)
		self.disconMode.setEnabled(False)
		self.allButtons_torf(False)
		
		sender = self.sender()
		self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.calib_file_str,move_num)
		self.connect(self.get_zaber_Thread,SIGNAL("more_tals(QString,QString)"),self.more_tals)
		self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
		
		self.get_zaber_Thread.start()
		
	def move_rel(self):
		
		# update the lcd motorstep position
		move_num = int(self.moverelEdit.text())
		move_tot = move_num+self.all_pos[-1]
		if move_tot<0 or move_tot>245000:
			QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid range is from ',str(0),' to ',str(245000),' microsteps.' ]) )
		else:
			self.stopButton.setEnabled(True)
			self.disconMode.setEnabled(False)
			self.allButtons_torf(False)
			
			sender = self.sender()
			self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.calib_file_str,move_num)
			self.connect(self.get_zaber_Thread,SIGNAL("more_tals(QString,QString)"),self.more_tals)
			self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
			
			self.get_zaber_Thread.start()
		
	def move_abs(self):
		
		# update the lcd motorstep position
		move_num = int(self.moveabsEdit.text())
		if move_num<0 or move_num>245000:
			QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid range is from ',str(0),' to ',str(245000),' microsteps.' ]) )
		else:
			self.stopButton.setEnabled(True)
			self.disconMode.setEnabled(False)
			self.allButtons_torf(False)
			
			sender = self.sender()
			self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.calib_file_str,move_num)
			self.connect(self.get_zaber_Thread,SIGNAL("more_tals(QString,QString)"),self.more_tals)
			self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
			    
			self.get_zaber_Thread.start()
		
	def move_jog(self):
		
		# update the lcd motorstep position
		sender = self.sender()
		self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.calib_file_str)
		self.connect(self.get_zaber_Thread,SIGNAL("more_tals(QString,QString)"),self.more_tals)
		self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
		
		self.get_zaber_Thread.start()
				
	def more_tals(self,pos,pos_nm):
		
		self.lcd.display(pos)
		self.lcd2.display(pos_nm)
		self.all_pos.extend([ int(pos) ])    
	
	def set_finished(self):
				
		self.stopButton.setEnabled(False)
		self.disconMode.setEnabled(True)
		self.allButtons_torf(True)
		
	def set_save_plots(self):
		
		save_pic_to_file=''.join([self.save_to_file[:-15],self.timestr,'.png'])
		# create an exporter instance, as an argument give it
		# the item you wish to export
		exporter = pg.exporters.ImageExporter(self.pw2.plotItem)
		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_pic_to_file)

	def set_save(self):
		
		self.timestr=time.strftime("%y%m%d-%H%M")
		with open("config_calib.py", 'w') as thefile:
			thefile.write( ''.join(["wavelengthfile=\"",self.wavelength_str,"\"\n"]) )
			thefile.write( ''.join(["calibfile=\"",self.calib_file_str,"\"\n"]) )
			thefile.write( ''.join(["filename=\"",str(self.filenameEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["create_folder=\"",str(self.folderEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["timestr=\"",self.timestr,"\"\n"]) )
			thefile.write( ''.join(["zaberport=\"",self.zaberport_str,"\"\n"]) )

		reload(config_calib)
		self.wavelength_str = config_calib.wavelengthfile
		self.calib_file_str = config_calib.calibfile
		self.filename_str=config_calib.filename
		self.folder_str=config_calib.create_folder
		self.timestr=config_calib.timestr
		self.zaberport_str = config_calib.zaberport
		
		self.lcd3.display(self.timestr)

def main():
  
  app=QtGui.QApplication(sys.argv)
  ex=run_zaber_gui()
  sys.exit(app.exec_())
    
if __name__=='__main__':
  main()
  
