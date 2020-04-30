import sys
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, SIGNAL
import config_CM110, Run_CM110_v8

if len(sys.argv)>1:
	raise ValueError('The function takes exactly 1 input argument!')
elif len(sys.argv)==1:
	start_str = config_CM110.Start
	stop_str = config_CM110.Stop
	step_str = config_CM110.Step
	dwell_time_str = config_CM110.Wait_time
	avg_pts_str = config_CM110.Avg_pts
	expand_str = config_CM110.Expand
	offset_str = config_CM110.Offset
	sens_str = config_CM110.Sensitivity
	unit_str = config_CM110.Sens_unit
	filename_str=config_CM110.filename
	folder_str=config_CM110.create_folder


class runCM110(QThread):
    def __init__(self):
        QThread.__init__(self)
    def __del__(self):
        self.wait()
    def run(self):
			Run_CM110_v8.main()


class Example(QtGui.QWidget):

	def __init__(self):
		super(Example, self).__init__()
		
		self.initUI()
			
	def initUI(self): 
		
		self.lbl_test='1'
		#self.lbl_test.move(30+100, 850)
		
		#####################################################
		lbl2 = QtGui.QLabel('Monochromator CM110 parameters:', self)
		start = QtGui.QLabel('Start [nm]',self)
		stop = QtGui.QLabel('Stop [nm]',self)
		step = QtGui.QLabel('Step [nm]',self)
		self.startEdit = QtGui.QLineEdit(str(start_str),self)
		self.stopEdit = QtGui.QLineEdit(str(stop_str),self)
		self.stepEdit = QtGui.QLineEdit(str(step_str),self)
		
		lbl3 = QtGui.QLabel('Arduino Mega2560 parameters:', self)
		dwelltime = QtGui.QLabel('Dwell time [sec]',self)
		self.dwelltimeEdit = QtGui.QLineEdit(str(dwell_time_str),self)
		lbl1 = QtGui.QLabel('Averaging points', self)
		combo1 = QtGui.QComboBox(self)
		combo1.addItem("1")
		combo1.addItem("5")
		combo1.addItem("10")
		combo1.addItem("20")
		combo1.addItem("50")
		combo1.addItem("100")
		combo1.addItem("200")
		
		lbl4 = QtGui.QLabel('Lock-in amplifier parameters:', self)
		expand = QtGui.QLabel('Expand',self)
		self.expandEdit = QtGui.QLineEdit(str(expand_str),self)
		offset = QtGui.QLabel('Offset',self)
		self.offsetEdit = QtGui.QLineEdit(str(offset_str),self)
		sens = QtGui.QLabel('Sensitivity ',self)
		self.sensEdit = QtGui.QLineEdit(str(sens_str),self)
		unit = QtGui.QLabel('Sensitivity unit',self)
		self.unitEdit = QtGui.QLineEdit(str(unit_str),self)
		
		lbl5 = QtGui.QLabel('Save to local memory parameters:', self)
		filename = QtGui.QLabel('Save to file',self)
		self.filenameEdit = QtGui.QLineEdit(str(filename_str),self)
		folder = QtGui.QLabel('Save to folder',self)
		self.folderEdit = QtGui.QLineEdit(str(folder_str),self)
		
		start_X=30
		start_Y=30
		adjust=3
		start_edit_X=start_X+120
		step_vertical=40
		
		lbl2.move(start_X, start_Y+adjust+0*step_vertical)
		start.move(start_X, start_Y+adjust+1*step_vertical)
		self.startEdit.move(start_edit_X,start_Y+1*step_vertical)
		stop.move(start_X, start_Y+adjust+2*step_vertical)
		self.stopEdit.move(start_edit_X,start_Y+2*step_vertical)
		step.move(start_X, start_Y+adjust+3*step_vertical)
		self.stepEdit.move(start_edit_X,start_Y+3*step_vertical)
		
		lbl3.move(start_X, start_Y+adjust+4*step_vertical)
		dwelltime.move(start_X, start_Y+adjust+5*step_vertical)
		self.dwelltimeEdit.move(start_edit_X,start_Y+5*step_vertical)
		lbl1.move(start_X, start_Y+adjust+6*step_vertical)
		combo1.move(start_edit_X,start_Y+6*step_vertical)
		
		lbl4.move(start_X, start_Y+adjust+7*step_vertical)
		expand.move(start_X, start_Y+adjust+8*step_vertical)
		self.expandEdit.move(start_edit_X,start_Y+8*step_vertical)
		offset.move(start_X, start_Y+adjust+9*step_vertical)
		self.offsetEdit.move(start_edit_X,start_Y+9*step_vertical)
		sens.move(start_X, start_Y+adjust+10*step_vertical)
		self.sensEdit.move(start_edit_X,start_Y+10*step_vertical)
		unit.move(start_X, start_Y+adjust+11*step_vertical)
		self.unitEdit.move(start_edit_X,start_Y+11*step_vertical)
		
		lbl5.move(start_X, start_Y+adjust+12*step_vertical)
		filename.move(start_X, start_Y+adjust+13*step_vertical)
		self.filenameEdit.move(start_edit_X,start_Y+13*step_vertical)
		folder.move(start_X, start_Y+adjust+14*step_vertical)
		self.folderEdit.move(start_edit_X,start_Y+14*step_vertical)
		
		##############################################
				
		config_str = QtGui.QLabel('Save changes to the config file', self)
		config_str.move(start_X, start_Y+16*step_vertical)
		self.saveButton = QtGui.QPushButton("Save",self)
		self.saveButton.move(start_X,start_Y+16*step_vertical+22)
				
		##############################################
				
		disc = QtGui.QLabel('Send commands to CM110 and acquire lock-in data', self)
		disc.move(start_X, start_Y+18*step_vertical)
		self.runButton = QtGui.QPushButton("Run",self)
		self.runButton.move(start_X,start_Y+18*step_vertical+22)
		#self.runButton.setDisabled(1)
		
		##############################################
		
		cancel_str = QtGui.QLabel('Cancel run and make plots of the currently saved data', self)
		cancel_str.move(start_X, start_Y+20*step_vertical)
		self.cancelButton = QtGui.QPushButton("Cancel run",self)
		self.cancelButton.move(start_X,start_Y+20*step_vertical+22)
		
		
		# give info which button has been pressed
		self.saveButton.clicked.connect(self.buttonClicked)
		self.runButton.clicked.connect(self.buttonClicked)
		self.cancelButton.clicked.connect(self.buttonClicked)
		self.status_str = QtGui.QLabel('Button status', self)
		self.status_str.move(start_X,950-25)
		
		# reacts to choises picked in the menu
		combo1.activated[str].connect(self.onActivated)
		
		# save all paramter data in the config file
		self.saveButton.clicked.connect(self.save_all)
		
		# run the main script
		self.runButton.clicked.connect(self.make_run)
		
		self.setGeometry(100, 100, 450, 950)
		self.setWindowTitle('CM110 Control Box And Data Acqusition')
		self.show()
	
	def buttonClicked(self):
  
		sender = self.sender()
		self.status_str.setText(sender.text() + ' was pressed!')
		self.status_str.adjustSize()
		#self.statusBar().showMessage(sender.text() + ' was pressed')
	
	def onActivated(self, text):
		
		self.lbl_test = str(text)

	def save_all(self):
		'''
		# replace all occurrences of 'sit' with 'SIT' and insert a line after the 5th
		for i, line in enumerate(fileinput.input(my_file_config, inplace=1)):
			if i==28: 
				sys.stdout.write(line.replace('start', 'START'))
		'''
		with open('config_CM110.py', 'w') as thefile:
			thefile.write( ''.join(['Start=',str(self.startEdit.text()),'\n']) )
			thefile.write( ''.join(['Stop=',str(self.stopEdit.text()),'\n']) )
			thefile.write( ''.join(['Step=',str(self.stepEdit.text()),'\n']) )
			thefile.write( ''.join(['Wait_time=',str(self.dwelltimeEdit.text()),'\n']) )
			thefile.write( ''.join(['Avg_pts=',self.lbl_test,'\n']) )
			thefile.write( ''.join(['Expand=',str(self.expandEdit.text()),'\n']) )
			thefile.write( ''.join(['Offset=',str(self.offsetEdit.text()),'\n']) )
			thefile.write( ''.join(['Sensitivity=',str(self.sensEdit.text()),'\n']) )
			thefile.write( ''.join(['Sens_unit=\'',str(self.unitEdit.text()),'\'\n']) )
			thefile.write( ''.join(['filename=\'',str(self.filenameEdit.text()),'\'\n']) )
			thefile.write( ''.join(['create_folder=\'',str(self.folderEdit.text()),'\'']) )
		
		
	def make_run(self):
		#QtCore.QCoreApplication.processEvents()
		self.myThread = runCM110()
		self.myThread.start()
		
		
#########################################
#########################################
#########################################
def main():
    
	app = QtGui.QApplication(sys.argv)
	ex = Example()
	ex.show()
	app.exec_()


if __name__ == '__main__':
	main()