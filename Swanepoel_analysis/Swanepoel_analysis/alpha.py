## Import libraries
import time, numpy
import matplotlib.pyplot as plt
from numpy.polynomial import polynomial as P
import Get_TM_Tm as gtt0
import get_m_d as gmd0
import warnings
warnings.filterwarnings("error")

'''
## For Matplotlib fonts
from matplotlib import rc
## for LaTeX style use:
rc("text", usetex=True)
rc("font", family="serif")
'''

## Define absorption (alpha) functions 

class Alpha:
	

	def __init__(self):
		
		gtt = gtt0.Get_TM_Tm()
		gmd = gmd0.Gmd()

		self.method, self.plot_X, self.config_file = gtt.get_method()
		self.sub_olis_check, self.raw_olis_check, self.sub_ftir_check, self.raw_ftir_check = gtt.data_checks()
		self.folder_str, self.filename_str, self.raw_olis, self.raw_ftir, self.sub_olis, self.sub_ftir, self.timestr, self.save_figs=gtt.folders_and_data()
		self.fit_poly_order, self.fit_poly_ranges, self.fit_poly_ranges_check = gtt.str_abs_params()
		
		if self.raw_olis_check or self.raw_ftir_check:
			self.x_all_Tr, self.y_all_Tr = gtt.pass_Tfilm()
		
		_, self.Ts = gtt.fit_Ts_to_data(self.x_all_Tr)
		
		_, _, com_axisTminTmax_final, all_extremas = gtt.get_T_alpha()
		_, extremas_final, _ = all_extremas
		x_min_, y_min_, x_max_, y_max_=[extremas_final[:][0],extremas_final[:][1],extremas_final[:][2],extremas_final[:][3]]
		
		indcs = numpy.where((self.x_all_Tr>x_min_[-1]) & (self.x_all_Tr>x_max_[-1]))
		self.x_all = self.x_all_Tr[indcs]
		self.y_all = self.y_all_Tr[indcs]
		self.Ts = self.Ts[indcs]
		
		self.xaxis, self.Tmin, self.Tmax = com_axisTminTmax_final
		
		_, self.Ts_min_max = gtt.fit_Ts_to_data(self.xaxis)

		_, _, self.n_min_max, self.d = gmd.pass_to_alpha()
	
		###############################################################
		
		if self.fit_poly_ranges_check==False:
		  self.coef = P.polyfit(self.xaxis,self.n_min_max,self.fit_poly_order)
		  self.curve_all = numpy.poly1d(self.coef[::-1])(self.x_all_Tr)
		    
		elif self.fit_poly_ranges_check==True:
			self.acc_min_max=numpy.array([])
			self.acc_n=numpy.array([])
			self.rej_min_max=numpy.array([])
			self.rej_n=numpy.array([])
			
			# add first and last index element from the min_max list 
			ranges=[self.xaxis[0]]+self.fit_poly_ranges+[self.xaxis[-1]]
			for i in range(len(ranges)-1):
				indx = numpy.where((self.xaxis>=ranges[i]) & (self.xaxis<ranges[i+1]))

				if i%2==0:
				  self.rej_min_max=numpy.append(self.rej_min_max, self.xaxis[indx])
				  self.rej_n=numpy.append(self.rej_n, self.n_min_max[indx])
				else:
				  self.acc_min_max=numpy.append(self.acc_min_max, self.xaxis[indx])
				  self.acc_n=numpy.append(self.acc_n, self.n_min_max[indx])
				   
			self.coef = P.polyfit(self.acc_min_max,self.acc_n,self.fit_poly_order)
			self.curve_all = numpy.poly1d(self.coef[::-1])(self.x_all_Tr)
 
 
		self.xaxis_12 , self.alpha_12 = self.alpha_eq12()
		self.xaxis_15 , self.alpha_15 = self.alpha_eq15()
		self.xaxis_A3 , self.alpha_A3 = self.alpha_eqA3()
		
		
		self.min_max2, self.nn2, self.curve_2 = self.show_n_fit()

	def pass_to_k(self):
		
		return  self.xaxis_12 , self.alpha_12, self.xaxis_15 , self.alpha_15

	def alpha_eq12(self):
		
		s = 1.0/self.Ts_min_max+(1.0/self.Ts_min_max**2-1)**0.5
		n = numpy.poly1d(self.coef[::-1])(self.xaxis)
		E_M = 8*n**2*s/self.Tmax+(n**2-1)*(n**2-s**2)
		try:
			xexp = (E_M-(E_M**2-(n**2-1)**3*(n**2-s**4))**0.5)/((n-1)**3*(n-s**2))
		except RuntimeWarning:
			raise Exception('squareroot')
		
		s = 1.0/self.Ts+(1.0/self.Ts**2-1)**0.5
		n = numpy.poly1d(self.coef[::-1])(self.x_all)
		E_M = 8*n**2*s/self.y_all+(n**2-1)*(n**2-s**2)
		try:
			xexp_sa = (E_M-(E_M**2-(n**2-1)**3*(n**2-s**4))**0.5)/((n-1)**3*(n-s**2))
		except RuntimeWarning:
			raise Exception('squareroot')
		
		# append together Tmin and Tmax region with strong absorption region
		new_x_axis = numpy.append(self.xaxis,self.x_all)
		new_xexp = numpy.append(xexp,xexp_sa)
		
		# take only positive values due to log function
		indx = numpy.where((1>new_xexp)&(0<new_xexp))[0]
		new_x_axis = new_x_axis[indx]
		new_xexp = new_xexp[indx]
		
		#x=math.exp(-alpha*d)
		alpha = -numpy.log(new_xexp)/self.d
		
		return new_x_axis, alpha


	def alpha_eq15(self):
		
		s = (1.0/self.Ts_min_max)+(1/self.Ts_min_max**2-1)**0.5
		Ti = 2.0*self.Tmax*self.Tmin/(self.Tmax+self.Tmin)
		n = numpy.poly1d(self.coef[::-1])(self.xaxis) 
		F = 8*s*n**2/Ti
		try:
			xexp = (F-(F**2-(n**2-1)**3*(n**2-s**4))**0.5)/((n-1)**3*(n-s**2))
		except RuntimeWarning:
			raise Exception('squareroot') 
		
		s = (1.0/self.Ts)+(1/self.Ts**2-1)**0.5
		n = numpy.poly1d(self.coef[::-1])(self.x_all) 
		F = 8*s*n**2/self.y_all
		try:
			xexp_sa = (F-(F**2-(n**2-1)**3*(n**2-s**4))**0.5)/((n-1)**3*(n-s**2))
		except RuntimeWarning:
			raise Exception('squareroot')
		
		# append together Tmin and Tmax region with strong absorption region
		new_x_axis = numpy.append(self.xaxis,self.x_all)
		new_xexp = numpy.append(xexp,xexp_sa)
		
		# take only positive values due to log function
		indx = numpy.where((1>new_xexp)&(0<new_xexp))[0]
		new_x_axis = new_x_axis[indx]
		new_xexp = new_xexp[indx]
		
		#x=math.exp(-alpha*d)
		alpha = -numpy.log(new_xexp)/self.d
		
		return new_x_axis, alpha


	def alpha_eqA3(self):
	  #print 'method alpha_eqA3 runs...'
	  
		s=1.0/self.Ts_min_max+(1.0/self.Ts_min_max**2-1)**0.5
		T_alpha = (self.Tmax*self.Tmin)**0.5
		n = numpy.poly1d(self.coef[::-1])(self.xaxis)
		R1=((1-n)/(1+n))**2
		R2=((n-s)/(n+s))**2
		R3=((s-1)/(s+1))**2
		Pp=(R1-1)*(R2-1)*(R3-1)
		Q=2*T_alpha*(R1*R2+R1*R3-2*R1*R2*R3)
		try:
			xexp = (Pp+(Pp**2+2*Q*T_alpha*(1-R2*R3))**0.5)/Q
		except RuntimeWarning:
			raise Exception('squareroot')
		
		s=1.0/self.Ts+(1.0/self.Ts**2-1)**0.5
		n = numpy.poly1d(self.coef[::-1])(self.x_all)
		R1=((1-n)/(1+n))**2
		R2=((n-s)/(n+s))**2
		R3=((s-1)/(s+1))**2
		Pp=(R1-1)*(R2-1)*(R3-1)
		Q=2*self.y_all*(R1*R2+R1*R3-2*R1*R2*R3)
		try:
			xexp_sa = (Pp+(Pp**2+2*Q*self.y_all*(1-R2*R3))**0.5)/Q
		except RuntimeWarning:
			raise Exception('squareroot')
	  
	  # append together Tmin and Tmax region with strong absorption region
		new_x_axis = numpy.append(self.xaxis,self.x_all)
		new_xexp = numpy.append(xexp,xexp_sa)
		
		# take only positive values due to log function
		indx = numpy.where((1>new_xexp)&(0<new_xexp))[0]
		new_x_axis = new_x_axis[indx]
		new_xexp = new_xexp[indx]
	  
		#x=math.exp(-alpha*d)
		alpha = -numpy.log(new_xexp)/self.d

		return new_x_axis, alpha
	
	def show_n_fit(self):
	  #print 'method show_n_fit runs...'
	  
	  if self.fit_poly_ranges_check==False:
	    print "polyfit coefs (order", self.fit_poly_order,") = ", self.coef
	    return self.xaxis, self.n_min_max, [self.x_all_Tr,self.curve_all]
	  
	  elif self.fit_poly_ranges_check==True:
			print "polyfit coefs (order", self.fit_poly_order,") = ", self.coef
			return [self.acc_min_max,self.rej_min_max], [self.acc_n,self.rej_n], [self.x_all_Tr,self.curve_all]


	def make_plots(self):

		pass_plots=[]
	
		plt.figure(figsize=(15,10))
		
		if self.plot_X=='eV':
			plt.plot(self.xaxis_12, 1e4*self.alpha_12, 'ro-', label=''.join(['alpha, eq. 12 (',self.method,')']))
			plt.plot(self.xaxis_15, 1e4*self.alpha_15, 'mo-', label=''.join(['alpha, eq. 15 (',self.method,')']))    
			plt.plot(self.xaxis_A3, 1e4*self.alpha_A3, 'go-', label=''.join(['alpha, eq. A3 (',self.method,')']))
			plt.xlabel("E, eV", fontsize=20)
		elif self.plot_X=='nm':
			plt.plot(1239.84187/self.xaxis_12, 1e4*self.alpha_12, 'ro-', label=''.join(['alpha, eq. 12 (',self.method,')']))
			plt.plot(1239.84187/self.xaxis_15, 1e4*self.alpha_15, 'mo-', label=''.join(['alpha, eq. 15 (',self.method,')']))    
			plt.plot(1239.84187/self.xaxis_A3, 1e4*self.alpha_A3, 'go-', label=''.join(['alpha, eq. A3 (',self.method,')']))   
			plt.xlabel("Wavelength, nm", fontsize=20)
		
		plt.ylabel("alpha, *10^3 cm^-1", fontsize=20)
		plt.title("Absorption alpha")
		plt.tick_params(axis="both", labelsize=20)
		#plt.yticks( numpy.linspace(2,3,11) )
		#plt.ylim([-0.1,5])
		#plt.xlim([95,108])
		l=plt.legend(loc=2, fontsize=20)
		l.draw_frame(False)

		string_1 = ''.join([self.folder_str, self.filename_str, '_alpha_', self.method,'_', self.timestr, '.png'])
		if self.save_figs==True:
			plt.savefig(string_1)
			pass_plots.extend([string_1])

		string_2 = ''.join([string_1[:-3], 'txt'])
		with open(string_2, 'w') as thefile:
			thefile.write(''.join(['This data is constructed from the config file ', self.config_file, '\n']))
			thefile.write(''.join(['Interpolation method for Tmin and Tmax points is ', self.method, '\n']))

			if self.plot_X=='eV':
				thefile.write('Column 1: energy in eV\n')
				thefile.write('Column 2: alpha_eq12 *1e3 in 1/cm\n')
				thefile.write('Column 3: energy in eV\n')
				thefile.write('Column 4: alpha_eq15 *1e3 in 1/cm\n')
				thefile.write('Column 5: energy in eV\n')
				thefile.write('Column 6: alpha_eqA3 *1e3 in 1/cm\n')
				for tal0,tal1,tal2,tal3,tal4,tal5 in zip(self.xaxis_12,1e4*self.alpha_12,self.xaxis_15,1e4*self.alpha_15,self.xaxis_A3,1e4*self.alpha_A3):
					thefile.write(''.join([str(tal0),'\t',str(tal1),'\t',str(tal2),'\t',str(tal3),'\t',str(tal4),'\t',str(tal5),'\n']))
					
			elif self.plot_X=='nm':
				thefile.write('Column 1: wavelength in nm\n')
				thefile.write('Column 2: alpha_eq12 *1e3 in 1/cm\n')
				thefile.write('Column 3: wavelength in nm\n')
				thefile.write('Column 4: alpha_eq15 *1e3 in 1/cm\n')
				thefile.write('Column 5: wavelength in nm\n')
				thefile.write('Column 6: alpha_eqA3 *1e3 in 1/cm\n')
				for tal0,tal1,tal2,tal3,tal4,tal5 in zip(1239.84187/self.xaxis_12,1e4*self.alpha_12,1239.84187/self.xaxis_15,1e4*self.alpha_15,1239.84187/self.xaxis_A3,1e4*self.alpha_A3):
					thefile.write(''.join([str(tal0),'\t',str(tal1),'\t',str(tal2),'\t',str(tal3),'\t',str(tal4),'\t',str(tal5),'\n']))
					
		pass_plots.extend([string_2])
		###############################################################

		plt.figure(figsize=(15,10))
		
		fit_poly_string=''.join(['n2, polyfit order ',str(self.fit_poly_order)])
		
		if self.plot_X=='eV':
			if self.fit_poly_ranges_check==False:
			  plt.plot(self.min_max2 , self.nn2, 'go', label=''.join(['n2, (', self.method, ')']))
			  plt.plot(self.curve_2[0], self.curve_2[1], 'k-', label=fit_poly_string)
			
			elif self.fit_poly_ranges_check==True:
			  plt.plot(self.min_max2[0] , self.nn2[0], 'go', label=''.join(['n2, (', self.method, ') acc. points']))
			  plt.plot(self.min_max2[1] , self.nn2[1], 'ro', label=''.join(['n2, (', self.method, ') rej. points']))
			  plt.plot(self.curve_2[0] , self.curve_2[1], 'k-', label=fit_poly_string)
			plt.xlabel("E, eV", fontsize=20)
		
		elif self.plot_X=='nm':
			if self.fit_poly_ranges_check==False:
			  plt.plot(1239.84187/self.min_max2, self.nn2, 'go', label=''.join(['n2, (', self.method, ')']))
			  plt.plot(1239.84187/self.curve_2[0], self.curve_2[1], 'k-', label=fit_poly_string)
			
			elif self.fit_poly_ranges_check==True:
			  plt.plot(1239.84187/self.min_max2[0], self.nn2[0], 'go', label=''.join(['n2, (', self.method, ') acc. points']))
			  plt.plot(1239.84187/self.min_max2[1], self.nn2[1], 'ro', label=''.join(['n2, (', self.method, ') rej. points']))
			  plt.plot(1239.84187/self.curve_2[0], self.curve_2[1], 'k-', label=fit_poly_string)
			plt.xlabel("Wavelength, nm", fontsize=20)
		
		plt.ylabel("n", fontsize=20)
		plt.tick_params(axis="both", labelsize=20)
		l=plt.legend(loc=2, fontsize=20)
		l.draw_frame(False)

		if self.save_figs==True:
			string_3 = ''.join([self.folder_str, self.filename_str,'_n2_', self.timestr,'.png'])
			plt.savefig(string_3)
			pass_plots.extend([string_3])
		
		return pass_plots
	

	def show_plots(self):
		
		plt.show()
	  
if __name__ == "__main__":
	
	get_class=Alpha()
	get_class.make_plots()
	get_class.show_plots()
