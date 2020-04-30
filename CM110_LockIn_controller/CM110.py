import sys, serial, argparse, time, re
import numpy as np
import matplotlib.pyplot as plt 

class CM110:
	
	def __init__(self,my_serial):
	  # activate the serial. CHECK the serial port name!
	  self.my_serial=my_serial
	  self.ser = serial.Serial(self.my_serial, 9600)
	  print "CM110 serial port:", self.my_serial

	# read from the serial
	def readBytes(self,num):
	  data=self.ser.read(num)
	  data_ord=[ord(val) for val in data]
	  if(len(data_ord)==num): # expected no. of bytes from serial
	    pass
	    #print "Status byte", bin(data_ord[num-2])[2:]
	    #print "Decimal", data_ord[num-1]
	  else:
	    raise ValueError(''.join(["Exactely ",num," bytes expected from CM110 but got ", str(len(data_ord)),"!"]) )

	  return data_ord
  
  ####################################################################
  # CM110 functions
  ####################################################################
  
	def set_um(self):
		#00 set units to microns
		self.ser.write([chr(tal) for tal in [50,00] ])
		output=self.readBytes(2)
		#print "Status byte for set_um:", bin(output[0])[2:]
		#print "Ready signal for set_um:", output[1]
		return output[1]

	def set_nm(self):
		#01 set units to nm
		self.ser.write([chr(tal) for tal in [50,01] ])
		output=self.readBytes(2)
		#print "Status byte for set_nm:", bin(output[0])[2:]
		#print "Ready signal for set_nm:", output[1]
		return output[1]

	def set_as(self):
		#02 set units to angstroms
		self.ser.write([chr(tal) for tal in [50,02] ])
		output=self.readBytes(2)
		#print "Status byte for set_as:", bin(output[0])[2:]
		#print "Ready signal for set_as:", output[1]
		return output[1]

	def set_goto(self,val):
		#GOTO to the very start of the scan                         		
		#calculate condition parameters suitable for byte operation
		multiplicator=val/256 #highbyte, 0 for numbers below 256
		runtohere=val-256*multiplicator #lowbyte
		#send the parameters to the CM110 monochromator
		self.ser.write([chr(tal) for tal in [16,multiplicator,runtohere] ])
		#print "...positioning scanner to the wavelength", val, "nm"
		output=self.readBytes(2)
		#print "Status byte for set_goto:", bin(output[0])[2:]
		#print "Ready signal for set_goto:", output[1]
		return output[1]
		
	def set_stepsize(self,val):
		if val<128:
			#call STEP and set setepsize
			self.ser.write([chr(tal) for tal in [55,val] ]) 
			output=self.readBytes(2)
			#print "Status byte for set_stepsize:", bin(output[0])[2:]
			#print "Ready signal for set_stepsize:", output[1]
			return output[1]

	def make_step(self):
		#Moves the monochromator by a preset amount defined by the set_stepsize
		self.ser.write(chr(54))
		output=self.readBytes(2)
		#print "Status byte for make_step:", bin(output[0])[2:]
		#print "Ready signal for make_step:", output[1]
		return output[1]

	def set_scan(self,start,end):
		#GOTO to the very start of the scan                         		
		#calculate condition parameters suitable for byte operation
		# START parameters
		mp_start=start/256 #highbyte, 0 for numbers below 256
		runtohere_start=start-256*mp_start #lowbyte
		# END parameters
		mp_end=end/256 #highbyte, 0 for numbers below 256
		runtohere_end=end-256*mp_end #lowbyte
		#send the parameters to the CM110 monochromator
		self.ser.write([chr(tal) for tal in [12,mp_start,runtohere_start,mp_end,runtohere_end] ])
		#print "...positioning scanner to the wavelength", val, "nm"
		output=self.readBytes(2)
		#print "Status byte for set_scan:", bin(output[0])[2:]
		#print "Ready signal for set_scan:", output[1]
		return output[1]

	def set_speed(self,speed):
		#GOTO to the very start of the scan                         		
		#calculate condition parameters suitable for byte operation
		multiplicator=speed/256 #highbyte, 0 for numbers below 256
		runtohere=speed-256*multiplicator 
		#send the parameters to the CM110 monochromator
		self.ser.write([chr(tal) for tal in [13,multiplicator,runtohere] ])
		#print "...positioning scanner to the wavelength", val, "nm"
		output=self.readBytes(2)
		#print "Status byte for set_speed:", bin(output[0])[2:]
		#print "Ready signal for set_speed:", output[1]
		return output[1]
	
	def get_position(self):
		# get current position of CM110
		self.ser.write([chr(tal) for tal in [56,00] ])
		output=self.readBytes(4)
		position = 256*output[0]+output[1]
		print "The current position of CM110 is", position
		#print "Status byte for get_position:", bin(output[2])[2:]
		#print "Ready signal for get_position:", output[3]
		return position
	
	def get_grprmm(self):
		# get grooves per mm of CM110
		self.ser.write([chr(tal) for tal in [56,02] ])
		output=self.readBytes(4)
		grprmm = 256*output[0]+output[1]
		#print "The grooves per mm of CM110 is", grprmm
		#print "Status byte for get_grprmm:", bin(output[2])[2:]
		#print "Ready signal for get_grprmm:", output[3]
		return grprmm
	
	def get_speed(self):
		# get speed A/s of CM110
		self.ser.write([chr(tal) for tal in [56,05] ])
		output=self.readBytes(4)
		speed = 256*output[0]+output[1]
		#print "The speed of CM110 is", speed, " A/s"
		#print "Status byte for get_speed:", bin(output[2])[2:]
		#print "Ready signal for get_speed:", output[3]
		return speed
	
	def get_units(self):
		# get current position of CM110
		self.ser.write([chr(tal) for tal in [56,14] ])
		output=self.readBytes(4)
		if output[1]==0:
			mystr="um"
		elif output[1]==1:
			mystr="nm"
		elif output[1]==2:
			mystr="as"
		else:
			mystr="(unknown)"
			print "Unkown units!"
		#print "Current units of CM110 are", mystr
		#print "Status byte for get_position:", bin(output[2])[2:]
		#print "Ready signal for get_position:", output[3]
		return mystr
	
	def get_echo(self):
		#Moves the monochromator by a preset amount defined by the set_stepsize
		self.ser.write(chr(27))
		self.ser.timeout=1
		try:
			output=self.readBytes(1)
			print "Echo signal from CM110:", output[0]
			self.ser.timeout=None
			return output[0]
		except Exception, e:
			self.ser.timeout=None
			print "No echo signal from CM110!"
			
	# clean up serial
	def close(self):
	  # flush and close serial
	  self.ser.flush()
	  self.ser.close()
	  print "CM110 port flushed and closed" 

def main():
  
	# call the cm110 port
	cm110 = CM110("/dev/ttyUSB0")
	# do some testing here
	cm110.set_nm()
	cm110.set_goto(1200)
	cm110.set_stepsize(100)
	for ii in range(10):
		cm110.make_step()
		time.sleep(0.2)
	
	cm110.get_position()
	cm110.get_grprmm()
	cm110.get_speed()	
	#cm110.set_goto(2500)
	#cm110.set_speed(500)
	#cm110.set_scan(1000,1500)	

	# clean up and close the cm110 port
	cm110.close()
 
if __name__ == "__main__":
	
  main()
  


