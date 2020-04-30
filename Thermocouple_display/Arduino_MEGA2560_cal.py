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

class Arduino_mega_cal:
  def __init__(self,my_string):
    # Open new datafile form SOURCE 2 (OLIS)
    #my_string='Arduino_UNO_R3_voltage_calibration.txt'
    f2 = open(my_string, 'r')

    # Read and ignore header lines
    headers = [f2.readline() for i in range(4)]
    
    self.bits=[]
    self.volt=[]
    # Read new datafile
    for line in f2:
      line = line.strip()
      columns = line.split()
      self.bits.extend([ float(columns[1]) ])
      self.volt.extend([ float(columns[0]) ])
    f2.close()
    
    string_1 = ''.join([my_string,'_bits_volts.txt'])
    # save data locally
    with open(string_1, 'w') as thefile:
      for ii in range(len(self.bits)):
	if ii == 0:
	  #thefile.write("{%s, " % self.bits[ii])
	  thefile.write("{%s, " % self.bits[ii])
	elif ii == len(self.bits)-1:
	  #thefile.write("%s};" % self.bits[ii])
	  thefile.write("%s};" % self.bits[ii])
	else:
	  #thefile.write("%s, " % self.bits[ii])
	  thefile.write("%s, " % self.bits[ii])
    
    #self.volt=list(np.linspace(0.01,1.11,len(self.bits)))
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
    
    return self.bits, self.volt
          
  def fit_data_to_poly(self,order):
    coefs = P.polyfit(self.bits, self.volt, order)
    print "coefs(", order, ") =", coefs    
    ny_true_volt = [np.poly1d(coefs[::-1])(i) for i in self.bits]
    
    return self.bits, ny_true_volt
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
  
  amc = Arduino_mega_cal('Ard_mega2560(1V1)_calfile4.txt')
  bits, true_volt = amc.get_data()
  
  bits_, true_volt_  = amc.fit_data_to_poly(1)
  bits__, true_volt__  = amc.fit_data_to_poly(2)
  bits___, true_volt___  = amc.fit_data_to_poly(3)

  # Plot the results
  plt.figure(1, figsize=(15,10))
  plt.plot(bits, true_volt,'ko',label="Thermocouple data")
  plt.plot(bits_, true_volt_, 'r-',label="1st order polyfit")
  plt.plot(bits__, true_volt__, 'b-',label="2nd order polyfit")
  plt.plot(bits___, true_volt___, 'm-',label="3rd order polyfit")

  #plt.plot(true_val,val_second,'r-',label="Parab. fit")
  plt.xlabel("Bit number", fontsize=20)
  plt.ylabel("Voltage [mV]", fontsize=20)
  plt.tick_params(axis="both", labelsize=20)
  #plt.yticks( np.linspace(0,1,11) )
  #plt.xticks( np.linspace(0,11000,12) )
  #plt.ylim([0,1])
  #plt.xlim([0,11000])
  l=plt.legend(loc=4, fontsize=15)
  l.draw_frame(False)

  plt.savefig('thermocouple_polyfit.pdf')
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
  

