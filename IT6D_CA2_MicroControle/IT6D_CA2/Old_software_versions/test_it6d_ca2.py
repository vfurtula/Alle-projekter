import sys, time 
import Gpib 

v=Gpib.Gpib(0,9)
my_file='data.txt'

class IT6D_CA_6:
  def __init__(self):
    #constants
    self.data_file=my_file
    self.abs_posx='it6d_ca2_pos_x.txt'
    self.abs_posy='it6d_ca2_pos_y.txt'

  def move_abs(self,axs,pos):
    if axs=='x':
      if pos>0:
        v.write(''.join(['I1=+',str(pos),'!',chr(10)]))
      else:
        v.write(''.join(['I1=',str(pos),'!',chr(10)]))
      with open('it6d_ca2_pos_x.txt','w') as thefile:
        thefile.write('%s' %pos) 
    elif axs=='y':
      if pos>0:
        v.write(''.join(['I2=+',str(pos),'!',chr(10)]))
      else:
        v.write(''.join(['I2=',str(pos),'!',chr(10)]))
      with open('it6d_ca2_pos_y.txt','w') as thefile:
        thefile.write('%s' %pos)
    else:
      raise ValueError('Specify axis and absolute position!')

  def move_rel(self,axs,pos):
    if axs=='x':
      # open x file
      with open('it6d_ca2_pos_x.txt','r') as thefile:
        abspos=thefile.read()
      # calculate a step and send move command
      newpos=int(abspos)+pos
      if newpos>0:
        v.write(''.join(['I1=+',str(newpos),'!',chr(10)]))
      else:
        v.write(''.join(['I1=',str(newpos),'!',chr(10)]))
      # save x file
      with open('it6d_ca2_pos_x.txt','w') as thefile:
        thefile.write('%s' %newpos) 
    elif axs=='y':
      # open y file
      with open('it6d_ca2_pos_y.txt','r') as thefile:
        abspos=thefile.read()
      # calculate a step and send move command
      newpos=int(abspos)+pos
      if newpos>0:
        v.write(''.join(['I2=+',str(newpos),'!',chr(10)]))
      else:
        v.write(''.join(['I2=',str(newpos),'!',chr(10)]))
      # save y file
      with open('it6d_ca2_pos_y.txt','w') as thefile:
        thefile.write('%s' %newpos)
    else:
      raise ValueError('Specify axis and relative position!')

  def scan(self,xstart,xend,ystart,yend,xstep,ystep,wait_time,scan_mode):
    # x-axis moves approx 400 steps (um) per second
    # y-axis moves approx 350 steps (um) per second
    with open('it6d_ca2_pos_x.txt','r') as thefile:
      abspos=thefile.read()
    wait_x=abs(int(abspos)-xstart)/400+1
    with open('it6d_ca2_pos_y.txt','r') as thefile:
      abspos=thefile.read()
    wait_y=abs(int(abspos)-ystart)/350+1

    IT6D_CA_6().move_abs('x',xstart)
    IT6D_CA_6().move_abs('y',ystart)

    if wait_x>wait_y:
      time.sleep(wait_x)
    else:
      time.sleep(wait_y)

    with open(self.data_file, 'w') as thefile:
      thefile.write("X pos [um], Y-pos [um]\n")

    if scan_mode=='ywise':
      for ii in range(xstart,xend+xstep,xstep):
	IT6D_CA_6().move_abs('x',ii)
	tal1=0
	for ss in range(ystart,yend+ystep,ystep):
	  IT6D_CA_6().move_abs('y',ss)
	  if tal1==0:
	    time.sleep(abs(ystart-yend)/350+1)
	  with open(self.data_file, 'a') as thefile:
	    thefile.write('%s ' %ii)
	    thefile.write('%s\n' %ss)
	    print 'X:',ii,', Y:',ss
	  time.sleep(wait_time)
	  tal1=1
    elif scan_mode=='xwise':
      for ii in range(ystart,yend+ystep,ystep):
	IT6D_CA_6().move_abs('y',ii)
	tal1=0
	for ss in range(xstart,xend+xstep,xstep):
	  IT6D_CA_6().move_abs('x',ss)
	  if tal1==0:
	    time.sleep(abs(xstart-xend)/400+1)
	  with open(self.data_file, 'a') as thefile:
	    thefile.write('%s ' %ss)
	    thefile.write('%s\n' %ii)
	    print 'X:',ss,', Y:',ii
	  time.sleep(wait_time)
	  tal1=1
    else:
      raise ValueError('Scan mode is either xwise or ywise!')
if __name__ == "__main__":

  #IT6D_CA_6().move_rel('x',-5000)
  #IT6D_CA_6().move_rel('y',18000)

  IT6D_CA_6().scan(1000,5000,5000,1000,100,-50,3,'xwise')
      

'''
#create arguments
if sys.argv[1]=='--absx':
  move=sys.argv[2]
  check=0
  if move[0]=='+':
    check=1
  if move[0]=='-':
    check=1
  if check==0:
    raise ValueError("The position is required to have + or - in the front")
  v.write(''.join(['I1=',move,'!']))
  v.write(chr(10)) #line feed (LF)
  with open('it6d_ca2_pos_x.txt','w') as thefile:
    thefile.write(move)

elif sys.argv[1]=='--relx':
  move=sys.argv[2]
  check=0
  if move[0]=='+':
    check=1
  if move[0]=='-':
    check=1
  if check==0:
    raise ValueError("The position is required to have + or - in the front")
  with open('it6d_ca2_pos_x.txt','r') as thefile:
    abspos=thefile.read()
  newpos=int(abspos)+int(move)
  if newpos>0:
    newpos_string=''.join(['+',str(newpos)])
  else:
    newpos_string=str(newpos)
  v.write(''.join(['I1=',newpos_string,'!']))
  v.write(chr(10)) #line feed (LF)
  with open('it6d_ca2_pos_x.txt','w') as thefile:
    thefile.write(newpos_string)

elif sys.argv[1]=='--absy':
  move=sys.argv[2]
  check=0
  if move[0]=='+':
    check=1
  if move[0]=='-':
    check=1
  if check==0:
    raise ValueError("The position is required to have + or - in the front")
  v.write(''.join(['I2=',move,'!']))
  v.write(chr(10)) #line feed (LF)
  with open('it6d_ca2_pos_y.txt','w') as thefile:
    thefile.write(move)

elif sys.argv[1]=='--rely':
  move=sys.argv[2]
  check=0
  if move[0]=='+':
    check=1
  if move[0]=='-':
    check=1
  if check==0:
    raise ValueError("The position is required to have + or - in the front")
  with open('it6d_ca2_pos_y.txt','r') as thefile:
    abspos=thefile.read()
  newpos=int(abspos)+int(move)
  if newpos>0:
    newpos_string=''.join(['+',str(newpos)])
  else:
    newpos_string=str(newpos)
  v.write(''.join(['I2=',newpos_string,'!']))
  v.write(chr(10)) #line feed (LF)
  with open('it6d_ca2_pos_y.txt','w') as thefile:
    thefile.write(newpos_string)

else:
 raise ValueError('Second argument is one of the following --absx or --relx or --absy or --rely')
'''


'''
v.write('I1?')
time.sleep(5)

try:
  while (True):
    v.write(":READ?")
    print v.read()
    time.sleep(0.1)

except KeyboardInterrupt:
  print 'exiting'  

'''
