# -*- coding: utf-8 -*-
"""
Created on Mon Nov 17 01:15:51 2014

@author: christian
"""
from __future__ import division
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
import scipy.special as spc
import calculationOfScattering as cs
import MuellerImportExport as mie
#Light scattering with a core shell structure
#Defining constants
def coeffCoreShell(rcore,rshell,ncore,nshell,nm,thetai,wL): 
    #wL,thetai=np.meshgrid(wL,thetai)
    #Defining constants
    #k1=2*np.pi/wL1
    #k2=2*np.pi/wL2
    k=2*np.pi/wL
    x1=k*rcore
    x2=k*rshell
    x=x1+x2
    phi=np.pi #scattering angle in phi direction radians
    psi=np.pi-phi 

    m1=ncore/nm #1 is core
    m2=nshell/nm #2 is shell
    mu1=1
    mu2=1

    eta1=x1*np.sqrt(m1**2-np.cos(thetai)**2)
    eta2=x2*np.sqrt(m2**2-np.cos(thetai)**2)
    beta1=x1*np.sqrt(m2**2-np.cos(thetai)**2)
    
    g1=mu1/m1
    xi1=x1*np.sin(thetai)
    v1=xi1/eta1
    gamma1=m1*xi1/(eta1)
    
    g2=mu2/m2
    xi2=x2*np.sin(thetai)
    v2=xi2/eta2
    gamma2=m2*xi2/(eta2)    
    
    n=0
    besselxi1=spc.jv(n,xi1)
    dbesselxi1=spc.jvp(n,xi1,1)
    besseleta1=spc.jv(n,eta1)
    dbesseleta1=spc.jvp(n,eta1,1)
    hankelxi1=spc.hankel1(n,xi1)
    dhankelxi1=spc.h1vp(n,xi1,1)
    #neumannxi1=spc.yv(n,xi1)    
    #dneumannxi1=spc.yvp(n,xi1,1)
        
    besselxi2=spc.jv(n,xi2)
    dbesselxi2=spc.jvp(n,xi2,1)
    besseleta2=spc.jv(n,eta2)
    dbesseleta2=spc.jvp(n,eta2,1)
    hankelxi2=spc.hankel1(n,xi2)
    dhankelxi2=spc.h1vp(n,xi2,1)
    #neumannxi2=spc.yv(n,xi2)    
    #dneumannxi2=spc.yvp(n,xi2,1)
    neumanneta2=spc.yv(n,eta2)    
    dneumanneta2=spc.yvp(n,eta2,1)    
    
    besselbeta1=spc.jv(n,beta1)
    dbesselbeta1=spc.jvp(n,beta1,1)
    neumannbeta1=spc.yv(n,beta1)    
    dneumannbeta1=spc.yvp(n,beta1,1)
    
    Dn1xi1=dbesselxi1/besselxi1
    #Dn2xi1=dneumannxi1/neumannxi1
    Dn3xi1=dhankelxi1/hankelxi1 #wrong in paper        
    Tnxi1=besselxi1/hankelxi1
    #Pnxi1=besselxi1/neumannxi1
    Dn1eta1=dbesseleta1/besseleta1
    Dn1beta1=dbesselbeta1/besselbeta1
    Dn2beta1=dneumannbeta1/neumannbeta1
    Pnbeta1=besselbeta1/neumannbeta1    
    
    Dn1xi2=dbesselxi2/besselxi2
    #Dn2xi2=dneumannxi2/neumannxi2
    Dn3xi2=dhankelxi2/hankelxi2 #wrong in paper        
    Tnxi2=besselxi2/hankelxi2
    #Pnxi2=besselxi2/neumannxi2    
    Pneta2=besseleta2/neumanneta2
    Dn1eta2=dbesseleta2/besseleta2
    Dn2eta2=dneumanneta2/neumanneta2
    #Initial conditions
    #An1=0
    #Bn1=0    
    Hna1=Dn1eta1
    Hnb1=Dn1eta1
    lambda1=np.cos(thetai)*(1-(eta1**2/beta1**2))
    
    Wna1=(mu1/mu2)*((Hna1/v1)+((n*lambda1)/(mu1*beta1)))
    Wnb1=(mu1/mu2)*(m1/m2)**2*((Hnb1/v1)+((n*lambda1*mu1)/(m1**2*beta1)))
    
    An2=Pnbeta1*(Wna1-Dn1beta1)/(Wna1-Dn2beta1)
    Bn2=Pnbeta1*(Wnb1-Dn1beta1)/(Wnb1-Dn2beta1)    
    
    Hna2=(Pneta2*Dn1eta2-An2*Dn2eta2)/(Pneta2-An2)
    Hnb2=(Pneta2*Dn1eta2-Bn2*Dn2eta2)/(Pneta2-Bn2)
    
    #Defining functions            
    L11=Dn1xi1-Dn3xi1
    L21=g1*Dn3xi1-gamma1*Hnb1
    L31=Dn3xi1-g1*gamma1*Hna1
    L41=g1*Dn1xi1-gamma1*Hnb1
    L51=Dn1xi1-g1*gamma1*Hna1
    
    L12=Dn1xi2-Dn3xi2
    L22=g2*Dn3xi2-gamma2*Hnb2
    L32=Dn3xi2-g2*gamma2*Hna2
    L42=g2*Dn1xi2-gamma2*Hnb2
    L52=Dn1xi2-g2*gamma2*Hna2
    
    denominator1=xi1**2*L21*L31-g1*n**2*np.cos(thetai)**2*(v1**2-1)**2
    denominator2=xi2**2*L22*L32-g2*n**2*np.cos(thetai)**2*(v2**2-1)**2          
            
    #TM
    a11=(1j*g1*(v1**2-1)*xi1*n*np.cos(thetai)*Tnxi1*L11)/(denominator1)
    a12=(1j*g2*(v2**2-1)*xi2*n*np.cos(thetai)*Tnxi2*L12)/(denominator2)
    a1=a11+a12
    b11=(xi1**2*L41*L31-g1*n**2*np.cos(thetai)**2*(v1**2-1)**2)/(denominator1)
    b12=(xi2**2*L42*L32-g2*n**2*np.cos(thetai)**2*(v2**2-1)**2)/(denominator2)
    b1=b11+b12
    #TE
    a21=Tnxi1*(xi1**2*L51*L21-g1*n**2*np.cos(thetai)**2*(v1**2-1)**2)/(denominator1)
    a22=Tnxi2*(xi2**2*L52*L22-g2*n**2*np.cos(thetai)**2*(v2**2-1)**2)/(denominator2)
    a2=a21+a22
    b21=-(1j*g1*(v1**2-1)*xi1*n*np.cos(thetai)*Tnxi1*L11)/(denominator1)
    b22=-(1j*g2*(v2**2-1)*xi2*n*np.cos(thetai)*Tnxi2*L12)/(denominator2)
    b2=b21+b22
    #Calculating T coefficents
    T1=b1
    T2=a2
    T3=0
    T4=0
    
    #Calculating Q coefficents
    Qsca1=(2/x1)*sp.absolute(b11)**2+(2/x2)*sp.absolute(b12)**2
    Qsca2=(2/x1)*sp.absolute(a21)**2+(2/x2)*sp.absolute(a22)**2
    Qext1=(2/x1)*sp.real(b11)+(2/x2)*sp.real(b12)
    Qext2=(2/x1)*sp.real(a21)+(2/x2)*sp.real(a22)
    
    for n in range(1,100):
        besselxi1=spc.jv(n,xi1)
        dbesselxi1=spc.jvp(n,xi1,1)
        besseleta1=spc.jv(n,eta1)
        dbesseleta1=spc.jvp(n,eta1,1)
        hankelxi1=spc.hankel1(n,xi1)
        dhankelxi1=spc.h1vp(n,xi1,1)
        #neumannxi1=spc.yv(n,xi1)    
        #dneumannxi1=spc.yvp(n,xi1,1)
            
        besselxi2=spc.jv(n,xi2)
        dbesselxi2=spc.jvp(n,xi2,1)
        besseleta2=spc.jv(n,eta2)
        dbesseleta2=spc.jvp(n,eta2,1)
        hankelxi2=spc.hankel1(n,xi2)
        dhankelxi2=spc.h1vp(n,xi2,1)
        #neumannxi2=spc.yv(n,xi2)    
        #dneumannxi2=spc.yvp(n,xi2,1)
        neumanneta2=spc.yv(n,eta2)    
        dneumanneta2=spc.yvp(n,eta2,1)    
        
        besselbeta1=spc.jv(n,beta1)
        dbesselbeta1=spc.jvp(n,beta1,1)
        neumannbeta1=spc.yv(n,beta1)    
        dneumannbeta1=spc.yvp(n,beta1,1)
        
        Dn1xi1=dbesselxi1/besselxi1
        #Dn2xi1=dneumannxi1/neumannxi1
        Dn3xi1=dhankelxi1/hankelxi1 #wrong in paper        
        Tnxi1=besselxi1/hankelxi1
        #Pnxi1=besselxi1/neumannxi1
        Dn1eta1=dbesseleta1/besseleta1
        Dn1beta1=dbesselbeta1/besselbeta1
        Dn2beta1=dneumannbeta1/neumannbeta1
        Pnbeta1=besselbeta1/neumannbeta1    
        
        Dn1xi2=dbesselxi2/besselxi2
        #Dn2xi2=dneumannxi2/neumannxi2
        Dn3xi2=dhankelxi2/hankelxi2 #wrong in paper        
        Tnxi2=besselxi2/hankelxi2
        #Pnxi2=besselxi2/neumannxi2    
        Pneta2=besseleta2/neumanneta2
        Dn1eta2=dbesseleta2/besseleta2
        Dn2eta2=dneumanneta2/neumanneta2
        
        #Initial conditions
        Hna1=Dn1eta1
        Hnb1=Dn1eta1
        lambda1=np.cos(thetai)*(1-(eta1**2/beta1**2))
        
        Wna1=(mu1/mu2)*((Hna1/v1)+((n*lambda1)/(mu1*beta1)))
        Wnb1=(mu1/mu2)*(m1/m2)**2*((Hnb1/v1)+((n*lambda1*mu1)/(m1**2*beta1)))
        
        An2=Pnbeta1*(Wna1-Dn1beta1)/(Wna1-Dn2beta1)
        Bn2=Pnbeta1*(Wnb1-Dn1beta1)/(Wnb1-Dn2beta1)    
        
        Hna2=(Pneta2*Dn1eta2-An2*Dn2eta2)/(Pneta2-An2)
        Hnb2=(Pneta2*Dn1eta2-Bn2*Dn2eta2)/(Pneta2-Bn2)
        
        #Defining functions            
        L11=Dn1xi1-Dn3xi1
        L21=g1*Dn3xi1-gamma1*Hnb1
        L31=Dn3xi1-g1*gamma1*Hna1
        L41=g1*Dn1xi1-gamma1*Hnb1
        L51=Dn1xi1-g1*gamma1*Hna1
        
        L12=Dn1xi2-Dn3xi2
        L22=g2*Dn3xi2-gamma2*Hnb2
        L32=Dn3xi2-g2*gamma2*Hna2
        L42=g2*Dn1xi2-gamma2*Hnb2
        L52=Dn1xi2-g2*gamma2*Hna2

        denominator1=xi1**2*L21*L31-g1*n**2*np.cos(thetai)**2*(v1**2-1)**2
        denominator2=xi2**2*L22*L32-g2*n**2*np.cos(thetai)**2*(v2**2-1)**2          
            
        #TM
        a11=(1j*g1*(v1**2-1)*xi1*n*np.cos(thetai)*Tnxi1*L11)/(denominator1)
        a12=(1j*g2*(v2**2-1)*xi2*n*np.cos(thetai)*Tnxi2*L12)/(denominator2)
        a1=a11+a12
        b11=(xi1**2*L41*L31-g1*n**2*np.cos(thetai)**2*(v1**2-1)**2)/(denominator1)
        b12=(xi2**2*L42*L32-g2*n**2*np.cos(thetai)**2*(v2**2-1)**2)/(denominator2)
        b1=b11+b12
        #TE
        a21=Tnxi1*(xi1**2*L51*L21-g1*n**2*np.cos(thetai)**2*(v1**2-1)**2)/(denominator1)
        a22=Tnxi2*(xi2**2*L52*L22-g2*n**2*np.cos(thetai)**2*(v2**2-1)**2)/(denominator2)
        a2=a21+a22
        b22=-(1j*g1*(v1**2-1)*xi1*n*np.cos(thetai)*Tnxi1*L11)/(denominator1)
        b21=-(1j*g2*(v2**2-1)*xi2*n*np.cos(thetai)*Tnxi2*L12)/(denominator2)
        b2=b21+b22
        #Calculating T coefficeients
        T1=T1+2*b1*np.cos(n*psi)
        T2=T2+2*a2*np.cos(n*psi)
        T3=T3-2j*a1*np.sin(n*psi)
        T4=T4-2j*b2*np.sin(n*psi)
        
        #Calculating Q coefficents
        Qsca1=Qsca1+(2/x1)*2*(sp.absolute(b11)**2+sp.absolute(a11)**2)+(2/x2)*2*(sp.absolute(b12)**2+sp.absolute(a12)**2) #p-polarized light
        Qsca2=Qsca2+(2/x1)*2*(sp.absolute(a21)**2+sp.absolute(b21)**2)+(2/x2)*2*(sp.absolute(a22)**2+sp.absolute(b22)**2) #s-polarized light
        Qext1=Qext1+(2/x1)*sp.real(2*b11)+(2/x2)*sp.real(2*b12) #p-polarized light
        Qext2=Qext2+(2/x1)*sp.real(2*a21)+(2/x2)*sp.real(2*a22) #s-polarized light
        
        if (sp.sum(a1)+sp.sum(a2)+sp.sum(b1)+sp.sum(b2))<10**-18:
            break
    
    Qabs1=Qext1-Qsca1 #p-polarized light
    Qabs2=Qext2-Qsca2 #s-polarized light
    Qsca=0.5*(Qsca1+Qsca2) #unpolarized light
    Qext=0.5*(Qext1+Qext2) #unpolarized light
    Qabs=Qext-Qsca 
    #thetai=180*thetai/np.pi
    
    Q=[[Qsca1,Qsca2,Qsca],[Qabs1,Qabs2,Qabs]]
    Q=np.squeeze(Q)
    
    T=[[T1,T4],[T3,T2]]
    T=np.squeeze(T)
    return T, Q, k


