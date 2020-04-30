import os, sys, serial, time, imp
import numpy, functools
import scipy.interpolate
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.exporters
#from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, SIGNAL
import config_scan, ESP300, MOTORSTEP_DRIVE

class my_Thread(QThread):
    
	def __init__(self, *argv):
		QThread.__init__(self)
		
		self.end_flag=False
		
		self.sender=argv[0]
		self.Esp=argv[1]
		self.Md=argv[2]
		self.calib_stepper=argv[3]
		self.ScanEdit=argv[4]
		self.drives_active=argv[5]
		self.B_rotwh=argv[6]
		self.PSG_colms=argv[7]
		self.PSA_rows=argv[8]
		self.Rows=argv[9]
		self.Colms=argv[10]
		self.channel=argv[11]
		self.avg_pts=argv[12]
		self.dwell=argv[13]
		self.filename_str=argv[14]
		self.folder_str=argv[15]
		self.timestr=argv[16]
		
		# For SAVING data
		if self.filename_str:
			self.string_filename=''.join([self.filename_str,self.timestr])
			#self.string_elapsedtime=''.join([self.filename_str,"elapsedtime_",self.timestr])
		else:
			self.string_filename=''.join(["data_",self.timestr])
			#self.string_elapsedtime=''.join(["data_elapsedtime_",self.timestr])
							
		if self.folder_str:
			self.saveinfolder=''.join([self.folder_str,"/"])
			if not os.path.isdir(self.folder_str):
				os.mkdir(self.folder_str)
		else:
			self.saveinfolder=""
			
    
	def __del__(self):
	  
	  self.wait()

	def abort_move(self):
		
		self.end_flag=True
		self.Md.stop_move()
		#self.Esp.set_stop()
	
	def make_header(self,drives_active):
		
		data_file=''.join([self.saveinfolder,self.string_filename,".txt"])
		# create regular text file, make headings and close it
		with open(data_file, 'w') as thefile:
			thefile.write("Your edit line - do NOT delete this line\n")
			
		if len(drives_active)==1:
			if drives_active==[0]:
				angs_to_move=["positioning Sampl ang."]
				with open(data_file, 'a') as thefile:
					thefile.write("Elapsed time [s], Sampl ang. [dg], M[row,column], Voltage [V]\n")
			elif drives_active==[1]:
				angs_to_move=["positioning In pl ang."]
				with open(data_file, 'a') as thefile:
					thefile.write("Elapsed time [s], In pl ang. [dg], M[row,column], Voltage [V]\n")	
			elif drives_active==[2]:
				angs_to_move=["positioning Out pl ang."]
				with open(data_file, 'a') as thefile:
					thefile.write("Elapsed time [s], Out pl ang. [dg], M[row,column], Voltage [V]\n")
		
		elif len(drives_active)==2:
			if drives_active==[0,1]:
				angs_to_move=["positioning Sampl ang.","positioning In pl ang."]
				with open(data_file, 'a') as thefile:
					thefile.write("Elapsed time [s], Sampl ang. [dg], In pl ang. [dg], M[row,column], Voltage [V]\n")
			elif drives_active==[0,2]:
				angs_to_move=["positioning Sampl ang.","positioning Out pl ang."]
				with open(data_file, 'a') as thefile:
					thefile.write("Elapsed time [s], Sampl ang. [dg], Out pl ang. [dg], M[row,column], Voltage [V]\n")	
			elif drives_active==[1,2]:
				angs_to_move=["positioning In pl ang.","positioning Out pl ang."]
				with open(data_file, 'a') as thefile:
					thefile.write("Elapsed time [s], In pl ang. [dg], Out pl ang. [dg], M[row,column], Voltage [V]\n")
		
		elif len(drives_active)==3:
			if drives_active==[0,1,2]:
				angs_to_move=["positioning Sampl ang.","positioning In pl ang.","positioning Out pl ang."]
				with open(data_file, 'a') as thefile:
					thefile.write("Elapsed time [s], Sampl ang. [dg], In pl ang. [dg], Out pl ang. [dg], M[row,column], Voltage [V]\n")		
	
		return data_file, angs_to_move
		
	def run(self):
		
		print self.drives_active
		
		data_file, angs_to_move = self.make_header(self.drives_active)
		positions = [[] for i in range(len(self.drives_active))]
		for i in range(len(self.drives_active)):
			ang_scanlist = numpy.arange(int(10*self.ScanEdit[i][0]),int(10*self.ScanEdit[i][1]),int(10*self.ScanEdit[i][2]))
			positions[i] = self.get_pos(self.drives_active[i],ang_scanlist/10.0)
			
		if self.sender=="Run scan":
			
			if len(self.drives_active)==1:
				
				time_start=time.time()
				for pos_1 in positions[0][:]:
					rot_drv=self.drives_active[0]
					self.emit(SIGNAL('clear_graphs_from_thread()'))
					self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),'red',angs_to_move[0])
					min_pos_drv=self.Md.move_Absolute(rot_drv,pos_1)
					pos_ang=self.get_ang(rot_drv,min_pos_drv)
					self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), rot_drv+3, pos_ang)
					
					self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),'red','positioning Rotation wheel')
					min_pos=self.Esp.move_abspos(0+1,self.B_rotwh[0])
					self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), 0, min_pos)
					
					for i,j in zip(self.Rows,self.Colms):
						if self.end_flag==True:
							break
						self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),'red','rotating PSG and PSA')
						min_pos=self.Esp.move_abspos(1+1,self.PSA_rows[i])
						self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), 1, min_pos)
						min_pos=self.Esp.move_abspos(2+1,self.PSG_colms[j])
						self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), 2, min_pos)
						
						time_s=time.time()
						while (time.time()-time_s)<self.dwell/1000.0:
							ard_volt=self.Md.read_analog(self.channel,self.avg_pts)
							time_elap=time.time()-time_start					
							self.emit(SIGNAL('volt_data(PyQt_PyObject,PyQt_PyObject)'), time_elap,ard_volt)
							
						M_str=''.join(["M[",str(i),",",str(j),"]"])
						with open(data_file, 'a') as thefile:
							thefile.write("%s" %time_elap)
							thefile.write("\t%s" %pos_ang)
							thefile.write("\t%s" %M_str)
							thefile.write("\t%s\n" %ard_volt)
						self.emit(SIGNAL('update_B(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),i,j,ard_volt)
						self.emit(SIGNAL('more_tals(PyQt_PyObject,PyQt_PyObject)'),time_elap,ard_volt)
						
					if self.end_flag==True:
						break
					
				self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),'blue','ready')
					
			elif len(self.drives_active)==2:
					
				time_start=time.time()
				for pos_1 in positions[0][:]:
					rot_drv=self.drives_active[0]
					self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),'red',angs_to_move[0])
					min_pos_drv=self.Md.move_Absolute(rot_drv,pos_1)
					pos_ang_1=self.get_ang(rot_drv,min_pos_drv)
					self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), rot_drv+3, pos_ang_1)
					
					for pos_2 in positions[1][:]:
						rot_drv=self.drives_active[1]
						self.emit(SIGNAL('clear_graphs_from_thread()'))
						self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),'red',angs_to_move[1])
						min_pos_drv=self.Md.move_Absolute(rot_drv,pos_2)
						pos_ang_2=self.get_ang(rot_drv,min_pos_drv)
						self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), rot_drv+3, pos_ang_2)
						
						self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),'red','positioning Rotation wheel')
						min_pos=self.Esp.move_abspos(0+1,self.B_rotwh[0])
						self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), 0, min_pos)
						
						for i,j in zip(self.Rows,self.Colms):
							if self.end_flag==True:
								break
							self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),'red','rotating PSG and PSA')
							min_pos=self.Esp.move_abspos(1+1,self.PSA_rows[i])
							self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), 1, min_pos)
							min_pos=self.Esp.move_abspos(2+1,self.PSG_colms[j])
							self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), 2, min_pos)
							
							time_s=time.time()
							while (time.time()-time_s)<self.dwell/1000.0:
								ard_volt=self.Md.read_analog(self.channel,self.avg_pts)
								time_elap=time.time()-time_start					
								self.emit(SIGNAL('volt_data(PyQt_PyObject,PyQt_PyObject)'), time_elap,ard_volt)
								
							M_str=''.join(["M[",str(i),",",str(j),"]"])
							with open(data_file, 'a') as thefile:
								thefile.write("%s" %time_elap)
								thefile.write("\t%s" %pos_ang_1)
								thefile.write("\t%s" %pos_ang_2)
								thefile.write("\t%s" %M_str)
								thefile.write("\t%s\n" %ard_volt)
							self.emit(SIGNAL('update_B(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),i,j,ard_volt)
							self.emit(SIGNAL('more_tals(PyQt_PyObject,PyQt_PyObject)'),time_elap,ard_volt)
							
						if self.end_flag==True:
							break
					if self.end_flag==True:
						break
				self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),'blue','ready')
				
			elif len(self.drives_active)==3:
					
				time_start=time.time()
				for pos_1 in positions[0][:]:
					rot_drv=self.drives_active[0]
					self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),'red',angs_to_move[0])
					min_pos_drv=self.Md.move_Absolute(rot_drv,pos_1)
					pos_ang_1=self.get_ang(rot_drv,min_pos_drv)
					self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), rot_drv+3, pos_ang_1)
					
					for pos_2 in positions[1][:]:
						rot_drv=self.drives_active[1]
						self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),'red',angs_to_move[1])
						min_pos_drv=self.Md.move_Absolute(rot_drv,pos_2)
						pos_ang_2=self.get_ang(rot_drv,min_pos_drv)
						self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), rot_drv+3, pos_ang_2)
					
						for pos_3 in positions[2][:]:
							rot_drv=self.drives_active[2]
							self.emit(SIGNAL('clear_graphs_from_thread()'))
							self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),'red',angs_to_move[2])
							min_pos_drv=self.Md.move_Absolute(rot_drv,pos_3)
							pos_ang_3=self.get_ang(rot_drv,min_pos_drv)
							self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), rot_drv+3, pos_ang_3)
							
							self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),'red','positioning Rotation wheel')
							min_pos=self.Esp.move_abspos(0+1,self.B_rotwh[0])
							self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), 0, min_pos)
							
							for i,j in zip(self.Rows,self.Colms):
								if self.end_flag==True:
									break
								self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),'red','rotating PSG and PSA')
								min_pos=self.Esp.move_abspos(1+1,self.PSA_rows[i])
								self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), 1, min_pos)
								min_pos=self.Esp.move_abspos(2+1,self.PSG_colms[j])
								self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), 2, min_pos)
								
								time_s=time.time()
								while (time.time()-time_s)<self.dwell/1000.0:
									ard_volt=self.Md.read_analog(self.channel,self.avg_pts)
									time_elap=time.time()-time_start					
									self.emit(SIGNAL('volt_data(PyQt_PyObject,PyQt_PyObject)'), time_elap,ard_volt)
									
								M_str=''.join(["M[",str(i),",",str(j),"]"])
								with open(data_file, 'a') as thefile:
									thefile.write("%s" %time_elap)
									thefile.write("\t%s" %pos_ang_1)
									thefile.write("\t%s" %pos_ang_2)
									thefile.write("\t%s" %pos_ang_3)
									thefile.write("\t%s" %M_str)
									thefile.write("\t%s\n" %ard_volt)
								self.emit(SIGNAL('update_B(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),i,j,ard_volt)
								self.emit(SIGNAL('more_tals(PyQt_PyObject,PyQt_PyObject)'),time_elap,ard_volt)
								
							if self.end_flag==True:
								break
						if self.end_flag==True:
							break
					if self.end_flag==True:
						break
				self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),'blue','ready')
			
			else:
				pass
		else:
			pass
	
	def get_pos(self,rot_drv,ang):	
		
		x=[]
		y=[]
		for i in range(4):
			if rot_drv==0:
				x.extend([ Stepper_calib_160715.sampl[i][0] ])
				y.extend([ Stepper_calib_160715.sampl[i][1] ])
			elif rot_drv==1:
				x.extend([ Stepper_calib_160715.inpl[i][0] ])
				y.extend([ Stepper_calib_160715.inpl[i][1] ])
			elif rot_drv==2:
				x.extend([ Stepper_calib_160715.outpl[i][0] ])
				y.extend([ Stepper_calib_160715.outpl[i][1] ])
			
		if numpy.min(ang)>=min(y) and numpy.max(ang)<=max(y):
			#spline
			pos_curve=scipy.interpolate.splrep(y, x, k=3, s=0)
			#linear
			#ang_curve = scipy.interpolate.splrep(x, y, k=1, s=0)
			pos_pos = scipy.interpolate.splev(ang, pos_curve, der=0)
			nums=numpy.rint(pos_pos) # round the up/down floats
			return nums.astype(int)
		
	def get_ang(self,rot_drv,pos):
		
		x=[]
		y=[]
		for i in range(4):
			if rot_drv==0:
				x.extend([ Stepper_calib_160715.sampl[i][0] ])
				y.extend([ Stepper_calib_160715.sampl[i][1] ])
			elif rot_drv==1:
				x.extend([ Stepper_calib_160715.inpl[i][0] ])
				y.extend([ Stepper_calib_160715.inpl[i][1] ])
			elif rot_drv==2:
				x.extend([ Stepper_calib_160715.outpl[i][0] ])
				y.extend([ Stepper_calib_160715.outpl[i][1] ])

		if numpy.min(pos)>=min(x) and numpy.max(pos)<=max(x):
			#spline
			ang_curve=scipy.interpolate.splrep(x, y, k=3, s=0)
			#linear
			#ang_curve = scipy.interpolate.splrep(x, y, k=1, s=0)
			pos_ang = scipy.interpolate.splev(pos, ang_curve, der=0)
			return numpy.round(pos_ang,1)


