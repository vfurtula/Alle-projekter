## Import libraries
import matplotlib.pyplot as plt
import os, sys, time, numpy
import Get_TM_Tm as gtt0

'''
## For Matplotlib fonts
from matplotlib import rc
## for LaTeX style use:
rc("text", usetex=True)
rc("font", family="serif")
'''

class Get_raw:
	
	def __init__(self):
		
		self.gtt = gtt0.Get_TM_Tm()
		
		_, self.plot_X, self.config_file = self.gtt.get_method()
		self.folder_str, self.filename_str, self.raw_olis, self.raw_ftir, self.sub_olis, self.sub_ftir, self.timestr, self.save_figs=self.gtt.folders_and_data()
		self.sub_olis_check, self.raw_olis_check, self.sub_ftir_check, self.raw_ftir_check = self.gtt.data_checks()
		
		if self.sub_olis_check or self.sub_ftir_check:
			self.x_all_Ts, self.y_all_Ts = self.gtt.pass_Ts()

		if self.raw_olis_check or self.raw_ftir_check:
			self.x_all_Tfilm, self.y_all_Tfilm = self.gtt.pass_Tfilm()
		
		
	def make_plots(self):
		
		pass_plots=[]
	
		if (self.raw_ftir_check or self.raw_olis_check) and not (self.sub_ftir_check or self.sub_olis_check):
			
			plt.figure(figsize=(15,10))
			
			if self.plot_X=='eV':
				plt.plot(self.x_all_Tfilm,self.y_all_Tfilm,'k-')
				plt.xlabel("E, eV", fontsize=20)
				
			elif self.plot_X=='nm':
				plt.plot(1239.84187/self.x_all_Tfilm,self.y_all_Tfilm,'k-')
				plt.xlabel("Wavelength, nm", fontsize=20)
				
			plt.ylabel("Tr_film", fontsize=20, color='k')
			plt.tick_params(axis="x", labelsize=20)
			plt.tick_params(axis="y", labelsize=20, colors='k')
			plt.title("FILM")
			
			string_1 = ''.join([self.folder_str, self.filename_str,'_Tr_filmRAW_',self.timestr,'.png'])
			if self.save_figs==True:
				plt.savefig(string_1)
				pass_plots.extend([string_1])
			
			########################################################################
			
			string_2 = ''.join([string_1[:-3],'txt'])
			with open(string_2, 'w') as thefile:
				thefile.write(''.join(['This data is constructed from the config file ', self.config_file, '\n']))
				thefile.write('Column 1: wavelength in nm\n')
				thefile.write('Column 2: energy in eV\n')
				thefile.write('Column 3: Tr (filmRAW)\n')

				for tal0,tal1,tal2 in zip(1239.84187/self.x_all_Tfilm,self.x_all_Tfilm,self.y_all_Tfilm):
					thefile.write(''.join([str(tal0),'\t',str(tal1),'\t',str(tal2),'\n']))

			pass_plots.extend([string_2])
		
		
		elif (self.sub_ftir_check or self.sub_olis_check) and not (self.raw_ftir_check or self.raw_olis_check):
			
			plt.figure(figsize=(15,10))
			
			if self.plot_X=='eV':
				plt.plot(self.x_all_Ts,self.y_all_Ts,'r-')
				plt.xlabel("E, eV", fontsize=20)
				
			elif self.plot_X=='nm':
				plt.plot(1239.84187/self.x_all_Ts,self.y_all_Ts,'r-')
				plt.xlabel("Wavelength, nm", fontsize=20)
				
			plt.ylabel("Tr_sub", fontsize=20, color='r')
			plt.tick_params(axis="x", labelsize=20)
			plt.tick_params(axis="y", labelsize=20, colors='r')
			plt.title("SUBSTRATE")
			
			string_1 = ''.join([self.folder_str, self.filename_str,'_Tr_subRAW_',self.timestr,'.png'])
			if self.save_figs==True:
				plt.savefig(string_1)
				pass_plots.extend([string_1])
			
			########################################################################
		
			string_2 = ''.join([string_1[:-3],'txt'])
			with open(string_2, 'w') as thefile:
				thefile.write(''.join(['This data is constructed from the config file ', self.config_file, '\n']))
				thefile.write('Column 1: wavelength in nm\n')
				thefile.write('Column 2: energy in eV\n')
				thefile.write('Column 3: Tr (subRAW)\n')
				
				for tal0,tal1,tal2 in zip(1239.84187/self.x_all_Ts,self.x_all_Ts,self.y_all_Ts):
					thefile.write(''.join([str(tal0),'\t',str(tal1),'\t',str(tal2),'\n']))

			pass_plots.extend([string_2])
			
		else:
			
			fig, ax1 = plt.subplots(figsize=(15,10))
			ax2 = ax1.twinx()
			
			if self.plot_X=='eV':
				ax1.plot(self.x_all_Tfilm,self.y_all_Tfilm,'k-')
				ax2.plot(self.x_all_Ts,self.y_all_Ts,'r-')
				ax1.set_xlabel("E, eV", fontsize=20)
				
			elif self.plot_X=='nm':
				ax1.plot(1239.84187/self.x_all_Tfilm,self.y_all_Tfilm,'k-')
				ax2.plot(1239.84187/self.x_all_Ts,self.y_all_Ts,'r-')
				ax1.set_xlabel("Wavelength, nm", fontsize=20)
				
			ax1.set_ylabel("Tr_film", fontsize=20, color='k')
			ax1.tick_params(axis="x", labelsize=20)
			ax1.tick_params(axis="y", labelsize=20, colors='k')
			
			ax2.set_ylabel("Tr_sub", fontsize=20, color='r')			
			ax2.tick_params(axis="x", labelsize=20)
			ax2.tick_params(axis="y", labelsize=20, colors='r')
			
			#plt.xlim([0,4])
			#plt.ylim([0,1])
			plt.title("SUBSTRATE and FILM")
			#l=plt.legend(loc=1, fontsize=15)
			#l.draw_frame(False)

			string_1 = ''.join([self.folder_str, self.filename_str,'_Tr_subfilmRAW_',self.timestr,'.png'])
			if self.save_figs==True:
				plt.savefig(string_1)
				pass_plots.extend([string_1])
			
			########################################################################
			
			string_2 = ''.join([string_1[:-3],'txt'])
			with open(string_2, 'w') as thefile:
				thefile.write(''.join(['This data is constructed from the config file ', self.config_file, '\n']))
				thefile.write('Column 1: wavelength in nm\n')
				thefile.write('Column 2: energy in eV\n')
				thefile.write('Column 3: Tr (filmRAW)\n')

				for tal0,tal1,tal2 in zip(1239.84187/self.x_all_Tfilm,self.x_all_Tfilm,self.y_all_Tfilm):
					thefile.write(''.join([str(tal0),'\t',str(tal1),'\t',str(tal2),'\n']))

			pass_plots.extend([string_2])
		
			string_3 = ''.join([self.folder_str, self.filename_str,'_Tr_subRAW_',self.timestr,'.txt'])
			with open(string_3, 'w') as thefile:
				thefile.write(''.join(['This data is constructed from the config file ', self.config_file, '\n']))
				thefile.write('Column 1: wavelength in nm\n')
				thefile.write('Column 2: energy in eV\n')
				thefile.write('Column 3: Tr (subRAW)\n')
				
				for tal0,tal1,tal2 in zip(1239.84187/self.x_all_Ts,self.x_all_Ts,self.y_all_Ts):
					thefile.write(''.join([str(tal0),'\t',str(tal1),'\t',str(tal2),'\n']))

			pass_plots.extend([string_3])
		
		return pass_plots
	
	
	def show_plots(self):
		
		plt.show()


if __name__ == "__main__":
	
	get_class=Get_raw()
	get_class.make_plots()
	get_class.show_plots()
	
	
	
