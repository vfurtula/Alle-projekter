# -*- coding: utf-8 -*-
"""
Created on Sun May 24 01:49:03 2015

@author: christian
"""

import numpy as np
import matplotlib.pyplot as plt
#import plotTools

import MuellerTools as mt
import BerremanLib as berrlib
import MuellerImportExport as mie
#import materialLib as matLib
#from lmfit import minimize, Parameters, Parameter, report_fit

import coreShellCylinder as coreshell
import calculationOfScattering as cs

import propertiesMM as propMM
# comment, wL_n, e1, e2 = mie.iMatCE('materialFiles/SiO2_JAW.MAT')
#plotMuellerReflCoreShell(1240/210,1240/1690,100,(1/4)*10**-9,50,200,4*10**3)
def plotMuellerReflCoreShell(wL_max,wL_min,N2,Nfactor,rcore,rshell,d):
	d=-d
	#wL_max=4.1
	#wL_min=1
	#N2=50
	wL=np.linspace(wL_min, wL_max,(wL_max-wL_min)/0.01+1)
	comment, wL, ec1, ec2 = mie.iMatCE('materialFiles/CE_MAT/Semiconductor/GaAs.mat',wL) #core
	comment, wL, es1, es2 = mie.iMatCE('materialFiles/CE_MAT/Semiconductor/Al3GaAs.mat',wL) #shell
	comment_s, wL_s, e1_s, e2_s = mie.iMatCE('materialFiles/Si_JAW.mat',wL)#Si_JAW
	wL=np.sort(wL)
	wL=1240/wL
	N=np.size(wL)
	#k=2*np.pi*1240/wL
	#Nfactor=(1/5)*10**-9
	thetai=np.linspace(25*np.pi/180,75*np.pi/180,N2) #incident angle
	#thetai=np.pi/4

	wL,thetai=np.meshgrid(wL,thetai)
	nn1,kk1=cs.eps2nk(ec1,ec2)
	nn2,kk2=cs.eps2nk(es1,es2)
	ncore=nn1+1j*kk1
	nshell=nn2+1j*kk2   
	nm=1
	#rshell=0.01
	#rcore=200

	S,Q,k=coreshell.coeffCoreShell(rcore,rshell,ncore,nshell,nm,thetai,wL)

	neffs,keffs=cs.refEff(Nfactor,k,S[0,0]) #s-polarisation
	neffp,keffp=cs.refEff(Nfactor,k,S[1,1]) #p-polarisation

	eps1s,eps2s=cs.nk2eps(neffs,keffs)
	eps1p,eps2p=cs.nk2eps(neffp,keffp)

	n_s=np.sqrt(e1_s-e2_s*1j)

	eps=np.zeros((3,3,N2,N),dtype=complex)
	eps[0,0,:,:]=eps1s-eps2s*1j
	eps[1,1,:,:]=eps1s-eps2s*1j
	eps[2,2,:,:]=eps1p-eps2p*1j
	angles=(0*np.pi/180,0*np.pi/180,0*np.pi/180)
	print eps[:,:,3,40]
	eps=berrlib.rotateTensor(eps,0*np.pi/180,0*np.pi/180,0*np.pi/180)
	#eps=berrlib.rotateTensor(eps,(90-thetai)*np.pi/180,(90-thetai)*np.pi/180,(90-thetai)*np.pi/180)
	#print eps[:,:,40]


	n_a=1.*np.ones((N,1),dtype=float)     # ambient refractive index
	#d=-5000                              # Film thickness

	#theta1=45.*np.pi/180. # incidence angle
	n_a=np.squeeze(n_a)
	costheta2=np.sqrt(1-np.square(np.divide(np.multiply(np.real(n_a),np.sin(thetai)),(n_s))))
	kx=n_a*np.sin(thetai)

	#wL=wL*1240
	#k0=wL*1.602176462E-19*1.E-9/(299792458.*1.054571596E-34) # wave vector in nm
	#wL=1240/wL
	k0=2*np.pi/wL

	T=np.zeros((4,4,N2,N),dtype=complex)
	J=np.zeros((2,2,N2,N),dtype=complex)
	M=np.zeros((4,4,N2,N),dtype=float)

	for i in range(N2):#thetai
		for j in range(N):#wavelength
			T[:,:,i,j]=berrlib.La_inv(n_a.item(j),thetai.item(i))*berrlib.Tp(berrlib.Delta(kx.item(i,j),eps[:,:,i,j]),k0.item(j),d,eps[:,:,i,j])*berrlib.Lf(n_s.item(j),costheta2.item(i,j))
			#T[:,:,i,j]=berrlib.La_inv(n_a.item(i),thetai.item(j))*berrlib.Tp(berrlib.Delta(kx.item(i),eps[:,:,i,j]),k0.item(i),d,eps[:,:,i,j])*berrlib.Lf(n_s.item(i),costheta2.item(i))
			#T[:,:,i,j]=berrlib.La_inv(n_a[i],thetai[j])*berrlib.Tp(berrlib.Delta(kx[i],eps[:,:,i,j]),k0[i],d,eps[:,:,i,j])*berrlib.Lf(n_s[i],costheta2[i])            
			J[:,:,i,j]=berrlib.GlobalTransfer2Jones(T[:,:,i,j])        
			M[:,:,i,j]=mt.normalize(mt.Jones2Mueller(J[:,:,i,j]))

	thetai=thetai*180/np.pi    

	#Plot of th mueller matrix
	#plt.figure()
	"""idx=1
	fig,axarr=plt.subplots(4,4)
	cax=np.zeros([4,4])
	for i in range(4):
			for j in range(4):
					if idx==1:
							cax=axarr[0,0].pcolormesh(wL,thetai,M[0,0],vmin=-1,vmax=1)
							fig.colorbar(cax,ax=axarr[0,0],ticks=[-1,0,1])
							axarr[0,0].set_title('M11')
					else:
							cax=axarr[i,j].pcolormesh(wL,thetai, M[i,j]/M[0,0],vmin=-1,vmax=1)
							axarr[i,j].set_title('M' +str(i+1)+str(j+1))#normalized values
							fig.colorbar(cax,ax=axarr[i,j],ticks=[-1,0,1])
							#fig.colorbar(cax,ax=axarr[i,j],ticks=[(M[i,j]/M[0,0]).min(),0.5*((M[i,j]/M[0,0]).min()+(M[i,j]/M[0,0]).max()),(M[i,j]/M[0,0]).max()])
					axarr[i,j].axis([210,1690,25,75])
					axarr[i,j].set_yticks([25,50,75])
					axarr[i,j].set_xticks([210,1000,1690])
					plt.setp([a.get_xticklabels() for a in axarr[0,:]], visible=False)
					plt.setp([a.get_xticklabels() for a in axarr[1,:]], visible=False)
					plt.setp([a.get_xticklabels() for a in axarr[2,:]], visible=False)
					plt.setp([a.get_yticklabels() for a in axarr[:,1]], visible=False)
					plt.setp([a.get_yticklabels() for a in axarr[:,2]], visible=False)
					plt.setp([a.get_yticklabels() for a in axarr[:,3]], visible=False)
					
					idx=idx+1
	axarr[0,0].set_ylabel(r'$\theta_i [\degree]$')
	#axarr[0,0].set_ylabel("Inc Ang [deg]")
	axarr[1,0].set_ylabel(r'$\theta_i [\degree]$')
	axarr[2,0].set_ylabel(r'$\theta_i [\degree]$')
	axarr[3,0].set_ylabel(r'$\theta_i [\degree]$')
	axarr[3,0].set_xlabel(r'$\lambda [nm]$')
	axarr[3,1].set_xlabel(r'$\lambda [nm]$') 
	axarr[3,2].set_xlabel(r'$\lambda [nm]$') 
	axarr[3,3].set_xlabel(r'$\lambda [nm]$')
	plt.show()

	idx=1
	fig,axarr=plt.subplots(4,4)
	cax=np.zeros([4,4])
	for i in range(4):
			for j in range(4):
					if idx==1:
							cax=axarr[0,0].pcolormesh(thetai,wL,M[0,0],vmin=-1,vmax=1)
							fig.colorbar(cax,ax=axarr[0,0],ticks=[-1,0,1])
							axarr[0,0].set_title('M11')
					else:
							cax=axarr[i,j].pcolormesh(thetai,wL, M[i,j]/M[0,0],vmin=-1,vmax=1)
							axarr[i,j].set_title('M' +str(i+1)+str(j+1))#normalized values
							fig.colorbar(cax,ax=axarr[i,j],ticks=[-1,0,1])
							#fig.colorbar(cax,ax=axarr[i,j],ticks=[(M[i,j]/M[0,0]).min(),0.5*((M[i,j]/M[0,0]).min()+(M[i,j]/M[0,0]).max()),(M[i,j]/M[0,0]).max()])
					axarr[i,j].axis([25,75,210,1690])
					axarr[i,j].set_xticks([25,50,75])
					axarr[i,j].set_yticks([210,1000,1690])
					plt.setp([a.get_xticklabels() for a in axarr[0,:]], visible=False)
					plt.setp([a.get_xticklabels() for a in axarr[1,:]], visible=False)
					plt.setp([a.get_xticklabels() for a in axarr[2,:]], visible=False)
					plt.setp([a.get_yticklabels() for a in axarr[:,1]], visible=False)
					plt.setp([a.get_yticklabels() for a in axarr[:,2]], visible=False)
					plt.setp([a.get_yticklabels() for a in axarr[:,3]], visible=False)
					
					idx=idx+1
	axarr[3,0].set_xlabel(r'$\theta_i [\degree]$')
	axarr[3,1].set_xlabel(r'$\theta_i [\degree]$')
	axarr[3,2].set_xlabel(r'$\theta_i [\degree]$')
	axarr[3,3].set_xlabel(r'$\theta_i [\degree]$')
	axarr[0,0].set_ylabel(r'$\lambda [nm]$')
	axarr[1,0].set_ylabel(r'$\lambda [nm]$') 
	axarr[2,0].set_ylabel(r'$\lambda [nm]$') 
	axarr[3,0].set_ylabel(r'$\lambda [nm]$')
	plt.show()"""

	#Make 1D plot of incident angles at 45 degrees
	deg=40
	print deg
	idx=1
	fig,axarr=plt.subplots(4,4)
	for i in range(4):
		for j in range(4):
			if idx==1:
				axarr[0,0].plot((M[0,0])[deg,:])
				#axarr[0,0].set_title('M11')
				axarr[0,0].set_visible(False)
			else:
				axarr[i,j].plot(M[i,j][deg,:])
				axarr[i,j].set_title(r'$M_{%s}$' %(str(i+1)+str(j+1)),fontsize=14)#normalized values
			#axarr[i,j].set_xticks([210,950,1690])
			axarr[i,j].axis([0,N,-1.1,1.1])
			axarr[i,j].set_yticks([-1,0,1])
			plt.setp(axarr[i,j], xticks=[0, (N-1)/2, (N-1)], xticklabels=[210,950,1690])
			plt.setp([a.get_xticklabels() for a in axarr[0,:]], visible=False)
			plt.setp([a.get_xticklabels() for a in axarr[1,:]], visible=False)
			plt.setp([a.get_xticklabels() for a in axarr[2,:]], visible=False)
			plt.setp([a.get_yticklabels() for a in axarr[1:4,1]], visible=False)
			plt.setp([a.get_yticklabels() for a in axarr[:,2]], visible=False)
			plt.setp([a.get_yticklabels() for a in axarr[:,3]], visible=False)

			idx=idx+1
	axarr[3,0].set_xlabel(r'$\lambda [nm]$',fontsize=14)
	axarr[3,1].set_xlabel(r'$\lambda [nm]$',fontsize=14) 
	axarr[3,2].set_xlabel(r'$\lambda [nm]$',fontsize=14) 
	axarr[3,3].set_xlabel(r'$\lambda [nm]$',fontsize=14)
	plt.show()

	#Make 1D plot of incident angles at 65 degrees
	#a=0.0    
	#a=(75-25)/N2
	#print a
	#deg=(65-25)/a  
	deg=80
	print deg
	idx=1
	fig,axarr=plt.subplots(4,4)
	for i in range(4):
		for j in range(4):
			if idx==1:
				axarr[0,0].plot((M[0,0])[deg,:])
				#axarr[0,0].set_title('M11')
				axarr[0,0].set_visible(False)
			else:
				axarr[i,j].plot((M[i,j])[deg,:])
				axarr[i,j].set_title(r'$M_{%s}$' %(str(i+1)+str(j+1)),fontsize=14)#normalized values
			#axarr[i,j].set_xticks([210,950,1690])
			axarr[i,j].axis([0,N,-1.1,1.1])
			axarr[i,j].set_yticks([-1,0,1])
			plt.setp(axarr[i,j], xticks=[0, (N-1)/2, (N-1)], xticklabels=[210,950,1690])
			plt.setp([a.get_xticklabels() for a in axarr[0,:]], visible=False)
			plt.setp([a.get_xticklabels() for a in axarr[1,:]], visible=False)
			plt.setp([a.get_xticklabels() for a in axarr[2,:]], visible=False)
			plt.setp([a.get_yticklabels() for a in axarr[1:4,1]], visible=False)
			plt.setp([a.get_yticklabels() for a in axarr[:,2]], visible=False)
			plt.setp([a.get_yticklabels() for a in axarr[:,3]], visible=False)

			idx=idx+1
	axarr[3,0].set_xlabel(r'$\lambda [nm]$',fontsize=14)
	axarr[3,1].set_xlabel(r'$\lambda [nm]$',fontsize=14) 
	axarr[3,2].set_xlabel(r'$\lambda [nm]$',fontsize=14) 
	axarr[3,3].set_xlabel(r'$\lambda [nm]$',fontsize=14)
	plt.show()

	idx=1
	fig,axarr=plt.subplots(4,4)
	cax=np.zeros([4,4])
	for i in range(4):
		for j in range(4):
			if idx==1:
				cax=axarr[0,0].pcolormesh(thetai,wL,M[0,0],vmin=-1,vmax=1)
				#fig.colorbar(cax,ax=axarr[0,0],ticks=[M[0,0].min(),0.5*(M[0,0].min()+M[0,0].max()),M[0,0].max()])
				#axarr[0,0].set_title('M11')
				axarr[0,0].set_visible(False) 
			else:
				cax=axarr[i,j].pcolormesh(thetai,wL,M[i,j],vmin=-1,vmax=1)
				axarr[i,j].set_title(r'$M_{%s}$' %(str(i+1)+str(j+1)),fontsize=14)#normalized values
				cb=fig.colorbar(cax,ax=axarr[i,j],ticks=[-1,0,1])
				for t in cb.ax.get_yticklabels():
						t.set_fontsize(14)
				#fig.colorbar(cax,ax=axarr[i,j],ticks=[(M[i,j]/M[0,0]).min(),0.5*((M[i,j]/M[0,0]).min()+(M[i,j]/M[0,0]).max()),(M[i,j]/M[0,0]).max()])
			axarr[i,j].axis([thetai.min(),thetai.max(),210,1690])
			axarr[i,j].set_xticks([thetai.min(),0.5*(thetai.min()+thetai.max()),thetai.max()])
			for t in axarr[i,j].xaxis.get_major_ticks():
				t.label.set_fontsize(14) 
			axarr[i,j].set_yticks([210,950,1690])
			for t in axarr[i,j].yaxis.get_major_ticks():
				t.label.set_fontsize(14) 
			#cbar.ax.set_xticklabels(
			#cbar.set_major_formatter(mtick.FormatStrFormatter('%.2'))
			plt.setp([a.get_xticklabels() for a in axarr[0,:]], visible=False)
			plt.setp([a.get_xticklabels() for a in axarr[1,:]], visible=False)
			plt.setp([a.get_xticklabels() for a in axarr[2,:]], visible=False)
			plt.setp([a.get_yticklabels() for a in axarr[1:4,1]], visible=False)
			plt.setp([a.get_yticklabels() for a in axarr[:,2]], visible=False)
			plt.setp([a.get_yticklabels() for a in axarr[:,3]], visible=False)
			
			idx=idx+1

	axarr[0,1].set_ylabel(r'$\lambda [nm]$',fontsize=14)
	axarr[1,0].set_ylabel(r'$\lambda [nm]$',fontsize=14)
	axarr[2,0].set_ylabel(r'$\lambda [nm]$',fontsize=14)
	axarr[3,0].set_ylabel(r'$\lambda [nm]$',fontsize=14)
	axarr[3,0].set_xlabel(r'$\theta_i [\degree]$',fontsize=14)
	axarr[3,1].set_xlabel(r'$\theta_i [\degree]$',fontsize=14) 
	axarr[3,2].set_xlabel(r'$\theta_i [\degree]$',fontsize=14) 
	axarr[3,3].set_xlabel(r'$\theta_i [\degree]$',fontsize=14)
	plt.show()

	Pd,wL,thetai=propMM.DepolIndex(wL,thetai,M)
	D,wL,thetai=propMM.Diattenuation(wL,thetai,M)
	P,wL,thetai=propMM.Polarizance(wL,thetai,M)
	#Plot of depolarization, polarizance and diattenuation
	plt.figure()
	plt.subplot(131)#depolarisation
	plt.pcolormesh(thetai,wL,Pd,vmin=0,vmax=1)
	#plt.colorbar(ticks=[0,0.5,1])
	plt.axis([thetai.min(),thetai.max(),210,1690])
	plt.xticks([thetai.min(),0.5*(thetai.min()+thetai.max()),thetai.max()],fontsize=14)
	plt.yticks([210,950,1690],fontsize=14)
	plt.title('a)',fontsize=14)
	plt.xlabel(r'$\theta_r [\degree]$',fontsize=14)
	plt.ylabel(r'$\lambda [nm]$',fontsize=14)
	plt.subplot(132)#diattenuation
	plt.pcolormesh(thetai,wL,D,vmin=0,vmax=1)
	#plt.colorbar(ticks=[0,0.5,1])
	plt.axis([thetai.min(),thetai.max(),210,1690])
	plt.xticks([thetai.min(),0.5*(thetai.min()+thetai.max()),thetai.max()],fontsize=14)
	plt.yticks([210,950,1690],visible=False)
	plt.title('b)',fontsize=14)
	plt.xlabel(r'$\theta_r [\degree]$',fontsize=14)
	#plt.ylabel(r'$\lambda [nm]$',fontsize=14)
	plt.subplot(133)#polarizance
	plt.pcolormesh(thetai,wL,P,vmin=0,vmax=1)
	cb=plt.colorbar(ticks=[0,0.5,1])
	for t in cb.ax.get_yticklabels():
		t.set_fontsize(14)
	plt.axis([thetai.min(),thetai.max(),210,1690])
	plt.xticks([thetai.min(),0.5*(thetai.min()+thetai.max()),thetai.max()],fontsize=14)
	plt.yticks([210,950,1690],visible=False)
	plt.title('c)',fontsize=14)
	plt.xlabel(r'$\theta_r [\degree]$',fontsize=14)
	#plt.ylabel(r'$\lambda [nm]$',fontsize=14)
	plt.show()    

	#Plot 45 deg and 64 deg in same Mueller matrix
	deg45=40
	deg65=80
	idx=1
	fig,axarr=plt.subplots(4,4)
	for i in range(4):
		for j in range(4):
			if idx==1:
				axarr[0,0].plot((M[0,0])[deg45,:])
				axarr[0,0].set_title('M11',fontsize=14)
				axarr[0,0].set_visible(False) 
			else:
				axarr[i,j].plot((M[i,j])[deg45,:],c='red')
				axarr[i,j].plot(M[i,j][deg65,:],c='blue')
				axarr[i,j].set_title(r'$M_{%s}$' %(str(i+1)+str(j+1)),fontsize=14)#normalized values
			axarr[i,j].set_xticks([210,950,1690])
			for t in axarr[i,j].xaxis.get_major_ticks():
				t.label.set_fontsize(14) 
			axarr[i,j].axis([0,N,-1.1,1.1])
			axarr[i,j].set_yticks([-1,0,1])
			for t in axarr[i,j].yaxis.get_major_ticks():
				t.label.set_fontsize(14) 
			plt.setp(axarr[i,j], xticks=[0, (N-1)/2, (N-1)], xticklabels=[210,950,1690])
			plt.setp([a.get_xticklabels() for a in axarr[0,:]], visible=False)
			plt.setp([a.get_xticklabels() for a in axarr[1,:]], visible=False)
			plt.setp([a.get_xticklabels() for a in axarr[2,:]], visible=False)
			plt.setp([a.get_yticklabels() for a in axarr[1:4,1]], visible=False)
			plt.setp([a.get_yticklabels() for a in axarr[:,2]], visible=False)
			plt.setp([a.get_yticklabels() for a in axarr[:,3]], visible=False)

			idx=idx+1
	axarr[3,0].set_xlabel(r'$\lambda [nm]$',fontsize=14)
	axarr[3,1].set_xlabel(r'$\lambda [nm]$',fontsize=14) 
	axarr[3,2].set_xlabel(r'$\lambda [nm]$',fontsize=14) 
	axarr[3,3].set_xlabel(r'$\lambda [nm]$',fontsize=14)
	plt.show()
	return 

#plotMuellerReflCoreShell(1240/210,1240/1690,100,(1/3.1)*10**-9,100,170,3.1*10**3)
