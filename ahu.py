#!/usr/bin/env python
# coding: utf-8

# In[1]:


from sections import Air, Section, Heater, Heater_water, Heater_electric,                     Heater_water_regenerator, Heater_plate_regenerator,                     Cooler, Cooler_water, Cooler_freon,                      Cooler_water_regenerator, Cooler_plate_regenerator,                     Filter, Humidifier, Humidifier_steam,                     Humidifier_adiabatic, Flex_joint, Damper, Silencer, Mixing,                     UV_filter
import os
from fan import Fan, Fan_reserved
from pic_generator import make_ahu_pic
import pandas as pd
import numpy as np
import time
import locale


# In[7]:


class Ahu:
    def __init__(self, name, air_in_s, air_in_w, air_out_s, air_out_w,
                  serie='basic', kind='П',
                  frame='auto',
                  weight=9999,
                  **kwargs ):
        self.name = name
        self.air_in_w = air_in_w
        self.air_in_s = air_in_s
        self.air_out_w = air_out_w
        self.air_out_s = air_out_s
        self.serie = serie
        self.kind = kind
        if frame == 'auto':
            if self.air_in_w.l > 3000:
                self.frame = 45
            else:
                self.frame = 25
        elif frame == 25:
            self.frame = 25
        elif frame == 45:
            self.frame = 45
        else:
            raise ValueError("Допустимые типы рамы 25, 45 или 'auto'.")
        if self.frame == 45:
            self.frame_width = 56
        elif self.frame == 25:
            self.frame_width = 36
        self.sections = []
        self.weight = weight
        self.__dict__.update(kwargs)


    def set_site_name(self, site_name):
        self.site_name = site_name

    def set_report_number(self, report_number):
        self.report_number = report_number

    def add(self, sect_type, **kwargs):
        section = globals()[sect_type](serie=self.serie, **kwargs)
        self.sections.append(section)

# Separate sections by working season
    def mode_list(self):
        self.sections_winter=[]
        self.sections_summer=[]
        for section in self.sections:
            if section.mode == 'winter':
                self.sections_winter.append(section)
            elif section.mode == 'summer':
                self.sections_summer.append(section)

# Initialise sections air_in
    def assignment_air_in(self):

        air_in = self.air_in_w
        for section in self.sections_winter:
            section.set_air_in(air_in)
            section.calculate()
            air_in = section.air_out

        air_in = self.air_in_s
        for section in self.sections_summer:
            section.set_air_in(air_in)
            section.calculate()
            air_in = section.air_out

# Prepearing base characteristics
    def base_characteristics(self):

        l_w = self.air_in_w.l
        t_in_w = self.air_in_w.t
        rh_in_w = self.air_in_w.rh
        if self.sections_winter:
            t_out_w = self.sections_winter[-1].air_out.t
            rh_out_w = self.sections_winter[-1].air_out.rh
        else:
            t_out_w = self.air_in_w.t
            rh_out_w = self.air_in_w.rh

        l_s = self.air_in_s.l
        t_in_s = self.air_in_s.t
        rh_in_s = self.air_in_s.rh
        if self.sections_summer:
            t_out_s = self.sections_summer[-1].air_out.t
            rh_out_s = self.sections_summer[-1].air_out.rh
        else:
            t_out_s = self.air_in_s.t
            rh_out_s = self.air_in_s.rh

        lines = []
        lines.append('\n')
        lines.append('\n## Основные характеристики установки\n')
        lines.append('|Параметр                      |Зима              |Лето               |')
        lines.append('|:-----------------------------| :---------------:| :----------------:|')
        lines.append(f'|Поток (м³/ч)                  |{l_w}             | {l_s}             |')
        lines.append(f'|Температура воздуха вход, °C  |{t_in_w:.1f}      | {t_in_s:.1f}      |')
        lines.append(f'|Влажность воздуха вход, %     |{rh_in_w*100:.1f} | {rh_in_s*100:.1f} |')
        lines.append(f'|Температура воздуха выход, °C |{t_out_w:.1f}     | {t_out_s:.1f}     |')
        lines.append(f'|Влажность воздуха выход, %    |{rh_out_w*100:.1f}| {rh_out_s*100:.1f}|')
        return lines

    def reprt_ender(self):
        lines = []
        lines.append('\n')
        lines.append('\n## Информация о корпусе\n')
        lines.append('|     |     |')
        lines.append('|:--------------|:------------:|')
        lines.append('| Профили корпуса                                       | Анодированный алюминий   |')
        lines.append('| Углы                                                  | Пластмасса               |')
        lines.append('| Материал изоляции                                     | Пенополиуретан           |')
        lines.append('| Толщина (мм) и покрытие внешнего листового металла    | 0.5 Zn RAL 9002(C4)      |')
        lines.append('| Толщина (мм) и покрытие внутреннего листового металла | 0.5 Zn RAL 9002(C4)      |')
        lines.append('| Условия                                               | Для внутренней установки |')
        lines.append('\n')
        lines.append('***В связи с непрерывной работой над улучшением своей                           продукции компания GreenAir сохраняет за собой право изменять как конструкцию,                           так и цены без предварительного уведомления.***')
        return lines

    def reprt_head_table(self):
        code = self.generate_code()
        pic = make_ahu_pic(code)
        pic_fn = os.path.join('.', 'tmp', 'ahu_scheme.png')
        os.makedirs(os.path.dirname(pic_fn), exist_ok=True)
        pic.save(pic_fn)
        lines = []
        lines.append('\n')
        lines.append('|      |        |')
        lines.append('|:-----| ------:|')
        locale.setlocale(locale.LC_TIME, "ru_RU.UTF8")  # russian locale for time format
        if hasattr(self, 'report_number'):
            lines.append(f'|Дата {time.strftime("%d %B %Y г.")}|№ расчета: {self.report_number}|\n')
        else:
            lines.append(f'|Дата {time.strftime("%d %B %Y г.")}|№ расчета: |\n')

        lines.append('\n\n# ТЕХНИЧЕСКОЕ ОПИСАНИЕ ОБОРУДОВАНИЯ\n')

        if hasattr(self, 'site_name'):
            lines.append(f'*Объект: {self.site_name}*')
        else:
            lines.append('*Объект:*')
        lines.append(f'\n\n### Система: {self.name}  \n')
        lines.append(f'Модель: **{self.generate_code()}**  \n\n') 
        lines.append(f'![Схема установки]({pic_fn})'+'{ width=15cm }  \n\n') 
        lines.append(f'Габаритные размеры (+с ножками) (BxHxL, мм): **{self.w_ext} x {self.h_ext} (+200) x {self.lenght}**   ')
        lines.append('**Напольная**, сторона подключения и обслуживания **правая**   ')
        lines.append(f'Масса установки (±10%): **{self.weight} кг**   \n')
        lines.append('**ODA** – Наружный воздух. Атмосферный воздух, поступающий в систему вентиляции и кондиционирования.   ')
        lines.append('**SUP** – Приточный воздух. Воздух, подаваемый в помещение (в систему) после подготовки.   ')
        lines.append('**ETA** – Вытяжной воздух. Воздух, удаляемый из помещения.   ')
        lines.append('**EHA** – Удаляемый воздух. Воздух, удаляемый в атмосферу.   ')
        lines.append('**RCA** – Рециркуляционный воздух. Воздух, забираемый для обработки из помещения.   \n\n')
        return lines       


    def _min_size_calc(self):
        w_min_ahu = h_min_ahu = 0

        for section in self.sections:
            w_min, h_min = section.min_width, section.min_height
            w_min_ahu = max(w_min_ahu, w_min)
            h_min_ahu = max(h_min_ahu, h_min)
        return (w_min_ahu, h_min_ahu)

    def check_size(self, w, h):

        for section in self.sections:
            if not section.check_dimensions(w, h):
                return False

        return True

    def size_calc(self):
        w_h_rate = 2
        step = 50
        panel_width = 1250
        w, h = self._min_size_calc()

        while not self.check_size(w, h):
            if (w < panel_width) and (h < panel_width):
                if w / h > w_h_rate:
                    h += step
                    h = min(h, panel_width)
                else:
                    w += step
                    w = min(w, panel_width)

            elif (w >= panel_width) and (h >= panel_width):
                if w / h > w_h_rate:
                    h += step
                else:
                    w += step

            elif w < panel_width:
                w += step
            else:
                h += step
        self.w_int, self.h_int = w, h
        self.w_ext = self.w_int + self.frame_width*2
        self.h_ext = self.h_int + self.frame_width*2

        #Calculating lenght of AHU
        self.lenght = 0
        self.num_blocks = 1
        self.num_doors = 0
        block_max_len = 1500
        block_len = 0
        for section in self.sections:
            self.lenght += section.lenght
            self.num_doors += section.door
            if (block_len + section.lenght) > block_max_len:
                self.num_blocks += 1
                block_len = 0
            else:
                block_len += section.lenght
        self.lenght += self.num_blocks*self.frame_width*2

    def generate_code(self):
        if self.kind == 'П':
            line = 'CAP'
        if self.kind == 'В':
            line = 'CAV'
        if self.kind == 'Р':
            line = 'CAR'

        if self.serie == 'pure':
            line += 'M'
        line = [line]
        line.append(str(int(np.ceil(self.w_ext/100))) +
                     str(int(np.ceil(self.h_ext/100))))
        for section in self.sections:
            line.append(section.get_code())
        if hasattr(self, 'report_number'):
            line.append(self.report_number)
        line.append(self.name)

        line = '.'.join(line)

        return line

    def generate_md(self):
        lines = []
        lines += self.reprt_head_table()
        lines += self.base_characteristics()
        for section in self.sections:
            lines += section.generate_md()
        lines += self.reprt_ender()
        return lines

    def calculate_case (self):
        PRICE_INC_RATE = 1.2
        door_width = 300
        base_frame = (((self.w_ext + self.h_ext) * 2) * self.num_blocks * 2 + self.lenght * 4)/1e3*PRICE_INC_RATE
        if not hasattr(self, 'thermal_brake'):
            if self.sections[0].air_in.t < -20:
                self.thermal_brake=True
            else:
                self.thermal_brake=False
            # lenght of thermal brake frames as sum of first ring and four 1 meter sides frame
        if self.thermal_brake:
            tb_frame = ((self.w_ext + self.h_ext) * 2 + 4*1000) /1e3*PRICE_INC_RATE
            base_frame -= tb_frame
        else:
            tb_frame = 0
        doors_area = self.num_doors * self.h_ext * door_width / 1e6
        panel = (self.lenght * (self.w_ext + self.h_ext) * 2 + self.w_ext * self.h_ext)/1e6*PRICE_INC_RATE - doors_area
        df = pd.DataFrame()
        if self.frame == 45:
            df.loc['Плита ППУ 45 мм','qty'] = panel
            df.loc['Профиль основной 45 мм','qty'] = base_frame
            if tb_frame > 0:
                df.loc['Профиль основной 45 мм ТБ','qty'] = tb_frame
            df.loc['Профиль блокировочный','qty'] = (base_frame + tb_frame) * 1.3
            df.loc['Уголок пластиковый 45 мм','qty'] = self.num_blocks * 8
            df.loc['Профиль омега 45 мм','qty'] = self.num_doors * self.h_ext / 1e3
            df.loc['Соединитель омега 45 мм','qty'] = self.num_doors *2
            df.loc['Рукоятка запорная','qty'] = self.num_doors * min(2, self.h_ext//500) *2

        if self.frame == 25:
            df.loc['Плита ППУ 25 мм','qty'] = panel
            df.loc['Профиль основной 25 мм','qty'] = base_frame + tb_frame
            df.loc['Профиль блокировочный','qty'] = (base_frame + tb_frame) * 1.3
            df.loc['Уголок пластиковый 25 мм','qty'] = self.num_blocks * 8
            df.loc['Профиль омега 25 мм','qty'] = self.num_doors * self.h_ext / 1e3
            df.loc['Соединитель омега 25 мм','qty'] = self.num_doors * 2
            df.loc['Петля черная нейлоновая','qty'] = self.num_doors * min(2, self.h_ext//500) *2
        df.loc['Ножки 200 мм','qty'] = self.num_blocks * 4

        return df

    def generate_bom(self):
        df = pd.DataFrame()
        for s in self.sections:
            s.prepear_bom()
            df1 = pd.DataFrame.from_dict(s.bom, orient='index')
            df = df.append (df1)
        df = df.append (self.calculate_case())
        return df

    def calculate(self):
        self.mode_list()
        self.assignment_air_in()
        self.size_calc()


# In[ ]:




