import statsmodels.api as sm
import pickle
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
import pandas as pd
import argparse
import numpy as np
import itertools
from math import log, exp


class ANOVA:

    def __init__(self, df, log_trans=False, cross=False, categ=None, covar=None):
        '''
        TODO: option to apply PCA on data first
        '''
        categ = [f'C({c})' for c in categ]
        features = categ+covar
        if cross: 
            features += ['*'.join(pair) for pair in itertools.combinations(features, 2)]
        self.features = features
        self.categ = categ
        self.covar = covar
        if log_trans: df.Price = df.Price.apply(log)
        self.log_trans = log_trans
        self.df = df

    def PCA(self, cutoff=0.99):
        '''
        Chooses only most relevant regressors.
        Finds eigenvalues of data matric, sort them 
        and choose largest 2 eigvalues.
        TODO: choose vars whose cumsum of eigenvals are < cutoff
        '''
        covariates = 'bedrooms area int_area ext_area'.split()
        data = self.df[covariates]
        data = data.sub(data.mean()).div(data.std())
        vcv = data.cov()
        val, vec = np.linalg.eigh(vcv)
        val = [v/sum(val) for v in val]
        
        feature = vec[:,2:] # choose 2 appropraitely!!

        data1 = feat.T@data.T

        return data1

    def get_model_eqn(self, features=None):
        '''
        creates R-style formula to input in ANOVA
        '''
        if not features: features = self.features
        return 'Price ~ ' + '+'.join(self.features)

    def fit(self, suppress_output=False):
        return self._fit(self.features)

    def _fit(self, features, suppress_output=False):
        '''
        Apply ANOVA on all columns with pairwise interactions.
        Check which p-values are greater than threshold and remove 
        worst-offending one. Repeat process until no offenders
        '''

        model_eqn = self.get_model_eqn(features)
        print(model_eqn)

        if(model_eqn==0): 
            print('No significant variable')
            return

        #apply anova
        lm = ols(model_eqn, data=self.df).fit()
        table = sm.stats.anova_lm(lm, typ=2)
        p_vals = table['PR(>F)']

        print(lm.summary())
        print(table)

        #value and index of largest p value
        max_p = np.max(p_vals)
        argmax_p = np.argmax(p_vals)

        if(max_p>0.05):
            #removes insignificant variables with largest p val
            #if(argmax_p<len(categ)):
            #    del categ[argmax_p]
            #else:
            #    del covar[argmax_p-len(categ)]
            del features[argmax_p]

            #performs analysis without the insignificant variable
            self._fit(features, suppress_output)
        else:
            #all remaining variables significant, so output info
            coefficients = lm.params
            r = lm.rsquared_adj
            adj_r = lm.rsquared
            if not suppress_output:
                print('Adjusted R-Squared: ' + str(adj_r))
                print(coefficients)
                print(p_vals)
            self.lm = lm

    def predict(self, X):
        preds = self.lm.get_prediction(X).predicted_mean
        return [exp(x) for x in preds] if self.log_trans else preds

    def __str__(self):
        return self.lm.summary().as_text()

def save(obj, fn='remax_model.pkl'):
    with open(fn, 'wb') as handle:
        pickle.dump(obj, handle)

def get_model():
    from data import remax as df

    categ = [
        'PropertyType',
        'Town',
        'Province',
        'TransactionType',
    ]

    covar = [
        #'TotalRooms', 
        'TotalBedrooms', 
        #'TotalBathrooms', 
        #'TotalSqm', 
        #'TotalIntArea', 
        #'TotalExtArea',
    ]

    model = ANOVA(
        df.copy(), 
        log_trans=True, 
        categ=categ, 
        covar=covar, 
        cross=False
    )
    model.fit()
    return model

if __name__=='__main__':
    from sklearn.metrics import mean_squared_error as mse
    model = get_model()
    df['pred'] = model.predict(df)
    save(model)
    print(f'RMSE = {mse(df.pred, df.Price)**0.5}')

