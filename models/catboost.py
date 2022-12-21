import pandas as pd
from catboost import CatBoostRegressor, Pool
import pickle 

  
class RFR(CatBoostRegressor):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _transform(self, df):
        categ = ['PropertyType', 'Town', 'Province']
        redundant = ['MLS', 'ContractType', 'TransactionType', 'Price', 'InsertionDate', 'LastModified']
        features = self.feature_names_

        x = df.drop(redundant, axis=1, errors='ignore')
        if features is not None:
        #if not self.is_fitted():
            unused_features = set(features).difference(set(x.columns))
            if len(unused_features):
                df_unused = pd.DataFrame('#N/A', columns=unused_features, index=[0])
                x = pd.concat([df_unused, x], axis=1)

        if 'Price' in df:
            y = df.Price
            return Pool(x, y, cat_features=categ)
        else:
            return Pool(x, cat_features=categ)

    #TODO: decorate following functions instead of doing this
    def my_train(self, df):
        pool_train = self._transform(df)
        self.fit(pool_train)

    def my_predict(self, df):
        pool_pred = self._transform(df)
        preds = self.predict(pool_pred)
        return preds
        
    def my_grid_search(self, grid, df):
        pool_pred = self._transform(df)
        return self.grid_search(grid, pool_pred)

    def my_score(self, df):
        pool_pred = self._transform(df)
        return self.score(pool_pred)

def save(obj, fn='remax_model.pkl'):
    with open(fn, 'wb') as handle:
        pickle.dump(obj, handle)


if __name__=='__main__':
    import matplotlib.pyplot as plt
    from sklearn.metrics import mean_squared_error as mse
    from IPython import embed
    from data import remax
    from math import log, exp, sqrt

    grid = {'iterations': [100, 150, 200],
        'learning_rate': [0.03, 0.1],
        'depth': [2, 4, 6, 8],
        'l2_leaf_reg': [0.2, 0.5, 1, 3]}

    params = {
        'depth': 6, 
        'l2_leaf_reg': 3, 
        'iterations': 10000, 
        'learning_rate': 0.1,
        'random_state': 1,
    }
    model = RFR(**params)

    model.my_train(remax)
    #res = model.my_grid_search(grid, remax) # find best params
    score = model.my_score(remax)
    print(f'R2 = {score}%')
    breakpoint()

    save(model)
    #model.save_model()
    remax['Pred'] = model.my_predict(remax)

    print(f'RMSE = {sqrt(mse(remax.Price, remax.Pred))}')
    plt.scatter(remax.Price, remax.Pred)
    plt.show()

    embed()
