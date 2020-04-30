import os, sys, re, serial, time, imp, yagmail
import numpy, functools
import scipy.interpolate
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.exporters
#from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, SIGNAL
import config_scan, config_calib, ESP300, MOTORSTEP_DRIVE
import Scatterometer_funksjoner_ver2

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
		self.analog_pin=argv[11]
		self.avg_pts=argv[12]
		self.dwell=argv[13]
		self.data_file=argv[14]
		self.sampl_vals=argv[15]
		self.inpl_vals=argv[16]
		self.outpl_vals=argv[17]
		self.A=argv[18]
		self.W=argv[19]
		
		self.sf=Scatterometer_funksjoner_ver2.Scatterometer_funksjoner()
    
	def __del__(self):
	  
	  self.wait()

	def abort_move(self):
		
		self.end_flag=True
		self.Md.stop_move()
		#self.Esp.set_stop()
	
	def make_header(self,drives_active):
		
		# create regular text file, make headings and close it
		with open(self.data_file, 'w') as thefile:
			thefile.write("Your edit line - do NOT delete this line\n")
			
		if len(drives_active)==1:
			if numpy.array_equal(drives_active,[0]):
				angs_to_move=["positioning Sampl ang."]
				with open(self.data_file, 'a') as thefile:
					thefile.write("Sampl ang.[dg], B[row,column], Bvals(1023=5V), M[row,column], Mvals\n")
			elif numpy.array_equal(drives_active,[1]):
				angs_to_move=["positioning In pl ang."]
				with open(self.data_file, 'a') as thefile:
					thefile.write("Inpl ang.[dg], B[row,column], Bvals(1023=5V), M[row,column], Mvals\n")	
			elif numpy.array_equal(drives_active,[2]):
				angs_to_move=["positioning Out pl ang."]
				with open(self.data_file, 'a') as thefile:
					thefile.write("Outpl ang.[dg], B[row,column], Bvals(1023=5V), M[row,column], Mvals\n")
		
		elif len(drives_active)==2:
			if numpy.array_equal(drives_active,[0,1]):
				angs_to_move=["positioning Sampl ang.","positioning In pl ang."]
				with open(self.data_file, 'a') as thefile:
					thefile.write("Sampl ang.[dg], In pl ang.[dg], B[row,column], Bvals(1023=5V), M[row,column], Mvals\n")
			elif numpy.array_equal(drives_active,[0,2]):
				angs_to_move=["positioning Sampl ang.","positioning Out pl ang."]
				with open(self.data_file, 'a') as thefile:
					thefile.write("Sampl ang.[dg], Out pl ang.[dg], B[row,column], Bvals(1023=5V), M[row,column], Mvals\n")	
			elif numpy.array_equal(drives_active,[1,2]):
				angs_to_move=["positioning In pl ang.","positioning Out pl ang."]
				with open(self.data_file, 'a') as thefile:
					thefile.write("Inpl ang.[dg], Outpl ang.[dg], B[row,column], Bvals(1023=5V), M[row,column], Mvals\n")
		
		elif len(drives_active)==3:
			if numpy.array_equal(drives_active,[0,1,2]):
				angs_to_move=["positioning Sampl ang.","positioning In pl ang.","positioning Out pl ang."]
				with open(self.data_file, 'a') as thefile:
					thefile.write("Sampl ang.[dg], Inpl ang.[dg], Outpl ang.[dg], B[row,column], Bvals(1023=5V), M[row,column], Mvals\n")		
							
		return angs_to_move
		
	def run(self):
		
		print self.drives_active
		
		angs_to_move = self.make_header(self.drives_active)
		positions = numpy.zeros(len(self.drives_active),dtype=object)
		for i in range(len(self.drives_active)):
			ang_scanlist = numpy.arange(int(10*self.ScanEdit[i,0]),int(10*self.ScanEdit[i,1]),int(10*self.ScanEdit[i,2]))
			positions[i] = self.get_pos(self.drives_active[i],ang_scanlist/10.0)
			
		if self.sender=="Run scan":
			
			Bb=numpy.zeros((4,4),dtype=int)
			if len(self.drives_active)==1:
				
				time_start=time.time()
				for pos_1 in positions[0]:
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
							ard_volt=self.Md.read_analog(self.analog_pin,self.avg_pts)
							time_elap=time.time()-time_start					
							self.emit(SIGNAL('volt_data(PyQt_PyObject,PyQt_PyObject)'), time_elap,ard_volt)
						
						Bb[i,j]=ard_volt
						self.emit(SIGNAL('update_B(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),i,j,ard_volt)
						self.emit(SIGNAL('more_tals(PyQt_PyObject,PyQt_PyObject)'),time_elap,ard_volt)
					
					Mm=self.get_MM(Bb)
					with open(self.data_file, 'a') as thefile:
						for i,j in zip(self.Rows,self.Colms):
							thefile.write('%s' %pos_ang)
							thefile.write(''.join(['\tB[',str(i),',',str(j),']']))
							thefile.write('\t%s' %Bb[i,j])
							thefile.write(''.join(['\tM[',str(i),',',str(j),']']))
							thefile.write('\t%s\n' %Mm[i,j])
						
					self.emit(SIGNAL('update_M(PyQt_PyObject)'),Mm)
					
					if self.end_flag==True:
						break
					
				self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),'blue','ready')
					
			elif len(self.drives_active)==2:
					
				time_start=time.time()
				for pos_1 in positions[0]:
					rot_drv=self.drives_active[0]
					self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),'red',angs_to_move[0])
					min_pos_drv=self.Md.move_Absolute(rot_drv,pos_1)
					pos_ang_1=self.get_ang(rot_drv,min_pos_drv)
					self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), rot_drv+3, pos_ang_1)
					
					for pos_2 in positions[1]:
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
								ard_volt=self.Md.read_analog(self.analog_pin,self.avg_pts)
								time_elap=time.time()-time_start					
								self.emit(SIGNAL('volt_data(PyQt_PyObject,PyQt_PyObject)'), time_elap,ard_volt)
								
							Bb[i,j]=ard_volt
							self.emit(SIGNAL('update_B(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),i,j,ard_volt)
							self.emit(SIGNAL('more_tals(PyQt_PyObject,PyQt_PyObject)'),time_elap,ard_volt)

						Mm=self.get_MM(Bb)
						with open(self.data_file, 'a') as thefile:
							for i,j in zip(self.Rows,self.Colms):
								thefile.write("%s" %pos_ang_1)
								thefile.write("\t%s" %pos_ang_2)
								thefile.write(''.join(['\tB[',str(i),',',str(j),']']))
								thefile.write('\t%s' %Bb[i,j])
								thefile.write(''.join(['\tM[',str(i),',',str(j),']']))
								thefile.write('\t%s\n' %Mm[i,j])
							
						self.emit(SIGNAL('update_M(PyQt_PyObject)'),Mm)
						
						if self.end_flag==True:
							break
					if self.end_flag==True:
						break
				self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),'blue','ready')
				
			elif len(self.drives_active)==3:
					
				time_start=time.time()
				for pos_1 in positions[0]:
					rot_drv=self.drives_active[0]
					self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),'red',angs_to_move[0])
					min_pos_drv=self.Md.move_Absolute(rot_drv,pos_1)
					pos_ang_1=self.get_ang(rot_drv,min_pos_drv)
					self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), rot_drv+3, pos_ang_1)
					
					for pos_2 in positions[1]:
						rot_drv=self.drives_active[1]
						self.emit(SIGNAL('change_color(PyQt_PyObject,PyQt_PyObject)'),'red',angs_to_move[1])
						min_pos_drv=self.Md.move_Absolute(rot_drv,pos_2)
						pos_ang_2=self.get_ang(rot_drv,min_pos_drv)
						self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), rot_drv+3, pos_ang_2)
					
						for pos_3 in positions[2]:
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
									ard_volt=self.Md.read_analog(self.analog_pin,self.avg_pts)
									time_elap=time.time()-time_start					
									self.emit(SIGNAL('volt_data(PyQt_PyObject,PyQt_PyObject)'), time_elap,ard_volt)
									
								Bb[i,j]=ard_volt
								self.emit(SIGNAL('update_B(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),i,j,ard_volt)
								self.emit(SIGNAL('more_tals(PyQt_PyObject,PyQt_PyObject)'),time_elap,ard_volt)
								
							Mm=self.get_MM(Bb)
							with open(self.data_file, 'a') as thefile:
								for i,j in zip(self.Rows,self.Colms):
									thefile.write("%s" %pos_ang_1)
									thefile.write("\t%s" %pos_ang_2)
									thefile.write("\t%s" %pos_ang_3)
									thefile.write(''.join(['\tB[',str(i),',',str(j),']']))
									thefile.write('\t%s' %Bb[i,j])
									thefile.write(''.join(['\tM[',str(i),',',str(j),']']))
									thefile.write('\t%s\n' %Mm[i,j])
									
							self.emit(SIGNAL('update_M(PyQt_PyObject)'),Mm)
								
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
		
	def get_MM(self,Bsingle):
		
		Msingle, Mf, Entrophy, DeltaM, DeltaH, Pd = self.sf.measure_single_Matrix(Bsingle,self.A,self.W)
		return Msingle

	def get_pos(self,rot_drv,ang):	
		
		x=[]
		y=[]
		for i in range(4):
			if rot_drv==0:
				x.extend([ self.sampl_vals[i,0] ])
				y.extend([ self.sampl_vals[i,1] ])
			elif rot_drv==1:
				x.extend([ self.inpl_vals[i,0] ])
				y.extend([ self.inpl_vals[i,1] ])
			elif rot_drv==2:
				x.extend([ self.outpl_vals[i,0] ])
				y.extend([ self.outpl_vals[i,1] ])
			
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
				x.extend([ self.sampl_vals[i,0] ])
				y.extend([ self.sampl_vals[i,1] ])
			elif rot_drv==1:
				x.extend([ self.inpl_vals[i,0] ])
				y.extend([ self.inpl_vals[i,1] ])
			elif rot_drv==2:
				x.extend([ self.outpl_vals[i,0] ])
				y.extend([ self.outpl_vals[i,1] ])

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
			self.Esp.go_home(axs+1)
			pos=self.Esp.return_pos(axs+1)
			self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), axs, pos)
			
			
			
			
