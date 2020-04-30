## Import libraries
import time, math
import numpy as np
import matplotlib.pyplot as plt
import Get_TM_Tm as gtt
import get_m_d as gmd
'''
## For Matplotlib fonts
from matplotlib import rc
## for LaTeX style use:
rc("text", usetex=True)
rc("font", family="serif")
'''
## Define absorption (alpha) functions  

timestr = time.strftime("%Y%m%d-%H%M%S")

def m_asf_igp(my_string, num):
  #print 'method m_asf_igp runs...'
  get_gmd_class=gmd.Gmd(num)
  common_xaxis, Tmin, Tmax = gtt.Ext_interp(my_string).interp_T()
  a=[]
  b=[]
  m1=[]
  d_mean=[]
  for i in range(len(common_xaxis)-2):
    get_x, get_y, coef, d_m=get_gmd_class.get_md_igpo(i)
    
    m1.extend([ round(-coef[0]*2.0)/2.0 ])
    a.extend([ coef[1] ])
    b.extend([ coef[0] ])
    d_mean.extend([ d_m ])
    
  return range(len(common_xaxis)-2), m1, a, b, d_mean

########################################################################

if __name__ == "__main__":

  gtc=gtt.get_control_file()
  analysis_folder, data_folder, raw_olis, raw_ftir, sub_olis, sub_ftir=gtt.folders_and_data()
  method = gtt.get_method()
  
  ###################
  
  xx,  m1, aa, bb, d_mean = m_asf_igp(method, 0.0)
  
  plt.figure(1, figsize=(15,10))
  plt.plot(xx, bb, 'ro-', label=''.join(['b, ', method, ' interp']))
  plt.plot(xx, [-i for i in m1], 'b^-', label=''.join(['Index -m$_1$, ', method, ' interp']))
  
  plt.xlabel("No. of ignored points", fontsize=20)
  #plt.ylabel("Intersep. b", fontsize=20)
  plt.title("Y-axis intercept point b and index m1 as a function of ignored points")
  plt.tick_params(axis="both", labelsize=20)
  #plt.ylim([0,5])
  #plt.yticks( np.linspace(2,3,11) )
  l=plt.legend(loc=2, fontsize=15)
  l.draw_frame(False)

  string_1 = ''.join([analysis_folder, raw_olis, '_m_asf_igp_', method,'_', timestr, '.png'])
  plt.savefig(string_1)
  plt.show()
  
  ##############################################################
  
  plt.figure(2, figsize=(15,10))
  plt.plot(xx, [1000*i/2.0 for i in aa], 'ro-', label=''.join(['slope a/2, ', method, ' interp']))
  plt.plot(xx, d_mean, 'b^-', label=''.join(['d2, 2nd iter, ', method, ' interp']))
  
  plt.xlabel("No. of ignored points", fontsize=20)
  plt.ylabel("Film thickness, nm", fontsize=20)
  #plt.title("Film thickness (NOT final) calculated from the fitted line slope a")
  plt.tick_params(axis="both", labelsize=20)
  #plt.ylim([0,5])
  #plt.yticks( np.linspace(2,3,11) )
  l=plt.legend(loc=1, fontsize=15)
  l.draw_frame(False)

  string_2 = ''.join([analysis_folder, raw_olis, '_d_asf_igp_', method,'_', timestr, '.png'])
  plt.savefig(string_2)
  plt.show()
  
  ##############################################################
  # save all data as a txt file
  string_12_ = ''.join([analysis_folder, raw_olis, '_m_and_d_asf_igp_', method,'_', timestr, '.txt'])
  thefile = open(string_12_, 'w') 
  thefile.write(''.join(['Interpolation method for Tmin and Tmax points is ', method, '\n']))
  thefile.write(''.join(['The control python file is ', gtc, '\n']))
  thefile.write(''.join(['The raw_olis data file is ', raw_olis, '\n']))
  thefile.write(''.join(['The raw_ftir data file is ', raw_ftir, '\n']))
  thefile.write(''.join(['The sub_olis data file is ', sub_olis, '\n']))
  thefile.write(''.join(['The sub_ftir data file is ', sub_ftir, '\n']))
  thefile.write('Column 1: Number of ignored points\n')
  thefile.write('Column 2: Y-axis intersept point in nm\n')
  thefile.write('Column 3: -m_1 index (given by l/2) in nm\n')
  thefile.write('Column 4: Film thickness calculated from the slope a (NOT final) in nm\n')
  thefile.write('Column 5: Film thickness 2nd iteration (d2 in Table 1 in Swanepoel(1983)) in nm\n')
  for i in range(len(xx)):
    thefile.write("%s\t" % xx[i])
    thefile.write("%s\t" % bb[i])
    thefile.write("%s\t" % ([-ii for ii in m1])[i])
    thefile.write("%s\t" % ([1000*ii/2.0 for ii in aa])[i])
    thefile.write("%s\n" % d_mean[i])
  thefile.close()












