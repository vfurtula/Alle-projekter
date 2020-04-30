import sys, serial, argparse, time, re
import numpy as np
import matplotlib.pyplot as plt 

class ARDUNO:
	
	def __init__(self,my_serial):
		# activate the serial. CHECK the serial port name!
		self.ser = serial.Serial(my_serial, baudrate=115200)
		print "Motorstep drive serial port:", my_serial
		time.sleep(1)


	############################################################
	def set_timeout(self,val):
		
		self.ser.timeout=val
	
	# Check input if a number, ie. digits or fractions such as 3.141
	# Source: http://www.pythoncentral.io/how-to-check-if-a-string-is-a-number-in-python-including-unicode/
	def is_number(self,s):
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
	
	# Pyserial readline() function reads until '\n' is sent (other EOLs are ignored).
  # Therefore changes to readline() are required to match it with EOL character '\r'.
  # See: http://stackoverflow.com/questions/16470903/pyserial-2-6-specify-end-of-line-in-readline
	def _readline(self):
		#eol=b'\r\n'
		eol=b'\n'
		leneol=len(eol)
		line=bytearray()
		while True:
		  c=self.ser.read(1)
		  if c:
		    line+=c
		    if line[-leneol:]==eol:
		      break
		  else:
		    break
		return bytes(line[:-leneol])
  
  ####################################################################
  # Motorstep drive functions
  ####################################################################
	
	def read_analog(self,dev,avgpts):
		#read digitized voltage value from the analog port number (dev)
		try:
			self.ser.write(''.join(['/a ',str(dev),' ',str(avgpts),'\n']))
			if self.ser.read(1)=='@':
				val=self._readline()
			else:
				return ValueError
		except serial.SerialException as e:
			print e
			return serial.SerialException
		
		if self.is_number(val):
			#print "return_reffreq: ", val
			return int(float(val))
		else:
			return ValueError
		
	def is_open(self):
		
		return self.ser.isOpen()
	
	# clean up serial
	def close(self):
		# flush and close serial
		self.ser.flush()
		self.ser.close()
		print "Arduino port flushed and closed" 

def test():
  
	# call the Motorstep drive port
	md = ARDUNO("/dev/ttyACM0")
	
	for i in range(10):
		volts=md.read_analog(1,10)
		print volts
		time.sleep(1)	

	# clean up and close the Motorstep drive port
	md.close()
 
if __name__ == "__main__":
	
  test()
  


