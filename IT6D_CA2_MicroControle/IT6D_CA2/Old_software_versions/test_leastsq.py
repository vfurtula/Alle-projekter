
import numpy
import scipy.optimize as scop
import numpy.polynomial.polynomial as poly


def nearest_point(a,b,c,x1,y1):
	# Nearest point on line ax+by+c=0 to the point (x1,y1)
	x=(b*(b*x1-a*y1)-a*c)/(a**2+b**2)
	y=(a*(-b*x1+a*y1)-b*c)/(a**2+b**2)	
	return x,y


def dist_to_line(y0,x1,y1):
	# Shortest distance between line ax+by+c=0 and point (x1,y1)
	a,b,c = y0
	d=(a*x1+b*y1+c)**2/(a**2+b**2)
	return sum(d)


#save_y=numpy.zeros(20)
save_y=range(20)
save_x=range(len(save_y))


y0=[1,1,1]
y_new = scop.fmin(dist_to_line,y0,args=(numpy.array(save_x),numpy.array(save_y)),xtol=1e-15)

a,b,c = y_new

print "a,b,c =", a,b,c
'''
coef = poly.polyfit(save_x,save_y,1)
a=-coef[1]
b=1
c=-coef[0]
'''

xp_acc,yp_acc = nearest_point(a,b,c,numpy.array(save_x),numpy.array(save_y))

delta_xy=(numpy.diff(xp_acc)**2+numpy.diff(yp_acc)**2)**0.5
S=numpy.append([0],numpy.add.accumulate(delta_xy))

print "S:",S