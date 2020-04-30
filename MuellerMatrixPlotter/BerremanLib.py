#!/usr/bin/env python

import numpy as np
import MuellerTools as mt
    
def rotation_Euler(phi,theta,psi):
		"""Returns rotation matrix defined by Euler angles (p,n,r)
			
		'angles' : tuple (p,n,r)
			
		Returns : rotation matrix M_R.
		If A is an initial vector,  B = M_R * A is the rotated vector

		Successive rotations : z,x',z'
				p = precession angle, 1st rotation, around z (0..2pi)
				n = nutation angle, 2nd rotation, around x' (0..pi)
				r = 3rd rotation, around z' (0..2pi)
			
		Euler rotation for the coordinates is Rz(p)*Rx(n)*Rz(r),
		where Rj(theta) is the matrix rotation for the coordinates.
		(see for example Fujiwara, p. 217)

		Note : The inverse rotation is (-r,-n,-p)
		"""
		c1 = np.cos(phi)
		s1 = np.sin(phi)
		c2 = np.cos(theta)
		s2 = np.sin(theta)
		c3 = np.cos(psi)
		s3 = np.sin(psi)
		return np.dot(np.dot([[c3,s3,0],[-s3,c3,0],[0,0,1]],[[1,0,0],[0,c2,s2],[0,-s2,c2]]),[[c1,s1,0],[-s1,c1,0],[0,0,1]])    
    
    
def rotateTensor(eps,phi,theta,psi,inline=True):
		sh=eps.shape
		rot1=rotation_Euler(phi,theta,psi)
		rot2=rotation_Euler(-1.*phi,-1.*theta,-1.*psi)
		eps2=np.zeros(eps.shape,dtype='complex')
		for i in range(sh[2]):
				for j in range(sh[3]):
						eps2[:,:,i,j]=np.dot(np.dot(rot1,np.squeeze(eps[:,:,i,j])),rot2)
		return eps2
   
    
def rotateTensor0D(eps,phi,theta,psi):
		rot1=rotation_Euler(phi,theta,psi)
		rot2=rotation_Euler(-1.*phi,-1.*theta,-1.*psi)
		return np.dot(np.dot(rot1,np.squeeze(eps)),rot2) 


def GlobalTransfer2Jones(T):
		"""returns the complex Jones matrix for a Berreman transfermatrix with no back reflections."""
		rpp=(T[0,0]*T[3,2]-T[3,0]*T[0,2])/(T[0,0]*T[2,2]-T[0,2]*T[2,0])
		rps=(T[0,0]*T[1,2]-T[1,0]*T[0,2])/(T[0,0]*T[2,2]-T[0,2]*T[2,0])
		rss=(T[1,0]*T[2,2]-T[1,2]*T[2,0])/(T[0,0]*T[2,2]-T[0,2]*T[2,0])
		rsp=(T[3,0]*T[2,2]-T[3,2]*T[2,0])/(T[0,0]*T[2,2]-T[0,2]*T[2,0])
		return np.matrix([[rpp,rps],[rsp,rss]],dtype=complex)

    
def La_inv(n_a,theta1):
		r1=[0,1,-1/(n_a*np.cos(theta1)),0]
		r2=[0,1,1/(n_a*np.cos(theta1)),0]
		r3=[1/np.cos(theta1),0,0,1/n_a]
		r4=[-1/np.cos(theta1),0,0,1/n_a]
		return 0.5*np.matrix([r1,r2,r3,r4],dtype=complex)

def Lf(n_s,cosTheta2):
		r1=[0,0,cosTheta2,0]
		r2=[1,0,0,0]
		r3=[-n_s*cosTheta2,0,0,0]
		r4=[0,0,n_s,0]
		return np.matrix([r1,r2,r3,r4],dtype=complex)

def Delta(kx,eps):
		r1=[-kx*np.divide(eps.item((2,0)),eps[2,2]),-kx*eps[2,1]/eps[2,2],0, 1-(kx**2/eps[2,2])]
		r2=[0,0,-1,0]
		r3=[eps[1,2]*eps[2,0]/eps[2,2]-eps[1,0], kx*kx+eps[1,2]*eps[2,1]/eps[2,2]-eps[1,1],0,kx*eps[1,2]/eps[2,2]]
		r4=[eps[0,0]-eps[0,2]*eps[2,1]/eps[2,2], eps[0,1]-eps[0,2]*eps[2,1]/eps[2,2],0,-kx*eps[0,2]/eps[2,2]]
		delta=np.matrix([r1,r2,r3,r4])
		#   print delta
		return delta

