## Import libraries
import time, math
import numpy as np
import matplotlib.pyplot as plt
import Get_TM_Tm_v0 as gtt
from numpy.polynomial import polynomial as P
#from numpy import linalg as lng
import n
import os, sys
'''
## For Matplotlib fonts
from matplotlib import rc
## for LaTeX style use:
rc("text", usetex=True)
rc("font", family="serif")
'''
## Define absorption (alpha) functions  

gtt = gtt.Get_TM_Tm()
ese = gtt.get_Expected_Substrate_Dev() 
my_string = gtt.get_method()
ignored_points = gtt.ig_po()
analysis_folder, data_folder, raw_olis, raw_ftir, sub_olis, sub_ftir=gtt.folders_and_data()
timestr = time.strftime("%Y%m%d-%H%M%S")

class Gmd:
	
  def __init__(self,num):
		
    axis_ev, self.nn = n.N_class().n_wm()
    # convert to wavelength in nm
    self.common_xaxis = 1239.84187/np.array(axis_ev)
    
    self.get_x=1e3*np.array(self.nn)/np.array(self.common_xaxis)
    self.get_y=np.array(range(len(self.nn)))/2.0
    
    ################################################
    ################################################
    
    if not ignored_points:
      print "WARNING: ignored_points list is empty! Entire get_x list is used to find the polyfit curve. Limit the range of points if needed"
      ################################################
      self.coef = P.polyfit(self.get_x,self.get_y,1)
      self.curve_ = [np.poly1d(self.coef[::-1])(i) for i in self.get_x]
      
      self.a=self.coef[1]
      self.b=self.coef[0]
      m_1 = round(-self.b*2.0)/2.0
      m_end = m_1+(len(self.common_xaxis)-1)/2.0
      self.m = [.5*x for x in range(int(m_1*2), int(m_end*2+1))]
      d_all=np.array(self.m)*np.array(self.common_xaxis)/(2.0*np.array(self.nn))
      
      self.d_mean = np.mean(d_all)
        
    elif sorted(ignored_points)==ignored_points:
      if len(ignored_points)%2==0:
				indcs=[]
				self.acc_x_tot=[]
				self.acc_y_tot=[]
				self.rej_x_tot=[]
				self.rej_y_tot=[]
				# add first and last index element from the get_x list 
				ranges=[self.get_x[0]]+ignored_points+[self.get_x[-1]]
				for ii,iii in zip(ranges,range(len(ranges))):
				  if iii>1 and iii%2==0:
				    indcs.extend([ np.argmin(np.abs(np.array(self.get_x)-ii))+1 ])
				  else:
				    indcs.extend([ np.argmin(np.abs(np.array(self.get_x)-ii)) ])
				  #indcs.extend([ min(range(len(get_x)), key=lambda i: abs(get_x[i]-ii)) ])
				for ii in range(len(indcs)):
				  if ii<len(indcs)-1:
				    if ii%2==0:
				      self.rej_x_tot.extend( self.get_x[indcs[ii]:indcs[ii+1]] )
				      self.rej_y_tot.extend( self.get_y[indcs[ii]:indcs[ii+1]] )
				    else:
				      self.acc_x_tot.extend( self.get_x[indcs[ii]:indcs[ii+1]] )
				      self.acc_y_tot.extend( self.get_y[indcs[ii]:indcs[ii+1]] )
						
				self.coef = P.polyfit(self.acc_x_tot,self.acc_y_tot,1)
				self.curve_ = [np.poly1d(self.coef[::-1])(i) for i in self.get_x]
				
				self.a=self.coef[1]
				self.b=self.coef[0]
				m_1 = round(-self.b*2.0)/2.0
				m_end = m_1+(len(self.common_xaxis)-1)/2.0
				self.m = [.5*x for x in range(int(m_1*2), int(m_end*2+1))]
				d_all_rej=[]
				d_all_acc=[]
				for ii in range(len(indcs)):
				  if ii<len(indcs)-1:
				    if ii%2==0:
				      d_all_rej.extend( np.array(self.m[indcs[ii]:indcs[ii+1]])*np.array(self.common_xaxis[indcs[ii]:indcs[ii+1]])/(2*np.array(self.nn[indcs[ii]:indcs[ii+1]])) )
				    else:
				      d_all_acc.extend( np.array(self.m[indcs[ii]:indcs[ii+1]])*np.array(self.common_xaxis[indcs[ii]:indcs[ii+1]])/(2*np.array(self.nn[indcs[ii]:indcs[ii+1]])) )
				
				self.d_mean = np.mean(d_all_acc)
      else:
				raise ValueError('The ignored_points list accepts only even number of enteries! Check your list once again')   
    else:
      raise ValueError('The ignored_points list is not sorted in ascending order! Check your list once again')
			    
    ################################################
    ################################################
    if not raw_olis:
      string_1_ = ''.join([analysis_folder, raw_ftir, '_d_mean_', my_string, '.txt'])
    else:
      string_1_ = ''.join([analysis_folder, raw_olis, '_d_mean_', my_string, '.txt'])
    ################################################
    ################################################
    
  
    '''   
    if not os.path.isdir(analysis_folder):
		os.makedirs(analysis_folder)
    '''
    
    with open(string_1_, 'w') as thefile:
	    thefile.write(''.join(['Interpolation method for Tmin and Tmax points is ', my_string, '\n']))
	    thefile.write(''.join(['The raw_olis data file is ', raw_olis, '\n']))
	    thefile.write(''.join(['The raw_ftir data file is ', raw_ftir, '\n']))
	    thefile.write(''.join(['The sub_olis data file is ', sub_olis, '\n']))
	    thefile.write(''.join(['The sub_ftir data file is ', sub_ftir, '\n']))
	    thefile.write('Substrate thickness in nm \n')
	    thefile.write("%s" % self.d_mean)
	    
  def get_md(self):
    #print 'method get_md runs...'
    
    if not ignored_points:
      return self.get_x, self.get_y, self.curve_, self.coef, self.d_mean
	  
    elif sorted(ignored_points)==ignored_points:
      if len(ignored_points)%2==0:
	return [self.acc_x_tot,self.rej_x_tot], [self.acc_y_tot,self.rej_y_tot], \
	  [self.get_x,self.curve_], self.coef, self.d_mean
      else:
	raise ValueError('The ignored_points list accepts only even number of enteries! Check your list once again')   
    else:
      raise ValueError('The ignored_points list is not sorted in ascending order! Check your list once again')
    
  def get_md_igpo(self,ignored_points):
    #print 'method get_md_igpo runs...'

    if ignored_points>0:
      coef = P.polyfit(self.get_x[:-ignored_points],self.get_y[:-ignored_points],1)
      
      a=coef[1]
      b=coef[0]
      m_1 = round(-b*2.0)/2.0
      m_end = m_1+(len(self.common_xaxis)-1)/2.0
      m = [.5*x for x in range(int(m_1*2), int(m_end*2+1))]
      d_all=np.array(m)*np.array(self.common_xaxis)/(2*np.array(self.nn))
      
      d_mean = np.mean(d_all[:-ignored_points])
      print 'd_mean = ', d_mean
      
    elif ignored_points==0:
      coef = P.polyfit(self.get_x,self.get_y,1)
      
      a=coef[1]
      b=coef[0]
      m_1 = round(-b*2.0)/2.0
      m_end = m_1+(len(self.common_xaxis)-1)/2.0
      m = [.5*x for x in range(int(m_1*2), int(m_end*2+1))]
      d_all=np.array(m)*np.array(self.common_xaxis)/(2*np.array(self.nn))
 
      d_mean = np.mean(d_all)
      print 'd_mean = ', d_mean
    else:
      raise ValueError('Number of ignored points should be at least zero')
    
    return self.get_x, self.get_y, coef, d_mean
  
  def get_new_n(self):
    #print 'method get_new_n runs...'
    
    nn_=np.array(self.m)*np.array(self.common_xaxis)/(2.0*self.d_mean)
    
    # convert back to eV
    xaxis_ev=1239.84187/np.array(self.common_xaxis)
    #xaxis_ev = [1239.84187/tal for tal in self.common_xaxis]
    
    return xaxis_ev, nn_

  def fit_line(self):
    #print 'method fit_line runs...'
    
    myline_x=[]
    myline_x.extend([0.0])
    myline_x.extend(self.get_x)
    myline_x = sorted(myline_x)
    print "a , b = ", self.a*1e3, self.b
    print "m1 = ", round(-self.b*2.0)/2.0
    print 'd_mean = ', self.d_mean
    myline_y = self.b+self.a*np.array(myline_x)

    return self.a, self.b, self.d_mean, myline_x, self.get_x, self.get_y, myline_y
  
