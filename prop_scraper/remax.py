import requests
import json
import pandas as pd
import time
import numpy as np
from datetime import datetime


class REMAX:

    def __init__(self):
        self.data = None

    def get_property_batch(self, take=500, pages=np.inf):
        url = 'https://remax-malta.com/api/properties?Residential=true&Commercial=false&ForSale=true&ForRent=true&page={}&Take={}'
        #url = 'https://remax-malta.com/api/properties?Residential=true&Commercial=false&ForSale=true&ForRent=false&page={}&Take={}'
        curr_page = 1
        n_loaded = 0
        tsr = 1 # will be overwritten
        while n_loaded < tsr and curr_page <= pages:
            res = requests.get(url.format(curr_page, take))
            res = json.loads(res.text)['data']
            tsr = res['TotalSearchResults']
            n_loaded += res['NumberOfReturnedListings']
            df = pd.DataFrame(res['Properties'])
            metadata = {
                'curr_page': curr_page,
                'tot_search_res': tsr,
                'n_loaded': n_loaded
            }
            if len(df) == 0: break
            yield metadata, df 
            curr_page += 1

    def clean(self):
        '''
        clean data
        '''
        outdoor_types = [
            'Agriculture Land',
            'Land',
            'Plot',
            'Site',
        ]
        indoor_types = [
            'Apartment',
            'Garage (Residential)',
        ]
        df = self.data
        df = df[df.Price!='POR']
        df = df[df.TransactionType == 'For Sale']

        df.TotalIntArea = np.where(
            (df.TotalIntArea==0)&(df.TotalExtArea==0)&(~df.PropertyType.isin(outdoor_types)), 
            df.TotalSqm,
            df.TotalIntArea
        )

        df.TotalExtArea = np.where(
            (df.TotalIntArea==0)&(df.TotalExtArea==0)&(df.PropertyType.isin(outdoor_types)), 
            df.TotalSqm,
            df.TotalExtArea
        )

        df.TotalExtArea = np.where(
            (df.TotalIntArea>0)&(df.TotalExtArea==0)&(df.TotalSqm>0), 
            df.TotalSqm-df.TotalIntArea,
            df.TotalExtArea
        )

        df.TotalIntArea = np.where(
            (df.TotalIntArea==0)&(df.TotalExtArea>0)&(df.TotalSqm>0), 
            df.TotalSqm-df.TotalExtArea,
            df.TotalIntArea
        )

        df.TotalSqm = np.where(
            (df.TotalIntArea>0)&(df.TotalExtArea>0)&(df.TotalSqm==0), 
            df.TotalIntArea+df.TotalExtArea,
            df.TotalSqm
        )

        df.TotalSqm = np.where(
            (df.TotalSqm-df.TotalIntArea-df.TotalExtArea)<40, 
            df.TotalIntArea+df.TotalExtArea, 
            df.TotalSqm
        )

        df = df[(df.TotalSqm-df.TotalIntArea-df.TotalExtArea)==0]

        self.data = df # technically not needed
        return self

    def get_data(self, batch_size=500, pages=np.inf):
        df = pd.DataFrame()
        for metadata, df_batch in self.get_property_batch(batch_size, pages):
            page = metadata['curr_page']
            tot_search_res = metadata['tot_search_res']
            n_loaded = metadata['n_loaded']
            df_batch = df_batch[[
                'MLS', 
                'ContractType', 
                'TransactionType', 
                'Price',
                'PropertyType',
                'Town',
                'Province',
                'TotalRooms',
                'TotalBedrooms',
                'TotalBathrooms',
                'TotalSqm',
                'TotalIntArea',
                'TotalExtArea',
                'InsertionDate',
                'LastModified',
            ]]

            print(f"Page {page}: {n_loaded}/{tot_search_res}", end='\r')
            df = pd.concat([df, df_batch])
        self.data = df
        return self

    def save(self, fn=None):
        today = str(datetime.now().date())
        fn = fn if fn is not None else f'remax_properties_{today}.csv'
        self.data.to_csv(fn)
        return self


if __name__ == '__main__':
    remax = REMAX()
    remax.get_data(2000).clean().save()
    print(remax.data)

