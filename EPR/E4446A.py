# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import matplotlib.pyplot as plt
import visa, time


class E4446A:
	
	def __init__(self, addr):
		rm = visa.ResourceManager()
		print(rm.list_resources())
		
		self.inst = rm.open_resource(addr)
		self.inst.clear()
		self.inst.timeout=500 # units in milliseconds
		
		time.sleep(1)
		
		self.inst.write("init:rest")  # reset scope - initialize to known state 
		self.inst.write("*cls")  # clear status registers and output queue
		print(self.inst.query("*idn?"))
		print( ''.join(["Time: ",self.inst.query(":system:time?")]) )
		
		time.sleep(1)
		
		
	def initialise(self):
		
		self.inst.write("disp:wind:trac:y:rlev 20 dbm")
		self.inst.write("disp:wind:trac:y:pdiv 5 db")
		self.inst.write("pow:att 0 db")
		self.inst.write("bwid:auto on")
		time.sleep(2)
		
		
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
	
	
	def pow_att(self,val):
		
		if self.is_number(val):
			if val>=0 and val<=70:
				self.inst.write(''.join(["pow:att ",str(val)," db"]))
				return self.inst.query("pow:att?")
			else:
				raise ValueError("The attenuation is in the range from 0 dB to 70 dB.")
		else:
			raise ValueError("The built-in method pow_att accepts only real numbers!")
		
		
	def track(self,val):
		
		if val in ["on","off"]:
			self.inst.write(''.join(["calc:mark1:trck ",val]))
			return self.inst.query("calc:mark1:trck?")
		else:
			raise ValueError("The built-in method track accepts only on or off.")
			
			
	def read_track(self):
		
		return self.inst.query("calc:mark1:trck?")
	
	
	def freq_cent(self):
		
		return self.inst.query("freq:cent?")
	
	
	def waveform(self):
		self.initialise()
		
		# set up the source for the waveform
		self.inst.write(":waveform:source chan1a")
		
		# set the general number of points    
		print(self.inst.query(":acquire:rlength?"))
		self.inst.write(":acquire:rlength:mode manual")
		self.inst.write(":acquire:rlength 4096")
		time.sleep(1)
		
		# show number of points for our waveform
		print(self.inst.query(":waveform:xyformat:points?"))
		
		# convert scope data to Python float object
		xdata = [float(i)*1e9 for i in self.inst.query(":waveform:xyformat:ascii:xdata?").split(",")]
		ydata = [float(i) for i in self.inst.query(":waveform:xyformat:ascii:ydata?").split(",")]
		
		# plot the data
		plt.plot(xdata, ydata, 'r--', linewidth=0.5)
		plt.xlabel("Time [nanoseconds]")
		plt.ylabel("Voltage [V]")
		plt.show()
		
		
def main():
	
	inst = E4446A("TCPIP0::169.254.250.68::inst0::INSTR")
	inst.initialise()
	print(inst.pow_att(10))
	
	print(inst.track("on"))
	time_start=time.time()
	while time.time()-time_start<60:
		val1=inst.freq_cent()
		print("freq: ",val1)
		val2=inst.read_track()
		print("amp: ",val2)
		
	inst.track("off")
	
	

if __name__ == "__main__":
	
	main()
  
  
  
  
  
  
  
