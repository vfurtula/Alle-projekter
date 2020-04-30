## Import libraries
import matplotlib.pyplot as plt
import numpy as np
import os, sys

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

inFile = sys.argv[1]
params = __import__(inFile)

raw_olis=params.raw_olis
raw_ftir=params.raw_ftir

sub_olis=params.sub_olis
sub_ftir=params.sub_ftir

fit_linear_spline=params.fit_linear_spline

read_min_max_txtfile=params.read_min_max_txtfile
read_d_mean_txtfile=params.read_d_mean_txtfile

Expected_Substrate_Dev=params.Expected_Substrate_Dev
gaussian_factors=params.gaussian_factors
gaussian_borders=params.gaussian_borders

index_m1_sections=params.index_m1_sections
num_periods=params.num_periods

iterations=params.iterations
strong_abs_start_eV=params.strong_abs_start_eV

fit_poly_order=params.fit_poly_order
fit_poly_ranges=params.fit_poly_ranges

read_data_folder = params.read_data_folder
save_analysis_folder = params.save_analysis_folder

'''
#############################
# USER OPTIONS - EDIT START # 
#############################

# film+substrate measurements
raw_olis = 'ek062-4'
raw_ftir = 'ek062-4'

# substrate measurements only
sub_olis = 'BareSapphire3b'
sub_ftir = 'sapphire 3 matt'

# perform interpolation using one of the following two arguments: 
# 'linear' or 'spline'
fit_linear_spline = 'linear'

# here you can edit the min_max text file after reviewing first graph in Get_TM_Tm.py
# first check min and max extremas without editing the min_max text file
# the input argument is either 'yes' or 'no'.
read_min_max_txtfile = 'no'

# here you can edit the d_mean text file (a single value) but first make sure the
# textfile with d_mean value exists. The input argument is either 'yes' or 'no'.
read_d_mean_txtfile = 'no'

# expected deviation in the substrate transmission measurements in decimal (percent/100)
# alternatively leave it blank or '0.0'
Expected_Substrate_Dev = 0.0

# gaussian factor parameters required for extrema point selection
# high gauissian fector = broadband noise filtering
# low gauissian fector = narrowband noise filtering
# as an example 4 gaussian factors means division of the spectrum in 4 parts
gaussian_factors = [6.5, 1.5, 1.0, 0.0]

# the brake points of the spectrum in electronVolts [eV]
# the length of this list should be larger than gaussian_factors by 1
gaussian_borders = [0.495, 0.6, 0.80, 1.6, 3.2]

# calculation of index m1, include following sections
# empty brackets means all points included
index_m1_sections = [1,1.65]

# Here you can extend the searching range for extremas where 1 period is given by distance
# between two last maxima points (or minima). The extended range is relative to extremas found 
# without applying the carrier function T_alpha.
num_periods = 2
iterations = 2

# extend the number of data points with additional points the strong absorption region 
# to find alpha and k in the strong absorption region
strong_abs_start_eV = '3.4'

# set order of the polyfit function that will determine extraploated refractive index points
fit_poly_order = 4

# set accepted ranges of the polyfit function in eV. You can set several ranges, they need to be in
# ascending order
fit_poly_ranges = [0.6, 0.95, 1.5, 2.5]

###########################
# USER OPTIONS - EDIT END # 
###########################
'''


###################################
# Create folders to save the data # 
###################################

# folder where all raw data is placed (program input)
if not read_data_folder:
  data_folder = ''
else:
  data_folder = ''.join([ read_data_folder, '/' ])

timestr = time.strftime("%Y%m%d-%H%M%S")

# create a folder where all post-processed data and graphs will be saved
# but first check if the folder exists
if not save_analysis_folder:
  analysis_folder = ''
else:
  analysis_folder = ''.join([save_analysis_folder, '/'])
  if not os.path.isdir(save_analysis_folder):
    os.mkdir(save_analysis_folder)


#####################
# START OF THE CODE #
#####################

def get_control_file():
  return inFile

def get_read_min_max_txtfile():
  return read_min_max_txtfile

def get_read_d_mean_txtfile():
  return read_d_mean_txtfile