class Email_dialog(QtGui.QDialog):

	def __init__(self, lcd1, parent=None):
		QtGui.QDialog.__init__(self, parent)
		
		# constants
		self.emailrec_str = config_scan.emailrec
		self.emailset_str = config_scan.emailset
		
		self.lcd1 = lcd1
		
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
		
		self.lb2 = QtGui.QLabel("Send notification when scan is done?",self)
		self.cb2 = QtGui.QComboBox(self)
		mylist=["yes","no"]
		self.cb2.addItems(mylist)
		self.cb2.setCurrentIndex(mylist.index(self.emailset_str[1]))
		grid_0.addWidget(self.lb2,3,0)
		grid_0.addWidget(self.cb2,3,1)
		
		self.lb3 = QtGui.QLabel("Send data when scan is done?",self)
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
		self.lcd1.display(timestr)
		
		self.replace_line("config_scan.py",14,''.join(["timestr=\"",timestr,"\"\n"]))
		self.replace_line("config_scan.py",17,''.join(["emailrec=[\"",'\",\"'.join([i for i in self.emailrec_str]),"\"]\n"]))
		self.replace_line("config_scan.py",18,''.join(["emailset=[\"",'\",\"'.join([i for i in self.emailset_str]),"\"]"]))
		
		imp.reload(config_scan)
	
	
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
		self.emailset_str = config_scan.emailset
		self.emailrec_str = config_scan.emailrec
		self.folder_str = config_scan.create_folder
		self.all_files=["The attached files are some chosen data sent from the scatterometer computer."]

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
		
		self.replace_line("config_scan.py",17,''.join(["emailrec=[\"",'\",\"'.join([i for i in self.emailrec_str]),"\"]\n"]) )
		imp.reload(config_scan)
		
	def replace_line(self,file_name, line_num, text):
		
		lines = open(file_name, 'r').readlines()
		lines[line_num] = text
		out = open(file_name, 'w')
		out.writelines(lines)
		out.close()
		
	def closeEvent(self,event):
	
		event.accept()
		
		
		

		
