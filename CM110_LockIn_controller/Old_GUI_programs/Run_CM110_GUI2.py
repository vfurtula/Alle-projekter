import os, sys, time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np
from pyqtgraph.Qt import QtCore, QtGui
#from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, SIGNAL
import config_CM110, Run_CM110_v8


if len(sys.argv)>1:
	raise ValueError('The function takes exactly 1 input argument!')
elif len(sys.argv)==1:
	start_str = config_CM110.Start
	stop_str = config_CM110.Stop
	step_str = config_CM110.Step
	dwell_time_str = config_CM110.Wait_time
	avg_pts = config_CM110.Avg_pts
	expand_str = config_CM110.Expand
	offset_str = config_CM110.Offset
	sens_str = config_CM110.Sensitivity
	unit_str = config_CM110.Sens_unit
	filename_str=config_CM110.filename
	folder_str=config_CM110.create_folder
	cm110port_str=config_CM110.cm110port
	ardport_str=config_CM110.ardport

'''
class runCM110(QThread):
  def __init__(self,bo,boo,num,mytext):
    QThread.__init__(self)
    self.bo=bo
    self.boo=boo
    self.num=num
    if not str(mytext):
      self.mytext='data.txt'
    else:
      self.mytext=''.join([str(mytext),'.txt'])

  def __del__(self):
    self.wait()

  def run(self):
    # your logic here
    #plt.plot(range(1000), np.array(range(1000))**2)
    #plt.show()
    #myplot_v1.main()
    ii=self.bo
    ss=self.boo
        
    while ii<ss:
      #text=str(int(self.lbl)+int(self.combo))
      with open(self.mytext,'a') as thefile:
				thefile.write('%s\n' %ii)
	
      self.emit(SIGNAL('make_update(QString)'),str(ii))
      ii+=self.num
      time.sleep(0.5)
      
'''

class runCM110(QThread):
	
	def __init__(self):
		QThread.__init__(self)
		
	def __del__(self):
		self.wait()
		
	def run(self):
		Run_CM110_v8.main()
		#self.emit(SIGNAL('make_update(QString)'),f1.readline())
		
		############################################################
		
