#!/usr/bin/env python
# coding: utf-8

# In[1]:


import math
import numpy as np
from CoolProp.HumidAirProp import HAPropsSI
import time
import locale
import os
import json
locale.setlocale(locale.LC_TIME, "ru_RU.UTF8")  # russian locale for time format


# # Functions

# In[2]:


def pipe_sizing(flow, velocity): #m3/h, m/s
    '''Selecting pipe size with fluid velocity less than velocity'''
    # Сечение, дюймов Наружный диаметр, мм Толщина стенки, мм
    sizes={ "1/4''":   (  6.4,  0.6),
            "3/8''":   (  9.5,  0.7),
            "1/2''":   ( 12.7,  0.9),
            "5/8''":   ( 15.9,  1.02),
            "3/4''":   ( 19.05, 1.02),
            "7/8''":   ( 22.2,  1.1),
            "1 1/8''": ( 28.6,  1.3),
            "1 3/8''": ( 35.0,  1.4),
            "2 1/8''": ( 54.0,  1.78),
            "2 5/8''": ( 66.7,  2.03),
            "3 1/8''": ( 79.4,  2.5),
            "4 1/8''": (104.7,  2.8)}
    for key, value in sizes.items():
        d_ext, wall = value  # mm
        d_int = d_ext - wall * 2  # mm
        area = math.pi * d_int ** 2 / 4  # mm2
        velocity_calc = flow / 3600 / area * 1e6  # m/s
        if velocity_calc < velocity:
            return key


# In[3]:


def pipe_sizing_freon(power, fluid):  # -W, str
    '''Selecting cooper pipe size for freons by capacity'''
    R410a = {5.3: '6.35/12.7',
             7.1: '9.52/12.7',
             10.5: '9.52/19',
             14: '9.52/19',
             16: '9.52/19',
             22: '9.52/22',
             28: '9.52/25',
             35: '12.7/28.6',
             45: '16/32',
             53: '(12.7/25)×2',
             61: '(12.7/25)×2',
             70: '(12.7/25)×2',
             105: '(12.7/25)×2'}
    if fluid == 'R410a':
        for nom_power, pipe_size in R410a.items():
            if nom_power >= - power / 1000:
                return pipe_size
    return 'Блок ККБ не подобран'


# In[4]:


def connection_calc (l, w, h, v_max=6):
    standart = [[100, 100],
                [400, 200],
                [500, 250],
                [500, 300],
                [600, 300],
                [600, 350],
                [700, 400],
                [800, 500],
                [900, 500],
                [1000, 500]]
    v = v_max + 1
    i = 0
    while i < len(standart):
        a, b = standart[i]
        if a < w and b < h:
            v = l / 3600 / (a * b) * 1e6
            if v < v_max:
                return a, b
        else:
            break
        i += 1

    a_b_rate = 1
    step = 100
    while v > v_max:
        if (a == w) and (b == h):
            raise RuntimeError('Невозможно подобрать присоединительный размер')
        if (a < w) and (b < h):
            if b / a > a_b_rate:
                a += step
                a = min(a, w)
            else:
                b += step
                b = min(b, h)

        elif a < w:
            a += step
            a = min(a, w)

        elif b < h:
            b += step
            b = min(b, h)

        v = l / 3600 / (a * b) * 1e6
    return a, b


# In[5]:


def json_read(filename):
    with open(filename) as f_in:
        return(json.load(f_in))


# # Classes

# ## Air

# In[6]:


class Air:
    def __init__(self, name, t, rh, l):
        self.name = name
        self.t = t
        self.rh = rh
        self.l = l
        self.h = HAPropsSI('H', 'T', self.t+273.15, 'P', 101325, 'R', self.rh)
        self.d = HAPropsSI('W', 'T', self.t+273.15, 'P', 101325, 'R', self.rh)
        self.vda = HAPropsSI('Vda', 'T', self.t+273.15, 'P', 101325, 'R', self.rh)
    def __str__(self):
        return f'Air flow {self.name}, L={self.l:.0f} m3/h, t={self.t:.1f} C,                RH={self.rh:.2f}, h={self.h:.0f} J/kg, d={self.d:.4f} kg/kg'


# ## Section

# In[7]:


class Section:
    def __init__(self, mode='winter', serie='basic', **kwargs):
        self.mode = mode
        self.serie = serie
        self.__dict__.update(kwargs)
        self._set_name()
        self.output_dict = {}
        self.bom = {}
        self._read_bom_dict()
        self.define_geometry()

    def _set_name(self):
        if not hasattr (self, 'name'):
            self.name = 'Пустая секция'

    def _read_bom_dict(self):
        fn = os.path.join('.' ,'ext_data', 'bom_dict.json')
        bom_dict = json_read(fn)

        if self.__class__.__name__ in bom_dict.keys():
            bom_dict = bom_dict[self.__class__.__name__]

            if 'model' in bom_dict.keys():
                if isinstance(bom_dict['model'], str):
                    self.model = bom_dict['model']
                elif self.serie in bom_dict['model'].keys():
                    self.model = bom_dict['model'][self.serie]

            if 'accesory' in bom_dict.keys():
                if isinstance(bom_dict['accesory'], str):
                    self.accesory = bom_dict['accesory']
                elif self.serie in bom_dict['accesory'].keys():
                    self.accesory = bom_dict['accesory'][self.serie]

            if 'sensors' in bom_dict.keys():
                if self.serie in bom_dict['sensors'].keys():
                    self.sensors = bom_dict['sensors'][self.serie]
                else:
                    self.sensors = bom_dict['sensors']
                

    def define_geometry(self):
        self.lenght = 0
        self.door = 0
        # set minimal internal dimensions
        self.min_width = 0
        self.min_height = 0
        # set internal margins
        self.mar_width = 0
        self.mar_height = 0
        self.max_velocity = 99

    def check_dimensions(self, w, h):
        if (w <= self.mar_width) or (h <= self.mar_height):
            return False
        elif self.l/((w-self.mar_width)*(h-self.mar_height))*1e6/3600 > self.max_velocity:
            self.v = self.l/((w-self.mar_width)*(h-self.mar_height))*1e6/3600
            return False
        else:
            self.v = self.l/((w-self.mar_width)*(h-self.mar_height))*1e6/3600
            self.w_int = w
            self.h_int = h
            return True

    def __str__(self):
        return f'AHU section {self.name}'

    def prepear_output(self):
        pass

    def set_air_in(self, air_in):
        self.air_in = air_in
        self.l = self.air_in.l

    def generate_md(self):
        self.prepear_output()
        lines=[]
        lines.append(f'\n## {self.name}\n')
        if self.output_dict:
            lines.append(f'\n')
            lines.append(f'|      |         |')
            lines.append(f'|:-----| :------:|')
            for key, value in self.output_dict.items():
                lines.append(f'|{key}|{value}|')
        if hasattr (self, 'accesory'):
            lines.append(f'\n\n***Принадлежности***  ')
            lines.append(f'{self.accesory}  ')
        lines.append(f'\n')
        return lines

    def prepear_bom(self):
        self.bom[self.name] = {'qty': 1}
        if hasattr(self, 'sensors'):
            self.bom.update(self.sensors)

    def get_code(self):
        return 'ES'


# ## Heater

# In[8]:


class Heater(Section):
    def __str__(self):
        self.calculate()
        return f'AHU section {self.name}. Heating power = {self.power/1000:.0f} kW'

    def _set_name(self):
        if not hasattr(self, 'name'):
            self.name = 'Нагреватель'

    def power_calc(self):
        if self.t_end > self.air_in.t:
            self.h_end = HAPropsSI('H', 'T', self.t_end+273.15, 'P', 101325, 'W', self.air_in.d)
            self.power = (self.h_end - self.air_in.h)*self.air_in.l/3600*1.2
        else:
            self.t_end = self.air_in.t
            self.power = 0

    def t_end_calc(self):
        if self.power > 0:
            self.h_end = self.power / (self.air_in.l/3600*1.2) + self.air_in.h
            self.t_end = HAPropsSI('T', 'H', self.h_end, 'P', 101325, 'W', self.air_in.d) - 273.15
        else:
            self.t_end = self.air_in.t

    def air_out_calc(self):
        rh_end = HAPropsSI('RH','T',self.t_end+273.15,'P',101325,'W',self.air_in.d)
        self.air_out = Air(self.name+' air out',self.t_end, rh_end, self.air_in.l)
    def prepear_output(self):
        self.output_dict['Расчетная мощность, кВт']         = round(self.power/1000, 1)
        self.output_dict['Температура воздуха вход, °C']    = round(self.air_in.t, 1)
        self.output_dict['Влажность воздуха вход, %']       = round(self.air_in.rh*100, 1)
        self.output_dict['Температура воздуха выход, °C']   = round(self.air_out.t, 1)
        self.output_dict['Влажность воздуха выход, %']      = round(self.air_out.rh*100, 1)

    def calculate(self):
        if hasattr(self, 't_end'):
            self.power_calc()
        if hasattr(self, 'power'):
            self.t_end_calc()
        self.air_out_calc()

    def prepear_bom(self):
        super().prepear_bom()
        self.bom[self.name] = {'qty': 1, 'model': self.model, 'power': self.power,
                               'a': self.w_int, 'b': self.h_int,
                               'air_flow':self.l}
    def get_code (self):
        return 'N'


# ### Heater_water

# In[9]:


class Heater_water(Heater):
    def __str__ (self):
        self.calculate()
        return f'AHU section {self.name}. Q = {self.power/1000:.0f} kW, G = {self.g_fluid:.1f} ton/h,         Connection = {self.pipe_size}``'

    def _set_name(self):
        if not hasattr(self, 'name'):
            self.name = 'Водяной нагреватель'

    def define_geometry(self):
        if self.serie == 'pure':
            self.lenght = 530
            self.door = 1
        else:
            self.lenght = 210
            self.door = 0
        # set minimal internal dimensions
        self.min_width = 110
        self.min_height = 60
        # set internal margins
        self.mar_width = 140
        self.mar_height = 100
        if not hasattr(self, 'max_velocity'):
            self.max_velocity = 3
    def _water_flow_calc(self):
        c = 4.2  # kJ/(kg*K) specific heat for water
        ro_fluid = 0.998   # kg*1e3/m3
        self.g_fluid = self.power/(c*(self.t1_fluid-self.t2_fluid))/ro_fluid*3600/1e6 #kg*1e3/h
        self.g_fluid = self.g_fluid
    def _pipe_size_calc(self):
        velocity_max = 1.4
        self.pipe_size = pipe_sizing (self.g_fluid, velocity_max)
    def prepear_output(self):
        super().prepear_output()
        self.output_dict['Расход теплоносителя, м³/ч']  = round (self.g_fluid, 2)
        self.output_dict['Диаметр подключения, мм']         = self.pipe_size
        self.output_dict['Темп. поступающей воды, °C']  = round (self.t1_fluid, 1)
        self.output_dict['Темп. уходящей воды, °C']     = round (self.t2_fluid, 1)
        self.output_dict['Теплоноситель']               = self.fluid

    def calculate(self):
        super().calculate()
        self._water_flow_calc()
        self._pipe_size_calc()
    def prepear_bom(self):
        super().prepear_bom()
        self.bom[self.name] = {'qty': 1, 'model': self.model, 'power': self.power,
                               'a': self.w_int - self.mar_width,
                               'b': self.h_int - self.mar_height,
                               'air_flow': self.l}
    def get_code (self):
        return 'NW'


