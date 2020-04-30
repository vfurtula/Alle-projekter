#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
#import plotTools

import MuellerTools as mt
import BerremanLib as berrlib
import MuellerImportExport as mie
#import materialLib as matLib
#from lmfit import minimize, Parameters, Parameter, report_fit

import calculationOfScattering as cs

import scipy.ndimage
#import propertiesMM as propMM
# comment, wL_n, e1, e2 = mie.iMatCE('materialFiles/SiO2_JAW.MAT')
def plotMuellerRefl(wL_max,wL_min,N2,Nfactor,r,d):
    d=-d
    #wL_max=4.1
    #wL_min=1
    #N2=50
    wL=np.linspace(wL_min, wL_max,(wL_max-wL_min)/0.01+1)
    comment, wL_n, e1, e2 = mie.iMatCE('GaAs.mat',wL)
    comment_s, wL_s, e1_s, e2_s = mie.iMatCE('Si_JAW.mat',wL)#Si_JAW
    wL=np.sort(wL)
    wL=1240/wL
    N=np.size(wL)
    #print wL
    #k=2*np.pi*1240/wL
    #Nfactor=(1/5)*10**-9
    thetai=np.linspace(25*np.pi/180,75*np.pi/180,N2) #incident angle
    #thetai=np.pi/4
    wL,thetai=np.meshgrid(wL,thetai)
    #r=100
    nm=1
    nn,kk=cs.eps2nk(e1,e2)
    nc=nn+kk*1j
    
    S, Q, k=cs.coeff(r,nc,nm,thetai,wL)
    
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
    #improved plots of the mueller matrix
    #plt.figure()
    idx=1
    fig,axarr=plt.subplots(4,4,sharex='col', sharey='row')
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
            axarr[i,j].set_xticks([210,950,1690])
            plt.setp([a.get_xticklabels() for a in axarr[0,:]], visible=False)
            plt.setp([a.get_xticklabels() for a in axarr[1,:]], visible=False)
            plt.setp([a.get_xticklabels() for a in axarr[2,:]], visible=False)
            plt.setp([a.get_yticklabels() for a in axarr[:,1]], visible=False)
            plt.setp([a.get_yticklabels() for a in axarr[:,2]], visible=False)
            plt.setp([a.get_yticklabels() for a in axarr[:,3]], visible=False)
            
            idx=idx+1
    '''        
    axarr[0,0].set_ylabel(r'$\theta_i [\degree]$')
    #axarr[0,0].set_ylabel("Inc Ang [deg]")
    axarr[1,0].set_ylabel(r'$\theta_i [\degree]$')
    axarr[2,0].set_ylabel(r'$\theta_i [\degree]$')
    axarr[3,0].set_ylabel(r'$\theta_i [\degree]$')
    axarr[3,0].set_xlabel(r'$\lambda [nm]$')
    axarr[3,1].set_xlabel(r'$\lambda [nm]$') 
    axarr[3,2].set_xlabel(r'$\lambda [nm]$') 
    axarr[3,3].set_xlabel(r'$\lambda [nm]$')
    '''
    fig.text(0.5, 0.04, 'Incident angle [deg]',ha='center',va='center',fontsize=20)
    fig.text(0.06, 0.5, 'Wavelength [nm]',ha='center',va='center',rotation='vertical',fontsize=20)
    
    plt.show()
    
    #Make 1D plot of incident angles at 45 degrees
    deg=40
    print deg
    idx=1
    fig,axarr=plt.subplots(4,4)
    for i in range(4):
        for j in range(4):
            if idx==1:
                axarr[0,0].plot((M[0,0])[deg,:])
                axarr[0,0].set_title('M11',fontsize=14)
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
                axarr[0,0].set_title('M11',fontsize=14)
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
    
    #Change axis for lambda and thetai
    idx=1
    
    
    my_string='SC571_FP_pos2_IncAng30-75_contour.txt'
    my_matrix='4x4'
    MMs=[['M11','M12','M13','M14'],['M21','M22','M23','M24'],['M31','M32','M33','M34'],['M41','M42','M43','M44']]
    
    wl=wL
    angs=thetai
    Mm=M
    
    # Prepare space new figure and respective subplots
    fig, axs = plt.subplots(4,4,sharex='col', sharey='row',figsize=(15,12))
    # Perform meshgrid for easy 2.5D plotting
    #X, Y = np.meshgrid(angs, wl)  
    # Global level can be set for all subplots by using My_level below
    #My_level = np.linspace(-1, 2, 40)
    for l in range(4): # columns
      for k in range(4): # rows
	# Make contour subplots
	if int(my_matrix[0])==1 and int(my_matrix[2])==1:
	  my_axs=axs
	elif int(my_matrix[0])>1 and int(my_matrix[2])==1:
	  my_axs=axs[k]
	elif int(my_matrix[0])==1 and int(my_matrix[2])>1:
	  my_axs=axs[l]
	else:
	  my_axs=axs[k,l]
	  
	# Individual contour levels for each subplot
	if l!=0 or k!=0:
	  My_level = np.linspace(-1, 1, 40)
	  #My_level = np.linspace(min(min(run) for run in Mm[k][l]), max(max(run) for run in Mm[k][l]), 40)
	else:
	  My_level = np.linspace(-1, 1, 40)
	  my_axs.text(0.5, 0.5, 'Normalized \n to unity', ha='center', va='center', \
	    transform=my_axs.transAxes, fontsize=24)

	css = my_axs.contourf(angs, wl, Mm[k][l], levels=My_level)
	fig.colorbar(css, ax=my_axs, format="%.2f")
	# Individual graph titles for each subplot
	my_axs.set_title(MMs[k][l])
	    
    # Adjust subplots spacing
    #fig.subplots_adjust(left=0.1, right=0.9, bottom=0.1, top=0.9, hspace=0.4, wspace=0.4)
    # Make a figure title. This is also a global title
    fig.suptitle(my_string, fontsize=20)
    fig.text(0.5, 0.04, 'Incident angle [deg]',ha='center',va='center',fontsize=20)
    fig.text(0.06, 0.5, 'Wavelength [nm]',ha='center',va='center',rotation='vertical',fontsize=20)
    # Save the figure. PNG is normally preferred to avoid very large files
    plt.savefig(my_string[:-3]+'png')
    plt.show()
    
    
    
    
      
    '''
    fig,axarr=plt.subplots(4,4,sharex='col', sharey='row',figsize=(15,12))
    
    cax=np.zeros([4,4])
    for i in range(4):
        for j in range(4):
            if idx==1:
                cax=axarr[0,0].pcolormesh(thetai,wL,M[0,0],vmin=-1,vmax=1)
                #fig.colorbar(cax,ax=axarr[0,0],ticks=[-1,0,1])
                axarr[0,0].set_title('M11',fontsize=14)
                axarr[0,0].set_visible(False) 
            else:
                cax=axarr[i,j].pcolormesh(thetai,wL,M[i,j]/M[0,0],vmin=-1,vmax=1)
                axarr[i,j].set_title(r'$M_{%s}$' %(str(i+1)+str(j+1)),fontsize=14)#normalized values
                cb=fig.colorbar(cax,ax=axarr[i,j],ticks=[-1,0,1])
                for t in cb.ax.get_yticklabels():
                    t.set_fontsize(14)
                #fig.colorbar(cax,ax=axarr[i,j],ticks=[(M[i,j]/M[0,0]).min(),0.5*((M[i,j]/M[0,0]).min()+(M[i,j]/M[0,0]).max()),(M[i,j]/M[0,0]).max()])
            
            axarr[i,j].axis([25,75,210,1690])
            axarr[i,j].set_xticks([25,50,75])
            for t in axarr[i,j].xaxis.get_major_ticks():
                t.label.set_fontsize(14) 
            axarr[i,j].set_yticks([210,950,1690])
            for t in axarr[i,j].yaxis.get_major_ticks():
                t.label.set_fontsize(14) 
            plt.setp([a.get_xticklabels() for a in axarr[0,:]], visible=False)
            plt.setp([a.get_xticklabels() for a in axarr[1,:]], visible=False)
            plt.setp([a.get_xticklabels() for a in axarr[2,:]], visible=False)
            plt.setp([a.get_yticklabels() for a in axarr[1:4,1]], visible=False)
            plt.setp([a.get_yticklabels() for a in axarr[:,2]], visible=False)
            plt.setp([a.get_yticklabels() for a in axarr[:,3]], visible=False)
            
            idx=idx+1
    
    axarr[0,1].set_ylabel(r'$\lambda [nm]$',fontsize=14)
    #axarr[0,0].set_ylabel("Inc Ang [deg]")
    axarr[1,0].set_ylabel(r'$\lambda [nm]$',fontsize=14)
    axarr[2,0].set_ylabel(r'$\lambda [nm]$',fontsize=14)
    axarr[3,0].set_ylabel(r'$\lambda [nm]$',fontsize=14)
    axarr[3,0].set_xlabel(r'$\theta_i [\degree]$',fontsize=14)
    axarr[3,1].set_xlabel(r'$\theta_i [\degree]$',fontsize=14) 
    axarr[3,2].set_xlabel(r'$\theta_i [\degree]$',fontsize=14) 
    axarr[3,3].set_xlabel(r'$\theta_i [\degree]$',fontsize=14)
    
    fig.text(0.5, 0.04, 'Incident angle [deg]',ha='center',va='center',fontsize=20)
    fig.text(0.06, 0.5, 'Wavelength [nm]',ha='center',va='center',rotation='vertical',fontsize=20)
    plt.show()
    '''
    
    
    
    
    
    
    
    
    
    
    
    
    
    '''
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
    '''
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
                axarr[i,j].plot(M[i,j][deg45,:],c='red')
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
    
