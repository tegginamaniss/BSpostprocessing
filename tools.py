'''A collection of general helper functions'''

import math
import numpy

############################################################
# General conversion functions
def m2nm(data):
    '''Convert meters to nautical miles'''
    return data / 1852.0

def nm2m(data):
    '''Convert nautical miles to meter'''
    return data * 1852.0

def m2ft(data):
    '''Convert meter to ft'''
    return data / 0.305

def ft2m(data):
    '''Convert ft to mt'''
    return data * 0.305

def ms2kts(data):
    '''Convert meter per second to knots'''
    return data * 1.943844

def kts2ms(data):
    ''''Convert knots to meter per second'''
    return data / 1.943844

def rad2deg(data):
    '''Convert radians to degrees'''
    return math.degrees(data)

def deg2rad(data):
    '''Convert degrees to radians'''
    return math.radians(data)

############################################################
# Vector functions
def normalized(vector):
    return vector / numpy.sqrt((vector ** 2).sum(-1))[..., numpy.newaxis]

############################################################
# XML Related helper functions
def create_text_element(document, node_name, node_text):
    '''A helper function to create dom nodes'''
    node = document.createElement(node_name)
    text = document.createTextNode(node_text)

    node.appendChild(text)

    return node

############################################################
# Bounding box calculations
def calculate_bounding_box(acft_trace):
    '''Calculate the bounding box for an aircraft trace'''
    posx = acft_trace.column('posx')
    posy = acft_trace.column('posy')

    xmin = posx.min()
    xmax = posx.max()
    ymin = posy.min()
    ymax = posy.max()

    return (xmin, xmax, ymin, ymax)

class BoundingBox:
    '''A class to help with bounding box calculations'''
    def __init__(self, aircraft):
        (xmin, xmax, ymin, ymax) = calculate_bounding_box(aircraft[0])
        
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax

        for acft in aircraft:
            self.add_aircraft(acft)

    def add_aircraft(self, aircraft):
        '''Add a new aircraft and expand the bounding box if necesary'''
        (xmin, xmax, ymin, ymax) = calculate_bounding_box(aircraft)

        self.xmin = min(self.xmin, xmin)
        self.xmax = max(self.xmax, xmax)
        self.ymin = min(self.ymin, ymin)
        self.ymax = max(self.ymax, ymax)

    def extent(self):
        '''Get the extents of the bounding box'''
        return (self.xmin, self.xmax, self.ymin, self.ymax)

    def pad(self, amount):
        '''Add some padding to the bounding box'''
        self.xmin -= amount
        self.xmax += amount
        self.ymin -= amount
        self.ymax += amount
