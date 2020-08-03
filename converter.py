#!/usr/bin/env python
# coding: utf-8

# In[1]:


from markdown import markdown
from IPython.core.display import HTML
import weasyprint as wp
import pypandoc
import os
from cost_calc import calc_price


# In[33]:


def get_report (fn):
    f = open(fn, 'r')
    characteristics = f.read()
    
    fn = './templates/ender.md'
    f = open(fn, 'r')
    ender = f.read()

    report = characteristics + ender
    return report


# In[29]:


#htmlmarkdown = markdown(report , extensions=['markdown.extensions.tables'])
#display(HTML(htmlmarkdown))


# In[30]:


def write_pdf (htmlmarkdown, fn):
    # HTML('<h1>foo') would be filename
    report_wp = wp.HTML(string=htmlmarkdown)
    wp.CSS(string='@page { size: A4; margin: 1cm }')
    report_wp.write_pdf(fn)


# output = pypandoc.convert_text(htmlmarkdown, format = 'html', to='docx', outputfile="./output/П1.docx",
#                               extra_args=['--reference-doc=./templates/cust.docx'])
# assert output == ""

# In[3]:


def write_odt (report, fn):
    output = pypandoc.convert_text (report, format = 'md', to = 'odt', outputfile=fn,
                                  extra_args=['--reference-doc=./templates/cust.odt'])
    assert output == ""


# In[ ]:


def write_all_reports(ahu, report_number='test', show=False):
    report = ahu.generate_md()
    report = '\n'.join(report)
    htmlmarkdown = markdown(report, extensions=['markdown.extensions.tables'])

    fn = os.path.join('.', 'output', report_number, ahu.name)
    os.makedirs(os.path.dirname(fn), exist_ok=True)

    write_odt(report, fn+'.odt')
    #write_pdf(htmlmarkdown, fn+'.pdf')
    bom_df = ahu.generate_bom()
    #bom_df.to_excel(fn+'.xlsx')
    calc_price(bom_df).to_excel(fn+'_price.xlsx')
    if show:
        display(HTML(htmlmarkdown))

