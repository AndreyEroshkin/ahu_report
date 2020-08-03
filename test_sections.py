#!/usr/bin/env python
# coding: utf-8

# In[1]:


from ahu import Air, Ahu
from cost_calc import calc_price
from converter import write_odt, write_pdf
import os
from markdown import markdown
from IPython.core.display import HTML


# Initial conditions

# In[2]:


report_number = 'test'


# In[12]:


def write_all_reports (ahu, report_number='test', show=False):
    report = ahu.generate_md()
    report = '\n'.join(report)
    htmlmarkdown = markdown(report , extensions=['markdown.extensions.tables'])

    fn = os.path.join('.' ,'output', report_number,ahu.name)
    os.makedirs(os.path.dirname(fn), exist_ok=True)

    write_odt (report, fn+'.odt')
    write_pdf (htmlmarkdown, fn+'.pdf')
    bom_df = ahu.generate_bom()
    bom_df.to_excel(fn+'.xlsx')
    calc_price(bom_df).to_excel(fn+'_price.xlsx')
    if show == True:
        display(HTML(htmlmarkdown))


# In[13]:


l = 1100
oda_w = Air('oda winter', -25., 0.86, l)
oda_s = Air('oda summer',  26., 0.5, l)
sup_w = Air('sup winter',  21., 0.4, l)
sup_s = Air('sup summer',  21., 0.4, l)


# In[14]:


w_connection = 900
h_connection = 500
p_tot = 600
p_net = 300

ahu1=Ahu('П1', oda_s, oda_w, sup_s, sup_w, 'pure')
ahu1.add('Flex_joint')
ahu1.add('Damper')
ahu1.add('Heater_water_regenerator', t_end=5, t1_fluid = 90, t2_fluid = 70, fluid = 'вода')
ahu1.add('Heater_electric', t_end=10, t1_fluid = 90, t2_fluid = 70, fluid = 'вода')
ahu1.add('Heater_water', t_end=20, t1_fluid = 90, t2_fluid = 70, fluid = 'вода')
ahu1.add('Cooler_water',  mode='summer', t_end=20, t1_fluid = 7, t2_fluid = 12, fluid = 'вода')
ahu1.add('Cooler_freon',  mode='summer', t_end=17, t_evap = 7, fluid='R410a')
ahu1.add('Cooler_water_regenerator',  mode='summer', t_end=15, t1_fluid = 7, t2_fluid = 12, fluid = 'вода')
ahu1.add('Filter', filter_type='кассетный', filter_class = 'G4')
ahu1.add('Filter', filter_type='кассетный', filter_class = 'F7')
ahu1.add('Filter', filter_type='кассетный', filter_class = 'F9')
ahu1.add('Filter', filter_type='карманный', filter_class = 'G4')
ahu1.add('Filter', filter_type='карманный', filter_class = 'F7')
ahu1.add('Filter', filter_type='карманный', filter_class = 'F9')
ahu1.add('Fan', p_net=300, p_tot = 700)
ahu1.add('Fan_reserved', p_net=300, p_tot = 700)
ahu1.add('Silencer')
ahu1.add('Humidifier', rh_end=0.2)
ahu1.add('Humidifier_steam', rh_end=0.3)
ahu1.add('Humidifier_adiabatic', rh_end=0.4)
ahu1.add( 'Flex_joint')
ahu1.calculate()

write_all_reports (ahu1, report_number=report_number, show=True)


# In[9]:


bom_df = ahu1.generate_bom()


# In[ ]:





# In[11]:


calc_price(bom_df)


# In[8]:


ahu2=Ahu('П2', oda_s, oda_w, sup_s, sup_w, 'pure')

ahu2.add('Flex_joint', w_connection =  1000,  h_connection =  1000)
ahu2.add('Damper',  w_connection =  1000, h_connection =  1000)
ahu2.add('Filter', filter_type='кассетный', filter_class = 'G4')
ahu2.add('Filter', filter_type='кассетный', filter_class = 'F7')
ahu2.add('Heater_water', t_end=sup_w.t, t1_fluid = 90, t2_fluid = 70, fluid = 'вода')
#ahu2.add('Cooler_freon',mode = 'summer' ,power=-4*1e3, t_evap = 7, fluid='R410a')
ahu2.add('Cooler_water',mode = 'summer' ,d_end=sup_s.d, t1_fluid = 0, t2_fluid = 12, fluid = 'вода')
ahu2.add('Heater_electric',mode = 'summer' ,t_end=sup_s.t)
ahu2.add('Fan_reserved', article='116890/A01', p_tot = 200, p_net = 500)
ahu2.add('Filter', filter_type='кассетный', filter_class = 'F9')
ahu2.add('Humidifier_steam', rh_end=sup_w.rh)
ahu2.add('Flex_joint', w_connection =  1000, h_connection =  1000)
ahu2.set_report_number('123')
ahu2.set_site_name ('Больница')
ahu2.calculate()
write_all_reports(ahu2, report_number=report_number, show=True)


# In[9]:


[(s.name, s.v, s.max_velocity, s.min_width, s.min_height) for s in ahu2.sections]


# In[10]:


l = 1150
oda_w = Air('oda winter', -25., 0.86, l)
oda_s = Air('oda summer',  26., 0.5, l)
sup_w = Air('sup winter',  21., 0.4, l)
sup_s = Air('sup summer',  21., 0.4, l)


# In[11]:


w_connection = 500
h_connection = 300
p_tot = 700
p_net = 300

ahu1=Ahu('В1', oda_s, oda_w, sup_s, sup_w, 'pool', kind='В', frame=25)
ahu1.add('Flex_joint', w_connection =  w_connection, h_connection =  h_connection)
ahu1.add('Fan_reserved', p_net=300, p_tot = 700)
ahu1.add( 'Flex_joint',  w_connection =  w_connection, h_connection =  h_connection)
ahu1.calculate()

write_all_reports (ahu1, report_number=report_number, show=True)


# In[12]:


ahu1.generate_bom()


# In[13]:


[(s.name, s.v, s.max_velocity, s.min_width, s.min_height) for s in ahu1.sections]


# In[ ]:





# In[ ]:




