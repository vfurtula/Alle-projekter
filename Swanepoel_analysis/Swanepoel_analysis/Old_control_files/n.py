## Import libraries
import time, numpy
import matplotlib.pyplot as plt
import Get_TM_Tm as gtt0

## Define refractive index (n) functions 


class N_class:
	
	def __init__(self):
		
		gtt = gtt0.Get_TM_Tm()
		self.method, self.plot_X, self.config_file = gtt.get_method()
		self.folder_str, self.filename_str, _, _, _, _, self.timestr, self.save_figs=gtt.folders_and_data()

		_, _, com_axisTminTmax_final, _ = gtt.get_T_alpha()
		self.common_xaxis, self.Tmin, self.Tmax = com_axisTminTmax_final
		_, self.Ts = gtt.fit_Ts_to_data(self.common_xaxis)
		
		self.x_trans, self.nn_trans = self.n_trans()
		self.min_max, self.nn_wm = self.n1()
    
    
	def n_trans(self):
		#print 'method n_trans runs...'

		s = (1.0/self.Ts)+numpy.sqrt(1.0/self.Ts**2-1)
		M = 2.0*s/self.Tmin-(s**2+1.0)/2 
		nn = numpy.sqrt(M+numpy.sqrt(M**2-s**2)) 

		return self.common_xaxis, nn

	def n1(self):
		#print 'method n1 runs...'

		s = (1.0/self.Ts)+numpy.sqrt(1/self.Ts**2-1)
		N = 2.0*s*(self.Tmax-self.Tmin)/(self.Tmax*self.Tmin)+(s**2+1)/2.0 
		n_min_max = numpy.sqrt(N+numpy.sqrt(N**2-s**2)) 

		return self.common_xaxis, n_min_max

	def make_plots(self):

		pass_plots=[]
		plt.figure(figsize=(15,10))
		
		if self.plot_X=='eV':
			plt.plot(self.x_trans, self.nn_trans, 'ko-', label=''.join(['Transp (',self.method,')']))
			plt.plot(self.min_max, self.nn_wm, 'ro-', label=''.join(['Weak and medium absorp (',self.method,')']))
			plt.xlabel("E, eV", fontsize=20)
		
		elif self.plot_X=='nm':
			plt.plot(1239.84187/numpy.array(self.x_trans), self.nn_trans, 'ko-', label=''.join(['Transp (',self.method,')']))
			plt.plot(1239.84187/numpy.array(self.min_max), self.nn_wm, 'ro-', label=''.join(['Weak and medium absorp (',self.method,')']))
			plt.xlabel("Wavelength, nm", fontsize=20)
		
		plt.ylabel("n", fontsize=20)
		plt.title("Ref. index n")
		plt.tick_params(axis="both", labelsize=20)
		#plt.yticks( numpy.linspace(2,3,11) )
		#plt.ylim([2,3])
		#plt.xlim([95,108])
		l=plt.legend(loc=2, fontsize=15)
		l.draw_frame(False)

		if self.save_figs==True:
			string_1 = ''.join([self.folder_str, self.filename_str, '_n_', self.method, '_', self.timestr, '.png'])
			plt.savefig(string_1)
			pass_plots.extend([string_1])
		
		return pass_plots

	def show_plots(self):
		
		plt.show()
	  
if __name__ == "__main__":
	
	get_class=N_class()
	get_class.make_plots()
	get_class.show_plots()
	
	
    





