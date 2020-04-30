import os, sys, serial, argparse, time, re
import numpy as np
import matplotlib.pyplot as plt 

timestr=time.strftime("%Y%m%d-%H%M%S")
analogRef=5 # units in Volts

if len(sys.argv)>3:
	raise ValueError('The function takes maximum 3 input arguments!')
elif len(sys.argv)==3 and sys.argv[2]=='help':
	inFile=sys.argv[1]
	params=__import__(inFile)
	if not hasattr(params, 'help_string'):
		raise ValueError("Basic help instructions are missing. Operation terminated!")
	print params.help_string
	sys.exit()
elif len(sys.argv)==2:
	inFile=sys.argv[1]
	params=__import__(inFile)
	if not hasattr(params, 'help_string'):
		raise ValueError("Basic help instructions are missing. Operation terminated!")
	start_CM = params.Start
	stop_CM = params.Stop
	step_CM = params.Step
	wait_CM = params.Wait_time
	avg_pts = params.Avg_pts
	expand_CM = params.Expand
	offset_CM = params.Offset
	sens_CM = params.Sensitivity
	sens_unit_CM = params.Sens_unit
	
	if params.filename:
		string_filename=''.join([params.filename,timestr])
	else:
		string_filename=''.join(['data_',timestr])
		
	if params.create_folder:
		saveinfolder=''.join([params.create_folder,'/'])
		if not os.path.isdir(params.create_folder):
			os.mkdir(params.create_folder)
	else:
		saveinfolder=''
else:
	raise ValueError('Config file required!')


class Fast_logdata:
	def __init__(self):
		# constants
		self.outputs=1
		self.start=start_CM
		self.stop=stop_CM
		self.step=step_CM 
		self.wait=wait_CM
		self.pts=avg_pts
		self.expand=expand_CM 
		self.offset=offset_CM 
		self.sens=sens_CM
		self.sens_unit=sens_unit_CM
		
		if isinstance(self.start, float):
			raise ValueError("Monochromator start accepts integers only!")
		if isinstance(self.stop, float):
			raise ValueError("Monochromator stop accepts integers only!")
		if isinstance(self.step, float):
			raise ValueError("Monochromator step accepts integers only!")
		if self.wait<1 or self.wait>100:
			raise ValueError("Waiting time is minimum 1 second and maximum 100 seconds!")
		if isinstance(self.pts, float):
			raise ValueError("Averaging only possibly using integers!")
		if self.offset<0 or self.offset>1:
			raise ValueError("Offset is a percentage value between 0 and 1!")
		if isinstance(self.expand, float):
			raise ValueError("Expand is required to be an integer")
		if self.expand<1 or self.expand>256:
			raise ValueError("Expand is an integer from 1 to 256!")
		if isinstance(self.sens, float):
			raise ValueError("Sensitivity is an integer!")
		if isinstance(self.sens_unit, int) or isinstance(self.sens_unit, float):
			raise ValueError("Sensitivity unit is a string!")
		
		self.my_file=''.join([saveinfolder,string_filename,'.txt'])	
		open(self.my_file, 'w').close()
		
		#Initialize CM110 serial port
		print 'Initialize CM110 serial port: COM1'
		self.ser_CM = serial.Serial("/dev/ttyACM0", 9600)
		time.sleep(0.2)
		
		#Initialize Arduino serial port and toggle DTR to reset Arduino
		print 'Initialize Arduino and set serial port: COM4'
		self.ser_ARD = serial.Serial("/dev/ttyACM0", 9600)
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
		if self.start>=0 and self.start<=9000:
			#calculate condition parameters suitable for byte operation
			multiplicator=self.start/256 #highbyte, 0 for numbers below 256
			runtohere=self.start-256*multiplicator 
			#send the parameters to the device
			self.ser_CM.write([chr(tal) for tal in [16,multiplicator,runtohere] ])
			
			print '...positioning scanner to the wavelength', self.start, 'nm'
			time.sleep(5)
		else:
			raise ValueError("Minimum start wavelength is 0 nm and maximum 9000 nm.")
		
		#STEPSIZE
		self.ser_CM.write([chr(tal) for tal in [55,self.step] ]) #call STEP and set setepsize
		time.sleep(0.1)
		
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

		new_position=self.start

		#make a heading for the textfile
		with open(self.my_file, 'a') as thefile:
			thefile.write( ''.join(['Start=',str(self.start),'nm, ', 'Stop=',str(self.stop),'nm, ','Step=',str(self.step),'nm, ','Wait-time=',str(self.wait),'s, ','Avg.pts.=',str(self.pts), '\n']) )
			thefile.write(''.join([ 'Wavelength[nm], Lock-in voltage[', self.sens_unit, '], Raw data[0..1023 steps]\n']))

		try:
			print '...current monochromator position is:'
			
			#Write the number of averaging points to the Arduino serial
			if self.pts==0 or self.pts>255:
				raise ValueError("The number of averaging points is minimum 1 and maximum 255")
			else:
				self.ser_ARD.write([chr(tal) for tal in [43,self.pts]])
			###########################################
			
			tal=0
			timelist=[]
			all_data=[]
			all_positions=[]
			time_endpoints=[]
			time_start=time.time()
			while(new_position<self.stop):
				# do not step the monochromator first time you enter then while loop
				if tal==1:
					# Do STEP
					self.ser_CM.write(chr(54))
					new_position+=self.step
				
				print new_position, 'nm'
				
				# WAITING time until the voltage is read from the serial
				timetot=0
				raw_data=[]
				while (timetot<=self.wait):
					timebeg=time.time()
					all_positions.extend([ new_position ])
					
					# Read voltage data from the serial
					line = self.ser_ARD.readline()
					
					# first read voltage (bit no.) from the serial 
					if(len(line.split()) == self.outputs): # expected no. of columns from Arduino
						for val in line.split():
							if is_number(val) and int(val)<2**10:
								raw_data.extend([ int(val) ])
								Vout=analogRef*float(val)/(2**10-1)
								Vlockin=(self.offset+Vout/(self.expand*10))*self.sens
								all_data.extend([ Vlockin ])
							else:
								raw_data.extend([ 0 ])
								all_data.extend([ 0 ])
					
					timelist.extend([ timebeg-time_start ])
					timetot+=time.time()-timebeg
				
				#give a warning if the last entry voltage is hitting 1023 
				if raw_data[-1]==2**10-1:
					print 'warning...possible voltage overload!'
				
				# Save stepped wavelengths and voltage data in a textfile
				time_endpoints.extend([ timelist[-1] ])
				with open(self.my_file, 'a') as thefile:
					thefile.write("%s " % new_position)
					thefile.write("\t%s" % all_data[-1])
					thefile.write("\t%s\n" % raw_data[-1])
					#thefile.write("\t%s\n" % timelist[-1])
				tal=1

		except KeyboardInterrupt:
			print('exiting')

		return all_data, all_positions, timelist, time_endpoints
		
	# clean up
	def close(self):
		# close serial
		self.ser_ARD.flush()
		self.ser_ARD.close()
		
		self.ser_CM.flush()
		self.ser_CM.close() 
 
if __name__ == "__main__":
	'''
	#create parser
	parser = argparse.ArgumentParser(description='Name for the textfile')
	# add expected arguments
	parser.add_argument(' ', dest='name', required=False)
	txtfile_name=parser.parse_args().name
	'''

	# run Microcontroller and save data in a textfile
	Ld = Fast_logdata()
	all_data, all_positions, timelist, time_endpoints = Ld.logdata()

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
	plt.show()
	
	
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
	plt.show()
	
	# clean up
	Ld.close()



