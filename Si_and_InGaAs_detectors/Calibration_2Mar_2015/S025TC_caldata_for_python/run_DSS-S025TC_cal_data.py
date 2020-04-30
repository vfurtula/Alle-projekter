## Import libraries
import matplotlib.pyplot as plt
import numpy as np
from numpy.polynomial import polynomial as P
from scipy import interpolate

## For Matplotlib fonts
from matplotlib import rc
## for LaTeX style use:
rc("text", usetex=True)
rc("font", family="serif")

######################################################
# Create folder structure for intput and output data # 
######################################################

class Get_DSS_S025TC_new:
  
  def __init__(self,my_string):
    # Open new datafile form SOURCE 2 (OLIS)
    #my_string='Kalibrering_DSS-S025TC.txt'
    #step=5
    
    f2 = open(my_string, 'r')

    # Read and ignore header lines
    headers = [f2.readline() for i in range(7)]

    self.all_data=[]
    # Read new datafile
    for line in f2:
      line = line.strip()
      columns = line.split()
      self.all_data.extend([ float(columns[0]) ])
      
    f2.close()

    self.wl_indx=[]
    self.res_m30C_indx=[]
    self.err_m30C_indx=[]
    self.res_p23C_indx=[]
    self.err_p23C_indx=[]
    
    self.wl=[]
    self.res_m30C=[]
    self.err_m30C=[]
    self.res_p23C=[]
    self.err_p23C=[]
    
  def getdata(self):
    for i in range(len(self.all_data)):
      if i*5<len(self.all_data):
	self.wl_indx.extend([ i*5 ])
      if 1+i*5<len(self.all_data):
	self.res_m30C_indx.extend([ 1+i*5 ])
      if 2+i*5<len(self.all_data):
	self.err_m30C_indx.extend([ 2+i*5 ])
      if 3+i*5<len(self.all_data):
	self.res_p23C_indx.extend([ 3+i*5 ])
      if 4+i*5<len(self.all_data):
	self.err_p23C_indx.extend([ 4+i*5 ])
	
    for i in range(len(self.wl_indx)):
      self.wl.extend([ self.all_data[self.wl_indx[i]] ])
      self.res_m30C.extend([ self.all_data[self.res_m30C_indx[i]] ])
      self.err_m30C.extend([ self.all_data[self.err_m30C_indx[i]] ])
      self.res_p23C.extend([ self.all_data[self.res_p23C_indx[i]] ])
      self.err_p23C.extend([ self.all_data[self.err_p23C_indx[i]] ])
      
    return self.wl, self.res_m30C, self.err_m30C, self.res_p23C, self.err_p23C


class Get_DSS_S025TC_old:
  
  def __init__(self,my_string):
    # Open new datafile form SOURCE 2 (OLIS)
    #my_string='Kalibrering_DSS-S025TC_HORIBA.txt'
    
    f2 = open(my_string, 'r')
    # Read and ignore header lines
    headers = [f2.readline() for i in range(3)]

    self.wl=[]
    self.res_m30C=[]
    self.res_p22C=[]
    # Read new datafile
    for line in f2:
      line = line.strip()
      columns = line.split()
      self.wl.extend([ float(columns[0]) ])
      self.res_m30C.extend([ float(columns[2]) ])
      self.res_p22C.extend([ float(columns[1]) ])
        
    f2.close()
    
  def getdata(self):
     
    return self.wl, self.res_m30C, self.res_p22C

