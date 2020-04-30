import sys, os, subprocess
import datetime, time
import Gpib, SR5210 
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D


timestr=time.strftime('%y%m%d-%H%M')
v=Gpib.Gpib(0,9)
time.sleep(0.5)
x_speed=380.0 # number of steps per second
y_speed=350.0 # number of steps per second

model_5210=SR5210.SR5210()
time.sleep(0.5)

if len(sys.argv)<2:
  raise ValueError('A setup file is required!')
else:
  inFile=sys.argv[1]
  params=__import__(inFile)

if len(params.x_scan_mm)!=3:
  raise ValueError('x_scan_mm is a list of 3 elements [x_start,x_end,x_step]')
if len(params.y_scan_mm)!=3:
  raise ValueError('y_scan_mm is a list of 3 elements [y_start,y_end,y_step]')

op_mode=params.op_mode
ASM_delay=params.asm_delay
if op_mode=='xyscan':
  xstart=int(params.x_scan_mm[0]*1000)
  xend=int(params.x_scan_mm[1]*1000)
  xstep=int(params.x_scan_mm[2]*1000)
  ystart=int(params.y_scan_mm[0]*10000)
  yend=int(params.y_scan_mm[1]*10000)
  ystep=int(params.y_scan_mm[2]*10000)
  xy_limiter=int(params.xy_limiter_mm*1000)
  wait_time=params.wait_time
  scan_mode=params.scan_mode
elif op_mode=='xscan':
  xstart=int(params.x_scan_mm[0]*1000)
  xend=int(params.x_scan_mm[1]*1000)
  xstep=int(params.x_scan_mm[2]*1000)
  xy_limiter=int(params.xy_limiter_mm*1000)
  wait_time=params.wait_time
elif op_mode=='yscan':
  ystart=int(params.y_scan_mm[0]*10000)
  yend=int(params.y_scan_mm[1]*10000)
  ystep=int(params.y_scan_mm[2]*10000)
  xy_limiter=int(params.xy_limiter_mm*1000)
  wait_time=params.wait_time
elif op_mode=='reset':
  reset_mode=params.reset_mode
elif op_mode in ['abs','rel']:
  if len(params.move_mm)!=2:
    raise ValueError('move_mm is a list of two elements, f.ex. move_mm=[-1,2]')
  move_x=int(params.move_mm[0]*1000)
  move_y=int(params.move_mm[1]*10000)
  xy_limiter=int(params.xy_limiter_mm*1000)
else:
  raise ValueError('Invalid operation mode (op_mode) input!')
  

if params.file_name:
  str_filename=''.join([params.file_name,timestr])
else:
  str_filename=''.join(['data_',timestr])

if params.new_folder:
  saveinfolder=''.join([params.new_folder,'/'])
  if not os.path.isdir(params.new_folder):
    os.mkdir(params.new_folder)
else:
  saveinfolder=''

############################################################
############################################################
############################################################

