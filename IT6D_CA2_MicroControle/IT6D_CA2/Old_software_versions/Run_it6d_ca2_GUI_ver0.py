import os, sys, serial, time
import numpy
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import pyqtgraph.exporters
#from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, SIGNAL
import config_Run_IT6D_CA2
import SR5210, IT6D_CA2 
import Methods_for_IT6D_CA2

class Run_IT6D_CA2_Thread(QThread):
	
	def __init__(self,*argv):
		QThread.__init__(self)
		
		# constants	
		self.end_flag=False
		
		self.op_mode = argv[0]
		self.scan_mode = argv[1]
		self.folder_str = argv[2]
		self.filename_str = argv[3]
		self.xscan = [int(argv[4][i]*1000) for i in range(3)]
		self.yscan = [int(argv[5][i]*10000) for i in range(3)]
		self.dwell_time = argv[6]
		self.reset_mode = argv[7]
		self.xy_limiter = int(argv[8]*1000)
		self.timestr = argv[9]
		self.it6d_ca2port_str = argv[10]
		self.sr5210port_str = argv[11]
				
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
	
	def abort(self):
		
		self.end_flag=True
		
	def run(self):
		
		self.it6d = IT6D_CA2.IT6D_CA2(self.xy_limiter,int(self.it6d_ca2port_str))
		self.sr5210 = SR5210.SR5210(int(self.sr5210port_str))
		self.sr5210.set_testechooff()
		###########################################
		
		if self.op_mode=='xyscan':
			self.xyscan()
		elif self.op_mode=='xscan':
			self.def_xscan()
		elif self.op_mode=='yscan':
			self.def_yscan()
		elif self.op_mode=='move rel':
			self.move_rel()
		elif self.op_mode=='move abs':
			self.move_abs()
		elif self.op_mode=='reset':
			self.reset()

	def xyscan(self):
		
		data_file=''.join([self.saveinfolder,self.string_filename,".txt"])	
		data_file_spine=''.join([self.saveinfolder,self.string_filename,"_spine.txt"])
		data_Spath_spine=''.join([self.saveinfolder,self.string_filename,"_Spath_spine.txt"])
		
		x_array=numpy.arange(self.xscan[0],self.xscan[1]+self.xscan[2],self.xscan[2])
		y_array=numpy.arange(self.yscan[0],self.yscan[1]+self.yscan[2],self.yscan[2])

		with open(data_file, 'w') as thefile:
		  thefile.write("Your comment line - do NOT delete this line\n") 
		  thefile.write("X-pos [m], Y-pos [m], Voltage [V]\n")
		
		with open(data_file_spine, 'w') as thefile:
			thefile.write("Your comment line - do NOT delete this line\n") 
			thefile.write("X-pos[m], Y-pos [m], Max voltage [V]\n")
			
		with open(data_Spath_spine, 'w') as thefile:
			thefile.write("Your comment line - do NOT delete this line\n")
			thefile.write("S [m], Max voltage [V]\n")
			
		save_x=[]
		save_y=[]
		save_Umax=[]
	  ###########################################
	  ########################################### 
	    
		if self.scan_mode=='xwise':

			time_start=time.time()
			for j in y_array:
				if self.end_flag==True:
					break
				self.it6d.move_abs('y',j)
				voltages=[]
				pos_x=[]
				for i in x_array:
					if self.end_flag==True:
						break
					# move the microsteppers to the calculated positions
					self.it6d.move_abs('x',i)
					time_now=time.time()
					# update voltage readouts during dwell time
					while (time.time()-time_now)<self.dwell_time:
						outputcalib=self.get_lockin_data()
						time_elap=time.time()-time_start
						self.emit(SIGNAL('make_update2(QString,QString,QString)'),str(time_elap),str(1e-6*i),str(outputcalib))
					# get the last voltage value and save to a file
					with open(data_file, 'a') as thefile:
						thefile.write('%s\t' %(1e-6*i))
						thefile.write('%s\t' %(1e-7*j))
						thefile.write('%s\n' %(outputcalib))
					self.emit(SIGNAL('make_update4(QString,QString)'),str(time_elap),str(outputcalib))
					self.emit(SIGNAL('make_update1(QString,QString,QString)'),str(1e-6*i),str(1e-7*j),str(outputcalib))
					self.emit(SIGNAL('scatter_plot()'))
					print 'X_abs:',i, ', Y_abs:',j, ', Vlockin:',outputcalib
					# calculate spine positions along the x axis
					pos_x.extend([ 1e-6*i ])
					voltages.extend([ outputcalib ])
				
				ind_max=numpy.argmax(voltages)
				with open(data_file_spine, 'a') as thefile:
					thefile.write('%s\t' %pos_x[ind_max])
					thefile.write('%s\t' %(1e-7*j))
					thefile.write('%s\n' %voltages[ind_max])
				
				save_x.extend([ pos_x[ind_max] ])
				save_y.extend([ 1e-7*j ])
				save_Umax.extend([ voltages[ind_max] ])
				if j==y_array[0]:
					S=numpy.array([0])
				else:
					delta_xy=(numpy.diff(save_x)**2+numpy.diff(save_y)**2)**0.5
					S=numpy.append([[0]],[numpy.add.accumulate(delta_xy)])
				self.emit(SIGNAL('update_Spath(QString,QString,QString,QString)'),str(save_x[-1]),str(save_y[-1]),str(S[-1]),str(save_Umax[-1]))
				with open(data_Spath_spine, 'a') as thefile:
					thefile.write('%s\t' %S[-1])
					thefile.write('%s\n' %save_Umax[-1])
				
		elif self.scan_mode=='ywise':

			time_start=time.time()
			for i in x_array:
				if self.end_flag==True:
					break
				self.it6d.move_abs('x',i)
				voltages=[]
				pos_y=[]
				for j in y_array:
					if self.end_flag==True:
						break
					# move the miself.it6dcrosteppers to the calculated positions
					self.it6d.move_abs('y',j)
					time_now=time.time()
					# update voltage readouts during dwell time
					while (time.time()-time_now)<self.dwell_time:
						outputcalib=self.get_lockin_data()
						time_elap=time.time()-time_start
						self.emit(SIGNAL('make_update2(QString,QString,QString)'),str(time_elap),str(1e-7*j),str(outputcalib))
					# get the last voltage value and save to a file
					with open(data_file, 'a') as thefile:
						thefile.write('%s\t' %(1e-6*i))
						thefile.write('%s\t' %(1e-7*j))
						thefile.write('%s\n' %(outputcalib))
					self.emit(SIGNAL('make_update4(QString,QString)'),str(time_elap),str(outputcalib))
					self.emit(SIGNAL('make_update1(QString,QString,QString)'),str(1e-6*i),str(1e-7*j),str(outputcalib))
					self.emit(SIGNAL('scatter_plot()'))
					print 'X_abs:',i, ', Y_abs:',j, ', Vlockin:',outputcalib
					# calculate spine positions along the y axis
					pos_y.extend([ 1e-7*j ])
					voltages.extend([ outputcalib ])
			
				ind_max=numpy.argmax(voltages)
				with open(data_file_spine, 'a') as thefile:
					thefile.write('%s\t' %(1e-6*i))
					thefile.write('%s\t' %pos_y[ind_max])
					thefile.write('%s\n' %voltages[ind_max])
					
				save_x.extend([ 1e-6*i ])
				save_y.extend([ pos_y[ind_max] ])
				save_Umax.extend([ voltages[ind_max] ])
				if i==x_array[0]:
					S=numpy.array([0])
				else:
					delta_xy=(numpy.diff(save_x)**2+numpy.diff(save_y)**2)**0.5
					S=numpy.append([[0]],[numpy.add.accumulate(delta_xy)])
				self.emit(SIGNAL('update_Spath(QString,QString,QString,QString)'),str(save_x[-1]),str(save_y[-1]),str(S[-1]),str(save_Umax[-1]))
				with open(data_Spath_spine, 'a') as thefile:
					thefile.write('%s\t' %S[-1])
					thefile.write('%s\n' %save_Umax[-1])
					
		elif self.scan_mode=='xsnake':
			
			turn=-1
			time_start=time.time()
			for j in y_array:
				if self.end_flag==True:
					break
				self.it6d.move_abs('y',j)
				turn=turn*-1
				voltages=[]
				pos_x=[]
				for i in x_array[::turn]:
					if self.end_flag==True:
						break
					# move the microsteppers to the calculated positions
					self.it6d.move_abs('x',i)
					time_now=time.time()
					# update voltage readouts during dwell time
					while (time.time()-time_now)<self.dwell_time:
						outputcalib=self.get_lockin_data()
						time_elap=time.time()-time_start
						self.emit(SIGNAL('make_update2(QString,QString,QString)'),str(time_elap),str(1e-6*i),str(outputcalib))
					# get the last voltage value and save to a file
					with open(data_file, 'a') as thefile:
						thefile.write('%s\t' %(1e-6*i))
						thefile.write('%s\t' %(1e-7*j))
						thefile.write('%s\n' %(outputcalib))
					self.emit(SIGNAL('make_update4(QString,QString)'),str(time_elap),str(outputcalib))
					self.emit(SIGNAL('make_update1(QString,QString,QString)'),str(1e-6*i),str(1e-7*j),str(outputcalib))
					self.emit(SIGNAL('scatter_plot()'))
					print 'X_abs:',i, ', Y_abs:',j, ', Vlockin:',outputcalib
					# calculate spine positions along the x axis
					pos_x.extend([ 1e-6*i ])
					voltages.extend([ outputcalib ])
				
				ind_max=numpy.argmax(voltages)
				with open(data_file_spine, 'a') as thefile:
				  thefile.write('%s\t' %pos_x[ind_max])
				  thefile.write('%s\t' %(1e-7*j))
				  thefile.write('%s\n' %voltages[ind_max])
				
				save_x.extend([ pos_x[ind_max] ])
				save_y.extend([ 1e-7*j ])
				save_Umax.extend([ voltages[ind_max] ])
				if j==y_array[0]:
					S=numpy.array([0])
				else:
					delta_xy=(numpy.diff(save_x)**2+numpy.diff(save_y)**2)**0.5
					S=numpy.append([[0]],[numpy.add.accumulate(delta_xy)])
				self.emit(SIGNAL('update_Spath(QString,QString,QString,QString)'),str(save_x[-1]),str(save_y[-1]),str(S[-1]),str(save_Umax[-1]))
				with open(data_Spath_spine, 'a') as thefile:
					thefile.write('%s\t' %S[-1])
					thefile.write('%s\n' %save_Umax[-1])
					
		elif self.scan_mode=='ysnake':
			
			turn=-1
			time_start=time.time()
			for i in x_array:
				if self.end_flag==True:
					break
				self.it6d.move_abs('x',i)
				turn=turn*-1
				voltages=[]
				pos_y=[]
				for j in y_array[::turn]:
					if self.end_flag==True:
						break
					# move the microsteppers to the calculated positions
					self.it6d.move_abs('y',j)
					time_now=time.time()
					# update voltage readouts during dwell time
					while (time.time()-time_now)<self.dwell_time:
						outputcalib=self.get_lockin_data()
						time_elap=time.time()-time_start
						self.emit(SIGNAL('make_update2(QString,QString,QString)'),str(time_elap),str(1e-7*j),str(outputcalib))
					# get the last voltage value and save to a file
					with open(data_file, 'a') as thefile:
						thefile.write('%s\t' %(1e-6*i))
						thefile.write('%s\t' %(1e-7*j))
						thefile.write('%s\n' %(outputcalib))
					self.emit(SIGNAL('make_update4(QString,QString)'),str(time_elap),str(outputcalib))
					self.emit(SIGNAL('make_update1(QString,QString,QString)'),str(1e-6*i),str(1e-7*j),str(outputcalib))
					self.emit(SIGNAL('scatter_plot()'))
					print 'X_abs:',i,', Y_abs:',j,', Vlockin:',outputcalib
					# calculate spine positions along the y axis
					pos_y.extend([ 1e-7*j ])
					voltages.extend([ outputcalib ])
				
				ind_max=numpy.argmax(voltages)
				with open(data_file_spine, 'a') as thefile:
					thefile.write('%s\t' %(1e-6*i))
					thefile.write('%s\t' %pos_y[ind_max])
					thefile.write('%s\n' %voltages[ind_max])
					
				save_x.extend([ 1e-6*i ])
				save_y.extend([ pos_y[ind_max] ])
				save_Umax.extend([ voltages[ind_max] ])
				if i==x_array[0]:
					S=numpy.array([0])
				else:
					delta_xy=(numpy.diff(save_x)**2+numpy.diff(save_y)**2)**0.5
					S=numpy.append([[0]],[numpy.add.accumulate(delta_xy)])
				self.emit(SIGNAL('update_Spath(QString,QString,QString,QString)'),str(save_x[-1]),str(save_y[-1]),str(S[-1]),str(save_Umax[-1]))
				with open(data_Spath_spine, 'a') as thefile:
					thefile.write('%s\t' %S[-1])
					thefile.write('%s\n' %save_Umax[-1])
					
		else:
			raise ValueError('Valid scan_mode input: xwise, ywise, xsnake, ysnake!')
	  
	def def_xscan(self):
		
		data_file=''.join([self.saveinfolder,self.string_filename,".txt"])
		x_array=numpy.arange(self.xscan[0],self.xscan[1]+self.xscan[2],self.xscan[2])

		with open(data_file, 'w') as thefile:
		  thefile.write("Your comment line - do NOT delete this line\n") 
		  thefile.write("X-pos [m], Voltage [V]\n")
	  
		_,j = self.it6d.get_positions()
		self.emit(SIGNAL('pass_y_pos(QString)'),str(1e-7*int(j)))
	  
		time_start=time.time()   
		for i in x_array:
			if self.end_flag==True:
				break
			self.it6d.move_abs('x',i)
			time_now=time.time()
			# update voltage readouts during dwell time
			while (time.time()-time_now)<self.dwell_time:
				outputcalib=self.get_lockin_data()
				time_elap=time.time()-time_start
				self.emit(SIGNAL('make_update2(QString,QString,QString)'),str(time_elap),str(1e-6*i),str(outputcalib))
			# get the last voltage value and save to a file
			with open(data_file, 'a') as thefile:
			  thefile.write('%s\t' %(1e-6*i))
			  thefile.write('%s\n' %(outputcalib))
			self.emit(SIGNAL('make_update1(QString,QString,QString)'),str(1e-6*i),str(1e-7*int(j)),str(outputcalib))
			self.emit(SIGNAL('make_update4(QString,QString)'),str(time_elap),str(outputcalib))
			#self.emit(SIGNAL('make_update3(QString,QString)'),str(time_elap),str(1e-6*i))
			print 'X_abs:',i,', Vlockin:',outputcalib

	def def_yscan(self):
		
		data_file=''.join([self.saveinfolder,self.string_filename,".txt"])
		y_array=numpy.arange(self.yscan[0],self.yscan[1]+self.yscan[2],self.yscan[2])

		with open(data_file, 'w') as thefile:
		  thefile.write("Your comment line - do NOT delete this line\n") 
		  thefile.write("Y-pos [m], Voltage [V]\n")

		i,_ = self.it6d.get_positions()
		self.emit(SIGNAL('pass_x_pos(QString)'),str(1e-6*int(i)))

		time_start=time.time()
		for j in y_array:
			if self.end_flag==True:
				break
			self.it6d.move_abs('y',j)
			time_now=time.time()
			# update voltage readouts during dwell time
			while (time.time()-time_now)<self.dwell_time:
				outputcalib=self.get_lockin_data()
				time_elap=time.time()-time_start
				self.emit(SIGNAL('make_update2(QString,QString,QString)'),str(time_elap),str(1e-7*j),str(outputcalib))
			# get the last voltage value and save to a file
			with open(data_file, 'a') as thefile:
			  thefile.write('%s\t' %(1e-7*j))
			  thefile.write('%s\n' %(outputcalib))
			self.emit(SIGNAL('make_update1(QString,QString,QString)'),str(1e-6*int(i)),str(1e-7*j),str(outputcalib))
			self.emit(SIGNAL('make_update4(QString,QString)'),str(time_elap),str(outputcalib))
			#self.emit(SIGNAL('make_update3(QString,QString)'),str(time_elap),str(1e-7*j))
			print 'Y_abs:',j,', Vlockin:',outputcalib

	def move_rel(self):

		if self.end_flag==False:
			self.it6d.move_rel('x',self.xscan[0])
		if self.end_flag==False:
			self.it6d.move_rel('y',self.yscan[0])

	def move_abs(self):

		if self.end_flag==False:
			self.it6d.move_abs('x',self.xscan[0])
		if self.end_flag==False:
			self.it6d.move_abs('y',self.yscan[0])

	def reset(self):
		
		self.it6d.reset(self.reset_mode)

	def get_lockin_data(self):
		'''
		# get the output from the overload status command
		self.sr5210.write(''.join(['N\n']))
		time.sleep(self.set_delay)
		out_N=self.sr5210.read()
		# the N output is following LSB-0, therefore list inversion
		N_to_bin='{0:08b}'.format(int(out_N))[::-1]
		#print 'N_to_bin =', N_to_bin
		'''

		# set auto-measure
		#self.sr5210.write(''.join(['ASM']))
		#time.sleep(self.ASM_delay)

		# set the output filter slope to 12dB/ostave
		#self.sr5210.write(''.join(['XDB 1']))
		#time.sleep(self.set_delay)

		# set time constant to 100 ms, since previous ASM may have changed it 
		#self.sr5210.write(''.join(['XTC 4']))
		#time.sleep(self.set_delay)

		# get the present sensitivity setting
		#self.sr5210.write(''.join(['SEN']))
		#time.sleep(self.set_delay)
		senrangecode=self.sr5210.return_sen()
		#print 'senrangecode =', senrangecode

		# for the equation see page 6-21 in the manual
		senrange=(1+(2*(int(senrangecode)%2)))*10**(int(senrangecode)/2-7)
		#print 'senrange =', senrange

		# reads X channel output
		#self.sr5210.write(''.join(['X']))
		#time.sleep(self.set_delay)
		outputuncalib=self.sr5210.return_X()
		#print 'outputuncalib =',outputuncalib

		# assuming N_to_bin[1]=='0' and N_to_bin[2]=='0'
		outputcalib=int(outputuncalib)*senrange*1e-4

		return outputcalib



