#!/usr/bin/env python
# coding: utf-8

# In[2]:


from sections import *
import pandas as pd
from CoolProp.HumidAirProp import HAPropsSI
import os


# In[3]:


class Fan (Section):

    def __init__(self, mode='winter', serie = 'basic', motor_type='EC', **kwargs):
        self.mode = mode
        self.serie = serie
        self.motor_type = motor_type
        self.__dict__.update(kwargs)
        self._set_name()
        self.output_dict = {}
        self.bom = {}
        self._read_bom_dict()

    def _set_name(self):
        if not hasattr(self, 'name'):
            self.name = 'Вентилятор'

    def define_geometry(self):
        self.lenght = 900
        self.door = 1

        #  set minimal internal dimensions
        self.min_width = self.fan_plate_size * self.fan_qty + 50
        self.min_height = self.fan_plate_size + 50

        #  set internal margins
        self.mar_width = 0
        self.mar_height = 0

        if not hasattr(self, 'max_velocity'):
            self.max_velocity = 9

    def _select_fan(self):

        df = pd.read_csv(os.path.join('.', 'ext_data', 'fan_matrix.csv'), index_col = 0)

        if hasattr(self, 'article'):
            df = df.loc[df['Каталожный номер'] == self.article, :]
        if hasattr(self, 'motor_type'):
            df = df.loc[df['Тип двигателя'] == self.motor_type, :]
        assert len(df) > 0, f'Нет вентиляторов соответствующих артиклей и типов двигателя'

        assert self.air_in.l <= df['Расход воздуха'].max(), f'Вентилятор на {self.air_in.l} м3/ч отсутствует в базе'
        assert self.p_tot <= df.loc[df['Расход воздуха'] >= self.air_in.l,
                                     'Статическое давление'].max(), \
            f'Вентилятор на {self.air_in.l} м3/ч не обеспечивает {self.p_tot} Па'

        delta_l = df['Расход воздуха'] - self.air_in.l
        delta_p = df['Статическое давление'] - self.p_tot
        delta = []
        for x, y in zip(delta_l, delta_p):
            if (x < 0) or (y < 0):
                delta.append(1e6)
            else:
                delta.append(x + y)
        minimum = min(delta)
        indices = [i for i, v in enumerate(delta) if v == minimum]
        df1 = df.iloc[indices]
        df2 = df1.loc[df1['Ширина'] == df1['Ширина'].min()]
        df2 = df2.loc[df2['Установленная мощность'] == df2['Установленная мощность'].min()]
        fan = df2.iloc[0]
        self.power_nom      = fan['Установленная мощность']
        self.electricity    = fan['Сеть электропитания']
        self.fan_plate_size = fan['Ширина']
        self.fan_depth_size = fan['Глубина']
        self.fan_weight     = fan['Масса изделия']
        self.fan_qty        = fan['Кол-во вентиляторов']
        self.article        = fan['Каталожный номер']
        self.motor_type     = fan['Тип двигателя']

    def calculate(self):
        self._select_fan()
        self.define_geometry()
        self.air_out_calc()

    def prepear_output(self):
        super().prepear_output()
        self.output_dict['Расход воздуха, м³/ч']                         = self.air_in.l
        self.output_dict['Статическое давление вентилятора, Па']         = self.p_tot
        self.output_dict['Давление на сеть, Пa']                         = self.p_net
        if self.fan_qty == 1:
            self.output_dict['Номинальная электрическая мощность, кВт']     = self.power_nom
        else:
            self.output_dict['Номинальная электрическая мощность, кВт']     = f'{self.power_nom}x{self.fan_qty}'
        self.output_dict['Сеть электропитания']                          = self.electricity
        self.output_dict['Тип двигателя']                                = f'{self.motor_type} двигатель'
        if self.fan_qty > 1:
            self.output_dict['Количество вентиляторов одновременно в работе, шт.'] = self.fan_qty

    def air_out_calc(self):
        self.air_out = Air(self.name + ' air out', self.air_in.t, self.air_in.rh, self.air_in.l)

    def prepear_bom(self):
        super().prepear_bom()
        self.bom[self.name] = {'qty': self.fan_qty, 'model': self.article}

    def get_code(self):
        return 'V'


# In[5]:


class Fan_reserved(Fan):


    def _set_name(self):
        if not hasattr(self, 'name'):
            self.name = 'Вентилятор с резервированием 100%'

    def define_geometry(self):
        self.lenght = 1200
        self.door = 1

        #set minimal internal dimensions
        self.min_width  = self.fan_plate_size * 2 + 140
        self.min_height = self.fan_plate_size * self.fan_qty + 100

        #set internal margins
        self.mar_width = 0
        self.mar_height = 0

        if not hasattr(self, 'max_velocity'):
            self.max_velocity = 9

    def prepear_output(self):
        super().prepear_output()
        self.output_dict['Номинальная электрическая мощность, кВт']     = f'{self.power_nom}x{2*self.fan_qty}'

    def prepear_bom(self):
        super().prepear_bom()
        self.bom[self.name] = {'qty': self.fan_qty * 2, 'model': self.article}
        if self.serie == 'pure':
            self.bom['Расходомер'] = {'qty': self.fan_qty * 2, 'model': 'DPT-Flow-2000-D'}
        self.bom['Воздушный клапан реверсивный'] = {'qty': 1, 'model': f'{self.w_int} x {self.h_int}'}
        self.bom['Электропривод'] = {'qty': 1, 'model': 'Siemens'}

    def get_code (self):
        return '2V'


# In[ ]:




