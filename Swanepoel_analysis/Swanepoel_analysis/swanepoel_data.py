import math
import numpy as np
from numpy.polynomial import polynomial as P
import matplotlib.pyplot as plt
import statistics as stats

def swa_dat():

	lambda_swa = [555, 564, 582, 598, 617, 636, 659, 683, 710, 740, 775, 814, 859]
	Tmax_swa = [0.328,0.433,0.616,0.715,0.805,0.847,0.882,0.896,0.908,0.913,0.916,0.919,0.919]
	Tmin_swa = [0.210,0.256,0.319,0.354,0.378,0.398,0.413,0.426,0.437,0.448,0.460,0.470,0.478] 

	return lambda_swa, Tmin_swa, Tmax_swa


def n_wm():

	common_xaxis, Tmin, Tmax =  swa_dat() #gtt.interp_T('linear')
	######################################################################

	inds=range(len(common_xaxis))
	#Ts=max(Tmax)
	# Eq.11 (p.1216) in Swanepoel (1983)
	s = 1.51 #(1.0/Ts)+math.sqrt(1/Ts**2-1)
	N = [2.0*s*(Tmax[i]-Tmin[i])/(Tmax[i]*Tmin[i])+(s**2+1)/2.0 for i in inds] 
	n_min_max = [math.sqrt(doh+math.sqrt(doh**2-s**2)) for doh in N]
	
	return common_xaxis, n_min_max

def get_md():

	common_xaxis, n_min_max = n_wm()

	run=range(len(n_min_max))
	get_x = [n_min_max[i]/common_xaxis[i] for i in run[::-1]]
	get_y = [ii/2.0 for ii in run]

	coef = P.polyfit(get_x,get_y,1)
	
	return get_x, get_y, coef[0], coef[1]

def get_d():

	min_max, nn = n_wm()
	get_x, get_y, b, a = get_md()
	
	m_1 = round(-b*2.0)/2.0
	m_end = m_1+(len(min_max)-1)/2.0
	m = [.5*x for x in range(int(m_1*2), int(m_end*2+1))]

	run = range(len(min_max))
	m_=m[::-1]

	d_all = [m_[i]*min_max[i]/(2*nn[i]) for i in run[::-1]]
	d_mean = stats.mean(d_all[:-2])

	print 'd_all = ', [round(x) for x in d_all]
	print 'd_mean = ', d_mean

	return round(d_mean) 

def get_new_n():

	min_max, nn = n_wm()
	get_x, get_y, b, a = get_md()
	dm = get_d()
	
	m_1 = round(-b*2.0)/2.0
	m_end = m_1+(len(min_max)-1)/2.0
	m = [.5*x for x in range(int(m_1*2), int(m_end*2+1))]

	run = range(len(min_max))
	min_max_=min_max[::-1]

	nn_ = [m[xx]*min_max_[xx]/(2*dm) for xx in run[::-1]]
	
	print 'm_ = ', m
	print 'lambda = ', min_max_
	print 'n2 = ', nn_
	
	return min_max, nn_

def alpha_v2(d):

	common_xaxis, Tmin, Tmax = swa_dat()
	min_max, nn = get_new_n()
	######################################################################

	inds=range(len(common_xaxis))
	# Eq.15 and Eq.16 (p.1216) in Swanepoel (1983)
	s = 1.51 # (1.0/Ts)+math.sqrt(1/Ts**2-1)
	Ti = [2.0*Tmax[i]*Tmin[i]/(Tmax[i]+Tmin[i]) for i in inds] 
	F = [8*s*nn[i]**2/Ti[i] for i in inds]
	xexp_wm = [(F[i]-math.sqrt(F[i]**2-(nn[i]**2-1)**3*(nn[i]**2-s**4)))/((nn[i]-1)**3*(nn[i]-s**2)) for i in inds]
	######################################################################
	
	#x=math.exp(-alpha*d)
	alpha_wm=[-math.log(doh)/d for doh in xexp_wm]

	return common_xaxis , alpha_wm

def k(wavelen,alpha):

	return wavelen*alpha/(4*math.pi)


