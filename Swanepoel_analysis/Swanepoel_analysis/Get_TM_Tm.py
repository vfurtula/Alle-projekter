## Import libraries
import matplotlib.pyplot as plt
import os, sys, time, numpy
import config_Swanepoel

from itertools import groupby
from scipy.ndimage import filters as fi
from scipy.interpolate import interp1d
from scipy.signal import argrelextrema
from scipy import interpolate
from numpy.polynomial import polynomial as P

'''
## For Matplotlib fonts
from matplotlib import rc
## for LaTeX style use:
rc("text", usetex=True)
rc("font", family="serif")
'''

class Get_TM_Tm:
	

	def __init__(self):
		
		# load the selected config file
		self.config_file = config_Swanepoel.current_config_file
		head, tail = os.path.split(self.config_file)
		sys.path.insert(0, head)
		
		cf = __import__(tail[:-3])
		
		# load all relevant parameters
		self.sub_olis = cf.loadSubOlis[0]
		self.raw_olis = cf.loadSubFilmOlis[0]
		self.sub_ftir = cf.loadSubFTIR[0]
		self.raw_ftir = cf.loadSubFilmFTIR[0]
		
		self.sub_olis_check = cf.loadSubOlis[1]
		self.raw_olis_check = cf.loadSubFilmOlis[1]
		self.sub_ftir_check = cf.loadSubFTIR[1]
		self.raw_ftir_check = cf.loadSubFilmFTIR[1]
		
		self.fit_linear_spline=cf.fit_linear_spline
		self.gaussian_factors=cf.gaussian_factors
		self.gaussian_borders=cf.gaussian_borders
		
		self.fit_poly_order=cf.fit_poly_order
		self.ignore_data_pts=cf.ignore_data_pts
		self.corr_slit=cf.corr_slit
		
		self.fit_poly_ranges=cf.fit_poly_ranges[0]
		self.fit_poly_ranges_check=cf.fit_poly_ranges[1]
		
		self.filename_str=cf.filename
		self.folder_str=cf.folder
		self.timestr=cf.timestr
		self.save_figs=cf.save_figs
		self.plot_X=cf.plot_X
		
		# create a folder where all post-processed data and graphs will be saved
		# but first check if the folder exists
		if not self.folder_str:
			self.folder_str = ''
		else:
		  self.folder_str = ''.join([cf.folder, '/'])
		  if not os.path.isdir(cf.folder):
		    os.mkdir(cf.folder)

		if not self.filename_str:
			if not self.raw_olis:
				head, tail = os.path.split(self.raw_ftir)
				sys.path.insert(0, head)
				self.filename_str = tail[:-4]
			else:
				head, tail = os.path.split(self.raw_olis)
				sys.path.insert(0, head)
				self.filename_str = tail[:-4]
		
		if self.raw_olis:
			self.x_all_olis, self.y_all_olis = self.get_olis_data(self.raw_olis)
			
		if self.raw_ftir:
			self.x_all_ftir, self.y_all_ftir = self.get_ftir_data(self.raw_ftir)
		
		if self.sub_ftir:
			self.x_all_ftir_Ts, self.y_all_ftir_Ts = self.get_ftir_data(self.sub_ftir)
		
		if self.sub_olis:
			self.x_all_olis_Ts, self.y_all_olis_Ts = self.get_olis_data(self.sub_olis)
		
		if self.sub_olis_check or self.sub_ftir_check:
			self.x_all_Ts, self.y_all_Ts = self.combined_Ts()

		if self.raw_olis_check or self.raw_ftir_check:
			self.x_all_Tfilm, self.y_all_Tfilm = self.combined_Tr()
		
	#####################
	# START OF THE CODE #
	#####################
	
	def pass_Ts(self):
		return self.x_all_Ts, self.y_all_Ts
	
	def pass_Tfilm(self):
		return self.x_all_Tfilm, self.y_all_Tfilm

	def get_method(self):
	  return self.fit_linear_spline, self.plot_X, self.config_file

	def str_abs_params(self):
	  return self.fit_poly_order, self.fit_poly_ranges, self.fit_poly_ranges_check

	def folders_and_data(self):
	  return self.folder_str, self.filename_str, self.raw_olis, self.raw_ftir, self.sub_olis, self.sub_ftir, self.timestr, self.save_figs

	def data_checks(self):
		return self.sub_olis_check, self.raw_olis_check, self.sub_ftir_check, self.raw_ftir_check

	def ig_po(self):
	  return self.ignore_data_pts

	###########################################################################
	# Data from FTIR and OLIS: find Tm and TM (m=min, M=max) in Swanepoel1983 # 
	###########################################################################


	def get_olis_data(self,my_string):
		#print 'method get_olis_data runs...'

		# Open new datafile (.asc) form SOURCE 2 (OLIS)
		# Read and ignore header lines
		#header1 = f2.readline()
		data_eV=numpy.array([])
		data_tr=numpy.array([])

		# Read new datafile
		with open(my_string, 'r') as f2:
		  for lines in f2:
				#line = line.strip()
				columns = lines.split()
				data_eV = numpy.append( data_eV, [1239.84187/float(columns[0])] ) # energy in eV
				data_tr = numpy.append( data_tr, [float(columns[1])] )
				
		idx=numpy.argsort(data_eV)
		data_eV=data_eV[idx]
		data_tr=data_tr[idx]
		
		return data_eV, data_tr


	def get_ftir_data(self,my_string):
		#print 'method get_ftir_data runs...'
		
		# Open new datafile (.DPT) from SOURCE 1 (FTIR)
		# Raw FTIR data has complicated structure, severeal vales for a single wavelength
		# Read and ignore header lines
		#header1 = f1.readline()
		data_eV=numpy.array([])
		data_tr=numpy.array([])
		# Read new datafile
		with open(my_string,'r') as f1:
		  for line in f1:
		    #line = line.strip()
		    columns = line.split()
		    data_eV = numpy.append( data_eV, [1239.84187/(1000*float(columns[0]))] ) # energy in eV
		    data_tr = numpy.append( data_tr, [float(columns[1])] )
	      
		# Determine no. of repetitions for each sweeped wavelength (mostly 4 or 5 for FTIR)
		d3=numpy.array([len(list(group)) for key, group in groupby(data_eV)])

		avg=numpy.array([])
		shortlist_eV=numpy.array([])
		stdev_mag=numpy.array([]) 

		for tal in range(len(d3)):
			d4=numpy.sum(d3[0:tal])
			d5=numpy.sum(d3[0:tal+1])
			
			# Y axis enteries
			avg = numpy.append( avg, [numpy.sum(data_tr[d4:d5])/d3[tal]] )
			# X axis enteries
			shortlist_eV = numpy.append( shortlist_eV, [data_eV[d5-1]] ) # energy in eV
			# Python sample std dev calculated by the statistics module
			stdev_mag = numpy.append( stdev_mag, [numpy.sum(data_tr[d4:d5])/len(data_tr[d4:d5])] )
			
		idx=numpy.argsort(shortlist_eV)
		shortlist_eV=shortlist_eV[idx]
		avg=avg[idx]

		return shortlist_eV, avg


	def combined_Tr(self):
		#print 'method combined_Tr runs...'

		if self.raw_ftir_check and not self.raw_olis_check:
		  return self.x_all_ftir, self.y_all_ftir
		  
		elif self.raw_olis_check and not self.raw_ftir_check:
			return self.x_all_olis, self.y_all_olis
		
		elif self.raw_ftir_check and self.raw_olis_check:
			
			indx=numpy.where(self.x_all_olis[0]>self.x_all_ftir)[0]
			
			x_all_ftir = self.x_all_ftir[indx]
			y_all_ftir = self.y_all_ftir[indx]
	  
			return numpy.append(x_all_ftir,self.x_all_olis), numpy.append(y_all_ftir,self.y_all_olis)
	

	def combined_Ts(self):
		#print 'method combined_Ts runs...'

		if self.sub_ftir_check and not self.sub_olis_check:
		  return self.x_all_ftir_Ts, self.y_all_ftir_Ts
		  
		elif self.sub_olis_check and not self.sub_ftir_check:
		  return self.x_all_olis_Ts, self.y_all_olis_Ts
		  
		elif self.sub_olis_check and self.sub_ftir_check:

			indx=numpy.where(self.x_all_olis_Ts[0]>self.x_all_ftir_Ts)[0]

			data_eV_f = self.x_all_ftir_Ts[indx]
			data_ts_f = self.y_all_ftir_Ts[indx]

			return numpy.append(data_eV_f,self.x_all_olis_Ts), numpy.append(data_ts_f,self.y_all_olis_Ts)
		

	def fit_Ts_to_data(self,common_xaxis):
		#print 'method fit_Ts_to_data runs...'

		if self.fit_linear_spline=='linear':
		  f = interpolate.splrep(self.x_all_Ts, self.y_all_Ts, k=1, s=0)
		  
		elif self.fit_linear_spline=='spline':
			f = interpolate.splrep(self.x_all_Ts, self.y_all_Ts, k=3, s=0)
			
		try:
			fit_yaxis = interpolate.splev(common_xaxis, f, der=0)
		except Exception,e:
			raise Exception('interpol')

		return common_xaxis, fit_yaxis


	def extremas(self,x_all,y_all):
	  #print 'method extremas runs...'
	  
	  # Find the correct indicies for the gaussian filter
	  GaussFilt=numpy.array([])
	  x_all_=numpy.array([])
	  y_all_=numpy.array([])
	  
	  for tal in range(len(self.gaussian_borders)-1):
			
			idx = numpy.where((self.gaussian_borders[tal]<=x_all)&(self.gaussian_borders[tal+1]>x_all))[0]
			# Perform gaussian filtering in order to remove noise
			GaussFilt=numpy.append(GaussFilt, fi.gaussian_filter1d(y_all[idx], self.gaussian_factors[tal], mode='nearest'))
			
			# Redefine x_all and y_all since we have cut out some of the original data
			x_all_ = numpy.append(x_all_, x_all[idx])
			y_all_ = numpy.append(y_all_, y_all[idx])

	  # Find the locations (indicies) of min and max
	  # for local maxima
	  max_loc=argrelextrema(GaussFilt, numpy.greater)[0]
	  
	  # and for local minima
	  min_loc=argrelextrema(GaussFilt, numpy.less)[0]
	    
	  x_max=x_all_[max_loc]
	  y_max=y_all_[max_loc]
	  x_min=x_all_[min_loc]
	  y_min=y_all_[min_loc]
	  
	  return x_min, y_min, x_max, y_max


	def interp_T(self, x_min, y_min, x_max, y_max, *argv):
		#print 'method interp_T runs...'
		
		if len(argv)==1:
			corr_slit=argv[0]
		else:
			corr_slit=0
		
		# convert all to nm
		x_min=1239.84187/x_min
		idx = numpy.argsort(x_min)
		x_min = x_min[idx]
		y_min = y_min[idx]
		
		x_max = 1239.84187/x_max
		idx = numpy.argsort(x_max)
		x_max = x_max[idx]
		y_max = y_max[idx]
		
		if (min(x_min)<min(x_max)) and (max(x_min)>max(x_max)):
			y_max = y_max+(y_max*corr_slit/numpy.diff(x_min))**2
			y_min = numpy.array([y_min[0]]+list(y_min[1:-1]-(y_min[1:-1]*corr_slit/numpy.diff(x_max))**2)+[y_min[-1]])
			x_max_ = x_max
			x_min_ = x_min[1:-1]
			
		elif (min(x_min)<min(x_max)) and (max(x_min)<max(x_max)):
			y_max = numpy.array(list(y_max[:-1]+(y_max[:-1]*corr_slit/numpy.diff(x_min))**2)+[y_max[-1]])
			y_min = numpy.array([y_min[0]]+list(y_min[1:]-(y_min[1:]*corr_slit/numpy.diff(x_max))**2))
			x_max_ = x_max[:-1]
			x_min_ = x_min[1:]
			
		elif (min(x_min)>min(x_max)) and (max(x_min)<max(x_max)):
			y_max = numpy.array([y_max[0]]+list(y_max[1:-1]+(y_max[1:-1]*corr_slit/numpy.diff(x_min))**2)+[y_max[-1]])
			y_min = y_min-(y_min*corr_slit/numpy.diff(x_max))**2
			x_max_ = x_max[1:-1]
			x_min_ = x_min
			
		elif (min(x_min)>min(x_max)) and (max(x_min)>max(x_max)):
			y_max = numpy.array([y_max[0]]+list(y_max[1:]+(y_max[1:]*corr_slit/numpy.diff(x_min))**2))
			y_min = numpy.array(list(y_min[:-1]-(y_min[:-1]*corr_slit/numpy.diff(x_max))**2)+[y_min[-1]])
			x_max_ = x_max[1:]
			x_min_ = x_min[:-1]
		
		# convert back to eV
		x_min=1239.84187/x_min
		idx = numpy.argsort(x_min)
		x_min = x_min[idx]
		y_min = y_min[idx]
		
		x_max = 1239.84187/x_max
		idx = numpy.argsort(x_max)
		x_max = x_max[idx]
		y_max = y_max[idx]
		
		common_xaxis=numpy.sort(numpy.append(1239.84187/x_min_,1239.84187/x_max_))
		
		if len(common_xaxis)==0:
			raise Exception('common_xaxis')
			
		else:
			if self.fit_linear_spline=='spline':
			  fmax = interpolate.splrep(x_max, y_max, k=3, s=0)
			  fmin = interpolate.splrep(x_min, y_min, k=3, s=0)
			  
			elif self.fit_linear_spline=='linear':
			  fmax = interpolate.splrep(x_max, y_max, k=1, s=0)
			  fmin = interpolate.splrep(x_min, y_min, k=1, s=0)
			
			Tmax = interpolate.splev(common_xaxis, fmax, der=0)
			Tmin = interpolate.splev(common_xaxis, fmin, der=0)

			return common_xaxis, Tmin, Tmax


	def get_T_alpha(self):
		#print 'method get_T_alpha runs...'
		
		if self.raw_ftir_check or self.raw_olis_check:
			
			x_min, y_min, x_max, y_max = self.extremas(self.x_all_Tfilm,self.y_all_Tfilm)
			
			# Find the extrema points and create a common x-axis
			common_xaxis, Tmin, Tmax = self.interp_T(x_min, y_min, x_max, y_max)

			extremas_first = [x_min, y_min, x_max, y_max]
			com_axisTminTmax_first=[common_xaxis, Tmin, Tmax]

			indx = numpy.where((self.x_all_Tfilm<=self.gaussian_borders[-1])&(self.x_all_Tfilm>=self.gaussian_borders[0]))[0]
			
			# Create T_alpha x-axis and ADD interference-free points 
			common_xaxis_fit = self.x_all_Tfilm[indx]
			T_all_minmax = self.y_all_Tfilm[indx]
			T_alpha_flatten = self.y_all_Tfilm[indx]

			# 2 iterationer plejer at vaere nok at flade ud transmissions kurven
			for tal in range(2):

				# Calculate T_alpha for the previously determined extrema points
				T_al=(Tmax+Tmin)/2.0
				
				# Perform spline to determine T_alpha in the newly found x-axis range
				if self.fit_linear_spline=='spline':
				  f=interpolate.splrep(common_xaxis, T_al, k=3, s=0)
				  
				elif self.fit_linear_spline=='linear':
				  f=interpolate.splrep(common_xaxis, T_al, k=1, s=0)
				  
				T_alpha = interpolate.splev(common_xaxis_fit, f, der=0)
				
				if tal==0:
					T_alpha_first=T_alpha
				
				# Substract T_alpha from the T_r in order to flatten out raw transmission data
				# and only to leave periodic oscillations 
				T_alpha_flatten=T_alpha_flatten-T_alpha
				
				# Calculate NEW extrema points from the flatten curve
				x_min, y_min, x_max, y_max = self.extremas(common_xaxis_fit, T_alpha_flatten)

				# Find the extrema points and create a common x-axis
				common_xaxis, Tmin, Tmax = self.interp_T(x_min, y_min, x_max, y_max)


			extremas_flatten = [x_min, y_min, x_max, y_max]
			
			# Find correct indicies of NEW extrema points relative to the original T_r data 
			idx=numpy.array([],dtype=int)
			for tal in x_min:
				idx=numpy.append(idx,numpy.where(common_xaxis_fit==tal)[0])
			y_min=T_all_minmax[idx]
			
			idx=numpy.array([],dtype=int)
			for tal in x_max:
				idx=numpy.append(idx,numpy.where(common_xaxis_fit==tal)[0])
			y_max=T_all_minmax[idx]
			
			extremas_final = [x_min, y_min, x_max, y_max]
			
			common_xaxis, Tmin, Tmax = self.interp_T(x_min, y_min, x_max, y_max, self.corr_slit)
			
			# Calculate T_alpha for the previously determined extrema points
			T_al=(Tmax+Tmin)/2.0
			# Perform spline to determine T_alpha in the newly found x-axis range
			if self.fit_linear_spline=='spline':
			  f=interpolate.splrep(common_xaxis, T_al, k=3, s=0)
			elif self.fit_linear_spline=='linear':
			  f=interpolate.splrep(common_xaxis, T_al, k=1, s=0)
			T_alpha_final = interpolate.splev(common_xaxis_fit, f, der=0)
				
			# Save the required data in new lists and make a return
			comax_alph_TalTalflat = [common_xaxis_fit, T_alpha_first, T_alpha_final, T_alpha_flatten]
			com_axisTminTmax_final=[common_xaxis, Tmin, Tmax]
			all_extremas = [extremas_first, extremas_final, extremas_flatten]
	        
			return indx, comax_alph_TalTalflat, com_axisTminTmax_final, all_extremas
	


if __name__ == "__main__":
	
	Get_TM_Tm().combined_Ts()
	
	
	
