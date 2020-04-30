import sys, serial, argparse, time, re
import numpy as np
import matplotlib.pyplot as plt 

class Fast_logdata:
  def __init__(self,strPort,i):
    # constants
    self.outputs=i
    self.strPort_=strPort
    self.my_file='read_fast_data.txt'
    open(self.my_file, 'w').close()
    
    self.ser = serial.Serial(strPort, 9600)
        
  def logdata(self):
    # Check input if a number, ie. digits or dots such as 3.141
    # Source: http://www.pythoncentral.io/how-to-check-if-a-string-is-a-number-in-python-including-unicode/
    def is_number(s):
      try:
	  float(s)
	  return True
      except ValueError:
	  pass
  
      try:
	  import unicodedata
	  unicodedata.numeric(s)
	  return True
      except (TypeError, ValueError):
	  pass
  
      return False
    ####################################################################################
    
    # Read the data and save the data
    try:
      while(1):
	
	line = self.ser.readline()
	
	self.data=[]
	if(len(line.split()) == self.outputs): # expected no. of columns from Arduino
	  for val in line.split():
	    if is_number(val):
	      self.data.extend([ val ])
	    else:
	      self.data.extend([ 0 ])
	  
	  # save data locally
	  with open(self.my_file, 'a') as thefile:
	    for tal in range(len(self.data)):
	      if tal == len(self.data)-1:
		thefile.write("%s\n" % self.data[tal])
	      else:
		thefile.write("%s " % self.data[tal])

    except KeyboardInterrupt:
      print('exiting')
        
  # clean up
  def close(self):
    # close serial
    self.ser.flush()
    self.ser.close() 
 
if __name__ == "__main__":
  
  # create parser
  parser = argparse.ArgumentParser(description="your arduino serial")
  # add expected arguments
  parser.add_argument('--port', dest='port', required=True)
  #strPort = '/dev/ttyACM0'
  strPort = parser.parse_args().port
  
  # run Microcontroller and save data in a textfile
  Ld = Fast_logdata(strPort,3)
  Ld.logdata()
  
  # open the textfile for plotting
  my_string='read_fast_data.txt'
  f2 = open(my_string, 'r')
  data0=[]
  data1=[]
  data2=[]
  # Read new datafile
  for line in f2:
    columns = line.split()
    data0.extend([ float(columns[0]) ])
    data1.extend([ float(columns[1]) ])
    data2.extend([ float(columns[2]) ])
  f2.close()
  
  # set up animation figure and background
  fig = plt.figure(1, figsize=(15,10))
  ax = fig.add_subplot(111)
  
  analogRef=1 # if analogRef is not enabled than analogRef=5 Volts
  ax.plot(range(len(data0))[:10000], data0[:10000], 'ko-')
  ax2 = ax.twinx()
  ax2.plot(range(len(data1))[:10000], analogRef*np.array(data1[:10000]), 'ro-')
  string_1 = ''.join([r'Microcontroller step, arb. unit'])
  ax.set_xlabel(string_1, fontsize=20)
  ax.set_ylabel("Bits, arb. units", fontsize=20)
  ax.tick_params(axis="both", labelsize=20)
  ax2.set_ylabel("Voltage, uV", fontsize=20, color='r')
  ax2.tick_params(axis="y", labelsize=20)
  for tl in ax2.get_yticklabels():
    tl.set_color('r')
  #plt.savefig('OEC_detector_noisefloor.pdf')
  plt.show()
  
  # Plot the results
  plt.figure(2, figsize=(15,10))
  plt.plot(range(len(data2))[:10000], data2[:10000], 'bo-')
  #plt.plot(true_val,val_second,'r-',label="Parab. fit")
  plt.ylabel("Temp [C]", fontsize=20)
  plt.xlabel("Microcontroller step, arb. unit", fontsize=20)
  plt.tick_params(axis="both", labelsize=20)
  #plt.yticks( np.linspace(0,1,11) )
  #plt.xticks( np.linspace(0,11000,12) )
  #plt.ylim([0,1])
  #plt.xlim([0,11000])
  #l=plt.legend(loc=4, fontsize=15)
  #l.draw_frame(False)
  plt.show()
  
  
  # clean up
  Ld.close()



