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

class Get_Tmax_Tmin:
	
	def __init__(self):
		
		self.gtt = gtt0.Get_TM_Tm()
		self.sub_olis_check, self.raw_olis_check, self.sub_ftir_check, self.raw_ftir_check = self.gtt.data_checks()
		self.fit_linear_spline, self.plot_X, self.config_file = self.gtt.get_method()
		self.folder_str, self.filename_str, self.raw_olis, self.raw_ftir, self.sub_olis, self.sub_ftir, self.timestr, self.save_figs=self.gtt.folders_and_data()
		
		if self.raw_olis_check or self.raw_ftir_check:
			self.x_all_Tfilm, self.y_all_Tfilm = self.gtt.pass_Tfilm()
			
	def make_plots(self):
		
		indx, comax_alph_TalTalflat, com_axisTminTmax_final, all_extremas = self.gtt.get_T_alpha()

		extremas_first, extremas_final, extremas_flatten = all_extremas
		common_xaxis, Tmin, Tmax = com_axisTminTmax_final
		common_xaxis_alpha, T_alpha_first, T_alpha_final, T_alpha_flatten = comax_alph_TalTalflat
		
		

		x_min, y_min, x_max, y_max=[extremas_first[:][0],extremas_first[:][1],extremas_first[:][2],extremas_first[:][3]]
		x_min_, y_min_, x_max_, y_max_=[extremas_final[:][0],extremas_final[:][1],extremas_final[:][2],extremas_final[:][3]]
		x_min__, y_min__, x_max__, y_max__=[extremas_flatten[:][0],extremas_flatten[:][1],extremas_flatten[:][2],extremas_flatten[:][3]]
		
		########################################################################
		pass_plots=[]
	
		plt.figure(figsize=(15,10))
		
		if self.plot_X=='eV':
			plt.plot(x_min, y_min, 'r-', label = "T_min first")
			plt.plot(x_max, y_max, 'b-', label = "T_max first")
			plt.plot(x_min_, y_min_, 'r--', label = "T_min final")
			plt.plot(x_max_, y_max_, 'b--', label = "T_max final")
			plt.plot(self.x_all_Tfilm,self.y_all_Tfilm,'k-', label = "T_raw data")
			plt.plot(common_xaxis_alpha,T_alpha_first,'m-', label = "T_alpha_first")
			plt.plot(common_xaxis_alpha,T_alpha_final,'g-', label = "T_alpha_final")
			plt.plot(self.x_all_Tfilm[indx[-1]+1:], self.y_all_Tfilm[indx[-1]+1:], 'co', label = ''.join(['fringes-free region']))
			string_lab1 = ''.join(['T_min interp (', self.fit_linear_spline , ')'])
			plt.plot(common_xaxis, Tmin, 'ro--', label = string_lab1)
			string_lab2 = ''.join(['T_max interp (', self.fit_linear_spline , ')'])
			plt.plot(common_xaxis, Tmax, 'bo--', label = string_lab2)
			plt.xlabel("E, eV", fontsize=20)
			
		elif self.plot_X=='nm':
			plt.plot(1239.84187/numpy.array(x_min), y_min, 'r-', label = "T_min first")
			plt.plot(1239.84187/numpy.array(x_max), y_max, 'b-', label = "T_max first")
			plt.plot(1239.84187/numpy.array(x_min_), y_min_, 'r--', label = "T_min final")
			plt.plot(1239.84187/numpy.array(x_max_), y_max_, 'b--', label = "T_max final")
			plt.plot(1239.84187/self.x_all_Tfilm,self.y_all_Tfilm,'k-', label = "T_raw data")
			plt.plot(1239.84187/common_xaxis_alpha,T_alpha_first,'m-', label = "T_alpha_first")
			plt.plot(1239.84187/common_xaxis_alpha,T_alpha_final,'g-', label = "T_alpha_final")
			plt.plot(1239.84187/self.x_all_Tfilm[indx[-1]+1:], self.y_all_Tfilm[indx[-1]+1:], 'co', label = ''.join(['fringes-free region']))
			string_lab1 = ''.join(['T_min interp (', self.fit_linear_spline , ')'])
			plt.plot(1239.84187/numpy.array(common_xaxis), Tmin, 'ro--', label = string_lab1)
			string_lab2 = ''.join(['T_max interp (', self.fit_linear_spline , ')'])
			plt.plot(1239.84187/numpy.array(common_xaxis), Tmax, 'bo--', label = string_lab2)
			plt.xlabel("Wavelength, nm", fontsize=20)
			
		plt.ylabel("Tr", fontsize=20)
		plt.tick_params(axis="both", labelsize=20)
		#plt.ylim([0,1])
		#plt.xlim([0,4])
		l=plt.legend(loc=1, fontsize=15)
		l.draw_frame(False)

		if self.save_figs==True:
			string_2 = ''.join([self.folder_str, self.filename_str,'_Tr_subfilm (', self.fit_linear_spline , ')_',self.timestr, '.png'])
			plt.savefig(string_2)
			pass_plots.extend([string_2])

		########################################################################
		
		x_Ts, y_Ts = self.gtt.fit_Ts_to_data(common_xaxis)
		
		plt.figure(figsize=(15,10))
		
		if self.plot_X=='eV':
			plt.plot(x_Ts,y_Ts,'k-')
			plt.xlabel("E, eV", fontsize=20)
			
		elif self.plot_X=='nm':
			plt.plot(1239.84187/numpy.array(x_Ts),y_Ts,'k-')
			plt.xlabel("Wavelength, nm", fontsize=20)
			
		plt.ylabel("Tr", fontsize=20)
		plt.tick_params(axis="both", labelsize=20)
		#plt.ylim([0,1])
		#plt.xlim([0,11000])
		plt.title("Tr (SUBSTRATE) for selected [Tmin, Tmax] region")
		#l=plt.legend(loc=1, fontsize=15)
		#l.draw_frame(False)
		
		if self.save_figs==True:
			string_3 = ''.join([self.folder_str, self.filename_str,'_Tr_sub (', self.fit_linear_spline , ')_',self.timestr, '.png'])
			plt.savefig(string_3)
			pass_plots.extend([string_2])
		
		########################################################################
		
		plt.figure(figsize=(15,10))
		if self.plot_X=='eV':
			plt.plot(common_xaxis_alpha,T_alpha_flatten,'k-', label = "T_alpha flatten")
			plt.plot(x_min__, y_min__, 'ro', label = "T_min flatten")
			plt.plot(x_max__, y_max__, 'bo', label = "T_max flatten")
			plt.xlabel("E, eV", fontsize=20)
			
		elif self.plot_X=='nm':
			plt.plot(1239.84187/numpy.array(common_xaxis_alpha),T_alpha_flatten,'k-', label = "T_alpha flatten")
			plt.plot(1239.84187/numpy.array(x_min__), y_min__, 'ro', label = "T_min flatten")
			plt.plot(1239.84187/numpy.array(x_max__), y_max__, 'bo', label = "T_max flatten")
			plt.xlabel("Wavelength, nm", fontsize=20)
			
		plt.ylabel("Tr", fontsize=20)
		plt.tick_params(axis="both", labelsize=20)
		#plt.yticks( numpy.linspace(0,1,11) )
		#plt.xticks( numpy.linspace(0,11000,12) )
		#plt.ylim([0,1])
		#plt.xlim([0,4])
		l=plt.legend(loc=1, fontsize=15)
		l.draw_frame(False)
		
		if self.save_figs==True:
			string_4 = ''.join([self.folder_str, self.filename_str,'_Tr_flatten (', self.fit_linear_spline , ')_',self.timestr, '.png'])
			plt.savefig(string_4)
			pass_plots.extend([string_4])
		
		return pass_plots
	
	def show_plots(self):
		
		plt.show()


if __name__ == "__main__":
	
	get_class=Get_Tmax_Tmin()
	get_class.make_plots()
	get_class.show_plots()
	
	
	
