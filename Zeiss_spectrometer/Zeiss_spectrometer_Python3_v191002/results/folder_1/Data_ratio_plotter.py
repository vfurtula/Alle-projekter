import os, os.path, sys
import numpy as np
import matplotlib.pyplot as plt
#from numpy.polynomial import polynomial as P

class Dat_rat_plt:
	def __init__(self,myfile1,myfile2):
		self.file1 = myfile1
		self.file2 = myfile2

	def plot_data(self):
		# open calib file and plot
		w1=[]
		d1=[]
		with open(self.file1, 'r') as thefile:
			[thefile.readline() for i in [0,1]]
			for line in thefile:
				columns = line.split()
				w1.extend([int(columns[0])])
				d1.extend([float(columns[2])])
		
		w2=[]
		d2=[]
		with open(self.file2, 'r') as thefile:
			[thefile.readline() for i in [0,1]]
			for line in thefile:
				columns = line.split()
				w2.extend([int(columns[0])])
				d2.extend([float(columns[2])])
				
		plt.plot(w1,np.array(d2)/np.array(d1))
		plt.xlabel("wavelength [nm]")
		plt.ylabel("air/filter [bit/bit]")
		plt.show()


def main():
	drp = Dat_rat_plt("air_600_670_1_5_20160301-1312.txt", "filter_600_670_1_5_20160301-1330.txt")
	drp.plot_data()

if __name__ == "__main__":
	main()