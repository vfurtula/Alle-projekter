import sys, os, subprocess
import datetime, time
import Gpib, SR5210, Methods_for_IT6D_CA2, IT6D_CA2 
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D


timestr=time.strftime('%y%m%d-%H%M')

if len(sys.argv)<2:
	raise ValueError('A setup file is required!')
else:
	inFile=sys.argv[1]
	params=__import__(inFile)

if len(params.x_scan_mm)!=3:
	raise ValueError('x_scan_mm is a list of 3 elements [x_start,x_end,x_step]')
if len(params.y_scan_mm)!=3:
	raise ValueError('y_scan_mm is a list of 3 elements [y_start,y_end,y_step]')

op_mode=params.op_mode
ASM_delay=params.asm_delay
if op_mode=='xyscan':
	xstart=int(params.x_scan_mm[0]*1000)
	xend=int(params.x_scan_mm[1]*1000)
	xstep=int(params.x_scan_mm[2]*1000)
	ystart=int(params.y_scan_mm[0]*10000)
	yend=int(params.y_scan_mm[1]*10000)
	ystep=int(params.y_scan_mm[2]*10000)
	xy_limiter=int(params.xy_limiter_mm*1000)
	dwell_time=params.wait_time
	scan_mode=params.scan_mode
elif op_mode=='xscan':
	xstart=int(params.x_scan_mm[0]*1000)
	xend=int(params.x_scan_mm[1]*1000)
	xstep=int(params.x_scan_mm[2]*1000)
	xy_limiter=int(params.xy_limiter_mm*1000)
	dwell_time=params.wait_time
elif op_mode=='yscan':
	ystart=int(params.y_scan_mm[0]*10000)
	yend=int(params.y_scan_mm[1]*10000)
	ystep=int(params.y_scan_mm[2]*10000)
	xy_limiter=int(params.xy_limiter_mm*1000)
	dwell_time=params.wait_time
elif op_mode=='reset':
	reset_mode=params.reset_mode
elif op_mode in ['abs','rel']:
	if len(params.move_mm)!=2:
		raise ValueError('move_mm is a list of two elements, f.ex. move_mm=[-1,2]')
	move_x=int(params.move_mm[0]*1000)
	move_y=int(params.move_mm[1]*10000)
	xy_limiter=int(params.xy_limiter_mm*1000)
else:
	raise ValueError('Invalid operation mode (op_mode) input!')
	
if params.file_name:
	str_filename=''.join([params.file_name,timestr])
else:
	str_filename=''.join(['data_',timestr])

if params.new_folder:
	saveinfolder=''.join([params.new_folder,'/'])
	if not os.path.isdir(params.new_folder):
		os.mkdir(params.new_folder)
else:
	saveinfolder=''

############################################################
############################################################
############################################################

