import os, sys, imp, serial, time, numpy
import scipy.interpolate
#from numpy.polynomial import polynomial as P
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.exporters
#from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, QTimer, SIGNAL
import config_zeiss, ZaberXmcb_ascii



class zaber_Thread(QThread):
    
	def __init__(self, sender, Za, adjust_mode, calib_file, *argv):
		QThread.__init__(self)
		
		self.end_flag=False
		
		self.sender=sender
		self.Za=Za
		self.calib_mode=adjust_mode
		self.calib_file=calib_file
		
		if self.calib_mode=="wavelength":
			self.axs=1
		elif self.calib_mode=="slit":
			self.axs=2
		
		if argv:
			self.move_num=argv[0]
    
	def __del__(self):
	  
	  self.wait()
	  
	def abort_move(self):
		
		self.Za.set_Stop(1,self.axs)
		self.end_flag=True
	
	
	def return_pos_if_stopped(self):
		
		return self.Za.return_Position_When_Stopped(1,self.axs)

		
	def update(self):
		
		min_pos=self.return_pos_if_stopped()
		if min_pos in [serial.SerialException, ValueError]:
			self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),min_pos)
			return
		
		pos_val=self.get_zeiss_value(min_pos)
		if self.calib_mode=="wavelength":
			self.replace_line("config_zeiss.py",4,''.join(["Last_position_lambda=[",str(min_pos),",",str(pos_val),"]\n"]))
		elif self.calib_mode=="slit":
			self.replace_line("config_zeiss.py",5,''.join(["Last_position_slit=[",str(min_pos),",",str(pos_val),"]\n"]))
		imp.reload(config_zeiss)
		
		
		more_tals_obj=type('more_tals_obj',(object,),{'min_pos':min_pos, 'pos_val':pos_val})
		self.emit(SIGNAL('more_tals(PyQt_PyObject)'), more_tals_obj)
		
		
	def replace_line(self,file_name, line_num, text):
		
		lines = open(file_name, 'r').readlines()
		lines[line_num] = text
		out = open(file_name, 'w')
		out.writelines(lines)
		out.close()
		
	
	def run(self):
		  
		if self.sender==u'\u25b2':
			check=self.Za.move_Relative(1,self.axs,10)
			if check in [serial.SerialException, ValueError]:
				self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),check)
				return
			self.update()
			  
		elif self.sender==u'\u25bc':
			check=self.Za.move_Relative(1,self.axs,-10)
			if check in [serial.SerialException, ValueError]:
				self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),check)
				return
			self.update()
  
		elif self.sender=='Move rel':
			check=self.Za.move_Relative(1,self.axs,self.move_num)
			if check in [serial.SerialException, ValueError]:
				self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),check)
				return
			self.update()
			  
		elif self.sender=='Move abs':
			check=self.Za.move_Absolute(1,self.axs,self.move_num)
			if check in [serial.SerialException, ValueError]:
				self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),check)
				return
			self.update()
			  
		elif 'Move to' in self.sender or 'Adjust' in self.sender:
			position=self.get_pos(self.move_num)
			check=self.Za.move_Absolute(1,self.axs,position)
			if check in [serial.SerialException, ValueError]:
				self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),check)
				return
			self.update()
					  
		elif self.sender=='-> nm':
			min_pos=self.get_pos(self.move_num)
			check=self.Za.set_Current_Position(1,self.axs,min_pos)
			if check in [serial.SerialException, ValueError]:
				self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),check)
				return
			
			more_tals_obj=type('more_tals_obj',(object,),{'min_pos':min_pos, 'pos_val':self.move_num})
			self.emit(SIGNAL('more_tals(PyQt_PyObject)'), more_tals_obj)
			
			self.replace_line("config_zeiss.py",4,''.join(["Last_position_lambda=[",str(min_pos),",",str(self.move_num),"]\n"]))
			imp.reload(config_zeiss)
			
			
		elif self.sender=='-> mm':
			min_pos=self.get_pos(self.move_num)
			check=self.Za.set_Current_Position(1,self.axs,min_pos)
			if min_pos in [serial.SerialException, ValueError]:
				self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),min_pos)
				return
			
			more_tals_obj=type('more_tals_obj',(object,),{'min_pos':min_pos, 'pos_val':self.move_num})
			self.emit(SIGNAL('more_tals(PyQt_PyObject)'), more_tals_obj)
			
			self.replace_line("config_zeiss.py",5,''.join(["Last_position_slit=[",str(min_pos),",",str(self.move_num),"]\n"]))
			imp.reload(config_zeiss)
			
		else:
		  pass
	
	def get_pos(self,nm):
		
		x=[]
		y=[]
		with open(self.calib_file, 'r') as thefile:
			for line in thefile:
				columns = line.split()
				x.extend([int(columns[0])]) #microstep pos.
				if self.calib_mode=="wavelength":
					y.extend([round(float(columns[1]),1)]) #wavelength
				elif self.calib_mode=="slit":
					y.extend([round(float(columns[1]),2)]) #slit
					
		if numpy.min(nm)>=min(y) and numpy.max(nm)<=max(y):
			#spline
			pos_curve=scipy.interpolate.splrep(y, x, k=3, s=0)
			#linear
			#wv_curve = scipy.interpolate.splrep(x, y, k=1, s=0)
			pos_pos = scipy.interpolate.splev(nm, pos_curve, der=0)
			nums=numpy.rint(pos_pos) # round the up/down floats
			return nums.astype(int)
		
	def get_zeiss_value(self,pos):
		
		x=[]
		y=[]
		with open(self.calib_file, 'r') as thefile:
			for line in thefile:
				columns = line.split()
				x.extend([int(columns[0])]) #microstep pos.
				if self.calib_mode=="wavelength":
					y.extend([round(float(columns[1]),1)]) #wavelength
				elif self.calib_mode=="slit":
					y.extend([round(float(columns[1]),2)]) #slit
					
		if numpy.min(pos)>=min(x) and numpy.max(pos)<=max(x):
			#spline
			wv_curve=scipy.interpolate.splrep(x, y, k=3, s=0)
			#linear
			#wv_curve = scipy.interpolate.splrep(x, y, k=1, s=0)
			pos = scipy.interpolate.splev(pos, wv_curve, der=0)
			if self.calib_mode=="wavelength":
				return numpy.round(pos,1)
			elif self.calib_mode=="slit":
				return numpy.round(pos,2)
	
	
	
	
	
	
	
	
	
	
	