# ### Heater_electric

# In[10]:


class Heater_electric(Heater):
    def __str__ (self):
        self.calculate()
        return f'AHU section {self.name}. Q = {self.power/1000:.0f} kW, G = {self.g_fluid:.1f} ton/h,         Connection = {self.pipe_size}``'
    def _set_name(self):
        if not hasattr (self, 'name'):
            self.name = 'Электрический нагреватель'
    def define_geometry(self):
        self.lenght = 345
        self.door = 1
        #set minimal internal dimensions
        self.min_width = 200
        self.min_height = 100
        #set internal margins
        self.mar_width = 250
        self.mar_height = 100
        if not hasattr(self, 'max_velocity'):
            self.max_velocity = 6
    @staticmethod
    def _electricity_type (power):
        if power > 2000:
            return '3~ 400V 50Hz'
        else:
            return '1~ 230V 50Hz'
    @staticmethod
    def _nominal_power(power):
        heater_step = 1000
        n_nom = np.ceil(power / heater_step) * heater_step
        return n_nom
    def prepear_output(self):
        super().prepear_output()
        self.output_dict['Номинальная мощность, кВт']  = round(self._nominal_power(self.power)/1000, 1)
        self.output_dict['Параметры электропитания']   = self._electricity_type (self.power)

    def calculate(self):
        super().calculate()
    def prepear_bom(self):
        super().prepear_bom()
        self.bom[self.name] = {'qty': 1, 'model': self.model, 'power': self._nominal_power(self.power)}

    def get_code (self):
        return 'NE'


# ### Heater_water_regenerator

# In[11]:


class Heater_water_regenerator (Heater):
    def define_geometry(self):
        self.lenght = 350
        self.door = 0
        #set minimal internal dimensions
        self.min_width = 200
        self.min_height = 100
        #set internal margins
        self.mar_width = 100
        self.mar_height = 100
        if not hasattr(self, 'max_velocity'):
            self.max_velocity = 2.5
    def prepear_output(self):
        super().prepear_output()

    def _set_name(self):
        if not hasattr (self, 'name'):
            self.name = 'Пластинчатый рекуператор (нагреватель)'

    def prepear_bom(self):
        super().prepear_bom()
        self.bom[self.name] = {'qty': 1,
                               'model': self.model,
                               'power': self.power,
                               'a': self.w_int - self.mar_width,
                               'b': self.h_int - self.mar_height,
                               'air_flow': self.l}
    def get_code (self):
        return 'NRG'


# ### Heater_plate_regenerator

# In[11]:


class Heater_plate_regenerator (Heater):
    def define_geometry(self):
        self.lenght = 350
        self.door = 0
        #set minimal internal dimensions
        self.min_width = 200
        self.min_height = 100
        #set internal margins
        self.mar_width = 140
        self.mar_height = 100
        if not hasattr(self, 'max_velocity'):
            self.max_velocity = 2.5
    def prepear_output(self):
        super().prepear_output()

    def _set_name(self):
        if not hasattr (self, 'name'):
            self.name = 'Пластинчатый рекуператор (нагреватель)'

    def prepear_bom(self):
        if not hasattr (self, 'model'):
            self.model = 'нет'
        super().prepear_bom()
        self.bom[self.name] = {'qty': 1,
                               'power': self.power,
                               'air_flow': self.l}
    def get_code (self):
        return 'PR'


# ## Cooler

# In[12]:


class Cooler(Section):
    def __str__ (self):
        self.calculate()
        return f'AHU section {self.name}. Cooling power={self.power/1000:.0f} kW,         t_end={self.t_end:.1f} C, Drain flow={self.drainage_flow:.0f} l/h'
    def _set_name(self):
        if not hasattr (self, 'name'):
            self.name = 'Охладитель'
    def define_geometry(self):
        self.lenght = 530
        self.door = 1
        #set minimal internal dimensions
        self.min_width = 200
        self.min_height = 100
        #set internal margins
        self.mar_width = 140
        self.mar_height = 100
        if not hasattr(self, 'max_velocity'):
            self.max_velocity = 2.5
    def _drying_calc(self):
        error = 0.0002
        assert self.air_in.d - self.d_end > error, 'На входе в осушитель воздух суше,                                                        чем требуемый после осушителя'
        ro_nom = 1.2 #kg/m3
        heat_vapor = 2257  #kJ/kg
        error = 0.0002
        step = 0.05
        t_end = self.air_in.t
        self.h_end  = self.air_in.h
        d_target = self.d_end
        self.d_end  = self.air_in.d
        while self.d_end-d_target > error:
            self._cooling_t_calc(t_start = self.air_in.t,
                                 d_start=self.air_in.d,
                                 h_start=self.air_in.h,
                                 t_end=t_end,
                                 l=self.air_in.l,
                                 t_coil=self.t_coil)
            t_end -= step
            assert t_end > self.t_coil, 'Осушение до требуемой влажности при заданной                                         температуре хладоносителя невозможно'
        self.drainage_flow = (self.air_in.d - self.d_end)*self.air_in.l*ro_nom

    def _cooling_t_calc(self, t_start, d_start, h_start, t_end, l, t_coil):
        assert t_end > t_coil, 'Охлаждение до требуемой температуры при заданной                                         температуре хладоносителя невозможно'
        ro_nom = 1.2 # kg/m3
        heat_vapor = 2257  # kJ/kg
        d_coil = HAPropsSI('W', 'T', t_coil + 273.15, 'P', 101325,'R',1)
        d_end = d_coil+(d_start-d_coil)*((t_end-t_coil)/(t_start-t_coil))
        if HAPropsSI('W', 'T', t_end+273.15, 'P', 101325,'R', 1) < d_end:
            rh_end = 1
        else:
            rh_end = HAPropsSI('R','T',t_end+273.15,'P',101325,'W',d_end)
        h_end  = HAPropsSI('H','T',t_end+273.15,'P',101325,'R',rh_end)
        d_end = HAPropsSI('W','T',t_end+273.15,'P',101325,'R',rh_end)
        self.power = (h_end-h_start)*self.air_in.l/3600*ro_nom
        self.d_end = d_end
        self.rh_end = rh_end
        self.h_end = h_end
        self.drainage_flow = (self.air_in.d - self.d_end)*self.air_in.l*1.2

    def _cooling_q_calc(self):
        ro_nom = 1.2 #kg/m3
        heat_vapor = 2257  #kJ/kg
        error = 10
        step = 0.05
        t_end = self.air_in.t
        power_target = self.power
        self.power = 0
        while self.power - power_target > error:
            self._cooling_t_calc(t_start = self.air_in.t,
                                 d_start=self.air_in.d,
                                 h_start=self.air_in.h,
                                 t_end=t_end,
                                 l=self.air_in.l,
                                 t_coil=self.t_coil)
            #print(f't_start={self.air_in.t}, t_end={t_end}, self.h_end={self.h_end}')
            t_end -= step
            assert t_end > self.t_coil, 'Достижение требуемой мощности при заданной  температуре хладоносителя невозможно'
    def _power_calc(self):
        if hasattr(self, 't_evap'):
            self.t_coil = self.t_evap
        elif hasattr(self, 't1_fluid') and hasattr(self, 't2_fluid'):
            self.t_coil = (self.t1_fluid  + self.t2_fluid) /2
        elif not hasattr(self, 't_coil'):
            self.t_coil = 8
        if hasattr(self, 't_end'):
            assert self.t_end < self.air_in.t, f'Требуемая температура {self.t_end} °C  ниже температуры входящего воздуха {self.air_in.t} °C.'
            self._target_val = 't'
            self._cooling_t_calc(t_start=self.air_in.t,
                                 d_start=self.air_in.d,
                                 h_start=self.air_in.h,
                                 t_end=self.t_end,
                                 l=self.air_in.l,
                                 t_coil=self.t_coil)
        elif hasattr(self, 'd_end'):
            if self.d_end > self.air_in.d:
                self.d_end = self.air_in.d
            self._target_val = 'd'
            self._drying_calc()
        elif hasattr(self, 'power'):
            if self.power > 0:
                self.power = 0
            self._target_val = 'power'
            self._cooling_q_calc()

    def _air_out_calc(self):
        self.t_end = HAPropsSI('T','H',self.h_end,'P',101325,'RH',self.rh_end)-273.15
        self.air_out = Air(self.name+' air out', self.t_end, self.rh_end, self.air_in.l)

    def prepear_output(self):
        self.output_dict['Расчетная мощность, кВт']         = round(self.power/1000, 1)
        self.output_dict['Температура воздуха вход, °C']    = round(self.air_in.t, 1)
        self.output_dict['Влажность воздуха вход, %']    = round(self.air_in.rh*100, 1)
        self.output_dict['Температура воздуха выход, °C']   = round(self.air_out.t, 1)
        self.output_dict['Влажность воздуха выход, %']    = round(self.air_out.rh*100, 1)
        self.output_dict['Отвод конденсата, кг/ч']    = round(self.drainage_flow, 1)
        
    def calculate(self):
        self._power_calc()
        self._air_out_calc()

    def prepear_bom(self):
        super().prepear_bom()
        if not hasattr(self, 'model'):
                self.model = 'нет'
        self.bom[self.name] = {'qty': 1,
                               'model': self.model,
                               'power': self.power,
                               'a': self.w_int - self.mar_width,
                               'b': self.h_int - self.mar_height,
                               'air_flow': self.l}
        self.bom['Каплеуловитель'] = {'qty': 1,
                               'a': self.w_int - self.mar_width,
                               'b': self.h_int - self.mar_height,
                               'air_flow': self.l}
        if self._target_val == 'd':
            self.bom['Канальный активный датчик температуры и влажности'] = {'qty': 1, 'model': 'KFTF-SD-U'}
    def get_code (self):
        return 'C'


# ### Cooler_water

# In[13]:


class Cooler_water (Cooler):
    def __str__ (self):
        self.calculate()
        return f'AHU section {self.name}. Q = {self.power/1000:.0f} kW, G = {self.g_fluid:.1f} ton/h, Connection = {self.pipe_size}``'

    def _set_name(self):
        if not hasattr (self, 'name'):
            self.name = 'Водяной охладитель'

    def water_flow_calc(self):
        if 'вода' in self.fluid.lower():
            c_fluid = 4.187  #  kJ/(kg*K) specific heat for water
            ro_fluid = 1.002 #kg*1e3/m3
        elif 'гликоль' in self.fluid.lower():
            c_fluid = 3.747  #  kJ/(kg*K) specific heat for 40% propylene glycol
            ro_fluid = 1.020  #  kg*1e3/m3
        self.g_fluid = self.power/(c_fluid*(self.t1_fluid-self.t2_fluid))/ro_fluid*3600/1e6 #kg*1e3/h
        self.g_fluid = self.g_fluid

    def pipe_size_calc(self):
        velocity_max = 1.4
        self.pipe_size = pipe_sizing (self.g_fluid, velocity_max)

    def prepear_output(self):
        super().prepear_output()
        self.output_dict['Расход хладоносителя, м³/ч']  = round (self.g_fluid, 2)
        self.output_dict['Диаметр подключения']         = self.pipe_size
        self.output_dict['Темп. поступающей воды, °C']  = round (self.t1_fluid, 1)
        self.output_dict['Темп. уходящей воды, °C']     = round (self.t2_fluid, 1)
        self.output_dict['Теплоноситель']               = self.fluid

    def calculate(self):
        super().calculate()
        self.water_flow_calc()
        self.pipe_size_calc()

    def get_code(self):
        return 'CW'


# ### Cooler_freon

# In[14]:


class Cooler_freon (Cooler):
    def __str__ (self):
        self.calculate()
        return f'AHU section {self.name}. Q = {self.power/1000:.0f} kW, Freon: {self.fluid}, Connection = {self.pipe_size}``'
    def _set_name(self):
        if not hasattr (self, 'name'):
            self.name = 'Фреоновый охладитель'
    def pipe_size_calc (self):
        self.pipe_size = pipe_sizing_freon (self.power, self.fluid)
    def prepear_output(self):
        super().prepear_output()
        self.output_dict['Диаметр подключения']         = self.pipe_size
        self.output_dict['Темп. кипения, °C']           = self.t_evap
        self.output_dict['Хладон']                      = self.fluid
    def calculate(self):
        super().calculate()
        self.pipe_size_calc()

    def get_code (self):
        return 'CF'


# ### Cooler_water_regenerator

# In[15]:


class Cooler_water_regenerator (Cooler_water):
    def define_geometry(self):
        self.lenght = 630
        self.door = 1
        #set minimal internal dimensions
        self.min_width = 200
        self.min_height = 100
        #set internal margins
        self.mar_width = 140
        self.mar_height = 100
        if not hasattr(self, 'max_velocity'):
            self.max_velocity = 2.5
    def _set_name(self):
        if not hasattr (self, 'name'):
            self.name = 'Гликолевый рекуператор (охладитель)'

    def get_code (self):
        return 'CRG'


# ### Cooler_plate_regenerator

# In[15]:


class Cooler_plate_regenerator (Cooler):
    def define_geometry(self):
        self.lenght = 630
        self.door = 1
        #set minimal internal dimensions
        self.min_width = 200
        self.min_height = 100
        #set internal margins
        self.mar_width = 100
        self.mar_height = 100
        if not hasattr(self, 'max_velocity'):
            self.max_velocity = 2.5
    def _set_name(self):
        if not hasattr (self, 'name'):
            self.name = 'Пластинчатый рекуператор (охладитель)'

    def get_code (self):
        return 'PR'


# ## Filter

# In[16]:


class Filter(Section):
    def define_geometry(self):
        self.lenght = 300
        self.door = 1
        #set minimal internal dimensions
        self.min_width = 200
        self.min_height = 100
        self._filter_case_width = 25
        #set internal margins
        self.mar_width = 50+self._filter_case_width*2
        self.mar_height = 45+self._filter_case_width*2
        if not hasattr(self, 'max_velocity'):
            self.max_velocity = 2.8

    def _set_name(self):
        if not hasattr (self, 'name'):
            self.name = 'Фильтр'

    def __str__(self):
        self.calculate()
        return f'AHU section {self.name}.'

    def pressure_loss(self):
        if self.filter_type == 'кассетный':
            if self.filter_class   == 'G4':
                self.model =  'ФВКасIII-G4-96'
            elif self.filter_class == 'F7':
                self.model =  'ФВКом-F7-96'
            elif self.filter_class == 'F9':
                self.model =  'ФВКом-F9-96'
        if self.filter_type == 'карманный':
            if self.filter_class   == 'G4':
                self.model =  'ФВКасIII-G4-96'
            elif self.filter_class == 'F7':
                self.model =  'ФВК-F7-300'
            elif self.filter_class == 'F9':
                self.model =  'ФВК-F9-300'
        self.dp = self._filter_pressure_loss(self.v, self.model)

    @staticmethod
    def _filter_pressure_loss (velocity, filter_type):
        filters_data = {
         'ФВКом-F5-96':   [43.5783172597273, -45.8064516129032],
         'ФВКом-F5-48':   [53.3954107083472, -25.6653225806452],
         'ФВКом-F6-96':   [46.3318922514134, -32.9879032258064],
         'ФВКом-F6-48':   [56.3086132357832, -13.0873655913979],
         'ФВКом-F7-96':   [50.3225806451613, -15.252688172043 ],
         'ФВКом-F7-48':   [59.1020951114067,  16.7647849462366],
         'ФВКом-F8-96':   [52.6770867974726,   9.3548387096774],
         'ФВКом-F8-48':   [56.5879614233455,  47.8978494623656],
         'ФВКом-F9-96':   [51.9188560026605,  24.2163978494624],
         'ФВКом-F9-48':   [62.1350182906551,  47.5685483870968],
         'ФВКасIII-G4-48':[34.7988027934819, -33.1989247311828],
         'ФВКасIII-G4-96':[31.0475557033588, -36.8575268817204],
         'ФВК-F7-600':    [35.0781509810442,   2.5362903225807],
         'ФВК-F7-300':    [43.4186897239773,   0.0591397849463],
         'ФВК-F8-600':    [38.4702361157299,   8.3924731182796],
         'ФВК-F8-300':    [44.6158962421017,  22.6922043010754],
         'ФВК-F9-600':    [41.8224143664782,  13.590053763441 ],
         'ФВК-F9-300':    [47.5690056534752,  35.6787634408604]
         }
        coef1, coef2 = filters_data[filter_type]
        return coef1*velocity + coef2

    def air_out_calc(self):
        self.air_out = Air(self.name + ' air out', self.air_in.t, self.air_in.rh, self.air_in.l)

    def prepear_output(self):
        self.pressure_loss()
        self.output_dict['Класс фильтрации']                 = self.filter_class
        self.output_dict['Тип фильтра']                      = self.filter_type
        self.output_dict['Начальные потери давления, Па']    = int (self.dp)
        self.output_dict['Расчетные потери давления, Па']    = int (self.dp*2)
        
    def calculate(self):
        self.air_out_calc()

    def prepear_bom(self):
        super().prepear_bom()
        self.bom[self.name] = {'qty': 1, 'model': self.model, 'a': self.w_int - self.mar_width + self._filter_case_width*2,
                              'b': self.h_int - self.mar_height + self._filter_case_width*2}
    def get_code(self):
        return self.filter_class


# ## Humidifier

# In[17]:


class Humidifier (Section):
    def _set_name(self):
        if not hasattr (self, 'name'):
            self.name = 'Увлажнитель'
    def humid_calc(self):
        ro_nom = 1.2 #kg/m3
        #steam humidifier
        if hasattr(self, 'rh_end'):
            self.d_end = HAPropsSI('W','T',self.air_in.t+273.15,'P',101325,'R',self.rh_end)
            self.t_end = self.air_in.t
        self.capacity = (self.d_end - self.air_in.d)*self.air_in.l*ro_nom
    def prepear_output(self):
        self.output_dict['Производительность, кг/ч']        = round(self.capacity, 1)
        self.output_dict['Температура воздуха вход, °C']    = round(self.air_in.t, 1)
        self.output_dict['Влажность воздуха вход, %']       = round(self.air_in.rh*100, 1)
        self.output_dict['Температура воздуха выход, °C']    = round(self.t_end, 1)
        self.output_dict['Влажность воздуха выход, %']       = round(self.rh_end*100, 1)

    def prepear_bom(self):
        super().prepear_bom()
        if not hasattr(self, 'model'):
                self.model = 'нет'
        self.bom[self.name] = {'qty': 1,
                               'model': self.model,
                               'capacity': self.capacity,
                               'air_flow': self.l}
        self.bom['Каплеуловитель'] = {'qty': 1,
                               'a': self.w_int - self.mar_width,
                               'b': self.h_int - self.mar_height,
                               'air_flow': self.l}
    def air_out_calc(self):
        self.air_out = Air(self.name+' air out',self.t_end, self.rh_end, self.air_in.l)
    def calculate(self):
        self.humid_calc()
        self.air_out_calc()
    def get_code (self):
        return 'H'


# ### Humidifier_steam

# In[18]:


class Humidifier_steam (Humidifier):
    def define_geometry(self):
        self.lenght = 730
        self.door = 1
        #set minimal internal dimensions
        self.min_width = 650
        self.min_height = 100
        #set internal margins
        self.mar_width = 0
        self.mar_height = 0
        if not hasattr(self, 'max_velocity'):
            self.max_velocity = 2.5
    def _set_name(self):
        if not hasattr (self, 'name'):
            self.name = 'Паровой увлажнитель'
    def get_code (self):
        return 'HS'


# ### Humidifier_adiabatic

# In[19]:


class Humidifier_adiabatic (Humidifier):
    def define_geometry(self):
        self.lenght = 1200
        self.door = 1
        #set minimal internal dimensions
        self.min_width = 650
        self.min_height = 100
        #set internal margins
        self.mar_width = 0
        self.mar_height = 0
        if not hasattr(self, 'max_velocity'):
            self.max_velocity = 2.5
    def humid_calc(self):
        ro_nom = 1.2 #kg/m3
        #adiabatic humidifier
        if hasattr(self, 'rh_end'):
            self.d_end = HAPropsSI('W','H',self.air_in.h,'P',101325,'R',self.rh_end)
            self.t_end = HAPropsSI('T','H',self.air_in.h,'P',101325,'R',self.rh_end) - 273.15
        self.capacity = (self.d_end - self.air_in.d)*self.air_in.l*ro_nom
    def _set_name(self):
        if not hasattr (self, 'name'):
            self.name = 'Адиабатический увлажнитель'
    def get_code (self):
        return 'HA'


# ## Flex_joint

# In[20]:


class Flex_joint (Section):
    def define_geometry(self):
        self.lenght = 100
        self.door = 0
        #set minimal internal dimensions
        self.min_width = 200
        self.min_height = 100
        #set internal margins
        self.mar_width = 0
        self.mar_height = 0
        if not hasattr(self, 'max_velocity'):
            self.max_velocity = 6

    def _set_name(self):
        if not hasattr (self, 'name'):
            self.name = 'Гибкая вставка'

    def calculate(self):
        self.air_out_calc()

    def air_out_calc(self):
        self.air_out = Air(self.name + ' air out', self.air_in.t, self.air_in.rh, self.air_in.l)

    def get_code (self):
        return 'Z'

    def prepear_output(self):
        self.h_connection, self.w_connection = connection_calc (self.l,
                                                                self.w_int,
                                                                self.h_int,
                                                                v_max=self.max_velocity)
        self.output_dict['Высота, мм']        = self.h_connection
        self.output_dict['Ширина, мм']        = self.w_connection
        self.output_dict['Скорость воздуха, м/с'] = round(self.air_in.l/3600 / self.w_connection/
                                                      self.h_connection*1e6, 1)
    def prepear_bom(self):
        super().prepear_bom()
        self.h_connection, self.w_connection = connection_calc (self.l,
                                                                self.w_int,
                                                                self.h_int,
                                                                v_max=self.max_velocity)
        self.bom[self.name] = {'qty': 1, 'model': f'{self.w_connection}x{self.h_connection}'}


# ## Damper

# In[21]:


class Damper(Section):
    def define_geometry(self):
        self.lenght = 150
        self.door = 0
        #set minimal internal dimensions
        self.min_width = 200
        self.min_height = 100
        #set internal margins
        self.mar_width = 0
        self.mar_height = 0
        if not hasattr(self, 'max_velocity'):
            self.max_velocity = 6

    def _set_name(self):
        if not hasattr (self, 'name'):
            self.name = 'Воздушная заслонка'

    def calculate(self):
        self.air_out_calc()

    def air_out_calc(self):
        self.air_out = Air(self.name+' air out', self.air_in.t, self.air_in.rh, self.air_in.l)

    def get_code (self):
        return 'AV'

    def prepear_output(self):
        self.h_connection, self.w_connection = connection_calc(self.l,
                                                               self.w_int,
                                                               self.h_int,
                                                               v_max=self.max_velocity)
        self.output_dict['Высота, мм'] = self.h_connection
        self.output_dict['Ширина, мм'] = self.w_connection
        self.output_dict['Скорость воздуха, м/с']       = round(self.air_in.l/3600 / self.w_connection/
                                                      self.h_connection*1e6, 1)
    def prepear_bom(self):
        super().prepear_bom()
        self.h_connection, self.w_connection = connection_calc(self.l,
                                                               self.w_int,
                                                               self.h_int,
                                                               v_max=self.max_velocity)
        self.bom[self.name] = {'qty': 1,
                               'model': f'{self.w_connection}x{self.h_connection}',
                               'a': self.w_connection,
                               'b': self.h_connection}


# ## Silencer

# In[22]:


class Silencer (Section):
    def define_geometry(self):
        if not hasattr(self, 'lenght'):
            self.lenght = 1000
        self.door = 0
        #set minimal internal dimensions
        self.min_width = 300
        self.min_height = 100
        #set internal margins
        self.mar_width = 0
        self.mar_height = 0
        if not hasattr(self, 'max_velocity'):
            self.max_velocity = 5
    def _set_name(self):
        if not hasattr (self, 'name'):
            self.name = 'Шумоглушитель'

    def calculate(self):
        self.air_out_calc()

    def air_out_calc(self):
        self.air_out = Air(self.name + ' air out', self.air_in.t, self.air_in.rh, self.air_in.l)

    def prepear_output(self):
        self.output_dict['Длина, мм']        = self.lenght

    def prepear_bom(self):
        splitter_num = np.floor(self.w_int / 100 / 2)

        super().prepear_bom()
        self.bom[self.name] = {'qty': 1,
                               'model': self.serie,
                               'a': self.lenght,
                               'b': self.h_int,
                               'splitter_num': splitter_num}

    def get_code (self):
        return 'SL'


# ## Mixing

# In[23]:


class Mixing (Section):
    def define_geometry(self):
        if not hasattr(self, 'lenght'):
            self.lenght = 1000
        self.door = 1
        #set minimal internal dimensions
        self.min_width = 300
        self.min_height = 100
        #set internal margins
        self.mar_width = 0
        self.mar_height = 0
        if not hasattr(self, 'max_velocity'):
            self.max_velocity = 5
    def _set_name(self):
        if not hasattr (self, 'name'):
            self.name = 'Камера смешения'
    def calculate(self):
        self.air_out_calc()

    def air_out_calc(self):
        l = self.air_in.l + self.air_rec.l

        h = ((self.air_in.h * self.air_in.l / self.air_in.vda) +        (self.air_rec.h * self.air_rec.l / self.air_rec.vda))/        (self.air_in.l / self.air_in.vda + self.air_rec.l / self.air_rec.vda)

        d = ((self.air_in.d * self.air_in.l / self.air_in.vda) +        (self.air_rec.d * self.air_rec.l / self.air_rec.vda))/        (self.air_in.l / self.air_in.vda + self.air_rec.l / self.air_rec.vda)

        if HAPropsSI('W', 'H', h, 'P', 101325, 'R', 1) < d:
            rh_end = 1
        else:
            rh_end = HAPropsSI('R','H', h, 'P', 101325,'W', d)
        t = HAPropsSI('T', 'H', h, 'P',101325, 'R', rh_end) - 273.15
        d_end = HAPropsSI('W','H', h, 'P',101325, 'R', rh_end)
        self.drainage_flow = (d - d_end) * l * 1.2

        self.air_out = Air(self.name + ' air out', t, rh_end, l)

    def prepear_output(self):
        self.output_dict['Температура воздуха вход, °C']    = round(self.air_in.t, 1)
        self.output_dict['Влажность воздуха вход, %']    = round(self.air_in.rh*100, 1)
        self.output_dict['Расход воздуха вход, м³/ч']    = round(self.air_in.l, 1)
        self.output_dict['Температура воздуха подмес, °C']    = round(self.air_rec.t, 1)
        self.output_dict['Влажность воздуха подмес, %']    = round(self.air_rec.rh*100, 1)
        self.output_dict['Расход воздуха подмес, м³/ч']    = round(self.air_rec.l, 1)
        self.output_dict['Температура воздуха выход, °C']   = round(self.air_out.t, 1)
        self.output_dict['Влажность воздуха выход, %']    = round(self.air_out.rh*100, 1)
        self.output_dict['Расход воздуха выход, м³/ч']    = round(self.air_out.l, 1)
        self.output_dict['Отвод конденсата, кг/ч']    = round(self.drainage_flow, 1)

    def prepear_bom(self):
        super().prepear_bom()
        self.h_connection, self.w_connection = connection_calc(self.air_rec.l,
                                                               self.w_int,
                                                               1e9,
                                                               v_max=self.max_velocity)
        self.bom[self.name] = {'qty': 1,
                               'model': f'{self.w_connection}x{self.h_connection}',
                               'a': self.w_connection,
                               'b': self.h_connection}
    def get_code (self):
        return 'MX'


# In[ ]:





# ## UV_filter

# In[22]:


class UV_filter (Section):
    def define_geometry(self):
        if not hasattr(self, 'lenght'):
            self.lenght = 1400
        self.door = 1
        #set minimal internal dimensions
        self.min_width = 300
        self.min_height = 100
        #set internal margins
        self.mar_width = 0
        self.mar_height = 0
        if not hasattr(self, 'max_velocity'):
            self.max_velocity = 7
    def _set_name(self):
        if not hasattr (self, 'name'):
            self.name = 'Секция ультрафиолетовой инактивации'

    def _uv_lamp_calc(self, l, category):
        hv_dict={1: ('Операционные, предоперационные, родильные,         стерильные зоны централизованных стерилизационных отделений (ЦСО),         детские палаты роддомов, палаты для недоношенных и травмированных детей', 385),
                2: ('Перевязочные комнаты стерилизации и пастеризации грудного молока, \
                палаты и отделения иммуноослабленных больных, палаты реанимационных отделений, \
                помещения нестерильных зон ЦСО, бактериологические и вирусологические \
                лаборатории, станции переливания крови, фармацевтические цеха', 256),
                3: ('Палаты, кабинеты и другие помещения ЛПУ (не включенные в I и II категории)',167),
                4: ('Детские игровые комнаты, школьные классы, бытовые помещения промышленных и \
                общественных зданий с большим скоплением людей при длительном пребывании', 130),
                5: ('Курительные комнаты, общественные туалеты и лестничные площадки помещений ЛПУ', 105)}
        category_info, hv = hv_dict[category]
        k = 1.3
        fbk_75W = 23 # UV power of 1 lamp 75 w
        fbk = hv * l * k / 3600
        num_lamp = np.ceil (fbk / fbk_75W)
        return (num_lamp, category_info)
    
    def calculate(self):
        if not hasattr (self, 'category'):
            self.category = 1
        (self.uv_lamp_75w_num, self.category_info) = self._uv_lamp_calc(self.air_in.l, self.category)
        self.air_out_calc()

    def air_out_calc(self):
        self.air_out = Air(self.name + ' air out', self.air_in.t, self.air_in.rh, self.air_in.l)

    def prepear_output(self):
        self.output_dict['Количество ламп, шт.']        = self.uv_lamp_75w_num
        self.output_dict['Потребляемая мощность, кВт.'] = round(self.uv_lamp_75w_num * 75 * 1.05 / 1000, 1)
        self.output_dict['Категория помещений'] = self.category
        self.output_dict['Описание категории помещений'] = self.category_info

    def prepear_bom(self):
        super().prepear_bom()
        self.bom[self.name] = {'qty': 1,
                               'model': self.serie,
                               'uv_lamp_75w': self.uv_lamp_75w_num}

    def get_code (self):
        return 'UV'