class Run_IT6D_CA2:
	
	def __init__(self,it6d):
		#constants
		self.data_file=''.join([saveinfolder,str_filename,'.txt'])
		self.data_file_spine=''.join([saveinfolder,str_filename,'_spine.txt'])
		
		if op_mode == 'xyscan':
			self.sm=Methods_for_IT6D_CA2.Scan_methods(xstart,xend,xstep,ystart,yend,ystep)
			
		self.it6d=it6d
		self.sr5210 = SR5210.SR5210()
		
		#self.ASM_delay=ASM_delay
		#self.XTC_delay=1.5

	def init_lockin(self):
		pass
		'''
		# Set the reference source to external input mode
		self.sr5210.write(''.join(['IE 0']))
		time.sleep(1)
		# Turn off line frequency rejection filter
		self.sr5210.write(''.join(['LF 0']))
		time.sleep(1)
		# set auto-measure
		self.sr5210.write(''.join(['SEN 14']))
		time.sleep(2)
		'''

	def get_lockin_data(self):
		'''
		# get the output from the overload status command
		self.sr5210.write(''.join(['N\n']))
		time.sleep(self.set_delay)
		out_N=self.sr5210.read()
		# the N output is following LSB-0, therefore list inversion
		N_to_bin='{0:08b}'.format(int(out_N))[::-1]
		#print 'N_to_bin =', N_to_bin
		'''
		
		# set auto-measure
		#self.sr5210.write(''.join(['ASM']))
		#time.sleep(self.ASM_delay)
		
		# set the output filter slope to 12dB/ostave
		#self.sr5210.write(''.join(['XDB 1']))
		#time.sleep(self.set_delay)
		
		# set time constant to 100 ms, since previous ASM may have changed it 
		#self.sr5210.write(''.join(['XTC 4']))
		#time.sleep(self.set_delay)
		
		# get the present sensitivity setting
		#self.sr5210.write(''.join(['SEN']))
		#time.sleep(self.set_delay)
		senrangecode=self.sr5210.return_sen()
		#print 'senrangecode =', senrangecode
		
		# for the equation see page 6-21 in the manual
		senrange=(1+(2*(int(senrangecode)%2)))*10**(int(senrangecode)/2-7)
		#print 'senrange =', senrange
		
		# reads X channel output
		#self.sr5210.write(''.join(['X']))
		#time.sleep(self.set_delay)
		outputuncalib=self.sr5210.return_X()
		#print 'outputuncalib =',outputuncalib
		
		# assuming N_to_bin[1]=='0' and N_to_bin[2]=='0'
		outputcalib=int(outputuncalib)*senrange*1e-4

		return outputcalib

	def xyscan(self):

		with open(self.data_file, 'w') as thefile:
			thefile.write("Your edit line - do NOT delete this line\n") 
			thefile.write("X-pos [um], Y-pos [um], Voltage [V]\n")
			
		with open(self.data_file_spine, 'w') as thefile:
			thefile.write("Your edit line - do NOT delete this line\n") 
			thefile.write("X-pos [um], Y-pos [um], Max voltage [V]\n")
		
		try:
			if scan_mode=='xwise':
				ii,jj = self.sm.xwise()
				for i,j in zip(ii,jj):
					# move the microsteppers to the calculated positions
					self.it6d.move_abs('x',i)
					self.it6d.move_abs('y',j)
					time.sleep(dwell_time)
					# get the voltage data and save data in a file
					outputcalib=self.get_lockin_data()
					with open(self.data_file, 'a') as thefile:
						thefile.write('%s\t' %i)
						thefile.write('%s\t' %(0.1*j))
						thefile.write('%s\n' %outputcalib)
					print 'X_abs:',i, ', Y_abs:',j, ', Vlockin:',outputcalib
				
			elif scan_mode=='ywise':
				ii,jj = self.sm.ywise()
				for i,j in zip(ii,jj):
					# move the microsteppers to the calculated positions
					self.it6d.move_abs('x',i)
					self.it6d.move_abs('y',j)
					time.sleep(dwell_time)
					# get the voltage data and save data in a file
					outputcalib=self.get_lockin_data()
					with open(self.data_file, 'a') as thefile:
						thefile.write('%s\t' %i)
						thefile.write('%s\t' %(0.1*j))
						thefile.write('%s\n' %outputcalib)
					print 'X_abs:',i, ', Y_abs:',j, ', Vlockin:',outputcalib
				
			elif scan_mode=='xsnake':
				ii,jj = self.sm.xsnake()
				for i,j in zip(ii,jj):
					voltages=[]
					pos_x=[]
					# move the microsteppers to the calculated positions
					self.it6d.move_abs('x',i)
					self.it6d.move_abs('y',j)
					time.sleep(dwell_time)
					# get the voltage data and save data in a file
					outputcalib=self.get_lockin_data()
					with open(self.data_file, 'a') as thefile:
						thefile.write('%s\t' %i)
						thefile.write('%s\t' %(0.1*j))
						thefile.write('%s\n' %outputcalib)
					print 'X_abs:',i, ', Y_abs:',j, ', Vlockin:',outputcalib
					# calculate spine positions along the x axis
					pos_x.extend([ i ])
					voltages.extend([ outputcalib ])
					ind_max=np.argmax(voltages)
					with open(self.data_file_spine, 'a') as thefile:
						thefile.write('%s\t' %pos_x[ind_max])
						thefile.write('%s\t' %(0.1*j))
						thefile.write('%s\n' %voltages[ind_max])
						
			elif scan_mode=='ysnake':
				ii,jj = self.sm.ysnake()
				for i,j in zip(ii,jj):
					voltages=[]
					pos_x=[]
					# move the microsteppers to the calculated positions
					self.it6d.move_abs('x',i)
					self.it6d.move_abs('y',j)
					time.sleep(dwell_time)
					# get the voltage data and save data in a file
					outputcalib=self.get_lockin_data()
					with open(self.data_file, 'a') as thefile:
						thefile.write('%s\t' %i)
						thefile.write('%s\t' %(0.1*j))
						thefile.write('%s\n' %outputcalib)
					print 'X_abs:',i, ', Y_abs:',j, ', Vlockin:',outputcalib
					# calculate spine positions along the x axis
					pos_x.extend([ i ])
					voltages.extend([ outputcalib ])
					ind_max=np.argmax(voltages)
					with open(self.data_file_spine, 'a') as thefile:
						thefile.write('%s\t' %pos_x[ind_max])
						thefile.write('%s\t' %(0.1*j))
						thefile.write('%s\n' %voltages[ind_max])
						
			else:
				raise ValueError('Valid scan_mode input: xwise, ywise, xsnake, ysnake!')
		
		except KeyboardInterrupt:
			print "exiting..."
		
	def xscan(self):

		with open(self.data_file, 'w') as thefile:
			thefile.write("Your edit line - do NOT delete this line\n") 
			thefile.write("X-pos [um], Voltage [V]\n")
			
		try:  
			for i in range(xstart,xend+xstep,xstep):
				self.it6d.move_abs('x',i)
				time.sleep(dwell_time)
				outputcalib=self.get_lockin_data()
				with open(self.data_file, 'a') as thefile:
					thefile.write('%s\t' %i)
					thefile.write('%s\n' %outputcalib)
				print 'X_abs:',i,', Vlockin:',outputcalib
				
		except KeyboardInterrupt:
			print "exiting..."

	def yscan(self):

		with open(self.data_file, 'w') as thefile:
			thefile.write("Your edit line - do NOT delete this line\n") 
			thefile.write("Y-pos [um], Voltage [V]\n")
		
		try:
			for j in range(ystart,yend+ystep,ystep):
				self.it6d.move_abs('y',j)
				time.sleep(dwell_time)
				outputcalib=self.get_lockin_data()
				with open(self.data_file, 'a') as thefile:
					thefile.write('%s\t' %j)
					thefile.write('%s\n' %outputcalib)
				print 'Y_abs:',j,', Vlockin:',outputcalib
			
		except KeyboardInterrupt:
			print "exiting..."

