import sys, serial, argparse, time, re
import numpy as np
import matplotlib as plt 

class ESP300:
	
	def __init__(self,my_serial):
	  # activate the serial. CHECK the serial port name!
	  self.ser = serial.Serial(my_serial, baudrate=19200)
	  print "ESP300 serial port:", my_serial
	  time.sleep(1)
	  
	  self.stop_falg=False

	def set_timeout(self,val):
		
		self.ser.timeout=val
		
	############################################################
	# Check input if a number, ie. digits or fractions such as 3.141
	# Source: http://www.pythoncentral.io/how-to-check-if-a-string-is-a-number-in-python-including-unicode/
	def is_int(self,s):
		try: 
		  int(s)
		  return True
		except ValueError:
		  return False
	
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
		return bytes(line[:-leneol])
  
  ####################################################################
  # ESP300 functions
  ####################################################################
	def set_speed(self,axs,sp):
		
		self.ser.write(''.join([str(axs),'VA',str(sp),'\r']))

	def return_speed(self,axs):
		
		while True:
			self.ser.write(''.join([str(axs),'VA?','\r']))
			val=self._readline()
			if self.is_number(val):
				return float(val)

	def return_acc(self,axs):
		
		while True:
			self.ser.write(''.join([str(axs),'AC?','\r']))
			val=self._readline()
			if self.is_number(val):
				return float(val)
			
	def return_pos(self,axs):
		
		while True:
			self.ser.write(''.join([str(axs),'TP','\r']))
			val=self._readline()
			if self.is_number(val):
				return round(float(val),2)
	
	def return_ver(self):
		
		self.ser.write(''.join(['VE?','\r']))
		val=self._readline()
		return val
		
	def set_acc(self,axs,acc):
		
		self.ser.write(''.join([str(axs),'AC',str(acc),'\r']))
	
	def set_motors(self,onoff):
		
		for axs in [1,2,3]:
			if onoff=="on":
				while True:
					self.ser.write(''.join([str(axs),'MO?','\r']))
					val=self._readline()
					if self.is_number(val):
						if int(val)==0:
							self.ser.write(''.join([str(axs),'MO','\r']))
							print "Axis",axs,"was turned off. Turned on now"
							break
						elif int(val)==1:
							print "Axis",axs,"is already turned on"
							break
			
			elif onoff=="off":
				while True:
					self.ser.write(''.join([str(axs),'MF?','\r']))
					val=self._readline()
					if self.is_number(val):
						if int(val)==1:
							self.ser.write(''.join([str(axs),'MF','\r']))
							print "Axis",axs,"was turned on. Turned off now"
							break
						elif int(val)==0:
							print "Axis",axs,"is already turned off"
							break
			
			else:
				raise ValueError("set_motors accepts strings on or off")
	
	def go_home(self,axs):
		
		self.ser.write(''.join([str(axs),'OH20','\r']))
		self.ser.write(''.join([str(axs),'OR1','\r']))
		while True:
			self.ser.write(''.join([str(axs),'MD?','\r']))
			val=self._readline()
			if self.is_int(val):
				if int(val)==1:
					print "Axis",axs,"homed"
					break
				elif int(val)==0:
					pass
	
	def set_stop(self):
		
		self.stop_falg=True
	
	def move_stop(self,axs):
		
		dwell=500 # dwell in milliseconds
		self.ser.write(''.join([str(axs),'ST','\r']))
		self.ser.write(''.join([str(axs),'WS',str(dwell),'\r']))
		curr_pos = self.return_pos(axs)
		return curr_pos

	def move_abspos(self,axs,pos):
		
		self.ser.write(''.join([str(axs),'PA',str(pos),'\r']))
		while True:
			self.ser.write(''.join([str(axs),'MD?','\r']))
			val=self._readline()

			if self.is_int(val):
				if int(val)==1:
					self.ser.write(''.join([str(axs),'WS',str(300),'\r']))
					curr_pos = self.return_pos(axs)
					return curr_pos
				elif int(val)==0:
					pass
			
			if self.stop_falg==True:
				pos_now = self.move_stop(axs)
				self.stop_falg=False
				return pos_now
			
	def move_relpos(self,axs,pos):
		
		self.ser.write(''.join([str(axs),'PR',str(pos),'\r']))
		while True:
			self.ser.write(''.join([str(axs),'MD?','\r']))
			val=self._readline()
			
			if self.is_int(val):
				if int(val)==1:
					self.ser.write(''.join([str(axs),'WS',str(300),'\r']))
					curr_pos = self.return_pos(axs)
					return curr_pos
				elif int(val)==0:
					pass				
			
			if self.stop_falg==True:
				pos_now = self.move_stop(axs)
				self.stop_falg=False
				return pos_now
			
	# clean up serial
	def close(self):
	  # flush and close serial
	  self.ser.flush()
	  self.ser.close()
	  print "ESP300 port flushed and closed" 

def test():
  
	# call the Motorstep drive port
	esp = ESP300("/dev/ttyUSB0")
	
	# do some testing here
	esp.set_speed(1,5)
	speed1 = esp.return_speed(1)
	print "axs1 speed:",speed1

	pos1 = esp.move_abspos(1,150)
	print "axs 1 pos:",pos1
	pos2 = esp.move_relpos(1,-20)
	print "axs 1 pos:",pos2
	
	pos1 = esp.move_abspos(2,110)
	print "axs 2 pos:",pos1
	pos2 = esp.move_relpos(2,-20)
	print "axs 2 pos:",pos2
	
	pos1 = esp.move_abspos(3,90)
	print "axs 3 pos:",pos1
	pos2 = esp.move_relpos(3,-20)
	print "axs 3 pos:",pos2
	
	# clean up and close the Motorstep drive port
	esp.close()
 
if __name__ == "__main__":
	
  test()
  