def get_Expected_Substrate_Dev():
  return Expected_Substrate_Dev

def get_method():
  return fit_linear_spline

def gaussian_parameters():
  return gaussian_borders, gaussian_factors, num_periods, iterations

def str_abs_params():
  return strong_abs_start_eV, fit_poly_order, fit_poly_ranges

def folders_and_data():
  #print 'method folders_and_method runs...'
  return analysis_folder, data_folder, raw_olis, raw_ftir, sub_olis, sub_ftir

def ig_po():
  #print 'method ig_po runs...'
  return index_m1_sections

###########################################################################
# Data from FTIR and OLIS: find Tm and TM (m=min, M=max) in Swanepoel1983 # 
###########################################################################

def get_olis_data(my_string):
  #print 'method get_olis_data runs...'

  # Open new datafile form SOURCE 2 (OLIS)

  # Read and ignore header lines
  #header1 = f2.readline()

  data2_eV=[]
  data2_tr=[]
  # Read new datafile
  with open(my_string, 'r') as f2:
    for lines in f2:
      #line = line.strip()
      columns = lines.split()
      data2_eV.extend([ 1239.84187/float(columns[0]) ]) # energy in eV
      data2_tr.extend([ float(columns[1] )])
      
  #plt.figure(figsize=(15,10))
  #plt.plot(data2_eV, data2_tr)
  #plt.xlabel("E, eV", fontsize=20)
  #plt.ylabel("T_r olis", fontsize=20)
  #plt.show()
  return data2_eV[::-1], data2_tr[::-1]

def get_ftir_data(my_string):
  #print 'method get_ftir_data runs...'

  # Open new datafile from SOURCE 1 (FTIR)
  # Raw FTIR data has complicated structure, severeal vales for a single wavelength
  #my_string='EK033-3.DPT'

  # Read and ignore header lines
  #header1 = f1.readline()

  data_eV=[]
  data_tr=[]

  # Read new datafile
  with open(my_string,'r') as f1:
    for line in f1:
      #line = line.strip()
      columns = line.split()
      data_eV.extend([ 1239.84187/(1000*float(columns[0])) ]) # energy in eV
      data_tr.extend([ float(columns[1]) ])
      
  # Determine no. of repetitions for each sweeped wavelength (mostly 4 or 5 for FTIR)
  d3=[len(list(group)) for key, group in groupby(data_eV)]

  avg=[]
  shortlist_eV=[]
  stdev_mag=[] 
  
  for tal in range(len(d3)):
    d4=sum(d3[0:tal])
    d5=sum(d3[0:tal+1])
    
    # Y axis enteries
    avg.extend([ sum(data_tr[d4:d5])/d3[tal] ])
    # X axis enteries
    shortlist_eV.extend([ data_eV[d5-1] ]) # energy in eV
    # Python sample std dev calculated by the statistics module
    stdev_mag.extend([ sum(data_tr[d4:d5])/len(data_tr[d4:d5]) ])

  #plt.figure(figsize=(15,10))
  #plt.plot(shortlist_eV, avg)
  #plt.xlabel("E, eV", fontsize=20)
  #plt.ylabel("T_r ftir", fontsize=20)
  #plt.show()
  return shortlist_eV[::-1], avg[::-1]

def combined_Tr():
  #print 'method combined_Tr runs...'
  
  if not raw_olis:
    string_ftir = ''.join([data_folder, raw_ftir, '.DPT'])
    shortlist_eV, avg = get_ftir_data(string_ftir)
    x_all = shortlist_eV
    y_all = avg
    
  elif not raw_ftir: 
    string_olis = ''.join([data_folder, raw_olis, '.asc'])
    data2_eV, data2_tr = get_olis_data(string_olis)
    x_all = data2_eV
    y_all = data2_tr
    
  else:
    string_olis = ''.join([data_folder, raw_olis, '.asc'])
    data2_eV, data2_tr = get_olis_data(string_olis)

    string_ftir = ''.join([data_folder, raw_ftir, '.DPT'])
    shortlist_eV, avg = get_ftir_data(string_ftir)

    index_1=np.argmin(np.abs(np.array(data2_eV)-shortlist_eV[-1]))
    #index_1 = min(range(len(data2_eV)), key=lambda i: abs(data2_eV[i]-shortlist_eV[-1]))

    x_olis = data2_eV[index_1+1:]
    y_olis = data2_tr[index_1+1:]

    x_all = shortlist_eV+x_olis
    y_all = avg+y_olis
  
  #plt.figure(figsize=(15,10))
  #plt.plot(x_all, y_all)
  #plt.xlabel("E, eV", fontsize=20)
  #plt.ylabel("T_r combined", fontsize=20)
  #plt.show()
  return x_all, y_all

