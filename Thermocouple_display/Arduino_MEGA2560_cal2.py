import sys, serial, argparse, time, re
import numpy as np
import matplotlib.pyplot as plt 

class Fast_logdata:
  def __init__(self,strPort,my_string,i):
    # constants
    self.outputs=i
    self.my_file=my_string
    open(self.my_file, 'w').close()
    
    self.ser = serial.Serial(strPort, 9600)

  def logdata(self):
    try:
      while(1):
	
	line = self.ser.readline()
	
	self.data=[]
	if(len(line.split()) == self.outputs): # expected no. of columns from Arduino
	  for val in line.split():
	    if val.isdigit():
	      self.data.extend([ int(val) ])
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
  my_string='Read_ard_mega2560.txt'
  Ld = Fast_logdata(strPort,my_string,1)
  Ld.logdata()
  
  # open the textfile for plotting
  f2 = open(my_string, 'r')
  data0=[]
  # Read new datafile
  for line in f2:
    columns = line.split()
    data0.extend([ float(columns[0]) ])
  f2.close()
  
  # set up animation figure and background
  fig = plt.figure(1, figsize=(15,10))
  ax = fig.add_subplot(111)
  
  analogRef=1.1 # if analogRef is not enabled than analogRef=5 Volts
  ax.plot(range(len(data0)), data0, 'ko-')
  ax2 = ax.twinx()
  ax2.plot(range(len(data0)), analogRef*np.array(data0), 'ro-')
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
  
  # clean up
  Ld.close()



