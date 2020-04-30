## Import libraries
import matplotlib.pyplot as plt
import numpy as np
import math
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

class Ref_typeB:
  def __init__(self,my_string,num):
    # Open new datafile form SOURCE 2 (OLIS)
    #my_string='Arduino_UNO_R3_voltage_calibration.txt'
    f2 = open(my_string, 'r')

    # Read and ignore header lines
    headers = [f2.readline() for i in range(num)]
    
    self.temp=[]
    self.volt=[]

    # Read new datafile
    for line in f2:
      line = line.strip()
      columns = line.split()
      self.temp.extend([ float(columns[0]) ])
      self.volt.extend([ float(columns[1]) ])
    f2.close()
    
    string_1 = ''.join([my_string,'_temp.txt'])
    # save data locally
    with open(string_1, 'w') as thefile:
      for ii in range(len(self.temp)):
	if ii == 0:
	  thefile.write("{%s, " % self.temp[ii])
	elif ii == len(self.temp)-1:
	  thefile.write("%s};" % self.temp[ii])
	else:
	  thefile.write("%s, " % self.temp[ii])
    
    string_2 = ''.join([my_string,'_muvolt.txt'])
    # save data locally
    with open(string_2, 'w') as thefile:
      for ii in range(len(self.volt)):
	if ii == 0:
	  thefile.write("{%s, " % self.volt[ii])
	elif ii == len(self.volt)-1:
	  thefile.write("%s};" % self.volt[ii])
	else:
	  thefile.write("%s, " % self.volt[ii])
  
    '''
    self.delta1=[]  
    self.delta2=[]
    for i in range(len(self.true_val)):
      if i==0:
	self.delta1.extend([ 1 ])
	self.delta2.extend([ 1 ])
      else:
	self.delta1.extend([ self.Ard_baud_23040[i]/self.true_val[i] ])
	self.delta2.extend([ self.Ard_baud_230400[i]/self.true_val[i] ]) 
    '''
  def get_data(self):
    
    return self.volt, self.temp
          
  def fit_data_to_poly(self,order):
    coefs = P.polyfit(self.volt, self.temp, order)
    print "polyfit coef = ", coefs    
    ny_temp = [np.poly1d(coefs[::-1])(i) for i in self.volt]
    
    return self.volt, ny_temp
  '''      
  def return_true_volt(self, volt):
    # make spline interpolation
    f1 = interpolate.splrep(self.true_val,self.delta1, s=0)
    f2 = interpolate.splrep(self.true_val,self.delta2, s=0)
    new_delta1 = interpolate.splev(volt, f1, der=0)
    new_delta2 = interpolate.splev(volt, f2, der=0)
    
    yaxis1_baud_23040 = [volt[i]/new_delta1[i] for i in range(len(volt))]
    yaxis2_baud_230400 = [volt[i]/new_delta2[i] for i in range(len(volt))]
    
    return yaxis1_baud_23040, yaxis2_baud_230400
  '''