if __name__ == "__main__":  
  
  out_data1=Get_DSS_S025TC_new('Kalibrering_DSS-S025TC.txt').getdata()
  out_data2=Get_DSS_S025TC_old('Kalibrering_DSS-S025TC_HORIBA.txt').getdata()
  out_data3=Get_DSS_S025TC_new('Kalibrering_DSS-S025TC_crosscheck.txt').getdata()
  
  '''  
  coef_first = P.polyfit(true_val,Ard_baud_23040,1)
  #print "polyfit coef = ", coef
  a1=coef_first[1]
  b1=coef_first[0]
  val_first = [a1*i+b1 for i in true_val]

  coef_second = P.polyfit(true_val,Ard_baud_23040,2)
  #print "polyfit coef = ", coef
  a2=coef_second[2]
  b2=coef_second[1]
  c2=coef_second[0]
  val_second = [a2*i**2+b2*i+c2 for i in true_val]


  delta1=[]  
  delta2=[]
  for i in range(len(true_val)):
    if i==0:
      delta1.extend([ 1 ])
      delta2.extend([ 1 ])
    else:
      delta1.extend([ Ard_baud_23040[i]/true_val[i] ])
      delta2.extend([ Ard_baud_230400[i]/true_val[i] ])

  f2.close()
  '''

  # Plot the results
  plt.figure(1, figsize=(18,12))
  
  plt.plot(out_data1[0],out_data1[1],'b-',label="-30C, JV, 5 nm step (supply 031113-2)")
  up_err_m30=[out_data1[1][i]*(1+out_data1[2][i]/100) for i in range(len(out_data1[1]))]
  do_err_m30=[out_data1[1][i]*(1-out_data1[2][i]/100) for i in range(len(out_data1[1]))]
  plt.fill_between(out_data1[0], up_err_m30, do_err_m30, facecolor='blue', alpha=0.3)
  
  plt.plot(out_data1[0],out_data1[3],'r-',label="+23C, JV, 5 nm step (supply 031113-2)")
  up_err_p23=[out_data1[3][i]*(1+out_data1[4][i]/100) for i in range(len(out_data1[3]))]
  do_err_p23=[out_data1[3][i]*(1-out_data1[4][i]/100) for i in range(len(out_data1[3]))]
  plt.fill_between(out_data1[0], up_err_p23, do_err_p23, facecolor='red', alpha=0.3)
  
  
  plt.plot(out_data2[0],out_data2[1],'b--',label="-30C, HORIBA, Oct 2010 (supply unknown)")
  plt.plot(out_data2[0],out_data2[2],'r--',label="+22C, HORIBA, Oct 2010 (supply unknown)")
  
  ###
  
  plt.plot(out_data3[0],out_data3[1],'bx-',label="-30C, JV, 100 nm step (supply 041004-1)")
  #up_err_m30=[out_data3[1][i]*(1+out_data3[2][i]/100) for i in range(len(out_data3[1]))]
  #do_err_m30=[out_data3[1][i]*(1-out_data3[2][i]/100) for i in range(len(out_data3[1]))]
  #plt.fill_between(out_data3[0], up_err_m30, do_err_m30, facecolor='yellow', alpha=0.3)
  
  plt.plot(out_data3[0],out_data3[3],'rx-',label="+23C, JV, 100 nm step (supply 041004-1)")
  #up_err_p23=[out_data3[3][i]*(1+out_data3[4][i]/100) for i in range(len(out_data3[3]))]
  #do_err_p23=[out_data3[3][i]*(1-out_data3[4][i]/100) for i in range(len(out_data3[3]))]
  #plt.fill_between(out_data3[0], up_err_p23, do_err_p23, facecolor='green', alpha=0.3)
  
  plt.xlabel("Wavelength [nm]", fontsize=20)
  plt.ylabel("Responsivity [A/W]", fontsize=20)
  plt.tick_params(axis="both", labelsize=20)
  plt.title('Calibration of DSS-S025TC (Serial No. 021113-2) at Justervesenet (JV), Jan 2015')
  #plt.yticks( np.linspace(0,1,11) )
  #plt.xticks( np.linspace(0,11000,12) )
  #plt.ylim([0,1])
  #plt.xlim([0,11000])
  l=plt.legend(loc=2, fontsize=15)
  l.draw_frame(False)

  plt.savefig('DSS-S025TC_calplots.pdf')
  plt.show()  

