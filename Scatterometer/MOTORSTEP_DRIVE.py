import sys, serial, argparse, time, re
import numpy as np
import matplotlib.pyplot as plt 

class MOTORSTEP_DRIVE:
	
	def __init__(self,my_serial):
	  # activate the serial. CHECK the serial port name!
	  self.ser = serial.Serial(my_serial, baudrate=115200)
	  print "Motorstep drive serial port:", my_serial
	  time.sleep(2)

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
		eol=b'\r\n'
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
  
	def stop_move(self):
		#turn on Vs, Vss, and enable on the drive 
		self.ser.write(''.join(['#']))
  
	def set_pin(self,dev,pin,highlow):
		#turn on Vs, Vss, and enable on the drive 
		self.ser.write(''.join(['/set_pin ',str(dev),' ',str(pin),' ',str(highlow),'\n']))
		while self.ser.read(1)!='@':
			pass
		val=self._readline()
		print val
		return val

	def drive_on(self,dev):
		#turn on Vs, Vss, and enable on the drive 
		self.ser.write(''.join(['/turn_on ',str(dev),'\n']))
		while self.ser.read(1)!='@':
			pass
		mystr=self._readline()
		if mystr=='ready':
			print "Driver",dev+1,"is on"
			return mystr
		else:
			pass

	def drive_off(self,dev):
		#turn on Vs, Vss, and enable on the drive 
		self.ser.write(''.join(['/turn_off ',str(dev),'\n']))
		while self.ser.read(1)!='@':
			pass
		mystr=self._readline()
		if mystr=='ready':
			print "Driver",dev+1,"is off"
			return mystr
		else:
			pass
	
	def set_pos(self,dev,pos):
		#turn on Vs, Vss, and enable on the drive 
		self.ser.write(''.join(['/set_pos ',str(dev),' ',str(pos),'\n']))
		while self.ser.read(1)!='@':
			pass
		val=self._readline()
		if self.is_number(val):
			#print "return_reffreq: ", val
			return int(val)
		else:
			pass
	
	def get_pos(self,dev):
		#turn on Vs, Vss, and enable on the drive 
		self.ser.write(''.join(['/get_pos ',str(dev),'\n']))
		while self.ser.read(1)!='@':
			pass
		val=self._readline()
		if self.is_number(val):
			#print "return_reffreq: ", val
			return int(val)
	
	def set_minmax_pos(self,dev,minmax,pos):
		#turn on Vs, Vss, and enable on the drive
		if minmax=='min': 
			self.ser.write(''.join(['/set_min_pos ',str(dev),' ',str(pos),'\n']))
		elif minmax=='max':
			self.ser.write(''.join(['/set_max_pos ',str(dev),' ',str(pos),'\n']))
		while self.ser.read(1)!='@':
			pass
		val=self._readline()
		if self.is_number(val):
			#print "return_reffreq: ", val
			return int(val)
		else:
			pass
	
	
	def get_minmax_pos(self,dev,minmax):
		#turn on Vs, Vss, and enable on the drive
		if minmax=='min': 
			self.ser.write(''.join(['/set_min_pos ',str(dev),'\n']))
		elif minmax=='max':
			self.ser.write(''.join(['/set_max_pos ',str(dev),'\n']))
		while self.ser.read(1)!='@':
			pass
		val=self._readline()
		if self.is_number(val):
			#print "return_reffreq: ", val
			return int(val)
		else:
			pass
		
	def move_Relative(self,dev,steps):
		#turn on Vs, Vss, and enable on the drive
		dwell_time=1 #period for the pulsetrain in milliseconds 
		self.ser.write(''.join(['/move_rel ',str(dev),' ',str(dwell_time),' ',str(steps),'\n']))
		while self.ser.read(1)!='@':
			pass
		val=self._readline()
		if self.is_number(val):
			#print "return_reffreq: ", val
			return int(val)
		else:
			print val
	
	def move_Absolute(self,dev,posnew):
		#turn on Vs, Vss, and enable on the drive
		dwell_time=1 #period for the pulsetrain in milliseconds 
		self.ser.write(''.join(['/move_abs ',str(dev),' ',str(dwell_time),' ',str(posnew),'\n']))
		while self.ser.read(1)!='@':
			pass
		val=self._readline()
		if self.is_number(val):
			#print "return_reffreq: ", val
			return int(val)
		else:
			print val
	
	def read_analog(self,dev,avgpts):
		#read digitized voltage value from the analog port number (dev)
		self.ser.write(''.join(['/read_analog ',str(dev),' ',str(avgpts),'\n']))
		while self.ser.read(1)!='@':
			pass
		val=self._readline()
		if self.is_number(val):
			#print "return_reffreq: ", val
			return int(val)
		else:
			pass
	
	# clean up serial
	def close(self):
	  # flush and close serial
	  self.ser.flush()
	  self.ser.close()
	  print "Stepper driver port flushed and closed" 

def test():
  
	# call the Motorstep drive port
	md = MOTORSTEP_DRIVE("/dev/ttyACM2")
	
	# do some testing here
	md.drive_on(1)
	
	#md.set_pin(1,1,'high')
	#md.set_pin(1,2,'high')
	
	md.set_pos(1,0)
	print md.get_pos(1)
	for i in range(10):
		md.move_Relative(1,500)
		volts=md.read_analog(1,10)
		print volts
		time.sleep(1)	

	# clean up and close the Motorstep drive port
	print md.get_pos(1)
	
	md.drive_off(1)
	md.close()
 
if __name__ == "__main__":
	
  test()
  


