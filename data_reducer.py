'''Reduce a data set based on some reduction parameters'''

import copy
import numpy
import time

from tools          import BoundingBox
from xmltree_writer import write_xml

def find_reduced_indices(remaining_acft, reduction_parameters):
    '''Calculate the reduced indices based on data from the gui'''
    # Collect the required parameters
    t       = remaining_acft[0].column('t')
    
    t_begin = reduction_parameters['t_begin']
    t_end   = reduction_parameters['t_end']
    stride  = reduction_parameters['stride']

    # Find the corresponding indices
    begin_idx = numpy.where(t <= t_begin)[0][-1]
    end_idx   = numpy.where(t <= t_end)  [0][-1]

    # Create a range with the required stride
    reduced_indices = numpy.arange(begin_idx, end_idx, stride)

    return reduced_indices

def center_data(aircraft):
    '''Calculate the center of all aircraft and shift them'''

    bb = BoundingBox(aircraft)

    (xmin,xmax,ymin,ymax) = bb.extent()

    xcenter = xmin + (xmax-xmin)/2.0
    ycenter = ymin + (ymax-ymin)/2.0

    for acft in aircraft:
        xpos = acft.column('posx')
        xpos -= xcenter

        ypos = acft.column('posy')
        ypos -= ycenter
    
        

class DataReducer:
    '''Helper class to reduce a set of data and write them'''
    
    def __init__(self, aircraft):
        self.aircraft = aircraft

    def write_data(self, reduction_parameters, filename):
        '''Reduce the data set and write the xml file'''

        # Select the aircraft objects whos callsign show up in the callsign list
        remaining_acft = copy.deepcopy([ acft for acft in self.aircraft
                                         if acft.callsign
                                         in reduction_parameters['callsigns'] ])

        # Guess what this does 
        if not remaining_acft:
            print 'No aircraft selected, skipping!'
            return

        # Data are usally logged at a higher rate than required, we can skip
        # over a number of points each time by specifying a stride and a
        # narrower range
        reduced_indices = find_reduced_indices(remaining_acft,
                                               reduction_parameters)

        # Reduce the data of the remaining aircraft to the points we need
        for acft in remaining_acft:
            acft.reduce(reduced_indices)

        # Center around the origin
        center_data(remaining_acft)

        # Time to write the data
        print 'Writing xml file: ' + filename
        
        t_begin = time.time()
        write_xml(remaining_acft, filename)
        t_end = time.time()
        
        print 'Writing took: {t} seconds'.format(t=t_end-t_begin)
