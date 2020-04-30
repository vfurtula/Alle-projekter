import sys, subprocess, argparse, time, re, visa
import numpy as np
import matplotlib.pyplot as plt


class COMPexPRO_pyvisa:
	
	def __init__(self,my_ser):
		
		#subprocess.call(['sudo','chown','vfurtula:vfurtula','/dev/ttyUSB0'])
		# activate the serial. CHECK the serial port name!
		self.my_ser=my_ser
		self.delay=0.05
		self.timeout=0.25
		rm = visa.ResourceManager()
		self.ser = rm.open_resource(self.my_ser, timeout=1)
		print("Serial port: ",my_ser)
		#self.ser=serial.Serial(my_ser,baudrate=9600)
		#print("Serial port: ",my_ser)
		
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
		
		return bytes(line)[:-1].decode()
  
	def set_timeout_(self,val):
		
		self.ser.timeout=val
		
	####################################################################
  # COMPexPRO functions
  ####################################################################
	
	def get_timeout(self):
		
		time_start=time.time()
		while time.time()-time_start<self.timeout:
			my_string=''.join(['TIMEOUT?\r'])
			self.ser.write(my_string.encode())
			#time.sleep(self.delay)
			val=self._readline()
			if val in ["ON","OFF"]:
				return val
		
		print("No return from TIMEOUT? command")
		return
	
	
	def set_timeout(self,val):
		
		my_string=''.join(['TIMEOUT=',val,'\r'])
		self.ser.write(my_string.encode())
		time.sleep(self.delay)
		return self.get_timeout()
	
	
	def set_opmode(self,val):
		
		my_string=''.join(['OPMODE=',val,'\r'])
		self.ser.write(my_string.encode())
		if val=='ON':
			time.sleep(4.5)
		elif val=='OFF':
			time.sleep(1)
		else:
			time.sleep(0.05)
			
		return self.get_opmode()
	
	def get_opmode(self):
		
		time_start=time.time()
		while time.time()-time_start<self.timeout:
			my_string=''.join(['OPMODE?\r'])
			self.ser.write(my_string.encode())
			#time.sleep(self.delay)
			val=self._readline()
			if val:
				if val[0]=="O":
					return val
				
		print("No return from OPMODE? command")
		return
	
	
	def set_counter_reset(self):
		
		my_string=''.join(['COUNTER=RESET\r'])
		self.ser.write(my_string.encode())
		time.sleep(self.delay)
		return self.get_counter()
	
	
	def get_counter(self):
		
		time_start=time.time()
		while time.time()-time_start<self.timeout:
			my_string=''.join(['COUNTER?\r'])
			self.ser.write(my_string.encode())
			#time.sleep(self.delay)
			val=self._readline()
			if self.is_number(val):
				return int(val)
					
		print("No return from COUNTER? command")
		return
		
		
	def get_totalcounter(self):
		
		time_start=time.time()
		while time.time()-time_start<self.timeout:
			my_string=''.join(['TOTALCOUNTER?\r'])
			self.ser.write(my_string.encode())
			#time.sleep(self.delay)
			val=self._readline()
			if self.is_number(val):
				return int(val)
				
		print("No return from TOTALCOUNTER? command")
		return
	
	
	def set_reprate(self,val):
		
		my_string=''.join(['REPRATE=',val,'\r'])
		self.ser.write(my_string.encode())
		time.sleep(self.delay)
		return self.get_reprate()
	
	
	def get_reprate(self):
		
		time_start=time.time()
		while time.time()-time_start<self.timeout:
			my_string=''.join(['REPRATE?\r'])
			self.ser.write(my_string.encode())
			#time.sleep(self.delay)
			val=self._readline()
			if self.is_number(val):
				return float(val)
				
		print("No return from REPRATE? command")
		return
	
	
	def set_hv(self,val):
		
		my_string=''.join(['HV=',val,'\r'])
		self.ser.write(my_string.encode())
		time.sleep(self.delay)
		return self.get_hv()
	
	
	def get_hv(self):
		
		time_start=time.time()
		while time.time()-time_start<self.timeout:
			my_string=''.join(['HV?\r'])
			self.ser.write(my_string.encode())
			#time.sleep(self.delay)
			val=self._readline()
			if self.is_number(val):
				return float(val)
				
		print("No return from HV? command")
		return
	
	
	def set_inlo(self,val):
		
		my_string=''.join(['INTERLOCK=',val,'\r'])
		self.ser.write(my_string.encode())
		time.sleep(self.delay)
		return self.get_inlo()
	
	
	def get_inlo(self):
		
		time_start=time.time()
		while time.time()-time_start<self.timeout:
			my_string=''.join(['INTERLOCK?\r'])
			self.ser.write(my_string.encode())
			#time.sleep(self.delay)
			val=self._readline()
			return val
		
		print("No return from INTERLOCK? command")
		return
	
	
	def set_trigger(self,val):
			
		my_string=''.join(['TRIGGER=',val,'\r'])
		self.ser.write(my_string.encode())
		time.sleep(self.delay)
		return self.get_trigger()
	
	
	def get_trigger(self):
		
		time_start=time.time()
		while time.time()-time_start<self.timeout:
			my_string=''.join(['TRIGGER?\r'])
			self.ser.write(my_string.encode())
			#time.sleep(self.delay)
			val=self._readline()
			if val in ["INT","EXT"]:
				return val
		
		print("No return from TRIGGER? command")
		return
	
	
	def get_menu(self):
		
		time_start=time.time()
		while time.time()-time_start<self.timeout:
			my_string=''.join(['MENU?\r'])
			self.ser.write(my_string.encode())
			#time.sleep(self.delay)
			val=self._readline()
			if self.is_number(val[0]):
				return val.split(' ')
		
		print("No return from MENU? command")
		return
	
	
	def set_gasmode(self,val):
		
		my_string=''.join(['GASMODE=',val,'\r'])
		self.ser.write(my_string.encode())
		time.sleep(self.delay)
		return self.get_gasmode()
	
	
	def get_gasmode(self):
		
		my_string=''.join(['GASMODE?\r'])
		#time.sleep(self.delay)
		val=self.ser.query_ascii_values(my_string)
		if val in ["PREMIX","SINGLE GASES"]:
			return val
		
		print("No return from GASMODE? command")
		return
	
	
	def set_cod(self,val):
		
		my_string=''.join(['COD=',val,'\r'])
		self.ser.write(my_string.encode())
		time.sleep(self.delay)
		return self.get_cod()
	
	
	def get_cod(self):
		
		time_start=time.time()
		while time.time()-time_start<self.timeout:
			my_string=''.join(['COD?\r'])
			self.ser.write(my_string.encode())
			#time.sleep(self.delay)
			val=self._readline()
			if val:
				if val[0]=="O":
					return val
		
		print("No return from COD? command")
		return
		
		
	def get_buffer_press(self):
		
		my_string=''.join(['BUFFER?\r'])
		#time.sleep(self.delay)
		val=self.ser.query_ascii_values(my_string)
		if self.is_number(val):
			return float(val)
	
		print("No return from BUFFER? command")
		return
	
	
	def get_lt_press(self):
		
		my_string=''.join(['PRESSURE?\r'])
		#time.sleep(self.delay)
		val=self.ser.query_ascii_values(my_string)
		if self.is_number(val):
			return float(val)
				
		print("No return from PRESSURE? command")
		return
	
	
	def get_lt_temp(self):
		
		my_string=''.join(['RESERVOIR TEMP?\r'])
		#time.sleep(self.delay)
		val=self.ser.write(my_string)
		if self.is_number(val):
			return float(val)
				
		print("No return from RESERVOIR TEMP? command")
		return
	
	
	def get_f2_press(self):
		
		time_start=time.time()
		while time.time()-time_start<self.timeout:
			my_string=''.join(['LEAKRATE?\r'])
			self.ser.write(my_string.encode())
			#time.sleep(self.delay)
			val=self._readline()
			if self.is_number(val):
				return float(val)
				
		print("No return from LEAKRATE? command")
		return
	
	
	def get_f2_temp(self):
		
		time_start=time.time()
		while time.time()-time_start<self.timeout:
			my_string=''.join(['TEMP?\r'])
			self.ser.write(my_string.encode())
			#time.sleep(self.delay)
			val=self._readline()
			if self.is_number(val):
				return float(val)
				
		print("No return from TEMP? command")
		return
	
	
	def get_pulse_diff(self):
		
		time_start=time.time()
		while time.time()-time_start<self.timeout:
			my_string=''.join(['PULSE DIFF?\r'])
			self.ser.write(my_string.encode())
			#time.sleep(self.delay)
			val=self._readline()
			if self.is_number(val):
				return float(val)
				
		print("No return from PULSE DIFF? command")
		return
	
	
	def get_energy(self):
		
		my_string=''.join(['EGY?\r'])
		#time.sleep(self.delay)
		val=self.ser.query_ascii_values(my_string)
		print("return from EGY?\t",val)
		if self.is_number(val):
			return float(val)
				
		print("No return from EGY? command")
		return
	
	def get_pow_stab(self):
		
		my_string=''.join(['POWER STABILIZATION ACHIEVED?\r'])
		#time.sleep(self.delay)
		val=self.ser.query_ascii_values(my_string)
		if val in ["YES","NO"]:
			return val
				
		print("No return from POWER STABILIZATION ACHIEVED? command")
		return
	
	def get_version(self):
		
		time_start=time.time()
		while time.time()-time_start<self.timeout:
			my_string=''.join(['VERSION?\r'])
			self.ser.write(my_string.encode())
			#time.sleep(self.delay)
			val=self._readline()
			if val:
				if val[0]=="V":
					return val
				
		print("No return from VERSION? command")
		return
	
	def get_lasertype(self):
		
		time_start=time.time()
		while time.time()-time_start<self.timeout:
			my_string=''.join(['TYPE OF LASER?\r'])
			self.ser.write(my_string.encode())
			#time.sleep(self.delay)
			val=self._readline()
			if val:
				return val
				
		print("No return from TYPE OF LASER? command")
		return
	
	
	# clean up serial
	def close(self):
		# flush and close serial
		self.ser.flush()
		self.ser.close()
		print("Serial port flushed and closed")