def main():
  
	it6d = IT6D_CA2.IT6D_CA2(xy_limiter)
	it6d_ = Run_IT6D_CA2(it6d)

	if op_mode=='xyscan':
		it6d_.xyscan()
		data_raw=''.join([saveinfolder,str_filename,'.txt'])
		# plot the data as a contour plot
		X_data=[]
		Y_data=[]
		Lockin_data=[]
		with open(data_raw,'r') as thefile:
			header1=thefile.readline()
			header2=thefile.readline()
			for lines in thefile:
				columns=lines.split()
				X_data.extend([ float(columns[0]) ])
				Y_data.extend([ float(columns[1]) ])
				Lockin_data.extend([ float(columns[2]) ])
		fig=plt.figure(figsize=(8,6))
		ax= fig.add_subplot(111, projection='3d')
		#ax=fig.gca(projection='2d')
		ax.plot_trisurf(np.array(X_data),np.array(Y_data),np.array(Lockin_data),cmap=cm.jet,linewidth=0.2)
		ax.set_xlabel('X[um]')
		ax.set_ylabel('Y[um]')
		ax.set_zlabel('U[V]')
		plt.savefig(''.join([saveinfolder,str_filename,'.png']))
		# only if scan_mode is set to xsnake or ysnake
		if scan_mode in ['xsnake','ysnake']:
			X_data=[]
			Y_data=[]
			Lockin_data=[]
			data_raw_spine=''.join([saveinfolder,str_filename,'_spine.txt'])
			with open(data_raw_spine,'r') as thefile:
				header1=thefile.readline()
				header2=thefile.readline()
				for lines in thefile:
					columns=lines.split()
					X_data.extend([ float(columns[0]) ])
					Y_data.extend([ float(columns[1]) ])
					Lockin_data.extend([ float(columns[2]) ])

			delta_x=X_data[0]-X_data[-1]
			delta_y=Y_data[0]-Y_data[-1]
			S=(delta_x**2+delta_y**2)**0.5
			print "S factor:", S
			
			with open(data_raw_spine, 'a') as thefile:
				thefile.write("\nY_new [um], Max voltage [V]\n")
				for ydata,Umax in zip(Y_data,Lockin_data):
					thefile.write('%s\t' %((S/abs(delta_y))*ydata))
					thefile.write('%s\n' %Umax)
			
			fig=plt.figure(figsize=(8,6))
			plt.plot((S/abs(delta_y))*np.array(Y_data), np.log(Lockin_data), linewidth=0.5)
			plt.xlabel('Y_new [um]')
			plt.ylabel('Ln(U_max) [V]')
			plt.savefig(''.join([saveinfolder,str_filename,'_spine.png']))
			subprocess.call(['gedit',data_raw])
			plt.show()
		
	elif op_mode=='xscan':
		it6d_.xscan()
		data_raw=''.join([saveinfolder,str_filename,'.txt'])
		# plot the data as a contour plot
		X_data=[]
		Lockin_data=[]
		with open(data_raw,'r') as thefile:
			header1=thefile.readline()
			header2=thefile.readline()
			for lines in thefile:
				columns=lines.split()
				X_data.extend([ float(columns[0]) ])
				Lockin_data.extend([ float(columns[1]) ])
		fig=plt.figure(figsize=(8,6))
		plt.plot(np.array(X_data),np.array(Lockin_data))
		plt.xlabel('X[um]')
		plt.ylabel('U[V]')
		plt.savefig(''.join([saveinfolder,str_filename,'.png']))
		subprocess.call(['gedit',data_raw])
		plt.show()
		
	elif op_mode=='yscan':
		it6d_.yscan()
		data_raw=''.join([saveinfolder,str_filename,'.txt'])
		# plot the data as a contour plot
		Y_data=[]
		Lockin_data=[]
		with open(data_raw,'r') as thefile:
			header1=thefile.readline()
			header2=thefile.readline()
			for lines in thefile:
				columns=lines.split()
				Y_data.extend([ float(columns[0]) ])
				Lockin_data.extend([ float(columns[1]) ])
		fig=plt.figure(figsize=(8,6))
		plt.plot(np.array(Y_data),np.array(Lockin_data))
		plt.xlabel('Y[um]')
		plt.ylabel('U[V]')
		plt.savefig(''.join([saveinfolder,str_filename,'.png']))
		subprocess.call(['gedit',data_raw])
		plt.show()

	elif op_mode=='rel':
		it6d.move_rel('x',move_x)
		it6d.move_rel('y',move_y)

	elif op_mode=='abs':
		it6d.move_abs('x',move_x)
		it6d.move_abs('y',move_y)

	elif op_mode=='reset':
		it6d.reset(reset_mode)

	else:
		raise ValueError('Operation mode parameter op_mode has an invalid input!')

if __name__ == "__main__":
	main()

  
  
  