########################################################################

class Tsub:
  
  def __init__(self,num):
    # num is the expected deviation in decimal (percent/100) from the sub transmission data
    
    if not sub_olis:
      string_ftir = ''.join([data_folder, sub_ftir, '.DPT'])
      data_eV_f, data_ts_f = get_ftir_data(string_ftir)
      self.x_all = data_eV_f
      self.y_all = [ii*(1+num) for ii in data_ts_f]
      
    elif not sub_ftir:
      string_olis = ''.join([data_folder, sub_olis, '.asc'])
      data_eV_o, data_ts_o = get_olis_data(string_olis)
      self.x_all = data_eV_o
      self.y_all = [ii*(1+num) for ii in data_ts_o]
      
    else:
      string_olis = ''.join([data_folder, sub_olis, '.asc'])
      data_eV_o, data_ts_o = get_olis_data(string_olis)

      string_ftir = ''.join([data_folder, sub_ftir, '.DPT'])
      data_eV_f, data_ts_f = get_ftir_data(string_ftir)
      
      index_1=np.argmin(np.abs(np.array(data_eV_o)-data_eV_f[-1]))
      #index_1 = min(range(len(data_eV_o)), key=lambda i: abs(data_eV_o[i]-data_eV_f[-1]))

      x_olis = data_eV_o[index_1+1:]
      y_olis = data_ts_o[index_1+1:]

      self.x_all = data_eV_f+x_olis
      #self.y_all = data_ts_f+y_olis
      self.y_all = [i_*(1+num) for i_ in data_ts_f]+[ii_*(1+num) for ii_ in y_olis]
      
  def combined_Ts(self):
    #print 'method combined_Ts runs...'
    
    return self.x_all, self.y_all

  def fit_Ts_to_data(self,my_string):
    #print 'method fit_Ts_to_data runs...'
    
    if my_string=='linear':
      common_xaxis, Tmin, Tmax = Ext_interp(my_string).interp_T()
      f = interpolate.splrep(self.x_all, self.y_all, k=1, s=0)
      
    elif my_string=='spline':
      common_xaxis, Tmin, Tmax = Ext_interp(my_string).interp_T()
      f = interpolate.splrep(self.x_all, self.y_all, k=3, s=0)
      
    else:
      raise ValueError('Interpolation should be linear or spline!')
    
    fit_yaxis = interpolate.splev(common_xaxis, f, der=0)
    
    return common_xaxis, fit_yaxis

########################################################################

class Ext_interp:
  
  def __init__(self,my_string):
    
    self.indicies, self.comax_alph_TalTalflat, self.com_axisTminTmax_first, self.com_axisTminTmax_final, self.all_extremas = \
      ge.Find_extrema().get_T_alpha(my_string, num_periods, iterations)
    

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

if __name__ == "__main__":

  x_all, y_all = combined_Tr()
  
  method = fit_linear_spline
  ese = get_Expected_Substrate_Dev()
  ext = Ext_interp(method)
  x_min, y_min, x_max, y_max = ext.extremas() 
  common_xaxis, Tmin, Tmax = ext.interp_T()
  
  ########################################################################   

  # Plot the results
  fig=plt.figure(1, figsize=(15,10))
  plt.plot(x_all,y_all,'k-', label = "T_raw data")
  plt.plot(x_min, y_min, 'ro', label = "Min")
  plt.plot(x_max, y_max, 'bo', label = "Max")
  plt.xlabel("E, eV", fontsize=20)
  plt.ylabel("T_r", fontsize=20)
  plt.tick_params(axis="both", labelsize=20)
  #plt.yticks( np.linspace(0,1,11) )
  #plt.xticks( np.linspace(0,11000,12) )
  #plt.ylim([0,1])
  plt.xlim([0,4])
  l=plt.legend(loc=1, fontsize=15)
  l.draw_frame(False)

  if not raw_olis:
    string_1 = ''.join([analysis_folder,raw_ftir,'_Tr_',timestr,'.png'])
  else:
    string_1 = ''.join([analysis_folder,raw_olis,'_Tr_',timestr,'.png'])
  plt.savefig(string_1)
  plt.show()
    
  ########################################################################

  plt.figure(2, figsize=(15,10))
  plt.plot(x_min, y_min, 'r-', label = "T_min")
  plt.plot(x_max, y_max, 'b-', label = "T_max")
  plt.plot(x_all,y_all,'k-', label = "T_raw data")
  string_lab1 = ''.join(['T_min interp(', method , ')'])
  plt.plot(common_xaxis, Tmin, 'ro--', label = string_lab1)
  string_lab2 = ''.join(['T_max interp(', method , ')'])
  plt.plot(common_xaxis, Tmax, 'bo--', label = string_lab2)

  plt.xlabel("E, eV", fontsize=20)
  plt.ylabel("T_r", fontsize=20)
  plt.tick_params(axis="both", labelsize=20)
  #plt.ylim([0,1])
  plt.xlim([0,4])
  l=plt.legend(loc=1, fontsize=15)
  l.draw_frame(False)
  
  if not raw_olis:
    string_2 = ''.join([analysis_folder, raw_ftir, '_Tr_interp(', method , ')_',timestr, '.png'])
  else:
    string_2 = ''.join([analysis_folder, raw_olis, '_Tr_interp(', method , ')_',timestr, '.png'])
  plt.savefig(string_2)
  plt.show()
  
  ########################################################################
  
  if not raw_olis:
    string_lab1 = ''.join(['sub files = ', sub_ftir, '.DPT'])
  elif not raw_ftir:
    string_lab1 = ''.join(['sub files = ', sub_olis, '.asc'])
  else:
    string_lab1 = ''.join(['sub files = ', sub_olis, '.asc + ', sub_ftir, '.DPT'])
  
  if not ese or float(ese)==0.0:
    tsub_noe = Tsub(0.0)
    xxx, yyy = tsub_noe.fit_Ts_to_data(method)
    #tsub_up=Tsub(ese)
    #xxx_, yyy_ = tsub_up.fit_Ts_to_data(method)
    #tsub_down=Tsub(-ese)
    #xxx__, yyy__ = tsub_down.fit_Ts_to_data(method)
    plt.figure(3, figsize=(15,10))
    plt.plot(xxx,yyy,'ro-', label = string_lab1)
    
  else:
    tsub_noe = Tsub(0.0)
    xxx, yyy = tsub_noe.fit_Ts_to_data(method)
    tsub_up=Tsub(float(ese))
    xxx_, yyy_ = tsub_up.fit_Ts_to_data(method)
    tsub_down=Tsub(-float(ese))
    xxx__, yyy__ = tsub_down.fit_Ts_to_data(method)
    
    plt.figure(3, figsize=(15,10))
    plt.plot(xxx,yyy,'ro-', label = string_lab1)
    plt.fill_between(xxx, yyy_, yyy__, facecolor='red', alpha=0.2)
    
  plt.xlabel("E, eV", fontsize=20)
  plt.ylabel("T_r,sub", fontsize=20)
  plt.tick_params(axis="both", labelsize=20)
  #plt.ylim([0,1])
  #plt.xlim([0,11000])
  l=plt.legend(loc=1, fontsize=15)
  l.draw_frame(False)

  if not raw_olis:
    string_3 = ''.join([analysis_folder, raw_ftir, '_', sub_ftir, '_', method, '_',timestr, '.png'])
  else:
    string_3 = ''.join([analysis_folder, raw_olis, '_', sub_olis, '_', method, '_',timestr, '.png'])
  plt.savefig(string_3)
  plt.show()
  

