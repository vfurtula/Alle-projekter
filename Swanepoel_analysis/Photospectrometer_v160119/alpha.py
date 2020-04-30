## Import libraries
import time, math
import numpy as np
import matplotlib.pyplot as plt
from numpy.polynomial import polynomial as P
import Get_TM_Tm_v0 as gtt
import get_m_d as gmd
'''
## For Matplotlib fonts
from matplotlib import rc
## for LaTeX style use:
rc("text", usetex=True)
rc("font", family="serif")
'''
## Define absorption (alpha) functions 

gtt = gtt.Get_TM_Tm()
strong_abs_start_eV, fit_poly_order, fit_poly_ranges = gtt.str_abs_params()
ignored_points = gtt.ig_po()
ese = gtt.get_Expected_Substrate_Dev()
my_string = gtt.get_method()

timestr = time.strftime("%Y%m%d-%H%M")

class Alpha:
	
  def __init__(self,disc_ratio):
		
		gtt.ext_interp()
		self.common_xaxis, Tmin, Tmax = gtt.interp_T()
		Gmd_class=gmd.Gmd(disc_ratio)

		xxx, Ts = gtt.fit_Ts_to_data(0)
		#xxx, Ts = gtt.fit_Ts_to_data(my_string)
		self.min_max, self.nn = Gmd_class.get_new_n()
		self.d=Gmd_class.get_md()[4]

		######################################################################

		inds=range(len(self.common_xaxis))
		s = [(1.0/doh)+math.sqrt(1/doh**2-1) for doh in Ts]
		Ti = [2.0*Tmax[i]*Tmin[i]/(Tmax[i]+Tmin[i]) for i in inds] 
		F = [8*s[i]*self.nn[i]**2/Ti[i] for i in inds]
		xexp_wm = [(F[i]-math.sqrt(F[i]**2-(self.nn[i]**2-1)**3*(self.nn[i]**2-s[i]**4)))/ \
		  ((self.nn[i]-1)**3*(self.nn[i]-s[i]**2)) for i in inds]
		######################################################################
		#x=math.exp(-alpha*d)
		self.alpha_wm=[-math.log(doh)/self.d for doh in xexp_wm]

		####################################################################################
		####################################################################################

		if not fit_poly_ranges:
		  print "WARNING: fit_poly_ranges list is empty! Entire min_max list is used to find the polyfit curve. Limit the range of points if needed"
		  ################################################
		  self.coef = P.polyfit(self.min_max,self.nn,fit_poly_order)
		  self.curve_ = [np.poly1d(self.coef[::-1])(i) for i in self.min_max]
		    
		elif sorted(fit_poly_ranges)==fit_poly_ranges:
			
		  if len(fit_poly_ranges)%2==0:
				indcs=[]
				self.acc_min_max_tot=[]
				self.acc_nn_tot=[]
				self.rej_min_max_tot=[]
				self.rej_nn_tot=[]
				# add first and last index element from the min_max list 
				ranges=[self.min_max[0]]+fit_poly_ranges+[self.min_max[-1]]
				for ii,iii in zip(ranges,range(len(ranges))):
				  if iii>1 and iii%2==0:
				    indcs.extend([ np.argmin(np.abs(np.array(self.min_max)-ii))+1 ])
				  else:
				    indcs.extend([ np.argmin(np.abs(np.array(self.min_max)-ii)) ])
				  #indcs.extend([ min(range(len(min_max)), key=lambda i: abs(min_max[i]-ii)) ])
				for ii in range(len(indcs)):
				  if ii<len(indcs)-1:
				    if ii%2==0:
				      self.rej_min_max_tot.extend( self.min_max[indcs[ii]:indcs[ii+1]] )
				      self.rej_nn_tot.extend( self.nn[indcs[ii]:indcs[ii+1]] )
				      
				    else:
				      self.acc_min_max_tot.extend( self.min_max[indcs[ii]:indcs[ii+1]] )
				      self.acc_nn_tot.extend( self.nn[indcs[ii]:indcs[ii+1]] )
					      
				################################################
				self.coef = P.polyfit(self.acc_min_max_tot,self.acc_nn_tot,fit_poly_order)
				self.curve_ = [np.poly1d(self.coef[::-1])(i) for i in self.min_max]
		  else:
				raise ValueError('The fit_poly_ranges list accepts only even number of enteries! Check your list once again')   
		else:
		  raise ValueError('The fit_poly_ranges list is not sorted in ascending order! Check your list once again')
 
  def alpha_(self):
    #print 'method alpha_ runs...'
    
    return self.common_xaxis, self.alpha_wm

  def alpha_strabs_appendix(self):
    #print 'method alpha_strabs_appendix runs...'
    
    #common_xaxis2, alpha_wm = alpha_(ignored_points,my_string, num)
    #tsub_=gtt.Tsub(num)
    xxx, Ts = gtt.combined_Ts(0)
    #xxx, Ts = gtt.combined_Ts()
    #min_max, nn = gmd.get_new_n(ignored_points, my_string, num)
    #self.d=gmd.Gmd().get_md()[3]
    x_all,y_all = gtt.combined_Tr()
    
    ################################################
    '''
    if not fit_poly_ranges:
      minmax, dummy2, dummy3, coef = show_n_fit()
    elif sorted(fit_poly_ranges)==fit_poly_ranges:
      dummy1, dummy2, [minmax,dummy3], coef = show_n_fit()
    else:
      raise ValueError('The fit_poly_ranges list is not sorted in ascending order! Check your list once again')
    #coef = P.polyfit(minmax,nn,4)
    #print "polyfit coef = ", coef
    '''
    ################################################
    
    if not strong_abs_start_eV:
      if x_all==xxx:
				print "Substrate x-axis data and deposited film x-axis data are equal - good"
				idx=np.argmin(np.abs(np.array(x_all)-self.min_max[-1]))
      else:
				print "Substrate x-axis data does NOT MATCH deposited film x-axis data"
      
      more_x = x_all[idx+1:]
      more_n = [np.poly1d(self.coef[::-1])(i) for i in more_x]
    else:
      if x_all==xxx:
				print "Substrate x-axis data and deposited film x-axis data are equal - good"
				idx=np.argmin(np.abs(np.array(x_all)-float(strong_abs_start_eV)))
				#idx = min(range(len(x_all)), key=lambda i: abs(x_all[i]-float(strong_abs_start_eV)))
      else:
				print "Substrate x-axis data does NOT MATCH deposited film x-axis data"
      
      more_x = x_all[idx+1:]
      more_n = [np.poly1d(self.coef[::-1])(i) for i in more_x]

    ######################################################################
    x_all_new=x_all[idx+1:]
    
    T0 = y_all[idx+1:]
    Ts_= Ts[idx+1:]

    #inds=range(len(more_x))
    #s = [(1.0/doh)+math.sqrt(1/doh**2-1) for doh in Ts_]
    s=1.0/np.array(Ts_)+(1.0/np.array(Ts_)**2-1)**0.5
    # take absolute of T0 since it might become negative in the strong absorption region
    
    xexp_wm=[]
    bad_x_vals=[]
    for i in range(len(more_x)):
      R1=((1-more_n[i])/(1+more_n[i]))**2
      R2=((more_n[i]-s[i])/(more_n[i]+s[i]))**2
      R3=((s[i]-1)/(s[i]+1))**2
      Pp=(R1-1)*(R2-1)*(R3-1)
      
      Q=2*T0[i]*(R1*R2+R1*R3-2*R1*R2*R3)
      xexp_wm.extend([ (Pp+math.sqrt(Pp**2+2*Q*T0[i]*(1-R2*R3)))/Q ])
      # give a warning if xexp_wm becomes negative
      if (Pp+math.sqrt(Pp**2+2*Q*T0[i]*(1-R2*R3)))/Q<=0:
				bad_x_vals.extend([ i ])
	
    if bad_x_vals:
      print "WARNING: x in eq. A3 in Swanepoel is negative or zero from",  x_all_new[bad_x_vals[0]], "eV"
    
    ######################################################################
    #x=math.exp(-alpha*d)
    alpha_wm_=[-math.log(abs(doh))/self.d for doh in xexp_wm]
    
    return more_x, alpha_wm_

  def show_n_fit(self):
    #print 'method show_n_fit runs...'
    
    #self.min_max, self.nn = gmd.Gmd().get_new_n()
    
    if not fit_poly_ranges:
      print "polyfit coefs( order", fit_poly_order,") = ", self.coef
      return self.min_max, self.nn, self.curve_, self.coef
	  
    elif sorted(fit_poly_ranges)==fit_poly_ranges:
      if len(fit_poly_ranges)%2==0:
				print "polyfit coefs( order", fit_poly_order,") = ", self.coef
				return [self.acc_min_max_tot,self.rej_min_max_tot], [self.acc_nn_tot,self.rej_nn_tot], [self.min_max,self.curve_], self.coef
      else:
				raise ValueError('The fit_poly_ranges list accepts only even number of enteries! Check your list once again')   
    else:
      raise ValueError('The fit_poly_ranges list is not sorted in ascending order! Check your list once again')
  
  
if __name__ == "__main__":

  analysis_folder, data_folder, raw_olis, raw_ftir, sub_olis, sub_ftir=gtt.folders_and_data()
  
  plt.figure(1, figsize=(15,10))
  
  if ese==0 or ese==0.0:
		
    Alpha_class=Alpha(0.0)
    common_xaxis1 , alpha_wm1 = Alpha_class.alpha_()
    common_xaxis2 , alpha_wm2 = Alpha_class.alpha_strabs_appendix()
    
    common_xaxis = common_xaxis1+common_xaxis2
    alpha_wm = alpha_wm1+alpha_wm2
    
    ###############################################################
 
    plt.plot(common_xaxis1 , 1e4*np.array(alpha_wm1), 'ro-', label=''.join(['alpha, ', my_string, ' interp']))    
    plt.plot(common_xaxis2 , 1e4*np.array(alpha_wm2), 'go-', label=''.join(['alpha, strong abs ', \
      my_string, ' interp']))
  
  else:
    Alpha_class=Alpha(0.0)
    Alpha_class_p=Alpha(ese)
    Alpha_class_m=Alpha(-ese)
    
    common_xaxis1 , alpha_wm1 = Alpha_class.alpha_()
    common_xaxis1_ , alpha_wm1_ = Alpha_class_p.alpha_()
    common_xaxis1__ , alpha_wm1__ = Alpha_class_m.alpha_()
    
    common_xaxis2 , alpha_wm2 = Alpha_class.alpha_strabs_appendix()
    common_xaxis2_ , alpha_wm2_ = Alpha_class_p.alpha_strabs_appendix()
    common_xaxis2__ , alpha_wm2__ = Alpha_class_m.alpha_strabs_appendix()
    
    common_xaxis = common_xaxis1+common_xaxis2
    alpha_wm = alpha_wm1+alpha_wm2
    alpha_wm_ = alpha_wm1_+alpha_wm2_
    alpha_wm__ = alpha_wm1__+alpha_wm2__
    
    ###############################################################
  
    plt.plot(common_xaxis1 , 1e4*np.array(alpha_wm1), 'ro-', label=''.join(['alpha, ', my_string, ' interp']))
    plt.fill_between(common_xaxis1, 1e4*np.array(alpha_wm1_), 1e4*np.array(alpha_wm1__), facecolor='blue', \
      alpha=0.2)
    
    plt.plot(common_xaxis2 , 1e4*np.array(alpha_wm2), 'go-', label=''.join(['alpha, strong abs ', \
      my_string, ' interp']))
    plt.fill_between(common_xaxis2, 1e4*np.array(alpha_wm2_), 1e4*np.array(alpha_wm2__), facecolor='yellow', \
      alpha=0.2)
  
  plt.xlabel("E, eV", fontsize=20)
  plt.ylabel("alpha, *10^3 cm^-1", fontsize=20)
  plt.title("Swanepoel (1983) absorption method applied to photospectrometer data")
  plt.tick_params(axis="both", labelsize=20)
  #plt.yticks( np.linspace(2,3,11) )
  #plt.ylim([-0.1,5])
  #plt.xlim([95,108])
  l=plt.legend(loc=2, fontsize=20)
  l.draw_frame(False)
  
  if not raw_olis:
    string_1 = ''.join([analysis_folder, raw_ftir, '_alpha_eV_', my_string,'_', timestr, '.png'])
  else:
    string_1 = ''.join([analysis_folder, raw_olis, '_alpha_eV_', my_string,'_', timestr, '.png'])
  plt.savefig(string_1)
  plt.show()

  if not raw_olis:
    string_2 = ''.join([analysis_folder, raw_ftir, '_alpha_', my_string,'_', timestr, '.txt'])
  else:
    string_2 = ''.join([analysis_folder, raw_olis, '_alpha_', my_string,'_', timestr, '.txt'])
  
  thefile = open(string_2, 'w')
  thefile.write(''.join(['Interpolation method for Tmin and Tmax points is ', my_string, '\n']))
  thefile.write(''.join(['The raw_olis data file is ', raw_olis, '\n']))
  thefile.write(''.join(['The raw_ftir data file is ', raw_ftir, '\n']))
  thefile.write(''.join(['The sub_olis data file is ', sub_olis, '\n']))
  thefile.write(''.join(['The sub_ftir data file is ', sub_ftir, '\n']))
  thefile.write('Column 1: energy in eV\n')
  thefile.write('Column 2: alpha *1e3 in 1/cm\n')
  if not ese or ese==0.0:   
    thefile.write('Column 3: lambda in nm\n')
    thefile.write('Column 4: alpha *1e3 in 1/cm\n')
  else:
    thefile.write(''.join(['Column 3: alpha *1e3 in 1/cm, ', str(1+ese) ,'*Ts (upper Ts limit)\n']))
    thefile.write(''.join(['Column 4: alpha *1e3 in 1/cm, ', str(1-ese) ,'*Ts (lower Ts limit)\n']))
    thefile.write('Column 5: lambda in nm\n')
    thefile.write('Column 6: alpha *1e3 in 1/cm\n')
    thefile.write(''.join(['Column 7: alpha *1e3 in 1/cm, ', str(1+ese) ,'*Ts (upper Ts limit)\n']))
    thefile.write(''.join(['Column 8: alpha *1e3 in 1/cm, ', str(1-ese) ,'*Ts (lower Ts limit)\n']))

  for i in range(len(common_xaxis)):
    thefile.write("%s\t" % common_xaxis[i])
    thefile.write("%s\t" % [1e4*alpha_wm[i]][0])
    if not ese or ese==0.0:
      thefile.write("%s\t" % [1239.84187/common_xaxis[i]][0])
      thefile.write("%s\n" % [1e4*alpha_wm[i]][0])
    else:
      thefile.write("%s\t" % [1e4*alpha_wm_[i]][0])
      thefile.write("%s\t" % [1e4*alpha_wm__[i]][0]) 
      thefile.write("%s\t" % [1239.84187/common_xaxis[i]][0])
      thefile.write("%s\t" % [1e4*alpha_wm[i]][0])
      thefile.write("%s\t" % [1e4*alpha_wm_[i]][0])
      thefile.write("%s\n" % [1e4*alpha_wm__[i]][0])
     
  thefile.close()
  
  ###############################################################
  
  plt.figure(2, figsize=(15,10))
  
  if not ese or ese==0.0:
    plt.plot(1239.84187/np.array(common_xaxis1) , 1e4*np.array(alpha_wm1), 'bo-', \
      label=''.join(['alpha, ', my_string, ' interp']))
    plt.plot(1239.84187/np.array(common_xaxis2) , 1e4*np.array(alpha_wm2), 'yx-', \
      label=''.join(['alpha, strong abs ', my_string, ' interp']))
    
  else:
    plt.plot(1239.84187/np.array(common_xaxis1) , 1e4*np.array(alpha_wm1), 'bo-', \
      label=''.join(['alpha, ', my_string, ' interp']))
    plt.fill_between(1239.84187/np.array(common_xaxis1), 1e4*np.array(alpha_wm1_), \
      1e4*np.array(alpha_wm1__), facecolor='blue', alpha=0.2)
    
    plt.plot(1239.84187/np.array(common_xaxis2) , 1e4*np.array(alpha_wm2), 'yx-', \
      label=''.join(['alpha, strong abs ', my_string, ' interp']))
    plt.fill_between(1239.84187/np.array(common_xaxis2), 1e4*np.array(alpha_wm2_), \
      1e4*np.array(alpha_wm2__), facecolor='yellow', alpha=0.2)
  
  plt.xlabel("lambda, nm", fontsize=20)
  plt.ylabel("alpha, *10^3 cm^-1", fontsize=20)
  plt.title("Swanepoel (1983) absorption method applied to photospectrometer data")
  plt.tick_params(axis="both", labelsize=20)
  #plt.yticks( np.linspace(2,3,11) )
  #plt.ylim([-0.1,5])
  #plt.xlim([95,108])
  l=plt.legend(loc=2, fontsize=20)
  l.draw_frame(False)
  
  if not raw_olis:
    string_2 = ''.join([analysis_folder, raw_ftir, '_alpha_nm_', my_string,'_', timestr, '.png'])
  else:
    string_2 = ''.join([analysis_folder, raw_olis, '_alpha_nm_', my_string,'_', timestr, '.png'])
  plt.savefig(string_2)
  plt.show()
  
  ###############################################################
  min_max2, nn2, curve_2, coef = Alpha(0.0).show_n_fit()

  if fit_poly_order==1:
    fit_poly_string=''.join(['n2, polyfit (', str(fit_poly_order),'st order)'])
  elif fit_poly_order==2:
    fit_poly_string=''.join(['n2, polyfit (', str(fit_poly_order),'nd order)'])
  elif fit_poly_order==3:
    fit_poly_string=''.join(['n2, polyfit (', str(fit_poly_order),'rd order)'])
  else:
    fit_poly_string=''.join(['n2, polyfit (', str(fit_poly_order),'th order)'])

  if not fit_poly_ranges:
    plt.figure(3, figsize=(15,10))
    plt.plot(min_max2 , nn2, 'go', label=''.join(['n2, ', my_string, ' interp']))
    plt.plot(min_max2, curve_2, 'k-', label=fit_poly_string)
  else:
    plt.figure(3, figsize=(15,10))
    plt.plot(min_max2[0] , nn2[0], 'go', label=''.join(['n2, ', my_string, ' interp (acc. points)']))
    plt.plot(min_max2[1] , nn2[1], 'ro', label=''.join(['n2, ', my_string, ' interp (rej. points)']))
    plt.plot(curve_2[0] , curve_2[1], 'k-', label=fit_poly_string)
    
  plt.xlabel("E, eV", fontsize=20)
  plt.ylabel("n", fontsize=20)
  plt.tick_params(axis="both", labelsize=20)
  l=plt.legend(loc=2, fontsize=20)
  l.draw_frame(False)
  
  if not raw_olis:
    save_fit_poly = ''.join([analysis_folder, raw_ftir, fit_poly_string,'_', timestr,'.png'])
  else:
    save_fit_poly = ''.join([analysis_folder, raw_olis, fit_poly_string,'_', timestr,'.png'])
  plt.savefig(save_fit_poly)
  plt.show()




