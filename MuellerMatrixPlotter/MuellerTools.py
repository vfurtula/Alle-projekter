#!/usr/bin/env python

import numpy as np

def Jones2Mueller(J):
	"""Converts a Jones matrix to a Mueller matrix"""
	r_pp=J[0,0]
	r_ps=J[0,1]
	r_sp=J[1,0]
	r_ss=J[1,1]
	M=np.zeros((4,4),dtype=complex)
	M[0,0]=0.5*(r_ss*np.conj(r_ss)+r_sp*np.conj(r_sp)+r_ps*np.conj(r_ps)+r_pp*np.conj(r_pp))
	M[0,1]=0.5*(-r_ss*np.conj(r_ss)+r_sp*np.conj(r_sp)-r_ps*np.conj(r_ps)+r_pp*np.conj(r_pp))
	M[1,0]=0.5*(r_pp*np.conj(r_pp)-r_sp*np.conj(r_sp)+r_ps*np.conj(r_ps)-r_ss*np.conj(r_ss))
	M[1,1]=0.5*(r_ss*np.conj(r_ss)-r_sp*np.conj(r_sp)-r_ps*np.conj(r_ps)+r_pp*np.conj(r_pp))
	M[0,2]=np.real(r_pp*np.conj(r_ps)+np.conj(r_ss)*r_sp)
	M[0,3]=np.imag(r_pp*np.conj(r_ps)+np.conj(r_ss)*r_sp)
	M[1,2]=np.real(r_pp*np.conj(r_ps)-np.conj(r_ss)*r_sp)
	M[1,3]=np.imag(r_pp*np.conj(r_ps)-np.conj(r_ss)*r_sp)
	M[2,0]=np.real(r_pp*np.conj(r_sp)+np.conj(r_ss)*r_ps)
	M[3,0]=-np.imag(r_pp*np.conj(r_sp)+np.conj(r_ss)*r_ps)
	M[2,1]=np.real(r_pp*np.conj(r_sp)-np.conj(r_ss)*r_ps)
	M[3,1]=-np.imag(r_pp*np.conj(r_sp)-np.conj(r_ss)*r_ps)
	M[2,2]=np.real(r_pp*np.conj(r_ss)+r_ps*np.conj(r_sp))
	M[3,3]=np.real(r_pp*np.conj(r_ss)-r_ps*np.conj(r_sp))
	M[2,3]=np.imag(r_pp*np.conj(r_ss)-r_ps*np.conj(r_sp))
	M[3,2]=-np.imag(r_pp*np.conj(r_ss)+r_ps*np.conj(r_sp))
	return np.matrix(np.real(M),dtype=float)

def normalize(M):
	M00=M[0,0]
	return np.divide(M,M00)

def MuellerElementInd(i):
	Ind=[[0,0],[0,1],[0,2],[0,3],[1,0],[1,1],[1,2],[1,3],[2,0],[2,1],[2,2],[2,3],[3,0],[3,1],[3,2],[3,3]]
	return Ind[i]
    