def plotCoreShellEff():
    wL_max=4.1
    wL_min=1
    wL=np.linspace(wL_min, wL_max,100)
    thetai=np.linspace(0.001,np.pi/2,50)
    comment, wL1, ec1, ec2 = mie.iMatCE('materialFiles/CE_MAT/Semiconductor/GaAs.mat',wL) #core #GaAsSb
    comment, wL2, es1, es2 = mie.iMatCE('materialFiles/CE_MAT/Semiconductor/GaAs.mat',wL) #shell

    wL=1240/wL
    wL=np.sort(wL)
    wL,thetai=np.meshgrid(wL,thetai)
    nn1,kk1=cs.eps2nk(ec1,ec2)
    nn2,kk2=cs.eps2nk(es1,es2)
    ncore=nn1+1j*kk1
    nshell=nn2+1j*kk2   
    nm=1
    rshell=200
    rcore=50
    
    T,Q,k=coeffCoreShell(rcore,rshell,ncore,nshell,nm,thetai,wL)
    #TM=T[0,0] #s-polarized
    #TE=T[1,1] #p-polarized
    #print 'TE='+str(TE)
    #print 'TM='+str(TM)
    print Q
    Qsca1=Q[0,0]
    Qsca2=Q[0,1]
    Qsca=Q[0,2]
    Qabs1=Q[1,0]
    Qabs2=Q[1,1]
    Qabs=Q[1,2]
    
    thetai=180*thetai/np.pi   
    plt.figure()
    plt.subplot(3,2,1)
    plt.pcolormesh(thetai,wL,Qsca1,vmin=Qsca1.min(),vmax=Qsca1.max())
    plt.colorbar(ticks=[Qsca1.min(),0.5*(Qsca1.min()+Qsca1.max()),Qsca1.max()])
    plt.title('a)')
    plt.xlabel('Incident Angle [deg]')
    plt.ylabel('Wavelength [nm]')
    plt.xticks([0,np.ceil(thetai.max())/2,np.ceil(thetai.max())])
    plt.yticks([200,wL.max()/2+100,wL.max()])  
        
    plt.subplot(3,2,3)
    plt.pcolormesh(thetai,wL,Qsca2,vmin=Qsca2.min(),vmax=Qsca2.max())
    plt.colorbar(ticks=[Qsca2.min(),0.5*(Qsca2.min()+Qsca2.max()),Qsca2.max()])
    plt.title('c)')
    plt.xlabel('Incident Angle [deg]')
    plt.ylabel('Wavelength [nm]')
    plt.xticks([0,np.ceil(thetai.max())/2,np.ceil(thetai.max())])
    plt.yticks([200,wL.max()/2+100,wL.max()])
        
    plt.subplot(3,2,5)
    plt.pcolormesh(thetai,wL,Qsca,vmin=Qsca.min(),vmax=Qsca.max())
    plt.colorbar(ticks=[Qsca.min(),0.5*(Qsca.min()+Qsca.max()),Qsca.max()])
    plt.title('e)')
    plt.xlabel('Incident Angle [deg]')
    plt.ylabel('Wavelength [nm]')
    plt.xticks([0,np.ceil(thetai.max())/2,np.ceil(thetai.max())])
    plt.yticks([200,wL.max()/2+100,wL.max()])
            
    plt.subplot(3,2,2)
    plt.pcolormesh(thetai,wL,Qabs1,vmin=Qabs1.min(),vmax=Qabs1.max())
    plt.colorbar(ticks=[Qabs1.min(),0.5*(Qabs1.min()+Qabs1.max()),Qabs1.max()])
    plt.title('b)')
    plt.xlabel('Incident Angle [deg]')
    plt.ylabel('Wavelength [nm]')
    plt.xticks([0,np.ceil(thetai.max())/2,np.ceil(thetai.max())])
    plt.yticks([200,wL.max()/2+100,wL.max()])
            
    plt.subplot(3,2,4)
    plt.pcolormesh(thetai,wL,Qabs2,vmin=Qabs2.min(),vmax=Qabs2.max())
    plt.colorbar(ticks=[Qabs2.min(),0.5*(Qabs2.min()+Qabs2.max()),Qabs2.max()])
    plt.title('d)')
    plt.xlabel('Incident Angle [deg]')
    plt.ylabel('Wavelength [nm]')
    plt.xticks([0,np.ceil(thetai.max())/2,np.ceil(thetai.max())])
    plt.yticks([200,wL.max()/2+100,wL.max()])
            
    plt.subplot(3,2,6)
    plt.pcolormesh(thetai,wL,Qabs,vmin=Qabs.min(),vmax=Qabs.max())
    plt.colorbar(ticks=[Qabs.min(),0.5*(Qabs.min()+Qabs.max()),Qabs.max()])
    plt.title('f)')
    plt.xlabel('Incident Angle [deg]')
    plt.ylabel('Wavelength [nm]')
    plt.xticks([0,np.ceil(thetai.max())/2,np.ceil(thetai.max())])
    plt.yticks([200,wL.max()/2+100,wL.max()])
    plt.tight_layout()
    plt.show()
    return
       

