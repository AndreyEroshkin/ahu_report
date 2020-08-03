#!/usr/bin/env python
# coding: utf-8

# In[3]:


import pandas as pd
import os
import numpy as np


# In[4]:


def read_price():
    fn = os.path.join('.', 'ext_data', 'price.xlsx')
    price_df = pd.read_excel(fn)
    price_df = price_df.dropna(how='all')
    return price_df


# In[5]:


def filter_cost(area, filter_type):
    filters_data = {
                    'ФВКом-F7-96': [-80, 2850],
                    'ФВКом-F9-96': [-87, 2955],
                    'ФВКом-G4-96': [116, 1361],
                    'ФВКас-I-G4-48': [114, 1302],
                    'ФВКасIII-G4-48': [329, 1598],
                    'ФВКасIII-G4-96': [500, 1800],  #  Recalculate it!!!!
                    'ФВК-F7-300': [536, 14982],
                    'ФВК-F9-300': [536, 14982],
                    }
    coef1, coef2 = filters_data[filter_type]
    return coef2*area + coef1


# In[6]:


def heat_exchanger_cost(air_flow, heat_exchanger_type):
    data = {'ИФн-э': (6.405136472279891, 8500.643416747705),
            'КВн-э': (3.200178135561211, 7402.262377605983),
            'КФн-э': (7.8819290125705574, 7160.325684730837)}
    coef1, coef2 = data[heat_exchanger_type]
    return coef1 * air_flow + coef2


# In[7]:


def electric_heater_cost(power, model):
    data = {'ТЭНы из нержавеющей стали': (1.5, 7000),
            'Стальные ТЭНы': (1, 7000)}
    coef1, coef2 = data[model]
    return coef1 * power + coef2


# In[18]:


def silencer_cost(area, splitter_num, model):
    data = {'pure': 5000,
            'pool': 2500,
            'basic': 2500}
    return area * splitter_num * data[model]


# In[19]:


def calc_price(bom_df):
    price_df = read_price()
    bom_df.loc[bom_df['model'].isna(),'model'] = bom_df.index[bom_df['model'].isna()].values
    df = bom_df.reset_index().merge(price_df,
                               how="left",
                               on='model',
                               sort=False,
                               suffixes=('', '_y')).set_index('index')
    df.drop(df.filter(regex='_y$').columns.tolist(), axis=1, inplace=True)
    # calculate filters price
    df.loc[df.index == 'Фильтр', 'price'] = df.loc[df.index == 'Фильтр', :].apply(
        lambda x: filter_cost(x['a'] * x['b'] * 1e-6, x['model']), axis=1)
    # calculate heat exchangers  price
    df.loc[df['model'].isin(['ИФн-э', 'КВн-э', 'КФн-э']), 'price'] = df.loc[df['model'].isin(['ИФн-э', 'КВн-э', 'КФн-э']), :].apply(
        lambda x: heat_exchanger_cost(x['air_flow'], x['model']), axis=1)
    # calculate electric heater price
    df.loc[df.index == 'Электрический нагреватель', 'price'] = df.loc[df.index == 'Электрический нагреватель', :].apply(
        lambda x: electric_heater_cost(x['power'], x['model']), axis=1)
    # calculate silencer  price
    df.loc[df.index == 'Шумоглушитель', 'price'] = df.loc[df.index == 'Шумоглушитель', :].apply(
        lambda x: silencer_cost(x['a'] * x['b'] * 1e-6, x['splitter_num'], x['model']), axis=1)
    
    df['cost'] = df['qty'] * df['price']
    return df


# In[20]:


# bom_df = pd.read_excel('./output/test/П1.xlsx', index_col=0)


# In[21]:


# cost_df = calc_price(bom_df)


# In[22]:


# cost_df


# In[ ]:




