import os, sys, serial, argparse, time, re
import numpy as np
import matplotlib.pyplot as plt 
import config_CM110

'''
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

self.start_str = config_CM110.Start
self.stop_str = config_CM110.Stop
self.step_str = config_CM110.Step
self.dwell_time_str = config_CM110.Wait_time
self.avg_pts = config_CM110.Avg_pts
self.expand_str = config_CM110.Expand
self.offset_str = config_CM110.Offset
self.sens_str = config_CM110.Sensitivity
self.unit_str = config_CM110.Sens_unit
self.filename_str=config_CM110.filename
self.folder_str=config_CM110.create_folder
self.cm110port_str=config_CM110.cm110port
self.ardport_str=config_CM110.ardport
'''



class Fast_logdata:
	def __init__(self):
				
		reload(config_CM110)
		# constants
		self.start_str = config_CM110.Start
		self.stop_str = config_CM110.Stop
		self.step_str = config_CM110.Step
		self.dwell_time_str = config_CM110.Wait_time
		self.avg_pts = config_CM110.Avg_pts
		self.expand_str = config_CM110.Expand
		self.offset_str = config_CM110.Offset
		self.sens_str = config_CM110.Sensitivity
		self.unit_str = config_CM110.Sens_unit
		self.analogRef = config_CM110.analogref		
		self.cm110port_str=config_CM110.cm110port
		self.ardport_str=config_CM110.ardport
		self.timestr=config_CM110.timestr
		
		self.outputs = 1

		if config_CM110.filename:
			self.string_filename=''.join([config_CM110.filename,self.timestr])
			self.string_timetrace=''.join([config_CM110.filename,'timetrace_',self.timestr])
		else:
			self.string_filename=''.join(['data_',self.timestr])
			self.string_timetrace=''.join(['data_timetrace_',self.timestr])
			
		if config_CM110.create_folder:
			self.saveinfolder=''.join([config_CM110.create_folder,'/'])
			if not os.path.isdir(config_CM110.create_folder):
				os.mkdir(config_CM110.create_folder)
		else:
			self.saveinfolder=''
		
		########################################
		
		if isinstance(self.start_str, float):
			raise ValueError("Monochromator start accepts integers only!")
		if isinstance(self.stop_str, float):
			raise ValueError("Monochromator stop accepts integers only!")
		if isinstance(self.step_str, float):
			raise ValueError("Monochromator step accepts integers only!")
		if self.dwell_time_str<1 or self.dwell_time_str>100:
			raise ValueError("Waiting time is minimum 1 second and maximum 100 seconds!")
		if isinstance(self.avg_pts, float):
			raise ValueError("Averaging only possibly using integers!")
		if self.offset_str<0 or self.offset_str>1:
			raise ValueError("Offset is a percentage value between 0 and 1!")
		if isinstance(self.expand_str, float):
			raise ValueError("Expand is required to be an integer")
		if self.expand_str<1 or self.expand_str>256:
			raise ValueError("Expand is an integer from 1 to 256!")
		if isinstance(self.sens_str, float):
			raise ValueError("Sensitivity is an integer!")
		if isinstance(self.unit_str, int) or isinstance(self.unit_str, float):
			raise ValueError("Sensitivity unit is a string!")
		
		self.my_file=''.join([self.saveinfolder,self.string_filename,'.txt'])	
		open(self.my_file, 'w').close()
		
		self.timetrace_plot=''.join([self.saveinfolder,self.string_timetrace,'.txt'])	
		open(self.timetrace_plot, 'w').close()
		
		#Initialize CM110 serial port
		print 'Initialize CM110 serial port: COM1'
		self.ser_CM = serial.Serial(self.cm110port_str, 9600)
		time.sleep(0.2)
		
		#Initialize Arduino serial port and toggle DTR to reset Arduino
		print 'Initialize Arduino and set serial port: COM4'
		self.ser_ARD = serial.Serial(self.ardport_str, 9600)
		time.sleep(0.2)
		self.ser_ARD.setDTR(False)
		time.sleep(1)
		self.ser_ARD.flushInput()
		self.ser_ARD.setDTR(True)
		time.sleep(1.5)
		
		#UNITS
		self.ser_CM.write([chr(tal) for tal in [50,01] ]) #01 set units to nm
		print '...setting units to nm'
		time.sleep(5)
		
		#GOTO                         
		#self.ser_CM.write(chr(16)) #call GOTO
		#time.sleep(0.1)
		if self.start_str>=0 and self.start_str<=9000:
			#calculate condition parameters suitable for byte operation
			multiplicator=self.start_str/256 #highbyte, 0 for numbers below 256
			runtohere=self.start_str-256*multiplicator 
			#send the parameters to the device
			self.ser_CM.write([chr(tal) for tal in [16,multiplicator,runtohere] ])
			
			print '...positioning scanner to the wavelength', self.start_str, 'nm'
			time.sleep(5)
		else:
			raise ValueError("Minimum start wavelength is 0 nm and maximum 9000 nm.")
		
		#STEPSIZE
		self.ser_CM.write([chr(tal) for tal in [55,self.step_str] ]) #call STEP and set setepsize
		time.sleep(0.1)
		
	def get_names(self):
		
		return self.string_filename, self.saveinfolder, self.unit_str, self.avg_pts, self.dwell_time_str
		
	def logdata(self):
		# Check input if a number, ie. digits or fractions such as 3.141
		# Source: http://www.pythoncentral.io/how-to-check-if-a-string-is-a-number-in-python-including-unicode/
		def is_number(s):
			try:
				float(s)
				return True
			except ValueError:
				pass

			try:
				import unicodedata
				unicodedata.numeric(s)
				return True
			except (TypeError, ValueError):
				pass

			return False
		####################################################################################

		new_position=self.start_str

		#make a heading for the textfile
		with open(self.my_file, 'a') as thefile:
			thefile.write( ''.join(['Start=',str(self.start_str),'nm, ', 'Stop=',str(self.stop_str),'nm, ','Step=',str(self.step_str),'nm, ','Wait-time=',str(self.dwell_time_str),'s, ','Avg.pts.=',str(self.avg_pts), '\n']) )
			thefile.write(''.join([ 'Wavelength[nm], Lock-in voltage[', self.unit_str, '], Raw data[0..1023 steps], ', 'Timetrace [sec]\n']))

		print '...current monochromator position is:'
		
		#Write the number of averaging points to the Arduino serial
		if self.avg_pts==0 or self.avg_pts>200:
			raise ValueError("The number of averaging points is minimum 1 and maximum 200")
		else:
			self.ser_ARD.write([chr(tal) for tal in [43,self.avg_pts]])
		###########################################
		
		tal=0
		timelist=[]
		all_data=[]
		all_positions=[]
		time_endpoints=[]
		time_start=time.time()
		while(new_position<self.stop_str):
			# do not step the monochromator first time you enter then while loop
			if tal==1:
				# Do STEP
				self.ser_CM.write(chr(54))
				new_position+=self.step_str
			
			print new_position, 'nm'
			
			# WAITING time until the voltage is read from the serial
			timetot=0
			raw_data=[]
			while (timetot<=self.dwell_time_str):
				timebeg=time.time()
				all_positions.extend([ new_position ])
				
				# Read voltage data from the serial
				line = self.ser_ARD.readline()
				
				# first read voltage (bit no.) from the serial 
				if(len(line.split()) == self.outputs): # expected no. of columns from Arduino
					for val in line.split():
						if is_number(val) and int(val)<2**10:
							raw_data.extend([ int(val) ])
							Vout=self.analogRef*float(val)/(2**10-1)
							Vlockin=(self.offset_str+Vout/(self.expand_str*10))*self.sens_str
							all_data.extend([ Vlockin ])
						else:
							raw_data.extend([ 0 ])
							all_data.extend([ 0 ])
				
				timelist.extend([ timebeg-time_start ])
				timetot+=time.time()-timebeg
				
				with open(self.timetrace_plot, 'a') as thefile:
					thefile.write("%s" % new_position)
					thefile.write("\t%s" % Vlockin)
					thefile.write("\t%s" % val)
					thefile.write("\t%s\n" % (timebeg-time_start))
			
			#give a warning if the last entry voltage is hitting 1023 
			if raw_data[-1]==2**10-1:
				print 'warning...possible voltage overload!'
			
			# Save stepped wavelengths and voltage data in a textfile
			time_endpoints.extend([ timelist[-1] ])
			with open(self.my_file, 'a') as thefile:
				thefile.write("%s " % new_position)
				thefile.write("\t%s" % all_data[-1])
				thefile.write("\t%s" % raw_data[-1])
				thefile.write("\t%s\n" % timelist[-1])
			tal=1
			
		#return all_data, all_positions, timelist, time_endpoints
		
	# clean up
	def close(self):
		# close serial
		self.ser_ARD.flush()
		self.ser_ARD.close()
		
		self.ser_CM.flush()
		self.ser_CM.close() 


def main():
	'''
	#create parser
	parser = argparse.ArgumentParser(description='Name for the textfile')
	# add expected arguments
	parser.add_argument(' ', dest='name', required=False)
	txtfile_name=parser.parse_args().name
	'''

	# run Microcontroller and save data in a textfile
	Ld = Fast_logdata()	
	Ld.logdata()
	'''
	string_filename, saveinfolder, sens_unit_CM, avg_pts, wait_CM = Ld.get_names()
	
	# open the textfile for plotting
	f2 = open(''.join([saveinfolder,string_filename,'.txt']), 'r')
	ignore_lines=[0,1]
	for i in ignore_lines:
		f2.readline()
	wl=[]
	uvolts=[]
	# Read new datafile
	for line in f2:
		columns = line.split()
		wl.extend([ float(columns[0]) ])
		uvolts.extend([ float(columns[1]) ])
	f2.close()

	# set up animation figure and background
	plt.figure(1, figsize=(15,10))
	plt.plot(wl, uvolts, '-bo', label=''.join(["Wait-time ",str(wait_CM),"s, ","Avg.pts. ",str(avg_pts)]))
	#plt.plot(all_positions, all_data, 'rx', label='all data')
	plt.xlabel("Wavelength, nm", fontsize=20)
	plt.ylabel(''.join(["Lock-in voltage, ", sens_unit_CM]), fontsize=20)
	plt.tick_params(axis="both", labelsize=20)
	l=plt.legend(loc=1, fontsize=12)
	l.draw_frame(False)
	
	# save and show plot
	plt.savefig(''.join([saveinfolder,string_filename,'.png']) )
	#plt.show()
	
	
	fig = plt.figure(2, figsize=(15,10))
	ax = fig.add_subplot(111)
	ax.plot(timelist, all_positions, 'k-')
	ax2 = ax.twinx()
	ax2.plot(timelist, all_data, 'r-', label='all points')
	ax2.plot(time_endpoints, uvolts, '-bo', label='end points')

	string_1 = ''.join(["Wavelength, nm"])
	ax.set_ylabel(string_1, fontsize=20)
	ax.set_xlabel("Elapsed time, s", fontsize=20)
	ax.tick_params(axis="both", labelsize=20)
	ax.set_title(''.join(["Wait-time ",str(wait_CM),"s, ","Avg.pts. ",str(avg_pts)]))
	l=plt.legend(loc=1, fontsize=15)
	l.draw_frame(False)

	ax2.set_ylabel(''.join(["Lock-in voltage, ", sens_unit_CM]), fontsize=20, color='r')
	ax2.tick_params(axis="y", labelsize=20)
	for tl in ax2.get_yticklabels():
		tl.set_color('r')
		
	# save and show plot
	plt.savefig(''.join([saveinfolder,string_filename,'_TimeElapsed.png']) )
	#plt.show()
	'''
	# clean up
	Ld.close()
	 
if __name__ == "__main__":
	main()



