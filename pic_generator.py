#!/usr/bin/env python
# coding: utf-8

# In[39]:


from PIL import Image
import os


# In[108]:


def append_images(images, direction='horizontal',
                  bg_color=(255,255,255), aligment='center', gap = 0):
    """
    Appends images in horizontal/vertical direction.

    Args:
        images: List of PIL images
        direction: direction of concatenation, 'horizontal' or 'vertical'
        bg_color: Background color (default: white)
        aligment: alignment mode if images need padding;
           'left', 'right', 'top', 'bottom', or 'center'
        gap: gap between images
    Returns:
        Concatenated image as a new PIL image object.
    """
    widths, heights = zip(*(i.size for i in images))

    if direction=='horizontal':
        new_width = sum(widths)+(len(widths)-1)*gap
        new_height = max(heights)
    else:
        new_width = max(widths)
        new_height = sum(heights)+(len(widths)-1)*gap

    new_im = Image.new('RGB', (new_width, new_height), color=bg_color)


    offset = 0
    for im in images:
        if direction=='horizontal':
            y = 0
            if aligment == 'center':
                y = int((new_height - im.size[1])/2)
            elif aligment == 'bottom':
                y = new_height - im.size[1]
            new_im.paste(im, (offset, y))
            offset += im.size[0]+gap
        else:
            x = 0
            if aligment == 'center':
                x = int((new_width - im.size[0])/2)
            elif aligment == 'right':
                x = new_width - im.size[0]
            new_im.paste(im, (x, offset))
            offset += im.size[1]+gap

    return new_im


# In[1]:


def make_ahu_pic (code, basewidth = 800):
    supply =['CAPM', 'CAP']
    recirculator = ['CAR', 'CARM']
    elements = code.split('.')
    ahu_type = elements[0]
    elements = elements[2:]
    
    if ahu_type in supply:
        elements = ['ODA']+elements
        elements = elements +['SUP']
    elif ahu_type in recirculator:
        elements = ['RCA']+elements
        elements = elements +['SUP']        
    else:
        elements = ['ETA']+elements
        elements = elements +['EHA']
    el_pics = []
    for element in elements:
        try:
            fn =  os.path.join('.' ,'templates', 'pic', 'white', element+'.png')
            el_pics.append ( Image.open(fn))
        except:
            print (f'Cant open pic {fn}')
    ahu_pic = append_images(el_pics[:-1], direction='horizontal', bg_color=(255,255,255), aligment='bottom', gap = -5)
    ahu_pic = append_images([ahu_pic,el_pics[-1]], direction='horizontal', bg_color=(255,255,255), aligment='bottom', gap = 0)
    #resizing to width equal basewidth
    wpercent = (basewidth/float(ahu_pic.size[0]))
    hsize = int((float(ahu_pic.size[1])*float(wpercent)))
    ahu_pic = ahu_pic.resize((basewidth,hsize), Image.ANTIALIAS)
    
    
    return ahu_pic     
           


# In[ ]:




