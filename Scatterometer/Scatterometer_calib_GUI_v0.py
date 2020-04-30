import os, sys, serial, time, Scatterometer_funksjoner_ver2
import numpy, functools
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.exporters
#from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, SIGNAL
import config_calib, ESP300, MOTORSTEP_DRIVE

class my_Thread(QThread):
    
	def __init__(self, *argv):
		QThread.__init__(self)
		
		self.end_flag=False
		
		self.sender=argv[0]
		self.Esp=argv[1]
		self.Md=argv[2]
		self.rot_axs=argv[3]
		self.B_rotwh=argv[4]
		self.PSG_colms=argv[5]
		self.PSA_rows=argv[6]
		self.Rows=argv[7]
		self.Colms=argv[8]
		self.analog_pin=argv[9]
		self.avg_pts=argv[10]
		self.dwell=argv[11]
	
	def __del__(self):
	  
	  self.wait()

	def abort_move(self):
		
		self.end_flag=True
		#self.Esp.set_stop()
		
	def run(self):
		
		if self.sender[0:2]=="B[":
			B_matr = numpy.zeros((4,4))
			self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),self.rot_axs,'red')
			self.emit(SIGNAL('clear_graphs_from_thread(PyQt_PyObject)'),self.rot_axs)
			min_pos=self.Esp.move_abspos(0+1,self.B_rotwh[self.rot_axs])
			self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), 0, min_pos)
			time_start=time.time()
			for i,j in zip(self.Rows,self.Colms):
				if self.end_flag==True:
					break
				min_pos=self.Esp.move_abspos(1+1,self.PSA_rows[i])
				self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), 1, min_pos)
				min_pos=self.Esp.move_abspos(2+1,self.PSG_colms[j])
				self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), 2, min_pos)
				
				time_s=time.time()
				while (time.time()-time_s)<self.dwell/1000.0:
					ard_volt=self.Md.read_analog(self.analog_pin,self.avg_pts)
					time_elap=time.time()-time_start					
					self.emit(SIGNAL('volt_data(PyQt_PyObject,PyQt_PyObject)'), time_elap,ard_volt)
					
				B_matr[i,j]=ard_volt
				self.emit(SIGNAL('update_B(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),self.rot_axs,i,j,ard_volt)
				self.emit(SIGNAL('more_tals(PyQt_PyObject,PyQt_PyObject)'),time_elap,ard_volt)
			self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),self.rot_axs,'black')
			
			if self.rot_axs==0:
				condB0 = numpy.linalg.cond(B_matr)
				self.emit(SIGNAL('update_condB0(PyQt_PyObject)'),condB0)
			
		elif self.sender=="All B":
			B_matr = numpy.zeros((4,4,4))
			time_start=time.time()
			for rot_axs in range(4):
				self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),rot_axs,'AllBred')
				self.emit(SIGNAL('clear_graphs_from_thread(PyQt_PyObject)'),rot_axs)
				min_pos=self.Esp.move_abspos(0+1,self.B_rotwh[rot_axs])
				self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), 0, min_pos)
				for i,j in zip(self.Rows,self.Colms):
					if self.end_flag==True:
						break
					min_pos=self.Esp.move_abspos(1+1,self.PSA_rows[i])
					self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), 1, min_pos)
					min_pos=self.Esp.move_abspos(2+1,self.PSG_colms[j])
					self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), 2, min_pos)
					
					time_s=time.time()
					while (time.time()-time_s)<self.dwell/1000.0:
						ard_volt=self.Md.read_analog(self.analog_pin,self.avg_pts)
						time_elap=time.time()-time_start						
						self.emit(SIGNAL('volt_data(PyQt_PyObject,PyQt_PyObject)'), time_elap,ard_volt)

					B_matr[rot_axs,i,j]=ard_volt
					self.emit(SIGNAL('update_B(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),rot_axs,i,j,ard_volt)
					self.emit(SIGNAL('more_tals(PyQt_PyObject,PyQt_PyObject)'),time_elap,ard_volt)
				self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),rot_axs,'SomeBblue')
				
				if rot_axs==0:
					condB0 = numpy.linalg.cond(B_matr[0,:,:])
					self.emit(SIGNAL('update_condB0(PyQt_PyObject)'),condB0)
				
				if self.end_flag==True:
					break
				
			self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),rot_axs,'AllBblack')
			
		else:
			pass



class my_Thread_homeAll(QThread):
    
	def __init__(self, *argv):
		QThread.__init__(self)
		
		self.Esp=argv[0]
		
	def __del__(self):
	  
	  self.wait()
	
	def run(self):
		
		self.Esp.set_motors("on")
		
		for axs in range(3):
			self.Esp.go_home(axs+1)
			pos=self.Esp.return_pos(axs+1)
			self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), axs, pos)


		