if __name__ == "__main__":
  
  amc = Ref_typeB('Ard_mega2560(1V1)_calfile4.txt',4)
  bits, true_volt = amc.get_data()
  
  rb = Ref_typeB('Reftab_typeB.txt',6)
  volt, temp = rb.get_data()
  
  volt_, temp_  = rb.fit_data_to_poly(2)
  volt__, temp__  = rb.fit_data_to_poly(6)
  volt___, temp___  = rb.fit_data_to_poly(10)

  # Plot the results
  plt.figure(1, figsize=(15,10))
  plt.plot(volt, temp,'k-',label="Thermocouple data")
  plt.plot(volt_, temp_, 'r-',label="2nd order polyfit")
  plt.plot(volt__, temp__, 'b-',label="6th order polyfit")
  plt.plot(volt___, temp___, 'm-',label="10th order polyfit")
  #plt.plot(true_val,val_second,'r-',label="Parab. fit")
  plt.ylabel("Temp [C]", fontsize=20)
  plt.xlabel("Voltage [mV]", fontsize=20)
  plt.tick_params(axis="both", labelsize=20)
  #plt.yticks( np.linspace(0,1,11) )
  #plt.xticks( np.linspace(0,11000,12) )
  #plt.ylim([0,1])
  #plt.xlim([0,11000])
  l=plt.legend(loc=4, fontsize=15)
  l.draw_frame(False)
  #plt.savefig('thermocouple_polyfit.pdf')
  plt.show()
  
  # Here we assume constant calibration factor of x70 (amplification)
  # In true life it would be a function of applied voltage (volt)
  #ampl_volt=[ii*70 for ii in volt]
  
  #volt_bit_space=np.linspace(0,1100000,1024) #in microvolts
  bit_space=np.linspace(0,1023,1024)
  
  f1 = interpolate.splrep(bits, true_volt, k=1, s=0)
  volt_bit_space = interpolate.splev(bit_space, f1, der=0)
  
  # 1 bit = 1.075 mV assuming 1024 bits for 1.1V (Ref Voltage for MEGA2560)
  f2 = interpolate.splrep(volt, temp, k=1, s=0)
  temp_space = interpolate.splev(volt_bit_space, f2, der=0)
  # Check your results
  print temp_space[0]
  print temp_space[-1]
  
  #get_log_yaxis=[math.log(ii) for ii in np.diff(temp_space)]
  plt.figure(2, figsize=(15,10))
  plt.plot(volt_bit_space[:-1], np.diff(temp_space),'ko', label="derivative")
  plt.ylabel("$\Delta$ Temp/1 step [C/step]", fontsize=20)
  plt.xlabel("Voltage [mV]", fontsize=20)
  plt.tick_params(axis="both", labelsize=20)
  #plt.yticks( np.linspace(0,1,11) )
  #plt.xticks( np.linspace(0,11000,12) )
  #plt.ylim([0,1])
  #plt.xlim([0,11000])
  l=plt.legend(loc=1, fontsize=15)
  l.draw_frame(False)
  plt.show()
  
  #get_log_xaxis=[math.log(ii) for ii in temp_space[:-1]]
  plt.figure(3, figsize=(15,10))
  plt.plot(temp_space[:-1], np.diff(temp_space),'ko', label="derivative")
  plt.ylabel("$\Delta$Temp per step [C/step]", fontsize=20)
  plt.xlabel("Temp [C]", fontsize=20)
  plt.tick_params(axis="both", labelsize=20)
  plt.title("Controller sensitivity, 10 bits = 1024 steps")
  #plt.yticks( np.linspace(0,1,11) )
  #plt.xticks( np.linspace(0,11000,12) )
  plt.ylim([1,5.5])
  plt.xlim([200,1800])
  l=plt.legend(loc=1, fontsize=15)
  l.draw_frame(False)
  plt.savefig("Contr_sens.pdf")
  plt.show()
  
  #get_log_xaxis=[math.log(ii) for ii in temp_space[:-1]]
  plt.figure(4, figsize=(15,10))
  plt.plot(bit_space, temp_space,'ko', label="Temp[C]")
  plt.ylabel("Temp [C]", fontsize=20)
  plt.xlabel("Bit no.", fontsize=20)
  plt.tick_params(axis="both", labelsize=20)
  #plt.yticks( np.linspace(0,1,11) )
  #plt.xticks( np.linspace(0,11000,12) )
  #plt.ylim([0,1])
  #plt.xlim([0,11000])
  l=plt.legend(loc=1, fontsize=15)
  l.draw_frame(False)
  plt.show()
  

  '''
  # make spline interpolation
  fine_points=np.linspace(true_val[0],true_val[-1],10)
  yaxis1_baud_23040, yaxis2_baud_230400 = AU.return_true_volt(fine_points)
  
  # Plot the results
  plt.figure(1, figsize=(15,10))
  plt.plot(true_val,delta1,'ro-',label="Ard/True, spl. fit (baudrate 23040)")
  plt.plot(true_val,delta2,'bo-',label="Ard/True, spl. fit (baudrate 230400)")
  plt.xlabel("True voltage [mV]", fontsize=20)
  plt.ylabel("Arduino/True [mV/mV]", fontsize=20)
  plt.tick_params(axis="both", labelsize=20)
  #plt.yticks( np.linspace(0,1,11) )
  #plt.xticks( np.linspace(0,11000,12) )
  #plt.ylim([0,1])
  #plt.xlim([0,11000])
  l=plt.legend(loc=4, fontsize=15)
  l.draw_frame(False)

  #plt.savefig('scatterplot.pdf')
  plt.show()
  '''
  

