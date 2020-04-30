import os, sys, serial, time
import numpy, functools
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.exporters
#from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, SIGNAL
import config_calib, MOTORSTEP_DRIVE

class zaber_Thread(QThread):
    
	def __init__(self, *argv):
		QThread.__init__(self)
		
		self.sender=argv[0]
		self.Md=argv[1]
		self.move_num=argv[2]
		self.drive=argv[3]
		self.analog_pin=argv[4]
		self.avg_pts=argv[5]
    
	def __del__(self):
	  
	  self.wait()

	def abort_move(self):
		
		self.Md.stop_move()
		
	def run(self):
		  
		if self.sender==u'\u25b2':
			min_pos=self.Md.move_Relative(self.drive,5)
			ard_volt=self.Md.read_analog(self.analog_pin,self.avg_pts)
			self.emit(SIGNAL('more_tals(PyQt_PyObject,PyQt_PyObject)'), min_pos, ard_volt)
			
		elif self.sender==u'\u25bc':
			min_pos=self.Md.move_Relative(self.drive,-5)
			ard_volt=self.Md.read_analog(self.analog_pin,self.avg_pts)
			self.emit(SIGNAL('more_tals(PyQt_PyObject,PyQt_PyObject)'), min_pos, ard_volt)
			  
		elif self.sender=='Move rel':
			min_pos=self.Md.move_Relative(self.drive,self.move_num)
			ard_volt=self.Md.read_analog(self.analog_pin,self.avg_pts)
			self.emit(SIGNAL('more_tals(PyQt_PyObject,PyQt_PyObject)'), min_pos, ard_volt)
			
		elif self.sender=='Move abs':
			min_pos=self.Md.move_Absolute(self.drive,self.move_num)
			ard_volt=self.Md.read_analog(self.analog_pin,self.avg_pts)
			self.emit(SIGNAL('more_tals(PyQt_PyObject,PyQt_PyObject)'), min_pos, ard_volt)
			
		else:
		  pass
  
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
		self.stepper_lbl=[]; self.upButton=[]; self.downButton=[]
		self.moverelButton=[]; self.moveabsButton=[]; self.stopButton=[]
		self.moverelEdit=[]; self.moveabsEdit=[]; self.lcd=[]
		self.min_lbl=[]; self.max_lbl=[]; self.minEdit=[]; self.maxEdit=[]; 
		
		for i in range(3):
			self.stepper_lbl.extend([ QtGui.QLabel(''.join(["Drive ", str(i+1)]), self) ])
			self.stepper_lbl[i].setStyleSheet("color: blue")
			self.upButton.extend([ QtGui.QPushButton(u'\u25b2',self) ])
			self.set_bstyle_v1(self.upButton[i])
			self.downButton.extend([ QtGui.QPushButton(u'\u25bc',self) ])
			self.set_bstyle_v1(self.downButton[i])
			self.moverelButton.extend([ QtGui.QPushButton('Move rel',self) ])
			self.moveabsButton.extend([ QtGui.QPushButton('Move abs',self) ])
			#self.moveabsButton.setStyleSheet('QPushButton {color: red}')
			self.moverelEdit.extend([ QtGui.QLineEdit(str(100),self) ])
			self.moverelEdit[i].setFixedWidth(60)
			self.moveabsEdit.extend([ QtGui.QLineEdit(str(10000),self) ])
			self.moveabsEdit[i].setFixedWidth(60)
			self.stopButton.extend([ QtGui.QPushButton('STOP',self) ])
			self.stopButton[i].setEnabled(False)
			self.min_lbl.extend([ QtGui.QLabel("Min pos", self) ])
			self.max_lbl.extend([ QtGui.QLabel("Max pos", self) ])
			self.minEdit.extend([ QtGui.QLineEdit(str(self.Minpos[i]),self) ])
			self.minEdit[i].setFixedWidth(60)
			self.maxEdit.extend([ QtGui.QLineEdit(str(self.Maxpos[i]),self) ])
			self.maxEdit[i].setFixedWidth(60)
			
			##############################################
			
			self.lcd.extend([ QtGui.QLCDNumber(self) ])
			self.lcd[i].setStyleSheet("color: black")
			#self.set_lcd_style(self.lcd[i])
			self.lcd[i].setSegmentStyle(QtGui.QLCDNumber.Flat)
			self.lcd[i].setNumDigits(5)
			self.lcd[i].display('-----')
			#self.lcd[i].setFixedWidth(280)
		
		##############################################
		
		ard_lbl = QtGui.QLabel("Arduino settings", self)
		ard_lbl.setStyleSheet("color: blue")
			
		channel_lbl = QtGui.QLabel("Analog pin no.", self)
		self.combo0 = QtGui.QComboBox(self)
		mylist0=["0","1","2","3"]
		self.combo0.addItems(mylist0)
		self.combo0.setCurrentIndex(mylist0.index(str(self.analog_pin)))
		
		shutter_pin_lbl = QtGui.QLabel("Shutter pin no.", self)
		self.combo2 = QtGui.QComboBox(self)
		mylist2=["45","46","47","48"]
		self.combo2.addItems(mylist2)
		self.combo2.setCurrentIndex(mylist2.index(str(self.shutter_pin)))
		
		avgpts_lbl = QtGui.QLabel("Averaging points", self)
		self.combo1 = QtGui.QComboBox(self)
		mylist1=["5","20","100","200","500","1000","2000"]
		self.combo1.addItems(mylist1)
		self.combo1.setCurrentIndex(mylist1.index(str(self.avg_pts)))
		
		self.openShutter = QtGui.QPushButton("Open shutter",self)
		self.closeShutter = QtGui.QPushButton("Close shutter",self)
		self.openShutter.setEnabled(False)
		self.closeShutter.setEnabled(False)

		################### MENU BARS START ##################
		
		MyBar = QtGui.QMenuBar(self)
		fileMenu = MyBar.addMenu("File")
		fileSaveSet = fileMenu.addAction("Save settings")
		fileSaveSet.triggered.connect(self.set_save)
		fileSaveSet.setShortcut('Ctrl+S')
		self.fileClose = fileMenu.addAction("Close")        
		self.fileClose.triggered.connect(self.close) # triggers closeEvent()
		self.fileClose.setShortcut('Ctrl+X')
		
		serialMenu = MyBar.addMenu("Serial")
		self.conSerial = serialMenu.addAction("Connect to serial")
		self.conSerial.triggered.connect(self.set_connect_serial)
		self.disconSerial = serialMenu.addAction("Disconnect from serial")
		self.disconSerial.triggered.connect(self.set_disconnect_serial)
		self.disconSerial.setEnabled(False)
		##
		self.serialStepper = serialMenu.addAction("Serial port")
		self.serialStepper.triggered.connect(self.StepperDialog)
		
		modeMenu = MyBar.addMenu("Drivers")
		self.conMode=[]; self.disconMode=[]
		for i in range(3):
			self.conMode.extend([ modeMenu.addAction(''.join(["Connect Drive ", str(i+1)])) ])
			self.conMode[i].triggered.connect(functools.partial(self.set_connect,i))
			self.conMode[i].setEnabled(False)
			self.disconMode.extend([ modeMenu.addAction(''.join(["Disconnect Drive ", str(i+1)])) ])
			self.disconMode[i].triggered.connect(functools.partial(self.set_disconnect,i))
			self.disconMode[i].setEnabled(False)
		
		################### MENU BARS END ##################
		
		g0_0=QtGui.QGridLayout()
		g0_0.addWidget(MyBar,0,0)
		v0 = QtGui.QVBoxLayout()
		v0.addLayout(g0_0)

		g_0=[]; g_1=[]; g_2=[]; h_0=[]; g_3=[]; g_4=[]
		g_5=[]; h_1=[]; h_2=[]; v=[]
		
		for i in range(3):
			g_0.extend([ QtGui.QSplitter(QtCore.Qt.Vertical) ])
			g_0[i].addWidget(self.stepper_lbl[i])
			g_1.extend([ QtGui.QSplitter(QtCore.Qt.Vertical) ])
			g_1[i].addWidget(self.upButton[i])
			g_1[i].addWidget(self.downButton[i])
			g_2.extend([ QtGui.QSplitter(QtCore.Qt.Vertical) ])
			g_2[i].addWidget(self.lcd[i])
			h_0.extend([ QtGui.QSplitter(QtCore.Qt.Horizontal) ])
			h_0[i].addWidget(g_1[i])
			h_0[i].addWidget(g_2[i])
			g_3.extend([ QtGui.QSplitter(QtCore.Qt.Vertical) ])
			g_3[i].addWidget(self.moverelButton[i])
			g_3[i].addWidget(self.moveabsButton[i])
			g_4.extend([ QtGui.QSplitter(QtCore.Qt.Vertical) ])
			g_4[i].addWidget(self.moverelEdit[i])
			g_4[i].addWidget(self.moveabsEdit[i])
			g_5.extend([ QtGui.QSplitter(QtCore.Qt.Vertical) ])
			g_5[i].addWidget(self.stopButton[i])
			h_1.extend([ QtGui.QSplitter(QtCore.Qt.Horizontal) ])
			h_1[i].addWidget(g_5[i])
			h_1[i].addWidget(g_3[i])
			h_1[i].addWidget(g_4[i])
			h_2.extend([ QtGui.QSplitter(QtCore.Qt.Horizontal) ])
			h_2[i].addWidget(self.min_lbl[i])
			h_2[i].addWidget(self.minEdit[i])
			h_2[i].addWidget(self.max_lbl[i])
			h_2[i].addWidget(self.maxEdit[i])
		
			v.extend([ QtGui.QSplitter(QtCore.Qt.Vertical) ])
			v[i].addWidget(g_0[i])
			v[i].addWidget(h_0[i])
			v[i].addWidget(h_1[i])
			v[i].addWidget(h_2[i])
		
		g1_0 = QtGui.QGridLayout()
		g1_0.addWidget(ard_lbl,0,0)
		g1_1 = QtGui.QGridLayout()
		g1_1.addWidget(channel_lbl,0,0)
		g1_1.addWidget(self.combo0,0,1)
		g1_1.addWidget(shutter_pin_lbl,1,0)
		g1_1.addWidget(self.combo2,1,1)
		g1_1.addWidget(avgpts_lbl,2,0)
		g1_1.addWidget(self.combo1,2,1)
		g1_1.addWidget(self.openShutter,3,0)
		g1_1.addWidget(self.closeShutter,3,1)
		
		v1 = QtGui.QVBoxLayout()
		v1.addLayout(g1_0)
		v1.addLayout(g1_1)
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		v_all = QtGui.QVBoxLayout()
		v_all.addLayout(v0)
		for i in range(3):
			v_all.addWidget(v[i])
		v_all.addLayout(v1)

		# set graph  and toolbar to a new vertical group vcan
		gr0_0 = QtGui.QGridLayout()
		self.pw0 = pg.PlotWidget(name="Plot1")  ## giving the plot names allows us to link their axes together
		self.pw0.setTitle('Real-time datalogger')
		self.pw0.setLabel('left', 'Stepper pos.')
		self.pw0.setLabel('bottom', 'no. of moves')
		gr0_0.addWidget(self.pw0,0,0)
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		h_all = QtGui.QHBoxLayout()
		h_all.addLayout(v_all,1)
		h_all.addLayout(gr0_0,4)
		self.setLayout(h_all)

		########################################
		# PLOT 1 settings
		# create plot and add it to the figure canvas
		self.p0 = self.pw0.plotItem
		self.curve0=self.p0.plot(pen='y')
		self.p0.getAxis('left').setLabel("Arb unit, 1023=5V", units="", color='yellow')
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw0.setDownsampling(mode='peak')
		self.pw0.setClipToView(True)
		
		#########################################

		#0 is A0 analog port
		#10 is number og averaging points
		self.some_volts=[]

		# reacts to choises picked in the menu
		self.combo0.activated[str].connect(self.onActivated0)
		self.combo1.activated[str].connect(self.onActivated1)
		self.combo2.activated[str].connect(self.onActivated2)
		
		self.drives_onoff=[0,0,0]
		for i in range(3):
			self.upButton[i].clicked.connect(functools.partial(self.move_jog,i))
			self.downButton[i].clicked.connect(functools.partial(self.move_jog,i))
			self.moverelButton[i].clicked.connect(functools.partial(self.move_rel,i))
			self.moveabsButton[i].clicked.connect(functools.partial(self.move_abs,i))
			self.stopButton[i].clicked.connect(self.move_stop)
			self.allButtons_torf(i,False)
		
		self.openShutter.clicked.connect(self.open_shutter)
		self.closeShutter.clicked.connect(self.close_shutter)
		
		self.send_close_signal=False	
		#self.setGeometry(600,0,1200,550)
		self.move(600,0)
		self.setWindowTitle('Scatterometer - align arm/sample stage')
		self.show()

	##########################################
	def onActivated0(self, text):
		
		self.analog_pin = int(text)
		
		volts=self.Md.read_analog(self.analog_pin,self.avg_pts)
		self.some_volts.extend([ volts ])    
		self.curve0.setData(self.some_volts)
		
	def onActivated1(self, text):
		
		self.avg_pts = int(text)
	
	def onActivated2(self, text):
		
		self.shutter_pin = int(text)
	
	def open_shutter(self):
		
		self.openShutter.setEnabled(False)
		self.closeShutter.setEnabled(True)
	
	def close_shutter(self):
		
		self.openShutter.setEnabled(True)
		self.closeShutter.setEnabled(False)
	
	def StepperDialog(self):

		text, ok = QtGui.QInputDialog.getText(self, 'Serial Port Dialog','Enter stepper driver serial', text=self.ardport_str)
		if ok:
			self.ardport_str = str(text)	
	
	def set_connect_serial(self):
		
		try:
			self.Md = MOTORSTEP_DRIVE.MOTORSTEP_DRIVE(self.ardport_str)
			self.Md.set_timeout(2)
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message',"No response from stepper serial port! Check the Arduino port name and check the cable connection.")
			return None
		
		for i in range(3):
			self.conMode[i].setEnabled(True)
			self.disconMode[i].setEnabled(False)
			
		self.disconSerial.setEnabled(True)
		self.conSerial.setEnabled(False)
		self.serialStepper.setEnabled(False)
		self.combo0.setEnabled(True)
		self.combo1.setEnabled(True)
		self.combo2.setEnabled(True)
		
		self.close_shutter()
			
	def set_disconnect_serial(self):

		self.Md.close()

		for i in range(3):
			self.conMode[i].setEnabled(False)
			self.disconMode[i].setEnabled(False)
			
		self.disconSerial.setEnabled(False)
		self.conSerial.setEnabled(True)
		self.serialStepper.setEnabled(True)
		self.combo0.setEnabled(False)
		self.combo1.setEnabled(False)
		self.combo2.setEnabled(False)
		
		self.close_shutter()
		self.openShutter.setEnabled(False)
	
	def drives(self,drive,mystr):
		
		if mystr=='on':
			self.drives_onoff[drive]=1
		elif mystr=='off':
			self.drives_onoff[drive]=0
			
	def set_connect(self,drive):
		
		self.drives(drive,'on')
		self.driveButtons_torf(drive,True)
		self.disconSerial.setEnabled(False)		
		self.conMode[drive].setEnabled(False)
		self.disconMode[drive].setEnabled(True)
		
		# constants
		self.Md.set_minmax_pos(drive,'max',int(self.maxEdit[drive].text()))
		self.Md.set_minmax_pos(drive,'min',int(self.minEdit[drive].text()))
		self.Md.drive_on(drive)
		
		pos=self.Md.get_pos(drive)
		self.lcd[drive].display(str(pos))
		
		volts=self.Md.read_analog(self.analog_pin,self.avg_pts)
		self.some_volts.extend([ volts ])    
		self.curve0.setData(self.some_volts)
		
	def set_disconnect(self,drive):

		self.drives(drive,'off')
		self.driveButtons_torf(drive,False)
		self.conMode[drive].setEnabled(True)
		self.disconMode[drive].setEnabled(False)
		
		if all(self.conMode[i].isEnabled() for i in range(3))==True:
			self.disconSerial.setEnabled(True)
			self.conSerial.setEnabled(False)
			self.serialStepper.setEnabled(False)
	
		self.Md.drive_off(drive)
	
	def driveButtons_torf(self,drive,text):
		
		self.upButton[drive].setEnabled(text)
		self.downButton[drive].setEnabled(text)
		self.moverelButton[drive].setEnabled(text)
		self.moveabsButton[drive].setEnabled(text)
		self.moverelEdit[drive].setEnabled(text)
		self.moveabsEdit[drive].setEnabled(text)
		self.minEdit[drive].setEnabled(text)
		self.maxEdit[drive].setEnabled(text)

	def allButtons_torf(self,drive,text):
		
		self.combo0.setEnabled(text)
		self.combo1.setEnabled(text)
		self.combo2.setEnabled(text)
		for i in range(3):
			self.upButton[i].setEnabled(text)
			self.downButton[i].setEnabled(text)
			self.moverelButton[i].setEnabled(text)
			self.moveabsButton[i].setEnabled(text)
			self.moverelEdit[i].setEnabled(text)
			self.moveabsEdit[i].setEnabled(text)
			self.minEdit[i].setEnabled(text)
			self.maxEdit[i].setEnabled(text)
			if i!=drive:
				self.stopButton[i].setEnabled(text)
		
	def closeEvent(self,event):
		
		reply = QtGui.QMessageBox.question(self, 'Message', "Quit now? The microstep position will be saved and the stepper will turn off the hold current!", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes:
			if hasattr(self, 'Md'):	
				if not hasattr(self, 'get_zaber_Thread'):
					if self.disconSerial.isEnabled()==True:
						self.Md.close()
						self.send_close_signal=True
						event.accept()
					elif self.conSerial.isEnabled()==True:
						self.send_close_signal=True
						event.accept()
					else:
						QtGui.QMessageBox.warning(self, 'Message', "Disconnect all the drivers before you close the program!")
						event.ignore()
				
				else:
					if self.get_zaber_Thread.isRunning():
						QtGui.QMessageBox.warning(self, 'Message', "Run in progress. Stop the run and disconnect all the drivers before you close the program!")
						event.ignore()
					else:
						if self.disconSerial.isEnabled()==True:
							self.Md.close()
							self.send_close_signal=True
							event.accept()
						elif self.conSerial.isEnabled()==True:
							self.send_close_signal=True
							event.accept()
						else:
							QtGui.QMessageBox.warning(self, 'Message', "Disconnect all the drivers before you close the program!")
							event.ignore()
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
  
	def move_stop(self):
		
		self.get_zaber_Thread.abort_move()
			
	def move_rel(self,drive):
		
		# update the lcd motorstep position
		self.drive=drive
		move_num = int(self.moverelEdit[drive].text())
		
		self.Md.set_minmax_pos(drive,'max',int(self.maxEdit[drive].text()))
		self.Md.set_minmax_pos(drive,'min',int(self.minEdit[drive].text()))
		move_tot = move_num+self.Md.get_pos(drive)
		
		if move_tot<int(self.minEdit[drive].text()) or move_tot>int(self.maxEdit[drive].text()):
			QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid range is from ',str(self.minEdit[drive].text()),' to ',str(self.maxEdit[drive].text()),' microsteps.' ]) )
		else:
			self.disconMode[drive].setEnabled(False)
			self.allButtons_torf(drive,False)
			self.stopButton[drive].setEnabled(True)
			
			sender = self.sender()
			self.get_zaber_Thread=zaber_Thread(sender.text(),self.Md,move_num,drive,self.analog_pin,self.avg_pts)
			self.connect(self.get_zaber_Thread,SIGNAL("more_tals(PyQt_PyObject,PyQt_PyObject)"), self.more_tals)
			self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
			
			self.get_zaber_Thread.start()
		
	def move_abs(self,drive):
		
		# update the lcd motorstep position
		self.drive = drive
		move_num = int(self.moveabsEdit[drive].text())
		
		self.Md.set_minmax_pos(drive,'max',int(self.maxEdit[drive].text()))
		self.Md.set_minmax_pos(drive,'min',int(self.minEdit[drive].text()))
		
		if move_num<int(self.minEdit[drive].text()) or move_num>int(self.maxEdit[drive].text()):
			QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid range is from ',str(self.minEdit[drive].text()),' to ',str(self.maxEdit[drive].text()),' microsteps.' ]) )
		else:
			self.disconMode[drive].setEnabled(False)
			self.allButtons_torf(drive,False)
			self.stopButton[drive].setEnabled(True)
			
			sender = self.sender()
			self.get_zaber_Thread=zaber_Thread(sender.text(),self.Md,move_num,drive,self.analog_pin,self.avg_pts)
			self.connect(self.get_zaber_Thread,SIGNAL("more_tals(PyQt_PyObject,PyQt_PyObject)"),self.more_tals)
			self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
			    
			self.get_zaber_Thread.start()
		
	def move_jog(self,drive):
		
		# update the lcd motorstep position
		self.drive = drive
		sender = self.sender()
		if sender.text()==u'\u25b2':
			move_num=5
		elif sender.text()==u'\u25bc':
			move_num=-5
			
		move_tot = move_num+self.Md.get_pos(drive)
		if move_tot<int(self.minEdit[drive].text()) or move_tot>int(self.maxEdit[drive].text()):
			QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid range is from ',str(self.minEdit[drive].text()),' to ',str(self.maxEdit[drive].text()),' microsteps.' ]) )
		else:
			self.disconMode[drive].setEnabled(False)
			
			self.get_zaber_Thread=zaber_Thread(sender.text(),self.Md,None,drive,self.analog_pin,self.avg_pts)
			self.connect(self.get_zaber_Thread,SIGNAL("more_tals(PyQt_PyObject,PyQt_PyObject)"),self.more_tals)
			self.connect(self.get_zaber_Thread, SIGNAL('finished()'), self.set_finished)
			
			self.get_zaber_Thread.start()
	
	def more_tals(self,pos,volts):
		
		self.lcd[self.drive].display(str(pos))
		self.some_volts.extend([ volts ])    
		
		self.curve0.setData(self.some_volts)
	
	def set_finished(self):
		
		self.disconMode[self.drive].setEnabled(True)
		self.stopButton[self.drive].setEnabled(False)
		self.combo0.setEnabled(True)
		self.combo1.setEnabled(True)
		self.combo2.setEnabled(True)

		for i in range(3):
			if self.drives_onoff[i]==1:
				self.driveButtons_torf(i,True)
			elif self.drives_onoff[i]==0:
				self.driveButtons_torf(i,False)


	def set_save(self):
		
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
			thefile.write( ''.join(["Theta0=[",','.join([str(self.Theta0[i]) for i in range(3)]),"]\n"]) )
			thefile.write( ''.join(["Minpos=[",','.join([str(self.minEdit[i].text()) for i in range(3)]),"]\n"]) )
			thefile.write( ''.join(["Maxpos=[",','.join([str(self.maxEdit[i].text()) for i in range(3)]),"]\n"]) )
			thefile.write( ''.join(["filename=\"",self.filename_str,"\"\n"]) )
			thefile.write( ''.join(["create_folder=\"",self.folder_str,"\"\n"]) )
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
  
