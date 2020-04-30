## Import libraries
import matplotlib.pyplot as plt
import os, sys, numpy
import config_Swanepoel

import time, math
from itertools import groupby
from scipy.ndimage import filters as fi
from scipy.interpolate import interp1d
from scipy import interpolate
import get_extrema as ge
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
		config_file = config_Swanepoel.current_config_file
		head, tail = os.path.split(config_file)
		sys.path.insert(0, head)
		cf_start = __import__(tail[:-3])
		
		# load all relevant parameters
		self.raw_olis = cf_start.loadSubFilmOlis_str
		self.raw_ftir = cf_start.loadSubFilmFTIR_str 
		self.sub_olis = cf_start.loadSubOlis_str
		self.sub_ftir = cf_start.loadSubFTIR_str
		
		self.fit_linear_spline=cf_start.fit_linear_spline
		self.num_periods=cf_start.num_periods
		self.iterations=cf_start.iterations
		self.Expected_Substrate_Dev=abs(cf_start.Expected_Substrate_Dev)
		self.strong_abs_start_eV=cf_start.strong_abs_start_eV
		self.gaussian_factors=cf_start.gaussian_factors
		self.gaussian_borders=cf_start.gaussian_borders
		self.index_m1_sections=cf_start.index_m1_sections
		self.fit_poly_order=cf_start.fit_poly_order
		self.fit_poly_ranges=cf_start.fit_poly_ranges
		
		self.filename_str=cf_start.filename
		self.folder_str=cf_start.save_analysis_folder
		self.timestr=cf_start.timestr
		
		# create a folder where all post-processed data and graphs will be saved
		# but first check if the folder exists
		if not self.folder_str:
			self.folder_str = ''
		else:
		  self.folder_str = ''.join([cf_start.save_analysis_folder, '/'])
		  if not os.path.isdir(cf_start.save_analysis_folder):
		    os.mkdir(cf_start.save_analysis_folder)

		if not self.filename_str:
			if not self.raw_olis:
				head, tail = os.path.split(self.raw_ftir)
				sys.path.insert(0, head)
				self.filename_str = tail[:-3]
			else:
				head, tail = os.path.split(self.raw_olis)
				sys.path.insert(0, head)
				self.filename_str = tail[:-3]

	#####################
	# START OF THE CODE #
	#####################

	def get_read_min_max_txtfile():
	  return read_min_max_txtfile

	def get_read_d_mean_txtfile():
	  return read_d_mean_txtfile

	def get_Expected_Substrate_Dev(self):
	  return self.Expected_Substrate_Dev

	def get_method(self):
	  return self.fit_linear_spline

	def gaussian_parameters(self):
	  return self.gaussian_borders, self.gaussian_factors, self.num_periods, self.iterations

	def str_abs_params(self):
	  return self.strong_abs_start_eV, self.fit_poly_order, self.fit_poly_ranges

	def folders_and_data(self):
	  #print 'method folders_and_method runs...'
	  return self.folder_str, self.filename_str, self.raw_olis, self.raw_ftir, self.sub_olis, self.sub_ftir

	def ig_po(self):
	  #print 'method ig_po runs...'
	  return self.index_m1_sections

	###########################################################################
	# Data from FTIR and OLIS: find Tm and TM (m=min, M=max) in Swanepoel1983 # 
	###########################################################################

	def get_olis_data(self,my_string):
		#print 'method get_olis_data runs...'

		# Open new datafile (.asc) form SOURCE 2 (OLIS)
		# Read and ignore header lines
		#header1 = f2.readline()
		data2_eV=numpy.array([])
		data2_tr=numpy.array([])

		# Read new datafile
		with open(my_string, 'r') as f2:
		  for lines in f2:
				#line = line.strip()
				columns = lines.split()
				data2_eV = numpy.append( data2_eV, [1239.84187/float(columns[0])] ) # energy in eV
				data2_tr = numpy.append( data2_tr, [float(columns[1])] )
				
		idx=numpy.argsort(data2_eV)
		data2_eV=data2_eV[idx]
		data2_tr=data2_tr[idx]
		
		return data2_eV, data2_tr

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

		if not self.raw_olis:
		  shortlist_eV, avg = self.get_ftir_data(self.raw_ftir)
		  x_all = shortlist_eV
		  y_all = avg
		  
		elif not self.raw_ftir:
			data2_eV, data2_tr = self.get_olis_data(self.raw_olis)
			x_all = data2_eV
			y_all = data2_tr
		  
		else:
			data2_eV, data2_tr = self.get_olis_data(self.raw_olis)
			shortlist_eV, avg = self.get_ftir_data(self.raw_ftir)

			index_1=numpy.argmin(numpy.abs(data2_eV-shortlist_eV[-1]))
			#index_1 = min(range(len(data2_eV)), key=lambda i: abs(data2_eV[i]-shortlist_eV[-1]))

			x_olis = data2_eV[index_1+1:]
			y_olis = data2_tr[index_1+1:]

			x_all = numpy.append(shortlist_eV,x_olis)
			y_all = numpy.append(avg,y_olis)
	  
		return x_all, y_all


	def combined_Ts(self,val):
		
		if not self.sub_olis:
		  data_eV_f, data_ts_f = get_ftir_data(self.sub_ftir)
		  x_all = data_eV_f
		  y_all = [ii*(1+val) for ii in data_ts_f]
		  
		elif not self.sub_ftir:
		  data_eV_o, data_ts_o = self.get_olis_data(self.sub_olis)
		  x_all = data_eV_o
		  y_all = [ii*(1+val) for ii in data_ts_o]
		  
		else:
			data_eV_o, data_ts_o = self.get_olis_data(self.sub_olis)
			data_eV_f, data_ts_f = self.get_ftir_data(self.sub_ftir)

			index_1=numpy.argmin(numpy.abs(numpy.array(data_eV_o)-data_eV_f[-1]))
			#index_1 = min(range(len(data_eV_o)), key=lambda i: abs(data_eV_o[i]-data_eV_f[-1]))

			x_olis = data_eV_o[index_1+1:]
			y_olis = data_ts_o[index_1+1:]

			x_all = numpy.append(data_eV_f,x_olis)
			#self.y_all = data_ts_f+y_olis
			y_all = numpy.append([i_*(1+val) for i_ in data_ts_f],[ii_*(1+val) for ii_ in y_olis])
			
		return x_all, y_all
	
	def fit_Ts_to_data(self,val):
		#print 'method fit_Ts_to_data runs...'

		x_all, y_all = self.combined_Ts(val)
		#self.ext_interp()

		if self.fit_linear_spline=='linear':
		  common_xaxis, Tmin, Tmax = self.interp_T()
		  f = interpolate.splrep(x_all, y_all, k=1, s=0)
		  
		elif self.fit_linear_spline=='spline':
		  common_xaxis, Tmin, Tmax = self.interp_T()
		  f = interpolate.splrep(x_all, y_all, k=3, s=0)
		  
		else:
		  raise ValueError('Interpolation should be linear or spline!')

		fit_yaxis = interpolate.splev(common_xaxis, f, der=0)

		return common_xaxis, fit_yaxis

