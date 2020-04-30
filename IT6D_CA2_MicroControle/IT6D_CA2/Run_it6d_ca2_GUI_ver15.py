import os, sys, re, imp, serial, time, numpy, yagmail
import matplotlib as mpl
from matplotlib import cm
import scipy.optimize as scop
from scipy.interpolate import UnivariateSpline
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
#import pyqtgraph.opengl as gl
import pyqtgraph.exporters
#from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread, SIGNAL
import config_IT6D_CA2
import SR810
import Methods_for_IT6D_CA2
import numpy.polynomial.polynomial as poly
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D




class Run_IT6D_CA2_Thread(QThread):
	
	def __init__(self,*argv):
		QThread.__init__(self)
		
		# constants	
		self.end_flag=False
		
		self.op_mode = argv[0]
		self.scan_mode = argv[1]
		self.smart_scan = argv[2]
		self.data_file = argv[3]
		self.xscan = argv[4]
		self.yscan = argv[5]
		self.dwell_time = argv[6]
		self.reset_mode = argv[7]
		self.it6d = argv[8]
		self.sr810 = argv[9]

	def __del__(self):
		
		self.wait()
	
	def abort(self):
		
		self.end_flag=True
	
	def nearest_point(self,a,b,c,x1,y1):
		# Nearest point on line ax+by+c=0 to the point (x1,y1)
		x=(b*(b*x1-a*y1)-a*c)/(a**2+b**2)
		y=(a*(-b*x1+a*y1)-b*c)/(a**2+b**2)	
		return x,y
	
	
	def dist_to_line(self,p0,x1,y1):
		# Shortest distance between line ax+by+c=0 and points (x1,y1)
		return (p0[0]*x1+p0[1]*y1+p0[2])/(p0[0]**2+p0[1]**2)**0.5
	
	
	def gauss(self,x,p): #p[0]==mean, p[1]==stdev, p[2]==peak height, p[3]==noise floor
		
		return p[2]*numpy.exp(-(x-p[0])**2/(2*p[1]**2))+p[3]
	
	def fit_to_gauss(self,pos,volts):
		
		# Fit a gaussian
		# p0 is the initial guess for the gaussian
		p0 = [pos[numpy.argmax(volts)]] # mean
		p0.extend([numpy.std(volts)]) # stdev
		p0.extend([max(volts)-min(volts)]) # peak height
		p0.extend([min(volts)]) # noise floor
		
		errfunc = lambda p,x,y: self.gauss(x,p)-y # Distance to the target function
		p1, success = scop.leastsq(errfunc, p0, args=(pos,volts))
		
		#fit_stdev = p1[1]
		#fwhm = 2*(2*numpy.log(2))**0.5*fit_stdev
		sorted_pos=numpy.argsort(pos)
		spl=UnivariateSpline(pos[sorted_pos],volts[sorted_pos]-numpy.max(volts)/2,s=0)
		try:
			r1,r2 = spl.roots()
		except Exception as e:
			print "Roots r1 and r2 not found. Possibly number of roots is not 2."
			r1,r2=[0,0]
		
		return p1,r1,r2
	
	
	def atten(self,S,p):
		
		return p[1]*numpy.exp(-S*p[0])
	
	
	def fit_to_atten(self,S,volts):
		
		# Fit a gaussian
		p0 = [1,1] # Initial guess for the gaussian
		errfunc = lambda p,x,y: self.atten(x,p)-y # Distance to the target function
		p1, success = scop.leastsq(errfunc, p0[:], args=(S,numpy.array(volts)))
		#a, b = p1
		
		return p1
	
	
	def run(self):
		
		if self.op_mode=='xyscan':
			self.xyscan()
		elif self.op_mode=='xscan':
			self.def_xscan()
		elif self.op_mode=='yscan':
			self.def_yscan()
		elif self.op_mode=='move rel':
			self.move_rel()
		elif self.op_mode=='move abs':
			self.move_abs()
		elif self.op_mode=='reset':
			self.reset()
			
			
	def update_graphs(self,save_x,save_y,save_Umax,tal):
		
		self.emit(SIGNAL('update_Umax(PyQt_PyObject,PyQt_PyObject)'),save_x,save_y)
		
		if tal==0:
			S=numpy.array([0])
			
			return S
			
		elif tal==1:
			S=numpy.array([0])
			S=numpy.append(S, (numpy.diff(save_x)**2+numpy.diff(save_y)**2)**0.5)
			
			return S
		
		elif tal>1:
			save_Umax = numpy.array(save_Umax)
			# Shortest distance between line ax+by+c=0 and point (x1,y1)
			p0 = [1,1,1] # Initial guess for the gaussian
			errfunc = lambda p,xp,yp: self.dist_to_line(p,xp,yp) # Distance to the target function
			p1, success = scop.leastsq(errfunc, p0[:], args=(numpy.array(save_x),numpy.array(save_y)))
			a,b,c = p1

			xp_acc,yp_acc = self.nearest_point(a,b,c,numpy.array(save_x),numpy.array(save_y))

			delta_xy=(numpy.diff(xp_acc)**2+numpy.diff(yp_acc)**2)**0.5
			S=numpy.array([0])
			S=numpy.append(S, numpy.add.accumulate(delta_xy))
			xp_sor_round = numpy.round(xp_acc,6) # 1 um round accuracy
			yp_sor_round = numpy.round(yp_acc,7) # 0.1 um round accuracy
			
			self.emit(SIGNAL('update_Spath(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),xp_sor_round,yp_sor_round,S,save_Umax)
		
			return S
		
		
	def xyscan(self):
		
		data_file=''.join([self.data_file,".txt"])	
		data_file_spine=''.join([self.data_file,"_spine.txt"])
		
		x_array=self.xscan
		y_array=self.yscan

		with open(data_file, 'w') as thefile:
			thefile.write("Your comment line - do NOT delete this line\n")
			thefile.write("Col 0: X-pos [m]\nCol 1: Y-pos [m]\nCol 2: Voltage [V]\n\n")
			thefile.write('%s\t\t%s\t\t%s\n' %(tuple(''.join(["Col ",str(tal)]) for tal in range(3))))
		
		with open(data_file_spine, 'w') as thefile:
			thefile.write("Your comment line - do NOT delete this line\n")
			thefile.write("Col 0: Axis index\nCol 1: S_path [m]\n")
			thefile.write("Col 2: Max voltage X-pos[m]\nCol 3: Max voltage Y-pos[m]\n")
			thefile.write("Col 4: Max voltage [V]\nCol 5: Full width half maximum (FWHM) [m]\n\n")
			thefile.write('%s\t%s\t%s\t%s\t%s\t%s\n' %(tuple(''.join(["Col ",str(tal)]) for tal in range(6))))
			
		save_x=[]
		save_y=[]
		save_Umax=[]
		a2=[]
		fwhm=[]
		tals=[]
		i_,j_ = self.it6d.get_positions()
	  ###########################################
	  ########################################### 
		
		if self.scan_mode=='xwise':
			
			time_start=time.time()
			for j,tal_outer in zip(y_array,range(len(y_array))):
				self.it6d.move_abs('y',j)
				j_ = self.it6d.get_positions('y')
				self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'),1e-6*int(i_),1e-7*int(j_))
				voltages=[]
				pos_x=[]
				for i in x_array:
					if self.end_flag==True:
						break
					# move the microsteppers to the calculated positions
					self.it6d.move_abs('x',i)
					i_ = self.it6d.get_positions('x')
					self.emit(SIGNAL('update_pos_lcd(PyQt_PyObject,PyQt_PyObject)'),1e-6*int(i_),1e-7*int(j_))
					time_now=time.time()
					# update voltage readouts during dwell time
					while (time.time()-time_now)<self.dwell_time:
						outputcalib=self.sr810.return_X()
						time_elap=time.time()-time_start
						self.emit(SIGNAL('make_update2(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),time_elap,1e-6*int(i_),outputcalib)
					self.emit(SIGNAL('update_color_map(PyQt_PyObject)'),outputcalib)
					# get the last voltage value and save to a file
					with open(data_file, 'a') as thefile:
						thefile.write('%s\t\t' %(1e-6*int(i_)))
						thefile.write('%s\t\t' %(1e-7*int(j_)))
						thefile.write('%s\n' %(outputcalib))
					self.emit(SIGNAL('make_update4(PyQt_PyObject,PyQt_PyObject)'),time_elap,outputcalib)
					print 'X_abs:',int(i_), ', Y_abs:',int(j_), ', Vlockin:',outputcalib
					# calculate spine positions along the x axis
					pos_x.extend([ numpy.round(1e-6*int(i_),6) ])
					voltages.extend([ outputcalib ])
				
				if self.end_flag==True:
					break
				ind_max=numpy.argmax(voltages)
				
				save_x.extend([ pos_x[ind_max] ])
				save_y.extend([ numpy.round(1e-7*int(j_),7) ])
				save_Umax.extend([ voltages[ind_max] ])
				
				S = self.update_graphs(save_x,save_y,save_Umax,tal_outer)
				p1,r1,r2 = self.fit_to_gauss(numpy.array(pos_x),numpy.array(voltages))
				
				tals.extend([ tal_outer ])
				fwhm.extend([ abs(r1-r2) ])
				
				with open(data_file_spine, 'a') as thefile:
					for q,w,e,r,t,y in zip(tals,S,save_x,save_y,save_Umax,fwhm):
						thefile.write('%s\t' %q)
						thefile.write('%s\t' %w)
						thefile.write('%s\t' %e)
						thefile.write('%s\t' %r)
						thefile.write('%s\t' %t)
						thefile.write('%s\n' %y)
					
				self.emit(SIGNAL('update_fwhm(PyQt_PyObject,PyQt_PyObject)'),tals,fwhm)
				print "FWHM:", abs(r1-r2), "m"
				
				gauss_pos = numpy.linspace(min(pos_x),max(pos_x),5*len(pos_x))
				gauss_volts = self.gauss(gauss_pos,p1)
				self.emit(SIGNAL('plot_gaussian(PyQt_PyObject)'),[pos_x,voltages,'y',save_y[-1],gauss_pos,gauss_volts,[r1,r2]])
				
				if len(tals)>1:
					coef = self.fit_to_atten(S,save_Umax)
					a2.extend([ 4.343*coef[0]/100 ])
					self.emit(SIGNAL('update_slope(PyQt_PyObject,PyQt_PyObject)'),tals[1:],a2)
				
				if self.smart_scan=="yes":
					x_array=x_array+(ind_max-len(x_array)/2)*(x_array[1]-x_array[0])
				
		elif self.scan_mode=='ywise':

			time_start=time.time()
			for i,tal_outer in zip(x_array,range(len(x_array))):
				self.it6d.move_abs('x',i)
				i_ = self.it6d.get_positions('x')
				self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'),1e-6*int(i_),1e-7*int(j_))
				voltages=[]
				pos_y=[]
				for j in y_array:
					if self.end_flag==True:
						break
					# move the miself.it6dcrosteppers to the calculated positions
					self.it6d.move_abs('y',j)
					j_ = self.it6d.get_positions('y')
					self.emit(SIGNAL('update_pos_lcd(PyQt_PyObject,PyQt_PyObject)'),1e-6*int(i_),1e-7*int(j_))
					time_now=time.time()
					# update voltage readouts during dwell time
					while (time.time()-time_now)<self.dwell_time:
						outputcalib=self.sr810.return_X()
						time_elap=time.time()-time_start
						self.emit(SIGNAL('make_update2(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),time_elap,1e-7*int(j_),outputcalib)
					self.emit(SIGNAL('update_color_map(PyQt_PyObject)'),outputcalib)
					# get the last voltage value and save to a file
					with open(data_file, 'a') as thefile:
						thefile.write('%s\t\t' %(1e-6*int(i_)))
						thefile.write('%s\t\t' %(1e-7*int(j_)))
						thefile.write('%s\n' %(outputcalib))
					self.emit(SIGNAL('make_update4(PyQt_PyObject,PyQt_PyObject)'),time_elap,outputcalib)
					print 'X_abs:',int(i_), ', Y_abs:',int(j_), ', Vlockin:',outputcalib
					# calculate spine positions along the y axis
					pos_y.extend([ numpy.round(1e-7*int(j_),7) ])
					voltages.extend([ outputcalib ])
			
				if self.end_flag==True:
					break
				ind_max=numpy.argmax(voltages)
				
				save_x.extend([ numpy.round(1e-6*int(i_),6) ])
				save_y.extend([ pos_y[ind_max] ])
				save_Umax.extend([ voltages[ind_max] ])
				
				S = self.update_graphs(save_x,save_y,save_Umax,tal_outer)
				p1,r1,r2 = self.fit_to_gauss(numpy.array(pos_y),numpy.array(voltages))
				
				tals.extend([ tal_outer ])
				fwhm.extend([ abs(r1-r2) ])
				
				with open(data_file_spine, 'a') as thefile:
					for q,w,e,r,t,y in zip(tals,S,save_x,save_y,save_Umax,fwhm):
						thefile.write('%s\t' %q)
						thefile.write('%s\t' %w)
						thefile.write('%s\t' %e)
						thefile.write('%s\t' %r)
						thefile.write('%s\t' %t)
						thefile.write('%s\n' %y)
					
				self.emit(SIGNAL('update_fwhm(PyQt_PyObject,PyQt_PyObject)'),tals,fwhm)
				print "FWHM:", abs(r1-r2), "m"
				
				gauss_pos = numpy.linspace(min(pos_y),max(pos_y),5*len(pos_y))
				gauss_volts = self.gauss(gauss_pos,p1)
				self.emit(SIGNAL('plot_gaussian(PyQt_PyObject)'),[pos_y,voltages,'x',save_x[-1],gauss_pos,gauss_volts,[r1,r2]])
				
				if len(tals)>1:
					coef = self.fit_to_atten(S,save_Umax)
					a2.extend([ 4.343*coef[0]/100 ])
					self.emit(SIGNAL('update_slope(PyQt_PyObject,PyQt_PyObject)'),tals[1:],a2)
				
				if self.smart_scan=="yes":
					y_array=y_array+(ind_max-len(y_array)/2)*(y_array[1]-y_array[0])
					
		elif self.scan_mode=='xsnake':
			
			turn=-1
			time_start=time.time()
			for j,tal_outer in zip(y_array,range(len(y_array))):
				self.it6d.move_abs('y',j)
				j_ = self.it6d.get_positions('y')
				self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'),1e-6*int(i_),1e-7*int(j_))
				turn=turn*-1
				voltages=[]
				pos_x=[]
				for i in x_array[::turn]:
					if self.end_flag==True:
						break
					# move the microsteppers to the calculated positions
					self.it6d.move_abs('x',i)
					i_ = self.it6d.get_positions('x')
					self.emit(SIGNAL('update_pos_lcd(PyQt_PyObject,PyQt_PyObject)'),1e-6*int(i_),1e-7*int(j_))
					time_now=time.time()
					# update voltage readouts during dwell time
					while (time.time()-time_now)<self.dwell_time:
						outputcalib=self.sr810.return_X()
						time_elap=time.time()-time_start
						self.emit(SIGNAL('make_update2(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),time_elap,1e-6*int(i_),outputcalib)
					self.emit(SIGNAL('update_color_map(PyQt_PyObject)'),outputcalib)
					# get the last voltage value and save to a file
					with open(data_file, 'a') as thefile:
						thefile.write('%s\t\t' %(1e-6*int(i_)))
						thefile.write('%s\t\t' %(1e-7*int(j_)))
						thefile.write('%s\n' %(outputcalib))
					self.emit(SIGNAL('make_update4(PyQt_PyObject,PyQt_PyObject)'),time_elap,outputcalib)
					print 'X_abs:',int(i_), ', Y_abs:',int(j_), ', Vlockin:',outputcalib
					# calculate spine positions along the x axis
					pos_x.extend([ numpy.round(1e-6*int(i_),6) ])
					voltages.extend([ outputcalib ])
				
				if self.end_flag==True:
					break
				ind_max=numpy.argmax(voltages)
				
				save_x.extend([ pos_x[ind_max] ])
				save_y.extend([ numpy.round(1e-7*int(j_),7) ])
				save_Umax.extend([ voltages[ind_max] ])
				
				S = self.update_graphs(save_x,save_y,save_Umax,tal_outer)
				p1,r1,r2 = self.fit_to_gauss(numpy.array(pos_x),numpy.array(voltages))
				
				tals.extend([ tal_outer ])
				fwhm.extend([ abs(r1-r2) ])
				
				with open(data_file_spine, 'a') as thefile:
					for q,w,e,r,t,y in zip(tals,S,save_x,save_y,save_Umax,fwhm):
						thefile.write('%s\t' %q)
						thefile.write('%s\t' %w)
						thefile.write('%s\t' %e)
						thefile.write('%s\t' %r)
						thefile.write('%s\t' %t)
						thefile.write('%s\n' %y)
				
				self.emit(SIGNAL('update_fwhm(PyQt_PyObject,PyQt_PyObject)'),tals,fwhm)
				print "FWHM:", abs(r1-r2), "m"
				
				gauss_pos = numpy.linspace(min(pos_x),max(pos_x),5*len(pos_x))
				gauss_volts = self.gauss(gauss_pos,p1)
				self.emit(SIGNAL('plot_gaussian(PyQt_PyObject)'),[pos_x,voltages,'y',save_y[-1],gauss_pos,gauss_volts,[r1,r2]])
				
				if len(tals)>1:
					coef = self.fit_to_atten(S,save_Umax)
					a2.extend([ 4.343*coef[0]/100 ])
					self.emit(SIGNAL('update_slope(PyQt_PyObject,PyQt_PyObject)'),tals[1:],a2)
				
				if self.smart_scan=="yes":
					x_array=x_array+(ind_max-len(x_array)/2)*(x_array[1]-x_array[0])*turn
					
		elif self.scan_mode=='ysnake':
			
			turn=-1
			time_start=time.time()
			for i,tal_outer in zip(x_array,range(len(x_array))):
				self.it6d.move_abs('x',i)
				i_ = self.it6d.get_positions('x')
				self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'),1e-6*int(i_),1e-7*int(j_))
				turn=turn*-1
				voltages=[]
				pos_y=[]
				for j in y_array[::turn]:
					if self.end_flag==True:
						break
					# move the microsteppers to the calculated positions
					self.it6d.move_abs('y',j)
					j_ = self.it6d.get_positions('y')
					self.emit(SIGNAL('update_pos_lcd(PyQt_PyObject,PyQt_PyObject)'),1e-6*int(i_),1e-7*int(j_))
					time_now=time.time()
					# update voltage readouts during dwell time
					while (time.time()-time_now)<self.dwell_time:
						outputcalib=self.sr810.return_X()
						time_elap=time.time()-time_start
						self.emit(SIGNAL('make_update2(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),time_elap,1e-7*int(j_),outputcalib)
					self.emit(SIGNAL('update_color_map(PyQt_PyObject)'),outputcalib)
					# get the last voltage value and save to a file
					with open(data_file, 'a') as thefile:
						thefile.write('%s\t\t' %(1e-6*int(i_)))
						thefile.write('%s\t\t' %(1e-7*int(j_)))
						thefile.write('%s\n' %(outputcalib))
					self.emit(SIGNAL('make_update4(PyQt_PyObject,PyQt_PyObject)'),time_elap,outputcalib)
					print 'X_abs:',int(i_),', Y_abs:',int(j_),', Vlockin:',outputcalib
					# calculate spine positions along the y axis
					pos_y.extend([ numpy.round(1e-7*int(j_),7) ])
					voltages.extend([ outputcalib ])
				
				if self.end_flag==True:
					break
				ind_max=numpy.argmax(voltages)
				
				save_x.extend([ numpy.round(1e-6*int(i_),6) ])
				save_y.extend([ pos_y[ind_max] ])
				save_Umax.extend([ voltages[ind_max] ])
					
				S = self.update_graphs(save_x,save_y,save_Umax,tal_outer)
				p1,r1,r2 = self.fit_to_gauss(numpy.array(pos_y),numpy.array(voltages))
				
				tals.extend([ tal_outer ])
				fwhm.extend([ abs(r1-r2) ])
				
				with open(data_file_spine, 'a') as thefile:
					for q,w,e,r,t,y in zip(tals,S,save_x,save_y,save_Umax,fwhm):
						thefile.write('%s\t' %q)
						thefile.write('%s\t' %w)
						thefile.write('%s\t' %e)
						thefile.write('%s\t' %r)
						thefile.write('%s\t' %t)
						thefile.write('%s\n' %y)
				
				self.emit(SIGNAL('update_fwhm(PyQt_PyObject,PyQt_PyObject)'),tals,fwhm)
				print "FWHM:", abs(r1-r2), "m"
				
				gauss_pos = numpy.linspace(min(pos_y),max(pos_y),5*len(pos_y))
				gauss_volts = self.gauss(gauss_pos,p1)
				self.emit(SIGNAL('plot_gaussian(PyQt_PyObject)'),[pos_y,voltages,'x',save_x[-1],gauss_pos,gauss_volts,[r1,r2]])
				
				if len(tals)>1:
					coef = self.fit_to_atten(S,save_Umax)
					a2.extend([ 4.343*coef[0]/100 ])
					self.emit(SIGNAL('update_slope(PyQt_PyObject,PyQt_PyObject)'),tals[1:],a2)
				
				if self.smart_scan=="yes":
					y_array=y_array+(ind_max-len(y_array)/2)*(y_array[1]-y_array[0])*turn
					
		else:
			pass
		
		if tal_outer>1:
			# plot the data as a contour plot
			time.sleep(1)
			self.emit(SIGNAL('make_3Dplot()'))
			
			
	def def_xscan(self):
		
		data_file=''.join([self.data_file,".txt"])
		j_ = self.it6d.get_positions('y')

		with open(data_file, 'w') as thefile:
			thefile.write("Your comment line - do NOT delete this line\n") 
			thefile.write("X-pos [m], Y-pos [m], Voltage [V]\n")
			
		time_start=time.time() 
		voltages=[]
		pos_x=[]
		for i in self.xscan:
			if self.end_flag==True:
				break
			self.it6d.move_abs('x',i)
			i_ = self.it6d.get_positions('x')
			self.emit(SIGNAL('update_pos_lcd(PyQt_PyObject,PyQt_PyObject)'),1e-6*int(i_),1e-7*int(j_))
			time_now=time.time()
			# update voltage readouts during dwell time
			while (time.time()-time_now)<self.dwell_time:
				outputcalib=self.sr810.return_X()
				time_elap=time.time()-time_start
				self.emit(SIGNAL('make_update2(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),time_elap,1e-6*int(i_),outputcalib)
			self.emit(SIGNAL('update_color_map(PyQt_PyObject)'),outputcalib)
			# get the last voltage value and save to a file
			with open(data_file, 'a') as thefile:
				thefile.write('%s\t\t' %(1e-6*int(i_)))
				thefile.write('%s\t\t' %(1e-7*int(j_)))
				thefile.write('%s\n' %(outputcalib))
			self.emit(SIGNAL('make_update4(PyQt_PyObject,PyQt_PyObject)'),time_elap,outputcalib)
			#self.emit(SIGNAL('make_update3(PyQt_PyObject,PyQt_PyObject)'),time_elap,1e-6*int(i_))
			print 'X_abs:',int(i_),', Y_abs:',int(j_),', Vlockin:',outputcalib
			pos_x.extend([ numpy.round(1e-6*int(i_),6) ])
			voltages.extend([ outputcalib ])
			
		ind_max=numpy.argmax(voltages)
		
		self.update_graphs([pos_x[ind_max]], [numpy.round(1e-7*int(j_),7)], None, None)
		p1,r1,r2 = self.fit_to_gauss(numpy.array(pos_x),numpy.array(voltages))
		
		self.emit(SIGNAL('update_fwhm(PyQt_PyObject,PyQt_PyObject)'),[0],[abs(r1-r2)])
		print "FWHM:", abs(r1-r2), "m"
		
		gauss_pos = numpy.linspace(min(pos_x),max(pos_x),5*len(pos_x))
		gauss_volts = self.gauss(gauss_pos,p1)
		self.emit(SIGNAL('plot_gaussian(PyQt_PyObject)'),[pos_x,voltages,'y',1e-7*int(j_),gauss_pos,gauss_volts,[r1,r2]])
		
		
	def def_yscan(self):
		
		data_file=''.join([self.data_file,".txt"])
		i_ = self.it6d.get_positions('x')

		with open(data_file, 'w') as thefile:
		  thefile.write("Your comment line - do NOT delete this line\n") 
		  thefile.write("X-pos [m], Y-pos [m], Voltage [V]\n")

		time_start=time.time()
		voltages=[]
		pos_y=[]
		for j in self.yscan:
			if self.end_flag==True:
				break
			self.it6d.move_abs('y',j)
			j_ = self.it6d.get_positions('y')
			self.emit(SIGNAL('update_pos_lcd(PyQt_PyObject,PyQt_PyObject)'),1e-6*int(i_),1e-7*int(j_))
			time_now=time.time()
			# update voltage readouts during dwell time
			while (time.time()-time_now)<self.dwell_time:
				outputcalib=self.sr810.return_X()
				time_elap=time.time()-time_start
				self.emit(SIGNAL('make_update2(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),time_elap,1e-7*int(j_),outputcalib)
			self.emit(SIGNAL('update_color_map(PyQt_PyObject)'),outputcalib)
			# get the last voltage value and save to a file
			with open(data_file, 'a') as thefile:
				thefile.write('%s\t\t' %(1e-6*int(i_)))
				thefile.write('%s\t\t' %(1e-7*int(j_)))
				thefile.write('%s\n' %(outputcalib))
			self.emit(SIGNAL('make_update4(PyQt_PyObject,PyQt_PyObject)'),time_elap,outputcalib)
			#self.emit(SIGNAL('make_update3(PyQt_PyObject,PyQt_PyObject)'),time_elap,1e-7*int(j_))
			print 'X_abs:',int(i_),', Y_abs:',int(j_),', Vlockin:',outputcalib
			pos_y.extend([ numpy.round(1e-7*int(j_),7) ])
			voltages.extend([ outputcalib ])
			
		ind_max=numpy.argmax(voltages)
		
		self.update_graphs([numpy.round(1e-6*int(i_),6)], [pos_y[ind_max]], None, None)
		p1,r1,r2 = self.fit_to_gauss(numpy.array(pos_y),numpy.array(voltages))
		
		self.emit(SIGNAL('update_fwhm(PyQt_PyObject,PyQt_PyObject)'),[0],[abs(r1-r2)])
		print "FWHM:", abs(r1-r2), "m"
		
		gauss_pos = numpy.linspace(min(pos_y),max(pos_y),5*len(pos_y))
		gauss_volts = self.gauss(gauss_pos,p1)
		self.emit(SIGNAL('plot_gaussian(PyQt_PyObject)'),[pos_y,voltages,'x',1e-6*int(i_),gauss_pos,gauss_volts,[r1,r2]])
		
		
	def move_rel(self):

		if self.end_flag==False:
			self.it6d.move_rel('x',self.xscan)
			i_,j_ = self.it6d.get_positions()
			self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'),1e-6*int(i_),1e-7*int(j_))
			
		if self.end_flag==False:
			self.it6d.move_rel('y',self.yscan)
			i_,j_ = self.it6d.get_positions()
			self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'),1e-6*int(i_),1e-7*int(j_))
			
	def move_abs(self):

		if self.end_flag==False:
			self.it6d.move_abs('x',self.xscan)
			i_,j_ = self.it6d.get_positions()
			self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'),1e-6*int(i_),1e-7*int(j_))
			
		if self.end_flag==False:
			self.it6d.move_abs('y',self.yscan)
			i_,j_ = self.it6d.get_positions()
			self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'),1e-6*int(i_),1e-7*int(j_))
			
	def reset(self):
		
		self.it6d.reset(self.reset_mode)
		i_,j_ = self.it6d.get_positions()
		self.emit(SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'),1e-6*int(i_),1e-7*int(j_))









class Email_dialog(QtGui.QDialog):

	def __init__(self, lcd, parent=None):
		QtGui.QDialog.__init__(self, parent)
		
		# constants
		self.emailrec_str = config_IT6D_CA2.emailrec
		self.emailset_str = config_IT6D_CA2.emailset
		
		self.lcd = lcd
		
		self.setupUi()

	def setupUi(self):
		
		grid_0 = QtGui.QGridLayout()
		
		self.lb4 = QtGui.QLabel("Active gmail account:",self)
		self.lb5 = QtGui.QLabel(self.emailset_str[0],self)
		self.lb5.setStyleSheet("color: magenta")
		grid_0.addWidget(self.lb4,0,0)
		grid_0.addWidget(self.lb5,0,1)
		
		self.btnNewGmail = QtGui.QPushButton("Register account",self)
		self.btnNewGmail.clicked.connect(self.btn_newgmail)
		self.btnNewGmail.setEnabled(False)
		grid_0.addWidget(self.btnNewGmail,1,0)
		
		grid_2 = QtGui.QGridLayout()
		self.le2 = QtGui.QLineEdit("username",self)
		self.le2.setFixedWidth(70)
		self.le2.textChanged.connect(self.on_text_changed2)
		self.le3 = QtGui.QLineEdit("password",self)
		self.le3.setFixedWidth(70)
		self.le3.setEchoMode(QtGui.QLineEdit.Password)
		self.le3.textChanged.connect(self.on_text_changed2)
		grid_2.addWidget(self.le2,0,0)
		grid_2.addWidget(self.le3,0,1)
		grid_0.addLayout(grid_2,1,1)
		
		self.lb1 = QtGui.QLabel("Receiver(s) comma(,) separated:",self)
		self.le1 = QtGui.QLineEdit()
		self.le1.setText(','.join([i for i in self.emailrec_str]))
		self.le1.textChanged.connect(self.on_text_changed)
		grid_0.addWidget(self.lb1,2,0)
		grid_0.addWidget(self.le1,2,1)
		
		self.lb2 = QtGui.QLabel("Send notification when scan is done?",self)
		self.cb2 = QtGui.QComboBox(self)
		mylist=["yes","no"]
		self.cb2.addItems(mylist)
		self.cb2.setCurrentIndex(mylist.index(self.emailset_str[1]))
		grid_0.addWidget(self.lb2,3,0)
		grid_0.addWidget(self.cb2,3,1)
		
		self.lb3 = QtGui.QLabel("Send data when scan is done?",self)
		self.cb3 = QtGui.QComboBox(self)
		self.cb3.addItems(mylist)
		self.cb3.setCurrentIndex(mylist.index(self.emailset_str[2]))
		grid_0.addWidget(self.lb3,4,0)
		grid_0.addWidget(self.cb3,4,1)
		
		self.btnSave = QtGui.QPushButton("Changes saved",self)
		self.btnSave.clicked.connect(self.btn_accepted)
		self.btnSave.setEnabled(False)
		
		grid_1 = QtGui.QGridLayout()
		grid_1.addWidget(self.btnSave,0,0)
		
		self.cb2.activated[str].connect(self.onActivated2)
		self.cb3.activated[str].connect(self.onActivated3)
		
		v0 = QtGui.QVBoxLayout()
		v0.addLayout(grid_0)
		v0.addLayout(grid_1)
		
		self.setLayout(v0)
		self.setWindowTitle("E-mail settings")
		
	def onActivated2(self, text):
		
		self.emailset_str[1] = str(text)
		self.btnSave.setText("*Save changes*")
		self.btnSave.setEnabled(True)
	
	def onActivated3(self, text):
		
		self.emailset_str[2] = str(text)
		self.btnSave.setText("*Save changes*")
		self.btnSave.setEnabled(True)
	
	def on_text_changed(self):
		
		self.emailrec_str = str(self.le1.text()).split(',')
		self.emailrec_str = [emails.strip() for emails in self.emailrec_str]
		
		for emails in self.emailrec_str:
			if not re.match(r"[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$", emails):
				self.btnSave.setText("*Invalid e-mail(s)*")
				self.btnSave.setEnabled(False)
			else:
				self.btnSave.setText("*Save changes*")
				self.btnSave.setEnabled(True)
	
	def on_text_changed2(self):
		
		if str(self.le2.text())!="username" and len(str(self.le2.text()))>0:
			if str(self.le3.text())!="password" and len(str(self.le3.text()))>0:
				self.btnNewGmail.setText("Register account")
				self.btnNewGmail.setEnabled(True)
			else:
				self.btnNewGmail.setText("*Invalid account*")
				self.btnNewGmail.setEnabled(False)
		else:
			self.btnNewGmail.setText("*Invalid account*")
			self.btnNewGmail.setEnabled(False)
	
	def btn_newgmail(self):
		
		yagmail.register(''.join([str(self.le2.text()),'@gmail.com']),str(self.le3.text()))
		self.btnNewGmail.setText("Account registered")
		self.btnNewGmail.setEnabled(False)
		
		self.emailset_str[0]=str(self.le2.text())
		self.lb5.setText(self.emailset_str[0])
		self.btnSave.setText("*Save changes*")
		self.btnSave.setEnabled(True)
	
	def btn_accepted(self):
		
		self.set_save()
		
		self.btnSave.setText("Changes saved")
		self.btnSave.setEnabled(False)
		
	def set_save(self):
		
		self.emailrec_str = str(self.le1.text()).split(',')
		timetrace=time.strftime("%y%m%d-%H%M")
		self.lcd.display(timetrace)
		
		self.replace_line("config_IT6D_CA2.py",14,''.join(["timetrace=\"",timetrace,"\"\n"]))
		self.replace_line("config_IT6D_CA2.py",17,''.join(["emailrec=[\"",'\",\"'.join([i for i in self.emailrec_str]),"\"]\n"]))
		self.replace_line("config_IT6D_CA2.py",18,''.join(["emailset=[\"",'\",\"'.join([i for i in self.emailset_str]),"\"]\n"]))
		
		imp.reload(config_IT6D_CA2)
	
	def replace_line(self,file_name, line_num, text):
		
		lines = open(file_name, 'r').readlines()
		lines[line_num] = text
		out = open(file_name, 'w')
		out.writelines(lines)
		out.close()
		
		
		
		
class Send_email_dialog(QtGui.QDialog):

	def __init__(self, parent=None):
		QtGui.QDialog.__init__(self, parent)
		
		# constants
		self.emailset_str = config_IT6D_CA2.emailset
		self.emailrec_str = config_IT6D_CA2.emailrec
		self.folder_str = config_IT6D_CA2.folder
		self.all_files=["The attached files are some chosen data sent from the microstepper computer."]

		self.setupUi()

	def setupUi(self):
		
		self.lb0 = QtGui.QLabel("Receiver(s) comma(,) separated:",self)
		self.le1 = QtGui.QLineEdit()
		self.le1.setText(','.join([i for i in self.emailrec_str]))
		self.le1.textChanged.connect(self.on_text_changed)
		
		self.btnSave = QtGui.QPushButton("Receivers saved",self)
		self.btnSave.clicked.connect(self.btn_save)
		self.btnSave.setEnabled(False)
		
		self.btnSend = QtGui.QPushButton("Send e-mail",self)
		self.btnSend.clicked.connect(self.btn_send_email)
		self.btnSend.setEnabled(False)
		
		self.btnBrowse = QtGui.QPushButton("Pick files",self)
		self.btnBrowse.clicked.connect(self.btn_browse_files)
		
		self.btnClear = QtGui.QPushButton("Clear list",self)
		self.btnClear.clicked.connect(self.btn_clear_list)
		self.btnClear.setEnabled(False)
		
		# set layout
		
		grid_0 = QtGui.QGridLayout()
		grid_0.addWidget(self.lb0,0,0)
		grid_0.addWidget(self.le1,1,0)
		grid_0.addWidget(self.btnSave,2,0)
		
		grid_1 = QtGui.QGridLayout()
		grid_1.addWidget(self.btnSend,0,0)
		grid_1.addWidget(self.btnBrowse,0,1)
		grid_1.addWidget(self.btnClear,0,2)
		
		grid_2 = QtGui.QGridLayout()
		self.lb1 = QtGui.QLabel("No files selected!",self)
		grid_2.addWidget(self.lb1,0,0)
		
		v0 = QtGui.QVBoxLayout()
		v0.addLayout(grid_0)
		v0.addLayout(grid_1)
		v0.addLayout(grid_2)
		
		self.setLayout(v0)
		self.setWindowTitle("E-mail data")
		
		# re-adjust/minimize the size of the e-mail dialog
		# depending on the number of attachments
		v0.setSizeConstraint(v0.SetFixedSize)
		
	def btn_send_email(self):
		
		try:
			self.yag = yagmail.SMTP(self.emailset_str[0])
			self.yag.send(self.emailrec_str, "File(s) sent from the microstepper computer", contents=self.all_files)
			QtGui.QMessageBox.warning(self, 'Message', ''.join(["E-mail is sent to ", ' and '.join([i for i in self.emailrec_str]) ," including ",str(len(self.all_files[1:]))," attachment(s)!"]))
		except Exception as e:
			QtGui.QMessageBox.warning(self, 'Message',''.join(["Could not load the gmail account ",self.emailset_str[0],"! Try following steps:\n1. Check internet connection. Only wired internet will work, ie. no wireless.\n2. Check the account username and password.\n3. Make sure that the account accepts less secure apps."]))
			

	def btn_clear_list(self):
	
		self.all_files=["The attached files are some chosen data sent from the microstepper computer."]
		self.lb1.setText("No files selected!")

		self.btnSend.setEnabled(False)
		self.btnClear.setEnabled(False)
	
	def btn_browse_files(self):
	
		for path in QtGui.QFileDialog.getOpenFileNames(self, 'Open file',''.join([self.folder_str,'/'])):
			self.all_files.extend([str(path)])
		
		for emails in self.emailrec_str:
			if not re.match(r"[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$", emails):
				self.btnSend.setEnabled(False)
			else:
				if len(self.all_files)==1:
					self.btnSend.setEnabled(False)
				else:
					self.btnSend.setEnabled(True)
					
		if len(self.all_files)==1:
			self.lb1.setText("No files selected!")
			self.btnClear.setEnabled(False)
		else:
			self.print_files = "Selected files:\n"
			self.tal = 0
			for paths in self.all_files[1:]:
				head, tail = os.path.split(paths)
				self.tal +=1
				self.print_files += ''.join([str(self.tal),': ',tail, "\n"])
				
			self.lb1.setText(self.print_files)
			self.btnClear.setEnabled(True)
			
	def on_text_changed(self):
		
		self.emailrec_str = str(self.le1.text()).split(',')
		self.emailrec_str = [emails.strip() for emails in self.emailrec_str]
		
		for emails in self.emailrec_str:
			if not re.match(r"[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$", emails):
				self.btnSend.setEnabled(False)
				self.btnSave.setText("*Invalid e-mail(s)*")
				self.btnSave.setEnabled(False)
			else:
				if len(self.all_files)==1:
					self.btnSend.setEnabled(False)
				else:
					self.btnSend.setEnabled(True)
				self.btnSave.setText("*Save receivers*")
				self.btnSave.setEnabled(True)
				
	def btn_save(self):
		
		self.btnSave.setText("Receivers saved")
		self.btnSave.setEnabled(False)
		
		self.replace_line("config_IT6D_CA2.py",12,''.join(["emailrec=[\"",'\",\"'.join([i for i in self.emailrec_str]),"\"]\n"]) )
		imp.reload(config_IT6D_CA2)
		
	def replace_line(self,file_name, line_num, text):
		
		lines = open(file_name, 'r').readlines()
		lines[line_num] = text
		out = open(file_name, 'w')
		out.writelines(lines)
		out.close()
		
	def closeEvent(self,event):
	
		event.accept()







class Run_IT6D_CA2(QtGui.QWidget):

	def __init__(self):
		super(Run_IT6D_CA2, self).__init__()
		
		# Initial read of the config file
		self.op_mode = config_IT6D_CA2.op_mode
		self.scan_mode = config_IT6D_CA2.scan_mode
		self.folder_str=config_IT6D_CA2.folder
		self.filename_str=config_IT6D_CA2.filename
		self.xscan = config_IT6D_CA2.x_scan_mm
		self.yscan = config_IT6D_CA2.y_scan_mm
		self.absrel_mm = config_IT6D_CA2.absrel_mm
		self.dwell_time = config_IT6D_CA2.wait_time
		self.reset_mode = config_IT6D_CA2.reset_mode
		self.xy_limiter_mm = config_IT6D_CA2.xy_limiter_mm
		self.smart_scan = config_IT6D_CA2.smart_scan
		self.lockin_volt = config_IT6D_CA2.lockin_volt
		self.lockin_freq = config_IT6D_CA2.lockin_freq
		self.schroll_pts = config_IT6D_CA2.schroll_pts
		self.timetrace=config_IT6D_CA2.timetrace
		self.it6d_ca2port_str=config_IT6D_CA2.it6d_ca2port
		self.sr810port_str=config_IT6D_CA2.sr810port
		
		# Enable antialiasing for prettier plots		
		pg.setConfigOptions(antialias=True)
		self.initUI()
			
	def initUI(self):
		
		################### MENU BARS START ##################
		
		MyBar = QtGui.QMenuBar(self)
		fileMenu = MyBar.addMenu("File")
		fileSavePlt = fileMenu.addAction("Save plots")
		fileSavePlt.triggered.connect(self.set_save_plots)
		fileSavePlt.setShortcut('Ctrl+P')
		fileSaveSet = fileMenu.addAction("Save settings")        
		fileSaveSet.triggered.connect(self.set_save) # triggers closeEvent()
		fileSaveSet.setShortcut('Ctrl+S')
		self.fileClose = fileMenu.addAction("Close")        
		self.fileClose.triggered.connect(self.close) # triggers closeEvent()
		self.fileClose.setShortcut('Ctrl+X')
		
		modeMenu = MyBar.addMenu("Mode")
		self.conMode = modeMenu.addAction("Connect to serial")
		self.conMode.triggered.connect(self.set_connect)
		self.disconMode = modeMenu.addAction("Disconnect from serial")
		self.disconMode.triggered.connect(self.set_disconnect)
		
		gpibMenu = MyBar.addMenu("Ports")
		self.gpibIT6D_CA2 = gpibMenu.addAction("IT6D CA2")
		self.gpibIT6D_CA2.triggered.connect(self.IT6D_CA2Dialog)
		self.serSR810 = gpibMenu.addAction("SR810")
		self.serSR810.triggered.connect(self.SR810Dialog)
		
		self.emailMenu = MyBar.addMenu("E-mail")
		self.emailSet = self.emailMenu.addAction("E-mail settings")
		self.emailSet.triggered.connect(self.email_set_dialog)
		self.emailData = self.emailMenu.addAction("E-mail data")
		self.emailData.triggered.connect(self.email_data_dialog)
		
		################### MENU BARS END ##################

		lbl1 = QtGui.QLabel("OPERATION mode settings:", self)
		lbl1.setStyleSheet("color: blue")	
		
		opmode_lbl = QtGui.QLabel("Operation", self)
		self.combo4 = QtGui.QComboBox(self)
		mylist4=["move abs","move rel","xyscan","xscan","yscan","reset"]
		self.combo4.addItems(mylist4)
		self.combo4.setCurrentIndex(mylist4.index(self.op_mode))
		
		scanmode_lbl = QtGui.QLabel("Scan", self)
		self.combo5 = QtGui.QComboBox(self)
		mylist5=["xsnake","ysnake","xwise","ywise"]
		self.combo5.addItems(mylist5)
		self.combo5.setCurrentIndex(mylist5.index(self.scan_mode))
		
		resetmode_lbl = QtGui.QLabel("Reset", self)
		self.combo6 = QtGui.QComboBox(self)
		mylist6=["x","y","xy"]
		self.combo6.addItems(mylist6)
		self.combo6.setCurrentIndex(mylist6.index(self.reset_mode))
		
		dwelltime_lbl = QtGui.QLabel("Dwell [s]",self)
		self.dwelltimeEdit = QtGui.QLineEdit(str(self.dwell_time),self)
		xy_limiter_lbl = QtGui.QLabel("XY-limits [mm]",self)
		self.xy_limiterEdit = [QtGui.QLineEdit("",self) for tal in range(2)]
		for i in range(2):
			self.xy_limiterEdit[i].setText(str(self.xy_limiter_mm[i]))
			self.xy_limiterEdit[i].setFixedWidth(40)
		
		smartscan_lbl = QtGui.QLabel("Smart scan",self)
		self.combo7 = QtGui.QComboBox(self)
		mylist7=["yes","no"]
		self.combo7.addItems(mylist7)
		self.combo7.setCurrentIndex(mylist7.index(self.smart_scan))
		#####################################################
			
		#lockin_lbl = QtGui.QLabel("SR810 lock-in oscillator settings:", self)
		#lockin_lbl.setStyleSheet("color: blue")	
		
		self.amp_lbl = QtGui.QLabel(''.join(["Osc. Vpk-pk (",str(self.lockin_volt),") [V]"]), self)
		self.sld_amp = QtGui.QSlider(QtCore.Qt.Horizontal,self)
		#self.sld_amp.setFocusPolicy(QtCore.Qt.NoFocus)
		self.sld_amp.tickPosition()
		self.sld_amp.setRange(1,400)
		self.sld_amp.setSingleStep(1)
		self.sld_amp.setPageStep(10)
		self.sld_amp.setValue(int(1000*self.lockin_volt))
		
		self.freq_lbl = QtGui.QLabel(''.join(["Osc. freq (",str(self.lockin_freq),") [Hz]"]), self)
		self.sld_freq = QtGui.QSlider(QtCore.Qt.Horizontal,self)
		#self.sld_freq.setFocusPolicy(QtCore.Qt.NoFocus)
		self.sld_freq.tickPosition()
		self.sld_freq.setRange(1,5000)
		self.sld_freq.setSingleStep(1)
		self.sld_freq.setPageStep(10)
		self.sld_freq.setValue(self.lockin_freq)
		
		#self.freqEdit=QtGui.QLineEdit("",self)
		#self.freqEdit.setText(str(self.lockin_freq))
		#self.freqEdit.setFixedWidth(60)
		#self.freqEdit.setEnabled(False)
		
		#rate_lbl = QtGui.QLabel("Sample rate[Hz]", self)
		#self.combo8 = QtGui.QComboBox(self)
		#self.mylist8=["0.0625","0.125","0.25","0.5","1.0","2.0","4.0","8.0","16.0","32.0","64.0","128.0","256.0","512.0"]
		#self.combo8.addItems(self.mylist8)
		#self.combo8.setCurrentIndex(self.mylist8.index(str(self.sample_rate)))
			
		#####################################################
		
		lbl7 = QtGui.QLabel("SCAN or MOVE axis[mm]:", self)
		lbl7.setStyleSheet("color: blue")	
		
		start_lbl = QtGui.QLabel("Start",self)
		stop_lbl = QtGui.QLabel("Stop",self)
		step_lbl = QtGui.QLabel("Step",self)
		self.absrel_lbl = QtGui.QLabel("Abs/Rel",self)
		xy_lbl = [QtGui.QLabel(i,self) for i in ["X:","Y:"]]
		[xy_lbl[i].setFixedWidth(15) for i in range(2)]
		self.xscanEdit = [QtGui.QLineEdit("",self) for tal in range(3)] 
		self.yscanEdit = [QtGui.QLineEdit("",self) for tal in range(3)]
		self.absrelEdit = [QtGui.QLineEdit("",self) for tal in range(2)]
		# set initial values into the fields
		for i in range(3):
			self.xscanEdit[i].setText(str(self.xscan[i]))
			self.yscanEdit[i].setText(str(self.yscan[i]))
			self.xscanEdit[i].setFixedWidth(53)
			self.yscanEdit[i].setFixedWidth(53)
		for i in range(2):
			self.absrelEdit[i].setText(str(self.absrel_mm[i]))
			self.absrelEdit[i].setFixedWidth(50)
			
		actual_lbl = QtGui.QLabel("Actual",self)
		self.lcd_actual = [QtGui.QLCDNumber(self) for i in range(2)]
		for i in range(2):
			self.lcd_actual[i].setStyleSheet("color: blue")
			#self.lcd_actual.setFixedHeight(60)
			self.lcd_actual[i].setSegmentStyle(QtGui.QLCDNumber.Flat)
			self.lcd_actual[i].setNumDigits(7)
			self.lcd_actual[i].display('-------')
		
		#####################################################
		
		lbl4 = QtGui.QLabel("STORE data with a timetrace:", self)
		lbl4.setStyleSheet("color: blue")
		
		filename = QtGui.QLabel("File name",self)
		foldername = QtGui.QLabel("Folder name",self)
		self.filenameEdit = QtGui.QLineEdit(str(self.filename_str),self)
		self.folderEdit = QtGui.QLineEdit(str(self.folder_str),self)
		self.filenameEdit.setFixedWidth(190)
		#self.folderEdit.setFixedWidth(150)
		
		#####################################################
		
		schroll_lbl = QtGui.QLabel("Schroll X-axis",self)
		self.combo2 = QtGui.QComboBox(self)
		mylist2=["200","500","1000","2000","5000","10000"]
		self.combo2.addItems(mylist2)
		# initial combo settings
		self.combo2.setCurrentIndex(mylist2.index(str(self.schroll_pts)))
		#self.combo2.setFixedWidth(90)
		
		#####################################################
		
		lbl5 = QtGui.QLabel("EXECUTE operation:", self)
		lbl5.setStyleSheet("color: blue")
		
		self.runButton = QtGui.QPushButton("Run",self)
		self.cancelButton = QtGui.QPushButton("STOP",self)
		
		#####################################################
		
		self.lcd = QtGui.QLCDNumber(self)
		self.lcd.setStyleSheet("color: red")
		self.lcd.setFixedHeight(60)
		self.lcd.setSegmentStyle(QtGui.QLCDNumber.Flat)
		self.lcd.setNumDigits(11)
		self.lcd.display(self.timetrace)
			
		#####################################################
		#####################################################
		
		# Add all widgets		
		g1_0 = QtGui.QGridLayout()
		g1_0.addWidget(MyBar,0,0)
		g1_0.addWidget(lbl1,1,0)

		g1_1 = QtGui.QGridLayout()
		g1_1.addWidget(opmode_lbl,0,0)
		g1_1.addWidget(self.combo4,1,0)
		g1_1.addWidget(scanmode_lbl,0,1)
		g1_1.addWidget(self.combo5,1,1)
		g1_1.addWidget(resetmode_lbl,0,2)
		g1_1.addWidget(self.combo6,1,2)
		
		g1_2 = QtGui.QGridLayout()
		g1_2.addWidget(dwelltime_lbl,0,0)
		g1_2.addWidget(self.dwelltimeEdit,1,0)
		g1_2.addWidget(smartscan_lbl,0,1)
		g1_2.addWidget(self.combo7,1,1)
		g1_2.addWidget(schroll_lbl,0,2)
		g1_2.addWidget(self.combo2,1,2)
		
		g1_3 = QtGui.QGridLayout()
		g1_3.addWidget(xy_limiter_lbl,0,0)
		g1_4 = QtGui.QGridLayout()
		for tal in range(2):
			g1_4.addWidget(self.xy_limiterEdit[tal],0,tal)
		
		v1_ = QtGui.QVBoxLayout()
		v1_.addLayout(g1_3)
		v1_.addLayout(g1_4)
		
		h1_ = QtGui.QHBoxLayout()
		h1_.addLayout(g1_2)
		h1_.addLayout(v1_)
			
		v1 = QtGui.QVBoxLayout()
		v1.addLayout(g1_0)
		v1.addLayout(g1_1)
		v1.addLayout(h1_)
		
		#####################################################
		
		#g8_0 = QtGui.QGridLayout()
		#g8_0.addWidget(lockin_lbl,0,0)
		g8_1 = QtGui.QGridLayout()
		g8_1.addWidget(self.amp_lbl,0,0)
		g8_1.addWidget(self.sld_amp,1,0)
		g8_1.addWidget(self.freq_lbl,0,1)
		g8_1.addWidget(self.sld_freq,1,1)
		#g8_1.addWidget(rate_lbl,0,2)
		#g8_1.addWidget(self.freqEdit,1,2)
		v8 = QtGui.QVBoxLayout()
		#v8.addLayout(g8_0)
		v8.addLayout(g8_1)
		
		#####################################################
		
		g2_0 = QtGui.QGridLayout()
		g2_0.addWidget(lbl7,0,0)
		
		g2_1 = QtGui.QGridLayout()
		g2_1.addWidget(start_lbl,0,1)
		g2_1.addWidget(stop_lbl,0,2)
		g2_1.addWidget(step_lbl,0,3)
		g2_1.addWidget(self.absrel_lbl,0,4)
		g2_1.addWidget(actual_lbl,0,5)
		
		for tal in range(2):
			g2_1.addWidget(xy_lbl[tal],1+tal,0)
		for tal in range(3):
			g2_1.addWidget(self.xscanEdit[tal],1,1+tal)
			g2_1.addWidget(self.yscanEdit[tal],2,1+tal)
		for tal in range(2):
			g2_1.addWidget(self.absrelEdit[tal],1+tal,4)
		for tal in range(2):
			g2_1.addWidget(self.lcd_actual[tal],1+tal,5)
		
		v2 = QtGui.QVBoxLayout()
		v2.addLayout(g2_0)
		v2.addLayout(g2_1)
		
		#####################################################
		
		g3_0 = QtGui.QGridLayout()
		g3_0.addWidget(lbl4,0,0)
		
		g3_1 = QtGui.QGridLayout()
		g3_1.addWidget(filename,0,0)
		g3_1.addWidget(self.filenameEdit,1,0)
		g3_1.addWidget(foldername,0,1)
		g3_1.addWidget(self.folderEdit,1,1)
		
		g3_2 = QtGui.QGridLayout()
		g3_2.addWidget(self.lcd,0,0)
		
		v3 = QtGui.QVBoxLayout()
		v3.addLayout(g3_0)
		v3.addLayout(g3_1)
		v3.addLayout(g3_2)
		
		#####################################################
		
		g5_0 = QtGui.QGridLayout()
		g5_0.addWidget(lbl5,0,0)
		
		g5_1 = QtGui.QGridLayout()
		g5_1.addWidget(self.runButton,0,1)
		g5_1.addWidget(self.cancelButton,0,2)
		
		v5 = QtGui.QVBoxLayout()
		v5.addLayout(g5_0)
		v5.addLayout(g5_1)
		
		#####################################################
		
		# add ALL groups from v1 to v6 in one vertical group v7
		v7 = QtGui.QVBoxLayout()
		v7.addLayout(v1)
		v7.addLayout(v8)
		v7.addLayout(v2)
		v7.addLayout(v3)
		v7.addLayout(v5)
	
		#####################################################
		
		# set GRAPHS and TOOLBARS to a new vertical group vcan
		win2 = pg.GraphicsWindow()
		vcan0 = QtGui.QGridLayout()
		vcan0.addWidget(win2,0,0)
		
		# SET ALL HORIZONTAL COLUMNS TOGETHER
		hbox = QtGui.QHBoxLayout()
		hbox.addLayout(v7)
		hbox.addLayout(vcan0)
		
		
		vcan1 = QtGui.QGridLayout()
		self.pw3 = pg.PlotWidget()
		vcan1.addWidget(self.pw3,0,0)
		
		# SET VERTICAL COLUMNS TOGETHER TO FINAL LAYOUT
		vbox = QtGui.QVBoxLayout()
		vbox.addLayout(hbox)
		vbox.addLayout(vcan1)
		
		
		win = pg.GraphicsWindow()
		#win.resize(1000,600)
		vcan2 = QtGui.QGridLayout()
		vcan2.addWidget(win,0,0)
		
		# SET HORIZONTAL COLUMNS TOGETHER TO FINAL LAYOUT
		hbox1 = QtGui.QHBoxLayout()
		hbox1.addLayout(vbox)
		hbox1.addLayout(vcan2)
		
		self.setLayout(hbox1) 
		
		##############################################
		
		# INITIAL SETTINGS PLOT 1
		
		self.p0 = win2.addPlot()
		self.curve1 = self.p0.plot(pen='w', symbol='s', symbolPen='w', symbolBrush='b', symbolSize=4)
		self.curve2 = self.p0.plot(pen='k', symbol='s', symbolPen='k', symbolSize=6)
	
		self.p0.enableAutoRange()
		self.p0.setTitle(''.join(["2-D scan, Jet colormap"]))
		self.p0.setLabel('left', "Y", units='m', color='red')
		self.p0.setLabel('bottom', "X", units='m', color='red')
		
		win2.nextRow()
		
		self.p11 = win2.addPlot()
		self.curve11 = self.p11.plot(pen='y')
		self.curve12 = self.p11.plot(pen=None, symbol='s', symbolPen='m', symbolBrush='m', symbolSize=6)
		self.curve13 = self.p11.plot(pen={'color':'m','width':1}, symbol='o', symbolPen='w', symbolBrush='b', symbolSize=6)
		
		self.my_text = pg.TextItem("FWHM", anchor=(0.5,-0.75))
		self.my_text.setParentItem(self.curve13)
		self.my_arrow = pg.ArrowItem(angle=90)
		self.my_arrow.setParentItem(self.curve13)
		
		
		self.p11.enableAutoRange()
		self.p11.setTitle(''.join(["Latest gaussian fit"]), color='y')
		self.p11.setLabel('left', "U", units='V', color='yellow')
		self.p11.setLabel('bottom', "X or Y", units='m', color='yellow')
		
		
		# INITIAL SETTINGS PLOT 2
		p6 = win.addPlot()
		self.curve6=p6.plot(pen='w', symbol='o', symbolPen='w',symbolSize=8)
		p6.setTitle(''.join(["Mapping (X,Y) -> S"]))
		p6.setLabel('left', "U_max", units='V', color='white')
		p6.setLabel('bottom', "S", units='m', color='white')
		p6.setLogMode(y=True)
		p6.enableAutoRange()
		
		win.nextRow()
		
		# INITIAL SETTINGS PLOT 5
		p8 = win.addPlot()
		self.curve8=p8.plot(pen='r', symbol='o', symbolPen='w',symbolSize=8)
		self.curve7=p8.plot(pen=None, symbol='o', symbolPen=None, symbolBrush='y', symbolSize=8)
		p8.setTitle(''.join(["U_max positions"]))
		p8.setLabel('left', "Y", units='m', color='red')
		p8.setLabel('bottom', "X", units='m', color='red')
		p8.enableAutoRange()
		
		win.nextRow()
		
		# INITIAL SETTINGS PLOT 6
		p9 = win.addPlot()
		self.curve9=p9.plot(pen='m', symbol='d', symbolPen='m',symbolSize=8)
		p9.setTitle(''.join(["FWHM by spline"]))
		p9.setLabel('left', "FWHM", units='m', color='magenta')
		p9.setLabel('bottom', "Index of axis scanned", color='magenta')
		
		win.nextRow()
		
		# INITIAL SETTINGS PLOT 7
		p10 = win.addPlot()
		self.curve10=p10.plot(pen='y', symbol='d', symbolPen='y',symbolSize=8)
		p10.setTitle(''.join(["Attenuation slope a"]))
		p10.setLabel('left', "a", units='dB/cm', color='yellow')
		p10.setLabel('bottom', "Index of axis scanned", color='yellow')
		
		# INITIAL SETTINGS PLOT 3
		self.p1 = self.pw3.plotItem
		self.curve3=self.p1.plot(pen='w')
		self.curve4=self.p1.plot(pen='y')
		# create plot and add it to the figure
		self.p2 = pg.ViewBox()
		self.curve5=pg.PlotCurveItem(pen='r')
		self.p2.addItem(self.curve5)
		# connect respective axes to the plot 
		self.p1.scene().addItem(self.p2)
		self.p1.getAxis('right').linkToView(self.p2)
		self.p2.setXLink(self.p1)
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw3.setDownsampling(mode='peak')
		self.pw3.setClipToView(True)
		self.pw3.enableAutoRange()
		# Labels and titels are placed here since they change dynamically
		self.pw3.setTitle(''.join(["Voltage and position as function of time"]))
		self.pw3.setLabel('left', "Lock-in voltage", units='V', color='yellow')
		self.pw3.setLabel('right', "Scan axis", units='m', color='red')
		self.pw3.setLabel('bottom', "Elapsed time", units='s', color='white')
		'''
		# INITIAL SETTINGS PLOT 4
		self.pw4 = gl.GLViewWidget()
		self.pw4.opts['distance'] = 0.03
		self.pw4.setWindowTitle('Scatter plot of sweeped poins')
		
		#zx = gl.GLGridItem()
		#zx.rotate(90, 0, 1, 0) # zx-plane
		#zx.translate(-1, 0, 0)
		#zx.scale(0.1,0.1,0.1,local=True)
		#self.pw4.addItem(zx)
		
		zy = gl.GLGridItem()
		zy.rotate(90, 1, 0, 0) # zy-plane
		zy_spacing=1e-3 # Volts
		zy.translate(0, 0, 10*zy_spacing)
		zy.scale(zy_spacing,zy_spacing,zy_spacing,local=True)
		self.pw4.addItem(zy)
		
		xy = gl.GLGridItem()
		xy_spacing=1e-3 # Meters
		xy.translate(0, -10*xy_spacing, 0) # xy-plane
		xy.scale(xy_spacing,xy_spacing,xy_spacing,local=True)
		self.pw4.addItem(xy)
		## create a new AxisItem, linked to view
		#ax2 = gl.GLAxisItem()
		#ax2.setSize(x=10,y=10,z=10)
		#self.pw4.addItem(ax2)
		#ax2.setLabel('latitude', color='#0000ff')
		self.sp1 = gl.GLScatterPlotItem()
		'''
		# Initialize and set titles and axis names for both plots
		
		##############################################
		
		# reacts to drop-down menus
		self.combo2.activated[str].connect(self.onActivated2)
		self.combo4.activated[str].connect(self.onActivated4)
		self.combo5.activated[str].connect(self.onActivated5)
		self.combo6.activated[str].connect(self.onActivated6)
		self.combo7.activated[str].connect(self.onActivated7)
		self.sld_freq.valueChanged[int].connect(self.changeFreq)
		self.sld_amp.valueChanged[int].connect(self.changeAmp)
	
		# run the main script
		self.runButton.clicked.connect(self.set_run)
		
		# cancel the script run
		self.cancelButton.clicked.connect(self.set_cancel)
		
		self.clear_vars_graphs()
		self.disconMode.setEnabled(False)
		self.allFields(False)
		self.cancelButton.setEnabled(False)
		self.runButton.setEnabled(False)
		self.fileClose.setEnabled(True)
		
		self.setGeometry(10, 10, 1300, 1100)
		#self.move(0,0)
		self.setWindowTitle("IT6D CA2 Microstepper And SR810 Lock-In Data Acqusition")
		self.show()
	
	def update_lcd(self,i,j):
		# i and j are always in meters
		self.lcd_actual[0].display(str(i*1000)) # convert meters to mm
		self.lcd_actual[1].display(str(j*1000)) # convert meters to mm
	
	def update_pos_lcd(self,i,j):
		# i and j are always in meters
		self.acc_x_pos.extend([ i ])
		self.acc_y_pos.extend([ j ])
		self.lcd_actual[0].display(str(i*1000)) # convert meters to mm
		self.lcd_actual[1].display(str(j*1000)) # convert meters to mm
		
			
	def update_color_map(self,volt):
		
		self.all_volt_endpts.extend([volt])
		my_norm = mpl.colors.Normalize(vmin=min(self.all_volt_endpts), vmax=max(self.all_volt_endpts))
		m = cm.ScalarMappable(norm=my_norm, cmap=mpl.cm.jet)
		my_color = m.to_rgba(self.all_volt_endpts,bytes=True)
		
		colors_=[]
		for i in my_color:
			colors_.append(pg.mkBrush(tuple(i)))
		
		self.curve2.setData(self.acc_x_pos, self.acc_y_pos, symbolBrush=colors_)
		
		'''
		spots3 = []
		for i,j,k in zip(self.acc_x_pos,self.acc_y_pos,my_color):
			spots3.append({'pos': (i, j), 'brush':tuple(k)})
		self.curve2.addPoints(spots3)
		'''
		
	def set_connect(self):
		
		try:
			self.sr810 = SR810.SR810(self.sr810port_str)
		except Exception as e:
			QtGui.QMessageBox.warning(self, 'Message',"No response from SR810 serial port! Check the serial port name.")
			return None


		try:
			self.sr810.set_to_rs232()
			self.sr810.set_timeout(1)
			val=self.sr810.return_id()
			if val=="":
				self.sr810.close()
				QtGui.QMessageBox.warning(self, 'Message',"No response from SR810 lock-in amplifier! Is SR810 powered and connected to serial?")
				return None
		except Exception as e:
			self.sr810.close()
			QtGui.QMessageBox.warning(self, 'Message',"No response from SR810 lock-in amplifier! Is SR810 powered and connected to serial?")
			return None


		try:
			self.it6d = IT6D_CA2_gpib.IT6D_CA2(int(self.it6d_ca2port_str))
		except Exception as e:
			QtGui.QMessageBox.warning(self, 'Message',"No response from IT6D_CA2 microstepper Gpib port! Check the Gpib port name.")	
			return None


		try:
			i_,j_ = self.it6d.get_positions()
		except Exception as e:
			QtGui.QMessageBox.warning(self, 'Message',"No response from IT6D_CA2 microstepper! Is IT6D_CA2 powered and connected to Gpib?")	
			return None

		self.update_lcd(1e-6*int(i_),1e-7*int(j_))

		self.onActivated4(self.op_mode)
		self.conMode.setEnabled(False)
		self.disconMode.setEnabled(True)
		self.serSR810.setEnabled(False)
		self.gpibIT6D_CA2.setEnabled(False)
			
	def set_disconnect(self):

		self.sr810.close()
		
		self.allFields(False)
		self.conMode.setEnabled(True)
		self.disconMode.setEnabled(False)
		self.serSR810.setEnabled(True)
		self.gpibIT6D_CA2.setEnabled(True)
	
	def allFields(self,trueorfalse):
		
		self.combo2.setEnabled(trueorfalse)
		self.combo4.setEnabled(trueorfalse)
		self.combo5.setEnabled(trueorfalse)
		self.combo6.setEnabled(trueorfalse)
		self.combo7.setEnabled(trueorfalse)
		
		self.sld_freq.setEnabled(trueorfalse)
		self.sld_amp.setEnabled(trueorfalse)
		self.dwelltimeEdit.setEnabled(trueorfalse)
		
		for i in range(2):
			self.xy_limiterEdit[i].setEnabled(trueorfalse)
		for i in range(3):
			self.xscanEdit[i].setEnabled(trueorfalse)
			self.yscanEdit[i].setEnabled(trueorfalse)
		for i in range(2):
			self.absrelEdit[i].setEnabled(trueorfalse)
			
		self.filenameEdit.setEnabled(trueorfalse)
		self.folderEdit.setEnabled(trueorfalse)
		self.runButton.setEnabled(trueorfalse)
	
	def IT6D_CA2Dialog(self):

		text, ok = QtGui.QInputDialog.getText(self, 'Gpib Port Dialog','Enter IT6D_CA2 microstepper port number:', text=self.it6d_ca2port_str)
		if ok:
			self.it6d_ca2port_str = str(text)
	
	def SR810Dialog(self):

		text, ok = QtGui.QInputDialog.getText(self, 'Serial Port Dialog','Enter SR810 lock-in port number:', text=self.sr810port_str)
		if ok:
			self.sr810port_str = str(text)
	
	
	def email_data_dialog(self):
		
		self.Send_email_dialog = Send_email_dialog()
		self.Send_email_dialog.exec_()
	
	def email_set_dialog(self):
		
		self.Email_dialog = Email_dialog(self.lcd)
		self.Email_dialog.exec_()
	
	def reload_email(self):
		
		imp.reload(config_IT6D_CA2)	
		self.emailrec_str = config_IT6D_CA2.emailrec
		self.emailset_str = config_IT6D_CA2.emailset
	
	
	
	def changeFreq(self, val):
		
		self.lockin_freq=val
		self.freq_lbl.setText(''.join(["Osc. freq (",str(val),") [Hz]"]))
		self.sr810.set_intrl_freq(val)
		time.sleep(0.05)
		
	def changeAmp(self, val):
		
		self.lockin_volt=val/1000.0
		self.amp_lbl.setText(''.join(["Osc. Vpk-pk (",str(val/1000.0),") [V]"]))
		self.sr810.set_intrl_volt(val/1000.0)
		time.sleep(0.05)
		
	def onActivated2(self, text):
		
		self.schroll_pts=int(text)
	
	def onActivated6(self, text):
		
		self.reset_mode = str(text)
	
	def onActivated7(self, text):
		
		self.smart_scan = str(text)
		
	def onActivated5(self, text):
		
		self.scan_mode = str(text)
	
	def onActivated4(self, text):
		
		self.op_mode = str(text)
		self.combo4.setEnabled(True)
		self.cancelButton.setEnabled(False)
		self.runButton.setEnabled(True)
		self.fileClose.setEnabled(True)
		self.sld_freq.setEnabled(True)
		self.sld_amp.setEnabled(True)
		
		if self.op_mode=='xyscan':
			self.combo2.setEnabled(True)
			self.combo5.setEnabled(True)
			self.combo6.setEnabled(False)
			self.combo7.setEnabled(True)
			self.dwelltimeEdit.setEnabled(True)
			self.filenameEdit.setEnabled(True)
			self.folderEdit.setEnabled(True)
			for i in range(2):
				self.xy_limiterEdit[i].setEnabled(True)
			for i in range(3):
				self.xscanEdit[i].setEnabled(True)
				self.yscanEdit[i].setEnabled(True)
			for i in range(2):
				self.absrelEdit[i].setEnabled(False)
		
		elif self.op_mode=='xscan':
			self.combo2.setEnabled(True)
			self.combo5.setEnabled(False)
			self.combo6.setEnabled(False)
			self.combo7.setEnabled(False)
			self.dwelltimeEdit.setEnabled(True)
			self.filenameEdit.setEnabled(True)
			self.folderEdit.setEnabled(True)
			self.xy_limiterEdit[0].setEnabled(True)
			self.xy_limiterEdit[1].setEnabled(False)
			for i in range(3):
				self.xscanEdit[i].setEnabled(True)
				self.yscanEdit[i].setEnabled(False)
			for i in range(2):
				self.absrelEdit[i].setEnabled(False)
				
		elif self.op_mode=='yscan':
			self.combo2.setEnabled(True)
			self.combo5.setEnabled(False)
			self.combo6.setEnabled(False)
			self.combo7.setEnabled(False)
			self.dwelltimeEdit.setEnabled(True)
			self.filenameEdit.setEnabled(True)
			self.folderEdit.setEnabled(True)
			self.xy_limiterEdit[0].setEnabled(False)
			self.xy_limiterEdit[1].setEnabled(True)
			for i in range(3):
				self.xscanEdit[i].setEnabled(False)
				self.yscanEdit[i].setEnabled(True)
			for i in range(2):
				self.absrelEdit[i].setEnabled(False)
		
		elif self.op_mode in ['move abs','move rel']:
			if self.op_mode=='move rel':
				self.absrel_lbl.setText('Rel')
			elif self.op_mode=='move abs':
				self.absrel_lbl.setText('Abs')
			self.combo2.setEnabled(False)
			self.combo5.setEnabled(False)
			self.combo6.setEnabled(False)
			self.combo7.setEnabled(False)
			self.dwelltimeEdit.setEnabled(False)
			self.filenameEdit.setEnabled(False)
			self.folderEdit.setEnabled(False)
			for i in range(2):
				self.xy_limiterEdit[i].setEnabled(True)
			for i in range(3):
				self.xscanEdit[i].setEnabled(False)
				self.yscanEdit[i].setEnabled(False)
			for i in range(2):
				self.absrelEdit[i].setEnabled(True)

		elif self.op_mode=='reset':
			self.combo2.setEnabled(False)
			self.combo5.setEnabled(False)
			self.combo6.setEnabled(True)
			self.combo7.setEnabled(False)
			self.dwelltimeEdit.setEnabled(False)
			self.filenameEdit.setEnabled(False)
			self.folderEdit.setEnabled(False)
			for i in range(2):
				self.xy_limiterEdit[i].setEnabled(False)
			for i in range(3):
				self.xscanEdit[i].setEnabled(False)
				self.yscanEdit[i].setEnabled(False)
			for i in range(2):
				self.absrelEdit[i].setEnabled(False)
		else:
			pass
	
	
			
	def set_run(self):
		
		xy_limiter=[float(self.xy_limiterEdit[tal].text()) for tal in range(2)]
		i_,j_ = self.it6d.get_positions()
		
		filename = str(self.filenameEdit.text())
		folder = str(self.folderEdit.text())
		# For SAVING data
		if filename:
			full_filename=''.join([filename,self.timetrace])
		else:
			full_filename=''.join(["data_",self.timetrace])
			
		if folder:
			saveinfolder=''.join([folder,"/"])
			if not os.path.isdir(folder):
				os.mkdir(folder)
		else:
			saveinfolder=""
		self.data_file=''.join([saveinfolder,full_filename])
		
		
		if self.op_mode=='xyscan':
			
			# Initial read of the config file
			xx = [int(1000*float(self.xscanEdit[ii].text())) for ii in range(3)]
			yy = [int(10000*float(self.yscanEdit[ii].text())) for ii in range(3)]
			sm = Methods_for_IT6D_CA2.Scan_methods(xx[0],xx[1],xx[2],yy[0],yy[1],yy[2])
			
			xf=Methods_for_IT6D_CA2.Myrange(xx[0],xx[1],xx[2])
			x_fields=xf.myrange() # 1 unit = 1 um
			
			yf=Methods_for_IT6D_CA2.Myrange(yy[0],yy[1],yy[2])
			y_fields=yf.myrange() # 1 unit = 0.1 um
			
			dwelltime = float(self.dwelltimeEdit.text())
			xscan = [float(self.xscanEdit[ii].text()) for ii in range(3)]
			yscan = [float(self.yscanEdit[ii].text()) for ii in range(3)]
			i_vals,j_vals = sm.run(self.scan_mode)
			
			if abs(xscan[0]-int(i_)/1000.0)>xy_limiter[0] or abs(xscan[1]-int(i_)/1000.0)>xy_limiter[0]:
				QtGui.QMessageBox.warning(self, 'Message',''.join([ "All movements in the X direction limited to ", str(xy_limiter[0]) ,' mm' ]))
			elif abs(yscan[0]-int(j_)/10000.0)>xy_limiter[1] or abs(yscan[1]-int(j_)/10000.0)>xy_limiter[1]:
				QtGui.QMessageBox.warning(self, 'Message',''.join([ "All movements in the Y direction limited to ", str(xy_limiter[1]) ,' mm' ]))
			elif len(x_fields)<3 or len(y_fields)<3:
				QtGui.QMessageBox.warning(self, 'Message',''.join([ "Number of scan points is minimum 3 along X-axis and along Y-axis" ]))
			else:
				all_pts=len(x_fields)*len(y_fields)*dwelltime+sum(abs(numpy.diff(i_vals)))/380.0+sum(abs(numpy.diff(j_vals)))/350.0
				mi,se=divmod(int(all_pts),60)
				ho,mi=divmod(mi,60)
				da,ho=divmod(ho,24)
				if self.smart_scan=="yes":
					if mi==0 and ho==0 and da==0:
						msg=''.join(["Smart scan is activated. The xyscan will take ",str(se)," seconds. Continue?"])
					elif ho==0 and da==0:
						msg=''.join(["Smart scan is activated. The xyscan will take ",str(mi)," minutes and ",str(se)," seconds. Continue?"])
					elif da==0:
						msg=''.join(["Smart scan is activated. The xyscan will take ",str(ho)," hour(s) and ",str(mi)," minutes and ",str(se)," seconds. Continue?"])
					else:
						msg=''.join(["Smart scan is activated. The xyscan will take ",str(da)," day(s), ",str(ho)," hour(s) and ",str(mi)," minutes and ",str(se)," seconds. Continue?"])
				else:
					if mi==0 and ho==0 and da==0:
						msg=''.join(["The xyscan will take ",str(se)," seconds. Continue?"])
					elif ho==0 and da==0:
						msg=''.join(["The xyscan will take ",str(mi)," minutes and ",str(se)," seconds. Continue?"])
					elif da==0:
						msg=''.join(["The xyscan will take ",str(ho)," hour(s) and ",str(mi)," minutes and ",str(se)," seconds. Continue?"])
					else:
						msg=''.join(["The xyscan will take ",str(da)," day(s), ",str(ho)," hour(s) and ",str(mi)," minutes and ",str(se)," seconds. Continue?"])
				reply = QtGui.QMessageBox.question(self, 'Message', msg, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
				if reply == QtGui.QMessageBox.Yes:
					pass
				else:
					return None
				
				self.clear_vars_graphs()
				self.allFields(False)
				self.cancelButton.setEnabled(True)
				self.runButton.setEnabled(False)
				self.fileClose.setEnabled(False)
				self.disconMode.setEnabled(False)
				self.get_thread=Run_IT6D_CA2_Thread(self.op_mode,self.scan_mode,self.smart_scan,self.data_file,x_fields,y_fields, dwelltime,self.reset_mode,self.it6d,self.sr810)
				
				self.all_xy(i_vals*1e-6,j_vals*1e-7) # convert to meters
				self.connect(self.get_thread, SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), self.update_lcd)
				self.connect(self.get_thread, SIGNAL('update_pos_lcd(PyQt_PyObject,PyQt_PyObject)'), self.update_pos_lcd)
				self.connect(self.get_thread, SIGNAL('update_color_map(PyQt_PyObject)'), self.update_color_map)
				self.connect(self.get_thread, SIGNAL('make_update2(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.make_update2)
				self.connect(self.get_thread, SIGNAL('make_update4(PyQt_PyObject,PyQt_PyObject)'), self.make_update4)
				self.connect(self.get_thread, SIGNAL('update_Spath(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.update_Spath)
				self.connect(self.get_thread, SIGNAL('update_Umax(PyQt_PyObject,PyQt_PyObject)'), self.update_Umax)
				self.connect(self.get_thread, SIGNAL('update_fwhm(PyQt_PyObject,PyQt_PyObject)'), self.update_fwhm)
				self.connect(self.get_thread, SIGNAL('plot_gaussian(PyQt_PyObject)'), self.plot_gaussian)
				self.connect(self.get_thread, SIGNAL('update_slope(PyQt_PyObject,PyQt_PyObject)'), self.update_slope)
				self.connect(self.get_thread, SIGNAL('make_3Dplot()'), self.make_3Dplot)
				self.connect(self.get_thread, SIGNAL('finished()'), self.set_finished)
				self.get_thread.start()
				
		elif self.op_mode=='xscan':
			# Set the internal oscillator on SR810
			
			# Initial read of the config file
			xscan = [float(self.xscanEdit[ii].text()) for ii in range(3)]
			xx = [int(1000*float(self.xscanEdit[ii].text())) for ii in range(3)]
			xf=Methods_for_IT6D_CA2.Myrange(xx[0],xx[1],xx[2])
			x_fields=xf.myrange() # 1 unit = 1 um
			
			dwelltime = float(self.dwelltimeEdit.text())
			filename = str(self.filenameEdit.text())
			folder = str(self.folderEdit.text())
			
			i_vals=x_fields
			j_vals=numpy.array([int(j_) for jj in range(len(x_fields))])
			
			if abs(xscan[0]-int(i_)/1000.0)>xy_limiter[0] or abs(xscan[1]-int(i_)/1000.0)>xy_limiter[0]:
				QtGui.QMessageBox.warning(self, 'Message',''.join([ "All movements in the X direction limited to ", str(xy_limiter[0]) ,' mm' ]))
			elif len(x_fields)<3:
				QtGui.QMessageBox.warning(self, 'Message',''.join([ "Number of scan points is minimum 3 along X-axis" ]))
			else:
				all_pts=len(x_fields)*dwelltime+sum(abs(numpy.diff(i_vals)))/380.0
				mi,se=divmod(int(all_pts),60)
				ho,mi=divmod(mi,60)
				da,ho=divmod(ho,24)
				if mi==0 and ho==0 and da==0:
					msg=''.join(["The xscan will take ",str(se)," seconds. Continue?"])
				elif ho==0 and da==0:
					msg=''.join(["The xscan will take ",str(mi)," minutes and ",str(se)," seconds. Continue?"])
				elif da==0:
					msg=''.join(["The xscan will take ",str(ho)," hour(s) and ",str(mi)," minutes and ",str(se)," seconds. Continue?"])
				else:
					msg=''.join(["The xscan will take ",str(da)," day(s), ",str(ho)," hour(s) and ",str(mi)," minutes and ",str(se)," seconds. Continue?"])
				reply = QtGui.QMessageBox.question(self, 'Message', msg, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
				if reply == QtGui.QMessageBox.Yes:
					pass
				else:
					return None
				
				self.clear_vars_graphs()
				self.allFields(False)
				self.cancelButton.setEnabled(True)
				self.runButton.setEnabled(False)
				self.fileClose.setEnabled(False)
				self.disconMode.setEnabled(False)
				self.get_thread=Run_IT6D_CA2_Thread(self.op_mode,self.scan_mode,None,self.data_file,x_fields,None,
																					dwelltime,self.reset_mode,self.it6d,self.sr810)
				self.all_xy(i_vals*1e-6,j_vals*1e-7) # convert to meters
				self.connect(self.get_thread, SIGNAL('update_pos_lcd(PyQt_PyObject,PyQt_PyObject)'), self.update_pos_lcd)
				self.connect(self.get_thread, SIGNAL('update_color_map(PyQt_PyObject)'), self.update_color_map)
				self.connect(self.get_thread, SIGNAL('make_update2(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.make_update2)
				self.connect(self.get_thread, SIGNAL('make_update4(PyQt_PyObject,PyQt_PyObject)'), self.make_update4)
				self.connect(self.get_thread, SIGNAL('update_Umax(PyQt_PyObject,PyQt_PyObject)'), self.update_Umax)
				self.connect(self.get_thread, SIGNAL('update_fwhm(PyQt_PyObject,PyQt_PyObject)'), self.update_fwhm)
				self.connect(self.get_thread, SIGNAL('plot_gaussian(PyQt_PyObject)'), self.plot_gaussian)
				self.connect(self.get_thread, SIGNAL('finished()'), self.set_finished)
				self.get_thread.start()
				
		elif self.op_mode=='yscan':
			# Set the internal oscillator on SR810
			
			# Initial read of the config file
			yscan = [float(self.yscanEdit[ii].text()) for ii in range(3)]
			yy = [int(10000*float(self.yscanEdit[ii].text())) for ii in range(3)]
			yf=Methods_for_IT6D_CA2.Myrange(yy[0],yy[1],yy[2])
			y_fields=yf.myrange() # 1 unit = 0.1 um
			dwelltime = float(self.dwelltimeEdit.text())
			filename = str(self.filenameEdit.text())
			folder = str(self.folderEdit.text())
			
			j_vals=y_fields
			i_vals=numpy.array([int(i_) for ii in range(len(y_fields))])
			
			if abs(yscan[0]-int(j_)/10000.0)>xy_limiter[1] or abs(yscan[1]-int(j_)/10000.0)>xy_limiter[1]:
				QtGui.QMessageBox.warning(self, 'Message',''.join([ "All movements in the Y direction limited to ", str(xy_limiter[1]) ,' mm' ]))
			elif len(y_fields)<3:
				QtGui.QMessageBox.warning(self, 'Message',''.join([ "Number of scan points is minimum 3 along Y-axis" ]))
			else:
				all_pts=len(y_fields)*dwelltime+sum(abs(numpy.diff(j_vals)))/350.0
				mi,se=divmod(int(all_pts),60)
				ho,mi=divmod(mi,60)
				da,ho=divmod(ho,24)
				if mi==0 and ho==0 and da==0:
					msg=''.join(["The yscan will take ",str(se)," seconds. Continue?"])
				elif ho==0 and da==0:
					msg=''.join(["The yscan will take ",str(mi)," minutes and ",str(se)," seconds. Continue?"])
				elif da==0:
					msg=''.join(["The yscan will take ",str(ho)," hour(s) and ",str(mi)," minutes and ",str(se)," seconds. Continue?"])
				else:
					msg=''.join(["The yscan will take ",str(da)," day(s), ",str(ho)," hour(s) and ",str(mi)," minutes and ",str(se)," seconds. Continue?"])
				reply = QtGui.QMessageBox.question(self, 'Message', msg, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
				if reply == QtGui.QMessageBox.Yes:
					pass
				else:
					return None
				
				self.clear_vars_graphs()
				self.allFields(False)
				self.cancelButton.setEnabled(True)
				self.runButton.setEnabled(False)
				self.fileClose.setEnabled(False)
				self.disconMode.setEnabled(False)
				self.get_thread=Run_IT6D_CA2_Thread(self.op_mode,self.scan_mode,None,self.data_file,None,y_fields,
																					dwelltime,self.reset_mode,self.it6d,self.sr810)
				self.all_xy(i_vals*1e-6,j_vals*1e-7) # convert to meters
				self.connect(self.get_thread, SIGNAL('update_pos_lcd(PyQt_PyObject,PyQt_PyObject)'), self.update_pos_lcd)
				self.connect(self.get_thread, SIGNAL('update_color_map(PyQt_PyObject)'), self.update_color_map)
				self.connect(self.get_thread, SIGNAL('make_update2(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.make_update2)
				self.connect(self.get_thread, SIGNAL('make_update4(PyQt_PyObject,PyQt_PyObject)'), self.make_update4)
				self.connect(self.get_thread, SIGNAL('update_Umax(PyQt_PyObject,PyQt_PyObject)'), self.update_Umax)
				self.connect(self.get_thread, SIGNAL('update_fwhm(PyQt_PyObject,PyQt_PyObject)'), self.update_fwhm)
				self.connect(self.get_thread, SIGNAL('plot_gaussian(PyQt_PyObject)'), self.plot_gaussian)
				self.connect(self.get_thread, SIGNAL('finished()'), self.set_finished)
				self.get_thread.start()
				
		elif self.op_mode=='move abs':
			
			abss = [float(self.absrelEdit[ii].text()) for ii in range(2)]
			
			if abs(abss[0]-int(i_)/1000.0)>xy_limiter[0]:
				QtGui.QMessageBox.warning(self, 'Message',''.join([ "All movements in the X direction limited to ", str(xy_limiter[0]) ,' mm' ]))
			elif abs(abss[1]-int(j_)/10000.0)>xy_limiter[1]:
				QtGui.QMessageBox.warning(self, 'Message',''.join([ "All movements in the Y direction limited to ", str(xy_limiter[1]) ,' mm' ]))
			else:
				self.allFields(False)
				self.cancelButton.setEnabled(True)
				self.runButton.setEnabled(False)
				self.disconMode.setEnabled(False)
				absrel_x = int(1000*float(self.absrelEdit[0].text())) 
				absrel_y = int(10000*float(self.absrelEdit[1].text()))
				self.get_thread=Run_IT6D_CA2_Thread(self.op_mode,self.scan_mode,None,None,absrel_x,absrel_y,
																					None,self.reset_mode,self.it6d,self.sr810)
				self.connect(self.get_thread, SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), self.update_lcd)
				self.connect(self.get_thread, SIGNAL('finished()'), self.set_finished)
				self.get_thread.start()
		
		elif self.op_mode=='move rel':
			
			rell = [float(self.absrelEdit[ii].text()) for ii in range(2)]
		
			if abs(rell[0]/1000.0)>xy_limiter[0]:
				QtGui.QMessageBox.warning(self, 'Message',''.join([ "All movements in the X direction limited to ", str(xy_limiter[0]) ,' mm' ]))
			elif abs(rell[1]/10000.0)>xy_limiter[1]:
				QtGui.QMessageBox.warning(self, 'Message',''.join([ "All movements in the Y direction limited to ", str(xy_limiter[1]) ,' mm' ]))
			else:
				self.allFields(False)
				self.cancelButton.setEnabled(True)
				self.runButton.setEnabled(False)
				self.disconMode.setEnabled(False)
				absrel_x = int(1000*float(self.absrelEdit[0].text())) 
				absrel_y = int(10000*float(self.absrelEdit[1].text()))
				self.get_thread=Run_IT6D_CA2_Thread(self.op_mode,self.scan_mode,None,None,absrel_x,absrel_y,
																					None,self.reset_mode,self.it6d,self.sr810)
				self.connect(self.get_thread, SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), self.update_lcd)
				self.connect(self.get_thread, SIGNAL('finished()'), self.set_finished)
				self.get_thread.start()
				
		elif self.op_mode=='reset':
			
			self.allFields(False)
			self.cancelButton.setEnabled(True)
			self.runButton.setEnabled(False)
			self.fileClose.setEnabled(False)
			self.disconMode.setEnabled(False)
			
			self.get_thread=Run_IT6D_CA2_Thread(self.op_mode,self.scan_mode,None,None,None,None,
																				None,self.reset_mode,self.it6d,self.sr810)
			self.connect(self.get_thread, SIGNAL('update_lcd(PyQt_PyObject,PyQt_PyObject)'), self.update_lcd)
			self.connect(self.get_thread, SIGNAL('finished()'), self.set_finished)
			self.get_thread.start()
	
	def make_update4(self,time_endpoint,volt_endpoint):
		
		# Update curve3 in different plot
		if len(self.all_pos)>self.schroll_pts:
			self.acc_time_endpoint[:-1] = self.acc_time_endpoint[1:]  # shift data in the array one sample left
			self.acc_time_endpoint[-1] = time_endpoint
			self.acc_volt_endpoint[:-1] = self.acc_volt_endpoint[1:]  # shift data in the array one sample left
			self.acc_volt_endpoint[-1] = volt_endpoint
		else:
			self.acc_time_endpoint.extend([ time_endpoint ])
			self.acc_volt_endpoint.extend([ volt_endpoint ])
			
		self.curve3.setData(self.acc_time_endpoint,self.acc_volt_endpoint)
		
	def make_3Dplot(self):
		
		X_data=[]
		Y_data=[]
		Lockin_data=[]
		data_file=''.join([self.data_file,".txt"])
		with open(data_file,'r') as thefile:
			for i in range(6):
				headers=thefile.readline()
			for lines in thefile:
				columns=lines.split()
				X_data.extend([ 1000*float(columns[0]) ])
				Y_data.extend([ 1000*float(columns[1]) ])
				Lockin_data.extend([ 1000*float(columns[2]) ])
				
		fig=plt.figure(figsize=(8,6))
		ax= fig.add_subplot(111, projection='3d')
		ax.plot_trisurf(X_data,Y_data,Lockin_data,cmap=cm.jet,linewidth=0.2)
		#ax=fig.gca(projection='2d')
		ax.set_xlabel('X[mm]')
		ax.set_ylabel('Y[mm]')
		ax.set_zlabel('U[mV]')
		
		self.save_3Dplot=''.join([self.data_file,'_3D.png'])
		fig.savefig(self.save_3Dplot)
		
		
			
	'''
	def surf_line_plot(self):
		
		if self.scan_mode=='ywise':
			n = len(self.x_fields)
			x = self.x_fields
			y = self.y_fields
			z = self.acc_volt.reshape((len(self.x_fields),len(self.y_fields) ))
			for i in range(n):
				pts = (x,y,z[i,:])
				self.plt1.setData(pos=pts, color=pg.glColor((i,n*1.3)), width=(i+1)/10., antialias=True)
				self.pw4.addItem(self.plt1)
				
		elif self.scan_mode=='xwise':
			n = len(self.y_fields)
			x = self.x_fields
			y = self.y_fields
			z = self.acc_volt.reshape((len(self.x_fields),len(self.y_fields) ))
			for i in range(n):
				pts = (x,y,z[:,i])
				self.plt1.setData(pos=pts, color=pg.glColor((i,n*1.3)), width=(i+1)/10., antialias=True)
				self.pw4.addItem(self.plt1)
	'''
	def update_Spath(self,umax_X_lsf,umax_Y_lsf,S,Umax):
		
		self.curve6.setData(S,Umax)
		self.curve8.setData(umax_X_lsf,umax_Y_lsf)
		
		
	def update_Umax(self,umax_X,umax_Y):
		
		self.curve7.setData(umax_X,umax_Y)
	
		
	def update_fwhm(self,tals,fwhm):
		
		self.curve9.setData(tals,fwhm)
	
	
	def plot_gaussian(self,my_object):
		
		pos_y,voltages,xy_string,save_xy,gauss_pos,gauss_volts,roots = my_object
		
		if xy_string=='x':
			self.p11.setTitle(''.join(["Latest gaussian fit (X=",str(1000*save_xy),"mm)"]))
			self.p11.setLabel('bottom', "Y", units='m', color='yellow')
		elif xy_string=='y':
			self.p11.setTitle(''.join(["Latest gaussian fit (Y=",str(1000*save_xy),"mm)"]))
			self.p11.setLabel('bottom', "X", units='m', color='yellow')
		
		self.curve11.setData(gauss_pos,gauss_volts)
		self.curve12.setData(pos_y,voltages)
		self.curve13.setData(roots,2*[max(voltages)/2])
		
		self.my_text.setPos(numpy.mean(roots),max(voltages)/2)
		self.my_arrow.setPos(numpy.mean(roots),max(voltages)/2)
		
	def update_slope(self,tals,slope):
		
		self.curve10.setData(tals,slope)
		
		
	def all_xy(self,i,j):
		
		if self.smart_scan=="yes":
			self.curve1.setData(i,j, symbolBrush='k')
		else:
			self.curve1.setData(i,j)

	def make_update2(self,time_elap,pos,volt):
    
		self.all_pos.extend([ pos ])
		if len(self.all_pos)>self.schroll_pts:
			self.plot_time_tt[:-1] = self.plot_time_tt[1:]  # shift data in the array one sample left
			self.plot_time_tt[-1] = time_elap
			self.plot_pos_tt[:-1] = self.plot_pos_tt[1:]  # shift data in the array one sample left
			self.plot_pos_tt[-1] = pos
			self.plot_volts_tt[:-1] = self.plot_volts_tt[1:]  # shift data in the array one sample left
			self.plot_volts_tt[-1] = volt
		else:
			self.plot_time_tt.extend([ time_elap ])
			self.plot_pos_tt.extend([ pos ])
			self.plot_volts_tt.extend([ volt ])
			

		## Handle view resizing 
		def updateViews():
			## view has resized; update auxiliary views to match
			self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
			#p3.setGeometry(p1.vb.sceneBoundingRect())

			## need to re-update linked axes since this was called
			## incorrectly while views had different shapes.
			## (probably this should be handled in ViewBox.resizeEvent)
			self.p2.linkedViewChanged(self.p1.vb, self.p2.XAxis)
			#p3.linkedViewChanged(p1.vb, p3.XAxis)
			
		updateViews()
		self.p1.vb.sigResized.connect(updateViews)
		self.curve4.setData(self.plot_time_tt, self.plot_volts_tt)
		self.curve5.setData(self.plot_time_tt, self.plot_pos_tt)
			
	def set_cancel(self):

		self.get_thread.abort()
		
	def clear_vars_graphs(self):
		
		# PLOT 1 initial canvas settings
		self.all_pos=[]
		self.all_volt_endpts=[]
		self.acc_x_pos=[]
		self.acc_y_pos=[]
		self.curve1.clear()
		self.curve2.clear()
		
		# PLOT 2 initial canvas settings
		self.curve6.clear()
		
		# PLOT 5 initial canvas settings
		self.curve7.clear()
		self.curve8.clear()
		
		# PLOT 6 initial canvas settings
		self.curve9.clear()
		self.curve10.clear()
		
		# PLOT 3 initial canvas settings
		self.plot_time_tt=[]
		self.plot_volts_tt=[]
		self.plot_pos_tt=[]
		self.acc_time_endpoint=[]
		self.acc_volt_endpoint=[]
		# create plot and add it to the figure canvas
		self.curve3.clear()
		self.curve4.clear()
		self.curve5.clear()

	def set_save(self):
		
		self.timetrace=time.strftime("%y%m%d-%H%M")
		self.reload_email()
		
		with open("config_IT6D_CA2.py", 'w') as thefile:
			thefile.write( ''.join(["op_mode=\"",self.op_mode,"\"\n"]) )
			thefile.write( ''.join(["scan_mode=\"",self.scan_mode,"\"\n"]) )
			thefile.write( ''.join(["folder=\"",str(self.folderEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["filename=\"",str(self.filenameEdit.text()),"\"\n"]) )
			thefile.write( ''.join(["x_scan_mm=[",','.join([str(self.xscanEdit[ii].text()) for ii in range(3)]),"]\n"]) )
			thefile.write( ''.join(["y_scan_mm=[",','.join([str(self.yscanEdit[ii].text()) for ii in range(3)]),"]\n"]) )
			thefile.write( ''.join(["absrel_mm=[",','.join([str(self.absrelEdit[ii].text()) for ii in range(2)]),"]\n"]) )
			thefile.write( ''.join(["wait_time=",str(self.dwelltimeEdit.text()),"\n"]) )
			thefile.write( ''.join(["reset_mode=\"",self.reset_mode,"\"\n"]) )
			thefile.write( ''.join(["xy_limiter_mm=[",','.join([str(self.xy_limiterEdit[ii].text()) for ii in range(2)]),"]\n"]) )
			thefile.write( ''.join(["smart_scan=\"",self.smart_scan,"\"\n"]) )
			thefile.write( ''.join(["lockin_volt=",str(self.lockin_volt),"\n"]) )
			thefile.write( ''.join(["lockin_freq=",str(self.lockin_freq),"\n"]) )
			thefile.write( ''.join(["schroll_pts=",str(self.schroll_pts),"\n"]) )
			thefile.write( ''.join(["timetrace=\"",self.timetrace,"\"\n"]) )
			thefile.write( ''.join(["it6d_ca2port=\"",self.it6d_ca2port_str,"\"\n"]) )
			thefile.write( ''.join(["sr810port=\"",self.sr810port_str,"\"\n"]) )
			thefile.write( ''.join(["emailrec=[\"",'\",\"'.join([i for i in self.emailrec_str]),"\"]\n"]) )
			thefile.write( ''.join(["emailset=[\"",'\",\"'.join([i for i in self.emailset_str]),"\"]\n"]) )
			
		self.lcd.display(self.timetrace)
	
	def set_finished(self):

		self.onActivated4(self.op_mode)
		self.disconMode.setEnabled(True)
		
		self.reload_email()
		if self.emailset_str[1] == "yes":
			self.send_notif()
		if self.emailset_str[2] == "yes":
			self.send_data()
			
		plt.show()

	def send_notif(self):
		
		try:
			self.yag = yagmail.SMTP(self.emailset_str[0])
			self.yag.send(to=self.emailrec_str, subject="Microstepper scan is done!", contents="Microstepper scan is done. Please visit the experiment site and make sure that all light sources are switched off.")
		except Exception as e:
			QtGui.QMessageBox.warning(self, 'Message',''.join(["Could not load the gmail account ",self.emailset_str[0],"! Try following steps:\n1. Check internet connection. Only wired internet will work, ie. no wireless.\n2. Check the account username and password.\n3. Make sure that the account accepts less secure apps."]))
			
	def send_data(self):
		
		try:
			if hasattr(self, "save_3Dplot") and hasattr(self,"data_file"):
				self.yag = yagmail.SMTP(self.emailset_str[0])
				self.yag.send(to=self.emailrec_str, subject="Microstepper data from the latest scan!", contents=["Microstepper scan is  done and the logged data is attached to this email. Please visit the experiment site and make sure that all light sources are switched off.", self.save_3Dplot,''.join([self.data_file,".txt"]) ])
		except Exception as e:
			QtGui.QMessageBox.warning(self, 'Message',''.join(["Could not load gmail account ",self.emailset_str[0],"! Try following steps:\n1. Check internet connection. Only wired internet will work, ie. no wireless.\n2. Check the account username and password.\n3. Make sure that the account accepts less secure apps."]))
			
	def closeEvent(self, event):
		reply = QtGui.QMessageBox.question(self, 'Message', "Quit now? Any changes that are not saved will stay unsaved!", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes:
			if hasattr(self, 'sr810'):
				if self.conMode.isEnabled()==False:
					if not hasattr(self, 'get_thread'):
						self.sr810.close()
						event.accept()
					else:
						if self.get_thread.isRunning():
							QtGui.QMessageBox.warning(self, 'Message', "Run in progress. Stop the run then quit!")
							event.ignore()
						else:
							self.sr810.close()
							event.accept()
				else:
					pass
			else:
				event.accept()
		else:
		  event.ignore() 

	##########################################
	
	def set_save_plots(self):
		
		filename = str(self.filenameEdit.text())
		folder = str(self.folderEdit.text())
		
		# For SAVING data
		if filename:
			full_filename=''.join([filename,self.timetrace])
		else:
			full_filename=''.join(["data_",self.timetrace])
			
		if folder:
			saveinfolder=''.join([folder,"/"])
			if not os.path.isdir(folder):
				os.mkdir(folder)
		else:
			saveinfolder=""
			
		save_plot1=''.join([saveinfolder,full_filename,'.png'])	
		
		# create an exporter instance, as an argument give it
		# the item you wish to export
		exporter = pg.exporters.ImageExporter(self.p0)
		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_plot1)
		
		
#########################################
#########################################
#########################################

def main():
	
	app = QtGui.QApplication(sys.argv)
	ex = Run_IT6D_CA2()
	sys.exit(app.exec_())

if __name__ == '__main__':
  
  main()
