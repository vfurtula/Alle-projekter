# -*- coding: utf-8 -*-
"""
Created on Thu Nov  6 11:21:35 2014

@author: Christian A. Storås
"""
#Functions for calculation of scattering
from __future__ import division
#import matplotlib.pyplot as plt;
import numpy as np;
import scipy as sp;
import scipy.special as spc;

#thetai corresponds to zeta the incident angle
def expCoeff(x,m,thetai,l,r,npsi):
    #Defining functions
    #k=2*np.pi/l
    xi=x*sp.sin(thetai)   
    eta=x*(m**2-sp.cos(thetai)**2)**0.5
    T=np.zeros([2,2])
    ang=np.pi*(np.linspace(0,npsi-1,340)/(npsi-1))
    Q=[[0,0],[0,0],[0,0]] 
    n=0
    besselxi=spc.jv(n,xi)
    besseleta=spc.jv(n,eta)
    dbesseleta=spc.jvp(n,eta,1)
    dbesselxi=spc.jvp(n,xi,1)
    hankelxi=spc.hankel1(n,xi)
    dhankelxi=spc.h1vp(n,xi,1)
    
    An=1j*xi*(xi*dbesseleta*besselxi-eta*besseleta*dbesselxi)
    Bn=xi*(m**2*xi*dbesseleta*besselxi-eta*besseleta*dbesselxi)
    Cn=n*sp.cos(thetai)*eta*besseleta*besselxi*((xi**2/eta**2)-1)
    Dn=n*sp.cos(thetai)*eta*besseleta*hankelxi*((xi**2/eta**2)-1)
    Vn=xi*(m**2*xi*dbesseleta*hankelxi-eta*besseleta*dhankelxi)
    Wn=1j*xi*(eta*besseleta*dhankelxi-xi*dbesseleta*hankelxi)

    a1=(Cn*Vn-Bn*Dn)/(Wn*Vn+1j*Dn**2)
    b1=(Wn*Bn+1j*Dn*Cn)/(Wn*Vn+1j*Dn**2)
    a2=-(An*Vn-1j*Cn*Dn)/(Wn*Vn+1j*Dn**2)
    b2=-1j*(Cn*Wn+An*Dn)/(Wn*Vn+1j*Dn**2)
    
    T1=b1#T1
    T2=a2#T2
    T3=0#T3
    T4=0#T4
    
    Qsca1=(2/x)*sp.absolute(b1)**2
    Qsca2=(2/x)*sp.absolute(a2)**2
    Qext1=(2/x)*sp.real(b1)
    Qext2=(2/x)*sp.real(a2)

    for n in range(1,100):
        besselxi=spc.jv(n,xi)
        besseleta=spc.jv(n,eta)
        dbesseleta=spc.jvp(n,eta,1)
        dbesselxi=spc.jvp(n,xi,1)
        hankelxi=spc.hankel1(n,xi)
        dhankelxi=spc.h1vp(n,xi,1)

        An=1j*xi*(xi*dbesseleta*besselxi-eta*besseleta*dbesselxi)
        Bn=xi*(m**2*xi*dbesseleta*besselxi-eta*besseleta*dbesselxi)
        Cn=n*sp.cos(thetai)*eta*besseleta*besselxi*((xi**2/eta**2)-1)
        Dn=n*sp.cos(thetai)*eta*besseleta*hankelxi*((xi**2/eta**2)-1)
        Vn=xi*(m**2*xi*dbesseleta*hankelxi-eta*besseleta*dhankelxi)
        Wn=1j*xi*(eta*besseleta*dhankelxi-xi*dbesseleta*hankelxi)

        a1=(Cn*Vn-Bn*Dn)/(Wn*Vn+1j*Dn**2)
        b1=(Wn*Bn+1j*Dn*Cn)/(Wn*Vn+1j*Dn**2)
        a2=-(An*Vn-1j*Cn*Dn)/(Wn*Vn+1j*Dn**2)
        b2=-1j*(Cn*Wn+An*Dn)/(Wn*Vn+1j*Dn**2)
        
        T1=T1+2*b1*sp.cos(n*ang)#T1
        T2=T2+2*a2*sp.cos(n*ang)#T2
        T3=T3-2j*a1*sp.sin(n*ang)#T3
        T4=T4-2j*b2*sp.sin(n*ang)#T4

        Qext1=Qext1+(2/x)*sp.real(2*b1)
        Qext2=Qext2+(2/x)*sp.real(2*a2)
        Qsca1=Qsca1+(2/x)*2*(np.absolute(b1)**2)#+np.absolute(a1)**2)
        Qsca2=Qsca2+(2/x)*2*(np.absolute(a2)**2)#+np.absolute(b2)**2)
        Qabs1=Qext1-Qsca1
        Qabs2=Qext2-Qsca2
        
        #Csca1=Csca1+4/k*(2*sp.absolute(b1**2)+2*sp.absolute(a1**2))
        if (sp.sum(a1)+sp.sum(a2)+sp.sum(b1)+sp.sum(b2))<10**-18:
            break
    
    Q=[[Qext1,Qext2],[Qsca1,Qsca2],[Qabs1,Qabs2]]
    Q=np.squeeze(Q)
    
    G=2*r  
    Cext1=Q[0,0]*G
    Cext2=Q[0,1]*G
    Csca1=Q[1,0]*G
    Csca2=Q[1,1]*G
    Cabs1=Q[2,0]*G
    Cabs2=Q[2,1]*G    
    C=[[Cext1, Cext2],[Csca1,Csca2],[Cabs1,Cabs2]]
    C=np.squeeze(C);

    T=[[T1,T4],[T3,T2]]
    T=np.squeeze(T)
    return T, C, ang, Q
    
