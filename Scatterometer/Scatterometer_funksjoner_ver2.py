#import matplotlib.pyplot as plt
import numpy
import scipy.optimize as scop

class Scatterometer_funksjoner:
  
  def __init__(self):
    
    pass
  
  
  def Mueller_Matrix_polarizer_error(self,px,py):
    
    M_pol=0.5*numpy.array([[px**2+py**2,px**2-py**2,0,0],
			   [px**2-py**2,px**2+py**2,0,0],
			   [0,0,2*px*py,0],
			   [0,0,0,2*px*py]])
    return M_pol
  
  
  def Changebasis3(self,m,c):
    #Rewritten by LM
    #H matrix calculated with Maple
    H=numpy.array([[m[0,0]-c[0,0], -c[1,0], -c[2,0], -c[3,0], m[0,1], 0, 0, 0, m[0,2], 0, 0, 0, m[0,3], 0, 0, 0],
		   [-c[0,1], m[0,0]-c[1,1], -c[2,1], -c[3,1], 0, m[0,1], 0, 0, 0, m[0,2], 0, 0, 0, m[0,3], 0, 0],
		   [-c[0,2], -c[1,2], m[0,0]-c[2,2], -c[3,2], 0, 0, m[0,1], 0, 0, 0, m[0,2], 0, 0, 0, m[0,3], 0],
		   [-c[0,3], -c[1,3], -c[2,3], m[0,0]-c[3,3], 0, 0, 0, m[0,1], 0, 0, 0, m[0,2], 0, 0, 0, m[0,3]],
		   [m[1,0], 0, 0, 0, m[1,1]-c[0,0], -c[1,0], -c[2,0], -c[3,0], m[1,2], 0, 0, 0, m[1,3], 0, 0, 0],
		   [0, m[1,0], 0, 0, -c[0,1], m[1,1]-c[1,1], -c[2,1], -c[3,1], 0, m[1,2], 0, 0, 0, m[1,3], 0, 0],
		   [0, 0, m[1,0], 0, -c[0,2], -c[1,2], m[1,1]-c[2,2], -c[3,2], 0, 0, m[1,2], 0, 0, 0, m[1,3], 0],
		   [0, 0, 0, m[1,0], -c[0,3], -c[1,3], -c[2,3], m[1,1]-c[3,3], 0, 0, 0, m[1,2], 0, 0, 0, m[1,3]],
		   [m[2,0], 0, 0, 0, m[2,1], 0, 0, 0, m[2,2]-c[0,0], -c[1,0], -c[2,0], -c[3,0], m[2,3], 0, 0, 0],
		   [0, m[2,0], 0, 0, 0, m[2,1], 0, 0, -c[0,1], m[2,2]-c[1,1], -c[2,1], -c[3,1], 0, m[2,3], 0, 0],
		   [0, 0, m[2,0], 0, 0, 0, m[2,1], 0, -c[0,2], -c[1,2], m[2,2]-c[2,2], -c[3,2], 0, 0, m[2,3], 0],
		   [0, 0, 0, m[2,0], 0, 0, 0, m[2,1], -c[0,3], -c[1,3], -c[2,3], m[2,2]-c[3,3], 0, 0, 0, m[2,3]],
		   [m[3,0], 0, 0, 0, m[3,1], 0, 0, 0, m[3,2], 0, 0, 0, m[3,3]-c[0,0], -c[1,0], -c[2,0], -c[3,0]],
		   [0, m[3,0], 0, 0, 0, m[3,1], 0, 0, 0, m[3,2], 0, 0, -c[0,1], m[3,3]-c[1,1], -c[2,1], -c[3,1]],
		   [0, 0, m[3,0], 0, 0, 0, m[3,1], 0, 0, 0, m[3,2], 0, -c[0,2], -c[1,2], m[3,3]-c[2,2], -c[3,2]],
		   [0, 0, 0, m[3,0], 0, 0, 0, m[3,1], 0, 0, 0, m[3,2], -c[0,3], -c[1,3], -c[2,3], m[3,3]-c[3,3]]])
    
    return H
  
  
  def changebasis3A(self,m,c):
    #Rewritten by LM
    #H matrix calculated with Maple
    H=numpy.array([[m[0,0]-c[0,0], m[1,0], m[2,0], m[3,0], -c[0,1], 0, 0, 0, -c[0,2], 0, 0, 0, -c[0,3], 0, 0, 0],
		   [m[0,1], m[1,1]-c[0,0], m[2,1], m[3,1], 0, -c[0,1], 0, 0, 0, -c[0,2], 0, 0, 0, -c[0,3], 0, 0],
		   [m[0,2], m[1,2], m[2,2]-c[0,0], m[3,2], 0, 0, -c[0,1], 0, 0, 0, -c[0,2], 0, 0, 0, -c[0,3], 0],
		   [m[0,3], m[1,3], m[2,3], m[3,3]-c[0,0], 0, 0, 0, -c[0,1], 0, 0, 0, -c[0,2], 0, 0, 0, -c[0,3]],
		   [-c[1,0], 0, 0, 0, m[0,0]-c[1,1], m[1,0], m[2,0], m[3,0], -c[1,2], 0, 0, 0, -c[1,3], 0, 0, 0],
		   [0, -c[1,0], 0, 0, m[0,1], m[1,1]-c[1,1], m[2,1], m[3,1], 0, -c[1,2], 0, 0, 0, -c[1,3], 0, 0],
		   [0, 0, -c[1,0], 0, m[0,2], m[1,2], m[2,2]-c[1,1], m[3,2], 0, 0, -c[1,2], 0, 0, 0, -c[1,3], 0],
		   [0, 0, 0, -c[1,0], m[0,3], m[1,3], m[2,3], m[3,3]-c[1,1], 0, 0, 0, -c[1,2], 0, 0, 0, -c[1,3]],
		   [-c[2,0], 0, 0, 0, -c[2,1], 0, 0, 0, m[0,0]-c[2,2], m[1,0], m[2,0], m[3,0], -c[2,3], 0, 0, 0],
		   [0, -c[2,0], 0, 0, 0, -c[2,1], 0, 0, m[0,1], m[1,1]-c[2,2], m[2,1], m[3,1], 0, -c[2,3], 0, 0],
		   [0, 0, -c[2,0], 0, 0, 0, -c[2,1], 0, m[0,2], m[1,2], m[2,2]-c[2,2], m[3,2], 0, 0, -c[2,3], 0],
		   [0, 0, 0, -c[2,0], 0, 0, 0, -c[2,1], m[0,3], m[1,3], m[2,3], m[3,3]-c[2,2], 0, 0, 0, -c[2,3]],
		   [-c[3,0], 0, 0, 0, -c[3,1], 0, 0, 0, -c[3,2], 0, 0, 0, m[0,0]-c[3,3], m[1,0], m[2,0], m[3,0]],
		   [0, -c[3,0], 0, 0, 0, -c[3,1], 0, 0, 0, -c[3,2], 0, 0, m[0,1], m[1,1]-c[3,3], m[2,1], m[3,1]],
		   [0, 0, -c[3,0], 0, 0, 0, -c[3,1], 0, 0, 0, -c[3,2], 0, m[0,2], m[1,2], m[2,2]-c[3,3], m[3,2]],
		   [0, 0, 0, -c[3,0], 0, 0, 0, -c[3,1], 0, 0, 0, -c[3,2], m[0,3], m[1,3], m[2,3], m[3,3]-c[3,3]]])

    return H
  
  
  def ConvertNxMby1To4byMMatrix(self,vec,m):

    if len(vec)==4*m:	
      M=numpy.zeros((4,m))
      for i in range(4):
				M[i,:] = vec[i*m:(i+1)*m]
      return M
    else:
      return None


  def FindEigenvalueRatio4forAandW2(self,y,InMatrisesW,InMatrisesA,theta1):
    
    errorKAW=self.FindEigenvalueRatio4forA2(InMatrisesA,theta1,y)+self.FindEigenvalueRatio5(InMatrisesW,theta1,y)

    return errorKAW


  def FindEigenvalueRatio4forA2(self,InMatrises,theta1,y):

    MC1=InMatrises[0:4,0:4]
    C1=InMatrises[4:8,0:4]
    MC2=InMatrises[8:12,0:4]
    C2=InMatrises[12:16,0:4]
    MC3=InMatrises[16:20,0:4]
    C3=InMatrises[20:24,0:4]

    H1=self.changebasis3A(self.MuellerRotation_inline(MC1,theta1),C1)
    H2=self.changebasis3A(self.MuellerRotation_inline(MC2,y[0]),C2)
    H3=self.changebasis3A(self.MuellerRotation_inline(MC3,y[1]),C3)
    K=numpy.dot(H1.T,H1)+numpy.dot(H2.T,H2)+numpy.dot(H3.T,H3)

    u_,s_,v_=numpy.linalg.svd(K)
    EIGK=numpy.sort(s_)
    
    EigenvalueRatioV=numpy.zeros(16)
    
    for h in numpy.arange(1,len(EIGK)):
      EigenvalueRatioV[h] = EIGK[0]/EIGK[h]
    
    EigenvalueRatio2=numpy.sum(EigenvalueRatioV)

    return EigenvalueRatio2
  
  
  def FindEigenvalueRatio5(self,InMatrises,theta1,y):

    MC1=InMatrises[0:4,0:4]
    C1=InMatrises[4:8,0:4]
    MC2=InMatrises[8:12,0:4]
    C2=InMatrises[12:16,0:4]
    MC3=InMatrises[16:20,0:4]
    C3=InMatrises[20:24,0:4]

    H1=self.Changebasis3(self.MuellerRotation_inline(MC1,theta1),C1)
    H2=self.Changebasis3(self.MuellerRotation_inline(MC2,y[0]),C2)
    H3=self.Changebasis3(self.MuellerRotation_inline(MC3,y[1]),C3)
    K=numpy.dot(H1.T,H1)+numpy.dot(H2.T,H2)+numpy.dot(H3.T,H3)

    u_,s_,v_=numpy.linalg.svd(K)
    EIGK=numpy.sort(s_)
    EigenvalueRatioV=numpy.zeros(16)
    
    for h in numpy.arange(1,len(EIGK)):
      EigenvalueRatioV[h] = EIGK[0]/EIGK[h]
    
    EigenvalueRatio2=numpy.sum(EigenvalueRatioV)

    return EigenvalueRatio2
  
  
  def EVCSamplePropertiesForAandW_MK2(self,C1W,C2W,C3W,C1A,C2A,C3A,THETA0,opt,mode,MC1Rold,MC2Rold,MC3Rold,thetaold):
		# Eigenvalue calibration method of a Mueller Matix ellipsometry 
		# Written after Applied optics vol38 No 16 1999

		#eml.extrinsic('fminegen');
		#if nargin==8:
		#  mode='r' #added 230407,JL,311007 tB

		#####################  FINNER EGENVERDIER OK pr 10.10 2006 ###########################
		#Egenverdien til polarisatoren samt r og p verdier.
		tauPol=(numpy.trace(C1W)+numpy.trace(C2W))/2
		MC1=tauPol*self.Mueller_Matrix_polarizer_error(1,0)
		MC2=MC1
		#################################################################
		#Egenverdien og fase til retarderen. 
		eig_vals, eig_vecs = numpy.linalg.eig(C3W)
		sortedEg = self.sortEig(eig_vals)
		# PSIM=[numpy.arctan(numpy.sqrt(numpy.real(sortedEg[0])),numpy.sqrt(numpy.real(sortedEg[1]))) numpy.arctan(numpy.sqrt(numpy.real(sortedEg[1])),numpy.sqrt(numpy.real(sortedEg[0])))];
		PSIM=numpy.array([numpy.arctan2(numpy.real(numpy.sqrt(sortedEg[0])),numpy.real(numpy.sqrt(sortedEg[1]))),
											numpy.arctan2(numpy.real(numpy.sqrt(sortedEg[1])),numpy.real(numpy.sqrt(sortedEg[0])))])
		DELTAM=0.5*numpy.array([numpy.angle(sortedEg[2]/sortedEg[3]),numpy.angle(sortedEg[3]/sortedEg[2])])

		# TAU=numpy.trace(C3)#bug? kan gi tau>1
		TAU = (sortedEg[0]+sortedEg[1])/2
		
		MC3 = self.Mueller_Matrix_ppret(TAU,PSIM[1],DELTAM[1]+numpy.pi,mode)
		#Her maa det kontrolleres DELTA, for retardanser over 90deg gir egenverdiene feil veerdi...

		# if opt==1,
		############################################################################
		# Finner ut av rotasjonen til polarizator
		MC1R=MC1Rold
		MC2R=MC2Rold
		MC3R=MC3Rold
		THETA=thetaold
		# if rot==1:

		############################################################################
		# Finner ut av rotasjonen til polarizator
		InMatrisesW=numpy.vstack([MC1,C1W,MC2,C2W,MC3,C3W])
		InMatrisesA=numpy.vstack([MC1,C1A,MC2,C2A,MC3,C3A])

		#options = optimset('Display','off','LargeScale','on','MaxFunEvals',8000,'TolX',1e-15)
		#options = optimset('Display','off','LevenbergMarquardt','on','LargeScale','off','MaxFunEvals',8000,'TolX',1e-15);
		#options = optimset('Display','off','lsqnonneg','on','LargeScale','off','MaxFunEvals',8000,'TolX',1e-15);

		if opt==0:
		  THETA=THETA0
		elif opt==1:
		  theta1=THETA0[0]
		  y0=numpy.array([THETA0[1], THETA0[2]])
		  #       [y1,y2,FinalEigenvalueRatio]=fminegen(InMatrisesW,InMatrisesA,theta1,y0);
		  #       Lars's fminegen har jeg ikke funnet. Kanskje paa NIR MMI maskinen?
		  #       THETA=[theta1,y1,y2];
		  y = scop.fmin(self.FindEigenvalueRatio4forAandW2,y0,args=(InMatrisesW,InMatrisesA,theta1),xtol=1e-15)
		  THETA=[theta1,y[0],y[1]]
		else:
		  pass

		MC1R=self.MuellerRotation_inline(MC1,THETA[0])
		MC2R=self.MuellerRotation_inline(MC2,THETA[1])
		MC3R=self.MuellerRotation_inline(MC3,THETA[2])
		# end

		return MC1R,MC2R,THETA,MC3R,TAU,PSIM,DELTAM,tauPol
  

  def sortEig(self,Ein):
    
    def is_real(val):
      if numpy.isreal(val)==True:
				return 1
      else:
				return 0
      
    Ein=numpy.sort(Ein)[::-1]
    # Sorterer egenverdiene
    antallimag=is_real(Ein[0])+is_real(Ein[1])+is_real(Ein[2])+is_real(Ein[3])
    # NumReal=sum(imag(Ein)==0);
    Es=numpy.zeros(4)+1j*numpy.zeros(4)
    if antallimag==2:
      j=0
      k=2
      for i in range(4):
				if numpy.isreal(Ein[i]):
				  Es[j]=Ein[i]
				  j=j+1
				else:
				  Es[k]=Ein[i]
				  k=k+1
    else:
      Ein_imag_abs=numpy.abs(numpy.imag(Ein))
      pos = numpy.argsort(Ein_imag_abs)
      Es[0]=Ein[pos[0]]
      Es[1]=Ein[pos[1]]
      Es[2]=Ein[pos[2]]
      Es[3]=Ein[pos[3]]
    
    Es[2:4]=numpy.sort(Es[2:4])
    # [V2 pos]=sort(real(Es(3:4)));
    # Es2(3)=Es(pos(1));
    # Es2(4)=Es(pos(2));
    Es[0:2]=numpy.sort(Es[0:2])[::-1]
    
    return Es

  def Mueller_Matrix_ppret(self,tau,psi,delta,mode):
    # M=Mueller_Matrix_diatonator(tau,psi,delta)
    # Returnes the mueller matrix for a retarder with beta phase between fast axis and slow axis 
    # Frantz Stabo-Eeg
    # M=tau*0.5*[1,-cos(2*psi),0,0;-cos(2*psi),1,0,0;0,0,sin(2*psi)*cos(delta),sin(2*psi)*sin(delta);0,0,-sin(2*psi)*sin(delta),sin(2*psi)*cos(delta)];

    #Jarle 200407, factor 0.5 removed
    #230407, mode added.
    #if nargin==3:
    #  mode = 'r'

    if mode=='r':
      tr=-1
    elif mode=='t':
      tr=1
    else:
      tr=-1
	  
    M=tau*numpy.array([[1,tr*numpy.cos(2*psi),0,0],[tr*numpy.cos(2*psi),1,0,0],
		       [0,0,numpy.sin(2*psi)*numpy.cos(delta),numpy.sin(2*psi)*numpy.sin(delta)],
		       [0,0,-numpy.sin(2*psi)*numpy.sin(delta),numpy.sin(2*psi)*numpy.cos(delta)]])

    return M


  def MuellerRotation_inline(self,M,theta):
  
    M = numpy.dot(numpy.dot(self.Mueller_rotator(-theta),M),self.Mueller_rotator(theta))
    
    return M


  def Mueller_rotator(self,theta):
  
    M = numpy.array([[1,0,0,0], [0, numpy.cos(2*theta), numpy.sin(2*theta), 0],
										 [0, -numpy.sin(2*theta), numpy.cos(2*theta), 0], [0,0,0,1]])

    return M


  def Mueller_Matrix_Rotate(self,M,theta):
    # Mueller_Matrix_Rotate(M,theta) 
    # Calculates the rotated Mueller matrix M, rotated by an angle theata
    # Frantz Stabo-Eeg
    M_P=numpy.array([[1,0,0,0],[0,numpy.cos(2*theta),-numpy.sin(2*theta),0],
										 [0,numpy.sin(2*theta),numpy.cos(2*theta),0],[0,0,0,1]])
    M_N=numpy.array([[1,0,0,0],[0,numpy.cos(2*theta),numpy.sin(2*theta),0],
										 [0,-numpy.sin(2*theta),numpy.cos(2*theta),0],[0,0,0,1]])
    M_theta=numpy.dot(numpy.dot(M_P,M),M_N)
    
    return M_theta


  def MuellerMatrix_depolIndex(self,M):
  
    # function [Pd]=MuellerMatrix_depolIndex(M)
    # Calculates the depolarization index Pd of a Mueller matrix M.
    # J. J. Gil and E. Bernabeu, Journal of Modern Optics 33, 185 (1986).
    # Note that depolarization index is not allways equvivalent to the
    # geometrical average of the degree of polarization
    # R. A. Chipman, Appl. Opt. 44, 2490 (2005).
    #Pd=sqrt(-M(1,1)^2)/(3*M(1,1)^2));
    Pd=numpy.sqrt(numpy.sum(numpy.sum(numpy.square(M)))-M[0,0]**2)/(numpy.sqrt(3)*M[0,0]) #Corrected 2007.11.07
    
    # Alternativley can the polindex be calculated from the eigenvalues
    # H=MullerCoherencyMatrixConversion(M);
    # # sorting the eigenvalues
    # [W D]=eig(H);
    # [lambda]=[D(1,1), D(2,2), D(3,3),D(4,4)];
    # [lambda2 sortI]=sort(abs(lambda),'descend');
    # D2=zeros(4,4);
    # for k=1:4
    #     W2(:,k)=W(:,sortI(k));
    #     D2(k,k)=lambda(sortI(k));
    #     P(k)=lambda2(k)/sum(lambda2);
    # end
    # 
    # Pd2=sqrt(1/3*(4*sum(P.^2)-1));
    
    return Pd


  def matrixFilteringCloude2(self,M):
  
    # function [Mf dBNoise DeltaM DeltaH]=matrixFilteringCloude2(M)
    # By Frantz Stabo-Eeg last updated 2007.09.03
    # Mf physical relizable filterd matix
    # dBNoise eigenvalue ratio of positive over negative egienvaluse of the
    # coherency matrix
    # DeltaM=norm(M-Mf,'fro');
    # References
    # Opt Eng vol 34 no 6 p1599 (1995), by Shane R Cloude 
    # Cloude SPIE vol. 1166  (1989)

    DeltaM=0
    ###########################################################################
    # Calculation of the Systems Coherency matrix H
    ###########################################################################
    # H=MullerCoherencyMatrixConversion(M);
    H=self.coherencyConversion(M)
    W2=numpy.zeros((4,4))+1j*numpy.zeros((4,4))
    # sorting the eigen values
    D,W = numpy.linalg.eig(H)
    sortI=numpy.argsort(numpy.abs(D))[::-1]
    D2=numpy.zeros((4,4))+1j*numpy.zeros((4,4))
    for k in range(4):
      W2[:,k]=W[:,sortI[k]]
      D2[k,k]=D[sortI[k]]
    ###########################################################################
    #  Noise filtering of the coherency matrix and entrophy  from Cloude SPIE vol. 1166
    #  (1989)
    #  Tested with values from  from Cloude SPIE vol. 1166 (1989)
    #  ok
    lambdap=0+1j*0
    lambdan=0+1j*0
    for k in range(4):
      if D2[k,k]<0:
				lambdan=D2[k,k]+lambdan
				D2[k,k]=0
      else:
				lambdap=D2[k,k]+lambdap
	  
    dBfidelity=-10*numpy.log10(lambdap/numpy.abs(lambdan)) # i dB lagt til 6. mars
    H2=numpy.dot(numpy.dot(W2,D2),numpy.conj(W2.T))
    DeltaH=numpy.linalg.norm(H-H2)          # Evaluation of measurements uncertainties

    ###########################################################################
    ###########################################################################

    #  Transforming back to filtered Mueller-Jones Matrix 
    #  J.Phys Appl. Phys 29 p34-38 (1996)
    Mf=numpy.real(self.coherencyConversion(H2))
    # Mf=real(MullerCoherencyMatrixConversion(H2));
    Mf=Mf/Mf[0,0]
    # DeltaM=norm(M-Mf,'fro');

    return Mf, dBfidelity, DeltaM, DeltaH


  def coherencyConversion(self,M):
    # pauli=zeros(2,2,4);
    # pauli(:,:,1)=[1,0;0,1];
    # pauli(:,:,2)=[1,0;0,-1];
    # pauli(:,:,3)=[0,1;1,0];
    # pauli(:,:,4)=[0,-1i;1i,0];
    # 
    # H=zeros(4,4);
    # 
    # for k=1:4
    #     for j=1:4
    #         H=H+(0.5*M(k,j)*kron(squeeze(pauli(:,:,k)),conj(squeeze(pauli(:,:,j)))));
    #     end
    # end

    # for k=1:4
    #     for j=1:4
    #         kron(squeeze(pauli(:,:,k)),conj(squeeze(pauli(:,:,j))))
    #     end
    # end
    ##
    H=numpy.zeros((4,4))+1j*numpy.zeros((4,4))
    eta=numpy.zeros((16,4,4))+1j*numpy.zeros((16,4,4))
    
    eta[0,:,:]=numpy.array([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])
    eta[1,:,:]=numpy.array([[0,1,0,0],[1,0,0,0],[0,0,0,1j],[0,0,-1j,0]])
    eta[2,:,:]=numpy.array([[0,0,1,0],[0,0,0,-1j],[1,0,0,0,],[0,1j,0,0]])
    eta[3,:,:]=numpy.array([[0,0,0,1],[0,0,1j,0],[0,-1j,0,0],[1,0,0,0]])
    eta[4,:,:]=numpy.array([[0,1,0,0,],[1,0,0,0,],[0,0,0,-1j],[0,0,1j,0,]])
    eta[5,:,:]=numpy.array([[1,0,0,0],[0,1,0,0],[0,0,-1,0],[0,0,0,-1]])
    eta[6,:,:]=numpy.array([[0,0,0,-1j],[0,0,1,0],[0,1,0,0],[1j,0,0,0]])
    eta[7,:,:]=numpy.array([[0,0,1j,0],[0,0,0,1],[-1j,0,0,0],[0,1,0,0]])
    eta[8,:,:]=numpy.array([[0,0,1,0],[0,0,0,1j],[1,0,0,0],[0,-1j,0,0]])
    eta[9,:,:]=numpy.array([[0,0,0,1j],[0,0,1,0],[0,1,0,0],[-1j,0,0,0]])
    eta[10,:,:]=numpy.array([[1,0,0,0],[0,-1,0,0],[0,0,1,0],[0,0,0,-1]])
    eta[11,:,:]=numpy.array([[0,-1j,0,0],[1j,0,0,0],[0,0,0,1],[0,0,1,0]])
    eta[12,:,:]=numpy.array([[0,0,0,1],[0,0,-1j,0],[0,1j,0,0],[1,0,0,0]])
    eta[13,:,:]=numpy.array([[0,0,-1j,0],[0,0,0,1],[1j,0,0,0],[0,1,0,0]])
    eta[14,:,:]=numpy.array([[0,1j,0,0],[-1j,0,0,0],[0,0,0,1],[0,0,1,0]])
    eta[15,:,:]=numpy.array([[1,0,0,0],[0,-1,0,0],[0,0,-1,0],[0,0,0,1]])

    for i in range(4):
      for j in range(4):
				H=H+0.5*M[i,j]*eta[4*i+j,:,:]
  
    return H
  

  def return_calib_params(self,B0,B1,B2,B3,THETA0):

		#addpath(genpath('C:\MatlabMM-hg'));
		condB0 = numpy.linalg.cond(B0) # sjekker Condition number direkt paa B0?

		MC1R=numpy.zeros((4,4))
		MC2R=numpy.zeros((4,4))
		MC3R=numpy.zeros((4,4))
		VEC_THETAM = numpy.zeros(3)

		C1W = numpy.linalg.solve(B0,B1)
		C2W = numpy.linalg.solve(B0,B2)
		C3W = numpy.linalg.solve(B0,B3)

		C1A = numpy.linalg.solve(B0.T,B1.T).T
		C2A = numpy.linalg.solve(B0.T,B2.T).T
		C3A = numpy.linalg.solve(B0.T,B3.T).T

		opt=1

		MC1R,MC2R,THETA,MC3R,TAU,PSIM,DELTAM,tauPol=self.EVCSamplePropertiesForAandW_MK2(C1W,C2W,C3W,C1A,C2A,C3A,THETA0*numpy.pi/180,opt,'t',MC1R,MC2R,MC3R,VEC_THETAM)

		#[MC1Rold,MC2Rold,THETAMold,MC3Rold,TAUold,PSIMold,DELTAMold,tauPolold]=EVCSamplePropertiesForAandW_LM(C1W,C2W,C3W,C1A,C2A,C3A,THETA0,opt,'t');
		# Final Calculation

		H1W=self.Changebasis3(MC1R,C1W) # Independent of A
		H2W=self.Changebasis3(MC2R,C2W)
		H3W=self.Changebasis3(MC3R,C3W)

		KW = numpy.dot(H1W.T,H1W)+numpy.dot(H2W.T,H2W)+numpy.dot(H3W.T,H3W)
		
		EIGKW, VectorEig = numpy.linalg.eig(KW)
		pos = EIGKW.argmin()
		EIGKW=numpy.sort(EIGKW)
		errorKW=numpy.sqrt(EIGKW[0]/EIGKW[1])

		n,m = B0.shape
		W = self.ConvertNxMby1To4byMMatrix(VectorEig[:,pos],m)
		condW = numpy.linalg.cond(W)

		# check condition number. If it's equal to 1000 or larger, we can consider
		# for sure that the matrix is singular. The user will be notified later
		# about the issue. tb.
		if condW<1000:
		  W=numpy.real(W/W[0,0])
		  AI=numpy.linalg.solve(W.T,B0.T).T

		# doing the same for A; 311007 tB
		H1A=self.changebasis3A(MC1R,C1A) # Independent of W
		H2A=self.changebasis3A(MC2R,C2A)
		H3A=self.changebasis3A(MC3R,C3A)

		KA = numpy.dot(H1A.T,H1A)+numpy.dot(H2A.T,H2A)+numpy.dot(H3A.T,H3A)
		
		EIGKA, VectorEig = numpy.linalg.eig(KA)
		pos = EIGKA.argmin()
		EIGKA=numpy.sort(EIGKA)
		errorKA=numpy.sqrt(EIGKA[0]/EIGKA[1])
		
		n,m = B0.shape
		A=self.ConvertNxMby1To4byMMatrix(VectorEig[:,pos],m)
		condA = numpy.linalg.cond(A)
		
		# check condition number. If it's equal to 1000 or larger, we can consider
		# for sure that the matrix is singular. The user will be notified later
		# about the issue. tb.
		if condA<1000:
		  A=numpy.real(A/A[0,0])
		  WI=numpy.linalg.solve(A,B0)

		scaling=numpy.linalg.norm(B0,2)/numpy.linalg.norm(numpy.dot(A,W),2) # Ny skalering FSE
		
		#print "scaling", scaling
		
		A=A*numpy.sqrt(scaling)
		W=W*numpy.sqrt(scaling)

		###############################################################################

		errorK = (errorKW + errorKA)/2 # (use some mean error)
		#THETAM*180/pi
		#condB0=condnr(B0)
		#condW=condnr(W);
		#condA=condnr(A);

		# These are now in principle converting to old variable names

		M0 = numpy.linalg.solve(W.T,numpy.linalg.solve(A,B0).T).T
		M1 = numpy.linalg.solve(W.T,numpy.linalg.solve(A,B1).T).T
		M2 = numpy.linalg.solve(W.T,numpy.linalg.solve(A,B2).T).T
		M3 = numpy.linalg.solve(W.T,numpy.linalg.solve(A,B3).T).T
		THETAM=THETA
		#THETAM=pi*THETA/180;

		Mf0, Entrophy0, DeltaM, DeltaH = self.matrixFilteringCloude2(M0)
		Mf1, Entrophy1, DeltaM, DeltaH = self.matrixFilteringCloude2(M1)
		Mf2, Entrophy2, DeltaM, DeltaH = self.matrixFilteringCloude2(M2)
		Mf3, Entrophy3, DeltaM, DeltaH = self.matrixFilteringCloude2(M3)
		M2ut=self.Mueller_Matrix_Rotate(M2,-THETAM[1])
		M3ut=self.Mueller_Matrix_Rotate(M3,-THETAM[2])

		Pd0 = self.MuellerMatrix_depolIndex(Mf0)
		Pd1 = self.MuellerMatrix_depolIndex(Mf1)
		Pd2 = self.MuellerMatrix_depolIndex(Mf2)
		Pd3 = self.MuellerMatrix_depolIndex(Mf3)
		
		return A, W, [condB0,condA,condW], THETAM, numpy.array([M0,M1,M2,M3]), [Pd0,Pd1,Pd2,Pd3]


  def measure_single_Matrix(self,Bsingle,A,W):
  
    #addpath('Y:\Phd\Lab maalinger\EVC Mueller\#MullerMatrixMaalinger\Analyse av #Maaleoppsett');
    #addpath('Y:\Phd\Matlab\polardecompostion');
    Msingle = numpy.linalg.solve(W.T,numpy.linalg.solve(A,Bsingle).T).T
    Mf, Entrophy, DeltaM, DeltaH = self.matrixFilteringCloude2(Msingle)
    Pd = self.MuellerMatrix_depolIndex(Mf)
    
    return Msingle, Mf, Entrophy, DeltaM, DeltaH, Pd