class my_Thread_homeAll(QThread):
    
	def __init__(self, *argv):
		QThread.__init__(self)
		
		self.Esp=argv[0]
		
	def __del__(self):
	  
	  self.wait()
	
	def run(self):
		
		self.Esp.set_motors("on")
		
		for axs in range(3):
			self.Esp.set_home(axs+1)
			pos=self.Esp.return_pos(axs+1)
			self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), axs, pos)


class run_zaber_gui(QtGui.QWidget):
  
	def __init__(self):
		super(run_zaber_gui, self).__init__()
		
		#####################################################
		
		# constants
		self.channel=config_scan.Channel
		self.avg_pts=config_scan.Avgpts
		self.dwell=config_scan.Dwell
		self.B_rotwh=config_scan.B_rotwh
		self.PSG_colms=config_scan.PSG_colms
		self.PSA_rows=config_scan.PSA_rows
		self.Rows=config_scan.Rows
		self.Colms=config_scan.Colms
		self.Minpos=config_scan.Minpos
		self.Maxpos=config_scan.Maxpos
		self.calib_aw_str=config_scan.Calib_AW
		self.calib_stepper_str=config_scan.Calib_stepper
		self.filename_str = config_scan.filename
		self.folder_str = config_scan.create_folder	
		self.timestr = config_scan.timestr
		self.ardport_str = config_scan.ardport
		self.espport_str = config_scan.espport
	
		self.initUI()
    
	def initUI(self):

		# status info which button has been pressed
		Bcalib_lbl = QtGui.QLabel("SCAN settings", self)
		Bcalib_lbl.setStyleSheet("color: blue")
		
		self.B_lbl=[ None for i in range(4) ]
		self.B=numpy.zeros((4,4,4),dtype=object)
		
		self.lcd = [ None for i in range(6) ]
		lcd_lbl = [ None for i in range(6) ]
		for i in range(6):
			if i==0:
				lcd_lbl[i] = QtGui.QLabel(''.join(["Wheel (Ax 1)"]), self)
			if i==1:
				lcd_lbl[i] = QtGui.QLabel(''.join(["PSG (Ax 2)"]), self) 
			if i==2:
				lcd_lbl[i] = QtGui.QLabel(''.join(["PSA (Ax 3)"]), self)
			if i==3:
				lcd_lbl[i] = QtGui.QLabel(''.join(["Samp (Drv 1)"]), self)
			if i==4:
				lcd_lbl[i] = QtGui.QLabel(''.join(["In pl (Drv 2)"]), self) 
			if i==5:
				lcd_lbl[i] = QtGui.QLabel(''.join(["Out pl (Drv 3)"]), self)	
				
			self.lcd[i] = QtGui.QLCDNumber(self)
			self.lcd[i].setStyleSheet("color: black")
			#self.set_lcd_style(self.lcd[i])
			self.lcd[i].setSegmentStyle(QtGui.QLCDNumber.Flat)
			self.lcd[i].setNumDigits(7)
			self.lcd[i].display('-------')
			self.lcd[i].setFixedWidth(95)
			self.lcd[i].setFixedHeight(40)
		
		####################################################
		
		Scan_lbl = [None for i in range(3)]
		Range_lbl = [None for i in range(3)]		
		for i in range(3):
			if i==0:
				Range_lbl[i] = QtGui.QLabel("Start", self)
				Scan_lbl[i] = QtGui.QLabel("Samp", self)
			if i==1:
				Range_lbl[i] = QtGui.QLabel("Stop", self)
				Scan_lbl[i] = QtGui.QLabel("In pl", self)
			if i==2:
				Range_lbl[i] = QtGui.QLabel("Step", self)
				Scan_lbl[i] = QtGui.QLabel("Out pl", self)
		
		self.ScanEdit = [[None for colms in range(3)] for rows in range(3)]
		for i in range(3):
			for j in range(3):
				self.ScanEdit[i][j] = QtGui.QLineEdit("",self)
				self.ScanEdit[i][j].setEnabled(False)
		
		####################################################
		
		self.Run_Button = QtGui.QPushButton("Run scan",self)
		self.Run_Button.setStyleSheet("color: black")
		#self.Run_Button.setFixedWidth(50)
		self.Run_Button.setEnabled(False)
		
		self.B_Stop_Button = QtGui.QPushButton("STOP",self)
		self.B_Stop_Button.setStyleSheet("color: black")
		#self.B_Stop_Button.setFixedWidth(50)
		self.B_Stop_Button.setEnabled(False)	
		
		for i in range(4):
			
			if i==0:
				self.B_lbl[i] = QtGui.QLabel("B", self)	
				self.B_lbl[i].setStyleSheet("color: blue")
			if i==1:
				self.B_lbl[i] = QtGui.QLabel("M", self)	
				self.B_lbl[i].setStyleSheet("color: blue")
			if i==2:
				self.B_lbl[i] = QtGui.QLabel("A (calib)", self)	
				self.B_lbl[i].setStyleSheet("color: blue")
			if i==3:
				self.B_lbl[i] = QtGui.QLabel("W (calib)", self)	
				self.B_lbl[i].setStyleSheet("color: blue")
			
			#self.moveabsButton.setStyleSheet('QPushButton {color: red}')
			for j in range(4):
				for k in range(4):
					self.B[i,j,k] = QtGui.QLineEdit("--",self)
					self.B[i,j,k].setFixedWidth(70)
					self.B[i,j,k].setEnabled(False)
		
		####################################################
		
		store_lbl = QtGui.QLabel("STORAGE filename and location", self)
		store_lbl.setStyleSheet("color: blue")
		filename = QtGui.QLabel("Save to file",self)
		foldername = QtGui.QLabel("Save to folder",self)
		self.filenameEdit = QtGui.QLineEdit(self.filename_str,self)
		self.folderEdit = QtGui.QLineEdit(self.folder_str,self)
		
		####################################################
		
		ard_lbl = QtGui.QLabel("ARDUINO and ESP settings", self)
		ard_lbl.setStyleSheet("color: blue")
			
		channel_lbl = QtGui.QLabel("Analog channel no.", self)
		self.combo0 = QtGui.QComboBox(self)
		mylist0=["0","1","2","3"]
		self.combo0.addItems(mylist0)
		self.combo0.setCurrentIndex(mylist0.index(str(self.channel)))
		
		avgpts_lbl = QtGui.QLabel("Averaging points", self)
		self.combo1 = QtGui.QComboBox(self)
		mylist1=["5","20","100","200","500","1000","2000"]
		self.combo1.addItems(mylist1)
		self.combo1.setCurrentIndex(mylist1.index(str(self.avg_pts)))
		
		dwell_lbl = QtGui.QLabel("Dwell time [ms]", self)
		self.combo2 = QtGui.QComboBox(self)
		mylist2=["500","1000","1500","2000","2500","3000","3500","4000"]
		self.combo2.addItems(mylist2)
		self.combo2.setCurrentIndex(mylist2.index(str(self.dwell)))

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
		
		self.serialMenu = MyBar.addMenu("Serial")
		self.conSerial = self.serialMenu.addAction("Connect to serial")
		self.conSerial.triggered.connect(self.set_connect_serial)
		self.disconSerial = self.serialMenu.addAction("Disconnect from serial")
		self.disconSerial.triggered.connect(self.set_disconnect_serial)
		self.disconSerial.setEnabled(False)
		##
		self.serialArd = self.serialMenu.addAction("Serial Arduino port")
		self.serialArd.triggered.connect(self.ArdDialog)
		self.serialEsp = self.serialMenu.addAction("Serial ESP port")
		self.serialEsp.triggered.connect(self.EspDialog)
		
		self.modeMenu = MyBar.addMenu("Steppers")
		self.homeAll = self.modeMenu.addAction(''.join(["ESP300 - Home all"]))
		self.homeAll.triggered.connect(self.set_homeAllAxes)
		self.conMode = [None for i in range(3)]
		self.disconMode = [None for i in range(3)]
		for i in range(3):
			self.conMode[i] = self.modeMenu.addAction(''.join(["Connect Drive ", str(i+1)]))
			self.conMode[i].triggered.connect(functools.partial(self.set_connect_drive,i))
			self.conMode[i].setEnabled(False)
			self.disconMode[i] = self.modeMenu.addAction(''.join(["Disconnect Drive ", str(i+1)]))
			self.disconMode[i].triggered.connect(functools.partial(self.set_disconnect_drive,i))
			self.disconMode[i].setEnabled(False)
		
		self.calibMenu = MyBar.addMenu("Calib")
		self.calibLoad = self.calibMenu.addAction("Calib file (A+W)")
		self.calibLoad.triggered.connect(self.loadCalibDialog)
		self.calibLoad.setShortcut('Ctrl+L')
		self.calibStepperLoad = self.calibMenu.addAction("Stepperbox calib file")
		self.calibStepperLoad.triggered.connect(self.loadStepperCalibDialog)
		
		################### MENU BARS END ##################
		
		g0_0=QtGui.QGridLayout()
		g0_0.addWidget(MyBar,0,0)
		v0 = QtGui.QVBoxLayout()
		v0.addLayout(g0_0)
		
		g4_0 = QtGui.QGridLayout()
		g4_0.addWidget(Bcalib_lbl,0,0)
		g4_1 = QtGui.QGridLayout()
		g4_1.addWidget(self.Run_Button,0,i+1)
		g4_1.addWidget(self.B_Stop_Button,0,i+2)
		v4 = QtGui.QVBoxLayout()
		v4.addLayout(g4_0)
		v4.addLayout(g4_1)
		
		g5_0 = QtGui.QGridLayout()
		for i in range(3):
			g5_0.addWidget(lcd_lbl[i],0,i)
			g5_0.addWidget(self.lcd[i],1,i)
		g5_1 = QtGui.QGridLayout()
		for i in range(3):
			g5_1.addWidget(lcd_lbl[i+3],0,i)
			g5_1.addWidget(self.lcd[i+3],1,i)
		v5 = QtGui.QVBoxLayout()
		v5.addLayout(g5_0)
		v5.addLayout(g5_1)
		
		g6_0 = QtGui.QGridLayout()
		for i in range(3):
			g6_0.addWidget(Range_lbl[i],0,i+1)
			g6_0.addWidget(Scan_lbl[i],i+1,0)
		for i in range(3):
			for j in range(3):
				g6_0.addWidget(self.ScanEdit[i][j],i+1,j+1)
		
		g_0=[ QtGui.QSplitter(QtCore.Qt.Vertical) for i in range(4)]		
		g_1h=[[ QtGui.QSplitter(QtCore.Qt.Horizontal) for i in range(4)] for j in range(4)]
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
		g1_1.addWidget(channel_lbl,0,0)
		g1_1.addWidget(self.combo0,0,1)
		g1_1.addWidget(avgpts_lbl,1,0)
		g1_1.addWidget(self.combo1,1,1)
		g1_1.addWidget(dwell_lbl,2,0)
		g1_1.addWidget(self.combo2,2,1)
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
		v_all.addLayout(g6_0)
		v_all.addLayout(v5)
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
		self.p0.getAxis('left').setLabel("Voltage", units="V", color='yellow')
		self.p0.getAxis('bottom').setLabel("Elapsed time", units="s", color='yellow')
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw0.setDownsampling(mode='peak')
		self.pw0.setClipToView(True)
		
		#########################################

		#0 is A0 analog port
		#10 is number og averaging points
		self.drives=[None for i in range(3)]
		self.drives_active=[]
		self.clear_all_graphs()

		# reacts to choises picked in the menu
		self.combo0.activated[str].connect(self.onActivated0)
		self.combo1.activated[str].connect(self.onActivated1)
		self.combo2.activated[str].connect(self.onActivated2)
		self.allButtons_torf(False)
		
		self.B_Stop_Button.clicked.connect(self.stop_moving)
		self.Run_Button.clicked.connect(self.scan_func)
		
		self.setGeometry(30,30,1200,550)
		self.setWindowTitle('Scatterometer')
		self.show()

	##########################################
	def loadStepperCalibDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file','/home/vfurtula/Documents/Projects/Scatteromter/Calib_files')
		if fname:
			self.calib_stepper_str = str(fname)
	
	def loadCalibDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file','/home/vfurtula/Documents/Projects/Scatterometer/Calib_files')
		if fname:
			self.calib_aw_str = str(fname)
			calib_path= imp.load_source("",str(fname))
			try:
				Rows = calib_path.Rows
				Colms = calib_path.Colms
				A = calib_path.A
				W = calib_path.W
				self.A=numpy.zeros((4,4))
				self.W=numpy.zeros((4,4))
				for i,j,s in zip(Rows,Colms,range(len(Rows))):
					self.A[i,j]=A[s]
					self.W[i,j]=W[s]
					self.B[2,i,j].setText(str(A[s]))
					self.B[3,i,j].setText(str(W[s]))
			except Exception, e:
				QtGui.QMessageBox.warning(self, 'Message',"Could not load calib params! Calib file must have among others following 1-D arrays: Rows,Colms,A,B!")
				return None
				
	def onActivated0(self, text):
		
		self.channel = int(text)
		
	def onActivated1(self, text):
		
		self.avg_pts = int(text)
		
	def onActivated2(self, text):
		
		self.dwell = int(text)
	
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
			self.Esp.set_timeout(0.025)
			vers=self.Esp.return_ver()
			print vers
			self.Esp.set_motors("on")
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message',"No response from the ESP serial port! Check the ESP port name and check the cable connection.")
			return None
		
		try:
			self.Md = MOTORSTEP_DRIVE.MOTORSTEP_DRIVE(self.ardport_str)
			self.Md.set_timeout(0.025)
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message',"No response from the Arduino serial port! Check the Arduino port name and check the cable connection.")
			return None
		
		self.disconSerial.setEnabled(True)
		self.conSerial.setEnabled(False)
		self.serialArd.setEnabled(False)
		self.serialEsp.setEnabled(False)
		self.calibLoad.setEnabled(False)
		self.calibStepperLoad.setEnabled(False)
		
		for axs in range(3):
			pos=self.Esp.return_pos(axs+1)
			self.lcd[axs].display(str(pos))	
			
			self.conMode[axs].setEnabled(True)
		
		self.allButtons_torf(True)
		
	def set_disconnect_serial(self):

		self.Esp.close()
		self.Md.close()

		self.disconSerial.setEnabled(False)
		self.conSerial.setEnabled(True)
		self.serialArd.setEnabled(True)
		self.serialEsp.setEnabled(True)
		self.calibLoad.setEnabled(True)
		self.calibStepperLoad.setEnabled(True)
		
		for i in range(3):
			self.conMode[i].setEnabled(False)
		
		self.allButtons_torf(False)

	def set_homeAllAxes(self):
		
		self.get_my_Thread_homeAll=my_Thread_homeAll(self.Esp)
		self.connect(self.get_my_Thread_homeAll,SIGNAL("update_lcd(PyQt_PyObject,PyQt_PyObject)"),self.update_lcd)
		self.connect(self.get_my_Thread_homeAll,SIGNAL('finished()'),self.set_finished_homed)
		
		self.disconSerial.setEnabled(False)
		self.B_Stop_Button.setEnabled(False)
		
		if self.Run_Button.isEnabled()==True:
			self.run__button_OldStatus=True
		else:
			self.run__button_OldStatus=False
		
		self.Run_Button.setEnabled(False)
		self.serialMenu.setEnabled(False)
		self.modeMenu.setEnabled(False)
		self.calibMenu.setEnabled(False)
			
		self.allButtons_torf(False)
		
		self.get_my_Thread_homeAll.start()

	def set_connect_drive(self,drive):
		
		self.drive_onoff('on',drive)
		self.disconSerial.setEnabled(False)		
		self.conMode[drive].setEnabled(False)
		self.disconMode[drive].setEnabled(True)
		self.Run_Button.setEnabled(True)
		
		# constants
		self.Md.set_minmax_pos(drive,'min',int(self.Minpos[drive]))
		self.Md.set_minmax_pos(drive,'max',int(self.Maxpos[drive]))
		self.Md.drive_on(drive)
		
		pos=self.Md.get_pos(drive)
		pos_ang=self.get_ang(drive,pos)
		self.lcd[drive+3].display(str(pos_ang))
		
		for i in range(3):
			self.ScanEdit[drive][i].setEnabled(True)
		
		#volts=self.Md.read_analog(self.channel,self.avg_pts)
		#self.some_volts.extend([ volts ])    
		#self.curve0.setData(self.some_volts)

	def set_disconnect_drive(self,drive):
		
		self.drive_onoff('off',drive)
		self.conMode[drive].setEnabled(True)
		self.disconMode[drive].setEnabled(False)
		
		if all(self.conMode[i].isEnabled() for i in range(3))==True:
			self.disconSerial.setEnabled(True)
			self.conSerial.setEnabled(False)
			self.serialArd.setEnabled(False)
			self.serialEsp.setEnabled(False)
			self.Run_Button.setEnabled(False)
	
		self.Md.drive_off(drive)
		self.lcd[drive+3].display("-------")
		for i in range(3):
			self.ScanEdit[drive][i].setEnabled(False)

	def drive_onoff(self,mystr,drive):
		
		if mystr=='on':
			self.drives[drive]=1
		elif mystr=='off':
			self.drives[drive]=None
		
		if self.drives==[None,None,None]:
			self.drives_active=[]
		elif self.drives==[1,None,None]:
			self.drives_active=[0]
		elif self.drives==[None,1,None]:
			self.drives_active=[1]
		elif self.drives==[None,None,1]:
			self.drives_active=[2]
		elif self.drives==[1,1,None]:
			self.drives_active=[0,1]
		elif self.drives==[None,1,1]:
			self.drives_active=[1,2]	
		elif self.drives==[1,None,1]:
			self.drives_active=[0,2]
		elif self.drives==[1,1,1]:
			self.drives_active=[0,1,2]
		
	def allButtons_torf(self,text):
		
		self.filenameEdit.setEnabled(text)
		self.folderEdit.setEnabled(text)
		self.homeAll.setEnabled(text)
		
		self.combo0.setEnabled(text)
		self.combo1.setEnabled(text)
		self.combo2.setEnabled(text)
		
	def closeEvent(self,event):
		
		reply = QtGui.QMessageBox.question(self, 'Message', "Quit now? Serial ports will be flushed and disconnected!", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes:
			if hasattr(self, 'Md') or hasattr(self, 'Esp'):	
				if not hasattr(self, 'get_my_Thread') and not hasattr(self, 'get_my_Thread_homeAll'):
					if self.conSerial.isEnabled()==True:
						event.accept()
					elif self.disconSerial.isEnabled()==True:
						self.Esp.close()
						self.Md.close()
						event.accept()
					else:
						QtGui.QMessageBox.warning(self, 'Message', "Disconnect all stepper drives before you close the program!")
						event.ignore()
				else:
					if hasattr(self, 'get_my_Thread'):
						if self.get_my_Thread.isRunning():
							QtGui.QMessageBox.warning(self, 'Message', "Run in progress. Stop the run and disconnect all stepper drives before closing the program!")
							event.ignore()
						else:
							if self.conSerial.isEnabled()==True:
								event.accept()
							elif self.disconSerial.isEnabled()==True:
								self.Esp.close()
								self.Md.close()
								event.accept()
							else:
								QtGui.QMessageBox.warning(self, 'Message', "Disconnect all stepper drives before you close the program!")
								event.ignore()
					elif hasattr(self, 'get_my_Thread_homeAll'):
						if self.get_my_Thread_homeAll.isRunning():
							QtGui.QMessageBox.warning(self, 'Message', "Homing in progress. Wait for homing to finish before closing the program!")
							event.ignore()
			else:
				event.accept()
		else:
			event.ignore() 
	##########################################

	def set_bstyle_v1(self,button):
		
		button.setStyleSheet('QPushButton {font-size: 25pt}')
		button.setFixedWidth(40)
		button.setFixedHeight(40)
  
	def set_lcd_style(self,lcd):

		#lcd.setFixedWidth(40)
		lcd.setFixedHeight(60)
  
	def stop_moving(self):
		
		self.get_my_Thread.abort_move()
		
	def scan_func(self):
		
		# update the lcd motorstep position
		passScanEdit=[[None for colms in range(3)] for rows in range(len(self.drives_active))]
		for i in range(len(self.drives_active)):
			try:
				passScanEdit[i][0] = float(self.ScanEdit[self.drives_active[i]][0].text())
				passScanEdit[i][1] = float(self.ScanEdit[self.drives_active[i]][1].text())
				passScanEdit[i][2] = float(self.ScanEdit[self.drives_active[i]][2].text())
			except Exception, e:
				QtGui.QMessageBox.warning(self, 'Message',"Only integers or floating point numbers accepted!")
				return None
				
		filename_str=str(self.filenameEdit.text())
		folder_str=str(self.folderEdit.text())
		timestr=self.timestr
		
		sender = self.sender()
		self.get_my_Thread=my_Thread(sender.text(),self.Esp,self.Md,self.calib_stepper_str,passScanEdit,self.drives_active,self.B_rotwh,self.PSG_colms,self.PSA_rows,self.Rows,self.Colms,self.channel,self.avg_pts,self.dwell,filename_str,folder_str,timestr)
		self.connect(self.get_my_Thread,SIGNAL("more_tals(PyQt_PyObject,PyQt_PyObject)"),self.more_tals)
		self.connect(self.get_my_Thread,SIGNAL("volt_data(PyQt_PyObject,PyQt_PyObject)"),self.volt_data)
		self.connect(self.get_my_Thread,SIGNAL("update_lcd(PyQt_PyObject,PyQt_PyObject)"),self.update_lcd)
		self.connect(self.get_my_Thread,SIGNAL("update_B(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"),self.update_B)
		self.connect(self.get_my_Thread,SIGNAL("clear_graphs_from_thread()"),self.clear_graphs_from_thread)
		self.connect(self.get_my_Thread,SIGNAL("change_color(PyQt_PyObject,PyQt_PyObject)"),self.change_color)
		self.connect(self.get_my_Thread,SIGNAL('finished()'),self.set_finished)
		
		self.allButtons_torf(False)
		self.B_Stop_Button.setEnabled(True)
		self.Run_Button.setEnabled(False)
		self.serialMenu.setEnabled(False)
		self.modeMenu.setEnabled(False)
		self.calibMenu.setEnabled(False)
		
		self.get_my_Thread.start()
	
	def change_color(self,get_color,mystr):
		
		if get_color=="red":
			self.B_lbl[0].setText(''.join(["B...",str(mystr)]))
			self.B_lbl[0].setStyleSheet("color: red")
		elif get_color=="blue":
			self.B_lbl[0].setText(''.join(["B ",str(mystr)]))
			self.B_lbl[0].setStyleSheet("color: blue")
			
	def clear_graphs_from_thread(self):
		
		self.clear_all_graphs()
		for j in range(4):
			for k in range(4):
				self.B[0,j,k].setText("--")
	
	def clear_all_graphs(self):
		
		self.end_volts_array=[]
		self.end_time_elap_aray=[]
		self.all_volts_array=[]
		self.all_time_elap_aray=[]
		
		self.curve0.clear()
		self.curve1.clear()
	
	def update_B(self,i,j,volt):
		
		self.B[0,i,j].setText(str(round(volt,2)))
	
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
	
	def set_finished_homed(self):
		
		self.allButtons_torf(True)
		self.serialMenu.setEnabled(True)
		self.modeMenu.setEnabled(True)
		self.calibMenu.setEnabled(True)
		
		if self.run__button_OldStatus==True:
			self.Run_Button.setEnabled(True)
		else:
			self.Run_Button.setEnabled(False)
		
	def set_finished(self):
		
		self.allButtons_torf(True)
		self.B_Stop_Button.setEnabled(False)
		self.Run_Button.setEnabled(True)
		self.serialMenu.setEnabled(True)
		self.modeMenu.setEnabled(True)
		self.calibMenu.setEnabled(True)
		
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
		
		with open("config_scan.py", 'w') as thefile:
			thefile.write( ''.join(["Channel=",str(self.channel),"\n"]) )
			thefile.write( ''.join(["Avgpts=",str(self.avg_pts),"\n"]) )
			thefile.write( ''.join(["Dwell=",str(self.dwell),"\n"]) )
			thefile.write( ''.join(["B_rotwh=[",','.join([str(self.B_rotwh[i]) for i in range(4)]),"]\n"]) )
			thefile.write( ''.join(["PSG_colms=[",','.join([str(self.PSG_colms[i]) for i in range(4)]),"]\n"]) )
			thefile.write( ''.join(["PSA_rows=[",','.join([str(self.PSA_rows[i]) for i in range(4)]),"]\n"]) )
			thefile.write( ''.join(["Rows=[",','.join([str(self.Rows[i]) for i in range(16)]),"]\n"]) )
			thefile.write( ''.join(["Colms=[",','.join([str(self.Colms[i]) for i in range(16)]),"]\n"]) )
			thefile.write( ''.join(["Minpos=[",','.join([str(self.Minpos[i]) for i in range(3)]),"]\n"]) )
			thefile.write( ''.join(["Maxpos=[",','.join([str(self.Maxpos[i]) for i in range(3)]),"]\n"]) )
			thefile.write( ''.join(["Calib_AW=\"",self.calib_aw_str,"\"\n"]) )
			thefile.write( ''.join(["Calib_stepper=\"",self.calib_stepper_str,"\"\n"]) )
			thefile.write( ''.join(["filename=\"",str(self.filenameEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["create_folder=\"",str(self.folderEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["timestr=\"",self.timestr,"\"\n"]) )
			thefile.write( ''.join(["ardport=\"",self.ardport_str,"\"\n"]) )
			thefile.write( ''.join(["espport=\"",self.espport_str,"\"\n"]) )

		reload(config_scan)
		self.channel=config_scan.Channel
		self.avg_pts=config_scan.Avgpts
		self.dwell=config_scan.Dwell
		self.B_rotwh=config_scan.B_rotwh
		self.PSG_colms=config_scan.PSG_colms
		self.PSA_rows=config_scan.PSA_rows
		self.Rows=config_scan.Rows
		self.Colms=config_scan.Colms
		self.Minpos=config_scan.Minpos
		self.Maxpos=config_scan.Maxpos
		self.calib_aw_str=config_scan.Calib_AW
		self.calib_stepper_str=config_scan.Calib_stepper
		self.filename_str = config_scan.filename
		self.folder_str = config_scan.create_folder	
		self.timestr = config_scan.timestr
		self.ardport_str = config_scan.ardport
		self.espport_str = config_scan.espport

	def get_ang(self,rot_drv,pos):
		
		x=[]
		y=[]
		for i in range(4):
			if rot_drv==0:
				x.extend([ Stepper_calib_160715.sampl[i][0] ])
				y.extend([ Stepper_calib_160715.sampl[i][1] ])
			elif rot_drv==1:
				x.extend([ Stepper_calib_160715.inpl[i][0] ])
				y.extend([ Stepper_calib_160715.inpl[i][1] ])
			elif rot_drv==2:
				x.extend([ Stepper_calib_160715.outpl[i][0] ])
				y.extend([ Stepper_calib_160715.outpl[i][1] ])
				
		if numpy.min(pos)>=min(x) and numpy.max(pos)<=max(x):
			#spline
			ang_curve=scipy.interpolate.splrep(x, y, k=3, s=0)
			#linear
			#ang_curve = scipy.interpolate.splrep(x, y, k=1, s=0)
			pos_ang = scipy.interpolate.splev(pos, ang_curve, der=0)
			return numpy.round(pos_ang,1)


def main():
  
  app=QtGui.QApplication(sys.argv)
  ex=run_zaber_gui()
  sys.exit(app.exec_())
    
if __name__=='__main__':
  main()
  
