import os, sys, imp, serial, time, numpy
import scipy.interpolate
#from numpy.polynomial import polynomial as P
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.exporters
#from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, QTimer, SIGNAL
import matplotlib as mpl
from matplotlib import cm

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

from mpl_toolkits.mplot3d import Axes3D
import config_zeiss, SR510, ZaberXmcb_ascii, Methods_for_XYscan



class zaber_Thread(QThread):
    
	def __init__(self, *argv):
		
		QThread.__init__(self)
		
		self.abort_flag=False
		self.pause_flag=False
		
		self.sender=argv[0]
		self.some_obj=argv[1]
		
	def __del__(self):
	  
		self.wait()

	def abort(self):
		
		self.some_obj.zaber.set_Stop(1,self.axs)
		self.abort_flag=True
	
	def pause(self):
		
		self.pause_flag = not self.pause_flag
			
			
	def return_pos_if_stopped(self):
		
		return self.some_obj.zaber.return_Position_When_Stopped(1,self.axs)
		
		
	def update(self):

		min_pos=self.return_pos_if_stopped()
		if min_pos in [serial.SerialException, ValueError]:
			self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),min_pos)
			return
		
		pos_val=self.get_zeiss_value(min_pos,self.some_obj.calib_file,self.some_obj.adjust_mode)
		sr510_volt=self.some_obj.sr510.return_voltage()
		if sr510_volt in [serial.SerialException, ValueError]:
			self.emit(SIGNAL('bad_sr510_val(PyQt_PyObject)'),sr510_volt)
			return
		
		more_tals_obj=type('more_tals_obj',(object,),{'min_pos':min_pos, 'pos_val':pos_val, 'sr510_volt':sr510_volt})
		self.emit(SIGNAL('more_tals(PyQt_PyObject)'), more_tals_obj)
		
		lcd_obj=type('lcd_obj',(object,),{'min_pos':min_pos, 'pos_val':pos_val})
		self.emit(SIGNAL('update_pos_lcd(PyQt_PyObject)'),lcd_obj)
		
		if self.some_obj.adjust_mode=="wavelength":
			lcd_obj=type('lcd_obj',(object,),{'pos_wl':pos_val})
			self.emit(SIGNAL('update_lcd(PyQt_PyObject)'),lcd_obj)
			self.replace_line("config_zeiss.py",4,''.join(["Last_position_lambda=[",str(min_pos),",",str(pos_val),"]\n"]))
		elif self.some_obj.adjust_mode=="slit":
			lcd_obj=type('lcd_obj',(object,),{'pos_slit':pos_val})
			self.emit(SIGNAL('update_lcd(PyQt_PyObject)'),lcd_obj)
			self.replace_line("config_zeiss.py",5,''.join(["Last_position_slit=[",str(min_pos),",",str(pos_val),"]\n"]))
		imp.reload(config_zeiss)
		
		
	def replace_line(self,file_name, line_num, text):
		
		lines = open(file_name, 'r').readlines()
		lines[line_num] = text
		out = open(file_name, 'w')
		out.writelines(lines)
		out.close()
		
	
	def run(self):
			
		if self.sender==u'\u25b2':
			if self.some_obj.adjust_mode=="wavelength":
				self.axs=1
			elif self.some_obj.adjust_mode=="slit":
				self.axs=2
				
			min_pos=self.some_obj.zaber.move_Relative(1,self.axs,10)
			if min_pos in [serial.SerialException, ValueError]:
				self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),min_pos)
				return
			self.update()
			
		elif self.sender==u'\u25bc':
			if self.some_obj.adjust_mode=="wavelength":
				self.axs=1
			elif self.some_obj.adjust_mode=="slit":
				self.axs=2
				
			min_pos=self.some_obj.zaber.move_Relative(1,self.axs,-10)
			if min_pos in [serial.SerialException, ValueError]:
				self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),min_pos)
				return
			self.update()
			  
		elif self.sender=='Move rel':
			if self.some_obj.adjust_mode=="wavelength":
				self.axs=1
			elif self.some_obj.adjust_mode=="slit":
				self.axs=2
				
			check=self.some_obj.zaber.move_Relative(1,self.axs,self.some_obj.move_num)
			if check in [serial.SerialException, ValueError]:
				self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),check)
				return 
			self.update()
			
		elif self.sender=='Move abs':
			if self.some_obj.adjust_mode=="wavelength":
				self.axs=1
			elif self.some_obj.adjust_mode=="slit":
				self.axs=2
				
			check=self.some_obj.zaber.move_Absolute(1,self.axs,self.some_obj.move_num)
			if check in [serial.SerialException, ValueError]:
				self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),check)
				return
			self.update()
			  
		elif self.sender=='Move to nm':
			self.axs=1
			position=self.get_pos(self.some_obj.move_num,self.some_obj.calib_file,self.some_obj.adjust_mode)
			check=self.some_obj.zaber.move_Absolute(1,self.axs,position)
			if check in [serial.SerialException, ValueError]:
				self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),check)
				return
			self.update()
			
		elif self.sender=='Move to mm':
			self.axs=2
			position=self.get_pos(self.some_obj.move_num,self.some_obj.calib_file,self.some_obj.adjust_mode)
			check=self.some_obj.zaber.move_Absolute(1,self.axs,position)
			if check in [serial.SerialException, ValueError]:
				self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),check)
				return
			self.update()
			
		elif self.sender=='-> nm':
			self.axs=1
			alignEdit_nm=self.some_obj.move_num
			min_pos=self.get_pos(alignEdit_nm,self.some_obj.calib_file,self.some_obj.adjust_mode)
			check=self.some_obj.zaber.set_Current_Position(1,self.axs,min_pos)
			if check in [serial.SerialException, ValueError]:
				self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),check)
				return
			sr510_volt=self.some_obj.sr510.return_voltage()
			if sr510_volt in [serial.SerialException, ValueError]:
				self.emit(SIGNAL('bad_sr510_val(PyQt_PyObject)'),sr510_volt)
				return
			
			more_tals_obj=type('more_tals_obj',(object,),{'min_pos':min_pos, 'pos_val':alignEdit_nm, 'sr510_volt':sr510_volt})
			self.emit(SIGNAL('more_tals(PyQt_PyObject)'), more_tals_obj)
			
			lcd_obj=type('lcd_obj',(object,),{'min_pos':min_pos, 'pos_val':alignEdit_nm})
			self.emit(SIGNAL('update_pos_lcd(PyQt_PyObject)'),lcd_obj)
			
			lcd_obj=type('lcd_obj',(object,),{'pos_wl':alignEdit_nm})
			self.emit(SIGNAL('update_lcd(PyQt_PyObject)'),lcd_obj)
			
			self.replace_line("config_zeiss.py",4,''.join(["Last_position_lambda=[",str(min_pos),",",str(alignEdit_nm),"]\n"]))
			imp.reload(config_zeiss)
			
		elif self.sender=='-> mm':
			self.axs=2
			alignEdit_mm=self.some_obj.move_num
			min_pos=self.get_pos(alignEdit_mm,self.some_obj.calib_file,self.some_obj.adjust_mode)
			check=self.some_obj.zaber.set_Current_Position(1,self.axs,min_pos)
			if check in [serial.SerialException, ValueError]:
				self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),check)
				return
			sr510_volt=self.some_obj.sr510.return_voltage()
			if sr510_volt in [serial.SerialException, ValueError]:
				self.emit(SIGNAL('bad_sr510_val(PyQt_PyObject)'),sr510_volt)
				return
			
			more_tals_obj=type('more_tals_obj',(object,),{'min_pos':min_pos, 'pos_val':alignEdit_mm, 'sr510_volt':sr510_volt})
			self.emit(SIGNAL('more_tals(PyQt_PyObject)'), more_tals_obj)
			
			lcd_obj=type('lcd_obj',(object,),{'min_pos':min_pos, 'pos_val':alignEdit_mm})
			self.emit(SIGNAL('update_pos_lcd(PyQt_PyObject)'),lcd_obj)
			
			lcd_obj=type('lcd_obj',(object,),{'pos_slit':alignEdit_mm})
			self.emit(SIGNAL('update_lcd(PyQt_PyObject)'),lcd_obj)
			
			self.replace_line("config_zeiss.py",5,''.join(["Last_position_slit=[",str(min_pos),",",str(alignEdit_mm),"]\n"]))
			imp.reload(config_zeiss)
						
		elif self.sender=='Start scan':
			
			# open calib file and plot
			calib_file_slit=self.some_obj.calib_file_slit
			calib_file_lambda=self.some_obj.calib_file_lambda
			save_to_file = self.some_obj.save_to_file
			
			start_wl = self.some_obj.start_wl
			stop_wl = self.some_obj.stop_wl
			step_wl = self.some_obj.step_wl
			dwell_wl = self.some_obj.dwell_wl
			start_slit = self.some_obj.start_slit
			stop_slit = self.some_obj.stop_slit
			step_slit = self.some_obj.step_slit
			dwell_slit = self.some_obj.dwell_slit
			
			# Initial read of the config file
			sm = Methods_for_XYscan.Scan_methods(start_wl,stop_wl,step_wl,'wavelength', start_slit,stop_slit,step_slit,'slit')
			
			xf = Methods_for_XYscan.Myrange(start_wl,stop_wl,step_wl,'wavelength')
			wv_fields=xf.myrange() # wavelength movement
			
			yf = Methods_for_XYscan.Myrange(start_slit,stop_slit,step_slit,'slit')
			slit_fields=yf.myrange() # slit movement
			
			# wl_vals, slit_vals = sm.run('xsnake')
					
			# create regular text file, make headings and close it
			with open(save_to_file, 'w') as thefile:
				thefile.write("Your edit line - do NOT delete this line\n")
				thefile.write("Wavelength [nm], Slit width [mm], Voltage [V], Elapsed time [s]\n")
			
			time_start=time.time()
			
			wv_positions = self.get_pos(wv_fields,calib_file_lambda,'wavelength')
			slit_positions = self.get_pos(slit_fields,calib_file_slit,'slit')
			
			#wv_positions = scipy.interpolate.splev(wv_scanlist, wv_curve, der=0)
			
			switch_pp=1
			for hh,dd,numofslits in zip(slit_fields,slit_positions,range(len(slit_fields))):
				
				if self.abort_flag==True:
					return
				# pause the scan
				while self.pause_flag:
					time.sleep(0.25)
				
				self.axs=2
				check=self.some_obj.zaber.move_Absolute(1,self.axs,dd)
				if check in [serial.SerialException, ValueError]:
					self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),check)
					return
				min_pos_slit=self.return_pos_if_stopped()
				if min_pos_slit in [serial.SerialException, ValueError]:
					self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),min_pos_slit)
					return
				pos_val_slit=self.get_zeiss_value(min_pos_slit,calib_file_slit,'slit')
				
				if self.some_obj.adjust_mode=="slit":
					lcd_obj=type('lcd_obj',(object,),{'min_pos':min_pos_slit, 'pos_val':pos_val_slit})
					self.emit(SIGNAL('update_pos_lcd(PyQt_PyObject)'),lcd_obj)
				
				lcd_obj=type('lcd_obj',(object,),{'pos_slit':pos_val_slit})
				self.emit(SIGNAL('update_lcd(PyQt_PyObject)'),lcd_obj)
				
				self.replace_line("config_zeiss.py",5,''.join(["Last_position_slit=[",str(min_pos_slit),",",str(pos_val_slit),"]\n"]))
				imp.reload(config_zeiss)
				
				time_s=time.time()
				while (time.time()-time_s)<dwell_slit:
					pass
				
				for ff,pp,numofwl in zip(wv_fields[::switch_pp],wv_positions[::switch_pp],range(len(wv_fields))):
					
					if self.abort_flag==True:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.25)
					
					self.axs=1
					check=self.some_obj.zaber.move_Absolute(1,self.axs,pp)
					if check in [serial.SerialException, ValueError]:
						self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),check)
						return
					min_pos_wl=self.return_pos_if_stopped()
					if min_pos_wl in [serial.SerialException, ValueError]:
						self.emit(SIGNAL('bad_zaber_val(PyQt_PyObject)'),min_pos_wl)
						return
					pos_val_wl=self.get_zeiss_value(min_pos_wl,calib_file_lambda,'wavelength')
					sr510_volt=self.some_obj.sr510.return_voltage()
					if sr510_volt in [serial.SerialException, ValueError]:
						self.emit(SIGNAL('bad_sr510_val(PyQt_PyObject)'),sr510_volt)
						return
					
					more_tals_obj=type('more_tals_obj',(object,),{'min_pos':min_pos_wl, 'pos_val':pos_val_wl, 'sr510_volt':sr510_volt})
					self.emit(SIGNAL('more_tals(PyQt_PyObject)'), more_tals_obj)
					
					curve3_obj=type('curve3_obj',(object,),{'min_pos_wl':min_pos_wl, 'wl':ff,'min_pos_slit':min_pos_slit,'slit':hh})
					self.emit(SIGNAL('curve3_data(PyQt_PyObject)'), curve3_obj)
					
					if self.some_obj.adjust_mode=="wavelength":
						lcd_obj=type('lcd_obj',(object,),{'min_pos':min_pos_wl, 'pos_val':pos_val_wl})
						self.emit(SIGNAL('update_pos_lcd(PyQt_PyObject)'),lcd_obj)
					
					lcd_obj=type('lcd_obj',(object,),{'pos_wl':pos_val_wl})
					self.emit(SIGNAL('update_lcd(PyQt_PyObject)'),lcd_obj)
					
					self.replace_line("config_zeiss.py",4,''.join(["Last_position_lambda=[",str(min_pos_wl),",",str(pos_val_wl),"]\n"]))
					imp.reload(config_zeiss)

					
					time_s=time.time()
					while (time.time()-time_s)<dwell_wl:
						sr510_volt=self.some_obj.sr510.return_voltage()
						if sr510_volt in [serial.SerialException, ValueError]:
							self.emit(SIGNAL('bad_sr510_val(PyQt_PyObject)'),sr510_volt)
							return
						time_elap=time.time()-time_start
						volt_obj=type('volt_obj',(object,),{'time_elap':time_elap, 'wl':ff, 'slit':hh, 'sr510_volt':sr510_volt})
						self.emit(SIGNAL('volt_data(PyQt_PyObject)'), volt_obj)
						
					with open(save_to_file, 'a') as thefile:
						thefile.write("%s\t" %ff)
						thefile.write("%s\t" %hh)
						thefile.write("%s\t" %sr510_volt)
						thefile.write("%s\n" %time_elap)
						
					self.emit(SIGNAL('time_data(PyQt_PyObject)'), volt_obj)
				
				switch_pp=switch_pp*-1
			
			if numofslits>1 and numofwl>1:
				# plot the data as a contour plot
				time.sleep(1)
				
				self.emit(SIGNAL('make_3Dplot()'))
			
		else:
			pass
		
		
	def get_pos(self,nm,calib_file,adjust_mode):
		
		x=[]
		y=[]
		with open(calib_file, 'r') as thefile:
			for line in thefile:
				columns = line.split()
				x.extend([int(columns[0])]) #microstep pos.
				if adjust_mode=="wavelength":
					y.extend([round(float(columns[1]),1)]) #wavelength
				elif adjust_mode=="slit":
					y.extend([round(float(columns[1]),2)]) #slit
					
		if numpy.min(nm)>=min(y) and numpy.max(nm)<=max(y):
			#spline
			pos_curve=scipy.interpolate.splrep(y, x, k=3, s=0)
			#linear
			#wv_curve = scipy.interpolate.splrep(x, y, k=1, s=0)
			pos_pos = scipy.interpolate.splev(nm, pos_curve, der=0)
			nums=numpy.rint(pos_pos) # round the up/down floats
			return nums.astype(int)
		
		
	def get_zeiss_value(self,pos,calib_file,adjust_mode):
		
		x=[]
		y=[]
		with open(calib_file, 'r') as thefile:
			for line in thefile:
				columns = line.split()
				x.extend([int(columns[0])]) #microstep pos.
				if adjust_mode=="wavelength":
					y.extend([round(float(columns[1]),1)]) #wavelength
				elif adjust_mode=="slit":
					y.extend([round(float(columns[1]),2)]) #slit
					
		if numpy.min(pos)>=min(x) and numpy.max(pos)<=max(x):
			#spline
			wv_curve=scipy.interpolate.splrep(x, y, k=3, s=0)
			#linear
			#wv_curve = scipy.interpolate.splrep(x, y, k=1, s=0)
			pos = scipy.interpolate.splev(pos, wv_curve, der=0)
			if adjust_mode=="wavelength":
				return numpy.round(pos,1)
			elif adjust_mode=="slit":
				return numpy.round(pos,2)
			
			
			
			
			
			
			
			
			
			
		
			
			
			
			
			
			
		
		
		