if __name__ == "__main__":

  ###########################################
  

  Gmd_class_0=Gmd(0.0)
  
  a_0, b_0, d_mean_0, myline_x_0, get_x_0, get_y_0, myline_y_0 = Gmd_class_0.fit_line()
  get_x_copy_0, get_y_copy_0, curve_0, coef_0, d_mean_copy_0 = Gmd_class_0.get_md()
  #get_x=1e3*np.array(get_x)
  
  if not ignored_points:
    f=plt.figure(1, figsize=(15,10))
    ax=f.add_subplot(111)
    plt.plot(get_x_copy_0, get_y_copy_0, 'go', label=''.join(['acc. points, ', my_string]))
    plt.plot(get_x_copy_0, curve_0, 'k-', label='Least sq. line fit')
  else:
    f=plt.figure(1, figsize=(15,10))
    ax=f.add_subplot(111)
    plt.plot(get_x_copy_0[0] , get_y_copy_0[0], 'go', label=''.join(['acc. points, ', my_string]))
    plt.plot(get_x_copy_0[1] , get_y_copy_0[1], 'ro', label=''.join(['rej. points, ', my_string]))
    plt.plot(curve_0[0] , curve_0[1], 'k-', label='Least sq. line fit')
      
  plt.xlabel("n/lambda, *10^-3 nm^-1", fontsize=20)
  plt.ylabel("l/2", fontsize=20)
  plt.title("Order number m1 and thickness d based on Swanepoel (1983)")
  
  a_norm=1e3*a_0
  string_1 = ''.join(['a , b = ', str("%.2f" % a_norm), ' , ', str("%.2f" %b_0), '\n'])
  string_2 = ''.join(['m1 = ', str(round(-b_0*2.0)/2.0), '\n'])
  string_3 = ''.join(['d_mean = ', str("%.1f" % d_mean_0 ), ' nm\n'])
  string_tot = ''.join([string_1, string_2, string_3])
  plt.text(0.72,0.1, string_tot, fontsize=16, ha='left', va='center', transform=ax.transAxes)
  
  plt.tick_params(axis="both", labelsize=20)
  #plt.yticks( np.linspace(-10,60,15) )
  #plt.ylim([-10,60])
  #plt.xlim([0,7])
  l=plt.legend(loc=9, fontsize=15)
  l.draw_frame(False)

  if not raw_olis:
    string_1 = ''.join([analysis_folder, raw_ftir, '_m_index_', my_string,'_', timestr, '.png'])
  else:
    string_1 = ''.join([analysis_folder, raw_olis, '_m_index_', my_string,'_', timestr, '.png'])
  plt.savefig(string_1)
  plt.show()

  ###################
  # save as txt file
  if not raw_olis:
    string_1_ = ''.join([analysis_folder, raw_ftir, '_m_index_', my_string,'_', timestr, '.txt'])
  else:
    string_1_ = ''.join([analysis_folder, raw_olis, '_m_index_', my_string,'_', timestr, '.txt'])
  thefile = open(string_1_, 'w')
  thefile.write(''.join(['Interpolation method for Tmin and Tmax points is ', my_string, '\n']))
  thefile.write(''.join(['The raw_olis data file is ', raw_olis, '\n']))
  thefile.write(''.join(['The raw_ftir data file is ', raw_ftir, '\n']))
  thefile.write(''.join(['The sub_olis data file is ', sub_olis, '\n']))
  thefile.write(''.join(['The sub_ftir data file is ', sub_ftir, '\n']))
  thefile.write('Column 1-2: raw data (x,y), Column 3-4 fitted line (x,y)\n')
  thefile.write('x = n/lambda [*1e-3 in 1/nm], y = l/2 [arb. units] where l=0,1,2...\n')
  thefile.write('x\t\ty\tx\t\ty \n')
  for i in range(len(myline_x_0)):
    if i<len(get_x_0)-1 or i==len(get_x_0)-1:
      thefile.write("%s\t" % get_x_0[i])
      thefile.write("%s\t" % get_y_0[i])
      thefile.write("%s\t" % myline_x_0[i])
      thefile.write("%s\n" % myline_y_0[i])    
    else:
      thefile.write("\t\t\t%s\t" % myline_x_0[i])
      thefile.write("%s\n" % myline_y_0[i])	
      
  thefile.close()
  ###################

  if not ese or ese==0.0:
    common_xaxis_, nn_ = Gmd_class_0.get_new_n()
    axis_ev, nn = n.N_class(0.0).n_wm()
  else:
    Gmd_class_p=Gmd(ese)
    Gmd_class_m=Gmd(-ese)
    
    common_xaxis_, nn_ = Gmd_class_0.get_new_n()
    common_xaxis_p, nn_p = Gmd_class_p.get_new_n()
    common_xaxis_m, nn_m = Gmd_class_m.get_new_n()
    axis_ev, nn = n.N_class(0.0).n_wm()
  
  plt.figure(2, figsize=(15,10))
  if not ese or ese==0.0:
    plt.plot(1239.84187/np.array(common_xaxis_), nn_, 'ro-', label=''.join(['n2, ', my_string]))
    plt.plot(1239.84187/np.array(axis_ev), nn, 'ko-', label=''.join(['n1, ', my_string]))
  else:
    plt.plot(1239.84187/np.array(common_xaxis_), nn_, 'ro-', label=''.join(['n2, ', my_string]))
    plt.plot(1239.84187/np.array(axis_ev), nn, 'ko-', label=''.join(['n1, ', my_string]))
    plt.fill_between(1239.84187/np.array(common_xaxis_), nn_p, nn_m, facecolor='blue', alpha=0.2)
    
  plt.xlabel("lambda, nm", fontsize=20)
  plt.ylabel("Ref. Index n", fontsize=20)
  plt.title("Ref index n based on Swanepoel (1983)")
  plt.tick_params(axis="both", labelsize=20)
  #plt.ylim([0,5])
  #plt.yticks( np.linspace(2,3,11) )
  l=plt.legend(loc=1, fontsize=15)
  l.draw_frame(False)
  
  if not raw_olis:
    string_2 = ''.join([analysis_folder, raw_ftir, '_new_n_', my_string,'_', timestr, '.png'])
  else:
    string_2 = ''.join([analysis_folder, raw_olis, '_new_n_', my_string,'_', timestr, '.png'])
  plt.savefig(string_2)
  plt.show()
  
  ###################
  # save datas as a txt file  
  if not raw_olis:
    string_1_ = ''.join([analysis_folder, raw_ftir, '_n_', my_string,'_', timestr, '.txt'])
  else:
    string_1_ = ''.join([analysis_folder, raw_olis, '_n_', my_string,'_', timestr, '.txt'])
    
  thefile = open(string_1_, 'w')
  thefile.write(''.join(['Interpolation method for Tmin and Tmax points is ', my_string, '\n']))
  thefile.write(''.join(['The raw_olis data file is ', raw_olis, '\n']))
  thefile.write(''.join(['The raw_ftir data file is ', raw_ftir, '\n']))
  thefile.write(''.join(['The sub_olis data file is ', sub_olis, '\n']))
  thefile.write(''.join(['The sub_ftir data file is ', sub_ftir, '\n']))
  thefile.write('Column 1: lambda in eV\n')
  if not ese or ese==0.0:
    thefile.write('Column 2: n2\n')
    thefile.write('Column 3: energy in nm\n')
    thefile.write('Column 4: n2\n')
  else:
    thefile.write('Column 2: n2\n')
    thefile.write(''.join(['Column 3: n2, ', str(1+ese) ,'*Ts (upper Ts limit)\n']))
    thefile.write(''.join(['Column 4: n2, ', str(1-ese) ,'*Ts (lower Ts limit)\n']))
    thefile.write('Column 5: energy in nm\n')
    thefile.write('Column 6: n2\n')
    thefile.write(''.join(['Column 7: n2, ', str(1+ese) ,'*Ts (upper Ts limit)\n']))
    thefile.write(''.join(['Column 8: n2, ', str(1-ese) ,'*Ts (lower Ts limit)\n']))
    
  for i in range(len(common_xaxis_)):
    thefile.write("%s\t" % common_xaxis_[i])
    if not ese or ese==0.0:
      thefile.write("%s\t" % nn_[i])
      thefile.write("%s\t" % [1239.84187/common_xaxis_[i]][0])
      thefile.write("%s\n" % nn_[i])
    else:
      thefile.write("%s\t" % nn_[i])
      thefile.write("%s\t" % nn_p[i])
      thefile.write("%s\t" % nn_m[i])
      thefile.write("%s\t" % [1239.84187/common_xaxis_[i]][0])
      thefile.write("%s\t" % nn_[i])
      thefile.write("%s\t" % nn_p[i])
      thefile.write("%s\n" % nn_m[i])
     
  thefile.close()
  ###################