class CM110(QtGui.QWidget):

	def __init__(self):
		super(CM110, self).__init__()
		
		# a figure instance to plot on
		self.figure = plt.figure()
		# this is the Canvas Widget that displays the `figure`
		# it takes the `figure` instance as a parameter to __init__
		self.canvas = FigureCanvas(self.figure)

		# this is the Navigation widget
		# it takes the Canvas widget and a parent
		self.toolbar = NavigationToolbar(self.canvas, self)
		
		# real-time figure ipdate
		#self.on_launch()
		
		self.initUI()
			
	def initUI(self): 
		
		#####################################################
		lbl1 = QtGui.QLabel('MONOCHROMATOR CM110 settings:', self)
		lbl1.setStyleSheet('color: blue')
		start = QtGui.QLabel('Start [nm]',self)
		stop = QtGui.QLabel('Stop [nm]',self)
		step = QtGui.QLabel('Step [nm]',self)
		cm110port = QtGui.QLabel('CM110 serial port',self)
		self.startEdit = QtGui.QLineEdit(str(start_str),self)
		self.stopEdit = QtGui.QLineEdit(str(stop_str),self)
		self.stepEdit = QtGui.QLineEdit(str(step_str),self)
		self.cm110portEdit = QtGui.QLineEdit(str(cm110port_str),self)
		
		lbl2 = QtGui.QLabel('ARDUINO Mega2560 settings:', self)
		lbl2.setStyleSheet('color: blue')
		dwelltime = QtGui.QLabel('Dwell time [sec]',self)
		avgpts_lbl = QtGui.QLabel('Averaging points', self)
		ardport = QtGui.QLabel('Arduino serial port',self)
		self.dwelltimeEdit = QtGui.QLineEdit(str(dwell_time_str),self)
		self.ardportEdit = QtGui.QLineEdit(str(ardport_str),self)
		self.combo1 = QtGui.QComboBox(self)
		mylist=['1', '5','10','20','50','100','200']
		self.combo1.addItems(mylist)
		self.combo1.setCurrentIndex(mylist.index(str(avg_pts)))
		self.avgpts=avg_pts
		
		lbl3 = QtGui.QLabel('LOCK-IN amplifier settings:', self)
		lbl3.setStyleSheet('color: blue')
		expand = QtGui.QLabel('Expand',self)
		self.expandEdit = QtGui.QLineEdit(str(expand_str),self)
		offset = QtGui.QLabel('Offset',self)
		self.offsetEdit = QtGui.QLineEdit(str(offset_str),self)
		sens = QtGui.QLabel('Sensitivity ',self)
		self.sensEdit = QtGui.QLineEdit(str(sens_str),self)
		unit = QtGui.QLabel('Sensitivity unit',self)
		self.unitEdit = QtGui.QLineEdit(str(unit_str),self)
		
		lbl4 = QtGui.QLabel('STORAGE location settings:', self)
		lbl4.setStyleSheet('color: blue')
		filename = QtGui.QLabel('Save to the file',self)
		self.filenameEdit = QtGui.QLineEdit(str(filename_str),self)
		folder = QtGui.QLabel('Save to the folder',self)
		self.folderEdit = QtGui.QLineEdit(str(folder_str),self)
		
		##############################################
		
		lbl5 = QtGui.QLabel('RECORD data and save images:', self)
		lbl5.setStyleSheet('color: blue')
		
		save_str = QtGui.QLabel('Save changes to the config file', self)
		self.saveButton = QtGui.QPushButton("Save",self)
		
		run_str = QtGui.QLabel('Record lock-in data', self)
		self.runButton = QtGui.QPushButton("Run",self)
		self.runButton.setEnabled(False)
		
		plot_str = QtGui.QLabel('Show voltage vs. wavelength', self)
		self.plotButton = QtGui.QPushButton("Plot 1",self)
		self.plotButton.setEnabled(False)
		
		timetrace_str = QtGui.QLabel('Show voltage vs. time', self)
		self.timetraceButton = QtGui.QPushButton("Plot 2",self)
		self.timetraceButton.setEnabled(False)
		
		cancel_str = QtGui.QLabel('Cancel current run', self)
		self.cancelButton = QtGui.QPushButton("Cancel",self)
		self.cancelButton.setEnabled(False)
		
		##############################################
		'''
		# status info which button has been pressed
		self.status_str = QtGui.QLabel('PRESS SAVE!', self)
		self.status_str.setStyleSheet('color: red')
		'''
		##############################################
		
		# status info which button has been pressed
		self.timetrace_str = QtGui.QLabel('TIME trace used for storing the data:', self)
		self.timetrace_str.setStyleSheet('color: blue')
		
		##############################################
		
		self.lcd = QtGui.QLCDNumber(self)
		self.lcd.setStyleSheet('color: red')
		self.lcd.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd.setNumDigits(13)
		self.lcd.display("")
			
		##############################################
		# Add all widgets
		g1_0 = QtGui.QGridLayout()
		g1_0.addWidget(lbl1,0,0)
		g1_1 = QtGui.QGridLayout()
		g1_1.addWidget(cm110port,0,0)
		g1_1.addWidget(start,1,0)
		g1_1.addWidget(stop,2,0)
		g1_1.addWidget(step,3,0)
		g1_1.addWidget(self.cm110portEdit,0,1)
		g1_1.addWidget(self.startEdit,1,1)
		g1_1.addWidget(self.stopEdit,2,1)
		g1_1.addWidget(self.stepEdit,3,1)
		v1 = QtGui.QVBoxLayout()
		v1.addLayout(g1_0)
		v1.addLayout(g1_1)
		
		g2_0 = QtGui.QGridLayout()
		g2_0.addWidget(lbl2,0,0)
		g2_1 = QtGui.QGridLayout()
		g2_1.addWidget(ardport,0,0)
		g2_1.addWidget(dwelltime,1,0)
		g2_1.addWidget(avgpts_lbl,2,0)
		g2_1.addWidget(self.ardportEdit,0,1)
		g2_1.addWidget(self.dwelltimeEdit,1,1)
		g2_1.addWidget(self.combo1,2,1)
		v2 = QtGui.QVBoxLayout()
		v2.addLayout(g2_0)
		v2.addLayout(g2_1)
		
		g3_0 = QtGui.QGridLayout()
		g3_0.addWidget(lbl3,0,0)
		g3_1 = QtGui.QGridLayout()
		g3_1.addWidget(expand,0,0)
		g3_1.addWidget(offset,1,0)
		g3_1.addWidget(sens,2,0)
		g3_1.addWidget(unit,3,0)
		g3_1.addWidget(self.expandEdit,0,1)
		g3_1.addWidget(self.offsetEdit,1,1)
		g3_1.addWidget(self.sensEdit,2,1)
		g3_1.addWidget(self.unitEdit,3,1)
		v3 = QtGui.QVBoxLayout()
		v3.addLayout(g3_0)
		v3.addLayout(g3_1)
		
		g4_0 = QtGui.QGridLayout()
		g4_0.addWidget(lbl4,0,0)
		g4_1 = QtGui.QGridLayout()
		g4_1.addWidget(filename,0,0)
		g4_1.addWidget(folder,1,0)
		g4_1.addWidget(self.filenameEdit,0,1)
		g4_1.addWidget(self.folderEdit,1,1)
		v4 = QtGui.QVBoxLayout()
		v4.addLayout(g4_0)
		v4.addLayout(g4_1)
		
		g5_0 = QtGui.QGridLayout()
		g5_0.addWidget(lbl5,0,0)
		g5_1 = QtGui.QGridLayout()
		g5_1.addWidget(save_str,0,0)
		g5_1.addWidget(run_str,1,0)
		g5_1.addWidget(plot_str,2,0)
		g5_1.addWidget(timetrace_str,3,0)
		g5_1.addWidget(cancel_str,4,0)
		g5_1.addWidget(self.saveButton,0,1)
		g5_1.addWidget(self.runButton,1,1)
		g5_1.addWidget(self.plotButton,2,1)
		g5_1.addWidget(self.timetraceButton,3,1)
		g5_1.addWidget(self.cancelButton,4,1)
		v5 = QtGui.QVBoxLayout()
		v5.addLayout(g5_0)
		v5.addLayout(g5_1)
		
		g6_0 = QtGui.QGridLayout()
		#g6_0.addWidget(self.status_str,1,0)
		g6_0.addWidget(self.timetrace_str,1,0)
		g6_1 = QtGui.QGridLayout()
		g6_1.addWidget(self.lcd,0,0)
		v6 = QtGui.QVBoxLayout()
		v6.addLayout(g6_0)
		v6.addLayout(g6_1)
		
		# add all groups from v1 to v6 in one vertical group v7
		v7 = QtGui.QVBoxLayout()
		v7.addLayout(v1)
		v7.addLayout(v2)
		v7.addLayout(v3)
		v7.addLayout(v4)
		v7.addLayout(v5)
		v7.addLayout(v6)
	
		# set graph  and toolbar to a new vertical group vcan
		vcan = QtGui.QVBoxLayout()
		vcan.addWidget(self.toolbar)
		vcan.addWidget(self.canvas)

		# SET ALL VERTICAL COLUMNS TOGETHER
		hbox = QtGui.QHBoxLayout()
		hbox.addLayout(v7)
		hbox.addLayout(vcan,1)
		self.setLayout(hbox) 
		
    ##############################################
		
		# send status info which button has been pressed
		'''
		self.saveButton.clicked.connect(self.buttonClicked)
		self.runButton.clicked.connect(self.buttonClicked)
		self.cancelButton.clicked.connect(self.buttonClicked)
		self.plotButton.clicked.connect(self.buttonClicked)
		self.timetraceButton.clicked.connect(self.buttonClicked)
		'''
		
		# reacts to choises picked in the menu
		self.combo1.activated[str].connect(self.onActivated)
		
		# save all paramter data in the config file
		self.saveButton.clicked.connect(self.set_save)
		self.saveButton.clicked.connect(self.set_timetrace_text)
	
		# run the main script
		self.runButton.clicked.connect(self.set_run)
		
		# plot the collected data
		self.plotButton.clicked.connect(self.make_plot1)
		
		# plot the collected data
		self.timetraceButton.clicked.connect(self.make_plot2)
		
		# cancel the script run
		self.cancelButton.clicked.connect(self.set_cancel)
		
		self.setGeometry(100, 100, 1300, 1000)
		self.setWindowTitle('Monochromator CM110 Control Box And Data Acqusition')
		self.show()
		
		
		
		'''
		reload(config_CM110)
		start_str = config_CM110.Start
		stop_str = config_CM110.Stop
		step_str = config_CM110.Step
		filename_str=config_CM110.filename
		folder_str=config_CM110.create_folder
		timestr=config_CM110.timestr
		full_filename=''.join([ filename_str,timestr ])
		saveinfolder=''.join([folder_str,'/'])
		
		
		myrange=range(start_str,stop_str+step_str,step_str)
		# Read data file or wait for it
		myfile=''.join([saveinfolder,full_filename,'.txt'])
		while not os.path.exists(myfile):
			time.sleep(.25)
		
		if os.path.isfile(myfile):
			print 'geeeeeeeeed'
			wl=[]
			uvolts=[]
			time_endpoints=[]
			# Read new datafile
			f1 = open(myfile, 'r')
			f1.readline()
			f1.readline()
			for i in myrange:
				print f1.readline()
				
				line = f1.readline()
				columns = line.split()
				wl.extend([ float(columns[0]) ])
				uvolts.extend([ float(columns[1]) ])
				time_endpoints.extend([ float(columns[3]) ])
				# update the graph
				self.on_running(wl,uvolts)
				
			f1.close()
			
		else:
			raise ValueError("%s isn't a file!" % myfile)
		'''
	
	def allEditFields(self,trueorfalse):
		
		self.startEdit.setEnabled(trueorfalse)
		self.stopEdit.setEnabled(trueorfalse)
		self.stepEdit.setEnabled(trueorfalse)
		self.dwelltimeEdit.setEnabled(trueorfalse)
		self.combo1.setEnabled(trueorfalse)
		self.expandEdit.setEnabled(trueorfalse)
		self.offsetEdit.setEnabled(trueorfalse)
		self.sensEdit.setEnabled(trueorfalse)
		self.unitEdit.setEnabled(trueorfalse)
		self.filenameEdit.setEnabled(trueorfalse)
		self.folderEdit.setEnabled(trueorfalse)
		self.cm110portEdit.setEnabled(trueorfalse)
		self.ardportEdit.setEnabled(trueorfalse)
	
	'''
	def buttonClicked(self):
  
		sender = self.sender()
		self.status_str.setText(sender.text() + ' was pressed!')
		self.status_str.adjustSize()
		#self.statusBar().showMessage(sender.text() + ' was pressed')
	'''
	
	def set_timetrace_text(self):
		
		self.lcd.display(self.timetrace)
		#self.timetrace_str.setText(self.timetrace)
		#self.timetrace_str.adjustSize()
		
	def onActivated(self, text):
		
		self.avgpts = str(text)

	def set_cancel(self):
		
		#self.get_thread = runCM110('cancel')
		#self.connect(self.get_thread, SIGNAL("make_update(QString)"), self.make_update)
		
		self.allEditFields(True)
		self.saveButton.setEnabled(True)
		self.cancelButton.setEnabled(False)
		self.runButton.setEnabled(True)
		self.plotButton.setEnabled(True)
		self.timetraceButton.setEnabled(True)
		self.make_plot1()
		
	def set_save(self):
		
		self.allEditFields(True)
		self.saveButton.setEnabled(True)
		self.cancelButton.setEnabled(False)
		self.runButton.setEnabled(True)
		self.plotButton.setEnabled(False)
		self.timetraceButton.setEnabled(False)
		
		'''
		# replace all occurrences of 'sit' with 'SIT' and insert a line after the 5th
		for i, line in enumerate(fileinput.input(my_file_config, inplace=1)):
			if i==28: 
				sys.stdout.write(line.replace('start', 'START'))
		'''
		
		timestr=time.strftime("%Y%m%d-%H%M%S")
		self.timetrace=timestr
		analogRef=5 # units in Volts
		
		with open('config_CM110.py', 'w') as thefile:
			thefile.write( ''.join(['Start=',str(self.startEdit.text()),'\n']) )
			thefile.write( ''.join(['Stop=',str(self.stopEdit.text()),'\n']) )
			thefile.write( ''.join(['Step=',str(self.stepEdit.text()),'\n']) )
			thefile.write( ''.join(['Wait_time=',str(self.dwelltimeEdit.text()),'\n']) )
			thefile.write( ''.join(['Avg_pts=',str(self.avgpts),'\n']) )
			thefile.write( ''.join(['Expand=',str(self.expandEdit.text()),'\n']) )
			thefile.write( ''.join(['Offset=',str(self.offsetEdit.text()),'\n']) )
			thefile.write( ''.join(['Sensitivity=',str(self.sensEdit.text()),'\n']) )
			thefile.write( ''.join(['Sens_unit=\'',str(self.unitEdit.text()),'\'\n']) )
			thefile.write( ''.join(['filename=\'',str(self.filenameEdit.text()),'\'\n']) )
			thefile.write( ''.join(['create_folder=\'',str(self.folderEdit.text()),'\'\n']) )
			thefile.write( ''.join(['timestr=\'',timestr,'\'\n']) )
			thefile.write( ''.join(['analogref=',str(analogRef),'\n']) )
			thefile.write( ''.join(['cm110port=\'',str(self.cm110portEdit.text()),'\'\n']) )
			thefile.write( ''.join(['ardport=\'',str(self.ardportEdit.text()),'\'\n']) )
		
		reload(config_CM110)
		dwell_time_str = config_CM110.Wait_time
		avg_pts = config_CM110.Avg_pts
		unit_str = config_CM110.Sens_unit
		filename_str=config_CM110.filename
		folder_str=config_CM110.create_folder
		timestr=config_CM110.timestr
		
		self.unit_str=unit_str
		self.dwell_time_str=dwell_time_str
		self.avg_pts=avg_pts
		
		self.full_filename=''.join([ filename_str,timestr ])
		self.full_filename_time=''.join([ filename_str,'timetrace_',timestr ])
		self.saveinfolder=''.join([folder_str,'/'])
	
	'''
	# real-time plotting
	def on_launch(self):		
		#Set up plot
		#self.ax = self.figure.add_subplot(111)
		self.ax = plt.axes(ylim=(0, 1023))
		self.line1, = plt.plot([], [], 'ko-')
		#l=plt.legend(loc=1, fontsize=15)
		#l.draw_frame(False)

		#Autoscale on unknown axis and known lims on the other
		self.ax.set_autoscaley_on(True)
		#self.ax.set_xlim(self.min_x, self.max_x)

		string_1 = ''.join([r'Microcontroller step, arb. unit'])
		plt.xlabel(string_1, fontsize=20)
		plt.ylabel("Bits, arb. units", fontsize=20)
		plt.tick_params(axis="both", labelsize=20)
       
	def on_running(self, xdata, ydata):
		#Update data (with the new _and_ the old points)
		self.line1.set_xdata(xdata)
		self.line1.set_ydata(ydata)
		#Need both of these in order to rescale
		self.ax.relim()
		self.ax.autoscale_view()
		#We need to draw *and* flush
		self.figure.canvas.draw()
		self.figure.canvas.flush_events()
	'''
	
	def set_run(self):
		
		self.get_thread = runCM110()
		
		#self.connect(self.get_thread, SIGNAL("make_update(QString)"), self.make_update)
		self.connect(self.get_thread, SIGNAL("finished()"), self.set_finished)

		self.get_thread.start()
		
		self.allEditFields(False)
		self.saveButton.setEnabled(False)
		self.cancelButton.setEnabled(True)
		self.runButton.setEnabled(False)
		self.plotButton.setEnabled(False)
		self.timetraceButton.setEnabled(False)
				
		self.cancelButton.clicked.connect(self.get_thread.terminate)
		
	
		
	'''
	def make_update(self,endpoints):
    
		self.time_endpoints=endpoints
		#self.lcd.adjustSize()

		#self.lbl.setText(ii)
		#self.lbl.adjustSize() 
	'''
	
	def set_finished(self):
		
		self.allEditFields(True)
		self.saveButton.setEnabled(True)
		self.cancelButton.setEnabled(False)
		self.runButton.setEnabled(True)
		self.plotButton.setEnabled(True)
		self.timetraceButton.setEnabled(True)
		self.make_plot1()
	
	def make_plot1(self):

		# open the textfile for plotting
		#self.full_filename=''.join([ filename_str,config_CM110.timestr ])
		#self.saveinfolder=''.join([folder_str,'/'])
		f1 = open(''.join([self.saveinfolder,self.full_filename,'.txt']), 'r')
		ignore_lines=[0,1]
		for i in ignore_lines:
			f1.readline()
		wl=[]
		uvolts=[]
		time_endpoints=[]
		# Read new datafile
		for line in f1:
			columns = line.split()
			wl.extend([ float(columns[0]) ])
			uvolts.extend([ float(columns[1]) ])
			time_endpoints.extend([ float(columns[3]) ])
		f1.close()

		# set up animation figure and background
		self.figure.clf()
		ax = self.figure.add_subplot(111)
		# discards the old graph
		ax.hold(False)
		# plot data
		ax.plot(wl, uvolts, '-bo', label='end points')
		#plt.plot(all_positions, all_data, 'rx', label='all data')
		
		ax.set_xlabel("Wavelength, nm", fontsize=15)
		ax.set_ylabel(''.join(["Lock-in voltage, ", self.unit_str]), fontsize=15)
		ax.set_title(''.join(["PLOT 1: Wait-time ",str(self.dwell_time_str),"s, ","Avg.pts. ",str(self.avg_pts)]))
		ax.tick_params(axis="both", labelsize=15)
		l=ax.legend(loc=1, fontsize=12)
		l.draw_frame(False)

		# save and refresh canvas
		plt.savefig(''.join([self.saveinfolder,self.full_filename,'.png']) )
		self.canvas.draw()
		
	def make_plot2(self):
		
		# open the textfile for plotting
		#self.full_filename_time=''.join([ filename_str,'timetrace_',config_CM110.timestr ])
		f1 = open(''.join([self.saveinfolder,self.full_filename,'.txt']), 'r')
		ignore_lines=[0,1]
		for i in ignore_lines:
			f1.readline()
		uvolts=[]
		time_endpoints=[]
		# Read new datafile
		for line in f1:
			columns = line.split()
			uvolts.extend([ float(columns[1]) ])
			time_endpoints.extend([ float(columns[3]) ])
		f1.close()
		
		f2 = open(''.join([self.saveinfolder,self.full_filename_time,'.txt']), 'r')
		all_data=[]
		timelist=[]
		all_positions=[]
		# Read new datafile
		for line in f2:
			columns = line.split()
			all_positions.extend([ float(columns[0])  ])
			all_data.extend([ float(columns[1]) ])
			timelist.extend([ float(columns[3]) ])
		f2.close()

		# set up animation figure and background
		self.figure.clf()
		ax = self.figure.add_subplot(111)
		# discards the old graph
		ax.hold(False)
		# plot data
		ax.plot(timelist, all_positions, 'k-')
		ax2 = ax.twinx()
		ax2.plot(timelist, all_data, 'r-', label='all points')
		ax2.plot(time_endpoints, uvolts, '--ro', label='end points')

		string_1 = ''.join(["Wavelength, nm"])
		ax.set_ylabel(string_1, fontsize=15)
		ax.set_xlabel("Elapsed time, s", fontsize=15)
		ax.tick_params(axis="both", labelsize=15)
		ax.set_title(''.join(["PLOT 2: Wait-time ",str(self.dwell_time_str),"s, ","Avg.pts. ",str(self.avg_pts)]))
		l=plt.legend(loc=1, fontsize=12)
		l.draw_frame(False)

		ax2.set_ylabel(''.join(["Lock-in voltage, ", self.unit_str]), fontsize=15, color='r')
		ax2.tick_params(axis="y", labelsize=15)
		for tl in ax2.get_yticklabels():
			tl.set_color('r')
		
		# save and refresh canvas
		plt.savefig(''.join([self.saveinfolder,self.full_filename_time,'.png']) )
		self.canvas.draw()
		
#########################################
#########################################
#########################################
def main():
	
	app = QtGui.QApplication(sys.argv)
	ex = CM110()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()