class Run_IT6D_CA2(QtGui.QWidget):

	def __init__(self):
		super(Run_IT6D_CA2, self).__init__()
		
		# Initial read of the config file
		self.op_mode = config_Run_IT6D_CA2.op_mode
		self.scan_mode = config_Run_IT6D_CA2.scan_mode
		self.folder_str=config_Run_IT6D_CA2.new_folder
		self.filename_str=config_Run_IT6D_CA2.filename
		self.xscan = config_Run_IT6D_CA2.x_scan_mm
		self.yscan = config_Run_IT6D_CA2.y_scan_mm
		self.dwell_time = config_Run_IT6D_CA2.wait_time
		self.reset_mode = config_Run_IT6D_CA2.reset_mode
		self.xy_limiter_mm = config_Run_IT6D_CA2.xy_limiter_mm
		self.timestr=config_Run_IT6D_CA2.timestr
		self.it6d_ca2port_str=config_Run_IT6D_CA2.it6d_ca2port
		self.sr5210port_str=config_Run_IT6D_CA2.sr5210port
		
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
		
		gpibMenu = MyBar.addMenu("Gpib ports")
		self.gpibIT6D_CA2 = gpibMenu.addAction("IT6D CA2")
		self.gpibIT6D_CA2.triggered.connect(self.IT6D_CA2Dialog)
		self.gpibSR5210 = gpibMenu.addAction("SR5210")
		self.gpibSR5210.triggered.connect(self.SR5210Dialog)
				
		################### MENU BARS END ##################

		lbl1 = QtGui.QLabel("OPERATION mode settings:", self)
		lbl1.setStyleSheet("color: blue")	
		
		opmode_lbl = QtGui.QLabel("Operation", self)
		self.combo4 = QtGui.QComboBox(self)
		mylist4=["move abs","move rel","xyscan","xscan","yscan","reset"]
		self.combo4.addItems(mylist4)
		self.combo4.setCurrentIndex(mylist4.index(self.op_mode))
		
		scanmode_lbl = QtGui.QLabel("Scan", self)
		self.combo5 = QtGui.QComboBox(self)
		mylist5=["xsnake","ysnake","xwise","ywise"]
		self.combo5.addItems(mylist5)
		self.combo5.setCurrentIndex(mylist5.index(self.scan_mode))
		
		resetmode_lbl = QtGui.QLabel("Reset", self)
		self.combo6 = QtGui.QComboBox(self)
		mylist6=["x","y","xy"]
		self.combo6.addItems(mylist6)
		self.combo6.setCurrentIndex(mylist6.index(self.reset_mode))
		
		dwelltime_lbl = QtGui.QLabel("Dwell time[s]",self)
		self.dwelltimeEdit = QtGui.QLineEdit(str(self.dwell_time),self)
		xy_limiter_lbl = QtGui.QLabel("XY-limiter[mm]",self)
		self.xy_limiterEdit = QtGui.QLineEdit(str(self.xy_limiter_mm),self)
		
		#####################################################
		
		lbl7 = QtGui.QLabel("SCAN or move values:", self)
		lbl7.setStyleSheet("color: blue")	
		
		start_lbl = QtGui.QLabel("Start[mm]",self)
		stop_lbl = QtGui.QLabel("Stop[mm]",self)
		step_lbl = QtGui.QLabel("Step[mm]",self)
		x_lbl = QtGui.QLabel("X-axis:    ",self)
		y_lbl = QtGui.QLabel("Y-axis:    ",self)
		self.xscanEdit = [QtGui.QLineEdit("",self) for tal in range(3)] 
		self.yscanEdit = [QtGui.QLineEdit("",self) for tal in range(3)]
		# set initial values into the fields
		for i in range(3):
			self.xscanEdit[i].setText(str(self.xscan[i]))
			self.yscanEdit[i].setText(str(self.yscan[i]))
		
		#####################################################
		
		lbl4 = QtGui.QLabel("STORAGE  and PLOT settings:", self)
		lbl4.setStyleSheet("color: blue")
		
		filename = QtGui.QLabel("File name",self)
		foldername = QtGui.QLabel("Folder name",self)
		self.filenameEdit = QtGui.QLineEdit(str(self.filename_str),self)
		self.folderEdit = QtGui.QLineEdit(str(self.folder_str),self)
		
		#####################################################
		
		schroll_lbl = QtGui.QLabel("Schroll elapsed time after",self)
		self.combo2 = QtGui.QComboBox(self)
		mylist2=[".2k points",".5k points","1k points","2k points","5k points","10k points"]
		mylist2_tal=[200,500,1000,2000,5000,10000]
		self.combo2.addItems(mylist2)
		# initial combo settings
		self.combo2.setCurrentIndex(0)
		self.schroll_time=mylist2_tal[0]
		
		#####################################################
		
		lbl5 = QtGui.QLabel("EXECUTE operation settings:", self)
		lbl5.setStyleSheet("color: blue")
		
		self.runButton = QtGui.QPushButton("Run",self)
		self.cancelButton = QtGui.QPushButton("STOP",self)
		self.cancelButton.setEnabled(False)
		
		#####################################################
		
		# status info which button has been pressed
		self.elapsedtime_str = QtGui.QLabel("TIME trace for storing plots and data:", self)
		self.elapsedtime_str.setStyleSheet("color: blue")
		
		self.lcd = QtGui.QLCDNumber(self)
		self.lcd.setStyleSheet("color: red")
		self.lcd.setFixedHeight(60)
		self.lcd.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd.setNumDigits(11)
		self.lcd.display(self.timestr)
			
		#####################################################
		#####################################################
		
		# Add all widgets		
		g1_0 = QtGui.QGridLayout()
		g1_0.addWidget(MyBar,0,0)
		g1_0.addWidget(lbl1,1,0)

		g1_1 = QtGui.QGridLayout()
		g1_1.addWidget(opmode_lbl,0,0)
		g1_1.addWidget(self.combo4,1,0)
		g1_1.addWidget(scanmode_lbl,0,1)
		g1_1.addWidget(self.combo5,1,1)
		g1_1.addWidget(resetmode_lbl,0,2)
		g1_1.addWidget(self.combo6,1,2)
		
		g1_2 = QtGui.QGridLayout()
		g1_2.addWidget(dwelltime_lbl,0,0)
		g1_2.addWidget(self.dwelltimeEdit,1,0)
		g1_2.addWidget(xy_limiter_lbl,0,1)
		g1_2.addWidget(self.xy_limiterEdit,1,1)
		
		v1 = QtGui.QVBoxLayout()
		v1.addLayout(g1_0)
		v1.addLayout(g1_1)
		v1.addLayout(g1_2)
		
		#####################################################
		
		g2_0 = QtGui.QGridLayout()
		g2_0.addWidget(lbl7,0,0)
		
		g2_1 = QtGui.QGridLayout()
		g2_1.addWidget(start_lbl,0,1)
		g2_1.addWidget(stop_lbl,0,2)
		g2_1.addWidget(step_lbl,0,3)
		g2_1.addWidget(x_lbl,1,0)
		g2_1.addWidget(y_lbl,2,0)
		for tal in range(3):
			g2_1.addWidget(self.xscanEdit[tal],1,1+tal)
			g2_1.addWidget(self.yscanEdit[tal],2,1+tal)
			
		v2 = QtGui.QVBoxLayout()
		v2.addLayout(g2_0)
		v2.addLayout(g2_1)
		
		#####################################################
		
		g3_0 = QtGui.QGridLayout()
		g3_0.addWidget(lbl4,0,0)
		
		g3_1 = QtGui.QGridLayout()
		g3_1.addWidget(filename,0,0)
		g3_1.addWidget(self.filenameEdit,1,0)
		g3_1.addWidget(foldername,0,1)
		g3_1.addWidget(self.folderEdit,1,1)
		
		g3_2 = QtGui.QGridLayout()
		g3_2.addWidget(schroll_lbl,0,0)
		g3_2.addWidget(self.combo2,0,1)
		
		v3 = QtGui.QVBoxLayout()
		v3.addLayout(g3_0)
		v3.addLayout(g3_1)
		v3.addLayout(g3_2)
		
		#####################################################
		
		g5_0 = QtGui.QGridLayout()
		g5_0.addWidget(lbl5,0,0)
		
		g5_1 = QtGui.QGridLayout()
		g5_1.addWidget(self.runButton,0,1)
		g5_1.addWidget(self.cancelButton,0,2)
		
		v5 = QtGui.QVBoxLayout()
		v5.addLayout(g5_0)
		v5.addLayout(g5_1)
		
		#####################################################
		
		g6_0 = QtGui.QGridLayout()
		g6_0.addWidget(self.elapsedtime_str,0,0)
		g6_0.addWidget(self.lcd,1,0)
		
		v6 = QtGui.QVBoxLayout()
		v6.addLayout(g6_0)
		
		#####################################################
		
		# add ALL groups from v1 to v6 in one vertical group v7
		v7 = QtGui.QVBoxLayout()
		v7.addLayout(v1)
		v7.addLayout(v2)
		v7.addLayout(v3)
		v7.addLayout(v5)
		v7.addLayout(v6)
	
		#####################################################
		
		# set GRAPHS and TOOLBARS to a new vertical group vcan
		vcan0 = QtGui.QGridLayout()
		self.pw1 = pg.PlotWidget() 
		vcan0.addWidget(self.pw1,0,0)
		self.pw2 = pg.PlotWidget()
		vcan0.addWidget(self.pw2,0,1)
		
		vcan1 = QtGui.QGridLayout()
		self.pw3 = pg.PlotWidget()
		vcan1.addWidget(self.pw3,0,0)
		self.pw5 = pg.PlotWidget()
		vcan1.addWidget(self.pw5,0,1)
		
		# SET ALL HORIZONTAL COLUMNS TOGETHER
		hbox = QtGui.QHBoxLayout()
		hbox.addLayout(v7,1)
		hbox.addLayout(vcan0,3.5)
		
		# SET VERTICAL COLUMNS TOGETHER TO FINAL LAYOUT
		vbox = QtGui.QVBoxLayout()
		vbox.addLayout(hbox)
		vbox.addLayout(vcan1)
		
		self.setLayout(vbox) 
		
		##############################################
		
		# INITIAL SETTINGS PLOT 1
		p0 = self.pw1.plotItem
		self.curve1=p0.plot(pen='w', symbol='o', symbolPen='w')
		self.curve2=p0.plot(pen='r', symbol='o', symbolPen='r')
		self.pw1.enableAutoRange()
		self.pw1.setTitle(''.join(["2-D scan pattern"]))
		self.pw1.setLabel('left', "Y", units='m', color='red')
		self.pw1.setLabel('bottom', "X", units='m', color='red')
		
		# INITIAL SETTINGS PLOT 2
		p6 = self.pw2.plotItem
		self.curve6=p6.plot(pen='w', symbol='o', symbolPen='w')
		self.pw2.setTitle(''.join(["Normalized surface spine, S"]))
		self.pw2.setLabel('left', "U_max", units='V', color='white')
		self.pw2.setLabel('bottom', "S", units='m', color='white')
		self.pw2.enableAutoRange()
		
		# INITIAL SETTINGS PLOT 5
		self.curve7=pg.ScatterPlotItem(size=10, pen=pg.mkPen(None), brush=pg.mkBrush(255, 255, 255, 120))
		self.pw5.setTitle(''.join(["U_max positions"]))
		self.pw5.setLabel('left', "Y", units='m', color='red')
		self.pw5.setLabel('bottom', "X", units='m', color='red')
		self.pw5.enableAutoRange()
		
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
		self.pw3.setTitle(''.join(["Voltage and position as function of time"]))
		self.pw3.setLabel('left', "Lock-in voltage", units='V', color='yellow')
		self.pw3.setLabel('right', "Scan axis", units='m', color='red')
		self.pw3.setLabel('bottom', "Elapsed time", units='s', color='white')
		
		# INITIAL SETTINGS PLOT 4
		self.pw4 = gl.GLViewWidget()
		self.pw4.opts['distance'] = 5
		self.pw4.setWindowTitle('Scatter plot of sweeped poins')
		gx = gl.GLGridItem()
		gx.rotate(90, 0, 1, 0)
		gx.translate(-1, 0, 0)
		gx.scale(0.1,0.1,0.1,local=True)
		self.pw4.addItem(gx)
		gy = gl.GLGridItem()
		gy.rotate(90, 1, 0, 0)
		gy.translate(0, -1, 0)
		gy.scale(0.1,0.1,0.1,local=True)
		self.pw4.addItem(gy)
		gz = gl.GLGridItem()
		gz.translate(0, 0, -1)
		gz.scale(0.1,0.1,0.1,local=True)
		self.pw4.addItem(gz)
		## create a new AxisItem, linked to view
		ax2 = gl.GLAxisItem()
		#ax2.setSize(x=10,y=10,z=10)
		self.pw4.addItem(ax2)
		#ax2.setLabel('latitude', color='#0000ff')
		self.sp1 = gl.GLScatterPlotItem()
		
		# Initialize and set titles and axis names for both plots
		
		##############################################
		
		# reacts to drop-down menus
		self.combo2.activated[str].connect(self.onActivated2)
		self.combo4.activated[str].connect(self.onActivated4)
		self.combo5.activated[str].connect(self.onActivated5)
		self.combo6.activated[str].connect(self.onActivated6)
	
		# run the main script
		self.runButton.clicked.connect(self.set_run)
		
		# cancel the script run
		self.cancelButton.clicked.connect(self.set_cancel)
		
		self.allEditFields(True)
		
		self.setGeometry(10, 10, 1300, 1100)
		self.setWindowTitle("IT6D CA2 Microstepper And SR5210 Lock-In Data Acqusition")
		self.show()
			
	def allEditFields(self,trueorfalse):
		
		if trueorfalse==False:
			self.combo4.setEnabled(False)
			self.combo5.setEnabled(False)
			self.combo6.setEnabled(False)
			self.cancelButton.setEnabled(True)
		else:
			self.combo4.setEnabled(True)
			self.onActivated4(self.op_mode)
			self.cancelButton.setEnabled(False)
		
		self.combo2.setEnabled(trueorfalse)
		self.dwelltimeEdit.setEnabled(trueorfalse)
		self.xy_limiterEdit.setEnabled(trueorfalse)
		for i in range(3):
			self.xscanEdit[i].setEnabled(trueorfalse)
			self.yscanEdit[i].setEnabled(trueorfalse)
			
		self.fileClose.setEnabled(trueorfalse)
		self.gpibIT6D_CA2.setEnabled(trueorfalse)
		self.gpibSR5210.setEnabled(trueorfalse)
		self.filenameEdit.setEnabled(trueorfalse)
		self.folderEdit.setEnabled(trueorfalse)
		self.runButton.setEnabled(trueorfalse)
	
	def IT6D_CA2Dialog(self):

		text, ok = QtGui.QInputDialog.getText(self, 'Gpib Port Dialog','Enter IT6D_CA2 microstepper port number:', text=self.it6d_ca2port_str)
		if ok:
			self.it6d_ca2port_str = str(text)
	
	def SR5210Dialog(self):

		text, ok = QtGui.QInputDialog.getText(self, 'Gpib Port Dialog','Enter SR5210 lock-in port number:', text=self.sr5210port_str)
		if ok:
			self.sr5210port_str = str(text)
	
	def onActivated2(self, text):
		
		if str(text)==".2k points":
			self.schroll_time=200
		elif str(text)==".5k points":
			self.schroll_time=500
		elif str(text)=="1k points":
			self.schroll_time=1000
		elif str(text)=="2k points":
			self.schroll_time=2000
		elif str(text)=="5k points":
			self.schroll_time=5000
		elif str(text)=="10k points":
			self.schroll_time=10000
		else:
			pass
	
	def onActivated6(self, text):
		
		self.reset_mode = str(text)
	
	def onActivated5(self, text):
		
		self.scan_mode = str(text)
	
	def onActivated4(self, text):
		
		self.op_mode = str(text)
		
		if self.op_mode=='xyscan':
			self.combo5.setEnabled(True)
			self.combo6.setEnabled(False)
			self.dwelltimeEdit.setEnabled(True)
			self.xy_limiterEdit.setEnabled(True)
			for i in range(3):
				self.xscanEdit[i].setEnabled(True)
				self.yscanEdit[i].setEnabled(True)
		elif self.op_mode=='xscan':	
			self.combo5.setEnabled(False)
			self.combo6.setEnabled(False)
			self.dwelltimeEdit.setEnabled(True)
			self.xy_limiterEdit.setEnabled(True)
			for i in range(3):
				self.xscanEdit[i].setEnabled(True)
				self.yscanEdit[i].setEnabled(False)
		elif self.op_mode=='yscan':
			self.combo5.setEnabled(False)
			self.combo6.setEnabled(False)
			self.dwelltimeEdit.setEnabled(True)
			self.xy_limiterEdit.setEnabled(True)
			for i in range(3):
				self.xscanEdit[i].setEnabled(False)
				self.yscanEdit[i].setEnabled(True)
		elif self.op_mode in ['move abs','move rel']:
			self.combo5.setEnabled(False)
			self.combo6.setEnabled(False)
			self.dwelltimeEdit.setEnabled(False)
			self.xy_limiterEdit.setEnabled(False)
			for i in range(3):
				if i==0:
					self.xscanEdit[i].setEnabled(True)
					self.yscanEdit[i].setEnabled(True)
				else:
					self.xscanEdit[i].setEnabled(False)
					self.yscanEdit[i].setEnabled(False)
		elif self.op_mode=='reset':
			self.combo5.setEnabled(False)
			self.combo6.setEnabled(True)
			self.dwelltimeEdit.setEnabled(False)
			self.xy_limiterEdit.setEnabled(False)
			for i in range(3):
				self.xscanEdit[i].setEnabled(False)
				self.yscanEdit[i].setEnabled(False)
		else:
			pass
		
	def set_run(self):
		
		xx = [int(1000*float(self.xscanEdit[i].text())) for i in range(3)]
		yy = [int(10000*float(self.yscanEdit[i].text())) for i in range(3)]
		self.sm = Methods_for_IT6D_CA2.Scan_methods(xx[0],xx[1],xx[2],yy[0],yy[1],yy[2])
		
		self.x_fields=numpy.arange(xx[0],xx[1]+xx[2],xx[2])/1e6
		self.y_fields=numpy.arange(yy[0],yy[1]+yy[2],yy[2])/1e7
		# Initial read of the config file		
		xscan = [float(self.xscanEdit[i].text()) for i in range(3)]
		yscan = [float(self.yscanEdit[i].text()) for i in range(3)]
		dwelltime = float(self.dwelltimeEdit.text())
		xy_limiter = float(self.xy_limiterEdit.text())
		filename = str(self.filenameEdit.text())
		folder = str(self.folderEdit.text())

		self.clear_vars_graphs()
		
		self.allEditFields(False)
		
		self.get_thread=Run_IT6D_CA2_Thread(self.op_mode,self.scan_mode,folder,filename,xscan,yscan,
																			dwelltime,self.reset_mode,xy_limiter,self.timestr,self.it6d_ca2port_str,self.sr5210port_str)
		
		if self.op_mode=='xyscan':
			self.all_xy()
			self.connect(self.get_thread, SIGNAL('make_update1(QString,QString,QString)'), self.make_update1)
			self.connect(self.get_thread, SIGNAL('make_update2(QString,QString,QString)'), self.make_update2)
			self.connect(self.get_thread, SIGNAL('make_update4(QString,QString)'), self.make_update4)
			self.connect(self.get_thread, SIGNAL('update_Spath(QString,QString,QString,QString)'), self.update_Spath)
			self.connect(self.get_thread, SIGNAL('scatter_plot()'), self.scatter_plot)
		elif self.op_mode=='xscan':
			self.connect(self.get_thread, SIGNAL('make_update1(QString,QString,QString)'), self.make_update1)
			self.connect(self.get_thread, SIGNAL('make_update2(QString,QString,QString)'), self.make_update2)
			self.connect(self.get_thread, SIGNAL('make_update4(QString,QString)'), self.make_update4)
			self.connect(self.get_thread, SIGNAL('pass_y_pos(QString)'), self.all_x)
		elif self.op_mode=='yscan':
			self.connect(self.get_thread, SIGNAL('make_update1(QString,QString,QString)'), self.make_update1)
			self.connect(self.get_thread, SIGNAL('make_update2(QString,QString,QString)'), self.make_update2)
			self.connect(self.get_thread, SIGNAL('make_update4(QString,QString)'), self.make_update4)
			self.connect(self.get_thread, SIGNAL('pass_x_pos(QString)'), self.all_y)
		elif self.op_mode=='move rel':
			pass
		elif self.op_mode=='move abs':
			pass
		elif self.op_mode=='reset':
			pass
		
		self.connect(self.get_thread, SIGNAL('finished()'), self.set_finished)

		self.get_thread.start()
	
	def make_update4(self,time_endpoint,volt_endpoint):
		
		# Update curve3 in different plot
		if len(self.all_pos)>self.schroll_time:
			self.acc_time_endpoint[:-1] = self.acc_time_endpoint[1:]  # shift data in the array one sample left
			self.acc_time_endpoint[-1] = float(time_endpoint)
			self.acc_volt_endpoint[:-1] = self.acc_volt_endpoint[1:]  # shift data in the array one sample left
			self.acc_volt_endpoint[-1] = float(volt_endpoint)
		else:
			self.acc_time_endpoint.extend([ float(time_endpoint) ])
			self.acc_volt_endpoint.extend([ float(volt_endpoint) ])
			
		self.curve3.setData(self.acc_time_endpoint,self.acc_volt_endpoint)
	
	def make_update1(self,x_pos,y_pos,volt):
		
		self.acc_x_pos.extend([ float(x_pos) ])
		self.acc_y_pos.extend([ float(y_pos) ])
		self.acc_volt.extend([ float(volt) ])
		self.curve2.setData(self.acc_x_pos,self.acc_y_pos)
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
	def scatter_plot(self):
		
		x=self.acc_x_pos
		y=self.acc_y_pos
		z=self.acc_volt
		pos=numpy.empty((len(z),3))
		size = numpy.empty((len(z)))
		color = numpy.empty((len(z), 4))
		for i in range(len(z)):
			size[i] = 1./40
			color[i] = (0.0, 0.5, 0.5, 1.0)
			pos[i]=(x[i],y[i],z[i])
		#pos = (self.acc_x_pos,self.acc_x_pos,self.acc_volt)
		self.sp1.setData(pos=pos, size=size, color=color, pxMode=False)
		self.pw4.addItem(self.sp1)
		
	def update_Spath(self,umax_X,umax_Y,S_last_point,Umax_last_point):
		
		self.S_path.extend([ float(S_last_point) ])
		self.U_max.extend([ float(Umax_last_point) ])
		self.curve6.setData(self.S_path,self.U_max)
		
		self.Umax_X_acc.extend([ float(umax_X) ])
		self.Umax_Y_acc.extend([ float(umax_Y) ])
		self.curve7.setData(self.Umax_X_acc,self.Umax_Y_acc)
		self.pw5.addItem(self.curve7)
		
	def all_x(self,val):
		
		i = self.x_fields
		j = len(i)*[float(val)]
		self.curve1.setData(i,j)
			
	def all_y(self,val):
		
		j = self.x_fields
		i = len(j)*[float(val)]
		self.curve1.setData(i,j)
		
	def all_xy(self):
		
		if self.scan_mode=='xsnake':
			i,j = self.sm.xsnake()
			i_ = [val/1e6 for val in i]
			j_ = [val/1e7 for val in j]
			self.curve1.setData(i_,j_)
		elif self.scan_mode=='ysnake':
			i,j = self.sm.ysnake()
			i_ = [val/1e6 for val in i]
			j_ = [val/1e7 for val in j]
			self.curve1.setData(i_,j_)
		elif self.scan_mode=='xwise':
			i,j = self.sm.xwise()
			i_ = [val/1e6 for val in i]
			j_ = [val/1e7 for val in j]
			self.curve1.setData(i_,j_)
		elif self.scan_mode=='ywise':
			i,j = self.sm.ywise()
			i_ = [val/1e6 for val in i]
			j_ = [val/1e7 for val in j]
			self.curve1.setData(i_,j_)
		else:
			pass
			
	def make_update2(self,time_elap,pos,volt):
    
		self.all_pos.extend([ float(pos) ])
		if len(self.all_pos)>self.schroll_time:
			self.plot_time_tt[:-1] = self.plot_time_tt[1:]  # shift data in the array one sample left
			self.plot_time_tt[-1] = float(time_elap)
			self.plot_pos_tt[:-1] = self.plot_pos_tt[1:]  # shift data in the array one sample left
			self.plot_pos_tt[-1] = float(pos)
			self.plot_volts_tt[:-1] = self.plot_volts_tt[1:]  # shift data in the array one sample left
			self.plot_volts_tt[-1] = float(volt)
		else:
			self.plot_time_tt.extend([ float(time_elap) ])
			self.plot_pos_tt.extend([ float(pos) ])
			self.plot_volts_tt.extend([ float(volt) ])
			

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
		self.curve4.setData(self.plot_time_tt, self.plot_volts_tt)
		self.curve5.setData(self.plot_time_tt, self.plot_pos_tt)
			
	def set_cancel(self):

		self.get_thread.abort()
		
	def clear_vars_graphs(self):
		
		# PLOT 1 initial canvas settings
		self.all_pos=[]
		self.acc_x_pos=[]
		self.acc_y_pos=[]
		self.acc_volt=[]
		self.curve1.clear()
		self.curve2.clear()
		
		# PLOT 2 initial canvas settings
		self.S_path=[]
		self.U_max=[]
		self.curve6.clear()
		
		# PLOT 5 initial canvas settings
		self.Umax_X_acc=[]
		self.Umax_Y_acc=[]
		self.curve7.clear()
		
		# PLOT 3 initial canvas settings
		self.plot_time_tt=[]
		self.plot_volts_tt=[]
		self.plot_pos_tt=[]
		self.acc_time_endpoint=[]
		self.acc_volt_endpoint=[]
		# create plot and add it to the figure canvas
		self.curve3.clear()
		self.curve4.clear()
		self.curve5.clear()
		
		if self.op_mode=='xyscan':
			# PLOT 4 initial canvas settings
			self.pw4.show()
		else:
			self.pw4.close()
			
	def set_save(self):
		
		self.timestr=time.strftime("%y%m%d-%H%M")
		with open("config_Run_IT6D_CA2.py", 'w') as thefile:
			thefile.write( ''.join(["op_mode=\"",self.op_mode,"\"\n"]) )
			thefile.write( ''.join(["scan_mode=\"",self.scan_mode,"\"\n"]) )
			thefile.write( ''.join(["new_folder=\"",str(self.folderEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["filename=\"",str(self.filenameEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["x_scan_mm=[",','.join([str(self.xscanEdit[ii].text()) for ii in range(3)]),"]\n"]) )
			thefile.write( ''.join(["y_scan_mm=[",','.join([str(self.yscanEdit[ii].text()) for ii in range(3)]),"]\n"]) )
			thefile.write( ''.join(["wait_time=",str(self.dwelltimeEdit.text()),"\n"]) )
			thefile.write( ''.join(["reset_mode=\"",self.reset_mode,"\"\n"]) )
			thefile.write( ''.join(["xy_limiter_mm=",str(self.xy_limiterEdit.text()),"\n"]) )
			thefile.write( ''.join(["timestr=\"",self.timestr,"\"\n"]) )
			thefile.write( ''.join(["it6d_ca2port=\"",self.it6d_ca2port_str,"\"\n"]) )
			thefile.write( ''.join(["sr5210port=\"",self.sr5210port_str,"\""]) )
		
		reload(config_Run_IT6D_CA2)
		self.op_mode = config_Run_IT6D_CA2.op_mode
		self.scan_mode = config_Run_IT6D_CA2.scan_mode
		self.folder_str=config_Run_IT6D_CA2.new_folder
		self.filename_str=config_Run_IT6D_CA2.filename
		self.xscan = config_Run_IT6D_CA2.x_scan_mm
		self.yscan = config_Run_IT6D_CA2.y_scan_mm
		self.dwell_time = config_Run_IT6D_CA2.wait_time
		self.reset_mode = config_Run_IT6D_CA2.reset_mode
		self.xy_limiter_mm = config_Run_IT6D_CA2.xy_limiter_mm
		self.timestr=config_Run_IT6D_CA2.timestr
		self.it6d_ca2port_str=config_Run_IT6D_CA2.it6d_ca2port
		self.sr5210port_str=config_Run_IT6D_CA2.sr5210port
		
		self.lcd.display(self.timestr)
	
	def set_finished(self):

		self.allEditFields(True)

	def closeEvent(self, event):
		
		reply = QtGui.QMessageBox.question(self, 'Message', "Quit now? Any changes that are not saved will stay unsaved!", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes:
			if not hasattr(self, 'get_thread'):
				event.accept()
			else:
				if self.get_thread.isRunning():
					QtGui.QMessageBox.warning(self, 'Message', "Run in progress. Cancel the run then quit!")
					event.ignore()
				else:
					event.accept()
		else:
		  event.ignore() 
		
	##########################################
	
	def set_save_plots(self):
		
		self.filename_str=str(self.filenameEdit.text())
		self.folder_str=str(self.folderEdit.text())
		
		# For SAVING graphs
		if self.filename_str:
			self.full_filename=''.join([self.filename_str,self.timestr])
			self.full_filename_time=''.join([self.filename_str,"elapsedtime_",self.timestr])
		else:
			self.full_filename=''.join(["data_",self.timestr])
			self.full_filename_time=''.join(["data_elapsedtime_",self.timestr])
			
		if self.folder_str:
			self.saveinfolder=''.join([self.folder_str,"/"])
			if not os.path.isdir(self.folder_str):
				os.mkdir(self.folder_str)
		else:
			self.saveinfolder=""
		
		save_plot1=''.join([self.saveinfolder,self.full_filename,'.png'])	
		save_plot2=''.join([self.saveinfolder,self.full_filename_time,'.png'])	
		save_plot3=''.join([self.saveinfolder,self.full_filename,'_3Dscatter.png'])	

		# create an exporter instance, as an argument give it
		# the item you wish to export
		exporter = pg.exporters.ImageExporter(self.pw1.plotItem)
		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_plot1)
		
		exporter = pg.exporters.ImageExporter(self.pw2.plotItem)
		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_plot2)
		
		
		d = self.pw4.renderToArray((1000, 1000))
		pg.makeQImage(d).save(save_plot3)
		
#########################################
#########################################
#########################################

def main():
	
	app = QtGui.QApplication(sys.argv)
	ex = Run_IT6D_CA2()
	sys.exit(app.exec_())

if __name__ == '__main__':
	
	main()