def findBeta(Deig,k0,d):
		def eigeig(Deig,i,j):
				return (Deig[i]-Deig[j])
		f=np.exp(1j*k0*Deig*d)
		beta=np.zeros((4,1),dtype=complex)
		a=np.array([[1,2,3,0],[2,3,0,1],[3,0,1,2],[0,1,2,3]])
		for i in range(4):
				beta[0]=beta[0]-Deig[np.mod(i+1,4)]*Deig[np.mod(i+2,4)]*Deig[np.mod(i+3,4)]*f[i]/(eigeig(Deig,i,np.mod(i+1,4))*eigeig(Deig,i,np.mod(i+2,4))*eigeig(Deig,i,np.mod(i+3,4)))
				beta[1]=beta[1]+((Deig[np.mod(i+1,4)]*Deig[np.mod(i+2,4)]+Deig[np.mod(i+1,4)]*Deig[np.mod(i+3,4)] + Deig[np.mod(i+2,4)]*Deig[np.mod(i+3,4)])*f[i]/(eigeig(Deig,i,np.mod(i+1,4))*eigeig(Deig,i,np.mod(i+2,4))*eigeig(Deig,i,np.mod(i+3,4))))
				beta[2]=beta[2]-(Deig[np.mod(i+1,4)]+Deig[np.mod(i+2,4)]+Deig[np.mod(i+3,4)])*f[i]/(eigeig(Deig,i,np.mod(i+1,4))*eigeig(Deig,i,np.mod(i+2,4))*eigeig(Deig,i,np.mod(i+3,4)))
				beta[3]=beta[3]+f[i]/(eigeig(Deig,i,np.mod(i+1,4))*eigeig(Deig,i,np.mod(i+2,4))*eigeig(Deig,i,np.mod(i+3,4)))
		return beta
    
def Tp(Delta,k0,d,eps):
		Deig,v = np.linalg.eig(Delta)
		if ((np.abs(Deig[0]-Deig[1]))<0.0001 or (np.abs(Deig[1]-Deig[2]))<0.0001 or 
				(np.abs(Deig[0]-Deig[2]))<0.0001 or (np.abs(Deig[1]-Deig[3]))<0.0001 or
				(np.abs(Deig[0]-Deig[3]))<0.0001): #Check if film is isotropic
		#         print 'anisotropic material does not work yet'
		#         print 'isotropic'
				tp1=np.cos(k0*d*Deig[0])
				r1=[tp1, 0, 0, -1j*Deig[0]*np.sin(k0*d*Deig[0])/eps[0,0]]
				r2=[0,tp1,1j*np.sin(k0*d*Deig[0])/Deig[0],0]
				r3=[0,1j*Deig[0]*np.sin(k0*d*Deig[0]),tp1,0]
				r4=[-1j*eps[0,0]*np.sin(k0*d*Deig[0])/Deig[0],0,0,tp1]
				Tp=np.matrix([r1,r2,r3,r4], dtype=complex)
		else: # if not it's anisotropic
				beta=findBeta(Deig,k0,-d)
				Tp=np.matrix(beta[0]*np.eye(4),dtype=complex)+np.multiply(beta[1],Delta)+np.multiply(beta[2],(Delta**2))+np.multiply(beta[3],(Delta**3))
		return Tp
        

class Material():

		def __init__(self):
				"""Creates a new material"""
				raise NotImplementedError("Should be implemented in derived classes")

		def getPermittivity(self,wl):
				"""Returns permittivity tensor"""
				raise NotImplementedError("Should be implemented in derived classes")
    
class isotropicMaterial(Material):
		material = None
		t = None


		def __init__(self,material=None,t=1e-6):
				"""Creates a new material"""
				self.setMaterial
				
		def setMaterial(self,material):
				"""Defines the material of layer"""
				self.material=material
				
		def setThickness(self,t):
				self.t=t

		def getPermittivityProfile(self,wl=1e-6):
				"""Returns permittivity  tensor of layer
				"""
				return [self.t, self.material.getTensor(wl)]
