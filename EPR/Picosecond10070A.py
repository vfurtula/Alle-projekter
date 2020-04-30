# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import visa, time

# Python driver for Picosecond Model 10,070A pulse generator
class Picosecond10070A:
	
	def __init__(self, myadr):
		rm = visa.ResourceManager()
		print(rm.list_resources())
		self.picosecond = rm.open_resource(myadr)
		self.picosecond.clear()
		
		self.arguments=["amplitude", "delay", "disable", "duration", "enable", "frequency", "gate", "header", "hysteresis", "level", "limit", "offset", "period", "*rcl", "*rst", "*trg"]
		
	def communicate(self,*argv):
		if len(argv)==1 and type(argv[0]).__name__=='str':
			mystr=argv[0]
			
			if mystr:
				if len(mystr.split())==1:
					if mystr[-1]=='?' and mystr[:-1] in self.arguments:
						self.picosecond.write(mystr)
						time.sleep(5e-3)
						return self.picosecond.read()
					elif mystr[0]=='*' and mystr in self.arguments:
						self.picosecond.write(mystr)
						time.sleep(5e-3)
						return ''.join([mystr.upper(), " passed to the Picosecond Model 10,070A"])
					elif mystr in ['enable','disable']:
						self.picosecond.write(mystr)
						time.sleep(5e-3)
						return ''.join([mystr.upper(), " passed to the Picosecond Model 10,070A"])
					else:
						raise ValueError(''.join([mystr.upper(), " is not a valid Picosecond Model 10,070A command!"]))
					
				elif len(mystr.split())==2:
					if mystr.split()[0] in self.arguments:
						self.picosecond.write(mystr)
						time.sleep(5e-3)
						return ''.join([mystr.upper(), " passed to the Picosecond Model 10,070A"])
					else:
						raise ValueError(''.join([mystr.upper(), " is not a valid Picosecond Model 10,070A command!"]))
				
				else:
					raise ValueError(''.join(["You have passed more than 1 argument to the Picosecond Model 10,070A. Only 1 argument per command is required!"]))
			else:
				raise ValueError("An empty string is not a valid command to the Picosecond Model 10,070A!")
		else:
			raise ValueError("Pass a single and non-empty commandstring to the Picosecond Model 10,070A!")
		
		
		
if __name__=="__main__":
	
	# a small test program for the Picosecond Model 10,070A pulse generator
	ps = Picosecond10070A('GPIB0::6::INSTR')

	print(ps.communicate("*rst"))
	print(ps.communicate("frequency?"))
	print(ps.communicate("amplitude?"))
	print(ps.communicate("period?"))
	
	for i in range(5):
		print(ps.communicate("frequency 3578"))
		print(ps.communicate("frequency?"))
		
		print(ps.communicate("frequency 671"))
		print(ps.communicate("frequency?"))
		
		print(ps.communicate("amplitude -7.5e-2"))
		print(ps.communicate("amplitude?"))
		
		print(ps.communicate("amplitude 7.5e-2"))
		print(ps.communicate("amplitude?"))
		
		print(ps.communicate("period?"))
		
		print(ps.communicate("gate?"))
		
	print(ps.communicate("disable?"))