########################################################################

	def ext_interp(self):
  
		self.indicies, self.comax_alph_TalTalflat, self.com_axisTminTmax_first, self.com_axisTminTmax_final, self.all_extremas=ge.Find_extrema().get_T_alpha()
    

	def extremas(self):
		#print 'method extremas runs...'

		extremas_first, extremas_final, extremas_flatten = self.all_extremas

		x_min, y_min, x_max, y_max = \
		  [extremas_final[:][0],extremas_final[:][1],extremas_final[:][2],extremas_final[:][3]]
		    
		return x_min, y_min, x_max, y_max
  
  ########################################################################

	def interp_T(self):
		#print interp_T runs...'

		common_xaxis_, Tmin_, Tmax_ = self.com_axisTminTmax_final
		    
		return common_xaxis_, Tmin_, Tmax_
  
  ########################################################################

	def make_plots(self):

		x_all, y_all = self.combined_Tr()

		self.ext_interp()
		self.x_min, self.y_min, self.x_max, self.y_max = self.extremas() 
		self.common_xaxis, self.Tmin, self.Tmax = self.interp_T()
		  
		########################################################################

		plt.figure(1, figsize=(15,10))
		plt.plot(self.x_min, self.y_min, 'r-', label = "T_min")
		plt.plot(self.x_max, self.y_max, 'b-', label = "T_max")
		plt.plot(x_all,y_all,'k-', label = "T_raw data")
		string_lab1 = ''.join(['T_min interp(', self.fit_linear_spline , ')'])
		plt.plot(self.common_xaxis, self.Tmin, 'ro--', label = string_lab1)
		string_lab2 = ''.join(['T_max interp(', self.fit_linear_spline , ')'])
		plt.plot(self.common_xaxis, self.Tmax, 'bo--', label = string_lab2)

		plt.xlabel("E, eV", fontsize=20)
		plt.ylabel("T_r", fontsize=20)
		plt.tick_params(axis="both", labelsize=20)
		#plt.ylim([0,1])
		plt.xlim([0,4])
		l=plt.legend(loc=1, fontsize=15)
		l.draw_frame(False)

		if not self.raw_olis:
		  string_2 = ''.join([self.folder_str, '_Tr_interp(', self.fit_linear_spline , ')_',self.timestr, '.png'])
		else:
		  string_2 = ''.join([self.folder_str, '_Tr_interp(', self.fit_linear_spline , ')_',self.timestr, '.png'])
		plt.savefig(string_2)
		plt.show()

		########################################################################

		if self.Expected_Substrate_Dev==0 or self.Expected_Substrate_Dev==0.0:
			
			xxx, y = self.fit_Ts_to_data(0.0)
			
			plt.figure(2, figsize=(15,10))
			plt.plot(xxx,y,'k-')
			plt.xlabel("E, eV", fontsize=20)
			plt.ylabel("T_r,sub", fontsize=20)
			plt.tick_params(axis="both", labelsize=20)
			#plt.ylim([0,1])
			#plt.xlim([0,11000])
			#l=plt.legend(loc=1, fontsize=15)
			#l.draw_frame(False)
		
		else:

			xxx, y_up = self.fit_Ts_to_data(self.Expected_Substrate_Dev)
			xxx, y = self.fit_Ts_to_data(0.0)
			xxx, y_low = self.fit_Ts_to_data(-self.Expected_Substrate_Dev)

			plt.figure(2, figsize=(15,10))
			plt.plot(xxx,y,'k-')
			plt.fill_between(xxx, y_up, y_low, facecolor='red', alpha=0.2)
			  
			plt.xlabel("E, eV", fontsize=20)
			plt.ylabel("T_r,sub", fontsize=20)
			plt.tick_params(axis="both", labelsize=20)
			#plt.ylim([0,1])
			#plt.xlim([0,11000])
			#l=plt.legend(loc=1, fontsize=15)
			#l.draw_frame(False)

		if not self.raw_olis:
		  string_3 = ''.join([self.folder_str,'_', self.fit_linear_spline, '_',self.timestr, '.png'])
		else:
		  string_3 = ''.join([self.folder_str,'_', self.fit_linear_spline, '_',self.timestr, '.png'])
		plt.savefig(string_3)
		plt.show()

if __name__ == "__main__":
	
	Get_TM_Tm().make_plots()