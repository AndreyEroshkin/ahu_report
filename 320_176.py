#!/usr/bin/env python
# coding: utf-8

# In[1]:


from ahu import Air, Ahu
from converter import write_all_reports
from IPython.core.display import HTML
from CoolProp.HumidAirProp import HAPropsSI


# In[2]:


report_number = 'test/176'
site_name = 'test'


# In[3]:


def make_pure_sup(system_name, l, t_after_recup, power, p_tot, p_net, weight):
    oda_w = Air('oda winter', -30., 0.84, l)
    oda_s = Air('oda summer',  25.1, 0.56, l)
    sup_w = Air('sup winter',  20., 0.40, l)
    sup_s = Air('sup summer',  19., 0.60, l)

    ahu = Ahu(system_name, oda_s, oda_w, sup_s, sup_w, 'basic', 'П', weight = weight)
    ahu.add('Flex_joint')
    ahu.add('Damper')

    ahu.add('Filter',
            filter_type='кассетный',
            filter_class='G4')

#     ahu.add('Filter',
#             filter_type='кассетный',
#             filter_class='F7')

    ahu.add('Heater_plate_regenerator',
            t_end=t_after_recup)

    ahu.add('Heater_water',
            t_end=sup_w.t,
            t1_fluid=80,
            t2_fluid=60,
            fluid='вода')

    ahu.add('Cooler_freon',
            mode='summer',
            t_end=sup_s.t,
            t_evap=7,
            fluid='R410a')

#     ahu.add('Heater_electric',  mode = 'summer', t_end=sup_s.t)
#     ahu.add('Heater_electric',  mode = 'summer', power=power)

    ahu.add('Fan',
            motor_type='EC',
            p_tot=p_tot,
            p_net=p_net)

#     ahu.add('Filter',
#             filter_type='кассетный',
#             filter_class='F9')
#     ahu.add('Humidifier_steam',
#             rh_end=sup_w.rh)
    ahu.add('Flex_joint')

    ahu.set_report_number(report_number)
    ahu.set_site_name(site_name)
    ahu.calculate()

    write_all_reports(ahu, report_number=report_number, show=False)


# In[4]:


def make_pure_exh(system_name, l, recup_power, p_tot, p_net, weight):
    eta_w = Air('eta winter',  20., 0.4, l)
    eta_s = Air('eta summer',  20., 0.4, l)
    eha_w = Air('eha winter',  20., 0.4, l)
    eha_s = Air('eha summer',  20., 0.4, l)

    ahu = Ahu(system_name, eta_s, eta_w, eha_s, eha_w, 'basic', 'В', weight=weight)
    ahu.add('Flex_joint')
    ahu.add('Filter', filter_type = 'кассетный', filter_class =  'G4')
    ahu.add('Filter', filter_type = 'кассетный', filter_class =  'G4')
    ahu.add('Cooler_plate_regenerator',  power=-recup_power, t_coil=-20)

    ahu.add('Fan',
            motor_type='EC',
            p_tot=p_tot,
            p_net=p_net)

    
    ahu.add('Damper')
    ahu.add( 'Flex_joint')

    ahu.set_report_number(report_number)
    ahu.set_site_name (site_name)
    
    ahu.calculate()

    write_all_reports(ahu, report_number=report_number, show=False)


# In[5]:


l = 11600
l_oda_w = l
l_rec = l - l_oda_w
oda_w = Air('oda winter', -30., 0.86, l_oda_w)


# In[6]:


l = 11600
eta_w = Air('eta winter',  20., 0.4, l)


# In[7]:


recup_eff = 0.4
h_recup_out = oda_w.h - recup_eff * min(oda_w.l, eta_w.l) / oda_w.l * (oda_w.h - eta_w.h)
t_after_recup = HAPropsSI('T', 'H', h_recup_out, 'P', 101325, 'W', oda_w.d) - 273.15
t_after_recup

print(f'Температура после рекуператора {t_after_recup} C')


# In[8]:


systems = {'П1': {'l': 11600, 't_after_recup': t_after_recup, 'power': 4e3, 'p_tot': 1000, 'p_net': 500, 'weight':1430}
          }


# In[9]:


for system_name, value in systems.items():
    make_pure_sup (system_name, value['l'], value['t_after_recup'],
                   value['power'],
                   value['p_tot'], value['p_net'], value['weight'],)


# In[12]:


systems = {'В1': {'l': 11600,  'recup_power': 99.9e3, 'p_tot': 1000, 'p_net': 500, 'weight':80}
          }


# In[13]:


for system_name, value in systems.items():
    make_pure_exh (system_name, value['l'], value['recup_power'], value['p_tot'], value['p_net'], value['weight'])


# In[ ]:





# In[ ]:




