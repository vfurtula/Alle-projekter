#!/usr/bin/env python
import numpy as np

def nk2eps(n,k):
		e1=np.multiply(n,n)-np.multiply(k,k)
		e2=2*np.multiply(n,k)
		return e1, e2

def eps2nk(e1,e2):
		n=np.sqrt((0.5*e1)+(0.5*np.sqrt(np.square(e1)+np.square(e2))))
		k=0.5*np.divide(e2,n)
		return n, k
    
