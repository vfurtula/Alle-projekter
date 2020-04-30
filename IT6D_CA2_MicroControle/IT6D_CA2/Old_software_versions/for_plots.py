import sys, os
import datetime, time
import numpy
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from numpy.polynomial import polynomial as P

## For Matplotlib fonts
from matplotlib import rc
## for LaTeX style use:
rc("text", usetex=True)
rc("font", family="serif")

folder_and_file='EK076-2/1060nm EK076-220160206-180216'
data_raw=''.join([folder_and_file,'.txt'])
# plot the data as a contour plot
X_data=[]
Y_data=[]
Lockin_data=[]
with open(data_raw,'r') as thefile:
  headers=[thefile.readline() for i in range(2)]
  for lines in thefile:
    columns=lines.split()
    X_data.extend([ float(columns[0])/1000 ])
    Y_data.extend([ float(columns[1])/1000 ])
    Lockin_data.extend([ 1000*float(columns[2]) ])
fig=plt.figure(figsize=(8,6))
ax= fig.add_subplot(111, projection='3d')
#ax=fig.gca(projection='2d')
ax.plot_trisurf(numpy.array(X_data),numpy.array(Y_data),numpy.array(Lockin_data),cmap=cm.jet,linewidth=0.2)
ax.xaxis.set_ticks([-2,-1,0,1,2])
#ax.yaxis.set_ticks([1,0,-2,-4,-6])
ax.set_xlabel('X[mm]')
ax.set_ylabel('Y[mm]')
ax.set_zlabel('U[mV]')
ax.view_init(elev=33, azim=-40)


data_Spath_spine=''.join([folder_and_file,'_LSFspine.txt'])
with open(data_Spath_spine, 'w') as thefile:
	thefile.write("Including points, slope a_lsf [mV/mm], intercept b_lsf [mm], LSF residual sum \n")
	thefile.write("0,1,2\t At least four points required for a valid LSF! \n")
	
def nearest_point(a,b,c,x1,y1):
	# distance between line ax+by+c=0 and point (x1,y1)
	x=(b*(b*x1-a*y1)-a*c)/(a**2+b**2)
	y=(a*(-b*x1+a*y1)-b*c)/(a**2+b**2)
	
	return x,y	

x_array=numpy.arange(-2000,2000+200,200)
y_array=numpy.arange(100,-6000-100,-100)
save_x=[]
save_y=[]
save_Umax=[]
turn=-1
taeller=0
for j,tal in zip(y_array,range(len(y_array))):
	turn=turn*-1
	voltages=[]
	pos_x=[]
	for i in x_array[::turn]:
		pos_x.extend([ i ])
		voltages.extend([ Lockin_data[taeller] ])
		taeller+=1
		
	ind_max=numpy.argmax(voltages)
	save_x.extend([ pos_x[ind_max] ])
	save_y.extend([ j ])
	save_Umax.extend([ voltages[ind_max] ])
	xp_acc=[]
	yp_acc=[]
	a2=[]
	c2=[]
	resid=[]
	if tal>2:
		coef = P.polyfit(save_x,save_y,1)
		a=-coef[1]
		b=1
		c=-coef[0]
		for i,j in zip(save_x,save_y):
			xp,yp = nearest_point(a,b,c,i,j)
			xp_acc.extend([ xp ])
			yp_acc.extend([ yp ])

		delta_xy=(numpy.diff(xp_acc)**2+numpy.diff(yp_acc)**2)**0.5
		S=numpy.append([[0]],[numpy.add.accumulate(delta_xy)])
		
		coef2 , stats = P.polyfit(S/1000,numpy.log(save_Umax),1,full=True)
		a2.extend([ coef2[1] ])
		c2.extend([ coef2[0] ])
		resid.extend([ stats[0][0] ])
		Umax_lsf = [numpy.poly1d(coef2[::-1])(i) for i in S/1000] 
		with open(data_Spath_spine, 'a') as thefile:
			thefile.write('%s\t' %tal)
			thefile.write('%s\t' %a2[-1])
			thefile.write('%s\t' %c2[-1])
			thefile.write('%s\n' %resid[-1])

curve_ = [numpy.poly1d(coef2[::-1])(i) for i in S/1000]

fig=plt.figure(figsize=(10,7))
plt.plot(S/1000, numpy.log(save_Umax),'-o',linewidth=1, label='Raw data')
plt.plot(S/1000 , curve_, 'k-',linewidth=1, label='Least squares fit')
plt.xlabel('S [mm]', fontsize=20)
plt.ylabel('Log(Umax) [mV]', fontsize=20)
plt.tick_params(axis="both", labelsize=20)
l=plt.legend(loc=9, fontsize=20)
l.draw_frame(False)
#plt.ylim([-1,2])
#plt.xlim([0,5])
plt.savefig(''.join([folder_and_file,'_spine.png']))

fig=plt.figure(figsize=(10,7))
plt.plot(S/1000, save_Umax,'-o',linewidth=1, label='Raw data')
plt.xlabel('S [mm]', fontsize=20)
plt.ylabel('Log(Umax) [mV]', fontsize=20)
plt.tick_params(axis="both", labelsize=20)
l=plt.legend(loc=9, fontsize=20)
l.draw_frame(False)
#plt.ylim([-1,2])
#plt.xlim([0,5])


#curve_ = [numpy.poly1d(coef[::-1])(i) for i in self.get_x]

fig=plt.figure(figsize=(10,7))
plt.plot(save_x, save_y, 'o') 
plt.xlabel('X [um]', fontsize=20)
plt.ylabel('Y [um]', fontsize=20)
plt.tick_params(axis="both", labelsize=20)
#plt.savefig(''.join([folder_and_file,'_spine.png']))

plt.show()