def calcScat(r,nc,nm,l,npsi,thetai):
    #defining constants    
    k=2*np.pi/l
    x=k*r
    m=nc/nm
    T, C, ang, Q=expCoeff(x,m,thetai,l,r,npsi)
    #ang=180*ang/np.pi; #returning the angle in degrees
    return T, C, ang, Q, k
    
    
#Calculation of Muller matrices    
def muellerMatrix(S):
    S=np.squeeze(S)    
    M=np.zeros([4,4,np.size(S,2)])
    S1=S[1,1]
    S2=S[0,0]
    S3=S[1,0]
    S4=S[0,1]

    absS1=sp.absolute(S1)**2
    absS2=sp.absolute(S2)**2
    absS3=sp.absolute(S3)**2
    absS4=sp.absolute(S4)**2
 
    M[0,0]=0.5*(absS1+absS2+absS3+absS4)
    M[0,1]=0.5*(absS2-absS1+absS4-absS3)
    M[0,2]=sp.real(S2*S3.conjugate()+S1*S4.conjugate())
    M[0,3]=sp.imag(S2*S3.conjugate()-S1*S4.conjugate())
    M[1,0]=0.5*(absS2 -absS1-absS4+absS3)
    M[1,1]=0.5*(absS2+absS1-absS4-absS3)
    M[1,2]=sp.real(S2*S3.conjugate()-S1*S4.conjugate())
    M[1,3]=sp.imag(S2*S3.conjugate()+S1*S4.conjugate())
    M[2,0]=sp.real(S2*S4.conjugate()+S1*S3.conjugate())
    M[2,1]=sp.real(S2*S4.conjugate()-S1*S3.conjugate())
    M[2,2]=sp.real(S1*S2.conjugate()+S3*S4.conjugate())
    M[2,3]=sp.imag(S2*S1.conjugate()+S4*S3.conjugate())
    M[3,0]=sp.imag(S2.conjugate()*S4+S3.conjugate()*S1)
    M[3,1]=sp.imag(S2.conjugate()*S4-S3.conjugate()*S1)
    M[3,2]=sp.imag(S1*S2.conjugate()-S3*S4.conjugate())
    M[3,3]=sp.real(S1*S2.conjugate()-S3*S4.conjugate())     
     
    return M

def refEff(N, k, S):
    neff=1+2*np.pi*N*k**(-3)*np.imag(S) #phase shift neff
    keff=-2*np.pi*N*k**(-3)*np.real(S) #change in intensity neff
    return  neff, keff

"""alfaVert=0.02 #different in GaAs
alfaNonVert=0.005 #different in GaAs

def refToEff(integral,k,S,alfaVert,alfaNonVert):
    neff=1+1j*2/(np.pi*k**2*integral)*(alfaVert*S+alfaNonVert*S)
    return neff"""
 
   
def convertEpsToRef(epsilon1, epsilon2):
    nreal=np.sqrt(0.5*(np.sqrt(epsilon1**2+epsilon2**2)+epsilon1))
    nim=np.sqrt(0.5*(np.sqrt(epsilon1**2+epsilon2**2)-epsilon1))*1j
    return nreal, nim

def eps2nk(e1,e2):
    n=np.sqrt((0.5*e1)+(0.5*np.sqrt(np.square(e1)+np.square(e2))))
    k=0.5*np.divide(e2,n)
    return n, k
    
def convertEnergToWl(E):
    h=4.135667516*10**-15 #eV s
    c=299792458 #m/s
    wl=c*h*10**9/E #return wavelength in nm
    return wl
    