if __name__ == "__main__":
      
    #plotMuellerRefl(1240/210,1240/1690,10,(1/4)*10**-9,200,4*10**3)
    plotMuellerRefl(6,0.2,100,(1/0.72*0.98*0.98)*10**-9,60,0.72*10**3)
    #plotMuellerRefl(1240/210,1240/1690,100,(1/3.8*0.6*0.6)*10**-9,50,3.8*10**3)


    """idx=1
	fig,axarr=plt.subplots(4,4)
	a=(1690-210)/N
	degpix=(1-25)/a
	x0, y0 = 0, degpix-1# These are in _pixel_ coordinates!!
	x1, y1 = degpix-1, degpix-1
	x, y = np.linspace(x0, x1, N), np.linspace(y0, y1, N)
	z=np.zeros([4,4,N])
	for i in range(4):
	    for j in range(4):
		if idx==1:
		    z[0,0]=scipy.ndimage.map_coordinates(M[0,0], np.vstack((x,y)))
		    axarr[0,0].plot(z[0,0])
		    axarr[0,0].set_title('M11')
		else:
		    z[i,j]=scipy.ndimage.map_coordinates(M[i,j]/M[0,0], np.vstack((x,y)))
		    axarr[i,j].plot(z[i,j])
		    axarr[i,j].set_title('M' +str(i+1)+str(j+1))#normalized values
		#axarr[i,j].axis([0,N2,-1,1.1])
		axarr[i,j].set_yticks([-1,0,1])
		plt.setp(axarr[i,j], xticks=[0, N/2, N], xticklabels=[210,950,1690])
		plt.setp([a.get_xticklabels() for a in axarr[0,:]], visible=False)
		plt.setp([a.get_xticklabels() for a in axarr[1,:]], visible=False)
		plt.setp([a.get_xticklabels() for a in axarr[2,:]], visible=False)
		plt.setp([a.get_yticklabels() for a in axarr[:,1]], visible=False)
		plt.setp([a.get_yticklabels() for a in axarr[:,2]], visible=False)
		plt.setp([a.get_yticklabels() for a in axarr[:,3]], visible=False)
      
		idx=idx+1
	axarr[3,0].set_xlabel(r'$\lambda [nm]$')
	axarr[3,1].set_xlabel(r'$\lambda [nm]$') 
	axarr[3,2].set_xlabel(r'$\lambda [nm]$') 
	axarr[3,3].set_xlabel(r'$\lambda [nm]$')
	plt.show()"""
	
    """plt.figure()
	plt.plot((M[3,3]/M[0,0])[8,:])"""
	#point (r,c)
	#vertikal: imdat[:,c]
	#horisontal: imdat[r,:]
    """plt.figure()
	x=plt.takeXsliceset(wL)
	plt.plot(wL,x)
	plt.show()  """
	#plot of the Jones vector J
    """plt.figure()
	plt.subplot(2,1,1)
	plt.pcolormesh(thetai,wL,J[0,0],vmin=J[0,0].min(),vmax=J[0,0].max())
	plt.colorbar()
	plt.title('J s-pol')
	plt.xlabel('Incident Angle [deg]')
	plt.ylabel('Wavelength [nm]')
	plt.xticks([np.ceil(thetai.min()),np.ceil((thetai.min()+thetai.max())/2),np.ceil(thetai.max())])
	plt.yticks([np.ceil(wL.min()),np.ceil((wL.max()+wL.min())/2),np.ceil(wL.max())])
	plt.subplot(2,1,2)
	plt.pcolormesh(thetai,wL,J[1,1],vmin=J[1,1].min(),vmax=J[1,1].max())
	plt.colorbar()
	plt.title('J p-pol')
	plt.xlabel('Incident Angle [deg]')
	plt.ylabel('Wavelength [nm]')
	plt.xticks([np.ceil(thetai.min()),np.ceil((thetai.min()+thetai.max())/2),np.ceil(thetai.max())])
	plt.yticks([np.ceil(wL.min()),np.ceil((wL.max()+wL.min())/2),np.ceil(wL.max())])
	plt.tight_layout()"""

    """#plot for M
	plt.figure()
	idx=1
	for i in range(4):
	    for j in range(4):
		plt.subplot(4,4,idx)
		if idx==1:
		    plt.pcolormesh(thetai,wL,M[0,0],vmin=M[0,0].min(),vmax=M[0,0].max())
		    plt.colorbar()
		    plt.title("M11")
		else:
		    plt.pcolormesh(thetai,wL, M[i,j]/M[0,0],vmin=(M[i,j]/M[0,0]).min(),vmax=(M[i,j]/M[0,0]).max())
		    #plt.contourf(thetai,wL,M[i,j]/M[0,0])
		    plt.colorbar(ticks=[(M[i,j]/M[0,0]).min(),0.5*((M[i,j]/M[0,0]).min()+(M[i,j]/M[0,0]).max()),(M[i,j]/M[0,0]).max()])
		    #plt.colorbar(ticks=[-1,0,1])
		    #if(not(M[i,j].min())  or (not(M[i,j].max()))): 
			#cbar.set_ticks([M[i,j].min(),(M[i,j].min()+M[i,j].max())/2,M[i,j].max()])
			#cbar.set_ticklabels([M[i,j].min(),(M[i,j].min()+M[i,j].max())/2,M[i,j].max()])
		    #else:
		    #cbar.set_ticks([-1,0,1])
		    #cbar.set_ticklabels([-1,0,1])
		    plt.title('M' +str(i+1)+str(j+1))
		plt.xlabel("Incident Angle [deg]")
		plt.ylabel("Wavelength [nm]")
		#plt.savefig(str(filname))
		plt.xticks([np.ceil(thetai.min()),np.ceil((thetai.min()+thetai.max())/2),np.ceil(thetai.max())])
		plt.yticks([np.ceil(wL.min()),np.ceil((wL.max()+wL.min())/2),np.ceil(wL.max())])
		idx=idx+1
	plt.tight_layout()
	plt.show()"""
	
    """plt.figure()
	idx=1
	for i in range(4):
	    for j in range(4):
		plt.subplot(4,4,idx)
		if idx==1:
		    plt.pcolormesh(thetai,wL,M[0,0],vmin=-1,vmax=1)
		    plt.colorbar(ticks=[-1,0,1])
		    plt.title("M11")
		else:
		    plt.pcolormesh(thetai,wL, M[i,j]/M[0,0],vmin=-1,vmax=1)
		    #plt.contourf(thetai,wL,M[i,j]/M[0,0])
		    plt.colorbar(ticks=[-1,0,1])
		    #plt.colorbar(ticks=[-1,0,1])
		    #if(not(M[i,j].min())  or (not(M[i,j].max()))): 
			#cbar.set_ticks([M[i,j].min(),(M[i,j].min()+M[i,j].max())/2,M[i,j].max()])
			#cbar.set_ticklabels([M[i,j].min(),(M[i,j].min()+M[i,j].max())/2,M[i,j].max()])
		    #else:
		    #cbar.set_ticks([-1,0,1])
		    #cbar.set_ticklabels([-1,0,1])
		    plt.title('M' +str(i+1)+str(j+1))#normalized values
		plt.xlabel("Incident Angle [deg]")
		plt.ylabel("Wavelength [nm]")
		#plt.savefig(str(filname))
		#plt.xticks([np.ceil(thetai.min()),np.ceil((thetai.min()+thetai.max())/2),np.ceil(thetai.max())])
		#plt.yticks([np.ceil(wL.min()),np.ceil((wL.max()+wL.min())/2),np.ceil(wL.max())])
		plt.xticks([25,50,75])
		plt.yticks([210,950,1690])
		idx=idx+1
	plt.tight_layout()
	#newimage = image.thumbnail(new_size)
	#im = im.resize(size_tuple)
	#image=Image.resize([2,2])
	plt.show()
	#plotMuellerRefl(1240/210,1240/1690,50,(1/3)*10**-9,20,3*10**3)
	#change MM such that Incident angle is Y and wL X
	plt.figure()
	#plt.figure(figsize=(100,100))
	idx=1
	#plt.subplots_adjust(left=0.1, bottom=0.1, right=2, top=2, wspace=0.5, hspace=0.7)
	for i in range(4):
	    for j in range(4):
		plt.subplot(4,4,idx)#sharex=True, sharey=True
		if idx==1:
		    plt.pcolormesh(wL,thetai,M[0,0],vmin=-1,vmax=1)
		    plt.colorbar(ticks=[-1,0,1])
		    plt.title("M11")
		else:
		    plt.pcolormesh(wL,thetai, M[i,j]/M[0,0],vmin=-1,vmax=1)
		    #plt.contourf(thetai,wL,M[i,j]/M[0,0])
		    plt.colorbar(ticks=[-1,0,1])
		    #plt.colorbar(ticks=[-1,0,1])
		    #if(not(M[i,j].min())  or (not(M[i,j].max()))): 
			#cbar.set_ticks([M[i,j].min(),(M[i,j].min()+M[i,j].max())/2,M[i,j].max()])
			#cbar.set_ticklabels([M[i,j].min(),(M[i,j].min()+M[i,j].max())/2,M[i,j].max()])
		    #else:
		    #cbar.set_ticks([-1,0,1])
		    #cbar.set_ticklabels([-1,0,1])
		    plt.title('M' +str(i+1)+str(j+1))#normalized values
		plt.ylabel("Inc Ang [deg]")
		plt.xlabel("Wavelength [nm]")
		#plt.savefig(str(filname))
		#plt.xticks([np.ceil(thetai.min()),np.ceil((thetai.min()+thetai.max())/2),np.ceil(thetai.max())])
		#plt.yticks([np.ceil(wL.min()),np.ceil((wL.max()+wL.min())/2),np.ceil(wL.max())])
		plt.yticks([25,50,75])
		plt.xticks([210,950,1690])
		idx=idx+1
	#plt.subplots_adjust(wspace=0,hspace=0)
	plt.show()"""
	
    """#plot of the nonzero values
	plt.figure()
	plt.subplot(2,1,1)
	plt.pcolormesh(thetai,wL,M[0,1]/M[0,0],vmin=-1,vmax=1)
	plt.colorbar()
	plt.title('M12')
	plt.xlabel('Incident Angle [deg]')
	plt.ylabel('Wavelength [nm]')
	plt.xticks([np.ceil(thetai.min()),np.ceil((thetai.min()+thetai.max())/2),np.ceil(thetai.max())])
	plt.yticks([np.ceil(wL.min()),np.ceil((wL.max()+wL.min())/2),np.ceil(wL.max())])
	plt.subplot(2,1,2)
	plt.pcolormesh(thetai,wL,M[1,0]/M[0,0],vmin=-1,vmax=1)
	plt.colorbar()
	plt.title('M21')
	plt.xlabel('Incident Angle [deg]')
	plt.ylabel('Wavelength [nm]')
	plt.xticks([np.ceil(thetai.min()),np.ceil((thetai.min()+thetai.max())/2),np.ceil(thetai.max())])
	plt.yticks([np.ceil(wL.min()),np.ceil((wL.max()+wL.min())/2),np.ceil(wL.max())])
	plt.tight_layout()
	
	plt.figure()
	plt.subplot(2,2,1)
	plt.pcolormesh(thetai,wL,M[2,2]/M[0,0],vmin=M[2,2].min(),vmax=M[2,2].max())
	plt.colorbar()
	plt.title('M33')
	plt.xlabel('Incident Angle [deg]')
	plt.ylabel('Wavelength [nm]')
	plt.xticks([np.ceil(thetai.min()),np.ceil((thetai.min()+thetai.max())/2),np.ceil(thetai.max())])
	plt.yticks([np.ceil(wL.min()),np.ceil((wL.max()+wL.min())/2),np.ceil(wL.max())])   
	plt.subplot(2,2,2)
	plt.pcolormesh(thetai,wL,M[2,3]/M[0,0],vmin=M[2,3].min(),vmax=M[2,3].max())
	plt.colorbar()
	plt.title('M34')
	plt.xlabel('Incident Angle [deg]')
	plt.ylabel('Wavelength [nm]')
	plt.xticks([np.ceil(thetai.min()),np.ceil((thetai.min()+thetai.max())/2),np.ceil(thetai.max())])
	plt.yticks([np.ceil(wL.min()),np.ceil((wL.max()+wL.min())/2),np.ceil(wL.max())])
	plt.subplot(2,2,3)
	plt.pcolormesh(thetai,wL,M[3,2]/M[0,0],vmin=M[3,2].min(),vmax=M[3,2].max())
	plt.colorbar()
	plt.title('M43')
	plt.xlabel('Incident Angle [deg]')
	plt.ylabel('Wavelength [nm]')
	plt.xticks([np.ceil(thetai.min()),np.ceil((thetai.min()+thetai.max())/2),np.ceil(thetai.max())])
	plt.yticks([np.ceil(wL.min()),np.ceil((wL.max()+wL.min())/2),np.ceil(wL.max())-1])
	plt.subplot(2,2,4)
	plt.pcolormesh(thetai,wL,M[3,3]/M[0,0],vmin=M[3,3].min(),vmax=M[3,3].max())
	plt.colorbar()
	plt.title('M44')
	plt.xlabel('Incident Angle [deg]')
	plt.ylabel('Wavelength [nm]')
	plt.xticks([np.ceil(thetai.min()),np.ceil((thetai.min()+thetai.max())/2),np.ceil(thetai.max())-1])
	plt.yticks([np.ceil(wL.min()),np.ceil((wL.max()+wL.min())/2),np.ceil(wL.max())])
	plt.tight_layout()
	plt.show()"""
	
    """#plot of the nonzero values with yticks from -1 to1
	plt.figure()
	plt.subplot(2,1,1)
	plt.pcolormesh(thetai,wL,M[0,1]/M[0,0],vmin=-1,vmax=1)
	plt.colorbar()
	plt.title('M12')
	plt.xlabel('Incident Angle [deg]')
	plt.ylabel('Wavelength [nm]')
	plt.xticks([15,45,75])
	plt.yticks([300,1000,1700])
	plt.subplot(2,1,2)
	plt.pcolormesh(thetai,wL,M[1,0]/M[0,0],vmin=-1,vmax=1)
	plt.colorbar()
	plt.title('M21')
	plt.xlabel('Incident Angle [deg]')
	plt.ylabel('Wavelength [nm]')
	plt.xticks([15,45,75])
	plt.yticks([300,1000,1700])
	plt.tight_layout()
	
	plt.figure()
	plt.subplot(2,2,1)
	plt.pcolormesh(thetai,wL,M[2,2]/M[0,0],vmin=-1,vmax=-1)
	plt.colorbar()
	plt.title('M33')
	plt.xlabel('Incident Angle [deg]')
	plt.ylabel('Wavelength [nm]')
	plt.xticks([15,45,75])
	plt.yticks([300,1000,1700])   
	plt.subplot(2,2,2)
	plt.pcolormesh(thetai,wL,M[2,3]/M[0,0],vmin=-1,vmax=1)
	plt.colorbar()
	plt.title('M34')
	plt.xlabel('Incident Angle [deg]')
	plt.ylabel('Wavelength [nm]')
	plt.xticks([15,45,75])
	plt.yticks([300,1000,1700])
	plt.subplot(2,2,3)
	plt.pcolormesh(thetai,wL,M[3,2]/M[0,0],vmin=-1,vmax=1)
	plt.colorbar()
	plt.title('M43')
	plt.xlabel('Incident Angle [deg]')
	plt.ylabel('Wavelength [nm]')
	plt.xticks([15,45,75])
	plt.yticks([300,1000,1700])
	plt.subplot(2,2,4)
	plt.pcolormesh(thetai,wL,M[3,3]/M[0,0],vmin=-1,vmax=1)
	plt.colorbar()
	plt.title('M44')
	plt.xlabel('Incident Angle [deg]')
	plt.ylabel('Wavelength [nm]')
	plt.xticks([15,45,75])
	plt.yticks([300,1000,1700])
	plt.tight_layout()
	plt.show()"""