class Run_gui(QtGui.QDialog):
  
	def __init__(self, MyBar, parent=None):
		QtGui.QDialog.__init__(self, parent)
		#super(Run_gui, self).__init__()
		
		#####################################################
		
		# constants
		self.Validrange_lambda = config_zeiss.Validrange_lambda
		self.Validrange_slit = config_zeiss.Validrange_slit
		self.Range_lambda = config_zeiss.Range_lambda
		self.Range_slit = config_zeiss.Range_slit

		self.calibfile_lambda_str = config_zeiss.calibfile_lambda
		self.calibfile_slit_str = config_zeiss.calibfile_slit
		
		self.lambda_str=config_zeiss.lambdafile
		self.slit_str=config_zeiss.slitfile
		
		self.timestr = config_zeiss.timestr
		self.filename_str = config_zeiss.filename
		self.folder_str = config_zeiss.foldername	
		self.zaberport_str = config_zeiss.zaberport
		self.sr510port_str = config_zeiss.sr510port
		
		
		self.all_pos=[config_zeiss.Last_position_lambda[0]]
		
		self.MyBar=MyBar
		
		self.initUI()
    
	def initUI(self):
		
		self.infoCalibButton = QtGui.QPushButton('Calib files info',self)
		
		################### MENU BARS START ##################
		
		#MyBar = QtGui.QMenuBar(self)
		fileMenu = self.MyBar.addMenu("File")
		fileSavePlt = fileMenu.addAction("Save calib plot")
		fileSavePlt.triggered.connect(self.set_save_plots)
		fileSavePlt.setShortcut('Ctrl+P')
		fileSaveSet = fileMenu.addAction("Save settings")        
		fileSaveSet.triggered.connect(self.set_save) # triggers closeEvent()
		fileSaveSet.setShortcut('Ctrl+S')
		fileClose = fileMenu.addAction("Close")        
		fileClose.triggered.connect(self.close) # triggers closeEvent()
		fileClose.setShortcut('Ctrl+X')
				
		modeMenu = self.MyBar.addMenu("Mode")
		self.conMode = modeMenu.addAction("Connect to serial")
		self.conMode.triggered.connect(self.set_connect)
		self.disconMode = modeMenu.addAction("Disconnect from serial")
		self.disconMode.triggered.connect(self.set_disconnect)
		
		serialMenu = self.MyBar.addMenu("Serial")
		self.serialZaber = serialMenu.addAction("Zaber stepper")
		self.serialZaber.triggered.connect(self.ZaberDialog)
		
		calibMenu = self.MyBar.addMenu("Calib")
		self.calibWaveZeiss = calibMenu.addAction("Load ref lambda calib file")
		self.waveZeiss = calibMenu.addAction("Load wavelength file")
		self.waveZeiss.setShortcut('Ctrl+W')
		self.calibWaveZeiss.triggered.connect(self.loadCalibLambdaDialog)
		self.waveZeiss.triggered.connect(self.loadWaveDialog)
		
		self.calibSlitZeiss = calibMenu.addAction("Load ref slit calib file")
		self.slitZeiss = calibMenu.addAction("Load slit width file")
		self.slitZeiss.setShortcut('Ctrl+Q')
		self.calibSlitZeiss.triggered.connect(self.loadCalibSlitDialog)
		self.slitZeiss.triggered.connect(self.loadSlitDialog)
		
		################### MENU BARS END ##################


		lb3 = QtGui.QLabel("CALIBRATE:",self)
		lb3.setStyleSheet("color: blue")
		self.cb3 = QtGui.QComboBox(self)
		mylist3=["wavelength","slit"]
		self.cb3.addItems(mylist3)
		self.cb3.setCurrentIndex(mylist3.index("wavelength"))
		#self.cb3.setEnabled(True)

		##############################################
		
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
		self.moveButton = QtGui.QPushButton('Move to nm',self)
		self.moveButton.setStyleSheet('QPushButton {color: magenta}')
		self.moveEdit = QtGui.QLineEdit("",self)
		self.stopButton = QtGui.QPushButton('STOP MOVE',self)
		
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
		
		self.lcd1 = QtGui.QLCDNumber(self)
		self.lcd1.setStyleSheet("color: black")
		self.lcd1.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd1.setNumDigits(6)
		
		self.lcd2 = QtGui.QLCDNumber(self)
		self.lcd2.setStyleSheet("color: magenta")
		self.lcd2.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd2.setNumDigits(6)
		#self.lcd2.setFixedWidth(120)
		
		self.lcd3 = QtGui.QLCDNumber(self)
		self.lcd3.setStyleSheet("color: red")
		self.lcd3.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd3.setNumDigits(11)
		self.lcd3.setFixedHeight(60)
		self.lcd3.display(self.timestr)
		
		##############################################
		
		#g4_0=QtGui.QGridLayout()
		#g4_0.addWidget(MyBar,0,0)
		v4 = QtGui.QVBoxLayout()
		#v4.addLayout(g4_0)
		v4.addWidget(self.infoCalibButton)
		
		g2_0 = QtGui.QSplitter(QtCore.Qt.Horizontal)
		g2_0.addWidget(lb3)
		g2_0.addWidget(self.cb3)
		
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
		v8.addWidget(g2_0)
		v8.addWidget(g8_3)

		g0_0 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g0_0.addWidget(self.motorstep_lbl)
		g0_1 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g0_1.addWidget(self.upButton)
		g0_1.addWidget(self.downButton)
		g0_2 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g0_2.addWidget(self.lcd1)
		h0 = QtGui.QSplitter(QtCore.Qt.Horizontal)
		h0.addWidget(g0_1)
		h0.addWidget(g0_2)
		g0_3=QtGui.QSplitter(QtCore.Qt.Vertical)
		g0_3.addWidget(self.moverelButton)
		g0_3.addWidget(self.moveabsButton)
		g0_3.addWidget(self.moveButton)
		g0_4=QtGui.QSplitter(QtCore.Qt.Vertical)
		g0_4.addWidget(self.moverelEdit)
		g0_4.addWidget(self.moveabsEdit)
		g0_4.addWidget(self.moveEdit)
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
		pw = pg.GraphicsLayoutWidget()
		pw.setFixedWidth(750)
		
		self.p0 = pw.addPlot()
		self.p0.setTitle('Ref calib file')
		self.p0.setLabel('left', u'\u03bb', units='m')
		self.p0.setLabel('bottom', 'stepper micropos.')
		
		self.p1 = pw.addPlot()
		self.p1.setTitle('New calib file')
		self.p1.setLabel('left', u'\u03bb', units='m')
		self.p1.setLabel('bottom', 'stepper micropos.')
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		h_all = QtGui.QHBoxLayout()
		h_all.addLayout(v_all)
		h_all.addWidget(pw)
		self.setLayout(h_all)

		########################################
		# create plot and add it to the figure canvas		
		self.p0.addLegend()
		#self.curve0=self.p0.plot(pen='r')
		self.curve0_1=self.p0.plot(pen='m',name='raw data')
		self.curve0_2=self.p0.plot(pen='b',name='spline')
		#self.p0.setDownsampling(mode='peak')
		#self.p0.setClipToView(True)
		
		# PLOT 3 settings
		self.p1.addLegend()
		self.curve2=self.p1.plot(pen='m',name='raw data')
		#self.curve1=self.p1.plot(pen='b',name='spline')
		#self.curve3=self.p1.plot(pen='w',name='scan')
		
		#########################################
		
		self.calibSaveButton.clicked.connect(self.add_calib)
		self.calibButton.clicked.connect(self.move_to_val2)
		self.calibButton.clicked.connect(self.update_calib_button)
		self.setzeroButton.clicked.connect(self.set_zero)
		self.cb3.activated[str].connect(self.onActivated3)
		#self.reorderButton.clicked.connect(self.set_reorder)
		
		self.upButton.clicked.connect(self.move_jog)
		self.downButton.clicked.connect(self.move_jog)
		self.moverelButton.clicked.connect(self.move_rel)
		self.moveabsButton.clicked.connect(self.move_abs)
		self.moveButton.clicked.connect(self.move_to_val)
		self.stopButton.clicked.connect(self.move_stop)
		self.infoCalibButton.clicked.connect(self.showInfoCalibFiles)
		
		#self.move(0,175)
		#self.setWindowTitle('Zeiss spectrometer calibration')
		self.show()
		
		self.allButtons_torf(False)
		self.stopButton.setEnabled(False)
		self.bad_zaber_vals=False
		
		self.calib_mode="wavelength"
		self.set_lambda_calib_data()
		self.loadWaveCalibValues()

	##########################################
	
	def ZaberDialog(self):

		text, ok = QtGui.QInputDialog.getText(self, 'Serial Port Dialog','Enter Zaber stepper serial:', text=self.zaberport_str)
		if ok:
			self.zaberport_str = str(text)
	
	def loadCalibLambdaDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Load ref wavelength calib','Calib_files')
		old_calib=self.calibfile_lambda_str
		if fname:
			try:
				self.calibfile_lambda_str = str(fname)
				self.showInfoCalibFiles()
			except ValueError as e:
				self.calibfile_lambda_str = old_calib
				QtGui.QMessageBox.warning(self, 'Message', "Something is wrong with lambda calib file! Do you have a file with 2 columns, no headers, and all inputs are digits?")
				return
			if self.calib_mode=="wavelength":
				self.set_lambda_calib_data()
		
	def loadWaveDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Load wavelength vals for calib','Calib_files')
		if fname:
			self.lambda_str = str(fname)
		
		if self.calib_mode=="wavelength":
			self.loadWaveCalibValues()
	
	def loadWaveCalibValues(self):
	
		try:
			self.y_local=[]
			self.calibCounter=0
			with open(self.lambda_str, 'r') as thefile:
				for line in thefile:
					columns = line.split()
					self.y_local.extend([round(float(columns[0]),1)])
		except ValueError as e:
			QtGui.QMessageBox.warning(self, 'Message',"Something is wrong with the wavelength file! Do you have a wavelength file with 1 column, no headers, and all inputs are digits?")
			self.calibButton.setText('Adjust to ---- nm')
			self.calibButton.setEnabled(False)
			self.calibSaveButton.setEnabled(False)
		
		self.calibButton.setText(''.join(['Adjust to ',str(self.y_local[self.calibCounter]),' nm']))
		self.val_point=self.y_local[self.calibCounter]
		self.calibSaveButton.setText(''.join(['Save at ',str(self.val_point),' nm' ]))
		#self.calibCounter+=1
	
	
	
	
	def loadCalibSlitDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Load ref slit width calib','Calib_files')
		old_calib=self.calibfile_slit_str
		if fname:
			try:
				self.calibfile_slit_str = str(fname)
				self.showInfoCalibFiles()
			except ValueError as e:
				self.calibfile_slit_str = old_calib
				QtGui.QMessageBox.warning(self, 'Message', "Something is wrong with slit calib file! Do you have a file with 2 columns, no headers, and all inputs are digits?")
				return
			if self.calib_mode=="slit":
				self.set_slit_calib_data()
	
	def loadSlitDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Load slit width vals for calib','Calib_files')
		if fname:
			self.slit_str = str(fname)
		
		if self.calib_mode=="slit":
			self.loadSlitCalibValues()
		
	def loadSlitCalibValues(self):
	
		try:
			self.y_local=[]
			self.calibCounter=0
			with open(self.slit_str, 'r') as thefile:
				for line in thefile:
					columns = line.split()
					self.y_local.extend([round(float(columns[0]),2)])
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message',"Something is wrong with the slit width file! Do you have a slit width file with 1 column, no headers, and all inputs are digits?")
			self.calibButton.setText('Adjust to ---- mm')
			self.calibButton.setEnabled(False)
			self.calibSaveButton.setEnabled(False)
		
		self.calibButton.setText(''.join(['Adjust to ',str(self.y_local[self.calibCounter]),' mm']))
		self.val_point=self.y_local[self.calibCounter]
		self.calibSaveButton.setText(''.join(['Save at ',str(self.val_point),' mm' ]))
		#self.calibCounter+=1
	

	
	
	def showInfoCalibFiles(self):
		
		head, tail1 = os.path.split(self.calibfile_lambda_str)
		head, tail2 = os.path.split(self.calibfile_slit_str)
		
		x0=[]
		y0=[]
		with open(self.calibfile_lambda_str, 'r') as thefile:
			for line in thefile:
				columns = line.split()
				x0.extend([int(columns[0])]) #microstep pos.
				y0.extend([round(float(columns[1]),1)]) #wavelength
				
		x1=[]
		y1=[]
		with open(self.calibfile_slit_str, 'r') as thefile:
			for line in thefile:
				columns = line.split()
				x1.extend([int(columns[0])]) #microstep pos.
				y1.extend([round(float(columns[1]),2)]) #wavelength
		
		QtGui.QMessageBox.information(self, "Drive files information",''.join(["<font color=\"black\">Calib lambda: </font> <font color=\"green\">",tail1,"< </font> <br> <font color=\"black\">Calib lambda range: </font> <font color=\"green\">",str(y0[0])," to ",str(y0[-1])," nm < </font> <br> <font color=\"black\">Calib slit:< </font> <font color=\"blue\">",tail2,"<  </font> <br> <font color=\"black\">Calib slit range: </font> <font color=\"blue\">",str(y1[0])," to ",str(y1[-1])," mm <" ]))


	def set_connect(self):
		
		try:
			self.Za = ZaberXmcb_ascii.Zaber_Xmcb(self.zaberport_str)
		except Exception as e:
			QtGui.QMessageBox.warning(self, 'Message',"No response from the Zaber serial port! Check the serial port name and connections.")
			return

		# constants
		min_pos_lambda=self.Validrange_lambda[0]
		max_pos_lambda=self.Validrange_lambda[1]
		min_pos_slit=self.Validrange_slit[0]
		max_pos_slit=self.Validrange_slit[1]
		hc=25
		rc=50
		ms=2048
			
		try:
			self.Za.set_timeout(0.5)
			self.Za.set_Maximum_Position(1,1,max_pos_lambda)
			self.Za.set_Minimum_Position(1,1,min_pos_lambda)
			self.Za.set_Hold_Current(1,1,hc)
			self.Za.set_Running_Current(1,1,rc)
			self.Za.set_Max_Speed(1,1,ms)
			
			# Enable user to edit advanced settings
			#self.Za.set_System_Access(1,2) # OPEN ADVANCED
			#self.Za.set_Motor_Dir(1,2,1) # REVERSE motor direction
			#self.Za.set_System_Access(1,1) # CLOSE ADVANCED
			
			self.Za.set_Maximum_Position(1,2,max_pos_slit)
			self.Za.set_Minimum_Position(1,2,min_pos_slit)
			self.Za.set_Hold_Current(1,2,hc)
			self.Za.set_Running_Current(1,2,rc)
			self.Za.set_Max_Speed(1,2,ms)

			micstep=self.Za.return_Microstep_Resolution(1,1)
			sc=self.Za.return_System_Current(1)
			# TURN ON/OFF ALERTS
			if self.Za.return_Alert(1)==0:
				self.Za.set_Alert(1,1)
			
			self.Za.set_Current_Position(1,1,config_zeiss.Last_position_lambda[0])
			self.Za.set_Current_Position(1,2,config_zeiss.Last_position_slit[0])
			
		except Exception as e:
			self.Za.close()
			QtGui.QMessageBox.warning(self, 'Message',"No response from the Zaber stepper! Is stepper powered and connected to the serial?")
			return None
			
		
		hc_str=''.join([str(hc*25e-3)," / ",str(rc*25e-3)," Amps" ])
		print "Hold / Running current:", hc_str
		sys_str=''.join([ str(sc), " Amps" ])
		print "System current (0-5):", sys_str
		ms_str=''.join([str(ms/1.6384), " microsteps/s"])
		print "Max speed:", ms_str
		micstep_str=''.join([str(micstep), " microsteps/step"])
		print "Microstep resolution:", str(micstep_str)
		pos_lambda_str=''.join([str(min_pos_lambda)," to ", str(max_pos_lambda)," microsteps"])
		print "Stepper range for the wavelengths:", pos_lambda_str
		pos_slit_str=''.join([str(min_pos_slit)," to ", str(max_pos_slit)," microsteps"])
		print "Stepper range for the slits:", pos_slit_str
		
		self.allButtons_torf(True)
		self.stopButton.setEnabled(False)
		
		self.conMode.setEnabled(False)
		self.serialZaber.setEnabled(False)
		
		if self.calib_mode=="wavelength":
			self.set_lambda_calib_data()
		elif self.calib_mode=="slit":
			self.set_slit_calib_data()
		
		self.timer = QTimer(self)
		self.connect(self.timer, SIGNAL("timeout()"), self.set_disconnect)
		self.timer.setSingleShot(True)
		self.timer.start(1000*60*10)
		
		
	def set_disconnect(self):

		self.Za.set_Hold_Current(1,1,0)
		self.Za.set_Hold_Current(1,2,0)
		self.Za.close()
		
		self.allButtons_torf(False)
		self.conMode.setEnabled(True)
		
		
	def allButtons_torf(self,trueorfalse):
		
		
		self.calibWaveZeiss.setEnabled(trueorfalse)
		self.waveZeiss.setEnabled(trueorfalse)
		self.calibSlitZeiss.setEnabled(trueorfalse)
		self.slitZeiss.setEnabled(trueorfalse)
		
		self.disconMode.setEnabled(trueorfalse)
		self.calibButton.setEnabled(trueorfalse)
		self.alignEdit.setEnabled(trueorfalse)
		self.setzeroButton.setEnabled(trueorfalse)
		self.calibSaveButton.setEnabled(trueorfalse)
		self.cb3.setEnabled(trueorfalse)
		self.infoCalibButton.setEnabled(trueorfalse)
		#self.reorderButton.setEnabled(trueorfalse)
		
		self.filenameEdit.setEnabled(trueorfalse)
		self.folderEdit.setEnabled(trueorfalse)
		
		self.upButton.setEnabled(trueorfalse)
		self.downButton.setEnabled(trueorfalse)
		self.moverelButton.setEnabled(trueorfalse)
		self.moveabsButton.setEnabled(trueorfalse)
		self.moveButton.setEnabled(trueorfalse)
		self.moverelEdit.setEnabled(trueorfalse)
		self.moveabsEdit.setEnabled(trueorfalse)
		self.moveEdit.setEnabled(trueorfalse)
		#self.stopButton.setEnabled(trueorfalse)
	
	##########################################

	def set_bstyle_v1(self,button):
		
		button.setStyleSheet('QPushButton {font-size: 25pt}')
		button.setFixedWidth(40)
		button.setFixedHeight(40)
	
	def onActivated3(self, text):
		
		if str(text)=="wavelength":
			reply = QtGui.QMessageBox.question(self, 'Message', "Do you want to calibrate wavelengths stepper positions?", QtGui.QMessageBox.Yes |  QtGui.QMessageBox.No)
			if reply == QtGui.QMessageBox.Yes:
				self.calib_mode="wavelength"
				self.p0.setLabel('left', u'\u03bb', units='m')
				self.p1.setLabel('left', u'\u03bb', units='m')
				self.setzeroButton.setText("-> nm")
				self.moveButton.setText("Move to nm")
				self.all_pos=[config_zeiss.Last_position_lambda[0]]
				self.set_lambda_calib_data()
				self.loadWaveCalibValues()
				self.curve2.clear()
				self.set_save()
			else:
				self.cb3.setCurrentIndex(1)
			
		elif str(text)=="slit":
			reply = QtGui.QMessageBox.question(self, 'Message', "Do you want to calibrate slit widths stepper positions?", QtGui.QMessageBox.Yes |  QtGui.QMessageBox.No)
			if reply == QtGui.QMessageBox.Yes:
				self.calib_mode="slit"
				self.p0.setLabel('left', 'slit width', units='m')
				self.p1.setLabel('left', 'slit width', units='m')
				self.setzeroButton.setText("-> mm")
				self.moveButton.setText("Move to mm")
				self.all_pos=[config_zeiss.Last_position_slit[0]]
				self.set_slit_calib_data()
				self.loadSlitCalibValues()
				self.curve2.clear()
				self.set_save()
			else:
				self.cb3.setCurrentIndex(0)
		
		
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
			
		save_to_file=''.join([saveinfolder,saveinfile,".txt"])
		
		if not os.path.exists(save_to_file):
			print "Calib file created: ", save_to_file
			with open(save_to_file, 'w') as thefile:
				pass
			
		with open(save_to_file, 'r') as thefile:
			# read a list of lines into data
			data = thefile.readlines()
		
		if data and str(self.val_point) in data[-1]:
			if self.calib_mode=="wavelength":
				data[-1]=''.join([str(self.all_pos[-1]),'\t',str(self.val_point),'\n'])
			elif self.calib_mode=="slit":
				data[-1]=''.join([str(self.all_pos[-1]),'\t',str(self.val_point),'\n'])
			with open(save_to_file, 'w') as thefile:
				thefile.writelines(data)
		else:
			if self.calib_mode=="wavelength":
				with open(save_to_file, 'a') as thefile:
					thefile.write('%s' %self.all_pos[-1] )
					thefile.write('\t%s\n' %self.val_point)
			elif self.calib_mode=="slit":
				with open(save_to_file, 'a') as thefile:
					thefile.write('%s' %self.all_pos[-1] )
					thefile.write('\t%s\n' %self.val_point)
					
		# open calib file and plot
		x=[]
		y=[]
		with open(save_to_file, 'r') as thefile:
		  for line in thefile:
				columns = line.split()
				x.extend([int(columns[0])])
				if self.calib_mode=="wavelength":
					y.extend([round(float(columns[1]),1)])
				elif self.calib_mode=="slit":
					y.extend([round(float(columns[1]),2)])
		
		if self.calib_mode=="wavelength":
			self.curve2.setData(x,numpy.array(y)/1.0e9)
		elif self.calib_mode=="slit":
			self.curve2.setData(x,numpy.array(y)/1.0e3) 
		#self.reorderButton.setEnabled(True)
	
	def update_calib_button(self):
		
		if self.calib_mode=="wavelength":
			if len(self.y_local)-1>self.calibCounter:
				self.val_point=self.y_local[self.calibCounter]
				self.calibSaveButton.setText(''.join(['Save at ',str(self.val_point),' nm' ]))
				
				self.calibCounter+=1
				self.calibButton.setText(''.join(['Adjust to ',str(self.y_local[self.calibCounter]),' nm']))
			else:
				self.val_point=self.y_local[self.calibCounter]
				self.calibSaveButton.setText(''.join(['Save at ',str(self.val_point),' nm' ]))
				
				self.calibCounter=0
				self.calibButton.setText(''.join(['Adjust to ',str(self.y_local[self.calibCounter]),' nm']))
				
		elif self.calib_mode=="slit":
			if len(self.y_local)-1>self.calibCounter:
				self.val_point=self.y_local[self.calibCounter]
				self.calibSaveButton.setText(''.join(['Save at ',str(self.val_point),' mm' ]))
				
				self.calibCounter+=1
				self.calibButton.setText(''.join(['Adjust to ',str(self.y_local[self.calibCounter]),' mm']))
			else:
				self.val_point=self.y_local[self.calibCounter]
				self.calibSaveButton.setText(''.join(['Save at ',str(self.val_point),' mm' ]))
				
				self.calibCounter=0
				self.calibButton.setText(''.join(['Adjust to ',str(self.y_local[self.calibCounter]),' mm']))
			
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
		
	def set_lambda_calib_data(self):
		
		try:
			x=[]
			y=[]
			with open(self.calibfile_lambda_str, 'r') as thefile:
				for line in thefile:
					columns = line.split()
					x.extend([int(columns[0])])
					y.extend([round(float(columns[1]),1)])
		except ValueError as e:
			QtGui.QMessageBox.warning(self, 'Message',"Something is wrong with the ref calib file! Do you have a ref Calib file with 2 columns, no headers, and all inputs are numbers?")
			return
		
		self.min_y_calib=min(y)
		self.max_y_calib=max(y)
		if min(x)<self.Validrange_lambda[0] or max(x)>self.Validrange_lambda[1]:
			QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid wavelength stepper range is from ',str(self.Validrange_lambda[0]),' to ',str(self.Validrange_lambda[1]),' microsteps.' ]) )
			return 
		
		self.curve0_1.setData(x,numpy.array(y)/1.0e9) 
		
		wv_fine=numpy.arange(y[0],y[-1]+0.1,0.1)
		#spline
		wv_curve=scipy.interpolate.splrep(y, x, k=3, s=0)
		#linear
		#wv_curve = scipy.interpolate.splrep(y, x, k=1, s=0)		
		positions_fine = scipy.interpolate.splev(wv_fine, wv_curve, der=0)
		self.curve0_2.setData(positions_fine,numpy.array(wv_fine)/1.0e9)
		
		my_pos = self.all_pos[-1]
		if my_pos<min(x) or my_pos>max(x):
			QtGui.QMessageBox.warning(self, 'Message', "Current wavelength position is outside range of the calibration lambda file!")
			self.lcd1.display('-')
			self.lcd2.display('-')
		else:
			# Update the LCD display lcd2 with the wavelength which
			# corresponds to the saved Zaber microposition
			wv_curve2=scipy.interpolate.splrep(x, y, k=3, s=0)
			first_pos_val = round(scipy.interpolate.splev(my_pos, wv_curve2, der=0), 1)
			
			lcd_obj=type('lcd_obj',(object,),{'min_pos':my_pos, 'pos_val':first_pos_val})
			self.more_tals(lcd_obj)
			
			self.replace_line("config_zeiss.py",4,''.join(["Last_position_lambda=[",str(my_pos),",",str(first_pos_val),"]\n"]))
			imp.reload(config_zeiss)
	
	
	def set_slit_calib_data(self):
		
		try:
			x=[]
			y=[]
			with open(self.calibfile_slit_str, 'r') as thefile:
				for line in thefile:
					columns = line.split()
					x.extend([int(columns[0])])
					y.extend([round(float(columns[1]),2)])
		except ValueError as e:
			QtGui.QMessageBox.warning(self, 'Message',"Something is wrong with the ref calib file! Do you have a ref Calib file with 2 columns, no headers, and all inputs are numbers?")
			return
			
		self.min_y_calib=min(y)
		self.max_y_calib=max(y)
		if min(x)<self.Validrange_slit[0] or max(x)>self.Validrange_slit[1]:
			QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid slit stepper range is from ',str(self.Validrange_slit[0]),' to ',str(self.Validrange_slit[1]),' microsteps.' ]) )
			return
		
		self.curve0_1.setData(x,numpy.array(y)/1.0e3) 
		
		slit_fine=numpy.arange(y[0],y[-1]+0.01,0.01)
		#spline
		slit_curve=scipy.interpolate.splrep(y, x, k=3, s=0)
		#linear
		#slit_curve = scipy.interpolate.splrep(y, x, k=1, s=0)		
		positions_fine = scipy.interpolate.splev(slit_fine, slit_curve, der=0)
		self.curve0_2.setData(positions_fine,numpy.array(slit_fine)/1.0e3)
		
		my_pos = self.all_pos[-1]
		if my_pos<min(x) or my_pos>max(x):
			QtGui.QMessageBox.warning(self, 'Message', "Current slit position is outside range of the calibration slit file!")
			self.lcd1.display('-')
			self.lcd2.display('-')
		else:
			# Update the LCD display lcd2 with the wavelength which
			# corresponds to the saved Zaber microposition
			wv_curve2=scipy.interpolate.splrep(x, y, k=3, s=0)
			first_pos_val = round(scipy.interpolate.splev(my_pos, wv_curve2, der=0), 2)
			
			lcd_obj=type('lcd_obj',(object,),{'min_pos':my_pos, 'pos_val':first_pos_val})
			self.more_tals(lcd_obj)
			
			self.replace_line("config_zeiss.py",5,''.join(["Last_position_slit=[",str(my_pos),",",str(first_pos_val),"]\n"]))
			imp.reload(config_zeiss)
	
	
	
	
	
	
	def move_stop(self):
		
		self.get_zaber_Thread.abort_move()

	def set_zero(self):
		
		if self.calib_mode=="wavelength":
			try:
				move_num=round(float(self.alignEdit.text()),1)
			except ValueError as e:
				QtGui.QMessageBox.warning(self, 'Message', "Only real decimal numbers are accepted as a wavelength!")
				return
			
			if move_num<self.min_y_calib or move_num>self.max_y_calib:
				QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid wavelength range is from ',str(self.min_y_calib),' nm to ',str(self.max_y_calib),' nm.' ]) )
				return
			else:
				self.timer.stop()
				sender = self.sender()
				self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.calib_mode,self.calibfile_lambda_str,move_num)
				
		elif self.calib_mode=="slit":
			try:
				move_num=round(float(self.alignEdit.text()),2)
			except ValueError as e:
				QtGui.QMessageBox.warning(self, 'Message', "Only real decimal numbers are accepted as a slit width!")
				return
			
			if move_num<self.min_y_calib or move_num>self.max_y_calib:
				QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid slit range is from ',str(self.min_y_calib),' mm to ',str(self.max_y_calib),' mm.' ]) )
				return
			else:
				self.timer.stop()
				sender = self.sender()
				self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.calib_mode,self.calibfile_slit_str,move_num)
		
		self.connect(self.get_zaber_Thread,SIGNAL("more_tals(PyQt_PyObject)"),self.more_tals)
		self.connect(self.get_zaber_Thread,SIGNAL('bad_zaber_val(PyQt_PyObject)'), self.bad_zaber_val)
		self.connect(self.get_zaber_Thread,SIGNAL('finished()'), self.set_finished)

		self.get_zaber_Thread.start()
	
	def move_to_val(self):
		
		if self.calib_mode=="wavelength":
			try:
				move_num=round(float(self.moveEdit.text()),1)
			except ValueError as e:
				QtGui.QMessageBox.warning(self, 'Message', "Only real decimal numbers are accepted as a wavelength!")
				return
			
			if move_num<self.min_y_calib or move_num>self.max_y_calib:
				QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid wavelength range is from ',str(self.min_y_calib),' nm to ',str(self.max_y_calib),' nm.' ]) )
				return
			else:
				self.timer.stop()
				sender = self.sender()
				self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.calib_mode,self.calibfile_lambda_str,move_num)
			
		elif self.calib_mode=="slit":
			try:
				move_num=round(float(self.moveEdit.text()),2)
			except ValueError as e:
				QtGui.QMessageBox.warning(self, 'Message', "Only real decimal numbers are accepted as a slit width!")
				return
			
			if move_num<self.min_y_calib or move_num>self.max_y_calib:
				QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid slit width range is from ',str(self.min_y_calib),' mm to ',str(self.max_y_calib),' mm.' ]) )
				return
			else:
				self.timer.stop()
				sender = self.sender()
				self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.calib_mode,self.calibfile_slit_str,move_num)
				
		self.allButtons_torf(False)
		self.stopButton.setEnabled(True)
		
		self.connect(self.get_zaber_Thread,SIGNAL("more_tals(PyQt_PyObject)"),self.more_tals)
		self.connect(self.get_zaber_Thread,SIGNAL('bad_zaber_val(PyQt_PyObject)'), self.bad_zaber_val)
		self.connect(self.get_zaber_Thread,SIGNAL('finished()'), self.set_finished)
		
		self.get_zaber_Thread.start()
		
	def move_to_val2(self):
		
		if self.calib_mode=="wavelength":
			move_num = round(self.y_local[self.calibCounter],1)
			
			self.timer.stop()
			sender = self.sender()
			self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.calib_mode,self.calibfile_lambda_str,move_num)
			
		elif self.calib_mode=="slit":
			move_num = round(self.y_local[self.calibCounter],2)
			
			self.timer.stop()
			sender = self.sender()
			self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.calib_mode,self.calibfile_slit_str,move_num)
		
		print move_num
		self.allButtons_torf(False)
		self.stopButton.setEnabled(True)
		
		self.connect(self.get_zaber_Thread,SIGNAL("more_tals(PyQt_PyObject)"),self.more_tals)
		self.connect(self.get_zaber_Thread,SIGNAL('bad_zaber_val(PyQt_PyObject)'), self.bad_zaber_val)
		self.connect(self.get_zaber_Thread,SIGNAL('finished()'), self.set_finished)
		
		self.get_zaber_Thread.start()
		
	def move_rel(self):
		
		move_num = int(self.moverelEdit.text())
		if self.calib_mode=="wavelength":
			move_tot = move_num+self.all_pos[-1]
			if move_tot<self.Validrange_lambda[0] or move_tot>self.Validrange_lambda[1]:
				QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid wavelength stepper range is from ',str(self.Validrange_lambda[0]),' to ',str(self.Validrange_lambda[1]),' microsteps.' ]) )
				return
			else:
				self.timer.stop()
				sender = self.sender()
				self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.calib_mode,self.calibfile_lambda_str,move_num)
				
		elif self.calib_mode=="slit":
			move_tot = move_num+self.all_pos[-1]
			if move_tot<self.Validrange_slit[0] or move_tot>self.Validrange_slit[1]:
				QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid slit width stepper range is from ',str(self.Validrange_slit[0]),' to ',str(self.Validrange_slit[1]),' microsteps.' ]) )
				return
			else:
				self.timer.stop()
				sender = self.sender()
				self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.calib_mode,self.calibfile_slit_str,move_num)
				
		self.allButtons_torf(False)
		self.stopButton.setEnabled(True)
		
		self.connect(self.get_zaber_Thread,SIGNAL("more_tals(PyQt_PyObject)"),self.more_tals)
		self.connect(self.get_zaber_Thread,SIGNAL('bad_zaber_val(PyQt_PyObject)'), self.bad_zaber_val)
		self.connect(self.get_zaber_Thread,SIGNAL('finished()'), self.set_finished)
		
		self.get_zaber_Thread.start()
		
	def move_abs(self):
		
		move_num = int(self.moveabsEdit.text())
		if self.calib_mode=="wavelength":
			if move_num<self.Validrange_lambda[0] or move_num>self.Validrange_lambda[1]:
				QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid wavelength stepper range is from ',str(self.Validrange_lambda[0]),' to ',str(self.Validrange_lambda[1]),' microsteps.' ]) )
				return 
			else:
				self.timer.stop()
				sender = self.sender()
				self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.calib_mode,self.calibfile_lambda_str,move_num)
				
		elif self.calib_mode=="slit":
			if move_num<self.Validrange_slit[0] or move_num>self.Validrange_slit[1]:
				QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid slit stepper range is from ',str(self.Validrange_slit[0]),' to ',str(self.Validrange_slit[1]),' microsteps.' ]) )
				return
			else:
				self.timer.stop()
				sender = self.sender()
				self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.calib_mode,self.calibfile_slit_str,move_num)
		
		self.allButtons_torf(False)
		self.stopButton.setEnabled(True)
		
		self.connect(self.get_zaber_Thread,SIGNAL("more_tals(PyQt_PyObject)"),self.more_tals)
		self.connect(self.get_zaber_Thread,SIGNAL('bad_zaber_val(PyQt_PyObject)'), self.bad_zaber_val)
		self.connect(self.get_zaber_Thread,SIGNAL('finished()'), self.set_finished)
				
		self.get_zaber_Thread.start()
		
	def move_jog(self):
		
		sender = self.sender()
		if sender.text()==u'\u25b2':
			move_num=10
		elif sender.text()==u'\u25bc':
			move_num=-10
		
		######################################
		if self.calib_mode=="wavelength":
			# update the lcd motorstep position
			validrange_min, validrange_max=self.Validrange_lambda
			move_tot = move_num+self.all_pos[-1]
			if move_tot<validrange_min or move_tot>validrange_max:
				QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid range is from ',str(validrange_min),' to ',str(validrange_max),' microsteps.' ]) )
				return 
			else:
				self.timer.stop()
				self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.calib_mode,self.calibfile_lambda_str)

		if self.calib_mode=="slit":
			# update the lcd motorstep position
			validrange_min, validrange_max=self.Validrange_slit
			move_tot = move_num+self.all_pos[-1]
			if move_tot<validrange_min or move_tot>validrange_max:
				QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid range is from ',str(validrange_min),' to ',str(validrange_max),' microsteps.' ]) )
				return 
			else:
				self.timer.stop()
				self.get_zaber_Thread=zaber_Thread(sender.text(),self.Za,self.calib_mode,self.calibfile_slit_str)
				
		self.connect(self.get_zaber_Thread,SIGNAL("more_tals(PyQt_PyObject)"),self.more_tals)
		self.connect(self.get_zaber_Thread,SIGNAL('bad_zaber_val(PyQt_PyObject)'), self.bad_zaber_val)
		self.connect(self.get_zaber_Thread,SIGNAL('finished()'), self.set_finished)
		
		self.get_zaber_Thread.start()
		
		
	def more_tals(self,more_tals_obj):
		
		self.all_pos.extend([ int(more_tals_obj.min_pos) ])
		
		self.lcd1.display(str(more_tals_obj.min_pos))
		self.lcd2.display(str(more_tals_obj.pos_val))
			
			
	def bad_zaber_val(self,pyqt_object):
		
		self.bad_zaber_vals=pyqt_object
	
	
	def set_finished(self):
		
		if self.bad_zaber_vals==serial.SerialException:
			QtGui.QMessageBox.warning(self, 'Message',"Zaber serial severed. Closing the program..." )
			sys.exit()
			
		self.stopButton.setEnabled(False)
		
		if self.bad_zaber_vals==ValueError:
			QtGui.QMessageBox.warning(self, 'Message',"Zaber getting bad values. Closing the serial..." )
			self.bad_zaber_vals=False
			self.set_disconnect()
			return
		
		self.allButtons_torf(True)
		self.timer.start(1000*60*10)
		
	
	def closeEvent(self, event):

		if hasattr(self, 'Za'):
			reply = QtGui.QMessageBox.question(self, 'Message', "Quit calibration now? The microstep position will be saved and the stepper hold current will be set to zero!", QtGui.QMessageBox.Yes |  QtGui.QMessageBox.No)
		else:
			reply = QtGui.QMessageBox.question(self, 'Message', "Quit calibration now?", QtGui.QMessageBox.Yes |  QtGui.QMessageBox.No)
			
		
		if reply==QtGui.QMessageBox.Yes:
			
			if hasattr(self, 'Za'):
				if not hasattr(self, 'get_zaber_Thread'):
					if self.Za.is_open():
						self.Za.set_Hold_Current(1,1,0)
						self.Za.set_Hold_Current(1,2,0)
						self.Za.close()
				else:
					if self.get_zaber_Thread.isRunning():
						QtGui.QMessageBox.warning(self, 'Message', "Calibration in progress. Cancel the move then quit!")
						event.ignore()
						return
					else:
						if self.Za.is_open():
							self.Za.set_Hold_Current(1,1,0)
							self.Za.set_Hold_Current(1,2,0)
							self.Za.close()
							
			if hasattr(self, 'timer'):
				if self.timer.isActive():
					self.timer.stop()
					
			event.accept()
			
		else:
			event.ignore()
			
			
			
	def set_save_plots(self):
		
		if str(self.folderEdit.text()):
			if not os.path.isdir(str(self.folderEdit.text())):
				os.mkdir(str(self.folderEdit.text()))
			saveinfolder=''.join([str(self.folderEdit.text()),"/"])
		else:
			saveinfolder=""
		
		save_pic_to_file=''.join([saveinfolder,self.timestr,'.png'])
		# create an exporter instance, as an argument give it
		# the item you wish to export
		exporter = pg.exporters.ImageExporter(self.p0.scene())
		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_pic_to_file)
		
		
	def set_save(self):
		
		self.timestr=time.strftime("%y%m%d-%H%M")
		
		self.replace_line("config_zeiss.py",4, ''.join(["Last_position_lambda=",str(config_zeiss.Last_position_lambda),"\n"]) )
		self.replace_line("config_zeiss.py",5, ''.join(["Last_position_slit=",str(config_zeiss.Last_position_slit),"\n"]) )
		
		self.replace_line("config_zeiss.py",7, ''.join(["calibfile_lambda=\"",self.calibfile_lambda_str,"\"\n"]) )
		self.replace_line("config_zeiss.py",8, ''.join(["calibfile_slit=\"",self.calibfile_slit_str,"\"\n"]) )
		self.replace_line("config_zeiss.py",9, ''.join(["lambdafile=\"",self.lambda_str,"\"\n"]) )
		self.replace_line("config_zeiss.py",10, ''.join(["slitfile=\"",self.slit_str,"\"\n"]) )
		self.replace_line("config_zeiss.py",11, ''.join(["calib_lambda_filename=\"",str(self.filenameEdit.text()),"\"\n"]) )
		self.replace_line("config_zeiss.py",12, ''.join(["calib_lambda_foldername=\"",str(self.folderEdit.text()),"\"\n"]) )
		self.replace_line("config_zeiss.py",13, ''.join(["calib_slit_filename=\"",str(self.filenameEdit.text()),"\"\n"]) )
		self.replace_line("config_zeiss.py",14, ''.join(["calib_slit_foldername=\"",str(self.folderEdit.text()),"\"\n"]) )
		
		self.replace_line("config_zeiss.py",17, ''.join(["timestr=\"",self.timestr,"\"\n"]) )
		self.replace_line("config_zeiss.py",18, ''.join(["zaberport=\"",self.zaberport_str,"\"\n"]) )
		self.replace_line("config_zeiss.py",19, ''.join(["sr510port=\"",self.sr510port_str,"\"\n"]) )
		
		self.lcd3.display(self.timestr)
		imp.reload(config_zeiss)
		
		
	def replace_line(self,file_name, line_num, text):
		
		lines = open(file_name, 'r').readlines()
		lines[line_num] = text
		out = open(file_name, 'w')
		out.writelines(lines)
		out.close()
	
	

def main():
  
	app=QtGui.QApplication(sys.argv)
	ex=Run_gui()
	#sys.exit(app.exec_())

	# avoid message 'Segmentation fault (core dumped)' with app.deleteLater()
	app.exec_()
	app.deleteLater()
	sys.exit()
    
if __name__=='__main__':
	
	main()
  
