#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""



import sys, serial, argparse, time, re, random
import numpy as np
import matplotlib.pyplot as plt 




class Zaber_Xmcb:
	
	def __init__(self,my_serial,testmode):
		# activate the serial. CHECK the serial port name!
		self.testmode = testmode
		
		if self.testmode:
			print("Testmode: Zaber X-MCB2 port opened")
			self.isopen = True
		elif not self.testmode:
			self.ser = serial.Serial(my_serial, 115200)
			print("Zaber X-MCB2 serial port:", my_serial)
			self.isopen = True
			time.sleep(1)
		
		
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
	
	
	####################################################################
	# Zaber functions Zaber functions Zaber functions Zaber functions ##
	####################################################################
	def set_timeout(self,val):
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method set_timeout")
		elif not self.testmode:
			self.ser.timeout=val
		
		
	def system_Reset(self,dev):
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method system_Reset")
		elif not self.testmode:
			sysRes=''.join(['/',str(dev),' system reset\r'])
			self.ser.write(sysRes)
			self.ser.readline()
		
		
	def move_Home(self,dev,axs):
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method move_Home")
		elif not self.testmode:
			moveHome=''.join(['/',str(dev),' ',str(axs),' home\r'])
			try:
				self.ser.write(moveHome)
				self.ser.readline()
			except Exception as e:
				raise Exception("No return from the move_Home command!")
			
			
	def move_Absolute(self,dev,axs,val):
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method move_Absolute")
		elif not self.testmode:
			moveAbsolute=''.join(['/',str(dev),' ',str(axs),' move abs ', str(val), '\r'])
			try:
				self.ser.write(moveAbsolute)
				self.ser.readline()
			except Exception as e:
				raise Exception("No return from the move_Absolute command!")
			
			
	def move_Relative(self,dev,axs,val):
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method move_Relative")
		elif not self.testmode:
			moveRelative=''.join(['/',str(dev),' ',str(axs),' move rel ', str(val),'\r'])
			try:
				self.ser.write(moveRelative)
				self.ser.readline()
			except Exception as e:
				raise Exception("No return from the moveRelative command!")
			
			
	def set_Current_Position(self,dev,axs,val):
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method set_Current_Position")
		elif not self.testmode:
			setPos=''.join(['/',str(dev),' ',str(axs),' set pos ', str(val), '\r'])
			try:
				self.ser.write(setPos)
				self.ser.readline()
			except Exception as e:
				raise Exception("No return from the set_Current_Position command!")
			
			
	def set_Alert(self,dev,val):
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method set_Alert")
		elif not self.testmode:
			setAlert=''.join(['/',str(dev),' set comm.alert ', str(val), '\r'])
			self.ser.write(setAlert)
			self.ser.readline()
		
		
	def return_Alert(self,dev):
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method return_Alert")
			return 1
		elif not self.testmode:
			getAlert=''.join(['/',str(dev),' get comm.alert\r'])
			try:
				self.ser.write(getAlert)
				val=self.ser.readline().split()
			except Exception as e:
				raise Exception("No return from the return_Alert command!")
			return int(val[5])
	
	
	def echo(self,axs):
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method echo")
		elif not self.testmode:
			echo=''.join(['/',str(axs),' tools echo $\r'])
			self.ser.write(echo)
			
			
	def set_Stop(self,dev,axs):
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method set_Stop")
		elif not self.testmode:
			setStop=''.join(['/',str(dev),' ',str(axs),' stop\r'])
			self.ser.write(setStop)
		
		
	def return_Current_Position(self,dev,axs):
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method return_Current_Position")
			if axs==1:
				return random.randint(210000,245000)
			elif axs==2:
				return random.randint(400,11000)
		elif not self.testmode:
			retPos=''.join(['/',str(dev),' ',str(axs),' get pos\r'])
			try:
				self.ser.write(retPos)
				val=self.ser.readline().split()
			except Exception as e:
				raise Exception("No return from the return_Current_Position command!")
			return int(val[5])
		
		
	def return_Position_When_Stopped(self,dev,axs):
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method return_Position_When_Stopped")
			return self.return_Current_Position(dev,axs)
		elif not self.testmode:
			while True:
				try:
					val=self.ser.readline().split()
				except Exception as e:
					raise Exception("No return from the return_Current_Position command!")
				
				if val[0:3]==[''.join(['!0',str(dev)]),str(axs),"IDLE"]:
					break
				
			return self.return_Current_Position(dev,axs)
		
		
	def set_System_Access(self,dev,val):
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method set_System_Access")
		elif not self.testmode:
			setSysAcc=''.join(['/',str(dev),' set system.access ', str(val), '\r'])
			self.ser.write(setSysAcc)
			self.ser.readline()
		
		
	def set_Motor_Dir(self,dev,axs,val):
		# val in range from 0 to 255
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method set_Motor_Dir")
		elif not self.testmode:
			setMotDir=''.join(['/',str(dev),' ',str(axs),' set driver.dir ',str(val),'\r'])
			self.ser.write(setMotDir)
			self.ser.readline()
		
		
	def set_Microstep_Resolution(self,dev,val):
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method set_Microstep_Resolution")
		elif not self.testmode:
			setResol=''.join(['/',str(dev),' set resolution ', str(val), '\r'])
			self.ser.write(setResol)
			self.ser.readline()
		
		
	def set_Maximum_Position(self,dev,axs,val):
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method set_Maximum_Position")
		elif not self.testmode:
			maxPos=''.join(['/',str(dev),' ',str(axs),' set limit.max ', str(val), '\r'])
			self.ser.write(maxPos)
			self.ser.readline()
		
		
	def set_Minimum_Position(self,dev,axs,val):
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method set_Minimum_Position")
		elif not self.testmode:
			minPos=''.join(['/',str(dev),' ',str(axs),' set limit.min ', str(val), '\r'])
			self.ser.write(minPos)
			self.ser.readline()
		
		
	def set_Max_Speed(self,dev,axs,val):
		# Valid Range: 1 to resolution*16384
		# The actual speed is calculated as val/1.6384 microsteps/sec
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method set_Max_Speed")
		elif not self.testmode:
			setMaxSpeed=''.join(['/',str(dev),' ',str(axs),' set maxspeed ',str(val),'\r'])
			self.ser.write(setMaxSpeed)
			self.ser.readline()
		
		
	def set_Hold_Current(self,dev,axs,val):
		# val in range from 0 to 255
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method set_Hold_Current")
		elif not self.testmode:
			setHoldCurr=''.join(['/',str(dev),' ',str(axs),' set driver.current.hold ',str(val),'\r'])
			self.ser.write(setHoldCurr)
			self.ser.readline()
		
		
	def set_Running_Current(self,dev,axs,val): 
		# val in range from 0 to 255
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method set_Running_Current")
		elif not self.testmode:
			setRunCurr=''.join(['/',str(dev),' ',str(axs),' set driver.current.run ',str(val),'\r'])
			self.ser.write(setRunCurr)
			self.ser.readline()
		
		
	def return_Max_Current(self,dev,axs):
		# val in range from 0 to 255
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method return_Max_Current")
			return 1
		elif not self.testmode:
			retMaxCurr=''.join(['/',str(dev),' ',str(axs),' get driver.current.max\r'])
			self.ser.write(retMaxCurr)
			my_string=self.ser.readline().split()
			return int(my_string[5])
		
		
	def return_System_Current(self,dev):
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method return_System_Current")
			return 1
		elif not self.testmode:
			retSysCurr=''.join(['/',str(dev),' get system.current\r'])
			self.ser.write(retSysCurr)
			my_string=self.ser.readline().split()
			return float(my_string[5])
		
		
	def return_Microstep_Resolution(self,dev,axs):
		if self.testmode:
			print("Testmode: Zaber X-MCB2 method return_Microstep_Resolution")
			if axs==1:
				return random.randint(210000,245000)
			elif axs==2:
				return random.randint(400,11000)
		elif not self.testmode:
			retResol=''.join(['/',str(dev),' ',str(axs),' get resolution\r'])
			self.ser.write(retResol)
			my_string=self.ser.readline().split()
			return int(my_string[5])
		
	# clean up and close the serial
	def close(self):
		if self.testmode:
			print("Testmode: Zaber port flushed and closed")
			self.isopen=False
		elif not self.testmode:
			print("Zaber port flushed and closed")
			self.ser.flush()
			self.ser.close()
			self.isopen=False
		
		
	def is_open(self):
		return self.isopen
	
	
		
		
		
		
