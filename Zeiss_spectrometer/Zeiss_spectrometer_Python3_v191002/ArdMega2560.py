import os, sys, serial, time
import numpy as np

class ArdMega2560():
	
	def __init__(self,my_serial):

		#Initialize Arduino serial port and toggle DTR to reset Arduino
		self.my_serial=my_serial
		self.ser_ARD = serial.Serial(self.my_serial, 9600)
		print "Initialize Arduino and set serial port:", self.my_serial
		time.sleep(1)
		
		'''
		time.sleep(0.2)
		#Initialize Arduino serial port and toggle DTR to reset Arduino
		print "Initialize Arduino and set serial port:", self.my_serial
		#self.ser_ARD = serial.Serial(self.ardport_str, 9600)
		#time.sleep(0.2)
		self.ser_ARD.setDTR(False)
		time.sleep(1)
		self.ser_ARD.flushInput()
		self.ser_ARD.setDTR(True)
		time.sleep(1.5)
		'''
		
	def get_val(self,avg_pts):
		
		############################################################
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
		
		# and pass the number of averaging points to the Arduino serial
		if avg_pts<1:
			raise ValueError("The number of averaging points is minimum 1")
		else:
			# pass number of averaging points, 43 is + in ascii
			self.ser_ARD.write([chr(tal) for tal in [43,avg_pts]])
			
		# Read voltage data from the serial
		line = self.ser_ARD.readline()
		
		# first read voltage (bit no.) from the serial 
		if(len(line.split())==1): # expected no. of columns from Arduino
			for val in line.split():
				if is_number(val) and int(val)<2**10:
					return int(val)
					#Vout=self.analogRef*float(val)/(2**10-1)
				else:
					raise ValueError("Arduino output larger than 1023!")
		else:
			raise ValueError("Multiple outputs at the Arduino serial!")
			
	# close serial and clean up
	def close(self):
		# close serial
		print "Arduino port flushed and closed"
		self.ser_ARD.flush()
		self.ser_ARD.close()

def main():
	Ard = ArdMega2560("/dev/ttyACM0",1)
	tal=0
	while tal<10:
		time.sleep(0.25)
		print Ard.get_val()
		tal+=1
	Ard.close()
	
if __name__ == "__main__":
  main()