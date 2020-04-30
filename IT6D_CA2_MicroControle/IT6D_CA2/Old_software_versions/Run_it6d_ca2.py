import sys, os
import datetime, time
import Gpib 
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D


timestr=time.strftime('%Y%m%d-%H%M%S')
v=Gpib.Gpib(0,9)
time.sleep(1.5)
x_speed=380.0 # number of steps per second
y_speed=350.0 # number of steps per second

model_5210=Gpib.Gpib(0,12)
time.sleep(1.5)
# Set the reference source to external input mode
model_5210.write(''.join(['IE 0']))
time.sleep(1)
# Turn off line frequency rejection filter
model_5210.write(''.join(['LF 0']))
time.sleep(1)
# set auto-measure
model_5210.write(''.join(['SEN 14']))
time.sleep(1)


if len(sys.argv)<2:
  raise ValueError('A setup file is required!')
else:
  inFile=sys.argv[1]
  params=__import__(inFile)

op_mode=params.op_mode
ASM_delay=params.asm_delay
if op_mode=='xyscan':
  xstart=params.xstart
  xend=params.xend
  xstep=params.xstep
  ystart=params.ystart
  yend=params.yend
  ystep=params.ystep
  wait_time=params.wait_time
  scan_mode=params.scan_mode
elif op_mode=='xscan':
  xstart=params.xstart
  xend=params.xend
  xstep=params.xstep
  wait_time=params.wait_time
elif op_mode=='yscan':
  ystart=params.ystart
  yend=params.yend
  ystep=params.ystep
  wait_time=params.wait_time
elif op_mode=='reset':
  reset_mode=params.reset_mode
elif op_mode in ['absx','absy','relx','rely']:
  move_axis=params.move_axis
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
    self.abs_posx='it6d_ca2_pos_x.txt'
    self.abs_posy='it6d_ca2_pos_y.txt'
    self.set_delay=0.4
    self.ASM_delay=ASM_delay
    self.XTC_delay=1.5
    self.lockin_delay=self.ASM_delay+4*self.set_delay
        
    if op_mode!='reset':
      if os.path.isfile(self.abs_posx)==False:
	raise ValueError(''.join(['Position file ', self.abs_posx,' does not exist!']))
      
      if os.path.isfile(self.abs_posy)==False:
	raise ValueError(''.join(['Position file ', self.abs_posy,' does not exist!']))
     
    if op_mode=='xyscan':
      if xstart<xend:
	if xstep<=0:
	  raise ValueError('xstep should be positive!')
      elif xstart>xend:
	if xstep>=0:
	  raise ValueError('xstep should be negative!')
      else:
	raise ValueError('xstart and xend should not be equal!')
      
      if ystart<yend:
	if ystep<=0:
	  raise ValueError('ystep should be positive!')
      elif ystart>yend:
	if ystep>=0:
	  raise ValueError('ystep should be negative!')
      else:
	raise ValueError('ystart and yend should not be equal!')
    
    if op_mode=='xscan':
      if xstart<xend:
	if xstep<=0:
	  raise ValueError('xstep should be positive!')
      elif xstart>xend:
	if xstep>=0:
	  raise ValueError('xstep should be negative!')
      else:
	raise ValueError('xstart and xend should not be equal!')
      
    if op_mode=='yscan': 
      if ystart<yend:
	if ystep<=0:
	  raise ValueError('ystep should be positive!')
      elif ystart>yend:
	if ystep>=0:
	  raise ValueError('ystep should be negative!')
      else:
	raise ValueError('ystart and yend should not be equal!')

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
    model_5210.write(''.join(['ASM']))
    time.sleep(self.ASM_delay)
    
    # set the output filter slope to 12dB/ostave
    model_5210.write(''.join(['XDB 1']))
    time.sleep(self.set_delay)
    
    # set time constant to 100 ms, since previous ASM may have changed it 
    model_5210.write(''.join(['XTC 4']))
    time.sleep(self.set_delay)
    
    # get the present sensitivity setting
    model_5210.write(''.join(['SEN']))
    time.sleep(self.set_delay)
    senrangecode=model_5210.read()
    #print 'senrangecode =', senrangecode)
    
    # for the equation see page 6-21 in the manual
    senrange=(1+(2*(int(senrangecode)%2)))*10**(int(senrangecode)/2-7)
    #print 'senrange =', senrange
    
    # reads X channel output
    model_5210.write(''.join(['X']))
    time.sleep(self.set_delay)
    outputuncalib=model_5210.read()
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
  
  def time_left(self):
    # calculate tme left of the total scan
    if op_mode=='xscan':
      with open(self.abs_posx,'r') as thefile:
	pos_x=thefile.read()
      xlen=len(range(xstart,xend+xstep,xstep))
      sweep_runtime_x=xlen*(self.lockin_delay+wait_time)+(xlen-1)*abs(xstep)/x_speed
      return sweep_runtime_x
       
    if op_mode=='yscan':
      with open(self.abs_posy,'r') as thefile:
	pos_y=thefile.read()
      ylen=len(range(ystart,yend+ystep,ystep))
      sweep_runtime_y=ylen*(self.lockin_delay+wait_time)+(ylen-1)*abs(ystep)/y_speed
      return sweep_runtime_y
    
    if op_mode=='xyscan':
      with open(self.abs_posy,'r') as thefile:
	pos_y=thefile.read()
      with open(self.abs_posx,'r') as thefile:
	pos_x=thefile.read()
      xlen=len(range(xstart,xend+xstep,xstep))
      ylen=len(range(ystart,yend+ystep,ystep))
      if scan_mode=='xwise':
	sweep_runtime_x=xlen*ylen*(self.lockin_delay+wait_time)+ylen*(xlen-1)*abs(xstep)/x_speed+(ylen-1)*abs(xstart-xend)/x_speed
	sweep_runtime_y=(ylen-1)*abs(ystep)/y_speed 
	sweep_runtime=sweep_runtime_x+sweep_runtime_y
	return sweep_runtime
      elif scan_mode=='ywise':
	sweep_runtime_y=xlen*ylen*(self.lockin_delay+wait_time)+xlen*(ylen-1)*abs(ystep)/y_speed+(xlen-1)*abs(ystart-yend)/y_speed
	sweep_runtime_x=(xlen-1)*abs(xstep)/x_speed 
	sweep_runtime=sweep_runtime_x+sweep_runtime_y
	return sweep_runtime
      elif scan_mode=='xsnake':
	sweep_runtime_x=xlen*ylen*(self.lockin_delay+wait_time)+ylen*(xlen-1)*abs(xstep)/x_speed
	sweep_runtime_y=(ylen-1)*abs(ystep)/y_speed 
	sweep_runtime=sweep_runtime_x+sweep_runtime_y
	return sweep_runtime
      elif scan_mode=='ysnake':
	sweep_runtime_y=xlen*ylen*(self.lockin_delay+wait_time)+xlen*(ylen-1)*abs(ystep)/y_speed
	sweep_runtime_x=(xlen-1)*abs(xstep)/x_speed 
	sweep_runtime=sweep_runtime_x+sweep_runtime_y
	return sweep_runtime
      else:
	raise ValueError('Invalid scan mode input!')
      
  def time_to_str(self,sec):
    int_sec=int(((sec+0.5)*2)/2)
    return str(datetime.timedelta(seconds=int_sec))
      
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
      v.write('C1O\n')
      v.write('C2O\n')
      with open(self.abs_posx,'w') as thefile:
	thefile.write('%s' %pos)
      with open(self.abs_posy,'w') as thefile:
	thefile.write('%s' %pos)
    else:
      raise ValueError('Reset function accepets only x or y or xy!')
  
  def move_abs(self,axs,pos):
    # x-axis moves approx 380 steps (um) per second
    # y-axis moves approx 350 steps (um) per second
    if axs=='x':
      # open x file
      with open(self.abs_posx,'r') as thefile:
	oldpos=thefile.read()
      #write a time trace for the user
      if op_mode=='absx':
	time_left=abs(int(oldpos)-pos)/x_speed
	print 'X_abs:',pos,', The left:',IT6D_CA_6().time_to_str(time_left)
      # move and wait until movement finished
      if pos>0:
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
      return abs(int(oldpos)-pos)/x_speed
    elif axs=='y':
      # open y file
      with open(self.abs_posy,'r') as thefile:
	oldpos=thefile.read()
      #write a time trace for the user
      if op_mode=='absy':
	time_left=abs(int(oldpos)-pos)/y_speed
	print 'Y_abs:',pos,', The left:',IT6D_CA_6().time_to_str(time_left)
      # move and wait until movement finished
      if pos>0:
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
      return abs(int(oldpos)-pos)/y_speed
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
    # set the microstepper to its initial positions
    IT6D_CA_6().move_abs('x',xstart)
    IT6D_CA_6().move_abs('y',ystart)

    with open(self.data_file, 'w') as thefile:
      thefile.write("X-pos [um], Y-pos [um], Voltage [V]\n") 
    
    try:
      time_tot=IT6D_CA_6().time_left()
      tot_time_x=0
      tot_time_y=0
      count=0
      if scan_mode=='xwise':
	for ii in range(ystart,yend+ystep,ystep):
	  delta_time_y=IT6D_CA_6().move_abs('y',ii)
	  tot_time_y=delta_time_y+tot_time_y
	  for ss in range(xstart,xend+xstep,xstep):
	    delta_time_x=IT6D_CA_6().move_abs('x',ss)
	    tot_time_x=delta_time_x+tot_time_x
	    time_str=IT6D_CA_6().time_to_str(time_tot-tot_time_x-tot_time_y-count*(wait_time+self.lockin_delay))
	    print 'X_abs:',ss,', Y_abs:',ii,', Scan time left:', time_str
	    time.sleep(wait_time)
	    outputcalib=IT6D_CA_6().get_lockin_data()
	    with open(self.data_file, 'a') as thefile:
	      thefile.write('%s\t' %ss)
	      thefile.write('%s\t' %(0.1*ii))
	      thefile.write('%s\n' %outputcalib)
	    count+=1
      elif scan_mode=='ywise':
	for ii in range(xstart,xend+xstep,xstep):
	  delta_time_x=IT6D_CA_6().move_abs('x',ii)
	  tot_time_x=delta_time_x+tot_time_x
	  for ss in range(ystart,yend+ystep,ystep):
	    delta_time_y=IT6D_CA_6().move_abs('y',ss)
	    tot_time_y=delta_time_y+tot_time_y
	    time_str=IT6D_CA_6().time_to_str(time_tot-tot_time_x-tot_time_y-count*(wait_time+self.lockin_delay))
	    print 'X_abs:',ii,', Y_abs:',ss,', Scan time left:',time_str
	    time.sleep(wait_time)
	    outputcalib=IT6D_CA_6().get_lockin_data()
	    with open(self.data_file, 'a') as thefile:
	      thefile.write('%s\t' %ii)
	      thefile.write('%s\t' %(0.1*ss))
	      thefile.write('%s\n' %outputcalib)
	    count+=1
      elif scan_mode=='xsnake':
	turn=-1
	for ii in range(ystart,yend+ystep,ystep):
	  delta_time_y=IT6D_CA_6().move_abs('y',ii)
	  tot_time_y=delta_time_y+tot_time_y
	  turn=turn*-1
	  for ss in range(xstart,xend+xstep,xstep)[::turn]:
	    delta_time_x=IT6D_CA_6().move_abs('x',ss)
	    tot_time_x=delta_time_x+tot_time_x
	    time_str=IT6D_CA_6().time_to_str(time_tot-tot_time_x-tot_time_y-count*(wait_time+self.lockin_delay))
	    print 'X_abs:',ss,', Y_abs:',ii,', Scan time left:',time_str
	    time.sleep(wait_time)
	    outputcalib=IT6D_CA_6().get_lockin_data()
	    with open(self.data_file, 'a') as thefile:
	      thefile.write('%s\t' %ss)
	      thefile.write('%s\t' %(0.1*ii))
	      thefile.write('%s\n' %outputcalib)
	    count+=1
      elif scan_mode=='ysnake':
	turn=-1
	for ii in range(xstart,xend+xstep,xstep):
	  delta_time_x=IT6D_CA_6().move_abs('x',ii)
	  tot_time_x=delta_time_x+tot_time_x
	  turn=turn*-1
	  for ss in range(ystart,yend+ystep,ystep)[::turn]:
	    delta_time_y=IT6D_CA_6().move_abs('y',ss)
	    tot_time_y=delta_time_y+tot_time_y
	    time_str=IT6D_CA_6().time_to_str(time_tot-tot_time_x-tot_time_y-count*(wait_time+self.lockin_delay))
	    print 'X_abs:',ii,', Y_abs:',ss,', Scan time left:',time_str
	    time.sleep(wait_time)
	    outputcalib=IT6D_CA_6().get_lockin_data()
	    with open(self.data_file, 'a') as thefile:
	      thefile.write('%s\t' %ii)
	      thefile.write('%s\t' %(0.1*ss))
	      thefile.write('%s\n' %outputcalib)
	    count+=1
      else:
	raise ValueError('Valid scan_mode input: xwise, ywise, xsnake, ysnake!')
    except KeyboardInterrupt:
      print('exiting...')
    
  def xscan(self):
    # set the microstepper to its initial positions
    IT6D_CA_6().move_abs('x',xstart)

    with open(self.data_file, 'w') as thefile:
      thefile.write("X-pos [um], Voltage [V]\n")
    try:  
      time_tot=IT6D_CA_6().time_left()
      tot_time_x=0
      count=0
      for ii in range(xstart,xend+xstep,xstep):
	delta_time_x=IT6D_CA_6().move_abs('x',ii)
	tot_time_x=delta_time_x+tot_time_x
	time_str=IT6D_CA_6().time_to_str(time_tot-tot_time_x-count*(wait_time+self.lockin_delay))
	print 'X_abs:',ii,', Scan time left:',time_str
	time.sleep(wait_time)
	outputcalib=IT6D_CA_6().get_lockin_data()
	with open(self.data_file, 'a') as thefile:
	  thefile.write('%s\t' %ii)
	  thefile.write('%s\n' %outputcalib)
	count+=1
    except KeyboardInterrupt:
      print('exiting...')
	
  def yscan(self):
    # set the microstepper to its initial positions
    IT6D_CA_6().move_abs('y',ystart)

    with open(self.data_file, 'w') as thefile:
      thefile.write("Y-pos [um], Voltage [V]\n")
    
    try:
      time_tot=IT6D_CA_6().time_left()
      tot_time_y=0
      count=0
      for ss in range(ystart,yend+ystep,ystep):
	delta_time_y=IT6D_CA_6().move_abs('y',ss)
	tot_time_y=delta_time_y+tot_time_y
	time_str=IT6D_CA_6().time_to_str(time_tot-tot_time_y-count*(wait_time+self.lockin_delay))
	print 'Y_abs:',ss,', Scan time left:',time_str
	time.sleep(wait_time)
	outputcalib=IT6D_CA_6().get_lockin_data()
	with open(self.data_file, 'a') as thefile:
	  thefile.write('%s\t' %(0.1*ss))
	  thefile.write('%s\n' %outputcalib)
	count+=1
    except KeyboardInterrupt:
      print('exiting...')

