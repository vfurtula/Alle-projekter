# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import matplotlib.pyplot as plt
import Picosecond10070A
import visa, time


class Agilent86100D:
	
	def __init__(self, addr):
		rm = visa.ResourceManager()
		print(rm.list_resources())
		
		self.scope = rm.open_resource(addr)
		self.scope.clear()
		self.scope.timeout=500 # units in milliseconds
		
	def initialise(self):
		self.scope.write('*rst')  # reset scope - initialize to known state 
		self.scope.write('*cls')  # clear status registers and output queue
		print(self.scope.query('*idn?'))
		#print( ''.join(["Time: ",self.scope.query(':system:time?')]) )
		self.scope.write(":system:autoscale")  # perform autoscale
		time.sleep(5)
		
		if self.scope.query(":timebase:units?") != "SEC":
			self.scope.write(":timebase:units sec")
		self.scope.write(":timebase:pos 35.0e-9")
		self.scope.write(":timebase:scale 2.5e-9")
		
	def measure(self):
		for i in range(10):
			print( ''.join(["Vamp=",self.scope.query(':meas:osc:vamplitude?')]) )
			print( ''.join(["Vpp=",self.scope.query(':meas:osc:vpp?')]) )
			print( ''.join(["Vbase=",self.scope.query(':meas:osc:vbase?')]) )
			print( ''.join(["Vrisetime=",self.scope.query(':meas:osc:risetime?')]) )
			
			
	def waveform(self):
		self.initialise()
		
		# set up the source for the waveform
		self.scope.write(":waveform:source chan1a")
		
		# set the general number of points    
		print(self.scope.query(":acquire:rlength?"))
		self.scope.write(":acquire:rlength:mode manual")
		self.scope.write(":acquire:rlength 4096")
		time.sleep(1)
		
		# show number of points for our waveform
		print(self.scope.query(":waveform:xyformat:points?"))
		
		# convert scope data to Python float object
		xdata = [float(i)*1e9 for i in self.scope.query(":waveform:xyformat:ascii:xdata?").split(',')]
		ydata = [float(i) for i in self.scope.query(":waveform:xyformat:ascii:ydata?").split(',')]
		
		# plot the data
		plt.plot(xdata, ydata, 'r--', linewidth=0.5)
		plt.xlabel('Time [nanoseconds]')
		plt.ylabel('Voltage [V]')
		plt.show()
		
		
def main():
	
	ps = Picosecond10070A.Picosecond10070A('GPIB0::6::INSTR')
	
	print(ps.communicate("*rst"))
	print(ps.communicate("frequency?"))
	print(ps.communicate("amplitude?"))
	print(ps.communicate("period?"))
	
	print(ps.communicate("amplitude 47e-2"))
	print(ps.communicate("period 10e-6"))
	print(ps.communicate("duration 5e-9"))
	print(ps.communicate("delay 40e-9"))
	
	print(ps.communicate("enable"))
	
	##############################################################
	
	scope=Agilent86100D('TCPIP0::169.254.250.68::inst0::INSTR')
	scope.waveform()
    

if __name__ == "__main__":
	
	main()
  
  
  
  
  
  
  
