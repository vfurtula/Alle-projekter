import sys, os
import datetime, time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D

data_raw=''.join(['data_folder/my_data_20160201-114042','.txt'])
# plot the data as a contour plot
X_data=[]
Y_data=[]
Lockin_data=[]
LI=[]
with open(data_raw,'r') as thefile:
  header1=thefile.readline()
  header2=thefile.readline()
  for lines in thefile:
    columns=lines.split()
    X_data.extend([ float(columns[0]) ])
    Y_data.extend([ float(columns[1]) ])
    Lockin_data.extend([ float(columns[2]) ])
    LI=np.log(Lockin_data)
fig=plt.figure(figsize=(8,6))
ax= fig.add_subplot(111, projection='3d')
#ax=fig.gca(projection='2d')
ax.plot_trisurf(np.array(X_data),np.array(Y_data),np.array(LI),cmap=cm.jet,linewidth=0.2)
ax.set_xlabel('X[um]')
ax.set_ylabel('Y[um]')
ax.set_zlabel('U[V]')
plt.show()
