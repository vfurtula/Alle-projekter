import sys, os, subprocess
import datetime, time
import Gpib
import numpy as np
import matplotlib.pyplot as plt

############################################################

class IT6D_CA2:
	
	def __init__(self,my_gpb):
		
		subprocess.call(['sudo','gpib_config'])
		subprocess.call(['sudo','chown','vfurtula:vfurtula','/dev/gpib0'])
		
		# adr=9 for IT6D_CA2
		self.v=Gpib.Gpib(0,my_gpb)
		print "IT6D_CA2 microstepper GPIB port:", my_gpb
		#constants
		self.abs_posx='it6d_ca2_pos_x.txt'
		self.abs_posy='it6d_ca2_pos_y.txt'

	def get_positions(self):
		
		if os.path.isfile(self.abs_posx)==False:
			raise ValueError(''.join(['Position file ', self.abs_posx,' does not exist!']))
		else:
			with open(self.abs_posx,'r') as thefile:
				x=thefile.read()
		
		if os.path.isfile(self.abs_posy)==False:
			raise ValueError(''.join(['Position file ', self.abs_posy,' does not exist!']))
		else:
			with open(self.abs_posy,'r') as thefile:
				y=thefile.read()
		
		return x, y
		
	def reset(self,axs):
		#reset the microstepper
		pos=0
		if axs=='x':
			self.v.write('C1O\n')
			with open(self.abs_posx,'w') as thefile:
				thefile.write('%s' %pos)
		elif axs=='y':
			self.v.write('C2O\n')
			with open(self.abs_posy,'w') as thefile:
				thefile.write('%s' %pos)
		elif axs=='xy':
			self.v.write('CCO\n')
			with open(self.abs_posx,'w') as thefile:
				thefile.write('%s' %pos)
			with open(self.abs_posy,'w') as thefile:
				thefile.write('%s' %pos)
		else:
			raise ValueError('Reset function accepets only x or y or xy!')
  
	def move_abs(self,axs,pos):
		# convert to int if float received
		pos=int(pos)
		# get axis pointer and read position file
		if axs=='x':
			pointer='1'
			speed=380.0 # number of steps per second
			# open x file
			oldpos,_ = self.get_positions()
		elif axs=='y':
			pointer='2'
			speed=350.0 # number of steps per second
			# open y file
			_,oldpos = self.get_positions()
		else:
			raise ValueError('Axis to move can only be x or y!')
		
		# write a position trace to the user
		#print ''.join([axs.capitalize(),'_abs:']),pos
		# move and wait until movement finished
		if pos>0:
			self.v.write(''.join(['I',pointer,'=+',str(pos),'!\n']))
			time.sleep(abs(int(oldpos)-pos)/speed)
		elif pos<0:
			self.v.write(''.join(['I',pointer,'=',str(pos),'!\n']))
			time.sleep(abs(int(oldpos)-pos)/speed)
		elif pos==0:
			self.v.write(''.join(['I',pointer,'=-',str(pos),'!\n']))
			time.sleep(abs(int(oldpos)-pos)/speed)
		else:
			raise ValueError('The relative position is an integer!')
		
		# save position file
		if axs=='x':
			# save x file
			with open(self.abs_posx,'w') as thefile:
				thefile.write('%s' %pos) 
		elif axs=='y':
			# save y file
			with open(self.abs_posy,'w') as thefile:
				thefile.write('%s' %pos)
		else:
			raise ValueError('Axis to move can only be x or y!')

	def move_rel(self,axs,pos):
		# convert to int if float received
		pos=int(pos)
		# get axis pointer and read position file
		if axs=='x':
			pointer='1'
			speed=380.0 # number of steps per second
			# open x file
			oldpos,_ = self.get_positions()
		elif axs=='y':
			pointer='2'
			speed=350.0 # number of steps per second
			# open y file
			_,oldpos = self.get_positions()
		else:
			raise ValueError('Axis can only be x or y!')
		
		# calculate absolute position using the relative position
		newpos=int(oldpos)+pos
		# write a position trace to the user
		#print ''.join([axs,'_rel:']),pos, ''.join([', ',axs.capitalize(),'_abs:']),newpos
		# move and wait until movement finished
		if newpos>0:
			self.v.write(''.join(['I',pointer,'=+',str(newpos),'!\n']))
			time.sleep(abs(pos)/speed)
		elif newpos<0:
			self.v.write(''.join(['I',pointer,'=',str(newpos),'!\n']))
			time.sleep(abs(pos)/speed)
		elif newpos==0:
			self.v.write(''.join(['I',pointer,'=-',str(newpos),'!\n']))
			time.sleep(abs(pos)/speed)
		else:
			raise ValueError('The relative position is an integer!')
		
		# save position file
		if axs=='x':
			# save x file
			with open(self.abs_posx,'w') as thefile:
				thefile.write('%s' %newpos) 
		elif axs=='y':
			# save y file
			with open(self.abs_posy,'w') as thefile:
				thefile.write('%s' %newpos)
		else:
			raise ValueError('Axis can only be x or y!')

def make_test():
	
	move_x=-100
	move_y=-100
	it6d=IT6D_CA2(9)

	it6d.move_rel('x',move_x)
	it6d.move_rel('y',move_y)

	#it6d.reset('xy')


if __name__ == "__main__":
	
	make_test()

  
  
  
