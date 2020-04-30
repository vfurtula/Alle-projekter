#!/usr/bin/env python

import numpy as np
import materialLib as matLib
from scipy.interpolate import interp1d
import scipy.stats


def iMatCE(fname,wL_n=None):
    """
    reads epsilon data from CompleteEASE material file
    """
    data=np.genfromtxt(fname, dtype=float, delimiter='\t',skip_header=3)
    f = open(fname, 'r')
    comment=f.readline()
    wL_units=f.readline()
    optConstType=f.readline()
    f.close()
    wL=data[:,0]
    e1=data[:,1]
    e2=data[:,2]
    wLu=wL_units.strip()
    if wLu.lower()=='nm':
        wL=1240./wL
    osr=optConstType.strip()
    if osr.lower()=='nk':
        e1,e2=matLib.nk2eps(e1,e2)
    
    if wL_n is None:
        return comment, np.array(wL), np.array(e1), np.array(e2)
    e1,e2 = interp_e1e2(wL,np.array(e1),np.array(e2),np.array(wL_n))
    return comment, wL_n, e1, e2
    
    
def interp_e1e2(wL_o,e1,e2,wL):
    if wL_o[-1]<wL_o[0]:
        wL_o=wL_o[::-1]
        e1=e1[::-1]
        e2=e2[::-1]        
    e1_spline=interp1d(wL_o, e1, kind='linear')
    e1=e1_spline(wL)
    e2_spline=interp1d(wL_o, e2, kind='linear')
    e2=e2_spline(wL)
    return e1,e2

def interp_Mueller(wL_o,M,wL):
    '''
    Will interpolate the last dimension of the Mueller matrix (i.e. wavelength)  
    '''
    dim=len(M.shape)
    if wL_o[-1]<wL_o[0]:
        wL_o=wL_o[::-1]
        if dim==3:
            M=M[:,:,::-1]
        elif dim==4:
            M=M[:,:,:,::-1]
        else:
            M=M[:,:,:,::-1]
    if dim==4:
        Mr=np.zeros((4,4,M.shape[2],len(wL)))
        for i in range(4):
            for j in range(4):
                for k in range(M.shape[2]):
#                     print len(wL_o), len(np.squeeze(M[i,j,k,:]))
                    M_spline=interp1d(wL_o, np.squeeze(M[i,j,k,:]), kind=5)
                    Mr[i,j,k,:]=M_spline(wL)
    return Mr

def importCEaseCountourRot(fname):
    data=np.genfromtxt(fname, dtype=float, delimiter='\t',skip_header=1)
    nsr=np.squeeze(data[:,1]).tolist()
    N=nsr.count(nsr[0])
    wL=data[0:N,0]
    nRot=len(data[:,0])/N
    M=np.ones((4,4,nRot,N))
    for i in range(nRot):
        ta=2
        for j in range(4):
            for k in range(4):
                if not(k==0 and j==0):
                    M[k,j,i,:]=data[i*N:(i+1)*N,ta]
                    ta=ta+1
    rot=data[0:N:-1,1]
#     print len(wL), len(rot),M.shape
    return M,wL, rot

def importCEaseTheta(fname):
    data=np.genfromtxt(fname, skip_header=3, usecols=(1,2,3))
    wL=[data[0,0]]
    w=0
    theta=[data[0,1]]
    t=0
    M=np.ones((4,4,len(scipy.stats.itemfreq(data[:,0])),len(scipy.stats.itemfreq(data[:,1]))))
    for i in range(len(data)/22):
        k=i*22
        if data[k,0] not in wL:
            wL.append(data[k,0])
        if data[k,1] not in theta:
            theta.append(data[k,1])
        t=theta.index(data[k,1])
        w=wL.index(data[k,0])
        M[0,0,w,t]=1
        Mind=[[0,1],[0,2],[0,3],[1,0],[1,1],[1,2],[1,3],[2,0],[2,1],[2,2],[2,3],[3,0],[3,1],[3,2],[3,3]]
        for j in range(15):
            M[Mind[j][0],Mind[j][1],w,t]=data[k+7+j,2]
    dict={'M':M,'wL':wL,'theta':theta}
    return dict
    