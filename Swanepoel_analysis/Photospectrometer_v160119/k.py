## Import libraries
import time, math
import numpy as np
import matplotlib.pyplot as plt
import Get_TM_Tm_v0 as gtt
import alpha as al
'''
## For Matplotlib fonts
from matplotlib import rc
## for LaTeX style use:
rc("text", usetex=True)
rc("font", family="serif")
'''
## Define k function 

timestr = time.strftime("%Y%m%d-%H%M%S")

class K_class:
	
  def __init__(self,num):
		
    self.Alpha_class=al.Alpha(num)

  def k1(self):
    #print 'method k runs...'
    common_xaxis , alpha_wm = self.Alpha_class.alpha_()
    
    # convert to wavelength in nm
    common_xaxis = [1239.84187/tal for tal in common_xaxis]
    
    k_=[common_xaxis[ii]*alpha_wm[ii]/(4*math.pi) for ii in range(len(common_xaxis))]
    
    # convert back to eV
    common_xaxis = [1239.84187/tal for tal in common_xaxis]
    
    return common_xaxis, k_

  def k1_strabs(self):
    #print 'method k runs...'
    common_xaxis , alpha_wm = self.Alpha_class.alpha_strabs_appendix()
    
    # convert to wavelength in nm
    common_xaxis = [1239.84187/tal for tal in common_xaxis]
    
    k_=[common_xaxis[ii]*alpha_wm[ii]/(4*math.pi) for ii in range(len(common_xaxis))]
    
    # convert back to eV
    common_xaxis = [1239.84187/tal for tal in common_xaxis]
    
    return common_xaxis, k_

	def make_plots(self):

	  #strong_abs_start_eV, fit_poly_order, fit_poly_ranges = gtt.str_abs_params()
	  #ignored_points = gtt.ig_po()
	  folder_str, filename_str, raw_olis, raw_ftir, sub_olis, sub_ftir=gtt.folders_and_data()
	  method = gtt.get_method()
	  
	  plt.figure(1, figsize=(15,10))
	  
	  ese = gtt.get_Expected_Substrate_Dev()
	  
	  if ese==0 or ese==0.0:
			
	    K_class_0=K_class(0.0)
	    common_xaxis2 , k_2 = K_class_0.k1()
	    common_xaxis4 , k_4 = K_class_0.k1_strabs()
	  
	    common_xaxis = common_xaxis2+common_xaxis4
	    k = k_2+k_4
		    
	    plt.plot(common_xaxis2 , 1e3*np.array(k_2), 'bo-', label=''.join(['k, ', method, ' interp']))   
	    plt.plot(common_xaxis4 , 1e3*np.array(k_4), 'yo-', label=''.join(['k, strong abs ', method, ' interp']))
	  
	  else:
			
	    K_class_0=K_class(0.0)
	    K_class_p=K_class(ese)
	    K_class_m=K_class(-ese)
	    
	    common_xaxis2 , k_2 = K_class_0.k1()
	    common_xaxis2_ , k_2_ = K_class_p.k1()
	    common_xaxis2__ , k_2__ = K_class_m.k1()
	    
	    common_xaxis4 , k_4 = K_class_0.k1_strabs()
	    common_xaxis4_ , k_4_ = K_class_p.k1_strabs()
	    common_xaxis4__ , k_4__ = K_class_m.k1_strabs()
	    
	    common_xaxis = common_xaxis2+common_xaxis4
	    k = k_2+k_4
	    k_ = k_2_+k_4_
	    k__ = k_2__+k_4__

	    plt.plot(common_xaxis2 , 1e3*np.array(k_2), 'bo-', label=''.join(['k, ', method, ' interp']))
	    plt.fill_between(common_xaxis2, 1e3*np.array(k_2_), 1e3*np.array(k_2__), facecolor='blue', alpha=0.2)
	    
	    plt.plot(common_xaxis4 , 1e3*np.array(k_4), 'yo-', label=''.join(['k, strong abs ', method, ' interp']))
	    plt.fill_between(common_xaxis4, 1e3*np.array(k_4_), 1e3*np.array(k_4__), facecolor='yellow', alpha=0.2)

	  plt.xlabel("E, eV", fontsize=20)
	  plt.ylabel("k, *10^-3", fontsize=20)
	  plt.title("Swanepoel (1983) k method applied to FTIR and OLIS data")
	  plt.tick_params(axis="both", labelsize=20)
	  #plt.yticks( np.linspace(2,3,11) )
	  #plt.ylim([2,3])
	  #plt.xlim([95,108])
	  l=plt.legend(loc=2, fontsize=15)
	  l.draw_frame(False)
	  
	  string_1 = ''.join([folder_str, filename_str, '_k_', method,'_', timestr, '.png'])
	  plt.savefig(string_1)
	  plt.show()

	  string_2 = ''.join([folder_str, filename_str, '_k_', method,'_', timestr, '.txt'])
	  
	  with open(string_2, 'w') as thefile:
		  thefile.write(''.join(['Interpolation method for Tmin and Tmax points is ', method, '\n']))
		  thefile.write(''.join(['The raw_olis data file is ', raw_olis, '\n']))
		  thefile.write(''.join(['The raw_ftir data file is ', raw_ftir, '\n']))
		  thefile.write(''.join(['The sub_olis data file is ', sub_olis, '\n']))
		  thefile.write(''.join(['The sub_ftir data file is ', sub_ftir, '\n']))
		  thefile.write('Column 1: energy in eV\n')
		  thefile.write('Column 2: k *1e-3\n')
		  if not ese or ese==0.0:
		    thefile.write('Column 3: lambda in nm\n')
		    thefile.write('Column 4: k *1e-3\n')
		  else:
		    thefile.write(''.join(['Column 3: k *1e-3, ', str(1+ese) ,'*Ts (upper Ts limit)\n']))
		    thefile.write(''.join(['Column 4: k *1e-3, ', str(1-ese) ,'*Ts (lower Ts limit)\n']))
		    thefile.write('Column 5: lambda in nm\n')
		    thefile.write('Column 6: k *1e-3\n')
		    thefile.write(''.join(['Column 7: k *1e-3, ', str(1+ese) ,'*Ts (upper Ts limit)\n']))
		    thefile.write(''.join(['Column 8: k *1e-3, ', str(1-ese) ,'*Ts (lower Ts limit)\n']))
		  
		  for i in range(len(common_xaxis)):
		    thefile.write("%s\t" % common_xaxis[i])
		    thefile.write("%s\t" % [1e3*k[i]][0])
		    if not ese or ese==0.0:
		      thefile.write("%s\t" % [1239.84187/common_xaxis[i]][0])
		      thefile.write("%s\n" % [1e3*k[i]][0])
		    else:
		      thefile.write("%s\t" % [1e3*k_[i]][0])
		      thefile.write("%s\t" % [1e3*k__[i]][0])
		      thefile.write("%s\t" % [1239.84187/common_xaxis[i]][0])
		      thefile.write("%s\t" % [1e3*k[i]][0]) 
		      thefile.write("%s\t" % [1e3*k_[i]][0])
		      thefile.write("%s\n" % [1e3*k__[i]][0])
	      
if __name__ == "__main__":
	
	make_plots()
  
  