class IT6D_CA_6:
  def __init__(self):
    #constants
    self.data_file=''.join([saveinfolder,str_filename,'.txt'])
    self.data_file_spine=''.join([saveinfolder,str_filename,'_spine.txt'])
    self.abs_posx='it6d_ca2_pos_x.txt'
    self.abs_posy='it6d_ca2_pos_y.txt'
    self.set_delay=0.4
    self.ASM_delay=ASM_delay
    #self.XTC_delay=1.5
        
    if op_mode!='reset':
      if os.path.isfile(self.abs_posx)==False:
	raise ValueError(''.join(['Position file ', self.abs_posx,' does not exist!']))
      
      if os.path.isfile(self.abs_posy)==False:
	raise ValueError(''.join(['Position file ', self.abs_posy,' does not exist!']))
     
    if op_mode=='xyscan':
      if abs(xstart-xend)>xy_limiter:
	raise ValueError(''.join(['X_span limited to ', str(xy_limiter/1000.0), ' mm']))
      elif xstart<xend:
	if xstep<=0:
	  raise ValueError('x_step_mm should be positive!')
      elif xstart>xend:
	if xstep>=0:
	  raise ValueError('x_step_mm should be negative!')
      else:
	raise ValueError('x_start_mm and x_end_mm should not be equal!')
      
      if abs(ystart-yend)>xy_limiter*10:
	raise ValueError(''.join(['Y_span limited to ', str(xy_limiter/1000.0), ' mm']))
      elif ystart<yend:
	if ystep<=0:
	  raise ValueError('y_step_mm should be positive!')
      elif ystart>yend:
	if ystep>=0:
	  raise ValueError('y_step_mm should be negative!')
      else:
	raise ValueError('y_start_mm and y_end_mm should not be equal!')
    
    if op_mode=='xscan':
      if abs(xstart-xend)>xy_limiter:
	raise ValueError(''.join(['X_span limited to ', str(xy_limiter/1000.0), ' mm']))
      if xstart<xend:
	if xstep<=0:
	  raise ValueError('x_step_mm should be positive!')
      elif xstart>xend:
	if xstep>=0:
	  raise ValueError('x_step_mm should be negative!')
      else:
	raise ValueError('x_start_mm and x_end_mm should not be equal!')
      
    if op_mode=='yscan':
      if abs(ystart-yend)>xy_limiter*10:
	raise ValueError(''.join(['Y_span limited to ', str(xy_limiter/1000.0), ' mm']))
      elif ystart<yend:
	if ystep<=0:
	  raise ValueError('y_step_mm should be positive!')
      elif ystart>yend:
	if ystep>=0:
	  raise ValueError('y_step_mm should be negative!')
      else:
	raise ValueError('y_start_mm and y_end_mm should not be equal!')

  def init_lockin(self):
    pass
    '''
    # Set the reference source to external input mode
    model_5210.write(''.join(['IE 0']))
    time.sleep(1)
    # Turn off line frequency rejection filter
    model_5210.write(''.join(['LF 0']))
    time.sleep(1)
    # set auto-measure
    model_5210.write(''.join(['SEN 14']))
    time.sleep(2)
    '''

  def get_lockin_data(self):
    '''
    # get the output from the overload status command
    model_5210.write(''.join(['N\n']))
    time.sleep(self.set_delay)
    out_N=model_5210.read()
    # the N output is following LSB-0, therefore list inversion
    N_to_bin='{0:08b}'.format(int(out_N))[::-1]
    #print 'N_to_bin =', N_to_bin
    '''
    
    # set auto-measure
    #model_5210.write(''.join(['ASM']))
    #time.sleep(self.ASM_delay)
    
    # set the output filter slope to 12dB/ostave
    #model_5210.write(''.join(['XDB 1']))
    #time.sleep(self.set_delay)
    
    # set time constant to 100 ms, since previous ASM may have changed it 
    #model_5210.write(''.join(['XTC 4']))
    #time.sleep(self.set_delay)
    
    # get the present sensitivity setting
    #model_5210.write(''.join(['SEN']))
    #time.sleep(self.set_delay)
    senrangecode=model_5210.return_sen()
    print 'senrangecode =', senrangecode
    
    # for the equation see page 6-21 in the manual
    senrange=(1+(2*(int(senrangecode)%2)))*10**(int(senrangecode)/2-7)
    #print 'senrange =', senrange
    
    # reads X channel output
    #model_5210.write(''.join(['X']))
    #time.sleep(self.set_delay)
    outputuncalib=model_5210.return_X()
    #print 'outputuncalib =',outputuncalib
    
    # assuming N_to_bin[1]=='0' and N_to_bin[2]=='0'
    outputcalib=int(outputuncalib)*senrange*1e-4

    return outputcalib
  
  '''
  def set_lockin_sens(self,volt):
    # Model 5210 sensitivity table from page 6-9 in the manual
    sens_tab=[100e-9,300e-9,1e-6,3e-6,10e-6,30e-6,100e-6,300e-6,1e-3,3e-3,10e-3,30e-3,100e-3,300e-3,1,3]
    #sens_args=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
    idx1=np.argmin(np.abs(np.array(sens_tab)-volt))
    if sens_tab[idx1]>volt:
      model_5210.write(''.join(['SEN ',str(idx1),'\n']))
      time.sleep(1.5)
      return idx1
    else:
      model_5210.write(''.join(['SEN ',str(idx1+1),'\n']))
      time.sleep(1.5)
      return idx1+1
  '''
      
  def reset(self,axs):
    #reset the microstepper
    pos=0
    if axs=='x':
      v.write('C1O\n')
      with open(self.abs_posx,'w') as thefile:
	thefile.write('%s' %pos)
    elif axs=='y':
      v.write('C2O\n')
      with open(self.abs_posy,'w') as thefile:
	thefile.write('%s' %pos)
    elif axs=='xy':
      v.write('CCO\n')
      with open(self.abs_posx,'w') as thefile:
	thefile.write('%s' %pos)
      with open(self.abs_posy,'w') as thefile:
	thefile.write('%s' %pos)
    else:
      raise ValueError('Reset function accepets only x or y or xy!')
  
  def move_abs(self,axs,pos):
    # define a local function
    def time_to_str(sec):
      int_sec=int(((sec+0.5)*2)/2)
      return str(datetime.timedelta(seconds=int_sec))
    # x-axis moves approx 380 steps (um) per second
    # y-axis moves approx 350 steps (um) per second
    if axs=='x':
      # open x file
      with open(self.abs_posx,'r') as thefile:
	oldpos=thefile.read()
      #write a time trace for the user
      if op_mode=='absx':
	time_left=abs(int(oldpos)-pos)/x_speed
	print 'X_abs:',pos,', Scan time left:',time_to_str(time_left)
      # move and wait until movement finished
      if abs(int(oldpos)-pos)>xy_limiter:
	raise ValueError(''.join(['X_abs movements limited to ', str(xy_limiter/1000.0), ' mm']))
      elif pos>0:
        v.write(''.join(['I1=+',str(pos),'!\n']))
        time.sleep(abs(int(oldpos)-pos)/x_speed)
      elif pos<0:
        v.write(''.join(['I1=',str(pos),'!\n']))
        time.sleep(abs(int(oldpos)-pos)/x_speed)
      elif pos==0:
	v.write(''.join(['I1=-',str(pos),'!\n']))
	time.sleep(abs(int(oldpos)-pos)/x_speed)
      else:
	raise ValueError('The absolute position is an integer!')
      # save x file
      with open(self.abs_posx,'w') as thefile:
        thefile.write('%s' %pos)
    elif axs=='y':
      # open y file
      with open(self.abs_posy,'r') as thefile:
	oldpos=thefile.read()
      #write a time trace for the user
      if op_mode=='absy':
	time_left=abs(int(oldpos)-pos)/y_speed
	print 'Y_abs:',pos,', Scan time left:',time_to_str(time_left)
      # move and wait until movement finished
      if abs(int(oldpos)-pos)>xy_limiter*10:
	raise ValueError(''.join(['Y_abs movements limited to ', str(xy_limiter/1000.0), ' mm']))
      elif pos>0:
        v.write(''.join(['I2=+',str(pos),'!\n']))
        time.sleep(abs(int(oldpos)-pos)/y_speed)
      elif pos<0:
        v.write(''.join(['I2=',str(pos),'!\n']))
        time.sleep(abs(int(oldpos)-pos)/y_speed)
      elif pos==0:
	v.write(''.join(['I2=-',str(pos),'!\n']))
	time.sleep(abs(int(oldpos)-pos)/y_speed)
      else:
	raise ValueError('The absolute position is an integer!')
      # save y file
      with open(self.abs_posy,'w') as thefile:
        thefile.write('%s' %pos)
    else:
      raise ValueError('Axis can only be x or y!')

  def move_rel(self,axs,pos):
    # x-axis moves approx 380 steps (um) per second
    # y-axis moves approx 350 steps (um) per second
    if axs=='x':
      # open x file
      with open(self.abs_posx,'r') as thefile:
	oldpos=thefile.read()
      # calculate absolute position using the relative position
      newpos=int(oldpos)+pos
      if abs(pos)>xy_limiter:
	raise ValueError(''.join(['X_rel movements limited to ', str(xy_limiter/1000.0), ' mm']))
      # move and wait until movement finished
      if newpos>0:
        v.write(''.join(['I1=+',str(newpos),'!\n']))
        if op_mode=='relx':
	  print 'X_rel:', pos, ', Xnew_abs:', newpos
        time.sleep(abs(pos)/x_speed)
      elif newpos<0:
        v.write(''.join(['I1=',str(newpos),'!\n']))
        if op_mode=='relx':
	  print 'X_rel:', pos, ', Xnew_abs:', newpos
        time.sleep(abs(pos)/x_speed)
      elif newpos==0:
        v.write(''.join(['I1=-',str(newpos),'!\n']))
        if op_mode=='relx':
	  print 'X_rel:', pos, ', Xnew_abs:', newpos
        time.sleep(abs(pos)/x_speed)
      else:
	raise ValueError('The relative position is an integer!')
      # save x file
      with open(self.abs_posx,'w') as thefile:
        thefile.write('%s' %newpos) 
    elif axs=='y':
      # open y file
      with open(self.abs_posy,'r') as thefile:
	oldpos=thefile.read()
      # calculate absolute position using the relative position
      newpos=int(oldpos)+pos
      if abs(pos)>xy_limiter*10:
	raise ValueError(''.join(['Y_rel movements limited to ', str(xy_limiter/1000.0), ' mm']))
      # move and wait until movement finished
      if newpos>0:
        v.write(''.join(['I2=+',str(newpos),'!\n']))
        if op_mode=='rely':
	  print 'Y_rel:', pos, ', Ynew_abs:', newpos
	time.sleep(abs(pos)/y_speed)
      elif newpos<0:
        v.write(''.join(['I2=',str(newpos),'!\n']))
        if op_mode=='rely':
	  print 'Y_rel:', pos, ', Ynew_abs:', newpos
        time.sleep(abs(pos)/y_speed)
      elif newpos==0:
        v.write(''.join(['I2=-',str(newpos),'!\n']))
        if op_mode=='rely':
	  print 'Y_rel:', pos, ', Ynew_abs:', newpos
        time.sleep(abs(pos)/y_speed)
      else:
	raise ValueError('The relative position is an integer!')
      # save y file
      with open(self.abs_posy,'w') as thefile:
        thefile.write('%s' %newpos)
    else:
      raise ValueError('Axis can only be x or y!')

  def xyscan(self):
    # define a local function
    def time_to_str(sec):
      int_sec=int(((sec+0.5)*2)/2)
      return str(datetime.timedelta(seconds=int_sec))
    # initialize lockin 
    IT6D_CA_6().init_lockin()
    # set the microstepper to its initial positions
    IT6D_CA_6().move_abs('x',xstart)
    IT6D_CA_6().move_abs('y',ystart)

    with open(self.data_file, 'w') as thefile:
      thefile.write("Your edit line - do NOT delete this line\n") 
      thefile.write("X-pos [um], Y-pos [um], Voltage [V]\n")
      
    with open(self.data_file_spine, 'w') as thefile:
      thefile.write("Your edit line - do NOT delete this line\n") 
      thefile.write("X-pos [um], Y-pos [um], Max voltage [V]\n")
    
    try:
      count=0
      len_x=len(range(xstart,xend+xstep,xstep))
      len_y=len(range(ystart,yend+ystep,ystep))
      
      time_start=time.time()
      if scan_mode=='xwise':
	for ii in range(ystart,yend+ystep,ystep):
	  IT6D_CA_6().move_abs('y',ii)
	  for ss in range(xstart,xend+xstep,xstep):
	    IT6D_CA_6().move_abs('x',ss)
	    time.sleep(wait_time)
	    outputcalib=IT6D_CA_6().get_lockin_data()
	    with open(self.data_file, 'a') as thefile:
	      thefile.write('%s\t' %ss)
	      thefile.write('%s\t' %(0.1*ii))
	      thefile.write('%s\n' %outputcalib)
	    count+=1
	    time_end=time.time()
	    time_avg=(time_end-time_start)/count
	    time_str=time_to_str(time_avg*(len_x*len_y-count))
	    print 'X_abs:',ss, ', Y_abs:',ii, ', Vlockin:',outputcalib, ', Scan time left:', time_str
	    #print 'X_abs:',ss,', Y_abs:',ii,', Scan time left:', time_str
      elif scan_mode=='ywise':
	for ii in range(xstart,xend+xstep,xstep):
	  IT6D_CA_6().move_abs('x',ii)
	  for ss in range(ystart,yend+ystep,ystep):
	    IT6D_CA_6().move_abs('y',ss)
	    time.sleep(wait_time)
	    outputcalib=IT6D_CA_6().get_lockin_data()
	    with open(self.data_file, 'a') as thefile:
	      thefile.write('%s\t' %ii)
	      thefile.write('%s\t' %(0.1*ss))
	      thefile.write('%s\n' %outputcalib)
	    count+=1
	    time_end=time.time()
	    time_avg=(time_end-time_start)/count
	    time_str=time_to_str(time_avg*(len_x*len_y-count))
	    print 'X_abs:',ii, ', Y_abs:',ss, ', Vlockin:',outputcalib, ', Scan time left:', time_str
	    #print 'X_abs:',ii,', Y_abs:',ss,', Scan time left:', time_str
      elif scan_mode=='xsnake':
	turn=-1
	for ii in range(ystart,yend+ystep,ystep):
	  IT6D_CA_6().move_abs('y',ii)
	  turn=turn*-1
	  voltages=[]
	  pos_x=[]
	  for ss in range(xstart,xend+xstep,xstep)[::turn]:
	    IT6D_CA_6().move_abs('x',ss)
	    time.sleep(wait_time)
	    outputcalib=IT6D_CA_6().get_lockin_data()
	    with open(self.data_file, 'a') as thefile:
	      thefile.write('%s\t' %ss)
	      thefile.write('%s\t' %(0.1*ii))
	      thefile.write('%s\n' %outputcalib)
	    count+=1
	    ## change start
	    pos_x.extend([ ss ])
	    voltages.extend([ outputcalib ])	    
	    ## change end
	    time_end=time.time()
	    time_avg=(time_end-time_start)/count
	    time_str=time_to_str(time_avg*(len_x*len_y-count))
	    print 'X_abs:',ss, ', Y_abs:',ii, ', Vlockin:',outputcalib, ', Scan time left:', time_str
	    #print 'X_abs:',ss,', Y_abs:',ii,', Scan time left:', time_str
	  # change start
	  ind_max=np.argmax(voltages)
	  with open(self.data_file_spine, 'a') as thefile:
	    thefile.write('%s\t' %pos_x[ind_max])
	    thefile.write('%s\t' %(0.1*ii))
	    thefile.write('%s\n' %voltages[ind_max])
	  #change end
      elif scan_mode=='ysnake':
	turn=-1
	for ii in range(xstart,xend+xstep,xstep):
	  IT6D_CA_6().move_abs('x',ii)
	  turn=turn*-1
	  for ss in range(ystart,yend+ystep,ystep)[::turn]:
	    IT6D_CA_6().move_abs('y',ss)
	    time.sleep(wait_time)
	    outputcalib=IT6D_CA_6().get_lockin_data()
	    with open(self.data_file, 'a') as thefile:
	      thefile.write('%s\t' %ii)
	      thefile.write('%s\t' %(0.1*ss))
	      thefile.write('%s\n' %outputcalib)
	    count+=1
	    time_end=time.time()
	    time_avg=(time_end-time_start)/count
	    time_str=time_to_str(time_avg*(len_x*len_y-count))
	    print 'X_abs:',ii, ', Y_abs:',ss, ', Vlockin:',outputcalib, ', Scan time left:',time_str
	    #print 'X_abs:',ii,', Y_abs:',ss,', Scan time left:', time_str
      else:
	raise ValueError('Valid scan_mode input: xwise, ywise, xsnake, ysnake!')
    except KeyboardInterrupt:
      print('exiting...')
    
  def xscan(self):
    # define a local function
    def time_to_str(sec):
      int_sec=int(((sec+0.5)*2)/2)
      return str(datetime.timedelta(seconds=int_sec))
    # initialize lockin 
    IT6D_CA_6().init_lockin()
    # set the microstepper to its initial positions
    IT6D_CA_6().move_abs('x',xstart)

    with open(self.data_file, 'w') as thefile:
      thefile.write("Your edit line - do NOT delete this line\n") 
      thefile.write("X-pos [um], Voltage [V]\n")
      
    try:  
      count=0
      len_x=len(range(xstart,xend+xstep,xstep))
      
      time_start=time.time()
      for ii in range(xstart,xend+xstep,xstep):
	IT6D_CA_6().move_abs('x',ii)
	time.sleep(wait_time)
	outputcalib=IT6D_CA_6().get_lockin_data()
	with open(self.data_file, 'a') as thefile:
	  thefile.write('%s\t' %ii)
	  thefile.write('%s\n' %outputcalib)
	count+=1
	time_end=time.time()
	time_avg=(time_end-time_start)/count
	time_str=time_to_str(time_avg*(len_x-count))
	print 'X_abs:',ii, ', Vlockin:',outputcalib, ', Scan time left:', time_str
	#print 'X_abs:',ii,', Scan time left:', time_str
    except KeyboardInterrupt:
      print('exiting...')
	
  def yscan(self):
    # define a local function
    def time_to_str(sec):
      int_sec=int(((sec+0.5)*2)/2)
      return str(datetime.timedelta(seconds=int_sec))
    # initialize lockin 
    IT6D_CA_6().init_lockin()
    # set the microstepper to its initial positions
    IT6D_CA_6().move_abs('y',ystart)

    with open(self.data_file, 'w') as thefile:
      thefile.write("Your edit line - do NOT delete this line\n") 
      thefile.write("Y-pos [um], Voltage [V]\n")
    
    try:
      count=0
      len_y=len(range(ystart,yend+ystep,ystep))
      
      time_start=time.time()
      for ss in range(ystart,yend+ystep,ystep):
	IT6D_CA_6().move_abs('y',ss)
	time.sleep(wait_time)
	outputcalib=IT6D_CA_6().get_lockin_data()
	with open(self.data_file, 'a') as thefile:
	  thefile.write('%s\t' %(0.1*ss))
	  thefile.write('%s\n' %outputcalib)
	count+=1
	time_end=time.time()
	time_avg=(time_end-time_start)/count
	time_str=time_to_str(time_avg*(len_y-count))
	print 'Y_abs:',ss, ', Vlockin:',outputcalib, ', Scan time left:', time_str
	#print 'Y_abs:',ss,', Scan time left:', time_str
    except KeyboardInterrupt:
      print('exiting...')