def nk2eps(n,k):
    e1=np.multiply(n,n)-np.multiply(k,k)
    e2=2*np.multiply(n,k)
    return e1, e2
   

def coeff(r,nc,nm,thetai,l):
    k=2*np.pi/l           
    x=k*r
    phi=np.pi #scattering angle in phi direction radians
    psi=np.pi-phi 
    m=nc/nm #relation between nc and nm
    #thetai,l=np.meshgrid(thetai,l)
    xi=x*sp.sin(thetai)
    eta=x*(m**2-sp.cos(thetai)**2)**0.5

    n=0
    #Define besselfunctions
    besselxi=spc.jv(n,xi)
    besseleta=spc.jv(n,eta)
    dbesseleta=spc.jvp(n,eta,1)
    dbesselxi=spc.jvp(n,xi,1)
    hankelxi=spc.hankel1(n,xi)
    dhankelxi=spc.h1vp(n,xi,1)

    An=1j*xi*(xi*dbesseleta*besselxi-eta*besseleta*dbesselxi)
    Bn=xi*(m**2*xi*dbesseleta*besselxi-eta*besseleta*dbesselxi)
    Cn=n*sp.cos(thetai)*eta*besseleta*besselxi*((xi**2/eta**2)-1)
    Dn=n*sp.cos(thetai)*eta*besseleta*hankelxi*((xi**2/eta**2)-1)
    Vn=xi*(m**2*xi*dbesseleta*hankelxi-eta*besseleta*dhankelxi)
    Wn=1j*xi*(eta*besseleta*dhankelxi-xi*dbesseleta*hankelxi)

    a1=(Cn*Vn-Bn*Dn)/(Wn*Vn+1j*Dn**2)
    b1=(Wn*Bn+1j*Dn*Cn)/(Wn*Vn+1j*Dn**2)
    a2=-(An*Vn-1j*Cn*Dn)/(Wn*Vn+1j*Dn**2)
    b2=-1j*(Cn*Wn+An*Dn)/(Wn*Vn+1j*Dn**2)

    #Calculating T coefficents
    T1=b1
    T2=a2
    T3=0
    T4=0

    #Calculating Q coefficents
    Qsca1=(2/x)*sp.absolute(b1)**2
    Qsca2=(2/x)*sp.absolute(a2)**2
    Qext1=(2/x)*sp.real(b1)
    Qext2=(2/x)*sp.real(a2)

    for n in range(1,100):
        besselxi=spc.jv(n,xi)
        besseleta=spc.jv(n,eta)
        dbesseleta=spc.jvp(n,eta,1)
        dbesselxi=spc.jvp(n,xi,1)
        hankelxi=spc.hankel1(n,xi)
        dhankelxi=spc.h1vp(n,xi,1)

        An=1j*xi*(xi*dbesseleta*besselxi-eta*besseleta*dbesselxi)
        Bn=xi*(m**2*xi*dbesseleta*besselxi-eta*besseleta*dbesselxi)
        Cn=n*sp.cos(thetai)*eta*besseleta*besselxi*((xi**2/eta**2)-1)
        Dn=n*sp.cos(thetai)*eta*besseleta*hankelxi*((xi**2/eta**2)-1)
        Vn=xi*(m**2*xi*dbesseleta*hankelxi-eta*besseleta*dhankelxi)
        Wn=1j*xi*(eta*besseleta*dhankelxi-xi*dbesseleta*hankelxi)

        a1=(Cn*Vn-Bn*Dn)/(Wn*Vn+1j*Dn**2)
        b1=(Wn*Bn+1j*Dn*Cn)/(Wn*Vn+1j*Dn**2)
        a2=-(An*Vn-1j*Cn*Dn)/(Wn*Vn+1j*Dn**2)
        b2=-1j*(Cn*Wn+An*Dn)/(Wn*Vn+1j*Dn**2)
    
        #Calculating T coefficeients
        T1=T1+2*b1*sp.cos(n*psi)
        T2=T2+2*a2*sp.cos(n*psi)
        T3=T3-2j*a1*sp.sin(n*psi)
        T4=T4-2j*b2*sp.sin(n*psi)
    
        #Calculating Q coefficents
        Qsca1=Qsca1+(2/x)*2*(sp.absolute(b1)**2+sp.absolute(a1)**2) #p-polarized light
        Qsca2=Qsca2+(2/x)*2*(sp.absolute(a2)**2+sp.absolute(b2)**2) #p-polarized light
        Qext1=Qext1+(2/x)*sp.real(2*b1) #s-polarized light
        Qext2=Qext2+(2/x)*sp.real(2*a2) #s-polarized light
    
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