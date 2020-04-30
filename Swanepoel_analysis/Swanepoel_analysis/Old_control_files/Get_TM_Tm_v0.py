## Import libraries
import matplotlib.pyplot as plt
import os, sys, numpy
import config_Swanepoel

import time, math
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
		self.index_m1_sections=cf.index_m1_sections[0]
		self.fit_poly_ranges=cf.fit_poly_ranges[0]
		self.strong_abs_start_eV=cf.strong_abs_start_eV[0]
		
		self.index_m1_sections_check=cf.index_m1_sections[1]
		self.fit_poly_ranges_check=cf.fit_poly_ranges[1]
		self.strong_abs_start_eV_check=cf.strong_abs_start_eV[1]
		
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
				
	#####################
	# START OF THE CODE #
	#####################

	def get_method(self):
	  return self.fit_linear_spline, self.plot_X, self.config_file

	def str_abs_params(self):
	  return self.strong_abs_start_eV, self.strong_abs_start_eV_check, self.fit_poly_order, self.fit_poly_ranges, self.fit_poly_ranges_check

	def folders_and_data(self):
	  return self.folder_str, self.filename_str, self.raw_olis, self.raw_ftir, self.sub_olis, self.sub_ftir, self.timestr, self.save_figs

	def ig_po(self):
	  return self.index_m1_sections, self.index_m1_sections_check

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
			
		  x_all, y_all = self.get_ftir_data(self.raw_ftir)
		  return x_all, y_all
		  
		elif self.raw_olis_check and not self.raw_ftir_check:
			
			x_all, y_all = self.get_olis_data(self.raw_olis)
			return x_all, y_all
		
		elif self.raw_ftir_check and self.raw_olis_check:
			
			data2_eV, data2_tr = self.get_olis_data(self.raw_olis)
			shortlist_eV, avg = self.get_ftir_data(self.raw_ftir)

			index_1=numpy.argmin(numpy.abs(data2_eV-shortlist_eV[-1]))
			#index_1 = min(range(len(data2_eV)), key=lambda i: abs(data2_eV[i]-shortlist_eV[-1]))

			x_olis = data2_eV[index_1+1:]
			y_olis = data2_tr[index_1+1:]

			x_all = numpy.append(shortlist_eV,x_olis)
			y_all = numpy.append(avg,y_olis)
	  
			return x_all, y_all
	
	def combined_Ts(self):
		#print 'method combined_Ts runs...'

		if self.sub_ftir_check and not self.sub_olis_check:
		  
		  x_all, y_all = self.get_ftir_data(self.sub_ftir)
		  return x_all, y_all
		  
		elif self.sub_olis_check and not self.sub_ftir_check:
		  
		  x_all, y_all = self.get_olis_data(self.sub_olis)
		  return x_all, y_all
		  
		elif self.sub_olis_check and self.sub_ftir_check:
			data_eV_o, data_ts_o = self.get_olis_data(self.sub_olis)
			data_eV_f, data_ts_f = self.get_ftir_data(self.sub_ftir)

			index_1=numpy.argmin(numpy.abs(data_eV_o-data_eV_f[-1]))
			#index_1 = min(range(len(data_eV_o)), key=lambda i: abs(data_eV_o[i]-data_eV_f[-1]))

			x_olis = data_eV_o[index_1+1:]
			y_olis = data_ts_o[index_1+1:]

			x_all = numpy.append(data_eV_f,x_olis)
			y_all = numpy.append(data_ts_f,y_olis)

			return x_all, y_all

	def fit_Ts_to_data(self,common_xaxis):
		#print 'method fit_Ts_to_data runs...'

		x_all, y_all = self.combined_Ts()

		if self.fit_linear_spline=='linear':
		  f = interpolate.splrep(x_all, y_all, k=1, s=0)
		  
		elif self.fit_linear_spline=='spline':
		  f = interpolate.splrep(x_all, y_all, k=3, s=0)

		fit_yaxis = interpolate.splev(common_xaxis, f, der=0)

		return common_xaxis, fit_yaxis

	def extremas(self,x_all,y_all):
	  #print 'method extremas runs...'
	  
	  # Find the correct indicies for the gaussian filter
	  brake_ind=[]
	  for i in self.gaussian_borders:
	    brake_ind.extend([ numpy.argmin(numpy.abs(x_all-i)) ])
	  
	  # Perform gaussian filtering in order to remove noise
	  GaussFilt=numpy.array([])
	  for i in range(len(self.gaussian_factors)):
	    GaussFilt=numpy.append(GaussFilt, fi.gaussian_filter1d(y_all[brake_ind[i]:brake_ind[i+1]], self.gaussian_factors[i], mode='nearest'))
	  
	  # Redefine x_all and y_all since we have cut out some of the original data
	  x_all_ = x_all[brake_ind[0]:brake_ind[-1]]
	  y_all_ = y_all[brake_ind[0]:brake_ind[-1]]

	  # Find the locations (indicies) of min and max
	  # for local maxima
	  max_loc=argrelextrema(GaussFilt, numpy.greater)[0]
	  
	  # and for local minima
	  min_loc=argrelextrema(GaussFilt, numpy.less)[0]
	    
	  x_max=[]
	  y_max=[]
	  x_min=[]
	  y_min=[]
	  for x in max_loc:
	    x_max.extend([x_all_[x]])
	    y_max.extend([y_all_[x]]) # We use original data to identify all max points
	  for x in min_loc:
	    x_min.extend([x_all_[x]])
	    y_min.extend([y_all_[x]]) # We use original data to identify all min points

	  return x_min, y_min, x_max, y_max

	def new_extremas(self, x_all, y_all, x_min, x_max):
		#print 'method new_extremas runs...'

		x_min_locs=[numpy.argmin(numpy.abs(x_all-x_min[ii])) for ii in range(len(x_min))]
		x_max_locs=[numpy.argmin(numpy.abs(x_all-x_max[ii])) for ii in range(len(x_max))]

		x_max_new=[]
		y_max_new=[]
		x_min_new=[]
		y_min_new=[]
		for x in x_max_locs:
		  x_max_new.extend([x_all[x]])
		  y_max_new.extend([y_all[x]]) # We use original data to identify all max points
		for x in x_min_locs:
		  x_min_new.extend([x_all[x]])
		  y_min_new.extend([y_all[x]]) # We use original data to identify all min points

		return x_min_new, y_min_new, x_max_new, y_max_new


	def interp_T(self, x_min, y_min, x_max, y_max):
		#print 'method interp_T runs...'
		    
		x_all_extremas = sorted(x_min+x_max)

		ind1 = x_all_extremas.index(x_min[0])
		ind2 = x_all_extremas.index(x_min[-1])
		x_mins = x_all_extremas[ind1:ind2+1]

		ind3 = x_all_extremas.index(x_max[0])
		ind4 = x_all_extremas.index(x_max[-1])
		x_maxs = x_all_extremas[ind3:ind4+1]

		#common_xaxis=x_all_extremas
		common_xaxis = sorted(list(set(x_mins).intersection(set(x_maxs))))

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
			
			x_all, y_all = self.combined_Tr()
			x_min, y_min, x_max, y_max = self.extremas(x_all,y_all)
			
			# Find the extrema points and create a common x-axis
			common_xaxis, Tmin, Tmax = self.interp_T(x_min, y_min, x_max, y_max)

			extremas_first = [x_min, y_min, x_max, y_max]
			com_axisTminTmax_first=[common_xaxis, Tmin, Tmax]

			indx_start=numpy.argmin(numpy.abs(x_all-self.gaussian_borders[0]))
			indx_end=numpy.argmin(numpy.abs(x_all-self.gaussian_borders[-1])) 

			# 2 iterationer plejer at vaere nok at flade ud transmissions kurven
			for iii in range(2):

				# Calculate T_alpha for the previously determined extrema points
				T_al=[math.sqrt(Tmax[i]*Tmin[i]) for i in range(len(common_xaxis))]
				# Create T_alpha x-axis and ADD interference-free points 
				common_xaxis_fit = numpy.append(common_xaxis,x_all[indx_end:])
				T_alpha_fit=numpy.append(T_al,y_all[indx_end:])
				# Perform spline to determine T_alpha in the newly found x-axis range

				if self.fit_linear_spline=='spline':
				  f=interpolate.splrep(common_xaxis_fit, T_alpha_fit, k=3, s=0)
				  
				elif self.fit_linear_spline=='linear':
				  f=interpolate.splrep(common_xaxis_fit, T_alpha_fit, k=1, s=0)

				common_xaxis_alpha = x_all[indx_start:indx_end]
				T_alpha = interpolate.splev(common_xaxis_alpha, f, der=0)
				# Substract T_alpha from the T_r in order to flatten out raw transmission data
				# and only to leave periodic oscillations 
				T_alpha_flatten=y_all[indx_start:indx_end]-T_alpha
				
				# Calculate NEW extrema points from the flatten curve
				x_min_, y_min_, x_max_, y_max_ = self.extremas(common_xaxis_alpha, T_alpha_flatten)

				extremas_flatten = [x_min_, y_min_, x_max_, y_max_]
				# Find correct indicies of NEW extrema points relative to the original T_r data 
				x_min, y_min, x_max, y_max = self.new_extremas(x_all,y_all,x_min_,x_max_)

			###########################################################
			extremas_final = [x_min, y_min, x_max, y_max]
			# Find the common x-axis for extrema points and determine transmission values
			common_xaxis, Tmin, Tmax = self.interp_T(x_min, y_min, x_max, y_max)

			# Save the required data in new lists and make a return
			indicies = [indx_start, indx_end]
			comax_alph_TalTalflat = [common_xaxis_alpha, T_alpha, T_alpha_flatten]
			com_axisTminTmax_final=[common_xaxis, Tmin, Tmax]
			all_extremas = [extremas_first, extremas_final, extremas_flatten]
	        
			return indicies, comax_alph_TalTalflat, com_axisTminTmax_final, all_extremas
	

	def plot_raw(self):
		
		pass_plots=[]
	
		if self.raw_ftir_check or self.raw_olis_check:
			
			x_all, y_all = self.combined_Tr()
			
			plt.figure(figsize=(15,10))
			
			if self.plot_X=='eV':
				plt.plot(x_all,y_all,'k-')
				plt.xlabel("E, eV", fontsize=20)
				
			elif self.plot_X=='nm':
				plt.plot(1239.84187/x_all,y_all,'k-')
				plt.xlabel("Wavelength, nm", fontsize=20)
				
			plt.ylabel("Tr", fontsize=20)
			plt.tick_params(axis="both", labelsize=20)
			#plt.xlim([0,4])
			#plt.ylim([0,1])
			plt.title("Tr (SUBSTRATE + FILM)")
			#l=plt.legend(loc=1, fontsize=15)
			#l.draw_frame(False)

			string_1 = ''.join([self.folder_str, self.filename_str,'_Tr(subfilmRAW)_',self.timestr, '.png'])
			if self.save_figs==True:
				plt.savefig(string_1)
				pass_plots.extend([string_1])
			
			string_2 = ''.join([string_1[:-3],'txt'])
			with open(string_2, 'w') as thefile:
				thefile.write(''.join(['This data is constructed from the config file ', self.config_file, '\n']))
				thefile.write('Column 1: wavelength in nm\n')
				thefile.write('Column 2: energy in eV\n')
				thefile.write('Column 3: Tr (subfilmRAW)\n')

				for tal0,tal1,tal2 in zip(1239.84187/x_all,x_all,y_all):
					thefile.write(''.join([str(tal0),'\t',str(tal1),'\t',str(tal2),'\n']))

			pass_plots.extend([string_2])
		
		########################################################################
		if self.sub_ftir_check or self.sub_olis_check:
			
			x_all_Ts, y_all_Ts = self.combined_Ts()

			plt.figure(figsize=(15,10))
			
			if self.plot_X=='eV':
				plt.plot(x_all_Ts,y_all_Ts,'k-')
				plt.xlabel("E, eV", fontsize=20)
				
			elif self.plot_X=='nm':
				plt.plot(1239.84187/x_all_Ts,y_all_Ts,'k-')
				plt.xlabel("Wavelength, nm", fontsize=20)
				
			plt.ylabel("Tr", fontsize=20)
			plt.tick_params(axis="both", labelsize=20)
			#plt.ylim([0,1])
			#plt.xlim([0,11000])
			plt.title("Tr (SUBSTRATE)")
			#l=plt.legend(loc=1, fontsize=15)
			#l.draw_frame(False)

			string_3 = ''.join([self.folder_str, self.filename_str,'_Tr(subRAW)_',self.timestr, '.png'])
			if self.save_figs==True:
				plt.savefig(string_3)
				pass_plots.extend([string_3])
			
			string_4 = ''.join([string_3[:-3],'txt'])
			with open(string_4, 'w') as thefile:
				thefile.write(''.join(['This data is constructed from the config file ', self.config_file, '\n']))
				thefile.write('Column 1: wavelength in nm\n')
				thefile.write('Column 2: energy in eV\n')
				thefile.write('Column 3: Tr (subRAW)\n')
				
				for tal0,tal1,tal2 in zip(1239.84187/x_all_Ts,x_all_Ts,y_all_Ts):
					thefile.write(''.join([str(tal0),'\t',str(tal1),'\t',str(tal2),'\n']))
		
			pass_plots.extend([string_4])
		
		return pass_plots


	def make_plots(self):
		
		x_all, y_all = self.combined_Tr()
		indicies, comax_alph_TalTalflat, com_axisTminTmax_final, all_extremas = self.get_T_alpha()
		
		extremas_first, extremas_final, extremas_flatten = all_extremas
		common_xaxis, Tmin, Tmax = com_axisTminTmax_final
		common_xaxis_alpha, T_alpha, T_alpha_flatten = comax_alph_TalTalflat
		indx_start, indx_end = indicies 

		x_min, y_min, x_max, y_max=[extremas_first[:][0],extremas_first[:][1],extremas_first[:][2],extremas_first[:][3]]
		x_min_, y_min_, x_max_, y_max_=[extremas_final[:][0],extremas_final[:][1],extremas_final[:][2],extremas_final[:][3]]
		x_min__, y_min__, x_max__, y_max__=[extremas_flatten[:][0],extremas_flatten[:][1],extremas_flatten[:][2],extremas_flatten[:][3]]
		
		########################################################################
		pass_plots=[]
	
		plt.figure(figsize=(15,10))
		
		if self.plot_X=='eV':
			plt.plot(x_min, y_min, 'r-', label = "T_min first")
			plt.plot(x_max, y_max, 'b-', label = "T_max first")
			plt.plot(x_min_, y_min_, 'r--', label = "T_min final")
			plt.plot(x_max_, y_max_, 'b--', label = "T_max final")
			plt.plot(x_all,y_all,'k-', label = "T_raw data")
			plt.plot(common_xaxis_alpha,T_alpha,'m-', label = "T_alpha")
			plt.plot(x_all[indx_end+1:], y_all[indx_end+1:], 'co', label = ''.join(['T_alpha (', self.fit_linear_spline,')']))
			string_lab1 = ''.join(['T_min interp (', self.fit_linear_spline , ')'])
			plt.plot(common_xaxis, Tmin, 'ro--', label = string_lab1)
			string_lab2 = ''.join(['T_max interp (', self.fit_linear_spline , ')'])
			plt.plot(common_xaxis, Tmax, 'bo--', label = string_lab2)
			plt.xlabel("E, eV", fontsize=20)
			
		elif self.plot_X=='nm':
			plt.plot(1239.84187/numpy.array(x_min), y_min, 'r-', label = "T_min first")
			plt.plot(1239.84187/numpy.array(x_max), y_max, 'b-', label = "T_max first")
			plt.plot(1239.84187/numpy.array(x_min_), y_min_, 'r--', label = "T_min final")
			plt.plot(1239.84187/numpy.array(x_max_), y_max_, 'b--', label = "T_max final")
			plt.plot(1239.84187/x_all,y_all,'k-', label = "T_raw data")
			plt.plot(1239.84187/numpy.array(common_xaxis_alpha),T_alpha,'m-', label = "T_alpha")
			plt.plot(1239.84187/x_all[indx_end+1:], y_all[indx_end+1:], 'co', label = ''.join(['T_alpha (', self.fit_linear_spline,')']))
			string_lab1 = ''.join(['T_min interp (', self.fit_linear_spline , ')'])
			plt.plot(1239.84187/numpy.array(common_xaxis), Tmin, 'ro--', label = string_lab1)
			string_lab2 = ''.join(['T_max interp (', self.fit_linear_spline , ')'])
			plt.plot(1239.84187/numpy.array(common_xaxis), Tmax, 'bo--', label = string_lab2)
			plt.xlabel("Wavelength, nm", fontsize=20)
			
		plt.ylabel("Tr", fontsize=20)
		plt.tick_params(axis="both", labelsize=20)
		#plt.ylim([0,1])
		#plt.xlim([0,4])
		l=plt.legend(loc=1, fontsize=15)
		l.draw_frame(False)

		if self.save_figs==True:
			string_2 = ''.join([self.folder_str, self.filename_str,'_Tr_subfilm (', self.fit_linear_spline , ')_',self.timestr, '.png'])
			plt.savefig(string_2)
			pass_plots.extend([string_2])

		########################################################################
		
		x_Ts, y_Ts = self.fit_Ts_to_data(common_xaxis)
		
		plt.figure(figsize=(15,10))
		
		if self.plot_X=='eV':
			plt.plot(x_Ts,y_Ts,'k-')
			plt.xlabel("E, eV", fontsize=20)
			
		elif self.plot_X=='nm':
			plt.plot(1239.84187/numpy.array(x_Ts),y_Ts,'k-')
			plt.xlabel("Wavelength, nm", fontsize=20)
			
		plt.ylabel("Tr", fontsize=20)
		plt.tick_params(axis="both", labelsize=20)
		#plt.ylim([0,1])
		#plt.xlim([0,11000])
		plt.title("Tr (SUBSTRATE) for selected [Tmin, Tmax] region")
		#l=plt.legend(loc=1, fontsize=15)
		#l.draw_frame(False)
		
		if self.save_figs==True:
			string_3 = ''.join([self.folder_str, self.filename_str,'_Tr_sub (', self.fit_linear_spline , ')_',self.timestr, '.png'])
			plt.savefig(string_3)
			pass_plots.extend([string_2])
		
		########################################################################
		
		plt.figure(figsize=(15,10))
		if self.plot_X=='eV':
			plt.plot(common_xaxis_alpha,T_alpha_flatten,'k-', label = "T_alpha flatten")
			plt.plot(x_min__, y_min__, 'ro', label = "T_min flatten")
			plt.plot(x_max__, y_max__, 'bo', label = "T_max flatten")
			plt.xlabel("E, eV", fontsize=20)
			
		elif self.plot_X=='nm':
			plt.plot(1239.84187/numpy.array(common_xaxis_alpha),T_alpha_flatten,'k-', label = "T_alpha flatten")
			plt.plot(1239.84187/numpy.array(x_min__), y_min__, 'ro', label = "T_min flatten")
			plt.plot(1239.84187/numpy.array(x_max__), y_max__, 'bo', label = "T_max flatten")
			plt.xlabel("Wavelength, nm", fontsize=20)
			
		plt.ylabel("Tr", fontsize=20)
		plt.tick_params(axis="both", labelsize=20)
		#plt.yticks( numpy.linspace(0,1,11) )
		#plt.xticks( numpy.linspace(0,11000,12) )
		#plt.ylim([0,1])
		#plt.xlim([0,4])
		l=plt.legend(loc=1, fontsize=15)
		l.draw_frame(False)
		
		if self.save_figs==True:
			string_4 = ''.join([self.folder_str, self.filename_str,'_Tr_flatten (', self.fit_linear_spline , ')_',self.timestr, '.png'])
			plt.savefig(string_4)
			pass_plots.extend([string_4])
		
		return pass_plots
	
	def show_plots(self):
		
		plt.show()


if __name__ == "__main__":
	
	get_class=Get_TM_Tm()
	get_class.plot_raw()
	get_class.make_plots()
	get_class.show_plots()
	
	
	