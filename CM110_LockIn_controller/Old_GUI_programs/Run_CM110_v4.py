import sys, serial, argparse, time, re
import numpy as np
import matplotlib.pyplot as plt 

timestr=time.strftime("%Y%m%d-%H%M%S")

class Fast_logdata:
  def __init__(self, start_CM, stop_CM, step_CM, wait_CM, avg_pts, string_filename):
		# constants
		self.outputs=1
		self.start=start_CM
		self.stop=stop_CM
		self.step=step_CM 
		self.wait=wait_CM
		self.pts=avg_pts
		self.my_file=''.join([string_filename,'.txt'])
		open(self.my_file, 'w').close()
		
		#Initialize CM110 serial port
		print 'Initialize CM110 serial port: COM1'
		self.ser_CM = serial.Serial("COM1", 9600)
		time.sleep(0.2)
		
		#Initialize Arduino serial port and toggle DTR to reset Arduino
		print 'Initialize Arduino and set serial port: COM4'
		self.ser_ARD = serial.Serial("COM4", 9600)
		time.sleep(0.2)
		self.ser_ARD.setDTR(False)
		time.sleep(1)
		self.ser_ARD.flushInput()
		self.ser_ARD.setDTR(True)
		
		#Write the number of averaging points to the Arduino serial
		time.sleep(1.5)
		if self.pts==0 or self.pts>255:
			raise ValueError("The number of averaging points is minimum 1 and maximum 255")
		else:
			self.ser_ARD.write([chr(tal) for tal in [43,self.pts]])
		time.sleep(0.1)
		
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
			thefile.write('Wavelength[nm], Voltage[mV], Raw data[0..1023 steps], Elapsed time[sec]\n')

		try:
			# do not step the monochromator first time you enter then while loop
			tal=0
			print '...the current monochromator position is:'
			timelist=[]
			time_start=time.time()
			while(new_position<self.stop):
				if tal==1:
					# Do STEP
					self.ser_CM.write(chr(54))
					new_position+=self.step
				
				# WAITING time until the voltage is read from the serial
				print new_position, 'nm'
				time.sleep(self.wait)
				
				# first save stepped wavelengths in a textfile				
				with open(self.my_file, 'a') as thefile:
					thefile.write("%s " % new_position)
				
				# then, read voltage data from the serial
				line = self.ser_ARD.readline()
				
				# save in-lock amp output voltage in the same textfile
				# first read voltage (bit no.) from the serial then save these values
				self.data=[]
				if(len(line.split()) == self.outputs): # expected no. of columns from Arduino
					for val in line.split():
						if is_number(val) and int(val)<2**10:
							self.data.extend([ val ])
							if int(val)==2**10-1:
								print 'warning...possible voltage overload!'
						else:
							self.data.extend([ 0 ])
					
					# save voltage data in the same textfile
					with open(self.my_file, 'a') as thefile:
						for tal in range(len(self.data)):
							if tal == len(self.data)-1:
								thefile.write("\t%s " % (1100*int(self.data[tal])/1023))
								thefile.write("\t%s" % self.data[tal])
								thefile.write("\t%s\n" % (time.time()-time_start))
							else:
								thefile.write("\t%s " % (1100*int(self.data[tal])/1023))
								thefile.write("\t%s " % self.data[tal])
								thefile.write("\t%s" % (time.time()-time_start))
				 
				tal=1
				timelist.extend([ time.time()-time_start ])
				
		except KeyboardInterrupt:
			print('exiting')

		return timelist
    
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
	if len(sys.argv)==7:
		start_CM=int(sys.argv[1])
		stop_CM=int(sys.argv[2])
		step_CM=int(sys.argv[3])
		wait_CM=int(sys.argv[4])
		avg_pts=int(sys.argv[5])
		string_filename=''.join([sys.argv[6],timestr])
	elif len(sys.argv)==2 and sys.argv[1]=='help':
		print 'USER INSTRUCTIONS'
		print '6 argument inputs, for numbers only integers accepted, the 6th argument is optional.'
		print 'Argument 1: Start [nm], range: 0-9000'
		print 'Argument 2: Stop [nm], range: 0-9000'
		print 'Argument 3: Step [nm], range: 1-255'
		print 'Argument 4: Wait-time [sec], range: 1-255'
		print 'Argument 5: No. of averaging points for Arduino, range: 1-255'
		print 'Argument 6: Give a filename [optional]'
		sys.exit()
	elif len(sys.argv)==6:
		start_CM=int(sys.argv[1])
		stop_CM=int(sys.argv[2])
		step_CM=int(sys.argv[3])
		wait_CM=int(sys.argv[4])
		avg_pts=int(sys.argv[5])
		string_filename=''.join(['data_',timestr])
	else:
		raise ValueError('5 integer arguments required: Start, Stop, Step, Wait time and Integrations points.')
  
	# run Microcontroller and save data in a textfile
	Ld = Fast_logdata(start_CM, stop_CM, step_CM, wait_CM, avg_pts, string_filename)
	timelist=Ld.logdata()

	# open the textfile for plotting
	f2 = open(''.join([string_filename,'.txt']), 'r')
	ignore_lines=[0,1]
	for i in ignore_lines:
		f2.readline()
	data1=[]
	data2=[]
	data3=[]
	# Read new datafile
	for line in f2:
		columns = line.split()
		data1.extend([ float(columns[0]) ])
		data2.extend([ float(columns[1]) ])
		data3.extend([ float(columns[2]) ])
	f2.close()

	# set up animation figure and background
	fig = plt.figure(1, figsize=(15,10))
	ax = fig.add_subplot(111)

	analogRef=1.1 # if analogRef (Arduino 2560) is not enabled than analogRef=5 Volts
	ax.plot(data1, timelist, 'k-')
	ax2 = ax.twinx()
	ax2.plot(data1, analogRef*np.array(data3)*1000/2**10, 'r-')

	string_1 = ''.join(["Wavelength, nm"])
	ax.set_xlabel(string_1, fontsize=20)
	ax.set_ylabel("Elapsed time, s", fontsize=20)
	ax.tick_params(axis="both", labelsize=20)

	ax2.set_ylabel("Voltage, mV", fontsize=20, color='r')
	ax2.tick_params(axis="y", labelsize=20)
	for tl in ax2.get_yticklabels():
		tl.set_color('r')

	# show plot
	plt.savefig(''.join([ string_filename,'.png']) )
	plt.show()

	# clean up
	Ld.close()