def test():

	Za = Zaber_Xmcb("/dev/ttyUSB0")

	# disable/enable home status
	#Za.move_Home(1)
	print("Return the alert setting: ", Za.return_Alert(1))
	
	if Za.return_Alert(1)==0:
		Za.set_Alert(1,1)
	Za.set_Maximum_Position(1,1,250000)
	Za.set_Minimum_Position(1,1,0)
	Za.set_Current_Position(1,1,50000)
	Za.set_Max_Speed(1,1,2048)
	
	Za.set_Running_Current(1,1,10)
	Za.set_Hold_Current(1,1,10)
	print(Za.return_Microstep_Resolution(1,1))
	
	#Za.set_Microstep_Resolution(1,64)
	print(Za.return_Current_Position(1,1))

	Za.move_Relative(1,1,-10000)
	time.sleep(3)
	Za.set_Stop(1,1)
	
	#print(Za.return_Current_Position(1,1))
	while True:
		mystr=Za.is_Stopped(1,1)
		if mystr:
			print(Za.return_Current_Position(1,1))
			break
		else:
			print(Za.return_Current_Position(1,1))
			
	Za.move_Relative(1,1,10000)
	#time.sleep(3)
	#Za.set_Stop(1,1)
	
	while True:
		mystr=Za.is_Stopped(1,1)
		if mystr:
			print(Za.return_Current_Position(1,1))
			break
		else:
			print(Za.return_Current_Position(1,1))
			
			
			
	# clean up
	Za.close()
	
	
	
	
if __name__ == "__main__":
	
	test()
  