def main():
  
  if op_mode=='xyscan':
    IT6D_CA_6().xyscan()
    data_raw=''.join([saveinfolder,str_filename,'.txt'])
    # plot the data as a contour plot
    X_data=[]
    Y_data=[]
    Lockin_data=[]
    with open(data_raw,'r') as thefile:
      header1=thefile.readline()
      header2=thefile.readline()
      for lines in thefile:
	columns=lines.split()
	X_data.extend([ float(columns[0]) ])
	Y_data.extend([ float(columns[1]) ])
	Lockin_data.extend([ float(columns[2]) ])
    fig=plt.figure(figsize=(8,6))
    ax= fig.add_subplot(111, projection='3d')
    #ax=fig.gca(projection='2d')
    ax.plot_trisurf(np.array(X_data),np.array(Y_data),np.array(Lockin_data),cmap=cm.jet,linewidth=0.2)
    ax.set_xlabel('X[um]')
    ax.set_ylabel('Y[um]')
    ax.set_zlabel('U[V]')
    plt.savefig(''.join([saveinfolder,str_filename,'.png']))
    # only if scan_mode is set to xsnake
    if scan_mode=='xsnake':
      X_data=[]
      Y_data=[]
      Lockin_data=[]
      data_raw_spine=''.join([saveinfolder,str_filename,'_spine.txt'])
      with open(data_raw_spine,'r') as thefile:
	header1=thefile.readline()
	header2=thefile.readline()
	for lines in thefile:
	  columns=lines.split()
	  X_data.extend([ float(columns[0]) ])
	  Y_data.extend([ float(columns[1]) ])
	  Lockin_data.extend([ float(columns[2]) ])

      delta_x=X_data[0]-X_data[-1]
      delta_y=Y_data[0]-Y_data[-1]
      S=(delta_x**2+delta_y**2)**0.5
      print "S factor:", S
      
      with open(data_raw_spine, 'a') as thefile:
	thefile.write("\nY_new [um], Max voltage [V]\n")
	for ydata,Umax in zip(Y_data,Lockin_data):
	  thefile.write('%s\t' %((S/abs(delta_y))*ydata))
	  thefile.write('%s\n' %Umax)
	    
      fig=plt.figure(figsize=(8,6))
      plt.plot((S/abs(delta_y))*np.array(Y_data), np.log(Lockin_data), linewidth=0.5)
      plt.xlabel('Y_new [um]')
      plt.ylabel('Ln(U_max) [V]')
      plt.savefig(''.join([saveinfolder,str_filename,'_spine.png']))
    subprocess.call(['gedit',data_raw])
    plt.show()
    
  elif op_mode=='xscan':
    IT6D_CA_6().xscan()
    data_raw=''.join([saveinfolder,str_filename,'.txt'])
    # plot the data as a contour plot
    X_data=[]
    Lockin_data=[]
    with open(data_raw,'r') as thefile:
      header1=thefile.readline()
      header2=thefile.readline()
      for lines in thefile:
	columns=lines.split()
	X_data.extend([ float(columns[0]) ])
	Lockin_data.extend([ float(columns[1]) ])
    fig=plt.figure(figsize=(8,6))
    plt.plot(np.array(X_data),np.array(Lockin_data))
    plt.xlabel('X[um]')
    plt.ylabel('U[V]')
    plt.savefig(''.join([saveinfolder,str_filename,'.png']))
    subprocess.call(['gedit',data_raw])
    plt.show()
  elif op_mode=='yscan':
    IT6D_CA_6().yscan()
    data_raw=''.join([saveinfolder,str_filename,'.txt'])
    # plot the data as a contour plot
    Y_data=[]
    Lockin_data=[]
    with open(data_raw,'r') as thefile:
      header1=thefile.readline()
      header2=thefile.readline()
      for lines in thefile:
	columns=lines.split()
	Y_data.extend([ float(columns[0]) ])
	Lockin_data.extend([ float(columns[1]) ])
    fig=plt.figure(figsize=(8,6))
    plt.plot(np.array(Y_data),np.array(Lockin_data))
    plt.xlabel('Y[um]')
    plt.ylabel('U[V]')
    plt.savefig(''.join([saveinfolder,str_filename,'.png']))
    subprocess.call(['gedit',data_raw])
    plt.show()
  elif op_mode=='rel':
    IT6D_CA_6().move_rel('x',move_x)
    IT6D_CA_6().move_rel('y',move_y)
  elif op_mode=='abs':
    IT6D_CA_6().move_abs('x',move_x)
    IT6D_CA_6().move_abs('y',move_y)
  elif op_mode=='reset':
    IT6D_CA_6().reset(reset_mode)
  else:
    raise ValueError('Operation mode parameter op_mode has an invalid input!')

if __name__ == "__main__":
  main()

  
  
  