def main():
  
	# call the COMPexPRO port
	COMPexPRO_laser = COMPexPRO("/dev/ttyUSB1")
	COMPexPRO_laser.set_timeout_(None)
	
	print(COMPexPRO_laser.set_timeout('OFF'))
	print(COMPexPRO_laser.set_trigger('INT'))
	
	#print COMPexPRO_laser.get_timeout()
	#print COMPexPRO_laser.get_opmode()
	
	#print COMPexPRO_laser.get_version()		
	#print COMPexPRO_laser.get_gasmode()
	#COMPexPRO_laser.set_gasmode('PREMIX')
	#print COMPexPRO_laser.get_gasmode()
	
	#print COMPexPRO_laser.get_reprate()
	#print COMPexPRO_laser.set_reprate('5')
	
	#print COMPexPRO_laser.get_hv()
	#print COMPexPRO_laser.set_hv('19.0')
	
	#val = COMPexPRO_laser.get_trigger()
	#print val

	#val = COMPexPRO_laser.get_inlo()
	#print val

	print(COMPexPRO_laser.get_opmode())
	print(COMPexPRO_laser.set_opmode('SKIP'))
	print(COMPexPRO_laser.set_opmode('ON'))
	
	print(COMPexPRO_laser.get_counter())
	time.sleep(5)
	print(COMPexPRO_laser.get_counter())
	
	print(COMPexPRO_laser.set_opmode('OFF'))
	COMPexPRO_laser.close()
	
 
if __name__ == "__main__":
	
  main()
  
