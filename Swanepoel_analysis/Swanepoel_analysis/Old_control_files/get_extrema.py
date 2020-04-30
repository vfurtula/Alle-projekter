## Import libraries
import matplotlib.pyplot as plt
import numpy
import os, sys

import time, math
from itertools import groupby
from scipy.ndimage import filters as fi
from scipy.interpolate import interp1d
from scipy.signal import argrelextrema
from scipy import interpolate
import Get_TM_Tm_v0
from numpy.polynomial import polynomial as P

class Find_extrema:
	
	def __init__(self):
		
		gtt=Get_TM_Tm_v0.Get_TM_Tm()
		self.x_all, self.y_all = gtt.combined_Tr()
		
		self.folder_str, self.filename_str, self.raw_olis, self.raw_ftir, self.sub_olis, self.sub_ftir, self.timestr=gtt.folders_and_data()
		self.fit_linear_spline = gtt.get_method()
		
		sections, gaussian_factors, num_periods, iterations = gtt.gaussian_parameters()
		self.gf = gaussian_factors
		self.se = sections
		self.np = num_periods
		self.its = iterations

	def extrema(self,x_all,y_all):
	  #print 'method extremas runs...'
	  
	  if len(self.se)<2 or len(self.gf)<1:
	    raise ValueError('You need at least one section for analysis!') 
	  elif len(self.se)!=len(self.gf)+1:
	    raise ValueError('The number of section brake points is not supporting the number of Gaussian factors!') 
	  
	  # Find the correct indicies for the gaussian filter
	  brake_ind=[]
	  for i in self.se:
	    brake_ind.extend([ numpy.argmin(numpy.abs(numpy.array(x_all)-i)) ])
	  
	  # Perform gaussian filtering in order to remove noise
	  GaussFilt=[]
	  for i in range(len(self.gf)):
	    GaussFilt.extend( fi.gaussian_filter1d(y_all[brake_ind[i]:brake_ind[i+1]], self.gf[i], mode='nearest') )
	  
	  # Redefine x_all and y_all since we have cut out some of the original data
	  x_all_ = x_all[brake_ind[0]:brake_ind[-1]]
	  y_all_ = y_all[brake_ind[0]:brake_ind[-1]]

	  # Find the locations (indicies) of min and max
	  # for local maxima
	  max_loc=argrelextrema(numpy.array(GaussFilt), numpy.greater)[0]
	  
	  # and for local minima
	  min_loc=argrelextrema(numpy.array(GaussFilt), numpy.less)[0]
	    
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

	########################################################################

	def get_T_alpha(self):
		#print 'method get_T_alpha runs...'

		x_min, y_min, x_max, y_max = self.extrema(self.x_all,self.y_all)
		    
		# Find the extrema points and create a common x-axis
		common_xaxis, Tmin, Tmax = self.interp_T(x_min, y_min, x_max, y_max)

		extremas_first = [x_min, y_min, x_max, y_max]
		self.com_axisTminTmax_first=[common_xaxis, Tmin, Tmax]

		xmax_delta = abs(x_max[-2]-x_max[-1])
		go_right = x_max[-1]+self.np*xmax_delta

		indx_start=numpy.argmin(numpy.abs(numpy.array(self.x_all)-0.90*x_max[0]))
		#indx_start=0
		indx_end=numpy.argmin(numpy.abs(numpy.array(self.x_all)-go_right)) 

		'''
		indx_start=min(range(len(self.x_all)), key=lambda i: abs(self.x_all[i]-0.90*x_max[0])) 
		#indx_start=0
		indx_end=min(range(len(self.x_all)), key=lambda i: abs(self.x_all[i]-go_right))
		'''
    
		for iii in range(self.its):

			# Calculate T_alpha for the previously determined extrema points
			T_al=[math.sqrt(Tmax[i]*Tmin[i]) for i in range(len(common_xaxis))]
			# Create T_alpha x-axis and ADD interference-free points 
			common_xaxis_fit = numpy.append(common_xaxis,self.x_all[indx_end:])
			T_alpha_fit=numpy.append(T_al,self.y_all[indx_end:])
			# Perform spline to determine T_alpha in the newly found x-axis range

			if self.fit_linear_spline=='spline':
			  f=interpolate.splrep(common_xaxis_fit, T_alpha_fit, k=3, s=0)
			elif self.fit_linear_spline=='linear':
			  f=interpolate.splrep(common_xaxis_fit, T_alpha_fit, k=1, s=0)
			else:
				raise ValueError('Interpolation should be linear or spline') 

			common_xaxis_alpha = self.x_all[indx_start:indx_end]
			T_alpha = interpolate.splev(common_xaxis_alpha, f, der=0)
			# Substract T_alpha from the T_r in order to flatten out raw transmission data
			# and only to leave periodic oscillations 
			T_alpha_flatten=numpy.array(self.y_all[indx_start:indx_end])-numpy.array(T_alpha)
			      
			# Calculate NEW extrema points from the flatten curve
			x_min_, y_min_, x_max_, y_max_ = self.extrema(common_xaxis_alpha, T_alpha_flatten)

			extremas_flatten = [x_min_, y_min_, x_max_, y_max_]
			# Find correct indicies of NEW extrema points relative to the original T_r data 
			x_min, y_min, x_max, y_max = self.new_extremas(x_min_,x_max_)

			###########################################################
			# Overwrite the latest found values for x_min, y_min, x_max, y_max since editing 
			# min_max file is activited
			if not self.raw_olis:
			  string_1_ = ''.join([self.folder_str, self.filename_str, '_min_max_', self.fit_linear_spline, '.txt'])
			else:
			  string_1_ = ''.join([self.folder_str, self.filename_str, '_min_max_', self.fit_linear_spline, '.txt'])

			'''
			if not os.path.isdir(self.analysis_folder):
			  os.makedirs(self.analysis_folder)
			'''
			with open(string_1_, 'w') as thefile:
				thefile.write(''.join(['Interpolation method for Tmin and Tmax points is ', self.fit_linear_spline, '\n']))
				thefile.write(''.join(['The raw_olis data file is ', self.raw_olis, '\n']))
				thefile.write(''.join(['The raw_ftir data file is ', self.raw_ftir, '\n']))
				thefile.write(''.join(['The sub_olis data file is ', self.sub_olis, '\n']))
				thefile.write(''.join(['The sub_ftir data file is ', self.sub_ftir, '\n']))
				thefile.write('# Row 1:x_min,\t\t Row 2:y_min,\t\t Row 3:x_max,\t\t Row 4:y_max\n')
				
				for i in range(len(x_min)):
				  if i<len(x_min)-1:
				    thefile.write("%s\t" % x_min[i])
				  if i==len(x_min)-1:
				    thefile.write("%s\n" % x_min[i])
				    
				for i in range(len(y_min)):
				  if i<len(y_min)-1:
				    thefile.write("%s\t" % y_min[i])
				  if i==len(y_min)-1:
				    thefile.write("%s\n" % y_min[i])
				    
				for i in range(len(x_max)):
				  if i<len(x_max)-1:
				    thefile.write("%s\t" % x_max[i])
				  if i==len(x_max)-1:
				    thefile.write("%s\n" % x_max[i])
				  
				for i in range(len(y_max)):
				  if i<len(y_max)-1:
				    thefile.write("%s\t" % y_max[i])
				  if i==len(y_max)-1:
				    thefile.write("%s\n" % y_max[i])

			extremas_final = [x_min, y_min, x_max, y_max]
			
	    #####################################################################
	    
	  #extremas_final = [x_min, y_min, x_max, y_max]
	  # Find the common x-axis for extrema points and determine transmission values
		common_xaxis, Tmin, Tmax = self.interp_T(x_min, y_min, x_max, y_max)
	  
	  # Save the required data in new lists and make a return
		self.indicies = [indx_start, indx_end]
		self.comax_alph_TalTalflat = [common_xaxis_alpha, T_alpha, T_alpha_flatten]
		com_axisTminTmax_final=[common_xaxis, Tmin, Tmax]
		all_extremas = [extremas_first, extremas_final, extremas_flatten]
        
		return com_axisTminTmax_final, all_extremas

	def new_extremas(self, x_min, x_max):
		#print 'method new_extremas runs...'

		x_min_locs=[numpy.argmin(numpy.abs(numpy.array(self.x_all)-x_min[ii])) for ii in range(len(x_min))]
		x_max_locs=[numpy.argmin(numpy.abs(numpy.array(self.x_all)-x_max[ii])) for ii in range(len(x_max))]

		x_max_new=[]
		y_max_new=[]
		x_min_new=[]
		y_min_new=[]
		for x in x_max_locs:
		  x_max_new.extend([self.x_all[x]])
		  y_max_new.extend([self.y_all[x]]) # We use original data to identify all max points
		for x in x_min_locs:
		  x_min_new.extend([self.x_all[x]])
		  y_min_new.extend([self.y_all[x]]) # We use original data to identify all min points

		return x_min_new, y_min_new, x_max_new, y_max_new

	########################################################################

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
		      
		else: 
		  raise ValueError('Interpolation should be linear or spline!')

		Tmax = interpolate.splev(common_xaxis, fmax, der=0)
		Tmin = interpolate.splev(common_xaxis, fmin, der=0)

		return common_xaxis, Tmin, Tmax


	def make_plots(self):
	  
		com_axisTminTmax_final, all_extremas = self.get_T_alpha()

		indx_start, indx_end = self.indicies
		common_xaxis, Tmin, Tmax = self.com_axisTminTmax_first
		common_xaxis_, Tmin_, Tmax_ = com_axisTminTmax_final
		common_xaxis_alpha, T_alpha, T_alpha_flatten = self.comax_alph_TalTalflat
		extremas_first, extremas_final, extremas_flatten = all_extremas

		x_min, y_min, x_max, y_max = \
		  [extremas_first[:][0],extremas_first[:][1],extremas_first[:][2],extremas_first[:][3]]

		x_min_, y_min_, x_max_, y_max_ = \
		  [extremas_final[:][0],extremas_final[:][1],extremas_final[:][2],extremas_final[:][3]]

		x_min__, y_min__, x_max__, y_max__ = \
		  [extremas_flatten[:][0],extremas_flatten[:][1],extremas_flatten[:][2],extremas_flatten[:][3]]

		########################################################################
		# Plot the results
		fig=plt.figure(1, figsize=(15,10))
		plt.plot(self.x_all,self.y_all,'k-', label = "T_raw data")
		plt.plot(common_xaxis_alpha,T_alpha,'m-', label = "T_alpha")
		plt.plot(x_min_, y_min_, 'r-', label = "T_min_final")
		plt.plot(x_max_, y_max_, 'b-', label = "T_max_final")

		plt.plot(self.x_all[indx_end+1:], self.y_all[indx_end+1:], 'co', label = ''.join(['T_alphas for ', self.fit_linear_spline]))

		string_lab1 = ''.join(['T_min_final interp(', self.fit_linear_spline , ')'])
		plt.plot(common_xaxis_, Tmin_, 'ro--', label = string_lab1)
		string_lab2 = ''.join(['T_max_final interp(', self.fit_linear_spline , ')'])
		plt.plot(common_xaxis_, Tmax_, 'bo--', label = string_lab2)

		plt.title("With flattening correction applied!")
		plt.xlabel("E, eV", fontsize=20)
		plt.ylabel("T_r", fontsize=20)
		plt.tick_params(axis="both", labelsize=20)
		#plt.yticks( numpy.linspace(0,1,11) )
		#plt.xticks( numpy.linspace(0,11000,12) )
		#plt.ylim([0,1])
		plt.xlim([0,4])
		l=plt.legend(loc=1, fontsize=15)
		l.draw_frame(False)
		plt.show()  

		########################################################################
		# Plot the results
		fig=plt.figure(2, figsize=(15,10))
		plt.plot(common_xaxis_alpha,T_alpha_flatten,'k-', label = "T_alpha_flatten")
		plt.plot(x_min__, y_min__, 'ro', label = "T_min")
		plt.plot(x_max__, y_max__, 'bo', label = "T_max")
		plt.xlabel("E, eV", fontsize=20)
		plt.ylabel("T_alpha", fontsize=20)
		plt.tick_params(axis="both", labelsize=20)
		#plt.yticks( numpy.linspace(0,1,11) )
		#plt.xticks( numpy.linspace(0,11000,12) )
		#plt.ylim([0,1])
		plt.xlim([0,4])
		l=plt.legend(loc=1, fontsize=15)
		l.draw_frame(False)
		plt.show()
	  
  ########################################################################
    
if __name__ == "__main__":
	
	Find_extrema().make_plots()

  
  
  
