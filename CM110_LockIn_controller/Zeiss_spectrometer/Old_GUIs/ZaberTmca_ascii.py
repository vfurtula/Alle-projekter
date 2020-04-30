import sys, serial, argparse, time, re
import numpy as np
import matplotlib.pyplot as plt 

class Zaber_Tmca:
	
	def __init__(self,my_serial):
	  # activate the serial. CHECK the serial port name!
	  self.my_serial=my_serial
	  self.ser = serial.Serial(self.my_serial, 115200, timeout=None)
	  print "Zaber serial port:", self.my_serial
  
  ####################################################################
  # Zaber functions
  ####################################################################
	def set_timeout(self,val):
		
		self.ser.timeout=val

	def system_Reset(self,dev):
	  sysRes=''.join(['/',str(dev),' system reset\r'])
	  self.ser.write(sysRes)
	  self.ser.readline()

	def move_Home(self,dev,axs):
		moveHome=''.join(['/',str(dev),' ',str(axs),' home\r'])
		self.ser.write(moveHome)
		self.ser.readline()

	def move_Absolute(self,dev,axs,val):
		moveAbsolute=''.join(['/',str(dev),' ',str(axs),' move abs ', str(val), '\r'])
		self.ser.write(moveAbsolute)
		self.ser.readline()
	  
	def move_Relative(self,dev,axs,val):
		moveRelative=''.join(['/',str(dev),' ',str(axs),' move rel ', str(val),'\r'])
		self.ser.write(moveRelative)
		self.ser.readline()

	def set_Stop(self,dev,axs):
	  setStop=''.join(['/',str(dev),' ',str(axs),' stop\r'])
	  self.ser.write(setStop)
	  self.ser.readline()

	def set_Current_Position(self,dev,axs,val):
	  setPos=''.join(['/',str(dev),' ',str(axs),' set pos ', str(val), '\r'])
	  self.ser.write(setPos)
	  self.ser.readline()
	  
	def set_Alert(self,dev,val):
	  setAlert=''.join(['/',str(dev),' set comm.alert ', str(val), '\r'])
	  self.ser.write(setAlert)
	  self.ser.readline()
	
	def return_Alert(self,dev):
		getAlert=''.join(['/',str(dev),' get comm.alert\r'])
		self.ser.write(getAlert)
		my_string=self.ser.readline().split()
		return int(my_string[5])
	
	def return_Position_When_Stopped(self,dev,axs):
		my_string=[''.join(['!0',str(dev)]),str(axs)]
		if self.ser.readline().split()[0:2]==my_string:
			return self.return_Current_Position(dev,axs)
		else:
			return None
	
	def return_Current_Position(self,dev,axs):
		retPos=''.join(['/',str(dev),' ',str(axs),' get pos\r'])
		self.ser.write(retPos)
		my_string=self.ser.readline().split()
		return int(my_string[5])
	
	def set_Microstep_Resolution(self,dev,val):
		setResol=''.join(['/',str(dev),' set resolution ', str(val), '\r'])
		self.ser.write(setResol)
		self.ser.readline()

	def set_Maximum_Position(self,dev,axs,val):
	  maxPos=''.join(['/',str(dev),' ',str(axs),' set limit.max ', str(val), '\r'])
	  self.ser.write(maxPos)
	  self.ser.readline()
	  
	def set_Minimum_Position(self,dev,axs,val):
	  minPos=''.join(['/',str(dev),' ',str(axs),' set limit.min ', str(val), '\r'])
	  self.ser.write(minPos)
	  self.ser.readline()
	
	def set_Max_Speed(self,dev,axs,val):
		# Valid Range: 1 to resolution*16384
		# The actual speed is calculated as val/1.6384 microsteps/sec
	  setMaxSpeed=''.join(['/',str(dev),' ',str(axs),' set maxspeed ',str(val),'\r'])
	  self.ser.write(setMaxSpeed)
	  self.ser.readline()
	
	def set_Hold_Current(self,dev,axs,val):
		# val in range from 0 to 255
	  setHoldCurr=''.join(['/',str(dev),' ',str(axs),' set driver.current.hold ',str(val),'\r'])
	  self.ser.write(setHoldCurr)
	  self.ser.readline()

	def set_Running_Current(self,dev,axs,val): 
		# val in range from 0 to 255
	  setRunCurr=''.join(['/',str(dev),' ',str(axs),' set driver.current.run ',str(val),'\r'])
	  self.ser.write(setRunCurr)
	  self.ser.readline()
	  
	def return_Max_Current(self,dev,axs):
		# val in range from 0 to 255
		retMaxCurr=''.join(['/',str(dev),' ',str(axs),' get driver.current.max\r'])
		self.ser.write(retMaxCurr)
		my_string=self.ser.readline().split()
		return int(my_string[5])
	
	def return_System_Current(self,dev):
		retSysCurr=''.join(['/',str(dev),' get system.current\r'])
		self.ser.write(retSysCurr)
		my_string=self.ser.readline().split()
		return float(my_string[5])

	def return_Microstep_Resolution(self,dev,axs):
		retResol=''.join(['/',str(dev),' ',str(axs),' get resolution\r'])
		self.ser.write(retResol)
		my_string=self.ser.readline().split()
		return int(my_string[5])

	# clean up serial
	def close(self):
	  # close serial
	  print "Zaber port flushed and closed"
	  self.ser.flush()
	  self.ser.close() 

def main():

	Za = Zaber_Tmca("/dev/ttyUSB0")

	# disable/enable home status
	#Za.move_Home(1)
	print "return alert setting: ", Za.return_Alert(1)
	if Za.return_Alert(1)==0:
		Za.set_Alert(1,1)
	Za.set_Maximum_Position(1,1,250000)
	Za.set_Minimum_Position(1,1,0)
	Za.set_Current_Position(1,1,50000)
	Za.set_Max_Speed(1,1,2048)
	
	Za.set_Running_Current(1,1,10)
	Za.set_Hold_Current(1,1,10)
	print Za.return_Microstep_Resolution(1,1)
	
	#Za.set_Microstep_Resolution(1,64)
	print Za.return_Current_Position(1,1)

	Za.move_Relative(1,1,-10000)
	time.sleep(3)
	Za.set_Stop(1,1)
	
	#print Za.return_Current_Position(1,1)
	while True:
		mystr=Za.return_Position_When_Stopped(1,1)
		if mystr==None:
			pass
		else:
			print mystr
			break
			
	Za.move_Relative(1,1,10000)
	#time.sleep(3)
	#Za.set_Stop(1,1)
	
	while True:
		mystr=Za.return_Position_When_Stopped(1,1)
		if mystr==None:
			pass
		else:
			print mystr
			break
	

	# clean up
	Za.close()

if __name__ == "__main__":
  main()
  


