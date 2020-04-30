## Import libraries
import time, numpy
import matplotlib.pyplot as plt
import Get_TM_Tm as gtt0
import alpha

'''
## For Matplotlib fonts
from matplotlib import rc
## for LaTeX style use:
rc("text", usetex=True)
rc("font", family="serif")
'''
## Define k function 

class K_class:
	
	def __init__(self):
		
		self.Alpha_class=alpha.Alpha()
		
		gtt = gtt0.Get_TM_Tm()
		self.folder_str, self.filename_str, self.raw_olis, self.raw_ftir, self.sub_olis, self.sub_ftir, self.timestr, self.save_figs=gtt.folders_and_data()
		self.method, self.plot_X, self.config_file = gtt.get_method()

		self.common_xaxis_12 , self.k_12 = self.k1_eq12()
		self.common_xaxis_15 , self.k_15 = self.k1_eq15()
		

	def k1_eq12(self):
	  #print 'method k runs...'
	  common_xaxis, alpha_wm,_ ,_ = self.Alpha_class.pass_to_k()
	  
	  # convert to wavelength in nm
	  common_xaxis = 1239.84187/common_xaxis
	  
	  k_=common_xaxis*alpha_wm/(4*numpy.pi)
	  
	  # convert back to eV
	  common_xaxis = 1239.84187/common_xaxis
	  
	  return common_xaxis, k_

	def k1_eq15(self):
	  #print 'method k runs...'
	  _, _, common_xaxis, alpha_wm = self.Alpha_class.pass_to_k()
	  
	  # convert to wavelength in nm
	  common_xaxis = 1239.84187/common_xaxis
	  
	  k_ = common_xaxis*alpha_wm/(4*numpy.pi)
	  
	  # convert back to eV
	  common_xaxis = 1239.84187/common_xaxis
	  
	  return common_xaxis, k_

	def make_plots(self):
		
		pass_plots=[]
	
		plt.figure(figsize=(15,10))	
		if self.plot_X=='eV':
			plt.plot(self.common_xaxis_12, 1e3*self.k_12, 'bo-', label=''.join(['k, eq. 12 (',self.method,')']))   
			plt.plot(self.common_xaxis_15, 1e3*self.k_15, 'yo-', label=''.join(['k, eq. 15 (',self.method,')']))
			plt.xlabel("E, eV", fontsize=20)
		
		elif self.plot_X=='nm':
			plt.plot(1239.84187/self.common_xaxis_12, 1e3*self.k_12, 'bo-', label=''.join(['k, eq. 12 (',self.method,')']))   
			plt.plot(1239.84187/self.common_xaxis_15, 1e3*self.k_15, 'yo-', label=''.join(['k, eq. 15 (',self.method,')']))
			plt.xlabel("Wavelength, nm", fontsize=20)
		
		plt.ylabel("k, *10^-3", fontsize=20)
		plt.title("Wavenumber k")
		plt.tick_params(axis="both", labelsize=20)
		#plt.yticks( numpy.linspace(2,3,11) )
		#plt.ylim([2,3])
		#plt.xlim([95,108])
		l=plt.legend(loc=2, fontsize=15)
		l.draw_frame(False)

		if self.save_figs==True:
			string_1 = ''.join([self.folder_str, self.filename_str, '_k_', self.method,'_', self.timestr, '.png'])
			plt.savefig(string_1)
			pass_plots.extend([string_1])

		string_2 = ''.join([self.folder_str, self.filename_str, '_k_', self.method,'_', self.timestr, '.txt'])
		with open(string_2, 'w') as thefile:
			thefile.write(''.join(['This data is constructed from the config file ', self.config_file, '\n']))
			thefile.write(''.join(['Interpolation method for Tmin and Tmax points is ', self.method, '\n']))

			if self.plot_X=='eV':
				thefile.write('Column 1: energy in eV\n')
				thefile.write('Column 2: k_eq12 *1e-3\n')
				thefile.write('Column 3: energy in eV\n')
				thefile.write('Column 4: k_eq15 *1e-3\n')
				for tal0,tal1,tal2,tal3 in zip(self.common_xaxis_12,1e3*self.k_12,self.common_xaxis_15,1e3*self.k_15):
					thefile.write(''.join([str(tal0),'\t',str(tal1),'\t',str(tal2),'\t',str(tal3),'\n',]))
					
			elif self.plot_X=='nm':
				thefile.write('Column 1: wavelength in nm\n')
				thefile.write('Column 2: k_eq12 *1e-3\n')
				thefile.write('Column 3: wavelength in nm\n')
				thefile.write('Column 4: k_eq15 *1e-3\n')
				for tal0,tal1,tal2,tal3 in zip(1239.84187/self.common_xaxis_12,1e3*self.k_12,1239.84187/self.common_xaxis_15,1e3*self.k_15):
					thefile.write(''.join([str(tal0),'\t',str(tal1),'\t',str(tal2),'\t',str(tal3),'\n',]))
			
		pass_plots.extend([string_2])
	
		return pass_plots

	def show_plots(self):
		
		plt.show()
		
if __name__ == "__main__":
	
	get_class=K_class()
	get_class.make_plots()
	get_class.show_plots()





