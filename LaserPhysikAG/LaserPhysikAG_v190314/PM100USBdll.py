# -*- coding: utf-8 -*-
"""
Spyder Editor

@author: Vedran Furtula
"""

import os, sys, time, ctypes, random

class PM100USBdll:
    
	def __init__(self, my_str, testmode):
		self.testmode = testmode
		
		if self.testmode:
			print("Testmode: PM100USB port opened")
			self.isopen = True
		elif not self.testmode:
			try:
				#os.chdir('C:/Program Files (x86)/IVI Foundation/VISA/WinNT/Bin/') #pointer to TLPM_32.dll
				os.chdir('C:/Program Files/IVI Foundation/VISA/Win64/Bin/')
				self.PM100USB = ctypes.cdll.LoadLibrary('TLPM_64.dll')
			except Exception as e:
				raise ValueError('PM100USB ValueError raised!\nDirectory where the dll file is placed does not exist!')
			
			inst = self.PM100USB.TLPM_init
			# prepare the constants and their type
			resourceName = my_str.encode()
			IDQuery = ctypes.c_bool(True)
			resetDevice = ctypes.c_bool(True)
			# prepare the pointer and its type
			self.instrumentHandle = ctypes.c_ulong()
			# call dll init function
			self.get_inst = inst(resourceName, IDQuery, resetDevice, ctypes.byref(self.instrumentHandle))
			print('TLPM_init\n\tdll reply code:', self.get_inst, '\n\t', self.errorMessage(self.get_inst))
			
			if self.get_inst!=0:
				raise ValueError( ''.join(['PM100USB ValueError raised!\nTLPM_init did not return 0, instead ',str(self.get_inst),' is returned!']) )
		
			self.isopen = True
			
	def findRsrc(self):
		if self.testmode:
			return "Testmode: TLPM_findRsrc"
		elif not self.testmode:
			if self.get_inst==0:
				inst = self.PM100USB.TLPM_findRsrc
				# prepare the pointer and its type
				resourceCount = ctypes.c_ulong()
				# call dll function
				get_inst = inst(self.instrumentHandle, ctypes.byref(resourceCount))
				print('TLPM_findRsrc\n\tdll reply code:', get_inst, '\n\t', self.errorMessage(get_inst))
				return resourceCount.value
		
		
	def getRsrcName(self, val):
		if self.testmode:
			return "Testmode: TLPM_getRsrcName"
		elif not self.testmode:
			if self.get_inst==0:
				inst = self.PM100USB.TLPM_getRsrcName
				# prepare constants, pointers and their types
				index=ctypes.c_ulong(val)
				readout = ctypes.create_string_buffer(512)
				# call dll function
				get_inst = inst(self.instrumentHandle, index, ctypes.byref(readout))
				print('TLPM_getRsrcName\n\tdll reply code:', get_inst, '\n\t', self.errorMessage(get_inst))
				return readout.value.decode()
		
		
	def reset(self):
		if self.testmode:
			return "Testmode: TLPM_reset"
		elif not self.testmode:
			if self.get_inst==0:
				inst = self.PM100USB.TLPM_reset
				# call dll function
				get_inst = inst(self.instrumentHandle)
				print('TLPM_reset\n\tdll reply code:', get_inst, '\n\t', self.errorMessage(get_inst))
		
		
	def setWavelength(self, val):
		if self.testmode:
			return "Testmode: TLPM_setWavelength"
		elif not self.testmode:
			if self.get_inst==0:
				inst = self.PM100USB.TLPM_setWavelength
				# prepare constants and their types
				wavelength=ctypes.c_double(val)
				# call dll function
				get_inst = inst(self.instrumentHandle, wavelength)
				print('TLPM_setWavelength\n\tdll reply code:', get_inst, '\n\t', self.errorMessage(get_inst))
			
			
	def setPowerRange(self, val):
		if self.testmode:
			return "Testmode: TLPM_setPowerRange"
		elif not self.testmode:
			if self.get_inst==0:
				inst = self.PM100USB.TLPM_setPowerRange
				# prepare constants and their types
				powerToMeasure=ctypes.c_double(val)
				# call dll function
				get_inst = inst(self.instrumentHandle, powerToMeasure)
				print('TLPM_setPowerRange\n\tdll reply code:', get_inst, '\n\t', self.errorMessage(get_inst))
			
			
	def getWavelength(self,val):
		if self.testmode:
			return "Testmode: TLPM_getWavelength"
		elif not self.testmode:
			if self.get_inst==0:
				inst = self.PM100USB.TLPM_getWavelength
				# prepare constants and their types 
				if val in [0,1,2]:
					attribute=ctypes.c_int(val) #args are 0, 1 or 2
				else:
					return ValueError('Arg should be 0, 1 or 2')
				wavelength=ctypes.c_double()
				# call dll function
				get_inst = inst(self.instrumentHandle, attribute, ctypes.byref(wavelength) )
				print('TLPM_getWavelength\n\tdll reply code:', get_inst, '\n\t', self.errorMessage(get_inst))
				return wavelength.value
		
		
	def getPowerRange(self,val):
		if self.testmode:
			return "Testmode: TLPM_getPowerRange"
		elif not self.testmode:
			if self.get_inst==0:
				inst = self.PM100USB.TLPM_getPowerRange
				# prepare constants and their types 
				if val in [0,1,2]:
					attribute=ctypes.c_int(val) #args are 0, 1 or 2
				else:
					return ValueError('Arg should be 0, 1 or 2')
				powerValue=ctypes.c_double()
				# call dll function
				get_inst = inst(self.instrumentHandle, attribute, ctypes.byref(powerValue) )
				print('TLPM_getPowerRange\n\tdll reply code:', get_inst, '\n\t', self.errorMessage(get_inst))
				return powerValue.value
		
		
	def measPower(self):
		if self.testmode:
			time.sleep(0.025)
			return random.uniform(-1,0)
		elif not self.testmode:
			if self.get_inst==0:
				inst = self.PM100USB.TLPM_measPower
				# prepare constants, pointers and their types
				power = ctypes.c_double()
				# call dll function
				get_inst = inst(self.instrumentHandle, ctypes.byref(power))
				print('TLPM_measPower\n\tdll reply code:', get_inst, '\n\t', self.errorMessage(get_inst))
				return power.value
		
		
	def measEnergy(self):
		if self.testmode:
			time.sleep(0.025)
			return random.uniform(-1,0)
		elif not self.testmode:
			if self.get_inst==0:
				inst = self.PM100USB.TLPM_measEnergy
				# prepare constants, pointers and their types
				energy = ctypes.c_double()
				# call dll function
				get_inst = inst(self.instrumentHandle, ctypes.byref(energy))
				print('TLPM_measEnergy\n\tdll reply code:', get_inst, '\n\t', self.errorMessage(get_inst))
				return energy.value
		
		
	def measFreq(self):
		if self.testmode:
			return "Testmode: TLPM_getPowerRange"
		elif not self.testmode:
			if self.get_inst==0:
				inst = self.PM100USB.TLPM_measFreq
				# prepare constants, pointers and their types
				freq = ctypes.c_double()
				# call dll function
				get_inst = inst(self.instrumentHandle, ctypes.byref(freq))
				print('TLPM_measFreq\n\tdll reply code:', get_inst, '\n\t', self.errorMessage(get_inst))
				return freq.value
		
		
	def errorMessage(self, statusCode):
		if self.testmode:
			return "Testmode: TLPM_getPowerRange"
		elif not self.testmode:
			if self.get_inst==0:
				inst = self.PM100USB.TLPM_errorMessage
				# prepare constants, pointers and their types
				readout = ctypes.create_string_buffer(512)
				# call dll function
				get_inst = inst(self.instrumentHandle, statusCode, ctypes.byref(readout))
				#print('errorMessage\n\t dll reply code:', get_inst)
				return readout.value.decode()
		
	
	def writeRaw(self, my_str):
		if self.testmode:
			return "Testmode: TLPM_writeRaw"
		elif not self.testmode:
			if self.get_inst==0:
				inst = self.PM100USB.TLPM_writeRaw
				# call dll function
				get_inst = inst(self.instrumentHandle, my_str)
				print('TLPM_writeRaw\n\tdll reply code:', get_inst, '\n\t', self.errorMessage(get_inst))
			
			
	def readRaw(self):
		if self.testmode:
			return "Testmode: TLPM_readRaw"
		elif not self.testmode:
			if self.get_inst==0:
				inst = self.PM100USB.TLPM_readRaw
				# prepare constants, pointers and their types
				string = ctypes.create_string_buffer(256)
				size = ctypes.c_ulong(256)
				returnCount = ctypes.c_ulong()
				# call dll function
				get_inst = inst(self.instrumentHandle, ctypes.byref(string),  size, ctypes.byref(returnCount))
				print('TLPM_readRaw\n\tdll reply code:', get_inst)
				print('Number of bytes returned from TLPM_readRaw:\n\t', returnCount.value, '\n\t', self.errorMessage(get_inst))
				return string.value.decode()
			
			
	def close(self):
		if self.testmode:
			print("Testmode: PM100USB port closed")
			self.isopen=False
		elif not self.testmode:
			if self.get_inst==0:
				inst = self.PM100USB.TLPM_close
				# call dll function
				get_inst = inst(self.instrumentHandle)
				print('TLPM_close\n\tdll reply code:', get_inst, '\n\t', self.errorMessage(get_inst))
				self.isopen=False
			
	def is_open(self):
		return self.isopen
			
			
class Test:

	def __init__(self):
		self.pm100usb = PM100USBdll('USB0::0x1313::0x8072::P2001111::INSTR')
		val = self.pm100usb.findRsrc()
		print(self.pm100usb.getRsrcName(val-1))
		
	def main(self):
		self.pm100usb.setWavelength(350)
		print(self.pm100usb.getWavelength(0))
		
		self.pm100usb.setWavelength(248)
		print(self.pm100usb.getWavelength(0))
		
		self.pm100usb.measFreq()
		self.pm100usb.setPowerRange(5)
		print(self.pm100usb.getPowerRange(0))
		
	def close(self):
		self.pm100usb.close()
			
			
			
			
if __name__=='__main__':
	
	try:
		run_test = Test()
		
		run_test.main()
		
		run_test.close()
	except KeyboardInterrupt:
		run_test.close()
		
		