class Run_gui(QtGui.QDialog):
  
	def __init__(self, parent=None):
		QtGui.QDialog.__init__(self, parent)
		
		# constants
		self.analog_pin=config_scan.Analog_pin
		self.shutter_pin=config_scan.Shutter_pin
		self.Det_set=config_scan.Det_set
		self.avg_pts=config_scan.Avgpts
		self.dwell=config_scan.Dwell
		self.B_rotwh=config_scan.B_rotwh
		self.PSG_colms=config_scan.PSG_colms
		self.PSA_rows=config_scan.PSA_rows
		self.Rows=config_scan.Rows
		self.Colms=config_scan.Colms
		self.calib_aw_str=config_scan.Calib_AW
		self.calib_stepper_str=config_scan.Calib_stepper
		self.filename_str = config_scan.filename
		self.folder_str = config_scan.create_folder	
		self.timestr = config_scan.timestr
		self.ardport_str = config_scan.ardport
		self.espport_str = config_scan.espport
		self.emailrec_str = config_scan.emailrec
		self.emailset_str = config_scan.emailset
		
		self.Minpos=config_calib.Minpos
		self.Maxpos=config_calib.Maxpos
		
		self.initUI()
    
	def initUI(self):

		# status info which button has been pressed
		Bcalib_lbl = QtGui.QLabel("SCAN settings", self)
		Bcalib_lbl.setStyleSheet("color: blue")
		
		self.B_lbl = numpy.zeros(4,dtype=object)
		self.B = numpy.zeros((4,4,4),dtype=object)
		
		self.lcd = numpy.zeros(6,dtype=object)
		lcd_lbl = numpy.zeros(6,dtype=object)
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
		
		Scan_lbl = numpy.zeros(3,dtype=object)
		Range_lbl = numpy.zeros(3,dtype=object)		
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
		
		self.ScanEdit = numpy.zeros((3,3),dtype=object)
		for i in range(3):
			for j in range(3):
				self.ScanEdit[i,j] = QtGui.QLineEdit("",self)
				self.ScanEdit[i,j].setEnabled(False)
		
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
					self.B[i,j,k].setFixedWidth(40)
					self.B[i,j,k].setEnabled(False)
		
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
		self.combo3 = QtGui.QComboBox(self)
		mylist3=["40","41","43","44"]
		self.combo3.addItems(mylist3)
		self.combo3.setCurrentIndex(mylist3.index(str(self.shutter_pin)))
		
		avgpts_lbl = QtGui.QLabel("Averaging points", self)
		self.combo1 = QtGui.QComboBox(self)
		mylist1=["5","20","100","200","500","1000","2000"]
		self.combo1.addItems(mylist1)
		self.combo1.setCurrentIndex(mylist1.index(str(self.avg_pts)))
		
		dwell_lbl = QtGui.QLabel("PSG/PSA dwell [ms]", self)
		self.combo2 = QtGui.QComboBox(self)
		mylist2=["500","1000","1500","2000","2500","3000","3500","4000"]
		self.combo2.addItems(mylist2)
		self.combo2.setCurrentIndex(mylist2.index(str(self.dwell)))

		##############################################
		
		det_lbl = QtGui.QLabel("DETECTOR sensitivity", self)
		det_lbl.setStyleSheet("color: blue")
		
		pin0_lbl = QtGui.QLabel("----- ----- (10^9V/W)", self)
		pin1_lbl = QtGui.QLabel("Pin1 high (10^8V/W)", self)
		self.combo4 = QtGui.QComboBox(self)
		self.combo4.addItems(mylist3)
		self.combo4.setCurrentIndex(mylist3.index(str(self.Det_set[0])))
		
		self.combo5 = QtGui.QComboBox(self)
		mylist4=["high","low"]
		self.combo5.addItems(mylist4)
		self.combo5.setCurrentIndex(mylist4.index(self.Det_set[1]))
		
		pin2_lbl = QtGui.QLabel("Pin2 high (10^5V/W)", self)
		self.combo6 = QtGui.QComboBox(self)
		self.combo6.addItems(mylist3)
		self.combo6.setCurrentIndex(mylist3.index(str(self.Det_set[2])))
		
		self.combo7 = QtGui.QComboBox(self)
		self.combo7.addItems(mylist4)
		self.combo7.setCurrentIndex(mylist4.index(self.Det_set[3]))
		
		##############################################

		# status info which button has been pressed
		et_lbl = QtGui.QLabel("TIME trace for storing data", self)
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
		self.homeAll.triggered.connect(self.go_homeAllAxes)
		self.conMode = numpy.zeros(3,dtype=object)
		self.disconMode = numpy.zeros(3,dtype=object)
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
		self.load_A_and_W(self.calib_aw_str)
		self.load_stepper_calib(self.calib_stepper_str)
		
		
		self.emailMenu = MyBar.addMenu("E-mail")
		self.emailSet = self.emailMenu.addAction("E-mail settings")
		self.emailSet.triggered.connect(self.email_set_dialog)
		self.emailData = self.emailMenu.addAction("E-mail data")
		self.emailData.triggered.connect(self.email_data_dialog)
		
		################### MENU BARS END ##################
		
		g0_0=QtGui.QGridLayout()
		g0_0.addWidget(MyBar,0,0)
		v0 = QtGui.QVBoxLayout()
		v0.addLayout(g0_0)
		
		g4_0 = QtGui.QGridLayout()
		g4_0.addWidget(Bcalib_lbl,0,0)
		g4_1 = QtGui.QGridLayout()
		g4_1.addWidget(self.Run_Button,0,0)
		g4_1.addWidget(self.B_Stop_Button,0,1)
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
				g6_0.addWidget(self.ScanEdit[i,j],i+1,j+1)
		
				
		g_1h=numpy.zeros((4,4),dtype=object)
		#g_1h=[[ QtGui.QSplitter(QtCore.Qt.Horizontal) for i in range(4)] for j in range(4)]
		for i in range(4):
			for j in range(4):
				g_1h[i,j] = QtGui.QSplitter(QtCore.Qt.Horizontal)
		
		g_0=numpy.zeros(4,dtype=object)
		g_1=numpy.zeros(4,dtype=object)
		for i in range(4):
			g_0[i] = QtGui.QSplitter(QtCore.Qt.Vertical) 
			g_1[i] = QtGui.QSplitter(QtCore.Qt.Vertical) 
		
		v=[]
		
		for i in range(4):
			g_0[i].addWidget(self.B_lbl[i])
		
			for j in range(4):
				for k in range(4):
					g_1h[i,j].addWidget(self.B[i,j,k])
				
				g_1[i].addWidget(g_1h[i,j])
		
			v.extend([ QtGui.QSplitter(QtCore.Qt.Vertical) ])
			v[i].addWidget(g_0[i])
			v[i].addWidget(g_1[i])
		
		g1_0 = QtGui.QGridLayout()
		g1_0.addWidget(ard_lbl,0,0)
		g1_1 = QtGui.QGridLayout()
		g1_1.addWidget(analog_pin_lbl,0,0)
		g1_1.addWidget(self.combo0,0,1)
		g1_1.addWidget(shutter_pin_lbl,1,0)
		g1_1.addWidget(self.combo3,1,1)
		g1_1.addWidget(avgpts_lbl,2,0)
		g1_1.addWidget(self.combo1,2,1)
		g1_1.addWidget(dwell_lbl,3,0)
		g1_1.addWidget(self.combo2,3,1)
		v1 = QtGui.QVBoxLayout()
		v1.addLayout(g1_0)
		v1.addLayout(g1_1)
		
		g7_0 = QtGui.QGridLayout()
		g7_0.addWidget(det_lbl,0,0)
		g7_1 = QtGui.QGridLayout()
		g7_1.addWidget(pin0_lbl,0,0)
		g7_1.addWidget(pin1_lbl,1,0)
		g7_1.addWidget(self.combo4,1,1)
		g7_1.addWidget(self.combo5,1,2)
		g7_1.addWidget(pin2_lbl,2,0)
		g7_1.addWidget(self.combo6,2,1)
		g7_1.addWidget(self.combo7,2,2)
		v7 = QtGui.QVBoxLayout()
		v7.addLayout(g7_0)
		v7.addLayout(g7_1)
		
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
		v_all.addLayout(v7)
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
		self.pw0.setFixedWidth(700)
		gr0_0.addWidget(self.pw0,0,0)
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		h_all = QtGui.QHBoxLayout()
		h_all.addLayout(h_some)
		h_all.addLayout(gr0_0)
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
		self.drives=numpy.zeros(3)
		self.drives_active=numpy.array([])
		self.clear_all_graphs()

		# reacts to choises picked in the menu
		self.combo0.activated[str].connect(self.onActivated0)
		self.combo1.activated[str].connect(self.onActivated1)
		self.combo2.activated[str].connect(self.onActivated2)
		self.combo3.activated[str].connect(self.onActivated3)
		self.combo4.activated[str].connect(self.onActivated4)
		self.combo5.activated[str].connect(self.onActivated5)
		self.combo6.activated[str].connect(self.onActivated6)
		self.combo7.activated[str].connect(self.onActivated7)
		self.allButtons_torf(False)
		
		self.B_Stop_Button.clicked.connect(self.stop_moving)
		self.Run_Button.clicked.connect(self.scan_func)
		
		#self.setGeometry(600,0,1400,550)
		self.move(0,250)
		self.setWindowTitle('Scatterometer - scan')
		self.show()

	##########################################
	def loadStepperCalibDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file','C:\Users\localuser\Documents\Vedran_workfolder\Scatterometer\Calib_files')
		if fname:
			self.calib_stepper_str = str(fname)
			self.load_stepper_calib(str(fname))
			
	def load_stepper_calib(self,fname):
		
		head, tail = os.path.split(fname)
		stepper_calib = imp.load_source(tail[:-3],fname)
		try:
			self.sampl_vals=numpy.array(stepper_calib.sampl)
			self.inpl_vals=numpy.array(stepper_calib.inpl)
			self.outpl_vals=numpy.array(stepper_calib.outpl)
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message',"Could not load stepper calib params! Stepper calib file must have arrays with names: sampl,inpl,outpl!")
			return None
		
	def loadCalibDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file','C:\Users\localuser\Documents\Vedran_workfolder\Scatterometer\Calib_files')
		if fname:
			self.calib_aw_str = str(fname)
			self.load_A_and_W(str(fname))
	
	def email_data_dialog(self):
	
		self.Send_email_dialog = Send_email_dialog()
		self.Send_email_dialog.exec_()
		
	
	def load_A_and_W(self,fname):
		
		head, tail = os.path.split(fname)
		calib_path = imp.load_source(tail[:-3],fname)
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
			QtGui.QMessageBox.warning(self, 'Message',"Could not load calib params! Calib file must have among others 1-D arrays with names: Rows,Colms,A,B!")
			return None
	
	def onActivated0(self, text):
		
		self.analog_pin = int(text)
		
	def onActivated1(self, text):
		
		self.avg_pts = int(text)
		
	def onActivated2(self, text):
		
		self.dwell = int(text)
	
	def onActivated3(self, text):
		
		self.shutter_pin = int(text)
	
	def onActivated4(self, text):
		
		self.Det_set[0] = int(text)
		self.Md.set_oec_sens(self.Det_set[0],self.Det_set[1])
	
	def onActivated5(self, text):
		
		self.Det_set[1] = str(text)
		self.Md.set_oec_sens(self.Det_set[0],self.Det_set[1])
	
	def onActivated6(self, text):
		
		self.Det_set[2] = int(text)
		self.Md.set_oec_sens(self.Det_set[2],self.Det_set[3])
	
	def onActivated7(self, text):
		
		self.Det_set[3] = str(text)
		self.Md.set_oec_sens(self.Det_set[2],self.Det_set[3])
	
	def ArdDialog(self):

		text, ok = QtGui.QInputDialog.getText(self, 'Serial Port Dialog','Enter Arduino serial', text=self.ardport_str)
		if ok:
			self.ardport_str = str(text)	
	
	def EspDialog(self):

		text, ok = QtGui.QInputDialog.getText(self, 'Serial Port Dialog','Enter ESP serial', text=self.espport_str)
		if ok:
			self.espport_str = str(text)
	
	def email_set_dialog(self):
	
		self.Email_dialog = Email_dialog(self.lcd1)
		self.Email_dialog.exec_()
		
	def reload_email(self):
	
		imp.reload(config_scan)	
		self.emailrec_str = config_scan.emailrec
		self.emailset_str = config_scan.emailset

	def set_connect_serial(self):
		
		try:
			self.Esp = ESP300.ESP300(self.espport_str)
			self.Esp.set_timeout(2)
			vers=self.Esp.return_ver()
			if vers:
				print vers
				self.Esp.set_motors("on")
			else:
				QtGui.QMessageBox.warning(self, 'Message',"No response from ESP300! Check the cable connection.")
				return None
		except Exception, e:
			QtGui.QMessageBox.warning(self, 'Message',"No response from the ESP serial port! Check the ESP port name and check the cable connection.")
			return None
		
		try:
			self.Md = MOTORSTEP_DRIVE.MOTORSTEP_DRIVE(self.ardport_str)
			self.Md.set_timeout(2)
			self.Md.set_oec_sens(self.Det_set[0],self.Det_set[1])
			self.Md.set_oec_sens(self.Det_set[2],self.Det_set[3])
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
		
		
		self.conSerial.setEnabled(False)
		self.serialArd.setEnabled(False)
		self.serialEsp.setEnabled(False)

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

	def go_homeAllAxes(self):
		
		self.get_my_Thread_homeAll=my_Thread_homeAll(self.Esp)
		self.connect(self.get_my_Thread_homeAll,SIGNAL("update_lcd(PyQt_PyObject,PyQt_PyObject)"),self.update_lcd)
		self.connect(self.get_my_Thread_homeAll,SIGNAL('finished()'),self.set_finished_homed)
		
		self.B_Stop_Button.setEnabled(False)
		
		if self.Run_Button.isEnabled()==True:
			self.run__button_OldStatus=True
		else:
			self.run__button_OldStatus=False
		
		self.Run_Button.setEnabled(False)
		self.serialMenu.setEnabled(False)
		self.modeMenu.setEnabled(False)
		self.calibMenu.setEnabled(False)
		self.emailMenu.setEnabled(False)
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
			self.ScanEdit[drive,i].setEnabled(True)
		
		#volts=self.Md.read_analog(self.analog_pin,self.avg_pts)
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
			self.ScanEdit[drive,i].setEnabled(False)

	def drive_onoff(self,mystr,drive):
		
		if mystr=='on':
			self.drives[drive]=1
		elif mystr=='off':
			self.drives[drive]=0
		
		if numpy.array_equal(self.drives,[0,0,0]):
			self.drives_active=numpy.array([])
		elif numpy.array_equal(self.drives,[1,0,0]):
			self.drives_active=numpy.array([0])
		elif numpy.array_equal(self.drives,[0,1,0]):
			self.drives_active=numpy.array([1])
		elif numpy.array_equal(self.drives,[0,0,1]):
			self.drives_active=numpy.array([2])
		elif numpy.array_equal(self.drives,[1,1,0]):
			self.drives_active=numpy.array([0,1])
		elif numpy.array_equal(self.drives,[0,1,1]):
			self.drives_active=numpy.array([1,2])	
		elif numpy.array_equal(self.drives,[1,0,1]):
			self.drives_active=numpy.array([0,2])
		elif numpy.array_equal(self.drives,[1,1,1]):
			self.drives_active=numpy.array([0,1,2])
		
	def allButtons_torf(self,text):
		
		self.filenameEdit.setEnabled(text)
		self.folderEdit.setEnabled(text)
		self.homeAll.setEnabled(text)
		
		self.combo0.setEnabled(text)
		self.combo1.setEnabled(text)
		self.combo2.setEnabled(text)
		self.combo3.setEnabled(text)
		self.combo4.setEnabled(text)
		self.combo5.setEnabled(text)
		self.combo6.setEnabled(text)
		self.combo7.setEnabled(text)
		
	def closeEvent(self,event):
		
		reply = QtGui.QMessageBox.question(self, 'Message', "Quit now? Serial ports will be flushed and disconnected!", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes:
			if hasattr(self, 'Md') or hasattr(self, 'Esp'):	
				
				if hasattr(self, 'get_my_Thread') and not hasattr(self, 'get_my_Thread_homeAll'):
					if self.get_my_Thread.isRunning():
						QtGui.QMessageBox.warning(self, 'Message', "Scan in progress. Stop the scan and disconnect all stepper drives before closing the program!")
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
				
				elif hasattr(self, 'get_my_Thread_homeAll') and not hasattr(self, 'get_my_Thread'):
					if self.get_my_Thread_homeAll.isRunning():
						QtGui.QMessageBox.warning(self, 'Message', "Homing in progress. Wait for homing to finish before closing the program!")
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
							
				elif hasattr(self, 'get_my_Thread_homeAll') and hasattr(self, 'get_my_Thread'):
					if self.get_my_Thread_homeAll.isRunning():
						QtGui.QMessageBox.warning(self, 'Message', "Homing in progress. Wait for homing to finish before closing the program!")
						event.ignore()
					elif self.get_my_Thread.isRunning():
						QtGui.QMessageBox.warning(self, 'Message', "Scan in progress. Stop the scan and disconnect all stepper drives before closing the program!")
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
	
		# For SAVING data
		if str(self.filenameEdit.text()):
			string_filename=''.join([str(self.filenameEdit.text()),self.timestr])
			#self.string_elapsedtime=''.join([self.filename_str,"elapsedtime_",self.timestr])
		else:
			string_filename=''.join(["data_",self.timestr])
			#self.string_elapsedtime=''.join(["data_elapsedtime_",self.timestr])
							
		if str(self.folderEdit.text()):
			saveinfolder=''.join([str(self.folderEdit.text()),"/"])
			if not os.path.isdir(str(self.folderEdit.text())):
				os.mkdir(str(self.folderEdit.text()))
		else:
			saveinfolder=""
			
		self.data_file=''.join([saveinfolder,string_filename,".txt"])
		
		# update the lcd motorstep position
		passScanEdit=numpy.zeros((len(self.drives_active),3))
		for i in range(len(self.drives_active)):
			try:
				passScanEdit[i,0] = float(str(self.ScanEdit[self.drives_active[i],0].text()))
				passScanEdit[i,1] = float(str(self.ScanEdit[self.drives_active[i],1].text()))
				passScanEdit[i,2] = float(str(self.ScanEdit[self.drives_active[i],2].text()))
			except Exception, e:
				QtGui.QMessageBox.warning(self, 'Message',"Only integers or floating point numbers accepted!")
				return None
		
		sender = self.sender()
		self.get_my_Thread=my_Thread(sender.text(),self.Esp,self.Md,self.calib_stepper_str,passScanEdit,self.drives_active
															 ,self.B_rotwh,self.PSG_colms,self.PSA_rows,self.Rows,self.Colms,self.analog_pin
															 ,self.avg_pts,self.dwell,self.data_file
															 ,self.sampl_vals,self.inpl_vals,self.outpl_vals,self.A,self.W)
		self.connect(self.get_my_Thread,SIGNAL("more_tals(PyQt_PyObject,PyQt_PyObject)"),self.more_tals)
		self.connect(self.get_my_Thread,SIGNAL("volt_data(PyQt_PyObject,PyQt_PyObject)"),self.volt_data)
		self.connect(self.get_my_Thread,SIGNAL("update_lcd(PyQt_PyObject,PyQt_PyObject)"),self.update_lcd)
		self.connect(self.get_my_Thread,SIGNAL("update_B(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"),self.update_B)
		self.connect(self.get_my_Thread,SIGNAL("update_M(PyQt_PyObject)"),self.update_M)
		self.connect(self.get_my_Thread,SIGNAL("clear_graphs_from_thread()"),self.clear_graphs_from_thread)
		self.connect(self.get_my_Thread,SIGNAL("change_color(PyQt_PyObject,PyQt_PyObject)"),self.change_color)
		self.connect(self.get_my_Thread,SIGNAL('finished()'),self.set_finished)
		
		self.allButtons_torf(False)
		self.B_Stop_Button.setEnabled(True)
		self.Run_Button.setEnabled(False)
		self.serialMenu.setEnabled(False)
		self.modeMenu.setEnabled(False)
		self.calibMenu.setEnabled(False)
		self.emailMenu.setEnabled(False)
		
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
		
		self.B[0,i,j].setText(str(volt))
	
	def update_M(self,Msingle):
		
		for i in range(4):
			for j in range(4):
				self.B[1,i,j].setText(str(round(Msingle[i,j],4)))
				
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
		self.emailMenu.setEnabled(True)
		
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
		self.emailMenu.setEnabled(True)
		
		self.reload_email()
		if self.emailset_str[1] == "yes":
			self.send_notif()
		if self.emailset_str[2] == "yes":
			self.send_data()

	def send_notif(self):
		
		try:
			self.yag = yagmail.SMTP(self.emailset_str[0])
			self.yag.send(to=self.emailrec_str, subject="Scatterometer scan is done!", contents="Scatteromoter scan is done so please visit the experiment site and make sure that all the light sources are switched off.")
		except Exception,e:
			QtGui.QMessageBox.warning(self, 'Message',''.join(["Could not load the gmail account ",self.emailset_str[0],"! Try following steps:\n1. Check internet connection. Only wired internet will work, ie. no wireless.\n2. Check the account username and its password.\n3. Make sure that the account accepts less secure apps."]))
		
	def send_data(self):
	
		try:
			self.yag = yagmail.SMTP(self.emailset_str[0])
			self.yag.send(to=self.emailrec_str, subject="Scatterometer data from the latest scan!", contents=["Scatteromoter scan is done and the logged data is attached to this email. Please visit the experiment site and make sure that all light sources are switched off.", self.data_file ])
		except Exception,e:
			QtGui.QMessageBox.warning(self, 'Message',''.join(["Could not load gmail account ",self.emailset_str[0],"! Try following steps:\n1. Check internet connection. Only wired internet will work, ie. no wireless.\n2. Check the account username and its password.\n3. Make sure that the account accepts less secure apps."]))
	
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
		self.reload_email()
		
		with open("config_scan.py", 'w') as thefile:
			thefile.write( ''.join(["Analog_pin=",str(self.analog_pin),"\n"]) )
			thefile.write( ''.join(["Shutter_pin=",str(self.shutter_pin),"\n"]) )
			thefile.write( ''.join(["Det_set=[",str(self.Det_set[0]),",\"",str(self.Det_set[1]),"\",",str(self.Det_set[2]),",\"",str(self.Det_set[3]),"\"]\n"]) )
			thefile.write( ''.join(["Avgpts=",str(self.avg_pts),"\n"]) )
			thefile.write( ''.join(["Dwell=",str(self.dwell),"\n"]) )
			thefile.write( ''.join(["B_rotwh=[",','.join([str(self.B_rotwh[i]) for i in range(4)]),"]\n"]) )
			thefile.write( ''.join(["PSG_colms=[",','.join([str(self.PSG_colms[i]) for i in range(4)]),"]\n"]) )
			thefile.write( ''.join(["PSA_rows=[",','.join([str(self.PSA_rows[i]) for i in range(4)]),"]\n"]) )
			thefile.write( ''.join(["Rows=[",','.join([str(self.Rows[i]) for i in range(16)]),"]\n"]) )
			thefile.write( ''.join(["Colms=[",','.join([str(self.Colms[i]) for i in range(16)]),"]\n"]) )
			thefile.write( ''.join(["Calib_AW=\"",self.calib_aw_str,"\"\n"]) )
			thefile.write( ''.join(["Calib_stepper=\"",self.calib_stepper_str,"\"\n"]) )
			thefile.write( ''.join(["filename=\"",str(self.filenameEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["create_folder=\"",str(self.folderEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["timestr=\"",self.timestr,"\"\n"]) )
			thefile.write( ''.join(["ardport=\"",self.ardport_str,"\"\n"]) )
			thefile.write( ''.join(["espport=\"",self.espport_str,"\"\n"]) )
			thefile.write( ''.join(["emailrec=[\"",'\",\"'.join([i for i in self.emailrec_str]),"\"]\n"]) )
			thefile.write( ''.join(["emailset=[\"",'\",\"'.join([i for i in self.emailset_str]),"\"]"]) )

		imp.reload(config_scan)

	def get_ang(self,rot_drv,pos):
		
		x=[]
		y=[]
		for i in range(4):
			if rot_drv==0:
				x.extend([ self.sampl_vals[i,0] ])
				y.extend([ self.sampl_vals[i,1] ])
			elif rot_drv==1:
				x.extend([ self.inpl_vals[i,0] ])
				y.extend([ self.inpl_vals[i,1] ])
			elif rot_drv==2:
				x.extend([ self.outpl_vals[i,0] ])
				y.extend([ self.outpl_vals[i,1] ])
				
		if numpy.min(pos)>=min(x) and numpy.max(pos)<=max(x):
			#spline
			ang_curve=scipy.interpolate.splrep(x, y, k=3, s=0)
			#linear
			#ang_curve = scipy.interpolate.splrep(x, y, k=1, s=0)
			pos_ang = scipy.interpolate.splev(pos, ang_curve, der=0)
			return numpy.round(pos_ang,1)


def main():
  
	app=QtGui.QApplication(sys.argv)
	ex=Run_gui()
	sys.exit(app.exec_())
    
if __name__=='__main__':
  main()
  