if __name__ == "__main__":

	lambda_swa, Tmin_swa, Tmax_swa = swa_dat()	

	plt.figure(1, figsize=(15,10))
	plt.plot(lambda_swa, Tmin_swa, 'ko-', label="Tmin Swanepoel")
	plt.plot(lambda_swa, Tmax_swa, 'ro-', label="Tmax Swanepoel")

	plt.xlabel("$\lambda$, nm", fontsize=20)
	plt.ylabel("Transmission", fontsize=20)
	plt.title("Tmin / Tmax, raw Swanepoel data (1983)")
	plt.tick_params(axis="both", labelsize=20)
	#plt.ylim([2,3])
	#plt.xlim([95,108])
	l=plt.legend(loc=4, fontsize=15)
	l.draw_frame(False)
	plt.savefig("Swanepoel_TminTmax.PDF")
	plt.show()

	######################################################################

	get_x, get_y, b, a  = get_md()
	get_xx = range(8)

	print "a , b = ", a, b
	print "m1 = ", round(-b*2.0)/2.0
	myline = [b+a*x for x in get_xx]

	plt.figure(3, figsize=(15,10))
	plt.plot(1e3*np.array(get_x), get_y, 'ro')
	plt.plot(1e3*np.array(get_xx), myline, 'k-')
	plt.xlabel("$n_1/\lambda$, (10$^{-3}$ nm$^{-1}$)", fontsize=20)
	plt.ylabel("$l/2$", fontsize=20)
	plt.title("Order number m$_1$ and thickness d based on Swanepoel data (1983)")
	plt.text(1, 1, r'd = 979 nm (not used)', fontsize=20)
	plt.text(1, 0, r'm$_1$ = 7.049', fontsize=20)
	plt.tick_params(axis="both", labelsize=20)
	plt.yticks( np.linspace(-8,7,31) )
	plt.ylim([-8,7])
	plt.xlim([0,7])
	#l=plt.legend(loc=4, fontsize=15)
	#l.draw_frame(False)
	plt.savefig("Swanepoel_m_d_graph.PDF")

	######################################################################

	min_max, nn = get_new_n()
	common_xaxis, n_min_max = n_wm()

	plt.figure(4, figsize=(15,10))
	plt.plot(min_max, nn, 'ro-', label = 'n2')
	plt.plot(common_xaxis, n_min_max, 'ko-', label = 'n1')

	plt.xlabel("$\lambda$, nm", fontsize=20)
	plt.ylabel("$n$", fontsize=20)
	plt.title("n2 vs n1 Ref. Index n based on Swanepoel data (1983)")
	plt.tick_params(axis="both", labelsize=20)
	#plt.yticks( np.linspace(2,3,11) )
	l=plt.legend(loc=4, fontsize=15)
	l.draw_frame(False)
	plt.savefig("Swanepoel_new_ref_index.PDF")

	######################################################################

	d=get_d()

	common_xaxis_all , alpha_wm = alpha_v2(d)

	plt.figure(5, figsize=(15,10))
	plt.plot(common_xaxis_all , 1e4*np.array(alpha_wm), 'ko-', label=r"Absorption $\alpha$")

	plt.xlabel("$\lambda$, nm", fontsize=20)
	plt.ylabel(r"$\alpha$, (10$^3$ cm$^{-1}$)", fontsize=20)
	plt.title(r"Absorption $\alpha$ based on Swanepoel data (1983)")
	plt.tick_params(axis="both", labelsize=20)
	#plt.yticks( np.linspace(2,3,11) )
	#plt.ylim([2,3])
	#plt.xlim([95,108])
	l=plt.legend(loc=1, fontsize=20)
	l.draw_frame(False)
	plt.savefig("Swanepoel_alpha.PDF")

	######################################################################

	k_=[k(common_xaxis_all[ii],alpha_wm[ii]) for ii in range(len(common_xaxis_all))]
		
	plt.figure(6, figsize=(15,10))

	plt.plot(common_xaxis , 1e3*np.array(k_), 'ko-', label="k")

	plt.xlabel("$\lambda$, nm", fontsize=20)
	plt.ylabel(r"k, (10$^{-3}$)", fontsize=25)
	plt.title(r"k based on Swanepoel data (1983)")
	plt.tick_params(axis="both", labelsize=20)
	#plt.yticks( np.linspace(2,3,11) )
	#plt.ylim([2,3])
	#plt.xlim([95,108])
	l=plt.legend(loc=4, fontsize=15)
	l.draw_frame(False)
	plt.savefig("Swanepoel_k.PDF")
	plt.show()
    
