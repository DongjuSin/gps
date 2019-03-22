""" This file defines linear regression with an arbitrary prior. """
import numpy as np

from gps.algorithm.dynamics.dynamics import Dynamics
from gps.algorithm.algorithm_utils import gauss_fit_joint_prior


class DynamicsLRPrior(Dynamics):
    """ Dynamics with linear regression, with arbitrary prior. """
    def __init__(self, hyperparams):
        Dynamics.__init__(self, hyperparams)
        self.Fm = None
        self.fv = None
        self.dyn_covar = None
        self.prior = \
                self._hyperparams['prior']['type'](self._hyperparams['prior'])

    def update_prior(self, samples):
        """ Update dynamics prior. """
        X = samples.get_X()
        U = samples.get_U()
        self.prior.update(X, U)

    def get_prior(self):
        """ Return the dynamics prior. """
        return self.prior

    #TODO: Merge this with DynamicsLR.fit - lots of duplicated code.
    def fit(self, X, U):
        """ Fit dynamics. """
        N, T, dX = X.shape
        dU = U.shape[2]

        if N == 1:
            raise ValueError("Cannot fit dynamics on 1 sample")

        self.Fm = np.zeros([T, dX, dX+dU])
        self.fv = np.zeros([T, dX])
        self.dyn_covar = np.zeros([T, dX, dX])

        it = slice(dX+dU)
        ip = slice(dX+dU, dX+dU+dX)
        # Fit dynamics with least squares regression.
        dwts = (1.0 / N) * np.ones(N)
        for t in range(T - 1):
            Ys = np.c_[X[:, t, :], U[:, t, :], X[:, t+1, :]]
            # Obtain Normal-inverse-Wishart prior.
            mu0, Phi, mm, n0 = self.prior.eval(dX, dU, Ys)
            sig_reg = np.zeros((dX+dU+dX, dX+dU+dX))
            sig_reg[it, it] = self._hyperparams['regularization']
            Fm, fv, dyn_covar = gauss_fit_joint_prior(Ys,
                        mu0, Phi, mm, n0, dwts, dX+dU, dX, sig_reg)
            self.Fm[t, :, :] = Fm
            self.fv[t, :] = fv
            self.dyn_covar[t, :, :] = dyn_covar
        return self.Fm, self.fv, self.dyn_covar
    
    ### This function generated by Dongju 
    def next_state(self, X, U):
        _, T, _ = X.shape
        XU = np.concatenate((X, U), axis=2)
        print('XU.shape: ', XU.shape) # (10,20,97)
        
        XU_init = XU[0,0,:]
        # print('XU_init.shape: ', XU_init.shape) # (97,)
        print('Fm.shape: ', self.Fm.shape) # (20,90,97)
        X_infer = np.zeros((20,90))
        X_infer[0] = XU_init[:90]
        for i in range(1, T-1):
            # X_hat = np.matmul(self.Fm[0,:,:], XU_init) + self.fv[0,:]
            XU_cur = np.concatenate((X_infer[i-1, :], XU[0,i-1,90:]), axis=0)
            X_next = np.matmul(self.Fm[i,:,:], XU_cur) + self.fv[i,:]
            X_infer[i] = X_next
        print(X_next.shape) # (90,1)

        self.plot(X, X_infer)
        
    # plot and compare next states computed from acquired dynamics and whole states in sample
    def plot(self, X, X_infer):
        import matplotlib.pyplot as plt
        T, _ = X.shape
        
        for i in range(7):
            plt.figure()
            plt.plot(range(T), X_infer[:, i], 'ro', label='dynamcis')
            plt.plot(range(T), X[:, i], 'bo', label='sample')
            plt.xlabel("step")
            plt.ylabel("state")
            plt.title("state-step plot")
            plt.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))
            # plt.show()
            
            plt.savefig('/hdd/gps-master/plot_coeff/joint_%d.png' %i)
            
    def next_state(self, X, U):
        _, T, _ = X.shape
        XU = np.concatenate((X, U), axis=2)
        print('XU.shape: ', XU.shape) # (10,20,97)
        
        XU_init = XU[0,0,:]
        # print('XU_init.shape: ', XU_init.shape) # (97,)
        print('Fm.shape: ', self.Fm.shape) # (20,90,97)
        X_infer = np.zeros((20,90))
        X_infer[0] = XU_init[:90]
        # for i in range(T-1):
        for i in range(T-2):
            XU_cur = np.concatenate((X_infer[i, :], XU[0,i,90:]), axis=0)
            X_next = np.matmul(self.Fm[i+1,:,:], XU_cur) + self.fv[i+1,:]
            X_infer[i+1] = X_next
        print(X_next.shape) # (90,1)

        self.plot(X[0,:,:], X_infer)
        
    def next_state2(self, X, U):
        N, T, _ = X.shape
        XU = np.concatenate((X, U), axis=2) # (10,20,97)
        
        for i in range(N):
            XU_init = XU[i,0,:]
            X_infer = np.zeros((10,20,90))
            X_infer[i,0,:] = XU_init[:90]
            for j in range(T-1):
                XU_cur = np.concatenate((X_infer[i,j, :], XU[i,j,90:]), axis=0)
                X_next = np.matmul(self.Fm[j+1,:,:], XU_cur) + self.fv[j+1,:]
                X_infer[j+1] = X_next
        
        self.plot(X, X_infer)
