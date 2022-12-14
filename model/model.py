import pandas as pd
from catboost import CatBoostRegressor, Pool

  
class RFR(CatBoostRegressor):

    def __init__(self, data_trans=(None, None), **kwargs):
        '''
        data_trans: tuple with first element being the transformation of the data and
        the second element its inverse. No transformation by default
        '''
        if data_trans == (None, None):
            self.data_trans = (lambda x: x, lambda x: x)
        else:
            self.data_trans = data_trans

        super().__init__(
            iterations=100,
            loss_function='RMSE',
            learning_rate=0.5,
            depth=10,
            task_type='CPU',
            random_state=1,
            verbose=False
        )

    def _transform(self, df):
        categ = ['PropertyType', 'Town', 'Province']
        redundant = ['MLS', 'ContractType', 'TransactionType', 'Price', 'InsertionDate', 'LastModified']

        x = df.drop(redundant, axis=1)

        if 'Price' in df:
            y = df.Price.apply(self.data_trans[0])
            return Pool(x, y, cat_features=categ)
        else:
            return Pool(x, cat_features=categ)

    def my_train(self, df):
        pool_train = self._transform(df)
        self.fit(pool_train)

    def my_predict(self, df):
        pool_pred = self._transform(df)
        preds = self.predict(pool_pred)
        return [self.data_trans[1](x) for x in preds] # inverse of log-transform


if __name__=='__main__':
    import matplotlib.pyplot as plt
    from sklearn.metrics import mean_squared_error as mse
    from IPython import embed
    from data import remax
    from math import log, exp, sqrt

    model = RFR() # OR RFR(data_trans=(log, exp))
    model.my_train(remax)
    remax['Pred'] = model.my_predict(remax)

    print(f'RMSE = {sqrt(mse(remax.Price, remax.Pred))}')
    plt.scatter(remax.Price, remax.Pred)
    plt.show()

    embed()