class run_zaber_gui(QtGui.QWidget):
  
	def __init__(self):
		super(run_zaber_gui, self).__init__()
		
		#####################################################
		
		# constants
		self.analog_pin=config_calib.Analog_pin
		self.shutter_pin=config_calib.Shutter_pin
		self.avg_pts=config_calib.Avgpts
		self.shutter_dwell=config_calib.Shutter_dwell
		self.dwell=config_calib.Dwell
		self.B_rotwh=config_calib.B_rotwh
		self.PSG_colms=config_calib.PSG_colms
		self.PSA_rows=config_calib.PSA_rows
		self.Rows=config_calib.Rows
		self.Colms=config_calib.Colms
		self.Theta0=config_calib.Theta0
		self.Minpos=config_calib.Minpos
		self.Maxpos=config_calib.Maxpos
		self.timestr = config_calib.timestr
		self.filename_str = config_calib.filename
		self.folder_str = config_calib.create_folder	
		self.ardport_str = config_calib.ardport
		self.espport_str = config_calib.espport
	
		self.initUI()
    
	def initUI(self):

		# status info which button has been pressed
		Bcalib_lbl = QtGui.QLabel("CALIBRATION", self)
		Bcalib_lbl.setStyleSheet("color: blue")
		self.Bcalib_Button = [None for i in range(4)]
		
		self.B_lbl=[None for i in range(4)]
		self.B=numpy.zeros((4,4,4),dtype=object)
		
		self.lcd = [None for i in range(3)]
		lcd_lbl = [None for i in range(3)]
		for i in range(3):
			if i==0:
				lcd_lbl[i] = QtGui.QLabel(''.join(["Wheel (Ax 1)"]), self)
			if i==1:
				lcd_lbl[i] = QtGui.QLabel(''.join(["PSG (Ax 2)"]), self) 
			if i==2:
				lcd_lbl[i] = QtGui.QLabel(''.join(["PSA (Ax 3)"]), self)
			self.lcd[i] = QtGui.QLCDNumber(self)
			self.lcd[i].setStyleSheet("color: black")
			#self.set_lcd_style(self.lcd[i])
			self.lcd[i].setSegmentStyle(QtGui.QLCDNumber.Flat)
			self.lcd[i].setNumDigits(7)
			self.lcd[i].display('-------')
			self.lcd[i].setFixedWidth(95)
			self.lcd[i].setFixedHeight(40)
		
		shutter_dwell_lbl = QtGui.QLabel("Shutter dwell [s]", self)
		self.combo3 = QtGui.QComboBox(self)
		mylist3=["1","2","5","10","20","60"]
		self.combo3.addItems(mylist3)
		self.combo3.setCurrentIndex(mylist3.index(str(self.shutter_dwell)))
		
		dwell_lbl = QtGui.QLabel("PSG/PSA dwell [ms]", self)
		self.combo2 = QtGui.QComboBox(self)
		mylist2=["500","1000","1500","2000","2500","3000","3500","4000"]
		self.combo2.addItems(mylist2)
		self.combo2.setCurrentIndex(mylist2.index(str(self.dwell)))
		
		####################################################
		self.Bcalib_all_Button = QtGui.QPushButton("All B",self)
		self.Bcalib_all_Button.setStyleSheet("color: black")
		self.Bcalib_all_Button.setFixedWidth(50)
		
		self.Bcalib_stop_Button = QtGui.QPushButton("STOP",self)
		self.Bcalib_stop_Button.setStyleSheet("color: black")
		self.Bcalib_stop_Button.setFixedWidth(50)
		self.Bcalib_stop_Button.setEnabled(False)	
		
		for i in range(4):
			
			self.Bcalib_Button[i] = QtGui.QPushButton(''.join(["B[",str(i),"]"]),self)
			self.Bcalib_Button[i].setStyleSheet("color: black")
			self.Bcalib_Button[i].setFixedWidth(40)
			self.B_lbl[i] = QtGui.QLabel(''.join(["B[",str(i),"]"]), self)	
			self.B_lbl[i].setStyleSheet("color: blue")
			
			#self.moveabsButton.setStyleSheet('QPushButton {color: red}')
			for j in range(4):
				for k in range(4):
					self.B[i,j,k] = QtGui.QLineEdit("--",self)
					self.B[i,j,k].setFixedWidth(50)
					self.B[i,j,k].setEnabled(False)
		
		####################################################
		
		calcul_lbl = QtGui.QLabel("CALCULATE calib params", self)	
		calcul_lbl.setStyleSheet("color: blue")		
		theta0_lbl = QtGui.QLabel("Theta init", self)
		theta_opt_lbl = QtGui.QLabel("Theta opt", self)
		self.theta0Edit = [None for i in range(3)]
		self.theta_optEdit = [None for i in range(3)]
		for i in range(3):
			self.theta0Edit[i] = QtGui.QLineEdit(str(self.Theta0[i]),self)
			self.theta_optEdit[i] = QtGui.QLineEdit("--",self)
			self.theta_optEdit[i].setEnabled(False)
		
		cond_lbl = QtGui.QLabel("Cond B0,A,W", self)
		self.condEdit = [None for i in range(3)]
		for i in range(3):
			self.condEdit[i]=QtGui.QLineEdit("--",self)
			self.condEdit[i].setEnabled(False)
		
		self.Calc_Button = QtGui.QPushButton("Calc calib params",self)
		self.Calc_Button.setStyleSheet("color: black")
		self.Save_calc_Button = QtGui.QPushButton("Save calib params",self)
		self.Save_calc_Button.setStyleSheet("color: black")
				
		####################################################
		
		store_lbl = QtGui.QLabel("STORAGE filename and location", self)
		store_lbl.setStyleSheet("color: blue")
		filename = QtGui.QLabel("Save to file",self)
		foldername = QtGui.QLabel("Save to folder",self)
		self.filenameEdit = QtGui.QLineEdit(self.filename_str,self)
		self.folderEdit = QtGui.QLineEdit(self.folder_str,self)
		
		####################################################
		
		ard_lbl = QtGui.QLabel("ANALOG/DIGITAL settings", self)
		ard_lbl.setStyleSheet("color: blue")
			
		analog_pin_lbl = QtGui.QLabel("Analog pin no.", self)
		self.combo0 = QtGui.QComboBox(self)
		mylist0=["0","1","2","3"]
		self.combo0.addItems(mylist0)
		self.combo0.setCurrentIndex(mylist0.index(str(self.analog_pin)))
		
		shutter_pin_lbl = QtGui.QLabel("Shutter pin no.", self)
		self.combo4 = QtGui.QComboBox(self)
		mylist4=["45","46","47","48"]
		self.combo4.addItems(mylist4)
		self.combo4.setCurrentIndex(mylist4.index(str(self.shutter_pin)))
		
		avgpts_lbl = QtGui.QLabel("Averaging points", self)
		self.combo1 = QtGui.QComboBox(self)
		mylist1=["5","20","100","200","500","1000","2000"]
		self.combo1.addItems(mylist1)
		self.combo1.setCurrentIndex(mylist1.index(str(self.avg_pts)))

		##############################################

		# status info which button has been pressed
		et_lbl = QtGui.QLabel("TIME trace for storing the plot", self)
		et_lbl.setStyleSheet("color: blue")
		
		self.lcd1 = QtGui.QLCDNumber(self)
		self.lcd1.setStyleSheet("color: red")
		self.lcd1.setFixedHeight(60)
		self.lcd1.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd1.setNumDigits(11)
		self.lcd1.display(self.timestr)

		################### MENU BARS START ##################
		
		MyBar = QtGui.QMenuBar(self)
		fileMenu = MyBar.addMenu("File")
		fileSaveSet = fileMenu.addAction("Save settings")
		fileSaveSet.triggered.connect(self.set_save)
		fileSaveSet.setShortcut('Ctrl+S')
		fileSavePlt = fileMenu.addAction("Save plot")
		fileSavePlt.triggered.connect(self.set_save_plot)
		fileSavePlt.setShortcut('Ctrl+P')
		self.fileClose = fileMenu.addAction("Close")        
		self.fileClose.triggered.connect(self.close) # triggers closeEvent()
		self.fileClose.setShortcut('Ctrl+X')
		
		serialMenu = MyBar.addMenu("Serial")
		self.conSerial = serialMenu.addAction("Connect to serial")
		self.conSerial.triggered.connect(self.set_connect_serial)
		self.disconSerial = serialMenu.addAction("Disconnect from serial")
		self.disconSerial.triggered.connect(self.set_disconnect_serial)
		##
		self.serialArd = serialMenu.addAction("Serial Arduino port")
		self.serialArd.triggered.connect(self.ArdDialog)
		self.serialEsp = serialMenu.addAction("Serial ESP port")
		self.serialEsp.triggered.connect(self.EspDialog)
		
		self.modeMenu = MyBar.addMenu("ESP300")
		self.homeAll = self.modeMenu.addAction(''.join(["Home all axis"]))
		self.homeAll.triggered.connect(self.go_homeAllAxes)
		
		################### MENU BARS END ##################
		
		g0_0=QtGui.QGridLayout()
		g0_0.addWidget(MyBar,0,0)
		v0 = QtGui.QVBoxLayout()
		v0.addLayout(g0_0)
		
		g4_0 = QtGui.QGridLayout()
		g4_0.addWidget(Bcalib_lbl,0,0)
		g4_1 = QtGui.QGridLayout()
		for i in range(4):
			g4_1.addWidget(self.Bcalib_Button[i],0,i)
		g4_1.addWidget(self.Bcalib_all_Button,0,i+1)
		g4_1.addWidget(self.Bcalib_stop_Button,0,i+2)
		v4 = QtGui.QVBoxLayout()
		v4.addLayout(g4_0)
		v4.addLayout(g4_1)
		
		g5_0 = QtGui.QGridLayout()
		for i in range(3):
			g5_0.addWidget(lcd_lbl[i],0,i)
			g5_0.addWidget(self.lcd[i],1,i)
		
		g7_0 = QtGui.QGridLayout()
		g7_0.addWidget(shutter_dwell_lbl,0,0)
		g7_0.addWidget(self.combo3,0,1)
		g7_0.addWidget(dwell_lbl,1,0)
		g7_0.addWidget(self.combo2,1,1)
		
		g6_0 = QtGui.QGridLayout()
		g6_0.addWidget(calcul_lbl,0,0)
		g6_1 = QtGui.QGridLayout()
		g6_1.addWidget(theta0_lbl,0,0)
		for i in range(3):
			g6_1.addWidget(self.theta0Edit[i],0,i+1)
		g6_1.addWidget(theta_opt_lbl,1,0)
		for i in range(3):
			g6_1.addWidget(self.theta_optEdit[i],1,i+1)
		g6_1.addWidget(cond_lbl,2,0)
		for i in range(3):
			g6_1.addWidget(self.condEdit[i],2,i+1)
		g6_2 = QtGui.QGridLayout()
		g6_2.addWidget(self.Calc_Button,0,0)
		g6_2.addWidget(self.Save_calc_Button,0,1)
		v6 = QtGui.QVBoxLayout()
		v6.addLayout(g6_0)
		v6.addLayout(g6_1)
		v6.addLayout(g6_2)

		g_0 = [ QtGui.QSplitter(QtCore.Qt.Vertical) for i in range(4)]		
		g_1h= [[QtGui.QSplitter(QtCore.Qt.Horizontal) for i in range(4)] for j in range(4)]
		g_1 = [ QtGui.QSplitter(QtCore.Qt.Vertical) for i in range(4)]
		v=[]
		
		for i in range(4):
			g_0[i].addWidget(self.B_lbl[i])
		
			for j in range(4):
				for k in range(4):
					g_1h[i][j].addWidget(self.B[i,j,k])
				
				g_1[i].addWidget(g_1h[i][j])
		
			v.extend([ QtGui.QSplitter(QtCore.Qt.Vertical) ])
			v[i].addWidget(g_0[i])
			v[i].addWidget(g_1[i])
		
		g1_0 = QtGui.QGridLayout()
		g1_0.addWidget(ard_lbl,0,0)
		g1_1 = QtGui.QGridLayout()
		g1_1.addWidget(analog_pin_lbl,0,0)
		g1_1.addWidget(self.combo0,0,1)
		g1_1.addWidget(shutter_pin_lbl,1,0)
		g1_1.addWidget(self.combo4,1,1)
		g1_1.addWidget(avgpts_lbl,2,0)
		g1_1.addWidget(self.combo1,2,1)
		v1 = QtGui.QVBoxLayout()
		v1.addLayout(g1_0)
		v1.addLayout(g1_1)
		
		g2_0 = QtGui.QGridLayout()
		g2_0.addWidget(et_lbl,0,0)
		g2_0.addWidget(self.lcd1,1,0)
		v2 = QtGui.QVBoxLayout()
		v2.addLayout(g2_0)
		
		g3_0 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g3_0.addWidget(store_lbl)
		g3_1 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g3_1.addWidget(filename)
		g3_1.addWidget(foldername)
		g3_2 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g3_2.addWidget(self.filenameEdit)
		g3_2.addWidget(self.folderEdit)
		g3_3 = QtGui.QSplitter(QtCore.Qt.Horizontal)
		g3_3.addWidget(g3_1)
		g3_3.addWidget(g3_2)
		v3 = QtGui.QSplitter(QtCore.Qt.Vertical)
		v3.addWidget(g3_0)
		v3.addWidget(g3_3)
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		v_all = QtGui.QVBoxLayout()
		v_all.addLayout(v0)
		v_all.addLayout(v4)
		v_all.addLayout(g5_0)
		v_all.addLayout(g7_0)
		v_all.addLayout(v6)
		v_all.addWidget(v3)
		v_all.addLayout(v1)
		v_all.addLayout(v2)
		
		v_4 = QtGui.QVBoxLayout()
		for i in range(4):
			v_4.addWidget(v[i])
			
		h_some = QtGui.QHBoxLayout()
		h_some.addLayout(v_all)
		h_some.addLayout(v_4)

		# set graph  and toolbar to a new vertical group vcan
		gr0_0 = QtGui.QGridLayout()
		self.pw0 = pg.PlotWidget(name="Plot1")  ## giving the plot names allows us to link their axes together
		self.pw0.setTitle('Real-time datalogger')
		gr0_0.addWidget(self.pw0,0,0)
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		h_all = QtGui.QHBoxLayout()
		h_all.addLayout(h_some,1)
		h_all.addLayout(gr0_0,4)
		self.setLayout(h_all)

		########################################
		# PLOT 1 settings
		# create plot and add it to the figure canvas
		self.p0 = self.pw0.plotItem
		self.curve0=self.p0.plot(pen='w')
		self.curve1=self.p0.plot(pen='y')
		self.p0.getAxis('left').setLabel("Arb unit, 1023=5V", units="", color='yellow')
		self.p0.getAxis('bottom').setLabel("Elapsed time", units="s", color='yellow')
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw0.setDownsampling(mode='peak')
		self.pw0.setClipToView(True)
		
		#########################################

		#0 is A0 analog port
		#10 is number og averaging points
		self.clear_all_graphs()

		# reacts to choises picked in the menu
		self.combo0.activated[str].connect(self.onActivated0)
		self.combo1.activated[str].connect(self.onActivated1)
		self.combo2.activated[str].connect(self.onActivated2)
		self.combo3.activated[str].connect(self.onActivated3)
		self.combo4.activated[str].connect(self.onActivated4)
		self.allButtons_torf(False)
		
		for i in range(4):
			self.Bcalib_Button[i].clicked.connect(functools.partial(self.calib_func,i))
		self.Bcalib_stop_Button.clicked.connect(self.stop_moving)
		self.Bcalib_all_Button.clicked.connect(functools.partial(self.calib_func,None))
		
		self.Calc_Button.clicked.connect(self.calc_calib_params)
		self.Save_calc_Button.clicked.connect(self.save_calib_params)
		
		self.send_close_signal=False
		#self.setGeometry(600,0,1200,550)
		self.move(600,0)
		self.setWindowTitle('Scatterometer - calibrate')
		self.show()

	##########################################
	def onActivated0(self, text):
		
		self.analog_pin = int(text)
		
	def onActivated1(self, text):
		
		self.avg_pts = int(text)
		
	def onActivated2(self, text):
		
		self.dwell = int(text)
	
	def onActivated3(self, text):
		
		self.shutter_dwell = int(text)
	
	def onActivated4(self, text):
		
		self.shutter_pin = int(text)
	
	def ArdDialog(self):

		text, ok = QtGui.QInputDialog.getText(self, 'Serial Port Dialog','Enter Arduino serial', text=self.ardport_str)
		if ok:
			self.ardport_str = str(text)	
	
	def EspDialog(self):

		text, ok = QtGui.QInputDialog.getText(self, 'Serial Port Dialog','Enter ESP serial', text=self.espport_str)
		if ok:
			self.espport_str = str(text)
	
	def set_connect_serial(self):
		
		try:
			self.Esp = ESP300.ESP300(self.espport_str)
			self.Esp.set_timeout(2)
			vers=self.Esp.return_ver()
			print vers
			self.Esp.set_motors("on")
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message',"No response from the ESP serial port! Check the ESP port name and check the cable connection.")
			return None
		
		try:
			self.Md = MOTORSTEP_DRIVE.MOTORSTEP_DRIVE(self.ardport_str)
			self.Md.set_timeout(2)
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message',"No response from the Arduino serial port! Check the Arduino port name and check the cable connection.")
			return None
		
		self.conSerial.setEnabled(False)
		self.serialArd.setEnabled(False)
		self.serialEsp.setEnabled(False)

		self.allButtons_torf(True)
		
		for axs in range(3):
			pos=self.Esp.return_pos(axs+1)
			self.lcd[axs].display(str(pos))	
		
	def set_disconnect_serial(self):

		self.Esp.close()
		self.Md.close()

		self.conSerial.setEnabled(True)
		self.serialArd.setEnabled(True)
		self.serialEsp.setEnabled(True)
		
		self.allButtons_torf(False)

	def go_homeAllAxes(self):
		
		self.allButtons_torf(False)
		
		self.get_my_Thread_homeAll=my_Thread_homeAll(self.Esp)
		self.connect(self.get_my_Thread_homeAll,SIGNAL("update_lcd(PyQt_PyObject,PyQt_PyObject)"),self.update_lcd)
		self.connect(self.get_my_Thread_homeAll,SIGNAL('finished()'),self.set_finished)
		
		self.get_my_Thread_homeAll.start()


	def allButtons_torf(self,text):
		
		self.filenameEdit.setEnabled(text)
		self.folderEdit.setEnabled(text)
		self.homeAll.setEnabled(text)
		self.disconSerial.setEnabled(text)
		
		self.combo0.setEnabled(text)
		self.combo1.setEnabled(text)
		self.combo2.setEnabled(text)
		self.combo3.setEnabled(text)
		self.combo4.setEnabled(text)
		
		for i in range(4):
			self.Bcalib_Button[i].setEnabled(text)
		self.Bcalib_all_Button.setEnabled(text)
		
		for i in range(3):
			self.theta0Edit[i].setEnabled(text)
		self.Calc_Button.setEnabled(text)
		self.Save_calc_Button.setEnabled(text)
		
	def closeEvent(self,event):
		
		reply = QtGui.QMessageBox.question(self, 'Message', "Quit now? Serial ports will be flushed and disconnected!", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes:
			if hasattr(self, 'Md') or hasattr(self, 'Esp'):	
				
				if hasattr(self, 'get_my_Thread') and not hasattr(self, 'get_my_Thread_homeAll'):
					if self.get_my_Thread.isRunning():
						QtGui.QMessageBox.warning(self, 'Message', "Calibration in progress. Stop the calibration before closing the program!")
						event.ignore()
					else:
						if self.conSerial.isEnabled()==True:
							self.send_close_signal=True
							event.accept()
						else:
							self.Esp.close()
							self.Md.close()
							self.send_close_signal=True
							event.accept()

				elif hasattr(self, 'get_my_Thread_homeAll') and not hasattr(self, 'get_my_Thread'):
					if self.get_my_Thread_homeAll.isRunning():
						QtGui.QMessageBox.warning(self, 'Message', "Homing in progress. Wait for homing to finish before closing the program!")
						event.ignore()
					else:
						if self.conSerial.isEnabled()==True:
							self.send_close_signal=True
							event.accept()
						else:
							self.Esp.close()
							self.Md.close()
							self.send_close_signal=True
							event.accept()

				elif hasattr(self, 'get_my_Thread_homeAll') and hasattr(self, 'get_my_Thread'):
					if self.get_my_Thread_homeAll.isRunning():
						QtGui.QMessageBox.warning(self, 'Message', "Homing in progress. Wait for homing to finish before closing the program!")
						event.ignore()
					elif self.get_my_Thread.isRunning():
						QtGui.QMessageBox.warning(self, 'Message', "Calibration in progress. Stop the calibration before closing the program!")
						event.ignore()
					else:
						if self.conSerial.isEnabled()==True:
							self.send_close_signal=True
							event.accept()
						else:
							self.Esp.close()
							self.Md.close()
							self.send_close_signal=True
							event.accept()

				else:
					if self.conSerial.isEnabled()==True:
						self.send_close_signal=True
						event.accept()
					else:
						self.Esp.close()
						self.Md.close()
						self.send_close_signal=True
						event.accept()
			
			else:
				self.send_close_signal=True
				event.accept()
		else:
			event.ignore() 
	##########################################
	def send_signal(self):
		
		return self.send_close_signal

	def set_bstyle_v1(self,button):
		
		button.setStyleSheet('QPushButton {font-size: 25pt}')
		button.setFixedWidth(40)
		button.setFixedHeight(40)
  
	def set_lcd_style(self,lcd):

		#lcd.setFixedWidth(40)
		lcd.setFixedHeight(60)
  
	def stop_moving(self):
		
		self.get_my_Thread.abort_move()
		
	def calib_func(self,rot_axs):
		
		# update the lcd motorstep position
		
		self.allButtons_torf(False)
		self.Bcalib_stop_Button.setEnabled(True)
		
		sender = self.sender()
		self.get_my_Thread=my_Thread(sender.text(),self.Esp,self.Md,rot_axs,self.B_rotwh,self.PSG_colms,self.PSA_rows,self.Rows,self.Colms,self.analog_pin,self.avg_pts,self.dwell)
		self.connect(self.get_my_Thread,SIGNAL("more_tals(PyQt_PyObject,PyQt_PyObject)"),self.more_tals)
		self.connect(self.get_my_Thread,SIGNAL("volt_data(PyQt_PyObject,PyQt_PyObject)"),self.volt_data)
		self.connect(self.get_my_Thread,SIGNAL("update_lcd(PyQt_PyObject,PyQt_PyObject)"),self.update_lcd)
		self.connect(self.get_my_Thread,SIGNAL("update_B(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"),self.update_B)
		self.connect(self.get_my_Thread,SIGNAL("update_condB0(PyQt_PyObject)"),self.update_condB0)
		self.connect(self.get_my_Thread,SIGNAL("clear_graphs_from_thread(PyQt_PyObject)"),self.clear_graphs_from_thread)
		self.connect(self.get_my_Thread,SIGNAL("change_color(PyQt_PyObject,PyQt_PyObject)"),self.change_color)
		self.connect(self.get_my_Thread,SIGNAL('finished()'),self.set_finished)
		
		self.get_my_Thread.start()
	
	def calc_calib_params(self):
		
		self.B_=numpy.zeros((4,4,4))
		theta0Edit_=numpy.zeros(3)
		try:
			for i in range(3):
				theta0Edit_[i]=float(str(self.theta0Edit[i].text()))
			for rot_axs in range(4):
				for j in range(4):
					for k in range(4):
						self.B_[rot_axs,j,k]=int(str(self.B[rot_axs,j,k].text()))
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message',"Not all elements are integers! Did you calibrate all elements in B arrays? Are Theta0 values present?")
			return None
		
		try:
			sf=Scatterometer_funksjoner_ver2.Scatterometer_funksjoner()
			self.A,self.W,self.condB0AW,self.THETAM,self.M,self.Pd = sf.return_calib_params(self.B_[0,:,:],self.B_[1,:,:],self.B_[2,:,:],self.B_[3,:,:],theta0Edit_)
			for i in range(3):
				self.theta_optEdit[i].setText(str(round(self.THETAM[i]*180/numpy.pi,2)))
			self.condEdit[1].setText(str(round(self.condB0AW[1],2)))
			self.condEdit[2].setText(str(round(self.condB0AW[2],2)))
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message',"Could not calculate arrays A and W. Are all elements in calib arrays B[0]..B[3] present? Possibly at least one of B arrays is singular.")
			return None

	def save_calib_params(self):
		
		filename_str=str(self.filenameEdit.text())
		folder_str=str(self.folderEdit.text())
		timestr=self.timestr
		
		# For SAVING data
		if filename_str:
			string_filename=''.join([filename_str,timestr])
			#self.string_elapsedtime=''.join([self.filename_str,"elapsedtime_",self.timestr])
		else:
			string_filename=''.join(["data_",timestr])
			#self.string_elapsedtime=''.join(["data_elapsedtime_",self.timestr])
							
		if folder_str:
			saveinfolder=''.join([folder_str,"/"])
			if not os.path.isdir(folder_str):
				os.mkdir(folder_str)
		else:
			saveinfolder=""
		
		data_file=''.join([saveinfolder,string_filename,".py"])	

		try:
			with open(data_file, 'w') as thefile:
				thefile.write( ''.join(["Rows=[",','.join([str(self.Rows[i]) for i in range(16)]),"]\n"]) )
				thefile.write( ''.join(["Colms=[",','.join([str(self.Colms[i]) for i in range(16)]),"]\n"]) )
				thefile.write( ''.join(["A=[",','.join([str(round(self.A[i,j],4)) for i,j in zip(self.Rows,self.Colms)]),"]\n"]) )
				thefile.write( ''.join(["W=[",','.join([str(round(self.W[i,j],4)) for i,j in zip(self.Rows,self.Colms)]),"]\n"]) )
				for i in range(4):
					thefile.write( ''.join(["B",str(i),"=[",','.join([str(self.B[i,j,k].text()) for j,k in zip(self.Rows,self.Colms)]),"]\n"]) )
				for i in range(4):
					thefile.write( ''.join(["M",str(i),"=[",','.join([str(round(self.M[i,j,k],4)) for j,k in zip(self.Rows,self.Colms)]),"]\n"]) )
				thefile.write( ''.join(["Pd=[",','.join([str(round(self.Pd[i],4)) for i in range(4)]),"]\n"]) )
				thefile.write( ''.join(["Theta_opt=[",','.join([str(round(self.THETAM[i]*180/numpy.pi,4)) for i in range(3)]),"]\n"]) )
				thefile.write( ''.join(["CondB0=[",str(self.condB0AW[0]),"]\n"]) )
				thefile.write( ''.join(["CondA=[",str(self.condB0AW[1]),"]\n"]) )
				thefile.write( ''.join(["CondW=[",str(self.condB0AW[2]),"]"]) )
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message',"Could not save properly! Did you press the button Calc calib params?")
			return None
		
	def change_color(self,rot_axs,mystr):
		
		if mystr=="red":
			self.Bcalib_Button[rot_axs].setStyleSheet("color: red")
			self.B_lbl[rot_axs].setText(''.join(["B[",str(rot_axs),"]...running" ]))
			self.B_lbl[rot_axs].setStyleSheet("color: red")
		elif mystr=="black":
			self.Bcalib_Button[rot_axs].setStyleSheet("color: black")
			self.B_lbl[rot_axs].setText(''.join(["B[",str(rot_axs),"]" ]))
			self.B_lbl[rot_axs].setStyleSheet("color: blue")
		elif mystr=="AllBred":
			self.Bcalib_all_Button.setStyleSheet("color: red")
			self.B_lbl[rot_axs].setText(''.join(["B[",str(rot_axs),"]...running" ]))
			self.B_lbl[rot_axs].setStyleSheet("color: red")
		elif mystr=="SomeBblue":
			self.B_lbl[rot_axs].setText(''.join(["B[",str(rot_axs),"]" ]))
			self.B_lbl[rot_axs].setStyleSheet("color: blue")
		elif mystr=="AllBblack":
			self.Bcalib_all_Button.setStyleSheet("color: black")
	
	def clear_graphs_from_thread(self,rot_axs):
		
		self.clear_all_graphs()
		for j in range(4):
			for k in range(4):
				self.B[rot_axs,j,k].setText("--")
	
	def clear_all_graphs(self):
		
		self.end_volts_array=[]
		self.end_time_elap_aray=[]
		self.all_volts_array=[]
		self.all_time_elap_aray=[]
		
		self.curve0.clear()
		self.curve1.clear()
	
	def update_condB0(self,condB0):
		
		self.condEdit[0].setText(str(round(condB0,2)))
	
	def update_B(self,rot_axs,i,j,volt):
		
		self.B[rot_axs,i,j].setText(str(volt))
	
	def update_lcd(self,axs,pos):
		
		self.lcd[axs].display(str(pos))
	
	def more_tals(self,time_elap,volts):
		
		self.end_volts_array.extend([ volts ]) 
		self.end_time_elap_aray.extend([ time_elap ])
		self.curve0.setData(self.end_time_elap_aray, self.end_volts_array)
	
	def volt_data(self,time_elap,volts):
		
		self.all_volts_array.extend([ volts ]) 
		self.all_time_elap_aray.extend([ time_elap ])
		self.curve1.setData(self.all_time_elap_aray, self.all_volts_array)
	
	def set_finished(self):
		
		self.allButtons_torf(True)
		self.Bcalib_stop_Button.setEnabled(False)
	
	def set_save_plot(self):
		
		if str(self.filenameEdit.text()):
			saveinfile=''.join([str(self.filenameEdit.text()),self.timestr])
			saveinfile_et=''.join([str(self.filenameEdit.text()),"elapsedtime_",self.timestr])
		else:
			saveinfile=''.join(["data_",self.timestr])
			saveinfile_et=''.join(["data_elapsedtime_",self.timestr])
			
		if str(self.folderEdit.text()):
			if not os.path.isdir(str(self.folderEdit.text())):
				os.mkdir(str(self.folderEdit.text()))
			saveinfolder=''.join([str(self.folderEdit.text()),"/"])
		else:
			saveinfolder=""
		
		save_plot1=''.join([saveinfolder,saveinfile,'_scan.png'])	
		save_plot2=''.join([saveinfolder,saveinfile_et,'_scan.png'])	

		# create an exporter instance, as an argument give it
		# the item you wish to export
		exporter = pg.exporters.ImageExporter(self.pw0.plotItem)
		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_plot1)
		'''
		exporter = pg.exporters.ImageExporter(self.pw3.plotItem)
		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_plot2)
		'''
	def set_save(self):
		
		self.timestr=time.strftime("%y%m%d-%H%M")
		self.lcd1.display(self.timestr)
		
		with open("config_calib.py", 'w') as thefile:
			thefile.write( ''.join(["Analog_pin=",str(self.analog_pin),"\n"]) )
			thefile.write( ''.join(["Shutter_pin=",str(self.shutter_pin),"\n"]) )
			thefile.write( ''.join(["Avgpts=",str(self.avg_pts),"\n"]) )
			thefile.write( ''.join(["Shutter_dwell=",str(self.shutter_dwell),"\n"]) )
			thefile.write( ''.join(["Dwell=",str(self.dwell),"\n"]) )
			thefile.write( ''.join(["B_rotwh=[",','.join([str(self.B_rotwh[i]) for i in range(4)]),"]\n"]) )
			thefile.write( ''.join(["PSG_colms=[",','.join([str(self.PSG_colms[i]) for i in range(4)]),"]\n"]) )
			thefile.write( ''.join(["PSA_rows=[",','.join([str(self.PSA_rows[i]) for i in range(4)]),"]\n"]) )
			thefile.write( ''.join(["Rows=[",','.join([str(self.Rows[i]) for i in range(16)]),"]\n"]) )
			thefile.write( ''.join(["Colms=[",','.join([str(self.Colms[i]) for i in range(16)]),"]\n"]) )
			thefile.write( ''.join(["Theta0=[",','.join([str(self.theta0Edit[i].text()) for i in range(3)]),"]\n"]) )
			thefile.write( ''.join(["Minpos=[",','.join([str(self.Minpos[i]) for i in range(3)]),"]\n"]) )
			thefile.write( ''.join(["Maxpos=[",','.join([str(self.Maxpos[i]) for i in range(3)]),"]\n"]) )
			thefile.write( ''.join(["filename=\"",str(self.filenameEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["create_folder=\"",str(self.folderEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["timestr=\"",self.timestr,"\"\n"]) )
			thefile.write( ''.join(["ardport=\"",self.ardport_str,"\"\n"]) )
			thefile.write( ''.join(["espport=\"",self.espport_str,"\"\n"]) )

		reload(config_calib)
		self.analog_pin=config_calib.Analog_pin
		self.shutter_pin=config_calib.Shutter_pin
		self.avg_pts=config_calib.Avgpts
		self.shutter_dwell=config_calib.Shutter_dwell
		self.dwell=config_calib.Dwell
		self.B_rotwh=config_calib.B_rotwh
		self.PSG_colms=config_calib.PSG_colms
		self.PSA_rows=config_calib.PSA_rows
		self.Rows=config_calib.Rows
		self.Colms=config_calib.Colms
		self.Theta0=config_calib.Theta0
		self.Minpos=config_calib.Minpos
		self.Maxpos=config_calib.Maxpos
		self.timestr = config_calib.timestr
		self.filename_str = config_calib.filename
		self.folder_str = config_calib.create_folder	
		self.ardport_str = config_calib.ardport
		self.espport_str = config_calib.espport

def main():
  
  app=QtGui.QApplication(sys.argv)
  ex=run_zaber_gui()
  sys.exit(app.exec_())
    
if __name__=='__main__':
  main()
  