if __name__ == "__main__":

  if op_mode=='xyscan':
    IT6D_CA_6().xyscan()
    data_raw=''.join([saveinfolder,str_filename,'.txt'])
    # plot the data as a contour plot
    X_data=[]
    Y_data=[]
    Lockin_data=[]
    with open(data_raw,'r') as thefile:
      header1=thefile.readline()
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
    plt.show()
  elif op_mode=='xscan':
    IT6D_CA_6().xscan()
    data_raw=''.join([saveinfolder,str_filename,'.txt'])
    # plot the data as a contour plot
    X_data=[]
    Lockin_data=[]
    with open(data_raw,'r') as thefile:
      header1=thefile.readline()
      for lines in thefile:
	columns=lines.split()
	X_data.extend([ float(columns[0]) ])
	Lockin_data.extend([ float(columns[1]) ])
    fig=plt.figure(figsize=(8,6))
    plt.plot(np.array(X_data),np.array(Lockin_data))
    plt.xlabel('X[um]')
    plt.ylabel('U[V]')
    plt.savefig(''.join([saveinfolder,str_filename,'.png']))
    plt.show()
  elif op_mode=='yscan':
    IT6D_CA_6().yscan()
    data_raw=''.join([saveinfolder,str_filename,'.txt'])
    # plot the data as a contour plot
    Y_data=[]
    Lockin_data=[]
    with open(data_raw,'r') as thefile:
      header1=thefile.readline()
      for lines in thefile:
	columns=lines.split()
	Y_data.extend([ float(columns[0]) ])
	Lockin_data.extend([ float(columns[1]) ])
    fig=plt.figure(figsize=(8,6))
    plt.plot(np.array(Y_data),np.array(Lockin_data))
    plt.xlabel('Y[um]')
    plt.ylabel('U[V]')
    plt.savefig(''.join([saveinfolder,str_filename,'.png']))
    plt.show()
  elif op_mode=='relx':
    IT6D_CA_6().move_rel('x',move_axis)
  elif op_mode=='rely':
    IT6D_CA_6().move_rel('y',move_axis)
  elif op_mode=='absx':
    IT6D_CA_6().move_abs('x',move_axis)
  elif op_mode=='absy':
    IT6D_CA_6().move_abs('y',move_axis)
  elif op_mode=='reset':
    IT6D_CA_6().reset(reset_mode)
  else:
    raise ValueError('Operation mode parameter op_mode has an invalid input!')
  
  
