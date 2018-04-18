from kivy.config import Config
Config.set('graphics', 'fullscreen','auto')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.graphics import Line, Rectangle, Color
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.video import Video
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.base import EventLoop
from kivy.core.text import Label as CoreLabel

import pandas as pd
import math
#import objgraph
#import cProfile
#import pdb
import time
import filetype
from socket import *

class PopupVideo(Video):

    def on_texture(self, temp1, temp2):
        anim = Animation(opacity=1, duration=0.5)
        anim.start(self)

    def __init__(self, **args):
        super(PopupVideo, self).__init__(**args)
        self.opacity = 0

class TimeLabel(Label):

    def __init__(self, time, unit, font_name, font_size, font_color, **kwargs):
        super(TimeLabel, self).__init__(**kwargs)
        
        self.time = time
        if unit == '':
            self.unit = unit
        else:
            self.unit = ' ' + unit
        self.text = str(round(time)) + self.unit
        self.center_x = 0
        self.font_size = font_size
        self.valign = 'middle'
        self.font_name = font_name
        self.color = (font_color[0],font_color[1],font_color[2],font_color[3])
        pos_hint = {'center_y': 0.5}
               
class Overlay(StackLayout):

    # This is a template overlay the needs to be subclassed to work.

    def show_content(self, title, media, text):
        print('Overlay.show_content()')
        self.title_label.text = title
        # Create an invisible, one-line label to measure the amount of text 
        temp_text = CoreLabel(text=title, size_hint=(1,1),
            font_size=self.title_label.font_size, valign='center', markup=True, opacity=0, disabled=True)           
        temp_text.refresh()   
        self.title_label.height = temp_text.content_size[1]

        self.media_source = media
        self.text_widget.text = text
        
        # Disable background buttons
        for item in self.parent.active_items:
            item.disabled = True
       
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.disabled = False
        self.parent.active_overlay = self
    
    def hide_content(self, *args):
        print('Overlay.hide_content()')
                
        # Re-enable background buttons
        for item in self.parent.active_items:
            item.disabled = False
            
        self.pos_hint = {'center_x': 0.5, 'center_y': -1.}
        self.disabled = True
        self.parent.active_overlay = None

    def draw(self, *args, no_resize=False):
        print('Overlay.draw(), no_resize='+str(no_resize))
        if not no_resize:
            app = App.get_running_app()
            self.width = app.root_window.width*0.5
            self.height = app.root_window.height*0.75

        self.canvas.before.clear()
        with self.canvas.before:
            # Fade out things behind the overlay
            if self.disabled == False:
                Color(0,0,0,0.5)
                self.back_rect = Rectangle(pos=self.parent.parent.pos, size=self.parent.parent.size)
            # Draw overlay background
            col = self.options['background_color']
            Color(col[0], col[1], col[2], col[3])
            self.rect = Rectangle(pos=self.pos, size=self.size)
            
    def make_visible(self, *args):
        self.opacity = 1

    def update_size(self, *args):
        print('Overlay.update_size()')
        self.height =   self.title_label.height + \
                        self.content_container.height + \
                        self.dismiss_button.height
                        
    def on_state(self, *args):
    
        # Change the color of the button when it's pressed
    
        state = self.dismiss_button.state
        if state == 'normal':
            self.dismiss_button.background_color = self.options['button_normal_color']
        else:
            self.dismiss_button.background_color = self.options['button_down_color']
        

    
    def __init__(self, options, **kwargs):

        super(Overlay, self).__init__(**kwargs)
        
        self.options = options
        self.orientation = 'tb-lr'
        self.spacing = 0
        self.size_hint = (None, None)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        
        self.media_source = ''
        
        self.title_label = Label(size_hint=(1,None),
                                    font_size=options['title_font_size'],
                                    font_name=options['title_font_name'],
                                    color=options['title_font_color'],
                                    markup=True,
                                    valign='center',
                                    halign='center')
                                    
        self.add_widget(self.title_label)
               
        self.content_container = BoxLayout(orientation='horizontal', size_hint = (1,None))
        self.add_widget(self.content_container)
        
        self.dismiss_button = Button(text='Go back',
                                        font_size = options['button_font_size'],
                                        color = options['button_font_color'],
                                        font_name = options['button_font_name'],
                                        size_hint = (1,None),
                                        background_normal='',
                                        background_down='',
                                        background_color=options['button_normal_color'],
                                        on_release=self.hide_content)
        
        self.dismiss_button.bind(state=self.on_state)
        self.dismiss_button.height = 2*self.dismiss_button.font_size
        self.add_widget(self.dismiss_button)

        self.bind(pos=self.draw)

class TextOverlay(Overlay):

    def show_content(self, title, text):
        self.opacity = 0
        super(TextOverlay, self).show_content(title, None, text)
        Clock.schedule_once(self.make_visible)

    def draw(self, *args):
    
        # Create an invisible, one-line label to measure the amount of text 
        temp_text = CoreLabel(text=self.text_widget.text, size_hint=(0.45,1),
            font_size=self.text_widget.font_size, valign='center', markup=True, opacity=0, disabled=True)           
        temp_text.refresh()
        
        text_height = temp_text.content_size[1]
        text_width = temp_text.content_size[0]
        text_area = text_height*text_width#*1.25 # Scale factor to account for line spacing
        
        self.content_container.height = ((2*text_area/3.)**.5)
        self.width = 1.5*self.height
    
        super(TextOverlay, self).draw(*args, no_resize=True)
        
        # Update the text box size once everything is redrawn 
        Clock.schedule_once(self.update_size)       

    def update_size(self, *args):
        
        # Function to refresh the size of the textbox. Called automatically after the
        # overlay is redrawn.
    
        self.text_widget.text_size = (0.95*self.text_widget.size[0],0.95*self.text_widget.size[1])
        super(TextOverlay, self).update_size(self, *args)
        
    def __init__(self, options, **kwargs):
    
        super(TextOverlay, self).__init__(options, **kwargs)
        
        self.text_widget = Label(text='', 
                                    size_hint=(1,1),
                                    font_size=options['body_font_size'],
                                    font_name=options['body_font_name'],
                                    color=options['body_font_color'],
                                    valign='center',
                                    markup=True)
        self.content_container.add_widget(self.text_widget)
        
class ImageOverlay(Overlay):

    def show_content(self, title, media, text):
        #print('------------')
        #print('ImageOverlay.show_content()')
        self.opacity = 0
        super(ImageOverlay, self).show_content(title, media, text)
        self.image_widget.source = 'media/'+media
        self.image_widget.reload()
        Clock.schedule_once(self.make_visible)
        
    def draw(self, *args, no_resize=False):
        #print('ImageOverlay.draw(no_resize='+str(no_resize)+')')
        # Create an invisible, one-line label to measure the amount of text 
        temp_text = CoreLabel(text=self.text_widget.text, size_hint=(0.45,1),
            font_size=self.text_widget.font_size, valign='center', markup=True, opacity=0, disabled=True)           
        temp_text.refresh()

        image_ratio = self.image_widget.image_ratio
        text_height = temp_text.content_size[1]
        text_width = temp_text.content_size[0]
        
        # Do some math to balance the size of the image and text blurb
        k = text_height*text_width*1.25 # Scale factor to account for line spacing
        self.content_container.height = ((k/image_ratio)**.5)
        # The following line assumes the image and text each take up .45 of the overlay
        self.width = (image_ratio*((k/image_ratio)**.5))/0.45      
        #self.height = 700
        # Update the text box size once everything is redrawn 
        #Clock.schedule_once(self.update_text_size)
        Clock.schedule_once(self.update_size)
        
        super(ImageOverlay, self).draw(*args, no_resize=True)

    def update_size(self, *args):
        #print('ImageOverlay.update_size()')
        # Function to refresh the size of the textbox. Called automatically after the
        # overlay is redrawn.
    
        self.text_widget.text_size = self.text_widget.size
        super(ImageOverlay, self).update_size(self, *args)

        
    def __init__(self, options, **kwargs):
    
        super(ImageOverlay, self).__init__(options, **kwargs)
        
        # Lay out the content container with an image and text
        image_width = 0.45
        text_width = 0.45
        spacer_width = (1. - image_width - text_width)/3.
        
        spacer1 = Label(text='', size_hint=(spacer_width,1))
        self.content_container.add_widget(spacer1)        
        
        self.image_widget = Image(source='', size_hint=(image_width,1), allow_stretch=True)
        self.content_container.add_widget(self.image_widget)
        
        spacer2 = Label(text='', size_hint=(spacer_width,1))
        self.content_container.add_widget(spacer2)
        
        self.text_widget = Label(text='This is temporary text',
                                size_hint=(text_width,1),
                                font_size=options['body_font_size'],
                                font_name=options['body_font_name'],
                                color=options['body_font_color'],
                                valign='center',
                                markup=True)
        self.content_container.add_widget(self.text_widget)
        
        spacer3 = Label(text='', size_hint=(spacer_width,1))
        self.content_container.add_widget(spacer3)        
        
class VideoOverlay(Overlay):
    
    def __init__(self, options, **kwargs):
    
        super(VideoOverlay, self).__init__(options,**kwargs)
        
class Item(StackLayout):  

    def more_info(self, *args):
        if self.media_type == 'image':
            self.parent.image_overlay.show_content(self.title_text, self.media_source, self.long)
        elif self.media_type == 'none':
            self.parent.text_overlay.show_content(self.title_text, self.long)
            
    def on_size(self, *args):
        # Recomputes the size of the widget when the window changes
        pass
        
    def draw(self, *args):
        # Redraws the item's background when it moves
                
        if self.media_type == 'image':
            self.body_text.text_size = (self.body_text.width, None)
            #self.body_image.width = self.body_container.width*0.45
            self.body_container.height = max(self.body_text.texture_size[1], 
                                             self.body_image.width/self.body_image.image_ratio)
        else:
            self.body_text.text_size = (self.body_text.width*0.933, None)
            self.body_container.height = self.body_text.texture_size[1]
            
        self.height =   self.title.height + \
                        self.body_container.height + \
                        self.more.height + \
                        10 # accounts for spacer

        app = App.get_running_app()
        self.target = app.root_window.height/2.

        self.canvas.before.clear()
        with self.canvas.before:
            # Draw the connecting line
            col = self.options['line_color']
            Color(col[0], col[1], col[2], col[3])
            self.line = Line(points=[self.center_x, self.center_y, self.center_x, self.target], width=3)
            # Draw the background
            col = self.options['background_color']
            Color(col[0], col[1], col[2], col[3])
            self.rect = Rectangle(pos=self.pos, size=self.size)
        
        #if self.body.texture != None:
            #self.body.texture.mag_filter = 'linear'
            
    def on_state(self, *args):
    
        # Change the color of the button when it's pressed
    
        state = self.more.state
        if state == 'normal':
            self.more.background_color = self.options['button_normal_color']
        else:
            self.more.background_color = self.options['button_down_color']
        
    def __init__(self, name, time, unit, rank, short, long,
                    media, options, **kwargs):
        super(Item, self).__init__(**kwargs)
        self.options = options
        self.target = 0 # must be before pos   
        self.size_hint = (0.2, None)
        self.pos_hint = {'top': 0.45}
        self.orientation = 'tb-lr'
        self.slot = 'bottom'
        self.spacing = 0
        self.center_x = 0
        self.color = (1, 1, 1, 1)
        self.text = short
        self.short = short
        self.long = long
        if self.long == '':
            self.no_overlay = True
        else:
            self.no_overlay = False
        self.title_text = name
        self.time = time
        if unit == '':
            self.unit = ''
        else:
            self.unit = ' ' + unit
        self.rank = rank
        self.media_source = media
        if media != '':
            kind = filetype.guess('media/'+media)
            if kind is not None:
                type = kind.mime[0:5]
                if type == 'image':
                    self.media_type = 'image'
                elif type == 'video':
                    self.media_type = 'video'
                else:
                    self.media_type = 'none'
                    print('Error: file ' + media + ' is of an unsupported type')
            else:
                self.media_type = 'none'
        else:
            self.media_type = 'none'
                
        self.title = Label(text=str(round(time))+self.unit,
                            size_hint=(1,None),
                            font_name=options['title_font_name'],
                            font_size=options['title_font_size'],
                            color=options['title_font_color'],
                            markup=True)
        self.title.height = self.title.font_size*1.5
            
        self.body_container = BoxLayout(orientation='horizontal',
                                        size_hint=(1,None))
        
        if self.media_type != 'image': # Display only text on main timeline
            
            self.body_text = Label(text=self.text,
                                    font_name=options['body_font_name'],
                                    font_size=options['body_font_size'],
                                    color=options['body_font_color'],
                                    markup=True)
            self.body_container.add_widget(self.body_text)
            
        else: # Display image and text on main timeline       
            # Lay out the content container with an image and text
            image_width = 0.45
            text_width = 0.45
            spacer_width = (1. - image_width - text_width)/3.
            
            spacer1 = Label(text='', size_hint=(spacer_width,1))
            
            self.body_text = Label(text=self.text,
                                    font_name=options['body_font_name'],
                                    font_size=options['body_font_size'], 
                                    color=options['body_font_color'],
                                    markup=True, 
                                    size_hint = (text_width, 1))
                        
            spacer2 = Label(text='', size_hint=(spacer_width,1))
            self.body_image = Image(source='media/'+self.media_source, 
                                size_hint=(image_width,1), allow_stretch=True)
                                
            spacer3 = Label(text='', size_hint=(spacer_width,1))
            
            self.body_container.add_widget(spacer1)
            self.body_container.add_widget(self.body_text)
            self.body_container.add_widget(spacer2)            
            self.body_container.add_widget(self.body_image)
            self.body_container.add_widget(spacer3)
        
        self.more = Button(text='Tap to learn more',
                            size_hint=(1,None),
                            font_name=options['button_font_name'],
                            font_size=options['button_font_size'],
                            color=options['button_font_color'],
                            background_normal='',
                            background_down='',
                            background_color=options['button_normal_color'],
                            on_release=self.more_info)
        self.more.height = 2*self.more.font_size
        self.more.bind(state=self.on_state)
                
        self.add_widget(self.title)
        self.add_widget(self.body_container)
        self.add_widget(Label(size_hint=(1,None), height=10)) # Spacer
        if not self.no_overlay: # Hide the learn more button if there's no overlay to show
            self.add_widget(self.more)
        
        self.bind(pos=self.draw)
        
class LineWidget(Widget):

    def draw(self, *args):
        with self.canvas:
            # Draw the line
            Color(self.color[0], self.color[1], self.color[2], self.color[3])
            self.line = Rectangle(pos=(0, self.height/2.-20),
                                    size=(self.width, 40))

    def __init__(self, color, *args):
        super(LineWidget, self).__init__(*args)
        self.color = color
        self.size_hint = (1,1)
        self.pos_hint = {'center.x': 0.5, 'center_y': 0.5}
        self.bind(size=self.draw)

class Timeline(FloatLayout):  
    
    items = list() # Holds the widgets for each item on the timeline
    active_items = list() # Only those widgets with opacity > 0
    neighbors = list() # Each element is a list of the closest widgets for the corresponding item
    labels = list() # Holds the time labels
    label_sep = 0.2 # Fraction of the screen between labels
    active_overlay = None # holds the name of the active overlay, if it exists
    
    def add_item(self, item):
            
        item.center_x = (item.time - self.time_window_left)/self.time_window_size*self.width
        self.add_widget(item)
        self.items.append(item)
        
    def add_label(self, label):
        
        label.center_x = (label.time - self.time_window_left)/self.time_window_size*self.width
        self.add_widget(label)
        self.labels.append(label)
                
    def position(self, full=False):
        
        # Function to place items and labels on the timeline in their correct position
        # full=True is only needed when we've moved things vertically
        
        if full:
            for item in self.items:
                # Place horizontally
                item.center_x = (item.time - self.time_window_left)/self.time_window_size*self.width
                
                # Place vertically
                if item.opacity > 0: # The widgets we want to show
                    if item.slot == 'top':
                        item.pos_hint = {'y': 0.55}
                    else:
                        item.pos_hint = {'top': 0.45}
                else: # Hide other widgets off the screen so they don't steal touch
                    item.pos_hint = {'top': -.1}
                    
        else:
            for item in self.active_items:
                # Place horizontally
                item.center_x = (item.time - self.time_window_left)/self.time_window_size*self.width
                
        for label in self.labels:
            # Place horizontally
            label.center_x = (label.time - self.time_window_left)/self.time_window_size*self.width
            if label.center_x < 0 or label.center_x > self.width:
                self.translate_label(label)

        self.check_labels()
    
    def refresh_items(self, *args):
        self.arrange_items()
        for item in self.items:
            item.draw()
        
    def check_labels(self):
    
        # Rapid swiping combined with translate_label() can result in labels
        # that are too close together. Zooming in/out will also misplace labels
    
        shift_list = self.labels[1:]+self.labels[:1]
        error = False
        for i in range(len(self.labels)):
            if abs(self.labels[i].time - shift_list[i].time) < 0.17*abs(self.time_window_size):
                error = True
        if error:
            for i in range(len(self.labels)):
                time = self.time_window_left+(2*i+1)/10.*self.time_window_size
                self.labels[i].time = time
                self.labels[i].text = str(round(time)) + self.labels[i].unit
    
    def translate_label(self, label):
        
        # Function called if label slides off the screen
        
        if self.reversed == 'True':
            if label.time < self.time_window_right:
                label.time = self.time_window_left
            elif label.time > self.time_window_left:
                label.time = self.time_window_right

        else:        
            if label.time > self.time_window_right:
                label.time = self.time_window_left
            elif label.time < self.time_window_left:
                label.time = self.time_window_right
            
        label.center_x = (label.time - self.time_window_left)/self.time_window_size*self.width
        label.text = str(round(label.time)) + label.unit

        self.check_labels()
    
    def arrange_items(self, *args):
        # Function to lay out the items so that they don't block each other
        
        x_list = list()
        width_list = list()
        slot_list = list()
        opacity_list = list()
        self.active_items = list() # Reset the active items
        
        # Start everything visible and in a line        
        for item in self.items:
            item.opacity = 1
            item.disabled = False
            x_list.append(item.x)
            width_list.append(item.width)
            slot_list.append(item.slot)
            opacity_list.append(item.opacity)
        
        # First arrange them top/bottom to resolve collisions
        for i in range(len(x_list)-1):
            for j in range(i+1,len(x_list)):
                col = False
                if slot_list[i] == slot_list[j]: # Objects in different slots don't collide
                    if x_list[i] <= x_list[j] and (x_list[i]+width_list[i]) > x_list[j]:
                        col = True
                    elif x_list[j] <= x_list[i] and (x_list[j]+width_list[j]) > x_list[i]:
                        col = True
                if col:
                    if slot_list[j] == 'top':
                        slot_list[j] = 'bottom'
                    else:
                        slot_list[j] = 'top'
        
        # If that's not enough, selectively hide them
        for i in range(len(x_list)-1):
            if opacity_list[i] > 0: # Hidden items don't get a vote
                for j in range(i+1,len(x_list)):
                    col = False
                    if slot_list[i] == slot_list[j]:
                        if x_list[i] < x_list[j] and (x_list[i]+width_list[i]) > x_list[j]:
                            col = True
                        elif x_list[j] < x_list[i] and (x_list[j]+width_list[j]) > x_list[i]:
                            col = True
                    if col:
                        opacity_list[j] = 0
                                
        bound_left = self.time_window_left - self.time_window_size/2.
        bound_right = self.time_window_right + self.time_window_size/2.        
        for i in range(len(x_list)):
            self.items[i].slot = slot_list[i]
            self.items[i].opacity = opacity_list[i]
            if bound_left < self.items[i].time < bound_right and self.items[i].opacity > 0:
                self.active_items.append(self.items[i])
        
        self.position(full=True)
        
    def translate_line(self, frac):
        
        # Function to handle slding left/right on the timeline
        # frac is the distance to slide in fraction of window width

        trans_mag = frac*self.time_window_size
        temp_left = self.time_window_left - trans_mag
        temp_right = self.time_window_right - trans_mag

        t_per_px = self.time_window_size/self.width
        item_half_size = self.width*0.1*t_per_px
        
        if self.reversed == 'True':
            if temp_left < self.time_start - item_half_size and\
            temp_right > self.time_stop+item_half_size: # Not outside the bounds
                # Update the timeline parameters
                self.time_window_left = temp_left
                self.time_window_right = temp_right
                self.time_window_size = self.time_window_right - self.time_window_left
                # Cull items not on or near the screen to improve performance
                bound_left = self.time_window_left - self.time_window_size/2.
                bound_right = self.time_window_right + self.time_window_size/2.
                self.active_items = list()
                for item in self.items:
                    if bound_left > item.time > bound_right and item.opacity > 0:
                        self.active_items.append(item)
                self.position()
        else:        
            if temp_left > self.time_start - item_half_size and\
            temp_right < self.time_stop+item_half_size: # Not outside the bounds
                # Update the timeline parameters
                self.time_window_left = temp_left
                self.time_window_right = temp_right
                self.time_window_size = self.time_window_right - self.time_window_left
                # Cull items not on or near the screen to improve performance
                bound_left = self.time_window_left - self.time_window_size/2.
                bound_right = self.time_window_right + self.time_window_size/2.
                self.active_items = list()
                for item in self.items:
                    if bound_left < item.time < bound_right and item.opacity > 0:
                        self.active_items.append(item)
                self.position()
                
    def scale_line(self, dist, center):
    
        # Funciton to handle zooming in and zooming out
    
        dist_frac = dist/self.width # Fraction of screen change
        dist_years = abs(self.time_window_size*dist_frac)*2 # Change factor to change scaling speed
        lean = 1 - center/self.parent.width # Fraction of distance to add to each side
        
        
        if self.reversed == 'True':
        
            if dist > 0: # Zoom out
                temp_left = self.time_window_left + (1-lean)*dist_years
                temp_right = self.time_window_right  - lean*dist_years
            else: # Zoom in
                temp_left = self.time_window_left - (1-lean)*dist_years
                temp_right = self.time_window_right  + lean*dist_years
            
            t_per_px = self.time_window_size/self.width
            item_half_size = self.width*0.1*t_per_px

            if temp_left > temp_right and \
                    temp_left < self.time_start - item_half_size and\
                    temp_right > self.time_stop+item_half_size and \
                    abs(temp_right - temp_left) > self.time_window_min:
                self.time_window_left = temp_left
                self.time_window_right = temp_right
                self.time_window_size = self.time_window_right - self.time_window_left            
                self.arrange_items()
        else:
        
            if dist > 0: # Zoom out
                temp_left = self.time_window_left - (1-lean)*dist_years
                temp_right = self.time_window_right  + lean*dist_years
            else: # Zoom in
                temp_left = self.time_window_left + (1-lean)*dist_years
                temp_right = self.time_window_right  - lean*dist_years
            
            t_per_px = self.time_window_size/self.width
            item_half_size = self.width*0.1*t_per_px
        
            if temp_left < temp_right and \
                    temp_left > self.time_start - item_half_size and\
                    temp_right < self.time_stop+item_half_size and \
                    (temp_right - temp_left) > self.time_window_min:
                self.time_window_left = temp_left
                self.time_window_right = temp_right
                self.time_window_size = self.time_window_right - self.time_window_left            
                self.arrange_items()

    def draw(self, *args):
    
        with self.canvas.before:
            # Draw the background
            col = self.options['background_color']
            Color(col[0],col[1],col[2],col[3])
            self.back_rect = Rectangle(pos=self.pos, size=self.size, source='test.png')

            # Draw the line
            # Color(1,1,1,1)
            # self.line = Rectangle(pos=(0, self.height/2.-20),
                                    # size=(self.width, 40))
            
    def __init__(self, options, **kwargs):
        super(FloatLayout, self).__init__(**kwargs)

        self.options = options
        self.reversed = options['reverse_time']
        self.size_hint = (1,1)
        self.center_y = self.height/2.
        
        # Set up the timeline parameters
        self.time_start = options['time_start'] # The earliest possible date
        self.time_stop = options['time_stop'] # The latest possible date
        self.time_window_left = options['time_window_left'] # Date of left edge of window
        self.time_window_right = options['time_window_right'] # Date of right edge of window
        self.time_window_min = options['time_window_min'] # Least amount of time the line can show
        self.time_window_size = self.time_window_right - self.time_window_left
        
        # Load the background image, if there is one
        if self.options['background_source'] is not '':
            self.background_image = Image(source='media/'+self.options['background_source'],
                                            size_hint=(1,1),
                                            pos_hint={'center_x': 0.5, 'center_y': 0.5},
                                            allow_stretch=True)
            self.add_widget(self.background_image)

        # Add in the horizontal line
        self.add_widget(LineWidget(options['line_color']))
        
        self.title = Label(text = options['title'],
                            size_hint = (1,0.1),
                            pos_hint = {'center_x': 0.5, 'top': 0.99},
                            font_size = options['title_font_size'],
                            font_name = options['title_font_name'],
                            color = options['title_font_color'])                            
        self.add_widget(self.title)
        
        self.subtitle = Label(text = options['subtitle'],
                            size_hint = (1,0.1),
                            pos_hint = {'center_x': 0.5, 'y': 0.01},
                            font_size = options['subtitle_font_size'],
                            font_name = options['subtitle_font_name'],
                            color = options['subtitle_font_color'])                            
        self.add_widget(self.subtitle)
        
        self.bind(size=self.draw)

class TimelineScreen(Screen):
    # This screen holds the main timeline. It is responsible for parsing detected
    # touches to determine if pinch-to-zoom or scrolling is happening. The rest of
    # this screen is setup in the kv file.
    
    start = 0
    active_touch = list()
    
    def on_touch_down(self, touch):
    
        if self.parent.screen.timeline.active_overlay is None: # Can only move when no overlay is up        
            if self.timeline.active_overlay is None: # Can't manipulate the timeline is overlay is up
                if len(self.active_touch) < 2:
                    self.active_touch.append(touch)
                    if len(self.active_touch) == 2:
                        self.pinch_start = abs(self.active_touch[0].x - self.active_touch[1].x)           
        
        super(Screen, self).on_touch_down(touch)
                       
    def on_touch_move(self, touch):

        if self.parent.screen.timeline.active_overlay is None: # Can only move when no overlay is up        
            if len(self.active_touch) > 0: 
                if touch is self.active_touch[0]:
                    trans = touch.x - touch.px
                    self.timeline.translate_line(trans/float(self.timeline.width))
                    
                if touch in self.active_touch and len(self.active_touch) == 2:
                    cur_pinch = math.sqrt((self.active_touch[0].x - self.active_touch[1].x)**2  +\
                        (self.active_touch[0].y - self.active_touch[1].y)**2)
                    old_pinch = math.sqrt((self.active_touch[0].px - self.active_touch[1].px)**2  +\
                        (self.active_touch[0].py - self.active_touch[1].py)**2)
                    center = (self.active_touch[0].x + self.active_touch[1].x)/2.
                    self.timeline.scale_line(old_pinch - cur_pinch, center)   
                
        super(Screen, self).on_touch_move(touch)
        
    def on_touch_up(self, touch):
    
        if self.parent.screen.timeline.active_overlay is None: # Can only move when no overlay is up    
            if len(self.active_touch) > 0:
                if touch in self.active_touch:
                    self.active_touch.remove(touch)
        else: # Dismiss the overlay if you tap outside it
            if not self.parent.screen.timeline.active_overlay.collide_point(touch.x, touch.y):
                self.parent.screen.timeline.active_overlay.hide_content()
                
        # Catch problems where we lose track of the number of active touches
        if len(EventLoop.touches) == 0 and len(self.active_touch) != 0:
            self.active_touch = list()
        
        super(Screen, self).on_touch_up(touch)
                   
class ScreenManagement(ScreenManager):
    
    item_options = {'title_font_size': 28,
                    'title_font_name': 'Roboto-Bold.ttf',
                    'title_font_color': (1,1,1,1),
                    'body_font_size': 24,
                    'body_font_name': 'Roboto-Regular.ttf',
                    'body_font_color': (1,1,1,1),
                    'button_font_size': 24,
                    'button_font_name': 'Roboto-Regular.ttf',
                    'button_font_color': (1,1,1,1),
                    'button_normal_color': (145./255,52./255,52./255, 1),
                    'button_down_color': (81./255,28./255,28./255,1),
                    'line_color': (1,1,1,1),
                    'background_color': (52./255,75./255,145./255,1)}    
                    
    overlay_options = {'title_font_size': 28,
                        'title_font_name': 'Roboto-Bold.ttf',
                        'title_font_color': (1,1,1,1),
                        'body_font_size': 24,
                        'body_font_name': 'Roboto-Regular.ttf',
                        'body_font_color': (1,1,1,1),
                        'button_font_size': 24,
                        'button_font_name': 'Roboto-Regular.ttf',
                        'button_font_color': (1,1,1,1),
                        'button_normal_color': (145./255,52./255,52./255, 1),
                        'button_down_color': (81./255,28./255,28./255,1),
                        'background_color': (52./255,75./255,145./255,1)}
                    
    timeline_options = {'filename': '',
                        'reverse_time': 'False',
                        'background_color': (0,0,0,1),
                        'background_source': '',
                        'line_color': (1,1,1,1),
                        'label_font_color': (0,0,0,1),
                        'label_font_size': 35,
                        'label_font_name': 'Roboto-Bold.ttf',
                        'title': '',
                        'title_font_size': 75,
                        'title_font_name': 'Roboto-Bold.ttf',
                        'title_font_color': (1,1,1,1),'title': '',
                        'subtitle': '',
                        'subtitle_font_size': 75,
                        'subtitle_font_name': 'Roboto-Bold.ttf',
                        'subtitle_font_color': (1,1,1,1),
                        'time_start': 1900,
                        'time_stop': 2000,
                        'time_window_left': 1900,
                        'time_window_right': 2000,
                        'time_window_min': 0,
                        'time_unit': ''}
    
    def check_in(self, *args):
    
        # Function to broadcast a UDP packet confirming that it's active
        
        s = socket(AF_INET, SOCK_DGRAM)
        s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        s.sendto(b'timeline',  ('255.255.255.255', 12345))
    
    def setup(self):
        self.get_config()
        self.screen = TimelineScreen()
        self.screen.timeline = Timeline(self.timeline_options)
        self.screen.add_widget(self.screen.timeline)
        
        self.add_widget(self.screen)
        Clock.schedule_once(self.populate_timeline)
        self.check_in()
        Clock.schedule_interval(self.check_in, 60) # Once per mintue
    
    def set_time_range(self, value1, value2):
    
        # Function to set the start and stop times for the timeline
    
        if self.timeline_options['reverse_time'] == 'True': # Larger numbers mean older time
            self.timeline_options['time_start'] = max(value1, value2)
            self.timeline_options['time_stop'] = min(value1, value2)
        else: # Larger numbers mean newer ("normal" timeline)
            self.timeline_options['time_start'] = min(value1, value2)
            self.timeline_options['time_stop'] = max(value1, value2)  
            
    def set_start_range(self, value1, value2):
    
        # Function to set the initial left and right edges of the screen
    
        if self.timeline_options['reverse_time'] == 'True': # Larger numbers mean older time
            self.timeline_options['time_window_left'] = max(value1, value2)
            self.timeline_options['time_window_right'] = min(value1, value2)
        else: # Larger numbers mean newer ("normal" timeline)
            self.timeline_options['time_window_left'] = min(value1, value2)
            self.timeline_options['time_window_right'] = max(value1, value2)
    
    def get_config(self):
        # Function to parse arguments from a configuration file
        # dt passed by clock. We ignore it
        
        options_set = list()

        try:
            with open('config.conf', 'r') as f:
                for line in f:

                    # Item options
                    if line[0:21].lower() == 'item_title_font_size:':
                        self.item_options['title_font_size'] = int(line[21:].strip())
                        options_set.append('item_title_font_size:')
                        
                    if line[0:21].lower() == 'item_title_font_name:': 
                        self.item_options['title_font_name'] = line[21:].strip()
                        options_set.append('item_title_font_name:')
                        
                    if line[0:22].lower() == 'item_title_font_color:': 
                        s = line[22:].strip().split(',')
                        self.item_options['title_font_color'] = (float(s[0])/255,
                                                                float(s[1])/255,
                                                                float(s[2])/255,
                                                                1)
                        options_set.append('item_title_font_color:')
                                                                
                    if line[0:20].lower() == 'item_body_font_size:': 
                        self.item_options['body_font_size'] = int(line[20:].strip())
                        options_set.append('item_body_font_size:')
                        
                    if line[0:20].lower() == 'item_body_font_name:': 
                        self.item_options['body_font_name'] = line[20:].strip()
                        options_set.append('item_body_font_name:')
                        
                    if line[0:21].lower() == 'item_body_font_color:': 
                        s = line[21:].strip().split(',')
                        self.item_options['body_font_color'] = (float(s[0])/255,
                                                                float(s[1])/255,
                                                                float(s[2])/255,
                                                                1)
                        options_set.append('item_body_font_color:')
                                                                
                    if line[0:22].lower() == 'item_button_font_size:':
                        self.item_options['button_font_size'] = int(line[22:].strip())
                        options_set.append('item_button_font_size:')
                        
                    if line[0:22].lower() == 'item_button_font_name:': 
                        self.item_options['button_font_name'] = line[22:].strip()
                        options_set.append('item_button_font_size:')
                        
                    if line[0:23].lower() == 'item_button_font_color:': 
                        s = line[23:].strip().split(',')
                        self.item_options['button_font_color'] = (float(s[0])/255,
                                                                float(s[1])/255,
                                                                float(s[2])/255,
                                                                1)  
                        options_set.append('item_button_font_color:')
                                                                
                    if line[0:25].lower() == 'item_button_normal_color:': 
                        s = line[25:].strip().split(',')
                        self.item_options['button_normal_color'] = (float(s[0])/255,
                                                                float(s[1])/255,
                                                                float(s[2])/255,
                                                                1)   
                        options_set.append('item_button_normal_color:')
                                                                
                    if line[0:23].lower() == 'item_button_down_color:': 
                        s = line[23:].strip().split(',')
                        self.item_options['button_down_color'] = (float(s[0])/255,
                                                                float(s[1])/255,
                                                                float(s[2])/255,
                                                                1)
                        options_set.append('item_button_down_color:')
                                                                
                    if line[0:22].lower() == 'item_background_color:':
                        s = line[22:].strip().split(',')
                        self.item_options['background_color'] = (float(s[0])/255,
                                                                float(s[1])/255,
                                                                float(s[2])/255,
                                                                1)
                        options_set.append('item_background_color:')
                                                                
                    # Overlay options
                    if line[0:24].lower() == 'overlay_title_font_size:':
                        self.overlay_options['title_font_size'] = int(line[24:].strip())
                        options_set.append('overlay_title_font_size:')
                        
                    if line[0:24].lower() == 'overlay_title_font_name:': 
                        self.overlay_options['title_font_name'] = line[24:].strip()
                        options_set.append('overlay_title_font_name:')
                        
                    if line[0:25].lower() == 'overlay_title_font_color:': 
                        s = line[25:].strip().split(',')
                        self.overlay_options['title_font_color'] = (float(s[0])/255,
                                                                float(s[1])/255,
                                                                float(s[2])/255,
                                                                1)
                        options_set.append('overlay_title_font_color:')
                                                                
                    if line[0:23].lower() == 'overlay_body_font_size:': 
                        self.overlay_options['body_font_size'] = int(line[23:].strip())
                        options_set.append('overlay_body_font_size:')
                        
                    if line[0:23].lower() == 'overlay_body_font_name:': 
                        self.overlay_options['body_font_name'] = line[23:].strip()
                        options_set.append('overlay_body_font_name:')
                        
                    if line[0:24].lower() == 'overlay_body_font_color:': 
                        s = line[24:].strip().split(',')
                        self.overlay_options['body_font_color'] = (float(s[0])/255,
                                                                float(s[1])/255,
                                                                float(s[2])/255,
                                                                1)
                        options_set.append('overlay_body_font_color:')
                                                                
                    if line[0:25].lower() == 'overlay_button_font_size:':
                        self.overlay_options['button_font_size'] = int(line[25:].strip())
                        options_set.append('overlay_button_font_size:')
                        
                    if line[0:25].lower() == 'overlay_button_font_name:': 
                        self.overlay_options['button_font_name'] = line[25:].strip()
                        options_set.append('overlay_button_font_name:')
                        
                    if line[0:26].lower() == 'overlay_button_font_color:': 
                        s = line[26:].strip().split(',')
                        self.overlay_options['button_font_color'] = (float(s[0])/255,
                                                                float(s[1])/255,
                                                                float(s[2])/255,
                                                                1)
                        options_set.append('overlay_button_font_color:')
                                                                
                    if line[0:28].lower() == 'overlay_button_normal_color:': 
                        s = line[28:].strip().split(',')
                        self.overlay_options['button_normal_color'] = (float(s[0])/255,
                                                                float(s[1])/255,
                                                                float(s[2])/255,
                                                                1)  
                        options_set.append('overlay_button_normal_color:')
                                                                
                    if line[0:26].lower() == 'overlay_button_down_color:': 
                        s = line[26:].strip().split(',')
                        self.overlay_options['button_down_color'] = (float(s[0])/255,
                                                                float(s[1])/255,
                                                                float(s[2])/255,
                                                                1)
                        options_set.append('overlay_button_down_color:')
                                                                
                    if line[0:25].lower() == 'overlay_background_color:':
                        s = line[25:].strip().split(',')
                        self.overlay_options['background_color'] = (float(s[0])/255,
                                                                float(s[1])/255,
                                                                float(s[2])/255,
                                                                1)
                        options_set.append('overlay_background_color:')
                                                                
                    # Timeline options
                    if line[0:9].lower() == 'filename:':
                        self.timeline_options['filename'] = line[9:].strip()
                        options_set.append('filename:')
                        
                    if line[0:13].lower() == 'reverse_time:':
                        self.timeline_options['reverse_time'] = line[13:].strip()
                        self.set_time_range(self.timeline_options['time_start'],
                                            self.timeline_options['time_stop'])
                        self.set_start_range(self.timeline_options['time_window_left'],
                                            self.timeline_options['time_window_right']) 
                        options_set.append('reverse_time:')
                                            
                    if line[0:26].lower() == 'timeline_background_color:':
                        s = line[26:].strip().split(',')
                        self.timeline_options['background_color'] = (float(s[0])/255,
                                                                        float(s[1])/255,
                                                                        float(s[2])/255,
                                                                        1)  
                        options_set.append('timeline_background_color:')
                                                                        
                    if line[0:20].lower() == 'timeline_line_color:':
                        s = line[20:].strip().split(',')
                        # Color of the main line
                        self.timeline_options['line_color'] = (float(s[0])/255,
                                                                        float(s[1])/255,
                                                                        float(s[2])/255,
                                                                        1)
                        options_set.append('timeline_line_color:')
                                                                        
                        # Color of the lines that connect the items
                        self.item_options['line_color'] = (float(s[0])/255,
                                                                        float(s[1])/255,
                                                                        float(s[2])/255,
                                                                        1)
                        options_set.append('timeline_line_color:')
                                                                        
                    if line[0:26].lower() == 'timeline_label_font_color:':
                        s = line[26:].strip().split(',')
                        self.timeline_options['label_font_color'] = (float(s[0])/255,
                                                                        float(s[1])/255,
                                                                        float(s[2])/255,
                                                                        1)
                        options_set.append('timeline_label_font_color:')
                                                                        
                    if line[0:25].lower() == 'timeline_label_font_size:':
                        self.timeline_options['label_font_size'] = int(line[25:].strip())
                        options_set.append('timeline_label_font_size:')
                        
                    if line[0:25].lower() == 'timeline_label_font_name:':
                        self.timeline_options['label_font_name'] = line[25:].strip()
                        options_set.append('timeline_label_font_name:')
                        
                    if line[0:26].lower() == 'timeline_background_image:':
                        self.timeline_options['background_source'] = line[26:].strip()
                        options_set.append('timeline_background_image:')
                        
                    if line[0:15].lower() == 'timeline_title:':
                        self.timeline_options['title'] = line[15:].strip()
                        options_set.append('timeline_title:')
                        
                    if line[0:25].lower() == 'timeline_title_font_size:':
                        self.timeline_options['title_font_size'] = int(line[25:].strip())
                        options_set.append('timeline_title_font_size:')
                        
                    if line[0:25].lower() == 'timeline_title_font_name:': 
                        self.timeline_options['title_font_name'] = line[25:].strip()
                        options_set.append('timeline_title_font_name:')
                        
                    if line[0:26].lower() == 'timeline_title_font_color:': 
                        s = line[26:].strip().split(',')
                        self.timeline_options['title_font_color'] = (float(s[0])/255,
                                                                float(s[1])/255,
                                                                float(s[2])/255,
                                                                1)
                        options_set.append('timeline_title_font_color:')
                                                                
                    if line[0:18].lower() == 'timeline_subtitle:':
                        self.timeline_options['subtitle'] = line[18:].strip()
                        options_set.append('timeline_subtitle:')
                        
                    if line[0:28].lower() == 'timeline_subtitle_font_size:':
                        self.timeline_options['subtitle_font_size'] = int(line[28:].strip())
                        options_set.append('timeline_subtitle_font_size:')
                        
                    if line[0:28].lower() == 'timeline_title_font_name:': 
                        self.timeline_options['subtitle_font_name'] = line[28:].strip()
                        options_set.append('timeline_title_font_name:')
                        
                    if line[0:29].lower() == 'timeline_subtitle_font_color:': 
                        s = line[29:].strip().split(',')
                        self.timeline_options['subtitle_font_color'] = (float(s[0])/255,
                                                                float(s[1])/255,
                                                                float(s[2])/255,
                                                                1)
                        options_set.append('timeline_subtitle_font_color:')
                                                                
                    if line[0:11].lower() == 'time_range:': 
                        input = line[11:].strip()
                        split = input.split(',')
                        if len(split) == 2:
                            self.set_time_range(float(split[0]), float(split[1]))
                            options_set.append('time_range:')
                        else:
                            print('Error: time_range must contain two values separated by a comma')
                        
                    if line[0:12].lower() == 'start_range:': 
                        input = line[12:].strip()
                        split = input.split(',')
                        if len(split) == 2:
                            self.set_start_range(float(split[0]), float(split[1]))
                            options_set.append('start_range:')
                        else:
                            print('Error: start_range must contain two values separated by a comma')                       
                    if line[0:16].lower() == 'time_window_min:': 
                        self.timeline_options['time_window_min'] = float(line[16:].strip())
                        options_set.append('time_window_min:')
                    if line[0:10].lower() == 'time_unit:':
                        self.timeline_options['time_unit'] = line[10:].strip()
                        options_set.append('time_unit:')

        except FileNotFoundError:
            print('Warning: configuration file config.conf not found')
            
        # Choose some best-guess settings for certain things if the user
        # has not supplied a setting
        
        # Read the input table to try and make guesses from that
        file = self.timeline_options['filename']
        type = file.split('.')[-1].lower()
        if type in ['xls', 'xlsx']:
            excel = pd.ExcelFile(file)
            tab = excel.parse(0).fillna('')
        elif type == 'csv':
            tab = pd.read_csv(file)
            
        if self.timeline_options['background_source'] is not '':
            # Make background rectangle transparent to see image
            col = self.timeline_options['background_color']
            self.timeline_options['background_color'] = (col[0], col[1], col[2], 0)
            
        if 'time_range:' not in options_set: # try time_range = min/max of input data
            try:
             times = tab['Year']
            except:
                pass
            else:
                self.set_time_range(min(times), max(times))
                
        if 'start_range:' not in options_set: # try start_range = time_range
            self.set_start_range(self.timeline_options['time_start'],
                                    self.timeline_options['time_stop'])
        
    def populate_timeline(self, *args):
    
        # This setup function parses the spreadsheet to create the timeline items.
        # It also adds labels to the timeline and initializes the overlays for later use
    
        # Read the specified table and create items
        file = self.timeline_options['filename']
        type = file.split('.')[-1].lower()
        if type in ['xls', 'xlsx']:
            excel = pd.ExcelFile(file)
            tab = excel.parse(0).fillna('')
        elif type == 'csv':
            tab = pd.read_csv(file)
        else:
            print('Error: unsupported file type: ' + type)
            
        for i in range(len(tab)):
            year = tab['Year'].iloc[i]
            short = tab['Short summary'].iloc[i].strip().replace('\\n', '\n')
            long = tab['Long summary'].iloc[i].strip().replace('\\n', '\n')
            rank = tab['Rank'].iloc[i]
            name = tab['Name'].iloc[i].strip().replace('\\n', '\n')
            media = tab['Media'].iloc[i]
            self.screen.timeline.add_item(Item(name, int(year), 
                                            self.timeline_options['time_unit'],
                                            int(rank),
                                            str(short), str(long), str(media),
                                            self.item_options))
        
        # Sort the list by rank
        self.screen.timeline.items.sort(key=lambda x: x.rank)

        # Add labels to the timeline
        window_size = self.screen.timeline.time_window_size
        n_labels = 5
        self.screen.timeline.label_sep = 1./n_labels
        
        # Add time labels to the timeline
        for i in range(n_labels):
            time = self.screen.timeline.time_window_left+(2*i+1)/10.*window_size
            self.screen.timeline.add_label(TimeLabel(time,
                                            self.timeline_options['time_unit'],
                                            self.timeline_options['label_font_name'],
                                            self.timeline_options['label_font_size'],
                                            self.timeline_options['label_font_color']))
               
        # Perform some first-time setup for the items.
        Clock.schedule_once(self.screen.timeline.arrange_items)       
        Clock.schedule_once(self.screen.timeline.refresh_items, 10)    
        
        # Initialize the overlays for later use
        self.screen.timeline.image_overlay = ImageOverlay(self.overlay_options)
        self.screen.timeline.add_widget(self.screen.timeline.image_overlay)
        self.screen.timeline.image_overlay.hide_content()
        self.screen.timeline.text_overlay = TextOverlay(self.overlay_options)
        self.screen.timeline.add_widget(self.screen.timeline.text_overlay)
        self.screen.timeline.text_overlay.hide_content()
        
        # Debugging code
        #Clock.schedule_interval(self.state, 1)
    
    def state(self, dt):
        objgraph.show_growth()
              

class MainApp(App):

    def build(self):
        self.manager = ScreenManagement()
        self.manager.setup()
        #self.profile = cProfile.Profile()
        #self.profile.enable()
        return(self.manager)
        
    def on_stop(self):
        pass
        #self.profile.disable()
        #self.profile.dump_stats('myapp.profile')
        #pdb.set_trace()
# Start the app
MainApp().run()














