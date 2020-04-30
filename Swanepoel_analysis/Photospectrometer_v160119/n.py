## Import libraries
import time, math
import numpy
import matplotlib.pyplot as plt
import Get_TM_Tm_v0 as gtt

## Define refractive index (n) functions 

timestr = time.strftime("%Y%m%d-%H%M")

class N_class:
	
	def __init__(self):
		
		self.gtt0 = gtt.Get_TM_Tm()
		self.my_string = self.gtt0.get_method()

		self.gtt0.ext_interp()
    
	def n_trans(self):
		#print 'method n_trans runs...'

		x_min, y_min, x_max, y_max = self.gtt0.extremas()
		######################################################################

		s = [(1.0/doh)+math.sqrt(1.0/doh**2-1) for doh in self.Ts]
		M = [2.0*s[i]/self.T_min[i]-(s[i]**2+1.0)/2 for i in range(len(self.T_min))] 
		nn = [math.sqrt(M[i]+math.sqrt(M[i]**2-s[i]**2)) for i in range(len(M))]

		return self.common_xaxis, nn

	def n_wm(self):
		#print 'method n_wm runs...'

		inds=range(len(self.common_xaxis))

		s = [(1.0/doh)+math.sqrt(1/doh**2-1) for doh in self.Ts]
		N = [2.0*s[i]*(self.T_max[i]-self.T_min[i])/(self.T_max[i]*self.T_min[i])+(s[i]**2+1)/2.0 for i in inds] 
		n_min_max = [math.sqrt(N[i]+math.sqrt(N[i]**2-s[i]**2)) for i in inds]
		######################################################################

		return self.common_xaxis, n_min_max

	def make_plots(self):
		
		folder_str, filename_str, raw_olis, raw_ftir, sub_olis, sub_ftir=self.gtt0.folders_and_data()
		Expected_Substrate_Dev = self.gtt0.get_Expected_Substrate_Dev()
		
		if Expected_Substrate_Dev==0 or Expected_Substrate_Dev==0.0:
		
			n0 = N_class(0.0)
			self.xxx, self.Ts = self.gtt0.fit_Ts_to_data(0.0)
			self.common_xaxis, self.T_min, self.T_max = self.gtt0.interp_T()
			x_trans, nn_trans = n0.n_trans()
			min_max, nn_wm = n0.n_wm()
			
			plt.figure(1, figsize=(15,10))
			plt.plot(x_trans, nn_trans, 'ko-', label=''.join(['Transp., ', self.my_string]))
			plt.plot(min_max, nn_wm, 'ro-', label=''.join(['Weak/Medium, ', self.my_string]))

		else:
			
			self.xxx, self.Ts = self.gtt0.fit_Ts_to_data(Expected_Substrate_Dev)
			self.common_xaxis, self.T_min, self.T_max = self.gtt0.interp_T()
			x_trans_up, nn_trans_up = self.n_trans()
			min_max_up, nn_wm_up = self.n_wm()
			
			self.xxx, self.Ts = self.gtt0.fit_Ts_to_data(0.0)
			self.common_xaxis, self.T_min, self.T_max = self.gtt0.interp_T()
			x_trans, nn_trans = self.n_trans()
			min_max, nn_wm = self.n_wm()
			
			self.xxx, self.Ts = self.gtt0.fit_Ts_to_data(-Expected_Substrate_Dev)
			self.common_xaxis, self.T_min, self.T_max = self.gtt0.interp_T()
			x_trans_low, nn_trans_low = self.n_trans()
			min_max_low, nn_wm_low = self.n_wm()
			
			############################
			
			plt.figure(1, figsize=(15,10))
			
			plt.plot(x_trans, nn_trans, 'ko-', label=''.join(['Transp., ', self.my_string]))
			plt.fill_between(x_trans, nn_trans_up, nn_trans_low, facecolor='red', alpha=0.2)
			
			plt.plot(min_max, nn_wm, 'ro-', label=''.join(['Weak/Medium, ', self.my_string]))
			plt.fill_between(min_max, nn_wm_up, nn_wm_low, facecolor='pink', alpha=0.2)
			

		plt.xlabel("E, eV", fontsize=20)
		plt.ylabel("n", fontsize=20)
		plt.title("Swanepoel (1983) ref. index methods applied to FTIR and OLIS data")
		plt.tick_params(axis="both", labelsize=20)
		#plt.yticks( numpy.linspace(2,3,11) )
		#plt.ylim([2,3])
		#plt.xlim([95,108])
		l=plt.legend(loc=2, fontsize=15)
		l.draw_frame(False)

		string_1 = ''.join([folder_str, filename_str, '_n_', self.my_string, '_', timestr, '.png'])
		  
		plt.savefig(string_1)
		plt.show()

if __name__ == "__main__":

	N_class().make_plots()
  
	
	
    





