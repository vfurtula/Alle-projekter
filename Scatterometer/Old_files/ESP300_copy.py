import sys, serial, argparse, time, re
import numpy as np
import matplotlib.pyplot as plt 

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
		
		self.ser.write(''.join([str(axs),'VA?','\r']))
		while True:
			val=self._readline()
			if self.is_number(val):
				return float(val)
			else:
				self.ser.write(''.join([str(axs),'VA?','\r']))

	def set_acc(self,axs,acc):
		
		self.ser.write(''.join([str(axs),'AC',str(acc),'\r']))

	def return_acc(self,axs):
		
		self.ser.write(''.join([str(axs),'AC?','\r']))
		while True:
			val=self._readline()
			if self.is_number(val):
				return float(val)
			else:
				self.ser.write(''.join([str(axs),'AC?','\r']))
			
	def return_pos(self,axs):
		
		self.ser.write(''.join([str(axs),'TP','\r']))
		while True:
			val=self._readline()
			if self.is_number(val):
				return round(float(val),2)
			else:
				self.ser.write(''.join([str(axs),'TP','\r']))
	
	def set_motors(self,onoff):
		
		for axs in [1,2,3]:
			if onoff=="on":
				self.ser.write(''.join([str(axs),'MO?','\r']))
				while True:
					val=self._readline()
					if self.is_number(val):
						if val==0:
							self.ser.write(''.join([str(axs),'MO','\r']))
							print "Motor",axs,"was turned off. Turned on now"
							return None
						elif val==1:
							print "Motor",axs,"is already turned on"
							return None
					else:
						self.ser.write(''.join([str(axs),'MO?','\r']))
			
			elif onoff=="off":
				self.ser.write(''.join([str(axs),'MF?','\r']))
				while True:
					val=self._readline()
					if self.is_number(val):
						if val==1:
							self.ser.write(''.join([str(axs),'MF','\r']))
							print "Motor",axs,"was turned on. Turned off now"
							return None
						elif val==0:
							print "Motor",axs,"is already turned off"
							return None
					else:
						self.ser.write(''.join([str(axs),'MF?','\r']))
			
			else:
				raise ValueError("set_motors accepts strings on or off")
	
	
	
	
	
	def set_all_home(self):
		
		for axs in [1,2,3]:
			self.ser.write(''.join([str(axs),'OR1','\r']))
	
	
	
	
	
	def set_stop(self):
		
		self.stop_falg=True
	
	def move_stop(self,axs):
		
		dwell=500 # dwell in milliseconds
		self.ser.write(''.join([str(axs),'ST','\r']))
		self.ser.write(''.join([str(axs),'WS',str(dwell),'\r']))
		return self.return_pos(axs)

	def move_abspos(self,axs,pos):
		
		#dwell=20 # dwell in milliseconds
		self.ser.write(''.join([str(axs),'PA',str(pos),'\r']))
		while True: 
			pos_now = self.return_pos(axs)
			if pos_now!=round(pos,2):
				if self.stop_falg==True:
					pos_now = self.move_stop(axs)
					self.stop_falg=False
					return pos_now
			else:
				return pos_now
	
	def move_relpos(self,axs,pos):
		
		#dwell=20 # dwell in milliseconds
		pos_init=self.return_pos(axs)
		self.ser.write(''.join([str(axs),'PR',str(pos),'\r']))
		while True: 
			pos_now = self.return_pos(axs)
			if pos_now!=round(pos_init+pos,2):
				if self.stop_falg==True:
					pos_now = self.move_stop(axs)
					self.stop_falg=False
					return pos_now
			else:
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
  