def test():
  
  sf=Scatterometer_funksjoner()
  B=numpy.array([[[4.1255,0.6310,6.7022,6.7677],[0.8191,7.5681,4.3100,7.0470],[3.7190,4.1148,7.6192,0.5092],[7.3032,3.5817,0.5545,4.0887]],
								 [[0.2010,0.1997,0.8529,0.5011],[1.0802,6.5608,4.4944,2.6172],[0.8551,5.4221,3.7119,2.1429],[0.2653,1.5821,1.0219,0.6140]],
								 [[5.0157,1.0076,1.7487,5.0128],[1.6775,0.3586,0.5522,1.6555],[1.1441,0.2244,0.3533,1.0905],[4.7943,1.0330,1.6344,4.8927]],
								 [[3.1867,2.6811,5.9539,0.5649],[3.0612,5.9736,1.4207,3.2600],[6.3661,1.2321,1.6104,3.5465],[0.8754,2.0146,3.7022,5.5458]]])
  THETA0=numpy.array([0,85,55])
  A, W, cond, THETAM, M, Pd = sf.return_calib_params(B[0,:,:],B[1,:,:],B[2,:,:],B[3,:,:],THETA0)
  
  print "A:", A
  print "W:", W 
  print "cond:", cond
  print "M0:", M[0]
  print "M1:", M[1]
  print "M2:", M[2]
  print "M3:", M[3]
  
  print "Pd0:", Pd[0]
  print "Pd1:", Pd[1]
  print "Pd2:", Pd[2]
  print "Pd3:", Pd[3]
  
  print "THETAM", THETAM
  
  
  Bsingle=numpy.random.rand(4,4)
  Msingle, Mf, Entrophy, DeltaM, DeltaH, Pd = sf.measure_single_Matrix(Bsingle,A,W)
  print "Msingle:", Msingle
  print "Entrophy:", Entrophy
  print "Pd:", Pd

if __name__=="__main__":
  
  test()