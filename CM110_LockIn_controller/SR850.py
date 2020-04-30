import sys, serial, argparse, time, re
import numpy as np
import matplotlib.pyplot as plt 

class SR850:
	
	def __init__(self,my_serial):
	  # activate the serial. CHECK the serial port name!
	  self.my_serial=my_serial
	  self.ser = serial.Serial(self.my_serial, 4800)
	  print "Lock-in serial port:", self.my_serial

	# read from the serial
	def readBytes(self,num):
	  data=self.ser.read(num)
	  data_ord=[ord(val) for val in data]
	  if(len(data_ord)==num): # expected no. of bytes from serial
	    pass
	    #print "Status byte", bin(data_ord[num-2])[2:]
	    #print "Decimal", data_ord[num-1]
	  else:
	    raise ValueError(''.join(["Exactely ",num," bytes expected from lock-in but got ", str(len(data_ord)),"!"]) )

	  return data_ord
  
  ############################################################
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
		eol=b'\r'
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
		return bytes(line)
  
  ####################################################################
  # SR850 functions
  ####################################################################
  
	def set_timeout(self,val):
		self.ser.timeout=val
  
	def set_to_rs232(self):
		my_string=''.join(['OUTX0;FAST1;STRD\r'])
		self.ser.write(my_string)
  
	def set_to_gpib(self):
		my_string=''.join(['OUTX1;FAST1;STRD\r'])
		self.ser.write(my_string)
		
	def set_autoscale(self):
		my_string=''.join(['ASCL\r'])
		self.ser.write(my_string)	
	
	def set_autogain(self):
		my_string=''.join(['AGAN\r'])
		self.ser.write(my_string)

	def return_id(self):
		my_string=''.join(['*IDN?\r'])
		self.ser.write(my_string)
		val=self._readline()
		#print "return_id: ", val
		return val

	def return_reffreq(self):
		my_string=''.join(['FREQ?\r'])
		self.ser.write(my_string)
		val=self._readline()
		print "return_reffreq: ", val
		return val
	
	def return_snap_data(self):
		# returns values of X, Y, Ref freq
		my_string=''.join(['SNAP?1,2,9\r'])
		self.ser.write(my_string)
		val=self._readline()
		#print "return_snap_data: ", val
		return val
		
	def return_X(self):
		my_counter=0
		my_string=''.join(['OUTP?1\r'])
		#self.return_status_byte(1)
		while True:
			self.ser.write(my_string)
			val=self._readline()
			if self.is_number(val):
				print "return_X: ", val
				return float(val)
			else:
				print "Bad value!"
				if my_counter==19:
					raise ValueError("20 consecutive failed attempts to get X value from SR850 lock-in! Is SR850 connected to the serial?")
				my_counter+=1
				
	def return_Y(self):
		my_string=''.join(['OUTP?2\r'])
		self.ser.write(my_string)
		val=self._readline()
		#print "return_Y: ", val
		return val
		
	def return_R(self):
		my_string=''.join(['OUTP?3\r'])
		self.ser.write(my_string)
		val=self._readline()
		#print "return_R: ", val
		return val

	def return_THETA(self):
		my_string=''.join(['OUTP?4\r'])
		self.ser.write(my_string)
		val=self._readline()
		#print "return_THETA: ", val
		return val

	def return_status_bytes(self):
		my_string=''.join(['LIAS?','\r'])
		self.ser.write(my_string)
		val=self._readline()
		val_='{0:08b}'.format(int(val))
		print "return_satus_bytes: ", val_
		return val_
			
	# clean up serial
	def close(self):
		# flush and close serial
		self.ser.flush()
		self.ser.close()
		print "Lock-in port flushed and closed" 

def main():
  
	# call the sr850 por
	sr850 = SR850("/dev/ttyUSB0")
	# do some testing here
	#sr850.set_to_rs232()
	#sr850.set_autoscale()
	
	#sr850.set_autogain()
	'''
	while True:
		val=sr850.return_status_bytes()
		if val[-2]=='1':
			break
	'''
	for ii in range(200):
		sr850.return_X()
		#sr850.return_reffreq()
	
	# clean up and close the sr850 port
	sr850.close()

 
if __name__ == "__main__":
	
  main()
  