class Run_gui(QtGui.QDialog):
  
	def __init__(self, MyBar, parent=None):
		QtGui.QDialog.__init__(self, parent)
		#super(Run_gui, self).__init__(parent)
		
		#####################################################

		# constants
		self.Validrange_lambda = config_zeiss.Validrange_lambda
		self.Validrange_slit = config_zeiss.Validrange_slit
		self.Range_lambda = config_zeiss.Range_lambda
		self.Range_slit = config_zeiss.Range_slit
		self.schroll_pts = config_zeiss.Schroll_pts

		self.calibfile_lambda_str = config_zeiss.calibfile_lambda
		self.calibfile_slit_str = config_zeiss.calibfile_slit
		
		self.timestr = config_zeiss.timestr
		self.filename_str = config_zeiss.filename
		self.folder_str = config_zeiss.foldername	
		self.zaberport_str = config_zeiss.zaberport
		self.sr510port_str = config_zeiss.sr510port
		
		self.MyBar=MyBar
		
		self.initUI()
    
	def initUI(self):
		
		##############################################
		
		lbl_zeiss = QtGui.QLabel("SCAN parameters:", self)
		lbl_zeiss.setStyleSheet("color: blue")
		
		lambda_lbl = QtGui.QLabel(u'\u03bb[nm]',self) 
		slit_lbl = QtGui.QLabel("Slit[mm]",self)
		
		start_lbl = QtGui.QLabel("Start",self) 
		stop_lbl = QtGui.QLabel("Stop",self)
		step_lbl = QtGui.QLabel("Step",self)
		dwelltime = QtGui.QLabel("Dwell",self)
		
		self.Range_lambdaEdit = [QtGui.QLineEdit(str(self.Range_lambda[tal]),self) for tal in range(4)]
		self.Range_slitEdit = [QtGui.QLineEdit(str(self.Range_slit[tal]),self) for tal in range(4)]
		for i in range(4):
			self.Range_lambdaEdit[i].setFixedWidth(35)
			self.Range_slitEdit[i].setFixedWidth(35)
			
		self.startscanButton = QtGui.QPushButton('Start scan',self)
		self.pausescanButton = QtGui.QPushButton('Pause scan',self)
		self.pausescanButton.setEnabled(False)
		self.infoCalibButton = QtGui.QPushButton('Files info',self)
		
		actual_lbl = QtGui.QLabel("Actual",self)
		self.lcd_actual = [QtGui.QLCDNumber(self) for i in range(2)]
		for i in range(2):
			self.lcd_actual[i].setStyleSheet("color: blue")
			#self.lcd_actual.setFixedHeight(60)
			self.lcd_actual[i].setSegmentStyle(QtGui.QLCDNumber.Flat)
			self.lcd_actual[i].setNumDigits(6)
			self.lcd_actual[i].display('-------')
		
		lb3 = QtGui.QLabel("ADJUST position for:",self)
		lb3.setStyleSheet("color: blue")
		self.cb3 = QtGui.QComboBox(self)
		mylist3=["wavelength","slit"]
		self.cb3.addItems(mylist3)
		self.cb3.setCurrentIndex(mylist3.index("wavelength"))
		self.cb3.setEnabled(True)
		
		##############################################
		
		schroll_lbl = QtGui.QLabel("Schroll elapsed time",self)
		self.combo2 = QtGui.QComboBox(self)
		mylist2=["250 pts","500 pts","1000 pts","2000 pts","4000 pts","5000 pts"]
		self.combo2.addItems(mylist2)
		self.combo2.setCurrentIndex(mylist2.index(''.join([str(self.schroll_pts)," pts"])))
		#self.combo2.setFixedWidth(90)
		
		##############################################
		
		lbl4 = QtGui.QLabel("STORAGE filename and location settings:", self)
		lbl4.setStyleSheet("color: blue")
		filename = QtGui.QLabel("Save to file",self)
		foldername = QtGui.QLabel("Save to folder",self)
		self.filenameEdit = QtGui.QLineEdit(self.filename_str,self)
		self.folderEdit = QtGui.QLineEdit(self.folder_str,self)
		
		##############################################

		# status info which button has been pressed
		self.motorstep_lbl = QtGui.QLabel("STEPPER micropostion:", self)
		self.motorstep_lbl.setStyleSheet("color: blue")
		self.upButton = QtGui.QPushButton(u'\u25b2',self)
		self.set_bstyle_v1(self.upButton)
		self.downButton = QtGui.QPushButton(u'\u25bc',self)
		self.set_bstyle_v1(self.downButton)
		self.moverelButton = QtGui.QPushButton('Move rel',self)
		self.moveabsButton = QtGui.QPushButton('Move abs',self)
		#self.moveabsButton.setStyleSheet('QPushButton {color: red}')
		self.moverelEdit = QtGui.QLineEdit(str(100),self)
		self.moveabsEdit = QtGui.QLineEdit(str(1000),self)
		self.moveButton = QtGui.QPushButton('Move to nm',self)
		self.moveButton.setStyleSheet('QPushButton {color: magenta}')
		self.moveEdit = QtGui.QLineEdit("",self)
		self.abortButton = QtGui.QPushButton('ABORT',self)
		self.abortButton.setEnabled(False)	
		
		##############################################

		self.lcd1 = QtGui.QLCDNumber(self)
		self.lcd1.setStyleSheet("color: black")
		self.lcd1.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd1.setNumDigits(6)
		self.lcd1.display(str(config_zeiss.Last_position_lambda[0]))
		
		self.lcd2 = QtGui.QLCDNumber(self)
		self.lcd2.setStyleSheet("color: magenta")
		self.lcd2.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd2.setNumDigits(6)
		#self.lcd2.display(str(config_zeiss.Last_position_lambda[1]))
		#self.lcd2.setFixedWidth(120)

		self.lcd3 = QtGui.QLCDNumber(self)
		self.lcd3.setStyleSheet("color: red")
		self.lcd3.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd3.setNumDigits(11)
		self.lcd3.display(self.timestr)
		self.lcd3.setFixedHeight(70)
		##############################################

		# status info which button has been pressed
		self.alignEdit = QtGui.QLineEdit("",self)
		self.setzeroButton = QtGui.QPushButton('-> nm',self)
		self.setzeroButton.setStyleSheet('QPushButton {color: magenta}')
		self.setzeroButton.setFixedWidth(70)
		#self.setzeroButton.setStyleSheet('QPushButton {color: black}')
		
		##############################################
		
		self.timetrace_str = QtGui.QLabel("TIME trace for storing plots and data:", self)
		self.timetrace_str.setStyleSheet("color: blue")	

		################### MENU BARS START ##################
		
		#self.MyBar = QtGui.QMenuBar(self)
		fileMenu = self.MyBar.addMenu("File")
		fileSaveSet = fileMenu.addAction("Save settings")
		fileSaveSet.triggered.connect(self.set_save)
		fileSaveSet.setShortcut('Ctrl+S')
		fileSavePlt = fileMenu.addAction("Save plots")
		fileSavePlt.triggered.connect(self.set_save_plots)
		fileSavePlt.setShortcut('Ctrl+P')
		fileClose = fileMenu.addAction("Close")        
		fileClose.triggered.connect(self.close) # triggers closeEvent()
		fileClose.setShortcut('Ctrl+X')
		
		modeMenu = self.MyBar.addMenu("Serial")
		self.conMode = modeMenu.addAction("Connect to serial")
		self.conMode.triggered.connect(self.set_connect)
		self.disconMode = modeMenu.addAction("Disconnect from serial")
		self.disconMode.triggered.connect(self.set_disconnect)
		
		serialMenu = self.MyBar.addMenu("Ports")
		self.serialZaber = serialMenu.addAction("Zaber X-MCB")
		self.serialZaber.triggered.connect(self.ZaberDialog)
		self.serialSr510 = serialMenu.addAction("SR510")
		self.serialSr510.triggered.connect(self.Sr510Dialog)
		
		calibMenu = self.MyBar.addMenu("Calib")
		self.calibLambdaZeiss = calibMenu.addAction("Load lambda calib file")
		self.calibLambdaZeiss.setShortcut('Ctrl+L')
		self.calibLambdaZeiss.triggered.connect(self.loadCalibLambdaDialog)
		
		self.calibSlitZeiss = calibMenu.addAction("Load slit calib file")
		self.calibSlitZeiss.setShortcut('Ctrl+T')
		self.calibSlitZeiss.triggered.connect(self.loadCalibSlitDialog)
		
		################### MENU BARS END ##################
		
		#g4_0=QtGui.QGridLayout()
		#g4_0.addWidget(self.MyBar,0,0)
		
		g7_3 = QtGui.QHBoxLayout()
		g7_3.addWidget(lbl_zeiss)
		
		g7_1 = QtGui.QGridLayout()
		g7_1.addWidget(start_lbl,0,1)
		g7_1.addWidget(stop_lbl,0,2)
		g7_1.addWidget(step_lbl,0,3)
		g7_1.addWidget(dwelltime,0,4)
		g7_1.addWidget(actual_lbl,0,5)
		g7_1.addWidget(lambda_lbl,1,0)
		g7_1.addWidget(slit_lbl,2,0)
		for tal in range(4):
			g7_1.addWidget(self.Range_lambdaEdit[tal],1,tal+1)
			g7_1.addWidget(self.Range_slitEdit[tal],2,tal+1)
		for tal in range(2): 
			g7_1.addWidget(self.lcd_actual[tal],1+tal,5)
		
		g7_2 = QtGui.QGridLayout()
		g7_2.addWidget(self.startscanButton,0,0)
		g7_2.addWidget(self.pausescanButton,0,1)
		g7_2.addWidget(self.infoCalibButton,0,2)
		
		g7_4 = QtGui.QHBoxLayout()
		g7_4.addWidget(schroll_lbl)
		g7_4.addWidget(self.combo2)
		
		v7 = QtGui.QVBoxLayout()
		v7.addLayout(g7_3)
		v7.addLayout(g7_1)
		v7.addLayout(g7_4)
		v7.addLayout(g7_2)
		
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
		
		g3_0 = QtGui.QSplitter(QtCore.Qt.Horizontal)
		g3_0.addWidget(lb3)
		g3_0.addWidget(self.cb3)
		g3_1=QtGui.QSplitter(QtCore.Qt.Vertical)
		g3_1.addWidget(self.alignEdit)
		g3_1.addWidget(self.setzeroButton)
		g3_2=QtGui.QSplitter(QtCore.Qt.Horizontal)
		g3_2.addWidget(g3_1)
		g3_2.addWidget(self.lcd2)
		h4 = QtGui.QSplitter(QtCore.Qt.Vertical)
		h4.addWidget(g3_0)
		h4.addWidget(g3_2)

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
		g0_5.addWidget(self.abortButton)
		h1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
		h1.addWidget(g0_5)
		h1.addWidget(g0_3)
		h1.addWidget(g0_4)
		v1 = QtGui.QSplitter(QtCore.Qt.Vertical)
		v1.addWidget(g0_0)
		v1.addWidget(h0)
		v1.addWidget(h1)
		
		g9_0 = QtGui.QSplitter(QtCore.Qt.Vertical)
		g9_0.addWidget(self.timetrace_str)
		g9_0.addWidget(self.lcd3)
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		v_all = QtGui.QVBoxLayout()
		#v_all.addLayout(g4_0)
		#v_all.addLayout(v6)
		v_all.addLayout(v7)
		v_all.addWidget(v8)
		v_all.addWidget(h4)
		v_all.addWidget(v1)
		v_all.addWidget(g9_0)
		
		# set graph  and toolbar to a new vertical group vcan
		pw = pg.GraphicsLayoutWidget()
		pw.setFixedWidth(750)
		
		self.p0 = pw.addPlot()
		self.p0.setTitle('Step WAVELENGTH')
		self.p0.setLabel('left', 'X-MCB micropos.')
		self.p0.setLabel('bottom', 'no. of moves')
		
		self.p1 = pw.addPlot()
		self.p1.setTitle(''.join(["2-D scan, Jet colormap"]))
		self.p1.setLabel('left', "slit width", units='m', color='red')
		self.p1.setLabel('bottom', u'\u03bb', units='m', color='red')
		self.p1.enableAutoRange()
		
		pw.nextRow()
		self.p2 = pw.addPlot()
		self.p2.setTitle('Wavelength calib')
		self.p2.setLabel('left', u'\u03bb', units='m')
		self.p2.setLabel('bottom', 'X-MCB micropos.')
		
		self.p3 = pw.addPlot()
		self.p3.setTitle('Scan')		
		self.p3.setLabel('left', u'\u03bb', units='m', color='red')
		self.p3.setLabel('bottom', 'elapsed time', units='s')
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		h_all = QtGui.QHBoxLayout()
		h_all.addLayout(v_all)
		h_all.addWidget(pw)
		self.setLayout(h_all)

		########################################
		
		# PLOT 1 settings
		# create plot and add it to the figure canvas
		self.curve0=self.p0.plot(pen='r')
		# create plot and add it to the figure
		self.p0_1 = pg.ViewBox()
		self.curve7=pg.PlotCurveItem(pen='y')
		self.p0_1.addItem(self.curve7)
		# connect respective axes to the plot 
		self.p0.showAxis('right')
		self.p0.getAxis('right').setLabel("voltage", units="V", color='yellow')
		self.p0.scene().addItem(self.p0_1)
		self.p0.getAxis('right').linkToView(self.p0_1)
		self.p0_1.setXLink(self.p0)
		# Use automatic downsampling and clipping to reduce the drawing load
		self.p0.setDownsampling(mode='peak')
		self.p0.setClipToView(True)
		
		
		# PLOT 2 settings
		#self.curve8 = self.p8.plot(pen='w', symbol='s', symbolPen='w', symbolBrush='k', symbolSize=4)
		#self.curve9 = self.p8.plot(pen='k', symbol='s', symbolPen='k', symbolSize=6)
		self.curve8 = self.p1.plot(pen='w')
		self.curve9 = self.p1.plot(pen='k')
		#self.p1.setDownsampling(mode='peak')
		#self.p1.setClipToView(True)
		
		
		# PLOT 3 settings	
		self.p2.addLegend()
		self.curve2=self.p2.plot(pen='m',name='raw data')
		self.curve1=self.p2.plot(pen='b',name='spline')
		self.curve3=self.p2.plot(pen='w',name='scan')
		
		
		# PLOT 4 settings
		# create plot and add it to the figure canvas
		self.curve4=self.p3.plot(pen='r')
		# create plot and add it to the figure
		self.p4 = pg.ViewBox()
		self.curve5=pg.PlotCurveItem(pen='y')
		self.curve6=pg.PlotCurveItem()
		self.p4.addItem(self.curve5)
		self.p4.addItem(self.curve6)
		# connect respective axes to the plot 
		self.p3.showAxis('right')
		self.p3.getAxis('right').setLabel("voltage", units='V', color='yellow')
		self.p3.scene().addItem(self.p4)
		self.p3.getAxis('right').linkToView(self.p4)
		self.p4.setXLink(self.p3)
		# Use automatic downsampling and clipping to reduce the drawing load
		self.p3.setDownsampling(mode='peak')
		self.p3.setClipToView(True)
		
		#########################################

		self.allEditFields(False)

		self.startscanButton.clicked.connect(self.set_scan)
		self.pausescanButton.clicked.connect(self.set_pause)
		
		self.setzeroButton.clicked.connect(self.set_zero)
		#self.combo1.activated[str].connect(self.onActivated1)
		
		self.upButton.clicked.connect(self.move_jog)
		self.downButton.clicked.connect(self.move_jog)
		self.moverelButton.clicked.connect(self.move_rel)
		self.moveabsButton.clicked.connect(self.move_abs)
		self.moveButton.clicked.connect(self.move_to)
		self.abortButton.clicked.connect(self.set_abort)
		self.cb3.activated[str].connect(self.onActivated3)
		self.infoCalibButton.clicked.connect(self.showInfoCalibFiles)
		self.combo2.activated[str].connect(self.onActivated2)
		
		#self.move(0,175)
		#self.setWindowTitle('Zeiss spectrometer')
		self.show()
		self.adjust_mode="wavelength"
		self.all_pos=[config_zeiss.Last_position_lambda[0]]
		self.bad_sr510_vals=False
		self.bad_zaber_vals=False
		
		lcd_obj=type('lcd_obj',(object,),{'pos_wl':config_zeiss.Last_position_lambda[1], 'pos_slit':config_zeiss.Last_position_slit[1]})
		self.update_lcd(lcd_obj)
		
		lcd_obj=type('lcd_obj',(object,),{'min_pos':config_zeiss.Last_position_lambda[0], 'pos_val':config_zeiss.Last_position_lambda[1]})
		self.update_pos_lcd(lcd_obj)

	##########################################
	
	def ZaberDialog(self):

		text, ok = QtGui.QInputDialog.getText(self, 'Serial Port Dialog','Enter Zaber X-MCB serial:', text=self.zaberport_str)
		if ok:
			self.zaberport_str = str(text)
	
	def Sr510Dialog(self):

		text, ok = QtGui.QInputDialog.getText(self, 'Serial Port Dialog','Enter SR510 serial:', text=self.sr510port_str)
		if ok:
			self.sr510port_str = str(text)
	
	
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
		
		QtGui.QMessageBox.information(self, "Drive files information",''.join(["<font color=\"black\">Calib lambda: </font> <font color=\"green\">",tail1,"< </font> <br> <font color=\"black\">Calib lambda range: </font> <font color=\"green\">",str(y0[0])," to ",str(y0[-1])," nm < </font> <br> <font color=\"black\">Calib slit:< </font> <font color=\"blue\">",tail2,"<  </font> <br> <font color=\"black\">Calib slit range: </font> <font color=\"blue\">",str(y1[0])," to ",str(y1[-1])," mm <"]))
		
	'''
	def showInfoCalibFiles():
		
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Information)

		msg.setText("This is a message box")
		msg.setInformativeText("This is additional information")
		msg.setWindowTitle("MessageBox demo")
		msg.setDetailedText("The details are as follows:")
		msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

		retval = msg.exec_()
	'''
	
	
	
	def loadCalibLambdaDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file','Calib_files')
		old_calib=self.calibfile_lambda_str
		if fname:
			try:
				self.calibfile_lambda_str = str(fname)
				self.showInfoCalibFiles()
			except ValueError as e:
				self.calibfile_lambda_str = old_calib
				QtGui.QMessageBox.warning(self, 'Message', "Something is wrong with lambda calib file! Do you have a file with 2 columns, no headers, and all inputs are digits?")
				return
			if self.adjust_mode=="wavelength":
				self.set_lambda_calib_data()
		
	def loadCalibSlitDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file','Calib_files')
		old_calib=self.calibfile_slit_str
		if fname:
			try:
				self.calibfile_slit_str = str(fname)
				self.showInfoCalibFiles()
			except ValueError as e:
				self.calibfile_slit_str = old_calib
				QtGui.QMessageBox.warning(self, 'Message', "Something is wrong with slit calib file! Do you have a file with 2 columns, no headers, and all inputs are digits?")
				return
			if self.adjust_mode=="slit":
				self.set_slit_calib_data()
		
	def update_lcd(self,pyqt_object):
		
		# i and j are always in meters
		if hasattr(pyqt_object, 'pos_wl'):
			self.lcd_actual[0].display(str(pyqt_object.pos_wl))
		if hasattr(pyqt_object, 'pos_slit'):
			self.lcd_actual[1].display(str(pyqt_object.pos_slit))
	
	def update_pos_lcd(self,pyqt_object):
		
		# i and j are always in meters
		if hasattr(pyqt_object, 'min_pos'):
			self.lcd1.display(str(pyqt_object.min_pos))
		if hasattr(pyqt_object, 'pos_val'):
			self.lcd2.display(str(pyqt_object.pos_val))
		
		
		
	def set_connect(self):
		
		try:
			self.Za = ZaberXmcb_ascii.Zaber_Xmcb(self.zaberport_str)
		except Exception as e:
			print e
			QtGui.QMessageBox.warning(self, 'Message',"No response from the Zaber serial port! Check serial port name.")
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
			
			self.Za.set_Maximum_Position(1,2,max_pos_slit)
			self.Za.set_Minimum_Position(1,2,min_pos_slit)
			self.Za.set_Hold_Current(1,2,hc)
			self.Za.set_Running_Current(1,2,rc)
			self.Za.set_Max_Speed(1,2,ms)

			micstep_lambda=self.Za.return_Microstep_Resolution(1,1)
			sc=self.Za.return_System_Current(1)
			# TURN ON/OFF ALERTS
			if self.Za.return_Alert(1)==0:
				self.Za.set_Alert(1,1)
			
			self.Za.set_Current_Position(1,1,config_zeiss.Last_position_lambda[0])
			self.Za.set_Current_Position(1,2,config_zeiss.Last_position_slit[0])
		except Exception as e:
			print e
			self.Za.close()
			QtGui.QMessageBox.warning(self, 'Message',"No response from the Zaber stepper! Is stepper powered and connected to the serial?")
			return
			
		hc_str=''.join([str(hc*25e-3)," / ",str(rc*25e-3)," Amps" ])
		print "Hold / Running current:", hc_str
		sys_str=''.join([ str(sc), " Amps" ])
		print "System current (0-5):", sys_str
		ms_str=''.join([str(ms/1.6384), " microsteps/s"])
		print "Max speed:", ms_str
		micstep_str=''.join([str(micstep_lambda), " microsteps/step"])
		print "Microstep resolution:", str(micstep_str)
		pos_lambda_str=''.join([str(min_pos_lambda)," to ", str(max_pos_lambda)," microsteps"])
		print u"Stepper range for lambda:", pos_lambda_str
		pos_slit_str=''.join([str(min_pos_slit)," to ", str(max_pos_slit)," microsteps"])
		print "Stepper range for slits:", pos_slit_str
		
		
		try:
			self.Sr510 = SR510.SR510(self.sr510port_str)
		except Exception as e:
			print e
			QtGui.QMessageBox.warning(self, 'Message',"SR510 serial port is not present! Check serial port name.")	
			return
		
		try:
			self.Sr510.set_timeout(1) # wait maximum 1 sec for response
			self.Sr510.set_wait(1) # wait 1*4ms between characters
			sr510_volt = self.Sr510.return_voltage()
		except Exception as e:
			print e
			self.Sr510.close()
			self.Za.close()
			QtGui.QMessageBox.warning(self, 'Message',"SR510 serial port does not respond! Is the lock-in powered and connected to the serial?")	
			return
		
		self.allEditFields(True)
		self.conMode.setEnabled(False)
		self.serialZaber.setEnabled(False)
		self.serialSr510.setEnabled(False)

		# constants
		self.some_volts=[float("%.3g"%sr510_volt)]
		self.set_lambda_calib_data()
		self.set_slit_calib_data()
		
		if self.adjust_mode=="wavelength":
			self.all_pos=[config_zeiss.Last_position_lambda[0]]
		elif self.adjust_mode=="slit":
			self.all_pos=[config_zeiss.Last_position_slit[0]]
		
		self.timer = QTimer(self)
		self.connect(self.timer, SIGNAL("timeout()"), self.set_disconnect)
		self.timer.setSingleShot(True)
		self.timer.start(1000*60*10)
		
		
		
		
	def set_disconnect(self):
		
		self.Sr510.close()
		self.Za.set_Hold_Current(1,1,0)
		self.Za.set_Hold_Current(1,2,0)
		self.Za.close()
		
		self.allEditFields(False)
		self.conMode.setEnabled(True)
		self.serialZaber.setEnabled(True)
		self.serialSr510.setEnabled(True)
	
	def allEditFields(self,trueorfalse):
		
		#self.dwelltimeEdit_ard.setEnabled(trueorfalse)
		#self.combo1.setEnabled(trueorfalse)
		self.disconMode.setEnabled(trueorfalse)
		self.calibLambdaZeiss.setEnabled(trueorfalse)
		self.calibSlitZeiss.setEnabled(trueorfalse)
		for tal in range(4):
			self.Range_lambdaEdit[tal].setEnabled(trueorfalse)
			self.Range_slitEdit[tal].setEnabled(trueorfalse)
			
		self.startscanButton.setEnabled(trueorfalse)
		#self.pausescanButton.setEnabled(trueorfalse)
		
		self.alignEdit.setEnabled(trueorfalse)
		self.setzeroButton.setEnabled(trueorfalse)
		self.filenameEdit.setEnabled(trueorfalse)
		self.folderEdit.setEnabled(trueorfalse)
		self.cb3.setEnabled(trueorfalse)
		self.infoCalibButton.setEnabled(trueorfalse)
		
		self.combo2.setEnabled(trueorfalse)
		self.upButton.setEnabled(trueorfalse)
		self.downButton.setEnabled(trueorfalse)
		self.moverelButton.setEnabled(trueorfalse)
		self.moveabsButton.setEnabled(trueorfalse)
		self.moveButton.setEnabled(trueorfalse)
		self.moverelEdit.setEnabled(trueorfalse)
		self.moveabsEdit.setEnabled(trueorfalse)
		self.moveEdit.setEnabled(trueorfalse)
		#self.abortButton.setEnabled(trueorfalse)

	##########################################

	def set_bstyle_v1(self,button):
		
		button.setStyleSheet('QPushButton {font-size: 25pt}')
		button.setFixedWidth(40)
		button.setFixedHeight(40)
  
	def set_lambda_calib_data(self):
		
		x=[]
		y=[]
		with open(self.calibfile_lambda_str, 'r') as thefile:
			for line in thefile:
				columns = line.split()
				x.extend([int(columns[0])])
				y.extend([round(float(columns[1]),1)])
		
		self.min_y_calib_lambda=min(y)
		self.max_y_calib_lambda=max(y)
		
		if self.adjust_mode=="wavelength":
			self.curve2.setData(x,1e-9*numpy.array(y))
			# Be careful with numpy.arange due to floating point errors. 
			# Always multiply up to integers and then divide back afterwards.
			wv_scanlist_=numpy.arange(int(10*y[0]),int(10*(y[-1]+0.1)),int(10*0.1))
			wv_scanlist=wv_scanlist_/10.0
			#spline
			wv_curve=scipy.interpolate.splrep(y, x, k=3, s=0)
			#linear
			#wv_curve = scipy.interpolate.splrep(y, x, k=1, s=0)		
			positions = scipy.interpolate.splev(wv_scanlist, wv_curve, der=0)
			self.curve1.setData(positions,1e-9*numpy.array(wv_scanlist))
			
			my_pos = config_zeiss.Last_position_lambda[0]
			if my_pos<min(x) or my_pos>max(x):
				QtGui.QMessageBox.warning(self, 'Message', "Current lambda position is outside range of the calibration lambda file!")
				self.lcd2.display('-')
				self.lcd2.display('-')
				return 
			else:
				# Update the LCD display lcd2 with the wavelength which
				# corresponds to the saved Zaber microposition
				wv_curve2=scipy.interpolate.splrep(x, y, k=3, s=0)
				first_pos_val = round(scipy.interpolate.splev(my_pos, wv_curve2, der=0), 1)
				
				lcd_obj=type('lcd_obj',(object,),{'pos_wl':first_pos_val})
				self.update_lcd(lcd_obj)
				
				lcd_obj=type('lcd_obj',(object,),{'min_pos':my_pos, 'pos_val':first_pos_val})
				self.update_pos_lcd(lcd_obj)
				
				self.replace_line("config_zeiss.py",4,''.join(["Last_position_lambda=[",str(my_pos),",",str(first_pos_val),"]\n"]))
				imp.reload(config_zeiss)
			
			
	def set_slit_calib_data(self):
		
		x=[]
		y=[]
		with open(self.calibfile_slit_str, 'r') as thefile:
			for line in thefile:
				columns = line.split()
				x.extend([int(columns[0])])
				y.extend([round(float(columns[1]),2)])
		
		self.min_y_calib_slit=min(y)
		self.max_y_calib_slit=max(y)
		
		if self.adjust_mode=="slit":
			self.curve2.setData(x,1e-3*numpy.array(y))
			
			# Be careful with numpy.arange due to floating point errors. 
			# Always multiply up to integers and then divide back afterwards.
			slit_scanlist_=numpy.arange(int(100*y[0]),int(100*(y[-1]+0.01)),int(100*0.01))
			slit_scanlist=slit_scanlist_/100.0
			#spline
			slit_curve=scipy.interpolate.splrep(y, x, k=3, s=0)
			#linear
			#wv_curve = scipy.interpolate.splrep(y, x, k=1, s=0)		
			positions = scipy.interpolate.splev(slit_scanlist, slit_curve, der=0)
			self.curve1.setData(positions,1e-3*numpy.array(slit_scanlist))
			
			my_pos = config_zeiss.Last_position_slit[0]
			if my_pos<min(x) or my_pos>max(x):
				QtGui.QMessageBox.warning(self, 'Message', "Current slit position is outside range of the calibration slit file!")
				self.lcd1.display('-')
				self.lcd2.display('-')
				return 
			else:
				# Update the LCD display lcd2 with the wavelength which
				# corresponds to the saved Zaber microposition
				wv_curve2=scipy.interpolate.splrep(x, y, k=3, s=0)
				first_pos_val = round(scipy.interpolate.splev(my_pos, wv_curve2, der=0), 2)
				
				lcd_obj=type('lcd_obj',(object,),{'pos_slit':first_pos_val})
				self.update_lcd(lcd_obj)
				
				lcd_obj=type('lcd_obj',(object,),{'min_pos':my_pos, 'pos_val':first_pos_val})
				self.update_pos_lcd(lcd_obj)
				
				self.replace_line("config_zeiss.py",5,''.join(["Last_position_slit=[",str(my_pos),",",str(first_pos_val),"]\n"]))
				imp.reload(config_zeiss)
			
			
	def set_scan(self):
		
		# Check for possible name conflicts
		
		if str(self.filenameEdit.text()):
			saveinfile=''.join([str(self.filenameEdit.text()),self.timestr])
		else:
			saveinfile=''.join(["data_",self.timestr])
			
		if str(self.folderEdit.text()):
			if not os.path.isdir(str(self.folderEdit.text())):
				os.mkdir(str(self.folderEdit.text()))
			saveinfolder=''.join([str(self.folderEdit.text()),"/"])
		else:
			saveinfolder=""
			
		self.save_to_file=''.join([saveinfolder,saveinfile,".txt"])	
		
		self.all_time=[]
		self.all_wv=[]
		self.all_slit=[]
		self.all_volts=[]
		self.some_end_time=[]
		self.some_wv=[]
		self.some_slits=[]
		self.some_end_volts=[]
		self.curve3_val=[]
		self.curve3_pos=[]
		self.acc_time=[]
		self.acc_volt=[]
		self.acc_wl=[]
		self.acc_slit=[]
		
		self.curve3.clear()
		self.curve4.clear()
		self.curve5.clear()
		self.curve6.clear()
		self.curve8.clear()
		self.curve9.clear()
		
		try:
			start_wl = round(float(self.Range_lambdaEdit[0].text()),1) 
			stop_wl = round(float(self.Range_lambdaEdit[1].text()),1)
			step_wl = round(float(self.Range_lambdaEdit[2].text()),1) 
			dwell_wl = float(self.Range_lambdaEdit[3].text())
			
			start_slit = round(float(self.Range_slitEdit[0].text()),2) 
			stop_slit = round(float(self.Range_slitEdit[1].text()),2)
			step_slit = round(float(self.Range_slitEdit[2].text()),2) 
			dwell_slit = float(self.Range_slitEdit[3].text())
		except ValueError as e:
			print e
			QtGui.QMessageBox.warning(self, 'Message', "Only real decimal numbers are accepted as scan parameters!")
			return
		
		#for ff,pp in zip(wv_scanlist,positions):
		if start_wl<self.min_y_calib_lambda or start_wl>self.max_y_calib_lambda or stop_wl<self.min_y_calib_lambda or stop_wl>self.max_y_calib_lambda:
			QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid wavelength scan range is from ',str(self.min_y_calib_lambda),' nm to ',str(self.max_y_calib_lambda),' nm.' ]) )
			return
		if start_slit<self.min_y_calib_slit or start_slit>self.max_y_calib_slit or stop_slit<self.min_y_calib_slit or stop_slit>self.max_y_calib_slit:
			QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid slit width scan range is from ',str(self.min_y_calib_slit),' mm to ',str(self.max_y_calib_slit),' mm.' ]) )
			return
			
		self.timer.stop()
		sender = self.sender()
		
		self.allEditFields(False)
		self.abortButton.setEnabled(True)
		self.pausescanButton.setEnabled(True)
		
		# Initial read of the config file
		if int(100*start_slit)==int(100*stop_slit):
			xf = Methods_for_XYscan.Myrange(start_wl,stop_wl,step_wl,'wavelength')
			wv_fields=xf.myrange() # wavelength movement
			self.all_xy(wv_fields*1e-9, len(wv_fields)*[start_slit*1e-3]) # convert to meters
			
		elif int(10*start_wl)==int(10*stop_wl):
			xs = Methods_for_XYscan.Myrange(start_slit,stop_slit,step_slit,'slit')
			slit_fields=xs.myrange() # slit movement
			self.all_xy(len(slit_fields)*[start_wl*1e-9], slit_fields*1e-3) # convert to meters
		
		else:
			sm = Methods_for_XYscan.Scan_methods(start_wl,stop_wl,step_wl,'wavelength', start_slit,stop_slit,step_slit,'slit')
			wl_vals, slit_vals = sm.run('xsnake')
			self.all_xy(wl_vals*1e-9, slit_vals*1e-3) # convert to meters
		
		setscan_obj=type('setscan_obj',(object,),{'zaber':self.Za, 'sr510':self.Sr510, 'calib_file_lambda':self.calibfile_lambda_str, 'calib_file_slit':self.calibfile_slit_str,'start_wl':start_wl,'stop_wl':stop_wl,'step_wl':step_wl,'dwell_wl':dwell_wl,'adjust_mode':self.adjust_mode,'start_slit':start_slit,'stop_slit':stop_slit,'step_slit':step_slit,'dwell_slit':dwell_slit,'save_to_file':self.save_to_file })
		self.get_zaber_Thread=zaber_Thread(sender.text(),setscan_obj)
		self.connect(self.get_zaber_Thread,SIGNAL('update_pos_lcd(PyQt_PyObject)'), self.update_pos_lcd)
		self.connect(self.get_zaber_Thread,SIGNAL('update_lcd(PyQt_PyObject)'), self.update_lcd)
		self.connect(self.get_zaber_Thread,SIGNAL("curve3_data(PyQt_PyObject)"),self.curve3_data)
		self.connect(self.get_zaber_Thread,SIGNAL("time_data(PyQt_PyObject)"),self.time_data)
		self.connect(self.get_zaber_Thread,SIGNAL("volt_data(PyQt_PyObject)"),self.volt_data)
		self.connect(self.get_zaber_Thread,SIGNAL('bad_sr510_val(PyQt_PyObject)'), self.bad_sr510_val)
		self.connect(self.get_zaber_Thread,SIGNAL('bad_zaber_val(PyQt_PyObject)'), self.bad_zaber_val)
		self.connect(self.get_zaber_Thread,SIGNAL('make_3Dplot()'), self.make_3Dplot)
		self.connect(self.get_zaber_Thread,SIGNAL('finished()'), self.set_finished)
		
		self.get_zaber_Thread.start()
			
			
	def onActivated2(self, text):
		
		my_string=str(text)
		self.schroll_pts=int(my_string.split()[0])
		
		
	def onActivated3(self, text):
		
		self.curve3.clear()
		self.curve0.clear()
		self.curve7.clear()
		self.some_volts=[self.some_volts[-1]]
			
		if str(text)=="wavelength":
			self.adjust_mode="wavelength"
			self.p0.setTitle('Step WAVELENGTH')
			self.p2.setTitle('Wavelength calib')
			self.p3.setLabel('left', u'\u03bb[nm]', units='m', color='red')
			self.setzeroButton.setText("-> nm")
			self.moveButton.setText("Move to nm")
			self.all_pos=[config_zeiss.Last_position_lambda[0]]
			self.set_lambda_calib_data()
			
		elif str(text)=="slit":
			self.adjust_mode="slit"
			self.p0.setTitle('Step SLIT')
			self.p2.setTitle('Slit width calib')
			self.p3.setLabel('left', 'slit width', units='m', color='red')
			self.setzeroButton.setText("-> mm")
			self.moveButton.setText("Move to mm")
			self.all_pos=[config_zeiss.Last_position_slit[0]]	
			self.set_slit_calib_data()
			
		else:
			pass
		
		
		
		
		
	def set_abort(self):
		
		self.get_zaber_Thread.abort()
		
		self.allEditFields(True)
		self.abortButton.setEnabled(False)
		self.pausescanButton.setEnabled(False)
		
		
		
		
	def set_pause(self):
		
		sender=self.sender()

		self.get_zaber_Thread.pause()
		
		self.allEditFields(False)
		self.abortButton.setEnabled(False)
		
		if sender.text()=="Continue scan":
			self.pausescanButton.setText("Pause scan")
			self.abortButton.setEnabled(True)
		elif sender.text()=="Pause scan":
			self.pausescanButton.setText("Continue scan")
			self.abortButton.setEnabled(False)
	
	
	def set_zero(self):
		
		if self.adjust_mode=="wavelength":
			try:
				move_num=round(float(self.alignEdit.text()),1)
			except ValueError as e:
				QtGui.QMessageBox.warning(self, 'Message', "Only real decimal numbers are accepted as a wavelength!")
				return
				
			if move_num<self.min_y_calib_lambda or move_num>self.max_y_calib_lambda:
				QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid wavelength range is from ',str(self.min_y_calib_lambda),' nm to ',str(self.max_y_calib_lambda),' nm.' ]) )
				return
			else:
				self.timer.stop()
				sender = self.sender()
				setzero_obj=type('setzero_obj',(object,),{'zaber':self.Za, 'sr510':self.Sr510, 'adjust_mode':self.adjust_mode, 'calib_file':self.calibfile_lambda_str, 'move_num':move_num})
				self.get_zaber_Thread=zaber_Thread(sender.text(),setzero_obj)
		
		elif self.adjust_mode=="slit":
			try:
				move_num=round(float(self.alignEdit.text()),2)
			except ValueError as e:
				QtGui.QMessageBox.warning(self, 'Message', "Only real decimal numbers are accepted as a slit width!")
				return
				
			if move_num<self.min_y_calib_slit or move_num>self.max_y_calib_slit:
				QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid slit range is from ',str(self.min_y_calib_slit),' mm to ',str(self.max_y_calib_slit),' mm.' ]) )
				return
			else:
				self.timer.stop()
				sender = self.sender()
				setzero_obj=type('setzero_obj',(object,),{'zaber':self.Za, 'sr510':self.Sr510, 'adjust_mode':self.adjust_mode, 'calib_file':self.calibfile_slit_str, 'move_num':move_num})
				self.get_zaber_Thread=zaber_Thread(sender.text(),setzero_obj)
		
		self.connect(self.get_zaber_Thread,SIGNAL('update_pos_lcd(PyQt_PyObject)'), self.update_pos_lcd)
		self.connect(self.get_zaber_Thread,SIGNAL('update_lcd(PyQt_PyObject)'), self.update_lcd)
		self.connect(self.get_zaber_Thread,SIGNAL('more_tals(PyQt_PyObject)'),self.more_tals)
		self.connect(self.get_zaber_Thread,SIGNAL('bad_sr510_val(PyQt_PyObject)'), self.bad_sr510_val)
		self.connect(self.get_zaber_Thread,SIGNAL('bad_zaber_val(PyQt_PyObject)'), self.bad_zaber_val)
		self.connect(self.get_zaber_Thread,SIGNAL('finished()'), self.set_finished)

		self.get_zaber_Thread.start()
		
		
		
	def move_to(self):
		
		if self.adjust_mode=="wavelength":
			try:
				move_num = round(float(self.moveEdit.text()),1)
			except ValueError as e:
				QtGui.QMessageBox.warning(self, 'Message', "Only real decimal numbers are accepted as a wavelength!")
				return
			
			if move_num<self.min_y_calib_lambda or move_num>self.max_y_calib_lambda:
				QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid wavelength range is from ',str(self.min_y_calib_lambda),' nm to ',str(self.max_y_calib_lambda),' nm.' ]) )
				return 
			else:
				self.timer.stop()
				sender = self.sender()
				moveto_obj=type('moveto_obj',(object,),{'zaber':self.Za, 'sr510':self.Sr510, 'adjust_mode':self.adjust_mode, 'calib_file':self.calibfile_lambda_str, 'move_num':move_num})
				self.get_zaber_Thread=zaber_Thread(sender.text(),moveto_obj)
		
		elif self.adjust_mode=="slit":
			try:
				move_num = round(float(self.moveEdit.text()),2)
			except ValueError as e:
				QtGui.QMessageBox.warning(self, 'Message', "Only real decimal numbers are accepted as a slit width!")
				return 
			
			if move_num<self.min_y_calib_slit or move_num>self.max_y_calib_slit:
				QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid slit range is from ',str(self.min_y_calib_slit),' mm to ',str(self.max_y_calib_slit),' mm.' ]) )
				return 
			else:
				self.timer.stop()
				sender = self.sender()
				moveto_obj=type('moveto_obj',(object,),{'zaber':self.Za, 'sr510':self.Sr510, 'adjust_mode':self.adjust_mode, 'calib_file':self.calibfile_slit_str, 'move_num':move_num})
				self.get_zaber_Thread=zaber_Thread(sender.text(),moveto_obj)
		
		self.allEditFields(False)
		self.abortButton.setEnabled(True)
		
		self.connect(self.get_zaber_Thread,SIGNAL('update_pos_lcd(PyQt_PyObject)'), self.update_pos_lcd)
		self.connect(self.get_zaber_Thread,SIGNAL('update_lcd(PyQt_PyObject)'), self.update_lcd)
		self.connect(self.get_zaber_Thread,SIGNAL('more_tals(PyQt_PyObject)'),self.more_tals)
		self.connect(self.get_zaber_Thread,SIGNAL('bad_sr510_val(PyQt_PyObject)'), self.bad_sr510_val)
		self.connect(self.get_zaber_Thread,SIGNAL('bad_zaber_val(PyQt_PyObject)'), self.bad_zaber_val)
		self.connect(self.get_zaber_Thread,SIGNAL('finished()'), self.set_finished)
		
		self.get_zaber_Thread.start()
		
	def move_rel(self):
		
		try:
			move_num = int(self.moverelEdit.text())
		except ValueError as e:
			QtGui.QMessageBox.warning(self, 'Message', "Only real decimal numbers accepted!")
			return 
		
		if self.adjust_mode=="wavelength":
			# update the lcd motorstep position
			validrange_min, validrange_max=self.Validrange_lambda
			move_tot = move_num+self.all_pos[-1]
			
			if move_tot<validrange_min or move_tot>validrange_max:
				QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid wavelength range is from ',str(validrange_min),' to ',str(validrange_max),' microsteps.' ]) )
				return 
			else:
				self.timer.stop()
				sender = self.sender()
				moverel_obj=type('moverel_obj',(object,),{'zaber':self.Za, 'sr510':self.Sr510, 'adjust_mode':self.adjust_mode, 'calib_file':self.calibfile_lambda_str, 'move_num':move_num})
				self.get_zaber_Thread=zaber_Thread(sender.text(),moverel_obj)
				
		elif self.adjust_mode=="slit":
			# update the lcd motorstep position
			validrange_min, validrange_max=self.Validrange_slit
			move_tot = move_num+self.all_pos[-1]
			
			if move_tot<validrange_min or move_tot>validrange_max:
				QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid slit range is from ',str(validrange_min),' to ',str(validrange_max),' microsteps.' ]) )
				return 
			else:
				self.timer.stop()
				sender = self.sender()
				moverel_obj=type('moverel_obj',(object,),{'zaber':self.Za, 'sr510':self.Sr510, 'adjust_mode':self.adjust_mode, 'calib_file':self.calibfile_slit_str, 'move_num':move_num})
				self.get_zaber_Thread=zaber_Thread(sender.text(),moverel_obj)
		
		self.allEditFields(False)
		self.abortButton.setEnabled(True)
		
		self.connect(self.get_zaber_Thread,SIGNAL('update_pos_lcd(PyQt_PyObject)'), self.update_pos_lcd)
		self.connect(self.get_zaber_Thread,SIGNAL('update_lcd(PyQt_PyObject)'), self.update_lcd)
		self.connect(self.get_zaber_Thread,SIGNAL('more_tals(PyQt_PyObject)'),self.more_tals)
		self.connect(self.get_zaber_Thread,SIGNAL('bad_sr510_val(PyQt_PyObject)'), self.bad_sr510_val)
		self.connect(self.get_zaber_Thread,SIGNAL('bad_zaber_val(PyQt_PyObject)'), self.bad_zaber_val)
		self.connect(self.get_zaber_Thread,SIGNAL('finished()'), self.set_finished)
		
		self.get_zaber_Thread.start()
		
		
				
	def move_abs(self):
		
		try:
			move_num = int(self.moveabsEdit.text())
		except ValueError as e:
			QtGui.QMessageBox.warning(self, 'Message', "Only real decimal numbers accepted!")
			return 
		
		if self.adjust_mode=="wavelength":
			# update the lcd motorstep position
			validrange_min, validrange_max=self.Validrange_lambda
			if move_num<validrange_min or move_num>validrange_max:
				QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid wavelength range is from ',str(validrange_min),' to ',str(validrange_max),' microsteps.' ]) )
				return 
			else:
				self.timer.stop()
				sender = self.sender()
				moveabs_obj=type('moveabs_obj',(object,),{'zaber':self.Za, 'sr510':self.Sr510, 'adjust_mode':self.adjust_mode, 'calib_file':self.calibfile_lambda_str, 'move_num':move_num})
				self.get_zaber_Thread=zaber_Thread(sender.text(),moveabs_obj)
		
		if self.adjust_mode=="slit":
			# update the lcd motorstep position
			validrange_min, validrange_max=self.Validrange_slit
			if move_num<validrange_min or move_num>validrange_max:
				QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid slit range is from ',str(validrange_min),' to ',str(validrange_max),' microsteps.' ]) )
				return 
			else:
				self.timer.stop()
				sender = self.sender()
				moveabs_obj=type('moveabs_obj',(object,),{'zaber':self.Za, 'sr510':self.Sr510, 'adjust_mode':self.adjust_mode, 'calib_file':self.calibfile_slit_str, 'move_num':move_num})
				self.get_zaber_Thread=zaber_Thread(sender.text(),moveabs_obj)
		
		self.allEditFields(False)
		self.abortButton.setEnabled(True)
		
		self.connect(self.get_zaber_Thread,SIGNAL('update_pos_lcd(PyQt_PyObject)'), self.update_pos_lcd)
		self.connect(self.get_zaber_Thread,SIGNAL('update_lcd(PyQt_PyObject)'), self.update_lcd)
		self.connect(self.get_zaber_Thread,SIGNAL("more_tals(PyQt_PyObject)"),self.more_tals)
		self.connect(self.get_zaber_Thread,SIGNAL('bad_sr510_val(PyQt_PyObject)'), self.bad_sr510_val)
		self.connect(self.get_zaber_Thread,SIGNAL('bad_zaber_val(PyQt_PyObject)'), self.bad_zaber_val)
		self.connect(self.get_zaber_Thread,SIGNAL('finished()'), self.set_finished)
		
		self.get_zaber_Thread.start()
		
		
	def move_jog(self):
		
		sender = self.sender()
		if sender.text()==u'\u25b2':
			move_num=10
		elif sender.text()==u'\u25bc':
			move_num=-10
		
		if self.adjust_mode=="wavelength":
			# update the lcd motorstep position
			validrange_min, validrange_max=self.Validrange_lambda
			move_tot = move_num+self.all_pos[-1]
			if move_tot<validrange_min or move_tot>validrange_max:
				QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid range is from ',str(validrange_min),' to ',str(validrange_max),' microsteps.' ]) )
				return 
			else:
				self.timer.stop()
				movejog_obj=type('movejog_obj',(object,),{'zaber':self.Za, 'sr510':self.Sr510, 'adjust_mode':self.adjust_mode, 'calib_file':self.calibfile_lambda_str})
				self.get_zaber_Thread=zaber_Thread(sender.text(),movejog_obj)
				
		if self.adjust_mode=="slit":
			# update the lcd motorstep position
			validrange_min, validrange_max=self.Validrange_slit
			move_tot = move_num+self.all_pos[-1]
			if move_tot<validrange_min or move_tot>validrange_max:
				QtGui.QMessageBox.warning(self, 'Message',''.join(['Valid range is from ',str(validrange_min),' to ',str(validrange_max),' microsteps.' ]) )
				return 
			else:
				self.timer.stop()
				movejog_obj=type('movejog_obj',(object,),{'zaber':self.Za, 'sr510':self.Sr510, 'adjust_mode':self.adjust_mode, 'calib_file':self.calibfile_slit_str})
				self.get_zaber_Thread=zaber_Thread(sender.text(),movejog_obj)
		
		self.connect(self.get_zaber_Thread,SIGNAL('update_pos_lcd(PyQt_PyObject)'), self.update_pos_lcd)
		self.connect(self.get_zaber_Thread,SIGNAL('update_lcd(PyQt_PyObject)'), self.update_lcd)
		self.connect(self.get_zaber_Thread,SIGNAL("more_tals(PyQt_PyObject)"),self.more_tals)
		self.connect(self.get_zaber_Thread,SIGNAL('bad_sr510_val(PyQt_PyObject)'), self.bad_sr510_val)
		self.connect(self.get_zaber_Thread,SIGNAL('bad_zaber_val(PyQt_PyObject)'), self.bad_zaber_val)
		self.connect(self.get_zaber_Thread,SIGNAL('finished()'), self.set_finished)

		self.get_zaber_Thread.start()
		
		
	def more_tals(self,more_tals_obj):
		
		self.some_volts.extend([ more_tals_obj.sr510_volt ])
		self.all_pos.extend([ more_tals_obj.min_pos ])    
		
		## Handle view resizing 
		def updateViews():
			## view has resized; update auxiliary views to match
			self.p0_1.setGeometry(self.p0.vb.sceneBoundingRect())
			#p3.setGeometry(p1.vb.sceneBoundingRect())

			## need to re-update linked axes since this was called
			## incorrectly while views had different shapes.
			## (probably this should be handled in ViewBox.resizeEvent)
			self.p0_1.linkedViewChanged(self.p0.vb, self.p0_1.XAxis)
			#p3.linkedViewChanged(p1.vb, p3.XAxis)
			
		updateViews()
		self.p0.vb.sigResized.connect(updateViews)
		self.curve0.setData(self.all_pos)
		self.curve7.setData(self.some_volts)
		
		
	def curve3_data(self,curve3_obj):
		
		if self.adjust_mode=="wavelength":
			self.curve3_val.extend([ curve3_obj.wl ])
			self.curve3_pos.extend([ curve3_obj.min_pos_wl ])
			self.curve3.setData(self.curve3_pos,1e-9*numpy.array(self.curve3_val))
			
		elif self.adjust_mode=="slit":
			self.curve3_val.extend([ curve3_obj.slit ])
			self.curve3_pos.extend([ curve3_obj.min_pos_slit ])
			self.curve3.setData(self.curve3_pos,1e-3*numpy.array(self.curve3_val))
		
	def time_data(self,volt_obj):
		
		self.some_end_time.extend([ volt_obj.time_elap ])
		self.some_wv.extend([ volt_obj.wl ])
		self.some_slits.extend([ volt_obj.slit ])
		self.some_end_volts.extend([ volt_obj.sr510_volt ])
		
		idx = numpy.where((numpy.array(self.some_end_time)>=min(self.acc_time)) & (numpy.array(self.some_end_time)<=max(self.acc_time)))[0]
		
		## update colormap
		
		my_norm = mpl.colors.Normalize(vmin=min(self.some_end_volts), vmax=max(self.some_end_volts))
		m = cm.ScalarMappable(norm=my_norm, cmap=mpl.cm.jet)
		my_color = m.to_rgba(self.some_end_volts,bytes=True)
		colors_=[]
		for i in my_color:
			colors_.append(pg.mkBrush(tuple(i)))

		self.curve9.setData(1e-9*numpy.array(self.some_wv), 1e-3*numpy.array(self.some_slits), symbolBrush=colors_, symbolSize=8)
		#self.curve9.setData(1e-9*numpy.array(self.some_wv), 1e-3*numpy.array(self.some_slits))
		self.curve6.setData([self.some_end_time[q] for q in idx], [self.some_end_volts[q] for q in idx])
		
		
	def all_xy(self,i,j):

		self.curve8.setData(i,j, symbol='o', symbolBrush='w', symbolSize=8)
		
		
	def volt_data(self,volt_obj):
		
		self.all_wv.extend([ volt_obj.wl ])
		self.all_slit.extend([ volt_obj.slit ])
		self.all_volts.extend([ volt_obj.sr510_volt ])
		self.all_time.extend([ volt_obj.time_elap ])
		
		# Update curve3 in different plot
		if len(self.all_time)>self.schroll_pts:
			self.acc_time[:-1] = self.acc_time[1:]  # shift data in the array one sample left
			self.acc_time[-1] = volt_obj.time_elap
			self.acc_volt[:-1] = self.acc_volt[1:]  # shift data in the array one sample left
			self.acc_volt[-1] = volt_obj.sr510_volt
			self.acc_wl[:-1] = self.acc_wl[1:]  # shift data in the array one sample left
			self.acc_wl[-1] = volt_obj.wl
			self.acc_slit[:-1] = self.acc_slit[1:]  # shift data in the array one sample left
			self.acc_slit[-1] = volt_obj.slit
		else:
			self.acc_time.extend([ volt_obj.time_elap ])
			self.acc_volt.extend([ volt_obj.sr510_volt ])
			self.acc_wl.extend([ volt_obj.wl ])
			self.acc_slit.extend([ volt_obj.slit ])
		
		## Handle view resizing 
		def updateViews():
			## view has resized; update auxiliary views to match
			self.p4.setGeometry(self.p3.vb.sceneBoundingRect())
			#p3.setGeometry(p1.vb.sceneBoundingRect())

			## need to re-update linked axes since this was called
			## incorrectly while views had different shapes.
			## (probably this should be handled in ViewBox.resizeEvent)
			self.p4.linkedViewChanged(self.p3.vb, self.p4.XAxis)
			#p3.linkedViewChanged(p1.vb, p3.XAxis)
			
		updateViews()
		self.p3.vb.sigResized.connect(updateViews)
		
		if self.adjust_mode=="wavelength":
			self.curve4.setData(self.acc_time, 1e-9*numpy.array(self.acc_wl))
		elif self.adjust_mode=="slit":
			self.curve4.setData(self.acc_time, 1e-3*numpy.array(self.acc_slit))
		self.curve5.setData(self.acc_time, self.acc_volt)
		
		
		
	def set_finished(self):
		
		if self.bad_zaber_vals==serial.SerialException:
			QtGui.QMessageBox.warning(self, 'Message',"Zaber serial severed. Closing the program..." )
			sys.exit()
		
		if self.bad_sr510_vals==serial.SerialException:
			QtGui.QMessageBox.warning(self, 'Message',"SR510 serial severed. Closing the program..." )
			sys.exit()
			
		self.pausescanButton.setEnabled(False)
		self.abortButton.setEnabled(False)
		
		if self.bad_zaber_vals==ValueError:
			QtGui.QMessageBox.warning(self, 'Message',"Zaber getting bad values. Closing the serial..." )
			self.bad_zaber_vals=False
			self.set_disconnect()
			return
		
		if self.bad_sr510_vals==ValueError:
			QtGui.QMessageBox.warning(self, 'Message',"SR510 getting bad values. Closing the serial..." )
			self.bad_sr510_vals=False
			self.set_disconnect()
			return
		
		self.allEditFields(True)
		self.timer.start(1000*60*10)
		
	
	def bad_zaber_val(self,pyqt_object):
		
		self.bad_zaber_vals=pyqt_object
	
	def bad_sr510_val(self,pyqt_object):
		
		self.bad_sr510_vals=pyqt_object
	
	def make_3Dplot(self):
		
		rg=make_3Dgui(self.save_to_file)
		rg.exec_()
		
		
	def closeEvent(self, event):
		
		if hasattr(self, 'Za'):
			reply = QtGui.QMessageBox.question(self, 'Message', "Quit scan now? The microstep position will be saved and the stepper hold current will be set to zero!", QtGui.QMessageBox.Yes |  QtGui.QMessageBox.No)
		else:
			reply = QtGui.QMessageBox.question(self, 'Message', "Quit scan now?", QtGui.QMessageBox.Yes |  QtGui.QMessageBox.No)
		
		
		if reply==QtGui.QMessageBox.Yes:
			
			if hasattr(self, 'Sr510'):
				if not hasattr(self, 'get_zaber_Thread'):
					if self.Sr510.is_open():
						self.Sr510.close()
				else:
					if self.get_zaber_Thread.isRunning():
						QtGui.QMessageBox.warning(self, 'Message', "Scan in progress. Cancel the scan then quit!")
						event.ignore()
						return
					else:
						if self.Sr510.is_open():
							self.Sr510.close()
			
			if hasattr(self, 'Za'):
				if not hasattr(self, 'get_zaber_Thread'):
					if self.Za.is_open():
						self.Za.set_Hold_Current(1,1,0)
						self.Za.set_Hold_Current(1,2,0)
						self.Za.close()
				else:
					if self.get_zaber_Thread.isRunning():
						QtGui.QMessageBox.warning(self, 'Message', "Scan in progress. Cancel the scan then quit!")
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
		
		if str(self.filenameEdit.text()):
			saveinfile=''.join([str(self.filenameEdit.text()),self.timestr])
		else:
			saveinfile=''.join(["data_",self.timestr])
			
		if str(self.folderEdit.text()):
			if not os.path.isdir(str(self.folderEdit.text())):
				os.mkdir(str(self.folderEdit.text()))
			saveinfolder=''.join([str(self.folderEdit.text()),"/"])
		else:
			saveinfolder=""
		
		save_plot1=''.join([saveinfolder,saveinfile,'_plots.png'])	

		# create an exporter instance, as an argument give it
		# the item you wish to export
		exporter = pg.exporters.ImageExporter(self.p0.scene())
		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_plot1)
		

	def set_save(self):
		
		self.timestr=time.strftime("%y%m%d-%H%M")
		
		self.replace_line("config_zeiss.py",0, ''.join(["Validrange_lambda=[",','.join([str(ii) for ii in [self.Validrange_lambda[0],self.Validrange_lambda[1]]]),"]\n"]) )
		self.replace_line("config_zeiss.py",1, ''.join(["Validrange_slit=[",','.join([str(ii) for ii in [self.Validrange_slit[0],self.Validrange_slit[1]]]),"]\n"]) )
		self.replace_line("config_zeiss.py",2, ''.join(["Range_lambda=[",','.join([str(self.Range_lambdaEdit[ii].text()) for ii in range(4)]),"]\n"]) )
		self.replace_line("config_zeiss.py",3, ''.join(["Range_slit=[",','.join([str(self.Range_slitEdit[ii].text()) for ii in range(4)]),"]\n"]) )
		self.replace_line("config_zeiss.py",4, ''.join(["Last_position_lambda=",str(config_zeiss.Last_position_lambda),"\n"]) )
		self.replace_line("config_zeiss.py",5, ''.join(["Last_position_slit=",str(config_zeiss.Last_position_slit),"\n"]) )
		self.replace_line("config_zeiss.py",6, ''.join(["Schroll_pts=",str(self.schroll_pts),"\n"]) )
		self.replace_line("config_zeiss.py",7, ''.join(["calibfile_lambda=\"",self.calibfile_lambda_str,"\"\n"]) )
		self.replace_line("config_zeiss.py",8, ''.join(["calibfile_slit=\"",self.calibfile_slit_str,"\"\n"]) )
		
		self.replace_line("config_zeiss.py",15, ''.join(["filename=\"",str(self.filenameEdit.text()),"\"\n"]) )
		self.replace_line("config_zeiss.py",16, ''.join(["foldername=\"",str(self.folderEdit.text()),"\"\n"]) )
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
		
		
		
		
		
		
		
		
class make_3Dgui(QtGui.QDialog):
	
	def __init__(self, save_to_file, parent=None):
		QtGui.QDialog.__init__(self, parent)
		#super(Window, self).__init__(parent)

		self.save_to_file = save_to_file
		# a figure instance to plot on
		self.figure=plt.figure(figsize=(10,8))

		# this is the Canvas Widget that displays the `figure`
		# it takes the `figure` instance as a parameter to __init__
		self.canvas = FigureCanvas(self.figure)

		# this is the Navigation widget
		# it takes the Canvas widget and a parent
		self.toolbar = NavigationToolbar(self.canvas, self)

		# Just some button connected to `plot` method
		#self.button = QtGui.QPushButton('Plot')
		#self.button.clicked.connect(self.plot)

		# set the layout
		layout = QtGui.QVBoxLayout()
		layout.addWidget(self.toolbar)
		layout.addWidget(self.canvas)
		self.plot()
		#layout.addWidget(self.button)
		self.setLayout(layout)
		self.setWindowTitle("3D surface plot")
		
		
	def plot(self):
		
		X_data=[]
		Y_data=[]
		Lockin_data=[]
		with open(self.save_to_file,'r') as thefile:
			for i in range(2):
				headers=thefile.readline()
			for lines in thefile:
				columns=lines.split()
				X_data.extend([ float(columns[0]) ])
				Y_data.extend([ float(columns[1]) ])
				Lockin_data.extend([ 1000*float(columns[2]) ])
				
		
		ax= self.figure.add_subplot(111, projection='3d')
		ax.plot_trisurf(X_data,Y_data,Lockin_data,cmap=cm.jet,linewidth=0.2)
		#ax=fig.gca(projection='2d')
		ax.set_xlabel(r'$\lambda$[nm]')
		ax.set_ylabel('Slit width[mm]')
		ax.set_zlabel('U[mV]')
		
		self.save_3Dplot=''.join([self.save_to_file[:-4],'_3D.png'])
		self.figure.savefig(self.save_3Dplot)
		
		#plt.show()

		# refresh canvas
		self.canvas.draw()


		
		
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
  
